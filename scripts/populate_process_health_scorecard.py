from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from ops_support import ROOT, canonical_path, ensure_queue_state, parse_metadata, queue_items_from_state


def validator_passes(strict: bool) -> bool:
    command = [sys.executable, str(ROOT / "scripts" / "ops_validator.py")]
    if strict:
        command.append("--strict")
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return result.returncode == 0


def detect_exception_docs(date_dir: str) -> list[Path]:
    target = ROOT / "docs" / date_dir
    if not target.exists():
        return []
    return sorted(target.glob("*exception*.md"))


def status_from_side_effect_coverage(items) -> tuple[str, str]:
    if not items:
        return ("green", "no active execution item requires side-effect coverage review")
    statuses = []
    for item in items:
        metadata = parse_metadata(canonical_path(item.canonical_path))
        statuses.append((metadata.get("side-effect_coverage") or "").lower())
    if all(status == "covered" for status in statuses):
        return ("green", "all active execution docs declare `Side-Effect Coverage: covered`")
    if any(status == "" for status in statuses):
        return ("amber", "one or more execution docs do not declare side-effect coverage")
    return ("amber", "one or more execution docs declare partial or non-covered side-effect status")


def manifest_path_for_item(date_dir: str, item_topic: str) -> Path:
    return ROOT / "docs" / date_dir / f"{item_topic}-evidence-manifest.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate a process health scorecard from current governance state.")
    parser.add_argument("--scope", default="docs/temp active execution queue", help="Scorecard scope label.")
    parser.add_argument("--output", help="Optional explicit scorecard output path.")
    args = parser.parse_args()

    state = ensure_queue_state(refresh=True)
    items = queue_items_from_state(state)
    date_dir = None
    if items:
        first_canonical = items[0].canonical_path.replace("\\", "/")
        parts = Path(first_canonical).parts
        if len(parts) >= 2:
            date_dir = parts[1]
    if not date_dir:
        date_dir = "2026-03-14"

    strict_validator_ok = validator_passes(strict=True)
    non_strict_validator_ok = validator_passes(strict=False)

    governance_alignment = (
        "green",
        "`AGENTS.md`, init harness, and governance map are present",
        "`AGENTS.md`, `docs/implementation/operations-governance-map.md`",
    )
    queue_integrity = (
        "green" if strict_validator_ok else "red",
        "strict validator passes" if strict_validator_ok else "strict validator fails",
        "`python scripts/ops_validator.py --strict`",
    )
    canonical_sync = (
        "green" if non_strict_validator_ok else "red",
        "canonical and temp queue artifacts are in sync" if non_strict_validator_ok else "queue sync drift detected",
        "`python scripts/ops_validator.py`",
    )

    manifest_paths = [manifest_path_for_item(date_dir, item.topic) for item in items] if items else []
    manifest_exists = bool(manifest_paths) and all(path.exists() for path in manifest_paths)
    evidence_freshness = (
        "green" if manifest_exists else "amber",
        "evidence manifest exists for active queue items" if manifest_exists else "one or more active queue items do not have an evidence manifest",
        f"`{manifest_paths[0].relative_to(ROOT).as_posix()}`" if manifest_exists and manifest_paths else "`none`",
    )
    side_effect_status, side_effect_note = status_from_side_effect_coverage(items)
    side_effect_coverage = (
        side_effect_status,
        side_effect_note,
        f"`{items[0].canonical_path}`" if items else "`none`",
    )

    exceptions = detect_exception_docs(date_dir)
    exception_debt = (
        "green" if not exceptions else "amber",
        "no active exception docs detected" if not exceptions else "one or more exception docs exist and should be reviewed",
        "`none`" if not exceptions else f"`{exceptions[0].relative_to(ROOT).as_posix()}`",
    )

    if not items:
        closure_readiness = ("green", "queue is empty", "`docs/temp/queue-state.json`")
    elif any(item.status == "blocked" for item in items):
        closure_readiness = ("red", "one or more queue items are blocked", "`docs/temp/queue-state.json`")
    else:
        closure_readiness = ("amber", "active queue items remain pending or in progress", "`docs/temp/queue-state.json`")

    validator_status = (
        "green" if strict_validator_ok else "red",
        "validator is clean" if strict_validator_ok else "validator reports failures",
        "`python scripts/ops_validator.py --strict`",
    )

    dimension_rows = [
        ("governance alignment",) + governance_alignment,
        ("queue integrity",) + queue_integrity,
        ("canonical/mirror sync",) + canonical_sync,
        ("evidence freshness",) + evidence_freshness,
        ("side-effect coverage",) + side_effect_coverage,
        ("exception debt",) + exception_debt,
        ("validator status",) + validator_status,
        ("closure readiness",) + closure_readiness,
    ]

    colors = [row[1] for row in dimension_rows]
    overall_color = "red" if "red" in colors else "amber" if "amber" in colors else "green"
    overall_reason = "validator or queue integrity is failing" if overall_color == "red" else (
        "active queue remains open but governance is healthy" if overall_color == "amber" else "governance and queue state are healthy"
    )

    actions = []
    if not strict_validator_ok:
        actions.append("- fix validator failures before claiming queue health")
    if items:
        actions.append("- keep queue-state and validator in sync after each execution-doc change")
    if exceptions:
        actions.append("- review active exception docs and confirm removal conditions remain valid")
    if not actions:
        actions.append("- no immediate corrective action required")

    output_path = canonical_path(args.output) if args.output else ROOT / "docs" / date_dir / "temp-execution-queue-process-health-scorecard.md"
    lines = [
        "# Temp Execution Queue Process Health Scorecard",
        "",
        f"Date: {date_dir}",
        "Status: final",
        f"Scope: `{args.scope}`",
        "",
        "## 1. Executive Read",
        f"- overall color: {overall_color}",
        f"- why: {overall_reason}",
        "",
        "## 2. Dimensions",
        "",
        "| Dimension | Status | Evidence | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for name, status, note, evidence in dimension_rows:
        lines.append(f"| {name} | {status} | {evidence} | {note} |")
    lines.extend(["", "## 3. Immediate Actions"])
    lines.extend(actions)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE: {output_path.relative_to(ROOT).as_posix()}")
    print(f"OVERALL: {overall_color}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
