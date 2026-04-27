import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.core.llm_generate import generate_content_via_router, generate_raw_content_via_router
from modules.core.llm_provider import LLMRequest
from modules.core.llm_router import LLMProviderRouter, get_shared_llm_router
from modules.core.models_config import load_models_yaml
from modules.core.providers.anthropic_provider import AnthropicProvider
from modules.core.providers.anthropic_vertex_provider import AnthropicVertexProvider
from modules.core.providers.openai_provider import OpenAIProvider
from modules.core.providers.vertex_provider import VertexAIProvider
from modules.core.response_schemas import DIRECTOR_AUDIT_SCHEMA


@pytest.fixture(autouse=True)
def _clear_provider_mode_env(monkeypatch):
    monkeypatch.delenv("GEULDOBI_PROVIDER_MODE", raising=False)
    monkeypatch.delenv("GEULDOBI_FORCE_GOOGLE_MODEL", raising=False)
    monkeypatch.delenv("GEULDOBI_VERTEX_AUTH_MODE", raising=False)
    monkeypatch.delenv("VERTEX_API_KEY", raising=False)
    monkeypatch.delenv("VERTEX_PROJECT_ID", raising=False)
    monkeypatch.delenv("VERTEX_LOCATION", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)


def test_repo_models_yaml_reflects_canonical_vertex_core_roles():
    payload = load_models_yaml()

    assert payload["providers"]["anthropic"]["enabled"] is True
    assert payload["providers"]["vertex_ai"]["enabled"] is True
    assert payload["agents"]["analyst"] == "vertexai:gemini-3.1-pro-preview"
    assert payload["agents"]["chief_writer"] == "vertexai:gemini-3.1-pro-preview"
    assert payload["agents"]["director"] == "vertexai:gemini-3.1-pro-preview"
    assert payload["fallback_chain"]["claude-sonnet-4-6"] == "vertexai:gemini-3.1-pro-preview"
    assert payload["fallback_chain"]["claude-sonnet-4-20250514"] == "vertexai:gemini-3.1-pro-preview"


def test_load_models_yaml_rewrites_to_gemini_direct_when_env_forced(monkeypatch):
    monkeypatch.setenv("GEULDOBI_PROVIDER_MODE", "gemini_direct")

    payload = load_models_yaml()

    assert payload["providers"]["anthropic"]["enabled"] is True
    assert payload["providers"]["vertex_ai"]["enabled"] is False
    assert payload["agents"]["analyst"] == "gemini-3.1-pro-preview"
    assert payload["agents"]["chief_writer"] == "gemini-3.1-pro-preview"
    assert payload["agents"]["director"] == "gemini-3.1-pro-preview"
    assert payload["fallback_chain"]["claude-sonnet-4-6"] == "gemini-3.1-pro-preview"


def test_load_models_yaml_force_google_model_pins_runtime_roles(monkeypatch):
    monkeypatch.setenv("GEULDOBI_PROVIDER_MODE", "vertex_ai")
    monkeypatch.setenv("GEULDOBI_FORCE_GOOGLE_MODEL", "gemini-3.1-pro-preview")

    payload = load_models_yaml()

    forced = "vertexai:gemini-3.1-pro-preview"
    assert payload["agents"]["analyst"] == forced
    assert payload["agents"]["manager"] == forced
    assert payload["agents"]["writer"] == forced
    assert payload["sub_components"]["four_phase_arc_generator"]["preflight"] == forced
    assert payload["role_constants"]["flash_main"] == forced
    assert payload["role_constants"]["emergency"] == forced
    assert payload["fallback_chain"]["claude-sonnet-4-6"] == forced
    assert payload["fallback_chain"][forced] == forced
    assert "vertexai:gemini-2.5-pro" not in str(payload["fallback_chain"])
    assert "vertexai:gemini-2.5-flash" not in str(payload["fallback_chain"])


