"""
[B-1-2] Stage4 Context Builder — 에피소드 컨텍스트 수집 및 프롬프트 조립.
"""

import json
import logging
import re

from modules.core.writer_prompt_builders import (
    build_anti_trope_instructions as _build_anti_trope,
)
from modules.core.writer_prompt_builders import (
    build_justification_guidance as _build_justification,
)
from modules.core.writer_prompt_builders import (
    build_mandatory_context as _build_writer_mandatory_context,
)


class Stage4ContextBuilder:
    """[B-1-2] Stage4 컨텍스트 빌더 전담 모듈."""

    def __init__(self, ctx) -> None:
        self.ctx = ctx

    def load_chain_link_section(self, next_ep: int) -> str:
        """
        [V68] 직전 화의 chain_link를 DB에서 로드하여 프롬프트 주입용 텍스트로 변환.

        1화이거나 직전 chain_link가 없으면 빈 문자열 반환.
        """
        if next_ep <= 1:
            return ""
        try:
            _cl_raw = self.ctx.current_project.db.load_anchor(f"chain_link_{next_ep - 1}")
            if not _cl_raw or not isinstance(_cl_raw, dict):
                return ""
            _cl_data = _cl_raw
            _cl_parts = ["### [V68] 직전 화 연결고리 - 반드시 이어받을 것"]
            if _cl_data.get("cliffhanger"):
                _cl_parts.append(f"- 진행 중 상황: {_cl_data['cliffhanger']}")
            if _cl_data.get("pending_actions"):
                actions = _cl_data["pending_actions"]
                if isinstance(actions, list):
                    _cl_parts.append(f"- 해야 할 행동: {', '.join(str(a) for a in actions)}")
                else:
                    _cl_parts.append(f"- 해야 할 행동: {actions}")
            if _cl_data.get("emotional_state"):
                _cl_parts.append(f"- 감정 상태: {_cl_data['emotional_state']}")
            if _cl_data.get("physical_state") and _cl_data["physical_state"] != "정상":
                _cl_parts.append(f"- 신체 상태: {_cl_data['physical_state']}")
            if _cl_data.get("location"):
                _cl_parts.append(f"- 현재 위치: {_cl_data['location']}")
            if _cl_data.get("time_marker"):
                _cl_parts.append(f"- 작중 시간: {_cl_data['time_marker']}")
            if len(_cl_parts) > 1:
                return "\n".join(_cl_parts)
            return ""
        except Exception as e:
            logging.warning(f"[SilentPass:ContextBuilder] ChainLink 다이제스트 로드 실패: {e!s:.100}")
            return ""

    def build_extended_lookback_digest(self, next_ep: int) -> str:
        """
        [V66] 직전 10화 원고에서 1-2줄 요약 추출 → mandatory_context 주입.
        기존 3화 lookback을 보완하여 중장기 맥락 제공.
        총 1,500자 이내 truncate.

        [V66.1] B-4: 전문 로드 → SQL SUBSTR 발췌 조회로 최적화 (~100KB I/O 제거/ep).
        첫 200자만 사용하므로 DB에서 200자만 가져옴.
        """
        if next_ep <= 3:
            return ""
        try:
            # 직전 10화 (기존 3화 제외 → ep-10 ~ ep-4 범위)
            start_ep = max(1, next_ep - 10)
            end_ep = max(1, next_ep - 3)  # 최근 3화는 기존 lookback이 커버
            # [V66.1] B-4: 발췌 전용 쿼리 (첫 200자만 DB에서 조회)
            manuscripts = self.ctx.current_project.db.get_recent_manuscript_excerpts(
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
                first_para = re.sub(r"\s+", " ", first_para).strip()
                if len(first_para) > 150:
                    first_para = first_para[:147] + "..."
                lines.append(f"[제{ep_num}화] {first_para}")

            if not lines:
                return ""

            digest = "\n".join(lines)
            if len(digest) > 1500:
                digest = digest[:1497] + "..."
            return f"[확장 Lookback: 직전 4~10화 요약]\n{digest}"
        except Exception as e:
            logging.warning(f"[SilentPass:ContextBuilder] 확장 lookback 다이제스트 실패: {e!s:.100}")
            return ""

    def prepare_episode_context(self, next_ep: int, arc_data: dict, chief_writer) -> dict:
        """에피소드별 컨텍스트 데이터 수집 (Arc 메타 + 이전 원고 + HUD + 연결고리)."""
        arc_pos = next_ep - arc_data.get("ep_start", next_ep) + 1
        total_ep_in_arc = arc_data.get("ep_count", 5)
        arc_tactical = arc_data.get("tactical_doc", "")
        if isinstance(arc_tactical, dict):  # [V70] dict 타입 방어
            arc_tactical = json.dumps(arc_tactical, ensure_ascii=False)
        arc_tactical = str(arc_tactical) if arc_tactical else ""

        # 직전 화 원고
        prev_ms_data = self.ctx.current_project.db.get_manuscript(next_ep - 1)
        prev_text = (prev_ms_data.get("content") or "") if prev_ms_data else ""  # [V70] NULL content 방어
        prev_ending = prev_text[-500:] if prev_text else ""

        # [V67] 이전 30화 원고 전문 로드 — Director + ChiefWriter 공유
        _prev_manuscripts_parts = []
        for _prev_ep in range(max(1, next_ep - 30), next_ep):
            try:
                _prev_ms_data = self.ctx.current_project.db.get_manuscript(_prev_ep)
                if _prev_ms_data:
                    _prev_content = (
                        _prev_ms_data.get("content", "") if isinstance(_prev_ms_data, dict) else str(_prev_ms_data)
                    )
                    if _prev_content and len(_prev_content) > 100:
                        _prev_manuscripts_parts.append(f"[제{_prev_ep}화]\n{_prev_content}")
            except Exception as e:
                logging.warning(f"[SilentPass:ContextBuilder] 제{_prev_ep}화 원고 로드 실패: {e!s:.100}")
        _prev_manuscripts_text = "\n\n---\n\n".join(_prev_manuscripts_parts) if _prev_manuscripts_parts else ""
        if _prev_manuscripts_parts:
            logging.info(
                f"📚 [V67] 이전 {len(_prev_manuscripts_parts)}화 원고 전문 로드 완료 ({len(_prev_manuscripts_text):,}자)"
            )

        # [V62.6] 에피소드 상태 다이제스트
        _episode_digest = ""
        if prev_text and hasattr(chief_writer, "_generate_episode_digest"):
            _episode_digest = chief_writer._generate_episode_digest(prev_text, next_ep - 1)

        # HUD 리포트
        hud_report = self.ctx.sys.hud.get_v20_hud_report() if hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud else ""

        # ===== [V60.80 FIX] 미래 침범 방지 데이터 추출 =====
        current_inventory = []
        current_martial_arts = []
        if hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud:
            current_inventory = (
                list(self.ctx.sys.hud.inventory)
                if hasattr(self.ctx.sys.hud, "inventory") and self.ctx.sys.hud.inventory
                else []
            )
            current_martial_arts = (
                list(self.ctx.sys.hud.techniques)
                if hasattr(self.ctx.sys.hud, "techniques") and self.ctx.sys.hud.techniques
                else []
            )

        cumulative_bible = self.ctx.current_project.db.get_cumulative_bible(next_ep - 1)
        dead_npcs = cumulative_bible.get("dead_npcs", []) if cumulative_bible else []

        item_acquisition_timeline = self.ctx.build_item_acquisition_timeline(next_ep - 1)

        # [V68] 직전 화 연결고리 로드
        _chain_link_section = self.load_chain_link_section(next_ep)
        if _chain_link_section:
            logging.info(f"[V68] 직전 화 연결고리 로드 완료 ({len(_chain_link_section)}자)")

        # [V68] 세계 상태 요약 로드 (ChiefWriter 프롬프트 주입용)
        _world_state_summary = ""
        if self.ctx.world_state:
            try:
                _world_state_summary = self.ctx.world_state.get_summary(max_chars=5000)
            except Exception as e:
                logging.warning(f"[SilentPass:ContextBuilder] WorldState 요약 로드 실패: {e!s:.100}")

        return {
            "arc_pos": arc_pos,
            "total_ep_in_arc": total_ep_in_arc,
            "arc_tactical": arc_tactical,
            "prev_text": prev_text,
            "prev_ending": prev_ending,
            "prev_manuscripts_text": _prev_manuscripts_text,
            "episode_digest": _episode_digest,
            "hud_report": hud_report,
            "current_inventory": current_inventory,
            "current_martial_arts": current_martial_arts,
            "cumulative_bible": cumulative_bible,
            "dead_npcs": dead_npcs,
            "item_acquisition_timeline": item_acquisition_timeline,
            "chain_link_section": _chain_link_section,
            "world_state_summary": _world_state_summary,
        }

    def build_mandatory_context(
        self,
        *,
        next_ep: int,
        arc_data: dict,
        arc_tactical: str,
        prev_text: str,
        prev_ending: str,
        hud_report: str,
        writer_agent,
        anchor_sys,
        s4_genre_type: str,
        v50_modules_available: bool,
        pacing_analyzer=None,
    ) -> dict:
        """[4-R1-b] mandatory_context + writer prompt 조립을 분리 (동작 변화 없음)."""
        reference_anchor_prompt = ""
        mandatory_context = ""
        anti_trope_prompt = ""
        justification_prompt = ""
        reflexion_prompt = ""
        genre_name = (getattr(self.ctx.current_project, "genre", None) or {}).get("name", "무협")

        if writer_agent is None:
            return {
                "reference_anchor_prompt": reference_anchor_prompt,
                "mandatory_context": mandatory_context,
                "anti_trope_prompt": anti_trope_prompt,
                "justification_prompt": justification_prompt,
                "reflexion_prompt": reflexion_prompt,
            }

        try:
            relevant_anchors = anchor_sys.get_relevant_anchors(
                current_ep_num=next_ep,
                arc_context=arc_tactical or "",
                n_anchors=5,
            )
            critical_anchors = anchor_sys.get_critical_anchors(
                current_ep_num=next_ep,
                anchor_types=["item", "injury", "power", "location"],
            )
            if relevant_anchors or critical_anchors:
                reference_anchor_prompt = anchor_sys.generate_reference_prompt(
                    relevant_anchors=relevant_anchors,
                    critical_anchors=critical_anchors,
                )
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ ReferenceAnchor 로드 실패 (비치명): {e}")

        try:
            _db = getattr(self.ctx.current_project, "db", None)
            _bible = getattr(self.ctx.current_project, "master_bible", {})
            mandatory_context = _build_writer_mandatory_context(_db, _bible, next_ep)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Mandatory Context 실패 (비치명): {e}")
            mandatory_context = (
                "[경고] 필수 컨텍스트 로딩 실패 - 이전 에피소드 상태를 우선 참조하여 연속성을 유지하세요."
            )

        _mc_parts = [mandatory_context] if mandatory_context else []

        _arc_cs = arc_data.get("constraint_summary", "") if arc_data else ""
        if _arc_cs:
            _mc_parts.append(f"[Arc 제약 - MUST NOT DO]\n{_arc_cs}")

        if self.ctx.world_state:
            try:
                _ws_summary = self.ctx.world_state.get_summary(max_chars=5000)
                if _ws_summary:
                    _mc_parts.insert(0, _ws_summary)
                    logging.info(f"🌍 [V68] 세계 상태 문서 주입 ({len(_ws_summary)}자)")
            except Exception as _ws_err:
                logging.warning(f"⚠️ [V68] 세계 상태 문서 주입 실패 (비치명): {str(_ws_err)[:50]}")

        try:
            _series_summary = self.ctx.current_project.load_v20_anchor("series_summary")
            if _series_summary:
                if isinstance(_series_summary, dict):
                    _series_summary = _series_summary.get("summary", "") or str(_series_summary)
                if _series_summary and len(str(_series_summary)) > 10:
                    _mc_parts.append(f"[V68 시리즈 전체 요약]\n{_series_summary}")

            _current_arc_no = arc_data.get("arc_no", 1) if arc_data else 1
            _current_vol = max(1, (_current_arc_no - 1) // 5 + 1)  # ARCS_PER_VOLUME = 5
            _volume_summaries = []
            for _vi in range(max(1, _current_vol - 2), _current_vol + 1):
                _vs = self.ctx.current_project.load_v20_anchor(f"volume_summary_{_vi}")
                if _vs:
                    if isinstance(_vs, dict):
                        _vs = _vs.get("summary", "") or str(_vs)
                    if _vs and len(str(_vs)) > 10:
                        _volume_summaries.append(f"[볼륨 {_vi}] {_vs}")
            if _volume_summaries:
                _mc_parts.append("[V68 볼륨 요약]\n" + "\n".join(_volume_summaries))
        except Exception as _hier_err:
            self.ctx.ui.log(f"   ⚠️ [V68] 계층형 요약 로드 실패 (비치명): {str(_hier_err)[:60]}")

        if self.ctx.fact_ledger:
            try:
                _fl_summary = self.ctx.fact_ledger.to_summary(max_chars=15000)
                if _fl_summary:
                    _mc_parts.insert(0, _fl_summary)
                    logging.info(f"📋 [V68] 팩트 원장 주입 ({len(_fl_summary)}자)")
            except Exception as _fl_mc_err:
                logging.warning(f"⚠️ [V68] 팩트 원장 주입 실패 (비치명): {str(_fl_mc_err)[:50]}")

        if self.ctx.state_tracker:
            _destroyed = self.ctx.state_tracker.get_entity_destruction_summary()
            if _destroyed:
                _mc_parts.append(_destroyed)

        if self.ctx.state_tracker:
            _resolved = self.ctx.state_tracker.get_resolved_plots_summary()
            if _resolved:
                _mc_parts.append(_resolved)

        if self.ctx.state_tracker:
            _personality = self.ctx.state_tracker.get_npc_personality_summary()
            if _personality:
                _mc_parts.append(_personality)

        if self.ctx.state_tracker:
            _npc_rel = self.ctx.state_tracker.get_npc_npc_relationship_summary()
            if _npc_rel:
                _mc_parts.append(_npc_rel)

        if self.ctx.state_tracker:
            _perm_inj = self.ctx.state_tracker.get_permanent_injury_summary()
            if _perm_inj:
                _mc_parts.append(_perm_inj)

        if self.ctx.state_tracker:
            _timeline = self.ctx.state_tracker.get_time_timeline_summary()
            if _timeline:
                _mc_parts.append(_timeline)

        if self.ctx.state_tracker:
            _companions = self.ctx.state_tracker.get_companion_summary()
            if _companions:
                _mc_parts.append(_companions)

        if self.ctx.state_tracker:
            _commitments = self.ctx.state_tracker.get_commitment_summary()
            if _commitments:
                _mc_parts.append(_commitments)

        if self.ctx.state_tracker:
            _emotion = self.ctx.state_tracker.get_protagonist_emotion_summary()
            if _emotion:
                _mc_parts.append(_emotion)

        if self.ctx.state_tracker:
            _item_state = self.ctx.state_tracker.get_item_state_summary()
            if _item_state:
                _mc_parts.append(_item_state)

        if self.ctx.state_tracker:
            _plot_suspension = self.ctx.state_tracker.get_plot_suspension_summary(
                arc_data.get("arc_no", 0) if arc_data else 0
            )
            if _plot_suspension:
                _mc_parts.append(_plot_suspension)

        if self.ctx.state_tracker:
            _dialogue_style = self.ctx.state_tracker.get_npc_dialogue_style_summary()
            if _dialogue_style:
                _mc_parts.append(_dialogue_style)

        if self.ctx.state_tracker:
            _rel_summary = self.ctx.state_tracker.get_relationship_changes_summary()
            if _rel_summary:
                _mc_parts.append(_rel_summary)

        if self.ctx.state_tracker:
            _injury_summary = self.ctx.state_tracker.get_npc_injury_summary()
            if _injury_summary:
                _mc_parts.append(_injury_summary)

        if self.ctx.state_tracker:
            _movement_summary = self.ctx.state_tracker.get_npc_movement_summary()
            if _movement_summary:
                _mc_parts.append(_movement_summary)

        if self.ctx.state_tracker:
            _skills_summary = self.ctx.state_tracker.get_protagonist_skills_summary()
            if _skills_summary:
                _mc_parts.append(_skills_summary)

        try:
            arc_summaries = []
            current_arc_no = arc_data.get("arc_no", 1) if arc_data else 1
            for prev_arc in range(max(1, current_arc_no - 3), current_arc_no):
                arc_sum = self.ctx.current_project.load_v20_anchor(f"arc_summary_{prev_arc}")
                if arc_sum and isinstance(arc_sum, dict):
                    arc_summaries.append(arc_sum)
            if arc_summaries and self.ctx.state_tracker:
                _arc_summary_text = self.ctx.state_tracker.format_arc_summary_for_prompt(arc_summaries)
                if _arc_summary_text:
                    _mc_parts.append(_arc_summary_text)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ [V66] Arc 요약 주입 실패 (비치명): {e}")

        if s4_genre_type == "investment" and self.ctx.state_tracker is not None:
            _fin_summary = self.ctx.state_tracker.get_financial_state_summary()
            if _fin_summary:
                _mc_parts.append(_fin_summary)

        try:
            if self.ctx.memory and prev_ending:
                _mq_queries = [prev_ending]
                if arc_data and arc_data.get("state_changes"):
                    _sc = arc_data["state_changes"]
                    _npc_names = []
                    for _field in ["npc_deaths", "relationship_changes", "npc_injuries"]:
                        for _entry in _sc.get(_field) or []:
                            # [Sweep54] string 엔트리 대응 (stage4_post_processor가 npc_deaths를 str로 생성)
                            if isinstance(_entry, dict):
                                _n = _entry.get("name") or _entry.get("npc", "")
                            elif isinstance(_entry, str):
                                _n = _entry
                            else:
                                continue
                            if _n:
                                _npc_names.append(_n)
                    if _npc_names:
                        _mq_queries.append(" ".join(_npc_names[:5]))
                if arc_tactical and len(arc_tactical) > 50:
                    _mq_queries.append(arc_tactical[:300])
                _genre_queries = {
                    "hunter": ["던전 클리어 각성 스킬 랭크"],
                    "investment": ["포트폴리오 거래 수익률 투자"],
                    "fantasy": ["마법 축복 주문 마나 정령"],
                }
                if s4_genre_type in _genre_queries:
                    _mq_queries.extend(_genre_queries[s4_genre_type])
                _vector_memory = self.ctx.memory.retrieve_multi_query_context(
                    queries=_mq_queries,
                    current_ep=next_ep,
                    n_per_query=3,
                    max_results=5,
                )
                if _vector_memory:
                    _mc_parts.append(f"[과거 유사 맥락 (벡터 검색)]\n{_vector_memory}")
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ 벡터 검색 실패 (비치명): {e}")

        try:
            _ext_lookback = self.build_extended_lookback_digest(next_ep)
            if _ext_lookback:
                _mc_parts.append(_ext_lookback)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ 확장 Lookback 실패 (비치명): {e}")

        try:
            if v50_modules_available and self.ctx.foreshadow_tracker:
                _foreshadow_prompt = self.ctx.foreshadow_tracker.generate_writer_prompt(next_ep)
                if _foreshadow_prompt:
                    _mc_parts.append(_foreshadow_prompt)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ ForeshadowTracker 프롬프트 실패 (비치명): {e}")

        if self.ctx.semantic_plot_guard:
            try:
                tactical_text = arc_data.get("tactical_doc", "") if arc_data else ""
                if isinstance(tactical_text, dict):
                    tactical_text = str(tactical_text)
                _spg_warnings = self.ctx.semantic_plot_guard.check_new_arc(tactical_doc=tactical_text)
                if _spg_warnings:
                    _spg_text = self.ctx.semantic_plot_guard.format_warnings(_spg_warnings)
                    if _spg_text:
                        _mc_parts.append(_spg_text)
            except Exception as e:
                logging.warning(f"[SilentPass:ContextBuilder] SemanticPlotGuard 경고 주입 실패: {e!s:.100}")

        if pacing_analyzer and prev_text and len(prev_text) >= 100:
            try:
                _pacing_result = pacing_analyzer.analyze(prev_text)
                _pacing_prompt = pacing_analyzer.generate_pacing_prompt(_pacing_result)
                if _pacing_prompt:
                    _mc_parts.append(_pacing_prompt)
            except Exception as _pace_err:
                self.ctx.ui.log(f"   ⚠️ [V65] 페이싱 분석 실패 (비치명): {str(_pace_err)[:60]}")

        try:
            _narrative_summaries = self.ctx.load_narrative_summaries()
            if _narrative_summaries:
                _mc_parts.append(_narrative_summaries)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ [V64.P4] 내러티브 요약 로드 실패 (비치명): {str(e)[:60]}")

        mandatory_context = "\n\n".join(_mc_parts)

        try:
            anti_trope_prompt = _build_anti_trope(genre_name)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Anti-Trope 실패 (비치명): {e}")

        try:
            justification_prompt = _build_justification(hud_report, genre_name)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Justification 실패 (비치명): {e}")

        try:
            if next_ep >= 20:
                from modules.core.reflexion_manager import ReflexionManager

                reflexion = ReflexionManager(self.ctx.current_project)
                reflexion_prompt = reflexion.get_prompt_injection(min_frequency=2)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Reflexion 실패 (비치명): {e}")

        return {
            "reference_anchor_prompt": reference_anchor_prompt,
            "mandatory_context": mandatory_context,
            "anti_trope_prompt": anti_trope_prompt,
            "justification_prompt": justification_prompt,
            "reflexion_prompt": reflexion_prompt,
        }

    def build_round_context(
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
        purism_prompt: str,
        genre_name: str,
        npc_equipment_summary: str,
        effective_anti_trope: str,
        intro_dna: str,
        story_context: str,
        style_guide: str,
        mandatory_context: str,
    ):
        """[4-R1-e-2] Build round context dict from episode context and prompts."""
        from modules.core.stage4_orchestrator import _RoundContext

        return _RoundContext(
            chief_writer=chief_writer,
            manuscript_validator=manuscript_validator,
            consistency_validator=consistency_validator,
            blocking_validator=blocking_validator,
            continuity_validator=continuity_validator,
            next_ep=next_ep,
            blueprint=blueprint,
            arc_data=arc_data,
            arc_pos=ep_ctx["arc_pos"],
            total_ep_in_arc=ep_ctx["total_ep_in_arc"],
            arc_tactical=ep_ctx["arc_tactical"],
            prev_text=ep_ctx["prev_text"],
            prev_ending=ep_ctx["prev_ending"],
            prev_manuscripts_text=ep_ctx["prev_manuscripts_text"],
            episode_digest=ep_ctx["episode_digest"],
            hud_report=ep_ctx["hud_report"],
            current_inventory=ep_ctx["current_inventory"],
            current_martial_arts=ep_ctx["current_martial_arts"],
            dead_npcs=ep_ctx["dead_npcs"],
            item_acquisition_timeline=ep_ctx["item_acquisition_timeline"],
            chain_link_section=ep_ctx["chain_link_section"],
            world_state_summary=ep_ctx["world_state_summary"],
            purism_prompt=purism_prompt,
            genre_name=genre_name,
            npc_equipment_summary=npc_equipment_summary,
            effective_anti_trope=effective_anti_trope,
            intro_dna=intro_dna,
            story_context=story_context,
            style_guide=style_guide,
            reference_anchor_prompt=ctx_prompts["reference_anchor_prompt"],
            mandatory_context=mandatory_context,
            justification_prompt=ctx_prompts["justification_prompt"],
            reflexion_prompt=ctx_prompts["reflexion_prompt"],
        )
