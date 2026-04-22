"""Run Stage 4 directly on an existing project and auto-archive a benchmark snapshot."""

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
from scripts.benchmark_archive_runtime import safe_archive_benchmark_record  # noqa: E402
from scripts.canary_path_utils import project_name_from_path, resolve_workspace_project_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Direct supervised Stage 4 runner")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--project", required=True)
    parser.add_argument("--target-ep", type=int, required=True)
    parser.add_argument(
        "--skip-benchmark-archive",
        action="store_true",
        help="Run Stage 4 but leave benchmark archiving to an external supervisor.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command != "run":
        raise ValueError(f"unsupported command: {args.command}")

    payload = run_direct_stage4(
        args.project,
        target_ep=args.target_ep,
        archive_enabled=not args.skip_benchmark_archive,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def run_direct_stage4(project_name: str, *, target_ep: int, archive_enabled: bool = True) -> dict:
    if target_ep < 1:
        raise ValueError("target-ep must be >= 1")

    project_root = resolve_workspace_project_dir(PROJECT_ROOT, project_name, prefer_canary=False, require_exists=True)
    runtime_project_name = project_name_from_path(PROJECT_ROOT, project_root)
    selected_genre = _load_project_genre(project_root)
    if not selected_genre:
        raise RuntimeError(f"genre_info anchor missing or invalid for {runtime_project_name}")

    before_latest_ep = _load_latest_written_ep(project_root)
    app = _boot_app(runtime_project_name, selected_genre)
    try:
        _ensure_pass_rate_monitor(app, project_root)
        app._get_int_input = lambda *args, **kwargs: kwargs.get("default", 1)
        app.ui.log(f"      🧭 [DirectS4] supervised Stage 4 run start (target_ep={target_ep})")
        with patch("builtins.input", side_effect=_auto_input):
            app._stage_4_v2_chief_writer(limit_mode=False, target_ep=target_ep, skip_pause=True)
        if getattr(app, "pass_rate_monitor", None):
            app.pass_rate_monitor.save()
        if hasattr(app, "_flush_audit_buffer"):
            app._flush_audit_buffer()
    finally:
        _close_app_handles(app)

    after_latest_ep = _load_latest_written_ep(project_root)
    runtime_audit_tag = _load_runtime_audit_tag(project_root)
    success = after_latest_ep >= target_ep or runtime_audit_tag == "stage4_complete"
    archive_status = "completed" if success else "partial"
    archive_notes = (
        f"direct supervised stage4; target_ep={target_ep}; before_latest_ep={before_latest_ep}; "
        f"after_latest_ep={after_latest_ep}; runtime_audit_tag={runtime_audit_tag or 'missing'}"
    )
    payload = {
        "project": runtime_project_name,
        "project_root": str(project_root),
        "target_ep": target_ep,
        "latest_written_ep_before": before_latest_ep,
        "latest_written_ep_after": after_latest_ep,
        "runtime_audit_tag": runtime_audit_tag,
        "success": success,
    }
    summary_path = project_root / "logs" / "stage4_direct_supervised_result.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if archive_enabled:
        payload["benchmark_archive"] = safe_archive_benchmark_record(
            workspace_root=PROJECT_ROOT,
            project=runtime_project_name,
            lane="stage4-supervised",
            target_ep=target_ep,
            status=archive_status,
            notes=archive_notes,
        )
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


def _load_latest_written_ep(project_root: Path) -> int:
    db = DBManager(project_root / "project_data.db")
    try:
        return int(db.get_latest_episode_number() or 0)
    finally:
        db.close()


def _load_runtime_audit_tag(project_root: Path) -> str:
    summary_path = project_root / "logs" / "runtime_audit_summary.json"
    if not summary_path.exists():
        return ""
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("tag", "") or "")


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
