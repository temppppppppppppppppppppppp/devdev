"""Helpers for repeatable Stage 4 canary preparation and analysis."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from modules.core.db_manager import DBManager
from modules.core.failure_analyzer import FailureAnalyzer


_LOG_FILE_NAMES = (
    "episode_production.jsonl",
    "pass_rate_monitor.json",
    "quality_metrics.jsonl",
    "runtime_audit.jsonl",
    "runtime_audit_summary.json",
)


def _normalize_from_ep(from_ep: int) -> int:
    normalized = max(1, int(from_ep or 1))
    if normalized != 1:
        raise ValueError("Stage 4 canary prep currently supports only from_ep=1")
    return normalized


def prepare_stage4_canary_project(
    source_root: str | Path,
    target_root: str | Path,
    *,
    from_ep: int = 1,
    force: bool = False,
) -> dict:
    """Copy a baseline project and reset only Stage 4 outputs on the copy."""
    source = Path(source_root)
    target = Path(target_root)
    from_ep = _normalize_from_ep(from_ep)
    if not source.exists():
        raise FileNotFoundError(f"source project not found: {source}")
    if source.resolve() == target.resolve():
        raise ValueError("source and target project must be different for canary prep")
    if target.exists():
        if not force:
            raise FileExistsError(f"target project already exists: {target}")
        shutil.rmtree(target)

    shutil.copytree(source, target)
    cleanup = reset_stage4_outputs(target, from_ep=from_ep)
    payload = {
        "prepared_at": datetime.now().isoformat(timespec="seconds"),
        "source_project": source.name,
        "target_project": target.name,
        "from_ep": int(from_ep),
        "cleanup": cleanup,
    }
    _write_json(target / "logs" / "canary_prep.json", payload)
    return payload


def reset_stage4_outputs(project_root: str | Path, *, from_ep: int = 1) -> dict:
    """Delete Stage 4 and episode-derived outputs while preserving Stage 3 blueprints."""
    root = Path(project_root)
    from_ep = _normalize_from_ep(from_ep)
    db_path = root / "project_data.db"
    if not db_path.exists():
        raise FileNotFoundError(f"project database not found: {db_path}")

    db = DBManager(db_path)
    try:
        impact = _collect_stage4_cleanup_impact(db, from_ep=from_ep)
        _delete_stage4_db_outputs(db, from_ep=from_ep)
    finally:
        db.close()

    files = _clear_stage4_files(root, from_ep=from_ep)
    return {
        "from_ep": from_ep,
        "db_impact": impact,
        "file_cleanup": files,
    }


def build_stage4_canary_summary(project_root: str | Path, *, target_ep: int | None = None) -> dict:
    """Summarize a prepared or completed Stage 4 canary project."""
    root = Path(project_root)
    db_path = root / "project_data.db"
    if not db_path.exists():
        raise FileNotFoundError(f"project database not found: {db_path}")

    db = DBManager(db_path)
    try:
        analyzer = FailureAnalyzer(db, project_path=root)
        patch_trace_summary = analyzer.patch_trace_summary()
        sink_alignment_summary = analyzer.sink_alignment_summary(stage=4)
        stage4_attempt_rows = db.conn.execute(
            """
            SELECT id, ep_num, attempt_num, verdict, score, session_id, attempt_key
            FROM stage_attempts
            WHERE stage = 4
            ORDER BY id ASC
            """
        ).fetchall()
        director_stage4_rows = db.conn.execute(
            """
            SELECT id, ep_num, verdict, score, attempt_key
            FROM director_selections
            WHERE """
            + DBManager._director_stage_predicate(4)
            + """
            ORDER BY id ASC
            """
        ).fetchall()
    finally:
        db.close()

    runtime_summary = _read_json(root / "logs" / "runtime_audit_summary.json")
    draft_files = sorted(root.glob("drafts/ep_*.txt"))
    pass_rate_monitor_exists = (root / "logs" / "pass_rate_monitor.json").exists()
    canary_prep = _read_json(root / "logs" / "canary_prep.json")

    latest_session_id = ""
    if stage4_attempt_rows:
        latest_session_id = str(stage4_attempt_rows[-1]["session_id"] or "").strip()

    hard_gates = _evaluate_stage4_canary_gates(
        target_ep=target_ep,
        draft_count=len(draft_files),
        runtime_summary=runtime_summary,
        pass_rate_monitor_exists=pass_rate_monitor_exists,
        patch_trace_summary=patch_trace_summary,
        sink_alignment_summary=sink_alignment_summary,
    )

    return {
        "project": root.name,
        "project_root": str(root),
        "target_ep": int(target_ep) if target_ep is not None else None,
        "prepared_from": canary_prep.get("source_project"),
        "latest_session_id": latest_session_id,
        "draft_count": len(draft_files),
        "draft_files": [path.name for path in draft_files],
        "runtime_audit_tag": runtime_summary.get("tag", ""),
        "runtime_audit_summary": runtime_summary,
        "stage4_attempts": len(stage4_attempt_rows),
        "director_stage4_rows": len(director_stage4_rows),
        "pass_rate_monitor_exists": pass_rate_monitor_exists,
        "patch_trace_summary": patch_trace_summary,
        "sink_alignment_summary": sink_alignment_summary,
        "hard_gates": hard_gates,
    }


def _collect_stage4_cleanup_impact(db: DBManager, *, from_ep: int) -> dict[str, int]:
    cur = db.cursor
    impact = {}
    count_queries = {
        "manuscripts": ("SELECT COUNT(*) AS c FROM manuscripts WHERE ep_num >= ?", (from_ep,)),
        "state_logs": ("SELECT COUNT(*) AS c FROM state_logs WHERE ep_num >= ?", (from_ep,)),
        "episode_bibles": ("SELECT COUNT(*) AS c FROM episode_bibles WHERE ep_num >= ?", (from_ep,)),
        "causal_graph": ("SELECT COUNT(*) AS c FROM causal_graph WHERE ep_num >= ?", (from_ep,)),
        "episode_meta": ("SELECT COUNT(*) AS c FROM episode_meta WHERE ep_num >= ?", (from_ep,)),
        "episode_quality_labels": ("SELECT COUNT(*) AS c FROM episode_quality_labels WHERE ep_num >= ?", (from_ep,)),
        "stage4_attempts": ("SELECT COUNT(*) AS c FROM stage_attempts WHERE stage = 4 AND ep_num >= ?", (from_ep,)),
        "stage4_director_selections": (
            "SELECT COUNT(*) AS c FROM director_selections WHERE ep_num >= ? AND "
            + DBManager._director_stage_predicate(4),
            (from_ep,),
        ),
    }
    for key, (sql, params) in count_queries.items():
        impact[key] = int(cur.execute(sql, params).fetchone()["c"])
    impact["blueprints_kept"] = int(
        cur.execute("SELECT COUNT(*) AS c FROM blueprints WHERE ep_num >= ?", (from_ep,)).fetchone()["c"]
    )
    return impact


def _delete_stage4_db_outputs(db: DBManager, *, from_ep: int) -> None:
    cur = db.cursor
    started_tx = not db.conn.in_transaction
    if started_tx:
        cur.execute("BEGIN")
    try:
        for table in ("state_logs", "causal_graph", "manuscripts", "martial_tracker"):
            cur.execute(f"DELETE FROM {table} WHERE ep_num >= ?", (from_ep,))
        cur.execute("DELETE FROM episode_bibles WHERE ep_num >= ?", (from_ep,))
        cur.execute("DELETE FROM sync_status WHERE ep_num >= ?", (from_ep,))
        cur.execute("DELETE FROM karma_status WHERE last_updated_ep >= ?", (from_ep,))
        cur.execute("DELETE FROM npc_history WHERE episode_no >= ?", (from_ep,))
        cur.execute("DELETE FROM episode_sentence_hashes WHERE episode_number >= ?", (from_ep,))
        cur.execute("DELETE FROM episode_satisfaction_tags WHERE ep_num >= ?", (from_ep,))
        cur.execute(
            "DELETE FROM director_selections WHERE ep_num >= ? AND " + DBManager._director_stage_predicate(4),
            (from_ep,),
        )
        cur.execute("DELETE FROM episode_pacing WHERE ep_num >= ?", (from_ep,))
        cur.execute("DELETE FROM episode_quality_labels WHERE ep_num >= ?", (from_ep,))
        cur.execute("DELETE FROM episode_quality_signals WHERE ep_num >= ?", (from_ep,))
        cur.execute("DELETE FROM episode_quality_observations WHERE ep_num >= ?", (from_ep,))
        cur.execute("DELETE FROM stage_attempts WHERE stage = 4 AND ep_num >= ?", (from_ep,))
        try:
            cur.execute("DELETE FROM episode_fts WHERE rowid >= ?", (from_ep,))
        except Exception:
            pass
        cur.execute("DELETE FROM episode_meta WHERE ep_num >= ?", (from_ep,))
        cur.execute("DELETE FROM foreshadow WHERE planted_ep >= ?", (from_ep,))
        cur.execute("DELETE FROM npc_relationship_edges WHERE updated_ep >= ?", (from_ep,))
        cur.execute("DELETE FROM npc_relationship_history WHERE change_ep >= ?", (from_ep,))
        cur.execute("DELETE FROM seeds WHERE planted_ep >= ?", (from_ep,))
        cur.execute("UPDATE seeds SET status = 'active', recovered_ep = NULL WHERE recovered_ep >= ?", (from_ep,))
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    try:
        db.conn.execute("VACUUM")
    except Exception:
        pass


def _clear_stage4_files(project_root: Path, *, from_ep: int) -> dict[str, int]:
    drafts_removed = 0
    drafts_dir = project_root / "drafts"
    if drafts_dir.exists():
        for draft in drafts_dir.glob("ep_*.txt"):
            ep_num = _extract_ep_num(draft.name)
            if ep_num is not None and ep_num >= from_ep:
                draft.unlink(missing_ok=True)
                drafts_removed += 1

    logs_removed = 0
    logs_dir = project_root / "logs"
    if logs_dir.exists():
        for child in list(logs_dir.iterdir()):
            _remove_path(child)
            logs_removed += 1
    logs_dir.mkdir(parents=True, exist_ok=True)

    memory_removed = 0
    memory_dir = project_root / "memory"
    if memory_dir.exists():
        for child in list(memory_dir.iterdir()):
            _remove_path(child)
            memory_removed += 1
    memory_dir.mkdir(parents=True, exist_ok=True)

    return {
        "draft_files_removed": drafts_removed,
        "log_entries_removed": logs_removed,
        "memory_entries_removed": memory_removed,
    }


def _evaluate_stage4_canary_gates(
    *,
    target_ep: int | None,
    draft_count: int,
    runtime_summary: dict,
    pass_rate_monitor_exists: bool,
    patch_trace_summary: dict,
    sink_alignment_summary: dict,
) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    runtime_tag = str((runtime_summary or {}).get("tag", "") or "")
    runtime_total_events = int((runtime_summary or {}).get("total_events", 0) or 0)

    if target_ep is not None and draft_count != int(target_ep):
        errors.append(f"draft_count_mismatch:{draft_count}!={int(target_ep)}")
    if runtime_tag and runtime_tag != "stage4_complete":
        errors.append(f"runtime_tag_not_complete:{runtime_tag}")
    if not runtime_tag:
        warnings.append("runtime_audit_summary_missing")
    elif runtime_total_events <= 0:
        errors.append("runtime_audit_empty")
    if not pass_rate_monitor_exists:
        errors.append("pass_rate_monitor_missing")

    if sink_alignment_summary:
        if sink_alignment_summary.get("final_sink_missing"):
            errors.append("final_sink_missing")
        if sink_alignment_summary.get("lifecycle_sink_missing"):
            errors.append("lifecycle_sink_missing")
        if sink_alignment_summary.get("lifecycle_missing_in_final_sinks"):
            errors.append("lifecycle_missing_in_final_sinks")
        for field in (
            "final_verdict_mismatches",
            "final_score_mismatches",
            "initial_verdict_mismatches",
            "patch_strategy_mismatches",
            "candidate_key_mismatches",
            "selection_candidate_key_mismatches",
            "content_hash_mismatches",
            "artifact_path_mismatches",
            "artifact_metadata_missing",
            "artifact_missing_files",
        ):
            if sink_alignment_summary.get(field):
                errors.append(field)
        if int(sink_alignment_summary.get("legacy_key_attempts", 0) or 0) > 0:
            errors.append("legacy_key_attempts")
        if sink_alignment_summary.get("status") not in ("", "ok"):
            errors.append(f"sink_alignment_status:{sink_alignment_summary.get('status')}")
    else:
        errors.append("sink_alignment_summary_empty")

    if patch_trace_summary:
        avg_unchanged = patch_trace_summary.get("avg_unchanged_ratio")
        if avg_unchanged is not None and float(avg_unchanged) < 0.70:
            errors.append("avg_unchanged_ratio_below_gate")
        fallback_reasons = patch_trace_summary.get("fallback_reasons", {}) or {}
        for blocked in ("missing_patched_blocks", "no_usable_patched_blocks", "patched_output_too_short"):
            if int(fallback_reasons.get(blocked, 0) or 0) > 0:
                errors.append(f"fallback_reason:{blocked}")
    else:
        warnings.append("patch_trace_not_exercised")

    status = "fail" if errors else ("warn" if warnings else "pass")
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }


def _extract_ep_num(filename: str) -> int | None:
    stem = Path(filename).stem
    digits = "".join(ch for ch in stem if ch.isdigit())
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
        return
    path.unlink(missing_ok=True)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
