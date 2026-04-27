from __future__ import annotations

from copy import deepcopy
from typing import Any

SUPPORTED_BLUEPRINT_PATCH_IR_TARGET_KINDS = {
    "dialogue",
    "entity_ref",
    "field_value",
    "local_phrase",
    "local_sentence",
}


def supports_blueprint_patch_ir(normalized_fix_pack: dict[str, Any] | None) -> bool:
    payload = normalized_fix_pack if isinstance(normalized_fix_pack, dict) else {}
    target_kind = str(payload.get("target_kind", "") or "").strip().lower()
    patch_target_records = list(payload.get("patch_target_records") or [])
    return bool(target_kind in SUPPORTED_BLUEPRINT_PATCH_IR_TARGET_KINDS and patch_target_records)


def explain_blueprint_patch_packet_failure(
    *,
    original_blueprint: dict[str, Any],
    normalized_fix_pack: dict[str, Any] | None,
) -> str:
    if not isinstance(original_blueprint, dict):
        return "invalid_original_blueprint"

    payload = normalized_fix_pack if isinstance(normalized_fix_pack, dict) else {}
    target_kind = str(payload.get("target_kind", "") or "").strip().lower()
    if target_kind not in SUPPORTED_BLUEPRINT_PATCH_IR_TARGET_KINDS:
        return "unsupported_target_kind" if target_kind else "missing_target_kind"

    patch_target_records = list(payload.get("patch_target_records") or [])
    if not patch_target_records:
        return "missing_patch_target_records"

    seen_target_ids: set[str] = set()
    for record in patch_target_records[:6]:
        if not isinstance(record, dict):
            return "invalid_patch_target_record"
        patch_target_id = str(record.get("patch_target_id") or "").strip()
        if not patch_target_id:
            return "missing_patch_target_id"
        if patch_target_id in seen_target_ids:
            return "duplicate_patch_target_id"
        seen_target_ids.add(patch_target_id)

        field_path = str(record.get("field_path") or "").strip()
        if not field_path:
            return "missing_field_path"
        found, _current_value = _resolve_path_value(original_blueprint, field_path)
        if not found:
            return "unresolved_field_path"

    return ""


