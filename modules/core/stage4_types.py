"""[I-17] Shared types for Stage 4 submodules.

Extracted from stage4_orchestrator.py to break circular imports between
stage4_orchestrator, stage4_interview_round, and stage4_context_builder.
"""

import dataclasses

from modules.core.constants import PatchModeThresholds

# [Phase 3-5B] 패치 모드 임계값 (모듈 레벨 상수로 캐시)
_PATCH_REWRITE_THRESHOLD = PatchModeThresholds.REWRITE


@dataclasses.dataclass(slots=True)
class _RoundContext:
    """[4-R2-b] Round-level context for interview round execution."""

    chief_writer: object
    manuscript_validator: object
    consistency_validator: object
    blocking_validator: object
    continuity_validator: object
    next_ep: int
    blueprint: dict
    arc_data: dict
    arc_pos: int
    total_ep_in_arc: int
    arc_tactical: str
    prev_text: str
    prev_ending: str
    prev_manuscripts_text: str
    episode_digest: str
    hud_report: str
    current_inventory: list
    current_martial_arts: list
    dead_npcs: list
    item_acquisition_timeline: str
    chain_link_section: str
    world_state_summary: str
    purism_prompt: str
    genre_name: str
    npc_equipment_summary: str
    effective_anti_trope: str
    intro_dna: str
    story_context: str
    style_guide: str
    reference_anchor_prompt: str
    mandatory_context: str
    justification_prompt: str
    reflexion_prompt: str


@dataclasses.dataclass(slots=True)
class _InterviewRoundResult:
    """[4-R2-e] Result of a single interview round."""

    verdict: str  # "PASS" | "REJECT" | "EMPTY"
    director_feedback: str
    previous_attempt: dict
    final_manuscript: object = None  # str | None, set only on PASS
    final_title: object = None  # str | None, set only on PASS
    final_state_updates: dict = dataclasses.field(default_factory=dict)  # set only on PASS
