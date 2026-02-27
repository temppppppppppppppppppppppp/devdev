"""
[Phase3-Timeline] Timeline DB 영속화 테스트
- DB round-trip
- DB 없을 때 in-memory fallback
- max_chars 준수
- update_from_state_changes → DB sync
"""

import pytest
from pathlib import Path


def _make_db(tmp_path):
    from modules.core.db_manager import DBManager
    return DBManager(tmp_path / "test.db")


# ── 1. DB round-trip ─────────────────────────────────────────────────

def test_upsert_and_get_timeline(tmp_path):
    """upsert_timeline_entry → get_timeline_range round-trip."""
    db = _make_db(tmp_path)
    db.upsert_timeline_entry(5, "봄 초입", 30, "약 1개월 경과")
    db.upsert_timeline_entry(10, "초여름", 60, "약 2개월 경과")
    entries = db.get_timeline_range()
    ep_nos = [e["ep_no"] for e in entries]
    assert 5 in ep_nos
    assert 10 in ep_nos


def test_timeline_entry_upsert_overwrites(tmp_path):
    """같은 ep_no 재삽입 시 덮어쓰기."""
    db = _make_db(tmp_path)
    db.upsert_timeline_entry(1, "겨울", None, "추운 날씨")
    db.upsert_timeline_entry(1, "봄", None, "따뜻한 날씨")
    entries = db.get_timeline_range()
    assert len(entries) == 1
    assert entries[0]["time_note"] == "따뜻한 날씨"


def test_get_timeline_range_limit(tmp_path):
    """limit 파라미터 동작 확인."""
    db = _make_db(tmp_path)
    for i in range(1, 21):
        db.upsert_timeline_entry(i, f"날짜_{i}", None, f"메모_{i}")
    entries = db.get_timeline_range(limit=5)
    assert len(entries) == 5
    assert entries[0]["ep_no"] == 1


# ── 2. in-memory fallback ─────────────────────────────────────────────

def test_get_timeline_summary_fallback_when_no_db(tmp_path):
    """DB 없을 때 in-memory timeline fallback."""
    from modules.core.world_state import WorldStateManager
    db = _make_db(tmp_path)
    ws = WorldStateManager(db)
    # db를 None으로 교체하여 fallback 경로 강제
    ws.db = None
    ws._state["timeline"] = [
        {"ep": 3, "type": "time", "description": "봄 시작"},
        {"ep": 7, "type": "time", "description": "여름 도래"},
    ]
    result = ws.get_timeline_summary()
    assert "[작중 타임라인]" in result
    assert "EP3" in result
    assert "봄 시작" in result


def test_get_timeline_summary_empty_when_no_data(tmp_path):
    """timeline 데이터 없으면 빈 문자열."""
    from modules.core.world_state import WorldStateManager
    db = _make_db(tmp_path)
    ws = WorldStateManager(db)
    result = ws.get_timeline_summary()
    assert result == ""


# ── 3. max_chars 준수 ─────────────────────────────────────────────────

def test_timeline_summary_max_chars(tmp_path):
    """max_chars 준수 확인."""
    db = _make_db(tmp_path)
    for i in range(1, 51):
        db.upsert_timeline_entry(i, f"날짜_{i:02d}", None, f"이것은 긴 메모입니다 에피소드 {i}")
    from modules.core.world_state import WorldStateManager
    ws = WorldStateManager(db)
    result = ws.get_timeline_summary(max_chars=200)
    assert len(result) <= 200


# ── 4. update_from_state_changes → DB sync ───────────────────────────

def test_world_state_syncs_time_markers_to_db(tmp_path):
    """update_from_state_changes의 time_markers가 DB에 sync됨."""
    from modules.core.world_state import WorldStateManager
    db = _make_db(tmp_path)
    ws = WorldStateManager(db)
    state_changes = {
        "time_markers": [
            {"episode": 15, "type": "season", "description": "가을 시작"},
        ]
    }
    ws.update_from_state_changes(15, state_changes)
    entries = db.get_timeline_range()
    ep_nos = [e["ep_no"] for e in entries]
    assert 15 in ep_nos
    entry = next(e for e in entries if e["ep_no"] == 15)
    assert "가을" in (entry.get("time_note") or "")


# ── 5. 마이그레이션 ───────────────────────────────────────────────────

def test_migrate_world_state_timeline(tmp_path):
    """WorldState anchor의 timeline 배열을 DB로 1회 마이그레이션."""
    import json
    from modules.core.db_manager import DBManager

    db_path = tmp_path / "migrate_test.db"
    db = DBManager(db_path)
    # world_state anchor에 timeline 삽입
    ws_data = {
        "version": 1,
        "last_updated_ep": 10,
        "timeline": [
            {"ep": 5, "type": "time", "description": "5화 시점"},
            {"ep": 8, "type": "season", "description": "8화 계절"},
        ],
    }
    db.save_anchor("world_state", ws_data)
    # 새 DB 인스턴스 생성 시 마이그레이션 실행
    db2 = DBManager(db_path)
    entries = db2.get_timeline_range()
    ep_nos = [e["ep_no"] for e in entries]
    assert 5 in ep_nos
    assert 8 in ep_nos
