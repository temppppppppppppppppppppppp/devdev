"""
[V64 P2-7] StateTracker Unit Tests

register_npc_death, _is_standalone_name, merge_npc_registry,
extract_resolved_plots_from_arc, register_entity_name (LRU),
check_entity_name_consistency, export/import_financial_registry,
check_dead_npc_in_manuscript 에 대한 단위 테스트.
"""

import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.domain.agents.state_tracker import StateTracker

# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def tracker():
    """기본 StateTracker 인스턴스"""
    return StateTracker()


@pytest.fixture
def tracker_with_dead_npc(tracker):
    """사망 NPC가 등록된 StateTracker"""
    tracker.register_npc_death("철무련주", death_arc=3, death_context="주인공에게 패배")
    tracker.register_npc_death("혈마", death_arc=5, death_context="독에 중독")
    return tracker


# ══════════════════════════════════════════════════════════════
# Test 1: register_npc_death
# ══════════════════════════════════════════════════════════════


class TestRegisterNpcDeath:
    def test_basic_registration(self, tracker):
        """NPC 사망 등록 기본 동작"""
        tracker.register_npc_death("철무련주", death_arc=3, death_context="전투 중 패배")

        assert "철무련주" in tracker.npc_registry
        info = tracker.npc_registry["철무련주"]
        assert info["status"] == "dead"
        assert info["death_arc"] == 3
        assert info["death_context"] == "전투 중 패배"

    def test_overwrite_existing_alive_npc(self, tracker):
        """살아있던 NPC를 사망으로 변경"""
        tracker.register_npc_info("철무련주", arc_no=1, weapon="철검")
        assert tracker.npc_registry["철무련주"]["status"] == "alive"

        tracker.register_npc_death("철무련주", death_arc=3)
        assert tracker.npc_registry["철무련주"]["status"] == "dead"
        assert tracker.npc_registry["철무련주"]["death_arc"] == 3

    def test_empty_context_default(self, tracker):
        """death_context 미지정 시 빈 문자열"""
        tracker.register_npc_death("혈마", death_arc=5)
        assert tracker.npc_registry["혈마"]["death_context"] == ""


# ══════════════════════════════════════════════════════════════
# Test 2: _is_standalone_name
# ══════════════════════════════════════════════════════════════


class TestIsStandaloneName:
    def test_standalone_match(self, tracker):
        """독립 이름 매칭 성공"""
        assert tracker._is_standalone_name("강철", "강철이 검을 들었다") is True

    def test_prefix_attached_false(self, tracker):
        """앞에 한글이 붙으면 오탐으로 판정"""
        assert tracker._is_standalone_name("강철", "냉강철의 검법") is False

    def test_suffix_attached_false(self, tracker):
        """뒤에 일반 한글(비조사)이 붙으면 오탐"""
        assert tracker._is_standalone_name("강철", "강철무의 검법") is False

    def test_particle_allowed(self, tracker):
        """뒤에 조사(은/는/이/가 등)가 오면 허용"""
        assert tracker._is_standalone_name("강철", "강철은 강했다") is True
        assert tracker._is_standalone_name("강철", "강철이 나섰다") is True
        assert tracker._is_standalone_name("강철", "강철을 만났다") is True

    def test_name_not_in_text(self, tracker):
        """텍스트에 이름이 없으면 False"""
        assert tracker._is_standalone_name("강철", "검은 바람이 불었다") is False


# ══════════════════════════════════════════════════════════════
# Test 3: merge_npc_registry (dead NPC protection)
# ══════════════════════════════════════════════════════════════


