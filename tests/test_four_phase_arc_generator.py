"""FourPhaseArcGenerator regression tests for pre-collected state normalization."""

from unittest.mock import MagicMock, patch

from modules.core.response_schemas import ARC_STATE_SCHEMA
from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator
from modules.domain.agents.four_phase_arc_runtime import (
    FourPhaseArcRuntime,
    _FourPhaseConstraintEnvelope,
    _FourPhaseGenerationEnvelope,
)


def _make_generator() -> FourPhaseArcGenerator:
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen.context = MagicMock()
    gen.context.master_bible = {}
    gen.stats = {
        "total_attempts": 0,
        "phase1_complete": 0,
        "phase2_complete": 0,
        "phase3_pass": 0,
        "phase3_reject": 0,
    }
    gen.preflight = MagicMock()
    gen.preflight.analyze.return_value = {}
    gen.preflight.generate_analyst_injection.return_value = "preflight"
    gen.compiler = MagicMock()
    gen.compiler.compile.return_value = "constraints"
    gen.negative_injector = MagicMock()
    gen.negative_injector.generate_injection.return_value = "neg"
    gen.negative_injector.generate_self_check_prompt.return_value = "self_check"
    gen.negative_injector.record_rejection = MagicMock()
    gen._genre = "wuxia"
    gen._flash_ask = None
    gen.ensemble = MagicMock()
    gen.ensemble.generate_ensemble.return_value = (
        None,
        [{"_ensemble_meta": {"best_strategy": "balanced"}, "tactical_doc": "mock tactical"}],
    )
    gen.validator = MagicMock()
    gen.validator.validate.return_value = ("PASS", {"issues": [], "confidence": 90})
    gen._determine_ep_count = MagicMock(return_value=(4, "reason"))
    gen._generate_prev_context = MagicMock(return_value="prev")
    gen._check_arc_end_state = MagicMock(side_effect=lambda arc: arc)
    gen.runtime = FourPhaseArcRuntime(gen)
    return gen


def test_resolve_constraint_phase_reuses_cached_block():
    gen = _make_generator()
    pipeline_result = {"phases": {}}

    envelope = gen.runtime._resolve_constraint_phase(
        retry=1,
        prev_arcs=[{"arc_no": 0}],
        cached_constraint_block="cached-block",
        cached_preflight={"cached": True},
        pipeline_result=pipeline_result,
    )

    assert envelope.full_constraint_block == "cached-block"
    assert envelope.preflight_result == {"cached": True}
    assert envelope.cached_constraint_block == "cached-block"
    assert envelope.cached_preflight == {"cached": True}
    assert pipeline_result["phases"]["constraint"]["status"] == "cached"
    gen.preflight.analyze.assert_not_called()
    gen.compiler.compile.assert_not_called()


def test_run_generation_phase_short_circuits_on_generate_failure():
    gen = _make_generator()
    gen.ensemble.generate_ensemble.return_value = (None, [])
    pipeline_result = {"phases": {}}

    envelope = gen.runtime._run_generation_phase(
        retry=0,
        arc_no=1,
        ep_start=1,
        vol_strategy="std",
        curr_block={},
        prev_arcs=[],
        assets=None,
        protagonist_name="주인공",
        entity_registry=None,
        state_tracker=None,
        vector_context="",
        adversarial_self_play=None,
        protagonist_config={},
        ep_count_suggestion=4,
        pacing_signals={},
        full_constraint_block="constraints",
        preflight_result={},
        feedback="seed feedback",
        base_director_feedback="[base]",
        prev_rejected_arc=None,
        prev_reject_feedback="",
        prev_selected_strategy="",
        spare_candidates=[],
        pipeline_result=pipeline_result,
    )

    assert envelope.best_arc is None
    assert envelope.all_candidates == []
    assert envelope.should_continue is True
    assert envelope.feedback == "[base]\nEnsemble 생성 실패. 다시 시도하세요."
    assert pipeline_result["phases"]["generate"]["status"] == "failed"


