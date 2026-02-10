"""
[V64.P3] Stage4Orchestrator — SovereignApp의 Stage 4 원고 집필 오케스트레이션 로직 캡슐화

SovereignApp에서 분리된 Stage 4 관련 메서드:
- stage_4_v2_chief_writer(): Chief Writer 주권주의 아키텍처 메인 루프 (~896줄)

모든 SovereignApp 속성은 self.app를 통해 접근.
"""

import os
import json
import logging
from typing import Optional

_perf_logger = logging.getLogger(__name__)  # [V65] PerfTimer 로깅


class Stage4Orchestrator:
    """
    [V64.P3] SovereignApp의 Stage 4 원고 집필 오케스트레이션 로직 캡슐화

    패턴: self.app = SovereignApp 인스턴스
    """

    def __init__(self, app):
        """
        Args:
            app: SovereignApp 인스턴스 (모든 속성 접근용)
        """
        self.app = app

    # ═══════════════════════════════════════════════════════════════════════
    # [V66] 확장 Lookback
    # ═══════════════════════════════════════════════════════════════════════

    def _build_extended_lookback_digest(self, next_ep: int) -> str:
        """
        [V66] 직전 10화 원고에서 1-2줄 요약 추출 → mandatory_context 주입.
        기존 3화 lookback을 보완하여 중장기 맥락 제공.
        총 1,500자 이내 truncate.

        [V66.1] B-4: 전문 로드 → SQL SUBSTR 발췌 조회로 최적화 (~100KB I/O 제거/ep).
        첫 200자만 사용하므로 DB에서 200자만 가져옴.
        """
        import re
        if next_ep <= 3:
            return ""
        try:
            # 직전 10화 (기존 3화 제외 → ep-10 ~ ep-4 범위)
            start_ep = max(1, next_ep - 10)
            end_ep = max(1, next_ep - 3)  # 최근 3화는 기존 lookback이 커버
            # [V66.1] B-4: 발췌 전용 쿼리 (첫 200자만 DB에서 조회)
            manuscripts = self.app.current_project.db.get_recent_manuscript_excerpts(
                before_ep=next_ep, limit=10, max_chars=200
            )
            if not manuscripts or not isinstance(manuscripts, list):
                return ""

            lines = []
            for ms in manuscripts:
                ep_num = ms.get("ep_num", 0)
                if ep_num < start_ep or ep_num >= end_ep:  # end_ep exclusive: 최근 3화는 기존 lookback이 커버
                    continue
                content = ms.get("content", "")
                if not content:
                    continue
                # 첫 문단 또는 첫 150자에서 핵심 요약 추출
                first_para = content.split("\n\n")[0] if "\n\n" in content else content[:150]
                # 줄바꿈 정리
                first_para = re.sub(r'\s+', ' ', first_para).strip()
                if len(first_para) > 150:
                    first_para = first_para[:147] + "..."
                lines.append(f"[제{ep_num}화] {first_para}")

            if not lines:
                return ""

            digest = "\n".join(lines)
            if len(digest) > 1500:
                digest = digest[:1497] + "..."
            return f"[확장 Lookback: 직전 4~10화 요약]\n{digest}"
        except Exception:
            return ""

    # ═══════════════════════════════════════════════════════════════════════
    # 메인 파이프라인
    # ═══════════════════════════════════════════════════════════════════════

    def stage_4_v2_chief_writer(self, limit_mode: bool = False) -> None:
        """
        [V60.80] Stage 4 V2 - Chief Writer 주권주의 아키텍처

        핵심 철학: "Blueprint를 토대로 양질의 원고를 연속성 있게 생산한다"

        구조:
        - Phase 1: 프롬프트 조립 (필수만)
        - Phase 2: Chief Writer 앙상블 (3개 병렬 생성)
        - Phase 3: Python 사전 검증 (경고만, REJECT 권한 없음)
        - Phase 4: Director 면담 (3번 기회)
        - 냉동인간: 기존 Writer (3번 실패 시)
        - 인간 개입: 냉동인간도 실패 시 중단
        """
        # [V64.P3] lazy imports
        from modules.domain.agents.chief_writer import ChiefWriter
        from modules.domain.agents.manuscript_validator import ManuscriptValidator
        from modules.validation.consistency_validator import ConsistencyValidator  # [V63.2]
        from modules.validation.blocking_validator import BlockingValidator  # [V66.1]
        from modules.validation.continuity_validator import ContinuityValidator  # [V66.1]
        from modules.core.constants import AIModels, RetryLimits, WritingLimits, Emojis

        # [V65] 스피너 & 전역 상수 → spinners 모듈에서 직접 import (순환 참조 해소)
        from modules.core.spinners import StageSpinner, V50_MODULES_AVAILABLE, STAGE0_AVAILABLE

        # 1. 기초 데이터 점검
        if not self.app.current_project.master_bible or not self.app.current_project.arcs:
            self.app.ui.log(f"{Emojis.ERROR} [System] Bible 또는 Arc 데이터가 없습니다. Stage 1-2를 먼저 실행하세요.")
            return

        # 2. Chief Writer 및 Validator 초기화
        chief_writer = ChiefWriter(
            context=self.app.current_project,
            client=self.app.sys.api_client,
            model_tier=AIModels.STAGE4_FIXED_WRITER_MODEL
        )
        _s4_genre_type = self.app.selected_genre.get('type', 'wuxia') if self.app.selected_genre else 'wuxia'
        manuscript_validator = ManuscriptValidator(
            context=self.app.current_project,
            genre_type=_s4_genre_type,
            llm_client=self.app.sys.api_client
        )
        consistency_validator = ConsistencyValidator(
            guard=getattr(self.app.sys, 'guard', None),
            genre=_s4_genre_type
        )
        # [V66.1] BlockingValidator/ContinuityValidator — item_states, npc_personalities, time_warnings 라우팅
        blocking_validator = BlockingValidator(context=self.app.current_project)
        continuity_validator = ContinuityValidator(context=self.app.current_project)

        self.app.ui.log(f"🎬 [V60.80] Stage 4 V2 - Chief Writer 주권주의 아키텍처 가동")
        self.app.ui.log(f"   • Chief Writer 모델: {AIModels.STAGE4_FIXED_WRITER_MODEL}")
        self.app.ui.log(f"   • 앙상블: 3개 병렬 생성")
        self.app.ui.log(f"   • Director 면담: 3번 기회")
        self.app.ui.log(f"   • 냉동인간: 기존 Writer (최후의 수단)")

        # 3. 환경 설정
        output_dir = self.app.current_project.paths.drafts
        output_dir.mkdir(exist_ok=True)
        total_planned_ep = self.app.current_project.db.get_latest_blueprint_number()
        target_ep = None

        try:
            # 4. 플랫폼 스타일 선택
            if limit_mode:
                target_ep = self.app._get_int_input(
                    f"\n👉 몇 화까지 집필하시겠습니까? (최대 {total_planned_ep}화): ",
                    default=None, min_val=1, max_val=total_planned_ep
                )

            self.app.ui.console.clear()
            self.app.ui.title("V60.80 CHIEF WRITER", "Director 주권주의 아키텍처")

            # [V60.95] 스타일 가이드 로드
            style_guide = ""
            saved_style = self.app.current_project.load_v20_anchor('style_guide')
            if saved_style and STAGE0_AVAILABLE:
                try:
                    from modules.core.stage0 import StyleGuide
                    loaded_sg = StyleGuide.from_dict(saved_style)
                    style_guide = loaded_sg.to_prompt()
                    self.app.ui.log(f"🎨 [V60.95] 저장된 스타일 가이드 로드됨 (톤: {loaded_sg.tone})")
                except Exception as e:
                    self.app.ui.log(f"⚠️ 스타일 가이드 로드 실패: {e}")
                    saved_style = None

            if not style_guide:
                style_choice = self.app._get_int_input(
                    "\n👉 스타일 선택 (1.카카오 / 2.네이버): ",
                    default=1, min_val=1, max_val=2
                )
                style_guide = (
                    "네이버: 심리 묘사 강조, 3-4문장 단위 줄바꿈, 여백 극대화"
                    if style_choice == 2 else
                    "카카오: 사이다 전개, 절벽걸기, 4K 해상도 묘사"
                )

            # [V62.5] 캐릭터 보이스 가이드 주입
            if self.app.character_voice and self.app.character_voice.profiles:
                try:
                    voice_prompt = self.app.character_voice.get_writer_injection()
                    if voice_prompt:
                        style_guide += f"\n\n{voice_prompt}"
                        self.app.ui.log(f"🎤 [V62.5] 캐릭터 보이스 가이드 주입됨 ({len(self.app.character_voice.profiles)}명)")
                except Exception as voice_err:
                    self.app.ui.log(f"   ⚠️ 캐릭터 보이스 주입 실패 (비차단): {voice_err}")

            loop_guard = 0
            max_loops = min((target_ep or total_planned_ep) - self.app.current_project.get_latest_episode_number() + 5, 100)

            # [V66.1] B-2: ReferenceAnchor 루프 밖 1회 생성 (내부 캐시로 DB 중복 조회 방지)
            from modules.core.reference_anchor import ReferenceAnchor
            _anchor_sys = ReferenceAnchor(self.app.current_project)

            # 5. 원고 생산 메인 루프
            while True:
                loop_guard += 1
                if loop_guard > max_loops:
                    self.app.ui.log("🛑 [Safety] 루프 제한 도달. 중단합니다.")
                    break

                next_ep = self.app.current_project.get_latest_episode_number()
                if target_ep and next_ep > target_ep:
                    self.app.ui.log(f"🏁 목표 회차({target_ep}화) 도달. 종료합니다.")
                    break

                # Blueprint 로드
                blueprint = self.app.current_project.get_blueprint(next_ep)
                if not blueprint:
                    self.app.ui.log(f"⚠️ 제{next_ep}화 Blueprint 없음. Stage 3 먼저 실행하세요.")
                    break

                # Arc 데이터 검색
                arc_data = next(
                    (a for a in self.app.current_project.arcs
                     if isinstance(a, dict) and a.get('ep_start', 0) <= next_ep <= a.get('ep_end', 0)),
                    None
                )
                if not arc_data:
                    self.app.ui.log(f"⚠️ 제{next_ep}화 Arc 데이터 없음.")
                    break

                arc_pos = next_ep - arc_data.get('ep_start', next_ep) + 1
                total_ep_in_arc = arc_data.get('ep_count', 5)
                arc_tactical = arc_data.get('tactical_doc', '')

                # 직전 화 원고
                prev_ms_data = self.app.current_project.db.get_manuscript(next_ep - 1)
                prev_text = prev_ms_data.get('content', '') if prev_ms_data else ""
                prev_ending = prev_text[-500:] if prev_text else ""

                # [V62.6] 에피소드 상태 다이제스트
                _episode_digest = ""
                if prev_text and hasattr(chief_writer, '_generate_episode_digest'):
                    _episode_digest = chief_writer._generate_episode_digest(prev_text, next_ep - 1)

                # HUD 리포트
                hud_report = self.app.sys.hud.get_v20_hud_report() if hasattr(self.app.sys, 'hud') else ""

                # ===== [V60.80 FIX] 미래 침범 방지 데이터 추출 =====
                current_inventory = []
                current_martial_arts = []
                if hasattr(self.app.sys, 'hud') and self.app.sys.hud:
                    current_inventory = list(self.app.sys.hud.inventory) if hasattr(self.app.sys.hud, 'inventory') and self.app.sys.hud.inventory else []
                    current_martial_arts = list(self.app.sys.hud.techniques) if hasattr(self.app.sys.hud, 'techniques') and self.app.sys.hud.techniques else []

                cumulative_bible = self.app.current_project.db.get_cumulative_bible(next_ep - 1)
                dead_npcs = cumulative_bible.get('dead_npcs', []) if cumulative_bible else []

                item_acquisition_timeline = self.app._build_item_acquisition_timeline(next_ep - 1)

                # ===== [V60.80+] 기존 Writer 핵심 기능 추출 =====
                reference_anchor_prompt = ""
                mandatory_context = ""

                anti_trope_prompt = ""
                justification_prompt = ""
                reflexion_prompt = ""
                genre_name = getattr(self.app.current_project, 'genre', {}).get('name', '무협')

                # [V60.85] 장르 Guard에서 Purism Prompt 추출
                purism_prompt = ""
                if hasattr(self.app.sys, 'guard') and self.app.sys.guard:
                    try:
                        purism_prompt = self.app.sys.guard.get_v20_purism_prompt()
                    except Exception as e:
                        self.app.ui.log(f"   ⚠️ Guard Purism Prompt 추출 실패 (비차단): {e}")

                # 기존 Writer 인스턴스에서 핵심 기능 프롬프트 추출
                if 'writer' in self.app.agents:
                    writer_agent = self.app.agents['writer']
                    try:
                        # [V66.1] B-2: 루프 밖에서 생성된 _anchor_sys 재사용 (내부 캐시로 DB 1회 로드)
                        relevant_anchors = _anchor_sys.get_relevant_anchors(
                            current_ep_num=next_ep,
                            arc_context=arc_tactical or "",
                            n_anchors=5
                        )
                        critical_anchors = _anchor_sys.get_critical_anchors(
                            current_ep_num=next_ep,
                            anchor_types=['item', 'injury', 'power', 'location']
                        )
                        if relevant_anchors or critical_anchors:
                            reference_anchor_prompt = _anchor_sys.generate_reference_prompt(
                                relevant_anchors=relevant_anchors,
                                critical_anchors=critical_anchors
                            )
                    except Exception as e:
                        self.app.ui.log(f"   ⚠️ ReferenceAnchor 로드 실패 (비차단): {e}")

                    try:
                        mandatory_context = writer_agent._build_mandatory_context(next_ep)
                    except Exception as e:
                        self.app.ui.log(f"   ⚠️ Mandatory Context 실패 (비차단): {e}")

                    # [V66.1] mandatory_context를 list로 조립 후 마지막에 join (O(n^2) → O(n) GC 경감)
                    _mc_parts = [mandatory_context] if mandatory_context else []  # [V66.1] C-1

                # [V63] Arc 제약 요약을 mandatory_context에 주입
                    _arc_cs = arc_data.get("constraint_summary", "") if arc_data else ""
                    if _arc_cs:
                        _mc_parts.append(f"[Arc 제약 - MUST NOT DO]\n{_arc_cs}")

                    # [V66.1] F-6: mandatory_context 우선순위 재배치 — 중요도 순 (25K truncation 시 상위가 생존)
                    # Priority 1: 파괴된 조직/장소 (BLOCKING level)
                    if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                        _destroyed = self.app.state_tracker.get_entity_destruction_summary()
                        if _destroyed:
                            _mc_parts.append(_destroyed)

                    # Priority 2: 완결 플롯 (재발생 방지)
                    if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                        _resolved = self.app.state_tracker.get_resolved_plots_summary()
                        if _resolved:
                            _mc_parts.append(_resolved)

                    # Priority 3: NPC 성격/동기 (성격 이탈 방지)
                    if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                        _personality = self.app.state_tracker.get_npc_personality_summary()
                        if _personality:
                            _mc_parts.append(_personality)

                    # Priority 4: NPC-NPC 관계 (관계 모순 방지)
                    if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                        _npc_rel = self.app.state_tracker.get_npc_npc_relationship_summary()
                        if _npc_rel:
                            _mc_parts.append(_npc_rel)

                    # [V66.1] Priority 5: NPC 신체 변화 (신체 일관성 — F-8)
                    if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                        _perm_inj = self.app.state_tracker.get_permanent_injury_summary()
                        if _perm_inj:
                            _mc_parts.append(_perm_inj)

                    # [V66.1] Priority 6: 시간선 요약 (시간 모순 방지 — F-1)
                    if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                        _timeline = self.app.state_tracker.get_time_timeline_summary()
                        if _timeline:
                            _mc_parts.append(_timeline)

                    # [V66.1] Priority 7: 동행자 현황 (동행 모순 방지)
                    if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                        _companions = self.app.state_tracker.get_companion_summary()
                        if _companions:
                            _mc_parts.append(_companions)

                    # [V66.1] Priority 8: 미이행 약속/맹세 (서사 약속 추적)
                    if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                        _commitments = self.app.state_tracker.get_commitment_summary()
                        if _commitments:
                            _mc_parts.append(_commitments)

                    # [V66.1] Priority 9: 주인공 감정 상태 (감정 일관성)
                    if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                        _emotion = self.app.state_tracker.get_protagonist_emotion_summary()
                        if _emotion:
                            _mc_parts.append(_emotion)

                    # Priority 10: 아이템 상태 (아이템 모순 방지)
                    if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                        _item_state = self.app.state_tracker.get_item_state_summary()
                        if _item_state:
                            _mc_parts.append(_item_state)

                    # Priority 11: 플롯 서스펜션 (플롯 관리)
                    if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                        _plot_suspension = self.app.state_tracker.get_plot_suspension_summary(arc_data.get('arc_no', 0))
                        if _plot_suspension:
                            _mc_parts.append(_plot_suspension)

                    # Priority 12: NPC 대화 스타일 (캐릭터 보이스)
                    if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                        _dialogue_style = self.app.state_tracker.get_npc_dialogue_style_summary()
                        if _dialogue_style:
                            _mc_parts.append(_dialogue_style)

                    # Priority 13: 멀티-Arc 요약 (직전 3개 Arc)
                    try:
                        arc_summaries = []
                        current_arc_no = arc_data.get('arc_no', 1) if arc_data else 1
                        for prev_arc in range(max(1, current_arc_no - 3), current_arc_no):
                            arc_sum = self.app.current_project.load_v20_anchor(f"arc_summary_{prev_arc}")
                            if arc_sum and isinstance(arc_sum, dict):
                                arc_summaries.append(arc_sum)
                        if arc_summaries:
                            _arc_summary_text = self.app.state_tracker.format_arc_summary_for_prompt(arc_summaries)
                            if _arc_summary_text:
                                _mc_parts.append(_arc_summary_text)
                    except Exception as e:
                        self.app.ui.log(f"   \u26a0\ufe0f [V66] Arc 요약 주입 실패 (비차단): {e}")

                    # Priority 14: 금융 상태 레지스트리 (투자물 전용)
                    if _s4_genre_type == 'investment' and hasattr(self.app, 'state_tracker'):
                        _fin_summary = self.app.state_tracker.get_financial_state_summary()
                        if _fin_summary:
                            _mc_parts.append(_fin_summary)

                    # Priority 15: ChromaDB 멀티쿼리 시맨틱 검색
                    try:
                        if hasattr(self.app, 'memory') and self.app.memory and prev_ending:
                            _mq_queries = [prev_ending]
                            if arc_data and arc_data.get("state_changes"):
                                _sc = arc_data["state_changes"]
                                _npc_names = []
                                for _field in ["npc_deaths", "relationship_changes", "npc_injuries"]:
                                    for _entry in (_sc.get(_field) or []):
                                        _n = _entry.get("name") or _entry.get("npc", "")
                                        if _n:
                                            _npc_names.append(_n)
                                if _npc_names:
                                    _mq_queries.append(" ".join(_npc_names[:5]))
                            if arc_tactical and len(arc_tactical) > 50:
                                _mq_queries.append(arc_tactical[:300])
                            # [V66] 장르별 추가 쿼리
                            _genre_queries = {
                                'hunter': ['던전 클리어 각성 스킬 랭크'],
                                'investment': ['포트폴리오 거래 수익률 투자'],
                                'fantasy': ['마법 축복 주문 마나 정령'],
                            }
                            if _s4_genre_type in _genre_queries:
                                _mq_queries.extend(_genre_queries[_s4_genre_type])
                            _vector_memory = self.app.memory.retrieve_multi_query_context(
                                queries=_mq_queries,
                                current_ep=next_ep,
                                n_per_query=3,
                                max_results=5
                            )
                            if _vector_memory:
                                _mc_parts.append(f"[과거 유사 맥락 (벡터 검색)]\n{_vector_memory}")
                    except Exception as e:
                        self.app.ui.log(f"   ⚠️ ChromaDB 시맨틱 검색 실패 (비차단): {e}")

                    # Priority 16: 확장 Lookback (직전 4~10화 요약)
                    try:
                        _ext_lookback = self._build_extended_lookback_digest(next_ep)
                        if _ext_lookback:
                            _mc_parts.append(_ext_lookback)
                    except Exception as e:
                        self.app.ui.log(f"   ⚠️ 확장 Lookback 실패 (비차단): {e}")

                    # Priority 17: ForeshadowTracker 프롬프트 주입
                    try:
                        if V50_MODULES_AVAILABLE and self.app.foreshadow_tracker:
                            _foreshadow_prompt = self.app.foreshadow_tracker.generate_writer_prompt(next_ep)
                            if _foreshadow_prompt:
                                _mc_parts.append(_foreshadow_prompt)
                    except Exception as e:
                        self.app.ui.log(f"   ⚠️ ForeshadowTracker 프롬프트 실패 (비차단): {e}")

                    # Priority 18: SemanticPlotGuard 경고 주입
                    if getattr(self.app, 'semantic_plot_guard', None):
                        try:
                            tactical_text = arc_data.get('tactical_doc', '') if arc_data else ''
                            if isinstance(tactical_text, dict):
                                tactical_text = str(tactical_text)
                            _spg_warnings = self.app.semantic_plot_guard.check_new_arc(tactical_doc=tactical_text)
                            if _spg_warnings:
                                _spg_text = self.app.semantic_plot_guard.format_warnings(_spg_warnings)
                                if _spg_text:
                                    _mc_parts.append(_spg_text)
                        except Exception:
                            pass

                    # Priority 19: 호흡 분석기 (코스메틱 — truncation 우선 대상)
                    _pacing_analyzer = getattr(self.app, 'pacing_analyzer', None)
                    if _pacing_analyzer and prev_text and len(prev_text) >= 100:
                        try:
                            _pacing_result = _pacing_analyzer.analyze(prev_text)
                            _pacing_prompt = _pacing_analyzer.generate_pacing_prompt(_pacing_result)
                            if _pacing_prompt:
                                _mc_parts.append(_pacing_prompt)
                        except Exception as _pace_err:
                            self.app.ui.log(f"   ⚠️ [V65] 호흡 분석 실패 (비차단): {str(_pace_err)[:60]}")

                    # Priority 20: 장기 내러티브 요약 (Arc 요약 등으로 이미 커버 — 최하위)
                    try:
                        _narrative_summaries = self.app._load_narrative_summaries()
                        if _narrative_summaries:
                            _mc_parts.append(_narrative_summaries)
                    except Exception as e:  # [V64.P4] IMPORTANT: narrative summary load failure
                        self.app.ui.log(f"   ⚠️ [V64.P4] 내러티브 요약 로드 실패 (비차단): {str(e)[:60]}")

                    # [V66.1] C-1: list → join (O(n) 단일 할당)
                    mandatory_context = "\n\n".join(_mc_parts)

                    try:
                        anti_trope_prompt = writer_agent._build_anti_trope_instructions(genre_name)
                    except Exception as e:
                        self.app.ui.log(f"   ⚠️ Anti-Trope 실패 (비차단): {e}")

                    try:
                        justification_prompt = writer_agent._build_justification_guidance(hud_report, genre_name)
                    except Exception as e:
                        self.app.ui.log(f"   ⚠️ Justification 실패 (비차단): {e}")

                    try:
                        if next_ep >= 20:
                            from modules.core.reflexion_manager import ReflexionManager
                            reflexion = ReflexionManager(self.app.current_project)
                            reflexion_prompt = reflexion.get_prompt_injection(min_frequency=2)
                    except Exception as e:
                        self.app.ui.log(f"   ⚠️ Reflexion 실패 (비차단): {e}")

                # [V60.81] NPC 장비 현황 추출
                npc_equipment_summary = ""
                try:
                    bible_root = self.app.current_project.master_bible.get('MasterBible', self.app.current_project.master_bible)
                    assets = bible_root.get('AssetLibrary', {})
                    key_npcs = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])
                    npc_equipment_lines = []
                    for npc in key_npcs:
                        if isinstance(npc, dict):
                            npc_name = npc.get('name') or npc.get('Name', '알 수 없음')
                            npc_hud = npc.get('NPC_Martial_HUD', {})
                            if isinstance(npc_hud, dict):
                                equip = npc_hud.get('equipment', [])
                                if equip:
                                    npc_equipment_lines.append(f"- {npc_name}: {equip}")
                    npc_equipment_summary = "\n".join(npc_equipment_lines) if npc_equipment_lines else "NPC 장비 정보 없음"
                except Exception as e:
                    self.app.ui.log(f"   ⚠️ NPC 장비 현황 추출 실패 (비차단): {e}")
                    npc_equipment_summary = ""

                # [V63] Contrastive CoT
                _effective_anti_trope = anti_trope_prompt
                if self.app.diversity_engine:
                    try:
                        _diversity_cot = self.app.diversity_engine.get_writer_injection()
                        if _diversity_cot:
                            _effective_anti_trope = f"{anti_trope_prompt}\n\n{_diversity_cot}"
                    except Exception:  # [V64.P4] OPTIONAL: diversity injection
                        pass

                intro_dna = "CYNICAL"

                self.app.ui.log(f"\n{'='*60}")
                self.app.ui.log(f"📝 제{next_ep}화 집필 시작 (Arc {arc_data.get('arc_no', '?')}, 위치 {arc_pos}/{total_ep_in_arc})")
                self.app.ui.log(f"{'='*60}")

                # ===== Phase 4: Director 면담 (3번 기회) =====
                final_manuscript = None
                final_title = None
                final_state_updates = {}
                director_feedback = ""
                previous_attempt = {}

                # [V66.1] mandatory_context 우선순위 기반 스마트 트렁케이션 (25,000자 상한)
                if len(mandatory_context) > 25000:
                    _original_len = len(mandatory_context)
                    # 섹션 분리: "\n[" 또는 "\n\n[" 마커 기준으로 분할
                    import re as _re_trunc
                    _section_pattern = _re_trunc.compile(r'\n(?=\[)')
                    _sections = _section_pattern.split(mandatory_context)
                    # 빈 섹션 제거
                    _sections = [s for s in _sections if s.strip()]
                    if len(_sections) > 1:
                        # 뒤에서부터 (낮은 우선순위) 하나씩 제거
                        _removed_count = 0
                        _removed_chars = 0
                        while len("\n".join(_sections)) > 25000 and len(_sections) > 1:
                            _removed_section = _sections.pop()
                            _removed_count += 1
                            _removed_chars += len(_removed_section)
                        mandatory_context = "\n".join(_sections)
                        if _removed_count > 0:
                            print(f"  [V66.1] mandatory_context {_removed_count}개 섹션 제거 ({_removed_chars}자)")
                            self.app.ui.log(f"   ⚠️ [V66.1] mandatory_context {_original_len}자 → {len(mandatory_context)}자 (섹션 {_removed_count}개 제거)")
                    else:
                        # 섹션 분리 불가 시 기존 방식 폴백
                        mandatory_context = mandatory_context[:24950] + "\n\n...(컨텍스트 크기 초과로 일부 생략)"
                        self.app.ui.log(f"   ⚠️ [V66.1] mandatory_context {_original_len}자 → 25,000자로 truncate (폴백)")

                # [V61.6] 전체 면담 루프를 스피너로 감싸기
                with StageSpinner(4, f"제{next_ep}화 · 앙상블 준비") as stage4_spinner:
                  for interview_round in range(3):
                    stage4_spinner.update_detail(f"제{next_ep}화 · {interview_round + 1}차 면담 · 앙상블 생성")
                    self.app.ui.log(f"\n🎬 [{interview_round + 1}차 면담] Chief Writer 앙상블 생성 중...")

                    # Phase 2: Chief Writer 앙상블 생성
                    # [V65] PerfTimer: 원고 생성 측정
                    try:
                        self.app.perf_timer.start(f"s4_ep{next_ep}_generate_r{interview_round}")
                    except Exception:
                        pass
                    if interview_round == 0:
                        candidates = chief_writer.generate_ensemble(
                            ep_num=next_ep,
                            blueprint=blueprint,
                            prev_manuscript=prev_text,
                            hud_report=hud_report,
                            arc_doc=arc_tactical,
                            master_bible=self.app.current_project.master_bible,
                            style_guide=style_guide,
                            current_inventory=current_inventory,
                            current_martial_arts=current_martial_arts,
                            dead_npcs=dead_npcs,
                            item_acquisition_timeline=item_acquisition_timeline,
                            reference_anchor_prompt=reference_anchor_prompt,
                            mandatory_context=mandatory_context,
                            anti_trope_prompt=_effective_anti_trope,
                            justification_prompt=justification_prompt,
                            reflexion_prompt=reflexion_prompt,
                            genre_name=genre_name,
                            npc_equipment_summary=npc_equipment_summary,
                            intro_dna=intro_dna,
                            purism_prompt=purism_prompt,
                            state_tracker=getattr(self.app, 'state_tracker', None)
                        )
                    else:
                        candidates = chief_writer.regenerate_with_feedback(
                            ep_num=next_ep,
                            blueprint=blueprint,
                            prev_manuscript=prev_text,
                            hud_report=hud_report,
                            arc_doc=arc_tactical,
                            master_bible=self.app.current_project.master_bible,
                            style_guide=style_guide,
                            director_feedback=director_feedback,
                            previous_attempt=previous_attempt,
                            attempt_number=interview_round + 1,
                            current_inventory=current_inventory,
                            current_martial_arts=current_martial_arts,
                            dead_npcs=dead_npcs,
                            item_acquisition_timeline=item_acquisition_timeline,
                            reference_anchor_prompt=reference_anchor_prompt,
                            mandatory_context=mandatory_context,
                            anti_trope_prompt=_effective_anti_trope,
                            justification_prompt=justification_prompt,
                            reflexion_prompt=reflexion_prompt,
                            genre_name=genre_name,
                            npc_equipment_summary=npc_equipment_summary,
                            intro_dna=intro_dna,
                            purism_prompt=purism_prompt,
                            state_tracker=getattr(self.app, 'state_tracker', None)
                        )

                    # [V65] PerfTimer: 원고 생성 종료
                    try:
                        self.app.perf_timer.stop(f"s4_ep{next_ep}_generate_r{interview_round}")
                    except Exception:
                        pass

                    # Phase 3: Python 사전 검증
                    stage4_spinner.update_detail(f"제{next_ep}화 · {interview_round + 1}차 면담 · Python 검증")
                    self.app.ui.log(f"   🔍 Python 사전 검증 중...")
                    _recent_ms = []
                    try:
                        _recent_ms = self.app.current_project.db.get_recent_manuscripts(before_ep=next_ep, limit=5)
                    except (AttributeError, Exception) as e:  # [V64.P4] IMPORTANT: recent manuscripts for cross-ep validation
                        self.app.ui.log(f"   ⚠️ [V64.P4] 최근 원고 로드 실패 (교차검증 약화): {str(e)[:60]}")
                    validation_results = manuscript_validator.validate_all_candidates(
                        candidates=candidates,
                        blueprint=blueprint,
                        prev_manuscript=prev_text,
                        hud_report=hud_report,
                        recent_manuscripts=_recent_ms
                    )

                    for i, vr in enumerate(validation_results):
                        strategy = candidates[i].get('strategy_name', f'후보{i+1}') if i < len(candidates) else f'후보{i+1}'
                        self.app.ui.log(f"      • {strategy}: 경고 {vr.get('warning_count', 0)}개, 분량 {vr.get('metrics', {}).get('length', 0)}자")

                    # [V63.2] ConsistencyValidator
                    try:
                        _cv_context = {
                            'martial_hud': {},
                            'karma_matrix': {},
                            'asset_library': {},
                            'npc_profiles': {},
                            'prev_episode_events': [],
                            'ep_num': next_ep,
                        }
                        # [V66.1] 시간선 경고를 검증 컨텍스트에 주입
                        _cv_context["time_warnings"] = getattr(self, '_time_consistency_warnings', [])
                        # [V66.1] BlockingValidator/ContinuityValidator에 추적 데이터 전달
                        if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                            _cv_context["item_states"] = {
                                name: info.get("condition", "정상")
                                for name, info in self.app.state_tracker.item_state_registry.items()
                            } if hasattr(self.app.state_tracker, 'item_state_registry') else {}
                            _cv_context["npc_personalities"] = {
                                name: {"traits": info.get("personality_traits", ""), "motivation": info.get("primary_motivation", "")}
                                for name, info in self.app.state_tracker.npc_registry.items()
                                if info.get("personality_traits")
                            } if hasattr(self.app.state_tracker, 'npc_registry') else {}
                        for ci, cand in enumerate(candidates):
                            _cv_ms = cand.get('manuscript', '')
                            if _cv_ms and ci < len(validation_results):
                                cv_result = consistency_validator.validate(_cv_ms, _cv_context)
                                cv_violations = cv_result.get('violations', [])
                                cv_penalty = cv_result.get('score_penalty', 0)
                                if cv_violations:
                                    for v in cv_violations:
                                        reason = v.get('reason', str(v))
                                        validation_results[ci]['warnings'].append(f"[V63.2] 일관성: {reason}")
                                    validation_results[ci]['warning_count'] = len(validation_results[ci]['warnings'])
                                    validation_results[ci]['focus_points'].append(
                                        f"일관성 위반 {len(cv_violations)}건 (감점 {cv_penalty})"
                                    )
                                    self.app.ui.log(f"      ⚠️ 후보{ci+1} 일관성 위반 {len(cv_violations)}건")
                    except Exception as _cv_err:
                        self.app.ui.log(f"      ⚠️ [V63.2] ConsistencyValidator 실행 실패: {str(_cv_err)[:60]}")

                    # [V66.1] BlockingValidator — item_states 기반 파손 아이템 사용 체크
                    try:
                        for ci, cand in enumerate(candidates):
                            _bv_ms = cand.get('manuscript', '')
                            if _bv_ms and ci < len(validation_results):
                                bv_result = blocking_validator.validate(_bv_ms, _cv_context)
                                bv_failures = bv_result.get('failures', [])
                                if bv_failures:
                                    for f in bv_failures:
                                        reason = f.get('reason', str(f))
                                        validation_results[ci]['warnings'].append(f"[V66.1] BLOCKING: {reason}")
                                    validation_results[ci]['warning_count'] = len(validation_results[ci]['warnings'])
                                    validation_results[ci]['focus_points'].append(
                                        f"BLOCKING 위반 {len(bv_failures)}건"
                                    )
                                    self.app.ui.log(f"      ⚠️ 후보{ci+1} BLOCKING 위반 {len(bv_failures)}건")
                    except Exception as _bv_err:
                        self.app.ui.log(f"      ⚠️ [V66.1] BlockingValidator 실행 실패: {str(_bv_err)[:60]}")

                    # [V66.1] ContinuityValidator — npc_personalities, time_warnings 라우팅
                    try:
                        for ci, cand in enumerate(candidates):
                            _ct_ms = cand.get('manuscript', '')
                            if _ct_ms and ci < len(validation_results):
                                ct_result = continuity_validator.validate(next_ep, _ct_ms, _cv_context)
                                ct_violations = ct_result.get('violations', [])
                                ct_warnings = ct_result.get('warnings', [])
                                if ct_violations:
                                    for v in ct_violations:
                                        reason = v.get('reason', str(v))
                                        validation_results[ci]['warnings'].append(f"[V66.1] 연속성: {reason}")
                                    validation_results[ci]['warning_count'] = len(validation_results[ci]['warnings'])
                                    validation_results[ci]['focus_points'].append(
                                        f"연속성 위반 {len(ct_violations)}건"
                                    )
                                    self.app.ui.log(f"      ⚠️ 후보{ci+1} 연속성 위반 {len(ct_violations)}건")
                                if ct_warnings:
                                    for w in ct_warnings:
                                        w_msg = w.get('reason', str(w)) if isinstance(w, dict) else str(w)
                                        validation_results[ci]['warnings'].append(f"[V66.1] 연속성 경고: {w_msg}")
                                    validation_results[ci]['warning_count'] = len(validation_results[ci]['warnings'])
                    except Exception as _ct_err:
                        self.app.ui.log(f"      ⚠️ [V66.1] ContinuityValidator 실행 실패: {str(_ct_err)[:60]}")

                    # [V61.5] 캐시 기반 연속성 검사
                    if interview_round == 0 and next_ep > 1 and candidates:
                        stage4_spinner.update_detail(f"제{next_ep}화 · 연속성 검사")
                        first_manuscript = candidates[0].get('manuscript', '')
                        continuity_check = self.app.agents['director'].check_manuscript_continuity_with_cache(
                            new_manuscript=first_manuscript,
                            ep_num=next_ep,
                            db=self.app.current_project.db,
                            limit=10
                        )
                        if continuity_check.get("decision") == "CONFLICT":
                            conflict_summary = continuity_check.get("summary", "연속성 충돌 감지")
                            self.app.ui.log(f"   ⚠️ [V61.5] 연속성 검사: {conflict_summary[:50]}...")
                            director_feedback += f"\n[연속성 충돌]\n{conflict_summary}"

                    # Phase 4: Director 면담
                    stage4_spinner.update_detail(f"제{next_ep}화 · {interview_round + 1}차 면담 · Director 심사")
                    self.app.ui.log(f"   🎬 Director 면담 중...")
                    # [V65] PerfTimer: Director 대면 측정
                    try:
                        self.app.perf_timer.start(f"s4_ep{next_ep}_director_r{interview_round}")
                    except Exception:
                        pass
                    director_result = self.app.agents['director'].select_and_judge_ensemble(
                        ep_num=next_ep,
                        candidates=candidates,
                        validation_results=validation_results,
                        blueprint=blueprint,
                        previous_ending=prev_ending,
                        arc_pos=arc_pos,
                        total_eps=total_ep_in_arc,
                        retry_count=interview_round,
                        episode_digest=_episode_digest
                    )
                    try:
                        self.app.perf_timer.stop(f"s4_ep{next_ep}_director_r{interview_round}")
                    except Exception:
                        pass

                    selected = director_result.get('selected', 'A')
                    verdict = director_result.get('verdict', 'REJECT')
                    score = director_result.get('score', 0)
                    reason = director_result.get('selection_reason', '')

                    self.app.ui.log(f"   📊 Director 판정: {verdict} (점수: {score}, 선택: 후보 {selected})")
                    self.app.ui.log(f"      └─ 사유: {reason[:80]}...")

                    if verdict == "PASS":
                        selected_candidate = director_result.get('selected_candidate', {})
                        final_manuscript = selected_candidate.get('manuscript', '')
                        final_title = selected_candidate.get('title', f'제{next_ep}화')
                        final_state_updates = director_result.get('state_updates', {})

                        # [V66] 파괴된 조직/장소 원고 내 활동 검사
                        try:
                            if hasattr(self.app, 'state_tracker') and final_manuscript:
                                _destroyed_warnings = self.app.state_tracker.check_destroyed_entity_in_manuscript(final_manuscript)
                                if _destroyed_warnings:
                                    for _dw in _destroyed_warnings:
                                        self.app.ui.log(f"   ⚠️ [V66] 파괴 엔티티 경고: {_dw.get('message', '')}")
                        except Exception:
                            pass

                        # [V66.1] F-1: 시간선 일관성 체크 → 검증 파이프라인에 경고 전달
                        if hasattr(self.app, 'state_tracker') and self.app.state_tracker:
                            try:
                                _time_warnings = self.app.state_tracker.check_time_consistency(final_manuscript, self.app.state_tracker.in_world_timeline)
                                if _time_warnings:
                                    for tw in _time_warnings:
                                        self.app.ui.log(f"   ⏰ [V66.1] 시간선 경고: {tw}")
                                    # [V66.1] 검증 파이프라인용 경고 저장
                                    if not hasattr(self, '_time_consistency_warnings'):
                                        self._time_consistency_warnings = []
                                    self._time_consistency_warnings.extend(_time_warnings)
                            except Exception:
                                pass

                        self.app.ui.log(f"   ✅ {interview_round + 1}차 면담 PASS!")
                        break
                    else:
                        feedback = director_result.get('feedback', {})
                        action_items = director_result.get('action_items', [])
                        director_feedback = "\n".join(action_items) if action_items else str(feedback.get('issues', []))
                        previous_attempt = {
                            'strategy': selected,
                            'rejection_reason': director_feedback,
                            'action_items': action_items,
                            'score': score
                        }
                        self.app.ui.log(f"   ❌ {interview_round + 1}차 면담 REJECT. 피드백: {director_feedback[:100]}...")

                # ===== 3번 모두 실패: 냉동인간 소환 =====
                if not final_manuscript:
                    self.app.ui.log(f"\n🧊 [냉동인간 소환] 3번 면담 모두 실패. 기존 Writer로 최종 시도...")

                    try:
                        frozen_result = self.app.agents['writer'].write_v20_manuscript(
                            ep_num=next_ep,
                            breakdown_doc=blueprint.get('integrated_scenario', ''),
                            master_bible=self.app.current_project.master_bible,
                            hud_report=hud_report,
                            purism_prompt=purism_prompt,
                            style_mode=style_guide,
                            feedback=director_feedback,
                            prev_full_manuscript=prev_text,
                            arc_doc=arc_tactical,
                            protagonist_name=self.app._get_protagonist_name()
                        )

                        frozen_manuscript = frozen_result.get('content', '') if isinstance(frozen_result, dict) else str(frozen_result)
                        frozen_title = frozen_result.get('title', f'제{next_ep}화') if isinstance(frozen_result, dict) else f'제{next_ep}화'

                        frozen_judge = self.app.agents['director'].quick_judge_single(
                            ep_num=next_ep,
                            manuscript=frozen_manuscript,
                            blueprint=blueprint,
                            previous_ending=prev_ending,
                            retry_count=3
                        )

                        if frozen_judge.get('verdict') == 'PASS':
                            final_manuscript = frozen_manuscript
                            final_title = frozen_title
                            final_state_updates = frozen_result.get('state_updates', {}) if isinstance(frozen_result, dict) else {}
                            self.app.ui.log(f"   ✅ 냉동인간 PASS (점수: {frozen_judge.get('score', 0)})")
                            self.app.ui.log(f"   ⚠️ [경고] 냉동인간 통과 - 품질 재검토 권장")
                        else:
                            self.app.ui.log(f"   ❌ 냉동인간도 REJECT. 인간 개입 필요!")
                            self.app.ui.log(f"      사유: {frozen_judge.get('reason', '알 수 없음')}")
                            self.app.ui.log(f"\n⛔ [EP {next_ep}] 자동 생산 실패. 인간 검토 필요.")
                            self.app.ui.log(f"   다음 옵션:")
                            self.app.ui.log(f"   1. Blueprint 수정 후 재시도")
                            self.app.ui.log(f"   2. 수동 원고 작성")
                            self.app.ui.log(f"   3. 이 에피소드 건너뛰기")

                            choice = self.app._get_int_input(
                                "\n👉 선택 (1.Blueprint수정 / 2.수동작성 / 3.건너뛰기 / 4.강제진행): ",
                                default=4, min_val=1, max_val=4
                            )

                            if choice == 4:
                                final_manuscript = frozen_manuscript
                                final_title = f"[⚠️ 강제 통과] {frozen_title}"
                                final_state_updates = frozen_result.get('state_updates', {}) if isinstance(frozen_result, dict) else {}
                                self.app.ui.log(f"   ⚠️ 강제 진행 선택됨. 품질 보장 불가.")
                            else:
                                self.app.ui.log(f"   🛑 제{next_ep}화 생산 중단. 메뉴로 돌아갑니다.")
                                return

                    except Exception as frozen_err:
                        self.app.ui.log(f"   🚨 냉동인간 호출 실패: {frozen_err}")
                        self.app.ui.log(f"\n⛔ [EP {next_ep}] 자동 생산 완전 실패. 인간 검토 필요.")
                        return

                # ===== Phase 5: 데이터 정산 =====
                if final_manuscript:
                    self.app.ui.log(f"\n📦 제{next_ep}화 데이터 정산 중...")

                    # HUD 업데이트
                    if final_state_updates and hasattr(self.app.sys, 'hud'):
                        try:
                            approved = self.app.agents['director'].on_approve_workflow(
                                ep_num=next_ep,
                                state_updates=final_state_updates,
                                current_hud=self.app.sys.hud.snapshot() if hasattr(self.app.sys.hud, 'snapshot') else {}
                            )
                            if approved.get('applied_updates'):
                                if hasattr(self.app.sys.hud, 'bulk_update'):
                                    self.app.sys.hud.bulk_update(approved['applied_updates'])
                                    self.app.ui.log(f"   ✅ HUD 업데이트 완료")
                                else:
                                    self.app.sys.hud.update_physical_status(approved['applied_updates'])
                                    self.app.ui.log(f"   ✅ HUD 업데이트 완료 (fallback)")
                        except Exception as hud_err:
                            self.app.ui.log(f"   ⚠️ HUD 업데이트 실패: {hud_err}")

                    # DB 저장
                    try:
                        self.app.current_project.db.save_manuscript(
                            ep_num=next_ep,
                            title=final_title,
                            content=final_manuscript
                        )

                        if final_state_updates:
                            self.app.current_project.db.update_martial_tracker(next_ep, final_state_updates)
                            self.app.ui.log(f"      📊 제 {next_ep}화 15대 지표 트래커 저장 완료")

                        self.app.current_project.db.conn.commit()
                        self.app.ui.log(f"   ✅ DB 저장 완료")
                    except Exception as db_err:
                        self.app.ui.log(f"   🚨 DB 저장 실패: {db_err}")
                        continue

                    # 파일 저장
                    try:
                        file_path = output_dir / f"ep_{next_ep:04d}.txt"
                        file_path.write_text(f"# {final_title}\n\n{final_manuscript}", encoding='utf-8')
                        self.app.ui.log(f"   ✅ 파일 저장: {file_path.name}")
                    except Exception as file_err:
                        self.app.ui.log(f"   ⚠️ 파일 저장 실패: {file_err}")

                    # [V63.3] 벡터 메모리 즉시 저장
                    try:
                        _mem_arc_no = arc_data.get("arc_no") if arc_data else None
                        _mem_event_types = set()
                        _mem_entity_names = set()
                        if arc_data and arc_data.get("state_changes"):
                            _sc = arc_data["state_changes"]
                            if _sc.get("npc_deaths"):
                                _mem_event_types.add("death")
                                for d in _sc["npc_deaths"]:
                                    _mem_entity_names.add(d.get("name", ""))
                            if _sc.get("skill_acquisitions"):
                                _mem_event_types.add("skill")
                                for s in _sc["skill_acquisitions"]:
                                    _mem_entity_names.add(s.get("name", ""))
                            if _sc.get("relationship_changes"):
                                _mem_event_types.add("relationship")
                                for r in _sc["relationship_changes"]:
                                    _mem_entity_names.add(r.get("npc", ""))
                            if _sc.get("major_items"):
                                _mem_event_types.add("item")
                                for i in _sc["major_items"]:
                                    _mem_entity_names.add(i.get("name", ""))
                            if _sc.get("npc_injuries"):
                                _mem_event_types.add("injury")
                            if _sc.get("npc_movements"):
                                _mem_event_types.add("movement")
                            if _sc.get("resolved_plots"):
                                _mem_event_types.add("resolved_plot")
                        _mem_entity_names.discard("")
                        self.app.memory.memorize_v20_episode(
                            ep_num=next_ep,
                            text=final_manuscript,
                            summary=final_title[:100] if final_title else f"제{next_ep}화",
                            causal_links=[],
                            arc_no=_mem_arc_no,
                            event_types=list(_mem_event_types),
                            entity_names=list(_mem_entity_names)
                        )
                        self.app.ui.log(f"   ✅ 벡터 메모리 저장 (arc={_mem_arc_no}, events={_mem_event_types})")
                    except Exception as _mem_err:
                        self.app.ui.log(f"   ⚠️ [V63.3] 벡터 메모리 저장 실패 (비차단): {str(_mem_err)[:60]}")

                    # [V66] 5화 단위 내러티브 요약 생성 (V63.2 10→5 단축)
                    if next_ep % 5 == 0:
                        try:
                            self.app._generate_narrative_summary(next_ep)
                        except Exception as _ns_err:
                            self.app.ui.log(f"   ⚠️ [V63.2] 내러티브 요약 생성 실패: {str(_ns_err)[:60]}")

                    # [V60.87 C] 로그 파일 저장
                    try:
                        logs_dir = os.path.join("projects", self.app.current_project.name, "logs")
                        os.makedirs(logs_dir, exist_ok=True)

                        if V50_MODULES_AVAILABLE and self.app.failure_learner:
                            self.app.failure_learner.save_to_json(os.path.join(logs_dir, "failure_learning.json"))

                        if V50_MODULES_AVAILABLE and self.app.character_voice:
                            try:
                                self.app.character_voice.analyze_manuscript(next_ep, final_manuscript)
                            except Exception:  # [V64.P4] OPTIONAL: voice analysis
                                pass
                            self.app.character_voice.save_to_json(os.path.join(logs_dir, "character_voice.json"))

                        if V50_MODULES_AVAILABLE and self.app.foreshadow_tracker:
                            # [V66] 원고에서 복선 자동 감지
                            try:
                                self.app.foreshadow_tracker.auto_detect_from_manuscript(next_ep, final_manuscript)
                            except Exception:  # [V66] OPTIONAL: foreshadow auto-detect
                                pass
                            self.app.foreshadow_tracker.save_to_json(os.path.join(logs_dir, "foreshadow.json"))

                        self.app.ui.log(f"   💾 [V60.87] 로그 파일 저장 완료")
                    except Exception as log_err:
                        self.app.ui.log(f"   ⚠️ 로그 저장 실패: {log_err}")

                    # ===== [V60.82] Episode Bible 저장 =====
                    try:
                        self.app.ui.log(f"   📖 [V60.82] Manager 정산 시작...")

                        audit = {}
                        try:
                            current_state = self.app.current_project.latest_state if hasattr(self.app.current_project, 'latest_state') else {}
                            if not current_state and hasattr(self.app.sys, 'hud') and self.app.sys.hud:
                                current_state = {'actual_truth': self.app.sys.hud.pro_data}

                            lore_list = []
                            active_seeds = []
                            causal_history = ""

                            if hasattr(self.app.current_project, 'master_bible'):
                                bible_root = self.app.current_project.master_bible.get('MasterBible', self.app.current_project.master_bible)
                                assets = bible_root.get('AssetLibrary', {})
                                lore_list = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])

                            if hasattr(self.app.current_project, 'db'):
                                try:
                                    seeds_data = self.app.current_project.db.load_anchor('active_seeds')
                                    if seeds_data:
                                        active_seeds = seeds_data if isinstance(seeds_data, list) else []
                                except (ValueError, TypeError, json.JSONDecodeError):
                                    pass

                            raw_audit = self.app.agents['manager'].update_state_and_lore_v20(
                                ep_num=next_ep,
                                manuscript=final_manuscript,
                                current_state=current_state,
                                lore_list=lore_list,
                                active_seeds=active_seeds,
                                causal_history=causal_history
                            )

                            if raw_audit and not raw_audit.get('parsing_error'):
                                audit = raw_audit
                                self.app.ui.log(f"      ✅ Manager 정산 완료")
                            else:
                                self.app.ui.log(f"      ⚠️ Manager 파싱 실패, 기본 추출 사용")
                        except Exception as mgr_err:
                            self.app.ui.log(f"      ⚠️ Manager 호출 실패: {str(mgr_err)[:50]}")

                        new_lore = audit.get('new_lore', {}) if isinstance(audit, dict) else {}
                        knowledge_map = audit.get('knowledge_map_updates', {}) if isinstance(audit, dict) else {}
                        recovered = audit.get('recovered_seeds', []) if isinstance(audit, dict) else []
                        state_updates_from_audit = audit.get('state_updates', {}) if isinstance(audit, dict) else {}
                        causal_links = audit.get('causal_links', []) if isinstance(audit, dict) else []

                        actual_truth = state_updates_from_audit.get('actual_truth', {}) if isinstance(state_updates_from_audit, dict) else {}

                        prev_actual = {}
                        if hasattr(self.app.current_project, 'latest_state'):
                            prev_actual = self.app.current_project.latest_state.get('actual_truth', {})

                        prev_equipment = set(prev_actual.get('equipment', []) if isinstance(prev_actual.get('equipment'), list) else [])
                        curr_equipment = set(actual_truth.get('equipment', []) if isinstance(actual_truth.get('equipment'), list) else [])
                        prev_martial = set(prev_actual.get('martial_arts', []) if isinstance(prev_actual.get('martial_arts'), list) else [])
                        curr_martial = set(actual_truth.get('martial_arts', []) if isinstance(actual_truth.get('martial_arts'), list) else [])

                        new_items_from_equip = list(curr_equipment - prev_equipment)
                        lost_items_from_equip = list(prev_equipment - curr_equipment)
                        new_martial_arts = list(curr_martial - prev_martial)

                        key_items = new_lore.get('Key_Items', []) if isinstance(new_lore.get('Key_Items'), list) else []
                        key_item_names = [i.get('name', str(i)) if isinstance(i, dict) else str(i) for i in key_items]

                        key_npcs = new_lore.get('Key_NPCs', []) if isinstance(new_lore.get('Key_NPCs'), list) else []
                        new_npc_names = [npc.get('name', str(npc)) if isinstance(npc, dict) else str(npc) for npc in key_npcs]

                        npc_deaths = []
                        for npc in key_npcs:
                            if isinstance(npc, dict):
                                status = npc.get('NPC_Martial_HUD', {}).get('current_status', '')
                                if '사망' in str(status) or '죽' in str(status) or '절명' in str(status):
                                    npc_deaths.append(npc.get('name', ''))

                        relationship_changes = []
                        if isinstance(knowledge_map, dict):
                            witnesses = knowledge_map.get('new_witnesses', [])
                            misled = knowledge_map.get('new_misled', [])
                            if witnesses:
                                relationship_changes.extend([f"목격: {w}" for w in witnesses if w])
                            if misled:
                                relationship_changes.extend([f"오해: {m}" for m in misled if m])

                        karma_matrix = state_updates_from_audit.get('karma_matrix', [])
                        if isinstance(karma_matrix, list):
                            for karma in karma_matrix:
                                if isinstance(karma, dict) and karma.get('target'):
                                    obs = karma.get('obsession', 0)
                                    val = karma.get('value', 0)
                                    if obs > 50 or val > 50:
                                        relationship_changes.append(f"{karma['target']}: 집착{obs}/오해{val}")

                        reveal_list = []
                        if isinstance(recovered, list):
                            for seed in recovered:
                                if isinstance(seed, dict):
                                    reveal_list.append(seed.get('seed_id', seed.get('description', str(seed))))
                                else:
                                    reveal_list.append(str(seed))

                        all_new_items = list(set(new_items_from_equip + key_item_names + new_martial_arts))

                        bible_delta = {
                            'new_items': all_new_items,
                            'lost_items': lost_items_from_equip,
                            'new_npcs': new_npc_names,
                            'npc_deaths': npc_deaths,
                            'relationship_changes': relationship_changes,
                            'state_changes': actual_truth if actual_truth else final_state_updates,
                            'time_passed': state_updates_from_audit.get('location', ''),
                            'reveals': reveal_list,
                            'causal_links': causal_links,
                            'karma_matrix': karma_matrix,
                            'knowledge_map': knowledge_map
                        }

                        self.app.current_project.db.save_episode_bible(next_ep, bible_delta)

                        if actual_truth or state_updates_from_audit:
                            state_log_data = {
                                'actual_truth': actual_truth if actual_truth else final_state_updates,
                                'karma_matrix': karma_matrix,
                                'knowledge_map': knowledge_map,
                                'public_reputation': state_updates_from_audit.get('public_reputation', {})
                            }
                            try:
                                summary = f"제{next_ep}화 정산: {', '.join(all_new_items[:3]) if all_new_items else '변화없음'}"
                                self.app.current_project.db.save_state_log_with_summary(next_ep, state_log_data, summary)
                            except Exception as state_err:
                                self.app.ui.log(f"      ⚠️ state_logs 저장 실패: {str(state_err)[:30]}")

                        changes_count = len(all_new_items) + len(lost_items_from_equip) + len(new_npc_names) + len(npc_deaths) + len(relationship_changes) + len(reveal_list)
                        if changes_count > 0:
                            self.app.ui.log(f"   📖 Episode Bible 저장: {changes_count}개 변화 기록")
                            if all_new_items:
                                self.app.ui.log(f"      • 신규 아이템/무공: {', '.join(all_new_items[:5])}")
                            if new_npc_names:
                                self.app.ui.log(f"      • 신규/갱신 NPC: {', '.join(new_npc_names[:5])}")
                            if npc_deaths:
                                self.app.ui.log(f"      • NPC 사망: {', '.join(npc_deaths)}")
                            if reveal_list:
                                self.app.ui.log(f"      • 복선 회수: {', '.join(reveal_list[:3])}")
                        else:
                            self.app.ui.log(f"   📖 Episode Bible 저장 완료 (변화 없음)")

                    except Exception as bible_err:
                        self.app.ui.log(f"   ⚠️ Episode Bible 저장 실패 (비차단): {str(bible_err)[:50]}")
                        import traceback
                        traceback.print_exc()

                    self.app.ui.log(f"\n✅ 제{next_ep}화 '{final_title}' 생산 완료! ({len(final_manuscript)}자)")

                    # [V66.1] B-3: 에피소드 완료 시 audit 버퍼 flush
                    self.app._flush_audit_buffer()

                    # [V65] PerfTimer: 에피소드 완료 시 요약 로그
                    try:
                        self.app.perf_timer.log_summary()
                        self.app.perf_timer.reset()
                    except Exception:
                        pass

            # [V62.3] Stage 4 루프 종료
            self.app.ui.log(f"\n{'='*50}")
            self.app.ui.log(f"📋 Stage 4 집필 세션 종료.")
            try:
                input("   ⏎ Enter를 누르면 메뉴로 돌아갑니다...")
            except EOFError:
                pass

            # [V62.3] 벡터 메모리 일괄 동기화
            try:
                self.app.ui.log(f"   🔄 벡터 메모리 일괄 동기화 중...")
                self.app.memory.sync_v20_drafts()
                self.app.ui.log(f"   ✅ 벡터 메모리 동기화 완료")
            except Exception as vec_err:
                self.app.ui.log(f"   ⚠️ 벡터 메모리 동기화 실패 (비차단): {vec_err}")

        except KeyboardInterrupt:
            self.app.ui.log("\n⚠️ 사용자 중단 요청. 저장 후 종료합니다.")
            self.app._flush_audit_buffer()  # [V66.1] B-3
            self.app._safe_commit()
        except Exception as e:
            self.app.ui.log(f"\n🚨 Stage 4 V2 오류: {e}")
            import traceback
            traceback.print_exc()
            self.app._flush_audit_buffer()  # [V66.1] B-3
            self.app._safe_commit()
