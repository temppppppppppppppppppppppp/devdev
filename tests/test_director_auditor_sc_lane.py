from unittest.mock import MagicMock

from modules.domain.agents.director_auditor import DirectorQualityAuditor


def _make_director():
    director = MagicMock()
    director.ambiguous_lower = 40
    director.ambiguous_upper = 80
    director.consistency_votes = 3
    director._last_thinking = "first-pass thinking"
    return director


def test_maybe_finalize_clear_strategic_audit_reject_sets_sc_metadata():
    auditor = DirectorQualityAuditor(_make_director())
    first_eval = {"decision": "REJECT", "score": 20, "reason": "bad"}

    result = auditor._maybe_finalize_clear_strategic_audit(
        first_eval=first_eval,
        first_decision="REJECT",
        first_score=20,
        first_thinking="reject-thinking",
    )

    assert result["self_consistency"]["reason"] == "clear_reject"
    assert result["self_consistency"]["pass_votes"] == 0
    assert result["_director_thinking"] == "reject-thinking"


def test_build_strategic_sc_result_merges_votes_and_logs():
    director = _make_director()
    auditor = DirectorQualityAuditor(director)
    representative = {"decision": "PASS", "score": 61, "reason": "ok"}

    result = auditor._build_strategic_sc_result(
        representative=representative,
        final_decision="PASS_WITH_FIX",
        median_score=63,
        evaluations=[
            {"decision": "PASS", "score": 61},
            {"decision": "PASS_WITH_FIX", "score": 63},
            {"decision": "REJECT", "score": 40},
        ],
        pass_votes=2,
        scores=[61, 63, 40],
        first_decision="PASS",
        first_score=61,
    )

    assert result["decision"] == "PASS_WITH_FIX"
    assert result["score"] == 63
    assert result["self_consistency"]["votes"] == 3
    assert result["self_consistency"]["pass_votes"] == 2
    director._operator_log.assert_called_once()


def test_strategic_audit_with_self_consistency_shell_aggregates_parallel_votes(monkeypatch):
    director = _make_director()
    director.ask.return_value = '{"decision": "PASS", "score": 60, "reason": "ok"}'
    director._extract_json_robust.return_value = {"decision": "PASS", "score": 60, "reason": "ok"}
    auditor = DirectorQualityAuditor(director)

    def _fake_collect(*, vote_tasks, vote_task, first_eval, arc_no):
        assert len(vote_tasks) == 2
        assert callable(vote_task)
        assert arc_no == 7
        return [
            first_eval,
            {"decision": "PASS_WITH_FIX", "score": 62, "reason": "fix"},
            {"decision": "REJECT", "score": 58, "reason": "concern"},
        ]

    monkeypatch.setattr(auditor, "_collect_strategic_sc_parallel_votes", _fake_collect)

    result = auditor._strategic_audit_with_self_consistency("prompt", arc_no=7)

    assert result["decision"] == "PASS_WITH_FIX"
    assert result["score"] == 60
    assert result["self_consistency"]["votes"] == 3
    assert result["_director_thinking"] == "first-pass thinking"
