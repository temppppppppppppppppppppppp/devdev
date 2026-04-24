from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


PROOF_STAGE_ORDER = ("stage4", "stage3")
PRIMARY_STAGE_AGENTS = {
    "stage3": ("blueprint_ensemble_generator",),
    "stage4": ("chief_writer",),
}
STAGE_PRIORITY = {
    "stage4": 0,
    "stage3": 1,
}
DEFAULT_STAGE_METRIC = {
    "attempt_count": 0,
    "pass_like_count": 0,
    "reject_count": 0,
    "total_duration_ms": 0,
    "avg_duration_ms": 0,
    "total_cost_usd": 0.0,
    "total_tokens": 0,
    "latest_episode": 0,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Stage3/Stage4 producer cache proof from one archived benchmark record."
    )
    parser.add_argument("record", help="benchmark record path or run_id")
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


def audit_stage34_cache_proof(
    identifier: str,
    *,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
) -> dict[str, Any]:
    workspace = Path(workspace_root).resolve()
    benchmark_dir = _resolve_benchmark_root(workspace, benchmark_root)
    record_root, index_row = _resolve_record_root(identifier, workspace_root=workspace, benchmark_root=benchmark_dir)
    manifest = _load_json(record_root / "manifest.json")
    stage_metrics = _load_stage_metrics(manifest)
    cache_gate = _load_cache_gate(workspace)
    db_summary = _load_llm_call_cache_summary(record_root / "snapshots" / "project_data.db")

    stage_proofs = {
        stage: _build_stage_proof(
            stage=stage,
            stage_metrics=stage_metrics.get(stage, DEFAULT_STAGE_METRIC),
            db_summary=db_summary,
        )
        for stage in PROOF_STAGE_ORDER
    }
    operator_summary = _build_operator_summary(stage_proofs)

    record_summary = {
        "run_id": _pick_first_nonempty(
            manifest.get("run_id") if isinstance(manifest, dict) else None,
            index_row.get("run_id"),
            record_root.name,
        ),
        "record_root": _display_relative_path(workspace, record_root),
        "project_name": _pick_first_nonempty(
            manifest.get("project_name") if isinstance(manifest, dict) else None,
            index_row.get("project_name"),
            record_root.parent.name,
        ),
        "lane": _pick_first_nonempty(
            manifest.get("lane") if isinstance(manifest, dict) else None,
            index_row.get("lane"),
        ),
        "target_ep": _coerce_optional_int(
            _pick_first_nonempty(
                manifest.get("target_ep") if isinstance(manifest, dict) else None,
                index_row.get("target_ep"),
            )
        ),
        "status": _pick_first_nonempty(
            manifest.get("status") if isinstance(manifest, dict) else None,
            index_row.get("status"),
        ),
        "runtime_audit_tag": _pick_first_nonempty(
            (manifest.get("runtime_summary") or {}).get("runtime_audit_tag") if isinstance(manifest, dict) else None,
            index_row.get("runtime_audit_tag"),
        ),
        "latest_session_id": _pick_first_nonempty(
            (manifest.get("runtime_summary") or {}).get("latest_session_id") if isinstance(manifest, dict) else None,
            index_row.get("latest_session_id"),
        ),
    }

    payload = {
        "record": record_summary,
        "cache_gate": cache_gate,
        "llm_call_summary": db_summary,
        "stage_proofs": stage_proofs,
        "operator_summary": operator_summary,
        "operator_report_line": _build_operator_report_line(record_summary, operator_summary, stage_proofs),
    }
    return payload


def _resolve_benchmark_root(workspace_root: Path, benchmark_root: str | Path) -> Path:
    candidate = Path(benchmark_root)
    if candidate.is_absolute():
        return candidate.resolve()
    return (workspace_root / candidate).resolve()


def _resolve_record_root(
    identifier: str,
    *,
    workspace_root: Path,
    benchmark_root: Path,
) -> tuple[Path, dict[str, str]]:
    candidate = Path(identifier)
    direct_candidates = (
        candidate,
        workspace_root / candidate,
        benchmark_root / candidate,
    )
    for path in direct_candidates:
        if path.exists() and path.is_dir() and (path / "manifest.json").exists():
            return path.resolve(), {}

    index_row = _find_index_row(benchmark_root / "benchmark_index.csv", identifier)
    if index_row:
        indexed = workspace_root / index_row.get("record_path", "")
        if indexed.exists() and indexed.is_dir() and (indexed / "manifest.json").exists():
            return indexed.resolve(), index_row

    matches = [
        path.resolve()
        for path in benchmark_root.glob(f"**/{identifier}")
        if path.is_dir() and (path / "manifest.json").exists()
    ]
    if len(matches) == 1:
        return matches[0], index_row
    if len(matches) > 1:
        raise ValueError(f"multiple benchmark records matched run_id {identifier!r}")
    if index_row and index_row.get("record_path"):
        raise FileNotFoundError(
            f"stale benchmark_index.csv record_path for run_id {identifier!r}: {index_row.get('record_path', '')}"
        )
    raise FileNotFoundError(f"benchmark record not found: {identifier}")


