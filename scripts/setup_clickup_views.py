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

PROFILE_CHOICES = ("system", "material")
OPERATIONS_BOARD_NAME = "글도비 운영 보드"
FULL_QUEUE_TABLE_NAME = "글도비 전체 큐"
MATERIAL_BOARD_NAME = "글도비 생산 보드"
MATERIAL_QUEUE_TABLE_NAME = "글도비 생산 큐"
MATERIAL_CANON_TABLE_NAME = "글도비 canon 큐"
MATERIAL_TR_BI_TABLE_NAME = "글도비 TR/BI 생산 큐"
MATERIAL_BI_COMPLETE_TABLE_NAME = "글도비 BI 완료 큐"
MATERIAL_EXCEPTION_TABLE_NAME = "글도비 생산 예외 큐"


def _extract_views(payload: dict[str, Any]) -> list[dict[str, Any]]:
    views = payload.get("views")
    if not isinstance(views, list):
        return []
    return [view for view in views if isinstance(view, dict)]


def _base_columns() -> dict[str, Any]:
    return {
        "fields": [
            {"field": "name", "idx": 0, "width": None, "hidden": False, "name": None, "display": None, "pinned": None},
            {
                "field": "status",
                "idx": 1,
                "width": None,
                "hidden": False,
                "name": None,
                "display": None,
                "pinned": None,
            },
            {
                "field": "assignee",
                "idx": 2,
                "width": None,
                "hidden": False,
                "name": None,
                "display": None,
                "pinned": None,
            },
            {
                "field": "priority",
                "idx": 3,
                "width": None,
                "hidden": False,
                "name": None,
                "display": None,
                "pinned": None,
            },
            {
                "field": "dueDate",
                "idx": 4,
                "width": None,
                "hidden": False,
                "name": None,
                "display": None,
                "pinned": None,
            },
        ]
    }


def build_operations_board_payload(name: str = OPERATIONS_BOARD_NAME) -> dict[str, Any]:
    return {
        "name": name,
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


def build_full_queue_table_payload(name: str = FULL_QUEUE_TABLE_NAME) -> dict[str, Any]:
    return {
        "name": name,
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


def _find_custom_field_by_name(fields: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    target = name.strip().lower()
    for field in fields:
        if str(field.get("name") or "").strip().lower() == target:
            return field
    return None


def _dropdown_option_id(field: dict[str, Any], option_name: str) -> str | None:
    type_config = field.get("type_config") if isinstance(field.get("type_config"), dict) else {}
    options = type_config.get("options") if isinstance(type_config.get("options"), list) else []
    target = option_name.strip().lower()
    for option in options:
        if not isinstance(option, dict):
            continue
        if str(option.get("name") or option.get("label") or "").strip().lower() == target:
            return str(option.get("id") or "").strip() or None
    return None


def build_material_stage_filtered_table_payload(
    material_stage_field_id: str,
    stage_value: str,
    *,
    name: str,
) -> dict[str, Any]:
    payload = build_full_queue_table_payload(name)
    payload["filters"]["fields"] = [
        {
            "field": f"cf_{material_stage_field_id}",
            "op": "EQ",
            "values": [stage_value],
        }
    ]
    return payload


def build_material_exception_table_payload(
    ops_state_field_id: str,
    normal_option_id: str,
    *,
    name: str = MATERIAL_EXCEPTION_TABLE_NAME,
) -> dict[str, Any]:
    payload = build_full_queue_table_payload(name)
    payload["filters"]["fields"] = [
        {
            "field": f"cf_{ops_state_field_id}",
            "op": "NOT",
            "values": [normal_option_id],
        }
    ]
    return payload


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
        "--profile",
        choices=PROFILE_CHOICES,
        default=os.environ.get("CLICKUP_VIEW_PROFILE", "system").strip().lower() or "system",
        help="Create system-queue views or material-side production views.",
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
    fields = client.get_list_custom_fields(list_id) if args.profile == "material" else []

    if args.profile == "material":
        desired = [
            (MATERIAL_BOARD_NAME, build_operations_board_payload(MATERIAL_BOARD_NAME)),
            (MATERIAL_QUEUE_TABLE_NAME, build_full_queue_table_payload(MATERIAL_QUEUE_TABLE_NAME)),
        ]
        material_stage_field = _find_custom_field_by_name(fields, "Material Stage")
        ops_state_field = _find_custom_field_by_name(fields, "Ops State")
        if material_stage_field is not None:
            material_stage_field_id = str(material_stage_field.get("id") or "").strip()
            if material_stage_field_id:
                desired.extend(
                    [
                        (
                            MATERIAL_CANON_TABLE_NAME,
                            build_material_stage_filtered_table_payload(
                                material_stage_field_id,
                                "canon 단계",
                                name=MATERIAL_CANON_TABLE_NAME,
                            ),
                        ),
                        (
                            MATERIAL_TR_BI_TABLE_NAME,
                            build_material_stage_filtered_table_payload(
                                material_stage_field_id,
                                "TR/BI 생산 단계",
                                name=MATERIAL_TR_BI_TABLE_NAME,
                            ),
                        ),
                        (
                            MATERIAL_BI_COMPLETE_TABLE_NAME,
                            build_material_stage_filtered_table_payload(
                                material_stage_field_id,
                                "BI 생산 완료",
                                name=MATERIAL_BI_COMPLETE_TABLE_NAME,
                            ),
                        ),
                    ]
                )
        if ops_state_field is not None:
            ops_state_field_id = str(ops_state_field.get("id") or "").strip()
            normal_option_id = _dropdown_option_id(ops_state_field, "normal")
            if ops_state_field_id and normal_option_id:
                desired.append(
                    (
                        MATERIAL_EXCEPTION_TABLE_NAME,
                        build_material_exception_table_payload(ops_state_field_id, normal_option_id),
                    )
                )
    else:
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
    print(f"- profile: {args.profile}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ClickUpSyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
