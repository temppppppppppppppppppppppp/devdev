from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.constants import GenreTypes
from modules.core.prompt_loader import PromptLoader
from modules.domain.agents.base_agent import AgentErrorType
from modules.domain.agents.blueprint_ensemble import BlueprintEnsembleGenerator


def _make_agent():
    ctx = SimpleNamespace()
    ctx.author_directives = ""
    ctx.db = MagicMock()
    ctx.db.load_anchor.return_value = {}
    ctx.current_project = SimpleNamespace(name="Lane Project")
    ctx.project_name = "Lane Project"
    return BlueprintEnsembleGenerator(ctx, MagicMock())


def test_generate_ensemble_owner_shell_coordinates_helper_chain():
    agent = _make_agent()
    prepared = {
        "arc_focus": "focus",
        "genre": GenreTypes.WUXIA,
        "constraints_str": "constraints",
        "tactical_excerpt": "tactical",
        "prev_info": "prev",
        "hud_context": "hud",
        "cache_name": "cache/bp",
    }
    active_strategies = [{"name": "action_focused"}]
    raw_candidates = [{"scene_breakdown": [1, 2, 3, 4], "integrated_scenario": "x" * 600}]
    qualified_candidates = [
        {
            "_strategy": "action_focused",
            "_scene_count": 4,
            "_length": 600,
            "scene_breakdown": [1, 2, 3, 4],
            "integrated_scenario": "x" * 600,
        }
    ]
    finalized = ({"best": True}, [{"best": True}])

    agent._prepare_blueprint_ensemble_context = MagicMock(return_value=prepared)
    agent._select_blueprint_ensemble_strategies = MagicMock(return_value=active_strategies)
    agent._run_blueprint_ensemble_workers = MagicMock(return_value=(raw_candidates, [AgentErrorType.TIMEOUT]))
    agent._qualify_blueprint_candidates = MagicMock(return_value=(qualified_candidates, []))
    agent._finalize_blueprint_candidates = MagicMock(return_value=finalized)

    result = agent.generate_ensemble(
        ep_num=9,
        arc_data={},
        constraint_block={},
        prev_blueprint={"end_location": "VIP 룸"},
        single_strategy="action_focused",
    )

    assert result == finalized
    assert agent.last_error_types == [AgentErrorType.TIMEOUT]
    assert agent.last_error_type == AgentErrorType.TIMEOUT
    agent._prepare_blueprint_ensemble_context.assert_called_once()
    agent._select_blueprint_ensemble_strategies.assert_called_once_with("action_focused")
    agent._run_blueprint_ensemble_workers.assert_called_once()
    assert agent._run_blueprint_ensemble_workers.call_args.kwargs["cache_name"] == "cache/bp"
    assert agent._run_blueprint_ensemble_workers.call_args.kwargs["prev_blueprint"] == {"end_location": "VIP 룸"}
    agent._qualify_blueprint_candidates.assert_called_once_with(raw_candidates)
    agent._finalize_blueprint_candidates.assert_called_once_with(qualified_candidates, [])


def test_qualify_blueprint_candidates_tracks_pass_and_fail_metadata():
    agent = _make_agent()

    qualified, disqualified = agent._qualify_blueprint_candidates(
        [
            {
                "_strategy": "action_focused",
                "scene_breakdown": [
                    {"summary": "주인공이 회의실 문을 열고 들어간다.", "key_events": ["회의실 문을 열고 들어간다."]},
                    {"summary": "PB가 투자 리스크를 경고한다.", "key_events": ["PB가 투자 리스크를 경고한다."]},
                    {"summary": "주인공이 매수 결정을 밀어붙인다.", "key_events": ["매수 결정을 밀어붙인다."]},
                    {"summary": "시세가 요동치며 끝난다.", "key_events": ["시세가 요동친다."]},
                ],
                "integrated_scenario": "x" * 900,
                "opening_transition": {"type": "direct_continuation"},
                "protagonist_state": {"mood": "긴장"},
            },
            {
                "_strategy": "dialogue_focused",
                "scene_breakdown": [
                    {"summary": "주인공이 PB를 만난다.", "key_events": ["PB를 만난다."]},
                    {"summary": "PB가 경고를 건넨다.", "key_events": ["경고를 건넨다."]},
                    {"summary": "주인공이 고민한다.", "key_events": ["매수 여부를 고민한다."]},
                ],
                "integrated_scenario": "x" * 320,
                "opening_transition": {"type": "direct_continuation"},
                "protagonist_state": {"mood": "긴장"},
            },
        ]
    )

    assert len(qualified) == 1
    assert qualified[0]["_qualified"] is True
    assert qualified[0]["_scene_count"] == 4
    assert qualified[0]["_length"] == 900
    assert disqualified == [("dialogue_focused", 3, 320)]


