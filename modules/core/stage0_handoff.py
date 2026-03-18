"""Shared Stage 0 -> Stage 2 handoff helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PlotRoadmapStatus:
    roadmap: list[dict[str, Any]]
    warnings: list[str]
    source: str

    @property
    def ready(self) -> bool:
        return bool(self.roadmap) and not self.warnings


def build_plot_roadmap_from_treatment(treatment: Any) -> list[dict[str, Any]]:
    """Normalize Stage 0 treatment blocks into the flat roadmap shape Stage 2 reads."""
    if isinstance(treatment, dict):
        treatment = treatment.get("treatments", [])
    if not isinstance(treatment, list):
        return []

    roadmap: list[dict[str, Any]] = []
    for i, block in enumerate(treatment):
        if not isinstance(block, dict):
            continue
        entry = {"block_no": i + 1}
        entry.update(block)
        roadmap.append(entry)
    return roadmap


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
