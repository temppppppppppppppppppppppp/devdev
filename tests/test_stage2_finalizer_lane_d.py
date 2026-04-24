import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

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
    ctx.cumulative_state_cache = None
    ctx.cumulative_state_cache_key = None
    ctx.agents = {"director": MagicMock()}
    ctx.pass_rate_monitor = None
    ctx.quality_dashboard = None
    ctx.stage2_optimizer = None
    ctx.stage_rejection_history = []
    ctx.semantic_plot_guard = None
    host = SimpleNamespace(ctx=ctx)
    return Stage2Finalizer(host)


def _make_finalize_kwargs():
    return {
        "refined_arc": {"arc_no": 1, "ep_start": 1, "ep_end": 3, "tactical_doc": "x" * 1600},
        "enriched_block": {"joint_docs": {}, "status_shadow": {}},
        "arc_drive": {"desire_vector": "test"},
        "all_refined_arcs": [],
        "global_arc_no": 1,
        "current_ep_start": 1,
        "current_feedback": "feedback",
        "protagonist_name": "hero",
        "suspected_duplicates": [],
        "entity_registry_for_director": {},
        "constraint_block": "MUST NOT regress",
        "draft_validator_passed": True,
        "consensus_passed": True,
        "attempt": 0,
        "generation_method": "four_phase",
        "st_snapshot": {"foo": 1},
        "director_feedback_for_fourphase": "director-note",
        "last_refined_context": "prev-context",
        "bible_root": {"protagonist_config": {"name": "hero"}},
        "genre": "fantasy",
        "constraint_db": MagicMock(),
        "is_patch": False,
        "prev_score": 88.0,
        "patch_fallback": False,
    }


def test_run_finalize_shell_delegates_pass_branch_to_helper(finalizer):
    audit_state = {
        "cdb_snapshot": {"snap": 1},
        "current_feedback": "feedback+spg",
        "expanded_prev_context": "prev-expanded",
        "story_context": "story",
        "audit": {"decision": "PASS", "score": 95},
        "director_duration_ms": 77,
        "decision": "PASS",
        "score": 95,
        "tactical_doc_len": 1600,
        "quality_gate_score": 90,
    }
    finalizer._prepare_stage2_finalize_audit_state = MagicMock(return_value=audit_state)
    finalizer._handle_stage2_finalize_pass_branch = AsyncMock(return_value={"action": "break"})
    finalizer._run_stage2_pass_with_fix_loop = MagicMock()
    finalizer._handle_stage2_reject_path = MagicMock()

    result = asyncio.run(finalizer.run_finalize(**_make_finalize_kwargs()))

    assert result == {"action": "break"}
    finalizer._prepare_stage2_finalize_audit_state.assert_called_once()
    finalizer._handle_stage2_finalize_pass_branch.assert_awaited_once()
    finalizer._run_stage2_pass_with_fix_loop.assert_not_called()
    finalizer._handle_stage2_reject_path.assert_not_called()


@patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
def test_record_s2_reject_metrics_persists_attempt_and_selection_records(finalizer, tmp_path):
    finalizer.ctx.current_project.paths = MagicMock()
    finalizer.ctx.current_project.paths.root = tmp_path
    finalizer.ctx.current_project.metrics_session_id = "sess_stage2_lane_d"

    finalizer._record_s2_reject_metrics(
        global_arc_no=4,
        attempt=1,
        generation_method="analyst",
        selected_strategy="creative",
        audit={
            "decision": "REJECT",
            "score": 42,
            "reason": "bad structure",
            "re_slice_instruction": "장면 순서를 재배치",
        },
        artifact_payload={"arc_no": 4, "tactical_doc": "x" * 1200},
    )

    stage_attempt_kw = finalizer.ctx.current_project.db.save_stage_attempt.call_args.kwargs
    selection_kw = finalizer.ctx.current_project.db.save_director_selection.call_args.kwargs

    assert stage_attempt_kw["session_id"] == "sess_stage2_lane_d"
    assert stage_attempt_kw["attempt_key"] == "s2:ep4:arc4:a2:sess_stage2_lane_d"
    assert stage_attempt_kw["candidate_key"] == "creative"
    assert stage_attempt_kw["artifact_path"].endswith("rejected_arc__creative.json")
    assert selection_kw["attempt_key"] == stage_attempt_kw["attempt_key"]
    assert selection_kw["candidate_key"] == "creative"
    assert (tmp_path / stage_attempt_kw["artifact_path"]).exists()


