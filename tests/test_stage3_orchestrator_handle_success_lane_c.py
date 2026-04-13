from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.stage3_orchestrator import Stage3Orchestrator


def _build_lane_orchestrator():
    app = MagicMock()
    app.quality_dashboard = MagicMock()
    orch = Stage3Orchestrator(app=app)
    ctx = SimpleNamespace(
        current_project=MagicMock(),
        ui=MagicMock(),
        audit_event=MagicMock(),
        validate_blueprint_integrity=MagicMock(return_value=True),
        safe_commit=MagicMock(return_value=True),
    )
    orch.ctx = ctx
    return orch, app, ctx


def test_lane_c_handle_success_short_circuits_on_persistence_failure():
    orch, _, _ = _build_lane_orchestrator()
    runtime_payload = {"attempt_key": "stage3:ep1:arc1:a1"}
    persistence_failure = {"next_ep": 2, "success_count": 4, "fail_count": 2, "break": True}

    orch._build_stage3_success_runtime_payload = MagicMock(return_value=runtime_payload)
    orch._record_stage3_success_observability = MagicMock()
    orch._annotate_stage3_success_blueprint = MagicMock(return_value={"integrated_scenario": "bp"})
    orch._persist_stage3_success_blueprint = MagicMock(return_value=persistence_failure)
    orch._record_stage3_success_completion = MagicMock()

    result = orch._handle_success(
        1,
        1,
        {"arc_no": 1},
        {"integrated_scenario": "bp"},
        {"final_verdict": "PASS"},
        [],
        4,
        1,
    )

    assert result == persistence_failure
    orch._record_stage3_success_completion.assert_not_called()
    orch._build_stage3_success_runtime_payload.assert_not_called()
    orch._record_stage3_success_observability.assert_not_called()


def test_lane_c_persist_stage3_success_blueprint_returns_break_on_commit_failure():
    orch, _, ctx = _build_lane_orchestrator()
    ctx.safe_commit.return_value = False
    ctx.current_project.save_episode_blueprint = MagicMock()
    prev_blueprints = []

    result = orch._persist_stage3_success_blueprint(
        working_ep=3,
        blueprint={"integrated_scenario": "bp"},
        prev_blueprints=prev_blueprints,
        success_count=2,
        fail_count=1,
    )

    assert result == {"next_ep": 4, "success_count": 2, "fail_count": 2, "break": True}
    assert prev_blueprints == []
    ctx.current_project.save_episode_blueprint.assert_called_once_with(3, {"integrated_scenario": "bp"})
    ctx.audit_event.assert_called_once()


def test_lane_c_record_stage3_success_completion_records_dashboard_warnings():
    orch, app, ctx = _build_lane_orchestrator()

    orch._record_stage3_success_completion(
        working_ep=5,
        arc_no=2,
        blueprint={"_inventory_gaps": [{"item": "법인 통장"}], "_continuity_pin_unresolved": [{"pin": "start"}]},
        pipeline_result={
            "retries": 1,
            "phases": {
                "generate": {"selected_strategy": "lane", "selected_score": 91},
                "validate": {
                    "selected_candidate_advisory": {"issue_count": 6},
                    "binding_prevalidation_issue_count": 2,
                },
            },
        },
        final_verdict="PASS_WITH_FIX",
        quality_gate_failed=True,
        quality_risk=True,
        revision_required=True,
    )

    ctx.audit_event.assert_called_once()
    app.quality_dashboard.record_validation.assert_called_once()
    kwargs = app.quality_dashboard.record_validation.call_args.kwargs
    assert kwargs["ep_num"] == 5
    assert kwargs["stage"] == 3
    assert kwargs["result"]["decision"] == "PASS"
    assert kwargs["result"]["warnings"] == [
        "quality_gate_failed",
        "quality_risk",
        "revision_required",
    ]
    log_texts = [call.args[0] for call in ctx.ui.log.call_args_list if call.args]
    assert any(
        "[Stage3 Summary] ep 5 | verdict=PASS_WITH_FIX | score=91 | attempt=2 | prevalidation=6 | binding=2 | TF-49=1 | PinGuard=1"
        in text
        for text in log_texts
    )
