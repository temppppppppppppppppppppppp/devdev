"""
[Phase 4C-1a] Stage3Orchestrator — SovereignApp의 Stage 3 Blueprint 배치 생성 로직 캡슐화

원본: main_a.py:2855-3254 (_stage_3_batch_blueprinting, 400줄)

패턴: self.app = SovereignApp 인스턴스 (Stage2/4 Orchestrator와 동일)
V68 lazy init: state_tracker, world_state, fact_ledger를 self.app에 할당
"""

import json as _json
import logging as _logging
import re as _re
import time as _time
import traceback as _traceback
from dataclasses import dataclass

from modules.core.artifact_logging import build_candidate_key, normalize_artifact_meta, snapshot_logged_artifact
from modules.core.constants import Emojis, ErrorMessages, smart_truncate
from modules.core.context_advisor import (
    RetrievalSources,
    build_context_budget_ledger,
    build_context_observation,
)
from modules.core.continuity_pin_guard import apply_continuity_pins
from modules.core.fact_ledger import summarize_fact_ledger_numbers_block
from modules.core.logging_keys import build_attempt_key, resolve_logging_session_id
from modules.core.metrics_collector import get_metrics_collector
from modules.core.project_support import build_style_guide_summary, resolve_project_pov_contract
from modules.core.rationale_contract import (
    first_nonempty_text,
    resolve_comparison_notes_text,
    resolve_selection_reason_text,
    resolve_structured_advisory_payload,
    resolve_verdict_reason_text,
)
from modules.core.semantic_query_broker import SemanticQueryBroker
from modules.core.stage3_envelope_builder import Stage3EnvelopeBuilder
from modules.core.tactical_utils import extract_episode_tactical

try:
    from modules.utils.notifier import notifier
except Exception:  # notifier 미설치 시 비차단
    notifier = None

_DB_ADVISORY_NOTICE = "(Python 자동 감지 — 오탐 가능, 참고용)"
_STAGE3_HISTORY_RECENT_LIMIT = 24
_STAGE3_HISTORY_ANCHOR_LIMIT = 6
_STAGE3_HISTORY_CACHE_LIMIT = 36


@dataclass(slots=True)
class Stage3AttemptEvidencePacket:
    db: object
    attempt_num: int
    session_id: str
    attempt_key: str
    score: int
    selected_strategy: str
    candidate_key: str
    artifact_meta: dict
    selection_kwargs: dict | None
    runtime_advisory: str
    retry_directives: str


def _peek_scope_total_cost_usd() -> float:
    try:
        collector = get_metrics_collector()
        if collector is None or not hasattr(collector, "peek_scope"):
            return 0.0
        scope = collector.peek_scope() or {}
        return float(scope.get("total_cost_usd", 0.0) or 0.0)
    except Exception as exc:
        _logging.debug("[Stage3] metrics scope peek failed (non-blocking): %s", exc)
        return 0.0


def _normalize_semantic_source_counts(source_counts: dict | None) -> dict[str, int]:
    if not isinstance(source_counts, dict):
        return {}
    normalized: dict[str, int] = {}
    for key, value in source_counts.items():
        name = str(key or "").strip()
        if not name:
            continue
        try:
            count = int(value)
        except (TypeError, ValueError):
            continue
        if count > 0:
            normalized[name] = count
    return normalized


def _build_stage3_observability_flags(meta: dict | None) -> dict:
    if not isinstance(meta, dict):
        return {}
    source_counts = _normalize_semantic_source_counts(meta.get("source_counts"))
    coverage_warnings = [str(item).strip() for item in (meta.get("coverage_warnings") or []) if str(item or "").strip()]
    provenance_ledger = meta.get("provenance_ledger") if isinstance(meta.get("provenance_ledger"), dict) else {}
    budget_ledger = meta.get("budget_ledger") if isinstance(meta.get("budget_ledger"), dict) else {}
    source_anchor_summary = (
        meta.get("source_anchor_summary") if isinstance(meta.get("source_anchor_summary"), dict) else {}
    )
    episode_state_packet_summary = (
        meta.get("episode_state_packet_summary") if isinstance(meta.get("episode_state_packet_summary"), dict) else {}
    )
    prompt_envelope = meta.get("prompt_envelope") if isinstance(meta.get("prompt_envelope"), dict) else {}
    flags = {
        "semantic_ctx_chars": int(meta.get("semantic_ctx_chars") or 0),
        "semantic_ctx_sources": sorted(source_counts.keys()),
        "semantic_ctx_source_counts": source_counts,
        "coverage_warnings": coverage_warnings,
        "advisor_path_used": bool(meta.get("advisor_path_used", False)),
        "planned_slots_count": int(meta.get("planned_slots_count") or 0),
        "work_focus_present": bool(meta.get("work_focus_present", False)),
        "provenance_ledger": provenance_ledger,
        "budget_ledger": budget_ledger,
        "source_anchor_summary": source_anchor_summary,
        "episode_state_packet_summary": episode_state_packet_summary,
        "prompt_envelope": prompt_envelope,
    }
    return {key: value for key, value in flags.items() if value not in ("", [], {}, None, 0, False)}


def _first_stage3_text(*values: object) -> str:
    return first_nonempty_text(*values)


def _resolve_stage3_validate_rationale(
    validate: dict | None, pipeline_result: dict | None = None
) -> tuple[str, str, str]:
    validate = validate if isinstance(validate, dict) else {}
    pipeline_result = pipeline_result if isinstance(pipeline_result, dict) else {}
    selection_reason = resolve_selection_reason_text(
        validate.get("selection_reason", ""),
        validate.get("feedback", ""),
        validate.get("summary", ""),
    )
    verdict_reason = resolve_verdict_reason_text(
        validate.get("verdict_reason", ""),
        validate.get("feedback", ""),
        pipeline_result.get("error", ""),
        selection_reason,
    )
    comparison_notes = resolve_comparison_notes_text(validate.get("comparison_notes", ""))
    return selection_reason, verdict_reason, comparison_notes


def _build_stage3_fix_pack_retry_directives(validate: dict | None) -> str:
    if not isinstance(validate, dict):
        return ""
    fix_pack = validate.get("fix_pack")
    if not isinstance(fix_pack, dict):
        return ""
    chunks: list[str] = []
    for item in list(fix_pack.get("must_fix") or [])[:2]:
        text = str(item or "").strip()
        if text and text not in chunks:
            chunks.append(text)
    success_condition = str(fix_pack.get("success_condition", "") or "").strip()
    if success_condition:
        chunks.append(f"success_condition: {success_condition}")
    return " | ".join(chunks[:3])


def _resolve_stage3_runtime_advisory(
    pipeline_result: dict | None,
    selection_kwargs: dict | None = None,
    *,
    reject_reason: str = "",
) -> str:
    if not isinstance(pipeline_result, dict):
        pipeline_result = {}
    phases = pipeline_result.get("phases", {})
    validate = phases.get("validate", {}) if isinstance(phases, dict) else {}
    if not isinstance(validate, dict):
        validate = {}
    selection = selection_kwargs if isinstance(selection_kwargs, dict) else {}
    explicit = _first_stage3_text(
        pipeline_result.get("runtime_advisory", ""),
        validate.get("runtime_advisory", ""),
    )
    if explicit:
        return explicit
    final_verdict = str(pipeline_result.get("final_verdict", "") or "").strip().upper()
    has_runtime_risk = bool(
        pipeline_result.get("quality_gate_failed", False)
        or pipeline_result.get("quality_risk", False)
        or pipeline_result.get("revision_required", False)
        or validate.get("quality_risk", False)
        or validate.get("revision_required", False)
        or final_verdict in {"PASS_WITH_FIX", "PASS_WITH_WARNING", "REJECT", "ERROR"}
    )
    if not has_runtime_risk:
        return ""
    return _first_stage3_text(
        validate.get("open_review", ""),
        reject_reason,
        selection.get("verdict_reason", ""),
        selection.get("selection_reason", ""),
    )


def _resolve_stage3_retry_directives(
    pipeline_result: dict | None,
    selection_kwargs: dict | None = None,
    *,
    reject_reason: str = "",
) -> str:
    if not isinstance(pipeline_result, dict):
        pipeline_result = {}
    phases = pipeline_result.get("phases", {})
    validate = phases.get("validate", {}) if isinstance(phases, dict) else {}
    if not isinstance(validate, dict):
        validate = {}
    selection = selection_kwargs if isinstance(selection_kwargs, dict) else {}
    explicit = _first_stage3_text(
        pipeline_result.get("retry_directives", ""),
        validate.get("retry_directives", ""),
        selection.get("retry_directives", ""),
    )
    if explicit:
        return explicit
    final_verdict = str(pipeline_result.get("final_verdict", "") or "").strip().upper()
    needs_retry_guidance = bool(
        pipeline_result.get("revision_required", False)
        or validate.get("revision_required", False)
        or final_verdict in {"PASS_WITH_FIX", "REJECT", "ERROR"}
    )
    if not needs_retry_guidance:
        return ""
    return _first_stage3_text(
        _build_stage3_fix_pack_retry_directives(validate),
        validate.get("fix_scope_reasoning", ""),
        validate.get("open_review", ""),
        reject_reason if final_verdict in {"REJECT", "ERROR"} else "",
    )


def _clip_stage3_anchor_text(value: object, limit: int = 80) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _compact_stage3_contract_list(raw: object, *, limit: int = 4, item_limit: int = 120) -> list[str]:
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


def _compact_stage3_repair_contract(payload: object) -> dict:
    source = payload if isinstance(payload, dict) else {}
    compact = {
        "subtype": str(source.get("subtype", "") or "").strip(),
        "subtypes": _compact_stage3_contract_list(source.get("subtypes"), limit=4, item_limit=80),
        "fix_scope": str(source.get("fix_scope", "") or "").strip(),
        "repair_scope": str(source.get("repair_scope", "") or "").strip(),
        "authoritative_fix_scope": str(source.get("authoritative_fix_scope", "") or "").strip(),
        "provenance": str(source.get("provenance", "") or "").strip(),
        "provenance_sources": _compact_stage3_contract_list(source.get("provenance_sources"), limit=4, item_limit=120),
        "target_kind": str(source.get("target_kind", "") or "").strip(),
    }
    return {key: value for key, value in compact.items() if value not in ("", [], {}, None)}


def _compact_stage3_scope_authority(payload: object) -> dict:
    source = payload if isinstance(payload, dict) else {}
    compact = {
        "fix_scope": str(source.get("fix_scope", "") or "").strip(),
        "repair_scope": str(source.get("repair_scope", "") or "").strip(),
        "authoritative_fix_scope": str(source.get("authoritative_fix_scope", "") or "").strip(),
    }
    widened = source.get("widened")
    if isinstance(widened, bool):
        compact["widened"] = widened
    return {key: value for key, value in compact.items() if value not in ("", [], {}, None)}


def _build_stage3_anchor_inventory_preview(raw: object, *, limit: int = 3) -> list[str]:
    items = raw if isinstance(raw, list) else ([raw] if raw not in (None, "", []) else [])
    preview: list[str] = []
    for item in items[: max(0, int(limit or 0))]:
        if isinstance(item, dict):
            label = ""
            for key in ("name", "item", "label", "summary"):
                label = _clip_stage3_anchor_text(item.get(key, ""), 40)
                if label:
                    break
            if not label:
                label = _clip_stage3_anchor_text(_json.dumps(item, ensure_ascii=False), 40)
        else:
            label = _clip_stage3_anchor_text(item, 40)
        if label and label not in preview:
            preview.append(label)
    return preview


def _build_stage3_source_anchor_summary(arc_data: dict | None, blueprint_window: list | None) -> dict:
    arc_payload = arc_data if isinstance(arc_data, dict) else {}
    state_constraints = (
        arc_payload.get("state_constraints") if isinstance(arc_payload.get("state_constraints"), dict) else {}
    )
    joint_docs = arc_payload.get("joint_docs") if isinstance(arc_payload.get("joint_docs"), dict) else {}
    semantic_carryover = (
        arc_payload.get("semantic_carryover") if isinstance(arc_payload.get("semantic_carryover"), dict) else {}
    )
    start_state = (
        state_constraints.get("arc_start_state") if isinstance(state_constraints.get("arc_start_state"), dict) else {}
    )
    prev_blueprint = blueprint_window[-1] if isinstance(blueprint_window, list) and blueprint_window else {}
    if not isinstance(prev_blueprint, dict):
        prev_blueprint = {}
    arc_ep_start_raw = arc_payload.get("ep_start")
    try:
        arc_ep_start = int(arc_ep_start_raw) if arc_ep_start_raw not in (None, "") else 0
    except (TypeError, ValueError):
        arc_ep_start = 0

    start_location = _clip_stage3_anchor_text(start_state.get("location") or joint_docs.get("final_location") or "", 80)
    start_inventory = start_state.get("equipment", [])
    inventory_preview = _build_stage3_anchor_inventory_preview(start_inventory)
    inventory_count = len(start_inventory) if isinstance(start_inventory, list) else (1 if inventory_preview else 0)
    prev_end_location = _clip_stage3_anchor_text(
        prev_blueprint.get("end_location") or prev_blueprint.get("location") or "",
        80,
    )
    prev_transition = (
        prev_blueprint.get("opening_transition") if isinstance(prev_blueprint.get("opening_transition"), dict) else {}
    )
    semantic_keys = [str(key).strip() for key in semantic_carryover.keys() if str(key or "").strip()]
    continuity = semantic_carryover.get("continuity_checkpoints")

    summary: dict[str, object] = {}
    if isinstance(blueprint_window, list) and blueprint_window:
        summary["blueprint_window_count"] = len(blueprint_window)
    prev_ep = prev_blueprint.get("ep_num") or prev_blueprint.get("episode_number")
    if prev_ep not in (None, ""):
        summary["previous_blueprint_ep"] = prev_ep
    current_ep = 0
    if prev_ep not in (None, ""):
        try:
            current_ep = int(prev_ep) + 1
        except (TypeError, ValueError):
            current_ep = 0
    if not current_ep and arc_ep_start > 0:
        current_ep = arc_ep_start
    is_arc_opening_episode = bool(arc_ep_start > 0 and current_ep == arc_ep_start)
    if prev_end_location:
        summary["previous_blueprint_end_location"] = prev_end_location
    prev_transition_type = _clip_stage3_anchor_text(prev_transition.get("type", ""), 40)
    if prev_transition_type:
        summary["previous_blueprint_opening_transition_type"] = prev_transition_type
    if start_location and (is_arc_opening_episode or not prev_end_location):
        summary["current_arc_start_location"] = start_location
    if inventory_count and (is_arc_opening_episode or not prev_end_location):
        summary["current_arc_start_inventory_count"] = inventory_count
    if inventory_preview and (is_arc_opening_episode or not prev_end_location):
        summary["current_arc_start_inventory_preview"] = inventory_preview
    if semantic_keys:
        summary["semantic_carryover_keys"] = semantic_keys[:6]
    if isinstance(continuity, list) and continuity:
        summary["continuity_checkpoint_count"] = len(continuity)

    anchor_surfaces: list[str] = []
    if prev_end_location:
        anchor_surfaces.append("prev_blueprint_end_location")
    if prev_transition_type:
        anchor_surfaces.append("prev_blueprint_opening_transition")
    if start_location and (is_arc_opening_episode or not prev_end_location):
        anchor_surfaces.append("arc_start_location")
    if inventory_count and (is_arc_opening_episode or not prev_end_location):
        anchor_surfaces.append("arc_start_inventory")
    if semantic_keys:
        anchor_surfaces.append("semantic_carryover")
    if anchor_surfaces:
        summary["anchor_surfaces"] = anchor_surfaces

    return summary


def _format_stage3_source_anchor_summary(summary: dict | None) -> str:
    if not isinstance(summary, dict) or not summary:
        return ""
    parts: list[str] = []
    prev_ep = summary.get("previous_blueprint_ep")
    prev_location = str(summary.get("previous_blueprint_end_location", "") or "").strip()
    if prev_ep not in (None, "") or prev_location:
        parts.append(f"prev_ep={prev_ep or '-'}:{prev_location or '-'}")
    transition_type = str(summary.get("previous_blueprint_opening_transition_type", "") or "").strip()
    if transition_type:
        parts.append(f"prev_opening={transition_type}")
    start_location = str(summary.get("current_arc_start_location", "") or "").strip()
    if start_location:
        parts.append(f"start={start_location}")
    inventory_count = int(summary.get("current_arc_start_inventory_count") or 0)
    if inventory_count:
        parts.append(f"start_items={inventory_count}")
    return " | ".join(parts[:4])


def _select_stage3_anchor_recent_window(
    items: list | None,
    *,
    recent_limit: int = _STAGE3_HISTORY_RECENT_LIMIT,
    anchor_limit: int = _STAGE3_HISTORY_ANCHOR_LIMIT,
) -> list:
    """Keep a bounded recent tail plus a few older anchors in chronological order."""
    if not isinstance(items, list) or not items:
        return []

    safe_recent = max(1, int(recent_limit))
    safe_anchor = max(0, int(anchor_limit))
    total_limit = safe_recent + safe_anchor
    selected = list(items)
    if len(selected) <= total_limit:
        return selected

    recent = selected[-safe_recent:]
    older = selected[:-safe_recent]
    if not older or safe_anchor == 0:
        return recent

    if len(older) <= safe_anchor:
        anchors = older
    elif safe_anchor == 1:
        anchors = [older[0]]
    else:
        max_index = len(older) - 1
        anchor_indexes: list[int] = []
        for offset in range(safe_anchor):
            candidate = round(offset * max_index / (safe_anchor - 1))
            if not anchor_indexes or candidate != anchor_indexes[-1]:
                anchor_indexes.append(candidate)
        if len(anchor_indexes) < safe_anchor:
            for idx in range(len(older)):
                if idx in anchor_indexes:
                    continue
                anchor_indexes.append(idx)
                if len(anchor_indexes) == safe_anchor:
                    break
        anchors = [older[idx] for idx in sorted(anchor_indexes)]

    return anchors + recent


