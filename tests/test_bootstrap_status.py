from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a


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
