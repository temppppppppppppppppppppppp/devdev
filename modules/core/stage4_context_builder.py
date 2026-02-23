"""
[B-1-2] Stage4 Context Builder — 에피소드 컨텍스트 수집 및 프롬프트 조립.
"""

import json
import logging
import re
from typing import TYPE_CHECKING

from modules.core.context_advisor import RetrievalSources
from modules.core.context_compression import ContextCompressor
from modules.core.writer_prompt_builders import (
    build_anti_trope_instructions as _build_anti_trope,
)
from modules.core.writer_prompt_builders import (
    build_justification_guidance as _build_justification,
)
from modules.core.writer_prompt_builders import (
    build_mandatory_context as _build_writer_mandatory_context,
)
from modules.validation.threshold_helper import _threshold

if TYPE_CHECKING:
    from modules.core.context_advisor import RetrievalPlan


class Stage4ContextBuilder:
    """[B-1-2] Stage4 컨텍스트 빌더 전담 모듈."""

    def __init__(self, ctx) -> None:
        self.ctx = ctx

    @staticmethod
    def _extract_npc_tokens(query: str) -> list[str]:
        """Extract candidate NPC tokens from retrieval query text."""
        if not query:
            return []

        stopwords = {
            "npc",
            "history",
            "context",
            "consistency",
            "query",
            "past",
            "state",
            "change",
            "relation",
            "event",
            "continuity",
            "appear",
            "verify",
            # [TF7-P1-02] 한국어 일반어 — NPC 코어 슬롯 오점유 방지
            "등장",
            "과거",
            "행적",
            "관계",
            "상태",
            "내용",
            "정보",
            "히스토리",
            "배경",
            "이야기",
            "설명",
            "기록",
            "요약",
            "분석",
            "추적",
        }
        tokens: list[str] = []
        for token in re.split(r"[\s,|/:;()\[\]{}]+", str(query)):
            text = token.strip()
            if len(text) < 2:
                continue
            if text.lower() in stopwords:
                continue
            if text not in tokens:
                tokens.append(text)
        return tokens[:20]

    @staticmethod
    def _collect_npc_roster(arc_data: dict, blueprint: dict | None = None) -> list[str]:
        """Collect NPC candidates from arc state_changes and blueprint hints."""
        names: list[str] = []
        state_changes = (arc_data or {}).get("state_changes", {}) if isinstance(arc_data, dict) else {}

        for field in ("npc_deaths", "relationship_changes", "npc_injuries"):
            for entry in state_changes.get(field) or []:
                if isinstance(entry, dict):
                    candidates = [
                        entry.get("name"),
                        entry.get("npc"),
                        entry.get("source"),
                        entry.get("target"),
                        entry.get("npc_name"),
                    ]
                    for cand in candidates:
                        text = str(cand or "").strip()
                        if text and text not in names:
                            names.append(text)
                elif isinstance(entry, str):
                    text = entry.strip()
                    if text and text not in names:
                        names.append(text)

        bp = blueprint or {}
        scene_blocks = bp.get("scene_breakdown") or bp.get("scenes") or []
        if isinstance(scene_blocks, dict):
            scene_blocks = list(scene_blocks.values())
        if isinstance(scene_blocks, list):
            for scene in scene_blocks:
                if not isinstance(scene, dict):
                    continue
                for key in ("npcs", "characters", "participants"):
                    raw = scene.get(key)
                    if isinstance(raw, list):
                        for item in raw:
                            text = str(item or "").strip()
                            if text and text not in names:
                                names.append(text)
                    elif isinstance(raw, str):
                        for item in re.split(r"[,\n/|]+", raw):
                            text = item.strip()
                            if text and text not in names:
                                names.append(text)

        for key in ("npc_roster", "key_npcs", "characters"):
            raw = bp.get(key)
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        text = str(item.get("name") or item.get("npc") or "").strip()
                    else:
                        text = str(item or "").strip()
                    if text and text not in names:
                        names.append(text)

        return names[:50]

    def _execute_retrieval_plan(self, plan: "RetrievalPlan", arc_no: int | None = None) -> list[str]:
        """Execute retrieval plan slots and return context sections."""
        memory = getattr(self.ctx, "memory", None)
        if not memory or not plan or not getattr(plan, "slots", None):
            return []

        sections: list[str] = []
        compressor = ContextCompressor()
        max_results = int(_threshold("context.vector_max_results_s4", 16))
        current_arc_no = arc_no
        ordered_slots = sorted(plan.slots, key=lambda slot: getattr(slot, "priority", 2))

        for slot in ordered_slots:
            _VM = RetrievalSources.VEC_MEMORY
            source = str(getattr(slot, "source", _VM) or _VM)
            query_text = str(getattr(slot, "query", "") or "").strip()
            if not query_text:
                continue

            try:
                if source == RetrievalSources.DB_NPC_HISTORY:
                    npc_tokens = self._extract_npc_tokens(query_text)
                    result = memory.retrieve_npc_context(
                        npc_names=npc_tokens,
                        current_ep=plan.episode_num,
                        max_results=max_results,
                    )
                else:
                    # [Hybrid-P4] retrieval_mode 플래그 기반 경로 분기
                    _retrieval_mode = _threshold("smart_retrieval.retrieval_mode", "dense")
                    if _retrieval_mode == "hybrid" and hasattr(memory, "retrieve_hybrid_context"):
                        result = memory.retrieve_hybrid_context(
                            query=query_text,
                            current_ep=plan.episode_num,
                            dense_k=int(_threshold("smart_retrieval.dense_k", 10)),
                            sparse_k=int(_threshold("smart_retrieval.sparse_k", 10)),
                            max_results=max_results,
                            current_arc_no=current_arc_no,
                            rrf_k=int(_threshold("smart_retrieval.rrf_k", 60)),
                        )
                    elif _retrieval_mode == "sparse" and hasattr(memory, "_fts_search"):
                        _fts = memory._fts_search(query_text, plan.episode_num, n_results=max_results)
                        result = (
                            "\n\n".join(f"=== EP {r['ep_num']} [sparse] ===\n{r['summary']}" for r in _fts)
                            if _fts
                            else ""
                        )
                    else:
                        if _retrieval_mode not in ("dense", "hybrid", "sparse"):
                            logging.warning(
                                "[Retrieval] 알 수 없는 retrieval_mode '%s', dense로 폴백",
                                _retrieval_mode,
                            )
                        result = memory.retrieve_multi_query_context(
                            queries=[query_text],
                            current_ep=plan.episode_num,
                            n_per_query=3,
                            max_results=max_results,
                            current_arc_no=current_arc_no,
                        )
            except Exception as e:
                self.ctx.ui.log(f"   [SC] retrieval slot failed ({source}/{slot.category}): {str(e)[:80]}")
                continue

            if not result:
                continue

            slot_max = int(getattr(slot, "max_chars", 0) or 0)
            if slot_max > 0 and len(result) > slot_max:
                result = compressor._smart_trim(result, slot_max)

            sections.append(f"[SC:{slot.category}]\n{result}")

        logging.info(f"[SC] stage4 retrieval: {len(sections)} sections from {len(plan.slots)} slots")
        return sections

    def _apply_context_budget(self, sections: list[str], total_budget_chars: int) -> list[str]:
        """Track section-level budget usage and trim large sections when over budget."""
        if not sections:
            return sections

        if total_budget_chars <= 0:
            total_budget_chars = int(_threshold("smart_retrieval.stage4_total_budget", 50000))
        if total_budget_chars <= 0:
            return sections

        from modules.core.context_advisor import ContextBudgetTracker

        def _build_tracker(values: list[str]) -> ContextBudgetTracker:
            tracker = ContextBudgetTracker(total_budget_chars=total_budget_chars)
            for idx, content in enumerate(values, start=1):
                tracker.register_section(f"section_{idx}", content)
            return tracker

        tracker = _build_tracker(sections)
        report = tracker.get_usage_report()
        logging.info(
            f"[SC] Context budget: {report['used_chars']}/{report['total_budget_chars']} ({report['usage_pct']}%)"
        )

        if report["used_chars"] <= report["total_budget_chars"]:
            return sections

        # [S4-P1-6] 압축 대상 목록을 루프 전 1회 캐시하여 O(n^2) → O(n) 개선
        compression_targets = tracker.get_compression_targets()
        compressor = ContextCompressor()
        for target in compression_targets:
            try:
                idx = int(target.split("_")[-1]) - 1
            except (TypeError, ValueError):
                continue
            if idx < 0 or idx >= len(sections):
                continue

            section = sections[idx]
            if len(section) <= 300:
                continue

            trim_target = max(300, int(len(section) * 0.7))
            sections[idx] = compressor._smart_trim(section, trim_target)

            # 총 사용량만 빠르게 체크 (tracker 재생성 대신 합산)
            _used = sum(len(s) for s in sections)
            if _used <= total_budget_chars:
                break

        # 최종 보고용 tracker 1회 재생성
        tracker = _build_tracker(sections)
        report = tracker.get_usage_report()
        logging.info(
            f"[SC] Context budget: {report['used_chars']}/{report['total_budget_chars']} ({report['usage_pct']}%)"
        )
        return sections

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
            _excerpt_max = _threshold("context.lookback_excerpt_chars", 500)
            manuscripts = self.ctx.current_project.db.get_recent_manuscript_excerpts(
                before_ep=next_ep, limit=10, max_chars=_excerpt_max
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
                paragraphs = content.split("\n\n")
                first_para = "\n\n".join(paragraphs[:2]) if len(paragraphs) > 1 else content[:_excerpt_max]
                # 줄바꿈 정리
                first_para = re.sub(r"\s+", " ", first_para).strip()
                if len(first_para) > _excerpt_max:
                    first_para = first_para[: _excerpt_max - 3] + "..."
                lines.append(f"[제{ep_num}화] {first_para}")

            if not lines:
                return ""

            digest = "\n".join(lines)
            _total_max = _threshold("context.lookback_total_chars", 4000)
            if len(digest) > _total_max:
                digest = digest[: _total_max - 3] + "..."
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

        _db = self.ctx.current_project.db
        _prev_manuscripts_parts: list[str] = []

        # [Tier4-12] Tier 1: recent 10 episodes full text
        _tier1_start = max(1, next_ep - 10)
        _tier1_rows: list[dict] = []
        try:
            if hasattr(_db, "get_manuscripts_range"):
                _tier1_rows = _db.get_manuscripts_range(_tier1_start, next_ep) or []
            else:
                for _prev_ep in range(_tier1_start, next_ep):
                    _row = _db.get_manuscript(_prev_ep)
                    if _row:
                        _tier1_rows.append(
                            {
                                "ep_num": _prev_ep,
                                "content": _row.get("content", "") if isinstance(_row, dict) else str(_row),
                            }
                        )
        except Exception as e:
            logging.warning(f"[SilentPass:Tier4-12] tier1 full-text load failed: {e!s:.100}")
            _tier1_rows = []

        for _row in _tier1_rows:
            _ep_no = int(_row.get("ep_num", 0) or 0)
            _content = str(_row.get("content", "") or "")
            if _content and len(_content) > 100:
                _prev_manuscripts_parts.append(f"[EP {_ep_no}]\n{_content}")

        # [Tier4-12] Tier 2: summaries for episodes 11~30 before current
        _tier2_start = max(1, next_ep - 30)
        _tier2_end = _tier1_start
        if _tier2_end > _tier2_start:
            _tier2_parts: list[str] = []
            try:
                if hasattr(_db, "_lock") and hasattr(_db, "cursor"):
                    with _db._lock:
                        _cur = _db.cursor.execute(
                            "SELECT ep_num, summary FROM episode_meta "
                            "WHERE ep_num >= ? AND ep_num < ? ORDER BY ep_num ASC",
                            (_tier2_start, _tier2_end),
                        )
                        _rows = _cur.fetchall()
                else:
                    _rows = []

                for _row in _rows:
                    if isinstance(_row, dict):
                        _ep_no = int(_row.get("ep_num", 0) or 0)
                        _summary = str(_row.get("summary", "") or "")
                    else:
                        _ep_no = int(_row["ep_num"] or 0)
                        _summary = str(_row["summary"] or "")
                    if _summary:
                        _tier2_parts.append(f"[EP {_ep_no} summary] {_summary[:500]}")
            except Exception as e:
                logging.warning(f"[SilentPass:Tier4-12] tier2 summary load failed: {e!s:.100}")

            if _tier2_parts:
                _prev_manuscripts_parts.insert(
                    0, "-- Tier2 summaries (11-30 episodes back) --\n" + "\n".join(_tier2_parts)
                )

        # [Tier4-12] Tier 3: older arc summaries
        if _tier2_start > 1:
            _tier3_parts: list[str] = []
            try:
                _arcs = _db.load_anchor("arcs") or []
            except Exception:
                _arcs = []

            for _idx, _arc in enumerate(_arcs):
                if not isinstance(_arc, dict):
                    continue
                _arc_no = int(_arc.get("arc_no", _idx + 1) or (_idx + 1))
                _arc_eps = _arc.get("episodes", [])
                if not isinstance(_arc_eps, list) or not _arc_eps:
                    continue

                _arc_max_ep = 0
                for _ep in _arc_eps:
                    if isinstance(_ep, int):
                        _arc_max_ep = max(_arc_max_ep, _ep)
                    elif isinstance(_ep, dict):
                        _cand = _ep.get("ep_num") or _ep.get("episode") or _ep.get("ep") or 0
                        try:
                            _arc_max_ep = max(_arc_max_ep, int(_cand))
                        except (TypeError, ValueError):
                            continue
                if _arc_max_ep >= _tier2_start:
                    continue

                try:
                    _arc_sum = self.ctx.current_project.load_v20_anchor(f"arc_summary_{_arc_no}")
                    if not _arc_sum:
                        continue
                    if isinstance(_arc_sum, dict):
                        _sum_text = str(_arc_sum.get("summary", _arc_sum) or "")
                    else:
                        _sum_text = str(_arc_sum)
                    if _sum_text:
                        _tier3_parts.append(f"[Arc {_arc_no} summary] {_sum_text[:1000]}")
                except Exception:
                    continue

            if _tier3_parts:
                _prev_manuscripts_parts.insert(
                    0,
                    "-- Tier3 arc summaries (older than 30 episodes) --\n" + "\n".join(_tier3_parts),
                )

        _prev_manuscripts_text = "\n\n---\n\n".join(_prev_manuscripts_parts) if _prev_manuscripts_parts else ""
        if _prev_manuscripts_parts:
            logging.info(
                "[Tier4-12] hybrid lookback ready: parts=%d chars=%d",
                len(_prev_manuscripts_parts),
                len(_prev_manuscripts_text),
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

        # [S4-P2-6] dead_npcs만 필요하지만 개별 쿼리 없음 — DBManager 내부 캐시(_cumulative_bible_cache)로 반복 로드 무비용
        cumulative_bible = self.ctx.current_project.db.get_cumulative_bible(next_ep - 1)
        dead_npcs = cumulative_bible.get("dead_npcs", []) if cumulative_bible else []
        if isinstance(dead_npcs, str):
            dead_npcs = [dead_npcs]  # LLM이 단일 문자열 반환 시 리스트화

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
        blueprint: dict | None = None,
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

        # [S4-I2] state_tracker 16종 요약을 get_all_summaries()로 일괄 수집
        _st = self.ctx.state_tracker
        if _st:
            _arc_no_for_st = arc_data.get("arc_no", 0) if arc_data else 0
            try:
                _all_summaries = _st.get_all_summaries(
                    arc_no=_arc_no_for_st,
                    genre=s4_genre_type,
                )
                for _summary in _all_summaries.values():
                    if _summary:
                        _mc_parts.append(_summary)
            except Exception as _st_err:
                logging.warning("[S4-I2] get_all_summaries 실패, 개별 폴백: %s", _st_err)
                # 폴백: 개별 호출 (하위 호환성 보장)
                for _summary in (
                    _st.get_entity_destruction_summary(),
                    _st.get_resolved_plots_summary(),
                    _st.get_npc_personality_summary(),
                    _st.get_npc_npc_relationship_summary(),
                    _st.get_permanent_injury_summary(),
                    _st.get_time_timeline_summary(),
                    _st.get_companion_summary(),
                    _st.get_commitment_summary(),
                    _st.get_protagonist_emotion_summary(),
                    _st.get_item_state_summary(),
                    _st.get_plot_suspension_summary(_arc_no_for_st),
                    _st.get_npc_dialogue_style_summary(),
                    _st.get_relationship_changes_summary(),
                    _st.get_npc_injury_summary(),
                    _st.get_npc_movement_summary(),
                    _st.get_protagonist_skills_summary(),
                ):
                    if _summary:
                        _mc_parts.append(_summary)

        try:
            arc_summaries = []
            current_arc_no = arc_data.get("arc_no", 1) if arc_data else 1
            for prev_arc in range(max(1, current_arc_no - 3), current_arc_no):
                arc_sum = self.ctx.current_project.load_v20_anchor(f"arc_summary_{prev_arc}")
                if arc_sum and isinstance(arc_sum, dict):
                    arc_summaries.append(arc_sum)
            if arc_summaries and _st:
                _arc_summary_text = _st.format_arc_summary_for_prompt(arc_summaries)
                if _arc_summary_text:
                    _mc_parts.append(_arc_summary_text)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ [V66] Arc 요약 주입 실패 (비치명): {e}")

        _retrieval_plan = None
        try:
            if self.ctx.memory and prev_ending:
                _use_advisor_path = False
                _advisor = getattr(self.ctx, "context_advisor", None)
                _smart_enabled = bool(_threshold("smart_retrieval.enabled", False)) and bool(
                    _threshold("smart_retrieval.stage4_enabled", False)
                )
                if _advisor and _smart_enabled:
                    _arc_ep_start = arc_data.get("ep_start", next_ep) if arc_data else next_ep
                    _arc_ep_count = arc_data.get("ep_count", 0) if arc_data else 0
                    _arc_pos = next_ep - _arc_ep_start + 1
                    _is_arc_boundary = _arc_pos <= 1 or (_arc_ep_count > 0 and _arc_pos >= _arc_ep_count)
                    _npc_roster = self._collect_npc_roster(arc_data=arc_data, blueprint=blueprint)
                    _retrieval_plan = _advisor.plan_stage4_retrieval(
                        arc_data=arc_data or {},
                        blueprint=blueprint or {},
                        prev_ending=prev_ending,
                        current_ep=next_ep,
                        npc_roster=_npc_roster,
                        genre=s4_genre_type,
                        is_arc_boundary=_is_arc_boundary,
                        is_reject_retry=False,
                    )
                    _perf_key = f"sc_stage4_ep{next_ep}_retrieval"
                    try:
                        self.ctx.perf_timer.start(_perf_key)
                    except Exception as _e:
                        logging.debug("[Stage4ContextBuilder] perf_timer SC start 실패 (무시): %s", _e)
                    try:
                        _arc_no_s4 = arc_data.get("arc_no", None) if arc_data else None
                        for _retrieved in self._execute_retrieval_plan(_retrieval_plan, arc_no=_arc_no_s4):
                            _mc_parts.append(_retrieved)
                    finally:
                        try:
                            self.ctx.perf_timer.stop(_perf_key)
                        except Exception as _e:
                            logging.debug("[Stage4ContextBuilder] perf_timer SC stop 실패 (무시): %s", _e)
                    _use_advisor_path = True

                _mq_queries = [] if _use_advisor_path else [prev_ending]
                if (not _use_advisor_path) and arc_data and arc_data.get("state_changes"):
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
                if (not _use_advisor_path) and arc_tactical and len(arc_tactical) > 50:
                    _mq_queries.append(arc_tactical[:600])
                _genre_queries = {
                    "hunter": ["던전 클리어 각성 스킬 랭크"],
                    "investment": ["포트폴리오 거래 수익률 투자"],
                    "fantasy": ["마법 축복 주문 마나 정령"],
                }
                if (not _use_advisor_path) and s4_genre_type in _genre_queries:
                    _mq_queries.extend(_genre_queries[s4_genre_type])
                if _mq_queries:
                    _vector_memory = self.ctx.memory.retrieve_multi_query_context(
                        queries=_mq_queries,
                        current_ep=next_ep,
                        n_per_query=3,
                        max_results=_threshold("context.vector_max_results_s4", 16),
                        current_arc_no=current_arc_no,
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

        _sc_budget = int(getattr(_retrieval_plan, "total_budget_chars", 0) or 0)
        # [TF7-P1-03] SC 비활성 시 비-SC 필수 문맥이 절삭되지 않도록 양쪽 플래그 모두 확인
        if _threshold("smart_retrieval.enabled", False) and _threshold("smart_retrieval.stage4_enabled", False):
            _mc_parts = self._apply_context_budget(_mc_parts, _sc_budget)

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
        from modules.core.stage4_types import _RoundContext

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
