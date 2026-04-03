from __future__ import annotations

from modules.core.llm_provider import LLMProvider
from modules.core.models_config import load_models_yaml, resolve_models_yaml_path
from modules.core.provider_mode import (
    GEMINI_DIRECT_MODE,
    VERTEX_AI_MODE,
    get_env_provider_mode,
    is_gemini_model,
    rewrite_google_model_for_mode,
)
from modules.core.providers.anthropic_provider import AnthropicProvider
from modules.core.providers.anthropic_vertex_provider import AnthropicVertexProvider
from modules.core.providers.gemini_provider import GeminiProvider
from modules.core.providers.openai_provider import OpenAIProvider
from modules.core.providers.vertex_provider import VertexAIProvider

DEFAULT_PROVIDER_CONFIGS = {
    "gemini": {"enabled": True, "sdk": "google-genai", "api_key_env": "GOOGLE_API_KEY"},
    "anthropic": {"enabled": False, "sdk": "anthropic", "api_key_env": "ANTHROPIC_API_KEY"},
    "openai": {"enabled": False, "sdk": "openai", "api_key_env": "OPENAI_API_KEY"},
    "vertex_ai": {
        "enabled": False,
        "sdk": "google-genai",
        "auth_mode": "api_key",
        "api_key_env": "VERTEX_API_KEY",
        "project_id_env": "VERTEX_PROJECT_ID",
        "location_env": "VERTEX_LOCATION",
        "credentials_env": "GOOGLE_APPLICATION_CREDENTIALS",
    },
    "anthropic_vertex": {
        "enabled": False,
        "sdk": "anthropic",
        "project_id_env": "VERTEX_PROJECT_ID",
        "location_env": "VERTEX_LOCATION",
    },
}

# Multi-provider spine identity map: provider_name → (backend, family)
BACKEND_FAMILY_MAP: dict[str, tuple[str, str]] = {
    "gemini": ("google_direct", "gemini"),
    "vertex_ai": ("google_vertex", "gemini"),
    "anthropic": ("anthropic_direct", "claude"),
    "anthropic_vertex": ("anthropic_vertex", "claude"),
    "openai": ("openai_direct", "gpt"),
}


def _infer_provider_name_safe(model: str) -> str:
    """Infer provider name from model string prefix.

    Returns ``"unknown"`` for unrecognised prefixes instead of raising.
    This is the single implementation of the prefix-matching logic;
    :meth:`LLMProviderRouter.infer_provider_name` and
    :func:`resolve_provider_identity` both delegate here.
    """
    rewritten_model = rewrite_google_model_for_mode(model, get_env_provider_mode())
    normalized = (rewritten_model or model or "").strip().lower()
    mode = get_env_provider_mode()
    if mode == GEMINI_DIRECT_MODE and is_gemini_model(model):
        return "gemini"
    if mode == VERTEX_AI_MODE and is_gemini_model(model):
        return "vertex_ai"
    if normalized.startswith(("anthropic-vertex:", "anthropic_vertex:")):
        return "anthropic_vertex"
    if normalized.startswith(("vertexai:", "vertex:", "vertex/")):
        return "vertex_ai"
    if normalized.startswith("gemini"):
        return "gemini"
    if normalized.startswith("claude"):
        return "anthropic"
    if normalized.startswith(("gpt", "o1", "o3", "o4")):
        return "openai"
    return "unknown"


def resolve_provider_identity(model: str) -> tuple[str, str, str]:
    """Return ``(provider_name, backend, family)`` for a model string.

    Single source of truth for provider identity resolution across
    routing, metrics, and observability surfaces.  Falls back to
    ``("unknown", "unknown", "unknown")`` for unrecognised models.
    """
    provider_name = _infer_provider_name_safe(model)
    backend, family = BACKEND_FAMILY_MAP.get(provider_name, ("unknown", "unknown"))
    return (provider_name, backend, family)


def _resolve_models_config_path():
    return resolve_models_yaml_path()


