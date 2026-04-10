"""Create recommended ClickUp views for the repo-side queue mirror."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.sync_clickup_queue import ClickUpClient, ClickUpSyncError, _load_dotenv_if_available


OPERATIONS_BOARD_NAME = "글도비 운영 보드"
FULL_QUEUE_TABLE_NAME = "글도비 전체 큐"


def _extract_views(payload: dict[str, Any]) -> list[dict[str, Any]]:
    views = payload.get("views")
    if not isinstance(views, list):
        return []
    return [view for view in views if isinstance(view, dict)]


def _base_columns() -> dict[str, Any]:
    return {
        "fields": [
            {"field": "name", "idx": 0, "width": None, "hidden": False, "name": None, "display": None, "pinned": None},
            {"field": "status", "idx": 1, "width": None, "hidden": False, "name": None, "display": None, "pinned": None},
            {"field": "assignee", "idx": 2, "width": None, "hidden": False, "name": None, "display": None, "pinned": None},
            {"field": "priority", "idx": 3, "width": None, "hidden": False, "name": None, "display": None, "pinned": None},
            {"field": "dueDate", "idx": 4, "width": None, "hidden": False, "name": None, "display": None, "pinned": None},
        ]
    }


def build_operations_board_payload() -> dict[str, Any]:
    return {
        "name": OPERATIONS_BOARD_NAME,
        "type": "board",
        "grouping": {
            "field": "status",
            "dir": 1,
            "collapsed": [],
            "ignore": False,
            "single": False,
        },
        "divide": {
            "field": None,
            "dir": None,
            "by_subcategory": None,
            "collapsed": [],
        },
        "sorting": {"fields": []},
        "filters": {
            "op": "AND",
            "fields": [],
            "search": None,
            "search_custom_fields": None,
            "search_description": False,
            "search_name": False,
            "show_closed": False,
        },
        "columns": _base_columns(),
        "team_sidebar": {
            "assignees": [],
            "group_assignees": [],
            "assigned_comments": False,
            "unassigned_tasks": False,
        },
        "settings": {
            "show_task_locations": False,
            "show_subtasks": 3,
            "show_subtask_parent_names": False,
            "show_closed_subtasks": False,
            "show_assignees": True,
            "show_images": True,
            "show_timer": False,
            "collapse_empty_columns": False,
            "me_comments": True,
            "me_subtasks": True,
            "me_checklists": True,
            "show_empty_statuses": True,
            "auto_wrap": False,
            "time_in_status_view": 1,
            "is_description_pinned": False,
            "override_parent_hierarchy_filter": False,
            "fast_load_mode": False,
        },
    }


def build_full_queue_table_payload() -> dict[str, Any]:
    return {
        "name": FULL_QUEUE_TABLE_NAME,
        "type": "table",
        "grouping": {
            "field": "none",
            "dir": None,
            "collapsed": [],
            "ignore": False,
            "single": False,
        },
        "divide": {
            "field": None,
            "dir": None,
            "by_subcategory": None,
            "collapsed": [],
        },
        "sorting": {"fields": []},
        "filters": {
            "op": "AND",
            "fields": [],
            "search": None,
            "search_custom_fields": None,
            "search_description": False,
            "search_name": False,
            "show_closed": True,
        },
        "columns": _base_columns(),
        "team_sidebar": {
            "assignees": [],
            "group_assignees": [],
            "assigned_comments": False,
            "unassigned_tasks": False,
        },
        "settings": {
            "show_task_locations": False,
            "show_subtasks": 3,
            "show_subtask_parent_names": False,
            "show_closed_subtasks": True,
            "show_assignees": True,
            "show_images": True,
            "show_timer": False,
            "collapse_empty_columns": None,
            "me_comments": True,
            "me_subtasks": True,
            "me_checklists": True,
            "show_empty_statuses": True,
            "auto_wrap": False,
            "time_in_status_view": 1,
            "is_description_pinned": False,
            "override_parent_hierarchy_filter": False,
            "fast_load_mode": False,
        },
    }


def _find_view_by_name(views: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    target = name.strip().lower()
    for view in views:
        if str(view.get("name") or "").strip().lower() == target:
            return view
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--list-id",
        default=os.environ.get("CLICKUP_LIST_ID", "").strip(),
        help="ClickUp List ID. Defaults to CLICKUP_LIST_ID.",
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
    _load_dotenv_if_available()
    parser = build_parser()
    args = parser.parse_args(argv)
    list_id = str(args.list_id or "").strip()
    token = os.environ.get(args.token_env, "").strip()
    if not list_id:
        raise ClickUpSyncError("missing ClickUp list ID; pass --list-id or set CLICKUP_LIST_ID")
    if not token:
        raise ClickUpSyncError(f"missing ClickUp token in environment variable {args.token_env}")

    client = ClickUpClient(token)
    views_payload = client.request("GET", f"/list/{list_id}/view")
    views = _extract_views(views_payload if isinstance(views_payload, dict) else {})

    desired = [
        (OPERATIONS_BOARD_NAME, build_operations_board_payload()),
        (FULL_QUEUE_TABLE_NAME, build_full_queue_table_payload()),
    ]

    created = 0
    skipped = 0
    for name, payload in desired:
        existing = _find_view_by_name(views, name)
        if existing is not None:
            print(f"skip: {name} already exists ({existing.get('id')})")
            skipped += 1
            continue
        print(f"create: {name}")
        if not args.dry_run:
            result = client.request("POST", f"/list/{list_id}/view", body=payload)
            view = result.get("view") if isinstance(result, dict) else None
            if isinstance(view, dict):
                print(f"  created id: {view.get('id')}")
        created += 1

    print("")
    print("Summary")
    print(f"- created: {created}")
    print(f"- skipped: {skipped}")
    print(f"- dry_run: {'yes' if args.dry_run else 'no'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ClickUpSyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
