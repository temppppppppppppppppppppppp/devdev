from pathlib import Path

from modules.api import bridge_server


def test_lane_c_load_artifact_ladder_db_snapshot_reads_counts_and_closes(tmp_path, monkeypatch):
    db_path = tmp_path / "project_data.db"
    db_path.write_text("", encoding="utf-8")

    calls = {"closed": False}

    class FakeDB:
        def __init__(self, _db_path):
            pass

        def load_anchor(self, key):
            if key == "bible":
                return {
                    "MasterBible": {
                        "ProjectData": {"MetaInfo": {"title": "Demo Title"}},
                        "plot_roadmap": [1, 2, 3],
                    }
                }
            if key == "arcs":
                return [{"arc_no": 1}, {"arc_no": 2}]
            return {}

        def get_latest_blueprint_number(self):
            return 4

        def get_latest_episode_number(self):
            return 6

        def close(self):
            calls["closed"] = True

    monkeypatch.setattr(bridge_server, "DBManager", FakeDB)

    snapshot = bridge_server._load_artifact_ladder_db_snapshot("demo", db_path)

    assert snapshot == {
        "bible_title": "Demo Title",
        "roadmap_count": 3,
        "blueprint_count": 4,
        "manuscript_count": 5,
        "arc_count_from_anchor": 2,
    }
    assert calls["closed"] is True


def test_lane_c_build_artifact_ladder_items_marks_derived_treatment_without_file(tmp_path):
    project_dir = tmp_path / "demo"
    project_dir.mkdir()
    db_path = project_dir / "project_data.db"
    db_path.write_text("", encoding="utf-8")
    file_context = {
        "latest_treatment": None,
        "treatment_blocks": 0,
        "arc_files": [],
        "latest_arc": None,
        "blueprint_files": [],
        "latest_blueprint": None,
        "manuscript_files": [],
        "latest_manuscript": None,
        "support_assets": {},
    }
    db_snapshot = {
        "bible_title": "Demo",
        "roadmap_count": 2,
        "blueprint_count": 0,
        "manuscript_count": 0,
        "arc_count_from_anchor": 0,
    }

    items = bridge_server._build_artifact_ladder_items(project_dir, db_path, file_context, db_snapshot)

    assert items[0]["key"] == "bible"
    assert items[0]["status"] == "ready"
    assert items[1]["key"] == "treatment"
    assert items[1]["status"] == "derived"
    assert items[1]["path"] == "project_data.db :: anchors[bible].plot_roadmap"
    assert items[-1]["key"] == "manuscript"
    assert items[-1]["status"] == "pending"


def test_lane_c_build_artifact_ladder_payload_shell_builds_ready_ladder(tmp_path, monkeypatch):
    project_dir = tmp_path / "projects" / "demo"
    (project_dir / "plans" / "arcs").mkdir(parents=True)
    (project_dir / "plans" / "blueprints").mkdir(parents=True)
    (project_dir / "drafts").mkdir(parents=True)
    (project_dir / "treatment.json").write_text("[{}, {}]", encoding="utf-8")
    (project_dir / "plans" / "arcs" / "arc_0001.txt").write_text("arc", encoding="utf-8")
    (project_dir / "plans" / "blueprints" / "blueprint_0001.txt").write_text("bp", encoding="utf-8")
    (project_dir / "drafts" / "ep_0001.txt").write_text("ms", encoding="utf-8")
    db_path = project_dir / "project_data.db"
    db_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        bridge_server,
        "inspect_project_support_assets",
        lambda _project_dir: {
            "author_directives": {"ready": True, "path": str(project_dir / "author_directives.txt"), "size_bytes": 42},
            "work_guard": {
                "ready": True,
                "path": str(project_dir / "work_guard.yaml"),
                "tracking_slots": 3,
                "registry_profiles": 2,
                "role_fit_constraints": 1,
            },
            "style_guide": {"ready": True, "path": str(project_dir / "style_guide.json"), "tone": "grim", "pov": "3p"},
        },
    )
    monkeypatch.setattr(
        bridge_server,
        "_load_artifact_ladder_db_snapshot",
        lambda _project, _db_path: {
            "bible_title": "Demo Bible",
            "roadmap_count": 2,
            "blueprint_count": 0,
            "manuscript_count": 0,
            "arc_count_from_anchor": 0,
        },
    )

    payload = bridge_server._build_artifact_ladder_payload("demo", project_dir, db_path)

    assert payload["available"] is True
    assert [item["short"] for item in payload["items"]] == ["BI", "TR", "ARC", "BP", "MS"]
    assert payload["items"][0]["title"] == "Demo Bible"
    assert payload["items"][1]["meta"] == "2 blocks"
    assert payload["items"][-1]["status"] == "ready"
    assert payload["support"][0]["status"] == "ready"
    assert payload["hint"] == "현재 프로젝트는 기본 산출물이 준비되어 있습니다."