def _load_provider_configs() -> dict[str, dict]:
    path = _resolve_models_config_path()
    configs = {name: values.copy() for name, values in DEFAULT_PROVIDER_CONFIGS.items()}
    try:
        provider_data = load_models_yaml(path=path).get("providers", {})
        if isinstance(provider_data, dict):
            for name, values in provider_data.items():
                if isinstance(name, str) and isinstance(values, dict):
                    merged = configs.get(name, {}).copy()
                    merged.update(values)
                    configs[name] = merged
    except OSError:
        pass
    return configs


def _build_provider(provider_name: str, config: dict) -> LLMProvider:
    if provider_name == "gemini":
        return GeminiProvider()
    if provider_name == "anthropic":
        return AnthropicProvider(api_key_env=config.get("api_key_env", "ANTHROPIC_API_KEY"))
    if provider_name == "openai":
        return OpenAIProvider(api_key_env=config.get("api_key_env", "OPENAI_API_KEY"))
    if provider_name == "vertex_ai":
        return VertexAIProvider(
            auth_mode=config.get("auth_mode", "api_key"),
            api_key_env=config.get("api_key_env", "VERTEX_API_KEY"),
            project_id_env=config.get("project_id_env", "VERTEX_PROJECT_ID"),
            location_env=config.get("location_env", "VERTEX_LOCATION"),
            credentials_env=config.get("credentials_env", "GOOGLE_APPLICATION_CREDENTIALS"),
        )
    if provider_name == "anthropic_vertex":
        return AnthropicVertexProvider(
            project_id_env=config.get("project_id_env", "VERTEX_PROJECT_ID"),
            location_env=config.get("location_env", "VERTEX_LOCATION"),
        )
    raise ValueError(f"Unsupported provider registration: {provider_name}")


class LLMProviderRouter:
    """Resolve provider by model naming convention.

    Phase 1 keeps Gemini as the only active provider. Other providers can be
    registered later without changing BaseAgent's public contract.
    """

    def __init__(
        self,
        providers: dict[str, LLMProvider] | None = None,
        provider_configs: dict[str, dict] | None = None,
    ) -> None:
        self._provider_configs = _load_provider_configs()
        if provider_configs:
            for name, values in provider_configs.items():
                merged = self._provider_configs.get(name, {}).copy()
                if isinstance(values, dict):
                    merged.update(values)
                self._provider_configs[name] = merged

        if providers is not None:
            self._providers = providers
            for name in providers:
                merged = self._provider_configs.get(name, {}).copy()
                merged["enabled"] = True
                self._provider_configs[name] = merged
        else:
            self._providers = {
                name: _build_provider(name, config)
                for name, config in self._provider_configs.items()
                if config.get("enabled")
            }

    @staticmethod
    def infer_provider_name(model: str) -> str:
        """Infer provider name from model string.

        Raises :class:`ValueError` for unrecognised models (routing must
        fail loudly).  Delegates to :func:`_infer_provider_name_safe`.
        """
        result = _infer_provider_name_safe(model)
        if result == "unknown":
            raise ValueError(f"Unsupported LLM model/provider mapping: {model!r}")
        return result

    def get_provider_for_model(self, model: str) -> LLMProvider:
        provider_name = self.infer_provider_name(model)
        provider_config = self._provider_configs.get(provider_name)
        if provider_config and not provider_config.get("enabled"):
            raise ValueError(f"Provider disabled in config/models.yaml: {provider_name}")

        provider = self._providers.get(provider_name)
        if provider is None:
            if provider_config:
                provider = _build_provider(provider_name, provider_config)
                self._providers[provider_name] = provider
            else:
                raise ValueError(f"Provider not registered for model {model!r}: {provider_name}")
        return provider

    def get_enabled_provider_names(self) -> tuple[str, ...]:
        return tuple(sorted(name for name, config in self._provider_configs.items() if config.get("enabled")))


_SHARED_ROUTER: LLMProviderRouter | None = None


def get_shared_llm_router(*, force_reload: bool = False) -> LLMProviderRouter:
    global _SHARED_ROUTER
    if force_reload or _SHARED_ROUTER is None:
        _SHARED_ROUTER = LLMProviderRouter()
    return _SHARED_ROUTER
