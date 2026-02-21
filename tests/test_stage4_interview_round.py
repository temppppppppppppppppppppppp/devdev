"""[B-1-3] Stage4InterviewRound unit tests."""

import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

from modules.core.context_advisor import RetrievalPlan, RetrievalSlot
from modules.core.stage4_interview_round import Stage4InterviewRound
from modules.core.stage4_orchestrator import Stage4Orchestrator, _RoundContext


def _make_ctx():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.current_project = MagicMock()
    ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {}}}
    ctx.current_project.db = MagicMock()
    ctx.current_project.db.get_recent_manuscripts.return_value = []
    ctx.current_project.db.get_manuscript.return_value = {"content": "이전 원고"}
    ctx.state_tracker = MagicMock()
    ctx.state_tracker.npc_registry = {}
    ctx.state_tracker.item_state_registry = {}
    ctx.state_tracker.get_npc_change_history.return_value = []
    ctx.state_tracker.check_destroyed_entity_in_manuscript.return_value = []
    ctx.state_tracker.in_world_timeline = []
    ctx.state_tracker.check_time_consistency.return_value = []
    ctx.agents = {"director": MagicMock()}
    ctx.context_advisor = None
    ctx.memory = None
    ctx.get_module = MagicMock(return_value=None)
    return ctx


def _make_round_ctx():
    chief_writer = MagicMock()
    chief_writer.generate_ensemble.return_value = []
    chief_writer.patch_with_feedback.return_value = []
    chief_writer.regenerate_with_feedback.return_value = []

    manuscript_validator = MagicMock()
    manuscript_validator.validate_all_candidates.return_value = []
    consistency_validator = MagicMock()
    consistency_validator.validate.return_value = {"violations": [], "score_penalty": 0}
    blocking_validator = MagicMock()
    blocking_validator.validate.return_value = {"failures": []}
    continuity_validator = MagicMock()
    continuity_validator.validate.return_value = {"violations": [], "warnings": []}
    continuity_validator.check_frustration_streak.return_value = []

    return _RoundContext(
        chief_writer=chief_writer,
        manuscript_validator=manuscript_validator,
        consistency_validator=consistency_validator,
        blocking_validator=blocking_validator,
        continuity_validator=continuity_validator,
        next_ep=1,
        blueprint={"integrated_scenario": "테스트"},
        arc_data={"arc_no": 1},
        arc_pos=1,
        total_ep_in_arc=10,
        arc_tactical="전술",
        prev_text="이전 원고",
        prev_ending="엔딩",
        prev_manuscripts_text="",
        episode_digest="",
        hud_report="HUD",
        current_inventory=[],
        current_martial_arts=[],
        dead_npcs=[],
        item_acquisition_timeline="",
        chain_link_section="",
        world_state_summary="",
        purism_prompt="",
        genre_name="무협",
        npc_equipment_summary="",
        effective_anti_trope="",
        intro_dna="CYNICAL",
        story_context="",
        style_guide="",
        reference_anchor_prompt="",
        mandatory_context="",
        justification_prompt="",
        reflexion_prompt="",
    )


def _candidate():
    return {"manuscript": "테스트 원고 " * 300, "strategy_name": "balanced", "title": "테스트"}


def _validation_result():
    return {"warnings": [], "warning_count": 0, "focus_points": [], "metrics": {"length": 2000}}


