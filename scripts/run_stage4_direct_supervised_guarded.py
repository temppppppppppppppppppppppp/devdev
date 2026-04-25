"""Run Stage 4 direct supervised inside a monitored wrapper.

This launcher delegates the actual Stage 4 execution to
`run_stage4_direct_supervised.py`, then polls the authoritative stage_attempts
sink at a fixed interval. If any Stage 4 episode exceeds the configured
attempt ceiling, the child run is terminated and the run is archived as an
operational failure.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.benchmark_archive_runtime import safe_archive_benchmark_record  # noqa: E402
from scripts.canary_path_utils import project_name_from_path, resolve_workspace_project_dir  # noqa: E402
from scripts.canary_semantic_exit import guarded_stage4_exit_code  # noqa: E402
from scripts.run_stage4_direct_supervised import (  # noqa: E402
    _load_latest_written_ep,
    _load_project_genre,
    _load_runtime_audit_tag,
)

DEFAULT_POLL_INTERVAL_SECONDS = 300
DEFAULT_TERMINATION_GRACE_SECONDS = 20
MONITOR_TICK_SECONDS = 2
_ROUND_PATTERNS = (
    re.compile(r"\[Round\s+(\d+)/(\d+)\]"),
    re.compile(r"\[(\d+)차 면담\]"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guarded direct supervised Stage 4 runner")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--project", required=True)
    parser.add_argument("--target-ep", type=int, required=True)
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=5,
        help="Maximum allowed Stage 4 attempt_num for a single episode before forced stop.",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="How often to inspect stage_attempts while the child process is running.",
    )
    parser.add_argument(
        "--termination-grace-seconds",
        type=int,
        default=DEFAULT_TERMINATION_GRACE_SECONDS,
        help="How long to wait after terminate() before escalating to kill().",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command != "run":
        raise ValueError(f"unsupported command: {args.command}")

    payload = run_guarded_stage4(
        args.project,
        target_ep=args.target_ep,
        max_attempts=args.max_attempts,
        poll_interval_seconds=args.poll_interval_seconds,
        termination_grace_seconds=args.termination_grace_seconds,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return guarded_stage4_exit_code(payload)


def run_guarded_stage4(
    project_name: str,
    *,
    target_ep: int,
    max_attempts: int,
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS,
    termination_grace_seconds: int = DEFAULT_TERMINATION_GRACE_SECONDS,
) -> dict[str, Any]:
    if target_ep < 1:
        raise ValueError("target-ep must be >= 1")
    if max_attempts < 1:
        raise ValueError("max-attempts must be >= 1")
    if poll_interval_seconds < 1:
        raise ValueError("poll-interval-seconds must be >= 1")
    if termination_grace_seconds < 1:
        raise ValueError("termination-grace-seconds must be >= 1")

    project_root = resolve_workspace_project_dir(PROJECT_ROOT, project_name, prefer_canary=False, require_exists=True)
    runtime_project_name = project_name_from_path(PROJECT_ROOT, project_root)
    selected_genre = _load_project_genre(project_root)
    if not selected_genre:
        raise RuntimeError(f"genre_info anchor missing or invalid for {runtime_project_name}")

    before_latest_ep = _load_latest_written_ep(project_root)
    baseline_attempt_id = _capture_stage4_baseline(project_root)
    launched_at = _now_iso()
    launched_at_epoch = time.time()
    child = _launch_direct_stage4_child(runtime_project_name, target_ep=target_ep)
    stream_state = _build_stream_monitor_state()
    stream_threads = _start_child_stream_pumps(child, stream_state)

    child_exit_code: int | None = None
    terminated_by_monitor = False
    termination_method = ""
    termination_reason = ""
    observed_ep: int | None = None
    observed_attempt_num: int | None = None
    monitor_checks: list[dict[str, Any]] = []
    next_db_check_at = time.monotonic() + poll_interval_seconds

    while True:
        try:
            child_exit_code = child.wait(timeout=min(MONITOR_TICK_SECONDS, poll_interval_seconds))
            break
        except subprocess.TimeoutExpired:
            round_snapshot = _get_stream_monitor_snapshot(stream_state)
            if int(round_snapshot.get("latest_round_seen") or 0) > max_attempts:
                terminated_by_monitor = True
                termination_reason = "stage4_round_limit_exceeded"
                observed_attempt_num = int(round_snapshot.get("latest_round_seen") or 0)
                termination_method, child_exit_code = _terminate_process(child, termination_grace_seconds)
                break
            now = time.monotonic()
            if now < next_db_check_at:
                continue
            next_db_check_at = now + poll_interval_seconds
            snapshot = _load_stage4_attempt_summary(project_root, baseline_attempt_id)
            check_record = {
                "checked_at": _now_iso(),
                "max_attempt_num": snapshot.get("max_attempt_num", 0),
                "ep_num": snapshot.get("ep_num"),
                "episodes": snapshot.get("episodes", []),
                "latest_round_seen": round_snapshot.get("latest_round_seen", 0),
                "latest_round_total": round_snapshot.get("latest_round_total", 0),
            }
            monitor_checks.append(check_record)
            if int(snapshot.get("max_attempt_num") or 0) > max_attempts:
                terminated_by_monitor = True
                termination_reason = "stage4_attempt_limit_exceeded"
                observed_ep = snapshot.get("ep_num")
                observed_attempt_num = int(snapshot.get("max_attempt_num") or 0)
                termination_method, child_exit_code = _terminate_process(child, termination_grace_seconds)
                break

    if child_exit_code is None:
        child_exit_code = child.poll()
    _join_child_stream_pumps(stream_threads)

    after_latest_ep = _load_latest_written_ep(project_root)
    runtime_audit_tag = _load_runtime_audit_tag(project_root)
    child_summary = _load_json_if_exists(
        project_root / "logs" / "stage4_direct_supervised_result.json",
        min_mtime_epoch=launched_at_epoch,
    )
    round_snapshot = _get_stream_monitor_snapshot(stream_state)
    clean_exit = child_exit_code in (0, None)

    payload: dict[str, Any] = {}
    if isinstance(child_summary, dict):
        payload.update(child_summary)
    payload.update(
        {
            "project": runtime_project_name,
            "project_root": str(project_root),
            "target_ep": target_ep,
            "latest_written_ep_before": before_latest_ep,
            "latest_written_ep_after": after_latest_ep,
            "runtime_audit_tag": runtime_audit_tag,
            "monitor_policy": {
                "poll_interval_seconds": poll_interval_seconds,
                "max_attempts": max_attempts,
                "termination_grace_seconds": termination_grace_seconds,
                "attempt_authority_sink": "stage_attempts",
                "attempt_threshold_rule": f"terminate when stage4 attempt_num > {max_attempts}",
                "round_threshold_rule": f"terminate when observed round > {max_attempts}",
            },
            "monitor_launched_at": launched_at,
            "monitor_checks": monitor_checks,
            "monitor_check_count": len(monitor_checks),
            "baseline_stage4_attempt_id": baseline_attempt_id,
            "latest_round_seen": int(round_snapshot.get("latest_round_seen") or 0),
            "latest_round_total": int(round_snapshot.get("latest_round_total") or 0),
            "terminated_by_monitor": terminated_by_monitor,
            "termination_reason": termination_reason,
            "termination_method": termination_method,
            "terminated_ep": observed_ep,
            "terminated_attempt_num": observed_attempt_num,
            "child_exit_code": child_exit_code,
        }
    )

    if terminated_by_monitor:
        payload["success"] = False
        archive_status = "operational_failure"
    else:
        success = False
        if clean_exit:
            success = bool(payload.get("success"))
            if not child_summary:
                success = after_latest_ep >= target_ep
        payload["success"] = success
        archive_status = "completed" if success else ("operational_failure" if not clean_exit else "partial")

    archive_notes = _build_archive_notes(
        target_ep=target_ep,
        max_attempts=max_attempts,
        before_latest_ep=before_latest_ep,
        after_latest_ep=after_latest_ep,
        runtime_audit_tag=runtime_audit_tag,
        child_exit_code=child_exit_code,
        terminated_by_monitor=terminated_by_monitor,
        termination_reason=termination_reason,
        observed_ep=observed_ep,
        observed_attempt_num=observed_attempt_num,
    )
    payload["benchmark_archive"] = safe_archive_benchmark_record(
        workspace_root=PROJECT_ROOT,
        project=runtime_project_name,
        lane="stage4-supervised",
        target_ep=target_ep,
        status=archive_status,
        notes=archive_notes,
    )

    _write_summary(project_root / "logs" / "stage4_direct_supervised_result.json", payload)
    _write_summary(project_root / "logs" / "stage4_direct_supervised_guarded_result.json", payload)
    return payload


def _launch_direct_stage4_child(project_name: str, *, target_ep: int) -> subprocess.Popen[str]:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "run_stage4_direct_supervised.py"),
        "run",
        "--project",
        project_name,
        "--target-ep",
        str(target_ep),
        "--skip-benchmark-archive",
    ]
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        env=env,
    )


def _build_stream_monitor_state() -> dict[str, Any]:
    return {
        "lock": threading.Lock(),
        "latest_round_seen": 0,
        "latest_round_total": 0,
        "lines_seen": 0,
    }


def _start_child_stream_pumps(proc: subprocess.Popen[str], state: dict[str, Any]) -> list[threading.Thread]:
    threads: list[threading.Thread] = []
    for stream_name, mirror in (("stdout", sys.stdout), ("stderr", sys.stderr)):
        stream = getattr(proc, stream_name, None)
        if stream is None:
            continue
        thread = threading.Thread(
            target=_pump_child_stream,
            args=(stream, mirror, state),
            name=f"stage4-guarded-{stream_name}",
            daemon=True,
        )
        thread.start()
        threads.append(thread)
    return threads


def _join_child_stream_pumps(threads: list[threading.Thread]) -> None:
    for thread in threads:
        thread.join(timeout=1)


def _pump_child_stream(stream, mirror, state: dict[str, Any]) -> None:
    try:
        for line in iter(stream.readline, ""):
            if not line:
                break
            _update_stream_monitor_state(state, line)
            try:
                mirror.write(line)
                mirror.flush()
            except Exception:
                pass
    finally:
        try:
            stream.close()
        except Exception:
            pass


def _update_stream_monitor_state(state: dict[str, Any], line: str) -> None:
    latest_round_seen = 0
    latest_round_total = 0
    for pattern in _ROUND_PATTERNS:
        match = pattern.search(line)
        if not match:
            continue
        latest_round_seen = int(match.group(1) or 0)
        if match.lastindex and match.lastindex >= 2:
            latest_round_total = int(match.group(2) or 0)
        break

    with state["lock"]:
        state["lines_seen"] = int(state.get("lines_seen", 0) or 0) + 1
        if latest_round_seen > int(state.get("latest_round_seen", 0) or 0):
            state["latest_round_seen"] = latest_round_seen
        if latest_round_total > int(state.get("latest_round_total", 0) or 0):
            state["latest_round_total"] = latest_round_total


def _get_stream_monitor_snapshot(state: dict[str, Any]) -> dict[str, int]:
    with state["lock"]:
        return {
            "latest_round_seen": int(state.get("latest_round_seen", 0) or 0),
            "latest_round_total": int(state.get("latest_round_total", 0) or 0),
            "lines_seen": int(state.get("lines_seen", 0) or 0),
        }


def _capture_stage4_baseline(project_root: Path) -> int:
    db_path = project_root / "project_data.db"
    if not db_path.exists():
        return 0
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT COALESCE(MAX(id), 0) AS max_id FROM stage_attempts WHERE stage = 4").fetchone()
    return int(row["max_id"] if row else 0)


def _load_stage4_attempt_summary(project_root: Path, baseline_attempt_id: int) -> dict[str, Any]:
    db_path = project_root / "project_data.db"
    if not db_path.exists():
        return {"ep_num": None, "max_attempt_num": 0, "episodes": []}

    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT ep_num,
                       MAX(attempt_num) AS max_attempt_num,
                       COUNT(*) AS row_count,
                       MAX(id) AS latest_id,
                       MAX(ts) AS latest_ts
                FROM stage_attempts
                WHERE stage = 4 AND id > ?
                GROUP BY ep_num
                ORDER BY latest_id DESC, ep_num DESC
                """,
                (baseline_attempt_id,),
            ).fetchall()
    except sqlite3.Error:
        return {"ep_num": None, "max_attempt_num": 0, "episodes": []}

    episodes = [
        {
            "ep_num": int(row["ep_num"] or 0),
            "max_attempt_num": int(row["max_attempt_num"] or 0),
            "row_count": int(row["row_count"] or 0),
            "latest_id": int(row["latest_id"] or 0),
            "latest_ts": str(row["latest_ts"] or ""),
        }
        for row in rows
    ]
    if not episodes:
        return {"ep_num": None, "max_attempt_num": 0, "episodes": []}
    hottest = max(episodes, key=lambda item: (item["max_attempt_num"], item["latest_id"], item["ep_num"]))
    return {
        "ep_num": hottest["ep_num"],
        "max_attempt_num": hottest["max_attempt_num"],
        "episodes": episodes,
    }


