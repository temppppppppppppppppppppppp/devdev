from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_GH_PATH = Path(r"C:\Program Files\GitHub CLI\gh.exe")

from scripts.render_benchmark_operator_comment_md import render_benchmark_operator_comment_markdown
from scripts.report_benchmark_operator_lines import build_benchmark_operator_line_report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or post a benchmark operator markdown snapshot to a GitHub issue comment."
    )
    parser.add_argument(
        "--repo",
        default="",
        help="GitHub repository in owner/name form. Required with --post.",
    )
    parser.add_argument(
        "--issue-number",
        type=int,
        default=0,
        help="GitHub issue number to comment on. Required with --post.",
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
    parser.add_argument(
        "--gh-path",
        default="",
        help="optional explicit path to the GitHub CLI executable",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="actually post the rendered markdown to the GitHub issue instead of printing a preview",
    )
    return parser.parse_args(argv)


def build_comment_markdown(
    *,
    title: str,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
    pairs: list[tuple[str, str]] | None = None,
) -> str:
    payload = build_benchmark_operator_line_report(
        workspace_root=workspace_root,
        benchmark_root=benchmark_root,
        pairs=pairs,
    )
    return render_benchmark_operator_comment_markdown(payload, title=title)


def resolve_gh_executable(explicit_path: str = "") -> str:
    if explicit_path:
        return explicit_path
    discovered = shutil.which("gh")
    if discovered:
        return discovered
    if DEFAULT_GH_PATH.exists():
        return str(DEFAULT_GH_PATH)
    raise FileNotFoundError("GitHub CLI not found; install gh or pass --gh-path")


def post_issue_comment(
    *,
    repo: str,
    issue_number: int,
    markdown: str,
    gh_path: str = "",
) -> str:
    gh_executable = resolve_gh_executable(gh_path)
    result = subprocess.run(
        [
            gh_executable,
            "issue",
            "comment",
            str(issue_number),
            "--repo",
            repo,
            "--body-file",
            "-",
        ],
        input=markdown,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    markdown = build_comment_markdown(
        title=args.title,
        workspace_root=args.workspace_root,
        benchmark_root=args.benchmark_root,
        pairs=[(str(left), str(right)) for left, right in (args.pairs or [])],
    )
    if not args.post:
        print(markdown, end="")
        return 0
    if not args.repo or int(args.issue_number or 0) <= 0:
        raise SystemExit("--repo and --issue-number are required with --post")
    response = post_issue_comment(
        repo=args.repo,
        issue_number=args.issue_number,
        markdown=markdown,
        gh_path=args.gh_path,
    )
    if response:
        print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
