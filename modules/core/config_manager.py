import json
import logging
import threading
from pathlib import Path
from typing import Any

import yaml

from modules.core.models_config import DEFAULT_AGENT_MODELS, load_model_contract


class ConfigManager:
    """Central config loader with authority and fallback provenance."""

    _SETTINGS_DIR = "config/settings"
    _VALIDATION_YAML = "validation.yaml"
    _SETTINGS_JSON = "settings.json"
    _settings_lock = threading.Lock()

    def __init__(self) -> None:
        self.root = Path.cwd()

        target_manuscript_length = 5000

        self.projects_dir = self.root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        self.logs_dir = self.root / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        logging.info(" [System] required paths ready: %s", self.logs_dir)

        models_from_yaml = self._load_agents_from_yaml()
        self._default_models = dict(DEFAULT_AGENT_MODELS)
        self._yaml_models = dict(models_from_yaml or {})

        self.settings = {
            "models": dict(self._yaml_models) if self._yaml_models else dict(self._default_models),
            "limits": {
                "max_retries": 10,
                "target_manuscript_length": target_manuscript_length,
            },
        }

        self._validation_settings: dict | None = None
        self._settings_json_cache: dict | None = None

    def get_v20_project_paths(self, project_name: str) -> dict:
        base = self.projects_dir / project_name
        return {
            "root": base,
            "config": base / "config",
            "db": base / "db",
            "drafts": base / "drafts",
            "logs": base / "logs",
            "blueprints": base / "blueprints",
            "memory": base / "memory",
        }

    def _validation_yaml_path(self) -> Path:
        return self.root / self._SETTINGS_DIR / self._VALIDATION_YAML

    def _settings_json_path(self) -> Path:
        return self.root / "config" / self._SETTINGS_JSON

    def _load_agents_from_yaml(self) -> dict | None:
        try:
            yaml_path = Path(__file__).parent.parent.parent / "config" / "models.yaml"
            if yaml_path.exists():
                data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
                agents = (data or {}).get("agents")
                if isinstance(agents, dict) and agents:
                    return dict(agents)
        except Exception as exc:
            logging.warning("[ConfigManager] models.yaml load failed: %s", exc)
        return None

    def _relative_source(self, path: Path, *, suffix: str = "") -> str:
        try:
            normalized = path.relative_to(self.root).as_posix()
        except ValueError:
            normalized = path.as_posix()
        return f"{normalized}{suffix}" if suffix else normalized

    @staticmethod
    def _get_nested_from(payload: dict, dotted_key: str, default: Any = None) -> Any:
        parts = str(dotted_key or "").split(".")
        current: Any = payload
        for part in parts:
            if not isinstance(current, dict):
                return default
            current = current.get(part)
            if current is None:
                return default
        return current

    @staticmethod
    def _coerce_to_default_type(value: Any, default: Any) -> tuple[Any, bool]:
        if default is None:
            return value, True
        if isinstance(default, bool):
            return (value, True) if isinstance(value, bool) else (default, False)
        if isinstance(default, (int, float)) and not isinstance(default, bool):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return type(default)(value), True
            return default, False
        if isinstance(value, type(default)):
            return value, True
        return default, False

    def load_settings(self, *, force_reload: bool = False) -> dict:
        if self._validation_settings is not None and not force_reload:
            return self._validation_settings

        with self._settings_lock:
            if self._validation_settings is not None and not force_reload:
                return self._validation_settings

            yaml_path = self._validation_yaml_path()
            if not yaml_path.exists():
                logging.warning("[ConfigManager] validation.yaml missing: %s", yaml_path)
                self._validation_settings = {}
                return self._validation_settings

            try:
                with open(yaml_path, encoding="utf-8") as handle:
                    payload = yaml.safe_load(handle)
                self._validation_settings = payload if isinstance(payload, dict) else {}
            except Exception as exc:
                logging.warning("[ConfigManager] validation.yaml parse failed: %s", exc)
                self._validation_settings = {}

            return self._validation_settings

    def load_settings_json(self, *, force_reload: bool = False) -> dict:
        if self._settings_json_cache is not None and not force_reload:
            return self._settings_json_cache

        with self._settings_lock:
            if self._settings_json_cache is not None and not force_reload:
                return self._settings_json_cache

            json_path = self._settings_json_path()
            if not json_path.exists():
                self._settings_json_cache = {}
                return self._settings_json_cache

            try:
                with open(json_path, encoding="utf-8") as handle:
                    payload = json.load(handle)
                self._settings_json_cache = payload if isinstance(payload, dict) else {}
            except Exception as exc:
                logging.warning("[ConfigManager] settings.json parse failed: %s", exc)
                self._settings_json_cache = {}

            return self._settings_json_cache

    def _get_nested(self, dotted_key: str, default: Any = None) -> Any:
        return self._get_nested_from(self.load_settings(), dotted_key, default)

    def _compat_validation_value(self, key: str) -> tuple[Any, str]:
        settings_json = self.load_settings_json()
        validation_block = settings_json.get("validation") if isinstance(settings_json, dict) else {}
        if not isinstance(validation_block, dict):
            return None, ""

        compat_key = ""
        if str(key).startswith("orchestrator."):
            compat_key = str(key).split(".", 1)[1]
        elif str(key).startswith("validation."):
            compat_key = str(key).split(".", 1)[1]
        if not compat_key or compat_key not in validation_block:
            return None, ""

        source = self._relative_source(self._settings_json_path(), suffix=f":validation.{compat_key}")
        return validation_block.get(compat_key), source

    def get_guard_threshold_contract(self, key: str, default: Any = None) -> dict:
        authoritative_source = self._relative_source(self._validation_yaml_path(), suffix=f":{key}")
        compatibility_value, compatibility_source = self._compat_validation_value(key)
        contract = {
            "key": str(key or "").strip(),
            "authoritative_source": authoritative_source,
            "compatibility_source": compatibility_source,
            "fallback_source": "caller_default",
            "effective_source": "caller_default",
            "effective_value": default,
            "used_fallback": True,
            "used_compatibility": False,
        }

        value = self._get_nested(key)
        if value is not None:
            coerced, valid = self._coerce_to_default_type(value, default)
            if valid:
                contract["effective_source"] = authoritative_source
                contract["effective_value"] = coerced
                contract["used_fallback"] = False
            else:
                contract["type_mismatch_source"] = authoritative_source
            return contract

        if compatibility_source:
            coerced, valid = self._coerce_to_default_type(compatibility_value, default)
            if valid:
                contract["effective_source"] = compatibility_source
                contract["effective_value"] = coerced
                contract["used_fallback"] = False
                contract["used_compatibility"] = True
            else:
                contract["type_mismatch_source"] = compatibility_source
        return contract

    def get_guard_threshold(self, key: str, default: Any = None) -> Any:
        return self.get_guard_threshold_contract(key, default).get("effective_value")

    def get_validation_policy(self, key: str, default: Any = None) -> Any:
        return self.get_guard_threshold(key, default)

    def get_feature_flag(self, key: str, default: bool = False) -> bool:
        contract = self.get_guard_threshold_contract(f"feature_flags.{key}", default)
        value = contract.get("effective_value")
        return value if isinstance(value, bool) else default

    def get_model_for_agent_contract(self, agent_role: str, fallback: str | None = None) -> dict:
        resolved_fallback = str(fallback or self._default_models.get(agent_role, "gemini-2.5-flash"))
        contract = load_model_contract(section="agents", key=agent_role, fallback=resolved_fallback)
        if contract.get("used_fallback"):
            contract["fallback_source"] = (
                "config_manager.defaults.models"
                if agent_role in self._default_models and resolved_fallback == self._default_models[agent_role]
                else "caller_default"
            )
            contract["effective_source"] = contract["fallback_source"]
        return contract

    def get_model_for_agent(self, agent_role: str) -> str:
        contract = self.get_model_for_agent_contract(agent_role)
        return str(contract.get("effective_value") or "gemini-2.5-flash")

    def __getitem__(self, key: str) -> dict:
        return self.settings[key]

    def invalidate_settings_cache(self) -> None:
        self._validation_settings = None
        self._settings_json_cache = None

    def build_config_authority_summary(self) -> dict:
        threshold_defaults = {
            "scoring.default_pass_threshold": 60,
            "context.mandatory_context_max": 400000,
            "smart_retrieval.stage4_total_budget": 300000,
            "patch_mode.inplace_below": 60,
            "orchestrator.use_self_consistency": True,
        }
        thresholds = {
            key: self.get_guard_threshold_contract(key, default)
            for key, default in threshold_defaults.items()
        }
        models = {
            role: self.get_model_for_agent_contract(role)
            for role in ("director", "chief_writer", "analyst")
        }
        return {
            "available": True,
            "settings_json_available": bool(self.load_settings_json()),
            "thresholds": thresholds,
            "models": models,
        }
