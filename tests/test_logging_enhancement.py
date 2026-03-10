"""[Log-Enhancement] Logging enhancement tests."""

import json
import os
import tempfile

import pytest


@pytest.fixture
def tmp_db():
    from modules.core.db_manager import DBManager

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name

    db = DBManager(path)
    db.initialize_db()
    yield db
    db.conn.close()
    os.unlink(path)


def test_llm_calls_table_exists(tmp_db):
    tables = [
        r[0]
        for r in tmp_db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    ]
    assert "llm_calls" in tables


def test_save_llm_call_success(tmp_db):
    tmp_db.save_llm_call(
        agent_name="director",
        model="gemini-2.5-pro",
        prompt_chars=5000,
        response_chars=800,
        duration_ms=1200,
        success=True,
        stage=4,
        ep_num=3,
        verdict="PASS",
    )
    rows = tmp_db.conn.execute("SELECT * FROM llm_calls").fetchall()
    assert len(rows) == 1
    assert rows[0]["agent_name"] == "director"
    assert rows[0]["success"] == 1
    assert rows[0]["verdict"] == "PASS"


def test_save_llm_call_failure(tmp_db):
    tmp_db.save_llm_call(
        agent_name="analyst",
        model="gemini-2.0-flash",
        prompt_chars=3000,
        response_chars=0,
        duration_ms=500,
        success=False,
        error_type="ConnectionError",
        error_msg="network error",
    )
    rows = tmp_db.conn.execute("SELECT * FROM llm_calls WHERE success=0").fetchall()
    assert len(rows) == 1
    assert rows[0]["error_type"] == "ConnectionError"


def test_save_llm_call_noncritical(tmp_db):
    tmp_db.conn.close()
    tmp_db.save_llm_call(
        agent_name="writer",
        model="gemini-2.5-pro",
        prompt_chars=1000,
        response_chars=500,
        duration_ms=800,
    )


def test_stage_attempts_table_exists(tmp_db):
    tables = [
        r[0]
        for r in tmp_db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    ]
    assert "stage_attempts" in tables


def test_save_stage_attempt(tmp_db):
    tmp_db.save_stage_attempt(
        stage=4,
        verdict="REJECT",
        attempt_num=2,
        ep_num=5,
        arc_num=2,
        score=72,
        failure_category="CONTINUITY",
        reject_reason="continuity broken",
        advisory_flags={"truth_gate": 1, "npc_drift": 0},
        prompt_version="chief_writer@v1|director@v1",
    )
    rows = tmp_db.conn.execute("SELECT * FROM stage_attempts").fetchall()
    assert len(rows) == 1
    assert rows[0]["verdict"] == "REJECT"
    assert rows[0]["prompt_version"] == "chief_writer@v1|director@v1"
    flags = json.loads(rows[0]["advisory_flags"])
    assert flags["truth_gate"] == 1


def test_failure_analyzer_summary(tmp_db):
    from modules.core.failure_analyzer import FailureAnalyzer

    fa = FailureAnalyzer(tmp_db)
    result = fa.summary()
    assert isinstance(result, dict)


def test_failure_analyzer_empty_db(tmp_db):
    from modules.core.failure_analyzer import FailureAnalyzer

    fa = FailureAnalyzer(tmp_db)
    assert fa.stage_pass_rates() == {}
    assert fa.most_failed_agents() == []
    assert fa.advisory_reject_correlation() == {}
    assert fa.model_performance() == {}


def test_advisory_reject_correlation(tmp_db):
    from modules.core.failure_analyzer import FailureAnalyzer

    tmp_db.conn.execute(
        """INSERT INTO director_selections
           (ep_num, round_num, selected_label, selected_strategy, verdict, score,
            selection_reason, candidate_count, fix_scope, advisory_warnings)
           VALUES (1,0,'A','balanced','REJECT',60,'reason',3,'full',?)""",
        (json.dumps({"truth_gate": 1}),),
    )
    tmp_db.conn.execute(
        """INSERT INTO director_selections
           (ep_num, round_num, selected_label, selected_strategy, verdict, score,
            selection_reason, candidate_count, fix_scope, advisory_warnings)
           VALUES (2,0,'B','balanced','PASS',90,'reason',3,NULL,?)""",
        (json.dumps({"truth_gate": 0}),),
    )
    tmp_db.conn.commit()

    fa = FailureAnalyzer(tmp_db)
    corr = fa.advisory_reject_correlation()
    assert "truth_gate" in corr
    assert corr["truth_gate"]["triggered_count"] == 1
    assert corr["truth_gate"]["reject_rate_when_triggered_pct"] == 100.0
