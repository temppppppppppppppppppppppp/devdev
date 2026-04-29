"""Stage3 blueprint lineage metadata helpers."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from modules.core.final_accepted_context import load_final_accepted_manuscript_row

BLUEPRINT_LINEAGE_SCHEMA_VERSION = "stage3-blueprint-lineage-v1"
FRONTIER_BASIS_VERSION = "stage3-frontier-basis-v1"


def _compact_contract_id(blueprint: dict[str, Any]) -> str:
    ensemble_meta = blueprint.get("_ensemble_meta")
    if not isinstance(ensemble_meta, dict):
        return ""

    contract = ensemble_meta.get("genre_strategy_contract")
    if isinstance(contract, dict):
        contract_id = str(contract.get("contract_id") or "").strip()
        if contract_id:
            return contract_id

    prompt_envelope = ensemble_meta.get("prompt_envelope")
    contracts = prompt_envelope.get("genre_strategy_contracts") if isinstance(prompt_envelope, dict) else None
    if isinstance(contracts, list):
        for item in contracts:
            if not isinstance(item, dict):
                continue
            contract_id = str(item.get("contract_id") or "").strip()
            if contract_id:
                return contract_id
    return ""


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
        contract_id = _compact_contract_id(blueprint)
        if contract_id:
            meta["genre_strategy_contract_id"] = contract_id

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
