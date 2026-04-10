#!/usr/bin/env python3
"""Operational normalization runner for live production BI/TR pairs."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_bi_tr_consumability import (
    choose_preferred_treatment,
    infer_bible_work_key,
    infer_treatment_work_key,
    inspect_pair,
)
from modules.core.stage0_handoff import get_effective_bible_root, normalize_bible_to_canonical_view, normalize_treatment_blocks
from modules.core.work_identity_surface import resolve_phase0_work_identity_surface

LIVE_BIBLE_DIR = ROOT / "bible"
LIVE_TREATMENT_DIR = ROOT / "treatments"
PHASE0_DIR = ROOT / "treatments" / "phase0"
PREPROCESS_DIR = ROOT / "treatments" / "preprocess"
GRADE_ALIAS_README = ROOT / "material_ssot" / "00_governance" / "production_pair_grade_aliases" / "README.md"
OPERATIONAL_REGISTRY_JSON = ROOT / "material_ssot" / "00_governance" / "production-pair-operational-registry-v1.json"

DEFAULT_STATE = "untouched_historical_live_pair"
STATE_CHOICES = (
    "untouched_historical_live_pair",
    "new_live_pair",
    "newly_touched_live_pair",
    "regenerated_pair",
    "promotion_target_pair",
    "reference_pair",
    "newly_touched_reference_pair",
)
SEVERITY_ORDER = {
    "blocker": 0,
    "drift": 1,
    "alias": 2,
    "warning": 3,
    "note": 4,
}
BLOCK_CORE_PATHS = (
    ("block_id", "TR.blocks[*].block_id"),
    ("block_no", "TR.blocks[*].block_no"),
    ("title", "TR.blocks[*].title"),
    ("content.context", "TR.blocks[*].content.context"),
    ("content.event_villain", "TR.blocks[*].content.event_villain"),
    ("content.solution", "TR.blocks[*].content.solution"),
    ("content.reward", "TR.blocks[*].content.reward"),
    ("stakes", "TR.blocks[*].stakes"),
    ("emotional_beat", "TR.blocks[*].emotional_beat"),
    ("tension_level", "TR.blocks[*].tension_level"),
    ("location", "TR.blocks[*].location"),
    ("time_span", "TR.blocks[*].time_span"),
    ("relationship_delta", "TR.blocks[*].relationship_delta"),
    ("power_shift", "TR.blocks[*].power_shift"),
)
BI_FAMILY_CORE = {
    "blockguide": ("FinanceHUD", "WorldState", "AssetLibrary", "Seeds"),
    "wuxguide": ("MartialHUD", "WorldState", "AssetLibrary", "FactionMap", "Treasures", "Seeds"),
}
BLOCKGUIDE_PROMOTED_SLOTS = (
    ("regulatory_context", "WorldState.regulatory_context", "BI.MasterBible.WorldState.regulatory_context"),
    ("expansion_order_locked", "WorldState.expansion_order_locked", "BI.MasterBible.WorldState.expansion_order_locked"),
    ("hud_interpretation", "WorldState.hud_interpretation", "BI.MasterBible.WorldState.hud_interpretation"),
    ("capital_curve", "AssetLibrary.CapitalCurve", "BI.MasterBible.AssetLibrary.CapitalCurve"),
    ("do_not_fake", "GenreRules.do_not_fake", "BI.MasterBible.GenreRules.do_not_fake"),
    ("contamination_guard", "GenreRules.contamination_guard", "BI.MasterBible.GenreRules.contamination_guard"),
)
WUXGUIDE_PROMOTED_SLOTS = (
    ("internal_energy_curve", "WorldState.internal_energy_curve", "BI.MasterBible.WorldState.internal_energy_curve"),
    ("taboo_rules", "GenreRules.taboo_rules", "BI.MasterBible.GenreRules.taboo_rules"),
    ("do_not_fake", "GenreRules.do_not_fake", "BI.MasterBible.GenreRules.do_not_fake"),
)


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    fix_target: str | None = None
    count: int | None = None


@dataclass
class PairNormalizationReport:
    work_id: str
    family: str
    bible_path: str | None
    treatment_path: str | None
    reference_only: bool
    operational_state: str
    operational_state_source: str
    pair_consumability: str
    strict_tier_a_status: str
    tier_b_status: str
    schema_status: str
    evidence_mode: str
    open_migration_debt: bool
    alias_refresh_eligible: bool
    active_baseline_eligible: bool
    root_phase0_status: str
    preprocess_authority_available: bool
    naming_surface_status: str
    naming_surface_resolution: str | None
    canonical_title: str | None
    observed_bi_title: str | None
    raw_pair_canonical_valid: bool
    normalized_pair_canonical_valid: bool
    counts: dict[str, int] = field(default_factory=dict)
    required_fix_targets: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def load_json(path: Path | None) -> Any | None:
    if path is None or not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_work_id(value: str) -> str:
    cleaned = re.sub(r"^\d+_", "", value)
    return cleaned.strip("_").lower()


def load_reference_only_work_ids() -> set[str]:
    if not GRADE_ALIAS_README.is_file():
        return set()
    text = GRADE_ALIAS_README.read_text(encoding="utf-8")
    results: set[str] = set()
    for line in text.splitlines():
        if "reference pair" not in line:
            continue
        match = re.search(r"`([^`]+)\.md`", line)
        if not match:
            continue
        stem = re.sub(r"^[A-Z]+_", "", match.group(1))
        results.add(normalize_work_id(stem))
    return results


def infer_family(bible_data: Any, treatment_data: Any, work_id: str) -> str:
    if isinstance(treatment_data, dict):
        family = as_text(treatment_data.get("_family")).lower()
        if family:
            return family
    if isinstance(bible_data, dict):
        family = as_text(bible_data.get("_family")).lower()
        if family:
            return family
        genre = as_text(bible_data.get("_genre")).lower()
        if "wux" in genre or "무협" in genre:
            return "wuxguide"
    blocks = normalize_treatment_blocks(treatment_data)
    if any(isinstance(block.get("martial_ext"), dict) for block in blocks if isinstance(block, dict)):
        return "wuxguide"
    if "wux" in work_id:
        return "wuxguide"
    return "blockguide"


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set)):
        return any(is_present(item) for item in value)
    if isinstance(value, dict):
        return any(is_present(item) for item in value.values()) if value else False
    return True


def get_nested(data: Any, path: str, default: Any = None) -> Any:
    current = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return default
        if part not in current:
            return default
        current = current[part]
    return current


def deep_key_present(data: Any, key: str) -> bool:
    if isinstance(data, dict):
        if key in data:
            return True
        return any(deep_key_present(value, key) for value in data.values())
    if isinstance(data, list):
        return any(deep_key_present(item, key) for item in data)
    return False


def unique_texts(items: list[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = as_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def count_missing_blocks(blocks: list[dict[str, Any]], path: str) -> int:
    count = 0
    for block in blocks:
        if not is_present(get_nested(block, path)):
            count += 1
    return count


def collect_git_path_state(paths: list[Path]) -> dict[str, str]:
    results = {str(path): "clean" for path in paths}
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "-c",
                "core.quotepath=false",
                "status",
                "--porcelain",
                "--",
                *[str(path.relative_to(ROOT)) for path in paths if path],
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return results

    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        rel = line[3:].strip()
        abs_path = str((ROOT / rel).resolve())
        if "?" in status:
            results[abs_path] = "untracked"
        else:
            results[abs_path] = "modified"
    return results


def infer_operational_state(
    work_id: str,
    *,
    bible_path: Path | None,
    treatment_path: Path | None,
    reference_only: bool,
    global_state: str | None,
    overrides: dict[str, str],
) -> tuple[str, str]:
    if work_id in overrides:
        return overrides[work_id], "override"
    if global_state:
        return global_state, "global-override"

    paths = [path.resolve() for path in (bible_path, treatment_path) if path is not None]
    git_state = collect_git_path_state(paths)
    if reference_only:
        if any(git_state.get(str(path), "clean") in {"modified", "untracked"} for path in paths):
            return "newly_touched_reference_pair", "reference-git-modified"
        return "reference_pair", "reference-default"
    if any(git_state.get(str(path), "clean") == "untracked" for path in paths):
        return "new_live_pair", "git-untracked"
    if any(git_state.get(str(path), "clean") == "modified" for path in paths):
        return "newly_touched_live_pair", "git-modified"
    return DEFAULT_STATE, "default-live-root"


def gather_metadata_strings(tr_data: Any, bi_data: Any) -> list[str]:
    values: list[str] = []
    for payload in (tr_data, bi_data):
        if not isinstance(payload, dict):
            continue
        for key in ("_authority_chain", "_authority_sources", "_phase0_ref", "_source_phase0", "_source_tr"):
            raw = payload.get(key)
            if isinstance(raw, list):
                values.extend(as_text(item) for item in raw if as_text(item))
            else:
                text = as_text(raw)
                if text:
                    values.append(text)
    return values


def resolve_phase0_status(work_id: str, metadata_strings: list[str], untouched_historical: bool) -> tuple[str, bool, bool]:
    root_phase0 = PHASE0_DIR / f"{work_id}_phase0_design.json"
    preprocess_manifest = PREPROCESS_DIR / work_id / "source_manifest.json"
    root_exists = root_phase0.is_file()
    preprocess_available = preprocess_manifest.is_file()
    authority_named = any(work_id in value and ("phase0" in value or "preprocess" in value) for value in metadata_strings)
    if root_exists:
        return "root-phase0-present", preprocess_available, True
    if untouched_historical and preprocess_available and authority_named:
        return "preprocess-fallback-alias-pass", preprocess_available, False
    return "missing-root-phase0", preprocess_available, False


def add_finding(
    findings: list[Finding],
    severity: str,
    code: str,
    message: str,
    *,
    fix_target: str | None = None,
    count: int | None = None,
) -> None:
    findings.append(Finding(severity=severity, code=code, message=message, fix_target=fix_target, count=count))


def get_ext(block: dict[str, Any], *, allow_alias: bool) -> tuple[dict[str, Any], str | None]:
    genre_ext = block.get("genre_ext")
    if isinstance(genre_ext, dict):
        return genre_ext, "genre_ext"
    if allow_alias:
        martial_ext = block.get("martial_ext")
        if isinstance(martial_ext, dict):
            return martial_ext, "martial_ext"
    return {}, None


def count_blocks_missing_resolved_fields(
    blocks: list[dict[str, Any]],
    field_paths: list[str],
    *,
    allow_alias: bool,
    alias_field_map: dict[str, str] | None = None,
) -> dict[str, int]:
    alias_field_map = alias_field_map or {}
    counts = {field: 0 for field in field_paths}
    for block in blocks:
        ext, _ext_key = get_ext(block, allow_alias=allow_alias)
        for field in field_paths:
            canonical_value = get_nested(ext, field)
            alias_value = get_nested(ext, alias_field_map.get(field, "")) if alias_field_map.get(field) else None
            if not is_present(canonical_value) and not is_present(alias_value):
                counts[field] += 1
    return counts


def top_findings(findings: list[Finding], *, limit: int = 3) -> list[Finding]:
    return sorted(findings, key=lambda item: (SEVERITY_ORDER[item.severity], -(item.count or 0), item.code))[:limit]


def sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda item: (SEVERITY_ORDER[item.severity], -(item.count or 0), item.code))


def read_bi_naming_surface(canonical_bi: Any) -> dict[str, Any]:
    master_bible = get_effective_bible_root(canonical_bi)
    project_data = master_bible.get("ProjectData") if isinstance(master_bible, dict) else {}
    meta_info = project_data.get("MetaInfo") if isinstance(project_data, dict) else {}
    slug_aliases_raw = meta_info.get("slug_aliases") if isinstance(meta_info, dict) else []
    slug_aliases = unique_texts(slug_aliases_raw if isinstance(slug_aliases_raw, list) else [])
    title = as_text(meta_info.get("title")) if isinstance(meta_info, dict) else ""
    commercial_label = as_text(meta_info.get("commercial_label")) if isinstance(meta_info, dict) else ""
    return {
        "title": title,
        "commercial_label": commercial_label,
        "slug_aliases": slug_aliases,
        "allowed_titles": unique_texts([title, commercial_label, *slug_aliases]),
    }


def inspect_naming_surface(
    *,
    phase0_data: Any,
    canonical_bi: Any,
    untouched_historical: bool,
    findings: list[Finding],
    counts: dict[str, int],
    notes: list[str],
) -> tuple[str, str | None, str | None, str | None]:
    bi_naming_surface = read_bi_naming_surface(canonical_bi)
    observed_bi_title = bi_naming_surface["title"] or None
    if not isinstance(phase0_data, dict):
        notes.append("naming surface unavailable: root phase0 payload missing")
        counts["naming_surface_available"] = 0
        return "unavailable", None, None, observed_bi_title

    phase0_naming_surface = resolve_phase0_work_identity_surface(phase0_data)
    canonical_title = as_text(phase0_naming_surface.get("canonical_title")) or None
    allowed_titles = phase0_naming_surface.get("allowed_titles", [])
    resolution = as_text(phase0_naming_surface.get("resolution")) or None
    counts["naming_surface_available"] = 1
    counts["naming_allowed_title_count"] = len(allowed_titles)

    if not canonical_title:
        notes.append("naming surface unavailable: phase0 title authority unresolved")
        return "unavailable", resolution, None, observed_bi_title
    if not observed_bi_title:
        notes.append(f"naming title missing: expected canonical '{canonical_title}'")
        return "missing", resolution, canonical_title, None
    if observed_bi_title == canonical_title:
        return "canonical", resolution, canonical_title, observed_bi_title
    if observed_bi_title in allowed_titles:
        add_finding(
            findings,
            "alias",
            "BI-NAMING-ALIAS-SURFACE",
            (
                f"BI MetaInfo.title '{observed_bi_title}' is inside the allowed phase0 naming surface "
                f"but not canonical title '{canonical_title}'."
            ),
            fix_target="BI.MasterBible.ProjectData.MetaInfo.title",
        )
        notes.append(f"naming alias surface: {observed_bi_title} -> {canonical_title}")
        return "alias-surface", resolution, canonical_title, observed_bi_title

    add_finding(
        findings,
        "drift",
        "BI-NAMING-DRIFT",
        (
            f"BI MetaInfo.title '{observed_bi_title}' is outside the phase0 naming surface "
            f"{allowed_titles or [canonical_title]}."
        ),
        fix_target="BI.MasterBible.ProjectData.MetaInfo.title",
    )
    notes.append(f"naming drift: {observed_bi_title} vs {canonical_title}")
    return "drifting", resolution, canonical_title, observed_bi_title


def inspect_family_fields(
    *,
    blocks: list[dict[str, Any]],
    family: str,
    untouched_historical: bool,
    forward_strict: bool,
    findings: list[Finding],
    counts: dict[str, int],
) -> tuple[bool, list[str], list[str]]:
    strict_blockers: list[str] = []
    tier_b_drifts: list[str] = []

    if family == "blockguide":
        for field in ("capital_before", "capital_after", "capital_delta"):
            missing = count_missing_blocks(blocks, f"genre_ext.{field}")
            counts[f"missing_{field}"] = missing
            if missing:
                strict_blockers.append(field)
                add_finding(
                    findings,
                    "blocker",
                    f"TR-{field.upper()}",
                    f"{missing}/{len(blocks)} blocks miss canonical genre_ext.{field}.",
                    fix_target=f"TR.blocks[*].genre_ext.{field}",
                    count=missing,
                )

        block_cider_missing = 0
        block_cider_invalid = 0
        for block in blocks:
            block_cider = get_nested(block, "genre_ext.block_cider")
            if not isinstance(block_cider, dict):
                block_cider_missing += 1
                continue
            has_cider = block_cider.get("has_cider")
            receipt_type = as_text(block_cider.get("receipt_type"))
            receipt_line = as_text(block_cider.get("receipt_line"))
            pain_only_exit = block_cider.get("pain_only_exit")
            if has_cider is not True or not receipt_type or not receipt_line or pain_only_exit is not False:
                block_cider_invalid += 1
        counts["missing_block_cider"] = block_cider_missing
        counts["invalid_block_cider"] = block_cider_invalid
        if block_cider_missing or block_cider_invalid:
            strict_blockers.append("block_cider")
            add_finding(
                findings,
                "blocker" if forward_strict or not untouched_historical else "drift",
                "TR-BLOCK-CIDER",
                (
                    f"canonical genre_ext.block_cider is missing in {block_cider_missing}/{len(blocks)} blocks "
                    f"and invalid in {block_cider_invalid}/{len(blocks)} blocks."
                ),
                fix_target="TR.blocks[*].genre_ext.block_cider",
                count=block_cider_missing + block_cider_invalid,
            )

        for field in ("method", "success_pattern", "deal_type", "opponent.name"):
            missing = count_missing_blocks(blocks, f"genre_ext.{field}")
            counts[f"tier_b_missing_{field.replace('.', '_')}"] = missing
            if missing:
                tier_b_drifts.append(field)
                add_finding(
                    findings,
                    "drift",
                    f"TR-TIERB-{field.replace('.', '-').upper()}",
                    f"{missing}/{len(blocks)} blocks miss stable blockguide field genre_ext.{field}.",
                    fix_target=f"TR.blocks[*].genre_ext.{field}",
                    count=missing,
                )
        return ("block_cider" in strict_blockers), strict_blockers, tier_b_drifts

    alias_only_blocks = 0
    faction_alias_blocks = 0
    canonical_ext_missing = 0
    for block in blocks:
        genre_ext = block.get("genre_ext")
        martial_ext = block.get("martial_ext")
        if not isinstance(genre_ext, dict):
            canonical_ext_missing += 1
            if isinstance(martial_ext, dict):
                alias_only_blocks += 1
        if isinstance(martial_ext, dict) and not is_present(get_nested(genre_ext or {}, "faction_position")) and is_present(
            get_nested(martial_ext, "faction_status")
        ):
            faction_alias_blocks += 1
    counts["alias_only_martial_ext_blocks"] = alias_only_blocks
    counts["missing_canonical_genre_ext_blocks"] = canonical_ext_missing
    counts["faction_status_alias_blocks"] = faction_alias_blocks

    if alias_only_blocks:
        severity = "alias" if untouched_historical and not forward_strict else "blocker"
        if severity == "blocker":
            strict_blockers.append("genre_ext")
        add_finding(
            findings,
            severity,
            "TR-MARTIAL-ALIAS",
            f"{alias_only_blocks}/{len(blocks)} blocks write martial_ext without canonical forward genre_ext.",
            fix_target="TR.blocks[*].genre_ext",
            count=alias_only_blocks,
        )

    required_fields = [
        "realm_before",
        "realm_after",
        "internal_energy_before",
        "internal_energy_after",
        "faction_position",
        "jianghu_reputation",
        "enemy_pressure",
    ]
    resolved_missing = count_blocks_missing_resolved_fields(
        blocks,
        required_fields,
        allow_alias=untouched_historical,
        alias_field_map={"faction_position": "faction_status"},
    )
    for field, missing in resolved_missing.items():
        counts[f"missing_{field}"] = missing
        if missing:
            strict_blockers.append(field)
            add_finding(
                findings,
                "blocker",
                f"TR-{field.upper()}",
                f"{missing}/{len(blocks)} blocks miss required wuxguide field {field}.",
                fix_target=f"TR.blocks[*].genre_ext.{field}",
                count=missing,
            )

    block_cider_missing = 0
    for block in blocks:
        genre_ext = block.get("genre_ext")
        if not isinstance(genre_ext, dict) or not isinstance(genre_ext.get("block_cider"), dict):
            block_cider_missing += 1
    counts["missing_block_cider"] = block_cider_missing
    if block_cider_missing:
        strict_blockers.append("block_cider")
        add_finding(
            findings,
            "blocker" if forward_strict or not untouched_historical else "drift",
            "TR-BLOCK-CIDER",
            f"canonical genre_ext.block_cider is missing in {block_cider_missing}/{len(blocks)} blocks.",
            fix_target="TR.blocks[*].genre_ext.block_cider",
            count=block_cider_missing,
        )

    tier_b_missing = count_blocks_missing_resolved_fields(blocks, ["opponent.name"], allow_alias=untouched_historical)
    counts["tier_b_missing_opponent_name"] = tier_b_missing["opponent.name"]
    if tier_b_missing["opponent.name"]:
        tier_b_drifts.append("opponent.name")
        add_finding(
            findings,
            "drift",
            "TR-TIERB-OPPONENT",
            f"{tier_b_missing['opponent.name']}/{len(blocks)} blocks miss stable wuxguide field opponent.name.",
            fix_target="TR.blocks[*].genre_ext.opponent.name",
            count=tier_b_missing["opponent.name"],
        )

    if faction_alias_blocks:
        severity = "alias" if untouched_historical and not forward_strict else "blocker"
        if severity == "blocker":
            strict_blockers.append("faction_position_alias")
        add_finding(
            findings,
            severity,
            "TR-FACTION-ALIAS",
            f"{faction_alias_blocks}/{len(blocks)} blocks still write faction_status instead of canonical faction_position.",
            fix_target="TR.blocks[*].genre_ext.faction_position",
            count=faction_alias_blocks,
        )
    return ("block_cider" in strict_blockers), strict_blockers, tier_b_drifts


def inspect_bi_family_sections(
    *,
    master_bible: dict[str, Any],
    family: str,
    findings: list[Finding],
    counts: dict[str, int],
) -> list[str]:
    blockers: list[str] = []
    required_sections = BI_FAMILY_CORE[family]
    missing_sections = 0
    for section in required_sections:
        value = master_bible.get(section)
        if not is_present(value):
            missing_sections += 1
            blockers.append(section)
            add_finding(
                findings,
                "blocker",
                f"BI-SECTION-{section.upper()}",
                f"MasterBible.{section} is missing or blank.",
                fix_target=f"BI.MasterBible.{section}",
            )
    counts["missing_bi_family_sections"] = missing_sections
    return blockers


def inspect_promoted_slots(
    *,
    family: str,
    phase0_data: Any,
    master_bible: dict[str, Any],
    findings: list[Finding],
    counts: dict[str, int],
) -> list[str]:
    drifts: list[str] = []
    promoted = BLOCKGUIDE_PROMOTED_SLOTS if family == "blockguide" else WUXGUIDE_PROMOTED_SLOTS
    missing_promoted = 0
    for source_key, bi_path, fix_target in promoted:
        if not deep_key_present(phase0_data, source_key):
            continue
        if not is_present(get_nested(master_bible, bi_path)):
            missing_promoted += 1
            drifts.append(source_key)
            add_finding(
                findings,
                "drift",
                f"BI-PROMOTED-{source_key.upper()}",
                f"Phase0 carries {source_key}, but canonical BI slot {bi_path} is blank.",
                fix_target=fix_target,
            )
    counts["missing_promoted_bi_slots"] = missing_promoted

    if family == "blockguide":
        root_capital_curve = get_nested(master_bible, "capital_curve")
        canonical_capital_curve = get_nested(master_bible, "AssetLibrary.CapitalCurve")
        if is_present(root_capital_curve) and not is_present(canonical_capital_curve):
            drifts.append("capital_curve_alias")
            add_finding(
                findings,
                "alias",
                "BI-CAPITAL-CURVE-ALIAS",
                "root-level capital_curve exists without canonical MasterBible.AssetLibrary.CapitalCurve.",
                fix_target="BI.MasterBible.AssetLibrary.CapitalCurve",
            )
    return drifts


def derive_tier_b_status(findings: list[Finding], counts: dict[str, int]) -> str:
    severities = {finding.severity for finding in findings}
    if (
        "alias" in severities
        or counts.get("missing_promoted_bi_slots", 0) >= 3
        or counts.get("missing_bi_family_sections", 0) > 0
    ):
        return "drifting"
    if "drift" in severities:
        return "partial"
    return "normalized"


def derive_schema_status(
    *,
    blockers: list[Finding],
    aliases: list[Finding],
    warnings: list[Finding],
    open_migration_debt: bool,
) -> str:
    if open_migration_debt:
        return "pass-with-migration-debt"
    if blockers:
        return "fail"
    if aliases or warnings:
        return "alias-pass"
    return "pass"


def build_report(
    *,
    work_id: str,
    bible_path: Path | None,
    treatment_path: Path | None,
    global_state: str | None,
    overrides: dict[str, str],
    reference_only_work_ids: set[str],
) -> PairNormalizationReport:
    bi_data = load_json(bible_path)
    tr_data = load_json(treatment_path)
    consumability = inspect_pair(bible_path=bible_path, treatment_path=treatment_path, work_key=work_id)

    family = infer_family(bi_data, tr_data, work_id)
    reference_only = work_id in reference_only_work_ids
    operational_state, operational_state_source = infer_operational_state(
        work_id,
        bible_path=bible_path,
        treatment_path=treatment_path,
        reference_only=reference_only,
        global_state=global_state,
        overrides=overrides,
    )
    untouched_historical = operational_state == "untouched_historical_live_pair"
    forward_strict = operational_state in {"new_live_pair", "newly_touched_live_pair", "regenerated_pair", "promotion_target_pair"}

    findings: list[Finding] = []
    notes: list[str] = list(consumability.notes)
    counts: dict[str, int] = {"block_count": consumability.canonical_block_count}

    if bi_data is None:
        add_finding(findings, "blocker", "PAIR-BI-MISSING", "BI file is missing.", fix_target="BI file")
    if tr_data is None:
        add_finding(findings, "blocker", "PAIR-TR-MISSING", "TR file is missing.", fix_target="TR file")
    if not consumability.normalized_pair_canonical_valid:
        add_finding(
            findings,
            "blocker",
            "PAIR-NORMALIZED-CANONICAL",
            "Normalized pair still fails the current canonical consumability validator.",
            fix_target="pair canonical contract",
        )

    tr_blocks = normalize_treatment_blocks(tr_data)
    canonical_bi, _bi_norm_warnings = normalize_bible_to_canonical_view(bi_data, treatment=tr_data) if bi_data is not None else ({}, [])
    master_bible = get_effective_bible_root(canonical_bi)

    for path, fix_target in BLOCK_CORE_PATHS:
        missing = count_missing_blocks(tr_blocks, path)
        counts[f"missing_{path.replace('.', '_')}"] = missing
        if missing:
            add_finding(
                findings,
                "blocker",
                f"TR-CORE-{path.replace('.', '-').upper()}",
                f"{missing}/{len(tr_blocks)} blocks miss required core field {path}.",
                fix_target=fix_target,
                count=missing,
            )

    tr_authority_chain = tr_data.get("_authority_chain") if isinstance(tr_data, dict) else None
    tr_authority_sources = tr_data.get("_authority_sources") if isinstance(tr_data, dict) else None
    bi_authority_chain = canonical_bi.get("_authority_chain") if isinstance(canonical_bi, dict) else None
    bi_authority_sources = canonical_bi.get("_authority_sources") if isinstance(canonical_bi, dict) else None

    if isinstance(tr_data, dict):
        if not is_present(tr_data.get("_work_id")):
            add_finding(findings, "warning" if untouched_historical else "blocker", "TR-META-WORK-ID", "TR top-level _work_id is missing.", fix_target="TR._work_id")
        if not is_present(tr_authority_chain):
            if is_present(tr_authority_sources) and untouched_historical:
                add_finding(findings, "alias", "TR-META-AUTHORITY-ALIAS", "TR still uses _authority_sources instead of canonical _authority_chain.", fix_target="TR._authority_chain")
            else:
                add_finding(findings, "blocker", "TR-META-AUTHORITY", "TR canonical _authority_chain is missing.", fix_target="TR._authority_chain")
        if family != "blockguide" and not is_present(tr_data.get("_family")):
            add_finding(findings, "blocker", "TR-META-FAMILY", f"TR _family is required for {family} pairs.", fix_target="TR._family")
        if not is_present(tr_data.get("_phase0_ref")):
            add_finding(findings, "warning" if untouched_historical else "blocker", "TR-META-PHASE0-REF", "TR _phase0_ref is missing.", fix_target="TR._phase0_ref")

    if isinstance(canonical_bi, dict):
        if not is_present(canonical_bi.get("_work_id")):
            add_finding(findings, "warning" if untouched_historical else "blocker", "BI-META-WORK-ID", "BI top-level _work_id is missing.", fix_target="BI._work_id")
        if not is_present(bi_authority_chain):
            if is_present(bi_authority_sources) and untouched_historical:
                add_finding(findings, "alias", "BI-META-AUTHORITY-ALIAS", "BI still uses _authority_sources instead of canonical _authority_chain.", fix_target="BI._authority_chain")
            else:
                add_finding(findings, "blocker", "BI-META-AUTHORITY", "BI canonical _authority_chain is missing.", fix_target="BI._authority_chain")
        if family != "blockguide" and not is_present(canonical_bi.get("_family")):
            add_finding(findings, "blocker", "BI-META-FAMILY", f"BI _family is required for {family} pairs.", fix_target="BI._family")
        source_severity = "warning" if untouched_historical or operational_state == "newly_touched_live_pair" else "blocker"
        if not is_present(canonical_bi.get("_source_phase0")):
            add_finding(findings, source_severity, "BI-META-SOURCE-PHASE0", "BI _source_phase0 is missing.", fix_target="BI._source_phase0")
        if not is_present(canonical_bi.get("_source_tr")):
            add_finding(findings, source_severity, "BI-META-SOURCE-TR", "BI _source_tr is missing.", fix_target="BI._source_tr")

    metadata_strings = gather_metadata_strings(tr_data, canonical_bi)
    root_phase0_status, preprocess_authority_available, _root_phase0_exists = resolve_phase0_status(work_id, metadata_strings, untouched_historical)
    if root_phase0_status == "preprocess-fallback-alias-pass":
        add_finding(findings, "alias", "PHASE0-FALLBACK", "Root treatments/phase0 file is missing, but historical preprocess authority fallback is available.", fix_target=f"treatments/phase0/{work_id}_phase0_design.json")
    elif root_phase0_status == "missing-root-phase0":
        add_finding(
            findings,
            "blocker",
            "PHASE0-MISSING",
            "Canonical root treatments/phase0 file is missing and no alias-pass fallback is available.",
            fix_target=f"treatments/phase0/{work_id}_phase0_design.json",
        )

    block_cider_gap, strict_family_blockers, tier_b_drifts = inspect_family_fields(
        blocks=tr_blocks,
        family=family,
        untouched_historical=untouched_historical,
        forward_strict=forward_strict,
        findings=findings,
        counts=counts,
    )
    bi_section_blockers = inspect_bi_family_sections(master_bible=master_bible, family=family, findings=findings, counts=counts)
    phase0_data = load_json(PHASE0_DIR / f"{work_id}_phase0_design.json")
    promoted_drifts = inspect_promoted_slots(
        family=family,
        phase0_data=phase0_data,
        master_bible=master_bible,
        findings=findings,
        counts=counts,
    )
    (
        naming_surface_status,
        naming_surface_resolution,
        canonical_title,
        observed_bi_title,
    ) = inspect_naming_surface(
        phase0_data=phase0_data,
        canonical_bi=canonical_bi,
        untouched_historical=untouched_historical,
        findings=findings,
        counts=counts,
        notes=notes,
    )

    blocker_findings = [finding for finding in findings if finding.severity == "blocker"]
    alias_findings = [finding for finding in findings if finding.severity == "alias"]
    warning_findings = [finding for finding in findings if finding.severity == "warning"]

    other_non_block_cider_blockers = [
        finding
        for finding in blocker_findings
        if finding.fix_target not in {"TR.blocks[*].genre_ext.block_cider", "pair canonical contract"}
        and finding.code not in {"TR-BLOCK-CIDER", "PAIR-NORMALIZED-CANONICAL"}
    ]
    open_migration_debt = (
        untouched_historical
        and block_cider_gap
        and not other_non_block_cider_blockers
        and not bi_section_blockers
        and root_phase0_status != "missing-root-phase0"
        and len(strict_family_blockers) == 1
    )

    if open_migration_debt and consumability.verdicts["pair_consumability"] == "pass":
        pair_consumability = "pass_with_migration_debt"
    else:
        pair_consumability = consumability.verdicts["pair_consumability"]

    evidence_mode = "legacy_read" if open_migration_debt else "serialized_canonical"
    schema_status = derive_schema_status(blockers=blocker_findings, aliases=alias_findings, warnings=warning_findings, open_migration_debt=open_migration_debt)
    strict_tier_a_status = "fail" if blocker_findings or alias_findings or block_cider_gap else "pass"
    tier_b_status = derive_tier_b_status(findings, counts)
    required_fix_targets = sorted({finding.fix_target for finding in findings if finding.fix_target})
    alias_refresh_eligible = schema_status == "pass" and not reference_only
    active_baseline_eligible = alias_refresh_eligible and operational_state != "promotion_target_pair"

    notes.extend(consumability.bible_normalization_warnings[:2])
    notes.extend(consumability.treatment_normalization_warnings[:2])
    if promoted_drifts:
        notes.append(f"phase0-promoted-slot drift: {', '.join(promoted_drifts[:3])}")
    if tier_b_drifts:
        notes.append(f"tier-b drift: {', '.join(tier_b_drifts[:3])}")

    return PairNormalizationReport(
        work_id=work_id,
        family=family,
        bible_path=str(bible_path) if bible_path else None,
        treatment_path=str(treatment_path) if treatment_path else None,
        reference_only=reference_only,
        operational_state=operational_state,
        operational_state_source=operational_state_source,
        pair_consumability=pair_consumability,
        strict_tier_a_status=strict_tier_a_status,
        tier_b_status=tier_b_status,
        schema_status=schema_status,
        evidence_mode=evidence_mode,
        open_migration_debt=open_migration_debt,
        alias_refresh_eligible=alias_refresh_eligible,
        active_baseline_eligible=active_baseline_eligible,
        root_phase0_status=root_phase0_status,
        preprocess_authority_available=preprocess_authority_available,
        naming_surface_status=naming_surface_status,
        naming_surface_resolution=naming_surface_resolution,
        canonical_title=canonical_title,
        observed_bi_title=observed_bi_title,
        raw_pair_canonical_valid=consumability.pair_canonical_valid,
        normalized_pair_canonical_valid=consumability.normalized_pair_canonical_valid,
        counts=counts,
        required_fix_targets=required_fix_targets,
        findings=sort_findings(findings),
        notes=notes[:6],
    )


def collect_live_pairs(bible_dir: Path, treatment_dir: Path) -> list[tuple[str, Path | None, Path | None]]:
    bible_paths = sorted(path for path in bible_dir.glob("*.json") if path.is_file())
    treatment_paths = sorted(path for path in treatment_dir.glob("*.json") if path.is_file())

    treatments_by_key: dict[str, list[Path]] = {}
    for path in treatment_paths:
        work_key = infer_treatment_work_key(path)
        if work_key is None:
            continue
        treatments_by_key.setdefault(work_key, []).append(path)

    pairs: list[tuple[str, Path | None, Path | None]] = []
    matched_keys: set[str] = set()
    for bible_path in bible_paths:
        work_key = infer_bible_work_key(bible_path)
        treatment_path = choose_preferred_treatment(treatments_by_key.get(work_key, []))
        if treatment_path is not None:
            matched_keys.add(work_key)
        pairs.append((work_key, bible_path, treatment_path))

    for work_key, candidates in sorted(treatments_by_key.items()):
        if work_key in matched_keys:
            continue
        pairs.append((work_key, None, choose_preferred_treatment(candidates)))
    return pairs


def parse_state_overrides(raw_values: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for raw in raw_values:
        if "=" not in raw:
            raise ValueError(f"Invalid --state-override '{raw}'. Expected work_id=state.")
        work_id, state = raw.split("=", 1)
        normalized = normalize_work_id(work_id)
        state = state.strip()
        if state not in STATE_CHOICES:
            raise ValueError(f"Invalid state '{state}' for --state-override.")
        overrides[normalized] = state
    return overrides


def load_registry_state_overrides() -> dict[str, str]:
    if not OPERATIONAL_REGISTRY_JSON.is_file():
        return {}
    try:
        data = json.loads(OPERATIONAL_REGISTRY_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    entries = data.get("pairs")
    if not isinstance(entries, list):
        return {}
    overrides: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        work_id = normalize_work_id(as_text(entry.get("work_id")))
        state = as_text(entry.get("operational_state"))
        if work_id and state in STATE_CHOICES:
            overrides[work_id] = state
    return overrides


def render_text(reports: list[PairNormalizationReport]) -> str:
    lines = [f"Scanned {len(reports)} pair(s)"]
    for report in reports:
        lines.append(
            " | ".join(
                [
                    f"{report.work_id}",
                    f"family={report.family}",
                    f"state={report.operational_state}",
                    f"schema={report.schema_status}",
                    f"tierA={report.strict_tier_a_status}",
                    f"tierB={report.tier_b_status}",
                    f"naming={report.naming_surface_status}",
                    f"evidence={report.evidence_mode}",
                    f"migration_debt={'yes' if report.open_migration_debt else 'no'}",
                ]
            )
        )
        if report.findings:
            for finding in top_findings(report.findings):
                count = f" ({finding.count})" if finding.count is not None else ""
                lines.append(f"  - [{finding.severity}] {finding.code}{count}: {finding.message}")
        if report.required_fix_targets:
            lines.append(f"  fixes: {', '.join(report.required_fix_targets[:6])}")
        if report.notes:
            lines.append(f"  notes: {' | '.join(report.notes[:3])}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run production-pair normalization audits against live BI/TR pairs.")
    parser.add_argument("--bible", type=Path, help="Single BI JSON path")
    parser.add_argument("--treatment", type=Path, help="Single TR JSON path")
    parser.add_argument("--bible-dir", type=Path, default=LIVE_BIBLE_DIR, help="Live BI directory")
    parser.add_argument("--treatment-dir", type=Path, default=LIVE_TREATMENT_DIR, help="Live TR directory")
    parser.add_argument("--work-id", action="append", default=[], help="Restrict scan to one or more normalized work ids")
    parser.add_argument("--state", choices=STATE_CHOICES, help="Apply one operational state to all targeted pairs")
    parser.add_argument(
        "--state-override",
        action="append",
        default=[],
        help="Override operational state per work id. Format: work_id=state",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        cli_overrides = parse_state_overrides(args.state_override)
    except ValueError as exc:
        parser.error(str(exc))
    overrides = load_registry_state_overrides()
    overrides.update(cli_overrides)

    reference_only_work_ids = load_reference_only_work_ids()

    if args.bible or args.treatment:
        pairs = [
            (
                infer_bible_work_key(args.bible) if args.bible else infer_treatment_work_key(args.treatment) or "unknown",
                args.bible,
                args.treatment,
            )
        ]
    else:
        pairs = collect_live_pairs(args.bible_dir, args.treatment_dir)

    if args.work_id:
        wanted = {normalize_work_id(value) for value in args.work_id}
        pairs = [pair for pair in pairs if pair[0] in wanted]

    reports = [
        build_report(
            work_id=work_id,
            bible_path=bible_path,
            treatment_path=treatment_path,
            global_state=args.state,
            overrides=overrides,
            reference_only_work_ids=reference_only_work_ids,
        )
        for work_id, bible_path, treatment_path in pairs
    ]

    if args.json:
        print(json.dumps({"results": [asdict(report) for report in reports]}, ensure_ascii=False, indent=2))
    else:
        print(render_text(reports))

    return 1 if any(report.schema_status == "fail" for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
