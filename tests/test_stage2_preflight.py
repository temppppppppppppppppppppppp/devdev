"""[B-1-8] Unit tests for Stage2PreflightAnalysis extracted from Stage2Orchestrator."""

import concurrent.futures
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.context_advisor import RetrievalPlan, RetrievalSlot
from modules.core.stage2_preflight import Stage2PreflightAnalysis


@pytest.fixture
def preflight_ctx():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.audit_event = MagicMock()

    weaver = MagicMock()
    weaver.generate_arc_drive.return_value = {"desire_vector": "grow", "status": "ok"}

    preflight_agent = MagicMock()
    preflight_agent.analyze.return_value = {
        "item_timeline": [1],
        "absolute_prohibitions": [],
        "relationship_map": {"A": 1},
    }
    preflight_agent.generate_analyst_injection.return_value = "preflight injection"

    state_extractor = MagicMock()
    state_extractor.extract_cumulative_state.return_value = {"entity_registry": {"npc": {"role": "ally"}}}

    four_phase = MagicMock()
    four_phase.generate.return_value = (None, {"final_verdict": "REJECT", "phases": {"validate": {"issues_count": 1}}})

    ctx.agents = {
        "weaver": weaver,
        "preflight": preflight_agent,
        "state_extractor": state_extractor,
        "four_phase": four_phase,
    }

    tracker = MagicMock()
    tracker.get_resolved_plots_summary.return_value = "resolved"
    tracker.resolved_plots = []
    ctx.state_tracker = tracker

    ctx.constraint_compiler = None
    ctx.cumulative_state_cache = None
    ctx.cumulative_state_cache_key = 0

    ctx.quality_dashboard = None
    ctx.stage2_optimizer = None
    ctx.quality_amplifier = None
    ctx.agent_intelligence = None
    ctx.failure_learner = None
    ctx.constitutional_checker = None
    ctx.stage_rejection_history = []
    ctx.generate_reverse_feedback_stage3_to_2 = MagicMock(return_value="reverse")
    ctx.build_minimal_arc_context = MagicMock(return_value="minimal context")
    ctx.fix_entity_registry_protagonist = MagicMock(side_effect=lambda registry, _name: registry)

    ctx.memory = None
    ctx.context_advisor = None
    ctx.semantic_plot_guard = None
    ctx.current_project = MagicMock()

    return ctx


@pytest.fixture
def preflight(preflight_ctx):
    host = MagicMock()
    host.ctx = preflight_ctx
    return Stage2PreflightAnalysis(host)


def _state_setup_kwargs(**overrides):
    defaults = {
        "all_refined_arcs": [],
        "arcs_source": [{"arc_no": 1}],
        "arc_idx": 0,
        "lack_report": {"lack": []},
        "grand_obj": "goal",
        "global_arc_no": 1,
        "constraint_db": MagicMock(generate_constraint_block=MagicMock(return_value="block")),
    }
    defaults.update(overrides)
    return defaults


def _arc_analysis_kwargs(**overrides):
    defaults = {
        "attempt": 0,
        "current_feedback": "",
        "constraint_block": "constraint block",
        "last_refined_context": "last context",
        "all_refined_arcs": [],
        "protagonist_name": "hero",
        "global_arc_no": 1,
        "cached_preflight_injection": "cached inj",
        "cached_preflight_result": {"k": 1},
    }
    defaults.update(overrides)
    return defaults


def _enrichment_kwargs(**overrides):
    defaults = {
        "attempt": 0,
        "global_arc_no": 1,
        "current_ep_start": 1,
        "current_vol_strategy": {"strategy_doc": "doc"},
        "enriched_block": {"block_theme": "theme", "joint_docs": {}, "status_shadow": {}},
        "all_refined_arcs": [],
        "bible_root": {"AssetLibrary": {}},
        "protagonist_name": "hero",
        "director_feedback_for_fourphase": "",
        "entity_registry_for_director": {},
        "genre_for_tracker": "wuxia",
    }
    defaults.update(overrides)
    return defaults


class TestPreflightStructure:
    def test_init_requires_host_for_ctx(self):
        p = Stage2PreflightAnalysis(None)
        with pytest.raises(AttributeError):
            _ = p.ctx

    def test_ctx_proxy(self, preflight, preflight_ctx):
        assert preflight.ctx is preflight_ctx

    def test_methods_exist(self, preflight):
        assert hasattr(preflight, "_preflight_state_setup")
        assert hasattr(preflight, "_preflight_arc_analysis")
        assert hasattr(preflight, "_preflight_enrichment")
        assert hasattr(preflight, "_build_stage3_to_2_reverse_feedback_fallback")

    def test_runtime_attached(self, preflight):
        from modules.core.stage2_preflight_runtime import Stage2PreflightRuntime

        assert isinstance(preflight.runtime, Stage2PreflightRuntime)

    def test_preflight_arc_analysis_wrapper_delegates_to_runtime(self, preflight):
        expected = {
            "refined_arc": None,
            "generation_method": "analyst",
            "constraint_block": "constraint block",
            "entity_registry_for_director": {"hero": {"role": "lead"}},
            "narrative_enriched": True,
        }
        preflight.runtime.preflight_arc_analysis = MagicMock(return_value=expected)

        out = preflight._preflight_arc_analysis(**_arc_analysis_kwargs())

        assert out == expected
        preflight.runtime.preflight_arc_analysis.assert_called_once_with(**_arc_analysis_kwargs())

    def test_preflight_enrichment_wrapper_delegates_to_runtime(self, preflight):
        expected = {
            "four_phase_passed": False,
            "refined_arc": None,
            "generation_method": "analyst",
            "draft_validator_passed": False,
            "consensus_passed": False,
            "st_snapshot": None,
            "director_feedback_for_fourphase": "retry",
            "was_patch": False,
            "patch_fallback": False,
            "prev_score": 0,
        }
        preflight.runtime.preflight_enrichment = MagicMock(return_value=expected)

        out = preflight._preflight_enrichment(**_enrichment_kwargs())

        assert out == expected
        preflight.runtime.preflight_enrichment.assert_called_once_with(
            **_enrichment_kwargs(),
            previous_attempt=None,
        )


class TestStage3To2Fallback:
    def test_stage3_reverse_feedback_fallback_includes_reasons_and_details(self, preflight):
        result = preflight._build_stage3_to_2_reverse_feedback_fallback(
            [
                {"reason": "설정 충돌", "specific_issue": "장면 3에서 위치 불일치"},
                {"reason": "설정 충돌"},
                {"reason": "반복 전개"},
            ],
            4,
            status="callback_missing",
        )

        assert "callback_missing" in result
        assert "설정 충돌" in result
        assert "장면 3에서 위치 불일치" in result


class TestPreflightStateSetup:
    def test_returns_all_required_keys(self, preflight):
        out = preflight._preflight_state_setup(**_state_setup_kwargs())
        required = {
            "arc_drive",
            "cached_preflight_injection",
            "cached_preflight_result",
            "passed",
            "current_feedback",
            "constraint_block",
            "attempt",
            "max_attempts",
            "director_feedback_for_fourphase",
            "st_snapshot",
        }
        assert required == set(out.keys())

    def test_parallel_execution_runs_both_tasks(self, preflight):
        out = preflight._preflight_state_setup(**_state_setup_kwargs(all_refined_arcs=[{"arc_no": 0}]))
        preflight.ctx.agents["weaver"].generate_arc_drive.assert_called_once()
        preflight.ctx.agents["preflight"].analyze.assert_called_once()
        assert out["cached_preflight_injection"] == "preflight injection"

    def test_weaver_error_returns_error_drive(self, preflight):
        preflight.ctx.agents["weaver"].generate_arc_drive.side_effect = RuntimeError("boom")
        out = preflight._preflight_state_setup(**_state_setup_kwargs())
        assert out["arc_drive"]["status"] == "error"
        preflight.ctx.audit_event.assert_called()

    def test_compute_arc_drive_returns_error_payload_and_audit_event(self, preflight):
        preflight.ctx.agents["weaver"].generate_arc_drive.side_effect = RuntimeError("boom")

        out = preflight._compute_arc_drive(
            arcs_source=[{"arc_no": 1}],
            arc_idx=0,
            lack_report={"lack": []},
            grand_obj="goal",
            global_arc_no=1,
            perf_lock=threading.Lock(),
        )

        assert out["status"] == "error"
        preflight.ctx.audit_event.assert_called()

    def test_constraint_compiler_integration(self, preflight):
        compiler = MagicMock()
        compiler.compile.return_value = "compiled constraints"
        preflight.ctx.constraint_compiler = compiler

        out = preflight._preflight_state_setup(**_state_setup_kwargs(all_refined_arcs=[{"arc_no": 0}]))
        assert "compiled constraints" in out["constraint_block"]

    def test_apply_constraint_compiler_block_compiles_and_indexes_resolved_plots(self, preflight):
        compiler = MagicMock()
        compiler.compile.return_value = "compiled constraints"
        preflight.ctx.constraint_compiler = compiler
        preflight.ctx.state_tracker.resolved_plots = ["plot-a", "plot-b"]
        preflight.ctx.semantic_plot_guard = MagicMock()

        out = preflight._apply_constraint_compiler_block(
            all_refined_arcs=[{"arc_no": 0}],
            constraint_block="block",
        )

        assert out.startswith("compiled constraints")
        preflight.ctx.semantic_plot_guard.index_resolved_plots.assert_called_once_with(["plot-a", "plot-b"])

    def test_state_extractor_exception_non_propagating(self, preflight):
        preflight.ctx.constraint_compiler = MagicMock(compile=MagicMock(return_value="compiled"))
        preflight.ctx.agents["state_extractor"].extract_cumulative_state.side_effect = RuntimeError("err")

        out = preflight._preflight_state_setup(**_state_setup_kwargs(all_refined_arcs=[{"arc_no": 0}]))
        assert isinstance(out, dict)
        preflight.ctx.audit_event.assert_called()

    def test_extract_constraint_compiler_state_reuses_cache(self, preflight):
        preflight.ctx.cumulative_state_cache = {"cached": True}
        preflight.ctx.cumulative_state_cache_key = 2

        out = preflight._extract_constraint_compiler_state(all_refined_arcs=[{"arc_no": 0}, {"arc_no": 1}])

        assert out == {"cached": True}
        preflight.ctx.agents["state_extractor"].extract_cumulative_state.assert_not_called()

    def test_parallel_timeout_uses_nonblocking_shutdown(self, preflight):
        class _FakeFuture:
            def __init__(self, value=None, error=None):
                self._value = value
                self._error = error

            def result(self, timeout=None):  # noqa: ARG002 - 테스트 더블 시그니처 호환
                if self._error:
                    raise self._error
                return self._value

        class _FakeExecutor:
            instances = []

            def __init__(self, *args, **kwargs):  # noqa: ARG002 - 테스트 더블 시그니처 호환
                self.shutdown_calls = []
                _FakeExecutor.instances.append(self)

            def submit(self, fn, *args, **kwargs):  # noqa: ARG002 - 테스트 더블 시그니처 호환
                if fn.__name__ == "_compute_arc_drive":
                    return _FakeFuture(error=concurrent.futures.TimeoutError("timeout"))
                if fn.__name__ == "_compute_preflight":
                    return _FakeFuture(value=("", {}))
                if fn.__name__ == "_compute_constraint_block":
                    return _FakeFuture(value="")
                return _FakeFuture(value=None)

            def shutdown(self, wait=True, cancel_futures=False):
                self.shutdown_calls.append((wait, cancel_futures))

        with patch("modules.core.stage2_preflight.concurrent.futures.ThreadPoolExecutor", _FakeExecutor):
            out = preflight._preflight_state_setup(**_state_setup_kwargs(all_refined_arcs=[{"arc_no": 0}]))

        assert isinstance(out, dict)
        assert _FakeExecutor.instances
        shutdown_calls = _FakeExecutor.instances[-1].shutdown_calls
        assert any((wait is False and cancel is True) for wait, cancel in shutdown_calls)


