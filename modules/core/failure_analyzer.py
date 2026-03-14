"""[Log-4] Failure pattern post-analysis utility."""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from pathlib import Path

from modules.core.soft_failure import report_soft_failure


class FailureAnalyzer:
    """Utility for analyzing failure patterns from DB telemetry.

    단일 스레드 설계 — 분석 전용 유틸리티. threading.Lock 불필요.
    """

    def __init__(self, db, project_path: str | Path | None = None) -> None:
        self.db = db
        if project_path is not None:
            self.project_path = Path(project_path)
        else:
            db_path = getattr(db, "db_path", None)
            self.project_path = Path(db_path).parent if db_path else None

    def _report_soft_failure(
        self,
        operation: str,
        exc: Exception,
        *,
        message: str,
        extra: dict | None = None,
    ) -> None:
        log_dir = self.project_path / "logs" if self.project_path is not None else None
        report_soft_failure(
            component="failure_analyzer",
            operation=operation,
            message=message,
            exc=exc,
            degraded=True,
            user_visible=False,
            learnable=True,
            extra=extra,
            log_dir=log_dir,
            warning_window_sec=180.0,
        )

    def summary(self) -> dict:
        """Top-level summary for quick diagnostics."""
        result = {}
        metric_loaders = {
            "stage_pass_rates": lambda: self.stage_pass_rates(),
            "top_failed_agents": lambda: self.most_failed_agents(top_n=5),
            "top_failure_categories": lambda: self.top_failure_categories(top_n=5),
            "advisory_correlations": lambda: self.advisory_reject_correlation(),
            "avg_attempts_by_stage": lambda: self.avg_attempts_by_stage(),
            "failure_prompt_patterns": lambda: self.failure_prompt_patterns(top_n=5),
            "top_success_patterns": lambda: self.top_success_patterns(top_n=3),
            "quality_distribution": lambda: self.quality_distribution(),
            "patch_trace_summary": lambda: self.patch_trace_summary(),
            "sink_alignment_summary": lambda: self.sink_alignment_summary(),
        }
        for key, loader in metric_loaders.items():
            try:
                result[key] = loader()
            except Exception as _e:
                self._report_soft_failure(
                    key,
                    _e,
                    message=f"{key} summary collection failed",
                    extra={"summary_key": key},
                )
                logging.debug("[FailureAnalyzer] %s failed: %s", key, _e)
        return result

    def _load_episode_production_entries(self, min_score: int = 0) -> list[dict]:
        """episode_production.jsonl fallback loader."""
        if self.project_path is None:
            return []

        log_path = self.project_path / "logs" / "episode_production.jsonl"
        if not log_path.exists():
            return []

        entries: list[dict] = []
        try:
            with log_path.open("r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except (TypeError, ValueError, json.JSONDecodeError):
                        continue
                    try:
                        score = int(row.get("final_score", row.get("score", 0)) or 0)
                    except (TypeError, ValueError):
                        score = 0
                    if score < min_score:
                        continue
                    entries.append(row)
        except Exception as _e:
            self._report_soft_failure(
                "load_episode_production_entries",
                _e,
                message="episode_production.jsonl fallback load failed",
            )
            logging.debug("[FailureAnalyzer] episode_production load failed: %s", _e)
            return []
        return entries

    def _load_pass_rate_monitor_entries(self, stage: int | None = None) -> list[dict]:
        """pass_rate_monitor.json loader for cross-sink alignment checks."""
        if self.project_path is None:
            return []

        log_path = self.project_path / "logs" / "pass_rate_monitor.json"
        if not log_path.exists():
            return []

        try:
            payload = json.loads(log_path.read_text(encoding="utf-8"))
        except Exception as _e:
            self._report_soft_failure(
                "load_pass_rate_monitor_entries",
                _e,
                message="pass_rate_monitor.json load failed",
            )
            logging.debug("[FailureAnalyzer] pass_rate_monitor load failed: %s", _e)
            return []

        records = payload.get("records", [])
        if not isinstance(records, list):
            return []

        rows: list[dict] = []
        for row in records:
            if not isinstance(row, dict):
                continue
            if stage is not None:
                try:
                    if int(row.get("stage", 0) or 0) != int(stage):
                        continue
                except (TypeError, ValueError):
                    continue
            rows.append(row)
        return rows

    def _load_session_decision_entries(self, stage: int | None = None) -> list[dict]:
        """decisions.jsonl loader for session-level attempt join checks."""
        if self.project_path is None:
            return []

        log_path = self.project_path / "logs" / "session" / "decisions.jsonl"
        if not log_path.exists():
            return []

        stage_label = f"stage{max(1, int(stage))}" if stage is not None else ""
        entries: list[dict] = []
        try:
            with log_path.open("r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except (TypeError, ValueError, json.JSONDecodeError):
                        continue
                    if stage_label and str(row.get("stage", "") or "").strip().lower() != stage_label:
                        continue
                    meta = row.get("meta", {})
                    if not isinstance(meta, dict):
                        meta = {}
                    entries.append(
                        {
                            "attempt_key": str(meta.get("attempt_key", row.get("attempt_key", "")) or "").strip(),
                            "final_verdict": str(row.get("result", "") or "").strip(),
                            "final_score": self._coerce_int(row.get("score")),
                            "candidate_key": str(meta.get("candidate_key", row.get("candidate_key", "")) or "").strip(),
                            "content_hash": str(meta.get("content_hash", row.get("content_hash", "")) or "").strip(),
                            "artifact_path": str(meta.get("artifact_path", row.get("artifact_path", "")) or "").strip(),
                            "selection_candidate_key": str(
                                meta.get("selection_candidate_key", row.get("selection_candidate_key", "")) or ""
                            ).strip(),
                            "selection_content_hash": str(
                                meta.get("selection_content_hash", row.get("selection_content_hash", "")) or ""
                            ).strip(),
                            "selection_artifact_path": str(
                                meta.get("selection_artifact_path", row.get("selection_artifact_path", "")) or ""
                            ).strip(),
                            "reason": str(meta.get("reason", row.get("reason", "")) or "").strip(),
                            "selection_reason": str(
                                meta.get(
                                    "selection_reason",
                                    row.get("selection_reason", meta.get("reason", row.get("reason", ""))),
                                )
                                or ""
                            ).strip(),
                            "verdict_reason": str(
                                meta.get(
                                    "verdict_reason",
                                    row.get(
                                        "verdict_reason",
                                        meta.get("reason", row.get("reason", meta.get("selection_reason", ""))),
                                    ),
                                )
                                or ""
                            ).strip(),
                            "fix_scope": str(meta.get("fix_scope", row.get("fix_scope", "")) or "").strip(),
                            "runtime_advisory": str(
                                meta.get("runtime_advisory", row.get("runtime_advisory", "")) or ""
                            ).strip(),
                            "retry_directives": str(
                                meta.get("retry_directives", row.get("retry_directives", "")) or ""
                            ).strip(),
                        }
                    )
        except Exception as _e:
            self._report_soft_failure(
                "load_session_decision_entries",
                _e,
                message="session decisions load failed",
            )
            logging.debug("[FailureAnalyzer] decisions.jsonl load failed: %s", _e)
            return []
        return entries

    @staticmethod
    def _coerce_int(value) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _attempt_key_has_session_scope(attempt_key: str) -> bool:
        parts = [part for part in str(attempt_key or "").split(":") if part]
        return len(parts) > 4

    @staticmethod
    def _attempt_key_matches_session_id(attempt_key: str, session_id: str) -> bool:
        normalized_key = str(attempt_key or "").strip()
        normalized_session = str(session_id or "").strip()
        if not normalized_key or not normalized_session:
            return False
        parts = [part for part in normalized_key.split(":") if part]
        if not parts:
            return False
        return parts[-1] == normalized_session

    @staticmethod
    def _compact_examples(values: list[str], limit: int = 5) -> dict:
        if not values:
            return {}
        normalized = sorted(str(value) for value in values if str(value).strip())
        return {"count": len(normalized), "examples": normalized[:limit]}

    @staticmethod
    def _nonempty_value_map(values: dict[str, object]) -> dict[str, str]:
        result: dict[str, str] = {}
        for key, value in values.items():
            normalized = str(value or "").strip()
            if normalized:
                result[key] = normalized
        return result

    @staticmethod
    def _missing_value_sinks(values: dict[str, object]) -> list[str]:
        missing: list[str] = []
        for key, value in values.items():
            if not str(value or "").strip():
                missing.append(str(key))
        return missing

    def _artifact_file_exists(self, artifact_path: str) -> bool | None:
        normalized = str(artifact_path or "").strip()
        if not normalized or self.project_path is None:
            return None
        try:
            return (self.project_path / normalized).exists()
        except Exception:
            return None

    @staticmethod
    def _final_verdict_from_monitor(row: dict) -> str:
        verdict = str(row.get("final_verdict", "") or "").strip()
        if verdict:
            return verdict
        success = row.get("success")
        if success is True:
            return "PASS"
        if success is False:
            return "REJECT"
        return ""

    def sink_alignment_summary(
        self,
        stage: int = 4,
        lookback: int = 100,
        *,
        include_session_decisions: bool = False,
        session_id: str | None = None,
    ) -> dict:
        """Cross-check attempt-key alignment across DB and JSON sinks."""
        stage = max(1, int(stage or 4))
        lookback = max(1, int(lookback or 100))
        session_id = str(session_id or "").strip()

        try:
            if session_id:
                stage_attempt_rows = self.db.conn.execute(
                    """
                    SELECT id, attempt_key, verdict, score, session_id,
                           candidate_key, content_hash, artifact_path
                    FROM stage_attempts
                    WHERE stage = ? AND COALESCE(attempt_key, '') != '' AND session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (stage, session_id, lookback),
                ).fetchall()
            else:
                stage_attempt_rows = self.db.conn.execute(
                    """
                    SELECT id, attempt_key, verdict, score, session_id,
                           candidate_key, content_hash, artifact_path
                    FROM stage_attempts
                    WHERE stage = ? AND COALESCE(attempt_key, '') != ''
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (stage, lookback),
                ).fetchall()
        except Exception as _e:
            self._report_soft_failure(
                "sink_alignment_stage_attempts",
                _e,
                message="stage_attempts load for sink_alignment_summary failed",
                extra={"stage": stage, "session_id": session_id},
            )
            logging.debug("[FailureAnalyzer] sink_alignment stage_attempts failed: %s", _e)
            return {}

        stage_attempts: dict[str, dict] = {}
        for row in stage_attempt_rows:
            attempt_key = str(row["attempt_key"] or "").strip()
            if attempt_key and attempt_key not in stage_attempts:
                stage_attempts[attempt_key] = {
                    "final_verdict": str(row["verdict"] or ""),
                    "final_score": self._coerce_int(row["score"]),
                    "session_id": str(row["session_id"] or "").strip(),
                    "candidate_key": str(row["candidate_key"] or "").strip(),
                    "content_hash": str(row["content_hash"] or "").strip(),
                    "artifact_path": str(row["artifact_path"] or "").strip(),
                }

        pass_rate_monitor: dict[str, dict] = {}
        for row in self._load_pass_rate_monitor_entries(stage=stage)[-lookback:]:
            attempt_key = str(row.get("attempt_key", "") or "").strip()
            if not attempt_key:
                continue
            if session_id and not self._attempt_key_matches_session_id(attempt_key, session_id):
                continue
            pass_rate_monitor[attempt_key] = {
                "final_verdict": self._final_verdict_from_monitor(row),
                "patch_strategy": str(row.get("patch_strategy", "") or ""),
                "structural_attempted": bool(row.get("structural_attempted", False)),
                "candidate_key": str(row.get("candidate_key", "") or "").strip(),
                "content_hash": str(row.get("content_hash", "") or "").strip(),
                "artifact_path": str(row.get("artifact_path", "") or "").strip(),
            }

        director_selections: dict[str, dict] = {}
        if stage in (2, 3, 4):
            try:
                director_rows = self.db.conn.execute(
                    """
                    SELECT id, attempt_key, verdict, score, candidate_key, content_hash, artifact_path,
                           selection_reason, verdict_reason, fix_scope
                    FROM director_selections
                    WHERE COALESCE(stage, CASE WHEN ? = 3 THEN 3 ELSE 4 END) = ? AND COALESCE(attempt_key, '') != ''
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (stage, stage, lookback),
                ).fetchall()
            except Exception as _e:
                self._report_soft_failure(
                    "sink_alignment_director_selections",
                    _e,
                    message="director_selections load for sink_alignment_summary failed",
                    extra={"stage": stage, "session_id": session_id},
                )
                logging.debug("[FailureAnalyzer] sink_alignment director_selections failed: %s", _e)
                director_rows = []
            for row in director_rows:
                attempt_key = str(row["attempt_key"] or "").strip()
                if session_id and not self._attempt_key_matches_session_id(attempt_key, session_id):
                    continue
                if attempt_key and attempt_key not in director_selections:
                    director_selections[attempt_key] = {
                        "initial_verdict": str(row["verdict"] or ""),
                        "initial_score": self._coerce_int(row["score"]),
                        "candidate_key": str(row["candidate_key"] or "").strip(),
                        "content_hash": str(row["content_hash"] or "").strip(),
                        "artifact_path": str(row["artifact_path"] or "").strip(),
                        "selection_reason": str(row["selection_reason"] or "").strip(),
                        "verdict_reason": str(row["verdict_reason"] or "").strip(),
                        "fix_scope": str(row["fix_scope"] or "").strip(),
                    }

        session_decisions: dict[str, dict] = {}
        session_decision_rows_without_attempt_key = 0
        if include_session_decisions:
            for row in self._load_session_decision_entries(stage=stage)[-lookback:]:
                attempt_key = str(row.get("attempt_key", "") or "").strip()
                if not attempt_key:
                    session_decision_rows_without_attempt_key += 1
                    continue
                if session_id and not self._attempt_key_matches_session_id(attempt_key, session_id):
                    continue
                if attempt_key not in session_decisions:
                    session_decisions[attempt_key] = row

        episode_production: dict[str, dict] = {}
        if stage == 4:
            for row in self._load_episode_production_entries(min_score=0)[-lookback:]:
                attempt_key = str(row.get("attempt_key", "") or "").strip()
                if not attempt_key:
                    continue
                if session_id and not self._attempt_key_matches_session_id(attempt_key, session_id):
                    continue
                patch_trace = row.get("patch_trace", {}) or {}
                if not isinstance(patch_trace, dict):
                    patch_trace = {}
                episode_production[attempt_key] = {
                    "initial_verdict": str(row.get("initial_verdict", row.get("verdict", "")) or ""),
                    "final_verdict": str(row.get("final_verdict", row.get("verdict", "")) or ""),
                    "final_score": self._coerce_int(row.get("final_score", row.get("score", 0))),
                    "patch_strategy": str(patch_trace.get("patch_strategy", "") or ""),
                    "candidate_key": str(row.get("candidate_key", "") or "").strip(),
                    "content_hash": str(row.get("content_hash", "") or "").strip(),
                    "artifact_path": str(row.get("artifact_path", "") or "").strip(),
                    "selection_reason": str(row.get("selection_reason", row.get("reason", "")) or "").strip(),
                    "verdict_reason": str(
                        row.get("verdict_reason", row.get("reason", row.get("selection_reason", ""))) or ""
                    ).strip(),
                    "selection_candidate_key": str(
                        row.get("selection_candidate_key", row.get("candidate_key", "")) or ""
                    ).strip(),
                }

        final_union = set(stage_attempts) | set(pass_rate_monitor)
        if include_session_decisions:
            final_union |= set(session_decisions)
        lifecycle_union = set()
        if stage == 4:
            lifecycle_union = set(director_selections) | set(episode_production)
        attempts_considered = final_union | lifecycle_union
        if not attempts_considered and session_decision_rows_without_attempt_key <= 0:
            return {}

        final_missing = {
            "stage_attempts": self._compact_examples(list(final_union - set(stage_attempts))),
            "pass_rate_monitor": self._compact_examples(list(final_union - set(pass_rate_monitor))),
        }
        if include_session_decisions:
            final_missing["session_decisions"] = self._compact_examples(list(final_union - set(session_decisions)))
        final_missing = {key: value for key, value in final_missing.items() if value}

        lifecycle_missing: dict[str, dict] = {}
        lifecycle_missing_in_final: dict[str, dict] = {}
        if lifecycle_union:
            lifecycle_missing = {
                "director_selections": self._compact_examples(list(lifecycle_union - set(director_selections))),
                "episode_production": self._compact_examples(list(lifecycle_union - set(episode_production))),
            }
            lifecycle_missing = {key: value for key, value in lifecycle_missing.items() if value}
            lifecycle_missing_in_final = {
                "stage_attempts": self._compact_examples(list(lifecycle_union - set(stage_attempts))),
                "pass_rate_monitor": self._compact_examples(list(lifecycle_union - set(pass_rate_monitor))),
            }
            lifecycle_missing_in_final = {
                key: value for key, value in lifecycle_missing_in_final.items() if value
            }

        final_verdict_mismatches: list[dict] = []
        final_score_mismatches: list[dict] = []
        initial_verdict_mismatches: list[dict] = []
        patch_strategy_mismatches: list[dict] = []
        candidate_key_mismatches: list[dict] = []
        selection_candidate_key_mismatches: list[dict] = []
        content_hash_mismatches: list[dict] = []
        artifact_path_mismatches: list[dict] = []
        artifact_metadata_missing: list[dict] = []
        selection_reason_mismatches: list[dict] = []
        verdict_reason_mismatches: list[dict] = []
        fix_scope_mismatches: list[dict] = []
        rationale_metadata_missing: list[dict] = []
        artifact_missing_files: list[dict] = []

        for attempt_key in sorted(attempts_considered):
            final_verdicts = {}
            if attempt_key in stage_attempts:
                final_verdicts["stage_attempts"] = stage_attempts[attempt_key]["final_verdict"]
            if attempt_key in pass_rate_monitor:
                final_verdicts["pass_rate_monitor"] = pass_rate_monitor[attempt_key]["final_verdict"]
            if attempt_key in session_decisions:
                final_verdicts["session_decisions"] = session_decisions[attempt_key]["final_verdict"]
            if attempt_key in episode_production:
                final_verdicts["episode_production"] = episode_production[attempt_key]["final_verdict"]
            final_verdicts = {key: value for key, value in final_verdicts.items() if value}
            if len(set(final_verdicts.values())) > 1:
                final_verdict_mismatches.append({"attempt_key": attempt_key, **final_verdicts})

            final_scores = {}
            if attempt_key in stage_attempts and stage_attempts[attempt_key]["final_score"] is not None:
                final_scores["stage_attempts"] = stage_attempts[attempt_key]["final_score"]
            if attempt_key in session_decisions and session_decisions[attempt_key]["final_score"] is not None:
                final_scores["session_decisions"] = session_decisions[attempt_key]["final_score"]
            if attempt_key in episode_production and episode_production[attempt_key]["final_score"] is not None:
                final_scores["episode_production"] = episode_production[attempt_key]["final_score"]
            if len(set(final_scores.values())) > 1:
                final_score_mismatches.append({"attempt_key": attempt_key, **final_scores})

            if attempt_key in director_selections and attempt_key in episode_production:
                ds_verdict = director_selections[attempt_key]["initial_verdict"]
                ep_verdict = episode_production[attempt_key]["initial_verdict"]
                if ds_verdict and ep_verdict and ds_verdict != ep_verdict:
                    initial_verdict_mismatches.append(
                        {
                            "attempt_key": attempt_key,
                            "director_selections": ds_verdict,
                            "episode_production": ep_verdict,
                        }
                    )

            if attempt_key in pass_rate_monitor and attempt_key in episode_production:
                prm_strategy = pass_rate_monitor[attempt_key]["patch_strategy"]
                ep_strategy = episode_production[attempt_key]["patch_strategy"]
                if prm_strategy != ep_strategy:
                    patch_strategy_mismatches.append(
                        {
                            "attempt_key": attempt_key,
                            "pass_rate_monitor": prm_strategy,
                            "episode_production": ep_strategy,
                        }
                    )

            final_artifact_fields: dict[str, dict[str, str]] = {}
            if attempt_key in stage_attempts:
                final_artifact_fields["stage_attempts"] = {
                    "candidate_key": stage_attempts[attempt_key]["candidate_key"],
                    "content_hash": stage_attempts[attempt_key]["content_hash"],
                    "artifact_path": stage_attempts[attempt_key]["artifact_path"],
                }
            if attempt_key in pass_rate_monitor:
                final_artifact_fields["pass_rate_monitor"] = {
                    "candidate_key": pass_rate_monitor[attempt_key]["candidate_key"],
                    "content_hash": pass_rate_monitor[attempt_key]["content_hash"],
                    "artifact_path": pass_rate_monitor[attempt_key]["artifact_path"],
                }
            if attempt_key in session_decisions:
                final_artifact_fields["session_decisions"] = {
                    "candidate_key": session_decisions[attempt_key]["candidate_key"],
                    "content_hash": session_decisions[attempt_key]["content_hash"],
                    "artifact_path": session_decisions[attempt_key]["artifact_path"],
                }
            if attempt_key in episode_production:
                final_artifact_fields["episode_production"] = {
                    "candidate_key": episode_production[attempt_key]["candidate_key"],
                    "content_hash": episode_production[attempt_key]["content_hash"],
                    "artifact_path": episode_production[attempt_key]["artifact_path"],
                }

            if final_artifact_fields:
                for field_name, collector in (
                    ("candidate_key", candidate_key_mismatches),
                    ("content_hash", content_hash_mismatches),
                    ("artifact_path", artifact_path_mismatches),
                ):
                    values_by_sink = {sink: payload.get(field_name, "") for sink, payload in final_artifact_fields.items()}
                    nonempty_values = self._nonempty_value_map(values_by_sink)
                    if len(set(nonempty_values.values())) > 1:
                        collector.append({"attempt_key": attempt_key, **nonempty_values})
                    missing_sinks = self._missing_value_sinks(values_by_sink)
                    if missing_sinks:
                        artifact_metadata_missing.append(
                            {
                                "attempt_key": attempt_key,
                                "field": field_name,
                                "sinks": missing_sinks,
                            }
                        )

                for sink_name, payload in final_artifact_fields.items():
                    artifact_path = str(payload.get("artifact_path", "") or "").strip()
                    if not artifact_path:
                        continue
                    file_exists = self._artifact_file_exists(artifact_path)
                    if file_exists is False:
                        artifact_missing_files.append(
                            {
                                "attempt_key": attempt_key,
                                "sink": sink_name,
                                "artifact_path": artifact_path,
                            }
                        )

            if attempt_key in director_selections and attempt_key in episode_production:
                ds_candidate_key = str(director_selections[attempt_key]["candidate_key"] or "").strip()
                ep_candidate_key = str(episode_production[attempt_key]["selection_candidate_key"] or "").strip()
                if ds_candidate_key and ep_candidate_key and ds_candidate_key != ep_candidate_key:
                    selection_candidate_key_mismatches.append(
                        {
                            "attempt_key": attempt_key,
                            "director_selections": ds_candidate_key,
                            "episode_production": ep_candidate_key,
                        }
                    )

            if include_session_decisions:
                rationale_values_by_field: dict[str, dict[str, str]] = {}
                if attempt_key in director_selections:
                    rationale_values_by_field.setdefault("selection_reason", {})[
                        "director_selections"
                    ] = director_selections[attempt_key]["selection_reason"]
                    rationale_values_by_field.setdefault("verdict_reason", {})[
                        "director_selections"
                    ] = director_selections[attempt_key]["verdict_reason"]
                    rationale_values_by_field.setdefault("fix_scope", {})[
                        "director_selections"
                    ] = director_selections[attempt_key]["fix_scope"]
                if attempt_key in session_decisions:
                    rationale_values_by_field.setdefault("selection_reason", {})[
                        "session_decisions"
                    ] = str(session_decisions[attempt_key].get("selection_reason", "") or "").strip()
                    rationale_values_by_field.setdefault("verdict_reason", {})[
                        "session_decisions"
                    ] = str(session_decisions[attempt_key].get("verdict_reason", "") or "").strip()
                    rationale_values_by_field.setdefault("fix_scope", {})[
                        "session_decisions"
                    ] = str(session_decisions[attempt_key].get("fix_scope", "") or "").strip()
                if attempt_key in episode_production:
                    rationale_values_by_field.setdefault("selection_reason", {})[
                        "episode_production"
                    ] = str(episode_production[attempt_key].get("selection_reason", "") or "").strip()
                    rationale_values_by_field.setdefault("verdict_reason", {})[
                        "episode_production"
                    ] = str(episode_production[attempt_key].get("verdict_reason", "") or "").strip()

                for field_name, collector in (
                    ("selection_reason", selection_reason_mismatches),
                    ("verdict_reason", verdict_reason_mismatches),
                    ("fix_scope", fix_scope_mismatches),
                ):
                    values_by_sink = rationale_values_by_field.get(field_name, {})
                    if len(values_by_sink) < 2:
                        continue
                    nonempty_values = self._nonempty_value_map(values_by_sink)
                    if len(set(nonempty_values.values())) > 1:
                        collector.append({"attempt_key": attempt_key, **nonempty_values})
                    missing_sinks = self._missing_value_sinks(values_by_sink)
                    if missing_sinks and nonempty_values:
                        rationale_metadata_missing.append(
                            {
                                "attempt_key": attempt_key,
                                "field": field_name,
                                "sinks": missing_sinks,
                            }
                        )

        session_scoped_attempts = sum(
            1 for attempt_key in attempts_considered if self._attempt_key_has_session_scope(attempt_key)
        )
        complete_final_attempts = sum(
            1 for attempt_key in final_union if attempt_key in stage_attempts and attempt_key in pass_rate_monitor
        )
        complete_lifecycle_attempts = sum(
            1
            for attempt_key in lifecycle_union
            if attempt_key in director_selections and attempt_key in episode_production
        )

        has_issues = any(
            (
                final_missing,
                lifecycle_missing,
                lifecycle_missing_in_final,
                final_verdict_mismatches,
                final_score_mismatches,
                initial_verdict_mismatches,
                patch_strategy_mismatches,
                candidate_key_mismatches,
                selection_candidate_key_mismatches,
                content_hash_mismatches,
                artifact_path_mismatches,
                artifact_metadata_missing,
                selection_reason_mismatches,
                verdict_reason_mismatches,
                fix_scope_mismatches,
                rationale_metadata_missing,
                artifact_missing_files,
                session_decision_rows_without_attempt_key > 0,
            )
        )

        return {
            "stage": stage,
            "session_filter": session_id,
            "attempts_considered": len(attempts_considered),
            "coverage": {
                "stage_attempts": len(stage_attempts),
                "pass_rate_monitor": len(pass_rate_monitor),
                "director_selections": len(director_selections),
                "episode_production": len(episode_production),
                "session_decisions": len(session_decisions),
            },
            "complete_final_attempts": complete_final_attempts,
            "director_lifecycle_attempts": len(lifecycle_union),
            "complete_lifecycle_attempts": complete_lifecycle_attempts,
            "final_sink_missing": final_missing,
            "lifecycle_sink_missing": lifecycle_missing,
            "lifecycle_missing_in_final_sinks": lifecycle_missing_in_final,
            "final_verdict_mismatches": final_verdict_mismatches[:10],
            "final_score_mismatches": final_score_mismatches[:10],
            "initial_verdict_mismatches": initial_verdict_mismatches[:10],
            "patch_strategy_mismatches": patch_strategy_mismatches[:10],
            "candidate_key_mismatches": candidate_key_mismatches[:10],
            "selection_candidate_key_mismatches": selection_candidate_key_mismatches[:10],
            "content_hash_mismatches": content_hash_mismatches[:10],
            "artifact_path_mismatches": artifact_path_mismatches[:10],
            "artifact_metadata_missing": artifact_metadata_missing[:10],
            "selection_reason_mismatches": selection_reason_mismatches[:10],
            "verdict_reason_mismatches": verdict_reason_mismatches[:10],
            "fix_scope_mismatches": fix_scope_mismatches[:10],
            "rationale_metadata_missing": rationale_metadata_missing[:10],
            "artifact_missing_files": artifact_missing_files[:10],
            "session_scoped_attempts": session_scoped_attempts,
            "legacy_key_attempts": len(attempts_considered) - session_scoped_attempts,
            "session_decision_rows_without_attempt_key": session_decision_rows_without_attempt_key,
            "status": "warn" if has_issues else "ok",
        }

    def top_success_patterns(self, top_n: int = 5, min_score: int = 90) -> list[dict]:
        """고득점 에피소드의 공통 품질 패턴 요약."""
        rows: list[dict] = []
        try:
            db_rows = self.db.conn.execute(
                """SELECT ep_num, score, verdict, selection_reason, open_review,
                          score_breakdown, consistency_checklist
                   FROM episode_quality_labels
                   WHERE score >= ?
                   ORDER BY score DESC, ep_num DESC
                   LIMIT ?""",
                (min_score, max(top_n * 3, 6)),
            ).fetchall()
            for row in db_rows:
                item = dict(row)
                for field in ("score_breakdown", "consistency_checklist"):
                    try:
                        item[field] = json.loads(item.get(field) or "{}")
                    except (TypeError, ValueError, json.JSONDecodeError):
                        item[field] = {}
                rows.append(item)
        except Exception as _e:
            self._report_soft_failure(
                "top_success_patterns",
                _e,
                message="quality label query for top_success_patterns failed",
            )
            logging.debug("[FailureAnalyzer] top_success_patterns DB fallback: %s", _e)

        if not rows:
            for entry in self._load_episode_production_entries(min_score=min_score):
                verdict = str(entry.get("final_verdict", entry.get("verdict", "")) or "")
                if verdict not in ("PASS", "PASS_WITH_WARNING"):
                    continue
                rows.append(
                    {
                        "ep_num": entry.get("ep"),
                        "score": entry.get("final_score", entry.get("score", 0)),
                        "verdict": verdict,
                        "selection_reason": entry.get("reason", ""),
                        "open_review": entry.get("open_review", ""),
                        "score_breakdown": entry.get("score_breakdown", {}) or {},
                        "consistency_checklist": entry.get("consistency_checklist", {}) or {},
                    }
                )

        if not rows:
            return []

        score_totals: dict[str, float] = defaultdict(float)
        score_counts: dict[str, int] = defaultdict(int)
        checklist_ok: dict[str, int] = defaultdict(int)
        checklist_total: dict[str, int] = defaultdict(int)
        keyword_counts: dict[str, int] = defaultdict(int)
        stopwords = {"그리고", "그러나", "이번", "장면", "서사", "원고", "후보", "score", "review"}

        for row in rows:
            for key, value in (row.get("score_breakdown") or {}).items():
                if isinstance(value, int | float):
                    score_totals[key] += float(value)
                    score_counts[key] += 1
            for key, verdict in (row.get("consistency_checklist") or {}).items():
                verdict_text = str(verdict or "").upper()
                if verdict_text in {"OK", "ISSUE"}:
                    checklist_total[key] += 1
                    if verdict_text == "OK":
                        checklist_ok[key] += 1
            reason_text = " ".join(
                str(row.get(field, "") or "") for field in ("selection_reason", "open_review")
            )
            tokens = {
                token
                for token in re.findall(r"[가-힣A-Za-z]{2,}", reason_text)
                if token.lower() not in stopwords
            }
            for token in tokens:
                keyword_counts[token] += 1

        patterns: list[dict] = []
        axis_avgs = sorted(
            (
                (key, round(score_totals[key] / score_counts[key], 1))
                for key in score_totals
                if score_counts[key] > 0
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        for key, avg in axis_avgs[:2]:
            patterns.append(
                {
                    "pattern": key,
                    "count": len(rows),
                    "description": f"{key} 평균 {avg}점",
                }
            )

        stable_keys = [
            key
            for key, total in checklist_total.items()
            if total > 0 and checklist_ok[key] / total >= 0.8
        ]
        if stable_keys:
            patterns.append(
                {
                    "pattern": "stable_checklist",
                    "count": len(rows),
                    "description": "OK 비율 높음: " + ", ".join(sorted(stable_keys)[:4]),
                }
            )

        common_keywords = [key for key, count in sorted(keyword_counts.items(), key=lambda item: item[1], reverse=True) if count >= 2]
        if common_keywords:
            patterns.append(
                {
                    "pattern": "selection_reason_keywords",
                    "count": len(rows),
                    "description": "반복 키워드: " + ", ".join(common_keywords[:4]),
                }
            )

        return patterns[:top_n]

    def quality_distribution(self, lookback: int = 100) -> dict:
        """정규화된 품질 라벨 분포 요약."""
        rows: list[dict] = []
        try:
            db_rows = self.db.conn.execute(
                """SELECT score, verdict, score_breakdown
                   FROM episode_quality_labels
                   ORDER BY ep_num DESC
                   LIMIT ?""",
                (lookback,),
            ).fetchall()
            for row in db_rows:
                item = dict(row)
                try:
                    item["score_breakdown"] = json.loads(item.get("score_breakdown") or "{}")
                except (TypeError, ValueError, json.JSONDecodeError):
                    item["score_breakdown"] = {}
                rows.append(item)
        except Exception as _e:
            self._report_soft_failure(
                "quality_distribution",
                _e,
                message="quality_distribution DB query failed",
            )
            logging.debug("[FailureAnalyzer] quality_distribution DB fallback: %s", _e)

        if not rows:
            for entry in self._load_episode_production_entries(min_score=0)[-lookback:]:
                rows.append(
                    {
                        "score": entry.get("final_score", entry.get("score", 0)),
                        "verdict": entry.get("final_verdict", entry.get("verdict", "")),
                        "initial_verdict": entry.get("initial_verdict", entry.get("verdict", "")),
                        "score_breakdown": entry.get("score_breakdown", {}) or {},
                    }
                )

        if not rows:
            return {}

        scores = []
        breakdown_sum: dict[str, float] = defaultdict(float)
        breakdown_count: dict[str, int] = defaultdict(int)
        pass_with_fix_count = 0
        high_score_count = 0
        for row in rows:
            try:
                score = int(row.get("score", 0) or 0)
            except (TypeError, ValueError):
                score = 0
            scores.append(score)
            if score >= 90:
                high_score_count += 1
            if str(row.get("initial_verdict", row.get("verdict", "")) or "") == "PASS_WITH_FIX":
                pass_with_fix_count += 1
            for key, value in (row.get("score_breakdown") or {}).items():
                if isinstance(value, int | float):
                    breakdown_sum[key] += float(value)
                    breakdown_count[key] += 1

        return {
            "count": len(rows),
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
            "high_score_count": high_score_count,
            "pass_with_fix_count": pass_with_fix_count,
            "avg_breakdown": {
                key: round(breakdown_sum[key] / breakdown_count[key], 1)
                for key in breakdown_sum
                if breakdown_count[key] > 0
            },
        }

    def patch_trace_summary(self, lookback: int = 100) -> dict:
        """Summarize patch behavior from episode_production patch_trace payloads."""
        entries = self._load_episode_production_entries(min_score=0)
        if not entries:
            return {}

        rows = entries[-lookback:] if lookback else entries
        patch_rows: list[dict] = []
        for entry in rows:
            patch_trace = entry.get("patch_trace", {}) or {}
            flags = entry.get("flags", {}) or {}
            if not isinstance(patch_trace, dict):
                patch_trace = {}
            if not isinstance(flags, dict):
                flags = {}

            patch_strategy = str(patch_trace.get("patch_strategy", "") or "")
            structural_attempted = bool(patch_trace.get("structural_attempted", False))
            if not patch_strategy and not structural_attempted and not bool(flags.get("patch_mode", False)):
                continue

            patch_rows.append(
                {
                    "patch_strategy": patch_strategy,
                    "patch_targets": list(patch_trace.get("patch_targets") or []),
                    "fallback_reason": str(patch_trace.get("fallback_reason", "") or ""),
                    "focus": str(patch_trace.get("focus", "") or ""),
                    "structural_attempted": structural_attempted,
                    "unchanged_ratio": patch_trace.get("unchanged_ratio"),
                    "final_verdict": str(entry.get("final_verdict", entry.get("verdict", "")) or ""),
                }
            )

        if not patch_rows:
            return {}

        strategy_counts: dict[str, int] = defaultdict(int)
        fallback_counts: dict[str, int] = defaultdict(int)
        focus_counts: dict[str, int] = defaultdict(int)
        target_counts: dict[str, int] = defaultdict(int)
        unchanged_ratios: list[float] = []
        final_pass = 0
        final_reject = 0
        structural_attempted_count = 0

        for row in patch_rows:
            strategy = row["patch_strategy"]
            if strategy:
                strategy_counts[strategy] += 1
            fallback_reason = row["fallback_reason"]
            if fallback_reason:
                fallback_counts[fallback_reason] += 1
            focus = row["focus"]
            if focus:
                focus_counts[focus] += 1
            for target in row["patch_targets"]:
                target_text = str(target or "").strip()
                if target_text:
                    target_counts[target_text] += 1
            try:
                unchanged_ratio = float(row["unchanged_ratio"])
            except (TypeError, ValueError):
                unchanged_ratio = None
            if unchanged_ratio is not None:
                unchanged_ratios.append(unchanged_ratio)
            if row["structural_attempted"]:
                structural_attempted_count += 1
            if row["final_verdict"] in {"PASS", "PASS_WITH_WARNING"}:
                final_pass += 1
            elif row["final_verdict"] == "REJECT":
                final_reject += 1

        return {
            "count": len(patch_rows),
            "structural_attempted_count": structural_attempted_count,
            "final_pass": final_pass,
            "final_reject": final_reject,
            "avg_unchanged_ratio": round(sum(unchanged_ratios) / len(unchanged_ratios), 4)
            if unchanged_ratios
            else None,
            "strategy_counts": dict(sorted(strategy_counts.items())),
            "fallback_reasons": dict(sorted(fallback_counts.items())),
            "focus_counts": dict(sorted(focus_counts.items())),
            "top_patch_targets": [
                {"target": target, "count": count}
                for target, count in sorted(target_counts.items(), key=lambda item: (-item[1], item[0]))[:5]
            ],
        }

    def compare_versions(
        self,
        version_a: str,
        version_b: str,
        *,
        stage: int | None = None,
        lookback: int = 200,
    ) -> dict:
        """Compare pass-rate and score deltas between two prompt-version tags."""
        version_a = str(version_a or "").strip()
        version_b = str(version_b or "").strip()
        if not version_a or not version_b:
            return {}

        clauses = ["prompt_version IN (?, ?)"]
        params: list = [version_a, version_b]
        if stage is not None:
            clauses.append("stage = ?")
            params.append(stage)
        where_sql = " AND ".join(clauses)
        params.append(max(int(lookback or 0), 1))

        try:
            rows = self.db.conn.execute(
                f"""SELECT prompt_version, verdict, score
                    FROM (
                        SELECT prompt_version, verdict, score, id
                        FROM stage_attempts
                        WHERE {where_sql}
                        ORDER BY id DESC
                        LIMIT ?
                    ) recent""",
                tuple(params),
            ).fetchall()
        except Exception as _e:
            logging.debug("[FailureAnalyzer] compare_versions: %s", _e)
            return {}

        if not rows:
            return {}

        stats = {
            version_a: {"attempts": 0, "pass": 0, "reject": 0, "scores": []},
            version_b: {"attempts": 0, "pass": 0, "reject": 0, "scores": []},
        }
        for row in rows:
            version = str(row["prompt_version"] or "")
            if version not in stats:
                continue
            stats[version]["attempts"] += 1
            verdict = str(row["verdict"] or "")
            if verdict in {"PASS", "PASS_WITH_WARNING"}:
                stats[version]["pass"] += 1
            elif verdict == "REJECT":
                stats[version]["reject"] += 1
            try:
                score = int(row["score"])
            except (TypeError, ValueError):
                score = None
            if score is not None:
                stats[version]["scores"].append(score)

        versions: dict[str, dict] = {}
        for version, data in stats.items():
            attempts = int(data["attempts"])
            scores = data["scores"]
            versions[version] = {
                "attempts": attempts,
                "pass": int(data["pass"]),
                "reject": int(data["reject"]),
                "pass_rate_pct": round((data["pass"] / attempts) * 100, 1) if attempts else 0.0,
                "avg_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
            }

        delta_pass_rate = round(
            versions[version_b]["pass_rate_pct"] - versions[version_a]["pass_rate_pct"],
            1,
        )
        delta_avg_score = round(
            versions[version_b]["avg_score"] - versions[version_a]["avg_score"],
            1,
        )

        winner = None
        if versions[version_a]["attempts"] and versions[version_b]["attempts"]:
            if (versions[version_b]["pass_rate_pct"], versions[version_b]["avg_score"]) > (
                versions[version_a]["pass_rate_pct"],
                versions[version_a]["avg_score"],
            ):
                winner = version_b
            elif (versions[version_a]["pass_rate_pct"], versions[version_a]["avg_score"]) > (
                versions[version_b]["pass_rate_pct"],
                versions[version_b]["avg_score"],
            ):
                winner = version_a

        return {
            "versions": versions,
            "pass_rate_delta_pct": delta_pass_rate,
            "avg_score_delta": delta_avg_score,
            "winner": winner,
        }

    def stage_pass_rates(self) -> dict:
        """Per-stage attempt/pass/reject rates."""
        try:
            rows = self.db.conn.execute(
                """SELECT stage, verdict, COUNT(*) as cnt
                   FROM stage_attempts GROUP BY stage, verdict"""
            ).fetchall()
            if not rows:
                return {}
            by_stage: dict[int, dict] = defaultdict(lambda: defaultdict(int))
            for r in rows:
                by_stage[r["stage"]][r["verdict"]] += r["cnt"]
            result = {}
            for stage, counts in sorted(by_stage.items()):
                total = sum(counts.values())
                passes = counts.get("PASS", 0) + counts.get("PASS_WITH_WARNING", 0)
                result[f"stage_{stage}"] = {
                    "total_attempts": total,
                    "pass": passes,
                    "reject": counts.get("REJECT", 0),
                    "pass_with_fix_transient": counts.get("PASS_WITH_FIX", 0),
                    "pass_rate_pct": round(passes / total * 100, 1) if total else 0,
                }
            return result
        except Exception as _e:
            logging.debug("[FailureAnalyzer] stage_pass_rates: %s", _e)
            return {}

    def avg_attempts_by_stage(self) -> dict:
        """Average max attempt count per episode by stage."""
        try:
            rows = self.db.conn.execute(
                """SELECT stage, ep_num, MAX(attempt_num) as max_attempt
                   FROM stage_attempts GROUP BY stage, ep_num"""
            ).fetchall()
            if not rows:
                return {}
            by_stage: dict[int, list] = defaultdict(list)
            for r in rows:
                by_stage[r["stage"]].append(r["max_attempt"])
            return {f"stage_{s}": round(sum(v) / len(v), 2) if v else 0 for s, v in sorted(by_stage.items())}
        except Exception as _e:
            logging.debug("[FailureAnalyzer] avg_attempts_by_stage: %s", _e)
            return {}

    def most_failed_agents(self, top_n: int = 10) -> list[dict]:
        """Top agents by absolute failure counts."""
        try:
            rows = self.db.conn.execute(
                """SELECT agent_name, model,
                          SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failures,
                          COUNT(*) as total,
                          AVG(duration_ms) as avg_ms
                   FROM llm_calls
                   GROUP BY agent_name, model
                   ORDER BY failures DESC
                   LIMIT ?""",
                (top_n,),
            ).fetchall()
            return [
                {
                    "agent": r["agent_name"],
                    "model": r["model"],
                    "failures": r["failures"],
                    "total": r["total"],
                    "fail_rate_pct": round(r["failures"] / r["total"] * 100, 1) if r["total"] else 0,
                    "avg_duration_ms": int(r["avg_ms"] or 0),
                }
                for r in rows
            ]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] most_failed_agents: %s", _e)
            return []

    def slowest_agents(self, top_n: int = 10) -> list[dict]:
        """Top agents by average successful latency."""
        try:
            rows = self.db.conn.execute(
                """SELECT agent_name, model,
                          AVG(duration_ms) as avg_ms,
                          MAX(duration_ms) as max_ms,
                          COUNT(*) as total
                   FROM llm_calls WHERE success=1
                   GROUP BY agent_name, model
                   ORDER BY avg_ms DESC LIMIT ?""",
                (top_n,),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] slowest_agents: %s", _e)
            return []

    def agent_error_types(self) -> dict:
        """Error type distribution grouped by agent."""
        try:
            rows = self.db.conn.execute(
                """SELECT agent_name, error_type, COUNT(*) as cnt
                   FROM llm_calls WHERE success=0 AND error_type IS NOT NULL
                   GROUP BY agent_name, error_type
                   ORDER BY cnt DESC"""
            ).fetchall()
            result: dict[str, dict] = defaultdict(dict)
            for r in rows:
                result[r["agent_name"]][r["error_type"]] = r["cnt"]
            return dict(result)
        except Exception as _e:
            logging.debug("[FailureAnalyzer] agent_error_types: %s", _e)
            return {}

    def failed_call_snippets(self, agent_name: str | None = None, top_n: int = 20) -> list[dict]:
        """Recent failed-call prompt/response snippets for root-cause tracing."""
        try:
            if agent_name:
                rows = self.db.conn.execute(
                    """SELECT ts, agent_name, model, ep_num, stage,
                              error_type, error_msg,
                              prompt_snippet, response_snippet,
                              prompt_chars, response_chars, duration_ms
                       FROM llm_calls
                       WHERE success=0 AND prompt_snippet IS NOT NULL
                         AND agent_name=?
                       ORDER BY ts DESC LIMIT ?""",
                    (agent_name, top_n),
                ).fetchall()
            else:
                rows = self.db.conn.execute(
                    """SELECT ts, agent_name, model, ep_num, stage,
                              error_type, error_msg,
                              prompt_snippet, response_snippet,
                              prompt_chars, response_chars, duration_ms
                       FROM llm_calls
                       WHERE success=0 AND prompt_snippet IS NOT NULL
                       ORDER BY ts DESC LIMIT ?""",
                    (top_n,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] failed_call_snippets: %s", _e)
            return []

    def failure_prompt_patterns(self, top_n: int = 10) -> list[dict]:
        """Failure prompt-size/response-size distribution by agent."""
        try:
            rows = self.db.conn.execute(
                """SELECT agent_name,
                          COUNT(*) as fail_count,
                          AVG(prompt_chars) as avg_prompt_chars,
                          MAX(prompt_chars) as max_prompt_chars,
                          AVG(response_chars) as avg_resp_chars
                   FROM llm_calls
                   WHERE success=0
                   GROUP BY agent_name
                   ORDER BY fail_count DESC LIMIT ?""",
                (top_n,),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] failure_prompt_patterns: %s", _e)
            return []

    def top_failure_categories(self, top_n: int = 10, stage: int | None = None) -> list[dict]:
        """Top reject categories from stage attempts."""
        try:
            if stage is not None:
                rows = self.db.conn.execute(
                    """SELECT failure_category, COUNT(*) as cnt
                       FROM stage_attempts
                       WHERE verdict='REJECT' AND failure_category IS NOT NULL AND stage=?
                       GROUP BY failure_category ORDER BY cnt DESC LIMIT ?""",
                    (stage, top_n),
                ).fetchall()
            else:
                rows = self.db.conn.execute(
                    """SELECT failure_category, COUNT(*) as cnt
                       FROM stage_attempts
                       WHERE verdict='REJECT' AND failure_category IS NOT NULL
                       GROUP BY failure_category ORDER BY cnt DESC LIMIT ?""",
                    (top_n,),
                ).fetchall()
            return [{"category": r["failure_category"], "count": r["cnt"]} for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] top_failure_categories: %s", _e)
            return []

    def failure_trend_by_episode(self) -> list[dict]:
        """Reject rate trend by episode."""
        try:
            rows = self.db.conn.execute(
                """SELECT ep_num,
                          SUM(CASE WHEN verdict='REJECT' THEN 1 ELSE 0 END) as rejects,
                          COUNT(*) as total
                   FROM stage_attempts
                   WHERE ep_num IS NOT NULL
                   GROUP BY ep_num ORDER BY ep_num"""
            ).fetchall()
            return [
                {
                    "ep": r["ep_num"],
                    "rejects": r["rejects"],
                    "total": r["total"],
                    "reject_rate_pct": round(r["rejects"] / r["total"] * 100, 1) if r["total"] else 0,
                }
                for r in rows
            ]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] failure_trend_by_episode: %s", _e)
            return []

    def advisory_reject_correlation(self) -> dict:
        """Compare reject rates when each advisory flag is triggered vs not triggered."""
        try:
            rows = self.db.conn.execute(
                """SELECT advisory_warnings, verdict
                   FROM director_selections
                   WHERE advisory_warnings IS NOT NULL"""
            ).fetchall()
            if not rows:
                return {}

            advisory_types = [
                "truth_gate",
                "npc_drift",
                "numeric_drift",
                "rel_drift",
                "flashback",
                "info_paradox",
                "long_term_rep",
            ]
            result = {}
            for adv_type in advisory_types:
                with_adv_pass = with_adv_reject = without_adv_pass = without_adv_reject = 0
                for r in rows:
                    try:
                        flags = json.loads(r["advisory_warnings"] or "{}")
                    except (json.JSONDecodeError, TypeError):
                        continue
                    has_flag = bool(flags.get(adv_type))
                    is_reject = r["verdict"] == "REJECT"
                    if has_flag:
                        if is_reject:
                            with_adv_reject += 1
                        else:
                            with_adv_pass += 1
                    else:
                        if is_reject:
                            without_adv_reject += 1
                        else:
                            without_adv_pass += 1

                total_with = with_adv_pass + with_adv_reject
                total_without = without_adv_pass + without_adv_reject
                if total_with == 0:
                    continue
                result[adv_type] = {
                    "triggered_count": total_with,
                    "reject_rate_when_triggered_pct": round(with_adv_reject / total_with * 100, 1),
                    "reject_rate_when_not_triggered_pct": (
                        round(without_adv_reject / total_without * 100, 1) if total_without else 0
                    ),
                    "signal_lift": round(
                        (with_adv_reject / total_with) / (without_adv_reject / total_without)
                        if total_without and without_adv_reject
                        else 0,
                        2,
                    ),
                }
            return result
        except Exception as _e:
            logging.debug("[FailureAnalyzer] advisory_reject_correlation: %s", _e)
            return {}

    def model_performance(self) -> dict:
        """Model-level success/latency/response-size summary."""
        try:
            rows = self.db.conn.execute(
                """SELECT model,
                          SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successes,
                          COUNT(*) as total,
                          AVG(duration_ms) as avg_ms,
                          AVG(response_chars) as avg_resp_chars
                   FROM llm_calls
                   GROUP BY model ORDER BY total DESC"""
            ).fetchall()
            if not rows:
                return {}
            return {
                r["model"]: {
                    "total_calls": r["total"],
                    "success_rate_pct": round(r["successes"] / r["total"] * 100, 1) if r["total"] else 0,
                    "avg_duration_ms": int(r["avg_ms"] or 0),
                    "avg_response_chars": int(r["avg_resp_chars"] or 0),
                }
                for r in rows
            }
        except Exception as _e:
            logging.debug("[FailureAnalyzer] model_performance: %s", _e)
            return {}

    def large_prompt_calls(self, threshold_chars: int = 50000, top_n: int = 20) -> list[dict]:
        """Calls with unusually large prompt payloads."""
        try:
            rows = self.db.conn.execute(
                """SELECT ts, agent_name, model, ep_num, stage,
                          prompt_chars, response_chars, duration_ms, context_tag
                   FROM llm_calls
                   WHERE prompt_chars >= ?
                   ORDER BY prompt_chars DESC LIMIT ?""",
                (threshold_chars, top_n),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] large_prompt_calls: %s", _e)
            return []

    def empty_response_calls(self) -> list[dict]:
        """Successful API calls with near-empty responses."""
        try:
            rows = self.db.conn.execute(
                """SELECT ts, agent_name, model, ep_num, stage,
                          prompt_chars, response_chars, error_type, error_msg
                   FROM llm_calls
                   WHERE success=1 AND (response_chars IS NULL OR response_chars < 50)
                   ORDER BY ts DESC LIMIT 50"""
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] empty_response_calls: %s", _e)
            return []

    @staticmethod
    def _collect_suffix_candidates(unmatched: list[str], min_count: int = 2) -> list[dict]:
        """미매칭 아이템 목록에서 접미사 후보(count/examples) 추출."""
        counts: dict[str, int] = {}
        examples: dict[str, list[str]] = {}

        for raw_name in unmatched:
            name = str(raw_name).strip()
            if len(name) < 2:
                continue
            for length in (1, 2, 3):
                if len(name) <= length:
                    continue
                suffix = name[-length:]
                counts[suffix] = counts.get(suffix, 0) + 1
                bucket = examples.setdefault(suffix, [])
                if len(bucket) < 3 and name not in bucket:
                    bucket.append(name)

        rows = []
        for suffix, cnt in counts.items():
            if cnt >= min_count:
                rows.append({"suffix": suffix, "count": cnt, "examples": examples.get(suffix, [])})

        rows.sort(key=lambda row: (-int(row["count"]), len(str(row["suffix"])), str(row["suffix"])))
        return rows

    def item_suffix_gap_report(self, registry, genre: str = "") -> dict:
        """아이템 접미사 안전망 갭 리포트 생성."""
        try:
            total_items = len(getattr(registry, "items", {}) or {})
            if not registry or not hasattr(registry, "get_unmatched_items"):
                return {"total_items": total_items, "unmatched_count": 0, "unmatched": [], "suggested_suffixes": []}

            unmatched = registry.get_unmatched_items(genre)
            if not isinstance(unmatched, list):
                unmatched = []

            candidates = self._collect_suffix_candidates(unmatched, min_count=2)
            suggested = [str(row.get("suffix", "")).strip() for row in candidates if str(row.get("suffix", "")).strip()]

            return {
                "total_items": total_items,
                "unmatched_count": len(unmatched),
                "unmatched": unmatched[:30],
                "suggested_suffixes": suggested[:10],
            }
        except Exception as _e:
            logging.debug("[FailureAnalyzer] item_suffix_gap_report: %s", _e)
            return {"total_items": 0, "unmatched_count": 0, "unmatched": [], "suggested_suffixes": []}

    @staticmethod
    def _parse_json_array_response(raw_text: str) -> list[dict]:
        """LLM 텍스트에서 JSON 배열 파싱."""
        if not raw_text:
            return []
        raw_text = str(raw_text).strip()
        if not raw_text:
            return []

        try:
            parsed = json.loads(raw_text)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            pass

        m = re.search(r"\[[\s\S]*\]", raw_text)
        if not m:
            return []

        try:
            parsed = json.loads(m.group(0))
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    def review_suffix_candidates(self, candidates: list[dict], llm_ask=None) -> list[dict]:
        """미매칭 아이템 접미사 후보를 LLM으로 배치 심사.

        Args:
            candidates: [{"suffix": str, "examples": list[str], "count": int}, ...]
            llm_ask: prompt(str) -> response(str) callable

        Returns:
            [{"suffix": str, "verdict": "APPROVE"|"REJECT", "reason": str}, ...]
        """
        if not candidates:
            return []

        normalized: list[dict] = []
        for row in candidates[:10]:
            if not isinstance(row, dict):
                continue
            suffix = str(row.get("suffix", "")).strip()
            if not suffix:
                continue

            raw_examples = row.get("examples", [])
            if not isinstance(raw_examples, list):
                raw_examples = [raw_examples]
            examples = [str(x).strip() for x in raw_examples if str(x).strip()][:5]

            try:
                count = int(row.get("count", len(examples)))
            except (TypeError, ValueError):
                count = len(examples)

            normalized.append({"suffix": suffix, "examples": examples, "count": max(1, count)})

        if not normalized:
            return []

        if llm_ask is None:
            return [
                {"suffix": row["suffix"], "verdict": "REJECT", "reason": "llm_ask 콜백 없음 (수동 검토 필요)"}
                for row in normalized
            ]

        prompt = (
            "다음은 웹소설 아이템 regex 안전망에 추가할 접미사 후보 목록입니다.\n"
            '각 후보에 대해 "일반적인 아이템/도구/장비의 접미사로 적합한가?"를 판정해 주세요.\n\n'
            "판정 기준:\n"
            '- APPROVE: 해당 접미사가 아이템 카테고리를 나타냄 (예: "칼", "서", "증")\n'
            '- REJECT: 고유명사/브랜드/우연의 일치 (예: "프로", "플러스", "맥스")\n\n'
            "후보 목록:\n"
            f"{json.dumps(normalized, ensure_ascii=False, indent=2)}\n\n"
            'JSON 배열로 응답: [{"suffix":"...","verdict":"APPROVE"|"REJECT","reason":"..."}]'
        )

        try:
            raw = llm_ask(prompt) or ""
        except Exception as _e:
            logging.debug("[FailureAnalyzer] review_suffix_candidates llm_ask failed: %s", _e)
            raw = ""

        parsed = self._parse_json_array_response(raw)
        parsed_map: dict[str, dict] = {}
        for row in parsed:
            if not isinstance(row, dict):
                continue
            suffix = str(row.get("suffix", "")).strip()
            if not suffix:
                continue
            verdict = str(row.get("verdict", "REJECT")).strip().upper()
            if verdict not in ("APPROVE", "REJECT"):
                verdict = "REJECT"
            reason = str(row.get("reason", "")).strip() or "사유 미기재"
            parsed_map[suffix] = {"suffix": suffix, "verdict": verdict, "reason": reason}

        results: list[dict] = []
        for row in normalized:
            suffix = row["suffix"]
            judged = parsed_map.get(suffix)
            if judged:
                results.append(judged)
            else:
                results.append({"suffix": suffix, "verdict": "REJECT", "reason": "LLM 응답 누락/파싱 실패"})
        return results

    def review_and_apply_suffixes(self, registry, genre: str = "", llm_ask=None) -> dict:
        """미매칭 아이템 → LLM 심사 → APPROVE 시 YAML 자동 append.

        Returns:
            {"reviewed": int, "approved": list[str], "rejected": list[str]}
        """
        report = self.item_suffix_gap_report(registry, genre)
        if report["unmatched_count"] < 10:
            logging.debug("[ItemGap] unmatched %d건 < 10 — 스킵", report["unmatched_count"])
            return {"reviewed": 0, "approved": [], "rejected": []}

        # 후보 구성 (접미사 + 등장 예시)
        candidates = []
        for suffix in report["suggested_suffixes"]:
            examples = [n for n in report["unmatched"] if n.endswith(suffix)][:3]
            candidates.append({"suffix": suffix, "examples": examples, "count": len(examples)})

        if not candidates:
            return {"reviewed": 0, "approved": [], "rejected": []}

        results = self.review_suffix_candidates(candidates, llm_ask=llm_ask)
        approved = [r["suffix"] for r in results if r.get("verdict") == "APPROVE"]
        rejected = [r["suffix"] for r in results if r.get("verdict") == "REJECT"]

        if approved:
            self._append_to_suffix_yaml(genre, approved)
            logging.info("[ItemGap] YAML 자동 추가: genre=%s, suffixes=%s", genre, approved)

        return {"reviewed": len(results), "approved": approved, "rejected": rejected}

    @staticmethod
    def _append_to_suffix_yaml(genre: str, suffixes: list[str]) -> None:
        """APPROVE된 접미사를 item_suffixes.yaml에 자동 append."""
        from pathlib import Path

        import yaml

        from modules.core.genre_schema_builder import _normalize_item_genre_key

        yaml_path = Path(__file__).resolve().parents[2] / "config" / "settings" / "item_suffixes.yaml"
        if not yaml_path.exists():
            logging.warning("[ItemGap] item_suffixes.yaml 없음 — append 스킵")
            return

        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            logging.warning("[ItemGap] YAML 로드 실패: %s", e)
            return

        genre_key = _normalize_item_genre_key(genre) or "_common"
        existing = data.get(genre_key, [])
        if not isinstance(existing, list):
            existing = []

        added = []
        for s in suffixes:
            s = str(s).strip()
            if s and s not in existing:
                existing.append(s)
                added.append(s)

        if not added:
            return

        data[genre_key] = existing
        try:
            yaml_path.write_text(
                yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
                encoding="utf-8",
            )
            logging.info("[ItemGap] item_suffixes.yaml 업데이트: %s += %s", genre_key, added)
        except Exception as e:
            logging.warning("[ItemGap] YAML 쓰기 실패: %s", e)

    def print_report(self) -> None:
        """Print summary report to console."""
        import pprint

        pprint.pprint(self.summary(), width=100, sort_dicts=False)
