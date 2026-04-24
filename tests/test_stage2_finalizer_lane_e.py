import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.core.stage2_finalizer import Stage2Finalizer


@pytest.fixture
def finalizer():
    ctx = MagicMock()
    ctx.ui = SimpleNamespace(log=MagicMock())
    ctx.current_project = MagicMock()
    ctx.current_project.db = MagicMock()
    ctx.current_project.load_v20_anchor = MagicMock(return_value=None)
    ctx.current_project.save_v20_anchor = MagicMock()
    ctx.safe_commit_async = AsyncMock(return_value=True)
    ctx.generate_arc_context_v60 = MagicMock(return_value="next-context")
    ctx.cumulative_state_cache = "cached"
    ctx.cumulative_state_cache_key = "key"
    ctx.agents = {"director": MagicMock()}
    host = SimpleNamespace(ctx=ctx)
    return Stage2Finalizer(host)


def test_prepare_stage2_pass_arc_for_persistence_shell_delegates_to_family(finalizer):
    repair_result = {"action": "continue", "refined_arc": {"ep_end": 5, "state_changes": {}}}
    finalize_result = {"action": "continue", "refined_arc": {"ep_end": 5, "state_changes": {}}}
    finalizer._repair_stage2_pass_arc_structure = MagicMock(return_value=repair_result)
    finalizer._finalize_stage2_pass_arc_preparation = MagicMock(return_value=finalize_result)
    refined_arc = {
        "joint_docs": {"world_joint": "llm-world"},
        "status_shadow": {"hp": "stable", "key_stat_change": "llm-stat"},
    }

    result = finalizer._prepare_stage2_pass_arc_for_persistence(
        refined_arc=refined_arc,
        arc_drive={"desire_vector": "test"},
        enriched_block={
            "joint_docs": {"final_location": "city", "world_joint": "stale-world"},
            "status_shadow": {"hp": "fallback-stable", "expected_injuries": "none"},
        },
        all_refined_arcs=[],
        global_arc_no=3,
        current_feedback="",
        generation_method="four_phase",
        st_snapshot=None,
        cdb_snapshot=None,
        constraint_db=MagicMock(),
        constraint_block="MUST NOT regress",
        genre="investment",
    )

    assert result == finalize_result
    assert refined_arc["arc_drive"] == {"desire_vector": "test"}
    assert refined_arc["joint_docs"] == {"final_location": "city", "world_joint": "llm-world"}
    assert refined_arc["status_shadow"] == {
        "hp": "stable",
        "expected_injuries": "none",
        "key_stat_change": "llm-stat",
    }
    finalizer._repair_stage2_pass_arc_structure.assert_called_once()
    finalizer._finalize_stage2_pass_arc_preparation.assert_called_once_with(
        refined_arc=repair_result["refined_arc"],
        all_refined_arcs=[],
        global_arc_no=3,
        constraint_block="MUST NOT regress",
        enriched_block={
            "joint_docs": {"final_location": "city", "world_joint": "stale-world"},
            "status_shadow": {"hp": "fallback-stable", "expected_injuries": "none"},
        },
        genre="investment",
    )


