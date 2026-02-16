"""
[Phase 4A] DBAdapter 테스트

검증 항목:
1. conn/cursor 직접 접근 차단 (AttributeError)
2. public 메서드 위임 정상 동작
3. close() 전달
4. in_transaction 프로퍼티 동작
5. raw_execute() 화이트리스트 동작
"""

from pathlib import Path
from unittest.mock import MagicMock, PropertyMock

import pytest

from modules.core.db_adapter import DBAdapter

# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────


@pytest.fixture
def mock_db():
    """DBManager mock"""
    db = MagicMock()
    db.db_path = Path("/fake/db.sqlite")
    db.conn = MagicMock()
    db.cursor = MagicMock()
    type(db).in_transaction = PropertyMock(return_value=False)
    return db


@pytest.fixture
def adapter(mock_db):
    return DBAdapter(mock_db)


@pytest.fixture
def real_adapter(tmp_path):
    """실제 SQLite DB로 테스트"""
    from modules.core.db_manager import DBManager

    db_path = tmp_path / "test.db"
    db_mgr = DBManager(db_path)
    return DBAdapter(db_mgr), db_mgr


# ──────────────────────────────────────────────────────────────
# 1. conn/cursor 차단
# ──────────────────────────────────────────────────────────────


class TestBlockedAccess:
    def test_conn_blocked(self, adapter):
        with pytest.raises(AttributeError, match="conn.*차단"):
            _ = adapter.conn

    def test_cursor_blocked(self, adapter):
        with pytest.raises(AttributeError, match="cursor.*차단"):
            _ = adapter.cursor

    def test_db_path_blocked(self, adapter):
        with pytest.raises(AttributeError, match="db_path.*차단"):
            _ = adapter.db_path


# ──────────────────────────────────────────────────────────────
# 2. public 메서드 위임
# ──────────────────────────────────────────────────────────────


class TestDelegation:
    def test_save_anchor(self, adapter, mock_db):
        adapter.save_anchor("key", {"data": 1})
        mock_db.save_anchor.assert_called_once_with("key", {"data": 1})

    def test_load_anchor(self, adapter, mock_db):
        mock_db.load_anchor.return_value = {"test": True}
        result = adapter.load_anchor("key")
        assert result == {"test": True}
        mock_db.load_anchor.assert_called_once_with("key")

    def test_commit(self, adapter, mock_db):
        adapter.commit()
        mock_db.commit.assert_called_once()

    def test_rollback(self, adapter, mock_db):
        adapter.rollback()
        mock_db.rollback.assert_called_once()

    def test_begin(self, adapter, mock_db):
        adapter.begin()
        mock_db.begin.assert_called_once()

    def test_get_manuscript(self, adapter, mock_db):
        mock_db.get_manuscript.return_value = {"ep_num": 1, "content": "test"}
        result = adapter.get_manuscript(1)
        assert result["ep_num"] == 1

    def test_get_latest_episode_number(self, adapter, mock_db):
        mock_db.get_latest_episode_number.return_value = 5
        assert adapter.get_latest_episode_number() == 5

    def test_execute_query(self, adapter, mock_db):
        mock_db.execute_query.return_value = [{"a": 1}]
        result = adapter.execute_query("SELECT 1")
        assert len(result) == 1


# ──────────────────────────────────────────────────────────────
# 3. close() 전달
# ──────────────────────────────────────────────────────────────


class TestClose:
    def test_close_delegates(self, adapter, mock_db):
        adapter.close()
        mock_db.close.assert_called_once()

    def test_close_with_real_db(self, real_adapter):
        adapter, db_mgr = real_adapter
        assert db_mgr.conn is not None
        adapter.close()
        assert db_mgr.conn is None
        assert db_mgr.cursor is None


# ──────────────────────────────────────────────────────────────
# 4. in_transaction 프로퍼티
# ──────────────────────────────────────────────────────────────


class TestInTransaction:
    def test_false_by_default(self, adapter, mock_db):
        type(mock_db).in_transaction = PropertyMock(return_value=False)
        assert adapter.in_transaction is False

    def test_true_when_active(self, adapter, mock_db):
        type(mock_db).in_transaction = PropertyMock(return_value=True)
        assert adapter.in_transaction is True

    def test_real_db_transaction(self, real_adapter):
        adapter, db_mgr = real_adapter
        assert adapter.in_transaction is False
        db_mgr.begin()
        assert adapter.in_transaction is True
        db_mgr.commit()
        assert adapter.in_transaction is False


# ──────────────────────────────────────────────────────────────
# 5. raw_execute()
# ──────────────────────────────────────────────────────────────


class TestRawExecute:
    def test_select_allowed(self, real_adapter):
        adapter, _ = real_adapter
        result = adapter.raw_execute("SELECT 1 AS val")
        assert len(result) == 1

    def test_delete_allowed(self, real_adapter):
        adapter, _ = real_adapter
        # manuscripts 테이블이 이미 존재 (DBManager._boot_db에서 생성)
        adapter.raw_execute("DELETE FROM manuscripts WHERE ep_num = ?", (-1,))
        adapter.raw_commit()

    def test_drop_blocked(self, adapter):
        with pytest.raises(ValueError, match="허용되지 않은 SQL"):
            adapter.raw_execute("DROP TABLE manuscripts")

    def test_create_blocked(self, adapter):
        with pytest.raises(ValueError, match="허용되지 않은 SQL"):
            adapter.raw_execute("CREATE TABLE hack (id INTEGER)")

    def test_alter_blocked(self, adapter):
        with pytest.raises(ValueError, match="허용되지 않은 SQL"):
            adapter.raw_execute("ALTER TABLE manuscripts ADD COLUMN x TEXT")


# ──────────────────────────────────────────────────────────────
# 6. repr
# ──────────────────────────────────────────────────────────────


class TestRepr:
    def test_repr(self, adapter):
        r = repr(adapter)
        assert "DBAdapter" in r
