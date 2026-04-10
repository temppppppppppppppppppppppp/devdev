# -*- coding: utf-8 -*-
"""Create a narrative_ssot project scaffold for a new work_id.

This is a low-risk filesystem utility for the narrative_ssot v0.1 pilot flow.
It copies `narrative_ssot/50_projects/_template` into
`narrative_ssot/50_projects/{work_id}` and rewrites a few placeholder values.

Usage:
    python -X utf8 scripts/create_narrative_project_scaffold.py --work-id demo_work
    python -X utf8 scripts/create_narrative_project_scaffold.py --work-id demo_work --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECTS_ROOT = ROOT / "narrative_ssot" / "50_projects"
TEMPLATE_ROOT = PROJECTS_ROOT / "_template"

WORK_ID_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


def _validate_work_id(work_id: str) -> str | None:
    """Return an error message when work_id is invalid."""
    if not work_id:
        return "work_id must not be empty"
    if work_id.startswith("_"):
        return "work_id must not start with '_' because that prefix is reserved"
    if not WORK_ID_RE.fullmatch(work_id):
        return "work_id must be snake_case using only lowercase letters, digits, and underscores"
    return None


def _read_json(path: Path) -> Any:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    return json.loads(text)


def _write_json(path: Path, data: Any) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def _replace_placeholder_text(path: Path, old: str, new: str) -> None:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    path.write_text(text.replace(old, new), encoding="utf-8")


def _placeholder_opening_bundle_contract() -> dict[str, Any]:
    return {
        "bundle_window": "TR 2~6",
        "macro_battlefield": "TODO: replace opening macro battlefield",
        "macro_battlefield_map": ["TODO: replace opening sub-battlefield lane"],
        "bundle_goal": "TODO: define the opening reader-earning goal for TR 2~6",
        "first_signboard_block": 3,
        "representative_reevaluation_block": 4,
        "next_battlefield_ticket_block": 6,
        "timing_reconciliation_note": (
            "TODO: reconcile Phase0 arc scale with the faster TR 2~6 reader-earning window."
        ),
    }


def _rewrite_placeholders(dest_root: Path, work_id: str) -> None:
    today = date.today().isoformat()

    intake_meta_path = dest_root / "00_intake" / "intake_meta.json"
    intake_meta = _read_json(intake_meta_path)
    if isinstance(intake_meta, dict):
        intake_meta.clear()
        intake_meta.update(
            {
                "work_id": work_id,
                "intake_date": today,
                "status": "pilot_scaffold_created",
                "notes": "",
            }
        )
        _write_json(intake_meta_path, intake_meta)

    reference_selection_path = dest_root / "10_reference_selection" / "reference_selection.json"
    reference_selection = _read_json(reference_selection_path)
    if isinstance(reference_selection, dict):
        reference_selection["work_id"] = work_id
        reference_selection["selection_date"] = today
        _write_json(reference_selection_path, reference_selection)

    contamination_guard_path = dest_root / "10_reference_selection" / "contamination_guard.json"
    contamination_guard = _read_json(contamination_guard_path)
    if isinstance(contamination_guard, dict):
        contamination_guard["notes"] = f"Scaffold created for {work_id} on {today}."
        _write_json(contamination_guard_path, contamination_guard)

    source_manifest_path = dest_root / "20_preprocess" / "source_manifest.json"
    source_manifest = _read_json(source_manifest_path)
    if isinstance(source_manifest, dict):
        source_manifest.clear()
        source_manifest.update(
            {
                "work_identity": {
                    "work_id": work_id,
                    "title": f"TODO: replace title for {work_id}",
                    "subtitle": "",
                    "commercial_label": "",
                    "slug_aliases": [],
                    "primary_profile": "business_growth_profile",
                    "secondary_profile": "",
                },
                "canonical_sources": [f"material_ssot/20_pitch/canon/{work_id}.md"],
                "reference_only_sources": [],
                "core_materials": [],
                "npc_pool": [],
                "crisis_pool": [],
                "hard_constraints": [],
                "do_not_fake": [],
                "manual_audit_note": (
                    f"Scaffold placeholder created on {today}. "
                    "Replace with audited source notes before Stage0 lock."
                ),
            }
        )
        _write_json(source_manifest_path, source_manifest)

    profile_lock_path = dest_root / "20_preprocess" / "profile_lock.json"
    profile_lock = _read_json(profile_lock_path)
    if isinstance(profile_lock, dict):
        profile_lock.clear()
        profile_lock.update(
            {
                "primary_profile": "business_growth_profile",
                "secondary_profile": "",
                "resource_axis": [],
                "power_axis": [],
                "control_axis": [],
                "payoff_axis": [],
                "failure_axis": [],
                "hud_interpretation": {},
            }
        )
        _write_json(profile_lock_path, profile_lock)

    material_bundle_path = dest_root / "20_preprocess" / "material_bundle_summary.json"
    material_bundle = _read_json(material_bundle_path)
    if isinstance(material_bundle, dict):
        material_bundle.clear()
        material_bundle.update(
            {
                "events": [],
                "npc_candidates": [],
                "crisis_candidates": [],
                "terms": [],
                "scene_details": [],
                "notes": (
                    f"Scaffold placeholder created on {today}. "
                    "Replace with audited material bundle notes before Stage0 lock."
                ),
                "opening_bundle_contract": _placeholder_opening_bundle_contract(),
            }
        )
        _write_json(material_bundle_path, material_bundle)

    phase0_ready_snapshot_path = dest_root / "20_preprocess" / "phase0_ready_snapshot.json"
    phase0_ready_snapshot = _read_json(phase0_ready_snapshot_path)
    if isinstance(phase0_ready_snapshot, dict):
        phase0_ready_snapshot.clear()
        phase0_ready_snapshot.update(
            {
                "identity_locked": False,
                "profile_locked": False,
                "material_sufficient": False,
                "manual_audit_pass": False,
                "remaining_risks": [
                    "Scaffold placeholders must be replaced before planning handoff."
                ],
            }
        )
        _write_json(phase0_ready_snapshot_path, phase0_ready_snapshot)

    phase0_design_path = dest_root / "30_planning" / "phase0_design.json"
    phase0_design = _read_json(phase0_design_path)
    if isinstance(phase0_design, dict):
        phase0_design.clear()
        phase0_design.update(
            {
                "work_id": work_id,
                "title": f"TODO: replace title for {work_id}",
                "work_identity_surface": {
                    "work_id": work_id,
                    "title": f"TODO: replace title for {work_id}",
                    "subtitle": "",
                    "commercial_label": "",
                    "slug_aliases": [],
                    "primary_profile": "business_growth_profile",
                    "secondary_profile": "",
                },
                "protagonist": "TODO: replace protagonist",
                "core_fantasy": "TODO: replace core fantasy",
                "opening_arc": {},
                "opening_bundle_contract": _placeholder_opening_bundle_contract(),
                "representative_spike": {},
                "growth_axis": {},
                "opponent_transition_plan": {},
                "payoff_axis": {},
            }
        )
        _write_json(phase0_design_path, phase0_design)

    sequential_status_path = dest_root / "40_production" / "sequential_run_status.json"
    sequential_status = _read_json(sequential_status_path)
    if isinstance(sequential_status, dict):
        sequential_status["work_id"] = work_id
        sequential_status["updated_at"] = today
        sequential_status["notes"] = f"Initial scaffold created on {today}."
        _write_json(sequential_status_path, sequential_status)

    release_gate_path = dest_root / "60_audit" / "release_gate.json"
    release_gate = _read_json(release_gate_path)
    if isinstance(release_gate, dict):
        release_gate["work_id"] = work_id
        _write_json(release_gate_path, release_gate)

    bi_template_path = dest_root / "50_bi" / "0_bi_template.json"
    bi_output_path = dest_root / "50_bi" / f"0_bi_{work_id}.json"
    bi_template = _read_json(bi_template_path)
    if isinstance(bi_template, dict):
        _write_json(bi_output_path, bi_template)
    bi_template_path.unlink()

    project_readme_path = dest_root / "README.md"
    _replace_placeholder_text(project_readme_path, "Project Template", f"Project Scaffold: {work_id}")


def create_scaffold(work_id: str, dry_run: bool = False, force: bool = False) -> tuple[bool, list[str]]:
    """Create a new project scaffold. Returns (ok, messages)."""
    messages: list[str] = []
    error = _validate_work_id(work_id)
    if error:
        return False, [error]

    if not TEMPLATE_ROOT.is_dir():
        return False, [f"Template root not found: {TEMPLATE_ROOT}"]

    destination = PROJECTS_ROOT / work_id
    if destination.exists():
        if not force:
            return False, [f"Destination already exists: {destination}"]
        if dry_run:
            messages.append(f"[dry-run] would replace existing destination: {destination}")
        else:
            shutil.rmtree(destination)
            messages.append(f"Removed existing destination: {destination}")

    if dry_run:
        messages.append(f"[dry-run] template root: {TEMPLATE_ROOT}")
        messages.append(f"[dry-run] destination: {destination}")
        messages.append(f"[dry-run] would copy template and rewrite work_id placeholders for '{work_id}'")
        return True, messages

    shutil.copytree(TEMPLATE_ROOT, destination)
    messages.append(f"Copied template to: {destination}")

    _rewrite_placeholders(destination, work_id)
    messages.append(f"Rewrote placeholder fields for work_id: {work_id}")
    messages.append("Scaffold creation complete.")
    return True, messages


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a new narrative_ssot project scaffold for a work_id."
    )
    parser.add_argument("--work-id", required=True, help="Canonical work_id (snake_case).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without creating files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace the destination if it already exists.",
    )
    args = parser.parse_args()

    ok, messages = create_scaffold(args.work_id, dry_run=args.dry_run, force=args.force)
    for message in messages:
        print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
