from types import SimpleNamespace

import pytest

from modules.core.db_manager import DBError, DBManager
from modules.core.reflexion_manager import ReflexionManager


def test_record_failure_respects_outer_transaction_rollback_and_defers_memory_cache(tmp_path):
    db = DBManager(tmp_path / "reflexion.db")
    try:
        manager = ReflexionManager(SimpleNamespace(db=db))

        with pytest.raises(DBError):
            with db.transaction():
                manager.record_failure(3, "consistency", "HUD contradiction detected", solution="recheck HUD state")
                raise RuntimeError("rollback trigger")

        row = db.conn.execute("SELECT COUNT(*) AS cnt FROM reflexion_memory").fetchone()
        assert row["cnt"] == 0
        assert manager.loaded is False
        assert manager.memory == []
    finally:
        db.close()
