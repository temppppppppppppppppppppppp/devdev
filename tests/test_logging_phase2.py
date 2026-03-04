"""[Log-Phase2] Failure snippet persistence and analyzer query tests."""

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


def test_llm_calls_has_snippet_columns(tmp_db):
    cols = [r[1] for r in tmp_db.conn.execute("PRAGMA table_info(llm_calls)").fetchall()]
    assert "prompt_snippet" in cols
    assert "response_snippet" in cols


def test_save_llm_call_failure_with_snippet(tmp_db):
    long_prompt = "A" * 5000
    tmp_db.save_llm_call(
        agent_name="director",
        model="gemini-2.5-pro",
        prompt_chars=5000,
        response_chars=50,
        duration_ms=800,
        success=False,
        error_type="JSONDecodeError",
        error_msg="parse failure",
        prompt_snippet=long_prompt,
        response_snippet="malformed json response",
    )
    row = tmp_db.conn.execute("SELECT prompt_snippet, response_snippet FROM llm_calls WHERE success=0").fetchone()
    assert row is not None
    assert len(row["prompt_snippet"]) == 3000
    assert row["response_snippet"] == "malformed json response"


def test_save_llm_call_success_no_snippet(tmp_db):
    tmp_db.save_llm_call(
        agent_name="analyst",
        model="gemini-2.0-flash",
        prompt_chars=3000,
        response_chars=500,
        duration_ms=600,
        success=True,
        prompt_snippet="must not persist",
        response_snippet="must not persist",
    )
    row = tmp_db.conn.execute("SELECT prompt_snippet, response_snippet FROM llm_calls WHERE success=1").fetchone()
    assert row is not None
    assert row["prompt_snippet"] is None
    assert row["response_snippet"] is None


def test_save_llm_call_failure_no_snippet_provided(tmp_db):
    tmp_db.save_llm_call(
        agent_name="writer",
        model="gemini-2.5-pro",
        prompt_chars=2000,
        response_chars=0,
        duration_ms=500,
        success=False,
        error_type="TimeoutError",
    )
    row = tmp_db.conn.execute("SELECT prompt_snippet, response_snippet FROM llm_calls WHERE success=0").fetchone()
    assert row is not None
    assert row["prompt_snippet"] is None
    assert row["response_snippet"] is None


def test_save_llm_call_snippet_noncritical(tmp_db):
    tmp_db.conn.close()
    tmp_db.save_llm_call(
        agent_name="writer",
        model="gemini-2.5-pro",
        prompt_chars=1000,
        response_chars=500,
        duration_ms=800,
        success=False,
        prompt_snippet="test",
        response_snippet="test",
    )


def test_failure_analyzer_failed_call_snippets(tmp_db):
    from modules.core.failure_analyzer import FailureAnalyzer

    tmp_db.save_llm_call(
        agent_name="director",
        model="gemini-2.5-pro",
        prompt_chars=5000,
        response_chars=50,
        duration_ms=800,
        success=False,
        error_type="JSONDecodeError",
        prompt_snippet="prompt snippet",
        response_snippet="broken response",
    )
    fa = FailureAnalyzer(tmp_db)
    results = fa.failed_call_snippets()
    assert len(results) == 1
    assert results[0]["prompt_snippet"] == "prompt snippet"
    assert results[0]["response_snippet"] == "broken response"


def test_failure_analyzer_failed_call_snippets_by_agent(tmp_db):
    from modules.core.failure_analyzer import FailureAnalyzer

    tmp_db.save_llm_call(
        agent_name="director",
        model="m",
        prompt_chars=100,
        response_chars=0,
        duration_ms=100,
        success=False,
        prompt_snippet="dir prompt",
    )
    tmp_db.save_llm_call(
        agent_name="analyst",
        model="m",
        prompt_chars=100,
        response_chars=0,
        duration_ms=100,
        success=False,
        prompt_snippet="ana prompt",
    )
    fa = FailureAnalyzer(tmp_db)
    results = fa.failed_call_snippets(agent_name="director")
    assert len(results) == 1
    assert results[0]["agent_name"] == "director"


def test_failure_analyzer_failure_prompt_patterns(tmp_db):
    from modules.core.failure_analyzer import FailureAnalyzer

    for i in range(3):
        tmp_db.save_llm_call(
            agent_name="director",
            model="m",
            prompt_chars=5000 + i * 1000,
            response_chars=0,
            duration_ms=800,
            success=False,
        )
    fa = FailureAnalyzer(tmp_db)
    results = fa.failure_prompt_patterns()
    assert len(results) == 1
    assert results[0]["fail_count"] == 3
    assert results[0]["agent_name"] == "director"


def test_failure_analyzer_snippets_empty_db(tmp_db):
    from modules.core.failure_analyzer import FailureAnalyzer

    fa = FailureAnalyzer(tmp_db)
    assert fa.failed_call_snippets() == []
    assert fa.failure_prompt_patterns() == []
