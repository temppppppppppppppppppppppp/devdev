"""Run Stage 2 directly on an existing project with a bounded target arc total.

This launcher boots the live app surface, reuses an existing project as-is,
and invokes Stage 2 arc design directly. It never enters Stage 3 or Stage 4.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main_a import SovereignApp  # noqa: E402
from modules.core.db_manager import DBManager  # noqa: E402
from modules.core.pass_rate_monitor import PassRateMonitor  # noqa: E402
from modules.core.stage2_context import Stage2Context  # noqa: E402
from scripts.canary_path_utils import project_name_from_path, resolve_workspace_project_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Direct supervised Stage 2 runner")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--project", required=True)
    parser.add_argument(
        "--target-total-arcs",
        type=int,
        required=True,
        help="Absolute target arc count. If the project already has this many arcs, no-op.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command != "run":
        raise ValueError(f"unsupported command: {args.command}")

    payload = run_direct_stage2(
        args.project,
        target_total_arcs=args.target_total_arcs,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def run_direct_stage2(project_name: str, *, target_total_arcs: int) -> dict:
    if target_total_arcs < 1:
        raise ValueError("target-total-arcs must be >= 1")

    project_root = resolve_workspace_project_dir(PROJECT_ROOT, project_name, prefer_canary=False, require_exists=True)
    runtime_project_name = project_name_from_path(PROJECT_ROOT, project_root)
    selected_genre = _load_project_genre(project_root)
    if not selected_genre:
        raise RuntimeError(f"genre_info anchor missing or invalid for {runtime_project_name}")

    before_arcs = _load_arc_count(project_root)
    requested_delta = max(0, target_total_arcs - before_arcs)

    app = _boot_app(runtime_project_name, selected_genre)
    env_backup = {
        "GEULDOBI_STAGE2_HEADLESS": os.environ.get("GEULDOBI_STAGE2_HEADLESS"),
        "GEULDOBI_STAGE2_FAILURE_POLICY": os.environ.get("GEULDOBI_STAGE2_FAILURE_POLICY"),
    }
    try:
        _ensure_pass_rate_monitor(app, project_root)
        app._stage2_orch.ctx = Stage2Context.from_app(app)
        app._get_int_input = lambda *args, **kwargs: kwargs.get("default", 1)
        os.environ["GEULDOBI_STAGE2_HEADLESS"] = "1"
        os.environ["GEULDOBI_STAGE2_FAILURE_POLICY"] = "abort"
        with patch("builtins.input", side_effect=_auto_input):
            if requested_delta > 0:
                app.ui.log(
                    "      🧭 [DirectS2] supervised Stage 2 run start "
                    f"(target_total_arcs={target_total_arcs}, current_arcs={before_arcs}, delta={requested_delta})"
                )
                app._run_stage2_arc_async(target_arc_count=requested_delta)
            else:
                app.ui.log(
                    "      ✅ [DirectS2] no-op "
                    f"(current_arcs={before_arcs} already >= target_total_arcs={target_total_arcs})"
                )
        if getattr(app, "pass_rate_monitor", None):
            app.pass_rate_monitor.save()
        if hasattr(app, "_flush_audit_buffer"):
            app._flush_audit_buffer()
    finally:
        _restore_env(env_backup)
        _close_app_handles(app)

    after_arcs = _load_arc_count(project_root)
    payload = {
        "project": runtime_project_name,
        "project_root": str(project_root),
        "target_total_arcs": target_total_arcs,
        "current_arcs_before": before_arcs,
        "current_arcs_after": after_arcs,
        "requested_delta": requested_delta,
        "realized_delta": max(0, after_arcs - before_arcs),
        "success": after_arcs >= target_total_arcs,
    }
    summary_path = project_root / "logs" / "stage2_direct_supervised_result.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


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


def _load_arc_count(project_root: Path) -> int:
    db = DBManager(project_root / "project_data.db")
    try:
        arcs = db.load_anchor("arcs") or []
    finally:
        db.close()
    return len(arcs) if isinstance(arcs, list) else 0


def _restore_env(snapshot: dict[str, str | None]) -> None:
    for key, value in snapshot.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


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
