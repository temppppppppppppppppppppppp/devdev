"""
Stage4 reject/runtime orchestration split.
"""

import copy
import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from modules.core import stage4_episode_logging as s4_episode_logging
from modules.core.artifact_logging import build_candidate_key, normalize_artifact_meta
from modules.core.logging_keys import build_attempt_key, resolve_logging_session_id
from modules.core.stage4_raw_evidence import (
    build_stage4_raw_rationale_record,
    persist_stage4_raw_rationale_records,
)
from modules.core.stage4_runtime_route import (
    STAGE4_RUNTIME_ROUTE_SCALAR_KEYS,
    copy_stage4_runtime_route_fields,
    is_stage4_nonlocal_repair_route,
    is_stage4_post_select_route,
)

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


@dataclass
class _RejectDecisionSurface:
    selection_reason: str
    verdict_reason: str
    decision_reason: str
    open_review: str
    action_items: list


@dataclass
class _RejectGateSemanticsBundle:
    gate_semantics: dict[str, object]
    repair_contract: dict[str, object]
    scope_authority: dict[str, object]
    fix_pack_origin: dict[str, object]


def _normalize_stage4_strategy_feedback_value(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict | list):
        return json.dumps(value, ensure_ascii=False).strip()
    return str(value or "").strip()


def _normalize_stage4_strategy_feedback_map(strategy_feedback_map: object) -> dict[str, str]:
    if not isinstance(strategy_feedback_map, dict):
        return {}
    normalized: dict[str, str] = {}
    for raw_key, raw_value in strategy_feedback_map.items():
        key = str(raw_key or "").strip()
        if not key:
            continue
        value = _normalize_stage4_strategy_feedback_value(raw_value)
        if value:
            normalized[key] = value
    return normalized


def _build_stage4_selected_strategy_feedback(
    *,
    selection_reason: str,
    verdict_reason: str,
    director_feedback: str,
    runtime_advisory: str,
    retry_directives: str,
    open_review: str,
    action_items: list,
    fix_scope: str,
) -> str:
    lines = ["[Selected Strategy Retry Focus]"]
    if selection_reason:
        lines.append(f"- Previous selection rationale: {selection_reason}")
    if verdict_reason and verdict_reason != selection_reason:
        lines.append(f"- Reject reason: {verdict_reason}")
    if director_feedback and director_feedback not in {selection_reason, verdict_reason}:
        lines.append(f"- Director feedback: {director_feedback}")
    if runtime_advisory:
        lines.append(f"- Runtime advisory: {runtime_advisory}")
    if retry_directives:
        lines.append(f"- Retry directives: {retry_directives}")
    if open_review:
        lines.append(f"- Open review: {open_review}")
    if fix_scope:
        lines.append(f"- Fix scope: {fix_scope}")
    valid_action_items = [str(item or "").strip() for item in (action_items or []) if str(item or "").strip()]
    if valid_action_items:
        lines.append("- Action items:")
        lines.extend(f"  - {item}" for item in valid_action_items[:5])
    return "\n".join(lines) if len(lines) > 1 else ""


def _build_stage4_strategy_feedback_map(
    *,
    previous_attempt: dict | None,
    selected_strategy_key: str,
    selection_reason: str,
    verdict_reason: str,
    director_feedback: str,
    runtime_advisory: str,
    retry_directives: str,
    open_review: str,
    action_items: list,
    fix_scope: str,
) -> dict[str, str]:
    previous_payload = previous_attempt if isinstance(previous_attempt, dict) else {}
    normalized = _normalize_stage4_strategy_feedback_map(previous_payload.get("strategy_feedback_map"))
    selected_feedback = _build_stage4_selected_strategy_feedback(
        selection_reason=selection_reason,
        verdict_reason=verdict_reason,
        director_feedback=director_feedback,
        runtime_advisory=runtime_advisory,
        retry_directives=retry_directives,
        open_review=open_review,
        action_items=action_items,
        fix_scope=fix_scope,
    )
    strategy_key = str(selected_strategy_key or "").strip()
    if strategy_key and selected_feedback:
        normalized[strategy_key] = selected_feedback
    return normalized