class TestMergeNpcRegistry:
    def test_merge_new_npcs(self, tracker):
        """새 NPC가 정상적으로 병합"""
        other = StateTracker()
        other.npc_registry["검성"] = {"status": "alive", "role": "고수"}

        tracker.merge_npc_registry(other)
        assert "검성" in tracker.npc_registry
        assert tracker.npc_registry["검성"]["status"] == "alive"

    def test_dead_npc_protection(self, tracker_with_dead_npc):
        """사망한 NPC를 비사망 업데이트로 덮어쓸 수 없음"""
        other = StateTracker()
        other.npc_registry["철무련주"] = {"status": "alive", "role": "무림맹주"}

        tracker_with_dead_npc.merge_npc_registry(other)
        # 사망 상태 보존
        assert tracker_with_dead_npc.npc_registry["철무련주"]["status"] == "dead"
        assert tracker_with_dead_npc.npc_registry["철무련주"]["death_arc"] == 3

    def test_dead_overrides_alive(self, tracker):
        """다른 tracker에서 사망 정보가 오면 기존 alive를 dead로 갱신"""
        tracker.register_npc_info("검성", arc_no=1)

        other = StateTracker()
        other.register_npc_death("검성", death_arc=4, death_context="결투 패배")

        tracker.merge_npc_registry(other)
        assert tracker.npc_registry["검성"]["status"] == "dead"
        assert tracker.npc_registry["검성"]["death_arc"] == 4

    def test_merge_skills(self, tracker):
        """무공 목록도 병합"""
        tracker.protagonist_skills.add("태극검법")
        other = StateTracker()
        other.protagonist_skills.add("파천검법")
        other.skill_acquisitions["파천검법"] = 5

        tracker.merge_npc_registry(other)
        assert "파천검법" in tracker.protagonist_skills
        assert tracker.skill_acquisitions["파천검법"] == 5


# ══════════════════════════════════════════════════════════════
# Test 4: extract_resolved_plots_from_arc
# ══════════════════════════════════════════════════════════════


class TestExtractResolvedPlots:
    def test_basic_extraction(self, tracker):
        """state_changes.resolved_plots에서 정상 추출"""
        arc = {
            "arc_no": 5,
            "state_changes": {
                "resolved_plots": [{"plot": "철무련주와의 복수극", "resolution": "결투 승리", "episode": 25}]
            },
        }
        plots = tracker.extract_resolved_plots_from_arc(arc)

        assert len(plots) == 1
        assert plots[0]["plot"] == "철무련주와의 복수극"
        assert plots[0]["arc_no"] == 5
        # 누적 목록에도 추가
        assert len(tracker.resolved_plots) == 1

    def test_empty_state_changes(self, tracker):
        """state_changes가 없으면 빈 목록"""
        arc = {"arc_no": 3}
        plots = tracker.extract_resolved_plots_from_arc(arc)
        assert plots == []

    def test_dedup_same_arc(self, tracker):
        """같은 arc_no+plot 조합은 중복 누적 안 함"""
        arc = {
            "arc_no": 5,
            "state_changes": {"resolved_plots": [{"plot": "복수극", "resolution": "승리", "episode": 25}]},
        }
        tracker.extract_resolved_plots_from_arc(arc)
        tracker.extract_resolved_plots_from_arc(arc)
        assert len(tracker.resolved_plots) == 1


# ══════════════════════════════════════════════════════════════
# Test 5: register_entity_name (LRU, max 200)
# ══════════════════════════════════════════════════════════════


