from __future__ import annotations

import json
import shutil
from pathlib import Path

import scripts.create_narrative_project_scaffold as scaffold


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_create_scaffold_seeds_stage0_and_phase0_opening_contract(monkeypatch, temp_dir) -> None:
    projects_root = temp_dir / "narrative_ssot" / "50_projects"
    template_root = projects_root / "_template"
    shutil.copytree(Path(scaffold.TEMPLATE_ROOT), template_root)

    monkeypatch.setattr(scaffold, "PROJECTS_ROOT", projects_root)
    monkeypatch.setattr(scaffold, "TEMPLATE_ROOT", template_root)

    ok, messages = scaffold.create_scaffold("demo_work")

    assert ok
    assert any("Scaffold creation complete." in message for message in messages)

    destination = projects_root / "demo_work"
    reference_selection = _read_json(destination / "10_reference_selection" / "reference_selection.json")
    source_manifest = _read_json(destination / "20_preprocess" / "source_manifest.json")
    profile_lock = _read_json(destination / "20_preprocess" / "profile_lock.json")
    material_bundle = _read_json(destination / "20_preprocess" / "material_bundle_summary.json")
    phase0_ready_snapshot = _read_json(destination / "20_preprocess" / "phase0_ready_snapshot.json")
    phase0_design = _read_json(destination / "30_planning" / "phase0_design.json")

    assert reference_selection["profile_override"] is None
    assert reference_selection["work_identity_override"] is None
    assert reference_selection["opening_bundle_contract_override"] is None
    assert source_manifest["work_identity"]["work_id"] == "demo_work"
    assert source_manifest["work_identity"]["subtitle"] == ""
    assert source_manifest["work_identity"]["commercial_label"] == ""
    assert source_manifest["work_identity"]["slug_aliases"] == []
    assert source_manifest["canonical_sources"] == ["material_ssot/20_pitch/canon/demo_work.md"]
    assert profile_lock["primary_profile"] == "business_growth_profile"
    assert profile_lock["resource_axis"] == []
    assert material_bundle["notes"].startswith("Scaffold placeholder created on ")
    assert material_bundle["opening_bundle_contract"]["bundle_window"] == "TR 2~6"
    assert material_bundle["opening_bundle_contract"]["next_battlefield_ticket_block"] == 6
    assert phase0_ready_snapshot["manual_audit_pass"] is False
    assert phase0_ready_snapshot["remaining_risks"]
    assert phase0_design["work_id"] == "demo_work"
    assert phase0_design["work_identity_surface"]["slug_aliases"] == []
    assert phase0_design["opening_bundle_contract"]["first_signboard_block"] == 3
    assert (destination / "50_bi" / "0_bi_demo_work.json").is_file()
    assert not (destination / "50_bi" / "0_bi_template.json").exists()
