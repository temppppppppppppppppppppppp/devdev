import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def _load_link_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "link_benchmark_companions.py"
    spec = importlib.util.spec_from_file_location("link_benchmark_companions", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_compare_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "compare_benchmark_records.py"
    spec = importlib.util.spec_from_file_location("compare_benchmark_records", script_path)
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
    (record_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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


def _write_evidence(workspace: Path, relative_path: str, payload: dict) -> Path:
    target = workspace / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def _write_markdown(workspace: Path, relative_path: str, body: str) -> Path:
    target = workspace / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


def test_write_benchmark_companion_links_creates_sidecar(tmp_path):
    module = _load_link_module()
    run_id = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    _write_record(tmp_path, run_id=run_id, status="completed")
    evidence = _write_evidence(
        tmp_path,
        "docs/2026-04-23/right-post-run-evidence.json",
        {"hard_gates": {"status": "fail"}},
    )
    audit = _write_markdown(tmp_path, "docs/2026-04-23/right-post-run-merge-audit.md", "# audit\n")

    result = module.write_benchmark_companion_links(
        run_id,
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
        post_run_evidence_json=evidence,
        post_run_merge_audit_md=audit,
    )

    links_path = tmp_path / result["links_path"]
    payload = json.loads(links_path.read_text(encoding="utf-8"))
    assert payload == {
        "schema_version": "benchmark-companion-links-v1",
        "post_run_evidence_json": "docs/2026-04-23/right-post-run-evidence.json",
        "post_run_merge_audit_md": "docs/2026-04-23/right-post-run-merge-audit.md",
    }


def test_compare_benchmark_records_auto_loads_sidecar_companion_links(tmp_path):
    link_module = _load_link_module()
    compare_module = _load_compare_module()
    left_run_id = "20260423_120000__stage4-supervised__target-ep15__aaaa1111"
    right_run_id = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    left_root = _write_record(tmp_path, run_id=left_run_id, status="snapshot")
    right_root = _write_record(tmp_path, run_id=right_run_id, status="completed")
    evidence = _write_evidence(
        tmp_path,
        "docs/2026-04-23/right-post-run-evidence.json",
        {
            "hard_gates": {"status": "fail"},
            "current_session_sink_alignment_summary": {"status": "warn"},
            "final_authority_contract_summary": {"status": "missing"},
        },
    )
    audit = _write_markdown(tmp_path, "docs/2026-04-23/right-post-run-merge-audit.md", "# audit\n")
    link_module.write_benchmark_companion_links(
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
        post_run_evidence_json=evidence,
        post_run_merge_audit_md=audit,
    )

    diff = compare_module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
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
        "id": "post_run_merge_audit_linked",
        "severity": "info",
        "scope": "benchmark_companion_links",
        "side": "right",
        "message": "right companion links include post_run_merge_audit_md docs/2026-04-23/right-post-run-merge-audit.md",
    } in watchpoints


def test_compare_benchmark_records_surfaces_missing_link_targets(tmp_path):
    compare_module = _load_compare_module()
    right_root = _write_record(
        tmp_path,
        run_id="20260423_130000__stage4-supervised__target-ep15__bbbb2222",
        status="completed",
    )
    (right_root / "benchmark_companion_links.json").write_text(
        json.dumps(
            {
                "schema_version": "benchmark-companion-links-v1",
                "post_run_evidence_json": "docs/2026-04-23/missing-evidence.json",
                "post_run_merge_audit_md": "docs/2026-04-23/missing-audit.md",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    left_root = _write_record(
        tmp_path,
        run_id="20260423_120000__stage4-supervised__target-ep15__aaaa1111",
        status="snapshot",
    )

    diff = compare_module.compare_benchmark_records(
        str(left_root),
        str(right_root),
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    watchpoints = diff["delta"]["watchpoints"]
    assert {
        "id": "post_run_evidence_link_missing",
        "severity": "warn",
        "scope": "benchmark_companion_links",
        "side": "right",
        "message": "right companion links reference missing post_run_evidence_json docs/2026-04-23/missing-evidence.json",
    } in watchpoints
    assert {
        "id": "post_run_merge_audit_link_missing",
        "severity": "warn",
        "scope": "benchmark_companion_links",
        "side": "right",
        "message": "right companion links reference missing post_run_merge_audit_md docs/2026-04-23/missing-audit.md",
    } in watchpoints


def test_link_benchmark_companions_cli_writes_sidecar(tmp_path):
    run_id = "20260423_130000__stage4-supervised__target-ep15__bbbb2222"
    _write_record(tmp_path, run_id=run_id, status="completed")
    evidence = _write_evidence(
        tmp_path,
        "docs/2026-04-23/right-post-run-evidence.json",
        {"hard_gates": {"status": "fail"}},
    )
    audit = _write_markdown(tmp_path, "docs/2026-04-23/right-post-run-merge-audit.md", "# audit\n")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/link_benchmark_companions.py",
            run_id,
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--post-run-evidence-json",
            str(evidence),
            "--post-run-merge-audit-md",
            str(audit),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    links_path = tmp_path / payload["links_path"]
    assert links_path.exists()
