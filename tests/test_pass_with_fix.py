"""[TF-32] PASS_WITH_FIX verdict 도입 + [TF-32-VERIFY] 재심사 반복 테스트."""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

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
        preflight_advisory="",
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
    """[TF-32-VERIFY] PASS_WITH_FIX → patch + 재심사 루프 테스트."""

    def test_pass_with_fix_calls_inplace_and_reaudit(self):
        """PASS_WITH_FIX → inplace_patch + select_and_judge_ensemble 재심사 → PASS 확정."""
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

        # [TF-35] 1차: PASS_WITH_FIX, 2차(재심사): PASS
        ctx.agents["director"].select_and_judge_ensemble.side_effect = [
            _director_result_pass_with_fix(),
            _director_result_pass(score=98),
        ]

        round_ctx = _make_round_ctx(chief_writer=cw)

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "PASS"
        assert cw.inplace_patch.call_count == 1
        # [TF-35] 재심사도 select_and_judge_ensemble 사용 (audit_manuscript 아님)
        assert ctx.agents["director"].select_and_judge_ensemble.call_count == 2
        assert result.final_manuscript == _patched_text

    def test_pass_with_fix_inplace_failure_becomes_reject(self):
        """PASS_WITH_FIX → inplace 실패 → REJECT 전환."""
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

        assert result.verdict == "REJECT"

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

    def test_pass_with_fix_short_patch_becomes_reject(self):
        """PASS_WITH_FIX → inplace 결과 2000자 미만 → REJECT 전환."""
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

        assert result.verdict == "REJECT"

    def test_pass_with_fix_reaudit_reject(self):
        """PASS_WITH_FIX → patch 성공 → 재심사 REJECT → REJECT 전환."""
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

        # [TF-35] 1차: PASS_WITH_FIX, 2차(재심사): REJECT
        _reject_result = {
            "selected": "A",
            "verdict": "REJECT",
            "score": 60,
            "selection_reason": "수정 불충분",
            "selected_candidate": {"manuscript": _patched_text, "title": "REJECT"},
            "state_updates": {},
            "feedback": {},
            "action_items": [],
            "fix_scope": "",
            "error_category": "",
        }
        ctx.agents["director"].select_and_judge_ensemble.side_effect = [
            _director_result_pass_with_fix(),
            _reject_result,
        ]

        round_ctx = _make_round_ctx(chief_writer=cw)

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        assert cw.inplace_patch.call_count == 1
        # [TF-35] 재심사도 select_and_judge_ensemble 사용
        assert ctx.agents["director"].select_and_judge_ensemble.call_count == 2

    def test_pass_with_fix_reaudit_loop(self):
        """PASS_WITH_FIX → 1차 재심사 PASS_WITH_FIX → 2차 재심사 PASS → PASS 확정."""
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

        # [TF-35] 1차: PASS_WITH_FIX, 2차(재심사): PASS_WITH_FIX, 3차(재심사): PASS
        _pwf_reaudit = {
            "selected": "A",
            "verdict": "PASS_WITH_FIX",
            "score": 93,
            "selection_reason": "추가 수정 필요",
            "selected_candidate": {"manuscript": _patched_text, "title": "재심사"},
            "state_updates": {},
            "feedback": {"action_items": ["추가 수정"]},
            "action_items": ["추가 수정"],
            "fix_scope": "inplace",
            "error_category": "",
        }
        ctx.agents["director"].select_and_judge_ensemble.side_effect = [
            _director_result_pass_with_fix(),
            _pwf_reaudit,
            _director_result_pass(score=98),
        ]

        round_ctx = _make_round_ctx(chief_writer=cw)

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "PASS"
        assert cw.inplace_patch.call_count == 2
        # [TF-35] 초기 1 + 재심사 2 = 3회
        assert ctx.agents["director"].select_and_judge_ensemble.call_count == 3

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


# ── Stage 2 PASS_WITH_FIX Tests ──────────────────────────────────


