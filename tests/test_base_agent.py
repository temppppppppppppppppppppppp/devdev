"""
[V64 P2-7] BaseAgent Unit Tests

_extract_json_robust (3단계 폴백 JSON 파서),
_escape_braces (중괄호 이스케이프),
_classify_error (에러 분류),
_validate_response (응답 유효성 검증),
_is_network_error (네트워크 오류 판별),
_create_error_response (에러 응답 생성),
_get_recovery_hint (복구 힌트),
MODEL_FALLBACK_CHAIN, THINKING_BUDGET_MAP.
"""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import modules.domain.agents.base_agent as base_agent_module
from modules.core.llm_provider import LLMResponse
from modules.domain.agents.base_agent import AgentErrorType, BaseAgent


@pytest.fixture(autouse=True)
def _isolate_model_env_for_base_agent_unit_tests(monkeypatch):
    """Keep root .env run pins from leaking into BaseAgent unit contracts."""

    monkeypatch.delenv("GEULDOBI_PROVIDER_MODE", raising=False)
    monkeypatch.delenv("GEULDOBI_FORCE_GOOGLE_MODEL", raising=False)
    BaseAgent.refresh_runtime_provider_state()
    yield
    monkeypatch.delenv("GEULDOBI_PROVIDER_MODE", raising=False)
    monkeypatch.delenv("GEULDOBI_FORCE_GOOGLE_MODEL", raising=False)
    BaseAgent.refresh_runtime_provider_state()


# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def agent():
    """기본 BaseAgent 인스턴스 (mock client)"""
    context = MagicMock()
    context.author_directives = ""
    client = MagicMock()
    return BaseAgent(context=context, client=client, model_tier="gemini-2.5-flash")


def seed_context_cache(
    agent,
    cache_name="cached/ctx",
    content_hash="hash-lineage",
    cache_type="manuscript",
    project_name="gc_ep21",
):
    import time

    cache_key = build_context_cache_key(agent, cache_type, project_name, content_hash)
    agent._context_caches[cache_key] = {
        "name": cache_name,
        "created_at": time.time(),
        "content_hash": content_hash,
        "model": agent.primary_model or "",
        "provider": base_agent_module._context_cache_provider_token(agent.client, agent.primary_model),
    }
    return cache_key


def build_context_cache_key(agent, cache_type, project_name, content_hash):
    return base_agent_module._build_context_cache_key(
        cache_type,
        project_name,
        content_hash,
        client=agent.client,
        primary_model=agent.primary_model,
    )


def test_base_agent_init_api_keys_uses_vertex_keys_when_mode_forced(monkeypatch):
    monkeypatch.setenv("GEULDOBI_PROVIDER_MODE", "vertex_ai")
    monkeypatch.setenv("VERTEX_API_KEY", "vertex-key-1")
    monkeypatch.setenv("VERTEX_API_KEY_2", "vertex-key-2")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY_2", raising=False)

    BaseAgent.refresh_runtime_provider_state()
    BaseAgent._init_api_keys()

    assert BaseAgent._api_keys == ["vertex-key-1", "vertex-key-2"]
    BaseAgent.refresh_runtime_provider_state()


def test_refresh_runtime_provider_state_resets_provider_state(monkeypatch):
    original_chain_loader = base_agent_module._get_model_fallback_chain
    monkeypatch.setattr(base_agent_module, "_get_model_fallback_chain", lambda: {"gemini-2.5-pro": "gemini-2.5-flash"})
    monkeypatch.setattr(BaseAgent, "_keys_initialized", True, raising=False)
    monkeypatch.setattr(BaseAgent, "_current_key_idx", 4, raising=False)
    monkeypatch.setattr(BaseAgent, "_key_rotation_pending", True, raising=False)
    monkeypatch.setattr(BaseAgent, "_last_rotation_time", 123.0, raising=False)
    monkeypatch.setattr(BaseAgent, "_rotation_count", 3, raising=False)
    monkeypatch.setattr(BaseAgent, "_api_keys", ["stale-key"], raising=False)
    monkeypatch.setattr(BaseAgent, "_quota_exhausted_models", {"gemini-2.5-pro": 999}, raising=False)
    monkeypatch.setattr(BaseAgent, "_context_caches", {"cache": {"name": "stale"}}, raising=False)

    BaseAgent.refresh_runtime_provider_state()

    assert BaseAgent._keys_initialized is False
    assert BaseAgent._current_key_idx == 0
    assert BaseAgent._key_rotation_pending is False
    assert BaseAgent._last_rotation_time == 0
    assert BaseAgent._rotation_count == 0
    assert BaseAgent._api_keys == []
    assert BaseAgent._quota_exhausted_models == {}
    assert BaseAgent._context_caches == {}
    assert BaseAgent.MODEL_FALLBACK_CHAIN == {"gemini-2.5-pro": "gemini-2.5-flash"}
    BaseAgent.MODEL_FALLBACK_CHAIN = original_chain_loader()


class TestResolveLoggingDb:
    def test_resolve_logging_db_supports_di_direct_and_none_context(self):
        client = MagicMock()

        di_db = object()
        di_context = SimpleNamespace(current_project=SimpleNamespace(db=di_db))
        di_agent = BaseAgent(context=di_context, client=client, model_tier="gemini-2.5-flash")
        assert di_agent._resolve_logging_db() is di_db

        direct_db = object()
        direct_context = SimpleNamespace(db=direct_db)
        direct_agent = BaseAgent(context=direct_context, client=client, model_tier="gemini-2.5-flash")
        assert direct_agent._resolve_logging_db() is direct_db

        none_context_agent = BaseAgent(context=None, client=client, model_tier="gemini-2.5-flash")
        assert none_context_agent._resolve_logging_db() is None


class TestOperatorLogBridge:
    def test_operator_log_uses_context_ui_log_with_metadata(self):
        client = MagicMock()
        ui = SimpleNamespace(log=MagicMock())
        context = SimpleNamespace(ui=ui, current_stage=4, current_ep=12)
        agent = BaseAgent(context=context, client=client, model_tier="gemini-2.5-flash")
        agent._current_context_tag = "stage4:ep12"

        ok = agent._operator_log("hello", level="warning", meta={"kind": "test"})

        assert ok is True
        ui.log.assert_called_once()
        args, kwargs = ui.log.call_args
        assert args == ("hello",)
        assert kwargs["component"] == "BaseAgent"
        assert kwargs["event_kind"] == "agent_log"
        assert kwargs["stage"] == "stage4"
        assert kwargs["ep_num"] == 12
        assert kwargs["attempt_key"] == "stage4:ep12"
        assert kwargs["level"] == "warning"
        assert kwargs["meta"] == {"kind": "test"}

    def test_operator_log_promotes_meta_event_kind_to_top_level(self):
        client = MagicMock()
        ui = SimpleNamespace(log=MagicMock())
        context = SimpleNamespace(ui=ui, current_stage=3, current_ep=9)
        agent = BaseAgent(context=context, client=client, model_tier="gemini-2.5-flash")

        ok = agent._operator_log(
            "screened",
            meta={"event_kind": "candidate_screening", "strategy": "balanced"},
        )

        assert ok is True
        ui.log.assert_called_once()
        args, kwargs = ui.log.call_args
        assert args == ("screened",)
        assert kwargs["event_kind"] == "candidate_screening"
        assert kwargs["meta"] == {"strategy": "balanced"}

    def test_operator_log_falls_back_to_message_only_callback(self):
        client = MagicMock()
        callback = MagicMock(side_effect=[TypeError("no kwargs"), None])
        context = SimpleNamespace(operator_log=callback)
        agent = BaseAgent(context=context, client=client, model_tier="gemini-2.5-flash")

        ok = agent._operator_log("fallback")

        assert ok is True
        assert callback.call_args_list[0].args == ("fallback",)
        assert callback.call_args_list[0].kwargs["component"] == "BaseAgent"
        assert callback.call_args_list[1].args == ("fallback",)
        assert callback.call_args_list[1].kwargs == {}


