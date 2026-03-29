import json
from pathlib import Path

from modules.core.db_manager import DBManager
from modules.core.stage4_canary_tools import (
    build_stage4_branch_inventory,
    build_stage4_canary_summary,
    prepare_stage4_canary_project,
    prepare_stage34_canary_project,
)


def _make_project_root(root: Path) -> None:
    for rel in ("drafts", "logs", "memory", "plans/arcs", "plans/blueprints", "config", "stage0_output"):
        (root / rel).mkdir(parents=True, exist_ok=True)


def test_prepare_stage4_canary_project_copies_and_resets_stage4_only(tmp_path):
    source = tmp_path / "source_project"
    target = tmp_path / "target_project"
    _make_project_root(source)

    source_db = DBManager(source / "project_data.db")
    try:
        source_db.save_anchor("genre_info", {"type": "investment", "name": "investment"})
        source_db.save_blueprint(1, {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "bp"}]})
        source_db.save_manuscript(1, "제1화", "원고 본문")
        source_db.save_state_log(1, {"state_updates": {"cash": "1000"}})
        source_db.save_director_selection(
            ep_num=1,
            round_num=1,
            selected_label="best",
            selected_strategy="ensemble",
            verdict="PASS",
            score=96,
            stage=4,
            attempt_key="stage4:1:1:1:session",
        )
        source_db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            ep_num=1,
            attempt_num=1,
            score=96,
            session_id="session",
            attempt_key="stage4:1:1:1:session",
        )
        source_db.save_stage_attempt(
            stage=3,
            verdict="PASS_WITH_WARNING",
            ep_num=1,
            attempt_num=1,
            score=91,
            session_id="session",
            attempt_key="stage3:1:1:1:session",
        )
    finally:
        source_db.close()

    (source / "drafts" / "ep_0001.txt").write_text("draft", encoding="utf-8")
    (source / "logs" / "episode_production.jsonl").write_text('{"ep": 1}\n', encoding="utf-8")
    (source / "logs" / "pass_rate_monitor.json").write_text('{"records": []}', encoding="utf-8")
    (source / "memory" / "vec.db").write_text("stub", encoding="utf-8")

    result = prepare_stage4_canary_project(source, target)

    assert result["source_project"] == "source_project"
    assert result["target_project"] == "target_project"
    assert result["cleanup"]["db_impact"]["blueprints_kept"] == 1

    target_db = DBManager(target / "project_data.db")
    try:
        assert target_db.get_blueprint(1)["ep_num"] == 1
        assert target_db.get_manuscript(1) is None
        stage4_count = target_db.conn.execute("SELECT COUNT(*) AS c FROM stage_attempts WHERE stage = 4").fetchone()["c"]
        stage3_count = target_db.conn.execute("SELECT COUNT(*) AS c FROM stage_attempts WHERE stage = 3").fetchone()["c"]
        sel_count = target_db.conn.execute(
            "SELECT COUNT(*) AS c FROM director_selections WHERE stage = 4"
        ).fetchone()["c"]
        assert stage4_count == 0
        assert sel_count == 0
        assert stage3_count == 1
    finally:
        target_db.close()

    assert (target / "drafts" / "ep_0001.txt").exists() is False
    assert sorted(p.name for p in (target / "logs").iterdir()) == ["canary_prep.json"]
    assert list((target / "memory").iterdir()) == []

    source_db = DBManager(source / "project_data.db")
    try:
        assert source_db.get_blueprint(1)["ep_num"] == 1
        assert source_db.get_manuscript(1)["title"] == "제1화"
    finally:
        source_db.close()


def test_prepare_stage4_canary_project_supports_partial_from_ep(tmp_path):
    source = tmp_path / "source_project"
    target = tmp_path / "target_project"
    _make_project_root(source)
    db = DBManager(source / "project_data.db")
    try:
        db.save_anchor("genre_info", {"type": "investment", "name": "investment"})
    finally:
        db.close()

    (source / "drafts" / "ep_0001.txt").write_text("draft-1", encoding="utf-8")
    (source / "drafts" / "ep_0004.txt").write_text("draft-4", encoding="utf-8")

    result = prepare_stage4_canary_project(source, target, from_ep=4)

    assert result["from_ep"] == 4
    assert (target / "drafts" / "ep_0001.txt").exists() is True
    assert (target / "drafts" / "ep_0004.txt").exists() is False


