"""
Bounded Stage3 prompt-envelope helpers.
"""

from __future__ import annotations

import re
from typing import Any

from modules.core.constants import ContextLimits, smart_truncate
from modules.core.context_advisor import build_context_budget_ledger

_STAGE3_ARCHIVE_APPENDIX_DEFAULT_CAP = 120_000
_STAGE3_CARRYOVER_ORDER_FAMILIES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("gold", ("금 선물", "금 시장", "금값", "골드", "gold", "금 관련", "금 데이터"), "금"),
    ("oil", ("wti", "유가", "원유", "오일", "브렌트"), "유가/원유"),
    ("equity", ("코스피", "코스닥", "증시", "주식", "종목"), "주식"),
    ("fx", ("환율", "외환", "환시장", "달러", "엔화", "fx"), "환율/외환"),
    ("crypto", ("비트코인", "이더리움", "가상자산", "코인", "btc", "eth"), "가상자산"),
)
_STAGE3_CARRYOVER_ORDER_SIGNALS: tuple[str, ...] = (
    "지시",
    "자료",
    "보고",
    "보고서",
    "정리",
    "조사",
    "챙겨",
    "내일 아침",
    "내일까지",
    "열리기 전까지",
)


def _fit_stage3_prompt_lane(text: str, *, max_chars: int, head_ratio: float = 0.55) -> str:
    if len(text) <= max_chars:
        return text
    head_chars = max(0, min(int(max_chars * head_ratio), max_chars - 80))
    return smart_truncate(text, max_chars=max_chars, head_chars=head_chars)


def build_stage3_recent_carryover_digest(
    prev_manuscripts_text: str,
    *,
    max_items: int = 4,
) -> str:
    raw = str(prev_manuscripts_text or "")
    if not raw:
        return ""

    block_pattern = re.compile(r"━━━\s*제(\d+)화 원고\s*━━━\s*\n", re.MULTILINE)
    matches = list(block_pattern.finditer(raw))
    if not matches:
        return ""

    carryover_rows: list[str] = []
    seen_keys: set[tuple[str, str]] = set()
    recent_matches = matches[-4:]
    for index, match in enumerate(recent_matches):
        ep_num = match.group(1)
        block_start = match.end()
        block_end = recent_matches[index + 1].start() if index + 1 < len(recent_matches) else len(raw)
        block_text = raw[block_start:block_end].strip()
        if not block_text:
            continue

        sentences = [
            part.strip()
            for part in re.split(  # utf8-hygiene: allow-line regex metacharacters (?<=...).
                r"(?<=[.!?。！？])\s+|\n+",  # utf8-hygiene: allow-line regex metacharacters (?<=...).
                block_text,
            )
            if part and part.strip()
        ]
        if not sentences:
            sentences = [block_text]

        windows: list[str] = []
        for sentence_index in range(len(sentences)):
            for width in (1, 2, 3):
                window = " ".join(sentences[sentence_index : sentence_index + width]).strip()
                if window:
                    windows.append(window)

        for window in windows:
            compact = " ".join(window.split()).strip()
            if not compact:
                continue
            lowered = compact.casefold()
            if not any(signal in lowered for signal in _STAGE3_CARRYOVER_ORDER_SIGNALS):
                continue
            for family_key, tokens, label in _STAGE3_CARRYOVER_ORDER_FAMILIES:
                if not any(token.casefold() in lowered for token in tokens):
                    continue
                seen_key = (ep_num, family_key)
                if seen_key in seen_keys:
                    continue
                seen_keys.add(seen_key)
                carryover_rows.append(
                    f"- 제{ep_num}화 carryover order ({label}): {compact[:160]} "
                    "(이미 내려진 지시/대기 과업이면 새 지시처럼 반복하지 말 것)"
                )
                break
            if len(carryover_rows) >= max_items:
                return "\n".join(carryover_rows)

    return "\n".join(carryover_rows[:max_items])


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
