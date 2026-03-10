import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.core.llm_provider import LLMRequest
from modules.core.llm_router import LLMProviderRouter, get_shared_llm_router
from modules.core.providers.anthropic_provider import AnthropicProvider
from modules.core.providers.openai_provider import OpenAIProvider
from modules.core.providers.vertex_provider import VertexAIProvider
from modules.core.response_schemas import DIRECTOR_AUDIT_SCHEMA


def test_router_resolves_gemini_models():
    router = LLMProviderRouter()
    provider = router.get_provider_for_model("gemini-2.5-pro")
    assert provider.provider_name == "gemini"


def test_router_rejects_unknown_models():
    router = LLMProviderRouter()
    with pytest.raises(ValueError):
        router.get_provider_for_model("mystery-1")


def test_router_rejects_disabled_provider():
    router = LLMProviderRouter(provider_configs={"anthropic": {"enabled": False}})
    with pytest.raises(ValueError, match="disabled"):
        router.get_provider_for_model("claude-sonnet-4-6")


def test_router_enables_registered_non_gemini_providers():
    router = LLMProviderRouter(
        provider_configs={
            "anthropic": {"enabled": True, "api_key_env": "ANTHROPIC_API_KEY"},
            "openai": {"enabled": True, "api_key_env": "OPENAI_API_KEY"},
            "vertex_ai": {"enabled": True, "project_id_env": "VERTEX_PROJECT_ID", "location_env": "VERTEX_LOCATION"},
        }
    )
    assert isinstance(router.get_provider_for_model("claude-sonnet-4-6"), AnthropicProvider)
    assert isinstance(router.get_provider_for_model("gpt-5"), OpenAIProvider)
    assert isinstance(router.get_provider_for_model("vertexai:gemini-2.5-pro"), VertexAIProvider)
    assert router.get_enabled_provider_names() == ("anthropic", "gemini", "openai", "vertex_ai")


def test_shared_router_is_singleton():
    assert get_shared_llm_router() is get_shared_llm_router()


def test_router_rejects_disabled_vertex_provider():
    router = LLMProviderRouter(provider_configs={"vertex_ai": {"enabled": False}})
    with pytest.raises(ValueError, match="disabled"):
        router.get_provider_for_model("vertexai:gemini-2.5-pro")


def test_gemini_provider_preserves_raw_response():
    router = LLMProviderRouter()
    client = MagicMock()
    raw = MagicMock()
    raw.text = '{"ok": true}'
    raw.candidates = [MagicMock(finish_reason="STOP")]
    client.models.generate_content.return_value = raw

    response = router.get_provider_for_model("gemini-2.5-flash").generate(
        client=client,
        request=LLMRequest(model="gemini-2.5-flash", contents="hello", config={"temperature": 0.1}),
    )

    assert response.raw is raw
    assert response.text == '{"ok": true}'
    assert response.finish_reason == "STOP"
    client.models.generate_content.assert_called_once_with(
        model="gemini-2.5-flash",
        contents="hello",
        config={"temperature": 0.1},
    )


def test_anthropic_provider_generate_with_fake_sdk(monkeypatch):
    captured_kwargs = {}

    class FakeAnthropic:
        def __init__(self, api_key):
            self.api_key = api_key
            self.messages = SimpleNamespace(create=self._create)

        @staticmethod
        def _create(**kwargs):
            captured_kwargs.update(kwargs)
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text="hello from claude")],
                stop_reason="end_turn",
                usage=SimpleNamespace(input_tokens=10, output_tokens=20),
            )

    fake_module = ModuleType("anthropic")
    fake_module.Anthropic = FakeAnthropic
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    provider = AnthropicProvider()
    response = provider.generate(
        client=MagicMock(),
        request=LLMRequest(
            model="claude-sonnet-4-6",
            contents="hello",
            config={"max_output_tokens": 64, "temperature": 0.2, "top_p": 0.9, "system": "sys"},
        ),
    )

    assert response.text == "hello from claude"
    assert response.finish_reason == "end_turn"
    assert response.usage == {"input_tokens": 10, "output_tokens": 20}
    assert captured_kwargs["max_tokens"] == 64
    assert captured_kwargs["temperature"] == 0.2
    assert captured_kwargs["top_p"] == 0.9
    assert captured_kwargs["system"] == "sys"


