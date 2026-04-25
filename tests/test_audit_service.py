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
        assert data["summary_window"]["count_window_size"] == 200
        assert data["summary_window"]["counted_events"] == 1
        assert data["summary_window"]["recent_event_window_size"] == 10
        assert data["summary_window"]["recent_events_returned"] == 1
        assert data["summary_window"]["counts_truncated"] is False
        assert data["summary_window"]["event_window_truncated"] is False

    def test_write_summary_discloses_compact_event_windows(self, svc, tmp_project):
        for idx in range(205):
            svc.audit_event("evt", f"msg-{idx}")
        svc.write_audit_summary("window_tag")

        summary_path = tmp_project.root / "logs" / "runtime_audit_summary.json"
        data = json.loads(summary_path.read_text(encoding="utf-8"))

        assert data["total_events"] == 205
        assert data["counts"]["evt"] == 200
        assert data["summary_window"]["counted_events"] == 200
        assert data["summary_window"]["recent_events_returned"] == 10
        assert data["summary_window"]["counts_truncated"] is True
        assert data["summary_window"]["event_window_truncated"] is True

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
        monkeypatch.setenv("GEULDOBI_RUN_ID", "run-proof-123")
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
            for payload_kind in (
                "selection_contract_snapshot_raw",
                "selection_surface_raw",
                "feedback_provenance_raw",
                "contract_snapshot_raw",
            ):
                db.save_attempt_raw_rationale(
                    attempt_key=attempt_key,
                    stage=4,
                    ep_num=9,
                    payload_kind=payload_kind,
                    payload=json.dumps({"_meta": {"surface": payload_kind}}, ensure_ascii=False),
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
            (tmp_project.root / "logs" / "session_legacy_token.log").write_text("session log", encoding="utf-8")
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
            assert data["proof_digest"]["session_lineage"]["plain_log_token"] == "legacy_token"
            assert data["proof_digest"]["session_lineage"]["structured_session_id"] == "sess_proof"
            assert data["proof_digest"]["session_lineage"]["status"] == "split_mapped"
            assert data["run_scope"]["status"] == "scoped"
            assert data["run_scope"]["engine_run_id"] == "run-proof-123"
            assert data["run_scope"]["latest_session_id"] == "sess_proof"
            assert data["freshness"]["status"] == "scoped"
            assert data["freshness"]["engine_run_id_present"] is True
            assert data["freshness"]["latest_session_id_present"] is True
            assert data["freshness"]["operator_guidance_only"] is True
            assert data["proof_digest"]["stages"]["stage4"]["status"] == "ok"
            assert data["proof_digest"]["stages"]["stage4"]["coverage"]["session_decisions"] == 1
            runtime_audit_path = tmp_project.root / "logs" / "runtime_audit.jsonl"
            if runtime_audit_path.exists():
                runtime_audit_text = runtime_audit_path.read_text(encoding="utf-8")
                assert "sink_alignment_final_authority_contract" not in runtime_audit_text
        finally:
            db.close()

    def test_write_summary_proof_digest_surfaces_numeric_consistency_summary(self, svc, tmp_project):
        db = DBManager(tmp_project.root / "project_data.db")
        attempt_key = "s4:ep2:arc1:a1:sess_num"
        artifact_path = "logs/artifacts/stage4/ep_0002/attempt_01/final_manuscript__A_balanced.txt"
        try:
            artifact_file = tmp_project.root / artifact_path
            artifact_file.parent.mkdir(parents=True, exist_ok=True)
            artifact_file.write_text("artifact", encoding="utf-8")
            (tmp_project.root / "logs" / "session").mkdir(parents=True, exist_ok=True)
            (tmp_project.root / "logs" / "session" / "ui_events.jsonl").write_text(
                json.dumps(
                    {
                        "session_id": "sess_num",
                        "seq": 1,
                        "component": "UI",
                        "stage": 4,
                        "ep_num": 2,
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
                verdict="REJECT",
                attempt_num=1,
                ep_num=2,
                arc_num=1,
                score=71,
                session_id="sess_num",
                attempt_key=attempt_key,
                candidate_key="A|balanced",
                content_hash="hash-num",
                artifact_path=artifact_path,
                runtime_advisory=(
                    "[NC-1][후보 A][MAJOR][numeric_carryover_authority] "
                    "[numeric carryover authority mismatch] 원고 '20억 원' (20.0억) vs resumed "
                    "FactLedger 'capital'=2000000000.0억 (EP1 carryover baseline)."
                ),
            )
            db.save_ui_event(
                session_id="sess_num",
                seq=1,
                stage=4,
                ep_num=2,
                attempt_key=attempt_key,
                component="UI",
                message="visible operator event",
            )
            db.save_director_selection(
                ep_num=2,
                round_num=1,
                selected_label="A",
                selected_strategy="balanced",
                verdict="REJECT",
                score=71,
                stage=4,
                attempt_key=attempt_key,
                candidate_key="A|balanced",
                content_hash="hash-num",
                artifact_path=artifact_path,
            )
            (tmp_project.root / "logs" / "session" / "decisions.jsonl").write_text(
                json.dumps(
                    {
                        "stage": "stage4",
                        "ep_num": 2,
                        "result": "REJECT",
                        "score": 71,
                        "meta": {
                            "attempt_key": attempt_key,
                            "candidate_key": "A|balanced",
                            "content_hash": "hash-num",
                            "artifact_path": artifact_path,
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            (tmp_project.root / "logs" / "episode_production.jsonl").write_text(
                json.dumps(
                    {
                        "ep": 2,
                        "attempt_key": attempt_key,
                        "verdict": "REJECT",
                        "initial_verdict": "REJECT",
                        "final_verdict": "REJECT",
                        "final_score": 71,
                        "candidate_key": "A|balanced",
                        "selection_candidate_key": "A|balanced",
                        "content_hash": "hash-num",
                        "artifact_path": artifact_path,
                        "patch_trace": {"patch_strategy": "", "structural_attempted": False},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            svc.audit_event("evt", "msg")
            svc.write_audit_summary("numeric_surface")

            summary_path = tmp_project.root / "logs" / "runtime_audit_summary.json"
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            numeric_summary = data["proof_digest"]["stages"]["stage4"]["numeric_consistency_summary"]

            assert numeric_summary["status"] == "warn"
            assert numeric_summary["signal_count"] == 1
            assert numeric_summary["category_counts"]["numeric_carryover_authority"] == 1
            assert numeric_summary["ledger_field_counts"]["capital"] == 1
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

    def test_compact_sink_alignment_summary_counts_gate_repair_contract_issues(self, svc):
        compact = svc._compact_sink_alignment_summary(
            {
                "status": "warn",
                "attempts_considered": 1,
                "complete_final_attempts": 1,
                "complete_lifecycle_attempts": 1,
                "legacy_key_attempts": 0,
                "session_scoped_attempts": 1,
                "coverage": {"stage_attempts": 1},
                "repair_contract_subtype_mismatches": [{"attempt_key": "a1"}],
                "repair_contract_provenance_mismatches": [{"attempt_key": "a1"}],
                "scope_authority_fix_scope_mismatches": [{"attempt_key": "a1"}],
                "scope_authority_authoritative_fix_scope_mismatches": [{"attempt_key": "a1"}],
                "scope_authority_widened_mismatches": [{"attempt_key": "a1"}],
                "gate_repair_metadata_missing": [{"attempt_key": "a1", "field": "repair_contract_subtype"}],
            }
        )

        assert compact["status"] == "warn"
        assert compact["issue_counts"]["repair_contract_subtype_mismatches"] == 1
        assert compact["issue_counts"]["repair_contract_provenance_mismatches"] == 1
        assert compact["issue_counts"]["scope_authority_fix_scope_mismatches"] == 1
        assert compact["issue_counts"]["scope_authority_authoritative_fix_scope_mismatches"] == 1
        assert compact["issue_counts"]["scope_authority_widened_mismatches"] == 1
        assert compact["issue_counts"]["gate_repair_metadata_missing"] == 1

    def test_write_summary_proof_digest_uses_committed_snapshot_only(self, runtime_audit, tmp_project):
        db = DBManager(tmp_project.root / "project_data.db")
        try:
            svc = AuditService(
                runtime_audit=runtime_audit,
                project_paths_fn=lambda: tmp_project,
                ui_log_fn=lambda msg: None,
                project_db_fn=lambda: db,
            )

            with db.transaction():
                persisted = db.save_ui_event(
                    session_id="sess-uncommitted",
                    seq=1,
                    stage=4,
                    ep_num=1,
                    component="Stage4",
                    message="not committed yet",
                )
                assert persisted is True

                svc.audit_event("evt", "msg")
                svc.write_audit_summary("committed_only")

                summary_path = tmp_project.root / "logs" / "runtime_audit_summary.json"
                data = json.loads(summary_path.read_text(encoding="utf-8"))

                assert data["contract"]["proof_digest_truth_scope"] == "committed_persistence_only"
                assert data["proof_digest"]["artifacts"]["ui_events_db_available"] is True
                assert data["proof_digest"]["artifacts"]["ui_events_count"] == 0
        finally:
            db.close()

    def test_write_summary_proof_digest_includes_latest_stage2_session_alignment(self, svc, tmp_project):
        db = DBManager(tmp_project.root / "project_data.db")
        attempt_key = "s2:ep2:arc2:a1:sess-stage2"
        artifact_path = "logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json"
        try:
            (tmp_project.root / "logs" / "session").mkdir(parents=True, exist_ok=True)
            artifact_file = tmp_project.root / artifact_path
            artifact_file.parent.mkdir(parents=True, exist_ok=True)
            artifact_file.write_text("{}", encoding="utf-8")
            (tmp_project.root / "logs" / "session_legacy_token.log").write_text("session log", encoding="utf-8")

            db.save_stage_attempt(
                stage=2,
                verdict="PASS",
                attempt_num=1,
                ep_num=2,
                arc_num=2,
                score=93,
                session_id="sess-stage2",
                attempt_key=attempt_key,
                candidate_key="balanced",
                content_hash="hash-stage2-proof",
                artifact_path=artifact_path,
                selection_reason="carryover packet remains stable",
                verdict_reason="ready for blueprint handoff",
            )
            db.save_director_selection(
                ep_num=2,
                round_num=1,
                selected_label="A",
                selected_strategy="balanced",
                verdict="PASS",
                score=93,
                stage=2,
                attempt_key=attempt_key,
                candidate_key="balanced",
                content_hash="hash-stage2-proof",
                artifact_path=artifact_path,
                selection_reason="carryover packet remains stable",
            )
            (tmp_project.root / "logs" / "session" / "decisions.jsonl").write_text(
                json.dumps(
                    {
                        "stage": "stage2",
                        "ep_num": 2,
                        "result": "PASS",
                        "score": 93,
                        "meta": {
                            "session_id": "sess-stage2",
                            "attempt_key": attempt_key,
                            "candidate_key": "balanced",
                            "content_hash": "hash-stage2-proof",
                            "artifact_path": artifact_path,
                            "selection_reason": "carryover packet remains stable",
                            "verdict_reason": "ready for blueprint handoff",
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
                                "stage": 2,
                                "episode": 2,
                                "arc": 2,
                                "attempt_num": 1,
                                "success": True,
                                "attempt_key": attempt_key,
                                "final_verdict": "PASS",
                                "candidate_key": "balanced",
                                "content_hash": "hash-stage2-proof",
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
            svc.write_audit_summary("stage2_proof")

            summary_path = tmp_project.root / "logs" / "runtime_audit_summary.json"
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            stage2 = data["proof_digest"]["stages"]["stage2"]

            assert data["proof_digest"]["available"] is True
            assert stage2["status"] == "warn"
            assert stage2["attempts_considered"] == 1
            assert stage2["session_scoped_attempts"] == 1
            assert stage2["coverage"]["session_decisions"] == 1
            assert stage2["coverage"]["pass_rate_monitor"] == 1
            assert stage2["issue_counts"]["rationale_metadata_missing"] == 1
        finally:
            db.close()

    def test_write_summary_stage2_proof_digest_warns_when_stage2_monitor_sink_is_missing(self, svc, tmp_project):
        db = DBManager(tmp_project.root / "project_data.db")
        attempt_key = "s2:ep1:arc1:a1:sess-stage2-missing-monitor"
        artifact_path = "logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json"
        try:
            (tmp_project.root / "logs" / "session").mkdir(parents=True, exist_ok=True)
            artifact_file = tmp_project.root / artifact_path
            artifact_file.parent.mkdir(parents=True, exist_ok=True)
            artifact_file.write_text("{}", encoding="utf-8")

            db.save_stage_attempt(
                stage=2,
                verdict="PASS",
                attempt_num=1,
                ep_num=1,
                arc_num=1,
                score=93,
                session_id="sess-stage2-missing-monitor",
                attempt_key=attempt_key,
                candidate_key="balanced",
                content_hash="hash-stage2-missing-monitor",
                artifact_path=artifact_path,
                selection_reason="carryover packet remains stable",
                verdict_reason="ready for Stage3 handoff",
            )
            db.save_director_selection(
                ep_num=1,
                round_num=1,
                selected_label="A",
                selected_strategy="balanced",
                verdict="PASS",
                score=93,
                stage=2,
                attempt_key=attempt_key,
                candidate_key="balanced",
                content_hash="hash-stage2-missing-monitor",
                artifact_path=artifact_path,
                selection_reason="carryover packet remains stable",
                verdict_reason="ready for Stage3 handoff",
            )
            (tmp_project.root / "logs" / "session" / "decisions.jsonl").write_text(
                json.dumps(
                    {
                        "stage": "stage2",
                        "ep_num": 1,
                        "decision_type": "arc_final",
                        "result": "PASS",
                        "score": 93,
                        "meta": {
                            "session_id": "sess-stage2-missing-monitor",
                            "attempt_key": attempt_key,
                            "candidate_key": "balanced",
                            "content_hash": "hash-stage2-missing-monitor",
                            "artifact_path": artifact_path,
                            "selection_reason": "carryover packet remains stable",
                            "verdict_reason": "ready for Stage3 handoff",
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            svc.audit_event("evt", "msg")
            svc.write_audit_summary("stage2_missing_monitor")

            summary_path = tmp_project.root / "logs" / "runtime_audit_summary.json"
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            stage2 = data["proof_digest"]["stages"]["stage2"]

            assert stage2["status"] == "warn"
            assert stage2["issue_counts"]["final_sink_missing"] == 1
        finally:
            db.close()

    def test_write_summary_stage2_proof_digest_warns_on_stage_attempt_rationale_drift(self, svc, tmp_project):
        db = DBManager(tmp_project.root / "project_data.db")
        attempt_key = "s2:ep4:arc4:a1:sess-stage2-rationale"
        artifact_path = "logs/artifacts/stage2/arc_004/attempt_01/final_arc__balanced.json"
        try:
            (tmp_project.root / "logs" / "session").mkdir(parents=True, exist_ok=True)
            artifact_file = tmp_project.root / artifact_path
            artifact_file.parent.mkdir(parents=True, exist_ok=True)
            artifact_file.write_text("{}", encoding="utf-8")

            db.save_stage_attempt(
                stage=2,
                verdict="PASS",
                attempt_num=1,
                ep_num=4,
                arc_num=4,
                score=95,
                session_id="sess-stage2-rationale",
                attempt_key=attempt_key,
                candidate_key="balanced",
                content_hash="hash-stage2-rationale",
                artifact_path=artifact_path,
                selection_reason="carryover packet remains stable",
                verdict_reason="stage-attempt rationale only",
            )
            db.save_director_selection(
                ep_num=4,
                round_num=1,
                selected_label="A",
                selected_strategy="balanced",
                verdict="PASS",
                score=95,
                stage=2,
                attempt_key=attempt_key,
                candidate_key="balanced",
                content_hash="hash-stage2-rationale",
                artifact_path=artifact_path,
                selection_reason="carryover packet remains stable",
                verdict_reason="shared final rationale",
            )
            (tmp_project.root / "logs" / "session" / "decisions.jsonl").write_text(
                json.dumps(
                    {
                        "stage": "stage2",
                        "ep_num": 4,
                        "decision_type": "arc_final",
                        "result": "PASS",
                        "score": 95,
                        "meta": {
                            "session_id": "sess-stage2-rationale",
                            "attempt_key": attempt_key,
                            "candidate_key": "balanced",
                            "content_hash": "hash-stage2-rationale",
                            "artifact_path": artifact_path,
                            "selection_reason": "carryover packet remains stable",
                            "verdict_reason": "shared final rationale",
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
                                "stage": 2,
                                "episode": 4,
                                "arc": 4,
                                "attempt_num": 1,
                                "success": True,
                                "attempt_key": attempt_key,
                                "final_verdict": "PASS",
                                "candidate_key": "balanced",
                                "content_hash": "hash-stage2-rationale",
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
            svc.write_audit_summary("stage2_rationale_drift")

            data = json.loads((tmp_project.root / "logs" / "runtime_audit_summary.json").read_text(encoding="utf-8"))
            stage2 = data["proof_digest"]["stages"]["stage2"]

            assert data["proof_digest"]["status"] == "warn"
            assert stage2["status"] == "warn"
            assert stage2["issue_counts"]["verdict_reason_mismatches"] == 1
        finally:
            db.close()

    def test_write_summary_stage2_proof_digest_warns_on_blank_stage_attempt_attempt_key(self, svc, tmp_project):
        db = DBManager(tmp_project.root / "project_data.db")
        try:
            db.save_stage_attempt(
                stage=2,
                verdict="PASS",
                attempt_num=1,
                ep_num=5,
                arc_num=5,
                score=88,
                session_id="sess-stage2-blank-key",
                attempt_key="",
                candidate_key="balanced",
                content_hash="hash-stage2-blank-key",
                artifact_path="logs/artifacts/stage2/arc_005/attempt_01/final_arc__balanced.json",
                selection_reason="carryover packet remains stable",
                verdict_reason="ready for Stage3 handoff",
            )

            svc.audit_event("evt", "msg")
            svc.write_audit_summary("stage2_blank_attempt_key")

            data = json.loads((tmp_project.root / "logs" / "runtime_audit_summary.json").read_text(encoding="utf-8"))
            stage2 = data["proof_digest"]["stages"]["stage2"]

            assert data["proof_digest"]["available"] is True
            assert data["proof_digest"]["status"] == "warn"
            assert stage2["status"] == "warn"
            assert stage2["attempts_considered"] == 0
            assert stage2["issue_counts"]["stage_attempt_rows_without_attempt_key"] == 1
        finally:
            db.close()

    def test_write_summary_stage2_proof_digest_warns_when_session_verdict_reason_is_missing(self, svc, tmp_project):
        db = DBManager(tmp_project.root / "project_data.db")
        attempt_key = "s2:ep6:arc6:a1:sess-stage2-missing-verdict"
        artifact_path = "logs/artifacts/stage2/arc_006/attempt_01/final_arc__balanced.json"
        try:
            (tmp_project.root / "logs" / "session").mkdir(parents=True, exist_ok=True)
            artifact_file = tmp_project.root / artifact_path
            artifact_file.parent.mkdir(parents=True, exist_ok=True)
            artifact_file.write_text("{}", encoding="utf-8")

            db.save_stage_attempt(
                stage=2,
                verdict="PASS",
                attempt_num=1,
                ep_num=6,
                arc_num=6,
                score=92,
                session_id="sess-stage2-missing-verdict",
                attempt_key=attempt_key,
                candidate_key="balanced",
                content_hash="hash-stage2-missing-verdict",
                artifact_path=artifact_path,
                selection_reason="carryover packet remains stable",
                verdict_reason="ready for Stage3 handoff",
            )
            db.save_director_selection(
                ep_num=6,
                round_num=1,
                selected_label="A",
                selected_strategy="balanced",
                verdict="PASS",
                score=92,
                stage=2,
                attempt_key=attempt_key,
                candidate_key="balanced",
                content_hash="hash-stage2-missing-verdict",
                artifact_path=artifact_path,
                selection_reason="carryover packet remains stable",
                verdict_reason="ready for Stage3 handoff",
            )
            (tmp_project.root / "logs" / "session" / "decisions.jsonl").write_text(
                json.dumps(
                    {
                        "stage": "stage2",
                        "ep_num": 6,
                        "decision_type": "arc_final",
                        "result": "PASS",
                        "score": 92,
                        "meta": {
                            "session_id": "sess-stage2-missing-verdict",
                            "attempt_key": attempt_key,
                            "candidate_key": "balanced",
                            "content_hash": "hash-stage2-missing-verdict",
                            "artifact_path": artifact_path,
                            "selection_reason": "carryover packet remains stable",
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
                                "stage": 2,
                                "episode": 6,
                                "arc": 6,
                                "attempt_num": 1,
                                "success": True,
                                "attempt_key": attempt_key,
                                "final_verdict": "PASS",
                                "candidate_key": "balanced",
                                "content_hash": "hash-stage2-missing-verdict",
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
            svc.write_audit_summary("stage2_missing_verdict_reason")

            data = json.loads((tmp_project.root / "logs" / "runtime_audit_summary.json").read_text(encoding="utf-8"))
            stage2 = data["proof_digest"]["stages"]["stage2"]

            assert data["proof_digest"]["status"] == "warn"
            assert stage2["status"] == "warn"
            assert stage2["issue_counts"]["rationale_metadata_missing"] == 1
        finally:
            db.close()

    def test_write_summary_stage2_proof_digest_surfaces_runtime_and_retry_mismatches(self, svc, tmp_project):
        db = DBManager(tmp_project.root / "project_data.db")
        attempt_key = "s2:ep7:arc7:a1:sess-stage2-runtime-retry"
        artifact_path = "logs/artifacts/stage2/arc_007/attempt_01/final_arc__balanced.json"
        try:
            (tmp_project.root / "logs" / "session").mkdir(parents=True, exist_ok=True)
            artifact_file = tmp_project.root / artifact_path
            artifact_file.parent.mkdir(parents=True, exist_ok=True)
            artifact_file.write_text("{}", encoding="utf-8")

            db.save_stage_attempt(
                stage=2,
                verdict="REJECT",
                attempt_num=1,
                ep_num=7,
                arc_num=7,
                score=61,
                session_id="sess-stage2-runtime-retry",
                attempt_key=attempt_key,
                candidate_key="balanced",
                content_hash="hash-stage2-runtime-retry",
                artifact_path=artifact_path,
                selection_reason="carryover packet drifted",
                verdict_reason="repair required before Stage3 handoff",
                runtime_advisory="authority digest A",
                retry_directives="retry plan A",
            )
            db.save_director_selection(
                ep_num=7,
                round_num=1,
                selected_label="A",
                selected_strategy="balanced",
                verdict="REJECT",
                score=61,
                stage=2,
                attempt_key=attempt_key,
                candidate_key="balanced",
                content_hash="hash-stage2-runtime-retry",
                artifact_path=artifact_path,
                selection_reason="carryover packet drifted",
                verdict_reason="repair required before Stage3 handoff",
                runtime_advisory="authority digest B",
                retry_directives="retry plan B",
            )
            (tmp_project.root / "logs" / "session" / "decisions.jsonl").write_text(
                json.dumps(
                    {
                        "stage": "stage2",
                        "ep_num": 7,
                        "decision_type": "arc_final",
                        "result": "REJECT",
                        "score": 61,
                        "meta": {
                            "session_id": "sess-stage2-runtime-retry",
                            "attempt_key": attempt_key,
                            "candidate_key": "balanced",
                            "content_hash": "hash-stage2-runtime-retry",
                            "artifact_path": artifact_path,
                            "selection_reason": "carryover packet drifted",
                            "verdict_reason": "repair required before Stage3 handoff",
                            "runtime_advisory": "authority digest B",
                            "retry_directives": "retry plan B",
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
                                "stage": 2,
                                "episode": 7,
                                "arc": 7,
                                "attempt_num": 1,
                                "success": False,
                                "attempt_key": attempt_key,
                                "final_verdict": "REJECT",
                                "candidate_key": "balanced",
                                "content_hash": "hash-stage2-runtime-retry",
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
            svc.write_audit_summary("stage2_runtime_retry")

            data = json.loads((tmp_project.root / "logs" / "runtime_audit_summary.json").read_text(encoding="utf-8"))
            stage2 = data["proof_digest"]["stages"]["stage2"]

            assert data["proof_digest"]["status"] == "warn"
            assert stage2["status"] == "warn"
            assert stage2["issue_counts"]["runtime_advisory_mismatches"] == 1
            assert stage2["issue_counts"]["retry_directives_mismatches"] == 1
        finally:
            db.close()

    def test_write_summary_stage2_proof_digest_prefers_authoritative_session_decision_row(self, svc, tmp_project):
        db = DBManager(tmp_project.root / "project_data.db")
        attempt_key = "s2:ep3:arc3:a1:sess-stage2-rich"
        artifact_path = "logs/artifacts/stage2/arc_003/attempt_01/final_arc__balanced.json"
        try:
            (tmp_project.root / "logs" / "session").mkdir(parents=True, exist_ok=True)
            artifact_file = tmp_project.root / artifact_path
            artifact_file.parent.mkdir(parents=True, exist_ok=True)
            artifact_file.write_text("{}", encoding="utf-8")
            (tmp_project.root / "logs" / "session_legacy_token.log").write_text("session log", encoding="utf-8")

            db.save_stage_attempt(
                stage=2,
                verdict="PASS",
                attempt_num=1,
                ep_num=3,
                arc_num=3,
                score=94,
                session_id="sess-stage2-rich",
                attempt_key=attempt_key,
                candidate_key="balanced",
                content_hash="hash-stage2-rich",
                artifact_path=artifact_path,
                selection_reason="carryover packet remains stable",
                verdict_reason="ready for blueprint handoff",
            )
            db.save_director_selection(
                ep_num=3,
                round_num=1,
                selected_label="A",
                selected_strategy="balanced",
                verdict="PASS",
                score=94,
                stage=2,
                attempt_key=attempt_key,
                candidate_key="balanced",
                content_hash="hash-stage2-rich",
                artifact_path=artifact_path,
                selection_reason="carryover packet remains stable",
                verdict_reason="ready for blueprint handoff",
            )
            (tmp_project.root / "logs" / "session" / "decisions.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "stage": "stage2",
                                "ep_num": 3,
                                "decision_type": "arc",
                                "result": "PASS",
                                "score": 94,
                                "meta": {
                                    "session_id": "sess-stage2-rich",
                                    "attempt_key": attempt_key,
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "stage": "stage2",
                                "ep_num": 3,
                                "decision_type": "arc_final",
                                "result": "PASS",
                                "score": 94,
                                "meta": {
                                    "session_id": "sess-stage2-rich",
                                    "attempt_key": attempt_key,
                                    "candidate_key": "balanced",
                                    "content_hash": "hash-stage2-rich",
                                    "artifact_path": artifact_path,
                                    "selection_reason": "carryover packet remains stable",
                                    "verdict_reason": "ready for blueprint handoff",
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "stage": "stage2",
                                "ep_num": 3,
                                "decision_type": "arc_design",
                                "result": "PASS",
                                "score": 94,
                                "meta": {
                                    "session_id": "sess-stage2-rich",
                                    "attempt_key": attempt_key,
                                    "candidate_key": "balanced",
                                    "content_hash": "hash-stage2-rich",
                                    "artifact_path": artifact_path,
                                    "selection_reason": "stale intermediate row",
                                    "verdict_reason": "stale intermediate verdict",
                                },
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (tmp_project.root / "logs" / "pass_rate_monitor.json").write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "stage": 2,
                                "episode": 3,
                                "arc": 3,
                                "attempt_num": 1,
                                "success": True,
                                "attempt_key": attempt_key,
                                "final_verdict": "PASS",
                                "candidate_key": "balanced",
                                "content_hash": "hash-stage2-rich",
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
            svc.write_audit_summary("stage2_richest")

            summary_path = tmp_project.root / "logs" / "runtime_audit_summary.json"
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            stage2 = data["proof_digest"]["stages"]["stage2"]
            operational = data["proof_digest"]["operational_metadata"]["stage2_live_session"]

            assert data["proof_digest"]["status"] == "ok"
            assert stage2["status"] == "ok"
            assert stage2["attempts_considered"] == 1
            assert stage2["issue_counts"] == {}
            assert operational["decision_artifact_path_coverage"] == {
                "present": 2,
                "total": 3,
                "status": "partial",
            }
        finally:
            db.close()

    def test_write_summary_includes_operational_metadata_for_latest_stage4_session(self, svc, tmp_project):
        db = DBManager(tmp_project.root / "project_data.db")
        stage2_artifact_path = "logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json"
        artifact_path = "logs/artifacts/stage4/ep_0002/attempt_01/final_manuscript__A_balanced.txt"
        stage3_artifact_path = "logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__A_balanced.json"
        try:
            (tmp_project.root / "logs" / "session").mkdir(parents=True, exist_ok=True)
            stage2_artifact_file = tmp_project.root / stage2_artifact_path
            stage2_artifact_file.parent.mkdir(parents=True, exist_ok=True)
            stage2_artifact_file.write_text("{}", encoding="utf-8")
            artifact_file = tmp_project.root / artifact_path
            artifact_file.parent.mkdir(parents=True, exist_ok=True)
            artifact_file.write_text("manuscript", encoding="utf-8")
            stage3_artifact_file = tmp_project.root / stage3_artifact_path
            stage3_artifact_file.parent.mkdir(parents=True, exist_ok=True)
            stage3_artifact_file.write_text("{}", encoding="utf-8")

            db.save_stage_attempt(
                stage=2,
                verdict="PASS",
                attempt_num=1,
                ep_num=2,
                arc_num=2,
                score=91,
                session_id="sess-wave",
                attempt_key="s2:ep2:arc2:a1:sess-wave",
                candidate_key="balanced",
                content_hash="hash-stage2",
                artifact_path=stage2_artifact_path,
                selection_reason="arc 2 closes the carryover boundary cleanly",
                verdict_reason="ready for Stage3 handoff",
                advisory_flags={
                    "carryover_authority": {
                        "start_location": "장례식장 운영실",
                        "end_location": "장례식장 지하 1층 후방 복도",
                        "start_inventory_count": 2,
                        "end_inventory_count": 3,
                    }
                },
            )
            db.save_stage_attempt(
                stage=3,
                verdict="PASS",
                attempt_num=1,
                ep_num=2,
                arc_num=1,
                score=94,
                session_id="sess-wave",
                attempt_key="s3:ep2:arc1:a1:sess-wave",
                candidate_key="A|bp",
                content_hash="hash-stage3",
                artifact_path=stage3_artifact_path,
                selection_reason="candidate A preserves the opening transition cleanly",
                verdict_reason="blueprint is ready without structural drift",
                advisory_flags={
                    "source_anchor_summary": {
                        "previous_blueprint_ep": 1,
                        "previous_blueprint_end_location": "서재 앞 복도",
                        "current_arc_start_location": "SW인베스트먼트 사무실",
                    }
                },
            )
            db.save_stage_attempt(
                stage=4,
                verdict="PASS",
                attempt_num=1,
                ep_num=2,
                arc_num=1,
                score=97,
                session_id="sess-wave",
                attempt_key="s4:ep2:arc1:a1:sess-wave",
                candidate_key="A|balanced",
                content_hash="hash-stage4",
                artifact_path=artifact_path,
            )
            db.save_ui_event(
                session_id="sess-wave",
                seq=1,
                stage=2,
                ep_num=2,
                attempt_key="s2:ep2:arc2:a1:sess-wave",
                component="Stage2Finalizer",
                event_kind="carryover_authority",
                message="carryover authority emitted",
                artifact_path=stage2_artifact_path,
                meta={
                    "start_location": "장례식장 운영실",
                    "end_location": "장례식장 지하 1층 후방 복도",
                },
            )
            db.save_ui_event(
                session_id="sess-wave",
                seq=2,
                stage=3,
                ep_num=2,
                attempt_key="s3:ep2:arc1:a1:sess-wave",
                component="blueprint_generation",
                event_kind="summary",
                message="source anchor emitted",
                artifact_path=stage3_artifact_path,
                meta={
                    "source_anchor_summary": {
                        "previous_blueprint_ep": 1,
                        "previous_blueprint_end_location": "서재 앞 복도",
                        "current_arc_start_location": "SW인베스트먼트 사무실",
                    }
                },
            )
            (tmp_project.root / "logs" / "session" / "decisions.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "stage": "stage2",
                                "ep_num": 2,
                                "result": "PASS",
                                "score": 91,
                                "meta": {
                                    "attempt_key": "s2:ep2:arc2:a1:sess-wave",
                                    "artifact_path": stage2_artifact_path,
                                    "selection_reason": "arc 2 closes the carryover boundary cleanly",
                                    "verdict_reason": "ready for Stage3 handoff",
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "stage": "stage3",
                                "ep_num": 2,
                                "result": "PASS",
                                "score": 94,
                                "meta": {
                                    "attempt_key": "s3:ep2:arc1:a1:sess-wave",
                                    "artifact_path": stage3_artifact_path,
                                    "selection_reason": "candidate A preserves the opening transition cleanly",
                                    "verdict_reason": "blueprint is ready without structural drift",
                                },
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            svc.audit_event(
                "stage4_session_scope",
                "stage4 session scope declared",
                {
                    "session_id": "sess-wave",
                    "start_ep": 2,
                    "target_ep": 2,
                    "total_planned_ep": 2,
                },
            )
            svc.audit_event(
                "stage4_post_pass_contract_signal",
                "stage4 post-pass contract persisted",
                {
                    "session_id": "sess-wave",
                    "ep": 2,
                },
            )
            svc.audit_event(
                "target_ep_reached",
                "stage4 target episode reached",
                {
                    "session_id": "sess-wave",
                    "target_ep": 2,
                    "next_ep": 3,
                },
            )
            svc.audit_event(
                "stage4_complete",
                "stage4 production completed",
                {
                    "session_id": "sess-wave",
                    "target_ep": 2,
                },
            )

            svc.write_audit_summary("stage4_complete")

            summary_path = tmp_project.root / "logs" / "runtime_audit_summary.json"
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            operational = data["proof_digest"]["operational_metadata"]

            assert operational["status"] == "ok"
            assert operational["latest_session_id"] == "sess-wave"
            assert operational["stage2_live_session"]["status"] == "ok"
            assert operational["stage2_live_session"]["episodes"] == [2]
            assert operational["stage2_live_session"]["attempt_key_coverage"]["status"] == "ok"
            assert operational["stage2_live_session"]["carryover_authority_event_count"] == 1
            assert (
                operational["stage2_live_session"]["latest_carryover_authority"]["end_location"]
                == "장례식장 지하 1층 후방 복도"
            )
            assert operational["stage3_live_session"]["status"] == "ok"
            assert operational["stage3_live_session"]["episodes"] == [2]
            assert operational["stage3_live_session"]["selection_reason_coverage"]["status"] == "ok"
            assert operational["stage3_live_session"]["source_anchor_summary_count"] == 1
            assert operational["stage3_live_session"]["source_anchor_ui_event_count"] == 1
            assert operational["stage3_live_session"]["latest_source_anchor_summary"]["previous_blueprint_ep"] == 1
            assert operational["stage4_live_session"]["status"] == "ok"
            assert operational["stage4_live_session"]["episodes"] == [2]
            assert operational["stage4_live_session"]["retry_exercised"] is False
            assert operational["stage4_live_session"]["patch_exercised"] is False
            assert operational["stage4_live_session"]["post_pass_contract_signal_count"] == 1
            assert operational["stage4_live_session"]["target_ep_reached"] is True
            assert operational["stage4_live_session"]["stage4_complete_emitted"] is True
            assert operational["stage4_live_session"]["session_scope"]["target_ep"] == 2
            assert operational["stage4_live_session"]["non_exercised_reasons"] == [
                "stage4_retry_not_needed_round1_pass",
                "stage4_patch_not_needed",
            ]
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