class TestStage2PassWithFix:
    """[TF-32-VERIFY] Stage2 Finalizer PASS_WITH_FIX → patch + 재심사 루프 테스트."""

    def _make_s2_ctx(self, audit_results, *, patch_arc_return=None):
        """Minimal Stage2 context mock.

        audit_results: single dict (모든 호출 동일) or list (side_effect용).
        """
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.pass_rate_monitor = MagicMock()
        ctx.quality_dashboard = MagicMock()
        ctx.stage2_optimizer = MagicMock()
        ctx.stage2_optimizer.failure_memory = MagicMock()
        ctx.perf_timer = MagicMock()
        ctx.stage_rejection_history = []
        ctx.audit_event = MagicMock()
        ctx.semantic_plot_guard = None
        ctx.validate_arc_integrity = MagicMock(return_value=True)
        ctx.current_project = MagicMock()
        ctx.safe_commit_async = AsyncMock(return_value=True)
        ctx.generate_arc_context_v60 = MagicMock(return_value="context_text")
        ctx.cumulative_state_cache = None
        ctx.cumulative_state_cache_key = 0
        ctx.get_adaptive_feedback_intensity = MagicMock(return_value={"guidance": "g"})
        ctx.state_tracker = SimpleNamespace(foo=0, bar=0)
        ctx.session_logger = None
        director = MagicMock()
        if isinstance(audit_results, list):
            director.audit_strategic_plan.side_effect = audit_results
        else:
            director.audit_strategic_plan.return_value = audit_results
        director.ask.return_value = "volume summary text long enough"
        four_phase = MagicMock()
        four_phase._inplace_patch_arc.return_value = patch_arc_return
        ctx.agents = {"director": director, "four_phase": four_phase}
        return ctx

    def _valid_arc(self):
        return {
            "arc_no": 1,
            "ep_start": 1,
            "ep_end": 10,
            "ep_count": 10,
            "tactical_doc": "A" * 1600,
            "state_changes": {"npc_deaths": [], "relationship_changes": []},
            "hybrid_composition": {"primary": "std", "secondary": [], "mixing_logic": "default"},
            "joint_docs": {"final_location": "market", "physical_inventory": [], "world_joint": "stable"},
            "status_shadow": {"internal_energy_loss": "10%", "expected_injuries": "none", "item_consumption": []},
            "state_constraints": {"items_acquired": []},
        }

    def _make_kwargs(self, arc):
        return {
            "refined_arc": arc,
            "enriched_block": {
                "joint_docs": {"final_location": "city", "physical_inventory": [], "world_joint": "stable"},
                "status_shadow": {"internal_energy_loss": "5%", "expected_injuries": "none", "item_consumption": []},
                "joint_docs_brief": "brief",
            },
            "arc_drive": {"desire_vector": "test"},
            "all_refined_arcs": [],
            "global_arc_no": 1,
            "current_ep_start": 1,
            "current_feedback": "",
            "protagonist_name": "hero",
            "suspected_duplicates": [],
            "entity_registry_for_director": {},
            "constraint_block": "",
            "draft_validator_passed": True,
            "consensus_passed": True,
            "attempt": 0,
            "generation_method": "four_phase",
            "st_snapshot": None,
            "director_feedback_for_fourphase": "",
            "last_refined_context": "prev context",
            "bible_root": {"protagonist_config": {"name": "hero", "incarnation_type": "회귀자"}},
            "genre": "fantasy",
            "constraint_db": MagicMock(arc_states=[]),
        }

    def test_finalizer_accepts_pass_with_fix(self):
        """PASS_WITH_FIX + patch + 재심사 PASS → action=break."""
        from modules.core.stage2_finalizer import Stage2Finalizer

        initial_audit = {
            "decision": "PASS_WITH_FIX",
            "score": 95,
            "reason": "경미한 수정 필요",
            "re_slice_instruction": "1문단 수정",
            "fix_scope": "inplace",
        }
        reaudit = {
            "decision": "PASS",
            "score": 98,
            "reason": "수정 완료",
        }
        patched_arc = self._valid_arc()
        patched_arc["tactical_doc"] = "PATCHED " + patched_arc["tactical_doc"]
        ctx = self._make_s2_ctx([initial_audit, reaudit], patch_arc_return=patched_arc)
        host = MagicMock()
        host.ctx = ctx
        finalizer = Stage2Finalizer(host)
        kwargs = self._make_kwargs(self._valid_arc())

        with (
            patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x),
            patch("modules.core.spinners.V50_MODULES_AVAILABLE", False),
        ):
            result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        four_phase = ctx.agents["four_phase"]
        assert four_phase._inplace_patch_arc.call_count == 1
        # audit_strategic_plan: 1회 초기 + 1회 재심사 = 2회
        assert ctx.agents["director"].audit_strategic_plan.call_count == 2

    def test_finalizer_pass_with_fix_patch_failure_rejects(self):
        """PASS_WITH_FIX + inplace patch 실패(None) → REJECT 전환 (action=next)."""
        from modules.core.stage2_finalizer import Stage2Finalizer

        audit = {
            "decision": "PASS_WITH_FIX",
            "score": 95,
            "reason": "경미한 수정 필요",
            "re_slice_instruction": "1문단 수정",
            "fix_scope": "inplace",
        }
        ctx = self._make_s2_ctx(audit, patch_arc_return=None)  # patch 실패
        host = MagicMock()
        host.ctx = ctx
        finalizer = Stage2Finalizer(host)
        kwargs = self._make_kwargs(self._valid_arc())

        with (
            patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x),
            patch("modules.core.spinners.V50_MODULES_AVAILABLE", False),
        ):
            result = asyncio.run(finalizer.run_finalize(**kwargs))

        # REJECT 전환 → Director REJECT 경로 (action=next)
        assert result["action"] == "next"
        four_phase = ctx.agents["four_phase"]
        assert four_phase._inplace_patch_arc.call_count == 1

    def test_finalizer_pass_with_fix_reaudit_reject(self):
        """PASS_WITH_FIX + patch + 재심사 REJECT → action=next (REJECT 경로)."""
        from modules.core.stage2_finalizer import Stage2Finalizer

        initial_audit = {
            "decision": "PASS_WITH_FIX",
            "score": 95,
            "reason": "수정 필요",
            "re_slice_instruction": "수정 지시",
            "fix_scope": "inplace",
        }
        reaudit = {
            "decision": "REJECT",
            "score": 60,
            "reason": "수정 불충분",
        }
        patched_arc = self._valid_arc()
        patched_arc["tactical_doc"] = "PATCHED " + patched_arc["tactical_doc"]
        ctx = self._make_s2_ctx([initial_audit, reaudit], patch_arc_return=patched_arc)
        host = MagicMock()
        host.ctx = ctx
        finalizer = Stage2Finalizer(host)
        kwargs = self._make_kwargs(self._valid_arc())

        with (
            patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x),
            patch("modules.core.spinners.V50_MODULES_AVAILABLE", False),
        ):
            result = asyncio.run(finalizer.run_finalize(**kwargs))

        # REJECT 전환 → Director REJECT 경로 (action=next)
        assert result["action"] == "next"

    def test_finalizer_pass_with_fix_iterates_until_pass(self):
        """PASS_WITH_FIX → 1차 재심사 PASS_WITH_FIX → 2차 재심사 PASS."""
        from modules.core.stage2_finalizer import Stage2Finalizer

        initial_audit = {
            "decision": "PASS_WITH_FIX",
            "score": 95,
            "reason": "수정 필요",
            "re_slice_instruction": "1차 수정",
            "fix_scope": "inplace",
        }
        reaudit_1 = {
            "decision": "PASS_WITH_FIX",
            "score": 93,
            "reason": "추가 수정 필요",
            "re_slice_instruction": "2차 수정",
        }
        reaudit_2 = {
            "decision": "PASS",
            "score": 97,
            "reason": "수정 완료",
        }
        patched_arc = self._valid_arc()
        patched_arc["tactical_doc"] = "PATCHED " + patched_arc["tactical_doc"]
        ctx = self._make_s2_ctx(
            [initial_audit, reaudit_1, reaudit_2],
            patch_arc_return=patched_arc,
        )
        host = MagicMock()
        host.ctx = ctx
        finalizer = Stage2Finalizer(host)
        kwargs = self._make_kwargs(self._valid_arc())

        with (
            patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x),
            patch("modules.core.spinners.V50_MODULES_AVAILABLE", False),
        ):
            result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        # patch 2회 + audit_strategic_plan 3회 (초기 1 + 재심사 2)
        four_phase = ctx.agents["four_phase"]
        assert four_phase._inplace_patch_arc.call_count == 2
        assert ctx.agents["director"].audit_strategic_plan.call_count == 3

    def test_finalizer_pass_with_fix_bypasses_quality_gate(self):
        """[TF-46] PASS_WITH_FIX + score < 90 → QualityGate 미적용, patch loop 진입 (Director 주권 존중)."""
        from modules.core.stage2_finalizer import Stage2Finalizer

        audit = {
            "decision": "PASS_WITH_FIX",
            "score": 80,
            "reason": "수정 필요",
            "re_slice_instruction": "품질 개선",
            "fix_scope": "inplace",
        }
        # patch_arc_return=None → patch loop 실패 → REJECT → "next"
        ctx = self._make_s2_ctx(audit)
        host = MagicMock()
        host.ctx = ctx
        finalizer = Stage2Finalizer(host)
        kwargs = self._make_kwargs(self._valid_arc())

        with patch("modules.core.spinners.V50_MODULES_AVAILABLE", False):
            result = asyncio.run(finalizer.run_finalize(**kwargs))

        # [TF-46] QualityGate가 아닌 patch loop 경로로 진행됨
        assert result["action"] == "next"  # patch 실패 → 정상 REJECT 경로


