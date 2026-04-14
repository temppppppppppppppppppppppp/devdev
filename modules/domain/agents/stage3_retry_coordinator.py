"""
Bounded Stage3 retry coordination helpers.
"""

from __future__ import annotations

import logging
from typing import Any


class Stage3RetryCoordinator:
    def __init__(
        self,
        runtime,
        *,
        repair_router_cls,
        threshold_fn,
        patch_mode_thresholds,
        build_fix_pack_guidance_fn,
    ) -> None:
        self.runtime = runtime
        self.owner = runtime.owner
        self.repair_router_cls = repair_router_cls
        self.threshold_fn = threshold_fn
        self.patch_mode_thresholds = patch_mode_thresholds
        self.build_fix_pack_guidance_fn = build_fix_pack_guidance_fn

    @staticmethod
    def _to_result_dict(result) -> dict[str, Any]:
        return {
            "best_blueprint": getattr(result, "best_blueprint", None),
            "all_candidates": list(getattr(result, "all_candidates", []) or []),
            "should_continue": bool(getattr(result, "should_continue", False)),
            "should_break": bool(getattr(result, "should_break", False)),
        }

    def _record_inplace_block(
        self,
        *,
        retry: int,
        max_retries: int,
        retry_state,
        pipeline_result: dict,
        repair_route,
        resolved_fix_scope: str,
    ) -> None:
        if not (repair_route.inplace_retry_candidate and repair_route.block_reasons):
            return
        logging.info(
            "[PF-EE] skip Stage3 inplace patch retry; reasons=%s",
            ", ".join(repair_route.block_reasons),
        )
        pipeline_result["inplace_plateau_block_reasons"] = list(repair_route.block_reasons)
        self.owner._operator_log(
            "[Phase 2] inplace patch blocked; switch back to full_ensemble",
            meta={
                "phase": "generate",
                "retry_index": retry + 1,
                "max_retries": max_retries + 1,
                "mode": "full_ensemble",
                "inplace_blocked": True,
                "inplace_block_reasons": list(repair_route.block_reasons),
                "prev_reject_score": retry_state.prev_reject_score,
                "fix_scope": resolved_fix_scope or "",
            },
        )

    def _run_inplace_patch(
        self,
        *,
        retry: int,
        max_retries: int,
        ep_num: int,
        arc_data: dict,
        retry_state,
        resolved_fix_scope: str,
        effective_fix_pack: dict,
    ) -> dict | None:
        logging.info(" [Patch Mode] retry=%d blueprint in-place patch 시도", retry)
        self.owner._operator_log(
            (
                f"[Phase 2] patch mode 진입 "
                f"(retry={retry + 1}/{max_retries + 1}, prev_score={retry_state.prev_reject_score}, "
                f"fix_scope={resolved_fix_scope or '-'})"
            ),
            meta={
                "phase": "generate",
                "retry_index": retry + 1,
                "max_retries": max_retries + 1,
                "mode": "inplace_patch",
                "prev_reject_score": retry_state.prev_reject_score,
                "fix_scope": resolved_fix_scope or "",
            },
        )
        patch_feedback = str(retry_state.prev_reject_feedback or "").strip()
        fix_pack_guidance = self.build_fix_pack_guidance_fn(effective_fix_pack)
        if fix_pack_guidance:
            patch_feedback = f"{fix_pack_guidance}\n\n{patch_feedback}".strip() if patch_feedback else fix_pack_guidance
        try:
            return self.runtime._call_with_operator_heartbeat(
                title="[Phase 2] in-place patch",
                meta={
                    "phase": "generate",
                    "retry_index": retry + 1,
                    "max_retries": max_retries + 1,
                    "mode": "inplace_patch",
                    "feedback_chars": len(str(patch_feedback or "")),
                },
                fn=lambda: self.owner._inplace_patch_blueprint(
                    original_blueprint=retry_state.previous_best,
                    director_feedback=patch_feedback,
                    ep_num=ep_num,
                    arc_data=arc_data,
                    normalized_fix_pack=effective_fix_pack,
                ),
            )
        except Exception:
            logging.exception("[Patch Mode] Blueprint in-place patch 예외")
            return None

    def _run_ensemble_generation(
        self,
        *,
        retry: int,
        max_retries: int,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        prev_blueprints: list[dict] | None,
        protagonist_name: str,
        protagonist_config: dict,
        state_tracker,
        prev_manuscripts_text: str,
        attempt_feedback: str,
        strategy_feedback: str,
        rejected_strategy: str,
        single_strategy: str,
        effective_fix_pack: dict,
        repair_contract: dict,
    ) -> tuple[dict | None, list[dict]]:
        try:
            ensemble_kwargs = {
                "ep_num": ep_num,
                "arc_data": arc_data,
                "constraint_block": constraint_block,
                "prev_blueprint": prev_blueprint,
                "feedback": attempt_feedback,
                "strategy_specific_feedback": strategy_feedback,
                "rejected_strategy": rejected_strategy,
                "protagonist_name": protagonist_name,
                "protagonist_config": protagonist_config,
                "state_tracker": state_tracker,
                "prev_blueprints": prev_blueprints,
                "prev_manuscripts_text": prev_manuscripts_text,
                "fix_pack": effective_fix_pack,
                "repair_contract": repair_contract,
                "attempt_num": retry + 1,
            }
            if single_strategy:
                ensemble_kwargs["single_strategy"] = single_strategy
            generation_mode = f"single_strategy:{single_strategy}" if single_strategy else "full_ensemble"
            return self.runtime._call_with_operator_heartbeat(
                title=f"[Phase 2] 후보 생성 ({generation_mode})",
                meta={
                    "phase": "generate",
                    "retry_index": retry + 1,
                    "max_retries": max_retries + 1,
                    "mode": generation_mode,
                    "feedback_chars": len(str(attempt_feedback or "")),
                    "strategy_feedback_chars": len(str(strategy_feedback or "")),
                    "previous_blueprint_present": bool(prev_blueprint),
                    "blueprint_window_count": len(prev_blueprints or []),
                    "prev_manuscript_chars": len(str(prev_manuscripts_text or "")),
                },
                fn=lambda: self.owner.ensemble.generate_ensemble(**ensemble_kwargs),
            )
        except Exception:
            logging.exception("[Phase 2] generate_ensemble 예외")
            return None, []

    def run_phase2_generation(
        self,
        *,
        retry: int,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        prev_blueprints: list[dict] | None,
        protagonist_name: str,
        protagonist_config: dict,
        state_tracker,
        prev_manuscripts_text: str,
        attempt_feedback: str,
        strategy_feedback: str,
        adversarial_self_play,
        pipeline_result: dict,
        retry_state,
        max_retries: int,
    ) -> dict[str, Any]:
        best_blueprint: dict | None = None
        all_candidates: list[dict] = []
        rejected_strategy = retry_state.prev_reject_strategy if retry > 0 else ""
        single_strategy = ""
        repair_material = self.repair_router_cls.build_retry_material(retry_state)
        repair_route = self.repair_router_cls.decide_phase2_retry(
            retry=retry,
            retry_state=retry_state,
            material=repair_material,
            inplace_threshold=int(self.threshold_fn("patch_mode.inplace_below", self.patch_mode_thresholds.INPLACE)),
        )
        resolved_fix_scope = repair_route.resolved_fix_scope or repair_material.normalized_requested_fix_scope
        if retry > 0 and resolved_fix_scope == "partial" and rejected_strategy:
            single_strategy = rejected_strategy

        self._record_inplace_block(
            retry=retry,
            max_retries=max_retries,
            retry_state=retry_state,
            pipeline_result=pipeline_result,
            repair_route=repair_route,
            resolved_fix_scope=resolved_fix_scope,
        )

        if repair_route.use_inplace_patch:
            best_blueprint = self._run_inplace_patch(
                retry=retry,
                max_retries=max_retries,
                ep_num=ep_num,
                arc_data=arc_data,
                retry_state=retry_state,
                resolved_fix_scope=resolved_fix_scope,
                effective_fix_pack=repair_material.effective_fix_pack,
            )
            if best_blueprint:
                all_candidates = [best_blueprint]
                pipeline_result["patch_fallback"] = False
            else:
                pipeline_result["patch_fallback"] = True
                logging.info("[Patch Mode] Blueprint in-place 패치 실패 → full rewrite 폴백")

        if not all_candidates:
            best_blueprint, all_candidates = self._run_ensemble_generation(
                retry=retry,
                max_retries=max_retries,
                ep_num=ep_num,
                arc_data=arc_data,
                constraint_block=constraint_block,
                prev_blueprint=prev_blueprint,
                prev_blueprints=prev_blueprints,
                protagonist_name=protagonist_name,
                protagonist_config=protagonist_config,
                state_tracker=state_tracker,
                prev_manuscripts_text=prev_manuscripts_text,
                attempt_feedback=attempt_feedback,
                strategy_feedback=strategy_feedback,
                rejected_strategy=rejected_strategy,
                single_strategy=single_strategy,
                effective_fix_pack=repair_material.effective_fix_pack,
                repair_contract=repair_material.repair_contract,
            )

        if not all_candidates:
            return self._to_result_dict(
                self.runtime._handle_phase2_generation_failure(
                    retry=retry,
                    ep_num=ep_num,
                    arc_data=arc_data,
                    pipeline_result=pipeline_result,
                    max_retries=max_retries,
                )
            )

        if best_blueprint is None and all_candidates:
            best_blueprint = all_candidates[0]

        best_blueprint, all_candidates = self.runtime._append_asp_candidate(
            retry=retry,
            ep_num=ep_num,
            attempt_feedback=attempt_feedback,
            best_blueprint=best_blueprint,
            all_candidates=all_candidates,
            adversarial_self_play=adversarial_self_play,
            pipeline_result=pipeline_result,
        )

        current_strategy = ""
        prompt_envelope = {}
        if isinstance(best_blueprint, dict):
            current_strategy = best_blueprint.get("_ensemble_meta", {}).get("strategy", "")
            prompt_envelope = dict(best_blueprint.get("_ensemble_meta", {}).get("prompt_envelope") or {})
        pipeline_result.pop("failure_reason", None)
        pipeline_result["phases"]["generate"] = {
            "status": "complete",
            "candidates_count": len(all_candidates),
            "selected_strategy": current_strategy or "unknown",
        }
        if prompt_envelope:
            pipeline_result["phases"]["generate"]["prompt_envelope"] = prompt_envelope
        self.owner.stats["phase2_complete"] += 1
        logging.info("✅ [Phase 2] Ensemble 완료 — %d개 후보 → Director 선택 대기", len(all_candidates))
        self.owner._operator_log(
            f"[Phase 2] 후보 생성 완료 ({len(all_candidates)}개, strategy={current_strategy or 'unknown'})",
            meta={
                "phase": "generate",
                "candidates_count": len(all_candidates),
                "selected_strategy": current_strategy or "unknown",
                "prompt_envelope": prompt_envelope,
            },
        )
        return {
            "best_blueprint": best_blueprint,
            "all_candidates": all_candidates,
            "should_continue": False,
            "should_break": False,
        }
