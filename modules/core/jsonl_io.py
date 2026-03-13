"""Utilities for synchronized JSONL appends."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

_JSONL_APPEND_LOCK = threading.Lock()


def append_jsonl_record(log_path: str | Path, payload: Any) -> Path:
    """Append one JSONL record under a process-wide write lock."""
    path = Path(log_path)
    line = json.dumps(payload, ensure_ascii=False, default=str)
    with _JSONL_APPEND_LOCK:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    return path
