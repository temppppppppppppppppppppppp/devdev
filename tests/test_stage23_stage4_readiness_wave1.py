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


def test_stage4_readiness_categories_are_director_required_not_binding():
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

    assert verdict == "PASS"
    assert feedback == ""
    assert verdict_reason == "ok"
    assert fix_scope == ""
    assert fix_scope_reasoning == ""
    assert binding_issues == []


def test_fact_lock_institution_stays_director_required_not_binding_gate():
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
    assert feedback == "기관명만 수정 필요"
    assert verdict_reason == "기관명 오류"
    assert fix_scope == "inplace"
    assert fix_scope_reasoning == "국소 수정"
    assert binding_issues == []


def test_person_fact_lock_stays_director_advisory_not_binding_gate():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    verdict, feedback, verdict_reason, fix_scope, fix_scope_reasoning, binding_issues = (
        validator._apply_binding_prevalidation_contract(
            verdict="PASS_WITH_FIX",
            issues=[
                {
                    "severity": "CRITICAL",
                    "category": "fact_lock_person",
                    "issue": "인물 사실잠금 위반: 확정 '한태성 회장' → blueprint '한정호 회장' 사용",
                    "fix_hint": "Director가 인물 혼동 여부를 판단",
                }
            ],
            feedback="핵심 인물 언급 보완 필요",
            verdict_reason="국소 보완",
            fix_scope="inplace",
            fix_scope_reasoning="Director 국소 수정",
        )
    )

    assert verdict == "PASS_WITH_FIX"
    assert feedback == "핵심 인물 언급 보완 필요"
    assert verdict_reason == "국소 보완"
    assert fix_scope == "inplace"
    assert fix_scope_reasoning == "Director 국소 수정"
    assert binding_issues == []


def test_python_pre_validate_flags_off_arc_intrusion_as_tactical_semantic_fidelity():
    validator = _make_validator()
    result = validator._python_pre_validate(
        blueprint={
            "ep_num": 5,
            "scene_breakdown": {
                "scene_1": {
                    "title": "난입",
                    "location": "오피스텔",
                    "goal": "대응",
                    "summary": "난입 대응",
                    "characters": ["한시우", "취객"],
                },
                "scene_2": {
                    "title": "주문",
                    "location": "오피스텔",
                    "goal": "매수",
                    "summary": "WTI 주문",
                    "characters": ["한시우", "박성호"],
                },
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
                    "details": [
                        "한시우가 박성호 PB의 만류를 무시하고 15억 원 규모의 WTI 6월물 3배 레버리지 매수를 지시함"
                    ],
                }
            ]
        },
    )

    categories = {issue["category"] for issue in result["issues"]}
    assert "tactical_semantic_fidelity" in categories


def test_python_pre_validate_flags_character_only_intrusion_as_tactical_semantic_fidelity():
    validator = _make_validator()
    result = validator._python_pre_validate(
        blueprint={
            "ep_num": 5,
            "scene_breakdown": {
                "scene_1": {
                    "title": "입장",
                    "location": "오피스텔",
                    "goal": "대면",
                    "summary": "오피스텔 안으로 들어간다.",
                    "characters": ["한시우", "괴한"],
                },
                "scene_2": {
                    "title": "협박",
                    "location": "오피스텔",
                    "goal": "압박",
                    "summary": "상대가 팔목을 비틀며 협박한다.",
                    "key_events": ["팔목을 비틀며 협박한다."],
                    "characters": ["한시우"],
                },
            },
            "integrated_scenario": ("한시우가 오피스텔 안으로 들어간다. 상대가 팔목을 비틀며 협박한다. " * 40).strip(),
            "start_location": "강남구 원룸 오피스텔",
            "time_flow": "2006년 2월 말의 밤",
            "core_tension": "첫 투자 지시와 통제력",
            "expected_ending": "WTI 주문 체결",
            "target_beat": "긴장과 통제",
            "protagonist_state": {"mood": "냉정"},
        },
        constraint_block={
            "must_focus": {
                "content": "한시우는 오피스텔에서 박성호와 통화하며 WTI 주문 여부를 결정한다.",
            }
        },
        prev_blueprint=None,
        arc_data={
            "episode_details": {
                "ep5": "한시우는 오피스텔에서 WTI 주문 여부를 결정한다.",
            }
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
                "scene_1": {
                    "title": "난입",
                    "location": "오피스텔",
                    "goal": "대응",
                    "summary": "난입 대응",
                    "characters": ["한시우", "취객"],
                },
                "scene_2": {
                    "title": "주문",
                    "location": "오피스텔",
                    "goal": "매수",
                    "summary": "WTI 주문",
                    "characters": ["한시우", "박성호"],
                },
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
            "integrated_scenario": (
                "2006년 2월 28일 밤. 한시우가 오피스텔에서 15억 원 규모 WTI 주문을 준비한다. " * 30
            ).strip(),
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
                    "details": [
                        "한시우가 박성호 PB의 만류를 무시하고 15억 원 규모의 WTI 6월물 3배 레버리지 매수를 지시함"
                    ],
                }
            ]
        },
    )

    categories = {issue["category"] for issue in result["issues"]}
    assert "tactical_semantic_fidelity" in categories


