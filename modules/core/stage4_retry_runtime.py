"""
Stage4 retry/runtime orchestration split.
"""

import copy
import hashlib
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from modules.core.partial_fix_contract import build_partial_fix_eval, normalize_guard_result

if TYPE_CHECKING:
    from modules.core.stage4_interview_round import Stage4InterviewRound


@dataclass
class _RetryLaneRoutingPayload:
    prev_score: int
    fix_scope: str
    fix_pack_contract: dict[str, object]
    reject_bucket: str
    selected_strategy_key: str
    patch_enabled: bool
    force_patch: bool
    use_inplace: bool
    use_patch: bool


@dataclass
class _PassWithFixIterationGatePayload:
    should_abort: bool
    current_audit_result: dict | object
    director_feedback: str
    fix_pack: dict[str, object]


@dataclass
class _PassWithFixPatchAttemptPayload:
    should_abort: bool
    patched_candidates: list[dict]
    patched_manuscript: str
    current_audit_result: dict | object
    director_feedback: str
    patch_trace: dict


@dataclass
class _PassWithFixPatchGuardPayload:
    should_abort: bool
    current_audit_result: dict | object
    director_feedback: str
    patch_trace: dict


@dataclass
class _PassWithFixPatchDeltaPayload:
    patch_trace: dict
    f2_advisory: str


@dataclass
class _PassWithFixReauditPayload:
    should_abort: bool
    re_audit: dict
    applied_patch_history: list[str]


@dataclass
class _PassWithFixReauditVerdictPayload:
    should_break: bool
    fix_ok: bool
    current_ms: str
    current_audit_result: dict | object
    director_result: dict
    final_state_updates: dict
    current_feedback: str


@dataclass
class _PassWithFixLoopFinalizationPayload:
    verdict: str
    final_manuscript: str
    director_result: dict
    director_feedback: str


