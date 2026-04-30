from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any


def compact_frontier_text(value: object, *, max_chars: int = 12000) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except Exception:
            text = str(value)
    return " ".join(text.split())[:max_chars]


def extract_wti_contract_months(text: str) -> set[str]:
    if not text or "WTI" not in text:
        return set()
    return {match.group(1) for match in re.finditer(r"WTI[^.\n\r]{0,80}(\d{1,2})\s*월물", text)}


def has_completed_investment_order(text: str) -> bool:
    if not text:
        return False
    if not any(term in text for term in ("WTI", "원유", "선물")):
        return False
    return any(term in text for term in ("진입", "체결", "완료", "딸깍", "매수 포지션", "전량"))


def _strip_stable_provisional_item_names(text: str) -> str:
    if not text:
        return ""
    stable_item_names = (
        "SW인베스트먼트 사업자 등록증 가승인 서류",
        "사업자 등록증 가승인 서류",
        "법인 설립 가승인 서류",
    )
    cleaned = text
    for item_name in stable_item_names:
        cleaned = cleaned.replace(item_name, "")
    return cleaned


_LINEAGE_SIGNAL_KEYS = {
    "lineage_schema_version",
    "frontier_basis_version",
    "generated_at",
    "source_prev_manuscript_ep",
    "source_prev_manuscript_hash",
    "source_prev_manuscript_created_at",
    "lineage_complete",
    "lineage_missing_reason",
    "genre_strategy_contract_id",
}


def _blueprint_lineage_meta(
    *,
    blueprint: dict,
    blueprint_lineage: dict | None = None,
) -> tuple[dict[str, Any], str]:
    if isinstance(blueprint_lineage, dict) and any(blueprint_lineage.get(key) for key in _LINEAGE_SIGNAL_KEYS):
        return dict(blueprint_lineage), "db_blueprint_lineage"
    stage3_meta = blueprint.get("_stage3_meta") if isinstance(blueprint, dict) else {}
    if not isinstance(stage3_meta, dict):
        return {}, ""
    return dict(stage3_meta), "_stage3_meta"


def _stage3_lineage_matches_prev_manuscript(
    *,
    ep_num: int,
    blueprint: dict,
    prev_manuscript_text: str,
    blueprint_lineage: dict | None = None,
) -> bool:
    lineage_meta, _source = _blueprint_lineage_meta(blueprint=blueprint, blueprint_lineage=blueprint_lineage)
    if not lineage_meta:
        return False

    recorded_prev_hash = str(lineage_meta.get("source_prev_manuscript_hash") or "").strip()
    if not recorded_prev_hash or not prev_manuscript_text:
        return False

    current_prev_hash = hashlib.sha256(str(prev_manuscript_text or "").encode("utf-8")).hexdigest()
    if recorded_prev_hash != current_prev_hash:
        return False

    try:
        recorded_prev_ep = int(lineage_meta.get("source_prev_manuscript_ep") or 0)
    except (TypeError, ValueError):
        recorded_prev_ep = 0
    if recorded_prev_ep and recorded_prev_ep != int(ep_num or 0) - 1:
        return False
    return True