def _build_stage4_reject_retry_snapshot_raw_record(
    *,
    attempt_key: str,
    ep_num: int,
    candidate_key: str,
    previous_attempt: dict | None,
) -> dict[str, object] | None:
    attempt_key = str(attempt_key or "").strip()
    if not attempt_key:
        return None
    previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
    payload = {
        "candidate_key": str(candidate_key or "").strip(),
        "previous_attempt": {
            str(key): value
            for key, value in previous_attempt.items()
            if str(key or "").strip() and value not in ("", None, [], {})
        },
    }
    if not payload["candidate_key"]:
        payload.pop("candidate_key", None)
    if not payload.get("previous_attempt"):
        return None
    return build_stage4_raw_rationale_record(
        attempt_key=attempt_key,
        ep_num=int(ep_num or 0),
        payload_kind="reject_retry_snapshot_raw",
        payload=payload,
        payload_meta={
            "record_family": "reject_retry_snapshot",
            "surface": "reject_retry_snapshot_raw",
        },
    )


def _resolve_stage4_scope_origin_fix_scope(*, fix_scope: str, authoritative_fix_scope: str) -> str:
    runtime_scope = str(fix_scope or "").strip().lower()
    authoritative_scope = str(authoritative_fix_scope or "").strip().lower()
    if runtime_scope and runtime_scope != authoritative_scope:
        return "runtime_widened"
    return "director_authoritative"


def _build_stage4_scope_origin_payload(
    *,
    fix_scope: str,
    authoritative_fix_scope: str,
    existing_scope_origin: dict | None = None,
    fix_scope_override: str = "",
) -> dict[str, str]:
    scope_origin = copy.deepcopy(existing_scope_origin) if isinstance(existing_scope_origin, dict) else {}
    computed_fix_scope = _resolve_stage4_scope_origin_fix_scope(
        fix_scope=str(fix_scope or ""),
        authoritative_fix_scope=str(authoritative_fix_scope or ""),
    )
    scope_origin.setdefault("authoritative_fix_scope", "director_authoritative")
    scope_origin.setdefault("repair_scope", "runtime_lane")
    if str(fix_scope_override or "").strip():
        scope_origin["fix_scope"] = str(fix_scope_override).strip()
    else:
        scope_origin.setdefault("fix_scope", computed_fix_scope)
    return scope_origin


def _build_stage4_retry_contract_carryover_fields(
    *,
    previous_attempt: dict | None,
    fix_scope: str,
    authoritative_fix_scope: str,
) -> dict[str, object]:
    previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
    carryover: dict[str, object] = {}
    conflict_contract = previous_attempt.get("conflict_contract")
    if isinstance(conflict_contract, dict) and conflict_contract:
        carryover["conflict_contract"] = copy.deepcopy(conflict_contract)
    reuse_contract = previous_attempt.get("reuse_contract")
    if isinstance(reuse_contract, dict) and reuse_contract:
        carryover["reuse_contract"] = copy.deepcopy(reuse_contract)
    truth_pins = previous_attempt.get("truth_pins")
    if isinstance(truth_pins, dict) and truth_pins:
        carryover["truth_pins"] = copy.deepcopy(truth_pins)
    truth_pin_items = previous_attempt.get("truth_pin_items")
    if not truth_pin_items and isinstance(conflict_contract, dict):
        truth_pin_items = conflict_contract.get("truth_pins")
    if isinstance(truth_pin_items, list) and truth_pin_items:
        carryover["truth_pin_items"] = copy.deepcopy(truth_pin_items)
    for key in ("repair_contract", "scope_authority", "fix_pack_origin"):
        value = previous_attempt.get(key)
        if isinstance(value, dict) and value:
            carryover[key] = copy.deepcopy(value)
    copy_stage4_runtime_route_fields(carryover, previous_attempt)
    carryover["scope_origin"] = _build_stage4_scope_origin_payload(
        fix_scope=fix_scope,
        authoritative_fix_scope=authoritative_fix_scope,
        existing_scope_origin=previous_attempt.get("scope_origin"),
    )
    return carryover


