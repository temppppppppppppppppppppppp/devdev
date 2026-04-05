"""Deterministic continuity pin fixes for Stage 3/4 handoff."""

from __future__ import annotations

import copy
import json
import re
from typing import Any

_TIME_BUCKET_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"(즉시|당일)", "same_day"),
    (r"(다음 날(?:\s*[가-힣]+)?|익일)", "next_day"),
    (r"(며칠 후|수일 후)", "few_days"),
    (r"(일주일 후|1주일 후|1주 후)", "one_week"),
    (r"(약\s*2주 후|2주 후|이주 후|보름 후)", "two_weeks"),
    (r"(한 달 후|1개월 후|몇 달 후)", "month_plus"),
)

_QUOTED_TOKEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r'"([^"\n]{2,40})"'),
    re.compile(r"“([^”\n]{2,40})”"),
    re.compile(r"‘([^’\n]{2,40})’"),
    re.compile(r"'([^'\n]{2,40})'"),
    re.compile(r"「([^」\n]{2,40})」"),
    re.compile(r"『([^』\n]{2,40})』"),
)

_FATHER_CALL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"아버지"),
    re.compile(r"회장"),
    re.compile(r"어디\s+가느냐"),
)

_NONSTOP_EXIT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"멈추지\s+않"),
    re.compile(r"걸음(?:을)?\s+멈추지\s+않"),
    re.compile(r"현관문(?:을)?\s+향해\s+나아"),
    re.compile(r"등\s*뒤로\s+흘려보냈"),
    re.compile(r"손잡이(?:를)?\s+단단히\s+움켜쥐"),
    re.compile(r"외면했"),
    re.compile(r"무시했"),
)

_OPENING_REVERSAL_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"걸음(?:을)?\s+멈췄"), "걸음을 멈춤"),
    (re.compile(r"몸을\s+돌"), "몸을 돌림"),
    (re.compile(r"마주\s+보"), "아버지를 마주 봄"),
    (re.compile(r"서재(?:로)?\s+와라"), "서재 호출"),
    (re.compile(r"서재(?:를)?\s+향해"), "서재 이동"),
    (re.compile(r"뒤를\s+따라"), "아버지 뒤를 따름"),
)


def _coerce_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "content" in value:
            return _coerce_text(value.get("content", ""))
        if "corrected_manuscript" in value:
            return _coerce_text(value.get("corrected_manuscript", ""))
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return str(value)


def _collect_string_values(node: Any) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, list):
        values: list[str] = []
        for item in node:
            values.extend(_collect_string_values(item))
        return values
    if isinstance(node, dict):
        values: list[str] = []
        for value in node.values():
            values.extend(_collect_string_values(value))
        return values
    return []


def _extract_time_surface(text: str) -> tuple[str, str]:
    for pattern, bucket in _TIME_BUCKET_PATTERNS:
        match = re.search(pattern, text or "")
        if match:
            return bucket, match.group(1)
    return "", ""


def _extract_quoted_tokens(text: str) -> list[str]:
    seen: list[str] = []
    for regex in _QUOTED_TOKEN_PATTERNS:
        for token in regex.findall(text or ""):
            cleaned = " ".join(str(token).split()).strip()
            if len(cleaned) < 2:
                continue
            if cleaned not in seen:
                seen.append(cleaned)
    return seen


def _replace_in_structure(node: Any, replacements: dict[str, str]) -> Any:
    if isinstance(node, str):
        updated = node
        for before, after in replacements.items():
            updated = updated.replace(before, after)
        return updated
    if isinstance(node, list):
        return [_replace_in_structure(item, replacements) for item in node]
    if isinstance(node, dict):
        return {key: _replace_in_structure(value, replacements) for key, value in node.items()}
    return node


def _find_first_match_surface(text: str, patterns: tuple[re.Pattern[str], ...]) -> str:
    for regex in patterns:
        match = regex.search(text or "")
        if match:
            return match.group(0)
    return ""


def _collect_reversal_surfaces(text: str) -> list[str]:
    surfaces: list[str] = []
    for regex, label in _OPENING_REVERSAL_PATTERNS:
        if regex.search(text or "") and label not in surfaces:
            surfaces.append(label)
    return surfaces


def apply_continuity_pins(
    blueprint: dict[str, Any],
    *,
    previous_published_text: str = "",
    arc_tactical_text: str = "",
) -> dict[str, Any]:
    """Patch deterministic handoff drift using previous text and arc cues."""
    if not isinstance(blueprint, dict):
        return {"blueprint": blueprint, "changes": [], "unresolved": []}

    patched = copy.deepcopy(blueprint)
    changes: list[dict[str, str]] = []
    unresolved: list[dict[str, str]] = []
    replacements: dict[str, str] = {}

    blueprint_text = "\n".join(_collect_string_values(blueprint))
    source_text = _coerce_text(previous_published_text) or _coerce_text(arc_tactical_text)

    source_quoted = _extract_quoted_tokens(source_text)
    blueprint_quoted = _extract_quoted_tokens(blueprint_text)

    if len(source_quoted) == 1 and blueprint_quoted:
        expected = source_quoted[0]
        mismatched = [token for token in blueprint_quoted if token != expected]
        if len(mismatched) == 1 and expected not in blueprint_quoted:
            replacements[mismatched[0]] = expected
            changes.append(
                {
                    "type": "proper_noun_pin",
                    "before": mismatched[0],
                    "after": expected,
                }
            )
        elif expected not in blueprint_quoted and mismatched:
            unresolved.append(
                {
                    "type": "proper_noun_pin",
                    "expected": expected,
                    "observed": ", ".join(mismatched[:3]),
                }
            )

    _, source_time_surface = _extract_time_surface(_coerce_text(arc_tactical_text) or source_text)
    _, blueprint_time_surface = _extract_time_surface(blueprint_text)
    if source_time_surface and blueprint_time_surface and source_time_surface != blueprint_time_surface:
        replacements[blueprint_time_surface] = source_time_surface
        changes.append(
            {
                "type": "elapsed_time_pin",
                "before": blueprint_time_surface,
                "after": source_time_surface,
            }
        )

    prev_tail = _coerce_text(previous_published_text)[-2000:]
    blueprint_head = blueprint_text[:4000]
    nonstop_surface = _find_first_match_surface(prev_tail, _NONSTOP_EXIT_PATTERNS)
    father_surface_prev = _find_first_match_surface(prev_tail, _FATHER_CALL_PATTERNS)
    father_surface_opening = _find_first_match_surface(blueprint_head, _FATHER_CALL_PATTERNS)
    opening_reversal_surfaces = _collect_reversal_surfaces(blueprint_head)
    if nonstop_surface and father_surface_prev and father_surface_opening and len(opening_reversal_surfaces) >= 2:
        changes.append(
            {
                "type": "opening_action_continuity_pin",
                "before": nonstop_surface,
                "after": "explicit transition or continued exit",
                "expected": "직전 화 엔딩에서 이미 이어진 이탈 동선을 유지하거나 재진입/전환을 명시해야 함",
                "observed": ", ".join(opening_reversal_surfaces[:3]),
            }
        )

    if replacements:
        patched = _replace_in_structure(patched, replacements)

    return {"blueprint": patched, "changes": changes, "unresolved": unresolved}