def _find_index_row(index_path: Path, run_id: str) -> dict[str, str]:
    if not index_path.exists():
        return {}
    with index_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("run_id", "") or "").strip() == str(run_id or "").strip():
                return dict(row)
    return {}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _load_stage_metrics(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics = {}
    raw = manifest.get("stage_metrics", {}) if isinstance(manifest, dict) else {}
    if not isinstance(raw, dict):
        return metrics
    for stage, row in raw.items():
        if not isinstance(row, dict):
            continue
        metrics[str(stage)] = {
            "attempt_count": _coerce_int(row.get("attempt_count")),
            "pass_like_count": _coerce_int(row.get("pass_like_count")),
            "reject_count": _coerce_int(row.get("reject_count")),
            "total_duration_ms": _coerce_int(row.get("total_duration_ms")),
            "avg_duration_ms": _coerce_int(row.get("avg_duration_ms")),
            "total_cost_usd": _coerce_float(row.get("total_cost_usd")),
            "total_tokens": _coerce_int(row.get("total_tokens")),
            "latest_episode": _coerce_int(row.get("latest_episode")),
        }
    return metrics


def _load_cache_gate(workspace_root: Path) -> dict[str, Any]:
    system_path = workspace_root / "config" / "system.yaml"
    if not system_path.exists():
        fallback = ROOT / "config" / "system.yaml"
        if fallback.exists():
            system_path = fallback
    if not system_path.exists():
        return {
            "status": "missing",
            "source": _display_relative_path(workspace_root, system_path),
            "min_content_chars": None,
            "context_max_entries": None,
        }
    payload = yaml.safe_load(system_path.read_text(encoding="utf-8")) or {}
    cache_cfg = payload.get("cache", {}) if isinstance(payload, dict) else {}
    return {
        "status": "ok",
        "source": _display_relative_path(workspace_root, system_path),
        "min_content_chars": _coerce_optional_int(cache_cfg.get("min_content_chars")),
        "context_max_entries": _coerce_optional_int(cache_cfg.get("context_max_entries")),
    }


def _load_llm_call_cache_summary(db_path: Path) -> dict[str, Any]:
    payload = {
        "db_path": str(db_path),
        "db_exists": db_path.exists(),
        "status": "missing_db",
        "total_calls": 0,
        "cached_call_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cached_tokens": 0,
        "cached_input_share": 0.0,
        "agent_breakdown": [],
        "top_cached_agents": [],
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

        overall = cur.execute(
            """
            SELECT
                COUNT(*),
                COALESCE(SUM(CASE WHEN COALESCE(cached_tokens, 0) > 0 THEN 1 ELSE 0 END), 0),
                COALESCE(SUM(COALESCE(input_tokens, 0)), 0),
                COALESCE(SUM(COALESCE(output_tokens, 0)), 0),
                COALESCE(SUM(COALESCE(cached_tokens, 0)), 0)
            FROM llm_calls
            """
        ).fetchone()
        agent_rows = cur.execute(
            """
            SELECT
                COALESCE(agent_name, ''),
                COALESCE(model, ''),
                COUNT(*) AS call_count,
                COALESCE(SUM(COALESCE(input_tokens, 0)), 0) AS input_tokens,
                COALESCE(SUM(COALESCE(output_tokens, 0)), 0) AS output_tokens,
                COALESCE(SUM(COALESCE(cached_tokens, 0)), 0) AS cached_tokens,
                COALESCE(SUM(CASE WHEN COALESCE(cached_tokens, 0) > 0 THEN 1 ELSE 0 END), 0) AS cached_calls,
                COALESCE(SUM(COALESCE(total_cost_usd, 0.0)), 0.0) AS total_cost_usd
            FROM llm_calls
            GROUP BY COALESCE(agent_name, ''), COALESCE(model, '')
            ORDER BY cached_tokens DESC, call_count DESC, agent_name ASC
            """
        ).fetchall()
    finally:
        conn.close()

    total_input_tokens = _coerce_int(overall[2] if overall else 0)
    total_cached_tokens = _coerce_int(overall[4] if overall else 0)
    payload.update(
        {
            "status": "ok",
            "total_calls": _coerce_int(overall[0] if overall else 0),
            "cached_call_count": _coerce_int(overall[1] if overall else 0),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": _coerce_int(overall[3] if overall else 0),
            "total_cached_tokens": total_cached_tokens,
            "cached_input_share": _ratio(total_cached_tokens, total_input_tokens),
        }
    )
    for row in agent_rows:
        entry = {
            "agent_name": str(row[0] or ""),
            "model": str(row[1] or ""),
            "call_count": _coerce_int(row[2]),
            "input_tokens": _coerce_int(row[3]),
            "output_tokens": _coerce_int(row[4]),
            "cached_tokens": _coerce_int(row[5]),
            "cached_call_count": _coerce_int(row[6]),
            "cached_input_share": _ratio(row[5], row[3]),
            "total_cost_usd": round(_coerce_float(row[7]), 6),
        }
        payload["agent_breakdown"].append(entry)
    payload["top_cached_agents"] = [
        row for row in payload["agent_breakdown"] if int(row.get("cached_tokens") or 0) > 0
    ][:8]
    return payload


def _build_stage_proof(
    *,
    stage: str,
    stage_metrics: dict[str, Any],
    db_summary: dict[str, Any],
) -> dict[str, Any]:
    primary_agents = list(PRIMARY_STAGE_AGENTS.get(stage, ()))
    agent_rows = list(db_summary.get("agent_breakdown") or [])
    primary_rows = [row for row in agent_rows if row.get("agent_name") in primary_agents]
    attempt_count = _coerce_int(stage_metrics.get("attempt_count"))
    primary_call_count = sum(_coerce_int(row.get("call_count")) for row in primary_rows)
    primary_cached_call_count = sum(_coerce_int(row.get("cached_call_count")) for row in primary_rows)
    primary_input_tokens = sum(_coerce_int(row.get("input_tokens")) for row in primary_rows)
    primary_cached_tokens = sum(_coerce_int(row.get("cached_tokens")) for row in primary_rows)
    missing_agents = [agent for agent in primary_agents if agent not in {row.get("agent_name") for row in primary_rows}]
    notes: list[str] = []

    if primary_cached_tokens > 0 and primary_cached_call_count > 0:
        proof_status = "proved"
        notes.append(f"{stage} producer cache evidence observed on {', '.join(primary_agents)}")
    elif primary_call_count > 0:
        proof_status = "attention"
        notes.append(f"{stage} producer calls exist but cached_tokens stayed at 0")
    elif attempt_count > 0:
        proof_status = "attention"
        notes.append(f"{stage} attempts were recorded but no primary producer agent rows were found")
    else:
        proof_status = "not_applicable"
        notes.append(f"{stage} has no recorded attempts in this benchmark record")

    if missing_agents and proof_status != "not_applicable":
        notes.append(f"missing primary agent rows: {', '.join(missing_agents)}")

    return {
        "stage": stage,
        "stage_attempt_count": attempt_count,
        "stage_pass_like_count": _coerce_int(stage_metrics.get("pass_like_count")),
        "stage_total_duration_ms": _coerce_int(stage_metrics.get("total_duration_ms")),
        "stage_total_cost_usd": round(_coerce_float(stage_metrics.get("total_cost_usd")), 6),
        "primary_agents": primary_agents,
        "proof_status": proof_status,
        "primary_call_count": primary_call_count,
        "primary_cached_call_count": primary_cached_call_count,
        "primary_input_tokens": primary_input_tokens,
        "primary_cached_tokens": primary_cached_tokens,
        "primary_cached_input_share": _ratio(primary_cached_tokens, primary_input_tokens),
        "agent_breakdown": primary_rows,
        "notes": notes,
    }


def _build_operator_summary(stage_proofs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    expected_stages = [
        stage
        for stage, proof in stage_proofs.items()
        if _coerce_int(proof.get("stage_attempt_count")) > 0
    ]
    attention_stages = [
        stage
        for stage in expected_stages
        if str(stage_proofs[stage].get("proof_status", "")) != "proved"
    ]
    proved_stages = [
        stage
        for stage in expected_stages
        if str(stage_proofs[stage].get("proof_status", "")) == "proved"
    ]

    if not expected_stages:
        status = "inconclusive"
        headline = "no stage3/stage4 attempts were recorded in this benchmark record"
    elif not attention_stages:
        status = "pass"
        headline = "stage3/stage4 producer cache proof is present on the expected primary agents"
    else:
        status = "attention"
        highest_priority_stage = sorted(attention_stages, key=lambda item: STAGE_PRIORITY.get(item, 99))[0]
        headline = f"{highest_priority_stage} producer cache proof is still missing or unproven"

    return {
        "status": status,
        "expected_stages": expected_stages,
        "proved_stages": proved_stages,
        "attention_stages": attention_stages,
        "needs_remediation": bool(attention_stages),
        "headline": headline,
    }


def _build_operator_report_line(
    record_summary: dict[str, Any],
    operator_summary: dict[str, Any],
    stage_proofs: dict[str, dict[str, Any]],
) -> str:
    parts = [
        f"cache-proof {operator_summary.get('status', 'unknown')}",
        f"run={record_summary.get('run_id', '')}",
        f"lane={record_summary.get('lane', '')}",
    ]
    for stage in PROOF_STAGE_ORDER:
        proof = stage_proofs.get(stage, {})
        if _coerce_int(proof.get("stage_attempt_count")) <= 0:
            continue
        parts.append(
            f"{stage}={proof.get('proof_status', 'unknown')}"
            f"(cached_tokens={_coerce_int(proof.get('primary_cached_tokens'))})"
        )
    return " | ".join(parts)


def _display_relative_path(workspace_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(workspace_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _pick_first_nonempty(*values: object) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _coerce_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _coerce_float(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _coerce_optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ratio(numerator: object, denominator: object) -> float:
    top = _coerce_float(numerator)
    bottom = _coerce_float(denominator)
    if bottom <= 0:
        return 0.0
    return round(top / bottom, 6)


def _render_text(payload: dict[str, Any]) -> str:
    record = payload.get("record", {})
    gate = payload.get("cache_gate", {})
    llm_summary = payload.get("llm_call_summary", {})
    stage_proofs = payload.get("stage_proofs", {})
    operator_summary = payload.get("operator_summary", {})

    lines = [
        f"run_id: {record.get('run_id', '')}",
        f"record_root: {record.get('record_root', '')}",
        f"lane: {record.get('lane', '')}",
        f"status: {record.get('status', '')}",
        f"runtime_audit_tag: {record.get('runtime_audit_tag', '')}",
        f"cache_gate.min_content_chars: {gate.get('min_content_chars', '')}",
        (
            "llm_calls: "
            f"total={llm_summary.get('total_calls', 0)} "
            f"cached_calls={llm_summary.get('cached_call_count', 0)} "
            f"cached_tokens={llm_summary.get('total_cached_tokens', 0)} "
            f"cached_input_share={llm_summary.get('cached_input_share', 0.0):.6f}"
        ),
        (
            "operator_summary: "
            f"{operator_summary.get('status', '')} | "
            f"{operator_summary.get('headline', '')}"
        ),
        "stage proofs:",
    ]
    for stage in PROOF_STAGE_ORDER:
        proof = stage_proofs.get(stage, {})
        lines.append(
            (
                f"- {stage}: {proof.get('proof_status', '')} | "
                f"attempts={proof.get('stage_attempt_count', 0)} | "
                f"primary_agents={','.join(proof.get('primary_agents', []))} | "
                f"calls={proof.get('primary_call_count', 0)} | "
                f"cached_calls={proof.get('primary_cached_call_count', 0)} | "
                f"cached_tokens={proof.get('primary_cached_tokens', 0)} | "
                f"cached_input_share={proof.get('primary_cached_input_share', 0.0):.6f}"
            )
        )
        for note in proof.get("notes", []):
            lines.append(f"  note: {note}")
    top_cached_agents = llm_summary.get("top_cached_agents", [])
    if top_cached_agents:
        lines.append("top cached agents:")
        for row in top_cached_agents[:5]:
            lines.append(
                (
                    f"- {row.get('agent_name', '')} "
                    f"model={row.get('model', '')} "
                    f"calls={row.get('call_count', 0)} "
                    f"cached_calls={row.get('cached_call_count', 0)} "
                    f"cached_tokens={row.get('cached_tokens', 0)}"
                )
            )
    lines.append(f"operator_report_line: {payload.get('operator_report_line', '')}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = audit_stage34_cache_proof(
        args.record,
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
