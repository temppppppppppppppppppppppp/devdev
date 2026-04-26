"""Shared semantic exit helpers for direct supervised runners."""

from __future__ import annotations

from typing import Any

ARCHIVE_OK_STATUS = "ok"


def semantic_exit_code(payload: Any) -> int:
    """Return shell success only when the run payload proves semantic success."""
    if isinstance(payload, dict) and payload.get("success") is True and not _archive_failed(payload):
        return 0
    return 1


def _archive_failed(payload: dict[str, Any]) -> bool:
    archive = payload.get("benchmark_archive")
    if not isinstance(archive, dict) or "status" not in archive:
        return False
    return str(archive.get("status", "") or "").strip().lower() != ARCHIVE_OK_STATUS
