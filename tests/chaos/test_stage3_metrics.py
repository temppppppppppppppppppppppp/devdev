"""[P7-06] Stage3Orchestrator QualityDashboard recording tests.

Verifies that the P6-02 patch causes _handle_success and _handle_failure
to call quality_dashboard.record_validation(stage=3, ...) with the correct
decision string, and that a None quality_dashboard does not crash.

All orchestrator dependencies (app, ctx, project, DB) are mocked so these
tests run instantly without I/O.
"""

from unittest.mock import MagicMock

from modules.core.stage3_orchestrator import Stage3Orchestrator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ctx(*, ui=None, project=None) -> MagicMock:
    """Build a minimal Stage3Context mock."""
    ctx = MagicMock()
    ctx.ui = ui or MagicMock()
    ctx.current_project = project or MagicMock()
    # Callbacks used in _handle_success/_handle_failure
    ctx.validate_blueprint_integrity = MagicMock(return_value=True)
    ctx.safe_commit = MagicMock(return_value=True)
    ctx.audit_event = MagicMock()
    return ctx


def _make_orch(quality_dashboard=None) -> Stage3Orchestrator:
    """Build a Stage3Orchestrator with a mocked app."""
    app = MagicMock()
    app.quality_dashboard = quality_dashboard
    orch = Stage3Orchestrator(app=app)
    # Inject ctx directly so from_app is never called
    orch._ctx = _make_ctx(project=app.current_project)
    return orch


def _pass_pipeline_result(score: float = 0.85) -> dict:
    return {
        "final_verdict": "PASS",
        "quality_gate_failed": False,
        "quality_risk": False,
        "last_score": score,
        "phases": {"generate": {"selected_score": score, "selected_strategy": "ensemble"}},
    }


def _fail_pipeline_result() -> dict:
    return {
        "final_verdict": "REJECT",
        "quality_gate_failed": True,
        "quality_risk": True,
        "last_score": 0,
        "phases": {},
    }


# ---------------------------------------------------------------------------
# Test 1: _handle_success() calls record_validation(stage=3, decision="PASS")
# ---------------------------------------------------------------------------


def test_handle_success_calls_record_validation_pass():
    qd = MagicMock()
    orch = _make_orch(quality_dashboard=qd)

    blueprint = {"ep_num": 3, "title": "테스트"}
    prev_blueprints = []
    pipeline_result = _pass_pipeline_result(score=0.9)

    orch._handle_success(
        working_ep=3,
        arc_no=1,
        arc_data={},
        blueprint=blueprint,
        pipeline_result=pipeline_result,
        prev_blueprints=prev_blueprints,
        success_count=0,
        fail_count=0,
    )

    assert qd.record_validation.called, "quality_dashboard.record_validation must be called on PASS"
    call_args, call_kwargs = qd.record_validation.call_args
    # Check keyword arguments
    assert call_kwargs.get("stage") == 3 or (len(call_args) >= 3 and call_args[2] == 3), (
        "record_validation must be called with stage=3"
    )
    result_arg = call_kwargs.get("result") or (call_args[1] if len(call_args) > 1 else None)
    assert result_arg is not None
    assert result_arg.get("decision") == "PASS"


# ---------------------------------------------------------------------------
# Test 2: _handle_failure() calls record_validation(stage=3, decision="REJECT")
# ---------------------------------------------------------------------------


def test_handle_failure_calls_record_validation_reject():
    qd = MagicMock()
    orch = _make_orch(quality_dashboard=qd)

    pipeline_result = _fail_pipeline_result()

    orch._handle_failure(
        working_ep=3,
        pipeline_result=pipeline_result,
        success_count=0,
        fail_count=0,
    )

    assert qd.record_validation.called, "quality_dashboard.record_validation must be called on REJECT"
    call_args, call_kwargs = qd.record_validation.call_args
    assert call_kwargs.get("stage") == 3 or (len(call_args) >= 3 and call_args[2] == 3), (
        "record_validation must be called with stage=3"
    )
    result_arg = call_kwargs.get("result") or (call_args[1] if len(call_args) > 1 else None)
    assert result_arg is not None
    assert result_arg.get("decision") == "REJECT"


# ---------------------------------------------------------------------------
# Test 3: quality_dashboard=None — _handle_success() does not crash
# ---------------------------------------------------------------------------


def test_handle_success_none_quality_dashboard_does_not_crash():
    orch = _make_orch(quality_dashboard=None)
    blueprint = {"ep_num": 5, "title": "테스트2"}
    prev_blueprints = []

    # Should not raise AttributeError or any other exception
    result = orch._handle_success(
        working_ep=5,
        arc_no=2,
        arc_data={},
        blueprint=blueprint,
        pipeline_result=_pass_pipeline_result(),
        prev_blueprints=prev_blueprints,
        success_count=1,
        fail_count=0,
    )
    assert isinstance(result, dict)
    assert "next_ep" in result


# ---------------------------------------------------------------------------
# Test 4: quality_dashboard=None — _handle_failure() does not crash
# ---------------------------------------------------------------------------


def test_handle_failure_none_quality_dashboard_does_not_crash():
    orch = _make_orch(quality_dashboard=None)

    result = orch._handle_failure(
        working_ep=5,
        pipeline_result=_fail_pipeline_result(),
        success_count=0,
        fail_count=1,
    )
    assert isinstance(result, dict)
    assert result.get("break") is True
