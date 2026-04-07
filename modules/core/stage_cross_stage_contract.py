"""Bounded helpers for cross-stage vocabulary alias normalization."""

from __future__ import annotations

import re


def _compact_text(value: object, *, item_limit: int = 220) -> str:
    if isinstance(value, list):
        parts = [_compact_text(item, item_limit=item_limit) for item in value]
        return "\n".join(part for part in parts if part)
    if isinstance(value, dict):
        for key in ("summary", "text", "content", "value", "constraint_summary", "arc_constraint_summary"):
            text = _compact_text(value.get(key), item_limit=item_limit)
            if text:
                return text
        return ""
    text = re.sub(r"\s+", " ", str(value or "")).strip().strip("-•*")
    if not text:
        return ""
    return text[:item_limit].strip()


def _normalize_episode_detail_lines(raw_value: object, *, item_limit: int = 180) -> list[str]:
    if isinstance(raw_value, list):
        raw_items = raw_value
    elif isinstance(raw_value, dict):
        raw_items = []
        for key in ("details", "mission", "summary", "goal", "hook", "content", "event"):
            value = raw_value.get(key)
            if isinstance(value, list):
                raw_items.extend(value)
            elif value:
                raw_items.append(value)
    elif raw_value:
        raw_items = [raw_value]
    else:
        raw_items = []

    normalized: list[str] = []
    for raw_item in raw_items:
        text = _compact_text(raw_item, item_limit=item_limit)
        if text and text not in normalized:
            normalized.append(text)
    return normalized[:5]


def _normalize_episode_details(raw_value: object) -> list[dict[str, object]]:
    if not isinstance(raw_value, list):
        return []

    normalized: list[dict[str, object]] = []
    seen_eps: set[int] = set()
    for raw_item in raw_value:
        if not isinstance(raw_item, dict):
            continue
        raw_ep_num = raw_item.get("ep_num", raw_item.get("episode_num", raw_item.get("episode_no")))
        try:
            ep_num = int(raw_ep_num)
        except (TypeError, ValueError):
            continue
        details = _normalize_episode_detail_lines(raw_item)
        if not details or ep_num in seen_eps:
            continue
        seen_eps.add(ep_num)
        normalized.append({"ep_num": ep_num, "details": details})
    normalized.sort(key=lambda item: int(item["ep_num"]))
    return normalized


def resolve_cross_stage_constraint_summary(payload: object, *, item_limit: int = 220) -> str:
    if not isinstance(payload, dict):
        return ""
    for key in ("constraint_summary", "arc_constraint_summary"):
        text = _compact_text(payload.get(key), item_limit=item_limit)
        if text:
            return text
    return ""


def resolve_cross_stage_episode_mission_lines(
    payload: object,
    *,
    ep_num: int | None,
    limit: int = 4,
    item_limit: int = 180,
) -> list[str]:
    if not isinstance(payload, dict):
        return []

    try:
        target_ep = int(ep_num) if ep_num is not None else None
    except (TypeError, ValueError):
        target_ep = None

    if target_ep is not None:
        for item in _normalize_episode_details(payload.get("episode_details")):
            if int(item["ep_num"]) == target_ep:
                return list(item["details"])[:limit]

    fallback: list[str] = []
    for key in ("goal", "hook", "core_conflict"):
        text = _compact_text(payload.get(key), item_limit=item_limit)
        if text and text not in fallback:
            fallback.append(text)
    return fallback[:limit]
