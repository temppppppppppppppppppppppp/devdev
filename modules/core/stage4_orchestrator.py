"""
[V64.P3] Stage4Orchestrator — SovereignApp의 Stage 4 원고 집필 오케스트레이션 로직 캡슐화

SovereignApp에서 분리된 Stage 4 관련 메서드:
- stage_4_v2_chief_writer(): Chief Writer 주권주의 아키텍처 메인 루프 (~896줄)

모든 SovereignApp 속성은 self.app를 통해 접근.
"""

import dataclasses
import logging

from modules.core.constants import PatchModeThresholds
from modules.core.stage4_context_builder import Stage4ContextBuilder
from modules.core.stage4_interview_round import Stage4InterviewRound
from modules.core.stage4_post_processor import Stage4PostProcessor
from modules.validation.threshold_helper import _threshold

_perf_logger = logging.getLogger(__name__)  # [V65] PerfTimer 로깅


# ═══════════════════════════════════════════════════════════════
# [Phase 3-5C] NPC 과잉 등장 감지 (advisory-only, pure function)
# ═══════════════════════════════════════════════════════════════
def _detect_npc_overexposure(
    manuscript: str,
    npc_names,
    protagonist_name: str = "",
    *,
    max_mentions: int = _threshold("npc_exposure.max_mentions_per_episode", 15),
    core_npc_names: frozenset = frozenset(),
    min_name_length: int = 2,
):
    """에피소드 원고에서 엑스트라 NPC별 언급 횟수를 세어 임계값 초과 시 경고 dict 반환.

    주인공·핵심NPC(core_npc_names)·짧은 이름(min_name_length 미만)은 제외.
    Longest-match-first 마스킹으로 부분일치 이중 카운트 방지.
    """
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
    warning_threshold: int = _threshold("cross_episode_repetition.overlap_warning", 3),
    regression_threshold: int = _threshold("cross_episode_repetition.overlap_regression", 6),
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
    if not fingerprints or not repeated:
        return None
    unique_hashes = {r["sentence_hash"] for r in repeated}
    overlap_count = len(unique_hashes)
    if overlap_count < warning_threshold:
        return None
    overlap_ratio = overlap_count / len(fingerprints) if fingerprints else 0
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


# [Phase 3-5B] 패치 모드 임계값 (모듈 레벨 상수로 캐시)
_PATCH_REWRITE_THRESHOLD = PatchModeThresholds.REWRITE


@dataclasses.dataclass(slots=True)
class _SessionConfig:
    """[4-R2-a] Session-level config for Stage 4 interview loop."""

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


