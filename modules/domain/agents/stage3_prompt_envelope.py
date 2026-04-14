"""
Bounded Stage3 prompt-envelope helpers.
"""

from __future__ import annotations

from typing import Any

from modules.core.constants import ContextLimits, smart_truncate
from modules.core.context_advisor import build_context_budget_ledger

_STAGE3_ARCHIVE_APPENDIX_DEFAULT_CAP = 120_000


def _fit_stage3_prompt_lane(text: str, *, max_chars: int, head_ratio: float = 0.55) -> str:
    if len(text) <= max_chars:
        return text
    head_chars = max(0, min(int(max_chars * head_ratio), max_chars - 80))
    return smart_truncate(text, max_chars=max_chars, head_chars=head_chars)


def build_stage3_archive_appendix(
    prev_manuscripts_text: str,
    *,
    max_chars: int = _STAGE3_ARCHIVE_APPENDIX_DEFAULT_CAP,
) -> tuple[str, dict[str, Any]]:
    raw = str(prev_manuscripts_text or "")
    configured_cap = max(0, int(max_chars or 0))
    if not raw:
        return "", {
            "enabled": False,
            "configured_cap": configured_cap,
            "raw_chars": 0,
            "consumed_chars": 0,
            "dropped_chars": 0,
            "demoted": False,
        }

    appendix_text = raw
    if configured_cap > 0 and len(appendix_text) > configured_cap:
        appendix_text = _fit_stage3_prompt_lane(appendix_text, max_chars=configured_cap)
    consumed_chars = len(appendix_text)
    dropped_chars = max(0, len(raw) - consumed_chars)
    return appendix_text, {
        "enabled": True,
        "configured_cap": configured_cap,
        "raw_chars": len(raw),
        "consumed_chars": consumed_chars,
        "dropped_chars": dropped_chars,
        "demoted": consumed_chars < len(raw),
    }


def build_stage3_prompt_envelope_meta(
    *,
    constraints_str: str = "",
    arc_focus: str = "",
    prev_info: str = "",
    hud_context: str = "",
    feedback_context: str = "",
    archive_appendix_meta: dict[str, Any] | None = None,
    max_context_chars: int | None = None,
) -> dict[str, Any]:
    lane_chars = {
        "constraints": len(str(constraints_str or "")),
        "arc_focus": len(str(arc_focus or "")),
        "prev_info": len(str(prev_info or "")),
        "hud_context": len(str(hud_context or "")),
        "feedback_context": len(str(feedback_context or "")),
    }
    shared_context_chars = (
        lane_chars["constraints"] + lane_chars["arc_focus"] + lane_chars["prev_info"] + lane_chars["hud_context"]
    )
    total_chars = shared_context_chars + lane_chars["feedback_context"]
    envelope_cap = max(0, int(max_context_chars or ContextLimits.MAX_CONTEXT_CHARS or 0))
    appendix_meta = dict(archive_appendix_meta or {})
    dropped_chars = max(0, int(appendix_meta.get("dropped_chars") or 0))
    overflow_chars = max(0, total_chars - envelope_cap) if envelope_cap > 0 else 0
    headroom_chars = max(0, envelope_cap - total_chars) if envelope_cap > 0 else 0
    dominant_lanes = [
        {"lane": lane, "chars": chars}
        for lane, chars in sorted(lane_chars.items(), key=lambda item: item[1], reverse=True)
        if chars > 0
    ][:3]
    return {
        "lane_chars": lane_chars,
        "shared_context_chars": shared_context_chars,
        "total_chars": total_chars,
        "dominant_lanes": dominant_lanes,
        "archive_appendix": appendix_meta,
        "budget_ledger": build_context_budget_ledger(
            stage="stage3",
            configured_cap=envelope_cap,
            fallback_cap=envelope_cap,
            effective_cap=envelope_cap,
            consumed_chars=total_chars,
            dropped_chars=dropped_chars,
            overflow_chars=overflow_chars,
            headroom_chars=headroom_chars,
            budget_bucket="stage3.prompt_envelope_total_chars",
        ),
    }
