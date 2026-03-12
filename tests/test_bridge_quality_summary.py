import asyncio
import json

from modules.api import bridge_server
from modules.core.db_manager import DBManager
from modules.core.quality_dashboard import QualityDashboard


def test_quality_summary_endpoint_reads_project_sidecar(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    db = DBManager(project_dir / "project_data.db")
    db.save_episode_quality_signal(
        3,
        {
            "ced_score": 1.1,
            "ai_slop_score": 0.8,
            "ai_slop_hits": [{"pattern": "그야말로", "count": 1}],
            "compression_ratio": 0.31,
            "burstiness": 9.4,
            "complexity": 28.8,
            "signal_summary": {"sentence_count": 37},
        },
    )
    db.close()

    response = asyncio.run(bridge_server.quality_summary_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["data"]["available"] is True
    assert payload["data"]["latest_ep"] == 3
    assert payload["data"]["signals"]["ced"]["value"] == 1.1


def test_quality_summary_endpoint_prefers_workspace_projects_root(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    monkeypatch.setenv("GEULDOBI_WORKSPACE", str(workspace_root))
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path / "engine")
    project_dir = workspace_root / "projects" / "demo"
    project_dir.mkdir(parents=True)

    db = DBManager(project_dir / "project_data.db")
    db.save_episode_quality_signal(2, {"ced_score": 0.9, "ai_slop_score": 0.4})
    db.close()

    response = asyncio.run(bridge_server.quality_summary_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["data"]["available"] is True
    assert payload["data"]["latest_ep"] == 2


def test_quality_summary_endpoint_rejects_missing_project():
    response = asyncio.run(bridge_server.quality_summary_endpoint(project="", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 400
    assert payload["code"] == "INVALID_PROJECT"


def test_quality_dashboard_endpoint_combines_result_and_patterns(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)
    logs_dir = project_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "config").mkdir(parents=True, exist_ok=True)
    (project_dir / "stage0_output").mkdir(parents=True, exist_ok=True)
    (project_dir / "plans" / "arcs").mkdir(parents=True, exist_ok=True)
    (project_dir / "plans" / "blueprints").mkdir(parents=True, exist_ok=True)
    (project_dir / "drafts").mkdir(parents=True, exist_ok=True)
    (project_dir / "config" / "author_directives.txt").write_text("writer intent", encoding="utf-8")
    (project_dir / "config" / "work_guard.yaml").write_text("work_identity:\n  work_type: enterprise\n", encoding="utf-8")
    (project_dir / "stage0_output" / "style_guide.json").write_text('{"tone":"sharp"}', encoding="utf-8")
    (project_dir / "treatment_generated.json").write_text(
        json.dumps([{"block": 1}, {"block": 2}], ensure_ascii=False),
        encoding="utf-8",
    )
    (project_dir / "plans" / "arcs" / "arc_001.txt").write_text("arc 1", encoding="utf-8")
    (project_dir / "plans" / "blueprints" / "blueprint_0003.txt").write_text("blueprint 3", encoding="utf-8")
    (project_dir / "drafts" / "ep_0003.txt").write_text("episode 3", encoding="utf-8")

    db = DBManager(project_dir / "project_data.db")
    db.save_anchor(
        "bible",
        {
            "MasterBible": {
                "ProjectData": {"MetaInfo": {"title": "Demo Bible"}},
                "plot_roadmap": [{"block": 1}, {"block": 2}],
            }
        },
    )
    db.save_anchor("arcs", [{"arc_no": 1}, {"arc_no": 2}])
    db.save_episode_quality_signal(
        3,
        {
            "ced_score": 1.1,
            "ai_slop_score": 0.8,
            "ai_slop_hits": [{"pattern": "그야말로", "count": 2}],
            "compression_ratio": 0.31,
            "burstiness": 9.4,
            "complexity": 28.8,
            "signal_summary": {"sentence_count": 37},
        },
    )
    db.save_episode_quality_label(
        3,
        {
            "score": 91,
            "verdict": "PASS_WITH_FIX",
            "selection_reason": "후반부 장면은 좋지만 호흡 보강이 필요함",
            "open_review": "톤은 안정적이나 장면 말미 설명이 반복됨.",
            "score_breakdown": {"quality_engagement": 88},
            "consistency_checklist": {"scene_variety": "ISSUE", "pacing_quality": "OK"},
        },
    )
    db.save_episode_quality_observation(3, {"operator_label": "AI 티", "note": "장면 말미 요약이 반복됨"})
    db.save_episode_quality_observation(2, {"operator_label": "경계", "note": "CED 상승 구간"})
    db.save_director_selection(
        ep_num=0,
        round_num=1,
        selected_label="",
        selected_strategy="stage2",
        verdict="PASS",
        score=0,
        selection_reason="stage2 selected",
        candidate_count=3,
        stage=2,
    )
    db.save_director_selection(
        ep_num=3,
        round_num=1,
        selected_label="A",
        selected_strategy="stage4",
        verdict="PASS_WITH_FIX",
        score=91,
        selection_reason="stage4 selected",
        candidate_count=3,
        stage=4,
    )
    db.close()

    dashboard = QualityDashboard(project_dir)
    dashboard.record_validation(ep_num=1, result={"decision": "PASS", "score": 88, "violations": []}, stage=4)
    dashboard.record_validation(
        ep_num=2,
        result={"decision": "REJECT", "score": 72, "violations": ["scene_variety", "pacing_quality"]},
        stage=4,
    )
    dashboard.record_validation(
        ep_num=3,
        result={"decision": "PASS_WITH_FIX", "score": 91, "violations": ["scene_variety"]},
        stage=4,
    )
    dashboard.record_retrieval_observation(
        ep_num=3,
        stage="director",
        observation={
            "work_focus_present": True,
            "work_slot_summary_included": True,
            "relation_slice_included": True,
            "source_counts": {"db_npc_relationship": 1},
            "coverage_warnings": [],
        },
    )
    (logs_dir / "soft_failures.jsonl").write_text(
        json.dumps(
            {
                "ts": "2026-03-10T00:00:00+00:00",
                "component": "stage4_post_processor",
                "operation": "save_episode_quality_signal",
                "message": "signal save failed",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    db = DBManager(project_dir / "project_data.db")
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
    assert after_counts == before_counts
    data = payload["data"]
    assert data["available"] is True
    assert data["quality_summary"]["latest_ep"] == 3
    assert data["result_summary"]["available"] is True
    assert data["result_summary"]["verdict"] == "PASS_WITH_FIX"
    assert len(data["result_summary"]["fix_now"]) >= 1
    assert data["result_summary"]["keep_next"]
    assert data["result_summary"]["avoid_next"]
    assert any("씬 다양성" in issue for issue in data["result_summary"]["issues"])
    assert data["compare_rows"][0]["ep_num"] == 3
    assert data["stage_stats"][0]["stage"] == 4
    assert data["failure_patterns"]["top_types"][0]["type"] == "scene_variety"
    assert data["runtime_health"]["available"] is True
    assert data["runtime_health"]["top_components"][0]["component"] == "stage4_post_processor.save_episode_quality_signal"
    assert data["retrieval_summary"]["available"] is True
    assert data["retrieval_summary"]["stage_rows"][0]["stage"] == "director"
    assert data["artifact_ladder"]["available"] is True
    assert data["artifact_ladder"]["items"][0]["short"] == "BI"
    assert data["artifact_ladder"]["items"][-1]["short"] == "MS"
    assert data["artifact_ladder"]["support"][0]["status"] == "ready"
    assert data["safe_ops"]["available"] is True
    assert data["safe_ops"]["arc_count"] == 2
    assert data["safe_ops"]["stage2_selection_count"] == 1
    assert data["safe_ops"]["stage4_selection_count"] == 1
    assert data["safe_ops"]["actions"]["wipe"]["requires_target"] is False
    assert data["safe_ops"]["actions"]["rollback"]["requires_target"] is True
    assert data["calibration"]["available"] is True
    assert data["calibration"]["total_reviews"] == 2
    assert data["calibration"]["recent_observations"][0]["ep_num"] == 3
    assert data["calibration"]["recent_observations"][0]["operator_label"] == "AI 티"


def test_safe_ops_preview_endpoint_exposes_stage_split(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    db = DBManager(project_dir / "project_data.db")
    db.save_anchor("arcs", [{"arc_no": 1}, {"arc_no": 2}, {"arc_no": 3}])
    db.save_episode_quality_signal(2, {"ced_score": 1.0, "ai_slop_score": 0.5})
    db.save_director_selection(
        ep_num=0,
        round_num=1,
        selected_label="",
        selected_strategy="stage2",
        verdict="PASS",
        selection_reason="stage2 history",
        stage=2,
    )
    db.save_director_selection(
        ep_num=2,
        round_num=1,
        selected_label="A",
        selected_strategy="stage4",
        verdict="PASS",
        selection_reason="stage4 history",
        stage=4,
    )
    db.close()

    response = asyncio.run(bridge_server.safe_ops_preview_endpoint(project="demo"))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    data = payload["data"]
    assert data["available"] is True
    assert data["arc_count"] == 3
    assert data["stage2_selection_count"] == 1
    assert data["stage4_selection_count"] == 1
    assert "Stage 2 selection history는 보존됩니다." in data["actions"]["rollback"]["notes"]
    assert data["actions"]["reset"]["impact_counts"][0]["label"] == "Arc 설계"


def test_quality_review_endpoint_saves_observation(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    class _Request:
        async def json(self):
            return {
                "project": "demo",
                "ep_num": 11,
                "operator_label": "과잉 설명",
                "note": "설명문이 과해 리듬이 무거움",
            }

    response = asyncio.run(bridge_server.quality_review_endpoint(_Request()))
    payload = json.loads(response.body.decode("utf-8"))

    db = DBManager(project_dir / "project_data.db")
    saved = db.get_episode_quality_observation(11)
    db.close()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert saved is not None
    assert saved["operator_label"] == "과잉 설명"
    assert saved["note"] == "설명문이 과해 리듬이 무거움"


def test_quality_review_endpoint_rejects_invalid_label():
    class _Request:
        async def json(self):
            return {
                "project": "demo",
                "ep_num": 11,
                "operator_label": "이상함",
                "note": "",
            }

    response = asyncio.run(bridge_server.quality_review_endpoint(_Request()))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 400
    assert payload["code"] == "INVALID_REQUEST"
