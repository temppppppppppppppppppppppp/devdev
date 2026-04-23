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
    assert "- Summary: live_records=2; records_with_missing_targets=0; stale_index_rows=0" in markdown
    assert "### Live Records" in markdown
    assert f"- run_id={run_a}; status=operational_failure; companion_state=linked; linked=supporting_context_md; missing=-" in markdown
    assert "### Explicit Comparisons" in markdown
    assert (
        f"- {record_a} -> {record_b}: status=clean; ci_gate=pass; gate_basis=clean; "
        "headline=no remediation needed; verdict=better; changed_sections=run_meta,stage_metrics,watchpoints"
    ) in markdown


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
