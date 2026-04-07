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

_HARD_PENDING_ACTION_TOKENS = (
    "도망",
    "탈출",
    "추격",
    "반격",
    "공격",
    "응급",
    "구조",
    "구출",
    "치료",
    "병원",
    "수술",
    "해독",
    "은신",
    "잠입",
    "추적",
    "저지",
    "인질",
    "폭발",
    "도주",
    "escape",
    "flee",
    "chase",
    "counterattack",
    "attack",
    "rescue",
    "emergency",
    "treat",
    "hospital",
    "surgery",
    "antidote",
    "hide",
    "infiltrate",
    "pursuit",
)
_HARD_PENDING_ACTION_PATTERNS = (
    r"\bescape\b",
    r"\bflee\b",
    r"\bchase\b",
    r"\bcounterattack\b",
    r"\battack\b",
    r"\brescue\b",
    r"\bemergency\b",
    r"\bsurgery\b",
    r"\bantidote\b",
    r"\binfiltrat(?:e|ion)\b",
)

_ROUTINE_PENDING_ACTION_TOKENS = (
    "전화",
    "통화",
    "회의",
    "미팅",
    "보고",
    "검토",
    "확인",
    "정리",
    "출근",
    "퇴근",
    "귀가",
    "현관",
    "복도",
    "사무실",
    "서재",
    "자리",
    "이동",
    "식사",
    "휴식",
    "수면",
    "잠",
    "샤워",
    "커피",
    "메일",
    "서류",
    "업무",
    "준비",
    "call",
    "phone",
    "meeting",
    "review",
    "report",
    "check",
    "organize",
    "commute",
    "office",
    "hallway",
    "door",
    "meal",
    "rest",
    "sleep",
    "shower",
    "coffee",
    "email",
    "document",
    "prepare",
    "move",
)
_ROUTINE_PENDING_ACTION_PATTERNS = (
    r"\bcall\b",
    r"\bphone\b",
    r"\bmeeting\b",
    r"\breview\b",
    r"\breport\b",
    r"\bcheck\b",
    r"\borganize\b",
    r"\bcommut(?:e|ing)\b",
    r"\boffice\b",
    r"\bhallway\b",
    r"\bmeal\b",
    r"\brest\b",
    r"\bsleep\b",
    r"\bshower\b",
    r"\bcoffee\b",
    r"\bemail\b",
    r"\bprepare\b",
    r"\bmove\b",
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


def classify_chain_link_physical_state(text: object, genre: object) -> str:
    normalized_text = str(text or "").strip()
    if not normalized_text or normalized_text == "정상":
        return "normal"

    genre_type = normalize_genre_type(genre)
    if is_wuxia(genre_type):
        return "hard"
    if has_hard_injury_signal(normalized_text):
        return "hard"
    if has_soft_non_wuxia_state_signal(normalized_text):
        return "soft"
    return "hard"


def _normalize_pending_action_items(actions: object) -> list[str]:
    if isinstance(actions, list):
        items = [str(item or "").strip() for item in actions]
        return [item for item in items if item]
    if isinstance(actions, str):
        text = str(actions).strip()
        if not text:
            return []
        parts = [part.strip() for part in re.split(r"[,\n/]+", text) if part.strip()]
        return parts if parts else [text]
    return []


def _is_hard_pending_action(text: object) -> bool:
    normalized_text = str(text or "").strip()
    if not normalized_text:
        return False
    if has_hard_injury_signal(normalized_text) or has_hard_recovery_action(normalized_text):
        return True
    return _contains_signal(
        normalized_text,
        tokens=_HARD_PENDING_ACTION_TOKENS,
        patterns=_HARD_PENDING_ACTION_PATTERNS,
    )


def _is_routine_pending_action(text: object) -> bool:
    normalized_text = str(text or "").strip()
    if not normalized_text:
        return False
    if _is_hard_pending_action(normalized_text):
        return False
    if has_soft_recovery_action(normalized_text) or has_vague_recovery_signal(normalized_text):
        return True
    return _contains_signal(
        normalized_text,
        tokens=_ROUTINE_PENDING_ACTION_TOKENS,
        patterns=_ROUTINE_PENDING_ACTION_PATTERNS,
    )


def split_chain_link_pending_actions(actions: object, genre: object) -> tuple[list[str], list[str]]:
    items = _normalize_pending_action_items(actions)
    if not items:
        return [], []

    genre_type = normalize_genre_type(genre)
    if is_wuxia(genre_type):
        return items, []

    hard_actions: list[str] = []
    soft_actions: list[str] = []
    for action in items:
        if _is_routine_pending_action(action):
            soft_actions.append(action)
            continue
        hard_actions.append(action)
    return hard_actions, soft_actions


def normalize_chain_link_for_genre(chain_link: object, genre: object) -> dict[str, object]:
    payload = dict(chain_link) if isinstance(chain_link, dict) else {}
    if not payload:
        return {}

    hard_actions, soft_actions = split_chain_link_pending_actions(payload.get("pending_actions"), genre)
    if hard_actions:
        payload["pending_actions"] = hard_actions
    else:
        payload["pending_actions"] = []
    if soft_actions:
        payload["soft_pending_actions"] = soft_actions
    else:
        payload.pop("soft_pending_actions", None)

    physical_state = str(payload.get("physical_state") or "").strip()
    physical_state_binding = classify_chain_link_physical_state(physical_state, genre)
    if physical_state_binding == "soft":
        payload["soft_physical_state"] = physical_state
        payload["physical_state"] = "정상"
    else:
        payload.pop("soft_physical_state", None)
        if physical_state_binding == "normal":
            payload["physical_state"] = "정상"
        elif physical_state:
            payload["physical_state"] = physical_state

    return payload
