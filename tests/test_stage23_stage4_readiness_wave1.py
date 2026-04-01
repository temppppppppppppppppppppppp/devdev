from unittest.mock import MagicMock

from modules.domain.agents.blueprint_ensemble import BlueprintEnsembleGenerator
from modules.domain.agents.unified_blueprint_validator import UnifiedBlueprintValidator


def _make_ensemble() -> BlueprintEnsembleGenerator:
    class _Stub:
        pass

    ctx = _Stub()
    ctx.current_project = None
    ctx.ui = _Stub()
    ctx.ui.log = lambda *a, **kw: None
    ens = object.__new__(BlueprintEnsembleGenerator)
    ens.context = ctx
    return ens


def _make_validator() -> UnifiedBlueprintValidator:
    validator = object.__new__(UnifiedBlueprintValidator)
    validator.min_chars = 800
    return validator


def test_arc_constraint_summary_is_promoted_to_hard_constraint_band():
    ens = _make_ensemble()
    result = ens._format_constraints(
        {
            "must_focus": {"key_events": ["핵심 사건"]},
            "arc_constraint_summary": "이번 화에서 깡패 난입 같은 외부 액션을 새로 만들지 말 것",
            "state_changes_summary": "참고용 상태 변화",
        },
        genre="investment",
    )

    hard_idx = result.find("HARD CONSTRAINT")
    summary_idx = result.find("이번 화에서 깡패 난입 같은 외부 액션을 새로 만들지 말 것")
    state_summary_idx = result.find("참고용 상태 변화")

    assert hard_idx >= 0
    assert summary_idx > hard_idx
    assert state_summary_idx >= 0
    assert summary_idx < state_summary_idx


def test_python_pre_validate_flags_stage4_readiness_contract_gaps():
    validator = _make_validator()
    result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {"goal": "갈등", "summary": "요약", "characters": ["한시우"]},
                "scene_2": {"goal": "추적", "summary": "요약", "characters": ["박성호"]},
                "scene_3": {"goal": "결정", "summary": "요약", "characters": ["한시우", "박성호"]},
            },
            "integrated_scenario": "A" * 900,
            "start_location": "",
            "time_flow": "",
            "core_tension": "",
            "expected_ending": "",
            "target_beat": "",
            "protagonist_state": {},
        },
        constraint_block={},
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    categories = {issue["category"] for issue in result["issues"]}
    assert "opening_anchor" in categories
    assert "mission_clarity" in categories
    assert "timeline_specificity" in categories
    assert "protagonist_state" in categories


def test_stage4_readiness_categories_are_binding():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    verdict, feedback, verdict_reason, fix_scope, fix_scope_reasoning, binding_issues = (
        validator._apply_binding_prevalidation_contract(
            verdict="PASS",
            issues=[
                {
                    "severity": "MAJOR",
                    "category": "opening_anchor",
                    "issue": "opening anchor 계약 누락",
                    "fix_hint": "fill opening anchor",
                }
            ],
            feedback="",
            verdict_reason="ok",
            fix_scope="",
            fix_scope_reasoning="",
        )
    )

    assert verdict == "PASS_WITH_FIX"
    assert fix_scope == "inplace"
    assert binding_issues[0]["category"] == "opening_anchor"
    assert "[Binding prevalidation]" in feedback


def test_binding_contract_merges_fact_lock_issue_into_existing_pass_with_fix():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    verdict, feedback, verdict_reason, fix_scope, fix_scope_reasoning, binding_issues = (
        validator._apply_binding_prevalidation_contract(
            verdict="PASS_WITH_FIX",
            issues=[
                {
                    "severity": "CRITICAL",
                    "category": "fact_lock_institution",
                    "issue": "기관 사실잠금 위반",
                    "fix_hint": "기관명을 확정 사실에 맞추기",
                }
            ],
            feedback="기관명만 수정 필요",
            verdict_reason="기관명 오류",
            fix_scope="inplace",
            fix_scope_reasoning="국소 수정",
        )
    )

    assert verdict == "PASS_WITH_FIX"
    assert "[Binding prevalidation]" in feedback
    assert "기관 사실잠금 위반" in feedback
    assert verdict_reason.endswith("binding prevalidation repair required")
    assert fix_scope == "inplace"
    assert fix_scope_reasoning == "국소 수정"
    assert binding_issues[0]["category"] == "fact_lock_institution"


