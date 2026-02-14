"""[Phase 3-5A-1] NPC append-only 이력 DB + StateTracker 기록 API 단위 테스트

검증 대상:
- DBManager.insert_npc_change / get_npc_history / get_npc_latest_fields
- StateTrackerNPC._record_change (비차단)
- register_npc_death / register_npc_info 이력 기록
- StateTracker.bind_db / get_npc_change_history / get_npc_latest_fields
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager
from modules.domain.agents.state_tracker import StateTracker

# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def tmp_db(tmp_path):
    """임시 DB 생성"""
    db_path = tmp_path / "test.db"
    db = DBManager(db_path)
    return db


@pytest.fixture
def tracker():
    """StateTracker (DB 미바인딩)"""
    return StateTracker()


@pytest.fixture
def tracker_with_db(tmp_db):
    """StateTracker + DB 바인딩"""
    t = StateTracker()
    t.bind_db(tmp_db)
    return t, tmp_db


# ══════════════════════════════════════════════════════════════
# TestNPCHistoryDB — DB CRUD 직접 테스트
# ══════════════════════════════════════════════════════════════


class TestNPCHistoryDB:
    def test_create_table(self, tmp_db):
        """npc_history 테이블이 생성되어야 한다"""
        cur = tmp_db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='npc_history'")
        assert cur.fetchone() is not None

    def test_insert_and_query(self, tmp_db):
        """삽입 후 조회 결과가 일치해야 한다"""
        tmp_db.insert_npc_change("장무기", 5, 2, "weapon", "없음", "의천검", "arc_extraction")
        history = tmp_db.get_npc_history("장무기")
        assert len(history) == 1
        row = history[0]
        assert row["npc_name"] == "장무기"
        assert row["episode_no"] == 5
        assert row["arc_no"] == 2
        assert row["field_name"] == "weapon"
        assert row["old_value"] == "없음"
        assert row["new_value"] == "의천검"
        assert row["change_source"] == "arc_extraction"

    def test_latest_fields(self, tmp_db):
        """필드별 최신 값만 반환해야 한다"""
        tmp_db.insert_npc_change("장무기", 0, 1, "weapon", "", "목검")
        tmp_db.insert_npc_change("장무기", 0, 3, "weapon", "목검", "의천검")
        tmp_db.insert_npc_change("장무기", 0, 2, "level", "", "초급")
        latest = tmp_db.get_npc_latest_fields("장무기")
        assert latest["weapon"] == "의천검"
        assert latest["level"] == "초급"

    def test_multiple_changes_ordering(self, tmp_db):
        """최신순 정렬이어야 한다 (id DESC)"""
        tmp_db.insert_npc_change("조민", 0, 1, "status", "alive", "dead")
        tmp_db.insert_npc_change("조민", 0, 5, "status", "dead", "alive")
        history = tmp_db.get_npc_history("조민")
        assert len(history) == 2
        assert history[0]["new_value"] == "alive"  # 최신
        assert history[1]["new_value"] == "dead"  # 이전

    def test_empty_history(self, tmp_db):
        """이력 없는 NPC → 빈 리스트"""
        assert tmp_db.get_npc_history("존재하지않는NPC") == []

    def test_latest_fields_empty(self, tmp_db):
        """이력 없는 NPC → 빈 dict"""
        assert tmp_db.get_npc_latest_fields("존재하지않는NPC") == {}

    def test_limit_parameter(self, tmp_db):
        """limit 파라미터가 결과 수를 제한해야 한다"""
        for i in range(10):
            tmp_db.insert_npc_change("장무기", 0, i, "level", f"lv{i}", f"lv{i + 1}")
        history = tmp_db.get_npc_history("장무기", limit=3)
        assert len(history) == 3


# ══════════════════════════════════════════════════════════════
# TestNPCRecordChange — StateTrackerNPC 이력 기록 통합
# ══════════════════════════════════════════════════════════════


class TestNPCRecordChange:
    def test_death_records_history(self, tracker_with_db):
        """register_npc_death → DB 이력 1건 기록"""
        tracker, db = tracker_with_db
        tracker.register_npc_death("사현", 3, "전투 중 사망")
        history = db.get_npc_history("사현")
        assert len(history) == 1
        assert history[0]["field_name"] == "status"
        assert history[0]["old_value"] == "alive"
        assert history[0]["new_value"] == "dead"

    def test_info_change_records_diff(self, tracker_with_db):
        """weapon 변경 시 이력 기록"""
        tracker, db = tracker_with_db
        tracker.register_npc_info("장무기", arc_no=1, weapon="목검")
        tracker.register_npc_info("장무기", arc_no=3, weapon="의천검")
        history = db.get_npc_history("장무기")
        assert len(history) == 2
        # 최신순: 의천검 변경이 먼저
        assert history[0]["old_value"] == "목검"
        assert history[0]["new_value"] == "의천검"
        # 초기 등록
        assert history[1]["old_value"] == ""
        assert history[1]["new_value"] == "목검"

    def test_same_value_no_record(self, tracker_with_db):
        """동일 값으로 업데이트 → 이력 미기록"""
        tracker, db = tracker_with_db
        tracker.register_npc_info("장무기", arc_no=1, weapon="목검")
        tracker.register_npc_info("장무기", arc_no=2, weapon="목검")  # 동일
        history = db.get_npc_history("장무기")
        assert len(history) == 1  # 최초 등록 1건만

    def test_record_failure_nonblocking(self, tracker):
        """DB 없어도(bind_db 미호출) 비차단으로 동작"""
        # _db가 None이므로 _record_change는 no-op, 예외 없음
        tracker.register_npc_death("테스트NPC", 1)
        assert tracker.npc_registry["테스트NPC"]["status"] == "dead"

    def test_personality_change_recorded(self, tracker_with_db):
        """personality_traits 변경 시 이력 기록"""
        tracker, db = tracker_with_db
        tracker.register_npc_info("무량검주", arc_no=1, personality_traits="냉혹한")
        tracker.register_npc_info("무량검주", arc_no=5, personality_traits="온화한")
        history = db.get_npc_history("무량검주")
        personality_records = [h for h in history if h["field_name"] == "personality_traits"]
        assert len(personality_records) == 2

    def test_multiple_fields_single_call(self, tracker_with_db):
        """한 번의 register_npc_info에서 여러 필드 변경 시 각각 기록"""
        tracker, db = tracker_with_db
        tracker.register_npc_info("장무기", arc_no=1, weapon="목검", level="초급")
        history = db.get_npc_history("장무기")
        fields = {h["field_name"] for h in history}
        assert fields == {"weapon", "level"}


# ══════════════════════════════════════════════════════════════
# TestBindDB — bind_db API 테스트
# ══════════════════════════════════════════════════════════════


class TestBindDB:
    def test_bind_db_enables_recording(self, tmp_db):
        """bind_db 후 이력 기록이 작동한다"""
        tracker = StateTracker()
        tracker.bind_db(tmp_db)
        tracker.register_npc_info("장무기", arc_no=1, weapon="의천검")
        history = tracker.get_npc_change_history("장무기")
        assert len(history) == 1
        assert history[0]["new_value"] == "의천검"

    def test_no_bind_graceful(self):
        """bind_db 미호출 → facade가 빈 결과 반환"""
        tracker = StateTracker()
        assert tracker.get_npc_change_history("누군가") == []
        assert tracker.get_npc_latest_fields("누군가") == {}

    def test_get_latest_fields_via_facade(self, tmp_db):
        """facade를 통해 최신 필드 조회"""
        tracker = StateTracker()
        tracker.bind_db(tmp_db)
        tracker.register_npc_info("장무기", arc_no=1, weapon="목검")
        tracker.register_npc_info("장무기", arc_no=3, weapon="의천검")
        latest = tracker.get_npc_latest_fields("장무기")
        assert latest["weapon"] == "의천검"
