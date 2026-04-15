"""
[B-1-3] Stage4 Interview Round — 단일 면담 라운드 실행.
"""

import copy
import inspect
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

from modules.core import stage4_episode_logging as s4_episode_logging
from modules.core.artifact_logging import (
    build_candidate_key,
    normalize_artifact_meta,
    snapshot_logged_artifact,
)
from modules.core.constants import smart_truncate
from modules.core.context_advisor import RetrievalSources
from modules.core.jsonl_io import append_jsonl_record
from modules.core.logging_keys import build_attempt_key, resolve_logging_session_id
from modules.core.partial_fix_contract import (
    build_partial_fix_eval,
    normalize_guard_result,
    normalize_patch_target_records,
    normalize_repair_trace_entries,
)
from modules.core.soft_failure import resolve_project_log_dir
from modules.core.stage4_director_runtime import Stage4DirectorRuntime
from modules.core.stage4_postselect_runtime import (
    Stage4PostSelectRuntime,
    _emit_stage4_ui_log,
)
from modules.core.stage4_raw_evidence import (
    build_stage4_raw_rationale_record,
    persist_stage4_raw_rationale_records,
)
from modules.core.stage4_reject_runtime import Stage4RejectRuntime
from modules.core.stage4_retry_runtime import Stage4RetryRuntime

_DB_ADVISORY_NOTICE = "(Python 자동 감지 — 오탐 가능, 참고용)"
_RETRY_ADVISORY_MARKER = "[Advisory 핵심 요약 - 재시도 시 반영]"
_RETRY_SYSTEM_PREFIXES = ("[연속성 충돌]", "[Continuity Conflict]", "[V67]", "[CoVe]", "[ToT", "[MAD")
_RETRY_PERSISTENT_DIRECTIVE_PREFIXES = (
    "[IFC]",
    "[Conflict-first retry]",
    "[Lane3 Gate]",
    "[A-4 continuity replay]",
)
_WRITER_BLUEPRINT_UI_CONTAMINATION_MARKERS = (
    "상태창",
    "상태 창",
    "시스템 메시지",
    "시스템 창",
    "status window",
    "system window",
    "system message",
    "홀로그램",
    "hologram",
    "퀘스트 창",
)


def _parse_retry_advisory_round_tag(line: str) -> int | None:
    stripped = str(line or "").strip()
    if not stripped.startswith("- [R"):
        return None
    tag_end = stripped.find("]", 4)
    if tag_end == -1:
        return None
    try:
        return int(stripped[4:tag_end])
    except ValueError:
        return None


def _strip_retry_advisory_round_tag(line: str) -> str:
    stripped = str(line or "").strip()
    if not stripped.startswith("- [R"):
        return stripped
    tag_end = stripped.find("]", 4)
    if tag_end == -1:
        return stripped
    remainder = stripped[tag_end + 1 :].strip()
    return f"- {remainder}".strip() if remainder else ""


def _is_retry_advisory_line(line: str) -> bool:
    return _strip_retry_advisory_round_tag(line).startswith("- ")


def _tag_retry_advisory_line(line: str, *, round_num: int) -> str:
    normalized = _strip_retry_advisory_round_tag(line)
    body = normalized[2:].strip() if normalized.startswith("- ") else normalized
    return f"- [R{round_num}] {body}".strip() if body else ""


def _is_persistent_retry_directive_line(line: str) -> bool:
    stripped = str(line or "").strip()
    return any(stripped.startswith(prefix) for prefix in _RETRY_PERSISTENT_DIRECTIVE_PREFIXES)


def _has_writer_blueprint_ui_contamination(text: object) -> bool:
    lowered = str(text or "").strip().lower()
    if not lowered:
        return False
    return any(marker.lower() in lowered for marker in _WRITER_BLUEPRINT_UI_CONTAMINATION_MARKERS)


def _sanitize_writer_blueprint_text(text: object) -> str:
    raw = str(text or "").strip()
    if not raw or not _has_writer_blueprint_ui_contamination(raw):
        return raw
    if "\n" not in raw:
        return ""
    kept_lines = [
        line.rstrip() for line in raw.splitlines() if line.strip() and not _has_writer_blueprint_ui_contamination(line)
    ]
    return "\n".join(kept_lines).strip()


