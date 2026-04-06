"""Shared Stage 2 facade and validation contracts."""

from copy import deepcopy
from typing import Any

TACTICAL_DOC_DUPLICATE_THRESHOLD = 0.92


def _stage2_packet_value_is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def merge_stage2_authoritative_packet(authoritative: Any, fallback: Any) -> dict[str, Any]:
    """Preserve non-empty refined-arc packet truth while backfilling missing block fields."""
    authoritative_dict = authoritative if isinstance(authoritative, dict) else {}
    fallback_dict = fallback if isinstance(fallback, dict) else {}
    if not fallback_dict:
        return deepcopy(authoritative_dict)
    if not authoritative_dict:
        return deepcopy(fallback_dict)

    merged = deepcopy(fallback_dict)
    for key, value in authoritative_dict.items():
        fallback_value = fallback_dict.get(key)
        if isinstance(value, dict) and isinstance(fallback_value, dict):
            merged[key] = merge_stage2_authoritative_packet(value, fallback_value)
            continue
        if _stage2_packet_value_is_empty(value) and key in fallback_dict:
            continue
        merged[key] = deepcopy(value)
    return merged
