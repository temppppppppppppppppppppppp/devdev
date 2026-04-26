from __future__ import annotations

import copy
import json
from collections.abc import Mapping, Sequence
from typing import Any

AUTHORITATIVE_CONTINUITY_PROJECTION_VERSION = "authoritative-continuity-projection-v1"
AUTHORITATIVE_CONTINUITY_PROJECTION_KEY = "authoritative_continuity_projection"
AUTHORITATIVE_CONTINUITY_PROJECTION_HEADER = "[Authoritative Continuity Projection]"

_APPROVED_BRIDGE_STATUSES = {"approved", "applied"}
_PENDING_BRIDGE_STATUSES = {"pending_director", "escalate"}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    return str(value)


def _as_dict(value: Any) -> dict[str, Any]:
    return copy.deepcopy(_json_safe(value)) if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return []


def _compact_text(value: Any, *, limit: int = 240) -> str:
    text = " ".join(str(value or "").split()).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _first_text(*values: Any, limit: int = 240) -> str:
    for value in values:
        text = _compact_text(value, limit=limit)
        if text:
            return text
    return ""


def _select_accepted_blueprint(
    *,
    accepted_blueprint: Mapping[str, Any] | None,
    prev_blueprint: Mapping[str, Any] | None,
    prev_blueprints: Sequence[Any] | None,
    ep_num: int,
) -> dict[str, Any]:
    for candidate in (accepted_blueprint, prev_blueprint):
        if isinstance(candidate, Mapping) and candidate:
            return _as_dict(candidate)

    selected: dict[str, Any] = {}
    for item in prev_blueprints or []:
        if not isinstance(item, Mapping):
            continue
        item_ep = _safe_int(item.get("ep_num") or item.get("episode_number"))
        if item_ep and ep_num and item_ep >= ep_num:
            continue
        if not selected or item_ep >= _safe_int(selected.get("ep_num") or selected.get("episode_number")):
            selected = _as_dict(item)
    return selected


def _extract_arc_contract(arc_data: Mapping[str, Any] | None) -> dict[str, Any]:
    arc = _as_dict(arc_data)
    state_constraints = _as_dict(arc.get("state_constraints"))
    semantic_carryover = _as_dict(arc.get("semantic_carryover"))
    return {
        key: value
        for key, value in {
            "arc_no": arc.get("arc_no"),
            "ep_start": arc.get("ep_start"),
            "ep_end": arc.get("ep_end"),
            "title": _first_text(arc.get("title"), arc.get("arc_title"), limit=120),
            "constraint_summary": _first_text(
                arc.get("constraint_summary"),
                arc.get("arc_constraint_summary"),
                arc.get("block_theme"),
                limit=280,
            ),
            "arc_start_state": _as_dict(state_constraints.get("arc_start_state")),
            "arc_end_state": _as_dict(state_constraints.get("arc_end_state")),
            "semantic_carryover_keys": [
                str(key).strip() for key in semantic_carryover.keys() if str(key or "").strip()
            ][:12],
        }.items()
        if value not in ("", [], {}, None)
    }


def _extract_accepted_source_state(
    blueprint: Mapping[str, Any] | None,
    *,
    prev_manuscript_ending: str = "",
) -> dict[str, Any]:
    bp = _as_dict(blueprint)
    opening_transition = _as_dict(bp.get("opening_transition"))
    protagonist_state = _as_dict(bp.get("protagonist_state"))
    ending_state = _as_dict(bp.get("ending_state"))
    return {
        key: value
        for key, value in {
            "ep_num": bp.get("ep_num") or bp.get("episode_number"),
            "title": _first_text(bp.get("title"), bp.get("episode_title"), limit=120),
            "summary": _first_text(bp.get("summary"), bp.get("integrated_scenario"), limit=320),
            "start_location": _first_text(bp.get("start_location"), bp.get("location"), limit=120),
            "end_location": _first_text(bp.get("end_location"), ending_state.get("location"), limit=120),
            "time_flow": _first_text(
                bp.get("time_flow"), bp.get("time_context"), ending_state.get("timeline"), limit=160
            ),
            "ending_hook": _first_text(bp.get("ending_hook"), bp.get("ending"), prev_manuscript_ending, limit=320),
            "opening_transition_type": _first_text(opening_transition.get("type"), limit=80),
            "protagonist_state": protagonist_state,
        }.items()
        if value not in ("", [], {}, None)
    }


