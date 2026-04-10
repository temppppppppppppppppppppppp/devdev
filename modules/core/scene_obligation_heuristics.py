from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from modules.core.constants import ManuscriptLimits

_SCENE_TEXT_FIELDS = (
    "title",
    "goal",
    "summary",
    "description",
    "purpose",
    "conflict",
    "opening_anchor",
    "closing_hook",
    "ending_hook",
)
_SCENE_LIST_FIELDS = (
    "key_events",
    "required_beats",
    "must_include",
    "obligations",
    "core_beats",
    "turning_points",
)
_GENERIC_TOKENS = {
    "scene",
    "씬",
    "장면",
    "전개",
    "내용",
    "상황",
    "사건",
    "진행",
    "이후",
    "이번",
    "다음",
    "마지막",
    "핵심",
    "의무",
}


@dataclass(frozen=True)
class SceneKeywordPacket:
    scene_id: str
    keywords: tuple[str, ...]
    emphasis_keywords: tuple[str, ...]


@dataclass(frozen=True)
class BlueprintSceneProfile:
    scene_count: int
    total_keywords: int
    tail_keyword_count: int
    packets: tuple[SceneKeywordPacket, ...]


@dataclass(frozen=True)
class ManuscriptSceneProfile:
    scene_count: int
    total_keywords: int
    matched_keywords: int
    overall_ratio: float
    reflected_scenes: int
    tail_scene_reflected: bool
    weak_scenes: tuple[str, ...]


def _extract_keywords(text: str, *, max_terms: int) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        return []
    keywords: list[str] = []
    seen: set[str] = set()
    for token in re.findall(r"[\w가-힣]{2,}", text):
        lowered = token.lower()
        if lowered in seen or lowered in _GENERIC_TOKENS:
            continue
        seen.add(lowered)
        keywords.append(token)
        if len(keywords) >= max_terms:
            break
    return keywords


def build_blueprint_scene_profile(blueprint: dict[str, Any]) -> BlueprintSceneProfile:
    scene_breakdown = blueprint.get("scene_breakdown", {})
    if not isinstance(scene_breakdown, dict) or not scene_breakdown:
        return BlueprintSceneProfile(scene_count=0, total_keywords=0, tail_keyword_count=0, packets=())

    packets: list[SceneKeywordPacket] = []
    total_keywords = 0

    for scene_id, scene_data in scene_breakdown.items():
        text_parts: list[str] = []
        emphasis_parts: list[str] = []

        if isinstance(scene_data, dict):
            for field in _SCENE_TEXT_FIELDS:
                value = scene_data.get(field)
                if isinstance(value, str) and value.strip():
                    text_parts.append(value)
            for field in _SCENE_LIST_FIELDS:
                value = scene_data.get(field)
                if isinstance(value, list | tuple):
                    emphasis_parts.extend(str(item) for item in value if str(item).strip())
        else:
            text_parts.append(str(scene_data))

        emphasis_keywords = tuple(_extract_keywords(" ".join(emphasis_parts), max_terms=3))
        keywords = tuple(_extract_keywords(" ".join(emphasis_parts + text_parts), max_terms=6))
        total_keywords += len(keywords)
        packets.append(
            SceneKeywordPacket(
                scene_id=str(scene_id),
                keywords=keywords,
                emphasis_keywords=emphasis_keywords,
            )
        )

    tail_keyword_count = len(packets[-1].keywords) if packets else 0
    return BlueprintSceneProfile(
        scene_count=len(scene_breakdown),
        total_keywords=total_keywords,
        tail_keyword_count=tail_keyword_count,
        packets=tuple(packets),
    )


def estimate_scene_flex_budget(scene_count: int, total_keywords: int = 0, tail_keyword_count: int = 0) -> int:
    if scene_count <= 0:
        return 12000
    if scene_count == 1:
        return 2200 + (200 if tail_keyword_count >= 3 else 0)

    scene_budget = scene_count * 1500
    baseline_budget = max(scene_budget, int(ManuscriptLimits.TARGET_LENGTH))
    if scene_count <= 3:
        obligation_bonus = min(1600, max(0, total_keywords - scene_count * 2) * 100)
        tail_bonus = 400 if tail_keyword_count >= 3 else 0
        return baseline_budget + obligation_bonus + tail_bonus
    return baseline_budget


def measure_manuscript_scene_materialization(manuscript: str, blueprint: dict[str, Any]) -> ManuscriptSceneProfile:
    profile = build_blueprint_scene_profile(blueprint)
    if profile.scene_count == 0 or not isinstance(manuscript, str) or not manuscript:
        return ManuscriptSceneProfile(
            scene_count=profile.scene_count,
            total_keywords=profile.total_keywords,
            matched_keywords=0,
            overall_ratio=0.0,
            reflected_scenes=0,
            tail_scene_reflected=False,
            weak_scenes=(),
        )

    total_keywords = 0
    matched_keywords = 0
    reflected_scenes = 0
    tail_scene_reflected = False
    weak_scenes: list[str] = []

    for index, packet in enumerate(profile.packets):
        combined_terms = list(dict.fromkeys([*packet.emphasis_keywords, *packet.keywords]))
        if not combined_terms:
            continue

        matched_terms = [term for term in combined_terms if term in manuscript]
        total_keywords += len(combined_terms)
        matched_keywords += len(matched_terms)

        minimum_hits = 1 if len(combined_terms) <= 2 else 2
        ratio = len(matched_terms) / max(len(combined_terms), 1)
        reflected = bool([term for term in packet.emphasis_keywords if term in manuscript])
        reflected = reflected or len(matched_terms) >= minimum_hits or ratio >= 0.45
        if index == len(profile.packets) - 1 and matched_terms:
            reflected = True

        if reflected:
            reflected_scenes += 1
            if index == len(profile.packets) - 1:
                tail_scene_reflected = True
        else:
            weak_scenes.append(packet.scene_id)

    overall_ratio = matched_keywords / max(total_keywords, 1)
    return ManuscriptSceneProfile(
        scene_count=profile.scene_count,
        total_keywords=total_keywords,
        matched_keywords=matched_keywords,
        overall_ratio=overall_ratio,
        reflected_scenes=reflected_scenes,
        tail_scene_reflected=tail_scene_reflected,
        weak_scenes=tuple(weak_scenes),
    )
