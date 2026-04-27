from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canary_path_utils import resolve_workspace_project_dir  # noqa: E402, I001


PASS_LIKE_VERDICTS = {"PASS", "PASS_WITH_WARNING", "PASS_WITH_FIX"}
CORE_LOG_RELATIVE_PATHS = (
    "logs/stage2_direct_supervised_result.json",
    "logs/stage3_direct_supervised_result.json",
    "logs/stage4_direct_supervised_result.json",
    "logs/stage4_direct_supervised_guarded_result.json",
    "logs/pass_rate_monitor.json",
    "logs/runtime_audit_summary.json",
    "logs/runtime_audit.jsonl",
    "logs/episode_production.jsonl",
    "logs/quality_metrics.jsonl",
)
OPTIONAL_LOG_DIRS = ("logs/metrics",)
ARCHIVE_EVIDENCE_SCOPE = "local_ignored_snapshot"
ARCHIVE_REPRODUCIBILITY_STATUS = "local_only_non_reproducible"
ARCHIVE_REPO_TRACKING_POLICY = "benchmark_record_directories_ignored_by_git"
INDEX_FIELDNAMES = [
    "run_id",
    "recorded_at",
    "project_name",
    "project_locator",
    "lane",
    "target_ep",
    "status",
    "runtime_audit_tag",
    "latest_session_id",
    "runtime_freshness_status",
    "git_branch",
    "git_head",
    "git_dirty",
    "s2_attempts",
    "s2_pass_like",
    "s2_duration_ms",
    "s2_cost_usd",
    "s3_attempts",
    "s3_pass_like",
    "s3_duration_ms",
    "s3_cost_usd",
    "s4_attempts",
    "s4_pass_like",
    "s4_duration_ms",
    "s4_tokens",
    "s4_cost_usd",
    "total_cost_usd",
    "archive_evidence_scope",
    "archive_reproducibility_status",
    "archive_repo_tracking_policy",
    "record_path",
    "db_snapshot_path",
    "notes",
]


@dataclass
class StageAggregate:
    stage: str
    source_file: str
    attempt_count: int = 0
    pass_like_count: int = 0
    reject_count: int = 0
    total_duration_ms: int = 0
    avg_duration_ms: int = 0
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    latest_episode: int = 0

    def finalize(self) -> StageAggregate:
        if self.attempt_count > 0:
            self.avg_duration_ms = int(round(self.total_duration_ms / self.attempt_count))
        self.total_cost_usd = round(self.total_cost_usd, 6)
        return self


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive a completed or interrupted project run into benchmarks/.")
    parser.add_argument("--project", required=True, help="Project name under projects/ or an absolute project path.")
    parser.add_argument("--lane", default="manual", help="Short run label such as stage4-supervised.")
    parser.add_argument("--target-ep", type=int, default=None, help="Optional target episode for this run.")
    parser.add_argument(
        "--status",
        default="snapshot",
        help="Run state label such as completed, interrupted, or snapshot.",
    )
    parser.add_argument("--notes", default="", help="Optional free-form note stored in manifest and index.")
    parser.add_argument(
        "--run-label",
        default=None,
        help="Optional folder label override. Defaults to the sanitized lane name.",
    )
    parser.add_argument(
        "--recorded-at",
        default=None,
        help="Optional ISO timestamp override. Defaults to local current time.",
    )
    parser.add_argument(
        "--benchmark-root",
        default="benchmarks",
        help="Archive root. Relative paths are resolved from the workspace root.",
    )
    parser.add_argument(
        "--workspace-root",
        default=str(ROOT),
        help="Workspace root containing projects/ and benchmarks/.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing record directory and update the matching CSV row.",
    )
    return parser.parse_args()


