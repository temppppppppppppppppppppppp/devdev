#!/usr/bin/env python3
"""Build a UTF-8 safe Bible JSON from verified phase0 and treatment draft files."""

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

GARBLED_TOKENS = ("???", "\ufffd", "�")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def parse_block_range(block_range: str) -> tuple[int, int]:
    start_text, end_text = as_text(block_range).split("-", 1)
    return int(start_text), int(end_text)


def summarize_business_axis(sectors: list[str], limit: int = 4) -> str:
    cleaned = [sector for sector in sectors if as_text(sector)]
    if not cleaned:
        return "핵심 사업축"
    sample = cleaned[:limit]
    if len(cleaned) <= limit:
        return ", ".join(sample)
    return ", ".join(sample) + " 등"


def derive_talent_name(protagonist: dict[str, Any]) -> str:
    strength = as_text(protagonist.get("true_strength"))
    if "AI" in strength or "추론" in strength or "모델" in strength:
        return "추론 독점 감각"
    if "현금흐름" in strength or "지출" in strength or "운영비" in strength:
        return "현금흐름 장악 감각"
    if "계약" in strength or "규격" in strength:
        return "계약 구조 감각"
    return "사업 감각"


def derive_growth_rule(phase0: dict[str, Any]) -> str:
    sectors = unique_preserve_order(
        [
            *[sector for arc in phase0["partner_location_sector_distribution"]["front_sector_by_arc"] for sector in arc["front"]],
            *[sector for arc in phase0["partner_location_sector_distribution"]["front_sector_by_arc"] for sector in arc["support"]],
        ]
    )
    return f"{summarize_business_axis(sectors)} 순으로 사업축을 넓히며 지배력을 키운다."


def derive_debt_summary(starter_company: dict[str, Any]) -> str:
    liabilities = starter_company.get("liabilities", [])
    if isinstance(liabilities, list):
        return ", ".join(as_text(item) for item in liabilities if as_text(item))
    return as_text(liabilities)


def derive_starter_context(starter_company: dict[str, Any]) -> str:
    return f"{starter_company['name']}를 {starter_company['state']} 상태에서 되살려야 하는 출발점"


def derive_protagonist_faction(starter_company: dict[str, Any]) -> str:
    return f"{starter_company['name']} -> {starter_company['name']}"


def derive_public_influence(protagonist: dict[str, Any]) -> str:
    public_image = as_text(protagonist.get("public_image"))
    if not public_image:
        return "업계에서 과소평가된 인물로 보인다."
    return f"초반 평판은 '{public_image}' 쪽에 가까워 실권보다 저평가된다."


def derive_risk_tolerance(protagonist: dict[str, Any]) -> str:
    weakness = as_text(protagonist.get("true_weakness"))
    return f"리스크를 감수하지만 '{weakness}' 때문에 과신과 불신이 동시에 흔들릴 수 있다."


