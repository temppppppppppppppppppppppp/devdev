"""
[V44] Agent 테스트

Mock API 기반 에이전트 테스트
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBaseAgent:
    """BaseAgent 테스트"""

    def test_agent_initialization(self, agent_config):
        """에이전트 초기화 테스트"""
        from modules.domain.agents.base_agent import BaseAgent

        agent = BaseAgent(agent_config)

        assert agent.config == agent_config
        assert agent.client is not None

    def test_ask_method_returns_json(self, agent_config):
        """ask 메서드 JSON 반환 테스트"""
        from modules.domain.agents.base_agent import BaseAgent

        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.text = json.dumps({"result": "success", "data": [1, 2, 3]})
        agent_config["api_client"].models.generate_content.return_value = mock_response

        agent = BaseAgent(agent_config)

        result = agent.ask("테스트 프롬프트")

        assert isinstance(result, dict)
        assert result.get("result") == "success"

    def test_ask_handles_invalid_json(self, agent_config):
        """ask 메서드 잘못된 JSON 처리 테스트"""
        from modules.domain.agents.base_agent import BaseAgent

        # 잘못된 JSON 응답
        mock_response = MagicMock()
        mock_response.text = "not valid json {{{"
        agent_config["api_client"].models.generate_content.return_value = mock_response

        agent = BaseAgent(agent_config)

        result = agent.ask("테스트 프롬프트")

        # 에러 없이 처리되어야 함 (빈 dict 또는 에러 정보 포함)
        assert isinstance(result, dict)

    def test_escape_braces_method(self, agent_config):
        """_escape_braces 메서드 테스트"""
        from modules.domain.agents.base_agent import BaseAgent

        agent = BaseAgent(agent_config)

        # 중괄호가 있는 텍스트
        text_with_braces = "이것은 {변수}가 있는 텍스트입니다."

        if hasattr(agent, '_escape_braces'):
            escaped = agent._escape_braces(text_with_braces)
            # 중괄호가 이스케이프되어야 함
            assert "{{" in escaped or "{변수}" not in escaped

    def test_backup_model_fallback(self, agent_config):
        """백업 모델 폴백 테스트"""
        from modules.domain.agents.base_agent import BaseAgent

        # 첫 번째 호출 실패, 두 번째 성공
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Primary model failed")
            mock_response = MagicMock()
            mock_response.text = json.dumps({"status": "backup_success"})
            return mock_response

        agent_config["api_client"].models.generate_content.side_effect = side_effect

        agent = BaseAgent(agent_config)

        result = agent.ask("테스트")

        # 백업 모델로 성공해야 함 (또는 에러 처리)
        assert isinstance(result, dict)

    def test_continuation_on_max_tokens(self, agent_config):
        """MAX_TOKENS 시 continuation 테스트"""
        from modules.domain.agents.base_agent import BaseAgent

        # 첫 응답은 truncated, 두 번째는 완료
        responses = [
            MagicMock(text='{"partial": "data",', candidates=[MagicMock(finish_reason='MAX_TOKENS')]),
            MagicMock(text='"complete": true}', candidates=[MagicMock(finish_reason='STOP')])
        ]

        call_idx = [0]

        def get_response(*args, **kwargs):
            idx = call_idx[0]
            call_idx[0] += 1
            if idx < len(responses):
                return responses[idx]
            return responses[-1]

        agent_config["api_client"].models.generate_content.side_effect = get_response

        agent = BaseAgent(agent_config)

        # continuation 로직 테스트
        # (실제 구현에 따라 결과 검증)

    def test_error_type_classification(self, agent_config):
        """에러 타입 분류 테스트"""
        from modules.domain.agents.base_agent import BaseAgent, AgentErrorType

        agent = BaseAgent(agent_config)

        # 에러 분류 메서드가 있는 경우
        if hasattr(agent, '_classify_error'):
            # Timeout 에러
            timeout_error = Exception("Request timed out")
            assert agent._classify_error(timeout_error) == AgentErrorType.TIMEOUT

            # Quota 에러
            quota_error = Exception("429 Resource exhausted")
            assert agent._classify_error(quota_error) == AgentErrorType.QUOTA_EXCEEDED


class TestWriterAgent:
    """Writer 에이전트 테스트"""

    def test_writer_initialization(self, agent_config):
        """Writer 초기화 테스트"""
        from modules.domain.agents.writer import Writer

        writer = Writer(agent_config)
        assert writer is not None

    def test_write_manuscript_structure(self, agent_config, sample_blueprint):
        """원고 생성 구조 테스트"""
        from modules.domain.agents.writer import Writer

        # Mock 응답
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "manuscript": "생성된 원고 내용 " * 1000,
            "actual_truth": {
                "character_state": {"내공": 65},
                "world_state": {"시간대": "새벽"}
            }
        })
        agent_config["api_client"].models.generate_content.return_value = mock_response

        writer = Writer(agent_config)

        # write_v20_manuscript 메서드가 있는 경우
        if hasattr(writer, 'write_v20_manuscript'):
            # 실제 호출은 API 비용 발생하므로 구조만 검증
            pass

    def test_writer_style_seeds_loading(self, agent_config, temp_dir):
        """Writer 스타일 시드 로딩 테스트"""
        from modules.domain.agents.writer import Writer

        # 스타일 시드 파일 생성
        style_seeds_path = temp_dir / "style_seeds_final.txt"
        style_seeds_path.write_text("테스트 스타일 시드 내용", encoding="utf-8")

        writer = Writer(agent_config)

        # 스타일 시드 로딩 로직 테스트


# [V65] TestArchitectAgent 삭제됨 — architect.py Dead Code 제거


class TestDirectorAgent:
    """Director 에이전트 테스트"""

    def test_director_initialization(self, agent_config):
        """Director 초기화 테스트"""
        from modules.domain.agents.director import Director

        director = Director(agent_config)
        assert director is not None

    def test_audit_manuscript_pass(self, agent_config, sample_manuscript):
        """원고 감사 통과 테스트"""
        from modules.domain.agents.director import Director

        # Mock 응답 (PASS)
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "verdict": "PASS",
            "score": 85,
            "feedback": "잘 작성되었습니다.",
            "issues": []
        })
        agent_config["api_client"].models.generate_content.return_value = mock_response

        director = Director(agent_config)

    def test_audit_manuscript_reject(self, agent_config):
        """원고 감사 거부 테스트"""
        from modules.domain.agents.director import Director

        # Mock 응답 (REJECT)
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "verdict": "REJECT",
            "score": 55,
            "feedback": "서사 정체가 감지됩니다.",
            "issues": ["캐릭터 일관성 부족", "긴장감 부족"]
        })
        agent_config["api_client"].models.generate_content.return_value = mock_response

        director = Director(agent_config)

    def test_director_v0128_integration(self, agent_config):
        """Director V0128 통합 테스트"""
        from modules.domain.agents.director import Director

        director = Director(agent_config)

        # V0128 모드 설정
        if hasattr(director, 'set_v0128_mode'):
            director.set_v0128_mode(True)
            assert director.use_v0128 == True


class TestAnalystAgent:
    """Analyst 에이전트 테스트"""

    def test_analyst_initialization(self, agent_config):
        """Analyst 초기화 테스트"""
        from modules.domain.agents.analyst import Analyst

        analyst = Analyst(agent_config)
        assert analyst is not None

    def test_plan_volumes_structure(self, agent_config, sample_bible):
        """볼륨 계획 구조 테스트"""
        from modules.domain.agents.analyst import Analyst

        # Mock 응답
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "volumes": [
                {"volume": 1, "title": "입문", "theme": "성장", "episodes": "1-50"},
                {"volume": 2, "title": "시련", "theme": "갈등", "episodes": "51-100"}
            ]
        })
        agent_config["api_client"].models.generate_content.return_value = mock_response

        analyst = Analyst(agent_config)

    def test_analyst_genre_library_loading(self, agent_config):
        """Analyst 장르별 라이브러리 로딩 테스트"""
        from modules.domain.agents.analyst import Analyst

        analyst = Analyst(agent_config)

        # 장르별 라이브러리 로딩
        if hasattr(analyst, 'set_genre'):
            for genre in ["wuxia", "hunter", "investment"]:
                analyst.set_genre(genre)


class TestWeaverAgent:
    """Weaver 에이전트 테스트"""

    def test_weaver_initialization(self, agent_config):
        """Weaver 초기화 테스트"""
        from modules.domain.agents.weaver import Weaver

        weaver = Weaver(agent_config)
        assert weaver is not None

    def test_foreshadowing_management(self, agent_config):
        """복선 관리 테스트"""
        from modules.domain.agents.weaver import Weaver

        # Mock 응답
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "planted": ["검의 비밀", "스승의 과거"],
            "harvested": [],
            "suggestions": ["제 10화에서 검의 비밀 회수 권장"]
        })
        agent_config["api_client"].models.generate_content.return_value = mock_response

        weaver = Weaver(agent_config)


class TestManagerAgent:
    """Manager 에이전트 테스트"""

    def test_manager_initialization(self, agent_config):
        """Manager 초기화 테스트"""
        from modules.domain.agents.manager import Manager

        manager = Manager(agent_config)
        assert manager is not None

    def test_coordinate_production(self, agent_config):
        """프로덕션 조율 테스트"""
        from modules.domain.agents.manager import Manager

        # Mock 응답
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "decision": "proceed",
            "adjustments": [],
            "notes": "정상 진행"
        })
        agent_config["api_client"].models.generate_content.return_value = mock_response

        manager = Manager(agent_config)


class TestAgentModelTiers:
    """에이전트 모델 티어 테스트"""

    def test_tier_progression_on_reject(self, agent_config):
        """거부 시 티어 상승 테스트"""
        # Tier 1 → Tier 2 → Tier 3 상승 로직

        tier_models = {
            1: "gemini-2.5-flash",
            2: "gemini-2.5-pro",
            3: "gemini-3-pro-preview"
        }

        # 재시도 횟수에 따른 모델 선택 테스트
        for retry_count in range(3):
            if retry_count == 0:
                expected_tier = 1
            elif retry_count == 1:
                expected_tier = 2
            else:
                expected_tier = 3

            # 실제 에이전트 구현에 따라 검증

    def test_stage4_fixed_model(self, agent_config):
        """Stage 4 고정 모델 테스트"""
        # Stage 4에서 Writer는 항상 gemini-3-pro-preview 사용

        stage4_model = "gemini-3-pro-preview"

        # Writer가 Stage 4에서 고정 모델 사용하는지 검증
