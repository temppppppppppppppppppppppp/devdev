import json
import sqlite3
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


def test_build_execution_plan_records_budget_caps():
    plan = harness.build_execution_plan(
        arc_count=5,
        seed_profile="00_20260314",
        batch_size=1,
        target_project="budgeted",
        trigger="5아크런",
        max_runtime_seconds=7200,
        max_total_tokens=4_000_000,
        max_total_cost_usd=12.5,
        max_project_bytes=500_000_000,
    )

    assert plan["budget_caps"] == {
        "max_runtime_seconds": 7200,
        "max_total_tokens": 4_000_000,
        "max_total_cost_usd": 12.5,
        "max_project_bytes": 500_000_000,
    }
    assert plan["run_id"]


def test_default_profile_points_to_available_stage0_seed_files():
    profile = harness.default_profile()

    assert (harness.PROJECT_ROOT / "bible" / profile.bible_file).is_file()
    assert (harness.PROJECT_ROOT / "treatments" / profile.roadmap_file).is_file()


def test_menu_choice_for_value_resolves_semantic_option():
    assert harness._menu_choice_for_value(("현대인", "원시인"), "원시인") == "2"


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


def test_classify_poll_transition_allows_recoverable_reject_glyph_tail():
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
    current["session_log_size"] = 120
    current["session_log_tail"] = ["❌ [Stage 4] Director REJECT: retrying with repair guidance"]

    status, idle = harness.classify_poll_transition(previous, current, 0)

    assert status == "progressing"
    assert idle == 0


def test_classify_poll_transition_treats_provider_response_wait_as_active():
    previous = {
        "process_exit_code": None,
        "process_alive": True,
        "session_log_tail": ["[DEBUG] [httpcore.http11] receive_response_headers.started request=<Request [b'POST']>"],
        "session_log_size": 221745,
        "blueprint_count": 1,
        "draft_count": 0,
        "stage3_attempts": 1,
        "stage4_attempts": 0,
        "director_stage3_rows": 1,
        "director_stage4_rows": 0,
        "runtime_audit_total_events": 3,
        "harness_phase": "frontier_running",
        "prompt_blocked": False,
    }
    current = dict(previous)

    status, idle = harness.classify_poll_transition(previous, current, 1)

    assert status == "provider_wait"
    assert idle == 0


def test_detect_provider_response_wait_clears_after_response_complete():
    assert (
        harness.detect_provider_response_wait(
            [
                "[DEBUG] [httpcore.http11] receive_response_headers.started request=<Request [b'POST']>",
                "[DEBUG] [httpcore.http11] receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [])",
            ]
        )
        is False
    )


def test_detect_budget_breach_reports_first_exceeded_cap():
    snapshot = {
        "runtime_elapsed_seconds": 61,
        "metrics_total_tokens": 10,
        "metrics_total_cost_usd": 0.5,
        "project_bytes": 100,
    }
    caps = harness.normalize_budget_caps(
        max_runtime_seconds=60,
        max_total_tokens=100,
        max_total_cost_usd=2.0,
        max_project_bytes=500,
    )

    breach = harness.detect_budget_breach(snapshot, caps)

    assert breach == {
        "exceeded": True,
        "kind": "runtime_seconds",
        "observed": 61.0,
        "cap": 60.0,
    }


def test_capture_poll_snapshot_surfaces_metrics_and_project_bytes(tmp_path):
    project_root = tmp_path / "projects" / "budget_snapshot"
    metrics_dir = project_root / "logs" / "metrics"
    metrics_dir.mkdir(parents=True)
    (project_root / "drafts").mkdir()
    (project_root / "drafts" / "ep_0001.txt").write_text("hello", encoding="utf-8")
    (metrics_dir / "metrics_20260426_010101.json").write_text(
        json.dumps({"session_id": "m1", "total_tokens": 123, "total_cost_usd": 0.456}, ensure_ascii=False),
        encoding="utf-8",
    )

    snapshot = harness.capture_poll_snapshot(project_root)

    assert snapshot["metrics_session_id"] == "m1"
    assert snapshot["metrics_total_tokens"] == 123
    assert snapshot["metrics_total_cost_usd"] == 0.456
    assert snapshot["project_bytes"] >= 5


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


def test_write_execution_ssot_mentions_terminal_watchdog_and_ctrl_break(tmp_path):
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
        "process_status": "success",
        "process_success": True,
        "objective_status": "success",
        "objective_success": True,
        "objective_root_cause": "",
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
    assert "hard runtime cap" in text
    assert "CTRL_BREAK / Ctrl+C first" in text
    assert "objective_status: success" in text
    assert "confidence: 95%" in text


