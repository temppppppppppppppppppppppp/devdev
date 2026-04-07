# -*- coding: utf-8 -*-
"""Promotion gate for material-side canon and pre-Phase0 transitions.

Usage:
    python -X utf8 scripts/material_promotion_gate.py --stage canon --path material_ssot/20_pitch/canon/office_checkup_next_day.md
    python -X utf8 scripts/material_promotion_gate.py --stage phase0 --path material_ssot/20_pitch/canon/office_checkup_next_day.md --work-id office_checkup_next_day

Exit code 0 = pass, 1 = fail.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ops_support import ROOT
from material_readiness_validator import collect_targets, render_reports, validate_file
from stage0_handoff_validator import validate as validate_stage0_handoff


def resolve_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    return path


def run_material_gate(path: Path) -> int:
    targets = collect_targets(path, include_legacy=False)
    if not targets:
        print("No eligible candidate/canon/working-synthesis markdown targets found.")
        return 1
    reports = [validate_file(target) for target in targets]
    return render_reports(reports)


def run_stage0_gate(work_id: str) -> int:
    print()
    print(f"Stage0 Handoff Gate: work_id={work_id}")
    passed, messages = validate_stage0_handoff(work_id)
    for message in messages:
        print(f"  - {message}")
    print(f"Stage0 Handoff Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the material promotion gate for canon or pre-Phase0 promotion."
    )
    parser.add_argument(
        "--stage",
        required=True,
        choices=("canon", "phase0"),
        help="Promotion target stage.",
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Markdown candidate path or directory, absolute or repo-relative.",
    )
    parser.add_argument(
        "--work-id",
        help="Required for --stage phase0. Canonical work_id for Stage 0 handoff validation.",
    )
    args = parser.parse_args()

    path = resolve_path(args.path)
    if not path.exists():
        print(f"Path not found: {path}", file=sys.stderr)
        return 1

    print(f"Material Promotion Gate: stage={args.stage}")
    print(f"Target: {path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path}")
    print()

    readiness_code = run_material_gate(path)
    if readiness_code != 0:
        print()
        print("Promotion Gate Result: FAIL (material readiness gate)")
        return 1

    if args.stage == "canon":
        print()
        print("Promotion Gate Result: PASS (canon-ready gate)")
        return 0

    if not args.work_id:
        print("--work-id is required when --stage phase0", file=sys.stderr)
        return 1

    stage0_code = run_stage0_gate(args.work_id)
    if stage0_code != 0:
        print()
        print("Promotion Gate Result: FAIL (Stage0 handoff gate)")
        return 1

    print()
    print("Promotion Gate Result: PASS (pre-Phase0 gate)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
