import json
from pathlib import Path

import pytest

from modules.core.db_manager import DBManager
from modules.core.stage4_canary_tools import build_stage4_canary_summary, prepare_stage4_canary_project


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


def test_prepare_stage4_canary_project_rejects_partial_from_ep(tmp_path):
    source = tmp_path / "source_project"
    target = tmp_path / "target_project"
    _make_project_root(source)
    DBManager(source / "project_data.db").close()

    with pytest.raises(ValueError, match="from_ep=1"):
        prepare_stage4_canary_project(source, target, from_ep=2)


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
    assert summary["rationale_contract_summary"]["status"] == "ok"
    assert summary["rationale_contract_summary"]["field_nonempty_counts"]["selection_reason"] == 1
    assert summary["hard_gates"]["status"] == "fail"
    assert "pass_rate_monitor_missing" in summary["hard_gates"]["errors"]
    assert "stage4_retry_contract_not_exercised" in summary["hard_gates"]["warnings"]
    assert "patch_trace_not_exercised" in summary["hard_gates"]["warnings"]


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