def test_analyze_project_removes_stale_failure_digest_after_success(tmp_path):
    project_name = "auto_test_success_after_failure"
    logs_dir = tmp_path / "projects" / project_name / "logs"
    logs_dir.mkdir(parents=True)
    frontier_result = {
        "arcs_advanced": 1,
        "arcs_skipped": 0,
        "requested_arc_limit": 1,
        "requested_limit_hit": True,
        "stop_reason": "requested_arc_limit_reached",
    }
    (logs_dir / "auto_frontier_lag_worker_result.json").write_text(
        json.dumps(
            {
                "status": "success",
                "process_status": "success",
                "process_success": True,
                "objective_status": "success",
                "objective_success": True,
                "frontier_result": frontier_result,
                "arc_count": 1,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (logs_dir / "auto_frontier_lag_harness_manifest.json").write_text("{}", encoding="utf-8")
    (logs_dir / "runtime_audit_summary.json").write_text("{}", encoding="utf-8")
    (logs_dir / "pass_rate_monitor.json").write_text("{}", encoding="utf-8")
    (logs_dir / "auto_frontier_lag_poll_history.jsonl").write_text(
        json.dumps({"captured_at": "2026-03-14T12:00:00"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    stale_digest = logs_dir / "auto_frontier_lag_failure_digest.json"
    stale_digest.write_text('{"judgment":"failed"}', encoding="utf-8")
    project_root = tmp_path / "projects" / project_name
    (project_root / "project_data.db").write_text("", encoding="utf-8")

    class FakeConn:
        def execute(self, query):
            return SimpleNamespace(fetchall=MagicMock(return_value=[("sess-1",)]))

    fake_db = SimpleNamespace(conn=FakeConn(), close=MagicMock())
    fake_analyzer = SimpleNamespace(sink_alignment_summary=MagicMock(return_value={"status": "ok"}))

    with (
        patch.object(harness, "PROJECT_ROOT", tmp_path),
        patch.object(harness, "DBManager", return_value=fake_db),
        patch.object(harness, "FailureAnalyzer", return_value=fake_analyzer),
    ):
        payload = harness.analyze_project(project_name, arc_count=1)

    persisted = json.loads((logs_dir / "auto_frontier_lag_analysis.json").read_text(encoding="utf-8"))
    assert payload["judgment"] == "success"
    assert payload["strict_evidence_gaps"] == []
    assert persisted["ssot_path"] == payload["ssot_path"]
    assert not stale_digest.exists()


def test_analyze_project_keeps_failure_digest_when_strict_success_evidence_missing(tmp_path):
    project_name = "auto_test_missing_success_evidence"
    logs_dir = tmp_path / "projects" / project_name / "logs"
    logs_dir.mkdir(parents=True)
    frontier_result = {
        "arcs_advanced": 1,
        "arcs_skipped": 0,
        "requested_arc_limit": 1,
        "requested_limit_hit": True,
        "stop_reason": "requested_arc_limit_reached",
    }
    (logs_dir / "auto_frontier_lag_worker_result.json").write_text(
        json.dumps(
            {
                "status": "success",
                "process_status": "success",
                "process_success": True,
                "objective_status": "success",
                "objective_success": True,
                "frontier_result": frontier_result,
                "arc_count": 1,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (logs_dir / "auto_frontier_lag_harness_manifest.json").write_text("{}", encoding="utf-8")
    (logs_dir / "runtime_audit_summary.json").write_text("{}", encoding="utf-8")
    (logs_dir / "pass_rate_monitor.json").write_text("{}", encoding="utf-8")
    (logs_dir / "auto_frontier_lag_poll_history.jsonl").write_text(
        json.dumps({"captured_at": "2026-03-14T12:00:00"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    with patch.object(harness, "PROJECT_ROOT", tmp_path):
        payload = harness.analyze_project(project_name, arc_count=1)

    digest = json.loads((logs_dir / "auto_frontier_lag_failure_digest.json").read_text(encoding="utf-8"))
    assert payload["judgment"] == "failed"
    assert payload["root_cause"] == "strict_evidence_missing"
    assert "project_data_db_missing" in payload["strict_evidence_gaps"]
    assert digest["strict_evidence_gaps"] == payload["strict_evidence_gaps"]


def test_analyze_project_fails_stale_worker_result_run_id_mismatch(tmp_path):
    project_name = "auto_test_stale_worker_result"
    logs_dir = tmp_path / "projects" / project_name / "logs"
    logs_dir.mkdir(parents=True)
    frontier_result = {
        "arcs_advanced": 1,
        "arcs_skipped": 0,
        "requested_arc_limit": 1,
        "requested_limit_hit": True,
    }
    (logs_dir / "auto_frontier_lag_worker_result.json").write_text(
        json.dumps(
            {
                "run_id": "old-run",
                "status": "success",
                "process_status": "success",
                "process_success": True,
                "objective_status": "success",
                "objective_success": True,
                "frontier_result": frontier_result,
                "arc_count": 1,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (logs_dir / "auto_frontier_lag_harness_manifest.json").write_text(
        json.dumps({"run_id": "new-run"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (logs_dir / "runtime_audit_summary.json").write_text("{}", encoding="utf-8")
    (logs_dir / "pass_rate_monitor.json").write_text("{}", encoding="utf-8")
    (logs_dir / "auto_frontier_lag_poll_history.jsonl").write_text(
        json.dumps({"captured_at": "2026-03-14T12:00:00"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    with patch.object(harness, "PROJECT_ROOT", tmp_path):
        payload = harness.analyze_project(project_name, arc_count=1, expected_run_id="new-run")

    assert payload["judgment"] == "failed"
    assert payload["root_cause"] == "stale_worker_result_run_id_mismatch"
    assert payload["run_id_mismatch"] is True


def test_strict_success_artifact_gaps_require_drafts_and_settlement_packets(tmp_path):
    project_root = tmp_path / "projects" / "artifact_gap"
    (project_root / "drafts").mkdir(parents=True)
    (project_root / "drafts" / "ep_0001.txt").write_text("ok", encoding="utf-8")

    gaps = harness.derive_strict_success_evidence_gaps(
        project_root=project_root,
        frontier_result={"total_manuscripts": 2},
        boundary_reached=True,
        objective_success=True,
        stage3_attempts=1,
        stage4_attempts=1,
        stage3_summary={"status": "ok"},
        stage4_summary={"status": "ok"},
    )

    assert "settlement_packet_missing_or_empty:ep_0001" in gaps
    assert "draft_txt_missing_or_empty:ep_0002" in gaps
    assert "settlement_packet_missing_or_empty:ep_0002" in gaps


def test_strict_success_gaps_include_continuity_canary_review_required(tmp_path):
    project_root = tmp_path / "projects" / "continuity_canary_gap"
    project_root.mkdir(parents=True)
    (project_root / "project_data.db").write_text("", encoding="utf-8")

    gaps = harness.derive_strict_success_evidence_gaps(
        project_root=project_root,
        frontier_result={},
        boundary_reached=True,
        objective_success=True,
        stage3_attempts=1,
        stage4_attempts=1,
        stage3_summary={"status": "ok"},
        stage4_summary={"status": "ok"},
        continuity_canary_report={
            "status": "review_required",
            "finding_count": 2,
            "findings": [{"canary_id": "date_drift"}, {"canary_id": "location_drift"}],
        },
    )

    assert "continuity_canary_review_required:2" in gaps


def test_analyze_project_fails_success_when_continuity_canary_requires_review(tmp_path):
    project_name = "auto_test_continuity_canary_review"
    logs_dir = tmp_path / "projects" / project_name / "logs"
    logs_dir.mkdir(parents=True)
    frontier_result = {
        "arcs_advanced": 1,
        "arcs_skipped": 0,
        "requested_arc_limit": 1,
        "requested_limit_hit": True,
        "stop_reason": "requested_arc_limit_reached",
    }
    (logs_dir / "auto_frontier_lag_worker_result.json").write_text(
        json.dumps(
            {
                "status": "success",
                "process_status": "success",
                "process_success": True,
                "objective_status": "success",
                "objective_success": True,
                "frontier_result": frontier_result,
                "arc_count": 1,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (logs_dir / "auto_frontier_lag_harness_manifest.json").write_text("{}", encoding="utf-8")
    (logs_dir / "runtime_audit_summary.json").write_text("{}", encoding="utf-8")
    (logs_dir / "pass_rate_monitor.json").write_text("{}", encoding="utf-8")
    (logs_dir / "auto_frontier_lag_poll_history.jsonl").write_text(
        json.dumps({"captured_at": "2026-03-14T12:00:00"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (logs_dir / "continuity_canary_report.json").write_text(
        json.dumps(
            {
                "schema_version": "continuity-canary-v1",
                "status": "review_required",
                "finding_count": 1,
                "findings": [{"canary_id": "date_drift"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    project_root = tmp_path / "projects" / project_name
    (project_root / "project_data.db").write_text("", encoding="utf-8")

    class FakeConn:
        def execute(self, query):
            return SimpleNamespace(fetchall=MagicMock(return_value=[("sess-1",)]))

    fake_db = SimpleNamespace(conn=FakeConn(), close=MagicMock())
    fake_analyzer = SimpleNamespace(sink_alignment_summary=MagicMock(return_value={"status": "ok"}))

    with (
        patch.object(harness, "PROJECT_ROOT", tmp_path),
        patch.object(harness, "DBManager", return_value=fake_db),
        patch.object(harness, "FailureAnalyzer", return_value=fake_analyzer),
    ):
        payload = harness.analyze_project(project_name, arc_count=1)

    assert payload["judgment"] == "failed"
    assert payload["root_cause"] == "strict_evidence_missing"
    assert payload["continuity_canary_report"]["status"] == "review_required"
    assert "continuity_canary_review_required:1" in payload["strict_evidence_gaps"]


def test_terminate_process_tree_prefers_ctrl_break_when_available():
    process = MagicMock()
    process.poll.side_effect = [None, None, 0]

    with patch.object(harness.signal, "CTRL_BREAK_EVENT", 1, create=True), patch.object(harness.time, "sleep"):
        harness._terminate_process_tree(process)

    process.send_signal.assert_called_once_with(1)
    process.terminate.assert_not_called()


def test_run_harness_does_not_wait_full_poll_window_after_quick_worker_exit(tmp_path):
    class FakeProcess:
        def __init__(self):
            self.exit_code = None

        def poll(self):
            return self.exit_code

        def wait(self):
            return 0 if self.exit_code is None else self.exit_code

    process = FakeProcess()
    snapshots = [
        {"captured_at": "t0", "process_exit_code": None},
        {"captured_at": "t1", "process_exit_code": 0},
    ]
    sleeps: list[float] = []

    def fake_sleep(seconds):
        sleeps.append(seconds)
        process.exit_code = 0

    with (
        patch.object(harness, "PROJECT_ROOT", tmp_path),
        patch.object(harness, "build_execution_plan", return_value={"target_project": "auto_test_demo"}),
        patch.object(harness, "build_worker_command", return_value=["python", "worker"]),
        patch.object(harness.subprocess, "Popen", return_value=process),
        patch.object(harness, "capture_poll_snapshot", side_effect=snapshots),
        patch.object(harness, "_write_poll_history") as write_poll_history,
        patch.object(harness, "analyze_project", return_value={"judgment": "success"}),
        patch.object(harness.time, "sleep", side_effect=fake_sleep),
    ):
        payload = harness.run_harness(
            arc_count=10,
            seed_profile="00_20260314",
            batch_size=1,
            poll_interval_seconds=1800,
            target_project="",
            trigger="자동테스트 10아크런",
        )

    assert payload["process_exit_code"] == 0
    assert sleeps == [harness.PROCESS_CHECK_INTERVAL_SECONDS]
    assert write_poll_history.call_count >= 2


def test_run_harness_enforces_runtime_cap_without_waiting_poll_window(tmp_path):
    class FakeProcess:
        def __init__(self):
            self.exit_code = None

        def poll(self):
            return self.exit_code

        def wait(self):
            return -9 if self.exit_code is None else self.exit_code

    process = FakeProcess()
    snapshots = [
        {"captured_at": "t0", "process_exit_code": None},
        {"captured_at": "timeout", "process_exit_code": None},
        {"captured_at": "final", "process_exit_code": -9},
    ]
    sleeps: list[float] = []

    def fake_sleep(seconds):
        sleeps.append(seconds)

    def fake_terminate(proc):
        proc.exit_code = -9

    with (
        patch.object(harness, "PROJECT_ROOT", tmp_path),
        patch.object(
            harness, "build_execution_plan", return_value={"target_project": "auto_test_demo", "run_id": "run1"}
        ),
        patch.object(harness, "build_worker_command", return_value=["python", "worker"]),
        patch.object(harness.subprocess, "Popen", return_value=process),
        patch.object(harness, "capture_poll_snapshot", side_effect=snapshots),
        patch.object(harness, "_write_poll_history") as write_poll_history,
        patch.object(harness, "_terminate_process_tree", side_effect=fake_terminate) as terminate,
        patch.object(harness, "analyze_project", return_value={"judgment": "failed"}),
        patch.object(harness.time, "sleep", side_effect=fake_sleep),
        patch.object(harness.time, "monotonic", side_effect=[0.0, 0.0, 0.0, 5.1, 5.1]),
    ):
        payload = harness.run_harness(
            arc_count=10,
            seed_profile="00_20260314",
            batch_size=1,
            poll_interval_seconds=1800,
            target_project="",
            trigger="자동테스트 10아크런",
            max_runtime_seconds=5,
        )

    assert payload["watchdog_status"] == "failed"
    assert payload["termination_reason"] == "budget_runtime_seconds_exceeded"
    assert payload["process_exit_code"] == -9
    assert sleeps == [5.0]
    terminate.assert_called_once_with(process)
    assert write_poll_history.call_count >= 3


def test_apply_stage0_style_profile_absorbs_additional_pause_prompts(tmp_path):
    project_root = tmp_path / "projects" / "auto_test_style"
    style_file = project_root / "stage0_output" / "style_guide.json"
    fake_db = MagicMock()
    fake_db.load_anchor.return_value = {}
    prompt_values: list[str] = []

    def fake_stage0_extended(*, mode):
        assert mode == 5
        for _ in range(5):
            prompt_values.append(input("style replay prompt"))
        style_file.parent.mkdir(parents=True, exist_ok=True)
        style_file.write_text("{}", encoding="utf-8")

    app = SimpleNamespace(
        current_project=SimpleNamespace(paths=SimpleNamespace(root=project_root), db=fake_db),
        _stage_0_extended=fake_stage0_extended,
    )

    harness._apply_stage0_style_profile(app, harness.default_profile())

    assert prompt_values[:2] == ["y", "1"]
    assert prompt_values[2:] == ["", "", ""]
    assert style_file.exists()


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
        _shutdown_app=MagicMock(),
        memory=None,
    )

    with (
        patch.object(harness, "PROJECT_ROOT", tmp_path),
        patch.object(harness, "_boot_app", return_value=app),
        patch.object(harness, "_apply_stage0_existing_profile"),
        patch.object(harness, "_apply_stage0_style_profile"),
        patch.object(harness, "_close_app_handles") as close_handles,
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
        stage3_failure_policy="strict",
    )
    assert payload["status"] == "success"
    assert payload["process_status"] == "success"
    assert payload["objective_status"] == "success"
    worker_result = json.loads(
        (project_root / "logs" / "auto_frontier_lag_worker_result.json").read_text(encoding="utf-8")
    )
    assert worker_result["frontier_result"]["requested_limit_hit"] is True
    assert worker_result["stage3_failure_policy"] == "strict"
    app._shutdown_app.assert_called_once_with()
    close_handles.assert_not_called()


def test_objective_status_rejects_process_success_with_skipped_arc():
    frontier_result = {
        "arcs_advanced": 4,
        "arcs_skipped": 1,
        "requested_limit_hit": True,
        "stop_reason": "requested_arc_limit_reached",
    }

    objective = harness.derive_objective_status(frontier_result, arc_count=5)
    root_cause = harness.derive_root_cause(
        worker_result={"status": "success"},
        watchdog_status="progressing",
        stage3_summary={"status": "ok"},
        stage4_summary={"status": "ok"},
        boundary_reached=True,
        process_success=True,
        objective_success=objective["objective_success"],
        objective_root_cause=objective["objective_root_cause"],
    )
    judgment = harness.derive_judgment(
        worker_result={"status": "success"},
        watchdog_status="progressing",
        boundary_reached=True,
        stage3_summary={"status": "ok"},
        stage4_summary={"status": "ok"},
        root_cause=root_cause,
        process_success=True,
        objective_success=objective["objective_success"],
    )

    assert objective == {
        "objective_status": "failed",
        "objective_success": False,
        "objective_root_cause": "stage3_arc_skipped",
    }
    assert root_cause == "stage3_arc_skipped"
    assert judgment == "failed"


def test_derive_root_cause_prefers_budget_termination_reason():
    root_cause = harness.derive_root_cause(
        worker_result={"status": "success"},
        watchdog_status="failed",
        termination_reason="budget_total_cost_usd_exceeded",
        stage3_summary={"status": "ok"},
        stage4_summary={"status": "ok"},
        boundary_reached=True,
        process_success=True,
        objective_success=True,
    )

    assert root_cause == "budget_total_cost_usd_exceeded"


def _build_reuse_db(*, failed: bool):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE stage_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage INTEGER,
            ep_num INTEGER,
            arc_num INTEGER,
            attempt_num INTEGER,
            verdict TEXT,
            failure_category TEXT,
            reject_reason TEXT,
            primary_failure_layer TEXT
        )
        """
    )
    if failed:
        conn.execute(
            """
            INSERT INTO stage_attempts
                (stage, ep_num, arc_num, attempt_num, verdict, failure_category, reject_reason, primary_failure_layer)
            VALUES (3, 1, 1, 1, 'FAILED', 'binding', 'date mismatch', 'semantic')
            """
        )
    conn.commit()
    return conn


def test_reuse_existing_project_refuses_failed_stage_state(tmp_path):
    project_root = tmp_path / "projects" / "reuse_failed"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    conn = _build_reuse_db(failed=True)

    def load_anchor(key):
        if key == "bible":
            return {"MasterBible": {"plot_roadmap": [{"block_no": 1}]}}
        if key == "style_guide":
            return {"tone": "sharp"}
        if key == "arcs":
            return []
        return {}

    fake_db = SimpleNamespace(load_anchor=MagicMock(side_effect=load_anchor), conn=conn)
    app = SimpleNamespace(
        current_project=SimpleNamespace(paths=SimpleNamespace(root=project_root), db=fake_db),
        _resolve_one_stop_frontier_lag_plan=MagicMock(
            return_value={"frontier_ep_start": 1, "stage3_target": 2, "stage4_target": 1}
        ),
        _shutdown_app=MagicMock(),
        memory=None,
    )

    with (
        patch.object(harness, "PROJECT_ROOT", tmp_path),
        patch.object(harness, "_boot_app", return_value=app),
        patch.object(harness, "_apply_stage0_existing_profile"),
        patch.object(harness, "_apply_stage0_style_profile"),
    ):
        payload = harness.run_worker(
            target_project="reuse_failed",
            arc_count=1,
            seed_profile="00_20260314",
            batch_size=1,
            reuse_existing_project=True,
        )

    manifest = json.loads(
        (project_root / "logs" / "auto_frontier_lag_harness_manifest.json").read_text(encoding="utf-8")
    )
    assert payload["status"] == "failed"
    assert "reuse refused" in payload["error"]
    assert manifest["reuse_failed_state_detected"] is True
    assert manifest["reuse_allowed"] is False


def test_reuse_existing_project_reset_guard_allows_after_reset(tmp_path):
    project_root = tmp_path / "projects" / "reuse_reset"
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    (project_root / "drafts").mkdir(parents=True, exist_ok=True)
    (project_root / "drafts" / "ep_0001.txt").write_text("stale manuscript", encoding="utf-8")
    (project_root / "drafts" / "ep_0001.settlement.json").write_text("{}", encoding="utf-8")
    (project_root / "drafts" / "emergency_ep_0001.txt").write_text("emergency stale", encoding="utf-8")
    (project_root / "plans" / "blueprints").mkdir(parents=True, exist_ok=True)
    (project_root / "plans" / "blueprints" / "blueprint_0001.txt").write_text("bp stale", encoding="utf-8")
    (project_root / "plans" / "blueprints" / "ep_0001.json").write_text("{}", encoding="utf-8")
    stale_stage3 = project_root / "logs" / "artifacts" / "stage3" / "ep_0001"
    stale_stage4 = project_root / "logs" / "artifacts" / "stage4" / "ep_0001"
    stale_stage3.mkdir(parents=True, exist_ok=True)
    stale_stage4.mkdir(parents=True, exist_ok=True)
    (stale_stage3 / "final_blueprint__x.json").write_text("{}", encoding="utf-8")
    (stale_stage4 / "patched_after_fix__x.txt").write_text("stale", encoding="utf-8")
    conn = _build_reuse_db(failed=True)

    def load_anchor(key):
        if key == "bible":
            return {"MasterBible": {"plot_roadmap": [{"block_no": 1}]}}
        if key == "style_guide":
            return {"tone": "sharp"}
        if key == "arcs":
            return []
        return {}

    def reset_after(ep):
        conn.execute("DELETE FROM stage_attempts WHERE stage IN (3, 4) AND ep_num >= ?", (ep,))
        conn.commit()

    fake_db = SimpleNamespace(
        load_anchor=MagicMock(side_effect=load_anchor),
        conn=conn,
        reset_after=MagicMock(side_effect=reset_after),
    )
    app = SimpleNamespace(
        current_project=SimpleNamespace(paths=SimpleNamespace(root=project_root), db=fake_db),
        pass_rate_monitor=MagicMock(),
        _flush_audit_buffer=MagicMock(),
        _one_stop_pipeline_frontier_lag=MagicMock(
            return_value={
                "arcs_advanced": 1,
                "arcs_skipped": 0,
                "requested_limit_hit": True,
                "stop_reason": "requested_arc_limit_reached",
            }
        ),
        _resolve_one_stop_frontier_lag_plan=MagicMock(
            return_value={"frontier_ep_start": 1, "stage3_target": 2, "stage4_target": 1}
        ),
        _shutdown_app=MagicMock(),
        memory=None,
    )

    with (
        patch.object(harness, "PROJECT_ROOT", tmp_path),
        patch.object(harness, "_boot_app", return_value=app),
        patch.object(harness, "_ensure_pass_rate_monitor"),
    ):
        payload = harness.run_worker(
            target_project="reuse_reset",
            arc_count=1,
            seed_profile="00_20260314",
            batch_size=1,
            reuse_existing_project=True,
            reuse_reset_after_ep=1,
        )

    manifest = json.loads(
        (project_root / "logs" / "auto_frontier_lag_harness_manifest.json").read_text(encoding="utf-8")
    )
    fake_db.reset_after.assert_called_once_with(1)
    assert payload["status"] == "success"
    assert manifest["reuse_reset_applied"] is True
    assert manifest["reuse_allowed"] is True
    assert manifest["reuse_post_failed_state_count"] == 0
    assert manifest["reuse_reset_filesystem_archive_applied"] is True
    assert manifest["reuse_reset_filesystem_archived_count"] == 7
    assert not (project_root / "drafts" / "ep_0001.txt").exists()
    assert not (project_root / "drafts" / "emergency_ep_0001.txt").exists()
    assert not (project_root / "plans" / "blueprints" / "blueprint_0001.txt").exists()
    assert not stale_stage3.exists()
    archive_root = project_root / manifest["reuse_reset_filesystem_archive_root"]
    assert (archive_root / "drafts" / "ep_0001.txt").exists()
    assert (archive_root / "plans" / "blueprints" / "blueprint_0001.txt").exists()
    assert (archive_root / "logs" / "artifacts" / "stage4" / "ep_0001" / "patched_after_fix__x.txt").exists()


# ── Soak Profile Override Contract ───────────────────────────────────────


def test_default_soak_profile_uses_flash_and_reduced_lengths(monkeypatch):
    """default_soak_profile returns a well-formed profile with all-flash + lower lengths."""
    monkeypatch.delenv("GEULDOBI_FORCE_GOOGLE_MODEL", raising=False)

    soak = harness.default_soak_profile()
    assert soak.stage2_model is not None
    assert "flash" in soak.stage2_model.lower()
    assert soak.stage4_model is not None
    assert "flash" in soak.stage4_model.lower()
    assert soak.manuscript_min_length is not None
    assert soak.manuscript_min_length < 4000
    assert soak.manuscript_target_length is not None
    assert soak.manuscript_target_length < 5000
    assert soak.heavy_path_toggles.get("post_pass_advisories") is False


def test_default_soak_profile_respects_forced_google_model(monkeypatch):
    monkeypatch.setenv("GEULDOBI_PROVIDER_MODE", "vertex_ai")
    monkeypatch.setenv("GEULDOBI_FORCE_GOOGLE_MODEL", "gemini-3.1-pro-preview")

    soak = harness.default_soak_profile()

    assert soak.stage2_model == "vertexai:gemini-3.1-pro-preview"
    assert soak.stage4_model == "vertexai:gemini-3.1-pro-preview"


def test_resolve_soak_profile_returns_none_for_empty():
    assert harness.resolve_soak_profile(None) is None
    assert harness.resolve_soak_profile("") is None


def test_resolve_soak_profile_returns_profile_for_soak():
    soak = harness.resolve_soak_profile("soak")
    assert isinstance(soak, harness.SoakProfile)
    assert soak.stage2_model is not None


def test_resolve_soak_profile_rejects_unknown():
    import pytest

    with pytest.raises(ValueError, match="unknown soak profile"):
        harness.resolve_soak_profile("nonexistent")


def test_apply_soak_overrides_none_is_noop():
    """When soak is None, apply_soak_overrides yields without side effects."""
    from modules.core.constants import AIModels, ManuscriptLimits

    orig_s2 = AIModels.STAGE2_MAIN_MODEL
    orig_s4 = AIModels.STAGE4_FIXED_WRITER_MODEL
    orig_min = int(ManuscriptLimits.MIN_LENGTH)
    orig_target = int(ManuscriptLimits.TARGET_LENGTH)

    with harness.apply_soak_overrides(None):
        assert AIModels.STAGE2_MAIN_MODEL == orig_s2
        assert AIModels.STAGE4_FIXED_WRITER_MODEL == orig_s4
        assert int(ManuscriptLimits.MIN_LENGTH) == orig_min
        assert int(ManuscriptLimits.TARGET_LENGTH) == orig_target


def test_apply_soak_overrides_patches_and_restores():
    """Overrides take effect inside the context and are fully restored on exit."""
    from modules.core.constants import AIModels, ManuscriptLimits

    orig_s2 = AIModels.STAGE2_MAIN_MODEL
    orig_s4 = AIModels.STAGE4_FIXED_WRITER_MODEL
    orig_min = int(ManuscriptLimits.MIN_LENGTH)
    orig_target = int(ManuscriptLimits.TARGET_LENGTH)

    soak = harness.SoakProfile(
        stage2_model="test-flash-model",
        stage4_model="test-flash-model",
        manuscript_min_length=800,
        manuscript_target_length=1200,
        heavy_path_toggles={},
    )

    with harness.apply_soak_overrides(soak):
        assert AIModels.STAGE2_MAIN_MODEL == "test-flash-model"
        assert AIModels.STAGE4_FIXED_WRITER_MODEL == "test-flash-model"
        assert int(ManuscriptLimits.MIN_LENGTH) == 800
        assert int(ManuscriptLimits.TARGET_LENGTH) == 1200

    # Restored after exit
    assert AIModels.STAGE2_MAIN_MODEL == orig_s2
    assert AIModels.STAGE4_FIXED_WRITER_MODEL == orig_s4
    assert int(ManuscriptLimits.MIN_LENGTH) == orig_min
    assert int(ManuscriptLimits.TARGET_LENGTH) == orig_target


def test_apply_soak_overrides_heavy_path_toggle_disables_post_pass_advisories():
    """post_pass_advisories=False replaces the method with a no-op inside the context."""
    from modules.core.stage4_post_pass_runtime import Stage4PostPassRuntime

    original_method = Stage4PostPassRuntime._run_post_pass_advisories

    soak = harness.SoakProfile(
        heavy_path_toggles={"post_pass_advisories": False},
    )

    with harness.apply_soak_overrides(soak):
        # Method should be replaced with a no-op
        assert Stage4PostPassRuntime._run_post_pass_advisories is not original_method

    # Restored after exit
    assert Stage4PostPassRuntime._run_post_pass_advisories is original_method


def test_apply_soak_overrides_rejects_unknown_toggle():
    """Unknown toggle names raise ValueError."""
    import pytest

    soak = harness.SoakProfile(heavy_path_toggles={"nonexistent_toggle": False})
    with pytest.raises(ValueError, match="unknown heavy-path toggle"):
        with harness.apply_soak_overrides(soak):
            pass


def test_build_worker_command_includes_soak_profile_flag():
    cmd = harness.build_worker_command(
        target_project="test_proj",
        arc_count=3,
        seed_profile="00_20260314",
        batch_size=1,
        soak_profile_name="soak",
    )
    assert "--soak-profile" in cmd
    idx = cmd.index("--soak-profile")
    assert cmd[idx + 1] == "soak"


def test_build_worker_command_omits_soak_profile_when_empty():
    cmd = harness.build_worker_command(
        target_project="test_proj",
        arc_count=3,
        seed_profile="00_20260314",
        batch_size=1,
    )
    assert "--soak-profile" not in cmd


def test_build_execution_plan_includes_soak_profile_when_provided():
    soak = harness.default_soak_profile()
    plan = harness.build_execution_plan(
        arc_count=3,
        seed_profile="00_20260314",
        batch_size=1,
        target_project="test_proj",
        trigger="",
        soak_profile=soak,
    )
    assert "soak_profile" in plan
    assert plan["soak_profile"]["manuscript_min_length"] == soak.manuscript_min_length


def test_build_execution_plan_omits_soak_profile_when_none():
    plan = harness.build_execution_plan(
        arc_count=3,
        seed_profile="00_20260314",
        batch_size=1,
        target_project="test_proj",
        trigger="",
    )
    assert "soak_profile" not in plan
