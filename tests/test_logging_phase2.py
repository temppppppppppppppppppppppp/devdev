"""[Log-Phase2] Failure snippet persistence and analyzer query tests."""

import logging
import os
import sqlite3
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
    assert len(row["prompt_snippet"]) == 5000
    assert row["response_snippet"] == "malformed json response"


def test_save_llm_call_failure_persists_full_error_msg(tmp_db):
    long_error = "traceback:" + ("X" * 512)
    tmp_db.save_llm_call(
        agent_name="director",
        model="gemini-2.5-pro",
        prompt_chars=100,
        response_chars=0,
        duration_ms=800,
        success=False,
        error_type="RuntimeError",
        error_msg=long_error,
    )

    row = tmp_db.conn.execute("SELECT error_msg FROM llm_calls WHERE error_type='RuntimeError'").fetchone()

    assert row is not None
    assert row["error_msg"] == long_error


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


# ── [TF-60] 터미널 5 로깅 보완 테스트 ─────────────────────────────────────────

def test_llm_calls_has_thinking_snippet_column(tmp_db):
    """이슈 8: llm_calls 테이블에 thinking_snippet 컬럼 존재."""
    cols = [r[1] for r in tmp_db.conn.execute("PRAGMA table_info(llm_calls)").fetchall()]
    assert "thinking_snippet" in cols


def test_save_llm_call_thinking_snippet(tmp_db):
    """이슈 8: save_llm_call()에 thinking_snippet 전달 시 저장됨."""
    tmp_db.save_llm_call(
        agent_name="director",
        model="gemini-2.5-pro",
        prompt_chars=1000,
        response_chars=200,
        duration_ms=500,
        success=True,
        thinking_snippet="director thinking content here",
    )
    row = tmp_db.conn.execute("SELECT thinking_snippet FROM llm_calls WHERE agent_name='director'").fetchone()
    assert row is not None
    assert row["thinking_snippet"] == "director thinking content here"


def test_stage_attempts_has_generation_method_column(tmp_db):
    """이슈 10: stage_attempts 테이블에 generation_method 컬럼 존재."""
    cols = [r[1] for r in tmp_db.conn.execute("PRAGMA table_info(stage_attempts)").fetchall()]
    assert "generation_method" in cols
    assert "prompt_version" in cols


def test_save_stage_attempt_generation_method(tmp_db):
    """이슈 10: save_stage_attempt()에 generation_method 전달 시 저장됨."""
    tmp_db.save_stage_attempt(
        stage=2,
        verdict="PASS",
        attempt_num=1,
        ep_num=3,
        arc_num=3,
        score=85,
        generation_method="four_phase",
        prompt_version="ensemble@v1|director@v1",
    )
    row = tmp_db.conn.execute(
        "SELECT generation_method, prompt_version FROM stage_attempts WHERE stage=2 AND ep_num=3"
    ).fetchone()
    assert row is not None
    assert row["generation_method"] == "four_phase"
    assert row["prompt_version"] == "ensemble@v1|director@v1"


def test_reboot_current_schema_emits_no_duplicate_column_noise(tmp_path, caplog):
    from modules.core.db_manager import DBManager

    db_path = tmp_path / "current_logging.db"
    db = DBManager(db_path)
    db.close()

    with caplog.at_level(logging.DEBUG):
        reopened = DBManager(db_path)
    try:
        messages = [record.getMessage() for record in caplog.records]
        assert not any("llm_calls 컬럼 마이그레이션 스킵" in message for message in messages)
        assert not any("stage_attempts" in message and "마이그레이션 스킵" in message for message in messages)
        assert not any("compatibility migration added columns" in message for message in messages)
    finally:
        reopened.close()


def test_legacy_logging_tables_receive_missing_columns_safely(tmp_path, caplog):
    from modules.core.db_manager import DBManager

    db_path = tmp_path / "legacy_logging.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                ts TEXT NOT NULL,
                stage INTEGER,
                ep_num INTEGER,
                agent_name TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_chars INTEGER,
                response_chars INTEGER,
                duration_ms INTEGER,
                success INTEGER NOT NULL DEFAULT 1,
                error_type TEXT,
                error_msg TEXT,
                verdict TEXT,
                context_tag TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE stage_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                ts TEXT NOT NULL,
                stage INTEGER NOT NULL,
                ep_num INTEGER,
                arc_num INTEGER,
                attempt_num INTEGER NOT NULL DEFAULT 1,
                verdict TEXT NOT NULL,
                score INTEGER,
                failure_category TEXT,
                reject_reason TEXT,
                fix_scope TEXT,
                model TEXT,
                duration_ms INTEGER,
                advisory_flags TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

    with caplog.at_level(logging.INFO):
        db = DBManager(db_path)
    try:
        llm_cols = {row["name"] for row in db.conn.execute("PRAGMA table_info(llm_calls)").fetchall()}
        stage_cols = {row["name"] for row in db.conn.execute("PRAGMA table_info(stage_attempts)").fetchall()}

        assert {"input_tokens", "output_tokens", "thinking_snippet", "total_cost_usd"} <= llm_cols
        assert {
            "generation_method",
            "attempt_key",
            "selection_reason",
            "retry_directives",
            "director_quality_passed",
            "downstream_override_applied",
            "primary_failure_layer",
        } <= stage_cols

        messages = [record.getMessage() for record in caplog.records]
        assert sum("llm_calls compatibility migration added columns" in message for message in messages) == 1
        assert sum("stage_attempts compatibility migration added columns" in message for message in messages) == 1
    finally:
        db.close()
