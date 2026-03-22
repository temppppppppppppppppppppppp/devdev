from unittest.mock import MagicMock

from modules.core.stage2_orchestrator import Stage2Orchestrator


def test_validate_draft_or_fail_closed_returns_synthetic_reject_on_crash():
    orchestrator = Stage2Orchestrator(app=MagicMock())
    ctx = MagicMock()
    ctx.state_tracker = None
    ctx.arc_draft_validator = MagicMock()
    ctx.arc_draft_validator.validate.side_effect = RuntimeError("validator blew up")
    orchestrator._ctx = ctx

    result = orchestrator.validation_pipeline._validate_draft_or_fail_closed(
        refined_arc={"arc_no": 1},
        all_refined_arcs=[],
        constraint_block="rules",
    )

    assert result["valid"] is False
    assert result["score"] == 0
    assert result["advisory_issues"] == []
    assert result["warnings"] == []
    assert "DraftValidator crash:" in result["critical_issues"][0]