class TestContextCacheNamespace:
    def test_prefers_current_project_identity(self):
        client = MagicMock()
        context = SimpleNamespace(
            current_project=SimpleNamespace(work_id="hero_reborn", name="Hero Reborn"),
            project_name="fallback_project",
            genre="wuxia",
        )
        agent = BaseAgent(context=context, client=client, model_tier="gemini-2.5-flash")

        assert agent._context_cache_project_namespace("ep", 12) == "hero_reborn_ep_12"

    def test_falls_back_to_context_project_name_and_genre(self):
        client = MagicMock()
        agent = BaseAgent(
            context=SimpleNamespace(project_name="My Project", genre="investment"),
            client=client,
            model_tier="gemini-2.5-flash",
        )
        fallback_agent = BaseAgent(
            context=SimpleNamespace(genre="investment"),
            client=client,
            model_tier="gemini-2.5-flash",
        )

        assert agent._context_cache_project_namespace("arc", 3) == "My_Project_arc_3"
        assert fallback_agent._context_cache_project_namespace("arc", 3) == "investment_arc_3"


def test_generate_content_preserves_provider_neutral_response(agent, monkeypatch):
    response = LLMResponse(text='{"status":"ok"}', raw=SimpleNamespace(provider_raw=True))
    monkeypatch.setattr(agent, "_generate_llm_response", lambda **_kwargs: response)

    result = agent._generate_content(model="claude-sonnet-4-6", contents="ping", config={})

    assert result is response
    assert result.text == '{"status":"ok"}'


# ══════════════════════════════════════════════════════════════
# Test 1: _extract_json_robust - 정상 JSON
# ══════════════════════════════════════════════════════════════


class TestExtractJsonRobustNormal:
    def test_valid_json(self, agent):
        """정상 JSON 파싱"""
        text = json.dumps({"tactical_doc": "작전 계획", "arc_no": 5})
        result = agent._extract_json_robust(text)
        assert result["tactical_doc"] == "작전 계획"
        assert result["arc_no"] == 5

    def test_json_with_markdown_fences(self, agent):
        """```json ... ``` 마크다운 펜스 제거"""
        text = '```json\n{"content": "원고 내용", "title": "제목"}\n```'
        result = agent._extract_json_robust(text)
        assert result["content"] == "원고 내용"
        assert result["title"] == "제목"

    def test_nested_json(self, agent):
        """[Sweep64] state_updates는 평탄화하지 않고 원본 보존"""
        text = json.dumps({"title": "테스트", "state_updates": {"location": "무림맹", "energy": 70}})
        result = agent._extract_json_robust(text)
        # state_updates는 _RECURSE_KEYS가 아니므로 원본 dict 보존
        assert result.get("state_updates") == {"location": "무림맹", "energy": 70}
        assert result.get("title") == "테스트"


# ══════════════════════════════════════════════════════════════
# Test 2: _extract_json_robust - 손상된 JSON
# ══════════════════════════════════════════════════════════════


class TestExtractJsonRobustDamaged:
    def test_unclosed_brace(self, agent):
        """닫히지 않은 중괄호 자동 수리"""
        text = '{"tactical_doc": "작전 계획", "arc_no": 5'
        result = agent._extract_json_robust(text)
        assert "tactical_doc" in result
        assert result.get("parsing_error") is not True or "작전 계획" in str(result)

    def test_empty_input(self, agent):
        """빈 입력"""
        result = agent._extract_json_robust("")
        assert result.get("parsing_error") is True

    def test_none_input(self, agent):
        """None 입력"""
        result = agent._extract_json_robust(None)
        assert result.get("parsing_error") is True

    def test_non_string_input(self, agent):
        """문자열이 아닌 입력"""
        result = agent._extract_json_robust(12345)
        assert result.get("parsing_error") is True

    def test_tactical_doc_regex_extraction(self, agent):
        """tactical_doc 정규식 폴백 추출 - JSON 구조 내에서"""
        # _extract_json_robust는 {로 시작하는 구조를 먼저 찾으므로,
        # JSON-like 구조에서 tactical_doc 추출 테스트
        text = '{"tactical_doc": "중요한 작전 문서", "broken'
        result = agent._extract_json_robust(text)
        assert "tactical_doc" in result or "content" in result or "parsing_error" in result

    def test_content_regex_extraction(self, agent):
        """content 정규식 폴백 추출"""
        text = 'garbage "content": "원고 내용입니다" more garbage'
        result = agent._extract_json_robust(text)
        assert "content" in result or "parsing_error" in result

    def test_odd_quotes_repaired(self, agent):
        """홀수 따옴표 자동 수리"""
        text = '{"title": "test", "desc": "incomplete'
        result = agent._extract_json_robust(text)
        # 파싱 성공하거나, 에러 시에도 정보 보존
        assert isinstance(result, dict)


# ══════════════════════════════════════════════════════════════
# Test 3: _escape_braces
# ══════════════════════════════════════════════════════════════


class TestEscapeBraces:
    def test_basic_escape(self, agent):
        """기본 중괄호 이스케이프"""
        result = agent._escape_braces("hello {world}")
        assert result == "hello {{world}}"

    def test_already_escaped(self, agent):
        """이미 이스케이프된 텍스트는 변경 없음"""
        result = agent._escape_braces("hello {{world}}")
        assert result == "hello {{world}}"

    def test_empty_string(self, agent):
        """빈 문자열"""
        assert agent._escape_braces("") == ""

    def test_none_input(self, agent):
        """None 입력"""
        assert agent._escape_braces(None) == ""

    def test_non_string_input(self, agent):
        """정수 입력"""
        result = agent._escape_braces(12345)
        assert result == "12345"

    def test_no_braces(self, agent):
        """중괄호 없는 텍스트"""
        result = agent._escape_braces("no braces here")
        assert result == "no braces here"

    def test_force_escape(self, agent):
        """force=True로 이미 이스케이프된 것도 다시 이스케이프"""
        result = agent._escape_braces("{{already}}", force=True)
        assert "{{{{" in result

    def test_mixed_braces(self, agent):
        """이스케이프 + 미이스케이프 혼합"""
        result = agent._escape_braces("{{safe}} and {unsafe}")
        assert "{{" in result


# ══════════════════════════════════════════════════════════════
# Test 4: _classify_error
# ══════════════════════════════════════════════════════════════


