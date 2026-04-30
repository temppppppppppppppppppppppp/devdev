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


def test_stage4_diagnostic_packet_preserves_run_health_counts():
    module = _load_compare_module()

    packet = module._normalize_stage4_diagnostic_packet(
        {
            "schema_version": "stage4_diagnostic_packet_v1",
            "stage4_run_health_counts": {
                "pure_pass": 2,
                "repaired_pass": 1,
                "retry_heavy_pass": 1,
            },
        }
    )
    counts = module._stage4_diagnostic_count_summary(packet)

    assert packet["stage4_run_health_counts"]["pure_pass"] == 2
    assert counts["pure_pass"] == 2
    assert counts["repaired_pass"] == 1
    assert counts["retry_heavy_pass"] == 1


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
    stage4_diagnostic_packet: dict | None = None,
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
    if stage4_diagnostic_packet is not None:
        manifest["stage4_diagnostic_packet"] = stage4_diagnostic_packet
    (record_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if (
        runtime_audit_summary_payload is not None
        or proof_digest_status is not None
        or guarded_summary_payload is not None
    ):
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


def _write_companion_evidence(workspace: Path, relative_path: str, payload: dict) -> Path:
    target = workspace / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def _write_companion_markdown(workspace: Path, relative_path: str, body: str) -> Path:
    target = workspace / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


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


def test_load_benchmark_record_falls_back_from_stale_index_record_path(tmp_path):
    module = _load_compare_module()
    run_id = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    record_root = _write_record(
        tmp_path,
        run_id=run_id,
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
                "run_id": run_id,
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
                "record_path": f"benchmarks/stale-lane/{run_id}",
                "notes": "",
            },
        ],
    )

    record = module.load_benchmark_record(
        run_id,
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert record["run_id"] == run_id
    assert record["record_root"] == record_root.relative_to(tmp_path).as_posix()


def test_load_benchmark_record_raises_clear_error_for_stale_index_without_live_record(tmp_path):
    module = _load_compare_module()
    run_id = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    _write_index(
        tmp_path,
        rows=[
            {
                "run_id": run_id,
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
                "record_path": f"benchmarks/stale-lane/{run_id}",
                "notes": "",
            },
        ],
    )

    try:
        module.load_benchmark_record(
            run_id,
            workspace_root=tmp_path,
            benchmark_root="benchmarks",
        )
    except FileNotFoundError as exc:
        assert str(exc) == (
            "stale benchmark_index.csv record_path for run_id "
            f"{run_id}: missing manifest.json under "
            f"{(tmp_path / 'benchmarks' / 'stale-lane' / run_id).resolve()}"
        )
    else:
        raise AssertionError("expected FileNotFoundError for stale benchmark index row")


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
    assert payload["delta"]["operator_summary"] == {
        "status": "clean",
        "needs_remediation": False,
        "headline": "no remediation needed",
        "remediation_hint_count": 0,
        "highest_priority_surface": "",
        "surfaces_by_priority": [],
        "ci_gate": "pass",
        "gate_basis": "clean",
    }
    assert payload["delta"]["operator_report_line"] == (
        "status=clean; ci_gate=pass; gate_basis=clean; headline=no remediation needed"
    )


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
    assert diff["delta"]["operator_summary"]["status"] == "clean"
    assert diff["delta"]["operator_summary"]["ci_gate"] == "warn"
    assert diff["delta"]["operator_summary"]["gate_basis"] == "warn_watchpoints"
    assert diff["delta"]["operator_report_line"] == (
        "status=clean; ci_gate=warn; gate_basis=warn_watchpoints; headline=no remediation needed"
    )


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
            "stage4_diagnostic_packet": {
                "schema_version": "stage4_diagnostic_packet_v1",
                "authority_role": "runtime_audit_summary",
                "operator_guidance_only": True,
                "runtime_summary_freshness_status": "stale_for_stage4",
                "runtime_summary_scope_status": "pre_stage4_or_partial",
                "proof_digest_status": "ok",
                "proof_stage4_status": "warn",
                "proof_warning_taxonomy_counts": {
                    "coverage_warn": 1,
                    "runtime_advisory_warn": 2,
                },
                "cove_runtime_advisory_count": 2,
                "pass_preserved_cove_advisory_count": 2,
                "cove_semantic_fail_closed_count": 1,
                "post_select_conflict_count": 3,
                "settled_director_divergence_count": 4,
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
    assert {
        "id": "stage4_diagnostic_packet_attention",
        "severity": "warn",
        "scope": "stage4_diagnostic_packet",
        "side": "left",
        "message": "left stage4 diagnostic packet status is warn",
    } in watchpoints
    assert {
        "id": "stage4_diagnostic_packet_stale",
        "severity": "warn",
        "scope": "stage4_diagnostic_packet",
        "side": "left",
        "message": "left stage4 diagnostic packet reports stale runtime summary",
    } in watchpoints
    assert {
        "id": "stage4_diagnostic_packet_counts_recorded",
        "severity": "info",
        "scope": "stage4_diagnostic_packet",
        "side": "left",
        "message": (
            "left stage4 diagnostic packet counts: cove_runtime_advisory=2, "
            "pass_preserved_advisory=2, semantic_retry=1, post_select_conflict=3, "
            "proof_warn=3, settled_director_divergence=4"
        ),
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


def test_compare_benchmark_records_surfaces_companion_post_run_evidence_watchpoints(tmp_path):
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
    right_evidence = _write_companion_evidence(
        tmp_path,
        "docs/2026-04-23/right-post-run-evidence.json",
        {
            "runtime_terminal_state": {
                "runtime_audit_tag": "stage4_complete",
            },
            "hard_gates": {
                "status": "fail",
            },
            "current_session_sink_alignment_summary": {
                "status": "warn",
            },
            "final_authority_contract_summary": {
                "status": "missing",
            },
            "gate_repair_surface_summary": {
                "status": "missing",
            },
            "stage4_diagnostic_packet": {
                "schema_version": "stage4_diagnostic_packet_v1",
                "authority_role": "native_post_run_evidence",
                "operator_guidance_only": True,
                "proof_stage4_status": "warn",
                "proof_warning_taxonomy_counts": {
                    "runtime_advisory_warn": 2,
                },
                "cove_runtime_advisory_count": 2,
            },
        },
    )

    diff = module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
        right_evidence_json=right_evidence,
    )

    watchpoints = diff["delta"]["watchpoints"]
    assert {
        "id": "post_run_hard_gates_failed",
        "severity": "warn",
        "scope": "post_run_evidence_json",
        "side": "right",
        "message": "right companion evidence reports hard_gates.status=fail",
    } in watchpoints
    assert {
        "id": "post_run_sink_alignment_attention",
        "severity": "warn",
        "scope": "post_run_evidence_json",
        "side": "right",
        "message": "right companion evidence reports sink alignment status warn",
    } in watchpoints
    assert {
        "id": "post_run_final_authority_attention",
        "severity": "warn",
        "scope": "post_run_evidence_json",
        "side": "right",
        "message": "right companion evidence reports final authority status missing",
    } in watchpoints
    assert {
        "id": "post_run_gate_repair_attention",
        "severity": "warn",
        "scope": "post_run_evidence_json",
        "side": "right",
        "message": "right companion evidence reports gate repair status missing",
    } in watchpoints
    assert {
        "id": "stage4_diagnostic_packet_attention",
        "severity": "warn",
        "scope": "stage4_diagnostic_packet",
        "side": "right",
        "message": "right stage4 diagnostic packet status is warn",
    } in watchpoints
    assert {
        "id": "stage4_diagnostic_packet_counts_recorded",
        "severity": "info",
        "scope": "stage4_diagnostic_packet",
        "side": "right",
        "message": (
            "right stage4 diagnostic packet counts: cove_runtime_advisory=2, "
            "pass_preserved_advisory=0, semantic_retry=0, post_select_conflict=0, "
            "proof_warn=2, settled_director_divergence=0"
        ),
    } in watchpoints


def test_compare_benchmark_records_surfaces_companion_merge_audit_watchpoints(tmp_path):
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
    left_merge_audit = _write_companion_markdown(
        tmp_path,
        "docs/2026-04-23/left-post-run-merge-audit.md",
        "\n".join(
            [
                "# Left Merge Audit",
                "",
                "Status: final",
                "Confidence: `96%`",
                "",
                "### Finding 1. residual carryover seam remains",
                "",
                "Severity: medium",
                "",
                "## Remaining Watchpoints",
                "",
                "1. residual carryover seam remains",
                "2. source blocker still open",
                "",
                "This lane is partially realized and not resolved yet.",
                "",
                "## 6. Validation",
                "",
                "Static verification:",
                "",
                "- `pytest tests/test_unified_blueprint_validator_lane_c.py -q` -> `42 passed`",
                "- `pytest tests/test_stage3_orchestrator.py -q` -> `103 passed`",
                "",
                "Live verification:",
                "",
                "- fresh rerun `20260421_002444` -> `ep1 PASS 95`, `ep2 PASS_WITH_WARNING 95`",
                "- fresh rerun `20260421_003616` -> `ep1 PASS 95`, `ep2 FAILED`",
                "",
                "## 7. Current Rerun Posture",
                "",
                "- patch status: `ready`",
                "- local validation: `clean`",
                "- next operator step before rerun: rerun against refreshed watchlist",
                "",
            ]
        ),
    )
    (left_root / "benchmark_companion_links.json").write_text(
        json.dumps(
            {
                "schema_version": "benchmark-companion-links-v1",
                "post_run_evidence_json": "",
                "post_run_merge_audit_md": left_merge_audit.relative_to(tmp_path).as_posix(),
                "supporting_context_md": "",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    diff = module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert diff["left"]["companion_merge_audit"] == {
        "available": True,
        "source_path": "docs/2026-04-23/left-post-run-merge-audit.md",
        "title": "Left Merge Audit",
        "status": "final",
        "confidence_percent": 96,
        "finding_count": 1,
        "max_severity": "medium",
        "remaining_watchpoint_count": 2,
        "residual_markers": [
            "partially_realized",
            "not_resolved",
            "blocker",
            "remaining_watchpoints",
        ],
        "findings": [
            {
                "title": "residual carryover seam remains",
                "severity": "medium",
            }
        ],
        "finding_severity_counts": {
            "medium": 1,
        },
        "rerun_posture": {
            "patch_status": "ready",
            "local_validation": "clean",
            "next_operator_step_before_rerun": "rerun against refreshed watchlist",
        },
        "validation": {
            "available": True,
            "static_pass_total": 145,
            "result_count": 4,
            "live_rerun_count": 2,
            "live_rerun_status": "mixed",
            "live_reruns": [
                {
                    "run_id": "20260421_002444",
                    "result": "ep1 PASS 95, ep2 PASS_WITH_WARNING 95",
                    "has_pass_like": True,
                    "has_failure": False,
                },
                {
                    "run_id": "20260421_003616",
                    "result": "ep1 PASS 95, ep2 FAILED",
                    "has_pass_like": True,
                    "has_failure": True,
                },
            ],
            "replay_probe_count": 0,
            "result_signal_count": 0,
            "replay_probes": [],
        },
        "follow_up": {
            "available": False,
            "open_item_count": 0,
            "open_markers": [],
            "addendum_finding_count": 0,
            "consequence_markers": [],
        },
    }
    watchpoints = diff["delta"]["watchpoints"]
    assert {
        "id": "post_run_merge_audit_summary_recorded",
        "severity": "info",
        "scope": "post_run_merge_audit_md",
        "side": "left",
        "message": "left merge audit summary: status=final, max_severity=medium, finding_count=1",
    } in watchpoints
    assert {
        "id": "post_run_merge_audit_severity_attention",
        "severity": "warn",
        "scope": "post_run_merge_audit_md",
        "side": "left",
        "message": "left merge audit max_severity is medium",
    } in watchpoints
    assert {
        "id": "post_run_merge_audit_remaining_watchpoints",
        "severity": "warn",
        "scope": "post_run_merge_audit_md",
        "side": "left",
        "message": "left merge audit records 2 remaining watchpoints",
    } in watchpoints
    assert {
        "id": "post_run_merge_audit_residual_attention",
        "severity": "warn",
        "scope": "post_run_merge_audit_md",
        "side": "left",
        "message": ("left merge audit residual markers: partially_realized,not_resolved,blocker,remaining_watchpoints"),
    } in watchpoints
    assert {
        "id": "post_run_merge_audit_finding_breakdown",
        "severity": "info",
        "scope": "post_run_merge_audit_md",
        "side": "left",
        "message": "left merge audit finding breakdown: medium=1",
    } in watchpoints
    assert {
        "id": "post_run_merge_audit_top_finding_attention",
        "severity": "warn",
        "scope": "post_run_merge_audit_md",
        "side": "left",
        "message": "left merge audit top finding [medium]: residual carryover seam remains",
    } in watchpoints
    assert {
        "id": "post_run_merge_audit_rerun_posture_recorded",
        "severity": "info",
        "scope": "post_run_merge_audit_md",
        "side": "left",
        "message": (
            "left rerun posture: patch_status=ready, local_validation=clean, "
            "next_operator_step_before_rerun=rerun against refreshed watchlist"
        ),
    } in watchpoints
    assert {
        "id": "post_run_merge_audit_validation_summary_recorded",
        "severity": "info",
        "scope": "post_run_merge_audit_md",
        "side": "left",
        "message": "left merge audit validation summary: static_pass_total=145, result_count=4, live_reruns=2, live_status=mixed",
    } in watchpoints
    assert {
        "id": "post_run_merge_audit_live_verification_mixed",
        "severity": "warn",
        "scope": "post_run_merge_audit_md",
        "side": "left",
        "message": "left merge audit live verification is mixed across 2 reruns",
    } in watchpoints


def test_compare_benchmark_records_extracts_numbered_validation_probe_signals(tmp_path):
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
    right_merge_audit = _write_companion_markdown(
        tmp_path,
        "docs/2026-04-23/right-post-run-merge-audit.md",
        "\n".join(
            [
                "# Right Merge Audit",
                "",
                "Status: final",
                "",
                "## Validation",
                "",
                "1. targeted pytest",
                "   - `python -m pytest tests/test_unified_blueprint_validator_lane_c.py tests/test_blueprint_ensemble_generate_ensemble.py -q`",
                "   - result: `108 passed`",
                "",
                "2. adjacent carryover shard",
                "   - `python -m pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q`",
                "   - result: `49 passed`",
                "",
                "3. real-case replay",
                "   - replayed the accepted `ep10` Stage3 blueprint through `_python_pre_validate`",
                "   - result now emits:",
                "     - `CRITICAL / opening_transition`",
                "     - `carryover active character re-entry`",
                "",
            ]
        ),
    )
    (right_root / "benchmark_companion_links.json").write_text(
        json.dumps(
            {
                "schema_version": "benchmark-companion-links-v1",
                "post_run_evidence_json": "",
                "post_run_merge_audit_md": right_merge_audit.relative_to(tmp_path).as_posix(),
                "supporting_context_md": "",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    diff = module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert diff["right"]["companion_merge_audit"]["validation"] == {
        "available": True,
        "static_pass_total": 157,
        "result_count": 3,
        "live_rerun_count": 0,
        "live_rerun_status": "",
        "live_reruns": [],
        "replay_probe_count": 1,
        "result_signal_count": 2,
        "replay_probes": [
            {
                "description": "the accepted ep10 Stage3 blueprint through _python_pre_validate",
                "signals": [
                    "CRITICAL / opening_transition",
                    "carryover active character re-entry",
                ],
            }
        ],
    }
    watchpoints = diff["delta"]["watchpoints"]
    assert {
        "id": "post_run_merge_audit_validation_summary_recorded",
        "severity": "info",
        "scope": "post_run_merge_audit_md",
        "side": "right",
        "message": (
            "right merge audit validation summary: static_pass_total=157, result_count=3, "
            "replay_probes=1, result_signals=2"
        ),
    } in watchpoints


def test_compare_benchmark_records_extracts_addendum_and_follow_up_markers(tmp_path):
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
    right_merge_audit = _write_companion_markdown(
        tmp_path,
        "docs/2026-04-23/right-post-run-merge-audit.md",
        "\n".join(
            [
                "# Right Merge Audit",
                "",
                "Status: final",
                "",
                "Merged addendum findings:",
                "",
                "1. The first packet-side follow-up was necessary but not sufficient.",
                "2. The real root cause was the immutable previous-opening [FACT-LOCK] block.",
                "3. The bounded compiler fix now suppresses those previous-opening immutable anchors.",
                "4. The fresh exact-lineage Stage3 rerun now passes in bounded scope.",
                "",
                "Current authoritative consequence:",
                "",
                "- the previously assigned Stage3 arc_timeline residual is resolved in bounded scope on the exact failed lineage",
                "- the remaining blocker for closure-grade downstream replay is the Stage34 single-episode demo utility source-contract gap",
                "",
                "What remains open:",
                "",
                "- the Episode 2 frontier is still nondeterministic under fresh reruns",
                "- one fresh rerun cleared the narrative path and one later rerun regressed",
                "- therefore this lane should be read as bounded authority-alignment improvement landed with mixed fresh-proof stability",
                "",
            ]
        ),
    )
    (right_root / "benchmark_companion_links.json").write_text(
        json.dumps(
            {
                "schema_version": "benchmark-companion-links-v1",
                "post_run_evidence_json": "",
                "post_run_merge_audit_md": right_merge_audit.relative_to(tmp_path).as_posix(),
                "supporting_context_md": "",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    diff = module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert diff["right"]["companion_merge_audit"]["follow_up"] == {
        "available": True,
        "open_item_count": 3,
        "open_markers": [
            "nondeterministic",
            "regressed",
            "mixed_fresh_proof_stability",
        ],
        "addendum_finding_count": 4,
        "consequence_markers": [
            "resolved_in_bounded_scope",
            "remaining_blocker",
        ],
    }
    watchpoints = diff["delta"]["watchpoints"]
    assert {
        "id": "post_run_merge_audit_follow_up_summary_recorded",
        "severity": "info",
        "scope": "post_run_merge_audit_md",
        "side": "right",
        "message": "right merge audit follow-up summary: open_items=3, addendum_findings=4, consequence_markers=2",
    } in watchpoints
    assert {
        "id": "post_run_merge_audit_open_follow_up_attention",
        "severity": "warn",
        "scope": "post_run_merge_audit_md",
        "side": "right",
        "message": (
            "right merge audit follow-up still lists 3 open items "
            "(nondeterministic,regressed,mixed_fresh_proof_stability)"
        ),
    } in watchpoints
    assert {
        "id": "post_run_merge_audit_consequence_markers_recorded",
        "severity": "info",
        "scope": "post_run_merge_audit_md",
        "side": "right",
        "message": "right merge audit consequence markers: resolved_in_bounded_scope,remaining_blocker",
    } in watchpoints
    assert {
        "id": "post_run_merge_audit_remaining_blocker_attention",
        "severity": "warn",
        "scope": "post_run_merge_audit_md",
        "side": "right",
        "message": "right merge audit authoritative consequence still records a remaining blocker",
    } in watchpoints


def test_compare_benchmark_records_companion_merge_audit_clean_summary_is_info_only(tmp_path):
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
    right_merge_audit = _write_companion_markdown(
        tmp_path,
        "docs/2026-04-23/right-post-run-merge-audit.md",
        "\n".join(
            [
                "# Right Merge Audit",
                "",
                "Status: final",
                "Confidence: `97%`",
                "",
                "## Final Conclusion",
                "",
                "- bounded proof captured cleanly",
                "",
            ]
        ),
    )
    (right_root / "benchmark_companion_links.json").write_text(
        json.dumps(
            {
                "schema_version": "benchmark-companion-links-v1",
                "post_run_evidence_json": "",
                "post_run_merge_audit_md": right_merge_audit.relative_to(tmp_path).as_posix(),
                "supporting_context_md": "",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    diff = module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    watchpoints = diff["delta"]["watchpoints"]
    assert {
        "id": "post_run_merge_audit_summary_recorded",
        "severity": "info",
        "scope": "post_run_merge_audit_md",
        "side": "right",
        "message": "right merge audit summary: status=final",
    } in watchpoints
    assert not any(
        item["id"] == "post_run_merge_audit_severity_attention" and item.get("side") == "right" for item in watchpoints
    )
    assert not any(
        item["id"] == "post_run_merge_audit_remaining_watchpoints" and item.get("side") == "right"
        for item in watchpoints
    )
    assert not any(
        item["id"] == "post_run_merge_audit_residual_attention" and item.get("side") == "right" for item in watchpoints
    )


def test_compare_benchmark_records_cli_supports_companion_evidence_json(tmp_path):
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
    right_evidence = _write_companion_evidence(
        tmp_path,
        "docs/2026-04-23/right-post-run-evidence.json",
        {
            "hard_gates": {
                "status": "fail",
            },
        },
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
            "--right-evidence-json",
            str(right_evidence),
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
    assert "watchpoints" in payload["delta"]["changed_sections"]
    assert {
        "id": "post_run_hard_gates_failed",
        "severity": "warn",
        "scope": "post_run_evidence_json",
        "side": "right",
        "message": "right companion evidence reports hard_gates.status=fail",
    } in payload["delta"]["watchpoints"]


def test_compare_benchmark_records_surfaces_missing_target_hygiene_with_remediation_hints(tmp_path):
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
    (right_root / "benchmark_companion_links.json").write_text(
        json.dumps(
            {
                "schema_version": "benchmark-companion-links-v1",
                "post_run_evidence_json": "docs/2026-04-23/missing-evidence.json",
                "post_run_merge_audit_md": "",
                "supporting_context_md": "docs/2026-04-23/missing-context.md",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    diff = module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    watchpoints = diff["delta"]["watchpoints"]
    assert diff["delta"]["remediation_hints"] == [
        {
            "side": "right",
            "run_id": "20260423_130000__stage4-supervised__target-ep15__bbbb2222",
            "record_root": "benchmarks/golden-canary/20260423_130000__stage4-supervised__target-ep15__bbbb2222",
            "surface": "post_run_evidence_json",
            "current_value": "docs/2026-04-23/missing-evidence.json",
            "suggested_flag": "--post-run-evidence-json",
            "suggested_command": (
                "python scripts/link_benchmark_companions.py "
                "20260423_130000__stage4-supervised__target-ep15__bbbb2222 "
                "--post-run-evidence-json docs/2026-04-23/missing-evidence.json"
            ),
        },
        {
            "side": "right",
            "run_id": "20260423_130000__stage4-supervised__target-ep15__bbbb2222",
            "record_root": "benchmarks/golden-canary/20260423_130000__stage4-supervised__target-ep15__bbbb2222",
            "surface": "supporting_context_md",
            "current_value": "docs/2026-04-23/missing-context.md",
            "suggested_flag": "--supporting-context-md",
            "suggested_command": (
                "python scripts/link_benchmark_companions.py "
                "20260423_130000__stage4-supervised__target-ep15__bbbb2222 "
                "--supporting-context-md docs/2026-04-23/missing-context.md"
            ),
        },
    ]
    assert diff["delta"]["remediation_summary"] == {
        "hint_count": 2,
        "count_by_surface": {
            "post_run_evidence_json": 1,
            "supporting_context_md": 1,
        },
        "highest_priority_surface": "post_run_evidence_json",
        "surfaces_by_priority": [
            "post_run_evidence_json",
            "supporting_context_md",
        ],
    }
    assert diff["delta"]["operator_summary"] == {
        "status": "needs_remediation",
        "needs_remediation": True,
        "headline": "repair post_run_evidence_json first",
        "remediation_hint_count": 2,
        "highest_priority_surface": "post_run_evidence_json",
        "surfaces_by_priority": [
            "post_run_evidence_json",
            "supporting_context_md",
        ],
        "ci_gate": "warn",
        "gate_basis": "remediation_hints",
    }
    assert diff["delta"]["operator_report_line"] == (
        "status=needs_remediation; ci_gate=warn; gate_basis=remediation_hints; "
        "headline=repair post_run_evidence_json first"
    )
    assert "remediation_hints" in diff["delta"]["changed_sections"]
    assert {
        "id": "benchmark_companion_missing_target",
        "severity": "warn",
        "scope": "benchmark_companion_links",
        "side": "right",
        "message": (
            "right benchmark companion state is missing_target for post_run_evidence_json,supporting_context_md"
        ),
    } in watchpoints
    assert {
        "id": "benchmark_companion_remediation_hint",
        "severity": "info",
        "scope": "benchmark_companion_links",
        "side": "right",
        "message": (
            "right remediation post_run_evidence_json: "
            "python scripts/link_benchmark_companions.py "
            "20260423_130000__stage4-supervised__target-ep15__bbbb2222 "
            "--post-run-evidence-json docs/2026-04-23/missing-evidence.json"
        ),
    } in watchpoints
    assert {
        "id": "benchmark_companion_remediation_hint",
        "severity": "info",
        "scope": "benchmark_companion_links",
        "side": "right",
        "message": (
            "right remediation supporting_context_md: "
            "python scripts/link_benchmark_companions.py "
            "20260423_130000__stage4-supervised__target-ep15__bbbb2222 "
            "--supporting-context-md docs/2026-04-23/missing-context.md"
        ),
    } in watchpoints
