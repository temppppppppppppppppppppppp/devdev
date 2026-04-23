from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.report_benchmark_operator_lines import build_benchmark_operator_line_report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a GitHub-comment-ready markdown snapshot for benchmark operator surfaces."
    )
    parser.add_argument(
        "--title",
        default="Issue #5 Benchmark Operator Snapshot",
        help="markdown heading to use for the rendered snapshot",
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
        help="explicit benchmark pair to compare and include in the markdown snapshot",
    )
    return parser.parse_args(argv)


def render_benchmark_operator_comment_markdown(payload: dict[str, object], *, title: str) -> str:
    lines = [f"## {title}", ""]
    audit_operator_report_line = str(payload.get("audit_operator_report_line", "") or "")
    summary = payload.get("summary", {})
    strict = payload.get("strict", {})

    if audit_operator_report_line:
        lines.append(f"- Audit: {audit_operator_report_line}")
    if isinstance(summary, dict):
        lines.append(
            "- Summary: "
            f"live_records={summary.get('live_records', 0)}; "
            f"records_with_missing_targets={summary.get('records_with_missing_targets', 0)}; "
            f"stale_index_rows={summary.get('stale_index_rows', 0)}"
        )
    if isinstance(strict, dict):
        lines.append(f"- Strict: {strict.get('status', 'pass')}")

    record_report_lines = payload.get("record_report_lines", [])
    if isinstance(record_report_lines, list) and record_report_lines:
        lines.extend(["", "### Live Records"])
        for item in record_report_lines:
            if isinstance(item, dict):
                lines.append(f"- {item.get('operator_report_line', '')}")

    compare_report_lines = payload.get("compare_report_lines", [])
    if isinstance(compare_report_lines, list) and compare_report_lines:
        lines.extend(["", "### Explicit Comparisons"])
        for item in compare_report_lines:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "") or "")
            operator_report_line = str(item.get("operator_report_line", "") or "")
            verdict = str(item.get("verdict", "") or "")
            changed_sections = ",".join(str(section) for section in item.get("changed_sections", []))
            tail = []
            if verdict:
                tail.append(f"verdict={verdict}")
            if changed_sections:
                tail.append(f"changed_sections={changed_sections}")
            suffix = f"; {'; '.join(tail)}" if tail else ""
            lines.append(f"- {label}: {operator_report_line}{suffix}")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_benchmark_operator_line_report(
        workspace_root=args.workspace_root,
        benchmark_root=args.benchmark_root,
        pairs=[(str(left), str(right)) for left, right in (args.pairs or [])],
    )
    print(render_benchmark_operator_comment_markdown(payload, title=args.title), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