def _terminate_process(proc: subprocess.Popen[str], grace_seconds: int) -> tuple[str, int | None]:
    proc.terminate()
    try:
        return "terminate", proc.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        proc.kill()
        return "kill", proc.wait(timeout=grace_seconds)


def _build_archive_notes(
    *,
    target_ep: int,
    max_attempts: int,
    before_latest_ep: int,
    after_latest_ep: int,
    runtime_audit_tag: str,
    child_exit_code: int | None,
    terminated_by_monitor: bool,
    termination_reason: str,
    observed_ep: int | None,
    observed_attempt_num: int | None,
) -> str:
    parts = [
        "guarded direct supervised stage4",
        f"target_ep={target_ep}",
        f"max_attempts={max_attempts}",
        f"before_latest_ep={before_latest_ep}",
        f"after_latest_ep={after_latest_ep}",
        f"runtime_audit_tag={runtime_audit_tag or 'missing'}",
        f"child_exit_code={child_exit_code}",
    ]
    if terminated_by_monitor:
        parts.extend(
            [
                "terminated_by_monitor=true",
                f"termination_reason={termination_reason or 'unspecified'}",
                f"terminated_ep={observed_ep}",
                f"terminated_attempt_num={observed_attempt_num}",
            ]
        )
    return "; ".join(parts)


def _load_json_if_exists(path: Path, *, min_mtime_epoch: float | None = None) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if min_mtime_epoch is not None and path.stat().st_mtime < float(min_mtime_epoch):
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _write_summary(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