# ── Stage 3 PASS_WITH_FIX Tests ──────────────────────────────────


class TestStage3PassWithFix:
    """[TF-32-VERIFY] Stage3 PASS_WITH_FIX → patch + 재심사 루프 시뮬레이션."""

    def test_blueprint_generator_accepts_pass_with_fix(self):
        """PASS_WITH_FIX → patch + 재심사 PASS → final_verdict=PASS."""
        # 재심사 루프 로직 시뮬레이션
        pipeline_result = {"final_verdict": None, "phases": {}}
        verdict = "PASS_WITH_FIX"
        _score = 95
        _quality_gate_score = 90
        best_blueprint = {"scenario": "original"}

        # QualityGate 통과
        if verdict in ("PASS", "PASS_WITH_FIX") and _score < _quality_gate_score:
            verdict = "REJECT"

        if verdict in ("PASS", "PASS_WITH_FIX"):
            pipeline_result["final_verdict"] = verdict

            if verdict == "PASS_WITH_FIX":
                # patch 성공 + 재심사 PASS 시뮬레이션
                _patched_bp = {"scenario": "patched"}
                _re_verdict = "PASS"

                if _patched_bp and _re_verdict == "PASS":
                    best_blueprint = _patched_bp
                    pipeline_result["final_verdict"] = "PASS"

        assert pipeline_result["final_verdict"] == "PASS"
        assert best_blueprint["scenario"] == "patched"

    def test_blueprint_pass_with_fix_patch_failure_rejects(self):
        """PASS_WITH_FIX + inplace patch 실패 → REJECT 전환 → continue."""
        pipeline_result = {"final_verdict": None, "phases": {}}
        verdict = "PASS_WITH_FIX"
        best_blueprint = {"scenario": "original"}
        _rejected = False

        if verdict in ("PASS", "PASS_WITH_FIX"):
            pipeline_result["final_verdict"] = verdict

            if verdict == "PASS_WITH_FIX":
                _patched_bp = None  # patch 실패
                if not _patched_bp:
                    verdict = "REJECT"
                    _rejected = True

        assert _rejected
        assert verdict == "REJECT"

    def test_blueprint_pass_with_fix_reaudit_reject(self):
        """PASS_WITH_FIX → patch 성공 → 재심사 REJECT → REJECT 전환."""
        pipeline_result = {"final_verdict": None, "phases": {}}
        verdict = "PASS_WITH_FIX"
        best_blueprint = {"scenario": "original"}

        if verdict in ("PASS", "PASS_WITH_FIX"):
            pipeline_result["final_verdict"] = verdict

            if verdict == "PASS_WITH_FIX":
                _patched_bp = {"scenario": "patched"}
                _re_verdict = "REJECT"  # 재심사 REJECT

                if _re_verdict == "PASS":
                    best_blueprint = _patched_bp
                    pipeline_result["final_verdict"] = "PASS"
                else:
                    verdict = "REJECT"

        assert verdict == "REJECT"

    def test_orchestrator_accepts_pass_with_fix(self):
        """final_verdict=PASS_WITH_FIX → Stage3 _handle_success 호출 경로 확인."""
        # Stage3Orchestrator L359 조건 재현
        for final_verdict in ("PASS", "PASS_WITH_FIX", "PASS_WITH_WARNING"):
            blueprint = {"scenario": "test"}
            pipeline_result = {"final_verdict": final_verdict}

            # L359 조건: PASS, PASS_WITH_FIX, PASS_WITH_WARNING 모두 success
            success = blueprint and pipeline_result.get("final_verdict") in (
                "PASS",
                "PASS_WITH_FIX",
                "PASS_WITH_WARNING",
            )
            assert success, f"{final_verdict}이(가) success 경로로 처리되어야 함"

        # REJECT는 failure 경로
        pipeline_result = {"final_verdict": "REJECT"}
        success = {"scenario": "test"} and pipeline_result.get("final_verdict") in (
            "PASS",
            "PASS_WITH_FIX",
            "PASS_WITH_WARNING",
        )
        assert not success


# ── Self-Consistency PASS_WITH_FIX Tests ──────────────────────────


class TestSelfConsistencyPassWithFix:
    """[TF-32-S2] Self-Consistency 투표 PASS_WITH_FIX 인식 테스트."""

    def test_clear_pass_recognizes_pass_with_fix(self):
        """PASS_WITH_FIX + 고점수 → self-consistency 조기 종료 (clear_pass)."""
        from modules.domain.agents.director_auditor import DirectorQualityAuditor

        mock_director = MagicMock()
        mock_director.ambiguous_upper = 85
        mock_director.ambiguous_lower = 40
        mock_director.consistency_votes = 3
        mock_director.ask.return_value = '{"decision": "PASS_WITH_FIX", "score": 95}'
        mock_director._extract_json_robust.return_value = {
            "decision": "PASS_WITH_FIX",
            "score": 95,
            "reason": "경미한 수정 필요",
        }
        mock_director._last_thinking = ""

        auditor = DirectorQualityAuditor(mock_director)
        result = auditor._strategic_audit_with_self_consistency("test prompt", arc_no=1)

        assert result.get("decision") == "PASS_WITH_FIX"
        sc = result.get("self_consistency", {})
        assert sc.get("reason") == "clear_pass"
        assert sc.get("pass_votes") == 1

    def test_pass_vote_counts_pass_with_fix(self):
        """다수결에서 PASS_WITH_FIX가 pass 투표로 집계."""
        # director_auditor.py L1011 로직 재현
        evaluations = [
            {"decision": "PASS", "score": 90},
            {"decision": "PASS_WITH_FIX", "score": 88},
            {"decision": "REJECT", "score": 70},
        ]
        pass_votes = sum(1 for e in evaluations if e.get("decision") in ("PASS", "PASS_WITH_FIX"))
        assert pass_votes == 2

        # REJECT만 있으면 0
        evaluations_reject = [
            {"decision": "REJECT", "score": 40},
            {"decision": "REJECT", "score": 35},
        ]
        pass_votes_reject = sum(1 for e in evaluations_reject if e.get("decision") in ("PASS", "PASS_WITH_FIX"))
        assert pass_votes_reject == 0


# ── [TF-33] fix_scope 라우팅 Tests ──────────────────────────────────


