"""
Stage4 post-select validation/runtime orchestration split.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.core.stage4_interview_round import Stage4InterviewRound


def _build_post_select_conflict_contract(
    conflicts: list[str] | None,
    *,
    contradiction_types: list[str] | None = None,
    contradiction_details: list[str] | None = None,
    bounded_local_fix_hint: bool = False,
    target_kind: str = "",
) -> dict[str, object]:
    entries: list[dict[str, str]] = []
    if not isinstance(conflicts, list):
        return {}

    for raw_line in conflicts:
        line = str(raw_line or "").strip()
        if not line:
            continue
        if "Continuity" in line:
            conflict_type = "continuity"
        elif "History" in line:
            conflict_type = "history"
        else:
            conflict_type = "check_error"
        detail = line.split("]", 1)[1].strip() if "]" in line else line
        expected_truth = detail.split(":", 1)[1].strip() if ":" in detail else detail
        entries.append(
            {
                "conflict_type": conflict_type,
                "conflict_detail": detail,
                "source_episode": "",
                "expected_truth": expected_truth,
            }
        )

    if not entries:
        return {}

    contract: dict[str, object] = {
        "contract_type": "post_select_conflict",
        "mode": "rewrite_with_best_manuscript_reuse",
        "conflicts": entries,
    }
    normalized_contradiction_types: list[str] = []
    for item in contradiction_types or []:
        token = str(item or "").strip()
        if token and token not in normalized_contradiction_types:
            normalized_contradiction_types.append(token)
    if normalized_contradiction_types:
        contract["contradiction_types"] = normalized_contradiction_types
    normalized_contradiction_details: list[str] = []
    for item in contradiction_details or []:
        line = str(item or "").strip()
        if line and line not in normalized_contradiction_details:
            normalized_contradiction_details.append(line)
    if normalized_contradiction_details:
        contract["contradiction_details"] = normalized_contradiction_details
    normalized_target_kind = str(target_kind or "").strip().lower()
    if normalized_target_kind:
        contract["target_kind"] = normalized_target_kind
    if bounded_local_fix_hint:
        contract["bounded_local_fix_hint"] = True
    return contract


def _extract_opening_continuity_pin_metadata(blueprint: dict | None) -> tuple[list[str], list[str]]:
    if not isinstance(blueprint, dict):
        return [], []

    contradiction_types: list[str] = []
    contradiction_details: list[str] = []
    for item in blueprint.get("_continuity_pins") or []:
        if not isinstance(item, dict):
            continue
        pin_type = str(item.get("type", "") or "").strip().lower()
        if pin_type != "opening_action_continuity_pin":
            continue
        if "opening_action_continuity" not in contradiction_types:
            contradiction_types.append("opening_action_continuity")
        before = str(item.get("before", "") or "").strip()
        expected = str(item.get("expected", "") or "").strip()
        observed = str(item.get("observed", "") or "").strip()
        detail_parts = ["opening continuity pin"]
        if before:
            detail_parts.append(f"previous={before}")
        if expected:
            detail_parts.append(f"expected={expected}")
        if observed:
            detail_parts.append(f"observed={observed}")
        detail = " | ".join(detail_parts)
        if detail not in contradiction_details:
            contradiction_details.append(detail)
    return contradiction_types, contradiction_details


def _emit_stage4_ui_log(
    ui,
    message: str,
    *,
    component: str,
    event_kind: str,
    level: str = "warning",
    ep_num: int | None = None,
    round_num: int | None = None,
    meta: dict[str, object] | None = None,
) -> None:
    logger = getattr(ui, "log", None)
    if not callable(logger):
        return
    kwargs: dict[str, object] = {
        "stage": "stage4",
        "component": component,
        "event_kind": event_kind,
        "level": level,
    }
    if ep_num is not None:
        kwargs["ep_num"] = ep_num
    if round_num is not None:
        kwargs["round_num"] = round_num
    if meta:
        kwargs["meta"] = meta
    logger(message, **kwargs)


@dataclass
class _PostSelectConflictClassification:
    conflict_types: list[str]
    has_continuity: bool
    has_history: bool


@dataclass
class _PostSelectContradictionPayload:
    contradiction_types: list[str]
    raw_contradiction_details: list[str]
    compact_contradiction_details: list[str]
    conflict_contract: dict[str, object]


class Stage4PostSelectRuntime:
    """Owns post-select continuity/history downgrade handling for Stage 4."""

    def __init__(self, owner: "Stage4InterviewRound") -> None:
        self.owner = owner

    def build_manuscript_history_for_check(self, prev_manuscripts_text: str, next_ep: int) -> list:
        owner = self.owner
        import re as _re_hist

        history_for_check = []
        for block in str(prev_manuscripts_text or "").split("\n\n---\n\n"):
            match = _re_hist.match(r"^\[[^\d]*(\d+)[^\]]*\]\s*", block)
            if match:
                episode = int(match.group(1))
                text = block[match.end() :]
                if text and len(text) > 100:
                    history_for_check.append({"ep_num": episode, "text": text})

        if not history_for_check:
            for prev_ep in range(max(1, next_ep - 30), next_ep):
                try:
                    prev_ms_data = owner.ctx.current_project.db.get_manuscript(prev_ep)
                    if prev_ms_data:
                        content = (
                            prev_ms_data.get("content", "") if isinstance(prev_ms_data, dict) else str(prev_ms_data)
                        )
                        if content:
                            history_for_check.append({"ep_num": prev_ep, "text": content})
                except Exception as exc:
                    logging.warning(
                        "[SilentPass:InterviewRound] ep%s history load failed: %s",
                        prev_ep,
                        str(exc)[:100],
                    )

        return history_for_check

    def run_post_select_checks(
        self,
        *,
        verdict: str,
        final_manuscript: str,
        final_state_updates: dict,
        next_ep: int,
        round_num: int,
        round_ctx,
        director_result: dict,
        director_feedback: str,
        score: int,
        error_category: str,
        previous_attempt: dict | None,
        stage4_spinner,
        director_memory_context: str,
    ) -> tuple:
        post_select_conflicts = self._collect_post_select_conflicts(
            final_manuscript=final_manuscript,
            next_ep=next_ep,
            round_ctx=round_ctx,
            stage4_spinner=stage4_spinner,
            director_memory_context=director_memory_context,
        )
        if not post_select_conflicts:
            return verdict, director_feedback, previous_attempt, error_category

        classification = self._classify_post_select_conflicts(post_select_conflicts)
        self._emit_post_select_conflict_logs(
            post_select_conflicts=post_select_conflicts,
            classification=classification,
            next_ep=next_ep,
            round_num=round_num,
        )

        verdict = "REJECT"
        director_result = self.owner._apply_director_gate_update(
            director_result,
            final_verdict="REJECT",
            gate_basis="post_select_conflict",
            repair_scope="full",
        )
        director_result["fix_scope"] = "full"
        error_category = self._derive_post_select_error_category(classification)
        director_feedback += "\n" + "\n".join(post_select_conflicts)

        contradiction_payload = self._build_post_select_contradiction_payload(
            director_result=director_result,
            round_ctx=round_ctx,
            post_select_conflicts=post_select_conflicts,
            classification=classification,
        )
        previous_attempt = self._build_post_select_previous_attempt(
            final_manuscript=final_manuscript,
            final_state_updates=final_state_updates,
            score=score,
            director_result=director_result,
            director_feedback=director_feedback,
            prior_attempt=previous_attempt,
            error_category=error_category,
            classification=classification,
            contradiction_payload=contradiction_payload,
        )
        return verdict, director_feedback, previous_attempt, error_category

    def _collect_post_select_conflicts(
        self,
        *,
        final_manuscript: str,
        next_ep: int,
        round_ctx,
        stage4_spinner,
        director_memory_context: str,
    ) -> list[str]:
        owner = self.owner
        post_select_conflicts: list[str] = []
        prev_manuscripts_text = round_ctx.prev_manuscripts_text
        story_context = round_ctx.story_context
        director_agent = owner.ctx.agents.get("director", None)
        run_continuity = next_ep > 1 and final_manuscript
        run_history = (
            prev_manuscripts_text and final_manuscript and hasattr(director_agent, "check_manuscript_history_conflicts")
        )
        if not (run_continuity or run_history):
            return post_select_conflicts

        stage4_spinner.update_detail(f"Ep {next_ep} · post-select checks (parallel)")
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="postselect") as executor:
            fut_continuity = None
            fut_history = None

            if run_continuity:
                fut_continuity = executor.submit(
                    owner.ctx.agents["director"].check_manuscript_continuity_with_cache,
                    new_manuscript=final_manuscript,
                    ep_num=next_ep,
                    db=owner.ctx.current_project.db,
                    limit=10,
                    story_context=story_context,
                    memory_context=director_memory_context,
                )

            if run_history:
                history_for_check = self.build_manuscript_history_for_check(prev_manuscripts_text, next_ep)
                if history_for_check:
                    fut_history = executor.submit(
                        owner.ctx.agents["director"].check_manuscript_history_conflicts,
                        ep_num=next_ep,
                        current_manuscript=final_manuscript,
                        manuscript_history=history_for_check,
                        use_summary=False,
                        story_context=story_context,
                        memory_context=director_memory_context,
                    )

            if fut_continuity is not None:
                try:
                    continuity_check = fut_continuity.result(timeout=120)
                    if continuity_check.get("decision") == "CONFLICT":
                        conflict_msg = continuity_check.get("summary", "Continuity conflict detected")
                        post_select_conflicts.append(f"[Continuity Conflict] {conflict_msg}")
                        owner.ctx.ui.log(f"   [A-3] Post-select continuity conflict: {conflict_msg}")
                except Exception as exc:
                    logging.warning("[FailClosed:SC:PostSelectContinuity] %s", str(exc)[:100])
                    post_select_conflicts.append(f"[Continuity Check Error] 검증 실패 (fail-closed): {exc!s}")

            if fut_history is not None:
                try:
                    conflict_result = fut_history.result(timeout=120)
                    if conflict_result.get("decision") == "CONFLICT":
                        conflict_msg = conflict_result.get("summary", "History conflict detected")
                        post_select_conflicts.append(f"[V67] History Conflict: {conflict_msg}")
                        owner.ctx.ui.log(f"   [A-3] Post-select history conflict: {conflict_msg}")
                except Exception as exc:
                    logging.warning("[FailClosed:SC:PostSelectHistory] %s", str(exc)[:100])
                    post_select_conflicts.append(f"[History Check Error] 검증 실패 (fail-closed): {exc!s}")

        return post_select_conflicts

    @staticmethod
    def _classify_post_select_conflicts(
        post_select_conflicts: list[str],
    ) -> _PostSelectConflictClassification:
        conflict_types: list[str] = []
        for line in post_select_conflicts:
            if "Continuity" in line:
                conflict_types.append("continuity")
            elif "History" in line:
                conflict_types.append("history")
            else:
                conflict_types.append("check_error")
        return _PostSelectConflictClassification(
            conflict_types=conflict_types,
            has_continuity="continuity" in conflict_types,
            has_history="history" in conflict_types,
        )

    def _emit_post_select_conflict_logs(
        self,
        *,
        post_select_conflicts: list[str],
        classification: _PostSelectConflictClassification,
        next_ep: int,
        round_num: int,
    ) -> None:
        owner = self.owner
        for conflict_detail, conflict_type in zip(post_select_conflicts, classification.conflict_types):
            _emit_stage4_ui_log(
                owner.ctx.ui,
                f"   [TF-3 detail] {conflict_detail}",
                component="post_select_validation",
                event_kind="detail",
                ep_num=next_ep,
                round_num=round_num,
                meta={
                    "conflict_type": conflict_type,
                    "conflict_detail": conflict_detail,
                    "conflict_count": len(post_select_conflicts),
                },
            )
        _emit_stage4_ui_log(
            owner.ctx.ui,
            "   [TF-3] Provisional PASS → REJECT downgrade: "
            f"{len(post_select_conflicts)} post-select conflicts ({', '.join(classification.conflict_types)})",
            component="post_select_validation",
            event_kind="policy",
            ep_num=next_ep,
            round_num=round_num,
            meta={
                "conflict_types": list(classification.conflict_types),
                "conflict_count": len(post_select_conflicts),
                "conflict_details": list(post_select_conflicts),
            },
        )

    @staticmethod
    def _derive_post_select_error_category(
        classification: _PostSelectConflictClassification,
    ) -> str:
        if classification.has_continuity and classification.has_history:
            return "POST_SELECT_CONTINUITY_AND_HISTORY"
        if classification.has_continuity:
            return "POST_SELECT_CONTINUITY_CONFLICT"
        if classification.has_history:
            return "POST_SELECT_HISTORY_CONFLICT"
        return "POST_SELECT_CHECK_ERROR"

    def _build_post_select_contradiction_payload(
        self,
        *,
        director_result: dict,
        round_ctx,
        post_select_conflicts: list[str],
        classification: _PostSelectConflictClassification,
    ) -> _PostSelectContradictionPayload:
        owner = self.owner
        contradiction_types: list[str] = []
        for item in director_result.get("contradiction_types", []):
            token = str(item or "").strip()
            if token and token not in contradiction_types:
                contradiction_types.append(token)

        pin_contradiction_types, pin_contradiction_details = (
            _extract_opening_continuity_pin_metadata(getattr(round_ctx, "blueprint", None))
            if classification.has_continuity
            else ([], [])
        )
        for token in pin_contradiction_types:
            if token not in contradiction_types:
                contradiction_types.append(token)

        raw_contradiction_details = list(director_result.get("contradiction_details", []) or [])
        compact_contradiction_details = owner._compact_contradiction_detail_lines(
            raw_contradiction_details,
            max_items=None,
            line_limit=160,
        )
        for line in pin_contradiction_details:
            if line not in compact_contradiction_details:
                compact_contradiction_details.append(line)
        if not compact_contradiction_details:
            compact_contradiction_details = [
                str(item or "").strip() for item in post_select_conflicts if str(item or "").strip()
            ]

        fix_pack_contract = owner._evaluate_fix_pack_contract(director_result.get("fix_pack"))
        normalized_fix_pack = fix_pack_contract.get("fix_pack", {})
        conflict_contract = _build_post_select_conflict_contract(
            post_select_conflicts,
            contradiction_types=contradiction_types,
            contradiction_details=compact_contradiction_details,
            bounded_local_fix_hint=bool(fix_pack_contract.get("ready")),
            target_kind=str(normalized_fix_pack.get("target_kind", "") or ""),
        )

        if contradiction_types:
            director_result["contradiction_types"] = list(contradiction_types)
        elif classification.conflict_types:
            director_result["contradiction_types"] = list(dict.fromkeys(classification.conflict_types))
        if raw_contradiction_details:
            director_result["contradiction_details"] = list(raw_contradiction_details)
        elif compact_contradiction_details:
            director_result["contradiction_details"] = list(compact_contradiction_details)

        return _PostSelectContradictionPayload(
            contradiction_types=contradiction_types,
            raw_contradiction_details=raw_contradiction_details,
            compact_contradiction_details=compact_contradiction_details,
            conflict_contract=conflict_contract,
        )

    def _build_post_select_previous_attempt(
        self,
        *,
        final_manuscript: str,
        final_state_updates: dict,
        score: int,
        director_result: dict,
        director_feedback: str,
        prior_attempt: dict | None,
        error_category: str,
        classification: _PostSelectConflictClassification,
        contradiction_payload: _PostSelectContradictionPayload,
    ) -> dict:
        owner = self.owner
        fix_scope = str(director_result.get("fix_scope", "") or "")
        selected_candidate = director_result.get("selected_candidate") or {}
        if not isinstance(selected_candidate, dict):
            selected_candidate = {}
        selected_strategy_key = selected_candidate.get("strategy", "") or selected_candidate.get("strategy_name", "")
        selection_reason = str(director_result.get("selection_reason", "") or "")
        verdict_reason = str(director_result.get("verdict_reason", "") or "")

        previous_attempt = {
            "best_manuscript": final_manuscript,
            "state_updates": final_state_updates,
            "score": score,
            "fix_scope": "full",
            "authoritative_fix_scope": fix_scope,
            "rejection_reason": director_feedback,
            "selected_strategy": director_result.get("selected_strategy", ""),
            "selected_strategy_key": selected_strategy_key,
            "selection_reason": selection_reason,
            "verdict_reason": verdict_reason,
            "director_verdict": director_result.get("director_verdict", ""),
            "final_verdict": director_result.get("final_verdict", "REJECT"),
            "gate_basis": director_result.get("gate_basis", "post_select_conflict"),
            "repair_scope": director_result.get("repair_scope", "full"),
            "reject_bucket": "post_select_conflict",
            "retry_pathology_source": "post_select_conflict",
            "provisional_pass_downgrade": True,
            "score_breakdown": director_result.get("score_breakdown", {}),
            "consistency_checklist": director_result.get("consistency_checklist", {}),
            "error_category": error_category,
            "open_review": director_result.get("open_review", ""),
            "fix_pack": owner._build_fix_pack_payload(director_result),
            "action_items": list(director_result.get("action_items", []) or []),
            "prior_attempts": owner._inherit_attempt_history(prior_attempt),
        }
        if contradiction_payload.contradiction_types:
            previous_attempt["contradiction_types"] = list(contradiction_payload.contradiction_types)
        elif classification.conflict_types:
            previous_attempt["contradiction_types"] = list(dict.fromkeys(classification.conflict_types))
        if contradiction_payload.raw_contradiction_details:
            previous_attempt["contradiction_details"] = list(contradiction_payload.raw_contradiction_details)
        elif contradiction_payload.compact_contradiction_details:
            previous_attempt["contradiction_details"] = list(contradiction_payload.compact_contradiction_details)
        if contradiction_payload.conflict_contract:
            previous_attempt["conflict_contract"] = contradiction_payload.conflict_contract

        previous_attempt["reuse_contract"] = {
            "mode": "best_manuscript_baseline",
            "baseline_field": "best_manuscript",
            "conflict_field": "conflict_contract",
            "preserve_rationale": True,
        }
        previous_attempt["scope_origin"] = {
            "fix_scope": "post_select_conflict_override",
            "authoritative_fix_scope": "director_authoritative",
            "repair_scope": "runtime_lane",
        }

        repair_contract = owner._build_repair_contract_payload_from_parts(
            gate_semantics={
                "repair_scope": str(previous_attempt.get("repair_scope", "") or ""),
                "authoritative_fix_scope": str(previous_attempt.get("authoritative_fix_scope", "") or ""),
                "scope_origin": dict(previous_attempt.get("scope_origin") or {}),
            },
            fix_pack=previous_attempt.get("fix_pack") or {},
            source=director_result,
        )
        if repair_contract:
            previous_attempt["repair_contract"] = repair_contract

        scope_authority = owner._build_scope_authority_payload_from_parts(
            gate_semantics={
                "repair_scope": str(previous_attempt.get("repair_scope", "") or ""),
                "authoritative_fix_scope": str(previous_attempt.get("authoritative_fix_scope", "") or ""),
                "scope_origin": dict(previous_attempt.get("scope_origin") or {}),
            },
            source=previous_attempt,
        )
        if scope_authority:
            previous_attempt["scope_authority"] = scope_authority

        return previous_attempt
