import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

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
    constraint_db = overrides.pop("constraint_db", MagicMock())
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
        "constraint_db": constraint_db,
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


def test_run_stage2_single_arc_attempt_delegates_to_helper_family():
    orch = Stage2Orchestrator(app=MagicMock(), context=_make_ctx())
    kwargs = _make_attempt_kwargs()
    preflight_state = {
        "current_feedback": "augmented-feedback",
        "refined_arc": {"draft": "enriched"},
        "generation_method": "fourphase",
        "constraint_block": "analysis-constraint",
        "entity_registry_for_director": {"npc": "seed"},
        "four_phase_passed": True,
        "draft_validator_passed": True,
        "consensus_passed": False,
        "st_snapshot": {"snap": 2},
        "director_feedback_for_fourphase": "fourphase-feedback",
        "was_patch": True,
        "patch_fallback": False,
        "prev_score": 88,
    }
    validation_state = {
        "action": "continue",
        "refined_arc": {"draft": "validated"},
        "draft_validator_passed": True,
        "consensus_passed": True,
        "suspected_duplicates": ["dup"],
        "constraint_block": "merged-constraint",
    }
    finalize_payload = {
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
    orch._run_stage2_single_arc_preflight = MagicMock(return_value=preflight_state)
    orch._log_stage2_four_phase_retry = MagicMock(return_value=False)
    orch._run_stage2_single_arc_validation = MagicMock(return_value=validation_state)
    orch._finalize_stage2_single_arc_attempt = AsyncMock(return_value=finalize_payload)

    result = asyncio.run(orch._run_stage2_single_arc_attempt(**kwargs))

    assert result == finalize_payload
    orch._run_stage2_single_arc_preflight.assert_called_once()
    orch._run_stage2_single_arc_validation.assert_called_once_with(
        global_arc_no=2,
        attempt=0,
        refined_arc={"draft": "enriched"},
        four_phase_passed=True,
        all_refined_arcs=[],
        entity_registry_for_director={"npc": "seed"},
        current_ep_start=5,
        current_feedback="augmented-feedback",
        generation_method="fourphase",
        constraint_block="analysis-constraint",
        enriched_block={"content": {"context": "ctx"}},
        draft_validator_passed=True,
        consensus_passed=False,
        protagonist_name="hero",
        constraint_db=kwargs["constraint_db"],
        st_snapshot={"snap": 2},
        last_refined_context="last-context",
        previous_attempt={"score": 70},
    )
    orch._finalize_stage2_single_arc_attempt.assert_awaited_once()


def test_build_stage2_arc_failure_report_context_collects_prev_items_and_constraints():
    ctx = _make_ctx()
    ctx.stage_rejection_history = [
        {"stage": 2, "arc_no": 4, "attempt": 1, "reason": "reject-one"},
        {"stage": 2, "arc_no": 4, "attempt": 2, "reason": "reject-two"},
        {"stage": 4, "arc_no": 4, "attempt": 1, "reason": "ignore"},
    ]
    orch = Stage2Orchestrator(app=MagicMock(), context=ctx)
    constraint_db = MagicMock()
    constraint_db.generate_constraint_block.return_value = "HEAD\n" + ("C" * 7000) + "\nTAIL"

    context = orch._build_stage2_arc_failure_report_context(
        global_arc_no=4,
        all_refined_arcs=[
            {"state_constraints": {"protagonist_items": ["sword"]}},
            {"state_constraints": {"items_acquired": ["map", "seal"]}},
        ],
        constraint_db=constraint_db,
    )

    assert [item["reason"] for item in context["arc_rejects"]] == ["reject-one", "reject-two"]
    assert context["prev_items"] == ["sword", "map", "seal"]
    assert "TAIL" in context["current_constraints"]


def test_handle_stage2_arc_failure_skip_choice_uses_skip_helper(tmp_path):
    ctx = _make_ctx()
    ctx.current_project = SimpleNamespace(
        name="proj",
        paths=SimpleNamespace(root=tmp_path),
    )
    orch = Stage2Orchestrator(app=MagicMock(), context=ctx)
    orch._resolve_stage2_arc_failure_report_path = MagicMock(return_value=tmp_path / "logs" / "arc_2_failure_report.txt")
    orch._build_stage2_arc_failure_report_context = MagicMock(
        return_value={"arc_rejects": [], "current_constraints": "seed", "prev_items": ["sword"]}
    )
    orch._build_stage2_arc_failure_report_lines = MagicMock(return_value=["report"])
    orch._write_stage2_arc_failure_report = AsyncMock()
    orch._log_stage2_arc_failure_summary = MagicMock()
    orch._build_stage2_arc_failure_skip_payload = MagicMock(return_value={"action": "skip", "current_ep_start": 12})

    with patch("builtins.input", return_value="1"):
        result = asyncio.run(
            orch._handle_stage2_arc_failure(
                global_arc_no=2,
                batch_start=0,
                batch_end=2,
                all_refined_arcs=[],
                arcs_source=[{"ep_count": 3}, {"ep_count": 4}],
                constraint_db=MagicMock(),
                refined_arc={"tactical_doc": "draft"},
                current_ep_start=8,
            )
        )

    assert result == {"action": "skip", "current_ep_start": 12}
    orch._build_stage2_arc_failure_skip_payload.assert_called_once_with(
        global_arc_no=2,
        arcs_source=[{"ep_count": 3}, {"ep_count": 4}],
        current_ep_start=8,
    )
