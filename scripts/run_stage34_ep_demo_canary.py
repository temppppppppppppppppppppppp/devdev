"""Prepare, run, and analyze a repeatable single-episode Stage 3->4 demo canary.

Validation tier: full_canary_proof
Mutation boundary: boots live app surfaces, preserves prior authority, and
regenerates only one episode's blueprint/manuscript.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main_a import SovereignApp  # noqa: E402
from modules.core.db_manager import DBManager  # noqa: E402
from modules.core.pass_rate_monitor import PassRateMonitor  # noqa: E402
from modules.core.stage4_canary_tools import (  # noqa: E402
    build_stage3_canary_summary,
    build_stage4_canary_summary,
    prepare_stage34_canary_project,
)
from scripts.regression_validation_tiers import FULL_CANARY_PROOF  # noqa: E402

VALIDATION_TIER = FULL_CANARY_PROOF
MUTATES_PROJECT_STATE = True

PREP_LOG_NAME = "stage34_ep_demo_canary_prep.json"
SUMMARY_LOG_NAME = "stage34_ep_demo_canary_summary.json"
SUMMARY_ROLE = "stage34_single_episode_demo_canary"
MODE_NAME = "stage34_single_episode_demo"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single-episode Stage 3->4 demo canary helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="copy a baseline project and reset Stage 3/4 outputs from one ep")
    prepare.add_argument("--source-project", required=True)
    prepare.add_argument("--target-project", required=True)
    prepare.add_argument("--from-ep", type=int, default=2)
    prepare.add_argument("--force", action="store_true")

    run = subparsers.add_parser("run", help="run Stage 3 and Stage 4 for exactly one prepared episode")
    run.add_argument("--project", required=True)
    run.add_argument("--target-ep", type=int, default=2)

    analyze = subparsers.add_parser("analyze", help="analyze an existing single-episode Stage 3->4 demo canary")
    analyze.add_argument("--project", required=True)
    analyze.add_argument("--target-ep", type=int, default=2)

    full = subparsers.add_parser("full", help="prepare, run, and analyze in one command")
    full.add_argument("--source-project", required=True)
    full.add_argument("--target-project", required=True)
    full.add_argument("--from-ep", type=int, default=2)
    full.add_argument("--target-ep", type=int, default=2)
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
    source_root = PROJECT_ROOT / "projects" / source_project
    target_root = PROJECT_ROOT / "projects" / target_project
    base_payload = prepare_stage34_canary_project(source_root, target_root, from_ep=from_ep, force=force)
    stale_blueprint_txt_removed = _clear_demo_blueprint_text_files(target_root, from_ep=from_ep)
    cleanup = dict(base_payload.get("cleanup", {}) or {})
    file_cleanup = dict(cleanup.get("file_cleanup", {}) or {})
    file_cleanup["demo_blueprint_txt_removed"] = stale_blueprint_txt_removed
    cleanup["file_cleanup"] = file_cleanup
    payload = {
        "prepared_at": base_payload.get("prepared_at"),
        "mode": MODE_NAME,
        "source_project": source_project,
        "target_project": target_project,
        "from_ep": int(from_ep),
        "frozen_authority_ep": max(0, int(from_ep) - 1),
        "regen_blueprint_ep": int(from_ep),
        "regen_draft_ep": int(from_ep),
        "cleanup": cleanup,
        "base_stage34_prep_log": "logs/stage34_canary_prep.json",
    }
    _write_json(target_root / "logs" / PREP_LOG_NAME, payload)
    return payload


def run_canary(project_name: str, *, target_ep: int) -> dict:
    project_root = PROJECT_ROOT / "projects" / project_name
    prep_payload = _load_demo_prep(project_root)
    _assert_demo_target_matches_prep(prep_payload, target_ep=target_ep)
    selected_genre = _load_project_genre(project_root)
    if not selected_genre:
        raise RuntimeError(f"genre_info anchor missing or invalid for {project_name}")

    app = _boot_app(project_name, selected_genre)
    try:
        _ensure_pass_rate_monitor(app, project_root)
        app._get_int_input = lambda *args, **kwargs: kwargs.get("default", 1)
        with patch("builtins.input", side_effect=_auto_input):
            _run_stage34_ep_demo(app, target_ep=target_ep)
        if getattr(app, "pass_rate_monitor", None):
            app.pass_rate_monitor.save()
        if hasattr(app, "_flush_audit_buffer"):
            app._flush_audit_buffer()
    finally:
        _close_app_handles(app)

    return analyze_canary(project_name, target_ep=target_ep)


def analyze_canary(project_name: str, *, target_ep: int) -> dict:
    project_root = PROJECT_ROOT / "projects" / project_name
    prep_payload = _load_demo_prep(project_root)
    _assert_demo_target_matches_prep(prep_payload, target_ep=target_ep)

    stage3_summary = build_stage3_canary_summary(project_root, target_ep=target_ep)
    stage4_summary = build_stage4_canary_summary(project_root, target_ep=target_ep)
    boundary_summary = _build_demo_boundary_summary(project_root, target_ep=target_ep, prep_payload=prep_payload)

    stage3_session_id = str(stage3_summary.get("latest_session_id", "") or "")
    stage4_session_id = str(stage4_summary.get("latest_session_id", "") or "")
    shared_session_id = stage4_session_id if stage4_session_id and stage4_session_id == stage3_session_id else ""
    multi_stage_summary = _build_multi_stage_summary(
        stage3_current_session_summary=stage3_summary.get("sink_alignment_summary", {}) or {},
        stage4_summary=stage4_summary,
        boundary_summary=boundary_summary,
        shared_session_id=shared_session_id,
        stage3_session_id=stage3_session_id,
        stage4_session_id=stage4_session_id,
    )

    payload = {
        "summary_role": SUMMARY_ROLE,
        "mode": MODE_NAME,
        "project": project_name,
        "project_locator": stage4_summary.get("project_locator", ""),
        "project_root": stage4_summary.get("project_root", ""),
        "target_ep": int(target_ep),
        "frozen_authority_ep": int(prep_payload.get("frozen_authority_ep") or max(0, int(target_ep) - 1)),
        "regen_blueprint_ep": int(prep_payload.get("regen_blueprint_ep") or int(target_ep)),
        "regen_draft_ep": int(prep_payload.get("regen_draft_ep") or int(target_ep)),
        "stage3_latest_session_id": stage3_session_id,
        "stage4_latest_session_id": stage4_session_id,
        "shared_session_id": shared_session_id,
        "stage3_current_session_sink_alignment_summary": stage3_summary.get("sink_alignment_summary", {}) or {},
        "stage3_canary_summary": stage3_summary,
        "stage4_canary_summary": stage4_summary,
        "demo_boundary_summary": boundary_summary,
        "multi_stage_proof_scope_summary": multi_stage_summary,
    }

    summary_path = project_root / "logs" / SUMMARY_LOG_NAME
    _write_json(summary_path, payload)
    return payload


def _run_stage34_ep_demo(app: SovereignApp, *, target_ep: int) -> dict:
    from modules.core.stage3_context import Stage3Context

    app._stage3_orch.ctx = Stage3Context.from_app(app)
    stage3_result = app._stage3_orch.stage_3_batch_blueprinting(target_ep=target_ep)
    stage4_result = app._stage_4_v2_chief_writer(limit_mode=False, target_ep=int(target_ep), skip_pause=True)
    return {
        "stage3": stage3_result,
        "stage4": stage4_result,
    }


def _build_demo_boundary_summary(project_root: Path, *, target_ep: int, prep_payload: dict) -> dict:
    db = DBManager(project_root / "project_data.db")
    try:
        stage3_eps = _load_ep_list(db, "SELECT DISTINCT ep_num FROM stage_attempts WHERE stage = 3 ORDER BY ep_num ASC")
        stage4_eps = _load_ep_list(db, "SELECT DISTINCT ep_num FROM stage_attempts WHERE stage = 4 ORDER BY ep_num ASC")
        blueprint_eps = _load_ep_list(db, "SELECT DISTINCT ep_num FROM blueprints ORDER BY ep_num ASC")
        manuscript_eps = _load_ep_list(db, "SELECT DISTINCT ep_num FROM manuscripts ORDER BY ep_num ASC")
    finally:
        db.close()

    draft_eps = sorted(_collect_file_eps(project_root / "drafts", "ep_*.txt"))
    blueprint_file_eps = sorted(
        _collect_file_eps(project_root / "plans" / "blueprints", "blueprint_*.txt")
        | _collect_file_eps(project_root / "plans" / "blueprints", "ep_*.json")
    )
    target_ep = int(target_ep)
    beyond_target = {
        "stage3_attempt_eps": [ep for ep in stage3_eps if ep > target_ep],
        "stage4_attempt_eps": [ep for ep in stage4_eps if ep > target_ep],
        "blueprint_db_eps": [ep for ep in blueprint_eps if ep > target_ep],
        "manuscript_db_eps": [ep for ep in manuscript_eps if ep > target_ep],
        "draft_file_eps": [ep for ep in draft_eps if ep > target_ep],
        "blueprint_file_eps": [ep for ep in blueprint_file_eps if ep > target_ep],
    }
    errors = [
        f"{surface}_beyond_target:{eps}"
        for surface, eps in beyond_target.items()
        if eps
    ]
    frozen_authority_ep = int(prep_payload.get("frozen_authority_ep") or max(0, target_ep - 1))
    frozen_authority_draft_exists = (
        True if frozen_authority_ep <= 0 else (project_root / "drafts" / f"ep_{frozen_authority_ep:04d}.txt").exists()
    )
    anchor_validation = prep_payload.get("cleanup", {}).get("anchor_validation", {}) or {}
    if not frozen_authority_draft_exists:
        errors.append(f"frozen_authority_draft_missing:ep{frozen_authority_ep}")
    if str(anchor_validation.get("status", "") or "missing") != "ok":
        errors.append(f"prep_anchor_validation_status:{anchor_validation.get('status', 'missing')}")

    return {
        "summary_role": "stage34_single_episode_demo_boundary",
        "status": "fail" if errors else "pass",
        "target_ep": target_ep,
        "frozen_authority_ep": frozen_authority_ep,
        "frozen_authority_draft_exists": frozen_authority_draft_exists,
        "prep_anchor_validation_status": str(anchor_validation.get("status", "") or "missing"),
        "stage3_attempt_eps": stage3_eps,
        "stage4_attempt_eps": stage4_eps,
        "blueprint_db_eps": blueprint_eps,
        "manuscript_db_eps": manuscript_eps,
        "draft_file_eps": draft_eps,
        "blueprint_file_eps": blueprint_file_eps,
        "beyond_target": beyond_target,
        "errors": errors,
    }


def _build_multi_stage_summary(
    *,
    stage3_current_session_summary: dict,
    stage4_summary: dict,
    boundary_summary: dict,
    shared_session_id: str,
    stage3_session_id: str,
    stage4_session_id: str,
) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    stage4_current_summary = stage4_summary.get("current_session_sink_alignment_summary", {}) or {}
    stage4_rationale_summary = stage4_summary.get("rationale_contract_summary", {}) or {}
    stage4_companion_summary = stage4_summary.get("companion_audit_summary", {}) or {}

    if not stage3_session_id:
        errors.append("stage3_session_missing")
    if not stage4_session_id:
        errors.append("stage4_session_missing")
    if stage3_session_id and stage4_session_id and not shared_session_id:
        errors.append("stage3_stage4_session_split")
    if str((stage3_current_session_summary or {}).get("status", "") or "missing") != "ok":
        errors.append(f"stage3_current_session_status:{(stage3_current_session_summary or {}).get('status', 'missing')}")
    if str(stage4_current_summary.get("status", "") or "missing") != "ok":
        errors.append(f"stage4_current_session_status:{stage4_current_summary.get('status', 'missing')}")
    if str(stage4_rationale_summary.get("status", "") or "missing") != "ok":
        errors.append(f"stage4_rationale_status:{stage4_rationale_summary.get('status', 'missing')}")
    if str(stage4_companion_summary.get("status", "") or "missing") != "ok":
        errors.append(f"stage4_companion_status:{stage4_companion_summary.get('status', 'missing')}")
    if str(boundary_summary.get("status", "") or "missing") != "pass":
        errors.append(f"demo_boundary_status:{boundary_summary.get('status', 'missing')}")

    status = "fail" if errors else ("warn" if warnings else "pass")
    return {
        "summary_role": "stage34_single_episode_demo_proof_scope",
        "status": status,
        "shared_session_id": shared_session_id,
        "covered_surfaces": [
            "ep1_frozen_authority",
            "ep2_stage3_live_generation_path",
            "ep2_stage4_live_generation_path",
            "stage4_rationale_contract",
            "stage4_companion_audit",
        ],
        "uncovered_surfaces": [
            "ep3_plus_generation",
            "arc_frontier_lag_behavior",
            "broad_stage4_closure",
        ],
        "errors": errors,
        "warnings": warnings,
    }


def _load_ep_list(db: DBManager, query: str) -> list[int]:
    rows = db.conn.execute(query).fetchall()
    return sorted({int(row["ep_num"] or 0) for row in rows if int(row["ep_num"] or 0) > 0})


def _collect_file_eps(root: Path, pattern: str) -> set[int]:
    eps: set[int] = set()
    if not root.exists():
        return eps
    for path in root.glob(pattern):
        ep_num = _extract_ep_num(path.name)
        if ep_num is not None:
            eps.add(ep_num)
    return eps


def _clear_demo_blueprint_text_files(project_root: Path, *, from_ep: int) -> int:
    blueprints_dir = project_root / "plans" / "blueprints"
    if not blueprints_dir.exists():
        return 0
    removed = 0
    for path in blueprints_dir.glob("blueprint_*.txt"):
        ep_num = _extract_ep_num(path.name)
        if ep_num is not None and ep_num >= int(from_ep):
            path.unlink(missing_ok=True)
            removed += 1
    return removed


def _extract_ep_num(name: str) -> int | None:
    digits = "".join(ch for ch in str(name) if ch.isdigit())
    if not digits:
        return None
    return int(digits)


def _load_demo_prep(project_root: Path) -> dict:
    prep_path = project_root / "logs" / PREP_LOG_NAME
    payload = _read_json(prep_path)
    if not payload:
        raise FileNotFoundError(f"demo prep metadata missing: {prep_path}")
    return payload


def _assert_demo_target_matches_prep(prep_payload: dict, *, target_ep: int) -> None:
    prepared_blueprint_ep = int(prep_payload.get("regen_blueprint_ep") or 0)
    prepared_draft_ep = int(prep_payload.get("regen_draft_ep") or 0)
    normalized_target_ep = int(target_ep or 0)
    if normalized_target_ep <= 0:
        raise ValueError("target_ep must be a positive integer")
    if prepared_blueprint_ep != normalized_target_ep or prepared_draft_ep != normalized_target_ep:
        raise ValueError(
            "single-episode demo canary requires target_ep to match prepared regen episode"
            f" (target_ep={normalized_target_ep}, regen_blueprint_ep={prepared_blueprint_ep},"
            f" regen_draft_ep={prepared_draft_ep})"
        )


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


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