def detect_stage4_frontier_staleness(
    *,
    ep_num: int,
    blueprint: dict,
    arc_data: dict,
    prev_manuscript_text: str,
    blueprint_lineage: dict | None = None,
) -> dict:
    """Detect hard stale-frontier pressure without rewriting narrative facts."""

    prev_text = compact_frontier_text(prev_manuscript_text, max_chars=8000)
    lineage_meta, lineage_source = _blueprint_lineage_meta(blueprint=blueprint, blueprint_lineage=blueprint_lineage)
    recorded_prev_hash = ""
    if lineage_meta:
        recorded_prev_hash = str(lineage_meta.get("source_prev_manuscript_hash") or "").strip()
    current_prev_hash = hashlib.sha256(str(prev_manuscript_text or "").encode("utf-8")).hexdigest() if prev_text else ""
    if recorded_prev_hash and current_prev_hash and recorded_prev_hash != current_prev_hash:
        return {
            "stale": True,
            "severity": "hard",
            "reasons": ["Stage3 blueprint was generated from a different prior manuscript hash"],
            "evidence": {
                "ep_num": int(ep_num or 0),
                "recorded_prev_manuscript_hash": recorded_prev_hash,
                "current_prev_manuscript_hash": current_prev_hash,
                "source": f"{lineage_source or 'stage3_meta'}+accepted_prev_manuscript",
            },
        }
    stage3_lineage_matches_prev = _stage3_lineage_matches_prev_manuscript(
        ep_num=ep_num,
        blueprint=blueprint,
        prev_manuscript_text=prev_manuscript_text,
        blueprint_lineage=blueprint_lineage,
    )

    if not has_completed_investment_order(prev_text):
        return {"stale": False, "severity": "none", "reasons": [], "evidence": {}}

    frontier_parts = [compact_frontier_text(blueprint)]
    if not stage3_lineage_matches_prev:
        frontier_parts.extend(
            [
                compact_frontier_text(arc_data.get("tactical_doc", "") if isinstance(arc_data, dict) else ""),
                compact_frontier_text(arc_data.get("episode_details", []) if isinstance(arc_data, dict) else []),
            ]
        )
    frontier_text = "\n".join(part for part in frontier_parts if part)
    if not frontier_text:
        return {"stale": False, "severity": "none", "reasons": [], "evidence": {}}

    prev_months = extract_wti_contract_months(prev_text)
    frontier_months = extract_wti_contract_months(frontier_text)
    order_replay_terms = [term for term in ("매수 지시", "진입", "포지션", "주문", "체결") if term in frontier_text]

    reasons: list[str] = []
    if prev_months and frontier_months and not frontier_months.issubset(prev_months):
        reasons.append(
            "accepted prior manuscript completed WTI contract month "
            f"{sorted(prev_months)}, but current frontier carries {sorted(frontier_months)}"
        )
    if (
        not stage3_lineage_matches_prev
        and prev_months
        and frontier_months.intersection(prev_months)
        and order_replay_terms
    ):
        reasons.append(
            "current frontier appears to replay an already completed WTI order event "
            f"({', '.join(order_replay_terms[:4])})"
        )
    provisional_check_text = _strip_stable_provisional_item_names(frontier_text)
    if ("가승인" in provisional_check_text) and any(term in prev_text for term in ("딸깍", "완료", "진입")):
        reasons.append("current frontier still carries provisional approval language after accepted execution")

    if not reasons:
        return {"stale": False, "severity": "none", "reasons": [], "evidence": {}}

    return {
        "stale": True,
        "severity": "hard",
        "reasons": reasons,
        "evidence": {
            "ep_num": int(ep_num or 0),
            "prev_wti_months": sorted(prev_months),
            "frontier_wti_months": sorted(frontier_months),
            "order_replay_terms": order_replay_terms[:6],
            "source": "accepted_prev_manuscript+stage3_frontier",
            "lineage_source": lineage_source or "",
            "stage3_lineage_matches_prev_manuscript": stage3_lineage_matches_prev,
        },
    }


def frontier_status_satisfied_by_stage3_lineage(
    *,
    blueprint: dict,
    frontier_status: dict,
    prev_manuscript_text: str,
    blueprint_lineage: dict | None = None,
) -> bool:
    if not isinstance(blueprint, dict) or not isinstance(frontier_status, dict):
        return False
    if frontier_status.get("status") != "requires_actual_manuscript_revalidation":
        return False

    lineage_meta, _lineage_source = _blueprint_lineage_meta(blueprint=blueprint, blueprint_lineage=blueprint_lineage)
    status_evidence = frontier_status.get("evidence", {})
    if not lineage_meta or not isinstance(status_evidence, dict):
        return False

    try:
        recorded_prev_ep = int(lineage_meta.get("source_prev_manuscript_ep") or 0)
        accepted_ep = int(status_evidence.get("accepted_ep") or 0)
    except (TypeError, ValueError):
        return False
    recorded_prev_hash = str(lineage_meta.get("source_prev_manuscript_hash") or "").strip()
    accepted_hash = str(status_evidence.get("accepted_manuscript_hash") or "").strip()
    current_prev_hash = (
        hashlib.sha256(str(prev_manuscript_text or "").encode("utf-8")).hexdigest() if prev_manuscript_text else ""
    )
    return (
        recorded_prev_ep > 0
        and recorded_prev_ep == accepted_ep
        and bool(recorded_prev_hash)
        and bool(accepted_hash)
        and recorded_prev_hash == accepted_hash == current_prev_hash
    )


