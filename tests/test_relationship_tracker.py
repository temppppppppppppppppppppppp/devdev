"""
[V64 P2-7] RelationshipTracker Unit Tests

NPC 관계 상태 머신(validate_transition, record_transition),
세력 관계(register_faction_v59, validate_faction_transition_v59),
원고 추론(infer_state_from_manuscript), 파워 밸런스 분석.
"""

import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.relationship_tracker import (
    RelationshipTracker,
)

# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def tracker():
    """기본 RelationshipTracker"""
    return RelationshipTracker()


@pytest.fixture
def tracker_with_factions(tracker):
    """세력이 등록된 tracker"""
    tracker.register_faction_v59("무림맹", power_level=70, members=["맹주"], territory=["중원"], stance="우호")
    tracker.register_faction_v59("마교", power_level=80, members=["교주"], territory=["서역"], stance="적대")
    tracker.register_faction_v59("개방", power_level=40, members=["방주"], territory=["강남"], stance="중립")
    tracker.protagonist_faction = "무림맹"
    return tracker


# ══════════════════════════════════════════════════════════════
# Test 1: validate_transition (NPC FSM)
# ══════════════════════════════════════════════════════════════


class TestValidateTransition:
    def test_valid_transition(self, tracker):
        """허용된 전환은 valid=True"""
        result = tracker.validate_transition("철무련주", "무시", "의심")
        assert result["valid"] is True

    def test_invalid_transition(self, tracker):
        """불허 전환은 valid=False"""
        result = tracker.validate_transition("철무련주", "무시", "충성")
        assert result["valid"] is False
        assert "전환 불가능" in result["reason"]

    def test_same_state_always_valid(self, tracker):
        """같은 상태 유지는 항상 유효"""
        result = tracker.validate_transition("테스트", "적대", "적대")
        assert result["valid"] is True

    def test_unknown_state_passes(self, tracker):
        """'알 수 없음' 상태는 통과"""
        result = tracker.validate_transition("테스트", "알 수 없음", "충성")
        assert result["valid"] is True
        result2 = tracker.validate_transition("테스트", "무시", "알 수 없음")
        assert result2["valid"] is True

    def test_risky_transition_flagged(self, tracker):
        """위험한 전환은 risky=True"""
        result = tracker.validate_transition("테스트", "의심", "경외")
        assert result["valid"] is True
        assert result.get("risky") is True
        assert "경고" in result.get("reason", "") or "risk_warning" in result

    def test_death_is_terminal(self, tracker):
        """사망은 최종 상태 (전환 불가)"""
        result = tracker.validate_transition("테스트", "사망", "충성")
        assert result["valid"] is False

    def test_suggested_path(self, tracker):
        """불가 전환 시 권장 경로 제안"""
        result = tracker.validate_transition("테스트", "무시", "충성")
        assert "suggested_path" in result
        assert "의심" in result["suggested_path"]


# ══════════════════════════════════════════════════════════════
# Test 2: record_transition
# ══════════════════════════════════════════════════════════════


class TestRecordTransition:
    def test_successful_record(self, tracker):
        """정상 전이 기록"""
        result = tracker.record_transition(
            npc_name="철무련주",
            from_state="무시",
            to_state="의심",
            arc=1,
            episode=5,
            trigger="주인공이 마교를 물리치는 모습 목격",
            justification="무시하던 인물이 강한 것을 봤으므로 의심 시작",
        )
        assert result["valid"] is True
        assert result["event"] is not None
        assert tracker.npc_states["철무련주"] == "의심"
        assert len(tracker.transition_history) == 1

    def test_missing_trigger(self, tracker):
        """trigger 누락 시 실패"""
        result = tracker.record_transition(
            npc_name="철무련주",
            from_state="무시",
            to_state="의심",
            arc=1,
            episode=5,
            trigger="",  # 누락
            justification="충분한 근거가 있습니다",
        )
        assert result["valid"] is False
        assert "trigger" in result["error"]

    def test_short_trigger(self, tracker):
        """trigger가 너무 짧으면 실패 (5자 미만)"""
        result = tracker.record_transition(
            npc_name="철무련주",
            from_state="무시",
            to_state="의심",
            arc=1,
            episode=5,
            trigger="했다",  # 3자
            justification="충분한 근거가 있습니다 이것은 긴 문장입니다",
        )
        assert result["valid"] is False

    def test_missing_justification(self, tracker):
        """justification 누락 시 실패"""
        result = tracker.record_transition(
            npc_name="철무련주",
            from_state="무시",
            to_state="의심",
            arc=1,
            episode=5,
            trigger="마교 격퇴 목격",
            justification="짧",  # 10자 미만
        )
        assert result["valid"] is False
        assert "justification" in result["error"]

    def test_invalid_transition_blocked(self, tracker):
        """불가능한 전환은 기록 불가"""
        result = tracker.record_transition(
            npc_name="철무련주",
            from_state="무시",
            to_state="충성",
            arc=1,
            episode=5,
            trigger="어떤 사건이 발생",
            justification="이런 저런 이유로 충성하게 되었습니다",
        )
        assert result["valid"] is False


