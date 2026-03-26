#!/usr/bin/env python3
"""Run a deterministic 5-pass audit for a wuxia BI JSON against phase0 and treatment draft."""

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

from modules.core.response_schemas import validate_bible_structure, validate_treatment_structure
from wuxia_tr_batch_harness import compute_treatment_metrics

GARBLED_RE = re.compile(r"\?{3,}|\ufffd")
MARTIAL_REQUIRED_FIELDS = (
    "name",
    "alias",
    "realm",
    "internal_energy",
    "mental_method",
    "wealth",
    "causal_injuries",
    "current_objective",
    "equipment",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def parse_int(value: Any, default: int | None = None) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = as_text(value).replace(",", "")
    if text.lstrip("+-").isdigit():
        return int(text)
    return default


def build_source_tr_handoff_checks(
    source_metrics: dict[str, Any],
    *,
    protagonist_match: bool,
    title_match_phase0: bool,
    faction_match: bool,
    realm_sync: bool,
    internal_energy_sync: bool,
    reputation_sync: bool,
    enemy_pressure_sync: bool,
) -> dict[str, bool]:
    checks = {
        "source_tr_density_gate": bool(source_metrics.get("production_density_gate")),
        "source_tr_critical_thin_gate": source_metrics.get("hard_gate_checks", {}).get("critical_thin_blocks_zero", True),
        "source_tr_thin_ratio_gate": source_metrics.get("hard_gate_checks", {}).get("thin_blocks_ratio_ok", True),
        "source_tr_late_thin_gate": source_metrics.get("hard_gate_checks", {}).get("late_thin_blocks_zero", True),
        "source_tr_short_stakes_gate": source_metrics.get("hard_gate_checks", {}).get("short_stakes_blocks_total_ok", True),
        "source_tr_endgame_stakes_gate": source_metrics.get("hard_gate_checks", {}).get("endgame_low_stakes_zero", True),
        "source_tr_callback_gate": source_metrics.get("hard_gate_checks", {}).get("callback_ratio_ok", True),
        "source_tr_unresolved_foreshadow_gate": source_metrics.get("hard_gate_checks", {}).get("unresolved_foreshadow_count_ok", True),
        "source_tr_faction_position_gate": source_metrics.get("hard_gate_checks", {}).get("faction_position_present", True),
        "source_tr_reputation_gate": source_metrics.get("hard_gate_checks", {}).get("jianghu_reputation_present", True),
        "source_tr_enemy_pressure_gate": source_metrics.get("hard_gate_checks", {}).get("enemy_pressure_present", True),
        "source_tr_late_opponent_gate": source_metrics.get("hard_gate_checks", {}).get("late_blank_opponent_ok", True),
        "source_tr_solution_stakes_repeat_gate": source_metrics.get("hard_gate_checks", {}).get("normalized_solution_stakes_repeat_ok", True),
        "source_tr_martial_progress_gate": source_metrics.get("hard_gate_checks", {}).get("martial_progress_ratio_ok", True),
        "source_tr_opponent_diversity_gate": source_metrics.get("opponent_unique", 0) >= 8 and source_metrics.get("top_opponent_share", 100.0) <= 30.0,
        "source_tr_weakness_repeat_gate": source_metrics.get("top_weakness_repetition", 999) < 4,
        "source_tr_solution_gate": source_metrics.get("avg_solution_chars", 0) >= 120 and source_metrics.get("one_sentence_like_solution_blocks", 999) <= 20,
        "protagonist_match": protagonist_match,
        "title_match_phase0": title_match_phase0,
        "protagonist_faction_match": faction_match,
        "martial_realm_sync_with_tr": realm_sync,
        "martial_internal_energy_sync_with_tr": internal_energy_sync,
        "martial_reputation_sync_with_tr": reputation_sync,
        "martial_enemy_pressure_sync_with_tr": enemy_pressure_sync,
    }
    if source_metrics.get("is_regressor_treatment"):
        checks["source_tr_regressor_recognition_count_gate"] = source_metrics.get("hard_gate_checks", {}).get(
            "regressor_recognition_count_ok", True
        )
        checks["source_tr_regressor_recognition_gap_gate"] = source_metrics.get("hard_gate_checks", {}).get(
            "regressor_recognition_gap_ok", True
        )
    return checks


def report_lines(
    *,
    phase0_path: Path,
    draft_path: Path,
    bi_path: Path,
    phase0: dict[str, Any],
    draft: list[dict[str, Any]],
    bi: dict[str, Any],
    draft_valid: bool,
    draft_errors: list[str],
    draft_warnings: list[str],
    bi_valid: bool,
    bi_errors: list[str],
    bi_warnings: list[str],
) -> tuple[list[str], int]:
    master = bi["MasterBible"]
    meta = master["ProjectData"]["MetaInfo"]
    core = master["ProjectData"]["CoreIdentity"]
    martial = master["MartialHUD"]["Protagonist"]["actual_truth"]
    roadmap = master.get("plot_roadmap", [])
    faction_map = master.get("FactionMap", {})
    treasures = master.get("Treasures", [])
    seeds = master.get("Seeds", [])
    key_npcs = master.get("AssetLibrary", {}).get("KeyNPCs", [])

    expected_title = phase0["project"].get("title_ko") or phase0["project"].get("title", "")
    expected_protagonist = phase0["protagonist"]["name"]
    expected_npcs = [expected_protagonist, *[npc["name"] for npc in phase0["phase0_design"]["npc_timeline"]]]
    source_metrics = compute_treatment_metrics(draft)
    last_block = draft[-1] if draft else {}
    # Support both genre_ext (blockguide) and martial_ext (wuxguide) keys
    ext_key = "martial_ext" if "martial_ext" in last_block else "genre_ext"
    ext_data = last_block.get(ext_key, {})
    expected_realm = as_text(ext_data.get("realm_after"))
    expected_energy = parse_int(ext_data.get("internal_energy_after"))
    # jianghu_reputation may be a dict {before, after} — extract the 'after' value for comparison
    rep_raw = ext_data.get("jianghu_reputation")
    if isinstance(rep_raw, dict):
        expected_reputation = as_text(rep_raw.get("after")) or as_text(rep_raw.get("before"))
    else:
        expected_reputation = as_text(rep_raw)
    expected_enemy_pressure = as_text(ext_data.get("enemy_pressure"))

    serialized = json.dumps(bi, ensure_ascii=False)
    title_seq_match = [block["title"] for block in roadmap] == [block["title"] for block in draft]
    first_last_match = (
        len(roadmap) == len(draft)
        and len(roadmap) > 0
        and roadmap[0]["title"] == draft[0]["title"]
        and roadmap[-1]["title"] == draft[-1]["title"]
    )
    protagonist_match = core["protagonist"] == martial["name"] == expected_protagonist
    npc_name_match = [entry["name"] for entry in key_npcs[: len(expected_npcs)]] == expected_npcs
    martial_truth_complete = all(
        (isinstance(martial.get(field), list) and field == "equipment") or as_text(martial.get(field))
        for field in MARTIAL_REQUIRED_FIELDS
    )
    faction_map_ready = bool(as_text(faction_map.get("protagonist_faction"))) and isinstance(faction_map.get("enemies"), list)
    treasures_ready = isinstance(treasures, list)
    seeds_ready = isinstance(seeds, list) and len(seeds) > 0
    garbled_free = not GARBLED_RE.search(serialized)
    source_handoff_checks = build_source_tr_handoff_checks(
        source_metrics,
        protagonist_match=protagonist_match,
        title_match_phase0=(meta["title"] == expected_title),
        faction_match=(core["protagonist_faction"] == as_text(faction_map.get("protagonist_faction"))),
        realm_sync=(not expected_realm or as_text(martial.get("realm")) == expected_realm == as_text(martial.get("current_realm"))),
        internal_energy_sync=(expected_energy is None or parse_int(martial.get("internal_energy")) == expected_energy),
        reputation_sync=(not expected_reputation or as_text(martial.get("reputation")) == expected_reputation),
        enemy_pressure_sync=(not expected_enemy_pressure or as_text(martial.get("current_enemy_pressure")) == expected_enemy_pressure),
    )

    passes = [
        ("PASS 1", "encoding and parse", {"utf8_json_parse": True, "garbled_token_zero": garbled_free, "draft_schema_valid": draft_valid}),
        (
            "PASS 2",
            "minimum schema",
            {
                "validate_bible_structure": bi_valid,
                "meta_title_present": bool(meta.get("title")),
                "plot_roadmap_len_70": len(roadmap) == 70,
                "martial_hud_present": "MartialHUD" in master,
            },
        ),
        ("PASS 3", "source TR handoff gate", source_handoff_checks),
        (
            "PASS 4",
            "TR linkage",
            {
                "roadmap_title_sequence": title_seq_match,
                "roadmap_hash_equal": stable_hash(roadmap) == stable_hash(draft),
                "first_last_title_match": first_last_match,
                "plot_roadmap_len_matches_draft": len(roadmap) == len(draft),
            },
        ),
        (
            "PASS 5",
            "MartialHUD and consistency",
            {
                "martial_truth_complete": martial_truth_complete,
                "faction_map_ready": faction_map_ready,
                "treasures_ready": treasures_ready,
                "seeds_ready": seeds_ready,
                "npc_name_consistent": npc_name_match,
                "world_state_present": "WorldState" in master,
                "asset_library_present": "AssetLibrary" in master,
            },
        ),
    ]

    fail_count = 0
    lines = [
        f"# Wuxia BI 5-Pass Audit ({date.today()})",
        "",
        "## Inputs",
        f"- phase0: `{phase0_path.as_posix()}`",
        f"- draft: `{draft_path.as_posix()}`",
        f"- bi: `{bi_path.as_posix()}`",
        "",
    ]
    for pass_name, label, checks in passes:
        ok = all(checks.values())
        if not ok:
            fail_count += 1
        lines.append(f"## {pass_name}: {label}")
        lines.append(f"- result: {'OK' if ok else 'FAIL'}")
        for key, value in checks.items():
            lines.append(f"- {key}: {'OK' if value else 'FAIL'}")
        lines.append("")

    lines.append("## Martial Truth")
    for field in MARTIAL_REQUIRED_FIELDS:
        lines.append(f"- {field}: {martial.get(field)}")
    lines.append("")
    lines.append("## Notes")
    if draft_errors:
        lines.append(f"- draft_errors: {draft_errors}")
    if draft_warnings:
        lines.append(f"- draft_warnings: {draft_warnings}")
    if bi_errors:
        lines.append(f"- bi_errors: {bi_errors}")
    if bi_warnings:
        lines.append(f"- bi_warnings: {bi_warnings}")
    lines.append(f"- key_npcs_seen: {[entry['name'] for entry in key_npcs[:5]]}")
    lines.append(f"- treasures_count: {len(treasures)}")
    lines.append(f"- seeds_count: {len(seeds)}")
    lines.append(f"- source_tr_hard_gate_failures: {source_metrics.get('hard_gate_failures', [])}")
    lines.append(f"- source_tr_callback_ratio: {source_metrics.get('callback_ratio')}")
    lines.append(f"- source_tr_martial_progress_blocks: {len(source_metrics.get('martial_progress_blocks', []))}/{source_metrics.get('block_count', 0)}")
    lines.append(f"- expected_realm_from_tr: {expected_realm}")
    lines.append(f"- expected_internal_energy_from_tr: {expected_energy}")
    lines.append(f"- expected_reputation_from_tr: {expected_reputation}")
    lines.append(f"- expected_enemy_pressure_from_tr: {expected_enemy_pressure}")
    lines.append("")
    return lines, fail_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase0", type=Path, required=True, help="Phase0 design JSON path")
    parser.add_argument("--draft", type=Path, required=True, help="Treatment draft JSON path")
    parser.add_argument("--bi", type=Path, required=True, help="Bible JSON path")
    parser.add_argument("--report", type=Path, required=True, help="Markdown report output path")
    args = parser.parse_args()

    phase0 = load_json(args.phase0)
    draft_raw = load_json(args.draft)
    # Support both wrapped {"blocks": [...]} and plain list formats
    draft = draft_raw["blocks"] if isinstance(draft_raw, dict) and "blocks" in draft_raw else draft_raw
    bi = load_json(args.bi)
    draft_valid, draft_errors, draft_warnings = validate_treatment_structure(draft)
    bi_valid, bi_errors, bi_warnings = validate_bible_structure(bi)
    lines, fail_count = report_lines(
        phase0_path=args.phase0,
        draft_path=args.draft,
        bi_path=args.bi,
        phase0=phase0,
        draft=draft,
        bi=bi,
        draft_valid=draft_valid,
        draft_errors=draft_errors,
        draft_warnings=draft_warnings,
        bi_valid=bi_valid,
        bi_errors=bi_errors,
        bi_warnings=bi_warnings,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"[OK] report written: {args.report}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
