import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from modules.core.stage2_orchestrator import Stage2Orchestrator


def _make_ctx():
    ui = MagicMock()
    ui.log = MagicMock()
    return SimpleNamespace(
        ui=ui,
        agents={},
        sys=SimpleNamespace(),
        stage_rejection_history=[],
        current_project=SimpleNamespace(name="proj"),
    )


def _make_setup(**overrides):
    setup = {
        "arc_drive": {"drive": "arc"},
        "cached_preflight_injection": "inject",
        "cached_preflight_result": {"timeline": []},
        "passed": False,
        "current_feedback": "seed-feedback",
        "constraint_block": "base-constraint",
        "attempt": 0,
        "max_attempts": 3,
        "director_feedback_for_fourphase": "seed-director",
        "st_snapshot": {"seed": True},
    }
    setup.update(overrides)
    return setup


def _make_attempt_kwargs(**overrides):
    kwargs = {
        "global_arc_no": 2,
        "attempt": 0,
        "max_attempts": 3,
        "setup": _make_setup(),
        "enriched_block": {"content": {"context": "ctx"}},
        "all_refined_arcs": [],
        "current_vol_strategy": {"vol_no": 1, "strategy_doc": "vol"},
        "protagonist_name": "hero",
        "bible_root": {"root": True},
        "constraint_db": MagicMock(),
        "genre": "fantasy",
        "last_refined_context": "last-context",
        "current_ep_start": 5,
        "current_feedback": "current-feedback",
        "director_feedback_for_fourphase": "director-feedback",
        "st_snapshot": {"snap": 1},
        "previous_attempt": {"score": 70},
    }
    kwargs.update(overrides)
    return kwargs


def _make_design_kwargs(**overrides):
    kwargs = {
        "source_arc_idx": 1,
        "enriched_block": {"content": {"context": "ctx"}},
        "batch_start": 0,
        "batch_end": 2,
        "all_refined_arcs": [],
        "arcs_source": [{"arc_no": 1}],
        "volumes_strategy": [{"vol_no": 1, "strategy_doc": "vol"}],
        "protagonist_name": "hero",
        "grand_obj": "goal",
        "bible_root": {"root": True},
        "constraint_db": MagicMock(),
        "genre": "fantasy",
        "last_refined_context": "initial-context",
        "current_ep_start": 4,
    }
    kwargs.update(overrides)
    return kwargs


def test_run_stage2_single_arc_attempt_retries_before_validation():
    orch = Stage2Orchestrator(app=MagicMock(), context=_make_ctx())
    orch._augment_stage2_feedback_from_rejections = MagicMock(return_value="augmented-feedback")
    orch._log_stage2_four_phase_retry = MagicMock(return_value=True)
    orch._preflight = SimpleNamespace(
        _preflight_arc_analysis=MagicMock(
            return_value={
                "refined_arc": {"draft": "analysis"},
                "generation_method": "analyst",
                "constraint_block": "analysis-constraint",
                "entity_registry_for_director": {"npc": "seed"},
            }
        ),
        _preflight_enrichment=MagicMock(
            return_value={
                "four_phase_passed": False,
                "refined_arc": {"draft": "enriched"},
                "generation_method": "fourphase",
                "draft_validator_passed": False,
                "consensus_passed": False,
                "st_snapshot": {"snap": 2},
                "director_feedback_for_fourphase": "fourphase-feedback",
                "was_patch": False,
                "patch_fallback": False,
                "prev_score": 0,
            }
        ),
    )
    orch._validation_pipeline = SimpleNamespace(run_validation=MagicMock())
    orch._finalizer = SimpleNamespace(run_finalize=AsyncMock())

    result = asyncio.run(orch._run_stage2_single_arc_attempt(**_make_attempt_kwargs(previous_attempt=None)))

    assert result["action"] == "retry"
    assert result["next_attempt"] == 1
    assert result["current_feedback"] == "augmented-feedback"
    assert result["director_feedback_for_fourphase"] == "fourphase-feedback"
    assert result["refined_arc"] == {"draft": "enriched"}
    orch._validation_pipeline.run_validation.assert_not_called()
    orch._finalizer.run_finalize.assert_not_awaited()
    assert orch._preflight._preflight_arc_analysis.call_args.kwargs["cached_preflight_injection"] == "inject"


