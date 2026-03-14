"""Automated Frontier Lag N-arc harness with terminal-owned watchdog."""

from __future__ import annotations

import argparse
import json
import re
import signal
import subprocess
import sys
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main_a import SovereignApp  # noqa: E402
from modules.core.db_manager import DBManager  # noqa: E402
from modules.core.failure_analyzer import FailureAnalyzer  # noqa: E402
from modules.core.pass_rate_monitor import PassRateMonitor  # noqa: E402
from modules.core.project_support import (  # noqa: E402
    EXTERNAL_POV_INSERT_POLICY_OPTIONS,
    INCARNATION_TYPE_OPTIONS,
    POV_OPTIONS,
    WORLD_ORIGIN_OPTIONS,
)

DEFAULT_SEED_PROFILE = "00_20260314"
DEFAULT_BATCH_SIZE = 1
DEFAULT_POLL_INTERVAL_SECONDS = 30 * 60
PROCESS_CHECK_INTERVAL_SECONDS = 5
MANUAL_PROFILE_DOC = "docs/2026-03-14/main-a-manual-stage0-selection-harness-00_20260314.md"
HARNESS_SSOT_DOC = "docs/2026-03-14/auto-frontier-lag-n-arc-test-harness-ssot.md"
PROMPT_WAIT_MARKERS = (
    "건너뛰고 다음 Arc로?",
    "계속하시겠습니까?",
    "[Enter] 메뉴로 돌아가기",
    "👉 Choice",
    "선택 (기본:",
)


@dataclass(slots=True)
class HarnessProfile:
    seed_profile: str
    genre_type: str
    genre_name: str
    bible_file: str
    roadmap_file: str
    treatment_auto_condense: str
    protagonist_config: dict[str, str]
    style_analysis_mode: str
    style_analysis_confirm: str


def default_profile(seed_profile: str = DEFAULT_SEED_PROFILE) -> HarnessProfile:
    return HarnessProfile(
        seed_profile=seed_profile,
        genre_type="investment",
        genre_name="투자 (Investment Fiction)",
        bible_file="01_bi_투자물_골든_카나리아 테스트.json",
        roadmap_file="01_tr_투자물_골든_카나리아 테스트.json",
        treatment_auto_condense="n",
        protagonist_config={
            "world_origin": "원시인",
            "incarnation_type": "회귀자",
            "pov": "혼합",
            "external_pov_insert_policy": "적극 허용",
        },
        style_analysis_mode="use",
        style_analysis_confirm="y",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto Frontier-Lag N-arc harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="render a resolved harness execution plan")
    plan.add_argument("--arc-count", type=int)
    plan.add_argument("--trigger", default="")
    plan.add_argument("--seed-profile", default=DEFAULT_SEED_PROFILE)
    plan.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    plan.add_argument("--target-project", default="")

    worker = subparsers.add_parser("worker", help="internal worker that boots app and runs the pipeline")
    worker.add_argument("--target-project", required=True)
    worker.add_argument("--arc-count", type=int, required=True)
    worker.add_argument("--seed-profile", default=DEFAULT_SEED_PROFILE)
    worker.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)

    run = subparsers.add_parser("run", help="spawn worker, watchdog it, analyze outputs, write SSOT")
    run.add_argument("--arc-count", type=int)
    run.add_argument("--trigger", default="")
    run.add_argument("--seed-profile", default=DEFAULT_SEED_PROFILE)
    run.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    run.add_argument("--poll-interval-seconds", type=int, default=DEFAULT_POLL_INTERVAL_SECONDS)
    run.add_argument("--target-project", default="")

    analyze = subparsers.add_parser("analyze", help="analyze an existing harness run and write SSOT")
    analyze.add_argument("--project", required=True)
    analyze.add_argument("--arc-count", type=int)

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "plan":
        payload = build_execution_plan(
            arc_count=resolve_arc_count(args.arc_count, args.trigger),
            seed_profile=args.seed_profile,
            batch_size=args.batch_size,
            target_project=args.target_project or "",
            trigger=args.trigger,
        )
        _print_json(payload)
        return 0

    if args.command == "worker":
        payload = run_worker(
            target_project=args.target_project,
            arc_count=int(args.arc_count),
            seed_profile=args.seed_profile,
            batch_size=int(args.batch_size),
        )
        _print_json(payload)
        return 0 if payload.get("status") == "success" else 1

    if args.command == "analyze":
        payload = analyze_project(args.project, arc_count=args.arc_count)
        _print_json(payload)
        return 0

    payload = run_harness(
        arc_count=resolve_arc_count(args.arc_count, args.trigger),
        seed_profile=args.seed_profile,
        batch_size=int(args.batch_size),
        poll_interval_seconds=max(1, int(args.poll_interval_seconds or DEFAULT_POLL_INTERVAL_SECONDS)),
        target_project=args.target_project or "",
        trigger=args.trigger,
    )
    _print_json(payload)
    return 0 if payload.get("analysis", {}).get("judgment") == "success" else 1


