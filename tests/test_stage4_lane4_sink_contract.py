"""Lane 4 regression tests: sink-contract-normalization.

Covers two contracts:

  [Lane4-S1] save_stage_attempt and save_ui_event must use local cursor
             (self.conn.cursor() inside with self._lock:), not shared self.cursor.
             Enforces INF-P1-1 rule for authoritative telemetry sink writes.

  [Lane4-S2] All episode_production.jsonl writers must use the authoritative
             episode key "ep" — never "ep_num".
             Confirmed consumer contract: stagewise_manuscript_truth_report,
             failure_analyzer both read row.get("ep").

Happy-path regression:
  - save_stage_attempt writes a record that can be read back.
  - save_ui_event writes a record that can be read back.
  - CoVe runtime advisory sink uses "ep" key.
  - Retry pathology sink uses "ep" key.
"""

import ast
import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
DB_MANAGER_PATH = ROOT / "modules/core/db_manager.py"
OUTCOME_RUNTIME_PATH = ROOT / "modules/core/stage4_outcome_runtime.py"
SHARED_PATTERN = re.compile(r"self\.cursor\.(execute|executemany|fetchone|fetchall)")


# ── source-level contract tests ───────────────────────────────────────────────

def _method_texts() -> dict[str, str]:
    source = DB_MANAGER_PATH.read_text(encoding="utf-8")
    lines = source.splitlines()
    module = ast.parse(source)
    methods: dict[str, str] = {}
    for node in ast.walk(module):
        if not isinstance(node, ast.FunctionDef):
            continue
        end_lineno = getattr(node, "end_lineno", node.lineno)
        methods[node.name] = "\n".join(lines[node.lineno - 1 : end_lineno])
    return methods


def test_save_stage_attempt_uses_local_cursor():
    """[Lane4-S1a] save_stage_attempt must NOT use self.cursor after migration."""
    methods = _method_texts()
    assert "save_stage_attempt" in methods
    text = methods["save_stage_attempt"]
    assert not SHARED_PATTERN.search(text), (
        "save_stage_attempt still uses self.cursor.execute — must use local cursor per INF-P1-1"
    )
    assert "self.conn.cursor()" in text, (
        "save_stage_attempt must create a local cursor via self.conn.cursor()"
    )


def test_save_ui_event_uses_local_cursor():
    """[Lane4-S1b] save_ui_event must NOT use self.cursor after migration."""
    methods = _method_texts()
    assert "save_ui_event" in methods
    text = methods["save_ui_event"]
    assert not SHARED_PATTERN.search(text), (
        "save_ui_event still uses self.cursor.execute — must use local cursor per INF-P1-1"
    )
    assert "self.conn.cursor()" in text, (
        "save_ui_event must create a local cursor via self.conn.cursor()"
    )


# ── episode key contract tests (source-level) ─────────────────────────────────

def test_cove_advisory_writer_uses_ep_key():
    """[Lane4-S2a] _log_cove_runtime_advisory payload must use 'ep' not 'ep_num'."""
    source = OUTCOME_RUNTIME_PATH.read_text(encoding="utf-8")
    lines = source.splitlines()
    module = ast.parse(source)

    cove_method_text = None
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef) and node.name == "_log_cove_runtime_advisory":
            end_lineno = getattr(node, "end_lineno", node.lineno)
            cove_method_text = "\n".join(lines[node.lineno - 1 : end_lineno])
            break

    assert cove_method_text is not None, "_log_cove_runtime_advisory not found"
    # Normalize: no bare "ep_num" as a dict key string literal in the payload
    assert '"ep_num"' not in cove_method_text, (
        "_log_cove_runtime_advisory payload still uses 'ep_num' key — must use 'ep'"
    )
    assert '"ep"' in cove_method_text, (
        "_log_cove_runtime_advisory payload must contain 'ep' key"
    )


def test_retry_pathology_writer_uses_ep_key():
    """[Lane4-S2b] build_retry_pathology_payload must use 'ep' not 'ep_num'."""
    source = OUTCOME_RUNTIME_PATH.read_text(encoding="utf-8")
    lines = source.splitlines()
    module = ast.parse(source)

    method_text = None
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef) and node.name == "build_retry_pathology_payload":
            end_lineno = getattr(node, "end_lineno", node.lineno)
            method_text = "\n".join(lines[node.lineno - 1 : end_lineno])
            break

    assert method_text is not None, "build_retry_pathology_payload not found"
    assert '"ep_num"' not in method_text, (
        "build_retry_pathology_payload still uses 'ep_num' key — must use 'ep'"
    )
    assert '"ep"' in method_text, (
        "build_retry_pathology_payload payload must contain 'ep' key"
    )