# ══════════════════════════════════════════════════════════════
# Test 3: validate_transition_with_justification
# ══════════════════════════════════════════════════════════════


class TestValidateTransitionWithJustification:
    def test_ok_validation(self, tracker):
        """정상 전환 + 충분한 사유"""
        result = tracker.validate_transition_with_justification(
            "테스트NPC", "무시", "의심", trigger="마교 격퇴", justification=""
        )
        # 1단계 점프는 justification 부족해도 trigger만 있으면 OK
        assert result["severity"] in ["OK", "WARNING"]

    def test_big_jump_without_justification(self, tracker):
        """2단계 이상 점프 + justification 부족 시 CRITICAL"""
        result = tracker.validate_transition_with_justification(
            "테스트NPC", "무시", "경외", trigger="", justification=""
        )
        # 무시→경외는 FSM에서 불허 (의심 거쳐야 함)
        assert result["severity"] == "CRITICAL"

    def test_no_trigger_warning(self, tracker):
        """trigger 없으면 WARNING (1단계 전환의 경우)"""
        # 적대→의심은 FSM에서 허용되고 state_order에서 2단계 점프이므로
        # justification 부족 시 CRITICAL.
        # 1단계 전환(경외→충성)에서 trigger만 누락 시 WARNING
        result = tracker.validate_transition_with_justification(
            "테스트NPC", "경외", "충성", trigger="", justification="목숨을 걸고 지켜준 은혜에 보답하고자 합니다"
        )
        assert result["severity"] == "WARNING"


# ══════════════════════════════════════════════════════════════
# Test 4: infer_state_from_manuscript
# ══════════════════════════════════════════════════════════════


class TestInferStateFromManuscript:
    def test_death_detected(self, tracker):
        """사망 키워드 감지"""
        result = tracker.infer_state_from_manuscript("철무련주", "철무련주가 결국 숨이 끊어졌다.")
        assert result == "사망"

    def test_loyalty_detected(self, tracker):
        """충성 키워드 감지"""
        result = tracker.infer_state_from_manuscript("노사부", "노사부는 목숨 바쳐 주인공을 지키겠다고 맹세했다.")
        assert result == "충성"

    def test_npc_not_found(self, tracker):
        """NPC가 원고에 없으면 '알 수 없음'"""
        result = tracker.infer_state_from_manuscript("없는NPC", "주인공이 걷고 있었다.")
        assert result == "알 수 없음"

    def test_default_neutral(self, tracker):
        """키워드 없으면 중립"""
        result = tracker.infer_state_from_manuscript("노사부", "노사부가 차를 마시고 있었다.")
        assert result == "중립"

    def test_suspicion_detected(self, tracker):
        """의심 키워드 감지"""
        result = tracker.infer_state_from_manuscript("철무련주", "철무련주는 의심 가득한 눈으로 바라보았다.")
        assert result == "의심"


# ══════════════════════════════════════════════════════════════
# Test 5: register_faction_v59
# ══════════════════════════════════════════════════════════════


class TestRegisterFaction:
    def test_basic_registration(self, tracker):
        """세력 기본 등록"""
        faction = tracker.register_faction_v59("무림맹", power_level=70)
        assert faction.name == "무림맹"
        assert faction.power_level == 70
        assert "무림맹" in tracker.factions

    def test_power_level_clamped(self, tracker):
        """파워 레벨 0-100 범위 고정"""
        f1 = tracker.register_faction_v59("약한문파", power_level=-10)
        assert f1.power_level == 0

        f2 = tracker.register_faction_v59("강한문파", power_level=150)
        assert f2.power_level == 100

    def test_default_values(self, tracker):
        """기본값 확인"""
        faction = tracker.register_faction_v59("테스트")
        assert faction.power_level == 50.0
        assert faction.members == []
        assert faction.stance == "중립"