def test_initialize_generate_state_carries_bootstrap_defaults():
    gen = _make_generator()

    state = gen.runtime._initialize_generate_state(
        arc_no=2,
        curr_block={"title": "block"},
        prev_arcs=[{"state_constraints": {"items_acquired": [{"name": "천검"}]}}],
        director_feedback="재정 수치 보강",
    )

    assert state.ep_count_suggestion == 4
    assert state.cached_constraint_block is None
    assert state.cached_preflight is None
    assert "천검" in state.pre_items
    assert "재정 수치 보강" in state.feedback


def test_generate_returns_failed_pipeline_after_retry_exhaustion():
    gen = _make_generator()
    gen.runtime._resolve_constraint_phase = MagicMock(
        return_value=_FourPhaseConstraintEnvelope(
            full_constraint_block="constraints",
            preflight_result={},
            cached_constraint_block=None,
            cached_preflight=None,
        )
    )
    gen.runtime._run_generation_phase = MagicMock(
        return_value=_FourPhaseGenerationEnvelope(
            best_arc=None,
            all_candidates=[],
            prev_arc_context="",
            feedback="retry feedback",
            prev_rejected_arc=None,
            prev_reject_feedback="",
            prev_selected_strategy="",
            spare_candidates=[],
            should_continue=True,
        )
    )

    arc, pipeline_result = gen.runtime.generate(
        arc_no=1,
        ep_start=1,
        vol_strategy="std",
        curr_block={},
        prev_arcs=[],
        max_internal_retries=1,
    )

    assert arc is None
    assert pipeline_result["final_verdict"] == "FAILED"
    assert pipeline_result["retries"] == 1
    assert gen.runtime._run_generation_phase.call_count == 2


def test_prepare_candidates_for_selection_injects_forced_location():
    gen = _make_generator()
    gen._load_execution_state = MagicMock(return_value={"protagonist_location": "부산"})
    candidates = [{"tactical_doc": "mock tactical", "state_constraints": {"arc_start_state": {}, "arc_end_state": {}}}]

    envelope = gen.runtime._prepare_candidates_for_selection(
        arc_no=1,
        curr_block={},
        prev_arcs=[{"state_constraints": {"arc_end_state": {"location": "서울"}}}],
        all_candidates=candidates,
    )

    assert envelope.all_candidates[0]["state_constraints"]["arc_start_state"]["location"] == "부산"
    assert envelope.ns3b_director_advisory == ""
    assert envelope.investment_director_advisory == ""
    assert len(envelope.candidate_quality_flags) == 1


def test_run_director_selection_phase_reject_updates_retry_state():
    gen = _make_generator()
    rejected = {"_strategy": "aggressive", "tactical_doc": "reject tactical"}
    spare = {"_strategy": "balanced", "tactical_doc": "spare tactical"}
    director = MagicMock()
    director.compare_and_select_arc.return_value = {
        "decision": "REJECT",
        "selected_arc": rejected,
        "feedback": "구조를 다시 정리하라",
        "score": 41,
    }
    pipeline_result = {"phases": {}}

    envelope = gen.runtime._run_director_selection_phase(
        director=director,
        arc_no=1,
        curr_block={},
        prev_arc_context="prev",
        full_constraint_block="constraints",
        all_candidates=[rejected, spare],
        candidate_quality_flags=[{}, {}],
        ns3b_director_advisory="",
        investment_director_advisory="",
        investment_advisory=[],
        base_director_feedback="[base]",
        feedback="seed",
        prev_rejected_arc=None,
        prev_reject_feedback="",
        prev_selected_strategy="",
        spare_candidates=[],
        pipeline_result=pipeline_result,
    )

    assert envelope.should_continue is True
    assert envelope.best_arc is rejected
    assert envelope.prev_rejected_arc is rejected
    assert envelope.prev_reject_feedback == "[base]\n[Director 비교 피드백]\n구조를 다시 정리하라"
    assert envelope.prev_selected_strategy == "aggressive"
    assert envelope.spare_candidates == [spare]
    assert pipeline_result["phases"]["director_selection"]["status"] == "reject"


