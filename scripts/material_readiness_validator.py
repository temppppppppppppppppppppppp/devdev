# -*- coding: utf-8 -*-
"""Material readiness validator for canon/intake/synthesis markdown docs.

Usage:
    python -X utf8 scripts/material_readiness_validator.py --path material_ssot/20_pitch/canon/office_checkup_next_day.md
    python -X utf8 scripts/material_readiness_validator.py --path material_ssot/20_pitch/intake

Exit code 0 = pass, 1 = fail.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ops_support import ROOT

SECTION_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
ROW_EXACT_RE = re.compile(r"^-\s*block_no:\s*(\d+)\s*$", re.IGNORECASE)
ROW_LEGACY_RE = re.compile(r"^-\s*Block\s+(\d+)\s*:\s*$", re.IGNORECASE)
FIELD_RE = re.compile(r"^(?:-\s*)?([A-Za-z0-9_~+\-/ ]+):\s*(.*)$")

TARGET_PARTS = {"canon", "intake", "synthesis"}
SKIP_BASENAMES = {
    "README.md",
    "canonical_pitch_template_v1.md",
    "fresh_candidate_template_v1.md",
    "one_page_synthesis_template.md",
    "investment_one_page_synthesis_template.md",
}
SKIP_NAME_PARTS = (
    "_RETIRE",
    "checklist_audit",
    "integration_handoff",
)
PLACEHOLDER_VALUES = {"", "tbd", "todo", "pending", "fill", "n/a", "none", "-"}
REQUIRED_BLOCKS = (2, 3, 4, 5, 6)


@dataclass
class Finding:
    severity: str
    relpath: str
    detail: str
    line_no: int | None = None

    def render(self) -> str:
        prefix = f"{self.severity}: {self.relpath}"
        if self.line_no is not None:
            prefix += f":{self.line_no}"
        return f"{prefix} - {self.detail}"


@dataclass
class LedgerRow:
    block_no: int
    line_no: int
    style: str
    has_cider: bool | None = None
    same_block_receipt: str | None = None
    receipt_kind: str | None = None
    pain_only_exit: bool | None = None
    bridge_or_payback_note: str | None = None


@dataclass
class DocState:
    path: Path
    kind: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def relpath(self) -> str:
        return self.path.relative_to(ROOT).as_posix()

    def add(self, severity: str, detail: str, line_no: int | None = None) -> None:
        self.findings.append(Finding(severity, self.relpath, detail, line_no))


def normalize_key(raw: str) -> str:
    key = raw.strip().strip("`").lower()
    key = key.replace("same-block", "same_block")
    key = key.replace("2~6", "2_to_6")
    key = key.replace("+", "plus")
    key = re.sub(r"[^a-z0-9]+", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    return key


def parse_bool(raw: str) -> bool | None:
    value = raw.strip().strip("`").lower()
    value = re.sub(r"[().]", "", value)
    if value in {"yes", "true", "pass", "active"}:
        return True
    if value in {"no", "false", "hold", "reject", "inactive"}:
        return False
    return None


def infer_kind(path: Path) -> str | None:
    parts = set(path.parts)
    for part in TARGET_PARTS:
        if part in parts:
            return part
    return None


def should_validate(path: Path, include_legacy: bool) -> bool:
    if path.suffix.lower() != ".md":
        return False
    if path.name in SKIP_BASENAMES:
        return False
    rel = path.relative_to(ROOT).as_posix()
    if any(part in rel for part in SKIP_NAME_PARTS):
        return False
    kind = infer_kind(path)
    if kind is None:
        return False
    if not include_legacy and "/legacy_import/" in f"/{rel}/":
        return False
    if not include_legacy and "/supporting/" in f"/{rel}/":
        return False
    return True


def collect_targets(base: Path, include_legacy: bool) -> list[Path]:
    if base.is_file():
        return [base] if should_validate(base, include_legacy) else []
    if not base.is_dir():
        return []
    targets = [
        path
        for path in sorted(base.rglob("*.md"))
        if should_validate(path, include_legacy)
    ]
    return targets


def find_section_bounds(lines: list[str], needle: str) -> tuple[int, int, str] | None:
    needle_lc = needle.lower()
    for idx, line in enumerate(lines):
        match = SECTION_RE.match(line.strip())
        if not match:
            continue
        title = match.group(2).strip()
        if needle_lc not in title.lower():
            continue
        start = idx + 1
        end = len(lines)
        for probe in range(start, len(lines)):
            if SECTION_RE.match(lines[probe].strip()):
                end = probe
                break
        return start, end, title
    return None


def parse_ledger(lines: list[str], start: int, end: int) -> tuple[dict[int, LedgerRow], bool]:
    rows: dict[int, LedgerRow] = {}
    current: LedgerRow | None = None
    used_legacy_style = False

    for idx in range(start, end):
        raw = lines[idx]
        stripped = raw.strip()
        if not stripped:
            continue
        cleaned = stripped.replace("`", "")

        exact_match = ROW_EXACT_RE.match(cleaned)
        legacy_match = ROW_LEGACY_RE.match(cleaned)
        if exact_match:
            block_no = int(exact_match.group(1))
            current = LedgerRow(block_no=block_no, line_no=idx + 1, style="exact")
            rows[block_no] = current
            continue
        if legacy_match:
            block_no = int(legacy_match.group(1))
            current = LedgerRow(block_no=block_no, line_no=idx + 1, style="legacy")
            rows[block_no] = current
            used_legacy_style = True
            continue

        if current is None:
            continue

        field_match = FIELD_RE.match(cleaned)
        if not field_match:
            continue
        key = normalize_key(field_match.group(1))
        value = field_match.group(2).strip().strip("`")

        if key == "has_cider":
            current.has_cider = parse_bool(value)
        elif key == "same_block_receipt":
            current.same_block_receipt = value
        elif key == "receipt_kind":
            current.receipt_kind = value
        elif key == "pain_only_exit":
            current.pain_only_exit = parse_bool(value)
        elif key == "bridge_or_payback_note":
            current.bridge_or_payback_note = value

    return rows, used_legacy_style


def parse_readiness(lines: list[str], start: int, end: int) -> dict[str, tuple[bool | None, int, str]]:
    readiness: dict[str, tuple[bool | None, int, str]] = {}
    aliases = {
        "selection_ready": "selection_ready",
        "phase0_ready": "phase0_ready",
        "all_2_to_6_ledger_rows_have_has_cider_true": "all_rows_true",
        "all_2_to_6_rows_pay_in_block": "all_rows_true",
        "block_1_used_as_opening_rescue": "block1_rescue",
        "block_7plus_used_as_opening_rescue": "block7plus_rescue",
        "block_7_used_as_opening_rescue": "block7plus_rescue",
        "block_7_plus_used_as_opening_rescue": "block7plus_rescue",
    }

    for idx in range(start, end):
        stripped = lines[idx].strip()
        if not stripped:
            continue
        cleaned = stripped.replace("`", "")
        match = FIELD_RE.match(cleaned)
        if not match:
            continue
        raw_key = normalize_key(match.group(1))
        canonical_key = aliases.get(raw_key)
        if canonical_key is None:
            continue
        readiness[canonical_key] = (parse_bool(match.group(2)), idx + 1, match.group(2).strip())
    return readiness


def validate_file(path: Path) -> DocState:
    kind = infer_kind(path)
    assert kind is not None
    state = DocState(path=path, kind=kind)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    ledger_bounds = find_section_bounds(lines, "First-Block Cider Ledger")
    readiness_bounds = find_section_bounds(lines, "Readiness Declaration")
    if readiness_bounds is None:
        readiness_bounds = find_section_bounds(lines, "Readiness Claim")
    if ledger_bounds is None:
        state.add("ERROR", "Missing `First-Block Cider Ledger` section.")
    if readiness_bounds is None:
        state.add("ERROR", "Missing `Readiness Declaration` or `Readiness Claim` section.")
    if ledger_bounds is None or readiness_bounds is None:
        return state

    ledger_start, ledger_end, _ = ledger_bounds
    readiness_start, readiness_end, readiness_title = readiness_bounds

    rows, used_legacy_style = parse_ledger(lines, ledger_start, ledger_end)
    readiness = parse_readiness(lines, readiness_start, readiness_end)

    if used_legacy_style:
        state.add(
            "WARN",
            "Ledger uses legacy `- Block N:` row style. Migrate to exact `- block_no:` rows.",
        )

    missing_blocks = [block for block in REQUIRED_BLOCKS if block not in rows]
    extra_blocks = [block for block in sorted(rows) if block not in REQUIRED_BLOCKS]
    if missing_blocks:
        state.add("ERROR", f"Ledger missing required rows for blocks {missing_blocks}.")
    if extra_blocks:
        state.add("ERROR", f"Ledger contains out-of-scope rows {extra_blocks}; readiness uses strict 2~6 only.")

    for block_no in REQUIRED_BLOCKS:
        row = rows.get(block_no)
        if row is None:
            continue
        if row.has_cider is None:
            state.add("ERROR", "Missing boolean `has_cider`.", row.line_no)
        if row.same_block_receipt is None or row.same_block_receipt.strip().lower() in PLACEHOLDER_VALUES:
            state.add("ERROR", "Missing explicit `same_block_receipt`.", row.line_no)
        if row.receipt_kind is None or row.receipt_kind.strip().lower() in PLACEHOLDER_VALUES:
            state.add("ERROR", "Missing explicit `receipt_kind`.", row.line_no)
        if block_no == 6 and row.pain_only_exit is None:
            state.add("ERROR", "Block 6 must declare boolean `pain_only_exit`.", row.line_no)
        if row.has_cider is False and row.bridge_or_payback_note:
            if row.bridge_or_payback_note.strip().lower() not in PLACEHOLDER_VALUES:
                state.add(
                    "ERROR",
                    "`bridge_or_payback_note` cannot rescue a false ledger row.",
                    row.line_no,
                )

    selection_ready = readiness.get("selection_ready")
    phase0_ready = readiness.get("phase0_ready")
    all_rows_true = readiness.get("all_rows_true")
    block1_rescue = readiness.get("block1_rescue")
    block7plus_rescue = readiness.get("block7plus_rescue")

    if selection_ready is None:
        state.add("ERROR", f"`{readiness_title}` must declare `selection-ready: yes/no`.")
    if kind == "canon" and phase0_ready is None:
        state.add("ERROR", "Canon docs must declare `Phase0-ready: yes/no`.")
    if all_rows_true is None:
        state.add("ERROR", f"`{readiness_title}` must declare whether all 2~6 rows are true.")
    if block1_rescue is None:
        state.add("ERROR", f"`{readiness_title}` must declare `block 1 used as opening rescue: yes/no`.")
    if block7plus_rescue is None:
        state.add("ERROR", f"`{readiness_title}` must declare `block 7+ used as opening rescue: yes/no`.")

    actual_all_rows_true = (
        len(missing_blocks) == 0 and all(rows[block].has_cider is True for block in REQUIRED_BLOCKS if block in rows)
    )
    promoted = kind == "canon"
    if selection_ready is not None and selection_ready[0] is True:
        promoted = True
    if phase0_ready is not None and phase0_ready[0] is True:
        promoted = True

    if kind == "canon" and selection_ready is not None and selection_ready[0] is not True:
        state.add("ERROR", "Canon docs must declare `selection-ready: yes`.", selection_ready[1])

    if all_rows_true is not None and all_rows_true[0] != actual_all_rows_true:
        state.add(
            "ERROR",
            f"`all 2~6 rows true` claim does not match parsed ledger (`{actual_all_rows_true}`).",
            all_rows_true[1],
        )

    if block1_rescue is not None and block1_rescue[0] is True:
        state.add("ERROR", "Block 1 cannot be used as opening rescue.", block1_rescue[1])
    if block7plus_rescue is not None and block7plus_rescue[0] is True:
        state.add("ERROR", "Block 7+ cannot be used as opening rescue.", block7plus_rescue[1])

    if promoted and not actual_all_rows_true:
        state.add("ERROR", "Promoted docs may not retain any `has_cider: false` row.")
    block6 = rows.get(6)
    if promoted and block6 is not None and block6.pain_only_exit is True:
        state.add("ERROR", "Block 6 pain-only exit is an immediate HOLD for promoted docs.", block6.line_no)

    return state


def render_reports(reports: list[DocState]) -> int:
    failures = 0
    passes = 0
    warnings = 0

    for report in reports:
        errors = [finding for finding in report.findings if finding.severity == "ERROR"]
        warns = [finding for finding in report.findings if finding.severity == "WARN"]
        if errors:
            failures += 1
            print(f"FAIL {report.relpath}")
            for finding in report.findings:
                print(f"  - {finding.render()}")
            continue
        if warns:
            warnings += 1
            print(f"PASS-WARN {report.relpath}")
            for finding in report.findings:
                print(f"  - {finding.render()}")
        else:
            passes += 1
            print(f"PASS {report.relpath}")

    print()
    print(f"Summary: pass={passes}, pass_with_warn={warnings}, fail={failures}")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate material-side readiness markdown docs."
    )
    parser.add_argument(
        "--path",
        required=True,
        help="File or directory path relative to repo root or absolute path.",
    )
    parser.add_argument(
        "--include-legacy",
        action="store_true",
        help="Include intake legacy_import/supporting docs when scanning directories.",
    )
    args = parser.parse_args()

    base = Path(args.path)
    if not base.is_absolute():
        base = ROOT / base
    if not base.exists():
        print(f"Path not found: {base}", file=sys.stderr)
        return 1

    targets = collect_targets(base, args.include_legacy)
    if not targets:
        print("No eligible markdown targets found.")
        return 1

    reports = [validate_file(path) for path in targets]
    return render_reports(reports)


if __name__ == "__main__":
    raise SystemExit(main())
