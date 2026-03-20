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
from modules.core.constants import smart_truncate
from modules.core.jsonl_io import append_jsonl_record
from modules.core.llm_generate import generate_content_via_router
from modules.core.project_support import load_style_guide_anchor, resolve_project_bible_pov
from modules.core.soft_failure import resolve_project_log_dir
from modules.core.stage4_context_builder import Stage4ContextBuilder
from modules.core.stage4_interview_round import Stage4InterviewRound
from modules.core.stage4_post_processor import Stage4PostProcessor
from modules.core.stage4_types import _RoundContext
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
class _RoundOutcome:
    """[4-R2-d] Result of _handle_round_outcome."""

    final_manuscript: object  # str | None
    final_title: object  # str | None
    final_state_updates: dict
    should_return: bool


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
class _EpisodePromptBundle:
    genre_name: str
    ctx_prompts: dict
    prompt_supplements: _WriterPromptSupplements


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
                target_ep=int(target_ep),
                next_ep=int(next_ep),
            )

        _audit_event = getattr(self.ctx, "audit_event", None)
        if callable(_audit_event):
            _audit_event(
                "target_ep_reached",
                "stage4 target episode reached",
                {
                    "target_ep": int(target_ep),
                    "next_ep": int(next_ep),
                },
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
        if not callable(callback):
            return ""

        reason_parts: list[str] = []
        if director_feedback:
            reason_parts.append(str(director_feedback))
        if isinstance(previous_attempt, dict):
            for key in ("rejection_reason", "open_review", "verdict_reason"):
                value = str(previous_attempt.get(key, "") or "").strip()
                if value and value not in reason_parts:
                    reason_parts.append(value)
            action_items = previous_attempt.get("action_items", [])
            if isinstance(action_items, list) and action_items:
                reason_parts.append(" / ".join(str(item) for item in action_items[:3]))
        reject_reason = "\n".join(part for part in reason_parts if part).strip()
        if not reject_reason:
            return ""

        pre_checklist_result = None
        if isinstance(previous_attempt, dict):
            checklist = previous_attempt.get("consistency_checklist")
            if isinstance(checklist, dict) and checklist:
                pre_checklist_result = checklist

        try:
            return callback(
                writer_reject_reason=reject_reason,
                pre_checklist_result=pre_checklist_result,
            ) or ""
        except Exception as exc:
            logging.warning("[Stage4->3] reverse feedback helper 실패: %s", exc)
            return ""

    @staticmethod
    def _merge_blueprint_feedback(director_feedback: str, reverse_feedback: str) -> str:
        direct = str(director_feedback or "").strip()
        reverse = str(reverse_feedback or "").strip()
        if reverse and direct and reverse not in direct:
            return f"{reverse}\n\n[Stage4 원문 피드백]\n{direct}"
        return reverse or direct

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

            # 1. 데이터 수집
            _ws_summary = ""
            if self.ctx.world_state:
                try:
                    _ws_summary = self.ctx.world_state.get_summary(max_chars=8000)
                except Exception:
                    pass

            _fl_summary = ""
            if self.ctx.fact_ledger:
                try:
                    _fl_summary = self.ctx.fact_ledger.get_canonical_summary(max_chars=5000)
                except Exception:
                    pass

            _arc_tactical = ""
            if arc_data:
                try:
                    _arc_tactical = extract_episode_tactical(
                        arc_data.get("tactical_doc", ""),
                        ep_num,
                        episode_details=arc_data.get("episode_details"),
                    )[:3000]
                except Exception:
                    pass

            _prev_published_text = ""
            try:
                _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
                _prev_row = _db.get_manuscript(ep_num - 1) if _db and ep_num > 1 else None
                if isinstance(_prev_row, dict):
                    _prev_published_text = str(
                        _prev_row.get("content")
                        or _prev_row.get("corrected_manuscript")
                        or _prev_row.get("manuscript")
                        or ""
                    )
                elif _prev_row:
                    _prev_published_text = str(_prev_row)
            except Exception:
                _prev_published_text = ""

            _pin_result = apply_continuity_pins(
                blueprint,
                previous_published_text=_prev_published_text,
                arc_tactical_text=_arc_tactical,
            )
            _patched_blueprint = None
            _blueprint_for_validation = blueprint
            if _pin_result.get("changes"):
                _patched_blueprint = _pin_result.get("blueprint", blueprint)
                if isinstance(_patched_blueprint, dict):
                    _patched_blueprint["_continuity_pins"] = _pin_result["changes"]
                    _blueprint_for_validation = _patched_blueprint

            _bp_json = json.dumps(_blueprint_for_validation, ensure_ascii=False, indent=2)[:15000]

            # 2. 프롬프트 로드 + 포맷
            try:
                _template = PromptLoader().load("blueprint_generator", "BLUEPRINT_PREFLIGHT_VALIDATE_PROMPT")
            except Exception as e:
                _perf_logger.debug("[TF-49b] Preflight 프롬프트 로드 실패 (비치명): %s", e)
                return _pass_result

            def _esc(s):
                return s.replace("{", "{{").replace("}", "}}")

            _prompt = _template.format(
                world_state_summary=_esc(_ws_summary) if _ws_summary else "(상태 정보 없음)",
                fact_ledger_summary=_esc(_fl_summary) if _fl_summary else "(수치 기록 없음)",
                arc_tactical_excerpt=_esc(_arc_tactical) if _arc_tactical else "(전술서 없음)",
                ep_num=ep_num,
                blueprint_json=_esc(_bp_json),
            )

            # 3. Flash 모델 직접 호출
            from google.genai import types

            _response = generate_content_via_router(
                client=self.ctx.sys.api_client,
                model=AIModels.FLASH_ANALYSIS_MODEL,
                contents=_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    response_schema=BLUEPRINT_PREFLIGHT_SCHEMA,
                ),
            )
            _result = json.loads(_response.text)

            _issues = _result.get("issues", [])
            _summary = _result.get("summary", "")

            # [TF-49b] 웹소설 관용 기준: 2단계 severity 필터
            # 1단계: 가짜양성 패턴 → 무조건 low (WorldState 불완전성 등)
            # 2단계: 1단계 비해당 + CRITICAL 패턴 미매칭 → low
            _FALSE_POSITIVE_PATTERNS = (
                "출처 불분명",
                "출처가 불분명",  # WorldState에 이전 자금 미기재
                "획득 경로",
                "획득 경위",  # Stage 0 아이템 미추적
                "보유 근거",
                "기록되지 않",  # WorldState 누락
                "갑작스러운 등장",
                "갑자기 등장",  # 이전 화에서 확립된 것
                "고증",
                "시대",
                "연도",  # 웹소설 관용
                "해상도",
                "모니터",
                "컴퓨터",  # 기술 고증
            )
            _CRITICAL_PATTERNS = (
                "사망",
                "deceased",  # 사망 NPC 행동
                "시간 역행",
                "역행",  # 타임라인 역행
                "소진",
                "소모된",  # 소진 아이템 재등장
                "불가능",
                "도달 불가",  # 수학적 불가능
                "모순",  # 명시적 모순 언급
            )
            for _iss in _issues:
                if _iss.get("severity") != "high":
                    continue
                _combined = f"{_iss.get('category', '')} {_iss.get('description', '')}"
                # 1단계: 가짜양성이면 무조건 low
                if any(fp in _combined for fp in _FALSE_POSITIVE_PATTERNS):
                    _iss["severity"] = "low"
                # 2단계: CRITICAL 패턴 미매칭이면 low
                elif not any(cp in _combined for cp in _CRITICAL_PATTERNS):
                    _iss["severity"] = "low"

            # severity="high"인 이슈만 실패 판정
            _high_issues = [i for i in _issues if i.get("severity") == "high"]
            _truly_failed = not _result.get("passed", True) and len(_high_issues) > 0

            if not _truly_failed:
                _level = "PASS" if _result.get("passed", True) else "PASS (low/medium only)"
                _perf_logger.info("[TF-49b] Preflight %s — 제%d화 Blueprint 정합성 확인", _level, ep_num)
                if _issues and not _result.get("passed", True):
                    self.ctx.ui.log(f"   ℹ️ [TF-49b] Preflight: {len(_issues)}건 참고 사항 (경미, 패치 불필요)")
                return {
                    "passed": True,
                    "issues": _issues,
                    "summary": _summary,
                    "patched_blueprint": _patched_blueprint,
                }

            # 4. 실패 → advisory 텍스트 생성 (Blueprint 패치 대신 CW/Director에 전달)
            _high_count = len(_high_issues)
            _log_level = "⚠️" if _high_count > 0 else "ℹ️"
            self.ctx.ui.log(
                f"   {_log_level} [TF-49b] Preflight: {len(_issues)}건 발견 (high={_high_count}) → CW/Director advisory 전달"
            )
            for _iss in _issues[:5]:
                self.ctx.ui.log(
                    f"      [{_iss.get('severity', '?')}] {_iss.get('category', '?')}: "
                    f"{_iss.get('description', '')[:80]}"
                )

            # Advisory 텍스트 포맷
            _advisory_lines = [f"[TF-49b Preflight 발견 사항 — 제{ep_num}화]"]
            for _iss in _issues[:10]:
                _sev = _iss.get("severity", "?")
                _cat = _iss.get("category", "?")
                _desc = _iss.get("description", "")
                _advisory_lines.append(f"  - [{_sev}] {_cat}: {_desc}")
            _advisory_lines.append("위 사항에 주의하여 원고 작성/심사에 반영하세요.")
            _advisory_text = "\n".join(_advisory_lines)

            # 에스컬레이션 로그
            self._log_escalation_event(ep_num, "TF49b_PREFLIGHT", len(_issues), success=True)

            return {
                "passed": True,  # advisory 전달이므로 항상 pass (블루프린트 미수정)
                "issues": _issues,
                "summary": _summary,
                "patched_blueprint": _patched_blueprint,
                "advisory": _advisory_text,
            }

        except Exception as e:
            _perf_logger.debug("[TF-49b] Preflight 전체 실패 (fail-open): %s", e)
            return _pass_result

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

        arc_data = next(
            (
                arc
                for arc in self.ctx.current_project.arcs
                if isinstance(arc, dict) and arc.get("ep_start", 0) <= next_ep <= arc.get("ep_end", 0)
            ),
            None,
        )
        if not arc_data:
            self.ctx.ui.log(f"⚠️ 제{next_ep}화 Arc 데이터 없음.")
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

    def _run_interview_loop(self, session: _SessionConfig, *, skip_pause: bool = False) -> bool:
        """[4-R1-e-4] Run main episode production loop.

        Returns True if caller should return early.
        """
        # [4-R2-a] Unpack session config
        chief_writer = session.chief_writer
        manuscript_validator = session.manuscript_validator
        consistency_validator = session.consistency_validator
        blocking_validator = session.blocking_validator
        continuity_validator = session.continuity_validator
        s4_genre_type = session.s4_genre_type
        story_context = session.story_context
        style_guide = session.style_guide
        reference_excerpt = session.reference_excerpt
        target_ep = session.target_ep
        output_dir = session.output_dir
        v50_modules_available = session.v50_modules_available
        total_planned_ep = session.total_planned_ep

        loop_guard = 0
        # [P1-D2] total_planned_ep=0 방어 (블루프린트 없는 경우)
        if not target_ep and total_planned_ep <= 0:
            self.ctx.ui.log("⚠️ 블루프린트가 없습니다. Stage 2를 먼저 실행하세요.")
            return False
        # [Sweep45] max(1, ...) — latest_ep > total_planned_ep 시 음수 방지
        max_loops = max(
            1, min((target_ep or total_planned_ep) - self.ctx.current_project.get_latest_episode_number() + 5, 100)
        )

        # [V66.1] B-2: ReferenceAnchor 루프 밖 1회 생성 (내부 캐시로 DB 중복 조회 방지)
        from modules.core.reference_anchor import ReferenceAnchor

        _anchor_sys = ReferenceAnchor(self.ctx.current_project)

        # [LM-A-1] Bible → world_laws 자동 등록 (최초 1회)
        if self.ctx.world_state and not self.ctx.world_state.get_world_laws():
            self._register_bible_world_laws()

        # 5. 원고 생산 메인 루프
        while True:
            loop_guard += 1
            if loop_guard > max_loops:
                self.ctx.ui.log("🛑 [Safety] 루프 제한 도달. 중단합니다.")
                break

            next_ep = self.ctx.current_project.get_latest_episode_number()
            self.interview_round.time_warnings = []  # [V70] 에피소드마다 리셋 (누적 방지)
            self._set_agent_telemetry_context(ep_num=next_ep, extra_agents=[chief_writer])
            if target_ep and next_ep > target_ep:
                self._log_target_ep_reached(target_ep=int(target_ep), next_ep=int(next_ep))
                self.ctx.ui.log(f"🏁 목표 회차({target_ep}화) 도달. 종료합니다.")
                break

            _episode_inputs = self._prepare_current_episode_inputs(next_ep=next_ep)
            if _episode_inputs is None:
                break
            blueprint = _episode_inputs.blueprint
            arc_data = _episode_inputs.arc_data
            _preflight_advisory = _episode_inputs.preflight_advisory

            # [4-R1-a] 에피소드 컨텍스트 수집 (Extract Method)
            _ep_ctx = self.context_builder.prepare_episode_context(next_ep, arc_data, chief_writer)
            arc_pos = _ep_ctx["arc_pos"]
            total_ep_in_arc = _ep_ctx["total_ep_in_arc"]
            arc_tactical = _ep_ctx["arc_tactical"]
            prev_text = _ep_ctx["prev_text"]
            prev_ending = _ep_ctx["prev_ending"]
            _prev_manuscripts_text = _ep_ctx["prev_manuscripts_text"]
            _episode_digest = _ep_ctx["episode_digest"]
            hud_report = _ep_ctx["hud_report"]
            # reserved for future use: current_inventory, current_martial_arts, dead_npcs, item_acquisition_timeline
            _chain_link_section = _ep_ctx["chain_link_section"]
            _world_state_summary = _ep_ctx["world_state_summary"]

            _prompt_bundle = self._build_episode_prompt_bundle(
                next_ep=next_ep,
                arc_data=arc_data,
                blueprint=blueprint,
                arc_tactical=arc_tactical,
                prev_text=prev_text,
                prev_ending=prev_ending,
                hud_report=hud_report,
                anchor_sys=_anchor_sys,
                s4_genre_type=s4_genre_type,
                v50_modules_available=v50_modules_available,
            )
            genre_name = _prompt_bundle.genre_name
            _ctx_prompts = _prompt_bundle.ctx_prompts
            mandatory_context = _ctx_prompts["mandatory_context"]
            # reserved for future use: reference_anchor_prompt, justification_prompt, reflexion_prompt
            _prompt_supplements = _prompt_bundle.prompt_supplements
            purism_prompt = _prompt_supplements.purism_prompt
            npc_equipment_summary = _prompt_supplements.npc_equipment_summary
            _effective_anti_trope = _prompt_supplements.effective_anti_trope
            intro_dna = _prompt_supplements.intro_dna

            self.ctx.ui.log(f"\n{'=' * 60}")
            self.ctx.ui.log(
                f"📝 제{next_ep}화 집필 시작 (Arc {arc_data.get('arc_no', '?')}, 위치 {arc_pos}/{total_ep_in_arc})"
            )
            self.ctx.ui.log(f"{'=' * 60}")

            # [V67] mandatory_context 우선순위 기반 스마트 트렁케이션 (50,000자 상한)
            _mc_max = _threshold("context.mandatory_context_max", 80000)
            if len(mandatory_context) > _mc_max:
                _original_len = len(mandatory_context)
                _ctx_budget_meta = getattr(self.ctx, "_stage4_context_budget_meta", {}) or {}
                if isinstance(_ctx_budget_meta, dict) and _ctx_budget_meta:
                    _budget_ledger = _ctx_budget_meta.get("budget_ledger") or {}
                    _perf_logger.info(
                        "[V66.1] mandatory_context pretrim meta sc=%s mc=%s total=%s limit=%s headroom=%s effective=%s dropped=%s overflow=%s",
                        _ctx_budget_meta.get("sc_chars"),
                        _ctx_budget_meta.get("mc_chars"),
                        _ctx_budget_meta.get("total_chars"),
                        _ctx_budget_meta.get("limit_chars"),
                        _ctx_budget_meta.get("headroom_chars"),
                        _budget_ledger.get("effective_cap"),
                        _budget_ledger.get("dropped_chars"),
                        _budget_ledger.get("overflow_chars"),
                    )
                _budget_result = _fit_mandatory_context_budget(
                    mandatory_context,
                    max_chars=_mc_max,
                )
                mandatory_context = _budget_result.mandatory_context
                if _budget_result.removed_count > 0:
                    _perf_logger.info(
                        f"[V66.1] mandatory_context {_budget_result.removed_count}개 섹션 제거 ({_budget_result.removed_chars}자)"
                    )
                    self.ctx.ui.log(
                        f"   ⚠️ [V66.1] mandatory_context {_original_len}자 → {len(mandatory_context)}자 (섹션 {_budget_result.removed_count}개 제거)"
                    )
                elif _budget_result.used_fallback:
                    self.ctx.ui.log(
                        f"   ⚠️ [V66.1] mandatory_context {_original_len}자 → {_mc_max:,}자로 truncate (폴백)"
                    )

            # [V61.6] 전체 면담 루프를 스피너로 감싸기
            _round_ctx = self.context_builder.build_round_context(
                ep_ctx=_ep_ctx,
                ctx_prompts=_ctx_prompts,
                chief_writer=chief_writer,
                manuscript_validator=manuscript_validator,
                consistency_validator=consistency_validator,
                blocking_validator=blocking_validator,
                continuity_validator=continuity_validator,
                next_ep=next_ep,
                blueprint=blueprint,
                arc_data=arc_data,
                purism_prompt=purism_prompt,
                genre_name=genre_name,
                npc_equipment_summary=npc_equipment_summary,
                effective_anti_trope=_effective_anti_trope,
                intro_dna=intro_dna,
                story_context=story_context,
                style_guide=style_guide,
                reference_excerpt=reference_excerpt,
                mandatory_context=mandatory_context,
                preflight_advisory=_preflight_advisory,
            )
            # ===== Phase 4: Director 면담 (5회) =====
            _outcome = self._handle_round_outcome(round_ctx=_round_ctx)
            if _outcome.should_return:
                # [Sweep45] 5회 실패 시에도 벡터 메모리 동기화 보장
                self.post_processor.run_post_episode_tasks(skip_pause=skip_pause)
                return True
            final_manuscript = _outcome.final_manuscript
            final_title = _outcome.final_title
            final_state_updates = _outcome.final_state_updates

            # ===== Phase 5: 데이터 정산 =====
            if final_manuscript:
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
                    # [Sweep46] DB 저장 실패 시 무한 재시도 방지 — break
                    self.ctx.ui.log(f"   ⛔ [EP {next_ep}] DB 저장 실패. 집필 중단.")
                    break

                # [TF7-P2-07] PassRateMonitor 경보 소비
                _prm = getattr(self.ctx, "pass_rate_monitor", None)
                if _prm is not None:
                    try:
                        _alerts = _prm.check_alerts()
                        for _alert in _alerts:
                            logging.warning(f"[PassRate 경보] {_alert}")
                    except Exception as _e:
                        logging.debug("[Stage4] PassRateMonitor.check_alerts 실패 (무시): %s", _e)

        # [V62.3] Stage 4 루프 종료
        self.post_processor.run_post_episode_tasks(skip_pause=skip_pause)

        return False

    def _handle_round_outcome(self, *, round_ctx: _RoundContext) -> _RoundOutcome:
        """[4-R1-e-3] Run N-round interview loop (N = retry.director_max_attempts).

        Returns _RoundOutcome: final_manuscript, final_title, final_state_updates, should_return
        """
        from modules.core.spinners import StageSpinner

        next_ep = round_ctx.next_ep

        final_manuscript = None
        final_title = None
        final_state_updates = {}
        director_feedback = ""
        previous_attempt = {}
        _logic_error_streak = 0  # [V75-B] 연속 LOGIC_ERROR 카운터
        _inplace_attempted = False  # [V75-D] inplace 패치 1회 제한
        _blueprint_regenerated = False  # [V75-B] 재생성 1회 제한
        _prev_reject_bucket = ""  # [TF-29] reject_bucket 연속 패턴 감지
        _bucket_streak = 0
        _prev_dominant_contradiction = ""  # [A-4] contradiction type 수렴 추적
        _contradiction_type_streak = 0
        _score_history: list[int] = []
        _plateau_advisory_emitted = False
        _pathology_counts: dict[str, int] = {}
        _pathology_repeat_emitted: set[str] = set()

        with StageSpinner(4, f"제{next_ep}화 · 앙상블 준비") as stage4_spinner:
            try:
                _max_rounds = int(_threshold("retry.director_max_attempts", 5))
            except (TypeError, ValueError):
                _max_rounds = 5
            _max_rounds = max(1, _max_rounds)

            for interview_round in range(_max_rounds):
                self.ctx.ui.log(
                    f"   🔄 [Round {interview_round + 1}/{_max_rounds}] 원고 생성 시도...",
                    stage="stage4",
                    component="round_execution",
                    ep_num=next_ep,
                    arc_num=round_ctx.arc_data.get("arc_no", 0),
                    round_num=interview_round,
                    event_kind="progress",
                )
                _round_result = self.interview_round.run(
                    round_num=interview_round,
                    stage4_spinner=stage4_spinner,
                    director_feedback=director_feedback,
                    previous_attempt=previous_attempt,
                    round_ctx=round_ctx,
                )
                if _round_result.verdict in ("PASS", "PASS_WITH_FIX"):  # [TF-32]
                    self.ctx.ui.log(
                        f"   ✅ [Round {interview_round + 1}] {_round_result.verdict}",
                        stage="stage4",
                        component="round_execution",
                        ep_num=next_ep,
                        arc_num=round_ctx.arc_data.get("arc_no", 0),
                        round_num=interview_round,
                        event_kind="result",
                        meta={"verdict": _round_result.verdict},
                    )
                    final_manuscript = _round_result.final_manuscript
                    final_title = _round_result.final_title
                    final_state_updates = _round_result.final_state_updates

                    _cove = self.ctx.get_module("chain_of_verification")
                    if _cove and final_manuscript:
                        try:
                            _cove_context = {}
                            _prev_ms = round_ctx.prev_manuscripts_text or ""
                            _bp = round_ctx.blueprint
                            if _prev_ms:
                                _cove_context["prev_manuscript"] = _prev_ms[-1500:]
                            if _bp:
                                _cove_context["blueprint"] = _bp

                            # [S4-I5] CoVe 최적화: quick_verify(Python) → verify(LLM) 단일 경로
                            # quick_verify 통과 시 LLM 호출 스킵 (기존). 실패 시 경고를 LLM 컨텍스트에 주입.
                            _quick_ok, _quick_msg = _cove.quick_verify(final_manuscript, _cove_context)
                            if not _quick_ok:
                                self.ctx.ui.log(f"   ⚠️ [CoVe] 사후검증 경고: {_quick_msg[:60]}...")
                                # [S4-I5] quick_verify 경고를 LLM verify 컨텍스트에 주입 → 집중 검증
                                _cove_context["quick_verify_warnings"] = _quick_msg
                                try:
                                    _cove_result = _cove.verify(
                                        final_manuscript, _cove_context, content_type="manuscript"
                                    )
                                    if _cove_result.should_regenerate:
                                        self.ctx.ui.log("   🚨 [CoVe] 치명적 모순 감지 → REJECT 전환")
                                        _cove_feedback = _cove_result.correction_hints or _cove_result.summary
                                        director_feedback = f"[CoVe 사후검증 실패]\n{_cove_feedback}"
                                        previous_attempt = {
                                            "score": 90,
                                            "best_manuscript": final_manuscript,
                                            "rejection_reason": director_feedback,
                                            "state_updates": final_state_updates,  # [TF-S4-01] CoVe REJECT 시 소실 방지
                                            "retry_pathology_source": "cove_fail_closed",
                                            "cove_fail_closed": True,
                                            "cove_runtime_failure": False,
                                            "provisional_pass_downgrade": True,
                                        }
                                        final_manuscript = None
                                        final_title = None  # [S4-P1-1] CoVe REJECT 시 title도 리셋
                                        logging.warning(  # [F2] CoVe REJECT 라운드 소모 가시화
                                            "[Stage4] ep=%d round=%d/%d CoVe LLM REJECT → 라운드 소모",
                                            next_ep,
                                            interview_round + 1,
                                            _max_rounds,
                                        )
                                        self._emit_retry_pathology_signal(
                                            ep_num=next_ep,
                                            round_num=interview_round,
                                            previous_attempt=previous_attempt,
                                            pathology_counts=_pathology_counts,
                                            pathology_repeat_emitted=_pathology_repeat_emitted,
                                        )
                                        continue
                                    # [S4-I5] LLM verify에서 MINOR/MAJOR 경고만 → 통과 (REJECT 안 함)
                                    if _cove_result.issues:
                                        _cove_warnings = "; ".join(i.description[:40] for i in _cove_result.issues[:3])
                                        self.ctx.ui.log(f"   ℹ️ [CoVe] LLM 검증 경고 (비차단): {_cove_warnings}")
                                except Exception as e:
                                    logging.warning(f"[FailClosed:CoVe:LLM] {e!s:.100}")
                                    self.ctx.ui.log("   ⚠️ [CoVe] LLM 검증 런타임 실패 → Director PASS 유지")
                                    logging.warning(
                                        "[Stage4] ep=%d round=%d/%d CoVe LLM 런타임 실패 → PASS 유지",
                                        next_ep,
                                        interview_round + 1,
                                        _max_rounds,
                                    )
                                    self._log_cove_runtime_advisory(
                                        ep_num=next_ep,
                                        round_num=interview_round,
                                        source="llm_verify",
                                        error=e,
                                        quick_warning=_quick_msg,
                                    )
                        except Exception as e:
                            logging.warning(f"[FailClosed:CoVe:Quick] {e!s:.100}")
                            self.ctx.ui.log("   ⚠️ [CoVe] Quick 검증 런타임 실패 → Director PASS 유지")
                            logging.warning(
                                "[Stage4] ep=%d round=%d/%d CoVe Quick 런타임 실패 → PASS 유지",
                                next_ep,
                                interview_round + 1,
                                _max_rounds,
                            )
                            self._log_cove_runtime_advisory(
                                ep_num=next_ep,
                                round_num=interview_round,
                                source="quick_verify",
                                error=e,
                            )

                    break
                director_feedback = _round_result.director_feedback
                previous_attempt = _round_result.previous_attempt
                self.ctx.ui.log(
                    f"   ❌ [Round {interview_round + 1}/{_max_rounds}] REJECT → 다음 라운드",
                    stage="stage4",
                    component="round_execution",
                    ep_num=next_ep,
                    arc_num=round_ctx.arc_data.get("arc_no", 0),
                    round_num=interview_round,
                    event_kind="result",
                    level="warning",
                    meta={"verdict": "REJECT"},
                )

                _current_score = (previous_attempt or {}).get("score", 0)
                try:
                    _current_score = int(_current_score)
                except (TypeError, ValueError):
                    _current_score = 0
                if _current_score > 0:
                    _score_history.append(_current_score)
                    if not _plateau_advisory_emitted:
                        _plateau_advisory = ""
                        if len(_score_history) >= 3 and (
                            _score_history[-3] > _score_history[-2] > _score_history[-1]
                        ):
                            _plateau_advisory = (
                                f"[⚠️ 점수 하락 추세] 최근 점수가 "
                                f"{_score_history[-3]}→{_score_history[-2]}→{_score_history[-1]}로 3연속 하락했습니다. "
                                "현재 수정 루프의 효율이 낮습니다. fix_scope를 rewrite 이상으로 넓히거나 "
                                "Blueprint/Arc 구조를 재검토하세요."
                            )
                        elif len(_score_history) >= 2 and _score_history[-2] == _score_history[-1]:
                            _plateau_advisory = (
                                f"[⚠️ 점수 plateau] 최근 두 라운드 점수가 {_score_history[-1]}점으로 동일합니다. "
                                "동일 수정 루프를 반복 중일 수 있습니다. fix_scope 확대 또는 Blueprint 재검토를 우선 검토하세요."
                            )

                        if _plateau_advisory:
                            _plateau_advisory_emitted = True
                            director_feedback = _plateau_advisory + "\n" + director_feedback
                            if isinstance(previous_attempt, dict):
                                previous_attempt["score_history"] = list(_score_history[-3:])
                                previous_attempt["plateau_detected"] = True
                                _existing_reasoning = str(previous_attempt.get("fix_scope_reasoning", "") or "").strip()
                                previous_attempt["fix_scope_reasoning"] = (
                                    f"{_existing_reasoning}\n{_plateau_advisory}".strip()
                                    if _existing_reasoning
                                    else _plateau_advisory
                                )
                            self.ctx.ui.log(f"   ⚠️ [QR-7] {str(_plateau_advisory)[:80]}")

                # [V75-B] LOGIC_ERROR 연속 카운터
                if _round_result.error_category == "LOGIC_ERROR":
                    _logic_error_streak += 1
                else:
                    _logic_error_streak = 0

                # [TF-29] reject_bucket 연속 패턴 감지
                _current_bucket = (_round_result.previous_attempt or {}).get("reject_bucket", "")
                if _current_bucket and _current_bucket == _prev_reject_bucket:
                    _bucket_streak += 1
                else:
                    _bucket_streak = 1 if _current_bucket else 0
                _prev_reject_bucket = _current_bucket

                # [TF-29] 동일 reject_bucket 3연속 → 블루프린트/아크 문제 가능성 advisory
                _tf29_advisory = ""
                if _bucket_streak >= 3 and not _blueprint_regenerated:
                    _bucket_label = {
                        "quality_issue": "품질",
                        "constraint_violation": "제약 위반",
                        "structure_error": "구조",
                    }.get(_prev_reject_bucket, _prev_reject_bucket)
                    self.ctx.ui.log(
                        f"   ⚠️ [TF-29] '{_bucket_label}' 유형 REJECT {_bucket_streak}연속"
                        " — 블루프린트/아크 수준 문제 가능성"
                    )
                    _tf29_advisory = (
                        f"[⚠️ 반복 실패 패턴 감지] '{_bucket_label}' 유형 REJECT가 {_bucket_streak}회 연속입니다. "
                        f"원고 수준 수정으로 해결되지 않을 가능성이 높습니다. "
                        f"블루프린트의 해당 영역을 근본적으로 재검토하세요."
                    )
                    director_feedback = _tf29_advisory + "\n" + director_feedback

                # [A-4] Contradiction type 수렴 추적
                _curr_ct = (_round_result.previous_attempt or {}).get("contradiction_types", [])
                _curr_dominant_ct = ""
                if _curr_ct:
                    from collections import Counter

                    _ct_counter = Counter(_curr_ct)
                    _curr_dominant_ct = _ct_counter.most_common(1)[0][0] if _ct_counter else ""
                if _curr_dominant_ct and _curr_dominant_ct == _prev_dominant_contradiction:
                    _contradiction_type_streak += 1
                else:
                    _contradiction_type_streak = 1 if _curr_dominant_ct else 0
                _prev_dominant_contradiction = _curr_dominant_ct

                # [A-4] LOGIC_ERROR + 동일 모순 유형 2연속 → Arc 구조 문제 advisory
                if _contradiction_type_streak >= 2 and _logic_error_streak >= 2 and not _blueprint_regenerated:
                    _ct_label = {
                        "타임라인": "시간 순서/연대기",
                        "수치": "수치/금액 정합성",
                        "사망": "사망/생존 상태",
                        "고유명사": "고유명사 일관성",
                        "아이템": "아이템/장비",
                        "상태": "캐릭터 상태",
                    }.get(_curr_dominant_ct, _curr_dominant_ct)
                    _a4_advisory = (
                        f"[⚠️ A-4 구조 진단] '{_ct_label}' 모순이 {_contradiction_type_streak}라운드 연속. "
                        f"이는 Writer 문제가 아닌 Blueprint/Arc 설계의 구조적 결함 가능성이 높습니다. "
                        f"해당 영역의 Arc를 재검토하세요."
                    )
                    director_feedback = _a4_advisory + "\n" + director_feedback
                    self.ctx.ui.log(f"   ⚠️ [A-4] '{_ct_label}' 모순 {_contradiction_type_streak}연속 — Arc 구조 진단")

                # [V75-D] Step 1: N연속 → inplace 패치 (저비용 LLM 1회)
                # [S3-META] quality_risk Blueprint → 1연속에서 조기 트리거
                self._emit_retry_pathology_signal(
                    ep_num=next_ep,
                    round_num=interview_round,
                    previous_attempt=previous_attempt,
                    pathology_counts=_pathology_counts,
                    pathology_repeat_emitted=_pathology_repeat_emitted,
                )
                _s3_meta = round_ctx.blueprint.get("_stage3_meta", {}) if isinstance(round_ctx.blueprint, dict) else {}
                _quality_risk = bool(_s3_meta.get("quality_risk", False))
                _v75d_threshold = 1 if _quality_risk else 2
                logging.info("[V75-D] quality_risk=%s → threshold=%d, streak=%d",
                    _quality_risk,
                    _v75d_threshold,
                    _logic_error_streak,
                )
                if _logic_error_streak >= _v75d_threshold and not _inplace_attempted:
                    _inplace_attempted = True
                    _v75d_success = False
                    _bp_cr = None
                    _bp_artifact_meta = {
                        "candidate_key": "",
                        "content_hash": "",
                        "artifact_path": "",
                    }
                    try:
                        self.ctx.ui.log(
                            f"   🔧 [V75-D] LOGIC_ERROR {_logic_error_streak}연속 → 블루프린트 inplace 패치 시도..."
                        )
                        _bp_agent = self.ctx.agents.get("three_phase_bp")
                        if _bp_agent:
                            _reverse_feedback_43 = self._build_stage4_to_3_reverse_feedback(
                                director_feedback=director_feedback,
                                previous_attempt=previous_attempt,
                            )
                            _blueprint_feedback = self._merge_blueprint_feedback(
                                director_feedback,
                                _reverse_feedback_43,
                            )
                            _patched_bp = _bp_agent._inplace_patch_blueprint(
                                original_blueprint=round_ctx.blueprint,
                                director_feedback=_blueprint_feedback,
                                ep_num=next_ep,
                                arc_data=round_ctx.arc_data,
                            )
                            if _patched_bp:
                                # [TF-IPG GAP-4] V75-D blueprint 패치 diff 로깅 + 변경비율 체크
                                try:
                                    import json as _json_mod

                                    from modules.core.constants import calc_patch_change_ratio, log_patch_diff
                                    _bp_orig_j = _json_mod.dumps(round_ctx.blueprint, ensure_ascii=False, indent=2)
                                    _bp_patch_j = _json_mod.dumps(_patched_bp, ensure_ascii=False, indent=2)
                                    log_patch_diff("S4-V75D-Blueprint", _bp_orig_j, _bp_patch_j)
                                    _bp_cr = calc_patch_change_ratio(
                                        _json_mod.dumps(round_ctx.blueprint, ensure_ascii=False),
                                        _json_mod.dumps(_patched_bp, ensure_ascii=False),
                                    )
                                    if _bp_cr > 0.30:
                                        logging.warning("[TF-IPG] V75-D Blueprint 변경 비율 %.1f%% > 30%%", _bp_cr * 100)
                                except Exception as _diff_e:
                                    logging.debug("[TF-IPG] V75-D diff 계산 실패: %s", _diff_e)
                                _bp_artifact_meta = snapshot_logged_artifact(
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
                                    payload=_patched_bp,
                                )
                                _audit_event = getattr(self.ctx, "audit_event", None)
                                if callable(_audit_event):
                                    _audit_payload = {
                                        "ep_num": int(next_ep),
                                        "round_num": int(interview_round + 1),
                                        "candidate_key": str(_bp_artifact_meta.get("candidate_key", "") or "").strip(),
                                        "content_hash": str(_bp_artifact_meta.get("content_hash", "") or "").strip(),
                                        "artifact_path": str(_bp_artifact_meta.get("artifact_path", "") or "").strip(),
                                    }
                                    if isinstance(_bp_cr, (int, float)):
                                        _audit_payload["change_ratio"] = float(_bp_cr)
                                    _audit_event(
                                        "stage4_v75d_blueprint_patch_snapshot",
                                        "stage4 V75-D blueprint patch snapshot persisted",
                                        _audit_payload,
                                    )
                                _v75d_success = True
                                round_ctx = dataclasses.replace(round_ctx, blueprint=_patched_bp)
                                _logic_error_streak = 0
                                director_feedback = (
                                    "[V75-D 블루프린트 inplace 패치 완료]\n"
                                    "지적된 논리적 결함만 수정되었습니다. "
                                    "수정된 블루프린트 기반으로 원고를 작성하세요."
                                )
                                if _tf29_advisory:  # [TF-29] advisory 보존
                                    director_feedback = _tf29_advisory + "\n" + director_feedback
                                previous_attempt = {}
                                self.ctx.ui.log("   ✅ [V75-D] inplace 패치 성공")
                            else:
                                self.ctx.ui.log("   ⚠️ [V75-D] inplace 패치 실패 — 기존 블루프린트 유지")
                    except Exception as _patch_err:
                        logging.warning("[FailClosed:V75-D] inplace 패치 실패: %s",
                            _patch_err,
                        )
                    # [V76] 에스컬레이션 이벤트 로그
                    self._log_escalation_event(
                        next_ep,
                        "V75-D_INPLACE",
                        _logic_error_streak,
                        success=_v75d_success,
                        round_num=interview_round,
                        fix_scope=(previous_attempt or {}).get("fix_scope", ""),
                        reason=director_feedback,
                        contradiction_type=_curr_dominant_ct,
                        candidate_key=str(_bp_artifact_meta.get("candidate_key", "") or "").strip(),
                        content_hash=str(_bp_artifact_meta.get("content_hash", "") or "").strip(),
                        artifact_path=str(_bp_artifact_meta.get("artifact_path", "") or "").strip(),
                    )

                # [V75-B] Step 2: inplace 시도 후에도 계속 실패 → 전면 재생성
                elif _logic_error_streak >= 2 and _inplace_attempted and not _blueprint_regenerated:
                    _v75b_success = False
                    try:
                        self.ctx.ui.log(
                            f"   🔄 [V75-B] LOGIC_ERROR {_logic_error_streak}연속 → 블루프린트 재생성 시도..."
                        )
                        _reverse_feedback_43 = self._build_stage4_to_3_reverse_feedback(
                            director_feedback=director_feedback,
                            previous_attempt=previous_attempt,
                        )
                        _new_bp = self._regenerate_blueprint(
                            next_ep,
                            round_ctx.arc_data,
                            round_ctx,
                            external_feedback=self._merge_blueprint_feedback(director_feedback, _reverse_feedback_43),
                        )
                        if _new_bp:
                            _v75b_success = True
                            round_ctx = dataclasses.replace(round_ctx, blueprint=_new_bp)
                            _blueprint_regenerated = True
                            _logic_error_streak = 0
                            director_feedback = (
                                "[V75-B 블루프린트 재생성 완료]\n"
                                "이전 블루프린트의 논리적 결함으로 재생성되었습니다. "
                                "새 블루프린트 기반으로 원고를 작성하세요."
                            )
                            if _tf29_advisory:  # [TF-29] advisory 보존
                                director_feedback = _tf29_advisory + "\n" + director_feedback
                            previous_attempt = {}
                            self.ctx.ui.log("   ✅ [V75-B] 블루프린트 재생성 성공")
                        else:
                            _blueprint_regenerated = True
                            self.ctx.ui.log("   ⚠️ [V75-B] 블루프린트 재생성 실패 — 기존 블루프린트 유지")
                    except Exception as _regen_err:
                        _blueprint_regenerated = True
                        logging.warning("[SilentPass:V75-B] 블루프린트 재생성 실패: %s",
                            _regen_err,
                        )
                    # [V76] 에스컬레이션 이벤트 로그
                    self._log_escalation_event(
                        next_ep,
                        "V75-B_FULL_REGEN",
                        _logic_error_streak,
                        success=_v75b_success,
                        round_num=interview_round,
                        fix_scope=(previous_attempt or {}).get("fix_scope", ""),
                        reason=director_feedback,
                        contradiction_type=_curr_dominant_ct,
                    )

        # ===== 설정된 라운드 수 모두 실패 =====
        # [V75-B] B-Full: 블루프린트 재생성까지 했는데도 실패 → Arc 재생성 제안
        if not final_manuscript and _blueprint_regenerated:
            self.ctx.ui.log("   🚨 [V75-B] 블루프린트 재생성 후에도 실패. Arc(전술서) 자체에 문제가 있을 수 있습니다.")
            self.ctx.ui.log("   💡 Stage 2에서 Arc를 재생성하면 해결될 수 있습니다.")
        if not final_manuscript:
            _last_best = previous_attempt.get("best_manuscript", "") if previous_attempt else ""
            _last_score = previous_attempt.get("score", 0) if previous_attempt else 0
            if _last_best:
                self.ctx.ui.log(
                    f"\n⚠️ [EP {next_ep}] {_max_rounds}회 소진. 마지막 최선 결과물(score={_last_score}) 존재."
                )
                _choice = 2
                if callable(getattr(self.ctx, "get_int_input", None)):
                    _choice = self.ctx.get_int_input(
                        "  1=최선 결과물로 진행  2=건너뛰기: ", default=2, min_val=1, max_val=2
                    )
                if _choice == 1:
                    final_manuscript = _last_best
                    final_title = final_title or f"제{next_ep}화"
                    final_state_updates = previous_attempt.get("state_updates", {})  # [TF-R3-S4-03] 폴백 시 상태 복구
                else:
                    return _RoundOutcome(
                        final_manuscript=None,
                        final_title=None,
                        final_state_updates={},
                        should_return=True,
                    )
            else:
                self.ctx.ui.log(f"\n⛔ [EP {next_ep}] {_max_rounds}회 면담 모두 실패. 인간 검토 필요.")
                return _RoundOutcome(
                    final_manuscript=None,
                    final_title=None,
                    final_state_updates={},
                    should_return=True,
                )

        return _RoundOutcome(
            final_manuscript=final_manuscript,
            final_title=final_title,
            final_state_updates=final_state_updates,
            should_return=False,
        )

    def _evaluate_retry_fix_pack_contract(self, previous_attempt: dict | None) -> dict[str, object]:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        try:
            return self.interview_round._evaluate_fix_pack_contract(previous_attempt.get("fix_pack"))
        except Exception:
            return {"ready": False, "reason": "contract_eval_failed", "fix_pack": {}}

    @staticmethod
    def _pathology_contradiction_type(previous_attempt: dict | None) -> str:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        contradiction_types = previous_attempt.get("contradiction_types") or []
        if not isinstance(contradiction_types, list) or not contradiction_types:
            return ""
        counts: dict[str, int] = {}
        for item in contradiction_types:
            key = str(item or "").strip()
            if not key:
                continue
            counts[key] = counts.get(key, 0) + 1
        if not counts:
            return ""
        return max(counts.items(), key=lambda pair: pair[1])[0]

    def _build_retry_pathology_payload(
        self,
        *,
        ep_num: int,
        round_num: int,
        previous_attempt: dict | None,
    ) -> dict[str, object]:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        fix_pack_contract = self._evaluate_retry_fix_pack_contract(previous_attempt)
        reject_bucket = str(previous_attempt.get("reject_bucket", "") or "").strip()
        contradiction_type = self._pathology_contradiction_type(previous_attempt)
        gate_basis = str(previous_attempt.get("gate_basis", "") or "").strip()
        fix_scope = str(previous_attempt.get("fix_scope", "") or "").strip()
        repair_scope = str(previous_attempt.get("repair_scope", "") or "").strip()
        error_category = str(previous_attempt.get("error_category", "") or "").strip()
        pathology_source = str(previous_attempt.get("retry_pathology_source", "") or "").strip()
        fix_scope_reasoning = str(previous_attempt.get("fix_scope_reasoning", "") or "").strip()
        open_review = str(previous_attempt.get("open_review", "") or "").strip()
        firewall_triggered = bool(previous_attempt.get("firewall_triggered", False))
        cove_fail_closed = bool(previous_attempt.get("cove_fail_closed", False))
        cove_runtime_failure = bool(previous_attempt.get("cove_runtime_failure", False))
        provisional_pass_downgrade = bool(previous_attempt.get("provisional_pass_downgrade", False))

        tags: list[str] = []
        if pathology_source:
            tags.append(pathology_source)
        if reject_bucket:
            tags.append(reject_bucket)
        if contradiction_type:
            tags.append(f"contradiction:{contradiction_type}")
        if firewall_triggered:
            tags.append("continuity_firewall")
        if provisional_pass_downgrade:
            tags.append("provisional_pass_downgrade")
        if cove_fail_closed:
            tags.append("cove_fail_closed")
        if cove_runtime_failure:
            tags.append("cove_runtime_failure")
        tags.append(
            "fix_pack_ready" if bool(fix_pack_contract.get("ready")) else f"fix_pack:{str(fix_pack_contract.get('reason', '') or 'not_ready')}"
        )

        fingerprint = "|".join(tag for tag in tags if tag) or "unclassified_retry_pathology"
        return {
            "ep_num": int(ep_num),
            "round_num": int(round_num + 1),
            "pathology_fingerprint": fingerprint,
            "pathology_source": pathology_source,
            "reject_bucket": reject_bucket,
            "gate_basis": gate_basis,
            "fix_scope": fix_scope,
            "repair_scope": repair_scope,
            "error_category": error_category,
            "contradiction_type": contradiction_type,
            "fix_pack_ready": bool(fix_pack_contract.get("ready")),
            "fix_pack_reason": str(fix_pack_contract.get("reason", "") or "").strip(),
            "provisional_pass_downgrade": provisional_pass_downgrade,
            "firewall_triggered": firewall_triggered,
            "cove_fail_closed": cove_fail_closed,
            "cove_runtime_failure": cove_runtime_failure,
            "plateau_detected": bool(previous_attempt.get("plateau_detected", False)),
            "score": int(previous_attempt.get("score", 0) or 0),
            "fix_scope_reasoning": fix_scope_reasoning[:240],
            "open_review": open_review[:240],
        }

    def _emit_retry_pathology_signal(
        self,
        *,
        ep_num: int,
        round_num: int,
        previous_attempt: dict | None,
        pathology_counts: dict[str, int],
        pathology_repeat_emitted: set[str],
    ) -> None:
        payload = self._build_retry_pathology_payload(
            ep_num=ep_num,
            round_num=round_num,
            previous_attempt=previous_attempt,
        )
        entry = {"event": "STAGE4_RETRY_PATHOLOGY", **payload}
        current_project = getattr(self.ctx, "current_project", None)
        logs_dir = resolve_project_log_dir(current_project)
        if logs_dir is None:
            project_name = getattr(current_project, "name", None)
            if not isinstance(project_name, str) or not project_name.strip() or "MagicMock" in project_name:
                project_name = "_unknown_project"
            logs_dir = Path("projects") / project_name / "logs"
        log_file = Path(logs_dir) / "episode_production.jsonl"
        try:
            Path(logs_dir).mkdir(parents=True, exist_ok=True)
            append_jsonl_record(log_file, entry)
        except Exception as exc:
            logging.warning("[Stage4] retry pathology sink write skipped: %s", exc)

        _audit_event = getattr(self.ctx, "audit_event", None)
        if callable(_audit_event):
            _audit_event(
                "stage4_retry_pathology_signal",
                "stage4 retry pathology observed",
                dict(payload),
            )

        fingerprint = str(payload.get("pathology_fingerprint", "") or "").strip()
        if not fingerprint:
            return
        pathology_counts[fingerprint] = int(pathology_counts.get(fingerprint, 0) or 0) + 1
        repeat_count = pathology_counts[fingerprint]
        if repeat_count < 2 or fingerprint in pathology_repeat_emitted:
            return

        repeat_payload = dict(payload)
        repeat_payload["repeat_count"] = repeat_count
        repeat_payload["event"] = "STAGE4_RETRY_PATHOLOGY_REPEAT"
        try:
            append_jsonl_record(log_file, repeat_payload)
        except Exception as exc:
            logging.warning("[Stage4] retry pathology repeat sink write skipped: %s", exc)
        if callable(_audit_event):
            _audit_event(
                "stage4_retry_pathology_repeat",
                "stage4 retry pathology repeated",
                dict(repeat_payload),
            )
        pathology_repeat_emitted.add(fingerprint)

    def _log_cove_runtime_advisory(
        self,
        *,
        ep_num: int,
        round_num: int,
        source: str,
        error: Exception,
        quick_warning: str = "",
    ) -> None:
        current_project = getattr(self.ctx, "current_project", None)
        logs_dir = resolve_project_log_dir(current_project)
        if logs_dir is None:
            project_name = getattr(current_project, "name", None)
            if not isinstance(project_name, str) or not project_name.strip() or "MagicMock" in project_name:
                project_name = "_unknown_project"
            logs_dir = Path("projects") / project_name / "logs"
        payload = {
            "event": "STAGE4_COVE_RUNTIME_ADVISORY",
            "ep_num": int(ep_num),
            "round_num": int(round_num),
            "source": str(source or "").strip(),
            "error_type": type(error).__name__,
            "error_message": str(error)[:240],
            "director_pass_preserved": True,
            "quick_warning": str(quick_warning or "").strip()[:240],
        }
        try:
            Path(logs_dir).mkdir(parents=True, exist_ok=True)
            append_jsonl_record(Path(logs_dir) / "episode_production.jsonl", payload)
        except Exception as exc:
            logging.warning("[Stage4] CoVe runtime advisory sink write skipped: %s", exc)

        _audit_event = getattr(self.ctx, "audit_event", None)
        if callable(_audit_event):
            _audit_event(
                "stage4_cove_runtime_advisory",
                "stage4 CoVe runtime advisory observed",
                dict(payload),
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
                external_feedback=str(external_feedback or ""),
                entity_registry=_entity_registry,
                protagonist_name=_prot_name,
                protagonist_config=_prot_config,
                director=self.ctx.agents.get("director"),
                state_tracker=getattr(self.ctx, "state_tracker", None),
                db=getattr(self.ctx.current_project, "db", None),
            )

            if new_bp and isinstance(new_bp, dict):
                self.ctx.current_project.save_episode_blueprint(ep_num, new_bp)
                return new_bp
            return None
        except Exception as e:
            logging.warning("[V75-B] 블루프린트 재생성 내부 실패: %s", e)
            return None

    def _prepare_stage4_session(self, *, limit_mode: bool = False, target_ep: int | None = None) -> dict | None:
        """[4-R1-f] Prepare Stage 4 session: agents, context, style guide.

        Returns session config dict for _run_interview_loop, or None if data missing.
        """
        # [V64.P3] lazy imports
        from modules.core.constants import AIModels, Emojis

        # [V65] 스피너 & 전역 상수 → spinners 모듈에서 직접 import (순환 참조 해소)
        from modules.core.spinners import STAGE0_AVAILABLE, V50_MODULES_AVAILABLE
        from modules.domain.agents.chief_writer import ChiefWriter
        from modules.domain.agents.manuscript_validator import ManuscriptValidator
        from modules.validation.blocking_validator import BlockingValidator  # [V66.1]
        from modules.validation.consistency_validator import ConsistencyValidator  # [V63.2]
        from modules.validation.continuity_validator import ContinuityValidator  # [V66.1]

        # 1. 기초 데이터 점검
        if not self.ctx.current_project.master_bible or not self.ctx.current_project.arcs:
            self.ctx.ui.log(f"{Emojis.ERROR} [System] Bible 또는 Arc 데이터가 없습니다. Stage 1-2를 먼저 실행하세요.")
            return None

        # 2. Chief Writer 및 Validator 초기화
        chief_writer = ChiefWriter(
            context=self.ctx.current_project,
            client=self.ctx.sys.api_client,
            model_tier=AIModels.STAGE4_FIXED_WRITER_MODEL,
        )
        _s4_genre_type = self.ctx.selected_genre.get("type", "wuxia") if self.ctx.selected_genre else "wuxia"
        manuscript_validator = ManuscriptValidator(
            context=self.ctx.current_project, genre_type=_s4_genre_type, llm_client=self.ctx.sys.api_client
        )
        consistency_validator = ConsistencyValidator(guard=getattr(self.ctx.sys, "guard", None), genre=_s4_genre_type)
        # [V66.1] BlockingValidator/ContinuityValidator — item_states, npc_personalities, time_warnings 라우팅
        blocking_validator = BlockingValidator(context=self.ctx.current_project)
        continuity_validator = ContinuityValidator(context=self.ctx.current_project)

        # [V67.1] story_context 조립 — Director에게 작품 설정 전달
        _story_context = ""
        try:
            _bible_root = self.ctx.current_project.master_bible.get(
                "MasterBible", self.ctx.current_project.master_bible
            )
            _prot_config = _bible_root.get("protagonist_config", {})
            _sc_parts = []
            _sc_parts.append(f"- 장르: {_s4_genre_type}")
            if _prot_config:
                _sc_parts.append(f"- 주인공 이름: {_prot_config.get('name', '미상')}")
                _sc_parts.append(f"- 세계 출신: {_prot_config.get('world_origin', '미상')}")
                _incarnation = _prot_config.get("incarnation_type", "미상")
                _sc_parts.append(f"- 환생 유형: {_incarnation}")
                if _incarnation == "회귀자":
                    _sc_parts.append(
                        "→ 주인공은 미래에서 되돌아온 회귀자입니다. 미래의 사건, 주가, 인물 등을 미리 알고 있으며, 이 지식을 활용해 현재 역사를 의도적으로 변경하려 합니다. 이것은 모순이 아닙니다."
                    )
                elif _incarnation == "빙의자":
                    _sc_parts.append(
                        "→ 주인공은 다른 인물의 몸에 빙의한 존재입니다. 원래 인물의 기억/관계와 현재 인격이 다를 수 있습니다."
                    )
                elif _incarnation == "환생자":
                    _sc_parts.append(
                        "→ 주인공은 전생의 기억을 가진 환생자입니다. 전생의 지식이 단편적으로 나타날 수 있습니다."
                    )
                _core_traits = _prot_config.get("core_traits", "")
                if _core_traits:
                    _sc_parts.append(f"- 핵심 특성: {_core_traits}")
            _story_context = "\n".join(_sc_parts)
            _perf_logger.info(f"📋 [V67.1] story_context 조립 완료 ({len(_story_context)}자)")
        except Exception as _sc_err:
            _perf_logger.warning(f"⚠️ [V67.1] story_context 조립 실패 (비차단): {str(_sc_err)[:50]}")
            _story_context = f"- 장르: {_s4_genre_type}"

        self.ctx.ui.log("🎬 [V60.80] Stage 4 V2 - Chief Writer 주권주의 아키텍처 가동")
        self.ctx.ui.log(f"   • Chief Writer 모델: {AIModels.STAGE4_FIXED_WRITER_MODEL}")
        self.ctx.ui.log("   • 앙상블: 3개 병렬 생성")
        self.ctx.ui.log("   • Director 면담: 5번 기회 (패치 모드 전 라운드 적용)")

        # 3. 환경 설정
        output_dir = self.ctx.current_project.paths.drafts
        output_dir.mkdir(exist_ok=True)
        total_planned_ep = self.ctx.current_project.db.get_latest_blueprint_number()
        current_written = max(0, int(self.ctx.current_project.get_latest_episode_number() or 1) - 1)

        # 4. 플랫폼 스타일 선택
        if target_ep is not None:
            if target_ep <= current_written:
                self.ctx.ui.log(f"✅ 이미 {current_written}화까지 완료되어 제{target_ep}화 집필은 건너뜁니다.")
                return None
        elif limit_mode:
            # [TF-CX-BUG-02] 입력 범위 역전 방어: 블루프린트가 0개인 경우
            if total_planned_ep == 0:
                self.ctx.ui.log("⚠️ 블루프린트가 없습니다. Stage 3에서 먼저 설계도를 생성해주세요.")
                return None
            if current_written >= total_planned_ep:
                self.ctx.ui.log(f"✅ 이미 {current_written}화까지 완료되어 추가 집필할 범위가 없습니다.")
                return None
            target_ep = self.ctx.get_int_input(
                f"\n👉 몇 화까지 집필하시겠습니까? (현재 {current_written}화 / 최대 {total_planned_ep}화): ",
                default=total_planned_ep,
                min_val=current_written + 1,
                max_val=total_planned_ep,
            )
        else:
            target_ep = None

        self.ctx.ui.console.clear()
        self.ctx.ui.title("V60.80 CHIEF WRITER", "Director 주권주의 아키텍처")

        # [V60.95] 스타일 가이드 로드
        style_guide = ""
        reference_excerpt = ""
        saved_style = load_style_guide_anchor(self.ctx.current_project)
        if saved_style and STAGE0_AVAILABLE:
            try:
                from modules.core.stage0 import StyleGuide

                loaded_sg = StyleGuide.from_dict(saved_style)
                # [V70] Bible의 protagonist_config.pov로 오버라이드
                try:
                    _bible_pov = resolve_project_bible_pov(self.ctx.current_project)
                    if _bible_pov:
                        if loaded_sg.pov and _bible_pov != loaded_sg.pov:  # [TF-31-2]
                            logging.warning("[TF-31-2] StyleGuide POV(%s) ≠ Bible POV(%s) — Bible 우선 적용",
                                loaded_sg.pov,
                                _bible_pov,
                            )
                        loaded_sg.pov = _bible_pov
                except Exception as e:
                    _perf_logger.warning(f"[SilentPass:Stage4] Bible POV 오버라이드 실패: {e!s:.100}")
                style_guide = loaded_sg.to_prompt()
                reference_excerpt = getattr(loaded_sg, "reference_excerpt", "")
                self.ctx.ui.log(
                    f"🎨 [V60.95] 저장된 스타일 가이드 로드됨 (톤: {loaded_sg.tone}, 시점: {loaded_sg.pov})"
                )
            except Exception as e:
                self.ctx.ui.log(f"⚠️ 스타일 가이드 로드 실패: {e}")
                saved_style = None

        reference_excerpt = _clamp_reference_excerpt(reference_excerpt)

        # [V70] 스타일 가이드 없어도 Bible에 POV 설정이 있으면 최소 가이드 생성
        if not style_guide and STAGE0_AVAILABLE:
            try:
                from modules.core.stage0 import StyleGuide as _SG

                _bible_pov = resolve_project_bible_pov(self.ctx.current_project)
                if _bible_pov:
                    _min_sg = _SG(pov=_bible_pov)
                    style_guide = _min_sg.to_prompt()
                    self.ctx.ui.log(f"📖 [V70] Bible POV 기반 최소 스타일 가이드 생성 (시점: {_bible_pov})")
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

        # [V62.5] 캐릭터 보이스 가이드 주입
        if self.ctx.character_voice and self.ctx.character_voice.profiles:
            try:
                voice_prompt = self.ctx.character_voice.get_writer_injection()
                if voice_prompt:
                    style_guide += f"\n\n{voice_prompt}"
                    self.ctx.ui.log(
                        f"🎤 [V62.5] 캐릭터 보이스 가이드 주입됨 ({len(self.ctx.character_voice.profiles)}명)"
                    )
            except Exception as voice_err:
                self.ctx.ui.log(f"   ⚠️ 캐릭터 보이스 주입 실패 (비차단): {voice_err}")

        return _SessionConfig(
            chief_writer=chief_writer,
            manuscript_validator=manuscript_validator,
            consistency_validator=consistency_validator,
            blocking_validator=blocking_validator,
            continuity_validator=continuity_validator,
            s4_genre_type=_s4_genre_type,
            story_context=_story_context,
            style_guide=style_guide,
            reference_excerpt=reference_excerpt,
            target_ep=target_ep,
            output_dir=output_dir,
            v50_modules_available=V50_MODULES_AVAILABLE,
            total_planned_ep=total_planned_ep,
        )

    def stage_4_v2_chief_writer(self, limit_mode: bool = False, *, target_ep: int | None = None, skip_pause: bool = False) -> None:
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
            session = self._prepare_stage4_session(limit_mode=limit_mode, target_ep=target_ep)
            if session is None:
                return
            # 5. Episode production loop
            _should_return = self._run_interview_loop(session, skip_pause=skip_pause)
            if _should_return:
                return
            _audit_event = getattr(ctx, "audit_event", None)
            if callable(_audit_event):
                _audit_event(
                    "stage4_complete",
                    "stage4 production completed",
                    {"target_ep": getattr(session, "target_ep", target_ep)},
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
