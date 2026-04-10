#!/usr/bin/env python3
"""Run a deterministic 5-pass audit for a BI JSON against phase0 and treatment draft."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from tr_batch_harness import compute_treatment_metrics  # noqa: E402 - entrypoint path bootstrap must precede imports

from modules.core.response_schemas import (  # noqa: E402 - entrypoint path bootstrap must precede imports
    validate_bible_canonical_structure,
    validate_bible_structure,
    validate_treatment_canonical_structure,
    validate_treatment_structure,
)
from modules.core.stage0_handoff import normalize_bible_to_canonical_view, normalize_treatment_to_canonical_view
from modules.core.work_identity_surface import as_text, resolve_phase0_work_identity_surface, unique_preserve_order

GARBLED_RE = re.compile(r"\?{2,}|�|\ufffd")
META_REF_RE = re.compile(
    r"(?<![A-Za-z])(?:" 
    r"B\d{1,3}(?:\s*[~→\-]\s*B?\d{1,3})*|"
    r"Block\s+\d{1,3}|블록\s*\d{1,3}|"
    r"ARC[-\s]?\d{1,3}|Arc\s+\d{1,3}|아크\s*\d{1,3}|"
    r"Phase\s+\d{1,3}|페이즈\s*\d{1,3}|"
    r"Stage\s+\d{1,3}|스테이지\s*\d{1,3}"
    r")(?:에서의|에서|와의|과의|와|과|보다|의|으로|로|은|는|이|가|를|을|에|도|만)?(?![A-Za-z])",
    re.IGNORECASE,
)
ALLOWED_META_KEYS = {
    "block",
    "block_id",
    "ref",
    "arc_id",
    "arc_no",
    "phase_no",
    "stage_no",
    "recovery_block",
    "first_block",
    "last_confirmed_block",
    "block_acquired",
    "foreshadow_targets",
    "callback_sources",
    "foreshadow_block",
    "callback_block",
}
LABEL_META_KEYS = {"section_rotation", "arc_section", "phase", "phase_label"}
FOREIGN_TOKENS = [
    "골든 루트",
    "한시우",
    "SW인베스트먼트",
    "노스스타",
    "퀀텀바이오",
    "오로라 미디어",
    "엠파이어 리본",
]


def find_meta_leaks(value: Any, *, path: str = "", parent_key: str | None = None) -> dict[str, list[tuple[str, str]]]:
    leaks = {"diegetic": [], "label": []}
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else key
            child = find_meta_leaks(item, path=child_path, parent_key=key)
            leaks["diegetic"].extend(child["diegetic"])
            leaks["label"].extend(child["label"])
        return leaks
    if isinstance(value, list):
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]"
            child = find_meta_leaks(item, path=child_path, parent_key=parent_key)
            leaks["diegetic"].extend(child["diegetic"])
            leaks["label"].extend(child["label"])
        return leaks
    if isinstance(value, str) and parent_key not in ALLOWED_META_KEYS and META_REF_RE.search(value):
        bucket = "label" if parent_key in LABEL_META_KEYS else "diegetic"
        leaks[bucket].append((path, value.strip()))
    return leaks


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def preview_messages(messages: list[str], *, limit: int = 3) -> str:
    if not messages:
        return ""
    preview = messages[:limit]
    suffix = f" ... (+{len(messages) - limit} more)" if len(messages) > limit else ""
    return " | ".join(preview) + suffix


def read_bi_naming_surface(meta_info: dict[str, Any]) -> dict[str, Any]:
    commercial_label = as_text(meta_info.get("commercial_label"))
    slug_aliases_raw = meta_info.get("slug_aliases")
    slug_aliases = unique_preserve_order(slug_aliases_raw if isinstance(slug_aliases_raw, list) else [])
    return {
        "title": as_text(meta_info.get("title")),
        "commercial_label": commercial_label,
        "slug_aliases": slug_aliases,
        "allowed_titles": unique_preserve_order([as_text(meta_info.get("title")), commercial_label, *slug_aliases]),
    }


def parse_eok(raw: Any) -> int | None:
    if not isinstance(raw, str):
        return None
    text = raw.replace(" ", "")
    match = re.fullmatch(r"(?:(\d+)조)?(?:(\d+)억)?", text)
    if not match:
        return None
    jo = int(match.group(1) or 0)
    eok = int(match.group(2) or 0)
    return jo * 10000 + eok


def sample_fields(bi: dict[str, Any]) -> list[tuple[str, str]]:
    mb = bi["MasterBible"]
    meta = mb["ProjectData"]["MetaInfo"]
    core = mb["ProjectData"]["CoreIdentity"]
    actual = mb["FinanceHUD"]["Protagonist"]["actual_truth"]
    world = mb["WorldState"]
    key_npcs = mb["AssetLibrary"]["KeyNPCs"]
    roadmap = mb["plot_roadmap"]
    samples = [
        ("MetaInfo.title", meta["title"]),
        ("MetaInfo.grand_objective", meta["grand_objective"]),
        ("MetaInfo.genre_archetype", meta["genre_archetype"]),
        ("MetaInfo.logline", meta["logline"]),
        ("CoreIdentity.protagonist", core["protagonist"]),
        ("CoreIdentity.protagonist_faction", core["protagonist_faction"]),
        ("CoreIdentity.edge", core["edge"]),
        ("CoreIdentity.desire", core["desire"]),
        ("CoreIdentity.crisis", core["crisis"]),
        ("FinanceHUD.actual_truth.name", actual["name"]),
        ("FinanceHUD.actual_truth.rank", actual["rank"]),
        ("FinanceHUD.actual_truth.current_objective", actual["current_objective"]),
        ("FinanceHUD.actual_truth.final_goal", actual["final_goal"]),
        ("WorldState.CurrentEra", world["CurrentEra"]),
        ("WorldState.CurrentLocation", world["CurrentLocation"]),
        ("KeyNPCs[0].name", key_npcs[0]["name"]),
        ("KeyNPCs[1].name", key_npcs[1]["name"]),
        ("KeyNPCs[2].name", key_npcs[2]["name"]),
        ("plot_roadmap[0].title", roadmap[0]["title"]),
        ("plot_roadmap[34].title", roadmap[34]["title"]),
        ("plot_roadmap[69].title", roadmap[69]["title"]),
    ]
    return samples


def build_source_tr_handoff_checks(
    source_metrics: dict[str, Any],
    *,
    protagonist_match: bool,
    title_match_phase0: bool,
    title_within_phase0_surface: bool,
    starter_company_match: bool,
    portfolio_monotonic: bool,
    portfolio_sync: bool,
) -> dict[str, bool]:
    checks = {
        "source_tr_density_gate": bool(source_metrics.get("production_density_gate")),
        "source_tr_critical_thin_gate": source_metrics.get("hard_gate_checks", {}).get("critical_thin_blocks_zero", True),
        "source_tr_thin_ratio_gate": source_metrics.get("hard_gate_checks", {}).get("thin_blocks_ratio_ok", True),
        "source_tr_late_thin_gate": source_metrics.get("hard_gate_checks", {}).get("late_thin_blocks_zero", True),
        "source_tr_short_stakes_gate": source_metrics.get("hard_gate_checks", {}).get("short_stakes_blocks_total_ok", True),
        "source_tr_endgame_stakes_gate": source_metrics.get("hard_gate_checks", {}).get("endgame_low_stakes_zero", True),
        "source_tr_callback_gate": source_metrics.get("hard_gate_checks", {}).get("callback_ratio_ok", True),
        "source_tr_unresolved_foreshadow_gate": source_metrics.get("hard_gate_checks", {}).get(
            "unresolved_foreshadow_count_ok", True
        ),
        "source_tr_section_rotation_gate": source_metrics.get("hard_gate_checks", {}).get("section_rotation_present", True),
        "source_tr_late_opponent_gate": source_metrics.get("hard_gate_checks", {}).get("late_blank_opponent_ok", True),
        "source_tr_solution_stakes_repeat_gate": source_metrics.get("hard_gate_checks", {}).get(
            "normalized_solution_stakes_repeat_ok", True
        ),
        "source_tr_same_location_clone_gate": source_metrics.get("same_location_clone_count", 0) == 0,
        "source_tr_meta_gate": source_metrics.get("hard_gate_checks", {}).get("diegetic_meta_ref_zero", True),
        "source_tr_label_meta_gate": source_metrics.get("hard_gate_checks", {}).get("label_meta_ref_zero", True),
        "source_tr_block_meta_gate": source_metrics.get("hard_gate_checks", {}).get("diegetic_block_ref_zero", True),
        "source_tr_npc_continuity_gate": source_metrics.get("npc_continuity_mismatch_count", 0) == 0,
        "source_tr_opponent_diversity_gate": source_metrics["opponent_unique"] >= 8 and source_metrics["top_opponent_share"] <= 30.0,
        "source_tr_weakness_repeat_gate": source_metrics["top_weakness_repetition"] < 3,
        "source_tr_solution_gate": (
            source_metrics["avg_solution_chars"] >= 120
            and source_metrics["one_sentence_like_solution_blocks"] <= 20
        ),
        "protagonist_match": protagonist_match,
        "title_match_phase0": title_match_phase0,
        "title_within_phase0_surface": title_within_phase0_surface,
        "starter_company_match": starter_company_match,
        "portfolio_monotonic": portfolio_monotonic,
        "portfolio_sync_with_tr": portfolio_sync,
    }
    if source_metrics.get("is_regressor_treatment"):
        checks["source_tr_regressor_recognition_count_gate"] = source_metrics.get("hard_gate_checks", {}).get(
            "regressor_recognition_count_ok", True
        )
        checks["source_tr_regressor_recognition_gap_gate"] = source_metrics.get("hard_gate_checks", {}).get(
            "regressor_recognition_gap_ok", True
        )
    if "opening_reader_earning_signal_by6" in source_metrics.get("hard_gate_checks", {}):
        checks["source_tr_opening_reader_earning_gate"] = source_metrics.get("hard_gate_checks", {}).get(
            "opening_reader_earning_signal_by6", True
        )
    if "opening_macro_progression_ok" in source_metrics.get("hard_gate_checks", {}):
        checks["source_tr_opening_macro_progression_gate"] = source_metrics.get("hard_gate_checks", {}).get(
            "opening_macro_progression_ok", True
        )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase0", type=Path, required=True, help="Phase0 design JSON path")
    parser.add_argument("--draft", type=Path, required=True, help="Treatment draft JSON path")
    parser.add_argument("--bi", type=Path, required=True, help="Bible JSON path")
    parser.add_argument("--report", type=Path, required=True, help="Markdown report output path")
    args = parser.parse_args()

    report_lines: list[str] = []
    fail_count = 0

    phase0 = load_json(args.phase0)
    draft = load_json(args.draft)
    bi = load_json(args.bi)

    draft_valid, draft_errors, draft_warnings = validate_treatment_structure(draft)
    bi_valid, bi_errors, bi_warnings = validate_bible_structure(bi)
    draft_canonical_valid, draft_canonical_errors, draft_canonical_warnings = validate_treatment_canonical_structure(draft)
    bi_canonical_valid, bi_canonical_errors, bi_canonical_warnings = validate_bible_canonical_structure(bi)
    normalized_draft, draft_normalization_warnings = normalize_treatment_to_canonical_view(draft)
    normalized_bi, bi_normalization_warnings = normalize_bible_to_canonical_view(bi, treatment=draft)
    (
        normalized_draft_canonical_valid,
        normalized_draft_canonical_errors,
        normalized_draft_canonical_warnings,
    ) = validate_treatment_canonical_structure(normalized_draft)
    (
        normalized_bi_canonical_valid,
        normalized_bi_canonical_errors,
        normalized_bi_canonical_warnings,
    ) = validate_bible_canonical_structure(normalized_bi)
    source_metrics = compute_treatment_metrics(draft)

    mb = bi["MasterBible"]
    meta = mb["ProjectData"]["MetaInfo"]
    core = mb["ProjectData"]["CoreIdentity"]
    actual = mb["FinanceHUD"]["Protagonist"]["actual_truth"]
    roadmap = mb.get("plot_roadmap", [])
    starter_company = phase0["setting"]["starter_company"]["name"]
    phase0_naming_surface = resolve_phase0_work_identity_surface(phase0)
    bi_naming_surface = read_bi_naming_surface(meta)
    expected_title = phase0_naming_surface["canonical_title"]
    phase0_allowed_titles = phase0_naming_surface["allowed_titles"]
    expected_protagonist = phase0["protagonist"]["name"]
    expected_npcs = [phase0["protagonist"]["name"], *[npc["name"] for npc in phase0["phase0_design"]["npc_timeline"]]]

    serialized = json.dumps(bi, ensure_ascii=False)
    garbled_matches = GARBLED_RE.findall(serialized)
    meta_leaks = find_meta_leaks(mb)
    diegetic_meta_leaks = meta_leaks["diegetic"]
    label_meta_leaks = meta_leaks["label"]

    portfolio_history = actual["portfolio_history"]
    portfolio_monotonic = True
    portfolio_sync = True
    last_amount: int | None = None
    for entry in portfolio_history:
        amount = parse_eok(entry.get("total_assets"))
        if amount is None:
            portfolio_monotonic = False
            portfolio_sync = False
            break
        if last_amount is not None and amount < last_amount:
            portfolio_monotonic = False
        block_no = int(entry["block"])
        tr_amount = parse_eok(draft[block_no - 1]["genre_ext"]["capital_after"])
        if tr_amount != amount:
            portfolio_sync = False
        last_amount = amount

    title_seq_match = [block["title"] for block in roadmap] == [block["title"] for block in draft]
    first_last_match = (
        len(roadmap) == len(draft)
        and roadmap[0]["title"] == draft[0]["title"]
        and roadmap[-1]["title"] == draft[-1]["title"]
    )
    roadmap_hash_match = stable_hash(roadmap) == stable_hash(draft)

    sample_pairs = sample_fields(bi)
    sample_clean = all(not GARBLED_RE.search(value) for _, value in sample_pairs)

    foreign_hits = [token for token in FOREIGN_TOKENS if token in serialized]
    key_npc_names = [entry["name"] for entry in mb["AssetLibrary"]["KeyNPCs"]]
    npc_name_match = key_npc_names == expected_npcs
    source_handoff_checks = build_source_tr_handoff_checks(
        source_metrics,
        protagonist_match=(core["protagonist"] == actual["name"] == expected_protagonist),
        title_match_phase0=(meta["title"] == expected_title),
        title_within_phase0_surface=(as_text(meta["title"]) in phase0_allowed_titles),
        starter_company_match=(actual["financial_status"]["company"] == starter_company),
        portfolio_monotonic=portfolio_monotonic,
        portfolio_sync=portfolio_sync,
    )
    source_cadence_warning = source_metrics["solution_tail20_top_repetition"] > 50

    passes = [
        (
            "PASS 1",
            "인코딩/파싱",
            {
                "utf8_json_parse": True,
                "garbled_token_zero": len(garbled_matches) == 0,
                "diegetic_meta_text_zero": len(diegetic_meta_leaks) == 0,
                "label_meta_text_zero": len(label_meta_leaks) == 0,
                "draft_schema_valid": draft_valid,
            },
        ),
        (
            "PASS 2",
            "최소 스키마",
            {
                "validate_bible_structure": bi_valid,
                "meta_title_present": bool(meta.get("title")),
                "plot_roadmap_len_70": len(roadmap) == 70,
            },
        ),
        (
            "PASS 3",
            "source TR handoff gate",
            source_handoff_checks,
        ),
        (
            "PASS 4",
            "TR↔BI 동기화",
            {
                "roadmap_title_sequence": title_seq_match,
                "roadmap_first_last": first_last_match,
                "roadmap_hash_equal": roadmap_hash_match,
            },
        ),
        (
            "PASS 5",
            "품질 감리",
            {
                "sample_fields_clean": sample_clean,
                "foreign_token_zero": len(foreign_hits) == 0,
                "company_name_consistent": starter_company in serialized,
                "npc_name_consistent": npc_name_match,
            },
        ),
    ]

    report_lines.append(f"# BI 5-Pass 감리 보고서 ({date.today()})")
    report_lines.append("")
    report_lines.append("## 대상")
    report_lines.append(f"- phase0: `{args.phase0.as_posix()}`")
    report_lines.append(f"- draft: `{args.draft.as_posix()}`")
    report_lines.append(f"- bi: `{args.bi.as_posix()}`")
    report_lines.append("")
    report_lines.append("## Naming Authority")
    report_lines.append(f"- phase0_title_resolution: {phase0_naming_surface['resolution']}")
    report_lines.append(f"- phase0_canonical_title: {phase0_naming_surface['canonical_title']}")
    report_lines.append(f"- phase0_commercial_label: {phase0_naming_surface['commercial_label'] or '(none)'}")
    report_lines.append(f"- phase0_slug_aliases: {phase0_naming_surface['slug_aliases']}")
    report_lines.append(f"- phase0_allowed_titles: {phase0_allowed_titles}")
    report_lines.append(f"- bi_meta_title: {bi_naming_surface['title']}")
    report_lines.append(f"- bi_meta_commercial_label: {bi_naming_surface['commercial_label'] or '(none)'}")
    report_lines.append(f"- bi_meta_slug_aliases: {bi_naming_surface['slug_aliases']}")
    report_lines.append("")
    report_lines.append("## Source TR Metrics")
    report_lines.append(f"- production_density_gate: {'PASS' if source_metrics['production_density_gate'] else 'FAIL'}")
    report_lines.append(f"- avg_bundle_chars: {source_metrics['avg_bundle_chars']}")
    report_lines.append(f"- avg_solution_chars: {source_metrics['avg_solution_chars']}")
    report_lines.append(f"- foreshadow_total: {source_metrics['foreshadow_total']}")
    report_lines.append(f"- callback_total: {source_metrics['callback_total']}")
    report_lines.append(f"- callback_ratio: {source_metrics['callback_ratio']}")
    report_lines.append(f"- unresolved_foreshadow_count: {source_metrics['unresolved_foreshadow_count']}")
    report_lines.append(f"- diegetic_meta_ref_count: {source_metrics.get('diegetic_meta_ref_count', 0)}")
    report_lines.append(f"- label_meta_ref_count: {source_metrics.get('label_meta_ref_count', 0)}")
    report_lines.append(f"- diegetic_block_ref_count(alias): {source_metrics.get('diegetic_block_ref_count', 0)}")
    report_lines.append(f"- opponent_unique: {source_metrics['opponent_unique']}")
    report_lines.append(f"- top_opponent_repetition: {source_metrics['top_opponent_repetition']}")
    report_lines.append(f"- top_opponent_share: {source_metrics['top_opponent_share']}%")
    report_lines.append(f"- top_weakness_repetition: {source_metrics['top_weakness_repetition']}")
    report_lines.append(f"- deal_top_repetition: {source_metrics['deal_top_repetition']}")
    report_lines.append(f"- method_top_repetition: {source_metrics['method_top_repetition']}")
    report_lines.append(f"- solution_tail20_top_repetition: {source_metrics['solution_tail20_top_repetition']}")
    report_lines.append(f"- one_sentence_like_solution_blocks: {source_metrics['one_sentence_like_solution_blocks']}")
    report_lines.append(f"- business_sector_missing: {source_metrics['business_sector_missing']}")
    report_lines.append(f"- section_rotation_missing: {source_metrics['section_rotation_missing']}")
    report_lines.append(f"- critical_thin_blocks: {source_metrics['critical_thin_blocks']}")
    report_lines.append(f"- thin_blocks: {source_metrics['thin_blocks']}")
    report_lines.append(f"- short_stakes_blocks: {source_metrics['short_stakes_blocks']}")
    report_lines.append(f"- same_location_clone_count: {source_metrics.get('same_location_clone_count', 0)}")
    report_lines.append(f"- npc_continuity_mismatch_count: {source_metrics.get('npc_continuity_mismatch_count', 0)}")
    report_lines.append(f"- recognition_signal_blocks: {source_metrics['recognition_signal_blocks']}")
    report_lines.append(f"- max_recognition_gap_streak: {source_metrics['max_recognition_gap_streak']}")
    report_lines.append(f"- late_blank_opponent_blocks: {source_metrics['late_blank_opponent_blocks']}")
    report_lines.append(f"- endgame_low_stakes_blocks: {source_metrics['endgame_low_stakes_blocks']}")
    report_lines.append(
        f"- normalized_solution_stakes_repeat_max: {source_metrics['normalized_solution_stakes_repeat_max']}"
    )
    report_lines.append(f"- hard_gate_failures: {source_metrics['hard_gate_failures']}")
    report_lines.append(f"- window_10_opponent_unique_counts: {source_metrics['window_10_opponent_unique_counts']}")
    report_lines.append("")
    report_lines.append("## Meta Leak Check")
    report_lines.append(f"- bi_diegetic_meta_leak_count: {len(diegetic_meta_leaks)}")
    report_lines.append(f"- bi_label_meta_leak_count: {len(label_meta_leaks)}")
    if diegetic_meta_leaks:
        report_lines.append("- bi_diegetic_meta_leak_examples:")
        for leak_path, leak_value in diegetic_meta_leaks[:10]:
            report_lines.append(f"  - `{leak_path}` -> {leak_value}")
    if label_meta_leaks:
        report_lines.append("- bi_label_meta_leak_examples:")
        for leak_path, leak_value in label_meta_leaks[:10]:
            report_lines.append(f"  - `{leak_path}` -> {leak_value}")
    report_lines.append("")
    report_lines.append("## Canonical Contract")
    report_lines.append(f"- raw_bi_canonical_contract: {'PASS' if bi_canonical_valid else 'FAIL'}")
    report_lines.append(f"- raw_tr_canonical_contract: {'PASS' if draft_canonical_valid else 'FAIL'}")
    report_lines.append(
        f"- raw_pair_canonical_contract: {'PASS' if (bi_canonical_valid and draft_canonical_valid) else 'FAIL'}"
    )
    report_lines.append(f"- normalized_bi_canonical_view: {'PASS' if normalized_bi_canonical_valid else 'FAIL'}")
    report_lines.append(f"- normalized_tr_canonical_view: {'PASS' if normalized_draft_canonical_valid else 'FAIL'}")
    report_lines.append(
        f"- normalized_pair_canonical_view: {'PASS' if (normalized_bi_canonical_valid and normalized_draft_canonical_valid) else 'FAIL'}"
    )
    if bi_canonical_errors:
        report_lines.append(
            f"- raw_bi_canonical_errors[{len(bi_canonical_errors)}]: {preview_messages(bi_canonical_errors)}"
        )
    if draft_canonical_errors:
        report_lines.append(
            f"- raw_tr_canonical_errors[{len(draft_canonical_errors)}]: {preview_messages(draft_canonical_errors)}"
        )
    if bi_normalization_warnings:
        report_lines.append(
            f"- bi_normalization_warnings[{len(bi_normalization_warnings)}]: {preview_messages(bi_normalization_warnings)}"
        )
    if draft_normalization_warnings:
        report_lines.append(
            f"- tr_normalization_warnings[{len(draft_normalization_warnings)}]: {preview_messages(draft_normalization_warnings)}"
        )
    if normalized_bi_canonical_errors:
        report_lines.append(
            f"- normalized_bi_canonical_errors[{len(normalized_bi_canonical_errors)}]: "
            f"{preview_messages(normalized_bi_canonical_errors)}"
        )
    if normalized_draft_canonical_errors:
        report_lines.append(
            f"- normalized_tr_canonical_errors[{len(normalized_draft_canonical_errors)}]: "
            f"{preview_messages(normalized_draft_canonical_errors)}"
        )
    report_lines.append("")

    for pass_name, label, checks in passes:
        pass_ok = all(checks.values())
        if not pass_ok:
            fail_count += 1
        report_lines.append(f"## {pass_name}: {label}")
        report_lines.append(f"- result: {'OK' if pass_ok else 'FAIL'}")
        for key, ok in checks.items():
            report_lines.append(f"- {key}: {'OK' if ok else 'FAIL'}")
        report_lines.append("")

    report_lines.append("## 샘플링")
    for path, value in sample_pairs:
        report_lines.append(f"- {path}: {value}")
    report_lines.append("")

    report_lines.append("## 메모")
    if draft_errors:
        report_lines.append(f"- draft_errors: {draft_errors}")
    if draft_warnings:
        report_lines.append(f"- draft_warnings: {draft_warnings}")
    if bi_errors:
        report_lines.append(f"- bi_errors: {bi_errors}")
    if bi_warnings:
        report_lines.append(f"- bi_warnings: {bi_warnings}")
    if draft_canonical_warnings:
        report_lines.append(f"- draft_canonical_warnings: {draft_canonical_warnings}")
    if bi_canonical_warnings:
        report_lines.append(f"- bi_canonical_warnings: {bi_canonical_warnings}")
    if normalized_draft_canonical_warnings:
        report_lines.append(f"- normalized_draft_canonical_warnings: {normalized_draft_canonical_warnings}")
    if normalized_bi_canonical_warnings:
        report_lines.append(f"- normalized_bi_canonical_warnings: {normalized_bi_canonical_warnings}")
    if garbled_matches:
        report_lines.append(f"- garbled_matches: {garbled_matches[:20]}")
    if foreign_hits:
        report_lines.append(f"- foreign_hits: {foreign_hits}")
    if source_cadence_warning:
        report_lines.append(
            f"- source_tr_cadence_warning: solution tail-20 repeats {source_metrics['solution_tail20_top_repetition']} times"
        )
    if source_metrics["pattern_feedback_snapshot"]["top_opponents"]:
        report_lines.append(
            f"- pattern_feedback_snapshot.top_opponents: {source_metrics['pattern_feedback_snapshot']['top_opponents']}"
        )
    if source_metrics["pattern_feedback_snapshot"]["top_weaknesses"]:
        report_lines.append(
            f"- pattern_feedback_snapshot.top_weaknesses: {source_metrics['pattern_feedback_snapshot']['top_weaknesses']}"
        )
    if source_metrics["pattern_feedback_snapshot"]["solution_pattern_warnings"]:
        report_lines.append(
            f"- pattern_feedback_snapshot.solution_pattern_warnings: {source_metrics['pattern_feedback_snapshot']['solution_pattern_warnings']}"
        )
    if source_metrics["pattern_feedback_snapshot"]["forbidden_pattern_reuse"]:
        report_lines.append(
            f"- pattern_feedback_snapshot.forbidden_pattern_reuse: {source_metrics['pattern_feedback_snapshot']['forbidden_pattern_reuse']}"
        )
    if source_metrics["pattern_feedback_snapshot"]["structural_gate_failures"]:
        report_lines.append(
            f"- pattern_feedback_snapshot.structural_gate_failures: {source_metrics['pattern_feedback_snapshot']['structural_gate_failures']}"
        )
    if fail_count == 0:
        report_lines.append("- summary: 5개 PASS 모두 통과")
    else:
        report_lines.append(f"- summary: {fail_count}개 PASS 실패")
    report_lines.append("")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"[OK] audit report written: {args.report}")
    print(f"[RESULT] {'PASS' if fail_count == 0 else 'FAIL'}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
