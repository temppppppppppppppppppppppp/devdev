import inspect
from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a
from modules.core.stage2_contracts import TACTICAL_DOC_DUPLICATE_THRESHOLD
from modules.core.stage4_context import Stage4Context


def test_get_max_episode_from_manuscripts_uses_hybrid_project_head(tmp_path):
    drafts_dir = tmp_path / "drafts"
    drafts_dir.mkdir()

    app = SimpleNamespace(
        current_project=SimpleNamespace(
            paths=SimpleNamespace(drafts=drafts_dir),
            get_latest_episode_number=lambda: 7,
        ),
        ui=SimpleNamespace(log=MagicMock()),
    )

    assert main_a.SovereignApp._get_max_episode_from_manuscripts(app) == 6


def test_stage4_wrapper_builds_context_from_app_and_preserves_session_logger():
    stage4_orch = SimpleNamespace(ctx=None, stage_4_v2_chief_writer=MagicMock(return_value="ok"))
    app = SimpleNamespace(
        _show_resume_status=MagicMock(),
        _stage4_orch=stage4_orch,
        ui=SimpleNamespace(log=MagicMock(), console=SimpleNamespace(clear=MagicMock()), title=MagicMock()),
        current_project=SimpleNamespace(master_bible={"MasterBible": {}}, arcs=[], db=MagicMock()),
        agents={},
        sys=MagicMock(),
        state_tracker=MagicMock(),
        world_state=MagicMock(),
        fact_ledger=MagicMock(),
        memory=MagicMock(),
        context_advisor=MagicMock(),
        character_voice=None,
        perf_timer=MagicMock(),
        foreshadow_tracker=None,
        failure_learner=None,
        diversity_engine=None,
        semantic_plot_guard=None,
        selected_genre={"type": "investment", "name": "투자"},
        quality_dashboard=None,
        pacing_analyzer=None,
        pass_rate_monitor=None,
        emotion_tracker=None,
        pre_director_checklist=None,
        confidence_calibrator=None,
        prompt_weighter=None,
        cross_verifier=None,
        chain_of_verification=None,
        adversarial_self_play=None,
        tree_of_thoughts=None,
        multi_agent_deliberation=None,
        _get_int_input=MagicMock(),
        _build_item_acquisition_timeline=MagicMock(),
        _load_narrative_summaries=MagicMock(),
        _get_protagonist_name=MagicMock(),
        _generate_narrative_summary=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        _safe_commit=MagicMock(),
        _session_logger=MagicMock(),
    )

    result = main_a.SovereignApp._stage_4_v2_chief_writer(app, limit_mode=False, target_ep=4)

    assert result == "ok"
    assert isinstance(stage4_orch.ctx, Stage4Context)
    assert stage4_orch.ctx.session_logger is app._session_logger
    stage4_orch.stage_4_v2_chief_writer.assert_called_once_with(limit_mode=False, target_ep=4)