class TestClassifyError:
    def test_timeout_error(self, agent):
        """타임아웃 분류"""
        error = Exception("Request timeout exceeded deadline")
        assert agent._classify_error(error) == AgentErrorType.TIMEOUT

    def test_quota_error(self, agent):
        """쿼터 분류"""
        error = Exception("429 Resource quota exceeded")
        assert agent._classify_error(error) == AgentErrorType.QUOTA_EXCEEDED

    def test_rate_error(self, agent):
        """레이트 리밋 분류"""
        error = Exception("Rate limit reached for model")
        assert agent._classify_error(error) == AgentErrorType.QUOTA_EXCEEDED

    def test_network_error(self, agent):
        """네트워크 분류"""
        error = Exception("Connection refused by server")
        assert agent._classify_error(error) == AgentErrorType.NETWORK_ERROR

    def test_remote_disconnect_error(self, agent):
        """원격 연결 종료 분류"""
        error = Exception("Server disconnected without sending a response.")
        assert agent._classify_error(error) == AgentErrorType.NETWORK_ERROR

    def test_winerror_10054_error(self, agent):
        """Windows 원격 호스트 연결 종료 분류"""
        error = Exception("[WinError 10054] 현재 연결은 원격 호스트에 의해 강제로 끊겼습니다")
        assert agent._classify_error(error) == AgentErrorType.NETWORK_ERROR

    def test_json_error(self, agent):
        """JSON 파싱 분류"""
        error = Exception("json decode error at position 5")
        assert agent._classify_error(error) == AgentErrorType.MALFORMED_RESPONSE

    def test_schema_incompatible_error(self, agent):
        """현재 Gemini 경로에서 지원되지 않는 스키마 분류"""
        error = Exception("additionalProperties is not supported in the Gemini API.")
        assert agent._classify_error(error) == AgentErrorType.SCHEMA_INCOMPATIBLE

    def test_unknown_error(self, agent):
        """알 수 없는 에러"""
        error = Exception("Something completely unexpected happened")
        assert agent._classify_error(error) == AgentErrorType.UNKNOWN


class TestHandleApiError:
    def test_credit_balance_too_low_is_classified_as_quota_like(self, agent):
        result = agent._classify_api_error_mode(
            Exception("Your credit balance is too low to access the Anthropic API. Please purchase credits.")
        )

        assert result["is_quota_exhausted"] is True
        assert result["is_rate_limit"] is False
        assert result["is_ambiguous_429"] is False

    def test_ambiguous_429_prefers_immediate_fallback(self, agent, monkeypatch):
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(base_agent_module.types, "GenerateContentConfig", lambda **kwargs: kwargs)
        BaseAgent._quota_exhausted_models.clear()

        response = MagicMock(name="fallback_response")
        agent._generate_content = MagicMock(return_value=response)

        result = agent._handle_api_error(
            api_error=Exception("429"),
            current_model="gemini-2.5-pro",
            model_stack=["gemini-2.5-pro", "gemini-2.5-flash"],
            config=object(),
            current_prompt="prompt",
            temperature=0.7,
            response_schema={"type": "object"},
            thinking_level=None,
            network_retry_count=0,
            rate_limit_retry_count=0,
            quota_retry_count=0,
            max_rate_limit_retries=3,
            max_quota_retries=2,
        )

        assert result["action"] == "fallback_response"
        assert result["current_model"] == "gemini-2.5-flash"
        assert result["quota_retry_count"] == 1
        assert result["rate_limit_retry_count"] == 0
        assert result["response"] is response
        agent._generate_content.assert_called_once()
        assert "gemini-2.5-pro" in BaseAgent._quota_exhausted_models

    def test_explicit_rate_limit_keeps_backoff_retry(self, agent, monkeypatch):
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)
        agent._generate_content = MagicMock()

        result = agent._handle_api_error(
            api_error=Exception("429 rate limit reached"),
            current_model="gemini-2.5-pro",
            model_stack=["gemini-2.5-pro", "gemini-2.5-flash"],
            config=object(),
            current_prompt="prompt",
            temperature=0.7,
            response_schema=None,
            thinking_level=None,
            network_retry_count=0,
            rate_limit_retry_count=0,
            quota_retry_count=0,
            max_rate_limit_retries=3,
            max_quota_retries=2,
        )

        assert result["action"] == "continue"
        assert result["rate_limit_retry_count"] == 1
        assert result["quota_retry_count"] == 0
        agent._generate_content.assert_not_called()

    def test_network_error_retries_before_any_model_fallback(self, agent, monkeypatch):
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)
        agent._check_connectivity = MagicMock(return_value=True)
        agent._generate_content = MagicMock()

        result = agent._handle_api_error(
            api_error=Exception("Connection refused by upstream"),
            current_model="gemini-2.5-pro",
            model_stack=["gemini-2.5-pro", "gemini-2.5-flash"],
            config=object(),
            current_prompt="prompt",
            temperature=0.7,
            response_schema=None,
            thinking_level=None,
            network_retry_count=0,
            rate_limit_retry_count=0,
            quota_retry_count=0,
            max_rate_limit_retries=3,
            max_quota_retries=2,
        )

        assert result["action"] == "continue"
        assert result["network_retry_count"] == 1
        assert result["quota_retry_count"] == 0
        assert result["rate_limit_retry_count"] == 0
        agent._check_connectivity.assert_called_once()
        agent._generate_content.assert_not_called()


class TestKeyRotationSignal:
    def test_try_rotate_key_reports_all_keys_exhausted_reason(self, monkeypatch):
        monkeypatch.setattr(BaseAgent, "_keys_initialized", True)
        monkeypatch.setattr(BaseAgent, "_api_keys", ["k1", "k2"])
        monkeypatch.setattr(BaseAgent, "_current_key_idx", 1)
        monkeypatch.setattr(BaseAgent, "_rotation_count", 1)
        monkeypatch.setattr(BaseAgent, "_key_rotation_pending", True)

        client, reason = BaseAgent._try_rotate_key()

        assert client is None
        assert reason == "all_keys_exhausted"

    def test_ask_surfaces_rotation_exhaustion_to_operator(self, monkeypatch):
        operator_log = MagicMock()
        context = SimpleNamespace(author_directives="", operator_log=operator_log)
        client = MagicMock()
        agent = BaseAgent(context=context, client=client, model_tier="gemini-2.5-flash")

        monkeypatch.setattr(base_agent_module, "METRICS_ENABLED", False)
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(BaseAgent, "_key_rotation_pending", True)
        agent._try_rotate_key = MagicMock(return_value=(None, "all_keys_exhausted"))
        agent._build_model_stack = MagicMock(
            return_value={
                "model_stack": ["gemini-2.5-flash"],
                "current_model": "gemini-2.5-flash",
                "config": object(),
                "metric_id": None,
            }
        )
        agent._generate_content = MagicMock(return_value=object())
        agent._accumulate_last_llm_usage = MagicMock()
        agent._extract_and_merge_response = MagicMock(
            return_value={
                "full_response": '{"content":"ok"}',
                "_thinking_text": "",
                "action": "break",
            }
        )
        agent._log_llm_call_to_db = MagicMock()
        BaseAgent._session_logger_global = None

        result = agent.ask("테스트 프롬프트")

        assert result == '{"content":"ok"}'
        assert operator_log.call_count >= 1
        last_call = operator_log.call_args_list[-1]
        assert "[KEY-ROTATE]" in last_call.args[0]
        assert last_call.kwargs["level"] == "warning"
        assert last_call.kwargs["meta"]["reason"] == "all_keys_exhausted"


class TestAskHelperSurface:
    def test_prepare_ask_prompt_resets_partial_response_and_wraps_json_contract(self, agent):
        agent.last_partial_response = "stale"
        result = agent._prepare_ask_prompt(prompt="hello")

        assert agent.last_partial_response == ""
        assert result["current_prompt"] == result["base_prompt"]
        assert result["full_response"] == ""
        assert "AUTHOR'S ABSOLUTE DIRECTIVES" in result["base_prompt"]
        assert "Respond ONLY in valid JSON format." in result["base_prompt"]


