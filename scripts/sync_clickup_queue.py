"""Sync the repo-side temp execution queue into a ClickUp List.

This is intentionally one-way:
repo queue artifacts -> ClickUp visualization

ClickUp is treated as an operator-facing planning board, not as SSOT.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, parse, request

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE_STATE_PATH = ROOT / "docs" / "temp" / "queue-state.json"
DEFAULT_STATE_PATH = ROOT / "docs" / "temp" / "clickup-sync-state.json"
DEFAULT_CLICKUP_ENV_PATH = ROOT / "secrets" / "clickup.env"
CLICKUP_BASE_URL = "https://api.clickup.com/api/v2"
SYNC_MARKER_PREFIX = "<!-- geuldobi-clickup-sync:"
SYNC_STATE_VERSION = "clickup-queue-sync-v1"
PROOF_PENDING_MARKERS = (
    "verification-pending",
    "fresh-rerun-pending",
    "fresh rerun remains pending",
    "fresh rerun still pending",
    "fresh rerun validation",
    "runtime proof remains deferred",
    "fresh proof remains deferred",
    "fresh canary/live proof remains deferred",
    "canary/live proof remains deferred",
    "closure still waits on a fresh rerun",
    "closure still requires a completed rerun",
    "minimal merged proof wave",
    "merged proof wave",
)


class ClickUpSyncError(RuntimeError):
    """Raised when the sync cannot proceed safely."""


@dataclass(slots=True)
class QueueItem:
    topic: str
    temp_path: str
    canonical_path: str
    status: str
    queue_role: str
    roadmap_rank: int | None
    depends_on: list[str]
    mirror_present: bool
    canonical_present: bool


def _load_dotenv_if_available() -> None:
    if load_dotenv is None:
        return
    repo_env = ROOT / ".env"
    if repo_env.exists():
        load_dotenv(repo_env, override=False)
    clickup_env_override = os.environ.get("CLICKUP_ENV_FILE", "").strip()
    clickup_env_path = Path(clickup_env_override).expanduser() if clickup_env_override else DEFAULT_CLICKUP_ENV_PATH
    if clickup_env_path.exists():
        load_dotenv(clickup_env_path, override=True)
    load_dotenv(override=False)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _normalize_name(value: str) -> str:
    return " ".join(_stringify(value).strip().lower().replace("_", " ").split())


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _display_repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _infer_subsystem(item: QueueItem) -> str:
    topic = item.topic.lower()
    if "desktop" in topic:
        return "desktop"
    if "bridge" in topic:
        return "bridge"
    if "control" in topic:
        return "control-plane"
    if topic.startswith("stage0") or "stage0" in topic:
        return "stage0"
    if "stage2" in topic:
        return "stage2"
    if "stage3" in topic:
        return "stage3"
    if "stage4" in topic:
        return "stage4"
    if "test" in topic or "pytest" in topic:
        return "tests"
    return "ops"


def _infer_work_type(item: QueueItem) -> str:
    topic = item.topic.lower()
    if "canary" in topic or "proof" in topic or "soak" in topic:
        return "proof"
    if item.canonical_path.endswith("-execution-ssot.md"):
        return "execution"
    if "survey" in item.canonical_path or "audit" in item.canonical_path:
        return "survey"
    return "ops"


def _canonical_doc_path(item: QueueItem) -> Path | None:
    raw_path = _stringify(item.canonical_path).strip()
    if not raw_path:
        return None
    return ROOT / Path(raw_path)


def _load_canonical_doc_text(item: QueueItem) -> str:
    path = _canonical_doc_path(item)
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _looks_proof_pending(canonical_doc_text: str) -> bool:
    haystack = canonical_doc_text.lower()
    return any(marker in haystack for marker in PROOF_PENDING_MARKERS)


def _desired_clickup_status(item: QueueItem, *, canonical_doc_text: str = "") -> str:
    if item.status == "completed" or item.queue_role == "historical_backing":
        return "Closed"
    if item.status == "blocked":
        return "Blocked"
    if item.queue_role == "parked_future_wave":
        return "Parked"
    if item.status == "pending":
        return "Ready"
    if item.status == "in_progress":
        if canonical_doc_text and _looks_proof_pending(canonical_doc_text):
            return "Proof Pending"
        return "Realizing"
    return "Ready"


def _status_candidates(desired: str) -> list[str]:
    mapping = {
        "Ready": ["Ready", "To Do", "Todo", "Open", "Backlog"],
        "Realizing": ["Realizing", "In Progress", "Doing", "Active", "Working On It"],
        "Proof Pending": ["Proof Pending", "Review", "Verify", "Verification", "Testing", "QA"],
        "Blocked": ["Blocked", "Stuck", "On Hold"],
        "Parked": ["Parked", "Backlog", "Icebox", "On Hold", "To Do", "Open"],
        "Closed": ["Closed", "Done", "Complete", "Completed", "Archived"],
    }
    return mapping.get(desired, [desired])


def resolve_clickup_status_name(
    desired_status: str,
    available_statuses: list[str],
    explicit_map: dict[str, str] | None = None,
) -> str | None:
    explicit_map = explicit_map or {}
    if desired_status in explicit_map:
        return explicit_map[desired_status]
    if not available_statuses:
        return None

    normalized_to_actual = {_normalize_name(name): name for name in available_statuses}

    exact = normalized_to_actual.get(_normalize_name(desired_status))
    if exact:
        return exact

    for candidate in _status_candidates(desired_status):
        match = normalized_to_actual.get(_normalize_name(candidate))
        if match:
            return match

    return None


def build_task_markdown(
    item: QueueItem,
    *,
    queue_state_path: Path,
    work_type: str,
    subsystem: str,
    desired_status: str,
) -> str:
    lines = [
        f"{SYNC_MARKER_PREFIX} topic={item.topic} -->",
        "# Geuldobi Queue Mirror",
        "",
        "This task is a one-way mirror of the repo-side execution queue.",
        "",
        "## Current State",
        f"- Topic: `{item.topic}`",
        f"- Repo status: `{item.status}`",
        f"- Queue role: `{item.queue_role}`",
        f"- Desired ClickUp status: `{desired_status}`",
        f"- Roadmap rank: `{item.roadmap_rank if item.roadmap_rank is not None else '-'}`",
        f"- Work type: `{work_type}`",
        f"- Subsystem: `{subsystem}`",
        "",
        "## Source Paths",
        f"- Canonical doc: `{item.canonical_path}`",
        f"- Temp mirror: `{item.temp_path}`",
        f"- Queue state: `{_display_repo_path(queue_state_path)}`",
        f"- Roadmap: `docs/temp/execution-roadmap.md`",
        "",
        "## Guardrail",
        "- If ClickUp and the repo disagree, the repo-side canonical docs and queue artifacts win.",
    ]
    if item.depends_on:
        lines.extend(["", "## Dependencies"])
        lines.extend(f"- `{topic}`" for topic in item.depends_on)
    return "\n".join(lines).strip() + "\n"


def _extract_sync_marker(markdown: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith(SYNC_MARKER_PREFIX) and stripped.endswith("-->"):
            inner = stripped[len(SYNC_MARKER_PREFIX) : -3].strip()
            if inner.startswith("topic="):
                return inner.split("=", 1)[1].strip()
    return ""


def _extract_list_status_names(payload: dict[str, Any]) -> list[str]:
    statuses = payload.get("statuses")
    if not isinstance(statuses, list):
        return []
    names: list[str] = []
    for status in statuses:
        if not isinstance(status, dict):
            continue
        name = _stringify(status.get("status") or status.get("name")).strip()
        if name:
            names.append(name)
    return names


def _extract_task_markdown(task_payload: dict[str, Any]) -> str:
    for key in ("markdown_description", "description", "text_content"):
        value = task_payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _extract_tasks(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("tasks"), list):
        return [task for task in payload["tasks"] if isinstance(task, dict)]
    if isinstance(payload, list):
        return [task for task in payload if isinstance(task, dict)]
    return []


def _load_queue_items(queue_state_path: Path) -> tuple[dict[str, Any], list[QueueItem]]:
    payload = _read_json(queue_state_path)
    items_payload = payload.get("items")
    if not isinstance(items_payload, list):
        raise ClickUpSyncError(f"invalid queue-state payload: {queue_state_path}")
    items = [
        QueueItem(
            topic=_stringify(raw.get("topic")).strip(),
            temp_path=_stringify(raw.get("temp_path")).strip(),
            canonical_path=_stringify(raw.get("canonical_path")).strip(),
            status=_stringify(raw.get("status")).strip(),
            queue_role=_stringify(raw.get("queue_role")).strip(),
            roadmap_rank=raw.get("roadmap_rank") if isinstance(raw.get("roadmap_rank"), int) else None,
            depends_on=[_stringify(dep).strip() for dep in raw.get("depends_on") or [] if _stringify(dep).strip()],
            mirror_present=bool(raw.get("mirror_present")),
            canonical_present=bool(raw.get("canonical_present")),
        )
        for raw in items_payload
        if isinstance(raw, dict) and _stringify(raw.get("topic")).strip()
    ]
    return payload, items


class ClickUpClient:
    def __init__(self, token: str, *, base_url: str = CLICKUP_BASE_URL, timeout: int = 30) -> None:
        self._token = token.strip()
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        if not self._token:
            raise ClickUpSyncError("missing ClickUp API token")

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        if query:
            encoded = parse.urlencode([(key, value) for key, value in query.items() if value is not None], doseq=True)
            if encoded:
                url = f"{url}?{encoded}"
        data = None
        headers = {
            "Authorization": self._token,
            "Content-Type": "application/json",
        }
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, method=method.upper(), headers=headers, data=data)
        try:
            with request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise ClickUpSyncError(
                f"ClickUp API {method.upper()} {path} failed with {exc.code}: {details}"
            ) from exc
        except error.URLError as exc:
            raise ClickUpSyncError(f"ClickUp API {method.upper()} {path} network failure: {exc}") from exc

        if not raw.strip():
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    def get_list(self, list_id: str) -> dict[str, Any]:
        payload = self.request("GET", f"/list/{list_id}")
        if not isinstance(payload, dict):
            raise ClickUpSyncError("unexpected ClickUp list payload")
        return payload

    def get_list_custom_fields(self, list_id: str) -> list[dict[str, Any]]:
        payload = self.request("GET", f"/list/{list_id}/field")
        if isinstance(payload, dict):
            if isinstance(payload.get("fields"), list):
                return [field for field in payload["fields"] if isinstance(field, dict)]
            if isinstance(payload.get("custom_fields"), list):
                return [field for field in payload["custom_fields"] if isinstance(field, dict)]
        if isinstance(payload, list):
            return [field for field in payload if isinstance(field, dict)]
        return []

    def list_tasks(self, list_id: str) -> list[dict[str, Any]]:
        tasks: list[dict[str, Any]] = []
        page = 0
        while True:
            payload = self.request(
                "GET",
                f"/list/{list_id}/task",
                query={
                    "page": page,
                    "include_closed": "true",
                    "subtasks": "true",
                    "include_markdown_description": "true",
                },
            )
            batch = _extract_tasks(payload)
            tasks.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return tasks

    def create_task(self, list_id: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = self.request("POST", f"/list/{list_id}/task", body=body)
        if not isinstance(payload, dict):
            raise ClickUpSyncError("unexpected create-task response")
        return payload

    def update_task(self, task_id: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = self.request("PUT", f"/task/{task_id}", body=body)
        if not isinstance(payload, dict):
            raise ClickUpSyncError("unexpected update-task response")
        return payload

    def set_custom_field_value(self, task_id: str, field_id: str, body: dict[str, Any]) -> None:
        self.request("POST", f"/task/{task_id}/field/{field_id}", body=body)


def _resolve_field_value_payload(field: dict[str, Any], value: Any) -> dict[str, Any] | None:
    field_type = _stringify(field.get("type")).strip()
    field_name = _stringify(field.get("name")).strip() or _stringify(field.get("id")).strip()
    if value is None or value == "":
        return None

    if field_type in {"text", "short_text", "url", "email", "phone"}:
        return {"value": _stringify(value)}
    if field_type == "number":
        return {"value": int(value)}
    if field_type == "checkbox":
        return {"value": bool(value)}

    type_config = field.get("type_config") if isinstance(field.get("type_config"), dict) else {}
    options = type_config.get("options") if isinstance(type_config.get("options"), list) else []

    if field_type == "drop_down":
        target = _normalize_name(_stringify(value))
        for option in options:
            if not isinstance(option, dict):
                continue
            option_name = _stringify(option.get("name") or option.get("label"))
            if _normalize_name(option_name) == target:
                return {"value": _stringify(option.get("id"))}
        raise ClickUpSyncError(f"dropdown field '{field_name}' has no option matching '{value}'")

    if field_type == "labels":
        raw_values = value if isinstance(value, list) else [value]
        normalized_targets = {_normalize_name(_stringify(entry)) for entry in raw_values if _stringify(entry).strip()}
        option_ids: list[str] = []
        for option in options:
            if not isinstance(option, dict):
                continue
            option_name = _stringify(option.get("label") or option.get("name"))
            if _normalize_name(option_name) in normalized_targets:
                option_ids.append(_stringify(option.get("id")))
        missing = normalized_targets - {
            _normalize_name(_stringify(option.get("label") or option.get("name")))
            for option in options
            if isinstance(option, dict)
        }
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ClickUpSyncError(f"labels field '{field_name}' has no options matching: {missing_list}")
        return {"value": option_ids}

    return None


def _collect_field_values(item: QueueItem) -> dict[str, Any]:
    return {
        "Canonical Path": item.canonical_path,
        "Temp Mirror Path": item.temp_path,
        "Work Type": _infer_work_type(item),
        "Subsystem": _infer_subsystem(item),
        "Roadmap Rank": item.roadmap_rank,
        "Queue Role": item.queue_role,
    }


def _load_explicit_status_map() -> dict[str, str]:
    raw = os.environ.get("CLICKUP_STATUS_MAP_JSON", "").strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ClickUpSyncError("CLICKUP_STATUS_MAP_JSON must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ClickUpSyncError("CLICKUP_STATUS_MAP_JSON must be a JSON object")
    return {
        _stringify(key).strip(): _stringify(value).strip()
        for key, value in payload.items()
        if _stringify(key).strip() and _stringify(value).strip()
    }


def _load_sync_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "version": SYNC_STATE_VERSION,
            "updated_at": "",
            "list_id": "",
            "tasks": {},
        }
    payload = _read_json(path)
    if not isinstance(payload, dict):
        return {"version": SYNC_STATE_VERSION, "updated_at": "", "list_id": "", "tasks": {}}
    if not isinstance(payload.get("tasks"), dict):
        payload["tasks"] = {}
    return payload


def _build_task_body(
    item: QueueItem,
    *,
    queue_state_path: Path,
    status_name: str | None,
) -> dict[str, Any]:
    work_type = _infer_work_type(item)
    subsystem = _infer_subsystem(item)
    canonical_doc_text = _load_canonical_doc_text(item)
    desired_status = _desired_clickup_status(item, canonical_doc_text=canonical_doc_text)
    body: dict[str, Any] = {
        "name": item.topic,
        "markdown_content": build_task_markdown(
            item,
            queue_state_path=queue_state_path,
            work_type=work_type,
            subsystem=subsystem,
            desired_status=desired_status,
        ),
    }
    if status_name:
        body["status"] = status_name
    return body


def _sync_item_custom_fields(
    client: ClickUpClient,
    *,
    task_id: str,
    item: QueueItem,
    fields_by_name: dict[str, dict[str, Any]],
    dry_run: bool,
) -> list[str]:
    messages: list[str] = []
    for field_name, value in _collect_field_values(item).items():
        field = fields_by_name.get(_normalize_name(field_name))
        if field is None:
            continue
        field_id = _stringify(field.get("id")).strip()
        if not field_id:
            continue
        payload = _resolve_field_value_payload(field, value)
        if payload is None:
            continue
        messages.append(f"set field '{field_name}'")
        if not dry_run:
            client.set_custom_field_value(task_id, field_id, payload)
    return messages


def _print_list_inspection(list_payload: dict[str, Any], fields: list[dict[str, Any]]) -> None:
    status_names = _extract_list_status_names(list_payload)
    print("List inspection")
    print(f"- Name: {_stringify(list_payload.get('name')).strip() or '(unknown)'}")
    print(f"- ID: {_stringify(list_payload.get('id')).strip() or '(unknown)'}")
    print("- Available statuses:")
    if status_names:
        for name in status_names:
            print(f"  - {name}")
    else:
        print("  - (none surfaced by API response)")
    print("- Accessible custom fields:")
    if fields:
        for field in fields:
            print(f"  - {_stringify(field.get('name'))} [{_stringify(field.get('type'))}]")
    else:
        print("  - (none)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queue-state-path",
        type=Path,
        default=DEFAULT_QUEUE_STATE_PATH,
        help="Path to the repo-side queue-state.json payload.",
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="Local sync-state file used to remember ClickUp task IDs.",
    )
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
        help="Print planned changes without creating or updating ClickUp tasks.",
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
        help="Only sync the first N queue items.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    _load_dotenv_if_available()
    parser = build_parser()
    args = parser.parse_args(argv)

    queue_state_path = args.queue_state_path.resolve()
    state_path = args.state_path.resolve()
    list_id = _stringify(args.list_id).strip()
    token = os.environ.get(args.token_env, "").strip()

    if not queue_state_path.exists():
        raise ClickUpSyncError(f"queue-state file not found: {queue_state_path}")
    if not list_id:
        raise ClickUpSyncError("missing ClickUp list ID; pass --list-id or set CLICKUP_LIST_ID")
    if not token:
        raise ClickUpSyncError(f"missing ClickUp token in environment variable {args.token_env}")

    _, queue_items = _load_queue_items(queue_state_path)
    if args.limit is not None:
        queue_items = queue_items[: max(0, int(args.limit))]

    client = ClickUpClient(token)
    list_payload = client.get_list(list_id)
    fields = client.get_list_custom_fields(list_id)
    if args.inspect_list:
        _print_list_inspection(list_payload, fields)
        return 0

    explicit_status_map = _load_explicit_status_map()
    available_statuses = _extract_list_status_names(list_payload)
    fields_by_name = {
        _normalize_name(_stringify(field.get("name"))): field
        for field in fields
        if _stringify(field.get("name")).strip()
    }
    existing_tasks = client.list_tasks(list_id)
    tasks_by_name = {
        _stringify(task.get("name")).strip(): task
        for task in existing_tasks
        if _stringify(task.get("name")).strip()
    }
    tasks_by_id = {
        _stringify(task.get("id")).strip(): task
        for task in existing_tasks
        if _stringify(task.get("id")).strip()
    }
    tasks_by_marker = {
        marker: task
        for task in existing_tasks
        for marker in [_extract_sync_marker(_extract_task_markdown(task))]
        if marker
    }

    state = _load_sync_state(state_path)
    synced_tasks: dict[str, Any] = {}
    created_count = 0
    updated_count = 0

    for item in queue_items:
        canonical_doc_text = _load_canonical_doc_text(item)
        desired_status = _desired_clickup_status(item, canonical_doc_text=canonical_doc_text)
        status_name = resolve_clickup_status_name(desired_status, available_statuses, explicit_status_map)
        task_body = _build_task_body(item, queue_state_path=queue_state_path, status_name=status_name)

        remembered = state.get("tasks", {}).get(item.topic, {})
        remembered_id = _stringify(remembered.get("task_id")).strip()
        existing_task = tasks_by_marker.get(item.topic) or tasks_by_name.get(item.topic)
        if existing_task is None and remembered_id and remembered_id in tasks_by_id:
            existing_task = tasks_by_id[remembered_id]
        task_id = _stringify(existing_task.get("id") if isinstance(existing_task, dict) else "").strip()

        field_messages: list[str] = []
        if task_id:
            print(f"update: {item.topic}")
            if not args.dry_run:
                client.update_task(task_id, task_body)
            field_messages = _sync_item_custom_fields(
                client,
                task_id=task_id,
                item=item,
                fields_by_name=fields_by_name,
                dry_run=args.dry_run,
            )
            updated_count += 1
        else:
            print(f"create: {item.topic}")
            created_payload: dict[str, Any] = {}
            if not args.dry_run:
                created_payload = client.create_task(list_id, task_body)
                task_id = _stringify(created_payload.get("id")).strip()
            else:
                task_id = f"dry-run:{item.topic}"
            if task_id:
                field_messages = _sync_item_custom_fields(
                    client,
                    task_id=task_id,
                    item=item,
                    fields_by_name=fields_by_name,
                    dry_run=args.dry_run,
                )
            created_count += 1

        if status_name is None:
            print(f"  warning: no ClickUp status match for desired status '{desired_status}'")
        if field_messages:
            print(f"  fields: {', '.join(field_messages)}")

        synced_tasks[item.topic] = {
            "task_id": task_id,
            "name": item.topic,
            "desired_status": desired_status,
            "resolved_status": status_name or "",
            "synced_at": _utc_now(),
        }

    next_state = {
        "version": SYNC_STATE_VERSION,
        "updated_at": _utc_now(),
        "list_id": list_id,
        "queue_state_path": queue_state_path.relative_to(ROOT).as_posix(),
        "tasks": synced_tasks,
    }
    if not args.dry_run:
        _write_json(state_path, next_state)

    print("")
    print("Summary")
    print(f"- items considered: {len(queue_items)}")
    print(f"- created: {created_count}")
    print(f"- updated: {updated_count}")
    print(f"- dry_run: {'yes' if args.dry_run else 'no'}")
    print(f"- sync state path: {state_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ClickUpSyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
