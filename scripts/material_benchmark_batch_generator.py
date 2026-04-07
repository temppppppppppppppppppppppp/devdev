# -*- coding: utf-8 -*-
"""Generate filled material benchmark prompt files and one-line launch orders in batch.

Usage:
    python -X utf8 scripts/material_benchmark_batch_generator.py
    python -X utf8 scripts/material_benchmark_batch_generator.py --path material_ssot/20_pitch/canon --limit 3
"""
from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

from material_benchmark_order_generator import (
    build_one_line_order,
    build_prompt,
    build_spec,
    relpath,
    slugify,
)
from material_readiness_validator import collect_targets, infer_kind
from ops_support import ROOT, canonical_path, latest_dated_dir


DEFAULT_SCAN_PATHS = (
    "material_ssot/20_pitch/canon",
    "material_ssot/20_pitch/intake",
    "material_ssot/20_pitch/synthesis",
)


def choose_date_dir() -> Path:
    latest = latest_dated_dir()
    if latest is not None:
        return latest
    target = ROOT / "docs" / "material-benchmark-batch"
    target.mkdir(parents=True, exist_ok=True)
    return target


def gather_targets(raw_paths: list[str] | None) -> list[Path]:
    scan_paths = raw_paths or list(DEFAULT_SCAN_PATHS)
    found: list[Path] = []
    seen: set[Path] = set()
    for raw in scan_paths:
        base = canonical_path(raw)
        for target in collect_targets(base, include_legacy=False):
            if target in seen:
                continue
            seen.add(target)
            found.append(target)
    return sorted(found)


def auto_promotion_intent(path: Path) -> str:
    kind = infer_kind(path)
    if kind == "canon":
        return "none"
    if kind in {"intake", "synthesis"}:
        return "canon"
    return "none"


def default_watchpoint(path: Path) -> str:
    kind = infer_kind(path) or "material"
    if kind == "canon":
        return (
            "canon recheck only; do not drift into downstream pair scoring; "
            "do not claim new promotion from an already canon source"
        )
    if kind == "intake":
        return (
            "candidate audit only; do not infer selection-ready upward from premise heat alone; "
            "keep PASS/HOLD/REJECT only"
        )
    if kind == "synthesis":
        return (
            "working synthesis audit only; do not treat synthesis as canon lock; "
            "check ledger and readiness claim directly"
        )
    return (
        "do not widen beyond the target pitch markdown; keep PASS/HOLD/REJECT only; "
        "do not fake promotion-gate success"
    )


def build_spec_for_target(target: Path, promotion_mode: str):
    resolved_intent = auto_promotion_intent(target) if promotion_mode == "auto" else promotion_mode
    namespace = SimpleNamespace(
        pitch=relpath(target),
        report_path=None,
        prompt_path=None,
        target_id=None,
        target_label=None,
        family=None,
        promotion_intent=resolved_intent,
        work_id=None,
        watchpoint=default_watchpoint(target),
    )
    return build_spec(namespace)


def default_manifest_path(scan_paths: list[str] | None, promotion_mode: str) -> Path:
    date_dir = choose_date_dir()
    if not scan_paths:
        suffix = "all"
    elif len(scan_paths) == 1:
        suffix = slugify(Path(scan_paths[0]).stem or Path(scan_paths[0]).name)
    else:
        suffix = "multi"
    name = f"material_benchmark_batch_{suffix}_{promotion_mode}_orders.md"
    return date_dir / name


def render_manifest(specs, scan_paths: list[str] | None, promotion_mode: str) -> str:
    lines: list[str] = []
    lines.append("# Material Benchmark Batch Launch Orders")
    lines.append("")
    lines.append(f"Date: {choose_date_dir().name if choose_date_dir().name else 'n/a'}")
    lines.append("Status: active")
    lines.append("Mode: generated batch launch sheet")
    lines.append("")
    lines.append("## Batch Settings")
    lines.append("")
    lines.append(f"- scan roots: `{', '.join(scan_paths or DEFAULT_SCAN_PATHS)}`")
    lines.append(f"- promotion intent mode: `{promotion_mode}`")
    lines.append(f"- target count: `{len(specs)}`")
    lines.append("")
    lines.append("## Generated Prompt Files")
    lines.append("")
    for spec in specs:
        lines.append(f"- `{relpath(spec.prompt_path)}`")
    lines.append("")
    lines.append("## One-Line Orders")
    lines.append("")
    for idx, spec in enumerate(specs, start=1):
        lines.append(f"{idx}. {build_one_line_order(spec)}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate material benchmark prompt files and one-line launch orders in batch."
    )
    parser.add_argument(
        "--path",
        action="append",
        help="Scan root, absolute or repo-relative. Repeatable. Defaults to canon/intake/synthesis.",
    )
    parser.add_argument(
        "--promotion-intent",
        choices=("auto", "none", "canon", "phase0"),
        default="auto",
        help="Apply one promotion intent to all targets, or auto-resolve by kind.",
    )
    parser.add_argument(
        "--manifest-path",
        help="Optional output path for the batch launch sheet, absolute or repo-relative.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional limit for quick dry runs.",
    )
    args = parser.parse_args()

    targets = gather_targets(args.path)
    if args.limit is not None:
        targets = targets[: max(args.limit, 0)]
    if not targets:
        print("No eligible candidate/canon/working-synthesis markdown targets found.")
        return 1

    specs = [build_spec_for_target(target, args.promotion_intent) for target in targets]
    for spec in specs:
        spec.prompt_path.write_text(build_prompt(spec), encoding="utf-8")

    manifest_path = canonical_path(args.manifest_path) if args.manifest_path else default_manifest_path(
        args.path, args.promotion_intent
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(render_manifest(specs, args.path, args.promotion_intent), encoding="utf-8")

    print(f"Batch launch sheet written to: {manifest_path}")
    print(f"Generated prompt files: {len(specs)}")
    for spec in specs:
        print(f"- {spec.prompt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
