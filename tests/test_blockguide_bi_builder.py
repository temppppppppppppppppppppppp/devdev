from __future__ import annotations

import json
import sys

import scripts.build_bi_from_phase0_and_tr as build_script


def _build_phase0() -> dict:
    return {
        "project": {"title_ko": "테스트 프로젝트", "format": "investment"},
        "setting": {"starter_company": {"name": "테스트컴퍼니"}},
        "protagonist": {"name": "주인공"},
        "phase0_design": {
            "arcs": [],
            "npc_timeline": [],
            "foreshadow_map": [],
            "opponent_transition_plan": [],
        },
    }


def _build_blocks() -> list[dict]:
    return [{"block_id": f"Block {idx}", "title": f"테스트 블록 {idx}"} for idx in range(1, 71)]


def _full_content(label: str) -> dict:
    return {
        "context": f"{label} 배경",
        "event_villain": f"{label} 사건",
        "solution": f"{label} 해결",
        "reward": f"{label} 보상",
    }


def _build_phase0_for_real_bible() -> dict:
    return {
        "project": {
            "title_ko": "테스트 프로젝트",
            "format": "investment",
            "logline": "회귀한 주인공이 회사를 살린다.",
            "start_year": 2012,
            "end_year": 2026,
            "core_premise": "관문 회사를 다시 세운다.",
        },
        "setting": {
            "group_background": "오래된 그룹",
            "execution_doctrine": "현금흐름과 계약 우위",
            "starter_company": {
                "name": "테스트컴퍼니",
                "state": "위기",
                "assets": ["공장", "인력"],
                "liabilities": ["부채", "평판 추락"],
            },
        },
        "protagonist": {
            "name": "주인공",
            "status": "서울대 합격 직후",
            "public_image": "어린 후계자",
            "true_strength": "병목을 읽는다",
            "true_weakness": "감정 개입",
            "initial_goal": "회사를 살린다",
            "mid_goal": "세력을 만든다",
            "final_goal": "제국을 세운다",
            "age_at_start": 19,
        },
        "phase0_design": {
            "arcs": [
                {
                    "arc_id": "arc_1",
                    "title": "Arc 1",
                    "block_range": "1-35",
                    "time_window": "2012 상반기",
                    "capital_target": "35억",
                    "front_sectors": ["장비"],
                    "support_sectors": ["물류"],
                    "main_opponents": ["Opp A"],
                    "new_npcs": ["NPC A"],
                    "emotion_curve": "상승",
                    "quiet_blocks": [5],
                    "defeat_blocks": [10],
                },
                {
                    "arc_id": "arc_2",
                    "title": "Arc 2",
                    "block_range": "36-70",
                    "time_window": "2012 하반기",
                    "capital_target": "70억",
                    "front_sectors": ["소재"],
                    "support_sectors": ["금융"],
                    "main_opponents": ["Opp B"],
                    "new_npcs": ["NPC B"],
                    "emotion_curve": "가속",
                    "quiet_blocks": [40],
                    "defeat_blocks": [45],
                },
            ],
            "npc_timeline": [
                {"name": "조력자", "role": "멘토", "first_block": 2, "final_status": "합류", "turning_points": []}
            ],
            "foreshadow_map": [{"id": "S-001", "description": "초기 복선", "status": "active"}],
            "opponent_transition_plan": [{"faction": "Opp A", "phase": "초반", "goal": "인증 저지"}],
        },
    }


def _build_blocks_for_real_bible() -> list[dict]:
    return [
        {
            "block_id": f"Block {idx}",
            "title": f"테스트 블록 {idx}",
            "content": _full_content(f"블록 {idx}"),
            "stakes": f"위험 {idx}",
            "power_shift": {"protagonist": "상승", "antagonist": "하락"},
            "relationship_delta": [],
            "foreshadow": [],
            "callback": [],
            "emotional_beat": {"type": "resolve", "intensity": 6},
            "tension_level": 7,
            "pov_character": "주인공",
            "location": {"place": "서울", "type": "city"},
            "time_span": {"duration": "1주", "in_story_time": f"2012년 {idx}주"},
            "genre_ext": {"capital_after": f"{idx}억", "deal_type": "장비"},
            "regression_ext": {"is_regressor": True, "regression_type": "회귀"},
        }
        for idx in range(1, 71)
    ]


def test_blockguide_bi_main_accepts_wrapped_draft_input(monkeypatch, temp_dir) -> None:
    phase0_path = temp_dir / "phase0.json"
    draft_path = temp_dir / "draft.json"
    output_path = temp_dir / "bi.json"

    phase0 = _build_phase0()
    blocks = _build_blocks()
    phase0_path.write_text(json.dumps(phase0, ensure_ascii=False, indent=2), encoding="utf-8")
    draft_path.write_text(json.dumps({"blocks": blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_normalize_phase0_design(phase0_design: dict, treatment_blocks: list[dict]) -> dict:
        captured["normalized_blocks"] = treatment_blocks
        return phase0_design

    def fake_build_bible(payload: dict, treatment_blocks: list[dict]) -> dict:
        captured["build_blocks"] = treatment_blocks
        return {
            "MasterBible": {
                "ProjectData": {"CoreIdentity": {"protagonist": "주인공"}},
                "FinanceHUD": {"Protagonist": {"actual_truth": {"name": "주인공"}}},
                "plot_roadmap": treatment_blocks,
            }
        }

    monkeypatch.setattr(build_script, "normalize_phase0_design", fake_normalize_phase0_design)
    monkeypatch.setattr(build_script, "build_bible", fake_build_bible)
    monkeypatch.setattr(build_script, "validate_treatment_structure", lambda _: (True, [], []))
    monkeypatch.setattr(build_script, "validate_bible_structure", lambda _: (True, [], []))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_bi_from_phase0_and_tr.py",
            "--phase0",
            str(phase0_path),
            "--draft",
            str(draft_path),
            "--output",
            str(output_path),
        ],
    )

    exit_code = build_script.main()

    assert exit_code == 0
    assert output_path.exists()
    assert captured["normalized_blocks"][0]["block_no"] == 1
    assert captured["build_blocks"][0]["block_no"] == 1
    assert [block["title"] for block in captured["normalized_blocks"]] == [block["title"] for block in blocks]
    assert [block["title"] for block in captured["build_blocks"]] == [block["title"] for block in blocks]


def test_build_bible_emits_runtime_protagonist_contract_and_normalized_roadmap() -> None:
    bible = build_script.build_bible(_build_phase0_for_real_bible(), _build_blocks_for_real_bible())

    protagonist_config = bible["MasterBible"]["protagonist_config"]
    roadmap = bible["MasterBible"]["plot_roadmap"]

    assert protagonist_config["world_origin"] == "현대인"
    assert protagonist_config["incarnation_type"] == "회귀자"
    assert protagonist_config["pov"] == "3인칭"
    assert protagonist_config["external_pov_insert_policy"] == "제한적 허용"
    assert roadmap[0]["block_no"] == 1
    assert roadmap[-1]["block_no"] == 70
