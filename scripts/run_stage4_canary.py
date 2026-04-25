"""Prepare, run, and analyze a repeatable Stage 4 canary project.

Validation tier: full_canary_proof
Mutation boundary: boots live app surfaces, patches input, and writes proof artifacts.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main_a import SovereignApp  # noqa: E402
from modules.core.db_manager import DBManager  # noqa: E402
from modules.core.llm_router import get_shared_llm_router  # noqa: E402
from modules.core.pass_rate_monitor import PassRateMonitor  # noqa: E402
from modules.core.provider_mode import (  # noqa: E402
    AMBIENT_MODE,
    GEMINI_DIRECT_MODE,
    PROVIDER_MODE_ENV,
    VERTEX_AI_MODE,
    normalize_provider_mode,
)
from modules.core.stage4_canary_tools import (  # noqa: E402
    build_stage4_branch_inventory,
    build_stage4_canary_summary,
    prepare_stage4_canary_project,
)
from scripts.benchmark_archive_runtime import safe_archive_benchmark_record  # noqa: E402
from scripts.canary_path_utils import (  # noqa: E402
    project_name_from_path,
    resolve_workspace_project_dir,
    scoped_canary_projects_root,
)
from scripts.canary_semantic_exit import semantic_exit_code  # noqa: E402
from scripts.regression_validation_tiers import FULL_CANARY_PROOF  # noqa: E402

VALIDATION_TIER = FULL_CANARY_PROOF
MUTATES_PROJECT_STATE = True
DEFAULT_PROVIDER_MODE = GEMINI_DIRECT_MODE
AMBIENT_PROVIDER_MODE = AMBIENT_MODE
VERTEX_PROVIDER_MODE = VERTEX_AI_MODE
NON_GEMINI_PROVIDER_ENV_KEYS = (
    "ANTHROPIC_API_KEY",
    "CLAUDE_API",
    "VERTEX_API_KEY",
    "VERTEX_PROJECT_ID",
    "VERTEX_LOCATION",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_LOCATION",
    "OPENAI_API_KEY",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 4 canary helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="copy a baseline project and reset Stage 4 outputs")
    prepare.add_argument("--source-project", required=True)
    prepare.add_argument("--target-project", required=True)
    prepare.add_argument("--from-ep", type=int, default=1, help="reset Stage 4 outputs from this episode onward")
    prepare.add_argument("--force", action="store_true")

    run = subparsers.add_parser("run", help="run Stage 4 on a prepared project")
    run.add_argument("--project", required=True)
    run.add_argument("--target-ep", type=int, default=4)
    run.add_argument("--provider-mode", choices=(DEFAULT_PROVIDER_MODE, AMBIENT_PROVIDER_MODE, VERTEX_PROVIDER_MODE))

    analyze = subparsers.add_parser("analyze", help="analyze an existing canary project")
    analyze.add_argument("--project", required=True)
    analyze.add_argument("--target-ep", type=int, default=4)

    branch_inventory = subparsers.add_parser(
        "branch-inventory", help="aggregate multiple canary summaries into branch-proof coverage"
    )
    branch_inventory.add_argument("--project", action="append", required=True)
    branch_inventory.add_argument("--output", required=True)

    full = subparsers.add_parser("full", help="prepare, run, and analyze in one command")
    full.add_argument("--source-project", required=True)
    full.add_argument("--target-project", required=True)
    full.add_argument("--from-ep", type=int, default=1, help="reset Stage 4 outputs from this episode onward")
    full.add_argument("--target-ep", type=int, default=4)
    full.add_argument("--force", action="store_true")
    full.add_argument("--provider-mode", choices=(DEFAULT_PROVIDER_MODE, AMBIENT_PROVIDER_MODE, VERTEX_PROVIDER_MODE))

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "prepare":
        payload = prepare_canary(args.source_project, args.target_project, from_ep=args.from_ep, force=args.force)
        _print_json(payload)
        return 0

    if args.command == "run":
        payload = run_canary(args.project, target_ep=args.target_ep, provider_mode=args.provider_mode)
        _print_json(payload)
        return semantic_exit_code(payload)

    if args.command == "analyze":
        payload = analyze_canary(args.project, target_ep=args.target_ep)
        _print_json(payload)
        return 0

    if args.command == "branch-inventory":
        payload = branch_inventory(args.project, output_path=args.output)
        _print_json(payload)
        return 0

    payload = prepare_canary(args.source_project, args.target_project, from_ep=args.from_ep, force=args.force)
    _print_json(payload)
    payload = run_canary(args.target_project, target_ep=args.target_ep, provider_mode=args.provider_mode)
    _print_json(payload)
    return semantic_exit_code(payload)


def prepare_canary(source_project: str, target_project: str, *, from_ep: int, force: bool) -> dict:
    source_root = resolve_workspace_project_dir(PROJECT_ROOT, source_project, prefer_canary=False, require_exists=True)
    target_root = resolve_workspace_project_dir(PROJECT_ROOT, target_project, prefer_canary=True, require_exists=False)
    return prepare_stage4_canary_project(source_root, target_root, from_ep=from_ep, force=force)


def _normalize_provider_mode(provider_mode: str | None) -> str:
    requested = normalize_provider_mode(provider_mode, default="")
    if requested:
        return requested
    inherited = normalize_provider_mode(os.getenv(PROVIDER_MODE_ENV), default="")
    if inherited:
        return inherited
    return AMBIENT_PROVIDER_MODE


@contextmanager
def _provider_mode_env(provider_mode: str | None):
    normalized_mode = _normalize_provider_mode(provider_mode)
    backups = {key: os.environ.get(key) for key in NON_GEMINI_PROVIDER_ENV_KEYS}
    previous_provider_mode = os.environ.get(PROVIDER_MODE_ENV)
    os.environ[PROVIDER_MODE_ENV] = normalized_mode
    try:
        if normalized_mode == DEFAULT_PROVIDER_MODE:
            for key in NON_GEMINI_PROVIDER_ENV_KEYS:
                os.environ.pop(key, None)
        get_shared_llm_router(force_reload=True)
        yield normalized_mode
    finally:
        for key in NON_GEMINI_PROVIDER_ENV_KEYS:
            previous = backups[key]
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous
        if previous_provider_mode is None:
            os.environ.pop(PROVIDER_MODE_ENV, None)
        else:
            os.environ[PROVIDER_MODE_ENV] = previous_provider_mode
        get_shared_llm_router(force_reload=True)


def run_canary(project_name: str, *, target_ep: int, provider_mode: str | None = None) -> dict:
    project_root = resolve_workspace_project_dir(PROJECT_ROOT, project_name, prefer_canary=True, require_exists=True)
    runtime_project_name = project_name_from_path(PROJECT_ROOT, project_root)
    selected_genre = _load_project_genre(project_root)
    if not selected_genre:
        raise RuntimeError(f"genre_info anchor missing or invalid for {runtime_project_name}")

    with scoped_canary_projects_root(PROJECT_ROOT, project_path=project_root), _provider_mode_env(provider_mode):
        app = _boot_app(runtime_project_name, selected_genre)
        try:
            _ensure_pass_rate_monitor(app, project_root)
            app._get_int_input = lambda *args, **kwargs: kwargs.get("default", 1)
            with patch("builtins.input", side_effect=_auto_input):
                app._stage_4_v2_chief_writer(limit_mode=False, target_ep=int(target_ep))
        finally:
            monitor = getattr(app, "pass_rate_monitor", None)
            if monitor is not None:
                try:
                    monitor.save()
                except Exception as exc:
                    logging.warning("[run_stage4_canary] pass_rate_monitor save failed: %s", exc)
            if hasattr(app, "_flush_audit_buffer"):
                try:
                    app._flush_audit_buffer()
                except Exception as exc:
                    logging.warning("[run_stage4_canary] audit buffer flush failed: %s", exc)
            _close_app_handles(app)

    summary = analyze_canary(runtime_project_name, target_ep=target_ep)
    summary["benchmark_archive"] = safe_archive_benchmark_record(
        workspace_root=PROJECT_ROOT,
        project=runtime_project_name,
        lane="stage4-canary",
        target_ep=target_ep,
        status="completed" if summary.get("hard_gates", {}).get("status") == "pass" else "partial",
        notes=f"stage4 canary run; provider_mode={_normalize_provider_mode(provider_mode)}; target_ep={target_ep}",
    )
    return summary


def _ensure_pass_rate_monitor(app: SovereignApp, project_root: Path) -> None:
    expected_log_path = (project_root / "logs" / "pass_rate_monitor.json").resolve()
    monitor = getattr(app, "pass_rate_monitor", None)
    if monitor is not None:
        monitor_log_path = getattr(monitor, "log_path", None)
        if monitor_log_path is None:
            return
        if not isinstance(monitor_log_path, str | Path):
            return
        try:
            if Path(monitor_log_path).resolve() == expected_log_path:
                return
        except (OSError, RuntimeError, TypeError, ValueError):
            return
    app.pass_rate_monitor = PassRateMonitor(project_root)


def analyze_canary(project_name: str, *, target_ep: int) -> dict:
    project_root = resolve_workspace_project_dir(PROJECT_ROOT, project_name, prefer_canary=True, require_exists=True)
    summary = build_stage4_canary_summary(project_root, target_ep=target_ep)
    summary_path = project_root / "logs" / "canary_summary.json"
    companion_audit_path = project_root / "logs" / "canary_companion_audit.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    companion_audit_path.write_text(
        json.dumps(
            {
                "project_locator": summary.get("project_locator", ""),
                "proof_record_summary": summary.get("proof_record_summary", {}),
                "companion_audit_summary": summary.get("companion_audit_summary", {}),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return summary


def branch_inventory(project_names: list[str], *, output_path: str) -> dict:
    project_roots = [
        resolve_workspace_project_dir(PROJECT_ROOT, project_name, prefer_canary=True, require_exists=True)
        for project_name in project_names
    ]
    payload = build_stage4_branch_inventory(project_roots)
    out_path = PROJECT_ROOT / output_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


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
