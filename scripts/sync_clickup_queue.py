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
SYNC_PROFILE_CHOICES = ("system", "material")
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
    material_stage: str = ""


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


def _korean_work_type(work_type: str) -> str:
    mapping = {
        "execution": "실행",
        "proof": "증빙",
        "survey": "조사",
        "ops": "운영",
    }
    return mapping.get(work_type, work_type)


def _korean_subsystem(subsystem: str) -> str:
    mapping = {
        "stage0": "Stage0",
        "stage2": "Stage2",
        "stage3": "Stage3",
        "stage4": "Stage4",
        "desktop": "Desktop",
        "bridge": "Bridge",
        "control-plane": "Control Plane",
        "tests": "Tests",
        "ops": "Ops",
    }
    return mapping.get(subsystem, subsystem)


def _queue_role_summary(queue_role: str) -> str:
    mapping = {
        "front_active": "현재 실행 큐에서 추적 중인 활성 항목입니다.",
        "blocked_holding": "선행 항목이 정리될 때까지 멈춰 둔 보류 항목입니다.",
        "parked_future_wave": "지금은 우선순위를 낮춰 다음 wave로 미뤄 둔 항목입니다.",
        "historical_backing": "현재 실행 대상은 아니고, 과거 근거를 남겨 두는 참고 항목입니다.",
    }
    return mapping.get(queue_role, "현재 큐에서 추적 중인 항목입니다.")


def _status_summary(desired_status: str) -> str:
    mapping = {
        "Ready": "선행 조건만 맞으면 바로 진행할 수 있는 준비 상태입니다.",
        "Realizing": "현재는 문서 기준 realization/정리 작업이 진행 중입니다.",
        "Proof Pending": "지금은 추가 코드보다 fresh proof wave나 rerun으로 runtime truth를 다시 확인하는 단계입니다.",
        "Blocked": "선행 의존성이 풀리기 전까지는 바로 진행할 수 없습니다.",
        "Parked": "지금은 우선순위를 잠시 내리고 보류 중입니다.",
        "Closed": "현재는 닫힌 참고 항목이며, 직접 실행보다는 회고/근거 보존에 가깝습니다.",
    }
    return mapping.get(desired_status, "현재 상태를 다시 확인 중입니다.")


def _next_action_summary(item: QueueItem, desired_status: str) -> str:
    if desired_status == "Proof Pending":
        return "repo 쪽 canonical 문서와 run 결과를 기준으로 proof wave를 확인한 뒤 상태를 다시 반영합니다."
    if desired_status == "Realizing":
        return "로드맵 순서대로 현재 bounded tranche를 계속 진행합니다."
    if desired_status == "Ready":
        return "선행 항목 정리 후 바로 이 항목을 큐 순서대로 이어갑니다."
    if desired_status == "Blocked":
        if item.depends_on:
            depends = ", ".join(item.depends_on)
            return f"선행 항목({depends})이 정리되면 다시 활성화합니다."
        return "선행 의존성이 풀리면 다시 활성화합니다."
    if desired_status == "Parked":
        return "상위 proof/실행 항목이 끝난 뒤 필요 시 다시 활성화합니다."
    return "repo 쪽 canonical 문서를 기준으로만 상태를 갱신합니다."


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
    normalized_to_actual = {_normalize_name(name): name for name in available_statuses}
    if desired_status in explicit_map:
        explicit_target = explicit_map[desired_status]
        explicit_match = normalized_to_actual.get(_normalize_name(explicit_target))
        if explicit_match:
            return explicit_match
    if not available_statuses:
        return None

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
    profile: str = "system",
) -> str:
    if profile == "material":
        return _build_material_task_markdown(
            item,
            queue_state_path=queue_state_path,
            desired_status=desired_status,
        )

    rank_display = item.roadmap_rank if item.roadmap_rank is not None else "-"
    lines = [
        f"{SYNC_MARKER_PREFIX} topic={item.topic} -->",
        "# 글도비 실행 큐 미러",
        "",
        "이 카드는 저장소 실행 큐를 ClickUp에 비춘 읽기 전용 미러입니다.",
        "",
        "## 운영 요약",
        f"- 한줄 요약: `{_korean_subsystem(subsystem)}` `{_korean_work_type(work_type)}` 항목이며, 현재 로드맵 순위는 `{rank_display}`번입니다.",
        f"- 큐 해석: {_queue_role_summary(item.queue_role)}",
        f"- 현재 판단: {_status_summary(desired_status)}",
        f"- 다음 액션: {_next_action_summary(item, desired_status)}",
        "",
        "## 현재 상태",
        f"- Topic: `{item.topic}`",
        f"- Repo status: `{item.status}`",
        f"- Queue role: `{item.queue_role}`",
        f"- Desired ClickUp status: `{desired_status}`",
        f"- Roadmap rank: `{rank_display}`",
        f"- Work type: `{work_type}`",
        f"- Subsystem: `{subsystem}`",
        "",
        "## 소스 경로",
        f"- Canonical doc: `{item.canonical_path}`",
        f"- Temp mirror: `{item.temp_path}`",
        f"- Queue state: `{_display_repo_path(queue_state_path)}`",
        "- Roadmap: `docs/temp/execution-roadmap.md`",
        "",
        "## 가드레일",
        "- ClickUp과 저장소 내용이 다르면, 저장소 쪽 canonical 문서와 queue artifact가 우선입니다.",
    ]
    if item.depends_on:
        lines.extend(["", "## 선행 항목"])
        lines.extend(f"- `{topic}`" for topic in item.depends_on)
    return "\n".join(lines).strip() + "\n"


