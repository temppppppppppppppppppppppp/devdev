from __future__ import annotations

from modules.narrative_router.contracts import (
    NarrativeBIContract,
    NarrativeFamilyContract,
    NarrativePlanningContract,
    NarrativeTRContract,
)

from .base import NarrativeFamilyPlugin

PLUGIN = NarrativeFamilyPlugin(
    key="blockguide",
    display_name="Blockguide",
    description="Modern-fantasy business-power family preserving the existing blockguide stack.",
    family_aliases=("blockguide", "business-power", "modern-fantasy", "default"),
    genre_aliases=(
        "investment",
        "hunter",
        "fantasy",
        "modern-fantasy",
        "현판",
        "헌터",
        "현대판타지",
        "office",
        "business",
        "tech",
        "startup",
        "medical",
        "sports",
        "actor",
        "composer",
        "cooking",
        "alt-history",
        "alt_history",
        "대체역사",
    ),
    integrated_order_path="docs/blockguide/SSOT_blockguide-integrated-order.md",
    planning_path="docs/blockguide/treatment-planning-harness.md",
    production_path="docs/blockguide/treatment-production-harness-v2.md",
    bi_path="docs/blockguide/bi-production-harness-v1.md",
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
            harness_script="scripts/tr_batch_harness.py",
            continuity_profile="business-power",
            canonical_axes=("capital", "deal_type", "business_sector", "opponent_rotation"),
        ),
        bi=NarrativeBIContract(
            hud_root="FinanceHUD",
            builder_script="scripts/build_bi_from_phase0_and_tr.py",
            audit_script="scripts/audit_bi_5pass.py",
            required_phase0_sections=("project", "setting", "protagonist", "phase0_design"),
            required_phase0_design_fields=("arcs", "npc_timeline", "foreshadow_map", "opponent_transition_plan"),
            required_master_sections=("ProjectData", "FinanceHUD", "WorldState", "AssetLibrary", "Seeds", "plot_roadmap"),
        ),
    ),
    extra_paths={
        "alt-history": "docs/blockguide/alt_history_db_harness.md",
        "materials": "docs/blockguide/modern_fantasy_material_harness.md",
    },
)
