"""Regression tests for ArcDraftValidator grant timeline checks."""

from modules.domain.agents.arc_draft_validator import ArcDraftValidator


def test_validate_grant_timeline_detects_duplicate_from_state_constraints():
    validator = ArcDraftValidator()

    prev_arcs = [
        {
            "state_constraints": {"grants_received": ["철혈사자패"]},
            "tactical_doc": "",
        }
    ]
    arc = {
        "state_constraints": {"grants_received": ["철혈사자패"]},
        "tactical_doc": "",
    }

    result = validator._validate_grant_timeline(arc, prev_arcs)

    assert result["penalty"] >= 25
    assert any("철혈사자패" in msg and "state_constraints" in msg for msg in result["critical"])
