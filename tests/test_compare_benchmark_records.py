import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


INDEX_FIELDS = [
    "run_id",
    "recorded_at",
    "project_name",
    "project_locator",
    "lane",
    "target_ep",
    "status",
    "runtime_audit_tag",
    "latest_session_id",
    "git_branch",
    "git_head",
    "git_dirty",
    "record_path",
    "notes",
]


def _load_compare_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "compare_benchmark_records.py"
    spec = importlib.util.spec_from_file_location("compare_benchmark_records", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_record(
    workspace: Path,
    *,
    run_id: str,
    stage4_attempts: int,
    stage4_pass_like: int,
    stage4_duration_ms: int,
    stage4_tokens: int,
    stage4_cost_usd: float,
    status: str,
    git_head: str,
    notes: str = "",
    proof_digest_status: str | None = None,
    runtime_audit_summary_payload: dict | None = None,
    guarded_summary_payload: dict | None = None,
) -> Path:
    record_root = workspace / "benchmarks" / "golden-canary" / run_id
    record_root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "recorded_at": "2026-04-23T12:00:00+09:00",
        "project_name": "golden-canary",
        "project_locator": "projects/golden-canary",
        "lane": "stage4-supervised",
        "target_ep": 15,
        "status": status,
        "notes": notes,
        "runtime_summary": {
            "runtime_audit_tag": "stage4_complete" if status == "completed" else "stage3_complete",
            "latest_session_id": "20260423_120000",
        },
        "workspace_git": {
            "branch": "main",
            "head": git_head,
            "dirty": False,
        },
        "stage_metrics": {
            "stage2": {
                "stage": "stage2",
                "source_file": "logs/pass_rate_monitor.json",
                "attempt_count": 5,
                "pass_like_count": 5,
                "reject_count": 0,
                "total_duration_ms": 500,
                "avg_duration_ms": 100,
                "total_cost_usd": 0.1,
                "total_tokens": 0,
                "latest_episode": 1,
            },
            "stage3": {
                "stage": "stage3",
                "source_file": "logs/pass_rate_monitor.json",
                "attempt_count": 7,
                "pass_like_count": 6,
                "reject_count": 1,
                "total_duration_ms": 900,
                "avg_duration_ms": 129,
                "total_cost_usd": 0.2,
                "total_tokens": 0,
                "latest_episode": 5,
            },
            "stage4": {
                "stage": "stage4",
                "source_file": "logs/episode_production.jsonl",
                "attempt_count": stage4_attempts,
                "pass_like_count": stage4_pass_like,
                "reject_count": max(stage4_attempts - stage4_pass_like, 0),
                "total_duration_ms": stage4_duration_ms,
                "avg_duration_ms": int(round(stage4_duration_ms / max(stage4_attempts, 1))),
                "total_cost_usd": stage4_cost_usd,
                "total_tokens": stage4_tokens,
                "latest_episode": 15,
            },
        },
    }
    (record_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if runtime_audit_summary_payload is not None or proof_digest_status is not None or guarded_summary_payload is not None:
        logs_dir = record_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        payload = runtime_audit_summary_payload or {
            "tag": manifest["runtime_summary"]["runtime_audit_tag"],
            "summary_role": "runtime_heartbeat_with_proof_digest",
            "latest_event_type": "stage4_complete" if status == "completed" else "stage3_complete",
            "proof_digest": {
                "status": proof_digest_status,
            },
        }
        (logs_dir / "runtime_audit_summary.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if guarded_summary_payload is not None:
            (logs_dir / "stage4_direct_supervised_guarded_result.json").write_text(
                json.dumps(guarded_summary_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    with (record_root / "stage_metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "stage",
                "source_file",
                "attempt_count",
                "pass_like_count",
                "reject_count",
                "total_duration_ms",
                "avg_duration_ms",
                "total_cost_usd",
                "total_tokens",
                "latest_episode",
            ],
        )
        writer.writeheader()
        for stage in ("stage2", "stage3", "stage4"):
            writer.writerow(manifest["stage_metrics"][stage])
    return record_root


def _write_index(workspace: Path, rows: list[dict[str, str]]) -> None:
    index_path = workspace / "benchmarks" / "benchmark_index.csv"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_build_benchmark_record_diff_reports_better_result(tmp_path):
    module = _load_compare_module()
    left_root = _write_record(
        tmp_path,
        run_id="20260423_120000__stage4-supervised__target-ep15__aaaa1111",
        stage4_attempts=12,
        stage4_pass_like=4,
        stage4_duration_ms=8000,
        stage4_tokens=12000,
        stage4_cost_usd=1.5,
        status="interrupted",
        git_head="aaaa1111",
    )
    right_root = _write_record(
        tmp_path,
        run_id="20260423_130000__stage4-supervised__target-ep15__bbbb2222",
        stage4_attempts=8,
        stage4_pass_like=6,
        stage4_duration_ms=6000,
        stage4_tokens=9000,
        stage4_cost_usd=1.1,
        status="completed",
        git_head="bbbb2222",
    )

    diff = module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert diff["delta"]["verdict"] == "better"
    assert diff["delta"]["run_meta"]["status"] == {
        "before": "interrupted",
        "after": "completed",
    }
    assert diff["delta"]["stage_metrics"]["stage4"]["attempt_count"] == -4
    assert diff["delta"]["stage_metrics"]["stage4"]["pass_like_count"] == 2
    assert diff["delta"]["stage_metrics"]["stage4"]["total_duration_ms"] == -2000
    assert diff["delta"]["stage_metrics"]["stage4"]["total_tokens"] == -3000
    assert diff["delta"]["stage_metrics"]["stage4"]["total_cost_usd"] == -0.4
    assert "stage4.pass_like_count" in diff["delta"]["improvement_signals"]
    assert "run_meta.status" in diff["delta"]["improvement_signals"]
    assert diff["delta"]["regression_signals"] == []
    watchpoint_ids = [item["id"] for item in diff["delta"]["watchpoints"]]
    assert watchpoint_ids == [
        "status_upgraded",
        "runtime_audit_tag_changed",
        "stage4_attempt_count_improved",
        "stage4_pass_like_improved",
        "stage4_cost_improved",
    ]


def test_compare_benchmark_records_resolves_run_ids_from_index(tmp_path):
    module = _load_compare_module()
    left_run_id = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    right_run_id = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    left_root = _write_record(
        tmp_path,
        run_id=left_run_id,
        stage4_attempts=10,
        stage4_pass_like=5,
        stage4_duration_ms=7000,
        stage4_tokens=10000,
        stage4_cost_usd=1.3,
        status="completed",
        git_head="aaaa1111",
    )
    right_root = _write_record(
        tmp_path,
        run_id=right_run_id,
        stage4_attempts=11,
        stage4_pass_like=5,
        stage4_duration_ms=7200,
        stage4_tokens=10100,
        stage4_cost_usd=1.32,
        status="completed",
        git_head="bbbb2222",
    )
    _write_index(
        tmp_path,
        rows=[
            {
                "run_id": left_run_id,
                "recorded_at": "2026-04-23T12:00:00+09:00",
                "project_name": "golden-canary",
                "project_locator": "projects/golden-canary",
                "lane": "stage4-supervised",
                "target_ep": "15",
                "status": "completed",
                "runtime_audit_tag": "stage4_complete",
                "latest_session_id": "20260423_120000",
                "git_branch": "main",
                "git_head": "aaaa1111",
                "git_dirty": "false",
                "record_path": left_root.relative_to(tmp_path).as_posix(),
                "notes": "",
            },
            {
                "run_id": right_run_id,
                "recorded_at": "2026-04-23T13:00:00+09:00",
                "project_name": "golden-canary",
                "project_locator": "projects/golden-canary",
                "lane": "stage4-supervised",
                "target_ep": "15",
                "status": "completed",
                "runtime_audit_tag": "stage4_complete",
                "latest_session_id": "20260423_130000",
                "git_branch": "main",
                "git_head": "bbbb2222",
                "git_dirty": "false",
                "record_path": right_root.relative_to(tmp_path).as_posix(),
                "notes": "",
            },
        ],
    )

    diff = module.compare_benchmark_records(
        left_run_id,
        right_run_id,
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert diff["left"]["run_id"] == left_run_id
    assert diff["right"]["run_id"] == right_run_id
    assert diff["left"]["record_root"] == left_root.relative_to(tmp_path).as_posix()
    assert diff["right"]["record_root"] == right_root.relative_to(tmp_path).as_posix()
    assert diff["delta"]["verdict"] == "worse"
    assert "stage4.attempt_count" in diff["delta"]["regression_signals"]
    watchpoint_ids = [item["id"] for item in diff["delta"]["watchpoints"]]
    assert watchpoint_ids == [
        "stage4_attempt_count_regressed",
        "stage4_cost_regressed",
    ]


def test_compare_benchmark_records_cli_supports_json_output(tmp_path):
    left_root = _write_record(
        tmp_path,
        run_id="20260423_120000__stage4-supervised__target-ep15__aaaa1111",
        stage4_attempts=12,
        stage4_pass_like=4,
        stage4_duration_ms=8000,
        stage4_tokens=12000,
        stage4_cost_usd=1.5,
        status="interrupted",
        git_head="aaaa1111",
    )
    right_root = _write_record(
        tmp_path,
        run_id="20260423_130000__stage4-supervised__target-ep15__bbbb2222",
        stage4_attempts=8,
        stage4_pass_like=6,
        stage4_duration_ms=6000,
        stage4_tokens=9000,
        stage4_cost_usd=1.1,
        status="completed",
        git_head="bbbb2222",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/compare_benchmark_records.py",
            str(left_root),
            str(right_root),
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--format",
            "json",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload["delta"]["verdict"] == "better"
    assert payload["delta"]["changed_sections"] == ["run_meta", "stage_metrics", "watchpoints"]
    assert payload["delta"]["stage_metrics"]["stage4"]["pass_like_count"] == 2


def test_compare_benchmark_records_surfaces_note_and_proof_digest_watchpoints(tmp_path):
    module = _load_compare_module()
    left_root = _write_record(
        tmp_path,
        run_id="20260423_120000__stage4-supervised__target-ep15__aaaa1111",
        stage4_attempts=12,
        stage4_pass_like=4,
        stage4_duration_ms=8000,
        stage4_tokens=12000,
        stage4_cost_usd=1.5,
        status="operational_failure",
        git_head="aaaa1111",
        notes="terminated_by_monitor=true; termination_reason=stage4_round_limit_exceeded",
        runtime_audit_summary_payload={
            "tag": "stage3_complete",
            "summary_role": "runtime_heartbeat_with_proof_digest",
            "latest_event_type": "stage3_complete",
            "proof_digest": {
                "status": "warn",
                "operational_metadata": {
                    "status": "missing_session",
                    "latest_session_id": "20260423_120000",
                    "stage4_live_session": {
                        "status": "absent",
                        "retry_exercised": False,
                        "patch_exercised": False,
                        "target_ep_reached": False,
                        "stage4_complete_emitted": False,
                        "post_pass_contract_signal_count": 0,
                    },
                },
            },
        },
    )
    right_root = _write_record(
        tmp_path,
        run_id="20260423_130000__stage4-supervised__target-ep15__bbbb2222",
        stage4_attempts=10,
        stage4_pass_like=5,
        stage4_duration_ms=7900,
        stage4_tokens=11800,
        stage4_cost_usd=1.45,
        status="completed",
        git_head="bbbb2222",
        runtime_audit_summary_payload={
            "tag": "stage4_complete",
            "summary_role": "runtime_heartbeat_with_proof_digest",
            "latest_event_type": "stage4_complete",
            "proof_digest": {
                "status": "ok",
                "operational_metadata": {
                    "status": "ok",
                    "latest_session_id": "20260423_120000",
                    "stage4_live_session": {
                        "status": "ok",
                        "retry_exercised": False,
                        "patch_exercised": False,
                        "target_ep_reached": True,
                        "stage4_complete_emitted": True,
                        "post_pass_contract_signal_count": 1,
                    },
                },
            },
        },
    )

    diff = module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    watchpoints = diff["delta"]["watchpoints"]
    assert {
        "id": "proof_digest_attention",
        "severity": "warn",
        "scope": "runtime_audit_summary",
        "side": "left",
        "message": "left proof_digest.status is warn",
    } in watchpoints
    assert {
        "id": "runtime_operational_status_attention",
        "severity": "warn",
        "scope": "runtime_audit_summary",
        "side": "left",
        "message": "left operational_metadata.status is missing_session",
    } in watchpoints
    assert {
        "id": "stage4_live_session_attention",
        "severity": "warn",
        "scope": "stage4",
        "side": "left",
        "message": "left stage4_live_session.status is absent",
    } in watchpoints
    assert {
        "id": "monitor_termination_recorded",
        "severity": "warn",
        "scope": "notes",
        "side": "left",
        "message": "left record indicates monitor termination (stage4_round_limit_exceeded)",
    } in watchpoints
    assert {
        "id": "stage4_post_pass_contract_signals_recorded",
        "severity": "info",
        "scope": "stage4",
        "side": "right",
        "message": "right stage4 post_pass_contract_signal_count is 1",
    } in watchpoints


def test_compare_benchmark_records_surfaces_stage4_runtime_watchpoints(tmp_path):
    module = _load_compare_module()
    left_root = _write_record(
        tmp_path,
        run_id="20260423_120000__stage4-supervised__target-ep15__aaaa1111",
        stage4_attempts=12,
        stage4_pass_like=4,
        stage4_duration_ms=8000,
        stage4_tokens=12000,
        stage4_cost_usd=1.5,
        status="snapshot",
        git_head="aaaa1111",
        runtime_audit_summary_payload={
            "tag": "stage4_snapshot",
            "summary_role": "runtime_heartbeat_with_proof_digest",
            "latest_event_type": "stage4_runtime_advisory",
            "proof_digest": {
                "status": "ok",
                "operational_metadata": {
                    "status": "ok",
                    "latest_session_id": "20260423_120000",
                    "stage4_live_session": {
                        "status": "ok",
                        "retry_exercised": False,
                        "patch_exercised": False,
                        "target_ep_reached": False,
                        "stage4_complete_emitted": False,
                        "post_pass_contract_signal_count": 0,
                    },
                },
            },
        },
    )
    right_root = _write_record(
        tmp_path,
        run_id="20260423_130000__stage4-supervised__target-ep15__bbbb2222",
        stage4_attempts=8,
        stage4_pass_like=6,
        stage4_duration_ms=6000,
        stage4_tokens=9000,
        stage4_cost_usd=1.1,
        status="completed",
        git_head="bbbb2222",
        runtime_audit_summary_payload={
            "tag": "stage4_complete",
            "summary_role": "runtime_heartbeat_with_proof_digest",
            "latest_event_type": "stage4_complete",
            "proof_digest": {
                "status": "ok",
                "operational_metadata": {
                    "status": "ok",
                    "latest_session_id": "20260423_130000",
                    "stage4_live_session": {
                        "status": "ok",
                        "retry_exercised": True,
                        "patch_exercised": True,
                        "target_ep_reached": True,
                        "stage4_complete_emitted": True,
                        "post_pass_contract_signal_count": 2,
                    },
                },
            },
        },
    )

    diff = module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    watchpoints = diff["delta"]["watchpoints"]
    assert {
        "id": "stage4_target_ep_not_reached",
        "severity": "warn",
        "scope": "stage4",
        "side": "left",
        "message": "left stage4 live session did not emit target_ep_reached",
    } in watchpoints
    assert {
        "id": "stage4_complete_signal_missing",
        "severity": "warn",
        "scope": "stage4",
        "side": "left",
        "message": "left stage4 live session did not emit stage4_complete",
    } in watchpoints
    assert {
        "id": "stage4_retry_exercised",
        "severity": "info",
        "scope": "stage4",
        "side": "right",
        "message": "right stage4_live_session exercised retry",
    } in watchpoints
    assert {
        "id": "stage4_patch_exercised",
        "severity": "info",
        "scope": "stage4",
        "side": "right",
        "message": "right stage4_live_session exercised patch",
    } in watchpoints
    assert {
        "id": "stage4_post_pass_contract_signals_recorded",
        "severity": "info",
        "scope": "stage4",
        "side": "right",
        "message": "right stage4 post_pass_contract_signal_count is 2",
    } in watchpoints


def test_compare_benchmark_records_prefers_current_guarded_summary_for_rerun_watchpoints(tmp_path):
    module = _load_compare_module()
    left_run_id = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    left_root = _write_record(
        tmp_path,
        run_id=left_run_id,
        stage4_attempts=12,
        stage4_pass_like=4,
        stage4_duration_ms=8000,
        stage4_tokens=12000,
        stage4_cost_usd=1.5,
        status="operational_failure",
        git_head="aaaa1111",
        notes=(
            "guarded direct supervised stage4; target_ep=15; before_latest_ep=10; "
            "after_latest_ep=11; child_exit_code=1; terminated_by_monitor=true; "
            "termination_reason=stage4_round_limit_exceeded"
        ),
        guarded_summary_payload={
            "target_ep": 15,
            "latest_written_ep_before": 11,
            "latest_written_ep_after": 14,
            "terminated_by_monitor": True,
            "termination_reason": "stage4_round_limit_exceeded",
            "child_exit_code": 1,
            "benchmark_archive": {
                "run_id": left_run_id,
            },
        },
    )
    right_root = _write_record(
        tmp_path,
        run_id="20260423_130000__stage4-supervised__target-ep15__bbbb2222",
        stage4_attempts=8,
        stage4_pass_like=6,
        stage4_duration_ms=6000,
        stage4_tokens=9000,
        stage4_cost_usd=1.1,
        status="completed",
        git_head="bbbb2222",
    )

    diff = module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    watchpoints = diff["delta"]["watchpoints"]
    assert {
        "id": "monitor_termination_recorded",
        "severity": "warn",
        "scope": "stage4_guarded_result",
        "side": "left",
        "message": "left record indicates monitor termination (stage4_round_limit_exceeded)",
    } in watchpoints
    assert {
        "id": "stage4_child_exit_nonzero",
        "severity": "warn",
        "scope": "stage4_guarded_result",
        "side": "left",
        "message": "left record child_exit_code is 1",
    } in watchpoints
    assert {
        "id": "stage4_rerun_progress_recorded",
        "severity": "info",
        "scope": "stage4_guarded_result",
        "side": "left",
        "message": "left record advanced latest_written_ep from 11 to 14",
    } in watchpoints
    assert {
        "id": "stage4_target_gap_remaining",
        "severity": "warn",
        "scope": "stage4_guarded_result",
        "side": "left",
        "message": "left record stopped at latest_written_ep 14 before target_ep 15",
    } in watchpoints


def test_compare_benchmark_records_flags_stale_guarded_summary_and_falls_back_to_notes(tmp_path):
    module = _load_compare_module()
    left_root = _write_record(
        tmp_path,
        run_id="20260423_120000__stage4-supervised__target-ep15__aaaa1111",
        stage4_attempts=12,
        stage4_pass_like=4,
        stage4_duration_ms=8000,
        stage4_tokens=12000,
        stage4_cost_usd=1.5,
        status="operational_failure",
        git_head="aaaa1111",
        notes=(
            "guarded direct supervised stage4; target_ep=15; before_latest_ep=11; "
            "after_latest_ep=14; child_exit_code=1; terminated_by_monitor=true; "
            "termination_reason=stage4_round_limit_exceeded"
        ),
        guarded_summary_payload={
            "target_ep": 15,
            "latest_written_ep_before": 10,
            "latest_written_ep_after": 11,
            "terminated_by_monitor": True,
            "termination_reason": "stage4_round_limit_exceeded",
            "child_exit_code": 1,
            "benchmark_archive": {
                "run_id": "20260423_110000__stage4-supervised__target-ep15__old11111",
            },
        },
    )
    right_root = _write_record(
        tmp_path,
        run_id="20260423_130000__stage4-supervised__target-ep15__bbbb2222",
        stage4_attempts=8,
        stage4_pass_like=6,
        stage4_duration_ms=6000,
        stage4_tokens=9000,
        stage4_cost_usd=1.1,
        status="completed",
        git_head="bbbb2222",
    )

    diff = module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    watchpoints = diff["delta"]["watchpoints"]
    assert {
        "id": "stage4_guarded_summary_stale_reference",
        "severity": "warn",
        "scope": "stage4_guarded_result",
        "side": "left",
        "message": (
            "left archived guarded summary points at benchmark run "
            "20260423_110000__stage4-supervised__target-ep15__old11111, "
            "not 20260423_120000__stage4-supervised__target-ep15__aaaa1111"
        ),
    } in watchpoints
    assert {
        "id": "stage4_rerun_progress_recorded",
        "severity": "info",
        "scope": "notes",
        "side": "left",
        "message": "left record advanced latest_written_ep from 11 to 14",
    } in watchpoints
    assert {
        "id": "stage4_target_gap_remaining",
        "severity": "warn",
        "scope": "notes",
        "side": "left",
        "message": "left record stopped at latest_written_ep 14 before target_ep 15",
    } in watchpoints