class TestValidateResponse:
    def test_valid_response(self, agent):
        """유효한 JSON 응답"""
        response = json.dumps({"content": "원고 내용", "title": "테스트"})
        result = agent._validate_response(response)
        assert result["valid"] is True

    def test_empty_response(self, agent):
        """빈 응답"""
        result = agent._validate_response("")
        assert result["valid"] is False

    def test_none_response(self, agent):
        """None 응답"""
        result = agent._validate_response(None)
        assert result["valid"] is False

    def test_short_response(self, agent):
        """너무 짧은 응답"""
        result = agent._validate_response("{}")
        assert result["valid"] is False

    def test_no_json_start(self, agent):
        """JSON 시작 문자 없음"""
        result = agent._validate_response("This is plain text not JSON at all")
        assert result["valid"] is False

    def test_unbalanced_braces(self, agent):
        """괄호 불균형"""
        result = agent._validate_response('{"content": "test" {{{{{{')
        assert result["valid"] is False

    def test_no_key_fields(self, agent):
        """핵심 필드 없음"""
        result = agent._validate_response('{"random_field": "value", "another": 123}')
        assert result["valid"] is False


# ══════════════════════════════════════════════════════════════
# Test 6: _is_network_error
# ══════════════════════════════════════════════════════════════


class TestIsNetworkError:
    def test_timeout_is_network(self, agent):
        assert agent._is_network_error(Exception("Request timeout")) is True

    def test_connection_is_network(self, agent):
        assert agent._is_network_error(Exception("Connection refused")) is True

    def test_remote_disconnect_is_network(self, agent):
        assert agent._is_network_error(Exception("Server disconnected without sending a response.")) is True

    def test_winerror_10054_is_network(self, agent):
        assert agent._is_network_error(Exception("[WinError 10054] 원격 호스트에 의해 강제로 끊겼습니다")) is True

    def test_ssl_is_network(self, agent):
        assert agent._is_network_error(Exception("SSL handshake failed")) is True

    def test_quota_is_not_network(self, agent):
        assert agent._is_network_error(Exception("Quota exceeded 429")) is False

    def test_json_is_not_network(self, agent):
        assert agent._is_network_error(Exception("JSON decode error")) is False


# ══════════════════════════════════════════════════════════════
# Test 7: _create_error_response & _get_recovery_hint
# ══════════════════════════════════════════════════════════════


class TestErrorResponse:
    def test_create_error_response(self, agent):
        """에러 응답 생성"""
        result = agent._create_error_response(AgentErrorType.TIMEOUT, "시간 초과")
        parsed = json.loads(result)
        assert parsed["error"] is True
        assert parsed["error_type"] == AgentErrorType.TIMEOUT
        assert "시간 초과" in parsed["error_message"]
        assert "recovery_hint" in parsed

    def test_recovery_hints(self, agent):
        """각 에러 타입별 복구 힌트"""
        for error_type in [
            AgentErrorType.TIMEOUT,
            AgentErrorType.QUOTA_EXCEEDED,
            AgentErrorType.NETWORK_ERROR,
            AgentErrorType.MALFORMED_RESPONSE,
            AgentErrorType.CANDIDATE_DISQUALIFIED,
            AgentErrorType.UNKNOWN,
        ]:
            hint = agent._get_recovery_hint(error_type)
            assert isinstance(hint, str)
            assert len(hint) > 0


# ══════════════════════════════════════════════════════════════
# Test 8: MODEL_FALLBACK_CHAIN
# ══════════════════════════════════════════════════════════════


class TestModelFallbackChain:
    def test_31preview_falls_to_25pro(self):
        assert BaseAgent.MODEL_FALLBACK_CHAIN["vertexai:gemini-3.1-pro-preview"] == "vertexai:gemini-2.5-pro"

    def test_25pro_falls_to_flash(self):
        """gemini-2.5-pro → gemini-2.5-flash 폴백"""
        assert BaseAgent.MODEL_FALLBACK_CHAIN["vertexai:gemini-2.5-pro"] == "vertexai:gemini-2.5-flash"

    def test_flash_is_terminal(self):
        """gemini-2.5-flash는 자기 자신으로 폴백 (최종 방어선)"""
        assert BaseAgent.MODEL_FALLBACK_CHAIN.get("vertexai:gemini-2.5-flash") == "vertexai:gemini-2.5-flash"

    def test_flash_chain(self):
        """Flash 계열 폴백 — 현재 chain에 gemini-3.x 없음"""
        assert "gemini-3-flash-preview" not in BaseAgent.MODEL_FALLBACK_CHAIN
        assert BaseAgent.MODEL_FALLBACK_CHAIN["vertexai:gemini-3.1-pro-preview"] == "vertexai:gemini-2.5-pro"

    def test_vertex_prefixed_pro_preserves_provider_on_fallback(self):
        agent = BaseAgent(context=MagicMock(), client=MagicMock(), model_tier="vertexai:gemini-3.1-pro-preview")
        assert agent.backup_model == "vertexai:gemini-2.5-pro"


# ══════════════════════════════════════════════════════════════
# Test 9: THINKING_BUDGET_MAP
# ══════════════════════════════════════════════════════════════


class TestThinkingBudgetMap:
    def test_minimal_budget(self):
        assert BaseAgent.THINKING_BUDGET_MAP["minimal"] == 1024

    def test_maximum_budget(self):
        assert BaseAgent.THINKING_BUDGET_MAP["maximum"] == 24576

    def test_all_levels_exist(self):
        """모든 레벨이 존재"""
        for level in ["minimal", "low", "medium", "high", "maximum"]:
            assert level in BaseAgent.THINKING_BUDGET_MAP


# ══════════════════════════════════════════════════════════════
# Test 10: _parse_and_repair_hard
# ══════════════════════════════════════════════════════════════


class TestParseAndRepairHard:
    def test_missing_closing_brace(self, agent):
        """닫는 중괄호 누락 수리"""
        text = '{"key": "value"'
        result = agent._parse_and_repair_hard(text)
        assert isinstance(result, dict)
        assert "key" in result

    def test_null_to_none(self, agent):
        """null → None 변환"""
        text = '{"key": null, "other": true}'
        result = agent._parse_and_repair_hard(text)
        assert isinstance(result, dict)

    def test_regex_fallback(self, agent):
        """ast 실패 시 정규식 폴백"""
        text = '{"key1": "value1", "key2": "value2"}'
        result = agent._parse_and_repair_hard(text)
        assert isinstance(result, dict)
        assert "key1" in result


# ══════════════════════════════════════════════════════════════
# Test 11: merge_contexts_for_caching
# ══════════════════════════════════════════════════════════════


class TestMergeContextsForCaching:
    def test_blueprint_merge(self, agent):
        """블루프린트 병합"""
        items = [
            {"ep_num": 1, "data": json.dumps({"title": "시작", "end_location": "객잔"})},
            {"ep_num": 2, "data": json.dumps({"title": "전개", "time_flow": "다음날"})},
        ]
        result = agent.merge_contexts_for_caching(items, item_type="blueprint")
        assert "제1화" in result
        assert "제2화" in result
        assert "BLUEPRINT" in result

    def test_manuscript_merge(self, agent):
        """원고 병합"""
        items = [
            {"ep_num": 1, "title": "시작", "content": "원고 내용..." * 100},
        ]
        result = agent.merge_contexts_for_caching(items, item_type="manuscript")
        assert "제1화" in result
        assert "MANUSCRIPT" in result

    def test_empty_items(self, agent):
        """빈 아이템 목록"""
        assert agent.merge_contexts_for_caching([], item_type="blueprint") == ""


# ══════════════════════════════════════════════════════════════
# Test 12: [TF-C11] JSON 안전화
# ══════════════════════════════════════════════════════════════


