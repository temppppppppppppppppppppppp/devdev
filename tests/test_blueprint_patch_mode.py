"""Tests for Blueprint patch mode (ThreePhaseBlueprintGenerator._patch_blueprint_with_feedback)."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.master_bible = {"MasterBible": {"protagonist_config": {"name": "테스트주인공"}}}
    return ctx


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def blueprint_generator(mock_context, mock_client):
    with patch("modules.domain.agents.three_phase_blueprint_generator.BlueprintConstraintCompiler"):
        with patch("modules.domain.agents.three_phase_blueprint_generator.BlueprintEnsembleGenerator"):
            with patch("modules.domain.agents.three_phase_blueprint_generator.UnifiedBlueprintValidator"):
                from modules.domain.agents.three_phase_blueprint_generator import ThreePhaseBlueprintGenerator

                gen = ThreePhaseBlueprintGenerator(mock_context, mock_client)
                return gen


@pytest.fixture
def sample_blueprint():
    return {
        "ep_num": 1,
        "scene_list": [
            {"scene_no": 1, "summary": "도입부"},
            {"scene_no": 2, "summary": "전개"},
            {"scene_no": 3, "summary": "절정"},
        ],
        "emotion_curve": "상승→정점→하락",
    }


@pytest.fixture
def sample_arc_data():
    return {
        "arc_no": 1,
        "tactical_doc": "테스트 전술서",
        "ep_start": 1,
        "ep_end": 5,
    }


class TestBlueprintPatchMode:
    def test_patch_success(self, blueprint_generator, sample_blueprint, sample_arc_data):
        """패치 모드 정상 동작 — ensemble이 유효한 blueprint를 반환."""
        patched = {**sample_blueprint, "emotion_curve": "수정됨"}

        blueprint_generator.ensemble.generate_ensemble.return_value = (patched, [patched])

        result, candidates = blueprint_generator._patch_blueprint_with_feedback(
            original_blueprint=sample_blueprint,
            director_feedback="감정 곡선 부자연스러움",
            attempt_number=2,
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={},
            protagonist_name="주인공",
        )

        assert result is not None
        assert len(candidates) == 1
        # enhanced_feedback에 패치 모드 표시 확인
        call_args = blueprint_generator.ensemble.generate_ensemble.call_args
        feedback = call_args.kwargs.get("feedback", "")
        assert "패치 모드" in feedback

    def test_patch_failure_returns_none(self, blueprint_generator, sample_blueprint, sample_arc_data):
        """패치 실패 시 (None, []) 반환."""
        blueprint_generator.ensemble.generate_ensemble.return_value = (None, [])

        result, candidates = blueprint_generator._patch_blueprint_with_feedback(
            original_blueprint=sample_blueprint,
            director_feedback="구조 오류",
            attempt_number=2,
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={},
        )

        assert result is None
        assert candidates == []

    def test_patch_exception_returns_none(self, blueprint_generator, sample_blueprint, sample_arc_data):
        """ensemble 예외 시 (None, []) 반환."""
        blueprint_generator.ensemble.generate_ensemble.side_effect = RuntimeError("LLM 오류")

        result, candidates = blueprint_generator._patch_blueprint_with_feedback(
            original_blueprint=sample_blueprint,
            director_feedback="수정 필요",
            attempt_number=2,
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={},
        )

        assert result is None
        assert candidates == []

    def test_yaml_load_failure_uses_inline_fallback(self, blueprint_generator, sample_blueprint, sample_arc_data):
        """YAML 로드 실패 시 인라인 폴백으로 패치 프롬프트 생성."""
        patched = {**sample_blueprint, "scene_list": [{"scene_no": 1, "summary": "수정됨"}]}
        blueprint_generator.ensemble.generate_ensemble.return_value = (patched, [patched])

        with patch("modules.core.prompt_loader.PromptLoader") as mock_loader_cls:
            mock_loader_cls.return_value.load.side_effect = FileNotFoundError("not found")

            result, candidates = blueprint_generator._patch_blueprint_with_feedback(
                original_blueprint=sample_blueprint,
                director_feedback="씬 배분 불균형",
                attempt_number=2,
                ep_num=1,
                arc_data=sample_arc_data,
                constraint_block={},
            )

        assert result is not None
        call_args = blueprint_generator.ensemble.generate_ensemble.call_args
        feedback = call_args.kwargs.get("feedback", "")
        assert "패치 모드" in feedback
        assert "씬 배분 불균형" in feedback


class TestBlueprintPatchIntegration:
    """ThreePhaseBlueprintGenerator.generate() 내 패치 분기 테스트."""

    def test_retry1_with_high_score_enters_patch(self, blueprint_generator, sample_arc_data):
        """retry==1에서 score >= 50이면 패치 모드 진입."""
        bp1 = {"ep_num": 1, "scene_list": [{"scene_no": 1}]}
        bp_patched = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "패치됨"}]}

        # retry 0: 생성 성공 → REJECT (score=60)
        # retry 1: 패치 시도 → 생성 성공 → PASS
        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),  # retry 0: 정상 생성
            (bp_patched, [bp_patched]),  # retry 1: 패치 모드 ensemble
        ]
        blueprint_generator.validator.validate.side_effect = [
            ("REJECT", {"score": 60, "feedback": "밀도 부족", "issues": []}),
            ("PASS", {"score": 85, "issues": [], "confidence": 90}),
        ]

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=2,
        )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        # ensemble이 2번 호출됨 (retry 0: 일반, retry 1: 패치)
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 2

    def test_low_score_skips_patch(self, blueprint_generator, sample_arc_data):
        """score < 50이면 패치 미진입, 전면 재생성."""
        bp1 = {"ep_num": 1, "scene_list": [{"scene_no": 1}]}
        bp2 = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "재생성"}]}

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),  # retry 0
            (bp2, [bp2]),  # retry 1: 전면 재생성 (패치 아님)
        ]
        blueprint_generator.validator.validate.side_effect = [
            ("REJECT", {"score": 30, "feedback": "근본적 재설계 필요", "issues": []}),
            ("PASS", {"score": 80, "issues": [], "confidence": 85}),
        ]

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=2,
        )

        assert result is not None
        # retry 1에서 패치가 아닌 일반 생성이므로, 피드백에 "패치 모드"가 없어야 함
        call_args_list = blueprint_generator.ensemble.generate_ensemble.call_args_list
        retry1_feedback = call_args_list[1].kwargs.get("feedback", "")
        assert "패치 모드" not in retry1_feedback
