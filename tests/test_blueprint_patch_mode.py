"""Tests for Blueprint in-place patch mode (ThreePhaseBlueprintGenerator._inplace_patch_blueprint)."""

from unittest.mock import MagicMock, patch

import pytest

from modules.domain.agents.base_agent import AgentErrorType


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.master_bible = {"MasterBible": {"protagonist_config": {"name": "테스트주인공"}}}
    ctx.pass_rate_monitor = None
    ctx.current_project = None
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

    def test_yaml_load_failure_uses_inline_fallback(self, blueprint_generator, sample_blueprint, sample_arc_data):
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

    def test_schema_incompatible_failure_breaks_retry_loop(self, blueprint_generator, sample_arc_data):
        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.return_value = (None, [])
        blueprint_generator.ensemble.last_error_type = AgentErrorType.SCHEMA_INCOMPATIBLE

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=9,
        )

        assert result is None
        assert pipeline["final_verdict"] == "FAILED"
        assert pipeline["failure_reason"] == AgentErrorType.SCHEMA_INCOMPATIBLE
        assert pipeline["phases"]["generate"]["error_type"] == AgentErrorType.SCHEMA_INCOMPATIBLE
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 1

    def test_schema_incompatible_in_worker_bundle_overrides_stale_single_error(
        self, blueprint_generator, sample_arc_data
    ):
        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.return_value = (None, [])
        blueprint_generator.ensemble.last_error_type = AgentErrorType.TIMEOUT
        blueprint_generator.ensemble.last_error_types = [
            AgentErrorType.TIMEOUT,
            AgentErrorType.SCHEMA_INCOMPATIBLE,
        ]

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=9,
        )

        assert result is None
        assert pipeline["final_verdict"] == "FAILED"
        assert pipeline["failure_reason"] == AgentErrorType.SCHEMA_INCOMPATIBLE
        assert pipeline["phases"]["generate"]["error_type"] == AgentErrorType.SCHEMA_INCOMPATIBLE

    def test_schema_incompatible_does_not_emergency_fallback_previous_best(
        self, blueprint_generator, sample_arc_data
    ):
        bp1 = {"ep_num": 1, "scene_list": [{"scene_no": 1}]}

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),
            (None, []),
        ]
        blueprint_generator.validator.validate.return_value = (
            "REJECT",
            {"score": 60, "feedback": "보강 필요", "issues": []},
        )
        blueprint_generator.ensemble.last_error_type = None
        attempts = [(bp1, [bp1]), (None, [])]

        def _set_schema_error(*args, **kwargs):
            if len(attempts) == 1:
                blueprint_generator.ensemble.last_error_type = AgentErrorType.SCHEMA_INCOMPATIBLE
            return attempts.pop(0)

        blueprint_generator.ensemble.generate_ensemble.side_effect = _set_schema_error

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=1,
            director=MagicMock(),
        )

        assert result is None
        assert pipeline["final_verdict"] == "FAILED"
        assert pipeline["failure_reason"] == AgentErrorType.SCHEMA_INCOMPATIBLE

    def test_generate_failure_retry_records_intermediate_stage3_reject(
        self, blueprint_generator, sample_arc_data
    ):
        bp = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "retry success"}]}

        blueprint_generator.context.pass_rate_monitor = MagicMock()
        blueprint_generator.context.current_project = MagicMock(metrics_session_id="sess_stage3_mid")
        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (None, []),
            (bp, [bp]),
        ]
        blueprint_generator.ensemble.last_error_types = []
        blueprint_generator.ensemble.last_error_type = AgentErrorType.UNKNOWN
        blueprint_generator.validator.validate.return_value = (
            "PASS",
            {"score": 92, "issues": [], "confidence": 88},
        )

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=1,
        )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        kw = blueprint_generator.context.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["success"] is False
        assert kw["final_verdict"] == "REJECT"
        assert kw["generation_method"] == "blueprint_intermediate"
        assert kw["error_category"] == "generate_failed"
        assert kw["attempt_key"] == "s3:ep1:arc1:a1:sess_stage3_mid:intermediate:generate_failed"

    def test_continuity_reject_retry_records_intermediate_stage3_reject(
        self, blueprint_generator, sample_arc_data
    ):
        bp = {"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "retry success"}]}
        director = MagicMock()
        director.check_blueprint_continuity_with_cache.side_effect = [
            {"decision": "REJECT", "feedback": "continuity drift"},
            {},
        ]

        blueprint_generator.context.pass_rate_monitor = MagicMock()
        blueprint_generator.context.current_project = MagicMock(metrics_session_id="sess_stage3_mid")
        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp, [bp]),
            (bp, [bp]),
        ]
        blueprint_generator.validator.validate.return_value = (
            "PASS",
            {"score": 94, "issues": [], "confidence": 90},
        )

        result, pipeline = blueprint_generator.generate(
            ep_num=2,
            arc_data=sample_arc_data,
            max_retries=1,
            director=director,
            db=MagicMock(),
        )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        kw = blueprint_generator.context.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["error_category"] == "continuity_reject"
        assert kw["reject_reason"] == "continuity drift"
        assert kw["attempt_key"] == "s3:ep2:arc1:a1:sess_stage3_mid:intermediate:continuity_reject"

    def test_validation_reject_retry_records_intermediate_stage3_reject(
        self, blueprint_generator, sample_arc_data
    ):
        bp = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "retry success"}]}

        blueprint_generator.context.pass_rate_monitor = MagicMock()
        blueprint_generator.context.current_project = MagicMock(metrics_session_id="sess_stage3_mid")
        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp, [bp]),
            (bp, [bp]),
        ]
        blueprint_generator.validator.validate.side_effect = [
            ("REJECT", {"score": 55, "feedback": "director reject", "issues": []}),
            ("PASS", {"score": 93, "issues": [], "confidence": 87}),
        ]

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=1,
        )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        kw = blueprint_generator.context.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["error_category"] == "validation_reject"
        assert kw["reject_reason"] == "director reject"
        assert kw["candidate_key"] == ""
        assert kw["attempt_key"] == "s3:ep1:arc1:a1:sess_stage3_mid:intermediate:validation_reject"

    def test_terminal_stage3_reject_does_not_record_intermediate_observability(
        self, blueprint_generator, sample_arc_data
    ):
        bp = {"ep_num": 1, "scene_list": [{"scene_no": 1}]}

        blueprint_generator.context.pass_rate_monitor = MagicMock()
        blueprint_generator.context.current_project = MagicMock(metrics_session_id="sess_stage3_mid")
        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.return_value = (bp, [bp])
        blueprint_generator.validator.validate.return_value = (
            "REJECT",
            {"score": 55, "feedback": "final reject", "issues": []},
        )

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=0,
        )

        assert result is None
        assert pipeline["final_verdict"] == "FAILED"
        blueprint_generator.context.pass_rate_monitor.record_attempt.assert_not_called()

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

    def test_inplace_failure_falls_back_to_full_rewrite_in_same_attempt(self, blueprint_generator, sample_arc_data):
        """retry 마지막 기회에서도 inplace 실패 시 같은 시도 안에서 full rewrite로 폴백한다."""
        bp1 = {"ep_num": 1, "scene_list": [{"scene_no": 1}]}
        bp2 = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "풀 리라이트 재생성"}]}

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),  # retry 0
            (bp2, [bp2]),  # retry 1 same-attempt full rewrite fallback
        ]
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value=None)
        blueprint_generator.validator.validate.side_effect = [
            ("REJECT", {"score": 65, "feedback": "로컬 수정만으론 부족", "issues": []}),
            ("PASS", {"score": 93, "issues": [], "confidence": 87}),
        ]

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=1,
        )

        assert result is not None
        assert result["scene_list"][0]["summary"] == "풀 리라이트 재생성"
        assert pipeline["final_verdict"] == "PASS"
        blueprint_generator._inplace_patch_blueprint.assert_called_once_with(
            original_blueprint=bp1,
            director_feedback="로컬 수정만으론 부족",
            ep_num=1,
            arc_data=sample_arc_data,
        )
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 2

    def test_compare_mode_quality_risk_persists_in_pipeline(self, blueprint_generator, sample_arc_data):
        bp_a = {
            "ep_num": 1,
            "scene_list": [{"scene_no": 1}],
            "_ensemble_meta": {"strategy": "steady"},
        }
        bp_b = {
            "ep_num": 1,
            "scene_list": [{"scene_no": 1, "summary": "selected"}],
            "_ensemble_meta": {"strategy": "sharp"},
        }

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.return_value = (bp_b, [bp_a, bp_b])
        blueprint_generator.validator.validate.return_value = (
            "PASS",
            {
                "score": 91,
                "issues": [],
                "confidence": 88,
                "phase": "director_compare+python_prevalidate",
                "selected_index": 1,
                "selected_blueprint": bp_b,
                "comparison_notes": "candidate 2 is stronger on arc delivery",
                "selection_reason": "candidate 2 is stronger on arc delivery",
                "verdict_reason": "pass but keep advisory visible",
                "quality_risk": True,
                "candidate_count": 2,
                "candidate_advisories": [
                    {"candidate_index": 0, "quality_risk": False},
                    {"candidate_index": 1, "quality_risk": True},
                ],
                "selected_candidate_advisory": {
                    "candidate_index": 1,
                    "quality_risk": True,
                    "python_warnings": [{"message": "Arc NPC mention is thin"}],
                },
            },
        )

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=0,
        )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        assert pipeline["quality_risk"] is True
        assert pipeline["phases"]["validate"]["selection_reason"] == "candidate 2 is stronger on arc delivery"
        assert pipeline["phases"]["validate"]["selected_candidate_advisory"]["quality_risk"] is True

    def test_compare_mode_revision_required_persists_without_quality_risk(self, blueprint_generator, sample_arc_data):
        bp_a = {
            "ep_num": 1,
            "scene_list": [{"scene_no": 1, "summary": "selected"}],
            "_ensemble_meta": {"strategy": "steady"},
        }

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.return_value = (bp_a, [bp_a])
        blueprint_generator.validator.validate.return_value = (
            "PASS",
            {
                "score": 92,
                "issues": [],
                "confidence": 88,
                "phase": "director_compare+python_prevalidate",
                "selected_index": 0,
                "selected_blueprint": bp_a,
                "comparison_notes": "usable but still needs editorial polish",
                "selection_reason": "usable but still needs editorial polish",
                "verdict_reason": "warning only",
                "quality_risk": False,
                "revision_required": True,
                "candidate_count": 1,
                "selected_candidate_advisory": {
                    "candidate_index": 0,
                    "quality_risk": False,
                },
            },
        )

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=0,
        )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        assert bool(pipeline.get("quality_risk", False)) is False
        assert pipeline["revision_required"] is True
        assert pipeline["phases"]["validate"]["revision_required"] is True

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

    def test_pass_with_fix_partial_routes_to_single_strategy_regenerate(self, blueprint_generator, sample_arc_data):
        """PASS_WITH_FIX + partial은 inplace가 아니라 단일 전략 재생성으로 라우팅된다."""
        bp1 = {
            "ep_num": 1,
            "scene_list": [{"scene_no": 1}],
            "_ensemble_meta": {"strategy": "steady"},
        }
        bp2 = {
            "ep_num": 1,
            "scene_list": [{"scene_no": 1, "summary": "단일 전략 재생성"}],
            "_ensemble_meta": {"strategy": "steady"},
        }

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),
            (bp2, [bp2]),
        ]
        blueprint_generator.validator.validate.side_effect = [
            ("PASS_WITH_FIX", {"score": 82, "feedback": "구조 재배치 필요", "fix_scope": "partial", "issues": []}),
            ("PASS", {"score": 94, "issues": [], "confidence": 89}),
        ]
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=1,
        )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        blueprint_generator._inplace_patch_blueprint.assert_not_called()
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 2
        second_kwargs = blueprint_generator.ensemble.generate_ensemble.call_args_list[1].kwargs
        assert second_kwargs["single_strategy"] == "steady"
        assert second_kwargs["rejected_strategy"] == "steady"

    def test_pass_with_fix_full_routes_to_full_regenerate(self, blueprint_generator, sample_arc_data):
        """PASS_WITH_FIX + full은 inplace/partial이 아니라 전체 재생성으로 위임된다."""
        bp1 = {
            "ep_num": 1,
            "scene_list": [{"scene_no": 1}],
            "_ensemble_meta": {"strategy": "steady"},
        }
        bp2 = {
            "ep_num": 1,
            "scene_list": [{"scene_no": 1, "summary": "전체 재생성"}],
            "_ensemble_meta": {"strategy": "sharp"},
        }

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),
            (bp2, [bp2]),
        ]
        blueprint_generator.validator.validate.side_effect = [
            ("PASS_WITH_FIX", {"score": 82, "feedback": "전면 재구성 필요", "fix_scope": "full", "issues": []}),
            ("PASS", {"score": 93, "issues": [], "confidence": 88}),
        ]
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})

        result, pipeline = blueprint_generator.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=1,
        )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        blueprint_generator._inplace_patch_blueprint.assert_not_called()
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 2
        second_kwargs = blueprint_generator.ensemble.generate_ensemble.call_args_list[1].kwargs
        assert second_kwargs.get("single_strategy") is None
        assert second_kwargs["rejected_strategy"] == "steady"

    def test_pass_with_fix_high_change_ratio_is_warning_only(self, blueprint_generator, sample_arc_data, caplog):
        """Stage 3 F-2는 high change ratio에서도 warning-only로 남고 PASS를 막지 않는다."""
        bp1 = {"ep_num": 1, "scene_list": [{"scene_no": 1}], "emotion_curve": "기존"}
        bp_patched = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "수정됨"}], "emotion_curve": "수정됨"}

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.return_value = (bp1, [bp1])
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value=bp_patched)
        blueprint_generator.validator.validate.side_effect = [
            ("PASS_WITH_FIX", {"score": 84, "feedback": "로컬 보강", "fix_scope": "inplace", "issues": []}),
            ("PASS", {"score": 92, "issues": [], "confidence": 90}),
        ]

        with (
            patch("modules.core.constants.calc_patch_change_ratio", return_value=0.75),
            patch("modules.core.constants.log_patch_diff"),
            caplog.at_level("WARNING"),
        ):
            result, pipeline = blueprint_generator.generate(
                ep_num=1,
                arc_data=sample_arc_data,
                max_retries=0,
            )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        blueprint_generator._inplace_patch_blueprint.assert_called_once()
        assert "[F-2] InPlace Blueprint 변경 비율 75.0% > 30%" in caplog.text