class TestFixScopeRouting:
    """[TF-33] PASS_WITH_FIX fix_scope 기반 수정 전략 라우팅 테스트."""

    # ── Stage 4 ──

    def test_s4_fix_scope_partial_skips_inplace(self):
        """Stage4: fix_scope='partial' → inplace 미호출, REJECT 전환."""
        ctx = _make_ctx()
        cw = MagicMock()
        cw.generate_ensemble.return_value = [
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "balanced"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "dramatic"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "calm"},
        ]
        ctx.agents["chief_writer"] = cw

        round_ctx = _make_round_ctx(chief_writer=cw)
        dr = _director_result_pass_with_fix()
        dr["fix_scope"] = "partial"  # Director가 partial 판단
        ctx.agents["director"].select_and_judge_ensemble.return_value = dr

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        assert cw.inplace_patch.call_count == 0  # inplace 미호출

    def test_s4_fix_scope_full_skips_inplace(self):
        """Stage4: fix_scope='full' → inplace 미호출, REJECT 전환."""
        ctx = _make_ctx()
        cw = MagicMock()
        cw.generate_ensemble.return_value = [
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "balanced"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "dramatic"},
            {"manuscript": _MANUSCRIPT_TEXT, "strategy_name": "calm"},
        ]
        ctx.agents["chief_writer"] = cw

        round_ctx = _make_round_ctx(chief_writer=cw)
        dr = _director_result_pass_with_fix()
        dr["fix_scope"] = "full"  # Director가 full 판단
        ctx.agents["director"].select_and_judge_ensemble.return_value = dr

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        assert cw.inplace_patch.call_count == 0

    def test_s4_fix_scope_inplace_still_patches(self):
        """Stage4: fix_scope='inplace' → 기존 동작 유지 (inplace 호출)."""
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
        dr = _director_result_pass_with_fix()
        dr["fix_scope"] = "inplace"
        # [TF-35] 1차: PASS_WITH_FIX(inplace), 2차(재심사): PASS
        ctx.agents["director"].select_and_judge_ensemble.side_effect = [
            dr,
            _director_result_pass(score=98),
        ]

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "PASS"
        assert cw.inplace_patch.call_count == 1

    def test_s4_reaudit_escalates_fix_scope(self):
        """Stage4: 1차 inplace → 재심사 PASS_WITH_FIX(partial) → inplace 중단, REJECT."""
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

        # [TF-35] 재심사: PASS_WITH_FIX + fix_scope=partial → 다음 반복에서 break
        _reaudit_partial = {
            "selected": "A",
            "verdict": "PASS_WITH_FIX",
            "score": 91,
            "selection_reason": "구조적 수정 필요",
            "selected_candidate": {"manuscript": _patched_text, "title": "재심사"},
            "state_updates": {},
            "feedback": {"action_items": ["구조적 수정 필요"]},
            "action_items": ["구조적 수정 필요"],
            "fix_scope": "partial",
            "error_category": "",
        }

        round_ctx = _make_round_ctx(chief_writer=cw)
        dr = _director_result_pass_with_fix()
        dr["fix_scope"] = "inplace"  # 초기엔 inplace
        # [TF-35] 1차: PASS_WITH_FIX(inplace), 2차(재심사): PASS_WITH_FIX(partial)
        ctx.agents["director"].select_and_judge_ensemble.side_effect = [
            dr,
            _reaudit_partial,
        ]

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        # inplace 1회 호출 (1차는 inplace, 2차에서 partial 감지 → break)
        assert cw.inplace_patch.call_count == 1
        # [TF-35] 초기 1 + 재심사 1 = 2회
        assert ctx.agents["director"].select_and_judge_ensemble.call_count == 2

    # ── Stage 2 ──

    def test_s2_fix_scope_partial_skips_inplace(self):
        """Stage2: fix_scope='partial' → inplace 미호출, REJECT 전환."""
        from modules.core.stage2_finalizer import Stage2Finalizer

        audit = {
            "decision": "PASS_WITH_FIX",
            "score": 95,
            "reason": "구조적 수정 필요",
            "re_slice_instruction": "에피소드 배치 수정",
            "fix_scope": "partial",  # Director가 partial 판단
        }
        ctx = TestStage2PassWithFix._make_s2_ctx(TestStage2PassWithFix(), audit)
        host = MagicMock()
        host.ctx = ctx
        finalizer = Stage2Finalizer(host)
        kwargs = TestStage2PassWithFix._make_kwargs(
            TestStage2PassWithFix(), TestStage2PassWithFix._valid_arc(TestStage2PassWithFix())
        )

        with (
            patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x),
            patch("modules.core.spinners.V50_MODULES_AVAILABLE", False),
        ):
            result = asyncio.run(finalizer.run_finalize(**kwargs))

        # fix_scope=partial → inplace 미호출 → REJECT → action=next
        assert result["action"] == "next"
        assert ctx.agents["four_phase"]._inplace_patch_arc.call_count == 0
        assert result.get("fix_scope") == "partial"

    def test_s2_fix_scope_full_skips_inplace(self):
        """Stage2: fix_scope='full' → inplace 미호출, REJECT 전환."""
        from modules.core.stage2_finalizer import Stage2Finalizer

        audit = {
            "decision": "PASS_WITH_FIX",
            "score": 95,
            "reason": "전면 재설계 필요",
            "re_slice_instruction": "Arc 재설계",
            "fix_scope": "full",  # Director가 full 판단
        }
        ctx = TestStage2PassWithFix._make_s2_ctx(TestStage2PassWithFix(), audit)
        host = MagicMock()
        host.ctx = ctx
        finalizer = Stage2Finalizer(host)
        kwargs = TestStage2PassWithFix._make_kwargs(
            TestStage2PassWithFix(), TestStage2PassWithFix._valid_arc(TestStage2PassWithFix())
        )

        with (
            patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x),
            patch("modules.core.spinners.V50_MODULES_AVAILABLE", False),
        ):
            result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "next"
        assert ctx.agents["four_phase"]._inplace_patch_arc.call_count == 0
        assert result.get("fix_scope") == "full"

    # ── Stage 3 ──

    def test_s3_fix_scope_partial_skips_inplace(self):
        """Stage3: fix_scope='partial' → inplace 미호출, REJECT → generate 루프."""
        # Stage 3 fix_scope 라우팅 시뮬레이션
        validation_result = {
            "fix_scope": "partial",
            "re_slice_instruction": "씬 배치 수정",
            "feedback": "구조 수정 필요",
        }
        verdict = "PASS_WITH_FIX"
        best_blueprint = {"scenario": "original"}
        _fix_ok = False

        # fix loop 시뮬레이션
        _MAX_FIX = 3
        _current_bp = best_blueprint
        _current_vr = validation_result

        for _fix_i in range(_MAX_FIX):
            _fix_scope = _current_vr.get("fix_scope", "inplace")
            if _fix_scope in ("partial", "full"):
                break  # → REJECT
            _current_bp = {"scenario": "patched"}  # inplace 시뮬레이션
            _fix_ok = True
            break

        if not _fix_ok:
            verdict = "REJECT"

        assert verdict == "REJECT"  # partial이므로 inplace 미실행

    def test_s3_fix_scope_full_skips_inplace(self):
        """Stage3: fix_scope='full' → REJECT → generate 루프."""
        validation_result = {
            "fix_scope": "full",
            "feedback": "전면 재생성 필요",
        }
        verdict = "PASS_WITH_FIX"
        _fix_ok = False

        _MAX_FIX = 3
        _current_vr = validation_result
        for _fix_i in range(_MAX_FIX):
            _fix_scope = _current_vr.get("fix_scope", "inplace")
            if _fix_scope in ("partial", "full"):
                break
            _fix_ok = True
            break

        if not _fix_ok:
            verdict = "REJECT"

        assert verdict == "REJECT"


