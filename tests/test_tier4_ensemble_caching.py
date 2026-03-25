import inspect
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.domain.agents.base_agent import AgentErrorType
from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator, _build_block_event_guard
from modules.domain.agents.blueprint_ensemble import BlueprintEnsembleGenerator


def _make_agent_context():
    ctx = SimpleNamespace()
    ctx.author_directives = ""
    ctx.db = MagicMock()
    ctx.db.load_anchor.return_value = {}
    ctx.current_project = SimpleNamespace(name="Cache Project")
    ctx.project_name = "Cache Project"
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
    assert agent._get_or_create_context_cache.call_args.kwargs["project_name"] == "Cache_Project_arc_1"
    assert agent._generate_single.call_count == len(agent.strategies)
    assert all(call.kwargs["cache_name"] == "cache/arc" for call in agent._generate_single.call_args_list)


def test_arc_ensemble_cached_path_uses_stub_prompt_and_full_fallback():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = ArcEnsembleGenerator(ctx, client)

    def _load_side_effect(_file, _key, **kwargs):
        return (
            f"prev={kwargs['prev_arc_context']}|constraint={kwargs['constraint_block']}|"
            f"vol={kwargs['vol_strategy']}|assets={kwargs['assets']}|feedback={kwargs['feedback']}|"
            f"pacing={kwargs['pacing_signal_guide']}"
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

    vol_tail = "TAIL-VOL-STRATEGY"
    asset_tail = "TAIL-ASSET-PAYLOAD"
    feedback_tail = "TAIL-FEEDBACK-PAYLOAD"
    pacing_tail = "TAIL-PACING-GUIDE"
    result = agent._generate_single(
        arc_no=1,
        ep_start=1,
        ep_end=3,
        vol_strategy="HEAD-VOL\n" + ("V" * 6500) + "\n" + vol_tail,
        curr_block={"ep_count": 3},
        prev_arc_context="PREV_CONTEXT_PAYLOAD",
        constraint_block="CONSTRAINT_PAYLOAD",
        assets={"payload": "A" * 7000, "tail": asset_tail},
        feedback="HEAD-FEEDBACK\n" + ("F" * 9500) + "\n" + feedback_tail,
        pacing_signal_guide="HEAD-PACING\n" + ("P" * 1500) + "\n" + pacing_tail,
        strategy={"name": "balanced", "temperature": 0.5, "focus": "f", "style": "s"},
        cache_name="cache/arc",
    )

    assert result is not None
    assert captured["cache_name"] == "cache/arc"
    assert "PREV_CONTEXT_PAYLOAD" not in captured["prompt"]
    assert "CONSTRAINT_PAYLOAD" not in captured["prompt"]
    assert "PREV_CONTEXT_PAYLOAD" in captured["fallback"]
    assert "CONSTRAINT_PAYLOAD" in captured["fallback"]
    assert vol_tail in captured["prompt"]
    assert vol_tail in captured["fallback"]
    assert asset_tail in captured["prompt"]
    assert asset_tail in captured["fallback"]
    assert feedback_tail in captured["prompt"]
    assert feedback_tail in captured["fallback"]
    assert pacing_tail in captured["prompt"]
    assert pacing_tail in captured["fallback"]
    assert "...(중간 생략)..." in captured["prompt"]
    assert "...(중간 생략)..." in captured["fallback"]


def test_arc_ensemble_normalizes_llm_pacing_contract():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = ArcEnsembleGenerator(ctx, client)

    result = agent._normalize_pacing_contract(
        {
            "ep_count": 6,
            "pacing_decision": {
                "pace_mode": "compressed",
                "ep_count_reasoning": "사건 밀도가 높다",
                "density_focus": "설명 반복을 줄인다",
            },
        },
        ep_start=11,
        ep_count_suggestion=4,
    )

    assert result["ep_count"] == 3
    assert result["ep_start"] == 11
    assert result["ep_end"] == 13
    assert result["pacing_decision"]["pace_mode"] == "compressed"


def test_arc_ensemble_tactical_length_uses_candidate_ep_count_not_python_hint():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = ArcEnsembleGenerator(ctx, client)
    agent.max_workers = 1
    agent._get_or_create_context_cache = MagicMock(return_value={"cache_name": "cache/arc"})
    agent._evaluate_candidate = MagicMock(return_value=(95, []))

    candidate = {
        "arc_no": 1,
        "ep_count": 3,
        "pacing_decision": {"pace_mode": "compressed"},
        "tactical_doc": "x" * 1500,
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
        curr_block={},
        prev_arc_context="prev context",
        constraint_block="constraint",
        assets={},
        feedback="",
        ep_count_suggestion=6,
        pacing_signals={"ep_count_suggestion": 6, "suggested_pace_mode": "expanded"},
    )

    assert best is None
    assert len(candidates) > 0


def test_arc_ensemble_feedback_merge_appends_strategy_section_once():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = ArcEnsembleGenerator(ctx, client)

    merged = agent._merge_single_arc_feedback("기존 피드백", "전략 보정")

    assert merged == "기존 피드백\n\n[전략별 보정 피드백]\n전략 보정"


def test_arc_ensemble_finalize_single_arc_candidate_normalizes_and_fills_defaults():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = ArcEnsembleGenerator(ctx, client)

    finalized = agent._finalize_single_arc_candidate(
        {
            "ep_count": 6,
            "pacing_decision": {"pace_mode": "compressed"},
            "state_constraints": {},
        },
        arc_no=7,
        ep_start=21,
        ep_end=26,
        ep_count_suggestion=4,
    )

    assert finalized["arc_no"] == 7
    assert finalized["ep_start"] == 21
    assert finalized["ep_count"] == 3
    assert finalized["ep_end"] == 23
    assert "joint_docs" in finalized
    assert "state_constraints" in finalized
    assert "status_shadow" in finalized
    assert "state_changes" in finalized


def test_arc_block_event_guard_preserves_recent_tail_context():
    result = _build_block_event_guard(
        {
            "content": {
                "context": "HEAD-CONTEXT " + ("A" * 400) + " TAIL-CONTEXT",
                "solution": "HEAD-SOLUTION " + ("B" * 400) + " TAIL-SOLUTION",
            }
        },
        max_field_len=180,
    )

    assert "TAIL-CONTEXT" in result
    assert "TAIL-SOLUTION" in result
    assert "...(중간 생략)..." in result


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
    assert agent._get_or_create_context_cache.call_args.kwargs["project_name"] == "Cache_Project_ep_11"
    assert agent._generate_single.call_count == 1
    assert agent._generate_single.call_args.kwargs["cache_name"] == "cache/bp"


def test_blueprint_ensemble_aggregates_worker_error_types_without_race():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = BlueprintEnsembleGenerator(ctx, client)
    agent._get_or_create_context_cache = MagicMock(return_value={"cache_name": "cache/bp"})
    agent._generate_single = MagicMock(
        side_effect=[
            (None, AgentErrorType.TIMEOUT),
            (None, AgentErrorType.SCHEMA_INCOMPATIBLE),
            (None, AgentErrorType.QUOTA_EXCEEDED),
        ]
    )

    best, candidates = agent.generate_ensemble(
        ep_num=11,
        arc_data={},
        constraint_block={},
    )

    assert best is None
    assert candidates == []
    assert set(agent.last_error_types) == {
        AgentErrorType.TIMEOUT,
        AgentErrorType.SCHEMA_INCOMPATIBLE,
        AgentErrorType.QUOTA_EXCEEDED,
    }
    assert agent.last_error_type == AgentErrorType.SCHEMA_INCOMPATIBLE


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


def test_blueprint_ensemble_prev_info_expanded_preserves_tail_context():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = BlueprintEnsembleGenerator(ctx, client)

    bp_tail = "BP-TAIL-MARKER"
    ms_tail = "MS-TAIL-MARKER"
    prev_blueprints = [
        {
            "ep_num": idx,
            "title": f"title-{idx}",
            "integrated_scenario": ("장면 " * 150000) + (bp_tail if idx == 3 else ""),
            "end_location": "한양",
            "ending_hook": "후크",
            "scene_breakdown": [{"title": "scene", "characters": ["a"], "key_events": ["e"]}],
        }
        for idx in range(1, 4)
    ]
    prev_manuscripts_text = ("원고 " * 150000) + ms_tail

    result = agent._format_prev_info_expanded(
        prev_blueprint={"ep_num": 3, "title": "direct", "integrated_scenario": "direct"},
        prev_blueprints=prev_blueprints,
        prev_manuscripts_text=prev_manuscripts_text,
    )

    assert bp_tail in result
    assert ms_tail in result


def test_blueprint_ensemble_prev_info_scene_summary_preserves_tail_context():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = BlueprintEnsembleGenerator(ctx, client)

    char_tail = "TAIL-CHARACTER"
    event_tail = "TAIL-EVENT"
    result = agent._format_prev_info_expanded(
        prev_blueprint={"ep_num": 1, "title": "direct", "integrated_scenario": "direct"},
        prev_blueprints=[
            {
                "ep_num": 1,
                "title": "scene-heavy",
                "integrated_scenario": "scenario",
                "scene_breakdown": [
                    {
                        "title": "HEAD-SCENE\n" + ("S" * 140) + "\nTAIL-SCENE",
                        "characters": [f"char-{idx}" for idx in range(10)] + [char_tail],
                        "key_events": [f"event-{idx}" for idx in range(8)] + [event_tail],
                    }
                ],
            }
        ],
        prev_manuscripts_text="",
    )

    assert "TAIL-SCENE" in result
    assert char_tail in result
    assert event_tail in result


def test_blueprint_ensemble_arc_focus_preserves_tail_context():
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

    must_focus = "HEAD-FOCUS\n" + ("A" * 20000) + "\nTAIL-FOCUS"
    best, _ = agent.generate_ensemble(
        ep_num=11,
        arc_data={},
        constraint_block={"must_focus": {"content": must_focus}},
        single_strategy="action_focused",
    )

    assert best is not None
    passed_focus = agent._generate_single.call_args.kwargs["arc_focus"]
    assert len(passed_focus) <= 15000
    assert "TAIL-FOCUS" in passed_focus


def test_blueprint_ensemble_constraint_summary_preserves_recent_tail_context():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = BlueprintEnsembleGenerator(ctx, client)

    result = agent._format_constraints(
        {
            "must_focus": {"content": "HEAD-MUST\n" + ("A" * 900) + "\nTAIL-MUST"},
            "stop_line": {"content": "HEAD-STOP\n" + ("B" * 300) + "\nTAIL-STOP"},
            "continuity": {
                "location": "HEAD-LOC\n" + ("C" * 240) + "\nTAIL-LOC",
                "time_context": "HEAD-TIME\n" + ("D" * 220) + "\nTAIL-TIME",
                "ongoing_conflicts": ["HEAD-CONFLICT\n" + ("E" * 200) + "\nTAIL-CONFLICT"],
            },
            "inherited_state": {
                "equipment": "HEAD-EQUIP\n" + ("F" * 320) + "\nTAIL-EQUIP",
                "mood": "HEAD-MOOD\n" + ("G" * 200) + "\nTAIL-MOOD",
            },
            "arc_constraint_summary": "HEAD-ARC\n" + ("H" * 900) + "\nTAIL-ARC",
            "state_changes_summary": "HEAD-STATE\n" + ("I" * 1300) + "\nTAIL-STATE",
            "semantic_carryover": {
                "relationship_rationale": [
                    {"npc": "Han", "trigger": "HEAD-REL\n" + ("J" * 260) + "\nTAIL-REL"}
                ],
                "growth_justification": "HEAD-GROWTH\n" + ("K" * 320) + "\nTAIL-GROWTH",
                "foreshadow_anchors": ["HEAD-ANCHOR\n" + ("L" * 260) + "\nTAIL-ANCHOR"],
                "continuity_checkpoints": ["HEAD-CHK\n" + ("M" * 220) + "\nTAIL-CHK"],
            },
        }
    )

    for marker in [
        "TAIL-MUST",
        "TAIL-STOP",
        "TAIL-LOC",
        "TAIL-TIME",
        "TAIL-CONFLICT",
        "TAIL-EQUIP",
        "TAIL-MOOD",
        "TAIL-ARC",
        "TAIL-STATE",
        "TAIL-REL",
        # [W2] growth_justification and continuity_checkpoints are suppressed
        # "TAIL-GROWTH",
        "TAIL-ANCHOR",
        # "TAIL-CHK",
    ]:
        assert marker in result


def test_blueprint_ensemble_constraints_include_episode_title():
    ctx = _make_agent_context()
    client = MagicMock()
    agent = BlueprintEnsembleGenerator(ctx, client)

    result = agent._format_constraints(
        {
            "must_focus": {
                "arc_title": "의심의 씨앗",
                "content": "핵심 장면",
            }
        }
    )

    assert "[이번 화 제목]" in result
    assert "의심의 씨앗" in result


def test_blueprint_ensemble_has_single_format_constraints_definition():
    source = inspect.getsource(BlueprintEnsembleGenerator)

    assert source.count("def _format_constraints(") == 1
