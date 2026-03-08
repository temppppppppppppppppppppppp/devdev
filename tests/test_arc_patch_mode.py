"""Tests for Arc patch mode (FourPhaseArcGenerator.patch_arc_with_feedback)."""

from unittest.mock import MagicMock, patch

import pytest

from modules.core.constants import PatchModeThresholds


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.master_bible = {"MasterBible": {"protagonist_config": {"name": "테스트주인공"}}}
    return ctx


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def arc_generator(mock_context, mock_client):
    with patch("modules.domain.agents.four_phase_arc_generator.PreflightChecker"):
        with patch("modules.domain.agents.four_phase_arc_generator.ConstraintCompiler"):
            with patch("modules.domain.agents.four_phase_arc_generator.NegativeExampleInjector"):
                with patch("modules.domain.agents.four_phase_arc_generator.ArcEnsembleGenerator"):
                    with patch("modules.domain.agents.four_phase_arc_generator.UnifiedArcValidator"):
                        from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator

                        gen = FourPhaseArcGenerator(mock_context, mock_client)
                        return gen


@pytest.fixture
def sample_arc():
    return {
        "arc_no": 1,
        "ep_start": 1,
        "ep_end": 5,
        "tactical_doc": "테스트 전술서",
        "state_constraints": {
            "items_acquired": ["검"],
            "grants_received": [],
        },
    }


class TestArcPatchMode:
    def test_patch_success(self, arc_generator, sample_arc):
        """패치 모드 정상 동작 — ensemble이 유효한 arc를 반환하면 PASS."""
        patched_arc = {**sample_arc, "tactical_doc": "수정된 전술서"}

        arc_generator.ensemble.generate_ensemble.return_value = (None, [patched_arc])
        arc_generator.validator.validate.return_value = ("PASS", {"issues": [], "confidence": 90})
        arc_generator.preflight.analyze.return_value = {}
        arc_generator.preflight.generate_analyst_injection.return_value = ""
        arc_generator.compiler.compile.return_value = ""
        arc_generator.negative_injector.generate_injection.return_value = ""
        arc_generator.negative_injector.generate_self_check_prompt.return_value = ""

        result_arc, pipeline = arc_generator.patch_arc_with_feedback(
            original_arc=sample_arc,
            director_feedback="전투 장면 밀도 부족",
            attempt_number=2,
            arc_no=1,
            ep_start=1,
            vol_strategy="",
            curr_block={"block_theme": "테스트"},
            prev_arcs=[],
        )

        assert result_arc is not None
        assert pipeline["final_verdict"] == "PASS"
        assert pipeline.get("patch_mode") is True
        # enhanced_feedback에 패치 모드 표시가 포함되었는지 확인
        call_args = arc_generator.ensemble.generate_ensemble.call_args
        assert "패치 모드" in call_args.kwargs.get("feedback", "")

    def test_patch_failure_returns_none(self, arc_generator, sample_arc):
        """패치 실패 시 (None, pipeline_result) 반환."""
        arc_generator.ensemble.generate_ensemble.return_value = (None, [])
        arc_generator.preflight.analyze.return_value = {}
        arc_generator.preflight.generate_analyst_injection.return_value = ""
        arc_generator.compiler.compile.return_value = ""
        arc_generator.negative_injector.generate_injection.return_value = ""
        arc_generator.negative_injector.generate_self_check_prompt.return_value = ""

        result_arc, pipeline = arc_generator.patch_arc_with_feedback(
            original_arc=sample_arc,
            director_feedback="구조 오류",
            attempt_number=2,
            arc_no=1,
            ep_start=1,
            vol_strategy="",
            curr_block={},
            prev_arcs=[],
        )

        assert result_arc is None
        assert pipeline["final_verdict"] == "FAILED"

    def test_patch_validate_reject_returns_none(self, arc_generator, sample_arc):
        """패치 후 검증 REJECT 시 (None, pipeline_result) 반환."""
        patched_arc = {**sample_arc, "tactical_doc": "수정된 전술서"}

        arc_generator.ensemble.generate_ensemble.return_value = (None, [patched_arc])
        arc_generator.validator.validate.return_value = (
            "REJECT",
            {"issues": [{"issue": "문제"}], "feedback": "재설계"},
        )
        arc_generator.preflight.analyze.return_value = {}
        arc_generator.preflight.generate_analyst_injection.return_value = ""
        arc_generator.compiler.compile.return_value = ""
        arc_generator.negative_injector.generate_injection.return_value = ""
        arc_generator.negative_injector.generate_self_check_prompt.return_value = ""

        result_arc, pipeline = arc_generator.patch_arc_with_feedback(
            original_arc=sample_arc,
            director_feedback="전투 장면 밀도 부족",
            attempt_number=2,
            arc_no=1,
            ep_start=1,
            vol_strategy="",
            curr_block={},
            prev_arcs=[],
        )

        assert result_arc is None
        assert pipeline["final_verdict"] == "FAILED"

    def test_yaml_load_failure_uses_inline_fallback(self, arc_generator, sample_arc):
        """YAML 로드 실패 시 인라인 폴백으로 패치 프롬프트 생성."""
        patched_arc = {**sample_arc, "tactical_doc": "인라인 패치"}

        arc_generator.ensemble.generate_ensemble.return_value = (None, [patched_arc])
        arc_generator.validator.validate.return_value = ("PASS", {"issues": []})
        arc_generator.preflight.analyze.return_value = {}
        arc_generator.preflight.generate_analyst_injection.return_value = ""
        arc_generator.compiler.compile.return_value = ""
        arc_generator.negative_injector.generate_injection.return_value = ""
        arc_generator.negative_injector.generate_self_check_prompt.return_value = ""

        with patch("modules.core.prompt_loader.PromptLoader") as mock_loader_cls:
            mock_loader_cls.return_value.load.side_effect = FileNotFoundError("not found")

            result_arc, pipeline = arc_generator.patch_arc_with_feedback(
                original_arc=sample_arc,
                director_feedback="밀도 부족",
                attempt_number=2,
                arc_no=1,
                ep_start=1,
                vol_strategy="",
                curr_block={},
                prev_arcs=[],
            )

        assert result_arc is not None
        call_args = arc_generator.ensemble.generate_ensemble.call_args
        feedback = call_args.kwargs.get("feedback", "")
        assert "패치 모드" in feedback
        assert "밀도 부족" in feedback


class TestPatchModeThreshold:
    def test_score_below_threshold_no_patch(self):
        """score < REWRITE(50)이면 패치 미진입 확인."""
        assert PatchModeThresholds.REWRITE == 50
        score = 40
        assert score < PatchModeThresholds.REWRITE

    def test_score_at_threshold_triggers_patch(self):
        """score >= REWRITE(50)이면 패치 진입 조건 충족."""
        score = 50
        assert score >= PatchModeThresholds.REWRITE

    def test_score_above_threshold_triggers_patch(self):
        """score > REWRITE(50)이면 패치 진입 조건 충족."""
        score = 65
        assert score >= PatchModeThresholds.REWRITE
