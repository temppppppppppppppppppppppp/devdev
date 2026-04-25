from __future__ import annotations

import copy
from typing import Any, Mapping

SESSION_MEMORY_ENVELOPE_VERSION = "session-memory-envelope-v1"
SESSION_MEMORY_ENVELOPE_KEY = "session_memory_envelope"


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)


def _as_dict(value: Any) -> dict[str, Any]:
    return _json_safe(value) if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return []


def _first_dict(*values: Any) -> dict[str, Any]:
    for value in values:
        normalized = _as_dict(value)
        if normalized:
            return normalized
    return {}


def _merge_dicts(*values: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for value in values:
        normalized = _as_dict(value)
        if normalized:
            merged.update(normalized)
    return merged


def _merge_lists(*values: Any) -> list[Any]:
    merged: list[Any] = []
    for value in values:
        merged.extend(_as_list(value))
    return merged


def _merge_truth_pin_items(*values: Any) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for value in values:
        if isinstance(value, Mapping):
            candidates = [_as_dict(value)]
        elif isinstance(value, (list, tuple)):
            candidates = [_as_dict(item) for item in value if isinstance(item, Mapping)]
        else:
            candidates = []
        for item in candidates:
            if not item:
                continue
            marker = (
                str(item.get("pin_key", "") or "").strip(),
                str(item.get("family", "") or "").strip(),
                str(item.get("expected", "") or "").strip(),
                str(item.get("observed", "") or "").strip(),
            )
            if marker in seen:
                continue
            seen.add(marker)
            merged.append(item)
    return merged


def _summarize_truth_pin_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for item in items:
        pin_key = str(item.get("pin_key", "") or "").strip()
        expected = _json_safe(item.get("expected"))
        if pin_key and expected not in ("", None, [], {}):
            summary[pin_key] = expected
    return summary


def build_stage4_session_memory_envelope(
    *,
    episode: int,
    round_num: int,
    arc: int,
    success: bool,
    score: int,
    verdict: str | None,
    reject_reason: str,
    fix_scope: str | None,
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
    reject_bucket: str = "",
    failure_category: str,
    initial_verdict: str,
    is_patch: bool,
    is_patch_fallback: bool,
    patch_strategy: str,
) -> dict[str, Any]:
    advisory = _as_dict(advisory_flags)
    gate_semantics = _as_dict(advisory.get("gate_semantics"))
    repair_contract = _first_dict(advisory.get("repair_contract"), gate_semantics.get("repair_contract"))
    scope_authority = _first_dict(advisory.get("scope_authority"), gate_semantics.get("scope_authority"))
    conflict_contract = _as_dict(advisory.get("conflict_contract"))
    fix_pack = _as_dict(advisory.get("fix_pack"))

    truth_pin_items = _merge_truth_pin_items(
        advisory.get("truth_pins"),
        gate_semantics.get("truth_pins"),
        conflict_contract.get("truth_pins"),
    )
    truth_pins = _merge_dicts(
        advisory.get("truth_pins"),
        gate_semantics.get("truth_pins"),
        _summarize_truth_pin_items(truth_pin_items),
    )
    carryover_refs = _merge_dicts(
        advisory.get("carryover_refs"),
        advisory.get("carryover_packet_refs"),
        gate_semantics.get("conflict_resolution_linkage"),
        gate_semantics.get("reuse_contract"),
    )
    coverage_warnings = _merge_lists(
        advisory.get("coverage_warnings"),
        advisory.get("candidate_warnings"),
        advisory.get("final_warnings"),
        advisory.get("warnings"),
    )

    return {
        "schema_version": SESSION_MEMORY_ENVELOPE_VERSION,
        "source": "stage4_attempt",
        "stage": 4,
        "ep_num": episode,
        "arc_num": arc,
        "attempt_num": round_num + 1,
        "attempt_key": str(attempt_key or ""),
        "session_id": str(session_id or ""),
        "candidate": {
            "candidate_key": str((artifact_meta or {}).get("candidate_key", "") or ""),
            "content_hash": str((artifact_meta or {}).get("content_hash", "") or ""),
            "artifact_path": str((artifact_meta or {}).get("artifact_path", "") or ""),
        },
        "verdict_surface": {
            "accepted": bool(success),
            "verdict": str(verdict or ("PASS" if success else "REJECT")),
            "initial_verdict": str(initial_verdict or ""),
            "score": int(score or 0),
            "failure_category": str(failure_category or ""),
            "reject_reason": str(reject_reason or ""),
            "selection_reason": str(selection_reason or ""),
            "verdict_reason": str(verdict_reason or ""),
            "open_review": str(open_review or ""),
        },
        "retry_surface": {
            "fix_scope": str(fix_scope or ""),
            "fix_scope_reasoning": str(fix_scope_reasoning or ""),
            "runtime_advisory": str(runtime_advisory or ""),
            "retry_directives": str(retry_directives or ""),
            "reject_bucket": str(reject_bucket or ""),
            "retry_budget_axes": _as_dict(advisory.get("retry_budget_axes")),
            "repair_contract": repair_contract,
            "scope_authority": scope_authority,
            "fix_pack": fix_pack,
            "is_patch": bool(is_patch),
            "is_patch_fallback": bool(is_patch_fallback),
            "patch_strategy": str(patch_strategy or ""),
        },
        "truth_pins": truth_pins,
        "truth_pin_items": truth_pin_items,
        "carryover_refs": carryover_refs,
        "coverage_warnings": coverage_warnings,
        "cache_lineage": _as_dict(advisory.get("cache_lineage")),
    }


def attach_session_memory_envelope(
    advisory_flags: dict | None,
    envelope: dict[str, Any],
) -> dict[str, Any]:
    merged = copy.deepcopy(advisory_flags) if isinstance(advisory_flags, dict) else {}
    existing = _as_dict(merged.get(SESSION_MEMORY_ENVELOPE_KEY))
    merged[SESSION_MEMORY_ENVELOPE_KEY] = {
        **existing,
        **_as_dict(envelope),
    }
    return merged


def get_session_memory_envelope(advisory_flags: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(advisory_flags, Mapping):
        return {}
    return copy.deepcopy(_as_dict(advisory_flags.get(SESSION_MEMORY_ENVELOPE_KEY)))
