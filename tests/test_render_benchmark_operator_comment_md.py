import importlib.util
import subprocess
import sys
from pathlib import Path


def _load_render_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "render_benchmark_operator_comment_md.py"
    spec = importlib.util.spec_from_file_location("render_benchmark_operator_comment_md", script_path)
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


def test_render_benchmark_operator_comment_markdown_includes_sections(tmp_path):
    render_module = _load_render_module()
    helper = _load_report_test_helpers()

    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    record_a = helper._write_record(tmp_path, run_id=run_a, status="operational_failure")
    record_b = helper._write_record(tmp_path, run_id=run_b, status="completed")
    helper._write_markdown(tmp_path, "docs/2026-04-23/context.md", "# context\n")
    helper._write_sidecar(
        record_a,
        {
            "schema_version": "benchmark-companion-links-v1",
            "post_run_evidence_json": "",
            "post_run_merge_audit_md": "",
            "supporting_context_md": "docs/2026-04-23/context.md",
        },
    )
    helper._write_index(
        tmp_path,
        rows=[
            {
                "run_id": run_a,
                "recorded_at": "2026-04-23T12:00:00+09:00",
                "project_name": "golden-canary",
                "project_locator": "projects/golden-canary",
                "lane": "stage4-supervised",
                "target_ep": "15",
                "status": "operational_failure",
                "runtime_audit_tag": "stage3_complete",
                "latest_session_id": "20260423_120000",
                "git_branch": "main",
                "git_head": "aaaa1111",
                "git_dirty": "false",
                "record_path": record_a.relative_to(tmp_path).as_posix(),
                "notes": "",
            },
            {
                "run_id": run_b,
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
                "record_path": record_b.relative_to(tmp_path).as_posix(),
                "notes": "",
            },
        ],
    )

    payload = helper._load_report_module().build_benchmark_operator_line_report(
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
        pairs=[(str(record_a), str(record_b))],
    )
    markdown = render_module.render_benchmark_operator_comment_markdown(
        payload,
        title="Issue #5 Benchmark Operator Snapshot",
    )

    assert markdown.startswith("## Issue #5 Benchmark Operator Snapshot\n")
    assert "- Audit: status=clean; ci_gate=pass; gate_basis=clean; headline=no remediation needed" in markdown
    assert "- Summary: live_records=2; records_with_sidecar=1; records_with_missing_targets=0; stale_index_rows=0" in markdown
    assert "### Live Records" in markdown
    assert f"- run_id={run_a}; status=operational_failure; companion_state=linked; linked=supporting_context_md; missing=-" in markdown
    assert "### Explicit Comparisons" in markdown
    assert (
        f"- {record_a} -> {record_b}: status=clean; ci_gate=pass; gate_basis=clean; "
        "headline=no remediation needed; verdict=better; changed_sections=run_meta,stage_metrics,watchpoints"
    ) in markdown


def test_render_benchmark_operator_comment_markdown_includes_proof_signal_summary(tmp_path):
    render_module = _load_render_module()
    helper = _load_report_test_helpers()

    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    left_root = helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    right_root = helper._write_record(tmp_path, run_id=run_b, status="completed")
    merge_audit = helper._write_markdown(
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
                "Live verification:",
                "",
                "- fresh rerun `20260421_002444` -> `ep1 PASS 95`, `ep2 PASS_WITH_WARNING 95`",
                "- fresh rerun `20260421_003616` -> `ep1 PASS 95`, `ep2 FAILED`",
                "",
                "Merged addendum findings:",
                "",
                "1. first follow-up",
                "2. second follow-up",
                "3. third follow-up",
                "4. fourth follow-up",
                "",
                "Current authoritative consequence:",
                "",
                "- resolved in bounded scope",
                "- remaining blocker still exists",
                "",
                "What remains open:",
                "",
                "- nondeterministic frontier remains",
                "- later rerun regressed",
                "- mixed fresh-proof stability remains",
                "",
            ]
        ),
    )
    helper._write_sidecar(
        right_root,
        {
            "schema_version": "benchmark-companion-links-v1",
            "post_run_evidence_json": "",
            "post_run_merge_audit_md": merge_audit.relative_to(tmp_path).as_posix(),
            "supporting_context_md": "",
        },
    )

    payload = helper._load_report_module().build_benchmark_operator_line_report(
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
        pairs=[(str(left_root), str(right_root))],
    )
    markdown = render_module.render_benchmark_operator_comment_markdown(
        payload,
        title="Issue #5 Benchmark Operator Snapshot",
    )

    assert "proof_signals=right:live=mixed,open=3,blocker,addendum=4" in markdown
    assert "proof_highlights=right remaining blocker || right live verification mixed" in markdown


