from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator


def _make_context():
    ctx = SimpleNamespace()
    ctx.author_directives = ""
    ctx.db = MagicMock()
    ctx.db.load_anchor.return_value = {}
    ctx.current_project = SimpleNamespace(name="Lane A Project")
    ctx.project_name = "Lane A Project"
    return ctx


def _make_agent() -> ArcEnsembleGenerator:
    agent = ArcEnsembleGenerator(_make_context(), MagicMock())
    agent._operator_log = MagicMock()
    agent._build_strategy_execution_plan = MagicMock(side_effect=lambda items: [dict(item) for item in items])
    return agent


def _base_candidate(**overrides) -> dict:
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
    candidate.update(overrides)
    return candidate


def test_generate_ensemble_single_strategy_live_shell_routes_only_selected_strategy():
    agent = _make_agent()
    agent.max_workers = 1
    agent.strategies = [
        {"name": "conservative", "temperature": 0.3, "focus": "", "style": ""},
        {"name": "balanced", "temperature": 0.5, "focus": "", "style": ""},
        {"name": "creative", "temperature": 0.7, "focus": "", "style": ""},
    ]
    agent._get_or_create_context_cache = MagicMock(return_value={"cache_name": "cache/arc"})
    agent._evaluate_candidate = MagicMock(return_value=(91, []))
    agent._generate_single = MagicMock(return_value=_base_candidate())

    best, candidates = agent.generate_ensemble(
        arc_no=4,
        ep_start=10,
        vol_strategy="",
        curr_block={"ep_count": 3},
        prev_arc_context="prev context",
        constraint_block="constraint",
        assets={},
        single_strategy="balanced",
        strategy_specific_feedback="tighten act 2",
        rejected_strategy="balanced",
    )

    assert best is None
    assert len(candidates) == 1
    assert agent._generate_single.call_count == 1
    kwargs = agent._generate_single.call_args.kwargs
    assert kwargs["strategy"]["name"] == "balanced"
    assert kwargs["strategy_feedback"] == "tighten act 2"


def test_qualify_candidates_by_tactical_length_keeps_longest_short_candidate():
    agent = _make_agent()

    shorter = _base_candidate(tactical_doc={"content": "a" * 400}, ep_count=3, _strategy="shorter")
    longer = _base_candidate(tactical_doc=["b" * 700], ep_count=3, _strategy="longer")

    qualified = agent._qualify_candidates_by_tactical_length([shorter, longer], fallback_ep_count=3)

    assert qualified == [longer]
    assert shorter["tactical_doc"] == "a" * 400
    assert longer["tactical_doc"] == "b" * 700


def test_apply_ensemble_metadata_strips_transient_scoring_fields():
    agent = _make_agent()
    director_candidates = [_base_candidate(_strategy="balanced", _score=88, _issues=["first issue"])]
    scored_candidates = director_candidates + [_base_candidate(_strategy="creative", _score=81, _issues=[])]

    agent._apply_ensemble_metadata(
        director_candidates,
        scored_candidates,
        {"max_similarity": 0.25, "warning": ""},
    )

    meta = director_candidates[0]["_ensemble_meta"]
    assert meta["all_scores"] == [("balanced", 88), ("creative", 81)]
    assert meta["candidate_index"] == 0
    assert meta["total_candidates"] == 1
    assert "_score" not in scored_candidates[0]
    assert "_issues" not in scored_candidates[1]


def test_build_single_arc_generation_context_uses_structured_current_block_authority_packet():
    agent = _make_agent()

    prompt_context = agent._build_single_arc_generation_context(
        curr_block={
            "block_id": "block_02",
            "title": "Branch Office Pressure",
            "ep_count": 3,
            "content": {"context": "The protagonist enters the branch office and faces pressure."},
            "block_theme": "escalation",
            "foreshadow": "a missing ledger",
        },
        prev_arc_context="previous context",
        constraint_block="constraint block",
        protagonist_config=None,
        entity_registry=None,
        genre="investment",
    )

    packet = prompt_context["curr_block_authority"]
    assert "CURRENT BLOCK DNA > BLOCK EVENT GUARD > PREVIOUS ARC CONTEXT > OPTIONAL EXTENSIONS" in packet
    assert '"title"' not in packet
    assert "- title: Branch Office Pressure" in packet
    assert "- block_premise: The protagonist enters the branch office and faces pressure." in packet


def test_arc_prompt_places_current_block_before_previous_arc_context():
    agent = _make_agent()
    prompt_context = agent._build_single_arc_generation_context(
        curr_block={
            "block_id": "block_02",
            "title": "Branch Office Pressure",
            "content": {"context": "The protagonist enters the branch office."},
        },
        prev_arc_context="PREV_ARC_CONTEXT",
        constraint_block="CONSTRAINT_BLOCK",
        protagonist_config=None,
        entity_registry=None,
        genre="investment",
    )

    prompt, _ = agent._build_single_arc_prompt_bundle(
        strategy={"name": "balanced", "focus": "focus", "style": "style"},
        prompt_context=prompt_context,
        constraint_block="CONSTRAINT_BLOCK",
        prev_arc_context="PREV_ARC_CONTEXT",
        curr_block={"title": "Branch Office Pressure"},
        pacing_signal_guide="",
        vol_strategy="",
        assets={},
        merged_feedback="",
        protagonist_name="Hero",
        genre="investment",
        arc_no=2,
        ep_start=5,
        ep_end=7,
        cache_name="",
    )

    block_idx = prompt.index("### [Current Block DNA]")
    guard_idx = prompt.index("### [Current Block Event Guard]")
    prev_idx = prompt.index("### [Previous Arc Context - carryover reference]")

    assert block_idx < prev_idx
    assert guard_idx < prev_idx
