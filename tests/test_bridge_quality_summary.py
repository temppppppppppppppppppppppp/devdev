import asyncio
import json
from unittest.mock import patch

from modules.api import bridge_server
from modules.core.db_manager import DBManager
from modules.core.pass_rate_monitor import PassRateMonitor
from modules.core.quality_dashboard import QualityDashboard
from modules.core.services.audit_service import AuditService


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
    assert payload["data"]["authority_role"] == "companion_snapshot"
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
    assert payload["data"]["authority_role"] == "companion_snapshot"
    assert payload["data"]["available"] is True
    assert payload["data"]["latest_ep"] == 2


def test_quality_summary_endpoint_rejects_missing_project():
    response = asyncio.run(bridge_server.quality_summary_endpoint(project="", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 400
    assert payload["code"] == "INVALID_PROJECT"


def test_quality_dashboard_endpoint_surfaces_authority_maps(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    data = payload["data"]
    assert data["runtime_authority_summary"]["supported_entry"] == "geuldobi-desktop/src/main.js"
    assert (
        data["runtime_authority_summary"]["boot_log_surfaces"]["desktop_pre_bridge"]["path"]
        == "%LOCALAPPDATA%/Geuldobi/electron-main.log"
    )
    assert (
        data["control_plane_authority_summary"]["companion_snapshots"]["/quality/summary"]
        == "read-only subset, not durable authority"
    )


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
    (project_dir / "config" / "work_guard.yaml").write_text(
        "work_identity:\n  work_type: enterprise\n", encoding="utf-8"
    )
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
    assert (
        data["runtime_health"]["top_components"][0]["component"] == "stage4_post_processor.save_episode_quality_signal"
    )
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


def test_quality_dashboard_endpoint_surfaces_proof_status_and_sink_alignment(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)
    logs_dir = project_dir / "logs"
    (logs_dir / "session").mkdir(parents=True, exist_ok=True)

    db = DBManager(project_dir / "project_data.db")
    attempt_key_s3 = "s3:ep6:arc1:a1:sess_demo"
    attempt_key_s4 = "s4:ep6:arc1:a1:sess_demo"
    stage3_artifact = "logs/artifacts/stage3/ep_0006/attempt_01/final_blueprint__balanced.json"
    stage4_artifact = "logs/artifacts/stage4/ep_0006/attempt_01/final_manuscript__A_balanced.txt"
    try:
        (project_dir / stage3_artifact).parent.mkdir(parents=True, exist_ok=True)
        (project_dir / stage3_artifact).write_text("{}", encoding="utf-8")
        (project_dir / stage4_artifact).parent.mkdir(parents=True, exist_ok=True)
        (project_dir / stage4_artifact).write_text("manuscript", encoding="utf-8")

        db.save_stage_attempt(
            stage=3,
            verdict="PASS",
            attempt_num=1,
            ep_num=6,
            arc_num=1,
            score=90,
            session_id="sess_demo",
            attempt_key=attempt_key_s3,
            candidate_key="balanced",
            content_hash="hash-s3",
            artifact_path=stage3_artifact,
        )
        db.save_director_selection(
            ep_num=6,
            round_num=1,
            selected_label="B",
            selected_strategy="balanced",
            verdict="PASS",
            score=90,
            stage=3,
            attempt_key=attempt_key_s3,
            candidate_key="balanced",
            content_hash="hash-s3",
            artifact_path=stage3_artifact,
        )
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=6,
            arc_num=1,
            score=96,
            session_id="sess_demo",
            attempt_key=attempt_key_s4,
            candidate_key="A|balanced",
            content_hash="hash-s4",
            artifact_path=stage4_artifact,
        )
        db.save_director_selection(
            ep_num=6,
            round_num=1,
            selected_label="A",
            selected_strategy="balanced",
            verdict="PASS",
            score=96,
            stage=4,
            attempt_key=attempt_key_s4,
            candidate_key="A|balanced",
            content_hash="hash-s4",
            artifact_path=stage4_artifact,
        )
        for payload_kind in (
            "selection_contract_snapshot_raw",
            "selection_surface_raw",
            "feedback_provenance_raw",
            "contract_snapshot_raw",
        ):
            db.save_attempt_raw_rationale(
                attempt_key=attempt_key_s4,
                stage=4,
                ep_num=6,
                payload_kind=payload_kind,
                payload=json.dumps({"_meta": {"surface": payload_kind}}, ensure_ascii=False),
            )
        (logs_dir / "session" / "decisions.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "stage": "stage3",
                            "ep_num": 6,
                            "decision_type": "blueprint",
                            "result": "PASS",
                            "score": 90,
                            "meta": {
                                "attempt_key": attempt_key_s3,
                                "candidate_key": "balanced",
                                "content_hash": "hash-s3",
                                "artifact_path": stage3_artifact,
                            },
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "stage": "stage4",
                            "ep_num": 6,
                            "decision_type": "manuscript",
                            "result": "PASS",
                            "score": 96,
                            "meta": {
                                "attempt_key": attempt_key_s4,
                                "candidate_key": "A|balanced",
                                "content_hash": "hash-s4",
                                "artifact_path": stage4_artifact,
                                "selection_candidate_key": "A|balanced",
                                "selection_content_hash": "hash-s4",
                                "selection_artifact_path": stage4_artifact,
                            },
                        },
                        ensure_ascii=False,
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (logs_dir / "pass_rate_monitor.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "stage": 3,
                            "episode": 6,
                            "arc": 1,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": attempt_key_s3,
                            "final_verdict": "PASS",
                            "candidate_key": "balanced",
                            "content_hash": "hash-s3",
                            "artifact_path": stage3_artifact,
                        },
                        {
                            "stage": 4,
                            "episode": 6,
                            "arc": 1,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": attempt_key_s4,
                            "final_verdict": "PASS",
                            "candidate_key": "A|balanced",
                            "content_hash": "hash-s4",
                            "artifact_path": stage4_artifact,
                            "patch_strategy": "",
                            "structural_attempted": False,
                        },
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (logs_dir / "episode_production.jsonl").write_text(
            json.dumps(
                {
                    "ep": 6,
                    "attempt_key": attempt_key_s4,
                    "verdict": "PASS",
                    "initial_verdict": "PASS",
                    "final_verdict": "PASS",
                    "final_score": 96,
                    "candidate_key": "A|balanced",
                    "selection_candidate_key": "A|balanced",
                    "content_hash": "hash-s4",
                    "artifact_path": stage4_artifact,
                    "patch_trace": {"patch_strategy": "", "structural_attempted": False},
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        audit_service = AuditService(
            runtime_audit=[],
            project_paths_fn=lambda: type("Paths", (), {"root": project_dir})(),
            ui_log_fn=lambda _msg: None,
        )
        audit_service.audit_event("heartbeat", "ok")
        audit_service.write_audit_summary("proof_snapshot")
    finally:
        db.close()

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    data = payload["data"]
    runtime_health = data["runtime_health"]
    if runtime_health["available"]:
        assert all(
            item["component"] != "failure_analyzer.sink_alignment_final_authority_contract"
            for item in runtime_health["top_components"]
        )
    else:
        assert runtime_health["recent_count"] == 0
    assert data["proof_status"]["available"] is True
    assert data["proof_status"]["status"] == "ok"
    assert data["proof_status"]["sink_alignment_status"] == "ok"
    assert data["proof_status"]["runtime_summary_status"] == "ok"
    assert data["sink_alignment_summary"]["available"] is True
    assert data["sink_alignment_summary"]["stages"]["stage3"]["coverage"]["session_decisions"] == 1
    assert data["sink_alignment_summary"]["stages"]["stage4"]["coverage"]["session_decisions"] == 1
    assert data["runtime_audit_summary"]["available"] is True
    assert data["runtime_audit_summary"]["summary_role"] == "runtime_heartbeat_with_proof_digest"
    assert data["runtime_audit_summary"]["contract"]["summary_scope"] == "runtime_heartbeat_plus_compact_proof_digest"
    assert data["runtime_audit_summary"]["contract"]["attempt_truth_authoritative"] is False
    assert "pass_rate_monitor" in data["runtime_audit_summary"]["contract"]["authoritative_attempt_sinks"]
    assert data["runtime_audit_summary"]["proof_digest"]["status"] == "ok"
    assert data["runtime_audit_summary"]["run_scope"]["status"] == "scoped"
    assert data["runtime_audit_summary"]["run_scope"]["latest_session_id"] == "sess_demo"
    assert data["runtime_audit_summary"]["freshness"]["status"] == "scoped"
    assert data["runtime_audit_summary"]["freshness"]["latest_session_id_present"] is True
    assert data["runtime_audit_summary"]["freshness"]["operator_guidance_only"] is True
    assert data["runtime_audit_summary"]["proof_digest"]["stages"]["stage4"]["coverage"]["session_decisions"] == 1


def test_quality_dashboard_endpoint_surfaces_gate_repair_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    db = DBManager(project_dir / "project_data.db")
    attempt_key = "s4:ep8:arc1:a1:sess_gate"
    artifact_path = "logs/artifacts/stage4/ep_0008/attempt_01/final_manuscript__A_balanced.txt"
    advisory_flags = {
        "gate_semantics": {
            "director_verdict": "PASS_WITH_FIX",
            "gate_basis": "bounded_local_repair",
            "repair_scope": "inplace",
        },
        "fix_pack": {
            "patch_targets": ["opening_location_name", "ending_location_name"],
            "must_fix": ["rename both location anchors"],
            "do_not_regress": ["scene mood", "timeline"],
            "success_condition": "Only the two approved location labels should change.",
            "target_kind": "entity_ref",
        },
        "repair_contract": {
            "subtype": "opening_spatial_continuity",
            "provenance": "runtime_synthesized",
            "fix_scope": "partial",
            "repair_scope": "inplace",
        },
        "partial_fix_eval": {
            "patch_round": 1,
            "is_patch_attempt": True,
            "patch_target_id": "pt:opening",
            "target_kind": "entity_ref",
            "must_fix_resolved": None,
            "do_not_regress_held": None,
            "success_condition_met": None,
            "fallback_reason": "",
        },
        "repair_trace": [
            {
                "target": "opening_location_name",
                "target_kind": "entity_ref",
                "patch_target_id": "pt:opening",
                "old_excerpt": "old venue",
                "new_excerpt": "new venue",
                "why_changed": "repair opening label",
            }
        ],
        "scope_authority": {
            "fix_scope": "partial",
            "repair_scope": "inplace",
            "authoritative_fix_scope": "inplace",
            "scope_origin": "runtime_lane",
            "widened": False,
        },
        "retry_budget_axes": {"round": 1, "repair": 1, "guidance": 0},
    }
    try:
        db.save_episode_quality_signal(
            8,
            {
                "ced_score": 1.0,
                "ai_slop_score": 0.3,
                "compression_ratio": 0.28,
                "burstiness": 8.6,
                "complexity": 31.0,
                "signal_summary": {"sentence_count": 42},
            },
        )
        db.save_episode_quality_label(
            8,
            {
                "score": 96,
                "verdict": "PASS",
                "selection_reason": "repair closed cleanly",
                "open_review": "local rename fixed without regressions",
                "score_breakdown": {"quality_engagement": 94},
                "consistency_checklist": {"scene_variety": "OK"},
            },
        )
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=8,
            arc_num=1,
            score=96,
            session_id="sess_gate",
            attempt_key=attempt_key,
            candidate_key="A|balanced",
            content_hash="hash-gate",
            artifact_path=artifact_path,
            advisory_flags=advisory_flags,
            selection_reason="repair closed cleanly",
            verdict_reason="two bounded anchors needed correction",
            open_review="local rename fixed without regressions",
        )
        db.save_director_selection(
            ep_num=8,
            round_num=1,
            selected_label="A",
            selected_strategy="balanced",
            verdict="PASS_WITH_FIX",
            score=92,
            selection_reason="local rename only",
            candidate_count=3,
            fix_scope="inplace",
            advisory_warnings=advisory_flags,
            stage=4,
            verdict_reason="two bounded anchors need correction",
            attempt_key=attempt_key,
            candidate_key="A|balanced",
            content_hash="hash-gate",
            artifact_path=artifact_path,
        )
    finally:
        db.close()

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    data = payload["data"]
    assert data["gate_repair_summary"]["available"] is True
    assert data["gate_repair_summary"]["director_verdict"] == "PASS_WITH_FIX"
    assert data["gate_repair_summary"]["gate_basis"] == "bounded_local_repair"
    assert data["gate_repair_summary"]["repair_scope"] == "inplace"
    assert data["gate_repair_summary"]["fix_scope"] == "partial"
    assert data["gate_repair_summary"]["authoritative_fix_scope"] == "inplace"
    assert data["gate_repair_summary"]["session_id"] == "sess_gate"
    assert data["gate_repair_summary"]["repair_contract_subtype"] == "opening_spatial_continuity"
    assert data["gate_repair_summary"]["repair_contract_provenance"] == "runtime_synthesized"
    assert data["gate_repair_summary"]["scope_authority_fix_scope"] == "partial"
    assert data["gate_repair_summary"]["scope_authority_authoritative_fix_scope"] == "inplace"
    assert data["gate_repair_summary"]["scope_authority_scope_origin"] == "runtime_lane"
    assert data["gate_repair_summary"]["scope_authority_widened"] is False
    assert data["gate_repair_summary"]["fix_pack"]["patch_targets"] == [
        "opening_location_name",
        "ending_location_name",
    ]
    assert data["gate_repair_summary"]["repair_contract"] == {
        "subtype": "opening_spatial_continuity",
        "provenance": "runtime_synthesized",
        "fix_scope": "partial",
        "repair_scope": "inplace",
    }
    assert data["gate_repair_summary"]["scope_authority"] == {
        "fix_scope": "partial",
        "repair_scope": "inplace",
        "authoritative_fix_scope": "inplace",
        "scope_origin": "runtime_lane",
        "widened": False,
    }
    assert data["gate_repair_summary"]["retry_budget_axes"] == {"round": 1, "repair": 1, "guidance": 0}
    assert data["gate_repair_summary"]["partial_fix_eval"]["patch_round"] == 1
    assert data["gate_repair_summary"]["partial_fix_eval"]["patch_target_id"] == "pt:opening"
    assert data["gate_repair_summary"]["repair_trace"][0]["target"] == "opening_location_name"
    assert data["gate_repair_summary"]["repair_trace"][0]["new_excerpt"] == "new venue"
    assert data["gate_repair_summary"]["authority"]["final_authority_sink"] == "stage_attempts"
    assert data["gate_repair_summary"]["authority"]["selection_role"] == "historical_companion"
    assert data["result_summary"]["gate_repair"]["director_verdict"] == "PASS_WITH_FIX"
    assert data["result_summary"]["gate_repair"]["fix_pack"]["target_kind"] == "entity_ref"
    assert data["result_summary"]["gate_repair"]["repair_contract"]["subtype"] == "opening_spatial_continuity"


def test_quality_dashboard_endpoint_surfaces_config_authority_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)
    (tmp_path / "config" / "settings").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config" / "prompts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config" / "settings" / "validation.yaml").write_text(
        "scoring:\n  default_pass_threshold: 66\norchestrator:\n  use_self_consistency: true\n"
        "context:\n  mandatory_context_max: 333333\npatch_mode:\n  inplace_below: 62\n"
        "smart_retrieval:\n  stage4_total_budget: 222222\n",
        encoding="utf-8",
    )
    (tmp_path / "config" / "models.yaml").write_text(
        "agents:\n  director: gemini-test-director\n  chief_writer: gemini-test-chief\n  analyst: gemini-test-analyst\n",
        encoding="utf-8",
    )
    (tmp_path / "config" / "prompts" / "director.yaml").write_text(
        '_version: "v-test"\nENSEMBLE_SELECTION_PROMPT: |\n  hello {story_context}\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "modules.core.models_config.resolve_models_yaml_path",
        lambda: tmp_path / "config" / "models.yaml",
    )
    monkeypatch.setenv("PROMPT_DIR", str(tmp_path / "config" / "prompts"))
    from modules.core.prompt_loader import PromptLoader

    PromptLoader._instance = None
    PromptLoader._cache = {}
    PromptLoader._metadata_cache = {}

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    summary = payload["data"]["config_authority_summary"]
    assert summary["available"] is True
    assert summary["thresholds"]["scoring.default_pass_threshold"]["effective_value"] == 66
    assert summary["models"]["director"]["effective_value"] == "gemini-test-director"
    assert summary["prompts"]["director_ensemble_selection"]["prompt_version"] == "director@v-test"
    assert summary["prompts"]["director_ensemble_selection"]["used_fallback"] is False


def test_quality_dashboard_endpoint_surfaces_cost_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    db = DBManager(project_dir / "project_data.db")
    try:
        db.save_cost_record(
            session_id="sess_ep3",
            scope_type="episode",
            scope_id=3,
            total_calls=5,
            total_tokens=900,
            total_cost_usd=1.25,
            model_breakdown={"gpt-5": {"calls": 5}},
        )
        db.save_cost_record(
            session_id="sess_arc1",
            scope_type="arc",
            scope_id=1,
            total_calls=2,
            total_tokens=300,
            total_cost_usd=0.5,
            model_breakdown={"gpt-5-mini": {"calls": 2}},
        )
    finally:
        db.close()

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    cost_summary = payload["data"]["cost_summary"]
    assert cost_summary["available"] is True
    assert cost_summary["row_count"] == 2
    assert cost_summary["latest_session_id"] == "sess_arc1"
    assert cost_summary["total_calls"] == 7
    assert cost_summary["total_tokens"] == 1200
    assert cost_summary["total_cost_usd"] == 1.75
    assert cost_summary["scope_counts"] == {"arc": 1, "episode": 1}
    assert cost_summary["recent"][0]["scope_type"] == "arc"
    assert cost_summary["recent"][1]["scope_type"] == "episode"


def test_quality_dashboard_endpoint_surfaces_patch_effectiveness(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    monitor = PassRateMonitor(str(project_dir))
    monitor.record_attempt(stage=4, episode=3, attempt_num=1, success=False, is_patch=False)
    monitor.record_attempt(stage=4, episode=3, attempt_num=2, success=True, is_patch=True, prev_score=82.0)
    monitor.record_attempt(
        stage=4, episode=4, attempt_num=1, success=False, is_patch=True, patch_fallback=True, prev_score=70.0
    )
    monitor.record_attempt(stage=4, episode=5, attempt_num=1, success=True, is_patch=False)
    monitor.save()

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    patch_effectiveness = payload["data"]["patch_effectiveness"]
    assert patch_effectiveness["available"] is True
    assert patch_effectiveness["stage"] == 4
    assert patch_effectiveness["lookback"] == 20
    assert patch_effectiveness["total_attempts"] == 4
    assert patch_effectiveness["patch_attempts"] == 2
    assert patch_effectiveness["has_patch_attempts"] is True
    assert patch_effectiveness["patch_success_rate"] == 0.5
    assert patch_effectiveness["patch_fallback_rate"] == 0.5
    assert patch_effectiveness["direct_patch_success_rate"] == 1.0
    assert patch_effectiveness["non_patch_success_rate"] == 0.5
    assert patch_effectiveness["avg_prev_score"] == 76.0


def test_quality_dashboard_endpoint_surfaces_episode_rol(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    dashboard = QualityDashboard(project_dir)
    dashboard.record_validation(ep_num=3, result={"decision": "PASS_WITH_FIX", "score": 88}, stage=4)
    dashboard.record_validation(ep_num=4, result={"decision": "PASS", "score": 90}, stage=4)

    monitor = PassRateMonitor(str(project_dir))
    monitor.record_attempt(stage=4, episode=3, attempt_num=1, success=False, token_cost=0.4, duration_ms=60000)
    monitor.record_attempt(stage=4, episode=3, attempt_num=2, success=True, token_cost=0.6, duration_ms=60000)
    monitor.record_attempt(stage=4, episode=4, attempt_num=1, success=True, token_cost=0.5, duration_ms=30000)
    monitor.save()

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    episode_rol = payload["data"]["episode_rol"]
    assert episode_rol["available"] is True
    assert episode_rol["stage"] == 4
    assert episode_rol["lookback"] == 8
    assert episode_rol["formula_version"] == "v1_quality_over_cost_time_retry"
    assert episode_rol["row_count"] == 2
    assert episode_rol["latest_ep"] == 4
    assert episode_rol["best_ep"] == 4
    assert episode_rol["best_rol"] == 90.0
    assert episode_rol["avg_rol"] == 56.0
    assert episode_rol["rows"][0]["ep_num"] == 3
    assert episode_rol["rows"][0]["attempts"] == 2
    assert episode_rol["rows"][0]["retry_penalty"] == 1
    assert episode_rol["rows"][0]["token_cost_usd"] == 1.0
    assert episode_rol["rows"][0]["duration_ms"] == 120000
    assert episode_rol["rows"][0]["duration_minutes"] == 2.0
    assert episode_rol["rows"][0]["investment_score"] == 4.0
    assert episode_rol["rows"][0]["rol_score"] == 22.0
    assert episode_rol["rows"][1]["ep_num"] == 4
    assert episode_rol["rows"][1]["rol_score"] == 90.0


def test_quality_dashboard_endpoint_surfaces_budget_status_as_read_only_guidance(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    dashboard = QualityDashboard(project_dir)
    dashboard.record_validation(ep_num=3, result={"decision": "PASS_WITH_FIX", "score": 88}, stage=4)
    dashboard.record_validation(ep_num=4, result={"decision": "PASS", "score": 90}, stage=4)
    dashboard.record_retrieval_observation(
        ep_num=4,
        stage="director",
        observation={
            "work_focus_present": True,
            "work_slot_summary_included": True,
            "relation_slice_included": True,
            "budget_ledger": {
                "budget_bucket": "context.mandatory_context_max",
                "configured_cap": 2000,
                "effective_cap": 1800,
                "consumed_chars": 1900,
                "dropped_chars": 200,
                "overflow_chars": 100,
                "headroom_chars": 0,
                "trim_applied": True,
            },
        },
    )

    monitor = PassRateMonitor(str(project_dir))
    monitor.record_attempt(stage=4, episode=3, attempt_num=1, success=False, token_cost=0.4, duration_ms=60000)
    monitor.record_attempt(stage=4, episode=3, attempt_num=2, success=True, token_cost=0.6, duration_ms=60000)
    monitor.record_attempt(stage=4, episode=4, attempt_num=1, success=True, token_cost=0.5, duration_ms=30000)
    monitor.save()

    db = DBManager(project_dir / "project_data.db")
    try:
        db.save_cost_record(
            session_id="sess_budget",
            scope_type="episode",
            scope_id=4,
            total_calls=5,
            total_tokens=900,
            total_cost_usd=1.25,
            model_breakdown={"gpt-5": {"calls": 5}},
        )
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=2,
            ep_num=4,
            arc_num=1,
            score=90,
            session_id="sess_budget",
            attempt_key="s4:ep4:arc1:a2:sess_budget",
            candidate_key="A|balanced",
            content_hash="hash-budget",
            artifact_path="logs/artifacts/stage4/ep_0004/attempt_02/final_manuscript__A_balanced.txt",
            advisory_flags={
                "retry_budget_axes": {"round": 1, "repair": 1, "guidance": 0},
            },
        )
        before_counts = {
            "cost_log": db.cursor.execute("SELECT COUNT(*) FROM cost_log").fetchone()[0],
            "stage_attempts": db.cursor.execute("SELECT COUNT(*) FROM stage_attempts").fetchone()[0],
        }
    finally:
        db.close()

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    db = DBManager(project_dir / "project_data.db")
    try:
        after_counts = {
            "cost_log": db.cursor.execute("SELECT COUNT(*) FROM cost_log").fetchone()[0],
            "stage_attempts": db.cursor.execute("SELECT COUNT(*) FROM stage_attempts").fetchone()[0],
        }
    finally:
        db.close()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert after_counts == before_counts
    budget_status = payload["data"]["budget_status"]
    assert budget_status["available"] is True
    assert budget_status["authority_role"] == "companion_snapshot"
    assert budget_status["operator_guidance_only"] is True
    assert budget_status["authoritative_inputs"] == ["cost_summary", "gate_repair_summary"]
    assert budget_status["companion_inputs"] == ["episode_rol", "retrieval_summary"]
    assert budget_status["status"] == "warning"
    assert "runtime gate" not in budget_status["summary"].lower()
    assert budget_status["components"]["cost"]["status"] == "warning"
    assert budget_status["components"]["cost"]["total_cost_usd"] == 1.25
    assert budget_status["components"]["rol"]["status"] == "watch"
    assert budget_status["components"]["rol"]["avg_rol"] == 56.0
    assert budget_status["components"]["retry"]["status"] == "watch"
    assert budget_status["components"]["retry"]["retry_budget_axes"] == {"round": 1, "repair": 1, "guidance": 0}
    assert budget_status["components"]["retrieval"]["status"] == "warning"
    assert budget_status["components"]["retrieval"]["trimmed_rows"] == 1
    assert budget_status["components"]["retrieval"]["overflow_rows"] == 1
    assert budget_status["components"]["retrieval"]["budget_buckets"] == ["context.mandatory_context_max"]


def test_quality_dashboard_endpoint_surfaces_arc_cost_correlation(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    db = DBManager(project_dir / "project_data.db")
    try:
        db.save_cost_record(
            session_id="arc_1_a",
            scope_type="arc",
            scope_id=1,
            total_calls=2,
            total_tokens=500,
            total_cost_usd=1.0,
            model_breakdown={"gpt-5": {"calls": 2}},
        )
        db.save_cost_record(
            session_id="arc_2_a",
            scope_type="arc",
            scope_id=2,
            total_calls=3,
            total_tokens=900,
            total_cost_usd=2.0,
            model_breakdown={"gpt-5": {"calls": 3}},
        )
        db.save_cost_record(
            session_id="arc_2_b",
            scope_type="arc",
            scope_id=2,
            total_calls=1,
            total_tokens=300,
            total_cost_usd=1.0,
            model_breakdown={"gpt-5-mini": {"calls": 1}},
        )
    finally:
        db.close()

    monitor = PassRateMonitor(str(project_dir))
    monitor.record_attempt(stage=4, episode=11, arc=1, attempt_num=1, success=True)
    for attempt in range(1, 4):
        monitor.record_attempt(stage=4, episode=21, arc=2, attempt_num=attempt, success=(attempt == 3))
    monitor.save()

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    arc_cost_correlation = payload["data"]["arc_cost_correlation"]
    assert arc_cost_correlation["available"] is True
    assert arc_cost_correlation["lookback"] == 8
    assert arc_cost_correlation["row_count"] == 2
    assert arc_cost_correlation["latest_arc_no"] == 2
    assert arc_cost_correlation["costliest_arc_no"] == 2
    assert arc_cost_correlation["hardest_arc_no"] == 2
    assert arc_cost_correlation["correlation_coefficient"] == 1.0
    assert arc_cost_correlation["correlation_label"] == "strong_positive"
    assert arc_cost_correlation["rows"][0]["arc_no"] == 1
    assert arc_cost_correlation["rows"][0]["total_cost_usd"] == 1.0
    assert arc_cost_correlation["rows"][1]["arc_no"] == 2
    assert arc_cost_correlation["rows"][1]["difficulty"] == "normal"
    assert arc_cost_correlation["rows"][1]["total_cost_usd"] == 3.0
    assert arc_cost_correlation["rows"][1]["cost_per_attempt_usd"] == 1.0


def test_quality_dashboard_endpoint_surfaces_quality_signal_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    dashboard = QualityDashboard(project_dir)
    dashboard.record_validation(
        ep_num=2,
        result={
            "decision": "PASS",
            "score": 88,
            "quality_signals": {"ced_score": 1.4, "ai_slop_score": 0.3},
        },
        stage=4,
    )
    dashboard.record_validation(
        ep_num=3,
        result={
            "decision": "PASS_WITH_FIX",
            "score": 91,
            "quality_signals": {"ced_score": 1.1, "ai_slop_score": 0.8},
        },
        stage=4,
    )

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    snapshot = payload["data"]["quality_signal_snapshot"]
    assert snapshot["available"] is True
    assert snapshot["lookback"] == 5
    assert snapshot["samples"] == 2
    assert snapshot["latest"]["ced_score"] == 1.1
    assert snapshot["recent"][0]["ep_num"] == 2
    assert snapshot["recent"][1]["quality_signals"]["ai_slop_score"] == 0.8


def test_quality_dashboard_endpoint_surfaces_dominant_contradiction_type_in_episode_trend(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    dashboard = QualityDashboard(project_dir)
    dashboard.record_validation(
        ep_num=2,
        result={
            "decision": "REJECT",
            "score": 74,
            "violations": [
                {
                    "type": "director_reject",
                    "subtype": "numeric_carryover_authority",
                    "dominant_contradiction_type": "numeric_carryover_authority",
                    "repair_contract": {"subtype": "numeric_carryover_authority", "fix_scope": "full"},
                    "scope_authority": {"fix_scope": "full", "authoritative_fix_scope": "inplace"},
                }
            ],
        },
        stage=4,
    )

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    trend_row = payload["data"]["episode_trend"][0]
    assert trend_row["ep_num"] == 2
    assert trend_row["decision"] == "REJECT"
    assert trend_row["dominant_contradiction_type"] == "numeric_carryover_authority"


def test_quality_dashboard_endpoint_surfaces_quality_dashboard_persistence_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    dashboard = QualityDashboard(project_dir)
    with patch("modules.core.quality_dashboard.open", side_effect=OSError("disk full")):
        dashboard.record_validation(
            ep_num=2,
            result={"decision": "PASS", "score": 88, "violations": []},
            stage=4,
        )

    response = asyncio.run(bridge_server.quality_dashboard_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    runtime_health = payload["data"]["runtime_health"]
    assert runtime_health["available"] is True
    assert any(item["component"] == "quality_dashboard.save_record" for item in runtime_health["top_components"])


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
