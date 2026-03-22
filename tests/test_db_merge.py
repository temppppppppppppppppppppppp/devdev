"""[DB-MERGE] DB SSOT 통합 테스트."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

import pytest

from modules.core.db_manager import DBManager
from modules.core.vec_memory import VecMemory, _GENAI_AVAILABLE

try:
    import sqlite_vec  # noqa: F401

    _VEC_AVAILABLE = True
except ImportError:
    _VEC_AVAILABLE = False


@pytest.fixture
def tmp_db(tmp_path):
    db = DBManager(tmp_path / "project_data.db")
    try:
        yield db
    finally:
        db.close()


class TestSharedMode:
    def test_shared_mode_creation(self, tmp_db):
        vm = VecMemory(
            api_key="",
            ui_log=MagicMock(),
            conn=tmp_db.conn,
            lock=tmp_db._lock,
        )
        assert vm._shared_mode is True
        assert vm._conn is tmp_db.conn
        assert vm._lock is tmp_db._lock

    @pytest.mark.skipif(not (_VEC_AVAILABLE and _GENAI_AVAILABLE), reason="sqlite-vec or google-genai not installed")
    def test_shared_mode_operational(self, tmp_db):
        vm = VecMemory(
            api_key="test-key",
            ui_log=MagicMock(),
            conn=tmp_db.conn,
            lock=tmp_db._lock,
        )
        assert vm.is_operational() is True

    def test_shared_mode_close_preserves_connection(self, tmp_db):
        vm = VecMemory(
            api_key="",
            ui_log=MagicMock(),
            conn=tmp_db.conn,
            lock=tmp_db._lock,
        )
        vm.close()
        row = tmp_db.conn.execute("SELECT 1").fetchone()
        assert row[0] == 1

    def test_standalone_mode_unchanged(self):
        vm = VecMemory(db_path=":memory:", api_key="", ui_log=MagicMock())
        assert vm._shared_mode is False
        vm.close()


class TestMigration:
    def test_migration_copies_episode_meta(self, tmp_path):
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        old_db = memory_dir / "vec_memory.db"
        conn = sqlite3.connect(old_db)
        conn.execute(
            """
            CREATE TABLE episode_meta (
                ep_num INTEGER PRIMARY KEY, summary TEXT,
                causal_data TEXT, arc_no INTEGER,
                event_types TEXT, entity_names TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE sync_status (
                ep_num INTEGER PRIMARY KEY,
                synced INTEGER DEFAULT 0,
                synced_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE anchors (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute("INSERT INTO episode_meta (ep_num, summary) VALUES (1, 'test summary')")
        conn.execute("INSERT INTO sync_status (ep_num, synced) VALUES (1, 1)")
        conn.execute("INSERT INTO anchors (key, value) VALUES ('test_key', '{}')")
        conn.commit()
        conn.close()

        db = DBManager(tmp_path / "project_data.db")
        try:
            row = db.conn.execute("SELECT summary FROM episode_meta WHERE ep_num = 1").fetchone()
            assert row is not None
            assert row[0] == "test summary"

            row = db.conn.execute("SELECT vector_synced FROM sync_status WHERE ep_num = 1").fetchone()
            assert row is not None
            assert row[0] == 1

            row = db.conn.execute("SELECT data FROM anchors WHERE key = 'test_key'").fetchone()
            assert row is not None
            assert row[0] == "{}"
        finally:
            db.close()

        assert not old_db.exists()
        if _VEC_AVAILABLE:
            assert (memory_dir / "vec_memory.db.migrated").exists()
        else:
            assert (memory_dir / "vec_memory.db.partial_migrated").exists()

    def test_no_migration_when_no_old_db(self, tmp_path):
        db = DBManager(tmp_path / "project_data.db")
        try:
            assert db.conn is not None
        finally:
            db.close()