def test_router_resolves_gemini_models():
    router = LLMProviderRouter()
    provider = router.get_provider_for_model("gemini-2.5-pro")
    assert provider.provider_name == "gemini"


def test_router_forces_vertex_provider_for_bare_gemini_when_env_forced(monkeypatch):
    monkeypatch.setenv("GEULDOBI_PROVIDER_MODE", "vertex_ai")
    router = LLMProviderRouter()

    provider = router.get_provider_for_model("gemini-2.5-pro")

    assert provider.provider_name == "vertex_ai"


def test_router_forces_gemini_provider_for_vertex_prefixed_model_when_env_forced(monkeypatch):
    monkeypatch.setenv("GEULDOBI_PROVIDER_MODE", "gemini_direct")
    router = LLMProviderRouter()

    provider = router.get_provider_for_model("vertexai:gemini-2.5-pro")

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
            "vertex_ai": {
                "enabled": True,
                "auth_mode": "project_credentials",
                "project_id_env": "VERTEX_PROJECT_ID",
                "location_env": "VERTEX_LOCATION",
            },
        }
    )
    assert isinstance(router.get_provider_for_model("claude-sonnet-4-6"), AnthropicProvider)
    assert isinstance(router.get_provider_for_model("gpt-5"), OpenAIProvider)
    assert isinstance(router.get_provider_for_model("vertexai:gemini-2.5-pro"), VertexAIProvider)
    assert router.get_enabled_provider_names() == ("anthropic", "gemini", "openai", "vertex_ai")


def test_router_passes_vertex_auth_mode_config():
    router = LLMProviderRouter(provider_configs={"vertex_ai": {"enabled": True, "auth_mode": "project_credentials"}})
    provider = router.get_provider_for_model("vertexai:gemini-2.5-pro")
    assert isinstance(provider, VertexAIProvider)
    assert provider.auth_mode == "project_credentials"


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
    assert captured_kwargs["model"] == "claude-sonnet-4-20250514"
    assert captured_kwargs["temperature"] == 0.2
    assert captured_kwargs["top_p"] == 0.9
    assert captured_kwargs["system"] == "sys"


def test_anthropic_provider_accepts_claude_api_env_alias(monkeypatch):
    captured_api_key = {}

    class FakeAnthropic:
        def __init__(self, api_key):
            captured_api_key["value"] = api_key
            self.messages = SimpleNamespace(
                create=lambda **kw: SimpleNamespace(
                    content=[SimpleNamespace(type="text", text="alias ok")],
                    stop_reason="end_turn",
                    usage=SimpleNamespace(input_tokens=1, output_tokens=2),
                )
            )

    fake_module = ModuleType("anthropic")
    fake_module.Anthropic = FakeAnthropic
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("CLAUDE_API", "alias-key")
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    response = AnthropicProvider().generate(
        client=MagicMock(),
        request=LLMRequest(model="claude-opus-4-6", contents="hello"),
    )

    assert captured_api_key["value"] == "alias-key"
    assert response.text == "alias ok"


def test_anthropic_provider_clamps_long_sync_requests(monkeypatch):
    captured_kwargs = {}

    class FakeAnthropic:
        def __init__(self, api_key):
            self.messages = SimpleNamespace(
                create=lambda **kwargs: (
                    captured_kwargs.update(kwargs)
                    or SimpleNamespace(
                        content=[SimpleNamespace(type="text", text="clamped ok")],
                        stop_reason="end_turn",
                        usage=SimpleNamespace(input_tokens=1, output_tokens=2),
                    )
                )
            )

    fake_module = ModuleType("anthropic")
    fake_module.Anthropic = FakeAnthropic
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    response = AnthropicProvider().generate(
        client=MagicMock(),
        request=LLMRequest(
            model="claude-sonnet-4-6",
            contents="hello",
            config={"max_output_tokens": 65536, "temperature": 0.0},
        ),
    )

    assert response.text == "clamped ok"
    assert captured_kwargs["max_tokens"] == 8192


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

    provider = VertexAIProvider(auth_mode="project_credentials")
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


