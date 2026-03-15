from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from ops_support import DOCS, ROOT, latest_dated_dir

TEXT_FILE_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml"}
CLAUDE_RE = re.compile(r"\bCLAUDE\.md\b")
DOCS_TEMP_RE = re.compile(r"\bdocs/temp\b")
IMPL_REF_RE = re.compile(r"docs/implementation/[A-Za-z0-9._/-]+")


def iter_text_files() -> list[Path]:
    roots = [ROOT / "AGENTS.md", ROOT / "CLAUDE.md"]
    files: list[Path] = [path for path in roots if path.exists()]
    for path in DOCS.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_FILE_SUFFIXES:
            if path.name.endswith("-stale-reference-sweep.md") or path.name.endswith("-stale-reference-findings.txt"):
                continue
            files.append(path)
    return sorted(set(files))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sweep the repo for stale operational references and produce findings docs.")
    parser.add_argument("--topic", default="operations-governance", help="Topic slug for output filenames.")
    args = parser.parse_args()

    latest_dir = latest_dated_dir()
    if latest_dir is None:
        raise SystemExit("No dated docs directory found under docs/")

    findings: list[str] = []
    claude_hits = 0
    docs_temp_hits = 0
    broken_impl_refs: set[str] = set()

    for path in iter_text_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(lines, start=1):
            if CLAUDE_RE.search(line):
                claude_hits += 1
                findings.append(f"{rel}:{lineno}: CLAUDE_REF: {line.strip()}")
            if DOCS_TEMP_RE.search(line):
                docs_temp_hits += 1
                findings.append(f"{rel}:{lineno}: TEMP_REF: {line.strip()}")
            for match in IMPL_REF_RE.findall(line):
                candidate = ROOT / match.replace("/", "\\")
                if not candidate.exists():
                    broken_impl_refs.add(match)
                    findings.append(f"{rel}:{lineno}: BROKEN_IMPL_REF: {match}")

    findings_txt = latest_dir / f"{args.topic}-stale-reference-findings.txt"
    findings_txt.write_text("\n".join(findings) + ("\n" if findings else ""), encoding="utf-8")

    summary_lines = [
        f"# {args.topic.replace('-', ' ').title()} Stale Reference Sweep",
        "",
        f"Date: {latest_dir.name}",
        "Status: final",
        f"Scope: `{args.topic}` governance and process-reference sweep",
        "",
        "## 1. Summary",
        f"- scanned files: {len(iter_text_files())}",
        f"- `CLAUDE.md` references found: {claude_hits}",
        f"- `docs/temp` references found: {docs_temp_hits}",
        f"- broken `docs/implementation/*` references found: {len(broken_impl_refs)}",
        "",
        "## 2. Findings",
        f"- findings log: `{findings_txt.relative_to(ROOT).as_posix()}`",
        "- historical references may be acceptable if they are clearly archival or compatibility-only",
        "",
        "## 3. Broken Implementation References",
    ]
    if broken_impl_refs:
        summary_lines.extend(f"- `{ref}`" for ref in sorted(broken_impl_refs))
    else:
        summary_lines.append("- none")
    summary_lines.extend(
        [
            "",
            "## 4. Recommendation",
            "- update active operational docs if any stale authority references are found outside historical context",
            "- keep compatibility-only `CLAUDE.md` mentions when they are intentional",
        ]
    )

    summary_md = latest_dir / f"{args.topic}-stale-reference-sweep.md"
    summary_md.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"WROTE: {summary_md.relative_to(ROOT).as_posix()}")
    print(f"WROTE: {findings_txt.relative_to(ROOT).as_posix()}")
    print(f"CLAUDE_REFS: {claude_hits}")
    print(f"TEMP_REFS: {docs_temp_hits}")
    print(f"BROKEN_IMPL_REFS: {len(broken_impl_refs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
