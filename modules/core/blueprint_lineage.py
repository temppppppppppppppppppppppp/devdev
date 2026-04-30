"""Stage3 blueprint lineage metadata helpers."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from modules.core.final_accepted_context import load_final_accepted_manuscript_row
from modules.core.genre_contract_transport import extract_stage3_genre_contract_summary

BLUEPRINT_LINEAGE_SCHEMA_VERSION = "stage3-blueprint-lineage-v1"
FRONTIER_BASIS_VERSION = "stage3-frontier-basis-v1"


def _attach_contract_summary(meta: dict[str, Any], blueprint: dict[str, Any]) -> None:
    summary = extract_stage3_genre_contract_summary(blueprint)
    if not summary:
        return
    field_map = {
        "contract_id": "genre_strategy_contract_id",
        "contract_hash": "genre_strategy_contract_hash",
        "authority_level": "genre_strategy_contract_authority_level",
        "strategy_name": "genre_strategy_contract_strategy",
        "source": "genre_strategy_contract_source",
        "coverage_outcome": "genre_strategy_contract_coverage_outcome",
    }
    for source_key, meta_key in field_map.items():
        value = str(summary.get(source_key) or "").strip()
        if value:
            meta[meta_key] = value


def build_stage3_blueprint_lineage_meta(
    *,
    db: object,
    ep_num: int,
    blueprint: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build deterministic lineage metadata for a Stage3 blueprint."""

    try:
        episode = int(ep_num or 0)
    except (TypeError, ValueError):
        episode = 0

    prev_ep = episode - 1 if episode > 1 else 0
    meta: dict[str, Any] = {
        "lineage_schema_version": BLUEPRINT_LINEAGE_SCHEMA_VERSION,
        "generated_at": generated_at or datetime.now(UTC).isoformat(),
        "frontier_basis_version": FRONTIER_BASIS_VERSION,
        "source_prev_manuscript_ep": prev_ep,
        "source_prev_manuscript_hash": "",
        "source_prev_manuscript_created_at": "",
        "lineage_complete": False,
        "lineage_missing_reason": "",
    }

    if isinstance(blueprint, dict):
        _attach_contract_summary(meta, blueprint)

    if prev_ep <= 0:
        meta["lineage_complete"] = True
        meta["lineage_missing_reason"] = "no_prior_episode"
        return meta

    prev_row = load_final_accepted_manuscript_row(db, prev_ep)
    prev_text = str((prev_row or {}).get("content") or "")
    if not prev_text:
        meta["lineage_missing_reason"] = "missing_final_accepted_prev_manuscript"
        return meta

    meta["source_prev_manuscript_hash"] = hashlib.sha256(prev_text.encode("utf-8")).hexdigest()
    meta["source_prev_manuscript_created_at"] = str(
        (prev_row or {}).get("manuscript_created_at") or (prev_row or {}).get("created_at") or ""
    )
    meta["lineage_complete"] = True
    return meta


def attach_stage3_blueprint_lineage_meta(
    blueprint: dict[str, Any],
    *,
    db: object,
    ep_num: int,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Attach lineage metadata while preserving existing Stage3 metadata."""

    if not isinstance(blueprint, dict):
        return blueprint
    existing = blueprint.get("_stage3_meta")
    merged = dict(existing) if isinstance(existing, dict) else {}
    lineage = build_stage3_blueprint_lineage_meta(
        db=db,
        ep_num=ep_num,
        blueprint=blueprint,
        generated_at=generated_at or str(merged.get("generated_at") or ""),
    )
    merged.update(lineage)
    blueprint["_stage3_meta"] = merged
    return blueprint
