from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

OPENING_BUNDLE_WINDOW = "TR 2~6"
OPENING_BLOCK_START = 2
OPENING_BLOCK_END = 6
DEFAULT_SIGNBOARD_BLOCK = 3
DEFAULT_REEVALUATION_BLOCK = 4
DEFAULT_TICKET_BLOCK = 6
SIGNBOARD_RE = re.compile(r"(간판|공식|언론|보도|공개|현판|메인|증명|표준|첫 월|대표 사례)")
REEVALUATION_RE = re.compile(r"(재평가|다시 봤|인정|시선|눈빛|존중|신뢰|대표|브레인|무시하지 못)")
TICKET_RE = re.compile(r"(입장권|다음 전장|다음 판|진입|열린다|호출|초대|출입권|패스|직행)")


@dataclass(frozen=True)
class OpeningContractSyncResult:
    work_id: str
    contract: dict[str, Any]
    updated_paths: tuple[str, ...]
    missing_paths: tuple[str, ...]


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _parse_block_no(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    text = _as_text(value)
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def _parse_block_range(value: Any) -> tuple[int | None, int | None]:
    text = _as_text(value)
    if "-" not in text:
        return None, None
    start_text, end_text = text.split("-", 1)
    try:
        return int(start_text), int(end_text)
    except ValueError:
        return None, None


def _phase0_design(phase0_payload: dict[str, Any]) -> dict[str, Any]:
    value = phase0_payload.get("phase0_design")
    return value if isinstance(value, dict) else {}


def _first_arc(phase0_payload: dict[str, Any]) -> dict[str, Any]:
    phase0_design = _phase0_design(phase0_payload)
    for key in ("arcs", "arc_design"):
        arcs = phase0_design.get(key)
        if isinstance(arcs, list):
            for arc in arcs:
                if isinstance(arc, dict):
                    return arc
    return {}


def _slot_rows(first_arc: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    for index, slot in enumerate(_ensure_list(first_arc.get("block_slots")), start=1):
        if not isinstance(slot, dict):
            continue
        block_no = _parse_block_no(slot.get("block")) or _parse_block_no(slot.get("block_no")) or index
        rows.append((block_no, slot))
    return rows


def _slot_window(rows: list[tuple[int, dict[str, Any]]]) -> list[tuple[int, dict[str, Any]]]:
    window = [row for row in rows if OPENING_BLOCK_START <= row[0] <= OPENING_BLOCK_END]
    if window:
        return window
    return rows[: OPENING_BLOCK_END - OPENING_BLOCK_START + 1]


def _slot_text(slot: dict[str, Any]) -> str:
    return " ".join(
        part for part in (_as_text(slot.get("title")), _as_text(slot.get("function"))) if part
    )


def _unique_nonempty(values: list[str], *, limit: int = 5) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _as_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
        if len(out) >= limit:
            break
    return out


def _select_signal_block(
    rows: list[tuple[int, dict[str, Any]]],
    pattern: re.Pattern[str],
    default_block: int,
) -> int:
    for block_no, slot in rows:
        if pattern.search(_slot_text(slot)):
            return max(OPENING_BLOCK_START, min(OPENING_BLOCK_END, block_no))
    return default_block


def _fallback_macro_map(first_arc: dict[str, Any]) -> list[str]:
    sectors = [
        *_ensure_list(first_arc.get("front_sectors")),
        *_ensure_list(first_arc.get("support_sectors")),
    ]
    return _unique_nonempty([_as_text(item) for item in sectors], limit=5)


def derive_opening_bundle_contract(
    phase0_payload: dict[str, Any],
    material_bundle_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    phase0_payload = phase0_payload if isinstance(phase0_payload, dict) else {}
    material_bundle_summary = material_bundle_summary if isinstance(material_bundle_summary, dict) else {}
    phase0_design = _phase0_design(phase0_payload)
    hud_interpretation = phase0_design.get("hud_interpretation") if isinstance(phase0_design.get("hud_interpretation"), dict) else {}
    protagonist = phase0_payload.get("protagonist", {}) if isinstance(phase0_payload.get("protagonist"), dict) else {}
    first_arc = _first_arc(phase0_payload)
    rows = _slot_rows(first_arc)
    window_rows = _slot_window(rows)

    macro_battlefield = _as_text(first_arc.get("title")) or _as_text(material_bundle_summary.get("notes")) or "opening battlefield"
    macro_map = _unique_nonempty([_as_text(slot.get("title")) for _block_no, slot in window_rows], limit=5)
    if not macro_map:
        macro_map = _fallback_macro_map(first_arc)
    if not macro_map and macro_battlefield:
        macro_map = [macro_battlefield]

    bundle_goal = (
        _as_text(protagonist.get("initial_goal"))
        or _as_text(first_arc.get("exit_function"))
        or _as_text(hud_interpretation.get("first_block_reward_rule"))
        or "TR 2~6 안에서 첫 reader-earning 보상과 다음 전장 입장권을 확보한다."
    )

    first_signboard_block = _select_signal_block(window_rows, SIGNBOARD_RE, DEFAULT_SIGNBOARD_BLOCK)
    representative_reevaluation_block = _select_signal_block(
        window_rows, REEVALUATION_RE, DEFAULT_REEVALUATION_BLOCK
    )
    next_battlefield_ticket_block = _select_signal_block(window_rows, TICKET_RE, DEFAULT_TICKET_BLOCK)

    range_start, range_end = _parse_block_range(first_arc.get("block_range"))
    arc_span = ""
    if range_start is not None and range_end is not None:
        arc_span = f"B{range_start}-{range_end}"
    timing_reconciliation_note = (
        f"{macro_battlefield} arc outline가 {arc_span}까지 이어져도 reader-earning signboard/reevaluation/ticket은 TR 2~6 안에서 먼저 끝낸다."
        if arc_span and range_end and range_end > OPENING_BLOCK_END
        else f"{macro_battlefield} opening은 같은 macro battlefield 안에 머물더라도 reader-earning signboard/reevaluation/ticket을 TR 2~6 안에서 끝낸다."
    )

    return {
        "bundle_window": OPENING_BUNDLE_WINDOW,
        "macro_battlefield": macro_battlefield,
        "macro_battlefield_map": macro_map,
        "bundle_goal": bundle_goal,
        "first_signboard_block": first_signboard_block,
        "representative_reevaluation_block": representative_reevaluation_block,
        "next_battlefield_ticket_block": next_battlefield_ticket_block,
        "timing_reconciliation_note": timing_reconciliation_note,
    }


def _canonicalize_existing_contract(candidate: Any, derived: dict[str, Any]) -> dict[str, Any]:
    existing = candidate if isinstance(candidate, dict) else {}
    contract = dict(derived)
    contract["bundle_window"] = OPENING_BUNDLE_WINDOW

    for field in ("macro_battlefield", "bundle_goal", "timing_reconciliation_note"):
        text = _as_text(existing.get(field))
        if text:
            contract[field] = text

    macro_map = [
        _as_text(item) for item in _ensure_list(existing.get("macro_battlefield_map")) if _as_text(item)
    ]
    if macro_map:
        contract["macro_battlefield_map"] = _unique_nonempty(macro_map, limit=5)

    for field in (
        "first_signboard_block",
        "representative_reevaluation_block",
        "next_battlefield_ticket_block",
    ):
        value = existing.get(field)
        if isinstance(value, int) and not isinstance(value, bool) and OPENING_BLOCK_START <= value <= OPENING_BLOCK_END:
            contract[field] = value

    return contract


def ensure_opening_bundle_contract(
    phase0_payload: dict[str, Any],
    material_bundle_summary: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any]]:
    phase0_copy = deepcopy(phase0_payload)
    bundle_copy = deepcopy(material_bundle_summary) if isinstance(material_bundle_summary, dict) else None

    phase0_existing = _phase0_design(phase0_copy).get("opening_bundle_contract")
    bundle_existing = bundle_copy.get("opening_bundle_contract") if isinstance(bundle_copy, dict) else None
    derived = derive_opening_bundle_contract(phase0_copy, bundle_copy)
    contract = _canonicalize_existing_contract(bundle_existing or phase0_existing, derived)

    phase0_design = _phase0_design(phase0_copy)
    if phase0_design:
        phase0_design["opening_bundle_contract"] = deepcopy(contract)
    if isinstance(bundle_copy, dict):
        bundle_copy["opening_bundle_contract"] = deepcopy(contract)
    return phase0_copy, bundle_copy, contract


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_opening_bundle_contract_for_work(
    work_id: str,
    *,
    root: Path | None = None,
    write: bool = True,
) -> OpeningContractSyncResult:
    root = (root or ROOT).resolve()
    bundle_path = root / "treatments" / "preprocess" / work_id / "material_bundle_summary.json"
    phase0_path = root / "treatments" / "phase0" / f"{work_id}_phase0_design.json"
    if not phase0_path.is_file():
        phase0_path = root / "treatments" / f"{work_id}_phase0_design.json"

    bundle_data = _load_json(bundle_path)
    phase0_data = _load_json(phase0_path)
    updated_paths: list[str] = []
    missing_paths: list[str] = []

    if phase0_data is None:
        missing_paths.append(str(phase0_path))
    if bundle_data is None:
        missing_paths.append(str(bundle_path))

    if phase0_data is None:
        return OpeningContractSyncResult(work_id=work_id, contract={}, updated_paths=(), missing_paths=tuple(missing_paths))

    updated_phase0, updated_bundle, contract = ensure_opening_bundle_contract(phase0_data, bundle_data)

    if write and updated_phase0 != phase0_data and phase0_path:
        _write_json(phase0_path, updated_phase0)
        updated_paths.append(str(phase0_path))

    if bundle_data is not None and isinstance(updated_bundle, dict) and write and updated_bundle != bundle_data:
        _write_json(bundle_path, updated_bundle)
        updated_paths.append(str(bundle_path))

    return OpeningContractSyncResult(
        work_id=work_id,
        contract=contract,
        updated_paths=tuple(updated_paths),
        missing_paths=tuple(missing_paths),
    )
