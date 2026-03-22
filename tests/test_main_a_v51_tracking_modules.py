from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a
from modules.core.sovereign_bootstrap_runtime import SovereignBootstrapRuntime


def test_restore_failure_learner_from_db_snapshot_loads_records():
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.failure_learner = SimpleNamespace(records=[])
    failure_row = (
        '{"records":[{"category":"unknown","stage":4,"episode":3,"arc":1,"reason":"boom","details":{},"timestamp":"2026-03-22"}]}',
    )
    app.current_project = SimpleNamespace(
        db=SimpleNamespace(
            conn=SimpleNamespace(
                execute=MagicMock(return_value=SimpleNamespace(fetchone=MagicMock(return_value=failure_row)))
            )
        )
    )

    result = SovereignBootstrapRuntime(app)._restore_failure_learner_from_db_snapshot()

    assert result is True
    assert len(app.failure_learner.records) == 1
    assert app.failure_learner.records[0].reason == "boom"


def test_migrate_failure_learner_snapshot_from_json_persists_db_snapshot(tmp_path):
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())
    conn = SimpleNamespace(execute=MagicMock(), commit=MagicMock())
    app.current_project = SimpleNamespace(db=SimpleNamespace(conn=conn))
    log_path = tmp_path / "failure_learning.json"
    log_path.write_text("{}", encoding="utf-8")
    app._get_current_project_log_path = MagicMock(return_value=log_path)

    record = SimpleNamespace(
        category=SimpleNamespace(value="unknown"),
        stage=4,
        episode=3,
        arc=1,
        reason="boom",
        details={},
        timestamp="2026-03-22",
    )

    def _load_from_json(_path):
        app.failure_learner.records = [record]

    app.failure_learner = SimpleNamespace(
        records=[],
        load_from_json=_load_from_json,
        get_failure_stats=lambda: {"total_failures": 1},
    )

    SovereignBootstrapRuntime(app)._migrate_failure_learner_snapshot_from_json()

    conn.execute.assert_called_once()
    conn.commit.assert_called_once()
    app.ui.log.assert_any_call("   📚 [DB-Eff] failure_learning JSON→DB 마이그레이션 완료")


def test_restore_character_voice_tracker_migrates_json_when_db_empty(tmp_path):
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())
    app.current_project = SimpleNamespace(db=object())
    log_path = tmp_path / "character_voice.json"
    log_path.write_text("{}", encoding="utf-8")
    app._get_current_project_log_path = MagicMock(return_value=log_path)
    app.character_voice = SimpleNamespace(
        load_from_db=MagicMock(return_value=0),
        load_from_json=MagicMock(),
        save_to_db=MagicMock(),
    )

    SovereignBootstrapRuntime(app)._restore_character_voice_tracker()

    app.character_voice.load_from_json.assert_called_once_with(log_path)
    app.character_voice.save_to_db.assert_called_once_with(app.current_project.db)
    app.ui.log.assert_any_call("   🎭 [DB-Eff] character_voice JSON→DB 마이그레이션 완료")


def test_restore_foreshadow_tracker_logs_loaded_db_stats():
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())
    app.current_project = SimpleNamespace(db=object())
    app.foreshadow_tracker = SimpleNamespace(
        load_from_db=MagicMock(return_value=2),
        get_stats=MagicMock(return_value={"total": 4, "active": 1, "payoff_rate": 50}),
    )

    SovereignBootstrapRuntime(app)._restore_foreshadow_tracker()

    app.foreshadow_tracker.get_stats.assert_called_once()
    app.ui.log.assert_any_call("   🔮 [V51.6] 복선 4개 로드(DB) (활성: 1, 회수율: 50%)")


def test_init_v51_tracking_modules_runtime_bootstraps_tracking_family():
    app = main_a.SovereignApp.__new__(main_a.SovereignApp)
    app.ui = SimpleNamespace(log=MagicMock())
    app._get_current_project_log_path = MagicMock()
    app.current_project = SimpleNamespace(db=MagicMock())
    app.failure_learner = None
    app.character_voice = None
    app.foreshadow_tracker = None
    runtime = SovereignBootstrapRuntime(app)
    runtime._restore_failure_learner_from_db_snapshot = MagicMock(return_value=True)
    runtime._migrate_failure_learner_snapshot_from_json = MagicMock()
    runtime._restore_character_voice_tracker = MagicMock()
    runtime._restore_foreshadow_tracker = MagicMock()
    runtime._init_semantic_plot_guard_module = MagicMock()
    v50_bundle = {
        "PacingAnalyzer": lambda: "pacing",
        "QualityAmplifier": lambda: "quality",
        "AgentIntelligence": lambda genre: f"ai:{genre}",
        "FailureLearner": lambda: SimpleNamespace(records=[1, 2]),
        "CharacterVoiceTracker": lambda: "voice",
        "ForeshadowTracker": lambda: "foreshadow",
    }

    runtime.init_v51_tracking_modules(_v50=v50_bundle, genre_type="investment")

    assert app.pacing_analyzer == "pacing"
    assert app.quality_amplifier == "quality"
    assert app.agent_intelligence == "ai:investment"
    assert app.character_voice == "voice"
    assert app.foreshadow_tracker == "foreshadow"
    runtime._restore_failure_learner_from_db_snapshot.assert_called_once_with()
    runtime._restore_character_voice_tracker.assert_called_once_with()
    runtime._restore_foreshadow_tracker.assert_called_once_with()
    runtime._init_semantic_plot_guard_module.assert_called_once_with()
