import csv
import importlib.util
import json
import sqlite3
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


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "audit_stage34_cache_proof.py"
    spec = importlib.util.spec_from_file_location("audit_stage34_cache_proof", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_index(workspace: Path, rows: list[dict[str, str]]) -> None:
    index_path = workspace / "benchmarks" / "benchmark_index.csv"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _write_record(
    workspace: Path,
    *,
    run_id: str,
    stage3_attempts: int,
    stage4_attempts: int,
    llm_rows: list[dict[str, object]],
) -> Path:
    record_root = workspace / "benchmarks" / "golden-canary" / run_id
    (record_root / "snapshots").mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "recorded_at": "2026-04-24T12:00:00+09:00",
        "project_name": "golden-canary",
        "project_locator": "projects/golden-canary",
        "lane": "stage4-supervised",
        "target_ep": 15,
        "status": "completed",
        "runtime_summary": {
            "runtime_audit_tag": "stage4_complete",
            "latest_session_id": "20260424_120000",
        },
        "workspace_git": {
            "branch": "feat/execution-meta-block-impl",
            "head": "abcd1234",
            "dirty": False,
        },
        "stage_metrics": {
            "stage2": {
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
                "attempt_count": stage3_attempts,
                "pass_like_count": max(stage3_attempts - 1, 0),
                "reject_count": 1 if stage3_attempts else 0,
                "total_duration_ms": 5000,
                "avg_duration_ms": 1000 if stage3_attempts else 0,
                "total_cost_usd": 0.5,
                "total_tokens": 0,
                "latest_episode": 15,
            },
            "stage4": {
                "attempt_count": stage4_attempts,
                "pass_like_count": max(stage4_attempts - 1, 0),
                "reject_count": 1 if stage4_attempts else 0,
                "total_duration_ms": 10000,
                "avg_duration_ms": 2000 if stage4_attempts else 0,
                "total_cost_usd": 1.25,
                "total_tokens": 9000,
                "latest_episode": 15,
            },
        },
    }
    (record_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    db_path = record_root / "snapshots" / "project_data.db"
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                model TEXT,
                context_tag TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cached_tokens INTEGER,
                total_cost_usd REAL
            )
            """
        )
        for row in llm_rows:
            cur.execute(
                """
                INSERT INTO llm_calls (
                    agent_name, model, context_tag, input_tokens, output_tokens, cached_tokens, total_cost_usd
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row.get("agent_name", "")),
                    str(row.get("model", "")),
                    str(row.get("context_tag", "")),
                    int(row.get("input_tokens", 0)),
                    int(row.get("output_tokens", 0)),
                    int(row.get("cached_tokens", 0)),
                    float(row.get("total_cost_usd", 0.0)),
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return record_root


