from __future__ import annotations

import os
from typing import Any

from google import genai

from modules.core.llm_provider import LLMRequest, LLMResponse


class VertexAIProvider:
    provider_name = "vertex_ai"
    _MODEL_PREFIXES = ("vertexai:", "vertex:", "vertex/")

    def __init__(
        self,
        *,
        project_id_env: str = "VERTEX_PROJECT_ID",
        location_env: str = "VERTEX_LOCATION",
        credentials_env: str = "GOOGLE_APPLICATION_CREDENTIALS",
    ) -> None:
        self.project_id_env = project_id_env
        self.location_env = location_env
        self.credentials_env = credentials_env
        self._client = None

    @classmethod
    def normalize_model_name(cls, model: str) -> str:
        normalized = (model or "").strip()
        lowered = normalized.lower()
        for prefix in cls._MODEL_PREFIXES:
            if lowered.startswith(prefix):
                return normalized[len(prefix) :]
        return normalized

    def _load_credentials(self):
        credentials_path = os.getenv(self.credentials_env)
        if not credentials_path:
            return None

        try:
            from google.auth import load_credentials_from_file
        except ImportError as exc:
            raise RuntimeError(
                "google-auth is required to load Vertex AI credentials files."
            ) from exc

        credentials, _ = load_credentials_from_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return credentials

    def _get_client(self):
        if self._client is not None:
            return self._client

        project = os.getenv(self.project_id_env) or os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv(self.location_env) or os.getenv("GOOGLE_CLOUD_LOCATION")
        if not project or not location:
            raise RuntimeError(
                f"Vertex AI requires {self.project_id_env}/{self.location_env} "
                "or GOOGLE_CLOUD_PROJECT/GOOGLE_CLOUD_LOCATION."
            )

        client_kwargs: dict[str, Any] = {
            "vertexai": True,
            "project": project,
            "location": location,
        }

        credentials = self._load_credentials()
        if credentials is not None:
            client_kwargs["credentials"] = credentials

        self._client = genai.Client(**client_kwargs)
        return self._client

    def generate(self, *, client: Any, request: LLMRequest) -> LLMResponse:
        resolved_client = self._get_client()
        raw = resolved_client.models.generate_content(
            model=self.normalize_model_name(request.model),
            contents=request.contents,
            config=request.config,
        )

        text = ""
        try:
            text = raw.text or ""
        except (AttributeError, ValueError):
            text = ""

        finish_reason = "stop"
        try:
            candidates = getattr(raw, "candidates", None) or []
            if candidates:
                finish_reason = str(getattr(candidates[0], "finish_reason", "stop") or "stop")
        except Exception:
            finish_reason = "stop"

        usage = None
        usage_meta = getattr(raw, "usage_metadata", None)
        if usage_meta is not None:
            usage = {
                "prompt_token_count": getattr(usage_meta, "prompt_token_count", None),
                "candidates_token_count": getattr(usage_meta, "candidates_token_count", None),
                "total_token_count": getattr(usage_meta, "total_token_count", None),
            }

        return LLMResponse(
            text=text,
            finish_reason=finish_reason,
            usage=usage,
            raw=raw,
            provider=self.provider_name,
        )
