import json
from pathlib import Path

import pytest

from modules.core.db_manager import DBManager
from modules.core.smoke_fixture_tools import prepare_smoke_fixture_project


def _make_project_root(root: Path) -> None:
    for rel in ("drafts", "logs", "memory", "plans/arcs", "plans/blueprints", "config", "stage0_output"):
        (root / rel).mkdir(parents=True, exist_ok=True)


def test_prepare_smoke_fixture_project_copies_fixture_and_writes_contract(tmp_path):
    source = tmp_path / "source_project"
    target = tmp_path / "target_project"
    _make_project_root(source)

    db = DBManager(source / "project_data.db")
    try:
        db.save_anchor("arcs", [{"arc_no": 1}, {"arc_no": 2}, {"arc_no": 3}])
        db.save_blueprint(1, {"ep_num": 1})
        db.save_blueprint(2, {"ep_num": 2})
        db.save_blueprint(3, {"ep_num": 3})
    finally:
        db.close()

    payload = prepare_smoke_fixture_project(source, target)

    assert payload["source_project"] == "source_project"
    assert payload["target_project"] == "target_project"
    assert payload["fixture_contract"]["arc_count"] == 3
    assert payload["fixture_contract"]["latest_blueprint_number"] == 3
    assert payload["fixture_contract"]["manuscript_count"] == 0

    prep_file = target / "logs" / "smoke_fixture_prep.json"
    assert prep_file.exists()
    saved = json.loads(prep_file.read_text(encoding="utf-8"))
    assert saved["fixture_contract"]["arc_count"] == 3

    target_db = DBManager(target / "project_data.db")
    try:
        assert target_db.get_latest_blueprint_number() == 3
        assert target_db.get_manuscript(1) is None
    finally:
        target_db.close()


def test_prepare_smoke_fixture_project_requires_force_for_existing_target(tmp_path):
    source = tmp_path / "source_project"
    target = tmp_path / "target_project"
    _make_project_root(source)
    _make_project_root(target)
    DBManager(source / "project_data.db").close()

    with pytest.raises(FileExistsError):
        prepare_smoke_fixture_project(source, target)
