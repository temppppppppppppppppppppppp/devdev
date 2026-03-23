from __future__ import annotations

from pathlib import Path

import yaml


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


def resolve_models_yaml_path() -> Path:
    """Return the repo-root `config/models.yaml` path."""

    return Path(__file__).resolve().parents[2] / "config" / "models.yaml"


def load_models_yaml(*, path: Path | None = None) -> dict:
    """Load the canonical repo-root models config."""

    config_path = path or resolve_models_yaml_path()
    try:
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if isinstance(data, dict):
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
