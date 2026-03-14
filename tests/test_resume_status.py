from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a


def test_show_resume_status_logs_project_progress():
    db = SimpleNamespace(
        load_anchor=MagicMock(return_value=[{"ep_count": 10}, {"ep_count": 5}]),
        get_latest_blueprint_number=MagicMock(return_value=12),
    )
    project = SimpleNamespace(name="resume_project", db=db, get_latest_episode_number=lambda: 13)
    ui = SimpleNamespace(log=MagicMock())
    app = SimpleNamespace(current_project=project, ui=ui)

    main_a.SovereignApp._show_resume_status(app)

    logs = [c.args[0] for c in ui.log.call_args_list]
    assert any("[Resume] 프로젝트: resume_project" in m for m in logs)
    assert any("Arc 설계: 2개 완료" in m for m in logs)
    assert any("Blueprint: ep 12까지 완료" in m for m in logs)
    assert any("원고: ep 12까지 완료" in m for m in logs)
    assert any("예상 총 에피소드: 15" in m for m in logs)


def test_show_resume_status_logs_warning_on_error(monkeypatch):
    db = SimpleNamespace(
        load_anchor=MagicMock(side_effect=RuntimeError("boom")),
        get_latest_blueprint_number=MagicMock(return_value=0),
    )
    project = SimpleNamespace(name="resume_project", db=db, get_latest_episode_number=lambda: 1)
    ui = SimpleNamespace(log=MagicMock())
    app = SimpleNamespace(current_project=project, ui=ui)

    warning_mock = MagicMock()
    monkeypatch.setattr(main_a.logging, "warning", warning_mock)

    main_a.SovereignApp._show_resume_status(app)

    warning_mock.assert_called_once()
    assert "[Resume] 상태 보고 실패: boom" in warning_mock.call_args.args[0]


def test_shutdown_pass_rate_save_failure_is_non_blocking(monkeypatch):
    monkeypatch.setattr(main_a, "V50_MODULES_AVAILABLE", True)
    monkeypatch.setattr(main_a, "get_metrics_collector", lambda: None)

    pass_rate_monitor = MagicMock()
    pass_rate_monitor.save.side_effect = RuntimeError("save-fail")

    db_conn = MagicMock()
    db = SimpleNamespace(conn=db_conn)
    project = SimpleNamespace(name="resume_project", db=db, save_v20_anchor=MagicMock())

    app = SimpleNamespace(
        _PROJECTS_DIR="projects",
        pass_rate_monitor=pass_rate_monitor,
        failure_learner=None,
        character_voice=None,
        foreshadow_tracker=None,
        current_project=project,
        selected_genre=None,
        ui=SimpleNamespace(log=MagicMock()),
    )

    main_a.SovereignApp._shutdown_app(app)

    pass_rate_monitor.save.assert_called_once()
    db_conn.commit.assert_called_once()
    db_conn.close.assert_called_once()


def test_shutdown_records_session_cost_when_scope_exists(monkeypatch):
    monkeypatch.setattr(main_a, "V50_MODULES_AVAILABLE", True)

    collector = MagicMock()
    collector.session_id = "sess_shutdown"
    collector.get_summary_report.return_value = "summary"
    collector.save_metrics.return_value = "metrics.json"
    collector.snapshot_and_reset_scope.return_value = {
        "total_calls": 2,
        "total_tokens": 900,
        "total_cost_usd": 0.009,
        "model_breakdown": "{}",
    }
    monkeypatch.setattr(main_a, "get_metrics_collector", lambda: collector)

    db_conn = MagicMock()
    db = SimpleNamespace(conn=db_conn, save_cost_record=MagicMock())
    project = SimpleNamespace(name="resume_project", db=db, save_v20_anchor=MagicMock())

    app = SimpleNamespace(
        _PROJECTS_DIR="projects",
        pass_rate_monitor=None,
        failure_learner=None,
        character_voice=None,
        foreshadow_tracker=None,
        current_project=project,
        selected_genre=None,
        ui=SimpleNamespace(log=MagicMock()),
    )

    main_a.SovereignApp._shutdown_app(app)

    db.save_cost_record.assert_called_once()
    kw = db.save_cost_record.call_args.kwargs
    assert kw["session_id"] == "sess_shutdown"
    assert kw["scope_type"] == "session"
    assert kw["total_calls"] == 2