def test_run_stage2_single_arc_attempt_finalizes_with_transition_state():
    orch = Stage2Orchestrator(app=MagicMock(), context=_make_ctx())
    orch._augment_stage2_feedback_from_rejections = MagicMock(return_value="augmented-feedback")
    orch._log_stage2_four_phase_retry = MagicMock(return_value=False)
    orch._apply_stage2_validation_advisories = MagicMock(return_value="merged-constraint")
    orch._handle_stage2_finalize_transition = MagicMock(
        return_value={
            "action": "break",
            "last_refined_context": "transition-context",
            "current_ep_start": 8,
            "current_feedback": "transition-feedback",
            "director_feedback_for_fourphase": "transition-director",
            "st_snapshot": {"transition": True},
            "previous_attempt": {"score": 81},
        }
    )
    orch._apply_stage2_finalize_transition_state = MagicMock(
        return_value={
            "action": "break",
            "last_refined_context": "state-context",
            "current_ep_start": 9,
            "current_feedback": "state-feedback",
            "director_feedback_for_fourphase": "state-director",
            "st_snapshot": {"state": True},
            "previous_attempt": {"score": 82},
        }
    )
    orch._preflight = SimpleNamespace(
        _preflight_arc_analysis=MagicMock(
            return_value={
                "refined_arc": {"draft": "analysis"},
                "generation_method": "analyst",
                "constraint_block": "analysis-constraint",
                "entity_registry_for_director": {"npc": "seed"},
            }
        ),
        _preflight_enrichment=MagicMock(
            return_value={
                "four_phase_passed": True,
                "refined_arc": {"draft": "enriched"},
                "generation_method": "fourphase",
                "draft_validator_passed": True,
                "consensus_passed": False,
                "st_snapshot": {"snap": 2},
                "director_feedback_for_fourphase": "fourphase-feedback",
                "was_patch": True,
                "patch_fallback": True,
                "prev_score": 88,
            }
        ),
    )
    orch._validation_pipeline = SimpleNamespace(
        run_validation=MagicMock(
            return_value={
                "action": "next",
                "refined_arc": {"draft": "validated"},
                "draft_validator_passed": True,
                "consensus_passed": True,
                "suspected_duplicates": ["dup"],
                "corrections_made": ["fix-one"],
                "python_advisories": [{"source": "flow", "severity": "warn", "message": "msg"}],
            }
        )
    )
    orch._finalizer = SimpleNamespace(run_finalize=AsyncMock(return_value={"action": "break"}))

    result = asyncio.run(orch._run_stage2_single_arc_attempt(**_make_attempt_kwargs()))

    assert result == {
        "action": "break",
        "next_attempt": 0,
        "current_feedback": "state-feedback",
        "director_feedback_for_fourphase": "state-director",
        "st_snapshot": {"state": True},
        "last_refined_context": "state-context",
        "current_ep_start": 9,
        "previous_attempt": {"score": 82},
        "refined_arc": {"draft": "validated"},
    }
    orch._apply_stage2_validation_advisories.assert_called_once_with(
        constraint_block="analysis-constraint",
        corrections_made=["fix-one"],
        python_advisories=[{"source": "flow", "severity": "warn", "message": "msg"}],
    )
    finalize_kwargs = orch._finalizer.run_finalize.await_args.kwargs
    assert finalize_kwargs["constraint_block"] == "merged-constraint"
    assert finalize_kwargs["is_patch"] is True
    assert finalize_kwargs["prev_score"] == 88
    assert finalize_kwargs["patch_fallback"] is True


