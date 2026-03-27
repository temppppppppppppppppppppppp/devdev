import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def _load_diff_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "diff_canary_summaries.py"
    spec = importlib.util.spec_from_file_location("diff_canary_summaries", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_canary_summary_diff_compares_stage4_sections():
    module = _load_diff_module()

    left = {
        "summary_role": "stage4_live_canary_with_stage3_sink_probe",
        "hard_gates": {"status": "warn", "errors": ["final_sink_missing"], "warnings": ["patch_trace_not_exercised"]},
        "sink_alignment_summary": {
            "status": "warn",
            "final_sink_missing": {"episode_production": ["attempt-1"]},
            "patch_strategy_mismatches": [],
            "coverage": {"stage_attempts": 1},
        },
        "current_session_sink_alignment_summary": {
            "status": "ok",
            "final_sink_missing": {},
            "coverage": {"stage_attempts": 1},
        },
        "stage3_sink_alignment_summary": {
            "status": "warn",
            "artifact_missing_files": ["bp-1"],
            "coverage": {"stage_attempts": 1},
        },
        "patch_trace_summary": {
            "count": 1,
            "structural_attempted_count": 0,
            "strategy_counts": {"inplace_patch": 1},
        },
        "rationale_contract_summary": {
            "status": "ok",
            "retry_required_row_count": 1,
            "rows_missing_retry_context": [],
        },
        "proof_scope_summary": {
            "summary_role": "stage4_live_canary_with_stage3_sink_probe",
            "scope_status": "partial_multi_stage_probe",
            "backend_wide_proof": False,
            "covered_surfaces": ["stage4_live_context_path"],
            "uncovered_surfaces": ["backend_wide_multi_stage_runtime"],
            "errors": [],
            "warnings": ["stage3_sink_alignment_probe_warn"],
        },
    }
    right = {
        "summary_role": "stage4_live_canary_with_stage3_sink_probe",
        "hard_gates": {"status": "fail", "errors": ["final_sink_missing", "sink_alignment_status:warn"], "warnings": []},
        "sink_alignment_summary": {
            "status": "fail",
            "final_sink_missing": {"episode_production": ["attempt-1", "attempt-2"]},
            "patch_strategy_mismatches": [{"attempt_key": "a2"}],
            "coverage": {"stage_attempts": 2},
        },
        "current_session_sink_alignment_summary": {
            "status": "warn",
            "artifact_missing_files": ["ms-2"],
            "coverage": {"stage_attempts": 1},
        },
        "stage3_sink_alignment_summary": {
            "status": "ok",
            "artifact_missing_files": [],
            "coverage": {"stage_attempts": 1},
        },
        "patch_trace_summary": {
            "count": 3,
            "structural_attempted_count": 1,
            "strategy_counts": {"inplace_patch": 2, "inplace_patch_structural": 1},
        },
        "rationale_contract_summary": {
            "status": "fail",
            "retry_required_row_count": 2,
            "rows_missing_retry_context": [{"attempt_key": "a2"}],
        },
        "proof_scope_summary": {
            "summary_role": "stage4_live_canary_with_stage3_sink_probe",
            "scope_status": "fail",
            "backend_wide_proof": False,
            "covered_surfaces": ["stage4_live_context_path", "stage4_sink_alignment"],
            "uncovered_surfaces": ["backend_wide_multi_stage_runtime", "stage3_live_generation_path"],
            "errors": ["stage4_sink_alignment_status:fail"],
            "warnings": [],
        },
    }

    diff = module.build_canary_summary_diff(left, right)

    assert diff["left"]["hard_gates"]["status"] == "warn"
    assert diff["right"]["hard_gates"]["status"] == "fail"
    assert diff["delta"]["hard_gates"]["added_errors"] == ["sink_alignment_status:warn"]
    assert diff["delta"]["hard_gates"]["removed_warnings"] == ["patch_trace_not_exercised"]
    assert diff["delta"]["sink_alignment"]["primary_issue_delta"] == 2
    assert diff["delta"]["sink_alignment"]["current_session_issue_delta"] == 1
    assert diff["delta"]["sink_alignment"]["stage3_probe_issue_delta"] == -1
    assert diff["delta"]["patch_trace"]["count_delta"] == 2
    assert diff["delta"]["patch_trace"]["structural_attempted_delta"] == 1
    assert diff["delta"]["patch_trace"]["strategy_count_delta"] == {
        "inplace_patch": 1,
        "inplace_patch_structural": 1,
    }
    assert diff["delta"]["retry_required_coverage"]["required_row_delta"] == 1
    assert diff["delta"]["retry_required_coverage"]["missing_retry_context_delta"] == 1
    assert diff["delta"]["proof_status_rollup"]["status_before"] == "partial_multi_stage_probe"
    assert diff["delta"]["proof_status_rollup"]["status_after"] == "fail"
    assert diff["delta"]["proof_status_rollup"]["covered_count_delta"] == 1
    assert diff["delta"]["proof_status_rollup"]["uncovered_count_delta"] == 1


def test_diff_canary_summaries_cli_supports_stage34_and_stage3_shapes(tmp_path):
    left_path = tmp_path / "stage34.json"
    right_path = tmp_path / "stage3.json"
    left_path.write_text(
        json.dumps(
            {
                "summary_role": "stage34_frontier_live_canary",
                "multi_stage_proof_scope_summary": {
                    "summary_role": "stage34_frontier_live_proof_scope",
                    "status": "fail",
                    "covered_surfaces": [
                        "stage3_live_generation_path",
                        "stage4_live_generation_path",
                    ],
                    "uncovered_surfaces": ["backend_wide_multi_stage_runtime"],
                    "errors": ["stage4_current_session_status:warn"],
                    "warnings": [],
                },
                "stage4_canary_summary": {
                    "hard_gates": {"status": "fail", "errors": ["sink_alignment_status:warn"], "warnings": []},
                    "sink_alignment_summary": {"status": "warn", "gate_basis_mismatches": [{"attempt_key": "a1"}]},
                    "current_session_sink_alignment_summary": {"status": "warn", "artifact_missing_files": ["m1"]},
                    "stage3_sink_alignment_summary": {"status": "ok"},
                    "patch_trace_summary": {"count": 2, "strategy_counts": {"inplace_patch": 2}},
                    "rationale_contract_summary": {
                        "status": "ok",
                        "retry_required_row_count": 3,
                        "rows_missing_retry_context": [],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    right_path.write_text(
        json.dumps(
            {
                "summary_role": "stage3_only_canary",
                "episode_telemetry": [],
                "hard_gates": {"status": "pass", "errors": [], "warnings": []},
                "sink_alignment_summary": {"status": "ok", "coverage": {"stage_attempts": 8}},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/diff_canary_summaries.py",
            str(left_path),
            str(right_path),
            "--format",
            "json",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload["left"]["source_kind"] == "stage34"
    assert payload["left"]["proof_status_rollup"]["status"] == "fail"
    assert payload["right"]["source_kind"] == "stage3"
    assert payload["right"]["patch_trace"]["available"] is False
    assert payload["right"]["retry_required_coverage"]["status"] == "missing"
    assert payload["delta"]["hard_gates"]["status_before"] == "fail"
    assert payload["delta"]["hard_gates"]["status_after"] == "pass"
    assert payload["delta"]["patch_trace"]["count_delta"] == -2
    assert payload["delta"]["retry_required_coverage"]["required_row_delta"] == -3
    assert payload["delta"]["proof_status_rollup"]["status_before"] == "fail"
    assert payload["delta"]["proof_status_rollup"]["status_after"] == "not_provided"
