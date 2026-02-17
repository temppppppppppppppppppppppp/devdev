"""[D-4] Director 선택 추적 테스트."""

import pytest

from modules.core.db_manager import DBManager


@pytest.fixture
def db(tmp_path):
    _db = DBManager(tmp_path / "test_selection.db")
    try:
        yield _db
    finally:
        _db.close()


class TestDirectorSelectionsTable:
    def test_save_and_retrieve(self, db):
        db.save_director_selection(
            ep_num=5,
            round_num=0,
            selected_label="B",
            selected_strategy="narrative",
            verdict="PASS",
            score=85,
            selection_reason="서사 밀도 우수",
        )
        rows = db.get_recent_selections(ep_num=10, lookback=5)
        assert len(rows) == 1
        assert rows[0]["selected_strategy"] == "narrative"
        assert rows[0]["verdict"] == "PASS"
        assert rows[0]["score"] == 85

    def test_multiple_rounds_recorded(self, db):
        db.save_director_selection(5, 0, "A", "balanced", "REJECT", 45, "길이 부족")
        db.save_director_selection(5, 1, "C", "tension", "PASS", 78, "재시도 후 합격")
        rows = db.get_recent_selections(ep_num=10, lookback=10)
        assert len(rows) == 2

    def test_reason_truncated(self, db):
        long_reason = "A" * 300
        db.save_director_selection(5, 0, "A", "balanced", "PASS", 80, long_reason)
        rows = db.get_recent_selections(ep_num=10)
        assert len(rows) == 1
        assert len(rows[0]["selection_reason"]) == 200


class TestStrategyWinRates:
    def test_single_strategy_100_percent(self, db):
        for i in range(5):
            db.save_director_selection(i + 1, 0, "A", "balanced", "PASS", 80)
        rates = db.get_strategy_win_rates(lookback=10)
        assert rates["balanced"] == 1.0
        assert rates["total"] == 5

    def test_mixed_strategies(self, db):
        db.save_director_selection(1, 0, "A", "balanced", "PASS", 80)
        db.save_director_selection(2, 0, "B", "narrative", "PASS", 75)
        db.save_director_selection(3, 0, "C", "tension", "PASS", 90)
        db.save_director_selection(4, 0, "A", "balanced", "PASS", 85)
        rates = db.get_strategy_win_rates(lookback=10)
        assert rates["total"] == 4
        assert rates["balanced"] == 0.5

    def test_reject_excluded(self, db):
        db.save_director_selection(1, 0, "A", "balanced", "PASS", 80)
        db.save_director_selection(2, 0, "B", "narrative", "REJECT", 40)
        rates = db.get_strategy_win_rates(lookback=10)
        assert rates["total"] == 1
        assert "narrative" not in rates

    def test_empty_db_returns_zero_total(self, db):
        rates = db.get_strategy_win_rates()
        assert rates["total"] == 0


class TestSelectionAnalysis:
    def test_get_selection_analysis_returns_latest_first(self, db):
        db.save_director_selection(1, 0, "A", "balanced", "PASS", 82, "ok")
        db.save_director_selection(2, 0, "B", "narrative", "REJECT", 35, "low")

        rows = db.get_selection_analysis(lookback=10)

        assert len(rows) == 2
        assert rows[0]["selected_strategy"] == "narrative"
        assert rows[0]["verdict"] == "REJECT"
        assert rows[0]["score"] == 35
        assert rows[1]["selected_strategy"] == "balanced"

    def test_get_selection_analysis_zero_lookback(self, db):
        db.save_director_selection(1, 0, "A", "balanced", "PASS", 80, "ok")

        rows = db.get_selection_analysis(lookback=0)

        assert rows == []


class TestRollbackIncludesSelections:
    def test_reset_after_deletes_selections(self, db):
        db.save_director_selection(3, 0, "A", "balanced", "PASS", 80)
        db.save_director_selection(5, 0, "B", "narrative", "PASS", 75)
        db.reset_after(4)
        rows = db.get_recent_selections(ep_num=10)
        assert len(rows) == 1
        assert rows[0]["ep_num"] == 3

    def test_rollback_impact_includes_selections(self, db):
        db.save_director_selection(5, 0, "A", "balanced", "PASS", 80)
        impact = db.get_rollback_impact(4)
        assert "director_selections" in impact
        assert impact["director_selections"] == 1