def archive_benchmark_record(
    *,
    workspace_root: str | Path,
    project: str,
    lane: str = "manual",
    target_ep: int | None = None,
    status: str = "snapshot",
    notes: str = "",
    run_label: str | None = None,
    recorded_at: str | None = None,
    benchmark_root: str | Path = "benchmarks",
    overwrite: bool = False,
) -> dict[str, Any]:
    workspace = Path(workspace_root).resolve()
    project_root = resolve_workspace_project_dir(
        workspace,
        project,
        prefer_canary=False,
        require_exists=True,
    )
    benchmark_dir = _resolve_benchmark_root(workspace, benchmark_root)
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    index_path = benchmark_dir / "benchmark_index.csv"
    _ensure_index_file(index_path)

    recorded_dt = _coerce_recorded_at(recorded_at)
    git_info = _collect_git_info(workspace)
    run_id = _build_run_id(
        recorded_dt=recorded_dt,
        lane=lane,
        run_label=run_label,
        target_ep=target_ep,
        git_head=git_info["head"],
    )
    record_root = benchmark_dir / project_root.name / run_id
    if record_root.exists():
        if not overwrite:
            raise FileExistsError(f"benchmark record already exists: {record_root}")
    build_root = _build_staging_record_root(record_root) if overwrite else record_root

    try:
        stage_metrics = collect_stage_metrics(project_root)
        runtime_summary = _load_json(project_root / "logs" / "runtime_audit_summary.json")
        latest_session_id = _extract_latest_session_id(runtime_summary)
        runtime_audit_tag = str(runtime_summary.get("tag", "")) if isinstance(runtime_summary, dict) else ""
        runtime_summary_window = runtime_summary.get("summary_window", {}) if isinstance(runtime_summary, dict) else {}
        runtime_run_scope = _extract_runtime_run_scope(runtime_summary, latest_session_id=latest_session_id)
        runtime_freshness = _extract_runtime_freshness(runtime_summary, run_scope=runtime_run_scope)
        stage4_diagnostic_packet = _build_stage4_diagnostic_packet(
            project_root=project_root,
            runtime_summary=runtime_summary,
            runtime_freshness=runtime_freshness,
            stage4_metrics=stage_metrics["stage4"],
        )
        effective_status = _resolve_benchmark_status(
            status=status,
            target_ep=target_ep,
            lane=lane,
            stage_metrics=stage_metrics,
            notes=notes,
            project_root=project_root,
        )

        copied_files = _copy_snapshot_payload(project_root=project_root, record_root=build_root)
        copied_files = _rewrite_copied_file_archives(copied_files, source_root=build_root, final_root=record_root)
        stage_metrics_path = build_root / "stage_metrics.csv"
        _write_stage_metrics_csv(stage_metrics_path, stage_metrics)

        project_locator = _display_relative_path(workspace, project_root)
        record_path = _display_relative_path(workspace, record_root)
        db_snapshot_path = _display_relative_path(workspace, record_root / "snapshots" / "project_data.db")
        archive_evidence = _build_archive_evidence_policy(
            record_path=record_path,
            db_snapshot_path=db_snapshot_path,
            copied_files=copied_files,
        )
        manifest = {
            "schema_version": "benchmark_record_v1",
            "run_id": run_id,
            "recorded_at": recorded_dt.isoformat(timespec="seconds"),
            "workspace_root": str(workspace),
            "project_name": project_root.name,
            "project_root": str(project_root),
            "project_locator": project_locator,
            "lane": lane,
            "target_ep": target_ep,
            "status": effective_status,
            "requested_status": status,
            "notes": notes,
            "benchmark_root": str(benchmark_dir),
            "record_root": str(record_root),
            "runtime_summary": {
                "runtime_audit_tag": runtime_audit_tag,
                "latest_session_id": latest_session_id,
                "summary_window": runtime_summary_window if isinstance(runtime_summary_window, dict) else {},
                "run_scope": runtime_run_scope,
                "freshness": runtime_freshness,
            },
            "stage4_diagnostic_packet": stage4_diagnostic_packet,
            "workspace_git": {
                "branch": git_info["branch"],
                "head": git_info["head"],
                "dirty": git_info["dirty"],
            },
            "archive_evidence": archive_evidence,
            "copied_files": copied_files,
            "stage_metrics": {key: asdict(value) for key, value in stage_metrics.items()},
        }
        _write_json(build_root / "manifest.json", manifest)
        if build_root != record_root:
            _commit_staged_record(build_root=build_root, record_root=record_root)
    except Exception:
        if build_root != record_root and build_root.exists():
            shutil.rmtree(build_root)
        raise

    index_row = _build_index_row(
        manifest=manifest,
        project_locator=project_locator,
        record_path=record_path,
        db_snapshot_path=db_snapshot_path,
        stage_metrics=stage_metrics,
    )
    _upsert_index_row(index_path=index_path, row=index_row)
    return manifest


