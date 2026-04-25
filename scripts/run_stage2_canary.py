"""Prepare, run, and analyze a repeatable Stage 2 canary project."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.stage4_canary_tools import (  # noqa: E402
    build_stage2_canary_summary,
    prepare_stage2_canary_project,
)
from scripts.benchmark_archive_runtime import safe_archive_benchmark_record  # noqa: E402
from scripts.canary_path_utils import (  # noqa: E402
    canary_runtime_env,
    project_name_from_path,
    resolve_workspace_project_dir,
)
from scripts.canary_semantic_exit import semantic_exit_code  # noqa: E402
from scripts.regression_validation_tiers import FULL_CANARY_PROOF  # noqa: E402

VALIDATION_TIER = FULL_CANARY_PROOF
MUTATES_PROJECT_STATE = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 2 canary helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="copy a baseline project and keep only the first N arcs")
    prepare.add_argument("--source-project", required=True)
    prepare.add_argument("--target-project", required=True)
    prepare.add_argument("--keep-arcs", type=int, required=True)
    prepare.add_argument("--force", action="store_true")

    run = subparsers.add_parser("run", help="run Stage 2 on a prepared project")
    run.add_argument("--project", required=True)
    run.add_argument("--target-arc-count", type=int, required=True)
    run.add_argument("--expected-final-arcs", type=int)

    analyze = subparsers.add_parser("analyze", help="analyze a prepared or completed Stage 2 canary")
    analyze.add_argument("--project", required=True)
    analyze.add_argument("--expected-final-arcs", type=int)

    full = subparsers.add_parser("full", help="prepare, run, and analyze in one command")
    full.add_argument("--source-project", required=True)
    full.add_argument("--target-project", required=True)
    full.add_argument("--keep-arcs", type=int, required=True)
    full.add_argument("--target-arc-count", type=int, required=True)
    full.add_argument("--expected-final-arcs", type=int)
    full.add_argument("--force", action="store_true")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "prepare":
        payload = prepare_canary(args.source_project, args.target_project, keep_arcs=args.keep_arcs, force=args.force)
        _print_json(payload)
        return 0

    if args.command == "run":
        payload = run_canary(
            args.project,
            target_arc_count=args.target_arc_count,
            expected_final_arcs=args.expected_final_arcs,
        )
        _print_json(payload)
        return semantic_exit_code(payload)

    if args.command == "analyze":
        payload = analyze_canary(args.project, expected_final_arcs=args.expected_final_arcs)
        _print_json(payload)
        return 0

    payload = prepare_canary(args.source_project, args.target_project, keep_arcs=args.keep_arcs, force=args.force)
    _print_json(payload)
    expected_final_arcs = args.expected_final_arcs
    if expected_final_arcs is None:
        expected_final_arcs = int(args.keep_arcs) + int(args.target_arc_count)
    payload = run_canary(
        args.target_project,
        target_arc_count=args.target_arc_count,
        expected_final_arcs=expected_final_arcs,
    )
    _print_json(payload)
    return semantic_exit_code(payload)


def prepare_canary(source_project: str, target_project: str, *, keep_arcs: int, force: bool) -> dict:
    source_root = resolve_workspace_project_dir(PROJECT_ROOT, source_project, prefer_canary=False, require_exists=True)
    target_root = resolve_workspace_project_dir(PROJECT_ROOT, target_project, prefer_canary=True, require_exists=False)
    return prepare_stage2_canary_project(source_root, target_root, keep_arcs=keep_arcs, force=force)


def run_canary(project_name: str, *, target_arc_count: int, expected_final_arcs: int | None = None) -> dict:
    project_root = resolve_workspace_project_dir(PROJECT_ROOT, project_name, prefer_canary=True, require_exists=True)
    runtime_project_name = project_name_from_path(PROJECT_ROOT, project_root)
    runner = PROJECT_ROOT / "scripts" / "canary_stage2_headless.py"
    subprocess.run(
        [sys.executable, str(runner), runtime_project_name, str(int(target_arc_count))],
        cwd=PROJECT_ROOT,
        env=canary_runtime_env(PROJECT_ROOT, project_path=project_root),
        check=True,
    )
    payload = analyze_canary(runtime_project_name, expected_final_arcs=expected_final_arcs)
    payload["benchmark_archive"] = safe_archive_benchmark_record(
        workspace_root=PROJECT_ROOT,
        project=runtime_project_name,
        lane="stage2-canary",
        status="completed" if payload.get("hard_gates", {}).get("status") == "pass" else "partial",
        notes=(
            f"stage2 canary run; target_arc_count={target_arc_count}; "
            f"expected_final_arcs={expected_final_arcs if expected_final_arcs is not None else ''}"
        ),
    )
    return payload


def analyze_canary(project_name: str, *, expected_final_arcs: int | None = None) -> dict:
    project_root = resolve_workspace_project_dir(PROJECT_ROOT, project_name, prefer_canary=True, require_exists=True)
    summary = build_stage2_canary_summary(project_root, expected_final_arc_count=expected_final_arcs)
    summary_path = project_root / "logs" / "stage2_canary_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
