"""Tests for Blueprint in-place patch mode (ThreePhaseBlueprintGenerator._inplace_patch_blueprint)."""

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


class TestBlueprintInplacePatchMode:
    def test_inplace_success(self, blueprint_generator, sample_blueprint, sample_arc_data):
        """in-place 패치 정상 동작 — ask()가 유효한 dict를 반환."""
        patched = {**sample_blueprint, "emotion_curve": "수정됨"}
        blueprint_generator.ensemble.ask.return_value = "{}"
        blueprint_generator.ensemble._extract_json_robust.return_value = patched

        result = blueprint_generator._inplace_patch_blueprint(
            original_blueprint=sample_blueprint,
            director_feedback="감정 곡선 부자연스러움",
            ep_num=1,
            arc_data=sample_arc_data,
        )

        assert result is not None
        assert result["emotion_curve"] == "수정됨"
        blueprint_generator.ensemble.ask.assert_called_once()

    def test_inplace_non_dict_returns_none(self, blueprint_generator, sample_blueprint, sample_arc_data):
        """_extract_json_robust가 dict가 아닐 때 None 반환."""
        blueprint_generator.ensemble.ask.return_value = "잘못된 응답"
        blueprint_generator.ensemble._extract_json_robust.return_value = None

        result = blueprint_generator._inplace_patch_blueprint(
            original_blueprint=sample_blueprint,
            director_feedback="구조 오류",
            ep_num=1,
            arc_data=sample_arc_data,
        )

        assert result is None

    def test_inplace_exception_returns_none(self, blueprint_generator, sample_blueprint, sample_arc_data):
        """ask() 예외 시 None 반환."""
        blueprint_generator.ensemble.ask.side_effect = RuntimeError("LLM 오류")

        result = blueprint_generator._inplace_patch_blueprint(
            original_blueprint=sample_blueprint,
            director_feedback="수정 필요",
            ep_num=1,
            arc_data=sample_arc_data,
        )

        assert result is None

    def test_yaml_load_failure_uses_inline_fallback(
        self, blueprint_generator, sample_blueprint, sample_arc_data
    ):
        """YAML 로드 실패 시 인라인 폴백으로 ask() 호출."""
        patched = {**sample_blueprint, "scene_list": [{"scene_no": 1, "summary": "수정됨"}]}
        blueprint_generator.ensemble.ask.return_value = "{}"
        blueprint_generator.ensemble._extract_json_robust.return_value = patched

        with patch("modules.core.prompt_loader.PromptLoader") as mock_loader_cls:
            mock_loader_cls.return_value.load.side_effect = FileNotFoundError("not found")

            result = blueprint_generator._inplace_patch_blueprint(
                original_blueprint=sample_blueprint,
                director_feedback="씬 배분 불균형",
                ep_num=1,
                arc_data=sample_arc_data,
            )

        assert result is not None
        call_args = blueprint_generator.ensemble.ask.call_args
        prompt = call_args.args[0] if call_args.args else ""
        assert "씬 배분 불균형" in prompt

    def test_missing_fields_filled_from_original(self, blueprint_generator, sample_blueprint, sample_arc_data):
        """결과에 누락된 필드는 원본 Blueprint에서 채워짐."""
        partial = {"emotion_curve": "수정됨"}  # scene_list 누락
        blueprint_generator.ensemble.ask.return_value = "{}"
        blueprint_generator.ensemble._extract_json_robust.return_value = partial

        result = blueprint_generator._inplace_patch_blueprint(
            original_blueprint=sample_blueprint,
            director_feedback="감정 곡선만 수정",
            ep_num=1,
            arc_data=sample_arc_data,
        )

        assert result is not None
        assert result["scene_list"] == sample_blueprint["scene_list"]
        assert result["emotion_curve"] == "수정됨"
        assert result["episode_number"] == 1


class TestBlueprintPatchIntegration:
    """ThreePhaseBlueprintGenerator.generate() 내 in-place 분기 테스트."""

    def test_retry1_with_high_score_enters_inplace(self, blueprint_generator, sample_arc_data):
        """retry==1에서 score >= 60이면 in-place 진입 (ask() 호출, generate_ensemble 1회만)."""
        bp1 = {"ep_num": 1, "scene_list": [{"scene_no": 1}]}
        bp_patched = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "인플레이스 수정됨"}]}

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),  # retry 0: 정상 생성
        ]
        blueprint_generator.ensemble.ask.return_value = "{}"
        blueprint_generator.ensemble._extract_json_robust.return_value = bp_patched

        blueprint_generator.validator.validate.side_effect = [
            ("REJECT", {"score": 65, "feedback": "밀도 부족", "issues": []}),
            ("PASS", {"score": 95, "issues": [], "confidence": 90}),
        ]

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=2,
        )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        # generate_ensemble은 retry 0에서만 1회 호출
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 1
        # in-place ask()는 retry 1에서 호출됨
        assert blueprint_generator.ensemble.ask.call_count == 1

    def test_low_score_skips_inplace(self, blueprint_generator, sample_arc_data):
        """score < 50이면 in-place 미진입, 전면 재생성."""
        bp1 = {"ep_num": 1, "scene_list": [{"scene_no": 1}]}
        bp2 = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "재생성"}]}

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),  # retry 0
            (bp2, [bp2]),  # retry 1: 전면 재생성
        ]
        blueprint_generator.validator.validate.side_effect = [
            ("REJECT", {"score": 30, "feedback": "근본적 재설계 필요", "issues": []}),
            ("PASS", {"score": 95, "issues": [], "confidence": 85}),
        ]

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=2,
        )

        assert result is not None
        # generate_ensemble이 2번 호출됨 (retry 0, 1 모두 전면 재생성)
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 2
        # ask()는 호출 안 됨
        assert blueprint_generator.ensemble.ask.call_count == 0

    def test_score_50_to_59_uses_ensemble_not_inplace(self, blueprint_generator, sample_arc_data):
        """score 50~59는 _previous_best 보존되지만 in-place 미진입, 전면 재생성."""
        bp1 = {"ep_num": 1, "scene_list": [{"scene_no": 1}]}
        bp2 = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "재생성"}]}

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),  # retry 0
            (bp2, [bp2]),  # retry 1: 전면 재생성 (inplace 미진입)
        ]
        blueprint_generator.validator.validate.side_effect = [
            ("REJECT", {"score": 55, "feedback": "씬 밀도 부족", "issues": []}),
            ("PASS", {"score": 92, "issues": [], "confidence": 88}),
        ]

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=2,
        )

        assert result is not None
        # score=55 → 전면 재생성 (generate_ensemble 2회, ask 0회)
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 2
        assert blueprint_generator.ensemble.ask.call_count == 0

    def test_score_60_enters_inplace_boundary(self, blueprint_generator, sample_arc_data):
        """score == 60 경계값: in-place 진입 확인."""
        bp1 = {"ep_num": 1, "scene_list": [{"scene_no": 1}]}
        bp_patched = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "경계 수정"}]}

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),  # retry 0
        ]
        blueprint_generator.ensemble.ask.return_value = "{}"
        blueprint_generator.ensemble._extract_json_robust.return_value = bp_patched

        blueprint_generator.validator.validate.side_effect = [
            ("REJECT", {"score": 60, "feedback": "감정선 보완 필요", "issues": []}),
            ("PASS", {"score": 91, "issues": [], "confidence": 87}),
        ]

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=2,
        )

        assert result is not None
        # score=60 → in-place 진입 (generate_ensemble 1회, ask 1회)
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 1
        assert blueprint_generator.ensemble.ask.call_count == 1