def test_openai_provider_generate_with_fake_sdk(monkeypatch):
    captured_kwargs = {}

    class FakeResponses:
        @staticmethod
        def create(**kwargs):
            captured_kwargs.update(kwargs)
            return SimpleNamespace(
                output_text="hello from gpt",
                status="completed",
                usage=SimpleNamespace(input_tokens=11, output_tokens=22, total_tokens=33),
            )

    class FakeOpenAI:
        def __init__(self, api_key):
            self.api_key = api_key
            self.responses = FakeResponses()

    fake_module = ModuleType("openai")
    fake_module.OpenAI = FakeOpenAI
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", fake_module)

    provider = OpenAIProvider()
    response = provider.generate(
        client=MagicMock(),
        request=LLMRequest(
            model="gpt-5",
            contents="hello",
            config={
                "temperature": 0.1,
                "top_p": 0.8,
                "max_output_tokens": 321,
                "response_mime_type": "application/json",
                "response_schema": DIRECTOR_AUDIT_SCHEMA,
            },
        ),
    )

    assert response.text == "hello from gpt"
    assert response.finish_reason == "completed"
    assert response.usage == {"input_tokens": 11, "output_tokens": 22, "total_tokens": 33}
    assert captured_kwargs["temperature"] == 0.1
    assert captured_kwargs["top_p"] == 0.8
    assert captured_kwargs["max_output_tokens"] == 321
    assert captured_kwargs["text"]["format"]["type"] == "json_schema"
    assert captured_kwargs["text"]["format"]["strict"] is True
    assert captured_kwargs["text"]["format"]["schema"]["type"] == "object"


def test_vertex_provider_generate_with_fake_sdk(monkeypatch):
    captured_kwargs = {}
    fake_credentials = object()

    class FakeModels:
        @staticmethod
        def generate_content(**kwargs):
            captured_kwargs.update(kwargs)
            return SimpleNamespace(
                text='{"ok": true}',
                candidates=[SimpleNamespace(finish_reason="STOP")],
                usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=23, total_token_count=35),
            )

    class FakeClient:
        def __init__(self, **kwargs):
            captured_kwargs["client_kwargs"] = kwargs
            self.models = FakeModels()

    monkeypatch.setenv("VERTEX_PROJECT_ID", "vertex-proj")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "C:/tmp/fake-sa.json")
    monkeypatch.setattr("modules.core.providers.vertex_provider.genai.Client", FakeClient)
    monkeypatch.setattr(
        "modules.core.providers.vertex_provider.VertexAIProvider._load_credentials",
        lambda self: fake_credentials,
    )

    provider = VertexAIProvider()
    response = provider.generate(
        client=MagicMock(),
        request=LLMRequest(
            model="vertexai:gemini-2.5-pro",
            contents="hello",
            config={"temperature": 0.1},
        ),
    )

    assert response.text == '{"ok": true}'
    assert response.finish_reason == "STOP"
    assert response.usage == {
        "prompt_token_count": 12,
        "candidates_token_count": 23,
        "total_token_count": 35,
    }
    assert captured_kwargs["model"] == "gemini-2.5-pro"
    assert captured_kwargs["config"] == {"temperature": 0.1}
    assert captured_kwargs["client_kwargs"]["vertexai"] is True
    assert captured_kwargs["client_kwargs"]["project"] == "vertex-proj"
    assert captured_kwargs["client_kwargs"]["location"] == "us-central1"
    assert captured_kwargs["client_kwargs"]["credentials"] is fake_credentials
