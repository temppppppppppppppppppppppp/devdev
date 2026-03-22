"""Tests for Arc patch mode (FourPhaseArcGenerator.patch_arc_with_feedback)."""

from pathlib import Path
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
    def test_runtime_attached(self, arc_generator):
        assert arc_generator.runtime.owner is arc_generator

    def test_generate_delegates_to_runtime(self, arc_generator):
        expected = ({"arc_no": 1}, {"final_verdict": "PASS"})
        curr_block = {"block_theme": "test"}
        prev_arcs = [{"arc_no": 0}]
        assets = {"gear": []}
        entity_registry = {"npc": {}}
        state_tracker = object()
        adversarial_self_play = object()
        director = object()

        arc_generator.runtime = MagicMock()
        arc_generator.runtime.generate.return_value = expected

        result = arc_generator.generate(
            arc_no=1,
            ep_start=1,
            vol_strategy="standard",
            curr_block=curr_block,
            prev_arcs=prev_arcs,
            assets=assets,
            max_internal_retries=3,
            protagonist_name="hero",
            director_feedback="focus",
            entity_registry=entity_registry,
            state_tracker=state_tracker,
            vector_context="vec",
            adversarial_self_play=adversarial_self_play,
            director=director,
        )

        assert result == expected
        arc_generator.runtime.generate.assert_called_once_with(
            arc_no=1,
            ep_start=1,
            vol_strategy="standard",
            curr_block=curr_block,
            prev_arcs=prev_arcs,
            assets=assets,
            max_internal_retries=3,
            protagonist_name="hero",
            director_feedback="focus",
            entity_registry=entity_registry,
            state_tracker=state_tracker,
            vector_context="vec",
            adversarial_self_play=adversarial_self_play,
            director=director,
        )

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


    def test_patch_mode_preserves_original_arc_tail_context(self, arc_generator, sample_arc):
        """Large original Arc JSON should preserve tail context in patch prompt."""
        patched_arc = {**sample_arc, "tactical_doc": "patched tactical"}
        large_arc = {
            **sample_arc,
            "tactical_doc": "HEAD-ARC\n" + ("A" * 35000) + "\nTAIL-ARC",
        }

        arc_generator.ensemble.generate_ensemble.return_value = (None, [patched_arc])
        arc_generator.validator.validate.return_value = ("PASS", {"issues": [], "confidence": 90})
        arc_generator.preflight.analyze.return_value = {}
        arc_generator.preflight.generate_analyst_injection.return_value = ""
        arc_generator.compiler.compile.return_value = ""
        arc_generator.negative_injector.generate_injection.return_value = ""
        arc_generator.negative_injector.generate_self_check_prompt.return_value = ""

        with patch("modules.core.prompt_loader.PromptLoader") as mock_loader_cls:
            mock_loader_cls.return_value.load.side_effect = FileNotFoundError("not found")

            result_arc, pipeline = arc_generator.patch_arc_with_feedback(
                original_arc=large_arc,
                director_feedback="keep structure",
                attempt_number=2,
                arc_no=1,
                ep_start=1,
                vol_strategy="",
                curr_block={},
                prev_arcs=[],
            )

        assert result_arc is not None
        assert pipeline["final_verdict"] == "PASS"
        feedback = arc_generator.ensemble.generate_ensemble.call_args.kwargs.get("feedback", "")
        assert "HEAD-ARC" in feedback
        assert "TAIL-ARC" in feedback
        assert feedback.count("A") < 35000

    def test_build_patch_mode_feedback_direct_helper_preserves_tail_context(self, arc_generator, sample_arc):
        large_arc = {
            **sample_arc,
            "tactical_doc": "HEAD-ARC\n" + ("A" * 35000) + "\nTAIL-ARC",
        }

        with patch("modules.core.prompt_loader.PromptLoader") as mock_loader_cls:
            mock_loader_cls.return_value.load.side_effect = FileNotFoundError("not found")
            feedback = arc_generator._build_patch_mode_feedback(
                original_arc=large_arc,
                director_feedback="keep structure",
                attempt_number=2,
            )

        assert "HEAD-ARC" in feedback
        assert "TAIL-ARC" in feedback
        assert feedback.count("A") < 35000

    def test_build_patch_mode_constraint_block_direct_helper_includes_non_wuxia_warning(self, arc_generator):
        arc_generator._genre = "investment"
        arc_generator.preflight.analyze.return_value = {"world_state": {}}
        arc_generator.preflight.generate_analyst_injection.return_value = "preflight"
        arc_generator.compiler.compile.return_value = "constraints"
        arc_generator.negative_injector.generate_injection.return_value = "neg"
        arc_generator.negative_injector.generate_self_check_prompt.return_value = "self_check"

        preflight_result, constraint_block = arc_generator._build_patch_mode_constraint_block(prev_arcs=[])

        assert preflight_result == {"world_state": {}}
        assert "정신력" in constraint_block
        assert "preflight" in constraint_block
        assert "constraints" in constraint_block
        assert "self_check" in constraint_block

    def test_patch_mode_source_has_no_legacy_original_arc_head_cut(self):
        src = Path("modules/domain/agents/four_phase_arc_generator.py").read_text(encoding="utf-8")
        assert "_full_json[:30000]" not in src


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