def test_python_pre_validate_flags_off_arc_intrusion_as_tactical_semantic_fidelity():
    validator = _make_validator()
    result = validator._python_pre_validate(
        blueprint={
            "ep_num": 5,
            "scene_breakdown": {
                "scene_1": {"title": "난입", "location": "오피스텔", "goal": "대응", "summary": "난입 대응", "characters": ["한시우", "취객"]},
                "scene_2": {"title": "주문", "location": "오피스텔", "goal": "매수", "summary": "WTI 주문", "characters": ["한시우", "박성호"]},
            },
            "integrated_scenario": ("취객이 난입했고 한시우가 멱살을 잡은 뒤 무단침입을 경고했다. " * 40).strip(),
            "start_location": "강남구 원룸 오피스텔",
            "time_flow": "2006년 2월 말의 밤",
            "core_tension": "첫 투자 지시와 통제력",
            "expected_ending": "WTI 주문 체결",
            "target_beat": "긴장과 통제",
            "protagonist_state": {"mood": "냉정"},
        },
        constraint_block={
            "must_focus": {
                "content": "한시우가 박성호 PB의 만류를 무시하고 15억 원 규모의 WTI 6월물 3배 레버리지 매수를 지시함"
            }
        },
        prev_blueprint=None,
        state_tracker=None,
        arc_data={
            "episode_details": [
                {
                    "ep_num": 5,
                    "details": ["한시우가 박성호 PB의 만류를 무시하고 15억 원 규모의 WTI 6월물 3배 레버리지 매수를 지시함"],
                }
            ]
        },
    )

    categories = {issue["category"] for issue in result["issues"]}
    assert "tactical_semantic_fidelity" in categories


def test_python_pre_validate_skips_tactical_intrusion_flag_when_authorized_by_arc_focus():
    validator = _make_validator()
    result = validator._python_pre_validate(
        blueprint={
            "ep_num": 5,
            "scene_breakdown": {
                "scene_1": {"title": "난입", "location": "오피스텔", "goal": "대응", "summary": "난입 대응", "characters": ["한시우", "취객"]},
                "scene_2": {"title": "주문", "location": "오피스텔", "goal": "매수", "summary": "WTI 주문", "characters": ["한시우", "박성호"]},
            },
            "integrated_scenario": ("취객이 난입했고 한시우가 멱살을 잡은 뒤 무단침입을 경고했다. " * 40).strip(),
            "start_location": "강남구 원룸 오피스텔",
            "time_flow": "2006년 2월 말의 밤",
            "core_tension": "첫 투자 지시와 통제력",
            "expected_ending": "WTI 주문 체결",
            "target_beat": "긴장과 통제",
            "protagonist_state": {"mood": "냉정"},
        },
        constraint_block={
            "must_focus": {
                "content": "취객 난입을 처리한 뒤 한시우가 박성호 PB에게 15억 원 규모의 WTI 6월물 3배 레버리지 매수를 지시함"
            }
        },
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    categories = {issue["category"] for issue in result["issues"]}
    assert "tactical_semantic_fidelity" not in categories


def test_python_pre_validate_flags_disguised_intrusion_from_scene_breakdown_text():
    validator = _make_validator()
    result = validator._python_pre_validate(
        blueprint={
            "ep_num": 5,
            "scene_breakdown": {
                "scene_1": {
                    "title": "방문자",
                    "location": "강남구 원룸 오피스텔",
                    "goal": "침입자를 제압하고 외부의 간섭을 차단한다.",
                    "summary": "오피스텔에 들이닥친 심부름센터 직원을 시우가 쫓아낸다.",
                    "description": "낡은 오피스텔의 철문이 열리고 거대한 그림자 같은 심부름센터 직원이 들어선다.",
                    "key_events": [
                        "굳게 닫혀 있던 철문을 열고 심부름센터 직원이 들이닥침",
                        "한시우가 침입자를 압박해 쫓아냄",
                    ],
                    "characters": ["한시우", "심부름센터 직원"],
                },
                "scene_2": {
                    "title": "주문",
                    "location": "오피스텔",
                    "goal": "WTI 주문",
                    "summary": "박성호와 통화하며 15억 원 주문을 밀어붙인다.",
                    "characters": ["한시우", "박성호"],
                },
            },
            "integrated_scenario": ("2006년 2월 28일 밤. 한시우가 오피스텔에서 15억 원 규모 WTI 주문을 준비한다. " * 30).strip(),
            "start_location": "강남구 원룸 오피스텔",
            "time_flow": "2006년 2월 말의 밤",
            "core_tension": "첫 투자 지시와 통제력",
            "expected_ending": "WTI 주문 체결",
            "target_beat": "긴장과 통제",
            "protagonist_state": {"mood": "냉정"},
        },
        constraint_block={
            "must_focus": {
                "content": "한시우가 박성호 PB의 만류를 무시하고 15억 원 규모의 WTI 6월물 3배 레버리지 매수를 지시함"
            }
        },
        prev_blueprint=None,
        state_tracker=None,
        arc_data={
            "episode_details": [
                {
                    "ep_num": 5,
                    "details": ["한시우가 박성호 PB의 만류를 무시하고 15억 원 규모의 WTI 6월물 3배 레버리지 매수를 지시함"],
                }
            ]
        },
    )

    categories = {issue["category"] for issue in result["issues"]}
    assert "tactical_semantic_fidelity" in categories
