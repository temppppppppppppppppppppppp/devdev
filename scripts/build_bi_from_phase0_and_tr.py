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


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


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
        key_npcs.append(
            {
                "name": npc["name"],
                "role": npc["role"],
                "desc": f"{npc['role']}. Block {npc['first_block']}부터 본격적으로 영향력을 행사한다.",
                "first_block": npc["first_block"],
                "final_status": npc["final_status"],
                "key_turning_points": npc["turning_points"],
            }
        )
    return key_npcs


def build_arc_sheets(arcs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for arc in arcs:
        first_slot = arc["block_slots"][0]
        last_slot = arc["block_slots"][-1]
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
        first_slot = arc["block_slots"][0]
        last_slot = arc["block_slots"][-1]
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
    phase0 = phase0_payload["phase0_design"]
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
    max_capital = portfolio_history[-1]["total_assets"]

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
                "protagonist_faction": "세령컬처웍스 (초기) -> 스타 IP 복합기업 세령컬처웍스 (후기)",
                "edge": protagonist["true_strength"],
                "desire": protagonist["initial_goal"],
                "crisis": f"{protagonist['public_image']}으로 낙인찍혀 문화 사업에서도 실패를 기대받는 상태에서 출발한다.",
            },
            "CommercialCode": {
                "cider_point": "아무도 못 알아본 인재를 정확한 자리와 타이밍에 올려 성공으로 바꾸는 통쾌함",
                "success_device": "사람 발굴, 포지셔닝, 팬덤 접점 설계, 그룹 인프라 활용",
                "attitude": "망나니 외피 아래에서 사람과 포맷을 집요하게 배치하는 실전형 설계자",
            },
        },
        "protagonist_config": {
            "world_origin": protagonist["status"],
            "incarnation_type": "비회귀 / 비빙의",
            "special_talent": {
                "name": "스타 감각",
                "description": protagonist["true_strength"],
                "limits": protagonist["true_weakness"],
            },
            "start_point": {
                "year": project["start_year"],
                "month": first_block["time_span"]["in_story_time"],
                "age": protagonist["age_at_start"],
                "context": "부친이 던져 준 적자 엔터 자회사 세령컬처웍스를 1년 안에 살려야 하는 상황",
            },
        },
        "FinanceHUD": {
            "_description": "엔터 타이쿤 전용 HUD - 동원 가능 자본, 인재 축, 사업축, 지배력 추적",
            "Protagonist": {
                "actual_truth": {
                    "name": protagonist["name"],
                    "alias": "망나니 도련님 (초기) -> 스타 IP 제국 설계자 (후기)",
                    "age": protagonist["age_at_start"],
                    "rank": f"{protagonist['status']} / {starter_company['name']} 대표",
                    "financial_status": {
                        "mobilizable_capital": portfolio_history[0]["total_assets"],
                        "total_assets": portfolio_history[0]["total_assets"],
                        "max_assets": max_capital,
                        "company": starter_company["name"],
                        "company_state": starter_company["state"],
                        "business_lines": all_sectors,
                        "debt": "누적 적자와 낮은 신뢰도에서 출발",
                    },
                    "portfolio_history": portfolio_history,
                    "investment_style": "스타 감각 기반 발굴 + 포지셔닝 + 시스템 설계",
                    "risk_tolerance": "중고위험 감수. 확신이 서면 빠르게 밀어붙이지만 배신과 여론전에는 취약하다.",
                    "credentials": [
                        protagonist["status"],
                        starter_company["name"],
                    ],
                    "current_objective": "세령컬처웍스를 청산 직전 상태에서 생존시킨다.",
                    "mid_term_goal": protagonist["mid_goal"],
                    "final_goal": protagonist["final_goal"],
                    "causal_injuries": "망나니 낙인, 아버지의 불신, 내부 공신 라인의 감시",
                },
                "public_reputation": {
                    "identity": protagonist["public_image"],
                    "wealth_level": "오너가 출신이지만 개인 역량은 의심받는 상태",
                    "perceived_influence": "낙하산 대표 정도로만 보인다.",
                    "credit_rating": "세령그룹 후광은 있으나 업계 신뢰는 낮다.",
                },
            },
        },
        "MartialHUD": {
            "_alias_note": "main_a.py 호환용 alias",
            "Protagonist": {
                "actual_truth": {
                    "name": protagonist["name"],
                    "alias": "망나니 도련님 -> 스타 IP 제국 설계자",
                    "age": protagonist["age_at_start"],
                    "rank": f"{protagonist['status']} / {starter_company['name']} 대표",
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
            "growth_rule": "배우 -> 아이돌 -> 웹콘텐츠 -> 셰프/F&B -> 글로벌 -> 플랫폼 순으로 사업축을 확장한다.",
            "reward_rule": "승리는 화제성, 수익, 지배력의 세 층위로 측정한다.",
            "risk_rule": "패배는 여론전, 계약, 내부 정치, 지배구조 리스크에서 온다.",
            "talent_rule": "태하의 재능은 초능력이 아니라 사람과 포맷의 타이밍을 읽는 감각으로만 작동한다.",
        },
        "plot_roadmap": treatment_blocks,
    }

    return {
        "_schema_version": "2.0",
        "_schema_description": f"{project['title_ko']} Bible - phase0/TR draft 동기화 산출물",
        "_last_updated": date.today().isoformat(),
        "_genre": "entertainment",
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
    for field in ("arcs", "npc_timeline", "foreshadow_map", "partner_location_sector_distribution", "capital_curve", "defeat_blocks", "opponent_transition_plan"):
        require(field in phase0_design, f"Phase0 design missing field: {field}")

    payload = {
        "project": phase0["project"],
        "setting": phase0["setting"],
        "protagonist": phase0["protagonist"],
        "phase0_design": phase0_design,
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