def _build_non_regression_anchors(
    *,
    accepted_state: Mapping[str, Any],
    arc_contract: Mapping[str, Any],
) -> list[dict[str, str]]:
    anchors: list[dict[str, str]] = []

    end_location = _compact_text(accepted_state.get("end_location"), limit=120)
    start_location = _compact_text(accepted_state.get("start_location"), limit=120)
    time_flow = _compact_text(accepted_state.get("time_flow"), limit=160)
    ending_hook = _compact_text(accepted_state.get("ending_hook"), limit=220)
    arc_start = _as_dict(arc_contract.get("arc_start_state"))
    arc_start_location = _compact_text(arc_start.get("location"), limit=120)

    if end_location:
        anchors.append(
            {
                "anchor_key": "accepted_source_end_location",
                "expected": end_location,
                "route_instruction": "Honor this location or explicitly transition away before new action.",
            }
        )
    elif start_location:
        anchors.append(
            {
                "anchor_key": "accepted_source_start_location",
                "expected": start_location,
                "route_instruction": "Use as the default opening location unless the source explicitly moves away.",
            }
        )

    if time_flow:
        anchors.append(
            {
                "anchor_key": "accepted_source_time_flow",
                "expected": time_flow,
                "route_instruction": "Advance from this time context; do not silently reset to an earlier state.",
            }
        )
    if ending_hook:
        anchors.append(
            {
                "anchor_key": "accepted_source_ending_hook",
                "expected": ending_hook,
                "route_instruction": "Resolve or deliberately transition from this hook before opening a new thread.",
            }
        )
    if arc_start_location:
        anchors.append(
            {
                "anchor_key": "arc_start_location",
                "expected": arc_start_location,
                "route_instruction": "Treat as arc-level source context, below accepted episode-specific state.",
            }
        )
    return anchors[:8]


def _parse_jsonish(value: Any) -> Any:
    if not isinstance(value, str):
        return _json_safe(value)
    text = value.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _normalize_bridge_proposal(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "bridge_id": _compact_text(row.get("bridge_id"), limit=120),
            "source_stage": _compact_text(row.get("source_stage"), limit=40),
            "target_stage": _compact_text(row.get("target_stage"), limit=40),
            "arc_num": row.get("arc_num"),
            "ep_num": row.get("ep_num"),
            "authority_source": _compact_text(row.get("authority_source"), limit=120),
            "observed_conflict": _parse_jsonish(row.get("observed_conflict")),
            "proposed_bridge": _parse_jsonish(row.get("proposed_bridge")),
            "allowed_fix_scope": _compact_text(row.get("allowed_fix_scope"), limit=80),
            "director_verdict": _compact_text(row.get("director_verdict"), limit=80),
            "director_reason": _compact_text(row.get("director_reason"), limit=200),
            "applied_status": _compact_text(row.get("applied_status"), limit=80),
            "applied_artifact_key": _compact_text(row.get("applied_artifact_key"), limit=160),
            "source_hashes": _parse_jsonish(row.get("source_hashes")),
        }.items()
        if value not in ("", [], {}, None)
    }


