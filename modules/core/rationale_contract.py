"""Shared rationale text normalization helpers."""

from __future__ import annotations


def first_nonempty_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def resolve_selection_reason_text(*values: object) -> str:
    return first_nonempty_text(*values)


def resolve_verdict_reason_text(*values: object) -> str:
    return first_nonempty_text(*values)


def resolve_comparison_notes_text(*values: object) -> str:
    return first_nonempty_text(*values)


def compact_jsonish(value: object, *, max_depth: int = 6, list_limit: int = 32) -> object:
    if max_depth <= 0:
        return first_nonempty_text(value)
    if value is None:
        return None
    if isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for raw_key, raw_value in value.items():
            key = str(raw_key or "").strip()
            if not key:
                continue
            normalized = compact_jsonish(raw_value, max_depth=max_depth - 1, list_limit=list_limit)
            if normalized in ("", [], {}, None):
                continue
            result[key] = normalized
        return result
    if isinstance(value, list):
        result: list[object] = []
        for raw_item in value[: max(1, int(list_limit or 1))]:
            normalized = compact_jsonish(raw_item, max_depth=max_depth - 1, list_limit=list_limit)
            if normalized in ("", [], {}, None):
                continue
            result.append(normalized)
        return result
    return first_nonempty_text(value)


def resolve_structured_advisory_payload(value: object) -> dict[str, object]:
    normalized = compact_jsonish(value)
    return dict(normalized) if isinstance(normalized, dict) and normalized else {}
