from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from modules.core.partial_fix_contract import normalize_patch_target_records

SUPPORTED_LOCAL_TARGET_KINDS = {"entity_ref", "local_phrase", "local_sentence"}


@dataclass
class LocalEditAttempt:
    success: bool
    manuscript: str = ""
    state_updates: dict[str, Any] | None = None
    failure_reason: str = ""
    operation_count: int = 0
    patch_target_records: list[dict[str, Any]] | None = None
    repair_trace: list[dict[str, Any]] | None = None


def supports_local_edit_fix_pack(normalized_fix_pack: dict[str, Any] | None) -> bool:
    payload = normalized_fix_pack if isinstance(normalized_fix_pack, dict) else {}
    target_kind = str(payload.get("target_kind", "") or "").strip()
    patch_targets = payload.get("patch_targets") or []
    return bool(target_kind in SUPPORTED_LOCAL_TARGET_KINDS and patch_targets)


def attempt_local_edit_patch(
    *,
    ask_fn: Callable[..., str],
    original_manuscript: str,
    director_feedback: str,
    style_guide: str,
    fix_pack_guidance: str,
    normalized_fix_pack: dict[str, Any],
) -> LocalEditAttempt:
    if not supports_local_edit_fix_pack(normalized_fix_pack):
        return LocalEditAttempt(success=False)

    prompt = _build_local_edit_prompt(
        original_manuscript=original_manuscript,
        director_feedback=director_feedback,
        style_guide=style_guide,
        fix_pack_guidance=fix_pack_guidance,
        normalized_fix_pack=normalized_fix_pack,
    )
    try:
        response = ask_fn(prompt, temperature=0.1, thinking_level="medium")
    except Exception as exc:
        logging.warning("[PWF-LOCAL] local op generation failed: %s", exc)
        return LocalEditAttempt(success=False, failure_reason="local_ops_exception")

    payload = _parse_local_edit_payload(response)
    if payload is None:
        return LocalEditAttempt(success=False, failure_reason="invalid_local_ops_payload")

    operations = payload.get("operations") or []
    state_updates = payload.get("patch_state_updates", {})
    if not isinstance(state_updates, dict):
        state_updates = {}
    patch_target_records = list(normalized_fix_pack.get("patch_target_records") or [])
    if not patch_target_records:
        _, patch_target_records = normalize_patch_target_records(
            normalized_fix_pack.get("patch_targets"),
            stage="stage4",
            container_kind="manuscript",
            default_target_kind=str(normalized_fix_pack.get("target_kind", "") or ""),
        )

    patched = original_manuscript
    repair_trace: list[dict[str, Any]] = []
    for idx, op in enumerate(operations, start=1):
        matched = _find_matching_spans(
            text=patched,
            old_text=op["old_text"],
            anchor_before=op.get("anchor_before", ""),
            anchor_after=op.get("anchor_after", ""),
        )
        patched = _apply_replace_operation(
            patched,
            op,
            target_kind=str(normalized_fix_pack.get("target_kind", "") or ""),
        )
        if patched is None or len(matched) != 1:
            return LocalEditAttempt(success=False, failure_reason=f"op_{idx}_apply_failed")
        target_record = patch_target_records[min(idx - 1, len(patch_target_records) - 1)] if patch_target_records else {}
        repair_trace.append(
            {
                "target": str(target_record.get("summary") or "").strip(),
                "target_kind": str(
                    target_record.get("target_kind") or normalized_fix_pack.get("target_kind") or ""
                ).strip(),
                "patch_target_id": str(target_record.get("patch_target_id") or "").strip(),
                "old_excerpt": str(op.get("old_text", "") or "").strip()[:240],
                "new_excerpt": str(op.get("new_text", "") or "").strip()[:240],
                "why_changed": " / ".join(
                    str(item or "").strip()
                    for item in list(normalized_fix_pack.get("must_fix") or [])[:2]
                    if str(item or "").strip()
                )[:220],
            }
        )

    if patched == original_manuscript:
        return LocalEditAttempt(success=False, failure_reason="no_local_change")

    return LocalEditAttempt(
        success=True,
        manuscript=patched,
        state_updates=state_updates,
        operation_count=len(operations),
        patch_target_records=patch_target_records,
        repair_trace=repair_trace,
    )