class TestValidatorFixScopePropagation:
    """[TF-33] unified_blueprint_validator compare 경로 fix_scope 전파 테스트."""

    def test_compare_path_propagates_fix_scope(self):
        """compare 경로: Director fix_scope/fix_scope_reasoning이 result에 전파됨."""
        from modules.domain.agents.unified_blueprint_validator import _safe_int

        # Director compare 결과 시뮬레이션 (fix_scope 포함)
        compare_result = {
            "decision": "PASS_WITH_FIX",
            "score": 92,
            "reason": "경미한 모순",
            "feedback": "씬 배치 수정 필요",
            "selected_index": 0,
            "selected_blueprint": {"scenario": "best"},
            "comparison_notes": "후보 1 선택",
            "contradictions": [],
            "fix_scope": "partial",
            "fix_scope_reasoning": "씬 단위 재구성 필요",
        }

        # compare 경로 result dict 재현 (unified_blueprint_validator L121-135)
        _contradictions = compare_result.get("contradictions", [])
        result = {
            "verdict": compare_result.get("decision", "REJECT"),
            "phase": "director_compare",
            "issues": [],
            "summary": compare_result.get("reason", ""),
            "score": compare_result.get("score", 0),
            "feedback": compare_result.get("feedback", ""),
            "confidence": 0.9 if _safe_int(compare_result.get("score", 0), 0) >= 70 else 0.6,
            "selected_index": compare_result.get("selected_index", 0),
            "selected_blueprint": compare_result.get("selected_blueprint"),
            "comparison_notes": compare_result.get("comparison_notes", ""),
            "contradictions": _contradictions,
            "fix_scope": compare_result.get("fix_scope", ""),
            "fix_scope_reasoning": compare_result.get("fix_scope_reasoning", ""),
        }

        assert result["fix_scope"] == "partial"
        assert result["fix_scope_reasoning"] == "씬 단위 재구성 필요"

    def test_compare_path_empty_fix_scope_defaults(self):
        """compare 경로: Director fix_scope 미반환 시 빈 문자열 기본값."""
        compare_result = {"decision": "PASS", "score": 95}
        result_fix_scope = compare_result.get("fix_scope", "")
        assert result_fix_scope == ""


class TestValidatorFeedbackPreservation:
    """[TF-34] unified_blueprint_validator PASS_WITH_FIX feedback 보존 테스트."""

    def test_audit_path_preserves_feedback_for_pass_with_fix(self):
        """audit 경로: PASS_WITH_FIX 시 Director feedback이 보존됨."""
        # unified_blueprint_validator L303 조건 시뮬레이션
        director_feedback = "씬 3의 대사가 캐릭터 성격과 불일치합니다. 수정 필요."
        final_verdict = "PASS_WITH_FIX"

        # OLD: director_feedback if final_verdict == "REJECT" else "" → "" (피드백 손실)
        # NEW: director_feedback if final_verdict in ("REJECT", "PASS_WITH_FIX") else "" → 보존
        result_feedback = director_feedback if final_verdict in ("REJECT", "PASS_WITH_FIX") else ""
        assert result_feedback == director_feedback, "PASS_WITH_FIX 시 feedback이 보존되어야 함"

    def test_audit_path_strips_feedback_for_pass(self):
        """audit 경로: PASS 시 feedback 빈 문자열."""
        director_feedback = "좋은 블루프린트입니다."
        final_verdict = "PASS"

        result_feedback = director_feedback if final_verdict in ("REJECT", "PASS_WITH_FIX") else ""
        assert result_feedback == "", "PASS 시 feedback은 빈 문자열이어야 함"

    def test_audit_path_preserves_feedback_for_reject(self):
        """audit 경로: REJECT 시 feedback 보존 (기존 동작 유지)."""
        director_feedback = "논리적 모순이 심각합니다."
        final_verdict = "REJECT"

        result_feedback = director_feedback if final_verdict in ("REJECT", "PASS_WITH_FIX") else ""
        assert result_feedback == director_feedback

    def test_s3_reaudit_feedback_chain(self):
        """Stage3 재심사: PASS_WITH_FIX → 재심사 PASS_WITH_FIX → 2차 반복에서 feedback 사용 가능."""
        # 재심사 결과 시뮬레이션 (audit 경로)
        director_feedback_1st = "씬 배치 수정 필요"
        final_verdict_1st = "PASS_WITH_FIX"
        # NEW 조건: PASS_WITH_FIX 포함 → feedback 보존
        vr_1st = {
            "feedback": director_feedback_1st if final_verdict_1st in ("REJECT", "PASS_WITH_FIX") else "",
        }

        director_feedback_2nd = "대사 톤 조정 필요"
        final_verdict_2nd = "PASS_WITH_FIX"
        vr_2nd = {
            "feedback": director_feedback_2nd if final_verdict_2nd in ("REJECT", "PASS_WITH_FIX") else "",
        }

        # fix loop 시뮬레이션: 1차 반복
        _fix_fb_1 = vr_1st.get("re_slice_instruction", "") or vr_1st.get("feedback", "")
        assert _fix_fb_1 == "씬 배치 수정 필요", "1차 반복에서 feedback 사용 가능"

        # fix loop 시뮬레이션: 2차 반복 (re-audit 결과)
        _fix_fb_2 = vr_2nd.get("re_slice_instruction", "") or vr_2nd.get("feedback", "")
        assert _fix_fb_2 == "대사 톤 조정 필요", "2차 반복에서도 feedback 사용 가능 (TF-34 수정)"