def _sanitize_writer_blueprint_payload(value: object) -> object:
    if isinstance(value, dict):
        return {key: _sanitize_writer_blueprint_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        cleaned_items = []
        for item in value:
            cleaned = _sanitize_writer_blueprint_payload(item)
            if cleaned in ("", [], {}):
                continue
            cleaned_items.append(cleaned)
        return cleaned_items
    if isinstance(value, str):
        return _sanitize_writer_blueprint_text(value)
    return value


@dataclass
class _GenerationPhaseResult:
    candidates: list[dict]
    director_feedback: str
    is_patch: bool
    is_patch_fallback: bool
    prev_score: int
    prev_manuscript: str
    tot_used: bool
    mad_used: bool
    asp_manuscript: str | None
    empty_result: object | None = None


@dataclass
class _RoundExecutionSetupResult:
    chief_writer: object
    next_ep: int
    blueprint: dict
    style_guide: str
    mandatory_context: str
    writing_directive: str
    common_writer_kwargs: dict
    director_feedback: str


@dataclass
class _RoundOutcomeTracePayload:
    trace_director_result: object
    final_verdict: str
    final_score: int
    trace_patch_trace: dict
    is_patch: bool
    validation_warnings: list[str]


@dataclass
class _PassResultLoggingPayload:
    log_artifact_meta: dict[str, str]
    session_selection_reason: str
    session_verdict_reason: str
    session_runtime_advisory: str
    session_retry_directives: str
    session_gate_semantics: dict[str, object]
    session_fix_pack: dict[str, object] | None = None


@dataclass
class _PassDecisionSurface:
    selection_reason: str
    verdict_reason: str
    decision_reason: str
    open_review: str
    action_items: list
    fix_scope: str
    firewall_triggered: bool
    firewall_reason: str


@dataclass
class _VerdictProcessingPayload:
    pass_result: object | None
    director_feedback: str
    previous_attempt: dict | None
    trace_meta: dict


@dataclass
class _PositiveVerdictSeedPayload:
    next_ep: int
    initial_selected_candidate: dict
    final_manuscript: str
    final_title: str
    final_state_updates: dict


@dataclass
class _PositiveVerdictTransitionPayload:
    verdict: str
    director_feedback: str
    previous_attempt: dict | None
    error_category: str
    final_manuscript: str
    final_state_updates: dict
    director_result: dict
    patch_trace: dict
    final_score: int


@dataclass
class _Stage4AttemptPreludePayload:
    duration_ms: int | None
    token_cost: float
    session_id: str | None
    attempt_key: str
    normalized_patch_strategy: str
    artifact_meta: dict[str, str]


@dataclass
class _Stage4AttemptContractPacket:
    advisory_flags: dict[str, object]
    gate_semantics: dict[str, object]
    fix_pack: dict[str, object]
    repair_contract: dict[str, object]
    scope_authority: dict[str, object]
    retry_budget_axes: dict[str, object]
    verdict_layers: dict[str, object]


def _build_stage4_pass_carryover_linkage(previous_attempt: dict | None) -> dict[str, object]:
    previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
    payload: dict[str, object] = {}
    prior_conflict = previous_attempt.get("conflict_contract")
    if isinstance(prior_conflict, dict) and prior_conflict:
        payload["conflict_resolution_linkage"] = {
            "resolved_from": "prior_attempt_conflict",
            "original_contract_type": str(prior_conflict.get("contract_type", "") or ""),
            "conflict_count": len(prior_conflict.get("conflicts", []) or []),
        }
    prior_reuse = previous_attempt.get("reuse_contract")
    if isinstance(prior_reuse, dict) and prior_reuse:
        payload["reuse_contract"] = dict(prior_reuse)
    return payload


def _build_stage4_pass_decision_surface(
    *,
    director_result: dict | None,
    trace_director_result: dict | None,
    fallback_reason: str,
) -> _PassDecisionSurface:
    director_payload = director_result if isinstance(director_result, dict) else {}
    trace_payload = trace_director_result if isinstance(trace_director_result, dict) else {}
    has_trace = bool(trace_payload)
    selection_reason = str(
        (trace_payload.get("selection_reason") or director_payload.get("selection_reason", ""))
        if has_trace
        else director_payload.get("selection_reason", "")
    )
    verdict_reason = str(
        (trace_payload.get("verdict_reason") or fallback_reason or selection_reason)
        if has_trace
        else (fallback_reason or selection_reason)
    )
    decision_reason = str((trace_payload.get("verdict_reason") or fallback_reason) if has_trace else fallback_reason)
    open_review = str(trace_payload.get("open_review", "") if has_trace else director_payload.get("open_review", ""))
    action_items = list(
        trace_payload.get("action_items", []) if has_trace else director_payload.get("action_items", [])
    )
    fix_scope = str(trace_payload.get("fix_scope", "") if has_trace else director_payload.get("fix_scope", ""))
    firewall_triggered = bool(
        trace_payload.get("firewall_triggered") if has_trace else director_payload.get("firewall_triggered")
    )
    firewall_reason = str(
        trace_payload.get("firewall_reason", "") if has_trace else director_payload.get("firewall_reason", "")
    )
    return _PassDecisionSurface(
        selection_reason=selection_reason,
        verdict_reason=verdict_reason,
        decision_reason=decision_reason,
        open_review=open_review,
        action_items=action_items,
        fix_scope=fix_scope,
        firewall_triggered=firewall_triggered,
        firewall_reason=firewall_reason,
    )


def _build_stage4_pass_episode_log_kwargs(
    *,
    owner,
    ep_num: int,
    round_num: int,
    director_result: dict,
    trace_director_result: dict | None,
    director_feedback: str,
    initial_verdict: str,
    initial_score: int,
    final_verdict: str,
    final_score: int,
    is_patch: bool,
    is_patch_fallback: bool,
    tot_used: bool,
    mad_used: bool,
    asp_manuscript: str,
    chief_writer,
    validation_warnings: list[str],
    final_warnings: list[str],
    patch_trace: dict | None,
    logging_payload: _PassResultLoggingPayload,
    selection_artifact_meta: dict,
    arc_num: int,
) -> dict[str, object]:
    trace_verdict_reason = None
    if isinstance(trace_director_result, dict):
        trace_verdict_reason = trace_director_result.get("verdict_reason")
    return s4_episode_logging.build_pass_episode_log_append_kwargs(
        request=s4_episode_logging.Stage4PassEpisodeLogRequest(
            ep_num=ep_num,
            round_num=round_num,
            arc_num=arc_num,
            director_result=director_result,
            director_feedback=director_feedback,
            trace_verdict_reason=trace_verdict_reason,
            initial_verdict=initial_verdict,
            initial_score=initial_score,
            final_verdict=final_verdict,
            final_score=final_score,
            is_patch=is_patch,
            is_patch_fallback=is_patch_fallback,
            tot_used=tot_used,
            mad_used=mad_used,
            asp_used=bool(asp_manuscript),
            model_tier=getattr(chief_writer, "model_tier", None),
            validation_warnings=validation_warnings,
            final_warnings=final_warnings,
            patch_trace=patch_trace,
            session_runtime_advisory=logging_payload.session_runtime_advisory,
            session_retry_directives=logging_payload.session_retry_directives,
            log_artifact_meta=logging_payload.log_artifact_meta,
            selection_artifact_meta=selection_artifact_meta,
            session_id=resolve_logging_session_id(getattr(owner.ctx, "current_project", None)),
        ),
        selection_reason=logging_payload.session_selection_reason,
        verdict_reason=logging_payload.session_verdict_reason,
        gate_semantics=logging_payload.session_gate_semantics,
        fix_pack=dict(logging_payload.session_fix_pack or {}),
        runtime_advisory=logging_payload.session_runtime_advisory,
        retry_directives=logging_payload.session_retry_directives,
    )


def _build_stage4_pass_session_decision_kwargs(
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
    decision_surface: _PassDecisionSurface,
    logging_payload: _PassResultLoggingPayload,
) -> dict[str, object]:
    session_fix_pack = dict(
        logging_payload.session_fix_pack or owner._build_fix_pack_payload(logging_payload.session_gate_semantics) or {}
    )
    return owner._build_stage4_session_decision_kwargs(
        next_ep=next_ep,
        round_num=round_num,
        arc_num=arc_num,
        verdict=final_verdict,
        score=final_score,
        selected=selected,
        error_category=error_category,
        reason=decision_surface.decision_reason,
        fix_scope=decision_surface.fix_scope,
        open_review=decision_surface.open_review,
        action_items=decision_surface.action_items,
        attempt_key=attempt_key,
        artifact_meta=logging_payload.log_artifact_meta,
        selection_artifact_meta=selection_artifact_meta,
        initial_verdict=initial_verdict,
        initial_score=initial_score,
        selection_reason=logging_payload.session_selection_reason,
        verdict_reason=logging_payload.session_verdict_reason,
        session_gate_semantics=logging_payload.session_gate_semantics,
        fix_pack=session_fix_pack,
        retry_budget_axes=dict(getattr(owner, "_last_retry_budget_axes", {}) or {}),
        runtime_advisory=logging_payload.session_runtime_advisory,
        retry_directives=logging_payload.session_retry_directives,
        firewall_triggered=decision_surface.firewall_triggered,
        firewall_reason=decision_surface.firewall_reason,
    )


def _build_stage4_attempt_contract_projection(
    *,
    contract_packet: _Stage4AttemptContractPacket,
    fix_scope_fallback: str | None = None,
    empty_fix_scope_as_none: bool = False,
    include_director_quality_passed: bool = False,
    include_strong_advisory_escalation: bool = False,
) -> dict[str, object]:
    resolved_fix_scope = str(contract_packet.scope_authority.get("fix_scope", "") or fix_scope_fallback or "").strip()
    projection: dict[str, object] = {
        "director_verdict": str(contract_packet.gate_semantics.get("director_verdict", "") or ""),
        "gate_basis": str(contract_packet.gate_semantics.get("gate_basis", "") or ""),
        "repair_scope": str(contract_packet.gate_semantics.get("repair_scope", "") or ""),
        "fix_scope": resolved_fix_scope or (None if empty_fix_scope_as_none else ""),
        "authoritative_fix_scope": str(contract_packet.scope_authority.get("authoritative_fix_scope", "") or ""),
        "fix_pack": contract_packet.fix_pack,
        "repair_contract": contract_packet.repair_contract,
        "scope_authority": contract_packet.scope_authority,
        "retry_budget_axes": contract_packet.retry_budget_axes,
        "downstream_override_applied": bool(contract_packet.verdict_layers.get("downstream_override_applied", False)),
        "primary_failure_layer": str(contract_packet.verdict_layers.get("primary_failure_layer", "") or ""),
    }
    if include_director_quality_passed:
        projection["director_quality_passed"] = bool(
            contract_packet.verdict_layers.get("director_quality_passed", False)
        )
    if include_strong_advisory_escalation:
        strong_advisory = contract_packet.gate_semantics.get("strong_advisory_escalation")
        if isinstance(strong_advisory, dict):
            projection["strong_advisory_escalation"] = strong_advisory
    return projection


def _build_stage4_session_contract_projection(
    *,
    session_gate_semantics: dict | None,
    fix_pack: dict | None,
    retry_budget_axes: dict | None,
) -> dict[str, object]:
    gate_semantics = session_gate_semantics if isinstance(session_gate_semantics, dict) else {}
    projection: dict[str, object] = {
        "director_verdict": str(gate_semantics.get("director_verdict", "") or ""),
        "gate_basis": str(gate_semantics.get("gate_basis", "") or ""),
        "repair_scope": str(gate_semantics.get("repair_scope", "") or ""),
        "fix_pack": dict(fix_pack or {}),
        "retry_budget_axes": dict(retry_budget_axes or {}),
        "authoritative_fix_scope": str(gate_semantics.get("authoritative_fix_scope", "") or ""),
        "authoritative_fix_scope_violation": (
            dict(gate_semantics.get("authoritative_fix_scope_violation") or {})
            if isinstance(gate_semantics.get("authoritative_fix_scope_violation"), dict)
            else None
        ),
        "scope_origin": (
            dict(gate_semantics.get("scope_origin") or {})
            if isinstance(gate_semantics.get("scope_origin"), dict)
            else None
        ),
        "repair_contract": (
            dict(gate_semantics.get("repair_contract") or {})
            if isinstance(gate_semantics.get("repair_contract"), dict)
            else None
        ),
        "scope_authority": (
            dict(gate_semantics.get("scope_authority") or {})
            if isinstance(gate_semantics.get("scope_authority"), dict)
            else None
        ),
        "conflict_resolution_linkage": (
            dict(gate_semantics.get("conflict_resolution_linkage") or {})
            if isinstance(gate_semantics.get("conflict_resolution_linkage"), dict)
            else None
        ),
        "reuse_contract": (
            dict(gate_semantics.get("reuse_contract") or {})
            if isinstance(gate_semantics.get("reuse_contract"), dict)
            else None
        ),
    }
    strong_advisory = gate_semantics.get("strong_advisory_escalation")
    if isinstance(strong_advisory, dict):
        projection["strong_advisory_escalation"] = dict(strong_advisory)
    return projection


def _build_stage4_prompt_version() -> str | None:
    try:
        from modules.core.prompt_loader import PromptLoader

        return PromptLoader().compose_version_tag("chief_writer", "director")
    except Exception as _e:
        logging.debug("[Stage4] prompt_version 계산 실패 (비차단): %s", _e)
        return None


def _build_stage4_raw_rationale_records(
    *,
    attempt_key: str,
    ep_num: int,
    director_result: dict | None,
    raw_advisory_payload: dict | None,
    selection_advisory: dict | None = None,
    selection_surface: dict | None = None,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    director_payload = director_result if isinstance(director_result, dict) else {}
    director_thinking = str(director_payload.get("_director_thinking", "") or "").strip()
    if director_thinking:
        record = build_stage4_raw_rationale_record(
            attempt_key=attempt_key,
            ep_num=ep_num,
            payload_kind="director_thinking",
            payload=director_thinking,
        )
        if record:
            records.append(record)
    if isinstance(raw_advisory_payload, dict) and raw_advisory_payload:
        record = build_stage4_raw_rationale_record(
            attempt_key=attempt_key,
            ep_num=ep_num,
            payload_kind="advisory_warnings_raw",
            payload=raw_advisory_payload,
        )
        if record:
            records.append(record)
    advisory_payload = selection_advisory if isinstance(selection_advisory, dict) else {}
    selection_contract_record = _build_stage4_contract_snapshot_raw_record(
        attempt_key=attempt_key,
        ep_num=ep_num,
        gate_semantics=advisory_payload.get("gate_semantics"),
        fix_pack=advisory_payload.get("fix_pack"),
        repair_contract=advisory_payload.get("repair_contract"),
        scope_authority=advisory_payload.get("scope_authority"),
        retry_budget_axes=advisory_payload.get("retry_budget_axes"),
        payload_kind="selection_contract_snapshot_raw",
        extra_payload={
            "patch_context": copy.deepcopy(advisory_payload.get("patch_context"))
            if isinstance(advisory_payload.get("patch_context"), dict)
            else None,
        },
    )
    if selection_contract_record:
        records.append(selection_contract_record)
    selection_surface_payload = selection_surface if isinstance(selection_surface, dict) else {}
    selection_surface_record = _build_stage4_selection_surface_raw_record(
        attempt_key=attempt_key,
        ep_num=ep_num,
        selection_surface=selection_surface_payload,
    )
    if selection_surface_record:
        records.append(selection_surface_record)
    return records


def _build_stage4_feedback_provenance_raw_record(
    *,
    attempt_key: str,
    ep_num: int,
    feedback_provenance: dict | None,
) -> dict[str, object] | None:
    if not isinstance(feedback_provenance, dict):
        return None
    normalized_payload = {
        str(key): str(value or "") for key, value in feedback_provenance.items() if str(key or "").strip()
    }
    if not any(str(value or "").strip() for value in normalized_payload.values()):
        return None
    return build_stage4_raw_rationale_record(
        attempt_key=attempt_key,
        ep_num=ep_num,
        payload_kind="feedback_provenance_raw",
        payload=normalized_payload,
    )


def _build_stage4_patch_trace_raw_record(
    *,
    attempt_key: str,
    ep_num: int,
    patch_trace: dict | None,
) -> dict[str, object] | None:
    if not isinstance(patch_trace, dict):
        return None
    normalized_payload = {
        str(key): value
        for key, value in patch_trace.items()
        if str(key or "").strip() and value not in ("", None, [], {})
    }
    if not normalized_payload:
        return None
    return build_stage4_raw_rationale_record(
        attempt_key=attempt_key,
        ep_num=ep_num,
        payload_kind="patch_trace_raw",
        payload=normalized_payload,
    )


def _build_stage4_contract_snapshot_raw_record(
    *,
    attempt_key: str,
    ep_num: int,
    gate_semantics: dict | None,
    fix_pack: dict | None,
    repair_contract: dict | None,
    scope_authority: dict | None,
    retry_budget_axes: dict | None,
    payload_kind: str = "contract_snapshot_raw",
    extra_payload: dict[str, object] | None = None,
) -> dict[str, object] | None:
    payload: dict[str, object] = {}
    if isinstance(gate_semantics, dict) and gate_semantics:
        payload["gate_semantics"] = copy.deepcopy(gate_semantics)
    if isinstance(fix_pack, dict) and fix_pack:
        payload["fix_pack"] = copy.deepcopy(fix_pack)
    if isinstance(repair_contract, dict) and repair_contract:
        payload["repair_contract"] = copy.deepcopy(repair_contract)
    if isinstance(scope_authority, dict) and scope_authority:
        payload["scope_authority"] = copy.deepcopy(scope_authority)
    if isinstance(retry_budget_axes, dict) and retry_budget_axes:
        payload["retry_budget_axes"] = copy.deepcopy(retry_budget_axes)
    if isinstance(extra_payload, dict):
        for key, value in extra_payload.items():
            if not str(key or "").strip() or value in ("", None, [], {}):
                continue
            payload[str(key)] = copy.deepcopy(value)
    if not payload:
        return None
    return build_stage4_raw_rationale_record(
        attempt_key=attempt_key,
        ep_num=ep_num,
        payload_kind=str(payload_kind or "contract_snapshot_raw"),
        payload=payload,
        payload_meta={
            "record_family": "contract_snapshot",
            "surface": str(payload_kind or "contract_snapshot_raw"),
        },
    )


def _build_stage4_selection_surface_raw_record(
    *,
    attempt_key: str,
    ep_num: int,
    selection_surface: dict | None,
) -> dict[str, object] | None:
    if not isinstance(selection_surface, dict):
        return None
    payload: dict[str, object] = {}
    for key in (
        "selected_label",
        "selected_strategy",
        "verdict",
        "score",
        "selection_reason",
        "verdict_reason",
        "fix_scope",
        "candidate_count",
        "pre_firewall_score",
        "firewall_triggered",
        "firewall_reason",
        "candidate_key",
        "content_hash",
        "artifact_path",
    ):
        value = selection_surface.get(key)
        if value in ("", None, [], {}):
            continue
        payload[key] = copy.deepcopy(value)
    advisory_warnings = selection_surface.get("advisory_warnings")
    if isinstance(advisory_warnings, dict) and advisory_warnings:
        payload["advisory_warnings"] = copy.deepcopy(advisory_warnings)
    if not payload:
        return None
    return build_stage4_raw_rationale_record(
        attempt_key=attempt_key,
        ep_num=ep_num,
        payload_kind="selection_surface_raw",
        payload=payload,
        payload_meta={
            "record_family": "selection_surface",
            "surface": "selection_surface_raw",
        },
    )


def _build_stage4_attempt_raw_evidence_records(
    *,
    attempt_key: str,
    ep_num: int,
    feedback_provenance: dict | None,
    patch_trace: dict | None,
    gate_semantics: dict | None = None,
    fix_pack: dict | None = None,
    repair_contract: dict | None = None,
    scope_authority: dict | None = None,
    retry_budget_axes: dict | None = None,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    feedback_record = _build_stage4_feedback_provenance_raw_record(
        attempt_key=attempt_key,
        ep_num=ep_num,
        feedback_provenance=feedback_provenance,
    )
    if feedback_record:
        records.append(feedback_record)
    patch_trace_record = _build_stage4_patch_trace_raw_record(
        attempt_key=attempt_key,
        ep_num=ep_num,
        patch_trace=patch_trace,
    )
    if patch_trace_record:
        records.append(patch_trace_record)
    contract_snapshot_record = _build_stage4_contract_snapshot_raw_record(
        attempt_key=attempt_key,
        ep_num=ep_num,
        gate_semantics=gate_semantics,
        fix_pack=fix_pack,
        repair_contract=repair_contract,
        scope_authority=scope_authority,
        retry_budget_axes=retry_budget_axes,
    )
    if contract_snapshot_record:
        records.append(contract_snapshot_record)
    return records


def _ns4_extract_time_markers(arc_data: dict) -> list:
    """[NS-4-S4] Arc tactical_doc/beat_sequence에서 날짜·상대시간 마커 추출 (regex, LLM 0회)."""
    import re as _re

    tactical_doc = arc_data.get("tactical_doc") or ""
    beat_seq = arc_data.get("beat_sequence") or ""
    if isinstance(beat_seq, list):
        beat_seq = " ".join(str(b) for b in beat_seq)

    _text = str(tactical_doc) + "\n" + str(beat_seq)
    _patterns = [
        r"\d{4}년\s*\d{1,2}월(?:\s*\d{1,2}일)?",  # utf8-hygiene: allow-line regex optional quantifier
        r"\d{1,2}월\s*\d{1,2}일",
        r"\d{1,2}월(?:\s*(?:말|초|중순|하순|상순))?",  # utf8-hygiene: allow-line regex optional quantifier
        r"\d+(?:일|주|달|개월|년)\s*(?:후|전)",  # utf8-hygiene: allow-line regex optional quantifier
    ]
    _found = []
    for _p in _patterns:
        _found.extend(_re.findall(_p, _text))
    return list(dict.fromkeys(_found))[:5]


class Stage4InterviewRound:
    """[B-1-3] Stage4 단일 면담 라운드 실행 모듈.

    Section Map (navigation aid):
        L152   __init__ + utility helpers
        L529   retry feedback / failure signature helpers
        L792   director context builders (work focus, relationship, retrieval)
        L1160  director result enrichment + gate normalization
        L1656  fix-pack / pass-with-fix contract helpers
        L1802  writer directive + common kwargs
        L1958  generation phase + validation phase
        L2148  director selection persistence
        L2248  ═══ run() — main entry ═══
        L2334  round execution + outcome finalization
        L2749  PASS / REJECT result builders
        L3041  PASS logging + session decision
        L3244  post-select advisories (continuity, blocking validator)
        L3448  post-select checks
        L3600  pass-with-fix loop + verdict processing
        L4018  reject handling + candidate generation
        L4097  NPC / HUD / CV context helpers
        L4363  ═══ advisory chain (parallel, 8 advisories) ═══
        L4959  fix feedback + patch provenance
        L5152  episode log + attempt recording
    """

    def __init__(self, ctx) -> None:
        self.ctx = ctx
        self.time_warnings = []
        self._last_advisory_summary = {}
        self._last_advisory_details: list[str] = []
        self._last_advisory_metadata: dict[str, list[dict]] = {}
        self._last_retry_budget_axes: dict[str, str] = {}
        self._consecutive_empty_patches: int = 0  # [IFC] track consecutive empty patch rounds
        self.director_runtime = Stage4DirectorRuntime(self)
        self.post_select_runtime = Stage4PostSelectRuntime(self)
        self.reject_runtime = Stage4RejectRuntime(self)
        self.retry_runtime = Stage4RetryRuntime(self)

    def _build_retry_advisory_digest(self, *, max_items: int | None = None) -> str:
        """Condense current-round advisory findings for CW retry feedback."""
        details = []
        for item in self._last_advisory_details:
            text = str(item or "").strip()
            if not text or "이상 없음" in text:
                continue
            details.append(text.replace("\n", " / "))

        if not details:
            return ""

        lines = [_RETRY_ADVISORY_MARKER]
        selected_details = details if max_items is None else details[:max_items]
        for text in selected_details:
            lines.append(f"- {text}")
        return "\n".join(lines)

    def _merge_retry_advisory_feedback(self, director_feedback: str) -> str:
        """Append advisory digest once so retries see raw failure signals."""
        advisory_digest = self._build_retry_advisory_digest()
        if not advisory_digest:
            return director_feedback

        base = str(director_feedback or "").strip()
        if _RETRY_ADVISORY_MARKER in base:
            return base
        if not base:
            return advisory_digest
        return base + "\n\n" + advisory_digest

    def _truth_gate_llm_ask(self, prompt: str) -> str:
        """[LM-A-2] TruthGate 세계관 법칙 검사용 LLM 콜백."""
        try:
            director = getattr(self.ctx, "agents", {}).get("director")
            if director and hasattr(director, "ask"):
                return director.ask(prompt, temperature=0.1) or ""
        except Exception as e:
            logging.debug("[TruthGate] llm_ask 실패 (비치명): %s", e)
        return ""

    def _get_inplace_success_rate(self) -> float | None:
        """[PF-4] director_selections에서 inplace fix_scope의 PASS 비율 조회.

        Returns:
            float (0~100) 또는 None (샘플 부족).
        """
        from modules.validation.threshold_helper import _threshold

        try:
            db = self.ctx.current_project.db
            stats = db.get_fix_scope_stats(lookback=200)
        except Exception:
            return None

        _min_samples = int(_threshold("patch_mode.inplace_min_samples", 5))
        total = 0
        pass_cnt = 0
        for row in stats:
            if row.get("fix_scope") == "inplace":
                cnt = row.get("cnt", 0)
                total += cnt
                if row.get("verdict") == "PASS":
                    pass_cnt += cnt

        if total < _min_samples:
            return None
        return round(pass_cnt / total * 100, 1)

    @staticmethod
    def _normalize_scope_summary(summary: dict | None) -> dict:
        payload = summary if isinstance(summary, dict) else {}
        breakdown = payload.get("model_breakdown", {})
        if isinstance(breakdown, str):
            try:
                breakdown = json.loads(breakdown)
            except (TypeError, ValueError, json.JSONDecodeError):
                breakdown = {}
        if not isinstance(breakdown, dict):
            breakdown = {}
        return {
            "total_calls": int(payload.get("total_calls", 0) or 0),
            "total_tokens": int(payload.get("total_tokens", 0) or 0),
            "total_cost_usd": float(payload.get("total_cost_usd", 0.0) or 0.0),
            "model_breakdown": dict(breakdown),
        }

    def _peek_round_scope_summary(self) -> dict:
        try:
            from modules.core.metrics_collector import get_metrics_collector

            collector = get_metrics_collector()
            if collector is None or not hasattr(collector, "peek_scope"):
                return self._normalize_scope_summary({})
            return self._normalize_scope_summary(collector.peek_scope())
        except Exception as exc:
            logging.debug("[Stage4] round scope peek 실패 (비차단): %s", exc)
            return self._normalize_scope_summary({})

    def _capture_round_metrics_baseline(self) -> None:
        self._round_metrics_start = self._peek_round_scope_summary()

    def _build_round_attempt_key(self, *, next_ep: int, round_num: int, arc_num: int = 0) -> str:
        _session_id = resolve_logging_session_id(getattr(self.ctx, "current_project", None))
        return build_attempt_key(
            stage=4,
            ep_num=next_ep,
            arc_num=arc_num,
            attempt_num=round_num + 1,
            session_id=_session_id,
        )

    def _log_attempt_event(
        self,
        level: int,
        *,
        next_ep: int,
        round_num: int,
        arc_num: int = 0,
        message: str,
        args: tuple = (),
    ) -> None:
        _attempt_key = self._build_round_attempt_key(next_ep=next_ep, round_num=round_num, arc_num=arc_num)
        logging.log(level, "[%s] " + message, _attempt_key, *tuple(args))

    def _log_round_outcome(
        self,
        *,
        next_ep: int,
        round_num: int,
        arc_num: int = 0,
        initial_verdict: str,
        final_verdict: str,
        initial_score: int,
        final_score: int,
        patch_mode: bool,
        patch_fallback: bool,
        warning_count: int,
        final_warning_count: int,
        reject_bucket: str = "",
        candidate_key: str = "",
        artifact_path: str = "",
    ) -> None:
        self._log_attempt_event(
            logging.INFO,
            next_ep=next_ep,
            round_num=round_num,
            arc_num=arc_num,
            message=(
                "round_complete initial=%s/%s final=%s/%s patch=%s patch_fallback=%s "
                "warnings=%d final_warnings=%d reject_bucket=%s candidate_key=%s artifact=%s"
            ),
            args=(
                str(initial_verdict or ""),
                int(initial_score or 0),
                str(final_verdict or ""),
                int(final_score or 0),
                bool(patch_mode),
                bool(patch_fallback),
                int(warning_count or 0),
                int(final_warning_count or 0),
                str(reject_bucket or "-"),
                str(candidate_key or "-"),
                str(artifact_path or "-"),
            ),
        )

    @staticmethod
    def _build_stage4_session_decision_kwargs(
        *,
        next_ep: int,
        round_num: int,
        arc_num: int,
        verdict: str,
        score: int,
        selected: str,
        error_category: str,
        reason: str,
        fix_scope: str,
        open_review: str,
        action_items: list | None,
        attempt_key: str,
        artifact_meta: dict | None = None,
        selection_artifact_meta: dict | None = None,
        initial_verdict: str = "",
        initial_score: int = 0,
        selection_reason: str = "",
        verdict_reason: str = "",
        session_gate_semantics: dict | None = None,
        fix_pack: dict | None = None,
        retry_budget_axes: dict | None = None,
        runtime_advisory: str = "",
        retry_directives: str = "",
        firewall_triggered: bool = False,
        firewall_reason: str = "",
    ) -> dict:
        return {
            "next_ep": next_ep,
            "round_num": round_num,
            "arc_num": arc_num,
            "verdict": str(verdict or ""),
            "score": int(score or 0),
            "selected": str(selected or ""),
            "error_category": str(error_category or ""),
            "reason": reason,
            "fix_scope": str(fix_scope or ""),
            "open_review": open_review,
            "action_items": list(action_items or []),
            "attempt_key": str(attempt_key or ""),
            "artifact_meta": artifact_meta,
            "selection_artifact_meta": selection_artifact_meta,
            "initial_verdict": str(initial_verdict or ""),
            "initial_score": int(initial_score or 0),
            "selection_reason": str(selection_reason or ""),
            "verdict_reason": str(verdict_reason or ""),
            "runtime_advisory": runtime_advisory,
            "retry_directives": retry_directives,
            "firewall_triggered": bool(firewall_triggered),
            "firewall_reason": str(firewall_reason or ""),
            **_build_stage4_session_contract_projection(
                session_gate_semantics=session_gate_semantics,
                fix_pack=fix_pack,
                retry_budget_axes=retry_budget_axes,
            ),
        }

    def _log_session_decision(
        self,
        *,
        next_ep: int,
        round_num: int,
        arc_num: int,
        verdict: str,
        score: int,
        selected: str,
        error_category: str,
        reason: str,
        fix_scope: str,
        open_review: str,
        action_items: list | None,
        attempt_key: str,
        artifact_meta: dict | None = None,
        selection_artifact_meta: dict | None = None,
        initial_verdict: str = "",
        initial_score: int = 0,
        selection_reason: str = "",
        verdict_reason: str = "",
        director_verdict: str = "",
        gate_basis: str = "",
        repair_scope: str = "",
        fix_pack: dict | None = None,
        retry_budget_axes: dict | None = None,
        runtime_advisory: str = "",
        retry_directives: str = "",
        firewall_triggered: bool = False,
        firewall_reason: str = "",
        authoritative_fix_scope: str = "",
        authoritative_fix_scope_violation: dict | None = None,
        strong_advisory_escalation: dict | None = None,
        scope_origin: dict | None = None,
        repair_contract: dict | None = None,
        scope_authority: dict | None = None,
        conflict_resolution_linkage: dict | None = None,
        reuse_contract: dict | None = None,
    ) -> None:
        _sl = getattr(self.ctx, "session_logger", None)
        if not _sl:
            return
        _artifact = normalize_artifact_meta(artifact_meta)
        _selection = normalize_artifact_meta(selection_artifact_meta)
        _sl.log_decision(
            stage="stage4",
            ep_num=next_ep,
            round_num=round_num,
            decision_type="manuscript",
            result=str(verdict or ""),
            score=int(score or 0),
            selected=str(selected or ""),
            arc_no=int(arc_num or 0),
            error_category=str(error_category or ""),
            reason=self._compact_text(reason, limit=None),
            selection_reason=self._compact_text(selection_reason, limit=None),
            verdict_reason=self._compact_text(verdict_reason, limit=None),
            fix_scope=str(fix_scope or ""),
            open_review=self._compact_text(open_review, limit=None),
            action_items=list(action_items or []),
            attempt_key=str(attempt_key or ""),
            candidate_key=_artifact["candidate_key"],
            content_hash=_artifact["content_hash"],
            artifact_path=_artifact["artifact_path"],
            selection_candidate_key=_selection["candidate_key"],
            selection_content_hash=_selection["content_hash"],
            selection_artifact_path=_selection["artifact_path"],
            initial_verdict=str(initial_verdict or ""),
            initial_score=int(initial_score or 0),
            director_verdict=str(director_verdict or ""),
            gate_basis=str(gate_basis or ""),
            repair_scope=str(repair_scope or ""),
            fix_pack=dict(fix_pack or {}),
            retry_budget_axes=dict(retry_budget_axes or {}),
            runtime_advisory=self._compact_text(runtime_advisory, limit=None),
            retry_directives=self._compact_text(retry_directives, limit=None),
            firewall_triggered=bool(firewall_triggered),
            firewall_reason=self._compact_text(firewall_reason, limit=None),
            authoritative_fix_scope=str(authoritative_fix_scope or ""),
            authoritative_fix_scope_violation=dict(authoritative_fix_scope_violation or {}),
            **(
                {"strong_advisory_escalation": dict(strong_advisory_escalation)}
                if isinstance(strong_advisory_escalation, dict)
                else {}
            ),
            **({"scope_origin": dict(scope_origin)} if isinstance(scope_origin, dict) else {}),
            **({"repair_contract": dict(repair_contract)} if isinstance(repair_contract, dict) else {}),
            **({"scope_authority": dict(scope_authority)} if isinstance(scope_authority, dict) else {}),
            # [SSS-T2] Carryover linkage — captured via **meta in session logger
            **(
                {"conflict_resolution_linkage": conflict_resolution_linkage}
                if isinstance(conflict_resolution_linkage, dict)
                else {}
            ),
            **({"reuse_contract": dict(reuse_contract)} if isinstance(reuse_contract, dict) else {}),
        )

    def _get_round_metrics_delta(self) -> dict:
        start = self._normalize_scope_summary(getattr(self, "_round_metrics_start", {}))
        current = self._peek_round_scope_summary()
        delta_breakdown: dict[str, dict[str, float]] = {}
        model_names = set(start["model_breakdown"].keys()) | set(current["model_breakdown"].keys())
        for model_name in model_names:
            current_row = current["model_breakdown"].get(model_name, {}) or {}
            start_row = start["model_breakdown"].get(model_name, {}) or {}
            tokens = int(current_row.get("tokens", 0) or 0) - int(start_row.get("tokens", 0) or 0)
            cost = float(current_row.get("cost", 0.0) or 0.0) - float(start_row.get("cost", 0.0) or 0.0)
            if tokens or cost:
                delta_breakdown[model_name] = {"tokens": max(0, tokens), "cost": max(0.0, cost)}
        return {
            "total_calls": max(0, current["total_calls"] - start["total_calls"]),
            "total_tokens": max(0, current["total_tokens"] - start["total_tokens"]),
            "total_cost_usd": max(0.0, current["total_cost_usd"] - start["total_cost_usd"]),
            "model_breakdown": delta_breakdown,
        }

    @staticmethod
    def _classify_reject_bucket(*, director_feedback: str, feedback, action_items: list | None) -> str:
        issues = feedback.get("issues", []) if isinstance(feedback, dict) else []
        reject_text = f"{director_feedback}\n" + "\n".join(str(item) for item in (action_items or issues or []))
        reject_lower = reject_text.lower()
        if any(
            key in reject_lower
            for key in ("constraint", "consistency", "conflict", "contradiction", "logic", "validation", "continuity")
        ):
            return "constraint_violation"
        if any(key in reject_lower for key in ("structure", "structural", "flow", "outline", "pacing", "rewrite")):
            return "structure_error"
        return "quality_issue"

    @staticmethod
    def _compact_text(value, limit: int | None = 500) -> str:
        text = str(value or "").strip()
        if limit is None:
            return text
        return text[:limit]

    @staticmethod
    def _join_unique_lines(lines: list[str] | tuple[str, ...] | None, *, limit: int | None = None) -> str:
        unique: list[str] = []
        seen: set[str] = set()
        for line in lines or []:
            text = str(line or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            unique.append(text)
        merged = "\n".join(unique)
        if limit is None:
            return merged
        return merged[:limit]

    @staticmethod
    def _describe_coverage_warning(code: str) -> str:
        mapping = {
            "missing_work_slot_summary": "작품 추적 슬롯 요약이 컨텍스트에 없다. work focus continuity를 직접 회수할 것.",
            "work_focus_without_slots": "work_focus가 감지됐지만 retrieval plan에 work_* slot이 없다. 작품 추적 포인트를 직접 반영할 것.",
            "trimmed_work_slot_summary": "작품 추적 슬롯 요약이 context budget에서 잘렸다. 핵심 tracking slot을 직접 회수할 것.",
            "missing_relation_slice": "관계 의미 질의가 빠졌다. 인물 관계 변화와 호칭 근거를 직접 회수할 것.",
        }
        return mapping.get(str(code or "").strip(), str(code or "").strip())

    def _structured_validation_evidence_lines(
        self,
        validation_result: dict | None,
        *,
        candidate_label: str = "",
        limit_per_key: int | None = None,
    ) -> list[str]:
        if not isinstance(validation_result, dict):
            return []

        prefix = f"[후보 {candidate_label}] " if candidate_label else ""
        lines: list[str] = []

        npc_drift_warnings = list(validation_result.get("npc_drift_warnings") or [])
        if limit_per_key is not None:
            npc_drift_warnings = npc_drift_warnings[:limit_per_key]
        for warning in npc_drift_warnings:
            if not isinstance(warning, dict):
                continue
            npc = str(warning.get("npc", "") or "").strip()
            field = str(warning.get("field", "") or "").strip()
            expected = str(warning.get("expected", "") or "").strip()
            found = str(warning.get("found_in_ms", "") or "").strip()
            body = f"{npc} {field}: 기대='{expected}' → 원고='{found}'".strip()
            body = " ".join(part for part in body.split() if part)
            if body:
                lines.append(f"{prefix}[NPC] {body}")

        numeric_consistency_warnings = list(validation_result.get("numeric_consistency_warnings") or [])
        if limit_per_key is not None:
            numeric_consistency_warnings = numeric_consistency_warnings[:limit_per_key]
        for warning in numeric_consistency_warnings:
            if isinstance(warning, dict):
                text = str(warning.get("text", "") or "").strip()
                category = str(warning.get("category") or warning.get("contradiction_type") or "").strip()
            else:
                text = str(warning or "").strip()
                category = ""
            if text:
                category_prefix = f"[{category}] " if category else ""
                lines.append(f"{prefix}[FACT] {category_prefix}{text}")

        coverage_warnings = list(validation_result.get("coverage_warnings") or [])
        if limit_per_key is not None:
            coverage_warnings = coverage_warnings[:limit_per_key]
        for warning in coverage_warnings:
            text = self._describe_coverage_warning(str(warning or ""))
            if text:
                lines.append(f"{prefix}[COVERAGE] {text}")

        return lines

    def _collect_validation_warning_lines(self, validation_results: list[dict], *, limit: int = 20) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()

        for idx, validation_result in enumerate(validation_results or []):
            if not isinstance(validation_result, dict):
                continue

            for warning in validation_result.get("warnings", []) or []:
                text = self._compact_text(warning, None)
                if text and text not in seen:
                    seen.add(text)
                    merged.append(text)

            label = ["A", "B", "C"][idx] if idx < 3 else str(idx + 1)
            for line in self._structured_validation_evidence_lines(
                validation_result,
                candidate_label=label,
                limit_per_key=None,
            ):
                if line not in seen:
                    seen.add(line)
                    merged.append(line)

            if len(merged) >= limit:
                break

        return merged[:limit]

    # ═══════════════════════════════════════════════════════════════════════
    # Retry feedback / failure signature helpers
    # ═══════════════════════════════════════════════════════════════════════

    def _build_retry_feedback_provenance(
        self,
        *,
        director_result: dict,
        director_feedback: str,
        selected_validation: dict,
        round_num: int,
    ) -> dict:
        prev_system_lines = (
            [
                line.strip()
                for line in str(director_feedback or "").split("\n")
                if any(line.strip().startswith(prefix) for prefix in _RETRY_SYSTEM_PREFIXES)
            ]
            if director_feedback
            else []
        )
        prev_general_lines = (
            [
                line.strip()
                for line in str(director_feedback or "").split("\n")
                if line.strip()
                and not any(line.strip().startswith(prefix) for prefix in _RETRY_SYSTEM_PREFIXES)
                and not line.strip().startswith("[R")
                and _RETRY_ADVISORY_MARKER not in line
            ]
            if director_feedback
            else []
        )

        feedback = director_result.get("feedback") or {}
        action_items = director_result.get("action_items") or []
        issues = feedback.get("issues", []) if isinstance(feedback, dict) else []
        director_lines = [str(item).strip() for item in action_items if str(item or "").strip()]
        if not director_lines:
            director_lines = [str(item).strip() for item in issues if str(item or "").strip()]
        open_review_lines = [
            str(item).strip()
            for item in issues
            if isinstance(item, str) and "[자유 리뷰]" in item and str(item).strip()
        ]
        if open_review_lines and action_items:
            director_lines.extend(open_review_lines)
        contradiction_detail_lines = self._compact_contradiction_detail_lines(
            director_result.get("contradiction_details"),
            max_items=None,
            line_limit=180,
        )
        if contradiction_detail_lines:
            for line in contradiction_detail_lines:
                prefixed = f"[모순 세부] {line}"
                if prefixed not in director_lines:
                    director_lines.append(prefixed)

        evidence_lines: list[str] = []
        if isinstance(selected_validation, dict):
            for warning in selected_validation.get("truth_gate_warnings") or []:
                if isinstance(warning, dict):
                    evidence_lines.append(
                        f"[{warning.get('severity', '?')}] {str(warning.get('text', '') or '').strip()}"
                    )
            for violation in selected_validation.get("structured_violations") or []:
                if isinstance(violation, dict):
                    evidence_lines.append(f"[VIOLATION] {str(violation.get('reason', '') or '').strip()}")
            for warning in selected_validation.get("quality_signal_warnings") or []:
                text = str(warning or "").strip()
                if text:
                    evidence_lines.append(f"[STYLE] {text}")
            evidence_lines.extend(self._structured_validation_evidence_lines(selected_validation, limit_per_key=None))
        evidence_summary = ""
        if evidence_lines:
            evidence_summary = "[근거 요약 - 수정 시 반드시 반영]\n" + "\n".join(f"  {line}" for line in evidence_lines)

        runtime_advisory = self._build_retry_advisory_digest()
        retry_directives = ""
        if prev_general_lines and round_num > 0:
            # [FW-1] Keep only latest-round advisory entries while preserving structural directives.
            _MAX_RETRY_DIRECTIVE_LINES = 20
            _seen: set[str] = set()
            _retained: list[str] = []
            _latest_round = round_num - 1
            for _line in prev_general_lines:
                _stripped = _line.strip()
                if not _stripped:
                    continue

                _candidate = ""
                if _is_persistent_retry_directive_line(_stripped):
                    _candidate = _stripped
                elif _is_retry_advisory_line(_stripped):
                    _tagged_round = _parse_retry_advisory_round_tag(_stripped)
                    if _tagged_round is not None and _tagged_round != _latest_round:
                        continue
                    _candidate = _tag_retry_advisory_line(_stripped, round_num=_latest_round)

                if _candidate and _candidate not in _seen:
                    _seen.add(_candidate)
                    _retained.append(_candidate)

            retry_directives = "\n".join(_retained[-_MAX_RETRY_DIRECTIVE_LINES:])

        system_feedback = self._join_unique_lines(prev_system_lines)
        director_feedback_text = self._join_unique_lines(director_lines)

        merged_sections = [
            system_feedback,
            evidence_summary,
            director_feedback_text,
            f"[R{round_num - 1} 이전 지시] {retry_directives}" if retry_directives else "",
            runtime_advisory,
        ]
        merged_feedback = "\n".join(section for section in merged_sections if section)

        return self._build_stage4_feedback_provenance_payload(
            director_feedback=director_feedback_text,
            runtime_advisory=runtime_advisory,
            retry_directives=retry_directives,
            merged_feedback=merged_feedback,
            system_feedback=system_feedback,
            evidence_summary=evidence_summary,
        )

    @staticmethod
    def _build_stage4_feedback_provenance_payload(
        *,
        director_feedback: str,
        runtime_advisory: str,
        retry_directives: str,
        merged_feedback: str = "",
        system_feedback: str = "",
        evidence_summary: str = "",
    ) -> dict[str, str]:
        payload = s4_episode_logging.build_stage4_feedback_provenance(
            director_feedback=director_feedback,
            runtime_advisory=runtime_advisory,
            retry_directives=retry_directives,
        )
        payload["merged_feedback"] = str(merged_feedback or "")
        payload["system_feedback"] = str(system_feedback or "")
        payload["evidence_summary"] = str(evidence_summary or "")
        return payload

    @staticmethod
    def _compact_contradiction_detail_lines(
        details: object,
        *,
        max_items: int | None = None,
        line_limit: int = 160,
    ) -> list[str]:
        if not isinstance(details, list):
            return []

        lines: list[str] = []
        selected_details = details if max_items is None else details[:max_items]
        for item in selected_details:
            if isinstance(item, dict):
                severity = str(item.get("severity", "") or "").strip().upper() or "ISSUE"
                kind = str(item.get("type", "") or "모순").strip()
                body = (
                    str(item.get("current_violation", "") or "").strip()
                    or str(item.get("description", "") or "").strip()
                    or str(item.get("expected_truth", "") or "").strip()
                )
                fix = str(item.get("fix_suggestion", "") or "").strip()
                line = f"[{severity}] {kind}: {body}".strip()
                if fix:
                    line = f"{line} -> {fix}"
            else:
                line = str(item or "").strip()
            if line:
                lines.append(line)
        return lines

    def _is_continuity_replay_reject(self, *, director_result: dict, director_feedback: str) -> bool:
        if not isinstance(director_result, dict) or not director_result.get("firewall_triggered"):
            return False

        contradiction_types = {
            str(item or "").strip().lower()
            for item in (director_result.get("contradiction_types") or [])
            if str(item or "").strip()
        }
        continuity_types = {
            "scene_overlap",
            "event_ordering",
            "space_continuity",
            "timeline_arc_consistency",
            "opening_diversity",
            "opening_action_continuity",
        }
        if contradiction_types.intersection(continuity_types):
            return True

        continuity_markers = (
            "continuity conflict",
            "history conflict",
            "scene overlap",
            "event ordering",
            "space continuity",
            "이전 화",
            "직전 화",
            "이전 에피소드",
            "직전 에피소드",
            "같은 사건",
            "같은 장면",
        )
        signal_text = "\n".join(
            [
                str(director_feedback or ""),
                str(director_result.get("verdict_reason") or ""),
                str(director_result.get("open_review") or ""),
                str(director_result.get("firewall_reason") or ""),
            ]
        ).lower()
        return any(marker in signal_text for marker in continuity_markers)

    def _resolve_director_protagonist_name(self, genre_name: str = "") -> str:
        try:
            from modules.core.constants import HUDKeys

            master_bible = getattr(getattr(self.ctx, "current_project", None), "master_bible", {}) or {}
            bible_root = master_bible.get("MasterBible", {}) if isinstance(master_bible, dict) else {}
            return str(HUDKeys.get_protagonist_name(bible_root, genre_name) or "").strip()
        except Exception as exc:
            logging.debug("[Stage4] Director protagonist_name 조회 실패 (비치명): %s", exc)
            return ""

    def _compose_director_work_focus_text(
        self,
        *,
        blueprint: dict | None,
        prev_ending: str,
        npc_roster: list[str],
        max_chars: int = 2400,
    ) -> str:
        parts: list[str] = []
        if prev_ending:
            parts.append(str(prev_ending))
        if isinstance(blueprint, dict):
            for key in (
                "title",
                "summary",
                "hook",
                "core_conflict",
                "goal",
                "twist",
                "core_event",
                "story_goal",
                "integrated_scenario",
                "end_location",
                "start_location",
            ):
                value = str(blueprint.get(key, "") or "").strip()
                if value:
                    parts.append(value)
            scene_blocks = blueprint.get("scene_breakdown") or blueprint.get("scenes") or []
            if isinstance(scene_blocks, dict):
                scene_blocks = list(scene_blocks.values())
            if isinstance(scene_blocks, list):
                for scene in scene_blocks[:4]:
                    if not isinstance(scene, dict):
                        continue
                    for key in ("summary", "purpose", "conflict", "location"):
                        value = str(scene.get(key, "") or "").strip()
                        if value:
                            parts.append(value)
        if npc_roster:
            parts.append(" ".join(str(name).strip() for name in npc_roster[:8] if str(name).strip()))
        combined = "\n".join(part for part in parts if part)
        if len(combined) > max_chars:
            return smart_truncate(
                combined,
                max_chars=max_chars,
                head_chars=max(0, min(int(max_chars * 0.55), max_chars - 80)),
            )
        return combined

    @staticmethod
    def _normalize_writer_blueprint(blueprint: dict | None) -> dict:
        """Keep writer-facing blueprint authority narrow without mutating the original."""
        if not isinstance(blueprint, dict):
            return {}

        writer_blueprint = copy.deepcopy(blueprint)
        scenes = writer_blueprint.get("scene_breakdown")
        if isinstance(scenes, dict | list):
            writer_blueprint["scene_breakdown"] = _sanitize_writer_blueprint_payload(scenes)
        raw_advisory = str(writer_blueprint.get("integrated_scenario_advisory", "") or "").strip()
        raw_integrated = str(writer_blueprint.get("integrated_scenario", "") or "").strip()
        advisory = raw_advisory
        integrated = raw_integrated
        if integrated and not advisory:
            advisory = integrated
        advisory = _sanitize_writer_blueprint_text(advisory)
        integrated = _sanitize_writer_blueprint_text(integrated)
        if advisory:
            writer_blueprint["integrated_scenario_advisory"] = advisory
        elif raw_advisory or raw_integrated or "integrated_scenario_advisory" in writer_blueprint:
            writer_blueprint["integrated_scenario_advisory"] = ""
        if integrated:
            writer_blueprint["integrated_scenario"] = ""
        elif "integrated_scenario" in writer_blueprint:
            writer_blueprint["integrated_scenario"] = ""
        return writer_blueprint

    def _resolve_director_work_focus(
        self,
        *,
        blueprint: dict | None,
        prev_ending: str,
        npc_roster: list[str],
    ) -> dict[str, object]:
        guard = getattr(getattr(self.ctx, "sys", None), "guard", None)
        if not guard or not hasattr(guard, "select_retrieval_focus"):
            return {}

        focus_text = self._compose_director_work_focus_text(
            blueprint=blueprint,
            prev_ending=prev_ending,
            npc_roster=npc_roster,
        )
        if not focus_text:
            return {}

        try:
            focus = guard.select_retrieval_focus(stage="director", focus_text=focus_text)
        except Exception as exc:
            logging.debug("[Stage4] Director work_focus 선택 실패 (비치명): %s", exc)
            return {}
        return focus if isinstance(focus, dict) else {}

    # ═══════════════════════════════════════════════════════════════════════
    # Director context builders (work focus, relationship, retrieval)
    # ═══════════════════════════════════════════════════════════════════════

    def _build_director_work_focus_summary(
        self,
        *,
        work_focus: dict[str, object],
        blueprint: dict | None,
        protagonist_name: str = "",
        max_chars: int = 1200,
    ) -> str:
        if not isinstance(work_focus, dict) or not work_focus:
            return ""

        tracking_slots = [str(item).strip() for item in (work_focus.get("tracking_slots") or []) if str(item).strip()]
        scene_engines = [
            str(item).strip() for item in (work_focus.get("mandatory_scene_engines") or []) if str(item).strip()
        ]
        registry_profiles = [item for item in (work_focus.get("registry_profiles") or []) if isinstance(item, dict)]
        if not any([tracking_slots, scene_engines, registry_profiles]):
            return ""

        lines = ["[작품 추적 슬롯 요약]"]
        if tracking_slots:
            lines.append(f"- Director 우선 tracking_slots: {', '.join(tracking_slots[:3])}")
        if scene_engines:
            lines.append(f"- Director scene engines: {', '.join(scene_engines[:2])}")
        if registry_profiles:
            rendered_profiles = []
            for profile in registry_profiles[:2]:
                name = str(profile.get("name", "") or "").strip()
                fields = [str(item).strip() for item in (profile.get("required_fields") or []) if str(item).strip()]
                if not name:
                    continue
                rendered_profiles.append(name + (f"(fields={', '.join(fields[:4])})" if fields else ""))
            if rendered_profiles:
                lines.append(f"- registry focus: {', '.join(rendered_profiles)}")

        char_names: list[str] = []
        if isinstance(blueprint, dict):
            linked_parts: list[str] = []
            raw_chars = blueprint.get("characters") or blueprint.get("npcs") or []
            if isinstance(raw_chars, list):
                for item in raw_chars[:4]:
                    if isinstance(item, dict):
                        name = str(item.get("name", "") or item.get("npc", "")).strip()
                    else:
                        name = str(item).strip()
                    if name:
                        char_names.append(name)
            elif isinstance(raw_chars, str):
                char_names = [token.strip() for token in raw_chars.replace("|", ",").split(",") if token.strip()][:4]
            if char_names:
                linked_parts.append(f"NPC={', '.join(char_names)}")
            for label, key in (("장소", "end_location"), ("사건", "core_event"), ("목표", "story_goal")):
                value = str(blueprint.get(key, "") or "").strip()
                if value:
                    linked_parts.append(f"{label}={value[:80]}")
            if linked_parts:
                lines.append(f"- 이번 화 연결 엔티티: {' | '.join(linked_parts)}")

        try:
            from modules.core.semantic_query_broker import SemanticQueryBroker

            focus_text = " ".join(
                [
                    ", ".join(tracking_slots),
                    ", ".join(scene_engines),
                    " ".join(str(profile.get("purpose", "") or "") for profile in registry_profiles),
                    str((blueprint or {}).get("core_event", "") or ""),
                    str((blueprint or {}).get("story_goal", "") or ""),
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
            elif protagonist_name and char_names:
                fallback = self._build_director_relationship_context(
                    db=getattr(getattr(self.ctx, "current_project", None), "db", None),
                    npc_names=char_names,
                    protagonist_name=protagonist_name,
                    limit=4,
                )
                if fallback:
                    lines.append("[관계 의미 질의]\n" + fallback)
        except Exception as exc:
            logging.debug("[Stage4] Director semantic relation slice 생성 실패 (비치명): %s", exc)

        text = "\n".join(lines)
        if len(text) > max_chars:
            return smart_truncate(
                text,
                max_chars=max_chars,
                head_chars=max(0, min(int(max_chars * 0.55), max_chars - 80)),
            )
        return text

    def _build_director_relationship_context(
        self,
        *,
        db,
        npc_names: list[str],
        protagonist_name: str = "",
        limit: int = 6,
    ) -> str:
        if not db or not hasattr(db, "get_relationship_history"):
            return ""

        clean_names = [str(name).strip() for name in (npc_names or []) if str(name).strip()]
        protagonist_name = str(protagonist_name or "").strip()
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
            except Exception as exc:
                logging.debug("[Stage4] Director relationship history 조회 실패 (비치명): %s", exc)
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
            logging.debug("[Stage4] Director retrieval observation record failed: %s", exc)

    def _build_db_pacing_advisory(self, db, next_ep: int) -> str:
        """최근 호흡 분석 추이를 Director advisory로 변환한다."""
        getter = getattr(db, "get_recent_pacing_records", None)
        if not callable(getter):
            return ""

        try:
            pacing_recs = getter(before_ep=next_ep, lookback=5)
            if not isinstance(pacing_recs, list) or len(pacing_recs) < 2:
                return ""

            def _num(value, default: float = 0.0) -> float:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return default

            avg_dial = sum(_num(rec.get("dialogue_ratio")) for rec in pacing_recs) / len(pacing_recs)
            avg_score = sum(_num(rec.get("pacing_score"), 50.0) for rec in pacing_recs) / len(pacing_recs)
            pacing_lines: list[str] = []
            if avg_dial < 0.15:
                pacing_lines.append(f"대화 비율 평균 {avg_dial:.0%} — 최근 {len(pacing_recs)}화 대화 부족 추세")
            if avg_score < 40:
                pacing_lines.append(f"호흡 점수 평균 {avg_score:.0f}/100 — 문장 다양화·장면 전환 필요")

            dial_vals = [_num(rec.get("dialogue_ratio")) for rec in pacing_recs]
            if len(dial_vals) >= 3 and all(dial_vals[i] > dial_vals[i + 1] for i in range(len(dial_vals) - 1)):
                pacing_lines.append(f"대화 비율 {len(dial_vals)}화 연속 하락 ({dial_vals[0]:.0%}→{dial_vals[-1]:.0%})")

            if not pacing_lines:
                return ""
            return f"[DB-1 호흡 추이] {_DB_ADVISORY_NOTICE}\n" + "\n".join(pacing_lines)
        except Exception as pace_err:
            logging.debug("[DB-1] pacing advisory 실패 (비치명): %s", pace_err)
            return ""

    def _build_db_satisfaction_advisory(self, db, next_ep: int) -> str:
        """최근 만족도 태그 추이를 Director advisory로 변환한다."""
        getter = getattr(db, "get_recent_satisfaction_tags", None)
        if not callable(getter):
            return ""

        try:
            sat_tags = getter(before_ep=next_ep, lookback=5)
            if not isinstance(sat_tags, list) or len(sat_tags) < 2:
                return ""

            sat_lines: list[str] = []
            consecutive_frust = 0
            low_agency_count = 0
            for sat_tag in sat_tags:
                if bool(sat_tag.get("frustration_flag")):
                    consecutive_frust += 1
                else:
                    consecutive_frust = 0
                if str(sat_tag.get("protagonist_agency", "") or "") in {"타력", "수동"}:
                    low_agency_count += 1

            if consecutive_frust >= 2:
                sat_lines.append(f"좌절감 {consecutive_frust}화 연속 — 주인공 능동적 활약 필수")
            if low_agency_count >= 3:
                sat_lines.append(f"주인공 에이전시 저조 {low_agency_count}/{len(sat_tags)}화 — 주체적 선택 장면 필요")

            def _score(value) -> float:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return 5.0

            avg_score = sum(_score(tag.get("satisfaction_score")) for tag in sat_tags) / len(sat_tags)
            if avg_score < 4:
                sat_lines.append(f"만족도 평균 {avg_score:.1f}/10 — 긴장·보상·캐릭터 성장 보강 필요")

            if not sat_lines:
                return ""
            return f"[DB-2 만족도 추이] {_DB_ADVISORY_NOTICE}\n" + "\n".join(sat_lines)
        except Exception as sat_err:
            logging.debug("[DB-2] satisfaction advisory 실패 (비치명): %s", sat_err)
            return ""

    def _build_db_reveals_advisory(self, db, next_ep: int) -> str:
        """최근 episode_bible의 reveals를 Director advisory로 조립한다."""
        getter = getattr(db, "get_episode_bible", None)
        if not callable(getter):
            return ""

        try:
            reveal_all: list[str] = []
            for prev_ep in range(max(1, next_ep - 10), next_ep):
                bible = getter(prev_ep)
                if not isinstance(bible, dict):
                    continue
                for reveal in bible.get("reveals") or []:
                    if isinstance(reveal, str) and reveal.strip():
                        reveal_all.append(f"  ep{prev_ep}: {reveal[:80]}")

            if not reveal_all:
                return ""
            return f"[DB-6 최근 10화 내 밝혀진 사실 ({len(reveal_all)}건)] {_DB_ADVISORY_NOTICE}\n" + "\n".join(
                reveal_all[-8:]
            )
        except Exception as rev_err:
            logging.debug("[DB-6] reveals advisory 실패 (비치명): %s", rev_err)
            return ""

    def _build_db_reflexion_advisory(self, next_ep: int) -> str:
        """Reflexion memory의 상위 실패 패턴을 Director advisory로 조립한다."""
        if next_ep < 20:
            return ""

        try:
            from modules.core.reflexion_manager import ReflexionManager

            project = getattr(self.ctx, "current_project", None)
            if project is None:
                return ""
            top_patterns = ReflexionManager(project).get_top_patterns(min_frequency=3, limit=3)
            if not isinstance(top_patterns, list) or not top_patterns:
                return ""

            refl_lines: list[str] = []
            for pattern in top_patterns:
                if not isinstance(pattern, dict):
                    continue
                ptype = pattern.get("pattern_type", "?")
                freq = pattern.get("frequency", 0)
                desc = str(pattern.get("description", "") or "")[:60]
                refl_lines.append(f"  - {ptype} ({freq}회): {desc}")

            if not refl_lines:
                return ""
            return f"[DB-8 반복 실패 패턴 (빈도≥3)] {_DB_ADVISORY_NOTICE}\n" + "\n".join(refl_lines)
        except Exception as refl_err:
            logging.debug("[DB-8] reflexion advisory 실패 (비치명): %s", refl_err)
            return ""

    @staticmethod
    def _compact_attempt_snapshot(previous_attempt: dict | None) -> dict:
        """이전 시도 피드백을 재생성용 최소 스냅샷으로 축약."""
        if not isinstance(previous_attempt, dict) or not previous_attempt:
            return {}

        snapshot = {
            "strategy": previous_attempt.get("strategy", ""),
            "score": previous_attempt.get("score", 0),
            "fix_scope": previous_attempt.get("fix_scope", ""),
            # [DCM-T3] Preserve authoritative Director scope separate from derived retry scope
            "authoritative_fix_scope": previous_attempt.get("authoritative_fix_scope", ""),
            "attempt_key": previous_attempt.get("attempt_key", ""),
            "candidate_key": previous_attempt.get("candidate_key", ""),
            "content_hash": previous_attempt.get("content_hash", ""),
            "artifact_path": previous_attempt.get("artifact_path", ""),
            "selection_candidate_key": previous_attempt.get("selection_candidate_key", ""),
            "selection_content_hash": previous_attempt.get("selection_content_hash", ""),
            "selection_artifact_path": previous_attempt.get("selection_artifact_path", ""),
            "fix_scope_reasoning": str(previous_attempt.get("fix_scope_reasoning", "") or ""),
            "open_review": str(previous_attempt.get("open_review", "") or ""),
            "reject_bucket": previous_attempt.get("reject_bucket", ""),
            "error_category": previous_attempt.get("error_category", ""),
            "fix_pack_reason": previous_attempt.get("fix_pack_reason", ""),  # [TF-4]
            "rejection_reason": str(previous_attempt.get("rejection_reason", "") or ""),
            "action_items": list(previous_attempt.get("action_items", []) or []),
            "contradiction_types": list(previous_attempt.get("contradiction_types", []) or []),
            "retry_budget_axes": dict(previous_attempt.get("retry_budget_axes", {}) or {}),
        }
        contradiction_details = Stage4InterviewRound._compact_contradiction_detail_lines(
            previous_attempt.get("contradiction_details"),
            max_items=None,
            line_limit=120,
        )
        if contradiction_details:
            snapshot["contradiction_details"] = contradiction_details
        return {k: v for k, v in snapshot.items() if v not in ("", [], {}, None)}

    def _inherit_attempt_history(self, previous_attempt: dict | None) -> list[dict]:
        """직전 previous_attempt로부터 누적 재시도 히스토리를 계승한다."""
        if not isinstance(previous_attempt, dict) or not previous_attempt:
            return []

        history: list[dict] = []
        for key in ("prior_attempts", "history"):
            raw = previous_attempt.get(key)
            if isinstance(raw, list):
                for item in raw:
                    compact = self._compact_attempt_snapshot(item if isinstance(item, dict) else {})
                    if compact:
                        history.append(compact)

        current = self._compact_attempt_snapshot(previous_attempt)
        if current:
            history.append(current)

        deduped: list[dict] = []
        seen: set[tuple] = set()
        for item in history:
            marker = (
                item.get("strategy", ""),
                item.get("score", ""),
                item.get("fix_scope", ""),
                item.get("reject_bucket", ""),
                item.get("error_category", ""),
                item.get("rejection_reason", ""),
            )
            if marker in seen:
                continue
            seen.add(marker)
            deduped.append(item)
        return deduped[-3:]

    def _maybe_enrich_director_result(self, director_result: dict, manuscript_text: str = "") -> dict:
        try:
            inspect.getattr_static(self.ctx, "enrich_director_result")
        except AttributeError:
            callback = None
        else:
            callback = getattr(self.ctx, "enrich_director_result", None)
        if not callable(callback) or not isinstance(director_result, dict):
            return director_result

        try:
            enriched = callback(
                dict(director_result),
                stage=4,
                content_length=len(str(manuscript_text or "")),
            )
        except Exception as exc:
            logging.debug("[Stage4] enrich_director_result 실패 (비치명): %s", exc)
            return director_result

        if not isinstance(enriched, dict):
            return director_result

        merged = dict(director_result)
        for key, value in enriched.items():
            current = merged.get(key)
            if key == "action_items":
                if not current and value:
                    merged[key] = value
                continue
            if current in ("", None, [], {}) and value not in ("", None, [], {}):
                merged[key] = value
        return merged

    @staticmethod
    def _build_char_ngrams(text: str, n: int = 3) -> set[str]:
        import re as _re

        normalized = _re.sub(r"\s+", " ", str(text or "")).strip()
        if not normalized:
            return set()
        if len(normalized) < n:
            return {normalized}
        return {normalized[i : i + n] for i in range(len(normalized) - n + 1)}

    def _summarize_candidate_diversity(self, candidates: list[dict], *, threshold: float = 0.7) -> dict:
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            metadata = candidate.get("metadata", {})
            if isinstance(metadata, dict) and isinstance(metadata.get("diversity"), dict):
                return metadata["diversity"]

        indexed_texts: list[tuple[int, str]] = []
        for idx, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                continue
            manuscript = str(candidate.get("manuscript", "") or "").strip()
            if manuscript:
                indexed_texts.append((idx, manuscript))

        if len(indexed_texts) < 2:
            return {}

        labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        pairwise = []
        high_similarity_pairs = []
        max_similarity = 0.0
        for left_pos in range(len(indexed_texts)):
            left_idx, left_text = indexed_texts[left_pos]
            left_grams = self._build_char_ngrams(left_text)
            if not left_grams:
                continue
            for right_pos in range(left_pos + 1, len(indexed_texts)):
                right_idx, right_text = indexed_texts[right_pos]
                right_grams = self._build_char_ngrams(right_text)
                if not right_grams:
                    continue
                union = left_grams | right_grams
                similarity = (len(left_grams & right_grams) / len(union)) if union else 0.0
                similarity = round(similarity, 2)
                pair_label = f"{labels[left_idx]}-{labels[right_idx]}"
                pairwise.append({"pair": pair_label, "similarity": similarity})
                max_similarity = max(max_similarity, similarity)
                if similarity > threshold:
                    high_similarity_pairs.append({"pair": pair_label, "similarity": similarity})

        warning = ""
        if len(high_similarity_pairs) >= 2:
            pairs_text = ", ".join(
                f"{pair['pair']} {int(pair['similarity'] * 100)}%" for pair in high_similarity_pairs[:3]
            )
            warning = f"[후보 다양성 경고] 후보 유사도 높음: {pairs_text}"

        return {
            "pairwise": pairwise,
            "max_similarity": round(max_similarity, 2),
            "high_similarity_pairs": high_similarity_pairs,
            "warning": warning,
        }

    def _build_candidate_diversity_advisory(self, candidates: list[dict]) -> str:
        summary = self._summarize_candidate_diversity(candidates)
        if not isinstance(summary, dict):
            return ""

        warning = str(summary.get("warning", "") or "").strip()
        if not warning:
            return ""

        lines = [warning]
        for pair in summary.get("high_similarity_pairs", [])[:3]:
            if not isinstance(pair, dict):
                continue
            lines.append(f"- {pair.get('pair', '?')}: {int(float(pair.get('similarity', 0.0)) * 100)}%")
        lines.append("- 3후보가 지나치게 비슷하면 가장 다른 접근을 우대해 비교하세요.")
        return "\n".join(lines)

    @staticmethod
    def _normalize_failure_signature(text: str) -> str:
        import re as _re

        cleaned = str(text or "").strip()
        if not cleaned:
            return ""
        cleaned = _re.sub(r"^\[[^\]]+\]\s*", "", cleaned)
        cleaned = _re.sub(r"\d+", "#", cleaned)
        cleaned = _re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:80]

    def _extract_failure_signatures(self, validation_result: dict) -> set[str]:
        signatures: set[str] = set()
        if not isinstance(validation_result, dict):
            return signatures

        for violation in validation_result.get("structured_violations", []) or []:
            if not isinstance(violation, dict):
                continue
            raw = violation.get("type") or violation.get("reason") or violation.get("message") or ""
            normalized = self._normalize_failure_signature(raw)
            if normalized:
                signatures.add(normalized)

        tracked_prefixes = ("[Python검증-", "[V63.2] 일관성:", "[V66.1] 연속성:")
        for warning in validation_result.get("warnings", []) or []:
            warning_text = str(warning or "")
            if not warning_text.startswith(tracked_prefixes):
                continue
            normalized = self._normalize_failure_signature(warning_text)
            if normalized:
                signatures.add(normalized)
        return signatures

    def _detect_shared_failure_warnings(self, validation_results: list[dict]) -> list[str]:
        signature_sets = [
            self._extract_failure_signatures(result) for result in validation_results if isinstance(result, dict)
        ]
        signature_sets = [items for items in signature_sets if items]
        if len(signature_sets) < 2:
            return []

        shared = sorted(set.intersection(*signature_sets))
        return [f"[⚠️ 전원 동일 위반: {item}]" for item in shared[:3]]

    @staticmethod
    def _clone_validation_results_for_advisory(validation_results: list[dict]) -> list[dict]:
        cloned: list[dict] = []
        for result in validation_results or []:
            cloned.append(copy.deepcopy(result) if isinstance(result, dict) else result)
        return cloned

    @staticmethod
    def _merge_advisory_validation_results(target_results: list[dict], advisory_results: list[dict]) -> None:
        tracked_keys = (
            "truth_gate_warnings",
            "npc_drift_warnings",
            "numeric_consistency_warnings",
            "quality_signal_warnings",
        )
        for idx, advisory_result in enumerate(advisory_results or []):
            if idx >= len(target_results):
                break
            if not isinstance(target_results[idx], dict) or not isinstance(advisory_result, dict):
                continue
            for key in tracked_keys:
                value = advisory_result.get(key)
                if value:
                    target_results[idx][key] = copy.deepcopy(value)

    @staticmethod
    def _build_raw_advisory_payload(
        validation_results: list[dict],
        *,
        selection_summary: dict | None = None,
    ) -> dict | None:
        tracked_keys = (
            "truth_gate_warnings",
            "npc_drift_warnings",
            "numeric_consistency_warnings",
            "quality_signal_warnings",
            "coverage_warnings",
            "shared_failure_warnings",
            "structured_violations",
            "warnings",
        )
        candidate_payloads: list[dict] = []
        for idx, validation_result in enumerate(validation_results or []):
            if not isinstance(validation_result, dict):
                continue
            payload: dict[str, object] = {}
            for key in tracked_keys:
                value = validation_result.get(key)
                if value:
                    payload[key] = copy.deepcopy(value)
            warning_count = validation_result.get("warning_count")
            if warning_count:
                payload["warning_count"] = int(warning_count)
            if not payload:
                continue
            payload["candidate_index"] = idx
            payload["candidate_label"] = ["A", "B", "C"][idx] if idx < 3 else str(idx + 1)
            candidate_payloads.append(payload)
        if not candidate_payloads:
            return None
        raw_payload = {"candidate_validation_payloads": candidate_payloads}
        if isinstance(selection_summary, dict) and selection_summary:
            raw_payload["selection_summary"] = copy.deepcopy(selection_summary)
        return raw_payload

    @staticmethod
    def _classify_advisory_tier(advisory_text: str) -> tuple[int, str]:
        text = str(advisory_text or "")
        if "[TruthGate" in text:
            return 3, "TruthGate"
        if any(tag in text for tag in ("[LM-B]", "NpcDrift")):
            return 2, "NpcDrift"
        if any(tag in text for tag in ("[LM-D]", "RelDrift", "RelationshipDrift")):
            return 2, "RelDrift"
        if any(tag in text for tag in ("[LM-E]", "Flashback")):
            return 2, "Flashback"
        if any(tag in text for tag in ("[LM-F]", "InfoParadox")):
            return 2, "InfoParadox"
        if any(tag in text for tag in ("[LM-C]", "NumericDrift")):
            return 1, "NumericDrift"
        if any(tag in text for tag in ("[LM-P1]", "LongTerm")):
            return 1, "LongTermRepetition"
        return 1, "Advisory"

    @staticmethod
    def _extract_advisory_subjects(advisory_text: str) -> tuple[set[str], set[str]]:
        import re as _re

        text = str(advisory_text or "")
        explicit = {match.group(1).strip() for match in _re.finditer(r"'([^']{2,40})'", text) if match.group(1).strip()}
        broad = set(explicit)
        stopwords = {
            "truthgate",
            "advisory",
            "director",
            "major",
            "minor",
            "critical",
            "issue",
            "issues",
            "advisor",
            "candidate",
            "warning",
            "warnings",
            "python",
            "refer",
            "reference",
            "후보",
            "경고",
            "감지",
            "참고용",
            "판단",
            "최종",
            "전달",
            "이상",
            "없음",
        }
        for token in _re.findall(r"[가-힣A-Za-z][가-힣A-Za-z0-9_]{1,}", text):
            if token.lower() in stopwords:
                continue
            broad.add(token)
        return explicit, broad

    def _suppress_conflicting_advisories(self, advisory_parts: list[str]) -> list[str]:
        """상위 티어와 같은 대상을 가리키는 하위 advisory는 Director MC에서 제거."""
        if not advisory_parts:
            return []

        meta = []
        for idx, part in enumerate(advisory_parts):
            tier, kind = self._classify_advisory_tier(part)
            explicit, broad = self._extract_advisory_subjects(part)
            meta.append(
                {
                    "idx": idx,
                    "text": part,
                    "tier": tier,
                    "kind": kind,
                    "explicit": explicit,
                    "broad": broad,
                }
            )

        suppressed: set[int] = set()
        for high in sorted(meta, key=lambda item: (-item["tier"], item["idx"])):
            if high["idx"] in suppressed:
                continue
            for low in meta:
                if low["idx"] == high["idx"] or low["idx"] in suppressed or low["tier"] >= high["tier"]:
                    continue
                overlap = set()
                if high["explicit"] and low["explicit"]:
                    overlap = high["explicit"] & low["explicit"]
                if not overlap and high["explicit"]:
                    overlap = high["explicit"] & low["broad"]
                if not overlap and low["explicit"]:
                    overlap = low["explicit"] & high["broad"]
                if overlap:
                    suppressed.add(low["idx"])
                    logging.info(
                        "[QI-SNR-3] advisory suppress: %s <- %s (shared=%s)",
                        low["kind"],
                        high["kind"],
                        ",".join(sorted(overlap)[:3]),
                    )

        return [part for idx, part in enumerate(advisory_parts) if idx not in suppressed]

    @staticmethod
    def _build_reference_only_block(reference_parts: list[str]) -> str:
        if not reference_parts:
            return ""
        header = [
            "[참고 — 판정 무관]",
            "아래 통계·추세는 참고 메모입니다. score/verdict의 직접 근거로 사용하지 마세요.",
        ]
        return (
            "\n".join(header) + "\n\n" + "\n\n".join(str(part).strip() for part in reference_parts if str(part).strip())
        )

    @staticmethod
    def _join_director_pack_parts(parts: list[str] | tuple[str, ...]) -> str:
        return "\n\n".join(str(part).strip() for part in parts if str(part).strip())

    @classmethod
    def _format_director_pack(cls, title: str, parts: list[str] | tuple[str, ...]) -> str:
        body = cls._join_director_pack_parts(parts)
        if not body:
            return ""
        return f"### [{title}]\n{body}"

    @staticmethod
    def _normalize_repair_scope_value(value: object) -> str:
        scope = str(value or "").strip().lower()
        return scope if scope in {"inplace", "partial", "full"} else "none"

    @staticmethod
    def _normalize_fix_target_kind(value: object) -> str:
        raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "entity": "entity_ref",
            "entityref": "entity_ref",
            "named_entity": "entity_ref",
            "name_ref": "entity_ref",
            "phrase": "local_phrase",
            "localphrase": "local_phrase",
            "sentence": "local_sentence",
            "localsentence": "local_sentence",
            "scene": "scene_model",
            "scenelevel": "scene_model",
            "scene_level": "scene_model",
            "scene_model": "scene_model",
        }
        normalized = aliases.get(raw, raw)
        return normalized if normalized in {"entity_ref", "local_phrase", "local_sentence", "scene_model"} else ""

    @classmethod
    def _resolve_primary_fix_target_kind(cls, kinds: list[str]) -> str:
        normalized = [cls._normalize_fix_target_kind(item) for item in kinds]
        cleaned = [item for item in normalized if item]
        if not cleaned:
            return ""
        if "scene_model" in cleaned:
            return "scene_model"
        if "local_sentence" in cleaned:
            return "local_sentence"
        if "local_phrase" in cleaned:
            return "local_phrase"
        return "entity_ref"

    @staticmethod
    def _normalize_fix_pack_list(
        raw: object,
        *,
        limit: int | None = None,
        item_limit: int | None = None,
    ) -> list[str]:
        if isinstance(raw, str):
            candidates = [raw]
        elif isinstance(raw, list):
            candidates = raw
        else:
            return []
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in candidates:
            text = " ".join(str(item or "").split()).strip()
            if not text:
                continue
            if item_limit is not None:
                text = text[:item_limit]
            if text in seen:
                continue
            seen.add(text)
            cleaned.append(text)
            if limit is not None and len(cleaned) >= limit:
                break
        return cleaned

    @staticmethod
    def _normalize_fix_pack_provenance(raw: object) -> str:
        token = str(raw or "").strip().lower()
        if token in {"director_authored", "runtime_backfilled", "runtime_synthesized"}:
            return token
        return ""

    @staticmethod
    def _normalize_repair_subtype_value(raw: object) -> str:
        token = str(raw or "").strip().lower().replace("-", "_").replace(" ", "_")
        return token if token else ""

    @classmethod
    def _normalize_repair_subtype_list(cls, raw: object) -> list[str]:
        if isinstance(raw, str):
            candidates = [part.strip() for part in raw.split(",")]
        elif isinstance(raw, list):
            candidates = raw
        else:
            candidates = []
        cleaned: list[str] = []
        for item in candidates:
            token = cls._normalize_repair_subtype_value(item)
            if not token or token in cleaned:
                continue
            cleaned.append(token)
            if len(cleaned) >= 6:
                break
        return cleaned

    @classmethod
    def _normalize_fix_pack_provenance_sources(cls, raw: object) -> list[str]:
        if isinstance(raw, str):
            raw = [part.strip() for part in raw.split(",")]
        elif not isinstance(raw, list):
            raw = []
        cleaned: list[str] = []
        for item in raw:
            text = " ".join(str(item or "").split()).strip()
            if not text or text in cleaned:
                continue
            cleaned.append(text)
            if len(cleaned) >= 4:
                break
        return cleaned

    @classmethod
    def _stamp_fix_pack_provenance(
        cls,
        fix_pack: object,
        *,
        provenance: str,
        provenance_sources: list[str] | None = None,
    ) -> dict:
        normalized = cls._normalize_fix_pack(fix_pack)
        if not normalized:
            return {}
        normalized_provenance = cls._normalize_fix_pack_provenance(provenance)
        if not normalized_provenance:
            return normalized
        normalized["provenance"] = normalized_provenance
        normalized_sources = cls._normalize_fix_pack_provenance_sources(provenance_sources or [])
        if normalized_sources:
            normalized["provenance_sources"] = normalized_sources
        return normalized

    @classmethod
    def _normalize_fix_pack(cls, raw: object) -> dict:
        payload = raw if isinstance(raw, dict) else {}
        must_fix = cls._normalize_fix_pack_list(payload.get("must_fix"), limit=None, item_limit=None)
        do_not_regress = cls._normalize_fix_pack_list(payload.get("do_not_regress"), limit=None, item_limit=None)
        success_condition = " ".join(str(payload.get("success_condition", "") or "").split()).strip()
        evidence_summary = " ".join(str(payload.get("evidence_summary", "") or "").split()).strip()
        provenance = cls._normalize_fix_pack_provenance(
            payload.get("provenance", payload.get("fix_pack_provenance", ""))
        )
        provenance_sources = cls._normalize_fix_pack_provenance_sources(
            payload.get("provenance_sources", payload.get("backfilled_from", []))
        )
        subtype_candidates: list[str] = []
        for key in ("subtype", "contradiction_subtype", "drift_subtype"):
            token = cls._normalize_repair_subtype_value(payload.get(key, ""))
            if token and token not in subtype_candidates:
                subtype_candidates.append(token)
        for key in ("subtypes", "contradiction_types"):
            for token in cls._normalize_repair_subtype_list(payload.get(key)):
                if token not in subtype_candidates:
                    subtype_candidates.append(token)

        raw_kinds = payload.get("target_kinds")
        if isinstance(raw_kinds, str):
            raw_kinds = [part.strip() for part in raw_kinds.split(",")]
        elif not isinstance(raw_kinds, list):
            raw_kinds = []
        if payload.get("target_kind"):
            raw_kinds = [payload.get("target_kind"), *raw_kinds]
        target_kinds = []
        for item in raw_kinds:
            kind = cls._normalize_fix_target_kind(item)
            if kind and kind not in target_kinds:
                target_kinds.append(kind)
        target_kind = cls._resolve_primary_fix_target_kind(target_kinds)
        patch_targets, patch_target_records = normalize_patch_target_records(
            payload.get("patch_target_records") or payload.get("patch_targets"),
            stage="stage4",
            container_kind="manuscript",
            default_target_kind=target_kind,
            limit=6,
        )

        normalized = {
            "patch_targets": patch_targets,
            "must_fix": must_fix,
            "do_not_regress": do_not_regress,
            "success_condition": success_condition,
            "target_kind": target_kind,
        }
        if patch_target_records:
            normalized["patch_target_records"] = patch_target_records
        if target_kinds:
            normalized["target_kinds"] = target_kinds
        if evidence_summary:
            normalized["evidence_summary"] = evidence_summary
        if subtype_candidates:
            normalized["subtype"] = subtype_candidates[0]
            if len(subtype_candidates) > 1:
                normalized["subtypes"] = subtype_candidates[:4]
        if provenance:
            normalized["provenance"] = provenance
        if provenance_sources:
            normalized["provenance_sources"] = provenance_sources

        has_payload = any(
            normalized.get(key)
            for key in (
                "patch_targets",
                "must_fix",
                "do_not_regress",
                "success_condition",
                "target_kind",
                "evidence_summary",
            )
        )
        return normalized if has_payload else {}

    @classmethod
    def _evaluate_fix_pack_contract(cls, fix_pack: object) -> dict[str, object]:
        normalized = cls._normalize_fix_pack(fix_pack)
        if not normalized:
            return {"ready": False, "reason": "missing_fix_pack", "fix_pack": {}}
        if not normalized.get("patch_targets"):
            return {"ready": False, "reason": "missing_patch_targets", "fix_pack": normalized}
        if not normalized.get("must_fix"):
            return {"ready": False, "reason": "missing_must_fix", "fix_pack": normalized}
        if not normalized.get("do_not_regress"):
            return {"ready": False, "reason": "missing_do_not_regress", "fix_pack": normalized}
        if not normalized.get("success_condition"):
            return {"ready": False, "reason": "missing_success_condition", "fix_pack": normalized}
        target_kind = str(normalized.get("target_kind", "") or "")
        if target_kind == "scene_model":
            return {"ready": False, "reason": "scene_model_target", "fix_pack": normalized}
        if target_kind not in {"entity_ref", "local_phrase", "local_sentence"}:
            return {"ready": False, "reason": "invalid_target_kind", "fix_pack": normalized}
        return {"ready": True, "reason": "", "fix_pack": normalized}

    def _evaluate_pass_with_fix_contract(self, director_result: dict | None) -> dict[str, object]:
        normalized = self._normalize_director_gate_semantics(director_result)
        fix_scope = str(normalized.get("fix_scope", "") or "").strip().lower()
        fix_pack_contract = self._evaluate_fix_pack_contract(normalized.get("fix_pack"))
        if fix_scope != "inplace":
            return {
                "eligible": False,
                "reason": "missing_fix_scope" if not fix_scope else "non_local_fix_scope",
                "fix_scope": fix_scope,
                "fix_pack": fix_pack_contract.get("fix_pack", {}),
            }
        if not fix_pack_contract.get("ready"):
            return {
                "eligible": False,
                "reason": str(fix_pack_contract.get("reason", "") or "missing_fix_pack"),
                "fix_scope": fix_scope,
                "fix_pack": fix_pack_contract.get("fix_pack", {}),
            }
        return {
            "eligible": True,
            "reason": "",
            "fix_scope": fix_scope,
            "fix_pack": fix_pack_contract.get("fix_pack", {}),
        }

    @staticmethod
    def _pass_with_fix_contract_message(reason: str) -> str:
        messages = {
            "missing_fix_scope": "explicit local fix_scope is missing",
            "non_local_fix_scope": "fix_scope is not inplace-local",
            "missing_fix_pack": "Fix Pack is missing",
            "missing_patch_targets": "Fix Pack patch_targets is empty",
            "missing_must_fix": "Fix Pack must_fix is empty",
            "missing_do_not_regress": "Fix Pack do_not_regress is empty",
            "missing_success_condition": "Fix Pack success_condition is empty",
            "invalid_target_kind": "Fix Pack target_kind is not local-fixable",
            "scene_model_target": "Fix Pack target_kind=scene_model requires broader rewrite",
        }
        return messages.get(reason, "PASS_WITH_FIX contract is invalid")

    def _build_fix_pack_payload(self, director_result: dict | None) -> dict:
        if not isinstance(director_result, dict):
            return {}
        fix_pack = self._normalize_fix_pack(director_result.get("fix_pack"))
        if not fix_pack:
            return {}
        payload = {
            "patch_targets": list(fix_pack.get("patch_targets") or []),
            "must_fix": list(fix_pack.get("must_fix") or [])[:5],
            "do_not_regress": list(fix_pack.get("do_not_regress") or [])[:5],
            "success_condition": str(fix_pack.get("success_condition", "") or ""),
            "target_kind": str(fix_pack.get("target_kind", "") or ""),
        }
        if fix_pack.get("patch_target_records"):
            payload["patch_target_records"] = list(fix_pack.get("patch_target_records") or [])[:6]
        if fix_pack.get("evidence_summary"):
            payload["evidence_summary"] = str(fix_pack.get("evidence_summary", "") or "")
        if fix_pack.get("target_kinds"):
            payload["target_kinds"] = list(fix_pack.get("target_kinds") or [])[:4]
        if fix_pack.get("subtype"):
            payload["subtype"] = str(fix_pack.get("subtype", "") or "")
        if fix_pack.get("subtypes"):
            payload["subtypes"] = list(fix_pack.get("subtypes") or [])[:4]
        if fix_pack.get("provenance"):
            payload["provenance"] = str(fix_pack.get("provenance", "") or "")
        if fix_pack.get("provenance_sources"):
            payload["provenance_sources"] = list(fix_pack.get("provenance_sources") or [])[:4]
        return payload

    @staticmethod
    def _selected_candidate_index_for_fix_contract(director_result: dict | None) -> int | None:
        if not isinstance(director_result, dict):
            return None
        selected = str(director_result.get("selected", "") or "").strip().upper()
        if selected in {"A", "B", "C"}:
            return ord(selected) - ord("A")
        if selected.isdigit():
            index = int(selected) - 1
            return index if index >= 0 else None
        return None

    def _build_npc_drift_relation_tag_fix_pack(self, director_result: dict | None) -> dict:
        if not isinstance(director_result, dict):
            return {}
        metadata = getattr(self, "_last_advisory_metadata", None) or {}
        drift_items = metadata.get("npc_drift") or []
        if not isinstance(drift_items, list) or not drift_items:
            return {}
        selected_idx = self._selected_candidate_index_for_fix_contract(director_result)
        relevant: list[dict] = []
        for item in drift_items:
            if not isinstance(item, dict):
                continue
            subtype = str(item.get("subtype", item.get("drift_subtype", "")) or "").strip().lower()
            if subtype != "relation_tag_semantic":
                continue
            cand_idx = item.get("_cand_idx")
            if selected_idx is not None and cand_idx not in {None, selected_idx}:
                continue
            relevant.append(item)
        if not relevant:
            return {}

        npc_labels: list[str] = []
        axis_labels: list[str] = []
        direction_labels: list[str] = []
        relation_label_kinds: set[str] = set()
        for item in relevant:
            npc = str(item.get("npc", "") or "").strip()
            if npc and npc not in npc_labels:
                npc_labels.append(npc)
            axes = [str(axis).strip() for axis in (item.get("expected_relation_axes") or []) if str(axis).strip()]
            if npc and axes:
                label = f"{npc}:{'/'.join(axes)}"
                if label not in axis_labels:
                    axis_labels.append(label)
            direction_label = str(item.get("relation_direction_label", "") or "").strip()
            if direction_label and direction_label not in direction_labels:
                direction_labels.append(direction_label)
            relation_label_kind = str(item.get("relation_label_kind", "") or "").strip()
            if relation_label_kind:
                relation_label_kinds.add(relation_label_kind)

        target_suffix = f" ({', '.join(npc_labels[:2])})" if npc_labels else ""
        evidence_summary = "runtime npc_drift relation-tag semantic backfill"
        evidence_labels = list(axis_labels[:2])
        for label in direction_labels:
            if label not in evidence_labels:
                evidence_labels.append(label)
        if evidence_labels:
            evidence_summary = f"{evidence_summary}: {'; '.join(evidence_labels[:2])}"
        if "plain_directional" in relation_label_kinds:
            must_fix = ["relation_to_protag 방향성과 canonical relation semantics에 어긋난 관계 표현을 국소 수정"]
            do_not_regress = ["평문 관계 태그를 literal 뒤집기로 해석하지 말고 canonical direction 의미 정렬만 수행"]
            success_condition = (
                "NpcDrift relation_to_protag 경고가 사라지고 관계 프레이밍이 canonical direction과 의미적으로 합치한다"
            )
        else:
            must_fix = [
                "relation_to_protag 압축 관계 태그와 의미적으로 어긋난 관계 표현을 canonical relation framing에 맞게 국소 수정"
            ]
            do_not_regress = ["압축 관계 태그 숫자/토큰을 원고에 그대로 삽입하지 말고 prose 의미 정렬만 수행"]
            success_condition = "NpcDrift relation_to_protag 경고가 사라지고 관계 프레이밍이 canonical relation tag 축과 의미적으로 합치한다"
        return {
            "patch_targets": [f"NPC relation_to_protag 관계 프레이밍 문장{target_suffix}"],
            "must_fix": must_fix,
            "do_not_regress": do_not_regress,
            "success_condition": success_condition,
            "target_kind": "local_phrase",
            "subtype": "relation_tag_semantic",
            "evidence_summary": evidence_summary,
        }

    @staticmethod
    def _infer_flashback_contradiction_subtype(item: dict | None) -> str:
        if not isinstance(item, dict):
            return ""
        explicit = str(item.get("subtype", item.get("contradiction_subtype", "")) or "").strip().lower()
        if explicit in {"location", "movement", "facing", "dialogue", "timeline", "other"}:
            return explicit
        text = " ".join(
            str(item.get(key, "") or "")
            for key in ("issue", "patch_anchor", "expected_truth", "local_fix_hint", "referenced_context")
        )
        if any(token in text for token in ("현관문", "서재", "복도", "장소", "목적지")):
            return "location"
        if any(token in text for token in ("발걸음", "멈추", "따라", "향하", "걸어", "뒤돌아", "나아")):
            return "movement"
        if any(token in text for token in ("정면", "등 뒤", "마주", "대면", "내려다")):
            return "facing"
        if any(token in text for token in ("대답", "목소리", "말", "대화", "천천히 생각해보겠다")):
            return "dialogue"
        if any(token in text for token in ("직후", "이후", "먼저", "나중", "타임라인")):
            return "timeline"
        return "other"

    def _build_flashback_continuity_fix_pack(self, director_result: dict | None) -> dict:
        if not isinstance(director_result, dict):
            return {}
        metadata = getattr(self, "_last_advisory_metadata", None) or {}
        flashback_items = metadata.get("flashback") or []
        if not isinstance(flashback_items, list) or not flashback_items:
            return {}
        selected_idx = self._selected_candidate_index_for_fix_contract(director_result)
        relevant: list[dict] = []
        for item in flashback_items:
            if not isinstance(item, dict):
                continue
            cand_idx = item.get("_cand_idx")
            if selected_idx is not None and cand_idx not in {None, selected_idx}:
                continue
            local_fixable = item.get("local_fixable")
            subtype = self._infer_flashback_contradiction_subtype(item)
            if isinstance(local_fixable, bool):
                if not local_fixable:
                    continue
            elif subtype not in {"location", "movement", "facing", "dialogue", "timeline"}:
                continue
            relevant.append(item)
        if not relevant:
            return {}

        patch_targets: list[str] = []
        must_fix: list[str] = []
        do_not_regress: list[str] = []
        subtype_labels: list[str] = []
        target_kind = "local_sentence"
        target_templates = {
            "location": (
                "회상 장면 장소/목적지 서술 문장",
                "회상 장면의 장소 또는 목적지 묘사를 prior manuscript truth에 맞게 국소 수정",
                "prior manuscript에 없는 회상 장소/목적지를 새로 추가하지 말 것",
            ),
            "movement": (
                "회상 장면 동선/멈춤 서술 문장",
                "회상 장면의 동선 또는 멈춤 여부를 prior manuscript truth에 맞게 국소 수정",
                "prior manuscript의 동선/멈춤 여부를 뒤집는 새 행동을 추가하지 말 것",
            ),
            "facing": (
                "회상 장면 대면/시선 서술 문장",
                "회상 장면의 대면 여부와 시선 관계를 prior manuscript truth에 맞게 국소 수정",
                "prior manuscript에 없는 대면/시선 전환을 추가하지 말 것",
            ),
            "dialogue": (
                "회상 장면 대사/응답 서술 문장",
                "회상 장면의 대사 또는 응답 내용을 prior manuscript truth에 맞게 국소 수정",
                "prior manuscript에 없는 새 발화를 회상 장면에 추가하지 말 것",
            ),
            "timeline": (
                "회상 장면 순서/타이밍 서술 문장",
                "회상 장면의 순서와 타이밍 묘사를 prior manuscript truth에 맞게 국소 수정",
                "prior manuscript의 사건 순서를 뒤집는 새 회상 전개를 추가하지 말 것",
            ),
            "other": (
                "회상 장면 핵심 서술 문장",
                "회상 장면의 핵심 사실 묘사를 prior manuscript truth에 맞게 국소 수정",
                "prior manuscript에 없는 핵심 사실을 회상 장면에 추가하지 말 것",
            ),
        }
        for item in relevant:
            subtype = self._infer_flashback_contradiction_subtype(item)
            if subtype and subtype not in subtype_labels:
                subtype_labels.append(subtype)
            item_target_kind = str(item.get("target_kind", "") or "").strip()
            if item_target_kind in {"local_phrase", "local_sentence"}:
                target_kind = item_target_kind
            patch_anchor = str(item.get("patch_anchor", "") or "").strip()
            marker = str(item.get("marker", "") or "").strip()
            default_target, default_fix, default_guard = target_templates.get(
                subtype or "other", target_templates["other"]
            )
            target_label = patch_anchor or (f"{default_target} ('{marker}')" if marker else default_target)
            if target_label and target_label not in patch_targets:
                patch_targets.append(target_label)
            if default_fix not in must_fix:
                must_fix.append(default_fix)
            expected_truth = str(item.get("expected_truth", "") or item.get("referenced_context", "") or "").strip()
            if expected_truth:
                guard_line = f"prior truth: {expected_truth}"
            else:
                guard_line = default_guard
            if guard_line and guard_line not in do_not_regress:
                do_not_regress.append(guard_line)

        evidence_summary = "runtime flashback continuity backfill"
        if subtype_labels:
            evidence_summary = f"{evidence_summary}: {', '.join(subtype_labels[:3])}"
        return {
            "patch_targets": patch_targets[:3],
            "must_fix": must_fix[:4],
            "do_not_regress": do_not_regress[:4],
            "success_condition": "FlashbackVerifier 경고가 사라지고 회상 continuity가 prior manuscript truth와 합치한다",
            "target_kind": target_kind,
            "subtype": subtype_labels[0] if subtype_labels else "other",
            "subtypes": subtype_labels[:4],
            "evidence_summary": evidence_summary,
        }

    def _backfill_strong_advisory_fix_pack(self, director_result: dict | None) -> dict:
        if not isinstance(director_result, dict):
            return {}
        escalation = director_result.get("strong_advisory_escalation")
        if not isinstance(escalation, dict):
            return self._normalize_fix_pack(director_result.get("fix_pack"))
        fix_pack = self._normalize_fix_pack(director_result.get("fix_pack"))
        triggered = [str(item).strip().lower() for item in (escalation.get("triggered_by") or []) if str(item).strip()]
        target_kind = str(fix_pack.get("target_kind", "") or "").strip().lower()
        semantic_fix_pack = (
            self._build_npc_drift_relation_tag_fix_pack(director_result) if "npc_drift" in triggered else {}
        )
        flashback_fix_pack = (
            self._build_flashback_continuity_fix_pack(director_result) if "flashback" in triggered else {}
        )
        if not fix_pack and semantic_fix_pack:
            escalation["local_fix_contract_backfilled"] = True
            escalation["backfilled_from"] = ["npc_drift_relation_tag_semantic"]
            escalation["backfill_target_kind"] = semantic_fix_pack.get("target_kind", "")
            return self._stamp_fix_pack_provenance(
                semantic_fix_pack,
                provenance="runtime_synthesized",
                provenance_sources=["npc_drift_relation_tag_semantic"],
            )
        if not fix_pack and flashback_fix_pack:
            escalation["local_fix_contract_backfilled"] = True
            escalation["backfilled_from"] = ["flashback_continuity_localfix"]
            escalation["backfill_target_kind"] = flashback_fix_pack.get("target_kind", "")
            return self._stamp_fix_pack_provenance(
                flashback_fix_pack,
                provenance="runtime_synthesized",
                provenance_sources=["flashback_continuity_localfix"],
            )
        if not fix_pack:
            return {}
        if target_kind == "scene_model":
            return fix_pack
        changed = False
        specialized_sources: list[str] = []
        if semantic_fix_pack:
            semantic_changed = False
            if not fix_pack.get("target_kind"):
                fix_pack["target_kind"] = semantic_fix_pack.get("target_kind", "")
                target_kind = str(fix_pack.get("target_kind", "") or "").strip().lower()
                changed = True
                semantic_changed = True
            if target_kind in {"entity_ref", "local_phrase", "local_sentence"}:
                for key in ("patch_targets", "must_fix", "do_not_regress"):
                    if not fix_pack.get(key) and semantic_fix_pack.get(key):
                        fix_pack[key] = list(semantic_fix_pack.get(key) or [])
                        changed = True
                        semantic_changed = True
                if not fix_pack.get("success_condition") and semantic_fix_pack.get("success_condition"):
                    fix_pack["success_condition"] = str(semantic_fix_pack.get("success_condition", "") or "")
                    changed = True
                    semantic_changed = True
                if semantic_fix_pack.get("evidence_summary"):
                    existing_summary = str(fix_pack.get("evidence_summary", "") or "").strip()
                    semantic_summary = str(semantic_fix_pack.get("evidence_summary", "") or "").strip()
                    if semantic_summary and semantic_summary not in existing_summary:
                        fix_pack["evidence_summary"] = (
                            f"{existing_summary}; {semantic_summary}" if existing_summary else semantic_summary
                        )
                        changed = True
                        semantic_changed = True
            if semantic_changed and "npc_drift_relation_tag_semantic" not in specialized_sources:
                specialized_sources.append("npc_drift_relation_tag_semantic")
        if flashback_fix_pack:
            flashback_changed = False
            if not fix_pack.get("target_kind"):
                fix_pack["target_kind"] = flashback_fix_pack.get("target_kind", "")
                target_kind = str(fix_pack.get("target_kind", "") or "").strip().lower()
                changed = True
                flashback_changed = True
            if target_kind in {"entity_ref", "local_phrase", "local_sentence"}:
                for key in ("patch_targets", "must_fix", "do_not_regress"):
                    if not fix_pack.get(key) and flashback_fix_pack.get(key):
                        fix_pack[key] = list(flashback_fix_pack.get(key) or [])
                        changed = True
                        flashback_changed = True
                if not fix_pack.get("success_condition") and flashback_fix_pack.get("success_condition"):
                    fix_pack["success_condition"] = str(flashback_fix_pack.get("success_condition", "") or "")
                    changed = True
                    flashback_changed = True
                if flashback_fix_pack.get("evidence_summary"):
                    existing_summary = str(fix_pack.get("evidence_summary", "") or "").strip()
                    flashback_summary = str(flashback_fix_pack.get("evidence_summary", "") or "").strip()
                    if flashback_summary and flashback_summary not in existing_summary:
                        fix_pack["evidence_summary"] = (
                            f"{existing_summary}; {flashback_summary}" if existing_summary else flashback_summary
                        )
                        changed = True
                        flashback_changed = True
            if flashback_changed and "flashback_continuity_localfix" not in specialized_sources:
                specialized_sources.append("flashback_continuity_localfix")
        if target_kind not in {"entity_ref", "local_phrase", "local_sentence"}:
            return fix_pack
        if not triggered:
            return fix_pack
        templates = {
            "truth_gate": (
                "정합성 충돌 문장",
                "정합성 충돌을 일으킨 문장을 canonical truth에 맞게 국소 수정",
            ),
            "npc_drift": (
                "NPC 역할/관계 서술 문장",
                "NPC 역할 또는 관계 표현을 canonical truth에 맞게 국소 수정",
            ),
            "rel_drift": (
                "관계 프레이밍 문장",
                "인물 간 관계 프레이밍을 canonical relation truth에 맞게 국소 수정",
            ),
            "flashback": (
                "회상/기억 서술 문장",
                "회상 또는 기억 서술을 prior authority와 맞게 국소 수정",
            ),
            "info_paradox": (
                "정보 상태 충돌 문장",
                "정보 상태 충돌을 일으킨 문장을 canonical information state에 맞게 국소 수정",
            ),
        }
        if not fix_pack.get("patch_targets"):
            patch_targets: list[str] = []
            for key in triggered:
                label = str(templates.get(key, ("", ""))[0] or "").strip()
                if label and label not in patch_targets:
                    patch_targets.append(label)
            if patch_targets:
                fix_pack["patch_targets"] = patch_targets[:3]
                changed = True
        if not fix_pack.get("must_fix"):
            must_fix: list[str] = []
            for key in triggered:
                instruction = str(templates.get(key, ("", ""))[1] or "").strip()
                if instruction and instruction not in must_fix:
                    must_fix.append(instruction)
            if must_fix:
                fix_pack["must_fix"] = must_fix[:4]
                changed = True
        if changed:
            evidence_marker = f"runtime strong advisory backfill: {', '.join(triggered)}"
            existing_summary = str(fix_pack.get("evidence_summary", "") or "").strip()
            if evidence_marker not in existing_summary:
                fix_pack["evidence_summary"] = (
                    f"{existing_summary}; {evidence_marker}" if existing_summary else evidence_marker
                )
            escalation["local_fix_contract_backfilled"] = True
            escalation["backfilled_from"] = specialized_sources or list(triggered)
            escalation["backfill_target_kind"] = target_kind
            return self._stamp_fix_pack_provenance(
                fix_pack,
                provenance="runtime_backfilled",
                provenance_sources=specialized_sources or list(triggered),
            )
        return fix_pack

    def _enforce_pass_with_fix_contract(self, director_result: dict | None) -> dict:
        normalized = self._normalize_director_gate_semantics(director_result)
        if not normalized:
            return {}
        normalized["fix_pack"] = self._normalize_fix_pack(normalized.get("fix_pack"))
        if str(normalized.get("final_verdict", "") or "").strip().upper() != "PASS_WITH_FIX":
            return normalized

        contract = self._evaluate_pass_with_fix_contract(normalized)
        if contract.get("eligible"):
            normalized["fix_scope"] = "inplace"
            normalized["repair_scope"] = "inplace"
            normalized["fix_pack"] = contract.get("fix_pack", {})
            return normalized

        reason = str(contract.get("reason", "") or "missing_fix_pack")
        # [IFC] Track consecutive empty-patch rounds for rewrite escalation
        if reason == "missing_patch_targets":
            self._consecutive_empty_patches += 1
        else:
            self._consecutive_empty_patches = 0
        note = f"[Lane3 Gate] PASS_WITH_FIX downgraded: {self._pass_with_fix_contract_message(reason)}"
        fallback_fix_scope = str(normalized.get("fix_scope", "") or "").strip().lower()
        if fallback_fix_scope not in {"partial", "full"}:
            fallback_fix_scope = "partial"
        normalized["fix_scope"] = fallback_fix_scope
        normalized["repair_scope"] = fallback_fix_scope
        fix_scope_reasoning = str(normalized.get("fix_scope_reasoning", "") or "").strip()
        if note not in fix_scope_reasoning:
            normalized["fix_scope_reasoning"] = (
                f"{fix_scope_reasoning}\n{note}".strip() if fix_scope_reasoning else note
            )
        verdict_reason = str(normalized.get("verdict_reason", "") or "").strip()
        if note not in verdict_reason:
            normalized["verdict_reason"] = f"{note}\n{verdict_reason}".strip() if verdict_reason else note
        feedback = normalized.get("feedback")
        if isinstance(feedback, str):
            feedback = {"issues": [feedback]}
        elif not isinstance(feedback, dict):
            feedback = {}
        issues = [str(item).strip() for item in (feedback.get("issues") or []) if str(item).strip()]
        if note not in issues:
            issues.insert(0, note)
        feedback["issues"] = issues[:8]
        normalized["feedback"] = feedback
        normalized["action_items"] = feedback.get("action_items", []) if isinstance(feedback, dict) else []
        normalized = self._apply_director_gate_update(
            normalized,
            final_verdict="REJECT",
            gate_basis=f"pass_with_fix_contract_{reason}",
            repair_scope=fallback_fix_scope,
        )
        return normalized

    def _set_retry_budget_axes(
        self,
        *,
        round_num: int,
        repair_budget: str,
        strategy_budget: str,
        reject_bucket: str = "",
        previous_attempt: dict | None = None,
    ) -> dict[str, str]:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        guidance_budget = (
            "augmented"
            if any(
                str(previous_attempt.get(key, "") or "").strip()
                for key in ("runtime_advisory", "retry_directives", "fix_scope_reasoning")
            )
            else "baseline"
        )
        escalation_budget = "none"
        if reject_bucket == "structure_error":
            escalation_budget = "tot"
        elif reject_bucket == "constraint_violation":
            escalation_budget = "mad"
        axes = {
            "round": "initial" if round_num == 0 else f"retry_round_{round_num + 1}",
            "repair": str(repair_budget or ""),
            "strategy": str(strategy_budget or ""),
            "escalation": escalation_budget,
            "guidance": guidance_budget,
        }
        self._last_retry_budget_axes = axes
        return axes

    def _normalize_director_gate_semantics(self, director_result: dict | None) -> dict:
        if not isinstance(director_result, dict):
            return {}
        authoritative_fix_scope = str(
            director_result.get("authoritative_fix_scope", director_result.get("fix_scope", "")) or ""
        ).strip()
        director_verdict = (
            str(
                director_result.get("director_verdict")
                or director_result.get("original_verdict")
                or director_result.get("verdict")
                or "REJECT"
            ).strip()
            or "REJECT"
        )
        final_verdict = (
            str(
                director_result.get("final_verdict") or director_result.get("verdict") or director_verdict or "REJECT"
            ).strip()
            or "REJECT"
        )
        repair_scope = self._normalize_repair_scope_value(
            director_result.get("repair_scope") or director_result.get("fix_scope")
        )
        gate_basis = str(director_result.get("gate_basis") or "").strip()
        if not gate_basis:
            if final_verdict == "REJECT" and director_verdict in {"PASS", "PASS_WITH_FIX"}:
                gate_basis = "quality_floor_fail"
            elif final_verdict == "PASS":
                gate_basis = "director_primary_pass"
            elif final_verdict == "PASS_WITH_FIX":
                gate_basis = "director_primary_pass_with_fix"
            else:
                gate_basis = "director_primary_reject"
        director_result["director_verdict"] = director_verdict
        director_result["final_verdict"] = final_verdict
        director_result["gate_basis"] = gate_basis
        director_result["repair_scope"] = repair_scope
        director_result["fix_pack"] = self._normalize_fix_pack(director_result.get("fix_pack"))
        director_result["verdict"] = final_verdict
        director_result["authoritative_fix_scope"] = authoritative_fix_scope

        # [Lane2-G1] Strong advisory binding: tier-2+ advisory classes must not end as plain PASS.
        # TruthGate (tier 3) and NpcDrift/RelDrift/Flashback/InfoParadox (tier 2) are binding
        # advisory classes that require at minimum PASS_WITH_FIX acknowledgement.
        _STRONG_ADVISORY_KEYS = frozenset({"truth_gate", "npc_drift", "rel_drift", "flashback", "info_paradox"})
        _advisory_summary = getattr(self, "_last_advisory_summary", None) or {}
        _triggered = sorted(k for k in _STRONG_ADVISORY_KEYS if _advisory_summary.get(k))
        if final_verdict == "PASS" and _triggered:
            final_verdict = "PASS_WITH_FIX"
            director_result["final_verdict"] = "PASS_WITH_FIX"
            director_result["verdict"] = "PASS_WITH_FIX"
            director_result["gate_basis"] = "strong_advisory_escalation"
            director_result.setdefault(
                "strong_advisory_escalation",
                {
                    "source_verdict": "PASS",
                    "escalated_to": "PASS_WITH_FIX",
                    "triggered_by": _triggered,
                },
            )
            logging.warning(
                "[Stage4Gate] strong advisory escalation: PASS → PASS_WITH_FIX (classes=%s)",
                ",".join(_triggered),
            )
            _emit_stage4_ui_log(
                self.ctx.ui,
                f"   [Stage4Gate] strong advisory escalation: PASS → PASS_WITH_FIX ({', '.join(_triggered)})",
                component="director_gate",
                event_kind="policy",
                meta={
                    "gate_basis": "strong_advisory_escalation",
                    "source_verdict": "PASS",
                    "final_verdict": "PASS_WITH_FIX",
                    "triggered_by": list(_triggered),
                },
            )

        # [DCM-T2] Authoritative fix_scope contract validation
        _normalized_authoritative_scope = authoritative_fix_scope.lower()
        if final_verdict in ("REJECT", "PASS_WITH_FIX") and _normalized_authoritative_scope not in {
            "inplace",
            "partial",
            "full",
        }:
            _vtype = (
                "blank_authoritative_fix_scope"
                if not _normalized_authoritative_scope
                else "invalid_authoritative_fix_scope"
            )
            director_result.setdefault(
                "authoritative_fix_scope_violation",
                {
                    "type": _vtype,
                    "raw_value": authoritative_fix_scope,
                    "verdict": final_verdict,
                },
            )
            logging.warning(
                "[Stage4Gate] fix_scope contract violation: verdict=%s fix_scope=%r",
                final_verdict,
                authoritative_fix_scope,
            )
            # [Lane2-G2] PASS_WITH_FIX with blank/invalid fix_scope cannot run the repair loop.
            # Gate it to REJECT so the loop is not entered with an unresolved scope contract.
            if final_verdict == "PASS_WITH_FIX":
                _is_advisory_escalation = bool(director_result.get("strong_advisory_escalation"))
                _g2_basis = (
                    "strong_advisory_escalation_no_scope" if _is_advisory_escalation else "fix_scope_contract_violation"
                )
                final_verdict = "REJECT"
                director_result["final_verdict"] = "REJECT"
                director_result["verdict"] = "REJECT"
                director_result["gate_basis"] = _g2_basis
                # [Lane2-G2a] Advisory escalation REJECT must carry actionable fix_scope
                # so downstream reject guidance produces meaningful retry direction
                # instead of a blank-scope loop (C-1 seam fix).
                if _is_advisory_escalation:
                    director_result["fix_scope"] = "partial"
                    director_result["repair_scope"] = "partial"
                    _advisory_classes = sorted(
                        director_result.get("strong_advisory_escalation", {}).get("triggered_by", [])
                    )
                    _advisory_reason = (
                        f"[Lane2-G2a] Advisory escalation (classes={','.join(_advisory_classes)}) "
                        "requires non-local rewrite; fix_scope widened to partial"
                    )
                    _existing_reasoning = str(director_result.get("fix_scope_reasoning", "") or "").strip()
                    director_result["fix_scope_reasoning"] = (
                        f"{_existing_reasoning}\n{_advisory_reason}".strip()
                        if _existing_reasoning
                        else _advisory_reason
                    )
                logging.warning(
                    "[Stage4Gate] PASS_WITH_FIX → REJECT: repair blocked, fix_scope invalid"
                    " (gate_basis=%s type=%s scope=%r)",
                    _g2_basis,
                    _vtype,
                    authoritative_fix_scope,
                )
                _emit_stage4_ui_log(
                    self.ctx.ui,
                    "   [Stage4Gate] PASS_WITH_FIX → REJECT: repair blocked, fix_scope invalid",
                    component="director_gate",
                    event_kind="policy",
                    meta={
                        "gate_basis": _g2_basis,
                        "violation_type": _vtype,
                        "authoritative_fix_scope": authoritative_fix_scope,
                        "triggered_by": list(
                            director_result.get("strong_advisory_escalation", {}).get("triggered_by", [])
                        ),
                    },
                )

        # [Lane2-G2b] Strong advisory escalation may only stay PASS_WITH_FIX when the
        # result is truly local-fixable: fix_scope=inplace and fix_pack contract ready.
        if final_verdict == "PASS_WITH_FIX" and isinstance(director_result.get("strong_advisory_escalation"), dict):
            director_result["fix_pack"] = self._backfill_strong_advisory_fix_pack(director_result)
            _runtime_fix_scope = str(director_result.get("fix_scope") or authoritative_fix_scope or "").strip().lower()
            _fix_pack_contract = self._evaluate_fix_pack_contract(director_result.get("fix_pack"))
            _local_contract_ready = _runtime_fix_scope == "inplace" and bool(_fix_pack_contract.get("ready"))
            if not _local_contract_ready:
                final_verdict = "REJECT"
                director_result["final_verdict"] = "REJECT"
                director_result["verdict"] = "REJECT"
                director_result["gate_basis"] = "strong_advisory_escalation_non_local_fix"
                _widened_scope = _runtime_fix_scope if _runtime_fix_scope in {"partial", "full"} else "partial"
                director_result["fix_scope"] = _widened_scope
                director_result["repair_scope"] = _widened_scope
                _contract_reason = (
                    str(_fix_pack_contract.get("reason", "") or "non_local_fix_scope")
                    if _runtime_fix_scope == "inplace"
                    else "non_local_fix_scope"
                )
                _contract_message = self._pass_with_fix_contract_message(_contract_reason)
                _reason_line = (
                    "[Lane2-G2b] Strong advisory escalation requires a ready local fix contract; "
                    f"routed to REJECT ({_contract_message}, scope={_widened_scope})"
                )
                _existing_reasoning = str(director_result.get("fix_scope_reasoning", "") or "").strip()
                director_result["fix_scope_reasoning"] = (
                    f"{_existing_reasoning}\n{_reason_line}".strip() if _existing_reasoning else _reason_line
                )
                director_result.setdefault("strong_advisory_escalation", {}).update(
                    {
                        "requires_local_fix_contract": True,
                        "local_fix_contract": {
                            "ready": bool(_fix_pack_contract.get("ready")),
                            "reason": _contract_reason,
                            "fix_scope": _runtime_fix_scope,
                        },
                    }
                )
                logging.warning(
                    "[Stage4Gate] strong advisory escalation forced REJECT: local fix contract invalid"
                    " (scope=%s reason=%s)",
                    _runtime_fix_scope or "<blank>",
                    _contract_reason,
                )
                _emit_stage4_ui_log(
                    self.ctx.ui,
                    "   [Stage4Gate] strong advisory escalation forced REJECT: local fix contract invalid",
                    component="director_gate",
                    event_kind="policy",
                    meta={
                        "gate_basis": "strong_advisory_escalation_non_local_fix",
                        "triggered_by": list(
                            director_result.get("strong_advisory_escalation", {}).get("triggered_by", [])
                        ),
                        "fix_scope": _runtime_fix_scope,
                        "contract_reason": _contract_reason,
                    },
                )

        if director_result.get("fix_pack"):
            _normalized_fix_pack = self._normalize_fix_pack(director_result.get("fix_pack"))
            if _normalized_fix_pack and not _normalized_fix_pack.get("provenance"):
                _normalized_fix_pack = self._stamp_fix_pack_provenance(
                    _normalized_fix_pack,
                    provenance="director_authored",
                )
            director_result["fix_pack"] = _normalized_fix_pack

        return director_result

    def _apply_director_gate_update(
        self,
        director_result: dict | None,
        *,
        final_verdict: str | None = None,
        gate_basis: str | None = None,
        repair_scope: str | None = None,
    ) -> dict:
        normalized = self._normalize_director_gate_semantics(director_result)
        if not normalized:
            return {}
        if final_verdict:
            normalized["final_verdict"] = str(final_verdict)
            normalized["verdict"] = str(final_verdict)
        if gate_basis:
            normalized["gate_basis"] = str(gate_basis)
        if repair_scope is not None:
            normalized["repair_scope"] = self._normalize_repair_scope_value(repair_scope)
        elif "repair_scope" not in normalized:
            normalized["repair_scope"] = self._normalize_repair_scope_value(normalized.get("fix_scope"))
        return normalized

    def _build_gate_semantics_payload(self, director_result: dict | None) -> dict[str, object]:
        normalized = self._normalize_director_gate_semantics(director_result)
        if not normalized:
            return {}
        _authoritative_scope = str(normalized.get("authoritative_fix_scope", "") or "").strip().lower()
        _runtime_scope = str(normalized.get("fix_scope", "") or "").strip().lower()
        _fix_pack = self._normalize_fix_pack(normalized.get("fix_pack"))
        _verdict_layers = self._build_verdict_layers_payload(normalized)
        payload: dict[str, object] = {
            "director_verdict": str(normalized.get("director_verdict", "") or ""),
            "final_verdict": str(normalized.get("final_verdict", "") or ""),
            "gate_basis": str(normalized.get("gate_basis", "") or ""),
            "repair_scope": str(normalized.get("repair_scope", "none") or "none"),
            "authoritative_fix_scope": str(normalized.get("authoritative_fix_scope", "") or ""),
            "scope_origin": {
                "fix_scope": (
                    "runtime_widened"
                    if _runtime_scope and _runtime_scope != _authoritative_scope
                    else "director_authoritative"
                ),
                "authoritative_fix_scope": "director_authoritative",
                "repair_scope": "runtime_lane",
            },
        }
        if _verdict_layers:
            payload["verdict_layers"] = _verdict_layers
        # [DCM-T3] Surface authoritative fix_scope violation in gate semantics evidence
        violation = normalized.get("authoritative_fix_scope_violation")
        if isinstance(violation, dict):
            payload["authoritative_fix_scope_violation"] = violation
        escalation = normalized.get("strong_advisory_escalation")
        if isinstance(escalation, dict):
            payload["strong_advisory_escalation"] = escalation
        repair_contract = self._build_repair_contract_payload_from_parts(
            gate_semantics=payload,
            fix_pack=_fix_pack,
            source=normalized,
        )
        if repair_contract:
            payload["repair_contract"] = repair_contract
        scope_authority = self._build_scope_authority_payload_from_parts(
            gate_semantics=payload,
            source=normalized,
        )
        if scope_authority:
            payload["scope_authority"] = scope_authority
        return payload

    @classmethod
    def _build_repair_contract_payload_from_parts(
        cls,
        *,
        gate_semantics: dict | None,
        fix_pack: dict | None,
        source: dict | None = None,
    ) -> dict[str, object]:
        gate_semantics = gate_semantics if isinstance(gate_semantics, dict) else {}
        fix_pack = cls._normalize_fix_pack(fix_pack)
        source = source if isinstance(source, dict) else {}
        source_repair_contract = (
            source.get("repair_contract") if isinstance(source.get("repair_contract"), dict) else {}
        )

        subtype_candidates: list[str] = []

        def _push(raw: object) -> None:
            token = cls._normalize_repair_subtype_value(raw)
            if token and token not in subtype_candidates:
                subtype_candidates.append(token)

        def _push_many(raw: object) -> None:
            for token in cls._normalize_repair_subtype_list(raw):
                if token not in subtype_candidates:
                    subtype_candidates.append(token)

        _push(source_repair_contract.get("subtype", ""))
        _push_many(source_repair_contract.get("subtypes"))
        _push(fix_pack.get("subtype", ""))
        _push_many(fix_pack.get("subtypes"))
        for key in ("subtype", "contradiction_subtype", "drift_subtype"):
            _push(source.get(key, ""))
            _push(source_repair_contract.get(key, ""))
        for key in ("subtypes", "contradiction_types"):
            _push_many(source.get(key))
            _push_many(source_repair_contract.get(key))
        for item in source_repair_contract.get("contradiction_details") or []:
            if not isinstance(item, dict):
                continue
            for key in ("subtype", "contradiction_subtype", "drift_subtype"):
                _push(item.get(key, ""))
            _push_many(item.get("contradiction_types"))
        for item in source.get("contradiction_details") or []:
            if not isinstance(item, dict):
                continue
            for key in ("subtype", "contradiction_subtype", "drift_subtype"):
                _push(item.get(key, ""))
            _push_many(item.get("contradiction_types"))

        payload: dict[str, object] = {}
        if subtype_candidates:
            payload["subtype"] = subtype_candidates[0]
            if len(subtype_candidates) > 1:
                payload["subtypes"] = subtype_candidates[:4]

        fix_scope = str(
            source.get("fix_scope", "")
            or source_repair_contract.get("fix_scope", "")
            or gate_semantics.get("repair_scope", "")
            or ""
        ).strip()
        if fix_scope:
            payload["fix_scope"] = fix_scope
        repair_scope = str(
            gate_semantics.get("repair_scope", "")
            or source.get("repair_scope", "")
            or source_repair_contract.get("repair_scope", "")
            or ""
        ).strip()
        if repair_scope:
            payload["repair_scope"] = repair_scope
        authoritative_fix_scope = str(
            gate_semantics.get(
                "authoritative_fix_scope",
                source.get("authoritative_fix_scope", source_repair_contract.get("authoritative_fix_scope", "")),
            )
            or ""
        ).strip()
        if authoritative_fix_scope:
            payload["authoritative_fix_scope"] = authoritative_fix_scope
        scope_origin = gate_semantics.get("scope_origin")
        if not isinstance(scope_origin, dict) or not scope_origin:
            scope_origin = source_repair_contract.get("scope_origin")
        if isinstance(scope_origin, dict) and scope_origin:
            payload["scope_origin"] = dict(scope_origin)

        provenance = str(source_repair_contract.get("provenance", "") or fix_pack.get("provenance", "") or "").strip()
        if provenance:
            payload["provenance"] = provenance
        provenance_sources = cls._normalize_fix_pack_provenance_sources(
            source_repair_contract.get("provenance_sources") or fix_pack.get("provenance_sources") or []
        )
        if provenance_sources:
            payload["provenance_sources"] = provenance_sources[:4]
        target_kind = str(source_repair_contract.get("target_kind", "") or fix_pack.get("target_kind", "") or "").strip()
        if target_kind:
            payload["target_kind"] = target_kind

        return payload

    @classmethod
    def _build_scope_authority_payload_from_parts(
        cls,
        *,
        gate_semantics: dict | None,
        source: dict | None = None,
    ) -> dict[str, object]:
        gate_semantics = gate_semantics if isinstance(gate_semantics, dict) else {}
        source = source if isinstance(source, dict) else {}
        repair_contract = source.get("repair_contract") if isinstance(source.get("repair_contract"), dict) else {}
        source_scope_authority = (
            source.get("scope_authority") if isinstance(source.get("scope_authority"), dict) else {}
        )

        fix_scope = str(
            source_scope_authority.get("fix_scope", "")
            or source.get("fix_scope", "")
            or repair_contract.get("fix_scope", "")
            or gate_semantics.get("repair_scope", "")
            or ""
        ).strip()
        repair_scope = str(
            gate_semantics.get("repair_scope", "")
            or source_scope_authority.get("repair_scope", "")
            or source.get("repair_scope", "")
            or repair_contract.get("repair_scope", "")
            or ""
        ).strip()
        authoritative_fix_scope = str(
            gate_semantics.get("authoritative_fix_scope", "")
            or source_scope_authority.get("authoritative_fix_scope", "")
            or source.get("authoritative_fix_scope", "")
            or repair_contract.get("authoritative_fix_scope", "")
            or ""
        ).strip()
        scope_origin = (
            gate_semantics.get("scope_origin")
            if isinstance(gate_semantics.get("scope_origin"), dict)
            else source_scope_authority.get("scope_origin")
            if isinstance(source_scope_authority.get("scope_origin"), dict)
            else source.get("scope_origin")
            if isinstance(source.get("scope_origin"), dict)
            else repair_contract.get("scope_origin")
            if isinstance(repair_contract.get("scope_origin"), dict)
            else {}
        )
        violation = (
            gate_semantics.get("authoritative_fix_scope_violation")
            if isinstance(gate_semantics.get("authoritative_fix_scope_violation"), dict)
            else source.get("authoritative_fix_scope_violation")
            if isinstance(source.get("authoritative_fix_scope_violation"), dict)
            else {}
        )

        payload: dict[str, object] = {}
        if fix_scope:
            payload["fix_scope"] = fix_scope
        if repair_scope:
            payload["repair_scope"] = repair_scope
        if authoritative_fix_scope:
            payload["authoritative_fix_scope"] = authoritative_fix_scope
        if scope_origin:
            payload["scope_origin"] = dict(scope_origin)
        if violation:
            payload["authoritative_fix_scope_violation"] = dict(violation)

        widened = False
        if isinstance(scope_origin, dict) and scope_origin:
            widened = str(scope_origin.get("fix_scope", "") or "").strip() in {
                "runtime_widened",
                "post_select_conflict_override",
            }
        elif isinstance(source_scope_authority.get("widened"), bool):
            widened = bool(source_scope_authority.get("widened"))
        elif fix_scope and authoritative_fix_scope:
            widened = fix_scope.lower() != authoritative_fix_scope.lower()
        if payload:
            payload["widened"] = bool(widened)
        return payload

    @staticmethod
    def _build_verdict_layers_payload(normalized: dict | None) -> dict[str, object]:
        if not isinstance(normalized, dict) or not normalized:
            return {}

        director_verdict = str(normalized.get("director_verdict", "") or "").strip().upper()
        final_verdict = str(normalized.get("final_verdict", "") or "").strip().upper()
        director_quality_passed = director_verdict in {"PASS", "PASS_WITH_FIX"}
        downstream_override_applied = bool(director_verdict and final_verdict and director_verdict != final_verdict)
        primary_failure_layer = "none"
        if final_verdict == "REJECT":
            primary_failure_layer = "downstream_gate" if director_quality_passed else "director_quality"

        return {
            "director_quality_passed": director_quality_passed,
            "downstream_override_applied": downstream_override_applied,
            "primary_failure_layer": primary_failure_layer,
        }

    def _setup_writing_directive(
        self,
        chief_writer,
        blueprint: dict,
        genre_name: str,
        next_ep: int,
    ) -> tuple:
        """[God-1] PatternTracker + WritingDirective 초기화.

        Returns:
            (WritingDirective, dict): (_writing_directive, _wd_expression_freq)
        """
        from modules.core.pattern_tracker import PatternTracker
        from modules.core.stage4_types import WritingDirective
        from modules.core.writing_directive_generator import WritingDirectiveGenerator
        from modules.validation.threshold_helper import _threshold

        _writing_directive: WritingDirective = WritingDirective()
        _wd_expression_freq: dict[str, int] = {}
        try:
            _pt_enabled = bool(_threshold("pattern_tracker.enable", True))
            if _pt_enabled:
                _lookback = int(_threshold("pattern_tracker.lookback_episodes", 5))
                _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
                _pt = PatternTracker()
                _pt_report = _pt.build_report(db=_db, ep_num=next_ep, lookback=_lookback)
                if _pt_report:
                    _wd_expression_freq = dict(getattr(_pt_report, "expression_freq", {}) or {})
                    _wdg = WritingDirectiveGenerator()
                    _writing_directive = _wdg.generate(
                        pattern_report=_pt_report,
                        blueprint=blueprint if isinstance(blueprint, dict) else {},
                        genre=genre_name,
                        ep_num=next_ep,
                        llm_callback=self._truth_gate_llm_ask,
                        lookback=_lookback,
                    )
                    if not _writing_directive.is_empty():
                        logging.info(
                            "[TF-54] WritingDirective 생성 완료: ending=%s, ban=%d개",
                            _writing_directive.ending_style[:30],
                            len(_writing_directive.expression_ban),
                        )
        except Exception as _wd_e:
            logging.warning("[TF-54] WritingDirective 생성 실패 (비치명): %s", str(_wd_e)[:100])
            _writing_directive = WritingDirective()
            _wd_expression_freq = {}

        try:
            setattr(chief_writer, "_current_blueprint", blueprint if isinstance(blueprint, dict) else {})
            setattr(chief_writer, "_tf54_writing_directive", _writing_directive)
            setattr(chief_writer, "_tf54_expression_freq", _wd_expression_freq)
        except Exception as _tf54_ctx_e:
            logging.debug("[TF-54] ChiefWriter 공유 상태 주입 실패 (비치명): %s", str(_tf54_ctx_e)[:80])

        return _writing_directive, _wd_expression_freq

    def _build_common_writer_kwargs(
        self,
        round_ctx,
        next_ep: int,
        mandatory_context: str,
        writer_blueprint: dict | None = None,
    ) -> tuple:
        """[God-1] mandatory_context 정규화 + common_writer_kwargs dict 조립.

        Returns:
            (str, dict): (mandatory_context_str, common_writer_kwargs)
        """
        blueprint = (
            writer_blueprint
            if isinstance(writer_blueprint, dict)
            else self._normalize_writer_blueprint(round_ctx.blueprint)
        )
        prev_text = round_ctx.prev_text
        _prev_manuscripts_text = round_ctx.prev_manuscripts_text
        hud_report = round_ctx.hud_report
        current_inventory = round_ctx.current_inventory
        current_martial_arts = round_ctx.current_martial_arts
        dead_npcs = round_ctx.dead_npcs
        item_acquisition_timeline = round_ctx.item_acquisition_timeline
        _chain_link_section = round_ctx.chain_link_section
        _world_state_summary = round_ctx.world_state_summary
        purism_prompt = round_ctx.purism_prompt
        genre_name = round_ctx.genre_name
        npc_equipment_summary = round_ctx.npc_equipment_summary
        _effective_anti_trope = round_ctx.effective_anti_trope
        intro_dna = round_ctx.intro_dna
        style_guide = round_ctx.style_guide
        reference_excerpt = round_ctx.reference_excerpt
        reference_anchor_prompt = round_ctx.reference_anchor_prompt
        justification_prompt = round_ctx.justification_prompt
        reflexion_prompt = round_ctx.reflexion_prompt
        _preflight_advisory = round_ctx.preflight_advisory

        if type(mandatory_context) is not str:
            mandatory_context = str(mandatory_context or "")

        reflexion_prompt = self._merge_writer_preflight_guidance(
            reflexion_prompt=reflexion_prompt,
            preflight_advisory=_preflight_advisory,
        )

        emotional_beat_section = ""
        _arc_data_full = getattr(round_ctx, "arc_data", {}) or {}
        _eb = _arc_data_full.get("emotional_beat") or {}
        if isinstance(_eb, dict) and _eb:
            _eb_type = _eb.get("type", "")
            _eb_intensity = _eb.get("intensity", "")
            if _eb_type or _eb_intensity:
                emotional_beat_section = (
                    f"### 이 화의 감정 정점\n"
                    f"유형: {_eb_type}  강도: {_eb_intensity}/10\n"
                    f"(집필 시 이 감정 정점을 향해 씬을 구성하라)"
                )

        _ws = getattr(self.ctx, "world_state", None)
        _motivations = _ws._state.get("motivations", []) if _ws and hasattr(_ws, "_state") else []
        _promises = _ws._state.get("promises", []) if _ws and hasattr(_ws, "_state") else []

        _upcoming_arc_items: list[str] = []
        if _arc_data_full:
            _sc = _arc_data_full.get("state_constraints", {})
            if isinstance(_sc, dict):
                _planned = _sc.get("protagonist_items") or _sc.get("items_acquired") or []
                if isinstance(_planned, list):
                    _owned_set = set(current_inventory or [])
                    _upcoming_arc_items = [str(i) for i in _planned if i and str(i) not in _owned_set]

        _common_writer_kwargs = {
            "ep_num": next_ep,
            "blueprint": blueprint,
            "arc_data": _arc_data_full if isinstance(_arc_data_full, dict) else {},
            "prev_manuscript": prev_text,
            "hud_report": hud_report,
            "arc_doc": round_ctx.arc_tactical,
            "master_bible": self.ctx.current_project.master_bible,
            "style_guide": style_guide,
            "reference_excerpt": reference_excerpt,
            "current_inventory": current_inventory,
            "current_martial_arts": current_martial_arts,
            "dead_npcs": dead_npcs,
            "item_acquisition_timeline": item_acquisition_timeline,
            "reference_anchor_prompt": reference_anchor_prompt,
            "mandatory_context": mandatory_context,
            "anti_trope_prompt": _effective_anti_trope,
            "justification_prompt": justification_prompt,
            "reflexion_prompt": reflexion_prompt,
            "genre_name": genre_name,
            "npc_equipment_summary": npc_equipment_summary,
            "intro_dna": intro_dna,
            "purism_prompt": purism_prompt,
            "state_tracker": self.ctx.state_tracker,
            "prev_manuscripts_text": _prev_manuscripts_text,
            "world_state_summary": _world_state_summary,
            "chain_link_section": _chain_link_section,
            "emotional_beat_section": emotional_beat_section,
            "motivations": _motivations,  # [B-4]
            "promises": _promises,  # [B-4]
            "upcoming_arc_items": _upcoming_arc_items,  # [TF-49b]
            # episode_digest는 Director 전용 — L713에서 별도 전달
        }
        return mandatory_context, _common_writer_kwargs

    @staticmethod
    def _merge_writer_preflight_guidance(*, reflexion_prompt: str, preflight_advisory: str) -> str:
        base_prompt = reflexion_prompt if type(reflexion_prompt) is str else str(reflexion_prompt or "")
        advisory = preflight_advisory if type(preflight_advisory) is str else str(preflight_advisory or "")
        advisory = advisory.strip()
        if not advisory:
            return base_prompt
        advisory_block = (
            "### [Preflight Advisory - advisory only]\n"
            "아래 사전 점검 경고는 writer guidance다. mandatory truth나 established canon보다 우선하지 않는다.\n"
            f"{advisory}"
        )
        if not base_prompt:
            return advisory_block
        return f"{advisory_block}\n\n{base_prompt}"

    def _build_empty_candidates_result(
        self,
        *,
        next_ep: int,
        round_num: int,
        arc_num: int,
        model_tier,
        director_feedback: str,
        previous_attempt: dict,
        is_patch: bool,
        prev_score: int,
        tot_used: bool,
        mad_used: bool,
    ):
        from modules.core.stage4_types import _InterviewRoundResult

        logging.error(f"[Stage4] 제{next_ep}화 {round_num + 1}차 면담: candidates 빈 배열 — 모든 후보 생성 실패")
        self.ctx.ui.log(
            f"   🚨 [V66.3] 모든 후보 생성 실패 — {'최종 실패 처리' if round_num >= 4 else '다음 면담으로 진행'}"
        )
        director_feedback += "\n[시스템] 모든 후보 생성 실패. 재시도 필요."
        previous_attempt = {
            "strategy": "none",
            "rejection_reason": "모든 후보 생성 실패",
            "action_items": [],
            "score": 0,
            "_tot_used": tot_used,
            "_mad_used": mad_used,
            "prior_attempts": self._inherit_attempt_history(previous_attempt),
        }
        self._record_s4_attempt(
            episode=next_ep,
            round_num=round_num,
            success=False,
            score=0,
            is_patch=is_patch,
            prev_score=prev_score,
            patch_fallback=False,
            arc=arc_num,
            verdict="EMPTY",
            reject_reason="empty_candidates",
            model=model_tier,
        )
        if getattr(self.ctx, "quality_dashboard", None):
            try:
                self.ctx.quality_dashboard.record_validation(
                    ep_num=next_ep,
                    result={
                        "decision": "REJECT",
                        "score": 0,
                        "violations": [{"type": "empty_candidates"}],
                        "warnings": [],
                    },
                    stage=4,
                )
            except Exception as _qd_err:
                logging.debug(f"[SILENT] quality_dashboard EMPTY: {_qd_err}")
        return _InterviewRoundResult(
            verdict="EMPTY",
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
        )

    def _run_generation_phase(
        self,
        *,
        round_num: int,
        director_feedback: str,
        previous_attempt: dict,
        round_ctx,
        blueprint,
        style_guide: str,
        next_ep: int,
        common_writer_kwargs: dict,
    ) -> _GenerationPhaseResult:
        try:
            self.ctx.perf_timer.start(f"s4_ep{next_ep}_generate_r{round_num}")
        except Exception as e:
            logging.debug(f"[PerfTimer] start generate: {e}")

        is_patch = False
        is_patch_fallback = False
        prev_score = 0
        prev_manuscript = previous_attempt.get("best_manuscript", "") if previous_attempt else ""
        tot_used = bool(previous_attempt.get("_tot_used", False)) if previous_attempt else False
        mad_used = bool(previous_attempt.get("_mad_used", False)) if previous_attempt else False

        weighted_injection = ""
        prompt_weighter = self.ctx.get_module("prompt_weighter")
        if prompt_weighter:
            try:
                weighted_injection = prompt_weighter.get_weighted_prompt("writer", 4, top_n=3)
            except Exception as e:
                logging.warning(f"[SilentPass:PromptWeighter] {e!s:.100}")
        if weighted_injection:
            director_feedback = (
                weighted_injection + "\n\n" + director_feedback if director_feedback else weighted_injection
            )

        writer_kwargs = dict(common_writer_kwargs)
        if director_feedback and director_feedback.strip():
            writer_kwargs["director_feedback"] = director_feedback

        candidates, is_patch, is_patch_fallback, prev_score, asp_manuscript = self._generate_candidates(
            round_num=round_num,
            chief_writer=round_ctx.chief_writer,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            prev_manuscript=prev_manuscript,
            style_guide=style_guide,
            blueprint=blueprint,
            common_writer_kwargs=writer_kwargs,
            arc_num=round_ctx.arc_data.get("arc_no", 0),
        )

        try:
            self.ctx.perf_timer.stop(f"s4_ep{next_ep}_generate_r{round_num}")
        except Exception as e:
            logging.debug(f"[PerfTimer] stop generate: {e}")

        # [TF-1] None/non-list guard + 후보별 탈락 사유 관측
        if not candidates:
            logging.warning("[Stage4] R%d 후보 생성 결과 None/empty — candidates=[]", round_num)
            candidates = []
        _pre_filter_count = len(candidates)
        candidates = [c for c in candidates if isinstance(c, dict) and c.get("manuscript", "").strip()]
        if _pre_filter_count > 0 and not candidates:
            logging.warning(
                "[Stage4] R%d 후보 %d건 전량 필터링 탈락 (manuscript 누락/빈 문자열)",
                round_num,
                _pre_filter_count,
            )
        if not candidates:
            empty_result = self._build_empty_candidates_result(
                next_ep=next_ep,
                round_num=round_num,
                arc_num=round_ctx.arc_data.get("arc_no", 0),
                model_tier=getattr(round_ctx.chief_writer, "model_tier", None),
                director_feedback=director_feedback,
                previous_attempt=previous_attempt,
                is_patch=is_patch,
                prev_score=prev_score,
                tot_used=tot_used,
                mad_used=mad_used,
            )
            return _GenerationPhaseResult(
                candidates=[],
                director_feedback=director_feedback,
                is_patch=is_patch,
                is_patch_fallback=is_patch_fallback,
                prev_score=prev_score,
                prev_manuscript=prev_manuscript,
                tot_used=tot_used,
                mad_used=mad_used,
                asp_manuscript=asp_manuscript,
                empty_result=empty_result,
            )

        return _GenerationPhaseResult(
            candidates=candidates,
            director_feedback=director_feedback,
            is_patch=is_patch,
            is_patch_fallback=is_patch_fallback,
            prev_score=prev_score,
            prev_manuscript=prev_manuscript,
            tot_used=tot_used,
            mad_used=mad_used,
            asp_manuscript=asp_manuscript,
        )

    def _run_validation_phase(
        self,
        *,
        stage4_spinner,
        round_num: int,
        round_ctx,
        prev_manuscript: str,
        candidates: list[dict],
    ) -> tuple[list[dict], str]:
        validation_results, director_memory_context = self.director_runtime.run_pre_director_validation(
            candidates=candidates,
            next_ep=round_ctx.next_ep,
            blueprint=round_ctx.blueprint,
            prev_text=round_ctx.prev_text,
            hud_report=round_ctx.hud_report,
            genre_name=round_ctx.genre_name,
            manuscript_validator=round_ctx.manuscript_validator,
            consistency_validator=round_ctx.consistency_validator,
            blocking_validator=round_ctx.blocking_validator,
            continuity_validator=round_ctx.continuity_validator,
            stage4_spinner=stage4_spinner,
            round_num=round_num,
            arc_pos=round_ctx.arc_pos,
            total_ep_in_arc=round_ctx.total_ep_in_arc,
            arc_data=round_ctx.arc_data if isinstance(round_ctx.arc_data, dict) else {},
            prev_manuscript=prev_manuscript,
        )
        return validation_results, director_memory_context

    def _persist_director_selection(
        self,
        *,
        round_ctx,
        next_ep: int,
        round_num: int,
        candidates: list[dict],
        validation_results: list[dict],
        director_result: dict,
        advisory_summary: dict[str, int],
        selected: str,
        verdict: str,
        score: int,
        selection_reason: str,
        verdict_reason: str,
        attempt_key: str,
        is_patch: bool,
        is_patch_fallback: bool,
        prev_score: int,
    ) -> dict[str, str]:
        selection_artifact_meta = normalize_artifact_meta(None)
        raw_advisory_payload = None
        selection_advisory: dict[str, object] | None = None
        selection_kwargs: dict[str, object] | None = None
        try:
            selection_advisory = self._build_stage4_selection_advisory_payload(
                advisory_summary=advisory_summary,
                director_result=director_result,
                is_patch=is_patch,
                is_patch_fallback=is_patch_fallback,
                prev_score=prev_score,
            )
            raw_advisory_payload = self._build_raw_advisory_payload(
                validation_results,
                selection_summary=selection_advisory,
            )
            selected_candidate = director_result.get("selected_candidate", {})
            if not isinstance(selected_candidate, dict):
                selected_candidate = {}
            selected_strategy = selected_candidate.get("strategy_name", "") or selected_candidate.get("strategy", "")
            candidate_key = build_candidate_key(label=selected, strategy=selected_strategy, fallback="stage4")
            selection_artifact_kind = "selected_candidate"
            if verdict == "PASS_WITH_FIX":
                selection_artifact_kind = "selected_before_fix"
            elif verdict == "REJECT":
                selection_artifact_kind = "rejected_best"
            selection_artifact_meta = normalize_artifact_meta(
                snapshot_logged_artifact(
                    getattr(self.ctx, "current_project", None),
                    stage=4,
                    ep_num=next_ep,
                    arc_num=round_ctx.arc_data.get("arc_no", 0),
                    attempt_num=round_num + 1,
                    candidate_key=candidate_key,
                    artifact_kind=selection_artifact_kind,
                    payload=selected_candidate.get("manuscript", ""),
                )
            )
            selection_kwargs = self._build_stage4_director_selection_kwargs(
                ep_num=next_ep,
                round_num=round_num,
                selected_label=selected,
                selected_strategy=selected_strategy,
                verdict=verdict,
                score=score,
                selection_reason=selection_reason,
                candidate_count=len(candidates) if candidates else 0,
                director_result=director_result,
                advisory_warnings=selection_advisory or None,
                verdict_reason=verdict_reason,
                attempt_key=attempt_key,
                selection_artifact_meta=selection_artifact_meta,
            )
            self.ctx.current_project.db.save_director_selection(**selection_kwargs)
        except Exception as exc:
            logging.warning(f"[D-4] Director 선택 기록 실패 (비차단): {exc!s:.100}")
        # adjunct raw rationale: director thinking + advisory warnings
        try:
            _db_adj = getattr(self.ctx.current_project, "db", None)
            if attempt_key:
                persist_stage4_raw_rationale_records(
                    project_db=_db_adj,
                    records=_build_stage4_raw_rationale_records(
                        attempt_key=attempt_key,
                        ep_num=next_ep,
                        director_result=director_result,
                        raw_advisory_payload=raw_advisory_payload,
                        selection_advisory=selection_advisory,
                        selection_surface=selection_kwargs,
                    ),
                    log_prefix="Stage4Selection",
                )
        except Exception:
            pass
        return selection_artifact_meta

    def _build_stage4_director_selection_kwargs(
        self,
        *,
        ep_num: int,
        round_num: int,
        selected_label: str,
        selected_strategy: str,
        verdict: str,
        score: int,
        selection_reason: str,
        candidate_count: int,
        director_result: dict | None,
        advisory_warnings: dict | None,
        verdict_reason: str,
        attempt_key: str,
        selection_artifact_meta: dict[str, str],
    ) -> dict[str, object]:
        director_payload = director_result if isinstance(director_result, dict) else {}
        surface_kwargs = self._build_stage4_selection_rationale_update_kwargs(
            attempt_key=attempt_key,
            trace_director_result=None,
            director_result=director_payload,
            selection_reason=selection_reason,
            verdict_reason=verdict_reason,
            advisory_warnings=advisory_warnings,
            prefer_authoritative_scope=False,
        )
        return {
            "ep_num": ep_num,
            "round_num": round_num,
            "selected_label": selected_label,
            "selected_strategy": selected_strategy,
            "verdict": verdict,
            "stage": 4,
            "score": score,
            "selection_reason": surface_kwargs["selection_reason"],
            "candidate_count": candidate_count,
            "fix_scope": surface_kwargs["fix_scope"],
            "advisory_warnings": surface_kwargs["advisory_warnings"],
            "verdict_reason": surface_kwargs["verdict_reason"],
            "pre_firewall_score": director_payload.get("pre_firewall_score", score),
            "firewall_triggered": bool(director_payload.get("firewall_triggered")),
            "firewall_reason": director_payload.get("firewall_reason", ""),
            "attempt_key": attempt_key,
            "candidate_key": selection_artifact_meta["candidate_key"],
            "content_hash": selection_artifact_meta["content_hash"],
            "artifact_path": selection_artifact_meta["artifact_path"],
            "director_thinking": director_payload.get("_director_thinking", ""),
        }

    @staticmethod
    def _extract_blueprint_npc_roster(blueprint: dict) -> list[str]:
        npc_roster: list[str] = []
        if not isinstance(blueprint, dict):
            return npc_roster
        raw_chars = blueprint.get("characters") or blueprint.get("npcs") or []
        if isinstance(raw_chars, list):
            for char in raw_chars:
                name = char.get("name", "") if isinstance(char, dict) else str(char or "")
                name = name.strip()
                if name and name not in npc_roster:
                    npc_roster.append(name)
        elif isinstance(raw_chars, str):
            for char in raw_chars.replace("|", ",").split(","):
                name = char.strip()
                if name and name not in npc_roster:
                    npc_roster.append(name)
        return npc_roster

    # ═══════════════════════════════════════════════════════════════════════
    # run() — MAIN ENTRY POINT
    # ═══════════════════════════════════════════════════════════════════════

    def run(
        self,
        *,
        round_num: int,
        stage4_spinner,
        director_feedback: str,
        previous_attempt: dict,
        round_ctx,
    ):
        """[4-R1-e-1] Single interview round: generation, validation, judgment."""
        _setup = self._prepare_round_execution(
            round_num=round_num,
            stage4_spinner=stage4_spinner,
            director_feedback=director_feedback,
            round_ctx=round_ctx,
        )
        chief_writer = _setup.chief_writer
        next_ep = _setup.next_ep
        blueprint = _setup.blueprint
        style_guide = _setup.style_guide
        mandatory_context = _setup.mandatory_context
        _writing_directive = _setup.writing_directive
        _common_writer_kwargs = _setup.common_writer_kwargs
        director_feedback = _setup.director_feedback

        # Phase 2: Chief Writer 앙상블 생성
        _generation = self._run_generation_phase(
            round_num=round_num,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            round_ctx=round_ctx,
            blueprint=blueprint,
            style_guide=style_guide,
            next_ep=next_ep,
            common_writer_kwargs=_common_writer_kwargs,
        )
        director_feedback = _generation.director_feedback
        _is_patch = _generation.is_patch
        _is_patch_fallback = _generation.is_patch_fallback
        _prev_score = _generation.prev_score
        _prev_manuscript = _generation.prev_manuscript
        _tot_used = _generation.tot_used
        _mad_used = _generation.mad_used
        _asp_manuscript = _generation.asp_manuscript
        candidates = _generation.candidates
        if _generation.empty_result is not None:
            return _generation.empty_result

        # Phase 3: Python 사전 검증
        validation_results, _director_memory_context = self._run_validation_phase(
            stage4_spinner=stage4_spinner,
            round_num=round_num,
            round_ctx=round_ctx,
            prev_manuscript=_prev_manuscript,
            candidates=candidates,
        )

        # Phase 4: Director 면담
        _review = self.director_runtime.run_director_review_phase(
            stage4_spinner=stage4_spinner,
            round_num=round_num,
            round_ctx=round_ctx,
            candidates=candidates,
            validation_results=validation_results,
            mandatory_context=mandatory_context,
            writing_directive=_writing_directive,
            director_feedback=director_feedback,
            is_patch=_is_patch,
            is_patch_fallback=_is_patch_fallback,
            prev_score=_prev_score,
        )
        return self._complete_round_after_review(
            next_ep=next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            review=_review,
            generation=_generation,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            candidates=candidates,
            validation_results=validation_results,
            director_memory_context=_director_memory_context,
            stage4_spinner=stage4_spinner,
        )

    def _prepare_round_execution(
        self,
        *,
        round_num: int,
        stage4_spinner,
        director_feedback: str,
        round_ctx,
    ) -> _RoundExecutionSetupResult:
        self._round_start_ts = time.monotonic()
        self._last_advisory_summary = {}
        self._last_advisory_details = []
        self._last_advisory_metadata = {}
        self._last_strategy_budget = "full"
        self._last_strategy_count = 0
        self._capture_round_metrics_baseline()

        chief_writer = round_ctx.chief_writer
        next_ep = round_ctx.next_ep
        blueprint = round_ctx.blueprint
        writer_blueprint = self._normalize_writer_blueprint(blueprint)
        arc_pos = round_ctx.arc_pos
        genre_name = round_ctx.genre_name
        style_guide = round_ctx.style_guide
        mandatory_context = round_ctx.mandatory_context

        writing_directive, _ = self._setup_writing_directive(
            chief_writer=chief_writer,
            blueprint=writer_blueprint,
            genre_name=genre_name,
            next_ep=next_ep,
        )

        if type(director_feedback) is not str:
            director_feedback = str(director_feedback or "")

        mandatory_context = self._prepend_arc_first_location_note(
            arc_pos=arc_pos,
            mandatory_context=mandatory_context,
        )

        mandatory_context, common_writer_kwargs = self._build_common_writer_kwargs(
            round_ctx=round_ctx,
            next_ep=next_ep,
            mandatory_context=mandatory_context,
            writer_blueprint=writer_blueprint,
        )

        self._log_round_generation_start(
            next_ep=next_ep,
            round_num=round_num,
            arc_num=round_ctx.arc_data.get("arc_no", 0),
            stage4_spinner=stage4_spinner,
        )
        return _RoundExecutionSetupResult(
            chief_writer=chief_writer,
            next_ep=next_ep,
            blueprint=blueprint,
            style_guide=style_guide,
            mandatory_context=mandatory_context,
            writing_directive=writing_directive,
            common_writer_kwargs=common_writer_kwargs,
            director_feedback=director_feedback,
        )

    @staticmethod
    def _prepend_arc_first_location_note(*, arc_pos: int, mandatory_context: str) -> str:
        if arc_pos != 1:
            return mandatory_context
        arc_loc_note = (
            "[Arc 첫 화 특별 지시] 이번 화는 새 Arc의 첫 화입니다. "
            "mandatory_context의 위치 정보를 확인하여, 이전 Arc 종료 위치와 "
            "현재 화 시작 위치가 다르다면 반드시 이동 과정(교통수단·경로·시간 소요) "
            "또는 시간 경과 표지('다음날', 'N일 후' 등)를 도입부에 포함하세요. "
            "설명 없는 장소 단절은 독자 이탈의 원인입니다."
        )
        return f"{arc_loc_note}\n\n{mandatory_context}" if mandatory_context else arc_loc_note

    def _log_round_generation_start(
        self,
        *,
        next_ep: int,
        round_num: int,
        arc_num: int,
        stage4_spinner,
    ) -> None:
        stage4_spinner.update_detail(f"제{next_ep}화 · {round_num + 1}차 면담 · 앙상블 생성")
        self.ctx.ui.log(f"\n🎬 [{round_num + 1}차 면담] Chief Writer 앙상블 생성 중...")
        self.ctx.ui.log(
            f"   🎬 [{round_num + 1}차 면담] 원고 앙상블 생성 중...",
            stage="stage4",
            component="chief_writer_ensemble",
            ep_num=next_ep,
            arc_num=arc_num,
            round_num=round_num,
            event_kind="progress",
        )
        self._log_attempt_event(
            logging.INFO,
            next_ep=next_ep,
            round_num=round_num,
            arc_num=arc_num,
            message="chief_writer_ensemble_start",
        )

    def _complete_round_after_review(
        self,
        *,
        next_ep: int,
        round_num: int,
        round_ctx,
        chief_writer,
        review,
        generation,
        director_feedback: str,
        previous_attempt: dict,
        candidates: list[dict],
        validation_results: list[dict],
        director_memory_context: str,
        stage4_spinner,
    ):
        director_result = review.director_result
        selected_candidate = director_result.get("selected_candidate", {}) if isinstance(director_result, dict) else {}
        selected_manuscript = ""
        if isinstance(selected_candidate, dict):
            selected_manuscript = str(selected_candidate.get("manuscript", "") or "")
        director_result = self._maybe_enrich_director_result(director_result, manuscript_text=selected_manuscript)
        director_feedback = self._merge_retry_advisory_feedback(director_feedback)

        # [B-1-3b] PASS/PASS_WITH_FIX 처리 → 위임
        pass_result, director_feedback, previous_attempt, trace_meta = self._process_verdict(
            director_result=director_result,
            director_feedback=director_feedback,
            verdict=review.verdict,
            score=review.score,
            round_ctx=round_ctx,
            round_num=round_num,
            previous_attempt=previous_attempt,
            is_patch=generation.is_patch,
            is_patch_fallback=generation.is_patch_fallback,
            prev_score=generation.prev_score,
            stage4_spinner=stage4_spinner,
            director_mandatory_context=review.director_mandatory_context,
            director_memory_context=director_memory_context,
            error_category=review.error_category,
        )
        return self._finalize_round_outcome(
            pass_result=pass_result,
            next_ep=next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result=director_result,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            trace_meta=trace_meta,
            candidates=candidates,
            validation_results=validation_results,
            initial_verdict=review.verdict,
            initial_score=review.score,
            selected=review.selected,
            reason=review.reason,
            error_category=review.error_category,
            attempt_key=review.attempt_key,
            selection_artifact_meta=review.selection_artifact_meta,
            is_patch=generation.is_patch,
            is_patch_fallback=generation.is_patch_fallback,
            prev_score=generation.prev_score,
            prev_manuscript=generation.prev_manuscript,
            tot_used=generation.tot_used,
            mad_used=generation.mad_used,
            asp_manuscript=generation.asp_manuscript,
        )

    def _build_round_outcome_trace_payload(
        self,
        *,
        trace_meta,
        director_result: dict,
        initial_verdict: str,
        initial_score: int,
        validation_results: list[dict],
        is_patch: bool,
    ) -> _RoundOutcomeTracePayload:
        trace_director_result = (
            trace_meta.get("director_result", director_result) if isinstance(trace_meta, dict) else director_result
        )
        final_verdict = (
            trace_meta.get("final_verdict", initial_verdict) if isinstance(trace_meta, dict) else initial_verdict
        )
        final_score = trace_meta.get("final_score", initial_score) if isinstance(trace_meta, dict) else initial_score
        trace_patch_trace = trace_meta.get("patch_trace", {}) if isinstance(trace_meta, dict) else {}
        trace_contract_source = dict(trace_director_result) if isinstance(trace_director_result, dict) else {}
        trace_patch_trace, trace_fix_pack = self._resolve_stage4_patch_contract_payloads(
            director_result=trace_contract_source,
            patch_trace=trace_patch_trace,
        )
        if isinstance(trace_director_result, dict) and trace_fix_pack:
            trace_director_result = dict(trace_director_result)
            existing_fix_pack = trace_director_result.get("fix_pack")
            if isinstance(existing_fix_pack, dict) and existing_fix_pack:
                merged_fix_pack = dict(trace_fix_pack)
                merged_fix_pack.update(existing_fix_pack)
                trace_director_result["fix_pack"] = merged_fix_pack
            else:
                trace_director_result["fix_pack"] = dict(trace_fix_pack)
        validation_warnings = self._collect_validation_warning_lines(validation_results, limit=20)
        return _RoundOutcomeTracePayload(
            trace_director_result=trace_director_result,
            final_verdict=final_verdict,
            final_score=final_score,
            trace_patch_trace=trace_patch_trace,
            is_patch=bool(is_patch or trace_patch_trace),
            validation_warnings=validation_warnings,
        )

    def _finalize_round_reject_path(
        self,
        *,
        next_ep: int,
        round_num: int,
        round_ctx,
        chief_writer,
        director_result: dict,
        director_feedback: str,
        previous_attempt: dict,
        trace_payload: _RoundOutcomeTracePayload,
        candidates: list[dict],
        validation_results: list[dict],
        initial_verdict: str,
        initial_score: int,
        selected: str,
        reason: str,
        error_category: str,
        attempt_key: str,
        selection_artifact_meta: dict,
        is_patch_fallback: bool,
        prev_score: int,
        prev_manuscript: str,
        tot_used: bool,
        mad_used: bool,
        asp_manuscript: str,
    ):
        reject_result = self._handle_reject(
            director_result=trace_payload.trace_director_result,
            director_feedback=director_feedback,
            candidates=candidates,
            validation_results=validation_results,
            round_ctx=round_ctx,
            round_num=round_num,
            previous_attempt=previous_attempt,
            is_patch=trace_payload.is_patch,
            is_patch_fallback=is_patch_fallback,
            prev_score=prev_score,
            prev_manuscript=prev_manuscript,
            asp_manuscript=asp_manuscript,
            tot_used=tot_used,
            mad_used=mad_used,
            selected=selected,
            score=trace_payload.final_score,
            error_category=error_category,
            patch_trace=trace_payload.trace_patch_trace,
        )
        return self._finalize_reject_result(
            reject_result=reject_result,
            next_ep=next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result=director_result,
            trace_director_result=trace_payload.trace_director_result,
            initial_verdict=initial_verdict,
            initial_score=initial_score,
            final_verdict=trace_payload.final_verdict or "REJECT",
            final_score=trace_payload.final_score,
            selected=selected,
            reason=reason,
            error_category=error_category,
            attempt_key=attempt_key,
            selection_artifact_meta=selection_artifact_meta,
            validation_warnings=trace_payload.validation_warnings,
            is_patch=trace_payload.is_patch,
            is_patch_fallback=is_patch_fallback,
            trace_patch_trace=trace_payload.trace_patch_trace,
            tot_used=tot_used,
            mad_used=mad_used,
            asp_manuscript=asp_manuscript,
        )

    def _finalize_round_outcome(
        self,
        *,
        pass_result,
        next_ep: int,
        round_num: int,
        round_ctx,
        chief_writer,
        director_result: dict,
        director_feedback: str,
        previous_attempt: dict,
        trace_meta,
        candidates: list[dict],
        validation_results: list[dict],
        initial_verdict: str,
        initial_score: int,
        selected: str,
        reason: str,
        error_category: str,
        attempt_key: str,
        selection_artifact_meta: dict,
        is_patch: bool,
        is_patch_fallback: bool,
        prev_score: int,
        prev_manuscript: str,
        tot_used: bool,
        mad_used: bool,
        asp_manuscript: str,
    ):
        # ── Parameter / envelope relationship ──
        # director_result  : raw dict from DirectorEnsemble.compare_and_select()
        # initial_verdict  : director_result["final_verdict"] BEFORE post-gates
        # pass_result      : None when REJECT; populated dict when PASS/PASS_WITH_FIX
        # trace_meta       : round-level audit trace (verdict, score, patch info)
        # This method merges the above into the episode-level outcome and
        # persists to DB / JSONL / artifact sinks via _build_round_outcome_trace_payload.
        trace_payload = self._build_round_outcome_trace_payload(
            trace_meta=trace_meta,
            director_result=director_result,
            initial_verdict=initial_verdict,
            initial_score=initial_score,
            validation_results=validation_results,
            is_patch=is_patch,
        )

        if pass_result is not None:
            return self._finalize_round_pass_path(
                pass_result=pass_result,
                next_ep=next_ep,
                round_num=round_num,
                round_ctx=round_ctx,
                chief_writer=chief_writer,
                director_result=director_result,
                director_feedback=director_feedback,
                trace_payload=trace_payload,
                initial_verdict=initial_verdict,
                initial_score=initial_score,
                selected=selected,
                reason=reason,
                error_category=error_category,
                attempt_key=attempt_key,
                selection_artifact_meta=selection_artifact_meta,
                is_patch_fallback=is_patch_fallback,
                tot_used=tot_used,
                mad_used=mad_used,
                asp_manuscript=asp_manuscript,
            )

        return self._finalize_round_reject_path(
            next_ep=next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result=director_result,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            trace_payload=trace_payload,
            candidates=candidates,
            validation_results=validation_results,
            initial_verdict=initial_verdict,
            initial_score=initial_score,
            selected=selected,
            reason=reason,
            error_category=error_category,
            attempt_key=attempt_key,
            selection_artifact_meta=selection_artifact_meta,
            is_patch_fallback=is_patch_fallback,
            prev_score=prev_score,
            prev_manuscript=prev_manuscript,
            tot_used=tot_used,
            mad_used=mad_used,
            asp_manuscript=asp_manuscript,
        )

    def _finalize_round_pass_path(
        self,
        *,
        pass_result,
        next_ep: int,
        round_num: int,
        round_ctx,
        chief_writer,
        director_result: dict,
        director_feedback: str,
        trace_payload: _RoundOutcomeTracePayload,
        initial_verdict: str,
        initial_score: int,
        selected: str,
        reason: str,
        error_category: str,
        attempt_key: str,
        selection_artifact_meta: dict,
        is_patch_fallback: bool,
        tot_used: bool,
        mad_used: bool,
        asp_manuscript: str,
    ):
        return self._finalize_pass_result(
            pass_result=pass_result,
            next_ep=next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result=director_result,
            trace_director_result=trace_payload.trace_director_result,
            director_feedback=director_feedback,
            initial_verdict=initial_verdict,
            initial_score=initial_score,
            final_verdict=trace_payload.final_verdict,
            final_score=trace_payload.final_score,
            selected=selected,
            reason=reason,
            error_category=error_category,
            attempt_key=attempt_key,
            selection_artifact_meta=selection_artifact_meta,
            validation_warnings=trace_payload.validation_warnings,
            is_patch=trace_payload.is_patch,
            is_patch_fallback=is_patch_fallback,
            trace_patch_trace=trace_payload.trace_patch_trace,
            tot_used=tot_used,
            mad_used=mad_used,
            asp_manuscript=asp_manuscript,
        )

    def _finalize_reject_result(
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
        return self.reject_runtime.finalize_reject_result(
            reject_result=reject_result,
            next_ep=next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result=director_result,
            trace_director_result=trace_director_result,
            initial_verdict=initial_verdict,
            initial_score=initial_score,
            final_verdict=final_verdict,
            final_score=final_score,
            selected=selected,
            reason=reason,
            error_category=error_category,
            attempt_key=attempt_key,
            selection_artifact_meta=selection_artifact_meta,
            validation_warnings=validation_warnings,
            is_patch=is_patch,
            is_patch_fallback=is_patch_fallback,
            trace_patch_trace=trace_patch_trace,
            tot_used=tot_used,
            mad_used=mad_used,
            asp_manuscript=asp_manuscript,
        )

    def _finalize_pass_result(
        self,
        *,
        pass_result,
        next_ep: int,
        round_num: int,
        round_ctx,
        chief_writer,
        director_result: dict,
        trace_director_result,
        director_feedback: str,
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
        logging_payload = self._build_pass_result_logging_payload(
            pass_result=pass_result,
            next_ep=next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            director_result=director_result,
            trace_director_result=trace_director_result,
            reason=reason,
            is_patch=is_patch,
            trace_patch_trace=trace_patch_trace,
        )
        self._sync_pass_result_selection_rationale(
            attempt_key=attempt_key,
            trace_director_result=trace_director_result,
            director_result=director_result,
            selection_reason=logging_payload.session_selection_reason,
            verdict_reason=logging_payload.session_verdict_reason,
            gate_semantics=logging_payload.session_gate_semantics,
            fix_pack=dict(logging_payload.session_fix_pack or {}),
            retry_budget_axes=dict(getattr(self, "_last_retry_budget_axes", {}) or {}),
            preserve_historical_companion=bool(is_patch or trace_patch_trace),
        )
        self._emit_pass_result_logs(
            next_ep=next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result=director_result,
            trace_director_result=trace_director_result,
            director_feedback=director_feedback,
            initial_verdict=initial_verdict,
            initial_score=initial_score,
            final_verdict=final_verdict,
            final_score=final_score,
            selected=selected,
            reason=reason,
            error_category=error_category,
            attempt_key=attempt_key,
            selection_artifact_meta=selection_artifact_meta,
            validation_warnings=validation_warnings,
            is_patch=is_patch,
            is_patch_fallback=is_patch_fallback,
            trace_patch_trace=trace_patch_trace,
            tot_used=tot_used,
            mad_used=mad_used,
            asp_manuscript=asp_manuscript,
            logging_payload=logging_payload,
        )
        return pass_result

    def _build_pass_result_logging_payload(
        self,
        *,
        pass_result,
        next_ep: int,
        round_num: int,
        round_ctx,
        director_result: dict,
        trace_director_result,
        reason: str,
        is_patch: bool,
        trace_patch_trace: dict,
    ) -> _PassResultLoggingPayload:
        attempt_artifact_meta = normalize_artifact_meta(getattr(pass_result, "attempt_artifact_meta", {}) or {})
        log_artifact_meta = normalize_artifact_meta(attempt_artifact_meta)
        if not log_artifact_meta["candidate_key"] and isinstance(trace_director_result, dict):
            selected_candidate = trace_director_result.get("selected_candidate") or {}
            if not isinstance(selected_candidate, dict):
                selected_candidate = {}
            fallback_candidate = build_candidate_key(
                label=str(trace_director_result.get("selected", "") or ""),
                strategy=str(selected_candidate.get("strategy_name", "") or selected_candidate.get("strategy", "")),
                fallback="stage4",
            )
            log_artifact_meta = normalize_artifact_meta(
                snapshot_logged_artifact(
                    getattr(self.ctx, "current_project", None),
                    stage=4,
                    ep_num=next_ep,
                    arc_num=round_ctx.arc_data.get("arc_no", 0),
                    attempt_num=round_num + 1,
                    candidate_key=fallback_candidate,
                    artifact_kind="patched_after_fix" if (is_patch or trace_patch_trace) else "final_manuscript",
                    payload=getattr(pass_result, "final_manuscript", ""),
                )
            )
        _logging_source = dict(director_result or {}) if isinstance(director_result, dict) else {}
        if isinstance(trace_director_result, dict):
            for _key, _value in trace_director_result.items():
                if _value not in (None, "", [], {}):
                    _logging_source[_key] = _value
        _, _session_fix_pack = self._resolve_stage4_patch_contract_payloads(
            director_result=_logging_source,
            patch_trace=trace_patch_trace,
        )
        if _session_fix_pack and not self._normalize_fix_pack(_logging_source.get("fix_pack")):
            _logging_source["fix_pack"] = dict(_session_fix_pack)
        decision_surface = _build_stage4_pass_decision_surface(
            director_result=director_result,
            trace_director_result=trace_director_result if isinstance(trace_director_result, dict) else None,
            fallback_reason=reason,
        )
        _gate = self._build_gate_semantics_payload(_logging_source)
        # [SSS-T2] PASS-side carryover linkage — conflict resolution and reuse contract
        _gate.update(_build_stage4_pass_carryover_linkage(getattr(pass_result, "previous_attempt", None)))
        return _PassResultLoggingPayload(
            log_artifact_meta=log_artifact_meta,
            session_selection_reason=decision_surface.selection_reason,
            session_verdict_reason=decision_surface.verdict_reason,
            session_runtime_advisory=self._build_retry_advisory_digest(),
            session_retry_directives="",
            session_gate_semantics=_gate,
            session_fix_pack=dict(_session_fix_pack or {}),
        )

    def _sync_pass_result_selection_rationale(
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
        current_db = getattr(getattr(self.ctx, "current_project", None), "db", None)
        if current_db is None or not hasattr(current_db, "update_director_selection_rationale"):
            return
        if preserve_historical_companion:
            return
        try:
            current_db.update_director_selection_rationale(
                **self._build_stage4_selection_rationale_update_kwargs(
                    attempt_key=attempt_key,
                    trace_director_result=trace_director_result,
                    director_result=director_result,
                    selection_reason=selection_reason,
                    verdict_reason=verdict_reason,
                    advisory_warnings=advisory_warnings,
                    gate_semantics=gate_semantics,
                    fix_pack=fix_pack,
                    retry_budget_axes=retry_budget_axes,
                    prefer_authoritative_scope=False,
                )
            )
        except Exception as _e:
            logging.debug("[Stage4] director rationale sync failed: %s", _e)

    @staticmethod
    def _build_stage4_selection_rationale_sync_kwargs(
        *,
        attempt_key: str,
        trace_director_result,
        director_result: dict | None,
        selection_reason: str,
        verdict_reason: str,
        advisory_warnings: dict | None = None,
        prefer_authoritative_scope: bool,
    ) -> dict[str, object]:
        trace_payload = trace_director_result if isinstance(trace_director_result, dict) else {}
        director_payload = director_result if isinstance(director_result, dict) else {}
        if prefer_authoritative_scope:
            fix_scope = trace_payload.get(
                "authoritative_fix_scope",
                trace_payload.get(
                    "fix_scope",
                    director_payload.get("authoritative_fix_scope", director_payload.get("fix_scope", "")),
                ),
            )
        else:
            fix_scope = trace_payload.get("fix_scope", director_payload.get("fix_scope", ""))
        return {
            "attempt_key": attempt_key,
            "selection_reason": selection_reason,
            "verdict_reason": verdict_reason,
            "fix_scope": fix_scope,
            "advisory_warnings": advisory_warnings,
        }

    def _build_stage4_selection_rationale_update_kwargs(
        self,
        *,
        attempt_key: str,
        trace_director_result,
        director_result: dict | None,
        selection_reason: str,
        verdict_reason: str,
        advisory_warnings: dict | None = None,
        gate_semantics: dict | None = None,
        fix_pack: dict | None = None,
        retry_budget_axes: dict | None = None,
        prefer_authoritative_scope: bool,
    ) -> dict[str, object]:
        advisory_payload = (
            copy.deepcopy(advisory_warnings)
            if isinstance(advisory_warnings, dict)
            else self._build_final_selection_advisory_payload(
                gate_semantics=gate_semantics,
                fix_pack=fix_pack,
                retry_budget_axes=retry_budget_axes,
            )
        )
        return self._build_stage4_selection_rationale_sync_kwargs(
            attempt_key=attempt_key,
            trace_director_result=trace_director_result,
            director_result=director_result,
            selection_reason=selection_reason,
            verdict_reason=verdict_reason,
            advisory_warnings=advisory_payload or None,
            prefer_authoritative_scope=prefer_authoritative_scope,
        )

    def _build_final_selection_advisory_payload(
        self,
        *,
        gate_semantics: dict | None,
        fix_pack: dict | None = None,
        retry_budget_axes: dict | None = None,
    ) -> dict[str, object]:
        gate_payload = copy.deepcopy(gate_semantics) if isinstance(gate_semantics, dict) else {}
        fix_pack_payload = copy.deepcopy(fix_pack) if isinstance(fix_pack, dict) else {}
        if not fix_pack_payload and isinstance(gate_payload.get("fix_pack"), dict):
            fix_pack_payload = copy.deepcopy(gate_payload.get("fix_pack") or {})
        retry_payload = copy.deepcopy(retry_budget_axes) if isinstance(retry_budget_axes, dict) else {}
        contract_packet = self._build_stage4_attempt_contract_packet(
            {
                **({"gate_semantics": gate_payload} if gate_payload else {}),
                **({"fix_pack": fix_pack_payload} if fix_pack_payload else {}),
                **({"retry_budget_axes": retry_payload} if retry_payload else {}),
            },
            resolve_db_fallbacks=False,
        )
        advisory_payload: dict[str, object] = {}
        if gate_payload:
            advisory_payload["gate_semantics"] = gate_payload
        if fix_pack_payload:
            advisory_payload["fix_pack"] = fix_pack_payload
        if retry_payload:
            advisory_payload["retry_budget_axes"] = retry_payload
        if contract_packet.repair_contract:
            advisory_payload["repair_contract"] = contract_packet.repair_contract
        if contract_packet.scope_authority:
            advisory_payload["scope_authority"] = contract_packet.scope_authority
        return advisory_payload

    def _build_stage4_selection_advisory_payload(
        self,
        *,
        advisory_summary: dict[str, int] | None,
        director_result: dict | None,
        is_patch: bool,
        is_patch_fallback: bool,
        prev_score: int,
    ) -> dict[str, object]:
        selection_advisory: dict[str, object] = dict(advisory_summary or {})
        gate_semantics = self._build_gate_semantics_payload(
            director_result if isinstance(director_result, dict) else {}
        )
        fix_pack_payload = self._build_fix_pack_payload(director_result if isinstance(director_result, dict) else {})
        selection_advisory.update(
            self._build_final_selection_advisory_payload(
                gate_semantics=gate_semantics,
                fix_pack=fix_pack_payload,
            )
        )
        if is_patch:
            selection_advisory["patch_context"] = {
                "tag": "patch-fallback" if is_patch_fallback else "patch",
                "score": prev_score,
            }
        return selection_advisory

    def _emit_pass_result_logs(
        self,
        *,
        next_ep: int,
        round_num: int,
        round_ctx,
        chief_writer,
        director_result: dict,
        trace_director_result,
        director_feedback: str,
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
        logging_payload: _PassResultLoggingPayload,
    ) -> None:
        arc_num = round_ctx.arc_data.get("arc_no", 0)
        final_warnings = list(
            (trace_director_result.get("final_warnings") or []) if isinstance(trace_director_result, dict) else []
        )
        self._append_pass_round_logs(
            next_ep=next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result=director_result,
            trace_director_result=trace_director_result,
            director_feedback=director_feedback,
            initial_verdict=initial_verdict,
            initial_score=initial_score,
            final_verdict=final_verdict,
            final_score=final_score,
            selection_artifact_meta=selection_artifact_meta,
            validation_warnings=validation_warnings,
            is_patch=is_patch,
            is_patch_fallback=is_patch_fallback,
            trace_patch_trace=trace_patch_trace,
            tot_used=tot_used,
            mad_used=mad_used,
            asp_manuscript=asp_manuscript,
            logging_payload=logging_payload,
            arc_num=arc_num,
            final_warnings=final_warnings,
        )
        try:
            self._log_pass_session_decision(
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
                logging_payload=logging_payload,
            )
        except Exception as _e:
            logging.debug("[SilentPass:Stage4:SessionLog] %s", _e)

    def _append_pass_round_logs(
        self,
        *,
        next_ep: int,
        round_num: int,
        round_ctx,
        chief_writer,
        director_result: dict,
        trace_director_result,
        director_feedback: str,
        initial_verdict: str,
        initial_score: int,
        final_verdict: str,
        final_score: int,
        selection_artifact_meta: dict,
        validation_warnings: list[str],
        is_patch: bool,
        is_patch_fallback: bool,
        trace_patch_trace: dict,
        tot_used: bool,
        mad_used: bool,
        asp_manuscript: str,
        logging_payload: _PassResultLoggingPayload,
        arc_num: int,
        final_warnings: list[str],
    ) -> None:
        self._append_pass_episode_log(
            ep_num=next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result=director_result,
            trace_director_result=trace_director_result,
            director_feedback=director_feedback,
            initial_verdict=initial_verdict,
            initial_score=initial_score,
            final_verdict=final_verdict,
            final_score=final_score,
            is_patch=is_patch,
            is_patch_fallback=is_patch_fallback,
            tot_used=tot_used,
            mad_used=mad_used,
            validation_warnings=validation_warnings,
            final_warnings=final_warnings,
            patch_trace=trace_patch_trace,
            logging_payload=logging_payload,
            selection_artifact_meta=selection_artifact_meta,
            arc_num=arc_num,
            asp_manuscript=asp_manuscript,
        )
        self._log_round_outcome(
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
            final_warning_count=len(final_warnings),
            candidate_key=logging_payload.log_artifact_meta["candidate_key"],
            artifact_path=logging_payload.log_artifact_meta["artifact_path"],
        )

    def _append_pass_episode_log(
        self,
        *,
        ep_num: int,
        round_num: int,
        round_ctx,
        chief_writer,
        director_result: dict,
        trace_director_result,
        director_feedback: str,
        initial_verdict: str,
        initial_score: int,
        final_verdict: str,
        final_score: int,
        is_patch: bool,
        is_patch_fallback: bool,
        tot_used: bool,
        mad_used: bool,
        validation_warnings: list[str],
        final_warnings: list[str],
        patch_trace: dict,
        logging_payload: _PassResultLoggingPayload,
        selection_artifact_meta: dict,
        arc_num: int,
        asp_manuscript: str,
    ) -> None:
        self._append_episode_log(
            **_build_stage4_pass_episode_log_kwargs(
                owner=self,
                ep_num=ep_num,
                round_num=round_num,
                director_result=director_result,
                trace_director_result=trace_director_result if isinstance(trace_director_result, dict) else None,
                director_feedback=director_feedback,
                initial_verdict=initial_verdict,
                initial_score=initial_score,
                final_verdict=final_verdict,
                final_score=final_score,
                is_patch=is_patch,
                is_patch_fallback=is_patch_fallback,
                tot_used=tot_used,
                mad_used=mad_used,
                asp_manuscript=asp_manuscript,
                chief_writer=chief_writer,
                validation_warnings=validation_warnings,
                final_warnings=final_warnings,
                patch_trace=patch_trace,
                logging_payload=logging_payload,
                selection_artifact_meta=selection_artifact_meta,
                arc_num=arc_num,
            )
        )

    def _log_pass_session_decision(
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
        logging_payload: _PassResultLoggingPayload,
    ) -> None:
        decision_surface = _build_stage4_pass_decision_surface(
            director_result=director_result,
            trace_director_result=trace_director_result if isinstance(trace_director_result, dict) else None,
            fallback_reason=reason,
        )
        self._log_session_decision(
            **_build_stage4_pass_session_decision_kwargs(
                owner=self,
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
                logging_payload=logging_payload,
            )
        )

    def _run_director_continuity_and_state_tracker_advisories(
        self,
        *,
        candidates: list,
        validation_results: list[dict],
        next_ep: int,
        cv_context: dict,
        continuity_validator,
    ) -> None:
        # [V66.1] ContinuityValidator — npc_personalities, time_warnings 라우팅
        try:
            for ci, cand in enumerate(candidates):
                _ct_ms = cand.get("manuscript", "")
                if _ct_ms and ci < len(validation_results):
                    ct_result = continuity_validator.validate(next_ep, _ct_ms, cv_context)
                    ct_violations = ct_result.get("violations", [])
                    ct_warnings = ct_result.get("warnings", [])
                    if ct_violations:
                        for v in ct_violations:
                            reason = v.get("reason", str(v))
                            validation_results[ci]["warnings"].append(f"[V66.1] 연속성: {reason}")
                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                        validation_results[ci]["focus_points"].append(f"연속성 위반 {len(ct_violations)}건")
                        self.ctx.ui.log(f"      ⚠️ 후보{ci + 1} 연속성 위반 {len(ct_violations)}건")
                    if ct_warnings:
                        for w in ct_warnings:
                            w_msg = w.get("reason", str(w)) if isinstance(w, dict) else str(w)
                            validation_results[ci]["warnings"].append(f"[V66.1] 연속성 경고: {w_msg}")
                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
        except Exception as _ct_err:
            self.ctx.ui.log(f"      ⚠️ [V66.1] ContinuityValidator 실행 실패: {str(_ct_err)}")

        # [D Step 4] 좌절-보상 타이머 — Director에 advisory 전달
        try:
            _frust_warnings = continuity_validator.check_frustration_streak(next_ep)
            if _frust_warnings:
                for ci in range(len(validation_results)):
                    for _fw in _frust_warnings:
                        validation_results[ci]["warnings"].append(f"[D Step 4] {_fw}")
                    validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                for _fw in _frust_warnings:
                    self.ctx.ui.log(f"      ⚠️ {_fw}")
        except Exception as _frust_err:
            logging.warning("[D Step 4] 좌절-보상 타이머 실패 (비차단): %s", _frust_err)

        # [V66.2] C-4: 파괴 엔티티 감지 → Director에 경고 전달
        try:
            if self.ctx.state_tracker:
                for ci, cand in enumerate(candidates):
                    _de_ms = cand.get("manuscript", "")
                    if _de_ms and ci < len(validation_results):
                        _de_warnings = self.ctx.state_tracker.check_destroyed_entity_in_manuscript(_de_ms)
                        if _de_warnings:
                            for _dw in _de_warnings:
                                _dw_msg = _dw.get("message", str(_dw)) if isinstance(_dw, dict) else str(_dw)
                                validation_results[ci]["warnings"].append(f"[V66.2] 파괴된 엔티티 등장: {_dw_msg}")
                            validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
        except (KeyError, ValueError, TypeError) as _de_err:
            logging.warning(f" [V66.2] 파괴 엔티티 검사 오류: {_de_err}")

    def _run_blocking_validator_advisories(
        self,
        *,
        candidates: list,
        validation_results: list[dict],
        next_ep: int,
        round_num: int,
        cv_context: dict,
        blocking_validator,
    ) -> None:
        # [V66.1] BlockingValidator — advisory 경고 수집 (Director 전달용)
        # [V70.1] 대원칙 준수: Python은 수집만, 판단은 Director(LLM)가.
        #   기존 TF7-P0-02 즉시 제외 → advisory 경고로 변환, Director에게 전달.
        try:
            for ci, cand in enumerate(candidates):
                manuscript = cand.get("manuscript", "")
                if not manuscript or ci >= len(validation_results):
                    continue
                bv_result = blocking_validator.validate(manuscript, cv_context)
                self._apply_blocking_validator_result(
                    validation_result=validation_results[ci],
                    bv_result=bv_result,
                    candidate_index=ci + 1,
                    next_ep=next_ep,
                    round_num=round_num,
                )
        except Exception as bv_err:
            self.ctx.ui.log(f"      ⚠️ [V66.1] BlockingValidator 실행 실패: {str(bv_err)}")

    def _apply_blocking_validator_result(
        self,
        *,
        validation_result: dict,
        bv_result: dict | None,
        candidate_index: int,
        next_ep: int,
        round_num: int,
    ) -> None:
        bv_result = bv_result if isinstance(bv_result, dict) else {}
        bv_failures = bv_result.get("failures", []) or []
        bv_advisory_warnings = self._collect_blocking_validator_advisory_warnings(bv_result)

        self._apply_blocking_validator_failures(
            validation_result=validation_result,
            bv_failures=bv_failures,
            candidate_index=candidate_index,
            next_ep=next_ep,
            round_num=round_num,
        )
        self._apply_blocking_validator_advisories(
            validation_result=validation_result,
            bv_advisory_warnings=bv_advisory_warnings,
            candidate_index=candidate_index,
            next_ep=next_ep,
            round_num=round_num,
        )

    def _apply_blocking_validator_failures(
        self,
        *,
        validation_result: dict,
        bv_failures: list,
        candidate_index: int,
        next_ep: int,
        round_num: int,
    ) -> None:
        if not bv_failures:
            return
        for failure in bv_failures:
            reason = failure.get("reason", str(failure))
            severity = failure.get("severity", "HIGH")
            validation_result["warnings"].append(f"[Python검증-{severity}] {reason}")
        validation_result["warning_count"] = len(validation_result["warnings"])
        validation_result["focus_points"].append(f"Python 검증 경고 {len(bv_failures)}건 (Director 판단 필요)")
        self.ctx.ui.log(
            f"      ⚠️ 후보{candidate_index} Python 검증 경고 {len(bv_failures)}건 → Director에 전달",
            stage="stage4",
            component="python_prevalidation",
            ep_num=next_ep,
            round_num=round_num,
            event_kind="warning",
            level="warning",
            meta={"candidate_index": candidate_index, "failure_count": len(bv_failures)},
        )
        for failure in bv_failures:
            self.ctx.ui.log(
                f"         - [{failure.get('severity', '?')}] {failure.get('reason', '?')}",
                stage="stage4",
                component="python_prevalidation",
                ep_num=next_ep,
                round_num=round_num,
                event_kind="warning",
                level="warning",
                meta={"candidate_index": candidate_index, "severity": failure.get("severity", "?")},
            )

    def _apply_blocking_validator_advisories(
        self,
        *,
        validation_result: dict,
        bv_advisory_warnings: list[str],
        candidate_index: int,
        next_ep: int,
        round_num: int,
    ) -> None:
        if not bv_advisory_warnings:
            return
        for advisory_warning in bv_advisory_warnings:
            validation_result["warnings"].append(f"[Python검증-ADVISORY] {advisory_warning}")
        validation_result["warning_count"] = len(validation_result["warnings"])
        validation_result["focus_points"].append(f"Python 검증 advisory {len(bv_advisory_warnings)}건 (Director 참고)")
        _bv_detail_lines = "\n".join(f"    - {w}" for w in bv_advisory_warnings)
        self.ctx.ui.log(
            f"      ⚠️ 후보{candidate_index} Python 검증 advisory {len(bv_advisory_warnings)}건 → Director에 전달\n{_bv_detail_lines}",
            stage="stage4",
            component="python_prevalidation",
            ep_num=next_ep,
            round_num=round_num,
            event_kind="warning",
            level="warning",
            meta={
                "candidate_index": candidate_index,
                "advisory_count": len(bv_advisory_warnings),
                "advisory_details": bv_advisory_warnings,
            },
        )

    @staticmethod
    def _collect_blocking_validator_advisory_warnings(bv_result: dict | None) -> list[str]:
        bv_result = bv_result if isinstance(bv_result, dict) else {}
        bv_advisory_warnings: list[str] = []
        bv_seen_warnings: set[str] = set()
        for raw_warning in bv_result.get("warnings", []) or []:
            warning_text = str(raw_warning or "").strip()
            if warning_text and warning_text not in bv_seen_warnings:
                bv_advisory_warnings.append(warning_text)
                bv_seen_warnings.add(warning_text)
        for raw_check in bv_result.get("degraded_checks", []) or []:
            check_name = str(raw_check or "").strip()
            warning_text = f"degraded: {check_name}" if check_name else ""
            if warning_text and warning_text not in bv_seen_warnings:
                bv_advisory_warnings.append(warning_text)
                bv_seen_warnings.add(warning_text)
        return bv_advisory_warnings

    def _execute_pass_with_fix_loop(
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
        return self.retry_runtime.execute_pass_with_fix_loop(
            verdict=verdict,
            final_manuscript=final_manuscript,
            final_state_updates=final_state_updates,
            director_result=director_result,
            director_feedback=director_feedback,
            round_ctx=round_ctx,
            round_num=round_num,
            score=score,
            quality_gate_score=quality_gate_score,
            director_mandatory_context=director_mandatory_context,
        )

    def _process_verdict(
        self,
        *,
        director_result: dict,
        director_feedback: str,
        verdict: str,
        score: int,
        round_ctx,
        round_num: int,
        previous_attempt: dict | None,
        is_patch: bool,
        is_patch_fallback: bool,
        prev_score: int,
        stage4_spinner,
        director_mandatory_context: str,
        director_memory_context: str,
        error_category: str,
    ):
        """[B-1-3b] PASS/PASS_WITH_FIX 결과를 후처리한다.

        Returns (result|None, director_feedback, previous_attempt, trace_meta).

        Post-gate chain applied here (in order):
          1. Quality-floor gate — PASS with score < quality_gate_score → REJECT
          2. CONDITIONAL_PASS normalization → PASS
        After gates, positive verdicts delegate to _process_positive_verdict;
        negative verdicts return None with a trace_meta snapshot.
        """
        from modules.validation.threshold_helper import _threshold

        _quality_gate_score = _threshold("scoring.quality_gate_score", 90)
        if verdict == "PASS" and score < _quality_gate_score:
            self.ctx.ui.log(f"   [QualityGate] PASS -> score={score} < {_quality_gate_score}; downgrade to REJECT")
            verdict = "REJECT"
            error_category = error_category or "QUALITY_FLOOR_FAIL"  # [TF-5]
            director_result = self._apply_director_gate_update(
                director_result,
                final_verdict="REJECT",
                gate_basis="quality_floor_fail",
            )
            director_feedback += (
                f"\n[Quality Gate] Director PASS but score {score} is below {_quality_gate_score}. "
                "Retry after improvement."
            )

        # [TF-R4] CONDITIONAL_PASS가 upstream에서 미해소된 채 도달하면 PASS로 정규화
        if verdict == "CONDITIONAL_PASS":
            logging.info("[Stage4] _process_verdict: CONDITIONAL_PASS → PASS 정규화")
            verdict = "PASS"

        if verdict in ("PASS", "PASS_WITH_FIX"):
            self._consecutive_empty_patches = 0  # [IFC] reset on positive verdict
            processed = self._process_positive_verdict(
                director_result=director_result,
                director_feedback=director_feedback,
                verdict=verdict,
                score=score,
                round_ctx=round_ctx,
                round_num=round_num,
                previous_attempt=previous_attempt,
                is_patch=is_patch,
                is_patch_fallback=is_patch_fallback,
                prev_score=prev_score,
                stage4_spinner=stage4_spinner,
                director_mandatory_context=director_mandatory_context,
                director_memory_context=director_memory_context,
                error_category=error_category,
                quality_gate_score=int(_quality_gate_score),
            )
            return (
                processed.pass_result,
                processed.director_feedback,
                processed.previous_attempt,
                processed.trace_meta,
            )

        return (
            None,
            director_feedback,
            previous_attempt,
            {
                "final_verdict": verdict,
                "final_score": score,
                "director_result": director_result,
                "patch_trace": {},
            },
        )

    def _process_positive_verdict(
        self,
        *,
        director_result: dict,
        director_feedback: str,
        verdict: str,
        score: int,
        round_ctx,
        round_num: int,
        previous_attempt: dict | None,
        is_patch: bool,
        is_patch_fallback: bool,
        prev_score: int,
        stage4_spinner,
        director_mandatory_context: str,
        director_memory_context: str,
        error_category: str,
        quality_gate_score: int,
    ) -> _VerdictProcessingPayload:
        seed_payload = self._build_positive_verdict_seed(
            round_ctx=round_ctx,
            director_result=director_result,
        )
        transition = self._run_positive_verdict_transition(
            verdict=verdict,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            error_category=error_category,
            score=score,
            round_ctx=round_ctx,
            round_num=round_num,
            stage4_spinner=stage4_spinner,
            director_memory_context=director_memory_context,
            director_mandatory_context=director_mandatory_context,
            quality_gate_score=quality_gate_score,
            final_manuscript=seed_payload.final_manuscript,
            final_state_updates=seed_payload.final_state_updates,
            director_result=director_result,
        )
        is_patch = bool(is_patch or transition.patch_trace)

        if transition.verdict in ("PASS", "PASS_WITH_FIX", "CONDITIONAL_PASS"):
            return self._build_positive_verdict_success_result(
                transition=transition,
                seed_payload=seed_payload,
                round_ctx=round_ctx,
                round_num=round_num,
                prev_score=prev_score,
                is_patch=is_patch,
                is_patch_fallback=is_patch_fallback,
            )

        return self._build_positive_verdict_trace_only_payload(
            transition=transition,
        )

    def _build_positive_verdict_seed(
        self,
        *,
        round_ctx,
        director_result: dict,
    ) -> _PositiveVerdictSeedPayload:
        next_ep = round_ctx.next_ep
        selected_candidate = director_result.get("selected_candidate") or {}
        initial_selected_candidate = dict(selected_candidate) if isinstance(selected_candidate, dict) else {}
        final_manuscript = selected_candidate.get("manuscript", "")
        final_title = selected_candidate.get("title", f"\uc81c{next_ep}\ud654")
        final_state_updates = director_result.get("state_updates", {})
        if not isinstance(final_state_updates, dict):
            final_state_updates = {}
        else:
            final_state_updates = dict(final_state_updates)
        return _PositiveVerdictSeedPayload(
            next_ep=next_ep,
            initial_selected_candidate=initial_selected_candidate,
            final_manuscript=final_manuscript,
            final_title=final_title,
            final_state_updates=final_state_updates,
        )

    def _run_positive_verdict_transition(
        self,
        *,
        verdict: str,
        director_feedback: str,
        previous_attempt: dict | None,
        error_category: str,
        score: int,
        round_ctx,
        round_num: int,
        stage4_spinner,
        director_memory_context: str,
        director_mandatory_context: str,
        quality_gate_score: int,
        final_manuscript: str,
        final_state_updates: dict,
        director_result: dict,
    ) -> _PositiveVerdictTransitionPayload:
        verdict, director_feedback, previous_attempt, error_category = self.post_select_runtime.run_post_select_checks(
            verdict=verdict,
            final_manuscript=final_manuscript,
            final_state_updates=final_state_updates,
            next_ep=round_ctx.next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            director_result=director_result,
            director_feedback=director_feedback,
            score=score,
            error_category=error_category,
            previous_attempt=previous_attempt,
            stage4_spinner=stage4_spinner,
            director_memory_context=director_memory_context,
        )

        patch_trace = {}
        if verdict == "PASS_WITH_FIX" and final_manuscript:
            verdict, final_manuscript, final_state_updates, director_result, director_feedback, patch_trace = (
                self._execute_pass_with_fix_loop(
                    verdict=verdict,
                    final_manuscript=final_manuscript,
                    final_state_updates=final_state_updates,
                    director_result=director_result,
                    director_feedback=director_feedback,
                    round_ctx=round_ctx,
                    round_num=round_num,
                    score=score,
                    quality_gate_score=quality_gate_score,
                    director_mandatory_context=director_mandatory_context,
                )
            )
        final_score = score
        if isinstance(director_result, dict) and "score" in director_result:
            try:
                final_score = int(director_result.get("score", score))
            except (ValueError, TypeError):
                final_score = score
        return _PositiveVerdictTransitionPayload(
            verdict=verdict,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            error_category=error_category,
            final_manuscript=final_manuscript,
            final_state_updates=final_state_updates,
            director_result=director_result,
            patch_trace=patch_trace,
            final_score=final_score,
        )

    def _build_positive_verdict_success_result(
        self,
        *,
        transition: _PositiveVerdictTransitionPayload,
        seed_payload: _PositiveVerdictSeedPayload,
        round_ctx,
        round_num: int,
        prev_score: int,
        is_patch: bool,
        is_patch_fallback: bool,
    ) -> _VerdictProcessingPayload:
        final_state_updates = self._annotate_positive_verdict_state(
            final_state_updates=transition.final_state_updates,
            director_result=transition.director_result,
            final_score=transition.final_score,
            verdict=transition.verdict,
            final_manuscript=transition.final_manuscript,
        )
        return self._build_positive_verdict_payload(
            verdict=transition.verdict,
            director_feedback=transition.director_feedback,
            previous_attempt=transition.previous_attempt,
            final_manuscript=transition.final_manuscript,
            final_title=seed_payload.final_title,
            final_state_updates=final_state_updates,
            director_result=transition.director_result,
            error_category=transition.error_category,
            next_ep=seed_payload.next_ep,
            round_num=round_num,
            round_ctx=round_ctx,
            prev_score=prev_score,
            is_patch=is_patch,
            is_patch_fallback=is_patch_fallback,
            patch_trace=transition.patch_trace,
            initial_selected_candidate=seed_payload.initial_selected_candidate,
            final_score=transition.final_score,
        )

    @staticmethod
    def _build_positive_verdict_trace_only_payload(
        *,
        transition: _PositiveVerdictTransitionPayload,
    ) -> _VerdictProcessingPayload:
        return _VerdictProcessingPayload(
            pass_result=None,
            director_feedback=transition.director_feedback,
            previous_attempt=transition.previous_attempt,
            trace_meta={
                "final_verdict": transition.verdict,
                "final_score": transition.final_score,
                "director_result": transition.director_result,
                "patch_trace": transition.patch_trace,
            },
        )

    def _annotate_positive_verdict_state(
        self,
        *,
        final_state_updates: dict,
        director_result: dict,
        final_score: int,
        verdict: str,
        final_manuscript: str,
    ) -> dict:
        if final_score > 0:
            final_state_updates["director_score"] = final_score
        final_state_updates["_director_quality_labels"] = {
            "score": final_score,
            "verdict": verdict,
            "director_verdict": director_result.get("director_verdict", ""),
            "gate_basis": director_result.get("gate_basis", ""),
            "repair_scope": director_result.get("repair_scope", "none"),
            "selection_reason": director_result.get("selection_reason", ""),
            "open_review": director_result.get("open_review", ""),
            "score_breakdown": director_result.get("score_breakdown", {}) or {},
            "consistency_checklist": director_result.get("consistency_checklist", {}) or {},
        }
        if self.ctx.state_tracker:
            try:
                time_warnings = self.ctx.state_tracker.check_time_consistency(
                    final_manuscript, self.ctx.state_tracker.in_world_timeline
                )
                if time_warnings:
                    for warning in time_warnings:
                        self.ctx.ui.log(f"   [V66.1] Time warning: {warning}")
                    self.time_warnings.extend(time_warnings)
            except (KeyError, ValueError, TypeError) as tc_err:
                logging.warning(f"[V66.1] Time consistency check failed: {tc_err}")
        return final_state_updates

    def _build_positive_verdict_payload(
        self,
        *,
        verdict: str,
        director_feedback: str,
        previous_attempt: dict | None,
        final_manuscript: str,
        final_title: str,
        final_state_updates: dict,
        director_result: dict,
        error_category: str,
        next_ep: int,
        round_num: int,
        round_ctx,
        prev_score: int,
        is_patch: bool,
        is_patch_fallback: bool,
        patch_trace: dict,
        initial_selected_candidate: dict,
        final_score: int,
    ) -> _VerdictProcessingPayload:
        from modules.core.stage4_types import _InterviewRoundResult

        self.ctx.ui.log(f"   Round {round_num + 1} {verdict}!")
        selected_candidate = director_result.get("selected_candidate", {}) if isinstance(director_result, dict) else {}
        if not isinstance(selected_candidate, dict):
            selected_candidate = dict(initial_selected_candidate)
        if not selected_candidate:
            selected_candidate = dict(initial_selected_candidate)
        candidate_key = build_candidate_key(
            label=str(director_result.get("selected", "") or "") if isinstance(director_result, dict) else "",
            strategy=str(selected_candidate.get("strategy_name", "") or selected_candidate.get("strategy", "")),
            fallback="stage4",
        )
        patch_advisory_payload = self._build_stage4_patch_advisory_payload(
            director_result=director_result,
            patch_trace=patch_trace,
        )
        attempt_artifact_meta = self._record_s4_attempt(
            episode=next_ep,
            round_num=round_num,
            success=True,
            score=final_score,
            is_patch=is_patch,
            prev_score=prev_score,
            patch_fallback=is_patch_fallback,
            arc=round_ctx.arc_data.get("arc_no", 0),
            verdict=verdict,
            fix_scope=director_result.get("fix_scope", "") if isinstance(director_result, dict) else None,
            advisory_flags={
                **(dict(getattr(self, "_last_advisory_summary", None) or {})),
                "gate_semantics": self._build_gate_semantics_payload(director_result),
                "fix_pack": patch_advisory_payload.get("fix_pack", {}),
                "retry_budget_axes": dict(getattr(self, "_last_retry_budget_axes", {}) or {}),
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
            artifact_payload=final_manuscript,
            artifact_kind="patched_after_fix" if (is_patch or patch_trace) else "final_manuscript",
            selection_reason=director_result.get("selection_reason", ""),
            verdict_reason=director_result.get("verdict_reason", ""),
            open_review=director_result.get("open_review", ""),
            fix_scope_reasoning=director_result.get("fix_scope_reasoning", ""),
            runtime_advisory=self._build_retry_advisory_digest(),
            error_category=error_category or director_result.get("error_category", ""),
            score_breakdown=director_result.get("score_breakdown", {}),
            initial_verdict=director_result.get("director_verdict", "") or director_result.get("original_verdict", ""),
        )
        return _VerdictProcessingPayload(
            pass_result=_InterviewRoundResult(
                verdict=verdict,
                director_feedback=director_feedback,
                previous_attempt=previous_attempt,
                final_manuscript=final_manuscript,
                final_title=final_title,
                final_state_updates=final_state_updates,
                error_category=error_category,
                attempt_artifact_meta=attempt_artifact_meta,
            ),
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            trace_meta={
                "final_verdict": verdict,
                "final_score": final_score,
                "director_result": director_result,
                "patch_trace": patch_trace,
            },
        )

    def _handle_reject(
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
        return self.reject_runtime.handle_reject(
            director_result=director_result,
            director_feedback=director_feedback,
            candidates=candidates,
            validation_results=validation_results,
            round_ctx=round_ctx,
            round_num=round_num,
            previous_attempt=previous_attempt,
            is_patch=is_patch,
            is_patch_fallback=is_patch_fallback,
            prev_score=prev_score,
            prev_manuscript=prev_manuscript,
            asp_manuscript=asp_manuscript,
            tot_used=tot_used,
            mad_used=mad_used,
            selected=selected,
            score=score,
            error_category=error_category,
            patch_trace=patch_trace,
        )

    def _build_retry_regenerate_kwargs(
        self,
        *,
        common_writer_kwargs: dict,
        reject_bucket: str,
        fix_scope: str,
        selected_strategy_key: str,
    ) -> tuple[dict, str, int]:
        regen_kwargs = dict(common_writer_kwargs)
        if reject_bucket in {"quality_issue", "constraint_violation"} and fix_scope != "full":
            regen_kwargs["strategy_budget"] = "reduced"
            regen_kwargs["preferred_strategy"] = selected_strategy_key
            return regen_kwargs, "reduced", 2
        return regen_kwargs, "full", 3

    def _generate_candidates(
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
        return self.retry_runtime.generate_candidates(
            round_num=round_num,
            chief_writer=chief_writer,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            prev_manuscript=prev_manuscript,
            style_guide=style_guide,
            blueprint=blueprint,
            common_writer_kwargs=common_writer_kwargs,
            arc_num=arc_num,
        )

    def _resolve_npc_profiles(self, arc_data) -> dict:
        """Prefer the Stage4 facade seam, then mirror PromptBuilder filtering as fallback."""
        _arc_data = arc_data if isinstance(arc_data, dict) else {}

        _extract_npc_profiles = getattr(self.ctx, "extract_npc_profiles", None)
        if callable(_extract_npc_profiles):
            try:
                _profiles = _extract_npc_profiles(_arc_data)
            except Exception as _npc_err:
                logging.warning(f"[SilentPass:InterviewRound] npc_profiles facade 실패: {_npc_err!s:.100}")
            else:
                if isinstance(_profiles, dict):
                    return _profiles

        try:
            _mb = self.ctx.current_project.master_bible or {}
            _mb_root = _mb.get("MasterBible", _mb)
            _npc_lib = _mb_root.get("AssetLibrary", {}).get("KeyNPCs", [])
            if not _npc_lib:
                _npc_lib = _mb_root.get("AssetLibrary", {}).get("Key_NPCs", [])
            if not isinstance(_npc_lib, list):
                return {}

            _arc_text = json.dumps(_arc_data, ensure_ascii=False) if _arc_data else ""
            _npc_profiles = {}
            for _npc in _npc_lib:
                if not isinstance(_npc, dict):
                    continue
                _npc_name = _npc.get("name", "") or _npc.get("Name", "")
                if not _npc_name:
                    continue
                if _arc_text and _npc_name not in _arc_text:
                    continue
                _npc_profiles[_npc_name] = _npc
            return _npc_profiles
        except Exception as _npc_err:
            logging.warning(f"[SilentPass:InterviewRound] npc_profiles fallback 실패: {_npc_err!s:.100}")
            return {}

    @staticmethod
    def _merge_prev_hud_extras(hud_snapshot: dict, state_data: dict) -> dict:
        if not isinstance(hud_snapshot, dict):
            return {}
        if not isinstance(state_data, dict):
            return copy.deepcopy(hud_snapshot)

        merged = copy.deepcopy(hud_snapshot)
        actual_truth = state_data.get("actual_truth", {})
        if not isinstance(actual_truth, dict):
            actual_truth = {}

        for key in ("active_pressure_vectors",):
            if key in merged:
                continue
            if key in actual_truth:
                merged[key] = copy.deepcopy(actual_truth.get(key))
            elif key in state_data:
                merged[key] = copy.deepcopy(state_data.get(key))
        return merged

    def _resolve_prev_hud_snapshot(self, next_ep: int) -> tuple[dict, str]:
        """Prefer persisted previous-episode truth over live HUD fallback."""
        if next_ep <= 1:
            return {}, "episode-1"

        _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
        _prev_ep = next_ep - 1
        _prev_ms = None
        _state_data = {}

        if _db:
            try:
                _prev_ms = _db.get_manuscript(_prev_ep)
            except Exception as _ms_err:
                logging.warning(f"[SilentPass:InterviewRound] prev_hud manuscript load 실패: {_ms_err!s:.100}")

            try:
                _state_log = _db.load_state_log(_prev_ep)
            except Exception as _state_err:
                logging.warning(f"[SilentPass:InterviewRound] prev_hud state_log load 실패: {_state_err!s:.100}")
            else:
                _loaded_state = _state_log.get("data", {}) if isinstance(_state_log, dict) else {}
                if isinstance(_loaded_state, dict):
                    _state_data = _loaded_state

            if isinstance(_prev_ms, dict):
                _hud_snapshot = _prev_ms.get("hud_snapshot")
                if isinstance(_hud_snapshot, dict) and _hud_snapshot:
                    return self._merge_prev_hud_extras(_hud_snapshot, _state_data), "manuscript.hud_snapshot"

            if isinstance(_state_data, dict):
                _hud_snapshot = _state_data.get("hud_snapshot")
                if isinstance(_hud_snapshot, dict) and _hud_snapshot:
                    return self._merge_prev_hud_extras(_hud_snapshot, _state_data), "state_logs.data.hud_snapshot"

                _actual_truth = _state_data.get("actual_truth")
                if isinstance(_actual_truth, dict) and _actual_truth:
                    return self._merge_prev_hud_extras(_actual_truth, _state_data), "state_logs.data.actual_truth"

        try:
            if hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud:
                _prev_hud = self.ctx.sys.hud.pro_root
                if isinstance(_prev_hud, dict) and _prev_hud:
                    return self._merge_prev_hud_extras(_prev_hud, _state_data), "live_hud.pro_root"
        except Exception as _hud_err:
            logging.warning(f"[SilentPass:InterviewRound] prev_hud live fallback 실패: {_hud_err!s:.100}")

        return {}, ""

    def _build_cv_identity_context(self, *, next_ep: int, genre_name: str) -> dict:
        cv_context = {
            "time_warnings": self.time_warnings,
            "_failure_learner": getattr(self.ctx, "failure_learner", None),
        }
        prev_hud, prev_hud_source = self._resolve_prev_hud_snapshot(next_ep)
        cv_context["prev_hud"] = prev_hud
        cv_context["prev_hud_source"] = prev_hud_source
        if prev_hud:
            cv_context["martial_hud"] = prev_hud

        incarnation_type = ""
        try:
            bible_root = self.ctx.current_project.master_bible.get("MasterBible", self.ctx.current_project.master_bible)
            incarnation_type = bible_root.get("protagonist_config", {}).get("incarnation_type", "")
        except Exception as e:
            logging.warning(f"[SilentPass:InterviewRound] incarnation_type 로드 실패: {e!s:.100}")
        cv_context["incarnation_type"] = incarnation_type

        protagonist_name = ""
        try:
            from modules.core.constants import HUDKeys

            mb = self.ctx.current_project.master_bible or {}
            mb_root = mb.get("MasterBible", mb)
            protagonist_name = HUDKeys.get_protagonist_name(mb_root, genre_name)
        except Exception as e:
            logging.debug("[SilentPass:Stage4:ProtoName] %s", e)
        if protagonist_name and protagonist_name != "주인공":
            cv_context["protagonist_name"] = protagonist_name
        else:
            logging.warning("[Stage4] protagonist_name 주입 실패 — POV 검사 민감도 저하 가능")
        return cv_context

    def _build_cv_state_tracker_context(self) -> dict:
        state_tracker = self.ctx.state_tracker
        cv_context = {"encyclopedia": {"npcs": []}}
        if not state_tracker:
            return cv_context

        encyclopedia_npcs = []
        for npc_name, npc_info in getattr(state_tracker, "npc_registry", {}).items():
            encyclopedia_npcs.append(
                {
                    "name": npc_name,
                    "status": npc_info.get("status", "alive"),
                    "death_arc": npc_info.get("death_arc"),
                    "aliases": npc_info.get("aliases", []),
                }
            )
        cv_context["encyclopedia"] = {"npcs": encyclopedia_npcs}
        cv_context["item_states"] = (
            {name: info.get("condition", "정상") for name, info in state_tracker.item_state_registry.items()}
            if hasattr(state_tracker, "item_state_registry")
            else {}
        )
        cv_context["npc_personalities"] = (
            {
                name: {
                    "traits": info.get("personality_traits", ""),
                    "motivation": info.get("primary_motivation", ""),
                }
                for name, info in state_tracker.npc_registry.items()
                if info.get("personality_traits")
            }
            if hasattr(state_tracker, "npc_registry")
            else {}
        )
        if hasattr(state_tracker, "get_npc_change_history") and state_tracker.npc_registry:
            npc_history = {}
            for history_name in state_tracker.npc_registry:
                try:
                    history = state_tracker.get_npc_change_history(history_name, limit=10)
                except Exception as npc_err:
                    logging.warning("[InterviewRound] get_npc_change_history 실패 (npc=%s): %s", history_name, npc_err)
                    continue
                if history:
                    npc_history[history_name] = history
            if npc_history:
                cv_context["npc_history"] = npc_history
        return cv_context

    def _build_cv_role_context(self, *, next_ep: int) -> dict:
        cv_context = {}
        karma_dict = {}
        try:
            if next_ep > 1:
                prev_bible = self.ctx.current_project.db.get_episode_bible(next_ep - 1)
                raw_karma = prev_bible.get("karma_matrix", []) if prev_bible else []
                if isinstance(raw_karma, list):
                    for karma_entry in raw_karma:
                        if isinstance(karma_entry, dict) and karma_entry.get("target"):
                            target = karma_entry["target"]
                            if target not in karma_dict:
                                karma_dict[target] = {"relation_type": karma_entry.get("relation", ""), "events": []}
                            karma_dict[target]["events"].append(
                                {
                                    "type": karma_entry.get("type", ""),
                                    "description": karma_entry.get("description", ""),
                                }
                            )
        except Exception as km_err:
            logging.warning(f"[SilentPass:InterviewRound] karma_matrix 조립 실패: {km_err!s:.100}")
        if karma_dict:
            cv_context["karma_matrix"] = karma_dict

        try:
            mb = self.ctx.current_project.master_bible or {}
            mb_root = mb.get("MasterBible", mb)
            key_npcs = mb_root.get("AssetLibrary", {}).get("KeyNPCs", [])
            if not key_npcs:
                key_npcs = mb_root.get("AssetLibrary", {}).get("Key_NPCs", [])
            villain_keywords = ("빌런", "적대", "악역", "antagonist", "주적", "숙적", "원수")
            superior_keywords = (
                "상사",
                "상관",
                "사부",
                "스승",
                "사형",
                "문주",
                "장문인",
                "회장",
                "대표",
                "사장",
                "원장",
                "교수",
            )
            for npc in key_npcs or []:
                if not isinstance(npc, dict):
                    continue
                role = str(npc.get("role", ""))
                name = npc.get("name", "")
                if not name:
                    continue
                if self.ctx.state_tracker and hasattr(self.ctx.state_tracker, "npc_registry"):
                    npc_info = self.ctx.state_tracker.npc_registry.get(name, {})
                    if npc_info.get("status") == "dead":
                        continue
                if "villain_context" not in cv_context and any(kw in role for kw in villain_keywords):
                    cv_context["villain_context"] = {
                        "villain_name": name,
                        "villain_role": role,
                        "is_aware": True,
                    }
                if "authority_context" not in cv_context and any(kw in role for kw in superior_keywords):
                    ws_position = ""
                    try:
                        ws = getattr(self.ctx, "world_state", None)
                        if ws:
                            ws_npc = ws._state.get("alive_npcs", {}).get(name, {})
                            ws_known_attrs = ws_npc.get("known_attrs", {})
                            if isinstance(ws_known_attrs.get("position"), dict):
                                ws_position = ws_known_attrs["position"].get("value", "")
                            elif isinstance(ws_known_attrs.get("position"), str):
                                ws_position = ws_known_attrs["position"]
                    except Exception:
                        pass
                    cv_context["authority_context"] = {
                        "protagonist_position": mb_root.get("protagonist_config", {}).get("position", ""),
                        "superior_alive": True,
                        "superior_name": name,
                        "superior_position": ws_position or npc.get("position", role),
                    }
                if "villain_context" in cv_context and "authority_context" in cv_context:
                    break
        except Exception as role_ctx_err:
            logging.warning(f"[SilentPass:InterviewRound] role context 조립 실패: {role_ctx_err!s:.100}")
        return cv_context

    # ═══════════════════════════════════════════════════════════════════════
    # Advisory chain (8 advisories, parallel ThreadPoolExecutor)
    # ═══════════════════════════════════════════════════════════════════════

    def _run_advisory_chain(
        self,
        candidates: list[dict],
        validation_results: list[dict],
        next_ep: int,
        genre_name: str,
        *,
        round_num: int | None = None,
    ) -> list[str]:
        """[B-1-3b][TF-50] Advisory chain 병렬 실행, Director mandatory_context 파트 반환."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from concurrent.futures import TimeoutError as FuturesTimeoutError

        logging.debug(
            "Advisory 검증 시작 — 9개 병렬 실행 (TruthGate, NPC, 수치, 회상, 정보역설, 관계, 장기반복, 수치정합, StyleSignal)"
        )
        _round_num = round_num
        self.ctx.ui.log(
            "      \u23f3 Advisory 체인 9개 병렬 실행 중...",
            stage="stage4",
            component="advisory_chain",
            ep_num=next_ep,
            round_num=_round_num,
            event_kind="progress",
        )

        futures = {}
        _advisory_parts: list[str] = []
        _advisory_per_type: dict[str, list[str]] = {}
        executor = ThreadPoolExecutor(max_workers=9, thread_name_prefix="advisory")
        try:
            _truth_gate_results = self._clone_validation_results_for_advisory(validation_results)
            futures[executor.submit(self._advisory_truth_gate, candidates, _truth_gate_results, next_ep)] = (
                "TruthGate",
                _truth_gate_results,
            )
            _npc_drift_results = self._clone_validation_results_for_advisory(validation_results)
            futures[executor.submit(self._advisory_npc_drift, candidates, _npc_drift_results, next_ep)] = (
                "NpcDrift",
                _npc_drift_results,
            )
            futures[executor.submit(self._advisory_numeric_drift, next_ep)] = ("NumericDrift", None)
            futures[executor.submit(self._advisory_flashback, candidates, next_ep)] = ("Flashback", None)
            futures[executor.submit(self._advisory_info_paradox, candidates, next_ep, genre_name)] = (
                "InfoParadox",
                None,
            )
            futures[executor.submit(self._advisory_rel_drift, candidates, next_ep)] = ("RelDrift", None)
            futures[executor.submit(self._advisory_long_term_rep, candidates, next_ep)] = ("LongTermRep", None)
            _numeric_consistency_results = self._clone_validation_results_for_advisory(validation_results)
            futures[
                executor.submit(
                    self._advisory_numeric_consistency,
                    candidates,
                    _numeric_consistency_results,
                    next_ep,
                )
            ] = (
                "NumericConsistency",
                _numeric_consistency_results,
            )
            _style_signal_results = self._clone_validation_results_for_advisory(validation_results)
            futures[executor.submit(self._advisory_style_signals, candidates, _style_signal_results, next_ep)] = (
                "StyleSignal",
                _style_signal_results,
            )

            for future in as_completed(futures, timeout=300):
                _name, _local_results = futures[future]
                try:
                    result = future.result(timeout=60)
                    if _local_results is not None:
                        self._merge_advisory_validation_results(validation_results, _local_results)
                    if result:
                        _advisory_parts.extend(result)
                        _advisory_per_type[_name] = list(result)
                        logging.debug("[Advisory] %s 완료 (%d건)", _name, len(result))
                except Exception as e:
                    logging.warning("[Advisory] %s 실패 (비치명): %s", _name, e)
        except FuturesTimeoutError as timeout_err:
            logging.warning("[Advisory] 병렬 실행 타임아웃 — 미완료 future 취소 후 계속 진행: %s", timeout_err)
        finally:
            for future in futures:
                if not future.done():
                    future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)

        if _advisory_parts:
            self.ctx.ui.log(
                f"      ✅ Advisory 체인 완료 — {len(_advisory_parts)}건 경고",
                stage="stage4",
                component="advisory_chain",
                ep_num=next_ep,
                round_num=_round_num,
                event_kind="result",
                meta={"warning_count": len(_advisory_parts)},
            )
            for _adv_type, _adv_lines in sorted(_advisory_per_type.items()):
                self.ctx.ui.log(
                    f"         [{_adv_type}] {len(_adv_lines)}건",
                    stage="stage4",
                    component="advisory_chain",
                    ep_num=next_ep,
                    round_num=_round_num,
                    event_kind="detail",
                )
                for _adv_line in _adv_lines:
                    self.ctx.ui.log(
                        f"            {_adv_line}",
                        stage="stage4",
                        component="advisory_chain",
                        ep_num=next_ep,
                        round_num=_round_num,
                        event_kind="detail",
                    )
        else:
            self.ctx.ui.log(
                "      ✅ Advisory 체인 완료 — 경고 없음",
                stage="stage4",
                component="advisory_chain",
                ep_num=next_ep,
                round_num=_round_num,
                event_kind="result",
                meta={"warning_count": 0},
            )
        return _advisory_parts

    # ── [TF-50] Advisory private methods ──────────────────────────────

    def _advisory_truth_gate(self, candidates: list[dict], validation_results: list[dict], next_ep: int) -> list[str]:
        """[TF-50] TruthGate advisory — 후보 원고별 사실 검증."""
        try:
            from modules.core.truth_gate import TruthGate as _TruthGate

            _tg = _TruthGate(
                world_state=getattr(self.ctx, "world_state", None),
                fact_ledger=getattr(self.ctx, "fact_ledger", None),
                llm_ask=self._truth_gate_llm_ask,
            )
            _npc_reg = getattr(getattr(self.ctx, "state_tracker", None), "npc_registry", {}) or {}
            _tg_warnings_all: list[dict] = []
            for _ci, _cand in enumerate(candidates):
                _ms = _cand.get("manuscript", "")
                if not _ms:
                    continue
                _tg_result = _tg.validate(
                    manuscript=_ms,
                    state_updates=_cand.get("state_updates") or {},
                    npc_registry=_npc_reg,
                )
                if _tg_result.get("structured_warnings"):
                    if _ci < len(validation_results) and isinstance(validation_results[_ci], dict):
                        validation_results[_ci].setdefault("truth_gate_warnings", _tg_result["structured_warnings"])
                    _cand_label = ["A", "B", "C"][_ci] if _ci < 3 else str(_ci + 1)
                    for _sw in _tg_result["structured_warnings"]:
                        _sw["text"] = f"[\ud6c4\ubcf4 {_cand_label}] {_sw.get('text', '')}"
                    _tg_warnings_all.extend(_tg_result["structured_warnings"])
            if _tg_warnings_all:
                _tg_lines = ["[TruthGate Advisory \u2014 CRITICAL \uacbd\uace0 \uc2dc \ubc18\ub4dc\uc2dc REJECT]"]
                for _w in _tg_warnings_all:
                    _tg_lines.append(f"- [{_w.get('severity', '?')}] {_w.get('text', '')}")
                logging.info("[TruthGate\u2192Director] %d\uac1c \uacbd\uace0 \uc804\ub2ec", len(_tg_warnings_all))
                return ["\n".join(_tg_lines)]
        except (AttributeError, TypeError, ValueError, RuntimeError) as _tg_err:
            logging.warning("[Phase4-Gate] TruthGate advisory \uc2e4\ud328 (\ube44\uce58\uba85): %s", str(_tg_err)[:80])
        return []

    @staticmethod
    def _extract_npc_drift_attr_value(raw) -> str:
        if isinstance(raw, dict):
            raw = raw.get("value", raw)
        return str(raw or "").strip()

    def _build_npc_drift_snapshots(self, base_snapshots: dict | None) -> dict:
        """Build a read-only advisory view with fresher runtime role signals."""
        merged = copy.deepcopy(base_snapshots or {})
        _npc_reg = getattr(getattr(self.ctx, "state_tracker", None), "npc_registry", {}) or {}
        if not isinstance(_npc_reg, dict):
            return merged

        for _name, _npc_info in _npc_reg.items():
            if not _name or not isinstance(_npc_info, dict):
                continue
            _snap = merged.setdefault(
                _name,
                {
                    "role": "",
                    "role_at_intro": "",
                    "authoritative_role": "",
                    "authoritative_role_source": "",
                    "first_seen_ep": 0,
                    "known_attrs": {},
                },
            )
            _known_attrs = _snap.setdefault("known_attrs", {})
            _existing_position = self._extract_npc_drift_attr_value(_known_attrs.get("position"))
            _registry_position = str(_npc_info.get("position", "") or "").strip()
            _registry_role = str(
                _npc_info.get("role") or _npc_info.get("public_role") or _npc_info.get("job") or ""
            ).strip()

            if _registry_position and not _existing_position:
                _known_attrs["position"] = {"value": _registry_position, "prev": "", "changed_ep": 0}
            if _registry_role and not str(_snap.get("role", "") or "").strip():
                _snap["role"] = _registry_role

            _existing_authoritative_role = str(_snap.get("authoritative_role", "") or "").strip()
            _existing_authority_source = str(_snap.get("authoritative_role_source", "") or "").strip()
            if _registry_position and (
                not _existing_authoritative_role or _existing_authority_source in {"", "role", "role_at_intro"}
            ):
                _snap["authoritative_role"] = _registry_position
                _snap["authoritative_role_source"] = "state_tracker.position"
            elif _registry_role and (
                not _existing_authoritative_role or _existing_authority_source in {"", "role_at_intro"}
            ):
                _snap["authoritative_role"] = _registry_role
                _snap["authoritative_role_source"] = "state_tracker.role"

        return merged

    def _advisory_npc_drift(self, candidates: list[dict], validation_results: list[dict], next_ep: int) -> list[str]:
        """[TF-50] NpcDriftAdvisor — 원고 내 NPC 속성 표류 advisory."""
        try:
            from modules.core.npc_drift_advisor import NpcDriftAdvisor as _NpcDriftAdvisor

            _ws = getattr(self.ctx, "world_state", None)
            _base_npc_snaps = {}
            if _ws and hasattr(_ws, "get_npc_role_snapshot"):
                _base_npc_snaps = _ws.get_npc_role_snapshot() or {}
            _npc_snaps = self._build_npc_drift_snapshots(_base_npc_snaps)
            if _npc_snaps:
                _drift_advisor = _NpcDriftAdvisor(llm_ask=self._truth_gate_llm_ask)
                _drift_all = []
                for _ci, _cand in enumerate(candidates):
                    _ms = _cand.get("manuscript", "")
                    if not _ms:
                        continue
                    _drifts = _drift_advisor.check(
                        manuscript=_ms,
                        npc_snapshots=_npc_snaps,
                        ep_num=next_ep,
                        max_npcs=8,
                    )
                    if _drifts:
                        for _d in _drifts:
                            _d["_cand_idx"] = _ci
                        _drift_all.extend(_drifts)
                        self._last_advisory_metadata.setdefault("npc_drift", []).extend(copy.deepcopy(_drifts))
                        if _ci < len(validation_results) and isinstance(validation_results[_ci], dict):
                            validation_results[_ci].setdefault("npc_drift_warnings", _drifts)
                if _drift_all:
                    _drift_lines = [
                        "[NpcDriftAdvisor \u2014 NPC \uc18d\uc131 \ud45c\ub958 \uac10\uc9c0, \ucc38\uace0\uc6a9 advisory \u2014 \ucd5c\uc885 \ud310\ub2e8\uc740 Director]"
                    ]
                    for _d in _drift_all:
                        _cl = (
                            ["A", "B", "C"][_d.get("_cand_idx", 0)]
                            if _d.get("_cand_idx", 0) < 3
                            else str(_d.get("_cand_idx", 0) + 1)
                        )
                        _drift_lines.append(
                            f"- [\ud6c4\ubcf4 {_cl}][MAJOR] NPC '{_d.get('npc', '')}' {_d.get('field', '')}: "
                            f"\uae30\ub300='{_d.get('expected', '')}' \u2192 \uc6d0\uace0='{_d.get('found_in_ms', '')}'"
                        )
                    logging.info(
                        "[NpcDriftAdvisor\u2192Director] %d\uac74 \ud45c\ub958 \uac10\uc9c0 \uc804\ub2ec",
                        len(_drift_all),
                    )
                    return ["\n".join(_drift_lines)]
        except (AttributeError, TypeError, ValueError, RuntimeError, OSError) as _drift_err:
            logging.warning("[LM-B] NpcDriftAdvisor \uc2e4\ud328 (\ube44\uce58\uba85): %s", str(_drift_err)[:80])
        return []

    def _advisory_numeric_drift(self, next_ep: int) -> list[str]:
        """[TF-50] NumericDriftAdvisor — 5화 단위 수치 누적 표류 advisory."""
        if next_ep % 5 != 0:
            return []
        try:
            from modules.core.numeric_drift_advisor import NumericDriftAdvisor as _NumDriftAdvisor

            _fl = getattr(self.ctx, "fact_ledger", None)
            if _fl:
                _nums = _fl.get_numbers() or {}
                if _nums:
                    _num_advisor = _NumDriftAdvisor(llm_ask=self._truth_gate_llm_ask)
                    _num_drifts = _num_advisor.check(numbers=_nums, ep_num=next_ep)
                    if _num_drifts:
                        _nd_lines = [
                            "[NumericDriftAdvisor \u2014 \uc218\uce58 \ub204\uc801 \ud45c\ub958 \uac10\uc9c0, \ucc38\uace0\uc6a9 advisory \u2014 \ucd5c\uc885 \ud310\ub2e8\uc740 Director]"
                        ]
                        for _nd in _num_drifts:
                            _nd_lines.append(f"- [MAJOR] '{_nd.get('key', '')}': {_nd.get('issue', '')}")
                        logging.info(
                            "[NumericDriftAdvisor\u2192Director] %d\uac74 \uc218\uce58 \ud45c\ub958 \uac10\uc9c0",
                            len(_num_drifts),
                        )
                        return ["\n".join(_nd_lines)]
        except (AttributeError, TypeError, ValueError, RuntimeError, OSError) as _nd_err:
            logging.warning("[LM-C] NumericDriftAdvisor \uc2e4\ud328 (\ube44\uce58\uba85): %s", str(_nd_err)[:80])
        return []

    def _advisory_flashback(self, candidates: list[dict], next_ep: int) -> list[str]:
        """[TF-50] FlashbackVerifier — 회상/플래시백 오염 advisory."""
        try:
            import re as _re_mod

            from modules.core.flashback_verifier import FlashbackVerifier as _FbVerifier

            _fb_verifier = _FbVerifier(llm_ask=self._truth_gate_llm_ask)
            _fb_all = []
            for _ci, _cand in enumerate(candidates):
                _ms = _cand.get("manuscript", "")
                if not _ms:
                    continue
                _flashbacks = _fb_verifier.detect_flashbacks(_ms)
                if not _flashbacks:
                    continue
                _mem = getattr(self.ctx, "memory", None)
                _ref_ctx = ""
                _ms_snippets = ""
                if _mem and hasattr(_mem, "retrieve_high_res_context"):
                    _fb_queries = [fb["text"][:200] for fb in _flashbacks[:3]]
                    _ref_parts = []
                    _seen_eps: set[int] = set()
                    for _q in _fb_queries:
                        _r = _mem.retrieve_high_res_context(_q, next_ep, n_results=2)
                        if _r:
                            _ref_parts.append(_r)
                            for _ep_match in _re_mod.finditer(r"\[(?:\uc81c\s*)?(\d+)\s*\ud654", _r):
                                _seen_eps.add(int(_ep_match.group(1)))
                    _ref_ctx = "\n\n".join(_ref_parts)
                    if _seen_eps and hasattr(_mem, "fetch_manuscript_snippet"):
                        _snip_parts = []
                        for _ep_n in sorted(_seen_eps)[:3]:
                            _snip = _mem.fetch_manuscript_snippet(_ep_n, max_chars=500)
                            if _snip:
                                _snip_parts.append(f"[\uc81c {_ep_n}\ud654 \uc6d0\ubb38]\n{_snip}")
                        _ms_snippets = "\n\n".join(_snip_parts)
                if not _ref_ctx:
                    continue
                _fb_warns = _fb_verifier.check(
                    _ms, ep_num=next_ep, reference_context=_ref_ctx, manuscript_snippets=_ms_snippets
                )
                if _fb_warns:
                    for _fw in _fb_warns:
                        _fw["_cand_idx"] = _ci
                    self._last_advisory_metadata.setdefault("flashback", []).extend(copy.deepcopy(_fb_warns))
                    _fb_all.extend(_fb_warns)
            if _fb_all:
                _fb_lines = [
                    "[FlashbackVerifier \u2014 \ud68c\uc0c1 \uc624\uc5fc \uac10\uc9c0, \ucc38\uace0\uc6a9 advisory \u2014 \ucd5c\uc885 \ud310\ub2e8\uc740 Director]"
                ]
                for _fw in _fb_all:
                    _cl = (
                        ["A", "B", "C"][_fw.get("_cand_idx", 0)]
                        if _fw.get("_cand_idx", 0) < 3
                        else str(_fw.get("_cand_idx", 0) + 1)
                    )
                    _fb_lines.append(f"- [\ud6c4\ubcf4 {_cl}][MAJOR] '{_fw.get('marker', '')}': {_fw.get('issue', '')}")
                logging.info(
                    "[FlashbackVerifier\u2192Director] %d\uac74 \ud68c\uc0c1 \uc624\uc5fc \uac10\uc9c0", len(_fb_all)
                )
                return ["\n".join(_fb_lines)]
        except (AttributeError, TypeError, ValueError, RuntimeError, OSError) as _fb_err:
            logging.warning("[LM-E] FlashbackVerifier \uc2e4\ud328 (\ube44\uce58\uba85): %s", str(_fb_err)[:80])
        return []

    def _advisory_info_paradox(self, candidates: list[dict], next_ep: int, genre_name: str) -> list[str]:
        """[TF-50] InfoParadoxChecker — 정보 역설 advisory (1인칭 전용)."""
        try:
            _mb = getattr(self.ctx.current_project, "master_bible", None) or {}
            _mb_root = _mb.get("MasterBible", _mb)
            _pov = _mb_root.get("protagonist_config", {}).get("pov", "")

            if _pov == "1\uc778\uce6d":
                from modules.core.constants import HUDKeys
                from modules.core.info_paradox_checker import InfoParadoxChecker as _IpChecker

                _proto_name = HUDKeys.get_protagonist_name(_mb_root, genre_name)
                _db = getattr(self.ctx.current_project, "db", None)

                # [TF-51] 회귀자/장르 예외 전달
                _incarnation_type = _mb_root.get("protagonist_config", {}).get("incarnation_type", "")
                if _db and _proto_name and _proto_name != "\uc8fc\uc778\uacf5":
                    _knowledge_summary = _IpChecker.build_knowledge_summary(_db, next_ep, _proto_name)
                    if _knowledge_summary:
                        _ip_checker = _IpChecker(llm_ask=self._truth_gate_llm_ask)
                        _ip_all = []
                        for _ci, _cand in enumerate(candidates):
                            _ms = _cand.get("manuscript", "")
                            if not _ms:
                                continue
                            _ip_warns = _ip_checker.check(
                                _ms,
                                ep_num=next_ep,
                                pov_character=_proto_name,
                                knowledge_summary=_knowledge_summary,
                                incarnation_type=_incarnation_type,
                                genre_name=genre_name,
                            )
                            if _ip_warns:
                                for _ipw in _ip_warns:
                                    _ipw["_cand_idx"] = _ci
                                _ip_all.extend(_ip_warns)
                        if _ip_all:
                            _ip_lines = [
                                "[InfoParadoxChecker \u2014 \uc815\ubcf4 \uc5ed\uc124 \uac10\uc9c0, \ucc38\uace0\uc6a9 advisory \u2014 \ucd5c\uc885 \ud310\ub2e8\uc740 Director]"
                            ]
                            for _ip in _ip_all:
                                _cl = (
                                    ["A", "B", "C"][_ip.get("_cand_idx", 0)]
                                    if _ip.get("_cand_idx", 0) < 3
                                    else str(_ip.get("_cand_idx", 0) + 1)
                                )
                                _ip_lines.append(
                                    f"- [\ud6c4\ubcf4 {_cl}][MAJOR] '{_ip.get('info_used', '')}': {_ip.get('why_paradox', '')}"
                                )
                            logging.info(
                                "[InfoParadoxChecker\u2192Director] %d\uac74 \uc815\ubcf4 \uc5ed\uc124 \uac10\uc9c0",
                                len(_ip_all),
                            )
                            return ["\n".join(_ip_lines)]
        except (AttributeError, TypeError, ValueError, RuntimeError, OSError) as _ip_err:
            logging.warning("[LM-F] InfoParadoxChecker \uc2e4\ud328 (\ube44\uce58\uba85): %s", str(_ip_err)[:80])
        return []

    def _advisory_rel_drift(self, candidates: list[dict], next_ep: int) -> list[str]:
        """[TF-50] RelationshipDriftAdvisor — 관계도 장기 표류 advisory."""
        if next_ep < 5:
            return []
        try:
            _db = getattr(self.ctx.current_project, "db", None)
            if _db and hasattr(_db, "get_all_relationship_pairs_with_history"):
                from modules.core.relationship_drift_advisor import RelationshipDriftAdvisor as _RdAdvisor

                _rel_timeline = _RdAdvisor.build_relationship_timeline(_db)
                if _rel_timeline:
                    _rd_advisor = _RdAdvisor(llm_ask=self._truth_gate_llm_ask)
                    _rd_all = []
                    for _ci, _cand in enumerate(candidates):
                        _ms = _cand.get("manuscript", "")
                        if not _ms:
                            continue
                        _rd_warns = _rd_advisor.check(
                            _ms,
                            ep_num=next_ep,
                            relationship_timeline=_rel_timeline,
                        )
                        if _rd_warns:
                            for _rdw in _rd_warns:
                                _rdw["_cand_idx"] = _ci
                            _rd_all.extend(_rd_warns)
                    if _rd_all:
                        _rd_lines = [
                            "[RelationshipDriftAdvisor \u2014 \uad00\uacc4\ub3c4 \ud45c\ub958 \uac10\uc9c0, \ucc38\uace0\uc6a9 advisory \u2014 \ucd5c\uc885 \ud310\ub2e8\uc740 Director]"
                        ]
                        for _rd in _rd_all:
                            _cl = (
                                ["A", "B", "C"][_rd.get("_cand_idx", 0)]
                                if _rd.get("_cand_idx", 0) < 3
                                else str(_rd.get("_cand_idx", 0) + 1)
                            )
                            _rd_lines.append(
                                f"- [\ud6c4\ubcf4 {_cl}][MAJOR] '{_rd.get('npc_pair', '')}': {_rd.get('why_drift', '')}"
                            )
                        logging.info(
                            "[RelationshipDriftAdvisor\u2192Director] %d\uac74 \uad00\uacc4 \ud45c\ub958 \uac10\uc9c0",
                            len(_rd_all),
                        )
                        return ["\n".join(_rd_lines)]
        except (AttributeError, TypeError, ValueError, RuntimeError, OSError) as _rd_err:
            logging.warning("[LM-D] RelationshipDriftAdvisor \uc2e4\ud328 (\ube44\uce58\uba85): %s", str(_rd_err)[:80])
        return []

    def _advisory_long_term_rep(self, candidates: list[dict], next_ep: int) -> list[str]:
        """[TF-50] LongTermRepetitionAdvisor — 20화 이상 장기 반복 패턴 감지."""
        if next_ep < 20:
            return []
        try:
            from modules.core.long_term_repetition_advisor import LongTermRepetitionAdvisor as _LtrAdvisor

            _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
            if _db is not None:
                _pattern_summary = _LtrAdvisor.build_pattern_summary(_db, next_ep, lookback=20)
                if _pattern_summary:
                    _ltr_advisor = _LtrAdvisor(llm_ask=self._truth_gate_llm_ask)
                    _ltr_all: list[dict] = []
                    for _ci, _cand in enumerate(candidates):
                        _ms = _cand.get("manuscript", "") if isinstance(_cand, dict) else str(_cand)
                        if _ms:
                            _ltr_results = _ltr_advisor.check(_ms, ep_num=next_ep, pattern_summary=_pattern_summary)
                            for _lr in _ltr_results:
                                _lr["_cand_idx"] = _ci
                            _ltr_all.extend(_ltr_results)
                    if _ltr_all:
                        _ltr_lines = [
                            f"[P1-5 \uc7a5\uae30 \ubc18\ubcf5 \uac10\uc9c0 \u2014 {len(_ltr_all)}\uac74, \ucc38\uace0\uc6a9 advisory \u2014 \ucd5c\uc885 \ud310\ub2e8\uc740 Director]"
                        ]
                        for _lr in _ltr_all:
                            _cl = (
                                ["A", "B", "C"][_lr.get("_cand_idx", 0)]
                                if _lr.get("_cand_idx", 0) < 3
                                else str(_lr.get("_cand_idx", 0) + 1)
                            )
                            _ltr_lines.append(
                                f"- [\ud6c4\ubcf4 {_cl}][MAJOR] '{_lr.get('pattern', '')}': {_lr.get('issue', '')}"
                            )
                        logging.info(
                            "[LongTermRepetitionAdvisor\u2192Director] %d\uac74 \uc7a5\uae30 \ubc18\ubcf5 \uac10\uc9c0",
                            len(_ltr_all),
                        )
                        return ["\n".join(_ltr_lines)]
        except (AttributeError, TypeError, ValueError, RuntimeError, OSError) as _ltr_err:
            logging.warning(
                "[P1-5] LongTermRepetitionAdvisor \uc2e4\ud328 (\ube44\uce58\uba85): %s", str(_ltr_err)[:80]
            )
        return []

    def _advisory_numeric_consistency(
        self,
        candidates: list[dict],
        validation_results: list[dict],
        next_ep: int,
    ) -> list[str]:
        """[NC-1] NumericConsistencyChecker — Python-only 수치 정합성 advisory."""
        try:
            from modules.core.numeric_consistency_checker import NumericConsistencyChecker

            _fl = getattr(self.ctx, "fact_ledger", None)
            _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
            _ws = getattr(self.ctx, "world_state", None)

            checker = NumericConsistencyChecker(fact_ledger=_fl, db=_db, world_state=_ws)

            # 직전 화 원고
            _prev_ms = None
            if _db and next_ep > 1:
                _prev_row = _db.get_manuscript(next_ep - 1)
                if _prev_row:
                    _prev_ms = _prev_row.get("manuscript", "") or _prev_row.get("text", "")

            _nc_all: list[dict] = []
            for _ci, _cand in enumerate(candidates):
                _ms = _cand.get("manuscript", "") if isinstance(_cand, dict) else ""
                if not _ms:
                    continue
                _su = _cand.get("state_updates") or {} if isinstance(_cand, dict) else {}
                _warns = checker.check(
                    _ms,
                    next_ep,
                    state_updates=_su,
                    prev_manuscript=_prev_ms,
                )
                if _warns and _ci < len(validation_results) and isinstance(validation_results[_ci], dict):
                    validation_results[_ci].setdefault("numeric_consistency_warnings", []).extend(copy.deepcopy(_warns))
                for _w in _warns:
                    _w["_cand_idx"] = _ci
                _nc_all.extend(_warns)

            if _nc_all:
                _nc_lines = [
                    "[NumericConsistency — Python 수치 검증 결과. 각 항목에 대해 numeric_consistency_review에서 AGREE/DISMISS 판정 필수]"
                ]
                for _wi, _w in enumerate(_nc_all, 1):
                    _cl = (
                        ["A", "B", "C"][_w.get("_cand_idx", 0)]
                        if _w.get("_cand_idx", 0) < 3
                        else str(_w.get("_cand_idx", 0) + 1)
                    )
                    _sev = _w.get("severity", "MAJOR")
                    _category = str(_w.get("category") or _w.get("contradiction_type") or "").strip()
                    _category_tag = f"[{_category}]" if _category else ""
                    _nc_lines.append(f"- [NC-{_wi}][후보 {_cl}][{_sev}]{_category_tag} {_w.get('text', '')}")
                logging.info(
                    "[NumericConsistency→Director] %d건 수치 정합성 경고",
                    len(_nc_all),
                )
                return ["\n".join(_nc_lines)]
        except (AttributeError, TypeError, ValueError, RuntimeError, OSError) as _nc_err:
            logging.warning("[NC-1] NumericConsistencyChecker 실패 (비치명): %s", str(_nc_err)[:80])
        return []

    def _advisory_style_signals(
        self,
        candidates: list[dict],
        validation_results: list[dict],
        next_ep: int,
    ) -> list[str]:
        """[TF-T1] StyleSignalAdvisor — ai_slop/CED/style-target drift advisory."""
        try:
            from modules.core.project_support import resolve_style_dialogue_ratio_target
            from modules.core.quality_signal_metrics import compute_quality_signal_bundle
            from modules.validation.dialogue_utils import count_dialogue_characters

            _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
            _summary = {}
            if _db and hasattr(_db, "get_quality_signal_summary"):
                _summary = _db.get_quality_signal_summary(before_ep=next_ep, lookback=5) or {}
            _signals = (_summary.get("signals") or {}) if isinstance(_summary, dict) else {}
            _ai_median = float((_signals.get("ai_slop") or {}).get("median", 0.0) or 0.0)
            _ced_median = float((_signals.get("ced") or {}).get("median", 0.0) or 0.0)
            _target_dialogue_ratio = resolve_style_dialogue_ratio_target(
                project=getattr(self.ctx, "current_project", None)
            )

            _advisory_lines = [
                "[StyleSignalAdvisor — ai_slop/CED/style-target drift, advisory only — 최종 판단은 Director]"
            ]
            _hit_count = 0

            for _ci, _cand in enumerate(candidates):
                _ms = _cand.get("manuscript", "") if isinstance(_cand, dict) else ""
                if not _ms:
                    continue

                _vr = (
                    validation_results[_ci]
                    if _ci < len(validation_results) and isinstance(validation_results[_ci], dict)
                    else {}
                )
                _warning_count = int(_vr.get("warning_count", 0) or 0) if isinstance(_vr, dict) else 0
                _bundle = compute_quality_signal_bundle(_ms, warning_count=_warning_count)
                _candidate_lines: list[str] = []
                _candidate_label = ["A", "B", "C"][_ci] if _ci < 3 else str(_ci + 1)

                _ai_score = float(_bundle.get("ai_slop_score", 0.0) or 0.0)
                _ai_hits = [item for item in (_bundle.get("ai_slop_hits") or []) if isinstance(item, dict)]
                _ai_total_hits = sum(max(0, int(item.get("count", 0) or 0)) for item in _ai_hits)
                _ai_threshold = max(0.6, _ai_median * 1.15 if _ai_median > 0 else 0.6)
                if _ai_score >= _ai_threshold or _ai_total_hits >= 3:
                    _hit_preview = ", ".join(
                        f"{str(item.get('pattern', '') or '')}x{int(item.get('count', 0) or 0)}"
                        for item in _ai_hits[:3]
                    )
                    if _ai_median > 0:
                        _candidate_lines.append(
                            f"ai_slop score {_ai_score:.2f} (recent median {_ai_median:.2f})"
                            + (f" / hits={_hit_preview}" if _hit_preview else "")
                        )
                    else:
                        _candidate_lines.append(
                            f"ai_slop score {_ai_score:.2f}" + (f" / hits={_hit_preview}" if _hit_preview else "")
                        )

                _ced_score = float(_bundle.get("ced_score", 0.0) or 0.0)
                _ced_threshold = max(1.0, _ced_median * 1.15 if _ced_median > 0 else 1.0)
                if _ced_score >= _ced_threshold:
                    if _ced_median > 0:
                        _candidate_lines.append(
                            f"ced_score {_ced_score:.2f} (recent median {_ced_median:.2f}, python warnings {_warning_count}건)"
                        )
                    else:
                        _candidate_lines.append(f"ced_score {_ced_score:.2f} (python warnings {_warning_count}건)")

                if _target_dialogue_ratio is not None and len(_ms) >= 1000:
                    _dialogue_ratio = count_dialogue_characters(_ms) / max(len(_ms), 1)
                    if _dialogue_ratio < _target_dialogue_ratio - 0.08:
                        _candidate_lines.append(
                            f"dialogue_ratio {_dialogue_ratio:.0%} < style target {_target_dialogue_ratio:.0%}"
                        )
                    elif _dialogue_ratio > _target_dialogue_ratio + 0.12:
                        _candidate_lines.append(
                            f"dialogue_ratio {_dialogue_ratio:.0%} > style target {_target_dialogue_ratio:.0%}"
                        )

                if _candidate_lines:
                    _hit_count += len(_candidate_lines)
                    _advisory_lines.extend(f"- [후보 {_candidate_label}] {line}" for line in _candidate_lines)
                    if isinstance(_vr, dict):
                        _vr["quality_signal_warnings"] = list(_candidate_lines)

            if _hit_count:
                logging.info("[StyleSignalAdvisor→Director] %d건 style/core 경고 전달", _hit_count)
                return ["\n".join(_advisory_lines)]
        except (AttributeError, TypeError, ValueError, RuntimeError, OSError) as _sig_err:
            logging.warning("[TF-T1] StyleSignalAdvisor 실패 (비치명): %s", str(_sig_err)[:80])
        return []

    # ── [TF-32] PASS_WITH_FIX helpers ──────────────────────────────

    def _extract_fix_feedback(self, director_result: dict) -> str:
        """[TF-32] Director 결과에서 수정 피드백 추출."""
        if not isinstance(director_result, dict):
            return ""

        parts: list[str] = []
        fix_pack = self._normalize_fix_pack(director_result.get("fix_pack"))
        if fix_pack:
            fix_pack_lines = []
            target_kind = str(fix_pack.get("target_kind", "") or "").strip()
            if target_kind:
                fix_pack_lines.append(f"target_kind={target_kind}")
            provenance = str(fix_pack.get("provenance", "") or "").strip()
            if provenance:
                fix_pack_lines.append(f"provenance={provenance}")
            provenance_sources = [
                str(item).strip() for item in (fix_pack.get("provenance_sources") or []) if str(item).strip()
            ]
            if provenance_sources:
                fix_pack_lines.append("provenance_sources=" + ", ".join(provenance_sources))
            patch_targets = [str(item).strip() for item in (fix_pack.get("patch_targets") or []) if str(item).strip()]
            if patch_targets:
                fix_pack_lines.append("patch_targets=" + ", ".join(patch_targets))
            must_fix = [str(item).strip() for item in (fix_pack.get("must_fix") or []) if str(item).strip()]
            if must_fix:
                fix_pack_lines.append("must_fix:\n" + "\n".join(f"- {item}" for item in must_fix))
            do_not_regress = [str(item).strip() for item in (fix_pack.get("do_not_regress") or []) if str(item).strip()]
            if do_not_regress:
                fix_pack_lines.append("do_not_regress:\n" + "\n".join(f"- {item}" for item in do_not_regress))
            success_condition = str(fix_pack.get("success_condition", "") or "").strip()
            if success_condition:
                fix_pack_lines.append("success_condition=" + success_condition)
            evidence_summary = str(fix_pack.get("evidence_summary", "") or "").strip()
            if evidence_summary:
                fix_pack_lines.append("evidence_summary=" + evidence_summary)
            if fix_pack_lines:
                parts.append("[Fix Pack]\n" + "\n".join(fix_pack_lines))

        action_items = [str(a).strip() for a in (director_result.get("action_items") or []) if str(a).strip()]
        if action_items:
            parts.append("[핵심 수정 지시]\n" + "\n".join(action_items))

        fix_scope_reasoning = str(director_result.get("fix_scope_reasoning", "") or "").strip()
        if fix_scope_reasoning:
            parts.append("[수정 범위 근거]\n" + fix_scope_reasoning)

        feedback = director_result.get("feedback") or {}
        if isinstance(feedback, dict):
            issues = [str(i).strip() for i in (feedback.get("issues") or []) if str(i).strip()]
            non_review_issues = [item for item in issues if "[자유 리뷰]" not in item]
            if non_review_issues:
                parts.append("[보조 이슈]\n" + "\n".join(non_review_issues))

        open_review = str(director_result.get("open_review", "") or "").strip()
        if open_review and open_review not in ("특이사항 없음", "없음"):
            parts.append("[Director 자유 리뷰]\n" + open_review)
        contradiction_detail_lines = self._compact_contradiction_detail_lines(
            director_result.get("contradiction_details"),
            max_items=None,
            line_limit=180,
        )
        if contradiction_detail_lines:
            parts.append("[모순 세부]\n" + "\n".join(contradiction_detail_lines))

        deduped: list[str] = []
        seen: set[str] = set()
        for part in parts:
            normalized = part.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                deduped.append(normalized)
        return "\n\n".join(deduped)

    @staticmethod
    def _summarize_patch_provenance(
        director_result: dict | None,
        feedback_text: str,
        patch_trace: dict | None,
    ) -> str:
        if not isinstance(director_result, dict):
            director_result = {}
        patch_trace = patch_trace if isinstance(patch_trace, dict) else {}

        summary_parts: list[str] = []
        fix_scope = str(director_result.get("fix_scope", "") or "").strip()
        if fix_scope:
            summary_parts.append(f"scope={fix_scope}")
        fix_pack = Stage4InterviewRound._normalize_fix_pack(director_result.get("fix_pack"))
        target_kind = str(fix_pack.get("target_kind", "") or "").strip()
        if target_kind:
            summary_parts.append(f"target_kind={target_kind}")
        fix_scope_reasoning = str(director_result.get("fix_scope_reasoning", "") or "").strip()
        if fix_scope_reasoning:
            summary_parts.append(f"reason={fix_scope_reasoning}")
        open_review = str(director_result.get("open_review", "") or "").strip()
        if open_review and open_review not in ("특이사항 없음", "없음"):
            summary_parts.append(f"review={open_review}")
        compact_feedback = " ".join(str(feedback_text or "").split())
        if compact_feedback:
            summary_parts.append(f"feedback={compact_feedback}")
        patch_targets = [str(item).strip() for item in (patch_trace.get("patch_targets") or []) if str(item).strip()]
        if not patch_targets:
            patch_targets = [str(item).strip() for item in (fix_pack.get("patch_targets") or []) if str(item).strip()]
        if patch_targets:
            summary_parts.append(f"targets={' / '.join(patch_targets)}")
        patch_strategy = str(patch_trace.get("patch_strategy", "") or "").strip()
        if patch_strategy:
            summary_parts.append(f"strategy={patch_strategy}")
        if patch_trace.get("change_ratio") is not None:
            try:
                summary_parts.append(f"change_ratio={float(patch_trace['change_ratio']):.1%}")
            except (TypeError, ValueError):
                pass
        return " | ".join(summary_parts)

    def _resolve_stage4_patch_contract_payloads(
        self,
        *,
        director_result: dict | None,
        patch_trace: dict | None,
    ) -> tuple[dict[str, object], dict[str, object]]:
        fix_pack_payload = self._build_fix_pack_payload(director_result)
        trace_payload = dict(patch_trace or {})
        if not trace_payload and not fix_pack_payload:
            return {}, fix_pack_payload

        default_target_kind = str(trace_payload.get("target_kind") or fix_pack_payload.get("target_kind") or "").strip()
        patch_targets, patch_target_records = normalize_patch_target_records(
            trace_payload.get("patch_target_records")
            or fix_pack_payload.get("patch_target_records")
            or trace_payload.get("patch_targets")
            or fix_pack_payload.get("patch_targets"),
            stage="stage4",
            container_kind="manuscript",
            default_target_kind=default_target_kind,
            limit=6,
        )
        if not default_target_kind:
            for patch_target_record in patch_target_records:
                if not isinstance(patch_target_record, dict):
                    continue
                record_target_kind = str(patch_target_record.get("target_kind") or "").strip()
                if record_target_kind:
                    default_target_kind = record_target_kind
                    break
        if patch_targets:
            trace_payload["patch_targets"] = patch_targets
            if not fix_pack_payload.get("patch_targets"):
                fix_pack_payload["patch_targets"] = list(patch_targets)
        if patch_target_records:
            trace_payload["patch_target_records"] = patch_target_records
            fix_pack_payload["patch_target_records"] = list(patch_target_records)
        if default_target_kind:
            trace_payload["target_kind"] = default_target_kind
            if not str(fix_pack_payload.get("target_kind") or "").strip():
                fix_pack_payload["target_kind"] = default_target_kind

        patch_round = trace_payload.get("patch_round")
        try:
            normalized_patch_round = int(patch_round or 0)
        except (TypeError, ValueError):
            normalized_patch_round = 0
        if normalized_patch_round > 0:
            trace_payload["patch_round"] = normalized_patch_round

        normalized_guard_result = normalize_guard_result(trace_payload.get("guard_result"))
        if normalized_guard_result:
            trace_payload["guard_result"] = normalized_guard_result

        normalized_repair_trace = normalize_repair_trace_entries(
            trace_payload.get("repair_trace"),
            default_target_records=patch_target_records,
            default_target_kind=default_target_kind,
            guard_result=normalized_guard_result,
        )
        if normalized_repair_trace:
            trace_payload["repair_trace"] = normalized_repair_trace

        partial_fix_eval_source = (
            trace_payload.get("partial_fix_eval") if isinstance(trace_payload.get("partial_fix_eval"), dict) else {}
        )
        partial_fix_eval = build_partial_fix_eval(
            patch_round=partial_fix_eval_source.get("patch_round", trace_payload.get("patch_round")),
            is_patch_attempt=partial_fix_eval_source.get("is_patch_attempt", bool(trace_payload)),
            patch_target_records=patch_target_records,
            target_kind=partial_fix_eval_source.get("target_kind", default_target_kind),
            fallback_reason=partial_fix_eval_source.get(
                "fallback_reason",
                str(
                    trace_payload.get("fallback_reason") or normalized_guard_result.get("failure_key", "")
                    if normalized_guard_result
                    else trace_payload.get("fallback_reason", "")
                ),
            ),
            must_fix_resolved=partial_fix_eval_source.get("must_fix_resolved"),
            do_not_regress_held=partial_fix_eval_source.get("do_not_regress_held"),
            success_condition_met=partial_fix_eval_source.get("success_condition_met"),
        )
        if partial_fix_eval:
            trace_payload["partial_fix_eval"] = partial_fix_eval

        return trace_payload, fix_pack_payload

    def _build_stage4_patch_advisory_payload(
        self,
        *,
        director_result: dict | None,
        patch_trace: dict | None,
    ) -> dict[str, object]:
        trace_payload, fix_pack_payload = self._resolve_stage4_patch_contract_payloads(
            director_result=director_result,
            patch_trace=patch_trace,
        )
        payload: dict[str, object] = {
            "fix_pack": fix_pack_payload,
        }
        if isinstance(trace_payload.get("partial_fix_eval"), dict):
            payload["partial_fix_eval"] = dict(trace_payload.get("partial_fix_eval") or {})
        if isinstance(trace_payload.get("repair_trace"), list):
            payload["repair_trace"] = list(trace_payload.get("repair_trace") or [])
        return payload

    @staticmethod
    def _build_reaudit_story_context(base_story_context: str, applied_patches: list[str]) -> str:
        story_context = str(base_story_context or "")
        cleaned = [str(item).strip() for item in (applied_patches or []) if str(item or "").strip()]
        if not cleaned:
            return story_context
        patch_block = "[PASS_WITH_FIX 재심사 — 이미 적용된 패치]\n" + "\n".join(f"- {item}" for item in cleaned[-3:])
        if not story_context:
            return patch_block
        return story_context.rstrip() + "\n\n" + patch_block

    def _mark_pass_with_fix_inplace_contract_fail(
        self,
        *,
        current_audit_result: dict | None,
        director_feedback: str,
        patch_trace: dict | None,
        failure_key: str,
        notice: str,
    ) -> tuple[dict, str, dict]:
        updated_result = self._apply_director_gate_update(
            current_audit_result,
            final_verdict="REJECT",
            gate_basis=f"pass_with_fix_inplace_contract_fail_{failure_key}",
            repair_scope="partial",
        )
        updated_result["fix_scope"] = "partial"

        existing_reasoning = str(updated_result.get("fix_scope_reasoning", "") or "").strip()
        if notice not in existing_reasoning:
            updated_result["fix_scope_reasoning"] = (
                f"{existing_reasoning}\n{notice}".strip() if existing_reasoning else notice
            )

        existing_verdict_reason = str(updated_result.get("verdict_reason", "") or "").strip()
        if notice not in existing_verdict_reason:
            updated_result["verdict_reason"] = (
                f"{existing_verdict_reason}\n{notice}".strip() if existing_verdict_reason else notice
            )

        existing_open_review = str(updated_result.get("open_review", "") or "").strip()
        if notice not in existing_open_review:
            updated_result["open_review"] = (
                f"{existing_open_review}\n{notice}".strip() if existing_open_review else notice
            )

        updated_trace = dict(patch_trace or {})
        updated_trace["patch_strategy"] = str(updated_trace.get("patch_strategy", "") or "inplace_patch")
        updated_trace["fallback_reason"] = str(failure_key or "inplace_contract_fail")

        logging.warning("[Lane3 Emergency] %s", notice)
        self.ctx.ui.log(f"   ⚠️ [Lane3 Emergency] {notice}")
        updated_feedback = f"{director_feedback}\n{notice}".strip()
        return updated_result, updated_feedback, updated_trace

    # ── Stage 4 PassRateMonitor 기록 ──────────────────────────────

    # ═══════════════════════════════════════════════════════════════════════
    # Episode log + attempt recording (DB, pass_rate_monitor, JSONL)
    # ═══════════════════════════════════════════════════════════════════════

    def _append_episode_log(
        self,
        *,
        ep_num,
        round_num,
        director_result,
        initial_verdict=None,
        initial_score=None,
        final_verdict=None,
        final_score=None,
        is_patch,
        patch_fallback,
        tot_used,
        mad_used,
        asp_used,
        model,
        reject_bucket="",
        validation_warnings=None,
        final_warnings=None,
        feedback_provenance=None,
        patch_trace=None,
        arc_num=0,
        attempt_key=None,
        candidate_key="",
        content_hash="",
        artifact_path="",
        selection_candidate_key="",
        selection_content_hash="",
        selection_artifact_path="",
        carryover_contracts=None,
        selection_reason="",
        verdict_reason="",
        gate_semantics=None,
        fix_pack=None,
        runtime_advisory="",
        retry_directives="",
    ):
        """[V76] 라운드별 생산 로그를 JSONL로 기록."""
        try:
            import datetime
            import os

            logs_dir = resolve_project_log_dir(getattr(self.ctx, "current_project", None))
            if logs_dir is None:
                logs_dir = Path("projects") / str(self.ctx.current_project.name) / "logs"
            os.makedirs(logs_dir, exist_ok=True)

            _sel_candidate = director_result.get("selected_candidate") or {}
            if not isinstance(_sel_candidate, dict):
                _sel_candidate = {}

            try:
                _initial_score = int(director_result.get("score", 0) if initial_score is None else initial_score)
            except (ValueError, TypeError):
                _initial_score = 0
            try:
                _final_score = int(_initial_score if final_score is None else final_score)
            except (ValueError, TypeError):
                _final_score = _initial_score
            _initial_verdict = str(director_result.get("verdict", "") if initial_verdict is None else initial_verdict)
            _final_verdict = str(_initial_verdict if final_verdict is None else final_verdict)

            _duration_ms = None
            if hasattr(self, "_round_start_ts"):
                try:
                    _duration_ms = int((time.monotonic() - self._round_start_ts) * 1000)
                except Exception:
                    _duration_ms = None
            _candidate_warnings = list(validation_warnings or [])
            _final_warnings = list(final_warnings or [])
            _round_metrics = self._get_round_metrics_delta()
            _selection_reason = str(selection_reason or director_result.get("selection_reason") or "")
            _verdict_reason = str(verdict_reason or director_result.get("verdict_reason") or _selection_reason)
            _gate_semantics = (
                dict(gate_semantics or {})
                if isinstance(gate_semantics, dict)
                else self._build_gate_semantics_payload(director_result)
            )
            _patch_trace = dict(patch_trace or {})
            _contract_source = dict(director_result or {}) if isinstance(director_result, dict) else {}
            if isinstance(fix_pack, dict) and fix_pack:
                _contract_source["fix_pack"] = dict(fix_pack)
            if isinstance(_gate_semantics.get("repair_contract"), dict) and _gate_semantics.get("repair_contract"):
                _contract_source["repair_contract"] = dict(_gate_semantics.get("repair_contract") or {})
            if isinstance(_gate_semantics.get("scope_authority"), dict) and _gate_semantics.get("scope_authority"):
                _contract_source["scope_authority"] = dict(_gate_semantics.get("scope_authority") or {})
            if is_patch or patch_fallback:
                _patch_trace, _fix_pack = self._resolve_stage4_patch_contract_payloads(
                    director_result=_contract_source,
                    patch_trace=_patch_trace,
                )
            else:
                _patch_trace = {}
                _fix_pack = self._build_fix_pack_payload(_contract_source)
            if isinstance(fix_pack, dict) and fix_pack and not _fix_pack:
                _fix_pack = dict(fix_pack)
            _derived_repair_contract = self._build_repair_contract_payload_from_parts(
                gate_semantics=_gate_semantics,
                fix_pack=_fix_pack,
                source=_contract_source,
            )
            _repair_contract = (
                dict(_derived_repair_contract or {}) | dict(_gate_semantics.get("repair_contract") or {})
                if isinstance(_gate_semantics.get("repair_contract"), dict)
                else dict(_derived_repair_contract or {})
            )
            _derived_scope_authority = self._build_scope_authority_payload_from_parts(
                gate_semantics=_gate_semantics,
                source={**_contract_source, "repair_contract": _repair_contract},
            )
            _scope_authority = (
                dict(_derived_scope_authority or {}) | dict(_gate_semantics.get("scope_authority") or {})
                if isinstance(_gate_semantics.get("scope_authority"), dict)
                else dict(_derived_scope_authority or {})
            )
            _feedback_provenance = dict(feedback_provenance or {})
            _normalized_patch_strategy = str(_patch_trace.get("patch_strategy", "") or "").strip()
            if is_patch and not _normalized_patch_strategy:
                _normalized_patch_strategy = "patch_fallback_rewrite" if patch_fallback else "patch_with_feedback"
            if _normalized_patch_strategy and not str(_patch_trace.get("patch_strategy", "") or "").strip():
                _patch_trace["patch_strategy"] = _normalized_patch_strategy
            _patch_targets = _patch_trace.get("patch_targets") or []
            _retry_budget_axes = dict(getattr(self, "_last_retry_budget_axes", {}) or {})
            _session_id = resolve_logging_session_id(getattr(self.ctx, "current_project", None))
            _attempt_key = str(
                attempt_key
                or build_attempt_key(
                    stage=4,
                    ep_num=ep_num,
                    arc_num=arc_num,
                    attempt_num=round_num + 1,
                    session_id=_session_id,
                )
            )
            try:
                _unchanged_ratio = (
                    float(_patch_trace["unchanged_ratio"]) if _patch_trace.get("unchanged_ratio") is not None else None
                )
            except (ValueError, TypeError):
                _unchanged_ratio = None

            entry = {
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "ep": ep_num,
                "round": round_num,
                "ep_attempt_total": round_num + 1,
                "attempt_key": _attempt_key,
                "candidate_key": str(candidate_key or ""),
                "content_hash": str(content_hash or ""),
                "artifact_path": str(artifact_path or ""),
                "selection_candidate_key": str(selection_candidate_key or ""),
                "selection_content_hash": str(selection_content_hash or ""),
                "selection_artifact_path": str(selection_artifact_path or ""),
                "verdict": _initial_verdict,
                "score": _initial_score,
                "initial_verdict": _initial_verdict,
                "initial_score": _initial_score,
                "director_verdict": _gate_semantics.get("director_verdict", _initial_verdict),
                "final_verdict": _final_verdict,
                "final_score": _final_score,
                "gate_basis": _gate_semantics.get("gate_basis", ""),
                "repair_scope": _gate_semantics.get(
                    "repair_scope",
                    self._normalize_repair_scope_value(director_result.get("fix_scope", "")),
                ),
                "fix_scope": str(_scope_authority.get("fix_scope", "") or ""),
                "authoritative_fix_scope": str(_gate_semantics.get("authoritative_fix_scope", "") or ""),
                "selected": director_result.get("selected", ""),
                "strategy": _sel_candidate.get("strategy", "") or _sel_candidate.get("strategy_name", ""),
                "model": model,
                "duration_ms": _duration_ms,
                "round_total_calls": _round_metrics["total_calls"],
                "round_total_tokens": _round_metrics["total_tokens"],
                "round_total_cost_usd": _round_metrics["total_cost_usd"],
                "round_model_breakdown": _round_metrics["model_breakdown"],
                "token_cost": _round_metrics["total_cost_usd"],
                "token_usage": {
                    "total_calls": _round_metrics["total_calls"],
                    "total_tokens": _round_metrics["total_tokens"],
                    "model_breakdown": _round_metrics["model_breakdown"],
                },
                "error_category": director_result.get("error_category", ""),
                "reason": _selection_reason,
                "selection_reason": _selection_reason,
                "verdict_reason": _verdict_reason,
                "action_items": list(director_result.get("action_items") or []),
                "score_breakdown": director_result.get("score_breakdown", {}),
                "open_review": str(director_result.get("open_review") or ""),
                "flags": {
                    "patch_mode": bool(is_patch),
                    "patch_fallback": patch_fallback,
                    "tot": tot_used,
                    "mad": mad_used,
                    "asp": asp_used,
                    "strategy_budget": getattr(self, "_last_strategy_budget", "full"),
                    "strategy_count": getattr(self, "_last_strategy_count", 0),
                    "reject_bucket": reject_bucket,
                    "retry_budget_axes": _retry_budget_axes,
                },
                "patch_trace": {
                    "patch_strategy": _normalized_patch_strategy,
                    "patch_targets": list(_patch_targets),
                    "unchanged_ratio": round(_unchanged_ratio, 4) if _unchanged_ratio is not None else None,
                    "fallback_reason": str(_patch_trace.get("fallback_reason", "") or ""),
                    "focus": str(_patch_trace.get("focus", "") or ""),
                    "structural_attempted": bool(_patch_trace.get("structural_attempted", False)),
                },
                "fix_pack": _fix_pack,
                "repair_contract": _repair_contract,
                "scope_authority": _scope_authority,
                "warnings": (_final_warnings if _final_verdict in ("PASS", "PASS_WITH_FIX") else _candidate_warnings),
                "final_warnings": _final_warnings,
                "candidate_warnings": _candidate_warnings,
                "feedback_provenance": self._build_stage4_feedback_provenance_payload(
                    director_feedback=self._compact_text(
                        _feedback_provenance.get(
                            "director_feedback", _feedback_provenance.get("director_feedback_text", "")
                        ),
                        None,
                    ),
                    runtime_advisory=self._compact_text(
                        runtime_advisory or _feedback_provenance.get("runtime_advisory", ""),
                        None,
                    ),
                    retry_directives=self._compact_text(
                        retry_directives or _feedback_provenance.get("retry_directives", ""),
                        None,
                    ),
                ),
            }
            _scope_violation = _gate_semantics.get("authoritative_fix_scope_violation")
            if isinstance(_scope_violation, dict):
                entry["authoritative_fix_scope_violation"] = _scope_violation
            _strong_advisory = _gate_semantics.get("strong_advisory_escalation")
            if isinstance(_strong_advisory, dict):
                entry["strong_advisory_escalation"] = _strong_advisory
            _verdict_layers = _gate_semantics.get("verdict_layers")
            if isinstance(_verdict_layers, dict):
                entry["verdict_layers"] = _verdict_layers
                entry["downstream_override_applied"] = bool(_verdict_layers.get("downstream_override_applied", False))
                entry["primary_failure_layer"] = str(_verdict_layers.get("primary_failure_layer", "") or "")
            if isinstance(_scope_authority.get("scope_origin"), dict):
                entry["scope_origin"] = dict(_scope_authority.get("scope_origin") or {})
            if str(_patch_trace.get("target_kind", "") or "").strip():
                entry["patch_trace"]["target_kind"] = str(_patch_trace.get("target_kind", "") or "").strip()
            if isinstance(_patch_trace.get("patch_round"), int) and int(_patch_trace.get("patch_round") or 0) > 0:
                entry["patch_trace"]["patch_round"] = int(_patch_trace.get("patch_round") or 0)
            if isinstance(_patch_trace.get("patch_target_records"), list) and _patch_trace.get("patch_target_records"):
                entry["patch_trace"]["patch_target_records"] = list(_patch_trace.get("patch_target_records") or [])
            if isinstance(_patch_trace.get("guard_result"), dict) and _patch_trace.get("guard_result"):
                entry["patch_trace"]["guard_result"] = dict(_patch_trace.get("guard_result") or {})
            if isinstance(_patch_trace.get("repair_trace"), list) and _patch_trace.get("repair_trace"):
                entry["patch_trace"]["repair_trace"] = list(_patch_trace.get("repair_trace") or [])
            if isinstance(_patch_trace.get("partial_fix_eval"), dict) and _patch_trace.get("partial_fix_eval"):
                entry["patch_trace"]["partial_fix_eval"] = dict(_patch_trace.get("partial_fix_eval") or {})
            # [SSS-T2] Carryover persistence from enriched gate_semantics
            if isinstance(carryover_contracts, dict):
                for _ck in ("conflict_resolution_linkage", "reuse_contract"):
                    _cv = carryover_contracts.get(_ck)
                    if isinstance(_cv, dict):
                        entry[_ck] = _cv
            log_path = Path(logs_dir) / "episode_production.jsonl"
            append_jsonl_record(log_path, entry)
            _db_adj = getattr(getattr(self.ctx, "current_project", None), "db", None)
            persist_stage4_raw_rationale_records(
                project_db=_db_adj,
                records=_build_stage4_attempt_raw_evidence_records(
                    attempt_key=_attempt_key,
                    ep_num=int(ep_num or 0),
                    feedback_provenance=_feedback_provenance,
                    patch_trace=_patch_trace,
                    gate_semantics=_gate_semantics,
                    fix_pack=_fix_pack,
                    repair_contract=_repair_contract,
                    scope_authority=_scope_authority,
                    retry_budget_axes=_retry_budget_axes,
                ),
                log_prefix="Stage4EpisodeLog",
            )
        except Exception as e:
            logging.warning("[V76] episode_production log 실패 (비차단): %s", e)

    def _build_stage4_attempt_artifact_meta(
        self,
        *,
        episode: int,
        round_num: int,
        arc: int,
        candidate_key: str,
        artifact_kind: str,
        artifact_payload,
    ) -> dict[str, str]:
        _candidate_key = str(candidate_key or "").strip()
        if not artifact_payload:
            return {
                "candidate_key": _candidate_key,
                "content_hash": "",
                "artifact_path": "",
            }
        return snapshot_logged_artifact(
            getattr(self.ctx, "current_project", None),
            stage=4,
            ep_num=episode,
            arc_num=arc,
            attempt_num=round_num + 1,
            candidate_key=_candidate_key,
            artifact_kind=artifact_kind,
            payload=artifact_payload,
        )

    def _extract_stage4_advisory_contract_payloads(
        self,
        advisory_flags: dict | None,
    ) -> tuple[dict, dict, dict, dict]:
        _gate_semantics = {}
        _fix_pack = {}
        _repair_contract = {}
        _retry_budget_axes = {}
        if isinstance(advisory_flags, dict):
            if isinstance(advisory_flags.get("gate_semantics"), dict):
                _gate_semantics = dict(advisory_flags.get("gate_semantics") or {})
            if isinstance(advisory_flags.get("fix_pack"), dict):
                _fix_pack = dict(advisory_flags.get("fix_pack") or {})
            if isinstance(advisory_flags.get("repair_contract"), dict):
                _repair_contract = dict(advisory_flags.get("repair_contract") or {})
            elif isinstance(_gate_semantics.get("repair_contract"), dict):
                _repair_contract = dict(_gate_semantics.get("repair_contract") or {})
            if isinstance(advisory_flags.get("retry_budget_axes"), dict):
                _retry_budget_axes = dict(advisory_flags.get("retry_budget_axes") or {})
        return _gate_semantics, _fix_pack, _repair_contract, _retry_budget_axes

    def _build_stage4_attempt_contract_packet(
        self,
        advisory_flags: dict | None,
        *,
        resolve_db_fallbacks: bool,
    ) -> _Stage4AttemptContractPacket:
        normalized_advisory = (
            self._resolve_stage4_db_attempt_advisory_flags(advisory_flags)
            if resolve_db_fallbacks
            else dict(advisory_flags or {})
            if isinstance(advisory_flags, dict)
            else {}
        )
        gate_semantics, fix_pack, repair_contract, retry_budget_axes = self._extract_stage4_advisory_contract_payloads(
            normalized_advisory
        )
        derived_repair_contract = self._build_repair_contract_payload_from_parts(
            gate_semantics=gate_semantics,
            fix_pack=fix_pack,
            source=normalized_advisory if isinstance(normalized_advisory, dict) else {},
        )
        if derived_repair_contract:
            repair_contract = {**repair_contract, **derived_repair_contract}
        scope_authority = self._build_scope_authority_payload_from_parts(
            gate_semantics=gate_semantics,
            source=(
                {**normalized_advisory, "repair_contract": repair_contract}
                if normalized_advisory
                else {"repair_contract": repair_contract}
            ),
        )
        verdict_layers = (
            dict(gate_semantics.get("verdict_layers") or {})
            if isinstance(gate_semantics.get("verdict_layers"), dict)
            else {}
        )
        return _Stage4AttemptContractPacket(
            advisory_flags=normalized_advisory if isinstance(normalized_advisory, dict) else {},
            gate_semantics=gate_semantics,
            fix_pack=fix_pack,
            repair_contract=repair_contract,
            scope_authority=scope_authority,
            retry_budget_axes=retry_budget_axes,
            verdict_layers=verdict_layers,
        )

    def _resolve_stage4_db_attempt_advisory_flags(
        self,
        advisory_flags: dict | None,
    ) -> dict | None:
        _adv = advisory_flags if advisory_flags is not None else getattr(self, "_last_advisory_summary", None)
        if not isinstance(_adv, dict):
            return _adv or None
        _normalized = dict(_adv)
        _gate_semantics = (
            dict(_normalized.get("gate_semantics") or {}) if isinstance(_normalized.get("gate_semantics"), dict) else {}
        )
        _fix_pack = dict(_normalized.get("fix_pack") or {}) if isinstance(_normalized.get("fix_pack"), dict) else {}
        _nested_repair_contract = (
            dict(_gate_semantics.get("repair_contract") or {})
            if isinstance(_gate_semantics.get("repair_contract"), dict)
            else {}
        )
        _repair_contract = (
            dict(_normalized.get("repair_contract") or {})
            if isinstance(_normalized.get("repair_contract"), dict)
            else {}
        )
        if _nested_repair_contract:
            _repair_contract = {**_repair_contract, **_nested_repair_contract}
        if not _repair_contract and _nested_repair_contract:
            _repair_contract = dict(_nested_repair_contract)
        _derived_repair_contract = self._build_repair_contract_payload_from_parts(
            gate_semantics=_gate_semantics,
            fix_pack=_fix_pack,
            source={**_normalized, **_nested_repair_contract},
        )
        if _derived_repair_contract:
            _repair_contract = {**_repair_contract, **_derived_repair_contract}
        if _repair_contract:
            _normalized["repair_contract"] = _repair_contract

        _nested_scope_authority = (
            dict(_gate_semantics.get("scope_authority") or {})
            if isinstance(_gate_semantics.get("scope_authority"), dict)
            else {}
        )
        _scope_authority = (
            dict(_normalized.get("scope_authority") or {})
            if isinstance(_normalized.get("scope_authority"), dict)
            else {}
        )
        if _nested_scope_authority:
            _scope_authority = {**_scope_authority, **_nested_scope_authority}
        if not _scope_authority and _nested_scope_authority:
            _scope_authority = dict(_nested_scope_authority)
        _derived_scope_authority = self._build_scope_authority_payload_from_parts(
            gate_semantics=_gate_semantics,
            source={
                **_normalized,
                **_repair_contract,
                "repair_contract": _repair_contract,
                "scope_authority": _scope_authority,
            },
        )
        if _derived_scope_authority:
            _scope_authority = {**_scope_authority, **_derived_scope_authority}
        if _scope_authority:
            _normalized["scope_authority"] = _scope_authority
        return _normalized or None

    def _resolve_stage4_db_attempt_model(
        self,
        model: str | None,
    ) -> str | None:
        if model:
            return str(model)
        _director = getattr(getattr(self.ctx, "agents", {}), "get", lambda *_: None)("director")
        _model = getattr(_director, "primary_model", None) if _director else None
        return str(_model) if _model else None

    def _build_stage4_pass_rate_attempt_payload(
        self,
        *,
        episode: int,
        round_num: int,
        score: int,
        arc: int,
        success: bool,
        reject_reason: str,
        is_patch: bool,
        patch_fallback: bool,
        duration_ms: int | None,
        token_cost: float | None,
        prev_score: float,
        attempt_key: str,
        verdict: str | None,
        advisory_flags: dict | None,
        patch_strategy: str,
        structural_attempted: bool,
        error_category: str,
        reject_bucket: str,
        score_breakdown: dict | None,
        artifact_meta: dict[str, str],
    ) -> dict:
        contract_packet = self._build_stage4_attempt_contract_packet(
            advisory_flags,
            resolve_db_fallbacks=False,
        )
        payload = {
            "stage": 4,
            "episode": episode,
            "arc": arc,
            "attempt_num": round_num + 1,
            "success": success,
            "reject_reason": "" if success else (reject_reason or f"score={score}"),
            "generation_method": "patch" if is_patch and not patch_fallback else "ensemble",
            "duration_ms": duration_ms or 0,
            "token_cost": token_cost or 0.0,
            "is_patch": is_patch,
            "prev_score": prev_score,
            "patch_fallback": patch_fallback,
            "attempt_key": attempt_key,
            "final_verdict": str(verdict or ("PASS" if success else "REJECT")),
            "patch_strategy": patch_strategy,
            "structural_attempted": bool(structural_attempted),
            "error_category": str(error_category or ""),
            "reject_bucket": str(reject_bucket or ""),
            "score_breakdown": (score_breakdown or {}),
            "candidate_key": artifact_meta["candidate_key"],
            "content_hash": artifact_meta["content_hash"],
            "artifact_path": artifact_meta["artifact_path"],
            **_build_stage4_attempt_contract_projection(
                contract_packet=contract_packet,
                include_strong_advisory_escalation=True,
            ),
        }
        return payload

    def _build_stage4_db_attempt_payload(
        self,
        *,
        episode: int,
        round_num: int,
        success: bool,
        score: int,
        arc: int,
        verdict: str | None,
        reject_reason: str,
        fix_scope: str | None,
        model: str | None,
        duration_ms: int | None,
        advisory_flags: dict | None,
        session_id: str | None,
        attempt_key: str,
        artifact_meta: dict[str, str],
        selection_reason: str,
        verdict_reason: str,
        open_review: str,
        fix_scope_reasoning: str,
        runtime_advisory: str,
        retry_directives: str,
        failure_category: str = "",
        initial_verdict: str = "",
        score_breakdown: dict | None = None,
        is_patch: bool = False,
        is_patch_fallback: bool = False,
        patch_strategy: str = "",
    ) -> dict:
        contract_packet = self._build_stage4_attempt_contract_packet(
            advisory_flags,
            resolve_db_fallbacks=True,
        )
        _model = self._resolve_stage4_db_attempt_model(model)
        db_projection = _build_stage4_attempt_contract_projection(
            contract_packet=contract_packet,
            fix_scope_fallback=fix_scope,
            empty_fix_scope_as_none=True,
            include_director_quality_passed=True,
        )
        return {
            "stage": 4,
            "verdict": verdict or ("PASS" if success else "REJECT"),
            "attempt_num": round_num + 1,
            "ep_num": episode,
            "arc_num": arc,
            "score": score,
            "failure_category": failure_category or None,
            "reject_reason": "" if success else (reject_reason or f"score={score}"),
            "fix_scope": db_projection.get("fix_scope"),
            "model": _model,
            "duration_ms": duration_ms,
            "advisory_flags": contract_packet.advisory_flags,
            "session_id": session_id,
            "attempt_key": attempt_key,
            "prompt_version": _build_stage4_prompt_version(),
            "candidate_key": artifact_meta["candidate_key"],
            "content_hash": artifact_meta["content_hash"],
            "artifact_path": artifact_meta["artifact_path"],
            "selection_reason": selection_reason,
            "verdict_reason": verdict_reason,
            "open_review": open_review,
            "fix_scope_reasoning": fix_scope_reasoning,
            "runtime_advisory": runtime_advisory,
            "retry_directives": retry_directives,
            "initial_verdict": initial_verdict or None,
            "score_breakdown": score_breakdown,
            "is_patch": is_patch,
            "is_patch_fallback": is_patch_fallback,
            "patch_strategy": patch_strategy or None,
            "director_quality_passed": bool(db_projection.get("director_quality_passed", False)),
            "downstream_override_applied": bool(db_projection.get("downstream_override_applied", False)),
            "primary_failure_layer": str(db_projection.get("primary_failure_layer") or "").strip() or None,
        }

    def _build_stage4_attempt_prelude(
        self,
        *,
        episode: int,
        round_num: int,
        arc: int,
        is_patch: bool,
        patch_fallback: bool,
        patch_strategy: str,
        candidate_key: str,
        artifact_kind: str,
        artifact_payload,
        duration_ms: int | None,
        token_cost: float | None,
    ) -> _Stage4AttemptPreludePayload:
        if duration_ms is None and hasattr(self, "_round_start_ts"):
            try:
                duration_ms = int((time.monotonic() - self._round_start_ts) * 1000)
            except Exception:
                duration_ms = None
        if token_cost is None:
            try:
                token_cost = float(self._get_round_metrics_delta().get("total_cost_usd", 0.0))
            except Exception:
                token_cost = 0.0
        session_id = resolve_logging_session_id(getattr(self.ctx, "current_project", None))
        attempt_key = build_attempt_key(
            stage=4,
            ep_num=episode,
            arc_num=arc,
            attempt_num=round_num + 1,
            session_id=session_id,
        )
        normalized_patch_strategy = str(patch_strategy or "").strip()
        if is_patch and not normalized_patch_strategy:
            normalized_patch_strategy = "patch_fallback_rewrite" if patch_fallback else "patch_with_feedback"
        artifact_meta = self._build_stage4_attempt_artifact_meta(
            episode=episode,
            round_num=round_num,
            arc=arc,
            candidate_key=candidate_key,
            artifact_kind=artifact_kind,
            artifact_payload=artifact_payload,
        )
        return _Stage4AttemptPreludePayload(
            duration_ms=duration_ms,
            token_cost=float(token_cost or 0.0),
            session_id=session_id,
            attempt_key=attempt_key,
            normalized_patch_strategy=normalized_patch_strategy,
            artifact_meta=artifact_meta,
        )

    def _record_stage4_pass_rate_attempt(
        self,
        *,
        episode: int,
        round_num: int,
        score: int,
        arc: int,
        success: bool,
        reject_reason: str,
        is_patch: bool,
        patch_fallback: bool,
        prev_score: float,
        verdict: str | None,
        advisory_flags: dict | None,
        structural_attempted: bool,
        error_category: str,
        reject_bucket: str,
        score_breakdown: dict | None,
        prelude: _Stage4AttemptPreludePayload,
    ) -> None:
        if not getattr(self.ctx, "pass_rate_monitor", None):
            return
        try:
            self.ctx.pass_rate_monitor.record_attempt(
                **self._build_stage4_pass_rate_attempt_payload(
                    episode=episode,
                    round_num=round_num,
                    score=score,
                    arc=arc,
                    success=success,
                    reject_reason=reject_reason,
                    is_patch=is_patch,
                    patch_fallback=patch_fallback,
                    duration_ms=prelude.duration_ms,
                    token_cost=prelude.token_cost,
                    prev_score=prev_score,
                    attempt_key=prelude.attempt_key,
                    verdict=verdict,
                    advisory_flags=advisory_flags,
                    patch_strategy=prelude.normalized_patch_strategy,
                    structural_attempted=structural_attempted,
                    error_category=error_category,
                    reject_bucket=reject_bucket,
                    score_breakdown=score_breakdown,
                    artifact_meta=prelude.artifact_meta,
                )
            )
        except Exception as _e:
            logging.debug("[InterviewRound] PassRateMonitor 기록 실패 (비차단): %s", _e)

    def _save_stage4_db_attempt(
        self,
        *,
        episode: int,
        round_num: int,
        success: bool,
        score: int,
        arc: int,
        verdict: str | None,
        reject_reason: str,
        fix_scope: str | None,
        model: str | None,
        advisory_flags: dict | None,
        selection_reason: str,
        verdict_reason: str,
        open_review: str,
        fix_scope_reasoning: str,
        runtime_advisory: str,
        retry_directives: str,
        error_category: str = "",
        initial_verdict: str = "",
        score_breakdown: dict | None = None,
        is_patch: bool = False,
        is_patch_fallback: bool = False,
        patch_strategy: str = "",
        prelude: _Stage4AttemptPreludePayload,
    ) -> None:
        try:
            _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
            if not _db or not hasattr(_db, "save_stage_attempt"):
                return
            _db.save_stage_attempt(
                **self._build_stage4_db_attempt_payload(
                    episode=episode,
                    round_num=round_num,
                    success=success,
                    score=score,
                    arc=arc,
                    verdict=verdict,
                    reject_reason=reject_reason,
                    fix_scope=fix_scope,
                    model=model,
                    duration_ms=prelude.duration_ms,
                    advisory_flags=advisory_flags,
                    session_id=prelude.session_id,
                    attempt_key=prelude.attempt_key,
                    artifact_meta=prelude.artifact_meta,
                    selection_reason=selection_reason,
                    verdict_reason=verdict_reason,
                    open_review=open_review,
                    fix_scope_reasoning=fix_scope_reasoning,
                    runtime_advisory=runtime_advisory,
                    retry_directives=retry_directives,
                    failure_category=error_category,
                    initial_verdict=initial_verdict,
                    score_breakdown=score_breakdown,
                    is_patch=is_patch,
                    is_patch_fallback=is_patch_fallback,
                    patch_strategy=patch_strategy,
                )
            )
        except Exception as _sa_err:
            logging.debug("[stage_attempts] Stage4 record failed (non-blocking): %s", _sa_err)

    @staticmethod
    def _build_stage4_attempt_return_payload(prelude: _Stage4AttemptPreludePayload) -> dict[str, str]:
        return {
            "attempt_key": prelude.attempt_key,
            "candidate_key": prelude.artifact_meta["candidate_key"],
            "content_hash": prelude.artifact_meta["content_hash"],
            "artifact_path": prelude.artifact_meta["artifact_path"],
        }

    def _record_s4_attempt(
        self,
        *,
        episode: int,
        round_num: int,
        success: bool,
        score: int = 0,
        is_patch: bool = False,
        prev_score: float = 0,
        patch_fallback: bool = False,
        arc: int = 0,
        verdict: str | None = None,
        reject_reason: str = "",
        fix_scope: str | None = None,
        advisory_flags: dict | None = None,
        model: str | None = None,
        duration_ms: int | None = None,
        token_cost: float | None = None,
        patch_strategy: str = "",
        structural_attempted: bool = False,
        candidate_key: str = "",
        artifact_payload=None,
        artifact_kind: str = "artifact",
        selection_reason: str = "",
        verdict_reason: str = "",
        open_review: str = "",
        fix_scope_reasoning: str = "",
        runtime_advisory: str = "",
        retry_directives: str = "",
        error_category: str = "",
        reject_bucket: str = "",
        score_breakdown: dict | None = None,
        initial_verdict: str = "",
    ) -> dict:
        """Stage 4 시도 결과를 stage_attempts DB에 저장한다."""
        prelude = self._build_stage4_attempt_prelude(
            episode=episode,
            round_num=round_num,
            arc=arc,
            is_patch=is_patch,
            patch_fallback=patch_fallback,
            patch_strategy=patch_strategy,
            candidate_key=candidate_key,
            artifact_kind=artifact_kind,
            artifact_payload=artifact_payload,
            duration_ms=duration_ms,
            token_cost=token_cost,
        )
        self._record_stage4_pass_rate_attempt(
            episode=episode,
            round_num=round_num,
            score=score,
            arc=arc,
            success=success,
            reject_reason=reject_reason,
            is_patch=is_patch,
            patch_fallback=patch_fallback,
            prev_score=prev_score,
            verdict=verdict,
            advisory_flags=advisory_flags,
            structural_attempted=structural_attempted,
            error_category=error_category,
            reject_bucket=reject_bucket,
            score_breakdown=score_breakdown,
            prelude=prelude,
        )
        self._save_stage4_db_attempt(
            episode=episode,
            round_num=round_num,
            success=success,
            score=score,
            arc=arc,
            verdict=verdict,
            reject_reason=reject_reason,
            fix_scope=fix_scope,
            model=model,
            advisory_flags=advisory_flags,
            selection_reason=selection_reason,
            verdict_reason=verdict_reason,
            open_review=open_review,
            fix_scope_reasoning=fix_scope_reasoning,
            runtime_advisory=runtime_advisory,
            retry_directives=retry_directives,
            error_category=error_category,
            initial_verdict=initial_verdict,
            score_breakdown=score_breakdown,
            is_patch=is_patch,
            is_patch_fallback=patch_fallback,
            patch_strategy=patch_strategy,
            prelude=prelude,
        )
        return self._build_stage4_attempt_return_payload(prelude)
