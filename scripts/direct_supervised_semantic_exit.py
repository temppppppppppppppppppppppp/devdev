"""Shared semantic exit helpers for direct supervised runners."""

from __future__ import annotations

from typing import Any


def semantic_exit_code(payload: Any) -> int:
    """Return shell success only when the run payload proves semantic success."""
    if isinstance(payload, dict) and payload.get("success") is True:
        return 0
    return 1
