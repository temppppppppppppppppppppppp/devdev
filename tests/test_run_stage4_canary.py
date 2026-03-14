from types import SimpleNamespace
import json
from unittest.mock import MagicMock, patch

import scripts.run_stage4_canary as canary_script


def test_run_canary_saves_and_flushes_before_analyze():
    app = SimpleNamespace(
        _get_int_input=None,
        _stage_4_v2_chief_writer=MagicMock(),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", return_value=app),
        patch.object(canary_script, "analyze_canary", return_value={"hard_gates": {"status": "pass"}}) as analyze,
    ):
        result = canary_script.run_canary("00_test_06", target_ep=4)

    app._stage_4_v2_chief_writer.assert_called_once_with(limit_mode=False, target_ep=4)
    app.pass_rate_monitor.save.assert_called_once()
    app._flush_audit_buffer.assert_called_once()
    analyze.assert_called_once_with("00_test_06", target_ep=4)
    assert result["hard_gates"]["status"] == "pass"


def test_run_canary_bootstraps_missing_pass_rate_monitor():
    monitor = MagicMock()
    app = SimpleNamespace(
        _get_int_input=None,
        _stage_4_v2_chief_writer=MagicMock(),
        pass_rate_monitor=None,
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", return_value=app),
        patch.object(canary_script, "PassRateMonitor", return_value=monitor) as prm_cls,
        patch.object(canary_script, "analyze_canary", return_value={"hard_gates": {"status": "pass"}}),
    ):
        canary_script.run_canary("00_test_06", target_ep=4)

    prm_cls.assert_called_once_with(canary_script.PROJECT_ROOT / "projects" / "00_test_06")
    assert app.pass_rate_monitor is monitor
    monitor.save.assert_called_once()
    app._stage_4_v2_chief_writer.assert_called_once_with(limit_mode=False, target_ep=4)


def test_run_canary_without_genre_raises():
    with patch.object(canary_script, "_load_project_genre", return_value={}):
        try:
            canary_script.run_canary("00_test_06", target_ep=4)
        except RuntimeError as exc:
            assert "genre_info" in str(exc)
        else:
            raise AssertionError("expected RuntimeError for missing genre")


def test_analyze_canary_writes_summary_and_companion_audit(tmp_path):
    project_root = tmp_path / "projects" / "proof_refresh"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    summary_payload = {
        "project_locator": "projects/proof_refresh",
        "proof_record_summary": {"classification": "current"},
        "companion_audit_summary": {"status": "fail", "row_count": 1},
        "hard_gates": {"status": "fail"},
    }

    with (
        patch.object(canary_script, "PROJECT_ROOT", tmp_path),
        patch.object(canary_script, "build_stage4_canary_summary", return_value=summary_payload),
    ):
        result = canary_script.analyze_canary("proof_refresh", target_ep=4)

    assert result == summary_payload
    summary_path = project_root / "logs" / "canary_summary.json"
    companion_path = project_root / "logs" / "canary_companion_audit.json"
    assert json.loads(summary_path.read_text(encoding="utf-8")) == summary_payload
    assert json.loads(companion_path.read_text(encoding="utf-8")) == {
        "project_locator": "projects/proof_refresh",
        "proof_record_summary": {"classification": "current"},
        "companion_audit_summary": {"status": "fail", "row_count": 1},
    }


def test_branch_inventory_writes_output(tmp_path):
    project_root = tmp_path / "projects" / "proof_refresh"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)

    with (
        patch.object(canary_script, "PROJECT_ROOT", tmp_path),
        patch.object(
            canary_script,
            "build_stage4_branch_inventory",
            return_value={"summary_role": "stage4_runtime_branch_proof_inventory", "entries_considered": 1},
        ),
    ):
        result = canary_script.branch_inventory(["proof_refresh"], output_path="docs/out.json")

    assert result["entries_considered"] == 1
    out_path = tmp_path / "docs" / "out.json"
    assert json.loads(out_path.read_text(encoding="utf-8")) == {
        "summary_role": "stage4_runtime_branch_proof_inventory",
        "entries_considered": 1,
    }
