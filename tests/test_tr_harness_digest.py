from __future__ import annotations

import json
from pathlib import Path

import scripts.tr_batch_harness as blockguide_harness
from scripts.tr_batch_harness import build_prompt as build_blockguide_prompt, render_pattern_feedback_lines
from scripts.wuxia_tr_batch_harness import build_prompt as build_wuxguide_prompt


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_blockguide_tr_prompt_includes_harness_digest_section() -> None:
    prompt = build_blockguide_prompt(
        draft_blocks=[],
        roadmap_blocks=None,
        meta={"title": "Demo", "genre": "investment", "protagonist": "Hero", "logline": "Grow the company."},
        start=1,
        batch_size=3,
        mode="flash",
    )

    assert "## Harness Digest" in prompt
    assert "- family: blockguide" in prompt
    assert "### Continuity Equalities" in prompt
    assert "capital_before == 직전 capital_after" in prompt


def test_wuxguide_tr_prompt_includes_harness_digest_section() -> None:
    prompt = build_wuxguide_prompt(
        draft_blocks=[],
        roadmap_blocks=None,
        meta={"title": "Demo", "genre": "wuxia", "protagonist": "Hero", "logline": "Climb the realm ladder."},
        start=1,
        batch_size=3,
        mode="flash",
    )

    assert "## Harness Digest" in prompt
    assert "- family: wuxguide" in prompt
    assert "### Lexicon Bans" in prompt
    assert "genre_ext.realm_before == previous realm_after" in prompt


def _make_history_block(block_no: int, opponent: str, weakness: str) -> dict:
    return {
        "block_id": f"Block {block_no}",
        "title": f"샘플 제목 {block_no}",
        "content": {
            "context": "x" * 120,
            "event_villain": "x" * 80,
            "solution": "x" * 120,
            "reward": "x" * 80,
        },
        "stakes": "x" * 50,
        "foreshadow": ["다음 질문이 승인선 공백을 찌른다"] if block_no < 10 else [],
        "callback": ["앞선 질문이 승인선 공백을 찔렀다"] if block_no > 1 else [],
        "genre_ext": {
            "opponent": {"name": opponent, "weakness_exploited": weakness},
            "deal_type": f"deal_{block_no}",
            "method": f"method_{block_no}",
            "section_rotation": "rotation",
            "opening_progression": {
                "public_signboard_event": "없음",
                "representative_reevaluation": "대표가 주인공 판단을 인정한다" if block_no == 3 else "없음",
                "next_battlefield_ticket": "다음 협상장 입장권이 열린다" if block_no == 5 else "없음",
            },
        },
        "emotional_beat": {"type": "resolve" if block_no % 2 else "pressure"},
        "relationship_delta": [],
        "location": {"place": f"yard-{block_no}", "type": "yard", "macro_battlefield": "opening yard"},
        "regression_ext": {},
    }


def test_pattern_feedback_lines_empty_for_no_history() -> None:
    assert render_pattern_feedback_lines([]) == []


def test_pattern_feedback_lines_includes_frequent_opponent() -> None:
    blocks = [_make_history_block(i, "Same Corp", f"weakness_{i}") for i in range(1, 11)]
    lines = render_pattern_feedback_lines(blocks)
    joined = "\n".join(lines)
    assert "## 패턴 피드백" in joined
    assert "Same Corp" in joined


def test_blockguide_prompt_includes_pattern_feedback_when_history_present() -> None:
    blocks = [_make_history_block(i, "Same Corp", f"weakness_{i}") for i in range(1, 6)]
    prompt = build_blockguide_prompt(
        draft_blocks=blocks,
        roadmap_blocks=None,
        meta={"title": "Demo", "genre": "investment", "protagonist": "Hero", "logline": "Grow."},
        start=6,
        batch_size=3,
        mode="flash",
    )
    assert "## 패턴 피드백" in prompt
    assert "Same Corp" in prompt


def test_blockguide_prompt_includes_opening_bundle_contract() -> None:
    prompt = build_blockguide_prompt(
        draft_blocks=[],
        roadmap_blocks=None,
        meta={"title": "Demo", "genre": "investment", "protagonist": "Hero", "logline": "Grow."},
        start=1,
        batch_size=3,
        mode="flash",
    )

    assert "downstream 2~6화 분량 planning bundle" in prompt
    assert "location.macro_battlefield" in prompt
    assert "genre_ext.opening_progression" in prompt


def test_infer_work_id_from_canonical_artifact_paths() -> None:
    assert blockguide_harness.infer_work_id_from_path(Path("02_demo_tr_block_070_draft.json")) == "demo"
    assert blockguide_harness.infer_work_id_from_path(Path("02_bi_demo.json")) == "demo"
    assert blockguide_harness.infer_work_id_from_path(
        Path("treatments") / "preprocess" / "demo" / "source_manifest.json"
    ) == "demo"


