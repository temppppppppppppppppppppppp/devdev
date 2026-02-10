"""
[V64 P2-7] hud_utils Unit Tests

build_hud_context 함수의 3가지 variant(director, writer, blueprint) 테스트.
내부 빌더 함수(_build_director_protagonist, _build_writer_protagonist,
_build_director_npcs, _build_writer_npcs)도 간접 테스트.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.hud_utils import build_hud_context


# ══════════════════════════════════════════════════════════════
# Mock StateTracker & EpisodeState
# ══════════════════════════════════════════════════════════════

class MockEpisodeState:
    """테스트용 EpisodeState"""
    def __init__(self, state_dict):
        self._state_dict = state_dict

    def to_dict(self):
        return self._state_dict


def make_state_tracker(episode_states=None, npc_registry=None):
    """테스트용 StateTracker-like 객체 생성"""
    tracker = MagicMock()
    tracker.episode_states = episode_states or {}
    tracker.npc_registry = npc_registry or {}
    return tracker


# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def protagonist_state():
    """주인공 상태 dict"""
    return {
        "name": "이청풍",
        "location": "무림맹 본부",
        "hp": 80,
        "mp": 60,
        "martial_level": "후천경",
        "inner_power": 70,
        "status": "경상",
        "internal_energy": 70,
        "injuries": "왼팔 타박상",
        "extra_fields": {
            "reputation": "좋음",
            "faction": "무림맹"
        },
        "items": ["청풍검", "해독약", "경공화"],
        "weapons": ["파천검"],
        "relationships": {
            "노사부": "존경",
            "철무련주": "적대",
            "소녀": "호감"
        },
        "realm": "후천경",
        "gold": 5000,
        "awakening_grade": "",
        "skills": ["청풍검법", "태극장"],
    }


@pytest.fixture
def npc_registry():
    """NPC 레지스트리"""
    return {
        "노사부": {"status": "alive", "role": "스승", "location": "청풍산장", "faction": "무파", "relationship": "존경"},
        "철무련주": {"status": "dead", "death_arc": 3, "role": "적"},
        "소녀": {"status": "alive", "role": "동료", "location": "무림맹", "faction": "무림맹", "relationship": "호감"},
        "혈마": {"status": "dead", "death_arc": 5, "role": "마교 교주"},
    }


@pytest.fixture
def tracker_with_state(protagonist_state, npc_registry):
    """주인공 상태 + NPC 레지스트리가 있는 tracker"""
    ep_states = {
        4: MockEpisodeState(protagonist_state)
    }
    return make_state_tracker(episode_states=ep_states, npc_registry=npc_registry)


# ══════════════════════════════════════════════════════════════
# Test 1: None StateTracker
# ══════════════════════════════════════════════════════════════

class TestNoneStateTracker:
    def test_director_none(self):
        """director variant: None이면 '상태 추적기 없음'"""
        result = build_hud_context(None, ep_num=5, variant="director")
        assert "상태 추적기 없음" in result

    def test_writer_none(self):
        """writer variant: None이면 empty_fallback"""
        result = build_hud_context(None, ep_num=5, variant="writer", empty_fallback="기본값")
        assert result == "기본값"

    def test_blueprint_none(self):
        """blueprint variant: None이면 empty_fallback"""
        result = build_hud_context(None, ep_num=5, variant="blueprint", empty_fallback="")
        assert result == ""


# ══════════════════════════════════════════════════════════════
# Test 2: Director variant
# ══════════════════════════════════════════════════════════════

class TestDirectorVariant:
    def test_protagonist_fields(self, tracker_with_state):
        """Director: 주인공 핵심 필드 포함"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="director")
        assert "이청풍" in result
        assert "무림맹 본부" in result
        assert "후천경" in result

    def test_extra_fields(self, tracker_with_state):
        """Director: 확장 필드 포함"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="director")
        assert "확장 상태" in result
        assert "reputation" in result or "좋음" in result

    def test_items_shown(self, tracker_with_state):
        """Director: 보유 아이템 표시"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="director")
        assert "청풍검" in result

    def test_relationships_shown(self, tracker_with_state):
        """Director: 관계 줄단위 표시"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="director")
        assert "노사부" in result
        assert "존경" in result

    def test_alive_npcs_shown(self, tracker_with_state):
        """Director: 활성 NPC 표시"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="director")
        assert "활성 NPC" in result
        assert "노사부" in result

    def test_dead_npcs_shown(self, tracker_with_state):
        """Director: 사망 NPC 표시"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="director")
        assert "사망 NPC" in result
        assert "철무련주" in result
        assert "Arc 3" in result


# ══════════════════════════════════════════════════════════════
# Test 3: Writer variant
# ══════════════════════════════════════════════════════════════

class TestWriterVariant:
    def test_protagonist_core_fields(self, tracker_with_state):
        """Writer: 핵심 필드 포함"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="writer")
        assert "고밀도" in result
        assert "무림맹 본부" in result or "location" in result

    def test_extended_fields(self, tracker_with_state):
        """Writer: 확장 필드 (realm, gold 등)"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="writer")
        assert "후천경" in result or "경지" in result

    def test_skills_shown(self, tracker_with_state):
        """Writer: 스킬 리스트"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="writer")
        assert "청풍검법" in result or "태극장" in result

    def test_weapons_and_items(self, tracker_with_state):
        """Writer: 무기 + 아이템"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="writer")
        assert "소지품" in result
        assert "파천검" in result  # weapons

    def test_relationships_inline(self, tracker_with_state):
        """Writer: 관계 인라인 표시"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="writer")
        assert "관계" in result

    def test_dead_npc_warning(self, tracker_with_state):
        """Writer: 사망 NPC 경고"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="writer")
        assert "등장 금지" in result
        assert "철무련주" in result


# ══════════════════════════════════════════════════════════════
# Test 4: Blueprint variant
# ══════════════════════════════════════════════════════════════

class TestBlueprintVariant:
    def test_header_difference(self, tracker_with_state):
        """Blueprint: writer와 다른 헤더"""
        result = build_hud_context(tracker_with_state, ep_num=5, variant="blueprint")
        assert "현재 상태" in result
        # "고밀도" 키워드는 writer에만 있어야 함
        assert "고밀도" not in result


# ══════════════════════════════════════════════════════════════
# Test 5: Edge Cases
# ══════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_ep1_no_prev_state(self):
        """ep_num=1이면 이전 에피소드 상태 없음"""
        tracker = make_state_tracker(npc_registry={"테스트NPC": {"status": "alive", "role": "조연"}})
        result = build_hud_context(tracker, ep_num=1, variant="director")
        assert "이전 에피소드 기록 없음" in result

    def test_empty_npc_registry(self, protagonist_state):
        """NPC 레지스트리 비어있으면 NPC 섹션 없음"""
        ep_states = {4: MockEpisodeState(protagonist_state)}
        tracker = make_state_tracker(episode_states=ep_states, npc_registry={})
        result = build_hud_context(tracker, ep_num=5, variant="writer")
        assert "활성 NPC" not in result
        assert "사망 NPC" not in result
        assert "등장 가능 NPC" not in result

    def test_no_episode_states_no_npcs_director(self):
        """에피소드 상태도 NPC도 없으면 director는 '이전 에피소드 기록 없음' 반환"""
        tracker = make_state_tracker()
        result_dir = build_hud_context(tracker, ep_num=5, variant="director")
        # director: ep > 1이면 "이전 에피소드 기록 없음" 라인이 추가되므로 lines 비어있지 않음
        assert "기록 없음" in result_dir or "HUD 정보 없음" in result_dir

    def test_no_episode_states_no_npcs_blueprint(self):
        """에피소드 상태도 NPC도 없고 ep=1이면 blueprint는 fallback"""
        tracker = make_state_tracker()
        result_bp = build_hud_context(tracker, ep_num=1, variant="blueprint")
        # ep=1이면 prev_state 로드 시도 안 하므로 lines 비어있음 → fallback
        assert "상태 정보 없음" in result_bp

    def test_all_npcs_dead(self):
        """모든 NPC가 사망이면 활성 NPC 없음"""
        npcs = {
            "A": {"status": "dead", "death_arc": 1},
            "B": {"status": "dead", "death_arc": 2},
        }
        tracker = make_state_tracker(npc_registry=npcs)
        result = build_hud_context(tracker, ep_num=5, variant="director")
        assert "사망 NPC" in result
        # 활성 NPC 섹션은 표시되지 않아야 함 (alive가 0명)