# ── runtime regression tests ──────────────────────────────────────────────────

@pytest.fixture
def db(tmp_path):
    from modules.core.db_manager import DBManager

    db_inst = DBManager(tmp_path / "test_sink.db")
    yield db_inst
    db_inst.close()


def test_save_stage_attempt_sink_roundtrip(db):
    """[Lane4-S1a-rt] save_stage_attempt writes and is readable via DB query."""
    written = db.save_stage_attempt(
        stage=4,
        verdict="PASS",
        ep_num=7,
        arc_num=2,
        attempt_num=1,
        score=85,
        session_id="test_session",
    )
    assert written is True
    rows = db.get_stage_attempts_for_arc(arc_num=2, stages=(4,))
    assert rows, "No stage attempt rows written for arc=2"
    assert rows[0]["verdict"] == "PASS"
    assert rows[0]["score"] == 85


def test_save_ui_event_sink_roundtrip(db):
    """[Lane4-S1b-rt] save_ui_event writes and does not raise."""
    written = db.save_ui_event(
        session_id="test_session",
        ep_num=7,
        arc_num=2,
        round_num=0,
        component="Stage4",
        event_kind="verdict",
        level="info",
        message="PASS with score 85",
    )
    assert written is True


def test_cove_advisory_sink_ep_key_in_record(tmp_path):
    """[Lane4-S2a-rt] CoVe advisory sink record uses 'ep' not 'ep_num'."""
    from modules.core.stage4_outcome_runtime import Stage4OutcomeRuntime

    ctx = MagicMock()
    ctx.current_project = MagicMock()
    ctx.current_project.name = "test_lane4"
    ctx.audit_event = None

    owner = MagicMock()
    owner.ctx = ctx

    runtime = Stage4OutcomeRuntime.__new__(Stage4OutcomeRuntime)
    runtime.owner = owner

    logs_dir = tmp_path / "test_lane4" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    with patch(
        "modules.core.stage4_outcome_runtime.resolve_project_log_dir",
        return_value=logs_dir,
    ):
        runtime._log_cove_runtime_advisory(
            ep_num=5,
            round_num=2,
            source="llm_verify",
            error=ValueError("test error"),
            quick_warning="advisory",
        )

    log_path = logs_dir / "episode_production.jsonl"
    assert log_path.exists()
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    advisory = [r for r in rows if r.get("event") == "STAGE4_COVE_RUNTIME_ADVISORY"]
    assert advisory, "No STAGE4_COVE_RUNTIME_ADVISORY record written"
    assert "ep" in advisory[-1], "STAGE4_COVE_RUNTIME_ADVISORY record missing 'ep' key"
    assert "ep_num" not in advisory[-1], "STAGE4_COVE_RUNTIME_ADVISORY record has drifted 'ep_num' key"
    assert advisory[-1]["ep"] == 5


def test_retry_pathology_sink_ep_key_in_record(tmp_path):
    """[Lane4-S2b-rt] Retry pathology sink record uses 'ep' not 'ep_num'."""
    from modules.core.stage4_outcome_runtime import Stage4OutcomeRuntime

    ctx = MagicMock()
    ctx.current_project = MagicMock()
    ctx.current_project.name = "test_lane4_pathology"
    ctx.audit_event = None

    owner = MagicMock()
    owner.ctx = ctx

    runtime = Stage4OutcomeRuntime.__new__(Stage4OutcomeRuntime)
    runtime.owner = owner

    logs_dir = tmp_path / "test_lane4_pathology" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    with patch(
        "modules.core.stage4_outcome_runtime.resolve_project_log_dir",
        return_value=logs_dir,
    ):
        runtime.emit_retry_pathology_signal(
            ep_num=3,
            round_num=1,
            previous_attempt={"reject_bucket": "numeric_conflict", "retry_pathology_source": "post_select_conflict"},
            pathology_counts={},
            pathology_repeat_emitted=set(),
        )

    log_path = logs_dir / "episode_production.jsonl"
    assert log_path.exists()
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    pathology = [r for r in rows if r.get("event") == "STAGE4_RETRY_PATHOLOGY"]
    assert pathology, "No STAGE4_RETRY_PATHOLOGY record written"
    assert "ep" in pathology[-1], "STAGE4_RETRY_PATHOLOGY record missing 'ep' key"
    assert "ep_num" not in pathology[-1], "STAGE4_RETRY_PATHOLOGY record has drifted 'ep_num' key"
    assert pathology[-1]["ep"] == 3
