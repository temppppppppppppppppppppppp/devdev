from __future__ import annotations

from typing import Any

from google.genai import types

from modules.core.llm_provider import LLMRequest, LLMResponse
from modules.core.llm_router import BACKEND_FAMILY_MAP, get_shared_llm_router

_GOOGLE_PROVIDER_NAMES = {"gemini", "vertex_ai"}
_DEFAULT_GOOGLE_TIMEOUT_SECONDS = 300


def _default_google_timeout_ms() -> int:
    return max(10_000, _DEFAULT_GOOGLE_TIMEOUT_SECONDS * 1000)


def _with_google_timeout(provider_name: str, config: Any | None) -> Any:
    """Give helper-layer Google calls the same hang guard as BaseAgent.ask()."""

    if provider_name not in _GOOGLE_PROVIDER_NAMES:
        return config

    timeout_ms = _default_google_timeout_ms()
    if config is None:
        return types.GenerateContentConfig(http_options=types.HttpOptions(timeout=timeout_ms))

    if isinstance(config, dict):
        updated = dict(config)
        http_options = updated.get("http_options")
        if isinstance(http_options, dict):
            http_options = dict(http_options)
            http_options.setdefault("timeout", timeout_ms)
            updated["http_options"] = http_options
        elif not http_options:
            updated["http_options"] = types.HttpOptions(timeout=timeout_ms)
        elif not getattr(http_options, "timeout", None):
            try:
                http_options.timeout = timeout_ms
            except Exception:
                updated["http_options"] = types.HttpOptions(timeout=timeout_ms)
        return updated

    http_options = getattr(config, "http_options", None)
    if http_options and getattr(http_options, "timeout", None):
        return config

    try:
        config.http_options = types.HttpOptions(timeout=timeout_ms)
        return config
    except Exception:
        pass

    if hasattr(config, "model_dump"):
        try:
            params = config.model_dump(exclude_none=True)
            params["http_options"] = types.HttpOptions(timeout=timeout_ms)
            return types.GenerateContentConfig(**params)
        except Exception:
            return config
    return config


def generate_llm_response_via_router(
    *,
    client: Any,
    model: str,
    contents: Any,
    config: Any | None = None,
) -> LLMResponse:
    """Provider-routed helper with a normalized response envelope."""

    router = get_shared_llm_router()
    provider = router.get_provider_for_model(model)
    config = _with_google_timeout(getattr(provider, "provider_name", ""), config)
    response = provider.generate(
        client=client,
        request=LLMRequest(model=model, contents=contents, config=config),
    )
    # [COMPAT-BELT] Per-adapter generate() already sets response.backend
    # and response.family. This overwrite is a safety belt ensuring consistency
    # with BACKEND_FAMILY_MAP. Adapters are the authoritative source; if
    # adapter values and map values ever diverge, investigate the adapter.
    backend, family = BACKEND_FAMILY_MAP.get(getattr(provider, "provider_name", ""), ("unknown", "unknown"))
    response.backend = backend
    response.family = family
    return response


def generate_content_via_router(*, client: Any, model: str, contents: Any, config: Any | None = None) -> LLMResponse:
    """Return normalized `LLMResponse` for helper-layer callers.

    Direct callers should read `.text`, `.finish_reason`, and `.usage`.
    Provider-native shape stays available on `.raw` for diagnostics and staged
    compatibility.
    """

    return generate_llm_response_via_router(client=client, model=model, contents=contents, config=config)


def generate_raw_content_via_router(*, client: Any, model: str, contents: Any, config: Any | None = None) -> Any:
    """Compatibility seam for callers that still need provider-native `raw`."""

    return generate_llm_response_via_router(client=client, model=model, contents=contents, config=config).raw
