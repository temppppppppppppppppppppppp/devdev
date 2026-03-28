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
    assert "CTRL_BREAK / Ctrl+C first" in text
    assert "confidence: 95%" in text


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
        patch.object(harness, "_write_poll_history"),
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
    )
    assert payload["status"] == "success"
    worker_result = json.loads(
        (project_root / "logs" / "auto_frontier_lag_worker_result.json").read_text(encoding="utf-8")
    )
    assert worker_result["frontier_result"]["requested_limit_hit"] is True
    app._shutdown_app.assert_called_once_with()
    close_handles.assert_not_called()


# ── Soak Profile Override Contract ───────────────────────────────────────


def test_default_soak_profile_uses_flash_and_reduced_lengths():
    """default_soak_profile returns a well-formed profile with all-flash + lower lengths."""
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