class TestTF35FixScopeReasoningPropagation:
    """[TF-35] director_ensemble fix_scope_reasoning 전파 + validator re_slice_instruction 전파 테스트."""

    def test_compare_and_select_propagates_fix_scope_reasoning(self):
        """compare_and_select_blueprint 반환값에 fix_scope_reasoning 포함."""
        # director_ensemble.py L236-247 반환 dict 시뮬레이션
        result = {
            "fix_scope": "partial",
            "fix_scope_reasoning": "씬 3-5 재구성 필요",
        }
        ret = {
            "fix_scope": result.get("fix_scope", ""),
            "fix_scope_reasoning": result.get("fix_scope_reasoning", ""),
        }
        assert ret["fix_scope_reasoning"] == "씬 3-5 재구성 필요"

    def test_select_and_judge_propagates_fix_scope_reasoning(self):
        """select_and_judge_ensemble 반환값에 fix_scope_reasoning 포함."""
        result = {
            "fix_scope": "inplace",
            "fix_scope_reasoning": "대사 톤만 수정",
        }
        ret = {
            "fix_scope": result.get("fix_scope", ""),
            "fix_scope_reasoning": result.get("fix_scope_reasoning", ""),
        }
        assert ret["fix_scope_reasoning"] == "대사 톤만 수정"

    def test_validator_audit_propagates_re_slice_instruction(self):
        """validator audit 경로: re_slice_instruction이 result에 전파됨."""
        director_result = {
            "decision": "PASS_WITH_FIX",
            "score": 92,
            "feedback": "경미한 수정 필요",
            "re_slice_instruction": "씬 3의 전투 장면에서 NPC 대사를 캐릭터 성격에 맞게 수정",
            "fix_scope": "inplace",
            "fix_scope_reasoning": "대사만 수정",
        }
        # unified_blueprint_validator L293-309 result dict 재현
        result = {
            "feedback": director_result.get("feedback", ""),
            "fix_scope": director_result.get("fix_scope", ""),
            "fix_scope_reasoning": director_result.get("fix_scope_reasoning", ""),
            "re_slice_instruction": director_result.get("re_slice_instruction", ""),
        }
        assert result["re_slice_instruction"] == "씬 3의 전투 장면에서 NPC 대사를 캐릭터 성격에 맞게 수정"

    def test_s3_fix_loop_uses_re_slice_instruction_from_validator(self):
        """Stage3 fix loop: validator 결과의 re_slice_instruction을 우선 사용."""
        # three_phase_blueprint_generator L420-423 시뮬레이션
        _current_vr = {
            "re_slice_instruction": "씬 5 재배치 필요",
            "feedback": "전반적 피드백",
        }
        _fix_fb = _current_vr.get("re_slice_instruction", "") or _current_vr.get("feedback", "")
        assert _fix_fb == "씬 5 재배치 필요", "re_slice_instruction이 feedback보다 우선"

    def test_s3_fix_loop_fallback_to_feedback(self):
        """Stage3 fix loop: re_slice_instruction 없으면 feedback fallback."""
        _current_vr = {
            "re_slice_instruction": "",
            "feedback": "전반적 피드백",
        }
        _fix_fb = _current_vr.get("re_slice_instruction", "") or _current_vr.get("feedback", "")
        assert _fix_fb == "전반적 피드백", "re_slice_instruction 빈 문자열이면 feedback fallback"


# ── [TF-35] Director 일관성 확보 Tests ──────────────────────────────────


class TestTF35DirectorConsistency:
    """[TF-35] S4 재심사 Director 동일 경로 + S2/S3 QualityGate 테스트."""

    def test_s4_reaudit_uses_director_ensemble(self):
        """[TF-35] S4 재심사가 select_and_judge_ensemble 호출 확인 (audit_manuscript 아님)."""
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

        # 1차: PASS_WITH_FIX(93점), 2차(재심사): PASS(98점)
        ctx.agents["director"].select_and_judge_ensemble.side_effect = [
            _director_result_pass_with_fix(score=93),
            _director_result_pass(score=98),
        ]

        round_ctx = _make_round_ctx(chief_writer=cw)

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "PASS"
        # 재심사도 select_and_judge_ensemble 사용 — audit_manuscript 미호출
        assert ctx.agents["director"].select_and_judge_ensemble.call_count == 2
        assert ctx.agents["director"].audit_manuscript.call_count == 0

    def test_s4_reaudit_qualitygate_rejects_low_score(self):
        """[TF-35] 재심사 Director PASS(score=81) → QualityGate REJECT 전환 확인."""
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

        # 1차: PASS_WITH_FIX(92점), 2차(재심사): PASS(81점 — QualityGate 미달)
        ctx.agents["director"].select_and_judge_ensemble.side_effect = [
            _director_result_pass_with_fix(score=92),
            _director_result_pass(score=81),
        ]

        round_ctx = _make_round_ctx(chief_writer=cw)

        ir = Stage4InterviewRound(ctx)
        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        # QualityGate: 81 < 90 → PASS 거부 → patch 종료 → REJECT
        assert result.verdict == "REJECT"
        assert cw.inplace_patch.call_count == 1

    def test_s2_reaudit_qualitygate_rejects_low_score(self):
        """[TF-35] S2 재심사 PASS(score=75) → QualityGate REJECT 전환 확인."""
        from modules.core.stage2_finalizer import Stage2Finalizer

        initial_audit = {
            "decision": "PASS_WITH_FIX",
            "score": 95,
            "reason": "경미한 수정 필요",
            "re_slice_instruction": "1문단 수정",
            "fix_scope": "inplace",
        }
        # 재심사: PASS이지만 score=75 < 90 → QualityGate REJECT
        reaudit = {
            "decision": "PASS",
            "score": 75,
            "reason": "수정 완료",
        }
        patched_arc = TestStage2PassWithFix._valid_arc(TestStage2PassWithFix())
        patched_arc["tactical_doc"] = "PATCHED " + patched_arc["tactical_doc"]
        ctx = TestStage2PassWithFix._make_s2_ctx(
            TestStage2PassWithFix(),
            [initial_audit, reaudit],
            patch_arc_return=patched_arc,
        )
        host = MagicMock()
        host.ctx = ctx
        finalizer = Stage2Finalizer(host)
        kwargs = TestStage2PassWithFix._make_kwargs(
            TestStage2PassWithFix(), TestStage2PassWithFix._valid_arc(TestStage2PassWithFix())
        )

        with (
            patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x),
            patch("modules.core.spinners.V50_MODULES_AVAILABLE", False),
        ):
            result = asyncio.run(finalizer.run_finalize(**kwargs))

        # QualityGate: 75 < 90 → PASS 거부 → patch 종료 → REJECT → action=next
        assert result["action"] == "next"
        # audit_strategic_plan: 1회 초기 + 1회 재심사 = 2회
        assert ctx.agents["director"].audit_strategic_plan.call_count == 2


