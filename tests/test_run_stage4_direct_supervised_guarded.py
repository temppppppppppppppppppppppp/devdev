import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import scripts.run_stage4_direct_supervised_guarded as guarded_script


class _FakeProc:
    def __init__(self, wait_results):
        self._wait_results = list(wait_results)
        self.returncode = None
        self.terminated = False
        self.killed = False
        self.stdout = None
        self.stderr = None

    def wait(self, timeout=None):
        if not self._wait_results:
            return self.returncode
        result = self._wait_results.pop(0)
        if isinstance(result, BaseException):
            raise result
        self.returncode = result
        return result

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True
        self.returncode = 1

    def poll(self):
        return self.returncode


def _make_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "projects" / "gold"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    (project_root / "project_data.db").write_bytes(b"db")
    return project_root


def test_run_guarded_stage4_archives_completed_child_run(tmp_path):
    project_root = _make_project(tmp_path)
    (project_root / "logs" / "stage4_direct_supervised_result.json").write_text(
        json.dumps(
            {
                "project": "gold",
                "project_root": str(project_root),
                "target_ep": 10,
                "latest_written_ep_before": 3,
                "latest_written_ep_after": 10,
                "runtime_audit_tag": "stage4_complete",
                "success": True,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with (
        patch.object(guarded_script, "PROJECT_ROOT", tmp_path),
        patch.object(guarded_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(guarded_script, "_capture_stage4_baseline", return_value=12),
        patch.object(guarded_script, "_launch_direct_stage4_child", return_value=_FakeProc([0])),
        patch.object(guarded_script, "_load_latest_written_ep", side_effect=[3, 10]),
        patch.object(guarded_script, "_load_runtime_audit_tag", return_value="stage4_complete"),
        patch.object(
            guarded_script,
            "safe_archive_benchmark_record",
            return_value={"status": "ok", "run_id": "guarded-archive"},
        ) as archive,
    ):
        payload = guarded_script.run_guarded_stage4(
            "gold",
            target_ep=10,
            max_attempts=5,
            poll_interval_seconds=300,
        )

    archive.assert_called_once()
    assert archive.call_args.kwargs["status"] == "completed"
    assert payload["success"] is True
    assert payload["terminated_by_monitor"] is False
    assert payload["benchmark_archive"]["run_id"] == "guarded-archive"
    assert payload["child_exit_code"] == 0

    guarded_summary = json.loads(
        (project_root / "logs" / "stage4_direct_supervised_guarded_result.json").read_text(encoding="utf-8")
    )
    assert guarded_summary["monitor_policy"]["max_attempts"] == 5
    assert guarded_summary["benchmark_archive"]["status"] == "ok"


def test_run_guarded_stage4_terminates_when_attempt_limit_is_exceeded(tmp_path):
    project_root = _make_project(tmp_path)

    timeout = subprocess.TimeoutExpired(cmd="stage4", timeout=300)

    with (
        patch.object(guarded_script, "PROJECT_ROOT", tmp_path),
        patch.object(guarded_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(guarded_script, "_capture_stage4_baseline", return_value=20),
        patch.object(guarded_script, "_launch_direct_stage4_child", return_value=_FakeProc([timeout])),
        patch.object(
            guarded_script,
            "_get_stream_monitor_snapshot",
            return_value={"latest_round_seen": 0, "latest_round_total": 10},
        ),
        patch.object(guarded_script, "_load_stage4_attempt_summary", return_value={"ep_num": 4, "max_attempt_num": 6}),
        patch.object(guarded_script, "_terminate_process", return_value=("terminate", 1)) as terminate,
        patch.object(guarded_script, "_load_latest_written_ep", side_effect=[3, 3]),
        patch.object(guarded_script, "_load_runtime_audit_tag", return_value="stage3_complete"),
        patch.object(guarded_script.time, "monotonic", side_effect=[0, 1]),
        patch.object(
            guarded_script,
            "safe_archive_benchmark_record",
            return_value={"status": "ok", "run_id": "guarded-failure"},
        ) as archive,
    ):
        payload = guarded_script.run_guarded_stage4(
            "gold",
            target_ep=10,
            max_attempts=5,
            poll_interval_seconds=1,
        )

    terminate.assert_called_once()
    archive.assert_called_once()
    assert archive.call_args.kwargs["status"] == "operational_failure"
    assert payload["success"] is False
    assert payload["terminated_by_monitor"] is True
    assert payload["terminated_ep"] == 4
    assert payload["terminated_attempt_num"] == 6

    summary = json.loads((project_root / "logs" / "stage4_direct_supervised_result.json").read_text(encoding="utf-8"))
    assert summary["termination_reason"] == "stage4_attempt_limit_exceeded"
    assert summary["benchmark_archive"]["run_id"] == "guarded-failure"


def test_run_guarded_stage4_terminates_when_round_six_starts(tmp_path):
    project_root = _make_project(tmp_path)

    timeout = subprocess.TimeoutExpired(cmd="stage4", timeout=2)

    with (
        patch.object(guarded_script, "PROJECT_ROOT", tmp_path),
        patch.object(guarded_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(guarded_script, "_capture_stage4_baseline", return_value=20),
        patch.object(guarded_script, "_launch_direct_stage4_child", return_value=_FakeProc([timeout])),
        patch.object(
            guarded_script,
            "_get_stream_monitor_snapshot",
            return_value={"latest_round_seen": 6, "latest_round_total": 10},
        ),
        patch.object(guarded_script, "_terminate_process", return_value=("terminate", 1)) as terminate,
        patch.object(guarded_script, "_load_latest_written_ep", side_effect=[3, 3]),
        patch.object(guarded_script, "_load_runtime_audit_tag", return_value="stage3_complete"),
        patch.object(
            guarded_script,
            "safe_archive_benchmark_record",
            return_value={"status": "ok", "run_id": "guarded-round-failure"},
        ) as archive,
    ):
        payload = guarded_script.run_guarded_stage4(
            "gold",
            target_ep=10,
            max_attempts=5,
            poll_interval_seconds=300,
        )

    terminate.assert_called_once()
    archive.assert_called_once()
    assert archive.call_args.kwargs["status"] == "operational_failure"
    assert payload["success"] is False
    assert payload["termination_reason"] == "stage4_round_limit_exceeded"
    assert payload["terminated_attempt_num"] == 6


def test_run_guarded_stage4_fallback_does_not_treat_stale_stage4_complete_tag_as_success(tmp_path):
    project_root = _make_project(tmp_path)

    with (
        patch.object(guarded_script, "PROJECT_ROOT", tmp_path),
        patch.object(guarded_script, "_load_project_genre", return_value={"type": "investment", "name": "investment"}),
        patch.object(guarded_script, "_capture_stage4_baseline", return_value=12),
        patch.object(guarded_script, "_launch_direct_stage4_child", return_value=_FakeProc([0])),
        patch.object(guarded_script, "_load_latest_written_ep", side_effect=[3, 4]),
        patch.object(guarded_script, "_load_runtime_audit_tag", return_value="stage4_complete"),
        patch.object(
            guarded_script,
            "safe_archive_benchmark_record",
            return_value={"status": "ok", "run_id": "guarded-partial"},
        ) as archive,
    ):
        payload = guarded_script.run_guarded_stage4(
            "gold",
            target_ep=10,
            max_attempts=5,
            poll_interval_seconds=300,
        )

    assert payload["success"] is False
    archive.assert_called_once()
    assert archive.call_args.kwargs["status"] == "partial"
    summary = json.loads(
        (project_root / "logs" / "stage4_direct_supervised_guarded_result.json").read_text(encoding="utf-8")
    )
    assert summary["success"] is False
    assert summary["runtime_audit_tag"] == "stage4_complete"


def test_launch_direct_stage4_child_pins_utf8_pipe_io():
    with patch.object(guarded_script.subprocess, "Popen") as popen:
        guarded_script._launch_direct_stage4_child("gold", target_ep=15)

    popen.assert_called_once()
    assert popen.call_args.args[0] == [
        sys.executable,
        str(guarded_script.PROJECT_ROOT / "scripts" / "run_stage4_direct_supervised.py"),
        "run",
        "--project",
        "gold",
        "--target-ep",
        "15",
        "--skip-benchmark-archive",
    ]
    assert popen.call_args.kwargs["text"] is True
    assert popen.call_args.kwargs["encoding"] == "utf-8"
    assert popen.call_args.kwargs["errors"] == "replace"
    assert popen.call_args.kwargs["env"]["PYTHONIOENCODING"] == "utf-8"
