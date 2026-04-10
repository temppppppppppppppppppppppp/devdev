from __future__ import annotations

import json

import scripts.build_bi_from_phase0_and_tr as bi_builder
from modules.core.stage0_opening_contract import (
    derive_opening_bundle_contract,
    ensure_opening_bundle_contract,
    sync_opening_bundle_contract_for_work,
)


def _write_json(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _phase0_payload() -> dict:
    return {
        "project": {
            "title_ko": "무일푼 후계자",
            "format": "support-system cashflow",
            "logline": "운영의 길목을 먹고 올라간다.",
        },
        "setting": {},
        "protagonist": {
            "name": "윤주인",
            "initial_goal": "첫 반복매출과 다음 전장 입장권을 확보한다.",
        },
        "phase0_design": {
            "hud_interpretation": {
                "first_block_reward_rule": "첫 보상은 돈보다 입장권과 승인권이다."
            },
            "arcs": [
                {
                    "arc_id": "ARC-01",
                    "title": "장례식장 뒤문",
                    "block_range": "1-10",
                    "front_sectors": ["장례 의전"],
                    "support_sectors": ["밥차", "셔틀", "세탁실"],
                    "entry_function": "카드가 잘리며 뒤문으로 밀려난다.",
                    "exit_function": "첫 반복매출과 함께 호텔 입장권이 열린다.",
                    "block_slots": [
                        {"block": 1, "title": "잘린 카드", "function": "뒤문으로 밀려난다."},
                        {"block": 2, "title": "장례 밥차", "function": "첫 운영권 조각을 뜯어낸다."},
                        {"block": 3, "title": "검은 리본 주차권", "function": "주요 동선이 정리되며 공개적으로 증명된다."},
                        {"block": 4, "title": "대표의 시선", "function": "형이 다시 보며 재평가가 시작된다."},
                        {"block": 5, "title": "빈소 셔틀", "function": "반복 수익 구조가 눈에 보이기 시작한다."},
                        {"block": 6, "title": "호텔 입장권", "function": "다음 전장 진입권이 열린다."},
                    ],
                }
            ],
        },
    }


def test_derive_opening_bundle_contract_uses_opening_slot_signals() -> None:
    contract = derive_opening_bundle_contract(_phase0_payload())

    assert contract["bundle_window"] == "TR 2~6"
    assert contract["macro_battlefield"] == "장례식장 뒤문"
    assert contract["macro_battlefield_map"][:3] == ["장례 밥차", "검은 리본 주차권", "대표의 시선"]
    assert contract["first_signboard_block"] == 3
    assert contract["representative_reevaluation_block"] == 4
    assert contract["next_battlefield_ticket_block"] == 6


def test_ensure_opening_bundle_contract_fills_material_bundle_summary() -> None:
    phase0, material_bundle, contract = ensure_opening_bundle_contract(
        _phase0_payload(),
        {
            "events": [],
            "npc_candidates": [],
            "crisis_candidates": [],
            "terms": [],
            "scene_details": [],
            "notes": "운영 레인을 먼저 먹는다.",
        },
    )

    assert phase0["phase0_design"]["opening_bundle_contract"] == contract
    assert material_bundle["opening_bundle_contract"] == contract


def test_sync_opening_bundle_contract_for_work_updates_phase0_and_preprocess(tmp_path) -> None:
    work_id = "demo"
    phase0_path = tmp_path / "treatments" / "phase0" / f"{work_id}_phase0_design.json"
    bundle_path = tmp_path / "treatments" / "preprocess" / work_id / "material_bundle_summary.json"

    _write_json(phase0_path, _phase0_payload())
    _write_json(
        bundle_path,
        {
            "events": [],
            "npc_candidates": [],
            "crisis_candidates": [],
            "terms": [],
            "scene_details": [],
            "notes": "운영 레인을 먼저 먹는다.",
        },
    )

    result = sync_opening_bundle_contract_for_work(work_id, root=tmp_path, write=True)
    synced_phase0 = json.loads(phase0_path.read_text(encoding="utf-8"))
    synced_bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    assert result.contract["bundle_window"] == "TR 2~6"
    assert str(phase0_path) in result.updated_paths
    assert str(bundle_path) in result.updated_paths
    assert synced_phase0["phase0_design"]["opening_bundle_contract"] == result.contract
    assert synced_bundle["opening_bundle_contract"] == result.contract


def test_blockguide_normalize_phase0_design_backfills_opening_bundle_contract() -> None:
    normalized = bi_builder.normalize_phase0_design(
        _phase0_payload()["phase0_design"],
        [
            {
                "block_id": "Block 1",
                "title": "Block 1",
                "time_span": {"in_story_time": "2012-01"},
                "genre_ext": {"capital_after": "1억", "deal_type": "운영권"},
                "location": {"place": "서울"},
            },
            {
                "block_id": "Block 2",
                "title": "Block 2",
                "time_span": {"in_story_time": "2012-02"},
                "genre_ext": {"capital_after": "2억", "deal_type": "운영권"},
                "location": {"place": "서울"},
            },
            {
                "block_id": "Block 3",
                "title": "Block 3",
                "time_span": {"in_story_time": "2012-03"},
                "genre_ext": {"capital_after": "3억", "deal_type": "운영권"},
                "location": {"place": "서울"},
            },
            {
                "block_id": "Block 4",
                "title": "Block 4",
                "time_span": {"in_story_time": "2012-04"},
                "genre_ext": {"capital_after": "4억", "deal_type": "운영권"},
                "location": {"place": "서울"},
            },
            {
                "block_id": "Block 5",
                "title": "Block 5",
                "time_span": {"in_story_time": "2012-05"},
                "genre_ext": {"capital_after": "5억", "deal_type": "운영권"},
                "location": {"place": "서울"},
            },
            {
                "block_id": "Block 6",
                "title": "Block 6",
                "time_span": {"in_story_time": "2012-06"},
                "genre_ext": {"capital_after": "6억", "deal_type": "운영권"},
                "location": {"place": "서울"},
            },
        ],
    )

    assert normalized["opening_bundle_contract"]["bundle_window"] == "TR 2~6"
    assert normalized["opening_bundle_contract"]["macro_battlefield"] == "장례식장 뒤문"