def test_run_stage2_single_arc_design_threads_attempt_state_between_calls():
    orch = Stage2Orchestrator(app=MagicMock(), context=_make_ctx())
    orch._resolve_stage2_current_vol_strategy = MagicMock(return_value={"vol_no": 1, "strategy_doc": "vol"})
    orch._prepare_stage2_single_arc_state = MagicMock(
        return_value=_make_setup(
            attempt=0,
            max_attempts=2,
            current_feedback="seed-feedback",
            director_feedback_for_fourphase="seed-director",
            st_snapshot={"seed": 1},
        )
    )
    orch._run_stage2_single_arc_attempt = AsyncMock(
        side_effect=[
            {
                "action": "retry",
                "next_attempt": 1,
                "current_feedback": "retry-feedback",
                "director_feedback_for_fourphase": "retry-director",
                "st_snapshot": {"snap": 2},
                "last_refined_context": "ctx-1",
                "current_ep_start": 6,
                "previous_attempt": {"score": 81},
                "refined_arc": {"draft": "retry"},
            },
            {
                "action": "break",
                "next_attempt": 1,
                "current_feedback": "break-feedback",
                "director_feedback_for_fourphase": "break-director",
                "st_snapshot": {"snap": 3},
                "last_refined_context": "ctx-2",
                "current_ep_start": 7,
                "previous_attempt": {"score": 82},
                "refined_arc": {"draft": "pass"},
            },
        ]
    )
    orch._handle_stage2_single_arc_failure = AsyncMock()

    result = asyncio.run(orch._run_stage2_single_arc_design(**_make_design_kwargs()))

    assert result == {"action": "next", "current_ep_start": 7, "last_refined_context": "ctx-2"}
    assert orch._run_stage2_single_arc_attempt.await_count == 2
    second_call = orch._run_stage2_single_arc_attempt.await_args_list[1].kwargs
    assert second_call["attempt"] == 1
    assert second_call["current_feedback"] == "retry-feedback"
    assert second_call["director_feedback_for_fourphase"] == "retry-director"
    assert second_call["st_snapshot"] == {"snap": 2}
    assert second_call["previous_attempt"] == {"score": 81}
    assert second_call["last_refined_context"] == "ctx-1"
    assert second_call["current_ep_start"] == 6
    orch._handle_stage2_single_arc_failure.assert_not_awaited()


def test_handle_stage2_finalize_transition_logs_attempt_key_for_arc_design():
    ctx = _make_ctx()
    ctx.current_project.metrics_session_id = "sess_stage2"
    ctx.session_logger = MagicMock()
    orch = Stage2Orchestrator(app=MagicMock(), context=ctx)

    orch._handle_stage2_finalize_transition(
        fin={
            "action": "break",
            "score": 96,
            "fix_scope": "inplace",
            "current_feedback": "ok",
            "director_feedback_for_fourphase": "ok",
            "st_snapshot": {"seed": True},
            "last_refined_context": "ctx",
        },
        global_arc_no=2,
        attempt=0,
        last_refined_context="ctx",
        current_ep_start=4,
        current_feedback="seed-feedback",
        director_feedback_for_fourphase="seed-director",
        st_snapshot={"seed": True},
    )

    log_kw = ctx.session_logger.log_decision.call_args.kwargs
    assert log_kw["decision_type"] == "arc_design"
    assert log_kw["ep_num"] == 2
    assert log_kw["round_num"] == 1
    assert log_kw["result"] == "PASS"
    assert log_kw["score"] == 96
    assert log_kw["fix_scope"] == "inplace"
    assert log_kw["attempt_key"] == "s2:ep2:arc2:a1:sess_stage2"


def test_handle_stage2_finalize_transition_logs_retry_for_non_break_arc_design():
    ctx = _make_ctx()
    ctx.current_project.metrics_session_id = "sess_stage2"
    ctx.session_logger = MagicMock()
    orch = Stage2Orchestrator(app=MagicMock(), context=ctx)

    orch._handle_stage2_finalize_transition(
        fin={
            "action": "retry",
            "score": 41,
            "fix_scope": "rewrite",
            "current_feedback": "retry-feedback",
            "director_feedback_for_fourphase": "retry-director",
            "st_snapshot": {"seed": True},
            "last_refined_context": "ctx",
        },
        global_arc_no=3,
        attempt=1,
        last_refined_context="ctx",
        current_ep_start=9,
        current_feedback="seed-feedback",
        director_feedback_for_fourphase="seed-director",
        st_snapshot={"seed": True},
    )

    log_kw = ctx.session_logger.log_decision.call_args.kwargs
    assert log_kw["decision_type"] == "arc_design"
    assert log_kw["ep_num"] == 3
    assert log_kw["round_num"] == 2
    assert log_kw["result"] == "RETRY"
    assert log_kw["score"] == 41
    assert log_kw["fix_scope"] == "rewrite"
    assert log_kw["attempt_key"] == "s2:ep3:arc3:a2:sess_stage2"