def _load_material_status_snapshot(item: QueueItem) -> dict[str, Any]:
    raw_path = _stringify(item.temp_path).strip()
    if not raw_path:
        return {}
    path = ROOT / Path(raw_path)
    if not path.is_file():
        return {}
    payload = _read_json(path)
    return payload if isinstance(payload, dict) else {}


def _material_next_action(snapshot: dict[str, Any]) -> str:
    next_unit_type = _stringify(snapshot.get("next_unit_type")).strip().lower()
    if next_unit_type == "complete":
        return "현재 생산 단위는 닫혀 있습니다. fresh inconsistency가 없으면 재개하지 않습니다."
    if next_unit_type == "bi_handoff":
        return "다음 법적 단위는 BI 생성/감리 handoff입니다."
    if next_unit_type == "ten_block_audit":
        return "다음 법적 단위는 ten-block audit입니다."
    if next_unit_type == "merge":
        return "다음 법적 단위는 bounded merge/rebuild입니다."
    if next_unit_type == "block":
        next_block_id = _stringify(snapshot.get("next_block_id")).strip() or "(unspecified)"
        return f"다음 법적 단위는 `{next_block_id}` 블록 continuation입니다."
    return "현재 current-truth 문서와 sequential status를 함께 다시 읽고 다음 합법 단위를 확인합니다."


def _material_snapshot_defaults(item: QueueItem, snapshot: dict[str, Any]) -> dict[str, Any]:
    next_unit_type = _stringify(snapshot.get("next_unit_type")).strip()
    resume_basis = _stringify(snapshot.get("resume_basis")).strip()
    production_complete = bool(snapshot.get("production_complete"))
    bi_complete = bool(snapshot.get("bi_complete"))
    if not snapshot and item.material_stage == "bi_production_complete":
        next_unit_type = "complete"
        resume_basis = "registry_deployable_live_pair"
        production_complete = True
        bi_complete = True
    elif not snapshot and item.material_stage == "canon_stage":
        next_unit_type = "canon_stage"
        resume_basis = "canon_pitch_anchor"
    elif not snapshot and item.material_stage:
        next_unit_type = item.material_stage
    return {
        "work_id": _stringify(snapshot.get("work_id")).strip() or item.topic,
        "material_stage": _material_stage_summary(item, snapshot),
        "next_unit_type": next_unit_type or "(unknown)",
        "next_block_id": _stringify(snapshot.get("next_block_id")).strip() or "-",
        "last_pass_display": snapshot.get("last_sequential_block_pass")
        if isinstance(snapshot.get("last_sequential_block_pass"), int)
        else "-",
        "resume_basis": resume_basis or "-",
        "production_complete": production_complete,
        "bi_complete": bi_complete,
        "updated_at": _stringify(snapshot.get("updated_at")).strip() or "-",
    }


