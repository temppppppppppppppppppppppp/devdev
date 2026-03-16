"""Utilities for count-aware inventory normalization."""

from __future__ import annotations

import re

_COUNT_SUFFIX_RE = re.compile(
    r"^(?P<name>.+?)\s*(?P<count>\d+)\s*(?P<unit>개|대|병|자루|권|장|벌|알|정|통|칸|쌍|척|세트)\s*$"
)
_SPLIT_RE = re.compile(r"[,/\n]+")


def _coerce_positive_int(raw) -> int | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw if raw > 0 else None
    if isinstance(raw, float):
        if raw.is_integer() and raw > 0:
            return int(raw)
        return None
    if isinstance(raw, str):
        text = raw.strip().replace(",", "")
        if text.isdigit():
            value = int(text)
            return value if value > 0 else None
    return None


def _clean_name(raw) -> str:
    return " ".join(str(raw or "").strip().split())


def _normalize_name_and_count(name: str, count_hint=None) -> tuple[str, int] | None:
    cleaned = _clean_name(name)
    if not cleaned:
        return None

    count = _coerce_positive_int(count_hint)
    if count is None:
        match = _COUNT_SUFFIX_RE.match(cleaned)
        if match:
            cleaned = _clean_name(match.group("name"))
            count = int(match.group("count"))
        else:
            count = 1

    if not cleaned:
        return None
    return cleaned, count


def _iter_inventory_pairs(raw):
    if raw is None:
        return

    if isinstance(raw, list):
        for entry in raw:
            yield from _iter_inventory_pairs(entry)
        return

    if isinstance(raw, dict):
        name = raw.get("name") or raw.get("item") or raw.get("label")
        count = raw.get("count")
        if count is None:
            count = raw.get("quantity")
        if count is None:
            count = raw.get("qty")
        if count is None:
            count = raw.get("amount")
        if name:
            pair = _normalize_name_and_count(name, count)
            if pair:
                yield pair
            return
        for key, value in raw.items():
            pair = _normalize_name_and_count(key, value)
            if pair:
                yield pair
        return

    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return
        parts = [part for part in _SPLIT_RE.split(text) if part.strip()]
        if len(parts) > 1:
            for part in parts:
                yield from _iter_inventory_pairs(part)
            return
        pair = _normalize_name_and_count(text)
        if pair:
            yield pair
        return


def normalize_inventory_counts(raw) -> dict[str, int]:
    """Normalize inventory-like structures into a name->count mapping."""
    counts: dict[str, int] = {}
    for name, count in _iter_inventory_pairs(raw):
        counts[name] = counts.get(name, 0) + count
    return dict(sorted(counts.items()))


def compute_inventory_count_deltas(prev_counts: dict | None, curr_counts: dict | None) -> list[dict]:
    """Return deterministic count deltas across two normalized inventory maps."""
    prev_counts = normalize_inventory_counts(prev_counts or {})
    curr_counts = normalize_inventory_counts(curr_counts or {})
    names = sorted(set(prev_counts) | set(curr_counts))
    deltas = []
    for name in names:
        prev_count = int(prev_counts.get(name, 0) or 0)
        curr_count = int(curr_counts.get(name, 0) or 0)
        if prev_count == curr_count:
            continue
        deltas.append(
            {
                "name": name,
                "from": prev_count,
                "to": curr_count,
                "delta": curr_count - prev_count,
            }
        )
    return deltas
