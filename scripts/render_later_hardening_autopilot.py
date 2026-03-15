from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANE_DOC = ROOT / "docs" / "2026-03-15" / "post-remediation-unqueued-survey-followups-execution-ssot.md"
ROADMAP_DOC = ROOT / "docs" / "2026-03-15" / "codebase-global-post-remediation-execution-roadmap.md"
QUEUE_STATE = ROOT / "docs" / "temp" / "queue-state.json"
TF_ORDER = ("TF-014", "TF-015", "TF-016", "TF-019")
TF_TITLES = {
    "TF-014": "Console Print Audit",
    "TF-015": "Ruff Auto-Fix",
    "TF-016": "Ruff Manual-Fix",
    "TF-019": "Guard Chain Config Validation",
}
PRINT_SCAN_ROOTS = (
    ROOT / "main_a.py",
    ROOT / "modules",
    ROOT / "scripts",
    ROOT / "geuldobi-desktop" / "src",
)
PRINT_SUFFIXES = {".py", ".js", ".html"}
GUARD_SURFACE_FILES = (
    ROOT / "main_a.py",
    ROOT / "modules" / "core" / "genre_guards" / "work_guard.py",
    ROOT / "modules" / "core" / "config_manager.py",
    ROOT / "modules" / "validation" / "scoring_validator.py",
    ROOT / "modules" / "validation" / "consistency_validator.py",
    ROOT / "modules" / "core" / "project_support.py",
)
GUARD_SIGNAL_RE = re.compile(
    r"(yaml\.safe_load|work_guard\.yaml|WorkGuard|_load_guard_for_genre|genre_guards)"
)


@dataclass(frozen=True)
class RuffStat:
    code: str
    count: int
    fixable_marker: str
    label: str


@dataclass(frozen=True)
class HitSummary:
    total_hits: int
    top_paths: list[tuple[int, str]]


@dataclass(frozen=True)
class Snapshot:
    head: str
    dirty_summary: str
    remaining_tfs: list[str]
    next_tf: str | None
    lane_status: str
    roadmap_status: str
    print_hits: HitSummary
    guard_hits: HitSummary
    ruff_total_errors: int | None
    ruff_fixable_errors: int | None
    ruff_stats: list[RuffStat]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _git_head() -> str:
    result = _run_command(["git", "rev-parse", "HEAD"])
    return result.stdout.strip()


def _dirty_summary() -> str:
    result = _run_command(["git", "status", "--short"])
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return "clean"
    untracked = sum(1 for line in lines if line.startswith("??"))
    deleted = sum(1 for line in lines if "D" in line[:2])
    modified = len(lines) - untracked - deleted
    return f"dirty: {modified} modified, {deleted} deleted, {untracked} untracked"


