from __future__ import annotations

from modules.narrative_router.contracts import (
    NarrativeBIContract,
    NarrativeFamilyContract,
    NarrativePlanningContract,
    NarrativeTRContract,
)

from .base import NarrativeFamilyPlugin

PLUGIN = NarrativeFamilyPlugin(
    key="wuxguide",
    display_name="Wuxguide",
    description="Martial-family narrative harness stack for wuxia and xianxia works.",
    family_aliases=("wuxguide", "wuxia", "martial", "jianghu"),
    genre_aliases=("wuxia", "무협", "murim", "jianghu", "xianxia", "선협"),
    integrated_order_path="docs/wuxguide/SSOT_wuxguide-integrated-order.md",
    planning_path="docs/wuxguide/wuxia-planning-harness.md",
    production_path="docs/wuxguide/wuxia-production-harness.md",
    bi_path="docs/wuxguide/wuxia-bi-production-harness.md",
    contract=NarrativeFamilyContract(
        planning=NarrativePlanningContract(
            required_preprocess_files=(
                "source_manifest.json",
                "profile_lock.json",
                "material_bundle_summary.json",
                "phase0_ready_snapshot.json",
            ),
            readiness_flag_file="phase0_ready_snapshot.json",
            readiness_flag_path=("manual_audit_pass",),
            phase0_output_pattern="treatments/{work_id}_phase0_design.json",
        ),
        tr=NarrativeTRContract(
            harness_script="scripts/wuxia_tr_batch_harness.py",
            continuity_profile="martial-family",
            canonical_axes=("realm", "internal_energy", "martial_arts", "faction", "jianghu_reputation"),
        ),
        bi=NarrativeBIContract(
            hud_root="MartialHUD",
            builder_script="scripts/build_wuxia_bi_from_phase0_and_tr.py",
            audit_script="scripts/audit_wuxia_bi_5pass.py",
            required_phase0_sections=("project", "setting", "protagonist", "phase0_design"),
            required_phase0_design_fields=("arcs", "npc_timeline", "foreshadow_map", "opponent_transition_plan"),
            required_master_sections=("ProjectData", "MartialHUD", "WorldState", "AssetLibrary", "FactionMap", "Treasures", "Seeds", "plot_roadmap"),
        ),
    ),
)
