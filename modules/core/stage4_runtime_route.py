from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

STAGE4_RUNTIME_ROUTE_PAYLOAD_VERSION = "stage4-runtime-route-v1"
STAGE4_RUNTIME_ROUTE_TAXONOMY = "runtime_route_guard"
STAGE4_RUNTIME_ROUTE_SCALAR_KEYS = (
    "runtime_route_payload_version",
    "runtime_route_verdict",
    "runtime_route_action",
    "runtime_route_reason",
    "runtime_route_taxonomy",
)

STAGE4_RUNTIME_ROUTE_ACTION_BY_GATE = {
    "director_primary_pass": "adopt_stage4_artifact",
    "director_primary_pass_with_fix": "enter_pass_with_fix_repair",
    "director_primary_reject": "director_reject_retry",
    "quality_floor_fail": "block_artifact_adoption",
    "post_select_conflict": "route_retry_full_rewrite",
    "empty_feedback_abort": "abort_local_repair_retry",
    "fix_scope_contract_violation": "block_local_repair_contract",
    "strong_advisory_escalation_no_scope": "block_local_repair_contract",
    "strong_advisory_escalation_non_local_fix": "route_retry_nonlocal_repair",
    "patch_reaudit_pass": "adopt_patched_artifact",
    "patch_reaudit_fail": "block_patch_adoption",
}

_SESSION_MEMORY_ENVELOPE_KEY = "session_memory_envelope"


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def stage4_runtime_route_action(*, gate_basis: object, final_verdict: object) -> str:
    basis = _clean_text(gate_basis)
    verdict = _clean_text(final_verdict).upper()
    if basis in STAGE4_RUNTIME_ROUTE_ACTION_BY_GATE:
        return STAGE4_RUNTIME_ROUTE_ACTION_BY_GATE[basis]
    if basis.startswith("pass_with_fix_contract_"):
        return "route_retry_nonlocal_repair"
    if basis.startswith("pass_with_fix_inplace_contract_fail_"):
        return "route_retry_partial_repair"
    if verdict == "REJECT":
        return "block_or_retry_stage4_artifact"
    if verdict == "PASS":
        return "adopt_stage4_artifact"
    if verdict == "PASS_WITH_FIX":
        return "enter_pass_with_fix_repair"
    return "record_stage4_route"


def _stage4_route_sources_for_payload(payload: object) -> list[dict[str, Any]]:
    root = _as_dict(payload)
    if not root:
        return []
    sources: list[dict[str, Any]] = [root]
    for key in ("gate_semantics", "verdict_layers"):
        nested = _as_dict(root.get(key))
        if nested:
            sources.append(nested)
    envelope = _as_dict(root.get(_SESSION_MEMORY_ENVELOPE_KEY))
    if envelope:
        for key in ("verdict_surface", "retry_surface"):
            nested = _as_dict(envelope.get(key))
            if nested:
                sources.append(nested)
    for key in ("verdict_surface", "retry_surface"):
        nested = _as_dict(root.get(key))
        if nested:
            sources.append(nested)
    return sources


def stage4_route_sources(payload: object, *extra_sources: object) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for source in (payload, *extra_sources):
        sources.extend(_stage4_route_sources_for_payload(source))
    return sources


def extract_stage4_runtime_route(payload: object, *extra_sources: object) -> dict[str, str]:
    route: dict[str, str] = {}
    for source in stage4_route_sources(payload, *extra_sources):
        for key in STAGE4_RUNTIME_ROUTE_SCALAR_KEYS:
            if key in route:
                continue
            value = _clean_text(source.get(key))
            if value:
                route[key] = value
        if len(route) == len(STAGE4_RUNTIME_ROUTE_SCALAR_KEYS):
            break
    return route


def copy_stage4_runtime_route_fields(target: dict[str, object], *sources: object) -> None:
    if not isinstance(target, dict):
        return
    route = extract_stage4_runtime_route(*sources)
    for key, value in route.items():
        if value:
            target[key] = copy.deepcopy(value)


def is_stage4_post_select_route(payload: object, *extra_sources: object) -> bool:
    route = extract_stage4_runtime_route(payload, *extra_sources)
    if route.get("runtime_route_action") == "route_retry_full_rewrite":
        return True
    return any(
        _clean_text(source.get("gate_basis")) == "post_select_conflict"
        for source in stage4_route_sources(payload, *extra_sources)
    )


def is_stage4_nonlocal_repair_route(payload: object, *extra_sources: object) -> bool:
    route = extract_stage4_runtime_route(payload, *extra_sources)
    if route.get("runtime_route_action") == "route_retry_nonlocal_repair":
        return True
    return any(
        _clean_text(source.get("gate_basis")) == "strong_advisory_escalation_non_local_fix"
        for source in stage4_route_sources(payload, *extra_sources)
    )


def stage4_reject_bucket_from_route(payload: object, *extra_sources: object) -> str:
    for source in stage4_route_sources(payload, *extra_sources):
        reject_bucket = _clean_text(source.get("reject_bucket"))
        if reject_bucket:
            return reject_bucket

    route = extract_stage4_runtime_route(payload, *extra_sources)
    action = route.get("runtime_route_action", "")
    if action == "route_retry_full_rewrite":
        return "post_select_conflict"
    if action == "block_artifact_adoption":
        return "quality_issue"

    for source in stage4_route_sources(payload, *extra_sources):
        gate_basis = _clean_text(source.get("gate_basis")).lower()
        if gate_basis == "post_select_conflict":
            return "post_select_conflict"
        if gate_basis == "quality_floor_fail":
            return "quality_issue"
    return ""
