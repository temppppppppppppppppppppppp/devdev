import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator
from modules.domain.agents.blueprint_ensemble import BlueprintEnsembleGenerator


def _make_agent_context():
    ctx = SimpleNamespace()
    ctx.author_directives = ""
    ctx.db = MagicMock()
    ctx.db.load_anchor.return_value = {}
    return ctx


def test_arc_ensemble_uses_shared_context_cache_name():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = ArcEnsembleGenerator(ctx, client)
    agent.max_workers = 1
    agent._get_or_create_context_cache = MagicMock(return_value={"cache_name": "cache/arc"})
    agent._evaluate_candidate = MagicMock(return_value=(95, []))

    candidate = {
        "arc_no": 1,
        "ep_count": 3,
        "tactical_doc": "x" * 1800,
        "joint_docs": {"final_location": "A", "physical_inventory": [], "world_joint": ""},
        "state_constraints": {
            "arc_start_state": {"location": "A", "equipment": []},
            "arc_end_state": {"location": "B", "equipment": []},
            "items_acquired": [],
            "items_consumed": [],
        },
        "state_changes": {
            "timeline": {"start": {}, "end": {}},
            "npc_deaths": [],
            "skill_acquisitions": [],
            "relationship_changes": [],
            "major_items": [],
            "resolved_plots": [],
        },
    }
    agent._generate_single = MagicMock(return_value=candidate)

    best, candidates = agent.generate_ensemble(
        arc_no=1,
        ep_start=1,
        vol_strategy="",
        curr_block={"ep_count": 3},
        prev_arc_context="prev context",
        constraint_block="constraint",
        assets={},
        feedback="",
    )

    assert best is None
    assert len(candidates) > 0
    agent._get_or_create_context_cache.assert_called_once()
    assert agent._generate_single.call_count == len(agent.strategies)
    assert all(call.kwargs["cache_name"] == "cache/arc" for call in agent._generate_single.call_args_list)


def test_arc_ensemble_cached_path_uses_stub_prompt_and_full_fallback():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = ArcEnsembleGenerator(ctx, client)

    def _load_side_effect(_file, _key, **kwargs):
        return (
            f"prev={kwargs['prev_arc_context']}|constraint={kwargs['constraint_block']}|"
            f"vol={kwargs['vol_strategy']}|assets={kwargs['assets']}"
        )

    agent._prompt_loader = MagicMock()
    agent._prompt_loader.load.side_effect = _load_side_effect

    captured = {}

    def _cached_side_effect(*, cache_name, prompt, temperature, thinking_level, full_prompt_fallback, response_schema=None):
        captured["cache_name"] = cache_name
        captured["prompt"] = prompt
        captured["fallback"] = full_prompt_fallback
        return {
            "arc_no": 1,
            "ep_count": 3,
            "tactical_doc": "x" * 1800,
            "joint_docs": {"final_location": "A", "physical_inventory": [], "world_joint": ""},
            "state_constraints": {
                "arc_start_state": {"location": "A", "equipment": []},
                "arc_end_state": {"location": "B", "equipment": []},
                "items_acquired": [],
                "items_consumed": [],
            },
            "state_changes": {
                "timeline": {"start": {}, "end": {}},
                "npc_deaths": [],
                "skill_acquisitions": [],
                "relationship_changes": [],
                "major_items": [],
                "resolved_plots": [],
            },
        }

    agent._ask_with_cached_context = MagicMock(side_effect=_cached_side_effect)

    result = agent._generate_single(
        arc_no=1,
        ep_start=1,
        ep_end=3,
        vol_strategy="V" * 6500,
        curr_block={"ep_count": 3},
        prev_arc_context="PREV_CONTEXT_PAYLOAD",
        constraint_block="CONSTRAINT_PAYLOAD",
        assets={"payload": "A" * 7000},
        feedback="",
        strategy={"name": "balanced", "temperature": 0.5, "focus": "f", "style": "s"},
        cache_name="cache/arc",
    )

    assert result is not None
    assert captured["cache_name"] == "cache/arc"
    assert "PREV_CONTEXT_PAYLOAD" not in captured["prompt"]
    assert "CONSTRAINT_PAYLOAD" not in captured["prompt"]
    assert "PREV_CONTEXT_PAYLOAD" in captured["fallback"]
    assert "CONSTRAINT_PAYLOAD" in captured["fallback"]
    assert "V" * 6000 in captured["prompt"]
    assert "V" * 6001 not in captured["prompt"]
    assert "V" * 6000 in captured["fallback"]
    assert "V" * 6001 not in captured["fallback"]
    expected_assets = json.dumps({"payload": "A" * 7000}, ensure_ascii=False)[:6000]
    assert expected_assets in captured["prompt"]
    assert expected_assets in captured["fallback"]


