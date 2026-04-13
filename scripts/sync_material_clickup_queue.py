#!/usr/bin/env python3
"""Build and sync the material-side production queue into a ClickUp List."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_material_queue_state import DEFAULT_OUTPUT_PATH
from scripts.build_material_queue_state import main as build_material_queue_main
from scripts.sync_clickup_queue import ClickUpSyncError
from scripts.sync_clickup_queue import main as sync_clickup_main

DEFAULT_STATE_PATH = ROOT / "docs" / "temp" / "clickup-material-sync-state.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queue-state-path",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Material-side queue-state output path.",
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="Material-side ClickUp sync-state file.",
    )
    parser.add_argument(
        "--list-id",
        default=os.environ.get("CLICKUP_MATERIAL_LIST_ID", "").strip() or os.environ.get("CLICKUP_LIST_ID", "").strip(),
        help="ClickUp List ID. Defaults to CLICKUP_MATERIAL_LIST_ID, then CLICKUP_LIST_ID.",
    )
    parser.add_argument(
        "--token-env",
        default="CLICKUP_API_TOKEN",
        help="Environment variable containing the ClickUp personal token.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect planned changes without mutating ClickUp tasks.",
    )
    parser.add_argument(
        "--inspect-list",
        action="store_true",
        help="Inspect the target List statuses/custom fields and exit.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only sync the first N material queue items.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Reuse the existing material queue-state file instead of rebuilding it first.",
    )
    parser.add_argument(
        "--include-completed",
        action="store_true",
        help="Include completed/historical material works in the generated queue snapshot. Default behavior already includes them.",
    )
    parser.add_argument(
        "--active-only",
        action="store_true",
        help="Emit only canon-stage and in-flight material work, excluding completed works.",
    )
    return parser


def _seed_material_env() -> None:
    material_env_file = os.environ.get("CLICKUP_MATERIAL_ENV_FILE", "").strip()
    if material_env_file and not os.environ.get("CLICKUP_ENV_FILE", "").strip():
        os.environ["CLICKUP_ENV_FILE"] = material_env_file
    material_status_map = os.environ.get("CLICKUP_MATERIAL_STATUS_MAP_JSON", "").strip()
    if material_status_map and not os.environ.get("CLICKUP_STATUS_MAP_JSON", "").strip():
        os.environ["CLICKUP_STATUS_MAP_JSON"] = material_status_map


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _seed_material_env()

    queue_state_path = args.queue_state_path.resolve()
    if not args.skip_build:
        build_args = ["--output", str(queue_state_path)]
        if args.include_completed:
            build_args.append("--include-completed")
        if args.active_only:
            build_args.append("--active-only")
        build_material_queue_main(build_args)

    sync_args = [
        "--profile",
        "material",
        "--queue-state-path",
        str(queue_state_path),
        "--state-path",
        str(args.state_path.resolve()),
        "--list-id",
        str(args.list_id),
        "--token-env",
        args.token_env,
    ]
    if args.dry_run:
        sync_args.append("--dry-run")
    if args.inspect_list:
        sync_args.append("--inspect-list")
    if args.limit is not None:
        sync_args.extend(["--limit", str(args.limit)])

    return sync_clickup_main(sync_args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ClickUpSyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
