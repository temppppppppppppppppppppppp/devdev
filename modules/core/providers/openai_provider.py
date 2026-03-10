from __future__ import annotations

import os
from typing import Any

from modules.core.llm_provider import LLMRequest, LLMResponse
from modules.core.llm_schema import schema_to_dict


class OpenAIProvider:
    provider_name = "openai"

    def __init__(self, api_key_env: str = "OPENAI_API_KEY") -> None:
        self.api_key_env = api_key_env
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"{self.api_key_env} is required to activate OpenAIProvider")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed. Install `openai` to enable GPT models.") from exc

        self._client = OpenAI(api_key=api_key)
        return self._client

    @staticmethod
    def _config_value(config: Any, key: str, default=None):
        if config is None:
            return default
        if isinstance(config, dict):
            return config.get(key, default)
        return getattr(config, key, default)

    def _build_request_kwargs(self, request: LLMRequest) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": request.model,
            "input": request.contents,
        }

        for src_key, dst_key in (
            ("temperature", "temperature"),
            ("top_p", "top_p"),
            ("max_output_tokens", "max_output_tokens"),
            ("store", "store"),
        ):
            value = self._config_value(request.config, src_key)
            if value is not None:
                kwargs[dst_key] = value

        response_mime_type = self._config_value(request.config, "response_mime_type")
        response_schema = self._config_value(request.config, "response_schema")
        if response_mime_type == "application/json":
            if response_schema is not None:
                kwargs["text"] = {
                    "format": {
                        "type": "json_schema",
                        "name": "structured_output",
                        "schema": schema_to_dict(response_schema),
                        "strict": True,
                    }
                }
            else:
                kwargs["text"] = {"format": {"type": "json_object"}}

        return kwargs

    @staticmethod
    def _extract_text(raw: Any) -> str:
        output_text = getattr(raw, "output_text", None)
        if isinstance(output_text, str) and output_text:
            return output_text

        chunks: list[str] = []
        for item in getattr(raw, "output", []) or []:
            for part in getattr(item, "content", []) or []:
                if getattr(part, "type", None) in {"output_text", "text"} and getattr(part, "text", None):
                    chunks.append(part.text)
        return "\n".join(chunks)

    def generate(self, *, client: Any, request: LLMRequest) -> LLMResponse:
        resolved_client = self._get_client()
        raw = resolved_client.responses.create(**self._build_request_kwargs(request))

        usage_raw = getattr(raw, "usage", None)
        usage = None
        if usage_raw is not None:
            usage = {
                "input_tokens": getattr(usage_raw, "input_tokens", None),
                "output_tokens": getattr(usage_raw, "output_tokens", None),
                "total_tokens": getattr(usage_raw, "total_tokens", None),
            }

        return LLMResponse(
            text=self._extract_text(raw),
            finish_reason=str(getattr(raw, "status", "completed") or "completed"),
            usage=usage,
            raw=raw,
            provider=self.provider_name,
        )