class TestPreflightArcAnalysis:
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_returns_all_required_keys(self, preflight):
        out = preflight._preflight_arc_analysis(**_arc_analysis_kwargs())
        required = {
            "refined_arc",
            "generation_method",
            "constraint_block",
            "entity_registry_for_director",
            "narrative_enriched",  # [TF-3T-A]
        }
        assert required == set(out.keys())

    def test_build_patch_feedback_merges_selection_score_warnings_and_fix_scope(self, preflight):
        result = preflight._build_patch_feedback(
            {
                "rejection_reason": "keep structure, fix only local issue",
                "selection_reason": "candidate 2 was closest",
                "score_breakdown": {"coherence": 8, "density": 7.5, "note": "skip"},
                "validation_warnings": ["minor drift", 123, "continuity watch"],
                "fix_scope_reasoning": "local continuity delta only",
            }
        )

        assert "keep structure, fix only local issue" in result
        assert "[선택/거절 사유]" in result
        assert "candidate 2 was closest" in result
        assert "[점수 분해]" in result
        assert "coherence=8" in result
        assert "density=7.5" in result
        assert "note=skip" not in result
        assert "[검증 경고]" in result
        assert "- minor drift" in result
        assert "- continuity watch" in result
        assert "[수정 범위 근거]" in result
        assert "local continuity delta only" in result

    def test_build_patch_feedback_defaults_to_rejection_reason_only(self, preflight):
        result = preflight._build_patch_feedback({"rejection_reason": "retry arc"})

        assert result == "retry arc"

    def test_resolve_patch_mode_for_inplace_scope(self, preflight):
        result = preflight._resolve_patch_mode({"best_arc": {"arc_no": 1}, "fix_scope": "inplace", "score": 95})

        assert result.fix_scope == "inplace"
        assert result.prev_score == 95
        assert result.has_best_arc is True
        assert result.use_inplace is True
        assert result.use_patch is True
        assert result.was_patch is True

    def test_resolve_patch_mode_for_partial_scope(self, preflight):
        result = preflight._resolve_patch_mode({"best_arc": {"arc_no": 1}, "fix_scope": "partial", "score": 81})

        assert result.fix_scope == "partial"
        assert result.use_inplace is False
        assert result.use_patch is True
        assert result.was_patch is True

    def test_resolve_patch_mode_without_scope_disables_local_patch(self, preflight):
        result = preflight._resolve_patch_mode({"best_arc": {"arc_no": 1}, "fix_scope": "", "score": 90})

        assert result.fix_scope == ""
        assert result.has_best_arc is True
        assert result.use_inplace is False
        assert result.use_patch is False
        assert result.was_patch is False

    def test_apply_retry_focus_mode_noops_for_first_attempt(self, preflight):
        result = preflight._apply_retry_focus_mode(
            attempt=0,
            current_feedback="",
            constraint_block="constraint",
            cached_preflight_injection="cached inj",
            all_refined_arcs=[{"arc_no": 1}],
            protagonist_name="hero",
            enhanced_context="base context",
        )

        assert result == "base context"
        preflight.ctx.build_minimal_arc_context.assert_not_called()

    def test_apply_retry_focus_mode_preserves_constraints_and_cached_preflight(self, preflight):
        result = preflight._apply_retry_focus_mode(
            attempt=1,
            current_feedback="fix this",
            constraint_block="constraint block",
            cached_preflight_injection="cached inj",
            all_refined_arcs=[{"arc_no": 1}],
            protagonist_name="hero",
            enhanced_context="base context",
        )

        assert result.startswith("fix this")
        assert "constraint block" in result
        assert "cached inj" in result
        assert "minimal context" in result
        preflight.ctx.build_minimal_arc_context.assert_called_once_with([{"arc_no": 1}], "hero")

    def test_build_stage2_vector_context_legacy_path_prepends_slot_summary_and_fact_ledger(self, preflight):
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_high_res_context.return_value = "legacy vector block"
        preflight._resolve_work_retrieval_focus = MagicMock(return_value={"tracking_slots": ["핵심 배우 라인"]})
        preflight._build_work_identity_slot_summary = MagicMock(
            return_value="[작품 추적 슬롯 요약]\n핵심 배우 라인"
        )
        preflight._build_fact_ledger_context = MagicMock(return_value="[팩트 저장 요약]\n수치")
        preflight._record_retrieval_observation = MagicMock()

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return False
            if key == "smart_retrieval.stage2_enabled":
                return False
            if key == "context.vector_max_results_s2":
                return 8
            return default

        with patch("modules.core.stage2_preflight._threshold", side_effect=threshold_side_effect):
            result = preflight._build_stage2_vector_context(
                global_arc_no=1,
                current_ep_start=3,
                enriched_block={"block_theme": "theme", "joint_docs": {}, "status_shadow": {}},
                current_vol_strategy={"strategy_doc": "doc"},
                protagonist_name="hero",
            )

        assert result.startswith("[작품 추적 슬롯 요약]")
        assert "[팩트 저장 요약]" in result
        assert "legacy vector block" in result
        preflight.ctx.memory.retrieve_high_res_context.assert_called_once_with("theme", 3, n_results=8)
        preflight._record_retrieval_observation.assert_called_once()
        observation = preflight._record_retrieval_observation.call_args.kwargs["observation"]
        assert observation["advisor_path_used"] is False
        assert observation["work_slot_summary_included"] is True
        assert observation["vector_context_chars"] == len(result)

    def test_build_stage2_vector_context_logs_when_retrieval_is_empty(self, preflight):
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_high_res_context.return_value = ""
        preflight._resolve_work_retrieval_focus = MagicMock(return_value={})
        preflight._build_work_identity_slot_summary = MagicMock(return_value="")
        preflight._build_fact_ledger_context = MagicMock(return_value="")
        preflight._record_retrieval_observation = MagicMock()

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return False
            if key == "smart_retrieval.stage2_enabled":
                return False
            if key == "context.vector_max_results_s2":
                return 8
            return default

        with patch("modules.core.stage2_preflight._threshold", side_effect=threshold_side_effect):
            result = preflight._build_stage2_vector_context(
                global_arc_no=1,
                current_ep_start=3,
                enriched_block={"block_theme": "theme", "joint_docs": {}, "status_shadow": {}},
                current_vol_strategy={"strategy_doc": "doc"},
                protagonist_name="hero",
            )

        assert result == ""
        preflight.ctx.ui.log.assert_any_call(
            "      [S2-OBS] Stage2 retrieval empty (chars=0, slots=0, scene_engines=0)"
        )

    def test_resolve_work_retrieval_focus_returns_fallback_when_guard_missing(self, preflight):
        preflight.ctx.sys = None

        result = preflight._resolve_work_retrieval_focus(
            {
                "block_theme": "유가 급등을 이용한 자산 불리기",
                "constraint_summary": "소꿉친구와의 관계 복구가 필요하다",
                "plot_suspension": ["PB 박성호와의 신뢰 회복"],
                "episode_details": [
                    {"ep_num": 4, "details": ["PB 박성호를 설득해 원유 익절 타이밍을 잡는다."]}
                ],
            },
            current_vol_strategy={"strategy_doc": "단기 유가 변동을 활용한 포지션 정리"},
        )

        assert result["tracking_slots"] == [
            "유가 급등을 이용한 자산 불리기",
            "PB 박성호와의 신뢰 회복",
            "소꿉친구와의 관계 복구가 필요하다",
        ]
        assert result["mandatory_scene_engines"][0].startswith("EP4:")

    def test_resolve_work_retrieval_focus_uses_raw_block_metadata_when_mission_packet_missing(self, preflight):
        preflight.ctx.sys = None

        result = preflight._resolve_work_retrieval_focus(
            {
                "content": {
                    "context": "2006년 1월 초, 한시우는 강남 사무실에서 원유 진입 시점을 계산한다.",
                    "event_villain": "PB 박성호는 아직 막내의 선언을 재롱으로 본다.",
                    "solution": "해외 선물 계좌와 법인 구조를 먼저 잠근다.",
                    "reward": "20억 운용 준비와 초기 법인 설립이 완료된다.",
                },
                "stakes": "이번 선언이 실패하면 회귀 지식도 모두 무의미해진다.",
                "foreshadow": ["이란 핵 이슈 재점화", "WTI 랠리 초입"],
                "relationship_delta": [
                    {"target": "박성호", "after": "경계", "trigger": "막내의 돌연한 선언"}
                ],
                "time_span": {"in_story_time": "2006년 1월 초", "duration": "3일"},
                "location": {"place": "서울 강남 대표실", "type": "실내"},
                "genre_ext": {
                    "method": "원자재 트레이딩 준비",
                    "time_pressure": "이란 핵 이슈 전 포지션 진입 준비",
                },
            },
            current_vol_strategy={"strategy_doc": "원유 진입 전 계좌와 법인을 먼저 잠근다."},
        )

        assert result["tracking_slots"]
        assert "이번 선언이 실패하면 회귀 지식도 모두 무의미해진다." in result["tracking_slots"]
        assert result["mandatory_scene_engines"]
        assert any("원유 진입 시점" in item for item in result["mandatory_scene_engines"])

    def test_build_stage2_vector_context_uses_fallback_work_focus_summary_when_guard_returns_empty(self, preflight):
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_high_res_context.return_value = ""
        preflight.ctx.sys = MagicMock()
        preflight.ctx.sys.guard = MagicMock()
        preflight.ctx.sys.guard.select_retrieval_focus.return_value = {}
        preflight._build_fact_ledger_context = MagicMock(return_value="")
        preflight._record_retrieval_observation = MagicMock()

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return False
            if key == "smart_retrieval.stage2_enabled":
                return False
            if key == "context.vector_max_results_s2":
                return 8
            return default

        with patch("modules.core.stage2_preflight._threshold", side_effect=threshold_side_effect):
            result = preflight._build_stage2_vector_context(
                global_arc_no=1,
                current_ep_start=3,
                enriched_block={
                    "block_theme": "유가 급등",
                    "constraint_summary": "여의도 사무실에서 다음 거래를 준비한다",
                    "episode_details": [{"ep_num": 4, "details": ["PB를 만나 다음 거래 조건을 조율한다."]}],
                    "joint_docs": {},
                    "status_shadow": {},
                },
                current_vol_strategy={"strategy_doc": "단기 포지션 정리"},
                protagonist_name="hero",
            )

        assert result.startswith("[작품 추적 슬롯 요약]")
        observation = preflight._record_retrieval_observation.call_args.kwargs["observation"]
        assert observation["work_focus_present"] is True
        assert observation["work_slot_summary_included"] is True
        assert observation["tracking_slots_count"] >= 1

    def test_build_stage2_vector_context_uses_raw_block_fallback_when_guard_returns_empty(self, preflight):
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_high_res_context.return_value = ""
        preflight.ctx.sys = MagicMock()
        preflight.ctx.sys.guard = MagicMock()
        preflight.ctx.sys.guard.select_retrieval_focus.return_value = {}
        preflight._build_fact_ledger_context = MagicMock(return_value="")
        preflight._record_retrieval_observation = MagicMock()

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return False
            if key == "smart_retrieval.stage2_enabled":
                return False
            if key == "context.vector_max_results_s2":
                return 8
            return default

        with patch("modules.core.stage2_preflight._threshold", side_effect=threshold_side_effect):
            result = preflight._build_stage2_vector_context(
                global_arc_no=2,
                current_ep_start=6,
                enriched_block={
                    "content": {
                        "context": "여의도 사무실에서 다음 원유 트레이드 타이밍을 계산한다.",
                        "event_villain": "PB는 여전히 막내의 판단을 의심한다.",
                    },
                    "stakes": "이번 타이밍을 놓치면 첫 수익 증명이 무너진다.",
                    "foreshadow": ["에콰도르 변수", "유가 급등 시작"],
                    "relationship_delta": [{"target": "박성호", "after": "경계"}],
                    "time_span": {"in_story_time": "2006년 2월 초"},
                    "location": {"place": "여의도 사무실", "type": "실내"},
                    "joint_docs": {},
                    "status_shadow": {},
                },
                current_vol_strategy={"strategy_doc": "원유 진입 직전 리스크를 정리한다."},
                protagonist_name="hero",
            )

        assert result.startswith("[작품 추적 슬롯 요약]")
        observation = preflight._record_retrieval_observation.call_args.kwargs["observation"]
        assert observation["work_focus_present"] is True
        assert observation["tracking_slots_count"] >= 1
        assert observation["scene_engines_count"] >= 1

    def test_apply_postpass_state_change_fixes_merges_relationship_delta_and_timeline(self, preflight):
        refined_arc = {
            "state_changes": {},
            "state_constraints": {
                "arc_start_state": {"equipment": []},
                "arc_end_state": {"equipment": ["청월검"]},
            },
        }
        enriched_block = {
            "relationship_delta": [
                {
                    "target": "연홍",
                    "before": "동료",
                    "after": "불신",
                    "trigger": "오해",
                    "justification": "거짓 보고",
                }
            ],
            "time_span": {"in_story_time": "사흘 뒤"},
        }

        result = preflight._apply_postpass_state_change_fixes(
            refined_arc=refined_arc,
            enriched_block=enriched_block,
        )

        assert result["state_changes"]["timeline"] == {"start": "사흘 뒤", "end": "사흘 뒤"}
        rel = result["state_changes"]["relationship_changes"][0]
        assert rel["npc"] == "연홍"
        assert rel["from"] == "동료"
        assert rel["to"] == "불신"
        assert rel["trigger"] == "오해"
        assert rel["justification"] == "거짓 보고"
        assert rel["episode"] is None

    def test_apply_postpass_state_change_fixes_updates_existing_relationship_without_overwriting_timeline(
        self, preflight
    ):
        refined_arc = {
            "state_changes": {
                "timeline": {"start": "당일", "end": "당일"},
                "relationship_changes": [{"npc": "연홍", "from": "동료", "to": "불신"}],
            },
            "state_constraints": {},
        }
        enriched_block = {
            "relationship_delta": [
                {
                    "target": "연홍",
                    "before": "동료",
                    "after": "불신",
                    "trigger": "오해",
                    "justification": "거짓 보고",
                }
            ],
            "time_span": {"in_story_time": "사흘 뒤"},
        }

        result = preflight._apply_postpass_state_change_fixes(
            refined_arc=refined_arc,
            enriched_block=enriched_block,
        )

        assert result["state_changes"]["timeline"] == {"start": "당일", "end": "당일"}
        rel = result["state_changes"]["relationship_changes"][0]
        assert rel["trigger"] == "오해"
        assert rel["justification"] == "거짓 보고"
        assert len(result["state_changes"]["relationship_changes"]) == 1

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_focus_mode_on_retry(self, preflight):
        out = preflight._preflight_arc_analysis(
            **_arc_analysis_kwargs(attempt=1, current_feedback="fix this", constraint_block="")
        )
        assert out["generation_method"] == "analyst"
        preflight.ctx.build_minimal_arc_context.assert_called_once()

    def test_focus_mode_fallback_source_preserves_recent_tail_context(self):
        src = Path("modules/core/stage2_preflight.py").read_text(encoding="utf-8")
        assert "enhanced_context[:15000]" not in src
        assert "smart_truncate(" in src
        assert "enhanced_context, max_chars=15000, head_chars=8250" in src

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_quality_trend_injected(self, preflight):
        preflight.ctx.quality_dashboard = MagicMock()
        preflight.ctx.quality_dashboard.get_score_trend_summary.return_value = {
            "trend": "up",
            "summary": "최근 추세 상승",
        }
        out = preflight._preflight_arc_analysis(**_arc_analysis_kwargs(constraint_block=""))
        preflight.ctx.quality_dashboard.get_score_trend_summary.assert_called_once_with(stage=2)
        assert "enhanced_context" not in out

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_constraint_compiler_sets_entity_registry(self, preflight):
        preflight.ctx.constraint_compiler = MagicMock(compile=MagicMock(return_value="cc"))
        out = preflight._preflight_arc_analysis(**_arc_analysis_kwargs(all_refined_arcs=[{"arc_no": 1}]))
        # [Sweep48] constraint_block은 입력값 그대로 보존 (setup에서 이미 병합됨)
        assert out["constraint_block"] == "constraint block"
        assert out["entity_registry_for_director"] == {"npc": {"role": "ally"}}

    def test_prepare_analyst_weapons_combines_cached_preflight_and_constraint_payload(self, preflight):
        from modules.core.stage2_preflight import Stage2AnalystWeaponsPayload

        preflight.ctx.constraint_compiler = MagicMock(compile=MagicMock(return_value="compiled constraints"))

        payload = preflight.runtime.prepare_analyst_weapons(
            all_refined_arcs=[{"arc_no": 1}],
            cached_preflight_result={"item_timeline": [1]},
            protagonist_name="hero",
        )

        assert payload == Stage2AnalystWeaponsPayload(
            analyst_weapons={
                "preflight": {"item_timeline": [1]},
                "constraints": "compiled constraints",
            },
            entity_registry_for_director={"npc": {"role": "ally"}},
        )
        preflight.ctx.constraint_compiler.compile.assert_called_once()

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_entity_registry_default_is_dict_on_exception(self, preflight):
        preflight.ctx.constraint_compiler = MagicMock(compile=MagicMock(side_effect=RuntimeError("err")))
        preflight.ctx.agents.pop("state_extractor", None)
        out = preflight._preflight_arc_analysis(**_arc_analysis_kwargs(all_refined_arcs=[{"arc_no": 1}]))
        assert out["entity_registry_for_director"] == {}

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_recent_patterns_collected(self, preflight):
        arcs = [
            {"hybrid_composition": {"primary": "p1"}},
            {"hybrid_composition": {"primary": "p2"}},
            {"hybrid_composition": {}},
        ]
        out = preflight._preflight_arc_analysis(**_arc_analysis_kwargs(all_refined_arcs=arcs))
        assert "recent_patterns" not in out

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_hollow_previous_arcs_are_skipped_before_preflight_analysis(self, preflight):
        preflight.ctx.agents["preflight"].analyze.return_value = {
            "item_timeline": [],
            "absolute_prohibitions": [],
            "relationship_map": {},
        }
        usable_arc = {"arc_no": 1, "tactical_doc": "usable tactical", "state_constraints": {"arc_end_state": {}}}
        result = preflight._preflight_state_setup(
            **_state_setup_kwargs(
                all_refined_arcs=[
                    usable_arc,
                    {"arc_no": 2, "tactical_doc": ""},
                    {"arc_no": 3},
                ]
            )
        )

        analyze_args, analyze_kwargs = preflight.ctx.agents["preflight"].analyze.call_args
        assert analyze_args[0] == [usable_arc]
        assert analyze_kwargs["resolved_plots_summary"] == "resolved"
        assert result["cached_preflight_result"]["_input_hygiene"]["skipped_hollow_arc_nos"] == [2, 3]
        preflight.ctx.audit_event.assert_any_call(
            "preflight_hollow_prev_arcs_skipped",
            "Preflight skipped hollow previous arcs",
            {
                "arc_no": 1,
                "skipped_arc_nos": [2, 3],
                "usable_prev_arc_count": 1,
                "total_prev_arc_count": 3,
            },
        )

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_stage3_reverse_feedback_injected_after_three_stage3_failures(self, preflight):
        preflight.ctx.stage_rejection_history = [
            {"stage": 3, "arc_no": 1, "reason": "continuity", "attempt": 1},
            {"stage": 3, "arc_no": 1, "reason": "continuity", "attempt": 2},
            {"stage": 3, "arc_no": 1, "reason": "coverage", "attempt": 3},
            {"stage": 2, "arc_no": 1, "reason": "ignore", "attempt": 1},
        ]
        preflight.ctx.generate_reverse_feedback_stage3_to_2 = MagicMock(return_value="reverse feedback")

        preflight._preflight_arc_analysis(**_arc_analysis_kwargs(constraint_block=""))

        preflight.ctx.generate_reverse_feedback_stage3_to_2.assert_called_once()
        call_kw = preflight.ctx.generate_reverse_feedback_stage3_to_2.call_args.kwargs
        assert call_kw["arc_no"] == 1
        assert len(call_kw["architect_failures"]) == 3
        assert all(item["stage"] == 3 for item in call_kw["architect_failures"])
        preflight.ctx.ui.log.assert_called()

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_build_arc_analysis_context_injects_stage3_and_stage4_reverse_feedback(self, preflight):
        from modules.core.stage2_preflight import Stage2ArcAnalysisContextPayload

        preflight.ctx.stage_rejection_history = [
            {"stage": 3, "arc_no": 2, "reason": "continuity", "attempt": 1},
            {"stage": 3, "arc_no": 2, "reason": "continuity", "attempt": 2},
            {"stage": 3, "arc_no": 2, "reason": "coverage", "attempt": 3},
        ]
        preflight.ctx.generate_reverse_feedback_stage3_to_2 = MagicMock(return_value="stage3 reverse")
        preflight.ctx.generate_reverse_feedback_stage4_to_2 = MagicMock(return_value="stage4 reverse")
        preflight.ctx.pass_rate_monitor = MagicMock()
        preflight.ctx.pass_rate_monitor.get_arc_difficulty.return_value = {"difficulty": "hard"}

        payload = preflight.runtime.build_arc_analysis_context(
            attempt=0,
            current_feedback="",
            constraint_block="",
            last_refined_context="last context",
            all_refined_arcs=[],
            protagonist_name="hero",
            global_arc_no=2,
            cached_preflight_injection="cached inj",
        )

        assert isinstance(payload, Stage2ArcAnalysisContextPayload)
        assert payload.narrative_enriched is False
        assert "stage3 reverse" in payload.enhanced_context
        assert "stage4 reverse" in payload.enhanced_context
        preflight.ctx.generate_reverse_feedback_stage3_to_2.assert_called_once()
        preflight.ctx.generate_reverse_feedback_stage4_to_2.assert_called_once_with({"difficulty": "hard"})
        preflight.ctx.audit_event.assert_any_call(
            "s4_to_s2_feedback",
            "Arc difficulty feedback injected",
            {"arc_no": 2, "prev_difficulty": {"difficulty": "hard"}},
        )

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_apply_arc_analysis_support_layers_prepends_optimizer_and_v51_layers(self, preflight):
        preflight.ctx.stage2_optimizer = MagicMock()
        preflight.ctx.stage2_optimizer.generate_optimized_prompt.return_value = "[optimizer]"
        preflight.ctx.quality_amplifier = MagicMock()
        preflight.ctx.quality_amplifier.generate_analyst_constraints.return_value = "[qa]"
        preflight.ctx.agent_intelligence = MagicMock()
        preflight.ctx.agent_intelligence.get_analyst_enhancement.return_value = "[intel]"
        preflight.ctx.failure_learner = MagicMock()
        preflight.ctx.failure_learner.generate_constraint_prompt.return_value = "[learned]"
        preflight.ctx.constitutional_checker = MagicMock()
        preflight.ctx.constitutional_checker.get_full_injection.return_value = "[constitution]"

        enhanced = preflight.runtime.apply_arc_analysis_support_layers(
            attempt=0,
            current_feedback="director feedback",
            constraint_block="[constraint]",
            enhanced_context="[base]",
            cached_preflight_injection="[cached]",
            all_refined_arcs=[{"arc_no": 1}],
            protagonist_name="hero",
            global_arc_no=2,
        )

        assert enhanced.startswith("[constitution]")
        assert "[qa]" in enhanced
        assert "[intel]" in enhanced
        assert "[learned]" in enhanced
        assert "[optimizer]" in enhanced
        assert "[cached]" in enhanced
        assert "[constraint]" in enhanced
        preflight.ctx.stage2_optimizer.generate_optimized_prompt.assert_called_once_with(
            prev_arcs=[{"arc_no": 1}],
            protagonist_name="hero",
            include_examples=True,
        )
        preflight.ctx.constitutional_checker.get_full_injection.assert_called_once_with(
            stage=2,
            context={"prev_arcs": [{"arc_no": 1}], "feedback": "director feedback"},
        )
        assert preflight.ctx.ui.log.call_count >= 2

    def test_build_arc_analysis_base_context_injects_quality_headers_narrative_and_fact_ledger(self, preflight):
        from modules.core.stage2_preflight import Stage2ArcAnalysisContextPayload

        preflight.ctx.quality_dashboard = MagicMock()
        preflight.ctx.quality_dashboard.get_score_trend_summary.return_value = {
            "trend": "up",
            "summary": "최근 추세 상승",
        }
        preflight.ctx.state_tracker.npc_registry = {
            "ally": {"primary_motivation": "protect"},
            "extra": {"primary_motivation": ""},
        }
        preflight.ctx.current_project.db.load_anchor.return_value = {"cumulative_elapsed": "3일"}
        preflight._build_style_guide_summary = MagicMock(return_value="[문체 가이드 요약]")
        preflight._build_protagonist_config_summary = MagicMock(return_value="[주인공 설정 요약]")
        preflight._build_fact_ledger_context = MagicMock(return_value="[팩트 원장 핵심 수치]")

        with patch(
            "modules.core.narrative_context_formatter.NarrativeContextFormatter.format_all",
            return_value="[서사 구조 컨텍스트]",
        ) as format_all:
            payload = preflight.runtime.build_arc_analysis_base_context(
                attempt=0,
                last_refined_context="last context",
                all_refined_arcs=[{"arc_no": 1}],
                protagonist_name="hero",
                global_arc_no=2,
            )

        assert payload == Stage2ArcAnalysisContextPayload(
            enhanced_context=(
                "[팩트 원장 핵심 수치]\n\n"
                "[서사 구조 컨텍스트]\n\n"
                "[문체 가이드 요약]\n\n"
                "[주인공 설정 요약]\n\n"
                "\n[품질 추세 참고]\n최근 추세 상승\nlast context"
            ),
            narrative_enriched=True,
        )
        format_kwargs = format_all.call_args.kwargs
        assert format_kwargs["npc_motivations"] == {"ally": "protect"}
        assert format_kwargs["all_refined_arcs"] == [{"arc_no": 1}]
        assert format_kwargs["current_arc_no"] == 2
        assert format_kwargs["cumulative_elapsed"] == "3일"
        preflight.ctx.ui.log.assert_called_with("      📖 [LM-G] 서사 구조 컨텍스트 주입 완료")

    def test_build_fact_ledger_context_reads_numbers_schema(self, preflight):
        preflight.ctx.current_project.db.load_anchor.side_effect = lambda key: (
            {
                "numbers": {
                    "자본금": {
                        "value": "10억",
                        "unit": "원",
                        "established_value": "1억",
                        "established_ep": 1,
                        "last_ep": 8,
                    }
                }
            }
            if key == "fact_ledger"
            else {}
        )

        text = preflight._build_fact_ledger_context(max_items=5)

        assert "[팩트 원장 핵심 수치]" in text
        assert "자본금" in text

    def test_style_guide_and_protagonist_helpers_read_anchor_data(self, preflight):
        preflight.ctx.current_project.load_v20_anchor.return_value = {
            "tone": "냉소적",
            "pov": "3인칭",
            "dialogue_ratio": 0.4,
            "sentence_length": "short",
            "anti_ai_patterns": ["그의 눈동자가 흔들렸다", "마침내 모든 것이 끝났다"],
            "forbidden_expressions": ["결국"],
        }
        preflight.ctx.current_project.master_bible = {
            "MasterBible": {
                "protagonist_config": {
                    "world_origin": "현대인",
                    "incarnation_type": "회귀자",
                    "pov": "1인칭",
                }
            }
        }

        style_text = preflight._build_style_guide_summary()
        protagonist_text = preflight._build_protagonist_config_summary()

        assert "[문체 가이드 요약]" in style_text
        assert "시점=1인칭" in style_text
        assert "anti-AI 금지" in style_text
        assert "[주인공 설정 요약]" in protagonist_text
        assert "환생 유형=회귀자" in protagonist_text
        assert "1인칭 유지" in protagonist_text


