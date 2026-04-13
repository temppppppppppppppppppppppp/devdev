#!/usr/bin/env python3
"""Create recommended material-side ClickUp views for the production schedule list."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.setup_clickup_views import main as setup_clickup_views_main
from scripts.sync_clickup_queue import ClickUpSyncError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
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
        help="Print planned changes without creating views.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    delegated = [
        "--profile",
        "material",
        "--list-id",
        str(args.list_id),
        "--token-env",
        args.token_env,
    ]
    if args.dry_run:
        delegated.append("--dry-run")
    return setup_clickup_views_main(delegated)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ClickUpSyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
