from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMP = ROOT / "docs" / "temp"
META_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9 /_-]*):(?:\s*(?P<value>.+?)\s*)?$")


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
    text = (raw_status or "").lower()
    if "blocked" in text:
        return "blocked"
    if "closed" in text or "completed" in text:
        return "completed"
    if "in progress" in text or "active" in text:
        return "in_progress"
    return "pending"


def build_item_payload(temp_doc: Path) -> dict[str, object]:
    metadata = parse_metadata(temp_doc)
    topic = temp_doc.name.removesuffix("-execution-ssot.md")
    canonical_rel = normalize_relpath(metadata.get("canonical_path")) or ""
    temp_rel = temp_doc.relative_to(ROOT).as_posix()
    status = infer_item_status(metadata.get("status"))
    canonical_path = ROOT / canonical_rel if canonical_rel else None
    return {
        "topic": topic,
        "temp_path": temp_rel,
        "canonical_path": canonical_rel,
        "status": status,
        "depends_on": [],
        "mirror_present": temp_doc.exists(),
        "canonical_present": bool(canonical_path and canonical_path.exists()),
    }


def infer_roadmap_status(roadmap_path: Path) -> str:
    metadata = parse_metadata(roadmap_path)
    status = (metadata.get("status") or "").lower()
    if "closed" in status:
        return "closed"
    if "active" in status or "in progress" in status:
        return "active"
    return "draft"


def main() -> int:
    TEMP.mkdir(parents=True, exist_ok=True)
    exec_docs = sorted(TEMP.glob("*-execution-ssot.md"))
    roadmap_path = TEMP / "execution-roadmap.md"

    if not exec_docs:
        payload = {
            "version": "temp-queue-state-v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "queue_mode": "empty",
            "active_item_count": 0,
            "roadmap": None,
            "items": [],
        }
    else:
        items = [build_item_payload(path) for path in exec_docs]
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
            "generated_at": datetime.now(timezone.utc).isoformat(),
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