def test_execute_stage2_pass_fix_iterations_delegates_to_helper_family(finalizer):
    current_arc = {"arc_no": 1, "tactical_doc": "draft"}
    current_audit = {"re_slice_instruction": "tighten midpoint"}
    patched_arc = {"arc_no": 1, "tactical_doc": "patched"}
    patch_state = {
        "patch_pressure_exceeded": False,
        "arith_patch_ctx": "[arith ctx]",
        "patch_guard_signals": [{"code": "missing_tactical_doc", "detail": "fixed"}],
    }
    re_state = {
        "audit": {"decision": "PASS", "score": 97},
        "decision": "PASS",
        "score": 97,
    }
    loop_state = {
        "current_arc": patched_arc,
        "current_audit": re_state["audit"],
        "fix_ok": True,
        "re_score": 97,
        "action": "break",
    }
    finalizer._resolve_stage2_pass_fix_instruction = MagicMock(return_value="tighten midpoint")
    finalizer._apply_stage2_pass_fix_patch = MagicMock(return_value=patched_arc)
    finalizer._analyze_stage2_pass_fix_patch = MagicMock(return_value=patch_state)
    finalizer._build_stage2_pass_fix_reaudit_story_context = MagicMock(return_value="story+patch")
    finalizer._run_stage2_pass_fix_reaudit = MagicMock(return_value=re_state)
    finalizer._apply_stage2_pass_fix_reaudit_result = MagicMock(return_value=loop_state)

    result = finalizer._execute_stage2_pass_fix_iterations(
        four_phase=MagicMock(),
        current_arc=current_arc,
        current_audit=current_audit,
        expanded_prev_context="prev-context",
        enriched_block={"joint_docs": {}, "status_shadow": {}},
        protagonist_name="hero",
        suspected_duplicates=[],
        entity_registry_for_director={},
        story_context="story",
        global_arc_no=1,
        max_fix=2,
        fix_ok=False,
        applied_patches=[],
        patch_pressure_exceeded=False,
        re_score=91,
    )

    assert result == {
        "current_arc": patched_arc,
        "current_audit": re_state["audit"],
        "fix_ok": True,
        "patch_pressure_exceeded": False,
        "re_score": 97,
    }
    finalizer._resolve_stage2_pass_fix_instruction.assert_called_once_with(
        current_audit=current_audit,
        fix_i=0,
        max_fix=2,
    )
    finalizer._apply_stage2_pass_fix_patch.assert_called_once()
    analyze_kw = finalizer._analyze_stage2_pass_fix_patch.call_args.kwargs
    assert analyze_kw["current_arc"] == current_arc
    assert analyze_kw["current_audit"] == current_audit
    assert analyze_kw["patched"] == patched_arc
    assert analyze_kw["fix_instr"] == "tighten midpoint"
    assert analyze_kw["global_arc_no"] == 1
    assert analyze_kw["fix_i"] == 0
    assert analyze_kw["patch_pressure_exceeded"] is False
    assert analyze_kw["applied_patches"] == ["tighten midpoint"]
    story_kw = finalizer._build_stage2_pass_fix_reaudit_story_context.call_args.kwargs
    assert story_kw["story_context"] == "story"
    assert story_kw["arith_patch_ctx"] == "[arith ctx]"
    assert story_kw["patch_guard_signals"] == patch_state["patch_guard_signals"]
    assert story_kw["patch_pressure_exceeded"] is False
    assert story_kw["current_audit"] == current_audit
    assert story_kw["applied_patches"] == ["tighten midpoint"]
    assert story_kw["fix_i"] == 0
    finalizer._run_stage2_pass_fix_reaudit.assert_called_once()
    finalizer._apply_stage2_pass_fix_reaudit_result.assert_called_once_with(
        patched=patched_arc,
        current_arc=current_arc,
        current_audit=current_audit,
        fix_ok=False,
        re_audit=re_state["audit"],
        re_decision="PASS",
        re_score=97,
    )