def test_qualify_blueprint_candidates_accepts_dense_three_scene_blueprint():
    agent = _make_agent()

    qualified, disqualified = agent._qualify_blueprint_candidates(
        [
            {
                "_strategy": "dense_three_scene",
                "scene_breakdown": {
                    "scene_1": {
                        "goal": "The protagonist forces the first buy order through the VIP room desk.",
                        "key_events": ["The protagonist forces the buy order through despite the PB objection."],
                    },
                    "scene_2": {
                        "summary": "Leverage warnings and collateral pressure hit the desk at the same time.",
                        "key_events": [
                            "The desk flashes a leverage warning.",
                            "Collateral pressure arrives from the broker.",
                        ],
                    },
                    "scene_3": {
                        "goal": "The trade settles at the closing bell and leaves the next crisis hanging.",
                        "key_events": ["The trade settles at the closing bell."],
                    },
                },
                "integrated_scenario": ("The trade desk keeps escalating as pressure piles on. " * 30),
                "opening_transition": {"type": "explicit_transition"},
                "protagonist_state": {"mood": "focused"},
            }
        ]
    )

    assert len(qualified) == 1
    assert qualified[0]["_qualified"] is True
    assert qualified[0]["_scene_count"] == 3
    assert qualified[0]["_length"] == len("The trade desk keeps escalating as pressure piles on. " * 30)
    assert disqualified == []


def test_qualify_blueprint_candidates_accepts_dense_two_scene_blueprint():
    agent = _make_agent()

    qualified, disqualified = agent._qualify_blueprint_candidates(
        [
            {
                "_strategy": "dense_two_scene",
                "scene_breakdown": {
                    "scene_1": {
                        "goal": "The protagonist hits the first buy button inside the PB center.",
                        "key_events": ["The protagonist hits the first buy button."],
                    },
                    "scene_2": {
                        "summary": "Leverage warnings and collateral pressure crash in together.",
                        "key_events": [
                            "A leverage warning crashes onto the desk.",
                            "Collateral pressure starts immediately.",
                        ],
                    },
                },
                "integrated_scenario": ("The protagonist keeps pushing through the market pressure. " * 30),
                "opening_transition": {"type": "explicit_transition"},
                "protagonist_state": {"mood": "focused"},
            }
        ]
    )

    assert len(qualified) == 1
    assert qualified[0]["_qualified"] is True
    assert qualified[0]["_scene_count"] == 2
    assert qualified[0]["_length"] == len("The protagonist keeps pushing through the market pressure. " * 30)
    assert disqualified == []


def test_finalize_blueprint_candidates_attaches_meta_and_cleans_temp_fields():
    agent = _make_agent()
    qualified_candidates = [
        {
            "_strategy": "emotion_focused",
            "_qualified": True,
            "_scene_count": 4,
            "_length": 700,
            "scene_breakdown": [{"scene": 1}],
            "integrated_scenario": "x" * 700,
        }
    ]
    disqualified = [("action_focused", 2, 120)]

    best, all_candidates = agent._finalize_blueprint_candidates(qualified_candidates, disqualified)

    assert best is all_candidates[0]
    meta = all_candidates[0]["_ensemble_meta"]
    assert meta["candidate_index"] == 0
    assert meta["strategy"] == "emotion_focused"
    assert meta["scene_count"] == 4
    assert meta["length"] == 700
    assert meta["disqualified"] == disqualified
    assert "_strategy" not in all_candidates[0]
    assert "_qualified" not in all_candidates[0]
    assert "_scene_count" not in all_candidates[0]
    assert "_length" not in all_candidates[0]


