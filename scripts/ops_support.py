from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TEMP = DOCS / "temp"
META_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9 /_-]*):(?:\s*(?P<value>.+?)\s*)?$")
DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
QUEUE_STATE_PATH = TEMP / "queue-state.json"


@dataclass
class QueueItem:
    topic: str
    temp_path: str
    canonical_path: str
    status: str
    depends_on: list[str]
    mirror_present: bool
    canonical_present: bool


def normalize_relpath(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().strip("`").replace("\\", "/")
    if not cleaned:
        return None
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def parse_metadata(path: Path, line_limit: int = 60) -> dict[str, str]:
    metadata: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines[:line_limit]:
        match = META_RE.match(line)
        if not match:
            continue
        key = match.group("key").strip().lower().replace(" ", "_")
        metadata[key] = (match.group("value") or "").strip()
    return metadata


def extract_labeled_list(text: str, label: str) -> list[str]:
    lines = text.splitlines()
    target = f"{label}:"
    items: list[str] = []
    capture = False

    for line in lines:
        stripped = line.strip()
        if not capture:
            if stripped == target:
                capture = True
                continue
            if stripped.startswith(target):
                value = stripped[len(target):].strip().strip("`")
                if value:
                    items.append(value)
                capture = True
                continue
        else:
            if stripped.startswith("- "):
                items.append(stripped[2:].strip().strip("`"))
                continue
            if not stripped:
                if items:
                    break
                continue
            if stripped.startswith("## ") or META_RE.match(stripped):
                break
            break

    return items


def read_text(path_or_rel: str | Path) -> str:
    path = ROOT / path_or_rel if isinstance(path_or_rel, str) else path_or_rel
    return path.read_text(encoding="utf-8")


def latest_dated_dir() -> Path | None:
    dated_dirs = sorted(
        [path for path in DOCS.iterdir() if path.is_dir() and DATE_DIR_RE.match(path.name)],
        key=lambda path: path.name,
    )
    return dated_dirs[-1] if dated_dirs else None


def extract_date_dir_name_from_relpath(relpath: str | None) -> str | None:
    normalized = normalize_relpath(relpath)
    if not normalized:
        return None
    parts = Path(normalized).parts
    if len(parts) >= 2 and parts[0] == "docs" and DATE_DIR_RE.match(parts[1]):
        return parts[1]
    return None


def choose_date_dir_name(paths: list[str]) -> str:
    candidates = [extract_date_dir_name_from_relpath(path) for path in paths]
    filtered = [candidate for candidate in candidates if candidate]
    if filtered:
        return sorted(filtered)[-1]
    latest = latest_dated_dir()
    if latest is None:
        raise FileNotFoundError("No dated docs directory found under docs/")
    return latest.name


def ensure_queue_state(refresh: bool = False) -> dict[str, object]:
    if refresh or not QUEUE_STATE_PATH.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sync_temp_queue_state.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    return json.loads(QUEUE_STATE_PATH.read_text(encoding="utf-8"))


def queue_items_from_state(state: dict[str, object]) -> list[QueueItem]:
    items: list[QueueItem] = []
    for raw_item in state.get("items", []):
        if not isinstance(raw_item, dict):
            continue
        items.append(
            QueueItem(
                topic=str(raw_item.get("topic", "")),
                temp_path=str(raw_item.get("temp_path", "")),
                canonical_path=str(raw_item.get("canonical_path", "")),
                status=str(raw_item.get("status", "pending")),
                depends_on=list(raw_item.get("depends_on", [])),
                mirror_present=bool(raw_item.get("mirror_present", False)),
                canonical_present=bool(raw_item.get("canonical_present", False)),
            )
        )
    return items


def canonical_path(path_or_rel: str | Path) -> Path:
    if isinstance(path_or_rel, Path):
        return path_or_rel
    normalized = normalize_relpath(path_or_rel)
    if normalized is None:
        raise ValueError("Path value is empty")
    return ROOT / normalized


def first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def topic_from_execution_doc_name(path_or_rel: str | Path) -> str:
    path = canonical_path(path_or_rel)
    name = path.name
    suffix = "-execution-ssot.md"
    if name.endswith(suffix):
        return name[: -len(suffix)]
    return path.stem


def classify_artifact(path_value: str) -> tuple[str, str, str]:
    normalized = normalize_relpath(path_value) or path_value
    suffix = Path(normalized).suffix.lower()
    lowered = normalized.lower()

    if suffix == ".py":
        return ("live code surface", "direct code read", "execution + closure")
    if suffix == ".md":
        return ("doc artifact", "document review", "survey + execution")
    if suffix == ".json":
        return ("structured artifact", "structured output review", "survey + closure")
    if suffix == ".jsonl":
        return ("event log", "log inspection", "closure + analysis")
    if suffix == ".txt":
        if "ast" in lowered:
            return ("inventory", "Python AST sweep", "survey + execution")
        return ("inventory", "text inventory review", "survey + execution")
    return ("artifact", "manual collection", "survey + execution")


def common_topic_slug(items: list[QueueItem]) -> str:
    if not items:
        return "temp-queue"
    token_lists = [item.topic.split("-") for item in items if item.topic]
    if not token_lists:
        return "temp-queue"
    prefix: list[str] = []
    shortest = min(len(tokens) for tokens in token_lists)
    for index in range(shortest):
        token = token_lists[0][index]
        if all(tokens[index] == token for tokens in token_lists[1:]):
            prefix.append(token)
        else:
            break
    if prefix:
        return "-".join(prefix) + "-aggregate"
    return "temp-queue"
