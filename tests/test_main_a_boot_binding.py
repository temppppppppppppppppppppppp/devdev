import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a
from main_a import SovereignApp
from modules.domain.agents.base_agent import BaseAgent


def _make_minimal_app():
    app = SovereignApp.__new__(SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock(), title=MagicMock())
    return app


def test_select_project_uses_explicit_projects_root(monkeypatch, tmp_path):
    explicit_root = tmp_path / "external-projects"
    (explicit_root / "beta").mkdir(parents=True)
    (explicit_root / "alpha").mkdir(parents=True)
    other_cwd = tmp_path / "other-cwd"
    other_cwd.mkdir()
    monkeypatch.chdir(other_cwd)
    monkeypatch.setenv("GEULDOBI_PROJECTS_ROOT", str(explicit_root))

    app = _make_minimal_app()
    app._get_int_input = MagicMock(return_value=2)

    selected = SovereignApp._select_project(app)

    assert selected == "beta"
    app.ui.log.assert_not_called()


def test_check_vector_db_lock_uses_explicit_projects_root(monkeypatch, tmp_path):
    explicit_root = tmp_path / "external-projects"
    project_dir = explicit_root / "demo"
    project_dir.mkdir(parents=True)
    (project_dir / "project_data.db").write_bytes(b"")

    local_project_dir = tmp_path / "projects" / "demo"
    local_project_dir.mkdir(parents=True)
    (local_project_dir / "project_data.db").write_bytes(b"not-empty")

    monkeypatch.setenv("GEULDOBI_PROJECTS_ROOT", str(explicit_root))

    app = _make_minimal_app()

    assert SovereignApp._check_vector_db_lock(app, "demo") is False
    app.ui.log.assert_any_call("💡 [Fix] Remove the file and rerun from Stage 0.")


def test_reload_project_environment_prefers_bound_project_dir(monkeypatch, tmp_path):
    explicit_root = tmp_path / "external-projects"
    project_dir = explicit_root / "demo"
    project_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("GOOGLE_API_KEY=root-key\n", encoding="utf-8")
    (project_dir / ".env").write_text("GOOGLE_API_KEY=project-key\nGOOGLE_API_KEY_2=project-key-2\n", encoding="utf-8")

    monkeypatch.setenv("GEULDOBI_PROJECTS_ROOT", str(explicit_root))
    monkeypatch.setenv("GOOGLE_API_KEY", "root-key")

    init_api_keys = MagicMock()
    monkeypatch.setattr(BaseAgent, "_init_api_keys", init_api_keys)
    monkeypatch.setattr(BaseAgent, "_context_caches", {"stale": "value"}, raising=False)
    monkeypatch.setattr(BaseAgent, "_keys_initialized", True, raising=False)
    monkeypatch.setattr(BaseAgent, "_current_key_idx", 5, raising=False)

    def fake_client(*, api_key):
        return SimpleNamespace(api_key=api_key)

    class FakeStudioSystem:
        def __init__(self, api_client=None):
            self.api_client = api_client

    monkeypatch.setattr(main_a.genai, "Client", fake_client)
    monkeypatch.setattr(main_a, "StudioSystem", FakeStudioSystem)

    app = _make_minimal_app()
    app.sys = SimpleNamespace(api_client=None)

    loaded_path = SovereignApp._reload_project_environment(app, "demo")

    assert loaded_path == (project_dir / ".env").resolve()
    assert app.sys.api_client.api_key == "project-key"
    assert BaseAgent._current_key_idx == 0
    assert BaseAgent._context_caches == {}
    assert os.environ["GOOGLE_API_KEY"] == "project-key"
    assert os.environ["GOOGLE_API_KEY_2"] == "project-key-2"
    init_api_keys.assert_called_once()


def test_reload_project_environment_without_project_env_keeps_agent_cache_state(monkeypatch, tmp_path):
    explicit_root = tmp_path / "external-projects"
    project_dir = explicit_root / "demo"
    project_dir.mkdir(parents=True)

    monkeypatch.setenv("GEULDOBI_PROJECTS_ROOT", str(explicit_root))
    monkeypatch.setenv("GOOGLE_API_KEY", "root-key")
    monkeypatch.setattr(BaseAgent, "_context_caches", {"stale": "value"}, raising=False)
    monkeypatch.setattr(BaseAgent, "_keys_initialized", True, raising=False)
    monkeypatch.setattr(BaseAgent, "_current_key_idx", 2, raising=False)
    init_api_keys = MagicMock()
    monkeypatch.setattr(BaseAgent, "_init_api_keys", init_api_keys)

    app = _make_minimal_app()
    app.sys = SimpleNamespace(api_client="existing-client")

    loaded_path = SovereignApp._reload_project_environment(app, "demo")

    assert loaded_path is None
    assert app.sys.api_client == "existing-client"
    assert BaseAgent._context_caches == {"stale": "value"}
    assert BaseAgent._current_key_idx == 2
    init_api_keys.assert_not_called()


