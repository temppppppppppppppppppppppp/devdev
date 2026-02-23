"""[B-1-8] Stage2 preflight analysis extracted from Stage2Orchestrator."""

import concurrent.futures
import json
import logging
import re
import threading

from modules.core.context_advisor import RetrievalSources
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

    def _execute_stage2_retrieval_plan(
        self,
        plan,
        *,
        current_ep: int,
        npc_roster: list[str] | None = None,
        current_arc_no: int | None = None,
    ) -> str:
        """Execute Stage2 retrieval plan and return merged context text."""
        memory = getattr(self.ctx, "memory", None)
        if not memory or not plan or not getattr(plan, "slots", None):
            return ""

        max_results = int(_threshold("context.vector_max_results_s2", 12))
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
                            logging.warning(
                                "[Retrieval] 알 수 없는 retrieval_mode '%s', dense로 폴백",
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
                self.ctx.ui.log(f"⚠️ [Weaver] 욕망 드라이브 생성 실패: {weaver_err}")
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
                            _pf_injection = self.ctx.agents["preflight"].generate_analyst_injection(_pf_result)
                    except Exception as pf_err:
                        logging.warning(f"⚠️ [Preflight] 스킵: {str(pf_err)[:50]}")
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
        try:
            _parallel_exec = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            _fut_drive = _parallel_exec.submit(_compute_arc_drive)
            _fut_preflight = _parallel_exec.submit(_compute_preflight)
            _fut_constraint = _parallel_exec.submit(_compute_constraint_block)
            arc_drive = _fut_drive.result(timeout=300)
            _cached_preflight_injection, _cached_preflight_result = _fut_preflight.result(timeout=300)
            constraint_block = _fut_constraint.result(timeout=60)
        except Exception as _pf_err:
            if _parallel_exec is not None:
                try:
                    _parallel_exec.shutdown(wait=False, cancel_futures=True)
                except Exception as _e:
                    logging.debug("[Stage2Preflight] executor shutdown(err path) 실패 (무시): %s", _e)
            logging.warning(f"⚠️ [Preflight] 병렬 실행 타임아웃/오류 (비치명): {str(_pf_err)[:80]}")
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
                            state_result = self.ctx.agents["state_extractor"].extract_cumulative_state(all_refined_arcs)
                            self.ctx.cumulative_state_cache = state_result
                            self.ctx.cumulative_state_cache_key = arc_count
                            # [Sweep3-D2][Sweep300-R1] app 캐시 키+객체 동기화
                            if self.ctx.sync_cache_key_to_app:
                                self.ctx.sync_cache_key_to_app(arc_count, cache=state_result)
                    except Exception as e:  # [V64.P4] CRITICAL: state extraction failure → NPC validation disabled
                        logging.warning(
                            f"[V64.P4] CRITICAL: extract_cumulative_state 실패 (NPC 검증 약화): {e}",
                            exc_info=True,
                        )
                        self.ctx.ui.log(
                            f"      ⚠️ [V64.P4] extract_cumulative_state 실패 (NPC 검증 약화): {str(e)[:80]}"
                        )
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
                        self.ctx.audit_event("semantic_plot_guard_index_failed", str(e)[:100])
            except Exception as cc_err:
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
            except Exception:
                pass  # [Phase 3-QR] advisory, 실패 시 비차단

        # [V49.4] 제약 블록을 prev_arc_context에 주입
        enhanced_context = last_refined_context
        if _quality_trend_block:
            enhanced_context = _quality_trend_block + enhanced_context
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
                self.ctx.audit_event("v60_25_optimizer_error", str(opt_err)[:100])

        # [V60.21] Focus Mode
        is_retry = attempt > 0 and current_feedback

        # [V51] Analyst 지능 향상 주입
        v51_analyst_injection = ""
        if V50_MODULES_AVAILABLE and not is_retry:
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
            minimal_prev_context = self.ctx.build_minimal_arc_context(all_refined_arcs, protagonist_name or "주인공")
            enhanced_context = f"{current_feedback}\n\n{minimal_prev_context}"
            context_size = len(enhanced_context)
            self.ctx.ui.log(f"      📢 [V60.21] Focus Mode 활성화 - 컨텍스트 {context_size}자 (최소화)")

        # [V60.9] Stage 3→2 역방향 피드백 주입
        try:
            if self.ctx.stage_rejection_history:
                arc_stage3_failures = [
                    r
                    for r in self.ctx.stage_rejection_history
                    if r.get("stage") == 3 and r.get("arc_no") == global_arc_no
                ]
                if len(arc_stage3_failures) >= 3:
                    reverse_feedback_3to2 = self.ctx.generate_reverse_feedback_stage3_to_2(
                        architect_failures=arc_stage3_failures, arc_no=global_arc_no
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
        except Exception as rf32_err:
            self.ctx.audit_event(
                "v60_9_stage3to2_error", "stage 3→2 reverse feedback failed", {"error": str(rf32_err)[:100]}
            )

        # [Item4] Stage 4→2 역방향 피드백 주입 (이전 Arc 집필 난이도 기반)
        try:
            if (
                global_arc_no > 1
                and self.ctx.pass_rate_monitor
                and self.ctx.generate_reverse_feedback_stage4_to_2
                and hasattr(self.ctx.pass_rate_monitor, "get_arc_difficulty")
            ):
                prev_difficulty = self.ctx.pass_rate_monitor.get_arc_difficulty(global_arc_no - 1)
                reverse_feedback_4to2 = self.ctx.generate_reverse_feedback_stage4_to_2(prev_difficulty)
                if reverse_feedback_4to2:
                    stage4_warning = "\n\n🔄 [Item4 Stage 4→2 역방향 피드백]\n"
                    stage4_warning += f"{reverse_feedback_4to2}\n"
                    enhanced_context = stage4_warning + "\n" + enhanced_context
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
            logging.warning(
                f"[S2-I8] enhanced_context {_ec_size:,}자 > {_CONTEXT_WARNING_THRESHOLD:,}자 경고: "
                "Gemini context window 초과 가능성 — 컨텍스트 축소 권장"
            )

        # ═══════════════════════════════════════════════════════════════
        # [V60.36] Analyst 강화 - Director 검수 통과를 위한 무장
        # ═══════════════════════════════════════════════════════════════
        refined_arc = None
        generation_method = "analyst"
        analyst_weapons = {}

        logging.warning(f"\n      {'=' * 60}")
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
                logging.info("📋 [무기 #2] ConstraintCompiler 컴파일 중...")
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
                    if entity_registry_for_director:
                        entity_registry_for_director = self.ctx.fix_entity_registry_protagonist(
                            entity_registry_for_director, protagonist_name
                        )
                        logging.info("🏷️ [V61] Entity Registry 추출됨 (Director용)")
                _resolved = getattr(self.ctx.state_tracker, "resolved_plots", []) if self.ctx.state_tracker else []
                _compiler_block = self.ctx.constraint_compiler.compile(
                    all_refined_arcs, state_result, resolved_plots=_resolved
                )
                analyst_weapons["constraints"] = _compiler_block
                logging.info(f"✅ [Constraints] 제약 블록 생성 완료 ({len(_compiler_block)}자)")
            except Exception as cc_err:
                logging.warning(
                    f"⚠️ [C-2] ConstraintCompiler/Entity 추출 실패 (entity_registry 빈 dict 폴백): {str(cc_err)[:80]}"
                )

        # [Sweep48] constraint_block은 입력값 그대로 보존 (setup에서 이미 DB+Compiler 병합됨)
        # _compiler_block은 analyst_weapons에만 전달, constraint_block에 중복 누적 방지

        return {
            "refined_arc": refined_arc,
            "generation_method": generation_method,
            "constraint_block": constraint_block,
            "entity_registry_for_director": entity_registry_for_director,
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
                with StageSpinner(2, f"Arc {global_arc_no}"):
                    # [V63.3] Stage 2 벡터 검색
                    _s2_vector_ctx = ""
                    try:
                        if self.ctx.memory and current_ep_start > 1:
                            _use_advisor_path = False
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
                                        )
                                    finally:
                                        try:
                                            self.ctx.perf_timer.stop(_perf_key)
                                        except Exception as _e:
                                            logging.debug("[Stage2Preflight] SC perf_timer stop 실패 (무시): %s", _e)
                                    _use_advisor_path = True
                                except Exception as exc:  # advisor path failure -> fallback to legacy
                                    _audit_cb = getattr(self.ctx, "audit_event", None)
                                    if callable(_audit_cb):
                                        _audit_cb("s2_vector_search_failed", str(exc)[:100])

                            if not _use_advisor_path:
                                _s2_vector_ctx = self.ctx.memory.retrieve_high_res_context(
                                    enriched_block.get("block_theme", ""),
                                    current_ep_start,
                                    n_results=int(_threshold("context.vector_max_results_s2", 12)),
                                )
                    except Exception as e:  # [V64.P4] OPTIONAL: vector search — non-blocking
                        _audit_cb = getattr(self.ctx, "audit_event", None)
                        if callable(_audit_cb):
                            _audit_cb("s2_vector_search_failed", str(e)[:100])
                    # [V65] PerfTimer: Arc 생성 측정
                    try:
                        self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_generate")
                    except Exception as e:
                        logging.warning(f"[SilentPass:Preflight] perf_timer start failed: {e!s:.100}")
                    # [Patch Mode] 점수 기반 분기: 패치 모드 vs 전면 재생성
                    from modules.core.constants import PatchModeThresholds

                    _use_patch = (
                        previous_attempt
                        and previous_attempt.get("score", 0) >= PatchModeThresholds.REWRITE
                        and previous_attempt.get("best_arc")
                    )
                    _was_patch = bool(_use_patch)
                    _prev_score = previous_attempt.get("score", 0) if previous_attempt else 0

                    four_phase_arc = None
                    pipeline_result = {"final_verdict": None}

                    if _use_patch:
                        _prev_score = previous_attempt["score"]
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
                        )
                        if not four_phase_arc:
                            _patch_fallback = True
                            logging.warning("[Patch Mode] Arc 패치 실패 → 전면 재생성 폴백")
                            self.ctx.ui.log("   ⚠️ [Patch Mode] Arc 패치 실패 → 전면 재생성 폴백")

                    if not four_phase_arc:
                        four_phase_arc, pipeline_result = self.ctx.agents["four_phase"].generate(
                            arc_no=global_arc_no,
                            ep_start=current_ep_start,
                            vol_strategy=current_vol_strategy.get("strategy_doc", ""),
                            curr_block=enriched_block,
                            prev_arcs=all_refined_arcs,
                            assets=bible_root.get("AssetLibrary", {}),
                            max_internal_retries=4,
                            protagonist_name=protagonist_name or "주인공",
                            director_feedback=director_feedback_for_fourphase,
                            entity_registry=entity_registry_for_director,
                            state_tracker=self.ctx.state_tracker,
                            vector_context=_s2_vector_ctx,
                            adversarial_self_play=self.ctx.adversarial_self_play,
                        )
                    try:
                        self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_generate")
                    except Exception as _e:
                        logging.debug("[Stage2Preflight] perf_timer generate stop 실패 (무시): %s", _e)

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

                    logging.info(f"✅ [V60.77] FourPhase 성공! (내부 재시도: {pipeline_result.get('retries', 0)}회)")

                    # [V70] Director REJECT 시 롤백을 위한 StateTracker 핵심 레지스트리 스냅샷
                    import copy as _copy

                    _st = self.ctx.state_tracker
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
                    _suspended = self.ctx.state_tracker.check_suspended_plots(global_arc_no)
                    if _suspended:
                        for sw in _suspended:
                            logging.warning(f"⚠️ [V66] {sw['message']}")
                    # [V66] 장르별 레지스트리 업데이트
                    try:
                        self.ctx.state_tracker._populate_genre_registries_from_arc(refined_arc)
                    except Exception as _e:
                        logging.warning(
                            "[Sweep5-D] genre registry update failed: %s",
                            _e,
                        )
                    if genre_for_tracker == "investment":
                        try:
                            self.ctx.state_tracker.extract_financial_events_from_arc(refined_arc)
                            self.ctx.current_project.save_v20_anchor(
                                "financial_registry", self.ctx.state_tracker.export_financial_registry()
                            )
                        except Exception as _fin_err:
                            logging.warning(
                                "[SilentPass:Preflight] financial registry save failed: %s",
                                _fin_err,
                            )

                    # [V66] SemanticPlotGuard 인덱싱
                    if self.ctx.semantic_plot_guard and self.ctx.state_tracker.resolved_plots:
                        try:
                            indexed = self.ctx.semantic_plot_guard.index_resolved_plots(
                                self.ctx.state_tracker.resolved_plots
                            )
                            if indexed > 0:
                                logging.warning(f"📊 [V66] SemanticPlotGuard: {indexed}개 플롯 인덱싱")
                        except Exception as _e:
                            logging.warning(
                                "[Sweep5-D] semantic plot indexing failed: %s",
                                _e,
                            )

                    # [V66] NPC 대화 스타일 추출
                    try:
                        self.ctx.state_tracker.extract_npc_dialogue_styles_from_arc(refined_arc)
                    except Exception:
                        pass  # [V66] OPTIONAL: 대화 스타일 추출 실패 비차단

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
                                logging.info(
                                    f"\U0001f9f9 [V69] NPC 레지스트리 정리: {len(removed)}개 오탐 제거 ({', '.join(removed[:5])})"
                                )
                        except Exception as e:
                            logging.warning(f"\u26a0\ufe0f [V69] NPC 레지스트리 정리 실패 (비차단): {e}")

                    # [V61.3] 동적 장르 감지
                    tactical_doc = refined_arc.get("tactical_doc", "")
                    if tactical_doc and hasattr(self.ctx.state_tracker, "check_and_expand_genre"):
                        new_genre = self.ctx.state_tracker.check_and_expand_genre(tactical_doc)
                        if new_genre:
                            logging.info(f"- 🎭 새 장르 감지: {new_genre}")

                    if dead_npcs:
                        logging.info(f"- 💀 사망 NPC 기록: {', '.join(dead_npcs)}")
                    if learned_skills:
                        logging.info(f"- 🥋 무공 습득 기록: {', '.join(learned_skills)}")
                    if npc_info:
                        logging.info(f"- 👤 NPC 정보 기록: {len(npc_info)}건")

                    phases = pipeline_result.get("phases", {})
                    if phases.get("generate"):
                        logging.info(f"- 후보 수: {phases['generate'].get('candidates_count', '?')}개")
                        logging.info(f"- 선택 전략: {phases['generate'].get('selected_strategy', '?')}")
                else:
                    logging.warning("⚠️ [V60.77] FourPhase 내부 검증 실패")
                    if pipeline_result.get("phases", {}).get("validate"):
                        issues = pipeline_result["phases"]["validate"].get("issues_count", 0)
                        logging.info(f"- 검증 이슈: {issues}개")
                    director_feedback_for_fourphase = "FourPhase 내부 검증 실패. 구조적 문제 해결 필요."
            except Exception as fp_err:
                logging.warning(f"❌ [V60.77] FourPhase 오류: {str(fp_err)[:80]}")
                self.ctx.audit_event("four_phase_error", str(fp_err)[:100], {"arc_no": global_arc_no})
                director_feedback_for_fourphase = f"FourPhase 오류 발생: {str(fp_err)[:100]}"

        if _was_patch:
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
