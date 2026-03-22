import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import main_a
from modules.core.sovereign_bootstrap_runtime import SovereignBootstrapRuntime


def test_load_bootstrap_components_syncs_spinner_flags(monkeypatch):
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)

    agent_bundle = {"writer": object()}
    v50_bundle = {"ContextAdvisor": object()}

    monkeypatch.setattr(main_a, "_lazy_load_agents", lambda: agent_bundle)
    monkeypatch.setattr(main_a, "_lazy_load_v50_modules", lambda: v50_bundle)
    monkeypatch.setattr(main_a, "_lazy_load_stage0", lambda: (None, None))
    monkeypatch.setattr(main_a, "V50_MODULES_AVAILABLE", True)
    monkeypatch.setattr(main_a, "STAGE0_AVAILABLE", False)
    monkeypatch.setattr(main_a._spinners_mod, "V50_MODULES_AVAILABLE", False, raising=False)
    monkeypatch.setattr(main_a._spinners_mod, "STAGE0_AVAILABLE", True, raising=False)

    agents, v50 = main_a.SovereignApp._load_bootstrap_components(app)

    assert agents is agent_bundle
    assert v50 is v50_bundle
    assert main_a._spinners_mod.V50_MODULES_AVAILABLE is True
    assert main_a._spinners_mod.STAGE0_AVAILABLE is False


def test_apply_genre_bindings_sets_genre_and_guard():
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())
    app.selected_genre = {"type": "investment"}
    base_guard = object()
    director = MagicMock()
    writer = MagicMock()
    app.sys = SimpleNamespace(guard=base_guard)
    app.current_project = SimpleNamespace(load_v20_anchor=MagicMock(return_value=None))
    app.agents = {"director": director, "writer": writer}

    main_a.SovereignApp._apply_genre_bindings(app)

    director.set_genre.assert_called_once_with("investment")
    director.set_guard.assert_called_once_with(base_guard)
    writer.set_genre.assert_called_once_with("investment")
    writer.set_guard.assert_called_once_with(base_guard)


def test_apply_validation_settings_enables_v0128(tmp_path):
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())
    app.agents = {"director": MagicMock()}
    app.current_project = SimpleNamespace(paths=SimpleNamespace(config=tmp_path))

    settings_path = tmp_path / "settings.json"
    settings_path.write_text('{"validation": {"use_v0128": true}}', encoding="utf-8")

    settings = main_a.SovereignApp._load_validation_settings(app)
    main_a.SovereignApp._apply_validation_settings(app, settings)

    app.agents["director"].set_v0128_enabled.assert_called_once_with(True)


def test_bootstrap_continuity_inspector_loads_trackers_from_db():
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())
    continuity_inspector = MagicMock()
    continuity_inspector.v49_7_enabled = True
    continuity_inspector.load_trackers_from_db.return_value = {
        "foreshadowings": 2,
        "relationships": 1,
        "power_entries": 3,
    }
    app.agents = {"continuity_inspector": continuity_inspector}
    app.current_project = SimpleNamespace(db=SimpleNamespace(load_anchor=MagicMock(return_value=[{"arc": 1}])))

    main_a.SovereignApp._bootstrap_continuity_inspector(app)

    app.current_project.db.load_anchor.assert_called_once_with("arcs")
    continuity_inspector.load_trackers_from_db.assert_called_once_with([{"arc": 1}])


def test_validate_initialized_agents_returns_partial_failure_status():
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())
    app.agents = {"director": SimpleNamespace()}
    app._bootstrap_status = main_a.BootstrapStatus()

    status = main_a.SovereignApp._validate_initialized_agents(app)

    assert status == app._bootstrap_status
    assert status.core_ok is False
    assert status.partial_failures == ["agent_missing_ask:director"]


def test_finalize_bootstrap_status_marks_partial_failures():
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())
    app._bootstrap_status = main_a.BootstrapStatus()

    status = main_a.SovereignApp._finalize_bootstrap_status(app, ["v50_init_failed:RuntimeError:boom"])

    assert status == app._bootstrap_status
    assert status.core_ok is True
    assert status.v50_ok is False
    assert status.partial_failures == ["v50_init_failed:RuntimeError:boom"]


