from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a


def test_build_main_process_menu_reflects_stage_status():
    app = SimpleNamespace()
    status = {
        "Stage 0 (Bible)": True,
        "Stage 1 (Volumes)": False,
        "Stage 2 (Arcs)": True,
    }

    menu = main_a.SovereignApp._build_main_process_menu(app, status)

    assert "✅" in menu["0"]
    assert "⏭️ 스킵가능" in menu["1"]
    assert "✅" in menu["2"]


def test_run_stage2_menu_step_stops_when_skip_declined():
    app = SimpleNamespace(
        ui=SimpleNamespace(log=MagicMock()),
        _confirm=MagicMock(return_value=False),
        _stage_2_arcs=MagicMock(),
    )

    main_a.SovereignApp._run_stage2_menu_step(app, {"Stage 1 (Volumes)": False})

    app._confirm.assert_called_once()
    app._stage_2_arcs.assert_not_called()


def test_run_stage2_menu_step_runs_stage2_when_skip_allowed():
    app = SimpleNamespace(
        ui=SimpleNamespace(log=MagicMock()),
        _confirm=MagicMock(return_value=True),
        _stage_2_arcs=MagicMock(),
    )

    main_a.SovereignApp._run_stage2_menu_step(app, {"Stage 1 (Volumes)": False})

    app._stage_2_arcs.assert_called_once_with()


def test_dispatch_main_process_choice_exit_returns_false():
    app = SimpleNamespace(_shutdown_app=MagicMock())

    should_continue = main_a.SovereignApp._dispatch_main_process_choice(app, "5", {})

    assert should_continue is False
    app._shutdown_app.assert_called_once_with()


def test_handle_main_process_error_writes_log_and_shutdown(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir(parents=True)
    app = SimpleNamespace(
        ui=SimpleNamespace(log=MagicMock()),
        current_project=SimpleNamespace(paths=SimpleNamespace(root=project_root)),
        _shutdown_app=MagicMock(),
    )

    try:
        raise RuntimeError("boom")
    except RuntimeError as error:
        main_a.SovereignApp._handle_main_process_error(app, error)

    error_log = project_root / "logs" / "error.log"
    assert error_log.exists()
    contents = error_log.read_text(encoding="utf-8")
    assert "RuntimeError: boom" in contents
    app._shutdown_app.assert_called_once_with()
    app.ui.log.assert_any_call(f"📝 에러 로그 저장: {error_log}")


def test_run_main_process_clears_menu_surface_before_dispatch():
    console = SimpleNamespace(clear=MagicMock())
    clear_helper = MagicMock(side_effect=lambda: main_a.SovereignApp._clear_main_menu_surface_after_choice(app))
    app = SimpleNamespace(
        selected_genre={"name": "투자"},
        ui=SimpleNamespace(menu=MagicMock(return_value="2"), console=console),
        _prepare_main_process_menu=MagicMock(return_value=({"Stage 2 (Arcs)": True}, {"2": "Stage 2"})),
        _dispatch_main_process_choice=MagicMock(return_value=False),
        _clear_main_menu_surface_after_choice=clear_helper,
    )

    main_a.SovereignApp._run_main_process(app)

    app.ui.menu.assert_called_once_with({"2": "Stage 2"})
    clear_helper.assert_called_once_with()
    console.clear.assert_called_once_with()
    app._dispatch_main_process_choice.assert_called_once_with("2", {"Stage 2 (Arcs)": True})
