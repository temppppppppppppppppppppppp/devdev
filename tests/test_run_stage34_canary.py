import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import scripts.run_stage34_canary as canary_script


def test_run_stage34_canary_uses_frontier_lag_and_analyzes():
    app = SimpleNamespace(
        _get_int_input=None,
        _one_stop_pipeline_frontier_lag=MagicMock(),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(
            db=MagicMock(),
            master_bible={"MasterBible": {"plot_roadmap": [{}, {}]}},
        ),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()
    app.current_project.db.load_anchor = MagicMock(
        side_effect=lambda key: [{"arc_no": 1, "ep_start": 1, "ep_end": 4}, {"arc_no": 2, "ep_start": 5, "ep_end": 8}]
        if key == "arcs"
        else None
    )

    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", return_value=app),
        patch.object(
            canary_script,
            "analyze_canary",
            return_value={"multi_stage_proof_scope_summary": {"status": "pass"}},
        ) as analyze,
    ):
        result = canary_script.run_canary("00_test_02", target_ep=4)

    app._one_stop_pipeline_frontier_lag.assert_called_once_with()
    app.pass_rate_monitor.save.assert_called_once()
    app._flush_audit_buffer.assert_called_once()
    analyze.assert_called_once_with("_canary/00_test_02", target_ep=4)
    assert result["multi_stage_proof_scope_summary"]["status"] == "pass"


def test_run_stage34_canary_clamps_frontier_to_target_ep():
    observed = {}

    def _run_frontier():
        observed["arcs"] = app.current_project.db.load_anchor("arcs")
        observed["plot_len"] = len(app.current_project.master_bible["MasterBible"]["plot_roadmap"])

    app = SimpleNamespace(
        _get_int_input=None,
        _one_stop_pipeline_frontier_lag=MagicMock(side_effect=_run_frontier),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(
            db=MagicMock(),
            master_bible={"MasterBible": {"plot_roadmap": [{}, {}, {}]}},
        ),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()
    app.current_project.db.load_anchor = MagicMock(
        side_effect=lambda key: [
            {"arc_no": 1, "ep_start": 1, "ep_end": 4},
            {"arc_no": 2, "ep_start": 5, "ep_end": 8},
            {"arc_no": 3, "ep_start": 9, "ep_end": 12},
        ]
        if key == "arcs"
        else None
    )

    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", return_value=app),
        patch.object(canary_script, "analyze_canary", return_value={"multi_stage_proof_scope_summary": {"status": "pass"}}),
    ):
        canary_script.run_canary("00_test_02", target_ep=4)

    assert observed["arcs"] == [{"arc_no": 1, "ep_start": 1, "ep_end": 4}]
    assert observed["plot_len"] == 1
    assert len(app.current_project.master_bible["MasterBible"]["plot_roadmap"]) == 3


def test_run_stage34_canary_rejects_target_ep_that_is_not_designed_arc_end():
    app = SimpleNamespace(
        _get_int_input=None,
        _one_stop_pipeline_frontier_lag=MagicMock(),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(
            db=MagicMock(),
            master_bible={"MasterBible": {"plot_roadmap": [{}, {}]}},
        ),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()
    app.current_project.db.load_anchor = MagicMock(
        return_value=[{"arc_no": 1, "ep_start": 1, "ep_end": 4}, {"arc_no": 2, "ep_start": 5, "ep_end": 8}]
    )

    with (
        patch.object(canary_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(canary_script, "_boot_app", return_value=app),
    ):
        try:
            canary_script.run_canary("00_test_02", target_ep=6)
        except ValueError as exc:
            assert "designed arc frontier ep_end" in str(exc)
        else:
            raise AssertionError("expected ValueError for non-frontier target_ep")

    app._one_stop_pipeline_frontier_lag.assert_not_called()


def test_analyze_stage34_canary_writes_summary(tmp_path):
    project_root = tmp_path / "projects" / "proof_refresh"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    stage4_summary = {
        "project_locator": "projects/proof_refresh",
        "project_root": str(project_root),
        "latest_session_id": "shared_sess",
        "current_session_sink_alignment_summary": {"status": "ok"},
        "rationale_contract_summary": {"status": "ok"},
        "companion_audit_summary": {"status": "ok"},
    }
    fake_db = MagicMock()
    fake_db.conn.execute.return_value.fetchall.return_value = [SimpleNamespace(session_id="shared_sess")]
    analyzer = MagicMock()
    analyzer.sink_alignment_summary.return_value = {"status": "ok"}

    with (
        patch.object(canary_script, "PROJECT_ROOT", tmp_path),
        patch.object(canary_script, "build_stage4_canary_summary", return_value=stage4_summary),
        patch.object(canary_script, "DBManager", return_value=fake_db),
        patch.object(canary_script, "FailureAnalyzer", return_value=analyzer),
        patch.object(canary_script, "latest_session_id_from_rows", return_value="shared_sess"),
    ):
        result = canary_script.analyze_canary("proof_refresh", target_ep=4)

    assert result["shared_session_id"] == "shared_sess"
    assert result["multi_stage_proof_scope_summary"]["status"] == "pass"
    summary_path = project_root / "logs" / "stage34_canary_summary.json"
    assert json.loads(summary_path.read_text(encoding="utf-8"))["shared_session_id"] == "shared_sess"
