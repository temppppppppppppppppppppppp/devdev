import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def _load_backfill_module():
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "backfill_benchmark_native_post_run_evidence.py"
    )
    spec = importlib.util.spec_from_file_location("backfill_benchmark_native_post_run_evidence", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_report_test_helpers():
    helper_path = Path(__file__).resolve().parents[1] / "tests" / "test_report_benchmark_operator_lines.py"
    spec = importlib.util.spec_from_file_location("test_report_benchmark_operator_lines", helper_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_runtime_audit_summary(record_root: Path, payload: dict) -> None:
    logs_dir = record_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "runtime_audit_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_guarded_result(record_root: Path, payload: dict) -> None:
    logs_dir = record_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "stage4_direct_supervised_guarded_result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_write_native_post_run_evidence_links_backfilled_json(tmp_path):
    module = _load_backfill_module()
    helper = _load_report_test_helpers()
    run_id = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    record_root = helper._write_record(tmp_path, run_id=run_id, status="operational_failure")
    _write_runtime_audit_summary(
        record_root,
        {
            "summary_role": "runtime_heartbeat_with_proof_digest",
            "latest_event_type": "stage4_runtime_advisory",
            "proof_digest": {
                "status": "ok",
                "operational_metadata": {
                    "status": "warn",
                    "latest_session_id": "20260423_130000",
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
            "stage4_diagnostic_packet": {
                "schema_version": "stage4_diagnostic_packet_v1",
                "authority_role": "runtime_audit_summary",
                "operator_guidance_only": True,
                "proof_stage4_status": "warn",
                "proof_warning_taxonomy_counts": {
                    "runtime_advisory_warn": 2,
                },
                "cove_runtime_advisory_count": 2,
                "pass_preserved_cove_advisory_count": 2,
            },
        },
    )
    _write_guarded_result(
        record_root,
        {
            "target_ep": 15,
            "latest_written_ep_before": 10,
            "latest_written_ep_after": 11,
            "terminated_by_monitor": True,
            "termination_reason": "stage4_round_limit_exceeded",
            "child_exit_code": 1,
            "benchmark_archive": {
                "run_id": run_id,
            },
        },
    )

    result = module.write_native_post_run_evidence(
        run_id,
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    evidence_path = tmp_path / result["evidence_path"]
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "benchmark-native-post-run-evidence-v1"
    assert payload["evidence_role"] == "archive_native_post_run_evidence"
    assert payload["run_id"] == run_id
    assert payload["runtime_terminal_state"] == {
        "status": "operational_failure",
        "runtime_audit_tag": "stage3_complete",
        "target_ep": 15,
        "latest_session_id": "20260423_120000",
    }
    assert payload["archive_native_summary"]["proof_digest_status"] == "ok"
    assert payload["archive_native_summary"]["operational_status"] == "warn"
    assert payload["archive_native_summary"]["stage4_live_session_status"] == "absent"
    assert payload["archive_native_summary"]["stage4_retry_exercised"] is False
    assert payload["archive_native_summary"]["stage4_patch_exercised"] is False
    assert payload["archive_native_summary"]["stage4_target_ep_reached"] is False
    assert payload["archive_native_summary"]["stage4_complete_emitted"] is False
    assert payload["archive_native_summary"]["stage4_post_pass_contract_signal_count"] == 0
    assert payload["archive_native_summary"]["guarded_result_available"] is True
    assert payload["archive_native_summary"]["guarded_result_run_id"] == run_id
    assert payload["archive_native_summary"]["guarded_target_ep"] == 15
    assert payload["archive_native_summary"]["guarded_latest_written_ep_before"] == 10
    assert payload["archive_native_summary"]["guarded_latest_written_ep_after"] == 11
    assert payload["archive_native_summary"]["guarded_terminated_by_monitor"] is True
    assert payload["archive_native_summary"]["guarded_termination_reason"] == "stage4_round_limit_exceeded"
    assert payload["archive_native_summary"]["guarded_child_exit_code"] == 1
    assert payload["archive_native_summary"]["note_markers"]["target_ep"] is None
    assert payload["stage4_diagnostic_packet"]["proof_stage4_status"] == "warn"
    assert payload["stage4_diagnostic_packet"]["cove_runtime_advisory_count"] == 2
    assert payload["stage4_diagnostic_packet"]["pass_preserved_cove_advisory_count"] == 2
    assert payload["stage4_diagnostic_packet"]["proof_warning_taxonomy_counts"] == {
        "runtime_advisory_warn": 2,
    }

    links_path = record_root / "benchmark_companion_links.json"
    links_payload = json.loads(links_path.read_text(encoding="utf-8"))
    assert links_payload == {
        "schema_version": "benchmark-companion-links-v1",
        "post_run_evidence_json": f"benchmarks/golden-canary/{run_id}/native-post-run-evidence.json",
        "post_run_merge_audit_md": "",
        "supporting_context_md": "",
    }


def test_backfill_native_post_run_evidence_cli_supports_all_live(tmp_path):
    helper = _load_report_test_helpers()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    record_a = helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    record_b = helper._write_record(tmp_path, run_id=run_b, status="completed")
    _write_runtime_audit_summary(record_a, {"proof_digest": {"status": "ok"}})
    _write_runtime_audit_summary(record_b, {"proof_digest": {"status": "ok"}})

    result = subprocess.run(
        [
            sys.executable,
            "scripts/backfill_benchmark_native_post_run_evidence.py",
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--all-live",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert [item["run_id"] for item in payload["records"]] == [run_a, run_b]
    for run_id in (run_a, run_b):
        assert (tmp_path / "benchmarks" / "golden-canary" / run_id / "native-post-run-evidence.json").exists()
        assert (tmp_path / "benchmarks" / "golden-canary" / run_id / "benchmark_companion_links.json").exists()
