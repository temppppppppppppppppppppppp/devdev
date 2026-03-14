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


def load_model_name(*, section: str, key: str, fallback: str) -> str:
    """Return one model name from the canonical models config."""

    value = load_models_yaml().get(section, {}).get(key)
    if isinstance(value, str) and value.strip():
        return value
    return fallback
