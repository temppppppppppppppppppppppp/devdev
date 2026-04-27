"""Tests for Blueprint in-place patch mode (ThreePhaseBlueprintGenerator._inplace_patch_blueprint)."""

import json
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


def _ready_stage3_local_contract(
    *,
    patch_target: str = "scene_2.summary",
    scene_id: str = "scene_2",
    field_path: str = "scene_breakdown.scene_2.summary",
    target_kind: str = "scene_block",
    patch_target_id: str = "scene_2.summary",
    old_text: str = "repaired reveal",
    must_fix: str = "scene 2 summary must reflect the repaired reveal",
    success_condition: str = "scene 2 now states the reveal without rewriting the arc shell",
    subtype: str = "movement",
) -> dict:
    return {
        "fix_pack": {
            "patch_targets": [patch_target],
            "patch_target_records": [
                {
                    "summary": patch_target,
                    "scene_id": scene_id,
                    "field_path": field_path,
                    "target_kind": target_kind,
                    "patch_target_id": patch_target_id,
                    "text_anchor": {"old_text": old_text},
                }
            ],
            "must_fix": [must_fix],
            "success_condition": success_condition,
            "target_kind": target_kind,
            "subtype": subtype,
            "provenance": "director_authored",
        },
        "repair_contract": {
            "subtype": subtype,
            "fix_scope": "inplace",
            "repair_scope": "inplace",
            "authoritative_fix_scope": "inplace",
            "provenance": "director_authored",
            "target_kind": target_kind,
        },
        "scope_authority": {
            "fix_scope": "inplace",
            "repair_scope": "inplace",
            "authoritative_fix_scope": "inplace",
            "widened": False,
        },
    }


class TestStage3RepairRouter:
    def test_router_blocks_phase2_inplace_when_contract_target_is_unsupported(self):
        from modules.domain.agents.three_phase_blueprint_runtime import _Stage3RepairRouter, _ThreePhaseRetryState

        retry_state = _ThreePhaseRetryState(
            previous_best={"ep_num": 4, "scene_list": [{"scene_no": 1, "summary": "stale scene model patch"}]},
            prev_reject_score=84,
            prev_fix_scope="inplace",
            prev_fix_pack={
                "patch_targets": ["scene_breakdown.scene_4"],
                "target_kind": "scene_model",
            },
            prev_repair_contract={
                "fix_scope": "inplace",
                "repair_scope": "inplace",
                "authoritative_fix_scope": "inplace",
                "target_kind": "scene_model",
            },
            prev_scope_authority={
                "fix_scope": "inplace",
                "repair_scope": "inplace",
                "authoritative_fix_scope": "inplace",
                "widened": False,
            },
        )

        material = _Stage3RepairRouter.build_retry_material(retry_state)
        route = _Stage3RepairRouter.decide_phase2_retry(
            retry=1,
            retry_state=retry_state,
            material=material,
            inplace_threshold=60,
        )

        assert route.inplace_retry_candidate is True
        assert route.use_inplace_patch is False
        assert route.block_reasons == ["local_patch_contract:unsupported_target_kind:scene_model"]
        assert material.local_patch_gate["reason"] == "unsupported_target_kind:scene_model"

    def test_router_forces_full_regenerate_for_binding_prevalidation(self):
        from modules.domain.agents.three_phase_blueprint_runtime import _Stage3RepairRouter

        current_validation = {
            "fix_scope": "inplace",
            "binding_prevalidation_issue_count": 1,
            "binding_prevalidation_categories": ["arc_timeline"],
            "feedback": "repair timeline binding",
        }

        material = _Stage3RepairRouter.build_validation_material(current_validation)
        route = _Stage3RepairRouter.decide_pass_with_fix(
            material=material,
            score=88,
            inplace_threshold=60,
        )

        assert route.effective_fix_scope == "full"
        assert route.should_break_to_generate is True
        assert "arc_timeline" in route.regenerate_only_reason

    def test_router_requires_explicit_local_contract_before_inplace(self):
        from modules.domain.agents.three_phase_blueprint_runtime import _Stage3RepairRouter

        material = _Stage3RepairRouter.build_validation_material(
            {
                "fix_scope": "inplace",
                "fix_pack": {
                    "patch_targets": ["scene_2.summary"],
                    "patch_target_records": [
                        {
                            "summary": "scene_2.summary",
                            "scene_id": "scene_2",
                            "field_path": "scene_breakdown.scene_2.summary",
                            "target_kind": "scene_block",
                            "patch_target_id": "scene_2.summary",
                        }
                    ],
                    "must_fix": ["scene 2 summary must reflect the repaired reveal"],
                    "success_condition": "scene 2 now states the reveal without rewriting the arc shell",
                    "target_kind": "scene_block",
                },
            }
        )

        route = _Stage3RepairRouter.decide_pass_with_fix(
            material=material,
            score=88,
            inplace_threshold=60,
        )

        assert material.local_patch_gate["reason"] == "missing_authoritative_fix_scope"
        assert route.effective_fix_scope == "full"
        assert route.should_break_to_generate is True


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

    def test_inplace_patch_short_circuits_on_empty_fix_pack(
        self, blueprint_generator, sample_blueprint, sample_arc_data
    ):
        result = blueprint_generator._inplace_patch_blueprint(
            original_blueprint=sample_blueprint,
            director_feedback="빈 계약으로는 로컬 수정 금지",
            ep_num=1,
            arc_data=sample_arc_data,
            normalized_fix_pack={},
        )

        assert result is None
        blueprint_generator.ensemble.ask.assert_not_called()

    def test_inplace_patch_ir_updates_targeted_field_values(self, blueprint_generator, sample_arc_data):
        original_blueprint = {
            "ep_num": 1,
            "integrated_scenario": "기존 시나리오",
            "scene_list": [{"scene_no": 1, "summary": "도입부"}],
        }
        normalized_fix_pack = {
            "patch_targets": ["integrated_scenario"],
            "patch_target_records": [
                {
                    "summary": "integrated_scenario",
                    "field_path": "integrated_scenario",
                    "target_kind": "local_sentence",
                    "patch_target_id": "pt:integrated",
                }
            ],
            "must_fix": ["add one named market anchor"],
            "success_condition": "integrated scenario adds one named market anchor",
            "target_kind": "local_sentence",
        }
        blueprint_generator.ensemble.ask.return_value = '{"patch_values":[{"patch_target_id":"pt:integrated","field_path":"integrated_scenario","new_value":"시장 앵커가 들어간 새 시나리오"}]}'
        blueprint_generator.ensemble._extract_json_robust.return_value = {
            "patch_values": [
                {
                    "patch_target_id": "pt:integrated",
                    "field_path": "integrated_scenario",
                    "new_value": "시장 앵커가 들어간 새 시나리오",
                }
            ]
        }

        result = blueprint_generator._inplace_patch_blueprint(
            original_blueprint=original_blueprint,
            director_feedback="시장 앵커를 하나만 추가하라",
            ep_num=1,
            arc_data=sample_arc_data,
            normalized_fix_pack=normalized_fix_pack,
        )

        assert result is not None
        assert result["integrated_scenario"] == "시장 앵커가 들어간 새 시나리오"
        assert result["scene_list"] == original_blueprint["scene_list"]
        prompt = blueprint_generator.ensemble.ask.call_args.args[0]
        assert "Target Patch Packet" in prompt
        assert "integrated_scenario" in prompt
        assert "patch_values" not in prompt

    def test_inplace_patch_ir_returns_none_when_target_snapshot_is_unresolvable(
        self, blueprint_generator, sample_blueprint, sample_arc_data
    ):
        normalized_fix_pack = {
            "patch_targets": ["missing_field"],
            "patch_target_records": [
                {
                    "summary": "missing_field",
                    "field_path": "scene_breakdown.scene_99.summary",
                    "target_kind": "local_sentence",
                    "patch_target_id": "pt:missing",
                }
            ],
            "must_fix": ["restore the missing anchor"],
            "success_condition": "missing scene is repaired",
            "target_kind": "local_sentence",
        }

        result = blueprint_generator._inplace_patch_blueprint(
            original_blueprint=sample_blueprint,
            director_feedback="없는 필드를 고치라고 하면 안 됨",
            ep_num=1,
            arc_data=sample_arc_data,
            normalized_fix_pack=normalized_fix_pack,
        )

        assert result is None
        blueprint_generator.ensemble.ask.assert_not_called()

    def test_inplace_scene_block_contract_still_uses_legacy_whole_blueprint_lane(
        self, blueprint_generator, sample_blueprint, sample_arc_data
    ):
        ready_contract = _ready_stage3_local_contract()
        patched = {**sample_blueprint, "emotion_curve": "legacy whole-blueprint lane"}
        blueprint_generator.ensemble.ask.return_value = "{}"
        blueprint_generator.ensemble._extract_json_robust.return_value = patched

        result = blueprint_generator._inplace_patch_blueprint(
            original_blueprint=sample_blueprint,
            director_feedback="scene_block 계열은 아직 whole-blueprint lane 유지",
            ep_num=1,
            arc_data=sample_arc_data,
            normalized_fix_pack=ready_contract["fix_pack"],
        )

        assert result is not None
        assert result["emotion_curve"] == "legacy whole-blueprint lane"
        ask_kwargs = blueprint_generator.ensemble.ask.call_args.kwargs
        assert ask_kwargs["response_schema"] is not None
        assert ask_kwargs["temperature"] == 0.3