def test_build_blueprint_prompt_bundle_uses_cache_stub_and_full_fallback():
    agent = _make_agent()

    def _load_side_effect(_file, _key, **kwargs):
        return (
            f"arc={kwargs['arc_focus']}|constraints={kwargs['constraints']}|"
            f"prev={kwargs['prev_info']}|hud={kwargs['hud_context']}"
        )

    agent._prompt_loader = MagicMock()
    agent._prompt_loader.load.side_effect = _load_side_effect

    prompt, fallback = agent._build_blueprint_prompt_bundle(
        ep_num=11,
        arc_focus="ARC_FOCUS_PAYLOAD",
        constraints_str="CONSTRAINTS_PAYLOAD",
        prev_info="PREV_INFO_PAYLOAD",
        strategy={"display": "action", "directive": "directive"},
        protagonist_name="hero",
        protagonist_instructions="do the thing",
        extra_directive="",
        hud_context="HUD_PAYLOAD",
        pov_constraint="POV_CONSTRAINT",
        reader_feedback="",
        cache_name="cache/bp",
    )

    assert "[context cached: refer to cached_content]" in prompt
    assert "ARC_FOCUS_PAYLOAD" not in prompt
    assert "CONSTRAINTS_PAYLOAD" not in prompt
    assert "PREV_INFO_PAYLOAD" not in prompt
    assert "HUD_PAYLOAD" not in prompt
    assert "ARC_FOCUS_PAYLOAD" in fallback
    assert "CONSTRAINTS_PAYLOAD" in fallback
    assert "PREV_INFO_PAYLOAD" in fallback
    assert "HUD_PAYLOAD" in fallback


def test_prepare_blueprint_ensemble_context_caches_constraints_before_arc_focus():
    agent = _make_agent()
    captured = {}

    def _capture_cache(**kwargs):
        captured["content"] = kwargs["content"]
        return {"cache_name": "cache/bp"}

    agent._resolve_blueprint_arc_focus = MagicMock(return_value="ARC_FOCUS_PAYLOAD")
    agent._resolve_blueprint_ensemble_genre = MagicMock(return_value=GenreTypes.WUXIA)
    agent._format_constraints = MagicMock(return_value="CONSTRAINTS_PAYLOAD")
    agent._format_prev_info_expanded = MagicMock(return_value="PREV_INFO_PAYLOAD")
    agent._build_hud_context = MagicMock(return_value="HUD_PAYLOAD")
    agent._get_or_create_context_cache = MagicMock(side_effect=_capture_cache)

    result = agent._prepare_blueprint_ensemble_context(
        ep_num=11,
        arc_data={},
        constraint_block={},
        prev_blueprint=None,
        prev_blueprints=None,
        prev_manuscripts_text="",
        state_tracker=None,
    )

    shared_context = captured["content"]
    assert shared_context.index("CONSTRAINTS_PAYLOAD") < shared_context.index("ARC_FOCUS_PAYLOAD")
    assert result["cache_name"] == "cache/bp"


def test_build_blueprint_prompt_bundle_places_constraints_before_arc_mission():
    agent = _make_agent()

    prompt, fallback = agent._build_blueprint_prompt_bundle(
        ep_num=11,
        arc_focus="ARC_FOCUS_PAYLOAD",
        constraints_str="CONSTRAINTS_PAYLOAD",
        prev_info="PREV_INFO_PAYLOAD",
        strategy={"display": "action", "directive": "directive"},
        protagonist_name="hero",
        protagonist_instructions="do the thing",
        extra_directive="",
        hud_context="HUD_PAYLOAD",
        pov_constraint="POV_CONSTRAINT",
        reader_feedback="",
        cache_name="",
    )

    assert prompt.index("### [Constraint Stack / 제약 조건]") < prompt.index("### [Arc Mission / 이번 화 핵심]")
    assert prompt.index("### [Previous Truth And Archive]") < prompt.index("### [HUD Convenience State]")
    assert fallback == prompt


def test_request_blueprint_generation_rejects_missing_required_fields():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(return_value='{"scene_breakdown": []}')
    agent._extract_json_robust = MagicMock(return_value={"scene_breakdown": []})

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert result == (None, AgentErrorType.SCHEMA_INCOMPATIBLE)


