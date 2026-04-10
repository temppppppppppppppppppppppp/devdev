from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from modules.core.reference_selection_stage0 import (
    build_stage0_selection_draft,
    load_selected_card_signals,
    resolve_opening_bundle_contract,
    resolve_profiles,
    resolve_work_identity,
)

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Phase0SeedResult:
    phase0_design: dict[str, Any]
    stage0_source_mode: str
    work_identity_resolution: str
    profile_resolution: str
    opening_contract_resolution: str
    title_resolution: str
    updated_paths: tuple[str, ...]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = _read_json(path)
    return data if isinstance(data, dict) else {}


def _meaningful_text(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    compact = value.strip()
    return bool(compact) and not compact.lower().startswith("todo:")


def _meaningful_value(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return _meaningful_text(value)
    if isinstance(value, list):
        return any(_meaningful_value(item) for item in value)
    if isinstance(value, dict):
        return any(_meaningful_value(item) for item in value.values())
    return value is not None


def _merge_value(existing: Any, seed: Any) -> Any:
    if isinstance(existing, dict) and isinstance(seed, dict):
        merged = deepcopy(seed)
        for key, value in existing.items():
            if key in merged:
                merged[key] = _merge_value(value, merged[key])
            elif _meaningful_value(value):
                merged[key] = deepcopy(value)
        return merged
    if isinstance(existing, list):
        return deepcopy(existing) if existing else deepcopy(seed)
    if _meaningful_value(existing):
        return deepcopy(existing)
    return deepcopy(seed)


def _pick_text(existing: Any, seed: str) -> str:
    return str(existing).strip() if _meaningful_text(existing) else seed


def _first_meaningful(items: list[Any], fallback: str) -> str:
    for item in items:
        if _meaningful_text(item):
            return str(item).strip()
    return fallback


def _shorten(text: str, limit: int = 160) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _resolve_stage0_authority(
    work_id: str,
    root: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    tuple[Any, ...],
    str,
    str,
    str,
    str,
]:
    project_root = root / "narrative_ssot" / "50_projects" / work_id
    preprocess_root = project_root / "20_preprocess"
    reference_selection, _guard, cards = load_selected_card_signals(work_id, root=root)
    draft = build_stage0_selection_draft(work_id, root=root)

    source_manifest = _merge_value(
        _load_json_if_exists(preprocess_root / "source_manifest.json"),
        draft.source_manifest,
    )
    profile_lock = _merge_value(
        _load_json_if_exists(preprocess_root / "profile_lock.json"),
        draft.profile_lock,
    )
    material_bundle_summary = _merge_value(
        _load_json_if_exists(preprocess_root / "material_bundle_summary.json"),
        draft.material_bundle_summary,
    )
    phase0_ready_snapshot = _merge_value(
        _load_json_if_exists(preprocess_root / "phase0_ready_snapshot.json"),
        draft.phase0_ready_snapshot,
    )

    work_identity_seed, work_identity_resolution = resolve_work_identity(reference_selection, work_id)
    primary_profile, secondary_profile, profile_resolution = resolve_profiles(reference_selection, cards)
    opening_bundle_contract, opening_contract_resolution = resolve_opening_bundle_contract(
        reference_selection,
        cards,
    )

    material_bundle_summary["opening_bundle_contract"] = deepcopy(opening_bundle_contract)
    work_identity = source_manifest.get("work_identity") if isinstance(source_manifest.get("work_identity"), dict) else {}
    work_identity["work_id"] = work_identity_seed["work_id"]
    work_identity["title"] = work_identity_seed["title"]
    work_identity["subtitle"] = work_identity_seed.get("subtitle", "")
    work_identity["commercial_label"] = work_identity_seed.get("commercial_label", "")
    work_identity["slug_aliases"] = deepcopy(work_identity_seed.get("slug_aliases", []))
    work_identity["primary_profile"] = primary_profile
    work_identity["secondary_profile"] = secondary_profile
    source_manifest["work_identity"] = work_identity
    profile_lock["primary_profile"] = primary_profile
    profile_lock["secondary_profile"] = secondary_profile

    persisted_has_signal = any(
        _meaningful_value(payload)
        for payload in (
            _load_json_if_exists(preprocess_root / "source_manifest.json"),
            _load_json_if_exists(preprocess_root / "profile_lock.json"),
            _load_json_if_exists(preprocess_root / "material_bundle_summary.json"),
        )
    )
    stage0_source_mode = "mixed_stage0_preprocess_plus_reference_selection" if persisted_has_signal else "reference_selection_fallback_only"

    return (
        source_manifest,
        profile_lock,
        material_bundle_summary,
        phase0_ready_snapshot,
        cards,
        stage0_source_mode,
        work_identity_resolution,
        profile_resolution,
        opening_contract_resolution,
    )


def _resolve_title_seed(
    work_id: str,
    work_identity: dict[str, Any],
    existing_phase0: dict[str, Any],
    work_identity_resolution: str,
) -> tuple[str, str]:
    stage0_title = work_identity.get("title")
    if _meaningful_text(stage0_title):
        return str(stage0_title).strip(), work_identity_resolution

    existing_title = existing_phase0.get("title")
    if _meaningful_text(existing_title):
        return (
            str(existing_title).strip(),
            "existing phase0 title retained because Stage0 work identity title is unresolved",
        )

    return (
        f"TODO: replace title for {work_id}",
        "placeholder title retained; add work_identity_override.title in reference_selection",
    )


def build_phase0_seed_from_stage0(work_id: str, root: Path = ROOT) -> Phase0SeedResult:
    (
        source_manifest,
        profile_lock,
        material_bundle_summary,
        phase0_ready_snapshot,
        cards,
        stage0_source_mode,
        work_identity_resolution,
        profile_resolution,
        opening_contract_resolution,
    ) = _resolve_stage0_authority(work_id, root=root)

    project_root = root / "narrative_ssot" / "50_projects" / work_id
    phase0_path = project_root / "30_planning" / "phase0_design.json"
    existing_phase0 = _load_json_if_exists(phase0_path)

    work_identity = source_manifest.get("work_identity") if isinstance(source_manifest.get("work_identity"), dict) else {}
    contract = material_bundle_summary.get("opening_bundle_contract")
    if not isinstance(contract, dict):
        raise ValueError("Stage0 material_bundle_summary is missing opening_bundle_contract")

    title_seed, title_resolution = _resolve_title_seed(
        work_id,
        work_identity,
        existing_phase0,
        work_identity_resolution,
    )
    protagonist_seed = _pick_text(
        existing_phase0.get("protagonist"),
        "TODO: replace protagonist from canon source",
    )

    resource_axis = profile_lock.get("resource_axis") if isinstance(profile_lock.get("resource_axis"), list) else []
    power_axis = profile_lock.get("power_axis") if isinstance(profile_lock.get("power_axis"), list) else []
    control_axis = profile_lock.get("control_axis") if isinstance(profile_lock.get("control_axis"), list) else []
    payoff_axis = profile_lock.get("payoff_axis") if isinstance(profile_lock.get("payoff_axis"), list) else []
    failure_axis = profile_lock.get("failure_axis") if isinstance(profile_lock.get("failure_axis"), list) else []
    work_identity_surface_seed = {
        "work_id": work_id,
        "title": title_seed,
        "subtitle": str(work_identity.get("subtitle") or "").strip(),
        "commercial_label": str(work_identity.get("commercial_label") or "").strip(),
        "slug_aliases": deepcopy(
            work_identity.get("slug_aliases") if isinstance(work_identity.get("slug_aliases"), list) else []
        ),
        "primary_profile": str(work_identity.get("primary_profile") or "").strip(),
        "secondary_profile": str(work_identity.get("secondary_profile") or "").strip(),
    }

    core_fantasy_seed = _pick_text(
        existing_phase0.get("core_fantasy"),
        _shorten(
            f"{_first_meaningful(power_axis, '주인공 우위')}를 활용해 "
            f"{contract.get('bundle_goal', 'opening payoff')}를 확보하고 "
            f"{_first_meaningful(resource_axis, '다음 성장 자산')}으로 확장한다.",
        ),
    )

    scene_details = material_bundle_summary.get("scene_details") if isinstance(material_bundle_summary.get("scene_details"), list) else []
    crisis_candidates = material_bundle_summary.get("crisis_candidates") if isinstance(material_bundle_summary.get("crisis_candidates"), list) else []
    events = material_bundle_summary.get("events") if isinstance(material_bundle_summary.get("events"), list) else []
    hard_constraints = source_manifest.get("hard_constraints") if isinstance(source_manifest.get("hard_constraints"), list) else []
    do_not_fake = source_manifest.get("do_not_fake") if isinstance(source_manifest.get("do_not_fake"), list) else []

    opening_arc_seed = {
        "macro_battlefield": contract.get("macro_battlefield"),
        "bundle_window": contract.get("bundle_window"),
        "bundle_goal": contract.get("bundle_goal"),
        "macro_battlefield_map": deepcopy(contract.get("macro_battlefield_map", [])),
        "first_signboard_block": contract.get("first_signboard_block"),
        "representative_reevaluation_block": contract.get("representative_reevaluation_block"),
        "next_battlefield_ticket_block": contract.get("next_battlefield_ticket_block"),
        "scene_axes": deepcopy(scene_details[:3]),
        "linked_crises": deepcopy(crisis_candidates[:2]),
    }

    representative_spike_seed = {
        "type": "opening_reader_earning",
        "target_block": contract.get("representative_reevaluation_block"),
        "signal": _first_meaningful(events, contract.get("bundle_goal", "")),
        "proof": _first_meaningful(scene_details, contract.get("macro_battlefield", "")),
    }

    growth_axis_seed = {
        "primary_profile": profile_lock.get("primary_profile", ""),
        "secondary_profile": profile_lock.get("secondary_profile", ""),
        "resource_axis": deepcopy(resource_axis[:3]),
        "power_axis": deepcopy(power_axis[:3]),
        "control_axis": deepcopy(control_axis[:3]),
    }

    opponent_transition_plan_seed = {
        "opening_pressures": deepcopy(crisis_candidates[:3]),
        "hard_constraints": deepcopy(hard_constraints[:3]),
        "do_not_fake": deepcopy(do_not_fake[:3]),
    }

    payoff_axis_seed = {
        "opening_bundle_goal": contract.get("bundle_goal"),
        "reader_earnings": deepcopy(payoff_axis[:3]),
        "failure_axis": deepcopy(failure_axis[:3]),
        "next_ticket_block": contract.get("next_battlefield_ticket_block"),
    }

    planning_seed_authority = {
        "seed_source": "stage0_authority_v2",
        "stage0_source_mode": stage0_source_mode,
        "work_identity_resolution": work_identity_resolution,
        "title_resolution": title_resolution,
        "profile_resolution": profile_resolution,
        "opening_contract_resolution": opening_contract_resolution,
        "work_identity_surface": deepcopy(work_identity_surface_seed),
        "source_paths": {
            "reference_selection": f"narrative_ssot/50_projects/{work_id}/10_reference_selection/reference_selection.json",
            "source_manifest": f"narrative_ssot/50_projects/{work_id}/20_preprocess/source_manifest.json",
            "profile_lock": f"narrative_ssot/50_projects/{work_id}/20_preprocess/profile_lock.json",
            "material_bundle_summary": f"narrative_ssot/50_projects/{work_id}/20_preprocess/material_bundle_summary.json",
            "phase0_ready_snapshot": f"narrative_ssot/50_projects/{work_id}/20_preprocess/phase0_ready_snapshot.json",
        },
        "selected_cards": [
            {
                "card_slug": card.card_slug,
                "track": card.track,
                "handoff_label": card.handoff_label,
            }
            for card in cards
        ],
    }

    seed_payload = {
        "work_id": work_id,
        "title": title_seed,
        "work_identity_surface": deepcopy(work_identity_surface_seed),
        "protagonist": protagonist_seed,
        "core_fantasy": core_fantasy_seed,
        "opening_arc": opening_arc_seed,
        "opening_bundle_contract": deepcopy(contract),
        "representative_spike": representative_spike_seed,
        "growth_axis": growth_axis_seed,
        "opponent_transition_plan": opponent_transition_plan_seed,
        "payoff_axis": payoff_axis_seed,
        "planning_seed_authority": planning_seed_authority,
    }

    merged = _merge_value(existing_phase0, seed_payload)
    merged["work_id"] = work_id
    merged["title"] = title_seed
    merged["work_identity_surface"] = deepcopy(work_identity_surface_seed)
    merged["protagonist"] = protagonist_seed
    merged["core_fantasy"] = core_fantasy_seed
    merged["opening_arc"] = _merge_value(existing_phase0.get("opening_arc"), opening_arc_seed)
    merged["opening_bundle_contract"] = deepcopy(contract)
    merged["representative_spike"] = _merge_value(
        existing_phase0.get("representative_spike"),
        representative_spike_seed,
    )
    merged["growth_axis"] = _merge_value(existing_phase0.get("growth_axis"), growth_axis_seed)
    merged["opponent_transition_plan"] = _merge_value(
        existing_phase0.get("opponent_transition_plan"),
        opponent_transition_plan_seed,
    )
    merged["payoff_axis"] = _merge_value(existing_phase0.get("payoff_axis"), payoff_axis_seed)
    merged["planning_seed_authority"] = planning_seed_authority

    if isinstance(phase0_ready_snapshot, dict):
        merged["planning_seed_authority"]["phase0_ready_snapshot"] = {
            "identity_locked": phase0_ready_snapshot.get("identity_locked"),
            "profile_locked": phase0_ready_snapshot.get("profile_locked"),
            "material_sufficient": phase0_ready_snapshot.get("material_sufficient"),
            "manual_audit_pass": phase0_ready_snapshot.get("manual_audit_pass"),
        }

    return Phase0SeedResult(
        phase0_design=merged,
        stage0_source_mode=stage0_source_mode,
        work_identity_resolution=work_identity_resolution,
        profile_resolution=profile_resolution,
        opening_contract_resolution=opening_contract_resolution,
        title_resolution=title_resolution,
        updated_paths=(),
    )


def sync_phase0_seed_from_stage0(
    work_id: str,
    root: Path = ROOT,
    write: bool = True,
) -> Phase0SeedResult:
    result = build_phase0_seed_from_stage0(work_id, root=root)
    planning_path = root / "narrative_ssot" / "50_projects" / work_id / "30_planning" / "phase0_design.json"
    updated_paths: list[str] = []
    if write:
        _write_json(planning_path, result.phase0_design)
        updated_paths.append(str(planning_path))
    return Phase0SeedResult(
        phase0_design=result.phase0_design,
        stage0_source_mode=result.stage0_source_mode,
        work_identity_resolution=result.work_identity_resolution,
        profile_resolution=result.profile_resolution,
        opening_contract_resolution=result.opening_contract_resolution,
        title_resolution=result.title_resolution,
        updated_paths=tuple(updated_paths),
    )
