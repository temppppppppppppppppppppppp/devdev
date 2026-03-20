"""Helpers for preparing and validating the bounded smoke fixture project."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from modules.core.db_manager import DBManager


SMOKE_FIXTURE_MIN_ARC_COUNT = 3
SMOKE_FIXTURE_MIN_BLUEPRINT_COUNT = 3
SMOKE_FIXTURE_MAX_BASELINE_MANUSCRIPTS = 0


def prepare_smoke_fixture_project(
    source_root: str | Path,
    target_root: str | Path,
    *,
    force: bool = False,
) -> dict:
    """Copy the canonical smoke fixture source into the bounded smoke target."""
    source = Path(source_root)
    target = Path(target_root)
    if not source.exists():
        raise FileNotFoundError(f"source project not found: {source}")
    if source.resolve() == target.resolve():
        raise ValueError("source and target project must be different for smoke fixture prep")
    if target.exists():
        if not force:
            raise FileExistsError(f"target project already exists: {target}")
        shutil.rmtree(target)

    shutil.copytree(source, target)
    contract = _collect_fixture_contract(target)
    payload = {
        "prepared_at": datetime.now().isoformat(timespec="seconds"),
        "source_project": source.name,
        "target_project": target.name,
        "fixture_contract": contract,
    }
    _write_json(target / "logs" / "smoke_fixture_prep.json", payload)
    return payload


def read_smoke_fixture_prep(project_root: str | Path) -> dict | None:
    prep_path = Path(project_root) / "logs" / "smoke_fixture_prep.json"
    if not prep_path.exists():
        return None
    try:
        return json.loads(prep_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def collect_smoke_fixture_contract(project_root: str | Path) -> dict:
    project_root = Path(project_root)
    contract = _collect_fixture_contract(project_root)
    contract["prep_marker_present"] = bool(read_smoke_fixture_prep(project_root))
    return contract


def assert_smoke_fixture_ready(project_root: str | Path, *, lane: str) -> dict:
    contract = collect_smoke_fixture_contract(project_root)
    prep_payload = read_smoke_fixture_prep(project_root)
    if not prep_payload:
        raise RuntimeError(
            "bounded smoke fixture target is missing logs/smoke_fixture_prep.json; "
            "run `python scripts/prepare_smoke_fixture.py --force` first"
        )

    if contract["arc_count"] < SMOKE_FIXTURE_MIN_ARC_COUNT:
        raise RuntimeError(
            f"bounded smoke fixture target is too shallow for {lane}: "
            f"arcs={contract['arc_count']} < {SMOKE_FIXTURE_MIN_ARC_COUNT}; "
            "run `python scripts/prepare_smoke_fixture.py --force` first"
        )

    if contract["latest_blueprint_number"] < SMOKE_FIXTURE_MIN_BLUEPRINT_COUNT:
        raise RuntimeError(
            f"bounded smoke fixture target is too shallow for {lane}: "
            f"blueprints={contract['latest_blueprint_number']} < {SMOKE_FIXTURE_MIN_BLUEPRINT_COUNT}; "
            "run `python scripts/prepare_smoke_fixture.py --force` first"
        )

    if contract["manuscript_count"] > SMOKE_FIXTURE_MAX_BASELINE_MANUSCRIPTS:
        raise RuntimeError(
            f"bounded smoke fixture target is dirty for {lane}: "
            f"manuscripts={contract['manuscript_count']} > {SMOKE_FIXTURE_MAX_BASELINE_MANUSCRIPTS}; "
            "run `python scripts/prepare_smoke_fixture.py --force` first"
        )

    contract["source_project"] = str(prep_payload.get("source_project", "") or "")
    contract["target_project"] = str(prep_payload.get("target_project", "") or "")
    return contract


def reset_stage2_smoke_state(project_root: str | Path) -> dict:
    """Reset bounded Stage2 smoke state inside the disposable target."""
    project_root = Path(project_root)
    db_path = project_root / "project_data.db"
    if not db_path.exists():
        raise FileNotFoundError(f"project database not found: {db_path}")

    db = DBManager(db_path)
    try:
        db.save_anchor("arcs", [])
    finally:
        db.close()

    removed_json = 0
    for path in (project_root / "plans" / "arcs").glob("arc_*.json"):
        path.unlink(missing_ok=True)
        removed_json += 1

    removed_reports = 0
    for path in (project_root / "logs").glob("arc_*_failure_report.txt"):
        path.unlink(missing_ok=True)
        removed_reports += 1

    stage2_artifacts = project_root / "logs" / "artifacts" / "stage2"
    removed_stage2_artifacts = stage2_artifacts.exists()
    if removed_stage2_artifacts:
        shutil.rmtree(stage2_artifacts)

    return {
        "cleared_arcs_anchor": True,
        "removed_arc_json_count": removed_json,
        "removed_failure_report_count": removed_reports,
        "removed_stage2_artifacts": removed_stage2_artifacts,
    }


def _collect_fixture_contract(project_root: Path) -> dict:
    db_path = project_root / "project_data.db"
    if not db_path.exists():
        raise FileNotFoundError(f"project database not found: {db_path}")
    db = DBManager(db_path)
    try:
        raw_arcs = db.load_anchor("arcs") or []
        if isinstance(raw_arcs, list):
            arc_count = len([arc for arc in raw_arcs if isinstance(arc, dict)])
        elif isinstance(raw_arcs, dict):
            arc_count = len([arc for arc in raw_arcs.values() if isinstance(arc, dict)])
        else:
            arc_count = 0

        latest_blueprint = int(db.get_latest_blueprint_number() or 0)
        manuscript_count = int(
            db.conn.execute("SELECT COUNT(*) AS c FROM manuscripts").fetchone()["c"]
        )
    finally:
        db.close()

    return {
        "arc_count": arc_count,
        "latest_blueprint_number": latest_blueprint,
        "manuscript_count": manuscript_count,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
