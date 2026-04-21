"""Run Stage 3 directly on an existing project with a supervised retry cap.

This launcher boots the live app surface, reuses an existing project as-is,
and invokes Stage 3 batch blueprinting directly. It never enters Stage 4.
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
from modules.core.stage3_context import Stage3Context  # noqa: E402
from modules.domain.agents.three_phase_blueprint_runtime import ThreePhaseBlueprintRuntime  # noqa: E402
from scripts.canary_path_utils import project_name_from_path, resolve_workspace_project_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Direct supervised Stage 3 runner")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--project", required=True)
    parser.add_argument("--target-ep", type=int, required=True)
    parser.add_argument(
        "--operational-attempt-cap",
        type=int,
        default=5,
        help="Maximum total Stage 3 tries per episode. 5 means max_retries=4.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command != "run":
        raise ValueError(f"unsupported command: {args.command}")

    payload = run_direct_stage3(
        args.project,
        target_ep=args.target_ep,
        operational_attempt_cap=args.operational_attempt_cap,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def run_direct_stage3(project_name: str, *, target_ep: int, operational_attempt_cap: int) -> dict:
    if operational_attempt_cap < 1:
        raise ValueError("operational-attempt-cap must be >= 1")

    project_root = resolve_workspace_project_dir(PROJECT_ROOT, project_name, prefer_canary=False, require_exists=True)
    runtime_project_name = project_name_from_path(PROJECT_ROOT, project_root)
    selected_genre = _load_project_genre(project_root)
    if not selected_genre:
        raise RuntimeError(f"genre_info anchor missing or invalid for {runtime_project_name}")

    app = _boot_app(runtime_project_name, selected_genre)
    try:
        _ensure_pass_rate_monitor(app, project_root)
        app._get_int_input = lambda *args, **kwargs: kwargs.get("default", 1)
        with patch("builtins.input", side_effect=_auto_input):
            result = _run_stage3_only(
                app,
                target_ep=target_ep,
                operational_attempt_cap=operational_attempt_cap,
            )
        if getattr(app, "pass_rate_monitor", None):
            app.pass_rate_monitor.save()
        if hasattr(app, "_flush_audit_buffer"):
            app._flush_audit_buffer()
    finally:
        _close_app_handles(app)

    payload = {
        "project": runtime_project_name,
        "project_root": str(project_root),
        "target_ep": target_ep,
        "operational_attempt_cap": operational_attempt_cap,
        "result": result,
    }
    summary_path = project_root / "logs" / "stage3_direct_supervised_result.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _run_stage3_only(app: SovereignApp, *, target_ep: int, operational_attempt_cap: int) -> dict:
    max_retries = max(0, operational_attempt_cap - 1)
    original_generate = ThreePhaseBlueprintRuntime.generate

    def _generate_with_cap(self, *args, **kwargs):
        if len(args) >= 5:
            args = list(args)
            args[4] = min(int(args[4]), max_retries)
            args = tuple(args)
        else:
            incoming = kwargs.get("max_retries", max_retries)
            kwargs["max_retries"] = min(int(incoming), max_retries)
        return original_generate(self, *args, **kwargs)

    app.ui.log(
        f"      🧭 [DirectS3] supervised Stage 3 run start (target_ep={target_ep}, attempt_cap={operational_attempt_cap})"
    )
    app._stage3_orch.ctx = Stage3Context.from_app(app)
    with patch.object(ThreePhaseBlueprintRuntime, "generate", _generate_with_cap):
        return app._stage3_orch.stage_3_batch_blueprinting(target_ep=target_ep)


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


if __name__ == "__main__":
    raise SystemExit(main())