def test_prepare_stage34_canary_project_resets_blueprints_and_stage3_stage4_outputs(tmp_path):
    source = tmp_path / "source_stage34"
    target = tmp_path / "target_stage34"
    _make_project_root(source)

    source_db = DBManager(source / "project_data.db")
    try:
        source_db.save_anchor("genre_info", {"type": "investment", "name": "investment"})
        source_db.save_anchor("arcs", [{"arc_no": 1, "ep_start": 1, "ep_end": 4}])
        source_db.save_blueprint(1, {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "bp"}]})
        source_db.save_manuscript(1, "제1화", "원고")
        source_db.save_stage_attempt(
            stage=3,
            verdict="PASS",
            ep_num=1,
            attempt_num=1,
            score=93,
            session_id="sess",
            attempt_key="stage3:1:1:1:sess",
        )
        source_db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            ep_num=1,
            attempt_num=1,
            score=97,
            session_id="sess",
            attempt_key="stage4:1:1:1:sess",
        )
        source_db.save_director_selection(
            ep_num=1,
            round_num=1,
            selected_label="best",
            selected_strategy="stage3",
            verdict="PASS",
            score=93,
            stage=3,
            attempt_key="stage3:1:1:1:sess",
        )
        source_db.save_director_selection(
            ep_num=1,
            round_num=1,
            selected_label="best",
            selected_strategy="stage4",
            verdict="PASS",
            score=97,
            stage=4,
            attempt_key="stage4:1:1:1:sess",
        )
    finally:
        source_db.close()

    (source / "drafts" / "ep_0001.txt").write_text("draft", encoding="utf-8")
    (source / "plans" / "blueprints" / "ep_0001.json").write_text('{"ep_num": 1}', encoding="utf-8")
    (source / "logs" / "episode_production.jsonl").write_text('{"ep": 1}\n', encoding="utf-8")

    result = prepare_stage34_canary_project(source, target)

    assert result["cleanup"]["db_impact"]["blueprints_removed"] == 1
    assert result["cleanup"]["db_impact"]["stage3_attempts"] == 1
    assert result["cleanup"]["db_impact"]["stage4_attempts"] == 1

    target_db = DBManager(target / "project_data.db")
    try:
        assert target_db.load_anchor("arcs") == [{"arc_no": 1, "ep_start": 1, "ep_end": 4}]
        assert target_db.get_blueprint(1) is None
        assert target_db.get_manuscript(1) is None
        assert target_db.conn.execute("SELECT COUNT(*) AS c FROM stage_attempts WHERE stage = 3").fetchone()["c"] == 0
        assert target_db.conn.execute("SELECT COUNT(*) AS c FROM stage_attempts WHERE stage = 4").fetchone()["c"] == 0
    finally:
        target_db.close()

    assert (target / "plans" / "blueprints" / "ep_0001.json").exists() is False
    assert sorted(p.name for p in (target / "logs").iterdir()) == ["stage34_canary_prep.json"]


