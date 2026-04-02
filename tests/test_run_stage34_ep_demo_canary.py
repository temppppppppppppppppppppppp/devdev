import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    with (
        patch.object(canary_script, "_load_demo_prep", return_value={"regen_blueprint_ep": 2, "regen_draft_ep": 2}),
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", return_value=app),
        patch.object(canary_script, "analyze_canary", return_value={"multi_stage_proof_scope_summary": {"status": "pass"}}) as analyze,
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
    analyze.assert_called_once_with("demo_project", target_ep=2)
    assert result["multi_stage_proof_scope_summary"]["status"] == "pass"


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
        tmp_path / "projects" / "demo_target",
        from_ep=2,
        force=True,
    )
    prep_path = tmp_path / "projects" / "demo_target" / "logs" / canary_script.PREP_LOG_NAME
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
