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
    """[4-R2-b] Round-level context for interview round execution.

    NOTE: chief_writer~continuity_validator, story_context, style_guide는
    _SessionConfig와 의도적으로 중복됩니다. _SessionConfig는 세션 전체 설정,
    _RoundContext는 에피소드별 컨텍스트 + 세션 설정의 스냅샷입니다.
    slots=True 데이터클래스는 다중 상속이 제한되어 구조적 분리를 유지합니다.
    """

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
    preflight_advisory: str  # [TF-49b] Preflight 발견 사항 advisory (CW/Director용)
    reference_excerpt: str = ""
    recent_scene_keywords: list = dataclasses.field(default_factory=list)  # [NC-2 GAP-1]


@dataclasses.dataclass(slots=True)
class _InterviewRoundResult:
    """[4-R2-e] Result of a single interview round."""

    verdict: str  # "PASS" | "PASS_WITH_FIX" | "REJECT" | "EMPTY"  # [TF-32]
    director_feedback: str
    previous_attempt: dict
    final_manuscript: object = None  # str | None, set only on PASS
    final_title: object = None  # str | None, set only on PASS
    final_state_updates: dict = dataclasses.field(default_factory=dict)  # set only on PASS
    error_category: str = ""  # [V75-B] LOGIC_ERROR | QUALITY_ISSUE | ""
    attempt_artifact_meta: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class WritingDirective:
    """에피소드별 동적 집필 지시. PatternTracker + LLM이 생성."""

    ending_style: str = ""
    ending_avoid_phrases: list[str] = dataclasses.field(default_factory=list)  # [QI-1-A4] 회피할 엔딩 문구
    metaphor_avoid: list[str] = dataclasses.field(default_factory=list)
    metaphor_suggest: list[str] = dataclasses.field(default_factory=list)
    emotion_required: str = ""
    npc_directives: dict[str, str] = dataclasses.field(default_factory=dict)
    intensity_note: str = ""
    expression_ban: list[str] = dataclasses.field(default_factory=list)

    def is_empty(self) -> bool:
        return not any([self.ending_style, self.metaphor_avoid, self.expression_ban])