def test_audit_stage34_cache_proof_reports_stage3_stage4_proof(tmp_path):
    module = _load_module()
    run_id = "20260424_120000__stage4-supervised__target-ep15__abcd1234"
    record_root = _write_record(
        tmp_path,
        run_id=run_id,
        stage3_attempts=5,
        stage4_attempts=6,
        llm_rows=[
            {
                "agent_name": "blueprint_ensemble_generator",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "s3:ep15:a1",
                "input_tokens": 20000,
                "output_tokens": 900,
                "cached_tokens": 3200,
                "total_cost_usd": 0.12,
            },
            {
                "agent_name": "chief_writer",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "",
                "input_tokens": 60000,
                "output_tokens": 1800,
                "cached_tokens": 15000,
                "total_cost_usd": 0.45,
            },
            {
                "agent_name": "director",
                "model": "vertexai:gemini-3.1-pro-preview",
                "context_tag": "",
                "input_tokens": 1000,
                "output_tokens": 200,
                "cached_tokens": 0,
                "total_cost_usd": 0.03,
            },
        ],
    )
    _write_index(
        tmp_path,
        [
            {
                "run_id": run_id,
                "recorded_at": "2026-04-24T12:00:00+09:00",
                "project_name": "golden-canary",
                "project_locator": "projects/golden-canary",
                "lane": "stage4-supervised",
                "target_ep": "15",
                "status": "completed",
                "runtime_audit_tag": "stage4_complete",
                "latest_session_id": "20260424_120000",
                "git_branch": "main",
                "git_head": "abcd1234",
                "git_dirty": "false",
                "record_path": str(record_root.relative_to(tmp_path)),
                "notes": "",
            }
        ],
    )

    payload = module.audit_stage34_cache_proof(
        run_id,
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert payload["record"]["run_id"] == run_id
    assert payload["cache_gate"]["min_content_chars"] == 50000
    assert payload["operator_summary"]["status"] == "pass"
    assert payload["stage_proofs"]["stage3"]["proof_status"] == "proved"
    assert payload["stage_proofs"]["stage3"]["primary_cached_tokens"] == 3200
    assert payload["stage_proofs"]["stage4"]["proof_status"] == "proved"
    assert payload["stage_proofs"]["stage4"]["primary_cached_tokens"] == 15000
    assert payload["llm_call_summary"]["cached_call_count"] == 2
    assert payload["llm_call_summary"]["total_cached_tokens"] == 18200
    assert "stage4=proved" in payload["operator_report_line"]


def test_audit_stage34_cache_proof_flags_missing_primary_cache(tmp_path):
    module = _load_module()
    run_id = "20260424_130000__stage4-supervised__target-ep15__bbbb2222"
    _write_record(
        tmp_path,
        run_id=run_id,
        stage3_attempts=4,
        stage4_attempts=5,
        llm_rows=[
            {
                "agent_name": "blueprint_ensemble_generator",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "s3:ep15:a1",
                "input_tokens": 15000,
                "output_tokens": 700,
                "cached_tokens": 0,
                "total_cost_usd": 0.1,
            },
            {
                "agent_name": "chief_writer",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "",
                "input_tokens": 45000,
                "output_tokens": 1500,
                "cached_tokens": 0,
                "total_cost_usd": 0.4,
            },
            {
                "agent_name": "preflight_checker",
                "model": "vertexai:gemini-2.5-flash",
                "context_tag": "",
                "input_tokens": 5000,
                "output_tokens": 250,
                "cached_tokens": 800,
                "total_cost_usd": 0.02,
            },
        ],
    )

    payload = module.audit_stage34_cache_proof(
        run_id,
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert payload["operator_summary"]["status"] == "attention"
    assert payload["stage_proofs"]["stage3"]["proof_status"] == "attention"
    assert payload["stage_proofs"]["stage4"]["proof_status"] == "attention"
    assert payload["llm_call_summary"]["total_cached_tokens"] == 800
    assert payload["llm_call_summary"]["top_cached_agents"][0]["agent_name"] == "preflight_checker"


def test_audit_stage34_cache_proof_cli_json_with_run_id(tmp_path):
    run_id = "20260424_140000__stage4-supervised__target-ep15__cccc3333"
    record_root = _write_record(
        tmp_path,
        run_id=run_id,
        stage3_attempts=1,
        stage4_attempts=1,
        llm_rows=[
            {
                "agent_name": "blueprint_ensemble_generator",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "s3:ep15:a1",
                "input_tokens": 12000,
                "output_tokens": 500,
                "cached_tokens": 1000,
                "total_cost_usd": 0.08,
            },
            {
                "agent_name": "chief_writer",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "",
                "input_tokens": 35000,
                "output_tokens": 1200,
                "cached_tokens": 6000,
                "total_cost_usd": 0.25,
            },
        ],
    )
    _write_index(
        tmp_path,
        [
            {
                "run_id": run_id,
                "recorded_at": "2026-04-24T14:00:00+09:00",
                "project_name": "golden-canary",
                "project_locator": "projects/golden-canary",
                "lane": "stage4-supervised",
                "target_ep": "15",
                "status": "completed",
                "runtime_audit_tag": "stage4_complete",
                "latest_session_id": "20260424_140000",
                "git_branch": "main",
                "git_head": "cccc3333",
                "git_dirty": "false",
                "record_path": str(record_root.relative_to(tmp_path)),
                "notes": "",
            }
        ],
    )

    script_path = Path(__file__).resolve().parents[1] / "scripts" / "audit_stage34_cache_proof.py"
    completed = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(script_path),
            run_id,
            "--workspace-root",
            str(tmp_path),
            "--benchmark-root",
            "benchmarks",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    payload = json.loads(completed.stdout)
    assert payload["record"]["run_id"] == run_id
    assert payload["operator_summary"]["status"] == "pass"
    assert payload["stage_proofs"]["stage4"]["primary_cached_tokens"] == 6000
