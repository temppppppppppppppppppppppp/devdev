"""Genre strategy contract transport helpers."""

from __future__ import annotations

from typing import Any

GENRE_CONTRACT_TRANSPORT_SCHEMA_VERSION = "genre-contract-transport-v1"
STAGE4_GENRE_CONTRACT_HEADER = "[Stage4 Genre Strategy Contract]"


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _first_prompt_contract(ensemble_meta: dict[str, Any], *, strategy_name: str = "") -> dict[str, Any]:
    prompt_envelope = ensemble_meta.get("prompt_envelope")
    contracts = prompt_envelope.get("genre_strategy_contracts") if isinstance(prompt_envelope, dict) else None
    if not isinstance(contracts, list):
        return {}
    if strategy_name:
        for item in contracts:
            if not isinstance(item, dict):
                continue
            if _clean_text(item.get("strategy_name")) == strategy_name and _clean_text(item.get("contract_id")):
                return item
        return {}
    for item in contracts:
        if isinstance(item, dict) and _clean_text(item.get("contract_id")):
            return item
    return {}


def _first_coverage_entry(ensemble_meta: dict[str, Any], *, strategy_name: str = "") -> dict[str, Any]:
    prompt_envelope = ensemble_meta.get("prompt_envelope")
    coverage = prompt_envelope.get("genre_strategy_contract_coverage") if isinstance(prompt_envelope, dict) else None
    if not isinstance(coverage, list):
        return {}
    if strategy_name:
        for item in coverage:
            if not isinstance(item, dict):
                continue
            if _clean_text(item.get("strategy_name")) == strategy_name and _clean_text(item.get("coverage_outcome")):
                return item
    for item in coverage:
        if isinstance(item, dict) and _clean_text(item.get("coverage_outcome")):
            return item
    return {}


def extract_stage3_genre_contract_summary(blueprint: dict[str, Any] | None) -> dict[str, Any]:
    """Return compact Stage3 genre-contract evidence without judging prose quality."""

    if not isinstance(blueprint, dict):
        return {}

    ensemble_meta = blueprint.get("_ensemble_meta")
    ensemble_meta = ensemble_meta if isinstance(ensemble_meta, dict) else {}
    stage3_meta = blueprint.get("_stage3_meta")
    stage3_meta = stage3_meta if isinstance(stage3_meta, dict) else {}
    selected_strategy = _clean_text(ensemble_meta.get("strategy"))

    contract = ensemble_meta.get("genre_strategy_contract")
    if isinstance(contract, dict) and _clean_text(contract.get("contract_id")):
        source = "_ensemble_meta.genre_strategy_contract"
    else:
        contract = _first_prompt_contract(ensemble_meta, strategy_name=selected_strategy)
        source = "_ensemble_meta.prompt_envelope.genre_strategy_contracts" if contract else ""

    coverage = _first_coverage_entry(ensemble_meta, strategy_name=selected_strategy)
    contract_id = _clean_text(contract.get("contract_id")) if isinstance(contract, dict) else ""
    if not contract_id:
        contract_id = _clean_text(stage3_meta.get("genre_strategy_contract_id"))
        if contract_id and not source:
            source = "_stage3_meta.genre_strategy_contract_id"

    if not contract_id and not coverage:
        return {}

    summary = {
        "schema_version": GENRE_CONTRACT_TRANSPORT_SCHEMA_VERSION,
        "contract_id": contract_id,
        "contract_hash": _clean_text(contract.get("contract_hash")) if isinstance(contract, dict) else "",
        "authority_level": _clean_text(contract.get("authority_level")) if isinstance(contract, dict) else "",
        "strategy_name": _clean_text(contract.get("strategy_name")) if isinstance(contract, dict) else "",
        "genre_type": _clean_text(contract.get("genre_type")) if isinstance(contract, dict) else "",
        "source": source,
        "coverage_outcome": _clean_text(coverage.get("coverage_outcome")) if isinstance(coverage, dict) else "",
    }
    if not summary["coverage_outcome"] and contract_id:
        summary["coverage_outcome"] = "route_contract_applied"
    if not summary["authority_level"] and contract_id:
        summary["authority_level"] = _clean_text(stage3_meta.get("genre_strategy_contract_authority_level")) or "route"
    if not summary["strategy_name"]:
        summary["strategy_name"] = _clean_text(coverage.get("strategy_name")) or _clean_text(
            stage3_meta.get("genre_strategy_contract_strategy")
        )
    if not summary["genre_type"]:
        summary["genre_type"] = _clean_text(coverage.get("genre_type"))
    if not summary["contract_hash"]:
        summary["contract_hash"] = _clean_text(stage3_meta.get("genre_strategy_contract_hash"))
    if not summary["source"]:
        summary["source"] = _clean_text(stage3_meta.get("genre_strategy_contract_source"))
    return {key: value for key, value in summary.items() if value != ""}


def render_stage4_genre_contract_packet(blueprint: dict[str, Any] | None) -> str:
    """Render Director-visible Stage4 contract transport context."""

    summary = extract_stage3_genre_contract_summary(blueprint)
    if not summary:
        return ""

    lines = [
        STAGE4_GENRE_CONTRACT_HEADER,
        f"- schema_version: {summary.get('schema_version')}",
        f"- coverage_outcome: {summary.get('coverage_outcome')}",
    ]
    for key in ("contract_id", "contract_hash", "authority_level", "strategy_name", "genre_type", "source"):
        value = summary.get(key)
        if value:
            lines.append(f"- {key}: {value}")
    lines.append("- role: Director-visible routing evidence only; prose quality remains Director authority.")
    return "\n".join(lines)