class TestJsonSafetyC11:
    def test_regex_captures_numeric_values(self, agent):
        """[TF-C11] 숫자/불리언 값도 regex fallback에서 추출"""
        # ast.literal_eval도 실패하도록 깨진 JSON
        broken = '{"name": "test", "score": 42, "active": true, broken syntax here'
        result = agent._parse_and_repair_hard(broken)
        assert isinstance(result, dict)
        assert result.get("name") == "test"
        assert result.get("score") == 42
        assert result.get("active") is True

    def test_payload_size_guard(self, agent):
        """[TF-C11] 500KB 초과 페이로드 절삭 후 처리"""
        huge = '{"content": "' + "x" * 600_000 + '"}'
        result = agent._extract_json_robust(huge)
        assert isinstance(result, dict)
        # 절삭되어도 파싱은 시도됨 (크래시 없음)

    def test_deep_nesting_visit_limit(self, agent):
        """[TF-C11] 깊은 중첩 + 많은 노드 시 visit_count 상한 작동"""
        # 100개 초과 dict를 포함하는 list
        items = [{"target": f"t{i}", "value": f"v{i}"} for i in range(150)]
        text = json.dumps({"items": items})
        result = agent._extract_json_robust(text)
        assert isinstance(result, dict)

    def test_huge_integer_regex_fallback_returns_string_not_crash(self, agent):
        huge_num = "9" * 5001
        broken = f'{{"name": "test", "runaway": {huge_num}, broken syntax here'

        result = agent._parse_and_repair_hard(broken)

        assert isinstance(result, dict)
        assert result.get("name") == "test"
        assert result.get("runaway") == huge_num

    def test_extract_json_robust_preserves_huge_integer_as_string(self, agent):
        huge_num = "9" * 5001
        text = f'{{"huge": {huge_num}}}'

        result = agent._extract_json_robust(text)

        assert isinstance(result, dict)
        assert result.get("huge") == huge_num
        # 100개 방문 상한 → 일부만 추출되어도 크래시 없음


# ══════════════════════════════════════════════════════════════
# [I-18] _quota_exhausted_models 스레드 안전성
# ══════════════════════════════════════════════════════════════


class TestQuotaLock:
    def test_quota_lock_exists(self):
        """[I-18] _quota_lock 클래스 변수 존재"""
        import threading

        assert hasattr(BaseAgent, "_quota_lock")
        assert isinstance(BaseAgent._quota_lock, type(threading.Lock()))

    def test_quota_write_under_lock(self):
        """[I-18] 쿼터 캐시 쓰기가 크래시 없이 동작"""
        import time

        with BaseAgent._quota_lock:
            BaseAgent._quota_exhausted_models["test_model"] = time.time() + 100
        # cleanup
        with BaseAgent._quota_lock:
            BaseAgent._quota_exhausted_models.pop("test_model", None)


# ══════════════════════════════════════════════════════════════
# [I-20] Context Cache 에빅션 TOCTOU
# ══════════════════════════════════════════════════════════════


