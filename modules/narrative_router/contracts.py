from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NarrativePlanningContract:
    required_preprocess_files: tuple[str, ...]
    readiness_flag_file: str
    readiness_flag_path: tuple[str, ...]
    phase0_output_pattern: str


@dataclass(frozen=True)
class NarrativeTRContract:
    harness_script: str | None
    continuity_profile: str
    canonical_axes: tuple[str, ...]


@dataclass(frozen=True)
class NarrativeBIContract:
    hud_root: str
    builder_script: str
    audit_script: str
    required_phase0_sections: tuple[str, ...]
    required_phase0_design_fields: tuple[str, ...]
    required_master_sections: tuple[str, ...]


@dataclass(frozen=True)
class NarrativeFamilyContract:
    planning: NarrativePlanningContract
    tr: NarrativeTRContract
    bi: NarrativeBIContract
