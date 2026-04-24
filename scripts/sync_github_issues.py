from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    from github_issue_readiness import get_origin_remote_url, parse_github_repo_from_remote
    from sync_temp_queue_state import ROOT, TEMP, describe_path, load_execution_meta_block
except ModuleNotFoundError:  # pragma: no cover - import path depends on invocation style
    from scripts.github_issue_readiness import get_origin_remote_url, parse_github_repo_from_remote
    from scripts.sync_temp_queue_state import ROOT, TEMP, describe_path, load_execution_meta_block


DEFAULT_QUEUE_STATE_PATH = TEMP / "queue-state.json"
DEFAULT_GH_PATH = Path(r"C:\Program Files\GitHub CLI\gh.exe")
ISSUE_URL_RE = re.compile(r"/issues/(?P<number>\d+)(?:$|[/?#])")
SYNC_MARKER_PREFIX = "<!-- geuldobi-github-issue-sync:"


class GitHubIssueSyncError(RuntimeError):
    """Raised when GitHub issue sync cannot proceed safely."""


@dataclass(slots=True)
class QueueItem:
    topic: str
    temp_path: str
    canonical_path: str
    status: str
    queue_role: str
    roadmap_rank: int | None
    depends_on: list[str]


@dataclass(slots=True)
class ExistingIssue:
    number: int
    title: str
    state: str = ""
    url: str = ""
    body: str = ""


@dataclass(slots=True)
class IssueSyncAction:
    kind: str
    item: QueueItem
    issue_number: int | None = None
    title: str = ""
    body: str = ""
    reason: str = ""


