"""Authority labels for Stage4 advisory payload surfaces.

The payload content can stay stable while consumers inherit authority from the
explicit top-level map. This avoids treating unlabeled advisory data as a
blocking route/verdict source by accident.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

ADVISORY_AUTHORITY_SCHEMA_VERSION = "advisory-authority-levels-v1"
ADVISORY_AUTHORITY_SCHEMA_KEY = "advisory_authority_schema_version"
ADVISORY_AUTHORITY_LEVELS_KEY = "advisory_authority_levels"
ADVISORY_AUTHORITY_SOURCES_KEY = "advisory_authority_sources"

AUTHORITY_LEVEL_ADVISORY = "advisory"
AUTHORITY_LEVEL_ROUTE = "route"
AUTHORITY_LEVEL_VERDICT = "verdict"
AUTHORITY_LEVEL_HISTORICAL_COMPANION = "historical_companion"

ROUTE_AUTHORITY_PAYLOAD_KEYS = (
    "fix_pack",
    "repair_contract",
    "scope_authority",
    "retry_budget_axes",
)

_VALID_AUTHORITY_LEVELS = {
    AUTHORITY_LEVEL_ADVISORY,
    AUTHORITY_LEVEL_ROUTE,
    AUTHORITY_LEVEL_VERDICT,
    AUTHORITY_LEVEL_HISTORICAL_COMPANION,
}
_AUTHORITY_LEVEL_RANK = {
    AUTHORITY_LEVEL_ADVISORY: 0,
    AUTHORITY_LEVEL_HISTORICAL_COMPANION: 1,
    AUTHORITY_LEVEL_ROUTE: 2,
    AUTHORITY_LEVEL_VERDICT: 3,
}


def _as_dict(value: Any) -> dict[str, Any]:
    return copy.deepcopy(dict(value)) if isinstance(value, Mapping) else {}


def normalize_authority_level(value: object, *, default: str = AUTHORITY_LEVEL_ADVISORY) -> str:
    level = str(value or "").strip().lower()
    if level in _VALID_AUTHORITY_LEVELS:
        return level
    return default


def _payload_exists(value: object) -> bool:
    return isinstance(value, Mapping) and bool(value)


def _record_level(
    levels: dict[str, str],
    sources: dict[str, str],
    *,
    key: str,
    source: str,
    level: str = AUTHORITY_LEVEL_ROUTE,
) -> None:
    normalized_key = str(key or "").strip()
    if not normalized_key:
        return
    normalized_level = normalize_authority_level(level, default=AUTHORITY_LEVEL_ROUTE)
    existing_level = normalize_authority_level(levels.get(normalized_key), default=normalized_level)
    if _AUTHORITY_LEVEL_RANK.get(normalized_level, 0) >= _AUTHORITY_LEVEL_RANK.get(existing_level, 0):
        levels[normalized_key] = normalized_level
        sources[normalized_key] = str(source or "").strip() or "stage4_runtime"
    else:
        levels[normalized_key] = existing_level
        sources.setdefault(normalized_key, str(source or "").strip() or "stage4_runtime")


def ensure_stage4_route_authority(
    advisory_flags: Mapping[str, Any] | None,
    *,
    route_payloads: Mapping[str, Any] | None = None,
    source: str = "stage4_attempt",
) -> dict[str, Any]:
    """Return advisory flags with explicit route-authority inheritance labels.

    The route payload dictionaries are intentionally not mutated. Consumers can
    resolve authority through the map, so legacy equality checks and payload
    shape contracts remain stable while the authority layer becomes explicit.
    """

    advisory = _as_dict(advisory_flags)
    if not advisory and not isinstance(route_payloads, Mapping):
        return {}

    existing_levels = _as_dict(advisory.get(ADVISORY_AUTHORITY_LEVELS_KEY))
    levels = {
        str(key): normalize_authority_level(value, default=AUTHORITY_LEVEL_ADVISORY)
        for key, value in existing_levels.items()
        if str(key or "").strip()
    }
    existing_sources = _as_dict(advisory.get(ADVISORY_AUTHORITY_SOURCES_KEY))
    sources = {
        str(key): str(value or "").strip()
        for key, value in existing_sources.items()
        if str(key or "").strip() and str(value or "").strip()
    }

    gate_semantics = advisory.get("gate_semantics")
    gate_payload = _as_dict(gate_semantics) if isinstance(gate_semantics, Mapping) else {}
    for key in ROUTE_AUTHORITY_PAYLOAD_KEYS:
        if _payload_exists(advisory.get(key)):
            _record_level(levels, sources, key=key, source=source)
        nested_key = f"gate_semantics.{key}"
        if _payload_exists(gate_payload.get(key)):
            _record_level(levels, sources, key=nested_key, source=source)

    if isinstance(route_payloads, Mapping):
        for key, payload in route_payloads.items():
            if str(key or "").strip() in ROUTE_AUTHORITY_PAYLOAD_KEYS and _payload_exists(payload):
                _record_level(levels, sources, key=str(key), source=source)

    if levels:
        advisory[ADVISORY_AUTHORITY_SCHEMA_KEY] = ADVISORY_AUTHORITY_SCHEMA_VERSION
        advisory[ADVISORY_AUTHORITY_LEVELS_KEY] = levels
        advisory[ADVISORY_AUTHORITY_SOURCES_KEY] = sources
    return advisory


def ensure_stage4_historical_companion_authority(
    advisory_flags: Mapping[str, Any] | None,
    *,
    source: str = "director_selection",
) -> dict[str, Any]:
    """Label director-selection advisory payloads as historical companions.

    Existing stronger labels are preserved, so an explicit typed promotion can
    still opt a payload into route/verdict authority.
    """

    advisory = _as_dict(advisory_flags)
    if not advisory:
        return {}

    existing_levels = _as_dict(advisory.get(ADVISORY_AUTHORITY_LEVELS_KEY))
    levels = {
        str(key): normalize_authority_level(value, default=AUTHORITY_LEVEL_ADVISORY)
        for key, value in existing_levels.items()
        if str(key or "").strip()
    }
    existing_sources = _as_dict(advisory.get(ADVISORY_AUTHORITY_SOURCES_KEY))
    sources = {
        str(key): str(value or "").strip()
        for key, value in existing_sources.items()
        if str(key or "").strip() and str(value or "").strip()
    }

    gate_payload = _as_dict(advisory.get("gate_semantics"))
    for key in ROUTE_AUTHORITY_PAYLOAD_KEYS:
        if _payload_exists(advisory.get(key)):
            _record_level(
                levels,
                sources,
                key=key,
                source=source,
                level=AUTHORITY_LEVEL_HISTORICAL_COMPANION,
            )
        nested_key = f"gate_semantics.{key}"
        if _payload_exists(gate_payload.get(key)):
            _record_level(
                levels,
                sources,
                key=nested_key,
                source=source,
                level=AUTHORITY_LEVEL_HISTORICAL_COMPANION,
            )

    if levels:
        advisory[ADVISORY_AUTHORITY_SCHEMA_KEY] = ADVISORY_AUTHORITY_SCHEMA_VERSION
        advisory[ADVISORY_AUTHORITY_LEVELS_KEY] = levels
        advisory[ADVISORY_AUTHORITY_SOURCES_KEY] = sources
    return advisory


def resolve_advisory_authority_level(
    advisory_flags: Mapping[str, Any] | None,
    key: str,
    *,
    default: str = "",
) -> str:
    advisory = _as_dict(advisory_flags)
    levels = _as_dict(advisory.get(ADVISORY_AUTHORITY_LEVELS_KEY))
    normalized_key = str(key or "").strip()
    if not normalized_key:
        return default
    for candidate in (normalized_key, f"gate_semantics.{normalized_key}"):
        if candidate in levels:
            return normalize_authority_level(levels.get(candidate), default=AUTHORITY_LEVEL_ADVISORY)
    return default


def build_retry_surface_authority_levels(
    advisory_flags: Mapping[str, Any] | None,
    *,
    route_payloads: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    advisory = ensure_stage4_route_authority(
        advisory_flags,
        route_payloads=route_payloads,
        source="session_memory_retry_surface",
    )
    return {
        key: level for key in ROUTE_AUTHORITY_PAYLOAD_KEYS if (level := resolve_advisory_authority_level(advisory, key))
    }