def mark_downstream_frontier_status(
    *,
    project: object,
    ep_start: int,
    ep_end: int,
    status: str,
    detected_at_stage: str,
    detected_before_ep: int,
    reasons: list[Any] | None = None,
    evidence: dict | None = None,
) -> list[int]:
    """Mark future blueprint metadata; do not rewrite story facts."""

    get_blueprint = getattr(project, "get_blueprint", None)
    save_blueprint = getattr(project, "save_episode_blueprint", None)
    if not callable(get_blueprint) or not callable(save_blueprint):
        return []

    marked: list[int] = []
    safe_ep_start = int(ep_start or 0)
    safe_ep_end = int(ep_end or safe_ep_start)
    for candidate_ep in range(safe_ep_start, safe_ep_end + 1):
        try:
            bp = get_blueprint(candidate_ep)
        except Exception:
            continue
        if not isinstance(bp, dict) or not bp:
            continue
        patched_bp = copy.deepcopy(bp)
        patched_bp["_frontier_status"] = {
            "status": str(status or ""),
            "detected_at_stage": str(detected_at_stage or ""),
            "detected_before_ep": int(detected_before_ep or 0),
            "affected_ep": int(candidate_ep),
            "authority_note": "Python marked routing metadata only; Director/LLM owns narrative correction.",
            "reasons": [str(reason) for reason in (reasons or [])[:5]],
            "evidence": dict(evidence or {}),
        }
        try:
            save_blueprint(candidate_ep, patched_bp)
            marked.append(candidate_ep)
        except Exception:
            continue
    return marked


def resolve_arc_end_episode(*, arc_data: dict, fallback_ep: int) -> int:
    payload = arc_data if isinstance(arc_data, dict) else {}
    for key in ("ep_end", "end_ep", "episode_end"):
        try:
            value = int(payload.get(key) or 0)
        except (TypeError, ValueError):
            value = 0
        if value > 0:
            return value
    try:
        ep_start = int(payload.get("ep_start") or 0)
        ep_count = int(payload.get("ep_count") or 0)
    except (TypeError, ValueError):
        ep_start = 0
        ep_count = 0
    if ep_start > 0 and ep_count > 0:
        return ep_start + ep_count - 1
    return int(fallback_ep or 0)


def mark_downstream_frontier_contaminated(
    *,
    project: object,
    ep_num: int,
    arc_data: dict,
    stale_check: dict,
) -> list[int]:
    arc_end = resolve_arc_end_episode(arc_data=arc_data, fallback_ep=ep_num)
    return mark_downstream_frontier_status(
        project=project,
        ep_start=int(ep_num or 0),
        ep_end=arc_end,
        status="contaminated_requires_regeneration",
        detected_at_stage="stage4_preflight",
        detected_before_ep=int(ep_num or 0),
        reasons=list(stale_check.get("reasons") or []),
        evidence=dict(stale_check.get("evidence") or {}),
    )


def mark_downstream_frontier_requires_adjudication(
    *,
    project: object,
    ep_num: int,
    arc_data: dict,
    stale_check: dict,
) -> list[int]:
    arc_end = resolve_arc_end_episode(arc_data=arc_data, fallback_ep=ep_num)
    return mark_downstream_frontier_status(
        project=project,
        ep_start=int(ep_num or 0),
        ep_end=arc_end,
        status="requires_director_frontier_adjudication",
        detected_at_stage="stage4_preflight",
        detected_before_ep=int(ep_num or 0),
        reasons=list(stale_check.get("reasons") or []),
        evidence=dict(stale_check.get("evidence") or {}),
    )


def mark_downstream_frontier_requires_revalidation(
    *,
    project: object,
    accepted_ep: int,
    arc_data: dict,
    manuscript_hash: str = "",
) -> list[int]:
    arc_end = resolve_arc_end_episode(arc_data=arc_data, fallback_ep=accepted_ep)
    if arc_end <= int(accepted_ep or 0):
        return []
    return mark_downstream_frontier_status(
        project=project,
        ep_start=int(accepted_ep or 0) + 1,
        ep_end=arc_end,
        status="requires_actual_manuscript_revalidation",
        detected_at_stage="stage4_pass_settlement",
        detected_before_ep=int(accepted_ep or 0) + 1,
        reasons=["prior Stage4 manuscript accepted after downstream Stage3 frontier may have been generated"],
        evidence={
            "accepted_ep": int(accepted_ep or 0),
            "accepted_manuscript_hash": str(manuscript_hash or ""),
            "source": "stage4_fully_settled_pass",
        },
    )