def _repo_path(path: Path, *, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_repo_path(value: str, *, root: Path = ROOT) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _coerce_str(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GitHubIssueSyncError(f"queue-state item field `{field}` must be a non-empty string")
    return value.strip()


def load_queue_items(queue_state_path: Path = DEFAULT_QUEUE_STATE_PATH) -> list[QueueItem]:
    if not queue_state_path.exists():
        raise GitHubIssueSyncError(f"queue-state file not found: {queue_state_path}")
    payload = json.loads(queue_state_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != "temp-queue-state-v1":
        raise GitHubIssueSyncError(f"invalid queue-state payload: {queue_state_path}")
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise GitHubIssueSyncError("queue-state payload field `items` must be a list")

    items: list[QueueItem] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise GitHubIssueSyncError("queue-state item must be an object")
        depends_on = raw.get("depends_on", [])
        if not isinstance(depends_on, list) or any(not isinstance(dep, str) for dep in depends_on):
            raise GitHubIssueSyncError("queue-state item field `depends_on` must be a string list")
        roadmap_rank = raw.get("roadmap_rank")
        if roadmap_rank is not None and not isinstance(roadmap_rank, int):
            raise GitHubIssueSyncError("queue-state item field `roadmap_rank` must be an integer or null")
        items.append(
            QueueItem(
                topic=_coerce_str(raw.get("topic"), field="topic"),
                temp_path=_coerce_str(raw.get("temp_path"), field="temp_path"),
                canonical_path=_coerce_str(raw.get("canonical_path"), field="canonical_path"),
                status=str(raw.get("status") or "pending").strip() or "pending",
                queue_role=str(raw.get("queue_role") or "").strip(),
                roadmap_rank=roadmap_rank,
                depends_on=[dep.strip() for dep in depends_on if dep.strip()],
            )
        )
    return items


def resolve_repo_name(root: Path = ROOT, explicit_repo: str = "") -> str:
    if explicit_repo.strip():
        return explicit_repo.strip()
    remote_url = get_origin_remote_url(root)
    if remote_url is None:
        raise GitHubIssueSyncError("git remote `origin` is missing or unreadable")
    repo_name = parse_github_repo_from_remote(remote_url)
    if repo_name is None:
        raise GitHubIssueSyncError(f"`origin` remote is not a supported GitHub URL: {remote_url}")
    return repo_name


def resolve_gh_executable(explicit_path: str = "") -> str:
    if explicit_path.strip():
        return explicit_path.strip()
    discovered = shutil.which("gh")
    if discovered:
        return discovered
    if DEFAULT_GH_PATH.exists():
        return str(DEFAULT_GH_PATH)
    raise FileNotFoundError("GitHub CLI not found; install gh or pass --gh-path")


def parse_issue_number_from_url(value: str) -> int:
    match = ISSUE_URL_RE.search(value.strip())
    if match is None:
        raise GitHubIssueSyncError(f"could not parse GitHub issue number from output: {value!r}")
    return int(match.group("number"))


def _humanize_topic(topic: str) -> str:
    raw_parts = [part for part in topic.replace("_", "-").split("-") if part]
    words: list[str] = []
    index = 0
    acronyms = {
        "api": "API",
        "bi": "BI",
        "db": "DB",
        "llm": "LLM",
        "ssot": "SSOT",
        "tr": "TR",
        "ui": "UI",
    }
    while index < len(raw_parts):
        current = raw_parts[index]
        current_lower = current.lower()
        next_lower = raw_parts[index + 1].lower() if index + 1 < len(raw_parts) else ""
        if current_lower == "bi" and next_lower == "tr":
            words.append("BI/TR")
            index += 2
            continue
        words.append(acronyms.get(current_lower, current[:1].upper() + current[1:]))
        index += 1
    return " ".join(words)


def _title_prefix(item: QueueItem) -> str:
    role = item.queue_role
    status = item.status
    if role == "parked_future_wave":
        return "Parked"
    if role == "blocked_holding" or status == "blocked":
        return "Blocked"
    if status == "in_progress":
        return "Active"
    if status == "completed" or role == "historical_backing":
        return "Closed"
    return "Ready"


def render_issue_title(item: QueueItem) -> str:
    return f"[{_title_prefix(item)}] {_humanize_topic(item.topic)}"


def render_issue_body(item: QueueItem) -> str:
    depends_on = ", ".join(f"`{dep}`" for dep in item.depends_on) or "`none`"
    rank = str(item.roadmap_rank) if item.roadmap_rank is not None else "unranked"
    return "\n".join(
        [
            "<!-- geuldobi-github-issue-sync:",
            f"topic={item.topic}",
            f"canonical={item.canonical_path}",
            f"temp={item.temp_path}",
            "-->",
            "",
            "## Summary",
            "",
            "This issue mirrors a repo-side execution queue item. The repository docs remain the source of truth.",
            "",
            "## Queue State",
            "",
            f"- topic: `{item.topic}`",
            f"- status: `{item.status}`",
            f"- queue role: `{item.queue_role or 'unspecified'}`",
            f"- roadmap rank: `{rank}`",
            f"- depends on: {depends_on}",
            "",
            "## Docs",
            "",
            f"- canonical: `{item.canonical_path}`",
            f"- temp mirror: `{item.temp_path}`",
            "- roadmap: `docs/temp/execution-roadmap.md`",
            "- queue state: `docs/temp/queue-state.json`",
            "",
            "## Guardrails",
            "",
            "- Treat GitHub Issues as an external visibility mirror, not SSOT.",
            "- Update repo-side canonical docs first.",
            "- Re-run `python scripts/sync_temp_queue_state.py` and `python scripts/ops_validator.py --strict` after queue edits.",
            "",
        ]
    )


def issue_matches_topic(issue: ExistingIssue, topic: str) -> bool:
    title = issue.title
    url = issue.url
    body = issue.body
    marker_topic = f"topic={topic}"
    return (
        topic in title
        or topic in url
        or marker_topic in body
        or f"`{topic}`" in body
    )


def _execution_doc_paths(item: QueueItem, *, root: Path = ROOT) -> list[Path]:
    paths = [
        _resolve_repo_path(item.canonical_path, root=root),
        _resolve_repo_path(item.temp_path, root=root),
    ]
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def _issue_from_execution_meta(path: Path, item: QueueItem) -> int | None:
    execution_meta = load_execution_meta_block(path, expected_topic=item.topic)
    if execution_meta is None:
        raise GitHubIssueSyncError(
            f"{describe_path(path)}: missing execution metadata block; add one before GitHub issue sync"
        )
    github_issue = execution_meta.get("github_issue")
    if github_issue is None:
        return None
    if not isinstance(github_issue, int):
        raise GitHubIssueSyncError(f"{describe_path(path)}: execution_meta.github_issue must be an integer")
    return github_issue


def resolve_linked_issue_number(item: QueueItem, *, root: Path = ROOT) -> int | None:
    issue_numbers: set[int] = set()
    for path in _execution_doc_paths(item, root=root):
        if not path.exists():
            raise GitHubIssueSyncError(f"execution doc not found: {_repo_path(path, root=root)}")
        issue_number = _issue_from_execution_meta(path, item)
        if issue_number is not None:
            issue_numbers.add(issue_number)
    if len(issue_numbers) > 1:
        joined = ", ".join(str(number) for number in sorted(issue_numbers))
        raise GitHubIssueSyncError(f"{item.topic}: canonical/temp docs disagree on github_issue: {joined}")
    return next(iter(issue_numbers), None)


def _find_execution_meta_yaml_bounds(lines: list[str]) -> tuple[int, int]:
    heading_index = None
    for index, line in enumerate(lines):
        if line.strip() == "## 0. Execution Metadata Block":
            heading_index = index
            break
    if heading_index is None:
        raise GitHubIssueSyncError("missing execution metadata block")

    fence_start = None
    for index in range(heading_index + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("## ") or stripped.startswith("# "):
            break
        if stripped.startswith("```") and stripped[3:].strip().lower() in {"yaml", "yml"}:
            fence_start = index
            break
    if fence_start is None:
        raise GitHubIssueSyncError("missing execution metadata YAML fence")

    for index in range(fence_start + 1, len(lines)):
        if lines[index].strip() == "```":
            return fence_start + 1, index
    raise GitHubIssueSyncError("execution metadata YAML fence is not closed")


def write_github_issue_to_execution_doc(path: Path, issue_number: int) -> bool:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    yaml_start, yaml_end = _find_execution_meta_yaml_bounds(lines)
    issue_line_index = None
    topic_line_index = None
    for index in range(yaml_start, yaml_end):
        stripped = lines[index].strip()
        if stripped.startswith("topic:"):
            topic_line_index = index
        if stripped.startswith("github_issue:"):
            issue_line_index = index
            break
    replacement = f"  github_issue: {issue_number}"
    if issue_line_index is not None:
        if lines[issue_line_index] == replacement:
            return False
        lines[issue_line_index] = replacement
    else:
        if topic_line_index is None:
            raise GitHubIssueSyncError(f"{describe_path(path)}: execution metadata block has no topic line")
        lines.insert(topic_line_index + 1, replacement)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return True


def writeback_issue_number(item: QueueItem, issue_number: int, *, root: Path = ROOT) -> list[str]:
    changed: list[str] = []
    for path in _execution_doc_paths(item, root=root):
        if write_github_issue_to_execution_doc(path, issue_number):
            changed.append(_repo_path(path, root=root))
    return changed


class GhIssueClient:
    def __init__(self, *, repo: str, gh_path: str = "") -> None:
        self.repo = repo
        self.gh_path = resolve_gh_executable(gh_path)

    def _run(self, args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.gh_path, *args],
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def find_existing_issue(self, topic: str) -> ExistingIssue | None:
        result = self._run(
            [
                "issue",
                "list",
                "--repo",
                self.repo,
                "--state",
                "all",
                "--search",
                topic,
                "--json",
                "number,title,state,url,body",
                "--limit",
                "20",
            ]
        )
        if result.returncode != 0:
            raise GitHubIssueSyncError(result.stderr.strip() or result.stdout.strip())
        payload = json.loads(result.stdout or "[]")
        if not isinstance(payload, list):
            raise GitHubIssueSyncError("unexpected gh issue list payload")
        for raw in payload:
            if not isinstance(raw, dict):
                continue
            issue = ExistingIssue(
                number=int(raw["number"]),
                title=str(raw.get("title") or ""),
                state=str(raw.get("state") or ""),
                url=str(raw.get("url") or ""),
                body=str(raw.get("body") or ""),
            )
            if issue_matches_topic(issue, topic):
                return issue
        return None

    def create_issue(self, *, title: str, body: str) -> int:
        result = self._run(
            ["issue", "create", "--repo", self.repo, "--title", title, "--body-file", "-"],
            input_text=body,
        )
        if result.returncode != 0:
            raise GitHubIssueSyncError(result.stderr.strip() or result.stdout.strip())
        return parse_issue_number_from_url(result.stdout.strip())

    def update_issue(self, *, issue_number: int, title: str, body: str) -> None:
        result = self._run(
            [
                "issue",
                "edit",
                str(issue_number),
                "--repo",
                self.repo,
                "--title",
                title,
                "--body-file",
                "-",
            ],
            input_text=body,
        )
        if result.returncode != 0:
            raise GitHubIssueSyncError(result.stderr.strip() or result.stdout.strip())


def build_sync_actions(
    items: list[QueueItem],
    *,
    root: Path = ROOT,
    find_existing_issue: Callable[[str], ExistingIssue | None] | None = None,
    update_existing: bool = False,
) -> list[IssueSyncAction]:
    actions: list[IssueSyncAction] = []
    for item in items:
        title = render_issue_title(item)
        body = render_issue_body(item)
        try:
            linked_issue = resolve_linked_issue_number(item, root=root)
        except GitHubIssueSyncError as exc:
            actions.append(IssueSyncAction("error", item, title=title, body=body, reason=str(exc)))
            continue

        if linked_issue is not None:
            kind = "update" if update_existing else "linked"
            actions.append(IssueSyncAction(kind, item, issue_number=linked_issue, title=title, body=body))
            continue

        existing_issue = find_existing_issue(item.topic) if find_existing_issue is not None else None
        if existing_issue is not None:
            actions.append(
                IssueSyncAction(
                    "link",
                    item,
                    issue_number=existing_issue.number,
                    title=title,
                    body=body,
                    reason=f"matched existing issue: {existing_issue.title}",
                )
            )
            continue

        actions.append(IssueSyncAction("create", item, title=title, body=body))
    return actions


def emit_actions(actions: list[IssueSyncAction], *, apply: bool) -> int:
    has_error = False
    prefix = "APPLY" if apply else "DRY-RUN"
    for action in actions:
        if action.kind == "error":
            has_error = True
            print(f"ERROR: {action.item.topic}: {action.reason}")
        elif action.kind == "linked":
            print(f"{prefix}: linked #{action.issue_number}: {action.item.topic}")
        elif action.kind == "link":
            print(f"{prefix}: link #{action.issue_number}: {action.item.topic} ({action.reason})")
        elif action.kind == "create":
            print(f"{prefix}: create: {action.item.topic} -> {action.title}")
        elif action.kind == "update":
            print(f"{prefix}: update #{action.issue_number}: {action.item.topic} -> {action.title}")
        else:
            has_error = True
            print(f"ERROR: {action.item.topic}: unknown action kind {action.kind}")
    return 1 if has_error else 0


def run_repo_command(args: list[str], *, root: Path = ROOT) -> None:
    result = subprocess.run([sys.executable, *args], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        raise GitHubIssueSyncError(output or f"command failed: {args}")


def apply_actions(actions: list[IssueSyncAction], *, client: GhIssueClient, root: Path = ROOT) -> list[str]:
    changes: list[str] = []
    for action in actions:
        if action.kind == "error":
            raise GitHubIssueSyncError(f"{action.item.topic}: {action.reason}")
        if action.kind == "linked":
            continue
        if action.kind == "create":
            issue_number = client.create_issue(title=action.title, body=action.body)
            changes.extend(writeback_issue_number(action.item, issue_number, root=root))
            print(f"CREATED: #{issue_number}: {action.item.topic}")
            continue
        if action.kind == "link":
            if action.issue_number is None:
                raise GitHubIssueSyncError(f"{action.item.topic}: link action missing issue number")
            changes.extend(writeback_issue_number(action.item, action.issue_number, root=root))
            print(f"LINKED: #{action.issue_number}: {action.item.topic}")
            continue
        if action.kind == "update":
            if action.issue_number is None:
                raise GitHubIssueSyncError(f"{action.item.topic}: update action missing issue number")
            client.update_issue(issue_number=action.issue_number, title=action.title, body=action.body)
            changes.extend(writeback_issue_number(action.item, action.issue_number, root=root))
            print(f"UPDATED: #{action.issue_number}: {action.item.topic}")
            continue
        raise GitHubIssueSyncError(f"{action.item.topic}: unknown action kind {action.kind}")
    return changes


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mirror repo-side temp execution queue items into GitHub Issues."
    )
    parser.add_argument("--repo", default="", help="GitHub repository in owner/name form. Defaults from origin.")
    parser.add_argument("--queue-state-path", default=str(DEFAULT_QUEUE_STATE_PATH), help="queue-state JSON path.")
    parser.add_argument("--gh-path", default="", help="optional explicit path to the GitHub CLI executable.")
    parser.add_argument("--apply", action="store_true", help="create/link/update GitHub Issues and write back issue numbers.")
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="also replace title/body for already linked issues. Off by default to avoid clobbering hand-written issue text.",
    )
    parser.add_argument(
        "--skip-queue-refresh",
        action="store_true",
        help="do not run sync_temp_queue_state.py before reading queue-state.",
    )
    parser.add_argument(
        "--skip-ops-validation",
        action="store_true",
        help="do not run ops_validator.py --strict before or after applying.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    queue_state_path = _resolve_repo_path(str(args.queue_state_path), root=ROOT)

    try:
        if not args.skip_queue_refresh:
            run_repo_command(["scripts/sync_temp_queue_state.py"], root=ROOT)
        if not args.skip_ops_validation:
            run_repo_command(["scripts/ops_validator.py", "--strict"], root=ROOT)

        repo = resolve_repo_name(ROOT, args.repo)
        client = GhIssueClient(repo=repo, gh_path=args.gh_path)
        items = load_queue_items(queue_state_path)
        actions = build_sync_actions(
            items,
            root=ROOT,
            find_existing_issue=client.find_existing_issue,
            update_existing=bool(args.update_existing),
        )
        error_count = emit_actions(actions, apply=bool(args.apply))
        if error_count:
            return error_count
        if not args.apply:
            print("SUMMARY: dry-run only; pass --apply to mutate GitHub Issues or docs")
            return 0

        changed_paths = apply_actions(actions, client=client, root=ROOT)
        if changed_paths:
            print("WRITEBACK:")
            for path in sorted(set(changed_paths)):
                print(f"- {path}")
            run_repo_command(["scripts/sync_temp_queue_state.py"], root=ROOT)
            if not args.skip_ops_validation:
                run_repo_command(["scripts/ops_validator.py", "--strict"], root=ROOT)
        print("SUMMARY: GitHub issue sync complete")
        return 0
    except GitHubIssueSyncError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
