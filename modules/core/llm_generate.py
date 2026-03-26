from __future__ import annotations

from typing import Any

from modules.core.llm_provider import LLMRequest, LLMResponse
from modules.core.llm_router import BACKEND_FAMILY_MAP, get_shared_llm_router


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
    response = provider.generate(
        client=client,
        request=LLMRequest(model=model, contents=contents, config=config),
    )
    backend, family = BACKEND_FAMILY_MAP.get(
        getattr(provider, "provider_name", ""), ("unknown", "unknown")
    )
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