def test_current_project_log_path_uses_bound_project_root(tmp_path):
    app = _make_minimal_app()
    app.current_project = SimpleNamespace(
        name="demo",
        paths=SimpleNamespace(root=(tmp_path / "external-projects" / "demo").resolve()),
    )

    log_path = SovereignApp._get_current_project_log_path(app, "voice_profiles.json")

    assert log_path == (tmp_path / "external-projects" / "demo" / "logs" / "voice_profiles.json").resolve()


def test_ui_events_buffer_until_project_binding_then_flush():
    app = _make_minimal_app()
    app._pending_ui_events = []
    app._session_logger = SimpleNamespace(log_ui_event=MagicMock())
    app.metrics_session_id = "sess_ui"
    app.current_project = None

    SovereignApp._capture_ui_event(
        app,
        {
            "seq": 1,
            "component": "UI",
            "message": "boot visible",
            "event_kind": "log",
            "render_format": "text",
            "visible": True,
            "meta": {"origin": "boot"},
        },
    )

    assert len(app._pending_ui_events) == 1

    db = SimpleNamespace(save_ui_event=MagicMock())
    app.current_project = SimpleNamespace(db=db, metrics_session_id="sess_ui")

    SovereignApp._flush_pending_ui_events(app)

    app._session_logger.log_ui_event.assert_called_once()
    db.save_ui_event.assert_called_once()
    payload = app._session_logger.log_ui_event.call_args.kwargs
    assert payload["session_id"] == "sess_ui"
    assert payload["message"] == "boot visible"
    assert payload["meta"]["origin"] == "boot"
    assert app._pending_ui_events == []


def test_boot_does_not_touch_legacy_quad_cache_helper(monkeypatch, tmp_path):
    project_root = (tmp_path / "projects" / "demo").resolve()
    (project_root / "logs").mkdir(parents=True)
    (project_root / "config").mkdir(parents=True)
    (project_root / "memory").mkdir(parents=True)

    db = SimpleNamespace(
        load_anchor=MagicMock(return_value={"type": "investment", "name": "투자"}),
        save_anchor=MagicMock(),
        conn=MagicMock(),
        _lock=MagicMock(),
    )
    current_project = SimpleNamespace(
        name="demo",
        db=db,
        paths=SimpleNamespace(root=project_root, config=project_root / "config", memory=project_root / "memory"),
    )

    class FakePromptLoader:
        def invalidate_cache(self):
            return None

    class FakeVecMemory:
        def __init__(self, **_kwargs):
            self.initialization_error = ""

        def is_operational(self):
            return True

    sys_obj = SimpleNamespace(project=None, boot_v20_project=None)

    def _boot_v20_project(project_name, genre="wuxia", projects_root=None):
        assert project_name == "demo"
        assert genre == "investment"
        assert projects_root == (tmp_path / "projects").resolve()
        sys_obj.project = current_project

    sys_obj.boot_v20_project = _boot_v20_project

    app = _make_minimal_app()
    app.sys = sys_obj
    app._session_logger = SimpleNamespace(set_log_dir=MagicMock())
    app._select_genre = MagicMock(return_value={"type": "investment", "name": "투자"})
    app._select_project = MagicMock(return_value="demo")
    app._reload_project_environment = MagicMock()
    app._get_projects_root = MagicMock(return_value=(tmp_path / "projects").resolve())
    app._restore_preset_registry = MagicMock()
    app.preset_registry = None
    app._check_vector_db_lock = MagicMock(return_value=True)
    app._attach_agents = MagicMock(return_value=False)
    app._run_main_process = MagicMock()
    app._ignite_quad_cache_system = MagicMock(side_effect=AssertionError("legacy cache helper must stay dead"))

    monkeypatch.setattr(main_a, "VecMemory", FakeVecMemory)
    monkeypatch.setattr("modules.core.prompt_loader.PromptLoader", FakePromptLoader)
    monkeypatch.setattr("modules.core.genre_hud_manager.create_hud_manager", lambda *_args, **_kwargs: SimpleNamespace())
    monkeypatch.setattr("modules.core.genre_hud_manager.log_hud_compatibility_report", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("modules.core.genre_guards.create_genre_guard", lambda *_args, **_kwargs: SimpleNamespace())

    SovereignApp.boot(app)

    app._ignite_quad_cache_system.assert_not_called()
    app._attach_agents.assert_called_once()
    app._run_main_process.assert_not_called()