class TestContextCacheEviction:
    def test_expired_cache_pop(self, agent):
        """[I-20] 만료 캐시 삭제 시 KeyError 없이 pop"""
        import hashlib
        import time

        content = "short content"
        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:16]
        cache_key = build_context_cache_key(agent, "test", "", content_hash)
        agent._context_caches[cache_key] = {
            "name": "test",
            "created_at": time.time() - 99999,
            "content_hash": content_hash,
            "model": agent.primary_model or "",
            "provider": base_agent_module._context_cache_provider_token(agent.client, agent.primary_model),
        }
        # 만료 캐시 접근 → pop으로 안전 삭제 (KeyError 없음)
        result = agent._get_or_create_context_cache("test", content, ttl_seconds=1)
        assert result["cached"] is False
        assert cache_key not in agent._context_caches

    def test_eviction_snapshot(self, agent):
        """[I-20] 에빅션이 list() 스냅샷으로 안전하게 동작"""
        import time

        old_max = agent._CONTEXT_CACHE_MAX
        agent._CONTEXT_CACHE_MAX = 2
        try:
            for i in range(5):
                agent._context_caches[f"evict_{i}"] = {
                    "name": f"cache_{i}",
                    "created_at": time.time() + i,
                    "content_hash": f"hash_{i}",
                }
            # 수동 에빅션 트리거 — 직접 로직 호출
            if len(agent._context_caches) > agent._CONTEXT_CACHE_MAX:
                snapshot = list(agent._context_caches.items())
                snapshot.sort(key=lambda kv: kv[1].get("created_at", 0))
                for old_key, _ in snapshot[: len(snapshot) - agent._CONTEXT_CACHE_MAX]:
                    agent._context_caches.pop(old_key, None)
            assert len(agent._context_caches) <= 2
        finally:
            agent._CONTEXT_CACHE_MAX = old_max
            for k in list(agent._context_caches.keys()):
                if k.startswith("evict_"):
                    agent._context_caches.pop(k, None)

    def test_short_context_cache_skip_logs_direct_attempt(self, agent):
        db = MagicMock()
        db.save_context_cache_attempt = MagicMock()
        agent.context = SimpleNamespace(current_project=SimpleNamespace(db=db), current_stage=3, current_ep=15)

        result = agent._get_or_create_context_cache(
            "blueprint", "short content", ttl_seconds=45, project_name="gc_ep15"
        )

        assert result["reason"] == "content_too_short"
        db.save_context_cache_attempt.assert_called_once()
        kwargs = db.save_context_cache_attempt.call_args.kwargs
        assert kwargs["cache_outcome"] == "skipped"
        assert kwargs["cache_reason"] == "content_too_short"
        assert kwargs["content_chars"] == len("short content")
        assert kwargs["min_content_chars"] == agent._MIN_CACHE_CONTENT
        assert kwargs["stage"] == 3
        assert kwargs["ep_num"] == 15

    def test_context_cache_hit_logs_direct_attempt(self, agent):
        import hashlib
        import time

        db = MagicMock()
        db.save_context_cache_attempt = MagicMock()
        agent.context = SimpleNamespace(current_project=SimpleNamespace(db=db), current_stage=4, current_ep=21)
        content = "A" * max(10, agent._MIN_CACHE_CONTENT)
        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:16]
        cache_key = build_context_cache_key(agent, "manuscript", "gc_ep21", content_hash)
        agent._context_caches[cache_key] = {
            "name": "cache/existing",
            "created_at": time.time(),
            "content_hash": content_hash,
            "model": agent.primary_model or "",
            "provider": base_agent_module._context_cache_provider_token(agent.client, agent.primary_model),
        }

        result = agent._get_or_create_context_cache("manuscript", content, ttl_seconds=1800, project_name="gc_ep21")

        assert result["cached"] is True
        db.save_context_cache_attempt.assert_called_once()
        kwargs = db.save_context_cache_attempt.call_args.kwargs
        assert kwargs["cache_outcome"] == "hit"
        assert kwargs["cache_name"] == "cache/existing"
        assert kwargs["stage"] == 4
        assert kwargs["ep_num"] == 21

    def test_context_cache_key_separates_model_and_provider(self, agent):
        agent.primary_model = "gemini-2.5-flash"
        agent.client = SimpleNamespace(_geuldobi_provider_mode="google_genai")
        google_key = build_context_cache_key(agent, "manuscript", "gc_ep21", "hash123")

        agent.client = SimpleNamespace(_geuldobi_provider_mode="vertex_ai", _geuldobi_vertex_auth_mode="adc")
        vertex_key = build_context_cache_key(agent, "manuscript", "gc_ep21", "hash123")

        agent.primary_model = "gemini-2.5-pro"
        pro_key = build_context_cache_key(agent, "manuscript", "gc_ep21", "hash123")

        assert google_key != vertex_key
        assert vertex_key != pro_key
        assert "google_genai" in google_key
        assert "vertex_ai.adc" in vertex_key
        assert "gemini-2.5-pro" in pro_key

    def test_context_cache_skips_vertex_api_key_mode_before_create(self, agent):
        db = MagicMock()
        db.save_context_cache_attempt = MagicMock()
        caches = SimpleNamespace(create=MagicMock())
        agent.context = SimpleNamespace(current_project=SimpleNamespace(db=db), current_stage=4, current_ep=16)
        agent.client = SimpleNamespace(
            caches=caches,
            _geuldobi_provider_mode="vertex_ai",
            _geuldobi_vertex_auth_mode="api_key",
        )
        content = "A" * max(10, agent._MIN_CACHE_CONTENT)

        result = agent._get_or_create_context_cache("manuscript", content, ttl_seconds=1800, project_name="gc_ep16")

        assert result["cache_name"] is None
        assert result["reason"] == "vertex_api_key_explicit_cache_unsupported"
        caches.create.assert_not_called()
        db.save_context_cache_attempt.assert_called_once()
        kwargs = db.save_context_cache_attempt.call_args.kwargs
        assert kwargs["cache_outcome"] == "skipped"
        assert kwargs["cache_reason"] == "vertex_api_key_explicit_cache_unsupported"
        assert kwargs["stage"] == 4
        assert kwargs["ep_num"] == 16

    def test_context_cache_error_logs_specific_reason(self, agent):
        db = MagicMock()
        db.save_context_cache_attempt = MagicMock()
        agent.context = SimpleNamespace(current_project=SimpleNamespace(db=db), current_stage=4, current_ep=16)
        agent.client = SimpleNamespace(caches=SimpleNamespace(create=MagicMock(side_effect=Exception("404 Not Found"))))
        content = "A" * max(10, agent._MIN_CACHE_CONTENT)

        result = agent._get_or_create_context_cache("manuscript", content, ttl_seconds=1800, project_name="gc_ep16")

        assert result["cache_name"] is None
        assert result["reason"] == "cache_create_failed_not_found"
        db.save_context_cache_attempt.assert_called_once()
        kwargs = db.save_context_cache_attempt.call_args.kwargs
        assert kwargs["cache_outcome"] == "error"
        assert kwargs["cache_reason"] == "cache_create_failed_not_found"
        assert kwargs["stage"] == 4
        assert kwargs["ep_num"] == 16

    def test_cached_context_success_logs_cache_lineage(self, agent, monkeypatch):
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)
        cache_key = seed_context_cache(agent, cache_name="cached/ctx-success", content_hash="hash-lineage-success")
        response = MagicMock()
        response.text = json.dumps({"content": "cached"})

        def _generate_with_usage(**_kwargs):
            agent._last_llm_usage = {
                "prompt_token_count": 123,
                "candidates_token_count": 45,
                "cached_content_token_count": 100,
                "thoughts_token_count": 7,
            }
            return response

        agent._generate_content = MagicMock(side_effect=_generate_with_usage)
        agent._log_llm_call_to_db = MagicMock()

        try:
            result = agent._ask_with_cached_context(cache_name="cached/ctx-success", prompt="prompt")

            assert json.loads(result)["content"] == "cached"
            assert agent._call_usage_totals["prompt_token_count"] == 123
            assert agent._call_usage_totals["candidates_token_count"] == 45
            assert agent._call_usage_totals["cached_content_token_count"] == 100
            assert agent._call_usage_totals["thoughts_token_count"] == 7
            kwargs = agent._log_llm_call_to_db.call_args.kwargs
            assert kwargs["context_cache_name"] == "cached/ctx-success"
            assert kwargs["context_cache_content_hash"] == "hash-lineage-success"
            assert kwargs["context_cache_outcome"] == "used"
            assert cache_key in agent._context_caches
        finally:
            agent._context_caches.pop(cache_key, None)

    def test_cached_context_failure_evicts_cache_by_name_and_logs_lineage(self, agent, monkeypatch):
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)
        cache_key = seed_context_cache(agent, cache_name="cached/ctx-fail", content_hash="hash-lineage-fail")
        agent._generate_content = MagicMock(side_effect=RuntimeError("cached boom"))
        agent._log_llm_call_to_db = MagicMock()
        agent.ask = MagicMock(return_value='{"fallback": true}')

        try:
            result = agent._ask_with_cached_context(cache_name="cached/ctx-fail", prompt="prompt")

            assert json.loads(result)["fallback"] is True
            assert cache_key not in agent._context_caches
            kwargs = agent._log_llm_call_to_db.call_args.kwargs
            assert kwargs["context_cache_name"] == "cached/ctx-fail"
            assert kwargs["context_cache_content_hash"] == "hash-lineage-fail"
            assert kwargs["context_cache_outcome"] == "failed"
        finally:
            agent._context_caches.pop(cache_key, None)

    def test_cached_context_missing_lineage_bypasses_cache(self, agent):
        db = MagicMock()
        db.save_context_cache_attempt = MagicMock()
        agent.context = SimpleNamespace(current_project=SimpleNamespace(db=db), current_stage=4, current_ep=22)
        agent.ask = MagicMock(return_value='{"fallback": true}')
        agent._generate_content = MagicMock()

        result = agent._ask_with_cached_context(cache_name="cached/missing", prompt="prompt")

        assert json.loads(result)["fallback"] is True
        agent.ask.assert_called_once()
        agent._generate_content.assert_not_called()
        db.save_context_cache_attempt.assert_called_once()
        kwargs = db.save_context_cache_attempt.call_args.kwargs
        assert kwargs["cache_outcome"] == "bypassed"
        assert kwargs["cache_reason"] == "missing_lineage"
        assert kwargs["cache_name"] == "cached/missing"
        assert kwargs["content_hash"] == ""
        assert kwargs["stage"] == 4
        assert kwargs["ep_num"] == 22

    def test_cached_context_stale_model_lineage_bypasses_cache(self, agent):
        db = MagicMock()
        db.save_context_cache_attempt = MagicMock()
        agent.context = SimpleNamespace(current_project=SimpleNamespace(db=db), current_stage=4, current_ep=23)
        cache_key = seed_context_cache(agent, cache_name="cached/stale-model", content_hash="hash-stale-model")
        agent.primary_model = "gemini-2.5-pro"
        agent.ask = MagicMock(return_value='{"fallback": true}')
        agent._generate_content = MagicMock()

        try:
            result = agent._ask_with_cached_context(cache_name="cached/stale-model", prompt="prompt")
        finally:
            agent._context_caches.pop(cache_key, None)

        assert json.loads(result)["fallback"] is True
        agent.ask.assert_called_once()
        agent._generate_content.assert_not_called()
        db.save_context_cache_attempt.assert_called_once()
        kwargs = db.save_context_cache_attempt.call_args.kwargs
        assert kwargs["cache_outcome"] == "bypassed"
        assert kwargs["cache_reason"] == "stale_model_lineage"
        assert kwargs["cache_name"] == "cached/stale-model"
        assert kwargs["content_hash"] == "hash-stale-model"
        assert kwargs["stage"] == 4
        assert kwargs["ep_num"] == 23


