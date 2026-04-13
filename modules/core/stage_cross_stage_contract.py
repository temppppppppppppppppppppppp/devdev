"""Bounded helpers for cross-stage contract normalization."""

from __future__ import annotations

import re

OPENING_TRANSITION_DIRECT = "direct_continuation"
OPENING_TRANSITION_EXPLICIT = "explicit_transition"
OPENING_TRANSITION_JUMP = "jump_opening"

_OPENING_TRANSITION_TYPES = frozenset(
    {
        OPENING_TRANSITION_DIRECT,
        OPENING_TRANSITION_EXPLICIT,
        OPENING_TRANSITION_JUMP,
    }
)
_OPENING_TRANSITION_SCENE_MARKERS = (
    "* * *",
    "장면 전환",
    "전환",
    "컷",
    "cut",
    "이동",
    "옮기",
    "걸음을 옮",
    "발을 옮",
    "나서",
    "들어서",
    "빠져나와",
    "도착",
    "한편",
)
_OPENING_TRANSITION_TIME_SHIFT_MARKERS = (
    "다음 날",
    "다음날",
    "이튿날",
    "사흘 후",
    "며칠 후",
    "몇 시간 후",
    "한 시간 후",
    "잠시 후",
    "한참 후",
    "이후",
    "뒤",
)


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


def _extract_opening_scene(payload: dict) -> dict:
    scenes = payload.get("scene_breakdown", {})
    if isinstance(scenes, dict):
        scene_1 = scenes.get("scene_1") or next(iter(scenes.values()), {})
        if isinstance(scene_1, dict):
            return scene_1
    return {}


def _extract_location_area(location: str) -> str:
    text = str(location or "").strip()
    match = re.search(r"^([가-힣]{2,5})", text)
    return match.group(1) if match else ""


def _locations_directly_continuous(prev_loc: str, curr_loc: str) -> bool:
    prev_text = str(prev_loc or "").strip()
    curr_text = str(curr_loc or "").strip()
    if not prev_text or not curr_text:
        return False
    return prev_text == curr_text or prev_text in curr_text or curr_text in prev_text


def _locations_share_area(prev_loc: str, curr_loc: str) -> bool:
    prev_area = _extract_location_area(prev_loc)
    curr_area = _extract_location_area(curr_loc)
    return bool(prev_area and curr_area and prev_area == curr_area)


def _normalize_signal_list(raw_value: object, *, limit: int = 6) -> list[str]:
    if isinstance(raw_value, str):
        raw_items = [raw_value]
    elif isinstance(raw_value, list):
        raw_items = raw_value
    else:
        raw_items = []

    normalized: list[str] = []
    for item in raw_items:
        text = re.sub(r"[^a-z0-9_]+", "_", str(item or "").strip().lower()).strip("_")
        if text and text not in normalized:
            normalized.append(text)
    return normalized[:limit]


def _normalize_opening_transition_type(raw_value: object) -> str:
    text = re.sub(r"[^a-z]+", "_", str(raw_value or "").strip().lower()).strip("_")
    alias_map = {
        "direct": OPENING_TRANSITION_DIRECT,
        "direct_continuation": OPENING_TRANSITION_DIRECT,
        "continuation": OPENING_TRANSITION_DIRECT,
        "same_place_continuation": OPENING_TRANSITION_DIRECT,
        "explicit_transition": OPENING_TRANSITION_EXPLICIT,
        "transition": OPENING_TRANSITION_EXPLICIT,
        "scene_transition": OPENING_TRANSITION_EXPLICIT,
        "cut_transition": OPENING_TRANSITION_EXPLICIT,
        "jump": OPENING_TRANSITION_JUMP,
        "jump_opening": OPENING_TRANSITION_JUMP,
        "time_jump": OPENING_TRANSITION_JUMP,
    }
    return alias_map.get(text, "")


def _extract_declared_opening_transition_type(raw_value: object) -> str:
    if isinstance(raw_value, dict):
        for key in ("type", "transition_type", "opening_type"):
            normalized = _normalize_opening_transition_type(raw_value.get(key))
            if normalized:
                return normalized
        return ""
    return _normalize_opening_transition_type(raw_value)


def _build_opening_scene_text(payload: dict, scene_1: dict) -> str:
    parts: list[str] = []
    for key in ("title", "summary", "goal", "description"):
        text = _compact_text(scene_1.get(key), item_limit=180)
        if text:
            parts.append(text)
    key_events = scene_1.get("key_events", [])
    if isinstance(key_events, list):
        parts.extend(_compact_text(item, item_limit=120) for item in key_events if _compact_text(item, item_limit=120))
    existing_summary = _compact_text((payload.get("opening_transition") or {}).get("summary"), item_limit=180)
    if existing_summary:
        parts.append(existing_summary)
    return "\n".join(part for part in parts if part)