def test_run_phase3_validation_reject_clears_spares_on_low_confidence():
    gen = _make_generator()
    gen.validator.validate.return_value = (
        "REJECT",
        {
            "issues": [{"severity": "MAJOR", "category": "logic", "issue": "불일치"}],
            "confidence": 0.3,
            "feedback": "검증 피드백",
        },
    )
    best_arc = {"_strategy": "balanced", "_ensemble_meta": {"best_strategy": "balanced"}}
    pipeline_result = {"phases": {}}

    envelope = gen.runtime._run_phase3_validation(
        arc_no=1,
        retry=0,
        max_internal_retries=2,
        curr_block={},
        best_arc=best_arc,
        all_candidates=[best_arc],
        full_constraint_block="constraints",
        prev_arcs=[],
        state_tracker=None,
        pre_items=set(),
        pre_grants=set(),
        feedback="seed",
        base_director_feedback="[base]",
        investment_advisory=[],
        prev_rejected_arc=None,
        prev_reject_feedback="",
        prev_selected_strategy="",
        spare_candidates=[{"_strategy": "other", "tactical_doc": "other"}],
        pipeline_result=pipeline_result,
    )

    assert envelope.should_continue is True
    assert envelope.prev_rejected_arc is best_arc
    assert envelope.prev_reject_feedback == "[base]\n[검증 피드백]\n검증 피드백"
    assert envelope.prev_selected_strategy == "balanced"
    assert envelope.spare_candidates == []
    gen.negative_injector.record_rejection.assert_called_once()
    assert pipeline_result["phases"]["validate"]["verdict"] == "REJECT"


def test_pre_collected_items_normalizes_dict_item_name():
    gen = _make_generator()
    prev_arcs = [
        {
            "state_constraints": {
                "items_acquired": [
                    {"name": "철검"},
                    {"item": "현천패"},
                ]
            }
        }
    ]

    arc, pipeline_result = gen.runtime.generate(
        arc_no=1,
        ep_start=1,
        vol_strategy="std",
        curr_block={},
        prev_arcs=prev_arcs,
    )

    assert arc is not None
    assert pipeline_result["final_verdict"] == "PASS"
    pre_collected_items = gen.validator.validate.call_args.kwargs["pre_collected_items"]
    assert "철검" in pre_collected_items
    assert "현천패" in pre_collected_items
    assert "{'name': '철검'}" not in pre_collected_items


def test_generate_passes_pacing_suggestion_and_density_signals():
    gen = _make_generator()
    gen._determine_ep_count = MagicMock(return_value=(2, "compressed reason"))
    curr_block = {
        "title": "저자원 블록",
        "context": "주인공이 다음 수를 고민한다. 긴장이 남아 있다.",
        "content": "설명만 늘이지 말고 사건을 촘촘하게 전개해야 한다.",
        "tension_level": 2,
    }

    arc, pipeline_result = gen.runtime.generate(
        arc_no=1,
        ep_start=1,
        vol_strategy="std",
        curr_block=curr_block,
        prev_arcs=[],
    )

    assert arc is not None
    assert pipeline_result["final_verdict"] == "PASS"
    call_kwargs = gen.ensemble.generate_ensemble.call_args.kwargs
    assert call_kwargs["ep_count_suggestion"] == 2
    pacing_signals = call_kwargs["pacing_signals"]
    assert pacing_signals["ep_count_suggestion"] == 2
    assert pacing_signals["suggested_pace_mode"] == "compressed"
    assert pacing_signals["low_resource_block"] is True
    assert pacing_signals["reward_present"] is False


def test_pre_collected_grants_normalizes_dict_item_name():
    gen = _make_generator()
    prev_arcs = [
        {
            "state_constraints": {
                "grants_received": [
                    {"name": "공훈패"},
                    {"item": "명예훈장"},
                ]
            }
        }
    ]

    arc, pipeline_result = gen.runtime.generate(
        arc_no=1,
        ep_start=1,
        vol_strategy="std",
        curr_block={},
        prev_arcs=prev_arcs,
    )

    assert arc is not None
    assert pipeline_result["final_verdict"] == "PASS"
    pre_collected_grants = gen.validator.validate.call_args.kwargs["pre_collected_grants"]
    assert "공훈패" in pre_collected_grants
    assert "명예훈장" in pre_collected_grants
    assert "{'name': '공훈패'}" not in pre_collected_grants