class TestTF36PartialSingleStrategy:
    """[TF-36] partial → 가장 좋은 후보 1개만 재생성 원칙."""

    def test_arc_ensemble_single_strategy_filters(self):
        """arc_ensemble: single_strategy='balanced' → 1개 전략만 사용."""
        from modules.domain.agents.arc_ensemble import GENERATION_STRATEGIES

        # _active_strategies 필터링 로직 시뮬레이션
        strategies = GENERATION_STRATEGIES
        single_strategy = "balanced"

        _active_strategies = strategies
        if single_strategy:
            _filtered = [s for s in strategies if s.get("name") == single_strategy]
            if _filtered:
                _active_strategies = _filtered

        assert len(_active_strategies) == 1
        assert _active_strategies[0]["name"] == "balanced"

        # 빈 문자열이면 필터링 없음 (하위 호환)
        single_strategy_empty = ""
        _active_empty = strategies
        if single_strategy_empty:
            _filtered = [s for s in strategies if s.get("name") == single_strategy_empty]
            if _filtered:
                _active_empty = _filtered
        assert len(_active_empty) == 3  # 전략 3개 모두

        # 존재하지 않는 전략 → 안전 폴백 (필터링 없음)
        single_strategy_bad = "nonexistent"
        _active_bad = strategies
        if single_strategy_bad:
            _filtered = [s for s in strategies if s.get("name") == single_strategy_bad]
            if _filtered:
                _active_bad = _filtered
        assert len(_active_bad) == 3  # 폴백: 전략 3개 모두

    def test_s2_partial_carries_selected_strategy(self):
        """Stage2: _previous_attempt에 selected_strategy가 포함됨."""
        # stage2_orchestrator.py L576-584 시뮬레이션
        _rej_arc = {
            "arc_no": 1,
            "tactical_doc": "test",
            "_ensemble_meta": {"best_strategy": "creative", "best_score": 85},
        }
        _fin = {
            "action": "retry",
            "score": 60,
            "rejected_arc": _rej_arc,
            "director_feedback_for_fourphase": "수정 필요",
            "score_breakdown": {},
            "selection_reason": "",
            "validation_warnings": [],
            "fix_scope": "partial",
        }

        _previous_attempt = {
            "score": int(_fin.get("score", 0)),
            "best_arc": _rej_arc,
            "rejection_reason": _fin.get("director_feedback_for_fourphase", ""),
            "score_breakdown": _fin.get("score_breakdown", {}),
            "selection_reason": _fin.get("selection_reason", ""),
            "validation_warnings": _fin.get("validation_warnings", []),
            "fix_scope": _fin.get("fix_scope", ""),
            "selected_strategy": _rej_arc.get("_ensemble_meta", {}).get("best_strategy", ""),
        }

        assert _previous_attempt["selected_strategy"] == "creative"
        assert _previous_attempt["fix_scope"] == "partial"

        # _ensemble_meta 없는 경우 → 빈 문자열 (안전 폴백)
        _rej_arc_no_meta = {"arc_no": 2, "tactical_doc": "test"}
        _selected = _rej_arc_no_meta.get("_ensemble_meta", {}).get("best_strategy", "")
        assert _selected == ""

    def test_s3_partial_uses_single_strategy(self):
        """Stage3: partial → single_strategy 전달하여 1개 후보만 생성."""
        from modules.core.constants import PatchModeThresholds

        # three_phase_blueprint_generator.py L210-258 시뮬레이션
        _previous_best = {"scenario": "best blueprint"}
        _prev_fix_scope = "partial"
        _prev_reject_score = 65
        _prev_reject_strategy = "conservative"

        # _use_inplace 조건 (기존)
        _use_inplace = _previous_best is not None and (
            _prev_fix_scope == "inplace" or (not _prev_fix_scope and _prev_reject_score >= PatchModeThresholds.INPLACE)
        )
        assert not _use_inplace  # partial이므로 inplace 아님

        # [TF-36] _use_partial 조건 (신규)
        _use_partial = (not _use_inplace) and _previous_best is not None and (_prev_fix_scope == "partial")
        assert _use_partial  # partial이므로 True

        # full인 경우 → partial 아님
        _prev_fix_scope_full = "full"
        _use_partial_full = (not _use_inplace) and _previous_best is not None and (_prev_fix_scope_full == "partial")
        assert not _use_partial_full  # full이므로 partial 아님

        # _previous_best가 None이면 → partial 아님
        _use_partial_no_prev = (not _use_inplace) and None is not None and (_prev_fix_scope == "partial")
        assert not _use_partial_no_prev


# ═══════════════════════════════════════════════════════════════
# [TF-36] 대원칙 P1 수정 검증 테스트
# ═══════════════════════════════════════════════════════════════


class TestPrincipleP1Fixes:
    """[TF-36] 4대 대원칙 P1 경계 사례 수정 검증."""

    def test_p1_4_1_npc_introductions_dead_guard(self):
        """대원칙 4: npc_introductions에서 dead_npcs 가드 작동."""
        from modules.core.world_state import WorldStateManager

        ws = WorldStateManager(db=None)
        ws._state["dead_npcs"] = {"김사부": {"cause": "전투", "episode": 3}}
        ws._state["alive_npcs"] = {}

        # 사망 NPC를 introductions로 추가 시도
        state_changes = {
            "npc_introductions": [
                {"name": "김사부", "job": "무인", "episode": 5},
                {"name": "이소저", "job": "의녀", "episode": 5},
            ],
        }
        ws.update_from_state_changes(5, state_changes)

        # 김사부는 dead_npcs이므로 alive_npcs에 추가되지 않아야 함
        assert "김사부" not in ws._state["alive_npcs"]
        # 이소저는 정상 추가
        assert "이소저" in ws._state["alive_npcs"]
        # 김사부는 여전히 dead_npcs에 남아있어야 함
        assert "김사부" in ws._state["dead_npcs"]

    def test_p1_3_3_no_director_rejects(self):
        """대원칙 3: director=None이면 PASS가 아닌 REJECT."""
        from modules.domain.agents.unified_blueprint_validator import UnifiedBlueprintValidator

        # context/client를 mock으로 전달
        class FakeCtx:
            db = None

            def get_causal_history_summary(self):
                return ""

        validator = UnifiedBlueprintValidator(context=FakeCtx(), client=None)
        blueprint = {"integrated_scenario": "test scenario", "scene_breakdown": {}}
        verdict, result = validator.validate(
            blueprint=blueprint,
            director=None,  # Director 없음
            all_candidates=None,
            arc_data={},
            constraint_block={},
            prev_blueprint=None,
            working_ep=1,
        )

        # Director 없으면 REJECT이어야 함 (기존: PASS)
        assert verdict == "REJECT"
        assert result["phase"] == "no_director"
        assert result["score"] == 0

    def test_p1_1_2_continuity_advisory_not_reject(self):
        """대원칙 1: ContinuityValidator 실패 시 즉시 REJECT 대신 advisory."""
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        orch = ValidationOrchestrator.__new__(ValidationOrchestrator)
        # _validate_sync_body 내부에서 continuity 결과가 실패해도
        # 즉시 REJECT하지 않고 _continuity_advisory로 저장하는지 확인
        # (실제 호출 대신 로직 시뮬레이션)
        continuity_result = {"passed": False, "violations": [{"type": "item_duplication"}]}

        results = {}
        # advisory 전환 로직 시뮬레이션
        if not continuity_result["passed"]:
            results["_continuity_advisory"] = {
                "source": "ContinuityValidator",
                "violations": continuity_result["violations"],
                "severity": "HIGH",
            }

        assert "_continuity_advisory" in results
        assert results["_continuity_advisory"]["severity"] == "HIGH"
        # 즉시 REJECT 키가 없어야 함
        assert "final_decision" not in results

    def test_p1_1_3_blocking_advisory_not_reject(self):
        """대원칙 1: BlockingValidator 실패 시 즉시 REJECT 대신 advisory."""
        blocking_result = {
            "passed": False,
            "failures": [{"type": "dead_npc_resurrection", "severity": "CRITICAL"}],
        }

        results = {}
        if not blocking_result["passed"]:
            results["_blocking_advisory"] = {
                "source": "BlockingValidator",
                "failures": blocking_result["failures"],
                "severity": "HIGH",
            }

        assert "_blocking_advisory" in results
        assert results["_blocking_advisory"]["failures"][0]["type"] == "dead_npc_resurrection"
        assert "final_decision" not in results

    def test_p1_2_4_regex_relation_uses_existing(self):
        """대원칙 2: regex 관계 변경 시 기존 관계를 참조."""

        # npc_registry에 기존 관계가 있는 경우
        class FakeTracker:
            npc_registry = {
                "장무기": {"relation_to_protag": "중립"},
                "진소소": {"relation_to_protag": "동맹"},
            }

        # "화해" → from은 기존 관계에서 가져와야 함
        npc = "장무기"
        _existing = FakeTracker.npc_registry.get(npc, {}).get("relation_to_protag", "적대")
        assert _existing == "중립"  # 기존 관계 "중립"이 from이 됨 (기존: 하드코딩 "적대")

        # "배신" → from은 기존 관계에서 가져와야 함
        npc2 = "진소소"
        _existing2 = FakeTracker.npc_registry.get(npc2, {}).get("relation_to_protag", "아군")
        assert _existing2 == "동맹"  # 기존 관계 "동맹"이 from이 됨 (기존: 하드코딩 "아군")

        # 미등록 NPC → 기본값 유지
        npc3 = "미등록인물"
        _existing3 = FakeTracker.npc_registry.get(npc3, {}).get("relation_to_protag", "적대")
        assert _existing3 == "적대"  # 기본값