def collect_stage_metrics(project_root: str | Path) -> dict[str, StageAggregate]:
    root = Path(project_root)
    pass_rate_rows = _load_pass_rate_rows(root / "logs" / "pass_rate_monitor.json")
    episode_rows = _load_jsonl(root / "logs" / "episode_production.jsonl")

    stage2_rows = _dedupe_attempt_rows(row for row in pass_rate_rows if _safe_int(row.get("stage")) == 2)
    stage3_rows = _dedupe_attempt_rows(row for row in pass_rate_rows if _safe_int(row.get("stage")) == 3)
    stage4_rows = _dedupe_attempt_rows(row for row in episode_rows if _is_stage4_attempt_row(row))

    return {
        "stage2": _aggregate_rows("stage2", "logs/pass_rate_monitor.json", stage2_rows, episode_key="episode"),
        "stage3": _aggregate_rows("stage3", "logs/pass_rate_monitor.json", stage3_rows, episode_key="episode"),
        "stage4": _aggregate_rows("stage4", "logs/episode_production.jsonl", stage4_rows, episode_key="ep"),
    }


def _resolve_benchmark_status(
    *,
    status: str,
    target_ep: int | None,
    lane: str,
    stage_metrics: dict[str, StageAggregate],
    notes: str,
    project_root: Path | None = None,
) -> str:
    normalized_status = str(status or "snapshot").strip() or "snapshot"
    if normalized_status != "completed" or target_ep is None:
        return normalized_status

    latest_ep = _benchmark_latest_progress_episode(lane=lane, stage_metrics=stage_metrics, notes=notes)
    if latest_ep is None or latest_ep < int(target_ep):
        return "operational_failure"
    db_latest_ep = _benchmark_latest_settled_db_episode(project_root=project_root, lane=lane)
    if db_latest_ep is not None and db_latest_ep < int(target_ep):
        return "operational_failure"
    if db_latest_ep is None and _benchmark_requires_settled_db_crosscheck(lane):
        return "operational_failure"
    return normalized_status


def _benchmark_requires_settled_db_crosscheck(lane: str) -> bool:
    return "stage4" in str(lane or "").lower()


def _benchmark_latest_settled_db_episode(*, project_root: Path | None, lane: str) -> int | None:
    if not _benchmark_requires_settled_db_crosscheck(lane) or project_root is None:
        return None

    db_path = Path(project_root) / "project_data.db"
    if not db_path.exists():
        return None

    try:
        conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    except sqlite3.Error:
        return None

    try:
        table_row = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='manuscripts'").fetchone()
        if table_row is None:
            return None
        row = conn.execute("SELECT MAX(ep_num) FROM manuscripts").fetchone()
        if not row or row[0] is None:
            return 0
        return _safe_int(row[0])
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def _benchmark_latest_progress_episode(
    *,
    lane: str,
    stage_metrics: dict[str, StageAggregate],
    notes: str,
) -> int | None:
    lane_text = str(lane or "").lower()
    if "stage4" in lane_text:
        latest = stage_metrics["stage4"].latest_episode
    elif "stage3" in lane_text:
        latest = stage_metrics["stage3"].latest_episode
    elif "stage2" in lane_text:
        latest = stage_metrics["stage2"].latest_episode
    else:
        latest = max(metric.latest_episode for metric in stage_metrics.values())

    noted_latest = _extract_latest_episode_from_notes(notes)
    if noted_latest is not None:
        latest = max(latest, noted_latest)
    return latest if latest > 0 else None


