"""Shared Stage 0 -> Stage 2 handoff helpers."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

RUNTIME_PROTAGONIST_KEYS = ("world_origin", "incarnation_type", "pov", "external_pov_insert_policy")
STAGE0_CONTRACT_KEY = "_stage0_contract"
STAGE0_CONTRACT_SCHEMA = "stage0.material.v1"
STAGE0_RUNTIME_HANDOFF_KEY = "_stage0_runtime_handoff"
STAGE0_RUNTIME_HANDOFF_SCHEMA = "stage0.runtime_handoff.v1"
STAGE0_RUNTIME_HANDOFF_OWNER = "db_anchor:bible"
STAGE0_RUNTIME_HANDOFF_ANCHOR = "bible"
STAGE0_RUNTIME_HANDOFF_SURFACE = "MasterBible.plot_roadmap"
STAGE0_RUNTIME_HANDOFF_CONSUMER_MODE = "db_anchor_first"
STAGE0_TREATMENT_ROLE = "canonical_material_source"
STAGE0_BIBLE_ROLE = "bi_projection_artifact"
PLOT_ROADMAP_LINEAGE_ANCHOR = "stage2_arcs_source_lineage"
PLOT_ROADMAP_LINEAGE_SCHEMA = "stage0.plot_roadmap_lineage.v1"


@dataclass
class PlotRoadmapStatus:
    roadmap: list[dict[str, Any]]
    warnings: list[str]
    source: str

    @property
    def ready(self) -> bool:
        return bool(self.roadmap) and not self.warnings


def _extract_block_no(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float):
        if value.is_integer() and value > 0:
            return int(value)
        return None
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return None


def resolve_treatment_block_sequence(treatment: Any) -> list[Any] | None:
    if isinstance(treatment, list):
        return treatment
    if not isinstance(treatment, dict):
        return None

    candidate_lists: list[list[Any]] = []
    for key in ("blocks", "treatments"):
        value = treatment.get(key)
        if isinstance(value, list):
            candidate_lists.append(value)
    if not candidate_lists:
        return None
    return next((blocks for blocks in candidate_lists if blocks), candidate_lists[0])


def get_effective_bible_root(bible: Any) -> dict[str, Any]:
    if not isinstance(bible, dict):
        return {}
    master = bible.get("MasterBible")
    return master if isinstance(master, dict) else bible


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _build_stage0_contract_base(*, artifact_role: str, artifact_truth: str) -> dict[str, Any]:
    return {
        "schema": STAGE0_CONTRACT_SCHEMA,
        "artifact_role": artifact_role,
        "artifact_truth": artifact_truth,
        "projection_model": "canonical_material_schema_to_projection",
        "projection_source": "treatment.blocks",
        "field_authority": {
            "treatment_blocks": "treatment.blocks",
            "plot_roadmap": "MasterBible.plot_roadmap",
            "protagonist_config": "MasterBible.protagonist_config",
        },
        "runtime_handoff": {
            "owner": STAGE0_RUNTIME_HANDOFF_OWNER,
            "stage2_surface": STAGE0_RUNTIME_HANDOFF_SURFACE,
            "stage2_consumer_mode": STAGE0_RUNTIME_HANDOFF_CONSUMER_MODE,
        },
        "compatibility_bridges": {
            "ensure_plot_roadmap": "compatibility_bridge",
            "force_sync_v25_dna": "compatibility_bridge",
        },
    }


def build_stage0_treatment_contract() -> dict[str, Any]:
    return _build_stage0_contract_base(
        artifact_role=STAGE0_TREATMENT_ROLE,
        artifact_truth="treatment.blocks",
    )


def build_stage0_bible_contract(*, treatment: Any | None = None) -> dict[str, Any]:
    contract = _build_stage0_contract_base(
        artifact_role=STAGE0_BIBLE_ROLE,
        artifact_truth="MasterBible",
    )
    projected_blocks = normalize_treatment_blocks(treatment) if treatment is not None else []
    contract["projection_block_count"] = len(projected_blocks)
    return contract


def resolve_stage0_treatment_contract(treatment: Any) -> dict[str, Any]:
    if isinstance(treatment, dict) and isinstance(treatment.get(STAGE0_CONTRACT_KEY), dict):
        return deepcopy(treatment[STAGE0_CONTRACT_KEY])
    return build_stage0_treatment_contract()


def resolve_stage0_bible_contract(bible: Any, *, treatment: Any | None = None) -> dict[str, Any]:
    if isinstance(bible, dict):
        if isinstance(bible.get(STAGE0_CONTRACT_KEY), dict):
            return deepcopy(bible[STAGE0_CONTRACT_KEY])
        master = bible.get("MasterBible")
        if isinstance(master, dict) and isinstance(master.get(STAGE0_CONTRACT_KEY), dict):
            return deepcopy(master[STAGE0_CONTRACT_KEY])
    return build_stage0_bible_contract(treatment=treatment)


def _contract_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _contract_text(value: Any, fallback: str) -> str:
    text = _as_text(value)
    return text or fallback


def build_stage0_runtime_handoff_summary(bible: Any, *, treatment: Any | None = None) -> dict[str, Any]:
    contract = resolve_stage0_bible_contract(bible, treatment=treatment)
    runtime_handoff = _contract_dict(contract.get("runtime_handoff"))
    field_authority = _contract_dict(contract.get("field_authority"))
    bridges = _contract_dict(contract.get("compatibility_bridges"))
    default_bridges = _build_stage0_contract_base(
        artifact_role=STAGE0_BIBLE_ROLE,
        artifact_truth="MasterBible",
    )["compatibility_bridges"]

    return {
        "schema": STAGE0_RUNTIME_HANDOFF_SCHEMA,
        "runtime_handoff_owner": _contract_text(runtime_handoff.get("owner"), STAGE0_RUNTIME_HANDOFF_OWNER),
        "runtime_handoff_anchor": STAGE0_RUNTIME_HANDOFF_ANCHOR,
        "runtime_handoff_surface": _contract_text(
            runtime_handoff.get("stage2_surface"),
            STAGE0_RUNTIME_HANDOFF_SURFACE,
        ),
        "stage2_consumer_mode": _contract_text(
            runtime_handoff.get("stage2_consumer_mode"),
            STAGE0_RUNTIME_HANDOFF_CONSUMER_MODE,
        ),
        "projection_source": _contract_text(contract.get("projection_source"), "treatment.blocks"),
        "plot_roadmap_authority": _contract_text(
            field_authority.get("plot_roadmap"),
            STAGE0_RUNTIME_HANDOFF_SURFACE,
        ),
        "persistence_call": f"save_v20_anchor:{STAGE0_RUNTIME_HANDOFF_ANCHOR}",
        "compatibility_bridges": {
            name: _contract_text(bridges.get(name), default_state) for name, default_state in default_bridges.items()
        },
    }


def _normalize_contract_genre(raw_genre: str) -> str:
    genre = _as_text(raw_genre).lower()
    if "wuxia" in genre or "무협" in genre:
        return "wuxia"
    if "investment" in genre or "투자" in genre or "chaebol" in genre or "재벌" in genre:
        return "investment"
    return genre


def _extract_contract_genre(bible: Any, *, explicit_hint: str = "") -> str:
    if explicit_hint:
        return explicit_hint

    master = get_effective_bible_root(bible)
    project_data = master.get("ProjectData", {}) if isinstance(master, dict) else {}
    meta = project_data.get("MetaInfo", {}) if isinstance(project_data, dict) else {}
    candidates = (
        bible.get("_genre") if isinstance(bible, dict) else None,
        meta.get("genre"),
        meta.get("genre_archetype"),
        meta.get("subgenre"),
    )
    for candidate in candidates:
        text = _as_text(candidate)
        if text:
            return text
    return ""


def _infer_world_origin_and_incarnation(
    protagonist_config: dict[str, Any],
    *,
    genre_hint: str,
) -> tuple[str, str]:
    world_origin = _as_text(protagonist_config.get("world_origin"))
    incarnation_type = _as_text(protagonist_config.get("incarnation_type"))
    if world_origin and incarnation_type:
        return world_origin, incarnation_type

    is_regressor = bool(protagonist_config.get("is_regressor"))
    has_regression_marker = any(
        protagonist_config.get(key) for key in ("regression_origin", "regression_point", "regression_mechanic")
    )
    normalized_genre = _normalize_contract_genre(genre_hint)

    if not world_origin:
        world_origin = "원시인" if normalized_genre == "wuxia" else "현대인"

    if not incarnation_type:
        incarnation_type = "회귀자" if (is_regressor or has_regression_marker) else "일반"

    return world_origin, incarnation_type


def normalize_treatment_blocks(treatment: Any) -> list[dict[str, Any]]:
    blocks = resolve_treatment_block_sequence(treatment)
    if blocks is None:
        return []

    normalized: list[dict[str, Any]] = []
    for index, block in enumerate(blocks, start=1):
        if not isinstance(block, dict):
            continue

        entry = dict(block)
        entry["block_no"] = (
            _extract_block_no(entry.get("block_no"))
            or _extract_block_no(entry.get("block"))
            or _extract_block_no(entry.get("block_id"))
            or index
        )
        normalized.append(entry)
    return normalized


def normalize_treatment_to_canonical_view(treatment: Any) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    blocks = normalize_treatment_blocks(treatment)

    canonical: dict[str, Any] = {
        "_schema": "tr.compat",
        "_total_blocks": len(blocks),
        "blocks": blocks,
    }

    if isinstance(treatment, list):
        warnings.append("treatment uses raw list wrapper; canonical wrapper should be dict.blocks")
        return canonical, warnings

    if not isinstance(treatment, dict):
        warnings.append(f"treatment is not dict/list ({type(treatment).__name__})")
        return canonical, warnings

    if "blocks" in treatment:
        source_blocks = treatment.get("blocks")
        if not isinstance(source_blocks, list):
            warnings.append("treatment.blocks is not a list")
    elif "treatments" in treatment:
        warnings.append("treatment uses legacy treatments wrapper; canonical wrapper should be blocks")
    else:
        warnings.append("treatment wrapper missing blocks/treatments list")

    for key, value in treatment.items():
        if key in {"blocks", "treatments"}:
            continue
        canonical[key] = deepcopy(value)

    if "_schema" not in canonical or not isinstance(canonical.get("_schema"), str) or not canonical["_schema"].strip():
        canonical["_schema"] = "tr.compat"
    canonical["_total_blocks"] = len(blocks)
    canonical["blocks"] = blocks
    return canonical, warnings


def build_plot_roadmap_from_treatment(treatment: Any) -> list[dict[str, Any]]:
    """Normalize Stage 0 treatment blocks into the flat roadmap shape Stage 2 reads."""
    return normalize_treatment_blocks(treatment)


def build_plot_roadmap_lineage(roadmap: Any) -> dict[str, Any]:
    normalized = normalize_treatment_blocks(roadmap)
    encoded = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )
    return {
        "schema": PLOT_ROADMAP_LINEAGE_SCHEMA,
        "fingerprint": hashlib.sha256(encoded).hexdigest(),
        "block_count": len(normalized),
        "authority": STAGE0_RUNTIME_HANDOFF_SURFACE,
    }


def plot_roadmap_lineage_matches(saved_lineage: Any, current_lineage: Any) -> bool:
    if not isinstance(saved_lineage, dict) or not isinstance(current_lineage, dict):
        return False
    return (
        saved_lineage.get("schema") == PLOT_ROADMAP_LINEAGE_SCHEMA
        and current_lineage.get("schema") == PLOT_ROADMAP_LINEAGE_SCHEMA
        and str(saved_lineage.get("fingerprint") or "") == str(current_lineage.get("fingerprint") or "")
    )


def load_plot_roadmap_lineage(project: Any) -> dict[str, Any]:
    db = getattr(project, "db", None)
    load_anchor = getattr(db, "load_anchor", None)
    if not callable(load_anchor):
        return {}
    lineage = load_anchor(PLOT_ROADMAP_LINEAGE_ANCHOR)
    return lineage if isinstance(lineage, dict) else {}


def cached_arcs_source_lineage_matches(
    project: Any,
    *,
    cached_arcs: Any,
    roadmap: Any,
) -> bool:
    if not isinstance(cached_arcs, list) or not cached_arcs:
        return True
    saved_lineage = load_plot_roadmap_lineage(project)
    if not saved_lineage:
        return True
    current_lineage = build_plot_roadmap_lineage(roadmap)
    return plot_roadmap_lineage_matches(saved_lineage, current_lineage)


def repair_runtime_protagonist_contract(
    payload: dict[str, Any],
    *,
    genre_hint: str = "",
    fallback_pov: str = "",
    fallback_external_pov_insert_policy: str = "",
) -> list[str]:
    warnings: list[str] = []
    master = get_effective_bible_root(payload)
    protagonist = master.get("protagonist_config")
    if protagonist is None or not isinstance(protagonist, dict):
        master["protagonist_config"] = {}
        protagonist = master["protagonist_config"]
        warnings.append("created protagonist_config dict for BI canonicalization")

    contract_genre = _normalize_contract_genre(_extract_contract_genre(payload, explicit_hint=genre_hint))
    world_origin, incarnation_type = _infer_world_origin_and_incarnation(protagonist, genre_hint=contract_genre)
    if not protagonist.get("world_origin") and world_origin:
        protagonist["world_origin"] = world_origin
        warnings.append(f"filled protagonist_config.world_origin='{world_origin}'")
    if not protagonist.get("incarnation_type") and incarnation_type:
        protagonist["incarnation_type"] = incarnation_type
        warnings.append(f"filled protagonist_config.incarnation_type='{incarnation_type}'")

    pov = _as_text(protagonist.get("pov")) or _as_text(fallback_pov) or "3인칭"
    if not protagonist.get("pov"):
        protagonist["pov"] = pov
        if fallback_pov:
            warnings.append(f"borrowed protagonist_config.pov fallback '{pov}'")
        else:
            warnings.append(f"filled protagonist_config.pov='{pov}'")

    from modules.core.project_support import (
        default_external_pov_insert_policy,
        normalize_external_pov_insert_policy,
    )

    external_policy = _as_text(protagonist.get("external_pov_insert_policy")) or _as_text(
        fallback_external_pov_insert_policy
    )
    if not external_policy:
        external_policy = default_external_pov_insert_policy(pov, genre=contract_genre)
    external_policy = normalize_external_pov_insert_policy(
        external_policy,
        primary_pov=pov,
        genre=contract_genre,
    )
    if not protagonist.get("external_pov_insert_policy"):
        protagonist["external_pov_insert_policy"] = external_policy
        if fallback_external_pov_insert_policy:
            warnings.append("borrowed protagonist_config.external_pov_insert_policy fallback")
        else:
            warnings.append(f"filled protagonist_config.external_pov_insert_policy='{external_policy}'")

    return warnings


def repair_bible_plot_roadmap(
    payload: dict[str, Any],
    *,
    treatment: Any | None,
    force_treatment_roadmap: bool = False,
) -> list[str]:
    if treatment is None:
        return []

    warnings: list[str] = []
    master = get_effective_bible_root(payload)
    current = master.get("plot_roadmap")
    current_warnings = validate_plot_roadmap_entries(current) if current is not None else ["plot_roadmap missing"]

    projected = build_plot_roadmap_from_treatment(treatment)
    projected_warnings = validate_plot_roadmap_entries(projected)
    if not projected:
        return warnings

    should_replace = force_treatment_roadmap
    if not should_replace:
        if not isinstance(current, list) or not current:
            should_replace = True
        elif current_warnings and len(projected_warnings) < len(current_warnings):
            should_replace = True

    if should_replace:
        master["plot_roadmap"] = projected
        if force_treatment_roadmap:
            warnings.append("force-replaced plot_roadmap with treatment-projected canonical roadmap")
        elif current_warnings:
            warnings.append("replaced weak plot_roadmap with treatment-projected canonical roadmap")
    return warnings


def canonicalize_treatment_payload(
    treatment: Any,
    *,
    schema: str = "tr.v1",
) -> tuple[dict[str, Any], list[str]]:
    payload, warnings = normalize_treatment_to_canonical_view(treatment)
    payload["_schema"] = schema
    payload["_total_blocks"] = len(payload.get("blocks", [])) if isinstance(payload.get("blocks"), list) else 0
    payload[STAGE0_CONTRACT_KEY] = build_stage0_treatment_contract()

    from modules.core.response_schemas import validate_treatment_canonical_structure

    valid, errors, _canonical_warnings = validate_treatment_canonical_structure(payload)
    if not valid:
        raise ValueError(f"canonical TR validation failed: {errors}")
    return payload, warnings


def build_plot_roadmap_from_saved_arcs(app: Any) -> list[dict[str, Any]]:
    """Promote saved arc stubs into the roadmap placeholder shape used by Stage 2."""
    project = getattr(app, "current_project", None)
    db = getattr(project, "db", None)
    if db is None or not hasattr(db, "load_anchor"):
        return []

    try:
        arcs = db.load_anchor("arcs") or []
    except Exception:
        return []

    if isinstance(arcs, dict):
        arcs = list(arcs.values())
    if not isinstance(arcs, list):
        return []

    roadmap: list[dict[str, Any]] = []
    for i, arc in enumerate(arcs):
        if not isinstance(arc, dict):
            continue
        entry = {"block_no": i + 1}
        for key in (
            "arc_no",
            "volume_no",
            "ep_start",
            "ep_end",
            "ep_count",
            "tactical_doc",
            "key_events",
            "joint_docs",
            "state_changes",
            "_stub",
            "_source",
        ):
            if key in arc:
                entry[key] = arc[key]
        if "ep_count" not in entry and isinstance(entry.get("ep_start"), int) and isinstance(entry.get("ep_end"), int):
            entry["ep_count"] = max(0, entry["ep_end"] - entry["ep_start"] + 1)
        roadmap.append(entry)
    return roadmap


def _append_nonempty(parts: list[str], value: Any) -> None:
    if isinstance(value, str) and value.strip():
        parts.append(value.strip())


def _collect_stage2_payload_fragments(entry: dict[str, Any]) -> list[str]:
    """Mirror the payload classes real Stage 2 consumers can actually use."""
    parts: list[str] = []

    for key in ("context", "event_villain", "solution", "reward"):
        _append_nonempty(parts, entry.get(key))

    content_obj = entry.get("content", {})
    if isinstance(content_obj, dict):
        for key in ("context", "event_villain", "solution", "reward"):
            _append_nonempty(parts, content_obj.get(key))
    else:
        _append_nonempty(parts, content_obj)

    raw_data = entry.get("raw_data", {})
    if isinstance(raw_data, dict):
        raw_content = raw_data.get("content", {})
        if isinstance(raw_content, dict):
            for key in ("context", "event_villain", "solution", "reward"):
                _append_nonempty(parts, raw_content.get(key))
        raw_genre_ext = raw_data.get("genre_ext", {})
        if isinstance(raw_genre_ext, dict):
            for value in raw_genre_ext.values():
                _append_nonempty(parts, value)
        _append_nonempty(parts, raw_data.get("title"))

    genre_ext = entry.get("genre_ext", {})
    if isinstance(genre_ext, dict):
        for value in genre_ext.values():
            _append_nonempty(parts, value)

    tactical_doc = entry.get("tactical_doc")
    if isinstance(tactical_doc, str) and tactical_doc.strip():
        parts.append(tactical_doc.strip())

    key_events = entry.get("key_events")
    if isinstance(key_events, list):
        for item in key_events:
            _append_nonempty(parts, item)
    else:
        _append_nonempty(parts, key_events)

    return parts


def normalize_bible_to_canonical_view(
    bible: Any,
    *,
    treatment: Any | None = None,
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []

    if not isinstance(bible, dict):
        return {"MasterBible": {}}, [f"bible is not a dict ({type(bible).__name__})"]

    top_level_metadata = {
        key: deepcopy(value) for key, value in bible.items() if isinstance(key, str) and key.startswith("_")
    }
    master = bible.get("MasterBible")
    if isinstance(master, dict):
        canonical = deepcopy(bible)
        master_root = canonical["MasterBible"]
    else:
        canonical = dict(top_level_metadata)
        master_root = {
            key: deepcopy(value) for key, value in bible.items() if not (isinstance(key, str) and key.startswith("_"))
        }
        canonical["MasterBible"] = master_root
        warnings.append("MasterBible wrapper missing; wrapped root into canonical BI view")

    if not isinstance(master_root, dict):
        canonical["MasterBible"] = {}
        return canonical, warnings + ["MasterBible is not a dict"]

    project_data = master_root.get("ProjectData")
    if isinstance(project_data, dict):
        lifted_protagonist = project_data.get("protagonist_config")
        if "protagonist_config" not in master_root and isinstance(lifted_protagonist, dict):
            master_root["protagonist_config"] = deepcopy(lifted_protagonist)
            warnings.append("lifted ProjectData.protagonist_config into MasterBible.protagonist_config")

    protagonist_config = master_root.get("protagonist_config")
    if protagonist_config is None:
        master_root["protagonist_config"] = {}
        protagonist_config = master_root["protagonist_config"]
        warnings.append("protagonist_config missing at effective BI root")
    elif not isinstance(protagonist_config, dict):
        master_root["protagonist_config"] = {}
        protagonist_config = master_root["protagonist_config"]
        warnings.append("protagonist_config is not a dict at effective BI root")

    runtime_missing = [key for key in RUNTIME_PROTAGONIST_KEYS if not protagonist_config.get(key)]
    if runtime_missing:
        warnings.append(f"runtime protagonist keys missing: {', '.join(runtime_missing)}")

    root_sidecar = bible.get("plot_roadmap")
    if "plot_roadmap" not in master_root and isinstance(root_sidecar, list):
        master_root["plot_roadmap"] = normalize_treatment_blocks(root_sidecar)
        warnings.append("lifted root-level plot_roadmap into MasterBible.plot_roadmap")
    elif "plot_roadmap" in master_root:
        master_root["plot_roadmap"] = normalize_treatment_blocks(master_root.get("plot_roadmap"))

    if "plot_roadmap" not in master_root and treatment is not None:
        projected = build_plot_roadmap_from_treatment(treatment)
        if projected:
            master_root["plot_roadmap"] = projected
            warnings.append("projected plot_roadmap from treatment into canonical BI view")

    if "plot_roadmap" not in master_root:
        master_root["plot_roadmap"] = []
        warnings.append("plot_roadmap missing at effective BI root")

    return canonical, warnings


def canonicalize_bible_payload(
    bible: Any,
    *,
    treatment: Any | None = None,
    force_treatment_roadmap: bool = False,
    genre_hint: str = "",
    fallback_pov: str = "",
    fallback_external_pov_insert_policy: str = "",
) -> tuple[dict[str, Any], list[str]]:
    payload, warnings = normalize_bible_to_canonical_view(bible, treatment=treatment)
    warnings.extend(
        repair_runtime_protagonist_contract(
            payload,
            genre_hint=genre_hint,
            fallback_pov=fallback_pov,
            fallback_external_pov_insert_policy=fallback_external_pov_insert_policy,
        )
    )
    warnings.extend(
        repair_bible_plot_roadmap(
            payload,
            treatment=treatment,
            force_treatment_roadmap=force_treatment_roadmap,
        )
    )

    master = payload.get("MasterBible")
    if isinstance(master, dict):
        if "plot_roadmap" in payload and isinstance(master.get("plot_roadmap"), list):
            payload.pop("plot_roadmap", None)
            warnings.append("removed root-level plot_roadmap sidecar from canonical BI copy")

        project_data = master.get("ProjectData")
        if (
            isinstance(project_data, dict)
            and "protagonist_config" in project_data
            and isinstance(master.get("protagonist_config"), dict)
        ):
            project_data.pop("protagonist_config", None)
            warnings.append("removed ProjectData.protagonist_config sidecar from canonical BI copy")
        if isinstance(master.get(STAGE0_CONTRACT_KEY), dict):
            master.pop(STAGE0_CONTRACT_KEY, None)
            warnings.append("removed MasterBible._stage0_contract sidecar from canonical BI copy")
        if isinstance(master.get(STAGE0_RUNTIME_HANDOFF_KEY), dict):
            master.pop(STAGE0_RUNTIME_HANDOFF_KEY, None)
            warnings.append("removed MasterBible._stage0_runtime_handoff sidecar from canonical BI copy")

    payload[STAGE0_CONTRACT_KEY] = build_stage0_bible_contract(treatment=treatment)
    payload[STAGE0_RUNTIME_HANDOFF_KEY] = build_stage0_runtime_handoff_summary(payload, treatment=treatment)

    from modules.core.response_schemas import validate_bible_canonical_structure

    valid, errors, _canonical_warnings = validate_bible_canonical_structure(payload)
    if not valid:
        raise ValueError(f"canonical BI validation failed: {errors}")
    return payload, warnings


def validate_plot_roadmap_entries(roadmap: Any) -> list[str]:
    """Validate the Stage 0 -> Stage 2 roadmap contract against real consumer fields."""
    if not isinstance(roadmap, list):
        return [f"plot_roadmap is not a list ({type(roadmap).__name__})"]
    if not roadmap:
        return ["plot_roadmap is empty"]

    warnings: list[str] = []
    for i, entry in enumerate(roadmap):
        if not isinstance(entry, dict):
            warnings.append(f"roadmap[{i}]: entry is not dict ({type(entry).__name__})")
            continue
        if "block_no" not in entry:
            warnings.append(f"roadmap[{i}]: block_no missing")

        payload_fragments = _collect_stage2_payload_fragments(entry)
        has_title = bool(str(entry.get("title", "") or "").strip())
        has_summary = bool(str(entry.get("summary", "") or "").strip())
        if not payload_fragments:
            if has_title or has_summary:
                warnings.append(
                    f"roadmap[{i}] (block_no={entry.get('block_no', '?')}): "
                    "title/summary only; no Stage 2 consumer-backed payload"
                )
            else:
                warnings.append(
                    f"roadmap[{i}] (block_no={entry.get('block_no', '?')}): no content/tactical_doc/key_events payload"
                )
    return warnings


def check_plot_roadmap_ready(roadmap: Any, *, source: str = "existing") -> PlotRoadmapStatus:
    normalized = roadmap if isinstance(roadmap, list) else []
    return PlotRoadmapStatus(roadmap=normalized, warnings=validate_plot_roadmap_entries(roadmap), source=source)


def ensure_plot_roadmap(app: Any, bible: Any, treatment: Any) -> PlotRoadmapStatus:
    """Populate plot_roadmap when possible, then return the shared readiness verdict."""
    if not isinstance(bible, dict):
        return PlotRoadmapStatus(roadmap=[], warnings=["bible is not a dict"], source="invalid_bible")

    master = bible.get("MasterBible")
    bible_root = master if isinstance(master, dict) else bible
    existing = bible_root.get("plot_roadmap", [])
    if isinstance(existing, list) and existing:
        return check_plot_roadmap_ready(existing, source="existing")

    roadmap = build_plot_roadmap_from_treatment(treatment)
    source = "treatment"
    if not roadmap:
        roadmap = build_plot_roadmap_from_saved_arcs(app)
        source = "saved_arcs"
    if roadmap:
        bible_root["plot_roadmap"] = roadmap

    return check_plot_roadmap_ready(roadmap, source=source)
