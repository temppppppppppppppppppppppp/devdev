"""[A-3] fix_scope DB 추적 테스트."""

import pytest

from modules.core.db_manager import DBManager


@pytest.fixture
def db(tmp_path):
    """임시 DB 인스턴스."""
    db_path = tmp_path / "test.db"
    mgr = DBManager(str(db_path))
    yield mgr
    mgr.close()


class TestFixScopeTracking:
    """A-3: fix_scope 컬럼 저장 + 교차집계."""

    def test_save_with_fix_scope(self, db):
        """fix_scope 값이 DB에 저장됨."""
        db.save_director_selection(
            ep_num=1,
            round_num=1,
            selected_label="A",
            selected_strategy="tension_arc",
            verdict="PASS",
            score=85,
            fix_scope="inplace",
        )
        rows = db.get_recent_selections(ep_num=2, lookback=5)
        assert len(rows) == 1
        assert rows[0]["fix_scope"] == "inplace"

    def test_save_without_fix_scope(self, db):
        """fix_scope 미전달 시 빈 문자열 저장."""
        db.save_director_selection(
            ep_num=1,
            round_num=1,
            selected_label="B",
            selected_strategy="growth",
            verdict="REJECT",
            score=50,
        )
        rows = db.get_recent_selections(ep_num=2, lookback=5)
        assert len(rows) == 1
        assert rows[0]["fix_scope"] == ""

    def test_fix_scope_stats_cross_tabulation(self, db):
        """fix_scope × verdict 교차 집계 정확성."""
        # 3 inplace PASS, 1 inplace REJECT, 2 partial PASS
        for _ in range(3):
            db.save_director_selection(
                ep_num=1,
                round_num=1,
                selected_label="A",
                selected_strategy="s1",
                verdict="PASS",
                fix_scope="inplace",
            )
        db.save_director_selection(
            ep_num=2,
            round_num=1,
            selected_label="A",
            selected_strategy="s1",
            verdict="REJECT",
            fix_scope="inplace",
        )
        for _ in range(2):
            db.save_director_selection(
                ep_num=3,
                round_num=1,
                selected_label="B",
                selected_strategy="s2",
                verdict="PASS",
                fix_scope="partial",
            )

        stats = db.get_fix_scope_stats(lookback=100)
        stats_map = {(r["fix_scope"], r["verdict"]): r["cnt"] for r in stats}
        assert stats_map[("inplace", "PASS")] == 3
        assert stats_map[("inplace", "REJECT")] == 1
        assert stats_map[("partial", "PASS")] == 2

    def test_fix_scope_stats_empty_scope_excluded(self, db):
        """fix_scope 빈 문자열은 집계에서 제외."""
        db.save_director_selection(
            ep_num=1,
            round_num=1,
            selected_label="A",
            selected_strategy="s1",
            verdict="PASS",
        )
        stats = db.get_fix_scope_stats()
        assert len(stats) == 0

    def test_migration_idempotent(self, db):
        """ALTER TABLE 마이그레이션 중복 실행 안전."""
        # 이미 init에서 실행됨. 두 번째 init으로 확인
        db2 = DBManager(db.db_path)
        db2.save_director_selection(
            ep_num=1,
            round_num=1,
            selected_label="C",
            selected_strategy="s3",
            verdict="PASS",
            fix_scope="full",
        )
        rows = db2.get_recent_selections(ep_num=2)
        assert rows[0]["fix_scope"] == "full"
        db2.close()
