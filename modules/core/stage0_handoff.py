"""Shared Stage 0 -> Stage 2 handoff helpers."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any

RUNTIME_PROTAGONIST_KEYS = ("world_origin", "incarnation_type", "pov", "external_pov_insert_policy")


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

    top_level_metadata = {key: deepcopy(value) for key, value in bible.items() if isinstance(key, str) and key.startswith("_")}
    master = bible.get("MasterBible")
    if isinstance(master, dict):
        canonical = deepcopy(bible)
        master_root = canonical["MasterBible"]
    else:
        canonical = dict(top_level_metadata)
        master_root = {key: deepcopy(value) for key, value in bible.items() if not (isinstance(key, str) and key.startswith("_"))}
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