class TestRegisterEntityName:
    def test_basic_registration(self, tracker):
        """엔티티 등록 기본 동작"""
        tracker.register_entity_name("무림맹", "organization", arc_no=1)

        assert "무림맹" in tracker.entity_name_registry
        info = tracker.entity_name_registry["무림맹"]
        assert info["type"] == "organization"
        assert info["first_arc"] == 1

    def test_lru_eviction(self, tracker):
        """200개 초과 시 가장 오래된 항목 삭제"""
        tracker._entity_registry_max_size = 5  # 테스트용 축소

        for i in range(7):
            tracker.register_entity_name(f"조직_{i:03d}", "organization", arc_no=i)

        assert len(tracker.entity_name_registry) == 5
        # 가장 처음 등록된 0, 1이 삭제되어야 함
        assert "조직_000" not in tracker.entity_name_registry
        assert "조직_001" not in tracker.entity_name_registry
        assert "조직_006" in tracker.entity_name_registry

    def test_lru_access_refreshes(self, tracker):
        """기존 엔티티 재등록 시 LRU 갱신 (move_to_end)"""
        tracker._entity_registry_max_size = 3

        tracker.register_entity_name("무림맹", "organization", arc_no=1)
        tracker.register_entity_name("마교", "organization", arc_no=2)
        tracker.register_entity_name("사천당가", "organization", arc_no=3)

        # 무림맹을 다시 접근 → LRU 갱신
        tracker.register_entity_name("무림맹", "organization", arc_no=4)

        # 새 항목 추가 → 마교가 eviction 대상
        tracker.register_entity_name("개방", "organization", arc_no=5)
        assert "무림맹" in tracker.entity_name_registry
        assert "마교" not in tracker.entity_name_registry  # LRU eviction

    def test_short_name_ignored(self, tracker):
        """1글자 이름은 등록 안 됨"""
        tracker.register_entity_name("맹", "organization", arc_no=1)
        assert "맹" not in tracker.entity_name_registry


# ══════════════════════════════════════════════════════════════
# Test 6: check_entity_name_consistency
# ══════════════════════════════════════════════════════════════


class TestCheckEntityNameConsistency:
    def test_exact_match_no_warning(self, tracker):
        """정확한 이름이 사용되면 경고 없음"""
        tracker.register_entity_name("무림맹주", "organization", arc_no=1)
        warnings = tracker.check_entity_name_consistency("무림맹주가 나섰다", arc_no=2)
        assert len(warnings) == 0

    def test_variant_name_warning(self, tracker):
        """유사하지만 다른 이름이 있으면 WARNING"""
        tracker.register_entity_name("천룡문파", "organization", arc_no=1)
        # "천룡문파"와 접두어 "천룡문"이 같지만 "천룡문회"는 다른 이름
        warnings = tracker.check_entity_name_consistency("천룡문회에서 회의가 열렸다", arc_no=2)
        # 접두어 60% = 2글자 이상이므로 "천룡" 접두어 매칭 여부에 따라 다름
        # 3자 이상 엔티티만 체크하므로 통과
        # 실제 로직: prefix_len = max(2, int(4 * 0.6)) = max(2, 2) = 2 → "천룡"
        # regex: r"천룡[가-힣]{1,4}" → "천룡문회" 매칭
        # |4 - 4| <= 2 → True → WARNING
        assert any(w["entity"] == "천룡문파" for w in warnings)

    def test_empty_content_no_warning(self, tracker):
        """빈 콘텐츠면 경고 없음"""
        tracker.register_entity_name("무림맹주", "organization", arc_no=1)
        warnings = tracker.check_entity_name_consistency("", arc_no=2)
        assert len(warnings) == 0


# ══════════════════════════════════════════════════════════════
# Test 7: export/import_financial_registry
# ══════════════════════════════════════════════════════════════


class TestFinancialRegistry:
    def test_export_int_to_str_keys(self, tracker):
        """export: int 키 → str 키"""
        tracker.financial_number_registry[1] = {"total_assets": [1000000]}
        tracker.financial_number_registry[3] = {"total_assets": [5000000]}

        exported = tracker.export_financial_registry()
        assert "1" in exported
        assert "3" in exported
        assert 1 not in exported  # int 키 없어야 함

    def test_import_str_to_int_keys(self, tracker):
        """import: str 키 → int 키"""
        data = {"2": {"total_assets": [2000000]}, "5": {"exchange_rates": [1100]}}
        tracker.import_financial_registry(data)

        assert 2 in tracker.financial_number_registry
        assert 5 in tracker.financial_number_registry
        assert tracker.financial_number_registry[2]["total_assets"] == [2000000]

    def test_import_empty_data(self, tracker):
        """빈 데이터 import 시 아무 일도 안 함"""
        tracker.import_financial_registry(None)
        tracker.import_financial_registry({})
        assert len(tracker.financial_number_registry) == 0

    def test_roundtrip(self, tracker):
        """export → import 라운드트립"""
        tracker.financial_number_registry[7] = {
            "total_assets": [100],
            "key_transactions": [{"type": "buy", "target": "삼성", "amount": "50억"}],
        }
        exported = tracker.export_financial_registry()

        tracker2 = StateTracker()
        tracker2.import_financial_registry(exported)
        assert tracker2.financial_number_registry[7]["total_assets"] == [100]
        assert len(tracker2.financial_number_registry[7]["key_transactions"]) == 1


