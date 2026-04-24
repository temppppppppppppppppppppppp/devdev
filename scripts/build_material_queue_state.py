#!/usr/bin/env python3
"""Build a bounded material-side queue snapshot for ClickUp mirroring."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PREPROCESS_ROOT = ROOT / "treatments" / "preprocess"
CANON_ROOT = ROOT / "material_ssot" / "20_pitch" / "canon"
REGISTRY_JSON = ROOT / "material_ssot" / "00_governance" / "production-pair-operational-registry-v1.json"
DEFAULT_OUTPUT_PATH = ROOT / "docs" / "temp" / "material-queue-state.json"
DEFAULT_CANON_ROOT = CANON_ROOT
DEFAULT_REGISTRY_JSON = REGISTRY_JSON
DEPLOYABLE_GREENPLUS_CLOSEOUT = "deployable_greenplus_certified_manual_closeout"


@dataclass(slots=True)
class MaterialQueueItem:
    work_id: str
    sequential_status_path: Path | None
    live_status_path: Path | None
    canon_path: Path | None
    status: str
    queue_role: str
    material_stage: str


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _latest_live_status_path(work_id: str) -> Path | None:
    matches = sorted(ROOT.glob(f"docs/**/{work_id}_live_status.md"))
    if not matches:
        return None
    return matches[-1]


def _current_canon_root() -> Path:
    if CANON_ROOT != DEFAULT_CANON_ROOT:
        return CANON_ROOT
    return ROOT / "material_ssot" / "20_pitch" / "canon"


def _current_registry_json() -> Path:
    if REGISTRY_JSON != DEFAULT_REGISTRY_JSON:
        return REGISTRY_JSON
    return ROOT / "material_ssot" / "00_governance" / "production-pair-operational-registry-v1.json"


def _iter_registry_rows() -> list[dict[str, Any]]:
    registry_json = _current_registry_json()
    if not registry_json.is_file():
        return []
    payload = _read_json(registry_json)
    if not isinstance(payload, dict):
        return []
    return [row for row in payload.get("pairs", []) if isinstance(row, dict)]


def _excluded_canon_work_ids() -> set[str]:
    excluded: set[str] = set()
    for row in _iter_registry_rows():
        work_id = str(row.get("work_id") or "").strip()
        benchmark_alias = str(row.get("benchmark_alias") or "").strip().upper()
        if work_id and benchmark_alias == "RED":
            excluded.add(work_id)
    return excluded


def _candidate_canon_paths() -> dict[str, Path]:
    excluded = _excluded_canon_work_ids()
    paths: dict[str, Path] = {}
    canon_root = _current_canon_root()
    if not canon_root.is_dir():
        return paths
    for path in sorted(canon_root.glob("*.md")):
        stem = path.stem
        if stem in {"README", "canonical_pitch_template_v1"}:
            continue
        if stem.endswith("_RETIRE"):
            continue
        if stem in excluded:
            continue
        paths[stem] = path
    return paths


def _status_from_snapshot(snapshot: dict[str, Any]) -> tuple[str, str, str]:
    next_unit_type = str(snapshot.get("next_unit_type") or "").strip().lower()
    production_complete = bool(snapshot.get("production_complete"))
    bi_complete = bool(snapshot.get("bi_complete"))
    if next_unit_type == "complete" or (production_complete and bi_complete):
        return "completed", "historical_backing", "bi_production_complete"
    return "in_progress", "front_active", "tr_or_bi_production"


def _canon_only_status() -> tuple[str, str, str]:
    return "pending", "front_active", "canon_stage"


def _first_live_pair_path(root: Path, work_id: str) -> Path | None:
    if not root.is_dir():
        return None
    for path in sorted(root.glob(f"*{work_id}*.json")):
        if "_quarantine" in path.parts or "phase0" in path.parts or "preprocess" in path.parts:
            continue
        return path
    return None


def _registry_truth_path(row: dict[str, Any], work_id: str, bi_path: Path) -> Path:
    artifact_candidates = [
        str(row.get("benchmark_artifact") or "").strip(),
        str((row.get("opening_pacing_triage") or {}).get("artifact") or "").strip(),
    ]
    for raw_path in artifact_candidates:
        if not raw_path:
            continue
        candidate = ROOT / Path(raw_path)
        if candidate.is_file():
            return candidate
    return _latest_live_status_path(work_id) or bi_path


def _registry_completed_items() -> dict[str, Path]:
    completed: dict[str, Path] = {}
    for row in _iter_registry_rows():
        work_id = str(row.get("work_id") or "").strip()
        if not work_id or bool(row.get("reference_only")):
            continue
        benchmark_alias = str(row.get("benchmark_alias") or "").strip().upper()
        opening = row.get("opening_pacing_triage") if isinstance(row.get("opening_pacing_triage"), dict) else {}
        opening_use = str(opening.get("opening_exemplar_use") or "").strip()
        if benchmark_alias != "GREENPLUS" or opening_use != DEPLOYABLE_GREENPLUS_CLOSEOUT:
            continue
        tr_path = _first_live_pair_path(ROOT / "treatments", work_id)
        bi_path = _first_live_pair_path(ROOT / "bible", work_id)
        if tr_path is None or bi_path is None:
            continue
        completed[work_id] = _registry_truth_path(row, work_id, bi_path)
    return completed


def collect_material_queue_items(preprocess_root: Path = PREPROCESS_ROOT) -> list[MaterialQueueItem]:
    items_by_work_id: dict[str, MaterialQueueItem] = {}
    canon_paths = _candidate_canon_paths()
    if not preprocess_root.is_dir():
        preprocess_directories: list[Path] = []
    else:
        preprocess_directories = sorted(path for path in preprocess_root.iterdir() if path.is_dir())

    for directory in preprocess_directories:
        sequential_path = directory / "sequential_run_status.json"
        if not sequential_path.is_file():
            continue
        snapshot = _read_json(sequential_path)
        if not isinstance(snapshot, dict):
            continue
        work_id = str(snapshot.get("work_id") or directory.name).strip()
        if not work_id:
            continue
        status, queue_role, material_stage = _status_from_snapshot(snapshot)
        items_by_work_id[work_id] = MaterialQueueItem(
            work_id=work_id,
            sequential_status_path=sequential_path,
            live_status_path=_latest_live_status_path(work_id),
            canon_path=canon_paths.get(work_id),
            status=status,
            queue_role=queue_role,
            material_stage=material_stage,
        )

    for work_id, canon_path in canon_paths.items():
        if work_id in items_by_work_id:
            continue
        status, queue_role, material_stage = _canon_only_status()
        items_by_work_id[work_id] = MaterialQueueItem(
            work_id=work_id,
            sequential_status_path=None,
            live_status_path=_latest_live_status_path(work_id),
            canon_path=canon_path,
            status=status,
            queue_role=queue_role,
            material_stage=material_stage,
        )

    for work_id, truth_path in _registry_completed_items().items():
        existing = items_by_work_id.get(work_id)
        if existing is not None:
            if existing.status == "completed":
                continue
            if existing.sequential_status_path is not None and existing.status == "in_progress":
                continue
        items_by_work_id[work_id] = MaterialQueueItem(
            work_id=work_id,
            sequential_status_path=None,
            live_status_path=None,
            canon_path=truth_path,
            status="completed",
            queue_role="historical_backing",
            material_stage="bi_production_complete",
        )

    items = list(items_by_work_id.values())
    items.sort(key=lambda item: (item.status == "completed", item.work_id))
    return items


def build_material_queue_payload(
    preprocess_root: Path = PREPROCESS_ROOT,
    *,
    include_completed: bool = True,
) -> dict[str, Any]:
    items = collect_material_queue_items(preprocess_root)
    active_items = [item for item in items if item.status != "completed"]
    visible_items = items if include_completed else active_items
    active_count = len(active_items)
    queue_mode = "empty"
    if active_count == 1:
        queue_mode = "single"
    elif active_count > 1:
        queue_mode = "aggregate"

    payload_items = [
        {
            "topic": item.work_id,
            "temp_path": (
                item.sequential_status_path.relative_to(ROOT).as_posix()
                if item.sequential_status_path is not None
                else ""
            ),
            "canonical_path": (
                item.live_status_path.relative_to(ROOT).as_posix()
                if item.live_status_path is not None
                else (
                    item.canon_path.relative_to(ROOT).as_posix()
                    if item.canon_path is not None
                    else (
                        item.sequential_status_path.relative_to(ROOT).as_posix()
                        if item.sequential_status_path is not None
                        else ""
                    )
                )
            ),
            "status": item.status,
            "queue_role": item.queue_role,
            "material_stage": item.material_stage,
            "roadmap_rank": None,
            "depends_on": [],
            "mirror_present": item.sequential_status_path.is_file()
            if item.sequential_status_path is not None
            else False,
            "canonical_present": (
                item.live_status_path.is_file()
                if item.live_status_path is not None
                else item.canon_path.is_file()
                if item.canon_path is not None
                else False
            ),
        }
        for item in visible_items
    ]

    return {
        "version": "temp-queue-state-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "queue_mode": queue_mode,
        "active_item_count": active_count,
        "roadmap": None,
        "items": payload_items,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preprocess-root",
        type=Path,
        default=PREPROCESS_ROOT,
        help="Root directory containing per-work preprocess folders.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output path for the material queue snapshot JSON.",
    )
    parser.add_argument(
        "--include-completed",
        action="store_true",
        help="Include completed/historical-backing works in the output. Default behavior already includes them.",
    )
    parser.add_argument(
        "--active-only",
        action="store_true",
        help="Exclude completed works and emit only canon-stage and in-flight production work.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_material_queue_payload(
        args.preprocess_root.resolve(),
        include_completed=not args.active_only,
    )
    output_path = args.output.resolve()
    _write_json(output_path, payload)
    print(f"wrote: {output_path}")
    print(f"- items: {len(payload['items'])}")
    print(f"- active_item_count: {payload['active_item_count']}")
    print(f"- queue_mode: {payload['queue_mode']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
