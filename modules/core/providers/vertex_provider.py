from __future__ import annotations

import os
from typing import Any

from google import genai

from modules.core.llm_provider import LLMRequest, LLMResponse


class VertexAIProvider:
    provider_name = "vertex_ai"
    _MODEL_PREFIXES = ("vertexai:", "vertex:", "vertex/")
    _AUTH_MODES = {"api_key", "project_credentials", "auto"}

    def __init__(
        self,
        *,
        api_key_env: str = "VERTEX_API_KEY",
        project_id_env: str = "VERTEX_PROJECT_ID",
        location_env: str = "VERTEX_LOCATION",
        credentials_env: str = "GOOGLE_APPLICATION_CREDENTIALS",
        auth_mode: str = "api_key",
    ) -> None:
        normalized_auth_mode = (auth_mode or "api_key").strip().lower()
        if normalized_auth_mode not in self._AUTH_MODES:
            raise ValueError(
                f"Unsupported Vertex AI auth_mode {auth_mode!r}; "
                f"expected one of {sorted(self._AUTH_MODES)}."
            )
        self.api_key_env = api_key_env
        self.project_id_env = project_id_env
        self.location_env = location_env
        self.credentials_env = credentials_env
        self.auth_mode = normalized_auth_mode
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

    def _resolve_auth_mode(self) -> str:
        if self.auth_mode != "auto":
            return self.auth_mode
        if os.getenv(self.api_key_env):
            return "api_key"
        return "project_credentials"

    def _build_api_key_client(self):
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Vertex AI auth_mode=api_key requires {self.api_key_env}."
            )
        return genai.Client(vertexai=True, api_key=api_key)

    def _build_project_credentials_client(self):
        project = os.getenv(self.project_id_env) or os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv(self.location_env) or os.getenv("GOOGLE_CLOUD_LOCATION")
        if not project or not location:
            raise RuntimeError(
                f"Vertex AI auth_mode=project_credentials requires "
                f"{self.project_id_env}/{self.location_env} or "
                "GOOGLE_CLOUD_PROJECT/GOOGLE_CLOUD_LOCATION."
            )

        client_kwargs = {
            "vertexai": True,
            "project": project,
            "location": location,
        }

        credentials = self._load_credentials()
        if credentials is not None:
            client_kwargs["credentials"] = credentials

        return genai.Client(**client_kwargs)

    def _get_client(self):
        if self._client is not None:
            return self._client

        auth_mode = self._resolve_auth_mode()
        if auth_mode == "api_key":
            self._client = self._build_api_key_client()
        elif auth_mode == "project_credentials":
            self._client = self._build_project_credentials_client()
        else:
            raise RuntimeError(f"Unexpected resolved Vertex AI auth mode: {auth_mode}")
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
                "thoughts_token_count": getattr(usage_meta, "thoughts_token_count", None),
                "cached_content_token_count": getattr(usage_meta, "cached_content_token_count", None),
            }

        return LLMResponse(
            text=text,
            finish_reason=finish_reason,
            usage=usage,
            raw=raw,
            provider=self.provider_name,
            backend="google_vertex",
            family="gemini",
        )