class TestPreflightEnrichment:
    def test_run_auxiliary_state_tracker_extractors_dispatches_all_tail_extractors(self, preflight):
        tracker = MagicMock()
        refined_arc = {"tactical_doc": "arc"}

        preflight._run_auxiliary_state_tracker_extractors(
            state_tracker=tracker,
            refined_arc=refined_arc,
        )

        tracker.extract_npc_dialogue_styles_from_arc.assert_called_once_with(refined_arc)
        tracker.extract_time_markers_from_arc.assert_called_once_with(refined_arc)
        tracker.extract_permanent_injuries_from_arc.assert_called_once_with(refined_arc)
        tracker.update_companions_from_arc.assert_called_once_with(refined_arc)
        tracker.extract_commitments_from_arc.assert_called_once_with(refined_arc)
        tracker.extract_protagonist_emotion_from_arc.assert_called_once_with(refined_arc)
        tracker.extract_relationship_changes_from_arc.assert_called_once_with(refined_arc)
        tracker.extract_npc_injuries_from_arc.assert_called_once_with(refined_arc)
        tracker.extract_npc_movements_from_arc.assert_called_once_with(refined_arc)

    def test_run_auxiliary_state_tracker_extractors_keeps_going_after_failure(self, preflight):
        tracker = MagicMock()
        refined_arc = {"tactical_doc": "arc"}
        tracker.extract_time_markers_from_arc.side_effect = RuntimeError("timeline fail")

        preflight._run_auxiliary_state_tracker_extractors(
            state_tracker=tracker,
            refined_arc=refined_arc,
        )

        tracker.extract_time_markers_from_arc.assert_called_once_with(refined_arc)
        tracker.extract_permanent_injuries_from_arc.assert_called_once_with(refined_arc)
        tracker.extract_npc_movements_from_arc.assert_called_once_with(refined_arc)

    def test_run_state_tracker_tail_tasks_dispatches_genre_semantic_summary_cleanup(self, preflight):
        tracker = MagicMock()
        tracker.resolved_plots = [{"plot": "회수"}]
        tracker.export_financial_registry.return_value = {"cash": 100}
        tracker.generate_arc_summary.return_value = {"summary": "ok"}
        tracker.cleanup_npc_registry_with_llm.return_value = ["오탐1"]
        tracker.check_and_expand_genre.return_value = "politics"
        preflight.ctx.state_tracker = tracker
        preflight.ctx.semantic_plot_guard = MagicMock()
        preflight.ctx.semantic_plot_guard.index_resolved_plots.return_value = 2
        refined_arc = {"tactical_doc": "정쟁 강화"}

        preflight._run_state_tracker_tail_tasks(
            refined_arc=refined_arc,
            global_arc_no=5,
            genre_for_tracker="investment",
        )

        tracker._populate_genre_registries_from_arc.assert_called_once_with(refined_arc)
        tracker.extract_financial_events_from_arc.assert_called_once_with(refined_arc)
        tracker.export_financial_registry.assert_called_once()
        preflight.ctx.semantic_plot_guard.index_resolved_plots.assert_called_once_with(tracker.resolved_plots)
        tracker.generate_arc_summary.assert_called_once_with(5, refined_arc)
        tracker.cleanup_npc_registry_with_llm.assert_called_once_with(5)
        tracker.check_and_expand_genre.assert_called_once_with("정쟁 강화")
        preflight.ctx.current_project.save_v20_anchor.assert_any_call("financial_registry", {"cash": 100})
        preflight.ctx.current_project.save_v20_anchor.assert_any_call("arc_summary_5", {"summary": "ok"})

    def test_run_state_tracker_tail_tasks_continues_after_partial_failure(self, preflight):
        tracker = MagicMock()
        tracker.resolved_plots = [{"plot": "회수"}]
        tracker._populate_genre_registries_from_arc.side_effect = RuntimeError("genre fail")
        tracker.generate_arc_summary.return_value = {"summary": "ok"}
        tracker.cleanup_npc_registry_with_llm.return_value = []
        preflight.ctx.state_tracker = tracker
        preflight.ctx.semantic_plot_guard = MagicMock()
        preflight.ctx.semantic_plot_guard.index_resolved_plots.side_effect = RuntimeError("semantic fail")
        refined_arc = {"tactical_doc": "무공 강화"}

        preflight._run_state_tracker_tail_tasks(
            refined_arc=refined_arc,
            global_arc_no=5,
            genre_for_tracker="wuxia",
        )

        tracker.generate_arc_summary.assert_called_once_with(5, refined_arc)
        tracker.cleanup_npc_registry_with_llm.assert_called_once_with(5)
        tracker.check_and_expand_genre.assert_called_once_with("무공 강화")
        preflight.ctx.current_project.save_v20_anchor.assert_called_once_with("arc_summary_5", {"summary": "ok"})

    def test_log_four_phase_pass_summary_logs_entities_and_generation_metadata(self, preflight, caplog):
        with caplog.at_level("INFO"):
            preflight._log_four_phase_pass_summary(
                dead_npcs=["흑풍"],
                learned_skills=["비연검"],
                npc_info=[{"name": "연홍"}],
                pipeline_result={"phases": {"generate": {"candidates_count": 3, "selected_strategy": "ensemble_b"}}},
            )

        assert "- 사망 NPC 기록: 흑풍" in caplog.text
        assert "- 무공 습득 기록: 비연검" in caplog.text
        assert "- NPC 정보 기록: 1건" in caplog.text
        assert "- 후보 수: 3개" in caplog.text
        assert "- 선택 전략: ensemble_b" in caplog.text

    def test_finalize_four_phase_pass_snapshots_tracker_and_runs_tail_tasks(self, preflight):
        from modules.core.stage2_preflight import Stage2FourPhasePassPayload

        tracker = MagicMock()
        tracker.npc_registry = {"npc": {"status": "alive"}}
        tracker.resolved_plots = [{"plot": "keep"}]
        tracker.entity_destructions = []
        tracker.protagonist_skills = {"sword"}
        tracker.skill_acquisitions = [{"name": "sword"}]
        tracker.npc_npc_relationships = {"npc": {"hero": "ally"}}
        tracker.item_state_registry = {"blade": {"owner": "hero"}}
        tracker.active_plots = [{"plot": "keep"}]
        tracker.npc_dialogue_profiles = {"npc": {"tone": "calm"}}
        tracker.in_world_timeline = [{"day": 1}]
        tracker.current_companions = ["npc"]
        tracker.pending_commitments = [{"promise": "return"}]
        tracker.protagonist_emotion = {"mood": "calm"}
        tracker.dungeon_clear_registry = {"cave": True}
        tracker.skill_cooldown_registry = {"slash": 2}
        tracker.spell_repertoire = {"flare": 1}
        tracker.financial_number_registry = {"cash": 10}
        tracker.extract_npc_deaths_from_arc.return_value = ["npc1"]
        tracker.extract_skill_acquisitions_from_arc.return_value = ["skill1"]
        tracker.extract_npc_info_from_arc.return_value = [{"name": "npc1"}]
        tracker.check_suspended_plots.return_value = [{"message": "watch suspended plot"}]
        preflight.ctx.state_tracker = tracker
        preflight.ctx.adversarial_self_play = None
        preflight._run_auxiliary_state_tracker_extractors = MagicMock()
        preflight._run_state_tracker_tail_tasks = MagicMock()
        preflight._log_four_phase_pass_summary = MagicMock()

        payload = preflight.runtime.finalize_four_phase_pass(
            attempt=0,
            global_arc_no=5,
            director_feedback_for_fourphase="feedback",
            refined_arc={"tactical_doc": "PASS ARC", "joint_docs": {}, "status_shadow": {}},
            pipeline_result={"retries": 1, "phases": {"generate": {"candidates_count": 2}}},
            enriched_block={"joint_docs": {"a": 1}, "status_shadow": {"b": 2}},
            genre_for_tracker="wuxia",
        )

        assert isinstance(payload, Stage2FourPhasePassPayload)
        assert payload.four_phase_passed is True
        assert payload.generation_method == "four_phase"
        assert payload.refined_arc["joint_docs"] == {"a": 1}
        assert payload.refined_arc["status_shadow"] == {"b": 2}
        assert payload.st_snapshot["npc_registry"] == {"npc": {"status": "alive"}}
        tracker.extract_resolved_plots_from_arc.assert_called_once_with(payload.refined_arc)
        tracker.extract_npc_deaths_from_arc.assert_called_once_with(payload.refined_arc)
        tracker.extract_skill_acquisitions_from_arc.assert_called_once_with(payload.refined_arc)
        tracker.extract_npc_info_from_arc.assert_called_once_with(payload.refined_arc, genre="wuxia")
        tracker.check_suspended_plots.assert_called_once_with(5)
        preflight._run_auxiliary_state_tracker_extractors.assert_called_once_with(
            state_tracker=tracker,
            refined_arc=payload.refined_arc,
        )
        preflight._run_state_tracker_tail_tasks.assert_called_once_with(
            refined_arc=payload.refined_arc,
            global_arc_no=5,
            genre_for_tracker="wuxia",
        )
        preflight._log_four_phase_pass_summary.assert_called_once()

    def test_finalize_four_phase_pass_preserves_existing_authoritative_packets(self, preflight):
        tracker = MagicMock()
        tracker.npc_registry = {}
        tracker.resolved_plots = []
        tracker.entity_destructions = []
        tracker.protagonist_skills = set()
        tracker.skill_acquisitions = []
        tracker.npc_npc_relationships = {}
        tracker.item_state_registry = {}
        tracker.active_plots = []
        tracker.npc_dialogue_profiles = {}
        tracker.in_world_timeline = []
        tracker.current_companions = []
        tracker.pending_commitments = []
        tracker.protagonist_emotion = {}
        tracker.dungeon_clear_registry = {}
        tracker.skill_cooldown_registry = {}
        tracker.spell_repertoire = {}
        tracker.financial_number_registry = {}
        tracker.extract_npc_deaths_from_arc.return_value = []
        tracker.extract_skill_acquisitions_from_arc.return_value = []
        tracker.extract_npc_info_from_arc.return_value = []
        tracker.check_suspended_plots.return_value = []
        preflight.ctx.state_tracker = tracker
        preflight.ctx.adversarial_self_play = None
        preflight._run_auxiliary_state_tracker_extractors = MagicMock()
        preflight._run_state_tracker_tail_tasks = MagicMock()
        preflight._log_four_phase_pass_summary = MagicMock()

        payload = preflight.runtime.finalize_four_phase_pass(
            attempt=0,
            global_arc_no=5,
            director_feedback_for_fourphase="feedback",
            refined_arc={
                "tactical_doc": "PASS ARC",
                "joint_docs": {"final_location": "llm-city", "world_joint": "llm-world"},
                "status_shadow": {"expected_injuries": "llm-wound", "item_consumption": []},
            },
            pipeline_result={"retries": 1, "phases": {"generate": {"candidates_count": 2}}},
            enriched_block={
                "joint_docs": {"final_location": "block-city", "physical_inventory": ["ledger"], "world_joint": "stale"},
                "status_shadow": {"expected_injuries": "stale-wound", "key_stat_change": "fallback-stat"},
            },
            genre_for_tracker="wuxia",
        )

        assert payload.refined_arc["joint_docs"] == {
            "final_location": "llm-city",
            "physical_inventory": ["ledger"],
            "world_joint": "llm-world",
        }
        assert payload.refined_arc["status_shadow"] == {
            "expected_injuries": "llm-wound",
            "item_consumption": [],
            "key_stat_change": "fallback-stat",
        }

    def test_apply_four_phase_pass_state_tracker_updates_snapshots_and_dispatches_tail_tasks(self, preflight):
        from modules.core.stage2_preflight import Stage2FourPhaseTrackerPayload

        tracker = MagicMock()
        tracker.npc_registry = {"npc": {"status": "alive"}}
        tracker.resolved_plots = [{"plot": "keep"}]
        tracker.entity_destructions = []
        tracker.protagonist_skills = {"sword"}
        tracker.skill_acquisitions = [{"name": "sword"}]
        tracker.npc_npc_relationships = {"npc": {"hero": "ally"}}
        tracker.item_state_registry = {"blade": {"owner": "hero"}}
        tracker.active_plots = [{"plot": "keep"}]
        tracker.npc_dialogue_profiles = {"npc": {"tone": "calm"}}
        tracker.in_world_timeline = [{"day": 1}]
        tracker.current_companions = ["npc"]
        tracker.pending_commitments = [{"promise": "return"}]
        tracker.protagonist_emotion = {"mood": "calm"}
        tracker.dungeon_clear_registry = {"cave": True}
        tracker.skill_cooldown_registry = {"slash": 2}
        tracker.spell_repertoire = {"flare": 1}
        tracker.financial_number_registry = {"cash": 10}
        tracker.extract_npc_deaths_from_arc.return_value = ["npc1"]
        tracker.extract_skill_acquisitions_from_arc.return_value = ["skill1"]
        tracker.extract_npc_info_from_arc.return_value = [{"name": "npc1"}]
        tracker.check_suspended_plots.return_value = [{"message": "watch suspended plot"}]
        preflight.ctx.state_tracker = tracker
        preflight._run_auxiliary_state_tracker_extractors = MagicMock()
        preflight._run_state_tracker_tail_tasks = MagicMock()
        preflight._log_four_phase_pass_summary = MagicMock()

        payload = preflight._apply_four_phase_pass_state_tracker_updates(
            refined_arc={"tactical_doc": "PASS ARC"},
            global_arc_no=5,
            genre_for_tracker="wuxia",
            pipeline_result={"phases": {"generate": {"candidates_count": 2}}},
        )

        assert payload == Stage2FourPhaseTrackerPayload(
            st_snapshot=payload.st_snapshot,
            dead_npcs=["npc1"],
            learned_skills=["skill1"],
            npc_info=[{"name": "npc1"}],
        )
        assert payload.st_snapshot["npc_registry"] == {"npc": {"status": "alive"}}
        tracker.extract_resolved_plots_from_arc.assert_called_once_with({"tactical_doc": "PASS ARC"})
        tracker.extract_npc_deaths_from_arc.assert_called_once_with({"tactical_doc": "PASS ARC"})
        tracker.extract_skill_acquisitions_from_arc.assert_called_once_with({"tactical_doc": "PASS ARC"})
        tracker.extract_npc_info_from_arc.assert_called_once_with({"tactical_doc": "PASS ARC"}, genre="wuxia")
        tracker.check_suspended_plots.assert_called_once_with(5)
        preflight._run_auxiliary_state_tracker_extractors.assert_called_once_with(
            state_tracker=tracker,
            refined_arc={"tactical_doc": "PASS ARC"},
        )
        preflight._run_state_tracker_tail_tasks.assert_called_once_with(
            refined_arc={"tactical_doc": "PASS ARC"},
            global_arc_no=5,
            genre_for_tracker="wuxia",
        )
        preflight._log_four_phase_pass_summary.assert_called_once_with(
            dead_npcs=["npc1"],
            learned_skills=["skill1"],
            npc_info=[{"name": "npc1"}],
            pipeline_result={"phases": {"generate": {"candidates_count": 2}}},
        )

    def test_build_patch_mode_audit_payload_increments_attempt_and_preserves_metadata(self, preflight):
        payload = preflight._build_patch_mode_audit_payload(
            global_arc_no=3,
            attempt=1,
            prev_score=82,
            patch_fallback=False,
        )

        assert payload == {
            "arc_no": 3,
            "attempt": 2,
            "prev_score": 82,
            "fallback": False,
        }

    def test_build_four_phase_result_payload_maps_all_result_fields(self, preflight):
        payload = preflight._build_four_phase_result_payload(
            four_phase_passed=True,
            refined_arc={"arc_no": 1},
            generation_method="four_phase",
            draft_validator_passed=False,
            consensus_passed=True,
            st_snapshot={"registry": 1},
            director_feedback_for_fourphase="feedback",
            was_patch=True,
            patch_fallback=False,
            prev_score=88,
        )

        assert payload == {
            "four_phase_passed": True,
            "refined_arc": {"arc_no": 1},
            "generation_method": "four_phase",
            "draft_validator_passed": False,
            "consensus_passed": True,
            "st_snapshot": {"registry": 1},
            "director_feedback_for_fourphase": "feedback",
            "was_patch": True,
            "patch_fallback": False,
            "prev_score": 88,
        }

    def test_build_four_phase_prerun_state_returns_default_flags(self, preflight):
        payload = preflight._build_four_phase_prerun_state()

        assert payload == {
            "four_phase_passed": False,
            "refined_arc": None,
            "generation_method": "analyst",
            "draft_validator_passed": False,
            "consensus_passed": False,
            "st_snapshot": None,
            "was_patch": False,
            "patch_fallback": False,
            "prev_score": 0,
        }

    def test_build_four_phase_spinner_labels_formats_attempt_and_arc_strings(self, preflight):
        payload = preflight._build_four_phase_spinner_labels(
            attempt=1,
            global_arc_no=7,
        )

        assert payload == {
            "attempt_log": "      🎯 [V60.77] FourPhase-Director 대면 2/5",
            "spinner_title": "Arc 7",
            "vector_detail": "Arc 7 · 벡터 검색",
        }

    def test_build_patch_mode_labels_formats_entry_and_fallback_messages(self, preflight):
        from modules.core.stage2_preflight import Stage2PatchModeLabels

        payload = preflight._build_patch_mode_labels(
            prev_score=82,
            attempt=1,
        )

        assert payload == Stage2PatchModeLabels(
            enter_log="[Patch Mode] Arc 패치 모드 진입 (score=82, attempt=1)",
            enter_ui="   🔧 [Patch Mode] Arc 패치: score=82, 원본 보존 수정",
            fallback_log="[Patch Mode] Arc 패치 실패 → 전면 재생성 폴백",
            fallback_ui="   ⚠️ [Patch Mode] Arc 패치 실패 → 전면 재생성 폴백",
        )

    def test_prepare_four_phase_generation_plan_warns_when_fix_scope_missing(self, preflight):
        from modules.core.stage2_preflight import Stage2FourPhaseGenerationPlan

        payload = preflight.runtime.prepare_four_phase_generation_plan(
            {
                "best_arc": {"arc_no": 3},
                "fix_scope": "",
                "score": 82,
                "selected_strategy": "ensemble_c",
            }
        )

        assert payload == Stage2FourPhaseGenerationPlan(
            fix_scope="",
            prev_score=82,
            was_patch=False,
            use_inplace=False,
            use_patch=False,
            four_phase_arc=None,
            pipeline_result={"final_verdict": None},
        )
        preflight.ctx.ui.log.assert_any_call("   ⚠️ [PF-1] fix_scope 누락 -> local patch 생략, full generate로 위임")

    def test_build_four_phase_generation_attempt_result_preserves_patch_flags(self, preflight):
        from modules.core.stage2_preflight import Stage2FourPhaseAttemptResult

        payload = preflight._build_four_phase_generation_attempt_result(
            four_phase_arc={"arc_no": 3},
            pipeline_result={"final_verdict": "PASS"},
            prev_score=82,
            was_patch=True,
            patch_fallback=False,
        )

        assert payload == Stage2FourPhaseAttemptResult(
            four_phase_arc={"arc_no": 3},
            pipeline_result={"final_verdict": "PASS"},
            prev_score=82,
            was_patch=True,
            patch_fallback=False,
        )

    def test_execute_four_phase_generation_plan_passes_inplace_result_into_patch_path(self, preflight):
        from modules.core.stage2_preflight import (
            Stage2FourPhaseGenerationPlan,
            Stage2FourPhaseGenerationRequest,
        )

        preflight._run_inplace_four_phase_attempt = MagicMock(
            return_value=({"arc_no": 3, "patched": True}, {"final_verdict": "PASS"})
        )
        preflight._run_patch_or_generate_four_phase_attempt = MagicMock(
            return_value=({"arc_no": 3, "patched": True}, {"final_verdict": "PASS"}, False)
        )

        result = preflight.runtime.execute_four_phase_generation_plan(
            request=Stage2FourPhaseGenerationRequest(
                attempt=1,
                global_arc_no=3,
                current_ep_start=11,
                current_vol_strategy={"strategy_doc": "doc"},
                enriched_block={"block_theme": "theme"},
                all_refined_arcs=[{"arc_no": 1}],
                bible_root={"AssetLibrary": {}},
                protagonist_name="hero",
                director_feedback_for_fourphase="director feedback",
                entity_registry_for_director={"npc": {}},
                previous_attempt={"best_arc": {"arc_no": 3}, "rejection_reason": "fix local issue"},
                s2_spinner=MagicMock(),
                s2_vector_ctx="vector ctx",
                generation_plan=Stage2FourPhaseGenerationPlan(
                    fix_scope="inplace",
                    prev_score=95,
                    was_patch=True,
                    use_inplace=True,
                    use_patch=True,
                    four_phase_arc=None,
                    pipeline_result={"final_verdict": None},
                ),
            ),
        )

        assert result == ({"arc_no": 3, "patched": True}, {"final_verdict": "PASS"}, False)
        preflight._run_inplace_four_phase_attempt.assert_called_once_with(
            global_arc_no=3,
            fix_scope="inplace",
            prev_score=95,
            previous_attempt={"best_arc": {"arc_no": 3}, "rejection_reason": "fix local issue"},
        )
        assert preflight._run_patch_or_generate_four_phase_attempt.call_args.kwargs["four_phase_arc"] == {
            "arc_no": 3,
            "patched": True,
        }
        assert preflight._run_patch_or_generate_four_phase_attempt.call_args.kwargs["pipeline_result"] == {
            "final_verdict": "PASS",
        }

    def test_resolve_four_phase_generation_seed_uses_plan_defaults_without_inplace(self, preflight):
        from modules.core.stage2_preflight import (
            Stage2FourPhaseGenerationPlan,
            Stage2FourPhaseGenerationRequest,
        )

        request = Stage2FourPhaseGenerationRequest(
            attempt=1,
            global_arc_no=3,
            current_ep_start=11,
            current_vol_strategy={"strategy_doc": "doc"},
            enriched_block={"block_theme": "theme"},
            all_refined_arcs=[{"arc_no": 1}],
            bible_root={"AssetLibrary": {}},
            protagonist_name="hero",
            director_feedback_for_fourphase="director feedback",
            entity_registry_for_director={"npc": {}},
            previous_attempt={"best_arc": {"arc_no": 3}},
            s2_spinner=MagicMock(),
            s2_vector_ctx="vector ctx",
            generation_plan=Stage2FourPhaseGenerationPlan(
                prev_score=82,
                was_patch=False,
                use_inplace=False,
                use_patch=True,
                four_phase_arc={"arc_no": 3, "seeded": True},
                pipeline_result={"final_verdict": "PASS"},
            ),
        )
        preflight._run_inplace_four_phase_attempt = MagicMock()

        four_phase_arc, pipeline_result = preflight._resolve_four_phase_generation_seed(request=request)

        assert four_phase_arc == {"arc_no": 3, "seeded": True}
        assert pipeline_result == {"final_verdict": "PASS"}
        preflight._run_inplace_four_phase_attempt.assert_not_called()

    def test_build_patch_or_generate_attempt_kwargs_reuses_request_and_generation_plan(self, preflight):
        from modules.core.stage2_preflight import (
            Stage2FourPhaseGenerationPlan,
            Stage2FourPhaseGenerationRequest,
        )

        request = Stage2FourPhaseGenerationRequest(
            attempt=1,
            global_arc_no=3,
            current_ep_start=11,
            current_vol_strategy={"strategy_doc": "doc"},
            enriched_block={"block_theme": "theme"},
            all_refined_arcs=[{"arc_no": 1}],
            bible_root={"AssetLibrary": {"sword": "iron"}},
            protagonist_name="hero",
            director_feedback_for_fourphase="director feedback",
            entity_registry_for_director={"npc": {}},
            previous_attempt={"best_arc": {"arc_no": 3}},
            s2_spinner=MagicMock(),
            s2_vector_ctx="vector ctx",
            generation_plan=Stage2FourPhaseGenerationPlan(
                prev_score=82,
                was_patch=False,
                use_inplace=False,
                use_patch=True,
                four_phase_arc={"arc_no": 3, "seeded": True},
                pipeline_result={"final_verdict": "PASS"},
            ),
        )

        kwargs = preflight._build_patch_or_generate_attempt_kwargs(
            request=request,
            four_phase_arc={"arc_no": 3, "patched": True},
            pipeline_result={"final_verdict": "PASS"},
        )

        assert kwargs["attempt"] == 1
        assert kwargs["global_arc_no"] == 3
        assert kwargs["current_ep_start"] == 11
        assert kwargs["current_vol_strategy"] == {"strategy_doc": "doc"}
        assert kwargs["previous_attempt"] == {"best_arc": {"arc_no": 3}}
        assert kwargs["prev_score"] == 82
        assert kwargs["use_patch"] is True
        assert kwargs["four_phase_arc"] == {"arc_no": 3, "patched": True}
        assert kwargs["pipeline_result"] == {"final_verdict": "PASS"}

    def test_build_patch_or_generate_request_fields_reuses_runtime_request_surface(self, preflight):
        from modules.core.stage2_preflight import (
            Stage2FourPhaseGenerationPlan,
            Stage2FourPhaseGenerationRequest,
        )

        spinner = MagicMock()
        request = Stage2FourPhaseGenerationRequest(
            attempt=1,
            global_arc_no=3,
            current_ep_start=11,
            current_vol_strategy={"strategy_doc": "doc"},
            enriched_block={"block_theme": "theme"},
            all_refined_arcs=[{"arc_no": 1}],
            bible_root={"AssetLibrary": {"sword": "iron"}},
            protagonist_name="hero",
            director_feedback_for_fourphase="director feedback",
            entity_registry_for_director={"npc": {}},
            previous_attempt={"best_arc": {"arc_no": 3}},
            s2_spinner=spinner,
            s2_vector_ctx="vector ctx",
            generation_plan=Stage2FourPhaseGenerationPlan(),
        )

        fields = preflight._build_patch_or_generate_request_fields(request)

        assert fields == {
            "attempt": 1,
            "global_arc_no": 3,
            "current_ep_start": 11,
            "current_vol_strategy": {"strategy_doc": "doc"},
            "enriched_block": {"block_theme": "theme"},
            "all_refined_arcs": [{"arc_no": 1}],
            "bible_root": {"AssetLibrary": {"sword": "iron"}},
            "protagonist_name": "hero",
            "director_feedback_for_fourphase": "director feedback",
            "entity_registry_for_director": {"npc": {}},
            "previous_attempt": {"best_arc": {"arc_no": 3}},
            "s2_spinner": spinner,
            "s2_vector_ctx": "vector ctx",
        }

    def test_build_patch_or_generate_episode_fields_preserves_episode_runtime_surface(self, preflight):
        from modules.core.stage2_preflight import (
            Stage2FourPhaseGenerationPlan,
            Stage2FourPhaseGenerationRequest,
        )

        spinner = MagicMock()
        request = Stage2FourPhaseGenerationRequest(
            attempt=1,
            global_arc_no=3,
            current_ep_start=11,
            current_vol_strategy={"strategy_doc": "doc"},
            enriched_block={"block_theme": "theme"},
            all_refined_arcs=[{"arc_no": 1}],
            bible_root={"AssetLibrary": {"sword": "iron"}},
            protagonist_name="hero",
            director_feedback_for_fourphase="director feedback",
            entity_registry_for_director={"npc": {}},
            previous_attempt={"best_arc": {"arc_no": 3}},
            s2_spinner=spinner,
            s2_vector_ctx="vector ctx",
            generation_plan=Stage2FourPhaseGenerationPlan(),
        )

        fields = preflight._build_patch_or_generate_episode_fields(request)

        assert fields == {
            "attempt": 1,
            "global_arc_no": 3,
            "current_ep_start": 11,
            "s2_spinner": spinner,
            "s2_vector_ctx": "vector ctx",
        }

    def test_build_patch_or_generate_content_fields_preserves_content_director_surface(self, preflight):
        from modules.core.stage2_preflight import (
            Stage2FourPhaseGenerationPlan,
            Stage2FourPhaseGenerationRequest,
        )

        request = Stage2FourPhaseGenerationRequest(
            attempt=1,
            global_arc_no=3,
            current_ep_start=11,
            current_vol_strategy={"strategy_doc": "doc"},
            enriched_block={"block_theme": "theme"},
            all_refined_arcs=[{"arc_no": 1}],
            bible_root={"AssetLibrary": {"sword": "iron"}},
            protagonist_name="hero",
            director_feedback_for_fourphase="director feedback",
            entity_registry_for_director={"npc": {}},
            previous_attempt={"best_arc": {"arc_no": 3}},
            s2_spinner=MagicMock(),
            s2_vector_ctx="vector ctx",
            generation_plan=Stage2FourPhaseGenerationPlan(),
        )

        fields = preflight._build_patch_or_generate_content_fields(request)

        assert fields == {
            "current_vol_strategy": {"strategy_doc": "doc"},
            "enriched_block": {"block_theme": "theme"},
            "all_refined_arcs": [{"arc_no": 1}],
            "bible_root": {"AssetLibrary": {"sword": "iron"}},
            "protagonist_name": "hero",
            "director_feedback_for_fourphase": "director feedback",
            "entity_registry_for_director": {"npc": {}},
            "previous_attempt": {"best_arc": {"arc_no": 3}},
        }

    def test_build_patch_or_generate_story_fields_preserves_story_surface(self, preflight):
        from modules.core.stage2_preflight import (
            Stage2FourPhaseGenerationPlan,
            Stage2FourPhaseGenerationRequest,
        )

        request = Stage2FourPhaseGenerationRequest(
            attempt=1,
            global_arc_no=3,
            current_ep_start=11,
            current_vol_strategy={"strategy_doc": "doc"},
            enriched_block={"block_theme": "theme"},
            all_refined_arcs=[{"arc_no": 1}],
            bible_root={"AssetLibrary": {"sword": "iron"}},
            protagonist_name="hero",
            director_feedback_for_fourphase="director feedback",
            entity_registry_for_director={"npc": {}},
            previous_attempt={"best_arc": {"arc_no": 3}},
            s2_spinner=MagicMock(),
            s2_vector_ctx="vector ctx",
            generation_plan=Stage2FourPhaseGenerationPlan(),
        )

        fields = preflight._build_patch_or_generate_story_fields(request)

        assert fields == {
            "current_vol_strategy": {"strategy_doc": "doc"},
            "enriched_block": {"block_theme": "theme"},
            "all_refined_arcs": [{"arc_no": 1}],
            "bible_root": {"AssetLibrary": {"sword": "iron"}},
            "protagonist_name": "hero",
        }

    def test_build_patch_or_generate_director_fields_preserves_director_surface(self, preflight):
        from modules.core.stage2_preflight import (
            Stage2FourPhaseGenerationPlan,
            Stage2FourPhaseGenerationRequest,
        )

        request = Stage2FourPhaseGenerationRequest(
            attempt=1,
            global_arc_no=3,
            current_ep_start=11,
            current_vol_strategy={"strategy_doc": "doc"},
            enriched_block={"block_theme": "theme"},
            all_refined_arcs=[{"arc_no": 1}],
            bible_root={"AssetLibrary": {"sword": "iron"}},
            protagonist_name="hero",
            director_feedback_for_fourphase="director feedback",
            entity_registry_for_director={"npc": {}},
            previous_attempt={"best_arc": {"arc_no": 3}},
            s2_spinner=MagicMock(),
            s2_vector_ctx="vector ctx",
            generation_plan=Stage2FourPhaseGenerationPlan(),
        )

        fields = preflight._build_patch_or_generate_director_fields(request)

        assert fields == {
            "director_feedback_for_fourphase": "director feedback",
            "entity_registry_for_director": {"npc": {}},
            "previous_attempt": {"best_arc": {"arc_no": 3}},
        }

    def test_build_patch_or_generate_plan_fields_reuses_generation_plan_flags(self, preflight):
        from modules.core.stage2_preflight import (
            Stage2FourPhaseGenerationPlan,
            Stage2FourPhaseGenerationRequest,
        )

        request = Stage2FourPhaseGenerationRequest(
            attempt=1,
            global_arc_no=3,
            current_ep_start=11,
            current_vol_strategy={"strategy_doc": "doc"},
            enriched_block={"block_theme": "theme"},
            all_refined_arcs=[{"arc_no": 1}],
            bible_root={"AssetLibrary": {"sword": "iron"}},
            protagonist_name="hero",
            director_feedback_for_fourphase="director feedback",
            entity_registry_for_director={"npc": {}},
            previous_attempt={"best_arc": {"arc_no": 3}},
            s2_spinner=MagicMock(),
            s2_vector_ctx="vector ctx",
            generation_plan=Stage2FourPhaseGenerationPlan(
                prev_score=82,
                use_patch=True,
            ),
        )

        fields = preflight._build_patch_or_generate_plan_fields(
            request=request,
            four_phase_arc={"arc_no": 3, "patched": True},
            pipeline_result={"final_verdict": "PASS"},
        )

        assert fields == {
            "prev_score": 82,
            "use_patch": True,
            "four_phase_arc": {"arc_no": 3, "patched": True},
            "pipeline_result": {"final_verdict": "PASS"},
        }

    def test_log_four_phase_generation_attempt_outcome_emits_success_and_failure(self, preflight):
        preflight._log_four_phase_generation_attempt_outcome({"arc_no": 3})
        preflight._log_four_phase_generation_attempt_outcome(None)

        preflight.ctx.ui.log.assert_any_call("      ✅ [TF-38] Arc 생성 완료")
        preflight.ctx.ui.log.assert_any_call("      ⚠️ [TF-38] Arc 생성 실패")

    def test_run_inplace_four_phase_attempt_marks_pass_after_successful_patch(self, preflight):
        best_arc = {
            "arc_no": 3,
            "ep_start": 11,
            "ep_end": 20,
            "ep_count": 10,
            "tactical_doc": "ORIGINAL ARC " * 30,
            "state_changes": {},
        }
        patched_arc = {
            "arc_no": 3,
            "ep_start": 11,
            "ep_end": 20,
            "ep_count": 10,
            "tactical_doc": "PATCHED ARC " * 30,
            "state_changes": {},
        }
        preflight.ctx.agents["four_phase"]._inplace_patch_arc.return_value = patched_arc

        with (
            patch("modules.core.constants.calc_patch_change_ratio", return_value=0.2),
            patch("modules.core.constants.log_patch_diff"),
        ):
            four_phase_arc, pipeline_result = preflight._run_inplace_four_phase_attempt(
                global_arc_no=3,
                fix_scope="inplace",
                prev_score=95,
                previous_attempt={
                    "best_arc": best_arc,
                    "rejection_reason": "fix local issue",
                },
            )

        assert four_phase_arc == patched_arc
        assert pipeline_result == {"final_verdict": "PASS"}
        preflight.ctx.agents["four_phase"]._inplace_patch_arc.assert_called_once_with(
            original_arc=best_arc,
            director_feedback="fix local issue",
            arc_no=3,
        )

    def test_run_patch_or_generate_four_phase_attempt_falls_back_to_generate_after_patch_failure(self, preflight):
        generated_arc = {
            "arc_no": 3,
            "ep_start": 11,
            "ep_end": 20,
            "ep_count": 10,
            "tactical_doc": "GENERATED ARC " * 40,
            "state_changes": {},
        }
        spinner = MagicMock()
        preflight.ctx.agents["four_phase"].patch_arc_with_feedback.return_value = (
            None,
            {"final_verdict": "REJECT"},
        )
        preflight.ctx.agents["four_phase"].generate.return_value = (
            generated_arc,
            {"final_verdict": "PASS"},
        )

        four_phase_arc, pipeline_result, patch_fallback = preflight._run_patch_or_generate_four_phase_attempt(
            attempt=1,
            global_arc_no=3,
            current_ep_start=11,
            current_vol_strategy={"strategy_doc": "doc"},
            enriched_block={"block_theme": "theme"},
            all_refined_arcs=[{"arc_no": 1}],
            bible_root={"AssetLibrary": {}},
            protagonist_name="hero",
            director_feedback_for_fourphase="director feedback",
            entity_registry_for_director={"npc": {}},
            previous_attempt={
                "best_arc": {"arc_no": 3},
                "selected_strategy": "ensemble_c",
            },
            s2_spinner=spinner,
            s2_vector_ctx="vector ctx",
            prev_score=82,
            use_patch=True,
            four_phase_arc=None,
            pipeline_result={"final_verdict": None},
        )

        assert four_phase_arc == generated_arc
        assert pipeline_result == {"final_verdict": "PASS"}
        assert patch_fallback is True
        preflight.ctx.agents["four_phase"].patch_arc_with_feedback.assert_called_once()
        preflight.ctx.agents["four_phase"].generate.assert_called_once()
        spinner.update_detail.assert_called_once_with("Arc 3 · Arc 생성")

    def test_run_four_phase_generation_attempt_falls_back_from_patch_to_generate(self, preflight):
        from modules.core.stage2_preflight import Stage2FourPhaseAttemptResult

        best_arc = {
            "arc_no": 3,
            "ep_start": 11,
            "ep_end": 20,
            "ep_count": 10,
            "tactical_doc": "ORIGINAL ARC " * 60,
            "state_changes": {},
        }
        generated_arc = {
            "arc_no": 3,
            "ep_start": 11,
            "ep_end": 20,
            "ep_count": 10,
            "tactical_doc": "GENERATED ARC " * 80,
            "state_changes": {},
        }
        previous_attempt = {
            "best_arc": best_arc,
            "fix_scope": "partial",
            "score": 82,
            "rejection_reason": "tighten continuity",
            "selected_strategy": "ensemble_c",
        }
        spinner = MagicMock()
        preflight.ctx.agents["four_phase"].patch_arc_with_feedback.return_value = (
            None,
            {"final_verdict": "REJECT"},
        )
        preflight.ctx.agents["four_phase"].generate.return_value = (
            generated_arc,
            {"final_verdict": "PASS"},
        )

        result = preflight.runtime.run_four_phase_generation_attempt(
            attempt=1,
            global_arc_no=3,
            current_ep_start=11,
            current_vol_strategy={"strategy_doc": "doc"},
            enriched_block={"block_theme": "theme"},
            all_refined_arcs=[{"arc_no": 1}],
            bible_root={"AssetLibrary": {}},
            protagonist_name="hero",
            director_feedback_for_fourphase="director feedback",
            entity_registry_for_director={"npc": {}},
            previous_attempt=previous_attempt,
            s2_spinner=spinner,
            s2_vector_ctx="vector ctx",
        )

        assert result == Stage2FourPhaseAttemptResult(
            four_phase_arc=generated_arc,
            pipeline_result={"final_verdict": "PASS"},
            prev_score=82,
            was_patch=True,
            patch_fallback=True,
        )
        preflight.ctx.agents["four_phase"].patch_arc_with_feedback.assert_called_once()
        preflight.ctx.agents["four_phase"].generate.assert_called_once()
        assert (
            preflight.ctx.agents["four_phase"].patch_arc_with_feedback.call_args.kwargs["rejected_strategy"]
            == "ensemble_c"
        )
        spinner.update_detail.assert_called_once_with("Arc 3 · Arc 생성")
        preflight.ctx.perf_timer.start.assert_called_once_with("s2_arc_3_generate")
        preflight.ctx.perf_timer.stop.assert_called_once_with("s2_arc_3_generate")

    def test_emit_patch_mode_audit_event_dispatches_attempt_metadata(self, preflight):
        preflight._emit_patch_mode_audit_event(
            was_patch=True,
            global_arc_no=3,
            attempt=1,
            prev_score=82,
            patch_fallback=False,
        )

        preflight.ctx.audit_event.assert_called_once_with(
            "stage2_patch_mode",
            "stage2 four_phase patch mode attempted",
            {"arc_no": 3, "attempt": 2, "prev_score": 82, "fallback": False},
        )

    def test_emit_patch_mode_audit_event_noops_when_not_patch(self, preflight):
        preflight._emit_patch_mode_audit_event(
            was_patch=False,
            global_arc_no=3,
            attempt=1,
            prev_score=82,
            patch_fallback=True,
        )

        preflight.ctx.audit_event.assert_not_called()

    def test_build_four_phase_failure_feedback_emits_failed_audit_event(self, preflight):
        feedback = preflight._build_four_phase_failure_feedback(
            pipeline_result={
                "final_verdict": "FAILED",
                "retries": 3,
                "phases": {"validate": {"issues_count": 2}},
            },
            global_arc_no=1,
        )

        assert feedback == "FourPhase 재시도 소진 실패 (final_verdict=FAILED). 구조적 문제 해결 후 재시도 필요."
        preflight.ctx.audit_event.assert_called_once_with(
            "four_phase_failed",
            "retry budget exhausted",
            {"arc_no": 1, "retries": 3, "issues_count": 2},
        )

    def test_build_four_phase_failure_feedback_returns_internal_validation_message(self, preflight):
        feedback = preflight._build_four_phase_failure_feedback(
            pipeline_result={"final_verdict": "REJECT", "phases": {"validate": {"issues_count": 1}}},
            global_arc_no=1,
        )

        assert feedback == "FourPhase 내부 검증 실패. 구조적 문제 해결 필요."
        preflight.ctx.audit_event.assert_not_called()

    def test_build_four_phase_exception_feedback_emits_error_audit_event(self, preflight):
        feedback = preflight._build_four_phase_exception_feedback(
            fp_err=RuntimeError("four phase exploded"),
            global_arc_no=1,
        )

        assert feedback == "FourPhase 오류 발생: four phase exploded"
        preflight.ctx.audit_event.assert_called_once_with(
            "four_phase_error",
            "four phase exploded",
            {"arc_no": 1},
        )

    def test_build_four_phase_exception_feedback_allows_missing_audit_event(self, preflight):
        preflight.ctx.audit_event = None

        feedback = preflight._build_four_phase_exception_feedback(
            fp_err=RuntimeError("four phase exploded"),
            global_arc_no=1,
        )

        assert feedback == "FourPhase 오류 발생: four phase exploded"

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_run_four_phase_enrichment_cycle_routes_non_pass_result_to_failure_feedback(self, preflight):
        from modules.core.stage2_preflight import Stage2FourPhaseAttemptResult, Stage2FourPhaseCyclePayload

        preflight._build_stage2_vector_context = MagicMock(return_value="vector context")
        preflight.runtime.run_four_phase_generation_attempt = MagicMock(
            return_value=Stage2FourPhaseAttemptResult(
                four_phase_arc={"tactical_doc": "candidate"},
                pipeline_result={"final_verdict": "REJECT"},
                prev_score=82,
                was_patch=True,
                patch_fallback=True,
            )
        )
        preflight._build_four_phase_failure_feedback = MagicMock(return_value="tighten continuity")
        preflight.runtime.finalize_four_phase_pass = MagicMock()

        payload = preflight.runtime.run_four_phase_enrichment_cycle(
            attempt=1,
            global_arc_no=3,
            current_ep_start=21,
            current_vol_strategy={"volume": 3},
            enriched_block={"joint_docs": {}, "status_shadow": {}},
            all_refined_arcs=[{"arc_no": 1}],
            bible_root={"meta": "bible"},
            protagonist_name="Hero",
            director_feedback_for_fourphase="previous feedback",
            entity_registry_for_director={"Hero": {"role": "lead"}},
            genre_for_tracker="wuxia",
            previous_attempt={"score": 82},
        )

        assert payload == Stage2FourPhaseCyclePayload(
            director_feedback_for_fourphase="tighten continuity",
            prev_score=82,
            was_patch=True,
            patch_fallback=True,
        )
        preflight._build_stage2_vector_context.assert_called_once_with(
            global_arc_no=3,
            current_ep_start=21,
            enriched_block={"joint_docs": {}, "status_shadow": {}},
            current_vol_strategy={"volume": 3},
            protagonist_name="Hero",
        )
        preflight.runtime.run_four_phase_generation_attempt.assert_called_once()
        preflight._build_four_phase_failure_feedback.assert_called_once_with(
            pipeline_result={"final_verdict": "REJECT"},
            global_arc_no=3,
        )
        preflight.runtime.finalize_four_phase_pass.assert_not_called()

    def test_resolve_four_phase_attempt_cycle_payload_routes_pass_to_finalize(self, preflight):
        from modules.core.stage2_preflight import (
            Stage2FourPhaseAttemptResult,
            Stage2FourPhaseCyclePayload,
            Stage2FourPhasePassPayload,
        )

        preflight.runtime.finalize_four_phase_pass = MagicMock(
            return_value=Stage2FourPhasePassPayload(
                refined_arc={"tactical_doc": "PASS ARC"},
                generation_method="four_phase",
                four_phase_passed=True,
                draft_validator_passed=False,
                consensus_passed=False,
                st_snapshot={"registry": 1},
            )
        )
        preflight._build_four_phase_failure_feedback = MagicMock()

        payload = preflight.runtime.resolve_four_phase_attempt_cycle_payload(
            attempt=1,
            global_arc_no=3,
            enriched_block={"joint_docs": {}, "status_shadow": {}},
            genre_for_tracker="wuxia",
            director_feedback_for_fourphase="previous feedback",
            base_payload=Stage2FourPhaseCyclePayload(
                director_feedback_for_fourphase="previous feedback",
            ),
            attempt_result=Stage2FourPhaseAttemptResult(
                four_phase_arc={"tactical_doc": "candidate"},
                pipeline_result={"final_verdict": "PASS"},
                prev_score=82,
                was_patch=True,
                patch_fallback=False,
            ),
        )

        assert payload == Stage2FourPhaseCyclePayload(
            director_feedback_for_fourphase="previous feedback",
            four_phase_passed=True,
            refined_arc={"tactical_doc": "PASS ARC"},
            generation_method="four_phase",
            draft_validator_passed=False,
            consensus_passed=False,
            st_snapshot={"registry": 1},
            was_patch=True,
            patch_fallback=False,
            prev_score=82,
        )
        preflight.runtime.finalize_four_phase_pass.assert_called_once_with(
            attempt=1,
            global_arc_no=3,
            director_feedback_for_fourphase="previous feedback",
            refined_arc={"tactical_doc": "candidate"},
            pipeline_result={"final_verdict": "PASS"},
            enriched_block={"joint_docs": {}, "status_shadow": {}},
            genre_for_tracker="wuxia",
        )
        preflight._build_four_phase_failure_feedback.assert_not_called()

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_no_fourphase_returns_defaults(self, preflight):
        preflight.ctx.agents = {}
        out = preflight._preflight_enrichment(**_enrichment_kwargs())
        assert out["four_phase_passed"] is False
        assert out["refined_arc"] is None
        assert out["generation_method"] == "analyst"

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_fourphase_exception_non_propagating(self, preflight):
        preflight.ctx.agents["four_phase"].generate.side_effect = RuntimeError("fail")
        out = preflight._preflight_enrichment(**_enrichment_kwargs())
        assert out["four_phase_passed"] is False
        assert "FourPhase" in out["director_feedback_for_fourphase"]
        assert "fail" in out["director_feedback_for_fourphase"]

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_inplace_failure_falls_back_to_patch_mode_in_same_attempt(self, preflight):
        best_arc = {
            "arc_no": 1,
            "ep_start": 1,
            "ep_end": 10,
            "ep_count": 10,
            "tactical_doc": "ORIGINAL ARC " * 120,
            "state_changes": {},
            "state_constraints": {
                "arc_start_state": {"equipment": []},
                "arc_end_state": {"equipment": []},
            },
        }
        patched_arc = {
            "arc_no": 1,
            "ep_start": 1,
            "ep_end": 10,
            "ep_count": 10,
            "tactical_doc": "PATCHED ARC " * 140,
            "state_changes": {},
            "state_constraints": {
                "arc_start_state": {"equipment": []},
                "arc_end_state": {"equipment": []},
            },
        }
        previous_attempt = {
            "best_arc": best_arc,
            "fix_scope": "inplace",
            "score": 95,
            "rejection_reason": "keep structure, fix only local issue",
            "selection_reason": "candidate 2 was closest",
            "score_breakdown": {"continuity": 82, "clarity": 79},
            "validation_warnings": ["minor drift"],
            "selected_strategy": "ensemble_b",
        }

        preflight.ctx.agents["four_phase"]._inplace_patch_arc.return_value = None
        preflight.ctx.agents["four_phase"].patch_arc_with_feedback.return_value = (
            patched_arc,
            {"final_verdict": "PASS", "patch_mode": True, "patch_fallback": False},
        )
        preflight.ctx.agents["four_phase"].generate.side_effect = AssertionError("generate() should not be called")

        out = preflight._preflight_enrichment(**_enrichment_kwargs(previous_attempt=previous_attempt))

        assert out["four_phase_passed"] is True
        assert out["generation_method"] == "four_phase"
        assert out["was_patch"] is True
        assert out["patch_fallback"] is False
        assert out["refined_arc"]["tactical_doc"].startswith("PATCHED ARC")

        preflight.ctx.agents["four_phase"]._inplace_patch_arc.assert_called_once_with(
            original_arc=best_arc,
            director_feedback="keep structure, fix only local issue",
            arc_no=1,
        )
        preflight.ctx.agents["four_phase"].patch_arc_with_feedback.assert_called_once()
        patch_kwargs = preflight.ctx.agents["four_phase"].patch_arc_with_feedback.call_args.kwargs
        assert patch_kwargs["original_arc"] == best_arc
        assert patch_kwargs["attempt_number"] == 1
        assert patch_kwargs["rejected_strategy"] == "ensemble_b"
        assert "keep structure, fix only local issue" in patch_kwargs["director_feedback"]
        assert "candidate 2 was closest" in patch_kwargs["director_feedback"]
        assert "minor drift" in patch_kwargs["director_feedback"]
        preflight.ctx.agents["four_phase"].generate.assert_not_called()

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_missing_fix_scope_skips_local_patch_and_uses_full_generate(self, preflight):
        best_arc = {
            "arc_no": 1,
            "ep_start": 1,
            "ep_end": 10,
            "ep_count": 10,
            "tactical_doc": "ORIGINAL ARC " * 120,
            "state_changes": {},
            "state_constraints": {
                "arc_start_state": {"equipment": []},
                "arc_end_state": {"equipment": []},
            },
        }
        regenerated_arc = {
            "arc_no": 1,
            "ep_start": 1,
            "ep_end": 10,
            "ep_count": 10,
            "tactical_doc": "REGENERATED ARC " * 140,
            "state_changes": {},
            "state_constraints": {
                "arc_start_state": {"equipment": []},
                "arc_end_state": {"equipment": []},
            },
        }
        previous_attempt = {
            "best_arc": best_arc,
            "fix_scope": "",
            "score": 95,
            "rejection_reason": "director forgot to provide explicit local scope",
            "selection_reason": "candidate 2 was closest",
        }

        preflight.ctx.agents["four_phase"]._inplace_patch_arc.side_effect = AssertionError("_inplace_patch_arc() should not be called")
        preflight.ctx.agents["four_phase"].patch_arc_with_feedback.side_effect = AssertionError(
            "patch_arc_with_feedback() should not be called"
        )
        preflight.ctx.agents["four_phase"].generate.return_value = (
            regenerated_arc,
            {"final_verdict": "PASS", "patch_mode": False, "patch_fallback": False},
        )

        out = preflight._preflight_enrichment(**_enrichment_kwargs(previous_attempt=previous_attempt))

        assert out["four_phase_passed"] is True
        assert out["generation_method"] == "four_phase"
        assert out["was_patch"] is False
        assert out["patch_fallback"] is False
        assert out["refined_arc"]["tactical_doc"].startswith("REGENERATED ARC")
        preflight.ctx.agents["four_phase"].generate.assert_called_once()

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_fourphase_pass_triggers_state_tracker_enrichment(self, preflight):
        tracker = MagicMock()
        tracker.npc_registry = {"npc": {"status": "alive"}}
        tracker.resolved_plots = []
        tracker.entity_destructions = []
        tracker.protagonist_skills = set()
        tracker.skill_acquisitions = []
        tracker.npc_npc_relationships = {}
        tracker.item_state_registry = {}
        tracker.active_plots = []
        tracker.npc_dialogue_profiles = {}
        tracker.in_world_timeline = []
        tracker.current_companions = []
        tracker.pending_commitments = []
        tracker.protagonist_emotion = {}
        tracker.extract_npc_deaths_from_arc.return_value = ["npc1"]
        tracker.extract_skill_acquisitions_from_arc.return_value = ["skill1"]
        tracker.extract_npc_info_from_arc.return_value = [{"name": "npc1"}]
        tracker.check_suspended_plots.return_value = []
        tracker.generate_arc_summary.return_value = {"summary": "ok"}
        tracker.cleanup_npc_registry_with_llm.return_value = []
        preflight.ctx.state_tracker = tracker

        refined_arc = {
            "tactical_doc": "x" * 1600,
            "joint_docs": {},
            "status_shadow": {},
        }
        preflight.ctx.agents["four_phase"].generate.return_value = (
            refined_arc,
            {"final_verdict": "PASS", "phases": {"generate": {"candidates_count": 3, "selected_strategy": "s"}}},
        )

        out = preflight._preflight_enrichment(**_enrichment_kwargs(global_arc_no=5, all_refined_arcs=[{"arc_no": 1}]))
        assert out["four_phase_passed"] is True
        assert out["generation_method"] == "four_phase"
        tracker.extract_npc_deaths_from_arc.assert_called_once()
        tracker.extract_skill_acquisitions_from_arc.assert_called_once()
        preflight.ctx.current_project.save_v20_anchor.assert_called()

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_legacy_vector_fallback_without_advisor(self, preflight):
        preflight.ctx.context_advisor = None
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_high_res_context.return_value = "legacy vector block"
        preflight.ctx.memory.retrieve_multi_query_context = MagicMock()
        preflight.ctx.memory.retrieve_npc_context = MagicMock()

        preflight._preflight_enrichment(**_enrichment_kwargs(current_ep_start=3))

        preflight.ctx.memory.retrieve_high_res_context.assert_called_once()
        assert not preflight.ctx.memory.retrieve_multi_query_context.called
        assert not preflight.ctx.memory.retrieve_npc_context.called
        call_kwargs = preflight.ctx.agents["four_phase"].generate.call_args.kwargs
        assert call_kwargs["vector_context"].startswith("[작품 추적 슬롯 요약]")
        assert "legacy vector block" in call_kwargs["vector_context"]

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_fact_ledger_context_prepended_to_fourphase_vector_context(self, preflight):
        preflight.ctx.context_advisor = None
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_high_res_context.return_value = "legacy vector block"
        preflight.ctx.current_project.db.load_anchor.side_effect = lambda key: (
            {"numbers": {"자본금": {"value": "10억", "unit": "원", "last_ep": 8}}} if key == "fact_ledger" else {}
        )

        preflight._preflight_enrichment(**_enrichment_kwargs(current_ep_start=3))

        call_kwargs = preflight.ctx.agents["four_phase"].generate.call_args.kwargs
        assert "[팩트 원장 핵심 수치]" in call_kwargs["vector_context"]
        assert "legacy vector block" in call_kwargs["vector_context"]

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_advisor_plan_dispatches_vec_and_npc_sources(self, preflight):
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_high_res_context = MagicMock(return_value="legacy")
        preflight.ctx.memory.retrieve_multi_query_context = MagicMock(side_effect=["vec one", "vec two"])
        preflight.ctx.memory.retrieve_npc_context = MagicMock(return_value="npc one")
        preflight.ctx.context_advisor = MagicMock()
        preflight.ctx.sys = MagicMock()
        preflight.ctx.sys.guard = MagicMock()
        preflight.ctx.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["핵심 배우 라인"],
            "mandatory_scene_engines": ["인재 발굴"],
            "registry_profiles": [
                {"name": "talent_registry", "required_fields": ["name", "heat", "fan_reaction"]}
            ],
        }
        preflight.ctx.context_advisor.plan_stage2_retrieval.return_value = RetrievalPlan(
            stage="stage2",
            episode_num=3,
            slots=[
                RetrievalSlot(category="block_theme", query="theme query", source="vec_memory", priority=1),
                RetrievalSlot(category="npc_recent", query="alice bob", source="db_npc_history", priority=1),
                RetrievalSlot(category="arc_tactical", query="tactical query", source="vec_memory", priority=2),
            ],
            total_budget_chars=2000,
        )

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage2_enabled":
                return True
            if key == "context.vector_max_results_s2":
                return 8
            return default

        with patch("modules.core.stage2_preflight._threshold", side_effect=threshold_side_effect):
            preflight._preflight_enrichment(
                **_enrichment_kwargs(
                    current_ep_start=3,
                    enriched_block={
                        "block_theme": "theme",
                        "tactical_doc": "tactical",
                        "npc_roster": ["alice", "bob"],
                        "joint_docs": {},
                        "status_shadow": {},
                    },
                )
            )

        preflight.ctx.context_advisor.plan_stage2_retrieval.assert_called_once()
        call_kwargs = preflight.ctx.context_advisor.plan_stage2_retrieval.call_args.kwargs
        assert call_kwargs["work_focus"]["tracking_slots"] == ["핵심 배우 라인"]
        assert preflight.ctx.memory.retrieve_multi_query_context.call_count == 2
        preflight.ctx.memory.retrieve_npc_context.assert_called_once()
        preflight.ctx.memory.retrieve_high_res_context.assert_not_called()

        npc_call = preflight.ctx.memory.retrieve_npc_context.call_args.kwargs
        assert npc_call["npc_names"][:2] == ["alice", "bob"]

        vector_context = preflight.ctx.agents["four_phase"].generate.call_args.kwargs["vector_context"]
        assert "[작품 추적 슬롯 요약]" in vector_context
        assert "핵심 배우 라인" in vector_context
        assert "[SC:block_theme]" in vector_context
        assert "[SC:npc_recent]" in vector_context
        assert "[SC:arc_tactical]" in vector_context

    def test_work_focus_relation_slice_included_in_vector_context(self, preflight):
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_multi_query_context = MagicMock(return_value="vec one")
        preflight.ctx.context_advisor = MagicMock()
        preflight.ctx.quality_dashboard = MagicMock()
        preflight.ctx.sys = MagicMock()
        preflight.ctx.sys.guard = MagicMock()
        preflight.ctx.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["소꿉친구 관계선"],
            "mandatory_scene_engines": [],
            "registry_profiles": [],
        }
        preflight.ctx.world_state = MagicMock()
        preflight.ctx.world_state.get_state_dict.return_value = {"relationships": {"연홍": "죽마고우"}}
        preflight.ctx.fact_ledger = MagicMock()
        preflight.ctx.fact_ledger._ledger = {
            "characters": {"연홍": {"relationship": "소꿉친구", "established_ep": 3, "history": []}}
        }
        preflight.ctx.current_project.db.get_npc_relationship_edges.return_value = [
            {"npc1": "주인공", "npc2": "연홍", "relation": "죽마고우", "updated_ep": 3}
        ]
        preflight.ctx.current_project.db.get_relationship_history.return_value = [
            {"old_relation": "친구", "new_relation": "죽마고우", "change_ep": 3}
        ]
        preflight.ctx.context_advisor.plan_stage2_retrieval.return_value = RetrievalPlan(
            stage="stage2",
            episode_num=3,
            slots=[RetrievalSlot(category="block_theme", query="theme query", source="vec_memory", priority=1)],
            total_budget_chars=2000,
        )

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage2_enabled":
                return True
            if key == "context.vector_max_results_s2":
                return 8
            return default

        with patch("modules.core.stage2_preflight._threshold", side_effect=threshold_side_effect):
            preflight._preflight_enrichment(
                **_enrichment_kwargs(
                    current_ep_start=3,
                    protagonist_name="주인공",
                    enriched_block={
                        "block_theme": "relation repair",
                        "constraint_summary": "소꿉친구와 관계 회복",
                        "joint_docs": {},
                        "status_shadow": {},
                    },
                )
            )

        vector_context = preflight.ctx.agents["four_phase"].generate.call_args.kwargs["vector_context"]
        preflight.ctx.quality_dashboard.record_retrieval_observation.assert_called_once()
        kwargs = preflight.ctx.quality_dashboard.record_retrieval_observation.call_args.kwargs
        assert kwargs["stage"] == "stage2"
        assert kwargs["observation"]["relation_slice_included"] is True
        assert kwargs["observation"]["provenance_ledger"]["source_pack"] == "stage2"
        assert kwargs["observation"]["budget_ledger"]["budget_bucket"] == "smart_retrieval.stage2_total_budget"
        assert "[관계 의미 질의]" in vector_context
        assert "연홍" in vector_context