def _build_local_edit_prompt(
    *,
    original_manuscript: str,
    director_feedback: str,
    style_guide: str,
    fix_pack_guidance: str,
    normalized_fix_pack: dict[str, Any],
) -> str:
    target_kind = str(normalized_fix_pack.get("target_kind", "") or "")
    patch_targets = ", ".join(normalized_fix_pack.get("patch_targets") or [])
    return (
        "You are an exact local manuscript editor.\n"
        "Return JSON only. Do not rewrite the whole manuscript.\n"
        "Your job is to propose minimal replace operations that can be applied mechanically.\n\n"
        f"[target_kind]\n{target_kind}\n\n"
        f"[patch_targets]\n{patch_targets}\n\n"
        f"[style_guide]\n{style_guide}\n\n"
        f"[director_feedback]\n{director_feedback}\n\n"
        f"[fix_pack]\n{fix_pack_guidance}\n\n"
        "[rules]\n"
        "- Only use op=replace.\n"
        "- old_text must be an exact substring from the manuscript.\n"
        "- Use anchor_before and anchor_after to disambiguate if needed.\n"
        "- Keep edits local. Do not rewrite unaffected paragraphs.\n"
        "- Max 6 operations.\n\n"
        "[json_schema]\n"
        "{\n"
        '  "operations": [\n'
        "    {\n"
        '      "op": "replace",\n'
        '      "old_text": "...",\n'
        '      "new_text": "...",\n'
        '      "anchor_before": "...",\n'
        '      "anchor_after": "..."\n'
        "    }\n"
        "  ],\n"
        '  "patch_state_updates": {}\n'
        "}\n\n"
        f"[manuscript]\n{original_manuscript}"
    )


def _parse_local_edit_payload(response: str) -> dict[str, Any] | None:
    stripped = str(response or "").strip()
    if not stripped:
        return None
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        payload = json.loads(stripped)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    operations = payload.get("operations")
    if not isinstance(operations, list) or not operations:
        return None

    normalized_ops: list[dict[str, str]] = []
    for raw in operations[:6]:
        if not isinstance(raw, dict):
            return None
        if str(raw.get("op", "") or "").strip() != "replace":
            return None
        old_text = str(raw.get("old_text", "") or "").strip()
        new_text = str(raw.get("new_text", "") or "").strip()
        anchor_before = str(raw.get("anchor_before", "") or "")
        anchor_after = str(raw.get("anchor_after", "") or "")
        if not old_text or not new_text or old_text == new_text:
            return None
        normalized_ops.append(
            {
                "old_text": old_text,
                "new_text": new_text,
                "anchor_before": anchor_before,
                "anchor_after": anchor_after,
            }
        )
    payload["operations"] = normalized_ops
    return payload


def _apply_replace_operation(text: str, operation: dict[str, str], *, target_kind: str) -> str | None:
    old_text = operation["old_text"]
    new_text = operation["new_text"]
    if not _passes_local_span_guard(old_text=old_text, new_text=new_text, target_kind=target_kind):
        return None

    matches = _find_matching_spans(
        text=text,
        old_text=old_text,
        anchor_before=operation.get("anchor_before", ""),
        anchor_after=operation.get("anchor_after", ""),
    )
    if len(matches) != 1:
        return None
    start, end = matches[0]
    return text[:start] + new_text + text[end:]


def _find_matching_spans(
    *,
    text: str,
    old_text: str,
    anchor_before: str,
    anchor_after: str,
) -> list[tuple[int, int]]:
    matches: list[tuple[int, int]] = []
    cursor = 0
    while True:
        idx = text.find(old_text, cursor)
        if idx < 0:
            break
        end = idx + len(old_text)
        if _anchor_matches(text=text, start=idx, end=end, anchor_before=anchor_before, anchor_after=anchor_after):
            matches.append((idx, end))
        cursor = idx + 1
    return matches


def _anchor_matches(
    *,
    text: str,
    start: int,
    end: int,
    anchor_before: str,
    anchor_after: str,
) -> bool:
    before = str(anchor_before or "").strip()
    after = str(anchor_after or "").strip()
    if before:
        window = text[max(0, start - 240) : start]
        if before not in window:
            return False
    if after:
        window = text[end : min(len(text), end + 240)]
        if after not in window:
            return False
    return True


def _passes_local_span_guard(*, old_text: str, new_text: str, target_kind: str) -> bool:
    limits = {
        "entity_ref": (160, 240),
        "local_phrase": (240, 480),
        "local_sentence": (1200, 1800),
    }
    old_limit, new_limit = limits.get(target_kind, (1200, 1800))
    return len(old_text) <= old_limit and len(new_text) <= new_limit
