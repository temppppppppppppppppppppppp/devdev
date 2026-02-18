"""[Phase 4-DB] Director bias detection unit tests."""

from modules.core.quality_dashboard import QualityDashboard


def _mk_records(strategy: str, scores: list[int], verdict: str = "PASS") -> list[dict]:
    return [
        {
            "selected_strategy": strategy,
            "verdict": verdict,
            "score": s,
            "selection_reason": "test",
        }
        for s in scores
    ]


def test_detect_director_bias_high_avg_warns():
    dashboard = QualityDashboard(project_path=None)
    selections = _mk_records("narrative", [85] * 10, verdict="PASS")

    result = dashboard.detect_director_bias(selections)

    assert "narrative" in result["strategy_stats"]
    assert result["strategy_stats"]["narrative"]["avg_score"] == 85.0
    assert result["strategy_stats"]["narrative"]["pass_rate"] == 1.0
    assert any("편향 가능성" in msg for msg in result["bias_warnings"])


def test_detect_director_bias_low_avg_warns():
    dashboard = QualityDashboard(project_path=None)
    selections = _mk_records("tension", [30] * 10, verdict="REJECT")

    result = dashboard.detect_director_bias(selections)

    assert "tension" in result["strategy_stats"]
    assert result["strategy_stats"]["tension"]["avg_score"] == 30.0
    assert result["strategy_stats"]["tension"]["pass_rate"] == 0.0
    assert any("과소평가 가능성" in msg for msg in result["bias_warnings"])


def test_detect_director_bias_insufficient_samples_no_warning():
    dashboard = QualityDashboard(project_path=None)
    selections = _mk_records("balanced", [90, 92, 95], verdict="PASS") + _mk_records(
        "narrative", [45, 47], verdict="REJECT"
    )

    result = dashboard.detect_director_bias(selections)

    assert result["strategy_stats"]["balanced"]["count"] == 3
    assert result["strategy_stats"]["narrative"]["count"] == 2
    assert result["bias_warnings"] == []


def test_detect_director_bias_uses_numeric_score_denominator():
    dashboard = QualityDashboard(project_path=None)
    selections = [
        {"selected_strategy": "balanced", "verdict": "PASS", "score": 80, "selection_reason": "ok"},
        {"selected_strategy": "balanced", "verdict": "PASS", "score": None, "selection_reason": "missing"},
        {"selected_strategy": "balanced", "verdict": "PASS", "selection_reason": "missing"},
        {"selected_strategy": "balanced", "verdict": "REJECT", "score": "N/A", "selection_reason": "invalid"},
    ]

    result = dashboard.detect_director_bias(selections)
    stats = result["strategy_stats"]["balanced"]

    assert stats["count"] == 1
    assert stats["avg_score"] == 80.0
    assert stats["pass_rate"] == 1.0
