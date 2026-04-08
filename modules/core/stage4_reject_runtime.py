"""
Stage4 reject/runtime orchestration split.
"""

import copy
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from modules.core.artifact_logging import build_candidate_key, normalize_artifact_meta
from modules.core.logging_keys import build_attempt_key, resolve_logging_session_id

if TYPE_CHECKING:
    from modules.core.stage4_interview_round import Stage4InterviewRound


@dataclass
class _RejectRetrySnapshotPayload:
    candidate_key: str
    previous_attempt: dict


@dataclass
class _RejectGuidancePayload:
    director_feedback: str
    action_items: list
    reject_bucket: str
    resolved_fix_scope: str
    resolved_fix_scope_reasoning: str
    resolved_fix_pack: dict
    feedback_provenance: dict[str, str]
    error_category: str
    tot_used: bool
    mad_used: bool


@dataclass
class _RejectLoggingPayload:
    reject_bucket: str
    reject_artifact_meta: dict[str, str]
    session_selection_reason: str
    session_verdict_reason: str
    session_runtime_advisory: str
    session_retry_directives: str
    session_gate_semantics: dict[str, object]
    feedback_provenance: dict[str, str]


class Stage4RejectRuntime:
    """Owns reject guidance, retry snapshotting, and reject-side runtime followups."""

    def __init__(self, owner: "Stage4InterviewRound") -> None:
        self.owner = owner

    @staticmethod
    def _conflict_first_retry_notice() -> str:
        return (
            "[Conflict-first retry] post-select hard conflict invalidated the provisional PASS. "
            "다음 라운드는 local patch가 아니라 authoritative carryover 기준 재작성으로 처리하세요."
        )

    @staticmethod
    def _should_preserve_post_select_fix_pack(fix_pack: dict | None) -> bool:
        if not isinstance(fix_pack, dict):
            return False
        patch_targets = [str(item).strip() for item in (fix_pack.get("patch_targets") or []) if str(item).strip()]
        if not patch_targets:
            return False
        target_kind = str(fix_pack.get("target_kind", "") or "").strip().lower()
        if target_kind not in {"entity_ref", "local_phrase", "local_sentence"}:
            return False
        return bool(
            fix_pack.get("must_fix")
            or str(fix_pack.get("success_condition", "") or "").strip()
            or fix_pack.get("do_not_regress")
        )

    @staticmethod
    def _merge_reject_sink_source(*, source: dict | None, previous_attempt: dict | None) -> dict:
        merged = copy.deepcopy(source) if isinstance(source, dict) else {}
        if not isinstance(previous_attempt, dict):
            return merged

        for key in (
            "gate_basis",
            "repair_scope",
            "fix_scope",
            "authoritative_fix_scope",
            "fix_pack",
            "repair_contract",
            "scope_authority",
            "scope_origin",
            "fix_pack_origin",
            "contradiction_types",
            "contradiction_details",
            "firewall_triggered",
            "firewall_reason",
            "authoritative_fix_scope_violation",
            "strong_advisory_escalation",
            "error_category",
            "director_verdict",
            "final_verdict",
        ):
            if key not in previous_attempt:
                continue
            value = previous_attempt.get(key)
            merged[key] = copy.deepcopy(value) if isinstance(value, (dict, list)) else value
        return merged

    @staticmethod
    def _enrich_reject_gate_semantics(
        gate_semantics: dict[str, object] | None,
        *,
        previous_attempt: dict | None,
    ) -> dict[str, object]:
        enriched = copy.deepcopy(gate_semantics) if isinstance(gate_semantics, dict) else {}
        if not isinstance(previous_attempt, dict):
            return enriched

        for key in ("fix_pack", "scope_origin", "repair_contract", "scope_authority", "fix_pack_origin"):
            value = previous_attempt.get(key)
            if isinstance(value, dict):
                existing = enriched.get(key)
                if isinstance(existing, dict):
                    merged_value = copy.deepcopy(existing)
                    merged_value.update(copy.deepcopy(value))
                    if merged_value or key == "fix_pack":
                        enriched[key] = merged_value
                    continue
                if value or key == "fix_pack":
                    enriched[key] = copy.deepcopy(value)
        if bool(previous_attempt.get("post_select_fix_pack_preserved")):
            enriched["post_select_fix_pack_preserved"] = True

        prior_conflict = previous_attempt.get("conflict_contract")
        if isinstance(prior_conflict, dict) and prior_conflict:
            enriched["conflict_resolution_linkage"] = {
                "resolved_from": "prior_attempt_conflict",
                "original_contract_type": str(prior_conflict.get("contract_type", "") or ""),
                "conflict_count": len(prior_conflict.get("conflicts", []) or []),
            }
        prior_reuse = previous_attempt.get("reuse_contract")
        if isinstance(prior_reuse, dict) and prior_reuse:
            enriched["reuse_contract"] = copy.deepcopy(prior_reuse)
        return enriched

    def _build_reject_sink_source(
        self,
        *,
        director_result: dict | None,
        trace_director_result: dict | None,
        previous_attempt: dict | None,
    ) -> dict[str, object]:
        base_source = trace_director_result if isinstance(trace_director_result, dict) else director_result
        merged = self._merge_reject_sink_source(source=base_source, previous_attempt=previous_attempt)
        return self._attach_explicit_non_local_fix_contract(merged)

    def _build_explicit_non_local_fix_pack(
        self,
        *,
        source: dict | None,
        fix_pack: object,
    ) -> dict[str, object]:
        source = source if isinstance(source, dict) else {}
        if self.owner._normalize_fix_pack(fix_pack):
            return {}
        gate_basis = str(source.get("gate_basis", "") or "").strip()
        if gate_basis != "strong_advisory_escalation_non_local_fix":
            return {}

        escalation = source.get("strong_advisory_escalation")
        escalation = escalation if isinstance(escalation, dict) else {}
        local_fix_contract = escalation.get("local_fix_contract")
        local_fix_contract = local_fix_contract if isinstance(local_fix_contract, dict) else {}
        contract_reason = str(local_fix_contract.get("reason", "") or source.get("fix_pack_reason", "") or "").strip()
        contract_message = self.owner._pass_with_fix_contract_message(contract_reason or "non_local_fix_scope")
        runtime_scope = str(source.get("fix_scope") or source.get("repair_scope") or "partial").strip().lower() or "partial"
        authoritative_scope = (
            str(source.get("authoritative_fix_scope") or source.get("fix_scope") or "inplace").strip().lower()
            or "inplace"
        )
        triggered_by = [
            str(item).strip()
            for item in list(escalation.get("triggered_by") or [])
            if str(item).strip()
        ]
        evidence_parts = [
            "Strong advisory escalation requires a broader rewrite contract; bounded local patching is not applicable.",
            f"Contract reason: {contract_message}.",
            f"Scope boundary: runtime={runtime_scope}, authoritative={authoritative_scope}.",
        ]
        if triggered_by:
            evidence_parts.append(f"Triggered by: {', '.join(triggered_by[:3])}.")

        return self.owner._stamp_fix_pack_provenance(
            {
                "patch_targets": ["scene-model rewrite boundary"],
                "must_fix": ["Resolve the advisory at scene-model scope before retrying this manuscript."],
                "do_not_regress": ["Do not reinterpret this broader rewrite requirement as a bounded local patch."],
                "success_condition": (
                    "The retry lane keeps an explicit non-local fix contract instead of missing fix-pack metadata."
                ),
                "target_kind": "scene_model",
                "evidence_summary": " ".join(str(part).strip() for part in evidence_parts if str(part).strip()),
            },
            provenance="runtime_synthesized",
            provenance_sources=["strong_advisory_non_local_fix", *triggered_by[:2]],
        )

    def _attach_explicit_non_local_fix_contract(self, source: dict | None) -> dict[str, object]:
        attached = copy.deepcopy(source) if isinstance(source, dict) else {}
        explicit_fix_pack = self._build_explicit_non_local_fix_pack(
            source=attached,
            fix_pack=attached.get("fix_pack"),
        )
        if not explicit_fix_pack:
            return attached

        attached["fix_pack"] = explicit_fix_pack
        attached["fix_pack_reason"] = "scene_model_target"
        repair_contract = attached.get("repair_contract")
        repair_contract = copy.deepcopy(repair_contract) if isinstance(repair_contract, dict) else {}
        if not str(repair_contract.get("provenance", "") or "").strip():
            repair_contract["provenance"] = str(explicit_fix_pack.get("provenance", "") or "")
        provenance_sources = list(explicit_fix_pack.get("provenance_sources") or [])[:4]
        if provenance_sources and not repair_contract.get("provenance_sources"):
            repair_contract["provenance_sources"] = provenance_sources
        if not str(repair_contract.get("target_kind", "") or "").strip():
            repair_contract["target_kind"] = str(explicit_fix_pack.get("target_kind", "") or "")
        if repair_contract:
            attached["repair_contract"] = repair_contract
        if not isinstance(attached.get("fix_pack_origin"), dict) or not attached.get("fix_pack_origin"):
            attached["fix_pack_origin"] = {
                "provenance": str(explicit_fix_pack.get("provenance", "") or ""),
                "provenance_sources": provenance_sources,
                "routing_contract": "runtime_generated_requires_rewrite",
            }
        return attached

    @staticmethod
    def _build_reject_followup_contract(
        *,
        reject_bucket: str,
        score: int,
        round_num: int,
        previous_attempt: dict | None,
    ) -> dict[str, object]:
        contract: dict[str, object] = {
            "bucket": reject_bucket,
            "score": score,
            "round": round_num,
        }
        if not isinstance(previous_attempt, dict):
            return contract

        contradiction_types = [
            str(item).strip()
            for item in list(previous_attempt.get("contradiction_types") or [])
            if str(item).strip()
        ]
        if contradiction_types:
            contract["contradiction_types"] = contradiction_types
            contract["dominant_contradiction_type"] = contradiction_types[0]

        for key in ("repair_contract", "scope_authority", "scope_origin", "fix_pack_origin"):
            value = previous_attempt.get(key)
            if isinstance(value, dict) and value:
                contract[key] = copy.deepcopy(value)

        fix_pack_reason = str(previous_attempt.get("fix_pack_reason", "") or "").strip()
        if fix_pack_reason:
            contract["fix_pack_reason"] = fix_pack_reason
        return contract

    @staticmethod
    def _append_operator_note(base_text: str, note: str) -> str:
        base = str(base_text or "").strip()
        note = str(note or "").strip()
        if not note:
            return base
        if note in base:
            return base
        return f"{base}\n{note}".strip() if base else note

    @staticmethod
    def _build_numeric_carryover_operator_notes(previous_attempt: dict | None) -> tuple[str, str]:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        contradiction_types = [
            str(item).strip()
            for item in list(previous_attempt.get("contradiction_types") or [])
            if str(item).strip()
        ]
        repair_contract = previous_attempt.get("repair_contract")
        repair_contract = repair_contract if isinstance(repair_contract, dict) else {}
        repair_subtype = str(repair_contract.get("subtype", "") or "").strip()
        if repair_subtype != "numeric_carryover_authority" and "numeric_carryover_authority" not in contradiction_types:
            return "", ""

        scope_authority = previous_attempt.get("scope_authority")
        scope_authority = scope_authority if isinstance(scope_authority, dict) else {}
        runtime_scope = str(
            scope_authority.get("fix_scope")
            or repair_contract.get("fix_scope")
            or previous_attempt.get("fix_scope", "")
            or ""
        ).strip()
        authoritative_scope = str(
            scope_authority.get("authoritative_fix_scope")
            or repair_contract.get("authoritative_fix_scope")
            or previous_attempt.get("authoritative_fix_scope", "")
            or ""
        ).strip()
        scope_suffix = ""
        if runtime_scope and authoritative_scope and runtime_scope != authoritative_scope:
            scope_suffix = f" Scope: runtime={runtime_scope}, authoritative={authoritative_scope}."
        elif runtime_scope:
            scope_suffix = f" Scope: {runtime_scope}."
        elif authoritative_scope:
            scope_suffix = f" Scope: authoritative={authoritative_scope}."

        fix_pack_origin = previous_attempt.get("fix_pack_origin")
        fix_pack_origin = fix_pack_origin if isinstance(fix_pack_origin, dict) else {}
        provenance = str(repair_contract.get("provenance", "") or fix_pack_origin.get("provenance", "") or "").strip()
        provenance_suffix = f" Provenance: {provenance}." if provenance else ""

        advisory = (
            "[Numeric carryover authority] FactLedger carryover baseline remains the canonical numeric source "
            "until an explicit carryover/state update replaces it."
            f"{scope_suffix}{provenance_suffix}"
        )
        directives = (
            "[Numeric carryover authority] Preserve the EP carryover baseline and do not promote "
            "blueprint/manuscript future or liquidatable asset claims into current ledger truth "
            "without an explicit transition."
        )
        return advisory, directives

    @staticmethod
    def _build_scope_authority_operator_notes(previous_attempt: dict | None) -> tuple[str, str]:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        scope_authority = previous_attempt.get("scope_authority")
        scope_authority = scope_authority if isinstance(scope_authority, dict) else {}
        repair_contract = previous_attempt.get("repair_contract")
        repair_contract = repair_contract if isinstance(repair_contract, dict) else {}
        scope_origin = previous_attempt.get("scope_origin")
        scope_origin = scope_origin if isinstance(scope_origin, dict) else {}
        runtime_scope = str(
            scope_authority.get("fix_scope")
            or repair_contract.get("fix_scope")
            or previous_attempt.get("fix_scope", "")
            or ""
        ).strip()
        authoritative_scope = str(
            scope_authority.get("authoritative_fix_scope")
            or repair_contract.get("authoritative_fix_scope")
            or previous_attempt.get("authoritative_fix_scope", "")
            or ""
        ).strip()
        provenance = str(repair_contract.get("provenance", "") or "").strip()
        scope_origin_label = str(scope_origin.get("fix_scope", "") or "").strip()
        widened = bool(scope_authority.get("widened"))
        if not widened and runtime_scope and authoritative_scope:
            widened = runtime_scope.lower() != authoritative_scope.lower()
        if not any((authoritative_scope, provenance, widened)):
            return "", ""

        if widened and runtime_scope and authoritative_scope:
            scope_phrase = (
                f"runtime scope widened from authoritative={authoritative_scope} to runtime={runtime_scope}"
            )
        elif authoritative_scope and runtime_scope:
            scope_phrase = f"runtime scope matches authoritative={authoritative_scope}"
        elif authoritative_scope:
            scope_phrase = f"authoritative scope={authoritative_scope}"
        else:
            scope_phrase = f"runtime scope={runtime_scope}"

        extras: list[str] = []
        if scope_origin_label:
            extras.append(f"origin={scope_origin_label}")
        if provenance:
            extras.append(f"provenance={provenance}")
        extra_suffix = f" ({', '.join(extras)})" if extras else ""
        advisory = f"[Repair scope authority] {scope_phrase}.{extra_suffix}"
        if widened and authoritative_scope:
            directives = (
                f"[Repair scope authority] Preserve authoritative_fix_scope={authoritative_scope} as the "
                "Director-authored boundary even when runtime routing widens the active repair scope."
            )
        elif authoritative_scope:
            directives = (
                f"[Repair scope authority] Keep runtime repair scope aligned with "
                f"authoritative_fix_scope={authoritative_scope} unless a later runtime contract widens it explicitly."
            )
        else:
            directives = ""
        return advisory, directives

    def handle_reject(
        self,
        *,
        director_result: dict,
        director_feedback: str,
        candidates: list[dict],
        validation_results: list[dict],
        round_ctx,
        round_num: int,
        previous_attempt: dict | None,
        is_patch: bool,
        is_patch_fallback: bool,
        prev_score: int,
        prev_manuscript: str,
        asp_manuscript: str | None,
        tot_used: bool,
        mad_used: bool,
        selected: str,
        score: int,
        error_category: str,
        patch_trace: dict | None = None,
    ):
        from modules.core.stage4_types import _InterviewRoundResult

        owner = self.owner
        next_ep = round_ctx.next_ep
        blueprint = round_ctx.blueprint
        verdict = "REJECT"
        _asp_manuscript = asp_manuscript
        _tot_used = tot_used
        _mad_used = mad_used
        _prev_manuscript = prev_manuscript
        _prev_score = prev_score
        _is_patch = is_patch
        _is_patch_fallback = is_patch_fallback
        _candidate_key = ""
        _resolved_fix_scope = ""
        _resolved_fix_scope_reasoning = ""
        _feedback_provenance = {
            "director_feedback_text": "",
            "runtime_advisory": "",
            "retry_directives": "",
        }
        _reject_bucket = ""

        if verdict not in ("PASS", "PASS_WITH_FIX"):  # [TF-32]
            reject_guidance = self._build_reject_guidance_payload(
                director_result=director_result,
                director_feedback=director_feedback,
                validation_results=validation_results,
                selected=selected,
                round_num=round_num,
                blueprint=blueprint,
                prev_manuscript=_prev_manuscript,
                tot_used=_tot_used,
                mad_used=_mad_used,
                error_category=error_category,
            )
            director_feedback = reject_guidance.director_feedback
            action_items = reject_guidance.action_items
            _reject_bucket = reject_guidance.reject_bucket
            _resolved_fix_scope = reject_guidance.resolved_fix_scope
            _resolved_fix_scope_reasoning = reject_guidance.resolved_fix_scope_reasoning
            _resolved_fix_pack = reject_guidance.resolved_fix_pack
            _feedback_provenance = reject_guidance.feedback_provenance
            error_category = reject_guidance.error_category
            # [TF-5] error_category가 비어 있으면 reject_bucket에서 유도
            if not error_category and _reject_bucket:
                _bucket_to_category = {
                    "post_select_conflict": "POST_SELECT_CONFLICT",
                    "constraint_violation": "CONSTRAINT_VIOLATION",
                    "structure_error": "STRUCTURE_ERROR",
                    "quality_issue": "QUALITY_ISSUE",
                }
                error_category = _bucket_to_category.get(_reject_bucket, _reject_bucket.upper())
            _tot_used = reject_guidance.tot_used
            _mad_used = reject_guidance.mad_used

            retry_snapshot = self._build_reject_retry_snapshot(
                director_result=director_result,
                selected=selected,
                director_feedback=director_feedback,
                action_items=action_items,
                score=score,
                validation_results=validation_results,
                reject_bucket=_reject_bucket,
                tot_used=_tot_used,
                mad_used=_mad_used,
                resolved_fix_scope=_resolved_fix_scope,
                resolved_fix_scope_reasoning=_resolved_fix_scope_reasoning,
                resolved_fix_pack=_resolved_fix_pack,
                error_category=error_category,
                feedback_provenance=_feedback_provenance,
                previous_attempt=previous_attempt,
                round_num=round_num,
            )
            _candidate_key = retry_snapshot.candidate_key
            previous_attempt = retry_snapshot.previous_attempt
            self._record_reject_round_metrics(
                next_ep=next_ep,
                reject_bucket=_reject_bucket,
                score=score,
                round_num=round_num,
                selected=selected,
                asp_manuscript=_asp_manuscript,
                tot_used=_tot_used,
                mad_used=_mad_used,
                director_feedback=director_feedback,
            )
        _attempt_artifact_meta = self._record_reject_attempt_artifact(
            next_ep=next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            score=score,
            is_patch=_is_patch,
            prev_score=_prev_score,
            is_patch_fallback=_is_patch_fallback,
            director_feedback=director_feedback,
            resolved_fix_scope=(
                _resolved_fix_scope
                if verdict == "REJECT"
                else (
                    director_result.get("fix_scope", "")
                    if isinstance(director_result, dict)
                    else None
                )
            ),
            resolved_fix_scope_reasoning=_resolved_fix_scope_reasoning,
            director_result=director_result,
            candidate_key=_candidate_key,
            previous_attempt=previous_attempt,
            prev_manuscript=_prev_manuscript,
            feedback_provenance=_feedback_provenance,
            reject_bucket=_reject_bucket,
            error_category=error_category,
            patch_trace=patch_trace,
        )
        if isinstance(previous_attempt, dict) and isinstance(_attempt_artifact_meta, dict):
            for key in ("attempt_key", "candidate_key", "content_hash", "artifact_path"):
                value = str(_attempt_artifact_meta.get(key, "") or "").strip()
                if value:
                    previous_attempt[key] = value
        director_feedback = self._run_reject_followup_side_effects(
            next_ep=next_ep,
            arc_num=round_ctx.arc_data.get("arc_no", 0),
            reject_bucket=_reject_bucket,
            director_feedback=director_feedback,
            score=score,
            round_num=round_num,
            previous_attempt=previous_attempt,
        )
        return _InterviewRoundResult(
            verdict="REJECT",
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            error_category=error_category,
            attempt_artifact_meta=_attempt_artifact_meta,
        )

    def finalize_reject_result(
        self,
        *,
        reject_result,
        next_ep: int,
        round_num: int,
        round_ctx,
        chief_writer,
        director_result: dict,
        trace_director_result,
        initial_verdict: str,
        initial_score: int,
        final_verdict: str,
        final_score: int,
        selected: str,
        reason: str,
        error_category: str,
        attempt_key: str,
        selection_artifact_meta: dict,
        validation_warnings: list[str],
        is_patch: bool,
        is_patch_fallback: bool,
        trace_patch_trace: dict,
        tot_used: bool,
        mad_used: bool,
        asp_manuscript: str,
    ):
        owner = self.owner
        selection_artifact_meta = normalize_artifact_meta(selection_artifact_meta or {})
        previous_attempt = getattr(reject_result, "previous_attempt", None)
        sink_source = self._build_reject_sink_source(
            director_result=director_result,
            trace_director_result=trace_director_result if isinstance(trace_director_result, dict) else None,
            previous_attempt=previous_attempt,
        )
        if isinstance(previous_attempt, dict):
            for source_key, target_key in (
                ("candidate_key", "selection_candidate_key"),
                ("content_hash", "selection_content_hash"),
                ("artifact_path", "selection_artifact_path"),
            ):
                value = str(selection_artifact_meta.get(source_key, "") or "").strip()
                if value:
                    previous_attempt[target_key] = value
        reject_logging = self._build_reject_logging_payload(
            reject_result=reject_result,
            director_result=director_result,
            trace_director_result=trace_director_result,
            reason=reason,
        )
        arc_num = round_ctx.arc_data.get("arc_no", 0)
        self._sync_reject_result_selection_rationale(
            attempt_key=attempt_key,
            trace_director_result=trace_director_result,
            director_result=director_result,
            selection_reason=reject_logging.session_selection_reason,
            verdict_reason=reject_logging.session_verdict_reason,
            advisory_warnings=owner._build_final_selection_advisory_payload(
                gate_semantics=reject_logging.session_gate_semantics,
                fix_pack=self.owner._build_fix_pack_payload(sink_source),
                retry_budget_axes=dict(previous_attempt.get("retry_budget_axes") or {}),
            ),
        )
        owner._append_episode_log(
            ep_num=next_ep,
            round_num=round_num,
            director_result=sink_source,
            initial_verdict=initial_verdict,
            initial_score=initial_score,
            final_verdict=final_verdict,
            final_score=final_score,
            is_patch=is_patch,
            patch_fallback=is_patch_fallback,
            tot_used=tot_used,
            mad_used=mad_used,
            asp_used=bool(asp_manuscript),
            model=getattr(chief_writer, "model_tier", None),
            reject_bucket=reject_logging.reject_bucket,
            validation_warnings=validation_warnings,
            feedback_provenance=reject_logging.feedback_provenance,
            patch_trace=trace_patch_trace,
            arc_num=arc_num,
            candidate_key=reject_logging.reject_artifact_meta["candidate_key"],
            content_hash=reject_logging.reject_artifact_meta["content_hash"],
            artifact_path=reject_logging.reject_artifact_meta["artifact_path"],
            selection_candidate_key=selection_artifact_meta["candidate_key"],
            selection_content_hash=selection_artifact_meta["content_hash"],
            selection_artifact_path=selection_artifact_meta["artifact_path"],
            attempt_key=build_attempt_key(
                stage=4,
                ep_num=next_ep,
                arc_num=arc_num,
                attempt_num=round_num + 1,
                session_id=resolve_logging_session_id(getattr(owner.ctx, "current_project", None)),
            ),
        )
        owner._log_round_outcome(
            next_ep=next_ep,
            round_num=round_num,
            arc_num=arc_num,
            initial_verdict=initial_verdict,
            final_verdict=final_verdict,
            initial_score=initial_score,
            final_score=final_score,
            patch_mode=bool(is_patch),
            patch_fallback=bool(is_patch_fallback),
            warning_count=len(validation_warnings),
            final_warning_count=0,
            reject_bucket=reject_logging.reject_bucket,
            candidate_key=reject_logging.reject_artifact_meta["candidate_key"],
            artifact_path=reject_logging.reject_artifact_meta["artifact_path"],
        )
        try:
            self._log_reject_session_decision(
                next_ep=next_ep,
                round_num=round_num,
                arc_num=arc_num,
                director_result=director_result,
                trace_director_result=trace_director_result,
                final_verdict=final_verdict,
                final_score=final_score,
                selected=selected,
                reason=reason,
                error_category=error_category,
                attempt_key=attempt_key,
                selection_artifact_meta=selection_artifact_meta,
                initial_verdict=initial_verdict,
                initial_score=initial_score,
                reject_logging=reject_logging,
            )
        except Exception as exc:
            logging.debug("[SilentPass:Stage4:SessionLog] %s", exc)
        return reject_result

    def _build_reject_retry_snapshot(
        self,
        *,
        director_result: dict,
        selected: str,
        director_feedback: str,
        action_items: list,
        score: int,
        validation_results: list[dict],
        reject_bucket: str,
        tot_used: bool,
        mad_used: bool,
        resolved_fix_scope: str,
        resolved_fix_scope_reasoning: str,
        resolved_fix_pack: dict,
        error_category: str,
        feedback_provenance: dict[str, str],
        previous_attempt: dict | None,
        round_num: int,
    ) -> _RejectRetrySnapshotPayload:
        owner = self.owner
        selected_candidate = director_result.get("selected_candidate", {})
        if not isinstance(selected_candidate, dict):
            selected_candidate = {}
        selected_strategy_key = selected_candidate.get("strategy", "") or selected_candidate.get("strategy_name", "")
        snapshot_selection_reason = director_result.get("selection_reason", "")
        snapshot_verdict_reason = director_result.get("verdict_reason", "")
        snapshot_open_review = director_result.get("open_review", "")
        snapshot_fix_pack = resolved_fix_pack
        snapshot_rejection_reason = director_result.get("verdict_reason") or director_feedback
        downgraded_score = director_result.get("pre_firewall_score", score)
        try:
            downgraded_score = int(downgraded_score)
        except (ValueError, TypeError):
            downgraded_score = int(score or 0)
        preserve_bounded_post_select_fix_pack = (
            reject_bucket == "post_select_conflict"
            and resolved_fix_scope == "full"
            and self._should_preserve_post_select_fix_pack(snapshot_fix_pack)
        )
        preserve_downgraded_pass_rationale = (
            reject_bucket == "post_select_conflict"
            and resolved_fix_scope == "full"
            and bool((previous_attempt or {}).get("provisional_pass_downgrade"))
            and downgraded_score >= 80
        )
        # [SSS-T3] Track runtime rationale elision — not Director omission
        _rationale_blanked_by = ""
        if reject_bucket == "post_select_conflict" and resolved_fix_scope == "full":
            if not preserve_downgraded_pass_rationale:
                snapshot_selection_reason = ""
                snapshot_open_review = ""
                _rationale_blanked_by = "runtime_post_select_conflict_elision"
            snapshot_verdict_reason = director_feedback
            snapshot_rejection_reason = director_feedback
            snapshot_fix_pack = owner._normalize_fix_pack(snapshot_fix_pack) if preserve_bounded_post_select_fix_pack else {}
        explicit_non_local_fix_pack = self._build_explicit_non_local_fix_pack(
            source=director_result,
            fix_pack=snapshot_fix_pack,
        )
        if explicit_non_local_fix_pack:
            snapshot_fix_pack = explicit_non_local_fix_pack
        candidate_key = build_candidate_key(
            label=str(selected or ""),
            strategy=str(selected_strategy_key or ""),
            fallback="stage4",
        )
        reject_attempt = {
            "strategy": selected,
            "selected_strategy_key": selected_strategy_key,
            "rejection_reason": snapshot_rejection_reason,
            "merged_director_feedback": director_feedback,
            "action_items": action_items,
            "score": director_result.get("pre_firewall_score", score),
            "best_manuscript": selected_candidate.get("manuscript", ""),
            "score_breakdown": director_result.get("score_breakdown", {}),
            "selection_reason": snapshot_selection_reason,
            "verdict_reason": snapshot_verdict_reason,
            "director_verdict": director_result.get("director_verdict", ""),
            "final_verdict": director_result.get("final_verdict", "REJECT"),
            "gate_basis": director_result.get("gate_basis", ""),
            "repair_scope": director_result.get("repair_scope", "none"),
            # [pre-rerun] 검증 경고 상한 완화 (이전: 20건 → 50건)
            "validation_warnings": owner._collect_validation_warning_lines(validation_results, limit=50),
            "reject_bucket": reject_bucket,
            "consistency_checklist": director_result.get("consistency_checklist", {}),
            "_tot_used": tot_used,
            "_mad_used": mad_used,
            "state_updates": director_result.get("state_updates", {}),
            "fix_scope": resolved_fix_scope,
            "authoritative_fix_scope": str(
                director_result.get("authoritative_fix_scope", director_result.get("fix_scope", "")) or ""
            ),
            "fix_scope_reasoning": resolved_fix_scope_reasoning,
            "fix_pack": snapshot_fix_pack,
            "fix_pack_reason": str(owner._evaluate_fix_pack_contract(snapshot_fix_pack).get("reason", "") or ""),  # [TF-4]
            "open_review": snapshot_open_review,
            "error_category": error_category or director_result.get("error_category", ""),
            "violation_families": self._classify_current_violation_families(director_feedback, snapshot_fix_pack),
            "contradiction_types": director_result.get("contradiction_types", []),
            # [pre-rerun] 모순 세부사항 전량 보존 (이전: [:5] 상한으로 진단 손실)
            "contradiction_details": list(director_result.get("contradiction_details", []) or []),
            "firewall_triggered": bool(director_result.get("firewall_triggered")),
            "firewall_reason": director_result.get("firewall_reason", ""),
            "director_feedback_text": feedback_provenance["director_feedback_text"],
            "runtime_advisory": feedback_provenance["runtime_advisory"],
            "retry_directives": feedback_provenance["retry_directives"],
            "prior_attempts": owner._inherit_attempt_history(previous_attempt),
        }
        if isinstance(director_result.get("authoritative_fix_scope_violation"), dict):
            reject_attempt["authoritative_fix_scope_violation"] = dict(
                director_result.get("authoritative_fix_scope_violation") or {}
            )
        conflict_contract = (previous_attempt or {}).get("conflict_contract")
        if isinstance(conflict_contract, dict) and conflict_contract:
            reject_attempt["conflict_contract"] = copy.deepcopy(conflict_contract)
        reuse_contract = (previous_attempt or {}).get("reuse_contract")
        if isinstance(reuse_contract, dict) and reuse_contract:
            reject_attempt["reuse_contract"] = dict(reuse_contract)
        if preserve_bounded_post_select_fix_pack:
            reject_attempt["post_select_fix_pack_preserved"] = True
        # [SSS-T3] Rationale elision marker
        if _rationale_blanked_by:
            reject_attempt["rationale_blanked_by"] = _rationale_blanked_by
        # [SSS-T1] Scope origin metadata — distinguishes semantic layers in operator evidence
        fix_pack_provenance = ""
        fix_pack_provenance_sources: list[str] = []
        if isinstance(snapshot_fix_pack, dict) and snapshot_fix_pack:
            fix_pack_provenance = str(snapshot_fix_pack.get("provenance", "") or "").strip().lower()
            fix_pack_provenance_sources = [
                str(item).strip() for item in (snapshot_fix_pack.get("provenance_sources") or []) if str(item).strip()
            ]
        if fix_pack_provenance:
            reject_attempt["fix_pack_origin"] = {
                "provenance": fix_pack_provenance,
                "provenance_sources": fix_pack_provenance_sources,
                "routing_contract": (
                    "runtime_generated_prefers_patch"
                    if fix_pack_provenance in {"runtime_backfilled", "runtime_synthesized"}
                    else "director_authored_allows_inplace"
                ),
            }
        reject_attempt["scope_origin"] = {
            "fix_scope": (
                "runtime_widened"
                if reject_attempt["fix_scope"]
                and reject_attempt["authoritative_fix_scope"].lower() != reject_attempt["fix_scope"].lower()
                else "director_authoritative"
            ),
            "authoritative_fix_scope": "director_authoritative",
            "repair_scope": "runtime_lane",
        }
        repair_contract = owner._build_repair_contract_payload_from_parts(
            gate_semantics={
                "repair_scope": str(reject_attempt.get("repair_scope", "") or ""),
                "authoritative_fix_scope": str(reject_attempt.get("authoritative_fix_scope", "") or ""),
                "scope_origin": dict(reject_attempt.get("scope_origin") or {}),
            },
            fix_pack=snapshot_fix_pack,
            source=director_result,
        )
        if repair_contract:
            reject_attempt["repair_contract"] = repair_contract
        scope_authority = owner._build_scope_authority_payload_from_parts(
            gate_semantics={
                "repair_scope": str(reject_attempt.get("repair_scope", "") or ""),
                "authoritative_fix_scope": str(reject_attempt.get("authoritative_fix_scope", "") or ""),
                "scope_origin": dict(reject_attempt.get("scope_origin") or {}),
            },
            source=reject_attempt,
        )
        if scope_authority:
            reject_attempt["scope_authority"] = scope_authority
        next_strategy_budget = (
            "reduced"
            if reject_bucket in {"quality_issue", "constraint_violation"} and resolved_fix_scope != "full"
            else "full"
        )
        reject_attempt["retry_budget_axes"] = owner._set_retry_budget_axes(
            round_num=round_num + 1,
            repair_budget="patch_revision" if resolved_fix_scope in {"inplace", "partial"} else "rewrite_regenerate",
            strategy_budget=next_strategy_budget,
            reject_bucket=reject_bucket,
            previous_attempt=reject_attempt,
        )
        return _RejectRetrySnapshotPayload(
            candidate_key=candidate_key,
            previous_attempt=reject_attempt,
        )

    def _build_reject_guidance_payload(
        self,
        *,
        director_result: dict,
        director_feedback: str,
        validation_results: list[dict],
        selected: str,
        round_num: int,
        blueprint: dict,
        prev_manuscript: str,
        tot_used: bool,
        mad_used: bool,
        error_category: str,
    ) -> _RejectGuidancePayload:
        owner = self.owner
        selected_ci = max(0, ord(selected) - ord("A")) if isinstance(selected, str) and selected.isalpha() else 0
        selected_vr = validation_results[selected_ci] if selected_ci < len(validation_results) else {}
        feedback_provenance = owner._build_retry_feedback_provenance(
            director_result=director_result,
            director_feedback=director_feedback,
            selected_validation=selected_vr,
            round_num=round_num,
        )
        director_feedback = feedback_provenance["merged_feedback"]
        feedback = director_result.get("feedback") or {}
        action_items = director_result.get("action_items") or []
        reject_bucket = owner._classify_reject_bucket(
            director_feedback=director_feedback,
            feedback=feedback,
            action_items=action_items,
        )
        # [C-2 seam fix] Text-based _classify_reject_bucket cannot detect post-select
        # conflict downgrades (they arrive via gate_basis, not via text patterns).
        # Promote reject_bucket from gate_basis so the existing "full" scope guard fires.
        _gate_basis = str(director_result.get("gate_basis", "") or "").strip()
        if _gate_basis == "post_select_conflict" and reject_bucket != "post_select_conflict":
            reject_bucket = "post_select_conflict"
            logging.info(
                "[Stage4Gate] reject_bucket promoted to post_select_conflict from gate_basis"
            )
        resolved_fix_scope = str(director_result.get("fix_scope", "") or "")
        resolved_fix_scope_reasoning = str(director_result.get("fix_scope_reasoning", "") or "")
        resolved_fix_pack = owner._normalize_fix_pack(director_result.get("fix_pack"))
        if owner._is_continuity_replay_reject(
            director_result=director_result,
            director_feedback=director_feedback,
        ):
            error_category = "LOGIC_ERROR"
            reject_bucket = "post_select_conflict" if resolved_fix_scope != "full" else "structure_error"
            if resolved_fix_scope != "full":
                resolved_fix_scope = "full"
            continuity_notice = (
                "[A-4 continuity replay] 직전 화와 충돌하는 frontier/연속성 신호가 방화벽 REJECT로 재발했습니다. "
                "다음 라운드는 국소 문장 보정이 아니라 blueprint/frontier 교정 우선으로 처리하세요."
            )
            if continuity_notice not in director_feedback:
                director_feedback = continuity_notice + "\n" + director_feedback
            resolved_fix_scope_reasoning = (
                f"{resolved_fix_scope_reasoning}\n{continuity_notice}".strip()
                if resolved_fix_scope_reasoning
                else continuity_notice
            )

        # [IFC] Classify violation families and check rewrite escalation
        try:
            from modules.core.stage4_immutable_fact_contract import (
                classify_violation_family,
                render_violation_summary,
                should_escalate_to_rewrite,
            )

            patch_targets_empty = not (resolved_fix_pack.get("patch_targets") if resolved_fix_pack else False)
            violation_families = classify_violation_family(
                rejection_reason=director_feedback,
                fix_pack=resolved_fix_pack,
                patch_targets_empty=patch_targets_empty,
            )
            if violation_families:
                vf_summary = render_violation_summary(violation_families)
                logging.info("[IFC] Violation families: %s", vf_summary)
                if should_escalate_to_rewrite(
                    violation_families=violation_families,
                    patch_targets_empty=patch_targets_empty,
                    consecutive_empty_patches=getattr(owner, "_consecutive_empty_patches", 0),
                ):
                    if resolved_fix_scope in ("", "inplace"):
                        resolved_fix_scope = "partial"
                    escalation_notice = (
                        f"[IFC] 불변사실 위반 감지 ({vf_summary}). "
                        "국소 패치 대신 재작성 우선 처리가 필요합니다."
                    )
                    if escalation_notice not in director_feedback:
                        director_feedback = escalation_notice + "\n" + director_feedback
                    resolved_fix_scope_reasoning = (
                        f"{resolved_fix_scope_reasoning}\n{escalation_notice}".strip()
                        if resolved_fix_scope_reasoning
                        else escalation_notice
                    )
        except Exception as exc:
            logging.debug("[IFC] violation classification non-blocking error: %s", exc)

        if reject_bucket == "post_select_conflict":
            preserve_bounded_post_select_fix_pack = self._should_preserve_post_select_fix_pack(resolved_fix_pack)
            resolved_fix_scope = "full"
            resolved_fix_pack = owner._normalize_fix_pack(resolved_fix_pack) if preserve_bounded_post_select_fix_pack else {}
            conflict_notice = self._conflict_first_retry_notice()
            if conflict_notice not in director_feedback:
                director_feedback = conflict_notice + "\n" + director_feedback
            resolved_fix_scope_reasoning = (
                f"{resolved_fix_scope_reasoning}\n{conflict_notice}".strip()
                if resolved_fix_scope_reasoning
                else conflict_notice
            )
            if preserve_bounded_post_select_fix_pack:
                preserve_notice = (
                    "[TF-F1] bounded post-select fix hints preserved for continuity-guided rewrite trace"
                )
                if preserve_notice not in resolved_fix_scope_reasoning:
                    resolved_fix_scope_reasoning = (
                        f"{resolved_fix_scope_reasoning}\n{preserve_notice}".strip()
                        if resolved_fix_scope_reasoning
                        else preserve_notice
                    )

        if resolved_fix_scope == "inplace":
            fix_pack_contract = owner._evaluate_fix_pack_contract(resolved_fix_pack)
            if not fix_pack_contract.get("ready"):
                resolved_fix_scope = "partial"
                contract_reason = str(fix_pack_contract.get("reason", "") or "missing_fix_pack")
                contract_notice = (
                    "[Lane3 Gate] REJECT retry widened to partial: "
                    + owner._pass_with_fix_contract_message(contract_reason)
                )
                if contract_notice not in director_feedback:
                    director_feedback = contract_notice + "\n" + director_feedback
                resolved_fix_scope_reasoning = (
                    f"{resolved_fix_scope_reasoning}\n{contract_notice}".strip()
                    if resolved_fix_scope_reasoning
                    else contract_notice
                )

        seed_manuscript = (director_result.get("selected_candidate") or {}).get("manuscript", "") or prev_manuscript
        tot_module = owner.ctx.get_module("tree_of_thoughts")
        if reject_bucket == "structure_error" and tot_module and not tot_used and seed_manuscript:
            try:
                tot_result = tot_module.explore(
                    task=f"원고 구조 개선: {director_feedback}",
                    context={"manuscript": seed_manuscript[:3000], "blueprint": blueprint},
                )
                best_path = getattr(tot_result, "best_path", None)
                tot_output = getattr(best_path, "output", "") if best_path else ""
                if tot_output:
                    director_feedback += f"\n[ToT 구조 개선 지침]\n{tot_output[:1000]}"
                    tot_used = True
            except Exception as exc:
                logging.warning(f"[SilentPass:ToT] {exc!s:.120}")
        mad_module = owner.ctx.get_module("multi_agent_deliberation")
        if reject_bucket == "constraint_violation" and mad_module and not mad_used and seed_manuscript:
            try:
                mad_result = mad_module.deliberate(
                    content=seed_manuscript,
                    content_type="manuscript",
                    context={"blueprint": blueprint, "director_feedback": director_feedback},
                )
                mad_output = getattr(mad_result, "consensus_output", "") if mad_result else ""
                if mad_output:
                    director_feedback += f"\n[MAD 제약/합의 개선 지침]\n{mad_output[:1000]}"
                    mad_used = True
            except Exception as exc:
                logging.warning(f"[SilentPass:MAD] {exc!s:.120}")

        return _RejectGuidancePayload(
            director_feedback=director_feedback,
            action_items=action_items,
            reject_bucket=reject_bucket,
            resolved_fix_scope=resolved_fix_scope,
            resolved_fix_scope_reasoning=resolved_fix_scope_reasoning,
            resolved_fix_pack=resolved_fix_pack,
            feedback_provenance=feedback_provenance,
            error_category=error_category,
            tot_used=tot_used,
            mad_used=mad_used,
        )

    @staticmethod
    def _classify_current_violation_families(director_feedback: str, fix_pack: dict | None) -> list[str]:
        """[IFC] Classify violation families for observability."""
        try:
            from modules.core.stage4_immutable_fact_contract import classify_violation_family

            patch_targets_empty = not (fix_pack.get("patch_targets") if isinstance(fix_pack, dict) else False)
            return classify_violation_family(
                rejection_reason=director_feedback,
                fix_pack=fix_pack,
                patch_targets_empty=patch_targets_empty,
            )
        except Exception:
            return []

    def _record_reject_round_metrics(
        self,
        *,
        next_ep: int,
        reject_bucket: str,
        score: int,
        round_num: int,
        selected: str,
        asp_manuscript: str | None,
        tot_used: bool,
        mad_used: bool,
        director_feedback: str,
    ) -> None:
        owner = self.owner
        try:
            owner.ctx.current_project.db.save_cost_record(
                session_id=resolve_logging_session_id(
                    getattr(owner.ctx, "current_project", None),
                    fallback=f"ep_{next_ep}",
                ),
                scope_type="episode",
                scope_id=int(next_ep),
                total_calls=0,
                total_tokens=0,
                total_cost_usd=0.0,
                model_breakdown={
                    "event": "stage4_reject",
                    "bucket": reject_bucket,
                    "score": score,
                    "round": round_num,
                    "ep_attempt_total": round_num + 1,
                    "strategy": selected,
                    "intelligence_used": {
                        "asp": bool(asp_manuscript),
                        "tot": tot_used,
                        "mad": mad_used,
                    },
                },
            )
        except Exception as exc:
            logging.warning(f"[SilentPass:Stage4RejectMetric] {exc!s:.120}")
        owner.ctx.ui.log(f"   ❌ {round_num + 1}차 면담 REJECT. 피드백: {director_feedback}")

    def _run_reject_followup_side_effects(
        self,
        *,
        next_ep: int,
        arc_num: int,
        reject_bucket: str,
        director_feedback: str,
        score: int,
        round_num: int,
        previous_attempt: dict | None = None,
    ) -> str:
        owner = self.owner
        followup_contract = self._build_reject_followup_contract(
            reject_bucket=reject_bucket,
            score=score,
            round_num=round_num,
            previous_attempt=previous_attempt,
        )
        try:
            failure_learner = getattr(owner.ctx, "failure_learner", None)
            if failure_learner is not None and hasattr(failure_learner, "record_failure"):
                failure_learner.record_failure(
                    stage=4,
                    episode=next_ep,
                    arc=arc_num,
                    reason=f"{reject_bucket}: {director_feedback}",
                    details=copy.deepcopy(followup_contract),
                )
        except Exception as failure_err:
            logging.debug(f"[TF7-P1-06] failure_learner Stage4 기록 실패 (비치명): {failure_err}")

        try:
            adaptive_mgr = getattr(owner.ctx, "adaptive_manager", None)
            if adaptive_mgr is not None and hasattr(adaptive_mgr, "record_failure"):
                adaptive_mgr.record_failure(
                    ep_num=next_ep,
                    agent="director",
                    error_info={
                        "reason": director_feedback,
                        **copy.deepcopy(followup_contract),
                    },
                    attempt=round_num + 1,
                )
                if hasattr(adaptive_mgr, "get_injection_prompt"):
                    injection = adaptive_mgr.get_injection_prompt(
                        ep_num=next_ep,
                        agent="director",
                        current_attempt=round_num + 1,
                    )
                    if injection:
                        director_feedback = director_feedback + "\n" + injection
        except Exception as adaptive_err:
            logging.debug(f"[TF7-P1-05] adaptive_manager REJECT 기록 실패 (비치명): {adaptive_err}")

        if getattr(owner.ctx, "quality_dashboard", None):
            try:
                violation = {
                    "type": "director_reject",
                    "description": str(director_feedback),
                }
                if "dominant_contradiction_type" in followup_contract:
                    violation["subtype"] = followup_contract["dominant_contradiction_type"]
                for key in (
                    "contradiction_types",
                    "repair_contract",
                    "scope_authority",
                    "scope_origin",
                    "fix_pack_reason",
                    "fix_pack_origin",
                ):
                    if key in followup_contract:
                        violation[key] = copy.deepcopy(followup_contract[key])
                owner.ctx.quality_dashboard.record_validation(
                    ep_num=next_ep,
                    result={
                        "decision": "REJECT",
                        "score": score,
                        "violations": [violation],
                        "warnings": [],
                    },
                    stage=4,
                )
            except Exception as dashboard_err:
                logging.debug(f"[SILENT] quality_dashboard REJECT: {dashboard_err}")

        return director_feedback

    def _record_reject_attempt_artifact(
        self,
        *,
        next_ep: int,
        round_num: int,
        round_ctx,
        score: int,
        is_patch: bool,
        prev_score: int,
        is_patch_fallback: bool,
        director_feedback: str,
        resolved_fix_scope: str,
        resolved_fix_scope_reasoning: str,
        director_result: dict,
        candidate_key: str,
        previous_attempt: dict | None,
        prev_manuscript: str,
        feedback_provenance: dict[str, str],
        reject_bucket: str,
        error_category: str,
        patch_trace: dict | None,
    ) -> dict:
        owner = self.owner
        sink_source = self._build_reject_sink_source(
            director_result=director_result,
            trace_director_result=None,
            previous_attempt=previous_attempt,
        )
        advisory_gate_semantics = self._enrich_reject_gate_semantics(
            owner._build_gate_semantics_payload(sink_source),
            previous_attempt=previous_attempt,
        )
        advisory_fix_pack = owner._build_fix_pack_payload(sink_source)
        if advisory_fix_pack and not advisory_gate_semantics.get("fix_pack"):
            advisory_gate_semantics["fix_pack"] = copy.deepcopy(advisory_fix_pack)
        sink_fix_pack_origin = sink_source.get("fix_pack_origin")
        if isinstance(sink_fix_pack_origin, dict) and sink_fix_pack_origin and not advisory_gate_semantics.get("fix_pack_origin"):
            advisory_gate_semantics["fix_pack_origin"] = copy.deepcopy(sink_fix_pack_origin)
        advisory_repair_contract = (
            dict(advisory_gate_semantics.get("repair_contract") or {})
            if isinstance(advisory_gate_semantics.get("repair_contract"), dict)
            else {}
        )
        advisory_scope_authority = (
            dict(advisory_gate_semantics.get("scope_authority") or {})
            if isinstance(advisory_gate_semantics.get("scope_authority"), dict)
            else {}
        )
        advisory_fix_pack_origin = (
            dict(advisory_gate_semantics.get("fix_pack_origin") or {})
            if isinstance(advisory_gate_semantics.get("fix_pack_origin"), dict)
            else {}
        )
        patch_advisory_payload = owner._build_stage4_patch_advisory_payload(
            director_result=sink_source,
            patch_trace=patch_trace,
        )
        return owner._record_s4_attempt(
            episode=next_ep,
            round_num=round_num,
            success=False,
            score=score,
            is_patch=is_patch,
            prev_score=prev_score,
            patch_fallback=is_patch_fallback,
            arc=round_ctx.arc_data.get("arc_no", 0),
            verdict="REJECT",
            reject_reason=director_feedback,
            fix_scope=resolved_fix_scope,
            advisory_flags={
                **(dict(getattr(owner, "_last_advisory_summary", None) or {})),
                "gate_semantics": advisory_gate_semantics,
                "fix_pack": patch_advisory_payload.get("fix_pack", advisory_fix_pack),
                "repair_contract": advisory_repair_contract,
                "scope_authority": advisory_scope_authority,
                "fix_pack_origin": advisory_fix_pack_origin,
                "retry_budget_axes": dict(getattr(owner, "_last_retry_budget_axes", {}) or {}),
                **(
                    {
                        key: value
                        for key, value in patch_advisory_payload.items()
                        if key != "fix_pack" and value not in ({}, [], "", None)
                    }
                ),
            },
            model=getattr(getattr(round_ctx, "chief_writer", None), "model_tier", None),
            candidate_key=candidate_key,
            artifact_payload=(previous_attempt or {}).get("best_manuscript", "") or prev_manuscript,
            artifact_kind="rejected_best",
            selection_reason=director_result.get("selection_reason", ""),
            verdict_reason=director_result.get("verdict_reason", ""),
            open_review=director_result.get("open_review", ""),
            fix_scope_reasoning=resolved_fix_scope_reasoning,
            runtime_advisory=feedback_provenance["runtime_advisory"],
            retry_directives=feedback_provenance["retry_directives"],
            error_category=error_category or director_result.get("error_category", ""),
            reject_bucket=reject_bucket,
            score_breakdown=director_result.get("score_breakdown", {}),
        )

    def _sync_reject_result_selection_rationale(
        self,
        *,
        attempt_key: str,
        trace_director_result,
        director_result: dict,
        selection_reason: str,
        verdict_reason: str,
        advisory_warnings: dict | None = None,
    ) -> None:
        current_db = getattr(getattr(self.owner.ctx, "current_project", None), "db", None)
        if current_db is None or not hasattr(current_db, "update_director_selection_rationale"):
            return
        try:
            current_db.update_director_selection_rationale(
                attempt_key=attempt_key,
                selection_reason=selection_reason,
                verdict_reason=verdict_reason,
                fix_scope=(
                    trace_director_result.get(
                        "authoritative_fix_scope",
                        trace_director_result.get("fix_scope", ""),
                    )
                    if isinstance(trace_director_result, dict)
                    else director_result.get(
                        "authoritative_fix_scope",
                        director_result.get("fix_scope", ""),
                    )
                ),
                advisory_warnings=advisory_warnings,
            )
        except Exception as exc:
            logging.debug("[Stage4] director rationale sync failed: %s", exc)

    def _build_reject_logging_payload(
        self,
        *,
        reject_result,
        director_result: dict,
        trace_director_result,
        reason: str,
    ) -> _RejectLoggingPayload:
        previous_attempt = getattr(reject_result, "previous_attempt", None)
        if not isinstance(previous_attempt, dict):
            previous_attempt = {}
        gate_source = self._build_reject_sink_source(
            director_result=director_result,
            trace_director_result=trace_director_result if isinstance(trace_director_result, dict) else None,
            previous_attempt=previous_attempt,
        )
        reject_bucket = str(previous_attempt.get("reject_bucket", "") or "")
        session_selection_reason = str(
            (
                trace_director_result.get("selection_reason")
                or director_result.get("selection_reason", "")
            )
            if isinstance(trace_director_result, dict)
            else director_result.get("selection_reason", "")
        )
        session_verdict_reason = str(
            (
                trace_director_result.get("verdict_reason")
                or reason
                or session_selection_reason
            )
            if isinstance(trace_director_result, dict)
            else (reason or session_selection_reason)
        )
        session_runtime_advisory = str(previous_attempt.get("runtime_advisory", "") or "")
        session_retry_directives = str(previous_attempt.get("retry_directives", "") or "")
        scope_runtime_note, scope_retry_note = self._build_scope_authority_operator_notes(previous_attempt)
        session_runtime_advisory = self._append_operator_note(session_runtime_advisory, scope_runtime_note)
        session_retry_directives = self._append_operator_note(session_retry_directives, scope_retry_note)
        numeric_runtime_note, numeric_retry_note = self._build_numeric_carryover_operator_notes(previous_attempt)
        session_runtime_advisory = self._append_operator_note(session_runtime_advisory, numeric_runtime_note)
        session_retry_directives = self._append_operator_note(session_retry_directives, numeric_retry_note)
        session_gate_semantics = self._enrich_reject_gate_semantics(
            self.owner._build_gate_semantics_payload(gate_source),
            previous_attempt=previous_attempt,
        )
        gate_fix_pack = self.owner._build_fix_pack_payload(gate_source)
        if gate_fix_pack and not session_gate_semantics.get("fix_pack"):
            session_gate_semantics["fix_pack"] = copy.deepcopy(gate_fix_pack)
        gate_fix_pack_origin = gate_source.get("fix_pack_origin")
        if isinstance(gate_fix_pack_origin, dict) and gate_fix_pack_origin and not session_gate_semantics.get("fix_pack_origin"):
            session_gate_semantics["fix_pack_origin"] = copy.deepcopy(gate_fix_pack_origin)

        return _RejectLoggingPayload(
            reject_bucket=reject_bucket,
            reject_artifact_meta=normalize_artifact_meta(
                getattr(reject_result, "attempt_artifact_meta", {}) or {}
            ),
            session_selection_reason=session_selection_reason,
            session_verdict_reason=session_verdict_reason,
            session_runtime_advisory=session_runtime_advisory,
            session_retry_directives=session_retry_directives,
            session_gate_semantics=session_gate_semantics,
            feedback_provenance={
                "director_feedback": str(previous_attempt.get("director_feedback_text", "") or ""),
                "runtime_advisory": session_runtime_advisory,
                "retry_directives": session_retry_directives,
            },
        )

    def _log_reject_session_decision(
        self,
        *,
        next_ep: int,
        round_num: int,
        arc_num: int,
        director_result: dict,
        trace_director_result,
        final_verdict: str,
        final_score: int,
        selected: str,
        reason: str,
        error_category: str,
        attempt_key: str,
        selection_artifact_meta: dict,
        initial_verdict: str,
        initial_score: int,
        reject_logging: _RejectLoggingPayload,
    ) -> None:
        previous_attempt_override: dict[str, object] = {}
        scope_authority = (
            reject_logging.session_gate_semantics.get("scope_authority")
            if isinstance(reject_logging.session_gate_semantics.get("scope_authority"), dict)
            else None
        )
        if isinstance(scope_authority, dict) and scope_authority:
            previous_attempt_override["scope_authority"] = copy.deepcopy(scope_authority)
            fix_scope = str(scope_authority.get("fix_scope", "") or "").strip()
            if fix_scope:
                previous_attempt_override["fix_scope"] = fix_scope
        authoritative_fix_scope = str(
            reject_logging.session_gate_semantics.get("authoritative_fix_scope", "") or ""
        ).strip()
        if authoritative_fix_scope:
            previous_attempt_override["authoritative_fix_scope"] = authoritative_fix_scope
        repair_scope = str(reject_logging.session_gate_semantics.get("repair_scope", "") or "").strip()
        if repair_scope:
            previous_attempt_override["repair_scope"] = repair_scope
        fix_pack_value = reject_logging.session_gate_semantics.get("fix_pack")
        if isinstance(fix_pack_value, dict):
            previous_attempt_override["fix_pack"] = copy.deepcopy(fix_pack_value)
        for key in ("scope_origin", "repair_contract"):
            value = reject_logging.session_gate_semantics.get(key)
            if isinstance(value, dict) and value:
                previous_attempt_override[key] = copy.deepcopy(value)
        sink_source = self._build_reject_sink_source(
            director_result=director_result,
            trace_director_result=trace_director_result if isinstance(trace_director_result, dict) else None,
            previous_attempt=previous_attempt_override,
        )
        self.owner._log_session_decision(
            next_ep=next_ep,
            round_num=round_num,
            arc_num=arc_num,
            verdict=final_verdict,
            score=final_score,
            selected=selected,
            error_category=error_category,
            reason=(
                (trace_director_result.get("verdict_reason") or reason)
                if isinstance(trace_director_result, dict)
                else reason
            ),
            fix_scope=(
                str(sink_source.get("fix_scope", "") or "")
            ),
            open_review=(
                trace_director_result.get("open_review", "")
                if isinstance(trace_director_result, dict)
                else director_result.get("open_review", "")
            ),
            action_items=(
                trace_director_result.get("action_items", [])
                if isinstance(trace_director_result, dict)
                else director_result.get("action_items", [])
            ),
            attempt_key=attempt_key,
            artifact_meta=reject_logging.reject_artifact_meta,
            selection_artifact_meta=selection_artifact_meta,
            initial_verdict=initial_verdict,
            initial_score=initial_score,
            selection_reason=reject_logging.session_selection_reason,
            verdict_reason=reject_logging.session_verdict_reason,
            director_verdict=reject_logging.session_gate_semantics.get("director_verdict", ""),
            gate_basis=reject_logging.session_gate_semantics.get("gate_basis", ""),
            repair_scope=reject_logging.session_gate_semantics.get("repair_scope", ""),
            fix_pack=self.owner._build_fix_pack_payload(sink_source),
            retry_budget_axes=dict(getattr(self.owner, "_last_retry_budget_axes", {}) or {}),
            runtime_advisory=reject_logging.session_runtime_advisory,
            retry_directives=reject_logging.session_retry_directives,
            firewall_triggered=bool(
                sink_source.get("firewall_triggered")
            ),
            firewall_reason=str(sink_source.get("firewall_reason", "") or ""),
            authoritative_fix_scope=str(
                reject_logging.session_gate_semantics.get("authoritative_fix_scope", "") or ""
            ),
            authoritative_fix_scope_violation=(
                reject_logging.session_gate_semantics.get("authoritative_fix_scope_violation")
                if isinstance(
                    reject_logging.session_gate_semantics.get("authoritative_fix_scope_violation"),
                    dict,
                )
                else None
            ),
            scope_origin=(
                reject_logging.session_gate_semantics.get("scope_origin")
                if isinstance(reject_logging.session_gate_semantics.get("scope_origin"), dict)
                else None
            ),
            repair_contract=(
                reject_logging.session_gate_semantics.get("repair_contract")
                if isinstance(reject_logging.session_gate_semantics.get("repair_contract"), dict)
                else None
            ),
            scope_authority=(
                reject_logging.session_gate_semantics.get("scope_authority")
                if isinstance(reject_logging.session_gate_semantics.get("scope_authority"), dict)
                else None
            ),
        )