def test_build_stage4_canary_summary_surfaces_warn_gates(tmp_path):
    project = tmp_path / "canary_project"
    _make_project_root(project)
    artifact_dir = project / "logs" / "artifacts" / "stage4" / "ep_0001" / "attempt_01"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "manuscript__best.txt"
    artifact_path.write_text("artifact", encoding="utf-8")

    db = DBManager(project / "project_data.db")
    try:
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            ep_num=1,
            attempt_num=1,
            score=98,
            session_id="sess",
            attempt_key="stage4:1:1:1:sess",
            candidate_key="best",
            content_hash="hash-1",
            artifact_path="logs/artifacts/stage4/ep_0001/attempt_01/manuscript__best.txt",
            selection_reason="best candidate",
            verdict_reason="director pass",
        )
    finally:
        db.close()

    for ep in range(1, 5):
        (project / "drafts" / f"ep_{ep:04d}.txt").write_text(f"ep{ep}", encoding="utf-8")
    (project / "logs" / "runtime_audit_summary.json").write_text(
        json.dumps({"tag": "stage4_complete", "total_events": 1, "counts": {"stage4_complete": 1}}, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = build_stage4_canary_summary(project, target_ep=4)

    assert summary["project_locator"].endswith("canary_project")
    assert summary["draft_count"] == 4
    assert summary["runtime_audit_tag"] == "stage4_complete"
    assert summary["stage4_attempts"] == 1
    assert summary["proof_record_summary"]["classification"] == "current"
    assert summary["companion_audit_summary"]["status"] == "ok"
    assert summary["final_authority_contract_summary"]["status"] == "ok"
    assert summary["final_authority_contract_summary"]["final_authority_sink"] == "stage_attempts"
    assert summary["proof_scope_summary"]["backend_wide_proof"] is False
    assert summary["proof_scope_summary"]["stage3_sink_probe_status"] == "missing"
    assert summary["rationale_contract_summary"]["status"] == "ok"
    assert summary["rationale_contract_summary"]["field_nonempty_counts"]["selection_reason"] == 1
    assert summary["hard_gates"]["status"] == "fail"
    assert "pass_rate_monitor_missing" in summary["hard_gates"]["errors"]
    assert "stage4_retry_contract_not_exercised" in summary["hard_gates"]["warnings"]
    assert "patch_trace_not_exercised" in summary["hard_gates"]["warnings"]


def test_build_stage4_canary_summary_reports_stage3_probe_scope(tmp_path):
    project = tmp_path / "canary_project"
    _make_project_root(project)

    stage3_artifact_dir = project / "logs" / "artifacts" / "stage3" / "ep_0001" / "attempt_01"
    stage3_artifact_dir.mkdir(parents=True, exist_ok=True)
    stage3_artifact_path = stage3_artifact_dir / "blueprint__best.json"
    stage3_artifact_path.write_text('{"ok": true}', encoding="utf-8")

    stage4_artifact_dir = project / "logs" / "artifacts" / "stage4" / "ep_0001" / "attempt_01"
    stage4_artifact_dir.mkdir(parents=True, exist_ok=True)
    stage4_artifact_path = stage4_artifact_dir / "manuscript__best.txt"
    stage4_artifact_path.write_text("artifact", encoding="utf-8")

    db = DBManager(project / "project_data.db")
    try:
        db.save_director_selection(
            ep_num=1,
            round_num=1,
            selected_label="best",
            selected_strategy="balanced",
            verdict="PASS",
            score=93,
            stage=3,
            attempt_key="stage3:1:1:1:sess",
            candidate_key="best",
            content_hash="hash-3",
            artifact_path="logs/artifacts/stage3/ep_0001/attempt_01/blueprint__best.json",
            selection_reason="stage3 selected",
            verdict_reason="stage3 ok",
            fix_scope="tighten beats",
        )
        db.save_stage_attempt(
            stage=3,
            verdict="PASS",
            ep_num=1,
            attempt_num=1,
            score=93,
            session_id="sess",
            attempt_key="stage3:1:1:1:sess",
            candidate_key="best",
            content_hash="hash-3",
            artifact_path="logs/artifacts/stage3/ep_0001/attempt_01/blueprint__best.json",
            selection_reason="stage3 selected",
            verdict_reason="stage3 ok",
            fix_scope="tighten beats",
        )
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            ep_num=1,
            attempt_num=1,
            score=98,
            session_id="sess",
            attempt_key="stage4:1:1:1:sess",
            candidate_key="best",
            content_hash="hash-4",
            artifact_path="logs/artifacts/stage4/ep_0001/attempt_01/manuscript__best.txt",
            selection_reason="best candidate",
            verdict_reason="director pass",
        )
    finally:
        db.close()

    (project / "drafts" / "ep_0001.txt").write_text("ep1", encoding="utf-8")
    (project / "logs" / "pass_rate_monitor.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "stage": 3,
                        "episode": 1,
                        "arc": 1,
                        "attempt_num": 1,
                        "success": True,
                        "attempt_key": "stage3:1:1:1:sess",
                        "final_verdict": "PASS",
                        "candidate_key": "best",
                        "content_hash": "hash-3",
                        "artifact_path": "logs/artifacts/stage3/ep_0001/attempt_01/blueprint__best.json",
                    },
                    {
                        "stage": 4,
                        "episode": 1,
                        "arc": 1,
                        "attempt_num": 1,
                        "success": True,
                        "attempt_key": "stage4:1:1:1:sess",
                        "final_verdict": "PASS",
                        "candidate_key": "best",
                        "content_hash": "hash-4",
                        "artifact_path": "logs/artifacts/stage4/ep_0001/attempt_01/manuscript__best.txt",
                    },
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (project / "logs" / "session").mkdir(parents=True, exist_ok=True)
    (project / "logs" / "session" / "decisions.jsonl").write_text(
        json.dumps(
            {
                "stage": "stage3",
                "result": "PASS",
                "score": 93,
                "meta": {
                    "attempt_key": "stage3:1:1:1:sess",
                    "candidate_key": "best",
                    "content_hash": "hash-3",
                    "artifact_path": "logs/artifacts/stage3/ep_0001/attempt_01/blueprint__best.json",
                    "selection_reason": "stage3 selected",
                    "verdict_reason": "stage3 ok",
                    "fix_scope": "tighten beats",
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "logs" / "runtime_audit_summary.json").write_text(
        json.dumps({"tag": "stage4_complete", "total_events": 1, "counts": {"stage4_complete": 1}}, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = build_stage4_canary_summary(project, target_ep=1)

    assert summary["stage3_sink_alignment_summary"]["status"] == "ok"
    assert summary["stage3_sink_alignment_summary"]["coverage"]["session_decisions"] == 1
    assert summary["proof_scope_summary"]["scope_status"] == "partial_multi_stage_probe"
    assert summary["proof_scope_summary"]["backend_wide_proof"] is False
    assert summary["proof_scope_summary"]["stage3_sink_probe_status"] == "ok"
    assert "stage3_sink_alignment_probe" in summary["proof_scope_summary"]["covered_surfaces"]
    assert "stage3_live_generation_path" in summary["proof_scope_summary"]["uncovered_surfaces"]


def test_build_stage4_canary_summary_companion_audit_flags_missing_stage_attempt_rationale(tmp_path):
    project = tmp_path / "기록용" / "canary_project"
    _make_project_root(project)
    artifact_dir = project / "logs" / "artifacts" / "stage4" / "ep_0001" / "attempt_01"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "manuscript__best.txt"
    artifact_path.write_text("artifact", encoding="utf-8")

    db = DBManager(project / "project_data.db")
    try:
        db.save_director_selection(
            ep_num=1,
            round_num=1,
            selected_label="best",
            selected_strategy="balanced",
            verdict="PASS",
            score=97,
            stage=4,
            attempt_key="stage4:1:1:1:sess",
            candidate_key="best",
            content_hash="hash-1",
            artifact_path="logs/artifacts/stage4/ep_0001/attempt_01/manuscript__best.txt",
            selection_reason="director reason",
            verdict_reason="director verdict",
        )
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            ep_num=1,
            attempt_num=1,
            score=97,
            session_id="sess",
            attempt_key="stage4:1:1:1:sess",
            candidate_key="best",
            content_hash="hash-1",
            artifact_path="logs/artifacts/stage4/ep_0001/attempt_01/manuscript__best.txt",
        )
    finally:
        db.close()

    (project / "drafts" / "ep_0001.txt").write_text("ep1", encoding="utf-8")
    (project / "logs" / "pass_rate_monitor.json").write_text('{"records": []}', encoding="utf-8")
    (project / "logs" / "runtime_audit_summary.json").write_text(
        json.dumps({"tag": "stage4_complete", "total_events": 1, "counts": {"stage4_complete": 1}}, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = build_stage4_canary_summary(project, target_ep=1)

    assert summary["proof_record_summary"]["classification"] == "historical"
    assert summary["companion_audit_summary"]["status"] == "fail"
    assert summary["companion_audit_summary"]["director_rationale_available"] == 1
    assert summary["companion_audit_summary"]["rows_missing_required_fields"] == [
        {
            "attempt_key": "stage4:1:1:1:sess",
            "locator": "ep1:a1:PASS",
            "missing_fields": ["selection_reason", "verdict_reason"],
            "director_rationale_available": True,
        }
    ]


def test_build_stage4_canary_summary_fails_when_rationale_fields_missing(tmp_path):
    project = tmp_path / "canary_project"
    _make_project_root(project)
    artifact_dir = project / "logs" / "artifacts" / "stage4" / "ep_0001" / "attempt_01"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "manuscript__best.txt"
    artifact_path.write_text("artifact", encoding="utf-8")

    db = DBManager(project / "project_data.db")
    try:
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            ep_num=1,
            attempt_num=1,
            score=98,
            session_id="sess",
            attempt_key="stage4:1:1:1:sess",
            candidate_key="best",
            content_hash="hash-1",
            artifact_path="logs/artifacts/stage4/ep_0001/attempt_01/manuscript__best.txt",
        )
    finally:
        db.close()

    (project / "drafts" / "ep_0001.txt").write_text("ep1", encoding="utf-8")
    (project / "logs" / "pass_rate_monitor.json").write_text('{"records": []}', encoding="utf-8")
    (project / "logs" / "runtime_audit_summary.json").write_text(
        json.dumps({"tag": "stage4_complete", "total_events": 1, "counts": {"stage4_complete": 1}}, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = build_stage4_canary_summary(project, target_ep=1)

    assert summary["rationale_contract_summary"]["status"] == "fail"
    assert summary["rationale_contract_summary"]["rows_missing_selection_reason"] == ["ep1:a1:PASS"]
    assert summary["rationale_contract_summary"]["rows_missing_verdict_reason"] == ["ep1:a1:PASS"]
    assert "stage4_selection_reason_missing" in summary["hard_gates"]["errors"]
    assert "stage4_verdict_reason_missing" in summary["hard_gates"]["errors"]


def test_build_stage4_canary_summary_fails_when_retry_context_missing(tmp_path):
    project = tmp_path / "canary_project"
    _make_project_root(project)
    artifact_dir = project / "logs" / "artifacts" / "stage4" / "ep_0001" / "attempt_01"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "manuscript__best.txt"
    artifact_path.write_text("artifact", encoding="utf-8")

    db = DBManager(project / "project_data.db")
    try:
        db.save_stage_attempt(
            stage=4,
            verdict="REJECT",
            ep_num=1,
            attempt_num=1,
            score=61,
            session_id="sess",
            attempt_key="stage4:1:1:1:sess",
            candidate_key="best",
            content_hash="hash-1",
            artifact_path="logs/artifacts/stage4/ep_0001/attempt_01/manuscript__best.txt",
            selection_reason="best candidate",
            verdict_reason="continuity conflict",
        )
    finally:
        db.close()

    (project / "drafts" / "ep_0001.txt").write_text("ep1", encoding="utf-8")
    (project / "logs" / "pass_rate_monitor.json").write_text('{"records": []}', encoding="utf-8")
    (project / "logs" / "runtime_audit_summary.json").write_text(
        json.dumps({"tag": "stage4_complete", "total_events": 1, "counts": {"stage4_complete": 1}}, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = build_stage4_canary_summary(project, target_ep=1)

    assert summary["rationale_contract_summary"]["retry_required_row_count"] == 1
    assert summary["rationale_contract_summary"]["rows_missing_retry_context"] == ["ep1:a1:REJECT"]
    assert "stage4_retry_context_missing" in summary["hard_gates"]["errors"]


def test_build_stage4_branch_inventory_tracks_pass_patch_and_retry_coverage(tmp_path):
    pass_project = tmp_path / "pass_project"
    patch_project = tmp_path / "patch_project"
    _make_project_root(pass_project)
    _make_project_root(patch_project)

    (pass_project / "logs").mkdir(parents=True, exist_ok=True)
    (patch_project / "logs").mkdir(parents=True, exist_ok=True)

    pass_summary = {
        "project": "pass_project",
        "project_locator": "projects/pass_project",
        "latest_session_id": "sess-pass",
        "proof_record_summary": {"classification": "current", "proof_origin": "current_workspace_refresh"},
        "sink_alignment_summary": {"status": "ok"},
        "current_session_sink_alignment_summary": {"status": "ok"},
        "rationale_contract_summary": {"status": "ok", "retry_required_row_count": 0, "rows_missing_retry_context": []},
        "companion_audit_summary": {"status": "ok"},
        "patch_trace_summary": {},
        "hard_gates": {"status": "warn", "warnings": ["stage4_retry_contract_not_exercised"], "errors": []},
    }
    patch_summary = {
        "project": "patch_project",
        "project_locator": "projects/patch_project",
        "latest_session_id": "sess-patch",
        "proof_record_summary": {"classification": "current", "proof_origin": "current_workspace_refresh"},
        "sink_alignment_summary": {"status": "fail"},
        "current_session_sink_alignment_summary": {"status": "ok"},
        "rationale_contract_summary": {"status": "ok", "retry_required_row_count": 0, "rows_missing_retry_context": []},
        "companion_audit_summary": {"status": "ok"},
        "patch_trace_summary": {"count": 1, "strategy_counts": {"inplace_patch_structural": 1}},
        "hard_gates": {"status": "fail", "warnings": [], "errors": ["final_sink_missing"]},
    }
    (pass_project / "logs" / "canary_summary.json").write_text(
        json.dumps(pass_summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (patch_project / "logs" / "canary_summary.json").write_text(
        json.dumps(patch_summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    inventory = build_stage4_branch_inventory([pass_project, patch_project])

    assert inventory["entries_considered"] == 2
    assert inventory["branch_coverage"]["pass_path_current_basis"]["status"] == "covered"
    assert inventory["branch_coverage"]["pass_path_current_basis"]["basis_project_locator"] == "projects/pass_project"
    assert inventory["branch_coverage"]["patch_path_current_basis"]["status"] == "covered"
    assert inventory["branch_coverage"]["patch_path_current_basis"]["basis_project_locator"] == "projects/patch_project"
    assert "same-session sink alignment is ok" in inventory["branch_coverage"]["patch_path_current_basis"]["note"]
    assert inventory["branch_coverage"]["retry_path_current_basis"]["status"] == "missing"
    assert "stage4_retry_contract_not_exercised_live" in inventory["unresolved_runtime_only"]


def test_build_stage3_canary_summary_includes_episode_telemetry(tmp_path):
    """Tranche B: canary summary includes compact per-episode telemetry."""
    from modules.core.stage4_canary_tools import build_stage3_canary_summary

    root = tmp_path / "stage3_telem"
    _make_project_root(root)
    db = DBManager(root / "project_data.db")
    try:
        db.save_anchor("genre_info", {"type": "wuxia", "name": "wuxia"})
        db.save_blueprint(1, {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "bp"}]})
        db.save_stage_attempt(
            stage=3, verdict="PASS", ep_num=1, attempt_num=1,
            score=90, session_id="sess", attempt_key="s3:1:1:1:sess",
        )
        db.save_llm_call(
            session_id="sess", stage=3, ep_num=1,
            agent_name="ChiefWriter", model="gemini-2.5-pro",
            prompt_chars=5000, response_chars=3000, duration_ms=12000,
            success=True, input_tokens=1000, output_tokens=500,
            total_cost_usd=0.005,
        )
    finally:
        db.close()
    (root / "logs" / "stage3_canary_prep.json").write_text(
        '{"source_project": "base"}', encoding="utf-8",
    )

    summary = build_stage3_canary_summary(root, target_ep=1)

    assert "episode_telemetry" in summary
    telem = summary["episode_telemetry"]
    assert len(telem) == 1
    assert telem[0]["ep_num"] == 1
    assert telem[0]["attempt_count"] == 1
    assert telem[0]["final_verdict"] == "PASS"
    assert telem[0]["llm_call_count"] == 1
    assert telem[0]["total_duration_ms"] == 12000
    assert telem[0]["total_cost_usd"] == 0.005