# [TF-59] 재무 상태 연속성 테스트


def test_arc_state_schema_backward_compat_without_capital():
    """[TF-59] ARC_STATE_SCHEMA: capital 없이도 required 통과 (무협 하위호환)."""
    required_fields = set(ARC_STATE_SCHEMA.required)
    optional_fields = {"capital", "total_assets", "portfolio_position"}

    # required는 기존 4개만
    assert required_fields == {"location", "equipment", "injuries", "internal_energy"}
    # 신규 재무 필드는 optional (required에 없음)
    assert optional_fields.isdisjoint(required_fields)
    # 신규 재무 필드는 properties에 존재
    for field in optional_fields:
        assert field in ARC_STATE_SCHEMA.properties, f"{field} not in ARC_STATE_SCHEMA.properties"


def test_generate_prev_context_includes_financial_fields():
    """[TF-59] arc_end_state에 재무 필드 있으면 _generate_prev_context 출력에 포함."""
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen._genre = "investment"

    prev_arcs = [
        {
            "arc_no": 1,
            "state_constraints": {
                "arc_end_state": {
                    "location": "서울",
                    "equipment": [],
                    "injuries": "없음",
                    "internal_energy": 100,
                    "capital": "5억원",
                    "total_assets": "10억원",
                    "portfolio_position": "삼성전자 1000주 보유",
                }
            },
            "joint_docs": {},
            "status_shadow": {},
        }
    ]

    with patch.object(gen, "_load_execution_state", return_value=None):
        result = gen._generate_prev_context(prev_arcs, preflight_result={})

    assert "자본금" in result
    assert "5억원" in result
    assert "총자산" in result
    assert "10억원" in result
    assert "포지션" in result
    assert "삼성전자 1000주 보유" in result


def test_build_prev_context_carryover_lines_direct_helper_includes_financial_fields():
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen._genre = "investment"

    last_arc = {
        "arc_no": 1,
        "state_constraints": {
            "arc_end_state": {
                "location": "서울",
                "equipment": [],
                "injuries": "없음",
                "internal_energy": 100,
                "capital": "5억원",
                "total_assets": "10억원",
                "portfolio_position": "삼성전자 1000주 보유",
            }
        },
        "joint_docs": {},
        "status_shadow": {},
    }

    result = "\n".join(gen._build_prev_context_carryover_lines(last_arc, 1))

    assert "자본금" in result
    assert "5억원" in result
    assert "총자산" in result
    assert "포지션" in result


def test_extract_current_state_includes_financial_keys():
    """[TF-59] _extract_current_state()가 재무 키(capital/total_assets/portfolio_position) 포함."""
    from modules.domain.agents.constraint_compiler import ConstraintCompiler

    compiler = ConstraintCompiler.__new__(ConstraintCompiler)

    # 폴백 경로: state_extractor_result=None, arc_end_state에 재무 필드 있음
    last_arc = {
        "joint_docs": {"final_location": "부산", "physical_inventory": []},
        "state_constraints": {
            "arc_end_state": {
                "capital": "3억원",
                "total_assets": "7억원",
                "portfolio_position": "현금 보유",
            }
        },
    }
    state = compiler._extract_current_state(last_arc, state_extractor_result=None)
    assert state["capital"] == "3억원"
    assert state["total_assets"] == "7억원"
    assert state["portfolio_position"] == "현금 보유"

    # state_extractor_result 경로: protagonist에 재무 필드 있음
    ser = {
        "protagonist_state": {
            "location": {"current": "서울"},
            "internal_energy": 100,
            "injuries": [],
            "capital": "2억원",
            "total_assets": "5억원",
            "portfolio_position": "채권 50%",
        },
        "inventory": {"current_items": []},
        "next_arc_constraints": {},
    }
    state2 = compiler._extract_current_state({}, state_extractor_result=ser)
    assert state2["capital"] == "2억원"
    assert state2["total_assets"] == "5억원"
    assert state2["portfolio_position"] == "채권 50%"


