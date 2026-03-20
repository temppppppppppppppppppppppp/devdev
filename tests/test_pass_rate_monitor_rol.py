from modules.core.pass_rate_monitor import PassRateMonitor, calculate_episode_rol


def test_calculate_episode_rol_uses_cost_time_and_retry_penalty():
    result = calculate_episode_rol(token_cost_usd=1.0, duration_ms=120000, attempts=2, quality_score=88)

    assert result["quality_score"] == 88.0
    assert result["token_cost_usd"] == 1.0
    assert result["duration_ms"] == 120000
    assert result["duration_minutes"] == 2.0
    assert result["attempts"] == 2
    assert result["retry_penalty"] == 1
    assert result["investment_score"] == 4.0
    assert result["rol_score"] == 22.0


def test_get_episode_rol_snapshot_joins_latest_quality_rows(tmp_path):
    monitor = PassRateMonitor(str(tmp_path))
    monitor.record_attempt(stage=4, episode=3, attempt_num=1, success=False, token_cost=0.4, duration_ms=60000)
    monitor.record_attempt(stage=4, episode=3, attempt_num=2, success=True, token_cost=0.6, duration_ms=60000)
    monitor.record_attempt(stage=4, episode=4, attempt_num=1, success=True, token_cost=0.5, duration_ms=30000)

    summary = monitor.get_episode_rol_snapshot(
        [
            {"ep_num": 2, "score": 70, "decision": "REJECT"},
            {"ep_num": 3, "score": 81, "decision": "REJECT"},
            {"ep_num": 3, "score": 88, "decision": "PASS_WITH_FIX"},
            {"ep_num": 4, "score": 90, "decision": "PASS"},
            {"ep_num": 5, "score": 95, "decision": "PASS"},
        ],
        stage=4,
        recent_n=3,
    )

    assert summary["available"] is True
    assert summary["formula_version"] == "v1_quality_over_cost_time_retry"
    assert summary["row_count"] == 2
    assert summary["latest_ep"] == 4
    assert summary["best_ep"] == 4
    assert summary["best_rol"] == 90.0
    assert summary["avg_rol"] == 56.0
    assert summary["rows"][0]["ep_num"] == 3
    assert summary["rows"][0]["decision"] == "PASS_WITH_FIX"
    assert summary["rows"][0]["success"] is True
    assert summary["rows"][0]["rol_score"] == 22.0
    assert summary["rows"][1]["ep_num"] == 4
    assert summary["rows"][1]["decision"] == "PASS"
    assert summary["rows"][1]["success"] is True
    assert summary["rows"][1]["rol_score"] == 90.0