def test_attach_agents_reports_partial_v50_failure_status(monkeypatch, tmp_path):
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())
    app.selected_genre = None
    app.sys = SimpleNamespace(guard=None)
    app.current_project = SimpleNamespace(paths=SimpleNamespace(config=tmp_path), db=MagicMock())
    writer = MagicMock()
    writer.ask = MagicMock()
    director = MagicMock()
    director.ask = MagicMock()
    continuity_inspector = MagicMock()
    continuity_inspector.ask = MagicMock()
    continuity_inspector.v49_7_enabled = False
    app.agents = {
        "writer": writer,
        "director": director,
        "continuity_inspector": continuity_inspector,
    }
    app.bootstrap_runtime = MagicMock()
    app._get_agent_model_map = MagicMock(return_value={"writer": "writer-model"})
    app._init_v50_modules = MagicMock(return_value=["v50_init_failed:RuntimeError:context advisor boom"])
    app._bootstrap_status = main_a.BootstrapStatus()

    monkeypatch.setattr(main_a, "_lazy_load_agents", lambda: {})
    monkeypatch.setattr(main_a, "_lazy_load_v50_modules", lambda: {"ContextAdvisor": object()})
    monkeypatch.setattr(main_a, "_lazy_load_stage0", lambda: (None, None))
    monkeypatch.setattr(main_a, "V50_MODULES_AVAILABLE", True)
    monkeypatch.setattr(main_a, "STAGE0_AVAILABLE", False)

    status = main_a.SovereignApp._attach_agents(app)

    assert bool(status) is True
    assert status.core_ok is True
    assert status.v50_ok is False
    assert status.partial_failures == ["v50_init_failed:RuntimeError:context advisor boom"]
    assert app._bootstrap_status == status
    app.bootstrap_runtime.init_core_agents.assert_called_once()
    app.ui.log.assert_any_call("   ⚠️ [Bootstrap] optional module partial failure 1건")


def test_init_v50_modules_delegates_bootstrap_runtime_family(monkeypatch):
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())
    app.selected_genre = {"type": "investment"}
    app.bootstrap_runtime = MagicMock()
    app._load_v50_history = MagicMock()
    v50_bundle = {"ContextAdvisor": object()}

    monkeypatch.setattr(main_a, "V50_MODULES_AVAILABLE", True)

    result = main_a.SovereignApp._init_v50_modules(app, v50_bundle)

    assert result == []
    app.bootstrap_runtime.init_v51_tracking_modules.assert_called_once_with(
        _v50=v50_bundle,
        genre_type="investment",
    )
    app.bootstrap_runtime.init_v6026_reasoning_modules.assert_called_once_with(
        _v50=v50_bundle,
        genre_type="investment",
    )
    app._load_v50_history.assert_called_once_with()