def test_sanitize_blueprint_candidate_normalizes_declared_opening_transition_alias():
    agent = _make_agent()

    result = agent._sanitize_blueprint_candidate(
        {
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 문을 열고 PB의 표정을 읽는다.", "key_events": ["PB의 눈빛이 굳는다."]},
                "scene_2": {"summary": "주인공이 매수 타이밍을 확정한다.", "key_events": ["매수 버튼을 누른다."]},
            },
            "integrated_scenario": "주인공이 문을 열고 들어가 PB의 경고를 읽은 뒤 바로 매수 결정을 밀어붙인다. " * 40,
            "opening_transition": {"type": "transition", "summary": "scene cut into the trading floor"},
            "protagonist_state": {"mood": "집중"},
        },
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert isinstance(result, dict)
    assert result["opening_transition"]["type"] == "explicit_transition"
    assert result["opening_transition"]["summary"] == "scene cut into the trading floor"


def test_request_blueprint_generation_uses_prev_blueprint_to_infer_direct_opening_transition():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(return_value="{}")
    agent._extract_json_robust = MagicMock(
        return_value={
            "start_location": "VIP 룸",
            "time_flow": "직후",
            "scene_breakdown": {
                "scene_1": {
                    "location": "VIP 룸",
                    "summary": "주인공이 VIP 룸 문을 열고 PB와 마주한다.",
                    "key_events": ["VIP 룸에 도착한다."],
                },
                "scene_2": {
                    "summary": "PB가 경고를 던지고 주인공은 매수 버튼을 누를 타이밍을 잰다.",
                    "key_events": ["PB의 경고를 무시한다."],
                },
            },
            "integrated_scenario": "주인공이 VIP 룸 직후 장면을 이어받아 PB의 경고를 넘기고 매수 타이밍을 재본다. "
            * 40,
            "protagonist_state": {"mood": "긴장"},
        }
    )

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
        prev_blueprint={"end_location": "VIP 룸", "time_flow": "같은 날 밤"},
    )

    assert isinstance(result, dict)
    assert result["opening_transition"]["type"] == "direct_continuation"


def test_request_blueprint_generation_infers_jump_opening_without_prev_blueprint():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(return_value="{}")
    agent._extract_json_robust = MagicMock(
        return_value={
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 택시 문을 열고 내린다.", "key_events": ["택시에서 내린다."]},
                "scene_2": {"summary": "VIP룸 앞에서 PB와 신경전을 벌인다.", "key_events": ["PB와 대치한다."]},
            },
            "integrated_scenario": "주인공은 택시에서 내려 VIP룸으로 향한다. " * 40,
            "protagonist_state": {"mood": "긴장"},
        }
    )

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert isinstance(result, dict)
    assert result["opening_transition"]["type"] == "jump_opening"


def test_request_blueprint_generation_rejects_empty_protagonist_state_contract():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(return_value="{}")
    agent._extract_json_robust = MagicMock(
        return_value={
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 택시 문을 열고 내린다.", "key_events": ["택시에서 내린다."]},
                "scene_2": {"summary": "VIP룸 앞에서 PB와 신경전을 벌인다.", "key_events": ["PB와 대치한다."]},
            },
            "integrated_scenario": "주인공은 택시에서 내려 VIP룸으로 향한다. " * 40,
            "opening_transition": {"type": "explicit_transition"},
            "protagonist_state": {},
        }
    )

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert result == (None, AgentErrorType.SCHEMA_INCOMPATIBLE)


def test_blueprint_contract_admission_reason_rejects_generic_scene_shells():
    agent = _make_agent()

    reason = agent._blueprint_contract_admission_reason(
        {
            "scene_breakdown": {
                "scene_1": {"summary": "setup", "key_events": ["progress"]},
                "scene_2": {"summary": "climax", "key_events": ["ending"]},
            },
            "integrated_scenario": "Trader moves through the episode." * 40,
            "opening_transition": {"type": "direct_continuation"},
            "protagonist_state": {"mood": "focused"},
        }
    )

    assert reason == "scene_completeness:2"


def test_blueprint_contract_admission_reason_rejects_placeholder_protagonist_state():
    agent = _make_agent()

    reason = agent._blueprint_contract_admission_reason(
        {
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 택시 문을 열고 내린다.", "key_events": ["택시에서 내린다."]},
                "scene_2": {"summary": "VIP룸 앞에서 PB와 대치한다.", "key_events": ["PB와 대치한다."]},
            },
            "integrated_scenario": "주인공은 택시에서 내려 VIP룸으로 향한다. " * 40,
            "opening_transition": {"type": "explicit_transition"},
            "protagonist_state": {"mood": "상태 유지", "objective": "변화"},
        }
    )

    assert reason == "missing_protagonist_state"