@dataclasses.dataclass(slots=True)
class _RoundOutcome:
    """[4-R2-d] Result of _handle_round_outcome."""

    final_manuscript: object  # str | None
    final_title: object  # str | None
    final_state_updates: dict
    should_return: bool


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

    def _load_chain_link_section(self, next_ep: int) -> str:
        return self.context_builder.load_chain_link_section(next_ep)

    @property
    def interview_round(self):
        """[B-1-3] Interview Round 서브모듈 (lazy init)."""
        if self._interview_round is None:
            self._interview_round = Stage4InterviewRound(self.ctx)
        return self._interview_round

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

    def _run_interview_loop(self, session: _SessionConfig) -> bool:
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
        target_ep = session.target_ep
        output_dir = session.output_dir
        v50_modules_available = session.v50_modules_available
        total_planned_ep = session.total_planned_ep

        loop_guard = 0
        # [Sweep45] max(1, ...) — latest_ep > total_planned_ep 시 음수 방지
        max_loops = max(
            1, min((target_ep or total_planned_ep) - self.ctx.current_project.get_latest_episode_number() + 5, 100)
        )

        # [V66.1] B-2: ReferenceAnchor 루프 밖 1회 생성 (내부 캐시로 DB 중복 조회 방지)
        from modules.core.reference_anchor import ReferenceAnchor

        _anchor_sys = ReferenceAnchor(self.ctx.current_project)

        # 5. 원고 생산 메인 루프
        while True:
            loop_guard += 1
            if loop_guard > max_loops:
                self.ctx.ui.log("🛑 [Safety] 루프 제한 도달. 중단합니다.")
                break

            next_ep = self.ctx.current_project.get_latest_episode_number()
            self.interview_round.time_warnings = []  # [V70] 에피소드마다 리셋 (누적 방지)
            if target_ep and next_ep > target_ep:
                self.ctx.ui.log(f"🏁 목표 회차({target_ep}화) 도달. 종료합니다.")
                break

            # Blueprint 로드
            blueprint = self.ctx.current_project.get_blueprint(next_ep)
            if not blueprint:
                self.ctx.ui.log(f"⚠️ 제{next_ep}화 Blueprint 없음. Stage 3 먼저 실행하세요.")
                break

            # Arc 데이터 검색
            arc_data = next(
                (
                    a
                    for a in self.ctx.current_project.arcs
                    if isinstance(a, dict) and a.get("ep_start", 0) <= next_ep <= a.get("ep_end", 0)
                ),
                None,
            )
            if not arc_data:
                self.ctx.ui.log(f"⚠️ 제{next_ep}화 Arc 데이터 없음.")
                break

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
            current_inventory = _ep_ctx["current_inventory"]
            current_martial_arts = _ep_ctx["current_martial_arts"]
            cumulative_bible = _ep_ctx["cumulative_bible"]
            dead_npcs = _ep_ctx["dead_npcs"]
            item_acquisition_timeline = _ep_ctx["item_acquisition_timeline"]
            _chain_link_section = _ep_ctx["chain_link_section"]
            _world_state_summary = _ep_ctx["world_state_summary"]
            # ===== [V60.80+] 기존 Writer 전달 기능 추출 =====
            # [V60.85] 장르 Guard에서 Purism Prompt 추출
            purism_prompt = ""
            if hasattr(self.ctx.sys, "guard") and self.ctx.sys.guard:
                try:
                    purism_prompt = self.ctx.sys.guard.get_v20_purism_prompt()
                except Exception as e:
                    self.ctx.ui.log(f"   ⚠️ Guard Purism Prompt 추출 실패 (비치명): {e}")

            genre_name = (getattr(self.ctx.current_project, "genre", None) or {}).get("name", "무협")
            writer_agent = self.ctx.agents.get("writer") if "writer" in self.ctx.agents else None
            _ctx_prompts = self.context_builder.build_mandatory_context(
                next_ep=next_ep,
                arc_data=arc_data,
                arc_tactical=arc_tactical,
                prev_text=prev_text,
                prev_ending=prev_ending,
                hud_report=hud_report,
                writer_agent=writer_agent,
                anchor_sys=_anchor_sys,
                s4_genre_type=s4_genre_type,
                v50_modules_available=v50_modules_available,
                pacing_analyzer=self.ctx.pacing_analyzer,
            )
            reference_anchor_prompt = _ctx_prompts["reference_anchor_prompt"]
            mandatory_context = _ctx_prompts["mandatory_context"]
            anti_trope_prompt = _ctx_prompts["anti_trope_prompt"]
            justification_prompt = _ctx_prompts["justification_prompt"]
            reflexion_prompt = _ctx_prompts["reflexion_prompt"]

            # [V60.81] NPC equipment summary extraction
            npc_equipment_summary = ""
            try:
                bible_root = self.ctx.current_project.master_bible.get(
                    "MasterBible", self.ctx.current_project.master_bible
                )
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

            # [V63] Contrastive CoT
            _effective_anti_trope = anti_trope_prompt
            if self.ctx.diversity_engine:
                try:
                    _diversity_cot = self.ctx.diversity_engine.get_writer_injection()
                    if _diversity_cot:
                        _effective_anti_trope = f"{anti_trope_prompt}\n\n{_diversity_cot}"
                except Exception:  # [V64.P4] OPTIONAL: diversity injection
                    pass

            intro_dna = "CYNICAL"

            self.ctx.ui.log(f"\n{'=' * 60}")
            self.ctx.ui.log(
                f"📝 제{next_ep}화 집필 시작 (Arc {arc_data.get('arc_no', '?')}, 위치 {arc_pos}/{total_ep_in_arc})"
            )
            self.ctx.ui.log(f"{'=' * 60}")

            # [V67] mandatory_context 우선순위 기반 스마트 트렁케이션 (50,000자 상한)
            if len(mandatory_context) > 50000:
                _original_len = len(mandatory_context)
                # 섹션 분리: "\n[" 또는 "\n\n[" 마커 기준으로 분할
                import re as _re_trunc

                _section_pattern = _re_trunc.compile(r"\n(?=\[)")
                _sections = _section_pattern.split(mandatory_context)
                # 빈 섹션 제거
                _sections = [s for s in _sections if s.strip()]
                if len(_sections) > 1:
                    # 뒤에서부터 (낮은 우선순위) 하나씩 제거
                    _removed_count = 0
                    _removed_chars = 0
                    while len("\n".join(_sections)) > 50000 and len(_sections) > 1:
                        _removed_section = _sections.pop()
                        _removed_count += 1
                        _removed_chars += len(_removed_section)
                    mandatory_context = "\n".join(_sections)
                    # [Sweep45] 첫 섹션 단독 > 50K 시 fallback truncation
                    if len(mandatory_context) > 50000:
                        mandatory_context = mandatory_context[:49950] + "\n\n...(컨텍스트 크기 초과로 일부 생략)"
                    if _removed_count > 0:
                        _perf_logger.info(
                            f"[V66.1] mandatory_context {_removed_count}개 섹션 제거 ({_removed_chars}자)"
                        )
                        self.ctx.ui.log(
                            f"   ⚠️ [V66.1] mandatory_context {_original_len}자 → {len(mandatory_context)}자 (섹션 {_removed_count}개 제거)"
                        )
                else:
                    # 섹션 분리 불가 시 기존 방식 폴백
                    mandatory_context = mandatory_context[:49950] + "\n\n...(컨텍스트 크기 초과로 일부 생략)"
                    self.ctx.ui.log(f"   ⚠️ [V66.1] mandatory_context {_original_len}자 → 50,000자로 truncate (폴백)")

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
                mandatory_context=mandatory_context,
            )
            # ===== Phase 4: Director 면담 (5회) =====
            _outcome = self._handle_round_outcome(round_ctx=_round_ctx)
            if _outcome.should_return:
                # [Sweep45] 5회 실패 시에도 벡터 메모리 동기화 보장
                self.post_processor.run_post_episode_tasks()
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
                    continue

        # [V62.3] Stage 4 루프 종료
        self.post_processor.run_post_episode_tasks()

        return False

    def _handle_round_outcome(self, *, round_ctx: _RoundContext) -> _RoundOutcome:
        """[4-R1-e-3] Run 5-round interview loop.

        Returns _RoundOutcome: final_manuscript, final_title, final_state_updates, should_return
        """
        from modules.core.spinners import StageSpinner

        next_ep = round_ctx.next_ep

        final_manuscript = None
        final_title = None
        final_state_updates = {}
        director_feedback = ""
        previous_attempt = {}

        with StageSpinner(4, f"제{next_ep}화 · 앙상블 준비") as stage4_spinner:
            for interview_round in range(5):
                _round_result = self.interview_round.run(
                    round_num=interview_round,
                    stage4_spinner=stage4_spinner,
                    director_feedback=director_feedback,
                    previous_attempt=previous_attempt,
                    round_ctx=round_ctx,
                )
                if _round_result.verdict == "PASS":
                    final_manuscript = _round_result.final_manuscript
                    final_title = _round_result.final_title
                    final_state_updates = _round_result.final_state_updates
                    break
                director_feedback = _round_result.director_feedback
                previous_attempt = _round_result.previous_attempt

        # ===== 5번 모두 실패 =====
        if not final_manuscript:
            self.ctx.ui.log(f"\n⛔ [EP {next_ep}] 5회 면담 모두 실패. 인간 검토 필요.")
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

    def _prepare_stage4_session(self, *, limit_mode: bool = False) -> dict | None:
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
        target_ep = None

        # 4. 플랫폼 스타일 선택
        if limit_mode:
            target_ep = self.ctx.get_int_input(
                f"\n👉 몇 화까지 집필하시겠습니까? (최대 {total_planned_ep}화): ",
                default=None,
                min_val=1,
                max_val=total_planned_ep,
            )

        self.ctx.ui.console.clear()
        self.ctx.ui.title("V60.80 CHIEF WRITER", "Director 주권주의 아키텍처")

        # [V60.95] 스타일 가이드 로드
        style_guide = ""
        saved_style = self.ctx.current_project.load_v20_anchor("style_guide")
        if saved_style and STAGE0_AVAILABLE:
            try:
                from modules.core.stage0 import StyleGuide

                loaded_sg = StyleGuide.from_dict(saved_style)
                # [V70] Bible의 protagonist_config.pov로 오버라이드
                try:
                    _bible = self.ctx.current_project.master_bible or {}
                    _bible_root = _bible.get("MasterBible", _bible)
                    _bible_pov = _bible_root.get("protagonist_config", {}).get("pov", "")
                    if _bible_pov:
                        loaded_sg.pov = _bible_pov
                except Exception as e:
                    _perf_logger.warning(f"[SilentPass:Stage4] Bible POV 오버라이드 실패: {e!s:.100}")
                style_guide = loaded_sg.to_prompt()
                self.ctx.ui.log(
                    f"🎨 [V60.95] 저장된 스타일 가이드 로드됨 (톤: {loaded_sg.tone}, 시점: {loaded_sg.pov})"
                )
            except Exception as e:
                self.ctx.ui.log(f"⚠️ 스타일 가이드 로드 실패: {e}")
                saved_style = None

        # [V70] 스타일 가이드 없어도 Bible에 POV 설정이 있으면 최소 가이드 생성
        if not style_guide and STAGE0_AVAILABLE:
            try:
                from modules.core.stage0 import StyleGuide as _SG

                _bible = self.ctx.current_project.master_bible or {}
                _bible_root = _bible.get("MasterBible", _bible)
                _bible_pov = _bible_root.get("protagonist_config", {}).get("pov", "")
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
            target_ep=target_ep,
            output_dir=output_dir,
            v50_modules_available=V50_MODULES_AVAILABLE,
            total_planned_ep=total_planned_ep,
        )

    def stage_4_v2_chief_writer(self, limit_mode: bool = False) -> None:
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
            session = self._prepare_stage4_session(limit_mode=limit_mode)
            if session is None:
                return
            # 5. Episode production loop
            if self._run_interview_loop(session):
                return

        except KeyboardInterrupt:
            self.ctx.ui.log("\n⚠️ 사용자 중단 요청. 저장 후 종료합니다.")
            self.ctx.flush_audit_buffer()  # [V66.1] B-3
            self.ctx.safe_commit()
        except Exception as e:
            self.ctx.ui.log(f"\n🚨 Stage 4 V2 오류: {e}")
            import traceback

            traceback.print_exc()
            self.ctx.flush_audit_buffer()  # [V66.1] B-3
            self.ctx.safe_commit()
