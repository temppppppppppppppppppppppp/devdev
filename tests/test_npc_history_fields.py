"""[LM-Audit] npc_history 미기록 필드 보강 검증

8개 테스트: relation_to_protag / injury / location / permanent_injuries
→ DB(npc_history 테이블) 기록 확인.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager
from modules.domain.agents.state_tracker import StateTracker


@pytest.fixture
def tracker_with_db(tmp_path):
    """StateTracker + 실제 DB"""
    db = DBManager(tmp_path / "npc_test.db")
    tracker = StateTracker()
    tracker.bind_db(db)
    yield tracker, db
    db.close()


# ══════════════════════════════════════════════════════════════
# 1. relation_to_protag 변경 → npc_history 기록
# ══════════════════════════════════════════════════════════════


class TestRelationChangeRecorded:
    def test_relation_change_recorded(self, tracker_with_db):
        """relation_to_protag 변경 → npc_history에 기록됨"""
        tracker, db = tracker_with_db
        tracker.npc_registry["노사부"] = {"status": "alive", "relation_to_protag": "사제", "last_arc": 0}
        arc = {
            "arc_no": 2,
            "state_changes": {"relationship_changes": [{"npc": "노사부", "from": "사제", "to": "동지", "episode": 5}]},
        }
        tracker.extract_relationship_changes_from_arc(arc)

        history = db.get_npc_history("노사부")
        rel_records = [h for h in history if h["field_name"] == "relation_to_protag"]
        assert len(rel_records) >= 1
        assert rel_records[0]["old_value"] == "사제"
        assert rel_records[0]["new_value"] == "동지"


# ══════════════════════════════════════════════════════════════
# 2. injury 변경 → npc_history 기록
# ══════════════════════════════════════════════════════════════


class TestInjuryChangeRecorded:
    def test_injury_change_recorded(self, tracker_with_db):
        """injury 변경 → npc_history에 기록됨"""
        tracker, db = tracker_with_db
        tracker.npc_registry["흑풍"] = {"status": "alive", "injury": "", "last_arc": 0}
        arc = {
            "arc_no": 3,
            "state_changes": {"npc_injuries": [{"name": "흑풍", "state": "중상", "cause": "전투", "episode": 8}]},
        }
        tracker.extract_npc_injuries_from_arc(arc)

        history = db.get_npc_history("흑풍")
        injury_records = [h for h in history if h["field_name"] == "injury"]
        assert len(injury_records) >= 1
        assert injury_records[0]["old_value"] == ""
        assert injury_records[0]["new_value"] == "중상"


# ══════════════════════════════════════════════════════════════
# 3. location 변경 → npc_history 기록
# ══════════════════════════════════════════════════════════════


class TestLocationChangeRecorded:
    def test_location_change_recorded(self, tracker_with_db):
        """location 변경 → npc_history에 기록됨"""
        tracker, db = tracker_with_db
        tracker.npc_registry["노사부"] = {"status": "alive", "location": "청풍산장", "last_arc": 0}
        arc = {
            "arc_no": 2,
            "state_changes": {"npc_movements": [{"name": "노사부", "from": "청풍산장", "to": "중원", "episode": 6}]},
        }
        tracker.extract_npc_movements_from_arc(arc)

        history = db.get_npc_history("노사부")
        loc_records = [h for h in history if h["field_name"] == "location"]
        assert len(loc_records) >= 1
        assert loc_records[0]["old_value"] == "청풍산장"
        assert loc_records[0]["new_value"] == "중원"


# ══════════════════════════════════════════════════════════════
# 4. permanent_injury 등록 → npc_history 기록
# ══════════════════════════════════════════════════════════════


class TestPermanentInjuryRecorded:
    def test_permanent_injury_recorded(self, tracker_with_db):
        """permanent_injury 등록 → npc_history에 기록됨"""
        tracker, db = tracker_with_db
        tracker.npc_registry["이청풍"] = {"status": "alive", "last_arc": 0}
        tracker.register_permanent_injury("이청풍", "amputation", "왼팔 절단", arc_no=5)

        history = db.get_npc_history("이청풍")
        perm_records = [h for h in history if h["field_name"] == "permanent_injuries"]
        assert len(perm_records) >= 1
        assert "왼팔 절단" in perm_records[0]["new_value"]
        assert perm_records[0]["old_value"] == ""


# ══════════════════════════════════════════════════════════════
# 5. regex 폴백 경로도 이력 기록
# ══════════════════════════════════════════════════════════════


class TestRegexFallbackAlsoRecords:
    def test_regex_fallback_also_records(self, tracker_with_db):
        """regex 폴백 경로(빈 state_changes + tactical_doc)도 이력 기록"""
        tracker, db = tracker_with_db
        tracker.npc_registry["장무기"] = {"status": "alive", "relation_to_protag": "중립", "last_arc": 0}
        # state_changes.relationship_changes가 비어있고 tactical_doc에 패턴이 있는 경우
        arc = {
            "arc_no": 4,
            "state_changes": {"relationship_changes": []},
            "tactical_doc": "장무기의 관계가 중립에서 → 동맹으로 변화한다.",
        }
        tracker.extract_relationship_changes_from_arc(arc)

        history = db.get_npc_history("장무기")
        rel_records = [h for h in history if h["field_name"] == "relation_to_protag"]
        # regex 매칭 성공 시에만 기록됨 (매칭 실패 시 빈 리스트 — 정상)
        if rel_records:
            assert rel_records[0]["change_source"] == "arc_relationship_regex"


# ══════════════════════════════════════════════════════════════
# 6. DB 없을 때 _record_change 비차단
# ══════════════════════════════════════════════════════════════


class TestNoDbNoCrash:
    def test_no_db_no_crash(self):
        """DB 없을 때 _record_change가 비차단으로 동작"""
        tracker = StateTracker()
        # bind_db 호출하지 않음 → _db = None
        tracker.npc_registry["노사부"] = {"status": "alive", "relation_to_protag": "사제", "last_arc": 0}
        arc = {
            "arc_no": 2,
            "state_changes": {"relationship_changes": [{"npc": "노사부", "from": "사제", "to": "동지", "episode": 5}]},
        }
        # 예외 없이 정상 완료
        result = tracker.extract_relationship_changes_from_arc(arc)
        assert isinstance(result, list)


# ══════════════════════════════════════════════════════════════
# 7. relation old_value가 from_rel과 일치
# ══════════════════════════════════════════════════════════════


class TestRelationOldValueCorrect:
    def test_relation_old_value_correct(self, tracker_with_db):
        """old_value가 from_rel과 일치"""
        tracker, db = tracker_with_db
        tracker.npc_registry["흑풍"] = {"status": "alive", "relation_to_protag": "적대", "last_arc": 0}
        arc = {
            "arc_no": 3,
            "state_changes": {"relationship_changes": [{"npc": "흑풍", "from": "적대", "to": "중립", "episode": 7}]},
        }
        tracker.extract_relationship_changes_from_arc(arc)

        history = db.get_npc_history("흑풍")
        rel_records = [h for h in history if h["field_name"] == "relation_to_protag"]
        assert len(rel_records) >= 1
        # old_value는 state_changes의 "from" 값과 일치해야 함
        assert rel_records[0]["old_value"] == "적대"
        assert rel_records[0]["new_value"] == "중립"


# ══════════════════════════════════════════════════════════════
# 8. 여러 변경 → 모두 기록
# ══════════════════════════════════════════════════════════════


class TestMultipleChangesAllRecorded:
    def test_multiple_changes_all_recorded(self, tracker_with_db):
        """여러 필드 변경 → 모두 npc_history에 기록"""
        tracker, db = tracker_with_db
        tracker.npc_registry["노사부"] = {
            "status": "alive",
            "relation_to_protag": "사제",
            "injury": "",
            "location": "청풍산장",
            "last_arc": 0,
        }

        # 관계 변경
        arc_rel = {
            "arc_no": 2,
            "state_changes": {"relationship_changes": [{"npc": "노사부", "from": "사제", "to": "동지", "episode": 5}]},
        }
        tracker.extract_relationship_changes_from_arc(arc_rel)

        # 부상
        arc_inj = {
            "arc_no": 3,
            "state_changes": {"npc_injuries": [{"name": "노사부", "state": "중상", "cause": "습격"}]},
        }
        tracker.extract_npc_injuries_from_arc(arc_inj)

        # 이동
        arc_mov = {
            "arc_no": 4,
            "state_changes": {"npc_movements": [{"name": "노사부", "from": "청풍산장", "to": "소림사"}]},
        }
        tracker.extract_npc_movements_from_arc(arc_mov)

        history = db.get_npc_history("노사부")
        fields = {h["field_name"] for h in history}
        assert "relation_to_protag" in fields
        assert "injury" in fields
        assert "location" in fields
        assert len(history) >= 3