def build_portfolio_history(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checkpoints = [1, 10, 20, 30, 40, 50, 60, 70]
    history: list[dict[str, Any]] = []
    for block_no in checkpoints:
        block = blocks[block_no - 1]
        history.append(
            {
                "episode": 0,
                "block": block_no,
                "month": block["time_span"]["in_story_time"],
                "total_assets": block["genre_ext"]["capital_after"],
                "event": block["title"],
            }
        )
    return history


def derive_partner_location_sector_distribution(
    phase0: dict[str, Any],
    treatment_blocks: list[dict[str, Any]],
) -> dict[str, Any]:
    front_sector_by_arc: list[dict[str, Any]] = []
    for arc in phase0["arcs"]:
        front_sector_by_arc.append(
            {
                "arc_id": arc["arc_id"],
                "front": list(arc.get("front_sectors", [])),
                "support": list(arc.get("support_sectors", [])),
            }
        )

    partners: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for entry in phase0.get("opponent_transition_plan", []):
        name = as_text(entry.get("faction")) or ", ".join(entry.get("main_actors", []))
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        partners.append(
            {
                "name": name,
                "cadence": as_text(entry.get("phase")) or as_text(entry.get("block_range")) or as_text(entry.get("entry_block")),
                "objective": as_text(entry.get("goal")) or as_text(entry.get("weakness")) or "source TR aligned business-power objective",
            }
        )

    if not partners:
        for arc in phase0["arcs"]:
            for name in arc.get("main_opponents", []):
                if not name or name in seen_names:
                    continue
                seen_names.add(name)
                partners.append({"name": name, "cadence": arc["arc_id"], "objective": arc["title"]})

    location_pool = unique_preserve_order(
        [as_text(block.get("location", {}).get("place")) for block in treatment_blocks if isinstance(block, dict)]
    )
    deal_type_rotation = unique_preserve_order(
        [as_text(block.get("genre_ext", {}).get("deal_type")) for block in treatment_blocks if isinstance(block, dict)]
    )

    return {
        "partners": partners,
        "location_pool": location_pool,
        "deal_type_rotation": deal_type_rotation,
        "front_sector_by_arc": front_sector_by_arc,
    }


def derive_capital_curve(treatment_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for block_no in [1, 10, 20, 30, 40, 50, 60, 70]:
        block = treatment_blocks[block_no - 1]
        points.append(
            {
                "block": block_no,
                "title": block["title"],
                "capital_after": block["genre_ext"]["capital_after"],
            }
        )
    return points


def derive_defeat_blocks(
    phase0: dict[str, Any],
    treatment_blocks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    derived: list[dict[str, Any]] = []
    for arc in phase0["arcs"]:
        for block_no in arc.get("defeat_blocks", []):
            if not isinstance(block_no, int) or not (1 <= block_no <= len(treatment_blocks)):
                continue
            block = treatment_blocks[block_no - 1]
            derived.append(
                {
                    "block": block_no,
                    "success_pattern": block.get("genre_ext", {}).get("success_pattern", ""),
                    "summary": as_text(block.get("content", {}).get("reward")) or block["title"],
                }
            )
    derived.sort(key=lambda item: item["block"])
    return derived


def normalize_phase0_design(
    phase0: dict[str, Any],
    treatment_blocks: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized = json.loads(json.dumps(phase0, ensure_ascii=False))
    if "partner_location_sector_distribution" not in normalized:
        normalized["partner_location_sector_distribution"] = derive_partner_location_sector_distribution(normalized, treatment_blocks)
    if "capital_curve" not in normalized:
        normalized["capital_curve"] = derive_capital_curve(treatment_blocks)
    if "defeat_blocks" not in normalized:
        normalized["defeat_blocks"] = derive_defeat_blocks(normalized, treatment_blocks)
    return normalized


def build_key_npcs(
    project: dict[str, Any],
    protagonist: dict[str, Any],
    npc_timeline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    key_npcs: list[dict[str, Any]] = [
        {
            "name": protagonist["name"],
            "role": "주인공",
            "desc": project["core_premise"],
            "first_block": 1,
            "final_status": protagonist["final_goal"],
            "key_turning_points": [
                {"block": 1, "event": protagonist["initial_goal"]},
                {"block": 35, "event": protagonist["mid_goal"]},
                {"block": 70, "event": protagonist["final_goal"]},
            ],
        }
    ]
    for npc in npc_timeline:
        turning_points = npc.get("turning_points") or npc.get("key_turning_points") or []
        key_npcs.append(
            {
                "name": npc["name"],
                "role": npc["role"],
                "desc": f"{npc['role']}. Block {npc['first_block']}부터 본격적으로 영향력을 행사한다.",
                "first_block": npc["first_block"],
                "final_status": npc["final_status"],
                "key_turning_points": turning_points,
            }
        )
    return key_npcs


def build_arc_sheets(arcs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for arc in arcs:
        if arc.get("block_slots"):
            first_slot = arc["block_slots"][0]
            last_slot = arc["block_slots"][-1]
        else:
            start_block, end_block = parse_block_range(arc["block_range"])
            first_slot = {"block": start_block, "title": arc["title"], "function": arc.get("entry_function", arc["title"])}
            last_slot = {"block": end_block, "title": arc["title"], "function": arc.get("exit_function", arc["title"])}
        out.append(
            {
                "arc_id": arc["arc_id"],
                "title": arc["title"],
                "block_range": arc["block_range"],
                "time_window": arc["time_window"],
                "capital_target": arc["capital_target"],
                "front_sectors": arc["front_sectors"],
                "support_sectors": arc["support_sectors"],
                "main_opponents": arc["main_opponents"],
                "new_npcs": arc["new_npcs"],
                "emotion_curve": arc["emotion_curve"],
                "quiet_blocks": arc["quiet_blocks"],
                "defeat_blocks": arc["defeat_blocks"],
                "entry_function": first_slot["function"],
                "exit_function": last_slot["function"],
            }
        )
    return out


def build_historical_events(
    arcs: list[dict[str, Any]],
    defeats: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for arc in arcs:
        if arc.get("block_slots"):
            first_slot = arc["block_slots"][0]
            last_slot = arc["block_slots"][-1]
        else:
            start_block, end_block = parse_block_range(arc["block_range"])
            first_slot = {"block": start_block, "title": arc["title"], "function": arc.get("entry_function", arc["title"])}
            last_slot = {"block": end_block, "title": arc["title"], "function": arc.get("exit_function", arc["title"])}
        events.append(
            {
                "type": "arc",
                "arc_id": arc["arc_id"],
                "title": arc["title"],
                "time_window": arc["time_window"],
                "block_range": arc["block_range"],
                "start_block": first_slot["block"],
                "end_block": last_slot["block"],
                "entry_event": first_slot["title"],
                "exit_event": last_slot["title"],
            }
        )
    for defeat in defeats:
        events.append(
            {
                "type": "defeat",
                "block": defeat["block"],
                "result": defeat["success_pattern"],
                "summary": defeat["summary"],
            }
        )
    return events


def build_world_state(
    project: dict[str, Any],
    setting: dict[str, Any],
    phase0: dict[str, Any],
    first_block: dict[str, Any],
) -> dict[str, Any]:
    distribution = phase0["partner_location_sector_distribution"]
    return {
        "CurrentEra": first_block["time_span"]["in_story_time"],
        "CurrentLocation": first_block["location"]["place"],
        "era_window": f"{project['start_year']}년~{project['end_year']}년",
        "group_background": setting["group_background"],
        "execution_doctrine": setting["execution_doctrine"],
        "starter_company": setting["starter_company"],
        "opponent_transition_plan": phase0["opponent_transition_plan"],
        "front_sector_by_arc": distribution["front_sector_by_arc"],
    }


def build_bible(phase0_payload: dict[str, Any], treatment_blocks: list[dict[str, Any]]) -> dict[str, Any]:
    project = phase0_payload["project"]
    setting_data = phase0_payload["setting"]
    protagonist = phase0_payload["protagonist"]
    phase0 = normalize_phase0_design(phase0_payload["phase0_design"], treatment_blocks)
    first_block = treatment_blocks[0]

    portfolio_history = build_portfolio_history(treatment_blocks)
    arc_sheets = build_arc_sheets(phase0["arcs"])
    key_npcs = build_key_npcs(project, protagonist, phase0["npc_timeline"])

    all_sectors = unique_preserve_order(
        [
            *[sector for arc in phase0["partner_location_sector_distribution"]["front_sector_by_arc"] for sector in arc["front"]],
            *[sector for arc in phase0["partner_location_sector_distribution"]["front_sector_by_arc"] for sector in arc["support"]],
        ]
    )

    starter_company = setting_data["starter_company"]
    final_capital = portfolio_history[-1]["total_assets"]
    max_capital = final_capital
    protagonist_faction = derive_protagonist_faction(starter_company)
    debt_summary = derive_debt_summary(starter_company)
    starter_context = derive_starter_context(starter_company)
    growth_rule = derive_growth_rule(phase0)
    talent_name = derive_talent_name(protagonist)
    public_influence = derive_public_influence(protagonist)
    risk_tolerance = derive_risk_tolerance(protagonist)

    master_bible = {
        "ProjectData": {
            "MetaInfo": {
                "title": project["title_ko"],
                "grand_objective": project["core_premise"],
                "genre_archetype": project["format"],
                "logline": project["logline"],
                "total_episodes": 350,
                "episodes_per_arc": 5,
                "arcs_per_volume": 5,
            },
            "CoreIdentity": {
                "protagonist": protagonist["name"],
                "protagonist_faction": protagonist_faction,
                "edge": protagonist["true_strength"],
                "desire": protagonist["initial_goal"],
                "crisis": project["logline"],
            },
            "CommercialCode": {
                "cider_point": "저평가된 자산과 병목을 먼저 읽고 지배력으로 전환하는 역전감",
                "success_device": setting_data["execution_doctrine"],
                "attitude": "큰 승부보다 반복 현금흐름, 통제권, 문서 우위를 차근차근 쌓는 사업 성장 서사",
            },
        },
        "protagonist_config": {
            "world_origin": protagonist["status"],
            "incarnation_type": "회귀/사업 감각 강화",
            "special_talent": {
                "name": talent_name,
                "description": protagonist["true_strength"],
                "limits": protagonist["true_weakness"],
            },
            "start_point": {
                "year": project["start_year"],
                "month": first_block["time_span"]["in_story_time"],
                "age": protagonist["age_at_start"],
                "context": starter_context,
            },
        },
        "FinanceHUD": {
            "_description": "Business-Power HUD - 동원 가능 자본, 사업축, 지배력, 반복 현금흐름 추적",
            "Protagonist": {
                "actual_truth": {
                    "name": protagonist["name"],
                    "alias": protagonist["public_image"],
                    "age": protagonist["age_at_start"],
                    "rank": f"{protagonist['status']} / {starter_company['name']}",
                    "financial_status": {
                        "mobilizable_capital": final_capital,
                        "total_assets": final_capital,
                        "max_assets": max_capital,
                        "company": starter_company["name"],
                        "company_state": starter_company["state"],
                        "business_lines": all_sectors,
                        "debt": debt_summary,
                    },
                    "portfolio_history": portfolio_history,
                    "investment_style": setting_data["execution_doctrine"],
                    "risk_tolerance": risk_tolerance,
                    "credentials": [
                        protagonist["status"],
                        starter_company["name"],
                    ],
                    "current_objective": protagonist["initial_goal"],
                    "mid_term_goal": protagonist["mid_goal"],
                    "final_goal": protagonist["final_goal"],
                    "causal_injuries": protagonist["true_weakness"],
                },
                "public_reputation": {
                    "identity": protagonist["public_image"],
                    "wealth_level": starter_company["state"],
                    "perceived_influence": public_influence,
                    "credit_rating": "법인과 계약 구조는 약하지만 판을 읽는 주도권은 점점 강해진다.",
                },
            },
        },
        "MartialHUD": {
            "_alias_note": "main_a.py 호환용 alias",
            "Protagonist": {
                "actual_truth": {
                    "name": protagonist["name"],
                    "alias": protagonist["public_image"],
                    "age": protagonist["age_at_start"],
                    "rank": f"{protagonist['status']} / {starter_company['name']}",
                }
            },
        },
        "WorldState": build_world_state(project, setting_data, phase0, first_block),
        "AssetLibrary": {
            "KeyNPCs": key_npcs,
            "StarterCompany": starter_company,
            "ArcSheets": arc_sheets,
            "Partners": phase0["partner_location_sector_distribution"]["partners"],
            "LocationPool": phase0["partner_location_sector_distribution"]["location_pool"],
            "DealTypeRotation": phase0["partner_location_sector_distribution"]["deal_type_rotation"],
            "BusinessAxis": {
                "front_sectors": all_sectors,
                "execution_doctrine": setting_data["execution_doctrine"],
                "group_assets": starter_company["assets"],
                "group_liabilities": starter_company["liabilities"],
            },
        },
        "Seeds": phase0["foreshadow_map"],
        "HistoricalEvents": build_historical_events(phase0["arcs"], phase0["defeat_blocks"]),
        "GenreRules": {
            "core_mode": project["format"],
            "growth_rule": growth_rule,
            "reward_rule": "승리의 단위는 수익, 지배력, 반복 현금흐름, 계약/규격 우위로 측정한다.",
            "risk_rule": "패배는 여론전, 계약, 내부 정치, 규제, 지배구조 리스크에서 온다.",
            "talent_rule": "능력은 전지적 예언이 아니라 사업 구조와 위험을 더 빨리 읽는 감각으로만 작동한다.",
        },
        "plot_roadmap": treatment_blocks,
    }

    return {
        "_schema_version": "2.0",
        "_schema_description": f"{project['title_ko']} Bible - phase0/TR draft 동기화 산출물",
        "_last_updated": date.today().isoformat(),
        "_genre": project["format"],
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
    require("project" in phase0 and "setting" in phase0 and "protagonist" in phase0 and "phase0_design" in phase0, "Phase0 payload is missing required sections")

    phase0_design = phase0["phase0_design"]
    for field in ("arcs", "npc_timeline", "foreshadow_map", "opponent_transition_plan"):
        require(field in phase0_design, f"Phase0 design missing field: {field}")

    payload = {
        "project": phase0["project"],
        "setting": phase0["setting"],
        "protagonist": phase0["protagonist"],
        "phase0_design": normalize_phase0_design(phase0_design, treatment_blocks),
    }
    payload["setting"]["protagonist"] = phase0["protagonist"]
    bible = build_bible(payload, treatment_blocks)

    valid, errors, warnings = validate_bible_structure(bible)
    require(valid, f"Bible validation failed: {errors}")
    require(
        bible["MasterBible"]["ProjectData"]["CoreIdentity"]["protagonist"]
        == bible["MasterBible"]["FinanceHUD"]["Protagonist"]["actual_truth"]["name"],
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

    print(f"[OK] BI generated: {args.output}")
    if warnings:
        print(f"[WARN] Bible warnings: {warnings}")
    print("[OK] plot_roadmap hash synchronized with draft")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
