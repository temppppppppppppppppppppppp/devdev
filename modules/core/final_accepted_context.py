"""Final-accepted episode context access helpers.

This module keeps downstream readers from promoting provisional lifecycle rows
or rejected attempts into accepted manuscript context by accident.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


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


def load_final_accepted_manuscript_text(db: object, ep_num: int) -> str:
    row = load_final_accepted_manuscript_row(db, ep_num)
    return _content_from_row(row)
