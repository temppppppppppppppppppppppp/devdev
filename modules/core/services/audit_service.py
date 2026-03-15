"""Audit service for buffered runtime audit logging and summary writing."""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any


class AuditService:
    """Buffer runtime audit events and persist log/summary artifacts."""

    _AUTHORITATIVE_ATTEMPT_SINKS = (
        "stage_attempts",
        "pass_rate_monitor",
        "session_decisions",
        "episode_production",
        "director_selections",
    )

    def __init__(
        self,
        runtime_audit: list,
        project_paths_fn: Callable[[], Any],
        ui_log_fn: Callable[[str], None],
        before_summary_write_fn: Callable[[], None] | None = None,
        project_db_fn: Callable[[], Any] | None = None,
    ) -> None:
        self._runtime_audit = runtime_audit
        self._project_paths_fn = project_paths_fn
        self._ui_log = ui_log_fn
        self._before_summary_write = before_summary_write_fn
        self._project_db_fn = project_db_fn
        self._buffer: list[dict] = []

    @property
    def buffer(self) -> list[dict]:
        """Return the live audit buffer reference."""
        return self._buffer

    def audit_event(self, event_type: str, message: str, data: dict | None = None) -> None:
        """Append an audit event to memory and the flush buffer."""
        event = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": event_type,
            "message": message,
            "data": data or {},
        }
        self._runtime_audit.append(event)
        if len(self._runtime_audit) > 1000:
            self._runtime_audit[:] = self._runtime_audit[-500:]
        self._buffer.append(event)

    def flush_audit_buffer(self) -> None:
        """Flush the in-memory audit buffer to ``runtime_audit.jsonl``."""
        paths = self._project_paths_fn()
        if not self._buffer or paths is None:
            return
        try:
            log_dir = paths.root / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "runtime_audit.jsonl"
            with log_path.open("a", encoding="utf-8") as handle:
                for event in self._buffer:
                    handle.write(json.dumps(event, ensure_ascii=False) + "\n")
            self._buffer.clear()
        except Exception as exc:
            self._ui_log(f"[Audit] log write failed: {exc}")

    @staticmethod
    def _count_issue_entries(value: object) -> int:
        if isinstance(value, list):
            return len(value)
        if isinstance(value, dict):
            total = 0
            for item in value.values():
                if isinstance(item, dict) and "count" in item:
                    try:
                        total += int(item.get("count", 0) or 0)
                    except (TypeError, ValueError):
                        total += 0
                else:
                    total += 1
            return total
        return 0

    def _compact_sink_alignment_summary(self, summary: dict | None) -> dict:
        if not isinstance(summary, dict) or not summary:
            return {}
        issue_fields = (
            "final_sink_missing",
            "lifecycle_sink_missing",
            "lifecycle_missing_in_final_sinks",
            "final_verdict_mismatches",
            "final_score_mismatches",
            "initial_verdict_mismatches",
            "patch_strategy_mismatches",
            "candidate_key_mismatches",
            "selection_candidate_key_mismatches",
            "content_hash_mismatches",
            "artifact_path_mismatches",
            "artifact_metadata_missing",
            "selection_reason_mismatches",
            "verdict_reason_mismatches",
            "fix_scope_mismatches",
            "rationale_metadata_missing",
            "artifact_missing_files",
        )
        issue_counts = {
            field: self._count_issue_entries(summary.get(field))
            for field in issue_fields
            if self._count_issue_entries(summary.get(field)) > 0
        }
        session_rows_without_attempt_key = int(summary.get("session_decision_rows_without_attempt_key", 0) or 0)
        if session_rows_without_attempt_key > 0:
            issue_counts["session_decision_rows_without_attempt_key"] = session_rows_without_attempt_key
        return {
            "status": str(summary.get("status", "") or ""),
            "attempts_considered": int(summary.get("attempts_considered", 0) or 0),
            "complete_final_attempts": int(summary.get("complete_final_attempts", 0) or 0),
            "complete_lifecycle_attempts": int(summary.get("complete_lifecycle_attempts", 0) or 0),
            "legacy_key_attempts": int(summary.get("legacy_key_attempts", 0) or 0),
            "session_scoped_attempts": int(summary.get("session_scoped_attempts", 0) or 0),
            "coverage": dict(summary.get("coverage") or {}),
            "issue_counts": issue_counts,
        }

    def _resolve_proof_digest_db(self, db_path) -> tuple[Any, bool]:
        if callable(self._project_db_fn):
            try:
                project_db = self._project_db_fn()
            except Exception:
                project_db = None
            if getattr(project_db, "conn", None) is not None:
                return project_db, False

        conn = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return SimpleNamespace(conn=conn, db_path=db_path), True

    def _build_proof_digest(self, paths) -> dict:
        log_dir = paths.root / "logs"
        digest = {
            "available": False,
            "status": "unavailable",
            "artifacts": {
                "db_available": bool((paths.root / "project_data.db").exists()),
                "session_decisions_exists": bool((log_dir / "session" / "decisions.jsonl").exists()),
                "ui_events_jsonl_exists": bool((log_dir / "session" / "ui_events.jsonl").exists()),
                "pass_rate_monitor_exists": bool((log_dir / "pass_rate_monitor.json").exists()),
                "episode_production_exists": bool((log_dir / "episode_production.jsonl").exists()),
                "runtime_audit_jsonl_exists": bool((log_dir / "runtime_audit.jsonl").exists()),
                "ui_events_db_available": False,
                "ui_events_count": 0,
                "ui_event_coverage_status": "missing",
            },
            "stages": {},
        }
        db_path = paths.root / "project_data.db"
        if not db_path.exists():
            return digest

        try:
            from modules.core.failure_analyzer import FailureAnalyzer

            db, should_close = self._resolve_proof_digest_db(db_path)
            try:
                try:
                    ui_event_count = int(db.conn.execute("SELECT COUNT(*) AS cnt FROM ui_events").fetchone()["cnt"])
                except Exception:
                    ui_event_count = 0
                digest["artifacts"]["ui_events_db_available"] = True
                digest["artifacts"]["ui_events_count"] = ui_event_count
                if digest["artifacts"]["ui_events_jsonl_exists"] and ui_event_count > 0:
                    digest["artifacts"]["ui_event_coverage_status"] = "ok"
                elif digest["artifacts"]["ui_events_jsonl_exists"] or ui_event_count > 0:
                    digest["artifacts"]["ui_event_coverage_status"] = "partial"
                analyzer = FailureAnalyzer(db, project_path=paths.root)
                for stage in (3, 4):
                    summary = analyzer.sink_alignment_summary(stage=stage, include_session_decisions=True)
                    compact = self._compact_sink_alignment_summary(summary)
                    if compact:
                        digest["stages"][f"stage{stage}"] = compact
            finally:
                if should_close:
                    db.conn.close()
        except Exception as exc:
            digest["status"] = "warn"
            digest["error"] = str(exc)[:200]
            return digest

        stage_statuses = [entry.get("status", "") for entry in digest["stages"].values() if isinstance(entry, dict)]
        digest["available"] = bool(digest["stages"])
        if not stage_statuses:
            digest["status"] = "unavailable"
        elif any(status not in ("", "ok") for status in stage_statuses):
            digest["status"] = "warn"
        else:
            digest["status"] = "ok"
        return digest

    @classmethod
    def _build_summary_contract(cls) -> dict:
        return {
            "summary_scope": "runtime_heartbeat_plus_compact_proof_digest",
            "attempt_truth_authoritative": False,
            "authoritative_attempt_sinks": list(cls._AUTHORITATIVE_ATTEMPT_SINKS),
            "proof_digest_truth_scope": "committed_persistence_only",
            "authoritative_attempt_truth_note": (
                "Use DB/JSONL/artifact sink join for authoritative attempt truth."
            ),
        }

    def write_audit_summary(self, tag: str = "snapshot") -> None:
        """Write a runtime heartbeat plus compact proof digest summary."""
        self.flush_audit_buffer()
        paths = self._project_paths_fn()
        if paths is None:
            return
        try:
            if callable(self._before_summary_write):
                try:
                    self._before_summary_write()
                except Exception as exc:
                    self._ui_log(f"[Audit] pre-summary hook failed: {exc}")
            summary = {
                "tag": tag,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "summary_role": "runtime_heartbeat_with_proof_digest",
                "total_events": len(self._runtime_audit),
                "counts": {},
                "latest_event_type": "",
                "recent_events": [],
            }
            summary["contract"] = self._build_summary_contract()
            recent_events = self._runtime_audit[-10:]
            for event in self._runtime_audit[-200:]:
                summary["counts"][event["type"]] = summary["counts"].get(event["type"], 0) + 1
            if recent_events:
                summary["latest_event_type"] = str(recent_events[-1].get("type", "") or "")
                summary["recent_events"] = [
                    {
                        "type": str(event.get("type", "") or ""),
                        "message": str(event.get("message", "") or "")[:160],
                    }
                    for event in recent_events
                ]
            summary["proof_digest"] = self._build_proof_digest(paths)
            log_dir = paths.root / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            summary_path = log_dir / "runtime_audit_summary.json"
            summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            self._ui_log(f"[Audit] summary write failed: {exc}")
