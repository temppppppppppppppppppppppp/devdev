from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a


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
    app._get_agent_model_map = MagicMock(return_value={"writer": "writer-model"})
    app._init_core_agents = MagicMock()
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
    app.ui.log.assert_any_call("   ⚠️ [Bootstrap] optional module partial failure 1건")