def _classify_stage3_failure_category(pipeline_result: dict) -> str | None:
    if not isinstance(pipeline_result, dict):
        return None

    verdict = str(pipeline_result.get("final_verdict", "") or "").upper()
    error_text = str(pipeline_result.get("error", "") or "").strip()
    if verdict == "ERROR" or error_text:
        return "generation_error"
    if pipeline_result.get("quality_gate_failed"):
        return "quality_gate"

    phases = pipeline_result.get("phases", {})
    validate = phases.get("validate", {}) if isinstance(phases, dict) else {}
    if isinstance(validate, dict):
        contradictions = validate.get("contradictions")
        if isinstance(contradictions, list) and contradictions:
            return "validation_contradiction"
        if validate.get("issues_count"):
            return "validation_issue"

    reject_reason = str(pipeline_result.get("reject_reason", "") or "")
    if "dead_npc_precheck" in reject_reason.lower():
        return "canonical_precheck"
    if "continuity" in reject_reason.lower():
        return "continuity"
    return "reject"


def _build_stage3_prompt_version() -> str | None:
    try:
        from modules.core.prompt_loader import PromptLoader

        return PromptLoader().compose_version_tag("ensemble", "blueprint_generator", "director")
    except Exception as _e:
        _logging.debug("[Stage3] prompt_version 계산 실패 (비차단): %s", _e)
        return None


def _build_stale_seed_advisory(db, next_ep: int) -> str:
    """장기 미회수 복선 경고를 Blueprint semantic_context용 문자열로 반환한다."""
    getter = getattr(db, "get_active_seeds", None)
    if not callable(getter):
        return ""

    try:
        seeds = getter()
        if not isinstance(seeds, list) or not seeds:
            return ""

        stale_seeds: list[str] = []
        for seed in seeds:
            if not isinstance(seed, dict):
                continue
            planted_ep = seed.get("planted_ep") or 0
            try:
                planted_ep = int(planted_ep)
            except (TypeError, ValueError):
                planted_ep = 0
            if planted_ep and (next_ep - planted_ep) >= 20:
                content = str(seed.get("content", "?") or "?")[:60]
                stale_seeds.append(f"  - {content} (ep{planted_ep}~ 미회수, {next_ep - planted_ep}화 경과)")

        if not stale_seeds:
            return ""
        return f"[DB-4 장기 미회수 복선] {_DB_ADVISORY_NOTICE}\n" + "\n".join(stale_seeds[:5])
    except Exception as seed_err:
        _logging.debug("[DB-4] foreshadow advisory 실패 (비치명): %s", seed_err)
        return ""


def _build_fact_ledger_advisory(db, *, max_items: int = 10) -> str:
    """Blueprint semantic_context용 핵심 수치 팩트 요약."""
    if db is None:
        return ""

    try:
        ledger = db.load_anchor("fact_ledger")
        return summarize_fact_ledger_numbers_block(
            ledger,
            header="[팩트 원장 핵심 수치]",
            max_items=max_items,
        )
    except Exception as fact_err:
        _logging.debug("[TF-DB-B1] Stage3 FactLedger advisory 실패 (비치명): %s", fact_err)
        return ""


def _build_world_state_advisory(world_state, *, max_chars: int = 1800) -> str:
    """Blueprint semantic_context용 compact WorldState 요약."""
    if world_state is None or not hasattr(world_state, "get_summary"):
        return ""

    try:
        summary = world_state.get_summary(max_chars=max_chars)
    except Exception as ws_err:
        _logging.debug("[CTX-P1-2] Stage3 WorldState advisory 실패 (비치명): %s", ws_err)
        return ""

    summary = str(summary or "").strip()
    if not summary:
        return ""
    return "[WorldState 핵심 요약]\n" + summary


def _build_style_guide_advisory(project, *, max_chars: int = 600) -> str:
    """Blueprint semantic_context용 compact StyleGuide 요약."""
    return build_style_guide_summary(
        project,
        heading="[StyleGuide 문체/anti-AI 참고]",
        max_chars=max_chars,
        include_dialogue_ratio=False,
        secondary_style_key="paragraph_style",
        secondary_style_label="문단 스타일",
        anti_ai_limit=6,
        forbidden_limit=5,
    )


def _compose_stage3_work_focus_text(
    *,
    arc_data: dict | None,
    prev_blueprints: list[dict] | None,
    entity_registry: dict | None,
) -> str:
    parts: list[str] = []
    if isinstance(arc_data, dict):
        for key in ("title", "summary", "block_theme", "tactical_doc", "arc_tactical", "constraint_summary"):
            value = str(arc_data.get(key, "") or "").strip()
            if value:
                parts.append(value)
        plot_suspension = arc_data.get("plot_suspension", []) or []
        if isinstance(plot_suspension, list) and plot_suspension:
            parts.append(" ".join(str(item).strip() for item in plot_suspension[:4] if str(item).strip()))

    if isinstance(prev_blueprints, list) and prev_blueprints:
        last_bp = prev_blueprints[-1] if isinstance(prev_blueprints[-1], dict) else {}
        if isinstance(last_bp, dict):
            for key in ("title", "ending_hook", "cliffhanger", "core_event"):
                value = str(last_bp.get(key, "") or "").strip()
                if value:
                    parts.append(value)

    if isinstance(entity_registry, dict):
        for values in entity_registry.values():
            if not isinstance(values, list):
                continue
            names: list[str] = []
            for item in values[:8]:
                if isinstance(item, dict):
                    name = str(item.get("name", "") or item.get("npc", "") or item.get("title", "")).strip()
                else:
                    name = str(item).strip()
                if name:
                    names.append(name)
            if names:
                parts.append(" ".join(names[:6]))

    combined = "\n".join(part for part in parts if part)
    return combined[:1800]


def _resolve_stage3_work_focus(
    ctx,
    *,
    arc_data: dict | None,
    prev_blueprints: list[dict] | None,
    entity_registry: dict | None,
) -> dict[str, object]:
    guard = getattr(getattr(ctx, "sys", None), "guard", None)
    if not guard or not hasattr(guard, "select_retrieval_focus"):
        return {}

    focus_text = _compose_stage3_work_focus_text(
        arc_data=arc_data,
        prev_blueprints=prev_blueprints,
        entity_registry=entity_registry,
    )
    if not focus_text:
        return {}

    try:
        focus = guard.select_retrieval_focus(stage="blueprint", focus_text=focus_text)
    except Exception as focus_err:
        _logging.debug("[Stage3] work_focus 선택 실패 (비치명): %s", focus_err)
        return {}

    return focus if isinstance(focus, dict) else {}