def test_finalize_stage2_pass_persistence_and_tail_shell_delegates_to_post_commit_family(finalizer):
    finalizer._persist_stage2_pass_arc_commit = AsyncMock(return_value=None)
    finalizer._update_stage2_pass_constraint_db = MagicMock()
    finalizer._advance_stage2_pass_persistence_state = MagicMock(
        return_value={"last_refined_context": "next-context", "current_ep_start": 11}
    )
    finalizer._record_s2_pass_metrics = MagicMock()
    finalizer._persist_stage2_pass_cost_record = MagicMock()
    finalizer._maybe_generate_stage2_volume_summaries = MagicMock()
    refined_arc = {"ep_end": 10, "_strategy": "ensemble"}
    all_refined_arcs = [refined_arc]

    result = asyncio.run(
        finalizer._finalize_stage2_pass_persistence_and_tail(
            refined_arc=refined_arc,
            all_refined_arcs=all_refined_arcs,
            global_arc_no=2,
            current_feedback="keep",
            st_snapshot={"foo": 1},
            cdb_snapshot={"bar": 2},
            constraint_db=MagicMock(),
            last_refined_context="prev-context",
            current_ep_start=1,
            director_feedback_for_fourphase="director-note",
            attempt=1,
            generation_method="four_phase",
            audit={"score": 92},
            director_duration_ms=77,
            is_patch=False,
            prev_score=91.0,
            patch_fallback=False,
        )
    )

    assert result == {
        "action": "break",
        "last_refined_context": "next-context",
        "current_ep_start": 11,
        "current_feedback": "keep",
        "director_feedback_for_fourphase": "director-note",
        "st_snapshot": None,
        "score": 92,
        "fix_scope": "",
    }
    finalizer._persist_stage2_pass_arc_commit.assert_awaited_once()
    finalizer._update_stage2_pass_constraint_db.assert_called_once()
    finalizer._advance_stage2_pass_persistence_state.assert_called_once_with(
        refined_arc=refined_arc,
        all_refined_arcs=all_refined_arcs,
        global_arc_no=2,
        last_refined_context="prev-context",
    )
    finalizer._record_s2_pass_metrics.assert_called_once()
    finalizer._persist_stage2_pass_cost_record.assert_called_once_with(global_arc_no=2)
    finalizer._maybe_generate_stage2_volume_summaries.assert_called_once_with(global_arc_no=2)
    assert finalizer.ctx.cumulative_state_cache is None
    assert finalizer.ctx.cumulative_state_cache_key is None


def test_run_stage2_pass_with_fix_loop_shell_routes_success_branch(finalizer):
    loop_state = {
        "current_arc": {"patched": True},
        "current_audit": {"decision": "PASS"},
        "fix_ok": True,
        "patch_pressure_exceeded": False,
        "re_score": 95,
    }
    finalizer._execute_stage2_pass_fix_iterations = MagicMock(return_value=loop_state)
    finalizer._finalize_stage2_pass_fix_success = MagicMock(return_value={"decision": "PASS", "score": 95})
    finalizer._finalize_stage2_pass_fix_reject = MagicMock(return_value={"decision": "REJECT", "score": 70})

    result = finalizer._run_stage2_pass_with_fix_loop(
        refined_arc={"arc_no": 1},
        audit={"decision": "PASS_WITH_FIX"},
        expanded_prev_context="prev",
        enriched_block={},
        protagonist_name="hero",
        suspected_duplicates=[],
        entity_registry_for_director={},
        story_context="story",
        global_arc_no=1,
        score=88,
    )

    assert result == {"decision": "PASS", "score": 95}
    finalizer._execute_stage2_pass_fix_iterations.assert_called_once()
    finalizer._finalize_stage2_pass_fix_success.assert_called_once_with(
        refined_arc={"arc_no": 1},
        current_arc={"patched": True},
        current_audit={"decision": "PASS"},
        re_score=95,
    )
    finalizer._finalize_stage2_pass_fix_reject.assert_not_called()


def test_run_stage2_pass_with_fix_loop_shell_routes_reject_branch(finalizer):
    loop_state = {
        "current_arc": {"patched": False},
        "current_audit": {"decision": "REJECT"},
        "fix_ok": False,
        "patch_pressure_exceeded": True,
        "re_score": 77,
    }
    finalizer._execute_stage2_pass_fix_iterations = MagicMock(return_value=loop_state)
    finalizer._finalize_stage2_pass_fix_success = MagicMock(return_value={"decision": "PASS", "score": 95})
    finalizer._finalize_stage2_pass_fix_reject = MagicMock(return_value={"decision": "REJECT", "score": 77})

    result = finalizer._run_stage2_pass_with_fix_loop(
        refined_arc={"arc_no": 2},
        audit={"decision": "PASS_WITH_FIX"},
        expanded_prev_context="prev",
        enriched_block={},
        protagonist_name="hero",
        suspected_duplicates=[],
        entity_registry_for_director={},
        story_context="story",
        global_arc_no=2,
        score=82,
    )

    assert result == {"decision": "REJECT", "score": 77}
    finalizer._finalize_stage2_pass_fix_success.assert_not_called()
    finalizer._finalize_stage2_pass_fix_reject.assert_called_once_with(
        refined_arc={"arc_no": 2},
        current_arc={"patched": False},
        current_audit={"decision": "REJECT"},
        audit={"decision": "PASS_WITH_FIX"},
        score=82,
        max_fix=3,
    )