def _extract_latest_episode_from_notes(notes: str) -> int | None:
    match = re.search(r"(?:after_latest_ep|latest_(?:blueprint|manuscript)?_?ep)\s*=\s*(\d+)", str(notes or ""))
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _aggregate_rows(
    stage_label: str,
    source_file: str,
    rows: list[dict[str, Any]],
    *,
    episode_key: str,
) -> StageAggregate:
    aggregate = StageAggregate(stage=stage_label, source_file=source_file)
    for row in rows:
        aggregate.attempt_count += 1
        aggregate.total_duration_ms += _safe_int(row.get("duration_ms"))
        aggregate.total_cost_usd += _extract_cost_usd(row)
        aggregate.total_tokens += _extract_total_tokens(row)
        aggregate.latest_episode = max(aggregate.latest_episode, _safe_int(row.get(episode_key)))
        if _is_pass_like(row):
            aggregate.pass_like_count += 1
    aggregate.reject_count = max(aggregate.attempt_count - aggregate.pass_like_count, 0)
    return aggregate.finalize()


def _build_index_row(
    *,
    manifest: dict[str, Any],
    project_locator: str,
    record_path: str,
    db_snapshot_path: str,
    stage_metrics: dict[str, StageAggregate],
) -> dict[str, str]:
    stage2 = stage_metrics["stage2"]
    stage3 = stage_metrics["stage3"]
    stage4 = stage_metrics["stage4"]
    total_cost_usd = round(stage2.total_cost_usd + stage3.total_cost_usd + stage4.total_cost_usd, 6)
    git_info = manifest.get("workspace_git", {})
    runtime_summary = manifest.get("runtime_summary", {})
    archive_evidence = (
        manifest.get("archive_evidence", {}) if isinstance(manifest.get("archive_evidence"), dict) else {}
    )
    return {
        "run_id": str(manifest["run_id"]),
        "recorded_at": str(manifest["recorded_at"]),
        "project_name": str(manifest["project_name"]),
        "project_locator": project_locator,
        "lane": str(manifest["lane"]),
        "target_ep": "" if manifest.get("target_ep") is None else str(manifest["target_ep"]),
        "status": str(manifest["status"]),
        "runtime_audit_tag": str(runtime_summary.get("runtime_audit_tag", "")),
        "latest_session_id": str(runtime_summary.get("latest_session_id", "")),
        "runtime_freshness_status": str((runtime_summary.get("freshness", {}) or {}).get("status", "")),
        "git_branch": str(git_info.get("branch", "")),
        "git_head": str(git_info.get("head", "")),
        "git_dirty": "true" if git_info.get("dirty") else "false",
        "s2_attempts": str(stage2.attempt_count),
        "s2_pass_like": str(stage2.pass_like_count),
        "s2_duration_ms": str(stage2.total_duration_ms),
        "s2_cost_usd": f"{stage2.total_cost_usd:.6f}",
        "s3_attempts": str(stage3.attempt_count),
        "s3_pass_like": str(stage3.pass_like_count),
        "s3_duration_ms": str(stage3.total_duration_ms),
        "s3_cost_usd": f"{stage3.total_cost_usd:.6f}",
        "s4_attempts": str(stage4.attempt_count),
        "s4_pass_like": str(stage4.pass_like_count),
        "s4_duration_ms": str(stage4.total_duration_ms),
        "s4_tokens": str(stage4.total_tokens),
        "s4_cost_usd": f"{stage4.total_cost_usd:.6f}",
        "total_cost_usd": f"{total_cost_usd:.6f}",
        "archive_evidence_scope": str(archive_evidence.get("scope", "")),
        "archive_reproducibility_status": str(archive_evidence.get("reproducibility_status", "")),
        "archive_repo_tracking_policy": str(archive_evidence.get("repo_tracking_policy", "")),
        "record_path": record_path,
        "db_snapshot_path": db_snapshot_path,
        "notes": str(manifest.get("notes", "")),
    }


def _build_archive_evidence_policy(
    *, record_path: str, db_snapshot_path: str, copied_files: list[dict[str, str]]
) -> dict[str, Any]:
    return {
        "scope": ARCHIVE_EVIDENCE_SCOPE,
        "reproducibility_status": ARCHIVE_REPRODUCIBILITY_STATUS,
        "repo_tracking_policy": ARCHIVE_REPO_TRACKING_POLICY,
        "record_path": record_path,
        "db_snapshot_path": db_snapshot_path,
        "copied_file_count": len(copied_files),
        "operator_note": (
            "benchmark_index.csv is durable repo metadata; backing snapshot bytes are local-only unless "
            "a separate export or tracked evidence bundle is created"
        ),
    }


