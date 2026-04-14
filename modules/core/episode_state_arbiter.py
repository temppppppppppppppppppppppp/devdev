"""
Stage3 episode-state arbiter.

Builds one bounded pre-generation packet so Stage3 can consume a single
authoritative carryover surface instead of re-deriving overlapping truths in
multiple places.
"""

from __future__ import annotations

from typing import Any
import re


def _clip(value: object, limit: int = 160) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _clean_token_list(values: list[object] | None, *, limit: int = 10) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in values or []:
        text = _clip(raw, 80)
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
        if len(normalized) >= limit:
            break
    return normalized


def _normalize_equipment(values: object, *, limit: int = 10) -> list[str]:
    if isinstance(values, list):
        return _clean_token_list(
            [item.get("name", item) if isinstance(item, dict) else item for item in values],
            limit=limit,
        )
    if isinstance(values, str):
        return _clean_token_list([chunk.strip() for chunk in values.split(",")], limit=limit)
    return []


def _dedupe_tokens(values: list[str] | None) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for raw in values or []:
        token = str(raw or "").strip()
        if not token or token in seen:
            continue
        seen.add(token)
        ordered.append(token)
    return ordered


def _normalize_scalar(value: object) -> str:
    return _clip(value, 160)


def _extract_last_scene(prev_blueprint: dict[str, Any] | None) -> dict[str, Any]:
    bp = prev_blueprint if isinstance(prev_blueprint, dict) else {}
    scenes = bp.get("scene_breakdown", {})
    if not isinstance(scenes, dict) or not scenes:
        return {}
    ordered_keys = sorted(
        scenes.keys(),
        key=lambda raw: int(re.search(r"\d+", raw).group()) if re.search(r"\d+", raw) else 0,
    )
    if not ordered_keys:
        return {}
    last_scene = scenes.get(ordered_keys[-1], {})
    return last_scene if isinstance(last_scene, dict) else {}


def _build_conflict(
    *,
    field: str,
    kept_source: str,
    kept_value: object,
    dropped_source: str,
    dropped_value: object,
    reason: str,
) -> dict[str, str]:
    return {
        "field": field,
        "kept_source": kept_source,
        "kept_value": _clip(kept_value, 120),
        "dropped_source": dropped_source,
        "dropped_value": _clip(dropped_value, 120),
        "reason": reason,
    }


