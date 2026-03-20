import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from modules.core.stage2_finalizer import Stage2Finalizer


def _build_stage2_finalizer_with_reject() -> Stage2Finalizer:
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.pass_rate_monitor = None
    ctx.quality_dashboard = None
    ctx.stage2_optimizer = None
    ctx.perf_timer = MagicMock()
    ctx.stage_rejection_history = []
    ctx.audit_event = MagicMock()
    ctx.semantic_plot_guard = None
    ctx.validate_arc_integrity = MagicMock(return_value=True)
    ctx.validate_arc_data_fields = None
    ctx.current_project = MagicMock()
    ctx.current_project.db = MagicMock()
    ctx.safe_commit_async = AsyncMock(return_value=True)
    ctx.generate_arc_context_v60 = MagicMock(return_value="context_text")
    ctx.cumulative_state_cache = None
    ctx.cumulative_state_cache_key = 0
    ctx.get_adaptive_feedback_intensity = MagicMock(return_value={"guidance": "guide"})
    ctx.state_tracker = SimpleNamespace(foo=0, bar=0)

    director = MagicMock()
    director.audit_strategic_plan.return_value = {
        "decision": "REJECT",
        "score": 30,
        "reason": "reject reason",
        "re_slice_instruction": "fix structure",
    }
    ctx.agents = {"director": director}

    host = MagicMock()
    host.ctx = ctx
    return Stage2Finalizer(host)


def _make_finalize_kwargs() -> dict:
    return {
        "refined_arc": {
            "arc_no": 1,
            "ep_start": 1,
            "ep_end": 10,
            "ep_count": 10,
            "tactical_doc": "A" * 1600,
            "state_changes": {"npc_deaths": [], "relationship_changes": []},
            "hybrid_composition": {"primary": "standard_progression", "secondary": [], "mixing_logic": "default"},
            "joint_docs": {
                "final_location": "market",
                "physical_inventory": [],
                "world_joint": "stable",
            },
            "status_shadow": {
                "internal_energy_loss": "10%",
                "expected_injuries": "none",
                "item_consumption": [],
            },
            "state_constraints": {"items_acquired": []},
        },
        "enriched_block": {
            "joint_docs": {"final_location": "city", "physical_inventory": [], "world_joint": "stable"},
            "status_shadow": {"internal_energy_loss": "5%", "expected_injuries": "none", "item_consumption": []},
            "joint_docs_brief": "brief",
        },
        "arc_drive": {"desire_vector": "test"},
        "all_refined_arcs": [],
        "global_arc_no": 1,
        "current_ep_start": 1,
        "current_feedback": "",
        "protagonist_name": "hero",
        "suspected_duplicates": [],
        "entity_registry_for_director": {},
        "constraint_block": "",
        "draft_validator_passed": False,
        "consensus_passed": False,
        "attempt": 0,
        "generation_method": "four_phase",
        "st_snapshot": None,
        "director_feedback_for_fourphase": "",
        "last_refined_context": "prev context",
        "bible_root": {"protagonist_config": {"name": "hero", "incarnation_type": "regressor"}},
        "genre": "fantasy",
        "constraint_db": MagicMock(arc_states=[]),
    }


def test_finalizer_returns_retry_on_director_reject() -> None:
    finalizer = _build_stage2_finalizer_with_reject()
    kwargs = _make_finalize_kwargs()

    with patch("modules.core.spinners.V50_MODULES_AVAILABLE", False):
        result = asyncio.run(finalizer.run_finalize(**kwargs))

    assert result["action"] == "retry"


def test_orchestrator_next_action_does_not_break_loop() -> None:
    source = Path("modules/core/stage2_orchestrator.py").read_text(encoding="utf-8")
    marker = 'elif transition["action"] == "next":'
    idx = source.find(marker)
    assert idx != -1

    window = source[idx : idx + 180]
    assert "attempt += 1" in window
    assert "continue" in window
    assert "break" not in window.split("continue", 1)[0]