# ══════════════════════════════════════════════════════════════
# Test 6: validate_faction_transition_v59
# ══════════════════════════════════════════════════════════════


class TestValidateFactionTransition:
    def test_valid_transition(self, tracker):
        """허용된 세력 전환"""
        result = tracker.validate_faction_transition_v59("A", "B", "중립", "우호")
        assert result["valid"] is True

    def test_invalid_transition(self, tracker):
        """불허 세력 전환"""
        result = tracker.validate_faction_transition_v59("A", "B", "동맹", "전쟁")
        assert result["valid"] is False

    def test_terminal_state(self, tracker):
        """최종 상태에서 전환 불가"""
        result = tracker.validate_faction_transition_v59("A", "B", "멸망", "중립")
        assert result["valid"] is False

    def test_same_state_valid(self, tracker):
        """같은 상태 유지"""
        result = tracker.validate_faction_transition_v59("A", "B", "중립", "중립")
        assert result["valid"] is True


# ══════════════════════════════════════════════════════════════
# Test 7: set_faction_relation_v59
# ══════════════════════════════════════════════════════════════


class TestSetFactionRelation:
    def test_symmetric_relation(self, tracker_with_factions):
        """양방향 관계 설정"""
        tracker_with_factions.set_faction_relation_v59("무림맹", "개방", "우호")
        assert tracker_with_factions.get_faction_relation_v59("무림맹", "개방") == "우호"
        assert tracker_with_factions.get_faction_relation_v59("개방", "무림맹") == "우호"

    def test_alliance_updates_lists(self, tracker_with_factions):
        """동맹 시 allies 업데이트"""
        tracker_with_factions.set_faction_relation_v59("무림맹", "개방", "동맹")
        assert "개방" in tracker_with_factions.factions["무림맹"].allies
        assert "무림맹" in tracker_with_factions.factions["개방"].allies

    def test_hostile_updates_enemies(self, tracker_with_factions):
        """적대 시 enemies 업데이트"""
        tracker_with_factions.set_faction_relation_v59("무림맹", "마교", "적대")
        assert "마교" in tracker_with_factions.factions["무림맹"].enemies
        assert "무림맹" in tracker_with_factions.factions["마교"].enemies

    def test_invalid_state_rejected(self, tracker):
        """유효하지 않은 상태는 거부"""
        result = tracker.set_faction_relation_v59("A", "B", "존재하지않는상태")
        assert result is False

    def test_alliance_to_hostile_clears(self, tracker_with_factions):
        """동맹에서 적대 전환 시 allies에서 제거"""
        tracker_with_factions.set_faction_relation_v59("무림맹", "개방", "동맹")
        assert "개방" in tracker_with_factions.factions["무림맹"].allies

        tracker_with_factions.set_faction_relation_v59("무림맹", "개방", "적대")
        assert "개방" not in tracker_with_factions.factions["무림맹"].allies
        assert "개방" in tracker_with_factions.factions["무림맹"].enemies


# ══════════════════════════════════════════════════════════════
# Test 8: record_faction_transition_v59
# ══════════════════════════════════════════════════════════════


class TestRecordFactionTransition:
    def test_successful_record(self, tracker_with_factions):
        """정상 세력 전이 기록"""
        result = tracker_with_factions.record_faction_transition_v59(
            "무림맹",
            "마교",
            "경계",
            "적대",
            arc=3,
            episode=15,
            trigger="마교의 중원 침공 시작",
            justification="마교가 무림맹 분파를 습격하며 전면 적대 관계 형성",
        )
        assert result["valid"] is True
        assert len(tracker_with_factions.faction_transition_history) == 1

    def test_power_shift_applied(self, tracker_with_factions):
        """파워 시프트 적용"""
        original_a = tracker_with_factions.factions["무림맹"].power_level
        original_b = tracker_with_factions.factions["마교"].power_level

        tracker_with_factions.record_faction_transition_v59(
            "무림맹",
            "마교",
            "경계",
            "적대",
            arc=3,
            episode=15,
            trigger="마교 침공으로 대규모 충돌",
            justification="무림맹이 선제 방어에 성공하면서 파워 밸런스 변화",
            power_shift=0.5,  # 무림맹 유리
        )
        assert tracker_with_factions.factions["무림맹"].power_level > original_a
        assert tracker_with_factions.factions["마교"].power_level < original_b

    def test_missing_trigger_fails(self, tracker_with_factions):
        """trigger 누락 시 실패"""
        result = tracker_with_factions.record_faction_transition_v59(
            "무림맹", "마교", "경계", "적대", arc=3, episode=15, trigger="", justification="충분한 사유가 있습니다"
        )
        assert result["valid"] is False