# [TF-60] 위치 트림 + 비무협 정신력 금지 테스트


def test_trim_location_long_string():
    """[TF-60] 80자+ 위치는 트림되고, 핵심 지명(지역명)은 보존."""
    from modules.domain.agents.four_phase_arc_generator import _trim_location

    long_loc = (
        "서울 강남구 테헤란로, SW인베스트먼트 개인 오피스. 책상 위 3개의 모니터 중 "
        "중앙 모니터에 WTI 실시간 시세창이 켜져 있고, 가격은 65.12달러에서 등락을 반복하고 있다."
    )
    result = _trim_location(long_loc)
    assert len(result) <= 80, f"트림 후에도 80자 초과: {len(result)}자"
    assert "서울 강남구 테헤란로" in result, "핵심 지명이 사라짐"


def test_trim_location_short_string():
    """[TF-60] 80자 이하는 그대로 반환."""
    from modules.domain.agents.four_phase_arc_generator import _trim_location

    short_loc = "서울 강남구 테헤란로"
    assert _trim_location(short_loc) == short_loc


def test_non_wuxia_constraint_block_has_energy_warning():
    """[TF-60] 비무협 장르에서 constraint_block에 정신력/내공/마나 금지 지시 포함."""
    gen = _make_generator()
    gen._genre = "investment"

    arc, _ = gen.runtime.generate(
        arc_no=1,
        ep_start=1,
        vol_strategy="std",
        curr_block={},
        prev_arcs=[],
    )

    call_kwargs = gen.ensemble.generate_ensemble.call_args.kwargs
    constraint_block = call_kwargs.get("constraint_block", "")
    assert "정신력" in constraint_block, "비무협 장르에 정신력 금지 지시 없음"
    assert "내공" in constraint_block
    assert "마나" in constraint_block


def test_wuxia_constraint_block_no_energy_warning():
    """[TF-60] 무협 장르에서는 정신력 금지 지시 없음 (내공 사용 허용)."""
    gen = _make_generator()
    gen._genre = "wuxia"

    gen.runtime.generate(
        arc_no=1,
        ep_start=1,
        vol_strategy="std",
        curr_block={},
        prev_arcs=[],
    )

    call_kwargs = gen.ensemble.generate_ensemble.call_args.kwargs
    constraint_block = call_kwargs.get("constraint_block", "")
    # 무협은 경고 없음 — 단, 다른 constraint는 존재
    assert "이 작품은 wuxia 장르" not in constraint_block


def test_generate_prev_context_dict_in_conflicts_no_typeerror():
    """[TF-60-T3] ongoing_conflicts/resolved_conflicts에 dict 항목이 있어도 TypeError 없음."""
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen._genre = "investment"

    prev_arcs = [
        {
            "arc_no": 1,
            "state_constraints": {
                "arc_end_state": {
                    "location": "서울",
                    "equipment": [],
                    "injuries": "없음",
                    "internal_energy": 100,
                }
            },
            "joint_docs": {},
            "status_shadow": {},
        }
    ]
    preflight_result = {
        "world_state": {
            "ongoing_conflicts": [
                {"conflict": "투자 갈등", "severity": "high"},
                "일반 갈등",
            ],
            "resolved_conflicts": [
                {"plot": "계약 분쟁 해결"},
                "단순 완결 갈등",
            ],
        }
    }

    with patch.object(gen, "_load_execution_state", return_value=None):
        result = gen._generate_prev_context(prev_arcs, preflight_result=preflight_result)

    assert "진행 중인 갈등" in result
    assert "완결된 갈등" in result


