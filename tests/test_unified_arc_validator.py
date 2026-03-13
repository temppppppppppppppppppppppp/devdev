import logging

from modules.domain.agents.unified_arc_validator import UnifiedArcValidator


def _make_validator() -> UnifiedArcValidator:
    return UnifiedArcValidator.__new__(UnifiedArcValidator)


def test_dead_npc_check_skips_without_prev_arcs(caplog):
    validator = _make_validator()

    with caplog.at_level(logging.INFO):
        issues = validator._check_dead_npc({"arc_no": 1, "tactical_doc": "text"}, state_tracker=None, prev_arcs=[])

    assert issues == []
    assert "no previous arcs" in caplog.text
    assert "state_tracker missing with previous arcs" not in caplog.text


def test_dead_npc_check_warns_only_when_tracker_missing_with_history(caplog):
    validator = _make_validator()

    with caplog.at_level(logging.WARNING):
        issues = validator._check_dead_npc({"arc_no": 2, "tactical_doc": "text"}, state_tracker=None, prev_arcs=[{}])

    assert issues == []
    assert "state_tracker missing with previous arcs" in caplog.text
