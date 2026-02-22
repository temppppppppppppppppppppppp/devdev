"""DBManager current-API regression tests."""

import pytest

from modules.core.db_manager import DBConnectionError, DBError, DBManager


@pytest.fixture
def db(tmp_path):
    manager = DBManager(tmp_path / "test.db")
    try:
        yield manager
    finally:
        manager.close()


def test_save_and_load_anchor(db):
    payload = {"key1": "value1", "nested": {"a": 1}}
    assert db.save_anchor("sample", payload) is True
    assert db.load_anchor("sample") == payload


def test_load_anchor_missing_default_behavior(db):
    assert db.load_anchor("missing_default") == {}
    assert db.load_anchor("missing_custom", default={"fallback": True}) == {"fallback": True}


def test_save_and_get_blueprint(db):
    blueprint = {"ep_num": 1, "title": "시작", "scenes": [{"scene_no": 1}]}
    db.save_blueprint(1, blueprint)
    loaded = db.get_blueprint(1)
    assert loaded["title"] == "시작"
    assert loaded["scenes"][0]["scene_no"] == 1


def test_save_and_get_manuscript_and_latest_episode_number(db):
    db.save_manuscript(1, "제목1", "내용1")
    db.save_manuscript(5, "제목5", "내용5")
    loaded = db.get_manuscript(5)
    assert loaded["title"] == "제목5"
    assert loaded["content"] == "내용5"
    # get_latest_episode_number는 "다음 회차 번호" 반환
    assert db.get_latest_episode_number() == 6


def test_transaction_rolls_back_on_exception(db):
    with pytest.raises(DBError):
        with db.transaction():
            db.save_anchor("tx_key", {"v": 1})
            raise RuntimeError("rollback trigger")

    assert db.load_anchor("tx_key", default=None) == {}


def test_close_then_query_raises_connection_error(tmp_path):
    manager = DBManager(tmp_path / "closed.db")
    manager.close()
    with pytest.raises(DBConnectionError):
        manager.execute_query("SELECT 1")


def test_get_all_episode_bibles_handles_malformed_json(db):
    db.save_episode_bible(1, {"new_items": ["철검"], "time_passed": "1일"})
    db.cursor.execute(
        "INSERT OR REPLACE INTO episode_bibles (ep_num, new_items, lost_items, new_npcs, npc_deaths, "
        "relationship_changes, state_changes, time_passed, reveals) "
        "VALUES (2, '{broken', '[]', '[]', '[]', '[]', '{}', '', '[]')"
    )
    db.conn.commit()

    rows = db.get_all_episode_bibles()
    assert len(rows) == 2
    assert rows[0]["new_items"] == ["철검"]
    assert rows[1]["new_items"] == []
