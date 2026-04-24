from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_stage34_cache_proof import (
    PROOF_STAGE_ORDER,
    PRIMARY_STAGE_AGENTS,
    _display_relative_path,
    _resolve_benchmark_root,
    audit_stage34_cache_proof,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Stage3/Stage4 producer prompt-char pressure against the current cache gate."
    )
    parser.add_argument(
        "records",
        nargs="*",
        help="benchmark record path(s) or run_id(s). Omit to audit every live benchmark record.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format",
    )
    parser.add_argument(
        "--benchmark-root",
        default="benchmarks",
        help="benchmark archive root relative to the workspace root unless absolute",
    )
    parser.add_argument(
        "--workspace-root",
        default=str(ROOT),
        help="workspace root containing the benchmark archive",
    )
    return parser.parse_args(argv)


def audit_stage34_cache_gate_corpus(
    records: list[str] | None = None,
    *,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
) -> dict[str, Any]:
    workspace = Path(workspace_root).resolve()
    benchmark_dir = _resolve_benchmark_root(workspace, benchmark_root)
    identifiers = _resolve_record_identifiers(benchmark_dir=benchmark_dir, records=records)

    record_rows: list[dict[str, Any]] = []
    cache_gate: dict[str, Any] = {}
    gate_chars = 0
    for identifier in identifiers:
        proof_payload = audit_stage34_cache_proof(
            identifier,
            workspace_root=workspace,
            benchmark_root=benchmark_dir,
        )
        if not cache_gate:
            cache_gate = dict(proof_payload.get("cache_gate", {}))
            gate_chars = int(cache_gate.get("min_content_chars") or 0)
        record_root = workspace / str(proof_payload.get("record", {}).get("record_root", "") or "")
        prompt_char_summary = _load_stage_prompt_char_summary(
            record_root / "snapshots" / "project_data.db",
            cache_gate_chars=gate_chars,
        )
        record_rows.append(
            _build_record_row(
                proof_payload=proof_payload,
                prompt_char_summary=prompt_char_summary,
            )
        )

    stage_summaries = {
        stage: _build_stage_summary(stage=stage, record_rows=record_rows)
        for stage in PROOF_STAGE_ORDER
    }
    operator_summary = _build_operator_summary(
        live_record_count=len(record_rows),
        gate_chars=gate_chars,
        stage_summaries=stage_summaries,
    )
    payload = {
        "benchmark_root": _display_relative_path(workspace, benchmark_dir),
        "summary": {
            "live_records": len(record_rows),
        },
        "cache_gate": cache_gate,
        "stage_summaries": stage_summaries,
        "record_rows": record_rows,
        "operator_summary": operator_summary,
        "operator_report_line": _build_operator_report_line(
            live_record_count=len(record_rows),
            gate_chars=gate_chars,
            stage_summaries=stage_summaries,
        ),
    }
    return payload