def test_blueprint_contract_admission_reason_rejects_scene_completeness_gap():
    agent = _make_agent()

    reason = agent._blueprint_contract_admission_reason(
        {
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 택시 문을 열고 내린다.", "key_events": ["택시에서 내린다."]},
                "scene_2": {"summary": "VIP룸 앞에서 PB와 대치한다.", "key_events": []},
            },
            "integrated_scenario": "주인공은 택시에서 내려 VIP룸으로 향한다. " * 40,
            "opening_transition": {"type": "explicit_transition"},
            "protagonist_state": {"mood": "긴장"},
        }
    )

    assert reason == "scene_completeness:1"


def test_sanitize_blueprint_candidate_rejects_unauthorized_tactical_intrusion():
    agent = _make_agent()

    result = agent._sanitize_blueprint_candidate(
        {
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 VIP룸 문을 열자 괴한이 난입한다.", "key_events": ["괴한이 난입한다."]},
                "scene_2": {"summary": "괴한이 멱살을 잡고 협박한다.", "key_events": ["멱살을 잡고 협박한다."]},
            },
            "integrated_scenario": "주인공이 VIP룸 문을 여는 순간 괴한이 난입하고 멱살을 잡아 협박한다. " * 40,
            "opening_transition": {"type": "jump_opening"},
            "protagonist_state": {"mood": "경계"},
        },
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
        tactical_excerpt="주인공은 PB와 대치하며 매수 여부를 결정한다.",
    )

    assert result == (None, AgentErrorType.SCHEMA_INCOMPATIBLE)


def test_request_blueprint_generation_rejects_contaminated_integrated_scenario():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(return_value="{}")
    agent._extract_json_robust = MagicMock(
        return_value={
            "scene_breakdown": [],
            "integrated_scenario": "직전 화의 HUD 상태창을 확인했다.",
        }
    )

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert result == (None, AgentErrorType.SCHEMA_INCOMPATIBLE)


def test_request_blueprint_generation_sanitizes_contaminated_key_events():
    agent = _make_agent()
    candidate = {
        "scene_breakdown": {
            "scene_1": {
                "summary": "주인공이 문을 열고 적과 마주친다.",
                "key_events": [
                    "문을 열고 적과 마주친다.",
                    "HUD 상태창 점검",
                ],
            },
            "scene_2": {
                "summary": "주인공이 적의 칼끝을 피하고 뒤로 물러선다.",
                "key_events": ["칼끝을 피한다."],
            },
        },
        "integrated_scenario": "주인공은 문을 열고 적과 마주친다. " * 40,
        "opening_transition": {"type": "direct_continuation"},
        "protagonist_state": {"mood": "경계"},
    }
    agent._ask_with_cached_context = MagicMock(return_value="{}")
    agent._extract_json_robust = MagicMock(return_value=candidate)

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert isinstance(result, dict)
    assert result["scene_breakdown"]["scene_1"]["key_events"] == ["문을 열고 적과 마주친다."]


