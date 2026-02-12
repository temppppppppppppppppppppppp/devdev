"""
[Phase 2] Model Cascading System

flash → pro → preview 자동 업그레이드
비용 최적화 + 품질 유지
"""
from typing import Dict, Tuple, Optional


class ModelCascade:
    """
    모델 티어 자동 업그레이드 시스템

    원리:
    - 1차 시도: flash (저렴, 빠름)
    - 2차 시도: pro (중간)
    - 3차 시도: preview (최고급, 최후 수단)
    """

    # 모델 티어 정의 (Gemini 3세대)
    TIER_1 = "gemini-2.5-flash"      # 저렴, 빠름
    TIER_2 = "gemini-2.5-pro"         # 중간
    TIER_3 = "gemini-3-pro-preview"   # 최고급

    # 티어 진행 순서
    CASCADE_ORDER = [TIER_1, TIER_2, TIER_3]

    # 비용 추정 (1K 입력 토큰 기준, USD)
    COSTS = {
        TIER_1: 0.0001,   # $0.0001/1K tokens
        TIER_2: 0.0003,   # $0.0003/1K tokens
        TIER_3: 0.001     # $0.001/1K tokens
    }

    def __init__(self, start_tier: int = 0, max_tier: int = 2):
        """
        Args:
            start_tier: 시작 티어 (0=flash, 1=pro, 2=preview)
            max_tier: 최대 티어 (2=preview까지 허용)
        """
        self.current_tier = start_tier
        self.max_tier = max_tier
        self.attempt_history = []

    def get_current_model(self) -> str:
        """현재 티어의 모델명 반환"""
        return self.CASCADE_ORDER[self.current_tier]

    def should_upgrade(self, result: dict) -> bool:
        """
        업그레이드 필요 여부 판단

        Args:
            result: 이전 시도 결과 dict
                - decision: "PASS" | "REJECT"
                - score: int (0-100)
                - error_category: "QUALITY_ISSUE" | "LOGIC_ERROR"

        Returns:
            True if upgrade needed, False otherwise
        """
        # 최대 티어 도달 시 업그레이드 불가
        if self.current_tier >= self.max_tier:
            return False

        # PASS면 업그레이드 불필요
        if result.get('decision') == 'PASS':
            return False

        # REJECT 시 업그레이드 판단
        error_category = result.get('error_category', 'QUALITY_ISSUE')

        # LOGIC_ERROR는 모델 업그레이드로 해결 불가능
        # (설정 오류는 아크 수정 필요)
        if error_category == 'LOGIC_ERROR':
            return False

        # QUALITY_ISSUE는 업그레이드로 개선 가능
        return True

    def upgrade(self) -> Tuple[bool, str]:
        """
        다음 티어로 업그레이드

        Returns:
            (success: bool, model_name: str)
        """
        if self.current_tier >= self.max_tier:
            return False, self.get_current_model()

        self.current_tier += 1
        new_model = self.get_current_model()

        self.attempt_history.append({
            'tier': self.current_tier,
            'model': new_model
        })

        return True, new_model

    def get_total_cost_estimate(self, input_tokens: int) -> float:
        """
        현재까지 사용한 총 비용 추정

        Args:
            input_tokens: 입력 토큰 수

        Returns:
            Estimated cost in USD
        """
        total_cost = 0.0
        for attempt in self.attempt_history:
            model = attempt['model']
            cost_per_1k = self.COSTS.get(model, 0.001)
            total_cost += (input_tokens / 1000) * cost_per_1k

        return total_cost

    def get_statistics(self) -> dict:
        """
        캐스케이드 통계 반환

        Returns:
            {
                "attempts": int,
                "final_tier": int,
                "final_model": str,
                "cost_saved": float (0~1, 0=최대 비용, 1=최대 절감)
            }
        """
        attempts = len(self.attempt_history)
        final_tier = self.current_tier
        final_model = self.get_current_model()

        # 비용 절감율 계산
        # 항상 최고급 모델 사용 시 vs 실제 사용 비용
        max_cost = self.COSTS[self.TIER_3]
        actual_cost = self.COSTS[final_model]
        cost_saved = 1 - (actual_cost / max_cost)

        return {
            "attempts": attempts,
            "final_tier": final_tier,
            "final_model": final_model,
            "cost_saved": cost_saved
        }

    def reset(self) -> None:
        """캐스케이드 초기화"""
        self.current_tier = 0
        self.attempt_history = []


class TaskBasedCascade:
    """
    작업 유형별 최적 모델 선택

    작업 복잡도에 따라 시작 티어 결정
    """

    @staticmethod
    def get_optimal_start_tier(task_type: str, retry_count: int = 0) -> int:
        """
        작업 유형과 재시도 횟수에 따른 최적 시작 티어

        Args:
            task_type: "BLUEPRINT" | "MANUSCRIPT" | "SCORING" | "ADVISORY"
            retry_count: 재시도 횟수 (높을수록 고급 모델부터 시작)

        Returns:
            Start tier (0=flash, 1=pro, 2=preview)
        """
        # 재시도 2회 이상 시 바로 pro부터 시작
        if retry_count >= 2:
            return 1  # pro

        # 재시도 3회 이상 시 바로 preview 사용
        if retry_count >= 3:
            return 2  # preview

        # 작업 유형별 시작 티어
        TASK_TIERS = {
            "ADVISORY": 0,      # 간단 → flash
            "SCORING": 0,       # Python 메트릭 있음 → flash 충분
            "BLUEPRINT": 0,     # 구조만 검증 → flash
            "MANUSCRIPT": 0,    # 대부분 flash로 통과 → flash 시작
        }

        return TASK_TIERS.get(task_type, 0)

    @staticmethod
    def should_skip_cascade(task_type: str) -> bool:
        """
        캐스케이드를 건너뛰고 바로 최고급 모델 사용할지 판단

        Args:
            task_type: 작업 유형

        Returns:
            True if skip cascade, False otherwise
        """
        # V0128 SCORING은 품질 중요 → pro 바로 사용
        if task_type == "SCORING_V0128":
            return True

        # 대부분은 캐스케이드 적용
        return False


def create_cascade_for_agent(agent_type: str, retry_count: int = 0) -> ModelCascade:
    """
    에이전트 타입에 맞는 ModelCascade 생성

    Args:
        agent_type: "writer" | "director" | "architect" | "analyst"
        retry_count: 현재 재시도 횟수

    Returns:
        ModelCascade instance
    """
    # 작업 유형 매핑
    task_type_map = {
        "writer": "MANUSCRIPT",
        "director": "MANUSCRIPT",
        "architect": "BLUEPRINT",
        "analyst": "BLUEPRINT"
    }

    task_type = task_type_map.get(agent_type, "MANUSCRIPT")
    start_tier = TaskBasedCascade.get_optimal_start_tier(task_type, retry_count)

    return ModelCascade(start_tier=start_tier, max_tier=2)