def summarize_episode_state_packet(packet: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(packet, dict):
        return {}
    opening = packet.get("opening_truth") if isinstance(packet.get("opening_truth"), dict) else {}
    protagonist = packet.get("protagonist_truth") if isinstance(packet.get("protagonist_truth"), dict) else {}
    protagonist_sources = protagonist.get("sources") if isinstance(protagonist.get("sources"), dict) else {}
    summary = {
        "opening_location": _clip(opening.get("location", ""), 80),
        "opening_location_source": _clip(opening.get("location_source", ""), 80),
        "time_source": _clip(opening.get("time_source", ""), 80),
        "protagonist_sources": {
            key: _clip(value, 80) for key, value in protagonist_sources.items() if str(value or "").strip()
        },
        "dropped_conflict_count": len(packet.get("dropped_conflicts") or []),
        "rewrite_required_reasons": list(packet.get("rewrite_required_reasons") or [])[:8],
    }
    return {key: value for key, value in summary.items() if value not in ("", [], {}, None, 0)}


class EpisodeStateArbiter:
    """Resolve one bounded Stage3-first episode-state packet."""

    def arbitrate(
        self,
        *,
        arc_data: dict[str, Any] | None,
        ep_num: int,
        prev_blueprint: dict[str, Any] | None = None,
        prev_blueprints: list[dict[str, Any]] | None = None,
        prev_manuscript_ending: str = "",
        genre: str = "wuxia",
        fact_lock_packet: dict[str, Any] | None = None,
        capital_continuity_packet: dict[str, Any] | None = None,
        episode_progression_packet: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        arc_payload = arc_data if isinstance(arc_data, dict) else {}
        bp = prev_blueprint if isinstance(prev_blueprint, dict) else {}
        ep_start = self._safe_int(arc_payload.get("ep_start"))
        arc_position = ep_num - ep_start + 1 if ep_start else 1
        is_arc_opening_episode = arc_position <= 1

        opening_truth, opening_conflicts = self._resolve_opening_truth(
            arc_payload=arc_payload,
            prev_blueprint=bp,
            prev_blueprints=prev_blueprints,
            prev_manuscript_ending=prev_manuscript_ending,
            is_arc_opening_episode=is_arc_opening_episode,
        )
        protagonist_truth, protagonist_conflicts = self._resolve_protagonist_truth(
            arc_payload=arc_payload,
            prev_blueprint=bp,
            genre=genre,
            is_arc_opening_episode=is_arc_opening_episode,
        )
        dropped_conflicts = opening_conflicts + protagonist_conflicts
        rewrite_required_reasons = _dedupe_tokens([item.get("reason", "") for item in dropped_conflicts])

        return {
            "source_precedence": {
                "opening_truth": [
                    "prev_blueprint.scene_breakdown.last.location",
                    "prev_blueprint.end_location",
                    "arc_data.state_constraints.arc_start_state.location",
                    "arc_data.joint_docs.final_location",
                ],
                "time_truth": [
                    "prev_manuscript_ending",
                    "prev_blueprint.time_flow",
                ],
                "protagonist_truth": [
                    "prev_blueprint.protagonist_state",
                    "arc_data.state_constraints.arc_start_state",
                    "arc_data.status_shadow",
                    "arc_data.joint_docs.physical_inventory",
                ],
                "fact_lock_truth": [
                    "prev_manuscript_ending",
                    "prev_blueprint",
                    "arc_data",
                ],
                "capital_truth": [
                    "prev_manuscript_ending",
                    "prev_blueprint",
                    "arc_data",
                ],
                "progression_truth": [
                    "prev_blueprint",
                    "arc_data",
                ],
            },
            "is_arc_opening_episode": is_arc_opening_episode,
            "opening_truth": opening_truth,
            "protagonist_truth": protagonist_truth,
            "fact_lock_truth": self._normalize_fact_lock_truth(fact_lock_packet),
            "capital_truth": self._normalize_capital_truth(capital_continuity_packet),
            "progression_truth": self._normalize_progression_truth(episode_progression_packet),
            "dropped_conflicts": dropped_conflicts,
            "rewrite_required_reasons": rewrite_required_reasons,
        }

    @staticmethod
    def _safe_int(value: object) -> int:
        try:
            return int(value) if value not in (None, "") else 0
        except (TypeError, ValueError):
            return 0

    def _resolve_opening_truth(
        self,
        *,
        arc_payload: dict[str, Any],
        prev_blueprint: dict[str, Any],
        prev_blueprints: list[dict[str, Any]] | None,
        prev_manuscript_ending: str,
        is_arc_opening_episode: bool,
    ) -> tuple[dict[str, Any], list[dict[str, str]]]:
        state_constraints = (
            arc_payload.get("state_constraints") if isinstance(arc_payload.get("state_constraints"), dict) else {}
        )
        start_state = (
            state_constraints.get("arc_start_state") if isinstance(state_constraints.get("arc_start_state"), dict) else {}
        )
        joint_docs = arc_payload.get("joint_docs") if isinstance(arc_payload.get("joint_docs"), dict) else {}
        last_scene = _extract_last_scene(prev_blueprint)
        prev_location = _normalize_scalar(last_scene.get("location") or prev_blueprint.get("end_location") or prev_blueprint.get("location"))
        arc_start_location = _normalize_scalar(start_state.get("location") or joint_docs.get("final_location"))

        dropped_conflicts: list[dict[str, str]] = []
        if prev_location:
            location = prev_location
            location_source = (
                "prev_blueprint.scene_breakdown.last.location"
                if _normalize_scalar(last_scene.get("location"))
                else "prev_blueprint.end_location"
            )
            if arc_start_location and arc_start_location != prev_location and not is_arc_opening_episode:
                dropped_conflicts.append(
                    _build_conflict(
                        field="opening.location",
                        kept_source=location_source,
                        kept_value=prev_location,
                        dropped_source="arc_data.state_constraints.arc_start_state.location",
                        dropped_value=arc_start_location,
                        reason="mid_arc_arc_start_location_override_blocked",
                    )
                )
        else:
            location = arc_start_location
            location_source = (
                "arc_data.state_constraints.arc_start_state.location" if _normalize_scalar(start_state.get("location")) else "arc_data.joint_docs.final_location"
            )

        time_source = ""
        time_context = ""
        bp_time_flow = _normalize_scalar(prev_blueprint.get("time_flow"))
        manuscript_tail = str(prev_manuscript_ending or "").strip()
        if manuscript_tail:
            time_source = "prev_manuscript_ending"
            time_context = (
                f"[manuscript ending]\n{manuscript_tail}\n[blueprint record] {bp_time_flow}"
                if bp_time_flow
                else f"[manuscript ending]\n{manuscript_tail}"
            )
        elif bp_time_flow:
            time_source = "prev_blueprint.time_flow"
            time_context = bp_time_flow

        active_characters = _clean_token_list(last_scene.get("characters") if isinstance(last_scene, dict) else [], limit=5)
        ongoing_conflicts: list[str] = []
        if isinstance(prev_blueprints, list) and prev_blueprints:
            collected: list[str] = []
            for bp_item in prev_blueprints[-3:]:
                if not isinstance(bp_item, dict):
                    continue
                collected.extend(str(item or "").strip() for item in (bp_item.get("ongoing_conflicts") or [])[:2])
                cliffhanger = str(bp_item.get("cliffhanger", "") or "").strip()
                if cliffhanger:
                    collected.append(cliffhanger[:50])
            ongoing_conflicts = _clean_token_list(collected, limit=5)

        return {
            "location": location,
            "location_source": location_source if location else "",
            "time_context": time_context,
            "time_source": time_source,
            "active_characters": active_characters,
            "ongoing_conflicts": ongoing_conflicts,
        }, dropped_conflicts

    def _resolve_protagonist_truth(
        self,
        *,
        arc_payload: dict[str, Any],
        prev_blueprint: dict[str, Any],
        genre: str,
        is_arc_opening_episode: bool,
    ) -> tuple[dict[str, Any], list[dict[str, str]]]:
        protagonist_truth: dict[str, Any] = {
            "equipment": [],
            "injuries": "없음",
            "companions": [],
            "mood": "평온",
            "sources": {},
        }
        if genre == "wuxia":
            protagonist_truth["internal_energy"] = "100%"

        dropped_conflicts: list[dict[str, str]] = []
        joint_docs = arc_payload.get("joint_docs") if isinstance(arc_payload.get("joint_docs"), dict) else {}
        status_shadow = arc_payload.get("status_shadow") if isinstance(arc_payload.get("status_shadow"), dict) else {}
        state_constraints = (
            arc_payload.get("state_constraints") if isinstance(arc_payload.get("state_constraints"), dict) else {}
        )
        start_state = (
            state_constraints.get("arc_start_state") if isinstance(state_constraints.get("arc_start_state"), dict) else {}
        )
        prev_protag = (
            prev_blueprint.get("protagonist_state") if isinstance(prev_blueprint.get("protagonist_state"), dict) else {}
        )

        equipment = _normalize_equipment(joint_docs.get("physical_inventory"))
        if equipment:
            protagonist_truth["equipment"] = equipment
            protagonist_truth["sources"]["equipment"] = "arc_data.joint_docs.physical_inventory"

        injuries = _normalize_scalar(status_shadow.get("expected_injuries"))
        if injuries:
            protagonist_truth["injuries"] = injuries
            protagonist_truth["sources"]["injuries"] = "arc_data.status_shadow.expected_injuries"

        if genre == "wuxia":
            energy = status_shadow.get("internal_energy_loss")
            if energy not in (None, ""):
                try:
                    loss = int(re.search(r"(\d+)", str(energy)).group(1))
                    protagonist_truth["internal_energy"] = f"{100 - loss}%"
                    protagonist_truth["sources"]["internal_energy"] = "arc_data.status_shadow.internal_energy_loss"
                except (AttributeError, TypeError, ValueError):
                    pass

        if is_arc_opening_episode or not prev_blueprint:
            self._apply_arc_start_state(
                protagonist_truth=protagonist_truth,
                start_state=start_state,
                genre=genre,
            )
        else:
            self._record_mid_arc_start_conflicts(
                dropped_conflicts=dropped_conflicts,
                protagonist_truth=protagonist_truth,
                start_state=start_state,
                prev_protag=prev_protag,
                genre=genre,
            )

        if prev_protag:
            prev_equipment = _normalize_equipment(prev_protag.get("equipment"))
            if prev_equipment:
                protagonist_truth["equipment"] = prev_equipment
                protagonist_truth["sources"]["equipment"] = "prev_blueprint.protagonist_state.equipment"
            prev_injuries = _normalize_scalar(prev_protag.get("injuries"))
            if prev_injuries:
                protagonist_truth["injuries"] = prev_injuries
                protagonist_truth["sources"]["injuries"] = "prev_blueprint.protagonist_state.injuries"
            prev_companions = _clean_token_list(prev_protag.get("companions"), limit=8)
            if prev_companions:
                protagonist_truth["companions"] = prev_companions
                protagonist_truth["sources"]["companions"] = "prev_blueprint.protagonist_state.companions"
            prev_mood = _normalize_scalar(prev_protag.get("mood"))
            if prev_mood:
                protagonist_truth["mood"] = prev_mood
                protagonist_truth["sources"]["mood"] = "prev_blueprint.protagonist_state.mood"

        return protagonist_truth, dropped_conflicts

    @staticmethod
    def _apply_arc_start_state(*, protagonist_truth: dict[str, Any], start_state: dict[str, Any], genre: str) -> None:
        start_injuries = _normalize_scalar(start_state.get("injuries"))
        if start_injuries:
            protagonist_truth["injuries"] = start_injuries
            protagonist_truth["sources"]["injuries"] = "arc_data.state_constraints.arc_start_state.injuries"

        start_equipment = _normalize_equipment(start_state.get("equipment"))
        if "equipment" in start_state and start_state.get("equipment") is not None:
            protagonist_truth["equipment"] = start_equipment
            protagonist_truth["sources"]["equipment"] = "arc_data.state_constraints.arc_start_state.equipment"

        if genre == "wuxia" and start_state.get("internal_energy") not in (None, ""):
            protagonist_truth["internal_energy"] = f"{start_state['internal_energy']}%"
            protagonist_truth["sources"]["internal_energy"] = "arc_data.state_constraints.arc_start_state.internal_energy"

    @staticmethod
    def _record_mid_arc_start_conflicts(
        *,
        dropped_conflicts: list[dict[str, str]],
        protagonist_truth: dict[str, Any],
        start_state: dict[str, Any],
        prev_protag: dict[str, Any],
        genre: str,
    ) -> None:
        start_equipment = _normalize_equipment(start_state.get("equipment"))
        prev_equipment = _normalize_equipment(prev_protag.get("equipment"))
        if start_equipment and prev_equipment and start_equipment != prev_equipment:
            dropped_conflicts.append(
                _build_conflict(
                    field="protagonist.equipment",
                    kept_source="prev_blueprint.protagonist_state.equipment",
                    kept_value=", ".join(prev_equipment[:5]),
                    dropped_source="arc_data.state_constraints.arc_start_state.equipment",
                    dropped_value=", ".join(start_equipment[:5]),
                    reason="mid_arc_arc_start_equipment_override_blocked",
                )
            )

        start_injuries = _normalize_scalar(start_state.get("injuries"))
        prev_injuries = _normalize_scalar(prev_protag.get("injuries"))
        if start_injuries and prev_injuries and start_injuries != prev_injuries:
            dropped_conflicts.append(
                _build_conflict(
                    field="protagonist.injuries",
                    kept_source="prev_blueprint.protagonist_state.injuries",
                    kept_value=prev_injuries,
                    dropped_source="arc_data.state_constraints.arc_start_state.injuries",
                    dropped_value=start_injuries,
                    reason="mid_arc_arc_start_injury_override_blocked",
                )
            )

        if genre == "wuxia" and start_state.get("internal_energy") not in (None, ""):
            kept_energy = _normalize_scalar(protagonist_truth.get("internal_energy"))
            dropped_conflicts.append(
                _build_conflict(
                    field="protagonist.internal_energy",
                    kept_source=protagonist_truth.get("sources", {}).get("internal_energy", "legacy_energy_default"),
                    kept_value=kept_energy,
                    dropped_source="arc_data.state_constraints.arc_start_state.internal_energy",
                    dropped_value=f"{start_state['internal_energy']}%",
                    reason="mid_arc_arc_start_energy_override_blocked",
                )
            )

    @staticmethod
    def _normalize_fact_lock_truth(packet: dict[str, Any] | None) -> dict[str, Any]:
        payload = packet if isinstance(packet, dict) else {}
        anchors = payload.get("anchors") if isinstance(payload.get("anchors"), list) else []
        return {
            "anchor_count": len(anchors),
            "source": _normalize_scalar(payload.get("source")),
        }

    @staticmethod
    def _normalize_capital_truth(packet: dict[str, Any] | None) -> dict[str, Any]:
        payload = packet if isinstance(packet, dict) else {}
        fields = payload.get("fields") if isinstance(payload.get("fields"), list) else []
        preview = []
        for field in fields[:4]:
            if not isinstance(field, dict):
                continue
            label = _normalize_scalar(field.get("label"))
            value = _normalize_scalar(field.get("value"))
            if label and value:
                preview.append(f"{label}: {value}")
        return {
            "field_count": len(fields),
            "field_preview": preview,
            "source": _normalize_scalar(payload.get("source")),
        }

    @staticmethod
    def _normalize_progression_truth(packet: dict[str, Any] | None) -> dict[str, Any]:
        payload = packet if isinstance(packet, dict) else {}
        time_truths = _clean_token_list(payload.get("time_truths"), limit=4)
        institution_truths = _clean_token_list(payload.get("institution_truths"), limit=4)
        blocked_scene_families = payload.get("blocked_scene_families")
        family_count = len(blocked_scene_families) if isinstance(blocked_scene_families, list) else 0
        return {
            "time_truths": time_truths,
            "institution_truths": institution_truths,
            "blocked_scene_family_count": family_count,
        }