class TestBlueprintTemporalCarryover:
    """[pre-rerun] Blueprint 시간 진실 소스가 원고 기준으로 전달되는지 검증."""

    def test_format_prev_info_expanded_includes_manuscript_ending_truth(self):
        """prev_manuscripts_text가 있으면 '원고 기준 종료 상황' 섹션이 포함."""
        agent = _make_agent()
        prev_bp = {
            "ending_hook": "적의 습격",
            "end_location": "객잔",
            "time_flow": "2006-01-17 저녁",
            "ending_state": {"timeline": {"expression": "2006-01-17 Evening"}},
        }
        manuscript_text = "주인공은 저녁 8시에 아버지를 만났다. [2006년 1월 18일, 저녁]"

        result = agent._format_prev_info_expanded(prev_bp, None, manuscript_text)

        assert "원고 기준" in result
        assert "2006년 1월 18일" in result

    def test_format_prev_info_expanded_without_manuscript_omits_truth_section(self):
        """prev_manuscripts_text가 없으면 원고 기준 섹션 없음."""
        agent = _make_agent()
        prev_bp = {"time_flow": "2006-01-17 저녁"}

        result = agent._format_prev_info_expanded(prev_bp, None, "")

        assert "원고 기준" not in result

    def test_format_prev_info_expanded_replaces_raw_scenario_with_structured_carryover(self):
        agent = _make_agent()
        prev_bp = {"time_flow": "2006-01-17 저녁"}
        previous_blueprints = [
            {
                "ep_num": 3,
                "title": "도약",
                "integrated_scenario": "상태창이 떠오르고 직전 화를 요약하는 장문 시나리오",
                "start_location": "객잔",
                "end_location": "산문 앞",
                "time_flow": "저녁 → 심야",
                "core_tension": "추적자 접근",
                "ending_hook": "문이 열렸다",
                "scene_breakdown": {
                    "scene_1": {
                        "title": "추적",
                        "location": "골목",
                        "summary": "주인공이 골목을 가로지른다.",
                        "characters": ["주인공", "추적자"],
                        "key_events": ["추적자를 따돌린다."],
                    }
                },
            }
        ]

        result = agent._format_prev_info_expanded(prev_bp, previous_blueprints, "")

        assert "상태창이 떠오르고 직전 화를 요약하는 장문 시나리오" not in result
        assert "[시작위치] 객잔" in result
        assert "[종료위치] 산문 앞" in result
        assert "[scene_1] 추적" in result
        assert "추적자를 따돌린다." in result

    def test_constraint_compiler_prefers_manuscript_ending(self):
        """원고 말미가 있으면 time_context에 원고 기준 정보가 포함."""
        from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler

        compiler = BlueprintConstraintCompiler()
        prev_bp = {"time_flow": "2006-01-17 저녁", "ending_hook": "습격"}
        continuity = compiler._extract_continuity(prev_bp, prev_manuscript_ending="저녁 8시, 1월 18일의 밤하늘")

        assert "원고 기준" in continuity["time_context"]
        assert "1월 18일" in continuity["time_context"]

    def test_constraint_compiler_falls_back_to_blueprint_without_manuscript(self):
        """원고 말미 없으면 blueprint time_flow 사용."""
        from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler

        compiler = BlueprintConstraintCompiler()
        prev_bp = {"time_flow": "2006-01-17 저녁", "ending_hook": "습격"}
        continuity = compiler._extract_continuity(prev_bp)

        assert continuity["time_context"] == "2006-01-17 저녁"

    def test_format_prev_info_expanded_marks_truth_tiers(self):
        agent = _make_agent()
        prev_bp = {"ending_hook": "late call", "end_location": "office"}
        previous_blueprints = [{"ep_num": 1, "title": "pilot", "scene_breakdown": {}}]

        result = agent._format_prev_info_expanded(prev_bp, previous_blueprints, "manuscript ending")

        assert "[Context Tier 1 - Direct Previous Episode Truth]" in result
        assert "[Context Tier 2 - Structured Previous Blueprint Carryover]" in result
        assert "[Context Tier 3 - Manuscript Ending Truth]" in result
        assert "[Context Tier 4 - Archive Appendix / lower priority than Tier 1-3]" in result


def test_blueprint_generation_prompt_contains_stage3_anti_contamination_contract():
    prompt = PromptLoader().load("ensemble", "BLUEPRINT_GENERATION_PROMPT")

    assert prompt is not None
    assert "Stage3 장면 권위 계약" in prompt
    assert "안티 HUD / 안티 시스템 UI" in prompt
    assert "안티 크로스 장르 오염" in prompt
    assert "scene_breakdown.key_events" in prompt
    assert '"opening_transition"' in prompt
    assert '"episode_number"' in prompt
    assert "장면 완성도 계약" in prompt
    assert "전술 권위 계약" in prompt


# ===========================================================================
# Tranche 1 (2026-04-14): Opening-Transition Vocabulary Coherence
# ===========================================================================


def test_tranche1_blueprint_generation_prompt_carries_opening_transition_decision_table():
    """Tranche 1 sub-edit 1.2: ensemble.yaml에 opening_transition decision table이 들어가
    LLM이 enum 이름만 보지 않고 실제 결정 규칙을 학습할 수 있어야 한다."""
    prompt = PromptLoader().load("ensemble", "BLUEPRINT_GENERATION_PROMPT")
    assert prompt is not None
    assert "opening_transition.type 결정 규칙" in prompt
    assert "direct_continuation" in prompt
    assert "explicit_transition" in prompt
    assert "jump_opening" in prompt
    assert "stage_cross_stage_contract.apply_opening_transition_contract" in prompt


