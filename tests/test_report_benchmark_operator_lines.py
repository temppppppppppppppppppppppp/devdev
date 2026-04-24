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


def _load_report_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "report_benchmark_operator_lines.py"
    spec = importlib.util.spec_from_file_location("report_benchmark_operator_lines", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_record(workspace: Path, *, run_id: str, status: str) -> Path:
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
        "notes": "",
        "runtime_summary": {
            "runtime_audit_tag": "stage4_complete" if status == "completed" else "stage3_complete",
            "latest_session_id": "20260423_120000",
        },
        "workspace_git": {
            "branch": "main",
            "head": "aaaa1111",
            "dirty": False,
        },
        "stage_metrics": {
            "stage2": {
                "stage": "stage2",
                "source_file": "logs/pass_rate_monitor.json",
                "attempt_count": 0,
                "pass_like_count": 0,
                "reject_count": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "latest_episode": 0,
            },
            "stage3": {
                "stage": "stage3",
                "source_file": "logs/pass_rate_monitor.json",
                "attempt_count": 0,
                "pass_like_count": 0,
                "reject_count": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "latest_episode": 0,
            },
            "stage4": {
                "stage": "stage4",
                "source_file": "logs/episode_production.jsonl",
                "attempt_count": 1,
                "pass_like_count": 1 if status == "completed" else 0,
                "reject_count": 0 if status == "completed" else 1,
                "total_duration_ms": 1000,
                "avg_duration_ms": 1000,
                "total_cost_usd": 0.1,
                "total_tokens": 100,
                "latest_episode": 15 if status == "completed" else 14,
            },
        },
    }
    (record_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (record_root / "stage_metrics.csv").write_text(
        "\n".join(
            [
                "stage,source_file,attempt_count,pass_like_count,reject_count,total_duration_ms,avg_duration_ms,total_cost_usd,total_tokens,latest_episode",
                "stage2,logs/pass_rate_monitor.json,0,0,0,0,0,0.000000,0,0",
                "stage3,logs/pass_rate_monitor.json,0,0,0,0,0,0.000000,0,0",
                f"stage4,logs/episode_production.jsonl,{manifest['stage_metrics']['stage4']['attempt_count']},{manifest['stage_metrics']['stage4']['pass_like_count']},{manifest['stage_metrics']['stage4']['reject_count']},1000,1000,0.100000,100,{manifest['stage_metrics']['stage4']['latest_episode']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return record_root


def _write_index(workspace: Path, rows: list[dict[str, str]]) -> None:
    index_path = workspace / "benchmarks" / "benchmark_index.csv"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _write_sidecar(record_root: Path, payload: dict) -> None:
    (record_root / "benchmark_companion_links.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_markdown(workspace: Path, relative_path: str, body: str) -> Path:
    target = workspace / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


def test_build_benchmark_operator_line_report_surfaces_audit_and_record_lines(tmp_path):
    module = _load_report_module()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    record_a = _write_record(tmp_path, run_id=run_a, status="operational_failure")
    record_b = _write_record(tmp_path, run_id=run_b, status="completed")
    _write_markdown(tmp_path, "docs/2026-04-23/context.md", "# context\n")
    _write_sidecar(
        record_a,
        {
            "schema_version": "benchmark-companion-links-v1",
            "post_run_evidence_json": "",
            "post_run_merge_audit_md": "",
            "supporting_context_md": "docs/2026-04-23/context.md",
        },
    )
    _write_index(
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

    payload = module.build_benchmark_operator_line_report(
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert payload["audit_operator_report_line"] == (
        "status=clean; ci_gate=pass; gate_basis=clean; headline=no remediation needed"
    )
    assert payload["record_report_lines"] == [
        {
            "run_id": run_a,
            "record_root": f"benchmarks/golden-canary/{run_a}",
            "operator_report_line": (
                f"run_id={run_a}; status=operational_failure; companion_state=linked; "
                "linked=supporting_context_md; missing=-"
            ),
        },
        {
            "run_id": run_b,
            "record_root": f"benchmarks/golden-canary/{run_b}",
            "operator_report_line": (
                f"run_id={run_b}; status=completed; companion_state=no_sidecar; linked=-; missing=-"
            ),
        },
    ]
    text = module.format_report_text(payload)
    assert "Audit: status=clean; ci_gate=pass; gate_basis=clean; headline=no remediation needed" in text
    assert (
        f"run_id={run_a}; status=operational_failure; companion_state=linked; "
        "linked=supporting_context_md; missing=-"
    ) in text


def test_build_benchmark_operator_line_report_includes_explicit_compare_pairs(tmp_path):
    module = _load_report_module()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    left_root = _write_record(tmp_path, run_id=run_a, status="interrupted")
    right_root = _write_record(tmp_path, run_id=run_b, status="completed")

    payload = module.build_benchmark_operator_line_report(
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
        pairs=[(str(left_root), str(right_root))],
    )

    assert payload["compare_report_lines"] == [
        {
            "label": f"{left_root} -> {right_root}",
            "left_run_id": run_a,
            "right_run_id": run_b,
            "verdict": "better",
            "changed_sections": ["run_meta", "stage_metrics", "watchpoints"],
            "operator_report_line": (
                "status=clean; ci_gate=pass; gate_basis=clean; headline=no remediation needed"
            ),
        }
    ]
    text = module.format_report_text(payload)
    assert "Comparisons:" in text
    assert (
        f"{left_root} -> {right_root} | "
        "status=clean; ci_gate=pass; gate_basis=clean; headline=no remediation needed | "
        "verdict=better | changed_sections=run_meta,stage_metrics,watchpoints"
    ) in text


def test_build_benchmark_operator_line_report_can_append_latest_live_pair(tmp_path):
    module = _load_report_module()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    _write_record(tmp_path, run_id=run_a, status="interrupted")
    _write_record(tmp_path, run_id=run_b, status="completed")

    payload = module.build_benchmark_operator_line_report(
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
        latest_live_pair=True,
    )

    assert payload["compare_report_lines"] == [
        {
            "label": f"{run_a} -> {run_b}",
            "left_run_id": run_a,
            "right_run_id": run_b,
            "verdict": "better",
            "changed_sections": ["run_meta", "stage_metrics", "watchpoints"],
            "operator_report_line": (
                "status=clean; ci_gate=pass; gate_basis=clean; headline=no remediation needed"
            ),
        }
    ]


def test_build_benchmark_operator_line_report_surfaces_proof_signal_summary(tmp_path):
    module = _load_report_module()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    left_root = _write_record(tmp_path, run_id=run_a, status="interrupted")
    right_root = _write_record(tmp_path, run_id=run_b, status="completed")
    merge_audit = _write_markdown(
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
    _write_sidecar(
        right_root,
        {
            "schema_version": "benchmark-companion-links-v1",
            "post_run_evidence_json": "",
            "post_run_merge_audit_md": merge_audit.relative_to(tmp_path).as_posix(),
            "supporting_context_md": "",
        },
    )

    payload = module.build_benchmark_operator_line_report(
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
        pairs=[(str(left_root), str(right_root))],
    )

    assert payload["compare_report_lines"] == [
        {
            "label": f"{left_root} -> {right_root}",
            "left_run_id": run_a,
            "right_run_id": run_b,
            "verdict": "better",
            "changed_sections": ["run_meta", "stage_metrics", "watchpoints"],
            "operator_report_line": (
                "status=clean; ci_gate=warn; gate_basis=warn_watchpoints; headline=no remediation needed"
            ),
            "proof_signal_summary": "right:live=mixed,open=3,blocker,addendum=4",
            "proof_highlights": [
                "right remaining blocker",
                "right live verification mixed",
            ],
        }
    ]
    text = module.format_report_text(payload)
    assert "proof_signals=right:live=mixed,open=3,blocker,addendum=4" in text
    assert "proof_highlights=right remaining blocker || right live verification mixed" in text


def test_apply_issue_5_snapshot_defaults_enables_latest_live_pair_for_report():
    module = _load_report_module()
    args = module.argparse.Namespace(
        latest_live_pair=False,
        issue_5_snapshot=True,
    )

    resolved = module.apply_issue_5_snapshot_defaults(args)

    assert resolved.latest_live_pair is True


def test_report_benchmark_operator_lines_cli_supports_json_output(tmp_path):
    run_id = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    record_root = _write_record(tmp_path, run_id=run_id, status="completed")
    _write_sidecar(
        record_root,
        {
            "schema_version": "benchmark-companion-links-v1",
            "post_run_evidence_json": "docs/2026-04-23/missing-evidence.json",
            "post_run_merge_audit_md": "",
            "supporting_context_md": "",
        },
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/report_benchmark_operator_lines.py",
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
    assert payload["audit_operator_report_line"] == (
        "status=needs_remediation; ci_gate=fail; gate_basis=strict_failure; "
        "headline=repair post_run_evidence_json first"
    )
    assert payload["record_report_lines"] == [
        {
            "run_id": run_id,
            "record_root": f"benchmarks/golden-canary/{run_id}",
            "operator_report_line": (
                f"run_id={run_id}; status=completed; companion_state=missing_target; "
                "linked=-; missing=post_run_evidence_json"
            ),
        }
    ]


def test_report_benchmark_operator_lines_cli_supports_text_compare_rows(tmp_path):
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    left_root = _write_record(tmp_path, run_id=run_a, status="interrupted")
    right_root = _write_record(tmp_path, run_id=run_b, status="completed")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/report_benchmark_operator_lines.py",
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--pair",
            str(left_root),
            str(right_root),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Comparisons:" in result.stdout
    assert (
        f"{left_root} -> {right_root} | "
        "status=clean; ci_gate=pass; gate_basis=clean; headline=no remediation needed | "
        "verdict=better | changed_sections=run_meta,stage_metrics,watchpoints"
    ) in result.stdout


def test_report_benchmark_operator_lines_cli_supports_latest_live_pair(tmp_path):
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    _write_record(tmp_path, run_id=run_a, status="interrupted")
    _write_record(tmp_path, run_id=run_b, status="completed")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/report_benchmark_operator_lines.py",
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

    assert "Comparisons:" in result.stdout
    assert (
        f"{run_a} -> {run_b} | "
        "status=clean; ci_gate=pass; gate_basis=clean; headline=no remediation needed | "
        "verdict=better | changed_sections=run_meta,stage_metrics,watchpoints"
    ) in result.stdout


def test_report_benchmark_operator_lines_cli_supports_issue_5_snapshot(tmp_path):
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    _write_record(tmp_path, run_id=run_a, status="interrupted")
    _write_record(tmp_path, run_id=run_b, status="completed")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/report_benchmark_operator_lines.py",
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

    assert "Comparisons:" in result.stdout
    assert (
        f"{run_a} -> {run_b} | "
        "status=clean; ci_gate=pass; gate_basis=clean; headline=no remediation needed | "
        "verdict=better | changed_sections=run_meta,stage_metrics,watchpoints"
    ) in result.stdout
