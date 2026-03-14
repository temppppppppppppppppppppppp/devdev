import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import scripts.run_auto_frontier_lag_harness as harness


def test_parse_arc_count_from_trigger_extracts_requested_arc_target():
    assert harness.parse_arc_count_from_trigger("자동테스트 10아크런") == 10
    assert harness.parse_arc_count_from_trigger("20아크 Frontier Lag 테스트") == 20
    assert harness.parse_arc_count_from_trigger("그냥 실행") is None


def test_build_worker_command_targets_same_script_and_has_no_timeout_flag():
    command = harness.build_worker_command(
        target_project="auto_test_20260314_120000_00_20260314_10arc",
        arc_count=10,
        seed_profile="00_20260314",
        batch_size=1,
    )

    assert command[0] == harness.sys.executable
    assert Path(command[1]).name == "run_auto_frontier_lag_harness.py"
    assert "worker" in command
    assert "--arc-count" in command
    assert "--timeout" not in command


def test_classify_poll_transition_marks_stalled_after_two_idle_windows():
    previous = {
        "process_exit_code": None,
        "process_alive": True,
        "session_log_tail": [],
        "session_log_size": 100,
        "blueprint_count": 3,
        "draft_count": 1,
        "stage3_attempts": 2,
        "stage4_attempts": 1,
        "director_stage3_rows": 2,
        "director_stage4_rows": 1,
        "runtime_audit_total_events": 4,
        "harness_phase": "frontier_running",
        "prompt_blocked": False,
    }
    current = dict(previous)

    status, idle = harness.classify_poll_transition(previous, current, 0)
    assert status == "stall-candidate"
    assert idle == 1

    status, idle = harness.classify_poll_transition(previous, current, idle)
    assert status == "stalled"
    assert idle == 2


def test_run_three_pass_audit_only_finalizes_success_at_95():
    audit = harness.run_three_pass_audit(
        worker_result={"status": "success"},
        boundary_reached=True,
        stage3_summary={"status": "ok"},
        stage4_summary={"status": "ok"},
        judgment="success",
        root_cause="",
        poll_history=[{"captured_at": "2026-03-14T12:00:00"}],
    )

    assert audit["confidence"] == 95
    assert audit["finalized"] is True

    degraded = harness.run_three_pass_audit(
        worker_result={"status": "success"},
        boundary_reached=False,
        stage3_summary={"status": "ok"},
        stage4_summary={"status": "ok"},
        judgment="failed",
        root_cause="requested_arc_boundary_not_reached",
        poll_history=[{"captured_at": "2026-03-14T12:00:00"}],
    )

    assert degraded["confidence"] < 95
    assert degraded["finalized"] is False


def test_write_execution_ssot_mentions_terminal_watchdog(tmp_path):
    analysis = {
        "generated_at": "2026-03-14T12:00:00",
        "project_locator": "projects/auto_test_demo",
        "judgment": "success",
        "root_cause": "",
        "watchdog_status": "progressing",
        "shared_session_id": "sess-1",
        "arc_count": 10,
        "poll_count": 4,
        "poll_history_path": "projects/auto_test_demo/logs/auto_frontier_lag_poll_history.jsonl",
        "worker_status": "success",
        "boundary_reached": True,
        "pass_rate_monitor_exists": True,
        "stage3_current_session_sink_alignment_summary": {"status": "ok"},
        "stage4_current_session_sink_alignment_summary": {"status": "ok"},
        "three_pass_audit": {
            "passes": {
                "pass1_fact_extraction": True,
                "pass2_contradiction_check": True,
                "pass3_decision_audit": True,
            },
            "confidence": 95,
            "finalized": True,
        },
    }

    with patch.object(harness, "PROJECT_ROOT", tmp_path):
        path = harness.write_execution_ssot(analysis)

    text = path.read_text(encoding="utf-8")
    assert "terminal-owned watchdog" in text
    assert "no hard process timeout" in text
    assert "confidence: 95%" in text


def test_run_worker_calls_frontier_with_requested_arc_limit_and_writes_result(tmp_path):
    project_root = tmp_path / "projects" / "auto_test_20260314_120000_00_20260314_10arc"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    fake_db = MagicMock()
    fake_db.load_anchor.side_effect = [{"MasterBible": {"plot_roadmap": [{"block_no": 1}]}}, {"tone": "sharp"}]
    fake_db.conn = MagicMock()
    fake_db.close = MagicMock()
    app = SimpleNamespace(
        current_project=SimpleNamespace(paths=SimpleNamespace(root=project_root), db=fake_db),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        _one_stop_pipeline_frontier_lag=MagicMock(
            return_value={
                "arcs_advanced": 10,
                "requested_limit_hit": True,
                "stop_reason": "requested_arc_limit_reached",
            }
        ),
        memory=None,
    )

    with (
        patch.object(harness, "PROJECT_ROOT", tmp_path),
        patch.object(harness, "_boot_app", return_value=app),
        patch.object(harness, "_apply_stage0_existing_profile"),
        patch.object(harness, "_apply_stage0_style_profile"),
        patch.object(harness, "_close_app_handles"),
    ):
        payload = harness.run_worker(
            target_project="auto_test_20260314_120000_00_20260314_10arc",
            arc_count=10,
            seed_profile="00_20260314",
            batch_size=1,
        )

    app._one_stop_pipeline_frontier_lag.assert_called_once_with(
        max_arc_advances=10,
        batch_size_override=1,
        wait_for_menu_return=False,
    )
    assert payload["status"] == "success"
    worker_result = json.loads(
        (project_root / "logs" / "auto_frontier_lag_worker_result.json").read_text(encoding="utf-8")
    )
    assert worker_result["frontier_result"]["requested_limit_hit"] is True