def test_blockguide_prompt_includes_stage0_phase0_authority_context(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(blockguide_harness, "ROOT", tmp_path)
    work_id = "demo"
    preprocess_dir = tmp_path / "treatments" / "preprocess" / work_id

    _write_json(
        preprocess_dir / "source_manifest.json",
        {
            "work_identity": {
                "work_id": work_id,
                "title": "무일푼 후계자",
                "primary_profile": "business_growth_profile",
                "secondary_profile": "office_power_profile",
            },
            "canonical_sources": ["docs/demo.md"],
            "reference_only_sources": [],
            "core_materials": [],
            "npc_pool": [],
            "crisis_pool": [],
            "hard_constraints": [
                "초반 해법은 운영 현장과 반복 현금흐름이어야 한다.",
                "주식 시세를 첫 성장 엔진으로 쓰지 않는다.",
            ],
            "do_not_fake": [],
            "manual_audit_note": "시장을 보지 말고 운영 레인을 보라.",
        },
    )
    _write_json(
        preprocess_dir / "profile_lock.json",
        {
            "primary_profile": "business_growth_profile",
            "secondary_profile": "office_power_profile",
            "resource_axis": ["반복 현금흐름", "정산 레인", "구매 코드"],
            "power_axis": ["승인권", "정산권", "현장 대체 불가능성"],
            "control_axis": [],
            "payoff_axis": [],
            "failure_axis": ["개인 자금 동결", "승인 지연", "가문 내부 책임 전가"],
            "hud_interpretation": {},
        },
    )
    _write_json(
        preprocess_dir / "material_bundle_summary.json",
        {
            "events": [],
            "npc_candidates": [],
            "crisis_candidates": [],
            "terms": [],
            "scene_details": [],
            "notes": "장례-호텔-정산 확장 순서를 유지한다.",
            "opening_bundle_contract": {
                "bundle_window": "TR 2~6",
                "macro_battlefield": "장례식장 뒤문",
                "macro_battlefield_map": ["밥차", "셔틀", "세탁실"],
                "bundle_goal": "첫 반복매출과 대표 재평가를 동시에 벌어야 한다.",
                "first_signboard_block": 3,
                "representative_reevaluation_block": 4,
                "next_battlefield_ticket_block": 6,
                "timing_reconciliation_note": "Arc는 길어도 독자 보상은 TR 2~6에서 끝낸다.",
            },
        },
    )
    _write_json(
        preprocess_dir / "phase0_ready_snapshot.json",
        {
            "identity_locked": True,
            "profile_locked": True,
            "material_sufficient": True,
            "manual_audit_pass": True,
            "remaining_risks": [],
        },
    )
    _write_json(
        tmp_path / "treatments" / "phase0" / f"{work_id}_phase0_design.json",
        {
            "project": {
                "title_ko": "무일푼 후계자",
                "format": "support-system cashflow",
                "logline": "운영의 길목을 먹고 올라간다.",
            },
            "protagonist": {
                "name": "윤주인",
                "initial_goal": "첫 월 반복매출과 다음 전장 입장권을 얻는다.",
            },
            "phase0_design": {
                "hud_interpretation": {
                    "first_block_reward_rule": "첫 보상은 돈보다 입장권과 승인권이다."
                },
                "opening_bundle_contract": {
                    "bundle_window": "TR 2~6",
                    "macro_battlefield": "장례식장 뒤문",
                    "macro_battlefield_map": ["밥차", "셔틀", "세탁실"],
                    "bundle_goal": "첫 반복매출과 대표 재평가를 동시에 벌어야 한다.",
                    "first_signboard_block": 3,
                    "representative_reevaluation_block": 4,
                    "next_battlefield_ticket_block": 6,
                    "timing_reconciliation_note": "Arc는 길어도 독자 보상은 TR 2~6에서 끝낸다.",
                },
                "arcs": [
                    {
                        "arc_id": "ARC-01",
                        "title": "장례식장 뒤문",
                        "block_range": "1-10",
                        "entry_function": "카드가 잘리며 뒤문으로 밀려난다.",
                        "exit_function": "첫 반복매출과 함께 호텔 입장권이 열린다.",
                    }
                ],
            },
        },
    )

    planning_context = blockguide_harness.load_planning_context(work_id)
    meta = blockguide_harness.merge_prompt_meta({}, planning_context)
    prompt = build_blockguide_prompt(
        draft_blocks=[],
        roadmap_blocks=None,
        meta=meta,
        start=1,
        batch_size=3,
        mode="flash",
        planning_context_lines=blockguide_harness.render_planning_context_lines(planning_context),
    )

    assert "## Stage0 / Phase0 Authority" in prompt
    assert "- work_id: demo" in prompt
    assert "locked profiles: business_growth_profile / office_power_profile" in prompt
    assert "opening bundle goal: 첫 반복매출과 대표 재평가를 동시에 벌어야 한다." in prompt
    assert "opening timing targets: signboard B3 / reevaluation B4 / ticket B6" in prompt
    assert "- 제목: 무일푼 후계자" in prompt
    assert "- 주인공: 윤주인" in prompt
