"""[Phase 3-QT] Unit tests for windowed quality trend and drift detection."""

from modules.core.quality_dashboard import QualityDashboard


def _record(db: QualityDashboard, ep_num: int, score: int, decision: str = "PASS", stage: int = 4):
    db.record_validation(ep_num=ep_num, result={"decision": decision, "score": score}, stage=stage)


def test_get_windowed_quality_trend_groups_and_aggregates():
    db = QualityDashboard(project_path=None)
    rows = [
        (1, 70, "PASS"),
        (2, 80, "PASS"),
        (3, 90, "REJECT"),
        (4, 60, "PASS"),
        (5, 50, "REJECT"),
        (6, 40, "REJECT"),
        (7, 30, "PASS"),
    ]
    for ep_num, score, decision in rows:
        _record(db, ep_num=ep_num, score=score, decision=decision)

    trend = db.get_windowed_quality_trend(window_size=3, stage=4)

    assert len(trend) == 3
    assert trend[0] == {"window": "ep1-3", "avg_score": 80.0, "pass_rate": 0.67, "count": 3}
    assert trend[1] == {"window": "ep4-6", "avg_score": 50.0, "pass_rate": 0.33, "count": 3}
    assert trend[2] == {"window": "ep7-7", "avg_score": 30.0, "pass_rate": 1.0, "count": 1}


def test_get_windowed_quality_trend_filters_stage_and_nonpositive_score():
    db = QualityDashboard(project_path=None)
    _record(db, ep_num=1, score=80, decision="PASS", stage=4)
    _record(db, ep_num=2, score=0, decision="PASS", stage=4)
    _record(db, ep_num=3, score=90, decision="PASS", stage=3)
    _record(db, ep_num=4, score=70, decision="REJECT", stage=4)

    trend = db.get_windowed_quality_trend(window_size=10, stage=4)

    assert len(trend) == 1
    assert trend[0]["count"] == 2
    assert trend[0]["avg_score"] == 75.0
    assert trend[0]["pass_rate"] == 0.5


def test_detect_quality_drift_declining():
    db = QualityDashboard(project_path=None)

    for ep_num in range(1, 11):
        _record(db, ep_num=ep_num, score=90, decision="PASS")
    for ep_num in range(11, 21):
        _record(db, ep_num=ep_num, score=80, decision="PASS")
    for ep_num in range(21, 31):
        _record(db, ep_num=ep_num, score=70, decision="PASS")

    result = db.detect_quality_drift(stage=4, min_windows=3, window_size=10)

    assert result["drift"] == "declining"
    assert result["windows"] == 3
    assert result["recent_avg"] == 80.0
    assert result["overall_avg"] == 80.0


def test_detect_quality_drift_insufficient_data():
    db = QualityDashboard(project_path=None)

    for ep_num in range(1, 9):
        _record(db, ep_num=ep_num, score=80, decision="PASS")

    result = db.detect_quality_drift(stage=4, min_windows=3, window_size=10)

    assert result["drift"] == "insufficient_data"
    assert result["windows"] == 1
    assert result["recent_avg"] == 0.0
    assert result["overall_avg"] == 0.0
