"""
Shared raw-evidence persistence helpers for Stage 4.
"""

import json
import logging

_STAGE4_RAW_RATIONALE_KIND_TO_FAMILY = {
    "director_thinking": "reasoning",
    "advisory_warnings_raw": "advisory_bundle",
    "selection_contract_snapshot_raw": "contract_snapshot",
    "contract_snapshot_raw": "contract_snapshot",
    "selection_surface_raw": "selection_surface",
    "feedback_provenance_raw": "feedback_provenance",
    "patch_trace_raw": "patch_trace",
    "reject_retry_snapshot_raw": "reject_retry_snapshot",
    "retry_pathology_raw": "retry_pathology",
}


def _safe_dict(value) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_str(value) -> str:
    return str(value or "").strip()


def _safe_str_list(value, *, limit: int = 8) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for raw in value:
        text = _safe_str(raw)
        if text:
            items.append(text)
        if len(items) >= limit:
            break
    return items


def _safe_bool(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
        return None
    if isinstance(value, (int, float)):
        return bool(value)
    return None


def _pick_repair_contract_subtype(repair_contract: dict[str, object]) -> str:
    subtype = _safe_str(repair_contract.get("subtype"))
    if subtype:
        return subtype
    subtypes = _safe_str_list(repair_contract.get("subtypes"))
    return subtypes[0] if subtypes else ""


def decode_stage4_raw_rationale_payload(payload) -> object:
    if not isinstance(payload, str):
        return payload
    try:
        return json.loads(payload)
    except (TypeError, ValueError, json.JSONDecodeError):
        return payload


def extract_stage4_raw_rationale_meta(payload) -> dict[str, object]:
    decoded = decode_stage4_raw_rationale_payload(payload)
    if not isinstance(decoded, dict):
        return {}
    meta = decoded.get("_meta")
    if not isinstance(meta, dict):
        return {}
    return {
        str(key): value for key, value in meta.items() if str(key or "").strip() and value not in ("", None, [], {})
    }


def infer_stage4_raw_rationale_family(
    *,
    payload_kind: str,
    payload,
) -> str:
    meta = extract_stage4_raw_rationale_meta(payload)
    family = str(meta.get("record_family", "") or "").strip()
    if family:
        return family
    return str(_STAGE4_RAW_RATIONALE_KIND_TO_FAMILY.get(str(payload_kind or "").strip(), "") or "")


def infer_stage4_raw_rationale_surface(
    *,
    payload_kind: str,
    payload,
) -> str:
    meta = extract_stage4_raw_rationale_meta(payload)
    surface = str(meta.get("surface", "") or "").strip()
    if surface:
        return surface
    return str(payload_kind or "").strip()


def summarize_stage4_raw_rationale_rows(rows: list[dict] | None) -> dict[str, object]:
    payload_kinds: set[str] = set()
    record_families: set[str] = set()
    surfaces: set[str] = set()
    decoded_payloads: dict[str, object] = {}
    projected_payloads: dict[str, dict[str, object]] = {}

    for row in rows or []:
        if not isinstance(row, dict):
            continue
        payload_kind = str(row.get("payload_kind") or "").strip()
        if not payload_kind:
            continue
        payload = row.get("payload")
        decoded_payload = decode_stage4_raw_rationale_payload(payload)
        payload_kinds.add(payload_kind)
        decoded_payloads[payload_kind] = decoded_payload

        family = infer_stage4_raw_rationale_family(
            payload_kind=payload_kind,
            payload=decoded_payload,
        )
        if family:
            record_families.add(family)

        surface = infer_stage4_raw_rationale_surface(
            payload_kind=payload_kind,
            payload=decoded_payload,
        )
        if surface:
            surfaces.add(surface)

        projected_payload = project_stage4_raw_payload(
            payload_kind=payload_kind,
            payload=decoded_payload,
        )
        if projected_payload:
            projected_payloads[payload_kind] = projected_payload

    return {
        "payload_kinds": payload_kinds,
        "record_families": record_families,
        "surfaces": surfaces,
        "decoded_payloads": decoded_payloads,
        "projected_payloads": projected_payloads,
    }


def project_stage4_raw_selection_surface(payload) -> dict[str, object]:
    decoded = decode_stage4_raw_rationale_payload(payload)
    if not isinstance(decoded, dict):
        return {}
    result: dict[str, object] = {}
    for key in (
        "selected_label",
        "selected_strategy",
        "verdict",
        "score",
        "selection_reason",
        "verdict_reason",
        "fix_scope",
        "candidate_key",
        "content_hash",
        "artifact_path",
    ):
        value = decoded.get(key)
        if value in ("", None, [], {}):
            continue
        result[key] = value
    return result


def project_stage4_raw_feedback_provenance(payload) -> dict[str, object]:
    decoded = decode_stage4_raw_rationale_payload(payload)
    if not isinstance(decoded, dict):
        return {}
    result: dict[str, object] = {}
    for key in ("director_feedback", "director_feedback_text", "runtime_advisory", "retry_directives"):
        value = _safe_str(decoded.get(key))
        if value:
            result[key] = value
    return result


def project_stage4_raw_patch_trace(payload) -> dict[str, object]:
    decoded = decode_stage4_raw_rationale_payload(payload)
    if not isinstance(decoded, dict):
        return {}
    result: dict[str, object] = {}
    patch_strategy = _safe_str(decoded.get("patch_strategy"))
    if patch_strategy:
        result["patch_strategy"] = patch_strategy
    if "structural_attempted" in decoded:
        structural_attempted = _safe_bool(decoded.get("structural_attempted"))
        if structural_attempted is not None:
            result["structural_attempted"] = structural_attempted
    return result


def project_stage4_raw_reject_retry_snapshot(payload) -> dict[str, object]:
    decoded = decode_stage4_raw_rationale_payload(payload)
    if not isinstance(decoded, dict):
        return {}
    result: dict[str, object] = {}
    candidate_key = _safe_str(decoded.get("candidate_key"))
    if candidate_key:
        result["candidate_key"] = candidate_key
    previous_attempt = _safe_dict(decoded.get("previous_attempt"))
    if previous_attempt:
        attempt_key = _safe_str(previous_attempt.get("attempt_key"))
        candidate_key = _safe_str(previous_attempt.get("candidate_key"))
        content_hash = _safe_str(previous_attempt.get("content_hash"))
        if attempt_key:
            result["previous_attempt_attempt_key"] = attempt_key
        if candidate_key:
            result["previous_attempt_candidate_key"] = candidate_key
        if content_hash:
            result["previous_attempt_content_hash"] = content_hash
        for raw_key, projected_key in (
            ("scope_origin", "previous_attempt_scope_origin"),
            ("reuse_contract", "previous_attempt_reuse_contract"),
            ("authoritative_fix_scope_violation", "previous_attempt_authoritative_fix_scope_violation"),
        ):
            value = previous_attempt.get(raw_key)
            if isinstance(value, dict) and value:
                result[projected_key] = value
    return result


def project_stage4_raw_retry_pathology(payload) -> dict[str, object]:
    decoded = decode_stage4_raw_rationale_payload(payload)
    if not isinstance(decoded, dict):
        return {}
    result: dict[str, object] = {}
    for key in ("attempt_key", "candidate_key", "content_hash", "pathology_fingerprint", "rationale_blanked_by"):
        value = _safe_str(decoded.get(key))
        if value:
            result[key] = value
    for key in ("scope_origin", "reuse_contract", "authoritative_fix_scope_violation"):
        value = decoded.get(key)
        if isinstance(value, dict) and value:
            result[key] = value
    return result


def project_stage4_raw_contract_snapshot(payload) -> dict[str, object]:
    decoded = decode_stage4_raw_rationale_payload(payload)
    if not isinstance(decoded, dict):
        return {}

    gate_payload = _safe_dict(decoded.get("gate_semantics"))
    fix_payload = _safe_dict(decoded.get("fix_pack"))
    retry_payload = _safe_dict(decoded.get("retry_budget_axes"))
    nested_repair_payload = _safe_dict(gate_payload.get("repair_contract"))
    repair_payload = {
        **nested_repair_payload,
        **_safe_dict(decoded.get("repair_contract")),
    }
    scope_seed = _safe_dict(gate_payload.get("scope_authority"))
    if not scope_seed:
        scope_seed = {
            key: gate_payload.get(key)
            for key in ("fix_scope", "authoritative_fix_scope", "scope_origin", "widened")
            if gate_payload.get(key) not in (None, "", [])
        }
    scope_payload = {
        **scope_seed,
        **_safe_dict(decoded.get("scope_authority")),
    }
    return {
        "director_verdict": _safe_str(gate_payload.get("director_verdict")),
        "gate_basis": _safe_str(gate_payload.get("gate_basis")),
        "repair_scope": _safe_str(gate_payload.get("repair_scope")),
        "fix_pack_target_kind": _safe_str(fix_payload.get("target_kind")),
        "fix_pack_patch_targets": _safe_str_list(fix_payload.get("patch_targets")),
        "retry_budget_axes": retry_payload,
        "repair_contract": repair_payload,
        "repair_contract_subtype": _pick_repair_contract_subtype(repair_payload),
        "repair_contract_provenance": _safe_str(repair_payload.get("provenance")),
        "scope_authority": scope_payload,
        "scope_authority_fix_scope": _safe_str(scope_payload.get("fix_scope")),
        "scope_authority_authoritative_fix_scope": _safe_str(scope_payload.get("authoritative_fix_scope")),
        "scope_authority_scope_origin": _safe_str(scope_payload.get("scope_origin")),
        "scope_authority_widened": _safe_bool(scope_payload.get("widened")),
    }


def project_stage4_raw_payload(*, payload_kind: str, payload) -> dict[str, object]:
    normalized_kind = _safe_str(payload_kind)
    if not normalized_kind:
        return {}
    if normalized_kind == "selection_surface_raw":
        return project_stage4_raw_selection_surface(payload)
    if normalized_kind in {"selection_contract_snapshot_raw", "contract_snapshot_raw"}:
        return project_stage4_raw_contract_snapshot(payload)
    if normalized_kind == "feedback_provenance_raw":
        return project_stage4_raw_feedback_provenance(payload)
    if normalized_kind == "patch_trace_raw":
        return project_stage4_raw_patch_trace(payload)
    if normalized_kind == "reject_retry_snapshot_raw":
        return project_stage4_raw_reject_retry_snapshot(payload)
    if normalized_kind == "retry_pathology_raw":
        return project_stage4_raw_retry_pathology(payload)
    return {}


def build_stage4_raw_rationale_record(
    *,
    attempt_key: str,
    ep_num: int,
    payload_kind: str,
    payload,
    stage: int = 4,
    payload_meta: dict[str, object] | None = None,
) -> dict[str, object] | None:
    attempt_key = str(attempt_key or "").strip()
    payload_kind = str(payload_kind or "").strip()
    if not attempt_key or not payload_kind or payload in ("", None, [], {}):
        return None

    if isinstance(payload, str):
        payload_text = payload
    else:
        normalized_payload = payload
        if isinstance(payload, dict) and isinstance(payload_meta, dict) and payload_meta:
            normalized_payload = {
                "_meta": {
                    str(key): value
                    for key, value in payload_meta.items()
                    if str(key or "").strip() and value not in ("", None, [], {})
                },
                **payload,
            }
        payload_text = json.dumps(normalized_payload, ensure_ascii=False)

    return {
        "attempt_key": attempt_key,
        "stage": int(stage),
        "ep_num": int(ep_num or 0),
        "payload_kind": payload_kind,
        "payload": payload_text,
    }


def persist_stage4_raw_rationale_records(
    *,
    project_db,
    records: list[dict[str, object]] | None,
    log_prefix: str = "Stage4",
) -> int:
    if not project_db or not hasattr(project_db, "save_attempt_raw_rationale"):
        return 0

    persisted = 0
    for record in records or []:
        if not isinstance(record, dict):
            continue
        attempt_key = str(record.get("attempt_key", "") or "").strip()
        payload_kind = str(record.get("payload_kind", "") or "").strip()
        if not attempt_key or not payload_kind:
            continue
        try:
            project_db.save_attempt_raw_rationale(**record)
            persisted += 1
        except Exception as exc:
            logging.warning("[%s] raw rationale sink write skipped: %s", log_prefix, exc)
    return persisted