class TestGlobalBudgetTruncation:
    """P1-3: stage2 글로벌 예산 가드 검증."""

    def test_global_budget_truncation(self, preflight):
        """결합 텍스트가 total_budget_chars 초과 시 절단."""
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_multi_query_context.return_value = "x" * 5000
        preflight.ctx.memory.retrieve_npc_context.return_value = "y" * 5000

        plan = RetrievalPlan(
            stage="stage2",
            episode_num=5,
            slots=[
                RetrievalSlot(category="block_theme", query="theme query", source="vec_memory", priority=1),
                RetrievalSlot(category="npc_recent", query="npc query", source="db_npc_history", priority=2),
            ],
            total_budget_chars=100,
        )

        result = preflight._execute_stage2_retrieval_plan(plan, current_ep=5)
        assert len(result) <= 100

    def test_global_budget_truncation_preserves_recent_tail_context(self, preflight):
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_multi_query_context.return_value = "HEAD-A " + ("a" * 240) + " TAIL-A"
        preflight.ctx.memory.retrieve_npc_context.return_value = "HEAD-B " + ("b" * 240) + " TAIL-B"

        plan = RetrievalPlan(
            stage="stage2",
            episode_num=5,
            slots=[
                RetrievalSlot(category="block_theme", query="theme query", source="vec_memory", priority=1),
                RetrievalSlot(category="npc_recent", query="npc query", source="db_npc_history", priority=2),
            ],
            total_budget_chars=140,
        )

        result = preflight._execute_stage2_retrieval_plan(plan, current_ep=5)
        assert len(result) <= 140
        assert "[SC:block_theme]" in result
        assert "TAIL-B" in result
