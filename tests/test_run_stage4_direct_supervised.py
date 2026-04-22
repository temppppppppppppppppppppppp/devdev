import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import scripts.run_stage4_direct_supervised as direct_script


def test_run_direct_stage4_writes_summary_and_archives(tmp_path):
    project_root = tmp_path / "projects" / "gold"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)

    app = SimpleNamespace(
        ui=MagicMock(),
        _stage_4_v2_chief_writer=MagicMock(),
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
        patch.object(direct_script, "_load_latest_written_ep", side_effect=[3, 5]),
        patch.object(direct_script, "_load_runtime_audit_tag", return_value="stage4_complete"),
        patch.object(
            direct_script,
            "safe_archive_benchmark_record",
            return_value={"status": "ok", "run_id": "archive-4"},
        ) as archive,
    ):
        payload = direct_script.run_direct_stage4("gold", target_ep=5)

    app._stage_4_v2_chief_writer.assert_called_once_with(limit_mode=False, target_ep=5, skip_pause=True)
    app.pass_rate_monitor.save.assert_called_once()
    app._flush_audit_buffer.assert_called_once()
    archive.assert_called_once()
    assert payload["success"] is True
    assert payload["runtime_audit_tag"] == "stage4_complete"
    assert payload["benchmark_archive"]["run_id"] == "archive-4"

    summary = json.loads((project_root / "logs" / "stage4_direct_supervised_result.json").read_text(encoding="utf-8"))
    assert summary["latest_written_ep_before"] == 3
    assert summary["latest_written_ep_after"] == 5
    assert summary["benchmark_archive"]["status"] == "ok"


def test_run_direct_stage4_can_skip_archive(tmp_path):
    project_root = tmp_path / "projects" / "gold"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)

    app = SimpleNamespace(
        ui=MagicMock(),
        _stage_4_v2_chief_writer=MagicMock(),
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
        patch.object(direct_script, "_load_latest_written_ep", side_effect=[3, 4]),
        patch.object(direct_script, "_load_runtime_audit_tag", return_value="stage3_complete"),
        patch.object(direct_script, "safe_archive_benchmark_record") as archive,
    ):
        payload = direct_script.run_direct_stage4("gold", target_ep=5, archive_enabled=False)

    archive.assert_not_called()
    assert "benchmark_archive" not in payload
    summary = json.loads((project_root / "logs" / "stage4_direct_supervised_result.json").read_text(encoding="utf-8"))
    assert "benchmark_archive" not in summary
