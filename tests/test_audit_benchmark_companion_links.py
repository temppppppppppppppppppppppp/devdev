import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def _load_audit_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "audit_benchmark_companion_links.py"
    spec = importlib.util.spec_from_file_location("audit_benchmark_companion_links", script_path)
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
                "attempt_count": 1 if status == "completed" else 2,
                "pass_like_count": 1 if status == "completed" else 0,
                "reject_count": 0 if status == "completed" else 2,
                "total_duration_ms": 1000 if status == "completed" else 2000,
                "avg_duration_ms": 1000,
                "total_cost_usd": 0.1 if status == "completed" else 0.2,
                "total_tokens": 100 if status == "completed" else 200,
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
                f"stage4,logs/episode_production.jsonl,{manifest['stage_metrics']['stage4']['attempt_count']},{manifest['stage_metrics']['stage4']['pass_like_count']},{manifest['stage_metrics']['stage4']['reject_count']},{manifest['stage_metrics']['stage4']['total_duration_ms']},{manifest['stage_metrics']['stage4']['avg_duration_ms']},{manifest['stage_metrics']['stage4']['total_cost_usd']:.6f},{manifest['stage_metrics']['stage4']['total_tokens']},{manifest['stage_metrics']['stage4']['latest_episode']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return record_root


def _write_index(workspace: Path, rows: list[dict[str, str]]) -> None:
    index_path = workspace / "benchmarks" / "benchmark_index.csv"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
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
    with index_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(workspace: Path, relative_path: str, body: str) -> Path:
    target = workspace / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


def _write_sidecar(record_root: Path, payload: dict) -> None:
    (record_root / "benchmark_companion_links.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_audit_benchmark_companion_links_reports_stale_rows_and_link_states(tmp_path):
    module = _load_audit_module()
    run_a = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    run_c = "20260423_140000__stage4-supervised__target-ep15__cccc3333"
    record_a = _write_record(tmp_path, run_id=run_a, status="operational_failure")
    record_b = _write_record(tmp_path, run_id=run_b, status="completed")
    context = _write_markdown(tmp_path, "docs/2026-04-23/context.md", "# context\n")
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
                "record_path": f"benchmarks/stale-lane/{run_b}",
                "notes": "",
            },
            {
                "run_id": run_c,
                "recorded_at": "2026-04-23T14:00:00+09:00",
                "project_name": "golden-canary",
                "project_locator": "projects/golden-canary",
                "lane": "stage4-supervised",
                "target_ep": "15",
                "status": "completed",
                "runtime_audit_tag": "stage4_complete",
                "latest_session_id": "20260423_140000",
                "git_branch": "main",
                "git_head": "cccc3333",
                "git_dirty": "false",
                "record_path": f"benchmarks/stale-lane/{run_c}",
                "notes": "",
            },
        ],
    )

    audit = module.audit_benchmark_companion_links(
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert audit["summary"] == {
        "indexed_rows": 3,
        "live_records": 2,
        "stale_index_rows": 2,
        "stale_index_only_rows": 1,
        "unindexed_live_records": 0,
        "records_with_sidecar": 1,
        "records_with_missing_targets": 0,
    }
    assert audit["strict"] == {
        "status": "pass",
        "failure_reasons": [],
    }
    record_map = {item["run_id"]: item for item in audit["records"]}
    assert record_map[run_a]["companion_state"] == "linked"
    assert record_map[run_a]["linked_surfaces"] == ["supporting_context_md"]
    assert record_map[run_b]["index_record_path_status"] == "stale"
    assert record_map[run_b]["companion_state"] == "no_sidecar"
    stale_map = {item["run_id"]: item for item in audit["stale_index_rows"]}
    assert stale_map[run_b]["live_record_present"] is True
    assert stale_map[run_c]["live_record_present"] is False
    text = module.format_audit_text(audit)
    assert "stale_index_rows=2" in text
    assert "Strict: pass" in text
    assert f"{run_a} [operational_failure] index=ok companion=linked linked=supporting_context_md missing=-" in text


def test_audit_benchmark_companion_links_reports_missing_targets(tmp_path):
    module = _load_audit_module()
    run_id = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    record_root = _write_record(tmp_path, run_id=run_id, status="completed")
    _write_sidecar(
        record_root,
        {
            "schema_version": "benchmark-companion-links-v1",
            "post_run_evidence_json": "docs/2026-04-23/missing-evidence.json",
            "post_run_merge_audit_md": "",
            "supporting_context_md": "docs/2026-04-23/missing-context.md",
        },
    )

    audit = module.audit_benchmark_companion_links(
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert audit["summary"]["records_with_missing_targets"] == 1
    assert audit["strict"] == {
        "status": "fail",
        "failure_reasons": ["records_with_missing_targets=1"],
    }
    assert audit["remediation_summary"] == {
        "hint_count": 2,
        "count_by_surface": {
            "post_run_evidence_json": 1,
            "supporting_context_md": 1,
        },
    }
    record = audit["records"][0]
    assert record["companion_state"] == "missing_target"
    assert record["missing_surfaces"] == ["post_run_evidence_json", "supporting_context_md"]
    assert record["remediation_hints"] == [
        {
            "side": "record",
            "run_id": run_id,
            "record_root": f"benchmarks/golden-canary/{run_id}",
            "surface": "post_run_evidence_json",
            "current_value": "docs/2026-04-23/missing-evidence.json",
            "suggested_flag": "--post-run-evidence-json",
            "suggested_command": (
                "python scripts/link_benchmark_companions.py "
                f"{run_id} --post-run-evidence-json docs/2026-04-23/missing-evidence.json"
            ),
        },
        {
            "side": "record",
            "run_id": run_id,
            "record_root": f"benchmarks/golden-canary/{run_id}",
            "surface": "supporting_context_md",
            "current_value": "docs/2026-04-23/missing-context.md",
            "suggested_flag": "--supporting-context-md",
            "suggested_command": (
                "python scripts/link_benchmark_companions.py "
                f"{run_id} --supporting-context-md docs/2026-04-23/missing-context.md"
            ),
        },
    ]
    text = module.format_audit_text(audit)
    assert (
        "remediation: post_run_evidence_json -> "
        f"python scripts/link_benchmark_companions.py {run_id} "
        "--post-run-evidence-json docs/2026-04-23/missing-evidence.json"
    ) in text
    assert (
        "remediation: supporting_context_md -> "
        f"python scripts/link_benchmark_companions.py {run_id} "
        "--supporting-context-md docs/2026-04-23/missing-context.md"
    ) in text
    assert (
        "Remediation summary: hint_count=2; "
        "count_by_surface=post_run_evidence_json=1, supporting_context_md=1"
    ) in text


def test_audit_benchmark_companion_links_cli_supports_json_output(tmp_path):
    run_id = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    record_root = _write_record(tmp_path, run_id=run_id, status="completed")
    _write_markdown(tmp_path, "docs/2026-04-23/context.md", "# context\n")
    _write_sidecar(
        record_root,
        {
            "schema_version": "benchmark-companion-links-v1",
            "post_run_evidence_json": "",
            "post_run_merge_audit_md": "",
            "supporting_context_md": "docs/2026-04-23/context.md",
        },
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/audit_benchmark_companion_links.py",
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
    assert payload["summary"]["live_records"] == 1
    assert payload["records"][0]["linked_surfaces"] == ["supporting_context_md"]


def test_audit_benchmark_companion_links_cli_strict_fails_on_missing_targets(tmp_path):
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
            "scripts/audit_benchmark_companion_links.py",
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--strict",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Strict: fail" in result.stdout
    assert "records_with_missing_targets=1" in result.stdout
