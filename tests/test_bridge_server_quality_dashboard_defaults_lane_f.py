from modules.api import bridge_server


def test_quality_dashboard_core_defaults_bind_project_and_authority():
    payload = bridge_server._quality_dashboard_core_defaults("demo", 7)

    assert payload["safe_ops"]["project"] == "demo"
    assert payload["artifact_ladder"]["project"] == "demo"
    assert payload["quality_summary"]["authority_role"] == bridge_server._authority_role_for(
        "/quality/summary"
    )
    assert payload["gate_repair_summary"]["available"] is False


def test_quality_dashboard_trend_and_roi_defaults_apply_floor_values():
    trend_payload = bridge_server._quality_dashboard_trend_defaults(3)
    roi_payload = bridge_server._quality_dashboard_roi_defaults(3)

    assert trend_payload["score_trend"]["summary"] == "데이터 부족 (0화)"
    assert roi_payload["patch_effectiveness"]["lookback"] == 20
    assert roi_payload["episode_rol"]["lookback"] == 8
    assert roi_payload["arc_cost_correlation"]["lookback"] == 8


def test_quality_dashboard_defaults_merges_all_sections():
    payload = bridge_server._quality_dashboard_defaults("demo", 3)

    assert payload["project"] == "demo"
    assert payload["lookback"] == 3
    assert payload["safe_ops"]["project"] == "demo"
    assert payload["cost_summary"]["lookback"] == 3
    assert payload["calibration"]["next_step"].startswith("실제 회차를 보며")