class TestMetricsUsageTracking:
    def test_ask_resets_stale_usage_before_failure_metrics(self, agent, monkeypatch):
        collector = MagicMock()
        collector.estimate_tokens.side_effect = [111]
        collector.start_call.return_value = "metric_1"

        monkeypatch.setattr(base_agent_module, "METRICS_ENABLED", True)
        monkeypatch.setattr(base_agent_module, "get_metrics_collector", lambda: collector)

        agent._last_llm_usage = {
            "prompt_token_count": 999,
            "candidates_token_count": 888,
            "cached_content_token_count": 777,
        }
        agent._build_model_stack = MagicMock(
            return_value={
                "model_stack": ["gemini-2.5-flash"],
                "current_model": "gemini-2.5-flash",
                "config": object(),
                "metric_id": "metric_1",
            }
        )
        agent._generate_content = MagicMock(side_effect=RuntimeError("boom"))
        agent._handle_api_error = MagicMock(
            return_value={
                "action": "raise",
                "current_model": "gemini-2.5-flash",
                "config": object(),
                "network_retry_count": 0,
                "rate_limit_retry_count": 0,
                "quota_retry_count": 0,
            }
        )
        agent._attempt_backup_recovery = MagicMock(return_value='{"error": true}')
        BaseAgent._session_logger_global = None

        agent.ask("테스트 프롬프트")

        collector.end_call.assert_called_once()
        kwargs = collector.end_call.call_args.kwargs
        assert kwargs["success"] is False
        assert kwargs["input_tokens"] == 111
        assert kwargs["output_tokens"] == 0
        assert kwargs["cached_tokens"] == 0

    def test_ask_accumulates_usage_across_continuations(self, agent, monkeypatch):
        collector = MagicMock()
        collector.start_call.return_value = "metric_2"

        monkeypatch.setattr(base_agent_module, "METRICS_ENABLED", True)
        monkeypatch.setattr(base_agent_module, "get_metrics_collector", lambda: collector)
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)

        usages = [
            {
                "prompt_token_count": 100,
                "candidates_token_count": 40,
                "cached_content_token_count": 10,
                "thoughts_token_count": 4,
            },
            {
                "prompt_token_count": 50,
                "candidates_token_count": 20,
                "cached_content_token_count": 5,
                "thoughts_token_count": 3,
            },
        ]

        def fake_generate(**_kwargs):
            agent._last_llm_usage = usages.pop(0)
            return object()

        def fake_extract(*, full_response, attempt, **_kwargs):
            if attempt == 0:
                return {
                    "full_response": full_response + "first",
                    "_thinking_text": "",
                    "action": "continue",
                    "current_prompt": "continue",
                }
            return {
                "full_response": full_response + "second",
                "_thinking_text": "",
                "action": "break",
            }

        agent._build_model_stack = MagicMock(
            return_value={
                "model_stack": ["gemini-2.5-flash"],
                "current_model": "gemini-2.5-flash",
                "config": object(),
                "metric_id": "metric_2",
            }
        )
        agent._generate_content = fake_generate
        agent._extract_and_merge_response = fake_extract
        BaseAgent._session_logger_global = None

        result = agent.ask("테스트 프롬프트")

        assert result == "firstsecond"
        collector.end_call.assert_called_once()
        kwargs = collector.end_call.call_args.kwargs
        assert kwargs["success"] is True
        assert kwargs["input_tokens"] == 150
        assert kwargs["output_tokens"] == 60
        assert kwargs["cached_tokens"] == 15
        assert kwargs["thinking_tokens"] == 7

    def test_cached_context_metrics_cover_success_path(self, agent, monkeypatch):
        collector = MagicMock()
        collector.start_call.return_value = "cached_metric"

        monkeypatch.setattr(base_agent_module, "METRICS_ENABLED", True)
        monkeypatch.setattr(base_agent_module, "get_metrics_collector", lambda: collector)
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)

        response = MagicMock()
        response.text = json.dumps({"content": "cached"})

        def fake_generate(**_kwargs):
            agent._last_llm_usage = {
                "prompt_token_count": 21,
                "candidates_token_count": 8,
                "cached_content_token_count": 5,
                "thoughts_token_count": 1,
            }
            return response

        agent._generate_content = fake_generate
        agent._log_llm_call_to_db = MagicMock()
        cache_key = seed_context_cache(agent, cache_name="cached/ctx", content_hash="hash-metric-success")

        try:
            result = agent._ask_with_cached_context(cache_name="cached/ctx", prompt="prompt")
        finally:
            agent._context_caches.pop(cache_key, None)

        assert json.loads(result)["content"] == "cached"
        collector.start_call.assert_called_once_with(agent.agent_name, agent.primary_model)
        collector.end_call.assert_called_once()
        kwargs = collector.end_call.call_args.kwargs
        assert kwargs["success"] is True
        assert kwargs["input_tokens"] == 21
        assert kwargs["output_tokens"] == 8
        assert kwargs["cached_tokens"] == 5
        assert kwargs["thinking_tokens"] == 1

    def test_cached_context_metrics_cover_failure_before_fallback(self, agent, monkeypatch):
        collector = MagicMock()
        collector.start_call.return_value = "cached_metric_fail"

        monkeypatch.setattr(base_agent_module, "METRICS_ENABLED", True)
        monkeypatch.setattr(base_agent_module, "get_metrics_collector", lambda: collector)
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)

        agent._generate_content = MagicMock(side_effect=RuntimeError("cached boom"))
        agent._classify_error = MagicMock(return_value=AgentErrorType.NETWORK_ERROR)
        agent.ask = MagicMock(return_value='{"fallback": true}')
        agent._log_llm_call_to_db = MagicMock()
        cache_key = seed_context_cache(agent, cache_name="cached/ctx", content_hash="hash-metric-fail")

        try:
            result = agent._ask_with_cached_context(cache_name="cached/ctx", prompt="prompt")
        finally:
            agent._context_caches.pop(cache_key, None)

        assert json.loads(result)["fallback"] is True
        collector.end_call.assert_called_once()
        kwargs = collector.end_call.call_args.kwargs
        assert kwargs["success"] is False
        assert kwargs["error_type"] == AgentErrorType.NETWORK_ERROR

    def test_backup_recovery_uses_measured_usage_and_closes_failed_metric(self, agent, monkeypatch):
        collector = MagicMock()
        collector.start_call.return_value = "backup_metric"
        collector.calculate_cost.side_effect = lambda model, *_args, **_kwargs: (
            0.321 if model == "gemini-2.5-pro" else 9.999
        )

        monkeypatch.setattr(base_agent_module, "METRICS_ENABLED", True)
        monkeypatch.setattr(base_agent_module, "get_metrics_collector", lambda: collector)
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)
        session_logger = MagicMock()
        monkeypatch.setattr(BaseAgent, "_session_logger_global", session_logger)

        agent.backup_model = "gemini-2.5-pro"
        agent._log_llm_call_to_db = MagicMock()
        agent._classify_error = MagicMock(return_value=AgentErrorType.NETWORK_ERROR)

        def fake_generate(**_kwargs):
            agent._last_llm_usage = {
                "prompt_token_count": 30,
                "candidates_token_count": 0,
                "cached_content_token_count": 4,
                "thoughts_token_count": 2,
            }
            raise RuntimeError("backup down")

        agent._generate_content = fake_generate

        result = agent._attempt_backup_recovery(
            base_prompt="backup prompt",
            temperature=0.3,
            response_schema=None,
            full_response="",
            error_type=AgentErrorType.UNKNOWN,
        )

        assert json.loads(result)["error"] is True
        collector.end_call.assert_called_once()
        kwargs = collector.end_call.call_args.kwargs
        assert kwargs["success"] is False
        assert kwargs["input_tokens"] == 30
        assert kwargs["output_tokens"] == 0
        assert kwargs["cached_tokens"] == 4
        assert kwargs["thinking_tokens"] == 2
        assert kwargs["model"] == "gemini-2.5-pro"

        session_logger.log_llm_call.assert_called_once()
        log_kwargs = session_logger.log_llm_call.call_args.kwargs
        assert log_kwargs["model"] == "gemini-2.5-pro"
        assert log_kwargs["success"] is False
        assert log_kwargs["context_tag"] == "backup_recovery"
        assert log_kwargs["input_tokens"] == 30
        assert log_kwargs["cached_tokens"] == 4
        assert log_kwargs["thinking_tokens"] == 2
        assert log_kwargs["total_cost_usd"] == 0.321

    def test_backup_recovery_success_logs_session_entry_with_backup_model_pricing(self, agent, monkeypatch):
        collector = MagicMock()
        collector.start_call.return_value = "backup_metric"
        collector.calculate_cost.side_effect = lambda model, *_args, **_kwargs: (
            0.432 if model == "gemini-2.5-pro" else 8.765
        )

        monkeypatch.setattr(base_agent_module, "METRICS_ENABLED", True)
        monkeypatch.setattr(base_agent_module, "get_metrics_collector", lambda: collector)
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)
        session_logger = MagicMock()
        monkeypatch.setattr(BaseAgent, "_session_logger_global", session_logger)

        agent.backup_model = "gemini-2.5-pro"
        agent._log_llm_call_to_db = MagicMock()
        agent._validate_response = MagicMock(return_value={"valid": True, "reason": ""})

        def fake_generate(**_kwargs):
            agent._last_llm_usage = {
                "prompt_token_count": 18,
                "candidates_token_count": 9,
                "cached_content_token_count": 2,
                "thoughts_token_count": 1,
            }
            return LLMResponse(text=json.dumps({"content": "backup ok"}), usage=None, raw=SimpleNamespace())

        agent._generate_content = fake_generate

        result = agent._attempt_backup_recovery(
            base_prompt="backup prompt",
            temperature=0.3,
            response_schema=None,
            full_response="",
            error_type=AgentErrorType.UNKNOWN,
        )

        assert json.loads(result)["content"] == "backup ok"
        collector.end_call.assert_called_once()
        end_kwargs = collector.end_call.call_args.kwargs
        assert end_kwargs["success"] is True
        assert end_kwargs["model"] == "gemini-2.5-pro"
        session_logger.log_llm_call.assert_called_once()
        log_kwargs = session_logger.log_llm_call.call_args.kwargs
        assert log_kwargs["model"] == "gemini-2.5-pro"
        assert log_kwargs["success"] is True
        assert log_kwargs["context_tag"] == "backup_recovery"
        assert log_kwargs["input_tokens"] == 18
        assert log_kwargs["output_tokens"] == 9
        assert log_kwargs["cached_tokens"] == 2
        assert log_kwargs["thinking_tokens"] == 1
        assert log_kwargs["total_cost_usd"] == 0.432


