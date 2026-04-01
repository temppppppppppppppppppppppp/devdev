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
        single_strategy="action_focused",
    )

    assert result == finalized
    assert agent.last_error_types == [AgentErrorType.TIMEOUT]
    assert agent.last_error_type == AgentErrorType.TIMEOUT
    agent._prepare_blueprint_ensemble_context.assert_called_once()
    agent._select_blueprint_ensemble_strategies.assert_called_once_with("action_focused")
    agent._run_blueprint_ensemble_workers.assert_called_once()
    assert agent._run_blueprint_ensemble_workers.call_args.kwargs["cache_name"] == "cache/bp"
    agent._qualify_blueprint_candidates.assert_called_once_with(raw_candidates)
    agent._finalize_blueprint_candidates.assert_called_once_with(qualified_candidates, [])


def test_qualify_blueprint_candidates_tracks_pass_and_fail_metadata():
    agent = _make_agent()

    qualified, disqualified = agent._qualify_blueprint_candidates(
        [
            {
                "_strategy": "action_focused",
                "scene_breakdown": [{"scene": 1}, {"scene": 2}, {"scene": 3}, {"scene": 4}],
                "integrated_scenario": "x" * 600,
            },
            {
                "_strategy": "dialogue_focused",
                "scene_breakdown": [{"scene": 1}, {"scene": 2}, {"scene": 3}],
                "integrated_scenario": "x" * 320,
            },
        ]
    )

    assert len(qualified) == 1
    assert qualified[0]["_qualified"] is True
    assert qualified[0]["_scene_count"] == 4
    assert qualified[0]["_length"] == 600
    assert disqualified == [("dialogue_focused", 3, 320)]


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
            }
        },
        "integrated_scenario": "주인공은 문을 열고 적과 마주친다. " * 40,
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
