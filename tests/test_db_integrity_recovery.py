"""DB integrity_check 자동 복구 회귀 테스트."""

from pathlib import Path

from modules.core.db_manager import DBManager


def test_integrity_recovery_quarantines_corrupt_db(tmp_path):
    db_path = tmp_path / "corrupt.db"
    db_path.write_bytes(b"not-a-sqlite-db")

    manager = DBManager(db_path)
    try:
        manager.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='anchors'")
        assert manager.cursor.fetchone() is not None
    finally:
        manager.close()

    quarantined = list(tmp_path.glob("corrupt.db.corrupt_*"))
    assert quarantined
    assert Path(db_path).exists()


def test_corruption_error_classifier():
    assert DBManager._is_db_corruption_error(Exception("database disk image is malformed"))
    assert DBManager._is_db_corruption_error(Exception("file is not a database"))
    assert not DBManager._is_db_corruption_error(Exception("database is locked"))