def _copy_snapshot_payload(*, project_root: Path, record_root: Path) -> list[dict[str, str]]:
    copied: list[dict[str, str]] = []
    db_source = project_root / "project_data.db"
    db_target = record_root / "snapshots" / "project_data.db"
    _copy_file(db_source, db_target)
    copied.append({"source": str(db_source), "archive": str(db_target)})

    for relative_path in CORE_LOG_RELATIVE_PATHS:
        source = project_root / relative_path
        if not source.exists():
            continue
        target = record_root / relative_path
        _copy_file(source, target)
        copied.append({"source": str(source), "archive": str(target)})

    for relative_dir in OPTIONAL_LOG_DIRS:
        source_dir = project_root / relative_dir
        if not source_dir.exists():
            continue
        target_dir = record_root / relative_dir
        shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
        copied.append({"source": str(source_dir), "archive": str(target_dir)})

    return copied


def _build_staging_record_root(record_root: Path) -> Path:
    return record_root.parent / f".{record_root.name}.staging-{uuid.uuid4().hex}"


def _rewrite_copied_file_archives(
    copied_files: list[dict[str, str]], *, source_root: Path, final_root: Path
) -> list[dict[str, str]]:
    rewritten: list[dict[str, str]] = []
    for entry in copied_files:
        archive_path = Path(entry.get("archive", ""))
        try:
            relative_archive = archive_path.resolve().relative_to(source_root.resolve())
            archive = str(final_root / relative_archive)
        except Exception:
            archive = str(archive_path)
        rewritten.append({**entry, "archive": archive})
    return rewritten


def _commit_staged_record(*, build_root: Path, record_root: Path) -> None:
    record_root.parent.mkdir(parents=True, exist_ok=True)
    if not record_root.exists():
        build_root.rename(record_root)
        return

    backup_root = record_root.parent / f".{record_root.name}.backup-{uuid.uuid4().hex}"
    record_root.rename(backup_root)
    try:
        build_root.rename(record_root)
    except Exception:
        if record_root.exists():
            shutil.rmtree(record_root)
        backup_root.rename(record_root)
        raise
    shutil.rmtree(backup_root)


def _ensure_index_file(index_path: Path) -> None:
    if index_path.exists():
        return
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDNAMES)
        writer.writeheader()


