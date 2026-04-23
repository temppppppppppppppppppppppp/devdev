from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import replace
from pathlib import Path

try:
    from ops_support import (
        DOCS,
        ROOT,
        TEMP,
        QUEUE_STATE_PATH,
        QueueItem,
        choose_date_dir_name,
        common_topic_slug,
        ensure_queue_state,
        queue_items_from_state,
    )
    from sync_temp_queue_state import compute_topological_order
except ModuleNotFoundError:  # pragma: no cover - import path depends on invocation style
    from scripts.ops_support import (
        DOCS,
        ROOT,
        TEMP,
        QUEUE_STATE_PATH,
        QueueItem,
        choose_date_dir_name,
        common_topic_slug,
        ensure_queue_state,
        queue_items_from_state,
    )
    from scripts.sync_temp_queue_state import compute_topological_order

WORKING_ORDER_RE = re.compile(r"^(?P<rank>\d+)\.\s+`(?P<topic>[^`]+)`(?:\s+\((?P<note>.+)\))?$")


def write_utf8_lf(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_roadmap_text(topic: str, date_dir: str, items) -> str:
    queue_snapshot = "\n".join(f"- `{item.temp_path}`" for item in items)
    inventory_rows = "\n".join(
        f"| `{item.topic}` | `{item.canonical_path}` | `{item.temp_path}` | {item.status} | "
        f"queue_role={item.queue_role}; roadmap_rank={item.roadmap_rank if item.roadmap_rank is not None else 'n/a'}; auto-built from queue-state |"
        for item in items
    )
    dependency_lines = []
    for item in items:
        if item.depends_on:
            for dep in item.depends_on:
                dependency_lines.append(f"- `{dep}` -> `{item.topic}`")
    if not dependency_lines:
        dependency_lines = [
            "- no explicit dependencies recorded in queue-state",
            "- shared substrate: determine during implementation",
            "- merge opportunities: review overlapping execution SSOT tranches",
        ]
    execution_order = "\n".join(f"{index}. `{item.topic}`" for index, item in enumerate(items, start=1))
    per_item_plans = "\n\n".join(
        "\n".join(
            [
                f"### {item.topic}",
                "- goal: realize this queued execution SSOT in roadmap order",
                f"- prerequisites: {', '.join(item.depends_on) if item.depends_on else 'none recorded'}",
                "- execution notes: review the canonical execution SSOT before patching",
                "- completion signal: acceptance criteria satisfied and closure harness applied",
                "- temp cleanup action: remove the mirror after canonical status and roadmap ledger are updated",
            ]
        )
        for item in items
    )
    ledger_rows = "\n".join(
        f"| `{item.topic}` | {item.status} | {date_dir} | none |" for item in items
    )

    return f"""# {topic.replace('-', ' ').title()} Execution Roadmap

Date: {date_dir}
Status: active
Canonical Path: `docs/{date_dir}/{topic}-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Queue Snapshot:
{queue_snapshot}

## 1. Purpose
- Provide an aggregate execution order for the current temp queue.
- Keep canonical and temp execution work aligned under one roadmap.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
{inventory_rows}

## 3. Dependency Graph
{chr(10).join(dependency_lines)}

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`
- current queue-state order plus explicit dependencies

{execution_order}

## 5. Per-Item Plan

{per_item_plans}

## 6. Shared Risks and Side-Effects
- shared write paths: review each canonical execution SSOT side-effect section before realization
- shared DB/schema touchpoints: determine from queued execution docs before patching
- shared logs/UI surfaces: queue items that touch operator-visible surfaces should coordinate output contracts
- rollback/recovery concerns: close one item cleanly before expanding the queue surface
- queue collision or ordering risks: out-of-order realization can invalidate temp queue meaning

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
{ledger_rows}

Allowed statuses:
- pending
- in_progress
- completed
- blocked

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all items are completed, remove `docs/temp/execution-roadmap.md`
- remove `docs/temp/queue-state.json` if present
- leave `docs/temp/README.md`
"""


def rewrite_items_to_topological_ranks(items: list[QueueItem]) -> list[QueueItem]:
    topic_order = compute_topological_order(
        [
            {
                "topic": item.topic,
                "depends_on": list(item.depends_on),
                "roadmap_rank": item.roadmap_rank,
            }
            for item in items
        ]
    )
    by_topic = {item.topic: item for item in items}
    rewritten: list[QueueItem] = []
    for rank, topic in enumerate(topic_order, start=1):
        rewritten.append(replace(by_topic[topic], roadmap_rank=rank))
    return rewritten


def rewrite_queue_state_payload(state: dict[str, object], items: list[QueueItem]) -> dict[str, object]:
    raw_items = state.get("items", [])
    if not isinstance(raw_items, list):
        raise ValueError("queue-state payload items must be an array")

    raw_by_topic: dict[str, dict[str, object]] = {}
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            raise ValueError("queue-state payload contains a non-object item")
        topic = raw_item.get("topic")
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("queue-state payload item topic must be a non-empty string")
        raw_by_topic[topic.strip()] = dict(raw_item)

    rewritten_payload = dict(state)
    rewritten_items: list[dict[str, object]] = []
    for item in items:
        raw = raw_by_topic[item.topic]
        raw["roadmap_rank"] = item.roadmap_rank
        rewritten_items.append(raw)
    rewritten_payload["items"] = rewritten_items
    return rewritten_payload


def existing_roadmap_topic(state: dict[str, object]) -> str | None:
    roadmap = state.get("roadmap")
    if not isinstance(roadmap, dict):
        return None
    canonical_path = roadmap.get("canonical_path")
    if not isinstance(canonical_path, str) or not canonical_path.strip():
        return None
    name = Path(canonical_path.strip().replace("\\", "/")).name
    suffix = "-execution-roadmap.md"
    if not name.endswith(suffix):
        return None
    return name[: -len(suffix)] or None


def existing_roadmap_canonical_path(state: dict[str, object]) -> Path | None:
    roadmap = state.get("roadmap")
    if not isinstance(roadmap, dict):
        return None
    canonical_path = roadmap.get("canonical_path")
    if not isinstance(canonical_path, str) or not canonical_path.strip():
        return None
    normalized = canonical_path.strip().strip("`").replace("\\", "/")
    return ROOT / normalized


def _ordered_lines(items: list[QueueItem], notes_by_topic: dict[str, str | None]) -> list[str]:
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        note = notes_by_topic.get(item.topic)
        if note:
            lines.append(f"{index}. `{item.topic}` ({note})")
        else:
            lines.append(f"{index}. `{item.topic}`")
    return lines


def rewrite_existing_roadmap_order(text: str, items: list[QueueItem]) -> str:
    lines = text.splitlines()
    notes_by_topic: dict[str, str | None] = {}
    for line in lines:
        match = WORKING_ORDER_RE.match(line.strip())
        if match:
            notes_by_topic[match.group("topic")] = (match.group("note") or "").strip() or None

    replacement_lines = _ordered_lines(items, notes_by_topic)

    def replace_after_header(header_index: int) -> str | None:
        entry_start: int | None = None
        entry_end: int | None = None
        for index in range(header_index + 1, len(lines)):
            stripped = lines[index].strip()
            if entry_start is None:
                if not stripped:
                    continue
                if stripped == "Priority basis:" or stripped.startswith("- "):
                    continue
                if WORKING_ORDER_RE.match(stripped):
                    entry_start = index
                    entry_end = index + 1
                    continue
                if stripped.startswith("## "):
                    break
                continue

            if WORKING_ORDER_RE.match(stripped):
                entry_end = index + 1
                continue
            break

        if entry_start is None or entry_end is None:
            return None

        updated_lines = lines[:entry_start] + replacement_lines + lines[entry_end:]
        return "\n".join(updated_lines) + "\n"

    for index, line in enumerate(lines):
        if line.strip() == "Working order:":
            updated = replace_after_header(index)
            if updated is not None:
                return updated

    for index, line in enumerate(lines):
        if line.strip() == "## 4. Execution Order":
            updated = replace_after_header(index)
            if updated is not None:
                return updated

    raise ValueError("existing roadmap is missing a recognizable execution-order block")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a canonical + temp aggregate execution roadmap from the temp queue.")
    parser.add_argument("--topic", help="Override the roadmap topic slug.")
    parser.add_argument(
        "--allow-single",
        action="store_true",
        help="Allow roadmap generation even when only one execution SSOT is active.",
    )
    parser.add_argument(
        "--refresh-queue-state",
        action="store_true",
        help="Refresh docs/temp/queue-state.json before reading queue state.",
    )
    parser.add_argument(
        "--rewrite-roadmap-ranks",
        action="store_true",
        help="Recompute dependency-respecting roadmap ranks and rewrite queue-state before rebuilding the roadmap.",
    )
    args = parser.parse_args()

    state = ensure_queue_state(refresh=args.refresh_queue_state)
    items = queue_items_from_state(state)

    if len(items) < 2 and not args.allow_single:
        print("NOOP: aggregate roadmap is not required because fewer than two execution SSOT mirrors are active.")
        return 0

    if args.rewrite_roadmap_ranks:
        items = rewrite_items_to_topological_ranks(items)
        state = rewrite_queue_state_payload(state, items)
        write_utf8_lf(QUEUE_STATE_PATH, json.dumps(state, ensure_ascii=True, indent=2) + "\n")
        print(f"REWROTE: {QUEUE_STATE_PATH.relative_to(ROOT).as_posix()}")

    date_dir = choose_date_dir_name([item.canonical_path for item in items])
    topic = args.topic or existing_roadmap_topic(state) or common_topic_slug(items)
    canonical_path = existing_roadmap_canonical_path(state) or (DOCS / date_dir / f"{topic}-execution-roadmap.md")
    temp_path = TEMP / "execution-roadmap.md"
    if args.rewrite_roadmap_ranks and (canonical_path.exists() or temp_path.exists()):
        source_path = canonical_path if canonical_path.exists() else temp_path
        roadmap_text = rewrite_existing_roadmap_order(source_path.read_text(encoding="utf-8"), items)
    else:
        roadmap_text = build_roadmap_text(topic, date_dir, items)
    final_text = roadmap_text if roadmap_text.endswith("\n") else roadmap_text + "\n"
    write_utf8_lf(canonical_path, final_text)
    write_utf8_lf(temp_path, final_text)

    print(f"WROTE: {canonical_path.relative_to(ROOT).as_posix()}")
    print(f"WROTE: {temp_path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
