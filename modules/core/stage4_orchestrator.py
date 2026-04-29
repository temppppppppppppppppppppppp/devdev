"""
[V64.P3] Stage4Orchestrator — SovereignApp의 Stage 4 원고 집필 오케스트레이션 로직 캡슐화

SovereignApp에서 분리된 Stage 4 관련 메서드:
- stage_4_v2_chief_writer(): Chief Writer 주권주의 아키텍처 메인 루프 (~896줄)

모든 SovereignApp 속성은 self.app를 통해 접근.
"""

import dataclasses
import logging
import re
from pathlib import Path

from modules.core.artifact_logging import build_candidate_key, snapshot_logged_artifact
from modules.core.blueprint_lineage import attach_stage3_blueprint_lineage_meta
from modules.core.constants import smart_truncate
from modules.core.final_accepted_context import load_final_accepted_manuscript_row
from modules.core.frontier_staleness import (
    detect_stage4_frontier_staleness,
    frontier_status_satisfied_by_stage3_lineage,
    mark_downstream_frontier_requires_adjudication,
    resolve_arc_end_episode,
)
from modules.core.jsonl_io import append_jsonl_record
from modules.core.llm_generate import generate_content_via_router
from modules.core.logging_keys import resolve_logging_session_id
from modules.core.project_support import (
    default_external_pov_insert_policy,
    load_style_guide_anchor,
    load_style_guide_file,
    resolve_project_bible_pov,
)
from modules.core.soft_failure import resolve_project_log_dir
from modules.core.stage4_context_builder import Stage4ContextBuilder
from modules.core.stage4_interview_round import Stage4InterviewRound
from modules.core.stage4_outcome_runtime import Stage4OutcomeRuntime
from modules.core.stage4_policy_digest import resolve_stage4_policy_value
from modules.core.stage4_post_processor import Stage4PostProcessor
from modules.core.stage4_types import _RoundContext
from modules.core.stage_cross_stage_contract import (
    OPENING_TRANSITION_DIRECT,
    OPENING_TRANSITION_EXPLICIT,
    OPENING_TRANSITION_JUMP,
    resolve_opening_transition_contract,
)
from modules.validation.threshold_helper import _threshold

_perf_logger = logging.getLogger(__name__)  # [V65] PerfTimer 로깅


def _clamp_reference_excerpt(reference_excerpt: str, *, max_chars: int | None = None) -> str:
    """Clamp Stage 0 reference excerpts before Stage 4 prompt injection."""

    text = str(reference_excerpt or "").strip()
    if not text:
        return ""

    limit = int(max_chars or _threshold("context.reference_excerpt_chars", 20000))
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text

    trimmed = smart_truncate(text, max_chars=limit, head_chars=max(1200, int(limit * 0.72)))
    logging.info("[Stage4] reference_excerpt budget clamp applied: %d -> %d chars", len(text), len(trimmed))
    return trimmed


def _trim_mandatory_context_for_budget(mandatory_context: str, *, max_chars: int) -> str:
    """Preserve recent tail context when Stage 4 mandatory context overflows the budget."""

    text = str(mandatory_context or "")
    if len(text) <= max_chars:
        return text

    head_chars = max(0, min(int(max_chars * 0.55), max_chars - 80))
    return smart_truncate(text, max_chars=max_chars, head_chars=head_chars)


def _render_style_guide_payload(
    style_payload: dict[str, object] | None,
    *,
    bible_pov: str = "",
) -> tuple[str, str, str, str]:
    payload = dict(style_payload or {})
    if not payload:
        return "", "", "", ""

    tone = str(payload.get("tone") or "").strip() or "중립"
    resolved_pov = (
        str(
            bible_pov
            or payload.get("effective_primary_pov")
            or payload.get("selected_primary_pov")
            or payload.get("pov")
            or ""
        ).strip()
        or "1인칭"
    )
    reference_excerpt = str(payload.get("reference_excerpt") or "").strip()

    explicit_prompt = str(payload.get("fallback_style_prompt") or "").strip()
    if explicit_prompt:
        return explicit_prompt, reference_excerpt, tone, resolved_pov

    dialogue_ratio = payload.get("dialogue_ratio")
    try:
        dialogue_value = float(dialogue_ratio)
    except (TypeError, ValueError):
        dialogue_value = 0.3
    if dialogue_value > 1.0:
        dialogue_value /= 100.0
    if not 0.0 <= dialogue_value <= 1.0:
        dialogue_value = 0.3

    sentence_length = str(payload.get("sentence_length") or "").strip() or "medium"
    description_style = str(payload.get("description_style") or "").strip() or "균형"
    vocabulary_level = str(payload.get("vocabulary_level") or "").strip() or "medium"
    external_policy = str(payload.get("external_pov_insert_policy") or "").strip()
    if external_policy:
        external_policy = f"\n- 외부 시점 삽입: {external_policy}"

    prompt = (
        "## 문체 DNA (절대 준수)\n"
        f"- 톤: {tone}\n"
        f"- 시점: {resolved_pov}\n"
        f"- 대화 비율: {dialogue_value:.0%}\n"
        f"- 문장 길이: {sentence_length}\n"
        f"- 묘사: {description_style}\n"
        f"- 어휘: {vocabulary_level}"
        f"{external_policy}"
    )
    return prompt, reference_excerpt, tone, resolved_pov


# ── Dataclass family: budget helpers ──────────────────────────
@dataclasses.dataclass(slots=True)
class _MandatoryContextBudgetResult:
    mandatory_context: str
    removed_count: int
    removed_chars: int
    used_fallback: bool


def _fit_mandatory_context_budget(mandatory_context: str, *, max_chars: int) -> _MandatoryContextBudgetResult:
    text = str(mandatory_context or "")
    if len(text) <= max_chars:
        return _MandatoryContextBudgetResult(
            mandatory_context=text,
            removed_count=0,
            removed_chars=0,
            used_fallback=False,
        )

    section_pattern = re.compile(r"\n(?=\[)")
    sections = [section for section in section_pattern.split(text) if section.strip()]
    if len(sections) <= 1:
        return _MandatoryContextBudgetResult(
            mandatory_context=_trim_mandatory_context_for_budget(text, max_chars=max_chars),
            removed_count=0,
            removed_chars=0,
            used_fallback=True,
        )

    removed_count = 0
    removed_chars = 0
    while len("\n".join(sections)) > max_chars and len(sections) > 1:
        removed_section = sections.pop()
        removed_count += 1
        removed_chars += len(removed_section)

    fitted = "\n".join(sections)
    used_fallback = False
    if len(fitted) > max_chars:
        fitted = _trim_mandatory_context_for_budget(fitted, max_chars=max_chars)
        used_fallback = True

    return _MandatoryContextBudgetResult(
        mandatory_context=fitted,
        removed_count=removed_count,
        removed_chars=removed_chars,
        used_fallback=used_fallback,
    )


# ═══════════════════════════════════════════════════════════════
# [Phase 3-5C] NPC 과잉 등장 감지 (advisory-only, pure function)
# ═══════════════════════════════════════════════════════════════
def _detect_npc_overexposure(
    manuscript: str,
    npc_names,
    protagonist_name: str = "",
    *,
    max_mentions: int | None = None,
    core_npc_names: frozenset = frozenset(),
    min_name_length: int = 2,
):
    """에피소드 원고에서 엑스트라 NPC별 언급 횟수를 세어 임계값 초과 시 경고 dict 반환.

    주인공·핵심NPC(core_npc_names)·짧은 이름(min_name_length 미만)은 제외.
    Longest-match-first 마스킹으로 부분일치 이중 카운트 방지.
    """
    if max_mentions is None:
        max_mentions = _threshold("npc_exposure.max_mentions_per_episode", 15)
    if not manuscript or not npc_names:
        return None
    # 후보 필터링: 주인공, 핵심NPC, 짧은 이름 제외
    excluded = set()
    candidates = []
    for name in npc_names:
        if not name or len(name) < min_name_length:
            continue
        if name == protagonist_name or name in core_npc_names:
            excluded.add(name)
            continue
        candidates.append(name)
    if not candidates:
        return None
    # Longest-match-first: 긴 이름 먼저 세고 마스킹 → 부분일치 방지
    sorted_names = sorted(candidates, key=len, reverse=True)
    temp = manuscript
    overexposed = {}
    for name in sorted_names:
        count = temp.count(name)
        if count >= max_mentions:
            overexposed[name] = count
        if count > 0:
            temp = temp.replace(name, "\x00" * len(name))
    if not overexposed:
        return None
    top = sorted(overexposed.items(), key=lambda x: -x[1])
    return {
        "npcs": dict(top),
        "total": len(top),
        "max_npc": top[0][0],
        "max_count": top[0][1],
        "excluded_core_npcs": sorted(excluded),
        "warning": f"NPC 과잉 등장: {', '.join(f'{n}({c}회)' for n, c in top[:5])}",
    }


# ═══════════════════════════════════════════════════════════════
# [Phase 3-B] 크로스 에피소드 문장 반복 감지 (advisory-only, pure function)
# ═══════════════════════════════════════════════════════════════
def _detect_cross_episode_repetition(
    fingerprints,
    repeated,
    *,
    warning_threshold: int | None = None,
    regression_threshold: int | None = None,
):
    """크로스 에피소드 문장 반복 감지 (advisory-only).

    Args:
        fingerprints: 현재 에피소드 [(hash, preview), ...]
        repeated: DB에서 조회된 [{"sentence_hash", "episode_number", "sentence_preview"}, ...]
        warning_threshold: 이 이상 반복 문장 → severity="warning"
        regression_threshold: 이 이상 → severity="regression"

    Returns:
        dict with detected/severity/overlap_count/overlap_ratio/top_repeated/warning
        or None if below threshold.
    """
    # [C4-P2-2] _threshold()를 default arg에서 호출하면 import 시점에 고정됨 — 함수 body에서 해소
    if warning_threshold is None:
        warning_threshold = _threshold("cross_episode_repetition.overlap_warning", 3)
    if regression_threshold is None:
        regression_threshold = _threshold("cross_episode_repetition.overlap_regression", 6)
    if not fingerprints or not repeated:
        return None
    unique_hashes = {r["sentence_hash"] for r in repeated}
    overlap_count = len(unique_hashes)
    if overlap_count < warning_threshold:
        return None
    overlap_ratio = overlap_count / len(fingerprints)
    severity = "regression" if overlap_count >= regression_threshold else "warning"
    # 반복 문장 상위 5개 (미리보기 포함)
    seen = set()
    top_repeated = []
    for r in repeated:
        if r["sentence_hash"] not in seen:
            seen.add(r["sentence_hash"])
            top_repeated.append(
                {
                    "preview": r.get("sentence_preview", "")[:40],
                    "ep": r["episode_number"],
                }
            )
            if len(top_repeated) >= 5:
                break
    summary_parts = [f"'{t['preview']}'(ep{t['ep']})" for t in top_repeated[:3]]
    return {
        "detected": True,
        "severity": severity,
        "overlap_count": overlap_count,
        "overlap_ratio": round(overlap_ratio, 3),
        "top_repeated": top_repeated,
        "warning": f"크로스 에피소드 반복 {overlap_count}건: {', '.join(summary_parts)}",
    }


# ── Dataclass family: session setup payloads ─────────────────
@dataclasses.dataclass(slots=True)
class _SessionConfig:
    """[4-R2-a] Session-level config for Stage 4 interview loop.

    NOTE: chief_writer~continuity_validator, story_context, style_guide는
    _RoundContext(stage4_types.py)와 의도적으로 중복됩니다.
    세션 설정이 에피소드별 _RoundContext로 복사되는 구조입니다.
    """

    chief_writer: object
    manuscript_validator: object
    consistency_validator: object
    blocking_validator: object
    continuity_validator: object
    s4_genre_type: str
    story_context: str
    style_guide: str
    target_ep: object  # int | None
    output_dir: object  # Path
    v50_modules_available: bool
    total_planned_ep: int
    reference_excerpt: str = ""


@dataclasses.dataclass(slots=True)
class _SessionTargetDecision:
    target_ep: object = None
    should_abort: bool = False


@dataclasses.dataclass(slots=True)
class _SessionStyleGuidePayload:
    style_guide: str = ""
    reference_excerpt: str = ""


@dataclasses.dataclass(slots=True)
class _SessionAgentBootstrap:
    chief_writer: object
    manuscript_validator: object
    consistency_validator: object
    blocking_validator: object
    continuity_validator: object
    s4_genre_type: str


@dataclasses.dataclass(slots=True)
class _SessionEnvironmentPayload:
    output_dir: object  # Path
    total_planned_ep: int
    current_written: int


@dataclasses.dataclass(slots=True)
class _SessionRuntimeDependencies:
    ai_models: object
    emojis: object
    stage0_available: bool
    v50_modules_available: bool
    chief_writer_cls: object
    manuscript_validator_cls: object
    blocking_validator_cls: object
    consistency_validator_cls: object
    continuity_validator_cls: object


# ── Dataclass family: round/interview outcome dispositions ───
@dataclasses.dataclass(slots=True)
class _RoundOutcome:
    """[4-R2-d] Result of _handle_round_outcome."""

    final_manuscript: object  # str | None
    final_title: object  # str | None
    final_state_updates: dict
    should_return: bool


@dataclasses.dataclass(slots=True)
class _PassRoundDisposition:
    accepted: bool = False
    should_continue: bool = False
    final_manuscript: object = None
    final_title: object = None
    final_state_updates: dict = dataclasses.field(default_factory=dict)
    director_feedback: str = ""
    previous_attempt: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(slots=True)
class _RejectRoundDisposition:
    director_feedback: str = ""
    previous_attempt: dict = dataclasses.field(default_factory=dict)
    logic_error_streak: int = 0
    prev_reject_bucket: str = ""
    bucket_streak: int = 0
    prev_dominant_contradiction: str = ""
    contradiction_type_streak: int = 0
    score_history: list[int] = dataclasses.field(default_factory=list)
    plateau_advisory_emitted: bool = False
    tf29_advisory_emitted: bool = False
    tf29_advisory: str = ""
    dominant_contradiction: str = ""


@dataclasses.dataclass(slots=True)
class _RetryEscalationDisposition:
    round_ctx: object = None
    director_feedback: str = ""
    previous_attempt: dict = dataclasses.field(default_factory=dict)
    logic_error_streak: int = 0
    inplace_attempted: bool = False
    blueprint_regenerated: bool = False