def resolve_arc_count(arc_count: int | None, trigger: str) -> int:
    if arc_count is not None:
        normalized = int(arc_count)
        if normalized <= 0:
            raise ValueError("arc_count must be a positive integer")
        return normalized

    parsed = parse_arc_count_from_trigger(trigger)
    if parsed is None:
        raise ValueError("arc_count is required when trigger does not contain an N-arc phrase")
    return parsed


def parse_arc_count_from_trigger(text: str) -> int | None:
    if not text:
        return None
    match = re.search(r"(\d+)\s*아크", str(text))
    if not match:
        return None
    value = int(match.group(1))
    return value if value > 0 else None


def build_target_project_name(seed_profile: str, arc_count: int, *, now: datetime | None = None) -> str:
    now = now or datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    return f"auto_test_{stamp}_{seed_profile}_{int(arc_count)}arc"


def build_execution_plan(
    *,
    arc_count: int,
    seed_profile: str,
    batch_size: int,
    target_project: str,
    trigger: str,
) -> dict[str, Any]:
    profile = default_profile(seed_profile)
    target_name = target_project or build_target_project_name(seed_profile, arc_count)
    return {
        "summary_role": "auto_frontier_lag_harness_plan",
        "created_at": _now_iso(),
        "operator_trigger": trigger,
        "arc_count": int(arc_count),
        "batch_size": max(1, int(batch_size or DEFAULT_BATCH_SIZE)),
        "seed_profile": seed_profile,
        "target_project": target_name,
        "project_locator": f"projects/{target_name}",
        "manual_profile_doc": MANUAL_PROFILE_DOC,
        "harness_ssot_doc": HARNESS_SSOT_DOC,
        "profile": asdict(profile),
    }


def run_harness(
    *,
    arc_count: int,
    seed_profile: str,
    batch_size: int,
    poll_interval_seconds: int,
    target_project: str,
    trigger: str,
) -> dict[str, Any]:
    plan = build_execution_plan(
        arc_count=arc_count,
        seed_profile=seed_profile,
        batch_size=batch_size,
        target_project=target_project,
        trigger=trigger,
    )
    project_name = str(plan["target_project"])
    project_root = PROJECT_ROOT / "projects" / project_name
    if project_root.exists():
        raise FileExistsError(f"target project already exists: {project_root}")

    command = build_worker_command(
        target_project=project_name,
        arc_count=arc_count,
        seed_profile=seed_profile,
        batch_size=batch_size,
    )
    process = subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        creationflags=_worker_creationflags(),
    )

    poll_history: list[dict[str, Any]] = []
    previous = capture_poll_snapshot(project_root, process=process)
    poll_history.append(previous)
    idle_windows = 0
    watchdog_status = "progressing"
    termination_reason = ""
    poll_interval_seconds = max(1, int(poll_interval_seconds or DEFAULT_POLL_INTERVAL_SECONDS))
    next_poll_deadline = time.monotonic() + poll_interval_seconds

    while True:
        if process.poll() is not None:
            break
        now = time.monotonic()
        if now >= next_poll_deadline:
            current = capture_poll_snapshot(project_root, process=process)
            poll_history.append(current)
            watchdog_status, idle_windows = classify_poll_transition(previous, current, idle_windows)
            if watchdog_status in {"stalled", "failed"}:
                termination_reason = watchdog_status
                _terminate_process_tree(process)
                break
            previous = current
            next_poll_deadline = now + poll_interval_seconds
            continue
        sleep_for = min(PROCESS_CHECK_INTERVAL_SECONDS, max(0.1, next_poll_deadline - now))
        time.sleep(sleep_for)

    exit_code = process.wait()
    final_snapshot = capture_poll_snapshot(project_root, process=process)
    final_snapshot["process_exit_code"] = exit_code
    poll_history.append(final_snapshot)
    _write_poll_history(project_root, poll_history)

    analysis = analyze_project(
        project_name,
        arc_count=arc_count,
        watchdog_status=watchdog_status,
        termination_reason=termination_reason,
        poll_history=poll_history,
    )
    return {
        "summary_role": "auto_frontier_lag_harness_run",
        "plan": plan,
        "worker_command": command,
        "watchdog_status": watchdog_status,
        "termination_reason": termination_reason,
        "process_exit_code": exit_code,
        "analysis": analysis,
    }


