from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMP = ROOT / "docs" / "temp"
META_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9 /_-]*):(?:\s*(?P<value>.+?)\s*)?$")
WORKING_ORDER_RE = re.compile(r"^(?P<rank>\d+)\.\s+`(?P<topic>[^`]+)`(?:\s+\((?P<note>.+)\))?$")
EXECUTION_META_HEADING = "## 0. Execution Metadata Block"
EXECUTION_META_SCHEMA_VERSION = "execution-meta-block-v1"

QUEUE_ROLE_FRONT_ACTIVE = "front_active"
QUEUE_ROLE_BLOCKED_HOLDING = "blocked_holding"
QUEUE_ROLE_PARKED_FUTURE_WAVE = "parked_future_wave"
QUEUE_ROLE_HISTORICAL_BACKING = "historical_backing"

HISTORICAL_ROLE_MARKERS = (
    "historical backing",
    "historical backing only",
    "retained only as historical backing",
    "runtime-positive substrate",
    "runtime-positive substrate lane",
    "runtime-positive substrate/reference seam",
    "no longer active queue work",
    "utility lane",
    "reference seam",
)
PARKED_ROLE_MARKERS = (
    "parked",
    "future wave",
    "stay parked",
    "context-only future wave",
    "soak lane",
)


def normalize_relpath(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().strip("`").replace("\\", "/")
    if not cleaned:
        return None
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def describe_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def write_utf8_lf(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def parse_metadata(path: Path, line_limit: int = 40) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[:line_limit]:
        match = META_RE.match(line)
        if not match:
            continue
        key = match.group("key").strip().lower().replace(" ", "_")
        metadata[key] = (match.group("value") or "").strip()
    return metadata


def _extract_first_yaml_fence_under_execution_meta_heading(path: Path) -> str | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    index = 0

    while index < len(lines):
        stripped = lines[index].strip()
        if not in_section:
            if stripped == EXECUTION_META_HEADING:
                in_section = True
            index += 1
            continue

        if stripped.startswith("## "):
            return None
        if not stripped:
            index += 1
            continue
        if not stripped.startswith("```"):
            index += 1
            continue

        fence_lang = stripped[3:].strip().lower()
        if fence_lang not in {"yaml", "yml"}:
            raise ValueError(
                f"{describe_path(path)}: first fenced block under '{EXECUTION_META_HEADING}' must be yaml"
            )

        index += 1
        block_lines: list[str] = []
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped == "```":
                return "\n".join(block_lines)
            block_lines.append(lines[index])
            index += 1
        raise ValueError(
            f"{describe_path(path)}: execution metadata block is missing a closing fence"
        )

    return None


def load_execution_meta_block(path: Path, expected_topic: str | None = None) -> dict[str, object] | None:
    raw_block = _extract_first_yaml_fence_under_execution_meta_heading(path)
    if raw_block is None:
        return None

    try:
        parsed = yaml.safe_load(raw_block)
    except yaml.YAMLError as exc:
        raise ValueError(f"{describe_path(path)}: invalid execution metadata YAML ({exc})") from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"{describe_path(path)}: execution metadata block must decode to an object")

    execution_meta = parsed.get("execution_meta")
    if not isinstance(execution_meta, dict):
        raise ValueError(
            f"{describe_path(path)}: execution metadata block must contain an 'execution_meta' object"
        )

    schema_version = execution_meta.get("schema_version")
    if schema_version != EXECUTION_META_SCHEMA_VERSION:
        raise ValueError(
            f"{describe_path(path)}: execution_meta.schema_version must be {EXECUTION_META_SCHEMA_VERSION}"
        )

    topic = execution_meta.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError(f"{describe_path(path)}: execution_meta.topic must be a non-empty string")
    topic = topic.strip()
    if expected_topic is not None and topic != expected_topic:
        raise ValueError(
            f"{describe_path(path)}: execution_meta.topic={topic} does not match expected topic {expected_topic}"
        )

    depends_on = execution_meta.get("depends_on")
    if not isinstance(depends_on, list) or any(not isinstance(item, str) or not item.strip() for item in depends_on):
        raise ValueError(
            f"{describe_path(path)}: execution_meta.depends_on must be a list of non-empty strings"
        )
    normalized_depends_on = [item.strip() for item in depends_on]
    if len(set(normalized_depends_on)) != len(normalized_depends_on):
        raise ValueError(
            f"{describe_path(path)}: execution_meta.depends_on must not contain duplicate topics"
        )
    if expected_topic is not None and expected_topic in normalized_depends_on:
        raise ValueError(
            f"{describe_path(path)}: execution_meta.depends_on must not contain its own topic {expected_topic}"
        )

    tranches = execution_meta.get("tranches")
    if not isinstance(tranches, list) or not tranches:
        raise ValueError(f"{describe_path(path)}: execution_meta.tranches must be a non-empty list")

    normalized_tranches: list[dict[str, str]] = []
    seen_tranche_ids: set[str] = set()
    for index, tranche in enumerate(tranches, start=1):
        if not isinstance(tranche, dict):
            raise ValueError(
                f"{describe_path(path)}: execution_meta.tranches[{index}] must be an object"
            )
        tranche_id = tranche.get("id")
        tranche_title = tranche.get("title")
        if not isinstance(tranche_id, str) or not tranche_id.strip():
            raise ValueError(
                f"{describe_path(path)}: execution_meta.tranches[{index}].id must be a non-empty string"
            )
        if not isinstance(tranche_title, str) or not tranche_title.strip():
            raise ValueError(
                f"{describe_path(path)}: execution_meta.tranches[{index}].title must be a non-empty string"
            )
        tranche_id = tranche_id.strip()
        if tranche_id in seen_tranche_ids:
            raise ValueError(
                f"{describe_path(path)}: execution_meta.tranches contains duplicate id {tranche_id}"
            )
        seen_tranche_ids.add(tranche_id)
        normalized_tranches.append({"id": tranche_id, "title": tranche_title.strip()})

    normalized_meta: dict[str, object] = {
        "schema_version": EXECUTION_META_SCHEMA_VERSION,
        "topic": topic,
        "depends_on": normalized_depends_on,
        "tranches": normalized_tranches,
    }

    github_issue = execution_meta.get("github_issue")
    if github_issue is not None:
        if not isinstance(github_issue, int):
            raise ValueError(f"{describe_path(path)}: execution_meta.github_issue must be an integer")
        normalized_meta["github_issue"] = github_issue

    status = execution_meta.get("status")
    if status is not None:
        if status not in {"pending", "in_progress", "completed", "blocked"}:
            raise ValueError(
                f"{describe_path(path)}: execution_meta.status has unsupported value {status!r}"
            )
        normalized_meta["status"] = status

    queue_role = execution_meta.get("queue_role")
    if queue_role is not None:
        if queue_role not in {
            QUEUE_ROLE_FRONT_ACTIVE,
            QUEUE_ROLE_BLOCKED_HOLDING,
            QUEUE_ROLE_PARKED_FUTURE_WAVE,
            QUEUE_ROLE_HISTORICAL_BACKING,
        }:
            raise ValueError(
                f"{describe_path(path)}: execution_meta.queue_role has unsupported value {queue_role!r}"
            )
        normalized_meta["queue_role"] = queue_role

    roadmap_rank = execution_meta.get("roadmap_rank")
    if roadmap_rank is not None:
        if not isinstance(roadmap_rank, int) or roadmap_rank < 1:
            raise ValueError(
                f"{describe_path(path)}: execution_meta.roadmap_rank must be a positive integer"
            )
        normalized_meta["roadmap_rank"] = roadmap_rank

    verification_commands = execution_meta.get("verification_commands")
    if verification_commands is not None:
        if not isinstance(verification_commands, list) or any(
            not isinstance(item, str) or not item.strip() for item in verification_commands
        ):
            raise ValueError(
                f"{describe_path(path)}: execution_meta.verification_commands must be a list of non-empty strings"
            )
        normalized_meta["verification_commands"] = [item.strip() for item in verification_commands]

    return normalized_meta


def validate_dependency_graph(items: list[dict[str, object]], *, enforce_rank_order: bool = True) -> None:
    dependency_map: dict[str, list[str]] = {}
    roadmap_ranks: dict[str, int] = {}

    for item in items:
        topic = item.get("topic")
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("queue item topic must be a non-empty string")
        topic = topic.strip()
        if topic in dependency_map:
            raise ValueError(f"queue dependency graph contains duplicate topic {topic}")

        depends_on = item.get("depends_on", [])
        if not isinstance(depends_on, list) or any(
            not isinstance(dep, str) or not dep.strip() for dep in depends_on
        ):
            raise ValueError(f"queue item {topic} depends_on must be a list of non-empty strings")

        normalized_depends_on = [dep.strip() for dep in depends_on]
        if len(set(normalized_depends_on)) != len(normalized_depends_on):
            raise ValueError(f"queue item {topic} depends_on contains duplicate topics")
        if topic in normalized_depends_on:
            raise ValueError(f"queue item {topic} cannot depend on itself")

        dependency_map[topic] = normalized_depends_on
        roadmap_rank = item.get("roadmap_rank")
        if isinstance(roadmap_rank, int):
            roadmap_ranks[topic] = roadmap_rank

    known_topics = set(dependency_map)
    for topic, depends_on in dependency_map.items():
        for dep in depends_on:
            if dep not in known_topics:
                raise ValueError(f"queue item {topic} depends_on unknown topic {dep}")
            if enforce_rank_order:
                dep_rank = roadmap_ranks.get(dep)
                item_rank = roadmap_ranks.get(topic)
                if dep_rank is not None and item_rank is not None and dep_rank >= item_rank:
                    raise ValueError(
                        "queue dependency rank inversion: "
                        f"{dep} -> {topic} requires {dep}.roadmap_rank < {topic}.roadmap_rank, "
                        f"got {dep_rank} >= {item_rank}"
                    )

    visit_state: dict[str, str] = {}
    stack: list[str] = []

    def visit(topic: str) -> None:
        state = visit_state.get(topic)
        if state == "done":
            return
        if state == "visiting":
            try:
                cycle_start = stack.index(topic)
            except ValueError:
                cycle = stack + [topic]
            else:
                cycle = stack[cycle_start:] + [topic]
            raise ValueError(f"queue dependency cycle detected: {' -> '.join(cycle)}")

        visit_state[topic] = "visiting"
        stack.append(topic)
        for dep in dependency_map[topic]:
            visit(dep)
        stack.pop()
        visit_state[topic] = "done"

    for topic in sorted(dependency_map):
        visit(topic)


def compute_topological_order(items: list[dict[str, object]]) -> list[str]:
    validate_dependency_graph(items, enforce_rank_order=False)

    dependency_map: dict[str, list[str]] = {}
    dependent_map: dict[str, list[str]] = {}
    indegree: dict[str, int] = {}
    stable_keys: dict[str, tuple[bool, int, int, str]] = {}

    for index, item in enumerate(items):
        topic = str(item["topic"]).strip()
        depends_on = [str(dep).strip() for dep in item.get("depends_on", [])]
        roadmap_rank = item.get("roadmap_rank")
        rank_value = roadmap_rank if isinstance(roadmap_rank, int) else 10**9
        dependency_map[topic] = depends_on
        dependent_map[topic] = []
        indegree[topic] = 0
        # Keep dependency-respecting order deterministic while preserving legacy rank/current order bias.
        stable_keys[topic] = (not isinstance(roadmap_rank, int), rank_value, index, topic)

    for topic, depends_on in dependency_map.items():
        indegree[topic] = len(depends_on)
        for dep in depends_on:
            dependent_map[dep].append(topic)

    ready = sorted(
        [topic for topic, degree in indegree.items() if degree == 0],
        key=lambda topic: stable_keys[topic],
    )
    ordered_topics: list[str] = []

    while ready:
        topic = ready.pop(0)
        ordered_topics.append(topic)
        released: list[str] = []
        for dependent in dependent_map[topic]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                released.append(dependent)
        if released:
            ready.extend(released)
            ready.sort(key=lambda candidate: stable_keys[candidate])

    if len(ordered_topics) != len(dependency_map):
        raise ValueError("queue dependency cycle detected during topological order computation")

    return ordered_topics


def infer_item_status(raw_status: str | None) -> str:
    text = (raw_status or "").strip().lower()
    if not text:
        return "pending"
    lead = text.split("(", 1)[0].strip()
    lead = lead.split("—", 1)[0].strip()
    normalized = lead.replace("-", "_").replace(" ", "_")
    if normalized.startswith("blocked"):
        return "blocked"
    if normalized.startswith("closed") or normalized.startswith("completed"):
        return "completed"
    if normalized.startswith("parked") or normalized.startswith("pending") or normalized.startswith("draft"):
        return "pending"
    if (
        normalized.startswith("in_progress")
        or normalized.startswith("active")
        or normalized.startswith("partially_realized")
    ):
        return "in_progress"
    return "pending"


def infer_queue_role(raw_status: str | None, roadmap_note: str | None = None) -> str:
    note = (roadmap_note or "").strip().lower()
    if "blocked" in note:
        return QUEUE_ROLE_BLOCKED_HOLDING
    if any(marker in note for marker in HISTORICAL_ROLE_MARKERS):
        return QUEUE_ROLE_HISTORICAL_BACKING
    if any(marker in note for marker in PARKED_ROLE_MARKERS):
        return QUEUE_ROLE_PARKED_FUTURE_WAVE

    status = infer_item_status(raw_status)
    if status == "blocked":
        return QUEUE_ROLE_BLOCKED_HOLDING
    if status == "completed":
        return QUEUE_ROLE_HISTORICAL_BACKING
    return QUEUE_ROLE_FRONT_ACTIVE


def extract_roadmap_item_context(roadmap_path: Path) -> dict[str, dict[str, object]]:
    items: dict[str, dict[str, object]] = {}
    capture = False
    saw_entries = False

    for line in roadmap_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not capture:
            if stripped == "Working order:" or stripped == "## 4. Execution Order":
                capture = True
            continue

        if not stripped:
            if saw_entries:
                break
            continue
        if stripped == "Priority basis:" or stripped.startswith("- "):
            continue

        match = WORKING_ORDER_RE.match(stripped)
        if not match:
            if saw_entries:
                break
            continue

        saw_entries = True
        topic = match.group("topic")
        roadmap_note = (match.group("note") or "").strip() or None
        items[topic] = {
            "roadmap_rank": int(match.group("rank")),
            "queue_role": infer_queue_role(None, roadmap_note),
        }

    return items


def build_item_payload(temp_doc: Path, roadmap_item_context: dict[str, dict[str, object]]) -> dict[str, object]:
    metadata = parse_metadata(temp_doc)
    topic = temp_doc.name.removesuffix("-execution-ssot.md")
    execution_meta = load_execution_meta_block(temp_doc, expected_topic=topic)
    canonical_rel = normalize_relpath(metadata.get("canonical_path")) or ""
    temp_rel = temp_doc.relative_to(ROOT).as_posix()
    raw_status = metadata.get("status")
    status = infer_item_status(raw_status)
    canonical_path = ROOT / canonical_rel if canonical_rel else None
    roadmap_context = roadmap_item_context.get(topic, {})
    roadmap_rank = roadmap_context.get("roadmap_rank")
    queue_role = str(roadmap_context.get("queue_role") or infer_queue_role(raw_status))
    depends_on = list(execution_meta.get("depends_on", [])) if execution_meta is not None else []
    return {
        "topic": topic,
        "temp_path": temp_rel,
        "canonical_path": canonical_rel,
        "status": status,
        "queue_role": queue_role,
        "roadmap_rank": roadmap_rank,
        "depends_on": depends_on,
        "mirror_present": temp_doc.exists(),
        "canonical_present": bool(canonical_path and canonical_path.exists()),
    }


def infer_roadmap_status(roadmap_path: Path) -> str:
    metadata = parse_metadata(roadmap_path)
    status = (metadata.get("status") or "").strip().lower()
    lead = status.split("(", 1)[0].strip()
    if lead.startswith("active") or "in progress" in lead:
        return "active"
    if lead.startswith("closed") or lead.startswith("completed"):
        return "closed"
    return "draft"


def main() -> int:
    TEMP.mkdir(parents=True, exist_ok=True)
    exec_docs = sorted(TEMP.glob("*-execution-ssot.md"))
    roadmap_path = TEMP / "execution-roadmap.md"
    roadmap_item_context = extract_roadmap_item_context(roadmap_path) if roadmap_path.exists() else {}

    if not exec_docs:
        payload = {
            "version": "temp-queue-state-v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "queue_mode": "empty",
            "active_item_count": 0,
            "roadmap": None,
            "items": [],
        }
    else:
        try:
            items = [build_item_payload(path, roadmap_item_context) for path in exec_docs]
            validate_dependency_graph(items)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        items.sort(
            key=lambda item: (
                item["roadmap_rank"] is None,
                item["roadmap_rank"] if item["roadmap_rank"] is not None else 10**9,
                item["temp_path"],
            )
        )
        queue_mode = "single" if len(items) == 1 else "aggregate"
        roadmap = None
        if roadmap_path.exists():
            roadmap_meta = parse_metadata(roadmap_path)
            roadmap = {
                "temp_path": roadmap_path.relative_to(ROOT).as_posix(),
                "canonical_path": normalize_relpath(roadmap_meta.get("canonical_path")) or "",
                "status": infer_roadmap_status(roadmap_path),
            }
        payload = {
            "version": "temp-queue-state-v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "queue_mode": queue_mode,
            "active_item_count": len(items),
            "roadmap": roadmap,
            "items": items,
        }

    target = TEMP / "queue-state.json"
    write_utf8_lf(target, json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    print(f"WROTE: {target.relative_to(ROOT).as_posix()}")
    print(f"ITEMS: {payload['active_item_count']}")
    print(f"MODE: {payload['queue_mode']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
