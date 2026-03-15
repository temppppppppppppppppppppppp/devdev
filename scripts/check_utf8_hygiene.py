from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
import re

TEXT_SUFFIXES = {
    ".bat",
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".jsx",
    ".log",
    ".md",
    ".ps1",
    ".psm1",
    ".py",
    ".scss",
    ".spec",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
ROOT_FILE_ALLOWLIST = {"AGENTS.md", ".pre-commit-config.yaml", ".editorconfig"}
SKIP_DIR_NAMES = {
    ".git",
    ".hypothesis",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "dist",
    "node_modules",
    "python-embed",
    "win-unpacked",
}
ALLOW_LINE_MARKER = "utf8-hygiene: allow-line"
ALLOW_FILE_MARKER = "utf8-hygiene: allow-file"
TRIPLE_QUESTION_RE = re.compile(r"\?{3,}")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int | None
    kind: str
    snippet: str


def _is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in ROOT_FILE_ALLOWLIST


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def _iter_candidate_files(paths: list[Path]) -> list[Path]:
    ordered: dict[Path, None] = {}
    for raw_path in paths:
        if not raw_path.exists():
            continue
        if raw_path.is_dir():
            for path in raw_path.rglob("*"):
                if path.is_file() and not _should_skip(path) and _is_text_candidate(path):
                    ordered[path] = None
            continue
        if raw_path.is_file() and not _should_skip(raw_path) and _is_text_candidate(raw_path):
            ordered[raw_path] = None
    return sorted(ordered)


def _contains_hangul(char: str) -> bool:
    codepoint = ord(char)
    return 0x1100 <= codepoint <= 0x11FF or 0x3130 <= codepoint <= 0x318F or 0xAC00 <= codepoint <= 0xD7A3


def _contains_cjk(char: str) -> bool:
    codepoint = ord(char)
    return (
        0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
    )


def _has_mixed_hangul_cjk_token(line: str) -> str | None:
    for token in line.split():
        stripped = token.strip("`'\"()[]{}<>,.:;")
        if not stripped:
            continue
        has_hangul = any(_contains_hangul(char) for char in stripped)
        has_cjk = any(_contains_cjk(char) for char in stripped)
        if has_hangul and has_cjk:
            return stripped
    return None


def _has_suspicious_question_token(line: str) -> str | None:
    for token in line.split():
        stripped = token.strip("`'\"()[]{}<>,.:;")
        if not stripped or "?" not in stripped:
            continue
        has_non_ascii = any(ord(char) > 0x7F for char in stripped if char != "?")
        if not has_non_ascii:
            continue
        has_ascii_alnum = any(char.isascii() and char.isalnum() for char in stripped)
        question_count = stripped.count("?")
        terminal_only = question_count == 1 and stripped.endswith("?")
        if has_ascii_alnum or question_count >= 2 or not terminal_only:
            return stripped
    return None


def _has_allow_file_marker(text: str) -> bool:
    return any(ALLOW_FILE_MARKER in line for line in text.splitlines()[:20])


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    raw = path.read_bytes()
    if b"\x00" in raw:
        return findings

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        findings.append(
            Finding(
                path=path.as_posix(),
                line=None,
                kind="invalid_utf8",
                snippet=f"{exc.reason} at byte {exc.start}",
            )
        )
        return findings

    if _has_allow_file_marker(text):
        return findings

    for line_no, line in enumerate(text.splitlines(), 1):
        if ALLOW_LINE_MARKER in line:
            continue
        if "\ufffd" in line:
            findings.append(Finding(path.as_posix(), line_no, "replacement_character", line[:240]))
        if TRIPLE_QUESTION_RE.search(line):
            findings.append(Finding(path.as_posix(), line_no, "triple_question_placeholder", line[:240]))
        suspicious_question_token = _has_suspicious_question_token(line)
        if suspicious_question_token:
            findings.append(Finding(path.as_posix(), line_no, "suspicious_question_token", suspicious_question_token[:240]))
        mixed_token = _has_mixed_hangul_cjk_token(line)
        if mixed_token:
            findings.append(Finding(path.as_posix(), line_no, "hangul_cjk_mixed_token", mixed_token[:240]))
    return findings


def collect_findings(paths: list[Path | str]) -> list[Finding]:
    normalized_paths = [Path(path) for path in paths]
    findings: list[Finding] = []
    for path in _iter_candidate_files(normalized_paths):
        findings.extend(scan_file(path))
    return findings


def _format_finding(finding: Finding) -> str:
    location = f"{finding.path}:{finding.line}" if finding.line is not None else finding.path
    return f"{location}: {finding.kind}: {finding.snippet}"


def _coerce_for_terminal(text: str, encoding: str | None = None) -> str:
    target_encoding = encoding or getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        return text.encode(target_encoding, errors="backslashreplace").decode(target_encoding)
    except LookupError:
        return text.encode("utf-8", errors="backslashreplace").decode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reject invalid UTF-8 and common mojibake signatures on touched text files."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to scan.")
    args = parser.parse_args(argv)

    findings = collect_findings(args.paths)
    if not findings:
        return 0

    print(_coerce_for_terminal("UTF-8 hygiene check failed:"))
    for finding in findings:
        print(_coerce_for_terminal(_format_finding(finding)))
    print(
        _coerce_for_terminal(
            "Use explicit UTF-8 reads before patching; only archival evidence may use utf8-hygiene allow markers."
        )
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
