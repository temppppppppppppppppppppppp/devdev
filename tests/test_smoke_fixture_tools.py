import json
from pathlib import Path

import pytest

from modules.core.db_manager import DBManager
from modules.core.smoke_fixture_tools import (
    assert_smoke_fixture_ready,
    prepare_smoke_fixture_project,
    reset_stage2_smoke_state,
)


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


def test_assert_smoke_fixture_ready_requires_prep_marker_and_contract(tmp_path):
    project = tmp_path / "fixture_project"
    _make_project_root(project)

    db = DBManager(project / "project_data.db")
    try:
        db.save_anchor("arcs", [{"arc_no": 1}, {"arc_no": 2}, {"arc_no": 3}])
        db.save_blueprint(1, {"ep_num": 1})
        db.save_blueprint(2, {"ep_num": 2})
        db.save_blueprint(3, {"ep_num": 3})
    finally:
        db.close()

    with pytest.raises(RuntimeError, match="smoke_fixture_prep.json"):
        assert_smoke_fixture_ready(project, lane="stage3_smoke")

    prep_payload = {
        "source_project": "smoke_fixture_demo",
        "target_project": "코덱스_테스트",
        "fixture_contract": {
            "arc_count": 3,
            "latest_blueprint_number": 3,
            "manuscript_count": 0,
        },
    }
    prep_file = project / "logs" / "smoke_fixture_prep.json"
    prep_file.parent.mkdir(parents=True, exist_ok=True)
    prep_file.write_text(json.dumps(prep_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = assert_smoke_fixture_ready(project, lane="stage3_smoke")
    assert result["arc_count"] == 3
    assert result["latest_blueprint_number"] == 3
    assert result["manuscript_count"] == 0
    assert result["source_project"] == "smoke_fixture_demo"


def test_reset_stage2_smoke_state_clears_arcs_and_stage2_outputs(tmp_path):
    project = tmp_path / "fixture_project"
    _make_project_root(project)

    db = DBManager(project / "project_data.db")
    try:
        db.save_anchor("arcs", [{"arc_no": 1}, {"arc_no": 2}, {"arc_no": 3}])
    finally:
        db.close()

    (project / "plans" / "arcs" / "arc_1.json").write_text("{}", encoding="utf-8")
    (project / "logs" / "arc_4_failure_report.txt").write_text("fail", encoding="utf-8")
    (project / "logs" / "artifacts" / "stage2" / "arc_004").mkdir(parents=True, exist_ok=True)

    result = reset_stage2_smoke_state(project)

    assert result["cleared_arcs_anchor"] is True
    assert result["removed_arc_json_count"] == 1
    assert result["removed_failure_report_count"] == 1
    assert result["removed_stage2_artifacts"] is True

    reloaded = DBManager(project / "project_data.db")
    try:
        assert reloaded.load_anchor("arcs") == []
    finally:
        reloaded.close()

    assert not (project / "plans" / "arcs" / "arc_1.json").exists()
    assert not (project / "logs" / "arc_4_failure_report.txt").exists()
    assert not (project / "logs" / "artifacts" / "stage2").exists()
