from __future__ import annotations

import os
from pathlib import Path

import yaml

from modules.core.provider_mode import (
    apply_provider_mode_to_models_payload,
    get_env_provider_mode,
    is_gemini_model,
    rewrite_google_model_for_mode,
)

# Runtime fallback SSOT.
# `config/models.yaml` is authoritative when present, and these defaults are the
# only inline mirrors code should rely on when the YAML is absent or incomplete.
DEFAULT_PRO_MODEL = "gemini-3.1-pro-preview"
DEFAULT_PRO_FALLBACK_MODEL = "gemini-2.5-pro"
DEFAULT_FLASH_MODEL = "gemini-2.5-flash"

DEFAULT_AGENT_MODELS = {
    "analyst": DEFAULT_PRO_MODEL,
    "manager": DEFAULT_FLASH_MODEL,
    "chief_writer": DEFAULT_PRO_MODEL,
    "blueprint_ensemble": DEFAULT_PRO_MODEL,
    "three_phase_blueprint_generator": DEFAULT_PRO_MODEL,
    "state_locked_arc_generator": DEFAULT_PRO_MODEL,
    "block_enricher": DEFAULT_FLASH_MODEL,
    "preflight_checker": DEFAULT_FLASH_MODEL,
    "state_extractor": DEFAULT_FLASH_MODEL,
    "four_phase_arc_generator": DEFAULT_PRO_MODEL,
    "continuity_inspector": DEFAULT_PRO_MODEL,
    "director": DEFAULT_PRO_MODEL,
    "arc_corrector": DEFAULT_FLASH_MODEL,
    "arc_critic": DEFAULT_FLASH_MODEL,
    "consensus_validator": DEFAULT_FLASH_MODEL,
    "unified_arc_validator": DEFAULT_FLASH_MODEL,
    "unified_blueprint_validator": DEFAULT_FLASH_MODEL,
    "critic": DEFAULT_FLASH_MODEL,
    "weaver": DEFAULT_FLASH_MODEL,
    "writer": DEFAULT_FLASH_MODEL,
}

DEFAULT_MODEL_FALLBACK_CHAIN = {
    DEFAULT_PRO_MODEL: DEFAULT_PRO_FALLBACK_MODEL,
    DEFAULT_PRO_FALLBACK_MODEL: DEFAULT_FLASH_MODEL,
    DEFAULT_FLASH_MODEL: DEFAULT_FLASH_MODEL,
}

FORCE_GOOGLE_MODEL_ENV = "GEULDOBI_FORCE_GOOGLE_MODEL"


def _force_google_mapping_values(mapping: dict, forced_model: str) -> dict:
    rewritten = {}
    for key, value in mapping.items():
        if isinstance(value, str):
            rewritten[key] = forced_model if is_gemini_model(value) else value
        elif isinstance(value, dict):
            rewritten[key] = _force_google_mapping_values(value, forced_model)
        else:
            rewritten[key] = value
    return rewritten


def _force_google_fallback_chain(mapping: dict, forced_model: str) -> dict:
    rewritten = {}
    for key, value in mapping.items():
        new_key = forced_model if isinstance(key, str) and is_gemini_model(key) else key
        new_value = forced_model if isinstance(value, str) and is_gemini_model(value) else value
        rewritten[new_key] = new_value
    rewritten[forced_model] = forced_model
    return rewritten


def apply_forced_google_model_to_models_payload(
    payload: dict,
    *,
    forced_model: str | None,
    provider_mode: str | None,
) -> dict:
    """Optionally pin every Gemini/Vertex-Gemini runtime role to one model.

    This is a run-scope escape hatch for high-rigor validation runs where silent
    fallback to a lower model tier would invalidate the evidence.
    """

    normalized = str(forced_model or "").strip()
    if not normalized or not is_gemini_model(normalized):
        return payload

    forced = rewrite_google_model_for_mode(normalized, provider_mode)
    result = dict(payload or {})

    for section in ("agents", "role_constants"):
        entry = result.get(section)
        if isinstance(entry, dict):
            result[section] = _force_google_mapping_values(entry, forced)

    sub_components = result.get("sub_components")
    if isinstance(sub_components, dict):
        result["sub_components"] = _force_google_mapping_values(sub_components, forced)

    fallback_chain = result.get("fallback_chain")
    if isinstance(fallback_chain, dict):
        result["fallback_chain"] = _force_google_fallback_chain(fallback_chain, forced)

    return result


def resolve_models_yaml_path() -> Path:
    """Return the authoritative `config/models.yaml` path.

    In packaged mode (PyInstaller) ``GEULDOBI_ENGINE_ROOT`` is set by
    ``backend_entry.py`` to ``resources/engine/``.  Dev mode falls back to the
    repo-root sibling path derived from ``__file__``.
    """
    engine_root = os.environ.get("GEULDOBI_ENGINE_ROOT")
    if engine_root:
        return Path(engine_root).resolve() / "config" / "models.yaml"
    return Path(__file__).resolve().parents[2] / "config" / "models.yaml"


def load_models_yaml(*, path: Path | None = None, apply_provider_mode: bool = True) -> dict:
    """Load the canonical repo-root models config."""

    config_path = path or resolve_models_yaml_path()
    try:
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if isinstance(data, dict):
                if apply_provider_mode:
                    provider_mode = get_env_provider_mode()
                    payload = apply_provider_mode_to_models_payload(data, provider_mode)
                    return apply_forced_google_model_to_models_payload(
                        payload,
                        forced_model=os.getenv(FORCE_GOOGLE_MODEL_ENV),
                        provider_mode=provider_mode,
                    )
                return data
    except (OSError, yaml.YAMLError):
        pass
    return {}


def load_model_contract(*, section: str, key: str, fallback: str) -> dict:
    """Return the effective model plus source provenance for one config key."""

    config_path = resolve_models_yaml_path()
    data = load_models_yaml(path=config_path)
    value = data.get(section, {}).get(key)
    relative_path = config_path.as_posix()
    try:
        relative_path = config_path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        pass

    contract = {
        "section": str(section or "").strip(),
        "key": str(key or "").strip(),
        "authoritative_source": f"{relative_path}:{section}.{key}",
        "fallback_source": "inline_default",
        "effective_source": "inline_default",
        "effective_value": fallback,
        "used_fallback": True,
    }
    if isinstance(value, str) and value.strip():
        contract["effective_source"] = contract["authoritative_source"]
        contract["effective_value"] = value.strip()
        contract["used_fallback"] = False
    return contract


def load_model_name(*, section: str, key: str, fallback: str) -> str:
    """Return one model name from the canonical models config."""

    return str(load_model_contract(section=section, key=key, fallback=fallback)["effective_value"] or fallback)
