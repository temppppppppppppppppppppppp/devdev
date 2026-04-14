"""Shared Stage2-to-Stage4 carryover authority transport contract helpers."""

from __future__ import annotations

from typing import Any

from modules.core.stage2_location_contract import collapse_stage2_location_label

CROSS_STAGE_AUTHORITY_PACKET_VERSION = "cross_stage_authority_packet.v1"

_OPENING_SOURCE_PRECEDENCE = [
    "state_constraints.arc_end_state.location",
    "joint_docs.final_location",
    "joint_docs.world_joint",
]
_PROTAGONIST_SOURCE_PRECEDENCE = [
    "state_constraints.arc_end_state.equipment",
    "joint_docs.physical_inventory",
    "state_constraints.arc_end_state.injuries",
    "state_constraints.arc_end_state.internal_energy",
]
_NUMERIC_SOURCE_PRECEDENCE = [
    "state_constraints.arc_end_state.capital",
    "state_constraints.arc_end_state.total_assets",
    "state_constraints.arc_end_state.portfolio_position",
    "state_constraints.investment_calc.final_cash",
    "state_constraints.investment_calc.final_total_assets",
]


def _clip_text(value: object, limit: int = 160) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _coerce_mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _coerce_scalar(value: object, *, limit: int = 160) -> object:
    if value is None:
        return None
    if isinstance(value, bool | int | float):
        return value
    text = _clip_text(value, limit)
    return text or None


def _normalize_list(values: object, *, limit: int = 12) -> list[str]:
    if isinstance(values, str):
        stripped = values.strip()
        raw_items: list[object]
        if stripped.startswith("[") and stripped.endswith("]"):
            stripped = stripped[1:-1]
        raw_items = [chunk.strip().strip("'\"") for chunk in stripped.split(",")] if stripped else []
    elif isinstance(values, list):
        raw_items = values
    else:
        raw_items = []

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_item in raw_items:
        if isinstance(raw_item, dict):
            text = _clip_text(raw_item.get("name") or raw_item.get("item") or raw_item.get("value") or "", 80)
        else:
            text = _clip_text(raw_item, 80)
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
        if len(normalized) >= limit:
            break
    return normalized


def _resolve_text_with_source(candidates: list[tuple[object, str]]) -> tuple[str, str]:
    for value, source in candidates:
        text = _clip_text(value)
        if text:
            return text, source
    return "", ""


def _resolve_location_with_source(end_state: dict[str, Any], joint_docs: dict[str, Any]) -> tuple[str, str]:
    for raw_value, source in (
        (end_state.get("location"), "state_constraints.arc_end_state.location"),
        (joint_docs.get("final_location"), "joint_docs.final_location"),
    ):
        normalized = collapse_stage2_location_label(raw_value)
        if normalized:
            return normalized, source
        text = _clip_text(raw_value)
        if text:
            return text, source
    return "", ""


def _resolve_equipment_with_source(end_state: dict[str, Any], joint_docs: dict[str, Any]) -> tuple[list[str], str]:
    for raw_value, source in (
        (end_state.get("equipment"), "state_constraints.arc_end_state.equipment"),
        (joint_docs.get("physical_inventory"), "joint_docs.physical_inventory"),
    ):
        normalized = _normalize_list(raw_value)
        if normalized:
            return normalized, source
    return [], ""


def _prune_empty_values(payload: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if value not in ("", [], {}, None) and not (isinstance(value, list) and len(value) == 0)
    }


