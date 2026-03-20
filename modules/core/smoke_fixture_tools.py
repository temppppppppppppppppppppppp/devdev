"""Helpers for preparing the bounded smoke fixture project."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from modules.core.db_manager import DBManager


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
