from __future__ import annotations

from pathlib import Path

import yaml


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