# ══════════════════════════════════════════════════════════════
# Test 8: check_dead_npc_in_manuscript
# ══════════════════════════════════════════════════════════════


class TestCheckDeadNpcInManuscript:
    def test_dead_npc_action_detected(self, tracker_with_dead_npc):
        """사망 NPC가 행동하면 CRITICAL 위반"""
        manuscript = "철무련주가 검을 들고 나섰다. 그의 눈빛은 차가웠다."
        violations = tracker_with_dead_npc.check_dead_npc_in_manuscript(manuscript, ep_num=20, arc_no=6)
        assert len(violations) >= 1
        assert any(v["npc_name"] == "철무련주" for v in violations)

    def test_flashback_allowed(self, tracker_with_dead_npc):
        """회상/추모 맥락은 허용"""
        manuscript = "그는 철무련주의 죽음을 떠올렸다. 가슴이 아팠다."
        violations = tracker_with_dead_npc.check_dead_npc_in_manuscript(manuscript, ep_num=20, arc_no=6)
        # 회상 패턴에 해당하므로 위반 아님
        assert not any(v["npc_name"] == "철무련주" for v in violations)

    def test_pre_death_arc_skipped(self, tracker_with_dead_npc):
        """사망 이전 Arc에서는 검사 스킵"""
        manuscript = "철무련주가 수련을 시작했다."
        violations = tracker_with_dead_npc.check_dead_npc_in_manuscript(
            manuscript,
            ep_num=5,
            arc_no=2,  # 사망 arc=3 이전
        )
        assert len(violations) == 0

    def test_empty_manuscript(self, tracker_with_dead_npc):
        """빈 원고는 위반 없음"""
        violations = tracker_with_dead_npc.check_dead_npc_in_manuscript("", ep_num=20, arc_no=6)
        assert violations == []

    def test_none_manuscript(self, tracker_with_dead_npc):
        """None 원고는 위반 없음"""
        violations = tracker_with_dead_npc.check_dead_npc_in_manuscript(None, ep_num=20, arc_no=6)
        assert violations == []


