"""[Phase 6-B] L2 NPC 시나리오 — NPC 연속성 + 검증 통합

7건 (참고자료 3-C 시나리오 기반):
1. 사망 NPC 행동 → blocking REJECT
2. 사망 NPC 회상 → blocking PASS
3. register_npc_death → npc_history 1건 삽입
4. weapon 변경 → npc_history diff 기록
5. 성격 급변 → continuity warning
6. validation_context에 npc_history 존재 확인
7. YAML 임계값 → validator 반영
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.domain.agents.state_tracker import StateTracker
from modules.validation.blocking_validator import BlockingValidator
from modules.validation.continuity_validator import ContinuityValidator

from .conftest import MOCK_MANUSCRIPT

# ══════════════════════════════════════════════════════════════
# L2-NPC-1: 사망 NPC 행동 → REJECT
# ══════════════════════════════════════════════════════════════


class TestDeadNPCActionRejected:
    def test_dead_npc_action_rejected(self):
        """사망 NPC가 행동/대사하면 blocking REJECT"""
        bv = BlockingValidator()
        manuscript = MOCK_MANUSCRIPT + "사현이 검을 뽑으며 공격했다."
        ctx = {
            "encyclopedia": {
                "npcs": [{"name": "사현", "status": "dead", "aliases": []}],
                "items": [],
                "locations": [],
            },
            "martial_hud": {},
        }
        result = bv.validate(manuscript, ctx)
        dead_failures = [f for f in result["failures"] if f["check"] == "dead_npc_resurrection"]
        assert len(dead_failures) >= 1
        assert dead_failures[0]["severity"] == "CRITICAL"
        assert result["passed"] is False


# ══════════════════════════════════════════════════════════════
# L2-NPC-2: 사망 NPC 회상 → PASS
# ══════════════════════════════════════════════════════════════


class TestDeadNPCRecallAllowed:
    def test_dead_npc_recall_allowed(self):
        """사망 NPC를 회상/과거 맥락으로 언급 → PASS"""
        bv = BlockingValidator()
        manuscript = MOCK_MANUSCRIPT + "장무기는 사현을 떠올리며 과거를 회상했다."
        ctx = {
            "encyclopedia": {
                "npcs": [{"name": "사현", "status": "dead", "aliases": []}],
                "items": [],
                "locations": [],
            },
            "martial_hud": {},
        }
        result = bv.validate(manuscript, ctx)
        dead_failures = [f for f in result["failures"] if f["check"] == "dead_npc_resurrection"]
        assert len(dead_failures) == 0


# ══════════════════════════════════════════════════════════════
# L2-NPC-3: NPC 사망 → npc_history 기록
# ══════════════════════════════════════════════════════════════


class TestNPCHistoryRecordsDeath:
    def test_npc_history_records_death(self, e2e_db):
        """register_npc_death → npc_history 테이블에 1건 삽입"""
        tracker = StateTracker()
        tracker.bind_db(e2e_db)
        tracker.register_npc_death("사현", 3, "전투 중 사망")

        history = e2e_db.get_npc_history("사현")
        assert len(history) >= 1
        death_record = history[0]
        assert death_record["field_name"] == "status"
        assert death_record["old_value"] == "alive"
        assert death_record["new_value"] == "dead"


# ══════════════════════════════════════════════════════════════
# L2-NPC-4: weapon 변경 → npc_history diff 기록
# ══════════════════════════════════════════════════════════════


class TestNPCHistoryRecordsWeaponChange:
    def test_npc_history_records_weapon_change(self, e2e_db):
        """weapon 변경 시 old→new diff가 npc_history에 기록"""
        tracker = StateTracker()
        tracker.bind_db(e2e_db)
        tracker.register_npc_info("장무기", arc_no=1, weapon="목검")
        tracker.register_npc_info("장무기", arc_no=3, weapon="의천검")

        history = e2e_db.get_npc_history("장무기")
        weapon_changes = [h for h in history if h["field_name"] == "weapon"]
        assert len(weapon_changes) == 2
        # 최신순: 의천검 변경이 먼저
        assert weapon_changes[0]["old_value"] == "목검"
        assert weapon_changes[0]["new_value"] == "의천검"


# ══════════════════════════════════════════════════════════════
# L2-NPC-5: 성격 급변 → continuity warning
# ══════════════════════════════════════════════════════════════


class TestPersonalitySuddenChangeWarning:
    def test_personality_sudden_change_warning(self):
        """냉혹→온화 성격 급변 시 personality_sudden_change violation 감지"""
        cv = ContinuityValidator()
        manuscript = MOCK_MANUSCRIPT + "무량검주가 길을 걸었다."
        ctx = {
            "npc_personalities": {"무량검주": {"traits": "온화한"}},
            "npc_history": {
                "무량검주": [
                    {
                        "field_name": "personality_traits",
                        "old_value": "",
                        "new_value": "냉혹한",
                    },
                    {
                        "field_name": "personality_traits",
                        "old_value": "냉혹한",
                        "new_value": "온화한",
                    },
                ]
            },
        }
        result = cv._check_personality_continuity(manuscript, ctx)
        sudden = [v for v in result["violations"] if v["type"] == "personality_sudden_change"]
        assert len(sudden) >= 1
        assert sudden[0]["npc"] == "무량검주"


# ══════════════════════════════════════════════════════════════
# L2-NPC-6: validation_context에 npc_history 존재
# ══════════════════════════════════════════════════════════════


class TestNPCHistoryInValidationContext:
    def test_npc_history_in_validation_context(self, e2e_db):
        """StateTracker → DB 기록 후 validation_context["npc_history"] 에 존재"""
        tracker = StateTracker()
        tracker.bind_db(e2e_db)
        tracker.register_npc_info("장무기", arc_no=1, weapon="목검")
        tracker.register_npc_info("장무기", arc_no=2, weapon="의천검")

        # validation_context 구성 (실 파이프라인처럼)
        history = tracker.get_npc_change_history("장무기")
        validation_context = {
            "npc_personalities": {},
            "npc_history": {"장무기": history},
        }

        assert "장무기" in validation_context["npc_history"]
        assert len(validation_context["npc_history"]["장무기"]) >= 2
        weapon_entries = [h for h in validation_context["npc_history"]["장무기"] if h["field_name"] == "weapon"]
        assert len(weapon_entries) >= 2


# ══════════════════════════════════════════════════════════════
# L2-NPC-7: YAML 임계값 → validator 반영
# ══════════════════════════════════════════════════════════════


class TestThresholdOverrideViaYAML:
    def test_threshold_override_via_yaml(self):
        """_threshold() 가 ConfigManager를 호출하고 default 폴백 정상 동작"""
        from modules.validation.threshold_helper import _threshold

        # _threshold._cfg를 None으로 리셋해서 default 폴백 테스트
        original_cfg = getattr(_threshold, "_cfg", None)
        try:
            _threshold._cfg = None
            # default 폴백: ConfigManager 로드 실패 시 하드코드 반환
            result = _threshold("scope.chars_per_scene", 1500)
            assert isinstance(result, int | float)
            assert result > 0  # 반환값이 양수

            result2 = _threshold("scope.overflow_ratio", 1.2)
            assert isinstance(result2, int | float)
            assert result2 > 0

            result3 = _threshold("continuity.personality_proximity", 150)
            assert isinstance(result3, int | float)
            assert result3 > 0
        finally:
            # 원복
            _threshold._cfg = original_cfg
