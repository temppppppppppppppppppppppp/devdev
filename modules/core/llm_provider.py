from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class LLMRequest:
    """Provider-agnostic generate request envelope."""

    model: str
    contents: Any
    config: Any | None = None


@dataclass(slots=True)
class LLMResponse:
    """Normalized generate response envelope.

    `raw` keeps the provider-native response so Gemini-first call sites can
    migrate incrementally without rewriting downstream parsing in the same batch.

    `backend` / `family` carry the multi-provider spine identity so downstream
    code never needs to parse model-name strings to decide behaviour.
    """

    text: str = ""
    finish_reason: str = "stop"
    usage: dict[str, Any] | None = None
    raw: Any | None = None
    provider: str = "unknown"
    backend: str = "unknown"
    family: str = "unknown"


class LLMProvider(Protocol):
    provider_name: str

    def generate(self, *, client: Any, request: LLMRequest) -> LLMResponse:
        """Execute one text generation request."""