# ══════════════════════════════════════════════════════════════
# Test 9: get_faction_power_balance_v59
# ══════════════════════════════════════════════════════════════


class TestGetFactionPowerBalance:
    def test_basic_balance(self, tracker_with_factions):
        """기본 파워 밸런스 분석"""
        result = tracker_with_factions.get_faction_power_balance_v59()
        assert result["dominant_faction"] == "마교"  # power 80 > 70 > 40
        assert "마교" in result["power_distribution"]
        assert isinstance(result["stability_score"], float)

    def test_empty_factions(self, tracker):
        """세력 없으면 기본값"""
        result = tracker.get_faction_power_balance_v59()
        assert result["dominant_faction"] is None
        assert result["balance_type"] == "fragmented"

    def test_monopoly_detection(self, tracker):
        """일극 체제 감지"""
        tracker.register_faction_v59("초강대국", power_level=90)
        tracker.register_faction_v59("약소국1", power_level=5)
        tracker.register_faction_v59("약소국2", power_level=5)
        result = tracker.get_faction_power_balance_v59()
        assert result["balance_type"] == "monopoly"

    def test_war_reduces_stability(self, tracker_with_factions):
        """전쟁 상태 시 안정성 감소"""
        balance_before = tracker_with_factions.get_faction_power_balance_v59()
        tracker_with_factions.set_faction_relation_v59("무림맹", "마교", "전쟁")
        balance_after = tracker_with_factions.get_faction_power_balance_v59()
        assert balance_after["stability_score"] < balance_before["stability_score"]


# ══════════════════════════════════════════════════════════════
# Test 10: infer_faction_state_from_manuscript_v59
# ══════════════════════════════════════════════════════════════


class TestInferFactionState:
    def test_war_detected(self, tracker):
        """전쟁 키워드 감지"""
        manuscript = "무림맹과 마교의 전쟁이 시작되었다. 양측 군대가 충돌했다."
        result = tracker.infer_faction_state_from_manuscript_v59("무림맹", "마교", manuscript)
        assert result == "전쟁"

    def test_alliance_detected(self, tracker):
        """동맹 키워드 감지"""
        manuscript = "무림맹과 개방이 동맹을 맺고 함께 싸우기로 했다."
        result = tracker.infer_faction_state_from_manuscript_v59("무림맹", "개방", manuscript)
        assert result == "동맹"

    def test_not_mentioned(self, tracker):
        """언급 안 되면 알 수 없음"""
        result = tracker.infer_faction_state_from_manuscript_v59("무림맹", "마교", "오늘은 맑은 날이었다.")
        assert result == "알 수 없음"

    def test_one_faction_missing(self, tracker):
        """한쪽만 언급되면 알 수 없음"""
        result = tracker.infer_faction_state_from_manuscript_v59("무림맹", "마교", "무림맹이 연회를 열었다.")
        assert result == "알 수 없음"


# ══════════════════════════════════════════════════════════════
# Test 11: generate_transition_prompt
# ══════════════════════════════════════════════════════════════


class TestGenerateTransitionPrompt:
    def test_known_transition(self, tracker):
        """알려진 전환 조건 프롬프트"""
        result = tracker.generate_transition_prompt("의심", "경외")
        assert "경외" in result
        assert "trigger" in result

    def test_unknown_transition(self, tracker):
        """알 수 없는 전환은 빈 문자열"""
        result = tracker.generate_transition_prompt("중립", "중립")
        assert result == ""


# ══════════════════════════════════════════════════════════════
# Test 12: get_transition_history
# ══════════════════════════════════════════════════════════════


class TestGetTransitionHistory:
    def test_empty_history(self, tracker):
        """비어있는 이력"""
        result = tracker.get_transition_history()
        assert result == []

    def test_filtered_by_npc(self, tracker):
        """NPC별 필터링"""
        tracker.record_transition("A", "무시", "의심", 1, 1, "사건A 발생", "근거A가 충분합니다")
        tracker.record_transition("B", "무시", "의심", 1, 2, "사건B 발생", "근거B가 충분합니다")

        result_a = tracker.get_transition_history("A")
        assert len(result_a) == 1
        assert result_a[0]["npc"] == "A"

        result_all = tracker.get_transition_history()
        assert len(result_all) == 2
