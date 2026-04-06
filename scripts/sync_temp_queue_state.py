from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMP = ROOT / "docs" / "temp"
META_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9 /_-]*):(?:\s*(?P<value>.+?)\s*)?$")
WORKING_ORDER_RE = re.compile(r"^(?P<rank>\d+)\.\s+`(?P<topic>[^`]+)`(?:\s+\((?P<note>.+)\))?$")

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


def parse_metadata(path: Path, line_limit: int = 40) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[:line_limit]:
        match = META_RE.match(line)
        if not match:
            continue
        key = match.group("key").strip().lower().replace(" ", "_")
        metadata[key] = (match.group("value") or "").strip()
    return metadata


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
    canonical_rel = normalize_relpath(metadata.get("canonical_path")) or ""
    temp_rel = temp_doc.relative_to(ROOT).as_posix()
    raw_status = metadata.get("status")
    status = infer_item_status(raw_status)
    canonical_path = ROOT / canonical_rel if canonical_rel else None
    roadmap_context = roadmap_item_context.get(topic, {})
    roadmap_rank = roadmap_context.get("roadmap_rank")
    queue_role = str(roadmap_context.get("queue_role") or infer_queue_role(raw_status))
    return {
        "topic": topic,
        "temp_path": temp_rel,
        "canonical_path": canonical_rel,
        "status": status,
        "queue_role": queue_role,
        "roadmap_rank": roadmap_rank,
        "depends_on": [],
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
        items = [build_item_payload(path, roadmap_item_context) for path in exec_docs]
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
    target.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE: {target.relative_to(ROOT).as_posix()}")
    print(f"ITEMS: {payload['active_item_count']}")
    print(f"MODE: {payload['queue_mode']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
