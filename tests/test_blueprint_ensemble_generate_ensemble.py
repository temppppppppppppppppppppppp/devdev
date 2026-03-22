from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.constants import GenreTypes
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


def test_request_blueprint_generation_rejects_missing_required_fields():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(return_value='{"scene_breakdown": []}')
    agent._extract_json_robust = MagicMock(return_value={"scene_breakdown": []})

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
    )

    assert result == (None, AgentErrorType.SCHEMA_INCOMPATIBLE)