def _upsert_index_row(*, index_path: Path, row: dict[str, str]) -> None:
    rows: list[dict[str, str]] = []
    if index_path.exists():
        with index_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

    replaced = False
    for idx, existing in enumerate(rows):
        if existing.get("run_id") == row["run_id"]:
            rows[idx] = row
            replaced = True
            break
    if not replaced:
        rows.append(row)

    with index_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def _write_stage_metrics_csv(path: Path, stage_metrics: dict[str, StageAggregate]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "stage",
        "source_file",
        "attempt_count",
        "pass_like_count",
        "reject_count",
        "total_duration_ms",
        "avg_duration_ms",
        "total_cost_usd",
        "total_tokens",
        "latest_episode",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for key in ("stage2", "stage3", "stage4"):
            metric = stage_metrics[key]
            writer.writerow(
                {
                    "stage": metric.stage,
                    "source_file": metric.source_file,
                    "attempt_count": metric.attempt_count,
                    "pass_like_count": metric.pass_like_count,
                    "reject_count": metric.reject_count,
                    "total_duration_ms": metric.total_duration_ms,
                    "avg_duration_ms": metric.avg_duration_ms,
                    "total_cost_usd": f"{metric.total_cost_usd:.6f}",
                    "total_tokens": metric.total_tokens,
                    "latest_episode": metric.latest_episode,
                }
            )


def _load_pass_rate_rows(path: Path) -> list[dict[str, Any]]:
    payload = _load_json(path)
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return [row for row in payload["records"] if isinstance(row, dict)]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def _load_json(path: Path) -> dict[str, Any] | list[Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _extract_latest_session_id(runtime_summary: dict[str, Any] | list[Any]) -> str:
    if not isinstance(runtime_summary, dict):
        return ""
    candidate_paths = (
        ("proof_digest", "operational_metadata", "latest_session_id"),
        ("operational_metadata", "latest_session_id"),
        ("latest_session_id",),
        ("proof_digest", "session_lineage", "structured_session_id"),
    )
    for path in candidate_paths:
        value: Any = runtime_summary
        for key in path:
            if not isinstance(value, dict):
                value = ""
                break
            value = value.get(key)
        if value:
            return str(value)
    return ""


def _extract_runtime_run_scope(
    runtime_summary: dict[str, Any] | list[Any], *, latest_session_id: str
) -> dict[str, Any]:
    if not isinstance(runtime_summary, dict) or not runtime_summary:
        return {
            "status": "unavailable",
            "engine_run_id": "",
            "latest_session_id": "",
            "basis": [],
            "authority_role": "companion_snapshot",
        }
    raw_scope = runtime_summary.get("run_scope", {})
    run_scope = dict(raw_scope) if isinstance(raw_scope, dict) else {}
    engine_run_id = str(run_scope.get("engine_run_id", "") or "").strip()
    resolved_session_id = str(run_scope.get("latest_session_id") or latest_session_id or "").strip()
    basis = [str(item) for item in run_scope.get("basis", []) if str(item or "").strip()]
    if engine_run_id and not any(item == "GEULDOBI_RUN_ID" for item in basis):
        basis.append("GEULDOBI_RUN_ID")
    if resolved_session_id and not any("session" in item for item in basis):
        basis.append("latest_session_id")
    return {
        **run_scope,
        "status": str(run_scope.get("status") or ("scoped" if basis else "unknown")),
        "engine_run_id": engine_run_id,
        "latest_session_id": resolved_session_id,
        "basis": basis,
        "authority_role": str(run_scope.get("authority_role") or "companion_snapshot"),
    }


def _extract_runtime_freshness(
    runtime_summary: dict[str, Any] | list[Any], *, run_scope: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(runtime_summary, dict) or not runtime_summary:
        return {
            "status": "unavailable",
            "basis": [],
            "engine_run_id_present": False,
            "latest_session_id_present": False,
            "operator_guidance_only": True,
        }
    raw_freshness = runtime_summary.get("freshness", {})
    if isinstance(raw_freshness, dict) and raw_freshness:
        return {
            **raw_freshness,
            "status": str(raw_freshness.get("status") or run_scope.get("status") or "unknown"),
            "basis": list(raw_freshness.get("basis") or run_scope.get("basis") or []),
            "engine_run_id_present": bool(raw_freshness.get("engine_run_id_present"))
            or bool(run_scope.get("engine_run_id")),
            "latest_session_id_present": bool(raw_freshness.get("latest_session_id_present"))
            or bool(run_scope.get("latest_session_id")),
            "operator_guidance_only": True,
        }
    basis = list(run_scope.get("basis") or [])
    return {
        "status": str(run_scope.get("status") or ("scoped" if basis else "unknown")),
        "basis": basis,
        "engine_run_id_present": bool(run_scope.get("engine_run_id")),
        "latest_session_id_present": bool(run_scope.get("latest_session_id")),
        "operator_guidance_only": True,
    }


def _build_stage4_diagnostic_packet(
    *,
    project_root: Path,
    runtime_summary: dict[str, Any] | list[Any],
    runtime_freshness: dict[str, Any],
    stage4_metrics: StageAggregate,
) -> dict[str, Any]:
    episode_rows = _load_jsonl(project_root / "logs" / "episode_production.jsonl")
    runtime_audit_rows = _load_jsonl(project_root / "logs" / "runtime_audit.jsonl")
    proof_digest = runtime_summary.get("proof_digest", {}) if isinstance(runtime_summary, dict) else {}
    stage4_digest = {}
    if isinstance(proof_digest, dict):
        stages = proof_digest.get("stages", {})
        if isinstance(stages, dict):
            stage4_digest = stages.get("stage4", {}) if isinstance(stages.get("stage4", {}), dict) else {}

    issue_counts = _positive_int_dict(stage4_digest.get("issue_counts", {}))
    warning_taxonomy_counts = _positive_int_dict(stage4_digest.get("warning_taxonomy_counts", {}))
    episode_cove_advisory_count = _count_rows_by_event(episode_rows, "STAGE4_COVE_RUNTIME_ADVISORY")
    runtime_audit_cove_advisory_count = _count_rows_by_type(runtime_audit_rows, "stage4_cove_runtime_advisory")
    cove_fail_closed_count = _count_stage4_retry_pathology(
        episode_rows,
        pathology_source="cove_fail_closed",
        flag_name="cove_fail_closed",
    )
    post_select_conflict_count = _count_stage4_retry_pathology(
        episode_rows,
        pathology_source="post_select_conflict",
    )
    settled_director_divergence_count = (
        int(issue_counts.get("final_verdict_mismatches", 0) or 0)
        + int(issue_counts.get("director_verdict_mismatches", 0) or 0)
    )
    return {
        "schema_version": "stage4_diagnostic_packet_v1",
        "authority_role": "benchmark_companion_snapshot",
        "operator_guidance_only": True,
        "stage4_attempt_count": int(stage4_metrics.attempt_count),
        "stage4_pass_like_count": int(stage4_metrics.pass_like_count),
        "stage4_reject_count": int(stage4_metrics.reject_count),
        "runtime_summary_freshness_status": str(runtime_freshness.get("status", "") or ""),
        "runtime_summary_scope_status": str(runtime_freshness.get("scope_status", "") or ""),
        "proof_digest_status": str(proof_digest.get("status", "") or "") if isinstance(proof_digest, dict) else "",
        "proof_stage4_status": str(stage4_digest.get("status", "") or ""),
        "proof_issue_counts": issue_counts,
        "proof_warning_taxonomy_counts": warning_taxonomy_counts,
        "runtime_advisory_warn_count": int(warning_taxonomy_counts.get("runtime_advisory_warn", 0) or 0),
        "cove_runtime_advisory_count": max(episode_cove_advisory_count, runtime_audit_cove_advisory_count),
        "pass_preserved_cove_advisory_count": _count_pass_preserved_cove_advisories(episode_rows),
        "cove_semantic_fail_closed_count": cove_fail_closed_count,
        "post_select_conflict_count": post_select_conflict_count,
        "settled_director_divergence_count": settled_director_divergence_count,
        "source_counts": {
            "episode_cove_runtime_advisory": episode_cove_advisory_count,
            "runtime_audit_cove_runtime_advisory": runtime_audit_cove_advisory_count,
            "episode_cove_semantic_fail_closed": cove_fail_closed_count,
            "episode_post_select_conflict": post_select_conflict_count,
        },
    }


def _positive_int_dict(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw_count in value.items():
        count = _safe_int(raw_count)
        if count > 0:
            result[str(key)] = count
    return result


def _count_rows_by_event(rows: list[dict[str, Any]], event_name: str) -> int:
    expected = str(event_name or "").strip().upper()
    return sum(1 for row in rows if str(row.get("event", "") or "").strip().upper() == expected)


def _count_rows_by_type(rows: list[dict[str, Any]], event_type: str) -> int:
    expected = str(event_type or "").strip()
    return sum(1 for row in rows if str(row.get("type", "") or "").strip() == expected)


def _count_pass_preserved_cove_advisories(rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        if str(row.get("event", "") or "").strip().upper() != "STAGE4_COVE_RUNTIME_ADVISORY":
            continue
        if row.get("director_pass_preserved") is False:
            continue
        count += 1
    return count


def _count_stage4_retry_pathology(
    rows: list[dict[str, Any]],
    *,
    pathology_source: str,
    flag_name: str | None = None,
) -> int:
    expected_source = str(pathology_source or "").strip()
    count = 0
    for row in rows:
        if str(row.get("event", "") or "").strip().upper() != "STAGE4_RETRY_PATHOLOGY":
            continue
        row_source = str(row.get("pathology_source") or row.get("retry_pathology_source") or "").strip()
        if row_source == expected_source or (flag_name and bool(row.get(flag_name))):
            count += 1
    return count


def _dedupe_attempt_rows(rows: Any) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        attempt_key = str(row.get("attempt_key") or f"row:{idx}")
        deduped[attempt_key] = row
    return list(deduped.values())


def _is_stage4_attempt_row(row: dict[str, Any]) -> bool:
    if not isinstance(row, dict):
        return False
    if row.get("event"):
        return False
    if not row.get("attempt_key"):
        return False
    if _safe_int(row.get("ep")) <= 0:
        return False
    verdict = row.get("final_verdict") or row.get("verdict") or row.get("initial_verdict")
    return bool(verdict)


def _is_pass_like(row: dict[str, Any]) -> bool:
    verdict = str(row.get("final_verdict") or row.get("verdict") or "").strip().upper()
    if verdict in PASS_LIKE_VERDICTS:
        return True
    return bool(row.get("success"))


def _extract_cost_usd(row: dict[str, Any]) -> float:
    for key in ("round_total_cost_usd", "token_cost", "total_cost_usd"):
        value = row.get(key)
        if value not in (None, ""):
            return _safe_float(value)
    token_usage = row.get("token_usage")
    if isinstance(token_usage, dict):
        return _safe_float(token_usage.get("total_cost_usd"))
    return 0.0


def _extract_total_tokens(row: dict[str, Any]) -> int:
    for key in ("round_total_tokens", "total_tokens"):
        value = row.get(key)
        if value not in (None, ""):
            return _safe_int(value)
    token_usage = row.get("token_usage")
    if isinstance(token_usage, dict):
        return _safe_int(token_usage.get("total_tokens"))
    return 0


def _copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _resolve_benchmark_root(workspace_root: Path, benchmark_root: str | Path) -> Path:
    candidate = Path(benchmark_root)
    if candidate.is_absolute():
        return candidate.resolve()
    return (workspace_root / candidate).resolve()


def _build_run_id(
    *,
    recorded_dt: datetime,
    lane: str,
    run_label: str | None,
    target_ep: int | None,
    git_head: str,
) -> str:
    label = _slug_token(run_label or lane or "manual")
    target_token = f"target-ep{target_ep}" if target_ep is not None else "target-open"
    head_token = _slug_token(git_head or "nogit")
    return f"{recorded_dt.strftime('%Y%m%d_%H%M%S')}__{label}__{target_token}__{head_token}"


def _coerce_recorded_at(recorded_at: str | None) -> datetime:
    if not recorded_at:
        return datetime.now().astimezone()
    parsed = datetime.fromisoformat(recorded_at)
    if parsed.tzinfo is None:
        return parsed.astimezone()
    return parsed


def _collect_git_info(workspace_root: Path) -> dict[str, Any]:
    branch = _run_git_command(workspace_root, "branch", "--show-current")
    head = _run_git_command(workspace_root, "rev-parse", "--short", "HEAD")
    dirty_status = _run_git_command(workspace_root, "status", "--short")
    return {
        "branch": branch,
        "head": head,
        "dirty": bool(dirty_status.strip()),
    }


def _run_git_command(workspace_root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(workspace_root), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except Exception:
        return ""
    return result.stdout.strip()


def _display_relative_path(workspace_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except Exception:
        return str(path.resolve())


def _slug_token(value: str) -> str:
    token = []
    last_was_sep = False
    for char in str(value).strip().lower():
        if char.isascii() and char.isalnum():
            token.append(char)
            last_was_sep = False
            continue
        if last_was_sep:
            continue
        token.append("-")
        last_was_sep = True
    cleaned = "".join(token).strip("-")
    return cleaned or "run"


def _safe_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    manifest = archive_benchmark_record(
        workspace_root=args.workspace_root,
        project=args.project,
        lane=args.lane,
        target_ep=args.target_ep,
        status=args.status,
        notes=args.notes,
        run_label=args.run_label,
        recorded_at=args.recorded_at,
        benchmark_root=args.benchmark_root,
        overwrite=args.overwrite,
    )
    print(json.dumps({"run_id": manifest["run_id"], "record_root": manifest["record_root"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
