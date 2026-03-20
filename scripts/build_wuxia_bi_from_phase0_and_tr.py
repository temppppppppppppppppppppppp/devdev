#!/usr/bin/env python3
"""Build a wuxia-family BI JSON from phase0 and treatment draft inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.response_schemas import validate_bible_structure, validate_treatment_structure

GARBLED_TOKENS = ("\ufffd",)
REQUIRED_PHASE0_SECTIONS = ("project", "setting", "protagonist", "phase0_design")
REQUIRED_PHASE0_FIELDS = ("arcs", "npc_timeline", "foreshadow_map", "opponent_transition_plan")
BLANKISH_VALUES = {"", "none", "null", "n/a", "na", "-", "unknown"}


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


def build_treasures(protagonist: dict[str, Any], setting: dict[str, Any]) -> list[dict[str, str]]:
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
    return treasures


def build_treatment_snapshot(treatment_blocks: list[dict[str, Any]]) -> dict[str, Any]:
    last_block = treatment_blocks[-1]
    recent_martial_gains = unique(
        [
            as_text(get_nested(block, "genre_ext.martial_art_gain"))
            for block in treatment_blocks
            if not is_blankish(get_nested(block, "genre_ext.martial_art_gain"))
        ]
    )
    recent_artifact_gains = unique(
        [
            as_text(get_nested(block, "genre_ext.artifact_or_manual_gain"))
            for block in treatment_blocks
            if not is_blankish(get_nested(block, "genre_ext.artifact_or_manual_gain"))
            and as_text(get_nested(block, "genre_ext.artifact_or_manual_gain")).lower() not in {"none", "no", "none."}
        ]
    )
    return {
        "current_realm": first_text(last_block, "genre_ext.realm_after", "genre_ext.realm_before", default="novice"),
        "internal_energy": parse_int(get_nested(last_block, "genre_ext.internal_energy_after"), default=10),
        "jianghu_reputation": first_text(last_block, "genre_ext.jianghu_reputation", default="unknown"),
        "faction_position": first_text(last_block, "genre_ext.faction_position", default="unsettled"),
        "enemy_pressure": first_text(last_block, "genre_ext.enemy_pressure", default="active"),
        "current_opponent": first_text(last_block, "genre_ext.opponent.name", default=""),
        "recent_martial_gains": recent_martial_gains,
        "recent_artifact_gains": recent_artifact_gains,
        "last_confirmed_block": len(treatment_blocks),
    }


def build_martial_hud(
    protagonist: dict[str, Any],
    setting: dict[str, Any],
    faction_map: dict[str, Any],
    treasures: list[dict[str, str]],
    snapshot: dict[str, Any],
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
                "internal_energy": parse_int(snapshot.get("internal_energy"), default=first_number(protagonist, "internal_energy", "energy", "qi", default=10)),
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


def build_bible(phase0: dict[str, Any], treatment_blocks: list[dict[str, Any]]) -> dict[str, Any]:
    project = phase0["project"]
    setting = phase0["setting"]
    protagonist = phase0["protagonist"]
    phase0_design = phase0["phase0_design"]
    faction_map = build_faction_map(protagonist, setting, phase0_design)
    treasures = build_treasures(protagonist, setting)
    snapshot = build_treatment_snapshot(treatment_blocks)
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
        "MartialHUD": build_martial_hud(protagonist, setting, faction_map, treasures, snapshot),
        "WorldState": {
            "CurrentEra": first_text(treatment_blocks[0], "time_span.in_story_time", default="작중 초반"),
            "CurrentLocation": first_text(treatment_blocks[0], "location.place", default="강호"),
            "EraWindow": f"{first_text(project, 'start_year', default='미상')} - {first_text(project, 'end_year', default='미상')}",
            "JianghuPhase": first_text(setting, "jianghu_phase", default="군웅할거"),
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
        "plot_roadmap": treatment_blocks,
    }
    return {
        "_schema_version": "2.1",
        "_schema_description": f"{master_bible['ProjectData']['MetaInfo']['title']} wuxia BI",
        "_last_updated": date.today().isoformat(),
        "_genre": detect_genre_code(project),
        "MasterBible": master_bible,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase0", type=Path, required=True, help="Phase0 design JSON path")
    parser.add_argument("--draft", type=Path, required=True, help="Treatment draft JSON path")
    parser.add_argument("--output", type=Path, required=True, help="Output BI JSON path")
    args = parser.parse_args()

    phase0 = load_json(args.phase0)
    treatment_blocks = load_json(args.draft)
    tr_valid, tr_errors, _tr_warnings = validate_treatment_structure(treatment_blocks)
    require(tr_valid, f"Treatment draft validation failed: {tr_errors}")
    require(isinstance(treatment_blocks, list) and len(treatment_blocks) == 70, "Treatment draft must contain 70 blocks")
    require(isinstance(phase0, dict), "Phase0 payload must be a dict")
    for section in REQUIRED_PHASE0_SECTIONS:
        require(section in phase0, f"Phase0 payload missing required section: {section}")
    for field in REQUIRED_PHASE0_FIELDS:
        require(field in phase0["phase0_design"], f"Phase0 design missing field: {field}")

    bible = build_bible(phase0, treatment_blocks)
    valid, errors, warnings = validate_bible_structure(bible)
    require(valid, f"Bible validation failed: {errors}")
    require(
        bible["MasterBible"]["ProjectData"]["CoreIdentity"]["protagonist"]
        == bible["MasterBible"]["MartialHUD"]["Protagonist"]["actual_truth"]["name"],
        "Protagonist name mismatch inside BI",
    )
    require(len(bible["MasterBible"]["plot_roadmap"]) == 70, "BI plot_roadmap must contain 70 blocks")

    draft_hash = hashlib.sha256(json.dumps(treatment_blocks, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    bible_hash = hashlib.sha256(
        json.dumps(bible["MasterBible"]["plot_roadmap"], ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    require(draft_hash == bible_hash, "BI plot_roadmap must match treatment draft exactly")

    serialized = json.dumps(bible, ensure_ascii=False, indent=2)
    require(not any(token in serialized for token in GARBLED_TOKENS), "Generated BI contains garbled text markers")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized + "\n", encoding="utf-8")

    print(f"[OK] Wuxia BI generated: {args.output}")
    if warnings:
        print(f"[WARN] Bible warnings: {warnings}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
