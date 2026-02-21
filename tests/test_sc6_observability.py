"""SC-6 observability and feature-flag coverage tests."""

from unittest.mock import MagicMock, patch

from modules.core.context_advisor import ContextAdvisor, RetrievalPlan, RetrievalSlot
from modules.core.stage2_preflight import Stage2PreflightAnalysis
from modules.core.stage4_context_builder import Stage4ContextBuilder
from modules.core.stage4_interview_round import Stage4InterviewRound
from tests.test_stage4_context_builder import _make_ctx as _make_stage4_ctx
from tests.test_stage4_interview_round import (
    _candidate,
    _make_round_ctx,
    _validation_result,
)
from tests.test_stage4_interview_round import (
    _make_ctx as _make_interview_ctx,
)


def _threshold_master_off(key, default=None):
    if key == "smart_retrieval.enabled":
        return False
    if key in {
        "smart_retrieval.stage2_enabled",
        "smart_retrieval.stage4_enabled",
        "smart_retrieval.director_enabled",
    }:
        return True
    return default


def _make_stage2_preflight():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.audit_event = MagicMock()
    ctx.current_project = MagicMock()
    ctx.memory = MagicMock()
    ctx.context_advisor = MagicMock()
    ctx.adversarial_self_play = None
    ctx.semantic_plot_guard = None
    ctx.constraint_compiler = None
    ctx.cumulative_state_cache = None
    ctx.cumulative_state_cache_key = 0
    ctx.quality_dashboard = None
    ctx.stage2_optimizer = None
    ctx.quality_amplifier = None
    ctx.agent_intelligence = None
    ctx.failure_learner = None
    ctx.constitutional_checker = None
    ctx.stage_rejection_history = []
    ctx.generate_reverse_feedback_stage3_to_2 = MagicMock(return_value="")
    ctx.build_minimal_arc_context = MagicMock(return_value="")
    ctx.fix_entity_registry_protagonist = MagicMock(side_effect=lambda registry, _name: registry)

    tracker = MagicMock()
    tracker.get_resolved_plots_summary.return_value = ""
    tracker.resolved_plots = []
    ctx.state_tracker = tracker

    weaver = MagicMock()
    weaver.generate_arc_drive.return_value = {"desire_vector": "grow", "status": "ok"}
    preflight_agent = MagicMock()
    preflight_agent.analyze.return_value = {}
    preflight_agent.generate_analyst_injection.return_value = ""
    state_extractor = MagicMock()
    state_extractor.extract_cumulative_state.return_value = {"entity_registry": {}}
    four_phase = MagicMock()
    four_phase.generate.return_value = (None, {"final_verdict": "REJECT", "phases": {"validate": {"issues_count": 1}}})
    ctx.agents = {
        "weaver": weaver,
        "preflight": preflight_agent,
        "state_extractor": state_extractor,
        "four_phase": four_phase,
    }

    host = MagicMock()
    host.ctx = ctx
    return Stage2PreflightAnalysis(host)


def test_context_advisor_default_disabled(monkeypatch):
    seen_keys: list[str] = []

    def fake_threshold(key, default):
        seen_keys.append(key)
        return default

    monkeypatch.setattr("modules.core.context_advisor._threshold", fake_threshold)
    advisor = ContextAdvisor(llm_enricher=None)
    assert advisor.enabled is False
    assert "smart_retrieval.enabled" in seen_keys


def test_build_plan_logs_metrics(monkeypatch, caplog):
    def fake_threshold(key, default):
        if key == "smart_retrieval.enabled":
            return True
        if key == "smart_retrieval.stage4_enabled":
            return True
        if key == "smart_retrieval.stage4_total_budget":
            return 30000
        return default

    monkeypatch.setattr("modules.core.context_advisor._threshold", fake_threshold)
    advisor = ContextAdvisor(llm_enricher=None)

    with caplog.at_level("INFO"):
        plan = advisor.plan_stage4_retrieval(
            arc_data={},
            blueprint={"scene_breakdown": [{"goal": "close the risk gap"}]},
            prev_ending="portfolio left exposed",
            current_ep=3,
            npc_roster=["Han"],
            genre="investment",
        )

    logs = [rec.message for rec in caplog.records if "[SC] stage4 plan:" in rec.message]
    assert logs
    assert f"{len(plan.slots)} slots" in logs[-1]
    assert f"budget={plan.total_budget_chars}" in logs[-1]
    assert f"llm={plan.used_llm}" in logs[-1]


def test_should_use_llm_logs_trigger(caplog):
    advisor = ContextAdvisor()
    with caplog.at_level("DEBUG"):
        assert advisor._should_use_llm("stage4", {"is_arc_boundary": True, "npc_roster": []}) is True
    assert any("[SC] LLM enrichment trigger: arc_boundary (stage4)" in rec.message for rec in caplog.records)


