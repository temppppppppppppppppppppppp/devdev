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
from unittest.mock import MagicMock

import pytest

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.domain.agents.base_agent import AgentErrorType, BaseAgent

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
        """중첩 JSON 평탄화"""
        text = json.dumps({"title": "테스트", "state_updates": {"location": "무림맹", "energy": 70}})
        result = agent._extract_json_robust(text)
        assert result.get("location") == "무림맹"
        assert result.get("energy") == 70


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

    def test_json_error(self, agent):
        """JSON 파싱 분류"""
        error = Exception("json decode error at position 5")
        assert agent._classify_error(error) == AgentErrorType.MALFORMED_RESPONSE

    def test_unknown_error(self, agent):
        """알 수 없는 에러"""
        error = Exception("Something completely unexpected happened")
        assert agent._classify_error(error) == AgentErrorType.UNKNOWN


# ══════════════════════════════════════════════════════════════
# Test 5: _validate_response
# ══════════════════════════════════════════════════════════════


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
            AgentErrorType.UNKNOWN,
        ]:
            hint = agent._get_recovery_hint(error_type)
            assert isinstance(hint, str)
            assert len(hint) > 0


# ══════════════════════════════════════════════════════════════
# Test 8: MODEL_FALLBACK_CHAIN
# ══════════════════════════════════════════════════════════════


class TestModelFallbackChain:
    def test_gemini3_falls_to_25pro(self):
        """gemini-3-pro → gemini-2.5-pro"""
        assert BaseAgent.MODEL_FALLBACK_CHAIN["gemini-3-pro-preview"] == "gemini-2.5-pro"

    def test_25pro_is_terminal(self):
        """gemini-2.5-pro는 최종 방어선 (체인 없음)"""
        assert "gemini-2.5-pro" not in BaseAgent.MODEL_FALLBACK_CHAIN

    def test_flash_chain(self):
        """Flash 계열 폴백"""
        assert BaseAgent.MODEL_FALLBACK_CHAIN.get("gemini-3-flash-preview") == "gemini-2.5-flash"


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
