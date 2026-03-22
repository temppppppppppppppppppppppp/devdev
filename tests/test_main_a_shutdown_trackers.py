import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a


def _capture_shutdown_logs(monkeypatch):
    calls = []

    def _shutdown_log(_self, message, **context):
        calls.append((message, context))

    monkeypatch.setattr(main_a.SovereignApp, "_shutdown_log", _shutdown_log)
    return calls


def test_persist_shutdown_failure_learner_saves_snapshot_to_db(monkeypatch):
    logs = _capture_shutdown_logs(monkeypatch)
    db_conn = MagicMock()
    db = SimpleNamespace(conn=db_conn)
    stats = {"total_failures": 1}
    record = SimpleNamespace(
        category=SimpleNamespace(value="logic"),
        stage="stage4",
        episode=3,
        arc=1,
        reason="stall",
        details={"cause": "conflict"},
        timestamp="2026-03-22 10:00:00",
    )
    app = SimpleNamespace(
        failure_learner=SimpleNamespace(
            records=[record],
            get_failure_stats=lambda: stats,
        )
    )

    main_a.SovereignApp._persist_shutdown_failure_learner(app, db)

    assert db_conn.execute.call_count == 1
    execute_args = db_conn.execute.call_args.args[1]
    payload = json.loads(execute_args[1])
    assert execute_args[0] == "failure_learner_snapshot"
    assert payload["records"][0]["category"] == "logic"
    assert payload["stats"] == stats
    db_conn.commit.assert_called_once()
    assert logs[-1][1]["meta"] == {"total_failures": 1}


def test_persist_shutdown_character_voice_saves_profiles(monkeypatch):
    logs = _capture_shutdown_logs(monkeypatch)
    db = SimpleNamespace()
    voice = SimpleNamespace(profiles=["a", "b"], save_to_db=MagicMock())
    app = SimpleNamespace(character_voice=voice)

    main_a.SovereignApp._persist_shutdown_character_voice(app, db)

    voice.save_to_db.assert_called_once_with(db)
    assert logs[-1][1]["meta"] == {"profile_count": 2}


def test_persist_shutdown_foreshadow_tracker_saves_stats(monkeypatch):
    logs = _capture_shutdown_logs(monkeypatch)
    db = SimpleNamespace()
    foreshadow = SimpleNamespace(
        save_to_db=MagicMock(),
        get_stats=lambda: {"total": 4, "payoff_rate": 75},
    )
    app = SimpleNamespace(foreshadow_tracker=foreshadow)

    main_a.SovereignApp._persist_shutdown_foreshadow_tracker(app, db)

    foreshadow.save_to_db.assert_called_once_with(db)
    assert logs[-1][1]["meta"] == {"total": 4, "payoff_rate": 75}


def test_persist_shutdown_emotion_tracker_saves_history_when_db_exists(monkeypatch):
    logs = _capture_shutdown_logs(monkeypatch)
    db = SimpleNamespace()
    emotion_tracker = SimpleNamespace(history=[1, 2, 3], save_to_db=MagicMock())
    app = SimpleNamespace(emotion_tracker=emotion_tracker)

    main_a.SovereignApp._persist_shutdown_emotion_tracker(app, db)

    emotion_tracker.save_to_db.assert_called_once_with(db)
    assert logs[-1][1]["meta"] == {"history_count": 3}


def test_persist_shutdown_trackers_delegates_to_family_helpers(monkeypatch):
    monkeypatch.setattr(main_a, "V50_MODULES_AVAILABLE", True)
    calls = []
    db = object()
    app = SimpleNamespace(
        current_project=SimpleNamespace(db=db),
        failure_learner=object(),
        character_voice=object(),
        foreshadow_tracker=object(),
        emotion_tracker=object(),
    )
    app._persist_shutdown_failure_learner = lambda arg: calls.append(("failure", arg))
    app._persist_shutdown_character_voice = lambda arg: calls.append(("voice", arg))
    app._persist_shutdown_foreshadow_tracker = lambda arg: calls.append(("foreshadow", arg))
    app._persist_shutdown_emotion_tracker = lambda arg: calls.append(("emotion", arg))

    main_a.SovereignApp._persist_shutdown_trackers(app)

    assert calls == [
        ("failure", db),
        ("voice", db),
        ("foreshadow", db),
        ("emotion", db),
    ]
