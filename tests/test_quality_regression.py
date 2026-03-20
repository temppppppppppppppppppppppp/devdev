"""[Phase 3-QR] Unit tests for quality score regression detection.

Tests detect_score_regression() and get_score_trend_summary() methods
added to QualityDashboard in Phase 3 Step 1.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.quality_dashboard import QualityDashboard

# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════


def _make_dashboard_with_scores(scores, stage=4):
    """점수 리스트로 QualityDashboard 인스턴스 생성 (파일 없음)."""
    db = QualityDashboard(project_path=None)
    for i, score in enumerate(scores, start=1):
        db.record_validation(
            ep_num=i,
            result={"decision": "PASS", "score": score},
            stage=stage,
        )
    return db


# ══════════════════════════════════════════════════════════════
# detect_score_regression
# ══════════════════════════════════════════════════════════════


class TestDetectScoreRegression:
    """detect_score_regression() 단위 테스트."""

    def test_regression_detected(self):
        """직전 대비 20점 이상 하락 → is_regression=True."""
        db = _make_dashboard_with_scores([85, 80, 55])
        result = db.detect_score_regression()
        assert result["is_regression"] is True
        assert result["severity"] == "regression"
        assert result["delta"] == 25  # 80 - 55

    def test_no_regression(self):
        """점수 안정 → is_regression=False, severity=none."""
        db = _make_dashboard_with_scores([80, 78, 82])
        result = db.detect_score_regression()
        assert result["is_regression"] is False
        assert result["severity"] == "none"

    def test_insufficient_data(self):
        """데이터 1건 → insufficient_data."""
        db = _make_dashboard_with_scores([80])
        result = db.detect_score_regression()
        assert result["is_regression"] is False
        assert result["severity"] == "insufficient_data"

    def test_empty_dashboard(self):
        """빈 대시보드 → insufficient_data, 크래시 없음."""
        db = QualityDashboard(project_path=None)
        result = db.detect_score_regression()
        assert result["is_regression"] is False
        assert result["severity"] == "insufficient_data"

    def test_boundary_equal_threshold(self):
        """정확히 threshold(20)만큼 하락 → regression."""
        db = _make_dashboard_with_scores([80, 80, 60])
        result = db.detect_score_regression()
        assert result["is_regression"] is True
        assert result["delta"] == 20

    def test_warning_severity(self):
        """10점 하락(warning_threshold) → severity=warning."""
        db = _make_dashboard_with_scores([80, 80, 70])
        result = db.detect_score_regression()
        assert result["is_regression"] is False
        assert result["severity"] == "warning"
        assert result["delta"] == 10

    def test_return_keys_complete(self):
        """반환 dict에 필수 키 6개 존재."""
        db = _make_dashboard_with_scores([80, 75])
        result = db.detect_score_regression()
        required = {"is_regression", "severity", "delta", "baseline_avg", "recent_avg", "reason"}
        assert required.issubset(result.keys())

    @patch("modules.validation.threshold_helper._threshold")
    def test_default_threshold_on_missing_yaml(self, mock_th):
        """_threshold가 기본값 반환 시에도 정상 동작."""
        mock_th.side_effect = lambda key, default: default
        db = _make_dashboard_with_scores([85, 60])
        result = db.detect_score_regression()
        assert result["is_regression"] is True
        assert result["delta"] == 25


# ══════════════════════════════════════════════════════════════
# get_score_trend_summary
# ══════════════════════════════════════════════════════════════


class TestGetScoreTrendSummary:
    """get_score_trend_summary() 단위 테스트."""

    def test_trend_up(self):
        """점수 상승 추세 → trend=up."""
        db = _make_dashboard_with_scores([60, 65, 70, 75, 80])
        result = db.get_score_trend_summary()
        assert result["trend"] == "up"
        assert result["samples"] == 5

    def test_trend_down(self):
        """점수 하락 추세 → trend=down."""
        db = _make_dashboard_with_scores([80, 75, 70, 65, 60])
        result = db.get_score_trend_summary()
        assert result["trend"] == "down"

    def test_trend_flat(self):
        """점수 안정 → trend=flat."""
        db = _make_dashboard_with_scores([75, 76, 74, 75, 76])
        result = db.get_score_trend_summary()
        assert result["trend"] == "flat"

    def test_insufficient_data(self):
        """데이터 1건 → insufficient_data."""
        db = _make_dashboard_with_scores([80])
        result = db.get_score_trend_summary()
        assert result["trend"] == "insufficient_data"

    def test_summary_string_format(self):
        """summary가 한국어 1줄 문자열."""
        db = _make_dashboard_with_scores([70, 75, 80])
        result = db.get_score_trend_summary()
        assert isinstance(result["summary"], str)
        assert "점" in result["summary"]
        assert "추세" in result["summary"]

    def test_return_keys_complete(self):
        """반환 dict에 필수 키 8개 존재."""
        db = _make_dashboard_with_scores([80, 75, 70])
        result = db.get_score_trend_summary()
        required = {"trend", "window_size", "avg", "min", "max", "delta", "samples", "summary"}
        assert required.issubset(result.keys())

    def test_min_max_correct(self):
        """min/max가 실제 최소/최대."""
        db = _make_dashboard_with_scores([60, 90, 70])
        result = db.get_score_trend_summary()
        assert result["min"] == 60
        assert result["max"] == 90


class TestRetrievalObservationSummary:
    def test_retrieval_summary_aggregates_stage_rows_and_warnings(self):
        db = QualityDashboard(project_path=None)
        db.record_retrieval_observation(
            ep_num=3,
            stage="stage2",
            observation={
                "work_focus_present": True,
                "tracking_slots_count": 2,
                "work_slot_summary_included": True,
                "relation_slice_included": False,
                "source_counts": {"vec_memory": 2, "db_npc_relationship": 1},
                "coverage_warnings": ["missing_relation_slice"],
                "provenance_ledger": {"source_pack": "stage2", "dropped_at": "stage2"},
                "budget_ledger": {"budget_bucket": "smart_retrieval.stage2_total_budget", "configured_cap": 1200},
            },
        )
        db.record_retrieval_observation(
            ep_num=4,
            stage="stage4",
            observation={
                "work_focus_present": True,
                "tracking_slots_count": 1,
                "work_slot_summary_included": True,
                "relation_slice_included": True,
                "source_counts": {"vec_memory": 1},
                "coverage_warnings": [],
            },
        )

        summary = db.get_retrieval_summary(recent_n=5)

        assert summary["available"] is True
        assert summary["total_observations"] == 2
        assert any(row["stage"] == "stage2" for row in summary["stage_rows"])
        assert summary["top_warnings"][0]["warning"] == "missing_relation_slice"
        assert summary["recent"][0]["stage"] == "stage4"
        assert summary["recent"][1]["provenance_ledger"]["source_pack"] == "stage2"
        assert summary["recent"][1]["budget_ledger"]["budget_bucket"] == "smart_retrieval.stage2_total_budget"


class TestPersistenceHealth:
    def test_save_record_failure_surfaces_persistence_health_and_soft_failure_sink(self, tmp_path):
        project_dir = tmp_path / "demo"
        db = QualityDashboard(project_path=project_dir)

        with patch("modules.core.quality_dashboard.open", side_effect=OSError("disk full")):
            db.record_validation(ep_num=1, result={"decision": "PASS", "score": 88}, stage=4)

        summary = db.get_summary()

        assert summary["persistence_health"]["available"] is True
        assert summary["persistence_health"]["recent_count"] == 1
        alert = summary["persistence_health"]["recent"][0]
        assert alert["component"] == "quality_dashboard"
        assert alert["operation"] == "save_record"
        assert alert["exception_type"] == "OSError"

        soft_failures = (project_dir / "logs" / "soft_failures.jsonl").read_text(encoding="utf-8").strip().splitlines()
        assert len(soft_failures) == 1
        payload = json.loads(soft_failures[0])
        assert payload["component"] == "quality_dashboard"
        assert payload["operation"] == "save_record"
