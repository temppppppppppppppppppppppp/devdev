from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a


def _capture_shutdown_logs(monkeypatch):
    calls = []

    def _shutdown_log(_self, message, **context):
        calls.append((message, context))

    monkeypatch.setattr(main_a.SovereignApp, "_shutdown_log", _shutdown_log)
    return calls


def test_persist_shutdown_pass_rate_state_logs_saved_record_count(monkeypatch):
    monkeypatch.setattr(main_a, "V50_MODULES_AVAILABLE", True)
    logs = _capture_shutdown_logs(monkeypatch)
    pass_rate_monitor = SimpleNamespace(records=[1, 2, 3], save=MagicMock(), reconcile_from_db=MagicMock(return_value=1))
    app = SimpleNamespace(
        pass_rate_monitor=pass_rate_monitor,
        current_project=SimpleNamespace(db=object()),
    )

    main_a.SovereignApp._persist_shutdown_pass_rate_state(app)

    pass_rate_monitor.reconcile_from_db.assert_called_once()
    pass_rate_monitor.save.assert_called_once()
    assert logs[-1][1]["meta"] == {"record_count": 3}
    assert "통과율 기록 저장" in logs[-1][0]


def test_persist_shutdown_director_bias_state_logs_warning_details(monkeypatch):
    monkeypatch.setattr(main_a, "V50_MODULES_AVAILABLE", True)
    logs = _capture_shutdown_logs(monkeypatch)
    quality_dashboard = SimpleNamespace(
        detect_director_bias=MagicMock(return_value={"bias_warnings": ["bias-a", "bias-b"]})
    )
    db = SimpleNamespace(get_selection_analysis=MagicMock(return_value=[{"score": 1}, {"score": 2}]))
    app = SimpleNamespace(quality_dashboard=quality_dashboard)

    main_a.SovereignApp._persist_shutdown_director_bias_state(app, db)

    db.get_selection_analysis.assert_called_once_with(lookback=100)
    quality_dashboard.detect_director_bias.assert_called_once()
    assert logs[0][1]["meta"] == {"warning_count": 2}
    assert logs[1][0] == "   - bias-a"
    assert logs[2][0] == "   - bias-b"


def test_persist_shutdown_quality_drift_state_logs_declining_warning(monkeypatch):
    monkeypatch.setattr(main_a, "V50_MODULES_AVAILABLE", True)
    logs = _capture_shutdown_logs(monkeypatch)
    quality_dashboard = SimpleNamespace(
        detect_quality_drift=MagicMock(
            return_value={"drift": "declining", "recent_avg": 71, "overall_avg": 82}
        )
    )
    app = SimpleNamespace(quality_dashboard=quality_dashboard)

    main_a.SovereignApp._persist_shutdown_quality_drift_state(app)

    quality_dashboard.detect_quality_drift.assert_called_once_with(stage=4, min_windows=3, window_size=10)
    assert logs[-1][1]["meta"] == {"drift_status": "declining"}
    assert "품질 하락 감지" in logs[-1][0]


def test_persist_shutdown_advisory_state_delegates_to_helper_family(monkeypatch):
    db = object()
    calls = []
    app = SimpleNamespace(
        current_project=SimpleNamespace(db=db),
        pass_rate_monitor=None,
        quality_dashboard=None,
    )
    monkeypatch.setattr(
        main_a.SovereignApp,
        "_persist_shutdown_pass_rate_state",
        lambda _self: calls.append(("pass_rate", None)),
    )
    monkeypatch.setattr(
        main_a.SovereignApp,
        "_persist_shutdown_director_bias_state",
        lambda _self, arg: calls.append(("director_bias", arg)),
    )
    monkeypatch.setattr(
        main_a.SovereignApp,
        "_persist_shutdown_quality_drift_state",
        lambda _self: calls.append(("quality_drift", None)),
    )

    main_a.SovereignApp._persist_shutdown_advisory_state(app)

    assert calls == [
        ("pass_rate", None),
        ("director_bias", db),
        ("quality_drift", None),
    ]
