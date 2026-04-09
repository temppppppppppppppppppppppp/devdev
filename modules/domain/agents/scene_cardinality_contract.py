from __future__ import annotations

LOW_SCENE_CARDINALITY_MIN_INTEGRATED_CHARS = 800
LOW_SCENE_CARDINALITY_MIN_MATERIALIZED_SCENES = 2
SCENE_OBLIGATION_MIN_CHARS = 8


def count_scene_entries(scenes) -> int:
    if isinstance(scenes, (dict, list)):
        return len(scenes)
    return 0


def iter_scene_entries(scenes):
    if isinstance(scenes, dict):
        yield from scenes.values()
    elif isinstance(scenes, list):
        yield from scenes


def _scene_has_materialized_obligation(scene_value) -> bool:
    if not isinstance(scene_value, dict):
        return False

    summary = str(
        scene_value.get("goal", "")
        or scene_value.get("summary", "")
        or scene_value.get("description", "")
        or scene_value.get("content", "")
        or ""
    ).strip()
    if len(summary) >= SCENE_OBLIGATION_MIN_CHARS:
        return True

    key_events = scene_value.get("key_events") or []
    if isinstance(key_events, str):
        return bool(key_events.strip())
    if isinstance(key_events, list):
        return any(str(item or "").strip() for item in key_events)
    return False


def evaluate_stage3_scene_cardinality(scenes, integrated_scenario) -> tuple[bool, int, str, str]:
    scene_count = count_scene_entries(scenes)
    integrated = integrated_scenario if isinstance(integrated_scenario, str) else str(integrated_scenario or "")

    if scene_count >= 4:
        return True, scene_count, "", ""

    if scene_count <= 1:
        return False, scene_count, f"씬 개수 부족: {scene_count}개", "최소 2개 이상의 씬이 필요합니다."

    if len(integrated) < LOW_SCENE_CARDINALITY_MIN_INTEGRATED_CHARS:
        return (
            False,
            scene_count,
            "씬 밀도 부족: 저씬수 예외 기준 미달",
            f"2-3씬 blueprint는 integrated_scenario {LOW_SCENE_CARDINALITY_MIN_INTEGRATED_CHARS}자 이상으로 충분히 구체화해야 합니다.",
        )

    materialized_scene_count = sum(1 for scene_value in iter_scene_entries(scenes) if _scene_has_materialized_obligation(scene_value))
    required_materialized_scene_count = min(scene_count, LOW_SCENE_CARDINALITY_MIN_MATERIALIZED_SCENES)
    if materialized_scene_count < required_materialized_scene_count:
        return (
            False,
            scene_count,
            "씬 밀도 부족: 저씬수 예외 기준 미달",
            f"2-3씬 blueprint는 최소 {required_materialized_scene_count}개 이상의 씬에 구체적 goal/summary 또는 key_events가 필요합니다.",
        )

    return True, scene_count, "", ""