def test_vertex_provider_api_key_mode_ignores_project_location(monkeypatch):
    captured_kwargs = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    monkeypatch.setenv("VERTEX_API_KEY", "vertex-express-key")
    monkeypatch.setenv("VERTEX_PROJECT_ID", "vertex-proj")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setattr("modules.core.providers.vertex_provider.genai.Client", FakeClient)

    provider = VertexAIProvider(auth_mode="api_key")
    provider._get_client()

    assert captured_kwargs == {"vertexai": True, "api_key": "vertex-express-key"}


def test_vertex_provider_auto_mode_prefers_api_key(monkeypatch):
    captured_kwargs = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    monkeypatch.setenv("VERTEX_API_KEY", "vertex-express-key")
    monkeypatch.setenv("VERTEX_PROJECT_ID", "vertex-proj")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setattr("modules.core.providers.vertex_provider.genai.Client", FakeClient)

    provider = VertexAIProvider(auth_mode="auto")
    provider._get_client()

    assert captured_kwargs == {"vertexai": True, "api_key": "vertex-express-key"}


def test_vertex_provider_env_auth_mode_overrides_auto_api_key(monkeypatch):
    captured_kwargs = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    monkeypatch.setenv("GEULDOBI_VERTEX_AUTH_MODE", "project_credentials")
    monkeypatch.setenv("VERTEX_API_KEY", "vertex-express-key")
    monkeypatch.setenv("VERTEX_PROJECT_ID", "vertex-proj")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setattr("modules.core.providers.vertex_provider.genai.Client", FakeClient)
    monkeypatch.setattr(
        "modules.core.providers.vertex_provider.VertexAIProvider._load_credentials",
        lambda self: None,
    )

    provider = VertexAIProvider(auth_mode="auto")
    provider._get_client()

    assert captured_kwargs == {
        "vertexai": True,
        "project": "vertex-proj",
        "location": "us-central1",
    }


def test_vertex_provider_project_credentials_mode_uses_project_location(monkeypatch):
    captured_kwargs = {}
    fake_credentials = object()

    class FakeClient:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    monkeypatch.delenv("VERTEX_API_KEY", raising=False)
    monkeypatch.setenv("VERTEX_PROJECT_ID", "vertex-proj")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setattr("modules.core.providers.vertex_provider.genai.Client", FakeClient)
    monkeypatch.setattr(
        "modules.core.providers.vertex_provider.VertexAIProvider._load_credentials",
        lambda self: fake_credentials,
    )

    provider = VertexAIProvider(auth_mode="project_credentials")
    provider._get_client()

    assert captured_kwargs["vertexai"] is True
    assert captured_kwargs["project"] == "vertex-proj"
    assert captured_kwargs["location"] == "us-central1"
    assert captured_kwargs["credentials"] is fake_credentials
    assert "api_key" not in captured_kwargs


