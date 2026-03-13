"""
[V64 P2-7] PromptBuilder Unit Tests

Pure 메서드(Writer 가이드) 및 App-dependent 메서드 테스트.
generate_arc_position_guide, generate_high_impact_zone_guide,
generate_npc_relationship_justification, generate_item_acquisition_timeline,
generate_temporal_spatial_guide, generate_cliche_avoidance_guide,
generate_self_diagnosis_checklist, generate_writer_guidance_v60_8,
generate_arc_context_fallback, build_item_acquisition_timeline 캐시 로직.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.prompt_builder import GRANT_PATTERNS_COMPILED, PromptBuilder

# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def builder():
    """앱 참조 없는 Pure PromptBuilder"""
    return PromptBuilder(app=None)


@pytest.fixture
def builder_with_mock_app():
    """Mock app이 있는 PromptBuilder"""
    mock_app = MagicMock()
    mock_app.ui = MagicMock()
    mock_app.ui.log = MagicMock()
    mock_app._audit_event = MagicMock()
    mock_app._cumulative_state_cache = None
    mock_app._cumulative_state_cache_key = None
    mock_app.agents = {}

    # Mock DB for build_item_acquisition_timeline
    mock_db = MagicMock()
    mock_db.get_episode_bible = MagicMock(return_value=None)
    mock_app.current_project = MagicMock()
    mock_app.current_project.db = mock_db

    return PromptBuilder(app=mock_app)


@pytest.fixture
def sample_blueprint_6scenes():
    """6개 씬이 있는 블루프린트"""
    return {
        "ep_num": 5,
        "title": "결전",
        "scene_breakdown": {
            "scene_1": {"title": "도입", "content": "..."},
            "scene_2": {"title": "전개1", "content": "..."},
            "scene_3": {"title": "전개2", "content": "..."},
            "scene_4": {"title": "위기", "content": "..."},
            "scene_5": {"title": "클라이맥스", "content": "..."},
            "scene_6": {"title": "결말", "content": "..."},
        },
        "relationship_changes": [
            {"target": "철무련주", "from": "적대", "to": "경외"},
        ],
    }


# ══════════════════════════════════════════════════════════════
# Test 1: generate_arc_position_guide
# ══════════════════════════════════════════════════════════════


class TestGenerateArcPositionGuide:
    def test_first_episode(self, builder):
        """아크 제1화 도입부 가이드"""
        result = builder.generate_arc_position_guide(arc_pos=1, total_eps=5)
        assert "도입부" in result
        assert "제1화" in result

    def test_mid_episode(self, builder):
        """아크 중반부 가이드 (전개부)"""
        result = builder.generate_arc_position_guide(arc_pos=2, total_eps=6)
        assert "전개부" in result

    def test_rising_episode(self, builder):
        """아크 상승부 가이드 (40-70%)"""
        result = builder.generate_arc_position_guide(arc_pos=3, total_eps=5)
        assert "상승부" in result

    def test_last_episode(self, builder):
        """아크 마지막 화 가이드"""
        result = builder.generate_arc_position_guide(arc_pos=5, total_eps=5)
        assert "마지막" in result or "절정" in result

    def test_climax_before_last(self, builder):
        """아크 절정부 가이드 (마지막 화 직전)"""
        result = builder.generate_arc_position_guide(arc_pos=4, total_eps=5)
        assert "절정부" in result

    def test_zero_total_eps(self, builder):
        """total_eps가 0이면 빈 문자열"""
        result = builder.generate_arc_position_guide(arc_pos=1, total_eps=0)
        assert result == ""

    def test_negative_total_eps(self, builder):
        """total_eps가 음수이면 빈 문자열"""
        result = builder.generate_arc_position_guide(arc_pos=1, total_eps=-3)
        assert result == ""


# ══════════════════════════════════════════════════════════════
# Test 2: generate_high_impact_zone_guide
# ══════════════════════════════════════════════════════════════


class TestGenerateHighImpactZoneGuide:
    def test_basic_generation(self, builder, sample_blueprint_6scenes):
        """6개 씬에 대한 분량 가이드 생성"""
        result = builder.generate_high_impact_zone_guide(sample_blueprint_6scenes, target_len=5000)
        assert "High Impact Zone" in result
        assert "전반부" in result
        assert "후반부" in result

    def test_less_than_4_scenes_returns_empty(self, builder):
        """4개 미만 씬이면 빈 문자열"""
        bp = {"scene_breakdown": {"s1": {}, "s2": {}, "s3": {}}}
        result = builder.generate_high_impact_zone_guide(bp)
        assert result == ""

    def test_empty_blueprint(self, builder):
        """빈 블루프린트이면 빈 문자열"""
        assert builder.generate_high_impact_zone_guide({}) == ""
        assert builder.generate_high_impact_zone_guide(None) == ""

    def test_no_scene_breakdown(self, builder):
        """scene_breakdown 없으면 빈 문자열"""
        result = builder.generate_high_impact_zone_guide({"title": "test"})
        assert result == ""


# ══════════════════════════════════════════════════════════════
# Test 3: generate_npc_relationship_justification
# ══════════════════════════════════════════════════════════════


class TestGenerateNpcRelationshipJustification:
    def test_large_jump_generates_guide(self, builder):
        """2단계 이상 관계 점프 시 가이드 생성"""
        bp = {"relationship_changes": [{"target": "철무련주", "from": "멸시", "to": "경외"}]}
        result = builder.generate_npc_relationship_justification(bp)
        assert "철무련주" in result
        assert "급격한 전환" in result or "단계 점프" in result

    def test_small_jump_no_guide(self, builder):
        """1단계 변화는 가이드 미생성"""
        bp = {"relationship_changes": [{"target": "노사부", "from": "중립", "to": "호기심"}]}
        result = builder.generate_npc_relationship_justification(bp)
        assert result == ""

    def test_no_relationship_changes(self, builder):
        """관계 변화 없으면 빈 문자열"""
        assert builder.generate_npc_relationship_justification({"relationship_changes": []}) == ""
        assert builder.generate_npc_relationship_justification({}) == ""

    def test_none_blueprint(self, builder):
        """None 블루프린트"""
        assert builder.generate_npc_relationship_justification(None) == ""

    def test_non_dict_change_skipped(self, builder):
        """관계 변화 항목이 dict 아니면 스킵"""
        bp = {"relationship_changes": ["invalid_string"]}
        result = builder.generate_npc_relationship_justification(bp)
        assert result == ""


# ══════════════════════════════════════════════════════════════
# Test 4: generate_item_acquisition_timeline
# ══════════════════════════════════════════════════════════════


class TestGenerateItemAcquisitionTimeline:
    def test_with_inventory(self, builder):
        """현재 인벤토리가 있으면 타임라인 생성"""
        bp = {"protagonist_state": {"inventory": ["청풍검", "경공화"], "skills": ["청풍검법"]}}
        result = builder.generate_item_acquisition_timeline(bp)
        assert "청풍검" in result
        assert "청풍검법" in result

    def test_empty_inventory(self, builder):
        """인벤토리와 스킬 모두 비어있으면 빈 문자열"""
        bp = {"protagonist_state": {"inventory": [], "skills": []}}
        result = builder.generate_item_acquisition_timeline(bp)
        assert result == ""

    def test_with_episode_bibles(self, builder):
        """에피소드 바이블에서 획득 시점 추출"""
        bp = {"protagonist_state": {"inventory": ["청풍검"], "skills": []}}
        bibles = [{"ep_num": 3, "new_items": [{"name": "청풍검"}]}]
        result = builder.generate_item_acquisition_timeline(bp, episode_bibles=bibles)
        assert "제3화" in result

    def test_no_blueprint(self, builder):
        """블루프린트 없으면 빈 문자열"""
        result = builder.generate_item_acquisition_timeline(None)
        assert result == ""


# ══════════════════════════════════════════════════════════════
# Test 5: generate_temporal_spatial_guide
# ══════════════════════════════════════════════════════════════


class TestGenerateTemporalSpatialGuide:
    def test_with_prev_manuscript(self, builder):
        """이전 원고에서 시간/장소 추출"""
        bp = {"time_flow": "다음 날 아침", "start_location": "객잔"}
        prev = "그날 밤 객잔에서 모든 일이 끝났다."
        result = builder.generate_temporal_spatial_guide(bp, prev)
        assert "시간/공간 연속성" in result
        assert "객잔" in result

    def test_empty_everything(self, builder):
        """모든 입력이 비어있으면 빈 문자열"""
        result = builder.generate_temporal_spatial_guide({}, "")
        assert result == ""

    def test_with_blueprint_only(self, builder):
        """블루프린트만 있어도 가이드 생성"""
        bp = {"time_flow": "다음 날", "start_location": "무림맹 본부"}
        result = builder.generate_temporal_spatial_guide(bp)
        assert "무림맹 본부" in result


# ══════════════════════════════════════════════════════════════
# Test 6: generate_cliche_avoidance_guide
# ══════════════════════════════════════════════════════════════


class TestGenerateClicheAvoidanceGuide:
    def test_always_generates(self, builder):
        """클리셰 가이드는 항상 생성"""
        result = builder.generate_cliche_avoidance_guide()
        assert "클리셰" in result
        assert "눈이 번쩍" in result or "심장이 멎" in result

    def test_contains_alternatives(self, builder):
        """대안 표현이 포함"""
        result = builder.generate_cliche_avoidance_guide()
        assert "→" in result


# ══════════════════════════════════════════════════════════════
# Test 7: generate_self_diagnosis_checklist
# ══════════════════════════════════════════════════════════════


class TestGenerateSelfDiagnosisChecklist:
    def test_basic_checklist(self, builder):
        """기본 체크리스트 생성"""
        result = builder.generate_self_diagnosis_checklist({})
        assert "자가 진단" in result
        assert "4,500자" in result or "4,000자" in result

    def test_with_scene_count(self, builder, sample_blueprint_6scenes):
        """씬 개수 반영"""
        result = builder.generate_self_diagnosis_checklist(sample_blueprint_6scenes)
        assert "6개" in result


# ══════════════════════════════════════════════════════════════
# Test 8: generate_writer_guidance_v60_8 (통합)
# ══════════════════════════════════════════════════════════════


class TestGenerateWriterGuidanceV608:
    def test_combines_multiple_guides(self, builder, sample_blueprint_6scenes):
        """여러 가이드를 통합 생성"""
        result = builder.generate_writer_guidance_v60_8(
            blueprint=sample_blueprint_6scenes, prev_manuscript="그날 밤 객잔에서 일이 있었다.", target_len=5000
        )
        # 최소한 클리셰 가이드는 항상 포함
        assert len(result) > 0

    def test_empty_blueprint_minimal(self, builder):
        """빈 블루프린트이면 최소 가이드만"""
        result = builder.generate_writer_guidance_v60_8(blueprint={})
        # 클리셰 가이드는 항상 생성
        assert "클리셰" in result or result == ""


# ══════════════════════════════════════════════════════════════
# Test 9: generate_arc_context_fallback
# ══════════════════════════════════════════════════════════════


class TestGenerateArcContextFallback:
    def test_basic_fallback(self, builder):
        """기본 폴백 컨텍스트 생성"""
        arcs = [
            {
                "arc_no": 3,
                "tactical_doc": "무림맹 습격 계획...",
                "joint_docs": {
                    "final_location": "무림맹 본부",
                    "physical_inventory": ["청풍검", "해독약"],
                    "world_joint": "무림맹 세력 약화",
                },
                "status_shadow": {
                    "internal_energy_loss": "30%",
                    "item_consumption": "해독약 1개",
                    "expected_injuries": "왼팔 부상",
                },
                "state_constraints": {
                    "arc_end_state": {
                        "internal_energy": 70,
                        "injuries": "왼팔 부상",
                        "location": "무림맹 본부",
                        "equipment": "청풍검",
                    },
                    "items_acquired": ["용린검"],
                },
            }
        ]
        result = builder.generate_arc_context_fallback(arcs)
        assert "아크 3" in result or "Arc 3" in result.lower() or "arc_no" in result.lower() or "직전 아크 3" in result
        assert "무림맹 본부" in result
        assert "70%" in result
        assert "왼팔 부상" in result

    def test_energy_history_tracking(self, builder):
        """내공 소모 이력 추적"""
        arcs = [
            {
                "arc_no": 1,
                "tactical_doc": "",
                "joint_docs": {},
                "status_shadow": {"internal_energy_loss": "20%"},
                "state_constraints": {"arc_end_state": {}},
            },
            {
                "arc_no": 2,
                "tactical_doc": "",
                "joint_docs": {},
                "status_shadow": {"internal_energy_loss": "30%"},
                "state_constraints": {"arc_end_state": {}},
            },
        ]
        result = builder.generate_arc_context_fallback(arcs)
        # 내공 소모 이력이 포함되어야 함
        assert "Arc1: -20%" in result or "소모" in result

    def test_grant_patterns_detection(self, builder):
        """수여물 패턴 감지"""
        arcs = [
            {
                "arc_no": 1,
                "tactical_doc": "무림맹 금패를 하사받았다.",
                "joint_docs": {},
                "status_shadow": {},
                "state_constraints": {"arc_end_state": {}},
            }
        ]
        result = builder.generate_arc_context_fallback(arcs)
        # 수여 패턴이 감지되어야 함
        assert "금패" in result or "수여" in result


# ══════════════════════════════════════════════════════════════
# Test 10: build_item_acquisition_timeline (캐시)
# ══════════════════════════════════════════════════════════════


class TestBuildItemAcquisitionTimeline:
    def test_zero_ep_returns_empty(self, builder_with_mock_app):
        """ep <= 0이면 빈 문자열"""
        result = builder_with_mock_app.build_item_acquisition_timeline(0)
        assert result == ""

    def test_cache_hit(self, builder_with_mock_app):
        """같은 ep 재호출 시 캐시 사용"""
        # 첫 호출 - 캐시에 저장
        builder_with_mock_app.build_item_acquisition_timeline(3)
        # 두 번째 호출 - 캐시에서 반환
        builder_with_mock_app.build_item_acquisition_timeline(3)
        # DB 호출은 첫 번째에만 발생해야 함
        db = builder_with_mock_app._app.current_project.db
        # ep 1, 2, 3에 대해 한 번씩만 호출
        assert db.get_episode_bible.call_count == 3

    def test_incremental_cache(self, builder_with_mock_app):
        """증분 캐시: ep 3까지 조회 후 ep 5 조회 시 4,5만 추가 조회"""
        db = builder_with_mock_app._app.current_project.db
        # 먼저 ep 3까지
        builder_with_mock_app.build_item_acquisition_timeline(3)
        assert db.get_episode_bible.call_count == 3

        # ep 5까지 - ep 4, 5만 추가
        builder_with_mock_app.build_item_acquisition_timeline(5)
        assert db.get_episode_bible.call_count == 5  # 3 + 2

    def test_with_items_in_bible(self, builder_with_mock_app):
        """에피소드 바이블에 아이템 있으면 타임라인 생성"""
        db = builder_with_mock_app._app.current_project.db
        db.get_episode_bible.side_effect = lambda ep: {"new_items": ["청풍검"]} if ep == 1 else None
        result = builder_with_mock_app.build_item_acquisition_timeline(3)
        assert "제1화" in result
        assert "청풍검" in result

    def test_lost_items_tracked(self, builder_with_mock_app):
        """분실 아이템도 타임라인에 포함"""
        db = builder_with_mock_app._app.current_project.db
        db.get_episode_bible.side_effect = lambda ep: {"lost_items": ["파천검"]} if ep == 2 else None
        result = builder_with_mock_app.build_item_acquisition_timeline(3)
        assert "파천검" in result
        assert "분실" in result or "파괴" in result


# ══════════════════════════════════════════════════════════════
# Test 11: GRANT_PATTERNS_COMPILED
# ══════════════════════════════════════════════════════════════


class TestGrantPatterns:
    def test_pattern_matches_grant(self):
        """수여 패턴이 한국어 텍스트에서 매칭"""
        text = "무림맹 금패를 하사받았다"
        matches_found = False
        for pattern, suffix in GRANT_PATTERNS_COMPILED:
            if pattern.search(text):
                matches_found = True
                break
        assert matches_found

    def test_pattern_matches_appointment(self):
        """직위 임명 패턴 매칭"""
        text = "총관직에 임명되었다"
        matches_found = False
        for pattern, suffix in GRANT_PATTERNS_COMPILED:
            if pattern.search(text):
                matches_found = True
                break
        assert matches_found


class TestAppNoneGuards:
    def test_extract_npc_profiles_with_none_app_returns_empty(self, builder):
        assert builder.extract_npc_profiles({"arc_no": 1}) == {}

    def test_get_character_traits_with_none_app_returns_empty(self, builder):
        assert builder.get_character_traits() == {}

    def test_generate_arc_context_v60_with_none_app_uses_fallback(self, builder):
        arcs = [
            {
                "arc_no": 1,
                "joint_docs": {},
                "status_shadow": {},
                "state_constraints": {"arc_end_state": {}},
            }
        ]
        result = builder.generate_arc_context_v60(arcs)
        assert isinstance(result, str)

    def test_build_item_acquisition_timeline_with_none_app_returns_empty(self, builder):
        result = builder.build_item_acquisition_timeline(1)
        assert result == ""


class TestGenerateArcContextV60Bound:
    def test_app_bound_path_uses_state_extractor_and_audit(self, builder_with_mock_app):
        state_extractor = MagicMock()
        state_extractor.extract_cumulative_state.return_value = {
            "inventory": {"current_items": ["청풍검"]},
        }
        state_extractor.generate_constraint_prompt.return_value = "constraint prompt"
        builder_with_mock_app._app.agents["state_extractor"] = state_extractor

        result = builder_with_mock_app.generate_arc_context_v60(
            [{"arc_no": 1, "joint_docs": {}, "status_shadow": {}, "state_constraints": {"arc_end_state": {}}}],
            current_arc_no=2,
        )

        assert result.startswith("[다음 Arc #2 설계 기준]")
        assert "constraint prompt" in result
        state_extractor.extract_cumulative_state.assert_called_once()
        builder_with_mock_app._app._audit_event.assert_called_once()
        audit_payload = builder_with_mock_app._app._audit_event.call_args.args[2]
        assert audit_payload["target_arc_no"] == 2

    def test_app_bound_path_uses_cache_on_repeat_call(self, builder_with_mock_app):
        state_extractor = MagicMock()
        state_extractor.extract_cumulative_state.return_value = {"inventory": {"current_items": []}}
        state_extractor.generate_constraint_prompt.return_value = "constraint prompt"
        builder_with_mock_app._app.agents["state_extractor"] = state_extractor
        arcs = [{"arc_no": 1, "joint_docs": {}, "status_shadow": {}, "state_constraints": {"arc_end_state": {}}}]

        builder_with_mock_app.generate_arc_context_v60(arcs, current_arc_no=2)
        builder_with_mock_app.generate_arc_context_v60(arcs, current_arc_no=3)

        state_extractor.extract_cumulative_state.assert_called_once()

    def test_current_arc_no_changes_output_even_on_fallback(self, builder_with_mock_app):
        arcs = [
            {
                "arc_no": 1,
                "joint_docs": {},
                "status_shadow": {"internal_energy_loss": "10%"},
                "state_constraints": {"arc_end_state": {}},
            }
        ]

        result_a = builder_with_mock_app.generate_arc_context_v60(arcs, current_arc_no=2)
        result_b = builder_with_mock_app.generate_arc_context_v60(arcs, current_arc_no=5)

        assert result_a != result_b
        assert result_a.startswith("[다음 Arc #2 설계 기준]")
        assert result_b.startswith("[다음 Arc #5 설계 기준]")