def _build_stage4_reject_retry_contract_projection(
    *,
    owner,
    previous_attempt: dict | None,
    director_result: dict | None,
    fix_scope: str,
    authoritative_fix_scope: str,
    repair_scope: str,
    fix_pack: dict | None,
) -> dict[str, object]:
    projection = _build_stage4_retry_contract_carryover_fields(
        previous_attempt=previous_attempt,
        fix_scope=fix_scope,
        authoritative_fix_scope=authoritative_fix_scope,
    )

    fix_pack_origin = (
        dict(projection.get("fix_pack_origin") or {}) if isinstance(projection.get("fix_pack_origin"), dict) else {}
    )
    if isinstance(fix_pack, dict) and fix_pack and not fix_pack_origin:
        fix_pack_provenance = str(fix_pack.get("provenance", "") or "").strip().lower()
        fix_pack_provenance_sources = [
            str(item).strip() for item in (fix_pack.get("provenance_sources") or []) if str(item).strip()
        ]
        if fix_pack_provenance:
            fix_pack_origin = {
                "provenance": fix_pack_provenance,
                "provenance_sources": fix_pack_provenance_sources,
                "routing_contract": (
                    "runtime_generated_prefers_patch"
                    if fix_pack_provenance in {"runtime_backfilled", "runtime_synthesized"}
                    else "director_authored_allows_inplace"
                ),
            }
    if fix_pack_origin:
        projection["fix_pack_origin"] = fix_pack_origin

    scope_origin = (
        dict(projection.get("scope_origin") or {}) if isinstance(projection.get("scope_origin"), dict) else {}
    )
    if not scope_origin:
        scope_origin = _build_stage4_scope_origin_payload(
            fix_scope=fix_scope,
            authoritative_fix_scope=authoritative_fix_scope,
        )
        projection["scope_origin"] = scope_origin

    gate_semantics = {
        "repair_scope": str(repair_scope or ""),
        "authoritative_fix_scope": str(authoritative_fix_scope or ""),
        "scope_origin": dict(scope_origin or {}),
    }
    source_payload = director_result if isinstance(director_result, dict) else {}
    copy_stage4_runtime_route_fields(projection, source_payload)

    existing_repair_contract = (
        dict(projection.get("repair_contract") or {}) if isinstance(projection.get("repair_contract"), dict) else {}
    )
    derived_repair_contract = owner._build_repair_contract_payload_from_parts(
        gate_semantics=gate_semantics,
        fix_pack=fix_pack,
        source=source_payload,
    )
    merged_repair_contract = {**existing_repair_contract, **dict(derived_repair_contract or {})}
    if merged_repair_contract:
        projection["repair_contract"] = merged_repair_contract

    existing_scope_authority = (
        dict(projection.get("scope_authority") or {}) if isinstance(projection.get("scope_authority"), dict) else {}
    )
    derived_scope_authority = owner._build_scope_authority_payload_from_parts(
        gate_semantics=gate_semantics,
        source={
            **source_payload,
            **projection,
            "fix_scope": str(fix_scope or ""),
            "authoritative_fix_scope": str(authoritative_fix_scope or ""),
            "repair_scope": str(repair_scope or ""),
            "repair_contract": merged_repair_contract,
        },
    )
    merged_scope_authority = {**existing_scope_authority, **dict(derived_scope_authority or {})}
    if merged_scope_authority:
        projection["scope_authority"] = merged_scope_authority

    return projection


def _build_stage4_reject_decision_surface(
    *,
    director_result: dict | None,
    trace_director_result: dict | None,
    fallback_reason: str,
) -> _RejectDecisionSurface:
    director_result = director_result if isinstance(director_result, dict) else {}
    trace_director_result = trace_director_result if isinstance(trace_director_result, dict) else {}
    has_trace = bool(trace_director_result)

    selection_reason = str(
        (trace_director_result.get("selection_reason") or director_result.get("selection_reason", ""))
        if has_trace
        else director_result.get("selection_reason", "")
    )
    verdict_reason = str(
        (trace_director_result.get("verdict_reason") or fallback_reason or selection_reason)
        if has_trace
        else (fallback_reason or selection_reason)
    )
    decision_reason = str(
        (trace_director_result.get("verdict_reason") or fallback_reason) if has_trace else fallback_reason
    )
    open_review = str(
        trace_director_result.get("open_review", "") if has_trace else director_result.get("open_review", "")
    )
    action_items = list(
        trace_director_result.get("action_items", []) if has_trace else director_result.get("action_items", [])
    )
    return _RejectDecisionSurface(
        selection_reason=selection_reason,
        verdict_reason=verdict_reason,
        decision_reason=decision_reason,
        open_review=open_review,
        action_items=action_items,
    )