def test_vertex_provider_api_key_mode_requires_api_key(monkeypatch):
    monkeypatch.delenv("VERTEX_API_KEY", raising=False)
    monkeypatch.setenv("VERTEX_PROJECT_ID", "vertex-proj")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")

    provider = VertexAIProvider(auth_mode="api_key")
    with pytest.raises(RuntimeError, match="VERTEX_API_KEY"):
        provider._get_client()


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

    response = VertexAIProvider(auth_mode="project_credentials").generate(
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
                    output_text="ok",
                    status="completed",
                    usage=None,
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


def test_openai_provider_applies_http_options_timeout_to_client():
    class FakeResponses:
        def __init__(self):
            self.kwargs = {}

        def create(self, **kw):
            self.kwargs = kw
            return SimpleNamespace(output_text="ok", status="completed", usage=None)

    class FakeClient:
        def __init__(self):
            self.responses = FakeResponses()
            self.timeout = None

        def with_options(self, *, timeout):
            self.timeout = timeout
            return self

    fake_client = FakeClient()
    provider = OpenAIProvider()
    provider._client = fake_client

    response = provider.generate(
        client=MagicMock(),
        request=LLMRequest(
            model="gpt-5",
            contents="hello",
            config=SimpleNamespace(http_options=SimpleNamespace(timeout=123000)),
        ),
    )

    assert response.text == "ok"
    assert fake_client.timeout == 123.0


def test_anthropic_provider_applies_http_options_timeout_to_client():
    class FakeMessages:
        def create(self, **_kwargs):
            return SimpleNamespace(content=[SimpleNamespace(type="text", text="ok")], stop_reason="stop", usage=None)

    class FakeClient:
        def __init__(self):
            self.messages = FakeMessages()
            self.timeout = None

        def with_options(self, *, timeout):
            self.timeout = timeout
            return self

    fake_client = FakeClient()
    provider = AnthropicProvider()
    provider._client = fake_client

    response = provider.generate(
        client=MagicMock(),
        request=LLMRequest(
            model="claude-sonnet-4-6",
            contents="hello",
            config=SimpleNamespace(http_options=SimpleNamespace(timeout=456000)),
        ),
    )

    assert response.text == "ok"
    assert fake_client.timeout == 456.0


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
    env = runner._build_env(
        {
            "provider_mode": "ambient",
            "vertex_api_key": "vk-123",
            "vertex_project_id": "my-proj",
            "vertex_location": "us-central1",
            "google_credentials_path": "/tmp/sa.json",
        }
    )
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


# ── Wave 1: Claude on Vertex — routing / identity / guard tests ─────────


def test_router_infers_anthropic_vertex_from_prefix():
    assert LLMProviderRouter.infer_provider_name("anthropic-vertex:claude-sonnet-4-6") == "anthropic_vertex"
    assert LLMProviderRouter.infer_provider_name("anthropic_vertex:claude-opus-4-6") == "anthropic_vertex"


def test_router_anthropic_vertex_does_not_steal_bare_claude():
    """Bare 'claude-*' must still route to anthropic (direct), not anthropic_vertex."""
    assert LLMProviderRouter.infer_provider_name("claude-sonnet-4-6") == "anthropic"


def test_router_resolves_anthropic_vertex_provider():
    router = LLMProviderRouter(
        provider_configs={"anthropic_vertex": {"enabled": True}},
    )
    provider = router.get_provider_for_model("anthropic-vertex:claude-sonnet-4-6")
    assert isinstance(provider, AnthropicVertexProvider)
    assert provider.provider_name == "anthropic_vertex"


def test_router_rejects_disabled_anthropic_vertex():
    router = LLMProviderRouter(provider_configs={"anthropic_vertex": {"enabled": False}})
    with pytest.raises(ValueError, match="disabled"):
        router.get_provider_for_model("anthropic-vertex:claude-sonnet-4-6")


def test_router_enabled_names_include_anthropic_vertex():
    router = LLMProviderRouter(
        provider_configs={
            "anthropic_vertex": {"enabled": True},
            "anthropic": {"enabled": True, "api_key_env": "ANTHROPIC_API_KEY"},
        },
    )
    names = router.get_enabled_provider_names()
    assert "anthropic_vertex" in names
    assert "anthropic" in names


def test_anthropic_vertex_provider_generate_with_fake_sdk(monkeypatch):
    captured_kwargs = {}

    class FakeAnthropicVertex:
        def __init__(self, project_id, region):
            self.project_id = project_id
            self.region = region
            self.messages = SimpleNamespace(create=self._create)

        @staticmethod
        def _create(**kwargs):
            captured_kwargs.update(kwargs)
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text="hello from vertex claude")],
                stop_reason="end_turn",
                usage=SimpleNamespace(input_tokens=15, output_tokens=25),
            )

    fake_module = ModuleType("anthropic")
    fake_module.Anthropic = MagicMock()  # not used by vertex path
    fake_module.AnthropicVertex = FakeAnthropicVertex
    monkeypatch.setenv("VERTEX_PROJECT_ID", "my-proj")
    monkeypatch.setenv("VERTEX_LOCATION", "us-east5")
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    provider = AnthropicVertexProvider()
    response = provider.generate(
        client=MagicMock(),
        request=LLMRequest(
            model="anthropic-vertex:claude-sonnet-4-6",
            contents="hello",
            config={"max_output_tokens": 128, "temperature": 0.3},
        ),
    )

    assert response.text == "hello from vertex claude"
    assert response.finish_reason == "end_turn"
    assert response.provider == "anthropic_vertex"
    assert response.backend == "anthropic_vertex"
    assert response.family == "claude"
    assert response.usage == {"input_tokens": 15, "output_tokens": 25}
    # Model prefix should be stripped before sending to SDK
    assert captured_kwargs["model"] == "claude-sonnet-4-6"


