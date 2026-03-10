"""Python-only quality signal metrics for final manuscripts."""

from __future__ import annotations

import gzip
import re
import statistics
from typing import Any

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…。！？])\s+|[\r\n]+")
_WHITESPACE_RE = re.compile(r"\s+")

_CHECKLIST_ALERT_VALUES = {"ISSUE", "WARN", "WARNING", "FAIL", "ERROR", "MISMATCH", "REJECT"}
_WARNING_KEYS = (
    "warnings",
    "_warnings",
    "python_warnings",
    "_python_warnings",
    "validator_warnings",
    "precheck_warnings",
)

_AI_SLOP_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("그야말로", re.compile(r"그야말로")),
    ("말 그대로", re.compile(r"말 그대로")),
    ("순식간에", re.compile(r"순식간에")),
    ("한순간", re.compile(r"한순간")),
    ("어느새", re.compile(r"어느새")),
    ("숨을 삼켰다", re.compile(r"숨을 삼켰다")),
    ("침을 삼켰다", re.compile(r"침을 삼켰다")),
    ("입꼬리 올림", re.compile(r"입꼬리(?:를|가)?\s*(?:올렸다|말아 올렸다)")),
    ("시선을 돌렸다", re.compile(r"시선을 돌렸다")),
    ("고개를 끄덕였다", re.compile(r"고개를 끄덕였다")),
    ("입을 열었다", re.compile(r"입을 열었다")),
)


def _normalize_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", str(text or "")).strip()


def split_sentences(text: str) -> list[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []

    parts = [chunk.strip() for chunk in _SENTENCE_SPLIT_RE.split(normalized)]
    sentences = [chunk for chunk in parts if len(chunk) >= 2]
    return sentences or [normalized]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _count_alert_checklist_items(consistency_checklist: dict | None) -> int:
    if not isinstance(consistency_checklist, dict):
        return 0

    count = 0
    for value in consistency_checklist.values():
        if isinstance(value, str) and value.strip().upper() in _CHECKLIST_ALERT_VALUES:
            count += 1
            continue
        if isinstance(value, dict):
            status = str(
                value.get("status")
                or value.get("result")
                or value.get("value")
                or value.get("severity")
                or ""
            ).strip().upper()
            if status in _CHECKLIST_ALERT_VALUES:
                count += 1
    return count


def extract_warning_count(payload: dict | None) -> int:
    if not isinstance(payload, dict):
        return 0

    total = 0
    for key in _WARNING_KEYS:
        value = payload.get(key)
        if isinstance(value, list | tuple | set):
            total += len(value)
        elif isinstance(value, dict):
            total += len(value)
        elif isinstance(value, int | float):
            total += max(0, int(value))

    if total == 0:
        for key in ("warning_count", "_warning_count", "structured_warning_count"):
            value = payload.get(key)
            if isinstance(value, int | float):
                total += max(0, int(value))
    return total


def compute_compression_ratio(text: str) -> float:
    raw = str(text or "").encode("utf-8")
    if not raw:
        return 0.0
    return round(len(gzip.compress(raw)) / max(len(raw), 1), 4)


def compute_burstiness(text: str, *, sentences: list[str] | None = None) -> float:
    source = sentences if sentences is not None else split_sentences(text)
    if len(source) < 2:
        return 0.0
    lengths = [len(sentence) for sentence in source]
    return round(statistics.pstdev(lengths), 2)


def compute_complexity(text: str, *, sentences: list[str] | None = None) -> float:
    source = sentences if sentences is not None else split_sentences(text)
    if not source:
        return 0.0

    lengths = [len(sentence) for sentence in source]
    avg_length = sum(lengths) / len(lengths)
    long_ratio = sum(1 for length in lengths if length >= 45) / len(lengths)
    return round(avg_length * (1 + long_ratio), 2)


def compute_ai_slop(text: str) -> dict[str, Any]:
    normalized = _normalize_text(text)
    if not normalized:
        return {"score": 0.0, "total_hits": 0, "density_per_10k": 0.0, "hits": []}

    hits: list[dict[str, Any]] = []
    total_hits = 0
    for label, pattern in _AI_SLOP_PATTERNS:
        count = len(pattern.findall(normalized))
        if count <= 0:
            continue
        total_hits += count
        hits.append({"pattern": label, "count": count})

    density = total_hits / max(len(normalized) / 10000, 1.0)
    hits.sort(key=lambda item: (-int(item["count"]), str(item["pattern"])))
    return {
        "score": round(density, 3),
        "total_hits": total_hits,
        "density_per_10k": round(density, 3),
        "hits": hits[:8],
    }


def compute_ced(
    text: str,
    *,
    consistency_checklist: dict | None = None,
    warning_count: int = 0,
) -> dict[str, Any]:
    issue_count = _count_alert_checklist_items(consistency_checklist)
    structured_warning_count = max(0, int(warning_count or 0))
    text_units = max(len(str(text or "")) / 10000, 1.0)
    error_count = issue_count + structured_warning_count
    return {
        "score": round(error_count / text_units, 3),
        "issue_count": issue_count,
        "warning_count": structured_warning_count,
        "error_count": error_count,
    }


def compute_quality_signal_bundle(
    text: str,
    *,
    consistency_checklist: dict | None = None,
    warning_count: int = 0,
) -> dict[str, Any]:
    sentences = split_sentences(text)
    ced = compute_ced(text, consistency_checklist=consistency_checklist, warning_count=warning_count)
    ai_slop = compute_ai_slop(text)
    compression_ratio = compute_compression_ratio(text)
    burstiness = compute_burstiness(text, sentences=sentences)
    complexity = compute_complexity(text, sentences=sentences)

    return {
        "ced_score": ced["score"],
        "ai_slop_score": ai_slop["score"],
        "ai_slop_hits": ai_slop["hits"],
        "compression_ratio": compression_ratio,
        "burstiness": burstiness,
        "complexity": complexity,
        "signal_summary": {
            "sentence_count": len(sentences),
            "ced_breakdown": {
                "issue_count": ced["issue_count"],
                "warning_count": ced["warning_count"],
            },
            "ai_slop_total_hits": ai_slop["total_hits"],
            "compression_ratio": compression_ratio,
            "burstiness": burstiness,
            "complexity": complexity,
        },
    }


def build_signal_stat(
    *,
    field: str,
    recent_rows: list[dict[str, Any]],
    mode: str,
) -> dict[str, Any]:
    values = [_safe_float(row.get(field)) for row in recent_rows]
    latest_value = values[-1] if values else 0.0
    median_value = statistics.median(values) if values else 0.0
    delta = round(latest_value - median_value, 3)

    if mode == "lower_better":
        if latest_value <= median_value * 0.9:
            status = "good"
        elif latest_value <= median_value * 1.15:
            status = "watch"
        else:
            status = "alert"
        trend = "down" if delta < -0.001 else ("up" if delta > 0.001 else "flat")
    elif mode == "deviation":
        deviation_ratio = abs(delta) / max(abs(median_value), 0.001)
        if deviation_ratio <= 0.1:
            status = "good"
        elif deviation_ratio <= 0.25:
            status = "watch"
        else:
            status = "alert"
        trend = "flat" if abs(delta) <= 0.001 else ("up" if delta > 0 else "down")
    else:
        status = "unknown"
        trend = "flat"

    return {
        "value": round(latest_value, 3),
        "median": round(median_value, 3),
        "delta": delta,
        "trend": trend,
        "status": status,
    }
