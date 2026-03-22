import json
import sqlite3

import pytest

from modules.core.db_manager import DBManager, DBTransactionError


@pytest.fixture
def db(tmp_path):
    manager = DBManager(tmp_path / "commit_episode_factory_lane_g.db")
    try:
        yield manager
    finally:
        manager.close()


def _make_commit_kwargs(**overrides):
    payload = {
        "ep_num": 4,
        "manuscript_data": {"title": "제4화", "content": "본문"},
        "martial_data": None,
        "state_data": {"context_audit": {"summary": "요약"}},
        "causal_links": [],
        "karma_data": [],
        "lore_data": {},
        "recovered_seeds": None,
    }
    payload.update(overrides)
    return payload


def test_normalize_commit_episode_factory_inputs_parses_json_and_fallbacks():
    manuscript_data, state_data = DBManager._normalize_commit_episode_factory_inputs(
        3,
        json.dumps({"title": "제3화", "content": "본문"}, ensure_ascii=False),
        "not-json",
    )

    assert manuscript_data == {"title": "제3화", "content": "본문"}
    assert state_data == {"context_audit": {"summary": "데이터 파싱 오류"}}

    fallback_manuscript, passthrough_state = DBManager._normalize_commit_episode_factory_inputs(
        7,
        "raw manuscript",
        {"context_audit": {"summary": "existing"}},
    )

    assert fallback_manuscript == {"title": "제 7 화", "content": "raw manuscript"}
    assert passthrough_state == {"context_audit": {"summary": "existing"}}


def test_normalize_commit_episode_factory_causal_links_accepts_strings_and_dicts():
    normalized = DBManager._normalize_commit_episode_factory_causal_links(
        [{"cause": "A", "effect": "B"}, "A -> B", 7, None, ""]
    )

    assert normalized == [
        {"cause": "A", "effect": "B"},
        {"cause": "서사 진행", "effect": "A -> B"},
        {"cause": "서사 진행", "effect": ""},
    ]


def test_commit_episode_factory_persists_normalized_flow(db):
    db.cursor.execute(
        "INSERT INTO seeds (seed_id, category, content, status, planted_ep) VALUES (?, ?, ?, ?, ?)",
        ("seed-1", "hook", "복선", "active", 1),
    )
    db.conn.commit()

    committed = db.commit_episode_factory(
        **_make_commit_kwargs(
            manuscript_data=json.dumps({"title": "제4화", "content": "본문"}, ensure_ascii=False),
            state_data=json.dumps({"context_audit": {"summary": "요약"}, "flags": ["ok"]}, ensure_ascii=False),
            causal_links=[{"cause": "A", "effect": "B", "ep": 4}, "C -> D"],
            karma_data=[{"target": "연아", "misunderstanding": 2, "obsession": 5}],
            lore_data={"ITEM": [{"name": "검", "description": "설명"}]},
            recovered_seeds=[{"seed_id": "seed-1"}],
        )
    )

    assert committed is True
    assert db.get_manuscript(4)["content"] == "본문"
    assert db.load_state_log(4)["summary"] == "요약"
    recent_links = db.get_recent_causal_links(current_ep=5, lookback=5)
    assert {"cause": "A", "effect": "B", "ep": 4} in recent_links
    assert any(link["cause"] == "서사 진행" and link["effect"] == "C -> D" and link["ep"] == 4 for link in recent_links)
    assert db.get_all_karma()["연아"]["misunderstanding"] == 2
    lore_rows = db.get_lore_list_by_category("ITEM")
    assert any(row["item"] == "검" and row["description"] == "설명" for row in lore_rows)
    seed_row = db.cursor.execute(
        "SELECT status, recovered_ep FROM seeds WHERE seed_id = ?",
        ("seed-1",),
    ).fetchone()
    assert seed_row["status"] == "archived"
    assert seed_row["recovered_ep"] == 4


def test_commit_episode_factory_rolls_back_outer_operational_error(db, monkeypatch):
    def _raise_locked(*_args, **_kwargs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(db, "save_state_log_with_summary", _raise_locked)

    committed = db.commit_episode_factory(**_make_commit_kwargs(ep_num=5))

    assert committed is False
    assert db.get_manuscript(5) is None
    assert db.conn.in_transaction is False


def test_commit_episode_factory_nested_operational_error_raises_transaction_error(db, monkeypatch):
    def _raise_locked(*_args, **_kwargs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(db, "save_state_log_with_summary", _raise_locked)

    db.begin()
    try:
        with pytest.raises(DBTransactionError):
            db.commit_episode_factory(**_make_commit_kwargs(ep_num=6))
        assert db.conn.in_transaction is True
    finally:
        if db.conn is not None and db.conn.in_transaction:
            db.rollback()

    assert db.get_manuscript(6) is None