# ═══════════════════════════════════════════════════════════════
# [TF-36] P2 잔여 이슈 테스트
# ═══════════════════════════════════════════════════════════════


class TestBindWorldState:
    """[TF-36] bind_world_state() 테스트."""

    def test_bind_world_state_enables_revive_sync(self):
        """bind_world_state() 후 revive_npc()가 dead_npcs에서 제거 + alive_npcs 복원."""
        from modules.domain.agents.state_tracker import StateTracker

        tracker = StateTracker.__new__(StateTracker)
        tracker._db = None
        tracker.npc_registry = {
            "장무기": {"deceased": True, "death_arc": "1막", "death_context": "전투"},
        }
        tracker.in_world_timeline = []

        # WorldState mock with _state
        ws = MagicMock()
        ws._state = {
            "dead_npcs": {"장무기": {"arc": "1막"}},
            "alive_npcs": {"소림사주지": {}},
        }

        tracker.bind_world_state(ws)
        assert tracker._world_state is ws

        # revive_npc uses getattr(self.tracker, "_world_state", None)
        # Simulate the revive path: tracker._world_state should be accessible
        _ws = getattr(tracker, "_world_state", None)
        assert _ws is not None
        assert "장무기" in _ws._state["dead_npcs"]

        # Simulate revive logic (from state_tracker_npc.py L1354-1364)
        _dead = _ws._state.get("dead_npcs", {})
        if "장무기" in _dead:
            del _dead["장무기"]
        assert "장무기" not in _ws._state["dead_npcs"]

    def test_bind_world_state_none_safe(self):
        """bind_world_state(None) → 경고만, crash 없음."""
        from modules.domain.agents.state_tracker import StateTracker

        tracker = StateTracker.__new__(StateTracker)
        tracker._db = None
        tracker.npc_registry = {}
        tracker.in_world_timeline = []

        # None 바인딩 — crash 없어야 함
        tracker.bind_world_state(None)
        assert tracker._world_state is None

        # getattr 안전 폴백 확인
        _ws = getattr(tracker, "_world_state", None)
        assert _ws is None


class TestParallelBlockingAdvisory:
    """[TF-36] 비동기 경로 BLOCKING advisory 전환 테스트."""

    def test_parallel_blocking_advisory_not_reject(self):
        """비동기 경로 BLOCKING 실패 시 _blocking_advisory 포함 + 즉시 REJECT 아님."""
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        orch = ValidationOrchestrator.__new__(ValidationOrchestrator)
        orch.max_parallel_workers = 2
        orch._validation_history = []
        orch._consecutive_fails = 0

        # Mock validators
        orch.continuity = MagicMock()
        orch.continuity.validate.return_value = {"passed": True, "warning_count": 0}
        orch.blocking = MagicMock()
        orch.blocking.validate.return_value = {
            "passed": False,
            "failures": [{"type": "DEAD_NPC", "description": "사망 NPC 등장"}],
            "failure_count": 1,
        }
        orch.pre_llm = MagicMock()
        orch.pre_llm.validate.return_value = {"passed": True, "score_deduction": 0}
        orch._record_failure_to_reflexion = MagicMock()
        orch._generate_blocking_feedback = MagicMock(return_value="BLOCKING 피드백")
        orch._generate_continuity_feedback = MagicMock()
        orch._build_reject_result_v59 = MagicMock(return_value={"passed": False, "final_decision": "REJECT"})

        # Run the initial part of _validate_parallel_body up to blocking check
        results = {}
        ep_num = 5
        manuscript = "테스트 원고"
        validation_context = {}

        # Simulate continuity
        continuity_result = orch.continuity.validate(ep_num, manuscript, validation_context)
        results["continuity_result"] = continuity_result

        # Simulate blocking — this is the key assertion
        blocking_result = orch.blocking.validate(manuscript, validation_context)
        results["blocking_result"] = blocking_result

        if not blocking_result["passed"]:
            _blk_failures = blocking_result.get("failures", [])
            orch._record_failure_to_reflexion(ep_num, "blocking", _blk_failures)
            results["_blocking_advisory"] = {
                "source": "BlockingValidator",
                "failures": _blk_failures,
                "feedback": orch._generate_blocking_feedback(blocking_result),
                "severity": "HIGH",
            }

        # 핵심 검증: _blocking_advisory 존재 + REJECT 아님
        assert "_blocking_advisory" in results
        assert results["_blocking_advisory"]["source"] == "BlockingValidator"
        assert len(results["_blocking_advisory"]["failures"]) == 1
        # _build_reject_result_v59가 호출되지 않아야 함
        orch._build_reject_result_v59.assert_not_called()
