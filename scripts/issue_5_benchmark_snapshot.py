from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.post_benchmark_operator_comment import (
    DEFAULT_ISSUE_5_NUMBER,
    DEFAULT_ISSUE_5_REPO,
    post_issue_comment,
)
from scripts.render_benchmark_operator_comment_md import render_benchmark_operator_comment_markdown
from scripts.report_benchmark_operator_lines import (
    build_benchmark_operator_line_report,
    format_report_text,
)

DEFAULT_TITLE = "Issue #5 Benchmark Operator Snapshot"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render or post the common issue-5 benchmark snapshot preset."
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--report",
        action="store_true",
        help="emit the issue-5 snapshot as an operator report surface instead of markdown",
    )
    mode_group.add_argument(
        "--post",
        action="store_true",
        help="post the issue-5 markdown snapshot directly to GitHub",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="report output format when --report is used",
    )
    parser.add_argument(
        "--title",
        default=DEFAULT_TITLE,
        help="markdown heading for preview/post modes",
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
        "--gh-path",
        default="",
        help="optional explicit path to the GitHub CLI executable for --post",
    )
    return parser.parse_args(argv)


def build_issue_5_snapshot_payload(
    *,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
) -> dict[str, object]:
    return build_benchmark_operator_line_report(
        workspace_root=workspace_root,
        benchmark_root=benchmark_root,
        latest_live_pair=True,
    )


def build_issue_5_snapshot_markdown(
    *,
    title: str = DEFAULT_TITLE,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
) -> str:
    payload = build_issue_5_snapshot_payload(
        workspace_root=workspace_root,
        benchmark_root=benchmark_root,
    )
    return render_benchmark_operator_comment_markdown(payload, title=title)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.report:
        payload = build_issue_5_snapshot_payload(
            workspace_root=args.workspace_root,
            benchmark_root=args.benchmark_root,
        )
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(format_report_text(payload))
        return 0

    markdown = build_issue_5_snapshot_markdown(
        title=args.title,
        workspace_root=args.workspace_root,
        benchmark_root=args.benchmark_root,
    )
    if not args.post:
        print(markdown, end="")
        return 0
    response = post_issue_comment(
        repo=DEFAULT_ISSUE_5_REPO,
        issue_number=DEFAULT_ISSUE_5_NUMBER,
        markdown=markdown,
        gh_path=args.gh_path,
    )
    if response:
        print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
