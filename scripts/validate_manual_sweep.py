#!/usr/bin/env python3
"""
Validate manual-only sweep findings markdown.

Checks:
1) round-level mandatory manual evidence constraints
2) optional false-positive (FP) interim settlement checkpoints
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROUND_RE = re.compile(r"^### Round (\d+)\b.*$", re.MULTILINE)
FILE_LINE_RE = re.compile(r"`[^`\n]+:\d+`|[A-Za-z0-9_./\\-]+:\d+")
SEVERITY_RE = re.compile(r"\[P[0-3]-")
SEARCH_ONLY_HINTS = (
    "rg output",
    "grep output",
    "freg output",
    "pattern search only",
    "search-only",
)


READ_FILES_ALIASES = ("read files", "읽은 파일")
EVIDENCE_ALIASES = ("manual inspection evidence", "수동 검토 근거")
CONFIRMED_ALIASES = ("confirmed bugs",)
RISKS_ALIASES = ("risks",)
FP_ALIASES = ("false positives excluded",)
GAP_ALIASES = ("test gaps",)
INTENT_ALIASES = ("intent", "의도")


@dataclass
class RoundBlock:
    round_no: int
    text: str


@dataclass
class RoundMetrics:
    round_no: int
    bugs: int
    risks: int
    fps: int
    gaps: int


def split_rounds(text: str) -> list[RoundBlock]:
    matches = list(ROUND_RE.finditer(text))
    blocks: list[RoundBlock] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        round_no = int(m.group(1))
        blocks.append(RoundBlock(round_no=round_no, text=text[start:end]))
    return blocks


def has_section(block: str, aliases: tuple[str, ...]) -> bool:
    lower = block.lower()
    return any(alias in lower for alias in aliases)


def extract_bullets(block: str, aliases: tuple[str, ...]) -> list[str]:
    lines = block.splitlines()
    out: list[str] = []
    in_section = False

    for line in lines:
        s = line.strip()
        if s.startswith("**"):
            lower = s.lower()
            if any(alias in lower for alias in aliases):
                in_section = True
                continue
            if in_section:
                break
        if in_section and s.startswith("- "):
            out.append(s[2:].strip())

    return out


def is_none_line(line: str) -> bool:
    return line.strip().lower() in {"none", "없음"}


def real_bullets(lines: list[str]) -> list[str]:
    return [x for x in lines if not is_none_line(x)]


def validate_round(rb: RoundBlock) -> list[str]:
    errors: list[str] = []
    block = rb.text

    if not has_section(block, READ_FILES_ALIASES):
        errors.append("missing Read files section")

    if not has_section(block, EVIDENCE_ALIASES):
        errors.append("missing Manual inspection evidence section")
    else:
        ev = extract_bullets(block, EVIDENCE_ALIASES)
        if len(ev) < 2:
            errors.append("manual evidence has fewer than 2 bullets")
        if not any(FILE_LINE_RE.search(x) for x in ev):
            errors.append("manual evidence missing file:line references")
        low = " ".join(ev).lower()
        if any(h in low for h in SEARCH_ONLY_HINTS):
            errors.append("manual evidence appears search-output-only")

    required_sections = (
        ("Confirmed Bugs", CONFIRMED_ALIASES),
        ("Risks", RISKS_ALIASES),
        ("False Positives Excluded", FP_ALIASES),
        ("Test Gaps", GAP_ALIASES),
    )
    for label, aliases in required_sections:
        if not has_section(block, aliases):
            errors.append(f"missing section: {label}")

    cb = real_bullets(extract_bullets(block, CONFIRMED_ALIASES))
    if cb:
        if not any(SEVERITY_RE.search(x) for x in cb):
            errors.append("confirmed bug missing severity tag [P0-..P3-]")
        if not any(FILE_LINE_RE.search(x) for x in cb):
            errors.append("confirmed bug missing file:line references")
        low_cb = " ".join(cb).lower()
        if not any(alias in low_cb for alias in INTENT_ALIASES):
            errors.append("confirmed bug missing intent-check explanation")

    return errors


def count_issue_items(lines: list[str], *, confirmed: bool = False) -> int:
    rows = real_bullets(lines)
    if not rows:
        return 0
    if confirmed:
        tagged = [x for x in rows if SEVERITY_RE.search(x)]
        if tagged:
            return len(tagged)
    return len(rows)


def round_metrics(rb: RoundBlock) -> RoundMetrics:
    bugs = count_issue_items(extract_bullets(rb.text, CONFIRMED_ALIASES), confirmed=True)
    risks = count_issue_items(extract_bullets(rb.text, RISKS_ALIASES))
    fps = count_issue_items(extract_bullets(rb.text, FP_ALIASES))
    gaps = count_issue_items(extract_bullets(rb.text, GAP_ALIASES))
    return RoundMetrics(round_no=rb.round_no, bugs=bugs, risks=risks, fps=fps, gaps=gaps)


def print_fp_checkpoints(
    metrics: list[RoundMetrics],
    interval: int,
    *,
    max_fp_ratio: float | None,
    max_fp_streak: int | None,
) -> tuple[bool, list[str]]:
    """Return (ok, violations)."""
    violations: list[str] = []
    cum_bugs = 0
    cum_risks = 0
    cum_fps = 0
    cum_gaps = 0
    fp_only_streak = 0

    print("[INFO] FP interim settlement checkpoints")
    print("round | bugs | risks | fp | gaps | fp_ratio | fp_only_streak")
    print("----- | ---- | ----- | -- | ---- | -------- | --------------")

    by_round = {m.round_no: m for m in metrics}
    rounds_sorted = sorted(by_round.keys())
    min_round, max_round = rounds_sorted[0], rounds_sorted[-1]

    for rno in range(min_round, max_round + 1):
        m = by_round.get(rno)
        if not m:
            continue

        cum_bugs += m.bugs
        cum_risks += m.risks
        cum_fps += m.fps
        cum_gaps += m.gaps

        if m.fps > 0 and m.bugs == 0:
            fp_only_streak += 1
        elif m.fps > 0:
            fp_only_streak = 1
        else:
            fp_only_streak = 0

        if rno % interval == 0:
            denom = max(1, cum_bugs + cum_risks + cum_fps)
            fp_ratio = cum_fps / denom
            print(
                f"{rno:>5} | {cum_bugs:>4} | {cum_risks:>5} | {cum_fps:>2} | "
                f"{cum_gaps:>4} | {fp_ratio:>8.1%} | {fp_only_streak:>14}"
            )

            if max_fp_ratio is not None and fp_ratio > max_fp_ratio:
                violations.append(f"round {rno}: cumulative fp_ratio {fp_ratio:.1%} exceeds limit {max_fp_ratio:.1%}")
            if max_fp_streak is not None and fp_only_streak > max_fp_streak:
                violations.append(f"round {rno}: fp_only_streak {fp_only_streak} exceeds limit {max_fp_streak}")

    if violations:
        return False, violations
    return True, []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate manual sweep findings markdown.")
    parser.add_argument("file", type=Path, help="Findings markdown file path")
    parser.add_argument("--from-round", type=int, default=1, help="Start round (inclusive)")
    parser.add_argument("--to-round", type=int, default=100, help="End round (inclusive)")
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Return success when no rounds are found in range (useful before round 1 starts).",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=10,
        help="Interim settlement interval in rounds (default: 10).",
    )
    parser.add_argument(
        "--max-fp-ratio",
        type=float,
        default=None,
        help="Fail if cumulative FP ratio exceeds this value at checkpoint (e.g. 0.35).",
    )
    parser.add_argument(
        "--max-fp-streak",
        type=int,
        default=None,
        help="Fail if FP-only streak exceeds this value at checkpoint.",
    )
    parser.add_argument(
        "--no-fp-report",
        action="store_true",
        help="Disable FP interim settlement report output.",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"[ERROR] file not found: {args.file}")
        return 2
    if args.checkpoint_interval <= 0:
        print("[ERROR] --checkpoint-interval must be > 0")
        return 2

    text = args.file.read_text(encoding="utf-8", errors="replace")
    rounds = [r for r in split_rounds(text) if args.from_round <= r.round_no <= args.to_round]

    if not rounds:
        if args.allow_empty:
            print("[WARN] no rounds found in specified range (allowed)")
            return 0
        print("[ERROR] no rounds found in specified range")
        return 2

    rounds = sorted(rounds, key=lambda r: r.round_no)
    invalid: list[tuple[int, list[str]]] = []
    metrics: list[RoundMetrics] = []

    for rb in rounds:
        errs = validate_round(rb)
        if errs:
            invalid.append((rb.round_no, errs))
        metrics.append(round_metrics(rb))

    print(f"[INFO] checked rounds: {len(rounds)} ({args.from_round}-{args.to_round})")

    fp_ok = True
    fp_violations: list[str] = []
    if not args.no_fp_report:
        fp_ok, fp_violations = print_fp_checkpoints(
            metrics,
            args.checkpoint_interval,
            max_fp_ratio=args.max_fp_ratio,
            max_fp_streak=args.max_fp_streak,
        )

    if invalid:
        print(f"[FAIL] invalid rounds: {len(invalid)}")
        for rno, errs in invalid:
            print(f"- Round {rno}")
            for e in errs:
                print(f"  - {e}")
        return 1

    if not fp_ok:
        print("[FAIL] FP interim settlement threshold violations")
        for v in fp_violations:
            print(f"- {v}")
        return 1

    print("[OK] manual sweep validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
