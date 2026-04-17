import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import scripts.run_stage34_ep_demo_canary as canary_script


def test_run_stage34_ep_demo_canary_calls_stage3_then_stage4_and_analyzes():
    observed = {}
    stage3_orch = MagicMock()

    def _capture_stage3(**kwargs):
        observed["ctx_at_stage3"] = stage3_orch.ctx
        return {"success_count": 1, "fail_count": 0}

    stage3_orch.stage_3_batch_blueprinting = MagicMock(side_effect=_capture_stage3)
    app = SimpleNamespace(
        _get_int_input=None,
        _stage3_orch=stage3_orch,
        _stage_4_v2_chief_writer=MagicMock(return_value={"status": "pass"}),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(
            db=MagicMock(),
            get_latest_episode_number=MagicMock(return_value=2),
        ),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    with (
        patch.object(canary_script, "_load_demo_prep", return_value={"regen_blueprint_ep": 2, "regen_draft_ep": 2}),
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", return_value=app),
        patch.object(
            canary_script, "analyze_canary", return_value={"multi_stage_proof_scope_summary": {"status": "pass"}}
        ) as analyze,
        patch("modules.core.stage3_context.Stage3Context") as mock_ctx_cls,
    ):
        fake_ctx = MagicMock(name="stage3_ctx")
        mock_ctx_cls.from_app.return_value = fake_ctx
        result = canary_script.run_canary("demo_project", target_ep=2)

    mock_ctx_cls.from_app.assert_called_once_with(app)
    stage3_orch.stage_3_batch_blueprinting.assert_called_once_with(target_ep=2)
    assert observed["ctx_at_stage3"] is fake_ctx
    app._stage_4_v2_chief_writer.assert_called_once_with(limit_mode=False, target_ep=2, skip_pause=True)
    app.pass_rate_monitor.save.assert_called_once()
    app._flush_audit_buffer.assert_called_once()
    analyze.assert_called_once_with("_canary/demo_project", target_ep=2)
    assert result["multi_stage_proof_scope_summary"]["status"] == "pass"


def test_run_stage34_ep_demo_canary_fails_fast_when_frontier_is_not_single_episode_aligned():
    stage3_orch = MagicMock()
    app = SimpleNamespace(
        _get_int_input=None,
        _stage3_orch=stage3_orch,
        _stage_4_v2_chief_writer=MagicMock(return_value={"status": "pass"}),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(
            db=MagicMock(),
            get_latest_episode_number=MagicMock(return_value=3),
        ),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    with (
        patch.object(canary_script, "_load_demo_prep", return_value={"regen_blueprint_ep": 7, "regen_draft_ep": 7}),
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", return_value=app),
        patch.object(canary_script, "analyze_canary") as analyze,
    ):
        with pytest.raises(RuntimeError, match="frontier alignment"):
            canary_script.run_canary("demo_project", target_ep=7)

    stage3_orch.stage_3_batch_blueprinting.assert_not_called()
    app._stage_4_v2_chief_writer.assert_not_called()
    app.pass_rate_monitor.save.assert_not_called()
    app._flush_audit_buffer.assert_not_called()
    analyze.assert_not_called()


def test_prepare_stage34_ep_demo_canary_writes_prep_metadata(tmp_path):
    project_root = tmp_path / "projects"
    target_root = project_root / "demo_target"
    target_root.mkdir(parents=True, exist_ok=True)

    with (
        patch.object(canary_script, "PROJECT_ROOT", tmp_path),
        patch.object(
            canary_script,
            "prepare_stage34_canary_project",
            return_value={"prepared_at": "2026-04-02T20:00:00", "cleanup": {"anchor_validation": {"status": "ok"}}},
        ) as prep,
    ):
        payload = canary_script.prepare_canary("src_project", "demo_target", from_ep=2, force=True)

    prep.assert_called_once_with(
        tmp_path / "projects" / "src_project",
        tmp_path / "projects" / "_canary" / "demo_target",
        from_ep=2,
        force=True,
    )
    prep_path = tmp_path / "projects" / "_canary" / "demo_target" / "logs" / canary_script.PREP_LOG_NAME
    saved = json.loads(prep_path.read_text(encoding="utf-8"))
    assert payload["mode"] == canary_script.MODE_NAME
    assert payload["frozen_authority_ep"] == 1
    assert payload["regen_blueprint_ep"] == 2
    assert payload["regen_draft_ep"] == 2
    assert saved["cleanup"]["anchor_validation"]["status"] == "ok"


def test_analyze_stage34_ep_demo_canary_writes_summary(tmp_path):
    project_root = tmp_path / "projects" / "demo_project"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    prep_payload = {
        "mode": canary_script.MODE_NAME,
        "frozen_authority_ep": 1,
        "regen_blueprint_ep": 2,
        "regen_draft_ep": 2,
        "cleanup": {"anchor_validation": {"status": "ok"}},
    }
    (project_root / "logs" / canary_script.PREP_LOG_NAME).write_text(
        json.dumps(prep_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    stage3_summary = {
        "latest_session_id": "shared_sess",
        "sink_alignment_summary": {"status": "ok"},
        "hard_gates": {"status": "pass"},
    }
    stage4_summary = {
        "project_locator": "projects/demo_project",
        "project_root": str(project_root),
        "latest_session_id": "shared_sess",
        "current_session_sink_alignment_summary": {"status": "ok"},
        "rationale_contract_summary": {"status": "ok"},
        "companion_audit_summary": {"status": "ok"},
        "hard_gates": {"status": "pass"},
    }

    with (
        patch.object(canary_script, "PROJECT_ROOT", tmp_path),
        patch.object(canary_script, "build_stage3_canary_summary", return_value=stage3_summary),
        patch.object(canary_script, "build_stage4_canary_summary", return_value=stage4_summary),
        patch.object(
            canary_script,
            "_build_demo_boundary_summary",
            return_value={"status": "pass", "frozen_authority_ep": 1},
        ),
    ):
        result = canary_script.analyze_canary("demo_project", target_ep=2)

    assert result["summary_role"] == canary_script.SUMMARY_ROLE
    assert result["shared_session_id"] == "shared_sess"
    summary_path = project_root / "logs" / canary_script.SUMMARY_LOG_NAME
    saved = json.loads(summary_path.read_text(encoding="utf-8"))
    assert saved["multi_stage_proof_scope_summary"]["status"] == "pass"
    assert saved["frozen_authority_ep"] == 1


def test_analyze_stage34_ep_demo_canary_requests_sparse_target_stage4_summary(tmp_path):
    project_root = tmp_path / "projects" / "demo_project"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    prep_payload = {
        "mode": canary_script.MODE_NAME,
        "frozen_authority_ep": 6,
        "regen_blueprint_ep": 7,
        "regen_draft_ep": 7,
        "cleanup": {"anchor_validation": {"status": "ok"}},
    }
    (project_root / "logs" / canary_script.PREP_LOG_NAME).write_text(
        json.dumps(prep_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with (
        patch.object(canary_script, "PROJECT_ROOT", tmp_path),
        patch.object(
            canary_script,
            "build_stage3_canary_summary",
            return_value={"latest_session_id": "s3", "sink_alignment_summary": {"status": "ok"}},
        ),
        patch.object(
            canary_script,
            "build_stage4_canary_summary",
            return_value={
                "project_locator": "projects/demo_project",
                "project_root": str(project_root),
                "latest_session_id": "s4",
                "current_session_sink_alignment_summary": {"status": "ok"},
                "rationale_contract_summary": {"status": "ok"},
                "companion_audit_summary": {"status": "ok"},
            },
        ) as build_stage4_summary,
        patch.object(
            canary_script,
            "_build_demo_boundary_summary",
            return_value={
                "status": "warn",
                "proof_grade": "demo_partial_source_authority",
                "closure_grade_ready": False,
            },
        ),
    ):
        canary_script.analyze_canary("demo_project", target_ep=7)

    build_stage4_summary.assert_called_once_with(project_root, target_ep=7, required_draft_eps=[7])


def test_build_demo_boundary_summary_warns_when_exact_frozen_authority_is_missing_but_history_exists(tmp_path):
    project_root = tmp_path / "demo_project"
    drafts_dir = project_root / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    for ep in (1, 2):
        (drafts_dir / f"ep_{ep:04d}.txt").write_text(f"draft {ep}", encoding="utf-8")

    fake_db = SimpleNamespace(conn=MagicMock(), close=MagicMock())
    with (
        patch.object(canary_script, "DBManager", return_value=fake_db),
        patch.object(
            canary_script,
            "_load_ep_list",
            side_effect=[
                [1, 2, 3, 4, 5, 6, 7],
                [1, 2],
                [1, 2, 3, 4, 5, 6, 7],
                [1, 2],
            ],
        ),
    ):
        summary = canary_script._build_demo_boundary_summary(
            project_root,
            target_ep=7,
            prep_payload={"frozen_authority_ep": 6, "cleanup": {"anchor_validation": {"status": "ok"}}},
        )

    assert summary["status"] == "warn"
    assert summary["proof_grade"] == "demo_partial_source_authority"
    assert summary["closure_grade_ready"] is False
    assert summary["latest_available_manuscript_ep"] == 2
    assert summary["latest_available_draft_ep"] == 2
    assert "frozen_authority_draft_missing:ep6" in summary["warnings"]
    assert "frozen_authority_manuscript_missing:ep6" in summary["warnings"]
    assert summary["errors"] == []
