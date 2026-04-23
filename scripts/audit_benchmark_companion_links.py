from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_benchmark_records import (
    _coerce_record_root,
    _display_relative_path,
    _resolve_benchmark_root,
    load_benchmark_record,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit archived benchmark companion-link coverage read-only."
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
        help="benchmark archive root. Relative paths resolve from the workspace root.",
    )
    parser.add_argument(
        "--workspace-root",
        default=str(ROOT),
        help="workspace root containing the benchmark archive.",
    )
    return parser.parse_args(argv)


def audit_benchmark_companion_links(
    *,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
) -> dict[str, Any]:
    workspace = Path(workspace_root).resolve()
    benchmark_dir = _resolve_benchmark_root(workspace, benchmark_root)
    index_rows = _load_index_rows(benchmark_dir / "benchmark_index.csv")
    index_state_by_run_id = {
        entry["run_id"]: entry
        for entry in (_classify_index_row(row, workspace_root=workspace) for row in index_rows)
        if entry.get("run_id")
    }

    records: list[dict[str, Any]] = []
    live_run_ids: set[str] = set()
    for manifest_path in sorted(benchmark_dir.glob("*/*/manifest.json")):
        record = load_benchmark_record(
            str(manifest_path.parent),
            workspace_root=workspace,
            benchmark_root=benchmark_dir,
        )
        run_id = str(record.get("run_id", "") or "")
        live_run_ids.add(run_id)
        index_state = index_state_by_run_id.get(
            run_id,
            {
                "run_id": run_id,
                "record_path": "",
                "resolved_record_path": "",
                "status": "absent",
            },
        )
        companion_links = record.get("companion_links", {})
        linked_surfaces, missing_surfaces = _classify_companion_surfaces(companion_links)
        companion_state = _classify_companion_state(
            available=bool(companion_links.get("available")) if isinstance(companion_links, dict) else False,
            linked_surfaces=linked_surfaces,
            missing_surfaces=missing_surfaces,
        )
        records.append(
            {
                "run_id": run_id,
                "record_root": str(record.get("record_root", "") or ""),
                "status": str(record.get("status", "") or ""),
                "indexed": index_state.get("status") != "absent",
                "index_record_path_status": str(index_state.get("status", "absent") or "absent"),
                "index_record_path": str(index_state.get("record_path", "") or ""),
                "index_resolved_record_path": str(index_state.get("resolved_record_path", "") or ""),
                "companion_state": companion_state,
                "sidecar_path": (
                    str(companion_links.get("source_path", "") or "") if isinstance(companion_links, dict) else ""
                ),
                "linked_surfaces": linked_surfaces,
                "missing_surfaces": missing_surfaces,
            }
        )

    stale_index_rows = [
        {
            **entry,
            "live_record_present": entry.get("run_id") in live_run_ids,
        }
        for entry in index_state_by_run_id.values()
        if entry.get("status") == "stale"
    ]
    records.sort(key=lambda item: str(item.get("run_id", "")))
    stale_index_rows.sort(key=lambda item: str(item.get("run_id", "")))

    summary = {
        "indexed_rows": len(index_rows),
        "live_records": len(records),
        "stale_index_rows": len(stale_index_rows),
        "stale_index_only_rows": sum(1 for entry in stale_index_rows if not entry["live_record_present"]),
        "unindexed_live_records": sum(1 for record in records if not record["indexed"]),
        "records_with_sidecar": sum(1 for record in records if record["companion_state"] != "no_sidecar"),
        "records_with_missing_targets": sum(1 for record in records if record["companion_state"] == "missing_target"),
    }
    return {
        "benchmark_root": _display_relative_path(workspace, benchmark_dir),
        "summary": summary,
        "records": records,
        "stale_index_rows": stale_index_rows,
    }


def format_audit_text(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "Benchmark Companion-Link Audit",
        (
            "Summary: "
            f"live_records={summary.get('live_records', 0)}; "
            f"indexed_rows={summary.get('indexed_rows', 0)}; "
            f"stale_index_rows={summary.get('stale_index_rows', 0)}; "
            f"stale_index_only_rows={summary.get('stale_index_only_rows', 0)}; "
            f"unindexed_live_records={summary.get('unindexed_live_records', 0)}; "
            f"records_with_sidecar={summary.get('records_with_sidecar', 0)}; "
            f"records_with_missing_targets={summary.get('records_with_missing_targets', 0)}"
        ),
    ]
    stale_rows = payload.get("stale_index_rows", [])
    if isinstance(stale_rows, list) and stale_rows:
        lines.append("Stale index rows:")
        for entry in stale_rows:
            lines.append(
                "- "
                f"{entry.get('run_id')} -> {entry.get('resolved_record_path') or entry.get('record_path')} "
                f"(live_record_present={'yes' if entry.get('live_record_present') else 'no'})"
            )
    records = payload.get("records", [])
    if isinstance(records, list) and records:
        lines.append("Live records:")
        for record in records:
            linked = ",".join(record.get("linked_surfaces", [])) or "-"
            missing = ",".join(record.get("missing_surfaces", [])) or "-"
            lines.append(
                "- "
                f"{record.get('run_id')} [{record.get('status')}] "
                f"index={record.get('index_record_path_status')} "
                f"companion={record.get('companion_state')} "
                f"linked={linked} missing={missing}"
            )
    return "\n".join(lines)


def _load_index_rows(index_path: Path) -> list[dict[str, str]]:
    if not index_path.exists():
        return []
    with index_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _classify_index_row(row: dict[str, str], *, workspace_root: Path) -> dict[str, str]:
    run_id = str(row.get("run_id", "") or "").strip()
    record_path_raw = str(row.get("record_path", "") or "").strip()
    if not record_path_raw:
        return {
            "run_id": run_id,
            "record_path": "",
            "resolved_record_path": "",
            "status": "stale",
        }
    resolved = Path(record_path_raw)
    if not resolved.is_absolute():
        resolved = (workspace_root / resolved).resolve()
    try:
        _coerce_record_root(resolved)
        status = "ok"
    except FileNotFoundError:
        status = "stale"
    return {
        "run_id": run_id,
        "record_path": record_path_raw,
        "resolved_record_path": str(resolved),
        "status": status,
    }


def _classify_companion_surfaces(companion_links: object) -> tuple[list[str], list[str]]:
    if not isinstance(companion_links, dict):
        return [], []
    linked_surfaces: list[str] = []
    missing_surfaces: list[str] = []
    for field in ("post_run_evidence_json", "post_run_merge_audit_md", "supporting_context_md"):
        resolved_value = str(companion_links.get(f"{field}_resolved", "") or "")
        missing_value = bool(companion_links.get(f"{field}_missing"))
        if resolved_value:
            linked_surfaces.append(field)
        if missing_value:
            missing_surfaces.append(field)
    return linked_surfaces, missing_surfaces


def _classify_companion_state(
    *,
    available: bool,
    linked_surfaces: list[str],
    missing_surfaces: list[str],
) -> str:
    if not available:
        return "no_sidecar"
    if missing_surfaces:
        return "missing_target"
    if linked_surfaces:
        return "linked"
    return "empty_sidecar"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = audit_benchmark_companion_links(
        workspace_root=args.workspace_root,
        benchmark_root=args.benchmark_root,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_audit_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
