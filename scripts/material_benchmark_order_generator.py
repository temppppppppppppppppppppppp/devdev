# -*- coding: utf-8 -*-
"""Generate a filled material benchmark prompt file plus a one-line launch order.

Usage:
    python -X utf8 scripts/material_benchmark_order_generator.py \
        --pitch material_ssot/20_pitch/canon/office_checkup_next_day.md
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ops_support import ROOT, canonical_path, first_heading, latest_dated_dir, parse_metadata


DEFAULT_WATCHPOINT = (
    "do not widen beyond the target pitch markdown; keep PASS/HOLD/REJECT only; "
    "do not fake promotion-gate success"
)


@dataclass
class PromptSpec:
    pitch_path: Path
    prompt_path: Path
    report_path: Path
    target_id: str
    target_label: str
    family: str
    watchpoint: str
    promotion_intent: str
    work_id: str | None


def relpath(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def default_date_dir() -> Path:
    latest = latest_dated_dir()
    if latest is not None:
        return latest
    docs_dir = ROOT / "docs" / date.today().isoformat()
    docs_dir.mkdir(parents=True, exist_ok=True)
    return docs_dir


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", lowered)
    cleaned = normalized.strip("_")
    return cleaned or "material_target"


def derive_target_id(path: Path, metadata: dict[str, str], heading: str | None) -> str:
    for key in ("proposed_work_id", "work_id"):
        value = metadata.get(key)
        if value:
            return value.strip("` ")
    if heading:
        heading_slug = slugify(heading)
        if heading_slug != "material_target":
            return heading_slug
    return slugify(path.stem)


def derive_target_label(metadata: dict[str, str], heading: str | None, target_id: str) -> str:
    title = metadata.get("title")
    if title:
        return title.strip()
    if heading:
        return heading.strip()
    return target_id


def resolve_output_path(raw: str | None, fallback_name: str) -> Path:
    if raw:
        return canonical_path(raw)
    target = default_date_dir() / fallback_name
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def build_spec(args: argparse.Namespace) -> PromptSpec:
    pitch_path = canonical_path(args.pitch)
    if not pitch_path.exists():
        raise FileNotFoundError(f"Pitch path not found: {pitch_path}")

    metadata = parse_metadata(pitch_path)
    heading = first_heading(pitch_path.read_text(encoding="utf-8"))
    target_id = args.target_id or derive_target_id(pitch_path, metadata, heading)
    target_label = args.target_label or derive_target_label(metadata, heading, target_id)
    family = args.family or metadata.get("family") or "n/a"
    slug = slugify(target_id)

    report_path = resolve_output_path(
        args.report_path,
        f"material_benchmark_{slug}_external_report.md",
    )
    prompt_path = resolve_output_path(
        args.prompt_path,
        f"material_benchmark_{slug}_external_prompt.md",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)

    promotion_intent = args.promotion_intent
    work_id = args.work_id or target_id
    if promotion_intent == "phase0" and not work_id:
        raise ValueError("--work-id is required when --promotion-intent phase0")

    return PromptSpec(
        pitch_path=pitch_path,
        prompt_path=prompt_path,
        report_path=report_path,
        target_id=target_id,
        target_label=target_label,
        family=family,
        watchpoint=args.watchpoint or DEFAULT_WATCHPOINT,
        promotion_intent=promotion_intent,
        work_id=work_id,
    )


def promotion_boundary_lines(spec: PromptSpec) -> list[str]:
    lines = [
        "- this benchmark report is not canon lock and not `Phase0` promotion",
        f"- promotion intent for this run: `{spec.promotion_intent}`",
    ]
    if spec.promotion_intent == "canon":
        lines.extend(
            [
                "- if operator later wants actual canon promotion, operator must separately run:",
                f"  - `python -X utf8 scripts/material_promotion_gate.py --stage canon --path {relpath(spec.pitch_path)}`",
            ]
        )
    elif spec.promotion_intent == "phase0":
        lines.extend(
            [
                "- if operator later wants actual `Phase0` promotion, operator must separately run:",
                "  - `python -X utf8 scripts/material_promotion_gate.py "
                f"--stage phase0 --path {relpath(spec.pitch_path)} --work-id {spec.work_id}`",
            ]
        )
    else:
        lines.append("- for this run, no promotion gate execution is requested")
    lines.append("- do not fabricate promotion-gate success inside the report")
    return lines


def build_prompt(spec: PromptSpec) -> str:
    boundary = "\n".join(promotion_boundary_lines(spec))
    return f"""# {spec.target_label} Material Benchmark Prompt

Date: {date.today().isoformat()}
Status: active
Document Type: external model prompt
Benchmark Type: material
Intended Report Path: `{relpath(spec.report_path)}`

## Mission

