"""Helpers for repeatable Stage 4 canary preparation and analysis."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from modules.core.db_manager import DBManager
from modules.core.fact_ledger import FactLedger
from modules.core.failure_analyzer import FailureAnalyzer
from modules.core.world_state import WorldStateManager

_APP_ROOT = Path(__file__).resolve().parents[2]

_LOG_FILE_NAMES = (
    "episode_production.jsonl",
    "pass_rate_monitor.json",
    "quality_metrics.jsonl",
    "runtime_audit.jsonl",
    "runtime_audit_summary.json",
)

_STAGE4_RATIONALE_FIELDS = (
    "selection_reason",
    "verdict_reason",
    "open_review",
    "fix_scope_reasoning",
    "runtime_advisory",
    "retry_directives",
)
_STAGE4_RETRY_CONTEXT_FIELDS = (
    "open_review",
    "fix_scope_reasoning",
    "runtime_advisory",
    "retry_directives",
)
_STAGE4_RETRY_REQUIRED_VERDICTS = {"REJECT", "PASS_WITH_FIX"}
_GATE_REPAIR_MISMATCH_FIELDS = (
    "repair_contract_subtype_mismatches",
    "repair_contract_provenance_mismatches",
    "scope_authority_fix_scope_mismatches",
    "scope_authority_authoritative_fix_scope_mismatches",
    "scope_authority_widened_mismatches",
    "gate_repair_metadata_missing",
)


def _normalize_from_ep(from_ep: int, *, allow_partial: bool = False) -> int:
    normalized = max(1, int(from_ep or 1))
    if not allow_partial and normalized != 1:
        raise ValueError("Stage 4 canary prep currently supports only from_ep=1")
    return normalized


# ─────────────────────────────────────────────────────────────
# Stage 3-only canary helpers
# ─────────────────────────────────────────────────────────────


def prepare_stage3_canary_project(
    source_root: str | Path,
    target_root: str | Path,
    *,
    from_ep: int = 1,
    force: bool = False,
) -> dict:
    """Copy a baseline project and reset only Stage 3 outputs on the copy.

    Stage 2 arcs and anchors are preserved.  Stage 4 outputs are also preserved
    (though they will be stale after Stage 3 reruns).
    """
    source = Path(source_root)
    target = Path(target_root)
    from_ep = _normalize_from_ep(from_ep, allow_partial=True)
    if not source.exists():
        raise FileNotFoundError(f"source project not found: {source}")
    if source.resolve() == target.resolve():
        raise ValueError("source and target project must be different for stage3 canary prep")
    if target.exists():
        if not force:
            raise FileExistsError(f"target project already exists: {target}")
        shutil.rmtree(target)

    shutil.copytree(source, target)
    cleanup = reset_stage3_outputs(target, from_ep=from_ep)
    payload = {
        "prepared_at": datetime.now().isoformat(timespec="seconds"),
        "source_project": source.name,
        "target_project": target.name,
        "canary_scope": "stage3_only",
        "reruns_stage3_generation": True,
        "preserves_stage2_arcs": True,
        "preserves_stage4_outputs": True,
        "from_ep": int(from_ep),
        "cleanup": cleanup,
    }
    _write_json(target / "logs" / "stage3_canary_prep.json", payload)
    return payload


def reset_stage3_outputs(project_root: str | Path, *, from_ep: int = 1) -> dict:
    """Delete Stage 3 outputs while preserving Stage 2 arcs/anchors and Stage 4 outputs."""
    root = Path(project_root)
    from_ep = _normalize_from_ep(from_ep, allow_partial=True)
    db_path = root / "project_data.db"
    if not db_path.exists():
        raise FileNotFoundError(f"project database not found: {db_path}")

    db = DBManager(db_path)
    try:
        impact = _collect_stage3_cleanup_impact(db, from_ep=from_ep)
        _delete_stage3_db_outputs(db, from_ep=from_ep)
    finally:
        db.close()

    files = _clear_stage3_files(root, from_ep=from_ep)
    return {
        "from_ep": from_ep,
        "db_impact": impact,
        "file_cleanup": files,
    }


def build_stage3_canary_summary(project_root: str | Path, *, target_ep: int | None = None) -> dict:
    """Summarize a prepared or completed Stage 3-only canary project."""
    root = Path(project_root)
    db_path = root / "project_data.db"
    if not db_path.exists():
        raise FileNotFoundError(f"project database not found: {db_path}")
    project_locator = _build_project_locator(root)

    db = DBManager(db_path)
    try:
        stage3_attempt_rows = db.conn.execute(
            """
            SELECT id, ep_num, attempt_num, verdict, score, session_id, attempt_key
            FROM stage_attempts
            WHERE stage = 3
            ORDER BY id ASC
            """
        ).fetchall()
        latest_session_id = latest_session_id_from_rows(stage3_attempt_rows)

        blueprint_rows = db.conn.execute(
            "SELECT ep_num FROM blueprints ORDER BY ep_num ASC"
        ).fetchall()

        analyzer = FailureAnalyzer(db, project_path=root)
        sink_alignment_summary = analyzer.sink_alignment_summary(
            stage=3,
            include_session_decisions=True,
            session_id=latest_session_id,
        )
        episode_telemetry = _build_stage3_episode_telemetry(db, stage3_attempt_rows)
    finally:
        db.close()

    blueprint_ep_nums = sorted({int(row["ep_num"]) for row in blueprint_rows})
    blueprint_files = sorted(root.glob("plans/blueprints/blueprint_*.txt"))
    canary_prep = _read_json(root / "logs" / "stage3_canary_prep.json")

    attempt_detail = _build_stage3_attempt_detail(stage3_attempt_rows)
    hard_gates = _evaluate_stage3_canary_gates(
        target_ep=target_ep,
        blueprint_db_count=len(blueprint_ep_nums),
        blueprint_file_count=len(blueprint_files),
        attempt_detail=attempt_detail,
        sink_alignment_summary=sink_alignment_summary,
    )

    return {
        "summary_role": "stage3_only_canary",
        "project": root.name,
        "project_locator": project_locator,
        "project_root": str(root),
        "target_ep": int(target_ep) if target_ep is not None else None,
        "prepared_from": canary_prep.get("source_project"),
        "latest_session_id": latest_session_id,
        "stage3_attempts": len(stage3_attempt_rows),
        "blueprint_db_count": len(blueprint_ep_nums),
        "blueprint_ep_nums": blueprint_ep_nums,
        "blueprint_file_count": len(blueprint_files),
        "blueprint_files": [p.name for p in blueprint_files],
        "attempt_detail": attempt_detail,
        "episode_telemetry": episode_telemetry,
        "sink_alignment_summary": sink_alignment_summary,
        "hard_gates": hard_gates,
    }


def _build_stage3_attempt_detail(rows) -> list[dict]:
    """Build per-episode attempt summary from stage_attempts rows."""
    episodes: dict[int, list[dict]] = {}
    for row in rows:
        ep = int(row["ep_num"] or 0)
        episodes.setdefault(ep, []).append({
            "attempt_num": int(row["attempt_num"] or 0),
            "verdict": str(row["verdict"] or "").strip(),
            "score": row["score"],
        })
    result = []
    for ep in sorted(episodes):
        attempts = episodes[ep]
        final = attempts[-1]
        result.append({
            "ep_num": ep,
            "attempt_count": len(attempts),
            "final_verdict": final["verdict"],
            "final_score": final["score"],
            "all_verdicts": [a["verdict"] for a in attempts],
        })
    return result


def _build_stage3_episode_telemetry(db, attempt_rows) -> list[dict]:
    """Compact per-episode telemetry from existing DB sinks (read-only).

    Timing field semantics (TM-1):
      total_duration_ms      — SUM of ask() wall-clock times. Includes retries,
                                continuations, API_DELAY sleeps, orchestration overhead.
                                NOT raw API latency. Retained for backward compatibility.
      total_api_elapsed_ms   — SUM of raw _generate_content() RTT for final successful
                                API calls only. 0 for legacy rows without TM-1 columns.
                                Use this field when attributing time to the API provider.
      total_retries          — total error-driven retry count across all calls.
      total_continuations    — total continuation rounds across all calls.
    """
    if not attempt_rows:
        return []
    ep_nums = sorted({int(row["ep_num"] or 0) for row in attempt_rows})
    if not ep_nums:
        return []
    try:
        placeholders = ",".join("?" for _ in ep_nums)
        cost_rows = db.conn.execute(
            f"""
            SELECT ep_num,
                   COUNT(*) as call_count,
                   SUM(duration_ms) as total_duration_ms,
                   SUM(COALESCE(total_cost_usd, 0)) as total_cost_usd,
                   SUM(COALESCE(api_elapsed_ms, 0)) as total_api_elapsed_ms,
                   SUM(COALESCE(retry_count, 0)) as total_retries,
                   SUM(COALESCE(continuation_count, 0)) as total_continuations
            FROM llm_calls
            WHERE stage = 3 AND ep_num IN ({placeholders})
            GROUP BY ep_num
            """,
            tuple(ep_nums),
        ).fetchall()
    except Exception:
        return []

    cost_by_ep: dict[int, dict] = {}
    for row in cost_rows:
        ep = int(row["ep_num"] or 0)
        cost_by_ep[ep] = {
            "llm_call_count": int(row["call_count"] or 0),
            "total_duration_ms": int(row["total_duration_ms"] or 0),
            "total_cost_usd": round(float(row["total_cost_usd"] or 0), 6),
            "total_api_elapsed_ms": int(row["total_api_elapsed_ms"] or 0),
            "total_retries": int(row["total_retries"] or 0),
            "total_continuations": int(row["total_continuations"] or 0),
        }

    ep_attempts: dict[int, list] = {}
    for row in attempt_rows:
        ep = int(row["ep_num"] or 0)
        ep_attempts.setdefault(ep, []).append(row)

    result: list[dict] = []
    for ep in ep_nums:
        attempts = ep_attempts.get(ep, [])
        final = attempts[-1] if attempts else None
        cost = cost_by_ep.get(ep, {})
        entry: dict = {
            "ep_num": ep,
            "attempt_count": len(attempts),
            "final_verdict": str(final["verdict"] or "").strip() if final else "",
            "final_score": final["score"] if final else None,
        }
        entry.update(cost)
        result.append(entry)
    return result


def _evaluate_stage3_canary_gates(
    *,
    target_ep: int | None,
    blueprint_db_count: int,
    blueprint_file_count: int,
    attempt_detail: list[dict],
    sink_alignment_summary: dict,
) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if target_ep is not None:
        if blueprint_db_count < int(target_ep):
            errors.append(f"blueprint_db_count_short:{blueprint_db_count}<{int(target_ep)}")
        if blueprint_file_count < int(target_ep):
            errors.append(f"blueprint_file_count_short:{blueprint_file_count}<{int(target_ep)}")
    if not attempt_detail:
        errors.append("no_stage3_attempts")
    else:
        failed_eps = [d for d in attempt_detail if d["final_verdict"] != "PASS"]
        if failed_eps:
            for d in failed_eps:
                errors.append(f"ep{d['ep_num']}_final_verdict:{d['final_verdict']}")

    if sink_alignment_summary:
        status = str(sink_alignment_summary.get("status", "") or "").strip()
        if status and status != "ok":
            warnings.append(f"sink_alignment_status:{status}")
    else:
        warnings.append("sink_alignment_summary_empty")

    status = "fail" if errors else ("warn" if warnings else "pass")
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }


def _collect_stage3_cleanup_impact(db: DBManager, *, from_ep: int) -> dict[str, int]:
    cur = db.cursor
    impact = {}
    impact["blueprints"] = int(
        cur.execute("SELECT COUNT(*) AS c FROM blueprints WHERE ep_num >= ?", (from_ep,)).fetchone()["c"]
    )
    impact["stage3_attempts"] = int(
        cur.execute(
            "SELECT COUNT(*) AS c FROM stage_attempts WHERE stage = 3 AND ep_num >= ?", (from_ep,)
        ).fetchone()["c"]
    )
    impact["stage3_director_selections"] = int(
        cur.execute(
            "SELECT COUNT(*) AS c FROM director_selections WHERE ep_num >= ? AND "
            + DBManager._director_stage_predicate(3),
            (from_ep,),
        ).fetchone()["c"]
    )
    return impact


def _delete_stage3_db_outputs(db: DBManager, *, from_ep: int) -> None:
    cur = db.cursor
    started_tx = not db.conn.in_transaction
    if started_tx:
        cur.execute("BEGIN")
    try:
        cur.execute("DELETE FROM blueprints WHERE ep_num >= ?", (from_ep,))
        cur.execute(
            "DELETE FROM director_selections WHERE ep_num >= ? AND "
            + DBManager._director_stage_predicate(3),
            (from_ep,),
        )
        cur.execute("DELETE FROM stage_attempts WHERE stage = 3 AND ep_num >= ?", (from_ep,))
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    try:
        db.conn.execute("VACUUM")
    except Exception:
        pass


def _clear_stage3_files(project_root: Path, *, from_ep: int) -> dict[str, int]:
    blueprints_removed = 0
    blueprints_dir = project_root / "plans" / "blueprints"
    if blueprints_dir.exists():
        for blueprint in blueprints_dir.glob("blueprint_*.txt"):
            ep_num = _extract_ep_num(blueprint.name)
            if ep_num is not None and ep_num >= from_ep:
                blueprint.unlink(missing_ok=True)
                blueprints_removed += 1

    stage3_artifacts_removed = 0
    stage3_artifacts_dir = project_root / "logs" / "artifacts" / "stage3"
    if stage3_artifacts_dir.exists():
        for child in list(stage3_artifacts_dir.iterdir()):
            ep_num = _extract_ep_num(child.name)
            if ep_num is not None and ep_num >= from_ep:
                _remove_path(child)
                stage3_artifacts_removed += 1

    logs_removed = 0
    logs_dir = project_root / "logs"
    if logs_dir.exists():
        for log_name in _LOG_FILE_NAMES:
            log_path = logs_dir / log_name
            if log_path.exists():
                log_path.unlink(missing_ok=True)
                logs_removed += 1
        for session_file in (logs_dir / "session").glob("*") if (logs_dir / "session").exists() else []:
            session_file.unlink(missing_ok=True)
            logs_removed += 1

    return {
        "blueprint_files_removed": blueprints_removed,
        "stage3_artifact_dirs_removed": stage3_artifacts_removed,
        "log_entries_removed": logs_removed,
    }


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
    from_ep = _normalize_from_ep(from_ep, allow_partial=True)
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
        "source_project": _build_project_name(source),
        "target_project": _build_project_name(target),
        "canary_scope": "stage4_only",
        "reruns_stage3_generation": False,
        "preserves_stage3_blueprints": True,
        "preserves_stage3_sink_baseline": True,
        "from_ep": int(from_ep),
        "cleanup": cleanup,
    }
    _write_json(target / "logs" / "canary_prep.json", payload)
    return payload


def prepare_stage34_canary_project(
    source_root: str | Path,
    target_root: str | Path,
    *,
    from_ep: int = 1,
    force: bool = False,
) -> dict:
    """Copy a baseline project and reset Stage 3/4 outputs on the copy."""
    source = Path(source_root)
    target = Path(target_root)
    from_ep = _normalize_from_ep(from_ep, allow_partial=True)
    if not source.exists():
        raise FileNotFoundError(f"source project not found: {source}")
    if source.resolve() == target.resolve():
        raise ValueError("source and target project must be different for stage3/4 canary prep")
    if target.exists():
        if not force:
            raise FileExistsError(f"target project already exists: {target}")
        shutil.rmtree(target)

    shutil.copytree(source, target)
    cleanup = reset_stage34_outputs(target, from_ep=from_ep)
    payload = {
        "prepared_at": datetime.now().isoformat(timespec="seconds"),
        "source_project": _build_project_name(source),
        "target_project": _build_project_name(target),
        "from_ep": int(from_ep),
        "cleanup": cleanup,
    }
    _write_json(target / "logs" / "stage34_canary_prep.json", payload)
    return payload


def reset_stage4_outputs(project_root: str | Path, *, from_ep: int = 1) -> dict:
    """Delete Stage 4 and episode-derived outputs while preserving Stage 3 blueprints."""
    root = Path(project_root)
    from_ep = _normalize_from_ep(from_ep, allow_partial=True)
    db_path = root / "project_data.db"
    if not db_path.exists():
        raise FileNotFoundError(f"project database not found: {db_path}")

    db = DBManager(db_path)
    try:
        impact = _collect_stage4_cleanup_impact(db, from_ep=from_ep)
        _delete_stage4_db_outputs(db, from_ep=from_ep)
        anchor_validation = _validate_truth_store_reset(db, from_ep=from_ep)
    finally:
        db.close()

    files = _clear_stage4_files(root, from_ep=from_ep)
    return {
        "from_ep": from_ep,
        "db_impact": impact,
        "anchor_validation": anchor_validation,
        "file_cleanup": files,
    }


def reset_stage34_outputs(project_root: str | Path, *, from_ep: int = 1) -> dict:
    """Delete Stage 3/4 outputs while preserving Stage 2 arc design and anchors."""
    root = Path(project_root)
    from_ep = _normalize_from_ep(from_ep, allow_partial=True)
    db_path = root / "project_data.db"
    if not db_path.exists():
        raise FileNotFoundError(f"project database not found: {db_path}")

    db = DBManager(db_path)
    try:
        impact = _collect_stage34_cleanup_impact(db, from_ep=from_ep)
        _delete_stage34_db_outputs(db, from_ep=from_ep)
        anchor_validation = _validate_truth_store_reset(db, from_ep=from_ep)
    finally:
        db.close()

    files = _clear_stage34_files(root, from_ep=from_ep)
    return {
        "from_ep": from_ep,
        "db_impact": impact,
        "anchor_validation": anchor_validation,
        "file_cleanup": files,
    }


def build_stage4_canary_summary(project_root: str | Path, *, target_ep: int | None = None) -> dict:
    """Summarize a prepared or completed Stage 4 canary project."""
    root = Path(project_root)
    db_path = root / "project_data.db"
    if not db_path.exists():
        raise FileNotFoundError(f"project database not found: {db_path}")
    project_locator = _build_project_locator(root)

    db = DBManager(db_path)
    try:
        analyzer = FailureAnalyzer(db, project_path=root)
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
        latest_session_id = latest_session_id_from_rows(stage4_attempt_rows)
        patch_trace_summary = analyzer.patch_trace_summary()
        sink_alignment_summary = analyzer.sink_alignment_summary(stage=4)
        current_session_sink_alignment_summary = analyzer.sink_alignment_summary(
            stage=4,
            session_id=latest_session_id,
        )
        stage3_sink_alignment_summary = analyzer.sink_alignment_summary(stage=3, include_session_decisions=True)
        final_authority_contract_summary = sink_alignment_summary.get("final_authority_contract", {}) or {}
        rationale_contract_summary = _summarize_stage4_rationale_contract(db)
        companion_audit_summary = _summarize_stage4_companion_audit(
            db,
            latest_session_id=latest_session_id,
        )
        gate_repair_summary = db.get_latest_stage4_gate_repair_snapshot(session_id=latest_session_id or None)
    finally:
        db.close()

    canary_prep = _read_json(root / "logs" / "canary_prep.json")
    runtime_summary = _read_json(root / "logs" / "runtime_audit_summary.json")
    draft_files = sorted(root.glob("drafts/ep_*.txt"))
    pass_rate_monitor_exists = (root / "logs" / "pass_rate_monitor.json").exists()
    canary_scope = str(canary_prep.get("canary_scope", "") or "").strip().lower()
    hard_gate_sink_alignment_scope = (
        "current_session"
        if canary_scope == "stage4_only" and current_session_sink_alignment_summary
        else "run_wide"
    )
    hard_gate_sink_alignment_summary = (
        current_session_sink_alignment_summary
        if hard_gate_sink_alignment_scope == "current_session"
        else sink_alignment_summary
    )

    gate_repair_surface_summary = _build_stage4_gate_repair_surface_summary(
        gate_repair_summary=gate_repair_summary,
        sink_alignment_summary=sink_alignment_summary,
        current_session_sink_alignment_summary=current_session_sink_alignment_summary,
    )
    hard_gates = _evaluate_stage4_canary_gates(
        target_ep=target_ep,
        draft_count=len(draft_files),
        runtime_summary=runtime_summary,
        pass_rate_monitor_exists=pass_rate_monitor_exists,
        patch_trace_summary=patch_trace_summary,
        sink_alignment_summary=hard_gate_sink_alignment_summary,
        rationale_contract_summary=rationale_contract_summary,
        final_authority_contract_summary=final_authority_contract_summary,
        companion_audit_summary=companion_audit_summary,
        gate_repair_surface_summary=gate_repair_surface_summary,
    )
    proof_scope_summary = _build_stage4_canary_proof_scope_summary(
        stage3_sink_alignment_summary=stage3_sink_alignment_summary,
        stage4_sink_alignment_summary=sink_alignment_summary,
        rationale_contract_summary=rationale_contract_summary,
        canary_prep=canary_prep,
    )
    proof_record_summary = _build_stage4_proof_record_summary(
        project_root=root,
        project_locator=project_locator,
        latest_session_id=latest_session_id,
    )

    return {
        "project": root.name,
        "project_locator": project_locator,
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
        "stage3_sink_alignment_summary": stage3_sink_alignment_summary,
        "sink_alignment_summary": sink_alignment_summary,
        "current_session_sink_alignment_summary": current_session_sink_alignment_summary,
        "hard_gate_sink_alignment_scope": hard_gate_sink_alignment_scope,
        "final_authority_contract_summary": final_authority_contract_summary,
        "gate_repair_summary": gate_repair_summary,
        "gate_repair_surface_summary": gate_repair_surface_summary,
        "rationale_contract_summary": rationale_contract_summary,
        "companion_audit_summary": companion_audit_summary,
        "proof_scope_summary": proof_scope_summary,
        "proof_record_summary": proof_record_summary,
        "hard_gates": hard_gates,
    }


def _build_stage4_gate_repair_surface_summary(
    *,
    gate_repair_summary: dict,
    sink_alignment_summary: dict,
    current_session_sink_alignment_summary: dict,
) -> dict:
    repair_contract = gate_repair_summary.get("repair_contract", {}) or {}
    if not isinstance(repair_contract, dict):
        repair_contract = {}
    scope_authority = gate_repair_summary.get("scope_authority", {}) or {}
    if not isinstance(scope_authority, dict):
        scope_authority = {}

    mismatch_source = (
        current_session_sink_alignment_summary
        if current_session_sink_alignment_summary
        else sink_alignment_summary
    )
    mismatch_scope = "current_session" if current_session_sink_alignment_summary else "run_wide"
    mismatch_counts = {
        field: len(mismatch_source.get(field) or [])
        for field in _GATE_REPAIR_MISMATCH_FIELDS
    }
    has_gate_surface = bool(
        gate_repair_summary
        or repair_contract
        or scope_authority
        or str(gate_repair_summary.get("fix_scope", "") or "").strip()
        or str(gate_repair_summary.get("authoritative_fix_scope", "") or "").strip()
    )

    if not has_gate_surface:
        status = "missing"
    elif any(count > 0 for count in mismatch_counts.values()):
        status = "warn"
    else:
        status = "ok"

    return {
        "status": status,
        "mismatch_scope": mismatch_scope,
        "attempt_key": str(gate_repair_summary.get("attempt_key", "") or "").strip(),
        "session_id": str(gate_repair_summary.get("session_id", "") or "").strip(),
        "final_verdict": str(gate_repair_summary.get("final_verdict", "") or "").strip(),
        "fix_scope": str(gate_repair_summary.get("fix_scope", "") or "").strip(),
        "authoritative_fix_scope": str(gate_repair_summary.get("authoritative_fix_scope", "") or "").strip(),
        "repair_scope": str(gate_repair_summary.get("repair_scope", "") or "").strip(),
        "repair_contract_subtype": str(repair_contract.get("subtype", "") or "").strip(),
        "repair_contract_provenance": str(repair_contract.get("provenance", "") or "").strip(),
        "scope_origin": str(scope_authority.get("scope_origin", "") or "").strip(),
        "widened": bool(scope_authority.get("widened", False)),
        "mismatch_counts": mismatch_counts,
    }


def build_stage4_branch_inventory(project_roots: list[str | Path]) -> dict:
    """Aggregate multiple current/historical canary summaries into branch-proof coverage."""
    entries: list[dict] = []
    missing_projects: list[dict[str, str]] = []

    for project_root in project_roots:
        root = Path(project_root)
        summary_path = root / "logs" / "canary_summary.json"
        summary = _read_json(summary_path)
        if not summary:
            missing_projects.append(
                {
                    "project_root": str(root),
                    "summary_path": str(summary_path),
                }
            )
            continue

        rationale_summary = summary.get("rationale_contract_summary", {}) or {}
        companion_summary = summary.get("companion_audit_summary", {}) or {}
        sink_summary = summary.get("sink_alignment_summary", {}) or {}
        current_session_sink_summary = summary.get("current_session_sink_alignment_summary", {}) or {}
        final_authority_contract_summary = summary.get("final_authority_contract_summary", {}) or {}
        patch_summary = summary.get("patch_trace_summary", {}) or {}
        proof_record = summary.get("proof_record_summary", {}) or {}
        hard_gates = summary.get("hard_gates", {}) or {}
        patch_count = int(patch_summary.get("count", 0) or 0)
        retry_required_row_count = int(rationale_summary.get("retry_required_row_count", 0) or 0)

        entry = {
            "project": str(summary.get("project", root.name) or root.name),
            "project_root": str(root),
            "project_locator": str(summary.get("project_locator", "") or _build_project_locator(root)),
            "latest_session_id": str(summary.get("latest_session_id", "") or ""),
            "classification": str(proof_record.get("classification", "") or ""),
            "proof_origin": str(proof_record.get("proof_origin", "") or ""),
            "hard_gates_status": str(hard_gates.get("status", "") or "missing"),
            "sink_alignment_status": _summary_status(sink_summary, default="missing"),
            "current_session_sink_alignment_status": _summary_status(current_session_sink_summary, default="missing"),
            "final_authority_contract_status": _summary_status(final_authority_contract_summary, default="missing"),
            "rationale_contract_status": _summary_status(rationale_summary, default="missing"),
            "companion_audit_status": _summary_status(companion_summary, default="missing"),
            "patch_trace_exercised": patch_count > 0,
            "patch_trace_count": patch_count,
            "retry_contract_exercised": retry_required_row_count > 0,
            "retry_required_row_count": retry_required_row_count,
            "retry_context_missing_rows": len(rationale_summary.get("rows_missing_retry_context") or []),
            "warnings": list(hard_gates.get("warnings") or []),
            "errors": list(hard_gates.get("errors") or []),
        }
        entries.append(entry)

    current_entries = [entry for entry in entries if entry.get("classification") == "current"]

    def _pick_pass_basis() -> dict:
        for entry in current_entries:
            if (
                entry["sink_alignment_status"] == "ok"
                and entry["rationale_contract_status"] == "ok"
                and entry["companion_audit_status"] == "ok"
            ):
                return {
                    "status": "covered",
                    "basis_project_locator": entry["project_locator"],
                    "latest_session_id": entry["latest_session_id"],
                    "hard_gates_status": entry["hard_gates_status"],
                    "note": "same-session current live proof with sink/rationale/companion audit all ok",
                }
        return {
            "status": "missing",
            "basis_project_locator": "",
            "latest_session_id": "",
            "hard_gates_status": "missing",
            "note": "no current proof entry satisfies sink/rationale/companion ok together",
        }

    def _pick_patch_basis() -> dict:
        for entry in current_entries:
            if (
                entry["patch_trace_exercised"]
                and entry["rationale_contract_status"] == "ok"
                and entry["companion_audit_status"] == "ok"
            ):
                note = "current live patch branch exercised"
                if entry["current_session_sink_alignment_status"] == "ok":
                    note += "; same-session sink alignment is ok"
                elif entry["sink_alignment_status"] != "ok":
                    note += "; sink alignment for the whole run is not closure-grade, so this is branch-only proof"
                return {
                    "status": "covered",
                    "basis_project_locator": entry["project_locator"],
                    "latest_session_id": entry["latest_session_id"],
                    "hard_gates_status": entry["hard_gates_status"],
                    "note": note,
                }
        return {
            "status": "missing",
            "basis_project_locator": "",
            "latest_session_id": "",
            "hard_gates_status": "missing",
            "note": "no current proof entry exercised patch_trace",
        }

    def _pick_retry_basis() -> dict:
        for entry in current_entries:
            if entry["retry_contract_exercised"] and entry["retry_context_missing_rows"] == 0:
                note = "current live retry-required row exists and retry context contract is populated"
                if entry["current_session_sink_alignment_status"] == "ok":
                    note += "; same-session sink alignment is ok"
                return {
                    "status": "covered",
                    "basis_project_locator": entry["project_locator"],
                    "latest_session_id": entry["latest_session_id"],
                    "hard_gates_status": entry["hard_gates_status"],
                    "note": note,
                }
        return {
            "status": "missing",
            "basis_project_locator": "",
            "latest_session_id": "",
            "hard_gates_status": "missing",
            "note": "no current proof entry exercised retry-required Stage 4 rows",
        }

    branch_coverage = {
        "pass_path_current_basis": _pick_pass_basis(),
        "patch_path_current_basis": _pick_patch_basis(),
        "retry_path_current_basis": _pick_retry_basis(),
    }

    unresolved_runtime_only = []
    if branch_coverage["retry_path_current_basis"]["status"] != "covered":
        unresolved_runtime_only.append("stage4_retry_contract_not_exercised_live")

    return {
        "summary_role": "stage4_runtime_branch_proof_inventory",
        "entries_considered": len(entries),
        "missing_projects": missing_projects,
        "proof_entries": entries,
        "branch_coverage": branch_coverage,
        "unresolved_runtime_only": unresolved_runtime_only,
    }


def _build_stage4_canary_proof_scope_summary(
    *,
    stage3_sink_alignment_summary: dict,
    stage4_sink_alignment_summary: dict,
    rationale_contract_summary: dict,
    canary_prep: dict | None = None,
) -> dict:
    stage3_observed = bool(stage3_sink_alignment_summary)
    stage4_observed = bool(stage4_sink_alignment_summary)
    rationale_observed = bool(rationale_contract_summary)
    prep_scope = str((canary_prep or {}).get("canary_scope", "") or "").strip().lower()
    stage4_only_canary = prep_scope == "stage4_only"

    covered_surfaces = [
        "stage4_live_context_path",
        "stage4_sink_alignment",
        "stage4_rationale_contract",
    ]
    if stage3_observed:
        covered_surfaces.append("stage3_baseline_sink_probe" if stage4_only_canary else "stage3_sink_alignment_probe")

    uncovered_surfaces = [
        "stage3_live_generation_path",
        "backend_wide_multi_stage_runtime",
    ]
    if not stage3_observed:
        uncovered_surfaces.append("stage3_sink_probe_missing")

    return {
        "summary_role": (
            "stage4_live_canary_with_baseline_stage3_probe"
            if stage4_only_canary
            else "stage4_live_canary_with_stage3_sink_probe"
        ),
        "backend_wide_proof": False,
        "scope_status": "stage4_only" if stage4_only_canary else ("partial_multi_stage_probe" if stage3_observed else "stage4_only"),
        "stage4_live_context_regression": "covered",
        "stage4_sink_alignment_status": _summary_status(stage4_sink_alignment_summary, default="missing"),
        "stage3_sink_probe_status": _summary_status(stage3_sink_alignment_summary, default="missing"),
        "stage3_probe_origin": (
            "baseline_copy"
            if stage4_only_canary and stage3_observed
            else ("live_or_unspecified" if stage3_observed else "missing")
        ),
        "rationale_contract_status": _summary_status(rationale_contract_summary, default="missing"),
        "covered_surfaces": covered_surfaces,
        "uncovered_surfaces": uncovered_surfaces,
        "notes": [
            "This canary is not a backend-wide proof net.",
            (
                "Stage 3 sink alignment here is baseline carryover from the copied source project; this canary does not rerun live Stage 3 generation."
                if stage4_only_canary
                else "Stage 3 is observed via sink alignment only; it does not rerun live Stage 3 generation."
            ),
        ],
        "observability_contract": {
            "stage3_sink_alignment_observed": stage3_observed,
            "stage4_sink_alignment_observed": stage4_observed,
            "stage4_rationale_contract_observed": rationale_observed,
        },
    }


def _build_stage4_proof_record_summary(
    *,
    project_root: Path,
    project_locator: str,
    latest_session_id: str,
) -> dict:
    is_historical = "기록용" in project_root.parts
    return {
        "classification": "historical" if is_historical else "current",
        "proof_origin": "archived_project" if is_historical else "current_workspace_refresh",
        "project_locator": project_locator,
        "summary_path": "logs/canary_summary.json",
        "companion_audit_path": "logs/canary_companion_audit.json",
        "latest_session_id": latest_session_id,
        "refreshed_at": datetime.now().isoformat(timespec="seconds"),
    }


def _summarize_stage4_companion_audit(db: DBManager, *, latest_session_id: str) -> dict:
    required_stage_attempt_fields = [
        "attempt_key",
        "candidate_key",
        "content_hash",
        "artifact_path",
        "selection_reason",
        "verdict_reason",
    ]
    params: tuple[object, ...]
    where_clause = "WHERE stage = 4"
    params = ()
    if latest_session_id:
        where_clause += " AND session_id = ?"
        params = (latest_session_id,)

    rows = db.conn.execute(
        f"""
        SELECT ep_num, attempt_num, verdict, session_id, attempt_key, candidate_key, content_hash,
               artifact_path, selection_reason, verdict_reason
        FROM stage_attempts
        {where_clause}
        ORDER BY id ASC
        """,
        params,
    ).fetchall()

    director_reasons: dict[str, dict[str, str]] = {}
    director_rows = db.conn.execute(
        """
        SELECT attempt_key, selection_reason, verdict_reason, fix_scope
        FROM director_selections
        WHERE """
        + DBManager._director_stage_predicate(4)
        + """
        ORDER BY id ASC
        """
    ).fetchall()
    for row in director_rows:
        attempt_key = str(row["attempt_key"] or "").strip()
        if attempt_key and attempt_key not in director_reasons:
            director_reasons[attempt_key] = {
                "selection_reason": str(row["selection_reason"] or "").strip(),
                "verdict_reason": str(row["verdict_reason"] or "").strip(),
                "fix_scope": str(row["fix_scope"] or "").strip(),
            }

    summary = {
        "status": "ok",
        "latest_session_id": latest_session_id,
        "row_count": len(rows),
        "required_stage_attempt_fields": required_stage_attempt_fields,
        "rows_missing_required_fields": [],
        "director_companion_rows": len(director_reasons),
        "director_rationale_available": 0,
        "note": "Same-run stage_attempt provenance/rationale fields must stand on their own; director_selections is companion evidence only.",
    }

    for row in rows:
        missing_fields = [field for field in required_stage_attempt_fields if not str(row[field] or "").strip()]
        attempt_key = str(row["attempt_key"] or "").strip()
        director_has_rationale = False
        if attempt_key in director_reasons:
            director_payload = director_reasons[attempt_key]
            director_has_rationale = bool(
                director_payload.get("selection_reason") or director_payload.get("verdict_reason")
            )
        if director_has_rationale:
            summary["director_rationale_available"] += 1
        if missing_fields:
            summary["rows_missing_required_fields"].append(
                {
                    "attempt_key": attempt_key,
                    "locator": _format_stage4_attempt_locator(row),
                    "missing_fields": missing_fields,
                    "director_rationale_available": director_has_rationale,
                }
            )

    if summary["rows_missing_required_fields"]:
        summary["status"] = "fail"
    return summary


def _summarize_stage4_rationale_contract(db: DBManager) -> dict:
    summary = {
        "status": "ok",
        "required_fields": list(_STAGE4_RATIONALE_FIELDS),
        "missing_columns": [],
        "stage4_row_count": 0,
        "retry_required_row_count": 0,
        "field_nonempty_counts": {field: 0 for field in _STAGE4_RATIONALE_FIELDS},
        "rows_missing_selection_reason": [],
        "rows_missing_verdict_reason": [],
        "rows_missing_retry_context": [],
    }

    columns = {
        str(row["name"] if isinstance(row, dict) else row[1] or "").strip()
        for row in db.conn.execute("PRAGMA table_info(stage_attempts)").fetchall()
    }
    summary["missing_columns"] = [field for field in _STAGE4_RATIONALE_FIELDS if field not in columns]
    if summary["missing_columns"]:
        summary["status"] = "fail"
        return summary

    rows = db.conn.execute(
        """
        SELECT ep_num, attempt_num, verdict, selection_reason, verdict_reason, open_review,
               fix_scope_reasoning, runtime_advisory, retry_directives
        FROM stage_attempts
        WHERE stage = 4
        ORDER BY id ASC
        """
    ).fetchall()
    summary["stage4_row_count"] = len(rows)

    for row in rows:
        locator = _format_stage4_attempt_locator(row)
        verdict = str(row["verdict"] or "").strip()
        for field in _STAGE4_RATIONALE_FIELDS:
            if str(row[field] or "").strip():
                summary["field_nonempty_counts"][field] += 1
        if not str(row["selection_reason"] or "").strip():
            summary["rows_missing_selection_reason"].append(locator)
        if not str(row["verdict_reason"] or "").strip():
            summary["rows_missing_verdict_reason"].append(locator)
        if verdict in _STAGE4_RETRY_REQUIRED_VERDICTS:
            summary["retry_required_row_count"] += 1
            if not any(str(row[field] or "").strip() for field in _STAGE4_RETRY_CONTEXT_FIELDS):
                summary["rows_missing_retry_context"].append(locator)

    if (
        summary["rows_missing_selection_reason"]
        or summary["rows_missing_verdict_reason"]
        or summary["rows_missing_retry_context"]
    ):
        summary["status"] = "fail"
    return summary


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
    impact["orphan_chain_link_anchors"] = len(_find_chain_link_keys(db, from_ep=from_ep))
    return impact


def _find_chain_link_keys(db: DBManager, *, from_ep: int) -> list[str]:
    rows = db.conn.execute("SELECT key FROM anchors WHERE key LIKE 'chain_link_%' ORDER BY key").fetchall()
    keys: list[str] = []
    for row in rows:
        key = str(row["key"] or "").strip()
        suffix = key.rsplit("_", 1)[-1]
        if suffix.isdigit() and int(suffix) >= int(from_ep):
            keys.append(key)
    return keys


def _extract_history_episode(history_entry) -> int | None:
    text = str(history_entry or "").strip()
    if not text.startswith("ep"):
        return None
    prefix = text.split(":", 1)[0]
    ep_text = prefix[2:]
    return int(ep_text) if ep_text.isdigit() else None


def _extract_episode_bible_delta_name(raw) -> str:
    if isinstance(raw, str):
        return raw.strip()
    if not isinstance(raw, dict):
        return ""
    for key in ("name", "npc", "target", "item"):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _collect_expected_world_state_minimums(db: DBManager, *, from_ep: int) -> dict:
    try:
        all_bibles = db.get_all_episode_bibles()
    except Exception:
        all_bibles = [db.get_episode_bible(ep) for ep in range(1, int(from_ep))]

    npc_names: set[str] = set()
    relationships: dict[str, str] = {}
    active_items: set[str] = set()
    for bible in all_bibles or []:
        if not isinstance(bible, dict):
            continue
        ep_num = int(bible.get("ep_num", 0) or 0)
        if ep_num <= 0 or ep_num >= int(from_ep):
            continue
        for raw_npc in bible.get("new_npcs") or []:
            npc_name = _extract_episode_bible_delta_name(raw_npc)
            if npc_name:
                npc_names.add(npc_name)
        for rel in bible.get("relationship_changes") or []:
            if not isinstance(rel, dict):
                continue
            npc_name = _extract_episode_bible_delta_name(rel)
            relation = str(rel.get("to") or "").strip()
            if npc_name:
                npc_names.add(npc_name)
            if npc_name and relation:
                relationships[npc_name] = relation
        for raw_item in bible.get("new_items") or []:
            item_name = _extract_episode_bible_delta_name(raw_item)
            if item_name:
                active_items.add(item_name)
        for raw_item in bible.get("lost_items") or []:
            item_name = _extract_episode_bible_delta_name(raw_item)
            if item_name:
                active_items.discard(item_name)

    return {
        "npc_names": sorted(npc_names),
        "relationships": {name: relationships[name] for name in sorted(relationships)},
        "active_items": sorted(active_items),
    }


def _collect_actual_world_state_minimums(world_state: dict) -> dict:
    alive_npcs = sorted(
        str(name).strip()
        for name, info in (world_state.get("alive_npcs") or {}).items()
        if isinstance(info, dict) and str(name).strip()
    )
    active_items = sorted(
        str(name).strip()
        for name, info in (world_state.get("active_items") or {}).items()
        if isinstance(info, dict)
        and str(name).strip()
        and str(info.get("status", "보유") or "보유").strip() not in {"소실", "파괴", "소모", "lost", "consumed", "destroyed"}
    )
    relationships = {
        str(name).strip(): str(value).strip()
        for name, value in (world_state.get("relationships") or {}).items()
        if str(name).strip() and str(value or "").strip()
    }
    return {
        "npc_names": alive_npcs,
        "relationships": relationships,
        "active_items": active_items,
    }


def _validate_truth_store_reset(db: DBManager, *, from_ep: int) -> dict:
    chain_links = _find_chain_link_keys(db, from_ep=from_ep)

    fact_ledger = db.load_anchor("fact_ledger") or {}
    fact_history_at_or_after: dict[str, list[str]] = {}
    for key, info in (fact_ledger.get("numbers") or {}).items():
        if not isinstance(info, dict):
            continue
        offending = [
            str(entry)
            for entry in (info.get("history") or [])
            if (_extract_history_episode(entry) or 0) >= int(from_ep)
        ]
        if offending:
            fact_history_at_or_after[str(key)] = offending

    world_state = db.load_anchor("world_state") or {}
    expected_minimums = _collect_expected_world_state_minimums(db, from_ep=from_ep)
    actual_minimums = _collect_actual_world_state_minimums(world_state)
    alive_npcs = [
        name
        for name, info in (world_state.get("alive_npcs") or {}).items()
        if isinstance(info, dict) and int(info.get("first_seen_ep", 0) or 0) >= int(from_ep)
    ]
    active_items = [
        name
        for name, info in (world_state.get("active_items") or {}).items()
        if isinstance(info, dict) and int(info.get("ep_acquired", 0) or 0) >= int(from_ep)
    ]
    world_last_updated_ep = int(world_state.get("last_updated_ep", 0) or 0)

    cleanup_ok = (
        not chain_links
        and not fact_history_at_or_after
        and not alive_npcs
        and not active_items
        and world_last_updated_ep <= max(0, int(from_ep) - 1)
    )
    actual_npc_names = set(actual_minimums["npc_names"])
    actual_active_items = set(actual_minimums["active_items"])
    missing_minimum_npcs = [name for name in expected_minimums["npc_names"] if name not in actual_npc_names]
    missing_minimum_active_items = [
        name for name in expected_minimums["active_items"] if name not in actual_active_items
    ]
    relationship_mismatches = [
        {
            "npc": name,
            "expected": expected_relation,
            "actual": actual_minimums["relationships"].get(name, ""),
        }
        for name, expected_relation in expected_minimums["relationships"].items()
        if actual_minimums["relationships"].get(name, "") != expected_relation
    ]
    minimum_truth_ok = (
        not missing_minimum_npcs
        and not missing_minimum_active_items
        and not relationship_mismatches
    )
    return {
        "status": "ok" if cleanup_ok and minimum_truth_ok else "fail",
        "cleanup_status": "ok" if cleanup_ok else "fail",
        "minimum_truth_status": "ok" if minimum_truth_ok else "fail",
        "from_ep": int(from_ep),
        "orphan_chain_links": chain_links,
        "fact_ledger_history_at_or_after": fact_history_at_or_after,
        "world_state_alive_npcs_at_or_after": alive_npcs,
        "world_state_active_items_at_or_after": active_items,
        "world_state_last_updated_ep": world_last_updated_ep,
        "expected_minimum_world_state": expected_minimums,
        "actual_minimum_world_state": actual_minimums,
        "missing_world_state_npcs": missing_minimum_npcs,
        "missing_world_state_active_items": missing_minimum_active_items,
        "world_state_relationship_mismatches": relationship_mismatches,
    }


def _reset_truth_store_anchors(db: DBManager, *, from_ep: int) -> None:
    for key in _find_chain_link_keys(db, from_ep=from_ep):
        db.cursor.execute("DELETE FROM anchors WHERE key = ?", (key,))

    FactLedger(db).rollback_to(from_ep)
    WorldStateManager(db).rollback_to(from_ep)


def _collect_stage34_cleanup_impact(db: DBManager, *, from_ep: int) -> dict[str, int]:
    cur = db.cursor
    impact = _collect_stage4_cleanup_impact(db, from_ep=from_ep)
    impact["blueprints_removed"] = int(
        cur.execute("SELECT COUNT(*) AS c FROM blueprints WHERE ep_num >= ?", (from_ep,)).fetchone()["c"]
    )
    impact["stage3_attempts"] = int(
        cur.execute("SELECT COUNT(*) AS c FROM stage_attempts WHERE stage = 3 AND ep_num >= ?", (from_ep,)).fetchone()[
            "c"
        ]
    )
    impact["stage3_director_selections"] = int(
        cur.execute(
            "SELECT COUNT(*) AS c FROM director_selections WHERE ep_num >= ? AND " + DBManager._director_stage_predicate(3),
            (from_ep,),
        ).fetchone()["c"]
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
        _reset_truth_store_anchors(db, from_ep=from_ep)
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    try:
        db.conn.execute("VACUUM")
    except Exception:
        pass


def _delete_stage34_db_outputs(db: DBManager, *, from_ep: int) -> None:
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
        cur.execute("DELETE FROM blueprints WHERE ep_num >= ?", (from_ep,))
        cur.execute(
            "DELETE FROM director_selections WHERE ep_num >= ? AND " + DBManager._director_stage_predicate(3),
            (from_ep,),
        )
        cur.execute("DELETE FROM stage_attempts WHERE stage = 3 AND ep_num >= ?", (from_ep,))
        _reset_truth_store_anchors(db, from_ep=from_ep)
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


def _clear_stage34_files(project_root: Path, *, from_ep: int) -> dict[str, int]:
    cleanup = _clear_stage4_files(project_root, from_ep=from_ep)
    blueprints_removed = 0
    blueprints_dir = project_root / "plans" / "blueprints"
    if blueprints_dir.exists():
        for blueprint in blueprints_dir.glob("ep_*.json"):
            ep_num = _extract_ep_num(blueprint.name)
            if ep_num is not None and ep_num >= from_ep:
                blueprint.unlink(missing_ok=True)
                blueprints_removed += 1
    cleanup["blueprint_files_removed"] = blueprints_removed
    return cleanup


def _evaluate_stage4_canary_gates(
    *,
    target_ep: int | None,
    draft_count: int,
    runtime_summary: dict,
    pass_rate_monitor_exists: bool,
    patch_trace_summary: dict,
    sink_alignment_summary: dict,
    rationale_contract_summary: dict,
    final_authority_contract_summary: dict | None = None,
    companion_audit_summary: dict | None = None,
    gate_repair_surface_summary: dict | None = None,
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
        warnings.append("pass_rate_monitor_cache_missing")

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
            "candidate_key_mismatches",
            "content_hash_mismatches",
            "artifact_path_mismatches",
            "artifact_metadata_missing",
            "artifact_missing_files",
        ):
            if sink_alignment_summary.get(field):
                errors.append(field)
        for field in (
            "initial_verdict_mismatches",
            "patch_strategy_mismatches",
            "selection_candidate_key_mismatches",
        ):
            if sink_alignment_summary.get(field):
                warnings.append(field)
        if int(sink_alignment_summary.get("legacy_key_attempts", 0) or 0) > 0:
            errors.append("legacy_key_attempts")
        _sink_alignment_status = str(sink_alignment_summary.get("status", "") or "").strip()
        if _sink_alignment_status == "fail":
            errors.append(f"sink_alignment_status:{_sink_alignment_status}")
        elif _sink_alignment_status not in ("", "ok") and _should_surface_stage4_sink_alignment_warn(
            sink_alignment_summary=sink_alignment_summary,
            final_authority_contract_summary=final_authority_contract_summary or {},
            companion_audit_summary=companion_audit_summary or {},
            gate_repair_surface_summary=gate_repair_surface_summary or {},
        ):
            warnings.append(f"sink_alignment_status:{_sink_alignment_status}")
    else:
        errors.append("sink_alignment_summary_empty")

    if rationale_contract_summary:
        if rationale_contract_summary.get("missing_columns"):
            errors.append("stage4_rationale_columns_missing")
        if rationale_contract_summary.get("rows_missing_selection_reason"):
            errors.append("stage4_selection_reason_missing")
        if rationale_contract_summary.get("rows_missing_verdict_reason"):
            errors.append("stage4_verdict_reason_missing")
        if rationale_contract_summary.get("rows_missing_retry_context"):
            errors.append("stage4_retry_context_missing")
        if int(rationale_contract_summary.get("stage4_row_count", 0) or 0) > 0:
            if int(rationale_contract_summary.get("retry_required_row_count", 0) or 0) == 0:
                warnings.append("stage4_retry_contract_not_exercised")
        if rationale_contract_summary.get("status") not in ("", "ok"):
            errors.append(f"stage4_rationale_status:{rationale_contract_summary.get('status')}")
    else:
        errors.append("stage4_rationale_summary_empty")

    if patch_trace_summary:
        avg_unchanged = patch_trace_summary.get("avg_unchanged_ratio")
        if avg_unchanged is not None and float(avg_unchanged) < 0.70:
            errors.append("avg_unchanged_ratio_below_gate")
        fallback_reasons = patch_trace_summary.get("fallback_reasons", {}) or {}
        for blocked in ("missing_patched_blocks", "no_usable_patched_blocks", "patched_output_too_short"):
            if int(fallback_reasons.get(blocked, 0) or 0) > 0:
                errors.append(f"fallback_reason:{blocked}")

    status = "fail" if errors else ("warn" if warnings else "pass")
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }


def _should_surface_stage4_sink_alignment_warn(
    *,
    sink_alignment_summary: dict,
    final_authority_contract_summary: dict,
    companion_audit_summary: dict,
    gate_repair_surface_summary: dict,
) -> bool:
    if not sink_alignment_summary:
        return False

    if any(
        sink_alignment_summary.get(field)
        for field in (
            "initial_verdict_mismatches",
            "patch_strategy_mismatches",
            "selection_candidate_key_mismatches",
        )
    ):
        return True

    if str((final_authority_contract_summary or {}).get("status", "") or "").strip() not in ("", "ok"):
        return True
    if str((companion_audit_summary or {}).get("status", "") or "").strip() not in ("", "ok"):
        return True
    if str((gate_repair_surface_summary or {}).get("status", "") or "").strip() not in ("", "ok"):
        return True

    return False


def _format_stage4_attempt_locator(row) -> str:
    ep_num = int(row["ep_num"] or 0)
    attempt_num = int(row["attempt_num"] or 0)
    verdict = str(row["verdict"] or "").strip() or "UNKNOWN"
    return f"ep{ep_num}:a{attempt_num}:{verdict}"


def latest_session_id_from_rows(rows) -> str:
    if not rows:
        return ""
    return str(rows[-1]["session_id"] or "").strip()


def _summary_status(summary: dict, *, default: str) -> str:
    if not summary:
        return default
    return str(summary.get("status", "") or default)


def _build_project_locator(project_root: Path) -> str:
    try:
        return project_root.resolve().relative_to(_APP_ROOT).as_posix()
    except Exception:
        return str(project_root)


def _build_project_name(project_root: Path) -> str:
    try:
        return project_root.resolve().relative_to((_APP_ROOT / "projects").resolve()).as_posix()
    except Exception:
        return project_root.name


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
