"""
Shared tactical-intrusion contract helpers for Stage3 producer/validator parity.
"""

from __future__ import annotations

import re

TACTICAL_INTRUSION_ENTRY_MARKERS = (
    "취객",
    "난입",
    "들이닥",
    "들이닥치",
    "무단침입",
    "괴한",
    "습격",
    "침입자",
    "철문",
    "심부름센터",
)

TACTICAL_INTRUSION_CONFLICT_MARKERS = (
    "멱살",
    "멱살을 잡",
    "결박",
    "제압",
    "처리",
    "대응",
    "차단",
    "쫓아낸",
    "도망치",
    "위협",
    "협박",
    "박살",
    "쇠파이프",
    "쇠지렛대",
    "군화",
    "팔목을 비틀",
    "팔을 비틀",
    "손목을 잡아채",
    "손목을 잡아챔",
    "주먹을 들이밀",
    "주먹을 들이밂",
    "입막음",
    "입막음을 강요",
    "강요",
    "강박",
    "목을 조르",
    "목덜미를 잡",
    "벽으로 밀치",
    "의자로 가로막",
)

_TACTICAL_INTRUSION_PROXIMITY_ENTRY_MARKERS = (
    "취객",
    "난입",
    "들이닥",
    "들이닥치",
    "무단침입",
    "괴한",
    "습격",
    "침입자",
    "심부름센터",
)

_TACTICAL_INTRUSION_PROXIMITY_CONFLICT_MARKERS = frozenset(
    {
        "멱살을 잡",
        "제압",
        "대응",
        "차단",
        "위협",
        "협박",
        "팔목을 비틀",
        "팔을 비틀",
        "손목을 잡아채",
        "손목을 잡아챔",
        "주먹을 들이밀",
        "주먹을 들이밂",
        "입막음",
        "입막음을 강요",
        "강요",
        "강박",
        "목을 조르",
        "목덜미를 잡",
        "벽으로 밀치",
        "의자로 가로막",
    }
)

_TACTICAL_SENTENCE_SPLIT_RE = re.compile(r"(?:\n+|(?<=[.!?。！？])\s+)")


def _collapse_whitespace(text: str) -> str:
    return " ".join(str(text or "").split()).casefold().strip()


def _split_tactical_sentences(text: str) -> list[str]:
    normalized = str(text or "").replace("\r\n", "\n").replace("\r", "\n").casefold()
    if not normalized.strip():
        return []
    sentences = [
        _collapse_whitespace(chunk)
        for chunk in _TACTICAL_SENTENCE_SPLIT_RE.split(normalized)
        if _collapse_whitespace(chunk)
    ]
    if sentences:
        return sentences
    fallback = _collapse_whitespace(normalized)
    return [fallback] if fallback else []


def _has_nearby_entry(sentences: list[str], conflict_marker: str, *, window: int = 5) -> bool:
    if not sentences:
        return False
    marker = conflict_marker.casefold()
    for idx, sentence in enumerate(sentences):
        if marker not in sentence:
            continue
        start = max(0, idx - window)
        end = min(len(sentences), idx + window + 1)
        window_text = " ".join(sentences[start:end])
        if any(entry.casefold() in window_text for entry in _TACTICAL_INTRUSION_PROXIMITY_ENTRY_MARKERS):
            return True
    return False


def detect_tactical_intrusion_signature(text: str) -> dict[str, list[str]]:
    """Detect unauthorized physical-threat intrusion signatures in a text surface."""
    flat_text = _collapse_whitespace(text)
    if not flat_text:
        return {}

    entry_hits = [marker for marker in TACTICAL_INTRUSION_ENTRY_MARKERS if marker.casefold() in flat_text]
    if not entry_hits:
        return {}

    sentences = _split_tactical_sentences(text)
    conflict_hits: list[str] = []
    for marker in TACTICAL_INTRUSION_CONFLICT_MARKERS:
        marker_folded = marker.casefold()
        if marker_folded not in flat_text:
            continue
        if marker in _TACTICAL_INTRUSION_PROXIMITY_CONFLICT_MARKERS and not _has_nearby_entry(
            sentences, marker
        ):
            continue
        conflict_hits.append(marker)

    if not conflict_hits:
        return {}

    return {"entry_hits": entry_hits, "conflict_hits": conflict_hits}


def collect_tactical_surface_text(candidate: dict | None) -> str:
    parts: list[str] = []
    if not isinstance(candidate, dict):
        return ""

    integrated = str(candidate.get("integrated_scenario", "") or "").strip()
    if integrated:
        parts.append(integrated)

    scenes = candidate.get("scene_breakdown", {})
    if isinstance(scenes, dict):
        scene_iter = scenes.values()
    elif isinstance(scenes, list):
        scene_iter = scenes
    else:
        scene_iter = []

    for scene in scene_iter:
        if not isinstance(scene, dict):
            continue
        for key in ("title", "summary", "goal", "description", "location"):
            value = str(scene.get(key, "") or "").strip()
            if value:
                parts.append(value)
        raw_events = scene.get("key_events", [])
        if isinstance(raw_events, str):
            raw_events = [raw_events]
        if isinstance(raw_events, list):
            parts.extend(str(item or "").strip() for item in raw_events if str(item or "").strip())
        characters = scene.get("characters", [])
        if isinstance(characters, str):
            characters = [characters]
        if isinstance(characters, list):
            parts.extend(str(item or "").strip() for item in characters if str(item or "").strip())

    return "\n".join(parts)
