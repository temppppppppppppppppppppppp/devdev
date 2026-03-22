"""Stage2 preflight per-attempt/runtime orchestration split."""

import json
import logging
from typing import TYPE_CHECKING

from modules.core.stage2_preflight import (
    Stage2AnalystWeaponsPayload,
    Stage2ArcAnalysisContextPayload,
    Stage2FourPhaseAttemptResult,
    Stage2FourPhaseCyclePayload,
    Stage2FourPhaseGenerationPlan,
    Stage2FourPhaseGenerationRequest,
    Stage2FourPhasePassPayload,
)

if TYPE_CHECKING:
    from modules.core.stage2_preflight import Stage2PreflightAnalysis


class Stage2PreflightRuntime:
    """Owns per-attempt analysis and FourPhase enrichment runtime orchestration."""

    def __init__(self, owner: "Stage2PreflightAnalysis") -> None:
        self.owner = owner

    @property
    def ctx(self):
        return self.owner.ctx

    def finalize_four_phase_pass(
        self,
        *,
        attempt: int,
        global_arc_no: int,
        director_feedback_for_fourphase: str,
        refined_arc: dict,
        pipeline_result: dict,
        enriched_block: dict,
        genre_for_tracker: str,
    ) -> Stage2FourPhasePassPayload:
        """Apply PASS-path postprocessing, snapshotting, and StateTracker updates."""
        owner = self.owner

        generation_method = "four_phase"
        four_phase_passed = True
        draft_validator_passed = False
        consensus_passed = False

        if attempt >= 2 and self.ctx.adversarial_self_play and refined_arc:
            try:
                asp_ctx = {
                    "arc_no": global_arc_no,
                    "director_feedback": director_feedback_for_fourphase,
                    "attempt": attempt + 1,
                }
                asp_input = json.dumps(refined_arc, ensure_ascii=False)
                asp_result = self.ctx.adversarial_self_play.generate_with_adversary(
                    initial_content=asp_input,
                    content_type="arc",
                    context=asp_ctx,
                )
                asp_output = getattr(asp_result, "final_output", "") if asp_result else ""
                if asp_output:
                    asp_arc = {}
                    fp_agent = self.ctx.agents.get("four_phase")
                    if fp_agent and hasattr(fp_agent, "_extract_json_robust"):
                        asp_arc = fp_agent._extract_json_robust(asp_output)
                    if not isinstance(asp_arc, dict) or not asp_arc:
                        try:
                            asp_arc = json.loads(asp_output)
                        except (json.JSONDecodeError, ValueError):
                            asp_arc = {}
                    if isinstance(asp_arc, dict) and asp_arc.get("tactical_doc"):
                        refined_arc = asp_arc
                        generation_method = "four_phase_asp"
                        logging.info("[ASP] Stage2 arc post-pass override applied (attempt=%s)", attempt + 1)
            except Exception as exc:
                logging.warning(f"[SilentPass:Stage2:ASP:Post] {exc!s:.120}")

        refined_arc["joint_docs"] = enriched_block.get("joint_docs", {})
        refined_arc["status_shadow"] = enriched_block.get("status_shadow", {})
        refined_arc = owner._apply_postpass_state_change_fixes(
            refined_arc=refined_arc,
            enriched_block=enriched_block,
        )

        logging.info("[V60.77] FourPhase PASS after %s retries", pipeline_result.get("retries", 0))
        tracker_payload = owner._apply_four_phase_pass_state_tracker_updates(
            refined_arc=refined_arc,
            global_arc_no=global_arc_no,
            genre_for_tracker=genre_for_tracker,
            pipeline_result=pipeline_result,
        )
        return Stage2FourPhasePassPayload(
            refined_arc=refined_arc,
            generation_method=generation_method,
            four_phase_passed=four_phase_passed,
            draft_validator_passed=draft_validator_passed,
            consensus_passed=consensus_passed,
            st_snapshot=tracker_payload.st_snapshot,
        )

    def preflight_arc_analysis(
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
        """Build per-attempt analysis context and analyst weapons."""
        from modules.core.constants import Emojis, RetryLimits

        owner = self.owner
        self.ctx.ui.log(
            f"   {Emojis.BRAIN} [Arc {global_arc_no}] 전술 설계 중 (시도 {attempt + 1}/{RetryLimits.ANALYST_MAX_ATTEMPTS})..."
        )

        analysis_context = self.build_arc_analysis_context(
            attempt=attempt,
            current_feedback=current_feedback,
            constraint_block=constraint_block,
            last_refined_context=last_refined_context,
            all_refined_arcs=all_refined_arcs,
            protagonist_name=protagonist_name,
            global_arc_no=global_arc_no,
            cached_preflight_injection=cached_preflight_injection,
        )
        narrative_enriched = analysis_context.narrative_enriched

        refined_arc = None
        generation_method = "analyst"

        logging.warning(f"\n {'=' * 60}")
        logging.info(f"[V60.36] Arc {global_arc_no} 생성 시작 (attempt {attempt + 1})")
        logging.info(f"{'=' * 60}")

        analyst_payload = self.prepare_analyst_weapons(
            all_refined_arcs=all_refined_arcs,
            cached_preflight_result=cached_preflight_result,
            protagonist_name=protagonist_name,
        )
        entity_registry_for_director = analyst_payload.entity_registry_for_director

        return {
            "refined_arc": refined_arc,
            "generation_method": generation_method,
            "constraint_block": constraint_block,
            "entity_registry_for_director": entity_registry_for_director,
            "narrative_enriched": narrative_enriched,
        }

    def build_arc_analysis_context(
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
    ) -> Stage2ArcAnalysisContextPayload:
        """Build the per-attempt analyst context envelope."""
        owner = self.owner

        base_context_payload = self.build_arc_analysis_base_context(
            attempt=attempt,
            last_refined_context=last_refined_context,
            all_refined_arcs=all_refined_arcs,
            protagonist_name=protagonist_name,
            global_arc_no=global_arc_no,
        )
        enhanced_context = self.apply_arc_analysis_support_layers(
            attempt=attempt,
            current_feedback=current_feedback,
            constraint_block=constraint_block,
            enhanced_context=base_context_payload.enhanced_context,
            cached_preflight_injection=cached_preflight_injection,
            all_refined_arcs=all_refined_arcs,
            protagonist_name=protagonist_name,
            global_arc_no=global_arc_no,
        )
        narrative_enriched = base_context_payload.narrative_enriched

        enhanced_context = owner._apply_retry_focus_mode(
            attempt=attempt,
            current_feedback=current_feedback,
            constraint_block=constraint_block,
            cached_preflight_injection=cached_preflight_injection,
            all_refined_arcs=all_refined_arcs,
            protagonist_name=protagonist_name,
            enhanced_context=enhanced_context,
        )

        enhanced_context = self.inject_reverse_feedback_advisories(
            enhanced_context=enhanced_context,
            global_arc_no=global_arc_no,
        )
        self.warn_on_large_arc_analysis_context(
            enhanced_context=enhanced_context,
            constraint_block=constraint_block,
        )
        return Stage2ArcAnalysisContextPayload(
            enhanced_context=enhanced_context,
            narrative_enriched=narrative_enriched,
        )

    def apply_arc_analysis_support_layers(
        self,
        *,
        attempt: int,
        current_feedback: str,
        constraint_block: str,
        enhanced_context: str,
        cached_preflight_injection: str,
        all_refined_arcs: list,
        protagonist_name: str,
        global_arc_no: int,
    ) -> str:
        """Prepend support layers before retry-focus and reverse-feedback handling."""
        from modules.core.spinners import V50_MODULES_AVAILABLE

        if constraint_block:
            enhanced_context = constraint_block + "\n" + enhanced_context
        if cached_preflight_injection:
            enhanced_context = cached_preflight_injection + "\n\n" + enhanced_context

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

        v51_analyst_injection = ""
        if V50_MODULES_AVAILABLE:
            try:
                if self.ctx.quality_amplifier:
                    analyst_constraints = self.ctx.quality_amplifier.generate_analyst_constraints(
                        arc_num=global_arc_no,
                        prev_arcs=all_refined_arcs,
                    )
                    v51_analyst_injection += analyst_constraints + "\n\n"

                if self.ctx.agent_intelligence:
                    intel_prompt = self.ctx.agent_intelligence.get_analyst_enhancement(
                        arc_num=global_arc_no,
                        prev_arcs=all_refined_arcs,
                    )
                    v51_analyst_injection += intel_prompt + "\n\n"

                if self.ctx.failure_learner:
                    learned_constraints = self.ctx.failure_learner.generate_constraint_prompt(stage=2)
                    if learned_constraints:
                        v51_analyst_injection += learned_constraints

                if self.ctx.constitutional_checker:
                    constitutional_prompt = self.ctx.constitutional_checker.get_full_injection(
                        stage=2,
                        context={"prev_arcs": all_refined_arcs, "feedback": current_feedback},
                    )
                    v51_analyst_injection = constitutional_prompt + "\n\n" + v51_analyst_injection

                if v51_analyst_injection:
                    enhanced_context = v51_analyst_injection + "\n\n" + enhanced_context
                    self.ctx.ui.log("      🧠 [V51+V55.2] Analyst 지능 향상 + Constitutional 주입 완료")
            except Exception as v51_err:
                self.ctx.ui.log(f"      ⚠️ [V51] Analyst 향상 실패: {v51_err}")

        return enhanced_context

    def build_arc_analysis_base_context(
        self,
        *,
        attempt: int,
        last_refined_context: str,
        all_refined_arcs: list,
        protagonist_name: str,
        global_arc_no: int,
    ) -> Stage2ArcAnalysisContextPayload:
        quality_trend_block = ""
        if self.ctx.quality_dashboard:
            try:
                trend = self.ctx.quality_dashboard.get_score_trend_summary(stage=2)
                if trend.get("trend") != "insufficient_data" and trend.get("summary"):
                    quality_trend_block = f"\n[품질 추세 참고]\n{trend['summary']}\n"
            except Exception as qr_err:
                logging.debug("[S2-QR] 품질 추세 수집 실패 (비차단): %s", qr_err)

        enhanced_context = last_refined_context
        if quality_trend_block:
            enhanced_context = quality_trend_block + enhanced_context
        context_headers: list[str] = []
        style_guide_block = self.owner._build_style_guide_summary()
        if style_guide_block:
            context_headers.append(style_guide_block)
        protagonist_block = self.owner._build_protagonist_config_summary()
        if protagonist_block:
            context_headers.append(protagonist_block)
        if context_headers:
            enhanced_context = "\n\n".join(context_headers) + "\n\n" + enhanced_context

        narrative_enriched = False
        try:
            from modules.core.narrative_context_formatter import NarrativeContextFormatter

            state_tracker = self.ctx.state_tracker
            npc_motivations = {}
            if state_tracker and hasattr(state_tracker, "npc_registry"):
                for npc_name, npc_info in list((state_tracker.npc_registry or {}).items())[:50]:
                    if isinstance(npc_info, dict):
                        motivation = npc_info.get("primary_motivation", "")
                        if motivation:
                            npc_motivations[npc_name] = motivation

            cumulative_elapsed = None
            try:
                db = getattr(getattr(self.ctx, "current_project", None), "db", None)
                if db:
                    ws_anchor = db.load_anchor("world_state")
                    if ws_anchor and isinstance(ws_anchor, dict):
                        cumulative_elapsed = ws_anchor.get("cumulative_elapsed")
            except Exception as cum_err:
                logging.debug("[TF-F] cumulative_elapsed 조회 실패 (비치명): %s", cum_err)
            narrative_ctx = NarrativeContextFormatter.format_all(
                active_plots=getattr(state_tracker, "active_plots", None) if state_tracker else None,
                npc_motivations=npc_motivations,
                pending_commitments=getattr(state_tracker, "pending_commitments", None) if state_tracker else None,
                all_refined_arcs=all_refined_arcs,
                current_arc_no=global_arc_no,
                cumulative_elapsed=cumulative_elapsed,
            )
            if narrative_ctx:
                enhanced_context = narrative_ctx + "\n\n" + enhanced_context
                narrative_enriched = True
                if attempt == 0:
                    self.ctx.ui.log("      📖 [LM-G] 서사 구조 컨텍스트 주입 완료")
        except Exception as lmg_err:
            logging.warning("[LM-G] NarrativeContextFormatter 실패 (비치명): %s", str(lmg_err)[:80])

        fact_ledger_block = self.owner._build_fact_ledger_context(max_items=10)
        if fact_ledger_block:
            enhanced_context = fact_ledger_block + "\n\n" + enhanced_context
        return Stage2ArcAnalysisContextPayload(
            enhanced_context=enhanced_context,
            narrative_enriched=narrative_enriched,
        )

    def inject_reverse_feedback_advisories(
        self,
        *,
        enhanced_context: str,
        global_arc_no: int,
    ) -> str:
        """Prepend Stage3/4 reverse feedback advisories when available."""
        owner = self.owner

        if self.ctx.stage_rejection_history:
            arc_stage3_failures = [
                record
                for record in self.ctx.stage_rejection_history
                if record.get("stage") == 3 and record.get("arc_no") == global_arc_no
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
                                "stage 3?? reverse feedback failed",
                                {"error": str(rf32_err)[:100], "arc_no": global_arc_no},
                            )
                        reverse_feedback_3to2 = owner._build_stage3_to_2_reverse_feedback_fallback(
                            arc_stage3_failures,
                            global_arc_no,
                            status=f"callback_error:{type(rf32_err).__name__}",
                        )
                else:
                    reverse_feedback_3to2 = owner._build_stage3_to_2_reverse_feedback_fallback(
                        arc_stage3_failures,
                        global_arc_no,
                        status="callback_missing",
                    )

                if reverse_feedback_3to2:
                    stage3_warning = "\n\n🔄 [V60.9 Stage 3→2 역방향 피드백]\n"
                    stage3_warning += (
                        f"이 Arc(#{global_arc_no})에서 Blueprint 설계가 {len(arc_stage3_failures)}회 실패했습니다.\n"
                    )
                    stage3_warning += "Arc 구조 자체에 문제가 있을 수 있습니다.\n\n"
                    stage3_warning += f"[Blueprint 실패 패턴 분석]\n{reverse_feedback_3to2}\n"
                    enhanced_context = stage3_warning + "\n" + enhanced_context
                    self.ctx.ui.log(
                        f"      🔄 [V60.9] Stage 3→2 역방향 피드백 주입 ({len(arc_stage3_failures)}회 실패 기반)"
                    )

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
                        f"      🔄 [Item4] Stage 4→2 역방향 피드백 주입 (이전 Arc 난이도 {prev_difficulty.get('difficulty')})"
                    )
        except Exception as rf42_err:
            logging.warning(f"[Item4] Stage 4→2 피드백 실패: {rf42_err}")

        return enhanced_context

    def warn_on_large_arc_analysis_context(
        self,
        *,
        enhanced_context: str,
        constraint_block: str,
    ) -> None:
        """Emit context-size diagnostics for the analyst envelope."""
        context_size = len(enhanced_context)
        logging.info(f"[S2-I8] enhanced_context 크기: {context_size:,}자 (constraint_block: {len(constraint_block):,}자)")
        context_warning_threshold = 100_000
        if context_size > context_warning_threshold:
            logging.warning(
                f"[S2-I8] enhanced_context {context_size:,}자 > {context_warning_threshold:,}자 경고: "
                "Gemini context window 초과 가능성 있음, 컨텍스트 축소 권장"
            )

    def run_four_phase_generation_attempt(
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
        previous_attempt: dict | None,
        s2_spinner,
        s2_vector_ctx: str,
    ) -> Stage2FourPhaseAttemptResult:
        owner = self.owner

        try:
            self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_generate")
        except Exception as exc:
            logging.warning(f"[SilentPass:Preflight] perf_timer start failed: {exc!s:.100}")

        generation_plan = self.prepare_four_phase_generation_plan(previous_attempt)
        generation_request = Stage2FourPhaseGenerationRequest(
            attempt=attempt,
            global_arc_no=global_arc_no,
            current_ep_start=current_ep_start,
            current_vol_strategy=current_vol_strategy,
            enriched_block=enriched_block,
            all_refined_arcs=all_refined_arcs,
            bible_root=bible_root,
            protagonist_name=protagonist_name,
            director_feedback_for_fourphase=director_feedback_for_fourphase,
            entity_registry_for_director=entity_registry_for_director,
            previous_attempt=previous_attempt,
            s2_spinner=s2_spinner,
            s2_vector_ctx=s2_vector_ctx,
            generation_plan=generation_plan,
        )
        four_phase_arc, pipeline_result, patch_fallback = self.execute_four_phase_generation_plan(
            request=generation_request,
        )
        owner._log_four_phase_generation_attempt_outcome(four_phase_arc)

        try:
            self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_generate")
        except Exception as exc:
            logging.debug("[Stage2Preflight] perf_timer generate stop 실패 (무시): %s", exc)

        return owner._build_four_phase_generation_attempt_result(
            four_phase_arc=four_phase_arc,
            pipeline_result=pipeline_result,
            prev_score=generation_plan.prev_score,
            was_patch=generation_plan.was_patch,
            patch_fallback=patch_fallback,
        )

    def prepare_four_phase_generation_plan(
        self,
        previous_attempt: dict | None,
    ) -> Stage2FourPhaseGenerationPlan:
        patch_mode = self.owner._resolve_patch_mode(previous_attempt)
        if patch_mode.has_best_arc and not patch_mode.fix_scope:
            logging.warning("[PF-1] previous_attempt.fix_scope 누락 -> local patch authority 없음, full generate 위임")
            self.ctx.ui.log("   ⚠️ [PF-1] fix_scope 누락 -> local patch 생략, full generate로 위임")
        return Stage2FourPhaseGenerationPlan(
            fix_scope=patch_mode.fix_scope,
            prev_score=patch_mode.prev_score,
            was_patch=patch_mode.was_patch,
            use_inplace=patch_mode.use_inplace,
            use_patch=patch_mode.use_patch,
            four_phase_arc=None,
            pipeline_result={"final_verdict": None},
        )

    def execute_four_phase_generation_plan(
        self,
        *,
        request: Stage2FourPhaseGenerationRequest,
    ) -> tuple[dict | None, dict, bool]:
        four_phase_arc, pipeline_result = self.owner._resolve_four_phase_generation_seed(request=request)
        return self.dispatch_four_phase_generation_request(
            request=request,
            four_phase_arc=four_phase_arc,
            pipeline_result=pipeline_result,
        )

    def dispatch_four_phase_generation_request(
        self,
        *,
        request: Stage2FourPhaseGenerationRequest,
        four_phase_arc: dict | None,
        pipeline_result: dict,
    ) -> tuple[dict | None, dict, bool]:
        attempt_kwargs = self.owner._build_patch_or_generate_attempt_kwargs(
            request=request,
            four_phase_arc=four_phase_arc,
            pipeline_result=pipeline_result,
        )
        return self.owner._run_patch_or_generate_four_phase_attempt(**attempt_kwargs)

    def prepare_analyst_weapons(
        self,
        *,
        all_refined_arcs: list,
        cached_preflight_result,
        protagonist_name: str,
    ) -> Stage2AnalystWeaponsPayload:
        analyst_weapons = {}
        if cached_preflight_result:
            analyst_weapons["preflight"] = cached_preflight_result

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
                        if self.ctx.sync_cache_key_to_app:
                            self.ctx.sync_cache_key_to_app(arc_count, cache=state_result)

                    entity_registry_for_director = (state_result.get("entity_registry") if state_result else None) or {}
                    if entity_registry_for_director and callable(
                        getattr(self.ctx, "fix_entity_registry_protagonist", None)
                    ):
                        entity_registry_for_director = self.ctx.fix_entity_registry_protagonist(
                            entity_registry_for_director,
                            protagonist_name,
                        )
                        logging.info(" [V61] Entity Registry 추출됨 (Director용)")
                resolved_plots = getattr(self.ctx.state_tracker, "resolved_plots", []) if self.ctx.state_tracker else []
                compiled_constraints = self.ctx.constraint_compiler.compile(
                    all_refined_arcs,
                    state_result,
                    resolved_plots=resolved_plots,
                )
                analyst_weapons["constraints"] = compiled_constraints
                logging.info(f"✅ [Constraints] 제약 블록 생성 완료 ({len(compiled_constraints)}자)")
            except Exception as cc_err:
                logging.warning(
                    f" [C-2] ConstraintCompiler/Entity 추출 실패 (entity_registry 빈 dict 폴백): {str(cc_err)[:80]}"
                )

        return Stage2AnalystWeaponsPayload(
            analyst_weapons=analyst_weapons,
            entity_registry_for_director=entity_registry_for_director,
        )

    def preflight_enrichment(
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
        owner = self.owner

        cycle_payload = self.run_four_phase_enrichment_cycle(
            attempt=attempt,
            global_arc_no=global_arc_no,
            current_ep_start=current_ep_start,
            current_vol_strategy=current_vol_strategy,
            enriched_block=enriched_block,
            all_refined_arcs=all_refined_arcs,
            bible_root=bible_root,
            protagonist_name=protagonist_name,
            director_feedback_for_fourphase=director_feedback_for_fourphase,
            entity_registry_for_director=entity_registry_for_director,
            genre_for_tracker=genre_for_tracker,
            previous_attempt=previous_attempt,
        )

        owner._emit_patch_mode_audit_event(
            was_patch=cycle_payload.was_patch,
            global_arc_no=global_arc_no,
            attempt=attempt,
            prev_score=cycle_payload.prev_score,
            patch_fallback=cycle_payload.patch_fallback,
        )

        return owner._build_four_phase_result_payload(
            four_phase_passed=cycle_payload.four_phase_passed,
            refined_arc=cycle_payload.refined_arc,
            generation_method=cycle_payload.generation_method,
            draft_validator_passed=cycle_payload.draft_validator_passed,
            consensus_passed=cycle_payload.consensus_passed,
            st_snapshot=cycle_payload.st_snapshot,
            director_feedback_for_fourphase=cycle_payload.director_feedback_for_fourphase,
            was_patch=cycle_payload.was_patch,
            patch_fallback=cycle_payload.patch_fallback,
            prev_score=cycle_payload.prev_score,
        )

    def build_prerun_four_phase_cycle_payload(
        self,
        *,
        director_feedback_for_fourphase: str,
    ) -> Stage2FourPhaseCyclePayload:
        prerun_state = self.owner._build_four_phase_prerun_state()
        return Stage2FourPhaseCyclePayload(
            director_feedback_for_fourphase=director_feedback_for_fourphase,
            four_phase_passed=prerun_state["four_phase_passed"],
            refined_arc=prerun_state["refined_arc"],
            generation_method=prerun_state["generation_method"],
            draft_validator_passed=prerun_state["draft_validator_passed"],
            consensus_passed=prerun_state["consensus_passed"],
            st_snapshot=prerun_state["st_snapshot"],
            was_patch=prerun_state["was_patch"],
            patch_fallback=prerun_state["patch_fallback"],
            prev_score=prerun_state["prev_score"],
        )

    def run_four_phase_attempt_with_spinner(
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
        previous_attempt: dict | None = None,
    ) -> Stage2FourPhaseAttemptResult:
        from modules.core.spinners import StageSpinner

        owner = self.owner
        spinner_labels = owner._build_four_phase_spinner_labels(
            attempt=attempt,
            global_arc_no=global_arc_no,
        )
        self.ctx.ui.log(spinner_labels["attempt_log"])
        with StageSpinner(2, spinner_labels["spinner_title"]) as s2_spinner:
            s2_spinner.update_detail(spinner_labels["vector_detail"])
            s2_vector_ctx = owner._build_stage2_vector_context(
                global_arc_no=global_arc_no,
                current_ep_start=current_ep_start,
                enriched_block=enriched_block,
                current_vol_strategy=current_vol_strategy,
                protagonist_name=protagonist_name,
            )
            attempt_result = self.run_four_phase_generation_attempt(
                attempt=attempt,
                global_arc_no=global_arc_no,
                current_ep_start=current_ep_start,
                current_vol_strategy=current_vol_strategy,
                enriched_block=enriched_block,
                all_refined_arcs=all_refined_arcs,
                bible_root=bible_root,
                protagonist_name=protagonist_name,
                director_feedback_for_fourphase=director_feedback_for_fourphase,
                entity_registry_for_director=entity_registry_for_director,
                previous_attempt=previous_attempt,
                s2_spinner=s2_spinner,
                s2_vector_ctx=s2_vector_ctx,
            )
            s2_spinner.update_detail(f"Arc {global_arc_no} · Director 심사")
        return attempt_result

    def resolve_four_phase_attempt_cycle_payload(
        self,
        *,
        attempt: int,
        global_arc_no: int,
        enriched_block: dict,
        genre_for_tracker: str,
        director_feedback_for_fourphase: str,
        base_payload: Stage2FourPhaseCyclePayload,
        attempt_result: Stage2FourPhaseAttemptResult,
    ) -> Stage2FourPhaseCyclePayload:
        owner = self.owner

        base_payload.prev_score = attempt_result.prev_score
        base_payload.was_patch = attempt_result.was_patch
        base_payload.patch_fallback = attempt_result.patch_fallback

        four_phase_arc = attempt_result.four_phase_arc
        pipeline_result = attempt_result.pipeline_result
        if four_phase_arc and pipeline_result.get("final_verdict") == "PASS":
            pass_payload = self.finalize_four_phase_pass(
                attempt=attempt,
                global_arc_no=global_arc_no,
                director_feedback_for_fourphase=director_feedback_for_fourphase,
                refined_arc=four_phase_arc,
                pipeline_result=pipeline_result,
                enriched_block=enriched_block,
                genre_for_tracker=genre_for_tracker,
            )
            base_payload.refined_arc = pass_payload.refined_arc
            base_payload.generation_method = pass_payload.generation_method
            base_payload.four_phase_passed = pass_payload.four_phase_passed
            base_payload.draft_validator_passed = pass_payload.draft_validator_passed
            base_payload.consensus_passed = pass_payload.consensus_passed
            base_payload.st_snapshot = pass_payload.st_snapshot
            return base_payload

        base_payload.director_feedback_for_fourphase = owner._build_four_phase_failure_feedback(
            pipeline_result=pipeline_result,
            global_arc_no=global_arc_no,
        )
        return base_payload

    def run_four_phase_enrichment_cycle(
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
    ) -> Stage2FourPhaseCyclePayload:
        """Run the FourPhase attempt cycle and normalize the orchestration state."""
        owner = self.owner

        base_payload = self.build_prerun_four_phase_cycle_payload(
            director_feedback_for_fourphase=director_feedback_for_fourphase,
        )

        if "four_phase" not in self.ctx.agents:
            return base_payload

        try:
            attempt_result = self.run_four_phase_attempt_with_spinner(
                attempt=attempt,
                global_arc_no=global_arc_no,
                current_ep_start=current_ep_start,
                current_vol_strategy=current_vol_strategy,
                enriched_block=enriched_block,
                all_refined_arcs=all_refined_arcs,
                bible_root=bible_root,
                protagonist_name=protagonist_name,
                director_feedback_for_fourphase=director_feedback_for_fourphase,
                entity_registry_for_director=entity_registry_for_director,
                previous_attempt=previous_attempt,
            )
            return self.resolve_four_phase_attempt_cycle_payload(
                attempt=attempt,
                global_arc_no=global_arc_no,
                enriched_block=enriched_block,
                genre_for_tracker=genre_for_tracker,
                director_feedback_for_fourphase=director_feedback_for_fourphase,
                base_payload=base_payload,
                attempt_result=attempt_result,
            )
        except Exception as fp_err:
            base_payload.director_feedback_for_fourphase = owner._build_four_phase_exception_feedback(
                fp_err=fp_err,
                global_arc_no=global_arc_no,
            )
            return base_payload
