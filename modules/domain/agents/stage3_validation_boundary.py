"""
Bounded Stage3 validation boundary helpers.
"""

from __future__ import annotations

import logging


class Stage3ValidationBoundary:
    def __init__(
        self,
        runtime,
        *,
        resolve_selection_reason_text_fn,
        threshold_fn,
        patch_mode_thresholds,
        normalize_fix_pack_fn,
        normalize_advisory_fix_pack_fn,
        normalize_repair_contract_fn,
        normalize_scope_authority_fn,
        build_local_patch_gate_fn,
    ) -> None:
        self.runtime = runtime
        self.owner = runtime.owner
        self.resolve_selection_reason_text_fn = resolve_selection_reason_text_fn
        self.threshold_fn = threshold_fn
        self.patch_mode_thresholds = patch_mode_thresholds
        self.normalize_fix_pack_fn = normalize_fix_pack_fn
        self.normalize_advisory_fix_pack_fn = normalize_advisory_fix_pack_fn
        self.normalize_repair_contract_fn = normalize_repair_contract_fn
        self.normalize_scope_authority_fn = normalize_scope_authority_fn
        self.build_local_patch_gate_fn = build_local_patch_gate_fn

    def run_phase3_validation_envelope(
        self,
        *,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        best_blueprint: dict | None,
        all_candidates: list[dict],
        director,
        arc_idx: int,
        entity_registry: dict | None,
        state_tracker,
        prev_hud: dict | None,
    ) -> dict:
        verdict, validation_result = self.runtime._call_with_operator_heartbeat(
            title="[Phase 3] Director compare + judge",
            meta={
                "phase": "validate",
                "candidate_count": len(all_candidates or []),
                "previous_blueprint_present": bool(prev_blueprint),
            },
            fn=lambda: self.owner.validator.validate(
                blueprint=best_blueprint,
                arc_data=arc_data,
                constraint_block=constraint_block,
                prev_blueprint=prev_blueprint,
                director=director,
                working_ep=ep_num,
                arc_idx=arc_idx,
                entity_registry=entity_registry,
                state_tracker=state_tracker,
                all_candidates=all_candidates,
                prev_hud=prev_hud,
            ),
        )

        if validation_result.get("selected_blueprint"):
            best_blueprint = validation_result["selected_blueprint"]
            selected_idx = validation_result.get("selected_index", 0)
            logging.info("[V60.85] Director selected candidate %d", selected_idx + 1)
            self.owner._operator_log(
                f"[Phase 3] Director selected candidate {selected_idx + 1}",
                meta={"phase": "validate", "selected_index": selected_idx + 1},
            )

        selected_meta = best_blueprint.get("_ensemble_meta", {}) if isinstance(best_blueprint, dict) else {}
        selected_strategy = selected_meta.get("strategy", "")
        score_raw = validation_result.get("score", 0)
        try:
            score = int(score_raw)
        except (ValueError, TypeError):
            score = 0

        return {
            "best_blueprint": best_blueprint,
            "validation_result": validation_result,
            "verdict": verdict,
            "selected_strategy": selected_strategy,
            "score": score,
        }

    def record_phase3_validation_payload(
        self,
        *,
        pipeline_result: dict,
        validation_result: dict,
        verdict: str,
        selected_strategy: str,
        all_candidates: list[dict],
        score: int,
    ) -> None:
        validation_selection_reason = self.resolve_selection_reason_text_fn(
            validation_result.get("selection_reason", "")
        )
        validation_verdict_reason = str(
            validation_result.get("verdict_reason")
            or validation_result.get("summary")
            or validation_result.get("feedback", "")
            or validation_selection_reason
            or ""
        ).strip()
        validation_quality_risk = bool(validation_result.get("quality_risk", False))
        validation_revision_required = bool(
            validation_result.get("revision_required", False) or verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")
        )
        pipeline_result["phases"]["validate"] = {
            "status": "complete",
            "verdict": verdict,
            "issues_count": len(validation_result.get("issues", [])),
            "confidence": validation_result.get("confidence", 0),
            "score": validation_result.get("score", 0),
            "phase": validation_result.get("phase", "unknown"),
            "selected_index": validation_result.get("selected_index", 0),
            "comparison_notes": validation_result.get("comparison_notes", ""),
            "selection_reason": validation_selection_reason,
            "verdict_reason": validation_verdict_reason,
            "fix_scope": validation_result.get("fix_scope", ""),
            "fix_scope_reasoning": validation_result.get("fix_scope_reasoning", ""),
            "quality_risk": validation_quality_risk,
            "revision_required": validation_revision_required,
            "candidate_count": validation_result.get(
                "candidate_count",
                len(all_candidates) if isinstance(all_candidates, list) else 1,
            ),
        }
        binding_issue_count = validation_result.get("binding_prevalidation_issue_count", 0)
        try:
            binding_issue_count = int(binding_issue_count or 0)
        except (TypeError, ValueError):
            binding_issue_count = 0
        if binding_issue_count > 0:
            pipeline_result["phases"]["validate"]["binding_prevalidation_issue_count"] = binding_issue_count

        binding_categories = validation_result.get("binding_prevalidation_categories", [])
        if isinstance(binding_categories, list):
            normalized_binding_categories = [
                str(item).strip() for item in binding_categories if str(item or "").strip()
            ]
            if normalized_binding_categories:
                pipeline_result["phases"]["validate"]["binding_prevalidation_categories"] = (
                    normalized_binding_categories[:6]
                )

        regenerate_only_categories = validation_result.get("binding_regenerate_only_categories", [])
        if isinstance(regenerate_only_categories, list):
            normalized_regenerate_only_categories = [
                str(item).strip() for item in regenerate_only_categories if str(item or "").strip()
            ]
            if normalized_regenerate_only_categories:
                pipeline_result["phases"]["validate"]["binding_regenerate_only_categories"] = (
                    normalized_regenerate_only_categories[:6]
                )

        regenerate_only_reason = str(validation_result.get("binding_regenerate_only_reason", "") or "").strip()
        if regenerate_only_reason:
            pipeline_result["phases"]["validate"]["binding_regenerate_only_reason"] = regenerate_only_reason

        candidate_advisories = validation_result.get("candidate_advisories", [])
        if isinstance(candidate_advisories, list) and candidate_advisories:
            pipeline_result["phases"]["validate"]["candidate_advisories"] = candidate_advisories[:3]

        selected_candidate_advisory = validation_result.get("selected_candidate_advisory", {})
        if isinstance(selected_candidate_advisory, dict) and selected_candidate_advisory:
            pipeline_result["phases"]["validate"]["selected_candidate_advisory"] = selected_candidate_advisory

        normalized_fix_pack = self.normalize_fix_pack_fn(validation_result)
        if normalized_fix_pack:
            pipeline_result["phases"]["validate"]["fix_pack"] = normalized_fix_pack

        advisory_fix_pack = self.normalize_advisory_fix_pack_fn(validation_result)
        if advisory_fix_pack:
            pipeline_result["phases"]["validate"]["advisory_fix_pack"] = advisory_fix_pack

        repair_contract = self.normalize_repair_contract_fn(
            validation_result,
            fix_pack=normalized_fix_pack or advisory_fix_pack,
        )
        if repair_contract:
            pipeline_result["phases"]["validate"]["repair_contract"] = repair_contract

        scope_authority = self.normalize_scope_authority_fn(validation_result)
        if scope_authority:
            pipeline_result["phases"]["validate"]["scope_authority"] = scope_authority

        local_patch_gate = self.build_local_patch_gate_fn(
            fix_scope=str(validation_result.get("fix_scope", "") or ""),
            fix_pack=normalized_fix_pack or advisory_fix_pack,
            repair_contract=repair_contract,
            scope_authority=scope_authority,
        )
        if isinstance(local_patch_gate, dict) and local_patch_gate:
            pipeline_result["phases"]["validate"]["local_patch_gate"] = dict(local_patch_gate)

        partial_fix_eval = validation_result.get("partial_fix_eval")
        if isinstance(partial_fix_eval, dict) and partial_fix_eval:
            pipeline_result["phases"]["validate"]["partial_fix_eval"] = dict(partial_fix_eval)

        if validation_quality_risk:
            pipeline_result["quality_risk"] = True
        if validation_revision_required:
            pipeline_result["revision_required"] = True

        pipeline_result["phases"]["generate"]["selected_strategy"] = selected_strategy or "unknown"
        pipeline_result["phases"]["generate"]["selected_score"] = score

    @staticmethod
    def record_phase3_contradictions(
        *,
        pipeline_result: dict,
        validation_result: dict,
    ) -> None:
        contradictions = validation_result.get("contradictions", [])
        if not (isinstance(contradictions, list) and contradictions):
            return

        logging.warning("[Consistency] contradictions=%d", len(contradictions))
        for contradiction in contradictions[:5]:
            logging.warning(" %s", str(contradiction)[:150])
        pipeline_result["phases"]["validate"]["contradictions"] = contradictions

    def apply_phase3_quality_gate(
        self,
        *,
        verdict: str,
        score: int,
        validation_result: dict | None = None,
    ) -> str:
        quality_gate_score = self.threshold_fn("scoring.quality_gate_score", 90)
        if verdict == "PASS" and score < quality_gate_score:
            if self.runtime._has_only_advisory_residuals(validation_result):
                logging.warning(
                    "[QualityGate] Stage3 PASS below threshold (%d < %s) but only advisory residuals remain; preserve PASS",
                    score,
                    quality_gate_score,
                )
                return verdict
            logging.warning(
                "[QualityGate] Stage3 PASS but score=%d < %s; route to REJECT as runtime gate",
                score,
                quality_gate_score,
            )
            return "REJECT"
        return verdict

    def annotate_or_accept_terminal_quality_gate_result(
        self,
        *,
        validation_verdict: str,
        verdict: str,
        validation_result: dict | None,
        effective_score: int,
        raw_score: int,
        ifc_penalty: int,
        retry: int,
        max_retries: int,
        best_blueprint: dict | None,
        pipeline_result: dict,
    ) -> tuple[str, dict]:
        if validation_verdict != "PASS" or verdict != "REJECT":
            return verdict, validation_result or {}

        normalized_validation = dict(validation_result or {})
        quality_gate_score = int(self.threshold_fn("scoring.quality_gate_score", 90))
        normalized_validation.setdefault("reject_origin", "quality_gate_reject")
        normalized_validation["quality_gate_score"] = quality_gate_score
        normalized_validation["quality_gate_effective_score"] = effective_score
        normalized_validation["quality_gate_raw_score"] = raw_score
        authority_payload = {
            "final_judgment_authority": "director_llm",
            "runtime_gate_authority": "python_runtime_routing_gate",
            "runtime_gate_role": "route_or_block_automatic_progress",
            "runtime_gate_basis": "quality_gate_reject",
        }
        normalized_validation.update(authority_payload)

        validate_phase = pipeline_result.setdefault("phases", {}).setdefault("validate", {})
        validate_phase["quality_gate_score"] = quality_gate_score
        validate_phase["quality_gate_effective_score"] = effective_score
        validate_phase["quality_gate_raw_score"] = raw_score
        validate_phase.update(authority_payload)

        terminal_retry = retry >= max_retries
        if terminal_retry and best_blueprint and effective_score >= self.patch_mode_thresholds.REWRITE:
            normalized_validation["quality_gate_terminal_acceptance"] = True
            normalized_validation["quality_gate_terminal_acceptance_reason"] = "terminal_below_threshold_warning"
            normalized_validation["quality_gate_soft_override"] = True
            normalized_validation["quality_risk"] = True
            normalized_validation["revision_required"] = True
            normalized_validation["verdict"] = "PASS_WITH_WARNING"
            normalized_validation["decision"] = "PASS_WITH_WARNING"

            validate_phase["verdict"] = "PASS_WITH_WARNING"
            validate_phase["quality_risk"] = True
            validate_phase["revision_required"] = True
            validate_phase["quality_gate_terminal_acceptance"] = {
                "decision": "promote_to_pass_with_warning",
                "effective_score": effective_score,
                "quality_gate_score": quality_gate_score,
                "raw_score": raw_score,
                "ifc_penalty": ifc_penalty,
                "retry_index": retry + 1,
                "max_retries": max_retries + 1,
            }

            pipeline_result["quality_gate_failed"] = True
            pipeline_result["quality_risk"] = True
            pipeline_result["revision_required"] = True

            logging.warning(
                "[QualityGate] terminal PASS below threshold (%d < %d) on retry %d/%d -> accept PASS_WITH_WARNING",
                effective_score,
                quality_gate_score,
                retry + 1,
                max_retries + 1,
            )
            self.runtime._log_operator_retry_context(
                title=(
                    f"[QualityGate] effective_score={effective_score} "
                    f"(raw={raw_score}, ifc_penalty={ifc_penalty}) < threshold -> PASS_WITH_WARNING"
                ),
                level="warning",
                meta={
                    "phase": "validate",
                    "score": effective_score,
                    "raw_score": raw_score,
                    "ifc_penalty": ifc_penalty,
                    "retry_index": retry + 1,
                    "max_retries": max_retries + 1,
                    "error_category": "quality_gate_terminal_acceptance",
                },
                feedback=normalized_validation.get("verdict_reason", "") or normalized_validation.get("feedback", ""),
                issues=normalized_validation.get("issues", []),
                fix_scope=str(normalized_validation.get("fix_scope", "") or ""),
            )
            return "PASS_WITH_WARNING", normalized_validation

        return verdict, normalized_validation