def test_render_benchmark_operator_comment_markdown_falls_back_to_native_proof_signals(tmp_path):
    render_module = _load_render_module()
    helper = _load_report_test_helpers()

    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    left_root = helper._write_record(tmp_path, run_id=run_a, status="operational_failure")
    right_root = helper._write_record(tmp_path, run_id=run_b, status="operational_failure")
    helper._write_guarded_result(
        left_root,
        {
            "target_ep": 15,
            "latest_written_ep_before": 10,
            "latest_written_ep_after": 10,
            "terminated_by_monitor": False,
            "termination_reason": "",
            "child_exit_code": 120,
            "benchmark_archive": {
                "run_id": run_a,
            },
        },
    )
    helper._write_guarded_result(
        right_root,
        {
            "target_ep": 15,
            "latest_written_ep_before": 10,
            "latest_written_ep_after": 11,
            "terminated_by_monitor": True,
            "termination_reason": "stage4_round_limit_exceeded",
            "child_exit_code": 1,
            "benchmark_archive": {
                "run_id": run_b,
            },
        },
    )

    payload = helper._load_report_module().build_benchmark_operator_line_report(
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
        pairs=[(str(left_root), str(right_root))],
    )
    markdown = render_module.render_benchmark_operator_comment_markdown(
        payload,
        title="Issue #5 Benchmark Operator Snapshot",
    )

    assert (
        "proof_signals=left:exit=120,gap=5; "
        "right:monitor=stage4_round_limit_exceeded,exit=1,advance=+1,gap=4"
    ) in markdown
    assert "proof_highlights=right monitor termination || left child exit 120" in markdown


def test_render_benchmark_operator_comment_md_cli_supports_title_and_pair(tmp_path):
    helper = _load_report_test_helpers()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    left_root = helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    right_root = helper._write_record(tmp_path, run_id=run_b, status="completed")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_benchmark_operator_comment_md.py",
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--title",
            "Custom Snapshot",
            "--pair",
            str(left_root),
            str(right_root),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.startswith("## Custom Snapshot\n")
    assert "### Explicit Comparisons" in result.stdout
    assert (
        f"- {left_root} -> {right_root}: status=clean; ci_gate=pass; gate_basis=clean; "
        "headline=no remediation needed; verdict=better; changed_sections=run_meta,stage_metrics,watchpoints"
    ) in result.stdout


def test_render_benchmark_operator_comment_md_cli_supports_latest_live_pair(tmp_path):
    helper = _load_report_test_helpers()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    helper._write_record(tmp_path, run_id=run_b, status="completed")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_benchmark_operator_comment_md.py",
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--latest-live-pair",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "### Explicit Comparisons" in result.stdout
    assert (
        f"- {run_a} -> {run_b}: status=clean; ci_gate=pass; gate_basis=clean; "
        "headline=no remediation needed; verdict=better; changed_sections=run_meta,stage_metrics,watchpoints"
    ) in result.stdout


def test_apply_issue_5_snapshot_defaults_enables_latest_live_pair_for_render():
    module = _load_render_module()
    args = module.argparse.Namespace(
        latest_live_pair=False,
        issue_5_snapshot=True,
    )

    resolved = module.apply_issue_5_snapshot_defaults(args)

    assert resolved.latest_live_pair is True


def test_render_benchmark_operator_comment_md_cli_supports_issue_5_snapshot(tmp_path):
    helper = _load_report_test_helpers()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    helper._write_record(tmp_path, run_id=run_a, status="interrupted")
    helper._write_record(tmp_path, run_id=run_b, status="completed")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_benchmark_operator_comment_md.py",
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--issue-5-snapshot",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.startswith("## Issue #5 Benchmark Operator Snapshot\n")
    assert (
        f"- {run_a} -> {run_b}: status=clean; ci_gate=pass; gate_basis=clean; "
        "headline=no remediation needed; verdict=better; changed_sections=run_meta,stage_metrics,watchpoints"
    ) in result.stdout
