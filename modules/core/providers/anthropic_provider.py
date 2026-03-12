from __future__ import annotations

import os
from typing import Any

from modules.core.llm_provider import LLMRequest, LLMResponse


class AnthropicProvider:
    provider_name = "anthropic"

    def __init__(self, api_key_env: str = "ANTHROPIC_API_KEY") -> None:
        self.api_key_env = api_key_env
        self._client = None

    @staticmethod
    def _config_value(config: Any, key: str, default=None):
        if config is None:
            return default
        if isinstance(config, dict):
            return config.get(key, default)
        return getattr(config, key, default)

    @staticmethod
    def _normalize_messages(contents: Any) -> list[dict[str, Any]]:
        if isinstance(contents, list) and all(isinstance(item, dict) and "role" in item for item in contents):
            return contents
        return [{"role": "user", "content": str(contents)}]

    def _get_client(self):
        if self._client is not None:
            return self._client

        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"{self.api_key_env} is required to activate AnthropicProvider")

        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic package is not installed. Install `anthropic` to enable Claude models.") from exc

        self._client = Anthropic(api_key=api_key)
        return self._client

    def generate(self, *, client: Any, request: LLMRequest) -> LLMResponse:
        resolved_client = self._get_client()
        max_tokens = int(self._config_value(request.config, "max_output_tokens", 4096) or 4096)
        kwargs = {
            "model": request.model,
            "messages": self._normalize_messages(request.contents),
            "max_tokens": max_tokens,
        }

        temperature = self._config_value(request.config, "temperature")
        if temperature is not None:
            kwargs["temperature"] = temperature

        top_p = self._config_value(request.config, "top_p")
        if top_p is not None:
            kwargs["top_p"] = top_p

        system = self._config_value(request.config, "system")
        if system:
            kwargs["system"] = system

        raw = resolved_client.messages.create(**kwargs)

        text_parts: list[str] = []
        for block in getattr(raw, "content", []) or []:
            if getattr(block, "type", None) == "text" and getattr(block, "text", None):
                text_parts.append(block.text)

        usage_raw = getattr(raw, "usage", None)
        usage = None
        if usage_raw is not None:
            usage = {
                "input_tokens": getattr(usage_raw, "input_tokens", None),
                "output_tokens": getattr(usage_raw, "output_tokens", None),
            }

        return LLMResponse(
            text="\n".join(text_parts),
            finish_reason=str(getattr(raw, "stop_reason", "stop") or "stop"),
            usage=usage,
            raw=raw,
            provider=self.provider_name,
        )
