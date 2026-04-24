import importlib.util
import json
import sqlite3
import subprocess
import sys
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "audit_stage34_cache_gate_corpus.py"
    spec = importlib.util.spec_from_file_location("audit_stage34_cache_gate_corpus", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_audit_helpers():
    helper_path = Path(__file__).resolve().parents[1] / "tests" / "test_audit_stage34_cache_proof.py"
    spec = importlib.util.spec_from_file_location("test_audit_stage34_cache_proof", helper_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _rewrite_llm_calls_with_prompt_chars(record_root: Path, llm_rows: list[dict[str, object]]) -> None:
    db_path = record_root / "snapshots" / "project_data.db"
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS llm_calls")
        cur.execute(
            """
            CREATE TABLE llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                model TEXT,
                context_tag TEXT,
                prompt_chars INTEGER,
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
                    agent_name, model, context_tag, prompt_chars, input_tokens, output_tokens, cached_tokens, total_cost_usd
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row.get("agent_name", "")),
                    str(row.get("model", "")),
                    str(row.get("context_tag", "")),
                    int(row.get("prompt_chars", 0)),
                    int(row.get("input_tokens", 0)),
                    int(row.get("output_tokens", 0)),
                    int(row.get("cached_tokens", 0)),
                    float(row.get("total_cost_usd", 0.0)),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def test_audit_stage34_cache_gate_corpus_summarizes_gate_crossings(tmp_path):
    module = _load_module()
    helpers = _load_audit_helpers()
    run_a = "20260424_120000__stage4-supervised__target-ep15__aaaa1111"
    run_b = "20260424_130000__stage4-supervised__target-ep15__bbbb2222"
    record_a = helpers._write_record(
        tmp_path,
        run_id=run_a,
        stage3_attempts=2,
        stage4_attempts=3,
        llm_rows=[],
    )
    record_b = helpers._write_record(
        tmp_path,
        run_id=run_b,
        stage3_attempts=1,
        stage4_attempts=2,
        llm_rows=[],
    )
    _rewrite_llm_calls_with_prompt_chars(
        record_a,
        [
            {
                "agent_name": "chief_writer",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "s4",
                "prompt_chars": 62000,
                "input_tokens": 10000,
                "output_tokens": 1200,
                "cached_tokens": 2000,
                "total_cost_usd": 0.3,
            },
            {
                "agent_name": "chief_writer",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "s4",
                "prompt_chars": 42000,
                "input_tokens": 8000,
                "output_tokens": 900,
                "cached_tokens": 0,
                "total_cost_usd": 0.2,
            },
            {
                "agent_name": "blueprint_ensemble_generator",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "s3",
                "prompt_chars": 39000,
                "input_tokens": 7000,
                "output_tokens": 800,
                "cached_tokens": 500,
                "total_cost_usd": 0.15,
            },
        ],
    )
    _rewrite_llm_calls_with_prompt_chars(
        record_b,
        [
            {
                "agent_name": "chief_writer",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "s4",
                "prompt_chars": 88000,
                "input_tokens": 14000,
                "output_tokens": 1500,
                "cached_tokens": 0,
                "total_cost_usd": 0.4,
            },
            {
                "agent_name": "blueprint_ensemble_generator",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "s3",
                "prompt_chars": 39500,
                "input_tokens": 6500,
                "output_tokens": 700,
                "cached_tokens": 700,
                "total_cost_usd": 0.14,
            },
        ],
    )

    payload = module.audit_stage34_cache_gate_corpus(
        workspace_root=tmp_path,
        benchmark_root="benchmarks",
    )

    assert payload["summary"]["live_records"] == 2
    assert payload["cache_gate"]["min_content_chars"] == 50000
    assert payload["stage_summaries"]["stage4"]["records_with_attempts"] == 2
    assert payload["stage_summaries"]["stage4"]["records_with_gate_crossings"] == 2
    assert payload["stage_summaries"]["stage4"]["calls_meeting_gate"] == 2
    assert payload["stage_summaries"]["stage4"]["cached_calls_meeting_gate"] == 1
    assert payload["stage_summaries"]["stage4"]["max_prompt_chars"] == 88000
    assert payload["stage_summaries"]["stage3"]["records_with_attempts"] == 2
    assert payload["stage_summaries"]["stage3"]["records_with_gate_crossings"] == 0
    assert payload["stage_summaries"]["stage3"]["calls_meeting_gate"] == 0
    assert payload["stage_summaries"]["stage3"]["cached_calls_below_gate"] == 2
    assert "archived producer prompt_chars" in payload["operator_summary"]["headline"]
    assert "stage3 gate-records=0/2" in payload["operator_summary"]["headline"]


def test_audit_stage34_cache_gate_corpus_cli_json_accepts_explicit_records(tmp_path):
    helpers = _load_audit_helpers()
    run_id = "20260424_140000__stage4-supervised__target-ep15__cccc3333"
    record_root = helpers._write_record(
        tmp_path,
        run_id=run_id,
        stage3_attempts=1,
        stage4_attempts=1,
        llm_rows=[],
    )
    _rewrite_llm_calls_with_prompt_chars(
        record_root,
        [
            {
                "agent_name": "chief_writer",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "s4",
                "prompt_chars": 55000,
                "input_tokens": 11000,
                "output_tokens": 1300,
                "cached_tokens": 1000,
                "total_cost_usd": 0.25,
            },
            {
                "agent_name": "blueprint_ensemble_generator",
                "model": "vertexai:gemini-2.5-pro",
                "context_tag": "s3",
                "prompt_chars": 34000,
                "input_tokens": 6000,
                "output_tokens": 600,
                "cached_tokens": 0,
                "total_cost_usd": 0.1,
            },
        ],
    )

    script_path = Path(__file__).resolve().parents[1] / "scripts" / "audit_stage34_cache_gate_corpus.py"
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
    assert payload["summary"]["live_records"] == 1
    assert payload["stage_summaries"]["stage4"]["calls_meeting_gate"] == 1
    assert payload["stage_summaries"]["stage3"]["calls_meeting_gate"] == 0
    assert payload["record_rows"][0]["run_id"] == run_id