def test_shutdown_metrics_summary_and_saved_path_are_logged_via_ui(monkeypatch):
    monkeypatch.setattr(main_a, "V50_MODULES_AVAILABLE", False)

    collector = MagicMock()
    collector.get_summary_report.return_value = "summary-line"
    collector.save_metrics.return_value = "metrics.json"
    collector.snapshot_and_reset_scope.return_value = {}
    monkeypatch.setattr(main_a, "get_metrics_collector", lambda: collector)

    db_conn = MagicMock()
    db = SimpleNamespace(conn=db_conn)
    ui = SimpleNamespace(log=MagicMock())
    project = SimpleNamespace(name="resume_project", db=db, save_v20_anchor=MagicMock())
    app = SimpleNamespace(
        _PROJECTS_DIR="projects",
        pass_rate_monitor=None,
        failure_learner=None,
        character_voice=None,
        foreshadow_tracker=None,
        current_project=project,
        selected_genre=None,
        ui=ui,
    )

    main_a.SovereignApp._shutdown_app(app)

    logs = [call.args[0] for call in ui.log.call_args_list if call.args]
    assert any("summary-line" in message for message in logs)
    assert any("세션 메트릭 저장: metrics.json" in message for message in logs)


def test_shutdown_bible_anchor_failure_is_non_blocking(monkeypatch):
    monkeypatch.setattr(main_a, "V50_MODULES_AVAILABLE", False)
    monkeypatch.setattr(main_a, "get_metrics_collector", lambda: None)

    db_conn = MagicMock()
    db = SimpleNamespace(conn=db_conn)
    project = SimpleNamespace(
        name="resume_project",
        db=db,
        master_bible={"MasterBible": {}},
        save_v20_anchor=MagicMock(side_effect=RuntimeError("bible-fail")),
    )

    app = SimpleNamespace(
        _PROJECTS_DIR="projects",
        pass_rate_monitor=None,
        failure_learner=None,
        character_voice=None,
        foreshadow_tracker=None,
        current_project=project,
        selected_genre=None,
        ui=SimpleNamespace(log=MagicMock()),
    )

    main_a.SovereignApp._shutdown_app(app)

    project.save_v20_anchor.assert_called_once_with("bible", project.master_bible)
    db_conn.commit.assert_called_once()
    db_conn.close.assert_called_once()


def test_shutdown_genre_anchor_failure_is_non_blocking(monkeypatch):
    monkeypatch.setattr(main_a, "V50_MODULES_AVAILABLE", False)
    monkeypatch.setattr(main_a, "get_metrics_collector", lambda: None)

    db_conn = MagicMock()
    db = SimpleNamespace(conn=db_conn, save_anchor=MagicMock(side_effect=RuntimeError("genre-fail")))
    project = SimpleNamespace(
        name="resume_project",
        db=db,
        master_bible={"MasterBible": {}},
        save_v20_anchor=MagicMock(),
    )

    app = SimpleNamespace(
        _PROJECTS_DIR="projects",
        pass_rate_monitor=None,
        failure_learner=None,
        character_voice=None,
        foreshadow_tracker=None,
        current_project=project,
        selected_genre={"type": "investment", "name": "투자"},
        ui=SimpleNamespace(log=MagicMock()),
    )

    main_a.SovereignApp._shutdown_app(app)

    db.save_anchor.assert_called_once_with("genre_info", app.selected_genre)
    db_conn.commit.assert_called_once()
    db_conn.close.assert_called_once()


def test_shutdown_app_delegates_to_split_helpers(monkeypatch):
    calls: list[str] = []

    def _shutdown_log(_self, message, **_context):
        if "종료 시퀀스" in message:
            calls.append("start")
        elif "종료 완료" in message:
            calls.append("end")

    monkeypatch.setattr(main_a.SovereignApp, "_shutdown_log", _shutdown_log)
    monkeypatch.setattr(main_a.SovereignApp, "_persist_shutdown_metrics", lambda _self: calls.append("metrics"))
    monkeypatch.setattr(main_a.SovereignApp, "_persist_shutdown_cost_scope", lambda _self: calls.append("cost"))
    monkeypatch.setattr(
        main_a.SovereignApp, "_persist_shutdown_advisory_state", lambda _self: calls.append("advisory")
    )
    monkeypatch.setattr(main_a.SovereignApp, "_persist_shutdown_trackers", lambda _self: calls.append("trackers"))
    monkeypatch.setattr(
        main_a.SovereignApp, "_persist_shutdown_project_state", lambda _self: calls.append("project")
    )
    monkeypatch.setattr(main_a.SovereignApp, "_close_shutdown_resources", lambda _self: calls.append("close"))

    main_a.SovereignApp._shutdown_app(SimpleNamespace())

    assert calls == ["start", "metrics", "cost", "advisory", "trackers", "project", "close", "end"]
