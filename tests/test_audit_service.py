"""[Phase 4B-1] AuditService 단위 테스트

테스트 게이트: docs/phase4b_test_gate.md Batch 4B-1 (8개)
차단 테스트 7개 + 허용 테스트 1개
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from modules.core.db_manager import DBManager
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

    def test_write_summary_runs_pre_summary_hook_before_proof_digest(self, runtime_audit, tmp_project):
        sentinel = tmp_project.root / "logs" / "pass_rate_monitor.json"

        def _write_sentinel():
            sentinel.parent.mkdir(parents=True, exist_ok=True)
            sentinel.write_text('{"records": []}', encoding="utf-8")

        svc = AuditService(
            runtime_audit=runtime_audit,
            project_paths_fn=lambda: tmp_project,
            ui_log_fn=lambda msg: None,
            before_summary_write_fn=_write_sentinel,
        )
        svc._build_proof_digest = lambda _paths: {"hook_ran": sentinel.exists()}

        svc.audit_event("evt", "msg")
        svc.write_audit_summary("hook_tag")

        summary_path = tmp_project.root / "logs" / "runtime_audit_summary.json"
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        assert data["proof_digest"]["hook_ran"] is True

    def test_write_summary_includes_structured_proof_digest(self, svc, tmp_project, monkeypatch):
        db = DBManager(tmp_project.root / "project_data.db")
        attempt_key = "s4:ep9:arc1:a1:sess_proof"
        artifact_path = "logs/artifacts/stage4/ep_0009/attempt_01/final_manuscript__A_balanced.txt"
        try:
            artifact_file = tmp_project.root / artifact_path
            artifact_file.parent.mkdir(parents=True, exist_ok=True)
            artifact_file.write_text("artifact", encoding="utf-8")
            (tmp_project.root / "logs" / "session").mkdir(parents=True, exist_ok=True)
            (tmp_project.root / "logs" / "session" / "ui_events.jsonl").write_text(
                json.dumps(
                    {
                        "session_id": "sess_proof",
                        "seq": 1,
                        "component": "UI",
                        "stage": 4,
                        "ep_num": 9,
                        "attempt_key": attempt_key,
                        "message": "visible operator event",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            db.save_stage_attempt(
                stage=4,
                verdict="PASS",
                attempt_num=1,
                ep_num=9,
                arc_num=1,
                score=98,
                session_id="sess_proof",
                attempt_key=attempt_key,
                candidate_key="A|balanced",
                content_hash="hash-proof",
                artifact_path=artifact_path,
            )
            db.save_ui_event(
                session_id="sess_proof",
                seq=1,
                stage=4,
                ep_num=9,
                attempt_key=attempt_key,
                component="UI",
                message="visible operator event",
            )
            db.save_director_selection(
                ep_num=9,
                round_num=1,
                selected_label="A",
                selected_strategy="balanced",
                verdict="PASS",
                score=98,
                stage=4,
                attempt_key=attempt_key,
                candidate_key="A|balanced",
                content_hash="hash-proof",
                artifact_path=artifact_path,
            )
            (tmp_project.root / "logs" / "session" / "decisions.jsonl").write_text(
                json.dumps(
                    {
                        "stage": "stage4",
                        "ep_num": 9,
                        "result": "PASS",
                        "score": 98,
                        "meta": {
                            "attempt_key": attempt_key,
                            "candidate_key": "A|balanced",
                            "content_hash": "hash-proof",
                            "artifact_path": artifact_path,
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            (tmp_project.root / "logs" / "pass_rate_monitor.json").write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "stage": 4,
                                "episode": 9,
                                "arc": 1,
                                "attempt_num": 1,
                                "success": True,
                                "attempt_key": attempt_key,
                                "final_verdict": "PASS",
                                "candidate_key": "A|balanced",
                                "content_hash": "hash-proof",
                                "artifact_path": artifact_path,
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (tmp_project.root / "logs" / "episode_production.jsonl").write_text(
                json.dumps(
                    {
                        "ep": 9,
                        "attempt_key": attempt_key,
                        "verdict": "PASS",
                        "initial_verdict": "PASS",
                        "final_verdict": "PASS",
                        "final_score": 98,
                        "candidate_key": "A|balanced",
                        "selection_candidate_key": "A|balanced",
                        "content_hash": "hash-proof",
                        "artifact_path": artifact_path,
                        "patch_trace": {"patch_strategy": "", "structural_attempted": False},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            from modules.core import db_manager as db_manager_module

            class _ExplodingDBManager:
                def __init__(self, *_args, **_kwargs):
                    raise AssertionError("proof digest must not re-enter DBManager boot")

            monkeypatch.setattr(db_manager_module, "DBManager", _ExplodingDBManager)

            svc.audit_event("evt", "msg")
            svc.write_audit_summary("proof_tag")

            summary_path = tmp_project.root / "logs" / "runtime_audit_summary.json"
            data = json.loads(summary_path.read_text(encoding="utf-8"))

            assert data["summary_role"] == "runtime_heartbeat_with_proof_digest"
            assert data["contract"]["summary_scope"] == "runtime_heartbeat_plus_compact_proof_digest"
            assert data["contract"]["attempt_truth_authoritative"] is False
            assert data["contract"]["proof_digest_truth_scope"] == "committed_persistence_only"
            assert "stage_attempts" in data["contract"]["authoritative_attempt_sinks"]
            assert "session_decisions" in data["contract"]["authoritative_attempt_sinks"]
            assert data["proof_digest"]["available"] is True
            assert data["proof_digest"]["status"] == "ok"
            assert data["proof_digest"]["artifacts"]["ui_events_jsonl_exists"] is True
            assert data["proof_digest"]["artifacts"]["ui_events_db_available"] is True
            assert data["proof_digest"]["artifacts"]["ui_events_count"] == 1
            assert data["proof_digest"]["artifacts"]["ui_event_coverage_status"] == "ok"
            assert data["proof_digest"]["stages"]["stage4"]["status"] == "ok"
            assert data["proof_digest"]["stages"]["stage4"]["coverage"]["session_decisions"] == 1
        finally:
            db.close()

    def test_write_summary_surfaces_rationale_mismatch_issue_counts(self, svc, tmp_project):
        db = DBManager(tmp_project.root / "project_data.db")
        attempt_key = "s3:ep12:arc1:a1:sess_warn"
        artifact_path = "logs/artifacts/stage3/ep_0012/attempt_01/final_blueprint__dialogue_focused.json"
        try:
            artifact_file = tmp_project.root / artifact_path
            artifact_file.parent.mkdir(parents=True, exist_ok=True)
            artifact_file.write_text("{}", encoding="utf-8")
            (tmp_project.root / "logs" / "session").mkdir(parents=True, exist_ok=True)

            db.save_stage_attempt(
                stage=3,
                verdict="PASS",
                attempt_num=1,
                ep_num=12,
                arc_num=1,
                score=93,
                session_id="sess_warn",
                attempt_key=attempt_key,
                candidate_key="dialogue_focused",
                content_hash="hash-stage3",
                artifact_path=artifact_path,
            )
            db.save_director_selection(
                ep_num=12,
                round_num=1,
                selected_label="B",
                selected_strategy="dialogue_focused",
                verdict="PASS",
                score=93,
                selection_reason="candidate B is the most stable choice",
                fix_scope="inplace",
                stage=3,
                verdict_reason="ready to use without structural risk",
                attempt_key=attempt_key,
                candidate_key="dialogue_focused",
                content_hash="hash-stage3",
                artifact_path=artifact_path,
            )
            (tmp_project.root / "logs" / "session" / "decisions.jsonl").write_text(
                json.dumps(
                    {
                        "stage": "stage3",
                        "ep_num": 12,
                        "result": "PASS",
                        "score": 93,
                        "meta": {
                            "attempt_key": attempt_key,
                            "candidate_key": "dialogue_focused",
                            "content_hash": "hash-stage3",
                            "artifact_path": artifact_path,
                            "reason": "different verdict rationale",
                            "selection_reason": "different selection rationale",
                            "verdict_reason": "different verdict rationale",
                            "fix_scope": "full",
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            (tmp_project.root / "logs" / "pass_rate_monitor.json").write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "stage": 3,
                                "episode": 12,
                                "arc": 1,
                                "attempt_num": 1,
                                "success": True,
                                "attempt_key": attempt_key,
                                "final_verdict": "PASS",
                                "candidate_key": "dialogue_focused",
                                "content_hash": "hash-stage3",
                                "artifact_path": artifact_path,
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            svc.audit_event("evt", "msg")
            svc.write_audit_summary("warn_tag")

            summary_path = tmp_project.root / "logs" / "runtime_audit_summary.json"
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            stage3 = data["proof_digest"]["stages"]["stage3"]

            assert data["proof_digest"]["status"] == "warn"
            assert stage3["status"] == "warn"
            assert stage3["issue_counts"]["selection_reason_mismatches"] == 1
            assert stage3["issue_counts"]["verdict_reason_mismatches"] == 1
            assert stage3["issue_counts"]["fix_scope_mismatches"] == 1
        finally:
            db.close()


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