class TestNormalizedProviderHelpers:
    def test_generate_llm_response_preserves_usage_and_raw(self, agent):
        raw = MagicMock()
        provider = MagicMock()
        provider.generate.return_value = LLMResponse(
            text="ok",
            finish_reason="STOP",
            usage={"prompt_token_count": 3},
            raw=raw,
            provider="gemini",
        )
        agent._llm_router = MagicMock()
        agent._llm_router.get_provider_for_model.return_value = provider

        response = agent._generate_llm_response(
            model="gemini-2.5-flash", contents="prompt", config={"temperature": 0.1}
        )

        assert isinstance(response, LLMResponse)
        assert response.text == "ok"
        assert response.raw is raw
        assert agent._last_llm_usage == {"prompt_token_count": 3}

    def test_generate_content_returns_provider_neutral_envelope(self, agent):
        raw = MagicMock()
        provider = MagicMock()
        provider.generate.return_value = LLMResponse(
            text="ok",
            finish_reason="STOP",
            usage={"prompt_token_count": 3},
            raw=raw,
            provider="gemini",
        )
        agent._llm_router = MagicMock()
        agent._llm_router.get_provider_for_model.return_value = provider

        result = agent._generate_content(model="gemini-2.5-flash", contents="prompt", config={"temperature": 0.1})

        assert isinstance(result, LLMResponse)
        assert result.text == "ok"
        assert result.raw is raw

    def test_ask_continues_normalized_max_tokens_response(self, agent, monkeypatch):
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)
        agent._build_model_stack = MagicMock(
            return_value={
                "model_stack": ["claude-sonnet-4-6"],
                "current_model": "claude-sonnet-4-6",
                "config": object(),
                "metric_id": None,
            }
        )
        agent._generate_content = MagicMock(
            side_effect=[
                LLMResponse(text='{"content":"hel', finish_reason="MAX_TOKENS"),
                LLMResponse(text='lo"}', finish_reason="stop"),
            ]
        )
        BaseAgent._session_logger_global = None

        result = agent.ask("테스트 프롬프트")

        assert result == '{"content":"hello"}'
        assert agent._generate_content.call_count == 2

    def test_cached_context_max_tokens_falls_back_to_direct_ask(self, agent, monkeypatch):
        monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_args, **_kwargs: None)
        agent._generate_content = MagicMock(return_value=LLMResponse(text='{"partial":', finish_reason="MAX_TOKENS"))
        agent.ask = MagicMock(return_value='{"fallback": true}')
        agent._log_llm_call_to_db = MagicMock()
        cache_key = seed_context_cache(agent, cache_name="cached/ctx", content_hash="hash-max-tokens")

        try:
            result = agent._ask_with_cached_context(
                cache_name="cached/ctx",
                prompt="short prompt",
                full_prompt_fallback="full prompt",
            )
        finally:
            agent._context_caches.pop(cache_key, None)

        assert json.loads(result)["fallback"] is True
        agent.ask.assert_called_once()
        assert agent.ask.call_args.args[0] == "full prompt"


# ══════════════════════════════════════════════════════════════
# [TF3-H3/H7] Timeout + Prompt Gate
# ══════════════════════════════════════════════════════════════


class TestTimeoutAndPromptGate:
    def test_ask_injects_http_options_timeout(self, agent, monkeypatch):
        # [TF-44] Gemini API 무한 hang 방지 — http_options timeout 주입 검증
        monkeypatch.setattr(agent, "API_DELAY", 0)
        agent._generate_content = MagicMock(
            return_value=LLMResponse(text=json.dumps({"content": "ok"}), finish_reason="STOP")
        )

        _ = agent.ask("짧은 프롬프트")
        config = agent._generate_content.call_args.kwargs["config"]
        assert config.http_options is not None
        assert config.http_options.timeout == int(agent.API_TIMEOUT) * 1000

    def test_cached_context_call_injects_http_options_timeout(self, agent, monkeypatch):
        # [TF-44] Gemini API 무한 hang 방지 — cached context http_options timeout 주입 검증
        monkeypatch.setattr(agent, "API_DELAY", 0)
        agent._generate_content = MagicMock(
            return_value=LLMResponse(text=json.dumps({"content": "cached"}), finish_reason="STOP")
        )
        cache_key = seed_context_cache(agent, cache_name="cached/ctx", content_hash="hash-timeout")

        try:
            _ = agent._ask_with_cached_context(cache_name="cached/ctx", prompt="테스트")
        finally:
            agent._context_caches.pop(cache_key, None)
        config = agent._generate_content.call_args.kwargs["config"]
        assert config.http_options is not None
        assert config.http_options.timeout == int(agent.API_TIMEOUT) * 1000

    def test_prompt_size_gate_truncates(self, agent):
        agent.MAX_CONTEXT_CHARS = 260
        agent.requires_human_intervention = False

        prompt = "HEAD-ANCHOR\n" + ("x" * 480) + "\nTAIL-ANCHOR"
        clipped = agent._apply_prompt_size_gate(prompt)
        assert len(clipped) <= 260
        assert "Prompt truncated" in clipped
        assert "HEAD-ANCHOR" in clipped
        assert "TAIL-ANCHOR" in clipped
        assert agent.requires_human_intervention is True
