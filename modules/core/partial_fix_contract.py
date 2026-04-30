from __future__ import annotations

import hashlib
import json
import re
from typing import Any

_SCENE_ID_PATTERN = re.compile(r"^scene[_-][A-Za-z0-9_-]+$")
_FIELD_PATH_PATTERN = re.compile(r"^[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+$")


def _compact_text(value: object, *, limit: int) -> str:
    return " ".join(str(value or "").split()).strip()[:limit]


def _coerce_bool_or_none(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def _guess_scene_id(summary: str) -> str:
    normalized = _compact_text(summary, limit=80)
    return normalized if _SCENE_ID_PATTERN.match(normalized) else ""


def _guess_field_path(summary: str) -> str:
    normalized = _compact_text(summary, limit=120)
    return normalized if _FIELD_PATH_PATTERN.match(normalized) else ""


def _normalize_text_anchor(raw: object) -> dict[str, str]:
    if isinstance(raw, dict):
        payload = raw
    else:
        payload = {}
    old_text = _compact_text(payload.get("old_text"), limit=240)
    anchor_before = _compact_text(payload.get("anchor_before"), limit=240)
    anchor_after = _compact_text(payload.get("anchor_after"), limit=240)
    if not any((old_text, anchor_before, anchor_after)):
        return {}
    result: dict[str, str] = {}
    if old_text:
        result["old_text"] = old_text
    if anchor_before:
        result["anchor_before"] = anchor_before
    if anchor_after:
        result["anchor_after"] = anchor_after
    return result


def _normalize_paragraph_span(raw: object) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    try:
        start = int(raw.get("start", 0) or 0)
        end = int(raw.get("end", 0) or 0)
    except (TypeError, ValueError):
        return {}
    if start <= 0 or end <= 0 or end < start:
        return {}
    return {"start": start, "end": end}


def build_patch_target_id(record: dict[str, Any]) -> str:
    material = {
        "stage": str(record.get("stage") or "").strip(),
        "container_kind": str(record.get("container_kind") or "").strip(),
        "container_id": str(record.get("container_id") or "").strip(),
        "target_kind": str(record.get("target_kind") or "").strip(),
        "scene_id": str(record.get("scene_id") or "").strip(),
        "field_path": str(record.get("field_path") or "").strip(),
        "summary": str(record.get("summary") or "").strip(),
        "text_anchor": record.get("text_anchor") if isinstance(record.get("text_anchor"), dict) else {},
        "paragraph_span": record.get("paragraph_span") if isinstance(record.get("paragraph_span"), dict) else {},
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"pt:{hashlib.sha1(encoded.encode('utf-8')).hexdigest()[:12]}"


def _normalize_single_patch_target(
    item: object,
    *,
    stage: str,
    container_kind: str,
    container_id: str = "",
    default_target_kind: str = "",
) -> dict[str, Any]:
    if isinstance(item, dict):
        summary = _compact_text(item.get("summary") or item.get("target") or item.get("label"), limit=80)
        scene_id = _compact_text(item.get("scene_id"), limit=80)
        field_path = _compact_text(item.get("field_path"), limit=160)
        text_anchor = _normalize_text_anchor(item.get("text_anchor"))
        if not text_anchor and any(key in item for key in ("old_text", "anchor_before", "anchor_after")):
            text_anchor = _normalize_text_anchor(item)
        paragraph_span = _normalize_paragraph_span(item.get("paragraph_span"))
        target_kind = _compact_text(item.get("target_kind") or default_target_kind, limit=80)
        normalized_stage = _compact_text(item.get("stage") or stage, limit=24)
        normalized_container_kind = _compact_text(item.get("container_kind") or container_kind, limit=32)
        normalized_container_id = _compact_text(item.get("container_id") or container_id, limit=80)
    elif isinstance(item, str):
        summary = _compact_text(item, limit=80)
        scene_id = _guess_scene_id(summary)
        field_path = _guess_field_path(summary)
        text_anchor = {}
        paragraph_span = {}
        target_kind = _compact_text(default_target_kind, limit=80)
        normalized_stage = _compact_text(stage, limit=24)
        normalized_container_kind = _compact_text(container_kind, limit=32)
        normalized_container_id = _compact_text(container_id, limit=80)
    else:
        return {}

    if not summary and not scene_id and not field_path and not text_anchor:
        return {}

    record: dict[str, Any] = {
        "stage": normalized_stage or stage,
        "container_kind": normalized_container_kind or container_kind,
        "container_id": normalized_container_id,
        "target_kind": target_kind,
        "summary": summary or scene_id or field_path or "patch_target",
    }
    if scene_id:
        record["scene_id"] = scene_id
    if field_path:
        record["field_path"] = field_path
    if text_anchor:
        record["text_anchor"] = text_anchor
    if paragraph_span:
        record["paragraph_span"] = paragraph_span
    if isinstance(item, dict):
        if item.get("visible_markdown_headers_required") is False:
            record["visible_markdown_headers_required"] = False
        repair_guidance = _compact_text(item.get("repair_guidance"), limit=220)
        if repair_guidance:
            record["repair_guidance"] = repair_guidance
    record["patch_target_id"] = build_patch_target_id(record)
    return record


def normalize_patch_target_records(
    raw_targets: object,
    *,
    stage: str,
    container_kind: str,
    container_id: str = "",
    default_target_kind: str = "",
    limit: int = 6,
) -> tuple[list[str], list[dict[str, Any]]]:
    if isinstance(raw_targets, str | dict):
        items = [raw_targets]
    elif isinstance(raw_targets, list):
        items = list(raw_targets)
    else:
        items = []

    summaries: list[str] = []
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_summaries: set[str] = set()

    for item in items:
        record = _normalize_single_patch_target(
            item,
            stage=stage,
            container_kind=container_kind,
            container_id=container_id,
            default_target_kind=default_target_kind,
        )
        if not record:
            continue
        patch_target_id = str(record.get("patch_target_id") or "").strip()
        summary = str(record.get("summary") or "").strip()
        if patch_target_id and patch_target_id in seen_ids:
            continue
        if summary and summary not in seen_summaries:
            summaries.append(summary)
            seen_summaries.add(summary)
        records.append(record)
        if patch_target_id:
            seen_ids.add(patch_target_id)
        if len(records) >= limit:
            break
    return summaries, records


def normalize_guard_result(raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    status = _compact_text(raw.get("status"), limit=40)
    failure_key = _compact_text(raw.get("failure_key"), limit=80)
    result: dict[str, Any] = {}
    if status:
        result["status"] = status
    if failure_key:
        result["failure_key"] = failure_key
    for key in ("must_fix_resolved", "do_not_regress_held", "success_condition_met"):
        coerced = _coerce_bool_or_none(raw.get(key))
        if coerced is not None:
            result[key] = coerced
    return result


def normalize_repair_trace_entries(
    raw_entries: object,
    *,
    default_target_records: list[dict[str, Any]] | None = None,
    default_target_kind: str = "",
    guard_result: dict[str, Any] | None = None,
    limit: int = 6,
    excerpt_limit: int = 240,
) -> list[dict[str, Any]]:
    if isinstance(raw_entries, dict):
        entries = [raw_entries]
    elif isinstance(raw_entries, list):
        entries = list(raw_entries)
    else:
        entries = []

    records = list(default_target_records or [])
    normalized_guard_result = normalize_guard_result(guard_result)
    results: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for idx, entry in enumerate(entries[:limit]):
        if not isinstance(entry, dict):
            continue
        target_record = records[min(idx, len(records) - 1)] if records else {}
        target = _compact_text(entry.get("target") or target_record.get("summary"), limit=80)
        target_kind = _compact_text(
            entry.get("target_kind") or target_record.get("target_kind") or default_target_kind, limit=80
        )
        patch_target_id = _compact_text(entry.get("patch_target_id") or target_record.get("patch_target_id"), limit=32)
        old_excerpt = _compact_text(entry.get("old_excerpt"), limit=excerpt_limit)
        new_excerpt = _compact_text(entry.get("new_excerpt"), limit=excerpt_limit)
        why_changed = _compact_text(entry.get("why_changed"), limit=220)
        if not any((target, patch_target_id, old_excerpt, new_excerpt, why_changed)):
            continue
        dedupe_key = "::".join(part for part in (patch_target_id, target, old_excerpt, new_excerpt) if part)
        if dedupe_key and dedupe_key in seen_keys:
            continue
        trace: dict[str, Any] = {}
        if target:
            trace["target"] = target
        if target_kind:
            trace["target_kind"] = target_kind
        if patch_target_id:
            trace["patch_target_id"] = patch_target_id
        if old_excerpt:
            trace["old_excerpt"] = old_excerpt
        if new_excerpt:
            trace["new_excerpt"] = new_excerpt
        if why_changed:
            trace["why_changed"] = why_changed
        entry_guard_result = normalize_guard_result(entry.get("guard_result"))
        if entry_guard_result:
            trace["guard_result"] = entry_guard_result
        elif normalized_guard_result:
            trace["guard_result"] = dict(normalized_guard_result)
        results.append(trace)
        if dedupe_key:
            seen_keys.add(dedupe_key)
    return results


def build_partial_fix_eval(
    *,
    patch_round: object,
    is_patch_attempt: object,
    patch_target_records: list[dict[str, Any]] | None = None,
    target_kind: str = "",
    fallback_reason: object = "",
    must_fix_resolved: object = None,
    do_not_regress_held: object = None,
    success_condition_met: object = None,
) -> dict[str, Any]:
    try:
        normalized_patch_round = int(patch_round or 0)
    except (TypeError, ValueError):
        normalized_patch_round = 0
    normalized_patch_round = normalized_patch_round if normalized_patch_round > 0 else 1
    normalized_is_patch_attempt = bool(is_patch_attempt)
    primary_record = (patch_target_records or [{}])[0] if patch_target_records else {}
    patch_target_id = _compact_text(primary_record.get("patch_target_id"), limit=32)
    normalized_target_kind = _compact_text(target_kind or primary_record.get("target_kind"), limit=80)
    normalized_fallback_reason = _compact_text(fallback_reason, limit=80)
    payload = {
        "patch_round": normalized_patch_round,
        "is_patch_attempt": normalized_is_patch_attempt,
        "patch_target_id": patch_target_id,
        "target_kind": normalized_target_kind,
        "must_fix_resolved": _coerce_bool_or_none(must_fix_resolved),
        "do_not_regress_held": _coerce_bool_or_none(do_not_regress_held),
        "success_condition_met": _coerce_bool_or_none(success_condition_met),
        "fallback_reason": normalized_fallback_reason,
    }
    if (
        not normalized_is_patch_attempt
        and not patch_target_id
        and not normalized_target_kind
        and not normalized_fallback_reason
    ):
        return {}
    return payload
