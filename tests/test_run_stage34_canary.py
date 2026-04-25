from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import scripts.run_stage34_canary as canary_script


def test_run_stage34_canary_archives_after_analyze():
    app = SimpleNamespace(
        _get_int_input=None,
        _one_stop_pipeline_frontier_lag=MagicMock(),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock(), master_bible={}),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()
    app.current_project.db.load_anchor = MagicMock(return_value=[{"ep_end": 4}])

    with (
        patch.object(
            canary_script,
            "resolve_workspace_project_dir",
            return_value=canary_script.PROJECT_ROOT / "canary" / "proof_refresh",
        ),
        patch.object(canary_script, "project_name_from_path", return_value="proof_refresh"),
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", return_value=app),
        patch.object(
            canary_script,
            "analyze_canary",
            return_value={"multi_stage_proof_scope_summary": {"status": "pass"}},
        ) as analyze,
        patch.object(
            canary_script,
            "safe_archive_benchmark_record",
            return_value={"status": "ok", "run_id": "canary-s34"},
        ) as archive,
    ):
        result = canary_script.run_canary("proof_refresh", target_ep=4)

    app._one_stop_pipeline_frontier_lag.assert_called_once()
    app.pass_rate_monitor.save.assert_called_once()
    app._flush_audit_buffer.assert_called_once()
    analyze.assert_called_once_with("proof_refresh", target_ep=4)
    archive.assert_called_once()
    assert result["benchmark_archive"]["run_id"] == "canary-s34"


def test_stage34_run_main_returns_nonzero_on_failed_multi_stage_proof():
    with (
        patch("sys.argv", ["run_stage34_canary.py", "run", "--project", "s34", "--target-ep", "4"]),
        patch.object(
            canary_script,
            "run_canary",
            return_value={"multi_stage_proof_scope_summary": {"status": "fail"}, "benchmark_archive": {"status": "ok"}},
        ),
    ):
        assert canary_script.main() == 1
