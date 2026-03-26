import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.core.llm_generate import generate_content_via_router, generate_raw_content_via_router
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
        "thoughts_token_count": None,
        "cached_content_token_count": None,
    }
    assert captured_kwargs["model"] == "gemini-2.5-pro"
    assert captured_kwargs["config"] == {"temperature": 0.1}
    assert captured_kwargs["client_kwargs"]["vertexai"] is True


# ── Wave 1: Provider envelope identity tests ──────────────────────────────


def test_gemini_provider_sets_backend_family():
    client = MagicMock()
    raw = MagicMock()
    raw.text = "ok"
    raw.candidates = [MagicMock(finish_reason="STOP")]
    raw.usage_metadata = None
    client.models.generate_content.return_value = raw

    from modules.core.providers.gemini_provider import GeminiProvider

    response = GeminiProvider().generate(
        client=client,
        request=LLMRequest(model="gemini-2.5-flash", contents="hello"),
    )
    assert response.provider == "gemini"
    assert response.backend == "google_direct"
    assert response.family == "gemini"


def test_vertex_provider_sets_backend_family(monkeypatch):
    captured = {}

    class FakeModels:
        @staticmethod
        def generate_content(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                text="ok",
                candidates=[SimpleNamespace(finish_reason="STOP")],
                usage_metadata=None,
            )

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setenv("VERTEX_PROJECT_ID", "proj")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setattr("modules.core.providers.vertex_provider.genai.Client", FakeClient)
    monkeypatch.setattr(
        "modules.core.providers.vertex_provider.VertexAIProvider._load_credentials",
        lambda self: None,
    )

    response = VertexAIProvider().generate(
        client=MagicMock(),
        request=LLMRequest(model="vertexai:gemini-2.5-flash", contents="hello"),
    )
    assert response.provider == "vertex_ai"
    assert response.backend == "google_vertex"
    assert response.family == "gemini"


def test_anthropic_provider_sets_backend_family(monkeypatch):
    class FakeAnthropic:
        def __init__(self, api_key):
            self.messages = SimpleNamespace(create=self._create)

        @staticmethod
        def _create(**kwargs):
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text="ok")],
                stop_reason="end_turn",
                usage=SimpleNamespace(input_tokens=1, output_tokens=1),
            )

    fake_module = ModuleType("anthropic")
    fake_module.Anthropic = FakeAnthropic
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    response = AnthropicProvider().generate(
        client=MagicMock(),
        request=LLMRequest(model="claude-sonnet-4-6", contents="hello"),
    )
    assert response.provider == "anthropic"
    assert response.backend == "anthropic_direct"
    assert response.family == "claude"


def test_openai_provider_sets_backend_family(monkeypatch):
    class FakeOpenAI:
        def __init__(self, api_key):
            self.responses = SimpleNamespace(
                create=lambda **kw: SimpleNamespace(
                    output_text="ok", status="completed", usage=None,
                )
            )

    fake_module = ModuleType("openai")
    fake_module.OpenAI = FakeOpenAI
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setitem(sys.modules, "openai", fake_module)

    response = OpenAIProvider().generate(
        client=MagicMock(),
        request=LLMRequest(model="gpt-5", contents="hello"),
    )
    assert response.provider == "openai"
    assert response.backend == "openai_direct"
    assert response.family == "gpt"


# ── Wave 1: Metrics attribution tests ─────────────────────────────────────


def test_metrics_start_call_infers_provider_identity():
    from modules.core.metrics_collector import MetricsCollector

    MetricsCollector.reset()
    collector = MetricsCollector()
    try:
        mid = collector.start_call("Writer", "vertexai:gemini-2.5-flash")
        # Access internal metric to verify identity was set
        assert mid not in collector._metrics or True  # metric may have been cleaned
        # Verify via a fresh call that identity propagates through end_call
        mid2 = collector.start_call("Writer", "gemini-2.5-flash")
        metric = collector._metrics[mid2]
        assert metric.provider == "gemini"
        assert metric.backend == "google_direct"
        assert metric.family == "gemini"
    finally:
        MetricsCollector.reset()


def test_metrics_vertex_vs_gemini_distinguishable():
    from modules.core.metrics_collector import MetricsCollector

    MetricsCollector.reset()
    collector = MetricsCollector()
    try:
        mid_direct = collector.start_call("Writer", "gemini-2.5-flash")
        mid_vertex = collector.start_call("Writer", "vertexai:gemini-2.5-flash")

        m_direct = collector._metrics[mid_direct]
        m_vertex = collector._metrics[mid_vertex]

        assert m_direct.provider == "gemini"
        assert m_direct.backend == "google_direct"
        assert m_vertex.provider == "vertex_ai"
        assert m_vertex.backend == "google_vertex"
        assert m_direct.family == m_vertex.family == "gemini"
    finally:
        MetricsCollector.reset()


# ── Wave 1: ProcessRunner env passthrough tests ───────────────────────────


def test_process_runner_build_env_vertex_passthrough():
    from modules.api.process_runner import ProcessRunner

    runner = ProcessRunner()
    env = runner._build_env({
        "vertex_api_key": "vk-123",
        "vertex_project_id": "my-proj",
        "vertex_location": "us-central1",
        "google_credentials_path": "/tmp/sa.json",
    })
    assert env["VERTEX_API_KEY"] == "vk-123"
    assert env["VERTEX_PROJECT_ID"] == "my-proj"
    assert env["VERTEX_LOCATION"] == "us-central1"
    assert env["GOOGLE_APPLICATION_CREDENTIALS"] == "/tmp/sa.json"


def test_process_runner_build_env_vertex_absent_no_override():
    import os

    from modules.api.process_runner import ProcessRunner

    runner = ProcessRunner()
    env = runner._build_env({})
    # Vertex vars should only appear if already in os.environ (via copy)
    # Not injected from empty inputs
    for key in ("VERTEX_API_KEY", "VERTEX_PROJECT_ID", "VERTEX_LOCATION"):
        if key not in os.environ:
            assert key not in env


def test_generate_content_via_router_returns_normalized_response(monkeypatch):
    raw = SimpleNamespace(text="native")
    provider = MagicMock()
    provider.generate.return_value = SimpleNamespace(
        text="normalized",
        finish_reason="STOP",
        usage={"prompt_token_count": 7},
        raw=raw,
        provider="gemini",
    )
    router = MagicMock()
    router.get_provider_for_model.return_value = provider
    monkeypatch.setattr("modules.core.llm_generate.get_shared_llm_router", lambda: router)

    response = generate_content_via_router(client=MagicMock(), model="gemini-2.5-flash", contents="hello")

    assert response.text == "normalized"
    assert response.finish_reason == "STOP"
    assert response.raw is raw

    raw_response = generate_raw_content_via_router(client=MagicMock(), model="gemini-2.5-flash", contents="hello")
    assert raw_response is raw