def test_tranche1_extract_episode_tactical_default_behavior_unchanged():
    """Tranche 1 sub-edit 1.3: prefer_full_doc default False이면 13개 다른 호출자에
    영향이 없어야 한다 (episode_details 우선, 없으면 regex slice, 없으면 fallback)."""
    from modules.core.tactical_utils import extract_episode_tactical

    # episode_details 있으면 그것을 반환 (default mode)
    result = extract_episode_tactical(
        "[제1화 prologue]\nfirst content\n[제2화 next]",
        1,
        episode_details=[{"ep_num": 1, "details": ["bullet a", "bullet b"]}],
    )
    assert result == "- bullet a\n- bullet b"

    # episode_details 없으면 regex slice 반환
    result2 = extract_episode_tactical(
        "[제1화 prologue]\nfirst content\n[제2화 next]",
        1,
    )
    assert result2 == "first content"

    # 둘 다 없으면 fallback_full=True이면 전체 문자열
    result3 = extract_episode_tactical("raw doc", 99)
    assert result3 == "raw doc"

    # fallback_full=False이면 빈 문자열
    result4 = extract_episode_tactical("raw doc", 99, fallback_full=False)
    assert result4 == ""


def test_tranche1_extract_episode_tactical_prefer_full_doc_concatenates_under_budget():
    """Tranche 1 sub-edit 1.3: prefer_full_doc=True (Stage3 producer 전용) 모드는
    bullet TL;DR과 per-ep prose를 함께 결합하고 budget으로 잘라야 한다."""
    from modules.core.tactical_utils import extract_episode_tactical

    tactical_doc = "[제1화 prologue]\nA detailed prose body about ep1 events.\n[제2화 next]\nlater\n"
    episode_details = [
        {"ep_num": 1, "details": ["concrete entity X", "arithmetic anchor Y"]},
    ]

    result = extract_episode_tactical(
        tactical_doc,
        1,
        episode_details=episode_details,
        prefer_full_doc=True,
    )
    # TL;DR과 prose가 모두 포함되어야 한다
    assert "[TL;DR — episode_details]" in result
    assert "concrete entity X" in result
    assert "arithmetic anchor Y" in result
    assert "[Tactical doc — 제1화]" in result
    assert "A detailed prose body about ep1 events." in result

    # budget 내에서 잘려야 한다
    long_tactical = "[제1화 X]\n" + ("a" * 5000) + "\n[제2화 Y]\n"
    result_truncated = extract_episode_tactical(
        long_tactical,
        1,
        episode_details=episode_details,
        prefer_full_doc=True,
        full_doc_budget_chars=500,
    )
    assert len(result_truncated) <= 600  # budget + truncation marker overhead
    assert "[truncated]" in result_truncated


def test_tranche1_normalize_opening_transition_returns_missing_on_pure_omission():
    """Tranche 1 sub-edit 1.4: LLM이 opening_transition을 선언하지 않았고
    prev_blueprint/scene 단서도 없으면 'missing'을 반환해 cheap admission이 fail-closed."""
    candidate = {
        # opening_transition 누락
        "scene_breakdown": {},
        # start_location/time_flow/scene_text 모두 부재
    }
    route = BlueprintEnsembleGenerator._normalize_opening_transition_contract(
        candidate,
        prev_blueprint=None,
    )
    assert route == "missing"


def test_tranche1_normalize_opening_transition_returns_inferred_when_continuity_anchor_exists():
    """Tranche 1 sub-edit 1.4: LLM이 선언하지 않았지만 prev_blueprint/scene 단서가
    있으면 'inferred'를 반환하고 candidate를 mutate해야 한다."""
    candidate = {
        "start_location": "한미증권 본사",
        "time_flow": "오전",
        "scene_breakdown": {
            "scene_1": {"location": "한미증권 본사", "summary": "회의 시작"},
        },
    }
    route = BlueprintEnsembleGenerator._normalize_opening_transition_contract(
        candidate,
        prev_blueprint={"end_location": "한미증권 본사", "time_flow": "오전"},
    )
    assert route == "inferred"
    assert isinstance(candidate.get("opening_transition"), dict)
    assert candidate["opening_transition"].get("type") in {
        "direct_continuation",
        "explicit_transition",
        "jump_opening",
    }