def test_python_pre_validate_flags_korean_synonym_intrusion_as_tactical_semantic_fidelity():
    validator = _make_validator()
    result = validator._python_pre_validate(
        blueprint={
            "ep_num": 5,
            "scene_breakdown": {
                "scene_1": {
                    "title": "리스크팀 난입",
                    "location": "한미증권 청담동 지점 15층 VIP룸",
                    "goal": "리스크 관리팀의 압박을 버틴다.",
                    "summary": "리스크 관리팀이 VIP룸에 들이닥쳐 한시우의 팔목을 비틀려 한다.",
                    "key_events": [
                        "리스크 관리팀이 들이닥쳐 한시우의 팔목을 비틀려 한다.",
                        "팀장이 주먹을 들이밀며 입막음을 강요한다.",
                    ],
                    "characters": ["한시우", "박성호", "리스크 관리팀장"],
                },
                "scene_2": {
                    "title": "체결 확인",
                    "location": "한미증권 청담동 지점 15층 VIP룸",
                    "goal": "WTI 주문 체결",
                    "summary": "한시우가 흔들림 없이 체결 여부를 확인한다.",
                    "characters": ["한시우", "박성호"],
                },
            },
            "integrated_scenario": (
                "리스크 관리팀이 VIP룸에 들이닥쳐 한시우의 팔목을 비틀고 주먹을 들이밀며 입막음을 강요한다. " * 30
            ).strip(),
            "start_location": "한미증권 청담동 지점 15층 VIP룸",
            "time_flow": "2006년 2월 16일 오전",
            "core_tension": "WTI 주문 체결과 협상 주도권",
            "expected_ending": "WTI 주문 체결",
            "target_beat": "협상과 체결",
            "protagonist_state": {"mood": "냉정"},
        },
        constraint_block={
            "must_focus": {
                "content": "한시우가 박성호 PB와 수수료 조건을 조정하고 15억 원 규모의 WTI 6월물 주문 체결을 밀어붙임"
            }
        },
        prev_blueprint=None,
        state_tracker=None,
        arc_data={
            "episode_details": [
                {
                    "ep_num": 5,
                    "details": [
                        "한시우가 박성호 PB와 수수료 조건을 조정하고 15억 원 규모의 WTI 6월물 주문 체결을 밀어붙임"
                    ],
                }
            ]
        },
    )

    categories = {issue["category"] for issue in result["issues"]}
    assert "tactical_semantic_fidelity" in categories


def test_python_pre_validate_skips_tactical_intrusion_fp_on_pb_negotiation_with_staff_words_only():
    validator = _make_validator()
    result = validator._python_pre_validate(
        blueprint={
            "ep_num": 5,
            "scene_breakdown": {
                "scene_1": {
                    "title": "조건표 확인",
                    "location": "한미증권 청담동 지점 15층 VIP룸",
                    "goal": "수수료 대응표를 확인한다.",
                    "summary": "박성호가 직원을 불러 대응표와 주문 확인서를 펼친다.",
                    "key_events": [
                        "직원이 대응표를 펼친다.",
                        "한시우와 박성호가 수수료 조건을 다시 맞춘다.",
                    ],
                    "characters": ["한시우", "박성호", "증권사 직원"],
                },
                "scene_2": {
                    "title": "주문 체결",
                    "location": "한미증권 청담동 지점 15층 VIP룸",
                    "goal": "WTI 주문 체결",
                    "summary": "한시우가 체결 순서를 확인하며 주문을 마무리한다.",
                    "characters": ["한시우", "박성호"],
                },
            },
            "integrated_scenario": (
                "박성호가 직원을 불러 대응표와 주문 확인서를 준비시키고, 한시우와 체결 순서를 차분히 조율한다. " * 30
            ).strip(),
            "start_location": "한미증권 청담동 지점 15층 VIP룸",
            "time_flow": "2006년 2월 16일 오전",
            "core_tension": "WTI 주문 체결과 협상 주도권",
            "expected_ending": "WTI 주문 체결",
            "target_beat": "협상과 체결",
            "protagonist_state": {"mood": "냉정"},
        },
        constraint_block={
            "must_focus": {
                "content": "한시우가 박성호 PB와 수수료 조건을 조정하고 15억 원 규모의 WTI 6월물 주문 체결을 밀어붙임"
            }
        },
        prev_blueprint=None,
        state_tracker=None,
        arc_data={
            "episode_details": [
                {
                    "ep_num": 5,
                    "details": [
                        "한시우가 박성호 PB와 수수료 조건을 조정하고 15억 원 규모의 WTI 6월물 주문 체결을 밀어붙임"
                    ],
                }
            ]
        },
    )

    categories = {issue["category"] for issue in result["issues"]}
    assert "tactical_semantic_fidelity" not in categories