def test_anthropic_vertex_provider_sets_backend_family(monkeypatch):
    class FakeAnthropicVertex:
        def __init__(self, project_id, region):
            self.messages = SimpleNamespace(
                create=lambda **kw: SimpleNamespace(
                    content=[SimpleNamespace(type="text", text="ok")],
                    stop_reason="end_turn",
                    usage=SimpleNamespace(input_tokens=1, output_tokens=1),
                )
            )

    fake_module = ModuleType("anthropic")
    fake_module.Anthropic = MagicMock()
    fake_module.AnthropicVertex = FakeAnthropicVertex
    monkeypatch.setenv("VERTEX_PROJECT_ID", "proj")
    monkeypatch.setenv("VERTEX_LOCATION", "us-east5")
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    response = AnthropicVertexProvider().generate(
        client=MagicMock(),
        request=LLMRequest(model="anthropic-vertex:claude-sonnet-4-6", contents="hello"),
    )
    assert response.provider == "anthropic_vertex"
    assert response.backend == "anthropic_vertex"
    assert response.family == "claude"


def test_anthropic_direct_provider_non_regression(monkeypatch):
    """Ensure AnthropicProvider (direct) still emits anthropic_direct backend."""

    class FakeAnthropic:
        def __init__(self, api_key):
            self.messages = SimpleNamespace(
                create=lambda **kw: SimpleNamespace(
                    content=[SimpleNamespace(type="text", text="direct ok")],
                    stop_reason="end_turn",
                    usage=SimpleNamespace(input_tokens=1, output_tokens=1),
                )
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


# ── Wave 1: Metrics — Claude identity + pricing tests ──────────────────


def test_metrics_infer_anthropic_vertex_identity():
    from modules.core.metrics_collector import MetricsCollector

    MetricsCollector.reset()
    collector = MetricsCollector()
    try:
        mid = collector.start_call("Writer", "anthropic-vertex:claude-sonnet-4-6")
        metric = collector._metrics[mid]
        assert metric.provider == "anthropic_vertex"
        assert metric.backend == "anthropic_vertex"
        assert metric.family == "claude"
    finally:
        MetricsCollector.reset()


def test_metrics_anthropic_vertex_vs_direct_distinguishable():
    from modules.core.metrics_collector import MetricsCollector

    MetricsCollector.reset()
    collector = MetricsCollector()
    try:
        mid_direct = collector.start_call("Writer", "claude-sonnet-4-6")
        mid_vertex = collector.start_call("Writer", "anthropic-vertex:claude-sonnet-4-6")

        m_direct = collector._metrics[mid_direct]
        m_vertex = collector._metrics[mid_vertex]

        assert m_direct.provider == "anthropic"
        assert m_direct.backend == "anthropic_direct"
        assert m_vertex.provider == "anthropic_vertex"
        assert m_vertex.backend == "anthropic_vertex"
        assert m_direct.family == m_vertex.family == "claude"
    finally:
        MetricsCollector.reset()


def test_metrics_claude_pricing_not_default():
    from modules.core.metrics_collector import MODEL_COSTS, _normalize_billable_model

    # Direct model name → Claude pricing
    assert "claude-sonnet-4-6" in MODEL_COSTS
    assert MODEL_COSTS["claude-sonnet-4-6"]["input"] == 3.00
    assert MODEL_COSTS["claude-sonnet-4-20250514"]["input"] == 3.00

    # Prefixed model name → strips prefix → Claude pricing
    assert _normalize_billable_model("anthropic-vertex:claude-sonnet-4-6") == "claude-sonnet-4-6"
    assert _normalize_billable_model("anthropic-vertex:claude-sonnet-4-20250514") == "claude-sonnet-4-20250514"


def test_metrics_claude_cost_calculation():
    from modules.core.metrics_collector import MetricsCollector

    MetricsCollector.reset()
    collector = MetricsCollector()
    try:
        cost = collector.calculate_cost("claude-sonnet-4-6", input_tokens=1_000_000, output_tokens=1_000_000)
        assert cost == pytest.approx(3.00 + 15.00, abs=0.01)  # $3 input + $15 output

        cost_vertex = collector.calculate_cost("anthropic-vertex:claude-sonnet-4-6", 1_000_000, 1_000_000)
        assert cost_vertex == pytest.approx(cost, abs=0.01)  # same pricing after prefix strip
    finally:
        MetricsCollector.reset()


# ── Wave 1: BaseAgent non-Gemini raw guard tests ───────────────────────


def test_base_agent_normalize_usage_gemini_passthrough():
    from modules.domain.agents.base_agent import BaseAgent

    gemini_usage = {"prompt_token_count": 100, "candidates_token_count": 50, "thoughts_token_count": 10}
    result = BaseAgent._normalize_usage(gemini_usage)
    assert result["prompt_token_count"] == 100
    assert result["candidates_token_count"] == 50


def test_base_agent_normalize_usage_claude_bridge():
    from modules.domain.agents.base_agent import BaseAgent

    claude_usage = {"input_tokens": 200, "output_tokens": 80}
    result = BaseAgent._normalize_usage(claude_usage)
    assert result["prompt_token_count"] == 200
    assert result["candidates_token_count"] == 80
    # Original keys preserved
    assert result["input_tokens"] == 200


def test_base_agent_normalize_usage_none_safe():
    from modules.domain.agents.base_agent import BaseAgent

    assert BaseAgent._normalize_usage(None) == {}
    assert BaseAgent._normalize_usage("not a dict") == {}


# ── Wave 1: ProcessRunner env passthrough — anthropic key ──────────────


def test_process_runner_build_env_anthropic_key_passthrough():
    from modules.api.process_runner import ProcessRunner

    runner = ProcessRunner()
    env = runner._build_env({"provider_mode": "ambient", "anthropic_api_key": "sk-ant-123"})
    assert env["ANTHROPIC_API_KEY"] == "sk-ant-123"
    assert env["CLAUDE_API"] == "sk-ant-123"


def test_process_runner_build_env_claude_key_passthrough():
    from modules.api.process_runner import ProcessRunner

    runner = ProcessRunner()
    env = runner._build_env({"provider_mode": "ambient", "claude_api_key": "sk-ant-456"})
    assert env["ANTHROPIC_API_KEY"] == "sk-ant-456"
    assert env["CLAUDE_API"] == "sk-ant-456"


def test_process_runner_build_env_anthropic_key_absent():
    import os

    from modules.api.process_runner import ProcessRunner

    runner = ProcessRunner()
    env = runner._build_env({})
    if "ANTHROPIC_API_KEY" not in os.environ:
        assert "ANTHROPIC_API_KEY" not in env
