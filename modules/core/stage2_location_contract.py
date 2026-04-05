"""Utilities for canonicalizing Stage2 location contract labels."""

from __future__ import annotations

import re
from typing import Any

_LOCATION_SENTENCE_SPLIT_RE = re.compile(r"[.!?]\s+")
_LOCATION_STOP_TOKENS = (
    "시계는",
    "창밖",
    "모니터",
    "모니터에",
    "가리킨다",
    "법인 설립",
    "초기 트레이딩",
    "초기 거래",
    "브리핑",
    "장부",
    "차트",
    "불빛",
    "서류",
    "비어",
    "놓인",
    "놓여",
    "아직 ",
    "위한 ",
)


def collapse_stage2_location_label(raw_value: Any, *, max_chars: int = 48) -> str:
    """Collapse scene-like location prose into a short canonical label."""
    text = re.sub(r"\s+", " ", str(raw_value or "")).strip(" ,./")
    if not text:
        return ""

    text = _LOCATION_SENTENCE_SPLIT_RE.split(text, maxsplit=1)[0].strip(" ,./")
    if not text:
        return ""

    earliest_stop_idx: int | None = None
    for token in _LOCATION_STOP_TOKENS:
        idx = text.find(token)
        if idx > 0 and (earliest_stop_idx is None or idx < earliest_stop_idx):
            earliest_stop_idx = idx
    if earliest_stop_idx is not None:
        candidate = text[:earliest_stop_idx].rstrip(" ,-/")
        if len(candidate) >= 4:
            text = candidate

    if len(text) > max_chars and "," in text:
        kept_parts: list[str] = []
        for part in (chunk.strip() for chunk in text.split(",") if chunk.strip()):
            candidate = ", ".join(kept_parts + [part]) if kept_parts else part
            if kept_parts and len(candidate) > max_chars:
                break
            kept_parts.append(part)
            if len(candidate) >= max_chars // 2 and len(kept_parts) >= 2:
                break
        if kept_parts:
            text = ", ".join(kept_parts)

    if len(text) > max_chars:
        truncated = text[:max_chars]
        if " " in truncated[20:]:
            truncated = truncated[: truncated.rfind(" ")]
        text = truncated.rstrip(" ,-/")

    return text.strip(" ,./")


def is_verbose_stage2_location_label(raw_value: Any, *, max_chars: int = 80) -> bool:
    """Return True when a location field looks like scene prose instead of a label."""
    text = re.sub(r"\s+", " ", str(raw_value or "")).strip(" ,./")
    if not text:
        return False
    return len(text) > max_chars or collapse_stage2_location_label(text, max_chars=max_chars) != text