def _resolve_record_identifiers(
    *,
    benchmark_dir: Path,
    records: list[str] | None,
) -> list[str]:
    if records:
        seen: set[str] = set()
        ordered: list[str] = []
        for item in records:
            text = str(item or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            ordered.append(text)
        return ordered
    return sorted(manifest_path.parent.name for manifest_path in benchmark_dir.glob("*/*/manifest.json"))


def _load_stage_prompt_char_summary(
    db_path: Path,
    *,
    cache_gate_chars: int,
) -> dict[str, Any]:
    payload = {
        "db_path": str(db_path),
        "db_exists": db_path.exists(),
        "status": "missing_db",
        "prompt_chars_available": False,
        "stages": {
            stage: _empty_stage_prompt_char_summary()
            for stage in PROOF_STAGE_ORDER
        },
    }
    if not db_path.exists():
        return payload

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        table_exists = cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'llm_calls' LIMIT 1"
        ).fetchone()
        if not table_exists:
            payload["status"] = "missing_llm_calls"
            return payload

        columns = {
            str(row[1] or "")
            for row in cur.execute("PRAGMA table_info(llm_calls)").fetchall()
        }
        if "prompt_chars" not in columns:
            payload["status"] = "missing_prompt_chars"
            return payload

        payload["status"] = "ok"
        payload["prompt_chars_available"] = True
        for stage, agents in PRIMARY_STAGE_AGENTS.items():
            placeholders = ",".join("?" for _ in agents)
            row = cur.execute(
                f"""
                SELECT
                    COUNT(*) AS call_count,
                    COALESCE(SUM(CASE WHEN prompt_chars >= ? THEN 1 ELSE 0 END), 0) AS calls_meeting_gate,
                    COALESCE(SUM(CASE WHEN prompt_chars > 0 AND prompt_chars < ? THEN 1 ELSE 0 END), 0) AS calls_below_gate,
                    COALESCE(SUM(CASE WHEN COALESCE(cached_tokens, 0) > 0 THEN 1 ELSE 0 END), 0) AS cached_call_count,
                    COALESCE(SUM(CASE WHEN COALESCE(cached_tokens, 0) > 0 AND prompt_chars >= ? THEN 1 ELSE 0 END), 0) AS cached_calls_meeting_gate,
                    COALESCE(SUM(CASE WHEN COALESCE(cached_tokens, 0) > 0 AND prompt_chars > 0 AND prompt_chars < ? THEN 1 ELSE 0 END), 0) AS cached_calls_below_gate,
                    COALESCE(SUM(COALESCE(prompt_chars, 0)), 0) AS total_prompt_chars,
                    COALESCE(MIN(COALESCE(prompt_chars, 0)), 0) AS min_prompt_chars,
                    COALESCE(MAX(COALESCE(prompt_chars, 0)), 0) AS max_prompt_chars
                FROM llm_calls
                WHERE agent_name IN ({placeholders})
                """,
                (cache_gate_chars, cache_gate_chars, cache_gate_chars, cache_gate_chars, *agents),
            ).fetchone()
            payload["stages"][stage] = {
                "call_count": int(row[0] or 0),
                "calls_meeting_gate": int(row[1] or 0),
                "calls_below_gate": int(row[2] or 0),
                "cached_call_count": int(row[3] or 0),
                "cached_calls_meeting_gate": int(row[4] or 0),
                "cached_calls_below_gate": int(row[5] or 0),
                "total_prompt_chars": int(row[6] or 0),
                "min_prompt_chars": int(row[7] or 0),
                "max_prompt_chars": int(row[8] or 0),
            }
    finally:
        conn.close()
    return payload


def _empty_stage_prompt_char_summary() -> dict[str, int]:
    return {
        "call_count": 0,
        "calls_meeting_gate": 0,
        "calls_below_gate": 0,
        "cached_call_count": 0,
        "cached_calls_meeting_gate": 0,
        "cached_calls_below_gate": 0,
        "total_prompt_chars": 0,
        "min_prompt_chars": 0,
        "max_prompt_chars": 0,
    }


def _build_record_row(
    *,
    proof_payload: dict[str, Any],
    prompt_char_summary: dict[str, Any],
) -> dict[str, Any]:
    record = proof_payload.get("record", {})
    stage_proofs = proof_payload.get("stage_proofs", {})
    rows: dict[str, Any] = {}
    for stage in PROOF_STAGE_ORDER:
        proof = stage_proofs.get(stage, {})
        prompt_stats = (prompt_char_summary.get("stages") or {}).get(stage, {})
        rows[stage] = {
            "attempt_count": int(proof.get("stage_attempt_count", 0) or 0),
            "proof_status": str(proof.get("proof_status", "") or ""),
            "primary_call_count": int(proof.get("primary_call_count", 0) or 0),
            "primary_cached_call_count": int(proof.get("primary_cached_call_count", 0) or 0),
            "primary_cached_tokens": int(proof.get("primary_cached_tokens", 0) or 0),
            "calls_meeting_gate": int(prompt_stats.get("calls_meeting_gate", 0) or 0),
            "calls_below_gate": int(prompt_stats.get("calls_below_gate", 0) or 0),
            "cached_calls_meeting_gate": int(prompt_stats.get("cached_calls_meeting_gate", 0) or 0),
            "cached_calls_below_gate": int(prompt_stats.get("cached_calls_below_gate", 0) or 0),
            "max_prompt_chars": int(prompt_stats.get("max_prompt_chars", 0) or 0),
            "min_prompt_chars": int(prompt_stats.get("min_prompt_chars", 0) or 0),
            "total_prompt_chars": int(prompt_stats.get("total_prompt_chars", 0) or 0),
        }
    return {
        "run_id": str(record.get("run_id", "") or ""),
        "record_root": str(record.get("record_root", "") or ""),
        "status": str(record.get("status", "") or ""),
        "prompt_chars_available": bool(prompt_char_summary.get("prompt_chars_available")),
        "stage_rows": rows,
    }