def _build_stage4_reject_gate_semantics_bundle(
    *,
    owner,
    sink_source: dict | None,
    previous_attempt: dict | None,
    enrich_gate_semantics_fn,
) -> _RejectGateSemanticsBundle:
    gate_semantics = enrich_gate_semantics_fn(
        owner._build_gate_semantics_payload(sink_source),
        previous_attempt=previous_attempt,
    )
    gate_fix_pack = owner._build_fix_pack_payload(sink_source)
    if gate_fix_pack and not gate_semantics.get("fix_pack"):
        gate_semantics["fix_pack"] = copy.deepcopy(gate_fix_pack)
    gate_fix_pack_origin = sink_source.get("fix_pack_origin") if isinstance(sink_source, dict) else None
    if isinstance(gate_fix_pack_origin, dict) and gate_fix_pack_origin and not gate_semantics.get("fix_pack_origin"):
        gate_semantics["fix_pack_origin"] = copy.deepcopy(gate_fix_pack_origin)
    return _RejectGateSemanticsBundle(
        gate_semantics=gate_semantics,
        repair_contract=(
            dict(gate_semantics.get("repair_contract") or {})
            if isinstance(gate_semantics.get("repair_contract"), dict)
            else {}
        ),
        scope_authority=(
            dict(gate_semantics.get("scope_authority") or {})
            if isinstance(gate_semantics.get("scope_authority"), dict)
            else {}
        ),
        fix_pack_origin=(
            dict(gate_semantics.get("fix_pack_origin") or {})
            if isinstance(gate_semantics.get("fix_pack_origin"), dict)
            else {}
        ),
    )


def _build_stage4_reject_previous_attempt_override(
    session_gate_semantics: dict | None,
) -> dict[str, object]:
    gate_semantics = session_gate_semantics if isinstance(session_gate_semantics, dict) else {}
    override: dict[str, object] = {}

    scope_authority = gate_semantics.get("scope_authority")
    scope_authority = copy.deepcopy(scope_authority) if isinstance(scope_authority, dict) else {}
    if scope_authority:
        override["scope_authority"] = scope_authority
        fix_scope = str(scope_authority.get("fix_scope", "") or "").strip()
        if fix_scope:
            override["fix_scope"] = fix_scope

    authoritative_fix_scope = str(
        gate_semantics.get("authoritative_fix_scope")
        or scope_authority.get("authoritative_fix_scope", "")
        or (
            gate_semantics.get("repair_contract", {}).get("authoritative_fix_scope", "")
            if isinstance(gate_semantics.get("repair_contract"), dict)
            else ""
        )
        or ""
    ).strip()
    if authoritative_fix_scope:
        override["authoritative_fix_scope"] = authoritative_fix_scope

    repair_scope = str(
        gate_semantics.get("repair_scope")
        or scope_authority.get("repair_scope", "")
        or (
            gate_semantics.get("repair_contract", {}).get("repair_scope", "")
            if isinstance(gate_semantics.get("repair_contract"), dict)
            else ""
        )
        or ""
    ).strip()
    if repair_scope:
        override["repair_scope"] = repair_scope

    fix_pack = gate_semantics.get("fix_pack")
    if isinstance(fix_pack, dict):
        override["fix_pack"] = copy.deepcopy(fix_pack)

    for key in (
        "scope_origin",
        "repair_contract",
        "fix_pack_origin",
        "authoritative_fix_scope_violation",
        "strong_advisory_escalation",
    ):
        value = gate_semantics.get(key)
        if isinstance(value, dict) and value:
            override[key] = copy.deepcopy(value)
    copy_stage4_runtime_route_fields(override, gate_semantics)

    return override


def _build_stage4_reject_episode_log_kwargs(
    *,
    owner,
    next_ep: int,
    round_num: int,
    sink_source: dict,
    initial_verdict: str,
    initial_score: int,
    final_verdict: str,
    final_score: int,
    is_patch: bool,
    is_patch_fallback: bool,
    tot_used: bool,
    mad_used: bool,
    asp_used: bool,
    model: str | None,
    reject_bucket: str,
    validation_warnings: list,
    feedback_provenance: dict[str, str],
    patch_trace: dict | None,
    arc_num: int,
    reject_artifact_meta: dict[str, str],
    selection_artifact_meta: dict[str, str],
    attempt_key: str,
    selection_reason: str,
    verdict_reason: str,
    session_gate_semantics: dict[str, object],
    runtime_advisory: str,
    retry_directives: str,
) -> dict[str, object]:
    return s4_episode_logging.build_reject_episode_log_append_kwargs(
        request=s4_episode_logging.Stage4RejectEpisodeLogRequest(
            ep_num=next_ep,
            round_num=round_num,
            arc_num=arc_num,
            sink_source=sink_source,
            initial_verdict=initial_verdict,
            initial_score=initial_score,
            final_verdict=final_verdict,
            final_score=final_score,
            is_patch=is_patch,
            is_patch_fallback=is_patch_fallback,
            tot_used=tot_used,
            mad_used=mad_used,
            asp_used=asp_used,
            model=model,
            reject_bucket=reject_bucket,
            validation_warnings=validation_warnings,
            feedback_provenance=feedback_provenance,
            patch_trace=patch_trace,
            reject_artifact_meta=reject_artifact_meta,
            selection_artifact_meta=selection_artifact_meta,
            attempt_key=attempt_key,
        ),
        selection_reason=selection_reason,
        verdict_reason=verdict_reason,
        gate_semantics=session_gate_semantics,
        fix_pack=owner._build_fix_pack_payload(sink_source),
        runtime_advisory=runtime_advisory,
        retry_directives=retry_directives,
    )


