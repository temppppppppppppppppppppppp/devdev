from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_benchmark_companion_links import audit_benchmark_companion_links
from scripts.compare_benchmark_records import compare_benchmark_records


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render one-line operator report surfaces for live benchmark records read-only."
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
    parser.add_argument(
        "--pair",
        dest="pairs",
        action="append",
        nargs=2,
        metavar=("LEFT", "RIGHT"),
        help="explicit benchmark pair to compare and render as a one-line operator surface",
    )
    return parser.parse_args(argv)


def build_benchmark_operator_line_report(
    *,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
    pairs: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    payload = audit_benchmark_companion_links(
        workspace_root=workspace_root,
        benchmark_root=benchmark_root,
    )
    record_report_lines = [
        {
            "run_id": str(record.get("run_id", "") or ""),
            "record_root": str(record.get("record_root", "") or ""),
            "operator_report_line": _build_record_operator_report_line(record),
        }
        for record in payload.get("records", [])
        if isinstance(record, dict)
    ]
    compare_report_lines = [
        _build_compare_report_entry(
            left=left,
            right=right,
            workspace_root=workspace_root,
            benchmark_root=benchmark_root,
        )
        for left, right in (pairs or [])
    ]
    return {
        "benchmark_root": payload.get("benchmark_root", ""),
        "summary": payload.get("summary", {}),
        "strict": payload.get("strict", {}),
        "audit_operator_report_line": str(payload.get("operator_report_line", "") or ""),
        "record_report_lines": record_report_lines,
        "compare_report_lines": compare_report_lines,
    }


def _build_record_operator_report_line(record: dict[str, Any]) -> str:
    linked = ",".join(str(item) for item in record.get("linked_surfaces", [])) or "-"
    missing = ",".join(str(item) for item in record.get("missing_surfaces", [])) or "-"
    bits = [
        f"run_id={record.get('run_id', '')}",
        f"status={record.get('status', '')}",
        f"companion_state={record.get('companion_state', '')}",
        f"linked={linked}",
        f"missing={missing}",
    ]
    return "; ".join(bits)


def _build_compare_report_entry(
    *,
    left: str,
    right: str,
    workspace_root: str | Path,
    benchmark_root: str | Path,
) -> dict[str, Any]:
    diff = compare_benchmark_records(
        left,
        right,
        workspace_root=workspace_root,
        benchmark_root=benchmark_root,
    )
    delta = diff.get("delta", {})
    return {
        "label": f"{left} -> {right}",
        "left_run_id": str(diff.get("left", {}).get("run_id", "") or ""),
        "right_run_id": str(diff.get("right", {}).get("run_id", "") or ""),
        "verdict": str(delta.get("verdict", "") or ""),
        "changed_sections": list(delta.get("changed_sections", [])),
        "operator_report_line": str(delta.get("operator_report_line", "") or ""),
    }


def format_report_text(payload: dict[str, Any]) -> str:
    lines = ["Benchmark Operator Report Lines"]
    audit_operator_report_line = str(payload.get("audit_operator_report_line", "") or "")
    if audit_operator_report_line:
        lines.append("Audit: " + audit_operator_report_line)
    summary = payload.get("summary", {})
    if isinstance(summary, dict):
        lines.append(
            "Summary: "
            f"live_records={summary.get('live_records', 0)}; "
            f"records_with_missing_targets={summary.get('records_with_missing_targets', 0)}; "
            f"stale_index_rows={summary.get('stale_index_rows', 0)}"
        )
    strict = payload.get("strict", {})
    if isinstance(strict, dict):
        lines.append(f"Strict: {strict.get('status', 'pass')}")
    record_report_lines = payload.get("record_report_lines", [])
    if isinstance(record_report_lines, list) and record_report_lines:
        lines.append("Records:")
        for item in record_report_lines:
            if isinstance(item, dict):
                lines.append("- " + str(item.get("operator_report_line", "") or ""))
    compare_report_lines = payload.get("compare_report_lines", [])
    if isinstance(compare_report_lines, list) and compare_report_lines:
        lines.append("Comparisons:")
        for item in compare_report_lines:
            if isinstance(item, dict):
                bits = [
                    str(item.get("label", "") or ""),
                    str(item.get("operator_report_line", "") or ""),
                    f"verdict={item.get('verdict', '')}",
                    "changed_sections=" + ",".join(str(section) for section in item.get("changed_sections", [])),
                ]
                lines.append("- " + " | ".join(bit for bit in bits if bit))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_benchmark_operator_line_report(
        workspace_root=args.workspace_root,
        benchmark_root=args.benchmark_root,
        pairs=[(str(left), str(right)) for left, right in (args.pairs or [])],
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_report_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
