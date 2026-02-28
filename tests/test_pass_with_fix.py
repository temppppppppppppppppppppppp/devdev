"""[TF-32] PASS_WITH_FIX verdict 도입 — Director 피드백 반영 경로 테스트."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.stage4_interview_round import Stage4InterviewRound
from modules.core.stage4_types import _RoundContext

# ── Helpers ──────────────────────────────────────────────────────


def _make_ctx():
    """Minimal Stage4 ProjectContext mock."""
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.current_project = MagicMock()
    ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {}}}
    ctx.current_project.db = MagicMock()
    ctx.current_project.db.get_recent_manuscripts.return_value = []
    ctx.current_project.db.get_manuscript.return_value = {"content": "이전 원고"}
    ctx.current_project.db.get_episode_bible.return_value = {}
    ctx.state_tracker = MagicMock()
    ctx.state_tracker.npc_registry = {}
    ctx.state_tracker.item_state_registry = {}
    ctx.state_tracker.get_npc_change_history.return_value = []
    ctx.state_tracker.check_destroyed_entity_in_manuscript.return_value = []
    ctx.state_tracker.in_world_timeline = []
    ctx.state_tracker.check_time_consistency.return_value = []
    ctx.agents = {
        "director": MagicMock(),
        "chief_writer": MagicMock(),
    }
    ctx.context_advisor = None
    ctx.memory = None
    ctx.get_module = MagicMock(return_value=None)
    ctx.quality_dashboard = None
    ctx.session_logger = None
    ctx.sys = MagicMock()
    ctx.sys.hud = MagicMock()
    ctx.sys.hud.pro_root = {}
    return ctx


_MANUSCRIPT_TEXT = "테스트 원고입니다. " * 200  # ~3600 chars


def _make_round_ctx(chief_writer=None):
    """Stage4 round context with mock agents."""
    cw = chief_writer or MagicMock()
    cw.generate_ensemble.return_value = [
        {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "balanced", "title": "테스트"},
        {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "dramatic", "title": "테스트2"},
        {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "calm", "title": "테스트3"},
    ]
    mv = MagicMock()
    mv.validate_all_candidates.return_value = [
        {"warnings": [], "warning_count": 0, "focus_points": [], "metrics": {"length": 3600}},
        {"warnings": [], "warning_count": 0, "focus_points": [], "metrics": {"length": 3600}},
        {"warnings": [], "warning_count": 0, "focus_points": [], "metrics": {"length": 3600}},
    ]
    cv = MagicMock()
    cv.validate.return_value = {"violations": [], "score_penalty": 0}
    bv = MagicMock()
    bv.validate.return_value = {"failures": []}
    cont_v = MagicMock()
    cont_v.validate.return_value = {"violations": [], "warnings": []}
    cont_v.check_frustration_streak.return_value = []

    return _RoundContext(
        chief_writer=cw,
        manuscript_validator=mv,
        consistency_validator=cv,
        blocking_validator=bv,
        continuity_validator=cont_v,
        next_ep=1,
        blueprint={"integrated_scenario": "테스트"},
        arc_data={"arc_no": 1},
        arc_pos=1,
        total_ep_in_arc=10,
        arc_tactical="전술",
        prev_text="이전 원고 텍스트",
        prev_ending="이전 엔딩",
        prev_manuscripts_text="",
        episode_digest="에피소드 요약",
        hud_report="HUD 리포트",
        current_inventory=[],
        current_martial_arts=[],
        dead_npcs=[],
        item_acquisition_timeline="",
        chain_link_section="",
        world_state_summary="",
        purism_prompt="",
        genre_name="investment",
        npc_equipment_summary="",
        effective_anti_trope="",
        intro_dna="",
        story_context="작품 설정",
        style_guide="문체 가이드",
        reference_anchor_prompt="",
        mandatory_context="",
        justification_prompt="",
        reflexion_prompt="",
    )


def _director_result_pass_with_fix(manuscript=_MANUSCRIPT_TEXT, score=93):
    """Director verdict: PASS_WITH_FIX."""
    return {
        "selected": "A",
        "verdict": "PASS_WITH_FIX",
        "score": score,
        "selection_reason": "합격이나 국소 수정 필요",
        "selected_candidate": {"manuscript": manuscript, "title": "수정 후 통과"},
        "state_updates": {"location": "사무실"},
        "feedback": {"issues": ["경미한 표현 어색함"], "action_items": ["1문단 대사를 자연스럽게 수정"]},
        "action_items": ["1문단 대사를 자연스럽게 수정"],
        "fix_scope": "inplace",
        "error_category": "",
    }


def _director_result_pass(manuscript=_MANUSCRIPT_TEXT, score=98):
    """Director verdict: PASS (clean)."""
    return {
        "selected": "A",
        "verdict": "PASS",
        "score": score,
        "selection_reason": "문제 없음",
        "selected_candidate": {"manuscript": manuscript, "title": "통과"},
        "state_updates": {},
        "feedback": {},
        "action_items": [],
        "fix_scope": "inplace",
        "error_category": "",
    }


# ── Tests ──────────────────────────────────────────────────────


class TestPassWithFixVerdict:
    """[TF-32] PASS_WITH_FIX verdict 분기 테스트."""

    def test_pass_with_fix_calls_inplace_patch(self):
        """PASS_WITH_FIX → chief_writer.inplace_patch 호출 확인."""
        ctx = _make_ctx()
        cw = MagicMock()
        _patched_text = "수정된 원고입니다. " * 200
        cw.generate_ensemble.return_value = [
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "balanced"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "dramatic"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "calm"},
        ]
        cw.inplace_patch.return_value = [{"manuscript": _patched_text}]
        ctx.agents["chief_writer"] = cw

        round_ctx = _make_round_ctx(chief_writer=cw)
        ctx.agents["director"].select_and_judge_ensemble.return_value = _director_result_pass_with_fix()

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "PASS_WITH_FIX"
        assert cw.inplace_patch.call_count == 1
        assert result.final_manuscript == _patched_text

    def test_pass_with_fix_fallback_on_inplace_failure(self):
        """PASS_WITH_FIX → inplace 실패 시 원본 유지 확인."""
        ctx = _make_ctx()
        cw = MagicMock()
        cw.generate_ensemble.return_value = [
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "balanced"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "dramatic"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "calm"},
        ]
        cw.inplace_patch.return_value = None  # inplace 실패
        ctx.agents["chief_writer"] = cw

        round_ctx = _make_round_ctx(chief_writer=cw)
        ctx.agents["director"].select_and_judge_ensemble.return_value = _director_result_pass_with_fix()

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "PASS_WITH_FIX"
        assert result.final_manuscript == _MANUSCRIPT_TEXT  # 원본 유지

    def test_pass_with_fix_quality_gate_rejects_low_score(self):
        """PASS_WITH_FIX + score < 90 → QualityGate에 의해 REJECT 전환."""
        ctx = _make_ctx()
        cw = MagicMock()
        cw.generate_ensemble.return_value = [
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "balanced"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "dramatic"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "calm"},
        ]
        cw.regenerate_with_feedback.return_value = [
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "rewrite"},
        ]
        ctx.agents["chief_writer"] = cw

        round_ctx = _make_round_ctx(chief_writer=cw)

        # score 85 < 90 → QualityGate에서 REJECT 강제
        ctx.agents["director"].select_and_judge_ensemble.return_value = _director_result_pass_with_fix(score=85)

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        # QualityGate에 의해 REJECT로 전환됨
        assert result.verdict == "REJECT"

    def test_pass_with_fix_short_patch_keeps_original(self):
        """PASS_WITH_FIX → inplace 결과가 2000자 미만이면 원본 유지."""
        ctx = _make_ctx()
        cw = MagicMock()
        cw.generate_ensemble.return_value = [
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "balanced"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "dramatic"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "calm"},
        ]
        cw.inplace_patch.return_value = [{"manuscript": "짧은 결과"}]  # < 2000자
        ctx.agents["chief_writer"] = cw

        round_ctx = _make_round_ctx(chief_writer=cw)
        ctx.agents["director"].select_and_judge_ensemble.return_value = _director_result_pass_with_fix()

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "PASS_WITH_FIX"
        assert result.final_manuscript == _MANUSCRIPT_TEXT  # 원본 유지 (짧은 패치 거부)

    def test_clean_pass_does_not_call_inplace(self):
        """순수 PASS → inplace_patch 미호출 확인."""
        ctx = _make_ctx()
        cw = MagicMock()
        cw.generate_ensemble.return_value = [
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "balanced"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "dramatic"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "calm"},
        ]
        ctx.agents["chief_writer"] = cw

        round_ctx = _make_round_ctx(chief_writer=cw)
        ctx.agents["director"].select_and_judge_ensemble.return_value = _director_result_pass()

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "PASS"
        assert cw.inplace_patch.call_count == 0


class TestExtractFixFeedback:
    """[TF-32] _extract_fix_feedback 헬퍼 단위 테스트."""

    def test_action_items_priority(self):
        """action_items가 있으면 우선 사용."""
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        result = ir._extract_fix_feedback(
            {
                "action_items": ["수정사항1", "수정사항2"],
                "feedback": {"issues": ["이슈1"]},
            }
        )
        assert "수정사항1" in result
        assert "수정사항2" in result

    def test_feedback_issues_fallback(self):
        """action_items 없으면 feedback.issues 사용."""
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        result = ir._extract_fix_feedback(
            {
                "action_items": [],
                "feedback": {"issues": ["이슈A", "이슈B"]},
            }
        )
        assert "이슈A" in result
        assert "이슈B" in result

    def test_empty_feedback(self):
        """피드백 없으면 빈 문자열."""
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        result = ir._extract_fix_feedback({})
        assert result == ""

    def test_none_action_items(self):
        """action_items=None → feedback.issues 폴백."""
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        result = ir._extract_fix_feedback(
            {
                "action_items": None,
                "feedback": {"issues": ["이슈"]},
            }
        )
        assert "이슈" in result


class TestAdaptiveDecisionPassWithFix:
    """[TF-32] adaptive_decision이 PASS_WITH_FIX를 올바르게 처리하는지."""

    def _make_grading_system(self):
        from modules.domain.agents.director_grading import DirectorGradingSystem

        mock_director = MagicMock()
        mock_director.adaptive_thresholds_enabled = True
        mock_director.genre = "investment"
        mock_director.base_pass_threshold = 65
        gs = DirectorGradingSystem(director=mock_director)
        return gs

    def test_pass_with_fix_low_score_becomes_conditional(self):
        """PASS_WITH_FIX + score < threshold → CONDITIONAL_PASS (adjusted)."""
        gs = self._make_grading_system()

        result = gs.apply_adaptive_decision(
            score=50,
            original_decision="PASS_WITH_FIX",
            arc_pos=1,
            total_eps=5,
            retry_count=0,
        )
        assert result["decision"] == "CONDITIONAL_PASS"
        assert result["adjusted"] is True

    def test_pass_with_fix_high_score_passes_through(self):
        """PASS_WITH_FIX + score >= threshold → 그대로 유지."""
        gs = self._make_grading_system()

        result = gs.apply_adaptive_decision(
            score=95,
            original_decision="PASS_WITH_FIX",
            arc_pos=1,
            total_eps=5,
            retry_count=0,
        )
        assert result["decision"] == "PASS_WITH_FIX"
        assert result["adjusted"] is False