def build_blueprint_patch_packet(
    *,
    original_blueprint: dict[str, Any],
    normalized_fix_pack: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(original_blueprint, dict):
        return {}

    payload = normalized_fix_pack if isinstance(normalized_fix_pack, dict) else {}
    if not supports_blueprint_patch_ir(payload):
        return {}

    target_kind = str(payload.get("target_kind", "") or "").strip().lower()
    patch_targets = list(payload.get("patch_targets") or [])
    patch_target_records = list(payload.get("patch_target_records") or [])
    must_fix = [str(item or "").strip() for item in list(payload.get("must_fix") or []) if str(item or "").strip()]
    do_not_regress = [
        str(item or "").strip() for item in list(payload.get("do_not_regress") or []) if str(item or "").strip()
    ]
    success_condition = str(payload.get("success_condition", "") or "").strip()

    target_snapshots: list[dict[str, Any]] = []
    for record in patch_target_records[:6]:
        if not isinstance(record, dict):
            return {}
        snapshot = _build_patch_target_snapshot(
            original_blueprint=original_blueprint, record=record, target_kind=target_kind
        )
        if not snapshot:
            return {}
        target_snapshots.append(snapshot)

    if not target_snapshots:
        return {}

    packet: dict[str, Any] = {
        "target_kind": target_kind,
        "patch_targets": list(patch_targets[:6]),
        "target_snapshots": target_snapshots,
    }
    if must_fix:
        packet["must_fix"] = must_fix[:6]
    if do_not_regress:
        packet["do_not_regress"] = do_not_regress[:6]
    if success_condition:
        packet["success_condition"] = success_condition[:220]
    return packet


def apply_blueprint_patch_ir(
    *,
    original_blueprint: dict[str, Any],
    patch_packet: dict[str, Any],
    patch_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(original_blueprint, dict) or not isinstance(patch_packet, dict):
        return None
    payload = patch_payload if isinstance(patch_payload, dict) else {}
    patch_values = payload.get("patch_values")
    if not isinstance(patch_values, list) or not patch_values:
        return None

    target_snapshots = list(patch_packet.get("target_snapshots") or [])
    if not target_snapshots:
        return None

    snapshot_by_id: dict[str, dict[str, Any]] = {}
    for snapshot in target_snapshots:
        if not isinstance(snapshot, dict):
            return None
        patch_target_id = str(snapshot.get("patch_target_id") or "").strip()
        field_path = str(snapshot.get("field_path") or "").strip()
        if not patch_target_id or not field_path:
            return None
        snapshot_by_id[patch_target_id] = snapshot

    if len(snapshot_by_id) != len(target_snapshots):
        return None

    patched_blueprint = deepcopy(original_blueprint)
    applied_ids: set[str] = set()

    for entry in patch_values[: len(target_snapshots)]:
        if not isinstance(entry, dict):
            return None
        patch_target_id = str(entry.get("patch_target_id") or "").strip()
        field_path = str(entry.get("field_path") or "").strip()
        if not patch_target_id or patch_target_id not in snapshot_by_id or patch_target_id in applied_ids:
            return None
        target_snapshot = snapshot_by_id[patch_target_id]
        expected_field_path = str(target_snapshot.get("field_path") or "").strip()
        if field_path and field_path != expected_field_path:
            return None
        new_value = entry.get("new_value")
        if not _is_valid_patch_value(new_value):
            return None
        if not _set_path_value(patched_blueprint, expected_field_path, deepcopy(new_value)):
            return None
        applied_ids.add(patch_target_id)

    if applied_ids != set(snapshot_by_id):
        return None
    if patched_blueprint == original_blueprint:
        return None
    return patched_blueprint


def _build_patch_target_snapshot(
    *,
    original_blueprint: dict[str, Any],
    record: dict[str, Any],
    target_kind: str,
) -> dict[str, Any]:
    field_path = str(record.get("field_path") or "").strip()
    patch_target_id = str(record.get("patch_target_id") or "").strip()
    if not field_path or not patch_target_id:
        return {}
    found, current_value = _resolve_path_value(original_blueprint, field_path)
    if not found:
        return {}

    snapshot: dict[str, Any] = {
        "patch_target_id": patch_target_id,
        "summary": str(record.get("summary") or "").strip()[:120],
        "field_path": field_path,
        "target_kind": str(record.get("target_kind") or target_kind or "").strip().lower(),
        "current_value": deepcopy(current_value),
    }
    scene_id = str(record.get("scene_id") or "").strip()
    if scene_id:
        snapshot["scene_id"] = scene_id
    text_anchor = record.get("text_anchor")
    if isinstance(text_anchor, dict) and text_anchor:
        snapshot["text_anchor"] = {
            key: str(value or "").strip()[:240] for key, value in text_anchor.items() if str(value or "").strip()
        }
    return snapshot


def _resolve_path_value(payload: dict[str, Any], field_path: str) -> tuple[bool, Any]:
    current: Any = payload
    for token in field_path.split("."):
        if isinstance(current, dict) and token in current:
            current = current[token]
            continue
        if isinstance(current, list) and token.isdigit():
            index = int(token)
            if 0 <= index < len(current):
                current = current[index]
                continue
        return False, None
    return True, current


def _set_path_value(payload: dict[str, Any], field_path: str, value: Any) -> bool:
    tokens = field_path.split(".")
    if not tokens:
        return False
    current: Any = payload
    for token in tokens[:-1]:
        if isinstance(current, dict) and token in current:
            current = current[token]
            continue
        if isinstance(current, list) and token.isdigit():
            index = int(token)
            if 0 <= index < len(current):
                current = current[index]
                continue
        return False

    last = tokens[-1]
    if isinstance(current, dict) and last in current:
        current[last] = value
        return True
    if isinstance(current, list) and last.isdigit():
        index = int(last)
        if 0 <= index < len(current):
            current[index] = value
            return True
    return False


def _is_valid_patch_value(value: Any) -> bool:
    if isinstance(value, str | int | float | bool) or value is None:
        return True
    if isinstance(value, list):
        return all(_is_valid_patch_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_valid_patch_value(item) for key, item in value.items())
    return False