def test_load_execution_state_reads_fact_ledger_numbers_schema():
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen.context = MagicMock()
    gen.context.current_project = MagicMock()
    db = MagicMock()
    db.load_anchor.side_effect = lambda key: {
        "world_state": {
            "protagonist": {"assets": {"현금": "10억"}, "location": "서울", "status": {"건강": "양호"}},
            "active_items": {"청룡검": {"status": "보유"}},
            "motivations": [{"text": "복수", "status": "active", "since_ep": 3}],
            "promises": [{"text": "사부를 지킨다", "status": "pending", "promiser": "주인공", "since_ep": 4}],
            "cumulative_elapsed": {"total_days": 42},
        },
        "fact_ledger": {
            "numbers": {
                "자본금": {
                    "value": "10억",
                    "unit": "원",
                    "established_value": "1억",
                    "established_ep": 1,
                    "last_ep": 12,
                }
            }
        },
    }.get(key, {})
    db.get_episode_bible.return_value = {
        "ep_num": 12,
        "capital": "10억",
        "total_assets": "30억",
        "new_items": [],
        "location": "서울",
    }
    gen.context.current_project.db = db

    state = gen._load_execution_state({"ep_end": 12})

    assert state["fact_ledger"]["자본금"]["value"] == "10억"
    assert state["fact_ledger"]["자본금"]["established_value"] == "1억"
    assert "자본금" in state["fact_ledger_summary"]
    assert state["motivations"][0]["text"] == "복수"
    assert state["promises"][0]["text"] == "사부를 지킨다"
    assert state["cumulative_elapsed"]["total_days"] == 42


def test_generate_prev_context_includes_execution_state_motivations_and_fact_ledger():
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen._genre = "investment"

    prev_arcs = [
        {
            "arc_no": 1,
            "state_constraints": {
                "arc_end_state": {
                    "location": "서울",
                    "equipment": [],
                    "injuries": "없음",
                    "internal_energy": 100,
                }
            },
            "joint_docs": {},
            "status_shadow": {},
        }
    ]

    execution_state = {
        "motivations": [{"text": "복수", "since_ep": 3}],
        "promises": [{"text": "사부를 지킨다", "promiser": "주인공", "since_ep": 4}],
        "cumulative_elapsed": {"total_days": 42},
        "fact_ledger_summary": "[팩트 원장 핵심 수치]\n- 자본금: 1억 원 (ep1) -> 10억 원 (ep12)",
    }

    with patch.object(gen, "_load_execution_state", return_value=execution_state):
        result = gen._generate_prev_context(prev_arcs, preflight_result={})

    assert "핵심 동기" in result
    assert "복수" in result
    assert "미이행 약속" in result
    assert "사부를 지킨다" in result
    assert "누적 경과: 총 42일" in result
    assert "[팩트 원장 핵심 수치]" in result


def test_generate_prev_context_includes_stage_attempt_and_quality_feedback():
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen._genre = "investment"
    gen.context = MagicMock()
    gen.context.current_project = MagicMock()
    db = MagicMock()
    db.get_stage_attempts_for_arc.return_value = [
        {"failure_category": "continuity", "reject_reason": "위치 텔레포트", "stage": 4},
        {"failure_category": "continuity", "reject_reason": "위치 텔레포트", "stage": 4},
        {"failure_category": "pacing", "reject_reason": "호흡 급변", "stage": 3},
    ]
    db.get_recent_episode_scores.return_value = [
        {"ep_num": 8, "score": 91, "verdict": "PASS"},
        {"ep_num": 9, "score": 84, "verdict": "PASS"},
        {"ep_num": 10, "score": 77, "verdict": "PASS"},
    ]
    gen.context.current_project.db = db

    prev_arcs = [
        {
            "arc_no": 2,
            "ep_start": 7,
            "ep_end": 10,
            "state_constraints": {"arc_end_state": {"location": "서울", "equipment": [], "injuries": "없음", "internal_energy": 100}},
            "joint_docs": {},
            "status_shadow": {},
        }
    ]

    with (
        patch.object(gen, "_load_execution_state", return_value=None),
        patch("modules.domain.agents.four_phase_arc_generator.FailureAnalyzer") as analyzer_cls,
    ):
        analyzer = analyzer_cls.return_value
        analyzer.summary.return_value = {
            "stage_pass_rates": {"stage_4": {"pass_rate_pct": 68.0, "total_attempts": 22}},
            "top_failed_agents": [{"agent": "chief_writer", "fail_rate_pct": 55.0}],
            "top_failure_categories": [{"category": "continuity", "count": 5}],
            "quality_distribution": {"avg_score": 82.3, "high_score_count": 2},
            "top_success_patterns": [{"description": "blueprint_coverage 평균 18.5점"}],
        }
        result = gen._generate_prev_context(prev_arcs, preflight_result={})

    assert "[직전 Arc Stage3/4 주요 실패]" in result
    assert "continuity" in result
    assert "[이전 Arc 실패 분석]" in result
    assert "chief_writer" in result
    assert "[직전 Arc 고득점 패턴]" in result
    assert "blueprint_coverage 평균 18.5점" in result
    assert "[품질 추세 경고]" in result