class Stage4RetryRuntime:
    """Owns retry generation and PASS_WITH_FIX runtime orchestration for Stage 4."""

    def __init__(self, owner: "Stage4InterviewRound") -> None:
        self.owner = owner

    def _build_retry_attempt_key(self, *, ep_num: int, round_num: int, arc_num: int = 0) -> str:
        owner = self.owner
        if hasattr(owner, "_build_round_attempt_key"):
            try:
                return str(owner._build_round_attempt_key(next_ep=ep_num, round_num=round_num, arc_num=arc_num) or "")
            except Exception:
                return ""
        return ""

    @staticmethod
    def _compute_candidate_content_hash(manuscript: str) -> str:
        text = str(manuscript or "")
        if not text.strip():
            return ""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _extract_fix_pack_provenance_fields(
        fix_pack_contract: dict[str, object] | None,
    ) -> tuple[str, list[str], str]:
        fix_pack = fix_pack_contract.get("fix_pack") if isinstance(fix_pack_contract, dict) else {}
        if not isinstance(fix_pack, dict):
            return "", [], ""
        provenance = str(fix_pack.get("provenance", "") or "").strip().lower()
        provenance_sources = [
            str(item).strip() for item in (fix_pack.get("provenance_sources") or []) if str(item).strip()
        ]
        target_kind = str(fix_pack.get("target_kind", "") or "").strip().lower()
        return provenance, provenance_sources, target_kind

    @classmethod
    def _should_prefer_patch_for_runtime_fix_pack(
        cls,
        *,
        patch_enabled: bool,
        prev_manuscript: str,
        fix_scope: str,
        fix_pack_contract: dict[str, object],
    ) -> bool:
        if not patch_enabled or not prev_manuscript:
            return False
        if str(fix_scope or "").strip().lower() != "inplace":
            return False
        if not bool(fix_pack_contract.get("ready")):
            return False
        provenance, _provenance_sources, target_kind = cls._extract_fix_pack_provenance_fields(fix_pack_contract)
        if provenance not in {"runtime_backfilled", "runtime_synthesized"}:
            return False
        return target_kind in {"entity_ref", "local_phrase", "local_sentence"}

    @staticmethod
    def _should_allow_bounded_post_select_patch_retry(
        previous_attempt: dict | None,
        fix_pack_contract: dict[str, object],
    ) -> bool:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        if not previous_attempt:
            return False
        if not bool(fix_pack_contract.get("ready")):
            return False
        if str(previous_attempt.get("reject_bucket", "") or "").strip() != "post_select_conflict":
            return False
        if str(previous_attempt.get("fix_scope", "") or "").strip() != "full":
            return False
        if bool(previous_attempt.get("plateau_detected", False)):
            return False
        if isinstance(previous_attempt.get("qr7_contract"), dict) and previous_attempt.get("qr7_contract"):
            return False

        conflict_contract = previous_attempt.get("conflict_contract")
        if not isinstance(conflict_contract, dict) or not conflict_contract:
            return False
        if not bool(conflict_contract.get("bounded_local_fix_hint")):
            return False

        contract_conflict_types = {
            str(item.get("conflict_type", "") or "").strip().lower()
            for item in (conflict_contract.get("conflicts") or [])
            if isinstance(item, dict) and str(item.get("conflict_type", "") or "").strip()
        }
        if {"continuity", "history"}.issubset(contract_conflict_types):
            return False

        truth_pins = conflict_contract.get("truth_pins") or []
        truth_pin_families = {
            str(item.get("family", "") or "").strip().lower()
            for item in truth_pins
            if isinstance(item, dict) and str(item.get("family", "") or "").strip()
        }
        if truth_pin_families & {"proper_noun_group", "asset_state", "capital_state", "world_fact"}:
            return False

        rewrite_required_reasons = {
            str(item or "").strip().lower()
            for item in (conflict_contract.get("rewrite_required_reasons") or [])
            if str(item or "").strip()
        }
        if rewrite_required_reasons:
            return False

        fix_pack = fix_pack_contract.get("fix_pack")
        if not isinstance(fix_pack, dict):
            return False
        target_kind = str(fix_pack.get("target_kind", "") or "").strip().lower()
        if target_kind not in {"entity_ref", "local_phrase", "local_sentence"}:
            return False

        contradiction_types = {
            str(item or "").strip().lower()
            for item in (conflict_contract.get("contradiction_types") or [])
            if str(item or "").strip()
        }
        effective_types = contradiction_types | contract_conflict_types
        if "proper_noun" in effective_types or "history" in effective_types:
            return False

        evidence_summary = str(fix_pack.get("evidence_summary", "") or "").strip().lower()
        if "flashback continuity backfill" in evidence_summary:
            return bool(effective_types) and effective_types.issubset(
                {
                    "continuity",
                    "timeline",
                    "movement",
                    "location",
                    "facing",
                    "dialogue",
                    "opening_action_continuity",
                }
            )

        return bool(effective_types) and effective_types.issubset(
            {
                "continuity",
                "timeline",
                "movement",
                "location",
                "facing",
                "dialogue",
                "opening_action_continuity",
            }
        )

    def suppress_equivalent_retry_candidates(
        self,
        *,
        candidates: list[dict],
        previous_attempt: dict | None,
        retry_family: str,
        reject_bucket: str,
        fix_pack_reason: str,
        ep_num: int,
        round_num: int,
        arc_num: int = 0,
    ) -> list[dict]:
        owner = self.owner
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        if not candidates or not previous_attempt:
            return candidates
        if self._should_bypass_duplicate_suppression_due_to_reuse_contract(previous_attempt):
            return candidates

        prior_hash = str(previous_attempt.get("content_hash", "") or "").strip()
        if not prior_hash:
            return candidates

        prev_bucket = str(previous_attempt.get("reject_bucket", "") or "").strip()
        prev_fix_pack_reason = str(previous_attempt.get("fix_pack_reason", "") or "").strip()
        prev_retry_axes = previous_attempt.get("retry_budget_axes") if isinstance(previous_attempt, dict) else {}
        prev_retry_family = (
            str(prev_retry_axes.get("repair", "") or prev_retry_axes.get("repair_budget", "") or "").strip()
            if isinstance(prev_retry_axes, dict)
            else ""
        )
        if reject_bucket and prev_bucket and reject_bucket != prev_bucket:
            return candidates
        if fix_pack_reason and prev_fix_pack_reason and fix_pack_reason != prev_fix_pack_reason:
            return candidates
        if retry_family and prev_retry_family and retry_family != prev_retry_family:
            return candidates

        filtered: list[dict] = []
        suppressed = 0
        for candidate in candidates:
            if not isinstance(candidate, dict):
                filtered.append(candidate)
                continue
            manuscript = str(candidate.get("manuscript", "") or "")
            if self._compute_candidate_content_hash(manuscript) == prior_hash:
                suppressed += 1
                continue
            filtered.append(candidate)

        if suppressed <= 0 or not filtered:
            return candidates

        attempt_key = self._build_retry_attempt_key(ep_num=ep_num, round_num=round_num, arc_num=arc_num)
        owner.ctx.ui.log(
            "   [TF-RH1] 동일 retry context의 exact duplicate hash 후보를 억제",
            stage="stage4",
            component="retry_lane",
            ep_num=ep_num,
            round_num=round_num,
            attempt_key=attempt_key,
            event_kind="policy",
            meta={
                "suppressed_count": suppressed,
                "retry_family": retry_family,
                "reject_bucket": reject_bucket,
                "content_hash": prior_hash,
            },
        )
        logging.info(
            "[TF-RH1] suppressed %d duplicate retry candidates (family=%s, bucket=%s, hash=%s)",
            suppressed,
            retry_family,
            reject_bucket,
            prior_hash[:16],
        )
        return filtered

    @staticmethod
    def _should_bypass_duplicate_suppression_due_to_reuse_contract(previous_attempt: dict | None) -> bool:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        if str(previous_attempt.get("best_manuscript_blocked_reason", "") or "").strip():
            return False
        reuse_contract = previous_attempt.get("reuse_contract")
        if not isinstance(reuse_contract, dict) or not reuse_contract:
            return False

        conflict_contract = previous_attempt.get("conflict_contract")
        if not isinstance(conflict_contract, dict) or not conflict_contract:
            return True

        if not bool(conflict_contract.get("bounded_local_fix_hint")):
            return False

        rewrite_required_reasons = {
            str(item or "").strip().lower()
            for item in (conflict_contract.get("rewrite_required_reasons") or [])
            if str(item or "").strip()
        }
        if rewrite_required_reasons:
            return False

        conflict_types = {
            str(item.get("conflict_type", "") or "").strip().lower()
            for item in (conflict_contract.get("conflicts") or [])
            if isinstance(item, dict) and str(item.get("conflict_type", "") or "").strip()
        }
        contradiction_types = {
            str(item or "").strip().lower()
            for item in (conflict_contract.get("contradiction_types") or [])
            if str(item or "").strip()
        }
        effective_types = conflict_types | contradiction_types
        if {"continuity", "history"}.issubset(effective_types):
            return False
        if "history" in effective_types or "proper_noun" in effective_types:
            return False
        return True

    def execute_pass_with_fix_loop(
        self,
        *,
        verdict: str,
        final_manuscript: str,
        final_state_updates: dict,
        director_result: dict,
        director_feedback: str,
        round_ctx,
        round_num: int,
        score: int,
        quality_gate_score: int,
        director_mandatory_context: str,
    ) -> tuple:
        from modules.validation.threshold_helper import _threshold

        owner = self.owner
        max_fix = 3
        current_ms = final_manuscript
        current_fb = owner._extract_fix_feedback(director_result)
        fix_ok = False
        director = owner.ctx.agents.get("director")
        chief_writer = round_ctx.chief_writer
        style_guide = round_ctx.style_guide
        current_audit_result = owner._enforce_pass_with_fix_contract(director_result)
        last_patched_ms = None
        last_patch_trace = {}
        applied_patch_history: list[str] = []

        for fix_i in range(max_fix):
            iteration_gate = self._prepare_pass_with_fix_iteration_gate(
                current_feedback=current_fb,
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                round_ctx=round_ctx,
                round_num=round_num,
            )
            current_audit_result = iteration_gate.current_audit_result
            director_feedback = iteration_gate.director_feedback
            if iteration_gate.should_abort:
                break
            fix_pack = dict(iteration_gate.fix_pack)

            if fix_i == 0:
                ip_rate = owner._get_inplace_success_rate()
                if ip_rate is not None:
                    logging.info("[PF-4] inplace 성공률 %.1f%%", ip_rate)

            owner.ctx.ui.log(f"   🔩 [TF-32-V] PASS_WITH_FIX patch #{fix_i + 1}/{max_fix}")
            patch_attempt = self._run_pass_with_fix_patch_attempt(
                chief_writer=chief_writer,
                round_ctx=round_ctx,
                current_ms=current_ms,
                current_feedback=current_fb,
                fix_index=fix_i,
                style_guide=style_guide,
                fix_pack=fix_pack,
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                last_patch_trace=last_patch_trace,
            )
            current_audit_result = patch_attempt.current_audit_result
            director_feedback = patch_attempt.director_feedback
            last_patch_trace = patch_attempt.patch_trace
            if patch_attempt.should_abort:
                break
            patched = patch_attempt.patched_candidates
            patched_ms = patch_attempt.patched_manuscript

            guard_result = self._run_pass_with_fix_patch_guards(
                current_ms=current_ms,
                patched_ms=patched_ms,
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                patch_trace=last_patch_trace,
            )
            current_audit_result = guard_result.current_audit_result
            director_feedback = guard_result.director_feedback
            last_patch_trace = guard_result.patch_trace
            if guard_result.should_abort:
                break

            last_patched_ms = patched_ms
            delta_payload = self._capture_pass_with_fix_patch_delta(
                current_ms=current_ms,
                patched_ms=patched_ms,
                patch_trace=last_patch_trace,
                max_change_ratio=float(_threshold("patch_mode.inplace_max_change_ratio", 0.30)),
            )
            last_patch_trace = delta_payload.patch_trace
            f2_advisory = delta_payload.f2_advisory

            reaudit_payload = self._run_pass_with_fix_reaudit(
                director=director,
                round_ctx=round_ctx,
                round_num=round_num,
                score=score,
                current_feedback=current_fb,
                current_audit_result=current_audit_result,
                patched_candidates=patched,
                patched_manuscript=patched_ms,
                final_state_updates=final_state_updates,
                director_mandatory_context=director_mandatory_context,
                applied_patch_history=applied_patch_history,
                last_patch_trace=last_patch_trace,
                f2_advisory=f2_advisory,
            )
            applied_patch_history = reaudit_payload.applied_patch_history
            if reaudit_payload.should_abort:
                break
            re_audit = reaudit_payload.re_audit

            verdict_payload = self._apply_pass_with_fix_reaudit_verdict(
                re_audit=re_audit,
                patched_ms=patched_ms,
                current_ms=current_ms,
                current_feedback=current_fb,
                current_audit_result=current_audit_result,
                final_state_updates=final_state_updates,
                director_result=director_result,
                quality_gate_score=quality_gate_score,
                fix_index=fix_i,
            )
            current_ms = verdict_payload.current_ms
            current_audit_result = verdict_payload.current_audit_result
            director_result = verdict_payload.director_result
            final_state_updates = verdict_payload.final_state_updates
            current_fb = verdict_payload.current_feedback
            fix_ok = fix_ok or verdict_payload.fix_ok
            if verdict_payload.should_break:
                break

        finalization = self._finalize_pass_with_fix_loop_outcome(
            fix_ok=fix_ok,
            current_ms=current_ms,
            current_audit_result=current_audit_result,
            director_result=director_result,
            final_manuscript=final_manuscript,
            director_feedback=director_feedback,
            last_patched_ms=last_patched_ms,
            score=score,
        )
        verdict = finalization.verdict
        final_manuscript = finalization.final_manuscript
        director_result = finalization.director_result
        director_feedback = finalization.director_feedback
        return verdict, final_manuscript, final_state_updates, director_result, director_feedback, last_patch_trace

    def generate_candidates(
        self,
        *,
        round_num: int,
        chief_writer,
        director_feedback: str,
        previous_attempt: dict | None,
        prev_manuscript: str,
        style_guide,
        blueprint,
        common_writer_kwargs: dict,
        arc_num: int = 0,
    ) -> tuple[list[dict], bool, bool, int, str | None]:
        owner = self.owner
        is_patch = False
        is_patch_fallback = False
        prev_score = 0
        ep_num = int(common_writer_kwargs.get("ep_num", 0) or 0)
        retry_family = ""
        reject_bucket = ""
        fix_pack_reason = ""
        owner._last_strategy_budget = "full"
        owner._last_strategy_count = 0

        if round_num == 0:
            owner._last_strategy_budget = "full"
            owner._last_strategy_count = 3
            owner._set_retry_budget_axes(
                round_num=round_num,
                repair_budget="ensemble_generation",
                strategy_budget="full",
            )
            candidates = chief_writer.generate_ensemble(**common_writer_kwargs)
        else:
            retry_lane = self._resolve_retry_lane_routing(
                previous_attempt=previous_attempt,
                prev_manuscript=prev_manuscript,
                round_num=round_num,
                ep_num=ep_num,
                arc_num=arc_num,
            )
            prev_score = retry_lane.prev_score
            fix_scope = retry_lane.fix_scope
            fix_pack_contract = retry_lane.fix_pack_contract
            reject_bucket = retry_lane.reject_bucket
            selected_strategy_key = retry_lane.selected_strategy_key
            use_inplace = retry_lane.use_inplace
            use_patch = retry_lane.use_patch
            fix_pack_reason = str(fix_pack_contract.get("reason", "") or "").strip()

            candidates = None
            if fix_scope == "inplace" and not fix_pack_contract.get("ready"):
                logging.info(
                    "[Lane3 Gate] retry inplace skipped: %s",
                    owner._pass_with_fix_contract_message(
                        str(fix_pack_contract.get("reason", "") or "missing_fix_pack")
                    ),
                )
                owner.ctx.ui.log("   🔀 [Lane3 Gate] explicit Fix Pack 없는 inplace retry 금지 → patch/rewrite로 이관")

            if use_inplace:
                candidates, is_patch = self._run_inplace_retry_lane(
                    chief_writer=chief_writer,
                    director_feedback=director_feedback,
                    round_num=round_num,
                    prev_score=prev_score,
                    prev_manuscript=prev_manuscript,
                    style_guide=style_guide,
                    fix_pack_contract=fix_pack_contract,
                    reject_bucket=reject_bucket,
                    previous_attempt=previous_attempt,
                )

            if not candidates:
                candidates, is_patch, is_patch_fallback = self._run_patch_or_rewrite_retry_lane(
                    chief_writer=chief_writer,
                    common_writer_kwargs=common_writer_kwargs,
                    previous_attempt=previous_attempt,
                    prev_manuscript=prev_manuscript,
                    round_num=round_num,
                    prev_score=prev_score,
                    reject_bucket=reject_bucket,
                    fix_scope=fix_scope,
                    selected_strategy_key=selected_strategy_key,
                    use_patch=use_patch,
                )

        asp_manuscript = self._run_asp_correction(
            round_num=round_num,
            previous_attempt=previous_attempt,
            prev_manuscript=prev_manuscript,
            blueprint=blueprint,
            director_feedback=director_feedback,
        )
        if asp_manuscript and candidates:
            candidates = self._apply_asp_candidate_replacement(
                candidates=candidates,
                asp_manuscript=asp_manuscript,
            )

        retry_axes = dict(getattr(owner, "_last_retry_budget_axes", {}) or {})
        retry_family = str(retry_axes.get("repair", "") or retry_axes.get("repair_budget", "") or "").strip()
        if round_num > 0 and candidates:
            candidates = self.suppress_equivalent_retry_candidates(
                candidates=candidates,
                previous_attempt=previous_attempt,
                retry_family=retry_family,
                reject_bucket=reject_bucket,
                fix_pack_reason=fix_pack_reason,
                ep_num=ep_num,
                round_num=round_num,
                arc_num=arc_num,
            )

        return candidates, is_patch, is_patch_fallback, prev_score, asp_manuscript

    def _prepare_pass_with_fix_iteration_gate(
        self,
        *,
        current_feedback: str,
        current_audit_result,
        director_feedback: str,
        round_ctx,
        round_num: int,
    ) -> _PassWithFixIterationGatePayload:
        owner = self.owner
        if not current_feedback:
            empty_feedback_notice = "[TF-32-V] PASS_WITH_FIX 피드백 비어 있음 → retry 경로로 명시 이관"
            logging.warning(
                "[TF-32-V] PASS_WITH_FIX empty feedback abort: ep=%s round=%s", round_ctx.next_ep, round_num
            )
            owner.ctx.ui.log("   ⚠️ [TF-32-V] PASS_WITH_FIX 피드백 비어 있음 — silent break 금지, retry 경로 이관")
            director_feedback = f"{director_feedback}\n{empty_feedback_notice}".strip()
            if isinstance(current_audit_result, dict):
                current_audit_result = dict(current_audit_result)
                current_audit_result.setdefault("verdict", "PASS_WITH_FIX")
                current_audit_result = owner._apply_director_gate_update(
                    current_audit_result,
                    final_verdict="REJECT",
                    gate_basis="empty_feedback_abort",
                )
                current_audit_result["verdict_reason"] = empty_feedback_notice
                current_audit_result["open_review"] = empty_feedback_notice
            return _PassWithFixIterationGatePayload(
                should_abort=True,
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                fix_pack={},
            )

        contract = owner._evaluate_pass_with_fix_contract(current_audit_result)
        if not contract.get("eligible"):
            contract_reason = str(contract.get("reason", "") or "missing_fix_pack")
            contract_notice = "[Lane3 Gate] PASS_WITH_FIX loop abort: " + owner._pass_with_fix_contract_message(
                contract_reason
            )
            logging.warning("[Lane3 Gate] PASS_WITH_FIX loop abort (%s)", contract_reason)
            owner.ctx.ui.log(f"   🔀 [Lane3 Gate] {contract_notice}")
            if isinstance(current_audit_result, dict):
                current_audit_result = owner._enforce_pass_with_fix_contract(current_audit_result)
            director_feedback = f"{director_feedback}\n{contract_notice}".strip()
            return _PassWithFixIterationGatePayload(
                should_abort=True,
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                fix_pack={},
            )

        fix_pack = dict(contract.get("fix_pack") or {})
        fix_scope = current_audit_result.get("fix_scope", "") if isinstance(current_audit_result, dict) else ""
        if fix_scope in ("partial", "full"):
            owner.ctx.ui.log(f"   🔀 [TF-33] fix_scope={fix_scope!r} → inplace 불가, retry 경로 위임")
            return _PassWithFixIterationGatePayload(
                should_abort=True,
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                fix_pack={},
            )

        return _PassWithFixIterationGatePayload(
            should_abort=False,
            current_audit_result=current_audit_result,
            director_feedback=director_feedback,
            fix_pack=fix_pack,
        )

    def _run_pass_with_fix_patch_attempt(
        self,
        *,
        chief_writer,
        round_ctx,
        current_ms: str,
        current_feedback: str,
        fix_index: int,
        style_guide,
        fix_pack: dict[str, object],
        current_audit_result,
        director_feedback: str,
        last_patch_trace: dict,
    ) -> _PassWithFixPatchAttemptPayload:
        owner = self.owner
        try:
            setattr(chief_writer, "_inplace_patch_blueprint", round_ctx.blueprint)
            setattr(chief_writer, "_inplace_patch_genre_name", getattr(round_ctx, "genre_name", ""))
            patched = chief_writer.inplace_patch(
                original_manuscript=current_ms,
                director_feedback=current_feedback,
                attempt_number=fix_index + 1,
                style_guide=style_guide,
                fix_pack=fix_pack,
            )
            patched_ms = patched[0].get("manuscript", "") if patched else ""
            patch_trace = dict(getattr(chief_writer, "_last_inplace_patch_trace", {}) or {})
            if patched:
                patch_trace["patch_strategy"] = str(
                    patch_trace.get("patch_strategy") or patched[0].get("strategy", "") or "inplace_patch"
                )
                patch_trace["patch_round"] = fix_index + 1
                if not patch_trace.get("patch_targets"):
                    patch_trace["patch_targets"] = list(
                        patched[0].get("patch_targets") or fix_pack.get("patch_targets") or []
                    )
                if not patch_trace.get("target_kind"):
                    patch_trace["target_kind"] = str(
                        patch_trace.get("target_kind")
                        or patched[0].get("target_kind", "")
                        or fix_pack.get("target_kind", "")
                        or ""
                    ).strip()
                if not patch_trace.get("patch_target_records"):
                    patch_trace["patch_target_records"] = list(
                        patch_trace.get("patch_target_records")
                        or patched[0].get("patch_target_records")
                        or fix_pack.get("patch_target_records")
                        or []
                    )
                if not patch_trace.get("repair_trace"):
                    patch_trace["repair_trace"] = list(
                        patch_trace.get("repair_trace") or patched[0].get("repair_trace") or []
                    )
                patch_trace["partial_fix_eval"] = build_partial_fix_eval(
                    patch_round=patch_trace.get("patch_round"),
                    is_patch_attempt=True,
                    patch_target_records=list(patch_trace.get("patch_target_records") or []),
                    target_kind=str(patch_trace.get("target_kind", "") or ""),
                    fallback_reason=str(patch_trace.get("fallback_reason", "") or ""),
                )
            return _PassWithFixPatchAttemptPayload(
                should_abort=False,
                patched_candidates=patched or [],
                patched_manuscript=patched_ms,
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                patch_trace=patch_trace,
            )
        except Exception as exc:
            logging.warning(f"[TF-32-V] inplace 실패: {exc!s:.100}")
            exception_notice = (
                f"[Lane3 Emergency] inplace 예외 ({type(exc).__name__}) → local 계약 실패로 간주, "
                "현재 시도는 REJECT, 다음 retry는 partial patch 경로로 이관"
            )
            current_audit_result, director_feedback, patch_trace = owner._mark_pass_with_fix_inplace_contract_fail(
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                patch_trace=last_patch_trace,
                failure_key="inplace_exception",
                notice=exception_notice,
            )
            return _PassWithFixPatchAttemptPayload(
                should_abort=True,
                patched_candidates=[],
                patched_manuscript="",
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                patch_trace=patch_trace,
            )
        finally:
            setattr(chief_writer, "_inplace_patch_blueprint", None)
            setattr(chief_writer, "_inplace_patch_genre_name", "")

    def _run_pass_with_fix_patch_guards(
        self,
        *,
        current_ms: str,
        patched_ms: str,
        current_audit_result,
        director_feedback: str,
        patch_trace: dict,
    ) -> _PassWithFixPatchGuardPayload:
        from modules.validation.threshold_helper import _threshold

        owner = self.owner
        min_patch_len = int(_threshold("patch_mode.min_patched_length", 2000))
        if not patched_ms or len(patched_ms) < min_patch_len:
            logging.warning("[TF-32-V] patch 결과 부족 (len=%d < %d)", len(patched_ms or ""), min_patch_len)
            length_notice = (
                f"[Lane3 Emergency] inplace 결과 길이 {len(patched_ms or '')} < min_patched_length {min_patch_len} "
                "→ local 계약 실패, 현재 시도는 REJECT, 다음 retry는 partial patch 경로로 이관"
            )
            failure_key = "empty_patch" if not patched_ms else "min_patched_length"
            current_audit_result, director_feedback, patch_trace = owner._mark_pass_with_fix_inplace_contract_fail(
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                patch_trace=patch_trace,
                failure_key=failure_key,
                notice=length_notice,
            )
            patch_trace["guard_result"] = normalize_guard_result(
                {
                    "status": "fail",
                    "failure_key": failure_key,
                }
            )
            if isinstance(patch_trace.get("partial_fix_eval"), dict):
                patch_trace["partial_fix_eval"] = {
                    **dict(patch_trace.get("partial_fix_eval") or {}),
                    "fallback_reason": failure_key,
                }
            return _PassWithFixPatchGuardPayload(
                should_abort=True,
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                patch_trace=patch_trace,
            )

        min_preserve = float(_threshold("patch_mode.inplace_min_preserve_ratio", 0.70))
        if len(current_ms) > 0 and len(patched_ms) < len(current_ms) * min_preserve:
            logging.warning(
                "[TF-IPG] patch 축소 감지: %d자 → %d자 (%.0f%%, 하한 %.0f%%) → patch 폐기",
                len(current_ms),
                len(patched_ms),
                len(patched_ms) / len(current_ms) * 100,
                min_preserve * 100,
            )
            preserve_notice = (
                f"[Lane3 Emergency] inplace 보존율 {len(patched_ms) / len(current_ms):.0%} < "
                f"inplace_min_preserve_ratio {min_preserve:.0%} → local 계약 실패, 현재 시도는 REJECT, "
                "다음 retry는 partial patch 경로로 이관"
            )
            current_audit_result, director_feedback, patch_trace = owner._mark_pass_with_fix_inplace_contract_fail(
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                patch_trace=patch_trace,
                failure_key="inplace_min_preserve_ratio",
                notice=preserve_notice,
            )
            patch_trace["guard_result"] = normalize_guard_result(
                {
                    "status": "fail",
                    "failure_key": "inplace_min_preserve_ratio",
                }
            )
            if isinstance(patch_trace.get("partial_fix_eval"), dict):
                patch_trace["partial_fix_eval"] = {
                    **dict(patch_trace.get("partial_fix_eval") or {}),
                    "fallback_reason": "inplace_min_preserve_ratio",
                }
            return _PassWithFixPatchGuardPayload(
                should_abort=True,
                current_audit_result=current_audit_result,
                director_feedback=director_feedback,
                patch_trace=patch_trace,
            )

        return _PassWithFixPatchGuardPayload(
            should_abort=False,
            current_audit_result=current_audit_result,
            director_feedback=director_feedback,
            patch_trace={
                **dict(patch_trace or {}),
                "guard_result": normalize_guard_result({"status": "pass", "failure_key": ""}),
            },
        )

    def _capture_pass_with_fix_patch_delta(
        self,
        *,
        current_ms: str,
        patched_ms: str,
        patch_trace: dict,
        max_change_ratio: float,
    ) -> _PassWithFixPatchDeltaPayload:
        from modules.core.constants import calc_patch_change_ratio, log_patch_diff

        log_patch_diff("S4-Manuscript", current_ms, patched_ms)
        change_ratio = calc_patch_change_ratio(current_ms, patched_ms)
        patch_trace = {
            **(patch_trace or {}),
            "change_ratio": round(float(change_ratio), 4),
            "unchanged_ratio": round(max(0.0, 1.0 - float(change_ratio)), 4),
        }

        f2_advisory = ""
        if change_ratio > max_change_ratio:
            f2_advisory = (
                f"[F-2 경고] InPlace 패치 변경 비율 {change_ratio:.1%} > 임계값 {max_change_ratio:.0%}. "
                "국소 수정이 아닌 대폭 재작성일 수 있음. 품질 저하 여부를 중점 확인하세요."
            )
            logging.warning(
                "[F-2] InPlace 변경 비율 %.1f%% > %.0f%% (S4 원고)", change_ratio * 100, max_change_ratio * 100
            )

        return _PassWithFixPatchDeltaPayload(
            patch_trace=patch_trace,
            f2_advisory=f2_advisory,
        )

    def _run_pass_with_fix_reaudit(
        self,
        *,
        director,
        round_ctx,
        round_num: int,
        score: int,
        current_feedback: str,
        current_audit_result,
        patched_candidates: list[dict],
        patched_manuscript: str,
        final_state_updates: dict,
        director_mandatory_context: str,
        applied_patch_history: list[str],
        last_patch_trace: dict,
        f2_advisory: str,
    ) -> _PassWithFixReauditPayload:
        owner = self.owner
        try:
            patch_state = patched_candidates[0].get("state_updates", {}) if patched_candidates else {}
            merged_state = {**final_state_updates, **patch_state}
            re_candidate = {
                "strategy": "inplace_patch",
                "strategy_name": "InPlace 수정",
                "manuscript": patched_manuscript,
                "title": f"제{round_ctx.next_ep}화",
                "state_updates": merged_state,
            }
            re_val_ctx = {
                "warnings": [
                    f"[TF-35 재심사] InPlace 패치 수정본입니다. 원본 점수: {score}점.",
                    "[TF-35 재심사] 수정 범위: inplace (국소 수정). 전면 재평가가 아닌 수정 부분 중심으로 평가하세요.",
                    f"[TF-35 재심사] 이전 피드백: {current_feedback[:2000]}",
                ],
                "focus_points": [f"[TF-35 재심사] 이전 피드백: {current_feedback[:1000]}"],
            }
            if f2_advisory:
                re_val_ctx["warnings"].append(f2_advisory)
            updated_patch_history = list(applied_patch_history)
            patch_summary = owner._summarize_patch_provenance(
                current_audit_result,
                current_feedback,
                last_patch_trace,
            )
            if patch_summary:
                updated_patch_history.append(patch_summary)
            re_story_context = owner._build_reaudit_story_context(
                round_ctx.story_context,
                updated_patch_history,
            )
            re_audit = director.select_and_judge_ensemble(
                ep_num=round_ctx.next_ep,
                candidates=[re_candidate],
                validation_results=[re_val_ctx],
                blueprint=round_ctx.blueprint,
                previous_ending=round_ctx.prev_ending,
                arc_pos=round_ctx.arc_pos,
                total_eps=round_ctx.total_ep_in_arc,
                retry_count=round_num,
                episode_digest=round_ctx.episode_digest,
                mandatory_context=director_mandatory_context,
                prev_manuscripts_text=round_ctx.prev_manuscripts_text,
                story_context=re_story_context,
            )
            # PASS_WITH_FIX re-audit judges the already-patched manuscript only.
            # Do not let stale advisory caches from the previous round re-escalate
            # a fresh PASS after the targeted local patch has already addressed it.
            advisory_summary_snapshot = copy.deepcopy(getattr(owner, "_last_advisory_summary", None) or {})
            advisory_details_snapshot = copy.deepcopy(getattr(owner, "_last_advisory_details", None) or [])
            advisory_metadata_snapshot = copy.deepcopy(getattr(owner, "_last_advisory_metadata", None) or {})
            try:
                owner._last_advisory_summary = {}
                owner._last_advisory_details = []
                owner._last_advisory_metadata = {}
                re_audit = owner._normalize_director_gate_semantics(re_audit)
                re_audit = owner._enforce_pass_with_fix_contract(re_audit)
            finally:
                owner._last_advisory_summary = advisory_summary_snapshot
                owner._last_advisory_details = advisory_details_snapshot
                owner._last_advisory_metadata = advisory_metadata_snapshot
            return _PassWithFixReauditPayload(
                should_abort=False,
                re_audit=re_audit,
                applied_patch_history=updated_patch_history,
            )
        except Exception:
            logging.exception("[TF-35] 재심사 예외")
            return _PassWithFixReauditPayload(
                should_abort=True,
                re_audit={},
                applied_patch_history=applied_patch_history,
            )

    def _apply_pass_with_fix_reaudit_verdict(
        self,
        *,
        re_audit: dict,
        patched_ms: str,
        current_ms: str,
        current_feedback: str,
        current_audit_result: dict | object,
        final_state_updates: dict,
        director_result: dict,
        quality_gate_score: int,
        fix_index: int,
    ) -> _PassWithFixReauditVerdictPayload:
        owner = self.owner
        re_verdict = re_audit.get("verdict", "REJECT")
        re_score = re_audit.get("score", 0)
        try:
            re_score = int(re_score)
        except (ValueError, TypeError):
            re_score = 0

        owner.ctx.ui.log(f"   🎬 [TF-35] 재심사 #{fix_index + 1}: {re_verdict} (score={re_score})")

        if re_verdict == "PASS":
            if re_score < quality_gate_score:
                owner.ctx.ui.log(f"   ⚠️ [TF-35] 재심사 PASS이나 score={re_score} < {quality_gate_score} → patch 종료")
                return _PassWithFixReauditVerdictPayload(
                    should_break=True,
                    fix_ok=False,
                    current_ms=current_ms,
                    current_audit_result=owner._apply_director_gate_update(
                        re_audit,
                        final_verdict="REJECT",
                        gate_basis="quality_floor_fail",
                    ),
                    director_result=director_result,
                    final_state_updates=final_state_updates,
                    current_feedback=current_feedback,
                )

            final_audit = dict(director_result) if isinstance(director_result, dict) else {}
            if isinstance(re_audit, dict):
                final_audit.update(re_audit)
            final_audit["score"] = re_score

            re_state_updates = re_audit.get("state_updates")
            if isinstance(re_state_updates, dict) and re_state_updates:
                final_state_updates = {**final_state_updates, **re_state_updates}

            return _PassWithFixReauditVerdictPayload(
                should_break=True,
                fix_ok=True,
                current_ms=patched_ms,
                current_audit_result=re_audit,
                director_result=owner._apply_director_gate_update(
                    final_audit,
                    final_verdict="PASS",
                    gate_basis="patch_reaudit_pass",
                ),
                final_state_updates=final_state_updates,
                current_feedback=current_feedback,
            )

        if re_verdict == "PASS_WITH_FIX":
            re_state_updates = re_audit.get("state_updates")
            if isinstance(re_state_updates, dict) and re_state_updates:
                final_state_updates = {**final_state_updates, **re_state_updates}

            return _PassWithFixReauditVerdictPayload(
                should_break=False,
                fix_ok=False,
                current_ms=patched_ms,
                current_audit_result=re_audit,
                director_result=director_result,
                final_state_updates=final_state_updates,
                current_feedback=owner._extract_fix_feedback(re_audit) or current_feedback,
            )

        return _PassWithFixReauditVerdictPayload(
            should_break=True,
            fix_ok=False,
            current_ms=current_ms,
            current_audit_result=owner._apply_director_gate_update(
                re_audit,
                final_verdict="REJECT",
                gate_basis="patch_reaudit_fail",
            ),
            director_result=director_result,
            final_state_updates=final_state_updates,
            current_feedback=current_feedback,
        )

    def _finalize_pass_with_fix_loop_outcome(
        self,
        *,
        fix_ok: bool,
        current_ms: str,
        current_audit_result: dict | object,
        director_result: dict,
        final_manuscript: str,
        director_feedback: str,
        last_patched_ms: str | None,
        score: int,
    ) -> _PassWithFixLoopFinalizationPayload:
        owner = self.owner
        if fix_ok:
            owner.ctx.ui.log("   ✅ [TF-32-V] 원고 수정 완료 → PASS 확정")
            return _PassWithFixLoopFinalizationPayload(
                verdict="PASS",
                final_manuscript=current_ms,
                director_result=owner._apply_director_gate_update(
                    director_result,
                    final_verdict="PASS",
                    gate_basis="patch_reaudit_pass",
                ),
                director_feedback=director_feedback,
            )

        verdict = "REJECT"
        last_verdict = current_audit_result.get("verdict", "") if isinstance(current_audit_result, dict) else ""
        if last_verdict == "PASS_WITH_FIX" and last_patched_ms and last_patched_ms != final_manuscript:
            final_manuscript = last_patched_ms
            last_re_score = current_audit_result.get("score", score)
            try:
                last_re_score = int(last_re_score)
            except (ValueError, TypeError):
                last_re_score = score
            director_result["score"] = last_re_score
            owner.ctx.ui.log(f"   📈 [PF-3] PASS_WITH_FIX 소진 → 패치본 채택 (score={last_re_score})")

        if isinstance(current_audit_result, dict):
            for key in (
                "director_verdict",
                "final_verdict",
                "gate_basis",
                "repair_scope",
                "selection_reason",
                "verdict_reason",
                "open_review",
                "feedback",
                "action_items",
                "selected_candidate",
                "score_breakdown",
                "error_category",
                "contradiction_types",
                "contradiction_details",
                "firewall_triggered",
                "firewall_reason",
                "fix_scope_reasoning",
                "state_updates",
            ):
                if key in current_audit_result:
                    director_result[key] = current_audit_result.get(key)

        last_fix_scope = current_audit_result.get("fix_scope", "") if isinstance(current_audit_result, dict) else ""
        if last_fix_scope:
            director_result["fix_scope"] = last_fix_scope

        director_result = owner._apply_director_gate_update(
            director_result,
            final_verdict=verdict,
            gate_basis=(
                current_audit_result.get("gate_basis", "")
                if isinstance(current_audit_result, dict)
                else "patch_reaudit_fail"
            )
            or "patch_reaudit_fail",
        )
        director_feedback += "\n[TF-32-V] PASS_WITH_FIX 수정 실패 → REJECT"
        owner.ctx.ui.log("   ❌ [TF-32-V] 원고 수정 실패 → REJECT 전환")

        return _PassWithFixLoopFinalizationPayload(
            verdict=verdict,
            final_manuscript=final_manuscript,
            director_result=director_result,
            director_feedback=director_feedback,
        )

    # [Retry lane routing priority]
    # 1. inplace: fix_scope == "inplace" AND fix_pack ready AND no consecutive empty patches
    # 2. patch: ready fix_pack contract required; otherwise fail-closed to rewrite
    # 3. rewrite: full scope, fallback from failed inplace/patch, or IFC escalation
    # 4. ASP correction: runs independently after candidate generation (not mutually exclusive)
    # Consecutive empty patches (missing_patch_targets) escalate from inplace -> rewrite.
    def _resolve_retry_lane_routing(
        self,
        *,
        previous_attempt: dict | None,
        prev_manuscript: str,
        round_num: int,
        ep_num: int = 0,
        arc_num: int = 0,
    ) -> _RetryLaneRoutingPayload:
        from modules.validation.threshold_helper import _threshold

        owner = self.owner
        attempt_key = self._build_retry_attempt_key(ep_num=ep_num, round_num=round_num, arc_num=arc_num)
        try:
            prev_score = int(previous_attempt.get("score", 0)) if previous_attempt else 0
        except (ValueError, TypeError):
            prev_score = 0
        reject_bucket = str(previous_attempt.get("reject_bucket", "") or "") if previous_attempt else ""
        fix_scope = str(previous_attempt.get("fix_scope", "") if previous_attempt else "").strip()
        if reject_bucket == "post_select_conflict" and fix_scope != "full":
            previous_attempt = dict(previous_attempt or {})
            previous_attempt["fix_scope"] = "full"
            fix_scope = "full"
        fix_pack_contract = owner._evaluate_fix_pack_contract(
            previous_attempt.get("fix_pack") if isinstance(previous_attempt, dict) else None
        )
        selected_strategy_key = (
            str(previous_attempt.get("selected_strategy_key", "") or previous_attempt.get("selected_strategy", ""))
            if previous_attempt
            else ""
        )
        patch_enabled = bool(_threshold("feature_flags.enable_patch_mode", True))
        # [TF-4] missing_patch_targets 연속 시 patch 강제 해제 → full rewrite로 escalation
        _prior_attempts = previous_attempt.get("prior_attempts", []) if isinstance(previous_attempt, dict) else []
        _consecutive_empty_patch = (
            not fix_pack_contract.get("ready")
            and fix_pack_contract.get("reason") == "missing_patch_targets"
            and any(
                isinstance(pa, dict) and pa.get("fix_pack_reason") == "missing_patch_targets"
                for pa in _prior_attempts[-2:]
            )
        )
        if _consecutive_empty_patch:
            logging.warning("[TF-4] missing_patch_targets 연속 감지 → patch 해제, full rewrite escalation")
            owner.ctx.ui.log(
                "   [TF-4] patch_targets 연속 부재 → full rewrite로 전환",
                stage="stage4",
                component="retry_lane",
                ep_num=ep_num,
                round_num=round_num,
                attempt_key=attempt_key,
                event_kind="policy",
            )

        bounded_post_select_patch = (
            patch_enabled
            and prev_manuscript
            and not _consecutive_empty_patch
            and self._should_allow_bounded_post_select_patch_retry(previous_attempt, fix_pack_contract)
        )
        runtime_fix_pack_prefers_patch = (
            not _consecutive_empty_patch
            and not bounded_post_select_patch
            and self._should_prefer_patch_for_runtime_fix_pack(
                patch_enabled=patch_enabled,
                prev_manuscript=prev_manuscript,
                fix_scope=fix_scope,
                fix_pack_contract=fix_pack_contract,
            )
        )
        if bounded_post_select_patch:
            repair_contract = owner._build_repair_contract_payload_from_parts(
                gate_semantics={
                    "repair_scope": str((previous_attempt or {}).get("repair_scope", fix_scope) or ""),
                    "authoritative_fix_scope": str((previous_attempt or {}).get("authoritative_fix_scope", "") or ""),
                    "scope_origin": dict((previous_attempt or {}).get("scope_origin") or {}),
                },
                fix_pack=fix_pack_contract.get("fix_pack") or {},
                source=previous_attempt or {},
            )
            owner.ctx.ui.log(
                "   [TF-F2] bounded post-select continuity patch retry 허용",
                stage="stage4",
                component="retry_lane",
                ep_num=ep_num,
                round_num=round_num,
                attempt_key=attempt_key,
                event_kind="policy",
                meta={
                    "reject_bucket": reject_bucket,
                    "target_kind": str((fix_pack_contract.get("fix_pack") or {}).get("target_kind", "") or ""),
                    "reason": "bounded_post_select_localfix",
                    "repair_contract": repair_contract,
                },
            )
        if runtime_fix_pack_prefers_patch:
            provenance, provenance_sources, target_kind = self._extract_fix_pack_provenance_fields(fix_pack_contract)
            repair_contract = owner._build_repair_contract_payload_from_parts(
                gate_semantics={
                    "repair_scope": str((previous_attempt or {}).get("repair_scope", fix_scope) or ""),
                    "authoritative_fix_scope": str((previous_attempt or {}).get("authoritative_fix_scope", "") or ""),
                    "scope_origin": dict((previous_attempt or {}).get("scope_origin") or {}),
                },
                fix_pack=fix_pack_contract.get("fix_pack") or {},
                source=previous_attempt or {},
            )
            owner.ctx.ui.log(
                "   [TF-FP1] runtime-generated local fix-pack -> patch_revision 우선",
                stage="stage4",
                component="retry_lane",
                ep_num=ep_num,
                round_num=round_num,
                attempt_key=attempt_key,
                event_kind="policy",
                meta={
                    "fix_scope": str(fix_scope or ""),
                    "provenance": provenance,
                    "provenance_sources": provenance_sources,
                    "target_kind": target_kind,
                    "reason": "runtime_generated_fix_pack_prefers_patch",
                    "repair_contract": repair_contract,
                },
            )

        force_patch = (
            patch_enabled
            and prev_manuscript
            and reject_bucket == "post_select_conflict"
            and fix_scope != "full"
            and round_num <= 1
            and not _consecutive_empty_patch  # [TF-4]
        )

        use_inplace = (
            patch_enabled
            and prev_manuscript
            and not force_patch
            and not bounded_post_select_patch
            and not runtime_fix_pack_prefers_patch
            and not _consecutive_empty_patch  # [TF-4]
            and fix_scope == "inplace"
            and bool(fix_pack_contract.get("ready"))
        )
        use_patch = (
            not _consecutive_empty_patch  # [TF-4]
            and bool(fix_pack_contract.get("ready"))
            and (
                runtime_fix_pack_prefers_patch
                or bounded_post_select_patch
                or force_patch
                or (
                    patch_enabled
                    and prev_manuscript
                    and (
                        fix_scope in ("inplace", "partial")
                        or (reject_bucket == "post_select_conflict" and fix_scope != "full")
                    )
                )
            )
        )
        if (
            patch_enabled
            and prev_manuscript
            and fix_scope in ("inplace", "partial")
            and not bool(fix_pack_contract.get("ready"))
            and not _consecutive_empty_patch
        ):
            logging.warning("[TF-PATCH-GATE] non-ready fix_pack blocks patch_revision; falling through to rewrite")
            owner.ctx.ui.log(
                "   [TF-PATCH-GATE] non-ready fix_pack -> patch 차단, rewrite 경로 사용",
                stage="stage4",
                component="retry_lane",
                ep_num=ep_num,
                round_num=round_num,
                attempt_key=attempt_key,
                event_kind="policy",
            )
        return _RetryLaneRoutingPayload(
            prev_score=prev_score,
            fix_scope=fix_scope,
            fix_pack_contract=fix_pack_contract,
            reject_bucket=reject_bucket,
            selected_strategy_key=selected_strategy_key,
            patch_enabled=patch_enabled,
            force_patch=force_patch,
            use_inplace=use_inplace,
            use_patch=use_patch,
        )

    def _run_inplace_retry_lane(
        self,
        *,
        chief_writer,
        director_feedback: str,
        round_num: int,
        prev_score: int,
        prev_manuscript: str,
        style_guide,
        fix_pack_contract: dict[str, object],
        reject_bucket: str,
        previous_attempt: dict | None,
    ) -> tuple[list[dict] | None, bool]:
        from modules.validation.threshold_helper import _threshold

        owner = self.owner
        inplace_rate = owner._get_inplace_success_rate()
        if inplace_rate is not None:
            logging.info("[PF-4] inplace 성공률 %.1f%%", inplace_rate)

        logging.info(f"[TF-23] InPlace 진입 (fix_scope='inplace', score={prev_score})")
        owner.ctx.ui.log(f"   🔧 [TF-23] InPlace: fix_scope='inplace', score={prev_score}")
        owner._last_strategy_budget = "inplace"
        owner._last_strategy_count = 1
        owner._set_retry_budget_axes(
            round_num=round_num,
            repair_budget="inplace_local_repair",
            strategy_budget="inplace",
            reject_bucket=reject_bucket,
            previous_attempt=previous_attempt,
        )
        candidates = chief_writer.inplace_patch(
            original_manuscript=prev_manuscript,
            director_feedback=director_feedback,
            attempt_number=round_num + 1,
            style_guide=style_guide,
            fix_pack=dict(fix_pack_contract.get("fix_pack") or {}),
        )
        if not candidates or not any(c.get("manuscript", "").strip() for c in candidates):
            logging.warning("[TF-23] InPlace 실패 → Patch 폴백")
            owner.ctx.ui.log("   ⚠️ [TF-23] InPlace 실패 → Patch 폴백")
            return None, False
        if candidates and prev_manuscript:
            inplace_manuscript = candidates[0].get("manuscript", "")
            inplace_min = int(_threshold("patch_mode.min_patched_length", 2000))
            inplace_preserve = float(_threshold("patch_mode.inplace_min_preserve_ratio", 0.70))
            if len(inplace_manuscript) < inplace_min:
                logging.warning(
                    "[TF-IPG] REJECT경로 patch 분량 부족 (%d < %d) → Patch 폴백",
                    len(inplace_manuscript),
                    inplace_min,
                )
                return None, False
            if len(prev_manuscript) > 0 and len(inplace_manuscript) < len(prev_manuscript) * inplace_preserve:
                logging.warning(
                    "[TF-IPG] REJECT경로 patch 축소 (%d→%d, %.0f%%) → Patch 폴백",
                    len(prev_manuscript),
                    len(inplace_manuscript),
                    len(inplace_manuscript) / len(prev_manuscript) * 100,
                )
                return None, False
        return candidates, True

    def _run_patch_or_rewrite_retry_lane(
        self,
        *,
        chief_writer,
        common_writer_kwargs: dict,
        previous_attempt: dict | None,
        prev_manuscript: str,
        round_num: int,
        prev_score: int,
        reject_bucket: str,
        fix_scope: str,
        selected_strategy_key: str,
        use_patch: bool,
    ) -> tuple[list[dict], bool, bool]:
        owner = self.owner
        candidates = None
        is_patch = False
        is_patch_fallback = False

        if use_patch:
            is_patch = True
            logging.info(f"[Phase 3-5B] 패치 모드 진입 (score={prev_score}, round={round_num})")
            owner.ctx.ui.log(f"   🔧 [Phase 3-5B] 패치 모드: score={prev_score}, 원본 보존 수정")
            owner._last_strategy_budget = "patch"
            owner._last_strategy_count = 1
            owner._set_retry_budget_axes(
                round_num=round_num,
                repair_budget="patch_revision",
                strategy_budget="patch",
                reject_bucket=reject_bucket,
                previous_attempt=previous_attempt,
            )
            candidates = chief_writer.patch_with_feedback(
                **common_writer_kwargs,
                original_manuscript=prev_manuscript,
                previous_attempt=previous_attempt,
                attempt_number=round_num + 1,
            )
            if not candidates:
                is_patch_fallback = True
                logging.warning("[Phase 3-5B] 패치 실패, full rewrite 폴백")
                owner.ctx.ui.log("   ⚠️ [Phase 3-5B] 패치 실패 → 전면 재작성 폴백")

        if not candidates:
            regen_kwargs, strategy_budget, strategy_count = owner._build_retry_regenerate_kwargs(
                reject_bucket=reject_bucket,
                fix_scope=fix_scope,
                selected_strategy_key=selected_strategy_key,
                common_writer_kwargs=common_writer_kwargs,
            )
            owner._last_strategy_budget = strategy_budget
            owner._last_strategy_count = strategy_count
            owner._set_retry_budget_axes(
                round_num=round_num,
                repair_budget="rewrite_regenerate",
                strategy_budget=strategy_budget,
                reject_bucket=reject_bucket,
                previous_attempt=previous_attempt,
            )
            candidates = chief_writer.regenerate_with_feedback(
                **regen_kwargs,
                previous_attempt=previous_attempt,
                attempt_number=round_num + 1,
            )

        return candidates, is_patch, is_patch_fallback

    def _run_asp_correction(
        self,
        *,
        round_num: int,
        previous_attempt: dict | None,
        prev_manuscript: str,
        blueprint,
        director_feedback: str,
    ) -> str | None:
        owner = self.owner
        asp_manuscript = None
        asp_module = owner.ctx.get_module("adversarial_self_play")
        if round_num >= 2 and asp_module and previous_attempt:
            try:
                if prev_manuscript:
                    owner.ctx.ui.log(f"   🔥 [ASP] 레드팀 교정 발동 (재시도 {round_num + 1}회차)")
                    asp_context = {}
                    if blueprint:
                        asp_context["blueprint"] = blueprint
                    if director_feedback:
                        asp_context["director_feedback"] = director_feedback
                    asp_result = asp_module.generate_with_adversary(
                        initial_content=prev_manuscript,
                        content_type="manuscript",
                        context=asp_context,
                    )
                    if asp_result and hasattr(asp_result, "final_output") and asp_result.final_output:
                        asp_manuscript = asp_result.final_output
                        owner.ctx.ui.log(
                            f"   ✅ [ASP] 교정 완료 (delta: +{getattr(asp_result, 'improvement_delta', '?')})"
                        )
            except Exception as exc:
                logging.warning(f"[SilentPass:ASP] {exc!s:.200}")
        return asp_manuscript

    def _apply_asp_candidate_replacement(
        self,
        *,
        candidates: list[dict],
        asp_manuscript: str,
    ) -> list[dict]:
        owner = self.owner
        if len(candidates) >= 3:
            worst_idx = 0
            worst_len = len(candidates[0].get("manuscript", ""))
            for candidate_idx in range(1, len(candidates)):
                candidate_len = len(candidates[candidate_idx].get("manuscript", ""))
                if candidate_len < worst_len:
                    worst_len = candidate_len
                    worst_idx = candidate_idx
            owner.ctx.ui.log(
                f"   🔄 [TF-25-01] ASP 교정 후보가 기존 후보 {worst_idx + 1}번 교체 (분량 최저 {worst_len}자)"
            )
            candidates[worst_idx] = {"manuscript": asp_manuscript, "strategy": "asp_correction"}
            return candidates

        candidates.append({"manuscript": asp_manuscript, "strategy": "asp_correction"})
        return candidates