def test_blueprint_ensemble_uses_shared_context_cache_name():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = BlueprintEnsembleGenerator(ctx, client)
    agent.max_workers = 1
    agent._get_or_create_context_cache = MagicMock(return_value={"cache_name": "cache/bp"})

    candidate = {
        "scene_breakdown": [{"scene": 1}, {"scene": 2}, {"scene": 3}, {"scene": 4}],
        "integrated_scenario": "x" * 600,
    }
    agent._generate_single = MagicMock(return_value=candidate)

    best, _ = agent.generate_ensemble(
        ep_num=11,
        arc_data={},
        constraint_block={},
        single_strategy="action_focused",
    )

    assert best is not None
    agent._get_or_create_context_cache.assert_called_once()
    assert agent._generate_single.call_count == 1
    assert agent._generate_single.call_args.kwargs["cache_name"] == "cache/bp"


def test_blueprint_ensemble_cached_path_uses_stub_prompt_and_full_fallback():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = BlueprintEnsembleGenerator(ctx, client)

    def _load_side_effect(_file, _key, **kwargs):
        return (
            f"arc={kwargs['arc_focus']}|constraints={kwargs['constraints']}|"
            f"prev={kwargs['prev_info']}|hud={kwargs['hud_context']}"
        )

    agent._prompt_loader = MagicMock()
    agent._prompt_loader.load.side_effect = _load_side_effect
    agent._build_reader_feedback_context = MagicMock(return_value="")

    captured = {}

    def _cached_side_effect(*, cache_name, prompt, temperature, thinking_level, full_prompt_fallback, response_schema=None):
        captured["cache_name"] = cache_name
        captured["prompt"] = prompt
        captured["fallback"] = full_prompt_fallback
        return json.dumps(
            {
                "scene_breakdown": [{"scene": 1}, {"scene": 2}, {"scene": 3}, {"scene": 4}],
                "integrated_scenario": "x" * 600,
            },
            ensure_ascii=False,
        )

    agent._ask_with_cached_context = MagicMock(side_effect=_cached_side_effect)

    result = agent._generate_single(
        ep_num=11,
        arc_focus="ARC_FOCUS_PAYLOAD",
        constraints_str="CONSTRAINTS_PAYLOAD",
        prev_info="PREV_INFO_PAYLOAD",
        strategy={"display": "액션", "directive": "지시문"},
        hud_context="HUD_PAYLOAD",
        cache_name="cache/bp",
    )

    assert result is not None
    assert captured["cache_name"] == "cache/bp"
    assert "ARC_FOCUS_PAYLOAD" not in captured["prompt"]
    assert "CONSTRAINTS_PAYLOAD" not in captured["prompt"]
    assert "PREV_INFO_PAYLOAD" not in captured["prompt"]
    assert "HUD_PAYLOAD" not in captured["prompt"]
    assert "ARC_FOCUS_PAYLOAD" in captured["fallback"]
    assert "CONSTRAINTS_PAYLOAD" in captured["fallback"]
    assert "PREV_INFO_PAYLOAD" in captured["fallback"]
    assert "HUD_PAYLOAD" in captured["fallback"]
