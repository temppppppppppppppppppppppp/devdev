"""FourPhaseArcGenerator regression tests for pre-collected state normalization."""

from unittest.mock import MagicMock, patch

from modules.core.response_schemas import ARC_STATE_SCHEMA
from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator


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
    gen.ensemble = MagicMock()
    gen.ensemble.generate_ensemble.return_value = (
        None,
        [{"_ensemble_meta": {"best_strategy": "balanced"}, "tactical_doc": "mock tactical"}],
    )
    gen.validator = MagicMock()
    gen.validator.validate.return_value = ("PASS", {"issues": [], "confidence": 90})
    gen._determine_ep_count = MagicMock(return_value=(5, "reason"))
    gen._generate_prev_context = MagicMock(return_value="prev")
    gen._check_arc_end_state = MagicMock(side_effect=lambda arc: arc)
    return gen


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

    arc, pipeline_result = gen.generate(
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

    arc, pipeline_result = gen.generate(
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

    arc, _ = gen.generate(
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

    gen.generate(
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
