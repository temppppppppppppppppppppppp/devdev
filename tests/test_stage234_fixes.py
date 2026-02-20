"""Stage 2/3/4 이슈 수정 테스트 (8건)"""

import inspect
import re

import pytest

from modules.core.constants import VolumeSettings


# ──────────────────────────────────────────────
# T1: stage2_orchestrator input() EOFError 처리
# ──────────────────────────────────────────────
class TestT1InputHandling:
    def test_stage2_input_eof_handling(self):
        """stage2_orchestrator의 input() 호출부에 EOFError 처리 존재"""
        from modules.core.stage2_orchestrator import Stage2Orchestrator

        src = inspect.getsource(Stage2Orchestrator.stage_2_arcs_async_logic)
        # input() 호출 근처에 EOFError 가 있어야 함
        assert "EOFError" in src, "stage_2_arcs_async_logic에 EOFError 처리 누락"

    def test_stage2_no_bare_print(self):
        """stage2_orchestrator 메뉴 블록에 bare print() 미존재"""
        from modules.core.stage2_orchestrator import Stage2Orchestrator

        src = inspect.getsource(Stage2Orchestrator.stage_2_arcs_async_logic)
        lines = src.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("print("):
                pytest.fail(f"stage_2_arcs_async_logic L{i}: bare print() 발견: {stripped[:80]}")


# ──────────────────────────────────────────────
# T2: ep_count 매직넘버 상수화
# ──────────────────────────────────────────────
class TestT2EpCount:
    def test_stage2_ep_count_no_magic_five(self):
        """stage2_orchestrator skip 로직에 하드코딩 5 미존재 (VolumeSettings 상수 사용)"""
        from modules.core.stage2_orchestrator import Stage2Orchestrator

        src = inspect.getsource(Stage2Orchestrator.stage_2_arcs_async_logic)
        # "ep_count", 5) 패턴이나 else 5 패턴 검사
        # ep_count 기본값으로 리터럴 5가 사용되면 안 됨
        matches = re.findall(r'get\("ep_count",\s*5\)', src)
        assert len(matches) == 0, f"ep_count 폴백에 하드코딩 5 잔존 ({len(matches)}곳)"

    def test_default_ep_count_uses_volume_settings(self):
        """DEFAULT_EP_COUNT가 VolumeSettings.EPISODES_PER_ARC와 동일"""
        from modules.core.stage2_orchestrator import DEFAULT_EP_COUNT

        assert DEFAULT_EP_COUNT == VolumeSettings.EPISODES_PER_ARC


# ──────────────────────────────────────────────
# T3: genre 폴백 상수화
# ──────────────────────────────────────────────
class TestT3GenreConstant:
    def test_arc_ensemble_genre_uses_constant(self):
        """arc_ensemble 소스에 GenreTypes 참조 확인"""
        from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator

        src = inspect.getsource(ArcEnsembleGenerator.generate_ensemble)
        assert "GenreTypes.WUXIA" in src, "arc_ensemble.generate_ensemble에 GenreTypes.WUXIA 참조 누락"
        assert '"wuxia"' not in src, 'arc_ensemble.generate_ensemble에 하드코딩 "wuxia" 잔존'

    def test_blueprint_ensemble_genre_uses_constant(self):
        """blueprint_ensemble 소스에 GenreTypes 참조 확인"""
        from modules.domain.agents.blueprint_ensemble import BlueprintEnsembleGenerator

        src = inspect.getsource(BlueprintEnsembleGenerator.generate_ensemble)
        assert "GenreTypes.WUXIA" in src, "blueprint_ensemble.generate_ensemble에 GenreTypes.WUXIA 참조 누락"
        assert '"wuxia"' not in src, 'blueprint_ensemble.generate_ensemble에 하드코딩 "wuxia" 잔존'


# ──────────────────────────────────────────────
# T4: kwargs 헬퍼 추출
# ──────────────────────────────────────────────
class TestT4KwargsHelper:
    def test_stage4_interview_uses_common_kwargs(self):
        """stage4_interview_round.run() 에서 _common_writer_kwargs 사용"""
        from modules.core.stage4_interview_round import Stage4InterviewRound

        src = inspect.getsource(Stage4InterviewRound.run)
        assert "_common_writer_kwargs" in src, "run()에 _common_writer_kwargs 미사용"
        # **_common_writer_kwargs 언팩이 최소 3회 사용되어야 함
        unpack_count = src.count("**_common_writer_kwargs")
        assert unpack_count >= 3, f"_common_writer_kwargs 언팩이 {unpack_count}회만 사용 (최소 3회 필요)"


# ──────────────────────────────────────────────
# T5: state_changes 헬퍼 추출
# ──────────────────────────────────────────────
class TestT5StateChangeHelper:
    def test_stage4_post_processor_has_state_change_helper(self):
        """_extract_state_change_info 메서드 존재"""
        from modules.core.stage4_post_processor import Stage4PostProcessor

        assert hasattr(Stage4PostProcessor, "_extract_state_change_info")
        assert callable(getattr(Stage4PostProcessor, "_extract_state_change_info"))

    def test_state_change_helper_returns_expected_keys(self):
        """헬퍼 반환값에 3개 키 포함 (event_types, entity_names, summary_parts)"""
        from modules.core.stage4_post_processor import Stage4PostProcessor

        sample = {
            "npc_deaths": [{"name": "장풍"}, "독고진"],
            "skill_acquisitions": [{"name": "파천신공"}],
            "relationship_changes": [{"npc": "한설", "change": "적대→우호"}],
            "major_items": [{"name": "천잠검"}],
            "npc_injuries": [{"name": "무영"}],
            "resolved_plots": ["복수극"],
        }
        result = Stage4PostProcessor._extract_state_change_info(sample)
        assert "event_types" in result
        assert "entity_names" in result
        assert "summary_parts" in result
        # event_types 검증
        assert "death" in result["event_types"]
        assert "skill" in result["event_types"]
        assert "relationship" in result["event_types"]
        assert "item" in result["event_types"]
        assert "injury" in result["event_types"]
        assert "resolved_plot" in result["event_types"]
        # entity_names 검증
        assert "장풍" in result["entity_names"]
        assert "독고진" in result["entity_names"]
        assert "파천신공" in result["entity_names"]
        assert "한설" in result["entity_names"]
        assert "천잠검" in result["entity_names"]
        # summary_parts 검증
        assert len(result["summary_parts"]) >= 3  # 사망, 관계, 아이템, 해결
