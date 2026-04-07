"""Shared Stage2 recovery policy helpers for non-wuxia soft-state handling."""

from __future__ import annotations

import re

from modules.core.constants import GenreTypes
from modules.core.genre_schema_builder import is_wuxia

_GENRE_ALIASES: dict[str, str] = {
    "wuxia": GenreTypes.WUXIA,
    "무협": GenreTypes.WUXIA,
    "hunter": GenreTypes.HUNTER,
    "헌터": GenreTypes.HUNTER,
    "investment": GenreTypes.INVESTMENT,
    "투자": GenreTypes.INVESTMENT,
    "fantasy": GenreTypes.FANTASY,
    "판타지": GenreTypes.FANTASY,
    "composer": GenreTypes.COMPOSER,
    "작곡가": GenreTypes.COMPOSER,
    "cooking": GenreTypes.COOKING,
    "요리": GenreTypes.COOKING,
    "alt_history": GenreTypes.ALT_HISTORY,
    "대체역사": GenreTypes.ALT_HISTORY,
    "actor": GenreTypes.ACTOR,
    "배우물": GenreTypes.ACTOR,
    "sports": GenreTypes.SPORTS,
    "스포츠": GenreTypes.SPORTS,
    "medical": GenreTypes.MEDICAL,
    "의학": GenreTypes.MEDICAL,
}

_SOFT_STATE_TOKENS = (
    "신경계 피로",
    "정신적 피로",
    "정신 피로",
    "피로",
    "스트레스",
    "과로",
    "번아웃",
    "burnout",
    "fatigue",
    "stress",
    "overwork",
    "두통",
    "headache",
    "지침",
    "지친",
    "tired",
    "exhausted",
)
_SOFT_STATE_PATTERNS = (
    r"\bfatigue\b",
    r"\bstress\b",
    r"\bburnout\b",
    r"\boverwork\b",
    r"\bheadache\b",
    r"\btired\b",
    r"\bexhausted\b",
)

_HARD_INJURY_TOKENS = (
    "골절",
    "출혈",
    "내상",
    "부상",
    "깁스",
    "붕대",
    "절뚝",
    "탈골",
    "화상",
    "찢",
    "베인",
    "중상",
    "위독",
    "손상",
    "fracture",
    "broken",
    "bleeding",
    "injured",
    "wound",
    "cast",
    "bandage",
    "sprain",
    "cannot move",
)
_HARD_INJURY_PATTERNS = (
    r"\bfracture(?:d)?\b",
    r"\bbroken\b",
    r"\bbleed(?:ing)?\b",
    r"\binjur(?:ed|y)\b",
    r"\bwound(?:ed)?\b",
    r"\bcast\b",
    r"\bbandage(?:d)?\b",
    r"\bsprain(?:ed)?\b",
)

_SOFT_RECOVERY_ACTION_TOKENS = (
    "수면",
    "잠",
    "잠들",
    "식사",
    "먹",
    "샤워",
    "씻",
    "산책",
    "걷",
    "휴식",
    "쉬",
    "대화",
    "통화",
    "술",
    "커피",
    "멍하니",
)
_SOFT_RECOVERY_ACTION_PATTERNS = (
    r"\bsleep\b",
    r"\bslept\b",
    r"\bmeal\b",
    r"\beat\b",
    r"\bate\b",
    r"\bshower\b",
    r"\bwalk(?:ed|ing)?\b",
    r"\brest(?:ed|ing)?\b",
    r"\btalk(?:ed|ing)?\b",
    r"\bdrink(?:ing)?\b",
    r"\bdrank\b",
    r"\bcoffee\b",
)

_HARD_RECOVERY_ACTION_TOKENS = (
    "치료",
    "병원",
    "진료",
    "약",
    "붕대",
    "깁스",
    "입원",
    "휴양",
    "안정",
    "재활",
    "봉합",
)
_HARD_RECOVERY_ACTION_PATTERNS = (
    r"\btreat(?:ed|ment)?\b",
    r"\bhospital\b",
    r"\bclinic\b",
    r"\bmedication\b",
    r"\bbandage(?:d)?\b",
    r"\bcast\b",
    r"\brehab\b",
    r"\brest\b",
)

_VAGUE_RECOVERY_TOKENS = (
    "회복하는 시간",
    "회복의 시간",
    "시간이 지나",
    "버티는 시간",
    "정리하는 시간",
    "최상의 컨디션",
    "멀쩡해져",
)
_VAGUE_RECOVERY_PATTERNS = (
    r"\brecovered over time\b",
    r"\btime passed\b",
    r"\bhad time to recover\b",
    r"\bback to full strength\b",
)


def normalize_genre_type(genre: object) -> str:
    text = str(genre or "").strip().lower()
    return _GENRE_ALIASES.get(text, text)


def _contains_signal(text: object, *, tokens: tuple[str, ...], patterns: tuple[str, ...]) -> bool:
    lowered = str(text or "").lower()
    if not lowered:
        return False
    return any(token in lowered for token in tokens) or any(re.search(pattern, lowered) for pattern in patterns)


def has_soft_non_wuxia_state_signal(text: object) -> bool:
    lowered = str(text or "").lower()
    if not lowered or has_hard_injury_signal(lowered):
        return False
    return _contains_signal(lowered, tokens=_SOFT_STATE_TOKENS, patterns=_SOFT_STATE_PATTERNS)


def has_hard_injury_signal(text: object) -> bool:
    return _contains_signal(text, tokens=_HARD_INJURY_TOKENS, patterns=_HARD_INJURY_PATTERNS)


def has_soft_recovery_action(text: object) -> bool:
    return _contains_signal(text, tokens=_SOFT_RECOVERY_ACTION_TOKENS, patterns=_SOFT_RECOVERY_ACTION_PATTERNS)


def has_hard_recovery_action(text: object) -> bool:
    return _contains_signal(text, tokens=_HARD_RECOVERY_ACTION_TOKENS, patterns=_HARD_RECOVERY_ACTION_PATTERNS)


def has_vague_recovery_signal(text: object) -> bool:
    return _contains_signal(text, tokens=_VAGUE_RECOVERY_TOKENS, patterns=_VAGUE_RECOVERY_PATTERNS)


def split_injury_entries_for_genre(injuries: list[dict], genre: object) -> tuple[list[dict], list[dict]]:
    genre_type = normalize_genre_type(genre)
    if is_wuxia(genre_type):
        return [inj for inj in injuries if isinstance(inj, dict)], []

    hard_injuries: list[dict] = []
    soft_states: list[dict] = []
    for injury in injuries:
        if not isinstance(injury, dict):
            continue
        text = " ".join(
            str(injury.get(key, "") or "")
            for key in ("name", "severity", "recovery_method")
        )
        if has_soft_non_wuxia_state_signal(text):
            soft_states.append(injury)
            continue
        hard_injuries.append(injury)
    return hard_injuries, soft_states
