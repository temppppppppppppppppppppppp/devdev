"""Final-accepted episode context access helpers.

This module keeps downstream readers from promoting provisional lifecycle rows
or rejected attempts into accepted manuscript context by accident.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

FINAL_ACCEPTED_STAGE_VERDICTS = frozenset({"PASS", "PASS_WITH_FIX", "PASS_WITH_WARNING"})
NON_FINAL_STAGE_VERDICTS = frozenset({"REJECT", "FAILED", "ERROR", "SETTLEMENT_FAILED"})
RETRY_HYDRATABLE_STAGE_VERDICTS = frozenset({"REJECT"})


def normalize_stage_verdict(value: object) -> str:
    return str(value or "").strip().upper()


def is_final_accepted_stage_verdict(value: object) -> bool:
    return normalize_stage_verdict(value) in FINAL_ACCEPTED_STAGE_VERDICTS


def is_non_final_stage_verdict(value: object) -> bool:
    return normalize_stage_verdict(value) in NON_FINAL_STAGE_VERDICTS


def is_retry_hydratable_stage_verdict(value: object) -> bool:
    return normalize_stage_verdict(value) in RETRY_HYDRATABLE_STAGE_VERDICTS


def _content_from_row(row: object) -> str:
    if isinstance(row, Mapping):
        return str(row.get("content") or row.get("corrected_manuscript") or row.get("manuscript") or "")
    if isinstance(row, str):
        return row
    return ""


def has_final_accepted_context_accessor(db: object) -> bool:
    if db is None:
        return False
    class_attr = getattr(type(db), "get_final_accepted_episode_context", None)
    if callable(class_attr):
        return True
    instance_attr = getattr(db, "get_final_accepted_episode_context", None)
    if not callable(instance_attr):
        return False
    module_name = str(type(instance_attr).__module__ or "")
    return not module_name.startswith("unittest.mock")


def load_final_accepted_manuscript_row(db: object, ep_num: int) -> dict[str, Any] | None:
    """Return the best final-accepted manuscript row for an episode.

    New DB implementations can expose ``get_final_accepted_episode_context``.
    Legacy mocks and older DBs fall back to ``get_manuscript`` so focused tests
    and old projects continue to run, but the source is explicit when available.
    """

    if db is None:
        return None
    try:
        episode = int(ep_num or 0)
    except (TypeError, ValueError):
        return None
    if episode <= 0:
        return None

    context_getter = getattr(db, "get_final_accepted_episode_context", None)
    if has_final_accepted_context_accessor(db) and callable(context_getter):
        try:
            context = context_getter(episode, stage=4)
        except TypeError:
            context = context_getter(episode)
        except Exception:
            context = None
        if isinstance(context, Mapping):
            content = _content_from_row(context)
            if content:
                return {
                    "ep_num": episode,
                    "title": str(context.get("title") or ""),
                    "content": content,
                    "final_context_status": str(context.get("authority_status") or ""),
                    "final_context_source": str(context.get("source_kind") or ""),
                    "content_hash": str(context.get("content_hash") or ""),
                    "manuscript_created_at": str(context.get("manuscript_created_at") or ""),
                }
            if str(context.get("authority_status") or "") == "blocked_by_non_final_stage4_attempt":
                return None

    getter = getattr(db, "get_manuscript", None)
    if not callable(getter):
        return None
    try:
        row = getter(episode)
    except Exception:
        return None
    content = _content_from_row(row)
    if not content:
        return None
    if isinstance(row, Mapping):
        result = dict(row)
    else:
        result = {"ep_num": episode, "content": content}
    result.setdefault("ep_num", episode)
    result.setdefault("final_context_status", "legacy_manuscript_fallback")
    result.setdefault("final_context_source", "get_manuscript")
    return result


def load_final_accepted_manuscript_rows(db: object, start_ep: int, end_ep: int) -> list[dict[str, Any]]:
    """Return final-accepted manuscript rows for ``[start_ep, end_ep)``.

    The helper keeps bulk readers on the same authority surface as single-episode
    readers. It intentionally omits blocked/non-final episodes instead of
    falling back to raw manuscript rows after an authority accessor has rejected
    the episode.
    """

    if db is None:
        return []
    try:
        start = int(start_ep or 0)
        end = int(end_ep or 0)
    except (TypeError, ValueError):
        return []
    if start <= 0 or end <= start:
        return []

    range_getter = getattr(db, "get_final_accepted_episode_context_range", None)
    if callable(range_getter):
        try:
            rows = range_getter(start, end)
        except TypeError:
            rows = range_getter(start_ep=start, end_ep=end)
        except Exception:
            rows = []
        if isinstance(rows, list):
            normalized: list[dict[str, Any]] = []
            for row in rows:
                if not isinstance(row, Mapping):
                    continue
                content = _content_from_row(row)
                if not content:
                    continue
                normalized.append(
                    {
                        "ep_num": int(row.get("ep_num") or 0),
                        "title": str(row.get("title") or ""),
                        "content": content,
                        "final_context_status": str(
                            row.get("authority_status") or row.get("final_context_status") or ""
                        ),
                        "final_context_source": str(row.get("source_kind") or row.get("final_context_source") or ""),
                        "content_hash": str(row.get("content_hash") or ""),
                        "manuscript_created_at": str(row.get("manuscript_created_at") or row.get("created_at") or ""),
                    }
                )
            return [row for row in normalized if start <= int(row.get("ep_num") or 0) < end]

    return [row for ep in range(start, end) if (row := load_final_accepted_manuscript_row(db, ep)) is not None]


def load_final_accepted_manuscript_text(db: object, ep_num: int) -> str:
    row = load_final_accepted_manuscript_row(db, ep_num)
    return _content_from_row(row)
