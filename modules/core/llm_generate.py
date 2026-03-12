from __future__ import annotations

from typing import Any

from modules.core.llm_provider import LLMRequest
from modules.core.llm_router import get_shared_llm_router


def generate_content_via_router(*, client: Any, model: str, contents: Any, config: Any | None = None) -> Any:
    """Provider-routed generate helper that preserves native response objects.

    Phase 2 migrates direct Gemini call sites onto this helper so downstream
    parsing can stay unchanged while provider selection moves behind the router.
    """

    provider = get_shared_llm_router().get_provider_for_model(model)
    response = provider.generate(
        client=client,
        request=LLMRequest(model=model, contents=contents, config=config),
    )
    return response.raw
