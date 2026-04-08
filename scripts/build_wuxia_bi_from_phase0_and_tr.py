#!/usr/bin/env python3
"""Build a wuxia-family BI JSON from phase0 and treatment draft inputs."""
# utf8-hygiene: allow-file rationale: this builder intentionally contains literal regex patterns for block-meta leak detection.

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

from modules.core.project_support import default_external_pov_insert_policy, normalize_external_pov_insert_policy
from modules.core.response_schemas import validate_bible_structure
from modules.core.stage0_handoff import (
    build_plot_roadmap_from_treatment,
    canonicalize_bible_payload,
    canonicalize_treatment_payload,
)

GARBLED_TOKENS = ("\ufffd",)
REQUIRED_PHASE0_SECTIONS = ("project", "setting", "protagonist", "phase0_design")
REQUIRED_PHASE0_FIELDS = ("arcs", "npc_timeline", "foreshadow_map", "opponent_transition_plan")
BLANKISH_VALUES = {"", "none", "null", "n/a", "na", "-", "unknown"}
BLOCK_META_REF_RE = re.compile(
    r"(?<![A-Za-z])(?:B\d{1,3}(?:\s*[~→\-]\s*B?\d{1,3})*|Block\s+\d{1,3}|블록\s*\d{1,3})(?:에서의|에서|와의|과의|와|과|보다|의|으로|로|은|는|이|가|를|을|에|도|만)?(?![A-Za-z])",
    re.IGNORECASE,
)
ALLOWED_BLOCK_META_KEYS = {
    "block",
    "block_id",
    "ref",
    "recovery_block",
    "first_block",
    "last_confirmed_block",
    "block_acquired",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def relative_posix(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def derive_work_id_from_phase0_path(path: Path) -> str:
    stem = path.stem
    if stem.endswith("_phase0_design"):
        return stem[: -len("_phase0_design")]
    return stem


def build_authority_chain(work_id: str, *, phase0_path: Path, draft_path: Path) -> list[str]:
    candidates = [
        ROOT / "material_ssot" / "20_pitch" / "canon" / f"{work_id}.md",
        ROOT / "treatments" / "preprocess" / work_id / "source_manifest.json",
        ROOT / "treatments" / "preprocess" / work_id / "material_bundle_summary.json",
        ROOT / "treatments" / "preprocess" / work_id / "profile_lock.json",
        ROOT / "treatments" / "preprocess" / work_id / "phase0_ready_snapshot.json",
        phase0_path,
        draft_path,
    ]
    return [relative_posix(path) for path in candidates if path.is_file()]


def ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def is_blankish(value: Any) -> bool:
    return as_text(value).lower() in BLANKISH_VALUES


def get_nested(obj: Any, path: str, default: Any = "") -> Any:
    current = obj
    for part in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(part)
    return current if current is not None else default


def first_text(obj: Any, *paths: str, default: str = "") -> str:
    for path in paths:
        value = as_text(get_nested(obj, path))
        if value:
            return value
    return default


def first_number(obj: Any, *paths: str, default: int = 0) -> int:
    for path in paths:
        value = get_nested(obj, path, None)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        text = as_text(value)
        if text.lstrip("+-").isdigit():
            return int(text)
    return default


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def strip_block_meta_refs(text: str) -> str:
    if not BLOCK_META_REF_RE.search(text):
        return text.strip()
    cleaned = BLOCK_META_REF_RE.sub("", text)
    cleaned = re.sub(r"(^|\s)(?:와 같은|과 달리|달리|보다 빠르게|보다|에서의|에서|와의|과의|와|과)\s+", " ", cleaned)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    cleaned = re.sub(r"\s*([→~\-])\s*", r" \1 ", cleaned)
    cleaned = re.sub(r"(?:\s+[→~\-]){2,}", " →", cleaned)
    cleaned = re.sub(r"^[\s,;:→~\-]+|[\s,;:→~\-]+$", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
    return cleaned.strip()


def sanitize_bi_value(value: Any, parent_key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {key: sanitize_bi_value(item, key) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_bi_value(item, parent_key) for item in value]
    if isinstance(value, str):
        if parent_key in ALLOWED_BLOCK_META_KEYS:
            return value.strip()
        return strip_block_meta_refs(value)
    return value


def parse_int(value: Any, default: int = 0) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = as_text(value).replace(",", "")
    if text.lstrip("+-").isdigit():
        return int(text)
    return default


def detect_genre_code(project: dict[str, Any]) -> str:
    format_text = first_text(project, "format", default="wuxia")
    lowered = format_text.lower()
    if any(token in lowered for token in ("wuxia", "murim", "jianghu", "xianxia")):
        return "wuxia"
    if any(token in format_text for token in ("무협", "선협", "강호", "문파")):
        return "wuxia"
    return lowered or "wuxia"


def build_faction_map(protagonist: dict[str, Any], setting: dict[str, Any], phase0_design: dict[str, Any]) -> dict[str, Any]:
    protagonist_faction = first_text(
        protagonist,
        "faction",
        "sect",
        "clan",
        default=first_text(
            setting,
            "starter_faction.name",
            "starter_sect.name",
            "starter_clan.name",
            "starter_group.name",
            default="독행",
        ),
    )
    enemies = unique(
        [
            first_text(entry, "faction")
            for entry in ensure_list(phase0_design.get("opponent_transition_plan"))
            if first_text(entry, "faction")
        ]
    )
    if not enemies:
        enemies = unique(
            [
                as_text(name)
                for arc in ensure_list(phase0_design.get("arcs"))
                for name in ensure_list(arc.get("main_opponents"))
                if as_text(name)
            ]
        )
    allies = unique(
        [
            as_text(npc.get("name"))
            for npc in ensure_list(phase0_design.get("npc_timeline"))
            if as_text(npc.get("name")) and any(token in as_text(npc.get("role")) for token in ("동료", "사형", "사매", "우군", "가족", "호법"))
        ]
    )
    neutrals = unique(
        [
            as_text(npc.get("name"))
            for npc in ensure_list(phase0_design.get("npc_timeline"))
            if as_text(npc.get("name")) and as_text(npc.get("name")) not in allies
        ]
    )
    return {
        "protagonist_faction": protagonist_faction,
        "allies": allies,
        "enemies": enemies,
        "neutral": neutrals,
    }


def build_treasures(
    protagonist: dict[str, Any],
    setting: dict[str, Any],
    phase0_design: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    treasures: list[dict[str, str]] = []
    for item in ensure_list(get_nested(protagonist, "inventory")):
        text = as_text(item)
        if text:
            treasures.append({"name": text, "role": "inventory", "status": "active"})
    for item in ensure_list(get_nested(protagonist, "martial_arts")):
        text = as_text(item)
        if text:
            treasures.append({"name": text, "role": "martial_art", "status": "active"})
    for path, role in (("equipment", "equipment"), ("starter_treasures", "starter_asset"), ("starter_artifacts", "starter_asset")):
        value = get_nested(protagonist if path == "equipment" else setting, path)
        for item in ensure_list(value):
            text = as_text(item.get("name") if isinstance(item, dict) else item)
            if text:
                treasures.append({"name": text, "role": role, "status": "active"})
    for item in ensure_list((phase0_design or {}).get("treasure_path")):
        if not isinstance(item, dict):
            continue
        text = as_text(item.get("treasure"))
        if text:
            status = as_text(item.get("arc")) or as_text(item.get("acquisition_block")) or "planned"
            treasures.append({"name": text, "role": "treasure_path", "status": status})
    for item in ensure_list((phase0_design or {}).get("martial_art_path")):
        if not isinstance(item, dict):
            continue
        text = as_text(item.get("art"))
        if text:
            status = as_text(item.get("arc")) or as_text(item.get("acquisition")) or "planned"
            treasures.append({"name": text, "role": "martial_art_path", "status": status})
    return treasures


def _ext_text(block: dict[str, Any], field: str, default: str = "") -> str:
    """Resolve a field from martial_ext (wuxguide) or genre_ext (blockguide)."""
    return first_text(block, f"martial_ext.{field}", f"genre_ext.{field}", default=default)


def _ext_nested(block: dict[str, Any], field: str, default: Any = "") -> Any:
    """Resolve a nested field from martial_ext or genre_ext."""
    val = get_nested(block, f"martial_ext.{field}")
    if val not in (None, ""):
        return val
    return get_nested(block, f"genre_ext.{field}", default)


def _resolve_reputation(raw: Any) -> str:
    """Handle jianghu_reputation that may be a dict {before, after} or a plain string."""
    if isinstance(raw, dict):
        return as_text(raw.get("after")) or as_text(raw.get("before")) or ""
    return as_text(raw)


def _resolve_faction_position(raw: Any) -> str:
    """Handle faction_status that may be a dict {affiliation, rank, ...} or a plain string."""
    if isinstance(raw, dict):
        rank = as_text(raw.get("rank"))
        affiliation = as_text(raw.get("affiliation"))
        if rank and affiliation:
            return f"{rank} ({affiliation})"
        return rank or affiliation or ""
    return as_text(raw)


def build_treatment_snapshot(treatment_blocks: list[dict[str, Any]]) -> dict[str, Any]:
    last_block = treatment_blocks[-1]

    # Collect martial art gains across all blocks (wuxguide: martial_arts_acquired, blockguide: martial_art_gain)
    recent_martial_gains: list[str] = []
    recent_artifact_gains: list[str] = []
    for block in treatment_blocks:
        # martial_arts_acquired may be a list of strings
        acq = _ext_nested(block, "martial_arts_acquired") or _ext_nested(block, "martial_art_gain")
        if isinstance(acq, list):
            recent_martial_gains.extend(as_text(item) for item in acq if not is_blankish(item))
        elif not is_blankish(acq):
            recent_martial_gains.append(as_text(acq))
        art = _ext_nested(block, "artifact_or_manual_gain")
        if not is_blankish(art) and as_text(art).lower() not in {"none", "no", "none."}:
            if isinstance(art, list):
                recent_artifact_gains.extend(as_text(item) for item in art if not is_blankish(item))
            else:
                recent_artifact_gains.append(as_text(art))

    recent_martial_gains = unique(recent_martial_gains)
    recent_artifact_gains = unique(recent_artifact_gains)

    rep_raw = _ext_nested(last_block, "jianghu_reputation", default="unknown")
    faction_raw = _ext_nested(last_block, "faction_status") or _ext_nested(last_block, "faction_position")

    return {
        "current_realm": _ext_text(last_block, "realm_after", default="") or _ext_text(last_block, "realm_before", default="novice"),
        "internal_energy": first_number(last_block, "martial_ext.internal_energy_after", "genre_ext.internal_energy_after", default=10),
        "jianghu_reputation": _resolve_reputation(rep_raw),
        "faction_position": _resolve_faction_position(faction_raw) or "unsettled",
        "enemy_pressure": _ext_text(last_block, "enemy_pressure", default="active"),
        "current_opponent": _ext_text(last_block, "opponent.name", default=""),
        "recent_martial_gains": recent_martial_gains,
        "recent_artifact_gains": recent_artifact_gains,
        "last_confirmed_block": len(treatment_blocks),
    }


def extract_realm_history(treatment_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract realm transition history from TR blocks (harness §2.2 realm_history)."""
    history: list[dict[str, Any]] = []
    prev_realm = ""
    for i, block in enumerate(treatment_blocks):
        realm_after = _ext_text(block, "realm_after")
        if realm_after and realm_after != prev_realm:
            event = as_text(block.get("title", ""))
            history.append({"block": i + 1, "realm": realm_after, "event": event})
            prev_realm = realm_after
    return history


def extract_injury_log(treatment_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract injury log from TR blocks (harness §2.2 injury_log)."""
    log: list[dict[str, Any]] = []
    for i, block in enumerate(treatment_blocks):
        inj = _ext_nested(block, "injury_status")
        if isinstance(inj, dict):
            change = as_text(inj.get("change", ""))
            if change and change not in ("변동 없음", "없음", ""):
                current = as_text(inj.get("current", ""))
                log.append({"block": i + 1, "injury": current, "change": change, "recovery_block": None})
    # Try to link recoveries: if a later block says "정상" or "완전 회복", mark previous injury's recovery_block
    for idx, entry in enumerate(log):
        if "정상" in entry.get("change", "") or "회복" in entry.get("change", ""):
            # Find the most recent non-recovered injury before this
            for prev_idx in range(idx - 1, -1, -1):
                if log[prev_idx]["recovery_block"] is None and "정상" not in log[prev_idx].get("change", ""):
                    log[prev_idx]["recovery_block"] = entry["block"]
                    break
    return log


def extract_kill_log(treatment_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract kill log from TR blocks (harness §2.2 kill_log)."""
    log: list[dict[str, Any]] = []
    for i, block in enumerate(treatment_blocks):
        kc = _ext_nested(block, "kill_count")
        if isinstance(kc, int) and kc > 0:
            target = _ext_text(block, "opponent.name", default="불명")
            method = _ext_text(block, "strategy", default="불명")
            log.append({"block": i + 1, "target": target, "method": method})
    return log


def extract_martial_arts_final(
    treatment_blocks: list[dict[str, Any]], phase0_design: dict[str, Any] | None = None
) -> list[dict[str, str]]:
    """Extract final martial arts inventory from all TR blocks."""
    arts: list[dict[str, str]] = []
    seen: set[str] = set()
    for art in ensure_list((phase0_design or {}).get("martial_art_path")):
        if not isinstance(art, dict):
            continue
        art_name = as_text(art.get("name"))
        if not art_name:
            continue
        key = art_name.split("(")[0].strip()
        if key in seen:
            continue
        seen.add(key)
        arts.append(
            {
                "name": art_name,
                "origin": strip_block_meta_refs(as_text(art.get("origin"))) or "전승 경로 기록",
                "proficiency": "습득",
            }
        )
    for i, block in enumerate(treatment_blocks):
        acq = _ext_nested(block, "martial_arts_acquired") or _ext_nested(block, "martial_art_gain")
        items: list[str] = []
        if isinstance(acq, list):
            items = [as_text(a) for a in acq if not is_blankish(a)]
        elif not is_blankish(acq):
            items = [as_text(acq)]
        for art_name in items:
            # Normalize: take the part before any parenthetical for dedup
            key = art_name.split("(")[0].strip()
            if key not in seen:
                seen.add(key)
                arts.append({
                    "name": art_name,
                    "origin": "TR 습득",
                    "proficiency": "습득",
                })
    return arts


def extract_faction_history(treatment_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract faction changes from TR blocks."""
    history: list[dict[str, Any]] = []
    prev_affiliation = ""
    for i, block in enumerate(treatment_blocks):
        fs = _ext_nested(block, "faction_status")
        if isinstance(fs, dict):
            aff = as_text(fs.get("affiliation", ""))
            if aff and aff != prev_affiliation:
                history.append({
                    "block": i + 1,
                    "faction": aff,
                    "role": as_text(fs.get("rank", "")),
                    "event": as_text(fs.get("change", "")),
                })
                prev_affiliation = aff
    return history


def _build_martial_status(
    realm: str,
    snapshot: dict[str, Any],
    treatment_blocks: list[dict[str, Any]],
    phase0_design: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Harness §2.1 martial_status nested structure."""
    return {
        "realm": realm,
        "realm_history": extract_realm_history(treatment_blocks),
        "internal_energy": snapshot.get("internal_energy", 10),
        "martial_arts": extract_martial_arts_final(treatment_blocks, phase0_design),
        "injury_log": extract_injury_log(treatment_blocks),
        "kill_log": extract_kill_log(treatment_blocks),
    }


def _build_faction_status(
    faction_map: dict[str, Any], snapshot: dict[str, Any], treatment_blocks: list[dict[str, Any]]
) -> dict[str, Any]:
    """Harness §2.1 faction_status nested structure."""
    return {
        "current_faction": as_text(snapshot.get("faction_position")) or faction_map["protagonist_faction"],
        "faction_history": extract_faction_history(treatment_blocks),
        "ally_factions": faction_map.get("allies", []),
        "enemy_factions": faction_map.get("enemies", []),
    }


def _build_equipment(treasures: list[dict[str, str]], snapshot: dict[str, Any]) -> dict[str, Any]:
    """Harness §2.1 equipment nested structure."""
    weapons = [
        {"name": item["name"], "grade": "범철", "origin": item.get("role", "")}
        for item in treasures
        if item.get("role") in {"inventory", "equipment"}
    ]
    artifacts = [
        {"name": item["name"], "origin": item.get("role", "")}
        for item in treasures
        if item.get("role") in {"starter_asset", "martial_art"}
    ]
    for art_name in ensure_list(snapshot.get("recent_artifact_gains")):
        if art_name:
            artifacts.append({"name": art_name, "origin": "TR 습득"})
    return {"weapons": weapons, "artifacts": artifacts}


def _build_jianghu_reputation(snapshot: dict[str, Any], protagonist: dict[str, Any]) -> dict[str, Any]:
    """Harness §2.1 jianghu_reputation nested structure."""
    rep = as_text(snapshot.get("jianghu_reputation")) or first_text(protagonist, "reputation", default="무명")
    return {
        "jianghu_title": rep,
        "feared_by": [],
        "trusted_by": [],
        "rumor_state": rep,
    }


def build_martial_hud(
    protagonist: dict[str, Any],
    setting: dict[str, Any],
    faction_map: dict[str, Any],
    treasures: list[dict[str, str]],
    snapshot: dict[str, Any],
    treatment_blocks: list[dict[str, Any]] | None = None,
    phase0_design: dict[str, Any] | None = None,
) -> dict[str, Any]:
    name = first_text(protagonist, "name", default="주인공")
    alias = first_text(protagonist, "public_image", "alias", default=name)
    realm = as_text(snapshot.get("current_realm")) or first_text(protagonist, "current_realm", "realm", "rank", "status", default="초입")
    injuries = first_text(protagonist, "injuries", "true_weakness", default="경상")
    equipment = unique([item["name"] for item in treasures if item["role"] in {"inventory", "equipment"}] + ensure_list(snapshot.get("recent_artifact_gains")))
    if not equipment:
        equipment = []
    martial_arts = unique([item["name"] for item in treasures if item["role"] == "martial_art"] + ensure_list(snapshot.get("recent_martial_gains")))
    if not martial_arts:
        martial_arts = [first_text(protagonist, "signature_art", "true_strength", default="기본 무공")]
    wealth = first_text(protagonist, "resources", "wealth", "wealth_status", default=first_text(setting, "resource_state", default="빈약"))
    status_tags = unique(
        [
            realm,
            faction_map["protagonist_faction"],
            as_text(snapshot.get("faction_position")),
            as_text(snapshot.get("jianghu_reputation")),
            first_text(protagonist, "status", default="무명"),
        ]
    )
    physical_tags = unique([injuries, "martial-ready" if martial_arts else "unarmed"])
    return {
        "Protagonist": {
            "actual_truth": {
                "name": name,
                "alias": alias,
                "age": first_number(protagonist, "age_at_start", "age", default=20),
                "rank": first_text(protagonist, "status", default=realm),
                "realm": realm,
                "current_realm": realm,
                "internal_energy": snapshot.get("internal_energy", first_number(protagonist, "internal_energy", "energy", "qi", default=10)),
                "mental_method": first_text(protagonist, "mental_method", "core_art", "signature_art", default="기본 심법"),
                "reputation": as_text(snapshot.get("jianghu_reputation")) or first_text(protagonist, "reputation", default="무명"),
                "public_image": alias,
                "equipment": equipment,
                "wealth": wealth,
                "resources": wealth,
                "token": first_text(protagonist, "token", default="없음"),
                "misunderstanding": first_number(protagonist, "misunderstanding", default=0),
                "obsession": first_number(protagonist, "obsession", default=0),
                "current_objective": first_text(protagonist, "initial_goal", default="생존"),
                "mid_term_goal": first_text(protagonist, "mid_goal", default="중간 목표"),
                "final_goal": first_text(protagonist, "final_goal", default="최종 목표"),
                "qi_nature": first_text(protagonist, "qi_nature", default="무색무취"),
                "causal_injuries": injuries,
                "injuries": injuries,
                "faction": faction_map["protagonist_faction"],
                "current_faction_position": as_text(snapshot.get("faction_position")) or faction_map["protagonist_faction"],
                "current_jianghu_reputation": as_text(snapshot.get("jianghu_reputation")) or first_text(protagonist, "reputation", default="무명"),
                "current_enemy_pressure": as_text(snapshot.get("enemy_pressure")) or "active",
                "martial_arts": martial_arts,
                "current_martial_arts": martial_arts,
                "recent_martial_art_gains": ensure_list(snapshot.get("recent_martial_gains")),
                "recent_artifact_gains": ensure_list(snapshot.get("recent_artifact_gains")),
                "inventory": equipment,
                "inventory_counts": {"equipment": len(equipment), "martial_arts": len(martial_arts)},
                "active_pressure_vectors": unique(
                    faction_map["enemies"][:3]
                    + [as_text(snapshot.get("current_opponent")), as_text(snapshot.get("enemy_pressure")), first_text(protagonist, "final_goal")]
                ),
                "status_tags": status_tags,
                "physical_tags": physical_tags,
                "last_confirmed_block": snapshot.get("last_confirmed_block", 0),
                # Harness §2.1 nested structures
                "martial_status": _build_martial_status(realm, snapshot, treatment_blocks or [], phase0_design),
                "faction_status": _build_faction_status(faction_map, snapshot, treatment_blocks or []),
                "equipment": _build_equipment(treasures, snapshot),
                "jianghu_reputation": _build_jianghu_reputation(snapshot, protagonist),
            },
            "public_reputation": {
                "identity": alias,
                "realm": realm,
                "jianghu_title": alias,
                "perceived_power": as_text(snapshot.get("jianghu_reputation")) or first_text(protagonist, "public_image", default="정체 불명"),
                "feared_by": faction_map["enemies"][:3],
                "trusted_by": faction_map["allies"][:3],
                "rumor_state": first_text(protagonist, "rumor_state", default="강호 소문이 막 형성되는 상태"),
            },
        }
    }


def build_key_npcs(project: dict[str, Any], protagonist: dict[str, Any], npc_timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = [
        {
            "name": first_text(protagonist, "name", default="주인공"),
            "role": "주인공",
            "desc": first_text(project, "core_premise", "logline", default="강호 중심축"),
            "first_block": 1,
            "final_status": first_text(protagonist, "final_goal", "status", default="미정"),
        }
    ]
    for npc in npc_timeline:
        out.append(
            {
                "name": as_text(npc.get("name")) or f"NPC {len(out)}",
                "role": as_text(npc.get("role")) or "조연",
                "desc": as_text(npc.get("desc")) or as_text(npc.get("description")) or "Phase0 기반 핵심 NPC",
                "first_block": npc.get("first_block", 1),
                "final_status": as_text(npc.get("final_status")) or "미정",
            }
        )
    return out


def _map_incarnation_type(raw_value: str) -> str:
    normalized = as_text(raw_value)
    if not normalized or normalized.lower() in {"none", "일반"}:
        return "일반"
    if "빙의" in normalized:
        return "빙의자"
    if "환생" in normalized:
        return "환생자"
    if "회귀" in normalized:
        return "회귀자"
    return normalized


def resolve_runtime_identity(
    protagonist: dict[str, Any],
    treatment_blocks: list[dict[str, Any]],
) -> tuple[str, str]:
    world_origin = as_text(protagonist.get("world_origin")) or "원시인"

    explicit_incarnation = _map_incarnation_type(as_text(protagonist.get("incarnation_type")))
    if explicit_incarnation != "일반":
        return world_origin, explicit_incarnation

    for block in treatment_blocks:
        if not isinstance(block, dict):
            continue
        regression_ext = block.get("regression_ext")
        if not isinstance(regression_ext, dict):
            continue
        if regression_ext.get("is_regressor") is True:
            return world_origin, "회귀자"
        mapped = _map_incarnation_type(as_text(regression_ext.get("regression_type")))
        if mapped != "일반":
            return world_origin, mapped

    return world_origin, "일반"


def resolve_runtime_pov_contract(
    protagonist: dict[str, Any],
    setting: dict[str, Any],
    project: dict[str, Any],
) -> tuple[str, str]:
    pov = as_text(protagonist.get("pov")) or as_text(setting.get("pov")) or as_text(project.get("pov")) or "3인칭"
    external_policy = normalize_external_pov_insert_policy(
        as_text(protagonist.get("external_pov_insert_policy"))
        or as_text(setting.get("external_pov_insert_policy"))
        or as_text(project.get("external_pov_insert_policy")),
        primary_pov=pov,
        genre=first_text(project, "format", default=""),
    )
    if not external_policy:
        external_policy = default_external_pov_insert_policy(pov, genre=first_text(project, "format", default=""))
    return pov, external_policy


def build_bible(
    phase0: dict[str, Any],
    treatment_blocks: list[dict[str, Any]],
    *,
    work_id: str,
    source_phase0: str,
    source_tr: str,
    authority_chain: list[str],
) -> dict[str, Any]:
    project = phase0["project"]
    setting = phase0["setting"]
    protagonist = phase0["protagonist"]
    treatment_blocks = build_plot_roadmap_from_treatment(treatment_blocks)
    phase0_design = phase0["phase0_design"]
    faction_map = build_faction_map(protagonist, setting, phase0_design)
    treasures = build_treasures(protagonist, setting, phase0_design)
    snapshot = build_treatment_snapshot(treatment_blocks)
    world_origin, incarnation_type = resolve_runtime_identity(protagonist, treatment_blocks)
    pov, external_pov_insert_policy = resolve_runtime_pov_contract(protagonist, setting, project)
    seeds = [
        {
            "id": as_text(item.get("id")) or f"S-{index + 1:03d}",
            "category": as_text(item.get("category")) or as_text(item.get("type")) or "foreshadow",
            "description": as_text(item.get("description")) or as_text(item.get("text")) or as_text(item),
            "status": as_text(item.get("status")) or "active",
        }
        for index, item in enumerate(ensure_list(phase0_design.get("foreshadow_map")))
        if as_text(item.get("description") if isinstance(item, dict) else item)
        or as_text(item.get("text") if isinstance(item, dict) else "")
    ]
    if not seeds:
        fallback_arc = ensure_list(phase0_design.get("arcs"))[:1]
        fallback_plan = ensure_list(phase0_design.get("opponent_transition_plan"))[:1]
        fallback_texts = unique(
            [as_text(arc.get("title")) for arc in fallback_arc if as_text(arc.get("title"))]
            + [as_text(entry.get("goal")) for entry in fallback_plan if as_text(entry.get("goal"))]
        )
        if not fallback_texts:
            fallback_texts = [first_text(project, "logline", default="강호 장기 복선")]
        seeds = [
            {
                "id": f"S-{index + 1:03d}",
                "category": "foreshadow",
                "description": text,
                "status": "active",
            }
            for index, text in enumerate(fallback_texts)
        ]
    master_bible = {
        "ProjectData": {
            "MetaInfo": {
                "title": first_text(project, "title_ko", "title", default="무협 프로젝트"),
                "grand_objective": first_text(project, "core_premise", default="강호 생존과 역전"),
                "genre_archetype": first_text(project, "format", default="무협"),
                "logline": first_text(project, "logline", default="강호 서사"),
                "total_episodes": 350,
                "episodes_per_arc": 5,
                "arcs_per_volume": 5,
            },
            "CoreIdentity": {
                "protagonist": first_text(protagonist, "name", default="주인공"),
                "protagonist_faction": faction_map["protagonist_faction"],
                "edge": first_text(protagonist, "true_strength", default="무공 재능"),
                "desire": first_text(protagonist, "initial_goal", default="생존"),
                "crisis": first_text(project, "logline", default="강호 위기"),
            },
            "CommercialCode": {
                "cider_point": first_text(setting, "cider_point", default="위계를 뒤집는 쾌감"),
                "success_device": first_text(setting, "execution_doctrine", default="경지 상승과 문파 역전"),
                "attitude": first_text(setting, "attitude", default="강호의 질서와 정면 충돌하는 무협 서사"),
            },
        },
        "protagonist_config": {
            "world_origin": world_origin,
            "incarnation_type": incarnation_type,
            "pov": pov,
            "external_pov_insert_policy": external_pov_insert_policy,
            "name": first_text(protagonist, "name", default="주인공"),
            "age_at_start": protagonist.get("age_at_start", ""),
            "opening_status": first_text(protagonist, "status", default="강호의 인물"),
            "initial_goal": first_text(protagonist, "initial_goal", default="생존"),
            "mid_goal": first_text(protagonist, "mid_goal", default="성장"),
            "final_goal": first_text(protagonist, "final_goal", default="돌파"),
            "true_strength": first_text(protagonist, "true_strength", default="무공 재능"),
            "true_weakness": first_text(protagonist, "true_weakness", default="미정"),
            "combat_role": first_text(protagonist, "combat_role", default="무인"),
        },
        "MartialHUD": build_martial_hud(
            protagonist,
            setting,
            faction_map,
            treasures,
            snapshot,
            treatment_blocks,
            phase0_design,
        ),
        "WorldState": {
            "CurrentEra": first_text(treatment_blocks[0], "time_span.in_story_time", default="작중 초반"),
            "CurrentLocation": first_text(treatment_blocks[0], "location.place", default="강호"),
            "EraWindow": f"{first_text(project, 'start_year', default='미상')} - {first_text(project, 'end_year', default='미상')}",
            "JianghuPhase": first_text(setting, "jianghu_phase", default="군웅할거"),
            "internal_energy_curve": phase0_design.get("internal_energy_curve"),
        },
        "AssetLibrary": {
            "KeyNPCs": build_key_npcs(project, protagonist, ensure_list(phase0_design.get("npc_timeline"))),
            "KeyItems": treasures,
            "ArcSheets": [
                {
                    "arc_id": as_text(arc.get("arc_id")) or f"arc_{index + 1}",
                    "title": as_text(arc.get("title")) or f"Arc {index + 1}",
                    "block_range": as_text(arc.get("block_range")),
                    "time_window": as_text(arc.get("time_window")),
                    "main_opponents": ensure_list(arc.get("main_opponents")),
                }
                for index, arc in enumerate(ensure_list(phase0_design.get("arcs")))
            ],
        },
        "FactionMap": faction_map,
        "Treasures": treasures,
        "Seeds": seeds,
        "HistoricalEvents": [
            {
                "type": "arc",
                "arc_id": as_text(arc.get("arc_id")) or f"arc_{index + 1}",
                "title": as_text(arc.get("title")) or f"Arc {index + 1}",
                "block_range": as_text(arc.get("block_range")),
                "time_window": as_text(arc.get("time_window")),
            }
            for index, arc in enumerate(ensure_list(phase0_design.get("arcs")))
        ],
        "GenreRules": {
            "core_mode": first_text(project, "format", default="무협"),
            "taboo_rules": ensure_list(phase0_design.get("taboo_rules")),
            "do_not_fake": ensure_list(phase0_design.get("do_not_fake")),
        },
        "plot_roadmap": treatment_blocks,
    }
    master_bible = sanitize_bi_value(master_bible)
    return {
        "_schema_version": "2.1",
        "_schema_description": f"{master_bible['ProjectData']['MetaInfo']['title']} wuxia BI",
        "_last_updated": date.today().isoformat(),
        "_genre": detect_genre_code(project),
        "_family": "wuxguide",
        "_work_id": work_id,
        "_authority_chain": authority_chain,
        "_source_phase0": source_phase0,
        "_source_tr": source_tr,
        "MasterBible": master_bible,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase0", type=Path, required=True, help="Phase0 design JSON path")
    parser.add_argument("--draft", type=Path, required=True, help="Treatment draft JSON path")
    parser.add_argument("--output", type=Path, required=True, help="Output BI JSON path")
    args = parser.parse_args()

    phase0 = load_json(args.phase0)
    draft_raw = load_json(args.draft)
    canonical_treatment, tr_warnings = canonicalize_treatment_payload(draft_raw)
    treatment_blocks = canonical_treatment["blocks"]
    require(isinstance(treatment_blocks, list) and len(treatment_blocks) >= 1, "Treatment draft must contain at least one block")
    require(isinstance(phase0, dict), "Phase0 payload must be a dict")
    for section in REQUIRED_PHASE0_SECTIONS:
        require(section in phase0, f"Phase0 payload missing required section: {section}")
    for field in REQUIRED_PHASE0_FIELDS:
        require(field in phase0["phase0_design"], f"Phase0 design missing field: {field}")

    work_id = derive_work_id_from_phase0_path(args.phase0)
    bible = build_bible(
        phase0,
        treatment_blocks,
        work_id=work_id,
        source_phase0=relative_posix(args.phase0),
        source_tr=relative_posix(args.draft),
        authority_chain=build_authority_chain(work_id, phase0_path=args.phase0, draft_path=args.draft),
    )
    bible, canonical_warnings = canonicalize_bible_payload(bible, treatment=canonical_treatment, genre_hint="wuxia")
    valid, errors, warnings = validate_bible_structure(bible)
    require(valid, f"Bible validation failed: {errors}")
    require(
        bible["MasterBible"]["ProjectData"]["CoreIdentity"]["protagonist"]
        == bible["MasterBible"]["MartialHUD"]["Protagonist"]["actual_truth"]["name"],
        "Protagonist name mismatch inside BI",
    )
    require(
        len(bible["MasterBible"]["plot_roadmap"]) == len(treatment_blocks),
        "BI plot_roadmap must align with treatment block count",
    )

    draft_titles = [as_text(block.get("title")) for block in treatment_blocks]
    bible_titles = [as_text(block.get("title")) for block in bible["MasterBible"]["plot_roadmap"]]
    require(draft_titles == bible_titles, "BI plot_roadmap title sequence must match treatment draft exactly")

    serialized = json.dumps(bible, ensure_ascii=False, indent=2)
    require(not any(token in serialized for token in GARBLED_TOKENS), "Generated BI contains garbled text markers")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized + "\n", encoding="utf-8")

    print(f"[OK] Wuxia BI generated: {args.output}")
    all_warnings = [*tr_warnings, *warnings, *canonical_warnings]
    if all_warnings:
        print(f"[WARN] Bible warnings: {all_warnings}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
