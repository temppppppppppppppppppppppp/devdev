"""[B-1-8] Stage2 preflight analysis extracted from Stage2Orchestrator."""

import concurrent.futures
import logging


class Stage2PreflightAnalysis:
    """State setup, arc analysis, and enrichment for Stage 2 preflight."""

    def __init__(self, host) -> None:
        self.host = host

    @property
    def ctx(self):
        return self.host.ctx

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

        def _compute_arc_drive() -> dict:
            """Weaver 욕망 드라이브 생성 (LLM)"""
            try:
                self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_arc_drive")
            except Exception:
                pass
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
                    self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_arc_drive")
                except Exception:
                    pass

        def _compute_preflight() -> tuple:
            """Preflight 분석 (LLM) — 결과를 attempt 루프에서 재사용"""
            try:
                self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_preflight_analysis")
            except Exception:
                pass
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
                        logging.info(f"⚠️ [Preflight] 스킵: {str(pf_err)[:50]}")
                return _pf_injection, _pf_result
            finally:
                try:
                    self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_preflight_analysis")
                except Exception:
                    pass

        # [Phase 3-Obs] PerfTimer: preflight 병렬 구간 외곽 타이머
        try:
            self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_preflight_parallel")
        except Exception:
            pass
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as _parallel_exec:
            _fut_drive = _parallel_exec.submit(_compute_arc_drive)
            _fut_preflight = _parallel_exec.submit(_compute_preflight)
            arc_drive = _fut_drive.result()
            _cached_preflight_injection, _cached_preflight_result = _fut_preflight.result()
        try:
            self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_preflight_parallel")
        except Exception:
            pass

        if _cached_preflight_result:
            logging.info("✅ [V66.1] arc_drive + preflight 병렬 완료")
            logging.info(f"- 아이템 타임라인: {len(_cached_preflight_result.get('item_timeline', []))}개")
            logging.info(f"- 금지 사항: {len(_cached_preflight_result.get('absolute_prohibitions', []))}개")
            logging.info(f"- 관계 맵: {len(_cached_preflight_result.get('relationship_map', {}))}명")

        passed = False
        current_feedback = ""

        # [V49.4] Pre-Generation Constraint 생성
        constraint_block = constraint_db.generate_constraint_block(global_arc_no)
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
                    except Exception as e:  # [V64.P4] CRITICAL: state extraction failure → NPC validation disabled
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
        max_fourphase_attempts = 5  # [V62.4]
        max_attempts = max_fourphase_attempts + 1
        director_feedback_for_fourphase = ""
        use_analyst_fallback = False

        _st_snapshot = None  # [V70] StateTracker 롤백용 스냅샷

        return {
            "arc_drive": arc_drive,
            "cached_preflight_injection": _cached_preflight_injection,
            "cached_preflight_result": _cached_preflight_result,
            "passed": passed,
            "current_feedback": current_feedback,
            "constraint_block": constraint_block,
            "attempt": attempt,
            "max_fourphase_attempts": max_fourphase_attempts,
            "max_attempts": max_attempts,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "use_analyst_fallback": use_analyst_fallback,
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

        recent_patterns = [
            a.get("hybrid_composition", {}).get("primary")
            for a in all_refined_arcs
            if a.get("hybrid_composition", {}).get("primary")
        ]

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

        # ═══════════════════════════════════════════════════════════════
        # [V60.36] Analyst 강화 - Director 검수 통과를 위한 무장
        # ═══════════════════════════════════════════════════════════════
        refined_arc = None
        generation_method = "analyst"
        analyst_weapons = {}

        logging.info(f"\n      {'=' * 60}")
        logging.info(f"[V60.36] Arc {global_arc_no} 생성 시작 (attempt {attempt + 1})")
        logging.info(f"{'=' * 60}")

        # ─────────────────────────────────────────────────────────────
        # [무기 #1] Preflight 분석 — [V66.1] 병렬 실행 캐시 재사용
        # ─────────────────────────────────────────────────────────────
        preflight_injection = cached_preflight_injection
        if cached_preflight_result:
            analyst_weapons["preflight"] = cached_preflight_result

        # ─────────────────────────────────────────────────────────────
        # [무기 #2] ConstraintCompiler
        # ─────────────────────────────────────────────────────────────
        constraint_block = ""
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
                    entity_registry_for_director = state_result.get("entity_registry") if state_result else None
                    if entity_registry_for_director:
                        entity_registry_for_director = self.ctx.fix_entity_registry_protagonist(
                            entity_registry_for_director, protagonist_name
                        )
                        logging.info("🏷️ [V61] Entity Registry 추출됨 (Director용)")
                _resolved = getattr(self.ctx.state_tracker, "resolved_plots", []) if self.ctx.state_tracker else []
                constraint_block = self.ctx.constraint_compiler.compile(
                    all_refined_arcs, state_result, resolved_plots=_resolved
                )
                analyst_weapons["constraints"] = constraint_block
                logging.info(f"✅ [Constraints] 제약 블록 생성 완료 ({len(constraint_block)}자)")
            except Exception as cc_err:
                logging.warning(
                    f"⚠️ [C-2] ConstraintCompiler/Entity 추출 실패 (entity_registry 빈 dict 폴백): {str(cc_err)[:80]}"
                )

        return {
            "enhanced_context": enhanced_context,
            "recent_patterns": recent_patterns,
            "refined_arc": refined_arc,
            "generation_method": generation_method,
            "preflight_injection": preflight_injection,
            "constraint_block": constraint_block,
            "entity_registry_for_director": entity_registry_for_director,
        }

    def _preflight_enrichment(
        self,
        *,
        attempt: int,
        use_analyst_fallback: bool,
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

        if "four_phase" in self.ctx.agents and not use_analyst_fallback:
            try:
                self.ctx.ui.log(f"      🎯 [V60.77] FourPhase-Director 대면 {attempt + 1}/3")
                with StageSpinner(2, f"Arc {global_arc_no}"):
                    # [V63.3] Stage 2 벡터 검색
                    _s2_vector_ctx = ""
                    try:
                        if self.ctx.memory and current_ep_start > 1:
                            _s2_vector_ctx = self.ctx.memory.retrieve_high_res_context(
                                enriched_block.get("block_theme", ""), current_ep_start, n_results=2
                            )
                    except Exception as e:  # [V64.P4] OPTIONAL: vector search — non-blocking
                        self.ctx.audit_event("s2_vector_search_failed", str(e)[:100])
                    # [V65] PerfTimer: Arc 생성 측정
                    try:
                        self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_generate")
                    except Exception as e:
                        logging.warning(f"[SilentPass:Preflight] 장르 레지스트리 갱신 실패: {e!s:.100}")
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
                    )
                    try:
                        self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_generate")
                    except Exception:
                        pass

                if four_phase_arc and pipeline_result.get("final_verdict") == "PASS":
                    refined_arc = four_phase_arc
                    generation_method = "four_phase"
                    four_phase_passed = True
                    draft_validator_passed = True
                    consensus_passed = True

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
                            logging.info(f"⚠️ [V66] {sw['message']}")
                    # [V66] 장르별 레지스트리 업데이트
                    try:
                        self.ctx.state_tracker._populate_genre_registries_from_arc(refined_arc)
                    except Exception:
                        pass
                    if genre_for_tracker == "investment":
                        self.ctx.state_tracker.extract_financial_events_from_arc(refined_arc)
                        self.ctx.current_project.save_v20_anchor(
                            "financial_registry", self.ctx.state_tracker.export_financial_registry()
                        )

                    # [V66] SemanticPlotGuard 인덱싱
                    if self.ctx.semantic_plot_guard and self.ctx.state_tracker.resolved_plots:
                        try:
                            indexed = self.ctx.semantic_plot_guard.index_resolved_plots(
                                self.ctx.state_tracker.resolved_plots
                            )
                            if indexed > 0:
                                logging.info(f"📊 [V66] SemanticPlotGuard: {indexed}개 플롯 인덱싱")
                        except Exception:
                            pass

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

        return {
            "four_phase_passed": four_phase_passed,
            "refined_arc": refined_arc,
            "generation_method": generation_method,
            "draft_validator_passed": draft_validator_passed,
            "consensus_passed": consensus_passed,
            "st_snapshot": _st_snapshot,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
        }
