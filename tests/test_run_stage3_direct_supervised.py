import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import scripts.run_stage3_direct_supervised as direct_script


def test_run_direct_stage3_writes_summary_and_archives(tmp_path):
    project_root = tmp_path / "projects" / "gold"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)

    app = SimpleNamespace(
        ui=MagicMock(),
        _stage3_orch=MagicMock(),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        memory=None,
        current_project=SimpleNamespace(db=MagicMock()),
    )
    app.current_project.db.conn = MagicMock()
    app.current_project.db.close = MagicMock()
    app._stage3_orch.stage_3_batch_blueprinting.return_value = {"success_count": 3, "fail_count": 0}

    with (
        patch.object(direct_script, "PROJECT_ROOT", tmp_path),
        patch.object(direct_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(direct_script, "_boot_app", return_value=app),
        patch.object(direct_script, "_load_latest_blueprint_ep", return_value=16),
        patch.object(
            direct_script,
            "safe_archive_benchmark_record",
            return_value={"status": "ok", "run_id": "archive-3"},
        ) as archive,
        patch.object(direct_script, "Stage3Context") as mock_ctx_cls,
    ):
        mock_ctx_cls.from_app.return_value = MagicMock()
        payload = direct_script.run_direct_stage3("gold", target_ep=16, operational_attempt_cap=5)

    app.pass_rate_monitor.save.assert_called_once()
    app._flush_audit_buffer.assert_called_once()
    archive.assert_called_once()
    assert payload["success"] is True
    assert payload["latest_blueprint_ep"] == 16
    assert payload["benchmark_archive"]["run_id"] == "archive-3"

    summary = json.loads((project_root / "logs" / "stage3_direct_supervised_result.json").read_text(encoding="utf-8"))
    assert summary["latest_blueprint_ep"] == 16
    assert summary["benchmark_archive"]["status"] == "ok"