class TestBlueprintPatchIntegration:
    """ThreePhaseBlueprintGenerator.generate() 내 in-place 분기 테스트."""

    def test_runtime_attached(self, blueprint_generator):
        assert blueprint_generator.runtime.owner is blueprint_generator

    def test_runtime_generate_uses_retry_cycle_helper(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import (
            _ThreePhaseRetryCycleResult,
            _ThreePhaseRetryState,
            _ThreePhaseRuntimeBootstrap,
        )

        runtime = blueprint_generator.runtime
        pipeline = {"phases": {"constraint": {}, "generate": {}, "validate": {}}}
        best_blueprint = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "candidate"}]}
        bootstrap = _ThreePhaseRuntimeBootstrap(
            genre="wuxia",
            protagonist_config={},
            pipeline_result=pipeline,
            initial_feedback="seed feedback",
            retry_state=_ThreePhaseRetryState(),
        )

        with (
            patch.object(runtime, "_bootstrap_runtime_context", return_value=bootstrap),
            patch.object(
                runtime,
                "_run_retry_cycle",
                side_effect=[
                    _ThreePhaseRetryCycleResult(
                        best_blueprint=best_blueprint,
                        feedback="director retry feedback",
                        should_continue=True,
                    ),
                    _ThreePhaseRetryCycleResult(
                        best_blueprint=best_blueprint,
                        feedback="director retry feedback",
                        final_result=(best_blueprint, pipeline),
                    ),
                ],
            ) as run_retry,
            patch.object(runtime, "_finalize_terminal_failure") as finalize_failure,
        ):
            result = runtime.generate(ep_num=1, arc_data=sample_arc_data, max_retries=1)

        assert result == (best_blueprint, pipeline)
        assert run_retry.call_count == 2
        assert run_retry.call_args_list[0].kwargs["current_best_blueprint"] is None
        assert run_retry.call_args_list[0].kwargs["feedback"] == "seed feedback"
        assert run_retry.call_args_list[0].kwargs["log_retry"] is False
        assert run_retry.call_args_list[1].kwargs["current_best_blueprint"] == best_blueprint
        assert run_retry.call_args_list[1].kwargs["feedback"] == "director retry feedback"
        finalize_failure.assert_not_called()

    def test_generate_delegates_to_runtime(self, blueprint_generator, sample_arc_data):
        expected = ({"ep_num": 1}, {"final_verdict": "PASS"})
        blueprint_generator.runtime = MagicMock()
        blueprint_generator.runtime.generate.return_value = expected

        result = blueprint_generator.generate(ep_num=1, arc_data=sample_arc_data)

        assert result == expected
        blueprint_generator.runtime.generate.assert_called_once_with(
            ep_num=1,
            arc_data=sample_arc_data,
            prev_blueprint=None,
            prev_blueprints=None,
            max_retries=9,
            external_feedback="",
            director=None,
            arc_idx=0,
            entity_registry=None,
            protagonist_name="주인공",
            protagonist_config=None,
            state_tracker=None,
            db=None,
            semantic_context="",
            prev_manuscripts_text="",
            adversarial_self_play=None,
            prev_hud=None,
        )

    def test_resolve_constraint_block_reuses_cached_payload(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        cached = {"arc_no": 1, "arc_position": "1/5", "must_focus": {"content": "cached"}}
        retry_state = _ThreePhaseRetryState(cached_constraint_block=cached)
        pipeline = {"phases": {"constraint": {}}}

        resolved = blueprint_generator.runtime._resolve_constraint_block(
            retry=1,
            ep_num=1,
            arc_data=sample_arc_data,
            prev_blueprint=None,
            prev_blueprints=None,
            genre="wuxia",
            pipeline_result=pipeline,
            retry_state=retry_state,
        )

        assert resolved is cached
        blueprint_generator.constraint_compiler.compile.assert_not_called()
        assert pipeline["phases"]["constraint"]["cached"] is True

    def test_resolve_constraint_block_forwards_prev_manuscript_ending(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        compiled = {"arc_no": 1, "arc_position": "1/5"}
        retry_state = _ThreePhaseRetryState()
        pipeline = {"phases": {"constraint": {}}}
        manuscript_tail = "직전 원고 실제 종료 상황 " + ("가" * 600)
        blueprint_generator.constraint_compiler.compile.return_value = compiled

        resolved = blueprint_generator.runtime._resolve_constraint_block(
            retry=0,
            ep_num=1,
            arc_data=sample_arc_data,
            prev_blueprint=None,
            prev_blueprints=None,
            genre="wuxia",
            pipeline_result=pipeline,
            retry_state=retry_state,
            prev_manuscripts_text=manuscript_tail,
        )

        assert resolved == compiled
        call_kwargs = blueprint_generator.constraint_compiler.compile.call_args.kwargs
        assert call_kwargs["prev_manuscript_ending"] == manuscript_tail[-1600:]
        assert pipeline["phases"]["constraint"]["cached"] is False

    def test_phase2_generation_failure_breaks_on_schema_incompatible(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        blueprint_generator.ensemble.last_error_type = AgentErrorType.TIMEOUT
        blueprint_generator.ensemble.last_error_types = [
            AgentErrorType.TIMEOUT,
            AgentErrorType.SCHEMA_INCOMPATIBLE,
        ]
        pipeline = {"phases": {"generate": {}}}
        retry_state = _ThreePhaseRetryState()

        result = blueprint_generator.runtime._handle_phase2_generation_failure(
            retry=0,
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={},
            pipeline_result=pipeline,
            retry_state=retry_state,
            max_retries=2,
        )

        assert result.should_break is True
        assert result.should_continue is False
        assert pipeline["failure_reason"] == AgentErrorType.SCHEMA_INCOMPATIBLE
        assert pipeline["phases"]["generate"]["error_type"] == AgentErrorType.SCHEMA_INCOMPATIBLE
        assert pipeline["reject_reason"] == "schema_incompatible로 즉시 중단합니다."

    def test_phase2_generation_failure_retries_on_candidate_disqualified_bundle(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        blueprint_generator.context.pass_rate_monitor = MagicMock(record_attempt=MagicMock())
        blueprint_generator.ensemble.last_error_type = AgentErrorType.TIMEOUT
        blueprint_generator.ensemble.last_error_types = [
            AgentErrorType.TIMEOUT,
            AgentErrorType.SCHEMA_INCOMPATIBLE,
            AgentErrorType.CANDIDATE_DISQUALIFIED,
        ]
        pipeline = {"phases": {"generate": {}}}
        retry_state = _ThreePhaseRetryState()

        result = blueprint_generator.runtime._handle_phase2_generation_failure(
            retry=0,
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={
                "episode_progression_packet": {
                    "next_gate_strength_mode": {
                        "mode": "foreshadow_only",
                        "reason": "새 타깃 handoff는 foreshadow 수준으로만 남기고 현재 압박을 먼저 정리한다.",
                    },
                    "lawful_repetition_window": {
                        "mode": "allow_escalated_repeat",
                        "allow_same_location_if_goal_changes": True,
                        "allow_same_counterparty_if_goal_changes": True,
                        "allow_same_channel_if_decision_escalates": True,
                    },
                    "surface_guidance": [
                        "시작 anchor 계승은 짧게 처리하고 이번 화의 주 장면은 직전 대치의 결과 이후 단계로 이동하라."
                    ],
                    "future_beat_reservations": [
                        "제2화 reserved beat anchor: 승인 완료 후 실제 체결에 들어간다.",
                        "승인, 전결, 컴플라이언스, 서류, 체결, 동결 같은 결과형 절차는 다음 화 reserved beat이므로 이번 화에서 완료 처리하지 말라.",
                    ],
                }
            },
            pipeline_result=pipeline,
            retry_state=retry_state,
            max_retries=2,
        )

        assert result.should_break is False
        assert result.should_continue is True
        assert pipeline["failure_reason"] == AgentErrorType.CANDIDATE_DISQUALIFIED
        assert pipeline["phases"]["generate"]["error_type"] == AgentErrorType.CANDIDATE_DISQUALIFIED
        record_attempt = blueprint_generator.context.pass_rate_monitor.record_attempt
        reject_reason = record_attempt.call_args.kwargs["reject_reason"]
        assert "Next-gate strength modulator" in reject_reason
        assert "새 타깃 handoff는 foreshadow 수준" in reject_reason
        assert "Replay reroute guidance" in reject_reason
        assert "lawful repetition이나 authority escalation surface 자체를 막는 지시는 아닙니다" in reject_reason
        assert "직전 대치의 결과 이후 단계로 이동" in reject_reason
        assert "Lawful repetition window" in reject_reason
        assert "같은 장소라도 장면 목표가 달라졌다면" in reject_reason
        assert "Next-episode reserved beat" in reject_reason
        assert "승인 완료 후 실제 체결" in reject_reason
        assert pipeline["reject_reason"].startswith("replay/authority/구조 계약 미달 후보만 생성됨")

    def test_phase2_generation_failure_breaks_on_repeated_candidate_disqualified_plateau(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        blueprint_generator.context.pass_rate_monitor = MagicMock(record_attempt=MagicMock())
        blueprint_generator.ensemble.last_error_type = AgentErrorType.CANDIDATE_DISQUALIFIED
        blueprint_generator.ensemble.last_error_types = [AgentErrorType.CANDIDATE_DISQUALIFIED]
        constraint_block = {
            "episode_progression_packet": {
                "surface_guidance": [
                    "시작 anchor 계승은 짧게 처리하고 이번 화의 주 장면은 직전 대치의 결과 이후 단계로 이동하라."
                ]
            }
        }
        prior_feedback = blueprint_generator.runtime._build_candidate_disqualified_retry_feedback(constraint_block)
        retry_state = _ThreePhaseRetryState(
            prev_phase2_failure_signature=blueprint_generator.runtime._normalize_phase2_failure_signature(
                error_type=AgentErrorType.CANDIDATE_DISQUALIFIED,
                feedback=prior_feedback,
            ),
            repeated_phase2_failure_streak=2,
        )
        pipeline = {"phases": {"generate": {}}}

        result = blueprint_generator.runtime._handle_phase2_generation_failure(
            retry=2,
            ep_num=2,
            arc_data=sample_arc_data,
            constraint_block=constraint_block,
            pipeline_result=pipeline,
            retry_state=retry_state,
            max_retries=9,
        )

        assert result.should_break is True
        assert result.should_continue is False
        assert pipeline["reject_reason"] == "동일 replay/authority reroute guidance가 3회 연속 반복되어 조기 중단"
        assert pipeline["phases"]["generate"]["plateau_guard"]["repeat_streak"] == 3
        record_attempt = blueprint_generator.context.pass_rate_monitor.record_attempt
        assert record_attempt.call_args.kwargs["error_category"] == "generate_candidate_disqualified_plateau"

    def test_phase2_generation_failure_records_focus_strategy_for_candidate_disqualified(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        blueprint_generator.context.pass_rate_monitor = MagicMock(record_attempt=MagicMock())
        blueprint_generator.ensemble.last_error_type = AgentErrorType.CANDIDATE_DISQUALIFIED
        blueprint_generator.ensemble.last_error_types = [AgentErrorType.CANDIDATE_DISQUALIFIED]
        blueprint_generator.ensemble.last_disqualified_candidates = [
            {"strategy": "dialogue_focused", "scene_count": 3, "integrated_len": 620, "contract_reason": ""},
            {"strategy": "action_focused", "scene_count": 2, "integrated_len": 720, "contract_reason": ""},
        ]
        retry_state = _ThreePhaseRetryState()
        pipeline = {"phases": {"generate": {}}}

        result = blueprint_generator.runtime._handle_phase2_generation_failure(
            retry=0,
            ep_num=2,
            arc_data=sample_arc_data,
            constraint_block={},
            pipeline_result=pipeline,
            retry_state=retry_state,
            max_retries=2,
        )

        assert result.should_continue is True
        assert retry_state.prev_phase2_focus_strategy == "dialogue_focused"
        assert pipeline["phases"]["generate"]["focus_strategy"] == "dialogue_focused"

    def test_phase2_generation_failure_records_focus_strategy_from_screening_disqualified_candidates(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        blueprint_generator.context.pass_rate_monitor = MagicMock(record_attempt=MagicMock())
        blueprint_generator.ensemble.last_error_type = AgentErrorType.CANDIDATE_DISQUALIFIED
        blueprint_generator.ensemble.last_error_types = [AgentErrorType.CANDIDATE_DISQUALIFIED]
        blueprint_generator.ensemble.last_disqualified_candidates = [
            {
                "strategy": "action_focused",
                "scene_count": 0,
                "integrated_len": 0,
                "contract_reason": "screening_disqualified",
                "ordinal": 0,
            },
            {
                "strategy": "dialogue_focused",
                "scene_count": 0,
                "integrated_len": 0,
                "contract_reason": "screening_disqualified",
                "ordinal": 1,
            },
        ]
        retry_state = _ThreePhaseRetryState()
        pipeline = {"phases": {"generate": {}}}

        result = blueprint_generator.runtime._handle_phase2_generation_failure(
            retry=0,
            ep_num=2,
            arc_data=sample_arc_data,
            constraint_block={},
            pipeline_result=pipeline,
            retry_state=retry_state,
            max_retries=2,
        )

        assert result.should_continue is True
        assert retry_state.prev_phase2_focus_strategy == "action_focused"
        assert pipeline["phases"]["generate"]["focus_strategy"] == "action_focused"

    def test_phase2_generation_failure_rotates_focus_strategy_after_repeated_screening_plateau(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        blueprint_generator.context.pass_rate_monitor = MagicMock(record_attempt=MagicMock())
        blueprint_generator.ensemble.last_error_type = AgentErrorType.CANDIDATE_DISQUALIFIED
        blueprint_generator.ensemble.last_error_types = [AgentErrorType.CANDIDATE_DISQUALIFIED]
        blueprint_generator.ensemble.last_disqualified_candidates = [
            {
                "strategy": "action_focused",
                "scene_count": 0,
                "integrated_len": 0,
                "contract_reason": "screening_disqualified",
                "ordinal": 0,
            },
            {
                "strategy": "emotion_focused",
                "scene_count": 0,
                "integrated_len": 0,
                "contract_reason": "screening_disqualified",
                "ordinal": 1,
            },
            {
                "strategy": "dialogue_focused",
                "scene_count": 0,
                "integrated_len": 0,
                "contract_reason": "screening_disqualified",
                "ordinal": 2,
            },
        ]
        retry_state = _ThreePhaseRetryState(
            prev_phase2_failure_signature=blueprint_generator.runtime._normalize_phase2_failure_signature(
                error_type=AgentErrorType.CANDIDATE_DISQUALIFIED,
                feedback=blueprint_generator.runtime._build_candidate_disqualified_retry_feedback({}),
            ),
            prev_phase2_focus_strategy="action_focused",
            repeated_phase2_failure_streak=1,
        )
        pipeline = {"phases": {"generate": {}}}

        result = blueprint_generator.runtime._handle_phase2_generation_failure(
            retry=1,
            ep_num=2,
            arc_data=sample_arc_data,
            constraint_block={},
            pipeline_result=pipeline,
            retry_state=retry_state,
            max_retries=2,
        )

        assert result.should_continue is True
        assert retry_state.prev_phase2_focus_strategy == "emotion_focused"
        assert pipeline["phases"]["generate"]["focus_strategy"] == "emotion_focused"

    def test_phase2_generation_failure_preserves_richer_focus_pool_across_single_strategy_retry(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        blueprint_generator.context.pass_rate_monitor = MagicMock(record_attempt=MagicMock())
        blueprint_generator.ensemble.last_error_type = AgentErrorType.CANDIDATE_DISQUALIFIED
        blueprint_generator.ensemble.last_error_types = [AgentErrorType.CANDIDATE_DISQUALIFIED]
        blueprint_generator.ensemble.last_disqualified_candidates = [
            {
                "strategy": "action_focused",
                "scene_count": 0,
                "integrated_len": 0,
                "contract_reason": "screening_disqualified",
                "ordinal": 0,
            }
        ]
        retry_state = _ThreePhaseRetryState(
            prev_phase2_failure_signature=blueprint_generator.runtime._normalize_phase2_failure_signature(
                error_type=AgentErrorType.CANDIDATE_DISQUALIFIED,
                feedback=blueprint_generator.runtime._build_candidate_disqualified_retry_feedback({}),
            ),
            prev_phase2_focus_strategy="action_focused",
            prev_phase2_focus_pool=[
                {
                    "strategy": "action_focused",
                    "scene_count": 0,
                    "integrated_len": 0,
                    "contract_reason": "screening_disqualified",
                    "ordinal": 0,
                },
                {
                    "strategy": "emotion_focused",
                    "scene_count": 0,
                    "integrated_len": 0,
                    "contract_reason": "screening_disqualified",
                    "ordinal": 1,
                },
                {
                    "strategy": "dialogue_focused",
                    "scene_count": 0,
                    "integrated_len": 0,
                    "contract_reason": "screening_disqualified",
                    "ordinal": 2,
                },
            ],
            repeated_phase2_failure_streak=1,
        )
        pipeline = {"phases": {"generate": {}}}

        result = blueprint_generator.runtime._handle_phase2_generation_failure(
            retry=1,
            ep_num=2,
            arc_data=sample_arc_data,
            constraint_block={},
            pipeline_result=pipeline,
            retry_state=retry_state,
            max_retries=2,
        )

        assert result.should_continue is True
        assert [item["strategy"] for item in retry_state.prev_phase2_focus_pool] == [
            "action_focused",
            "emotion_focused",
            "dialogue_focused",
        ]
        assert retry_state.prev_phase2_focus_strategy == "emotion_focused"
        assert pipeline["phases"]["generate"]["focus_strategy"] == "emotion_focused"

    def test_phase3_validation_continuity_reject_short_circuits(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        director = MagicMock()
        director.check_blueprint_continuity_with_cache.return_value = {
            "decision": "REJECT",
            "feedback": "continuity drift",
        }
        retry_state = _ThreePhaseRetryState()
        pipeline = {"phases": {"generate": {}, "validate": {}}}
        best_blueprint = {"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "candidate"}]}

        result = blueprint_generator.runtime._run_phase3_validation(
            ep_num=2,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            best_blueprint=best_blueprint,
            all_candidates=[best_blueprint],
            director=director,
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            db=MagicMock(),
            prev_hud=None,
            retry_state=retry_state,
            pipeline_result=pipeline,
            retry=0,
            max_retries=1,
        )

        assert result.should_continue is True
        assert retry_state.prev_reject_feedback == "continuity drift"
        assert retry_state.previous_best == best_blueprint
        blueprint_generator.validator.validate.assert_not_called()

    def test_record_phase3_validation_payload_truncates_candidate_advisories(self, blueprint_generator):
        pipeline = {"phases": {"generate": {}, "validate": {}}}
        validation_result = {
            "issues": [{"severity": "major"}],
            "confidence": 88,
            "score": 91,
            "phase": "judge",
            "selected_index": 1,
            "comparison_notes": "notes",
            "selection_reason": "pick steady",
            "verdict_reason": "best fit",
            "fix_scope": "inplace",
            "fix_scope_reasoning": "localized",
            "quality_risk": True,
            "candidate_advisories": [{"n": 1}, {"n": 2}, {"n": 3}, {"n": 4}],
            "selected_candidate_advisory": {"focus": "keep"},
            "fix_pack": {
                "patch_targets": ["scene_2.summary"],
                "patch_target_records": [
                    {
                        "summary": "scene_2.summary",
                        "scene_id": "scene_2",
                        "field_path": "scene_breakdown.scene_2.summary",
                        "target_kind": "scene_block",
                    }
                ],
                "must_fix": ["scene 2 summary must reflect the repaired reveal"],
                "do_not_regress": ["scene 1 opening cadence must stay intact"],
                "success_condition": "scene 2 now states the reveal without rewriting the arc shell",
                "target_kind": "scene_block",
            },
            "advisory_fix_pack": {
                "patch_targets": ["integrated_scenario"],
                "patch_target_records": [
                    {
                        "summary": "integrated_scenario",
                        "field_path": "integrated_scenario",
                        "target_kind": "local_sentence",
                    }
                ],
                "must_fix": ["add one named anchor"],
                "do_not_regress": ["keep the opening move"],
                "success_condition": "integrated scenario adds one named anchor",
                "target_kind": "local_sentence",
                "evidence_summary": "anchor_count=0",
            },
        }

        blueprint_generator.runtime._record_phase3_validation_payload(
            pipeline_result=pipeline,
            validation_result=validation_result,
            verdict="PASS_WITH_FIX",
            selected_strategy="steady",
            all_candidates=[{"ep_num": 1}],
            score=91,
        )

        assert pipeline["phases"]["validate"]["candidate_advisories"] == validation_result["candidate_advisories"][:3]
        assert pipeline["phases"]["validate"]["selected_candidate_advisory"] == {"focus": "keep"}
        assert pipeline["phases"]["validate"]["fix_pack"]["patch_targets"] == ["scene_2.summary"]
        assert pipeline["phases"]["validate"]["fix_pack"]["patch_target_records"][0]["scene_id"] == "scene_2"
        assert pipeline["phases"]["validate"]["advisory_fix_pack"]["patch_targets"] == ["integrated_scenario"]
        assert pipeline["phases"]["validate"]["advisory_fix_pack"]["evidence_summary"] == "anchor_count=0"
        assert pipeline["quality_risk"] is True
        assert pipeline["revision_required"] is True
        assert pipeline["phases"]["generate"]["selected_strategy"] == "steady"
        assert pipeline["phases"]["generate"]["selected_score"] == 91

    def test_record_phase3_validation_payload_does_not_backfill_selection_reason_from_comparison_notes(
        self, blueprint_generator
    ):
        pipeline = {"phases": {"generate": {}, "validate": {}}}
        validation_result = {
            "issues": [],
            "confidence": 88,
            "score": 91,
            "phase": "director_compare+python_prevalidate",
            "selected_index": 1,
            "comparison_notes": "candidate 2 is stronger on arc delivery",
            "verdict_reason": "pass but keep advisory visible",
        }

        blueprint_generator.runtime._record_phase3_validation_payload(
            pipeline_result=pipeline,
            validation_result=validation_result,
            verdict="PASS",
            selected_strategy="steady",
            all_candidates=[{"ep_num": 1}],
            score=91,
        )

        assert pipeline["phases"]["validate"]["selection_reason"] == ""
        assert pipeline["phases"]["validate"]["comparison_notes"] == "candidate 2 is stronger on arc delivery"

    def test_apply_phase3_quality_gate_downgrades_low_score_pass(self, blueprint_generator):
        with patch("modules.domain.agents.three_phase_blueprint_runtime._threshold", return_value=95):
            verdict = blueprint_generator.runtime._apply_phase3_quality_gate(
                verdict="PASS",
                score=94,
                validation_result={"issues": [{"category": "quality_gate", "issue": "score floor miss"}]},
            )

        assert verdict == "REJECT"

    def test_apply_phase3_quality_gate_preserves_advisory_only_low_score_pass(self, blueprint_generator):
        with patch("modules.domain.agents.three_phase_blueprint_runtime._threshold", return_value=95):
            verdict = blueprint_generator.runtime._apply_phase3_quality_gate(
                verdict="PASS",
                score=94,
                validation_result={
                    "issues": [
                        {
                            "category": "scenario_density",
                            "issue": "앵커가 얇음",
                            "advisory_only": True,
                            "director_focus": False,
                        }
                    ],
                    "quality_risk": False,
                    "binding_prevalidation_issue_count": 0,
                },
            )

        assert verdict == "PASS"

    def test_resolve_retry_cycle_result_accepts_low_yield_advisory_only_pass_with_fix_as_warning(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        pipeline_result = {"phases": {"validate": {}}}
        blueprint_generator.runtime._run_pass_with_fix_loop = MagicMock(side_effect=AssertionError("unexpected"))

        result = blueprint_generator.runtime._resolve_retry_cycle_result(
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            best_blueprint={"ep_num": 1, "integrated_scenario": "scenario"},
            validation_result={
                "issues": [
                    {
                        "category": "scenario_density",
                        "issue": "앵커가 얇음",
                        "advisory_only": True,
                        "director_focus": False,
                    }
                ],
                "quality_risk": False,
                "binding_prevalidation_issue_count": 0,
                "feedback": "기관명 anchor를 더 보강",
                "fix_scope": "inplace",
            },
            verdict="PASS_WITH_FIX",
            score=85,
            selected_strategy="dialogue",
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            initial_feedback="기관명 anchor를 더 보강",
            feedback="기관명 anchor를 더 보강",
            retry_state=_ThreePhaseRetryState(),
            pipeline_result=pipeline_result,
            retry=0,
            max_retries=2,
        )

        _, resolved_pipeline = result.final_result
        assert resolved_pipeline["final_verdict"] == "PASS_WITH_WARNING"
        assert resolved_pipeline["phases"]["validate"]["advisory_only_residual_acceptance"] == {
            "decision": "promote_to_pass_with_warning",
            "categories": ["scenario_density"],
            "reason": "low_yield_advisory_local_patch",
        }
        blueprint_generator.runtime._run_pass_with_fix_loop.assert_not_called()

    def test_resolve_retry_cycle_result_accepts_actionless_pass_with_fix_as_warning(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        pipeline_result = {"phases": {"validate": {}}}
        blueprint_generator.runtime._run_pass_with_fix_loop = MagicMock(side_effect=AssertionError("unexpected"))

        result = blueprint_generator.runtime._resolve_retry_cycle_result(
            ep_num=6,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            best_blueprint={"ep_num": 6, "integrated_scenario": "scenario"},
            validation_result={
                "issues": [],
                "contradictions": [],
                "contradiction_count": 0,
                "quality_risk": False,
                "binding_prevalidation_issue_count": 0,
                "feedback": "Arc 지시사항을 완벽히 반영",
                "fix_scope": "inplace",
            },
            verdict="PASS_WITH_FIX",
            score=95,
            selected_strategy="dialogue",
            director=MagicMock(),
            arc_idx=1,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            initial_feedback="",
            feedback="",
            retry_state=_ThreePhaseRetryState(),
            pipeline_result=pipeline_result,
            retry=3,
            max_retries=10,
        )

        _, resolved_pipeline = result.final_result
        assert resolved_pipeline["final_verdict"] == "PASS_WITH_WARNING"
        assert resolved_pipeline["phases"]["validate"]["actionless_pass_with_fix_acceptance"] == {
            "decision": "promote_to_pass_with_warning",
            "reason": "director_pass_with_fix_without_actionable_fix_payload",
        }
        blueprint_generator.runtime._run_pass_with_fix_loop.assert_not_called()

    def test_resolve_retry_cycle_result_routes_structural_binding_pass_with_fix_to_regenerate(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        retry_state = _ThreePhaseRetryState()
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}
        blueprint_generator.runtime._run_pass_with_fix_loop = MagicMock(side_effect=AssertionError("unexpected"))

        result = blueprint_generator.runtime._resolve_retry_cycle_result(
            ep_num=4,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            best_blueprint={"ep_num": 4, "integrated_scenario": "candidate"},
            validation_result={
                "issues": [
                    {
                        "severity": "MAJOR",
                        "category": "arc_timeline",
                        "issue": "timeline exceeds arc date window",
                    }
                ],
                "binding_prevalidation_issue_count": 1,
                "binding_prevalidation_categories": ["arc_timeline"],
                "feedback": "timeline repair required",
                "fix_scope": "inplace",
                "fix_scope_reasoning": "Director suggested a local fix, but binding is structural.",
            },
            verdict="PASS_WITH_FIX",
            score=88,
            selected_strategy="dialogue",
            director=MagicMock(),
            arc_idx=1,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            initial_feedback="timeline repair required",
            feedback="timeline repair required",
            retry_state=retry_state,
            pipeline_result=pipeline_result,
            retry=2,
            max_retries=9,
        )

        assert result.should_continue is True
        assert result.final_result is None
        assert retry_state.prev_reject_origin == "binding_prevalidation_reopen"
        assert retry_state.prev_binding_issue_count == 1
        assert retry_state.prev_fix_scope == "full"
        assert "arc_timeline" in retry_state.prev_reject_feedback
        validate_phase = pipeline_result["phases"]["validate"]
        assert validate_phase["director_verdict"] == "PASS_WITH_FIX"
        assert validate_phase["runtime_route_verdict"] == "REJECT"
        assert validate_phase["runtime_gate_basis"] == "binding_prevalidation_reopen"
        assert validate_phase["runtime_route_action"] == "full_regenerate_retry"
        assert validate_phase["fix_scope"] == "full"
        assert validate_phase["binding_regenerate_only_categories"] == ["arc_timeline"]
        blueprint_generator.runtime._run_pass_with_fix_loop.assert_not_called()

    def test_resolve_retry_cycle_result_keeps_opening_transition_alias_in_pass_with_fix_loop(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import (
            _ThreePhasePassWithFixResult,
            _ThreePhaseRetryState,
        )

        retry_state = _ThreePhaseRetryState()
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}
        patched_blueprint = {"ep_num": 8, "integrated_scenario": "patched"}
        blueprint_generator.runtime._run_pass_with_fix_loop = MagicMock(
            return_value=_ThreePhasePassWithFixResult(best_blueprint=patched_blueprint, should_continue=True)
        )

        result = blueprint_generator.runtime._resolve_retry_cycle_result(
            ep_num=8,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint={"end_location": "VIP룸"},
            best_blueprint={"ep_num": 8, "integrated_scenario": "candidate"},
            validation_result={
                "issues": [
                    {
                        "severity": "MAJOR",
                        "category": "opening_transition",
                        "issue": "opening_transition.type alias mismatch",
                    }
                ],
                "binding_prevalidation_issue_count": 1,
                "binding_prevalidation_categories": ["opening_transition"],
                "feedback": "opening transition alias normalization required",
                "fix_scope": "inplace",
                "fix_scope_reasoning": (
                    "Opening-transition alias mismatch is the sole binding category; "
                    "routing to inplace alias normalization instead of full regenerate."
                ),
            },
            verdict="PASS_WITH_FIX",
            score=91,
            selected_strategy="dialogue",
            director=MagicMock(),
            arc_idx=1,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            initial_feedback="opening transition alias normalization required",
            feedback="opening transition alias normalization required",
            retry_state=retry_state,
            pipeline_result=pipeline_result,
            retry=0,
            max_retries=9,
        )

        assert result.should_continue is True
        assert result.best_blueprint == patched_blueprint
        assert retry_state.prev_reject_origin == ""
        blueprint_generator.runtime._run_pass_with_fix_loop.assert_called_once()

    def test_refresh_phase3_validate_phase_after_reaudit_replaces_stale_binding_reason(self, blueprint_generator):
        pipeline_result = {
            "phases": {
                "validate": {
                    "selection_reason": "score strong (91.0); binding prevalidation repair required",
                    "verdict_reason": "score strong (91.0); binding prevalidation repair required",
                    "binding_prevalidation_issue_count": 1,
                    "binding_prevalidation_categories": ["opening_transition"],
                    "fix_scope": "inplace",
                    "candidate_count": 3,
                }
            }
        }

        blueprint_generator.runtime._refresh_phase3_validate_phase_after_reaudit(
            pipeline_result=pipeline_result,
            validation_result={
                "verdict": "PASS",
                "phase": "director",
                "issues": [],
                "score": 91,
                "confidence": 0.9,
                "selection_reason": "score strong (91.0)",
                "verdict_reason": "score strong (91.0)",
                "fix_scope": "",
                "fix_scope_reasoning": "",
                "quality_risk": False,
                "revision_required": False,
                "binding_prevalidation_issue_count": 0,
            },
        )

        validate_phase = pipeline_result["phases"]["validate"]
        assert validate_phase["selection_reason"] == "score strong (91.0)"
        assert validate_phase["verdict_reason"] == "score strong (91.0)"
        assert "binding_prevalidation_issue_count" not in validate_phase
        assert "binding_prevalidation_categories" not in validate_phase
        assert validate_phase["candidate_count"] == 3

    def test_run_phase3_validation_logs_quality_gate_reason(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import (
            _ThreePhaseRetryState,
            _ThreePhaseValidationEnvelope,
        )

        blueprint_generator._operator_log = MagicMock()
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}
        validation = _ThreePhaseValidationEnvelope(
            best_blueprint={"ep_num": 1},
            validation_result={
                "verdict_reason": "score는 통과선 아래라 재수정 필요",
                "issues": [{"severity": "HIGH", "category": "quality_gate", "issue": "score floor miss"}],
                "fix_scope": "inplace",
            },
            verdict="PASS",
            selected_strategy="balanced",
            score=89,
        )

        with (
            patch.object(blueprint_generator.runtime, "_maybe_reject_phase3_continuity", return_value=None),
            patch.object(blueprint_generator.runtime, "_run_phase3_validation_envelope", return_value=validation),
            patch.object(blueprint_generator.runtime, "_record_phase3_validation_payload"),
            patch.object(blueprint_generator.runtime, "_record_phase3_contradictions"),
            patch("modules.domain.agents.three_phase_blueprint_runtime._threshold", return_value=90),
        ):
            result = blueprint_generator.runtime._run_phase3_validation(
                ep_num=1,
                arc_data=sample_arc_data,
                constraint_block={},
                prev_blueprint=None,
                best_blueprint={"ep_num": 1},
                all_candidates=[{"ep_num": 1}],
                director=MagicMock(),
                arc_idx=0,
                entity_registry=None,
                state_tracker=None,
                db=None,
                prev_hud=None,
                retry_state=_ThreePhaseRetryState(),
                pipeline_result=pipeline_result,
                retry=0,
                max_retries=1,
            )

        log_texts = [call.args[0] for call in blueprint_generator._operator_log.call_args_list]
        assert result.verdict == "REJECT"
        assert result.validation_result["reject_origin"] == "quality_gate_reject"
        assert result.validation_result["quality_gate_effective_score"] == 89
        assert result.validation_result["director_verdict"] == "PASS"
        assert result.validation_result["runtime_route_verdict"] == "REJECT"
        assert result.validation_result["verdict_contract_version"] == "verdict-layer-v1"
        assert result.validation_result["final_judgment_authority"] == "director_llm"
        assert result.validation_result["runtime_gate_authority"] == "python_runtime_routing_gate"
        assert result.validation_result["runtime_gate_role"] == "route_or_block_automatic_progress"
        assert pipeline_result["phases"]["validate"]["director_verdict"] == "PASS"
        assert pipeline_result["phases"]["validate"]["runtime_route_verdict"] == "REJECT"
        assert pipeline_result["phases"]["validate"]["runtime_gate_basis"] == "quality_gate_reject"
        assert any("QualityGate" in text for text in log_texts)
        assert any("사유: score는 통과선 아래라 재수정 필요" in text for text in log_texts)
        assert any("fix_scope: inplace" in text for text in log_texts)
        assert any("이슈: HIGH | quality_gate | score floor miss" in text for text in log_texts)

    def test_run_phase3_validation_records_effective_score_after_ifc_penalty(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import (
            _ThreePhaseRetryState,
            _ThreePhaseValidationEnvelope,
        )

        blueprint_generator._operator_log = MagicMock()
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}
        validation = _ThreePhaseValidationEnvelope(
            best_blueprint={
                "ep_num": 1,
                "scene_breakdown": {
                    "scene_1": {"title": "도입", "goal": "상황 제시"},
                    "scene_2": {"title": "전개"},
                },
            },
            validation_result={
                "verdict_reason": "씬 메타가 부족해 handoff quality가 약함",
                "issues": [{"severity": "HIGH", "category": "ifc", "issue": "scene metadata incomplete"}],
                "fix_scope": "rewrite",
                "score": 91,
            },
            verdict="PASS",
            selected_strategy="balanced",
            score=91,
        )

        with (
            patch.object(blueprint_generator.runtime, "_maybe_reject_phase3_continuity", return_value=None),
            patch.object(blueprint_generator.runtime, "_run_phase3_validation_envelope", return_value=validation),
            patch.object(blueprint_generator.runtime, "_record_phase3_contradictions"),
            patch("modules.domain.agents.three_phase_blueprint_runtime._threshold", return_value=90),
        ):
            result = blueprint_generator.runtime._run_phase3_validation(
                ep_num=1,
                arc_data=sample_arc_data,
                constraint_block={},
                prev_blueprint=None,
                best_blueprint={"ep_num": 1},
                all_candidates=[{"ep_num": 1}],
                director=MagicMock(),
                arc_idx=0,
                entity_registry=None,
                state_tracker=None,
                db=None,
                prev_hud=None,
                retry_state=_ThreePhaseRetryState(),
                pipeline_result=pipeline_result,
                retry=0,
                max_retries=1,
            )

        assert result.verdict == "REJECT"
        assert result.score == 88
        assert pipeline_result["phases"]["validate"]["raw_score"] == 91
        assert pipeline_result["phases"]["validate"]["ifc_penalty"] == 3
        assert pipeline_result["phases"]["validate"]["effective_score"] == 88
        log_texts = [call.args[0] for call in blueprint_generator._operator_log.call_args_list]
        assert any("effective_score=88" in text for text in log_texts)

    def test_run_phase3_validation_promotes_terminal_quality_gate_warning(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import (
            _ThreePhaseRetryState,
            _ThreePhaseValidationEnvelope,
        )

        blueprint_generator._operator_log = MagicMock()
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}
        validation = _ThreePhaseValidationEnvelope(
            best_blueprint={"ep_num": 6, "scene_breakdown": {"scene_1": {"summary": "final"}}},
            validation_result={
                "verdict_reason": "score는 합격선 아래지만 치명 결함은 없음",
                "issues": [{"severity": "HIGH", "category": "quality_gate", "issue": "score floor miss"}],
                "fix_scope": "full",
                "score": 88,
            },
            verdict="PASS",
            selected_strategy="balanced",
            score=88,
        )

        with (
            patch.object(blueprint_generator.runtime, "_maybe_reject_phase3_continuity", return_value=None),
            patch.object(blueprint_generator.runtime, "_run_phase3_validation_envelope", return_value=validation),
            patch.object(blueprint_generator.runtime, "_record_phase3_contradictions"),
            patch("modules.domain.agents.three_phase_blueprint_runtime._threshold", return_value=90),
        ):
            result = blueprint_generator.runtime._run_phase3_validation(
                ep_num=6,
                arc_data=sample_arc_data,
                constraint_block={},
                prev_blueprint=None,
                best_blueprint={"ep_num": 6},
                all_candidates=[{"ep_num": 6}],
                director=MagicMock(),
                arc_idx=0,
                entity_registry=None,
                state_tracker=None,
                db=None,
                prev_hud=None,
                retry_state=_ThreePhaseRetryState(),
                pipeline_result=pipeline_result,
                retry=2,
                max_retries=2,
            )

        assert result.verdict == "PASS_WITH_WARNING"
        assert result.validation_result["quality_gate_terminal_acceptance"] is True
        assert result.validation_result["quality_gate_effective_score"] == 88
        assert pipeline_result["quality_gate_failed"] is True
        assert pipeline_result["quality_risk"] is True
        assert pipeline_result["revision_required"] is True
        assert result.validation_result["runtime_gate_authority"] == "python_runtime_routing_gate"
        assert pipeline_result["phases"]["validate"]["final_judgment_authority"] == "director_llm"
        assert pipeline_result["phases"]["validate"]["verdict"] == "PASS_WITH_WARNING"
        assert pipeline_result["phases"]["validate"]["quality_gate_terminal_acceptance"] == {
            "decision": "promote_to_pass_with_warning",
            "effective_score": 88,
            "quality_gate_score": 90,
            "raw_score": 88,
            "ifc_penalty": 0,
            "retry_index": 3,
            "max_retries": 3,
        }
        log_texts = [call.args[0] for call in blueprint_generator._operator_log.call_args_list]
        assert any("PASS_WITH_WARNING" in text for text in log_texts)

    def test_finalize_terminal_failure_uses_emergency_fallback(self, blueprint_generator):
        from modules.core.constants import PatchModeThresholds
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        retry_state = _ThreePhaseRetryState(
            prev_reject_score=PatchModeThresholds.REWRITE,
            prev_reject_feedback="latest feedback",
        )
        best_blueprint = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "fallback"}]}
        pipeline = {}

        result, resolved_pipeline = blueprint_generator.runtime._finalize_terminal_failure(
            ep_num=1,
            max_retries=2,
            pipeline_result=pipeline,
            retry_state=retry_state,
            best_blueprint=best_blueprint,
            director=MagicMock(),
            feedback="",
        )

        assert result is not None
        assert resolved_pipeline["final_verdict"] == "PASS_WITH_WARNING"
        assert resolved_pipeline["last_score"] == PatchModeThresholds.REWRITE

    def test_finalize_terminal_failure_blocks_emergency_fallback_with_binding_issue(
        self, blueprint_generator, tmp_path
    ):
        from modules.core.constants import PatchModeThresholds
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        blueprint_generator.context.current_project = MagicMock()
        blueprint_generator.context.current_project.paths.root = tmp_path
        retry_state = _ThreePhaseRetryState(
            prev_reject_score=PatchModeThresholds.REWRITE,
            prev_reject_feedback="latest feedback",
            prev_binding_issue_count=1,
        )
        best_blueprint = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "fallback"}]}
        pipeline = {
            "arc_no": 1,
            "phases": {
                "generate": {"selected_strategy": "steady"},
                "validate": {
                    "verdict": "PASS_WITH_FIX",
                    "director_verdict": "PASS",
                    "runtime_route_verdict": "PASS_WITH_FIX",
                    "binding_prevalidation_categories": ["arc_timeline"],
                },
            },
        }

        result, resolved_pipeline = blueprint_generator.runtime._finalize_terminal_failure(
            ep_num=1,
            max_retries=2,
            pipeline_result=pipeline,
            retry_state=retry_state,
            best_blueprint=best_blueprint,
            director=MagicMock(),
            feedback="",
        )

        assert result is None
        assert resolved_pipeline["final_verdict"] == "FAILED"
        assert resolved_pipeline["runtime_route_verdict"] == "REJECT"
        assert resolved_pipeline["runtime_gate_basis"] == "binding_prevalidation_reopen"
        assert resolved_pipeline["runtime_route_action"] == "block_artifact_adoption"
        assert resolved_pipeline["objective_status"] == "blocked_by_runtime_guard"
        assert resolved_pipeline["objective_success"] is False
        assert resolved_pipeline["objective_root_cause"] == "binding_prevalidation_unresolved"
        assert resolved_pipeline["final_verdict_authority"] == "compatibility_objective_status"
        diagnostic = resolved_pipeline["terminal_failure_diagnostic"]
        assert diagnostic["artifact_kind"] == "terminal_failure_diagnostic"
        assert diagnostic["official_artifact"] is False
        assert diagnostic["artifact_path"].endswith("terminal_failure_diagnostic__steady.json")
        diagnostic_path = tmp_path / diagnostic["artifact_path"]
        assert diagnostic_path.exists()
        payload = json.loads(diagnostic_path.read_text(encoding="utf-8"))
        assert payload["summary_role"] == "stage3_terminal_failure_diagnostic"
        assert payload["director_verdict"] == "PASS"
        assert payload["runtime_route_verdict"] == "REJECT"
        assert payload["binding_prevalidation_categories"] == ["arc_timeline"]
        assert payload["candidate_blueprint"] == best_blueprint

    def test_resolve_retry_cycle_result_accepts_direct_terminal_quality_gate_warning(self, blueprint_generator):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        pipeline_result = {"phases": {"generate": {}, "validate": {}}}

        result = blueprint_generator.runtime._resolve_retry_cycle_result(
            ep_num=6,
            arc_data={},
            constraint_block={},
            prev_blueprint=None,
            best_blueprint={"ep_num": 6, "scene_breakdown": {"scene_1": {"summary": "final"}}},
            validation_result={
                "quality_gate_terminal_acceptance": True,
                "quality_gate_effective_score": 88,
                "quality_gate_score": 90,
                "quality_gate_raw_score": 88,
                "fix_scope": "full",
            },
            verdict="PASS_WITH_WARNING",
            score=88,
            selected_strategy="balanced",
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            initial_feedback="",
            feedback="",
            retry_state=_ThreePhaseRetryState(),
            pipeline_result=pipeline_result,
            retry=2,
            max_retries=2,
        )

        assert result.final_result is not None
        _, resolved_pipeline = result.final_result
        assert resolved_pipeline["final_verdict"] == "PASS_WITH_WARNING"
        assert resolved_pipeline["quality_gate_failed"] is True
        assert resolved_pipeline["quality_risk"] is True
        assert resolved_pipeline["revision_required"] is True

    def test_schema_incompatible_failure_breaks_retry_loop(self, blueprint_generator, sample_arc_data):
        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.return_value = (None, [])
        blueprint_generator.ensemble.last_error_type = AgentErrorType.SCHEMA_INCOMPATIBLE

        result, pipeline = blueprint_generator.runtime.generate(
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

        result, pipeline = blueprint_generator.runtime.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=9,
        )

        assert result is None
        assert pipeline["final_verdict"] == "FAILED"
        assert pipeline["failure_reason"] == AgentErrorType.SCHEMA_INCOMPATIBLE
        assert pipeline["phases"]["generate"]["error_type"] == AgentErrorType.SCHEMA_INCOMPATIBLE

    def test_schema_incompatible_does_not_emergency_fallback_previous_best(self, blueprint_generator, sample_arc_data):
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

        result, pipeline = blueprint_generator.runtime.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=1,
            director=MagicMock(),
        )

        assert result is None
        assert pipeline["final_verdict"] == "FAILED"
        assert pipeline["failure_reason"] == AgentErrorType.SCHEMA_INCOMPATIBLE

    def test_candidate_disqualified_failure_retries_until_next_attempt_succeeds(
        self, blueprint_generator, sample_arc_data
    ):
        bp = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "retry success"}]}

        blueprint_generator.context.pass_rate_monitor = MagicMock()
        blueprint_generator.context.current_project = MagicMock(metrics_session_id="sess_stage3_candidate")
        blueprint_generator.constraint_compiler.compile.return_value = {}
        attempts = [(None, []), (bp, [bp])]

        def _set_candidate_disqualified(*args, **kwargs):
            if len(attempts) == 2:
                blueprint_generator.ensemble.last_error_type = AgentErrorType.CANDIDATE_DISQUALIFIED
                blueprint_generator.ensemble.last_error_types = [
                    AgentErrorType.CANDIDATE_DISQUALIFIED,
                    AgentErrorType.SCHEMA_INCOMPATIBLE,
                ]
            else:
                blueprint_generator.ensemble.last_error_type = None
                blueprint_generator.ensemble.last_error_types = []
            return attempts.pop(0)

        blueprint_generator.ensemble.generate_ensemble.side_effect = _set_candidate_disqualified
        blueprint_generator.validator.validate.return_value = (
            "PASS",
            {"score": 92, "issues": [], "confidence": 88},
        )

        result, pipeline = blueprint_generator.runtime.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=1,
        )

        assert result["ep_num"] == bp["ep_num"]
        assert result["scene_list"] == bp["scene_list"]
        assert pipeline["final_verdict"] == "PASS"
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 2

    def test_candidate_disqualified_plateau_breaks_retry_loop_early(self, blueprint_generator, sample_arc_data):
        blueprint_generator.context.pass_rate_monitor = MagicMock()
        blueprint_generator.context.current_project = MagicMock(metrics_session_id="sess_stage3_plateau")
        blueprint_generator.constraint_compiler.compile.return_value = {
            "episode_progression_packet": {
                "surface_guidance": [
                    "시작 anchor 계승은 짧게 처리하고 이번 화의 주 장면은 직전 대치의 결과 이후 단계로 이동하라."
                ]
            }
        }

        def _always_candidate_disqualified(*args, **kwargs):
            blueprint_generator.ensemble.last_error_type = AgentErrorType.CANDIDATE_DISQUALIFIED
            blueprint_generator.ensemble.last_error_types = [AgentErrorType.CANDIDATE_DISQUALIFIED]
            return None, []

        blueprint_generator.ensemble.generate_ensemble.side_effect = _always_candidate_disqualified

        result, pipeline = blueprint_generator.runtime.generate(
            ep_num=2,
            arc_data=sample_arc_data,
            max_retries=9,
            director=MagicMock(),
        )

        assert result is None
        assert pipeline["final_verdict"] == "FAILED"
        assert pipeline["reject_reason"] == "동일 replay/authority reroute guidance가 3회 연속 반복되어 조기 중단"
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 3
        assert pipeline["phases"]["generate"]["plateau_guard"]["triggered"] is True

    def test_candidate_disqualified_retry_switches_to_focus_strategy(self, blueprint_generator, sample_arc_data):
        bp2 = {
            "ep_num": 2,
            "scene_list": [{"scene_no": 1, "summary": "reroute 적용"}],
            "_ensemble_meta": {"strategy": "dialogue_focused"},
        }

        blueprint_generator.constraint_compiler.compile.return_value = {
            "episode_progression_packet": {
                "surface_guidance": [
                    "시작 anchor 계승은 짧게 처리하고 이번 화의 주 장면은 직전 대치의 결과 이후 단계로 이동하라."
                ]
            }
        }

        def _first_attempt(**kwargs):
            blueprint_generator.ensemble.last_error_type = AgentErrorType.CANDIDATE_DISQUALIFIED
            blueprint_generator.ensemble.last_error_types = [AgentErrorType.CANDIDATE_DISQUALIFIED]
            blueprint_generator.ensemble.last_disqualified_candidates = [
                {"strategy": "dialogue_focused", "scene_count": 3, "integrated_len": 620, "contract_reason": ""},
                {"strategy": "action_focused", "scene_count": 2, "integrated_len": 720, "contract_reason": ""},
            ]
            return None, []

        def _second_attempt(**kwargs):
            assert kwargs["single_strategy"] == "dialogue_focused"
            assert kwargs["rejected_strategy"] == "dialogue_focused"
            return bp2, [bp2]

        _attempts = {"count": 0}

        def _generate_ensemble_side_effect(**kwargs):
            _attempts["count"] += 1
            if _attempts["count"] == 1:
                return _first_attempt(**kwargs)
            return _second_attempt(**kwargs)

        blueprint_generator.ensemble.generate_ensemble.side_effect = _generate_ensemble_side_effect
        blueprint_generator.validator.validate.return_value = ("PASS", {"score": 94, "issues": [], "confidence": 89})

        result, pipeline = blueprint_generator.runtime.generate(
            ep_num=2,
            arc_data=sample_arc_data,
            max_retries=1,
            director=MagicMock(),
        )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 2
        second_kwargs = blueprint_generator.ensemble.generate_ensemble.call_args_list[1].kwargs
        assert second_kwargs["single_strategy"] == "dialogue_focused"
        assert second_kwargs["rejected_strategy"] == "dialogue_focused"

    def test_generate_failure_retry_records_intermediate_stage3_reject(self, blueprint_generator, sample_arc_data):
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

        result, pipeline = blueprint_generator.runtime.generate(
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

    def test_continuity_reject_retry_records_intermediate_stage3_reject(self, blueprint_generator, sample_arc_data):
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

        result, pipeline = blueprint_generator.runtime.generate(
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

    def test_continuity_reject_logs_operator_reason(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        blueprint_generator._operator_log = MagicMock()
        director = MagicMock()
        director.check_blueprint_continuity_with_cache.return_value = {
            "decision": "REJECT",
            "feedback": "opening continuity drift\nscene 1 location mismatch",
        }

        result = blueprint_generator.runtime._maybe_reject_phase3_continuity(
            ep_num=2,
            arc_data=sample_arc_data,
            best_blueprint={"ep_num": 2},
            director=director,
            db=MagicMock(),
            retry_state=_ThreePhaseRetryState(),
            retry=0,
            max_retries=1,
        )

        log_texts = [call.args[0] for call in blueprint_generator._operator_log.call_args_list]
        assert result is not None and result.should_continue is True
        assert any("연속성 검증 REJECT" in text for text in log_texts)
        assert any("사유: opening continuity drift" in text for text in log_texts)
        assert any("사유: scene 1 location mismatch" in text for text in log_texts)

    def test_validation_reject_retry_records_intermediate_stage3_reject(self, blueprint_generator, sample_arc_data):
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

        result, pipeline = blueprint_generator.runtime.generate(
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

    def test_validation_reject_logs_reason_issue_and_fix_scope(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        blueprint_generator._operator_log = MagicMock()
        blueprint_generator.runtime._handle_validation_reject(
            validation_result={
                "feedback": "director reject\nscene density too low",
                "issues": [{"severity": "HIGH", "category": "density", "issue": "scene 2 lacks action"}],
                "fix_scope": "inplace",
            },
            retry_state=_ThreePhaseRetryState(),
            score=55,
            selected_strategy="balanced",
            best_blueprint={"ep_num": 1},
            ep_num=1,
            arc_data=sample_arc_data,
            retry=0,
            max_retries=1,
        )

        log_texts = [call.args[0] for call in blueprint_generator._operator_log.call_args_list]
        assert any("[Phase 3] REJECT (score=55) - retry 1/2" in text for text in log_texts)
        assert any("fix_scope: inplace" in text for text in log_texts)
        assert any("사유: director reject" in text for text in log_texts)
        assert any("사유: scene density too low" in text for text in log_texts)
        assert any("이슈: HIGH | density | scene 2 lacks action" in text for text in log_texts)

    def test_apply_validation_reject_state_preserves_binding_regenerate_only_reason(self, blueprint_generator):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        retry_state = _ThreePhaseRetryState()

        blueprint_generator.runtime._apply_validation_reject_state(
            validation_result={
                "feedback": "structural reject",
                "issues": [],
                "fix_scope": "full",
                "binding_regenerate_only_reason": (
                    "Structural binding prevalidation requires regenerate-only repair: opening_anchor"
                ),
            },
            retry_state=retry_state,
            score=61,
            selected_strategy="balanced",
            best_blueprint={"ep_num": 1},
        )

        assert any(
            warning.startswith(
                "binding_regenerate_only: Structural binding prevalidation requires regenerate-only repair"
            )
            for warning in retry_state.prev_validation_warnings
        )

    def test_build_stage3_retry_feedback_payload_keeps_non_binding_critical_tail_when_binding_preferred(self):
        from modules.domain.agents.three_phase_blueprint_runtime import _build_stage3_retry_feedback_payload

        payload = _build_stage3_retry_feedback_payload(
            {
                "binding_regenerate_only_reason": "Structural binding prevalidation requires regenerate-only repair",
                "issues": [
                    {"severity": "CRITICAL", "category": "opening_anchor", "issue": "opening anchor drift"},
                    {"severity": "CRITICAL", "category": "scene_completeness", "issue": "scene 2 incomplete"},
                    {"severity": "CRITICAL", "category": "episode_progression", "issue": "replay drift"},
                    {"severity": "MAJOR", "category": "arc_timeline", "issue": "timeline exceeds arc"},
                    {"severity": "MAJOR", "category": "mission_clarity", "issue": "mission packet missing"},
                    {"severity": "MAJOR", "category": "protagonist_state", "issue": "state shell is empty"},
                    {
                        "severity": "CRITICAL",
                        "category": "temporal_deictic",
                        "issue": "ending hook invents a far-future memory anchor",
                    },
                ],
            },
            prefer_binding=True,
        )

        assert "binding_regenerate_only:" in payload
        assert "opening_anchor: opening anchor drift" in payload
        assert "arc_timeline: timeline exceeds arc" in payload
        assert "2006-01-15" in payload
        assert "temporal_deictic: ending hook invents a far-future memory anchor" in payload

    def test_apply_validation_reject_state_tracks_inplace_plateau_counters(self, blueprint_generator):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        retry_state = _ThreePhaseRetryState(
            prev_reject_score=66,
            prev_reject_signature="inplace|substantive|director",
            repeated_reject_score_streak=1,
            repeated_reject_signature_streak=1,
            inplace_reject_streak=1,
        )

        blueprint_generator.runtime._apply_validation_reject_state(
            validation_result={
                "feedback": "director reject",
                "issues": [{"category": "director", "issue": "below threshold"}],
                "fix_scope": "inplace",
            },
            retry_state=retry_state,
            score=66,
            selected_strategy="balanced",
            best_blueprint={"ep_num": 2},
        )

        assert retry_state.prev_reject_origin == "validation_reject"
        assert retry_state.repeated_reject_score_streak == 2
        assert retry_state.repeated_reject_signature_streak == 2
        assert retry_state.inplace_reject_streak == 2
        assert retry_state.prev_reject_signature == "inplace|substantive|director"
        assert any(
            "retry_plateau: inplace_score_plateau:66" in warning for warning in retry_state.prev_validation_warnings
        )
        assert any(
            "inplace_signature_plateau:inplace|substantive|director" in warning
            for warning in retry_state.prev_validation_warnings
        )

    def test_apply_validation_reject_state_emits_directive_block_with_allowed_values(self, blueprint_generator):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        retry_state = _ThreePhaseRetryState()

        blueprint_generator.runtime._apply_validation_reject_state(
            validation_result={
                "feedback": "generic reject",
                "issues": [
                    {
                        "category": "opening_transition",
                        "issue": "opening_transition.type mismatch: declared=scene_jump normalized=direct_continuation",
                    }
                ],
                "fix_scope": "full",
            },
            retry_state=retry_state,
            score=61,
            selected_strategy="balanced",
            best_blueprint={"ep_num": 2},
        )

        assert any(
            "allowed_values=[direct_continuation, explicit_transition, scene_jump]" in warning
            for warning in retry_state.prev_validation_warnings
        )

    def test_apply_validation_reject_state_leads_with_binding_directives_when_binding_origin(self, blueprint_generator):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        retry_state = _ThreePhaseRetryState()

        blueprint_generator.runtime._apply_validation_reject_state(
            validation_result={
                "feedback": "director praise should not lead",
                "issues": [
                    {
                        "category": "opening_transition",
                        "issue": "opening_transition.type mismatch: declared=scene_jump normalized=direct_continuation",
                    }
                ],
                "fix_scope": "full",
                "reject_origin": "pass_with_fix_unresolved",
                "binding_regenerate_only_reason": "binding issues require regenerate-only repair: opening_transition",
            },
            retry_state=retry_state,
            score=72,
            selected_strategy="balanced",
            best_blueprint={"ep_num": 2},
        )

        assert retry_state.prev_reject_feedback.startswith("binding_regenerate_only:")
        assert "director praise should not lead" not in retry_state.prev_reject_feedback

    def test_build_retry_strategy_feedback_omits_fix_scope_and_local_patch_gate_lines(self, blueprint_generator):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        retry_state = _ThreePhaseRetryState(
            prev_reject_feedback="retry this",
            prev_fix_scope="full",
            prev_local_patch_gate={
                "resolved_fix_scope": "full",
                "target_kind": "scene_block",
                "local_patch_ready": False,
                "reason": "missing_local_contract",
            },
            prev_validation_warnings=["opening_transition: retry with declared type"],
        )

        feedback = blueprint_generator.runtime._build_retry_strategy_feedback(retry_state)

        assert "[Director fix_scope]" not in feedback
        assert "[Local patch gate]" not in feedback
        assert "local_patch_gate:" not in feedback
        assert "[이전 검증 경고]" in feedback

    def test_apply_validation_reject_state_keeps_local_patch_gate_out_of_retry_warnings(self, blueprint_generator):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        retry_state = _ThreePhaseRetryState()
        ready_contract = _ready_stage3_local_contract()

        blueprint_generator.runtime._apply_validation_reject_state(
            validation_result={
                "feedback": "structural reject",
                "issues": [],
                "fix_scope": "inplace",
                "fix_pack": ready_contract["fix_pack"],
            },
            retry_state=retry_state,
            score=61,
            selected_strategy="balanced",
            best_blueprint={"ep_num": 1},
        )

        assert retry_state.prev_local_patch_gate["reason"] == "missing_authoritative_fix_scope"
        assert not any(warning.startswith("local_patch_gate:") for warning in retry_state.prev_validation_warnings)

    def test_apply_validation_reject_state_keeps_prev_selection_reason_blank_without_explicit_selection_reason(
        self, blueprint_generator
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        retry_state = _ThreePhaseRetryState()

        blueprint_generator.runtime._apply_validation_reject_state(
            validation_result={
                "feedback": "structural reject",
                "comparison_notes": "candidate B preserved continuity better",
                "summary": "legacy summary text",
                "issues": [],
                "fix_scope": "full",
            },
            retry_state=retry_state,
            score=61,
            selected_strategy="balanced",
            best_blueprint={"ep_num": 1},
        )

        assert retry_state.prev_selection_reason == ""

    def test_run_phase2_generation_blocks_inplace_after_pass_with_fix_unresolved(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        generated_blueprint = {"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "full regenerate"}]}
        ready_contract = _ready_stage3_local_contract()
        retry_state = _ThreePhaseRetryState(
            previous_best={"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "stale patch target"}]},
            prev_reject_score=66,
            prev_fix_scope="inplace",
            prev_reject_origin="pass_with_fix_unresolved",
            prev_fix_pack=ready_contract["fix_pack"],
            prev_repair_contract=ready_contract["repair_contract"],
            prev_scope_authority=ready_contract["scope_authority"],
        )
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})
        blueprint_generator.ensemble.generate_ensemble.return_value = (generated_blueprint, [generated_blueprint])
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}

        result = blueprint_generator.runtime._run_phase2_generation(
            retry=1,
            ep_num=2,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            prev_blueprints=None,
            protagonist_name="한시우",
            protagonist_config={},
            state_tracker=None,
            prev_manuscripts_text="",
            attempt_feedback="retry",
            strategy_feedback="",
            adversarial_self_play=None,
            pipeline_result=pipeline_result,
            retry_state=retry_state,
            max_retries=9,
        )

        assert result.best_blueprint == generated_blueprint
        assert pipeline_result["inplace_plateau_block_reasons"] == ["pass_with_fix_unresolved"]
        blueprint_generator._inplace_patch_blueprint.assert_not_called()
        blueprint_generator.ensemble.generate_ensemble.assert_called_once()

    def test_run_phase2_generation_blocks_repeated_inplace_score_plateau(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        generated_blueprint = {"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "full regenerate"}]}
        retry_state = _ThreePhaseRetryState(
            previous_best={"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "stale patch target"}]},
            prev_reject_score=66,
            prev_fix_scope="inplace",
            prev_reject_origin="validation_reject",
            prev_reject_signature="inplace|substantive|director",
            repeated_reject_score_streak=2,
            repeated_reject_signature_streak=2,
            inplace_reject_streak=2,
        )
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})
        blueprint_generator.ensemble.generate_ensemble.return_value = (generated_blueprint, [generated_blueprint])
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}

        result = blueprint_generator.runtime._run_phase2_generation(
            retry=1,
            ep_num=2,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            prev_blueprints=None,
            protagonist_name="한시우",
            protagonist_config={},
            state_tracker=None,
            prev_manuscripts_text="",
            attempt_feedback="retry",
            strategy_feedback="",
            adversarial_self_play=None,
            pipeline_result=pipeline_result,
            retry_state=retry_state,
            max_retries=9,
        )

        assert result.best_blueprint == generated_blueprint
        assert "inplace_score_plateau:66" in pipeline_result["inplace_plateau_block_reasons"]
        assert (
            "inplace_signature_plateau:inplace|substantive|director" in pipeline_result["inplace_plateau_block_reasons"]
        )
        blueprint_generator._inplace_patch_blueprint.assert_not_called()
        blueprint_generator.ensemble.generate_ensemble.assert_called_once()

    def test_run_phase2_generation_blocks_quality_gate_reopen(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        generated_blueprint = {"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "full regenerate"}]}
        ready_contract = _ready_stage3_local_contract()
        retry_state = _ThreePhaseRetryState(
            previous_best={"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "stale patch target"}]},
            prev_reject_score=88,
            prev_fix_scope="inplace",
            prev_reject_origin="quality_gate_reject",
            prev_fix_pack=ready_contract["fix_pack"],
            prev_repair_contract=ready_contract["repair_contract"],
            prev_scope_authority=ready_contract["scope_authority"],
        )
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})
        blueprint_generator.ensemble.generate_ensemble.return_value = (generated_blueprint, [generated_blueprint])
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}

        result = blueprint_generator.runtime._run_phase2_generation(
            retry=1,
            ep_num=2,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            prev_blueprints=None,
            protagonist_name="한시우",
            protagonist_config={},
            state_tracker=None,
            prev_manuscripts_text="",
            attempt_feedback="retry",
            strategy_feedback="",
            adversarial_self_play=None,
            pipeline_result=pipeline_result,
            retry_state=retry_state,
            max_retries=9,
        )

        assert result.best_blueprint == generated_blueprint
        assert pipeline_result["inplace_plateau_block_reasons"] == ["quality_gate_reopen"]
        blueprint_generator._inplace_patch_blueprint.assert_not_called()
        blueprint_generator.ensemble.generate_ensemble.assert_called_once()

    def test_run_phase2_generation_blocks_quality_gate_reopen_when_origin_is_missing(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        generated_blueprint = {"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "full regenerate"}]}
        ready_contract = _ready_stage3_local_contract()
        retry_state = _ThreePhaseRetryState(
            previous_best={"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "stale patch target"}]},
            prev_reject_score=88,
            prev_fix_scope="inplace",
            prev_reject_origin="",
            prev_quality_gate_reject=True,
            prev_fix_pack=ready_contract["fix_pack"],
            prev_repair_contract=ready_contract["repair_contract"],
            prev_scope_authority=ready_contract["scope_authority"],
        )
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})
        blueprint_generator.ensemble.generate_ensemble.return_value = (generated_blueprint, [generated_blueprint])
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}

        result = blueprint_generator.runtime._run_phase2_generation(
            retry=1,
            ep_num=2,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            prev_blueprints=None,
            protagonist_name="test-protagonist",
            protagonist_config={},
            state_tracker=None,
            prev_manuscripts_text="",
            attempt_feedback="retry",
            strategy_feedback="",
            adversarial_self_play=None,
            pipeline_result=pipeline_result,
            retry_state=retry_state,
            max_retries=9,
        )

        assert result.best_blueprint == generated_blueprint
        assert pipeline_result["inplace_plateau_block_reasons"] == ["quality_gate_reopen"]
        blueprint_generator._inplace_patch_blueprint.assert_not_called()
        blueprint_generator.ensemble.generate_ensemble.assert_called_once()

    def test_run_phase2_generation_blocks_binding_prevalidation_reopen(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        generated_blueprint = {"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "full regenerate"}]}
        ready_contract = _ready_stage3_local_contract()
        retry_state = _ThreePhaseRetryState(
            previous_best={"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "stale patch target"}]},
            prev_reject_score=84,
            prev_fix_scope="inplace",
            prev_reject_origin="validation_reject",
            prev_binding_issue_count=2,
            prev_fix_pack=ready_contract["fix_pack"],
            prev_repair_contract=ready_contract["repair_contract"],
            prev_scope_authority=ready_contract["scope_authority"],
        )
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})
        blueprint_generator.ensemble.generate_ensemble.return_value = (generated_blueprint, [generated_blueprint])
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}

        result = blueprint_generator.runtime._run_phase2_generation(
            retry=1,
            ep_num=2,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            prev_blueprints=None,
            protagonist_name="한시우",
            protagonist_config={},
            state_tracker=None,
            prev_manuscripts_text="",
            attempt_feedback="retry",
            strategy_feedback="",
            adversarial_self_play=None,
            pipeline_result=pipeline_result,
            retry_state=retry_state,
            max_retries=9,
        )

        assert result.best_blueprint == generated_blueprint
        assert pipeline_result["inplace_plateau_block_reasons"] == ["binding_prevalidation_reopen:2"]
        blueprint_generator._inplace_patch_blueprint.assert_not_called()
        blueprint_generator.ensemble.generate_ensemble.assert_called_once()

    def test_run_phase2_generation_blocks_contract_unsupported_target_kind(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        generated_blueprint = {"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "full regenerate"}]}
        retry_state = _ThreePhaseRetryState(
            previous_best={"ep_num": 2, "scene_list": [{"scene_no": 1, "summary": "stale scene model patch"}]},
            prev_reject_score=84,
            prev_fix_scope="inplace",
            prev_reject_origin="validation_reject",
            prev_fix_pack={
                "patch_targets": ["scene_breakdown.scene_4"],
                "target_kind": "scene_model",
            },
            prev_repair_contract={
                "fix_scope": "inplace",
                "repair_scope": "inplace",
                "authoritative_fix_scope": "inplace",
                "target_kind": "scene_model",
            },
            prev_scope_authority={
                "fix_scope": "inplace",
                "repair_scope": "inplace",
                "authoritative_fix_scope": "inplace",
                "widened": False,
            },
        )
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})
        blueprint_generator.ensemble.generate_ensemble.return_value = (generated_blueprint, [generated_blueprint])
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}

        result = blueprint_generator.runtime._run_phase2_generation(
            retry=1,
            ep_num=2,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            prev_blueprints=None,
            protagonist_name="한시우",
            protagonist_config={},
            state_tracker=None,
            prev_manuscripts_text="",
            attempt_feedback="retry",
            strategy_feedback="",
            adversarial_self_play=None,
            pipeline_result=pipeline_result,
            retry_state=retry_state,
            max_retries=9,
        )

        assert result.best_blueprint == generated_blueprint
        assert pipeline_result["inplace_plateau_block_reasons"] == [
            "local_patch_contract:unsupported_target_kind:scene_model"
        ]
        blueprint_generator._inplace_patch_blueprint.assert_not_called()
        blueprint_generator.ensemble.generate_ensemble.assert_called_once()

    def test_pass_with_fix_patch_failure_logs_patch_context(self, blueprint_generator, sample_arc_data):
        blueprint_generator._operator_log = MagicMock()
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value=None)
        current_validation = {"fix_scope": "inplace", "feedback": "scene 3 tension up\nrestore anchor"}
        current_validation.update(
            _ready_stage3_local_contract(
                patch_target="scene_3.summary",
                scene_id="scene_3",
                field_path="scene_breakdown.scene_3.summary",
                patch_target_id="scene_3.summary",
                must_fix="scene 3 summary must restore the dropped anchor",
                success_condition="scene 3 now restores the anchor without rewriting the arc shell",
            )
        )

        result = blueprint_generator.runtime._run_pass_with_fix_iteration(
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            current_blueprint={"ep_num": 1},
            current_validation=current_validation,
            pipeline_result={"phases": {"generate": {}, "validate": {}}},
            score=82,
            quality_gate_score=90,
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            fix_index=0,
            max_fix=3,
        )

        log_texts = [call.args[0] for call in blueprint_generator._operator_log.call_args_list]
        assert result.should_break is True
        assert any("[TF-32-V] Blueprint patch #1/3" in text for text in log_texts)
        assert any("fix_scope: inplace" in text for text in log_texts)
        assert any("사유: [Stage3 partial-fix contract]" in text for text in log_texts)
        assert any("사유: authoritative_scope:" in text for text in log_texts)
        assert any("[TF-32-V] patch #1 failed" in text for text in log_texts)

    def test_pass_with_fix_iteration_escalates_structural_binding_categories_to_full_regenerate(
        self, blueprint_generator, sample_arc_data
    ):
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})

        result = blueprint_generator.runtime._run_pass_with_fix_iteration(
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            current_blueprint={"ep_num": 1},
            current_validation={
                "fix_scope": "inplace",
                "feedback": "restore opening anchor",
                "binding_prevalidation_categories": ["opening_anchor", "scenario_density"],
            },
            pipeline_result={"phases": {"generate": {}, "validate": {}}},
            score=88,
            quality_gate_score=90,
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            fix_index=0,
            max_fix=3,
        )

        assert result.should_break is True
        assert result.current_validation["fix_scope"] == "full"
        assert result.current_validation["binding_regenerate_only_categories"] == ["opening_anchor"]
        assert "opening_anchor" in result.current_validation["binding_regenerate_only_reason"]
        assert "opening_anchor" in result.current_validation["fix_scope_reasoning"]
        blueprint_generator._inplace_patch_blueprint.assert_not_called()

    def test_pass_with_fix_iteration_escalates_episode_progression_to_full_regenerate(
        self, blueprint_generator, sample_arc_data
    ):
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})

        result = blueprint_generator.runtime._run_pass_with_fix_iteration(
            ep_num=3,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            current_blueprint={"ep_num": 3},
            current_validation={
                "fix_scope": "inplace",
                "feedback": "stop replaying prior-episode scenes",
                "binding_prevalidation_categories": ["episode_progression", "scenario_density"],
            },
            pipeline_result={"phases": {"generate": {}, "validate": {}}},
            score=91,
            quality_gate_score=90,
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            fix_index=0,
            max_fix=3,
        )

        assert result.should_break is True
        assert result.current_validation["fix_scope"] == "full"
        assert result.current_validation["binding_regenerate_only_categories"] == ["episode_progression"]
        assert "episode_progression" in result.current_validation["binding_regenerate_only_reason"]
        blueprint_generator._inplace_patch_blueprint.assert_not_called()

    def test_pass_with_fix_iteration_escalates_arc_timeline_to_full_regenerate(
        self, blueprint_generator, sample_arc_data
    ):
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})

        result = blueprint_generator.runtime._run_pass_with_fix_iteration(
            ep_num=7,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            current_blueprint={"ep_num": 7},
            current_validation={
                "fix_scope": "inplace",
                "feedback": "align ending timeline",
                "binding_prevalidation_categories": ["arc_timeline"],
                "binding_prevalidation_issue_count": 1,
            },
            pipeline_result={"phases": {"generate": {}, "validate": {}}},
            score=85,
            quality_gate_score=90,
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            fix_index=0,
            max_fix=3,
        )

        assert result.should_break is True
        assert result.current_validation["fix_scope"] == "full"
        assert result.current_validation["binding_regenerate_only_categories"] == ["arc_timeline"]
        assert "arc_timeline" in result.current_validation["binding_regenerate_only_reason"]
        blueprint_generator._inplace_patch_blueprint.assert_not_called()

    def test_pass_with_fix_iteration_escalates_contract_blocked_scene_model_to_full_regenerate(
        self, blueprint_generator, sample_arc_data
    ):
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})

        result = blueprint_generator.runtime._run_pass_with_fix_iteration(
            ep_num=4,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            current_blueprint={"ep_num": 4},
            current_validation={
                "fix_scope": "inplace",
                "feedback": "repair only scene 4 shell",
                "fix_pack": {
                    "patch_targets": ["scene_breakdown.scene_4"],
                    "target_kind": "scene_model",
                },
                "repair_contract": {
                    "fix_scope": "inplace",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "target_kind": "scene_model",
                },
                "scope_authority": {
                    "fix_scope": "inplace",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "widened": False,
                },
            },
            pipeline_result={"phases": {"generate": {}, "validate": {}}},
            score=88,
            quality_gate_score=90,
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            fix_index=0,
            max_fix=3,
        )

        assert result.should_break is True
        assert result.current_validation["fix_scope"] == "full"
        assert result.current_validation["local_patch_gate"]["reason"] == "unsupported_target_kind:scene_model"
        assert "Contract-driven local patch gate blocked" in result.current_validation["fix_scope_reasoning"]
        blueprint_generator._inplace_patch_blueprint.assert_not_called()

    def test_pass_with_fix_iteration_reaudits_normalized_opening_transition_alias_without_patch(
        self, blueprint_generator, sample_arc_data
    ):
        current_blueprint = {
            "episode_number": 8,
            "opening_transition": {"type": "explicit_transition"},
            "scene_breakdown": {
                "scene_1": {
                    "title": "VIP룸",
                    "location": "한미증권 청담동 지점 15층 VIP룸",
                    "summary": "박성호가 자리에 앉는다.",
                }
            },
        }
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})
        blueprint_generator.validator.validate.return_value = (
            "PASS",
            {
                "score": 95,
                "issues": [],
                "confidence": 91,
                "binding_prevalidation_issue_count": 0,
            },
        )

        result = blueprint_generator.runtime._run_pass_with_fix_iteration(
            ep_num=8,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint={"end_location": "한미증권 청담동 지점 15층 VIP룸"},
            current_blueprint=current_blueprint,
            current_validation={
                "fix_scope": "inplace",
                "fix_scope_reasoning": (
                    "Opening-transition alias mismatch is the sole binding category; "
                    "routing to inplace alias normalization instead of full regenerate."
                ),
                "feedback": "opening_transition.type을 continuity contract에 맞게 정규화",
                "binding_prevalidation_issue_count": 1,
                "binding_prevalidation_categories": ["opening_transition"],
            },
            pipeline_result={"phases": {"generate": {}, "validate": {}}},
            score=88,
            quality_gate_score=90,
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            fix_index=0,
            max_fix=3,
        )

        assert result.fix_ok is True
        assert result.patch_attempted is False
        assert result.current_blueprint == current_blueprint
        assert result.current_validation["verdict"] == "PASS"
        assert result.current_validation["binding_prevalidation_issue_count"] == 0
        assert result.current_validation["local_patch_gate"]["reason"] == "missing_local_contract"
        blueprint_generator._inplace_patch_blueprint.assert_not_called()

    def test_pass_with_fix_iteration_appends_fix_pack_guidance_and_partial_fix_eval(
        self, blueprint_generator, sample_arc_data
    ):
        blueprint_generator._inplace_patch_blueprint = MagicMock(
            return_value={
                "ep_num": 1,
                "scene_breakdown": {
                    "scene_1": {"summary": "opening"},
                    "scene_2": {"summary": "repaired"},
                },
            }
        )
        blueprint_generator.validator.validate.return_value = (
            "PASS",
            {"score": 95, "issues": [], "confidence": 91},
        )
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}

        result = blueprint_generator.runtime._run_pass_with_fix_iteration(
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            current_blueprint={
                "ep_num": 1,
                "scene_breakdown": {
                    "scene_1": {"summary": "opening"},
                    "scene_2": {"summary": "old"},
                },
            },
            current_validation={
                "fix_scope": "inplace",
                "feedback": "tighten scene 2 summary",
                **_ready_stage3_local_contract(),
            },
            pipeline_result=pipeline_result,
            score=84,
            quality_gate_score=90,
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            fix_index=0,
            max_fix=3,
        )

        assert result.fix_ok is True
        patch_feedback = blueprint_generator._inplace_patch_blueprint.call_args.kwargs["director_feedback"]
        assert patch_feedback.startswith("[Stage3 partial-fix contract]")
        assert "scene_2.summary" in patch_feedback
        assert "authoritative_scope" in patch_feedback
        assert "anchor=repaired reveal" in patch_feedback
        assert "scene 2 summary must reflect the repaired reveal" in patch_feedback
        assert pipeline_result["phases"]["validate"]["fix_pack"]["target_kind"] == "scene_block"
        assert pipeline_result["phases"]["validate"]["fix_pack"]["subtype"] == "movement"
        assert pipeline_result["phases"]["validate"]["repair_contract"]["subtype"] == "movement"
        assert pipeline_result["phases"]["validate"]["repair_contract"]["provenance"] == "director_authored"
        assert pipeline_result["phases"]["validate"]["scope_authority"]["widened"] is False
        assert pipeline_result["phases"]["validate"]["partial_fix_eval"]["patch_round"] == 1
        assert pipeline_result["phases"]["validate"]["partial_fix_eval"]["target_kind"] == "scene_block"
        assert pipeline_result["phases"]["validate"]["partial_fix_eval"]["must_fix_resolved"] is True
        assert pipeline_result["phases"]["validate"]["partial_fix_eval"]["success_condition_met"] is True

    def test_pass_with_fix_iteration_preserves_low_score_pass_for_retry(self, blueprint_generator, sample_arc_data):
        patched_blueprint = {
            "ep_num": 1,
            "scene_breakdown": {
                "scene_1": {"summary": "opening"},
                "scene_2": {"summary": "improved"},
            },
        }
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value=patched_blueprint)
        blueprint_generator.validator.validate.return_value = (
            "PASS",
            {"score": 85, "issues": [], "confidence": 90},
        )

        result = blueprint_generator.runtime._run_pass_with_fix_iteration(
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            current_blueprint={
                "ep_num": 1,
                "scene_breakdown": {
                    "scene_1": {"summary": "opening"},
                    "scene_2": {"summary": "old"},
                },
            },
            current_validation={
                "fix_scope": "inplace",
                "feedback": "tighten scene 2 summary",
                **_ready_stage3_local_contract(),
            },
            pipeline_result={"phases": {"generate": {}, "validate": {}}},
            score=95,
            quality_gate_score=90,
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            fix_index=0,
            max_fix=3,
        )

        assert result.should_break is True
        assert result.current_blueprint == patched_blueprint
        assert result.current_validation["score"] == 85
        assert result.current_validation["verdict"] == "PASS"

    def test_pass_with_fix_iteration_preserves_advisory_only_low_score_pass(self, blueprint_generator, sample_arc_data):
        patched_blueprint = {
            "ep_num": 1,
            "scene_breakdown": {
                "scene_1": {"summary": "opening"},
                "scene_2": {"summary": "improved"},
            },
        }
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value=patched_blueprint)
        blueprint_generator.validator.validate.return_value = (
            "PASS",
            {
                "score": 85,
                "issues": [
                    {
                        "category": "scenario_density",
                        "issue": "앵커가 얇음",
                        "advisory_only": True,
                        "director_focus": False,
                    }
                ],
                "confidence": 90,
                "binding_prevalidation_issue_count": 0,
                "quality_risk": False,
            },
        )

        result = blueprint_generator.runtime._run_pass_with_fix_iteration(
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            current_blueprint={
                "ep_num": 1,
                "scene_breakdown": {
                    "scene_1": {"summary": "opening"},
                    "scene_2": {"summary": "old"},
                },
            },
            current_validation={
                "fix_scope": "inplace",
                "feedback": "tighten scene 2 summary",
                **_ready_stage3_local_contract(),
            },
            pipeline_result={"phases": {"generate": {}, "validate": {}}},
            score=95,
            quality_gate_score=90,
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            fix_index=0,
            max_fix=3,
        )

        assert result.fix_ok is True
        assert result.current_blueprint == patched_blueprint
        assert result.current_validation["quality_gate_soft_override"] is True

    def test_pass_with_fix_iteration_uses_advisory_fix_pack_when_hard_fix_pack_absent(
        self, blueprint_generator, sample_arc_data
    ):
        patched_blueprint = {
            "ep_num": 1,
            "scene_breakdown": {
                "scene_1": {"summary": "opening"},
                "scene_2": {"summary": "improved"},
            },
        }
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value=patched_blueprint)
        blueprint_generator.validator.validate.return_value = (
            "PASS",
            {"score": 94, "issues": [], "confidence": 90},
        )
        pipeline_result = {"phases": {"generate": {}, "validate": {}}}

        result = blueprint_generator.runtime._run_pass_with_fix_iteration(
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            current_blueprint={
                "ep_num": 1,
                "scene_breakdown": {
                    "scene_1": {"summary": "opening"},
                    "scene_2": {"summary": "old"},
                },
            },
            current_validation={
                "fix_scope": "inplace",
                "feedback": "tighten scene 2 summary",
                "advisory_fix_pack": {
                    "patch_targets": ["integrated_scenario"],
                    "patch_target_records": [
                        {
                            "summary": "integrated_scenario",
                            "field_path": "integrated_scenario",
                            "target_kind": "local_sentence",
                        }
                    ],
                    "must_fix": ["add one named market anchor"],
                    "do_not_regress": ["keep the opening move"],
                    "success_condition": "integrated scenario adds one named market anchor",
                    "evidence_summary": "anchor_count=0",
                },
                "repair_contract": {
                    "fix_scope": "inplace",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "target_kind": "local_sentence",
                },
                "scope_authority": {
                    "fix_scope": "inplace",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "widened": False,
                },
            },
            pipeline_result=pipeline_result,
            score=84,
            quality_gate_score=90,
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            fix_index=0,
            max_fix=3,
        )

        assert result.fix_ok is True
        patch_feedback = blueprint_generator._inplace_patch_blueprint.call_args.kwargs["director_feedback"]
        assert patch_feedback.startswith("[Stage3 partial-fix contract]")
        assert "integrated_scenario" in patch_feedback
        assert "anchor_count=0" in patch_feedback
        assert pipeline_result["phases"]["validate"]["advisory_fix_pack"]["target_kind"] == "local_sentence"
        assert pipeline_result["phases"]["validate"]["partial_fix_eval"]["target_kind"] == "local_sentence"

    def test_pass_with_fix_iteration_blocks_missing_success_condition(self, blueprint_generator, sample_arc_data):
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value={"unexpected": True})
        current_validation = {
            "fix_scope": "inplace",
            "feedback": "tighten scene 2 summary",
            **_ready_stage3_local_contract(),
        }
        current_validation["fix_pack"].pop("success_condition")

        result = blueprint_generator.runtime._run_pass_with_fix_iteration(
            ep_num=1,
            arc_data=sample_arc_data,
            constraint_block={},
            prev_blueprint=None,
            current_blueprint={"ep_num": 1},
            current_validation=current_validation,
            pipeline_result={"phases": {"generate": {}, "validate": {}}},
            score=84,
            quality_gate_score=90,
            director=MagicMock(),
            arc_idx=0,
            entity_registry=None,
            state_tracker=None,
            prev_hud=None,
            fix_index=0,
            max_fix=3,
        )

        assert result.should_break is True
        assert result.current_validation["fix_scope"] == "full"
        assert result.current_validation["local_patch_gate"]["reason"] == "missing_success_condition"
        blueprint_generator._inplace_patch_blueprint.assert_not_called()

    def test_finalize_pass_with_fix_failure_adopts_low_score_pass_blueprint(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        original_blueprint = {"ep_num": 1, "scene_breakdown": {"scene_1": {"summary": "old"}}}
        patched_blueprint = {"ep_num": 1, "scene_breakdown": {"scene_1": {"summary": "improved"}}}
        retry_state = _ThreePhaseRetryState()
        blueprint_generator._record_intermediate_reject = MagicMock()
        blueprint_generator.runtime._apply_validation_reject_state = MagicMock()

        result = blueprint_generator.runtime._finalize_pass_with_fix_failure(
            best_blueprint=original_blueprint,
            current_blueprint=patched_blueprint,
            current_validation={"verdict": "PASS", "score": 85, "feedback": "needs stronger polish", "issues": []},
            validation_result={"score": 95},
            score=95,
            selected_strategy="balanced",
            initial_feedback="initial feedback",
            max_fix=3,
            retry_state=retry_state,
            ep_num=1,
            arc_data=sample_arc_data,
            retry=0,
            max_retries=1,
        )

        assert result.should_continue is True
        assert result.best_blueprint == patched_blueprint

    def test_finalize_pass_with_fix_failure_uses_route_honest_message_before_patch(
        self, blueprint_generator, sample_arc_data
    ):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        retry_state = _ThreePhaseRetryState()
        blueprint_generator._record_intermediate_reject = MagicMock()
        blueprint_generator.runtime._apply_validation_reject_state = MagicMock()

        blueprint_generator.runtime._finalize_pass_with_fix_failure(
            best_blueprint={"ep_num": 1},
            current_blueprint={"ep_num": 1},
            current_validation={
                "verdict": "PASS_WITH_FIX",
                "score": 85,
                "feedback": "binding residual remained",
                "issues": [],
                "fix_scope": "full",
                "binding_regenerate_only_reason": "binding issues require regenerate",
            },
            validation_result={"score": 85},
            score=85,
            selected_strategy="balanced",
            initial_feedback="initial feedback",
            max_fix=3,
            executed_patch_attempts=0,
            retry_state=retry_state,
            ep_num=1,
            arc_data=sample_arc_data,
            retry=0,
            max_retries=1,
        )

        assert "rerouted before local patch" in retry_state.prev_reject_feedback

    def test_finalize_pass_with_fix_failure_reports_executed_patch_attempts(self, blueprint_generator, sample_arc_data):
        from modules.domain.agents.three_phase_blueprint_runtime import _ThreePhaseRetryState

        retry_state = _ThreePhaseRetryState()
        blueprint_generator._record_intermediate_reject = MagicMock()
        blueprint_generator.runtime._apply_validation_reject_state = MagicMock()

        blueprint_generator.runtime._finalize_pass_with_fix_failure(
            best_blueprint={"ep_num": 1},
            current_blueprint={"ep_num": 1},
            current_validation={
                "verdict": "PASS_WITH_FIX",
                "score": 85,
                "feedback": "still weak",
                "issues": [],
                "fix_scope": "inplace",
            },
            validation_result={"score": 85},
            score=85,
            selected_strategy="balanced",
            initial_feedback="initial feedback",
            max_fix=3,
            executed_patch_attempts=1,
            retry_state=retry_state,
            ep_num=1,
            arc_data=sample_arc_data,
            retry=0,
            max_retries=1,
        )

        assert "after 1 executed local patch attempt" in retry_state.prev_reject_feedback
        apply_kwargs = blueprint_generator.runtime._apply_validation_reject_state.call_args.kwargs
        assert apply_kwargs["score"] == 85
        assert apply_kwargs["best_blueprint"] == {"ep_num": 1}

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

        result, pipeline = blueprint_generator.runtime.generate(
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
        ready_contract = _ready_stage3_local_contract()

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),  # retry 0: 정상 생성
        ]
        blueprint_generator.ensemble.ask.return_value = "{}"
        blueprint_generator.ensemble._extract_json_robust.return_value = bp_patched

        blueprint_generator.validator.validate.side_effect = [
            ("REJECT", {"score": 65, "feedback": "밀도 부족", "issues": [], **ready_contract}),
            ("PASS", {"score": 95, "issues": [], "confidence": 90}),
        ]

        result, pipeline = blueprint_generator.runtime.generate(
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
        ready_contract = _ready_stage3_local_contract()

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),  # retry 0
            (bp2, [bp2]),  # retry 1 same-attempt full rewrite fallback
        ]
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value=None)
        blueprint_generator.validator.validate.side_effect = [
            ("REJECT", {"score": 65, "feedback": "로컬 수정만으론 부족", "issues": [], **ready_contract}),
            ("PASS", {"score": 93, "issues": [], "confidence": 87}),
        ]

        result, pipeline = blueprint_generator.runtime.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=1,
        )

        assert result is not None
        assert result["scene_list"][0]["summary"] == "풀 리라이트 재생성"
        assert pipeline["final_verdict"] == "PASS"
        inplace_call = blueprint_generator._inplace_patch_blueprint.call_args.kwargs
        assert inplace_call["original_blueprint"] == bp1
        assert inplace_call["director_feedback"].startswith("[Stage3 partial-fix contract]")
        assert "로컬 수정만으론 부족" in inplace_call["director_feedback"]
        assert inplace_call["ep_num"] == 1
        assert inplace_call["arc_data"] == sample_arc_data
        normalized_fix_pack = inplace_call["normalized_fix_pack"]
        assert normalized_fix_pack["patch_targets"] == ready_contract["fix_pack"]["patch_targets"]
        assert normalized_fix_pack["must_fix"] == ready_contract["fix_pack"]["must_fix"]
        assert normalized_fix_pack["success_condition"] == ready_contract["fix_pack"]["success_condition"]
        assert normalized_fix_pack["target_kind"] == ready_contract["fix_pack"]["target_kind"]
        record = normalized_fix_pack["patch_target_records"][0]
        expected = ready_contract["fix_pack"]["patch_target_records"][0]
        assert record["field_path"] == expected["field_path"]
        assert record["scene_id"] == expected["scene_id"]
        assert record["target_kind"] == expected["target_kind"]
        assert record["summary"] == expected["summary"]
        assert record["patch_target_id"].startswith("pt:")
        assert blueprint_generator.ensemble.generate_ensemble.call_count == 2
        fallback_kwargs = blueprint_generator.ensemble.generate_ensemble.call_args_list[1].kwargs
        assert fallback_kwargs["fix_pack"]["must_fix"] == ready_contract["fix_pack"]["must_fix"]
        assert fallback_kwargs["repair_contract"]["target_kind"] == ready_contract["repair_contract"]["target_kind"]
        assert fallback_kwargs["attempt_num"] == 2

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

        result, pipeline = blueprint_generator.runtime.generate(
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
                "binding_prevalidation_issue_count": 1,
                "binding_prevalidation_categories": ["dead_npc"],
                "candidate_count": 1,
                "selected_candidate_advisory": {
                    "candidate_index": 0,
                    "quality_risk": False,
                },
            },
        )

        result, pipeline = blueprint_generator.runtime.generate(
            ep_num=1,
            arc_data=sample_arc_data,
            max_retries=0,
        )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        assert bool(pipeline.get("quality_risk", False)) is False
        assert pipeline["revision_required"] is True
        assert pipeline["phases"]["validate"]["revision_required"] is True
        assert pipeline["phases"]["validate"]["binding_prevalidation_issue_count"] == 1
        assert pipeline["phases"]["validate"]["binding_prevalidation_categories"] == ["dead_npc"]

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

        result, pipeline = blueprint_generator.runtime.generate(
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

        result, pipeline = blueprint_generator.runtime.generate(
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
        ready_contract = _ready_stage3_local_contract()

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.side_effect = [
            (bp1, [bp1]),  # retry 0
        ]
        blueprint_generator.ensemble.ask.return_value = "{}"
        blueprint_generator.ensemble._extract_json_robust.return_value = bp_patched

        blueprint_generator.validator.validate.side_effect = [
            ("REJECT", {"score": 60, "feedback": "감정선 보완 필요", "issues": [], **ready_contract}),
            ("PASS", {"score": 91, "issues": [], "confidence": 87}),
        ]

        result, pipeline = blueprint_generator.runtime.generate(
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

        result, pipeline = blueprint_generator.runtime.generate(
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
        assert second_kwargs["attempt_num"] == 2

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

        result, pipeline = blueprint_generator.runtime.generate(
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
        assert second_kwargs["attempt_num"] == 2

    def test_pass_with_fix_high_change_ratio_is_warning_only(self, blueprint_generator, sample_arc_data, caplog):
        """Stage 3 F-2는 high change ratio에서도 warning-only로 남고 PASS를 막지 않는다."""
        bp1 = {"ep_num": 1, "scene_list": [{"scene_no": 1}], "emotion_curve": "기존"}
        bp_patched = {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "수정됨"}], "emotion_curve": "수정됨"}

        blueprint_generator.constraint_compiler.compile.return_value = {}
        blueprint_generator.ensemble.generate_ensemble.return_value = (bp1, [bp1])
        blueprint_generator._inplace_patch_blueprint = MagicMock(return_value=bp_patched)
        ready_contract = _ready_stage3_local_contract()
        blueprint_generator.validator.validate.side_effect = [
            (
                "PASS_WITH_FIX",
                {
                    "score": 84,
                    "feedback": "로컬 보강",
                    "fix_scope": "inplace",
                    "issues": [],
                    **ready_contract,
                },
            ),
            ("PASS", {"score": 92, "issues": [], "confidence": 90}),
        ]

        with (
            patch("modules.core.constants.calc_patch_change_ratio", return_value=0.75),
            patch("modules.core.constants.log_patch_diff"),
            caplog.at_level("WARNING"),
        ):
            result, pipeline = blueprint_generator.runtime.generate(
                ep_num=1,
                arc_data=sample_arc_data,
                max_retries=0,
            )

        assert result is not None
        assert pipeline["final_verdict"] == "PASS"
        blueprint_generator._inplace_patch_blueprint.assert_called_once()
        assert "[F-2] InPlace Blueprint" in caplog.text
        assert "75.0% > 30%" in caplog.text

    # ── [IFC] Scene obligation completeness enforcement ──

    def test_enforce_scene_obligation_completeness_zero_missing(self, blueprint_generator):
        bp = {"scene_breakdown": {"scene_1": {"title": "A", "goal": "G1"}, "scene_2": {"title": "B", "summary": "S2"}}}
        penalty = blueprint_generator.runtime._enforce_scene_obligation_completeness(bp)
        assert penalty == 0

    def test_enforce_scene_obligation_completeness_one_missing(self, blueprint_generator):
        bp = {"scene_breakdown": {"scene_1": {"title": "A", "goal": "G1"}, "scene_2": {"title": "B"}}}
        blueprint_generator._operator_log = MagicMock()
        penalty = blueprint_generator.runtime._enforce_scene_obligation_completeness(bp)
        assert penalty == 3
        blueprint_generator._operator_log.assert_called_once()

    def test_enforce_scene_obligation_completeness_majority_missing(self, blueprint_generator):
        bp = {"scene_breakdown": {"scene_1": {"title": "A"}, "scene_2": {"title": "B"}, "scene_3": {"title": "C"}}}
        blueprint_generator._operator_log = MagicMock()
        penalty = blueprint_generator.runtime._enforce_scene_obligation_completeness(bp)
        assert penalty == 9  # 3 * 3

    def test_enforce_scene_obligation_completeness_cap_at_15(self, blueprint_generator):
        bp = {"scene_breakdown": {f"scene_{i}": {"title": f"S{i}"} for i in range(10)}}
        blueprint_generator._operator_log = MagicMock()
        penalty = blueprint_generator.runtime._enforce_scene_obligation_completeness(bp)
        assert penalty == 15  # capped

    def test_enforce_scene_obligation_completeness_none_blueprint(self, blueprint_generator):
        assert blueprint_generator.runtime._enforce_scene_obligation_completeness(None) == 0

    def test_enforce_scene_obligation_completeness_empty_scenes(self, blueprint_generator):
        assert blueprint_generator.runtime._enforce_scene_obligation_completeness({"scene_breakdown": {}}) == 0