def _build_stage_summary(
    *,
    stage: str,
    record_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = [
        row.get("stage_rows", {}).get(stage, {})
        for row in record_rows
        if int(row.get("stage_rows", {}).get(stage, {}).get("attempt_count", 0) or 0) > 0
    ]
    if not rows:
        return {
            "records_with_attempts": 0,
            "proved_record_count": 0,
            "records_with_gate_crossings": 0,
            "records_with_cached_gate_hits": 0,
            "primary_call_count": 0,
            "primary_cached_call_count": 0,
            "calls_meeting_gate": 0,
            "calls_below_gate": 0,
            "cached_calls_meeting_gate": 0,
            "cached_calls_below_gate": 0,
            "max_prompt_chars": 0,
            "min_prompt_chars": 0,
        }

    nonzero_mins = [int(row.get("min_prompt_chars", 0) or 0) for row in rows if int(row.get("min_prompt_chars", 0) or 0) > 0]
    return {
        "records_with_attempts": len(rows),
        "proved_record_count": sum(1 for row in rows if str(row.get("proof_status", "") or "") == "proved"),
        "records_with_gate_crossings": sum(1 for row in rows if int(row.get("calls_meeting_gate", 0) or 0) > 0),
        "records_with_cached_gate_hits": sum(1 for row in rows if int(row.get("cached_calls_meeting_gate", 0) or 0) > 0),
        "primary_call_count": sum(int(row.get("primary_call_count", 0) or 0) for row in rows),
        "primary_cached_call_count": sum(int(row.get("primary_cached_call_count", 0) or 0) for row in rows),
        "calls_meeting_gate": sum(int(row.get("calls_meeting_gate", 0) or 0) for row in rows),
        "calls_below_gate": sum(int(row.get("calls_below_gate", 0) or 0) for row in rows),
        "cached_calls_meeting_gate": sum(int(row.get("cached_calls_meeting_gate", 0) or 0) for row in rows),
        "cached_calls_below_gate": sum(int(row.get("cached_calls_below_gate", 0) or 0) for row in rows),
        "max_prompt_chars": max(int(row.get("max_prompt_chars", 0) or 0) for row in rows),
        "min_prompt_chars": min(nonzero_mins) if nonzero_mins else 0,
    }


def _build_operator_summary(
    *,
    live_record_count: int,
    gate_chars: int,
    stage_summaries: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if live_record_count <= 0:
        return {
            "status": "inconclusive",
            "headline": "no live benchmark records were available for cache-gate corpus audit",
        }

    spotlight_bits: list[str] = []
    for stage in PROOF_STAGE_ORDER:
        summary = stage_summaries.get(stage, {})
        records_with_attempts = int(summary.get("records_with_attempts", 0) or 0)
        if records_with_attempts <= 0:
            continue
        gate_records = int(summary.get("records_with_gate_crossings", 0) or 0)
        cached_gate_records = int(summary.get("records_with_cached_gate_hits", 0) or 0)
        spotlight_bits.append(
            f"{stage} gate-records={gate_records}/{records_with_attempts} cached-gate-records={cached_gate_records}/{records_with_attempts}"
        )

    headline = (
        f"current {gate_chars}-char cache gate compared against archived producer prompt_chars across {live_record_count} live benchmark records"
        + (f"; {'; '.join(spotlight_bits)}" if spotlight_bits else "")
    )
    return {
        "status": "ok",
        "headline": headline,
    }


def _build_operator_report_line(
    *,
    live_record_count: int,
    gate_chars: int,
    stage_summaries: dict[str, dict[str, Any]],
) -> str:
    bits = [
        "cache_gate_prompt_pressure",
        f"live_records={live_record_count}",
        f"cache_gate={gate_chars}",
    ]
    for stage in PROOF_STAGE_ORDER:
        summary = stage_summaries.get(stage, {})
        if int(summary.get("records_with_attempts", 0) or 0) <= 0:
            continue
        bits.append(
            f"{stage}=gate_calls:{int(summary.get('calls_meeting_gate', 0) or 0)}/{int(summary.get('primary_call_count', 0) or 0)}"
        )
        bits.append(
            f"{stage}_cached_gate_calls={int(summary.get('cached_calls_meeting_gate', 0) or 0)}/{int(summary.get('primary_cached_call_count', 0) or 0)}"
        )
    return " | ".join(bits)


def _render_text(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    gate = payload.get("cache_gate", {})
    operator_summary = payload.get("operator_summary", {})
    stage_summaries = payload.get("stage_summaries", {})
    lines = [
        "Stage34 Cache Gate Corpus Audit",
        (
            "Summary: "
            f"live_records={summary.get('live_records', 0)}; "
            f"cache_gate.min_content_chars={gate.get('min_content_chars', 0)}"
        ),
        f"Operator summary: {operator_summary.get('headline', '')}",
    ]
    for stage in PROOF_STAGE_ORDER:
        stage_summary = stage_summaries.get(stage, {})
        if int(stage_summary.get("records_with_attempts", 0) or 0) <= 0:
            continue
        lines.append(
            (
                f"{stage}: "
                f"records_with_attempts={stage_summary.get('records_with_attempts', 0)}; "
                f"proved_record_count={stage_summary.get('proved_record_count', 0)}; "
                f"records_with_gate_crossings={stage_summary.get('records_with_gate_crossings', 0)}; "
                f"records_with_cached_gate_hits={stage_summary.get('records_with_cached_gate_hits', 0)}; "
                f"gate_calls={stage_summary.get('calls_meeting_gate', 0)}/{stage_summary.get('primary_call_count', 0)}; "
                f"cached_gate_calls={stage_summary.get('cached_calls_meeting_gate', 0)}/{stage_summary.get('primary_cached_call_count', 0)}; "
                f"max_prompt_chars={stage_summary.get('max_prompt_chars', 0)}; "
                f"min_prompt_chars={stage_summary.get('min_prompt_chars', 0)}"
            )
        )
    record_rows = payload.get("record_rows", [])
    if isinstance(record_rows, list) and record_rows:
        lines.append("Live records:")
        for record in record_rows:
            stage_bits: list[str] = []
            for stage in PROOF_STAGE_ORDER:
                stage_row = record.get("stage_rows", {}).get(stage, {})
                if int(stage_row.get("attempt_count", 0) or 0) <= 0:
                    continue
                stage_bits.append(
                    f"{stage}[proof={stage_row.get('proof_status', '')}; gate_calls={stage_row.get('calls_meeting_gate', 0)}/{stage_row.get('primary_call_count', 0)}; cached_gate_calls={stage_row.get('cached_calls_meeting_gate', 0)}/{stage_row.get('primary_cached_call_count', 0)}; max_prompt_chars={stage_row.get('max_prompt_chars', 0)}]"
                )
            lines.append(
                f"- run_id={record.get('run_id', '')}; status={record.get('status', '')}; " + "; ".join(stage_bits)
            )
    lines.append(f"operator_report_line: {payload.get('operator_report_line', '')}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = audit_stage34_cache_gate_corpus(
        args.records,
        workspace_root=args.workspace_root,
        benchmark_root=args.benchmark_root,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
