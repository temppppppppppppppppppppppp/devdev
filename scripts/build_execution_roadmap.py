from __future__ import annotations

import argparse
import sys

from ops_support import (
    DOCS,
    ROOT,
    TEMP,
    choose_date_dir_name,
    common_topic_slug,
    ensure_queue_state,
    queue_items_from_state,
)


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
    args = parser.parse_args()

    state = ensure_queue_state(refresh=args.refresh_queue_state)
    items = queue_items_from_state(state)

    if len(items) < 2 and not args.allow_single:
        print("NOOP: aggregate roadmap is not required because fewer than two execution SSOT mirrors are active.")
        return 0

    date_dir = choose_date_dir_name([item.canonical_path for item in items])
    topic = args.topic or common_topic_slug(items)
    roadmap_text = build_roadmap_text(topic, date_dir, items)

    canonical_path = DOCS / date_dir / f"{topic}-execution-roadmap.md"
    temp_path = TEMP / "execution-roadmap.md"
    canonical_path.write_text(roadmap_text + "\n", encoding="utf-8")
    temp_path.write_text(roadmap_text + "\n", encoding="utf-8")

    print(f"WROTE: {canonical_path.relative_to(ROOT).as_posix()}")
    print(f"WROTE: {temp_path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
