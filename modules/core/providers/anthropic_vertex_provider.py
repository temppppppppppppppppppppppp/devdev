from __future__ import annotations

import os
from typing import Any

from modules.core.llm_provider import LLMRequest, LLMResponse
from modules.core.providers.anthropic_provider import AnthropicProvider


class AnthropicVertexProvider(AnthropicProvider):
    """Claude on Vertex AI — reuses AnthropicProvider request/response logic."""

    provider_name = "anthropic_vertex"
    _backend = "anthropic_vertex"
    _family = "claude"
    _MODEL_PREFIXES = ("anthropic-vertex:", "anthropic_vertex:")

    def __init__(
        self,
        *,
        project_id_env: str = "VERTEX_PROJECT_ID",
        location_env: str = "VERTEX_LOCATION",
    ) -> None:
        super().__init__()
        self.project_id_env = project_id_env
        self.location_env = location_env

    @classmethod
    def normalize_model_name(cls, model: str) -> str:
        normalized = (model or "").strip()
        lowered = normalized.lower()
        for prefix in cls._MODEL_PREFIXES:
            if lowered.startswith(prefix):
                return normalized[len(prefix) :]
        return normalized

    def _get_client(self):
        if self._client is not None:
            return self._client

        project_id = os.getenv(self.project_id_env) or os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv(self.location_env) or os.getenv("GOOGLE_CLOUD_LOCATION") or "us-east5"

        if not project_id:
            raise RuntimeError(
                f"{self.project_id_env} (or GOOGLE_CLOUD_PROJECT) is required "
                f"to activate AnthropicVertexProvider"
            )

        try:
            from anthropic import AnthropicVertex
        except ImportError as exc:
            raise RuntimeError(
                "anthropic package is not installed. "
                "Install `anthropic[vertex]` to enable Claude on Vertex AI."
            ) from exc

        self._client = AnthropicVertex(project_id=project_id, region=location)
        return self._client

    def generate(self, *, client: Any, request: LLMRequest) -> LLMResponse:
        normalized_request = LLMRequest(
            model=self.normalize_model_name(request.model),
            contents=request.contents,
            config=request.config,
        )
        return super().generate(client=client, request=normalized_request)