Run a read-only material benchmark for `{spec.target_id}` only.
Audit readiness from the target pitch markdown only.
Do not pretend this report itself is canon lock or `Phase0` promotion.
Write the final report directly to the intended report path if your environment allows file creation.

## Non-Negotiables

- opening readiness uses exact ledger rows `2, 3, 4, 5, 6` only
- `block 1` is setup only and cannot rescue opening readiness
- `block 7+` cannot rescue opening readiness
- any `has_cider:false` row means `not selection-ready`
- `bridge_or_payback_note` may explain a thin receipt, but cannot rescue a false row
- use `PASS / HOLD / REJECT`, not pair grade language
- this report is not promotion-gate output
- if evidence is ambiguous, downgrade
- never substitute a custom rubric

## Context Safety Rule

- do not widen the read beyond the target pitch markdown and the readiness harness unless the operator explicitly adds another source
- inspect the `First-Block Cider Ledger` rows `2~6` directly
- inspect the `Readiness Claim` or `Readiness Declaration` directly
- if the ledger is missing or malformed, downgrade immediately
- do not invent a parallel material scoring scale

## Compliance Self-Check Before Final Write

Before writing the final report, verify all of the following are `yes`:

- `strict first-block window uses 2~6 only`
- `block 1 is not used as opening cider proof`
- `block 7+ is not used as opening rescue`
- `ledger contains exact rows 2, 3, 4, 5, 6`
- `no ledger row is blank`
- `every selection-ready row has has_cider true`
- `bridge_or_payback_note is not used to rescue a false row`
- `block 6 is not pain_only_exit`
- `promotion verdict matches the ledger`
- `benchmark report is not pretending to be promotion-gate output`
- `pitch files were not mutated`

If any item is `no`, revise before writing the final report.

## Read Order

1. `material_ssot/00_governance/external-model-benchmark-operation-harness-v1.md`
2. `material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md`
3. `material_ssot/20_pitch/pitch-selection-checklist.md`
4. `{relpath(spec.pitch_path)}`
5. this prompt

## Assigned Target

- target id: `{spec.target_id}`
- benchmark type: `material`
- family: `{spec.family}`
- Pitch: `{relpath(spec.pitch_path)}`

## Watchpoint

- {spec.watchpoint}

## Promotion Gate Boundary

{boundary}

## Required Output

Create the final markdown report directly at:

- `{relpath(spec.report_path)}`

Fallback:

- if you cannot write files in your environment, output the same markdown body only, with no extra preface or postscript

Use these sections exactly:

1. `Pitch Identity`
2. `Material Compliance Self-Check`
3. `First-Block Cider Ledger Review`
4. `Planning Candidate 7 Questions`
5. `Work-Guard Freeze Check`
6. `Promotion Verdict`
7. `Fix Queue`

Rules:

- inside `Material Compliance Self-Check`, answer every required item with `yes` or `no`
- list exact ledger rows `2, 3, 4, 5, 6`
- if verdict is `PASS`, make clear that promotion still requires a separate gate run
- use `PASS / HOLD / REJECT`, not pair grades
- if the doc is exploratory only, say `HOLD`, not `PASS`
- last line must be:
  - `read-only material benchmark audit complete; no pitch files mutated`
"""


def build_one_line_order(spec: PromptSpec) -> str:
    return (
        f"{spec.prompt_path} 를 읽고 target pitch {spec.pitch_path} 에 대해 read-only material benchmark를 수행한 뒤 "
        f"{spec.report_path} 에 최종 markdown report를 직접 작성하라; 파일 쓰기가 불가하면 동일 markdown 본문만 출력하라."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a filled material benchmark prompt file and one-line launch order."
    )
    parser.add_argument("--pitch", required=True, help="Target pitch markdown path, absolute or repo-relative.")
    parser.add_argument("--report-path", help="Optional output report path, absolute or repo-relative.")
    parser.add_argument("--prompt-path", help="Optional output prompt path, absolute or repo-relative.")
    parser.add_argument("--target-id", help="Optional override for target id.")
    parser.add_argument("--target-label", help="Optional override for human-readable target label.")
    parser.add_argument("--family", help="Optional override for family.")
    parser.add_argument(
        "--promotion-intent",
        choices=("none", "canon", "phase0"),
        default="none",
        help="Operator intent after the benchmark completes.",
    )
    parser.add_argument("--work-id", help="Work id for future phase0 promotion intent.")
    parser.add_argument("--watchpoint", help="Optional anti-cheat watchpoint.")
    args = parser.parse_args()

    try:
        spec = build_spec(args)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    prompt_text = build_prompt(spec)
    spec.prompt_path.write_text(prompt_text, encoding="utf-8")

    print(f"Prompt written to: {spec.prompt_path}")
    print(f"Report target: {spec.report_path}")
    print()
    print("One-line order:")
    print(build_one_line_order(spec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
