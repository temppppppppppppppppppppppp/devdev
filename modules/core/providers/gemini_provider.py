from __future__ import annotations

from typing import Any

from modules.core.llm_provider import LLMRequest, LLMResponse


class GeminiProvider:
    provider_name = "gemini"

    def generate(self, *, client: Any, request: LLMRequest) -> LLMResponse:
        raw = client.models.generate_content(
            model=request.model,
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