def _has_scene_transition_cue(scene_text: str, *, start_location: str, scene_location: str) -> bool:
    compact = str(scene_text or "").lower()
    if any(marker in compact for marker in _OPENING_TRANSITION_SCENE_MARKERS):
        return True
    if start_location and scene_location and start_location.strip() != scene_location.strip():
        return True
    return False


def _has_time_shift_cue(time_flow: str) -> bool:
    compact = str(time_flow or "").strip()
    if not compact:
        return False
    if "직후" in compact or "곧바로" in compact or "바로" in compact:
        return False
    lowered = compact.lower()
    return any(marker in lowered for marker in _OPENING_TRANSITION_TIME_SHIFT_MARKERS)


def read_declared_opening_transition_type(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    raw_contract = payload.get("opening_transition")
    declared = _extract_declared_opening_transition_type(raw_contract)
    if declared:
        return declared
    return _extract_declared_opening_transition_type(payload.get("opening_transition_type"))


def infer_opening_transition_contract(payload: object, *, prev_blueprint: dict | None = None) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {}

    scene_1 = _extract_opening_scene(payload)
    start_location = str(payload.get("start_location", "") or payload.get("location", "") or "").strip()
    time_flow = str(payload.get("time_flow", "") or "").strip()
    scene_location = str(scene_1.get("location", "") or "").strip()
    prev_payload = prev_blueprint if isinstance(prev_blueprint, dict) else {}
    prev_end_location = str(prev_payload.get("end_location", "") or "").strip()
    prev_time_flow = str(prev_payload.get("time_flow", "") or "").strip()
    opening_anchor_location = start_location or scene_location
    has_prev_anchor = bool(prev_end_location or prev_time_flow)
    same_location = _locations_directly_continuous(prev_end_location, opening_anchor_location)
    same_area_shift = bool(
        prev_end_location
        and opening_anchor_location
        and not same_location
        and _locations_share_area(prev_end_location, opening_anchor_location)
    )
    location_shift = bool(prev_end_location and opening_anchor_location and not same_location)
    time_shift = _has_time_shift_cue(time_flow)
    scene_text = _build_opening_scene_text(payload, scene_1)
    scene_transition_cue = _has_scene_transition_cue(
        scene_text,
        start_location=start_location,
        scene_location=scene_location,
    )
    has_current_anchor = bool(opening_anchor_location or time_flow or scene_text)

    if not has_current_anchor and not has_prev_anchor:
        return {}

    if not has_prev_anchor:
        transition_type = OPENING_TRANSITION_JUMP
    elif same_location and not time_shift:
        transition_type = OPENING_TRANSITION_DIRECT
    elif scene_transition_cue or same_area_shift or (same_location and time_shift):
        transition_type = OPENING_TRANSITION_EXPLICIT
    else:
        transition_type = OPENING_TRANSITION_JUMP

    signals: list[str] = []
    if not has_prev_anchor:
        signals.append("no_prev_anchor")
    if same_location:
        signals.append("same_location_anchor")
    elif same_area_shift:
        signals.append("same_area_shift")
    elif location_shift:
        signals.append("location_shift")
    if time_shift:
        signals.append("time_shift")
    if scene_transition_cue:
        signals.append("scene_transition_cue")

    contract: dict[str, object] = {"type": transition_type}
    if signals:
        contract["signals"] = signals[:6]
    return contract


def apply_opening_transition_contract(payload: object, *, prev_blueprint: dict | None = None) -> dict[str, object]:
    contract = infer_opening_transition_contract(payload, prev_blueprint=prev_blueprint)
    if contract and isinstance(payload, dict):
        payload["opening_transition"] = dict(contract)
    return contract


def resolve_opening_transition_contract(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {}

    raw_contract = payload.get("opening_transition")
    declared_type = _extract_declared_opening_transition_type(raw_contract)
    declared_signals = _normalize_signal_list(
        (raw_contract or {}).get("signals") if isinstance(raw_contract, dict) else []
    )
    inferred = infer_opening_transition_contract(payload)

    if declared_type not in _OPENING_TRANSITION_TYPES:
        return inferred

    resolved = {"type": declared_type}
    if declared_signals:
        resolved["signals"] = declared_signals
    elif inferred.get("signals"):
        resolved["signals"] = list(inferred["signals"])
    return resolved


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