def test_master_switch_gates_all_stages(caplog):
    s4_ctx = _make_stage4_ctx()
    s4_ctx.memory = MagicMock()
    s4_ctx.context_advisor = MagicMock()
    s4_ctx.context_advisor.plan_stage4_retrieval.return_value = RetrievalPlan(
        stage="stage4",
        episode_num=3,
        slots=[RetrievalSlot(category="scene_context", query="scene", source="vec_memory", priority=1)],
        total_budget_chars=1000,
    )
    s4_builder = Stage4ContextBuilder(s4_ctx)
    anchor_sys = MagicMock()
    anchor_sys.get_relevant_anchors.return_value = []
    anchor_sys.get_critical_anchors.return_value = []
    with caplog.at_level("INFO"):
        with (
            patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value=""),
            patch("modules.core.stage4_context_builder._threshold", side_effect=_threshold_master_off),
        ):
            s4_builder.build_mandatory_context(
                next_ep=3,
                arc_data={"arc_no": 1, "ep_start": 1, "ep_count": 5},
                arc_tactical="arc tactical",
                prev_text="x" * 200,
                prev_ending="ending",
                hud_report="HUD",
                writer_agent=MagicMock(),
                anchor_sys=anchor_sys,
                s4_genre_type="wuxia",
                v50_modules_available=False,
            )
        s4_ctx.context_advisor.plan_stage4_retrieval.assert_not_called()

        s2 = _make_stage2_preflight()
        s2.ctx.context_advisor.plan_stage2_retrieval.return_value = RetrievalPlan(
            stage="stage2",
            episode_num=3,
            slots=[RetrievalSlot(category="block_theme", query="theme", source="vec_memory", priority=1)],
            total_budget_chars=1000,
        )
        with patch("modules.core.stage2_preflight._threshold", side_effect=_threshold_master_off):
            s2._preflight_enrichment(
                attempt=0,
                global_arc_no=1,
                current_ep_start=3,
                current_vol_strategy={"strategy_doc": "doc"},
                enriched_block={"block_theme": "theme", "joint_docs": {}, "status_shadow": {}},
                all_refined_arcs=[],
                bible_root={"AssetLibrary": {}},
                protagonist_name="hero",
                director_feedback_for_fourphase="",
                entity_registry_for_director={},
                genre_for_tracker="wuxia",
            )
        s2.ctx.context_advisor.plan_stage2_retrieval.assert_not_called()

        ir_ctx = _make_interview_ctx()
        ir_ctx.context_advisor = MagicMock()
        ir_ctx.memory = MagicMock()
        ir_ctx.context_advisor.plan_director_retrieval.return_value = RetrievalPlan(
            stage="director",
            episode_num=3,
            slots=[RetrievalSlot(category="event_claim", query="event", source="vec_memory", priority=1)],
            total_budget_chars=1000,
        )
        interview = Stage4InterviewRound(ir_ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "history-present"
        round_ctx.blueprint = {"characters": [{"name": "alice"}], "integrated_scenario": "x"}
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ir_ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
            "decision": "PASS",
            "summary": "",
        }
        ir_ctx.agents["director"].check_manuscript_history_conflicts.return_value = {"decision": "PASS", "summary": ""}
        ir_ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "pass manuscript", "title": "pass"},
            "state_updates": {},
        }
        with patch("modules.validation.threshold_helper._threshold", side_effect=_threshold_master_off):
            interview.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )
    ir_ctx.context_advisor.plan_director_retrieval.assert_not_called()
    assert not any("[SC]" in rec.message for rec in caplog.records)


def test_perf_timer_called_for_retrieval():
    ctx = _make_stage4_ctx()
    ctx.perf_timer = MagicMock()
    ctx.memory = MagicMock()
    ctx.memory.retrieve_multi_query_context.return_value = "vec hit"
    ctx.context_advisor = MagicMock()
    ctx.context_advisor.plan_stage4_retrieval.return_value = RetrievalPlan(
        stage="stage4",
        episode_num=4,
        slots=[RetrievalSlot(category="scene_context", query="scene", source="vec_memory", priority=1)],
        total_budget_chars=1200,
    )
    builder = Stage4ContextBuilder(ctx)
    anchor_sys = MagicMock()
    anchor_sys.get_relevant_anchors.return_value = []
    anchor_sys.get_critical_anchors.return_value = []

    def threshold_side_effect(key, default=None):
        if key == "smart_retrieval.enabled":
            return True
        if key == "smart_retrieval.stage4_enabled":
            return True
        if key == "context.vector_max_results_s4":
            return 16
        return default

    with (
        patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value=""),
        patch("modules.core.stage4_context_builder._threshold", side_effect=threshold_side_effect),
    ):
        builder.build_mandatory_context(
            next_ep=4,
            arc_data={"arc_no": 1, "ep_start": 1, "ep_count": 5},
            arc_tactical="arc tactical",
            prev_text="x" * 200,
            prev_ending="ending",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

    start_names = [call.args[0] for call in ctx.perf_timer.start.call_args_list]
    stop_names = [call.args[0] for call in ctx.perf_timer.stop.call_args_list]
    assert any(name.startswith("sc_stage4_ep4_retrieval") for name in start_names)
    assert any(name.startswith("sc_stage4_ep4_retrieval") for name in stop_names)