def test_init_v51_tracking_modules_loads_failure_snapshot_from_db(monkeypatch, tmp_path):
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())

    failure_row = (
        '{"records":[{"category":"unknown","stage":4,"episode":3,"arc":1,"reason":"boom","details":{},"timestamp":"2026-03-22"}]}',
    )
    conn = SimpleNamespace(
        execute=MagicMock(return_value=SimpleNamespace(fetchone=MagicMock(return_value=failure_row))),
        commit=MagicMock(),
    )
    app.current_project = SimpleNamespace(db=SimpleNamespace(conn=conn))
    app._get_current_project_log_path = MagicMock(return_value=tmp_path / "missing.json")

    fake_semantic_plot_guard = ModuleType("fake_semantic_plot_guard")

    class _Guard:
        def __init__(self, api_key=""):
            self.api_key = api_key
            self._client = None

    fake_semantic_plot_guard.SemanticPlotGuard = _Guard
    monkeypatch.setitem(sys.modules, "modules.core.semantic_plot_guard", fake_semantic_plot_guard)
    monkeypatch.setattr(main_a.os, "getenv", lambda *_args, **_kwargs: "")

    character_voice = SimpleNamespace(
        load_from_db=MagicMock(return_value=1),
        profiles={"윤호": {}},
    )
    foreshadow_tracker = SimpleNamespace(
        load_from_db=MagicMock(return_value=1),
        get_stats=MagicMock(return_value={"total": 2, "active": 1, "payoff_rate": 50}),
    )
    v50_bundle = {
        "PacingAnalyzer": lambda: "pacing",
        "QualityAmplifier": lambda: "amplifier",
        "AgentIntelligence": lambda genre: f"ai:{genre}",
        "FailureLearner": lambda: SimpleNamespace(records=[]),
        "CharacterVoiceTracker": lambda: character_voice,
        "ForeshadowTracker": lambda: foreshadow_tracker,
    }

    runtime = SovereignBootstrapRuntime(app)
    runtime.init_v51_tracking_modules(_v50=v50_bundle, genre_type="investment")

    assert app.pacing_analyzer == "pacing"
    assert app.quality_amplifier == "amplifier"
    assert app.agent_intelligence == "ai:investment"
    assert len(app.failure_learner.records) == 1
    assert app.failure_learner.records[0].reason == "boom"
    assert app.character_voice is character_voice
    assert app.foreshadow_tracker is foreshadow_tracker
    assert app.semantic_plot_guard is not None


def test_init_v6026_reasoning_modules_connects_failure_learner_and_context_advisor(tmp_path):
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())
    app.sys = SimpleNamespace(api_client=object())
    app.failure_learner = object()
    app.current_project = SimpleNamespace(
        db=MagicMock(),
        paths=SimpleNamespace(root=tmp_path),
    )
    app._get_current_project_log_path = MagicMock(return_value=tmp_path / "missing.json")

    adaptive_manager = MagicMock()
    emotion_tracker = SimpleNamespace(history=[], load_from_db=MagicMock())
    voice_profiler = SimpleNamespace(profiles={}, add_profile=MagicMock())
    pass_rate_monitor = MagicMock()
    quality_dashboard = MagicMock()
    context_advisor = MagicMock()
    v50_bundle = {
        "EmotionArcTracker": lambda _project: emotion_tracker,
        "PowerScalingTracker": lambda: "power",
        "StateDeltaTracker": lambda: "delta",
        "SemanticItemRegistry": lambda: "registry",
        "CharacterVoiceProfiler": lambda: voice_profiler,
        "SelfReflector": lambda **kwargs: ("self_reflector", kwargs),
        "ExpertMixture": lambda genre: ("expert", genre),
        "CrossAgentVerifier": lambda **kwargs: ("cross", kwargs),
        "DynamicPromptWeighter": lambda **kwargs: ("weighter", kwargs),
        "ChainOfVerification": lambda **kwargs: ("cov", kwargs),
        "ConfidenceCalibrator": lambda **kwargs: ("calibrator", kwargs),
        "PreDirectorChecklist": lambda: "checklist",
        "TreeOfThoughts": lambda **kwargs: ("tot", kwargs),
        "AdversarialSelfPlay": lambda **kwargs: ("asp", kwargs),
        "MultiAgentDeliberation": lambda **kwargs: ("mad", kwargs),
        "get_adaptive_manager": lambda: adaptive_manager,
        "ConstitutionalChecker": lambda genre: ("constitution", genre),
        "WriterTemplate": lambda genre: ("template", genre),
        "PassRateMonitor": lambda project_path: pass_rate_monitor if project_path == str(tmp_path) else None,
        "QualityDashboard": lambda path: quality_dashboard if str(path) == str(tmp_path) else None,
        "ContextAdvisor": lambda: context_advisor,
    }

    runtime = SovereignBootstrapRuntime(app)
    runtime.init_v6026_reasoning_modules(_v50=v50_bundle, genre_type="wuxia")

    adaptive_manager.connect_failure_learner.assert_called_once_with(app.failure_learner)
    assert app.emotion_tracker is emotion_tracker
    assert app.voice_profiler is voice_profiler
    assert app.pass_rate_monitor is pass_rate_monitor
    assert app.quality_dashboard is quality_dashboard
    assert app.context_advisor is context_advisor