def extract_explicit_cross_stage_authority_packet(arc_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    payload = arc_payload if isinstance(arc_payload, dict) else {}
    existing = payload.get("cross_stage_authority_packet")
    if isinstance(existing, dict) and existing.get("contract_version") == CROSS_STAGE_AUTHORITY_PACKET_VERSION:
        return existing
    return None


def collect_numeric_carryover_entries(packet: dict[str, Any] | None) -> list[dict[str, object]]:
    numeric_carryover = _coerce_mapping(_coerce_mapping(packet).get("numeric_carryover"))
    entries: list[dict[str, object]] = []
    for raw_key, raw_value in numeric_carryover.items():
        field_name = str(raw_key or "").strip()
        if not field_name or field_name.endswith("_source"):
            continue
        if raw_value in ("", [], {}, None):
            continue
        entries.append(
            {
                "field": field_name,
                "value": raw_value,
                "source": _clip_text(numeric_carryover.get(f"{field_name}_source")),
            }
        )
    return entries


def build_cross_stage_authority_packet(
    arc_payload: dict[str, Any] | None,
    *,
    emitted_by: str = "Stage2Finalizer",
) -> dict[str, Any] | None:
    payload = arc_payload if isinstance(arc_payload, dict) else {}
    state_constraints = _coerce_mapping(payload.get("state_constraints"))
    joint_docs = _coerce_mapping(payload.get("joint_docs"))
    end_state = _coerce_mapping(state_constraints.get("arc_end_state"))
    investment_calc = _coerce_mapping(state_constraints.get("investment_calc"))

    location, location_source = _resolve_location_with_source(end_state, joint_docs)
    world_joint, world_joint_source = _resolve_text_with_source(
        [(joint_docs.get("world_joint"), "joint_docs.world_joint")]
    )
    equipment, equipment_source = _resolve_equipment_with_source(end_state, joint_docs)
    injuries, injuries_source = _resolve_text_with_source(
        [(end_state.get("injuries"), "state_constraints.arc_end_state.injuries")]
    )
    internal_energy = _coerce_scalar(end_state.get("internal_energy"))
    internal_energy_source = (
        "state_constraints.arc_end_state.internal_energy" if internal_energy not in ("", None, [], {}) else ""
    )
    capital, capital_source = _resolve_text_with_source(
        [(end_state.get("capital"), "state_constraints.arc_end_state.capital")]
    )
    total_assets, total_assets_source = _resolve_text_with_source(
        [(end_state.get("total_assets"), "state_constraints.arc_end_state.total_assets")]
    )
    portfolio_position, portfolio_position_source = _resolve_text_with_source(
        [(end_state.get("portfolio_position"), "state_constraints.arc_end_state.portfolio_position")]
    )
    final_cash = _coerce_scalar(investment_calc.get("final_cash"))
    final_total_assets = _coerce_scalar(investment_calc.get("final_total_assets"))

    opening_carryover = _prune_empty_values(
        {
            "location": location,
            "location_source": location_source,
            "world_joint": world_joint,
            "world_joint_source": world_joint_source,
        }
    )
    protagonist_carryover = _prune_empty_values(
        {
            "equipment": equipment,
            "equipment_source": equipment_source,
            "injuries": injuries,
            "injuries_source": injuries_source,
            "internal_energy": internal_energy,
            "internal_energy_source": internal_energy_source,
        }
    )
    numeric_carryover = _prune_empty_values(
        {
            "capital": capital,
            "capital_source": capital_source,
            "total_assets": total_assets,
            "total_assets_source": total_assets_source,
            "portfolio_position": portfolio_position,
            "portfolio_position_source": portfolio_position_source,
            "investment_calc_final_cash": final_cash,
            "investment_calc_final_cash_source": (
                "state_constraints.investment_calc.final_cash" if final_cash not in ("", None, [], {}) else ""
            ),
            "investment_calc_final_total_assets": final_total_assets,
            "investment_calc_final_total_assets_source": (
                "state_constraints.investment_calc.final_total_assets"
                if final_total_assets not in ("", None, [], {})
                else ""
            ),
        }
    )

    if not any((opening_carryover, protagonist_carryover, numeric_carryover)):
        return None

    return {
        "contract_version": CROSS_STAGE_AUTHORITY_PACKET_VERSION,
        "opening_carryover": opening_carryover,
        "protagonist_carryover": protagonist_carryover,
        "numeric_carryover": numeric_carryover,
        "source_precedence": {
            "opening_carryover": list(_OPENING_SOURCE_PRECEDENCE),
            "protagonist_carryover": list(_PROTAGONIST_SOURCE_PRECEDENCE),
            "numeric_carryover": list(_NUMERIC_SOURCE_PRECEDENCE),
        },
        "provenance": _prune_empty_values(
            {
                "stage": 2,
                "emitted_by": emitted_by,
                "arc_no": _coerce_scalar(payload.get("arc_no")),
                "ep_start": _coerce_scalar(payload.get("ep_start")),
                "ep_end": _coerce_scalar(payload.get("ep_end")),
                "legacy_text_surface": "[Carryover Authority Packet]",
                "legacy_summary_surface": "advisory_flags.carryover_authority",
            }
        ),
    }


def resolve_cross_stage_authority_packet(arc_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    payload = arc_payload if isinstance(arc_payload, dict) else {}
    existing = extract_explicit_cross_stage_authority_packet(payload)
    if existing:
        return existing
    return build_cross_stage_authority_packet(payload)
