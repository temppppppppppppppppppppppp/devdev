"""[B-1-8] Stage2 preflight analysis extracted from Stage2Orchestrator."""

import concurrent.futures
import json
import logging
import re
import threading

from modules.core.constants import smart_truncate
from modules.core.context_advisor import RetrievalSources
from modules.core.fact_ledger import summarize_fact_ledger_numbers_block
from modules.core.project_support import build_style_guide_summary
from modules.core.semantic_query_broker import SemanticQueryBroker
from modules.validation.threshold_helper import _threshold


class Stage2PreflightAnalysis:
    """State setup, arc analysis, and enrichment for Stage 2 preflight."""

    def __init__(self, host) -> None:
        self.host = host

    @property
    def ctx(self):
        return self.host.ctx

    @staticmethod
    def _extract_npc_tokens(query: str) -> list[str]:
        """Extract candidate NPC tokens from retrieval query text."""
        if not query:
            return []

        stopwords = {
            "npc",
            "history",
            "context",
            "query",
            "past",
            "state",
            "change",
            "relation",
            "event",
            "continuity",
            "recent",
            "block",
            "theme",
            "arc",
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
    def _collect_npc_roster(enriched_block: dict | None) -> list[str]:
        """Collect NPC candidates from Stage2 enriched block."""
        if not isinstance(enriched_block, dict):
            return []

        names: list[str] = []

        def _add_name(value) -> None:
            text = str(value or "").strip()
            if text and text not in names:
                names.append(text)

        def _consume(raw) -> None:
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        for key in ("name", "npc", "source", "target", "npc_name", "character"):
                            if item.get(key):
                                _add_name(item.get(key))
                    else:
                        _add_name(item)
            elif isinstance(raw, dict):
                for key in ("name", "npc", "source", "target", "npc_name", "character"):
                    if raw.get(key):
                        _add_name(raw.get(key))
            elif isinstance(raw, str):
                for part in re.split(r"[,\n/|]+", raw):
                    _add_name(part)

        for key in ("npc_roster", "assigned_npcs", "key_npcs", "characters", "npcs"):
            _consume(enriched_block.get(key))

        for container_key in ("state_changes", "status_shadow", "joint_docs"):
            container = enriched_block.get(container_key)
            if not isinstance(container, dict):
                continue
            for key in ("npc_deaths", "relationship_changes", "npc_injuries", "npcs", "characters"):
                _consume(container.get(key))

        return names[:50]

    @staticmethod
    def _build_stage3_to_2_reverse_feedback_fallback(
        arc_stage3_failures: list[dict],
        global_arc_no: int,
        *,
        status: str,
    ) -> str:
        reason_counts = {}
        detail_lines = []
        for failure in arc_stage3_failures:
            reason = str(failure.get("reason", "사유 미상") or "사유 미상")[:120]
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            issue = str(failure.get("specific_issue", "") or "").strip()
            if issue and issue not in detail_lines:
                detail_lines.append(issue[:120])

        lines = [
            "",
            "=" * 50,
            f"[V60.9 Arc {global_arc_no} Blueprint 반복 실패 - fallback]",
            "=" * 50,
            f"Stage3->2 reverse feedback helper 상태: {status}",
            f"Blueprint 설계 실패 {len(arc_stage3_failures)}회 누적.",
            "다음 Arc 재시도에서는 아래 실패 사유를 직접 구조 제약으로 승격하세요.",
        ]
        for reason, count in sorted(reason_counts.items(), key=lambda item: (-item[1], item[0]))[:3]:
            lines.append(f"  - {reason}: {count}회")
        if detail_lines:
            lines.append("")
            lines.append("반복된 구체 지시:")
            for issue in detail_lines[:3]:
                lines.append(f"  - {issue}")
        lines.extend(
            [
                "",
                "권장 조치:",
                "  1. 핵심 갈등 축을 줄여 Blueprint 의존성을 단순화할 것",
                "  2. 아이템/NPC 배치 시점을 명시해 설정 충돌을 줄일 것",
                "  3. 직전 실패 사유가 반복된 장면은 Arc 구조에서 제거 또는 재배치할 것",
                "",
                "=" * 50,
                "",
            ]
        )
        return "\n".join(lines)

    def _execute_stage2_retrieval_plan(
        self,
        plan,
        *,
        current_ep: int,
        npc_roster: list[str] | None = None,
        current_arc_no: int | None = None,
        protagonist_name: str = "",
    ) -> str:
        """Execute Stage2 retrieval plan and return merged context text."""
        memory = getattr(self.ctx, "memory", None)
        if not memory or not plan or not getattr(plan, "slots", None):
            return ""

        max_results = int(_threshold("context.vector_max_results_s2", 40))
        sections: list[str] = []
        ordered_slots = sorted(plan.slots, key=lambda slot: getattr(slot, "priority", 2))
        _VM = RetrievalSources.VEC_MEMORY
        vec_slot_count = sum(1 for slot in ordered_slots if str(getattr(slot, "source", _VM) or _VM) == _VM)
        fallback_names = [str(name).strip() for name in (npc_roster or []) if str(name).strip()]

        for slot in ordered_slots:
            source = str(getattr(slot, "source", _VM) or _VM)
            category = str(getattr(slot, "category", "context") or "context")
            query_text = str(getattr(slot, "query", "") or "").strip()
            if not query_text:
                continue

            try:
                if source == RetrievalSources.DB_NPC_HISTORY:
                    npc_names = fallback_names or self._extract_npc_tokens(query_text)
                    result = memory.retrieve_npc_context(
                        npc_names=npc_names,
                        current_ep=current_ep,
                        max_results=max_results,
                    )
                elif source == RetrievalSources.DB_NPC_RELATIONSHIP:
                    npc_names = fallback_names or self._extract_npc_tokens(query_text)
                    result = self._build_relationship_context(
                        npc_names=npc_names,
                        protagonist_name=protagonist_name,
                    )
                else:
                    # [Hybrid-P4] retrieval_mode 플래그 기반 경로 분기
                    _retrieval_mode = _threshold("smart_retrieval.retrieval_mode", "dense")
                    if _retrieval_mode == "hybrid" and hasattr(memory, "retrieve_hybrid_context"):
                        result = memory.retrieve_hybrid_context(
                            query=query_text,
                            current_ep=current_ep,
                            dense_k=int(_threshold("smart_retrieval.dense_k", 10)),
                            sparse_k=int(_threshold("smart_retrieval.sparse_k", 10)),
                            max_results=max_results,
                            current_arc_no=current_arc_no,
                            rrf_k=int(_threshold("smart_retrieval.rrf_k", 60)),
                        )
                    elif _retrieval_mode == "sparse" and hasattr(memory, "_fts_search"):
                        _fts = memory._fts_search(query_text, current_ep, n_results=max_results)
                        result = (
                            "\n\n".join(f"=== EP {r['ep_num']} [sparse] ===\n{r['summary']}" for r in _fts)
                            if _fts
                            else ""
                        )
                    elif vec_slot_count <= 1:
                        result = memory.retrieve_high_res_context(
                            query_text,
                            current_ep,
                            n_results=max_results,
                        )
                    else:
                        if _retrieval_mode not in ("dense", "hybrid", "sparse"):
                            logging.warning("[Retrieval] 알 수 없는 retrieval_mode '%s', dense로 폴백",
                                _retrieval_mode,
                            )
                        result = memory.retrieve_multi_query_context(
                            queries=[query_text],
                            current_ep=current_ep,
                            n_per_query=3,
                            max_results=max_results,
                            current_arc_no=current_arc_no,
                        )
            except Exception as exc:  # OPTIONAL: retrieval failure should not block generation
                audit_cb = getattr(self.ctx, "audit_event", None)
                if callable(audit_cb):
                    audit_cb("s2_vector_search_failed", str(exc)[:100])
                continue

            if not result:
                continue

            slot_max = int(getattr(slot, "max_chars", 0) or 0)
            if slot_max > 0 and len(result) > slot_max:
                result = result[:slot_max]

            sections.append(f"[SC:{category}]\n{result}")

        logging.info(f"[SC] stage2 retrieval: {len(sections)} sections from {len(plan.slots)} slots")
        joined = "\n\n".join(sections)
        budget = int(getattr(plan, "total_budget_chars", 0) or 0)
        if budget > 0 and len(joined) > budget:
            joined = joined[:budget]
            logging.info(f"[SC] stage2 budget truncation → {budget}자")
        return joined

    def _build_relationship_context(
        self,
        *,
        npc_names: list[str],
        protagonist_name: str = "",
        limit: int = 6,
    ) -> str:
        db = getattr(getattr(self.ctx, "current_project", None), "db", None)
        if not db or not hasattr(db, "get_relationship_history"):
            return ""

        clean_names = [str(name).strip() for name in (npc_names or []) if str(name).strip()]
        if protagonist_name:
            protagonist_name = str(protagonist_name).strip()

        seen: set[tuple[str, str]] = set()
        lines: list[str] = []

        def _add_pair(n1: str, n2: str) -> None:
            if not n1 or not n2 or n1 == n2:
                return
            pair = tuple(sorted((n1, n2)))
            if pair in seen:
                return
            seen.add(pair)
            try:
                rows = db.get_relationship_history(pair[0], pair[1], limit=3)
            except Exception as rel_err:
                logging.debug("[Stage2Preflight] relationship history 조회 실패 (비치명): %s", rel_err)
                rows = []
            if not rows:
                return
            for row in rows[:2]:
                if not isinstance(row, dict):
                    continue
                old_relation = str(row.get("old_relation", "") or "").strip()
                new_relation = str(row.get("new_relation", "") or "").strip()
                change_ep = row.get("change_ep", "?")
                transition = " -> ".join(part for part in (old_relation, new_relation) if part)
                if transition:
                    lines.append(f"EP{change_ep} {pair[0]}-{pair[1]}: {transition}")

        if protagonist_name:
            for name in clean_names[:5]:
                _add_pair(protagonist_name, name)
        for idx, name in enumerate(clean_names[:4]):
            for other in clean_names[idx + 1 : idx + 4]:
                _add_pair(name, other)

        return "\n".join(lines[:limit])

    @staticmethod
    def _summarize_retrieval_sources(plan) -> dict[str, int]:
        counts: dict[str, int] = {}
        if not plan or not getattr(plan, "slots", None):
            return counts
        for slot in getattr(plan, "slots", []) or []:
            source = str(getattr(slot, "source", RetrievalSources.VEC_MEMORY) or RetrievalSources.VEC_MEMORY)
            counts[source] = counts.get(source, 0) + 1
        return counts

    def _record_retrieval_observation(self, *, ep_num: int, stage: str, observation: dict) -> None:
        dashboard = getattr(self.ctx, "quality_dashboard", None)
        if dashboard is None or not hasattr(dashboard, "record_retrieval_observation"):
            return
        try:
            dashboard.record_retrieval_observation(ep_num=ep_num, stage=stage, observation=observation)
        except Exception as exc:
            logging.debug("[Stage2Preflight] retrieval observation record failed: %s", exc)

    def _build_fact_ledger_context(self, *, max_items: int = 10) -> str:
        """Stage 2 Arc 생성기에 전달할 핵심 수치 요약."""
        try:
            db = getattr(getattr(self.ctx, "current_project", None), "db", None)
            if not db:
                return ""
            ledger = db.load_anchor("fact_ledger")
            return summarize_fact_ledger_numbers_block(
                ledger,
                header="[팩트 원장 핵심 수치]",
                max_items=max_items,
            )
        except Exception as fact_err:
            logging.debug("[TF-DB-B1] Stage2 FactLedger 요약 실패 (비치명): %s", fact_err)
            return ""

    def _build_style_guide_summary(self, *, max_chars: int = 1200) -> str:
        """Stage 2 Analyst용 compact StyleGuide 요약."""
        project = getattr(self.ctx, "current_project", None)
        return build_style_guide_summary(
            project,
            heading="[문체 가이드 요약]",
            max_chars=max_chars,
            include_dialogue_ratio=True,
            secondary_style_key="description_style",
            secondary_style_label="묘사",
        )

    def _build_protagonist_config_summary(self) -> str:
        """Stage 2 enhanced_context 상단용 compact protagonist_config 요약."""
        project = getattr(self.ctx, "current_project", None)
        if project is None:
            return ""

        master_bible = getattr(project, "master_bible", None)
        if not isinstance(master_bible, dict):
            return ""

        bible_root = master_bible.get("MasterBible", master_bible)
        protagonist_config = bible_root.get("protagonist_config", {}) if isinstance(bible_root, dict) else {}
        if not isinstance(protagonist_config, dict) or not protagonist_config:
            return ""

        world_origin = str(protagonist_config.get("world_origin", "") or "").strip()
        incarnation_type = str(protagonist_config.get("incarnation_type", "") or "").strip()
        pov = str(protagonist_config.get("pov", "") or "").strip()
        external_pov_insert_policy = str(protagonist_config.get("external_pov_insert_policy", "") or "").strip()

        if not any([world_origin, incarnation_type, pov, external_pov_insert_policy]):
            return ""

        lines = ["[주인공 설정 요약]"]
        parts = []
        if world_origin:
            parts.append(f"세계 출신={world_origin}")
        if incarnation_type:
            parts.append(f"환생 유형={incarnation_type}")
        if pov:
            parts.append(f"시점={pov}")
        if external_pov_insert_policy:
            parts.append(f"외부 시점 삽입={external_pov_insert_policy}")
        if parts:
            lines.append("- " + ", ".join(parts))
        if pov == "1인칭":
            lines.append("- 1인칭 유지: 주인공 부재 장면/타인 내면 직서술 금지")
        elif pov == "3인칭":
            lines.append("- 3인칭 유지: 주인공 중심 시점, 전지적 개입 최소화")

        return "\n".join(lines)

    def _compose_work_focus_text(self, enriched_block: dict | None, *, current_vol_strategy: dict | None = None) -> str:
        if not isinstance(enriched_block, dict):
            return ""

        parts: list[str] = []
        for key in ("block_theme", "tactical_doc", "arc_tactical", "constraint_summary"):
            value = str(enriched_block.get(key, "") or "").strip()
            if value:
                parts.append(value)

        plot_suspension = enriched_block.get("plot_suspension", []) or []
        if isinstance(plot_suspension, list) and plot_suspension:
            parts.append(" ".join(str(item).strip() for item in plot_suspension[:4] if str(item).strip()))

        npc_roster = self._collect_npc_roster(enriched_block)
        if npc_roster:
            parts.append(" ".join(npc_roster[:8]))

        for container_key in ("joint_docs", "status_shadow"):
            container = enriched_block.get(container_key)
            if not isinstance(container, dict):
                continue
            for key in ("constraint_summary", "core_conflict", "status_summary", "active_threads"):
                value = container.get(key)
                if isinstance(value, list):
                    text = " ".join(str(item).strip() for item in value[:4] if str(item).strip())
                else:
                    text = str(value or "").strip()
                if text:
                    parts.append(text)

        if isinstance(current_vol_strategy, dict):
            strategy_doc = str(current_vol_strategy.get("strategy_doc", "") or "").strip()
            if strategy_doc:
                parts.append(strategy_doc[:400])

        combined = "\n".join(part for part in parts if part)
        return combined[:1800]

    def _resolve_work_retrieval_focus(
        self,
        enriched_block: dict | None,
        *,
        current_vol_strategy: dict | None = None,
    ) -> dict[str, object]:
        guard = getattr(getattr(self.ctx, "sys", None), "guard", None)
        if not guard or not hasattr(guard, "select_retrieval_focus"):
            return {}

        focus_text = self._compose_work_focus_text(enriched_block, current_vol_strategy=current_vol_strategy)
        if not focus_text:
            return {}

        try:
            focus = guard.select_retrieval_focus(stage="block", focus_text=focus_text)
        except Exception as focus_err:
            logging.debug("[Stage2Preflight] work_focus 선택 실패 (비치명): %s", focus_err)
            return {}

        return focus if isinstance(focus, dict) else {}

    def _build_work_identity_slot_summary(
        self,
        focus: dict[str, object],
        enriched_block: dict | None,
        *,
        protagonist_name: str = "",
        max_chars: int = 1200,
    ) -> str:
        if not isinstance(focus, dict) or not focus:
            return ""

        tracking_slots = [str(item).strip() for item in (focus.get("tracking_slots") or []) if str(item).strip()]
        scene_engines = [
            str(item).strip() for item in (focus.get("mandatory_scene_engines") or []) if str(item).strip()
        ]
        registry_profiles = [
            item for item in (focus.get("registry_profiles") or []) if isinstance(item, dict)
        ]

        if not any([tracking_slots, scene_engines, registry_profiles]):
            return ""

        lines = ["[작품 추적 슬롯 요약]"]
        if tracking_slots:
            lines.append(f"- 이번 블록 우선 tracking_slots: {', '.join(tracking_slots[:3])}")
        if scene_engines:
            lines.append(f"- 이번 블록 scene engines: {', '.join(scene_engines[:2])}")
        if registry_profiles:
            rendered_profiles = []
            for profile in registry_profiles[:2]:
                name = str(profile.get('name', '') or '').strip()
                fields = [str(item).strip() for item in (profile.get("required_fields") or []) if str(item).strip()]
                if not name:
                    continue
                rendered_profiles.append(name + (f"(fields={', '.join(fields[:4])})" if fields else ""))
            if rendered_profiles:
                lines.append(f"- registry focus: {', '.join(rendered_profiles)}")

        if isinstance(enriched_block, dict):
            block_theme = str(enriched_block.get("block_theme", "") or "").strip()
            if block_theme:
                lines.append(f"- 현재 블록 중심축: {block_theme[:140]}")
            constraint_summary = str(enriched_block.get("constraint_summary", "") or "").strip()
            if constraint_summary:
                lines.append(f"- 갈등 요약: {constraint_summary[:160]}")

        try:
            focus_text = " ".join(
                [
                    ", ".join(tracking_slots),
                    ", ".join(scene_engines),
                    " ".join(str(profile.get("purpose", "") or "") for profile in registry_profiles),
                    str((enriched_block or {}).get("constraint_summary", "") or ""),
                    str((enriched_block or {}).get("block_theme", "") or ""),
                ]
            ).strip()
            broker = SemanticQueryBroker(
                db=getattr(getattr(self.ctx, "current_project", None), "db", None),
                world_state=getattr(self.ctx, "world_state", None),
                fact_ledger=getattr(self.ctx, "fact_ledger", None),
                state_tracker=getattr(self.ctx, "state_tracker", None),
                protagonist_name=protagonist_name,
            )
            relation_slice = broker.build_relation_slice(focus_text=focus_text, max_chars=420)
            if relation_slice:
                lines.append(relation_slice)
        except Exception as broker_err:
            logging.debug("[Stage2Preflight] semantic relation slice 생성 실패 (비치명): %s", broker_err)

        return smart_truncate("\n".join(lines), max_chars=max_chars, head_chars=max_chars // 2)

    def _preflight_state_setup(
        self,
        *,
        all_refined_arcs: list,
        arcs_source: list,
        arc_idx: int,
        lack_report: dict,
        grand_obj: str,
        global_arc_no: int,
        constraint_db,
        genre: str = "",
    ) -> dict:
        """[4-R3-a] Pre-attempt-loop state initialization.

        Computes arc_drive, preflight analysis (parallel), constraint block,
        and initializes attempt loop variables.

        Returns dict of computed values for the attempt loop.
        """
        ### [V66.1] arc_drive + preflight 병렬 실행 (ThreadPoolExecutor)
        # arc_drive: LLM 호출 (lack_report 의존, lack_report는 위에서 즉시 완료)
        # preflight: LLM 호출 (독립적 — all_refined_arcs만 사용)
        # 두 호출이 독립적이므로 병렬 실행하여 15-30s 절감

        # [S2-P1-5] perf_timer 공유 상태 보호용 Lock
        _perf_lock = threading.Lock()

        def _compute_arc_drive() -> dict:
            """Weaver 욕망 드라이브 생성 (LLM)"""
            try:
                with _perf_lock:
                    self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_arc_drive")
            except Exception as _e:
                logging.debug("[Stage2Preflight] perf_timer arc_drive start 실패 (무시): %s", _e)
            try:
                return self.ctx.agents["weaver"].generate_arc_drive(
                    current_arc_dna=arcs_source[arc_idx],
                    analyst_lack_report=lack_report,
                    grand_objective=grand_obj,
                )
            except Exception as weaver_err:
                logging.warning("[Weaver] 욕망 드라이브 생성 실패: %s", weaver_err)
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event(
                        "weaver_error",
                        "generate_arc_drive failed",
                        {"arc_no": global_arc_no, "error": str(weaver_err)},
                    )
                return {"desire_vector": "생성 실패", "status": "error"}
            finally:
                try:
                    with _perf_lock:
                        self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_arc_drive")
                except Exception as _e:
                    logging.debug("[Stage2Preflight] perf_timer arc_drive stop 실패 (무시): %s", _e)

        def _compute_preflight() -> tuple:
            """Preflight 분석 (LLM) — 결과를 attempt 루프에서 재사용"""
            try:
                with _perf_lock:
                    self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_preflight_analysis")
            except Exception as _e:
                logging.debug("[Stage2Preflight] perf_timer preflight start 실패 (무시): %s", _e)
            _pf_injection = ""
            _pf_result = None
            try:
                if "preflight" in self.ctx.agents and all_refined_arcs:
                    try:
                        _resolved_plots = ""
                        if self.ctx.state_tracker:
                            _resolved_plots = self.ctx.state_tracker.get_resolved_plots_summary()
                        _pf_result = self.ctx.agents["preflight"].analyze(
                            all_refined_arcs, resolved_plots_summary=_resolved_plots
                        )
                        if _pf_result:
                            # LLM이 서사에서 추론한 부상은 신뢰 불가.
                            # arc_end_state.injuries (공식 DB 값)로 강제 덮어씀.
                            _last_arc = all_refined_arcs[-1]
                            _actual_injuries = (
                                _last_arc.get("state_constraints", {}).get("arc_end_state", {}).get("injuries")
                                or "없음"
                            )
                            _ws = _pf_result.setdefault("world_state", {})
                            _ps = _ws.setdefault("protagonist_status", {})
                            _ps["injuries"] = _actual_injuries
                            _pf_injection = self.ctx.agents["preflight"].generate_analyst_injection(
                                _pf_result, genre=genre
                            )
                    except Exception as pf_err:
                        logging.warning(f" [Preflight] 스킵: {str(pf_err)[:50]}")
                return _pf_injection, _pf_result
            finally:
                try:
                    with _perf_lock:
                        self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_preflight_analysis")
                except Exception as _e:
                    logging.debug("[Stage2Preflight] perf_timer preflight stop 실패 (무시): %s", _e)

        # [S2-I1] constraint_db 수집을 arc_drive/preflight와 병렬 실행
        def _compute_constraint_block() -> str:
            """ConstraintDB 제약 블록 생성 (독립 — LLM 미사용)"""
            try:
                return constraint_db.generate_constraint_block(global_arc_no) or ""
            except Exception as _cb_err:
                logging.warning(f"[S2-I1] constraint_block 생성 실패 (비차단): {_cb_err}")
                return ""

        # [Phase 3-Obs] PerfTimer: preflight 병렬 구간 외곽 타이머
        try:
            self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_preflight_parallel")
        except Exception as _e:
            logging.debug("[Stage2Preflight] perf_timer parallel start 실패 (무시): %s", _e)
        arc_drive = {}
        _cached_preflight_injection = ""
        _cached_preflight_result = {}
        constraint_block = ""
        _parallel_exec = None
        self.ctx.ui.log("      ⏳ [Preflight] 병렬 분석 시작 (arc_drive + preflight + constraint)...")
        try:
            _parallel_exec = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            _fut_drive = _parallel_exec.submit(_compute_arc_drive)
            _fut_preflight = _parallel_exec.submit(_compute_preflight)
            _fut_constraint = _parallel_exec.submit(_compute_constraint_block)
            # [P1-B3] 개별 try/except — 부분 타임아웃 시에도 다른 결과 수거
            try:
                arc_drive = _fut_drive.result(timeout=300)
                self.ctx.ui.log("      ✅ [Preflight] arc_drive 완료")
            except Exception as _drv_err:
                logging.warning("[Preflight] arc_drive 타임아웃/실패: %s", str(_drv_err)[:80])
                self.ctx.ui.log("      ⚠️ [Preflight] arc_drive 실패")
            try:
                _cached_preflight_injection, _cached_preflight_result = _fut_preflight.result(timeout=300)
                self.ctx.ui.log("      ✅ [Preflight] preflight 완료")
            except Exception as _pf_err2:
                logging.warning("[Preflight] preflight 타임아웃/실패: %s", str(_pf_err2)[:80])
                self.ctx.ui.log("      ⚠️ [Preflight] preflight 실패")
            try:
                constraint_block = _fut_constraint.result(timeout=60)
                self.ctx.ui.log("      ✅ [Preflight] constraint 완료")
            except Exception as _con_err:
                logging.warning("[Preflight] constraint 타임아웃/실패: %s", str(_con_err)[:80])
                self.ctx.ui.log("      ⚠️ [Preflight] constraint 실패")
        except Exception as _pf_err:
            if _parallel_exec is not None:
                try:
                    _parallel_exec.shutdown(wait=False, cancel_futures=True)
                except Exception as _e:
                    logging.debug("[Stage2Preflight] executor shutdown(err path) 실패 (무시): %s", _e)
            logging.warning(f" [Preflight] 병렬 실행 타임아웃/오류 (비치명): {str(_pf_err)[:80]}")
        finally:
            if _parallel_exec is not None:
                try:
                    _parallel_exec.shutdown(wait=False, cancel_futures=True)
                except Exception as _e:
                    logging.debug("[Stage2Preflight] executor shutdown(finally) 실패 (무시): %s", _e)
            try:
                self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_preflight_parallel")
            except Exception as _e:
                logging.debug("[Stage2Preflight] perf_timer parallel stop 실패 (무시): %s", _e)

        if _cached_preflight_result:
            logging.info("✅ [V66.1] arc_drive + preflight + constraint 병렬 완료")
            logging.info(f"- 아이템 타임라인: {len(_cached_preflight_result.get('item_timeline', []))}개")
            logging.info(f"- 금지 사항: {len(_cached_preflight_result.get('absolute_prohibitions', []))}개")
            logging.info(f"- 관계 맵: {len(_cached_preflight_result.get('relationship_map', {}))}명")

        passed = False
        current_feedback = ""

        # [S2-I1] constraint_block 로깅 (병렬 결과)
        if constraint_block:
            self.ctx.ui.log(f"      🔒 [V49.4] Arc {global_arc_no} 제약 조건 주입됨")

        # [V60.11] ConstraintCompiler로 구조화된 체크리스트 생성
        if self.ctx.constraint_compiler and all_refined_arcs:
            try:
                state_result = None
                if "state_extractor" in self.ctx.agents:
                    try:
                        arc_count = len(all_refined_arcs)
                        if (
                            self.ctx.cumulative_state_cache is not None
                            and self.ctx.cumulative_state_cache_key == arc_count
                        ):
                            state_result = self.ctx.cumulative_state_cache
                        else:
                            self.ctx.ui.log("      ⏳ [StateExtractor] 누적 상태 추출 중...")
                            state_result = self.ctx.agents["state_extractor"].extract_cumulative_state(all_refined_arcs)
                            self.ctx.ui.log("      ✅ [StateExtractor] 누적 상태 추출 완료")
                            self.ctx.cumulative_state_cache = state_result
                            self.ctx.cumulative_state_cache_key = arc_count
                            # [Sweep3-D2][Sweep300-R1] app 캐시 키+객체 동기화
                            if self.ctx.sync_cache_key_to_app:
                                self.ctx.sync_cache_key_to_app(arc_count, cache=state_result)
                    except Exception as e:  # [V64.P4] CRITICAL: state extraction failure → NPC validation disabled
                        logging.warning(f"[V64.P4] CRITICAL: extract_cumulative_state 실패 (NPC 검증 약화): {e}",
                            exc_info=True,
                        )
                        self.ctx.ui.log(
                            f"      ⚠️ [V64.P4] extract_cumulative_state 실패 (NPC 검증 약화): {str(e)[:80]}"
                        )
                        if callable(getattr(self.ctx, "audit_event", None)):
                            self.ctx.audit_event("critical_state_extraction_failed", str(e)[:200])

                _resolved = getattr(self.ctx.state_tracker, "resolved_plots", []) if self.ctx.state_tracker else []
                compiled_constraints = self.ctx.constraint_compiler.compile(
                    all_refined_arcs, state_result, resolved_plots=_resolved
                )
                constraint_block = compiled_constraints + "\n\n" + (constraint_block or "")
                self.ctx.ui.log("      📋 [V60.11] ConstraintCompiler 체크리스트 생성 완료")

                # [V66] SemanticPlotGuard — 중앙 인스턴스 사용
                if _resolved and len(_resolved) >= 2 and self.ctx.semantic_plot_guard:
                    try:
                        self.ctx.semantic_plot_guard.index_resolved_plots(_resolved)
                    except Exception as e:  # [V64.P4] SPG init — OPTIONAL
                        if callable(getattr(self.ctx, "audit_event", None)):
                            self.ctx.audit_event("semantic_plot_guard_index_failed", str(e)[:100])
            except Exception as cc_err:
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event("v60_11_constraint_compiler_error", str(cc_err)[:100])

        # [V60.77] FourPhase-Director 대면 루프
        attempt = 0
        max_attempts = int(_threshold("retry.analyst_max_attempts", 5))
        director_feedback_for_fourphase = ""

        _st_snapshot = None  # [V70] StateTracker 롤백용 스냅샷

        return {
            "arc_drive": arc_drive,
            "cached_preflight_injection": _cached_preflight_injection,
            "cached_preflight_result": _cached_preflight_result,
            "passed": passed,
            "current_feedback": current_feedback,
            "constraint_block": constraint_block,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "st_snapshot": _st_snapshot,
        }

    def _preflight_arc_analysis(
        self,
        *,
        attempt: int,
        current_feedback: str,
        constraint_block: str,
        last_refined_context: str,
        all_refined_arcs: list,
        protagonist_name: str,
        global_arc_no: int,
        cached_preflight_injection: str,
        cached_preflight_result,
    ) -> dict:
        """[4-R3-b] Per-attempt context building and weapons preparation.

        Builds enhanced_context (constraints, optimizer, V51, focus mode,
        stage 3->2 feedback) and prepares analyst weapons (preflight cache,
        constraint compiler, entity registry).

        Returns dict of analysis results for the generation phase.
        """
        from modules.core.constants import Emojis, RetryLimits
        from modules.core.spinners import V50_MODULES_AVAILABLE

        self.ctx.ui.log(
            f"   {Emojis.BRAIN} [Arc {global_arc_no}] 전술 설계 중 (시도 {attempt + 1}/{RetryLimits.ANALYST_MAX_ATTEMPTS})..."
        )

        # [Phase 3-QR] 품질 추세 요약 주입 (advisory)
        _quality_trend_block = ""
        if self.ctx.quality_dashboard:
            try:
                _trend = self.ctx.quality_dashboard.get_score_trend_summary(stage=2)
                if _trend.get("trend") != "insufficient_data" and _trend.get("summary"):
                    _quality_trend_block = f"\n[품질 추세 참고]\n{_trend['summary']}\n"
            except Exception as _qr_e:
                logging.debug("[S2-QR] 품질 추세 수집 실패 (비차단): %s", _qr_e)  # [TF-S2PE-07]

        # [V49.4] 제약 블록을 prev_arc_context에 주입
        enhanced_context = last_refined_context
        if _quality_trend_block:
            enhanced_context = _quality_trend_block + enhanced_context
        _context_headers: list[str] = []
        _style_guide_block = self._build_style_guide_summary()
        if _style_guide_block:
            _context_headers.append(_style_guide_block)
        _protagonist_block = self._build_protagonist_config_summary()
        if _protagonist_block:
            _context_headers.append(_protagonist_block)
        if _context_headers:
            enhanced_context = "\n\n".join(_context_headers) + "\n\n" + enhanced_context
        # [LM-G] 서사 구조 컨텍스트 주입 (advisory)
        _narrative_enriched = False  # [TF-3T-A] orchestrator 추적용
        try:
            from modules.core.narrative_context_formatter import NarrativeContextFormatter

            _st = self.ctx.state_tracker
            _npc_motivations = {}
            if _st and hasattr(_st, "npc_registry"):
                for _npc_name, _npc_info in list((_st.npc_registry or {}).items())[:50]:  # [TF-39] P2-2
                    if isinstance(_npc_info, dict):
                        _mot = _npc_info.get("primary_motivation", "")
                        if _mot:
                            _npc_motivations[_npc_name] = _mot

            # [LM-Tier TF-F] 누적 경과 시간 조회
            _cumulative_elapsed = None
            try:
                _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
                if _db:
                    _ws_anchor = _db.load_anchor("world_state")
                    if _ws_anchor and isinstance(_ws_anchor, dict):
                        _cumulative_elapsed = _ws_anchor.get("cumulative_elapsed")
            except Exception as _cum_err:
                logging.debug("[TF-F] cumulative_elapsed 조회 실패 (비치명): %s", _cum_err)
            _narrative_ctx = NarrativeContextFormatter.format_all(
                active_plots=getattr(_st, "active_plots", None) if _st else None,
                npc_motivations=_npc_motivations,
                pending_commitments=getattr(_st, "pending_commitments", None) if _st else None,
                all_refined_arcs=all_refined_arcs,
                current_arc_no=global_arc_no,
                cumulative_elapsed=_cumulative_elapsed,
            )
            if _narrative_ctx:
                enhanced_context = _narrative_ctx + "\n\n" + enhanced_context
                _narrative_enriched = True  # [TF-3T-A]
                if attempt == 0:
                    self.ctx.ui.log("      📖 [LM-G] 서사 구조 컨텍스트 주입 완료")
        except Exception as _lmg_err:
            logging.warning("[LM-G] NarrativeContextFormatter 실패 (비치명): %s", str(_lmg_err)[:80])

        _fact_ledger_block = self._build_fact_ledger_context(max_items=10)
        if _fact_ledger_block:
            enhanced_context = _fact_ledger_block + "\n\n" + enhanced_context

        if constraint_block:
            enhanced_context = constraint_block + "\n" + enhanced_context
        # [Sweep48] Preflight 분석 결과 주입 (LLM이 생성한 분석 텍스트)
        if cached_preflight_injection:
            enhanced_context = cached_preflight_injection + "\n\n" + enhanced_context

        # [V60.25] Stage 2 Optimizer 주입
        if self.ctx.stage2_optimizer:
            try:
                optimizer_prompt = self.ctx.stage2_optimizer.generate_optimized_prompt(
                    prev_arcs=all_refined_arcs,
                    protagonist_name=protagonist_name or "주인공",
                    include_examples=(attempt == 0),
                )
                enhanced_context = optimizer_prompt + "\n\n" + enhanced_context
                if attempt == 0:
                    self.ctx.ui.log("      ⚡ [V60.25] Stage 2 Optimizer 프롬프트 주입 완료")
            except Exception as opt_err:
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event("v60_25_optimizer_error", str(opt_err)[:100])

        # [V60.21] Focus Mode
        is_retry = attempt > 0 and current_feedback

        # [V51] Analyst 지능 향상 주입
        v51_analyst_injection = ""
        if V50_MODULES_AVAILABLE:  # [TF-39] P1-7: retry에도 거버넌스 유지
            try:
                if self.ctx.quality_amplifier:
                    analyst_constraints = self.ctx.quality_amplifier.generate_analyst_constraints(
                        arc_num=global_arc_no, prev_arcs=all_refined_arcs
                    )
                    v51_analyst_injection += analyst_constraints + "\n\n"

                if self.ctx.agent_intelligence:
                    intel_prompt = self.ctx.agent_intelligence.get_analyst_enhancement(
                        arc_num=global_arc_no, prev_arcs=all_refined_arcs
                    )
                    v51_analyst_injection += intel_prompt + "\n\n"

                if self.ctx.failure_learner:
                    learned_constraints = self.ctx.failure_learner.generate_constraint_prompt(stage=2)
                    if learned_constraints:
                        v51_analyst_injection += learned_constraints

                if self.ctx.constitutional_checker:
                    constitutional_prompt = self.ctx.constitutional_checker.get_full_injection(
                        stage=2, context={"prev_arcs": all_refined_arcs, "feedback": current_feedback}
                    )
                    v51_analyst_injection = constitutional_prompt + "\n\n" + v51_analyst_injection

                if v51_analyst_injection:
                    enhanced_context = v51_analyst_injection + "\n\n" + enhanced_context
                    self.ctx.ui.log("      🧠 [V51+V55.2] Analyst 지능 향상 + Constitutional 주입 완료")
            except Exception as v51_err:
                self.ctx.ui.log(f"      ⚠️ [V51] Analyst 향상 실패: {v51_err}")

        # [V60.21] Focus Mode: 재시도 시 컨텍스트 대폭 축소
        if is_retry:
            # [TF-39] P0-1: retry 시에도 제약 블록 보존
            _preserved_constraints = ""
            if constraint_block:
                _preserved_constraints += constraint_block
            if cached_preflight_injection:
                _preserved_constraints += (
                    ("\n\n" + cached_preflight_injection) if _preserved_constraints else cached_preflight_injection
                )

            if callable(getattr(self.ctx, "build_minimal_arc_context", None)):
                minimal_prev_context = self.ctx.build_minimal_arc_context(
                    all_refined_arcs, protagonist_name or "주인공"
                )
            else:
                minimal_prev_context = enhanced_context[:15000]  # [Phase3-B] 2K→15K: 실패 반복 시 컨텍스트 역설 제거
            if _preserved_constraints:
                enhanced_context = f"{current_feedback}\n\n{_preserved_constraints}\n\n{minimal_prev_context}"
            else:
                enhanced_context = f"{current_feedback}\n\n{minimal_prev_context}"
            context_size = len(enhanced_context)
            self.ctx.ui.log(f"      📢 [V60.21] Focus Mode 활성화 - 컨텍스트 {context_size:,}자 (제약 보존)")

        # [V60.9] Stage 3→2 역방향 피드백 주입
        if self.ctx.stage_rejection_history:
            arc_stage3_failures = [
                r for r in self.ctx.stage_rejection_history if r.get("stage") == 3 and r.get("arc_no") == global_arc_no
            ]
            if len(arc_stage3_failures) >= 3:
                reverse_feedback_3to2 = ""
                callback = getattr(self.ctx, "generate_reverse_feedback_stage3_to_2", None)
                if callable(callback):
                    try:
                        reverse_feedback_3to2 = callback(
                            architect_failures=arc_stage3_failures,
                            arc_no=global_arc_no,
                        )
                    except Exception as rf32_err:
                        if callable(getattr(self.ctx, "audit_event", None)):
                            self.ctx.audit_event(
                                "v60_9_stage3to2_error",
                                "stage 3→2 reverse feedback failed",
                                {"error": str(rf32_err)[:100], "arc_no": global_arc_no},
                            )
                        reverse_feedback_3to2 = self._build_stage3_to_2_reverse_feedback_fallback(
                            arc_stage3_failures,
                            global_arc_no,
                            status=f"callback_error:{type(rf32_err).__name__}",
                        )
                else:
                    reverse_feedback_3to2 = self._build_stage3_to_2_reverse_feedback_fallback(
                        arc_stage3_failures,
                        global_arc_no,
                        status="callback_missing",
                    )

                if reverse_feedback_3to2:
                    stage3_warning = "\n\n🔄 [V60.9 Stage 3→2 역방향 피드백]\n"
                    stage3_warning += f"이 Arc(#{global_arc_no})에서 Blueprint 설계가 {len(arc_stage3_failures)}회 실패했습니다.\n"
                    stage3_warning += "Arc 구조 자체에 문제가 있을 수 있습니다.\n\n"
                    stage3_warning += f"[Blueprint 실패 패턴 분석]\n{reverse_feedback_3to2}\n"
                    enhanced_context = stage3_warning + "\n" + enhanced_context
                    self.ctx.ui.log(
                        f"      🔄 [V60.9] Stage 3→2 역방향 피드백 주입 ({len(arc_stage3_failures)}회 실패 기반)"
                    )

        # [Item4] Stage 4→2 역방향 피드백 주입 (이전 Arc 집필 난이도 기반)
        try:
            stage4_feedback_callback = getattr(self.ctx, "generate_reverse_feedback_stage4_to_2", None)
            if (
                global_arc_no > 1
                and self.ctx.pass_rate_monitor
                and callable(stage4_feedback_callback)
                and hasattr(self.ctx.pass_rate_monitor, "get_arc_difficulty")
            ):
                prev_difficulty = self.ctx.pass_rate_monitor.get_arc_difficulty(global_arc_no - 1)
                reverse_feedback_4to2 = stage4_feedback_callback(prev_difficulty)
                if reverse_feedback_4to2:
                    stage4_warning = "\n\n🔄 [Item4 Stage 4→2 역방향 피드백]\n"
                    stage4_warning += f"{reverse_feedback_4to2}\n"
                    enhanced_context = stage4_warning + "\n" + enhanced_context
                    if callable(getattr(self.ctx, "audit_event", None)):
                        self.ctx.audit_event(
                            "s4_to_s2_feedback",
                            "Arc difficulty feedback injected",
                            {"arc_no": global_arc_no, "prev_difficulty": prev_difficulty},
                        )
                    self.ctx.ui.log(
                        f"      🔄 [Item4] Stage 4→2 역방향 피드백 주입 (이전 Arc 난이도: {prev_difficulty.get('difficulty')})"
                    )
        except Exception as rf42_err:
            logging.warning(f"[Item4] Stage 4→2 피드백 실패: {rf42_err}")

        # [S2-I8] enhanced_context 총 크기 로깅 + Gemini context window 초과 경고
        _ec_size = len(enhanced_context)
        logging.info(f"[S2-I8] enhanced_context 크기: {_ec_size:,}자 (constraint_block: {len(constraint_block):,}자)")
        _CONTEXT_WARNING_THRESHOLD = 100_000
        if _ec_size > _CONTEXT_WARNING_THRESHOLD:
            logging.warning(f"[S2-I8] enhanced_context {_ec_size:,}자 > {_CONTEXT_WARNING_THRESHOLD:,}자 경고: "
                "Gemini context window 초과 가능성 — 컨텍스트 축소 권장"
            )

        # ═══════════════════════════════════════════════════════════════
        # [V60.36] Analyst 강화 - Director 검수 통과를 위한 무장
        # ═══════════════════════════════════════════════════════════════
        refined_arc = None
        generation_method = "analyst"
        analyst_weapons = {}

        logging.warning(f"\n {'=' * 60}")
        logging.info(f"[V60.36] Arc {global_arc_no} 생성 시작 (attempt {attempt + 1})")
        logging.info(f"{'=' * 60}")

        # ─────────────────────────────────────────────────────────────
        # [무기 #1] Preflight 분석 — [V66.1] 병렬 실행 캐시 재사용
        # ─────────────────────────────────────────────────────────────
        if cached_preflight_result:
            analyst_weapons["preflight"] = cached_preflight_result

        # ─────────────────────────────────────────────────────────────
        # [무기 #2] ConstraintCompiler
        # ─────────────────────────────────────────────────────────────
        # [Sweep46] 입력 constraint_block (ConstraintDB 데이터 포함) 보존
        _compiler_block = ""
        entity_registry_for_director = {}
        if self.ctx.constraint_compiler and all_refined_arcs:
            try:
                logging.info(" [무기 #2] ConstraintCompiler 컴파일 중...")
                state_result = None
                if "state_extractor" in self.ctx.agents:
                    arc_count = len(all_refined_arcs)
                    if self.ctx.cumulative_state_cache is not None and self.ctx.cumulative_state_cache_key == arc_count:
                        state_result = self.ctx.cumulative_state_cache
                    else:
                        state_result = self.ctx.agents["state_extractor"].extract_cumulative_state(all_refined_arcs)
                        self.ctx.cumulative_state_cache = state_result
                        self.ctx.cumulative_state_cache_key = arc_count
                        # [Sweep3-D2][CrosscutR32] app 캐시 키+객체 동기화
                        if self.ctx.sync_cache_key_to_app:
                            self.ctx.sync_cache_key_to_app(arc_count, cache=state_result)
                    # [Sweep45] None 대신 {} 폴백 (downstream .items() / .get() 크래시 방지)
                    entity_registry_for_director = (state_result.get("entity_registry") if state_result else None) or {}
                    if entity_registry_for_director and callable(
                        getattr(self.ctx, "fix_entity_registry_protagonist", None)
                    ):
                        entity_registry_for_director = self.ctx.fix_entity_registry_protagonist(
                            entity_registry_for_director, protagonist_name
                        )
                        logging.info(" [V61] Entity Registry 추출됨 (Director용)")
                _resolved = getattr(self.ctx.state_tracker, "resolved_plots", []) if self.ctx.state_tracker else []
                _compiler_block = self.ctx.constraint_compiler.compile(
                    all_refined_arcs, state_result, resolved_plots=_resolved
                )
                analyst_weapons["constraints"] = _compiler_block
                logging.info(f"✅ [Constraints] 제약 블록 생성 완료 ({len(_compiler_block)}자)")
            except Exception as cc_err:
                logging.warning(f" [C-2] ConstraintCompiler/Entity 추출 실패 (entity_registry 빈 dict 폴백): {str(cc_err)[:80]}"
                )

        # [Sweep48] constraint_block은 입력값 그대로 보존 (setup에서 이미 DB+Compiler 병합됨)
        # _compiler_block은 analyst_weapons에만 전달, constraint_block에 중복 누적 방지

        return {
            "refined_arc": refined_arc,
            "generation_method": generation_method,
            "constraint_block": constraint_block,
            "entity_registry_for_director": entity_registry_for_director,
            "narrative_enriched": _narrative_enriched,  # [TF-3T-A] orchestrator 추적용
        }

    def _preflight_enrichment(
        self,
        *,
        attempt: int,
        global_arc_no: int,
        current_ep_start: int,
        current_vol_strategy: dict,
        enriched_block: dict,
        all_refined_arcs: list,
        bible_root: dict,
        protagonist_name: str,
        director_feedback_for_fourphase: str,
        entity_registry_for_director,
        genre_for_tracker: str,
        previous_attempt: dict | None = None,
    ) -> dict:
        """[4-R3-c] FourPhase generation and state tracker enrichment.

        Runs FourPhaseArcGenerator if available, and on PASS enriches
        StateTracker with NPC deaths, skills, relationships, etc.

        Returns dict of generation results for the attempt loop.
        """
        from modules.core.spinners import StageSpinner

        # ─────────────────────────────────────────────────────────────
        # [V60.77] FourPhaseArcGenerator
        # ─────────────────────────────────────────────────────────────
        four_phase_passed = False
        refined_arc = None
        generation_method = "analyst"
        draft_validator_passed = False
        consensus_passed = False
        _st_snapshot = None
        _was_patch = False
        _patch_fallback = False
        _prev_score = 0

        if "four_phase" in self.ctx.agents:
            try:
                self.ctx.ui.log(f"      🎯 [V60.77] FourPhase-Director 대면 {attempt + 1}/5")
                with StageSpinner(2, f"Arc {global_arc_no}") as _s2_spinner:
                    # [V63.3] Stage 2 벡터 검색
                    _s2_spinner.update_detail(f"Arc {global_arc_no} · 벡터 검색")
                    _s2_vector_ctx = ""
                    _retrieval_plan = None
                    _use_advisor_path = False
                    _npc_roster: list[str] = []
                    _work_focus = self._resolve_work_retrieval_focus(
                        enriched_block,
                        current_vol_strategy=current_vol_strategy,
                    )
                    _work_slot_summary = self._build_work_identity_slot_summary(
                        _work_focus,
                        enriched_block,
                        protagonist_name=protagonist_name,
                    )
                    try:
                        if self.ctx.memory and current_ep_start > 1:
                            _advisor = getattr(self.ctx, "context_advisor", None)
                            _smart_enabled = bool(_threshold("smart_retrieval.enabled", False)) and bool(
                                _threshold("smart_retrieval.stage2_enabled", False)
                            )
                            if _advisor and _smart_enabled:
                                try:
                                    _npc_roster = self._collect_npc_roster(enriched_block)
                                    _retrieval_plan = _advisor.plan_stage2_retrieval(
                                        arc_data=enriched_block or {},
                                        current_ep=current_ep_start,
                                        npc_roster=_npc_roster,
                                        work_focus=_work_focus,
                                    )
                                    _perf_key = f"sc_stage2_arc{global_arc_no}_retrieval"
                                    try:
                                        self.ctx.perf_timer.start(_perf_key)
                                    except Exception as _e:
                                        logging.debug("[Stage2Preflight] SC perf_timer start 실패 (무시): %s", _e)
                                    try:
                                        _s2_vector_ctx = self._execute_stage2_retrieval_plan(
                                        _retrieval_plan,
                                        current_ep=current_ep_start,
                                        npc_roster=_npc_roster,
                                        current_arc_no=global_arc_no,
                                        protagonist_name=protagonist_name,
                                    )
                                    finally:
                                        try:
                                            self.ctx.perf_timer.stop(_perf_key)
                                        except Exception as _e:
                                            logging.debug("[Stage2Preflight] SC perf_timer stop 실패 (무시): %s", _e)
                                    _use_advisor_path = True
                                except Exception as exc:  # advisor path failure -> fallback to legacy
                                    logging.warning("[S2-SC] advisor 실패, legacy fallback: %s", exc)  # [TF-S2PE-08]
                                    _audit_cb = getattr(self.ctx, "audit_event", None)
                                    if callable(_audit_cb):
                                        _audit_cb("s2_vector_search_failed", str(exc)[:100])

                            if not _use_advisor_path:
                                _s2_vector_ctx = self.ctx.memory.retrieve_high_res_context(
                                    enriched_block.get("block_theme", ""),
                                    current_ep_start,
                                    n_results=int(_threshold("context.vector_max_results_s2", 40)),
                                )
                    except Exception as e:  # [V64.P4] OPTIONAL: vector search — non-blocking
                        _audit_cb = getattr(self.ctx, "audit_event", None)
                        if callable(_audit_cb):
                            _audit_cb("s2_vector_search_failed", str(e)[:100])
                    _fact_ledger_context = self._build_fact_ledger_context(max_items=10)
                    if _fact_ledger_context:
                        _s2_vector_ctx = _fact_ledger_context + ("\n\n" + _s2_vector_ctx if _s2_vector_ctx else "")
                    if _work_slot_summary:
                        _s2_vector_ctx = _work_slot_summary + ("\n\n" + _s2_vector_ctx if _s2_vector_ctx else "")
                    _source_counts = self._summarize_retrieval_sources(_retrieval_plan)
                    if not _source_counts and _s2_vector_ctx and not _use_advisor_path:
                        _source_counts = {"legacy_high_res": 1}
                    _coverage_warnings: list[str] = []
                    if _work_focus and not _work_slot_summary:
                        _coverage_warnings.append("missing_work_slot_summary")
                    if _work_focus and _retrieval_plan and not any(
                        str(getattr(_slot, "category", "")).startswith("work_")
                        for _slot in (getattr(_retrieval_plan, "slots", []) or [])
                    ):
                        _coverage_warnings.append("work_focus_without_slots")
                    if (
                        _source_counts.get(RetrievalSources.DB_NPC_RELATIONSHIP, 0) > 0
                        and "[관계 의미 질의]" not in _s2_vector_ctx
                    ):
                        _coverage_warnings.append("missing_relation_slice")
                    self._record_retrieval_observation(
                        ep_num=current_ep_start,
                        stage="stage2",
                        observation={
                            "work_focus_present": bool(_work_focus),
                            "tracking_slots_count": len(_work_focus.get("tracking_slots") or []) if isinstance(_work_focus, dict) else 0,
                            "scene_engines_count": len(_work_focus.get("mandatory_scene_engines") or []) if isinstance(_work_focus, dict) else 0,
                            "registry_profiles_count": len(_work_focus.get("registry_profiles") or []) if isinstance(_work_focus, dict) else 0,
                            "planned_slots_count": len(getattr(_retrieval_plan, "slots", []) or []) if _retrieval_plan else 0,
                            "advisor_path_used": bool(_use_advisor_path),
                            "work_slot_summary_included": bool(_work_slot_summary and "[작품 추적 슬롯 요약]" in _s2_vector_ctx),
                            "relation_slice_included": "[관계 의미 질의]" in _s2_vector_ctx,
                            "source_counts": _source_counts,
                            "coverage_warnings": _coverage_warnings,
                            "vector_context_chars": len(_s2_vector_ctx),
                        },
                    )
                    if _s2_vector_ctx:
                        self.ctx.ui.log(f"      🔎 [TF-38] 벡터 검색 완료 ({len(_s2_vector_ctx):,}자)")
                    # [V65] PerfTimer: Arc 생성 측정
                    try:
                        self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_generate")
                    except Exception as e:
                        logging.warning(f"[SilentPass:Preflight] perf_timer start failed: {e!s:.100}")
                    # [TF-23] 3단계 분기: InPlace → Patch → Rewrite (Director 판단 우선)
                    from modules.core.constants import PatchModeThresholds

                    _fix_scope = previous_attempt.get("fix_scope", "") if previous_attempt else ""
                    _prev_score = previous_attempt.get("score", 0) if previous_attempt else 0
                    _has_best_arc = bool(previous_attempt and previous_attempt.get("best_arc"))

                    # [TF-23] Director 판단 우선, 점수 fallback
                    _use_inplace = _has_best_arc and (
                        _fix_scope == "inplace" or (not _fix_scope and _prev_score >= PatchModeThresholds.INPLACE)
                    )
                    _use_patch = _has_best_arc and (
                        _fix_scope in ("inplace", "partial")  # inplace 실패 시 patch 폴백
                        or (not _fix_scope and _prev_score >= PatchModeThresholds.REWRITE)
                    )
                    _was_patch = bool(_use_patch)

                    four_phase_arc = None
                    pipeline_result = {"final_verdict": None}

                    # --- InPlace 시도 (LLM 1회) ---
                    if _use_inplace:
                        logging.info(f"[TF-23] Arc InPlace 진입 (fix_scope={_fix_scope!r}, score={_prev_score})")
                        self.ctx.ui.log(f"   🔧 [TF-23] Arc InPlace: fix_scope={_fix_scope!r}, score={_prev_score}")
                        _inplace_feedback = previous_attempt.get("rejection_reason", "")
                        four_phase_arc = self.ctx.agents["four_phase"]._inplace_patch_arc(
                            original_arc=previous_attempt["best_arc"],
                            director_feedback=_inplace_feedback,
                            arc_no=global_arc_no,
                        )
                        if not four_phase_arc:
                            logging.warning("[TF-23] Arc InPlace 실패 → Patch 폴백")
                            self.ctx.ui.log("   ⚠️ [TF-23] Arc InPlace 실패 → Patch 폴백")
                        else:
                            # [TF-IPG GAP-5] preflight retry 경로 diff 로깅
                            try:
                                import json as _json_mod

                                from modules.core.constants import calc_patch_change_ratio, log_patch_diff
                                _pf_orig_j = _json_mod.dumps(previous_attempt.get("best_arc", {}), ensure_ascii=False, indent=2)
                                _pf_patch_j = _json_mod.dumps(four_phase_arc, ensure_ascii=False, indent=2)
                                log_patch_diff("S2-Preflight-Arc", _pf_orig_j, _pf_patch_j)
                                _pf_cr = calc_patch_change_ratio(
                                    _json_mod.dumps(previous_attempt.get("best_arc", {}), ensure_ascii=False),
                                    _json_mod.dumps(four_phase_arc, ensure_ascii=False),
                                )
                                if _pf_cr > 0.30:
                                    logging.warning("[TF-IPG] Preflight Arc 변경 비율 %.1f%% > 30%%", _pf_cr * 100)
                            except Exception as _diff_e:
                                logging.debug("[TF-IPG] preflight diff 계산 실패: %s", _diff_e)
                            # [TF-36] S2-006: InPlace 성공 시 final_verdict 설정
                            pipeline_result["final_verdict"] = "PASS"

                    # --- Patch 시도 (Ensemble) ---
                    if not four_phase_arc and _use_patch:
                        logging.info(f"[Patch Mode] Arc 패치 모드 진입 (score={_prev_score}, attempt={attempt})")
                        self.ctx.ui.log(f"   🔧 [Patch Mode] Arc 패치: score={_prev_score}, 원본 보존 수정")
                        _patch_feedback = previous_attempt.get("rejection_reason", "")
                        _sel_reason = previous_attempt.get("selection_reason", "")
                        _score_breakdown = previous_attempt.get("score_breakdown", {})
                        _val_warnings = previous_attempt.get("validation_warnings", [])
                        if _sel_reason:
                            _patch_feedback += f"\n[선택/거절 사유]\n{_sel_reason}"
                        if isinstance(_score_breakdown, dict) and _score_breakdown:
                            _sb = ", ".join(
                                f"{k}={v}" for k, v in _score_breakdown.items() if isinstance(v, int | float)
                            )
                            if _sb:
                                _patch_feedback += f"\n[점수 분해]\n{_sb}"
                        if isinstance(_val_warnings, list) and _val_warnings:
                            _patch_feedback += "\n[검증 경고]\n" + "\n".join(
                                f"- {w}" for w in _val_warnings[:10] if isinstance(w, str)
                            )
                        _fsr = previous_attempt.get("fix_scope_reasoning", "")
                        if _fsr:
                            _patch_feedback += f"\n[수정 범위 근거]\n{_fsr}"
                        four_phase_arc, pipeline_result = self.ctx.agents["four_phase"].patch_arc_with_feedback(
                            original_arc=previous_attempt["best_arc"],
                            director_feedback=_patch_feedback,
                            attempt_number=attempt + 1,
                            arc_no=global_arc_no,
                            ep_start=current_ep_start,
                            vol_strategy=current_vol_strategy.get("strategy_doc", ""),
                            curr_block=enriched_block,
                            prev_arcs=all_refined_arcs,
                            assets=bible_root.get("AssetLibrary", {}),
                            protagonist_name=protagonist_name or "주인공",
                            entity_registry=entity_registry_for_director,
                            state_tracker=self.ctx.state_tracker,
                            vector_context=_s2_vector_ctx,
                            adversarial_self_play=self.ctx.adversarial_self_play,
                            rejected_strategy=previous_attempt.get("selected_strategy", ""),  # [TF-36]
                        )
                        if not four_phase_arc:
                            _patch_fallback = True
                            logging.warning("[Patch Mode] Arc 패치 실패 → 전면 재생성 폴백")
                            self.ctx.ui.log("   ⚠️ [Patch Mode] Arc 패치 실패 → 전면 재생성 폴백")

                    # --- Rewrite (Ensemble 전면 재생성) ---
                    _s2_spinner.update_detail(f"Arc {global_arc_no} · Arc 생성")
                    if not four_phase_arc:
                        four_phase_arc, pipeline_result = self.ctx.agents["four_phase"].generate(
                            arc_no=global_arc_no,
                            ep_start=current_ep_start,
                            vol_strategy=current_vol_strategy.get("strategy_doc", ""),
                            curr_block=enriched_block,
                            prev_arcs=all_refined_arcs,
                            assets=bible_root.get("AssetLibrary", {}),
                            max_internal_retries=9,
                            protagonist_name=protagonist_name or "주인공",
                            director_feedback=director_feedback_for_fourphase,
                            entity_registry=entity_registry_for_director,
                            state_tracker=self.ctx.state_tracker,
                            vector_context=_s2_vector_ctx,
                            adversarial_self_play=self.ctx.adversarial_self_play,
                            director=self.ctx.agents.get("director"),  # [TF-47]
                        )
                    if four_phase_arc:
                        self.ctx.ui.log("      ✅ [TF-38] Arc 생성 완료")
                    else:
                        self.ctx.ui.log("      ⚠️ [TF-38] Arc 생성 실패")
                    try:
                        self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_generate")
                    except Exception as _e:
                        logging.debug("[Stage2Preflight] perf_timer generate stop 실패 (무시): %s", _e)

                    _s2_spinner.update_detail(f"Arc {global_arc_no} · Director 심사")
                if four_phase_arc and pipeline_result.get("final_verdict") == "PASS":
                    refined_arc = four_phase_arc
                    generation_method = "four_phase"
                    four_phase_passed = True
                    draft_validator_passed = False  # FourPhase는 독립 파이프라인 — 별도 검증 미실행
                    consensus_passed = False

                    if attempt >= 2 and self.ctx.adversarial_self_play and refined_arc:
                        try:
                            _asp_ctx = {
                                "arc_no": global_arc_no,
                                "director_feedback": director_feedback_for_fourphase,
                                "attempt": attempt + 1,
                            }
                            _asp_input = json.dumps(refined_arc, ensure_ascii=False)
                            _asp_result = self.ctx.adversarial_self_play.generate_with_adversary(
                                initial_content=_asp_input,
                                content_type="arc",
                                context=_asp_ctx,
                            )
                            _asp_output = getattr(_asp_result, "final_output", "") if _asp_result else ""
                            if _asp_output:
                                _asp_arc = {}
                                _fp_agent = self.ctx.agents.get("four_phase")
                                if _fp_agent and hasattr(_fp_agent, "_extract_json_robust"):
                                    _asp_arc = _fp_agent._extract_json_robust(_asp_output)
                                if not isinstance(_asp_arc, dict) or not _asp_arc:
                                    try:
                                        _asp_arc = json.loads(_asp_output)
                                    except (json.JSONDecodeError, ValueError):
                                        _asp_arc = {}
                                if isinstance(_asp_arc, dict) and _asp_arc.get("tactical_doc"):
                                    refined_arc = _asp_arc
                                    generation_method = "four_phase_asp"
                                    logging.info(f"✅ [ASP] Stage2 Arc 교정 적용 (attempt={attempt + 1})")
                        except Exception as e:
                            logging.warning(f"[SilentPass:Stage2:ASP:Post] {e!s:.120}")

                    refined_arc["joint_docs"] = enriched_block.get("joint_docs", {})
                    refined_arc["status_shadow"] = enriched_block.get("status_shadow", {})

                    # --- Fix 6: enriched_block → state_changes 매핑 보강 ---
                    _sc = refined_arc.get("state_changes", {})
                    # relationship_delta → relationship_changes
                    _rd = enriched_block.get("relationship_delta", [])
                    if _rd and not _sc.get("relationship_changes"):
                        _sc["relationship_changes"] = [
                            {
                                "npc": r.get("target", ""),
                                "from": r.get("before", ""),
                                "to": r.get("after", ""),
                                "episode": None,  # [TF-S2PE-09] 미정 명시 (0 하드코딩 제거)
                            }
                            for r in _rd
                            if isinstance(r, dict)
                        ]
                    # time_span → timeline
                    _ts = enriched_block.get("time_span", {})
                    if isinstance(_ts, dict) and _ts and not _sc.get("timeline", {}).get("start"):
                        _ts_val = _ts.get("in_story_time", "")  # [TF-S2PE-06] 빈 문자열 건너뜀
                        if _ts_val:
                            _sc["timeline"] = {"start": _ts_val, "end": _ts_val}
                    refined_arc["state_changes"] = _sc

                    # --- Fix 7: items_acquired advisory (장비 diff는 이벤트와 다름) ---
                    # [TF-S2PE-02] equipment diff ≠ 획득 이벤트 — Python이 직접 쓰지 않음
                    # LLM(FourPhase state_constraints)이 대사·이벤트 기반으로 직접 명시해야 함
                    _stc = refined_arc.get("state_constraints", {})
                    # [BUG-F] protagonist_items 우선 폴백
                    if not (_stc.get("protagonist_items") or _stc.get("items_acquired")):
                        _end_eq = _stc.get("arc_end_state", {}).get("equipment", [])
                        _start_eq = _stc.get("arc_start_state", {}).get("equipment", [])
                        if isinstance(_end_eq, list) and isinstance(_start_eq, list):
                            _diff_items = [i for i in _end_eq if i not in _start_eq]
                            if _diff_items:
                                logging.debug(
                                    "[S2-Preflight] items_acquired LLM 미제공 — equipment diff advisory: %s",
                                    _diff_items,
                                )  # advisory 로깅만, items_acquired 자동 채움 제거

                    logging.info(f"✅ [V60.77] FourPhase 성공! (내부 재시도: {pipeline_result.get('retries', 0)}회)")

                    # [V70] Director REJECT 시 롤백을 위한 StateTracker 핵심 레지스트리 스냅샷
                    import copy as _copy

                    _st = self.ctx.state_tracker
                    if _st is None:
                        _st_snapshot = {}
                    else:
                        _st_snapshot = {
                        "npc_registry": _copy.deepcopy(_st.npc_registry),
                        "resolved_plots": _copy.deepcopy(_st.resolved_plots),
                        "entity_destructions": _copy.deepcopy(_st.entity_destructions),
                        "protagonist_skills": _copy.deepcopy(
                            _st.protagonist_skills
                        ),  # [V70] shallow→deep (set/list 내부 변형 방어)
                        "skill_acquisitions": _copy.deepcopy(
                            _st.skill_acquisitions
                        ),  # [V70] shallow→deep (list of dicts)
                        "npc_npc_relationships": _copy.deepcopy(_st.npc_npc_relationships),
                        "item_state_registry": _copy.deepcopy(_st.item_state_registry),
                        "active_plots": _copy.deepcopy(_st.active_plots),
                        # [V70] 누락 필드 추가 (lines 770-818에서 수정되는 필드들)
                        "npc_dialogue_profiles": _copy.deepcopy(_st.npc_dialogue_profiles),
                        "in_world_timeline": _copy.deepcopy(_st.in_world_timeline),
                        "current_companions": _copy.deepcopy(_st.current_companions),
                        "pending_commitments": _copy.deepcopy(_st.pending_commitments),
                        "protagonist_emotion": _copy.deepcopy(_st.protagonist_emotion),
                        "dungeon_clear_registry": _copy.deepcopy(_st.dungeon_clear_registry),
                        "skill_cooldown_registry": _copy.deepcopy(_st.skill_cooldown_registry),
                        "spell_repertoire": _copy.deepcopy(_st.spell_repertoire),
                        "financial_number_registry": _copy.deepcopy(_st.financial_number_registry),  # [TF-R2-S2-12]
                    }

                    # [V60.94] NPC 사망/무공 습득 추출 및 StateTracker 업데이트
                    # [TF-S2PE-05] 첫 9개 extract_* try/except 래핑 — 부분 업데이트 실패 명시 기록
                    dead_npcs = []
                    learned_skills = []
                    npc_info = []
                    try:
                        dead_npcs = self.ctx.state_tracker.extract_npc_deaths_from_arc(refined_arc)
                        learned_skills = self.ctx.state_tracker.extract_skill_acquisitions_from_arc(refined_arc)
                        npc_info = self.ctx.state_tracker.extract_npc_info_from_arc(
                            refined_arc, genre=genre_for_tracker
                        )  # [V66.2] F-1 장르 가드
                        self.ctx.state_tracker.extract_resolved_plots_from_arc(refined_arc)
                        # [V66] 조직/장소 파괴, NPC 성격, NPC-NPC 관계 추출
                        self.ctx.state_tracker.extract_entity_destructions_from_arc(refined_arc)
                        self.ctx.state_tracker.extract_npc_personality_from_arc(refined_arc)
                        self.ctx.state_tracker.extract_npc_npc_relationships_from_arc(refined_arc)
                        # [V66] 아이템 상태 추출
                        self.ctx.state_tracker.extract_item_states_from_arc(refined_arc)
                        # [V66] 플롯 서스펜션 추적
                        self.ctx.state_tracker.update_plot_mentions_from_arc(refined_arc)
                    except Exception as _st_err:
                        logging.error("[Preflight] StateTracker 부분 업데이트 실패: %s", _st_err)  # [TF-S2PE-05]
                    _suspended = self.ctx.state_tracker.check_suspended_plots(global_arc_no)
                    if _suspended:
                        for sw in _suspended:
                            logging.warning(f" [V66] {sw['message']}")
                    # [V66] 장르별 레지스트리 업데이트
                    try:
                        self.ctx.state_tracker._populate_genre_registries_from_arc(refined_arc)
                    except Exception as _e:
                        logging.warning("[Sweep5-D] genre registry update failed: %s",
                            _e,
                        )
                    if genre_for_tracker == "investment":
                        try:
                            self.ctx.state_tracker.extract_financial_events_from_arc(refined_arc)
                            self.ctx.current_project.save_v20_anchor(
                                "financial_registry", self.ctx.state_tracker.export_financial_registry()
                            )
                        except Exception as _fin_err:
                            logging.warning("[SilentPass:Preflight] financial registry save failed: %s",
                                _fin_err,
                            )

                    # [V66] SemanticPlotGuard 인덱싱
                    if self.ctx.semantic_plot_guard and self.ctx.state_tracker.resolved_plots:
                        try:
                            indexed = self.ctx.semantic_plot_guard.index_resolved_plots(
                                self.ctx.state_tracker.resolved_plots
                            )
                            if indexed > 0:
                                logging.warning(f" [V66] SemanticPlotGuard: {indexed}개 플롯 인덱싱")
                        except Exception as _e:
                            logging.warning("[Sweep5-D] semantic plot indexing failed: %s",
                                _e,
                            )

                    # [V66] NPC 대화 스타일 추출
                    try:
                        self.ctx.state_tracker.extract_npc_dialogue_styles_from_arc(refined_arc)
                    except Exception as _e:
                        logging.debug("[SilentPass:S2:NpcDialogue] %s", _e)

                    # [V66.1] F-1: 시간선 마커 추출
                    try:
                        self.ctx.state_tracker.extract_time_markers_from_arc(refined_arc)
                    except Exception as e:
                        logging.warning(f"[V66.1] 시간선 추출 실패 (무시): {e}")

                    # [V66.1] F-8: NPC 신체 변화 추출
                    try:
                        self.ctx.state_tracker.extract_permanent_injuries_from_arc(refined_arc)
                    except Exception as e:
                        logging.warning(f"[V66.1] 신체 변화 추출 실패 (무시): {e}")

                    # [V66.1] 동행자 변경 추출
                    try:
                        self.ctx.state_tracker.update_companions_from_arc(refined_arc)
                    except Exception as e:
                        logging.warning(f"[V66.1] 동행자 추출 실패 (무시): {e}")

                    # [V66.1] 약속/맹세 추출
                    try:
                        self.ctx.state_tracker.extract_commitments_from_arc(refined_arc)
                    except Exception as e:
                        logging.warning(f"[V66.1] 약속 추출 실패 (무시): {e}")

                    # [V66.1] 주인공 감정 추출
                    try:
                        self.ctx.state_tracker.extract_protagonist_emotion_from_arc(refined_arc)
                    except Exception as e:
                        logging.warning(f"[V66.1] 감정 추출 실패 (무시): {e}")

                    # [V66.2] D-1,2,3: 관계/부상/이동 추출 연결
                    try:
                        self.ctx.state_tracker.extract_relationship_changes_from_arc(refined_arc)
                    except Exception as e:
                        logging.warning(f"[V66.2] 관계 변화 추출 실패 (무시): {e}")
                    try:
                        self.ctx.state_tracker.extract_npc_injuries_from_arc(refined_arc)
                    except Exception as e:
                        logging.warning(f"[V66.2] NPC 부상 추출 실패 (무시): {e}")
                    try:
                        self.ctx.state_tracker.extract_npc_movements_from_arc(refined_arc)
                    except Exception as e:
                        logging.warning(f"[V66.2] NPC 이동 추출 실패 (무시): {e}")

                    # [V66] 멀티-Arc 요약 생성 및 저장
                    try:
                        arc_summary = self.ctx.state_tracker.generate_arc_summary(global_arc_no, refined_arc)
                        self.ctx.current_project.save_v20_anchor(f"arc_summary_{global_arc_no}", arc_summary)
                        logging.info(f"\U0001f4ca [V66] Arc {global_arc_no} 요약 저장 완료")
                    except Exception as e:
                        logging.warning(f"\u26a0\ufe0f [V66] Arc 요약 저장 실패 (비차단): {e}")

                    # [V69] 5 Arc마다 NPC 레지스트리 LLM 정리
                    if global_arc_no > 0 and global_arc_no % 5 == 0:
                        try:
                            removed = self.ctx.state_tracker.cleanup_npc_registry_with_llm(global_arc_no)
                            if removed:
                                logging.info(f"\U0001f9f9 [V69] NPC 레지스트리 정리: {len(removed)}개 오탐 제거 ({', '.join(removed[:5])})"
                                )
                        except Exception as e:
                            logging.warning(f"\u26a0\ufe0f [V69] NPC 레지스트리 정리 실패 (비차단): {e}")

                    # [V61.3] 동적 장르 감지
                    tactical_doc = refined_arc.get("tactical_doc", "")
                    if tactical_doc and hasattr(self.ctx.state_tracker, "check_and_expand_genre"):
                        new_genre = self.ctx.state_tracker.check_and_expand_genre(tactical_doc)
                        if new_genre:
                            logging.info(f"- 새 장르 감지: {new_genre}")

                    if dead_npcs:
                        logging.info(f"- 사망 NPC 기록: {', '.join(dead_npcs)}")
                    if learned_skills:
                        logging.info(f"- 무공 습득 기록: {', '.join(learned_skills)}")
                    if npc_info:
                        logging.info(f"- NPC 정보 기록: {len(npc_info)}건")

                    phases = pipeline_result.get("phases", {})
                    if phases.get("generate"):
                        logging.info(f"- 후보 수: {phases['generate'].get('candidates_count', '?')}개")
                        logging.info(f"- 선택 전략: {phases['generate'].get('selected_strategy', '?')}")
                else:
                    logging.warning(" [V60.77] FourPhase 내부 검증 실패")
                    if pipeline_result.get("phases", {}).get("validate"):
                        issues = pipeline_result["phases"]["validate"].get("issues_count", 0)
                        logging.info(f"- 검증 이슈: {issues}개")
                    director_feedback_for_fourphase = "FourPhase 내부 검증 실패. 구조적 문제 해결 필요."
            except Exception as fp_err:
                logging.warning(f"❌ [V60.77] FourPhase 오류: {str(fp_err)[:80]}")
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event("four_phase_error", str(fp_err)[:100], {"arc_no": global_arc_no})
                director_feedback_for_fourphase = f"FourPhase 오류 발생: {str(fp_err)[:100]}"

        if _was_patch:
            if callable(getattr(self.ctx, "audit_event", None)):
                try:
                    self.ctx.audit_event(
                        "stage2_patch_mode",
                        "stage2 four_phase patch mode attempted",
                        {
                            "arc_no": global_arc_no,
                            "attempt": attempt + 1,
                            "prev_score": _prev_score,
                            "fallback": _patch_fallback,
                        },
                    )
                except Exception as _e:
                    logging.debug("[Stage2Preflight] audit_event(patch_mode) 실패 (무시): %s", _e)

        return {
            "four_phase_passed": four_phase_passed,
            "refined_arc": refined_arc,
            "generation_method": generation_method,
            "draft_validator_passed": draft_validator_passed,
            "consensus_passed": consensus_passed,
            "st_snapshot": _st_snapshot,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "was_patch": _was_patch,
            "patch_fallback": _patch_fallback,
            "prev_score": _prev_score,
        }
