from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ops_support import ROOT

CLAUDE_SCOPE = (
    ".claude/get-shit-done",
    ".claude/commands",
    ".claude/agents",
)

TEXT_SUFFIXES = {".md"}

OLD_WORKSPACE_PATTERNS = (
    "C:/Users/wjjo/Desktop/글도비",
    r"C:\Users\wjjo\Desktop\글도비",
)


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    detail: str


@dataclass(frozen=True)
class TextRule:
    relpath: str
    required: tuple[str, ...]


TEXT_RULES = (
    TextRule(
        ".claude/commands/gsd/review.md",
        required=(
            "@./.claude/get-shit-done/workflows/review.md",
            "Execute the review workflow from @./.claude/get-shit-done/workflows/review.md end-to-end.",
        ),
    ),
    TextRule(
        ".claude/get-shit-done/workflows/review.md",
        required=('node "./.claude/get-shit-done/bin/gsd-tools.cjs" init phase-op "${PHASE_ARG}")',),
    ),
    TextRule(
        ".claude/agents/gsd-verifier.md",
        required=('node "./.claude/get-shit-done/bin/gsd-tools.cjs" roadmap get-phase "$PHASE_NUM"',),
    ),
)


def _read_utf8(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def _iter_md_files() -> list[Path]:
    files: dict[Path, None] = {}
    for relpath in CLAUDE_SCOPE:
        root = ROOT / relpath
        if not root.exists():
            continue
        if root.is_file():
            if root.suffix.lower() in TEXT_SUFFIXES:
                files[root] = None
            continue
        for candidate in root.rglob("*"):
            if candidate.is_file() and candidate.suffix.lower() in TEXT_SUFFIXES:
                files[candidate] = None
    return sorted(files)


def _scan_old_workspace_paths() -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_md_files():
        text = _read_utf8(path)
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pattern in OLD_WORKSPACE_PATTERNS:
                if pattern in line:
                    findings.append(
                        Finding(
                            "old_workspace_path",
                            f"{path.relative_to(ROOT).as_posix()}:{line_no}",
                            line.strip()[:240],
                        )
                    )
    return findings


def _check_text_rules() -> list[Finding]:
    findings: list[Finding] = []
    for rule in TEXT_RULES:
        path = ROOT / rule.relpath
        if not path.exists():
            findings.append(Finding("missing_path", rule.relpath, "rule target is missing"))
            continue
        text = _read_utf8(path)
        for required in rule.required:
            if required not in text:
                findings.append(Finding("missing_text", rule.relpath, required))
    return findings


def _format_finding(finding: Finding) -> str:
    return f"{finding.kind}: {finding.path}: {finding.detail}"


def main() -> int:
    findings: list[Finding] = []
    findings.extend(_scan_old_workspace_paths())
    findings.extend(_check_text_rules())

    if findings:
        print("claude local-path validation failed:")
        for finding in findings:
            print(_format_finding(finding))
        return 1

    print("claude local-path validation passed.")
    print(f"scanned markdown files: {len(_iter_md_files())}")
    print(f"checked text rules: {len(TEXT_RULES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
