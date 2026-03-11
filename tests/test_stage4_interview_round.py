"""[B-1-3] Stage4InterviewRound unit tests."""

import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

from modules.core.context_advisor import RetrievalPlan, RetrievalSlot, RetrievalSources
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
        preflight_advisory="",
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


class TestInterviewRoundHelpers:
    def test_inherit_attempt_history_appends_previous_attempt(self):
        ir = Stage4InterviewRound(_make_ctx())

        history = ir._inherit_attempt_history(
            {
                "strategy": "A",
                "score": 61,
                "rejection_reason": "연속성 실패",
                "reject_bucket": "constraint_violation",
                "prior_attempts": [{"strategy": "B", "score": 48, "rejection_reason": "분량 부족"}],
            }
        )

        assert len(history) == 2
        assert history[-1]["strategy"] == "A"
        assert history[-1]["reject_bucket"] == "constraint_violation"

    def test_suppress_conflicting_advisories_prefers_higher_tier(self):
        ir = Stage4InterviewRound(_make_ctx())
        parts = [
            "[NumericDriftAdvisor]\n- [MAJOR] '자본금': 누적 표류 의심",
            "[TruthGate Advisory — CRITICAL 경고 시 반드시 REJECT]\n- [CRITICAL] 자본금 10억이 갑자기 100억으로 변함",
        ]

        filtered = ir._suppress_conflicting_advisories(parts)

        assert len(filtered) == 1
        assert "TruthGate" in filtered[0]

    def test_build_candidate_diversity_advisory_warns_for_similar_candidates(self):
        ir = Stage4InterviewRound(_make_ctx())
        candidates = [
            {"manuscript": "같은 내용이 길게 이어진다. 같은 내용이 길게 이어진다."},
            {"manuscript": "같은 내용이 길게 이어진다! 같은 내용이 길게 이어진다."},
            {"manuscript": "같은 내용이 길게 이어진다? 같은 내용이 길게 이어진다."},
        ]

        advisory = ir._build_candidate_diversity_advisory(candidates)

        assert "후보 다양성 경고" in advisory
        assert "가장 다른 접근" in advisory

    def test_summarize_candidate_diversity_reports_pairwise_similarity(self):
        ir = Stage4InterviewRound(_make_ctx())
        candidates = [
            {"manuscript": "같은 내용이 길게 이어진다. 같은 내용이 길게 이어진다."},
            {"manuscript": "같은 내용이 길게 이어진다! 같은 내용이 길게 이어진다."},
            {"manuscript": "전혀 다른 접근으로 새로운 장면이 열린다."},
        ]

        summary = ir._summarize_candidate_diversity(candidates, threshold=0.6)

        assert summary["max_similarity"] >= 0.6
        assert any(pair["pair"] == "A-B" for pair in summary["pairwise"])
        assert any(pair["similarity"] < 0.5 for pair in summary["pairwise"])

    def test_detect_shared_failure_warnings_when_all_candidates_share_signature(self):
        ir = Stage4InterviewRound(_make_ctx())
        validation_results = [
            {"warnings": ["[Python검증-HIGH] NPC 텔레포트"], "structured_violations": []},
            {"warnings": ["[Python검증-HIGH] NPC 텔레포트"], "structured_violations": []},
            {"warnings": ["[Python검증-HIGH] NPC 텔레포트"], "structured_violations": []},
        ]

        warnings = ir._detect_shared_failure_warnings(validation_results)

        assert warnings == ["[⚠️ 전원 동일 위반: NPC 텔레포트]"]

    def test_merge_retry_advisory_feedback_appends_digest_once(self):
        ir = Stage4InterviewRound(_make_ctx())
        ir._last_advisory_details = [
            "[CRITICAL · TruthGate] 마지막 장면의 수치 모순",
            "[MAJOR · NpcDrift] 주연 NPC 말투 이탈",
        ]

        merged = ir._merge_retry_advisory_feedback("기본 피드백")

        assert "[Advisory 핵심 요약 - 재시도 시 반영]" in merged
        assert "TruthGate" in merged
        assert "NpcDrift" in merged
        assert ir._merge_retry_advisory_feedback(merged) == merged


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
        ir._run_advisory_chain = MagicMock(return_value=["[TruthGate Advisory] 마지막 장면 모순"])
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
        assert "[Advisory 핵심 요약 - 재시도 시 반영]" in result.previous_attempt["rejection_reason"]

    def test_patch_and_fallback_use_ctx_state_tracker(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.inplace_patch.return_value = []  # [TF-23] InPlace 실패 유도
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
        round_ctx.chief_writer.inplace_patch.return_value = []  # [TF-23] InPlace 안 타도록 방어
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

    def test_cv_context_includes_blueprint_payload(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 2
        round_ctx.blueprint = {"integrated_scenario": "테스트 플롯", "characters": [{"name": "청운"}]}
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
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
        assert used_context["blueprint"] == round_ctx.blueprint
        assert "integrated_scenario" in used_context["blueprint_text"]

    def test_director_mandatory_context_includes_pov_block(self):
        ctx = _make_ctx()
        ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {"pov": "혼합"}}}
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
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

        director_kwargs = ctx.agents["director"].select_and_judge_ensemble.call_args.kwargs
        assert "[작품 시점]" in director_kwargs["mandatory_context"]
        assert "기본 POV: 혼합" in director_kwargs["mandatory_context"]

    def test_build_history_parser_accepts_inline_header_without_newline(self):
        ctx = _make_ctx()
        ctx.current_project.db.get_manuscript.return_value = None
        ir = Stage4InterviewRound(ctx)
        prev_manuscripts_text = "[제2화] " + ("history " * 30)

        history = ir._build_manuscript_history_for_check(prev_manuscripts_text, next_ep=3)

        assert len(history) == 1
        assert history[0]["ep_num"] == 2
        assert "history" in history[0]["text"]

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

    def test_director_sc5_injects_work_focus_and_relation_slice(self):
        ctx = _make_ctx()
        ctx.context_advisor = MagicMock()
        ctx.quality_dashboard = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = "vec memory block"
        ctx.memory.retrieve_npc_context.return_value = "npc memory block"
        ctx.current_project.db.get_relationship_history.return_value = [
            {"change_ep": 7, "old_relation": "소꿉친구", "new_relation": "멀어진 동료"}
        ]
        ctx.sys = MagicMock()
        ctx.sys.guard = MagicMock()
        ctx.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["소꿉친구 관계선"],
            "mandatory_scene_engines": ["관계 반전"],
            "registry_profiles": [{"name": "relationship_registry", "purpose": "주인공의 오래된 인연 추적"}],
        }
        ctx.context_advisor.plan_director_retrieval.return_value = RetrievalPlan(
            stage="director",
            episode_num=3,
            slots=[
                RetrievalSlot(
                    category="relationship_consistency",
                    query="한태하 연홍 관계선",
                    source=RetrievalSources.DB_NPC_RELATIONSHIP,
                    priority=1,
                ),
            ],
            total_budget_chars=20000,
        )

        ir = Stage4InterviewRound(ctx)
        ir._resolve_director_protagonist_name = MagicMock(return_value="한태하")
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "history-present"
        round_ctx.prev_ending = "연홍과의 관계가 흔들린 채 끝난다."
        round_ctx.blueprint = {
            "characters": [{"name": "한태하"}, {"name": "연홍"}],
            "core_event": "오래된 인연이 시험받는다",
            "story_goal": "연홍의 진심을 확인한다",
            "integrated_scenario": "x",
        }
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

        call_kwargs = ctx.context_advisor.plan_director_retrieval.call_args.kwargs
        assert call_kwargs["work_focus"]["tracking_slots"] == ["소꿉친구 관계선"]
        continuity_ctx = ctx.agents["director"].check_manuscript_continuity_with_cache.call_args.kwargs[
            "memory_context"
        ]
        ctx.quality_dashboard.record_retrieval_observation.assert_called_once()
        kwargs = ctx.quality_dashboard.record_retrieval_observation.call_args.kwargs
        assert kwargs["stage"] == "director"
        assert kwargs["observation"]["relation_slice_included"] is True
        assert "[작품 추적 슬롯 요약]" in continuity_ctx
        assert "[관계 의미 질의]" in continuity_ctx
        assert "[SC:relationship_consistency]" in continuity_ctx
        ctx.current_project.db.get_relationship_history.assert_called()

    def test_post_select_continuity_conflict_downgrades_pass(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "selected manuscript", "title": "selected"},
            "state_updates": {},
            "feedback": {"issues": []},
            "action_items": [],
        }
        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
            "decision": "CONFLICT",
            "summary": "dead npc appears again",
        }
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {
            "decision": "PASS",
            "summary": "",
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        rejection_reason = result.previous_attempt.get("rejection_reason", "") if result.previous_attempt else ""
        assert "[Continuity Conflict]" in rejection_reason
        ctx.agents["director"].check_manuscript_continuity_with_cache.assert_called_once()

    def test_post_select_history_conflict_downgrades_pass(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "[제2화]\n" + ("history " * 60)
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "selected manuscript", "title": "selected"},
            "state_updates": {},
            "feedback": {"issues": []},
            "action_items": [],
        }
        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
            "decision": "PASS",
            "summary": "",
        }
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {
            "decision": "CONFLICT",
            "summary": "location mismatch",
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        rejection_reason = result.previous_attempt.get("rejection_reason", "") if result.previous_attempt else ""
        assert "[V67] History Conflict:" in rejection_reason
        ctx.agents["director"].check_manuscript_history_conflicts.assert_called_once()

    def test_post_select_no_conflict_keeps_pass(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "[제2화]\n" + ("history " * 60)
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "selected manuscript", "title": "selected"},
            "state_updates": {},
        }
        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
            "decision": "PASS",
            "summary": "",
        }
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {
            "decision": "PASS",
            "summary": "",
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "PASS"
        assert result.final_manuscript == "selected manuscript"

    def test_pre_selection_no_llm_continuity_check(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "[제2화]\n" + ("history " * 60)
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate(), _candidate(), _candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [
            _validation_result(),
            _validation_result(),
            _validation_result(),
        ]

        def _select_side_effect(*args, **kwargs):
            assert ctx.agents["director"].check_manuscript_continuity_with_cache.call_count == 0
            assert ctx.agents["director"].check_manuscript_history_conflicts.call_count == 0
            return {
                "selected": "A",
                "verdict": "REJECT",
                "score": 40,
                "selection_reason": "reject",
                "feedback": {"issues": ["issue"]},
                "action_items": ["fix"],
                "selected_candidate": {"manuscript": "candidate manuscript"},
            }

        ctx.agents["director"].select_and_judge_ensemble.side_effect = _select_side_effect

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        assert ctx.agents["director"].check_manuscript_continuity_with_cache.call_count == 0
        assert ctx.agents["director"].check_manuscript_history_conflicts.call_count == 0


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
        round_ctx.chief_writer.inplace_patch.return_value = []  # [TF-23] InPlace 실패 → Patch 폴백
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
        round_ctx.chief_writer.inplace_patch.return_value = []  # [TF-23] InPlace 실패
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


class TestSlotMaxChars:
    """P1-2: 슬롯별 max_chars가 하드코딩 1500 대신 반영되는지 검증."""

    def test_slot_max_chars_respected(self):
        ctx = _make_ctx()
        ctx.context_advisor = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = "A" * 3000
        ctx.context_advisor.plan_director_retrieval.return_value = RetrievalPlan(
            stage="director",
            episode_num=3,
            slots=[
                RetrievalSlot(
                    category="event_claim",
                    query="event query",
                    source=RetrievalSources.VEC_MEMORY,
                    priority=1,
                    max_chars=500,
                ),
            ],
            total_budget_chars=50000,
        )

        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "history-present"
        round_ctx.blueprint = {"characters": [{"name": "alice"}], "integrated_scenario": "x"}
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
                return 50000
            return default

        with patch("modules.validation.threshold_helper._threshold", side_effect=_threshold_side_effect):
            ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        continuity_ctx = ctx.agents["director"].check_manuscript_continuity_with_cache.call_args.kwargs[
            "memory_context"
        ]
        # slot.max_chars=500, so the content within [SC:event_claim] should be <= 500 chars
        sc_block = continuity_ctx.split("[SC:event_claim]\n")[-1] if "[SC:event_claim]" in continuity_ctx else ""
        assert len(sc_block) <= 500
