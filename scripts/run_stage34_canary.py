"""Prepare, run, and analyze a repeatable Stage 3->4 frontier-lag canary project.

Validation tier: full_canary_proof
Mutation boundary: boots live app surfaces, patches input, and writes proof artifacts.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main_a import SovereignApp  # noqa: E402
from modules.core.db_manager import DBManager  # noqa: E402
from modules.core.failure_analyzer import FailureAnalyzer  # noqa: E402
from modules.core.pass_rate_monitor import PassRateMonitor  # noqa: E402
from scripts.benchmark_archive_runtime import safe_archive_benchmark_record  # noqa: E402
from modules.core.stage4_canary_tools import (  # noqa: E402
    build_stage4_canary_summary,
    latest_session_id_from_rows,
    prepare_stage34_canary_project,
)
from scripts.canary_path_utils import project_name_from_path, resolve_workspace_project_dir  # noqa: E402
from scripts.regression_validation_tiers import FULL_CANARY_PROOF  # noqa: E402

VALIDATION_TIER = FULL_CANARY_PROOF
MUTATES_PROJECT_STATE = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 3->4 frontier canary helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="copy a baseline project and reset Stage 3/4 outputs")
    prepare.add_argument("--source-project", required=True)
    prepare.add_argument("--target-project", required=True)
    prepare.add_argument("--from-ep", type=int, default=1)
    prepare.add_argument("--force", action="store_true")

    run = subparsers.add_parser("run", help="run frontier-lag final close on a prepared project")
    run.add_argument("--project", required=True)
    run.add_argument("--target-ep", type=int, default=4)

    analyze = subparsers.add_parser("analyze", help="analyze an existing Stage 3->4 canary project")
    analyze.add_argument("--project", required=True)
    analyze.add_argument("--target-ep", type=int, default=4)

    full = subparsers.add_parser("full", help="prepare, run, and analyze in one command")
    full.add_argument("--source-project", required=True)
    full.add_argument("--target-project", required=True)
    full.add_argument("--from-ep", type=int, default=1)
    full.add_argument("--target-ep", type=int, default=4)
    full.add_argument("--force", action="store_true")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "prepare":
        payload = prepare_canary(args.source_project, args.target_project, from_ep=args.from_ep, force=args.force)
        _print_json(payload)
        return 0

    if args.command == "run":
        payload = run_canary(args.project, target_ep=args.target_ep)
        _print_json(payload)
        return 0

    if args.command == "analyze":
        payload = analyze_canary(args.project, target_ep=args.target_ep)
        _print_json(payload)
        return 0

    payload = prepare_canary(args.source_project, args.target_project, from_ep=args.from_ep, force=args.force)
    _print_json(payload)
    payload = run_canary(args.target_project, target_ep=args.target_ep)
    _print_json(payload)
    return 0


def prepare_canary(source_project: str, target_project: str, *, from_ep: int, force: bool) -> dict:
    source_root = resolve_workspace_project_dir(PROJECT_ROOT, source_project, prefer_canary=False, require_exists=True)
    target_root = resolve_workspace_project_dir(PROJECT_ROOT, target_project, prefer_canary=True, require_exists=False)
    return prepare_stage34_canary_project(source_root, target_root, from_ep=from_ep, force=force)


def run_canary(project_name: str, *, target_ep: int) -> dict:
    project_root = resolve_workspace_project_dir(PROJECT_ROOT, project_name, prefer_canary=True, require_exists=True)
    runtime_project_name = project_name_from_path(PROJECT_ROOT, project_root)
    selected_genre = _load_project_genre(project_root)
    if not selected_genre:
        raise RuntimeError(f"genre_info anchor missing or invalid for {runtime_project_name}")

    app = _boot_app(runtime_project_name, selected_genre)
    try:
        _ensure_pass_rate_monitor(app, project_root)
        app._get_int_input = lambda *args, **kwargs: kwargs.get("default", 1)
        with (
            _clamp_frontier_lag_to_target_ep(app, target_ep=target_ep),
            patch("builtins.input", side_effect=_auto_input),
        ):
            app._one_stop_pipeline_frontier_lag()
        if getattr(app, "pass_rate_monitor", None):
            app.pass_rate_monitor.save()
        if hasattr(app, "_flush_audit_buffer"):
            app._flush_audit_buffer()
    finally:
        _close_app_handles(app)

    payload = analyze_canary(runtime_project_name, target_ep=target_ep)
    payload["benchmark_archive"] = safe_archive_benchmark_record(
        workspace_root=PROJECT_ROOT,
        project=runtime_project_name,
        lane="stage34-canary",
        target_ep=target_ep,
        status="completed" if payload.get("multi_stage_proof_scope_summary", {}).get("status") == "pass" else "partial",
        notes=f"stage34 frontier canary run; target_ep={target_ep}",
    )
    return payload


def analyze_canary(project_name: str, *, target_ep: int) -> dict:
    project_root = resolve_workspace_project_dir(PROJECT_ROOT, project_name, prefer_canary=True, require_exists=True)
    stage4_summary = build_stage4_canary_summary(project_root, target_ep=target_ep)

    db = DBManager(project_root / "project_data.db")
    try:
        analyzer = FailureAnalyzer(db, project_path=project_root)
        stage3_rows = db.conn.execute(
            """
            SELECT id, session_id
            FROM stage_attempts
            WHERE stage = 3
            ORDER BY id ASC
            """
        ).fetchall()
        stage3_session_id = latest_session_id_from_rows(stage3_rows)
        stage4_session_id = str(stage4_summary.get("latest_session_id", "") or "")
        shared_session_id = stage4_session_id if stage4_session_id and stage4_session_id == stage3_session_id else ""
        stage3_current_session_summary = analyzer.sink_alignment_summary(
            stage=3,
            include_session_decisions=True,
            session_id=stage3_session_id,
        )
    finally:
        db.close()

    multi_stage_summary = _build_multi_stage_summary(
        stage3_session_id=stage3_session_id,
        stage4_session_id=stage4_session_id,
        shared_session_id=shared_session_id,
        stage3_current_session_summary=stage3_current_session_summary,
        stage4_summary=stage4_summary,
    )

    payload = {
        "summary_role": "stage34_frontier_live_canary",
        "project": project_name,
        "project_locator": stage4_summary.get("project_locator", ""),
        "project_root": stage4_summary.get("project_root", ""),
        "target_ep": target_ep,
        "stage3_latest_session_id": stage3_session_id,
        "stage4_latest_session_id": stage4_session_id,
        "shared_session_id": shared_session_id,
        "stage3_current_session_sink_alignment_summary": stage3_current_session_summary,
        "stage4_canary_summary": stage4_summary,
        "multi_stage_proof_scope_summary": multi_stage_summary,
    }

    summary_path = project_root / "logs" / "stage34_canary_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _build_multi_stage_summary(
    *,
    stage3_session_id: str,
    stage4_session_id: str,
    shared_session_id: str,
    stage3_current_session_summary: dict,
    stage4_summary: dict,
) -> dict:
    stage4_current_summary = stage4_summary.get("current_session_sink_alignment_summary", {}) or {}
    stage4_rationale_summary = stage4_summary.get("rationale_contract_summary", {}) or {}
    stage4_companion_summary = stage4_summary.get("companion_audit_summary", {}) or {}

    errors: list[str] = []
    warnings: list[str] = []
    if not stage3_session_id:
        errors.append("stage3_session_missing")
    if not stage4_session_id:
        errors.append("stage4_session_missing")
    if stage3_session_id and stage4_session_id and not shared_session_id:
        errors.append("stage3_stage4_session_split")
    if not stage3_current_session_summary:
        errors.append("stage3_current_session_summary_missing")
    elif str(stage3_current_session_summary.get("status", "") or "missing") != "ok":
        errors.append(f"stage3_current_session_status:{stage3_current_session_summary.get('status')}")
    if not stage4_current_summary:
        errors.append("stage4_current_session_summary_missing")
    elif str(stage4_current_summary.get("status", "") or "missing") != "ok":
        errors.append(f"stage4_current_session_status:{stage4_current_summary.get('status')}")
    if str(stage4_rationale_summary.get("status", "") or "missing") != "ok":
        errors.append(f"stage4_rationale_status:{stage4_rationale_summary.get('status')}")
    if str(stage4_companion_summary.get("status", "") or "missing") != "ok":
        errors.append(f"stage4_companion_status:{stage4_companion_summary.get('status')}")

    status = "fail" if errors else ("warn" if warnings else "pass")
    return {
        "summary_role": "stage34_frontier_live_proof_scope",
        "status": status,
        "stage3_live_generation_path": "covered" if stage3_current_session_summary else "missing",
        "stage4_live_generation_path": "covered" if stage4_current_summary else "missing",
        "shared_session_id": shared_session_id,
        "covered_surfaces": [
            "stage3_live_generation_path",
            "stage4_live_generation_path",
            "stage4_rationale_contract",
            "stage4_companion_audit",
        ],
        "uncovered_surfaces": [
            "stage2_live_generation_path",
            "backend_wide_multi_stage_runtime",
        ],
        "errors": errors,
        "warnings": warnings,
    }


def _ensure_pass_rate_monitor(app: SovereignApp, project_root: Path) -> None:
    if getattr(app, "pass_rate_monitor", None):
        return
    app.pass_rate_monitor = PassRateMonitor(project_root)


def _boot_app(project_name: str, selected_genre: dict) -> SovereignApp:
    with (
        patch.object(SovereignApp, "_select_genre", return_value=selected_genre),
        patch.object(SovereignApp, "_select_project", return_value=project_name),
        patch.object(SovereignApp, "_run_main_process", lambda self: None),
    ):
        app = SovereignApp()
        app.boot()
        return app


@contextmanager
def _clamp_frontier_lag_to_target_ep(app: SovereignApp, *, target_ep: int):
    current_project = getattr(app, "current_project", None)
    db = getattr(current_project, "db", None)
    if current_project is None or db is None or not callable(getattr(db, "load_anchor", None)):
        yield
        return

    original_load_anchor = db.load_anchor
    all_arcs = original_load_anchor("arcs") or []
    active_arc_count = _resolve_active_arc_count_for_target_ep(all_arcs, target_ep=target_ep)
    trimmed_arcs = [copy.deepcopy(arc) for arc in all_arcs[:active_arc_count]]
    trimmed_master_bible = _slice_master_bible_plot_roadmap(
        getattr(current_project, "master_bible", None),
        active_arc_count=active_arc_count,
    )

    def _load_anchor(key: str, *args, **kwargs):
        if key == "arcs":
            return copy.deepcopy(trimmed_arcs)
        return original_load_anchor(key, *args, **kwargs)

    with patch.object(db, "load_anchor", side_effect=_load_anchor):
        if trimmed_master_bible is None:
            yield
            return

        original_master_bible = current_project.master_bible
        current_project.master_bible = trimmed_master_bible
        try:
            yield
        finally:
            current_project.master_bible = original_master_bible


def _resolve_active_arc_count_for_target_ep(arcs: list[dict], *, target_ep: int) -> int:
    normalized_target_ep = int(target_ep or 0)
    if normalized_target_ep <= 0:
        raise ValueError("target_ep must be a positive integer")
    if not arcs:
        raise ValueError("stage34 canary run requires at least one designed arc")

    for index, arc in enumerate(arcs, start=1):
        ep_end = int(arc.get("ep_end") or arc.get("episode_end") or 0)
        if ep_end == normalized_target_ep:
            return index

    designed_arc_ends = [int(arc.get("ep_end") or arc.get("episode_end") or 0) for arc in arcs]
    raise ValueError(
        "target_ep must match a designed arc frontier ep_end for stage34 canary run"
        f" (target_ep={normalized_target_ep}, designed_arc_ends={designed_arc_ends})"
    )


def _slice_master_bible_plot_roadmap(master_bible: object, *, active_arc_count: int) -> dict | None:
    if not isinstance(master_bible, dict):
        return None

    cloned = copy.deepcopy(master_bible)
    root = cloned.get("MasterBible")
    if isinstance(root, dict):
        plot = root.get("plot_roadmap")
        if isinstance(plot, list):
            root["plot_roadmap"] = plot[:active_arc_count]
        return cloned

    plot = cloned.get("plot_roadmap")
    if isinstance(plot, list):
        cloned["plot_roadmap"] = plot[:active_arc_count]
    return cloned


def _load_project_genre(project_root: Path) -> dict:
    db = DBManager(project_root / "project_data.db")
    try:
        genre = db.load_anchor("genre_info") or {}
    finally:
        db.close()
    if not isinstance(genre, dict):
        return {}
    genre_type = str(genre.get("type", "") or "").strip()
    if not genre_type:
        return {}
    genre_name = str(genre.get("name", "") or genre_type).strip()
    return {"type": genre_type, "name": genre_name}


def _auto_input(prompt: str = "") -> str:
    text = str(prompt or "").lower()
    if "y/n" in text:
        return "y"
    return ""


def _close_app_handles(app: SovereignApp) -> None:
    current_project = getattr(app, "current_project", None)
    if getattr(app, "memory", None):
        try:
            app.memory.close()
        except Exception:
            pass
        app.memory = None
    if current_project is not None and hasattr(current_project, "db"):
        try:
            current_project.db.conn.commit()
        except Exception:
            pass
        try:
            current_project.db.close()
        except Exception:
            pass


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
