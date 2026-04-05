import logging
from unittest.mock import MagicMock

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


def test_llm_validate_preserves_tail_context():
    validator = _make_validator()
    validator.min_chars_per_ep = 300
    validator._generate_prev_summary = MagicMock(return_value="PREV")
    validator._format_python_result = MagicMock(return_value="PYTHON")
    validator._operator_log = MagicMock()
    captured = {}

    def _ask(prompt, **_kwargs):
        captured["prompt"] = prompt
        return {
            "verdict": "PASS",
            "issues": [],
            "contradictions": [],
            "summary": "ok",
            "confidence": 0.9,
        }

    validator.ask = MagicMock(side_effect=_ask)
    validator._extract_json_robust = MagicMock(
        return_value={
            "verdict": "PASS",
            "issues": [],
            "contradictions": [],
            "summary": "ok",
            "confidence": 0.9,
        }
    )

    result = validator._llm_validate(
        arc={"payload": "A" * 20000, "tail": "TAIL-UAV-ARC"},
        prev_arcs=[{"arc_no": 1}],
        constraints="HEAD-CONSTRAINT\n" + ("C" * 10000) + "\nTAIL-UAV-CONSTRAINT",
        python_result={"issues": [], "has_critical": False, "critical_summary": ""},
    )

    assert result["verdict"] == "PASS"
    assert "TAIL-UAV-ARC" in captured["prompt"]
    assert "TAIL-UAV-CONSTRAINT" in captured["prompt"]
    assert "...(" in captured["prompt"]


def test_validator_flags_episode_details_coverage_gap_as_major():
    validator = _make_validator()

    issues = validator._check_episode_details_contract(
        {
            "ep_count": 3,
            "episode_details": [{"ep_num": 1, "details": ["mission beat"]}],
        }
    )

    assert any(issue["severity"] == "MAJOR" for issue in issues)
    assert any("episode_details mission packet coverage" in issue["issue"] for issue in issues)


def test_validator_flags_end_state_and_joint_docs_mismatch_as_major():
    validator = _make_validator()

    issues = validator._check_state_contract_alignment(
        {
            "joint_docs": {"final_location": "Yeouido Office", "physical_inventory": ["BlackBerry", "memo"]},
            "state_constraints": {
                "arc_end_state": {"location": "Gangnam HQ", "equipment": ["BlackBerry", "contract"]}
            },
        }
    )

    assert any(issue["severity"] == "MAJOR" for issue in issues)
    assert any("final_location / arc_end_state.location mismatch" in issue["issue"] for issue in issues)
    assert any("physical_inventory / arc_end_state.equipment mismatch" in issue["issue"] for issue in issues)
