from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a


def _bind_director_enrichment_helpers(app):
    app._resolve_director_error_category = (
        lambda error_category, reason: main_a.SovereignApp._resolve_director_error_category(
            app,
            error_category,
            reason,
        )
    )
    app._build_director_reject_action_items = (
        lambda **kwargs: main_a.SovereignApp._build_director_reject_action_items(
            app,
            **kwargs,
        )
    )
    app._apply_director_breakdown_feedback = (
        lambda **kwargs: main_a.SovereignApp._apply_director_breakdown_feedback(
            app,
            **kwargs,
        )
    )
    app._apply_director_responsibility_fields = (
        lambda **kwargs: main_a.SovereignApp._apply_director_responsibility_fields(
            app,
            **kwargs,
        )
    )
    app._apply_quantified_director_reject_feedback = (
        lambda **kwargs: main_a.SovereignApp._apply_quantified_director_reject_feedback(
            app,
            **kwargs,
        )
    )
    return app


def test_resolve_director_error_category_defaults_unknown_to_quality_issue():
    app = SimpleNamespace()

    result = main_a.SovereignApp._resolve_director_error_category(
        app,
        "UNKNOWN",
        "plain rejection",
    )

    assert result == "QUALITY_ISSUE"


def test_resolve_director_error_category_preserves_known_category():
    app = SimpleNamespace()

    result = main_a.SovereignApp._resolve_director_error_category(
        app,
        "LOGIC_ERROR",
        "plain rejection",
    )

    assert result == "LOGIC_ERROR"


def test_build_director_reject_action_items_adds_length_guardrail():
    app = SimpleNamespace()
    content_length = main_a.ManuscriptLimits.MIN_LENGTH - 10

    items = main_a.SovereignApp._build_director_reject_action_items(
        app,
        decision="REJECT",
        error_category="QUALITY_ISSUE",
        reason="",
        stage=4,
        content_length=content_length,
    )

    assert len(items) == 1
    assert items[0]["type"] == "QUALITY_ISSUE"
    assert items[0]["severity"] == "CRITICAL"
    assert str(content_length) in items[0]["description"]


def test_build_director_reject_action_items_adds_logic_fallback():
    app = SimpleNamespace()

    items = main_a.SovereignApp._build_director_reject_action_items(
        app,
        decision="REJECT",
        error_category="LOGIC_ERROR",
        reason="logic mismatch",
        stage=3,
        content_length=0,
    )

    assert len(items) == 1
    assert items[0]["type"] == "LOGIC_ERROR"
    assert items[0]["severity"] == "HIGH"
    assert items[0]["description"] == "logic mismatch"


def test_apply_director_breakdown_feedback_sets_payload_and_filters_severity():
    app = SimpleNamespace(
        _analyze_score_breakdown=MagicMock(
            return_value={
                "scene": {
                    "name": "Scene",
                    "score": 10,
                    "max": 25,
                    "severity": "CRITICAL",
                    "suggestion": "tighten",
                },
                "prose": {
                    "name": "Prose",
                    "score": 11,
                    "max": 15,
                    "severity": "MEDIUM",
                    "suggestion": "polish",
                },
            }
        )
    )
    audit_result = {"decision": "REJECT", "score_breakdown": {"scene": 10}}
    action_items = []

    main_a.SovereignApp._apply_director_breakdown_feedback(
        app,
        audit_result=audit_result,
        action_items=action_items,
    )

    assert "breakdown_feedback" in audit_result
    assert len(action_items) == 1
    assert action_items[0]["type"] == "SCORE_BREAKDOWN"
    assert "10/25" in action_items[0]["description"]


def test_apply_director_responsibility_fields_switches_owner():
    app = SimpleNamespace()
    logic_result = {}
    quality_result = {}

    main_a.SovereignApp._apply_director_responsibility_fields(
        app,
        audit_result=logic_result,
        error_category="LOGIC_ERROR",
    )
    main_a.SovereignApp._apply_director_responsibility_fields(
        app,
        audit_result=quality_result,
        error_category="QUALITY_ISSUE",
    )

    assert logic_result["responsibility"] == "ANALYST"
    assert quality_result["responsibility"] == "WRITER"


def test_apply_quantified_director_reject_feedback_extends_action_items():
    quantified = [{"type": "QUANTIFIED", "severity": "MEDIUM", "suggestion": "expand"}]
    app = SimpleNamespace(_quantify_reject_feedback=MagicMock(return_value=quantified))
    audit_result = {"decision": "REJECT"}
    action_items = [{"type": "BASE"}]

    main_a.SovereignApp._apply_quantified_director_reject_feedback(
        app,
        audit_result=audit_result,
        action_items=action_items,
        reason="too short",
        stage=4,
        content_length=1000,
    )

    assert audit_result["quantified_feedback"] == quantified
    assert action_items[-1] == quantified[0]


def test_enrich_director_result_composes_helper_family():
    app = _bind_director_enrichment_helpers(
        SimpleNamespace(
            _analyze_score_breakdown=MagicMock(return_value={}),
            _quantify_reject_feedback=MagicMock(return_value=[]),
        )
    )
    audit_result = {
        "decision": "REJECT",
        "error_category": "LOGIC_ERROR",
        "reason": "logic mismatch",
    }

    result = main_a.SovereignApp._enrich_director_result(
        app,
        audit_result,
        stage=3,
        content_length=0,
    )

    assert result["error_category"] == "LOGIC_ERROR"
    assert result["responsibility"] == "ANALYST"
    assert result["action_items"][0]["type"] == "LOGIC_ERROR"
