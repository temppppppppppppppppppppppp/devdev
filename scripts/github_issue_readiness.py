from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    from sync_temp_queue_state import ROOT, TEMP, describe_path, load_execution_meta_block
except ModuleNotFoundError:  # pragma: no cover - import path depends on invocation style
    from scripts.sync_temp_queue_state import ROOT, TEMP, describe_path, load_execution_meta_block

HTTPS_REMOTE_RE = re.compile(r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$")
SSH_REMOTE_RE = re.compile(r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$")


@dataclass
class ReadinessResult:
    infos: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def info(self, message: str) -> None:
        self.infos.append(message)

    def fail(self, message: str) -> None:
        self.errors.append(message)


def parse_github_repo_from_remote(remote_url: str) -> str | None:
    value = remote_url.strip()
    if not value:
        return None
    match = HTTPS_REMOTE_RE.match(value) or SSH_REMOTE_RE.match(value)
    if match is None:
        return None
    return f"{match.group('owner')}/{match.group('repo')}"


def get_origin_remote_url(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def evaluate_github_issue_readiness(root: Path = ROOT, temp: Path = TEMP) -> ReadinessResult:
    result = ReadinessResult()

    remote_url = get_origin_remote_url(root)
    if remote_url is None:
        result.fail("git remote `origin` is missing or unreadable")
        repo_name = None
    else:
        repo_name = parse_github_repo_from_remote(remote_url)
        if repo_name is None:
            result.fail(f"`origin` remote is not a supported GitHub URL: {remote_url}")
        else:
            result.info(f"origin repo detected: {repo_name}")

    exec_docs = sorted(temp.glob("*-execution-ssot.md"))
    if not exec_docs:
        result.fail("docs/temp contains no active execution SSOT mirrors")
        return result

    issue_to_topics: dict[int, list[str]] = {}
    linked_docs = 0

    for path in exec_docs:
        topic = path.name.removesuffix("-execution-ssot.md")
        try:
            execution_meta = load_execution_meta_block(path, expected_topic=topic)
        except ValueError as exc:
            result.fail(str(exc))
            continue

        if execution_meta is None:
            result.fail(
                f"{describe_path(path)}: missing execution metadata block; GitHub issue readiness requires execution_meta.github_issue"
            )
            continue

        github_issue = execution_meta.get("github_issue")
        if not isinstance(github_issue, int):
            result.fail(
                f"{describe_path(path)}: execution_meta.github_issue is missing; GitHub issue readiness requires one issue per active queue doc"
            )
            continue

        linked_docs += 1
        issue_to_topics.setdefault(github_issue, []).append(topic)
        result.info(f"{describe_path(path)}: linked to GitHub issue #{github_issue}")

    for issue_number, topics in sorted(issue_to_topics.items()):
        if len(topics) > 1:
            joined = ", ".join(sorted(topics))
            result.fail(
                f"GitHub issue #{issue_number} is referenced by multiple active queue docs: {joined}"
            )

    active_count = len(exec_docs)
    result.info(f"active execution docs: {active_count}")
    result.info(f"active docs with github_issue links: {linked_docs}")
    if repo_name is not None and not result.errors:
        result.info("GitHub issue readiness: ready for repo-local issue workflows once repository access is available")
    return result


def emit_result(result: ReadinessResult) -> int:
    for message in result.infos:
        print(f"PASS: {message}")
    for message in result.errors:
        print(f"FAIL: {message}")
    print(f"SUMMARY: errors={len(result.errors)} infos={len(result.infos)}")
    return 1 if result.errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether the active temp execution queue is locally ready for GitHub issue-driven workflows."
    )
    parser.parse_args()
    return emit_result(evaluate_github_issue_readiness())


if __name__ == "__main__":
    sys.exit(main())
