import asyncio
import json

from modules.api import bridge_server
from modules.core.db_manager import DBManager
from modules.core.quality_sidecar_bootstrap import bootstrap_quality_sidecars, inspect_quality_sidecar_health


def _write_metrics(project_dir, rows):
    logs_dir = project_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "quality_metrics.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_bootstrap_quality_sidecars_backfills_legacy_stage4_rows(tmp_path):
    project_dir = tmp_path / "demo"
    project_dir.mkdir(parents=True)
    (project_dir / "config").mkdir(parents=True, exist_ok=True)
    (project_dir / "config" / "work_guard.yaml").write_text(
        "\n".join(
            [
                "work_identity:",
                "  tracking_slots:",
                "    - core cast",
                "  registry_profiles:",
                "    - talent_registry",
                "  role_fit_constraints:",
                "    - role: ceo",
                "      must_behave_like: cold negotiator",
            ]
        ),
        encoding="utf-8",
    )
    _write_metrics(
        project_dir,
        [
            {
                "type": "validation",
                "timestamp": "2026-03-11T00:00:00",
                "ep_num": 3,
                "stage": 4,
                "decision": "PASS",
                "score": 0,
                "violations": [],
                "warnings": 2,
            }
        ],
    )

    db = DBManager(project_dir / "project_data.db")
    db.save_manuscript(
        3,
        "ep3",
        "{'corrected_manuscript': 'The protagonist ended the negotiation coldly. The room stayed tense.'}",
    )
    db.save_director_selection(
        ep_num=3,
        round_num=1,
        selected_label="A",
        selected_strategy="stage4",
        verdict="PASS_WITH_FIX",
        score=91,
        selection_reason="Candidate A is selected but the final dialogue still needs a small polish.",
        candidate_count=3,
    )

    report = bootstrap_quality_sidecars(project_dir, db)
    health = inspect_quality_sidecar_health(project_dir, db)
    label = db.get_episode_quality_label(3)
    signal = db.get_episode_quality_signal(3)
    db.close()

    assert report["backfilled_labels"] == 1
    assert report["backfilled_signals"] == 1
    assert report["missing_manuscript_eps"] == []
    assert label is not None
    assert label["verdict"] == "PASS_WITH_FIX"
    assert label["score"] == 91
    assert "dialogue" in label["selection_reason"]
    assert signal is not None
    assert signal["ced_score"] > 0
    assert health["quality_label_rows"] == 1
    assert health["quality_signal_rows"] == 1
    assert health["stage4_validation_eps"] == 1
    assert health["role_fit_constraints"] == 1


def test_quality_dashboard_endpoint_is_read_only_for_legacy_quality_sidecars(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)
    (project_dir / "config").mkdir(parents=True, exist_ok=True)
    (project_dir / "plans" / "arcs").mkdir(parents=True, exist_ok=True)
    (project_dir / "plans" / "blueprints").mkdir(parents=True, exist_ok=True)
    (project_dir / "drafts").mkdir(parents=True, exist_ok=True)
    (project_dir / "stage0_output").mkdir(parents=True, exist_ok=True)
    (project_dir / "config" / "author_directives.txt").write_text("writer intent", encoding="utf-8")
    (project_dir / "config" / "work_guard.yaml").write_text(
        "\n".join(
            [
                "work_identity:",
                "  tracking_slots:",
                "    - core business axis",
                "  role_fit_constraints:",
                "    - role: ceo",
                "      must_behave_like: cold negotiator",
            ]
        ),
        encoding="utf-8",
    )
    (project_dir / "stage0_output" / "style_guide.json").write_text('{"tone":"sharp"}', encoding="utf-8")
    (project_dir / "drafts" / "ep_0003.txt").write_text(
        "{'corrected_manuscript': 'He controlled the meeting with silence and pressure. The numbers did not lie.'}",
        encoding="utf-8",
    )
    _write_metrics(
        project_dir,
        [
            {
                "type": "validation",
                "timestamp": "2026-03-11T00:00:00",
                "ep_num": 3,
                "stage": 4,
                "decision": "PASS",
                "score": 0,
                "violations": [],
                "warnings": 1,
            }
        ],
    )

    db = DBManager(project_dir / "project_data.db")
    db.save_anchor(
        "bible",
        {"MasterBible": {"ProjectData": {"MetaInfo": {"title": "Demo Bible"}}, "plot_roadmap": [{"block": 1}]}},
    )
    db.save_anchor("arcs", [{"arc_no": 1}])
    db.save_director_selection(
        ep_num=3,
        round_num=1,
        selected_label="A",
        selected_strategy="stage4",
        verdict="PASS",
        score=93,
        selection_reason="Stable hook and tension make this the selected version.",
        candidate_count=3,
    )
    before_counts = {
        "labels": db.cursor.execute("SELECT COUNT(*) FROM episode_quality_labels").fetchone()[0],
        "signals": db.cursor.execute("SELECT COUNT(*) FROM episode_quality_signals").fetchone()[0],
        "observations": db.cursor.execute("SELECT COUNT(*) FROM episode_quality_observations").fetchone()[0],
    }
    db.close()

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))
    db = DBManager(project_dir / "project_data.db")
    after_counts = {
        "labels": db.cursor.execute("SELECT COUNT(*) FROM episode_quality_labels").fetchone()[0],
        "signals": db.cursor.execute("SELECT COUNT(*) FROM episode_quality_signals").fetchone()[0],
        "observations": db.cursor.execute("SELECT COUNT(*) FROM episode_quality_observations").fetchone()[0],
    }
    db.close()

    assert response.status_code == 200
    assert payload["ok"] is True
    data = payload["data"]
    assert data["quality_summary"]["available"] is False
    assert data["result_summary"]["available"] is False
    assert data["calibration"]["data_health"]["stage4_validation_eps"] == 1
    assert data["calibration"]["data_health"]["quality_label_rows"] == 0
    assert data["calibration"]["data_health"]["quality_signal_rows"] == 0
    assert data["calibration"]["data_health"]["manual_review_rows"] == 0
    assert "review" in data["calibration"]["next_step"]
    assert before_counts == after_counts