@dataclasses.dataclass(slots=True)
class _V75DArtifactPayload:
    artifact_meta: dict = dataclasses.field(default_factory=dict)
    change_ratio: float | None = None


@dataclasses.dataclass(slots=True)
class _V75DSuccessPayload:
    round_ctx: object = None
    director_feedback: str = ""
    previous_attempt: dict = dataclasses.field(default_factory=dict)
    logic_error_streak: int = 0


@dataclasses.dataclass(slots=True)
class _V75DPatchAttemptPayload:
    round_ctx: object = None
    director_feedback: str = ""
    previous_attempt: dict = dataclasses.field(default_factory=dict)
    logic_error_streak: int = 0
    success: bool = False
    artifact_payload: _V75DArtifactPayload = dataclasses.field(default_factory=_V75DArtifactPayload)


@dataclasses.dataclass(slots=True)
class _RejectRoundStepDisposition:
    round_ctx: object = None
    director_feedback: str = ""
    previous_attempt: dict = dataclasses.field(default_factory=dict)
    logic_error_streak: int = 0
    inplace_attempted: bool = False
    blueprint_regenerated: bool = False
    prev_reject_bucket: str = ""
    bucket_streak: int = 0
    prev_dominant_contradiction: str = ""
    contradiction_type_streak: int = 0
    score_history: list[int] = dataclasses.field(default_factory=list)
    plateau_advisory_emitted: bool = False
    tf29_advisory_emitted: bool = False


@dataclasses.dataclass(slots=True)
class _InterviewRoundLoopState:
    final_manuscript: object = None
    final_title: object = None
    final_state_updates: dict = dataclasses.field(default_factory=dict)
    director_feedback: str = ""
    previous_attempt: dict = dataclasses.field(default_factory=dict)
    logic_error_streak: int = 0
    inplace_attempted: bool = False
    blueprint_regenerated: bool = False
    prev_reject_bucket: str = ""
    bucket_streak: int = 0
    prev_dominant_contradiction: str = ""
    contradiction_type_streak: int = 0
    score_history: list[int] = dataclasses.field(default_factory=list)
    plateau_advisory_emitted: bool = False
    tf29_advisory_emitted: bool = False
    pathology_counts: dict[str, int] = dataclasses.field(default_factory=dict)
    pathology_repeat_emitted: set[str] = dataclasses.field(default_factory=set)


# ── Dataclass family: episode loop payloads ──────────────────
@dataclasses.dataclass(slots=True)
class _InterviewRoundStepDisposition:
    round_ctx: object
    loop_state: _InterviewRoundLoopState
    should_continue: bool = False
    should_break: bool = False


@dataclasses.dataclass(slots=True)
class _EpisodeLoopDisposition:
    should_return: bool = False
    should_break: bool = False


@dataclasses.dataclass(slots=True)
class _EpisodeLoopCheckpoint:
    next_ep: object = None
    should_break: bool = False


@dataclasses.dataclass(slots=True)
class _WriterPromptSupplements:
    """Small prompt-only payload derived before round-context assembly."""

    purism_prompt: str
    npc_equipment_summary: str
    effective_anti_trope: str
    intro_dna: str


@dataclasses.dataclass(slots=True)
class _EpisodeLoopInputs:
    blueprint: dict
    arc_data: dict
    preflight_advisory: str


@dataclasses.dataclass(slots=True)
class _InterviewLoopRuntime:
    chief_writer: object
    target_ep: object = None
    output_dir: object = None
    v50_modules_available: bool = False
    max_loops: int = 1
    anchor_sys: object = None


@dataclasses.dataclass(slots=True)
class _EpisodePromptBundle:
    genre_name: str
    ctx_prompts: dict
    prompt_supplements: _WriterPromptSupplements


@dataclasses.dataclass(slots=True)
class _BlueprintPreflightRequest:
    prompt: str
    patched_blueprint: dict | None