def _partition_bridge_proposals(rows: Sequence[Any] | None) -> dict[str, list[dict[str, Any]]]:
    approved: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for row in rows or []:
        if not isinstance(row, Mapping):
            continue
        normalized = _normalize_bridge_proposal(row)
        status = str(normalized.get("applied_status", "") or "").strip().lower()
        if status in _APPROVED_BRIDGE_STATUSES:
            approved.append(normalized)
        elif status in _PENDING_BRIDGE_STATUSES:
            pending.append(normalized)
        else:
            rejected.append(normalized)
    return {
        "approved": approved[:6],
        "pending_director": pending[:6],
        "rejected_or_other": rejected[:6],
    }


def load_continuity_bridge_proposals_for_projection(
    db: Any,
    *,
    target_stage: str,
    ep_num: int | None = None,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """Load bridge rows for prompt projection without adjudicating them."""
    getter = getattr(db, "get_continuity_bridge_proposals", None)
    if not callable(getter):
        return []

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    statuses = ("approved", "pending_director", "escalate")
    for status in statuses:
        try:
            result = getter(applied_status=status, target_stage=target_stage, limit=limit)
        except TypeError:
            result = getter(applied_status=status, limit=limit)
        except Exception:
            continue
        if not isinstance(result, list):
            continue
        for row in result:
            if not isinstance(row, Mapping):
                continue
            if ep_num not in (None, 0):
                row_ep = row.get("ep_num")
                if row_ep not in (None, "", 0) and _safe_int(row_ep) != int(ep_num):
                    continue
            bridge_id = str(row.get("bridge_id") or "").strip()
            marker = bridge_id or json.dumps(_json_safe(row), ensure_ascii=False, sort_keys=True)
            if marker in seen_ids:
                continue
            seen_ids.add(marker)
            rows.append(_as_dict(row))
            if len(rows) >= limit:
                return rows
    return rows


def build_authoritative_continuity_projection(
    *,
    ep_num: int,
    arc_data: Mapping[str, Any] | None = None,
    accepted_blueprint: Mapping[str, Any] | None = None,
    prev_blueprint: Mapping[str, Any] | None = None,
    prev_blueprints: Sequence[Any] | None = None,
    prev_manuscript_ending: str = "",
    bridge_proposals: Sequence[Any] | None = None,
    source_stage: str = "",
    target_stage: str = "",
) -> dict[str, Any]:
    """Build a typed continuity packet; it routes source truth, never decides narrative truth."""
    safe_ep_num = _safe_int(ep_num)
    source_blueprint = _select_accepted_blueprint(
        accepted_blueprint=accepted_blueprint,
        prev_blueprint=prev_blueprint,
        prev_blueprints=prev_blueprints,
        ep_num=safe_ep_num,
    )
    accepted_state = _extract_accepted_source_state(
        source_blueprint,
        prev_manuscript_ending=prev_manuscript_ending,
    )
    arc_contract = _extract_arc_contract(arc_data)
    bridges = _partition_bridge_proposals(bridge_proposals)

    projection = {
        "schema_version": AUTHORITATIVE_CONTINUITY_PROJECTION_VERSION,
        "authority_role": "typed_route_packet_not_final_verdict",
        "judgment_authority": "director_llm",
        "mutation_policy": "python_may_collect_and_route_only",
        "source_stage": str(source_stage or ""),
        "target_stage": str(target_stage or ""),
        "ep_num": safe_ep_num,
        "arc_num": arc_contract.get("arc_no"),
        "accepted_source_state": accepted_state,
        "arc_contract": arc_contract,
        "non_regression_anchors": _build_non_regression_anchors(
            accepted_state=accepted_state,
            arc_contract=arc_contract,
        ),
        "bridge_proposals": bridges,
    }
    return {key: value for key, value in projection.items() if value not in ("", [], {}, None)}


def summarize_authoritative_continuity_projection(projection: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _as_dict(projection)
    bridges = _as_dict(payload.get("bridge_proposals"))
    return {
        key: value
        for key, value in {
            "schema_version": payload.get("schema_version"),
            "source_stage": payload.get("source_stage"),
            "target_stage": payload.get("target_stage"),
            "ep_num": payload.get("ep_num"),
            "arc_num": payload.get("arc_num"),
            "accepted_source_fields": sorted(_as_dict(payload.get("accepted_source_state")).keys()),
            "non_regression_anchor_count": len(_as_list(payload.get("non_regression_anchors"))),
            "approved_bridge_count": len(_as_list(bridges.get("approved"))),
            "pending_bridge_count": len(_as_list(bridges.get("pending_director"))),
        }.items()
        if value not in ("", [], {}, None, 0)
    }


def render_authoritative_continuity_projection_for_prompt(
    projection: Mapping[str, Any] | None,
    *,
    max_chars: int = 2600,
) -> str:
    payload = _as_dict(projection)
    if not payload:
        return ""

    anchors = _as_list(payload.get("non_regression_anchors"))
    bridges = _as_dict(payload.get("bridge_proposals"))
    approved_bridges = _as_list(bridges.get("approved"))
    pending_bridges = _as_list(bridges.get("pending_director"))
    accepted_state = _as_dict(payload.get("accepted_source_state"))
    arc_contract = _as_dict(payload.get("arc_contract"))

    if not any([anchors, approved_bridges, pending_bridges, accepted_state, arc_contract]):
        return ""

    lines = [
        AUTHORITATIVE_CONTINUITY_PROJECTION_HEADER,
        "- role: typed route packet; Director/LLM remains final narrative judge.",
        "- mutation_policy: Python collected this packet only; do not treat it as automatic fact rewrite.",
        f"- flow: {payload.get('source_stage', '?')} -> {payload.get('target_stage', '?')} / ep={payload.get('ep_num', '?')} / arc={payload.get('arc_num', '?')}",
    ]
    if accepted_state:
        state_items = []
        for key in ("ep_num", "title", "start_location", "end_location", "time_flow", "opening_transition_type"):
            value = _compact_text(accepted_state.get(key), limit=120)
            if value:
                state_items.append(f"{key}={value}")
        ending_hook = _compact_text(accepted_state.get("ending_hook"), limit=180)
        if ending_hook:
            state_items.append(f"ending_hook={ending_hook}")
        if state_items:
            lines.append("- accepted_source_state: " + "; ".join(state_items[:7]))
    if arc_contract:
        arc_items = []
        for key in ("ep_start", "ep_end", "title", "constraint_summary"):
            value = _compact_text(arc_contract.get(key), limit=160)
            if value:
                arc_items.append(f"{key}={value}")
        if arc_items:
            lines.append("- arc_contract: " + "; ".join(arc_items[:4]))
    if anchors:
        lines.append("- non_regression_anchors:")
        for anchor in anchors[:6]:
            if not isinstance(anchor, Mapping):
                continue
            lines.append(
                "  * "
                + _compact_text(anchor.get("anchor_key"), limit=80)
                + ": "
                + _compact_text(anchor.get("expected"), limit=160)
                + " | "
                + _compact_text(anchor.get("route_instruction"), limit=180)
            )
    if approved_bridges:
        lines.append("- director_approved_bridges:")
        for bridge in approved_bridges[:3]:
            if not isinstance(bridge, Mapping):
                continue
            lines.append(
                "  * "
                + _compact_text(bridge.get("bridge_id"), limit=80)
                + " | scope="
                + _compact_text(bridge.get("allowed_fix_scope"), limit=80)
                + " | "
                + _compact_text(bridge.get("proposed_bridge"), limit=220)
            )
    if pending_bridges:
        lines.append(
            f"- pending_director_bridge_count: {len(pending_bridges)} "
            "(surface only; do not apply as fact until Director approves)"
        )

    rendered = "\n".join(line for line in lines if line.strip())
    if len(rendered) <= max_chars:
        return rendered
    return rendered[: max(0, max_chars - 3)].rstrip() + "..."