def parse_remaining_tfs(lane_text: str) -> list[str]:
    match = re.search(r"later hardening tranche(?P<tail>.*)", lane_text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        tail = match.group("tail")[:300]
        found = re.findall(r"TF-\d+", tail)
        ordered = [tf for tf in TF_ORDER if tf in found]
        if ordered:
            return ordered
    fallback = re.findall(r"TF-\d+", lane_text)
    return [tf for tf in TF_ORDER if tf in fallback]


def parse_status_field(text: str) -> str:
    match = re.search(r"^Status:\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else "unknown"


def _iter_files(roots: Iterable[Path], suffixes: set[str]) -> Iterable[Path]:
    for root in roots:
        if root.is_file():
            if root.suffix in suffixes:
                yield root
            continue
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in suffixes:
                yield path


def collect_pattern_hits(
    roots: Iterable[Path],
    suffixes: set[str],
    pattern: re.Pattern[str],
    top_limit: int = 8,
) -> HitSummary:
    total = 0
    per_path: list[tuple[int, str]] = []
    for path in _iter_files(roots, suffixes):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8-sig")
        hits = len(pattern.findall(text))
        if hits:
            total += hits
            per_path.append((hits, path.relative_to(ROOT).as_posix()))
    per_path.sort(key=lambda item: (-item[0], item[1]))
    return HitSummary(total_hits=total, top_paths=per_path[:top_limit])


def parse_ruff_statistics(output: str) -> tuple[int | None, int | None, list[RuffStat]]:
    stats: list[RuffStat] = []
    total_errors = None
    fixable_errors = None
    stat_re = re.compile(r"^\s*(\d+)\s+([A-Z0-9]+)\s+\[([^\]]+)\]\s+(.+)$")
    total_re = re.compile(r"Found\s+(\d+)\s+errors?\.")
    fixable_re = re.compile(r"\[\*\]\s+(\d+)\s+fixable")
    for line in output.splitlines():
        stripped = line.strip()
        stat_match = stat_re.match(stripped)
        if stat_match:
            count, code, marker, label = stat_match.groups()
            stats.append(
                RuffStat(
                    code=code,
                    count=int(count),
                    fixable_marker=marker,
                    label=label,
                )
            )
            continue
        total_match = total_re.search(stripped)
        if total_match:
            total_errors = int(total_match.group(1))
            continue
        fixable_match = fixable_re.search(stripped)
        if fixable_match:
            fixable_errors = int(fixable_match.group(1))
    return total_errors, fixable_errors, stats


def collect_ruff_snapshot() -> tuple[int | None, int | None, list[RuffStat]]:
    result = _run_command(["ruff", "check", "modules", "scripts", "main_a.py", "--statistics"])
    combined = "\n".join(part for part in (result.stdout, result.stderr) if part)
    return parse_ruff_statistics(combined)


def collect_snapshot() -> Snapshot:
    lane_text = _read_text(LANE_DOC)
    roadmap_text = _read_text(ROADMAP_DOC)
    remaining_tfs = parse_remaining_tfs(lane_text)
    next_tf = remaining_tfs[0] if remaining_tfs else None
    print_hits = collect_pattern_hits(
        PRINT_SCAN_ROOTS,
        PRINT_SUFFIXES,
        re.compile(r"\bprint\s*\("),
        top_limit=10,
    )
    guard_hits = collect_pattern_hits(
        GUARD_SURFACE_FILES,
        {".py"},
        GUARD_SIGNAL_RE,
        top_limit=10,
    )
    ruff_total_errors, ruff_fixable_errors, ruff_stats = collect_ruff_snapshot()
    return Snapshot(
        head=_git_head(),
        dirty_summary=_dirty_summary(),
        remaining_tfs=remaining_tfs,
        next_tf=next_tf,
        lane_status=parse_status_field(lane_text),
        roadmap_status=parse_status_field(roadmap_text),
        print_hits=print_hits,
        guard_hits=guard_hits,
        ruff_total_errors=ruff_total_errors,
        ruff_fixable_errors=ruff_fixable_errors,
        ruff_stats=ruff_stats,
    )


def _format_top_paths(paths: list[tuple[int, str]]) -> str:
    if not paths:
        return "none"
    return ", ".join(f"{path} ({count})" for count, path in paths)


def build_prompt(snapshot: Snapshot) -> str:
    remaining_lines = "\n".join(
        f"{index}. {tf} {TF_TITLES.get(tf, '')}".rstrip()
        for index, tf in enumerate(snapshot.remaining_tfs, start=1)
    )
    ruff_lines = "\n".join(
        f"- {stat.code}: {stat.count} [{stat.fixable_marker}] {stat.label}"
        for stat in snapshot.ruff_stats
    )
    return "\n".join(
        [
            "# Post-Remediation Later Hardening Autopilot",
            "",
            f"- HEAD: `{snapshot.head}`",
            f"- Worktree: `{snapshot.dirty_summary}`",
            f"- Residual lane status: `{snapshot.lane_status}`",
            f"- Roadmap status: `{snapshot.roadmap_status}`",
            f"- Next TF: `{snapshot.next_tf or 'none'}`",
            "",
            "## Live Drift",
            f"- Remaining TF order: {', '.join(snapshot.remaining_tfs) if snapshot.remaining_tfs else 'none'}",
            (
                f"- Ruff live snapshot: `{snapshot.ruff_total_errors}` errors / "
                f"`{snapshot.ruff_fixable_errors}` fixable"
                if snapshot.ruff_total_errors is not None
                else "- Ruff live snapshot: unavailable"
            ),
            f"- Raw print inventory: `{snapshot.print_hits.total_hits}` hits; top paths: {_format_top_paths(snapshot.print_hits.top_paths)}",
            f"- Guard-config surface signals: `{snapshot.guard_hits.total_hits}` hits; top paths: {_format_top_paths(snapshot.guard_hits.top_paths)}",
            "",
            "## Copy-Paste Prompt",
            "```text",
            "You are Codex operating in c:\\Users\\User\\Desktop\\글도비.",
            "",
            "Treat this as system-track queue realization. The governing docs are:",
            "- AGENTS.md",
            "- docs/implementation/system-order-init-harness.md",
            "- docs/implementation/document-3pass-audit-harness.md",
            "- docs/implementation/temp-execution-queue-roadmap-harness.md",
            "- docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md",
            "- docs/2026-03-15/post-remediation-unqueued-survey-followups-3pass-audit.md",
            "- docs/2026-03-15/codebase-global-post-remediation-execution-roadmap.md",
            "- docs/temp/queue-state.json",
            "",
            "Current live drift:",
            f"- HEAD: {snapshot.head}",
            f"- Worktree: {snapshot.dirty_summary}",
            (
                f"- Ruff: {snapshot.ruff_total_errors} errors, {snapshot.ruff_fixable_errors} fixable"
                if snapshot.ruff_total_errors is not None
                else "- Ruff: unavailable"
            ),
            f"- Raw print inventory: {snapshot.print_hits.total_hits} hits",
            f"- Guard-config signals: {snapshot.guard_hits.total_hits} hits",
            "",
            "Execute only this order:",
            remaining_lines or "1. no remaining TFs",
            "",
            "For each TF, run the same bounded loop:",
            "1. Re-audit the current workspace with a fresh 3-pass review of the governing canonical doc and confirm confidence >= 95%.",
            "2. If the item is now a no-op or decision-only item, save the decision and close it without broad code churn.",
            "3. If code change is justified, patch only the smallest live surface needed.",
            "4. Run targeted validation plus UTF-8 hygiene for touched files.",
            "5. Update canonical docs first, then temp mirrors, roadmap state, and queue-state.",
            "6. Run `python scripts/sync_temp_queue_state.py` and `python scripts/ops_validator.py --strict`.",
            "7. Continue only after the current TF is closed or split into a successor execution SSOT.",
            "",
            "Mandatory validation baseline:",
            "- TF-014:",
            '  - `rg -n "\\bprint\\s*\\(" main_a.py modules scripts geuldobi-desktop/src`',
            "  - `python -m pytest tests/test_runtime_print_allowlist.py`",
            "- TF-015:",
            "  - `ruff check modules scripts main_a.py --statistics`",
            "  - `ruff check modules scripts main_a.py --fix`",
            "  - `ruff check modules scripts main_a.py`",
            "- TF-016:",
            "  - `ruff check modules scripts main_a.py`",
            "  - `python -m py_compile <touched python files>`",
            "  - targeted pytest shards for touched modules",
            "- TF-019:",
            "  - re-audit guard loader/runtime surfaces first",
            "  - add or update targeted tests around invalid YAML/schema failure at startup",
            "  - run only the relevant config/guard tests after patching",
            "",
            "Hard stop conditions:",
            "- confidence below 95%",
            "- evidence mismatch between canonical docs and live code",
            "- scope expansion that needs a successor execution SSOT",
            "- UTF-8 hygiene violation",
            "- direct collision with unrelated dirty user work that cannot be safely composed",
            "",
            "Do not reopen completed lanes or use stale March 15 counts as live truth.",
            "```",
            "",
            "## Live Ruff Breakdown",
            ruff_lines or "- unavailable",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the post-remediation later-hardening autopilot prompt.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON snapshot.")
    parser.add_argument("--write", type=Path, help="Write the rendered output to a file.")
    args = parser.parse_args()

    snapshot = collect_snapshot()
    if args.json:
        payload = asdict(snapshot)
        output = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        output = build_prompt(snapshot)

    if args.write:
        target = args.write if args.write.is_absolute() else ROOT / args.write
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output + "\n", encoding="utf-8")

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