def _build_stage4_reject_session_decision_kwargs(
    *,
    owner,
    next_ep: int,
    round_num: int,
    arc_num: int,
    final_verdict: str,
    final_score: int,
    selected: str,
    error_category: str,
    attempt_key: str,
    selection_artifact_meta: dict,
    initial_verdict: str,
    initial_score: int,
    decision_surface: _RejectDecisionSurface,
    reject_logging: _RejectLoggingPayload,
    sink_source: dict,
) -> dict[str, object]:
    return owner._build_stage4_session_decision_kwargs(
        next_ep=next_ep,
        round_num=round_num,
        arc_num=arc_num,
        verdict=final_verdict,
        score=final_score,
        selected=selected,
        error_category=error_category,
        reason=decision_surface.decision_reason,
        fix_scope=str(sink_source.get("fix_scope", "") or ""),
        open_review=decision_surface.open_review,
        action_items=decision_surface.action_items,
        attempt_key=attempt_key,
        artifact_meta=reject_logging.reject_artifact_meta,
        selection_artifact_meta=selection_artifact_meta,
        initial_verdict=initial_verdict,
        initial_score=initial_score,
        selection_reason=reject_logging.session_selection_reason,
        verdict_reason=reject_logging.session_verdict_reason,
        session_gate_semantics=reject_logging.session_gate_semantics,
        fix_pack=owner._build_fix_pack_payload(sink_source),
        retry_budget_axes=dict(getattr(owner, "_last_retry_budget_axes", {}) or {}),
        runtime_advisory=reject_logging.session_runtime_advisory,
        retry_directives=reject_logging.session_retry_directives,
        firewall_triggered=bool(sink_source.get("firewall_triggered")),
        firewall_reason=str(sink_source.get("firewall_reason", "") or ""),
    )


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
    def _has_opening_action_continuity_contract(payload: object) -> bool:
        if isinstance(payload, dict):
            scalar_keys = ("dominant_contradiction_type", "subtype")
            if any(
                str(payload.get(key, "") or "").strip().lower() == "opening_action_continuity" for key in scalar_keys
            ):
                return True
            contradiction_types = payload.get("contradiction_types")
            if isinstance(contradiction_types, list | tuple | set) and any(
                str(item or "").strip().lower() == "opening_action_continuity" for item in contradiction_types
            ):
                return True
            nested_keys = (
                "conflict_contract",
                "repair_contract",
                "authoritative_fix_scope_violation",
                "contradiction_details",
                "violations",
            )
            return any(
                Stage4RejectRuntime._has_opening_action_continuity_contract(payload.get(key)) for key in nested_keys
            )
        if isinstance(payload, list | tuple | set):
            return any(Stage4RejectRuntime._has_opening_action_continuity_contract(item) for item in payload)
        return False

    @staticmethod
    def _should_preserve_post_select_fix_pack(fix_pack: dict | None, *conflict_sources: object) -> bool:
        if any(Stage4RejectRuntime._has_opening_action_continuity_contract(source) for source in conflict_sources):
            return False
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
            *STAGE4_RUNTIME_ROUTE_SCALAR_KEYS,
        ):
            if key not in previous_attempt:
                continue
            value = previous_attempt.get(key)
            merged[key] = copy.deepcopy(value) if isinstance(value, dict | list) else value
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

        copy_stage4_runtime_route_fields(enriched, previous_attempt)
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
        if not is_stage4_nonlocal_repair_route(source):
            return {}

        escalation = source.get("strong_advisory_escalation")
        escalation = escalation if isinstance(escalation, dict) else {}
        local_fix_contract = escalation.get("local_fix_contract")
        local_fix_contract = local_fix_contract if isinstance(local_fix_contract, dict) else {}
        contract_reason = str(local_fix_contract.get("reason", "") or source.get("fix_pack_reason", "") or "").strip()
        contract_message = self.owner._pass_with_fix_contract_message(contract_reason or "non_local_fix_scope")
        runtime_scope = (
            str(source.get("fix_scope") or source.get("repair_scope") or "partial").strip().lower() or "partial"
        )
        authoritative_scope = (
            str(source.get("authoritative_fix_scope") or source.get("fix_scope") or "inplace").strip().lower()
            or "inplace"
        )
        triggered_by = [str(item).strip() for item in list(escalation.get("triggered_by") or []) if str(item).strip()]
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
            str(item).strip() for item in list(previous_attempt.get("contradiction_types") or []) if str(item).strip()
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
            str(item).strip() for item in list(previous_attempt.get("contradiction_types") or []) if str(item).strip()
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
            scope_phrase = f"runtime scope widened from authoritative={authoritative_scope} to runtime={runtime_scope}"
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
        _feedback_provenance = owner._build_stage4_feedback_provenance_payload(
            director_feedback="",
            runtime_advisory="",
            retry_directives="",
        )
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
            current_project = getattr(owner.ctx, "current_project", None)
            current_project_db = getattr(current_project, "db", None)
            retry_attempt_key = build_attempt_key(
                stage=4,
                ep_num=next_ep,
                arc_num=round_ctx.arc_data.get("arc_no", 0),
                attempt_num=round_num + 1,
                session_id=resolve_logging_session_id(current_project),
            )
            previous_attempt["attempt_key"] = retry_attempt_key
            if _candidate_key:
                previous_attempt["candidate_key"] = _candidate_key
            retry_snapshot_raw_record = _build_stage4_reject_retry_snapshot_raw_record(
                attempt_key=retry_attempt_key,
                ep_num=next_ep,
                candidate_key=_candidate_key,
                previous_attempt=previous_attempt,
            )
            persist_stage4_raw_rationale_records(
                project_db=current_project_db,
                records=[retry_snapshot_raw_record] if retry_snapshot_raw_record else [],
                log_prefix="Stage4RejectRetry",
            )
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
                else (director_result.get("fix_scope", "") if isinstance(director_result, dict) else None)
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
            gate_semantics=reject_logging.session_gate_semantics,
            fix_pack=self.owner._build_fix_pack_payload(sink_source),
            retry_budget_axes=dict(previous_attempt.get("retry_budget_axes") or {}),
            preserve_historical_companion=bool(is_patch or trace_patch_trace),
        )
        owner._append_episode_log(
            **_build_stage4_reject_episode_log_kwargs(
                owner=owner,
                next_ep=next_ep,
                round_num=round_num,
                sink_source=sink_source,
                initial_verdict=initial_verdict,
                initial_score=initial_score,
                final_verdict=final_verdict,
                final_score=final_score,
                is_patch=is_patch,
                is_patch_fallback=is_patch_fallback,
                tot_used=tot_used,
                mad_used=mad_used,
                asp_used=bool(asp_manuscript),
                model=getattr(chief_writer, "model_tier", None),
                reject_bucket=reject_logging.reject_bucket,
                validation_warnings=validation_warnings,
                feedback_provenance=reject_logging.feedback_provenance,
                patch_trace=trace_patch_trace,
                arc_num=arc_num,
                reject_artifact_meta=reject_logging.reject_artifact_meta,
                selection_artifact_meta=selection_artifact_meta,
                attempt_key=build_attempt_key(
                    stage=4,
                    ep_num=next_ep,
                    arc_num=arc_num,
                    attempt_num=round_num + 1,
                    session_id=resolve_logging_session_id(getattr(owner.ctx, "current_project", None)),
                ),
                selection_reason=reject_logging.session_selection_reason,
                verdict_reason=reject_logging.session_verdict_reason,
                session_gate_semantics=reject_logging.session_gate_semantics,
                runtime_advisory=reject_logging.session_runtime_advisory,
                retry_directives=reject_logging.session_retry_directives,
            )
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
            and self._should_preserve_post_select_fix_pack(
                snapshot_fix_pack,
                director_result,
                previous_attempt,
            )
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
            snapshot_fix_pack = (
                owner._normalize_fix_pack(snapshot_fix_pack) if preserve_bounded_post_select_fix_pack else {}
            )
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
        strategy_feedback_map = _build_stage4_strategy_feedback_map(
            previous_attempt=previous_attempt,
            selected_strategy_key=str(selected_strategy_key or ""),
            selection_reason=str(snapshot_selection_reason or ""),
            verdict_reason=str(snapshot_verdict_reason or ""),
            director_feedback=str(director_feedback or ""),
            runtime_advisory=str(feedback_provenance.get("runtime_advisory", "") or ""),
            retry_directives=str(feedback_provenance.get("retry_directives", "") or ""),
            open_review=str(snapshot_open_review or ""),
            action_items=action_items,
            fix_scope=str(resolved_fix_scope or ""),
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
            "fix_pack_reason": str(
                owner._evaluate_fix_pack_contract(snapshot_fix_pack).get("reason", "") or ""
            ),  # [TF-4]
            "open_review": snapshot_open_review,
            "error_category": error_category or director_result.get("error_category", ""),
            "violation_families": self._classify_current_violation_families(director_feedback, snapshot_fix_pack),
            "contradiction_types": director_result.get("contradiction_types", []),
            # [pre-rerun] 모순 세부사항 전량 보존 (이전: [:5] 상한으로 진단 손실)
            "contradiction_details": list(director_result.get("contradiction_details", []) or []),
            "firewall_triggered": bool(director_result.get("firewall_triggered")),
            "firewall_reason": director_result.get("firewall_reason", ""),
            "director_feedback_text": str(
                feedback_provenance.get("director_feedback_text", feedback_provenance.get("director_feedback", ""))
                or ""
            ),
            "runtime_advisory": feedback_provenance["runtime_advisory"],
            "retry_directives": feedback_provenance["retry_directives"],
            "strategy_feedback_map": strategy_feedback_map,
            "prior_attempts": owner._inherit_attempt_history(previous_attempt),
        }
        if isinstance(director_result.get("authoritative_fix_scope_violation"), dict):
            reject_attempt["authoritative_fix_scope_violation"] = dict(
                director_result.get("authoritative_fix_scope_violation") or {}
            )
        reject_attempt.update(
            _build_stage4_reject_retry_contract_projection(
                owner=owner,
                previous_attempt=previous_attempt,
                director_result=director_result,
                fix_scope=str(reject_attempt.get("fix_scope", "") or ""),
                authoritative_fix_scope=str(reject_attempt.get("authoritative_fix_scope", "") or ""),
                repair_scope=str(reject_attempt.get("repair_scope", "") or ""),
                fix_pack=snapshot_fix_pack,
            )
        )
        if preserve_bounded_post_select_fix_pack:
            reject_attempt["post_select_fix_pack_preserved"] = True
        # [SSS-T3] Rationale elision marker
        if _rationale_blanked_by:
            reject_attempt["rationale_blanked_by"] = _rationale_blanked_by
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
        # [C-2] Text-based _classify_reject_bucket cannot detect post-select
        # conflict downgrades. Prefer the typed runtime route payload; keep
        # gate_basis only as a compatibility fallback for older records.
        if is_stage4_post_select_route(director_result) and reject_bucket != "post_select_conflict":
            reject_bucket = "post_select_conflict"
            logging.info("[Stage4Gate] reject_bucket promoted to post_select_conflict from runtime route")
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
                        f"[IFC] 불변사실 위반 감지 ({vf_summary}). 국소 패치 대신 재작성 우선 처리가 필요합니다."
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
            preserve_bounded_post_select_fix_pack = self._should_preserve_post_select_fix_pack(
                resolved_fix_pack,
                director_result,
            )
            resolved_fix_scope = "full"
            resolved_fix_pack = (
                owner._normalize_fix_pack(resolved_fix_pack) if preserve_bounded_post_select_fix_pack else {}
            )
            conflict_notice = self._conflict_first_retry_notice()
            if conflict_notice not in director_feedback:
                director_feedback = conflict_notice + "\n" + director_feedback
            resolved_fix_scope_reasoning = (
                f"{resolved_fix_scope_reasoning}\n{conflict_notice}".strip()
                if resolved_fix_scope_reasoning
                else conflict_notice
            )
            if preserve_bounded_post_select_fix_pack:
                preserve_notice = "[TF-F1] bounded post-select fix hints preserved for continuity-guided rewrite trace"
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
        gate_bundle = _build_stage4_reject_gate_semantics_bundle(
            owner=owner,
            sink_source=sink_source,
            previous_attempt=previous_attempt,
            enrich_gate_semantics_fn=self._enrich_reject_gate_semantics,
        )
        patch_advisory_payload = owner._build_stage4_patch_advisory_payload(
            director_result=sink_source,
            patch_trace=patch_trace,
        )
        patch_trace = patch_trace if isinstance(patch_trace, dict) else {}
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
                "gate_semantics": gate_bundle.gate_semantics,
                "fix_pack": patch_advisory_payload.get("fix_pack", gate_bundle.gate_semantics.get("fix_pack", {})),
                "repair_contract": gate_bundle.repair_contract,
                "scope_authority": gate_bundle.scope_authority,
                "fix_pack_origin": gate_bundle.fix_pack_origin,
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
            patch_strategy=str(patch_trace.get("patch_strategy", "") or ""),
            structural_attempted=bool(patch_trace.get("structural_attempted", False)),
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
        gate_semantics: dict | None = None,
        fix_pack: dict | None = None,
        retry_budget_axes: dict | None = None,
        preserve_historical_companion: bool = False,
    ) -> None:
        current_db = getattr(getattr(self.owner.ctx, "current_project", None), "db", None)
        if current_db is None or not hasattr(current_db, "update_director_selection_rationale"):
            return
        if preserve_historical_companion:
            return
        try:
            current_db.update_director_selection_rationale(
                **self.owner._build_stage4_selection_rationale_update_kwargs(
                    attempt_key=attempt_key,
                    trace_director_result=trace_director_result,
                    director_result=director_result,
                    selection_reason=selection_reason,
                    verdict_reason=verdict_reason,
                    advisory_warnings=advisory_warnings,
                    gate_semantics=gate_semantics,
                    fix_pack=fix_pack,
                    retry_budget_axes=retry_budget_axes,
                    prefer_authoritative_scope=True,
                )
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
        decision_surface = _build_stage4_reject_decision_surface(
            director_result=director_result,
            trace_director_result=trace_director_result if isinstance(trace_director_result, dict) else None,
            fallback_reason=reason,
        )
        session_runtime_advisory = str(previous_attempt.get("runtime_advisory", "") or "")
        session_retry_directives = str(previous_attempt.get("retry_directives", "") or "")
        scope_runtime_note, scope_retry_note = self._build_scope_authority_operator_notes(previous_attempt)
        session_runtime_advisory = self._append_operator_note(session_runtime_advisory, scope_runtime_note)
        session_retry_directives = self._append_operator_note(session_retry_directives, scope_retry_note)
        numeric_runtime_note, numeric_retry_note = self._build_numeric_carryover_operator_notes(previous_attempt)
        session_runtime_advisory = self._append_operator_note(session_runtime_advisory, numeric_runtime_note)
        session_retry_directives = self._append_operator_note(session_retry_directives, numeric_retry_note)
        gate_bundle = _build_stage4_reject_gate_semantics_bundle(
            owner=self.owner,
            sink_source=gate_source,
            previous_attempt=previous_attempt,
            enrich_gate_semantics_fn=self._enrich_reject_gate_semantics,
        )

        return _RejectLoggingPayload(
            reject_bucket=reject_bucket,
            reject_artifact_meta=normalize_artifact_meta(getattr(reject_result, "attempt_artifact_meta", {}) or {}),
            session_selection_reason=decision_surface.selection_reason,
            session_verdict_reason=decision_surface.verdict_reason,
            session_runtime_advisory=session_runtime_advisory,
            session_retry_directives=session_retry_directives,
            session_gate_semantics=gate_bundle.gate_semantics,
            feedback_provenance=self.owner._build_stage4_feedback_provenance_payload(
                director_feedback=str(
                    previous_attempt.get("director_feedback_text", previous_attempt.get("director_feedback", "")) or ""
                ),
                runtime_advisory=session_runtime_advisory,
                retry_directives=session_retry_directives,
            ),
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
        previous_attempt_override = _build_stage4_reject_previous_attempt_override(
            reject_logging.session_gate_semantics
        )
        decision_surface = _build_stage4_reject_decision_surface(
            director_result=director_result,
            trace_director_result=trace_director_result if isinstance(trace_director_result, dict) else None,
            fallback_reason=reason,
        )
        sink_source = self._build_reject_sink_source(
            director_result=director_result,
            trace_director_result=trace_director_result if isinstance(trace_director_result, dict) else None,
            previous_attempt=previous_attempt_override,
        )
        self.owner._log_session_decision(
            **_build_stage4_reject_session_decision_kwargs(
                owner=self.owner,
                next_ep=next_ep,
                round_num=round_num,
                arc_num=arc_num,
                final_verdict=final_verdict,
                final_score=final_score,
                selected=selected,
                error_category=error_category,
                attempt_key=attempt_key,
                selection_artifact_meta=selection_artifact_meta,
                initial_verdict=initial_verdict,
                initial_score=initial_score,
                decision_surface=decision_surface,
                reject_logging=reject_logging,
                sink_source=sink_source,
            )
        )
