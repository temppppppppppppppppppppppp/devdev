from __future__ import annotations

import os
from copy import deepcopy
from typing import Any

PROVIDER_MODE_ENV = "GEULDOBI_PROVIDER_MODE"
GEMINI_DIRECT_MODE = "gemini_direct"
VERTEX_AI_MODE = "vertex_ai"
AMBIENT_MODE = "ambient"

_MODE_ALIASES = {
    "": AMBIENT_MODE,
    "ambient": AMBIENT_MODE,
    "default": AMBIENT_MODE,
    "gemini": GEMINI_DIRECT_MODE,
    "gemini_direct": GEMINI_DIRECT_MODE,
    "google_direct": GEMINI_DIRECT_MODE,
    "direct": GEMINI_DIRECT_MODE,
    "vertex": VERTEX_AI_MODE,
    "vertex_ai": VERTEX_AI_MODE,
    "vertexai": VERTEX_AI_MODE,
    "google_vertex": VERTEX_AI_MODE,
}
_VERTEX_PREFIXES = ("vertexai:", "vertex:", "vertex/")


def normalize_provider_mode(value: str | None, *, default: str = AMBIENT_MODE) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return default
    return _MODE_ALIASES.get(normalized, default)


def get_env_provider_mode(*, default: str = AMBIENT_MODE) -> str:
    return normalize_provider_mode(os.getenv(PROVIDER_MODE_ENV), default=default)


def strip_vertex_prefix(model: str | None) -> str:
    normalized = str(model or "").strip()
    lowered = normalized.lower()
    for prefix in _VERTEX_PREFIXES:
        if lowered.startswith(prefix):
            return normalized[len(prefix) :]
    return normalized


def is_gemini_model(model: str | None) -> bool:
    return strip_vertex_prefix(model).lower().startswith("gemini")


def rewrite_google_model_for_mode(model: str | None, provider_mode: str | None) -> str:
    normalized = str(model or "").strip()
    if not normalized or not is_gemini_model(normalized):
        return normalized

    mode = normalize_provider_mode(provider_mode)
    base_model = strip_vertex_prefix(normalized)
    if mode == GEMINI_DIRECT_MODE:
        return base_model
    if mode == VERTEX_AI_MODE:
        return f"vertexai:{base_model}"
    return normalized


def _rewrite_mapping_values(mapping: dict[str, Any], provider_mode: str) -> dict[str, Any]:
    rewritten: dict[str, Any] = {}
    for key, value in mapping.items():
        if isinstance(value, str):
            rewritten[key] = rewrite_google_model_for_mode(value, provider_mode)
        elif isinstance(value, dict):
            rewritten[key] = _rewrite_mapping_values(value, provider_mode)
        else:
            rewritten[key] = value
    return rewritten


def _rewrite_fallback_chain(mapping: dict[str, Any], provider_mode: str) -> dict[str, Any]:
    rewritten: dict[str, Any] = {}
    for key, value in mapping.items():
        new_key = rewrite_google_model_for_mode(key, provider_mode) if isinstance(key, str) else key
        new_value = rewrite_google_model_for_mode(value, provider_mode) if isinstance(value, str) else value
        rewritten[new_key] = new_value
    return rewritten


def apply_provider_mode_to_models_payload(payload: dict[str, Any], provider_mode: str | None) -> dict[str, Any]:
    mode = normalize_provider_mode(provider_mode)
    result = deepcopy(payload or {})
    if mode == AMBIENT_MODE:
        return result

    providers = result.get("providers")
    if isinstance(providers, dict):
        gemini_cfg = providers.get("gemini")
        if isinstance(gemini_cfg, dict):
            gemini_cfg["enabled"] = True
        vertex_cfg = providers.get("vertex_ai")
        if isinstance(vertex_cfg, dict):
            vertex_cfg["enabled"] = mode == VERTEX_AI_MODE

    for section in ("agents", "role_constants"):
        entry = result.get(section)
        if isinstance(entry, dict):
            result[section] = _rewrite_mapping_values(entry, mode)

    sub_components = result.get("sub_components")
    if isinstance(sub_components, dict):
        result["sub_components"] = _rewrite_mapping_values(sub_components, mode)

    fallback_chain = result.get("fallback_chain")
    if isinstance(fallback_chain, dict):
        result["fallback_chain"] = _rewrite_fallback_chain(fallback_chain, mode)

    return result
