"""Prepare, run, and analyze a repeatable Stage 4 canary project."""

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
    build_stage4_canary_summary,
    prepare_stage4_canary_project,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 4 canary helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="copy a baseline project and reset Stage 4 outputs")
    prepare.add_argument("--source-project", required=True)
    prepare.add_argument("--target-project", required=True)
    prepare.add_argument("--from-ep", type=int, default=1, help="currently only from-ep=1 is supported")
    prepare.add_argument("--force", action="store_true")

    run = subparsers.add_parser("run", help="run Stage 4 on a prepared project")
    run.add_argument("--project", required=True)
    run.add_argument("--target-ep", type=int, default=4)

    analyze = subparsers.add_parser("analyze", help="analyze an existing canary project")
    analyze.add_argument("--project", required=True)
    analyze.add_argument("--target-ep", type=int, default=4)

    full = subparsers.add_parser("full", help="prepare, run, and analyze in one command")
    full.add_argument("--source-project", required=True)
    full.add_argument("--target-project", required=True)
    full.add_argument("--from-ep", type=int, default=1, help="currently only from-ep=1 is supported")
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
    source_root = PROJECT_ROOT / "projects" / source_project
    target_root = PROJECT_ROOT / "projects" / target_project
    return prepare_stage4_canary_project(source_root, target_root, from_ep=from_ep, force=force)


def run_canary(project_name: str, *, target_ep: int) -> dict:
    project_root = PROJECT_ROOT / "projects" / project_name
    selected_genre = _load_project_genre(project_root)
    if not selected_genre:
        raise RuntimeError(f"genre_info anchor missing or invalid for {project_name}")

    app = _boot_app(project_name, selected_genre)
    try:
        _ensure_pass_rate_monitor(app, project_root)
        app._get_int_input = lambda *args, **kwargs: kwargs.get("default", 1)
        with patch("builtins.input", side_effect=_auto_input):
            app._stage_4_v2_chief_writer(limit_mode=False, target_ep=int(target_ep))
        if getattr(app, "pass_rate_monitor", None):
            app.pass_rate_monitor.save()
        if hasattr(app, "_flush_audit_buffer"):
            app._flush_audit_buffer()
    finally:
        _close_app_handles(app)

    summary = analyze_canary(project_name, target_ep=target_ep)
    return summary


def _ensure_pass_rate_monitor(app: SovereignApp, project_root: Path) -> None:
    if getattr(app, "pass_rate_monitor", None):
        return
    app.pass_rate_monitor = PassRateMonitor(project_root)


def analyze_canary(project_name: str, *, target_ep: int) -> dict:
    project_root = PROJECT_ROOT / "projects" / project_name
    summary = build_stage4_canary_summary(project_root, target_ep=target_ep)
    summary_path = project_root / "logs" / "canary_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


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


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
