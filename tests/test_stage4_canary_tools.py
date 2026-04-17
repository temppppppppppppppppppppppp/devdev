import json
from pathlib import Path

from modules.core.db_manager import DBManager
from modules.core.stage4_canary_tools import (
    _evaluate_stage4_canary_gates,
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
    assert result["canary_scope"] == "stage4_only"
    assert result["reruns_stage3_generation"] is False
    assert result["preserves_stage3_blueprints"] is True
    assert result["preserves_stage3_sink_baseline"] is True
    assert result["cleanup"]["db_impact"]["blueprints_kept"] == 1

    target_db = DBManager(target / "project_data.db")
    try:
        assert target_db.get_blueprint(1)["ep_num"] == 1
        assert target_db.get_manuscript(1) is None
        stage4_count = target_db.conn.execute("SELECT COUNT(*) AS c FROM stage_attempts WHERE stage = 4").fetchone()[
            "c"
        ]
        stage3_count = target_db.conn.execute("SELECT COUNT(*) AS c FROM stage_attempts WHERE stage = 3").fetchone()[
            "c"
        ]
        sel_count = target_db.conn.execute("SELECT COUNT(*) AS c FROM director_selections WHERE stage = 4").fetchone()[
            "c"
        ]
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
            advisory_flags={
                "repair_contract": {
                    "subtype": "opening_spatial_continuity",
                    "provenance": "runtime_synthesized",
                },
                "scope_authority": {
                    "fix_scope": "partial",
                    "authoritative_fix_scope": "inplace",
                    "scope_origin": "director_authored",
                    "widened": False,
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
                "gate_semantics": {
                    "repair_scope": "targeted_opening_patch",
                },
            },
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
    assert summary["gate_repair_summary"]["session_id"] == "sess"
    assert summary["gate_repair_summary"]["repair_contract_subtype"] == "opening_spatial_continuity"
    assert summary["gate_repair_summary"]["repair_contract_provenance"] == "runtime_synthesized"
    assert summary["gate_repair_summary"]["scope_authority_fix_scope"] == "partial"
    assert summary["gate_repair_summary"]["scope_authority_authoritative_fix_scope"] == "inplace"
    assert summary["gate_repair_summary"]["scope_authority_scope_origin"] == "director_authored"
    assert summary["gate_repair_summary"]["scope_authority_widened"] is False
    assert summary["gate_repair_summary"]["repair_contract"]["subtype"] == "opening_spatial_continuity"
    assert summary["gate_repair_summary"]["scope_authority"]["authoritative_fix_scope"] == "inplace"
    assert summary["gate_repair_summary"]["partial_fix_eval"]["patch_target_id"] == "pt:opening"
    assert summary["gate_repair_summary"]["repair_trace"][0]["target"] == "opening_location_name"
    assert summary["gate_repair_surface_summary"]["status"] == "ok"
    assert summary["gate_repair_surface_summary"]["session_id"] == "sess"
    assert summary["gate_repair_surface_summary"]["repair_contract_subtype"] == "opening_spatial_continuity"
    assert summary["gate_repair_surface_summary"]["repair_contract_provenance"] == "runtime_synthesized"
    assert summary["gate_repair_surface_summary"]["fix_scope"] == "partial"
    assert summary["gate_repair_surface_summary"]["authoritative_fix_scope"] == "inplace"
    assert summary["gate_repair_surface_summary"]["scope_origin"] == "director_authored"
    assert summary["gate_repair_surface_summary"]["widened"] is False
    assert summary["gate_repair_surface_summary"]["mismatch_scope"] == "current_session"
    assert summary["gate_repair_surface_summary"]["mismatch_counts"]["repair_contract_subtype_mismatches"] == 0
    assert summary["rationale_contract_summary"]["status"] == "ok"
    assert summary["rationale_contract_summary"]["field_nonempty_counts"]["selection_reason"] == 1
    assert summary["hard_gates"]["status"] == "warn"
    assert "pass_rate_monitor_cache_missing" in summary["hard_gates"]["warnings"]
    assert "stage4_retry_contract_not_exercised" in summary["hard_gates"]["warnings"]
    assert "patch_trace_not_exercised" not in summary["hard_gates"]["warnings"]


def test_build_stage4_canary_summary_reports_stage3_probe_scope(tmp_path):
    project = tmp_path / "canary_project"
    _make_project_root(project)
    (project / "logs" / "canary_prep.json").write_text(
        json.dumps(
            {
                "source_project": "base",
                "canary_scope": "stage4_only",
                "reruns_stage3_generation": False,
                "preserves_stage3_blueprints": True,
                "preserves_stage3_sink_baseline": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

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
    assert summary["proof_scope_summary"]["scope_status"] == "stage4_only"
    assert summary["proof_scope_summary"]["backend_wide_proof"] is False
    assert summary["proof_scope_summary"]["stage3_sink_probe_status"] == "ok"
    assert summary["proof_scope_summary"]["stage3_probe_origin"] == "baseline_copy"
    assert "stage3_baseline_sink_probe" in summary["proof_scope_summary"]["covered_surfaces"]
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


def test_build_stage4_canary_summary_surfaces_numeric_consistency_summary(tmp_path):
    project = tmp_path / "numauth_project"
    _make_project_root(project)
    artifact_dir = project / "logs" / "artifacts" / "stage4" / "ep_0002" / "attempt_01"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "final_manuscript__A_balanced.txt"
    artifact_path.write_text("artifact", encoding="utf-8")
    (project / "logs" / "canary_prep.json").write_text(
        json.dumps({"source_project": "source", "canary_scope": "stage4_only"}, ensure_ascii=False),
        encoding="utf-8",
    )

    db = DBManager(project / "project_data.db")
    try:
        db.save_stage_attempt(
            stage=4,
            verdict="REJECT",
            ep_num=2,
            attempt_num=1,
            arc_num=1,
            score=71,
            session_id="sess-num",
            attempt_key="s4:ep2:arc1:a1:sess-num",
            candidate_key="A|balanced",
            content_hash="hash-num",
            artifact_path="logs/artifacts/stage4/ep_0002/attempt_01/final_manuscript__A_balanced.txt",
            runtime_advisory=(
                "[NC-1][후보 A][MAJOR][numeric_carryover_authority] "
                "[numeric carryover authority mismatch] 원고 '20억 원' (20.0억) vs resumed "
                "FactLedger 'capital'=2000000000.0억 (EP1 carryover baseline)."
            ),
        )
        db.save_director_selection(
            ep_num=2,
            round_num=1,
            selected_label="A",
            selected_strategy="balanced",
            verdict="REJECT",
            score=71,
            stage=4,
            attempt_key="s4:ep2:arc1:a1:sess-num",
            candidate_key="A|balanced",
            content_hash="hash-num",
            artifact_path="logs/artifacts/stage4/ep_0002/attempt_01/final_manuscript__A_balanced.txt",
        )
    finally:
        db.close()

    (project / "logs" / "episode_production.jsonl").write_text(
        json.dumps(
            {
                "ep": 2,
                "attempt_key": "s4:ep2:arc1:a1:sess-num",
                "verdict": "REJECT",
                "initial_verdict": "REJECT",
                "final_verdict": "REJECT",
                "final_score": 71,
                "candidate_key": "A|balanced",
                "selection_candidate_key": "A|balanced",
                "content_hash": "hash-num",
                "artifact_path": "logs/artifacts/stage4/ep_0002/attempt_01/final_manuscript__A_balanced.txt",
                "patch_trace": {"patch_strategy": "", "structural_attempted": False},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "logs" / "session").mkdir(parents=True, exist_ok=True)
    (project / "logs" / "session" / "decisions.jsonl").write_text(
        json.dumps(
            {
                "stage": "stage4",
                "ep_num": 2,
                "result": "REJECT",
                "score": 71,
                "meta": {
                    "attempt_key": "s4:ep2:arc1:a1:sess-num",
                    "candidate_key": "A|balanced",
                    "content_hash": "hash-num",
                    "artifact_path": "logs/artifacts/stage4/ep_0002/attempt_01/final_manuscript__A_balanced.txt",
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "logs" / "runtime_audit_summary.json").write_text(
        json.dumps({"tag": "interrupted", "total_events": 1, "counts": {"evt": 1}}, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = build_stage4_canary_summary(project, target_ep=2)

    assert summary["numeric_consistency_summary"]["status"] == "warn"
    assert summary["numeric_consistency_summary"]["signal_count"] == 1
    assert summary["numeric_consistency_summary"]["category_counts"]["numeric_carryover_authority"] == 1
    assert summary["numeric_consistency_summary"]["ledger_field_counts"]["capital"] == 1


def test_evaluate_stage4_canary_gates_treats_metadata_only_sink_warn_as_warning():
    gates = _evaluate_stage4_canary_gates(
        target_ep=1,
        draft_count=1,
        runtime_summary={"tag": "stage4_complete", "total_events": 1},
        pass_rate_monitor_exists=True,
        patch_trace_summary={},
        sink_alignment_summary={
            "status": "warn",
            "final_sink_missing": {},
            "lifecycle_sink_missing": {},
            "lifecycle_missing_in_final_sinks": {},
            "patch_strategy_mismatches": [{"attempt_key": "s4:ep2:arc1:a2:sess"}],
            "initial_verdict_mismatches": [],
            "selection_candidate_key_mismatches": [],
            "legacy_key_attempts": 0,
        },
        rationale_contract_summary={"status": "ok", "missing_columns": [], "rows_missing_selection_reason": []},
    )

    assert gates["status"] == "warn"
    assert "patch_strategy_mismatches" in gates["warnings"]
    assert "sink_alignment_status:warn" in gates["warnings"]
    assert "patch_strategy_mismatches" not in gates["errors"]


def test_evaluate_stage4_canary_gates_ignores_companion_only_sink_warn_when_authority_surfaces_are_clean():
    gates = _evaluate_stage4_canary_gates(
        target_ep=1,
        draft_count=1,
        runtime_summary={"tag": "stage4_complete", "total_events": 1},
        pass_rate_monitor_exists=True,
        patch_trace_summary={},
        sink_alignment_summary={
            "status": "warn",
            "final_sink_missing": {},
            "lifecycle_sink_missing": {},
            "lifecycle_missing_in_final_sinks": {},
            "initial_verdict_mismatches": [],
            "patch_strategy_mismatches": [],
            "selection_candidate_key_mismatches": [],
            "legacy_key_attempts": 0,
            "selection_companion_pre_final_rows": [{"attempt_key": "s4:ep3:arc1:a2:sess"}],
        },
        rationale_contract_summary={
            "status": "ok",
            "missing_columns": [],
            "rows_missing_selection_reason": [],
            "rows_missing_verdict_reason": [],
            "rows_missing_retry_context": [],
            "stage4_row_count": 0,
            "retry_required_row_count": 0,
        },
        final_authority_contract_summary={"status": "ok"},
        companion_audit_summary={"status": "ok"},
        gate_repair_surface_summary={"status": "ok"},
    )

    assert gates["status"] == "pass"
    assert "sink_alignment_status:warn" not in gates["warnings"]


def test_evaluate_stage4_canary_gates_supports_sparse_required_draft_eps():
    gates = _evaluate_stage4_canary_gates(
        target_ep=7,
        draft_count=3,
        draft_eps=[1, 2, 7],
        required_draft_eps=[7],
        runtime_summary={"tag": "stage4_complete", "total_events": 1},
        pass_rate_monitor_exists=True,
        patch_trace_summary={},
        sink_alignment_summary={
            "status": "ok",
            "final_sink_missing": {},
            "lifecycle_sink_missing": {},
            "lifecycle_missing_in_final_sinks": {},
            "initial_verdict_mismatches": [],
            "patch_strategy_mismatches": [],
            "selection_candidate_key_mismatches": [],
            "legacy_key_attempts": 0,
        },
        rationale_contract_summary={
            "status": "ok",
            "missing_columns": [],
            "rows_missing_selection_reason": [],
            "rows_missing_verdict_reason": [],
            "rows_missing_retry_context": [],
            "stage4_row_count": 0,
            "retry_required_row_count": 0,
        },
        final_authority_contract_summary={"status": "ok"},
        companion_audit_summary={"status": "ok"},
        gate_repair_surface_summary={"status": "ok"},
    )

    assert gates["status"] == "pass"
    assert "draft_count_mismatch:3!=7" not in gates["errors"]
    assert "required_draft_missing:[7]" not in gates["errors"]


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
            stage=3,
            verdict="PASS",
            ep_num=1,
            attempt_num=1,
            score=90,
            session_id="sess",
            attempt_key="s3:1:1:1:sess",
        )
        db.save_llm_call(
            session_id="sess",
            stage=3,
            ep_num=1,
            agent_name="ChiefWriter",
            model="gemini-2.5-pro",
            prompt_chars=5000,
            response_chars=3000,
            duration_ms=12000,
            success=True,
            input_tokens=1000,
            output_tokens=500,
            total_cost_usd=0.005,
        )
    finally:
        db.close()
    (root / "logs" / "stage3_canary_prep.json").write_text(
        '{"source_project": "base"}',
        encoding="utf-8",
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
    # [TM-1] legacy rows without timing decomposition → 0 (not missing)
    assert telem[0]["total_api_elapsed_ms"] == 0
    assert telem[0]["total_retries"] == 0
    assert telem[0]["total_continuations"] == 0


def test_stage3_episode_telemetry_timing_decomposition(tmp_path):
    """TM-1: telemetry distinguishes ask wall-clock from raw API elapsed."""
    from modules.core.stage4_canary_tools import build_stage3_canary_summary

    root = tmp_path / "stage3_tm1"
    _make_project_root(root)
    db = DBManager(root / "project_data.db")
    try:
        db.save_anchor("genre_info", {"type": "wuxia", "name": "wuxia"})
        db.save_blueprint(1, {"ep_num": 1, "scene_list": [{"scene_no": 1, "summary": "bp"}]})
        db.save_stage_attempt(
            stage=3,
            verdict="PASS",
            ep_num=1,
            attempt_num=1,
            score=90,
            session_id="sess",
            attempt_key="s3:1:1:1:sess",
        )
        # Call 1: normal ask, 1 retry, 2 continuations
        # duration_ms=25000 (wall clock), api_elapsed_ms=8000 (raw API)
        db.save_llm_call(
            session_id="sess",
            stage=3,
            ep_num=1,
            agent_name="ChiefWriter",
            model="gemini-2.5-pro",
            prompt_chars=5000,
            response_chars=3000,
            duration_ms=25000,
            success=True,
            api_elapsed_ms=8000,
            retry_count=1,
            continuation_count=2,
        )
        # Call 2: cached context, 0 retries, 0 continuations
        # duration_ms=5000 (includes API_DELAY), api_elapsed_ms=3000 (raw API)
        db.save_llm_call(
            session_id="sess",
            stage=3,
            ep_num=1,
            agent_name="ChiefWriter",
            model="gemini-2.5-pro",
            prompt_chars=2000,
            response_chars=1500,
            duration_ms=5000,
            success=True,
            context_tag="cached_context",
            api_elapsed_ms=3000,
            retry_count=0,
            continuation_count=0,
        )
    finally:
        db.close()
    (root / "logs" / "stage3_canary_prep.json").write_text(
        '{"source_project": "base"}',
        encoding="utf-8",
    )

    summary = build_stage3_canary_summary(root, target_ep=1)
    telem = summary["episode_telemetry"]
    assert len(telem) == 1
    ep1 = telem[0]

    # Wall-clock sum: 25000 + 5000 = 30000
    assert ep1["total_duration_ms"] == 30000
    # Raw API sum: 8000 + 3000 = 11000 — NOT 30000
    assert ep1["total_api_elapsed_ms"] == 11000
    # Retries: 1 + 0 = 1
    assert ep1["total_retries"] == 1
    # Continuations: 2 + 0 = 2
    assert ep1["total_continuations"] == 2
    # The gap (30000 - 11000 = 19000ms) is orchestration overhead, NOT "API hang"
    assert ep1["total_duration_ms"] - ep1["total_api_elapsed_ms"] == 19000
