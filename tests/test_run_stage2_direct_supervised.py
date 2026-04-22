import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import scripts.run_stage2_direct_supervised as direct_script


def test_run_direct_stage2_writes_summary_and_archives(tmp_path):
    project_root = tmp_path / "projects" / "gold"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)

    app = SimpleNamespace(
        _run_stage2_arc_async=MagicMock(),
        _stage2_orch=MagicMock(),
        ui=MagicMock(),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()

    with (
        patch.object(direct_script, "PROJECT_ROOT", tmp_path),
        patch.object(direct_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(direct_script, "_boot_app", return_value=app),
        patch.object(direct_script, "_load_arc_count", side_effect=[2, 5]),
        patch.object(
            direct_script,
            "safe_archive_benchmark_record",
            return_value={"status": "ok", "run_id": "archive-1"},
        ) as archive,
        patch.object(direct_script, "Stage2Context") as mock_ctx_cls,
    ):
        mock_ctx_cls.from_app.return_value = MagicMock()
        payload = direct_script.run_direct_stage2("gold", target_total_arcs=5)

    app._run_stage2_arc_async.assert_called_once_with(target_arc_count=3)
    app.pass_rate_monitor.save.assert_called_once()
    app._flush_audit_buffer.assert_called_once()
    archive.assert_called_once()
    assert payload["success"] is True
    assert payload["benchmark_archive"]["run_id"] == "archive-1"

    summary = json.loads((project_root / "logs" / "stage2_direct_supervised_result.json").read_text(encoding="utf-8"))
    assert summary["current_arcs_before"] == 2
    assert summary["current_arcs_after"] == 5
    assert summary["benchmark_archive"]["status"] == "ok"