def _material_stage_summary(item: QueueItem, snapshot: dict[str, Any]) -> str:
    stage = _stringify(item.material_stage).strip() or ""
    if stage == "canon_stage":
        return "canon 단계"
    if stage == "tr_or_bi_production":
        return "TR/BI 생산 단계"
    if stage == "bi_production_complete":
        return "BI 생산 완료"
    next_unit_type = _stringify(snapshot.get("next_unit_type")).strip().lower()
    if next_unit_type == "complete":
        return "BI 생산 완료"
    if next_unit_type:
        return "TR/BI 생산 단계"
    return "canon 단계"


def _material_ops_state(item: QueueItem, snapshot: dict[str, Any]) -> str:
    explicit = _stringify(snapshot.get("ops_state")).strip().lower()
    if explicit in {"normal", "repair", "blocked", "parked"}:
        return explicit

    status = _stringify(item.status).strip().lower()
    queue_role = _stringify(item.queue_role).strip().lower()
    next_unit_type = _stringify(snapshot.get("next_unit_type")).strip().lower()

    if status == "blocked" or queue_role == "blocked_holding":
        return "blocked"
    if queue_role == "parked_future_wave":
        return "parked"
    if status == "repair" or queue_role == "repair_active" or next_unit_type == "repair":
        return "repair"
    return "normal"


def _build_material_task_markdown(
    item: QueueItem,
    *,
    queue_state_path: Path,
    desired_status: str,
) -> str:
    snapshot = _load_material_status_snapshot(item)
    view = _material_snapshot_defaults(item, snapshot)
    lines = [
        f"{SYNC_MARKER_PREFIX} topic={item.topic} -->",
        "# 글도비 재료 사이드 생산 스케줄 미러",
        "",
        "이 카드는 재료 사이드 current-truth를 ClickUp 생산 스케줄에 비춘 읽기 전용 미러입니다.",
        "",
        "## 운영 요약",
        (f"- 한줄 요약: `{view['work_id']}` 현재 material stage는 `{view['material_stage']}`입니다."),
        f"- 현재 판단: {_status_summary(desired_status)}",
        f"- 다음 액션: {_material_next_action({'next_unit_type': view['next_unit_type'], 'next_block_id': view['next_block_id']})}",
        "",
        "## 현재 상태",
        f"- Work ID: `{view['work_id']}`",
        f"- Material stage: `{view['material_stage']}`",
        f"- Repo status: `{item.status}`",
        f"- Desired ClickUp status: `{desired_status}`",
        f"- Last sequential block pass: `{view['last_pass_display']}`",
        f"- Next unit type: `{view['next_unit_type']}`",
        f"- Next block id: `{view['next_block_id']}`",
        f"- Resume basis: `{view['resume_basis']}`",
        f"- Production complete: `{str(view['production_complete']).lower()}`",
        f"- BI complete: `{str(view['bi_complete']).lower()}`",
        f"- Updated at: `{view['updated_at']}`",
        "",
        "## 소스 경로",
        f"- Current truth: `{item.canonical_path}`",
        f"- Sequential status: `{item.temp_path}`",
        f"- Queue state: `{_display_repo_path(queue_state_path)}`",
        "",
        "## 가드레일",
        "- ClickUp과 저장소 내용이 다르면, 재료 사이드 current-truth와 live artifact가 우선입니다.",
    ]
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
            material_stage=_stringify(raw.get("material_stage")).strip(),
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
            raise ClickUpSyncError(f"ClickUp API {method.upper()} {path} failed with {exc.code}: {details}") from exc
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


