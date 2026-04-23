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
        "--strict",
        action="store_true",
        help="exit non-zero when live records reference missing companion targets",
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
        remediation_hints = _build_remediation_hints(
            run_id=run_id,
            record_root=str(record.get("record_root", "") or ""),
            companion_links=companion_links,
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
                "remediation_hints": remediation_hints,
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
    remediation_summary = _build_remediation_summary(
        [hint for record in records for hint in record.get("remediation_hints", [])]
    )
    strict_failure_reasons = _collect_strict_failure_reasons(summary)
    return {
        "benchmark_root": _display_relative_path(workspace, benchmark_dir),
        "summary": summary,
        "remediation_summary": remediation_summary,
        "strict": {
            "status": "fail" if strict_failure_reasons else "pass",
            "failure_reasons": strict_failure_reasons,
        },
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
    strict = payload.get("strict", {})
    strict_status = str(strict.get("status", "pass") or "pass") if isinstance(strict, dict) else "pass"
    lines.append(f"Strict: {strict_status}")
    strict_failures = strict.get("failure_reasons", []) if isinstance(strict, dict) else []
    if isinstance(strict_failures, list) and strict_failures:
        lines.append("Strict failures: " + ", ".join(str(item) for item in strict_failures))
    remediation_summary = payload.get("remediation_summary", {})
    if isinstance(remediation_summary, dict):
        hint_count = int(remediation_summary.get("hint_count", 0) or 0)
        count_by_surface = remediation_summary.get("count_by_surface", {})
        if hint_count > 0:
            surface_bits = [
                f"{surface}={count}"
                for surface, count in sorted(count_by_surface.items())
            ] if isinstance(count_by_surface, dict) else []
            lines.append(
                "Remediation summary: "
                f"hint_count={hint_count}"
                + (f"; count_by_surface={', '.join(surface_bits)}" if surface_bits else "")
            )
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
            remediation_hints = record.get("remediation_hints", [])
            if isinstance(remediation_hints, list):
                for hint in remediation_hints:
                    lines.append(
                        "  remediation: "
                        f"{hint.get('surface')} -> {hint.get('suggested_command')}"
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


def _collect_strict_failure_reasons(summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    missing_target_count = int(summary.get("records_with_missing_targets", 0) or 0)
    if missing_target_count > 0:
        failures.append(f"records_with_missing_targets={missing_target_count}")
    return failures


def _build_remediation_summary(remediation_hints: list[dict[str, str]]) -> dict[str, Any]:
    count_by_surface: dict[str, int] = {}
    for hint in remediation_hints:
        surface = str(hint.get("surface", "") or "")
        if not surface:
            continue
        count_by_surface[surface] = count_by_surface.get(surface, 0) + 1
    return {
        "hint_count": len(remediation_hints),
        "count_by_surface": count_by_surface,
    }


def _build_remediation_hints(
    *,
    run_id: str,
    record_root: str,
    companion_links: object,
    missing_surfaces: list[str],
) -> list[dict[str, str]]:
    if not isinstance(companion_links, dict):
        return []
    hints: list[dict[str, str]] = []
    flag_by_surface = {
        "post_run_evidence_json": "--post-run-evidence-json",
        "post_run_merge_audit_md": "--post-run-merge-audit-md",
        "supporting_context_md": "--supporting-context-md",
    }
    placeholder_by_surface = {
        "post_run_evidence_json": "<valid-json-path>",
        "post_run_merge_audit_md": "<valid-markdown-path>",
        "supporting_context_md": "<valid-markdown-path>",
    }
    for surface in missing_surfaces:
        raw_value = str(companion_links.get(surface, "") or "")
        flag = flag_by_surface.get(surface, "")
        replacement = raw_value or placeholder_by_surface.get(surface, "<valid-path>")
        if not flag:
            continue
        hints.append(
            {
                "side": "record",
                "run_id": run_id,
                "record_root": record_root,
                "surface": surface,
                "current_value": raw_value,
                "suggested_flag": flag,
                "suggested_command": (
                    f"python scripts/link_benchmark_companions.py {run_id} "
                    f"{flag} {replacement}"
                ),
            }
        )
    return hints


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
    strict = payload.get("strict", {})
    if args.strict and isinstance(strict, dict) and strict.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
