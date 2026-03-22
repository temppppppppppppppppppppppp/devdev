import inspect
from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a


def test_init_core_runtime_state_binds_base_runtime(monkeypatch):
    import modules.core.logger as logger_module

    monkeypatch.setattr(logger_module, "init_logger", MagicMock())
    monkeypatch.setattr(main_a, "StudioVisualizer", lambda: SimpleNamespace(log=MagicMock()))
    monkeypatch.setattr(main_a.genai, "Client", lambda api_key=None: SimpleNamespace(api_key=api_key))
    monkeypatch.setattr(main_a, "StudioSystem", lambda api_client=None: SimpleNamespace(api_client=api_client))
    monkeypatch.setattr(main_a, "PromptBuilder", lambda app=None: ("prompt_builder", app))
    monkeypatch.setattr(main_a, "FeedbackSystem", lambda: "feedback_system")
    monkeypatch.setattr(main_a, "Stage01Helpers", lambda app=None: ("stage01", app))
    monkeypatch.setattr(main_a, "Stage2Orchestrator", lambda app=None: ("stage2", app))
    monkeypatch.setattr(main_a, "Stage3Orchestrator", lambda app=None: ("stage3", app))
    monkeypatch.setattr(main_a, "Stage4Orchestrator", lambda app=None: ("stage4", app))
    monkeypatch.setattr(main_a, "BootstrapStatus", lambda: "bootstrap_status")
    monkeypatch.setattr(main_a, "PerfTimer", lambda label: ("perf_timer", label))

    app = SimpleNamespace()

    main_a.SovereignApp._init_core_runtime_state(app)

    assert app.memory is None
    assert app.agents == {}
    assert app.runtime_audit == []
    assert app._prompt_builder == ("prompt_builder", app)
    assert app._feedback_system == "feedback_system"
    assert app._stage2_orch == ("stage2", app)
    assert app._stage3_orch == ("stage3", app)
    assert app._stage4_orch == ("stage4", app)
    assert app._bootstrap_status == "bootstrap_status"
    assert app.perf_timer == ("perf_timer", "Pipeline")
    assert app.world_state is None
    assert app.fact_ledger is None


def test_init_session_and_service_runtime_binds_logger_and_services(monkeypatch):
    from modules.domain.agents.base_agent import BaseAgent

    monkeypatch.setattr(main_a, "SessionLogger", lambda **kwargs: SimpleNamespace(config=kwargs))
    monkeypatch.setattr(main_a, "AuditService", lambda **kwargs: SimpleNamespace(buffer="audit-buffer", kwargs=kwargs))
    monkeypatch.setattr(main_a, "UIService", lambda **kwargs: SimpleNamespace(kwargs=kwargs))
    monkeypatch.setattr(main_a, "StateService", lambda **kwargs: SimpleNamespace(kwargs=kwargs))
    monkeypatch.setattr(main_a, "ProjectService", lambda **kwargs: SimpleNamespace(kwargs=kwargs))
    register_mock = MagicMock()
    monkeypatch.setattr(main_a.atexit, "register", register_mock)
    set_logger_mock = MagicMock()
    monkeypatch.setattr(BaseAgent, "set_session_logger", set_logger_mock)

    app = SimpleNamespace(
        ui=SimpleNamespace(log=MagicMock(), set_operator_event_sink=MagicMock()),
        runtime_audit=[],
        current_project=None,
        selected_genre=None,
        memory=None,
        world_state=None,
        fact_ledger=None,
        emotion_tracker=None,
        state_delta_tracker=None,
        _prompt_builder=object(),
        _feedback_system=object(),
        _capture_ui_event=MagicMock(),
        _save_pass_rate_monitor_for_audit_summary=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        _audit_event=MagicMock(),
        _safe_commit=MagicMock(),
        _restore_preset_registry=MagicMock(),
        _get_int_input=MagicMock(),
        _confirm=MagicMock(),
        _pause=MagicMock(),
    )

    main_a.SovereignApp._init_session_and_service_runtime(app)

    assert app._audit_buffer == "audit-buffer"
    assert app._narrative_summaries_cache is None
    app.ui.set_operator_event_sink.assert_called_once_with(app._capture_ui_event)
    register_mock.assert_called_once_with(app._flush_audit_buffer)
    set_logger_mock.assert_called_once_with(app._session_logger)


def test_init_optional_module_slots_sets_module_placeholders():
    app = SimpleNamespace()

    main_a.SovereignApp._init_optional_module_slots(app)

    assert app._entity_cache_arc_idx == -1
    assert app._cached_entity_registry is None
    assert app.failure_learner is None
    assert app.cross_verifier is None
    assert app.adaptive_manager is None
    assert app.semantic_plot_guard is None
    assert app.preset_registry is None


def test_init_source_delegates_to_bootstrap_helpers():
    source = inspect.getsource(main_a.SovereignApp.__init__)

    assert "self._init_core_runtime_state()" in source
    assert "self._init_session_and_service_runtime()" in source
    assert "self._init_optional_module_slots()" in source