def _build_stage3_work_focus_advisory(
    work_focus: dict[str, object],
    *,
    arc_data: dict | None,
    entity_registry: dict | None,
    ctx,
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
        lines.append(f"- 이번 화 우선 tracking_slots: {', '.join(tracking_slots[:3])}")
    if scene_engines:
        lines.append(f"- 이번 화 scene engines: {', '.join(scene_engines[:2])}")
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

    if isinstance(entity_registry, dict):
        linked_parts: list[str] = []
        for label, key in (("인물", "characters"), ("아이템", "items"), ("플롯", "plots"), ("위치", "locations")):
            values = entity_registry.get(key) or []
            rendered: list[str] = []
            if isinstance(values, list):
                for item in values[:4]:
                    if isinstance(item, dict):
                        name = str(item.get("name", "") or item.get("npc", "") or item.get("title", "")).strip()
                    else:
                        name = str(item).strip()
                    if name:
                        rendered.append(name)
            if rendered:
                linked_parts.append(f"{label}={', '.join(rendered[:4])}")
        if linked_parts:
            lines.append(f"- 연동 엔티티: {' | '.join(linked_parts)}")

    if isinstance(arc_data, dict):
        conflict = str(arc_data.get("constraint_summary", "") or arc_data.get("block_theme", "") or "").strip()
        if conflict:
            lines.append(f"- 현재 갈등축: {conflict[:160]}")

    try:
        focus_text = " ".join(
            [
                ", ".join(tracking_slots),
                ", ".join(scene_engines),
                " ".join(str(profile.get("purpose", "") or "") for profile in registry_profiles),
                str((arc_data or {}).get("constraint_summary", "") or ""),
                str((arc_data or {}).get("block_theme", "") or ""),
            ]
        ).strip()
        broker = SemanticQueryBroker(
            db=getattr(getattr(ctx, "current_project", None), "db", None),
            world_state=getattr(ctx, "world_state", None),
            fact_ledger=getattr(ctx, "fact_ledger", None),
            state_tracker=getattr(ctx, "state_tracker", None),
            protagonist_name=protagonist_name,
        )
        relation_slice = broker.build_relation_slice(focus_text=focus_text, max_chars=420)
        if relation_slice:
            lines.append(relation_slice)
    except Exception as broker_err:
        _logging.debug("[Stage3] semantic relation slice 생성 실패 (비치명): %s", broker_err)

    text = "\n".join(lines)
    if len(text) > max_chars:
        return smart_truncate(
            text,
            max_chars=max_chars,
            head_chars=max(0, min(int(max_chars * 0.55), max_chars - 80)),
        )
    return text


def _build_stage3_relationship_context(db, *, npc_names: list[str], protagonist_name: str = "", limit: int = 6) -> str:
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
        except Exception as rel_err:
            _logging.debug("[Stage3] relationship history 조회 실패 (비치명): %s", rel_err)
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


def _summarize_retrieval_sources(plan) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not plan or not getattr(plan, "slots", None):
        return counts
    for slot in getattr(plan, "slots", []) or []:
        source = str(getattr(slot, "source", RetrievalSources.VEC_MEMORY) or RetrievalSources.VEC_MEMORY)
        counts[source] = counts.get(source, 0) + 1
    return counts


def _record_retrieval_observation(app, *, ep_num: int, stage: str, observation: dict) -> None:
    dashboard = getattr(app, "quality_dashboard", None)
    if dashboard is None or not hasattr(dashboard, "record_retrieval_observation"):
        return
    try:
        dashboard.record_retrieval_observation(ep_num=ep_num, stage=stage, observation=observation)
    except Exception as exc:
        _logging.debug("[Stage3] retrieval observation record failed: %s", exc)


class Stage3Orchestrator:
    """
    [Phase 4C-1a] SovereignApp의 Stage 3 Blueprint 배치 생성 로직 캡슐화

    패턴: self.app = SovereignApp 인스턴스
    """

    def __init__(self, app, *, context=None) -> None:
        """
        Args:
            app: SovereignApp 인스턴스 (레거시 호환)
            context: Stage3Context DI 컨텍스트 (미주입 시 자동 빌드)
        """
        self.app = app
        self._ctx = context  # [Phase 4C-4] DI 컨텍스트
        # [V61.6] Entity Registry 캐시 (Arc 단위)
        self._entity_cache_arc_idx = -1
        self._cached_entity_registry = None
        self._stage3_envelope_builder = Stage3EnvelopeBuilder(
            self,
            anchor_selector_fn=_select_stage3_anchor_recent_window,
            history_cache_limit=_STAGE3_HISTORY_CACHE_LIMIT,
        )

    @property
    def ctx(self):
        """[Phase 4C-4] DI 컨텍스트 (미주입 시 app에서 자동 빌드)"""
        if self._ctx is None:
            from modules.core.stage3_context import Stage3Context

            self._ctx = Stage3Context.from_app(self.app)
        return self._ctx

    @ctx.setter
    def ctx(self, value):
        self._ctx = value

    def _get_stage3_envelope_builder(self) -> Stage3EnvelopeBuilder:
        builder = getattr(self, "_stage3_envelope_builder", None)
        if builder is None:
            builder = Stage3EnvelopeBuilder(
                self,
                anchor_selector_fn=_select_stage3_anchor_recent_window,
                history_cache_limit=_STAGE3_HISTORY_CACHE_LIMIT,
            )
            self._stage3_envelope_builder = builder
        return builder

    def _set_agent_telemetry_context(self, *, ep_num: int | None = None) -> None:
        """[LOG-Phase2] BaseAgent llm_calls stage/ep 메타데이터 주입."""
        agents = getattr(self.ctx, "agents", None)
        if not isinstance(agents, dict):
            return

        _ep_value = None
        if ep_num is not None:
            try:
                _ep_value = max(0, int(ep_num))
            except (TypeError, ValueError):
                _ep_value = None

        # 서브 에이전트 포함 전체 순회
        _all_agents = list(agents.values())
        _three_phase_bp = agents.get("three_phase_bp")
        if _three_phase_bp is not None:
            _sub = getattr(_three_phase_bp, "ensemble", None)
            if _sub is not None:
                _all_agents.append(_sub)

        for agent in _all_agents:
            if agent is None:
                continue
            try:
                setattr(agent, "_current_stage", 3)
            except Exception:
                pass
            if _ep_value is not None:
                try:
                    setattr(agent, "_current_ep_num", _ep_value)
                except Exception:
                    pass

    # ─────────────────────────────────────────────────────────────
    # Stage 3 메인 진입점
    # ─────────────────────────────────────────────────────────────
    def stage_3_batch_blueprinting(self, *, target_ep: int | None = None) -> dict:
        """
        [V60.80] Stage 3 - Three Phase Blueprint Generator

        3단계 파이프라인: 제약수집 → 앙상블생성 → 통합검증
        - Phase 1: Constraint compilation (Arc 섹션 추출, 연속성, 정지선)
        - Phase 2: Ensemble generation (3개 후보 → 최적 선택)
        - Phase 3: Unified validation (Python + LLM)

        철학: "Arc를 충실히 따르는, 연속성 있는 Blueprint"
        """
        ctx = self.ctx

        if not ctx.current_project.arcs:
            ctx.ui.log(f"{Emojis.ERROR} {ErrorMessages.STAGE_PREREQUISITE_MISSING}")
            return {"success_count": 0, "fail_count": 0}

        # ═══════════════════════════════════════════════════════════════
        # [V60.96] StateTracker 초기화 (Stage 2에서 생성되지 않은 경우)
        # ═══════════════════════════════════════════════════════════════
        self._init_state_tracker_if_needed()

        # ═══════════════════════════════════════════════════════════════
        # [V68] WorldStateManager 초기화
        # ═══════════════════════════════════════════════════════════════
        self._init_world_state_if_needed()

        # ═══════════════════════════════════════════════════════════════
        # [V68] FactLedger 초기화
        # ═══════════════════════════════════════════════════════════════
        self._init_fact_ledger_if_needed()

        # [E-1b] Sync lazy-inited objects to ctx (getattr for safety if lazy init failed)
        ctx.state_tracker = getattr(self.app, "state_tracker", None)
        ctx.world_state = getattr(self.app, "world_state", None)
        ctx.fact_ledger = getattr(self.app, "fact_ledger", None)
        # [TF-35b] StateTracker → WorldState re-bind (init 순서 보정)
        if ctx.state_tracker and ctx.world_state:
            ctx.state_tracker.bind_world_state(ctx.world_state)

        # ═══════════════════════════════════════════════════════════════
        # 1. 목표 범위 설정
        # ═══════════════════════════════════════════════════════════════
        _last_arc = ctx.current_project.arcs[-1] if ctx.current_project.arcs else None
        total_planned_ep = _last_arc.get("ep_end", 50) if isinstance(_last_arc, dict) else 50

        # [V60.80 FIX] Blueprint 테이블 기준으로 시작점 결정
        existing_bp_max = ctx.current_project.db.get_latest_blueprint_number()  # 0 if empty

        # [Smart Skip] 기존 원고가 있다면 원고 기준으로도 체크
        latest_ep_fn = getattr(ctx.current_project, "get_latest_episode_number", None)
        if callable(latest_ep_fn):
            existing_ms_max_ep = max(0, int(latest_ep_fn() or 1) - 1)
        else:
            existing_ms_max_ep = (
                ctx.get_max_episode_from_manuscripts() if callable(ctx.get_max_episode_from_manuscripts) else 0
            )

        # 둘 중 큰 값을 기준으로 (Blueprint나 원고가 있는 화 다음부터)
        production_head = max(existing_bp_max, existing_ms_max_ep)

        if production_head > 0:
            ctx.ui.log(f"📂 [Detected] Blueprint {existing_bp_max}화, 원고 {existing_ms_max_ep}화까지 발견")
        else:
            ctx.ui.log("📂 [Fresh Start] 기존 데이터 없음 - 1화부터 시작")

        ctx.ui.log(f"📊 [V60.80] 현재 총 {total_planned_ep}화까지 설계가 가능합니다.")

        # [TF-CX-BUG-01] 입력 범위 역전 방어: 모든 블루프린트 이미 완료된 경우
        if production_head >= total_planned_ep:
            ctx.ui.log(f"✅ 이미 {production_head}화까지 완료되어 추가 생성할 범위가 없습니다.")
            ctx.ui.log("   💡 Stage 2에서 Arc를 추가하면 설계 범위가 늘어납니다.")
            return {"success_count": 0, "fail_count": 0}

        if target_ep is None:
            target_ep = (
                ctx.get_int_input(
                    f"👉 몇 화까지 설계도를 생성하시겠습니까? (현재 {production_head}화 / 최대 {total_planned_ep}화): ",
                    default=total_planned_ep,
                    min_val=production_head + 1,
                    max_val=total_planned_ep,
                )
                if callable(ctx.get_int_input)
                else total_planned_ep
            )
        # else: [OneStop] caller가 직접 target_ep 지정

        # ═══════════════════════════════════════════════════════════════
        # 2. 메인 에피소드 루프
        # ═══════════════════════════════════════════════════════════════
        working_ep = production_head + 1
        success_count = 0
        fail_count = 0
        prev_blueprints = []  # 연속성 검증용

        # [S3-1][S3-2] 최근 tail만 자르지 않고 older anchor도 남길 수 있게 약간 더 넓게 적재.
        for prev_ep in range(max(1, working_ep - _STAGE3_HISTORY_CACHE_LIMIT), working_ep):
            prev_bp = ctx.current_project.get_blueprint(prev_ep)
            if prev_bp:
                prev_blueprints.append(prev_bp)

        # [감리] target_ep < working_ep 방어 (이미 완료된 범위)
        if target_ep < working_ep:
            ctx.ui.log(f"✅ 이미 {target_ep}화까지 완료되어 추가 생성할 범위가 없습니다.")
            return {"success_count": 0, "fail_count": 0}

        ctx.ui.log(f"\n{'═' * 60}")
        ctx.ui.log("🎯 [V60.80] Three Phase Blueprint Generator 시작")
        ctx.ui.log(f"   범위: 제{working_ep}화 ~ 제{target_ep}화 ({target_ep - working_ep + 1}개)")
        ctx.ui.log(f"{'═' * 60}\n")

        completed_normally = True
        while working_ep <= target_ep:
            result = self._process_single_episode(working_ep, target_ep, prev_blueprints, success_count, fail_count)
            working_ep = result["next_ep"]
            success_count = result["success_count"]
            fail_count = result["fail_count"]
            if result.get("break"):
                completed_normally = False
                break

        # ═══════════════════════════════════════════════════════════════
        # 3. 완료 처리
        # ═══════════════════════════════════════════════════════════════
        if completed_normally and callable(ctx.write_audit_summary):
            ctx.write_audit_summary("stage3_complete")

        # 통계 출력
        ctx.ui.log(f"\n{'═' * 60}")
        ctx.ui.log("📊 [V60.80] Stage 3 완료 통계")
        ctx.ui.log(f"   성공: {success_count}개 | 실패: {fail_count}개")
        run_total = success_count + fail_count
        session_pass_rate = f"{(success_count / run_total * 100):.1f}%" if run_total > 0 else ""
        if session_pass_rate:
            ctx.ui.log(f"   이번 실행 통과율: {session_pass_rate}")
        if ctx.agents and hasattr(ctx.agents.get("three_phase_bp"), "get_stats"):
            stats = ctx.agents["three_phase_bp"].get_stats()
            cumulative_pass_rate = str(stats.get("pass_rate", "") or "").strip()
            if cumulative_pass_rate:
                if session_pass_rate and cumulative_pass_rate != session_pass_rate:
                    ctx.ui.log(f"   누적 통과율: {cumulative_pass_rate}")
                elif not session_pass_rate:
                    ctx.ui.log(f"   통과율: {cumulative_pass_rate}")
        ctx.ui.log(f"{'═' * 60}\n")

        # Slack 알림
        if success_count > 0 and notifier:
            try:
                notifier.send_notification(
                    title="✅ [V60.80 Blueprint] 설계도 생성 완료",
                    message=f"프로젝트: {ctx.current_project.name}\n성공: {success_count}개 | 실패: {fail_count}개",
                    key_metrics={"성공": f"{success_count}개", "실패": f"{fail_count}개"},
                )
            except Exception as slack_err:
                ctx.ui.log(f"⚠️ [Slack] 알림 전송 실패: {slack_err}")

        return {"success_count": success_count, "fail_count": fail_count}

    # ─────────────────────────────────────────────────────────────
    # V68 Lazy Init 헬퍼
    # ─────────────────────────────────────────────────────────────
    # [DOMAIN-STATE AUTHORITY — Stage 3 primary producer]
    # On the Stage 2→3→4 path, Stage 3 is the authoritative lazy-init source
    # for state_tracker / world_state / fact_ledger on self.app.
    # Stage 4 gateway (_stage_4_v2_chief_writer, V69.1) re-runs these checks
    # as a fallback for Stage-3-skip flows only.
    # Each method is idempotent: no-op when app already carries the attribute.
    # Stage 2 write-back (main_a.py _run_stage2_arc_async) may pre-populate
    # state_tracker only; world_state and fact_ledger belong here exclusively.
    def _init_state_tracker_if_needed(self) -> None:
        """[V60.96] StateTracker lazy init — app 인스턴스에 할당"""
        app = self.app
        if not hasattr(app, "state_tracker") or app.state_tracker is None:
            try:
                from modules.domain.agents.state_tracker import StateTracker

                app.state_tracker = StateTracker(preset_registry=app.preset_registry, llm_client=app.sys.api_client)
                app.state_tracker.bind_db(app.current_project.db)  # [NPC-L1] NPC 이력 DB 배선
                app.state_tracker.bind_world_state(getattr(app, "world_state", None))  # [TF-36] WorldState 배선
                all_arcs = app.current_project.db.load_anchor("arcs") or []
                _g = app.selected_genre.get("type", "") if app.selected_genre else ""
                app.state_tracker.full_extract_from_arcs(all_arcs, genre=_g)
                if app.state_tracker.npc_registry:
                    dead_count = sum(
                        1 for info in app.state_tracker.npc_registry.values() if info.get("status") == "dead"
                    )
                    app.ui.log(
                        f"      👤 [V60.96] StateTracker 초기화: NPC {len(app.state_tracker.npc_registry)}명 (사망: {dead_count}명)"
                    )
            except Exception as _st_err:
                # [Sweep54] sister 메서드(WorldState, FactLedger)와 동일한 비차단 패턴
                app.ui.log(f"      ⚠️ [V60.96] StateTracker 초기화 실패 (비차단): {str(_st_err)}")
                app.state_tracker = None

    def _init_world_state_if_needed(self) -> None:
        """[V68] WorldStateManager lazy init — app 인스턴스에 할당"""
        app = self.app
        if not hasattr(app, "world_state") or app.world_state is None:
            try:
                from modules.core.world_state import WorldStateManager

                app.world_state = WorldStateManager(app.current_project.db)
                _ws_ep = app.world_state.last_updated_ep
                if _ws_ep > 0:
                    app.ui.log(f"      🌍 [V68] WorldStateManager 로드 완료 (제{_ws_ep}화 기준)")
                else:
                    app.ui.log("      🌍 [V68] WorldStateManager 초기화 (신규)")
            except Exception as _ws_err:
                app.ui.log(f"      ⚠️ [V68] WorldStateManager 초기화 실패 (비차단): {str(_ws_err)}")
                app.world_state = None

    def _init_fact_ledger_if_needed(self) -> None:
        """[V68] FactLedger lazy init — app 인스턴스에 할당"""
        app = self.app
        if not hasattr(app, "fact_ledger") or app.fact_ledger is None:
            try:
                from modules.core.fact_ledger import FactLedger

                app.fact_ledger = FactLedger(app.current_project.db)
                _fl_ep = app.fact_ledger.last_updated_ep
                if _fl_ep > 0:
                    _fl_stats = app.fact_ledger.get_stats()
                    app.ui.log(
                        f"      📋 [V68] 팩트 원장 로드 완료 (제{_fl_ep}화 기준, 인물 {_fl_stats.get('characters', 0)}명, 아이템 {_fl_stats.get('items', 0)}개)"
                    )
                else:
                    app.ui.log("      📋 [V68] 팩트 원장 초기화 (신규)")
            except Exception as _fl_err:
                app.ui.log(f"      ⚠️ [V68] 팩트 원장 초기화 실패 (비차단): {str(_fl_err)}")
                app.fact_ledger = None

    # ─────────────────────────────────────────────────────────────
    # 에피소드 단위 처리
    # ─────────────────────────────────────────────────────────────
    def _process_single_episode(
        self,
        working_ep: int,
        target_ep: int,
        prev_blueprints: list,
        success_count: int,
        fail_count: int,
    ) -> dict:
        """단일 에피소드 Blueprint 생성 처리. 루프 상태를 dict로 반환."""
        ctx = self.ctx

        # 이미 설계도가 존재하면 스킵 — [Sweep54] prev_blueprints에도 추가 (연속성 gap 방지)
        _existing_bp = ctx.current_project.get_blueprint(working_ep)
        if _existing_bp:
            prev_blueprints.append(_existing_bp)
            if len(prev_blueprints) > _STAGE3_HISTORY_CACHE_LIMIT:
                prev_blueprints[:] = prev_blueprints[-_STAGE3_HISTORY_CACHE_LIMIT:]
            ctx.ui.log(f"   ⏭️  제{working_ep}화 - 기존 설계도 존재, 스킵")
            return {"next_ep": working_ep + 1, "success_count": success_count, "fail_count": fail_count}

        # [V60.83] 직전 화 Blueprint 필수 체크 (연속성 보장)
        if working_ep > 1:
            prev_bp_check = ctx.current_project.get_blueprint(working_ep - 1)
            if not prev_bp_check:
                ctx.ui.log(f"🚨 [V60.83] 제{working_ep - 1}화 Blueprint 없음! 연속성 보장 불가.")
                ctx.ui.log(f"   → 제{working_ep - 1}화를 먼저 생성하세요.")
                if callable(ctx.audit_event):
                    ctx.audit_event(
                        "continuity_block",
                        f"ep_{working_ep}_blocked_no_prev",
                        {"blocked_ep": working_ep, "missing_ep": working_ep - 1},
                    )
                return {"next_ep": working_ep, "success_count": success_count, "fail_count": fail_count, "break": True}

        # Arc 컨텍스트 확보
        if callable(ctx.get_arc_context_for_episode):
            arc_idx, arc_data = ctx.get_arc_context_for_episode(working_ep)
        else:
            arc_idx, arc_data = 0, {}
        if arc_idx is None or arc_data is None:
            ctx.ui.log(f"❌ [V60.80] 제{working_ep}화의 Arc 컨텍스트를 찾을 수 없습니다.")
            return {"next_ep": working_ep, "success_count": success_count, "fail_count": fail_count, "break": True}

        ep_start_val = arc_data.get("ep_start")
        if ep_start_val is None or not isinstance(ep_start_val, int):
            ctx.ui.log(f"⚠️ [Stop] Arc ep_start 누락: arc_idx={arc_idx}")
            if callable(ctx.audit_event):
                ctx.audit_event("data_missing", "arc ep_start missing", {"arc_idx": arc_idx})
            return {"next_ep": working_ep, "success_count": success_count, "fail_count": fail_count, "break": True}

        # Arc 데이터 검증
        arc_data_validated = (
            ctx.validate_arc_data_fields(arc_data, arc_idx)
            if callable(getattr(ctx, "validate_arc_data_fields", None))
            else None
        )
        if arc_data_validated:
            arc_data = arc_data_validated

        arc_no = arc_data.get("arc_no", arc_idx + 1)

        # Entity Registry 추출/캐시
        entity_registry_for_stage3 = self._get_entity_registry(arc_idx)

        # 직전 Blueprint 로드
        prev_blueprint = self._load_prev_blueprint(working_ep)

        # 주인공 이름 추출
        protagonist_name_for_stage3 = self._get_protagonist_name_safe()

        # Three Phase Blueprint Generation
        ctx.ui.log(
            f"\n   📐 제{working_ep}화 Blueprint 생성 중... (Arc {arc_no}, 주인공: {protagonist_name_for_stage3})"
        )
        self._set_agent_telemetry_context(ep_num=working_ep)

        # [V67.1] protagonist_config 추출
        _bp_protagonist_config = {}
        try:
            _bp_bible_root = ctx.current_project.master_bible.get("MasterBible", ctx.current_project.master_bible)
            _bp_protagonist_config = _bp_bible_root.get("protagonist_config", {})
        except Exception as _e:
            _logging.warning("[Stage3] protagonist_config 추출 실패 (기본값 사용): %s", _e)

        blueprint, pipeline_result = self._generate_blueprint(
            working_ep,
            arc_data,
            arc_idx,
            prev_blueprint,
            prev_blueprints,
            entity_registry_for_stage3,
            protagonist_name_for_stage3,
            _bp_protagonist_config,
        )

        # 결과 처리
        if blueprint and pipeline_result.get("final_verdict") in (
            "PASS",
            "PASS_WITH_WARNING",
            "PASS_WITH_FIX",
        ):  # [TF-32-S3]
            return self._handle_success(
                working_ep, arc_no, arc_data, blueprint, pipeline_result, prev_blueprints, success_count, fail_count
            )
        else:
            return self._handle_failure(
                working_ep,
                pipeline_result,
                success_count,
                fail_count,
                arc_no=arc_no,
                blueprint=blueprint,
            )

    # ─────────────────────────────────────────────────────────────
    # Entity Registry 캐시
    # ─────────────────────────────────────────────────────────────
    def _get_entity_registry(self, arc_idx: int):
        """[V61.6] Arc 단위 Entity Registry 캐시 관리"""
        ctx = self.ctx

        if self._entity_cache_arc_idx != arc_idx:
            ctx.ui.log(f"      ⏳ Entity Registry 추출 중... (Arc {arc_idx}, 첫 호출)")
            try:
                if ctx.agents and "state_extractor" in ctx.agents and ctx.current_project.arcs:
                    all_arcs_for_entity = list(ctx.current_project.arcs)[: arc_idx + 1]
                    if all_arcs_for_entity:
                        state_for_entity = ctx.agents["state_extractor"].extract_cumulative_state(all_arcs_for_entity)
                        self._cached_entity_registry = (
                            state_for_entity.get("entity_registry") if state_for_entity else None
                        )
                        if self._cached_entity_registry:
                            stage3_protag = ctx.get_protagonist_name() if callable(ctx.get_protagonist_name) else ""
                            if callable(getattr(ctx, "fix_entity_registry_protagonist", None)):
                                self._cached_entity_registry = ctx.fix_entity_registry_protagonist(
                                    self._cached_entity_registry, stage3_protag
                                )
                            total_entities = sum(
                                len(v) for v in self._cached_entity_registry.values() if isinstance(v, list)
                            )
                            ctx.ui.log(f"      📋 [V61] Entity Registry 추출: {total_entities}개 엔티티")
                    else:
                        self._cached_entity_registry = None
                else:
                    self._cached_entity_registry = None
                self._entity_cache_arc_idx = arc_idx
            except Exception as entity_err:
                ctx.ui.log(f"      ⚠️ [V61] Entity Registry 추출 실패: {str(entity_err)}")
                self._cached_entity_registry = None
                # [P0] 실패한 arc_idx 캐싱 — 동일 arc 무한 재시도 방지
                self._entity_cache_arc_idx = arc_idx
        else:
            ctx.ui.log(f"      ♻️ [V61.6] Entity Registry 캐시 재사용 (Arc {arc_idx})")

        return self._cached_entity_registry

    def _load_prev_blueprint(self, working_ep: int):
        """직전 Blueprint 로드 [V61.3 보호]"""
        prev_blueprint = None
        try:
            prev_blueprint = self.ctx.current_project.get_blueprint(working_ep - 1) if working_ep > 1 else None
        except Exception as prev_bp_err:
            _logging.error(f" [V61.3] prev_blueprint 로드 크래시: {str(prev_bp_err)}")
            _logging.error(_traceback.format_exc())
            self.ctx.ui.log("      ⚠️ 직전 Blueprint 로드 실패, None으로 진행")
        # [C3-P1-5] prev_blueprint 미존재 시 경고 강화
        if prev_blueprint is None and working_ep > 1:
            _logging.warning("[Stage3] prev_blueprint is None for ep %d (ep>1) — 연속성 참조 없이 진행", working_ep)
            self.ctx.ui.log(f"      ⚠️ 제{working_ep - 1}화 Blueprint 없음 — 연속성 참조 없이 진행")
        return prev_blueprint

    def _get_protagonist_name_safe(self) -> str:
        """주인공 이름 추출 [V61.3 보호] [C4-P1-3] callable 사전 검사"""
        protagonist_name = "주인공"
        if callable(getattr(self.ctx, "get_protagonist_name", None)):
            try:
                protagonist_name = self.ctx.get_protagonist_name()
            except Exception as protag_err:
                _logging.error(f" [V61.3] protagonist_name 추출 크래시: {str(protag_err)}")
                _logging.error(_traceback.format_exc())
                self.ctx.ui.log("      ⚠️ 주인공 이름 추출 실패, 기본값 사용")
        else:
            _logging.debug("[C4-P1-3] ctx.get_protagonist_name이 callable이 아님 — 기본값 사용")
        return protagonist_name

    def _extract_arc_time_markers(self, arc_data: dict) -> list:
        """[NS-4] Arc tactical_doc에서 시간 마커 추출 (regex, LLM 0회)"""
        import re as _re

        _tactical = arc_data.get("tactical_doc") or ""
        _beats = arc_data.get("beat_sequence") or ""
        if isinstance(_beats, list):
            _beats = " ".join(str(b) for b in _beats)
        _text = str(_tactical) + "\n" + str(_beats)
        _patterns = [
            r"\d{4}년\s*\d{1,2}월(?:\s*\d{1,2}일)?",  # 2006년 7월 12일  # utf8-hygiene: allow-line regex optional quantifier
            r"\d{1,2}월\s*\d{1,2}일",  # 7월 12일
            r"\d{1,2}월(?:\s*(?:말|초|중순|하순|상순))?",  # 5월 말  # utf8-hygiene: allow-line regex optional quantifier
            r"\d+(?:일|주|달|개월|년)\s*(?:후|전)",  # 2달 후  # utf8-hygiene: allow-line regex optional quantifier
        ]
        _found = []
        for _p in _patterns:
            _found.extend(_re.findall(_p, _text))
        return list(dict.fromkeys(_found))[:5]

    def _extract_timeline_start_end(self, arc_data: dict) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
        """[NS-4] state_changes.timeline의 시작/종료 시점(연,월) 추출."""
        import re as _re

        def _parse_point(raw, *, pick: str) -> tuple[int, int] | None:
            if isinstance(raw, dict):
                year = raw.get("year")
                month = raw.get("month")
                if year is not None and month is not None:
                    try:
                        return (int(year), int(month))
                    except (TypeError, ValueError):
                        return None
                return None

            text = str(raw or "").strip()
            if not text:
                return None
            _year_m = _re.search(r"(\d{4})년", text)
            _year = int(_year_m.group(1)) if _year_m else 0
            _months = [int(m) for m in _re.findall(r"(\d{1,2})월", text)]
            if not _months:
                return None
            _month = _months[0] if pick == "start" else _months[-1]
            return (_year, _month)

        timeline = arc_data.get("state_changes", {}).get("timeline", {})
        if not isinstance(timeline, dict):
            return None, None
        return _parse_point(timeline.get("start"), pick="start"), _parse_point(timeline.get("end"), pick="end")

    def _timeline_start_end_raw_equal(self, arc_data: dict) -> bool:
        """[NS-4] timeline.start/end가 사실상 동일 표현인지 확인."""
        timeline = arc_data.get("state_changes", {}).get("timeline", {})
        if not isinstance(timeline, dict):
            return False
        start_raw = timeline.get("start")
        end_raw = timeline.get("end")
        if not start_raw or not end_raw:
            return False
        return str(start_raw).strip() == str(end_raw).strip()

    # ─────────────────────────────────────────────────────────────
    # Blueprint 생성 (LLM 호출)
    # ─────────────────────────────────────────────────────────────
    def _collect_stage3_smart_retrieval_bundle(
        self,
        *,
        working_ep,
        arc_data,
        prev_blueprints,
        entity_registry,
        protagonist_name,
    ) -> dict[str, object]:
        ctx = self.ctx
        _bp_semantic_ctx = ""
        _s3_work_focus: dict[str, object] = {}
        _s3_plan = None

        try:
            _s3_memory = getattr(ctx, "memory", None)
            _s3_advisor = getattr(ctx, "context_advisor", None)
            _s3_genre = ""
            if getattr(ctx, "selected_genre", None):
                _s3_genre = ctx.selected_genre.get("type", "")

            from modules.validation.threshold_helper import _threshold as _s3_th

            _s3_sc_enabled = bool(_s3_th("smart_retrieval.enabled", False)) and bool(
                _s3_th("smart_retrieval.stage3_enabled", False)
            )
            if _s3_sc_enabled and _s3_advisor and _s3_memory:
                _s3_npc_roster = []
                if entity_registry and isinstance(entity_registry, dict):
                    for _cat_items in entity_registry.values():
                        if isinstance(_cat_items, list):
                            for _item in _cat_items[:10]:
                                _name = _item.get("name", "") if isinstance(_item, dict) else str(_item)
                                if _name and _name not in _s3_npc_roster:
                                    _s3_npc_roster.append(_name)

                _s3_work_focus = _resolve_stage3_work_focus(
                    ctx,
                    arc_data=arc_data,
                    prev_blueprints=prev_blueprints,
                    entity_registry=entity_registry,
                )
                _s3_plan = _s3_advisor.plan_stage3_retrieval(
                    arc_data=arc_data,
                    prev_blueprints=prev_blueprints,
                    current_ep=working_ep,
                    npc_roster=_s3_npc_roster[:10],
                    genre=_s3_genre,
                    work_focus=_s3_work_focus,
                )
                _s3_parts = []
                _s3_max_results = int(_s3_th("context.vector_max_results_s4", 50))
                for _slot in getattr(_s3_plan, "slots", []) or []:
                    _slot_query = str(getattr(_slot, "query", "") or "").strip()
                    if not _slot_query:
                        continue
                    _slot_source = str(getattr(_slot, "source", "vec_memory") or "vec_memory")
                    _slot_category = str(getattr(_slot, "category", "stage3") or "stage3")
                    _slot_max = int(getattr(_slot, "max_chars", 0) or 0) or 2000
                    try:
                        if _slot_source == "db_npc_history" and hasattr(_s3_memory, "retrieve_npc_context"):
                            _s3_text = _s3_memory.retrieve_npc_context(
                                npc_names=_s3_npc_roster[:5],
                                current_ep=working_ep,
                                max_results=_s3_max_results,
                            )
                        elif _slot_source == "db_npc_relationship":
                            _s3_text = _build_stage3_relationship_context(
                                getattr(ctx.current_project, "db", None),
                                npc_names=_s3_npc_roster[:6],
                                protagonist_name=protagonist_name,
                            )
                        else:
                            _s3_text = _s3_memory.retrieve_multi_query_context(
                                queries=[_slot_query],
                                current_ep=working_ep,
                                n_per_query=3,
                                max_results=_s3_max_results,
                            )
                        if _s3_text:
                            _s3_parts.append(
                                f"[SC:{_slot_category}]\n"
                                + smart_truncate(
                                    str(_s3_text),
                                    max_chars=_slot_max,
                                    head_chars=max(0, min(int(_slot_max * 0.55), _slot_max - 80)),
                                )
                            )
                    except Exception as _s3_slot_err:
                        _logging.warning("[SilentPass:SC:Stage3] 슬롯 %s 실패: %s", _slot_category, _s3_slot_err)
                if _s3_parts:
                    _bp_semantic_ctx = "\n\n".join(_s3_parts)
                    _logging.info("[S3-I1] Stage3 SC 검색 완료: %d건, %d자", len(_s3_parts), len(_bp_semantic_ctx))
        except Exception as _s3_sc_err:
            _logging.warning("[SilentPass:SC:Stage3] SC 검색 실패 (비차단): %s", _s3_sc_err)

        return {
            "semantic_ctx": _bp_semantic_ctx,
            "work_focus": _s3_work_focus,
            "plan": _s3_plan,
        }

    def _inject_stage3_treatment_block_context(self, *, semantic_ctx: str, working_ep, arc_data, arc_idx: int) -> str:
        _bp_semantic_ctx = semantic_ctx
        try:
            _master_bible = getattr(self.ctx.current_project, "master_bible", None) or {}
            _bible_root = _master_bible.get("MasterBible", _master_bible)
            _plot_roadmap = _bible_root.get("plot_roadmap", [])
            if isinstance(_plot_roadmap, list) and 0 <= arc_idx < len(_plot_roadmap):
                _block = _plot_roadmap[arc_idx]
                if isinstance(_block, dict):
                    _ep_start = arc_data.get("ep_start", working_ep)
                    _ep_end = arc_data.get("ep_end", working_ep)
                    _block_fields = []
                    # [W1] Arc 개요 필드만 허용 — per-episode 이벤트 필드 제거
                    for _f in (
                        "title",
                        "emotional_beat",
                        "foreshadow",
                    ):
                        if _block.get(_f):
                            _block_fields.append(f"  {_f}: {_block[_f]}")
                    _content = _block.get("content", {})
                    if isinstance(_content, dict):
                        # [W1] content.context만 허용, event_villain/solution 제거
                        for _cf in ("context",):
                            if _content.get(_cf):
                                _block_fields.append(f"  content.{_cf}: {_content[_cf]}")
                    _genre_ext = _block.get("genre_ext", {})
                    if isinstance(_genre_ext, dict) and _genre_ext:
                        _ge_lines = []
                        for _gk, _gv in _genre_ext.items():
                            if isinstance(_gv, dict | list):
                                _ge_lines.append(f"    {_gk}: {_json.dumps(_gv, ensure_ascii=False)}")
                            else:
                                _ge_lines.append(f"    {_gk}: {_gv}")
                        _block_fields.append("  genre_ext:\n" + "\n".join(_ge_lines))
                    if _block_fields:
                        # [W1] 강화된 구조적 가드 — 이벤트 필드 제거 후 방향성만 주입
                        _tb_header = (
                            f"[Arc 개요 — 아크 {_ep_start}~{_ep_end}화 방향성 참조]\n"
                            f"⚠️ 현재 화는 {working_ep}화입니다. "
                            f"아래는 아크 전체의 제목·감정선·복선만 제공합니다. "
                            f"구체적 사건(빌런 등장, 해결책, 보상, 전력 변화)은 제거되었습니다. "
                            f"현재 화의 구체적 내용은 arc_focus와 MUST_FOCUS를 기준으로 작성하세요."
                        )
                        _tb_text = _tb_header + "\n" + "\n".join(_block_fields)
                        _bp_semantic_ctx = _tb_text + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")
                        _logging.info(
                            "[TF9] Treatment Block 주입 완료 (arc_idx=%d, ep=%d~%d, %d자)",
                            arc_idx,
                            _ep_start,
                            _ep_end,
                            len(_tb_text),
                        )
        except Exception as _tb_err:
            _logging.warning("[SilentPass:TreatmentBlock] 추출 실패 (비차단): %s", _tb_err)

        return _bp_semantic_ctx

    def _inject_stage3_timeline_advisory(self, *, semantic_ctx: str, arc_idx: int, arc_data) -> str:
        _bp_semantic_ctx = semantic_ctx
        try:
            if arc_idx > 0:
                _all_arcs = getattr(self.ctx.current_project, "arcs", []) or []
                if len(_all_arcs) >= arc_idx:
                    _prev_arc_data = _all_arcs[arc_idx - 1]
                    _prev_markers = self._extract_arc_time_markers(_prev_arc_data)
                    _cur_markers = self._extract_arc_time_markers(arc_data)
                    if _prev_markers or _cur_markers:
                        _ta_lines = ["[Arc 시간 연속성 참고]"]
                        if _prev_markers:
                            _ta_lines.append(f"이전 Arc 종료 시점 마커: {', '.join(_prev_markers)}")
                        if _cur_markers:
                            _ta_lines.append(f"현재 Arc 시간 마커: {', '.join(_cur_markers)}")
                        if self._timeline_start_end_raw_equal(arc_data):
                            _ta_lines.append(
                                "⚠️ [NS-4] 현재 Arc timeline.start와 end가 동일하게 기입됨 — "
                                "시작/종료 시점을 분리해 서술하세요."
                            )
                        _prev_start, _ = self._extract_timeline_start_end(_prev_arc_data)
                        _cur_start, _ = self._extract_timeline_start_end(arc_data)
                        if _prev_start and _cur_start and _prev_start[0] > 0 and _cur_start[0] > 0:
                            if _cur_start < _prev_start:
                                _ta_lines.append(
                                    "⚠️ [NS-4] Arc timeline 역전 감지 — 현재 Arc 시작 시점이 "
                                    "이전 Arc 시작 시점보다 과거입니다. 시간 순서를 재점검하세요."
                                )
                        _ta_lines.append(
                            "※ 현재 화에서 과거 사건 언급 시 '며칠 전'/'얼마 전' 같은 표현이 "
                            "위 시간 간격과 일치하는지 확인하세요."
                        )
                        _ta_text = "\n".join(_ta_lines)
                        _bp_semantic_ctx = _ta_text + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")
                        _logging.info(
                            "[NS-4] Arc 시간 마커 주입: prev=%s, cur=%s",
                            _prev_markers,
                            _cur_markers,
                        )
        except Exception as _ns4_err:
            _logging.debug("[NS-4] 시간 마커 주입 실패 (비차단): %s", _ns4_err)

        return _bp_semantic_ctx

    def _finalize_stage3_blueprint_semantic_bundle(
        self,
        *,
        semantic_ctx: str,
        work_focus: dict[str, object],
        plan,
        working_ep,
        arc_data,
        entity_registry,
        protagonist_name,
        blueprint_window: list,
        focus_window: list,
    ) -> dict[str, object]:
        ctx = self.ctx
        _bp_semantic_ctx = semantic_ctx
        _s3_work_focus = work_focus
        _s3_plan = plan
        _source_counts: dict[str, int] = {}
        _coverage_warnings: list[str] = []

        _world_state_advisory = _build_world_state_advisory(getattr(ctx, "world_state", None))
        if _world_state_advisory:
            _bp_semantic_ctx = _world_state_advisory + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")

        _style_guide_advisory = _build_style_guide_advisory(getattr(ctx, "current_project", None))
        if _style_guide_advisory:
            _bp_semantic_ctx = _style_guide_advisory + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")

        _fact_ledger_advisory = _build_fact_ledger_advisory(getattr(ctx.current_project, "db", None))
        if _fact_ledger_advisory:
            _bp_semantic_ctx = _fact_ledger_advisory + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")

        _seed_advisory = _build_stale_seed_advisory(getattr(ctx.current_project, "db", None), working_ep)
        if _seed_advisory:
            _bp_semantic_ctx = _seed_advisory + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")

        _work_focus_advisory = _build_stage3_work_focus_advisory(
            _s3_work_focus
            or _resolve_stage3_work_focus(
                ctx,
                arc_data=arc_data,
                prev_blueprints=focus_window,
                entity_registry=entity_registry,
            ),
            arc_data=arc_data,
            entity_registry=entity_registry,
            ctx=ctx,
            protagonist_name=protagonist_name,
        )
        if _work_focus_advisory:
            _bp_semantic_ctx = _work_focus_advisory + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")
        _source_counts = _summarize_retrieval_sources(_s3_plan)
        if not _source_counts and _bp_semantic_ctx:
            _source_counts = {"legacy_semantic_context": 1}
        if _s3_work_focus and not _work_focus_advisory:
            _coverage_warnings.append("missing_work_slot_summary")
        if (
            _s3_work_focus
            and _s3_plan
            and not any(
                str(getattr(_slot, "category", "")).startswith("work_")
                for _slot in (getattr(_s3_plan, "slots", []) or [])
            )
        ):
            _coverage_warnings.append("work_focus_without_slots")
        if (
            _source_counts.get(RetrievalSources.DB_NPC_RELATIONSHIP, 0) > 0
            and "[관계 의미 질의]" not in _bp_semantic_ctx
        ):
            _coverage_warnings.append("missing_relation_slice")
        _stage3_budget_cap = int(getattr(_s3_plan, "total_budget_chars", 0) or 0)
        _stage3_budget_ledger = build_context_budget_ledger(
            stage="stage3",
            configured_cap=_stage3_budget_cap,
            effective_cap=_stage3_budget_cap,
            consumed_chars=len(_bp_semantic_ctx),
            overflow_chars=max(0, len(_bp_semantic_ctx) - _stage3_budget_cap) if _stage3_budget_cap > 0 else 0,
        )
        _stage3_observation = build_context_observation(
            stage="stage3",
            work_focus=_s3_work_focus,
            retrieval_plan=_s3_plan,
            source_counts=_source_counts,
            coverage_warnings=_coverage_warnings,
            advisor_path_used=bool(_s3_plan),
            work_slot_summary_present=bool(_work_focus_advisory),
            work_slot_summary_included="[작품 추적 슬롯 요약]" in _bp_semantic_ctx,
            relation_slice_included="[관계 의미 질의]" in _bp_semantic_ctx,
            vector_context_chars=len(_bp_semantic_ctx),
            budget_ledger=_stage3_budget_ledger,
        )
        _source_anchor_summary = _build_stage3_source_anchor_summary(arc_data, blueprint_window)
        if _source_anchor_summary:
            _stage3_observation["source_anchor_summary"] = _source_anchor_summary
        _record_retrieval_observation(
            self.app,
            ep_num=working_ep,
            stage="stage3",
            observation=_stage3_observation,
        )
        return {
            "semantic_ctx": _bp_semantic_ctx,
            "work_focus": _s3_work_focus,
            "plan": _s3_plan,
            "source_counts": _source_counts,
            "coverage_warnings": _coverage_warnings,
            "observation": _stage3_observation,
            "blueprint_window": blueprint_window,
        }

    def _build_stage3_blueprint_semantic_bundle(
        self,
        *,
        working_ep,
        arc_data,
        arc_idx,
        prev_blueprints,
        entity_registry,
        protagonist_name,
    ) -> dict[str, object]:
        return self._get_stage3_envelope_builder().build_blueprint_semantic_bundle(
            working_ep=working_ep,
            arc_data=arc_data,
            arc_idx=arc_idx,
            prev_blueprints=prev_blueprints,
            entity_registry=entity_registry,
            protagonist_name=protagonist_name,
        )

    def _legacy_stage3_blueprint_semantic_bundle_tail(
        self,
        *,
        working_ep,
        arc_data,
        arc_idx,
        entity_registry,
        protagonist_name,
        semantic_ctx: str,
        work_focus: dict[str, object],
        plan,
        blueprint_window: list,
        focus_window: list,
    ) -> dict[str, object]:
        return self._get_stage3_envelope_builder().build_legacy_blueprint_semantic_bundle_tail(
            working_ep=working_ep,
            arc_data=arc_data,
            arc_idx=arc_idx,
            entity_registry=entity_registry,
            protagonist_name=protagonist_name,
            semantic_ctx=semantic_ctx,
            work_focus=work_focus,
            plan=plan,
            blueprint_window=blueprint_window,
            focus_window=focus_window,
        )

    def _run_stage3_blueprint_generation_handoff(
        self,
        *,
        working_ep,
        arc_data,
        arc_idx,
        prev_blueprint,
        protagonist_name,
        protagonist_config,
        entity_registry,
        semantic_bundle: dict[str, object],
    ):
        return self._get_stage3_envelope_builder().run_blueprint_generation_handoff(
            working_ep=working_ep,
            arc_data=arc_data,
            arc_idx=arc_idx,
            prev_blueprint=prev_blueprint,
            protagonist_name=protagonist_name,
            protagonist_config=protagonist_config,
            entity_registry=entity_registry,
            semantic_bundle=semantic_bundle,
        )

    def _apply_stage3_dead_npc_precheck(
        self,
        *,
        blueprint,
        pipeline_result,
        working_ep,
        arc_data,
    ):
        if not isinstance(blueprint, dict) or not isinstance(pipeline_result, dict):
            return blueprint, pipeline_result

        verdict = str(pipeline_result.get("final_verdict", "") or "").upper()
        if verdict in {"ERROR", "REJECT"}:
            return blueprint, pipeline_result

        tracker = getattr(self.ctx, "state_tracker", None)
        if tracker is None or not hasattr(tracker, "check_dead_npc_in_blueprint"):
            return blueprint, pipeline_result

        try:
            arc_no = int((arc_data or {}).get("arc_no") or 0)
        except (TypeError, ValueError):
            arc_no = 0

        try:
            violations = tracker.check_dead_npc_in_blueprint(blueprint, working_ep, arc_no) or []
        except Exception as precheck_err:
            _logging.debug("[Stage3] dead NPC pre-check failed (non-blocking): %s", precheck_err)
            return blueprint, pipeline_result

        if not isinstance(violations, list) or not violations:
            return blueprint, pipeline_result

        primary = violations[0] if isinstance(violations[0], dict) else {}
        npc_name = str(primary.get("npc_name", "") or "unknown NPC")
        reason = f"dead_npc_precheck: deceased NPC '{npc_name}' assigned active present-time role in blueprint"

        phases = pipeline_result.get("phases")
        if not isinstance(phases, dict):
            phases = {}
            pipeline_result["phases"] = phases
        validate = phases.get("validate")
        if not isinstance(validate, dict):
            validate = {}
            phases["validate"] = validate
        contradictions = validate.get("contradictions")
        if not isinstance(contradictions, list):
            contradictions = []
            validate["contradictions"] = contradictions
        if reason not in contradictions:
            contradictions.append(reason)

        validate["verdict"] = "REJECT"
        validate["issues_count"] = max(int(validate.get("issues_count") or 0), len(contradictions), len(violations))
        pipeline_result["final_verdict"] = "REJECT"
        pipeline_result["reject_reason"] = reason
        pipeline_result["precheck_failures"] = violations

        _logging.warning(
            "[Stage3] dead NPC pre-check reject: ep=%s arc=%s npc=%s violations=%d",
            working_ep,
            arc_no,
            npc_name,
            len(violations),
        )
        return blueprint, pipeline_result

    def _finalize_stage3_blueprint_pipeline_result(
        self,
        *,
        pipeline_result,
        started_at: float,
        started_cost_usd: float,
        semantic_bundle: dict[str, object],
    ) -> dict:
        if not isinstance(pipeline_result, dict):
            pipeline_result = {"final_verdict": "ERROR", "error": "invalid_pipeline_result"}

        phases = pipeline_result.get("phases", {}) if isinstance(pipeline_result.get("phases"), dict) else {}
        _stage3_observation = semantic_bundle.get("observation") or {}
        _s3_plan = semantic_bundle.get("plan")
        _s3_work_focus = semantic_bundle.get("work_focus") or {}
        _source_counts = semantic_bundle.get("source_counts") or {}
        _coverage_warnings = semantic_bundle.get("coverage_warnings") or []
        _bp_semantic_ctx = str(semantic_bundle.get("semantic_ctx", "") or "")
        _source_anchor_summary = {}
        if isinstance(_stage3_observation, dict):
            _source_anchor_summary = dict((_stage3_observation or {}).get("source_anchor_summary") or {})
        _constraint_phase = phases.get("constraint", {}) if isinstance(phases, dict) else {}
        if not isinstance(_constraint_phase, dict):
            _constraint_phase = {}
        _episode_state_packet_summary = dict(_constraint_phase.get("episode_state_packet_summary") or {})
        _generate_phase = phases.get("generate", {}) if isinstance(phases, dict) else {}
        if not isinstance(_generate_phase, dict):
            _generate_phase = {}
        _prompt_envelope = dict(_generate_phase.get("prompt_envelope") or {})

        pipeline_result["_stage3_duration_ms"] = max(0, int((_time.perf_counter() - started_at) * 1000))
        pipeline_result["_stage3_token_cost_usd"] = max(0.0, round(_peek_scope_total_cost_usd() - started_cost_usd, 6))
        pipeline_result["_stage3_observability"] = {
            "semantic_ctx_chars": len(_bp_semantic_ctx),
            "source_counts": _normalize_semantic_source_counts(_source_counts),
            "coverage_warnings": list(_coverage_warnings),
            "advisor_path_used": bool(_s3_plan),
            "planned_slots_count": len(getattr(_s3_plan, "slots", []) or []) if _s3_plan else 0,
            "work_focus_present": bool(_s3_work_focus),
            "provenance_ledger": dict((_stage3_observation or {}).get("provenance_ledger") or {}),
            "budget_ledger": dict((_stage3_observation or {}).get("budget_ledger") or {}),
            "source_anchor_summary": _source_anchor_summary,
            "episode_state_packet_summary": _episode_state_packet_summary,
            "prompt_envelope": _prompt_envelope,
        }
        return pipeline_result

    def _generate_blueprint(
        self,
        working_ep,
        arc_data,
        arc_idx,
        prev_blueprint,
        prev_blueprints,
        entity_registry,
        protagonist_name,
        protagonist_config,
    ):
        """[V60.80] Three Phase Blueprint Generation — LLM 호출 + 스피너"""
        ctx = self.ctx

        _started_at = _time.perf_counter()
        _started_cost_usd = _peek_scope_total_cost_usd()
        _semantic_bundle: dict[str, object] = {
            "semantic_ctx": "",
            "work_focus": {},
            "plan": None,
            "source_counts": {},
            "coverage_warnings": [],
            "observation": {},
            "blueprint_window": _select_stage3_anchor_recent_window(prev_blueprints),
        }
        try:
            _semantic_bundle = self._build_stage3_blueprint_semantic_bundle(
                working_ep=working_ep,
                arc_data=arc_data,
                arc_idx=arc_idx,
                prev_blueprints=prev_blueprints,
                entity_registry=entity_registry,
                protagonist_name=protagonist_name,
            )
            blueprint, pipeline_result = self._run_stage3_blueprint_generation_handoff(
                working_ep=working_ep,
                arc_data=arc_data,
                arc_idx=arc_idx,
                prev_blueprint=prev_blueprint,
                protagonist_name=protagonist_name,
                protagonist_config=protagonist_config,
                entity_registry=entity_registry,
                semantic_bundle=_semantic_bundle,
            )

        except Exception as gen_err:
            _logging.error(f" [V61.3] 제{working_ep}화 Blueprint 생성 크래시: {str(gen_err)}")
            _logging.error(_traceback.format_exc())

            ctx.ui.log(f"❌ [V60.80] 제{working_ep}화 생성 실패: {gen_err!s}")
            if callable(ctx.audit_event):
                ctx.audit_event("blueprint_gen_error", str(gen_err), {"ep_num": working_ep})
            blueprint = None
            pipeline_result = {"final_verdict": "ERROR", "error": str(gen_err)}

        pipeline_result = self._finalize_stage3_blueprint_pipeline_result(
            pipeline_result=pipeline_result,
            started_at=_started_at,
            started_cost_usd=_started_cost_usd,
            semantic_bundle=_semantic_bundle,
        )
        return blueprint, pipeline_result

    # ─────────────────────────────────────────────────────────────
    # 결과 처리
    # ─────────────────────────────────────────────────────────────
    def _handle_success(
        self, working_ep, arc_no, arc_data, blueprint, pipeline_result, prev_blueprints, success_count, fail_count
    ) -> dict:
        """Handle successful Stage 3 blueprint generation."""
        ctx = self.ctx
        final_verdict = pipeline_result.get("final_verdict", "PASS")
        quality_gate_failed = bool(pipeline_result.get("quality_gate_failed", False))
        quality_risk = bool(pipeline_result.get("quality_risk", False) or quality_gate_failed)
        revision_required = bool(
            pipeline_result.get("revision_required", False) or final_verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")
        )
        observability_flags = _build_stage3_observability_flags(pipeline_result.get("_stage3_observability"))
        pov_contract = resolve_project_pov_contract(ctx.current_project)
        duration_ms = int(pipeline_result.get("_stage3_duration_ms") or 0) or None
        token_cost = float(pipeline_result.get("_stage3_token_cost_usd") or 0.0)
        source_anchor_line = _format_stage3_source_anchor_summary(observability_flags.get("source_anchor_summary"))
        blueprint = self._annotate_stage3_success_blueprint(
            working_ep=working_ep,
            arc_data=arc_data,
            blueprint=blueprint,
            pipeline_result=pipeline_result,
            final_verdict=final_verdict,
            quality_gate_failed=quality_gate_failed,
            quality_risk=quality_risk,
            revision_required=revision_required,
        )

        persistence_failure = self._persist_stage3_success_blueprint(
            working_ep=working_ep,
            blueprint=blueprint,
            prev_blueprints=prev_blueprints,
            success_count=success_count,
            fail_count=fail_count,
        )
        if persistence_failure:
            return persistence_failure

        try:
            runtime_payload = self._build_stage3_success_runtime_payload(
                working_ep=working_ep,
                arc_no=arc_no,
                blueprint=blueprint,
                pipeline_result=pipeline_result,
                observability_flags=observability_flags,
            )
            self._record_stage3_success_observability(
                working_ep=working_ep,
                arc_no=arc_no,
                final_verdict=final_verdict,
                quality_risk=quality_risk,
                duration_ms=duration_ms,
                token_cost=token_cost,
                observability_flags=observability_flags,
                runtime_payload=runtime_payload,
                pipeline_result=pipeline_result,
                pov_contract=pov_contract,
            )
        except Exception as stage_attempt_err:
            _logging.debug("[stage_attempts] Stage3 PASS record failed (non-blocking): %s", stage_attempt_err)

        if source_anchor_line:
            ctx.ui.log(
                f"      source_anchor: {source_anchor_line}",
                stage="stage3",
                component="blueprint_generation",
                ep_num=working_ep,
                arc_num=arc_no,
                event_kind="summary",
                meta={"source_anchor_summary": observability_flags.get("source_anchor_summary")},
            )

        self._record_stage3_success_completion(
            working_ep=working_ep,
            arc_no=arc_no,
            blueprint=blueprint,
            pipeline_result=pipeline_result,
            final_verdict=final_verdict,
            quality_gate_failed=quality_gate_failed,
            quality_risk=quality_risk,
            revision_required=revision_required,
        )
        return {"next_ep": working_ep + 1, "success_count": success_count + 1, "fail_count": 0}

    def _build_stage3_success_runtime_payload(
        self,
        *,
        working_ep,
        arc_no,
        blueprint,
        pipeline_result,
        observability_flags: dict,
    ) -> Stage3AttemptEvidencePacket:
        return self._build_stage3_attempt_evidence_packet(
            working_ep=working_ep,
            arc_no=arc_no,
            blueprint=blueprint,
            pipeline_result=pipeline_result,
            observability_flags=observability_flags,
            artifact_kind="final_blueprint",
        )

    def _build_stage3_attempt_evidence_packet(
        self,
        *,
        working_ep,
        arc_no,
        pipeline_result,
        observability_flags: dict,
        blueprint=None,
        artifact_kind: str,
        reject_reason: str = "",
    ) -> Stage3AttemptEvidencePacket:
        ctx = self.ctx
        db = getattr(getattr(ctx, "current_project", None), "db", None)
        attempt_num = self._extract_stage3_attempt_num(pipeline_result)
        session_id = resolve_logging_session_id(getattr(ctx, "current_project", None))
        attempt_key = build_attempt_key(
            stage=3,
            ep_num=working_ep,
            arc_num=arc_no,
            attempt_num=attempt_num,
            session_id=session_id,
        )
        score = pipeline_result.get("last_score") or pipeline_result.get("phases", {}).get("generate", {}).get(
            "selected_score", 0
        )
        selected_strategy = str(
            pipeline_result.get("phases", {}).get("generate", {}).get("selected_strategy", "unknown") or "unknown"
        )
        candidate_key = build_candidate_key(strategy=selected_strategy, fallback="stage3")
        artifact_payload = blueprint if isinstance(blueprint, dict) else None
        artifact_meta = normalize_artifact_meta(
            snapshot_logged_artifact(
                getattr(ctx, "current_project", None),
                stage=3,
                ep_num=working_ep,
                arc_num=arc_no,
                attempt_num=attempt_num,
                candidate_key=candidate_key,
                artifact_kind=artifact_kind,
                payload=artifact_payload,
            )
            if artifact_payload is not None
            else None,
            fallback_candidate_key=candidate_key,
        )
        selection_kwargs = self._build_stage3_director_selection_kwargs(
            pipeline_result,
            ep_num=working_ep,
            attempt_num=attempt_num,
            attempt_key=attempt_key,
            selected_strategy=selected_strategy,
            score=score,
            candidate_key=candidate_key,
            advisory_flags=observability_flags,
            artifact_meta=artifact_meta,
        )
        runtime_advisory = _resolve_stage3_runtime_advisory(
            pipeline_result,
            selection_kwargs,
            reject_reason=reject_reason,
        )
        retry_directives = _resolve_stage3_retry_directives(
            pipeline_result,
            selection_kwargs,
            reject_reason=reject_reason,
        )
        if isinstance(selection_kwargs, dict) and (runtime_advisory or retry_directives):
            selection_kwargs = dict(selection_kwargs)
            if runtime_advisory:
                selection_kwargs["runtime_advisory"] = runtime_advisory
            if retry_directives:
                selection_kwargs["retry_directives"] = retry_directives
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 0
        return Stage3AttemptEvidencePacket(
            db=db,
            attempt_num=attempt_num,
            session_id=session_id,
            attempt_key=attempt_key,
            score=score,
            selected_strategy=selected_strategy,
            candidate_key=candidate_key,
            artifact_meta=artifact_meta,
            selection_kwargs=selection_kwargs,
            runtime_advisory=runtime_advisory,
            retry_directives=retry_directives,
        )

    def _record_stage3_success_observability(
        self,
        *,
        working_ep,
        arc_no,
        final_verdict: str,
        quality_risk: bool,
        duration_ms: int | None,
        token_cost: float,
        observability_flags: dict,
        runtime_payload: Stage3AttemptEvidencePacket,
        pipeline_result,
        pov_contract: dict,
    ) -> None:
        ctx = self.ctx
        attempt_key = runtime_payload.attempt_key
        artifact_meta = runtime_payload.artifact_meta
        selection_kwargs = runtime_payload.selection_kwargs
        score = runtime_payload.score
        candidate_key = runtime_payload.candidate_key

        session_logger = getattr(ctx, "session_logger", None)
        if session_logger:
            try:
                decision_kwargs = self._build_stage3_session_decision_kwargs(
                    ep_num=working_ep,
                    verdict=final_verdict,
                    score=pipeline_result.get("last_score", 0),
                    arc_no=arc_no,
                    quality_risk=quality_risk,
                    packet=runtime_payload,
                    validate=(pipeline_result.get("phases") or {}).get("validate", {})
                    if isinstance(pipeline_result, dict)
                    else {},
                    reason=str((selection_kwargs or {}).get("verdict_reason", "") or ""),
                    selection_reason=str((selection_kwargs or {}).get("selection_reason", "") or ""),
                    verdict_reason=str((selection_kwargs or {}).get("verdict_reason", "") or ""),
                    fix_scope=str((selection_kwargs or {}).get("fix_scope", "") or ""),
                )
                self._log_stage3_session_decision(
                    session_logger,
                    **decision_kwargs,
                )
            except Exception as log_err:
                _logging.debug("[TF-26] session_logger.log_decision failed: %s", str(log_err)[:100])

        if getattr(ctx, "pass_rate_monitor", None):
            try:
                _s3_pass_breakdown = {}
                _validate = (
                    (pipeline_result.get("phases") or {}).get("validate", {})
                    if isinstance(pipeline_result, dict)
                    else {}
                )
                if isinstance(_validate, dict):
                    _raw_bd = _validate.get("score_breakdown", {})
                    if isinstance(_raw_bd, dict):
                        _s3_pass_breakdown = {
                            str(k): v for k, v in list(_raw_bd.items())[:5] if isinstance(v, int | float)
                        }
                ctx.pass_rate_monitor.record_attempt(
                    **self._build_stage3_pass_rate_attempt_kwargs(
                        working_ep=working_ep,
                        arc_no=arc_no,
                        packet=runtime_payload,
                        success=final_verdict in ("PASS", "PASS_WITH_WARNING", "PASS_WITH_FIX"),
                        duration_ms=duration_ms,
                        token_cost=token_cost,
                        final_verdict=str(final_verdict),
                        score_breakdown=_s3_pass_breakdown,
                    )
                )
                if hasattr(ctx.pass_rate_monitor, "_save_records"):
                    ctx.pass_rate_monitor._save_records()
            except Exception as prm_err:
                _logging.debug("[stage3_prm] Stage3 PASS record failed (non-blocking): %s", prm_err)

        db = runtime_payload.db
        if db and hasattr(db, "save_stage_attempt"):
            director = getattr(getattr(ctx, "agents", {}), "get", lambda *_: None)("director")
            model = getattr(director, "primary_model", None) if director else None
            prompt_version = _build_stage3_prompt_version()
            _s3_validate = (
                (pipeline_result.get("phases") or {}).get("validate", {}) if isinstance(pipeline_result, dict) else {}
            )
            db.save_stage_attempt(
                **self._build_stage3_stage_attempt_kwargs(
                    ep_num=working_ep,
                    arc_no=arc_no,
                    verdict=str(final_verdict),
                    packet=runtime_payload,
                    model=str(model) if model else None,
                    prompt_version=prompt_version,
                    duration_ms=duration_ms,
                    advisory_flags=observability_flags,
                    validate=_s3_validate,
                )
            )
            if hasattr(db, "save_director_selection") and selection_kwargs:
                try:
                    db.save_director_selection(**selection_kwargs)
                except Exception as ds_err:
                    _logging.debug("[director_selections] Stage3 PASS record failed (non-blocking): %s", ds_err)

        _logging.info(
            "[STAGE3_EPISODE_SUMMARY] ep=%d arc=%d attempt_key=%s verdict=%s score=%s strategy=%s candidate_key=%s artifact=%s observability=%s primary_pov=%s external_pov_insert_policy=%s style_guide_extracted_pov=%s effective_pov=%s",
            working_ep,
            arc_no,
            attempt_key,
            final_verdict,
            score,
            runtime_payload.selected_strategy,
            candidate_key,
            str(artifact_meta.get("artifact_path", "") or "-"),
            ",".join(sorted(observability_flags.keys())) if observability_flags else "-",
            pov_contract.get("primary_pov", "") or "-",
            pov_contract.get("external_pov_insert_policy", "") or "-",
            pov_contract.get("style_guide_extracted_pov", "") or "-",
            pov_contract.get("effective_pov", "") or "-",
        )

    def _annotate_stage3_success_blueprint(
        self,
        *,
        working_ep,
        arc_data,
        blueprint,
        pipeline_result,
        final_verdict: str,
        quality_gate_failed: bool,
        quality_risk: bool,
        revision_required: bool,
    ):
        ctx = self.ctx
        if isinstance(blueprint, dict):
            validate_meta = (
                pipeline_result.get("phases", {}).get("validate", {}) if isinstance(pipeline_result, dict) else {}
            )
            binding_issue_count = 0
            if isinstance(validate_meta, dict):
                try:
                    binding_issue_count = int(validate_meta.get("binding_prevalidation_issue_count") or 0)
                except (TypeError, ValueError):
                    binding_issue_count = 0
            binding_categories = []
            if isinstance(validate_meta, dict):
                raw_binding_categories = validate_meta.get("binding_prevalidation_categories", [])
                if isinstance(raw_binding_categories, list):
                    binding_categories = [
                        str(item).strip() for item in raw_binding_categories if str(item or "").strip()
                    ][:6]
            regenerate_only_categories = []
            if isinstance(validate_meta, dict):
                raw_regenerate_only_categories = validate_meta.get("binding_regenerate_only_categories", [])
                if isinstance(raw_regenerate_only_categories, list):
                    regenerate_only_categories = [
                        str(item).strip() for item in raw_regenerate_only_categories if str(item or "").strip()
                    ][:6]
            regenerate_only_reason = (
                str(validate_meta.get("binding_regenerate_only_reason", "") or "").strip()
                if isinstance(validate_meta, dict)
                else ""
            )
            blueprint["_stage3_meta"] = {
                "final_verdict": final_verdict,
                "quality_gate_failed": quality_gate_failed,
                "quality_risk": quality_risk,
                "revision_required": revision_required,
                "last_score": pipeline_result.get("last_score", 0),
                "binding_prevalidation_issue_count": binding_issue_count,
            }
            if binding_categories:
                blueprint["_stage3_meta"]["binding_prevalidation_categories"] = binding_categories
            if regenerate_only_categories:
                blueprint["_stage3_meta"]["binding_regenerate_only_categories"] = regenerate_only_categories
            if regenerate_only_reason:
                blueprint["_stage3_meta"]["binding_regenerate_only_reason"] = regenerate_only_reason
            partial_fix_eval = validate_meta.get("partial_fix_eval") if isinstance(validate_meta, dict) else {}
            if isinstance(partial_fix_eval, dict) and partial_fix_eval:
                blueprint["_stage3_meta"]["partial_fix_eval"] = dict(partial_fix_eval)
            fix_pack = validate_meta.get("fix_pack") if isinstance(validate_meta, dict) else {}
            if isinstance(fix_pack, dict) and fix_pack:
                compact_fix_pack = {
                    key: value
                    for key, value in {
                        "patch_targets": list(fix_pack.get("patch_targets") or []),
                        "target_kind": str(fix_pack.get("target_kind", "") or "").strip(),
                        "must_fix": list(fix_pack.get("must_fix") or []),
                        "do_not_regress": list(fix_pack.get("do_not_regress") or []),
                        "success_condition": str(fix_pack.get("success_condition", "") or "").strip(),
                        "subtype": str(fix_pack.get("subtype", "") or "").strip(),
                        "subtypes": _compact_stage3_contract_list(fix_pack.get("subtypes"), limit=4, item_limit=80),
                        "provenance": str(fix_pack.get("provenance", "") or "").strip(),
                        "provenance_sources": _compact_stage3_contract_list(
                            fix_pack.get("provenance_sources"),
                            limit=4,
                            item_limit=120,
                        ),
                    }.items()
                    if value not in ("", [], {}, None)
                }
                if compact_fix_pack:
                    blueprint["_stage3_meta"]["fix_pack"] = compact_fix_pack
            repair_contract = validate_meta.get("repair_contract") if isinstance(validate_meta, dict) else {}
            compact_repair_contract = _compact_stage3_repair_contract(repair_contract)
            if compact_repair_contract:
                blueprint["_stage3_meta"]["repair_contract"] = compact_repair_contract
            scope_authority = validate_meta.get("scope_authority") if isinstance(validate_meta, dict) else {}
            compact_scope_authority = _compact_stage3_scope_authority(scope_authority)
            if compact_scope_authority:
                blueprint["_stage3_meta"]["scope_authority"] = compact_scope_authority

        if isinstance(blueprint, dict) and working_ep > 1:
            inventory_gaps = self._detect_inventory_gaps(blueprint, arc_data, working_ep=working_ep)
            if inventory_gaps:
                blueprint["_inventory_gaps"] = inventory_gaps
                ctx.ui.log(
                    f"   [TF-49] inventory gaps {len(inventory_gaps)}: {', '.join(g['item'] for g in inventory_gaps)}"
                )

        if isinstance(blueprint, dict):
            prev_published_text = ""
            try:
                db = getattr(getattr(ctx, "current_project", None), "db", None)
                prev_row = db.get_manuscript(working_ep - 1) if db and working_ep > 1 else None
                if isinstance(prev_row, dict):
                    prev_published_text = str(
                        prev_row.get("content")
                        or prev_row.get("corrected_manuscript")
                        or prev_row.get("manuscript")
                        or ""
                    )
                elif prev_row:
                    prev_published_text = str(prev_row)
            except Exception as pin_prev_err:
                _logging.debug("[Stage3] previous manuscript lookup failed (non-blocking): %s", pin_prev_err)

            arc_tactical_text = ""
            try:
                arc_tactical_text = extract_episode_tactical(
                    arc_data.get("tactical_doc", ""),
                    working_ep,
                    episode_details=arc_data.get("episode_details"),
                )
            except Exception as pin_tactical_err:
                _logging.debug("[Stage3] arc tactical extract failed (non-blocking): %s", pin_tactical_err)

            pin_result = apply_continuity_pins(
                blueprint,
                previous_published_text=prev_published_text,
                arc_tactical_text=arc_tactical_text,
            )
            blueprint = pin_result.get("blueprint", blueprint)
            if pin_result.get("changes"):
                blueprint["_continuity_pins"] = pin_result["changes"]
                ctx.ui.log(f"   [PinGuard] ep {working_ep} continuity pins applied: {len(pin_result['changes'])}")
            if pin_result.get("unresolved"):
                blueprint["_continuity_pin_unresolved"] = pin_result["unresolved"]
                ctx.ui.log(f"   [PinGuard][WARN] ep {working_ep} unresolved continuity pins")
                if callable(ctx.audit_event):
                    ctx.audit_event(
                        "continuity_pin_unresolved",
                        "stage3 continuity pin unresolved",
                        {"ep_num": working_ep, "items": pin_result["unresolved"][:3]},
                    )

        return blueprint

    def _persist_stage3_success_blueprint(
        self,
        *,
        working_ep,
        blueprint,
        prev_blueprints,
        success_count: int,
        fail_count: int,
    ) -> dict | None:
        ctx = self.ctx
        if callable(ctx.validate_blueprint_integrity) and not ctx.validate_blueprint_integrity(blueprint):
            ctx.ui.log(f"   [Integrity] ep {working_ep} blueprint integrity failed")
            if callable(ctx.audit_event):
                ctx.audit_event("integrity_fail", "blueprint integrity check failed", {"ep_num": working_ep})
            return {
                "next_ep": working_ep + 1,
                "success_count": success_count,
                "fail_count": fail_count + 1,
                "break": True,
            }

        ctx.current_project.save_episode_blueprint(working_ep, blueprint)
        if callable(ctx.safe_commit) and not ctx.safe_commit():
            ctx.ui.log(f"   [DB] ep {working_ep} blueprint commit failed")
            if callable(ctx.audit_event):
                ctx.audit_event("db_commit_error", "blueprint commit failed", {"ep_num": working_ep})
            return {
                "next_ep": working_ep + 1,
                "success_count": success_count,
                "fail_count": fail_count + 1,
                "break": True,
            }

        prev_blueprints.append(blueprint)
        if len(prev_blueprints) > _STAGE3_HISTORY_CACHE_LIMIT:
            prev_blueprints[:] = prev_blueprints[-_STAGE3_HISTORY_CACHE_LIMIT:]
        return None

    def _record_stage3_success_completion(
        self,
        *,
        working_ep,
        arc_no,
        blueprint,
        pipeline_result,
        final_verdict: str,
        quality_gate_failed: bool,
        quality_risk: bool,
        revision_required: bool,
    ) -> None:
        ctx = self.ctx
        if callable(ctx.audit_event):
            ctx.audit_event(
                "blueprint_success",
                f"ep_{working_ep}_blueprint_generated",
                {
                    "ep_num": working_ep,
                    "arc_no": arc_no,
                    "strategy": pipeline_result.get("phases", {})
                    .get("generate", {})
                    .get("selected_strategy", "unknown"),
                    "score": pipeline_result.get("phases", {}).get("generate", {}).get("selected_score", 0),
                    "final_verdict": final_verdict,
                    "quality_risk": quality_risk,
                    "revision_required": revision_required,
                },
            )

        ctx.ui.log(
            "   [Stage3] blueprint success "
            f"(verdict={final_verdict}, "
            f"strategy={pipeline_result.get('phases', {}).get('generate', {}).get('selected_strategy', 'unknown')}, "
            f"score={pipeline_result.get('phases', {}).get('generate', {}).get('selected_score', 0)})"
        )
        ctx.ui.log(f"   [Stage3] ep {working_ep} blueprint save completed")
        ctx.ui.log(
            self._build_stage3_success_summary_line(
                working_ep=working_ep,
                blueprint=blueprint,
                pipeline_result=pipeline_result,
                final_verdict=final_verdict,
            )
        )
        quality_dashboard = getattr(self.app, "quality_dashboard", None)
        if quality_dashboard is not None and hasattr(quality_dashboard, "record_validation"):
            try:
                blueprint_score = pipeline_result.get("last_score")
                if blueprint_score is None:
                    blueprint_score = pipeline_result.get("phases", {}).get("generate", {}).get("selected_score")
                quality_dashboard.record_validation(
                    ep_num=working_ep,
                    result=self._build_stage3_quality_dashboard_result(
                        final_verdict=final_verdict,
                        blueprint_score=blueprint_score,
                        quality_gate_failed=quality_gate_failed,
                        quality_risk=quality_risk,
                        revision_required=revision_required,
                    ),
                    stage=3,
                )
            except Exception as err:
                _logging.debug("[Stage3] QualityDashboard PASS record failed (ignored): %s", err)

    @staticmethod
    def _build_stage3_quality_dashboard_result(
        *,
        final_verdict: str,
        blueprint_score,
        quality_gate_failed: bool,
        quality_risk: bool,
        revision_required: bool,
    ) -> dict:
        if blueprint_score is None:
            blueprint_score = 1.0
        dashboard_warnings: list[str] = []
        if quality_gate_failed:
            dashboard_warnings.append("quality_gate_failed")
        if quality_risk:
            dashboard_warnings.append("quality_risk")
        if revision_required:
            dashboard_warnings.append("revision_required")
        normalized_decision = (
            final_verdict if final_verdict in ("PASS", "PASS_WITH_FIX", "PASS_WITH_WARNING") else "PASS"
        )
        return {
            "decision": normalized_decision,
            "score": blueprint_score,
            "violations": [],
            "warnings": dashboard_warnings,
            "quality_signals": {
                "final_verdict": final_verdict,
                "quality_gate_failed": quality_gate_failed,
                "quality_risk": quality_risk,
                "revision_required": revision_required,
            },
        }

    @staticmethod
    def _extract_stage3_attempt_num(pipeline_result: dict) -> int:
        """Convert pipeline retries(0-based) to attempt number(1-based)."""
        if not isinstance(pipeline_result, dict):
            return 1
        retries = pipeline_result.get("retries", 0)
        try:
            return max(1, int(retries) + 1)
        except (TypeError, ValueError):
            return 1

    @staticmethod
    def _extract_stage3_prevalidation_counts(pipeline_result: dict) -> tuple[int, int]:
        """Return total prevalidation issues and binding subset counts for operator summaries."""
        if not isinstance(pipeline_result, dict):
            return 0, 0
        phases = pipeline_result.get("phases", {})
        if not isinstance(phases, dict):
            return 0, 0
        validate = phases.get("validate", {})
        if not isinstance(validate, dict):
            return 0, 0
        advisory = validate.get("selected_candidate_advisory", {})
        issue_count = 0
        if isinstance(advisory, dict):
            try:
                issue_count = max(0, int(advisory.get("issue_count", 0) or 0))
            except (TypeError, ValueError):
                issue_count = 0
        try:
            binding_count = max(0, int(validate.get("binding_prevalidation_issue_count", 0) or 0))
        except (TypeError, ValueError):
            binding_count = 0
        return issue_count, binding_count

    @classmethod
    def _build_stage3_success_summary_line(
        cls,
        *,
        working_ep: int,
        blueprint,
        pipeline_result: dict,
        final_verdict: str,
    ) -> str:
        attempt_num = cls._extract_stage3_attempt_num(pipeline_result)
        issue_count, binding_count = cls._extract_stage3_prevalidation_counts(pipeline_result)
        score = pipeline_result.get(
            "last_score", pipeline_result.get("phases", {}).get("generate", {}).get("selected_score", 0)
        )
        inventory_gap_count = len(blueprint.get("_inventory_gaps", [])) if isinstance(blueprint, dict) else 0
        unresolved_pin_count = (
            len(blueprint.get("_continuity_pin_unresolved", [])) if isinstance(blueprint, dict) else 0
        )
        return (
            f"   [Stage3 Summary] ep {working_ep} | verdict={final_verdict} | score={score} | "
            f"attempt={attempt_num} | prevalidation={issue_count} | binding={binding_count} | "
            f"TF-49={inventory_gap_count} | PinGuard={unresolved_pin_count}"
        )

    @staticmethod
    def _resolve_stage3_arc_num(arc_no: int | None, pipeline_result: dict) -> int | None:
        """Recover arc number for REJECT path when available."""
        if isinstance(arc_no, int) and arc_no > 0:
            return arc_no
        if isinstance(pipeline_result, dict):
            candidate = pipeline_result.get("arc_no")
            try:
                candidate_int = int(candidate)
                if candidate_int > 0:
                    return candidate_int
            except (TypeError, ValueError):
                return None
        return None

    @staticmethod
    def _build_stage3_reject_reason(pipeline_result: dict) -> str:
        """Assemble a compact, informative reject reason for stage_attempts logging."""
        if not isinstance(pipeline_result, dict):
            return ""

        parts: list[str] = []
        error_text = str(pipeline_result.get("error", "") or "").strip()
        if error_text:
            parts.append(error_text)
        reject_reason = str(pipeline_result.get("reject_reason", "") or "").strip()
        if reject_reason:
            parts.append(reject_reason)

        score = pipeline_result.get("last_score")
        if isinstance(score, int | float):
            parts.append(f"score={int(score)}")

        if pipeline_result.get("quality_gate_failed"):
            parts.append("quality_gate_failed=1")

        phases = pipeline_result.get("phases", {})
        if isinstance(phases, dict):
            generate = phases.get("generate", {})
            if isinstance(generate, dict):
                strategy = str(generate.get("selected_strategy", "") or "").strip()
                if strategy:
                    parts.append(f"strategy={strategy[:40]}")

            validate = phases.get("validate", {})
            if isinstance(validate, dict):
                verdict = str(validate.get("verdict", "") or "").strip()
                if verdict:
                    parts.append(f"validate_verdict={verdict[:20]}")
                issues_count = validate.get("issues_count")
                if isinstance(issues_count, int):
                    parts.append(f"issues={issues_count}")
                notes = str(validate.get("comparison_notes", "") or "").strip()
                if notes:
                    parts.append(f"notes={notes}")
                contradictions = validate.get("contradictions")
                if isinstance(contradictions, list) and contradictions:
                    _contr = "; ".join(str(c) for c in contradictions)
                    if _contr:
                        parts.append(f"contradictions={_contr}")

        if not parts:
            verdict = str(pipeline_result.get("final_verdict", "REJECT") or "REJECT")
            parts.append(f"final_verdict={verdict[:20]}")

        return " | ".join(parts)

    @staticmethod
    def _build_stage3_success_operator_lines(pipeline_result: dict) -> list[str]:
        """Expose Director reasoning for successful blueprint selection to the live operator surface."""
        if not isinstance(pipeline_result, dict):
            return []

        phases = pipeline_result.get("phases", {})
        if not isinstance(phases, dict):
            return []

        validate = phases.get("validate", {})
        if not isinstance(validate, dict) or not validate:
            return []

        lines: list[str] = []
        seen: set[tuple[str, str]] = set()

        def _append(label: str, value: object) -> None:
            text = str(value or "").strip()
            if not text or text in {"없음", "특이사항 없음"}:
                return
            marker = (label, text)
            if marker in seen:
                return
            seen.add(marker)
            lines.append(f"      {label}: {text}")

        selection_reason, verdict_reason, comparison_notes = _resolve_stage3_validate_rationale(
            validate,
            pipeline_result,
        )
        open_review = str(validate.get("open_review", "") or "").strip()
        fix_scope_reasoning = str(validate.get("fix_scope_reasoning", "") or "").strip()

        _append("└─ Director 판정", verdict_reason)
        if selection_reason and selection_reason != verdict_reason:
            _append("선택 근거", selection_reason)
        if comparison_notes and comparison_notes not in {selection_reason, verdict_reason}:
            _append("비교 메모", comparison_notes)
        if fix_scope_reasoning and fix_scope_reasoning not in {selection_reason, verdict_reason, comparison_notes}:
            _append("보완 포인트", fix_scope_reasoning)
        if open_review and open_review not in {selection_reason, verdict_reason, comparison_notes, fix_scope_reasoning}:
            _append("자유 리뷰", open_review)

        contradictions = validate.get("contradictions")
        if isinstance(contradictions, list):
            for item in contradictions:
                _append("모순 메모", item)

        selected_candidate_advisory = validate.get("selected_candidate_advisory", {})
        if isinstance(selected_candidate_advisory, dict):
            for item in selected_candidate_advisory.get("python_warnings", []):
                if isinstance(item, dict):
                    _append("주의", item.get("message", ""))
                else:
                    _append("주의", item)

        return lines

    @staticmethod
    def _stage3_selected_label(selected_index: object) -> str:
        try:
            idx = int(selected_index)
        except (TypeError, ValueError):
            return ""
        if 0 <= idx < 26:
            return chr(ord("A") + idx)
        return ""

    @staticmethod
    def _build_stage3_session_decision_kwargs(
        *,
        ep_num: int,
        verdict: str,
        score: int,
        arc_no: int | None,
        quality_risk: bool,
        packet: Stage3AttemptEvidencePacket,
        validate: dict | None = None,
        reject_reason: str = "",
        reason: str = "",
        selection_reason: str = "",
        verdict_reason: str = "",
        fix_scope: str = "",
    ) -> dict:
        validate = validate if isinstance(validate, dict) else {}
        repair_contract = _compact_stage3_repair_contract(validate.get("repair_contract"))
        scope_authority = _compact_stage3_scope_authority(validate.get("scope_authority"))
        repair_scope = str(
            validate.get("repair_scope", "")
            or repair_contract.get("repair_scope", "")
            or scope_authority.get("repair_scope", "")
            or ""
        ).strip()
        authoritative_fix_scope = str(
            validate.get("authoritative_fix_scope", "")
            or repair_contract.get("authoritative_fix_scope", "")
            or scope_authority.get("authoritative_fix_scope", "")
            or ""
        ).strip()
        fix_pack = validate.get("fix_pack")
        fix_pack = dict(fix_pack) if isinstance(fix_pack, dict) and fix_pack else {}
        comparison_notes = resolve_comparison_notes_text(validate.get("comparison_notes", ""))
        selected_candidate_advisory_struct = resolve_structured_advisory_payload(
            validate.get("selected_candidate_advisory")
        )
        payload = {
            "ep_num": ep_num,
            "verdict": str(verdict or ""),
            "score": int(score or 0),
            "arc_no": arc_no,
            "quality_risk": bool(quality_risk),
            "reject_reason": str(reject_reason or ""),
            "reason": str(reason or ""),
            "selection_reason": str(selection_reason or ""),
            "verdict_reason": str(verdict_reason or ""),
            "fix_scope": str(fix_scope or ""),
            "runtime_advisory": str(packet.runtime_advisory or ""),
            "retry_directives": str(packet.retry_directives or ""),
            "attempt_key": str(packet.attempt_key or ""),
            "candidate_key": str(packet.artifact_meta.get("candidate_key", "") or ""),
            "content_hash": str(packet.artifact_meta.get("content_hash", "") or ""),
            "artifact_path": str(packet.artifact_meta.get("artifact_path", "") or ""),
        }
        if repair_scope:
            payload["repair_scope"] = repair_scope
        if authoritative_fix_scope:
            payload["authoritative_fix_scope"] = authoritative_fix_scope
        if fix_pack:
            payload["fix_pack"] = fix_pack
        if repair_contract:
            payload["repair_contract"] = repair_contract
        if scope_authority:
            payload["scope_authority"] = scope_authority
        if comparison_notes:
            payload["comparison_notes"] = comparison_notes
        if selected_candidate_advisory_struct:
            payload["selected_candidate_advisory_struct"] = selected_candidate_advisory_struct
        return payload

    @staticmethod
    def _log_stage3_session_decision(
        session_logger,
        *,
        ep_num: int,
        verdict: str,
        score: int,
        arc_no: int | None,
        quality_risk: bool,
        attempt_key: str,
        candidate_key: str,
        content_hash: str,
        artifact_path: str,
        reject_reason: str = "",
        reason: str = "",
        selection_reason: str = "",
        verdict_reason: str = "",
        fix_scope: str = "",
        repair_scope: str = "",
        authoritative_fix_scope: str = "",
        fix_pack: dict | None = None,
        repair_contract: dict | None = None,
        scope_authority: dict | None = None,
        runtime_advisory: str = "",
        retry_directives: str = "",
        comparison_notes: str = "",
        selected_candidate_advisory_struct: dict | None = None,
    ) -> None:
        if not session_logger:
            return
        session_logger.log_decision(
            stage="stage3",
            ep_num=ep_num,
            decision_type="blueprint",
            result=str(verdict or ""),
            score=int(score or 0),
            arc_no=arc_no,
            quality_risk=bool(quality_risk),
            reject_reason=str(reject_reason or ""),
            reason=str(reason or ""),
            selection_reason=str(selection_reason or ""),
            verdict_reason=str(verdict_reason or ""),
            fix_scope=str(fix_scope or ""),
            repair_scope=str(repair_scope or ""),
            authoritative_fix_scope=str(authoritative_fix_scope or ""),
            **({"fix_pack": dict(fix_pack)} if isinstance(fix_pack, dict) else {}),
            **({"repair_contract": dict(repair_contract)} if isinstance(repair_contract, dict) else {}),
            **({"scope_authority": dict(scope_authority)} if isinstance(scope_authority, dict) else {}),
            runtime_advisory=str(runtime_advisory or ""),
            retry_directives=str(retry_directives or ""),
            comparison_notes=str(comparison_notes or ""),
            **(
                {"selected_candidate_advisory_struct": dict(selected_candidate_advisory_struct)}
                if isinstance(selected_candidate_advisory_struct, dict) and selected_candidate_advisory_struct
                else {}
            ),
            attempt_key=str(attempt_key or ""),
            candidate_key=str(candidate_key or ""),
            content_hash=str(content_hash or ""),
            artifact_path=str(artifact_path or ""),
        )

    @staticmethod
    def _build_stage3_stage_attempt_kwargs(
        *,
        ep_num: int,
        arc_no: int | None,
        verdict: str,
        packet: Stage3AttemptEvidencePacket,
        model: str | None,
        prompt_version: str,
        duration_ms: int | None,
        advisory_flags: dict | None,
        validate: dict | None = None,
        failure_category: str = "",
        reject_reason: str = "",
    ) -> dict:
        selection_kwargs = packet.selection_kwargs or {}
        validate = validate if isinstance(validate, dict) else {}
        resolved_advisory_flags = dict(advisory_flags or {})
        for key in ("fix_pack", "advisory_fix_pack", "partial_fix_eval"):
            value = validate.get(key)
            if isinstance(value, dict) and value:
                resolved_advisory_flags[key] = dict(value)
        repair_contract = _compact_stage3_repair_contract(validate.get("repair_contract"))
        if repair_contract:
            resolved_advisory_flags["repair_contract"] = repair_contract
        scope_authority = _compact_stage3_scope_authority(validate.get("scope_authority"))
        if scope_authority:
            resolved_advisory_flags["scope_authority"] = scope_authority
        comparison_notes = resolve_comparison_notes_text(validate.get("comparison_notes", ""))
        if comparison_notes:
            resolved_advisory_flags["comparison_notes"] = comparison_notes
        selected_candidate_advisory_struct = resolve_structured_advisory_payload(
            validate.get("selected_candidate_advisory")
        )
        if selected_candidate_advisory_struct:
            resolved_advisory_flags["selected_candidate_advisory_struct"] = selected_candidate_advisory_struct
        if repair_contract or scope_authority:
            gate_semantics = resolved_advisory_flags.get("gate_semantics")
            gate_semantics = dict(gate_semantics) if isinstance(gate_semantics, dict) else {}
            if repair_contract:
                gate_semantics["repair_contract"] = dict(repair_contract)
            if scope_authority:
                gate_semantics["scope_authority"] = dict(scope_authority)
                if scope_authority.get("repair_scope"):
                    gate_semantics["repair_scope"] = str(scope_authority.get("repair_scope") or "")
                if scope_authority.get("authoritative_fix_scope"):
                    gate_semantics["authoritative_fix_scope"] = str(
                        scope_authority.get("authoritative_fix_scope") or ""
                    )
            if gate_semantics:
                resolved_advisory_flags["gate_semantics"] = gate_semantics
        payload = {
            "stage": 3,
            "verdict": str(verdict),
            "initial_verdict": str(validate.get("verdict", "") or selection_kwargs.get("verdict", "") or ""),
            "attempt_num": packet.attempt_num,
            "ep_num": ep_num,
            "arc_num": arc_no,
            "score": packet.score,
            "model": str(model) if model else None,
            "duration_ms": duration_ms,
            "advisory_flags": resolved_advisory_flags or None,
            "session_id": packet.session_id,
            "attempt_key": packet.attempt_key,
            "prompt_version": prompt_version,
            "candidate_key": packet.candidate_key,
            "content_hash": packet.artifact_meta["content_hash"],
            "artifact_path": packet.artifact_meta["artifact_path"],
            "selection_reason": str(selection_kwargs.get("selection_reason", "") or ""),
            "verdict_reason": str(selection_kwargs.get("verdict_reason", "") or ""),
            "fix_scope": str(selection_kwargs.get("fix_scope", "") or ""),
            "fix_scope_reasoning": str(selection_kwargs.get("fix_scope_reasoning", "") or ""),
            "open_review": str(validate.get("open_review", "") or "") if isinstance(validate, dict) else "",
            "runtime_advisory": str(packet.runtime_advisory or ""),
            "retry_directives": str(packet.retry_directives or ""),
        }
        if failure_category:
            payload["failure_category"] = failure_category
        if reject_reason:
            payload["reject_reason"] = reject_reason
        return payload

    @staticmethod
    def _build_stage3_pass_rate_attempt_kwargs(
        *,
        working_ep: int,
        arc_no: int | None,
        packet: Stage3AttemptEvidencePacket,
        success: bool,
        duration_ms: int | None,
        token_cost: float,
        final_verdict: str,
        score_breakdown: dict | None,
        generation_method: str = "blueprint",
        reject_reason: str = "",
    ) -> dict:
        payload = {
            "stage": 3,
            "episode": working_ep,
            "arc": arc_no,
            "attempt_num": packet.attempt_num,
            "success": bool(success),
            "generation_method": generation_method,
            "duration_ms": duration_ms or 0,
            "token_cost": token_cost,
            "attempt_key": packet.attempt_key,
            "final_verdict": str(final_verdict or ""),
            "candidate_key": packet.candidate_key,
            "content_hash": packet.artifact_meta["content_hash"],
            "artifact_path": packet.artifact_meta["artifact_path"],
            "score_breakdown": score_breakdown or None,
        }
        if reject_reason:
            payload["reject_reason"] = str(reject_reason or "")
        return payload

    @staticmethod
    def _build_stage3_director_selection_kwargs(
        pipeline_result: dict,
        *,
        ep_num: int,
        attempt_num: int,
        attempt_key: str,
        selected_strategy: str,
        score: int,
        candidate_key: str,
        advisory_flags: dict | None = None,
        artifact_meta: dict | None = None,
    ) -> dict | None:
        """Build a Stage 3 director_selections payload when compare metadata is available."""
        if not isinstance(pipeline_result, dict):
            return None

        phases = pipeline_result.get("phases", {})
        if not isinstance(phases, dict):
            return None

        validate = phases.get("validate", {})
        if not isinstance(validate, dict) or not validate:
            return None

        verdict = str(pipeline_result.get("final_verdict") or validate.get("verdict") or "").strip()
        initial_verdict = str(validate.get("verdict") or verdict or "").strip()
        if not verdict:
            return None

        selected_index = validate.get("selected_index", 0)
        selection_reason, verdict_reason, comparison_notes = _resolve_stage3_validate_rationale(
            validate, pipeline_result
        )
        fix_scope = str(validate.get("fix_scope", "") or "").strip()

        _advisory = dict(advisory_flags or {})
        contradictions = validate.get("contradictions")
        if isinstance(contradictions, list) and contradictions:
            _advisory["contradictions"] = [str(item) for item in contradictions]
        fix_scope_reasoning = str(validate.get("fix_scope_reasoning", "") or "").strip()
        if fix_scope_reasoning:
            _advisory["fix_scope_reasoning"] = fix_scope_reasoning
        if fix_scope:
            _advisory["fix_scope"] = fix_scope
        if bool(validate.get("quality_risk", False) or pipeline_result.get("quality_risk", False)):
            _advisory["quality_risk"] = True
        if bool(validate.get("revision_required", False) or pipeline_result.get("revision_required", False)):
            _advisory["revision_required"] = True
        fix_pack = validate.get("fix_pack")
        if isinstance(fix_pack, dict) and fix_pack:
            _advisory["fix_pack"] = dict(fix_pack)
        partial_fix_eval = validate.get("partial_fix_eval")
        if isinstance(partial_fix_eval, dict) and partial_fix_eval:
            _advisory["partial_fix_eval"] = dict(partial_fix_eval)
        repair_contract = _compact_stage3_repair_contract(validate.get("repair_contract"))
        if repair_contract:
            _advisory["repair_contract"] = repair_contract
        scope_authority = _compact_stage3_scope_authority(validate.get("scope_authority"))
        if scope_authority:
            _advisory["scope_authority"] = scope_authority
        selected_candidate_advisory = validate.get("selected_candidate_advisory", {})
        selected_candidate_advisory_struct = resolve_structured_advisory_payload(selected_candidate_advisory)
        if comparison_notes:
            _advisory["comparison_notes"] = comparison_notes
        if selected_candidate_advisory_struct:
            _advisory["selected_candidate_advisory_struct"] = selected_candidate_advisory_struct

        phase = str(validate.get("phase", "") or "").strip()
        candidate_count = validate.get("candidate_count")
        try:
            candidate_count = int(candidate_count)
        except (TypeError, ValueError):
            candidate_count = 3 if phase == "director_compare" else 1

        _artifact = normalize_artifact_meta(
            artifact_meta,
            fallback_candidate_key=candidate_key,
        )

        return {
            "ep_num": ep_num,
            "round_num": attempt_num,
            "selected_label": Stage3Orchestrator._stage3_selected_label(selected_index),
            "selected_strategy": str(selected_strategy or ""),
            "verdict": initial_verdict or verdict,
            "stage": 3,
            "score": int(score or 0),
            "selection_reason": selection_reason,
            "candidate_count": max(1, int(candidate_count or 1)),
            "fix_scope": fix_scope,
            "advisory_warnings": _advisory or None,
            "verdict_reason": verdict_reason,
            "attempt_key": str(attempt_key or ""),
            "candidate_key": _artifact["candidate_key"],
            "content_hash": _artifact["content_hash"],
            "artifact_path": _artifact["artifact_path"],
            "director_thinking": str(validate.get("_director_thinking", "") or ""),
        }

    @staticmethod
    def _extract_blueprint_equipment_items(blueprint: dict | None) -> set[str]:
        if not isinstance(blueprint, dict):
            return set()
        protagonist_state = blueprint.get("protagonist_state", {})
        if not isinstance(protagonist_state, dict):
            return set()
        equipment = protagonist_state.get("equipment", [])
        if not isinstance(equipment, list):
            return set()
        return {str(item).strip() for item in equipment if str(item or "").strip()}

    @staticmethod
    def _inventory_semantic_tokens(value: str) -> set[str]:
        text = str(value or "").strip().lower()
        if not text:
            return set()
        text = _re.sub(r"['\"`“”‘’\[\]\(\){}<>:;,.!?/\\|+-]", " ", text)
        return {token for token in _re.findall(r"[a-z0-9]+|[가-힣]{2,}", text) if token and token not in {"the", "and"}}

    @classmethod
    def _inventory_items_semantically_match(cls, left: str, right: str) -> bool:
        left_text = str(left or "").strip()
        right_text = str(right or "").strip()
        if not left_text or not right_text:
            return False
        if left_text == right_text:
            return True

        left_lower = left_text.lower()
        right_lower = right_text.lower()
        if len(left_lower) >= 6 and left_lower in right_lower:
            return True
        if len(right_lower) >= 6 and right_lower in left_lower:
            return True

        left_tokens = cls._inventory_semantic_tokens(left_text)
        right_tokens = cls._inventory_semantic_tokens(right_text)
        if not left_tokens or not right_tokens:
            return False
        overlap = left_tokens & right_tokens
        if len(overlap) >= 3:
            return True
        if len(overlap) >= 2 and any(token.isascii() for token in overlap):
            return True
        return False

    @classmethod
    def _narrative_semantically_mentions_item(cls, item: str, narrative_text: str) -> bool:
        item_text = str(item or "").strip()
        text = str(narrative_text or "").strip()
        if not item_text or not text:
            return False
        if item_text in text:
            return True

        item_tokens = cls._inventory_semantic_tokens(item_text)
        text_tokens = cls._inventory_semantic_tokens(text)
        if not item_tokens or not text_tokens:
            return False
        overlap = item_tokens & text_tokens
        if len(overlap) >= 3:
            return True
        if len(item_tokens) <= 3 and overlap == item_tokens:
            return True
        return False

    def _load_previous_blueprint_owned_items(self, current_ep: int) -> set[str]:
        if current_ep <= 1:
            return set()
        db = getattr(getattr(self.ctx, "current_project", None), "db", None)
        if db is None or not hasattr(db, "get_previous_blueprint"):
            return set()
        try:
            previous_blueprint = db.get_previous_blueprint(current_ep)
        except Exception as prev_err:
            _logging.debug("[SilentPass:S3] previous blueprint inventory fallback failed: %s", prev_err)
            return set()
        return self._extract_blueprint_equipment_items(previous_blueprint)

    def _get_inventory_constraint_db(self):
        constraint_db = getattr(self.app, "constraint_db", None)
        if constraint_db is not None:
            return constraint_db
        current_project = getattr(self.ctx, "current_project", None)
        if current_project is None:
            return None
        try:
            from modules.core.constraint_db import ConstraintDB

            genre_code = ""
            selected_genre = getattr(self.ctx, "selected_genre", None)
            if isinstance(selected_genre, dict):
                genre_code = str(selected_genre.get("type", "") or "").strip()
            constraint_db = ConstraintDB(current_project, genre=genre_code or "wuxia")
        except Exception as cdb_err:
            _logging.debug("[SilentPass:S3] ConstraintDB lazy init failed: %s", cdb_err)
            return None
        try:
            setattr(self.app, "constraint_db", constraint_db)
        except Exception:
            pass
        return constraint_db

    def _detect_inventory_gaps(self, blueprint: dict, arc_data: dict, *, working_ep: int | None = None) -> list[dict]:
        """[TF-49] Blueprint 참조 아이템 중 현재 미보유 항목 탐지."""
        ctx = self.ctx

        # 1. 현재 소지품
        owned = set()
        previous_blueprint_owned = set()
        if ctx.world_state:
            try:
                owned = set(ctx.world_state.get_owned_items())
            except Exception as e:
                _logging.debug("[SilentPass:S3] get_owned_items failed: %s", e)
        if not owned:
            _cdb = self._get_inventory_constraint_db()
            if _cdb:
                try:
                    owned = set(_cdb.get_current_inventory(arc_data.get("arc_no", 1) - 1))
                except Exception as e:
                    _logging.debug("[SilentPass:S3] get_current_inventory fallback failed: %s", e)
        if working_ep and int(working_ep) > 1:
            previous_blueprint_owned = self._load_previous_blueprint_owned_items(int(working_ep))
            if not owned:
                owned = set(previous_blueprint_owned)

        # 2. Arc 계획된 신규 아이템 (미보유 중 이번 Arc에서 획득 예정)
        _sc = arc_data.get("state_constraints", {}) if isinstance(arc_data, dict) else {}
        planned = set()
        # [BUG-F] protagonist_items 우선 폴백
        for item in _sc.get("protagonist_items") or _sc.get("items_acquired") or []:
            if item:
                planned.add(str(item))
        _end_eq = set(_sc.get("arc_end_state", {}).get("equipment", []))
        _start_eq = set(_sc.get("arc_start_state", {}).get("equipment", []))
        planned |= _end_eq - _start_eq

        # 3. Blueprint 참조 아이템 (구조화 필드 우선)
        referenced = {}  # item → source
        _ps = blueprint.get("protagonist_state", {})
        if isinstance(_ps, dict):
            for item in _ps.get("equipment") or []:
                if item:
                    referenced[str(item)] = "protagonist_state"

        # planned 아이템이 씬 텍스트에 언급되는지 확인
        scenes = blueprint.get("scene_breakdown") or blueprint.get("scenes") or {}
        if isinstance(scenes, dict):
            scenes = list(scenes.values())
        if isinstance(scenes, list):
            for i, scene in enumerate(scenes):
                scene_text = ""
                if isinstance(scene, dict):
                    scene_text = " ".join(str(v) for v in scene.values() if isinstance(v, str))
                elif isinstance(scene, str):
                    scene_text = scene
                for item in planned:
                    if item and item in scene_text and item not in referenced:
                        referenced[item] = f"scene_{i + 1}"

        integrated = blueprint.get("integrated_scenario", "")
        if isinstance(integrated, str):
            for item in planned:
                if item and item in integrated and item not in referenced:
                    referenced[item] = "integrated_scenario"

        narrative_text_parts: list[str] = []
        if isinstance(integrated, str) and integrated.strip():
            narrative_text_parts.append(integrated)
        if isinstance(scenes, list):
            for scene in scenes:
                if isinstance(scene, dict):
                    scene_text = " ".join(str(v) for v in scene.values() if isinstance(v, str))
                elif isinstance(scene, str):
                    scene_text = scene
                else:
                    scene_text = ""
                if scene_text.strip():
                    narrative_text_parts.append(scene_text)
        narrative_text = "\n".join(narrative_text_parts)
        seeded_planned_items = {
            item for item in planned if self._narrative_semantically_mentions_item(item, narrative_text)
        }

        # 4. 갭 = 참조됨 + 미보유
        gaps: list[dict] = []
        for item, src in referenced.items():
            owned_by_authority = item in owned or any(
                self._inventory_items_semantically_match(item, owned_item) for owned_item in owned
            )
            if owned_by_authority:
                continue

            owned_by_prev_blueprint_alias = item in previous_blueprint_owned or any(
                self._inventory_items_semantically_match(item, prev_item) for prev_item in previous_blueprint_owned
            )
            if owned_by_prev_blueprint_alias:
                continue

            if any(
                self._inventory_items_semantically_match(item, planned_item) for planned_item in seeded_planned_items
            ):
                continue

            gaps.append({"item": item, "source": src, "note": "현재 미보유 — 획득 장면 필요"})
        return gaps

    def _handle_failure(
        self, working_ep, pipeline_result, success_count, fail_count, arc_no: int | None = None, blueprint=None
    ) -> dict:
        """Blueprint 생성 실패 시 처리. 항상 break=True를 반환하여 루프를 종료한다
        (순차 의존성: 후속 에피소드는 현재 에피소드 Blueprint에 의존)."""
        ctx = self.ctx

        ctx.ui.log(f"   ❌ 제{working_ep}화 Blueprint 생성 실패")
        _reject_reason = self._build_stage3_reject_reason(pipeline_result)
        _failure_category = _classify_stage3_failure_category(pipeline_result)
        _observability_flags = _build_stage3_observability_flags(pipeline_result.get("_stage3_observability"))
        _selected_strategy = str(
            pipeline_result.get("phases", {}).get("generate", {}).get("selected_strategy", "unknown") or "unknown"
        )
        _source_anchor_line = _format_stage3_source_anchor_summary(_observability_flags.get("source_anchor_summary"))
        ctx.ui.log(
            f"      └─ REJECT 사유: {_reject_reason}",
            stage="stage3",
            component="blueprint_generation",
            ep_num=working_ep,
            arc_num=arc_no or 0,
            event_kind="summary",
            meta={"failure_category": _failure_category, "selected_strategy": _selected_strategy},
        )
        ctx.ui.log(
            f"      판정 근거: category={_failure_category} | strategy={_selected_strategy} | "
            f"observability={','.join(_observability_flags) if _observability_flags else '-'}",
            stage="stage3",
            component="blueprint_generation",
            ep_num=working_ep,
            arc_num=arc_no or 0,
            event_kind="summary",
            meta={
                "failure_category": _failure_category,
                "selected_strategy": _selected_strategy,
                "observability_flags": _observability_flags,
            },
        )
        if _source_anchor_line:
            ctx.ui.log(
                f"      source_anchor: {_source_anchor_line}",
                stage="stage3",
                component="blueprint_generation",
                ep_num=working_ep,
                arc_num=arc_no or 0,
                event_kind="summary",
                meta={"source_anchor_summary": _observability_flags.get("source_anchor_summary")},
            )
        self._record_stage3_failure_attempt(
            working_ep=working_ep,
            pipeline_result=pipeline_result,
            arc_no=arc_no,
            blueprint=blueprint,
        )
        self._append_stage3_rejection_history(pipeline_result=pipeline_result, arc_no=arc_no)
        self._record_stage3_failure_audit_metrics(working_ep=working_ep, pipeline_result=pipeline_result)
        new_fail_count = fail_count + 1
        self._record_stage3_failure_quality_dashboard(working_ep=working_ep)
        return {
            "next_ep": working_ep,
            "success_count": success_count,
            "fail_count": new_fail_count,
            "break": True,
        }

    def _record_stage3_failure_attempt(
        self,
        *,
        working_ep,
        pipeline_result,
        arc_no: int | None = None,
        blueprint=None,
    ) -> None:
        ctx = self.ctx

        # Prepare shared reject context once, then let each sink fail independently.
        try:
            _final_verdict = str(pipeline_result.get("final_verdict", "REJECT"))
            _arc_num = self._resolve_stage3_arc_num(arc_no=arc_no, pipeline_result=pipeline_result)
            _reject_reason = self._build_stage3_reject_reason(pipeline_result)
            _observability_flags = _build_stage3_observability_flags(pipeline_result.get("_stage3_observability"))
            _pov_contract = resolve_project_pov_contract(ctx.current_project)
            _duration_ms = int(pipeline_result.get("_stage3_duration_ms") or 0) or None
            _token_cost = float(pipeline_result.get("_stage3_token_cost_usd") or 0.0)
            _failure_category = _classify_stage3_failure_category(pipeline_result)
            _packet = self._build_stage3_attempt_evidence_packet(
                working_ep=working_ep,
                arc_no=_arc_num,
                pipeline_result=pipeline_result,
                observability_flags=_observability_flags,
                blueprint=blueprint,
                artifact_kind="selected_blueprint",
                reject_reason=_reject_reason,
            )
        except Exception as _prep_err:
            _logging.debug("[stage_attempts] Stage3 REJECT prep failed (best-effort: %s)", _prep_err)
            return

        _sl = getattr(ctx, "session_logger", None)
        if _sl:
            try:
                _decision_kwargs = self._build_stage3_session_decision_kwargs(
                    ep_num=working_ep,
                    verdict=_final_verdict,
                    score=pipeline_result.get("last_score", 0),
                    arc_no=_arc_num,
                    quality_risk=bool(pipeline_result.get("quality_risk", False)),
                    packet=_packet,
                    validate=(pipeline_result.get("phases") or {}).get("validate", {})
                    if isinstance(pipeline_result, dict)
                    else {},
                    reject_reason=_reject_reason,
                    reason=str((_packet.selection_kwargs or {}).get("verdict_reason", _reject_reason) or ""),
                    selection_reason=str((_packet.selection_kwargs or {}).get("selection_reason", "") or ""),
                    verdict_reason=str((_packet.selection_kwargs or {}).get("verdict_reason", _reject_reason) or ""),
                    fix_scope=str((_packet.selection_kwargs or {}).get("fix_scope", "") or ""),
                )
                self._log_stage3_session_decision(
                    _sl,
                    **_decision_kwargs,
                )
            except Exception as _log_err:
                _logging.debug("[TF-26] session_logger.log_decision failed: %s", str(_log_err)[:100])

        if getattr(ctx, "pass_rate_monitor", None):
            try:
                _s3_rej_breakdown = {}
                _rej_validate = (
                    (pipeline_result.get("phases") or {}).get("validate", {})
                    if isinstance(pipeline_result, dict)
                    else {}
                )
                if isinstance(_rej_validate, dict):
                    _rej_raw_bd = _rej_validate.get("score_breakdown", {})
                    if isinstance(_rej_raw_bd, dict):
                        _s3_rej_breakdown = {
                            str(k): v for k, v in list(_rej_raw_bd.items())[:5] if isinstance(v, int | float)
                        }
                ctx.pass_rate_monitor.record_attempt(
                    **self._build_stage3_pass_rate_attempt_kwargs(
                        working_ep=working_ep,
                        arc_no=_arc_num,
                        packet=_packet,
                        success=False,
                        duration_ms=_duration_ms,
                        token_cost=_token_cost,
                        final_verdict=_final_verdict,
                        score_breakdown=_s3_rej_breakdown,
                        reject_reason=_reject_reason,
                    )
                )
                if hasattr(ctx.pass_rate_monitor, "_save_records"):
                    ctx.pass_rate_monitor._save_records()
            except Exception as _prm_err:
                _logging.debug("[stage3_prm] Stage3 REJECT record failed (best-effort: %s)", _prm_err)

        if _packet.db and hasattr(_packet.db, "save_stage_attempt"):
            _director = getattr(getattr(ctx, "agents", {}), "get", lambda *_: None)("director")
            _model = getattr(_director, "primary_model", None) if _director else None
            _prompt_version = _build_stage3_prompt_version()
            try:
                _s3r_validate = (
                    (pipeline_result.get("phases") or {}).get("validate", {})
                    if isinstance(pipeline_result, dict)
                    else {}
                )
                _packet.db.save_stage_attempt(
                    **self._build_stage3_stage_attempt_kwargs(
                        ep_num=working_ep,
                        arc_no=_arc_num,
                        verdict=_final_verdict,
                        packet=_packet,
                        model=str(_model) if _model else None,
                        prompt_version=_prompt_version,
                        duration_ms=_duration_ms,
                        advisory_flags=_observability_flags,
                        validate=_s3r_validate,
                        failure_category=_failure_category,
                        reject_reason=_reject_reason,
                    )
                )
            except Exception as _sa_err:
                _logging.debug("[stage_attempts] Stage3 REJECT record failed (best-effort: %s)", _sa_err)
            if hasattr(_packet.db, "save_director_selection") and _packet.selection_kwargs:
                try:
                    _packet.db.save_director_selection(**_packet.selection_kwargs)
                except Exception as _ds_err:
                    _logging.debug("[director_selections] Stage3 REJECT record failed (best-effort: %s)", _ds_err)

        try:
            _logging.info(
                "[STAGE3_EPISODE_SUMMARY] ep=%d arc=%d attempt_key=%s verdict=%s score=%s failure=%s candidate_key=%s reject_reason=%s observability=%s primary_pov=%s external_pov_insert_policy=%s style_guide_extracted_pov=%s effective_pov=%s",
                working_ep,
                _arc_num,
                _packet.attempt_key,
                _final_verdict,
                _packet.score,
                _failure_category or "-",
                _packet.candidate_key,
                _reject_reason,
                ",".join(sorted(_observability_flags.keys())) if _observability_flags else "-",
                _pov_contract.get("primary_pov", "") or "-",
                _pov_contract.get("external_pov_insert_policy", "") or "-",
                _pov_contract.get("style_guide_extracted_pov", "") or "-",
                _pov_contract.get("effective_pov", "") or "-",
            )
        except Exception as _summary_err:
            _logging.debug("[stage3_summary] Stage3 REJECT summary failed (best-effort: %s)", _summary_err)

    def _append_stage3_rejection_history(self, *, pipeline_result, arc_no: int | None = None) -> None:
        # [S3-N-P1-3] DI 콜백 None 방어
        try:
            rejection_history = getattr(self.app, "stage_rejection_history", None)
            if isinstance(rejection_history, list):
                history_arc_no = self._resolve_stage3_arc_num(arc_no=arc_no, pipeline_result=pipeline_result)
                history_reason = self._build_stage3_reject_reason(pipeline_result)
                history_failure_category = _classify_stage3_failure_category(pipeline_result) or ""
                history_attempt = self._extract_stage3_attempt_num(pipeline_result)
                validate = (pipeline_result.get("phases") or {}).get("validate", {})
                score_breakdown = {}
                if isinstance(validate, dict):
                    raw_breakdown = validate.get("score_breakdown", {})
                    if isinstance(raw_breakdown, dict):
                        score_breakdown = {
                            str(key): value
                            for key, value in list(raw_breakdown.items())[:5]
                            if isinstance(value, int | float)
                        }
                rejection_history.append(
                    {
                        "stage": 3,
                        "arc_no": history_arc_no,
                        "reason": str(history_reason or ""),
                        "attempt": history_attempt,
                        "specific_issue": str(pipeline_result.get("specific_issue", "") or ""),
                        "failure_category": history_failure_category,
                        "fix_scope": str(pipeline_result.get("fix_scope", "") or ""),
                        "score_breakdown": score_breakdown,
                    }
                )
        except Exception as _history_err:
            _logging.debug("[stage3_history] reject history append failed: %s", _history_err)

    def _record_stage3_failure_audit_metrics(self, *, working_ep, pipeline_result) -> None:
        ctx = self.ctx
        if callable(ctx.audit_event):
            ctx.audit_event(
                "blueprint_fail",
                f"ep_{working_ep}_all_retries_exhausted",
                {"ep_num": working_ep, "final_verdict": pipeline_result.get("final_verdict", "UNKNOWN")},
            )
        try:
            _final_verdict = pipeline_result.get("final_verdict", "UNKNOWN")
            _score = pipeline_result.get("last_score", 0)
            if not isinstance(_score, int | float):
                try:
                    _score = float(_score)
                except (ValueError, TypeError):
                    _score = 0
            ctx.current_project.db.save_cost_record(
                session_id=resolve_logging_session_id(
                    getattr(ctx, "current_project", None),
                    fallback=f"ep_{working_ep}",
                ),
                scope_type="episode",
                scope_id=int(working_ep),
                total_calls=0,
                total_tokens=0,
                total_cost_usd=0.0,
                model_breakdown={
                    "event": "stage3_reject",
                    "verdict": _final_verdict,
                    "score": _score,
                    "quality_gate_failed": bool(pipeline_result.get("quality_gate_failed", False)),
                },
            )
        except Exception as e:
            _logging.warning(f"[SilentPass:Stage3RejectMetric] {e!s:.120}")

    def _record_stage3_failure_quality_dashboard(self, *, working_ep) -> None:
        # [P6-02] QualityDashboard Stage3 REJECT 기록
        _qd = getattr(self.app, "quality_dashboard", None)
        if _qd is not None and hasattr(_qd, "record_validation"):
            try:
                _qd.record_validation(
                    ep_num=working_ep,
                    result={
                        "decision": "REJECT",
                        "score": 0,
                        "violations": [{"type": "blueprint_max_retries", "description": "Blueprint 최대 재시도 초과"}],
                        "warnings": [],
                    },
                    stage=3,
                )
            except Exception as _e:
                _logging.debug("[Stage3] QualityDashboard REJECT 기록 실패 (무시): %s", _e)