class TestInterviewRoundInit:
    def test_init_with_ctx(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        assert ir.ctx is ctx
        assert ir.time_warnings == []

    def test_lazy_init_via_orchestrator(self):
        app = MagicMock()
        ctx = _make_ctx()
        orch = Stage4Orchestrator(app, context=ctx)
        ir = orch.interview_round
        assert isinstance(ir, Stage4InterviewRound)
        assert ir.ctx is ctx

    def test_lazy_init_singleton(self):
        app = MagicMock()
        ctx = _make_ctx()
        orch = Stage4Orchestrator(app, context=ctx)
        assert orch.interview_round is orch.interview_round


class TestInterviewRoundRun:
    def test_empty_candidates_returns_empty(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = []

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "EMPTY"

    def test_pass_returns_pass(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "좋음",
            "selected_candidate": {"manuscript": "통과 원고", "title": "통과"},
            "state_updates": {},
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "PASS"
        assert result.final_manuscript == "통과 원고"

    def test_reject_returns_reject(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "score": 40,
            "selection_reason": "부족",
            "feedback": {"issues": ["문제"]},
            "action_items": ["수정1"],
            "selected_candidate": {"manuscript": "거절 원고"},
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        assert result.final_manuscript is None

    def test_patch_and_fallback_use_ctx_state_tracker(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.patch_with_feedback.return_value = []  # 폴백 유도
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 80,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=1,
            stage4_spinner=MagicMock(),
            director_feedback="피드백",
            previous_attempt={"score": 70, "best_manuscript": "원고"},
            round_ctx=round_ctx,
        )

        assert round_ctx.chief_writer.patch_with_feedback.call_args.kwargs["state_tracker"] is ctx.state_tracker
        assert round_ctx.chief_writer.regenerate_with_feedback.call_args.kwargs["state_tracker"] is ctx.state_tracker

    def test_general_regenerate_uses_ctx_state_tracker(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 80,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=2,
            stage4_spinner=MagicMock(),
            director_feedback="피드백",
            previous_attempt={"score": 20, "best_manuscript": ""},
            round_ctx=round_ctx,
        )

        assert round_ctx.chief_writer.regenerate_with_feedback.call_args.kwargs["state_tracker"] is ctx.state_tracker

    def test_time_warnings_stored_and_used_in_context(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir.time_warnings = ["기존 경고"]
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.state_tracker.check_time_consistency.return_value = ["신규 경고"]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 90,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        used_context = round_ctx.consistency_validator.validate.call_args.args[1]
        assert "기존 경고" in used_context["time_warnings"]
        assert "신규 경고" in ir.time_warnings

    def test_director_sc5_legacy_fallback_without_advisor(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "history-present"
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "pass manuscript", "title": "pass"},
            "state_updates": {},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        continuity_call = ctx.agents["director"].check_manuscript_continuity_with_cache.call_args.kwargs
        history_call = ctx.agents["director"].check_manuscript_history_conflicts.call_args.kwargs
        assert continuity_call["memory_context"] == ""
        assert history_call["memory_context"] == ""

    def test_director_sc5_advisor_dispatches_memory_context(self):
        ctx = _make_ctx()
        ctx.context_advisor = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = "vec memory block"
        ctx.memory.retrieve_npc_context.return_value = "npc memory block"
        ctx.context_advisor.plan_director_retrieval.return_value = RetrievalPlan(
            stage="director",
            episode_num=3,
            slots=[
                RetrievalSlot(category="event_claim", query="event query", source="vec_memory", priority=1),
                RetrievalSlot(category="npc_consistency", query="alice bob", source="db_npc_history", priority=1),
            ],
            total_budget_chars=20000,
        )

        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "history-present"
        round_ctx.blueprint = {"characters": [{"name": "alice"}, {"name": "bob"}], "integrated_scenario": "x"}
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "pass manuscript", "title": "pass"},
            "state_updates": {},
        }

        def _threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.director_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            if key == "smart_retrieval.director_total_budget":
                return 20000
            return default

        with patch("modules.validation.threshold_helper._threshold", side_effect=_threshold_side_effect):
            ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        ctx.context_advisor.plan_director_retrieval.assert_called_once()
        ctx.memory.retrieve_multi_query_context.assert_called()
        ctx.memory.retrieve_npc_context.assert_called()

        continuity_ctx = ctx.agents["director"].check_manuscript_continuity_with_cache.call_args.kwargs[
            "memory_context"
        ]
        history_ctx = ctx.agents["director"].check_manuscript_history_conflicts.call_args.kwargs["memory_context"]
        assert continuity_ctx
        assert history_ctx
        assert continuity_ctx == history_ctx
        assert "[SC:" in continuity_ctx


class TestRecordS4Attempt:
    """Stage 4 PassRateMonitor 기록 테스트."""

    def test_pass_records_success(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "좋음",
            "selected_candidate": {"manuscript": "통과 원고", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        ctx.pass_rate_monitor.record_attempt.assert_called_once()
        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["stage"] == 4
        assert kw["success"] is True
        assert kw["generation_method"] == "ensemble"
        assert kw["is_patch"] is False
        assert kw["arc"] == 1

    def test_reject_records_failure(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "score": 40,
            "selection_reason": "부족",
            "feedback": {"issues": ["문제"]},
            "action_items": ["수정1"],
            "selected_candidate": {"manuscript": "거절 원고"},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        ctx.pass_rate_monitor.record_attempt.assert_called_once()
        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["success"] is False
        assert "score=40" in kw["reject_reason"]
        assert kw["arc"] == 1

    def test_patch_records_method_patch(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.patch_with_feedback.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 80,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=1,
            stage4_spinner=MagicMock(),
            director_feedback="피드백",
            previous_attempt={"score": 70, "best_manuscript": "원고"},
            round_ctx=round_ctx,
        )

        ctx.pass_rate_monitor.record_attempt.assert_called_once()
        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["is_patch"] is True
        assert kw["generation_method"] == "patch"
        assert kw["prev_score"] == 70
        assert kw["arc"] == 1

    def test_patch_fallback_records_method_ensemble(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.patch_with_feedback.return_value = []
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 82,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=1,
            stage4_spinner=MagicMock(),
            director_feedback="피드백",
            previous_attempt={"score": 70, "best_manuscript": "원고"},
            round_ctx=round_ctx,
        )

        ctx.pass_rate_monitor.record_attempt.assert_called_once()
        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["is_patch"] is True
        assert kw["patch_fallback"] is True
        assert kw["generation_method"] == "ensemble"
        round_ctx.chief_writer.regenerate_with_feedback.assert_called_once()

    def test_empty_candidates_records_failure(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = []

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        ctx.pass_rate_monitor.record_attempt.assert_called_once()
        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["success"] is False
        assert kw["reject_reason"] == "score=0"
        assert kw["arc"] == 1

    def test_no_monitor_does_not_crash(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = None
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = []

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "EMPTY"

    def test_monitor_exception_is_non_blocking(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ctx.pass_rate_monitor.record_attempt.side_effect = RuntimeError("boom")
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = []

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "EMPTY"


class TestModuleStructure:
    def test_import(self):
        assert Stage4InterviewRound is not None

    def test_orchestrator_has_interview_round_property(self):
        assert hasattr(Stage4Orchestrator, "interview_round")

    def test_orchestrator_no_legacy_interview_method(self):
        assert not hasattr(Stage4Orchestrator, "_run_interview_round")

    def test_no_self_app_in_interview_round(self):
        source = inspect.getsource(Stage4InterviewRound)
        assert "self.app" not in source

    def test_main_a_stage4_context_includes_pass_rate_monitor(self):
        source = Path("main_a.py").read_text(encoding="utf-8")
        assert 'pass_rate_monitor=getattr(self, "pass_rate_monitor", None),' in source