def build_worker_command(*, target_project: str, arc_count: int, seed_profile: str, batch_size: int) -> list[str]:
    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "worker",
        "--target-project",
        str(target_project),
        "--arc-count",
        str(int(arc_count)),
        "--seed-profile",
        str(seed_profile),
        "--batch-size",
        str(max(1, int(batch_size or DEFAULT_BATCH_SIZE))),
    ]


def _worker_creationflags() -> int:
    return int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))


def _menu_choice_for_value(options: tuple[str, ...] | list[str], expected: str) -> str:
    expected_text = str(expected).strip()
    for index, option in enumerate(options, 1):
        if str(option).strip() == expected_text:
            return str(index)
    raise ValueError(f"semantic option not found: {expected_text!r}")


def run_worker(*, target_project: str, arc_count: int, seed_profile: str, batch_size: int) -> dict[str, Any]:
    profile = default_profile(seed_profile)
    selected_genre = {"type": profile.genre_type, "name": profile.genre_name}
    app = _boot_app(target_project, selected_genre)
    project_root = Path(app.current_project.paths.root)
    manifest = {
        "summary_role": "auto_frontier_lag_harness_manifest",
        "created_at": _now_iso(),
        "status": "booted",
        "target_project": target_project,
        "project_locator": f"projects/{target_project}",
        "arc_count": int(arc_count),
        "batch_size": max(1, int(batch_size or DEFAULT_BATCH_SIZE)),
        "seed_profile": seed_profile,
        "manual_profile_doc": MANUAL_PROFILE_DOC,
        "harness_ssot_doc": HARNESS_SSOT_DOC,
        "profile": asdict(profile),
    }
    _update_manifest(project_root, manifest)

    try:
        _apply_stage0_existing_profile(app, profile)
        _update_manifest(project_root, {"status": "stage0_existing_complete", "updated_at": _now_iso()})

        _apply_stage0_style_profile(app, profile)
        _update_manifest(project_root, {"status": "stage0_style_complete", "updated_at": _now_iso()})

        _ensure_pass_rate_monitor(app, project_root)
        _update_manifest(project_root, {"status": "frontier_running", "updated_at": _now_iso()})

        with patch("builtins.input", side_effect=_worker_runtime_input):
            frontier_result = app._one_stop_pipeline_frontier_lag(
                max_arc_advances=int(arc_count),
                batch_size_override=max(1, int(batch_size or DEFAULT_BATCH_SIZE)),
                wait_for_menu_return=False,
            )
        if getattr(app, "pass_rate_monitor", None):
            app.pass_rate_monitor.save()
        if hasattr(app, "_flush_audit_buffer"):
            app._flush_audit_buffer()

        payload = {
            "summary_role": "auto_frontier_lag_worker_result",
            "created_at": _now_iso(),
            "status": "success",
            "project": target_project,
            "project_locator": f"projects/{target_project}",
            "arc_count": int(arc_count),
            "batch_size": max(1, int(batch_size or DEFAULT_BATCH_SIZE)),
            "frontier_result": frontier_result,
        }
        _write_json(project_root / "logs" / "auto_frontier_lag_worker_result.json", payload)
        _update_manifest(project_root, {"status": "worker_success", "updated_at": _now_iso()})
        return payload
    except Exception as exc:
        payload = {
            "summary_role": "auto_frontier_lag_worker_result",
            "created_at": _now_iso(),
            "status": "failed",
            "project": target_project,
            "project_locator": f"projects/{target_project}",
            "arc_count": int(arc_count),
            "batch_size": max(1, int(batch_size or DEFAULT_BATCH_SIZE)),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        _write_json(project_root / "logs" / "auto_frontier_lag_worker_result.json", payload)
        _update_manifest(project_root, {"status": "worker_failed", "updated_at": _now_iso(), "error": str(exc)})
        return payload
    finally:
        _close_app_handles(app)


def _boot_app(project_name: str, selected_genre: dict[str, Any]) -> SovereignApp:
    with (
        patch.object(SovereignApp, "_select_genre", return_value=selected_genre),
        patch.object(SovereignApp, "_select_project", return_value=project_name),
        patch.object(SovereignApp, "_run_main_process", lambda self: None),
    ):
        app = SovereignApp()
        app.boot()
        return app


def _apply_stage0_existing_profile(app: SovereignApp, profile: HarnessProfile) -> None:
    protagonist = profile.protagonist_config
    responses = [
        "1",
        profile.treatment_auto_condense,
        _menu_choice_for_value(WORLD_ORIGIN_OPTIONS, protagonist["world_origin"]),
        _menu_choice_for_value(INCARNATION_TYPE_OPTIONS, protagonist["incarnation_type"]),
        _menu_choice_for_value(POV_OPTIONS, protagonist["pov"]),
        _menu_choice_for_value(
            EXTERNAL_POV_INSERT_POLICY_OPTIONS,
            protagonist["external_pov_insert_policy"],
        ),
        "",
    ]
    with (
        patch.object(app, "_ui_select_bible", return_value=profile.bible_file),
        patch.object(app, "_ui_select_treatment", return_value=profile.roadmap_file),
        patch("builtins.input", side_effect=responses),
    ):
        app._phase_0_recovery()

    saved_bible = app.current_project.db.load_anchor("bible") or {}
    plot_roadmap = (
        saved_bible.get("MasterBible", saved_bible).get("plot_roadmap", []) if isinstance(saved_bible, dict) else []
    )
    if not saved_bible or not plot_roadmap:
        raise RuntimeError("stage0 existing-file replay did not persist bible/plot_roadmap")


def _apply_stage0_style_profile(app: SovereignApp, profile: HarnessProfile) -> None:
    cache_choice = {
        "use": "1",
        "refresh": "2",
        "reset": "3",
    }.get(profile.style_analysis_mode, "1")
    responses = [
        profile.style_analysis_confirm,
        cache_choice,
        "",
    ]
    with patch("builtins.input", side_effect=responses):
        app._stage_0_extended(mode=5)

    style_anchor = app.current_project.db.load_anchor("style_guide") or {}
    style_file = Path(app.current_project.paths.root) / "stage0_output" / "style_guide.json"
    if not style_anchor and not style_file.exists():
        raise RuntimeError("stage0 style-analysis replay did not persist style_guide")


def _worker_runtime_input(prompt: str = "") -> str:
    text = str(prompt or "")
    if "건너뛰고 다음 Arc로?" in text:
        return "2"
    if "[Enter] 메뉴로 돌아가기" in text:
        return ""
    return ""


def capture_poll_snapshot(project_root: Path, *, process: subprocess.Popen[Any] | None = None) -> dict[str, Any]:
    session_log = resolve_active_session_log(project_root)
    log_tail = _tail_text(session_log, max_lines=20)
    stage3_attempts, stage4_attempts, director_stage3_rows, director_stage4_rows = _read_attempt_counts(project_root)
    runtime_summary = _read_json(project_root / "logs" / "runtime_audit_summary.json")
    manifest = _read_json(project_root / "logs" / "auto_frontier_lag_harness_manifest.json")
    snapshot = {
        "captured_at": _now_iso(),
        "process_alive": bool(process is not None and process.poll() is None),
        "process_exit_code": process.poll() if process is not None else None,
        "session_log": str(session_log) if session_log else "",
        "session_log_size": session_log.stat().st_size if session_log and session_log.exists() else 0,
        "session_log_tail": log_tail,
        "blueprint_count": len(list((project_root / "plans" / "blueprints").glob("*.json"))) if project_root.exists() else 0,
        "draft_count": len(list((project_root / "drafts").glob("ep_*.txt"))) if project_root.exists() else 0,
        "stage3_attempts": stage3_attempts,
        "stage4_attempts": stage4_attempts,
        "director_stage3_rows": director_stage3_rows,
        "director_stage4_rows": director_stage4_rows,
        "runtime_audit_tag": str(runtime_summary.get("tag", "") or ""),
        "runtime_audit_total_events": int(runtime_summary.get("total_events", 0) or 0),
        "harness_phase": str(manifest.get("status", "") or ""),
        "prompt_blocked": detect_prompt_blocked(log_tail),
    }
    return snapshot


def resolve_active_session_log(project_root: Path) -> Path | None:
    if not project_root.exists():
        return None
    logs_root = project_root / "logs"
    candidates = sorted(logs_root.glob("session_*.log"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _tail_text(path: Path | None, *, max_lines: int) -> list[str]:
    if path is None or not path.exists():
        return []
    try:
        return path.read_text(encoding="utf-8").splitlines()[-max_lines:]
    except OSError:
        return []


def detect_prompt_blocked(log_tail: list[str]) -> bool:
    merged = "\n".join(str(line) for line in log_tail[-8:])
    return any(marker in merged for marker in PROMPT_WAIT_MARKERS)


def classify_poll_transition(previous: dict[str, Any], current: dict[str, Any], idle_windows: int) -> tuple[str, int]:
    if current.get("process_exit_code") not in (None, 0):
        return "failed", idle_windows

    merged_tail = "\n".join(str(line) for line in current.get("session_log_tail", []))
    if any(token in merged_tail for token in ("Traceback (most recent call last)", "❌", "crash_dump.log")):
        return "failed", idle_windows

    progress_keys = (
        "session_log_size",
        "blueprint_count",
        "draft_count",
        "stage3_attempts",
        "stage4_attempts",
        "director_stage3_rows",
        "director_stage4_rows",
        "runtime_audit_total_events",
        "harness_phase",
    )
    progressed = any(current.get(key) != previous.get(key) for key in progress_keys)
    if progressed:
        return "progressing", 0
    if current.get("prompt_blocked"):
        return "waiting_prompt", 0
    if current.get("process_alive"):
        idle_windows += 1
        if idle_windows >= 2:
            return "stalled", idle_windows
        return "stall-candidate", idle_windows
    return "idle", idle_windows


def analyze_project(
    project_name: str,
    *,
    arc_count: int | None = None,
    watchdog_status: str = "",
    termination_reason: str = "",
    poll_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    project_root = PROJECT_ROOT / "projects" / project_name
    worker_result = _read_json(project_root / "logs" / "auto_frontier_lag_worker_result.json")
    manifest = _read_json(project_root / "logs" / "auto_frontier_lag_harness_manifest.json")
    runtime_summary = _read_json(project_root / "logs" / "runtime_audit_summary.json")
    pass_rate_monitor = _read_json(project_root / "logs" / "pass_rate_monitor.json")
    poll_history_path = project_root / "logs" / "auto_frontier_lag_poll_history.jsonl"
    poll_history = poll_history or _read_jsonl(poll_history_path)

    if arc_count is None:
        arc_count = int(worker_result.get("arc_count") or manifest.get("arc_count") or 0)

    stage3_latest_session_id = ""
    stage4_latest_session_id = ""
    shared_session_id = ""
    stage3_summary: dict[str, Any] = {}
    stage4_summary: dict[str, Any] = {}
    stage3_attempts = 0
    stage4_attempts = 0

    db_path = project_root / "project_data.db"
    if db_path.exists():
        db = DBManager(db_path)
        try:
            analyzer = FailureAnalyzer(db, project_path=project_root)
            stage3_rows = db.conn.execute(
                "SELECT session_id FROM stage_attempts WHERE stage = 3 ORDER BY id ASC"
            ).fetchall()
            stage4_rows = db.conn.execute(
                "SELECT session_id FROM stage_attempts WHERE stage = 4 ORDER BY id ASC"
            ).fetchall()
            stage3_attempts = len(stage3_rows)
            stage4_attempts = len(stage4_rows)
            stage3_latest_session_id = latest_session_id_from_rows(stage3_rows)
            stage4_latest_session_id = latest_session_id_from_rows(stage4_rows)
            session_filter = stage4_latest_session_id or stage3_latest_session_id
            if stage3_latest_session_id and stage4_latest_session_id and stage3_latest_session_id == stage4_latest_session_id:
                shared_session_id = stage3_latest_session_id
            stage3_summary = analyzer.sink_alignment_summary(
                stage=3,
                include_session_decisions=True,
                session_id=session_filter or None,
            )
            stage4_summary = analyzer.sink_alignment_summary(
                stage=4,
                include_session_decisions=True,
                session_id=session_filter or None,
            )
        finally:
            db.close()

    frontier_result = worker_result.get("frontier_result", {}) if isinstance(worker_result, dict) else {}
    boundary_reached = bool(frontier_result.get("requested_limit_hit")) or (
        int(frontier_result.get("arcs_advanced", 0) or 0) >= int(arc_count or 0)
    )
    root_cause = derive_root_cause(
        worker_result=worker_result,
        watchdog_status=watchdog_status,
        stage3_summary=stage3_summary,
        stage4_summary=stage4_summary,
        boundary_reached=boundary_reached,
    )
    judgment = derive_judgment(
        worker_result=worker_result,
        watchdog_status=watchdog_status,
        boundary_reached=boundary_reached,
        stage3_summary=stage3_summary,
        stage4_summary=stage4_summary,
        root_cause=root_cause,
    )
    audit_summary = run_three_pass_audit(
        worker_result=worker_result,
        boundary_reached=boundary_reached,
        stage3_summary=stage3_summary,
        stage4_summary=stage4_summary,
        judgment=judgment,
        root_cause=root_cause,
        poll_history=poll_history,
    )

    payload = {
        "summary_role": "auto_frontier_lag_runtime_analysis",
        "generated_at": _now_iso(),
        "project": project_name,
        "project_locator": f"projects/{project_name}",
        "arc_count": int(arc_count or 0),
        "watchdog_status": watchdog_status,
        "termination_reason": termination_reason,
        "worker_status": str(worker_result.get("status", "") or ""),
        "boundary_reached": boundary_reached,
        "frontier_result": frontier_result,
        "runtime_audit_summary": runtime_summary,
        "pass_rate_monitor_exists": bool(pass_rate_monitor),
        "stage3_attempts": stage3_attempts,
        "stage4_attempts": stage4_attempts,
        "stage3_latest_session_id": stage3_latest_session_id,
        "stage4_latest_session_id": stage4_latest_session_id,
        "shared_session_id": shared_session_id,
        "stage3_current_session_sink_alignment_summary": stage3_summary,
        "stage4_current_session_sink_alignment_summary": stage4_summary,
        "judgment": judgment,
        "root_cause": root_cause,
        "poll_count": len(poll_history),
        "poll_history_path": str(poll_history_path) if poll_history else "",
        "three_pass_audit": audit_summary,
    }
    _write_json(project_root / "logs" / "auto_frontier_lag_analysis.json", payload)
    if judgment != "success":
        _write_json(
            project_root / "logs" / "auto_frontier_lag_failure_digest.json",
            {
                "generated_at": _now_iso(),
                "project_locator": payload["project_locator"],
                "judgment": judgment,
                "root_cause": root_cause,
                "watchdog_status": watchdog_status,
            },
        )
    ssot_path = write_execution_ssot(payload)
    payload["ssot_path"] = str(ssot_path)
    return payload


def derive_root_cause(
    *,
    worker_result: dict[str, Any],
    watchdog_status: str,
    stage3_summary: dict[str, Any],
    stage4_summary: dict[str, Any],
    boundary_reached: bool,
) -> str:
    worker_status = str(worker_result.get("status", "") or "")
    if watchdog_status == "stalled":
        return "watchdog_stalled_after_two_idle_windows"
    if watchdog_status == "failed":
        return "watchdog_observed_runtime_failure"
    if worker_status == "failed":
        return str(worker_result.get("error", "") or "worker_failed")
    if not boundary_reached:
        return "requested_arc_boundary_not_reached"
    if stage3_summary and str(stage3_summary.get("status", "") or "") != "ok":
        return "stage3_current_session_sink_alignment_not_ok"
    if stage4_summary and str(stage4_summary.get("status", "") or "") != "ok":
        return "stage4_current_session_sink_alignment_not_ok"
    return ""


def derive_judgment(
    *,
    worker_result: dict[str, Any],
    watchdog_status: str,
    boundary_reached: bool,
    stage3_summary: dict[str, Any],
    stage4_summary: dict[str, Any],
    root_cause: str,
) -> str:
    if watchdog_status == "stalled":
        return "stalled"
    if watchdog_status == "failed":
        return "failed"
    if str(worker_result.get("status", "") or "") != "success":
        return "failed"
    if not boundary_reached:
        return "failed"
    if stage3_summary and str(stage3_summary.get("status", "") or "") != "ok":
        return "failed"
    if stage4_summary and str(stage4_summary.get("status", "") or "") != "ok":
        return "failed"
    return "success" if not root_cause else "failed"


def run_three_pass_audit(
    *,
    worker_result: dict[str, Any],
    boundary_reached: bool,
    stage3_summary: dict[str, Any],
    stage4_summary: dict[str, Any],
    judgment: str,
    root_cause: str,
    poll_history: list[dict[str, Any]],
) -> dict[str, Any]:
    pass1 = bool(worker_result) and bool(poll_history)
    pass2 = (judgment == "success") == (
        boundary_reached
        and str(stage3_summary.get("status", "") or "ok") == "ok"
        and str(stage4_summary.get("status", "") or "ok") == "ok"
        and not bool(root_cause)
    )
    pass3 = bool(judgment) and ((judgment == "success" and not root_cause) or (judgment != "success" and bool(root_cause)))
    passed = sum(1 for item in (pass1, pass2, pass3) if item)
    confidence = 60 + passed * 10
    if judgment == "success":
        confidence = 95 if passed == 3 else min(confidence, 90)
    else:
        confidence = min(confidence, 90)
    return {
        "passes": {
            "pass1_fact_extraction": pass1,
            "pass2_contradiction_check": pass2,
            "pass3_decision_audit": pass3,
        },
        "confidence": confidence,
        "finalized": confidence >= 95,
    }


def write_execution_ssot(analysis: dict[str, Any]) -> Path:
    dt = datetime.now()
    doc_dir = PROJECT_ROOT / "docs" / dt.strftime("%Y-%m-%d")
    doc_dir.mkdir(parents=True, exist_ok=True)
    arc_count = int(analysis.get("arc_count", 0) or 0)
    path = doc_dir / f"auto-frontier-lag-{arc_count}arc-runtime-analysis-ssot.md"
    lines = [
        f"# Auto Frontier Lag {arc_count}Arc Runtime Analysis SSOT",
        "",
        f"- generated_at: {analysis.get('generated_at', '')}",
        f"- project_locator: {analysis.get('project_locator', '')}",
        f"- judgment: {analysis.get('judgment', '')}",
        f"- root_cause: {analysis.get('root_cause', '') or 'none'}",
        f"- watchdog_status: {analysis.get('watchdog_status', '') or 'n/a'}",
        f"- shared_session_id: {analysis.get('shared_session_id', '') or '-'}",
        "",
        "## Input Profile",
        "",
        f"- manual_profile_doc: `{MANUAL_PROFILE_DOC}`",
        f"- harness_ssot_doc: `{HARNESS_SSOT_DOC}`",
        f"- arc_count: {analysis.get('arc_count', 0)}",
        "- worker_model: subprocess-owned Python worker booting `SovereignApp` via direct seams",
        "",
        "## Terminal Watchdog",
        "",
        "- review cadence: every 30 minutes from the terminal-owned watchdog",
        "- no hard process timeout was part of the contract",
        f"- responsive process check interval: {PROCESS_CHECK_INTERVAL_SECONDS}s",
        "- graceful stop path: CTRL_BREAK / Ctrl+C first, terminate/kill only as fallback",
        f"- poll_count: {analysis.get('poll_count', 0)}",
        f"- poll_history_path: `{analysis.get('poll_history_path', '')}`",
        "",
        "## Evidence",
        "",
        f"- worker_status: {analysis.get('worker_status', '')}",
        f"- boundary_reached: {analysis.get('boundary_reached', False)}",
        f"- pass_rate_monitor_exists: {analysis.get('pass_rate_monitor_exists', False)}",
        f"- stage3_current_session_status: {((analysis.get('stage3_current_session_sink_alignment_summary') or {}).get('status', 'missing'))}",
        f"- stage4_current_session_status: {((analysis.get('stage4_current_session_sink_alignment_summary') or {}).get('status', 'missing'))}",
        "",
        "## 3-Pass Audit",
        "",
        f"- pass1_fact_extraction: {analysis['three_pass_audit']['passes']['pass1_fact_extraction']}",
        f"- pass2_contradiction_check: {analysis['three_pass_audit']['passes']['pass2_contradiction_check']}",
        f"- pass3_decision_audit: {analysis['three_pass_audit']['passes']['pass3_decision_audit']}",
        f"- confidence: {analysis['three_pass_audit']['confidence']}%",
        f"- finalized: {analysis['three_pass_audit']['finalized']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def latest_session_id_from_rows(rows: list[Any]) -> str:
    for row in reversed(rows):
        if isinstance(row, dict):
            value = row.get("session_id")
        elif hasattr(row, "keys") and "session_id" in row.keys():
            value = row["session_id"]
        else:
            value = getattr(row, "session_id", None)
            if value is None and isinstance(row, (list, tuple)) and row:
                value = row[0]
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _read_attempt_counts(project_root: Path) -> tuple[int, int, int, int]:
    db_path = project_root / "project_data.db"
    if not db_path.exists():
        return (0, 0, 0, 0)
    db = DBManager(db_path)
    try:
        stage3_attempts = db.conn.execute("SELECT COUNT(*) FROM stage_attempts WHERE stage = 3").fetchone()[0]
        stage4_attempts = db.conn.execute("SELECT COUNT(*) FROM stage_attempts WHERE stage = 4").fetchone()[0]
        director_stage3 = db.conn.execute(
            "SELECT COUNT(*) FROM director_selections WHERE " + DBManager._director_stage_predicate(3)
        ).fetchone()[0]
        director_stage4 = db.conn.execute(
            "SELECT COUNT(*) FROM director_selections WHERE " + DBManager._director_stage_predicate(4)
        ).fetchone()[0]
        return (int(stage3_attempts), int(stage4_attempts), int(director_stage3), int(director_stage4))
    finally:
        db.close()


def _ensure_pass_rate_monitor(app: SovereignApp, project_root: Path) -> None:
    if getattr(app, "pass_rate_monitor", None):
        return
    app.pass_rate_monitor = PassRateMonitor(project_root)


def _terminate_process_tree(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    ctrl_break = getattr(signal, "CTRL_BREAK_EVENT", None)
    if ctrl_break is not None:
        try:
            process.send_signal(ctrl_break)
        except Exception:
            pass
        else:
            for _ in range(10):
                if process.poll() is not None:
                    return
                time.sleep(1)
    try:
        process.terminate()
    except Exception:
        return
    for _ in range(10):
        if process.poll() is not None:
            return
        time.sleep(1)
    try:
        process.kill()
    except Exception:
        pass


def _write_poll_history(project_root: Path, history: list[dict[str, Any]]) -> None:
    if not project_root.exists():
        return
    log_path = project_root / "logs" / "auto_frontier_lag_poll_history.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(item, ensure_ascii=False) for item in history]
    log_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _update_manifest(project_root: Path, payload: dict[str, Any]) -> None:
    path = project_root / "logs" / "auto_frontier_lag_harness_manifest.json"
    current = _read_json(path)
    current.update(payload)
    _write_json(path, current)


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


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