class Stage4Orchestrator:
    """
    [V64.P3] SovereignApp의 Stage 4 원고 집필 오케스트레이션 로직 캡슐화

    패턴: self.app = SovereignApp 인스턴스
    """

    def __init__(self, app, *, context=None) -> None:
        """
        Args:
            app: SovereignApp 인스턴스 (비파일럿 속성 접근용)
            context: Stage4Context (파일럿 5종 DI, 미주입 시 app에서 자동 빌드)
        """
        self.app = app
        self._ctx = context  # [Phase 4C-2a] DI 파일럿 컨텍스트
        self._post_processor = None  # [B-1-1] lazy init
        self._context_builder = None  # [B-1-2] lazy init
        self._interview_round = None  # [B-1-3] lazy init
        self._stage4_completion_blocked = False
        self.outcome_runtime = Stage4OutcomeRuntime(self)

    def get_stage4_policy_value(self, *path: str, default=None):
        return resolve_stage4_policy_value(*path, default=default)

    def get_stage4_policy_int(self, *path: str, default: int) -> int:
        value = self.get_stage4_policy_value(*path, default=default)
        try:
            resolved = int(value)
        except (TypeError, ValueError):
            return int(default)
        return resolved if resolved > 0 else int(default)

    def get_stage4_policy_bool(self, *path: str, default: bool) -> bool:
        value = self.get_stage4_policy_value(*path, default=default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        return bool(default)

    def _get_stage4_accept_verdicts(self) -> set[str]:
        raw = self.get_stage4_policy_value(
            "interview_round",
            "accepted_verdicts",
            default=("PASS", "PASS_WITH_FIX"),
        )
        if not isinstance(raw, list | tuple | set):
            return {"PASS", "PASS_WITH_FIX"}
        normalized = {str(item or "").strip().upper() for item in raw if str(item or "").strip()}
        return normalized or {"PASS", "PASS_WITH_FIX"}

    def _get_stage4_max_rounds(self) -> int:
        raw = self.get_stage4_policy_value("interview_round", "max_rounds", default=None)
        if raw is None:
            try:
                return max(1, int(_threshold("retry.director_max_attempts", 5)))
            except (TypeError, ValueError):
                return 5
        return self.get_stage4_policy_int("interview_round", "max_rounds", default=5)

    def _get_stage4_shadow_max_rounds(self) -> int | None:
        if not self.get_stage4_policy_bool("shadow_mode", "enabled", default=False):
            return None
        raw = self.get_stage4_policy_value("shadow_mode", "max_rounds", default=None)
        if raw is None:
            return None
        try:
            resolved = int(raw)
        except (TypeError, ValueError):
            return None
        return resolved if resolved > 0 else None

    def _stage4_shadow_log_all_episodes(self) -> bool:
        return self.get_stage4_policy_bool("shadow_mode", "log_all_episodes", default=False)

    def _allow_stage4_best_manuscript_adoption(self) -> bool:
        return False

    def _get_stage4_exhaustion_default_choice(self) -> int:
        return self.get_stage4_policy_int("exhaustion", "default_operator_choice", default=2)

    @property
    def ctx(self):
        """[Phase 4C-2a] 파일럿 컨텍스트 (미주입 시 app에서 자동 빌드)"""
        if self._ctx is None:
            from modules.core.stage4_context import Stage4Context

            self._ctx = Stage4Context.from_app(self.app)
        return self._ctx

    @ctx.setter
    def ctx(self, value):
        self._ctx = value
        # 서브모듈이 새 ctx를 사용하도록 캐시 무효화
        self._post_processor = None
        self._context_builder = None
        self._interview_round = None

    @property
    def post_processor(self):
        """[B-1-1] Post-Processor 서브모듈 (lazy init)."""
        if self._post_processor is None:
            self._post_processor = Stage4PostProcessor(self.ctx)
        return self._post_processor

    @property
    def context_builder(self):
        """[B-1-2] Context Builder 서브모듈 (lazy init)."""
        if self._context_builder is None:
            self._context_builder = Stage4ContextBuilder(self.ctx)
        return self._context_builder

    def _log_target_ep_reached(self, *, target_ep: int, next_ep: int) -> None:
        """Record stage4 target-episode stop as a control-plane decision/audit event."""
        session_id = str(resolve_logging_session_id(getattr(self.ctx, "current_project", None)) or "")
        _sl = getattr(self.ctx, "session_logger", None)
        if _sl and hasattr(_sl, "log_decision"):
            _sl.log_decision(
                stage="stage4_control",
                ep_num=int(target_ep),
                round_num=0,
                decision_type="target_ep_reached",
                result="STOP",
                score=0,
                reason="stage4 target episode reached; stop before next episode generation",
                session_id=session_id,
                target_ep=int(target_ep),
                next_ep=int(next_ep),
            )

        _audit_event = getattr(self.ctx, "audit_event", None)
        if callable(_audit_event):
            _audit_event(
                "target_ep_reached",
                "stage4 target episode reached",
                {
                    "session_id": session_id,
                    "target_ep": int(target_ep),
                    "next_ep": int(next_ep),
                },
            )

    def _log_stage4_session_scope(self, *, start_ep: int, target_ep: int | None, total_planned_ep: int) -> None:
        """Record the bounded Stage4 live-session scope for later proof reuse."""
        session_id = str(resolve_logging_session_id(getattr(self.ctx, "current_project", None)) or "")
        payload = {
            "session_id": session_id,
            "start_ep": int(start_ep),
            "target_ep": int(target_ep) if target_ep is not None else None,
            "total_planned_ep": int(total_planned_ep),
        }
        _sl = getattr(self.ctx, "session_logger", None)
        if _sl and hasattr(_sl, "log_decision"):
            _sl.log_decision(
                stage="stage4_control",
                ep_num=int(start_ep),
                round_num=0,
                decision_type="session_scope",
                result="START",
                score=0,
                **payload,
            )

        _audit_event = getattr(self.ctx, "audit_event", None)
        if callable(_audit_event):
            _audit_event(
                "stage4_session_scope",
                "stage4 session scope declared",
                dict(payload),
            )

    def _load_chain_link_section(self, next_ep: int) -> str:
        return self.context_builder.load_chain_link_section(next_ep)

    @property
    def interview_round(self):
        """[B-1-3] Interview Round 서브모듈 (lazy init)."""
        if self._interview_round is None:
            self._interview_round = Stage4InterviewRound(self.ctx)
        return self._interview_round

    def _set_agent_telemetry_context(self, *, ep_num: int | None = None, extra_agents: list | None = None) -> None:
        """[LOG-Phase2] BaseAgent llm_calls stage/ep 메타데이터 주입."""
        targets = []
        agents = getattr(self.ctx, "agents", None)
        if isinstance(agents, dict):
            targets.extend(agents.values())
        if extra_agents:
            targets.extend(extra_agents)
        if not targets:
            return

        _ep_value = None
        if ep_num is not None:
            try:
                _ep_value = max(0, int(ep_num))
            except (TypeError, ValueError):
                _ep_value = None

        for agent in targets:
            if agent is None:
                continue
            try:
                setattr(agent, "_current_stage", 4)
            except Exception:
                pass
            if _ep_value is not None:
                try:
                    setattr(agent, "_current_ep_num", _ep_value)
                except Exception:
                    pass

    def _build_stage4_to_3_reverse_feedback(self, *, director_feedback: str, previous_attempt: dict | None) -> str:
        callback = getattr(self.ctx, "generate_reverse_feedback_stage4_to_3", None)

        reason_parts: list[str] = []
        if director_feedback:
            reason_parts.append(str(director_feedback))
        if isinstance(previous_attempt, dict):
            for key in ("rejection_reason", "open_review", "verdict_reason"):
                value = str(previous_attempt.get(key, "") or "").strip()
                if value and value not in reason_parts:
                    reason_parts.append(value)
            for key in ("reject_bucket", "gate_basis", "dominant_contradiction_type"):
                value = str(previous_attempt.get(key, "") or "").strip()
                if value:
                    reason_parts.append(f"{key}={value}")
            contradiction_types = previous_attempt.get("contradiction_types", [])
            if isinstance(contradiction_types, list) and contradiction_types:
                reason_parts.append("contradiction_types=" + ",".join(str(item) for item in contradiction_types[:5]))
            conflict_contract = previous_attempt.get("conflict_contract", {})
            if isinstance(conflict_contract, dict):
                if conflict_contract.get("completed_event_replay"):
                    reason_parts.append("completed_event_replay=True")
                contract_types = conflict_contract.get("contradiction_types", [])
                if isinstance(contract_types, list) and contract_types:
                    reason_parts.append("conflict_contract.types=" + ",".join(str(item) for item in contract_types[:5]))
            action_items = previous_attempt.get("action_items", [])
            if isinstance(action_items, list) and action_items:
                reason_parts.append(" / ".join(str(item) for item in action_items[:3]))
        reject_reason = "\n".join(part for part in reason_parts if part).strip()
        if not reject_reason:
            return ""
        completed_event_contract = Stage4Orchestrator._build_completed_event_replay_contract(reject_reason)

        pre_checklist_result = None
        if isinstance(previous_attempt, dict):
            checklist = previous_attempt.get("consistency_checklist")
            if isinstance(checklist, dict) and checklist:
                pre_checklist_result = checklist

        reverse_feedback = ""
        if not callable(callback):
            return completed_event_contract
        try:
            reverse_feedback = (
                callback(
                    writer_reject_reason=reject_reason,
                    pre_checklist_result=pre_checklist_result,
                )
                or ""
            )
        except Exception as exc:
            logging.warning("[Stage4->3] reverse feedback helper 실패: %s", exc)
        if completed_event_contract and completed_event_contract not in reverse_feedback:
            return f"{completed_event_contract}\n\n{reverse_feedback}".strip()
        return reverse_feedback

    @staticmethod
    def _build_completed_event_replay_contract(feedback: str) -> str:
        feedback_lower = str(feedback or "").lower()
        if not any(
            signal in feedback_lower
            for signal in (
                "completed_event_replay",
                "completed event",
                "already completed",
                "history conflict",
                "continuity replay",
                "replay",
                "contradiction_types=history",
                "contradiction_types=continuity",
                "conflict_contract.types=history",
                "conflict_contract.types=continuity",
                "post_select_conflict",
                "이미 완료",
                "이전 회차",
                "이전 화",
                "중복 묘사",
                "반복",
                "재연",
                "다시",
                "이미 끝난",
                "완료 사건",
                "타임라인",
            )
        ):
            return ""
        return "\n".join(
            [
                "[Completed prior event replay contract]",
                "- A completed prior-episode event must not become the next episode's scene_1/opening event again.",
                "- Treat the rejected event as already executed historical state; continue from its aftermath, consequence, or a new decision/action.",
                "- If the blueprint must mention the old event, mention it as remembered context or causal pressure, not as the live scene objective.",
                "- Regenerate scene_breakdown.scene_1.title, summary, key_events, integrated_scenario, and expected_ending so they advance after the prior event.",
            ]
        )

    @staticmethod
    def _merge_blueprint_feedback(director_feedback: str, reverse_feedback: str) -> str:
        direct = str(director_feedback or "").strip()
        reverse = str(reverse_feedback or "").strip()
        if reverse and direct and reverse not in direct:
            return f"{reverse}\n\n[Stage4 원문 피드백]\n{direct}"
        return reverse or direct

    @staticmethod
    def _build_v75d_blueprint_patch_contract(
        *,
        round_ctx: _RoundContext,
        director_feedback: str,
        previous_attempt: dict | None,
    ) -> str:
        feedback_parts: list[str] = []
        for value in (
            director_feedback,
            (previous_attempt or {}).get("rejection_reason", ""),
            (previous_attempt or {}).get("open_review", ""),
            ((previous_attempt or {}).get("feedback_provenance", {}) or {}).get("runtime_advisory", ""),
        ):
            text = str(value or "").strip()
            if text:
                feedback_parts.append(text)

        fix_pack = (previous_attempt or {}).get("fix_pack", {}) if isinstance(previous_attempt, dict) else {}
        if isinstance(fix_pack, dict):
            feedback_parts.extend(
                str(item or "").strip() for item in fix_pack.get("must_fix", []) if str(item or "").strip()
            )
            feedback_parts.extend(
                str(item or "").strip() for item in fix_pack.get("do_not_regress", []) if str(item or "").strip()
            )
            success_condition = str(fix_pack.get("success_condition", "") or "").strip()
            if success_condition:
                feedback_parts.append(success_condition)

        combined_feedback = "\n".join(part for part in feedback_parts if part).lower()
        opening_signals = ("continuity", "연속성", "시작 장소", "start location", "전화 통화", "서재 앞 복도", "현관")
        replay_signals = (
            "flashback",
            "회상",
            "replay",
            "재연",
            "과거의",
            "continuity replay",
            "history conflict",
            "completed event",
            "already completed",
            "completed_event_replay",
        )
        numeric_signals = ("20억", "22억", "수치", "신탁 자산", "현금화 금액", "페널티")
        if not any(signal in combined_feedback for signal in (*opening_signals, *replay_signals, *numeric_signals)):
            return ""

        blueprint = round_ctx.blueprint if isinstance(round_ctx.blueprint, dict) else {}
        scene_1 = blueprint.get("scene_breakdown", {}).get("scene_1", {})
        start_location = str(blueprint.get("start_location", "") or scene_1.get("location", "") or "").strip()
        time_flow = str(blueprint.get("time_flow", "") or "").strip()
        opening_transition = resolve_opening_transition_contract(blueprint)
        opening_transition_type = str(opening_transition.get("type", "") or "").strip()
        prev_ending_excerpt = smart_truncate(str(round_ctx.prev_ending or "").strip(), max_chars=220, head_chars=140)
        chain_link_excerpt = smart_truncate(
            str(round_ctx.chain_link_section or "").strip(),
            max_chars=220,
            head_chars=140,
        )

        lines = [
            "[V75-D correction contract]",
            "- opening continuity를 고칠 때는 top-level opening field와 scene_breakdown.scene_1 field를 함께 수정하세요.",
            "- start_location, time_flow, scene_breakdown.scene_1.location, scene_breakdown.scene_1.summary, scene_breakdown.scene_1.key_events를 서로 일치시키세요.",
        ]
        if start_location:
            lines.append(
                f"- authoritative opening location은 '{start_location}'입니다. 다른 장소로 바꾸려면 scene_1 내부에 explicit transition을 먼저 기입하세요."
            )
        if time_flow:
            lines.append(
                f"- authoritative opening time marker는 '{time_flow}'입니다. 시간 점프가 있으면 scene_1 summary와 key_events에 명시하세요."
            )
        if opening_transition_type:
            lines.append(
                f"- authoritative opening_transition.type은 '{opening_transition_type}'입니다. opening anchors와 scene_1 contract를 이 타입과 모순되게 바꾸지 마세요."
            )
            if opening_transition_type == OPENING_TRANSITION_DIRECT:
                lines.append(
                    "- direct_continuation이면 직전 ending의 후속 비트를 유지하고 새 jump/cut를 임의로 추가하지 마세요."
                )
            elif opening_transition_type == OPENING_TRANSITION_EXPLICIT:
                lines.append(
                    "- explicit_transition이면 scene_1 summary/key_events 첫 비트에 전환 문장 또는 cut을 남기고 새 anchor를 즉시 못 박으세요."
                )
            elif opening_transition_type == OPENING_TRANSITION_JUMP:
                lines.append(
                    "- jump_opening이면 direct continuation처럼 위장하지 말고 새 장소/시간/상태를 첫 비트에서 바로 선언하세요."
                )
        if any(signal in combined_feedback for signal in replay_signals):
            completed_event_contract = Stage4Orchestrator._build_completed_event_replay_contract(combined_feedback)
            if completed_event_contract:
                lines.append(completed_event_contract)
            lines.extend(
                [
                    "- EP1에서 이미 완료된 전화/행동을 EP2 opening에서 회상·재연 장면으로 다시 쓰지 마세요.",
                    "- EP2 opening은 직전 장면의 후속 비트 또는 explicit transition으로 시작해야 하며, 이전 장면의 핵심 이벤트를 새 장면으로 재상연하면 안 됩니다.",
                    "- 라운지, 차량 내부, 도로 관찰, 현관 박차고 나감 같은 새 공간/행동은 scene_1에서 explicit transition 없이 먼저 등장시키지 마세요.",
                ]
            )
        if any(signal in combined_feedback for signal in numeric_signals):
            lines.append(
                "- 수치 연속성을 고칠 때는 integrated_scenario, scene_1.summary, scene_1.key_events, expected_ending의 숫자 표현을 함께 갱신하고 stale value를 남기지 마세요."
            )
        if prev_ending_excerpt:
            lines.append(f"- 직전 화 ending authority excerpt: {prev_ending_excerpt}")
        if chain_link_excerpt:
            lines.append(f"- chain_link carryover excerpt: {chain_link_excerpt}")
        return "\n".join(lines).strip()

    # ═══════════════════════════════════════════════════════════════════════
    # [LM-A-1] Bible → world_laws 자동 등록 (최초 1회)
    # ═══════════════════════════════════════════════════════════════════════

    def _register_bible_world_laws(self) -> None:
        """Bible의 WorldLaws를 WorldState에 CRITICAL 우선순위로 등록."""
        try:
            bible = getattr(self.ctx.current_project, "master_bible", None)
            if not bible or not isinstance(bible, dict):
                return
            bible_root = bible.get("MasterBible", bible)
            if not isinstance(bible_root, dict):
                return
            world_laws = bible_root.get("WorldLaws", [])
            if not world_laws or not isinstance(world_laws, list):
                return
            for law in world_laws:
                if isinstance(law, str) and law.strip():
                    self.ctx.world_state.add_world_law(law.strip(), ep=0, priority="CRITICAL")
            if world_laws:
                _perf_logger.info("[LM-A-1] Bible → world_laws %d건 등록 완료", len(world_laws))
        except Exception as e:
            _perf_logger.debug("[LM-A-1] Bible world_laws 등록 실패 (비치명): %s", e)

    # ═══════════════════════════════════════════════════════════════════════
    # [TF-49b] Blueprint 사전검증 — 원고 생성 전 수치/팩트 정합성 LLM 체크
    # ═══════════════════════════════════════════════════════════════════════

    def _preflight_validate_blueprint(self, *, blueprint, arc_data, ep_num) -> dict:
        """[TF-49b] Blueprint 사전검증 — 수치/팩트 정합성 LLM 체크.

        Fail-open: 모든 예외 → pass 반환 (A-3이 백업).
        Returns: {"passed": bool, "issues": list, "summary": str, "patched_blueprint": dict|None}
        """
        import json

        _pass_result = {"passed": True, "issues": [], "summary": "", "patched_blueprint": None}

        # Feature flag 체크
        try:
            _enabled = _threshold("blueprint_preflight.enabled", True)
            _min_ep = _threshold("blueprint_preflight.min_episode", 2)
        except Exception:
            return _pass_result

        if not _enabled or ep_num < _min_ep:
            return _pass_result

        try:
            from modules.core.constants import AIModels
            from modules.core.continuity_pin_guard import apply_continuity_pins
            from modules.core.prompt_loader import PromptLoader
            from modules.core.response_schemas import BLUEPRINT_PREFLIGHT_SCHEMA
            from modules.core.tactical_utils import extract_episode_tactical

            try:
                _template = PromptLoader().load("blueprint_generator", "BLUEPRINT_PREFLIGHT_VALIDATE_PROMPT")
            except Exception as e:
                _perf_logger.debug("[TF-49b] Preflight 프롬프트 로드 실패 (비치명): %s", e)
                return _pass_result

            _request = self._build_blueprint_preflight_request(
                blueprint=blueprint,
                arc_data=arc_data,
                ep_num=ep_num,
                prompt_template=_template,
                apply_continuity_pins_fn=apply_continuity_pins,
                extract_episode_tactical_fn=extract_episode_tactical,
            )

            # 3. Flash 모델 직접 호출
            from google.genai import types

            _response = generate_content_via_router(
                client=self.ctx.sys.api_client,
                model=AIModels.FLASH_ANALYSIS_MODEL,
                contents=_request.prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    response_schema=BLUEPRINT_PREFLIGHT_SCHEMA,
                ),
            )
            _result = json.loads(_response.text)
            return self._resolve_blueprint_preflight_result(
                ep_num=ep_num,
                result=_result,
                patched_blueprint=_request.patched_blueprint,
            )

        except Exception as e:
            _perf_logger.debug("[TF-49b] Preflight 전체 실패 (fail-open): %s", e)
            return _pass_result

    def _build_blueprint_preflight_request(
        self,
        *,
        blueprint,
        arc_data,
        ep_num: int,
        prompt_template: str,
        apply_continuity_pins_fn,
        extract_episode_tactical_fn,
    ) -> _BlueprintPreflightRequest:
        import json

        ws_summary = ""
        if self.ctx.world_state:
            try:
                ws_summary = self.ctx.world_state.get_summary(max_chars=8000)
            except Exception:
                pass

        fl_summary = ""
        if self.ctx.fact_ledger:
            try:
                fl_summary = self.ctx.fact_ledger.get_canonical_summary(max_chars=5000)
            except Exception:
                pass

        arc_tactical = ""
        if arc_data:
            try:
                arc_tactical = extract_episode_tactical_fn(
                    arc_data.get("tactical_doc", ""),
                    ep_num,
                    episode_details=arc_data.get("episode_details"),
                )[:3000]
            except Exception:
                pass

        prev_published_text = ""
        try:
            db = getattr(getattr(self.ctx, "current_project", None), "db", None)
            prev_row = load_final_accepted_manuscript_row(db, ep_num - 1) if db and ep_num > 1 else None
            if isinstance(prev_row, dict):
                prev_published_text = str(
                    prev_row.get("content") or prev_row.get("corrected_manuscript") or prev_row.get("manuscript") or ""
                )
            elif prev_row:
                prev_published_text = str(prev_row)
        except Exception:
            prev_published_text = ""

        pin_result = apply_continuity_pins_fn(
            blueprint,
            previous_published_text=prev_published_text,
            arc_tactical_text=arc_tactical,
        )
        patched_blueprint = None
        blueprint_for_validation = blueprint
        if pin_result.get("changes"):
            patched_blueprint = pin_result.get("blueprint", blueprint)
            if isinstance(patched_blueprint, dict):
                patched_blueprint["_continuity_pins"] = pin_result["changes"]
                blueprint_for_validation = patched_blueprint

        def _esc(text: str) -> str:
            return text.replace("{", "{{").replace("}", "}}")

        bp_json = json.dumps(blueprint_for_validation, ensure_ascii=False, indent=2)[:15000]
        prompt = prompt_template.format(
            world_state_summary=_esc(ws_summary) if ws_summary else "(상태 정보 없음)",
            fact_ledger_summary=_esc(fl_summary) if fl_summary else "(수치 기록 없음)",
            arc_tactical_excerpt=_esc(arc_tactical) if arc_tactical else "(전술서 없음)",
            ep_num=ep_num,
            blueprint_json=_esc(bp_json),
        )
        return _BlueprintPreflightRequest(
            prompt=prompt,
            patched_blueprint=patched_blueprint,
        )

    def _resolve_blueprint_preflight_result(self, *, ep_num: int, result: dict, patched_blueprint) -> dict:
        issues = result.get("issues", [])
        summary = result.get("summary", "")

        false_positive_patterns = (
            "출처 불분명",
            "출처가 불분명",
            "획득 경로",
            "획득 경위",
            "보유 근거",
            "기록되지 않",
            "갑작스러운 등장",
            "갑자기 등장",
            "고증",
            "시대",
            "연도",
            "해상도",
            "모니터",
            "컴퓨터",
        )
        critical_patterns = (
            "사망",
            "deceased",
            "시간 역행",
            "역행",
            "소진",
            "소모된",
            "불가능",
            "도달 불가",
            "모순",
        )
        for issue in issues:
            if issue.get("severity") != "high":
                continue
            combined = f"{issue.get('category', '')} {issue.get('description', '')}"
            if any(pattern in combined for pattern in false_positive_patterns):
                issue["severity"] = "low"
            elif not any(pattern in combined for pattern in critical_patterns):
                issue["severity"] = "low"

        high_issues = [issue for issue in issues if issue.get("severity") == "high"]
        truly_failed = not result.get("passed", True) and len(high_issues) > 0
        if not truly_failed:
            level = "PASS" if result.get("passed", True) else "PASS (low/medium only)"
            _perf_logger.info("[TF-49b] Preflight %s — 제%d화 Blueprint 정합성 확인", level, ep_num)
            if issues and not result.get("passed", True):
                self.ctx.ui.log(f"   ℹ️ [TF-49b] Preflight: {len(issues)}건 참고 사항 (경미, 패치 불필요)")
            return {
                "passed": True,
                "issues": issues,
                "summary": summary,
                "patched_blueprint": patched_blueprint,
            }

        high_count = len(high_issues)
        log_level = "⚠️" if high_count > 0 else "ℹ️"
        self.ctx.ui.log(
            f"   {log_level} [TF-49b] Preflight: {len(issues)}건 발견 (high={high_count}) → CW/Director advisory 전달"
        )
        for issue in issues[:5]:
            self.ctx.ui.log(
                f"      [{issue.get('severity', '?')}] {issue.get('category', '?')}: "
                f"{issue.get('description', '')[:80]}"
            )

        advisory_lines = [f"[TF-49b Preflight 발견 사항 — 제{ep_num}화]"]
        for issue in issues[:10]:
            sev = issue.get("severity", "?")
            cat = issue.get("category", "?")
            desc = issue.get("description", "")
            advisory_lines.append(f"  - [{sev}] {cat}: {desc}")
        advisory_lines.append("위 사항에 주의하여 원고 작성/심사에 반영하세요.")
        advisory_text = "\n".join(advisory_lines)

        self._log_escalation_event(ep_num, "TF49b_PREFLIGHT", len(issues), success=True)
        return {
            "passed": True,
            "issues": issues,
            "summary": summary,
            "patched_blueprint": patched_blueprint,
            "advisory": advisory_text,
        }

    # NOTE: _preflight_patch_blueprint 삭제됨 (TF-49b v2: advisory 전달 방식으로 전환)
    # Blueprint 자체를 수정하지 않고, CW/Director에게 advisory로 전달.

    # ═══════════════════════════════════════════════════════════════════════
    # [V68] 에피소드 연결고리 (Episode Chain Links)
    # ═══════════════════════════════════════════════════════════════════════

    def _extract_chain_link(self, ep_num: int, manuscript: str, blueprint: dict = None) -> dict:
        """
        [V68] 원고 확정 후 다음 화 연결고리를 구조화 추출.

        Director 에이전트(LLM)로 정밀 추출.
        추출 실패 시 빈 dict 반환 (기존 동작 유지).

        Args:
            ep_num: 확정된 에피소드 번호
            manuscript: 확정된 원고 전문
            blueprint: 해당 에피소드 블루프린트 (선택)

        Returns:
            dict: chain_link 구조
        """
        if not manuscript or len(manuscript) < 200:
            return {}

        try:
            self._set_agent_telemetry_context(ep_num=ep_num)
            _escaped_tail = self.ctx.agents["director"]._escape_braces(manuscript[-3000:])
            prompt = f"""아래 원고의 마지막 상황을 분석하여 다음 화에서 반드시 이어받아야 할 요소를 추출하세요.

원고 (제{ep_num}화, 마지막 3000자):
{_escaped_tail}

JSON으로 출력:
{{
    "cliffhanger": "현재 진행 중인 상황/위기/긴장 (없으면 빈 문자열)",
    "pending_actions": ["다음 화에서 해야 할 행동 목록 (최대 5개)"],
    "emotional_state": "주인공의 현재 감정 상태 (한 줄)",
    "physical_state": "부상/피로/상태 (정상이면 '정상')",
    "location": "현재 위치 (구체적으로)",
    "time_marker": "작중 시간대 (알 수 있으면, 모르면 빈 문자열)"
}}"""

            result = self.ctx.agents["director"].ask(prompt, temperature=0.1)
            chain_link = self.ctx.agents["director"]._extract_json_robust(result)

            if chain_link and isinstance(chain_link, dict):
                chain_link.setdefault("cliffhanger", "")
                chain_link.setdefault("pending_actions", [])
                chain_link.setdefault("emotional_state", "")
                chain_link.setdefault("physical_state", "정상")
                chain_link.setdefault("location", "")
                chain_link.setdefault("time_marker", "")
                return chain_link
            return {}
        except Exception as e:
            _perf_logger.warning(f"[V68] chain_link 추출 실패 (ep={ep_num}): {str(e)[:80]}")
            return {}

    def _build_writer_prompt_supplements(self, *, anti_trope_prompt: str) -> _WriterPromptSupplements:
        purism_prompt = ""
        _guard = getattr(getattr(self.ctx, "sys", None), "guard", None)
        if _guard:
            try:
                purism_prompt = _guard.get_v20_purism_prompt()
                if hasattr(_guard, "get_retrieval_contract_prompt"):
                    _work_contract = str(_guard.get_retrieval_contract_prompt("manuscript") or "").strip()
                    if _work_contract:
                        purism_prompt = "\n\n".join(part for part in (purism_prompt, _work_contract) if part)
            except Exception as e:
                self.ctx.ui.log(f"   ⚠️ Guard Purism Prompt 추출 실패 (비치명): {e}")

        npc_equipment_summary = ""
        try:
            bible_root = self.ctx.current_project.master_bible.get("MasterBible", self.ctx.current_project.master_bible)
            assets = bible_root.get("AssetLibrary", {})
            key_npcs = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])
            npc_equipment_lines = []
            for npc in key_npcs:
                if isinstance(npc, dict):
                    npc_name = npc.get("name") or npc.get("Name", "알 수 없음")
                    npc_hud = npc.get("NPC_Martial_HUD", {})
                    if isinstance(npc_hud, dict):
                        equip = npc_hud.get("equipment", [])
                        if equip:
                            npc_equipment_lines.append(f"- {npc_name}: {equip}")
            npc_equipment_summary = "\n".join(npc_equipment_lines) if npc_equipment_lines else "NPC 장비 정보 없음"
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ NPC 장비 현황 추출 실패 (비차단): {e}")
            npc_equipment_summary = ""

        effective_anti_trope = anti_trope_prompt
        diversity_engine = getattr(self.ctx, "diversity_engine", None)
        if diversity_engine:
            try:
                _diversity_cot = diversity_engine.get_writer_injection()
                if _diversity_cot:
                    effective_anti_trope = f"{anti_trope_prompt}\n\n{_diversity_cot}"
            except Exception as _e:
                logging.debug("[Stage4] diversity_engine 주입 실패 (무시): %s", _e)

        intro_dna = ""
        try:
            _bible = self.ctx.current_project.master_bible
            _br = _bible.get("MasterBible", _bible) if isinstance(_bible, dict) else {}
            intro_dna = _br.get("protagonist_config", {}).get("personality", "")
        except Exception:
            logging.debug("[Stage4] intro_dna Bible 로드 실패 (빈 문자열 폴백)")

        return _WriterPromptSupplements(
            purism_prompt=purism_prompt,
            npc_equipment_summary=npc_equipment_summary,
            effective_anti_trope=effective_anti_trope,
            intro_dna=intro_dna,
        )

    def _prepare_current_episode_inputs(self, *, next_ep: int) -> _EpisodeLoopInputs | None:
        blueprint = self.ctx.current_project.get_blueprint(next_ep)
        if not blueprint:
            self.ctx.ui.log(f"⚠️ 제{next_ep}화 Blueprint 없음. Stage 3 먼저 실행하세요.")
            return None

        def _safe_int(value, default: int = 0) -> int:
            try:
                return int(value or default)
            except (TypeError, ValueError):
                return default

        arc_data = next(
            (
                arc
                for arc in self.ctx.current_project.arcs
                if isinstance(arc, dict)
                and _safe_int(arc.get("ep_start")) <= next_ep <= resolve_arc_end_episode(arc_data=arc, fallback_ep=0)
            ),
            None,
        )
        if not arc_data:
            self.ctx.ui.log(f"⚠️ 제{next_ep}화 Arc 데이터 없음.")
            return None

        prev_manuscript_text = ""
        try:
            db = getattr(self.ctx.current_project, "db", None)
            prev_row = load_final_accepted_manuscript_row(db, next_ep - 1) if db and next_ep > 1 else None
            if isinstance(prev_row, dict):
                prev_manuscript_text = str(
                    prev_row.get("content") or prev_row.get("corrected_manuscript") or prev_row.get("manuscript") or ""
                )
            elif prev_row:
                prev_manuscript_text = str(prev_row)
        except Exception:
            prev_manuscript_text = ""

        frontier_status = blueprint.get("_frontier_status") if isinstance(blueprint, dict) else {}
        frontier_status_value = ""
        if isinstance(frontier_status, dict):
            frontier_status_value = str(frontier_status.get("status") or "")
        if frontier_status_value in {
            "requires_actual_manuscript_revalidation",
            "requires_director_frontier_adjudication",
            "contaminated_requires_regeneration",
        }:
            marker_satisfied = frontier_status_satisfied_by_stage3_lineage(
                blueprint=blueprint,
                frontier_status=frontier_status,
                prev_manuscript_text=prev_manuscript_text,
            )
            if marker_satisfied:
                self.ctx.ui.log(
                    f"   [Stage4 Frontier Status] 제{next_ep}화 Blueprint는 확정 원고 기준 재생성 lineage가 확인되어 진행합니다."
                )
            else:
                self.ctx.ui.log(
                    f"   ⛔ [Stage4 Frontier Status] 제{next_ep}화 Blueprint는 {frontier_status_value} 상태입니다. Stage3 재생성이 필요합니다."
                )
                self._log_escalation_event(
                    next_ep,
                    "STAGE4_FRONTIER_STATUS_BLOCK",
                    1,
                    success=False,
                    reason=frontier_status_value,
                    contradiction_type="frontier_status",
                )
                self._stage4_completion_blocked = True
                return None

        stale_check = detect_stage4_frontier_staleness(
            ep_num=next_ep,
            blueprint=blueprint,
            arc_data=arc_data,
            prev_manuscript_text=prev_manuscript_text,
        )
        if stale_check.get("stale") and stale_check.get("severity") == "hard":
            reasons = stale_check.get("reasons") or []
            reason_text = "; ".join(str(reason) for reason in reasons[:3])
            marked_eps = mark_downstream_frontier_requires_adjudication(
                project=self.ctx.current_project,
                ep_num=next_ep,
                arc_data=arc_data,
                stale_check=stale_check,
            )
            self.ctx.ui.log(f"   ⛔ [Stage4 Frontier Staleness] 제{next_ep}화 Blueprint가 직전 확정 원고와 충돌합니다.")
            if reason_text:
                self.ctx.ui.log(f"      {reason_text[:240]}")
            if marked_eps:
                self.ctx.ui.log(f"      frontier adjudication required: ep {marked_eps[0]}~{marked_eps[-1]}")
            self._log_escalation_event(
                next_ep,
                "STAGE4_FRONTIER_STALE_PREFLIGHT",
                len(reasons),
                success=False,
                reason=reason_text,
                contradiction_type="frontier_staleness",
            )
            self._stage4_completion_blocked = True
            return None

        preflight = self._preflight_validate_blueprint(
            blueprint=blueprint,
            arc_data=arc_data,
            ep_num=next_ep,
        )
        return _EpisodeLoopInputs(
            blueprint=preflight.get("patched_blueprint") or blueprint,
            arc_data=arc_data,
            preflight_advisory=preflight.get("advisory", ""),
        )

    def _build_episode_prompt_bundle(
        self,
        *,
        next_ep: int,
        arc_data: dict,
        blueprint: dict,
        arc_tactical: str,
        prev_text: str,
        prev_ending: str,
        hud_report: str,
        anchor_sys,
        s4_genre_type: str,
        v50_modules_available: bool,
    ) -> _EpisodePromptBundle:
        genre_name = (getattr(self.ctx.current_project, "genre", None) or {}).get("name", "무협")
        writer_agent = self.ctx.agents.get("writer") if "writer" in self.ctx.agents else None
        ctx_prompts = self.context_builder.build_mandatory_context(
            next_ep=next_ep,
            arc_data=arc_data,
            arc_tactical=arc_tactical,
            prev_text=prev_text,
            prev_ending=prev_ending,
            hud_report=hud_report,
            writer_agent=writer_agent,
            anchor_sys=anchor_sys,
            s4_genre_type=s4_genre_type,
            v50_modules_available=v50_modules_available,
            blueprint=blueprint,
            pacing_analyzer=self.ctx.pacing_analyzer,
        )
        anti_trope_prompt = ctx_prompts["anti_trope_prompt"]
        prompt_supplements = self._build_writer_prompt_supplements(
            anti_trope_prompt=anti_trope_prompt,
        )
        return _EpisodePromptBundle(
            genre_name=genre_name,
            ctx_prompts=ctx_prompts,
            prompt_supplements=prompt_supplements,
        )

    def _build_episode_round_context(
        self,
        *,
        ep_ctx: dict,
        ctx_prompts: dict,
        chief_writer,
        manuscript_validator,
        consistency_validator,
        blocking_validator,
        continuity_validator,
        next_ep: int,
        blueprint: dict,
        arc_data: dict,
        story_context: str,
        style_guide: str,
        reference_excerpt: str,
        preflight_advisory: str,
        prompt_bundle: _EpisodePromptBundle,
    ) -> _RoundContext:
        prompt_supplements = prompt_bundle.prompt_supplements
        return self.context_builder.build_round_context(
            ep_ctx=ep_ctx,
            ctx_prompts=ctx_prompts,
            chief_writer=chief_writer,
            manuscript_validator=manuscript_validator,
            consistency_validator=consistency_validator,
            blocking_validator=blocking_validator,
            continuity_validator=continuity_validator,
            next_ep=next_ep,
            blueprint=blueprint,
            arc_data=arc_data,
            purism_prompt=prompt_supplements.purism_prompt,
            genre_name=prompt_bundle.genre_name,
            npc_equipment_summary=prompt_supplements.npc_equipment_summary,
            effective_anti_trope=prompt_supplements.effective_anti_trope,
            intro_dna=prompt_supplements.intro_dna,
            story_context=story_context,
            style_guide=style_guide,
            reference_excerpt=reference_excerpt,
            mandatory_context=ctx_prompts["mandatory_context"],
            preflight_advisory=preflight_advisory,
        )

    def _prepare_episode_round(
        self,
        *,
        next_ep: int,
        arc_data: dict,
        blueprint: dict,
        chief_writer,
        manuscript_validator,
        consistency_validator,
        blocking_validator,
        continuity_validator,
        story_context: str,
        style_guide: str,
        reference_excerpt: str,
        preflight_advisory: str,
        anchor_sys,
        s4_genre_type: str,
        v50_modules_available: bool,
    ) -> _RoundContext:
        ep_ctx = self.context_builder.prepare_episode_context(next_ep, arc_data, chief_writer)
        prompt_bundle = self._build_episode_prompt_bundle(
            next_ep=next_ep,
            arc_data=arc_data,
            blueprint=blueprint,
            arc_tactical=ep_ctx["arc_tactical"],
            prev_text=ep_ctx["prev_text"],
            prev_ending=ep_ctx["prev_ending"],
            hud_report=ep_ctx["hud_report"],
            anchor_sys=anchor_sys,
            s4_genre_type=s4_genre_type,
            v50_modules_available=v50_modules_available,
        )
        ctx_prompts = prompt_bundle.ctx_prompts

        self.ctx.ui.log(f"\n{'=' * 60}")
        self.ctx.ui.log(
            f"📝 제{next_ep}화 집필 시작 (Arc {arc_data.get('arc_no', '?')}, 위치 {ep_ctx['arc_pos']}/{ep_ctx['total_ep_in_arc']})"
        )
        self.ctx.ui.log(f"{'=' * 60}")

        ctx_prompts["mandatory_context"] = self._apply_mandatory_context_budget(ctx_prompts["mandatory_context"])
        return self._build_episode_round_context(
            ep_ctx=ep_ctx,
            ctx_prompts=ctx_prompts,
            chief_writer=chief_writer,
            manuscript_validator=manuscript_validator,
            consistency_validator=consistency_validator,
            blocking_validator=blocking_validator,
            continuity_validator=continuity_validator,
            next_ep=next_ep,
            blueprint=blueprint,
            arc_data=arc_data,
            story_context=story_context,
            style_guide=style_guide,
            reference_excerpt=reference_excerpt,
            preflight_advisory=preflight_advisory,
            prompt_bundle=prompt_bundle,
        )

    def _apply_mandatory_context_budget(self, mandatory_context: str) -> str:
        mc_max = _threshold("context.mandatory_context_max", 80000)
        if len(mandatory_context) <= mc_max:
            return mandatory_context

        original_len = len(mandatory_context)
        ctx_budget_meta = getattr(self.ctx, "_stage4_context_budget_meta", {}) or {}
        if isinstance(ctx_budget_meta, dict) and ctx_budget_meta:
            budget_ledger = ctx_budget_meta.get("budget_ledger") or {}
            _perf_logger.info(
                "[V66.1] mandatory_context pretrim meta sc=%s mc=%s total=%s limit=%s headroom=%s effective=%s dropped=%s overflow=%s",
                ctx_budget_meta.get("sc_chars"),
                ctx_budget_meta.get("mc_chars"),
                ctx_budget_meta.get("total_chars"),
                ctx_budget_meta.get("limit_chars"),
                ctx_budget_meta.get("headroom_chars"),
                budget_ledger.get("effective_cap"),
                budget_ledger.get("dropped_chars"),
                budget_ledger.get("overflow_chars"),
            )

        budget_result = _fit_mandatory_context_budget(
            mandatory_context,
            max_chars=mc_max,
        )
        trimmed = budget_result.mandatory_context
        if budget_result.removed_count > 0:
            _perf_logger.info(
                f"[V66.1] mandatory_context {budget_result.removed_count}개 섹션 제거 ({budget_result.removed_chars}자)"
            )
            self.ctx.ui.log(
                f"   ⚠️ [V66.1] mandatory_context {original_len}자 → {len(trimmed)}자 (섹션 {budget_result.removed_count}개 제거)"
            )
        elif budget_result.used_fallback:
            self.ctx.ui.log(f"   ⚠️ [V66.1] mandatory_context {original_len}자 → {mc_max:,}자로 truncate (폴백)")
        return trimmed

    def _process_episode_pass(
        self,
        *,
        next_ep: int,
        final_manuscript: str,
        final_title,
        final_state_updates: dict,
        blueprint: dict,
        arc_data: dict,
        output_dir,
        v50_modules_available: bool,
    ) -> bool:
        if not self.post_processor.process_pass_result(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
            final_title=final_title,
            final_state_updates=final_state_updates,
            blueprint=blueprint,
            arc_data=arc_data,
            output_dir=output_dir,
            v50_modules_available=v50_modules_available,
            extract_chain_link_fn=self._extract_chain_link,
            detect_npc_overexposure_fn=_detect_npc_overexposure,
            detect_cross_episode_repetition_fn=_detect_cross_episode_repetition,
        ):
            self.ctx.ui.log(f"   ⛔ [EP {next_ep}] DB 저장 실패. 집필 중단.")
            return False

        prm = getattr(self.ctx, "pass_rate_monitor", None)
        if prm is not None:
            try:
                alerts = prm.check_alerts()
                for alert in alerts:
                    logging.warning(f"[PassRate 경보] {alert}")
            except Exception as e:
                logging.debug("[Stage4] PassRateMonitor.check_alerts 실패 (무시): %s", e)
        return True

    def _consume_episode_round_outcome(
        self,
        *,
        outcome: _RoundOutcome,
        next_ep: int,
        blueprint: dict,
        arc_data: dict,
        output_dir,
        v50_modules_available: bool,
        skip_pause: bool,
    ) -> _EpisodeLoopDisposition:
        if outcome.should_return:
            self.post_processor.run_post_episode_tasks(skip_pause=skip_pause)
            return _EpisodeLoopDisposition(should_return=True)

        if outcome.final_manuscript and not self._process_episode_pass(
            next_ep=next_ep,
            final_manuscript=outcome.final_manuscript,
            final_title=outcome.final_title,
            final_state_updates=outcome.final_state_updates,
            blueprint=blueprint,
            arc_data=arc_data,
            output_dir=output_dir,
            v50_modules_available=v50_modules_available,
        ):
            self._stage4_completion_blocked = True
            return _EpisodeLoopDisposition(should_break=True)

        return _EpisodeLoopDisposition()

    def _checkpoint_episode_loop(
        self,
        *,
        loop_guard: int,
        max_loops: int,
        target_ep,
        chief_writer,
    ) -> _EpisodeLoopCheckpoint:
        if loop_guard > max_loops:
            self.ctx.ui.log("🚨 [Safety] 루프 상한 도달. 중단합니다.")
            return _EpisodeLoopCheckpoint(should_break=True)

        next_ep = self.ctx.current_project.get_latest_episode_number()
        self.interview_round.time_warnings = []
        self._set_agent_telemetry_context(ep_num=next_ep, extra_agents=[chief_writer])
        if target_ep and next_ep > target_ep:
            self._log_target_ep_reached(target_ep=int(target_ep), next_ep=int(next_ep))
            self.ctx.ui.log(f"🏁 목표 회차({target_ep}화) 도달. 종료합니다.")
            return _EpisodeLoopCheckpoint(should_break=True)

        return _EpisodeLoopCheckpoint(next_ep=next_ep)

    def _run_interview_loop(self, session: _SessionConfig, *, skip_pause: bool = False) -> bool:
        """[4-R1-e-4] Run main episode production loop.

        Returns True if caller should return early.
        """
        runtime = self._prepare_interview_loop_runtime(session)
        if runtime is None:
            return False
        start_ep = int(self.ctx.current_project.get_latest_episode_number() or 1)
        self._log_stage4_session_scope(
            start_ep=start_ep,
            target_ep=runtime.target_ep,
            total_planned_ep=session.total_planned_ep,
        )

        # 5. 원고 생산 메인 루프
        loop_guard = 0
        while True:
            loop_guard += 1
            _loop_checkpoint = self._checkpoint_episode_loop(
                loop_guard=loop_guard,
                max_loops=runtime.max_loops,
                target_ep=runtime.target_ep,
                chief_writer=runtime.chief_writer,
            )
            if _loop_checkpoint.should_break:
                break
            _loop_disposition = self._run_episode_loop_iteration(
                session=session,
                runtime=runtime,
                next_ep=_loop_checkpoint.next_ep,
                skip_pause=skip_pause,
            )
            if _loop_disposition.should_return:
                return True
            if _loop_disposition.should_break:
                break

        # [V62.3] Stage 4 루프 종료
        self.post_processor.run_post_episode_tasks(skip_pause=skip_pause)

        return False

    def _prepare_interview_loop_runtime(self, session: _SessionConfig) -> _InterviewLoopRuntime | None:
        target_ep = session.target_ep
        total_planned_ep = session.total_planned_ep

        # [P1-D2] total_planned_ep=0 방어 (블루프린트 없는 경우)
        if not target_ep and total_planned_ep <= 0:
            self.ctx.ui.log("⚠️ 블루프린트가 없습니다. Stage 2를 먼저 실행하세요.")
            return None
        # [Sweep45] max(1, ...) — latest_ep > total_planned_ep 시 음수 방지
        max_loops = max(
            1, min((target_ep or total_planned_ep) - self.ctx.current_project.get_latest_episode_number() + 5, 100)
        )

        # [V66.1] B-2: ReferenceAnchor 루프 밖 1회 생성 (내부 캐시로 DB 중복 조회 방지)
        from modules.core.reference_anchor import ReferenceAnchor

        anchor_sys = ReferenceAnchor(self.ctx.current_project)

        # [LM-A-1] Bible → world_laws 자동 등록 (최초 1회)
        if self.ctx.world_state and not self.ctx.world_state.get_world_laws():
            self._register_bible_world_laws()

        return _InterviewLoopRuntime(
            chief_writer=session.chief_writer,
            target_ep=target_ep,
            output_dir=session.output_dir,
            v50_modules_available=session.v50_modules_available,
            max_loops=max_loops,
            anchor_sys=anchor_sys,
        )

    def _run_episode_loop_iteration(
        self,
        *,
        session: _SessionConfig,
        runtime: _InterviewLoopRuntime,
        next_ep: int,
        skip_pause: bool = False,
    ) -> _EpisodeLoopDisposition:
        episode_inputs = self._prepare_current_episode_inputs(next_ep=next_ep)
        if episode_inputs is None:
            return _EpisodeLoopDisposition(should_break=True)

        round_ctx = self._prepare_episode_round(
            next_ep=next_ep,
            arc_data=episode_inputs.arc_data,
            blueprint=episode_inputs.blueprint,
            chief_writer=session.chief_writer,
            manuscript_validator=session.manuscript_validator,
            consistency_validator=session.consistency_validator,
            blocking_validator=session.blocking_validator,
            continuity_validator=session.continuity_validator,
            story_context=session.story_context,
            style_guide=session.style_guide,
            reference_excerpt=session.reference_excerpt,
            preflight_advisory=episode_inputs.preflight_advisory,
            anchor_sys=runtime.anchor_sys,
            s4_genre_type=session.s4_genre_type,
            v50_modules_available=runtime.v50_modules_available,
        )
        outcome = self._handle_round_outcome(round_ctx=round_ctx)
        return self._consume_episode_round_outcome(
            outcome=outcome,
            next_ep=next_ep,
            blueprint=episode_inputs.blueprint,
            arc_data=episode_inputs.arc_data,
            output_dir=runtime.output_dir,
            v50_modules_available=runtime.v50_modules_available,
            skip_pause=skip_pause,
        )

    @staticmethod
    def _build_interview_round_loop_state() -> _InterviewRoundLoopState:
        return _InterviewRoundLoopState()

    def _run_interview_round_step(
        self,
        *,
        round_ctx: _RoundContext,
        loop_state: _InterviewRoundLoopState,
        next_ep: int,
        interview_round: int,
        max_rounds: int,
        stage4_spinner,
    ) -> _InterviewRoundStepDisposition:
        self.ctx.ui.log(
            f"   🔄 [Round {interview_round + 1}/{max_rounds}] 원고 생성 시도...",
            stage="stage4",
            component="round_execution",
            ep_num=next_ep,
            arc_num=round_ctx.arc_data.get("arc_no", 0),
            round_num=interview_round,
            event_kind="progress",
        )
        round_result = self.interview_round.run(
            round_num=interview_round,
            stage4_spinner=stage4_spinner,
            director_feedback=loop_state.director_feedback,
            previous_attempt=loop_state.previous_attempt,
            round_ctx=round_ctx,
        )
        if str(round_result.verdict or "").strip().upper() in self._get_stage4_accept_verdicts():
            pass_disposition = self.outcome_runtime.handle_pass_round_result(
                round_ctx=round_ctx,
                round_result=round_result,
                next_ep=next_ep,
                interview_round=interview_round,
                max_rounds=max_rounds,
                pathology_counts=loop_state.pathology_counts,
                pathology_repeat_emitted=loop_state.pathology_repeat_emitted,
            )
            _step_disposition = self._apply_pass_round_step_disposition(
                round_ctx=round_ctx,
                loop_state=loop_state,
                pass_disposition=pass_disposition,
            )
            if _step_disposition is not None:
                return _step_disposition

        reject_step = self.outcome_runtime.handle_reject_round_result(
            round_ctx=round_ctx,
            round_result=round_result,
            next_ep=next_ep,
            interview_round=interview_round,
            max_rounds=max_rounds,
            logic_error_streak=loop_state.logic_error_streak,
            inplace_attempted=loop_state.inplace_attempted,
            blueprint_regenerated=loop_state.blueprint_regenerated,
            prev_reject_bucket=loop_state.prev_reject_bucket,
            bucket_streak=loop_state.bucket_streak,
            prev_dominant_contradiction=loop_state.prev_dominant_contradiction,
            contradiction_type_streak=loop_state.contradiction_type_streak,
            score_history=loop_state.score_history,
            plateau_advisory_emitted=loop_state.plateau_advisory_emitted,
            tf29_advisory_emitted=loop_state.tf29_advisory_emitted,
            pathology_counts=loop_state.pathology_counts,
            pathology_repeat_emitted=loop_state.pathology_repeat_emitted,
        )
        self._apply_reject_round_step_disposition(loop_state=loop_state, reject_step=reject_step)
        return _InterviewRoundStepDisposition(
            round_ctx=reject_step.round_ctx,
            loop_state=loop_state,
        )

    @staticmethod
    def _apply_pass_round_step_disposition(
        *,
        round_ctx: _RoundContext,
        loop_state: _InterviewRoundLoopState,
        pass_disposition: _PassRoundDisposition,
    ) -> _InterviewRoundStepDisposition | None:
        loop_state.final_manuscript = pass_disposition.final_manuscript
        loop_state.final_title = pass_disposition.final_title
        loop_state.final_state_updates = pass_disposition.final_state_updates
        loop_state.director_feedback = pass_disposition.director_feedback
        loop_state.previous_attempt = pass_disposition.previous_attempt
        if pass_disposition.should_continue:
            return _InterviewRoundStepDisposition(
                round_ctx=round_ctx,
                loop_state=loop_state,
                should_continue=True,
            )
        if pass_disposition.accepted:
            return _InterviewRoundStepDisposition(
                round_ctx=round_ctx,
                loop_state=loop_state,
                should_break=True,
            )
        return None

    @staticmethod
    def _apply_reject_round_step_disposition(
        *,
        loop_state: _InterviewRoundLoopState,
        reject_step: _RejectRoundStepDisposition,
    ) -> None:
        loop_state.director_feedback = reject_step.director_feedback
        loop_state.previous_attempt = reject_step.previous_attempt
        loop_state.logic_error_streak = reject_step.logic_error_streak
        loop_state.inplace_attempted = reject_step.inplace_attempted
        loop_state.blueprint_regenerated = reject_step.blueprint_regenerated
        loop_state.prev_reject_bucket = reject_step.prev_reject_bucket
        loop_state.bucket_streak = reject_step.bucket_streak
        loop_state.prev_dominant_contradiction = reject_step.prev_dominant_contradiction
        loop_state.contradiction_type_streak = reject_step.contradiction_type_streak
        loop_state.score_history = reject_step.score_history
        loop_state.plateau_advisory_emitted = reject_step.plateau_advisory_emitted
        loop_state.tf29_advisory_emitted = reject_step.tf29_advisory_emitted

    def _hydrate_round_loop_resume_state(
        self,
        *,
        round_ctx: _RoundContext,
        loop_state: _InterviewRoundLoopState,
    ) -> _InterviewRoundLoopState:
        if isinstance(loop_state.previous_attempt, dict) and loop_state.previous_attempt:
            return loop_state

        hydrated = self.interview_round.hydrate_persisted_stage4_previous_attempt(
            next_ep=round_ctx.next_ep,
            arc_num=int((round_ctx.arc_data or {}).get("arc_no", 0) or 0),
            previous_attempt=loop_state.previous_attempt,
        )
        if not hydrated:
            return loop_state

        loop_state.previous_attempt = hydrated
        if not str(loop_state.director_feedback or "").strip():
            feedback_provenance = hydrated.get("feedback_provenance")
            if not isinstance(feedback_provenance, dict):
                feedback_provenance = {}
            loop_state.director_feedback = str(
                feedback_provenance.get("merged_feedback")
                or hydrated.get("merged_director_feedback")
                or hydrated.get("rejection_reason")
                or ""
            ).strip()
        return loop_state

    def _handle_round_outcome(self, *, round_ctx: _RoundContext) -> _RoundOutcome:
        """[4-R1-e-3] Run N-round interview loop (N = retry.director_max_attempts).

        Returns _RoundOutcome: final_manuscript, final_title, final_state_updates, should_return
        """
        from modules.core.spinners import StageSpinner

        next_ep = round_ctx.next_ep

        loop_state = self._build_interview_round_loop_state()
        loop_state = self._hydrate_round_loop_resume_state(
            round_ctx=round_ctx,
            loop_state=loop_state,
        )
        rounds_attempted = 0

        with StageSpinner(4, f"제{next_ep}화 · 앙상블 준비") as stage4_spinner:
            _max_rounds = self._get_stage4_max_rounds()

            for interview_round in range(_max_rounds):
                rounds_attempted = interview_round + 1
                _step_disposition = self._run_interview_round_step(
                    round_ctx=round_ctx,
                    loop_state=loop_state,
                    next_ep=next_ep,
                    interview_round=interview_round,
                    max_rounds=_max_rounds,
                    stage4_spinner=stage4_spinner,
                )
                round_ctx = _step_disposition.round_ctx
                loop_state = _step_disposition.loop_state
                if _step_disposition.should_continue:
                    continue
                if _step_disposition.should_break:
                    break

        return self._finalize_round_outcome_loop(
            next_ep=next_ep,
            max_rounds=_max_rounds,
            final_manuscript=loop_state.final_manuscript,
            final_title=loop_state.final_title,
            final_state_updates=loop_state.final_state_updates,
            previous_attempt=loop_state.previous_attempt,
            blueprint_regenerated=loop_state.blueprint_regenerated,
            rounds_attempted=rounds_attempted,
        )

    def _finalize_round_outcome_loop(
        self,
        *,
        next_ep: int,
        max_rounds: int,
        final_manuscript,
        final_title,
        final_state_updates: dict,
        previous_attempt: dict,
        blueprint_regenerated: bool,
        rounds_attempted: int,
    ) -> _RoundOutcome:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}

        def _emit_shadow(final_result: str, *, accepted: bool, used_best_manuscript: bool = False) -> None:
            self._emit_stage4_retry_shadow_compare(
                next_ep=next_ep,
                max_rounds=max_rounds,
                rounds_attempted=rounds_attempted,
                final_result=final_result,
                accepted=accepted,
                used_best_manuscript=used_best_manuscript,
                blueprint_regenerated=blueprint_regenerated,
            )

        # ===== 설정된 라운드 수 모두 실패 =====
        # [V75-B] B-Full: 블루프린트 재생성까지 했는데도 실패 → Arc 재생성 제안
        if not final_manuscript and blueprint_regenerated:
            self.ctx.ui.log("   🚨 [V75-B] 블루프린트 재생성 후에도 실패. Arc(전술서) 자체에 문제가 있을 수 있습니다.")
            self.ctx.ui.log("   💡 Stage 2에서 Arc를 재생성하면 해결될 수 있습니다.")
        if not final_manuscript:
            last_best = previous_attempt.get("best_manuscript", "")
            last_score = previous_attempt.get("score", 0)
            if last_best and self._allow_stage4_best_manuscript_adoption():
                self.ctx.ui.log(f"\n⚠️ [EP {next_ep}] {max_rounds}회 소진. 마지막 최선 결과물(score={last_score}) 존재.")
                choice = self._get_stage4_exhaustion_default_choice()
                if callable(getattr(self.ctx, "get_int_input", None)):
                    choice = self.ctx.get_int_input(
                        "  1=최선 결과물로 진행  2=건너뛰기: ", default=2, min_val=1, max_val=2
                    )
                if choice == 1:
                    final_manuscript = last_best
                    final_title = final_title or f"제{next_ep}화"
                    final_state_updates = previous_attempt.get("state_updates", {})  # [TF-R3-S4-03] 폴백 시 상태 복구
                else:
                    _emit_shadow("SKIP", accepted=False)
                    return _RoundOutcome(
                        final_manuscript=None,
                        final_title=None,
                        final_state_updates={},
                        should_return=True,
                    )
            else:
                if last_best:
                    self.ctx.ui.log(
                        f"\n⛔ [EP {next_ep}] {max_rounds}회 면담 모두 실패. "
                        f"마지막 최선 결과물(score={last_score})은 Director 미승인 상태라 진행할 수 없습니다."
                    )
                self.ctx.ui.log(f"\n⛔ [EP {next_ep}] {max_rounds}회 면담 모두 실패. 인간 검토 필요.")
                _emit_shadow("HUMAN_REVIEW", accepted=False)
                return _RoundOutcome(
                    final_manuscript=None,
                    final_title=None,
                    final_state_updates={},
                    should_return=True,
                )

        used_best_manuscript = False
        _emit_shadow(
            "PASS",
            accepted=bool(final_manuscript),
            used_best_manuscript=used_best_manuscript,
        )
        return _RoundOutcome(
            final_manuscript=final_manuscript,
            final_title=final_title,
            final_state_updates=final_state_updates,
            should_return=False,
        )

    def _emit_stage4_retry_shadow_compare(
        self,
        *,
        next_ep: int,
        max_rounds: int,
        rounds_attempted: int,
        final_result: str,
        accepted: bool,
        used_best_manuscript: bool,
        blueprint_regenerated: bool,
    ) -> None:
        shadow_max_rounds = self._get_stage4_shadow_max_rounds()
        if shadow_max_rounds is None or rounds_attempted <= 0:
            return

        shadow_clipped = rounds_attempted > shadow_max_rounds
        if not shadow_clipped and not self._stage4_shadow_log_all_episodes():
            return

        payload = {
            "shadow_max_rounds": int(shadow_max_rounds),
            "actual_max_rounds": int(max_rounds),
            "rounds_attempted": int(rounds_attempted),
            "final_result": str(final_result or "").strip(),
            "accepted": bool(accepted),
            "used_best_manuscript": bool(used_best_manuscript),
            "blueprint_regenerated": bool(blueprint_regenerated),
            "shadow_clipped": bool(shadow_clipped),
        }
        result = "WOULD_CLIP" if shadow_clipped else "WITHIN_SHADOW"

        _sl = getattr(self.ctx, "session_logger", None)
        if _sl and hasattr(_sl, "log_decision"):
            _sl.log_decision(
                stage="stage4_control",
                ep_num=int(next_ep),
                round_num=max(0, int(rounds_attempted) - 1),
                decision_type="retry_shadow_compare",
                result=result,
                score=0,
                **payload,
            )

        audit_event = getattr(self.ctx, "audit_event", None)
        if callable(audit_event):
            audit_event(
                "stage4_retry_shadow_compare",
                "stage4 retry shadow comparison recorded",
                dict(payload),
            )

    def _apply_v75d_inplace_repair(
        self,
        *,
        round_ctx: _RoundContext,
        next_ep: int,
        interview_round: int,
        director_feedback: str,
        previous_attempt: dict,
        logic_error_streak: int,
        tf29_advisory: str,
        dominant_contradiction: str,
    ) -> _RetryEscalationDisposition:
        inplace_attempted = True
        patch_attempt = self._run_v75d_patch_attempt(
            round_ctx=round_ctx,
            next_ep=next_ep,
            interview_round=interview_round,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            logic_error_streak=logic_error_streak,
            tf29_advisory=tf29_advisory,
        )

        self._log_escalation_event(
            next_ep,
            "V75-D_INPLACE",
            patch_attempt.logic_error_streak,
            success=patch_attempt.success,
            round_num=interview_round,
            fix_scope=(patch_attempt.previous_attempt or {}).get("fix_scope", ""),
            reason=patch_attempt.director_feedback,
            contradiction_type=dominant_contradiction,
            candidate_key=str(patch_attempt.artifact_payload.artifact_meta.get("candidate_key", "") or "").strip(),
            content_hash=str(patch_attempt.artifact_payload.artifact_meta.get("content_hash", "") or "").strip(),
            artifact_path=str(patch_attempt.artifact_payload.artifact_meta.get("artifact_path", "") or "").strip(),
        )
        return _RetryEscalationDisposition(
            round_ctx=patch_attempt.round_ctx,
            director_feedback=patch_attempt.director_feedback,
            previous_attempt=patch_attempt.previous_attempt,
            logic_error_streak=patch_attempt.logic_error_streak,
            inplace_attempted=inplace_attempted,
            blueprint_regenerated=False,
        )

    def _run_v75d_patch_attempt(
        self,
        *,
        round_ctx: _RoundContext,
        next_ep: int,
        interview_round: int,
        director_feedback: str,
        previous_attempt: dict,
        logic_error_streak: int,
        tf29_advisory: str,
    ) -> _V75DPatchAttemptPayload:
        patched_bp = self._attempt_v75d_inplace_blueprint_patch(
            round_ctx=round_ctx,
            next_ep=next_ep,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            logic_error_streak=logic_error_streak,
        )
        if patched_bp:
            return self._apply_v75d_patch_success(
                round_ctx=round_ctx,
                patched_bp=patched_bp,
                next_ep=next_ep,
                interview_round=interview_round,
                director_feedback=director_feedback,
                previous_attempt=previous_attempt,
                logic_error_streak=logic_error_streak,
                tf29_advisory=tf29_advisory,
            )
        return self._build_failed_v75d_patch_attempt_payload(
            round_ctx=round_ctx,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            logic_error_streak=logic_error_streak,
        )

    def _attempt_v75d_inplace_blueprint_patch(
        self,
        *,
        round_ctx: _RoundContext,
        next_ep: int,
        director_feedback: str,
        previous_attempt: dict,
        logic_error_streak: int,
    ) -> dict | None:
        try:
            self.ctx.ui.log(f"   🔧 [V75-D] LOGIC_ERROR {logic_error_streak}연속 → 블루프린트 inplace 패치 시도...")
            patched_bp = self._request_v75d_inplace_blueprint_patch(
                round_ctx=round_ctx,
                next_ep=next_ep,
                director_feedback=director_feedback,
                previous_attempt=previous_attempt,
            )
            if not patched_bp:
                self.ctx.ui.log("   ⚠️ [V75-D] inplace 패치 실패 — 기존 블루프린트 유지")
            return patched_bp
        except Exception as patch_err:
            logging.warning("[FailClosed:V75-D] inplace 패치 실패: %s", patch_err)
            return None

    def _build_failed_v75d_patch_attempt_payload(
        self,
        *,
        round_ctx: _RoundContext,
        director_feedback: str,
        previous_attempt: dict,
        logic_error_streak: int,
    ) -> _V75DPatchAttemptPayload:
        return _V75DPatchAttemptPayload(
            round_ctx=round_ctx,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            logic_error_streak=logic_error_streak,
            success=False,
            artifact_payload=_V75DArtifactPayload(
                artifact_meta={
                    "candidate_key": "",
                    "content_hash": "",
                    "artifact_path": "",
                }
            ),
        )

    def _request_v75d_inplace_blueprint_patch(
        self,
        *,
        round_ctx: _RoundContext,
        next_ep: int,
        director_feedback: str,
        previous_attempt: dict,
    ) -> dict | None:
        bp_agent = self.ctx.agents.get("three_phase_bp")
        if not bp_agent:
            return None
        reverse_feedback_43 = self._build_stage4_to_3_reverse_feedback(
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
        )
        blueprint_feedback = self._merge_blueprint_feedback(
            director_feedback,
            reverse_feedback_43,
        )
        correction_contract = self._build_v75d_blueprint_patch_contract(
            round_ctx=round_ctx,
            director_feedback=blueprint_feedback,
            previous_attempt=previous_attempt,
        )
        if correction_contract and correction_contract not in blueprint_feedback:
            blueprint_feedback = f"{blueprint_feedback}\n\n{correction_contract}".strip()
        return bp_agent._inplace_patch_blueprint(
            original_blueprint=round_ctx.blueprint,
            director_feedback=blueprint_feedback,
            ep_num=next_ep,
            arc_data=round_ctx.arc_data,
        )

    def _apply_v75d_patch_success(
        self,
        *,
        round_ctx: _RoundContext,
        patched_bp: dict,
        next_ep: int,
        interview_round: int,
        director_feedback: str,
        previous_attempt: dict,
        logic_error_streak: int,
        tf29_advisory: str,
    ) -> _V75DPatchAttemptPayload:
        artifact_payload = self._capture_v75d_patch_artifact(
            round_ctx=round_ctx,
            patched_bp=patched_bp,
            next_ep=next_ep,
            interview_round=interview_round,
        )
        success_payload = self._build_v75d_success_payload(
            round_ctx=round_ctx,
            patched_bp=patched_bp,
            tf29_advisory=tf29_advisory,
        )
        self.ctx.ui.log("   ✅ [V75-D] inplace 패치 성공")
        return _V75DPatchAttemptPayload(
            round_ctx=success_payload.round_ctx,
            director_feedback=success_payload.director_feedback,
            previous_attempt=success_payload.previous_attempt,
            logic_error_streak=success_payload.logic_error_streak,
            success=True,
            artifact_payload=artifact_payload,
        )

    def _capture_v75d_patch_artifact(
        self,
        *,
        round_ctx: _RoundContext,
        patched_bp: dict,
        next_ep: int,
        interview_round: int,
    ) -> _V75DArtifactPayload:
        bp_change_ratio = None
        try:
            import json as _json_mod

            from modules.core.constants import calc_patch_change_ratio, log_patch_diff

            bp_orig_json = _json_mod.dumps(round_ctx.blueprint, ensure_ascii=False, indent=2)
            bp_patch_json = _json_mod.dumps(patched_bp, ensure_ascii=False, indent=2)
            log_patch_diff("S4-V75D-Blueprint", bp_orig_json, bp_patch_json)
            bp_change_ratio = calc_patch_change_ratio(
                _json_mod.dumps(round_ctx.blueprint, ensure_ascii=False),
                _json_mod.dumps(patched_bp, ensure_ascii=False),
            )
            if bp_change_ratio > 0.30:
                logging.warning("[TF-IPG] V75-D Blueprint 변경 비율 %.1f%% > 30%%", bp_change_ratio * 100)
        except Exception as diff_err:
            logging.debug("[TF-IPG] V75-D diff 계산 실패: %s", diff_err)
        bp_artifact_meta = snapshot_logged_artifact(
            getattr(self.ctx, "current_project", None),
            stage=4,
            ep_num=next_ep,
            attempt_num=interview_round + 1,
            candidate_key=build_candidate_key(
                label="V75-D",
                strategy="blueprint_inplace",
                fallback="v75d_blueprint_patch",
            ),
            artifact_kind="patched_blueprint_after_fix",
            payload=patched_bp,
        )
        audit_event = getattr(self.ctx, "audit_event", None)
        if callable(audit_event):
            audit_payload = {
                "ep_num": int(next_ep),
                "round_num": int(interview_round + 1),
                "candidate_key": str(bp_artifact_meta.get("candidate_key", "") or "").strip(),
                "content_hash": str(bp_artifact_meta.get("content_hash", "") or "").strip(),
                "artifact_path": str(bp_artifact_meta.get("artifact_path", "") or "").strip(),
            }
            if isinstance(bp_change_ratio, int | float):
                audit_payload["change_ratio"] = float(bp_change_ratio)
            audit_event(
                "stage4_v75d_blueprint_patch_snapshot",
                "stage4 V75-D blueprint patch snapshot persisted",
                audit_payload,
            )
        return _V75DArtifactPayload(
            artifact_meta=bp_artifact_meta,
            change_ratio=float(bp_change_ratio) if isinstance(bp_change_ratio, int | float) else None,
        )

    @staticmethod
    def _build_v75d_success_payload(
        *,
        round_ctx: _RoundContext,
        patched_bp: dict,
        tf29_advisory: str,
    ) -> _V75DSuccessPayload:
        success_feedback = (
            "[V75-D 블루프린트 inplace 패치 완료]\n"
            "지적된 논리적 결함만 수정되었습니다. "
            "수정된 블루프린트 기반으로 원고를 작성하세요."
        )
        if tf29_advisory:
            success_feedback = tf29_advisory + "\n" + success_feedback
        return _V75DSuccessPayload(
            round_ctx=dataclasses.replace(round_ctx, blueprint=patched_bp),
            director_feedback=success_feedback,
            previous_attempt={},
            logic_error_streak=0,
        )

    def _apply_v75b_blueprint_regeneration(
        self,
        *,
        round_ctx: _RoundContext,
        next_ep: int,
        interview_round: int,
        director_feedback: str,
        previous_attempt: dict,
        logic_error_streak: int,
        tf29_advisory: str,
        dominant_contradiction: str,
    ) -> _RetryEscalationDisposition:
        v75b_success = False
        blueprint_regenerated = False
        try:
            self.ctx.ui.log(f"   🔄 [V75-B] LOGIC_ERROR {logic_error_streak}연속 → 블루프린트 재생성 시도...")
            reverse_feedback_43 = self._build_stage4_to_3_reverse_feedback(
                director_feedback=director_feedback,
                previous_attempt=previous_attempt,
            )
            new_bp = self._regenerate_blueprint(
                next_ep,
                round_ctx.arc_data,
                round_ctx,
                external_feedback=self._merge_blueprint_feedback(director_feedback, reverse_feedback_43),
            )
            if new_bp:
                v75b_success = True
                round_ctx = dataclasses.replace(round_ctx, blueprint=new_bp)
                blueprint_regenerated = True
                logic_error_streak = 0
                director_feedback = (
                    "[V75-B 블루프린트 재생성 완료]\n"
                    "이전 블루프린트의 논리적 결함으로 재생성되었습니다. "
                    "새 블루프린트 기반으로 원고를 작성하세요."
                )
                if tf29_advisory:
                    director_feedback = tf29_advisory + "\n" + director_feedback
                previous_attempt = {}
                self.ctx.ui.log("   ✅ [V75-B] 블루프린트 재생성 성공")
            else:
                blueprint_regenerated = True
                self.ctx.ui.log("   ⚠️ [V75-B] 블루프린트 재생성 실패 — 기존 블루프린트 유지")
        except Exception as regen_err:
            blueprint_regenerated = True
            logging.warning("[SilentPass:V75-B] 블루프린트 재생성 실패: %s", regen_err)

        self._log_escalation_event(
            next_ep,
            "V75-B_FULL_REGEN",
            logic_error_streak,
            success=v75b_success,
            round_num=interview_round,
            fix_scope=(previous_attempt or {}).get("fix_scope", ""),
            reason=director_feedback,
            contradiction_type=dominant_contradiction,
        )
        return _RetryEscalationDisposition(
            round_ctx=round_ctx,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            logic_error_streak=logic_error_streak,
            inplace_attempted=True,
            blueprint_regenerated=blueprint_regenerated,
        )

    def _log_escalation_event(
        self,
        ep_num,
        event_type,
        streak,
        *,
        success,
        round_num: int | None = None,
        attempt_key: str = "",
        fix_scope: str = "",
        reason: str = "",
        contradiction_type: str = "",
        candidate_key: str = "",
        content_hash: str = "",
        artifact_path: str = "",
    ):
        """[V76] 에스컬레이션 이벤트를 episode_production.jsonl에 기록."""
        try:
            import datetime
            import os

            logs_dir = resolve_project_log_dir(getattr(self.ctx, "current_project", None))
            if logs_dir is None:
                logs_dir = Path("projects") / str(self.ctx.current_project.name) / "logs"
            os.makedirs(logs_dir, exist_ok=True)
            entry = {
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "ep": ep_num,
                "event": event_type,
                "streak": streak,
                "success": success,
            }
            if round_num is not None:
                entry["round_num"] = int(round_num)
            if attempt_key:
                entry["attempt_key"] = str(attempt_key).strip()
            if fix_scope:
                entry["fix_scope"] = str(fix_scope).strip()
            if contradiction_type:
                entry["contradiction_type"] = str(contradiction_type).strip()
            if candidate_key:
                entry["candidate_key"] = str(candidate_key).strip()
            if content_hash:
                entry["content_hash"] = str(content_hash).strip()
            if artifact_path:
                entry["artifact_path"] = str(artifact_path).strip()
            _reason = str(reason or "").strip()
            if _reason:
                entry["reason"] = _reason[:240]
            append_jsonl_record(Path(logs_dir) / "episode_production.jsonl", entry)
        except Exception as e:
            logging.warning("[V76] escalation log 실패: %s", e)

    def _regenerate_blueprint(
        self,
        ep_num: int,
        arc_data: dict,
        round_ctx: _RoundContext,
        external_feedback: str = "",
    ) -> dict | None:
        """[V75-B] Stage 3 블루프린트 재생성 (단일 에피소드)."""
        try:
            bp_agent = self.ctx.agents.get("three_phase_bp")
            if not bp_agent:
                return None

            prev_bp = None
            if ep_num > 1:
                prev_bp = self.ctx.current_project.get_blueprint(ep_num - 1)

            _bible_root = self.ctx.current_project.master_bible.get(
                "MasterBible",
                self.ctx.current_project.master_bible,
            )
            _prot_config = _bible_root.get("protagonist_config", {})
            _prot_name = _prot_config.get("name", "")

            _entity_registry = {}
            _state_ext = self.ctx.agents.get("state_extractor")
            if _state_ext and hasattr(_state_ext, "extract_cumulative_state"):
                try:
                    _entity_registry = _state_ext.extract_cumulative_state(ep_num - 1) or {}
                except Exception as e:
                    logging.warning("[TF-26] state_extractor cumulative_state failed: %s", str(e)[:100])

            self._set_agent_telemetry_context(ep_num=ep_num)
            new_bp, _ = bp_agent.generate(
                ep_num=ep_num,
                arc_data=arc_data,
                arc_idx=(arc_data.get("arc_no") or 1) - 1,
                prev_blueprint=prev_bp,
                prev_blueprints=[],
                prev_manuscripts_text=str(getattr(round_ctx, "prev_manuscripts_text", "") or ""),
                external_feedback=str(external_feedback or ""),
                entity_registry=_entity_registry,
                protagonist_name=_prot_name,
                protagonist_config=_prot_config,
                director=self.ctx.agents.get("director"),
                state_tracker=getattr(self.ctx, "state_tracker", None),
                db=getattr(self.ctx.current_project, "db", None),
            )

            if new_bp and isinstance(new_bp, dict):
                attach_stage3_blueprint_lineage_meta(
                    new_bp,
                    db=getattr(self.ctx.current_project, "db", None),
                    ep_num=ep_num,
                )
                self.ctx.current_project.save_episode_blueprint(ep_num, new_bp)
                return new_bp
            return None
        except Exception as e:
            logging.warning("[V75-B] 블루프린트 재생성 내부 실패: %s", e)
            return None

    def _resolve_session_target_ep(
        self,
        *,
        target_ep: int | None,
        limit_mode: bool,
        current_written: int,
        total_planned_ep: int,
    ) -> _SessionTargetDecision:
        if target_ep is not None:
            if target_ep <= current_written:
                self.ctx.ui.log(f"✅ 이미 {current_written}화까지 완료되어 제{target_ep}화 집필은 건너뜁니다.")
                return _SessionTargetDecision(should_abort=True)
            return _SessionTargetDecision(target_ep=target_ep)

        if not limit_mode:
            return _SessionTargetDecision()

        if total_planned_ep == 0:
            self.ctx.ui.log("⚠️ 블루프린트가 없습니다. Stage 3에서 먼저 설계도를 생성해주세요.")
            return _SessionTargetDecision(should_abort=True)
        if current_written >= total_planned_ep:
            self.ctx.ui.log(f"✅ 이미 {current_written}화까지 완료되어 추가 집필할 범위가 없습니다.")
            return _SessionTargetDecision(should_abort=True)
        return _SessionTargetDecision(
            target_ep=self.ctx.get_int_input(
                f"\n👉 몇 화까지 집필하시겠습니까? (현재 {current_written}화 / 최대 {total_planned_ep}화): ",
                default=total_planned_ep,
                min_val=current_written + 1,
                max_val=total_planned_ep,
            )
        )

    def _resolve_session_style_guide(self, *, stage0_available: bool) -> _SessionStyleGuidePayload:
        style_guide = ""
        reference_excerpt = ""
        bible_pov = ""
        try:
            bible_pov = resolve_project_bible_pov(self.ctx.current_project)
        except Exception as e:
            _perf_logger.warning(f"[SilentPass:Stage4] Bible POV 조회 실패: {e!s:.100}")

        saved_style = load_style_guide_anchor(self.ctx.current_project)
        if saved_style:
            try:
                from modules.core.stage0 import StyleGuide

                loaded_sg = StyleGuide.from_dict(saved_style)
                if bible_pov:
                    if loaded_sg.pov and bible_pov != loaded_sg.pov:  # [TF-31-2]
                        logging.warning(
                            "[TF-31-2] StyleGuide POV(%s) ≠ Bible POV(%s) — Bible 우선 적용",
                            loaded_sg.pov,
                            bible_pov,
                        )
                    loaded_sg.pov = bible_pov
                style_guide = loaded_sg.to_prompt()
                reference_excerpt = getattr(loaded_sg, "reference_excerpt", "")
                self.ctx.ui.log(
                    f"🎨 [V60.95] 저장된 스타일 가이드 로드됨 (톤: {loaded_sg.tone}, 시점: {loaded_sg.pov})"
                )
            except Exception as e:
                _perf_logger.warning(
                    f"[SilentPass:Stage4] Stage0 StyleGuide 렌더 실패, payload fallback 사용: {e!s:.100}"
                )
                style_guide, reference_excerpt, tone, resolved_pov = _render_style_guide_payload(
                    saved_style,
                    bible_pov=bible_pov,
                )
                if style_guide:
                    self.ctx.ui.log(f"🎨 [V60.95] 저장된 스타일 가이드 로드됨 (톤: {tone}, 시점: {resolved_pov})")

        reference_excerpt = _clamp_reference_excerpt(reference_excerpt)

        if not style_guide:
            file_style = load_style_guide_file(self.ctx.current_project)
            if file_style:
                style_guide, reference_excerpt, tone, resolved_pov = _render_style_guide_payload(
                    file_style,
                    bible_pov=bible_pov,
                )
                if style_guide:
                    reference_excerpt = _clamp_reference_excerpt(reference_excerpt)
                    self.ctx.ui.log(f"🎨 [V60.95] Stage0 style_guide.json 로드됨 (톤: {tone}, 시점: {resolved_pov})")

        if not style_guide:
            try:
                from modules.core.stage0 import StyleGuide as _SG

                if bible_pov:
                    min_style_guide = _SG(pov=bible_pov)
                    style_guide = min_style_guide.to_prompt()
                    self.ctx.ui.log(f"📖 [V70] Bible POV 기반 최소 스타일 가이드 생성 (시점: {bible_pov})")
            except Exception as e:
                _perf_logger.warning(f"[SilentPass:Stage4] Bible POV 기반 스타일 가이드 생성 실패: {e!s:.100}")

        if not style_guide:
            style_choice = self.ctx.get_int_input(
                "\n👉 스타일 선택 (1.카카오 / 2.네이버): ", default=1, min_val=1, max_val=2
            )
            style_guide = (
                "네이버: 심리 묘사 강조, 3-4문장 단위 줄바꿈, 여백 극대화"
                if style_choice == 2
                else "카카오: 사이다 전개, 절벽걸기, 4K 해상도 묘사"
            )
            save_anchor = getattr(self.ctx.current_project, "save_v20_anchor", None)
            if callable(save_anchor):
                try:
                    fallback_pov = bible_pov or "1인칭"
                    save_anchor(
                        "style_guide",
                        {
                            "tone": "네이버" if style_choice == 2 else "카카오",
                            "pov": fallback_pov,
                            "selected_primary_pov": fallback_pov,
                            "effective_primary_pov": fallback_pov,
                            "external_pov_insert_policy": default_external_pov_insert_policy(fallback_pov),
                            "fallback_style_prompt": style_guide,
                            "reference_excerpt": "",
                        },
                    )
                    self.ctx.ui.log("💾 [V60.95] 선택된 플랫폼 스타일을 style_guide anchor로 저장했습니다.")
                except Exception as e:
                    _perf_logger.warning(f"[SilentPass:Stage4] style_guide fallback anchor 저장 실패: {e!s:.100}")

        return _SessionStyleGuidePayload(
            style_guide=style_guide,
            reference_excerpt=reference_excerpt,
        )

    def _build_session_story_context(self, *, s4_genre_type: str) -> str:
        story_context = ""
        try:
            bible_root = self.ctx.current_project.master_bible.get(
                "MasterBible",
                self.ctx.current_project.master_bible,
            )
            protagonist_config = bible_root.get("protagonist_config", {})
            story_context_parts = [f"- 장르: {s4_genre_type}"]
            if protagonist_config:
                story_context_parts.append(f"- 주인공 이름: {protagonist_config.get('name', '미상')}")
                story_context_parts.append(f"- 세계 출신: {protagonist_config.get('world_origin', '미상')}")
                incarnation = protagonist_config.get("incarnation_type", "미상")
                story_context_parts.append(f"- 환생 유형: {incarnation}")
                if incarnation == "회귀자":
                    story_context_parts.append(
                        "→ 주인공은 미래에서 되돌아온 회귀자입니다. 미래의 사건, 주가, 인물 등을 미리 알고 있으며, 이 지식을 활용해 현재 역사를 의도적으로 변경하려 합니다. 이것은 모순이 아닙니다."
                    )
                elif incarnation == "빙의자":
                    story_context_parts.append(
                        "→ 주인공은 다른 인물의 몸에 빙의한 존재입니다. 원래 인물의 기억/관계와 현재 인격이 다를 수 있습니다."
                    )
                elif incarnation == "환생자":
                    story_context_parts.append(
                        "→ 주인공은 전생의 기억을 가진 환생자입니다. 전생의 지식이 단편적으로 나타날 수 있습니다."
                    )
                core_traits = protagonist_config.get("core_traits", "")
                if core_traits:
                    story_context_parts.append(f"- 핵심 특성: {core_traits}")
            story_context = "\n".join(story_context_parts)
            _perf_logger.info(f"📋 [V67.1] story_context 조립 완료 ({len(story_context)}자)")
        except Exception as story_context_err:
            _perf_logger.warning(f"⚠️ [V67.1] story_context 조립 실패 (비차단): {str(story_context_err)[:50]}")
            story_context = f"- 장르: {s4_genre_type}"
        return story_context

    def _apply_character_voice_guide(self, *, style_guide: str) -> str:
        character_voice = getattr(self.ctx, "character_voice", None)
        if not character_voice or not character_voice.profiles:
            return style_guide

        try:
            voice_prompt = character_voice.get_writer_injection()
            if voice_prompt:
                style_guide += f"\n\n{voice_prompt}"
                self.ctx.ui.log(f"🎤 [V62.5] 캐릭터 보이스 가이드 주입됨 ({len(character_voice.profiles)}명)")
        except Exception as voice_err:
            self.ctx.ui.log(f"   ⚠️ 캐릭터 보이스 주입 실패 (비차단): {voice_err}")
        return style_guide

    def _initialize_session_agents(
        self,
        *,
        chief_writer_cls,
        manuscript_validator_cls,
        consistency_validator_cls,
        blocking_validator_cls,
        continuity_validator_cls,
        writer_model,
    ) -> _SessionAgentBootstrap:
        s4_genre_type = self.ctx.selected_genre.get("type", "wuxia") if self.ctx.selected_genre else "wuxia"
        return _SessionAgentBootstrap(
            chief_writer=chief_writer_cls(
                context=self.ctx.current_project,
                client=self.ctx.sys.api_client,
                model_tier=writer_model,
            ),
            manuscript_validator=manuscript_validator_cls(
                context=self.ctx.current_project,
                genre_type=s4_genre_type,
                llm_client=self.ctx.sys.api_client,
            ),
            consistency_validator=consistency_validator_cls(
                guard=getattr(self.ctx.sys, "guard", None),
                genre=s4_genre_type,
            ),
            blocking_validator=blocking_validator_cls(context=self.ctx.current_project),
            continuity_validator=continuity_validator_cls(context=self.ctx.current_project),
            s4_genre_type=s4_genre_type,
        )

    def _prepare_session_environment(self) -> _SessionEnvironmentPayload:
        output_dir = self.ctx.current_project.paths.drafts
        output_dir.mkdir(exist_ok=True)
        total_planned_ep = self.ctx.current_project.db.get_latest_blueprint_number()
        current_written = max(0, int(self.ctx.current_project.get_latest_episode_number() or 1) - 1)
        return _SessionEnvironmentPayload(
            output_dir=output_dir,
            total_planned_ep=total_planned_ep,
            current_written=current_written,
        )

    def _prepare_session_ui(self, *, writer_model: str) -> None:
        self.ctx.ui.log("🎬 [V60.80] Stage 4 V2 - Chief Writer 주권주의 아키텍처 가동")
        self.ctx.ui.log(f"   • Chief Writer 모델: {writer_model}")
        self.ctx.ui.log("   • 앙상블: 3개 병렬 생성")
        self.ctx.ui.log("   • Director 면담: 5번 기회 (패치 모드 전 라운드 적용)")
        self.ctx.ui.console.clear()
        self.ctx.ui.title("V60.80 CHIEF WRITER", "Director 주권주의 아키텍처")

    @staticmethod
    def _build_session_config(
        *,
        agent_bootstrap: _SessionAgentBootstrap,
        story_context: str,
        style_guide: str,
        reference_excerpt: str,
        target_ep,
        session_environment: _SessionEnvironmentPayload,
        v50_modules_available: bool,
    ) -> _SessionConfig:
        return _SessionConfig(
            chief_writer=agent_bootstrap.chief_writer,
            manuscript_validator=agent_bootstrap.manuscript_validator,
            consistency_validator=agent_bootstrap.consistency_validator,
            blocking_validator=agent_bootstrap.blocking_validator,
            continuity_validator=agent_bootstrap.continuity_validator,
            s4_genre_type=agent_bootstrap.s4_genre_type,
            story_context=story_context,
            style_guide=style_guide,
            reference_excerpt=reference_excerpt,
            target_ep=target_ep,
            output_dir=session_environment.output_dir,
            v50_modules_available=v50_modules_available,
            total_planned_ep=session_environment.total_planned_ep,
        )

    def _validate_session_prerequisites(self, *, error_emoji: str) -> bool:
        if self.ctx.current_project.master_bible and self.ctx.current_project.arcs:
            return True
        self.ctx.ui.log(f"{error_emoji} [System] Bible 또는 Arc 데이터가 없습니다. Stage 1-2를 먼저 실행하세요.")
        return False

    def _prepare_session_style_payload(self, *, stage0_available: bool) -> _SessionStyleGuidePayload:
        style_payload = self._resolve_session_style_guide(stage0_available=stage0_available)
        return _SessionStyleGuidePayload(
            style_guide=self._apply_character_voice_guide(style_guide=style_payload.style_guide),
            reference_excerpt=style_payload.reference_excerpt,
        )

    @staticmethod
    def _load_session_runtime_dependencies() -> _SessionRuntimeDependencies:
        from modules.core.constants import AIModels, Emojis
        from modules.core.spinners import STAGE0_AVAILABLE, V50_MODULES_AVAILABLE
        from modules.domain.agents.chief_writer import ChiefWriter
        from modules.domain.agents.manuscript_validator import ManuscriptValidator
        from modules.validation.blocking_validator import BlockingValidator
        from modules.validation.consistency_validator import ConsistencyValidator
        from modules.validation.continuity_validator import ContinuityValidator

        return _SessionRuntimeDependencies(
            ai_models=AIModels,
            emojis=Emojis,
            stage0_available=STAGE0_AVAILABLE,
            v50_modules_available=V50_MODULES_AVAILABLE,
            chief_writer_cls=ChiefWriter,
            manuscript_validator_cls=ManuscriptValidator,
            blocking_validator_cls=BlockingValidator,
            consistency_validator_cls=ConsistencyValidator,
            continuity_validator_cls=ContinuityValidator,
        )

    def _prepare_stage4_session(self, *, limit_mode: bool = False, target_ep: int | None = None) -> dict | None:
        """[4-R1-f] Prepare Stage 4 session: agents, context, style guide.

        Returns session config dict for _run_interview_loop, or None if data missing.
        """
        runtime_deps = self._load_session_runtime_dependencies()

        # 1. 기초 데이터 점검
        if not self._validate_session_prerequisites(error_emoji=runtime_deps.emojis.ERROR):
            return None

        agent_bootstrap = self._initialize_session_agents(
            chief_writer_cls=runtime_deps.chief_writer_cls,
            manuscript_validator_cls=runtime_deps.manuscript_validator_cls,
            consistency_validator_cls=runtime_deps.consistency_validator_cls,
            blocking_validator_cls=runtime_deps.blocking_validator_cls,
            continuity_validator_cls=runtime_deps.continuity_validator_cls,
            writer_model=runtime_deps.ai_models.STAGE4_FIXED_WRITER_MODEL,
        )
        _story_context = self._build_session_story_context(s4_genre_type=agent_bootstrap.s4_genre_type)
        self._prepare_session_ui(writer_model=runtime_deps.ai_models.STAGE4_FIXED_WRITER_MODEL)

        # 3. 환경 설정
        session_environment = self._prepare_session_environment()

        target_decision = self._resolve_session_target_ep(
            target_ep=target_ep,
            limit_mode=limit_mode,
            current_written=session_environment.current_written,
            total_planned_ep=session_environment.total_planned_ep,
        )
        if target_decision.should_abort:
            return None
        target_ep = target_decision.target_ep

        style_payload = self._prepare_session_style_payload(stage0_available=runtime_deps.stage0_available)

        return self._build_session_config(
            agent_bootstrap=agent_bootstrap,
            story_context=_story_context,
            style_guide=style_payload.style_guide,
            reference_excerpt=style_payload.reference_excerpt,
            target_ep=target_ep,
            session_environment=session_environment,
            v50_modules_available=runtime_deps.v50_modules_available,
        )

    def stage_4_v2_chief_writer(
        self, limit_mode: bool = False, *, target_ep: int | None = None, skip_pause: bool = False
    ) -> None:
        """
        [V60.80] Stage 4 V2 - Chief Writer 주권주의 아키텍처

        핵심 철학: "Blueprint를 토대로 양질의 원고를 연속성 있게 생산한다"

        구조:
        - Phase 1: 프롬프트 조립 (필수만)
        - Phase 2: Chief Writer 앙상블 (3개 병렬 생성)
        - Phase 3: Python 사전 검증 (경고만, REJECT 권한 없음)
        - Phase 4: Director 면담 (5번 기회, 패치 모드 전 라운드 적용)
        - 인간 개입: 5번 실패 시 중단
        """
        try:
            ctx = self.ctx
            self._stage4_completion_blocked = False
            session = self._prepare_stage4_session(limit_mode=limit_mode, target_ep=target_ep)
            if session is None:
                return
            # 5. Episode production loop
            _should_return = self._run_interview_loop(session, skip_pause=skip_pause)
            if _should_return or self._stage4_completion_blocked:
                return
            _audit_event = getattr(ctx, "audit_event", None)
            if callable(_audit_event):
                _audit_event(
                    "stage4_complete",
                    "stage4 production completed",
                    {
                        "session_id": str(resolve_logging_session_id(getattr(ctx, "current_project", None)) or ""),
                        "target_ep": getattr(session, "target_ep", target_ep),
                    },
                )
            _write_summary = getattr(ctx, "write_audit_summary", None)
            if callable(_write_summary):
                _write_summary("stage4_complete")

        except KeyboardInterrupt:
            self.ctx.ui.log("\n⚠️ 사용자 중단 요청. 저장 후 종료합니다.")
            if callable(getattr(self.ctx, "flush_audit_buffer", None)):
                self.ctx.flush_audit_buffer()
            if callable(getattr(self.ctx, "safe_commit", None)):
                if not self.ctx.safe_commit():
                    self.ctx.ui.log("⚠️ [Stage4 Cleanup] interrupt cleanup commit failed")
        except Exception as e:
            self.ctx.ui.log(f"\n🚨 Stage 4 V2 오류: {e}")
            import traceback

            traceback.print_exc()
            if callable(getattr(self.ctx, "flush_audit_buffer", None)):
                self.ctx.flush_audit_buffer()
            if callable(getattr(self.ctx, "safe_commit", None)):
                if not self.ctx.safe_commit():
                    self.ctx.ui.log("⚠️ [Stage4 Cleanup] exception cleanup commit failed")
