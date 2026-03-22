from unittest.mock import MagicMock

import pytest

from modules.core.stage2_orchestrator import Stage2Orchestrator


@pytest.fixture
def pipeline():
    app = MagicMock()
    orchestrator = Stage2Orchestrator(app=app)

    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.audit_event = MagicMock()
    ctx.state_tracker = None
    ctx.arc_draft_validator = None
    ctx.arc_corrector = None
    ctx.use_arc_corrector = False
    ctx.agents = {}

    orchestrator._ctx = ctx
    return orchestrator.validation_pipeline


def test_run_draft_validator_full_sets_pass_flag_on_valid_result(pipeline):
    refined_arc = {"arc_no": 1, "tactical_doc": "alpha"}
    pipeline.ctx.arc_draft_validator = MagicMock()
    pipeline.ctx.arc_draft_validator.validate.return_value = {
        "valid": True,
        "score": 88,
        "advisory_issues": [],
        "critical_issues": [],
        "warnings": ["minor issue"],
    }

    result = pipeline._run_draft_validator_full(
        refined_arc=refined_arc,
        four_phase_passed=False,
        all_refined_arcs=[],
        constraint_block="",
        global_arc_no=7,
        draft_validator_passed=False,
        _python_advisories=[],
        _auto_corrections=[],
    )

    assert result["refined_arc"] == refined_arc
    assert result["draft_validator_passed"] is True


def test_run_draft_validator_full_appends_failure_advisory_when_critical_issue_present(pipeline):
    pipeline.ctx.arc_draft_validator = MagicMock()
    pipeline.ctx.arc_draft_validator.validate.return_value = {
        "valid": False,
        "score": 41,
        "advisory_issues": [],
        "critical_issues": ["missing causal chain"],
        "warnings": ["soft warning"],
    }
    advisories = []

    result = pipeline._run_draft_validator_full(
        refined_arc={"arc_no": 2},
        four_phase_passed=False,
        all_refined_arcs=[],
        constraint_block="block",
        global_arc_no=2,
        draft_validator_passed=False,
        _python_advisories=advisories,
        _auto_corrections=[],
    )

    assert result["draft_validator_passed"] is False
    assert advisories[-1]["source"] == "draft_validator"
    assert "missing causal chain" in advisories[-1]["message"]
    pipeline.ctx.audit_event.assert_any_call(
        "draft_validation_reject",
        "draft validation failed",
        {"arc_no": 2, "score": 41, "critical_count": 1},
    )


def test_run_draft_validator_full_uses_arc_corrector_for_warning_only_failure(pipeline):
    refined_arc = {"arc_no": 3, "tactical_doc": "before"}
    corrected_arc = {"arc_no": 3, "tactical_doc": "after"}
    pipeline.ctx.arc_draft_validator = MagicMock()
    pipeline.ctx.arc_draft_validator.validate.side_effect = [
        {
            "valid": False,
            "score": 62,
            "advisory_issues": [],
            "critical_issues": [],
            "warnings": ["tight pacing"],
        },
        {
            "valid": True,
            "score": 85,
            "critical_issues": [],
            "warnings": [],
        },
    ]
    pipeline.ctx.arc_corrector = MagicMock()
    pipeline.ctx.use_arc_corrector = True
    pipeline.ctx.arc_corrector.can_correct.return_value = (True, [{"message": "tight pacing"}], [])
    pipeline.ctx.arc_corrector.correct.return_value = (
        corrected_arc,
        {
            "success": True,
            "corrections_made": [{"change_summary": "tight pacing fixed"}],
            "corrections_failed": [],
        },
    )
    advisories = []
    corrections = []

    result = pipeline._run_draft_validator_full(
        refined_arc=refined_arc,
        four_phase_passed=False,
        all_refined_arcs=[{"arc_no": 2}],
        constraint_block="block",
        global_arc_no=3,
        draft_validator_passed=False,
        _python_advisories=advisories,
        _auto_corrections=corrections,
    )

    assert result["refined_arc"] == corrected_arc
    assert result["draft_validator_passed"] is False
    assert corrections == [{"change_summary": "tight pacing fixed"}]
    assert advisories == []
    pipeline.ctx.audit_event.assert_any_call(
        "arc_corrector_success",
        "arc partially corrected",
        {"arc_no": 3, "corrections": 1, "failed": 0},
    )