def test_build_prev_context_quality_lines_direct_helper_includes_quality_warning():
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen.context = MagicMock()
    gen.context.current_project = MagicMock()
    gen._build_forgotten_npc_advisory = MagicMock(return_value=("[방치 NPC 주의]", {"노사부"}))
    gen._build_dormant_promise_advisory = MagicMock(return_value="[방치 맹세 경고]")

    db = MagicMock()
    db.get_stage_attempts_for_arc.return_value = [
        {"failure_category": "continuity", "reject_reason": "위치 텔레포트", "stage": 4},
    ]
    db.get_recent_episode_scores.return_value = [
        {"ep_num": 8, "score": 91, "verdict": "PASS"},
        {"ep_num": 9, "score": 84, "verdict": "PASS"},
        {"ep_num": 10, "score": 77, "verdict": "PASS"},
    ]
    gen.context.current_project.db = db

    with patch("modules.domain.agents.four_phase_arc_generator.FailureAnalyzer") as analyzer_cls:
        analyzer = analyzer_cls.return_value
        analyzer.summary.return_value = {
            "stage_pass_rates": {"stage_4": {"pass_rate_pct": 68.0, "total_attempts": 22}},
            "top_failed_agents": [{"agent": "chief_writer", "fail_rate_pct": 55.0}],
            "top_failure_categories": [{"category": "continuity", "count": 5}],
            "quality_distribution": {"avg_score": 82.3, "high_score_count": 2},
            "top_success_patterns": [{"description": "blueprint_coverage 평균 18.5점"}],
        }
        result = "\n".join(gen._build_prev_context_quality_lines({"ep_end": 10}, 2))

    assert "[방치 NPC 주의]" in result
    assert "[방치 맹세 경고]" in result
    assert "[직전 Arc Stage3/4 주요 실패]" in result
    assert "[이전 Arc 실패 분석]" in result
    assert "[품질 추세 경고]" in result


def test_generate_prev_context_includes_forgotten_npc_and_dormant_promise_advisories():
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen._genre = "wuxia"
    gen.context = MagicMock()
    gen.context.master_bible = {
        "MasterBible": {
            "protagonist_config": {"name": "진우"},
            "AssetLibrary": {"KeyNPCs": [{"name": "노사부", "role": "사부"}]},
        }
    }
    gen.context.current_project = MagicMock()
    db = MagicMock()
    db.load_anchor.return_value = {
        "alive_npcs": {
            "노사부": {"role": "사부", "first_seen_ep": 2},
            "진우": {"role": "주인공", "first_seen_ep": 1},
        },
        "promises": [
            {"text": "제자를 지킨다", "promiser": "노사부", "promisee": "진우", "since_ep": 4, "status": "pending"}
        ],
    }
    db.get_npc_recent_episodes.side_effect = lambda name, before_ep, limit=1: [2] if name == "노사부" else [11]
    gen.context.current_project.db = db

    prev_arcs = [
        {
            "arc_no": 2,
            "ep_start": 8,
            "ep_end": 12,
            "state_constraints": {"arc_end_state": {"location": "개봉", "equipment": [], "injuries": "없음", "internal_energy": 100}},
            "joint_docs": {},
            "status_shadow": {},
        }
    ]

    with patch.object(gen, "_load_execution_state", return_value=None):
        result = gen._generate_prev_context(prev_arcs, preflight_result={})

    assert "[방치 NPC 주의]" in result
    assert "노사부" in result
    assert "[방치 맹세 경고]" in result
    assert "제자를 지킨다" in result
