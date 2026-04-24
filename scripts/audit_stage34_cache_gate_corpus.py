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
        description="Audit Stage3/Stage4 cache-gate pressure from live benchmark archives."
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
        db_path = record_root / "snapshots" / "project_data.db"
        direct_cache_summary = _load_stage_direct_cache_attempt_summary(
            db_path,
            cache_gate_chars=gate_chars,
        )
        prompt_char_summary = _load_stage_prompt_char_summary(
            db_path,
            cache_gate_chars=gate_chars,
        )
        record_rows.append(
            _build_record_row(
                proof_payload=proof_payload,
                direct_cache_summary=direct_cache_summary,
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
    return {
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


def _load_stage_direct_cache_attempt_summary(
    db_path: Path,
    *,
    cache_gate_chars: int,
) -> dict[str, Any]:
    payload = {
        "db_path": str(db_path),
        "db_exists": db_path.exists(),
        "status": "missing_db",
        "available": False,
        "stages": {
            stage: _empty_stage_direct_cache_attempt_summary()
            for stage in PROOF_STAGE_ORDER
        },
    }
    if not db_path.exists():
        return payload

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        table_exists = cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'context_cache_attempts' LIMIT 1"
        ).fetchone()
        if not table_exists:
            payload["status"] = "missing_context_cache_attempts"
            return payload

        payload["status"] = "ok"
        payload["available"] = True
        for stage, agents in PRIMARY_STAGE_AGENTS.items():
            placeholders = ",".join("?" for _ in agents)
            row = cur.execute(
                f"""
                SELECT
                    COUNT(*) AS attempt_count,
                    COALESCE(SUM(CASE WHEN content_chars >= ? THEN 1 ELSE 0 END), 0) AS attempts_meeting_gate,
                    COALESCE(SUM(CASE WHEN content_chars > 0 AND content_chars < ? THEN 1 ELSE 0 END), 0) AS attempts_below_gate,
                    COALESCE(SUM(CASE WHEN cache_outcome = 'hit' THEN 1 ELSE 0 END), 0) AS hit_count,
                    COALESCE(SUM(CASE WHEN cache_outcome = 'created' THEN 1 ELSE 0 END), 0) AS created_count,
                    COALESCE(SUM(CASE WHEN cache_outcome = 'skipped' AND cache_reason = 'content_too_short' THEN 1 ELSE 0 END), 0) AS skipped_short_count,
                    COALESCE(SUM(CASE WHEN cache_outcome = 'error' THEN 1 ELSE 0 END), 0) AS error_count,
                    COALESCE(MAX(COALESCE(content_chars, 0)), 0) AS max_content_chars,
                    COALESCE(MIN(COALESCE(content_chars, 0)), 0) AS min_content_chars
                FROM context_cache_attempts
                WHERE agent_name IN ({placeholders})
                """,
                (cache_gate_chars, cache_gate_chars, *agents),
            ).fetchone()
            skip_reason_counts = _load_stage_cache_skip_reason_counts(cur, agents=agents)
            error_reason_counts = _load_stage_cache_error_reason_counts(cur, agents=agents)
            payload["stages"][stage] = {
                "attempt_count": int(row[0] or 0),
                "attempts_meeting_gate": int(row[1] or 0),
                "attempts_below_gate": int(row[2] or 0),
                "hit_count": int(row[3] or 0),
                "created_count": int(row[4] or 0),
                "skipped_short_count": int(row[5] or 0),
                "error_count": int(row[6] or 0),
                "max_content_chars": int(row[7] or 0),
                "min_content_chars": int(row[8] or 0),
                "skip_reason_counts": skip_reason_counts,
                "skip_count": sum(skip_reason_counts.values()),
                "top_skip_reason": _pick_top_reason(skip_reason_counts),
                "error_reason_counts": error_reason_counts,
                "top_error_reason": _pick_top_reason(error_reason_counts),
            }
    finally:
        conn.close()
    return payload


def _load_stage_cache_skip_reason_counts(
    cur: sqlite3.Cursor,
    *,
    agents: list[str],
) -> dict[str, int]:
    placeholders = ",".join("?" for _ in agents)
    rows = cur.execute(
        f"""
        SELECT COALESCE(NULLIF(cache_reason, ''), 'skipped_unknown') AS cache_reason, COUNT(*) AS reason_count
        FROM context_cache_attempts
        WHERE agent_name IN ({placeholders}) AND cache_outcome = 'skipped'
        GROUP BY COALESCE(NULLIF(cache_reason, ''), 'skipped_unknown')
        ORDER BY reason_count DESC, cache_reason ASC
        """,
        (*agents,),
    ).fetchall()
    return {
        str(reason or "skipped_unknown"): int(count or 0)
        for reason, count in rows
        if int(count or 0) > 0
    }


def _load_stage_cache_error_reason_counts(
    cur: sqlite3.Cursor,
    *,
    agents: list[str],
) -> dict[str, int]:
    placeholders = ",".join("?" for _ in agents)
    rows = cur.execute(
        f"""
        SELECT cache_reason, error_msg
        FROM context_cache_attempts
        WHERE agent_name IN ({placeholders}) AND cache_outcome = 'error'
        """,
        (*agents,),
    ).fetchall()
    counts: dict[str, int] = {}
    for cache_reason, error_msg in rows:
        normalized_reason = _normalize_cache_error_reason(cache_reason, error_msg)
        counts[normalized_reason] = counts.get(normalized_reason, 0) + 1
    return counts


def _normalize_cache_error_reason(cache_reason: object, error_msg: object) -> str:
    reason = str(cache_reason or "").strip()
    if reason and reason != "cache_create_failed":
        return reason

    normalized_error = str(error_msg or "").lower()
    if "429" in normalized_error or "resource_exhausted" in normalized_error or "quota" in normalized_error:
        return "cache_create_failed_quota"
    if "timed out" in normalized_error or "timeout" in normalized_error:
        return "cache_create_failed_timeout"
    if "server disconnected" in normalized_error or "remoteprotocolerror" in normalized_error:
        return "cache_create_failed_disconnect"
    if "404" in normalized_error or "not found" in normalized_error:
        return "cache_create_failed_not_found"
    return reason or "cache_create_failed_unknown"


def _pick_top_reason(reason_counts: dict[str, int] | None) -> str:
    if not isinstance(reason_counts, dict):
        return ""
    ranked = [
        (int(count or 0), str(reason or "").strip())
        for reason, count in reason_counts.items()
        if str(reason or "").strip() and int(count or 0) > 0
    ]
    if not ranked:
        return ""
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][1]


def _empty_stage_direct_cache_attempt_summary() -> dict[str, Any]:
    return {
        "attempt_count": 0,
        "attempts_meeting_gate": 0,
        "attempts_below_gate": 0,
        "hit_count": 0,
        "created_count": 0,
        "skipped_short_count": 0,
        "error_count": 0,
        "max_content_chars": 0,
        "min_content_chars": 0,
        "skip_reason_counts": {},
        "skip_count": 0,
        "top_skip_reason": "",
        "error_reason_counts": {},
        "top_error_reason": "",
    }


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
    direct_cache_summary: dict[str, Any],
    prompt_char_summary: dict[str, Any],
) -> dict[str, Any]:
    record = proof_payload.get("record", {})
    stage_proofs = proof_payload.get("stage_proofs", {})
    rows: dict[str, Any] = {}
    for stage in PROOF_STAGE_ORDER:
        proof = stage_proofs.get(stage, {})
        direct_stats = (direct_cache_summary.get("stages") or {}).get(stage, {})
        prompt_stats = (prompt_char_summary.get("stages") or {}).get(stage, {})
        direct_attempt_count = int(direct_stats.get("attempt_count", 0) or 0)
        use_direct = direct_attempt_count > 0
        rows[stage] = {
            "attempt_count": int(proof.get("stage_attempt_count", 0) or 0),
            "proof_status": str(proof.get("proof_status", "") or ""),
            "primary_call_count": int(proof.get("primary_call_count", 0) or 0),
            "primary_cached_call_count": int(proof.get("primary_cached_call_count", 0) or 0),
            "primary_cached_tokens": int(proof.get("primary_cached_tokens", 0) or 0),
            "evidence_source": "context_cache_attempts" if use_direct else "llm_calls_prompt_proxy",
            "signal_count": direct_attempt_count if use_direct else int(prompt_stats.get("call_count", 0) or 0),
            "gate_signal_count": (
                int(direct_stats.get("attempts_meeting_gate", 0) or 0)
                if use_direct
                else int(prompt_stats.get("calls_meeting_gate", 0) or 0)
            ),
            "below_gate_signal_count": (
                int(direct_stats.get("attempts_below_gate", 0) or 0)
                if use_direct
                else int(prompt_stats.get("calls_below_gate", 0) or 0)
            ),
            "cache_success_count": (
                int(direct_stats.get("hit_count", 0) or 0) + int(direct_stats.get("created_count", 0) or 0)
                if use_direct
                else int(prompt_stats.get("cached_calls_meeting_gate", 0) or 0)
            ),
            "skipped_short_count": int(direct_stats.get("skipped_short_count", 0) or 0) if use_direct else 0,
            "skip_reason_counts": dict(direct_stats.get("skip_reason_counts", {}) or {}) if use_direct else {},
            "skip_count": int(direct_stats.get("skip_count", 0) or 0) if use_direct else 0,
            "top_skip_reason": str(direct_stats.get("top_skip_reason", "") or "") if use_direct else "",
            "error_count": int(direct_stats.get("error_count", 0) or 0) if use_direct else 0,
            "max_content_chars": (
                int(direct_stats.get("max_content_chars", 0) or 0)
                if use_direct
                else int(prompt_stats.get("max_prompt_chars", 0) or 0)
            ),
            "min_content_chars": (
                int(direct_stats.get("min_content_chars", 0) or 0)
                if use_direct
                else int(prompt_stats.get("min_prompt_chars", 0) or 0)
            ),
            "error_reason_counts": dict(direct_stats.get("error_reason_counts", {}) or {}) if use_direct else {},
            "top_error_reason": str(direct_stats.get("top_error_reason", "") or "") if use_direct else "",
        }
    return {
        "run_id": str(record.get("run_id", "") or ""),
        "record_root": str(record.get("record_root", "") or ""),
        "status": str(record.get("status", "") or ""),
        "direct_cache_attempts_available": bool(direct_cache_summary.get("available")),
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
            "evidence_source": "missing",
            "records_with_attempts": 0,
            "proved_record_count": 0,
            "records_with_direct_evidence": 0,
            "records_with_proxy_evidence": 0,
            "records_with_gate_crossings": 0,
            "records_with_cache_success": 0,
            "primary_call_count": 0,
            "primary_cached_call_count": 0,
            "signal_count": 0,
            "gate_signal_count": 0,
            "below_gate_signal_count": 0,
            "cache_success_count": 0,
            "skipped_short_count": 0,
            "error_count": 0,
            "max_content_chars": 0,
            "min_content_chars": 0,
            "skip_reason_counts": {},
            "skip_count": 0,
            "top_skip_reason": "",
            "error_reason_counts": {},
            "top_error_reason": "",
        }

    direct_rows = [row for row in rows if str(row.get("evidence_source", "")) == "context_cache_attempts"]
    proxy_rows = [row for row in rows if str(row.get("evidence_source", "")) == "llm_calls_prompt_proxy"]
    if direct_rows and proxy_rows:
        evidence_source = "mixed"
    elif direct_rows:
        evidence_source = "context_cache_attempts"
    else:
        evidence_source = "llm_calls_prompt_proxy"

    nonzero_mins = [
        int(row.get("min_content_chars", 0) or 0)
        for row in rows
        if int(row.get("min_content_chars", 0) or 0) > 0
    ]
    error_reason_counts: dict[str, int] = {}
    skip_reason_counts: dict[str, int] = {}
    for row in rows:
        for reason, count in dict(row.get("skip_reason_counts", {}) or {}).items():
            normalized_reason = str(reason or "").strip()
            normalized_count = int(count or 0)
            if not normalized_reason or normalized_count <= 0:
                continue
            skip_reason_counts[normalized_reason] = skip_reason_counts.get(normalized_reason, 0) + normalized_count
        for reason, count in dict(row.get("error_reason_counts", {}) or {}).items():
            normalized_reason = str(reason or "").strip()
            normalized_count = int(count or 0)
            if not normalized_reason or normalized_count <= 0:
                continue
            error_reason_counts[normalized_reason] = error_reason_counts.get(normalized_reason, 0) + normalized_count
    return {
        "evidence_source": evidence_source,
        "records_with_attempts": len(rows),
        "proved_record_count": sum(1 for row in rows if str(row.get("proof_status", "") or "") == "proved"),
        "records_with_direct_evidence": len(direct_rows),
        "records_with_proxy_evidence": len(proxy_rows),
        "records_with_gate_crossings": sum(1 for row in rows if int(row.get("gate_signal_count", 0) or 0) > 0),
        "records_with_cache_success": sum(1 for row in rows if int(row.get("cache_success_count", 0) or 0) > 0),
        "primary_call_count": sum(int(row.get("primary_call_count", 0) or 0) for row in rows),
        "primary_cached_call_count": sum(int(row.get("primary_cached_call_count", 0) or 0) for row in rows),
        "signal_count": sum(int(row.get("signal_count", 0) or 0) for row in rows),
        "gate_signal_count": sum(int(row.get("gate_signal_count", 0) or 0) for row in rows),
        "below_gate_signal_count": sum(int(row.get("below_gate_signal_count", 0) or 0) for row in rows),
        "cache_success_count": sum(int(row.get("cache_success_count", 0) or 0) for row in rows),
        "skipped_short_count": sum(int(row.get("skipped_short_count", 0) or 0) for row in rows),
        "skip_reason_counts": skip_reason_counts,
        "skip_count": sum(int(row.get("skip_count", 0) or 0) for row in rows),
        "top_skip_reason": _pick_top_reason(skip_reason_counts),
        "error_count": sum(int(row.get("error_count", 0) or 0) for row in rows),
        "max_content_chars": max(int(row.get("max_content_chars", 0) or 0) for row in rows),
        "min_content_chars": min(nonzero_mins) if nonzero_mins else 0,
        "error_reason_counts": error_reason_counts,
        "top_error_reason": _pick_top_reason(error_reason_counts),
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
        cache_success_records = int(summary.get("records_with_cache_success", 0) or 0)
        source = str(summary.get("evidence_source", "") or "unknown")
        if source == "context_cache_attempts":
            label = "direct"
        elif source == "llm_calls_prompt_proxy":
            label = "proxy"
        else:
            label = source
        spotlight = (
            f"{stage} {label}-gate-records={gate_records}/{records_with_attempts} "
            f"cache-success-records={cache_success_records}/{records_with_attempts}"
        )
        skip_count = int(summary.get("skip_count", 0) or 0)
        top_skip_reason = str(summary.get("top_skip_reason", "") or "")
        if skip_count > 0:
            spotlight += f" cache-skips={skip_count}"
            if top_skip_reason:
                spotlight += f"({top_skip_reason})"
        error_count = int(summary.get("error_count", 0) or 0)
        top_error_reason = str(summary.get("top_error_reason", "") or "")
        if error_count > 0:
            spotlight += f" cache-errors={error_count}"
            if top_error_reason:
                spotlight += f"({top_error_reason})"
        spotlight_bits.append(spotlight)

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
        source = str(summary.get("evidence_source", "") or "unknown")
        bits.append(
            f"{stage}[{source}]=gate:{int(summary.get('gate_signal_count', 0) or 0)}/{int(summary.get('signal_count', 0) or 0)}"
        )
        bits.append(
            f"{stage}_cache_success={int(summary.get('cache_success_count', 0) or 0)}"
        )
        skip_count = int(summary.get("skip_count", 0) or 0)
        if skip_count > 0:
            bits.append(f"{stage}_cache_skips={skip_count}")
            top_skip_reason = str(summary.get("top_skip_reason", "") or "")
            if top_skip_reason:
                bits.append(f"{stage}_top_skip_reason={top_skip_reason}")
        error_count = int(summary.get("error_count", 0) or 0)
        if error_count > 0:
            bits.append(f"{stage}_cache_errors={error_count}")
            top_error_reason = str(summary.get("top_error_reason", "") or "")
            if top_error_reason:
                bits.append(f"{stage}_top_error_reason={top_error_reason}")
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
                f"evidence_source={stage_summary.get('evidence_source', '')}; "
                f"records_with_attempts={stage_summary.get('records_with_attempts', 0)}; "
                f"proved_record_count={stage_summary.get('proved_record_count', 0)}; "
                f"records_with_gate_crossings={stage_summary.get('records_with_gate_crossings', 0)}; "
                f"records_with_cache_success={stage_summary.get('records_with_cache_success', 0)}; "
                f"signals={stage_summary.get('gate_signal_count', 0)}/{stage_summary.get('signal_count', 0)}; "
                f"cache_success={stage_summary.get('cache_success_count', 0)}; "
                f"skipped_short={stage_summary.get('skipped_short_count', 0)}; "
                f"skips={stage_summary.get('skip_count', 0)}; "
                f"top_skip_reason={stage_summary.get('top_skip_reason', '')}; "
                f"errors={stage_summary.get('error_count', 0)}; "
                f"top_error_reason={stage_summary.get('top_error_reason', '')}; "
                f"max_content_chars={stage_summary.get('max_content_chars', 0)}; "
                f"min_content_chars={stage_summary.get('min_content_chars', 0)}"
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
                    f"{stage}[proof={stage_row.get('proof_status', '')}; source={stage_row.get('evidence_source', '')}; gate={stage_row.get('gate_signal_count', 0)}/{stage_row.get('signal_count', 0)}; cache_success={stage_row.get('cache_success_count', 0)}; skipped_short={stage_row.get('skipped_short_count', 0)}; skips={stage_row.get('skip_count', 0)}; top_skip_reason={stage_row.get('top_skip_reason', '')}; errors={stage_row.get('error_count', 0)}; top_error_reason={stage_row.get('top_error_reason', '')}; max_content_chars={stage_row.get('max_content_chars', 0)}]"
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
