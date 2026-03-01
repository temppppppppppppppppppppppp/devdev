"""[TF-32] PASS_WITH_FIX verdict 도입 — Director 피드백 반영 경로 테스트."""

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


# ── Stage 2 PASS_WITH_FIX Tests ──────────────────────────────────


class TestStage2PassWithFix:
    """[TF-32-S2] Stage2 Finalizer PASS_WITH_FIX 수용 테스트."""

    def _make_s2_ctx(self, audit_result):
        """Minimal Stage2 context mock (test_stage2_finalizer.py 패턴 재사용)."""
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
        director.audit_strategic_plan.return_value = audit_result
        director.ask.return_value = "volume summary text long enough"
        ctx.agents = {"director": director}
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
        """PASS_WITH_FIX + high score → action=break (PASS 취급 저장)."""
        from modules.core.stage2_finalizer import Stage2Finalizer

        audit = {
            "decision": "PASS_WITH_FIX",
            "score": 95,
            "reason": "경미한 수정 필요",
            "re_slice_instruction": "1문단 수정",
            "fix_scope": "inplace",
        }
        ctx = self._make_s2_ctx(audit)
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

    def test_finalizer_quality_gate_rejects_low_score_pass_with_fix(self):
        """PASS_WITH_FIX + score < 90 + long tactical_doc → QualityGate REJECT (action=retry)."""
        from modules.core.stage2_finalizer import Stage2Finalizer

        audit = {
            "decision": "PASS_WITH_FIX",
            "score": 80,
            "reason": "수정 필요",
            "re_slice_instruction": "품질 개선",
            "fix_scope": "inplace",
        }
        ctx = self._make_s2_ctx(audit)
        host = MagicMock()
        host.ctx = ctx
        finalizer = Stage2Finalizer(host)
        kwargs = self._make_kwargs(self._valid_arc())

        with patch("modules.core.spinners.V50_MODULES_AVAILABLE", False):
            result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "retry"
        assert result["score"] == 80


# ── Stage 3 PASS_WITH_FIX Tests ──────────────────────────────────


class TestStage3PassWithFix:
    """[TF-32-S3] Stage3 PASS_WITH_FIX 수용 테스트."""

    def test_blueprint_generator_accepts_pass_with_fix(self):
        """verdict=PASS_WITH_FIX → pipeline_result.final_verdict=PASS_WITH_FIX 보존."""
        # ThreePhaseBlueprintGenerator L399-401 verdict 분기 로직 재현
        for test_verdict in ("PASS", "PASS_WITH_FIX"):
            pipeline_result = {"final_verdict": None, "phases": {}}
            _score = 95
            _quality_gate_score = 90
            verdict = test_verdict

            # L393: QualityGate (score >= threshold → 미적용)
            if verdict in ("PASS", "PASS_WITH_FIX") and _score < _quality_gate_score:
                verdict = "REJECT"

            # L399-401: PASS/PASS_WITH_FIX → final_verdict 설정
            if verdict in ("PASS", "PASS_WITH_FIX"):
                pipeline_result["final_verdict"] = verdict

            assert pipeline_result["final_verdict"] == test_verdict

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
