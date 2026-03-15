"""Shared helpers for deriving terminal arc state across retry/context paths."""

from typing import Any

_KOREAN_HAL = {"일": 10, "이": 20, "삼": 30, "사": 40, "오": 50, "육": 60, "칠": 70, "팔": 80, "구": 90}
_KOREAN_PUN = {"일": 1, "이": 2, "삼": 3, "사": 4, "오": 5, "육": 6, "칠": 7, "팔": 8, "구": 9}


def _parse_loss_percent(raw_value: Any) -> int:
    text = str(raw_value or "").strip()
    if not text:
        return 0
    if text.startswith("-"):
        return 0

    digits = "".join(ch for ch in text if ch.isdigit())
    if digits:
        try:
            return int(digits)
        except (TypeError, ValueError):
            return 0

    loss = 0
    for key, value in _KOREAN_HAL.items():
        if f"{key}할" in text or f"{key} 할" in text:
            loss += value
            break
    for key, value in _KOREAN_PUN.items():
        if f"{key}푼" in text or f"{key} 푼" in text:
            loss += value
            break
    return loss


def compute_terminal_arc_state(prev_arcs: list[dict] | None) -> dict[str, Any]:
    """Return a normalized terminal-state summary shared by retry/full context builders."""

    if not prev_arcs:
        return {
            "arc_no": 0,
            "final_energy": 100,
            "injuries": "없음",
            "location": "알 수 없음",
            "equipment": [],
            "equipment_text": "없음",
            "energy_history": [],
            "total_energy_consumed": 0,
        }

    last_arc = prev_arcs[-1] or {}
    state_constraints = last_arc.get("state_constraints", {}) if isinstance(last_arc, dict) else {}
    arc_end_state = state_constraints.get("arc_end_state", {}) if isinstance(state_constraints, dict) else {}
    joint_docs = last_arc.get("joint_docs", {}) if isinstance(last_arc, dict) else {}
    status_shadow = last_arc.get("status_shadow", {}) if isinstance(last_arc, dict) else {}

    total_energy_consumed = 0
    energy_history: list[str] = []
    for prev_arc in prev_arcs:
        if not isinstance(prev_arc, dict):
            continue
        prev_shadow = prev_arc.get("status_shadow", {}) or {}
        loss = _parse_loss_percent(prev_shadow.get("internal_energy_loss", "0%"))
        if loss <= 0:
            continue
        total_energy_consumed += loss
        energy_history.append(f"Arc{prev_arc.get('arc_no', '?')}: -{loss}%")

    final_energy = arc_end_state.get("internal_energy")
    if final_energy is None:
        final_energy = max(0, 100 - total_energy_consumed)
    try:
        final_energy = int(str(final_energy).replace("%", "").strip())
    except (ValueError, TypeError):
        final_energy = 50
    if final_energy < 10:
        final_energy = max(10, final_energy)

    injuries = arc_end_state.get("injuries") or status_shadow.get("expected_injuries", "없음")
    location = arc_end_state.get("location") or joint_docs.get("final_location", "알 수 없음")

    equipment = arc_end_state.get("equipment")
    if equipment is None:
        equipment = joint_docs.get("physical_inventory", [])
    if isinstance(equipment, str):
        equipment_list = [item.strip() for item in equipment.split(",") if item.strip()]
        equipment_text = equipment if equipment.strip() else "없음"
    elif isinstance(equipment, list):
        equipment_list = [str(item).strip() for item in equipment if str(item or "").strip()]
        equipment_text = ", ".join(equipment_list) if equipment_list else "없음"
    else:
        equipment_list = [str(equipment).strip()] if str(equipment or "").strip() else []
        equipment_text = str(equipment)[:100] if equipment_list else "없음"

    return {
        "arc_no": last_arc.get("arc_no", "?") if isinstance(last_arc, dict) else "?",
        "final_energy": final_energy,
        "injuries": injuries,
        "location": location,
        "equipment": equipment_list,
        "equipment_text": equipment_text,
        "energy_history": energy_history,
        "total_energy_consumed": total_energy_consumed,
    }