def _collect_material_field_values(item: QueueItem) -> dict[str, Any]:
    snapshot = _load_material_status_snapshot(item)
    view = _material_snapshot_defaults(item, snapshot)
    ops_state = _material_ops_state(item, snapshot)
    return {
        "Work ID": view["work_id"],
        "Material Stage": view["material_stage"],
        "Ops State": ops_state,
        "Current Truth Path": item.canonical_path,
        "Sequential Status Path": item.temp_path,
        "Next Unit Type": view["next_unit_type"],
        "Last Sequential Block Pass": snapshot.get("last_sequential_block_pass"),
        "Next Block ID": _stringify(snapshot.get("next_block_id")).strip(),
        "Resume Basis": view["resume_basis"] if view["resume_basis"] != "-" else "",
        "Production Complete": view["production_complete"],
        "BI Complete": view["bi_complete"],
        "Updated At": _stringify(snapshot.get("updated_at")).strip(),
    }


def _load_explicit_status_map(profile: str = "system") -> dict[str, str]:
    profile_env = f"CLICKUP_{profile.upper()}_STATUS_MAP_JSON"
    raw = os.environ.get(profile_env, "").strip()
    if not raw:
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
    profile: str = "system",
    include_status: bool = True,
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
            profile=profile,
        ),
    }
    if status_name and include_status:
        body["status"] = status_name
    return body


def _sync_item_custom_fields(
    client: ClickUpClient,
    *,
    task_id: str,
    item: QueueItem,
    fields_by_name: dict[str, dict[str, Any]],
    dry_run: bool,
    profile: str = "system",
) -> list[str]:
    messages: list[str] = []
    field_values = _collect_material_field_values(item) if profile == "material" else _collect_field_values(item)
    for field_name, value in field_values.items():
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
        "--profile",
        choices=SYNC_PROFILE_CHOICES,
        default=os.environ.get("CLICKUP_SYNC_PROFILE", "system").strip().lower() or "system",
        help="Render the ClickUp mirror for the system queue or the material-side production queue.",
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

    explicit_status_map = _load_explicit_status_map(args.profile)
    available_statuses = _extract_list_status_names(list_payload)
    fields_by_name = {
        _normalize_name(_stringify(field.get("name"))): field
        for field in fields
        if _stringify(field.get("name")).strip()
    }
    existing_tasks = client.list_tasks(list_id)
    tasks_by_name = {
        _stringify(task.get("name")).strip(): task for task in existing_tasks if _stringify(task.get("name")).strip()
    }
    tasks_by_id = {
        _stringify(task.get("id")).strip(): task for task in existing_tasks if _stringify(task.get("id")).strip()
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
        task_body = _build_task_body(
            item,
            queue_state_path=queue_state_path,
            status_name=status_name,
            profile=args.profile,
        )

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
                try:
                    client.update_task(task_id, task_body)
                except ClickUpSyncError as exc:
                    if status_name and ("Status not found" in str(exc) or "Status does not exist" in str(exc)):
                        retry_body = _build_task_body(
                            item,
                            queue_state_path=queue_state_path,
                            status_name=status_name,
                            profile=args.profile,
                            include_status=False,
                        )
                        print("  retry: update without explicit status")
                        client.update_task(task_id, retry_body)
                    else:
                        raise
            field_messages = _sync_item_custom_fields(
                client,
                task_id=task_id,
                item=item,
                fields_by_name=fields_by_name,
                dry_run=args.dry_run,
                profile=args.profile,
            )
            updated_count += 1
        else:
            print(f"create: {item.topic}")
            created_payload: dict[str, Any] = {}
            if not args.dry_run:
                try:
                    created_payload = client.create_task(list_id, task_body)
                except ClickUpSyncError as exc:
                    if status_name and "Status not found" in str(exc):
                        retry_body = _build_task_body(
                            item,
                            queue_state_path=queue_state_path,
                            status_name=status_name,
                            profile=args.profile,
                            include_status=False,
                        )
                        print("  retry: create without explicit status")
                        created_payload = client.create_task(list_id, retry_body)
                    else:
                        raise
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
                    profile=args.profile,
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
    print(f"- profile: {args.profile}")
    print(f"- sync state path: {state_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ClickUpSyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
