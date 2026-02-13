"""[Phase 4B-1] AuditService 단위 테스트

테스트 게이트: docs/phase4b_test_gate.md Batch 4B-1 (8개)
차단 테스트 7개 + 허용 테스트 1개
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from modules.core.services.audit_service import AuditService

# ── Fixture ──────────────────────────────────────────────────────


@pytest.fixture
def runtime_audit():
    return []


@pytest.fixture
def tmp_project(tmp_path):
    paths = MagicMock()
    paths.root = tmp_path
    return paths


@pytest.fixture
def svc(runtime_audit, tmp_project):
    return AuditService(
        runtime_audit=runtime_audit,
        project_paths_fn=lambda: tmp_project,
        ui_log_fn=lambda msg: None,
    )


# ── 차단 테스트 (7개) ────────────────────────────────────────────


class TestAuditEvent:
    def test_audit_event_appends_to_buffer(self, svc):
        svc.audit_event("test_type", "test_msg", {"key": "val"})
        assert len(svc.buffer) == 1
        assert svc.buffer[0]["type"] == "test_type"
        assert svc.buffer[0]["message"] == "test_msg"
        assert svc.buffer[0]["data"] == {"key": "val"}

    def test_audit_event_appends_to_runtime_audit(self, svc, runtime_audit):
        svc.audit_event("info", "hello")
        assert len(runtime_audit) == 1
        assert runtime_audit[0]["type"] == "info"
        assert runtime_audit[0]["message"] == "hello"
        assert runtime_audit[0]["data"] == {}


class TestFlushAuditBuffer:
    def test_flush_writes_jsonl_file(self, svc, tmp_project):
        svc.audit_event("a", "msg1")
        svc.audit_event("b", "msg2")
        svc.flush_audit_buffer()

        log_path = tmp_project.root / "logs" / "runtime_audit.jsonl"
        assert log_path.exists()
        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        parsed = json.loads(lines[0])
        assert parsed["type"] == "a"

    def test_flush_clears_buffer(self, svc):
        svc.audit_event("x", "y")
        assert len(svc.buffer) == 1
        svc.flush_audit_buffer()
        assert len(svc.buffer) == 0


class TestWriteAuditSummary:
    def test_write_summary_calls_flush_first(self, svc, tmp_project):
        svc.audit_event("evt", "msg")
        svc.write_audit_summary("test_tag")
        assert len(svc.buffer) == 0
        log_path = tmp_project.root / "logs" / "runtime_audit.jsonl"
        assert log_path.exists()

    def test_write_summary_creates_json_file(self, svc, tmp_project):
        svc.audit_event("evt", "msg")
        svc.write_audit_summary("my_tag")

        summary_path = tmp_project.root / "logs" / "runtime_audit_summary.json"
        assert summary_path.exists()
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        assert data["tag"] == "my_tag"
        assert data["total_events"] == 1
        assert "evt" in data["counts"]


class TestFacadeStub:
    def test_facade_stub_delegates_correctly(self):
        runtime = []
        paths = MagicMock()
        paths.root = Path(tempfile.mkdtemp())
        svc = AuditService(
            runtime_audit=runtime,
            project_paths_fn=lambda: paths,
            ui_log_fn=lambda msg: None,
        )
        svc.audit_event("delegate_test", "msg", {"k": 1})
        assert len(runtime) == 1
        assert runtime[0]["type"] == "delegate_test"

        svc.flush_audit_buffer()
        assert len(svc.buffer) == 0
        assert (paths.root / "logs" / "runtime_audit.jsonl").exists()

        svc.write_audit_summary("facade_tag")
        assert (paths.root / "logs" / "runtime_audit_summary.json").exists()


# ── 허용 테스트 (1개) ────────────────────────────────────────────


class TestEdgeCases:
    def test_flush_no_project_skips(self):
        runtime = []
        svc = AuditService(
            runtime_audit=runtime,
            project_paths_fn=lambda: None,
            ui_log_fn=lambda msg: None,
        )
        svc.audit_event("evt", "msg")
        svc.flush_audit_buffer()
        assert len(svc.buffer) == 1