def test_stage4_wrapper_lazy_inits_live_context_before_delegate(monkeypatch):
    import modules.core.fact_ledger as fact_ledger_module
    import modules.core.world_state as world_state_module
    import modules.domain.agents.state_tracker as state_tracker_module

    tracker = SimpleNamespace(
        bind_db=MagicMock(),
        full_extract_from_arcs=MagicMock(),
        bind_world_state=MagicMock(),
        npc_registry={},
    )
    world_state = SimpleNamespace(last_updated_ep=0)
    fact_ledger = SimpleNamespace(last_updated_ep=0)
    stage4_orch = SimpleNamespace(ctx=None, stage_4_v2_chief_writer=MagicMock(return_value="ok"))

    monkeypatch.setattr(state_tracker_module, "StateTracker", lambda preset_registry, llm_client: tracker)
    monkeypatch.setattr(world_state_module, "WorldStateManager", lambda db: world_state)
    monkeypatch.setattr(fact_ledger_module, "FactLedger", lambda db: fact_ledger)

    db = SimpleNamespace(load_anchor=MagicMock(return_value=[{"arc_no": 1}]))
    app = SimpleNamespace(
        _show_resume_status=MagicMock(),
        _stage4_orch=stage4_orch,
        ui=SimpleNamespace(log=MagicMock(), console=SimpleNamespace(clear=MagicMock()), title=MagicMock()),
        current_project=SimpleNamespace(master_bible={"MasterBible": {}}, arcs=[], db=db),
        agents={},
        sys=SimpleNamespace(api_client=MagicMock()),
        preset_registry=MagicMock(),
        state_tracker=None,
        world_state=None,
        fact_ledger=None,
        memory=MagicMock(),
        context_advisor=MagicMock(),
        character_voice=None,
        perf_timer=MagicMock(),
        foreshadow_tracker=None,
        failure_learner=None,
        diversity_engine=None,
        semantic_plot_guard=None,
        selected_genre={"type": "investment", "name": "investment"},
        quality_dashboard=None,
        pacing_analyzer=None,
        pass_rate_monitor=None,
        emotion_tracker=None,
        pre_director_checklist=None,
        confidence_calibrator=None,
        prompt_weighter=None,
        cross_verifier=None,
        chain_of_verification=None,
        adversarial_self_play=None,
        tree_of_thoughts=None,
        multi_agent_deliberation=None,
        _get_int_input=MagicMock(),
        _build_item_acquisition_timeline=MagicMock(),
        _load_narrative_summaries=MagicMock(),
        _get_protagonist_name=MagicMock(),
        _generate_narrative_summary=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        _safe_commit=MagicMock(),
        _session_logger=MagicMock(),
    )

    result = main_a.SovereignApp._stage_4_v2_chief_writer(app, limit_mode=False, target_ep=4)

    assert result == "ok"
    app._show_resume_status.assert_called_once()
    tracker.bind_db.assert_called_once_with(db)
    tracker.full_extract_from_arcs.assert_called_once()
    tracker.bind_world_state.assert_called_once_with(world_state)
    assert app.state_tracker is tracker
    assert app.world_state is world_state
    assert app.fact_ledger is fact_ledger
    assert isinstance(stage4_orch.ctx, Stage4Context)
    assert stage4_orch.ctx.state_tracker is tracker
    assert stage4_orch.ctx.world_state is world_state
    assert stage4_orch.ctx.fact_ledger is fact_ledger
    assert stage4_orch.ctx.session_logger is app._session_logger
    stage4_orch.stage_4_v2_chief_writer.assert_called_once_with(limit_mode=False, target_ep=4)


def test_stage3_wrapper_calls_resume_status_and_delegates_with_fresh_ctx(monkeypatch):
    from modules.core.stage3_context import Stage3Context

    sentinel_ctx = object()
    monkeypatch.setattr(Stage3Context, "from_app", classmethod(lambda cls, owner: sentinel_ctx))

    stage3_orch = SimpleNamespace(ctx=None, stage_3_batch_blueprinting=MagicMock(return_value={"ok": True}))
    app = SimpleNamespace(
        _show_resume_status=MagicMock(),
        _stage3_orch=stage3_orch,
    )

    result = main_a.SovereignApp._stage_3_batch_blueprinting(app)

    assert result == {"ok": True}
    app._show_resume_status.assert_called_once()
    assert stage3_orch.ctx is sentinel_ctx
    stage3_orch.stage_3_batch_blueprinting.assert_called_once()


def test_stage2_wrapper_calls_resume_status_and_syncs_ctx_state(monkeypatch):
    from modules.core.stage2_context import Stage2Context

    sentinel_tracker = MagicMock()
    sentinel_ctx = SimpleNamespace(state_tracker=sentinel_tracker, state_tracker_loaded_arcs=9)
    monkeypatch.setattr(Stage2Context, "from_app", classmethod(lambda cls, owner: sentinel_ctx))
    monkeypatch.setattr(main_a.asyncio, "get_running_loop", MagicMock(side_effect=RuntimeError))
    run_mock = MagicMock()
    monkeypatch.setattr(main_a.asyncio, "run", run_mock)

    stage2_orch = SimpleNamespace(ctx=None, stage_2_arcs_async_logic=MagicMock(return_value="stage2-coro"))
    app = SimpleNamespace(
        _show_resume_status=MagicMock(),
        _stage2_orch=stage2_orch,
        state_tracker=None,
        _state_tracker_loaded_arcs=0,
    )

    main_a.SovereignApp._stage_2_arcs(app)

    app._show_resume_status.assert_called_once()
    run_mock.assert_called_once_with("stage2-coro")
    assert app.state_tracker is sentinel_tracker
    assert app._state_tracker_loaded_arcs == 9


def test_stage2_duplicate_helper_signature_uses_shared_threshold():
    default = inspect.signature(main_a.SovereignApp._is_tactical_doc_duplicate).parameters["threshold"].default
    assert default == TACTICAL_DOC_DUPLICATE_THRESHOLD
