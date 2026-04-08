"""Audit service for buffered runtime audit logging and summary writing."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
import time
from collections.abc import Callable
from typing import Any

from modules.core.db_manager import DBManager


class _ProofDigestDBFacade:
    """Read-only DB facade with the minimal DBManager contract FailureAnalyzer expects."""

    _director_stage_predicate = staticmethod(DBManager._director_stage_predicate)
    get_stage4_final_authority_rows = DBManager.get_stage4_final_authority_rows

    def __init__(self, db_path) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True, check_same_thread=False, timeout=30.0)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._lock = threading.RLock()


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
            "director_verdict_mismatches",
            "gate_basis_mismatches",
            "repair_scope_mismatches",
            "fix_pack_target_kind_mismatches",
            "fix_pack_patch_targets_mismatches",
            "retry_budget_axes_mismatches",
            "repair_contract_subtype_mismatches",
            "repair_contract_provenance_mismatches",
            "scope_authority_fix_scope_mismatches",
            "scope_authority_authoritative_fix_scope_mismatches",
            "scope_authority_widened_mismatches",
            "gate_repair_metadata_missing",
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
        return _ProofDigestDBFacade(db_path), True

    @staticmethod
    def _latest_plain_log_token(log_dir) -> str:
        latest_token = ""
        latest_mtime = -1.0
        for path in log_dir.glob("session_*.log"):
            match = re.fullmatch(r"session_(.+)\.log", path.name)
            if not match:
                continue
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if mtime >= latest_mtime:
                latest_mtime = mtime
                latest_token = match.group(1).strip()
        return latest_token

    @staticmethod
    def _latest_structured_session_id(db) -> str:
        queries = (
            "SELECT session_id FROM stage_attempts WHERE COALESCE(session_id, '') != '' ORDER BY id DESC LIMIT 1",
            "SELECT session_id FROM ui_events WHERE COALESCE(session_id, '') != '' ORDER BY id DESC LIMIT 1",
            "SELECT session_id FROM llm_calls WHERE COALESCE(session_id, '') != '' ORDER BY id DESC LIMIT 1",
        )
        for sql in queries:
            try:
                row = db.conn.execute(sql).fetchone()
            except Exception:
                row = None
            if not row:
                continue
            value = str(row["session_id"] or "").strip()
            if value:
                return value
        return ""

    def _build_session_lineage(self, *, log_dir, db) -> dict:
        plain_log_token = self._latest_plain_log_token(log_dir)
        structured_session_id = self._latest_structured_session_id(db)
        if plain_log_token and structured_session_id:
            status = "unified" if plain_log_token == structured_session_id else "split_mapped"
        elif plain_log_token or structured_session_id:
            status = "partial"
        else:
            status = "missing"
        return {
            "plain_log_token": plain_log_token,
            "structured_session_id": structured_session_id,
            "status": status,
        }

    @staticmethod
    def _load_runtime_audit_events(log_dir) -> list[dict]:
        events: list[dict] = []
        log_path = log_dir / "runtime_audit.jsonl"
        if not log_path.exists():
            return events
        try:
            with log_path.open("r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                    except (TypeError, ValueError, json.JSONDecodeError):
                        continue
                    if isinstance(payload, dict):
                        events.append(payload)
        except Exception:
            return []
        return events

    @staticmethod
    def _runtime_event_session_id(event: dict) -> str:
        if not isinstance(event, dict):
            return ""
        data = event.get("data")
        if not isinstance(data, dict):
            return ""
        return str(data.get("session_id") or "").strip()

    @staticmethod
    def _attempt_key_session_id(attempt_key: str) -> str:
        key = str(attempt_key or "").strip()
        if not key:
            return ""
        parts = key.split(":")
        if len(parts) <= 4:
            return ""
        return ":".join(parts[4:]).strip()

    @classmethod
    def _filter_runtime_events_for_session(cls, events: list[dict], *, event_type: str, session_id: str) -> list[dict]:
        filtered: list[dict] = []
        for event in events:
            if str(event.get("type", "") or "").strip() != event_type:
                continue
            if session_id:
                event_session_id = cls._runtime_event_session_id(event)
                if event_session_id != session_id:
                    continue
            filtered.append(event)
        return filtered

    @staticmethod
    def _load_stage_attempt_rows_for_session(db, *, stage: int, session_id: str) -> list[dict]:
        if not session_id:
            return []
        try:
            rows = db.conn.execute(
                """
                SELECT ep_num, attempt_num, verdict, is_patch, is_patch_fallback, patch_strategy,
                       attempt_key, candidate_key, content_hash, artifact_path,
                       selection_reason, verdict_reason, fix_scope, failure_category,
                       reject_reason, advisory_flags
                FROM stage_attempts
                WHERE stage = ? AND session_id = ?
                ORDER BY id ASC
                """,
                (int(stage), session_id),
            ).fetchall()
        except Exception:
            return []
        return [dict(row) for row in rows]

    @classmethod
    def _load_session_decision_rows_for_session(cls, log_dir, *, stage_label: str, session_id: str) -> list[dict]:
        if not session_id:
            return []
        rows: list[dict] = []
        log_path = log_dir / "session" / "decisions.jsonl"
        if not log_path.exists():
            return rows
        try:
            with log_path.open("r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                    except (TypeError, ValueError, json.JSONDecodeError):
                        continue
                    if not isinstance(payload, dict):
                        continue
                    if str(payload.get("stage", "") or "").strip() != str(stage_label or "").strip():
                        continue
                    meta = payload.get("meta")
                    meta = meta if isinstance(meta, dict) else {}
                    candidate_session_id = str(meta.get("session_id") or "").strip()
                    if not candidate_session_id:
                        candidate_session_id = cls._attempt_key_session_id(str(meta.get("attempt_key") or ""))
                    if candidate_session_id != session_id:
                        continue
                    rows.append(payload)
        except Exception:
            return []
        return rows

    @staticmethod
    def _load_ui_event_rows_for_session(db, *, session_id: str, stage: int) -> list[dict]:
        if not session_id:
            return []
        try:
            rows = db.conn.execute(
                """
                SELECT ep_num, attempt_key, component, event_kind, artifact_path, meta_json
                FROM ui_events
                WHERE session_id = ? AND stage = ?
                ORDER BY id ASC
                """,
                (str(session_id), int(stage)),
            ).fetchall()
        except Exception:
            return []
        parsed_rows: list[dict] = []
        for row in rows:
            payload = dict(row)
            meta_json = payload.get("meta_json")
            if isinstance(meta_json, str) and meta_json.strip():
                try:
                    payload["meta"] = json.loads(meta_json)
                except (TypeError, ValueError, json.JSONDecodeError):
                    payload["meta"] = {}
            else:
                payload["meta"] = {}
            payload.pop("meta_json", None)
            parsed_rows.append(payload)
        return parsed_rows

    @staticmethod
    def _summarize_live_session_rows(rows: list[dict]) -> dict:
        episodes = sorted(
            {
                int(row.get("ep_num") or 0)
                for row in rows
                if isinstance(row.get("ep_num"), int) or str(row.get("ep_num") or "").strip()
            }
        )
        episodes = [ep for ep in episodes if ep > 0]
        return {
            "attempt_count": len(rows),
            "episode_count": len(episodes),
            "episodes": episodes,
            "latest_ep": episodes[-1] if episodes else None,
        }

    @staticmethod
    def _coverage_summary(rows: list[dict], key: str) -> dict:
        total = len(rows)
        present = 0
        for row in rows:
            value = row.get(key)
            if isinstance(value, str):
                if value.strip():
                    present += 1
            elif value:
                present += 1
        return {
            "present": present,
            "total": total,
            "status": "ok" if total > 0 and present == total else ("partial" if present > 0 else "missing"),
        }

    @staticmethod
    def _decision_meta_coverage(decision_rows: list[dict], meta_key: str) -> dict:
        total = len(decision_rows)
        present = 0
        for row in decision_rows:
            meta = row.get("meta")
            meta = meta if isinstance(meta, dict) else {}
            value = meta.get(meta_key)
            if isinstance(value, str):
                if value.strip():
                    present += 1
            elif value:
                present += 1
        return {
            "present": present,
            "total": total,
            "status": "ok" if total > 0 and present == total else ("partial" if present > 0 else "missing"),
        }

    @staticmethod
    def _advisory_flags(row: dict) -> dict:
        raw = row.get("advisory_flags")
        if isinstance(raw, dict):
            return dict(raw)
        if isinstance(raw, str) and raw.strip():
            try:
                payload = json.loads(raw)
            except (TypeError, ValueError, json.JSONDecodeError):
                return {}
            if isinstance(payload, dict):
                return payload
        return {}

    def _build_stage2_live_session_summary(
        self,
        *,
        rows: list[dict],
        decision_rows: list[dict],
        ui_rows: list[dict],
    ) -> dict:
        base = self._summarize_live_session_rows(rows)
        if not rows and not decision_rows and not ui_rows:
            return {
                "status": "absent",
                **base,
                "latest_final_verdict": "",
                "session_decision_count": 0,
                "ui_event_count": 0,
                "attempt_key_coverage": self._coverage_summary(rows, "attempt_key"),
                "artifact_path_coverage": self._coverage_summary(rows, "artifact_path"),
                "selection_reason_coverage": self._coverage_summary(rows, "selection_reason"),
                "verdict_reason_coverage": self._coverage_summary(rows, "verdict_reason"),
                "decision_attempt_key_coverage": self._decision_meta_coverage(decision_rows, "attempt_key"),
                "decision_artifact_path_coverage": self._decision_meta_coverage(decision_rows, "artifact_path"),
                "carryover_authority_event_count": 0,
                "latest_carryover_authority": {},
            }

        carryover_events = [row for row in ui_rows if str(row.get("event_kind", "") or "").strip() == "carryover_authority"]
        latest_carryover = {}
        if carryover_events:
            latest_meta = carryover_events[-1].get("meta")
            if isinstance(latest_meta, dict):
                latest_carryover = dict(latest_meta)
        return {
            "status": "ok",
            **base,
            "latest_final_verdict": str(rows[-1].get("verdict", "") or "").strip().upper() if rows else "",
            "session_decision_count": len(decision_rows),
            "ui_event_count": len(ui_rows),
            "attempt_key_coverage": self._coverage_summary(rows, "attempt_key"),
            "artifact_path_coverage": self._coverage_summary(rows, "artifact_path"),
            "selection_reason_coverage": self._coverage_summary(rows, "selection_reason"),
            "verdict_reason_coverage": self._coverage_summary(rows, "verdict_reason"),
            "decision_attempt_key_coverage": self._decision_meta_coverage(decision_rows, "attempt_key"),
            "decision_artifact_path_coverage": self._decision_meta_coverage(decision_rows, "artifact_path"),
            "carryover_authority_event_count": len(carryover_events),
            "latest_carryover_authority": latest_carryover,
        }

    def _build_stage3_live_session_summary(
        self,
        *,
        rows: list[dict],
        decision_rows: list[dict],
        ui_rows: list[dict],
    ) -> dict:
        base = self._summarize_live_session_rows(rows)
        if not rows and not decision_rows and not ui_rows:
            return {
                "status": "absent",
                **base,
                "latest_final_verdict": "",
                "session_decision_count": 0,
                "ui_event_count": 0,
                "attempt_key_coverage": self._coverage_summary(rows, "attempt_key"),
                "artifact_path_coverage": self._coverage_summary(rows, "artifact_path"),
                "selection_reason_coverage": self._coverage_summary(rows, "selection_reason"),
                "verdict_reason_coverage": self._coverage_summary(rows, "verdict_reason"),
                "decision_attempt_key_coverage": self._decision_meta_coverage(decision_rows, "attempt_key"),
                "decision_artifact_path_coverage": self._decision_meta_coverage(decision_rows, "artifact_path"),
                "source_anchor_summary_count": 0,
                "source_anchor_ui_event_count": 0,
                "latest_source_anchor_summary": {},
            }

        source_anchor_summaries: list[dict] = []
        for row in rows:
            advisory_flags = self._advisory_flags(row)
            summary = advisory_flags.get("source_anchor_summary")
            if isinstance(summary, dict) and summary:
                source_anchor_summaries.append(dict(summary))
        source_anchor_ui_events = [
            row
            for row in ui_rows
            if isinstance(row.get("meta"), dict) and isinstance(row["meta"].get("source_anchor_summary"), dict)
        ]
        latest_source_anchor = source_anchor_summaries[-1] if source_anchor_summaries else {}
        if not latest_source_anchor and source_anchor_ui_events:
            latest_meta = source_anchor_ui_events[-1].get("meta")
            latest_source_anchor = dict(latest_meta.get("source_anchor_summary") or {})
        return {
            "status": "ok",
            **base,
            "latest_final_verdict": str(rows[-1].get("verdict", "") or "").strip().upper() if rows else "",
            "session_decision_count": len(decision_rows),
            "ui_event_count": len(ui_rows),
            "attempt_key_coverage": self._coverage_summary(rows, "attempt_key"),
            "artifact_path_coverage": self._coverage_summary(rows, "artifact_path"),
            "selection_reason_coverage": self._coverage_summary(rows, "selection_reason"),
            "verdict_reason_coverage": self._coverage_summary(rows, "verdict_reason"),
            "decision_attempt_key_coverage": self._decision_meta_coverage(decision_rows, "attempt_key"),
            "decision_artifact_path_coverage": self._decision_meta_coverage(decision_rows, "artifact_path"),
            "source_anchor_summary_count": len(source_anchor_summaries),
            "source_anchor_ui_event_count": len(source_anchor_ui_events),
            "latest_source_anchor_summary": latest_source_anchor,
        }

    def _build_stage4_live_session_summary(self, *, rows: list[dict], runtime_events: list[dict], session_id: str) -> dict:
        scope_events = self._filter_runtime_events_for_session(
            runtime_events,
            event_type="stage4_session_scope",
            session_id=session_id,
        )
        target_events = self._filter_runtime_events_for_session(
            runtime_events,
            event_type="target_ep_reached",
            session_id=session_id,
        )
        complete_events = self._filter_runtime_events_for_session(
            runtime_events,
            event_type="stage4_complete",
            session_id=session_id,
        )
        contract_events = self._filter_runtime_events_for_session(
            runtime_events,
            event_type="stage4_post_pass_contract_signal",
            session_id=session_id,
        )

        base = self._summarize_live_session_rows(rows)
        if not rows and not scope_events and not target_events and not complete_events and not contract_events:
            return {
                "status": "absent",
                **base,
                "latest_final_verdict": "",
                "retry_exercised": False,
                "patch_exercised": False,
                "patch_attempt_count": 0,
                "fallback_patch_count": 0,
                "pass_count": 0,
                "session_scope": {},
                "target_ep_reached": False,
                "stage4_complete_emitted": False,
                "post_pass_contract_signal_count": 0,
                "non_exercised_reasons": [],
            }

        attempt_nums = [max(0, int(row.get("attempt_num") or 0)) for row in rows]
        patch_attempt_count = sum(1 for row in rows if bool(row.get("is_patch")))
        fallback_patch_count = sum(1 for row in rows if bool(row.get("is_patch_fallback")))
        pass_count = sum(1 for row in rows if str(row.get("verdict", "") or "").strip().upper() == "PASS")
        latest_final_verdict = str(rows[-1].get("verdict", "") or "").strip().upper() if rows else ""
        retry_exercised = any(attempt_num > 1 for attempt_num in attempt_nums)
        non_exercised_reasons: list[str] = []
        if rows and not retry_exercised and latest_final_verdict == "PASS" and max(attempt_nums or [0]) <= 1:
            non_exercised_reasons.append("stage4_retry_not_needed_round1_pass")
        if rows and patch_attempt_count == 0 and latest_final_verdict == "PASS":
            non_exercised_reasons.append("stage4_patch_not_needed")

        latest_scope = dict(scope_events[-1].get("data") or {}) if scope_events else {}
        return {
            "status": "ok",
            **base,
            "latest_final_verdict": latest_final_verdict,
            "retry_exercised": retry_exercised,
            "patch_exercised": patch_attempt_count > 0,
            "patch_attempt_count": patch_attempt_count,
            "fallback_patch_count": fallback_patch_count,
            "pass_count": pass_count,
            "session_scope": latest_scope,
            "target_ep_reached": bool(target_events),
            "stage4_complete_emitted": bool(complete_events),
            "post_pass_contract_signal_count": len(contract_events),
            "non_exercised_reasons": non_exercised_reasons,
        }

    def _build_operational_metadata(self, *, log_dir, db, latest_session_id: str) -> dict:
        if not latest_session_id:
            return {
                "status": "missing_session",
                "latest_session_id": "",
                "stage2_live_session": {
                    "status": "absent",
                    "attempt_count": 0,
                    "episode_count": 0,
                    "episodes": [],
                    "latest_ep": None,
                    "latest_final_verdict": "",
                    "session_decision_count": 0,
                    "ui_event_count": 0,
                    "attempt_key_coverage": {"present": 0, "total": 0, "status": "missing"},
                    "artifact_path_coverage": {"present": 0, "total": 0, "status": "missing"},
                    "selection_reason_coverage": {"present": 0, "total": 0, "status": "missing"},
                    "verdict_reason_coverage": {"present": 0, "total": 0, "status": "missing"},
                    "decision_attempt_key_coverage": {"present": 0, "total": 0, "status": "missing"},
                    "decision_artifact_path_coverage": {"present": 0, "total": 0, "status": "missing"},
                    "carryover_authority_event_count": 0,
                    "latest_carryover_authority": {},
                },
                "stage3_live_session": {
                    "status": "absent",
                    "attempt_count": 0,
                    "episode_count": 0,
                    "episodes": [],
                    "latest_ep": None,
                    "latest_final_verdict": "",
                    "session_decision_count": 0,
                    "ui_event_count": 0,
                    "attempt_key_coverage": {"present": 0, "total": 0, "status": "missing"},
                    "artifact_path_coverage": {"present": 0, "total": 0, "status": "missing"},
                    "selection_reason_coverage": {"present": 0, "total": 0, "status": "missing"},
                    "verdict_reason_coverage": {"present": 0, "total": 0, "status": "missing"},
                    "decision_attempt_key_coverage": {"present": 0, "total": 0, "status": "missing"},
                    "decision_artifact_path_coverage": {"present": 0, "total": 0, "status": "missing"},
                    "source_anchor_summary_count": 0,
                    "source_anchor_ui_event_count": 0,
                    "latest_source_anchor_summary": {},
                },
                "stage4_live_session": {
                    "status": "absent",
                    "attempt_count": 0,
                    "episode_count": 0,
                    "episodes": [],
                    "latest_ep": None,
                    "latest_final_verdict": "",
                    "retry_exercised": False,
                    "patch_exercised": False,
                    "patch_attempt_count": 0,
                    "fallback_patch_count": 0,
                    "pass_count": 0,
                    "session_scope": {},
                    "target_ep_reached": False,
                    "stage4_complete_emitted": False,
                    "post_pass_contract_signal_count": 0,
                    "non_exercised_reasons": [],
                },
            }

        runtime_events = self._load_runtime_audit_events(log_dir)
        stage2_rows = self._load_stage_attempt_rows_for_session(db, stage=2, session_id=latest_session_id)
        stage3_rows = self._load_stage_attempt_rows_for_session(db, stage=3, session_id=latest_session_id)
        stage4_rows = self._load_stage_attempt_rows_for_session(db, stage=4, session_id=latest_session_id)
        stage2_decisions = self._load_session_decision_rows_for_session(log_dir, stage_label="stage2", session_id=latest_session_id)
        stage3_decisions = self._load_session_decision_rows_for_session(log_dir, stage_label="stage3", session_id=latest_session_id)
        stage2_ui_rows = self._load_ui_event_rows_for_session(db, session_id=latest_session_id, stage=2)
        stage3_ui_rows = self._load_ui_event_rows_for_session(db, session_id=latest_session_id, stage=3)
        return {
            "status": "ok",
            "latest_session_id": latest_session_id,
            "stage2_live_session": self._build_stage2_live_session_summary(
                rows=stage2_rows,
                decision_rows=stage2_decisions,
                ui_rows=stage2_ui_rows,
            ),
            "stage3_live_session": self._build_stage3_live_session_summary(
                rows=stage3_rows,
                decision_rows=stage3_decisions,
                ui_rows=stage3_ui_rows,
            ),
            "stage4_live_session": self._build_stage4_live_session_summary(
                rows=stage4_rows,
                runtime_events=runtime_events,
                session_id=latest_session_id,
            ),
        }

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
                digest["session_lineage"] = self._build_session_lineage(log_dir=log_dir, db=db)
                latest_session_id = str(digest["session_lineage"].get("structured_session_id", "") or "")
                digest["operational_metadata"] = self._build_operational_metadata(
                    log_dir=log_dir,
                    db=db,
                    latest_session_id=latest_session_id,
                )
                digest["artifacts"]["ui_events_db_available"] = True
                digest["artifacts"]["ui_events_count"] = ui_event_count
                if digest["artifacts"]["ui_events_jsonl_exists"] and ui_event_count > 0:
                    digest["artifacts"]["ui_event_coverage_status"] = "ok"
                elif digest["artifacts"]["ui_events_jsonl_exists"] or ui_event_count > 0:
                    digest["artifacts"]["ui_event_coverage_status"] = "partial"
                analyzer = FailureAnalyzer(db, project_path=paths.root)
                for stage in (2, 3, 4):
                    summary = analyzer.sink_alignment_summary(
                        stage=stage,
                        include_session_decisions=True,
                        session_id=latest_session_id,
                    )
                    compact = self._compact_sink_alignment_summary(summary)
                    if compact:
                        digest["stages"][f"stage{stage}"] = compact
                stage4_numeric_summary = analyzer.numeric_consistency_summary(
                    stage=4,
                    session_id=latest_session_id,
                )
                if stage4_numeric_summary:
                    stage4_compact = dict(digest["stages"].get("stage4") or {})
                    if not stage4_compact.get("status"):
                        stage4_compact["status"] = str(stage4_numeric_summary.get("status", "") or "")
                    stage4_compact["numeric_consistency_summary"] = stage4_numeric_summary
                    digest["stages"]["stage4"] = stage4_compact
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
            "operational_metadata_scope": "latest_structured_session_plus_runtime_audit_events_and_session_sinks",
            "authoritative_attempt_truth_note": (
                "Use DB/JSONL/artifact sink join for authoritative attempt truth."
            ),
            "operational_metadata_note": (
                "Operational metadata is best-effort run interpretation and does not override persisted attempt truth."
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