def test_execute_stage2_pass_fix_iterations_fail_closes_on_blocking_patch_guard_signal(finalizer):
    current_arc = {"arc_no": 1, "tactical_doc": "draft"}
    current_audit = {"re_slice_instruction": "tighten midpoint", "decision": "PASS_WITH_FIX"}
    patched_arc = {"arc_no": 1, "tactical_doc": "patched"}
    blocking_signal = {
        "code": "episode_start_future_artifact",
        "detail": "제 15화 돌아온 방향타: 최종 매도 체결 확인서 precedes later action '전량 익절 청산'",
    }
    patch_state = {
        "patch_pressure_exceeded": False,
        "arith_patch_ctx": "",
        "patch_guard_signals": [blocking_signal],
        "blocking_patch_guard_signals": [blocking_signal],
    }
    finalizer._resolve_stage2_pass_fix_instruction = MagicMock(return_value="tighten midpoint")
    finalizer._apply_stage2_pass_fix_patch = MagicMock(return_value=patched_arc)
    finalizer._analyze_stage2_pass_fix_patch = MagicMock(return_value=patch_state)
    finalizer._build_stage2_pass_fix_reaudit_story_context = MagicMock()
    finalizer._run_stage2_pass_fix_reaudit = MagicMock()
    finalizer._apply_stage2_pass_fix_reaudit_result = MagicMock()

    result = finalizer._execute_stage2_pass_fix_iterations(
        four_phase=MagicMock(),
        current_arc=current_arc,
        current_audit=current_audit,
        expanded_prev_context="prev-context",
        enriched_block={"joint_docs": {}, "status_shadow": {}},
        protagonist_name="hero",
        suspected_duplicates=[],
        entity_registry_for_director={},
        story_context="story",
        global_arc_no=1,
        max_fix=2,
        fix_ok=False,
        applied_patches=[],
        patch_pressure_exceeded=False,
        re_score=91,
    )

    assert result == {
        "current_arc": current_arc,
        "current_audit": current_audit,
        "fix_ok": False,
        "patch_pressure_exceeded": False,
        "re_score": 91,
    }
    assert "Do not place an episode-end outcome artifact inside [시작 상태]." in current_audit["re_slice_instruction"]
    assert "episode_start_future_artifact" in current_audit["re_slice_instruction"]
    finalizer._resolve_stage2_pass_fix_instruction.assert_called()
    assert finalizer._resolve_stage2_pass_fix_instruction.call_count == 2
    assert finalizer._apply_stage2_pass_fix_patch.call_count == 2
    finalizer._build_stage2_pass_fix_reaudit_story_context.assert_not_called()
    finalizer._run_stage2_pass_fix_reaudit.assert_not_called()
    finalizer._apply_stage2_pass_fix_reaudit_result.assert_not_called()


def test_legacy_stage2_pass_persistence_tail_delegates_to_existing_helpers(finalizer):
    refined_arc = {
        "arc_no": 3,
        "ep_start": 11,
        "ep_end": 13,
        "tactical_doc": "x" * 1600,
        "_ensemble_meta": {"best_strategy": "cohesive"},
    }
    audit = {"decision": "PASS", "score": 93}
    finalizer._update_stage2_pass_constraint_db = MagicMock()
    finalizer._advance_stage2_pass_persistence_state = MagicMock(
        return_value={"last_refined_context": "next-context", "current_ep_start": 14}
    )
    finalizer._record_s2_pass_metrics = MagicMock()
    finalizer._persist_stage2_pass_cost_record = MagicMock()
    finalizer._maybe_generate_stage2_volume_summaries = MagicMock()

    result = asyncio.run(
        finalizer._legacy_stage2_pass_persistence_and_tail_body(
            refined_arc=refined_arc,
            all_refined_arcs=[{"arc_no": 1}, {"arc_no": 2}],
            global_arc_no=3,
            current_feedback="feedback",
            st_snapshot={"foo": 1},
            cdb_snapshot={"bar": 2},
            constraint_db=MagicMock(),
            last_refined_context="prev-context",
            current_ep_start=11,
            director_feedback_for_fourphase="director-note",
            attempt=2,
            generation_method="four_phase",
            audit=audit,
            director_duration_ms=88,
            is_patch=False,
            prev_score=91.0,
            patch_fallback=False,
        )
    )

    assert result == {
        "action": "break",
        "last_refined_context": "next-context",
        "current_ep_start": 14,
        "current_feedback": "feedback",
        "director_feedback_for_fourphase": "director-note",
        "st_snapshot": {"foo": 1},
        "score": 93,
        "fix_scope": "",
    }
    finalizer._update_stage2_pass_constraint_db.assert_called_once()
    finalizer._advance_stage2_pass_persistence_state.assert_called_once_with(
        refined_arc=refined_arc,
        all_refined_arcs=[{"arc_no": 1}, {"arc_no": 2}],
        global_arc_no=3,
        last_refined_context="prev-context",
    )
    finalizer._record_s2_pass_metrics.assert_called_once_with(
        global_arc_no=3,
        attempt=2,
        generation_method="four_phase",
        selected_strategy="cohesive",
        audit=audit,
        duration_ms=88,
        is_patch=False,
        prev_score=91.0,
        patch_fallback=False,
        artifact_payload=refined_arc,
    )
    finalizer._persist_stage2_pass_cost_record.assert_called_once_with(global_arc_no=3)
    finalizer._maybe_generate_stage2_volume_summaries.assert_called_once_with(global_arc_no=3)
