"""Shared Stage 2 facade and validation contracts."""

from copy import deepcopy
from typing import Any

TACTICAL_DOC_DUPLICATE_THRESHOLD = 0.92


def merge_stage2_authoritative_packet(authoritative: Any, fallback: Any) -> dict[str, Any]:
    """Preserve refined-arc packet truth while backfilling missing block fields."""
    authoritative_dict = authoritative if isinstance(authoritative, dict) else {}
    fallback_dict = fallback if isinstance(fallback, dict) else {}
    if not fallback_dict:
        return deepcopy(authoritative_dict)
    if not authoritative_dict:
        return deepcopy(fallback_dict)

    merged = deepcopy(fallback_dict)
    for key, value in authoritative_dict.items():
        merged[key] = deepcopy(value)
    return merged