class TestFullExtractFromArcs:
    """B-1/B-2: full_extract_from_arcs가 17개 메서드를 일관 호출하는지 검증."""

    def test_calls_all_17_extract_methods(self):
        """17개 extract 메서드가 모두 호출되는지 확인."""
        from unittest.mock import MagicMock

        tracker = MagicMock(spec=StateTracker)
        arcs = [{"arc_number": 1, "content": {}}]

        StateTracker.full_extract_from_arcs(tracker, arcs, genre="wuxia")

        tracker.extract_npc_deaths_from_arc.assert_called_once()
        tracker.extract_skill_acquisitions_from_arc.assert_called_once()
        tracker.extract_npc_info_from_arc.assert_called_once()
        tracker.extract_resolved_plots_from_arc.assert_called_once()
        tracker.extract_time_markers_from_arc.assert_called_once()
        tracker.extract_permanent_injuries_from_arc.assert_called_once()
        tracker.update_companions_from_arc.assert_called_once()
        tracker.extract_commitments_from_arc.assert_called_once()
        tracker.extract_protagonist_emotion_from_arc.assert_called_once()
        tracker.extract_item_states_from_arc.assert_called_once()
        tracker.extract_entity_destructions_from_arc.assert_called_once()
        tracker.extract_npc_personality_from_arc.assert_called_once()
        tracker.extract_npc_npc_relationships_from_arc.assert_called_once()
        tracker.extract_npc_dialogue_styles_from_arc.assert_called_once()
        tracker.extract_relationship_changes_from_arc.assert_called_once()
        tracker.extract_npc_injuries_from_arc.assert_called_once()
        tracker.extract_npc_movements_from_arc.assert_called_once()

    def test_financial_extract_only_for_investment_genre(self):
        """투자물 장르에서만 금융 이벤트 추출 호출."""
        from unittest.mock import MagicMock

        tracker = MagicMock(spec=StateTracker)
        arcs = [{"arc_number": 1}]

        StateTracker.full_extract_from_arcs(tracker, arcs, genre="wuxia")
        tracker.extract_financial_events_from_arc.assert_not_called()

        tracker.reset_mock()
        StateTracker.full_extract_from_arcs(tracker, arcs, genre="investment")
        tracker.extract_financial_events_from_arc.assert_called_once()

    def test_optional_extract_exception_does_not_propagate(self):
        """확장 extract 예외가 비전파되고 필수 4종 호출은 유지."""
        from unittest.mock import MagicMock

        tracker = MagicMock(spec=StateTracker)
        tracker.extract_time_markers_from_arc.side_effect = ValueError("test")
        tracker.extract_permanent_injuries_from_arc.side_effect = KeyError("test")
        tracker.extract_npc_personality_from_arc.side_effect = TypeError("test")

        StateTracker.full_extract_from_arcs(tracker, [{"arc_number": 1}])

        tracker.extract_npc_deaths_from_arc.assert_called_once()
        tracker.extract_skill_acquisitions_from_arc.assert_called_once()
        tracker.extract_npc_info_from_arc.assert_called_once()
        tracker.extract_resolved_plots_from_arc.assert_called_once()


# ══════════════════════════════════════════════════════════════
# [Sweep4] create_tracker_from_arcs — cross-arc boundary transition
# ══════════════════════════════════════════════════════════════
class TestCreateTrackerFromArcs:
    """create_tracker_from_arcs cross-arc transition 재구축 테스트"""

    def test_cross_arc_boundary_transition_exists(self):
        """[Sweep4] 2-arc 데이터 투입 → EP5→EP6 경계 transition 존재 확인"""
        from modules.domain.agents.state_tracker import create_tracker_from_arcs

        arc1 = {
            "arc_no": 1,
            "state_constraints": {
                "arc_start_state": {"location": "산동성", "equipment": ["철검"]},
                "arc_end_state": {"location": "화산파"},
                "continuity_checkpoints": [],
            },
            "episode_breakdown": {},
        }
        arc2 = {
            "arc_no": 2,
            "state_constraints": {
                "arc_start_state": {"location": "화산파", "equipment": ["화산검"]},
                "arc_end_state": {"location": "소림사"},
                "continuity_checkpoints": [],
            },
            "episode_breakdown": {},
        }

        tracker = create_tracker_from_arcs([arc1, arc2])

        # states에 arc1 시작(ep1)과 arc2 시작(ep6)이 모두 존재해야 함
        assert 1 in tracker.states, "Arc1 시작 EP1이 states에 없음"
        assert 6 in tracker.states, "Arc2 시작 EP6이 states에 없음"

        # cross-arc boundary transition (ep5→ep6 또는 ep1→ep6) 존재 확인
        boundary_transitions = [t for t in tracker.transitions if t.from_ep < 6 and t.to_ep >= 6]
        assert len(boundary_transitions) > 0, (
            f"Cross-arc boundary transition이 없음. transitions: {[(t.from_ep, t.to_ep) for t in tracker.transitions]}"
        )

    def test_empty_arcs_no_crash(self):
        """빈 arc 데이터에서 크래시 없음"""
        from modules.domain.agents.state_tracker import create_tracker_from_arcs

        tracker = create_tracker_from_arcs([])
        assert len(tracker.transitions) == 0
        assert len(tracker.states) == 0
