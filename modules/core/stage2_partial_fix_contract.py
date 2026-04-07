from __future__ import annotations

from modules.core.partial_fix_contract import build_partial_fix_eval, normalize_patch_target_records


def _compact_stage2_fix_list(raw: object, *, limit: int = 6, item_limit: int = 180) -> list[str]:
    if isinstance(raw, str):
        items = [raw]
    elif isinstance(raw, list):
        items = list(raw)
    else:
        items = []

    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = " ".join(str(item or "").split()).strip()[:item_limit]
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
        if len(normalized) >= limit:
            break
    return normalized


def normalize_stage2_fix_pack(raw_payload: object, *, default_fix_instruction: str = "") -> dict:
    payload = raw_payload if isinstance(raw_payload, dict) else {}
    source = payload.get("fix_pack") if isinstance(payload.get("fix_pack"), dict) else payload
    if not isinstance(source, dict):
        source = {}

    target_kind = str(source.get("target_kind") or payload.get("target_kind") or "").strip()
    raw_targets = source.get("patch_target_records") or source.get("patch_targets")
    patch_targets, patch_target_records = normalize_patch_target_records(
        raw_targets,
        stage="stage2",
        container_kind="arc",
        container_id="stage2_arc",
        default_target_kind=target_kind or "tactical_section",
    )
    if not patch_target_records and default_fix_instruction:
        patch_targets, patch_target_records = normalize_patch_target_records(
            [{"summary": "Arc tactical_doc section", "target_kind": target_kind or "tactical_section"}],
            stage="stage2",
            container_kind="arc",
            container_id="stage2_arc",
            default_target_kind=target_kind or "tactical_section",
        )

    must_fix = _compact_stage2_fix_list(source.get("must_fix"), limit=6, item_limit=180)
    if not must_fix and default_fix_instruction:
        must_fix = _compact_stage2_fix_list(default_fix_instruction, limit=1, item_limit=180)
    do_not_regress = _compact_stage2_fix_list(source.get("do_not_regress"), limit=6, item_limit=180)
    success_condition = " ".join(str(source.get("success_condition", "") or "").split()).strip()[:220]
    if not success_condition and default_fix_instruction:
        success_condition = "Director-requested local Arc repair lands without broad arc rewrite."

    normalized: dict = {}
    if patch_targets:
        normalized["patch_targets"] = patch_targets
    if patch_target_records:
        normalized["patch_target_records"] = patch_target_records
    resolved_target_kind = target_kind or str((patch_target_records or [{}])[0].get("target_kind") or "").strip()
    if resolved_target_kind:
        normalized["target_kind"] = resolved_target_kind
    if must_fix:
        normalized["must_fix"] = must_fix
    if do_not_regress:
        normalized["do_not_regress"] = do_not_regress
    if success_condition:
        normalized["success_condition"] = success_condition
    return normalized


def build_stage2_fix_pack_guidance(fix_pack: dict | None) -> str:
    payload = fix_pack if isinstance(fix_pack, dict) else {}
    if not payload:
        return ""

    lines: list[str] = []
    patch_targets = list(payload.get("patch_targets") or [])
    if patch_targets:
        lines.append("- patch_targets: " + ", ".join(str(item) for item in patch_targets[:6]))
    patch_target_records = list(payload.get("patch_target_records") or [])
    if patch_target_records:
        record_lines: list[str] = []
        for record in patch_target_records[:3]:
            if not isinstance(record, dict):
                continue
            parts = [str(record.get("summary") or "").strip()]
            field_path = str(record.get("field_path") or "").strip()
            scene_id = str(record.get("scene_id") or "").strip()
            target_kind = str(record.get("target_kind") or "").strip()
            detail = ", ".join(part for part in (field_path, scene_id, target_kind) if part)
            if detail:
                parts.append(f"({detail})")
            text = " ".join(part for part in parts if part).strip()
            if text:
                record_lines.append(text)
        if record_lines:
            lines.append("- patch_target_records: " + " | ".join(record_lines))
    must_fix = list(payload.get("must_fix") or [])
    if must_fix:
        lines.append("- must_fix: " + " | ".join(str(item) for item in must_fix[:4]))
    do_not_regress = list(payload.get("do_not_regress") or [])
    if do_not_regress:
        lines.append("- do_not_regress: " + " | ".join(str(item) for item in do_not_regress[:4]))
    success_condition = str(payload.get("success_condition", "") or "").strip()
    if success_condition:
        lines.append("- success_condition: " + success_condition)
    if not lines:
        return ""
    return "[Stage2 partial-fix contract]\n" + "\n".join(lines)


def build_stage2_partial_fix_eval(
    *,
    fix_pack: dict | None,
    patch_round: int,
    verdict: str = "",
    fallback_reason: str = "",
) -> dict:
    payload = fix_pack if isinstance(fix_pack, dict) else {}
    patch_target_records = list(payload.get("patch_target_records") or [])
    target_kind = str(payload.get("target_kind", "") or "").strip()
    normalized_verdict = str(verdict or "").strip().upper()
    must_fix_resolved = None
    do_not_regress_held = None
    success_condition_met = None
    if normalized_verdict == "PASS":
        must_fix_resolved = True
        do_not_regress_held = True
        success_condition_met = True
    elif normalized_verdict == "PASS_WITH_FIX":
        must_fix_resolved = False
        success_condition_met = False
    elif normalized_verdict == "REJECT":
        must_fix_resolved = False
        do_not_regress_held = False
        success_condition_met = False
    return build_partial_fix_eval(
        patch_round=patch_round,
        is_patch_attempt=True,
        patch_target_records=patch_target_records,
        target_kind=target_kind,
        fallback_reason=fallback_reason,
        must_fix_resolved=must_fix_resolved,
        do_not_regress_held=do_not_regress_held,
        success_condition_met=success_condition_met,
    )
