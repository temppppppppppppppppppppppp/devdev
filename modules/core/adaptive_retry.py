"""
[V54.3] Adaptive Retry System (Enhanced)

에러 타입에 따라 다른 재시도 전략을 적용하는 시스템
+ V54.3: 실패 패턴 학습, 필살기 권장, 에이전트별 약점 분석

에러 타입:
1. CONSTRAINT_VIOLATION - 제약 조건 위반 (중복 획득, 상태 불연속 등)
2. QUALITY_ISSUE - 품질 문제 (밀도 부족, 개연성 부족)
3. STRUCTURE_ERROR - 구조적 오류 (JSON 파싱 실패, 필수 키 누락)
4. TIMEOUT - 타임아웃/토큰 제한
5. QUOTA_EXCEEDED - API 할당량 초과
6. CHARACTER_INCONSISTENCY - 캐릭터 일관성 문제 [V54.3 NEW]
7. LOGIC_ERROR - 논리적 모순 [V54.3 NEW]
8. SCOPE_OVERFLOW - 범위 초과 [V54.3 NEW]

전략:
- CONSTRAINT_VIOLATION: 제약 블록 강화, 구체적 금지 항목 주입
- QUALITY_ISSUE: 온도 상향, 예시 추가
- STRUCTURE_ERROR: 온도 하향, 스키마 강제
- TIMEOUT: 청크 분할 또는 요약 요청
- QUOTA_EXCEEDED: 대기 후 재시도
- CHARACTER_INCONSISTENCY: 캐릭터 프로필 재주입
- LOGIC_ERROR: 인과관계 강화 지침
- SCOPE_OVERFLOW: 범위 제한 경고

V54.3 신규 기능:
- 에이전트별 실패 통계 및 약점 분석
- 필살기 발동 권장 (ToT/ASP/MAD)
- 연속 실패 에스컬레이션
"""

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ErrorType(Enum):
    """에러 타입 정의"""

    CONSTRAINT_VIOLATION = "constraint_violation"
    QUALITY_ISSUE = "quality_issue"
    STRUCTURE_ERROR = "structure_error"
    TIMEOUT = "timeout"
    QUOTA_EXCEEDED = "quota_exceeded"
    # V54.3 신규
    CHARACTER_INCONSISTENCY = "character_inconsistency"
    LOGIC_ERROR = "logic_error"
    SCOPE_OVERFLOW = "scope_overflow"
    UNKNOWN = "unknown"


@dataclass
class RetryContext:
    """재시도 컨텍스트"""

    attempt: int = 0
    max_attempts: int = 3
    error_history: list[dict] = field(default_factory=list)
    injected_constraints: list[str] = field(default_factory=list)
    temperature_delta: float = 0.0
    should_use_schema: bool = True
    prompt_modifications: list[str] = field(default_factory=list)


class AdaptiveRetryStrategy:
    """
    [V49.4] 적응형 재시도 전략 관리자

    에러 타입에 따라 다른 재시도 전략을 선택하고,
    누적된 실패 이력을 바탕으로 프롬프트를 수정합니다.
    """

    # 에러 타입별 최대 재시도 횟수
    MAX_RETRIES_BY_TYPE = {
        ErrorType.CONSTRAINT_VIOLATION: 3,
        ErrorType.QUALITY_ISSUE: 2,
        ErrorType.STRUCTURE_ERROR: 2,
        ErrorType.TIMEOUT: 1,
        ErrorType.QUOTA_EXCEEDED: 3,
        ErrorType.UNKNOWN: 2,
    }

    # 에러 타입별 대기 시간 (초)
    WAIT_TIME_BY_TYPE = {
        ErrorType.CONSTRAINT_VIOLATION: 0,
        ErrorType.QUALITY_ISSUE: 0,
        ErrorType.STRUCTURE_ERROR: 1,
        ErrorType.TIMEOUT: 2,
        ErrorType.QUOTA_EXCEEDED: 30,
        ErrorType.UNKNOWN: 1,
    }

    def __init__(self) -> None:
        self.contexts: dict[str, RetryContext] = {}

    def get_context(self, task_id: str) -> RetryContext:
        """태스크별 컨텍스트 가져오기"""
        if task_id not in self.contexts:
            self.contexts[task_id] = RetryContext()
        return self.contexts[task_id]

    def reset_context(self, task_id: str):
        """컨텍스트 초기화"""
        if task_id in self.contexts:
            del self.contexts[task_id]

    def classify_error(self, error_info: dict) -> ErrorType:
        """
        에러 정보를 분류하여 타입 반환

        Args:
            error_info: {
                "message": 에러 메시지,
                "violations": 위반 목록,
                "decision": PASS/REJECT,
                "score": 점수,
                "reason": 사유
            }

        Returns:
            ErrorType 열거형
        """
        message = str(error_info.get("message", "")).lower()
        violations = error_info.get("violations", [])
        reason = str(error_info.get("reason", "")).lower()

        # 제약 조건 위반 키워드
        constraint_keywords = [
            "중복 획득",
            "duplicate",
            "이미 보유",
            "already",
            "연속성",
            "continuity",
            "상태 불연속",
            "state mismatch",
            "획득 금지",
            "forbidden",
            "재획득",
        ]

        # 품질 문제 키워드
        quality_keywords = [
            "밀도 부족",
            "density",
            "개연성",
            "plausibility",
            "품질",
            "quality",
            "미달",
            "insufficient",
            "score",
            "점수",
        ]

        # 구조적 오류 키워드
        structure_keywords = ["json", "parsing", "파싱", "key", "누락", "missing", "required", "schema", "format"]

        # 타임아웃 키워드
        timeout_keywords = ["timeout", "max_tokens", "length", "truncate", "절단", "시간 초과"]

        # 할당량 초과 키워드
        quota_keywords = ["quota", "rate limit", "429", "too many", "할당량", "제한"]

        combined_text = f"{message} {reason} {' '.join(str(v) for v in violations)}"

        # 키워드 매칭
        if any(k in combined_text for k in constraint_keywords):
            return ErrorType.CONSTRAINT_VIOLATION
        if any(k in combined_text for k in quality_keywords):
            return ErrorType.QUALITY_ISSUE
        if any(k in combined_text for k in structure_keywords):
            return ErrorType.STRUCTURE_ERROR
        if any(k in combined_text for k in timeout_keywords):
            return ErrorType.TIMEOUT
        if any(k in combined_text for k in quota_keywords):
            return ErrorType.QUOTA_EXCEEDED

        return ErrorType.UNKNOWN

    def should_retry(self, task_id: str, error_info: dict) -> tuple[bool, ErrorType]:
        """
        재시도 여부 결정

        Args:
            task_id: 태스크 식별자
            error_info: 에러 정보

        Returns:
            (재시도 여부, 에러 타입)
        """
        ctx = self.get_context(task_id)
        error_type = self.classify_error(error_info)

        # 에러 이력 추가
        ctx.error_history.append({"type": error_type.value, "info": error_info, "attempt": ctx.attempt})

        max_retries = self.MAX_RETRIES_BY_TYPE.get(error_type, 2)

        if ctx.attempt >= max_retries:
            logging.info(f"🚫 [AdaptiveRetry] 최대 재시도 횟수 도달 ({ctx.attempt}/{max_retries})")
            return False, error_type

        ctx.attempt += 1
        return True, error_type

    def get_retry_strategy(self, task_id: str, error_type: ErrorType, error_info: dict) -> dict[str, Any]:
        """
        에러 타입에 맞는 재시도 전략 반환

        Args:
            task_id: 태스크 식별자
            error_type: 에러 타입
            error_info: 에러 상세 정보

        Returns:
            {
                "wait_time": 대기 시간,
                "temperature_delta": 온도 변경량,
                "prompt_injection": 프롬프트에 주입할 텍스트,
                "use_schema": 스키마 강제 여부,
                "constraints": 추가할 제약 조건 목록
            }
        """
        ctx = self.get_context(task_id)
        strategy = {
            "wait_time": self.WAIT_TIME_BY_TYPE.get(error_type, 1),
            "temperature_delta": 0.0,
            "prompt_injection": "",
            "use_schema": True,
            "constraints": [],
        }

        if error_type == ErrorType.CONSTRAINT_VIOLATION:
            strategy = self._strategy_for_constraint_violation(ctx, error_info)
        elif error_type == ErrorType.QUALITY_ISSUE:
            strategy = self._strategy_for_quality_issue(ctx, error_info)
        elif error_type == ErrorType.STRUCTURE_ERROR:
            strategy = self._strategy_for_structure_error(ctx, error_info)
        elif error_type == ErrorType.TIMEOUT:
            strategy = self._strategy_for_timeout(ctx, error_info)
        elif error_type == ErrorType.QUOTA_EXCEEDED:
            strategy = self._strategy_for_quota_exceeded(ctx, error_info)

        return strategy

    def _strategy_for_constraint_violation(self, ctx: RetryContext, error_info: dict) -> dict[str, Any]:
        """
        제약 조건 위반에 대한 전략
        - 위반한 항목을 명시적으로 프롬프트에 주입
        - 온도를 약간 낮춰 더 보수적인 생성 유도
        """
        violations = error_info.get("violations", [])

        # 위반 사항을 명시적 금지 목록으로 변환
        forbidden_items = []
        for v in violations:
            if isinstance(v, str):
                # "중복 획득: '대도'" 형태에서 아이템 추출
                match = re.search(r"['\"](.*?)['\"]", v)
                if match:
                    forbidden_items.append(match.group(1))

        # 강화된 경고 메시지 생성
        injection = "\n\n" + "=" * 60 + "\n"
        injection += "[!!! CRITICAL RETRY WARNING !!!]\n"
        injection += f"이전 시도에서 {len(violations)}건의 제약 조건 위반이 발생했습니다.\n"
        injection += "아래 항목을 절대 위반하지 마십시오:\n"
        for i, v in enumerate(violations[:5], 1):  # 최대 5개
            injection += f"  {i}. {v}\n"
        if forbidden_items:
            injection += f"\n[ABSOLUTE BAN - 절대 재획득 금지]: {', '.join(forbidden_items)}\n"
        injection += "=" * 60 + "\n"

        ctx.injected_constraints.extend(forbidden_items)

        return {
            "wait_time": 0,
            "temperature_delta": -0.1,  # 더 보수적으로
            "prompt_injection": injection,
            "use_schema": True,
            "constraints": forbidden_items,
        }

    def _strategy_for_quality_issue(self, ctx: RetryContext, error_info: dict) -> dict[str, Any]:
        """
        품질 문제에 대한 전략
        - 온도를 약간 높여 더 창의적인 생성 유도
        - 구체적인 피드백 주입
        """
        reason = error_info.get("reason", "")
        score = error_info.get("score", 0)

        injection = "\n\n" + "-" * 60 + "\n"
        injection += "[QUALITY IMPROVEMENT REQUIRED]\n"
        injection += f"이전 시도의 품질 점수: {score}점\n"
        injection += f"개선 필요 사항: {reason}\n"
        injection += "\n[개선 지침]:\n"
        injection += "1. 각 화의 전술 밀도를 높이십시오 (최소 800자/화)\n"
        injection += "2. 물리적 인과관계를 더 구체적으로 서술하십시오\n"
        injection += "3. 캐릭터의 심리적 동기를 명확히 하십시오\n"
        injection += "-" * 60 + "\n"

        return {
            "wait_time": 0,
            "temperature_delta": 0.1,  # 더 창의적으로
            "prompt_injection": injection,
            "use_schema": True,
            "constraints": [],
        }

    def _strategy_for_structure_error(self, ctx: RetryContext, error_info: dict) -> dict[str, Any]:
        """
        구조적 오류에 대한 전략
        - 온도를 낮춰 정형화된 출력 유도
        - 스키마 강제 활성화
        """
        missing_keys = error_info.get("missing_keys", [])

        injection = "\n\n" + "#" * 60 + "\n"
        injection += "[JSON STRUCTURE REPAIR REQUIRED]\n"
        injection += "이전 응답의 JSON 구조가 올바르지 않았습니다.\n"
        if missing_keys:
            injection += f"누락된 필수 키: {', '.join(missing_keys)}\n"
        injection += "\n반드시 아래 구조를 준수하십시오:\n"
        injection += "- 응답은 반드시 '{' 로 시작하고 '}' 로 끝나야 합니다\n"
        injection += "- 모든 필수 키를 포함해야 합니다\n"
        injection += "- 문자열 내 큰따옴표는 이스케이프 처리해야 합니다\n"
        injection += "#" * 60 + "\n"

        return {
            "wait_time": 1,
            "temperature_delta": -0.2,  # 더 보수적으로
            "prompt_injection": injection,
            "use_schema": True,  # 스키마 강제
            "constraints": [],
        }

    def _strategy_for_timeout(self, ctx: RetryContext, error_info: dict) -> dict[str, Any]:
        """
        타임아웃에 대한 전략
        - 출력 길이 제한 요청
        """
        injection = "\n\n" + "*" * 60 + "\n"
        injection += "[OUTPUT LENGTH CONSTRAINT]\n"
        injection += "이전 응답이 최대 토큰을 초과했습니다.\n"
        injection += "tactical_doc을 핵심 비트 위주로 압축하여 작성하십시오.\n"
        injection += "각 화당 최대 600자로 제한하십시오.\n"
        injection += "*" * 60 + "\n"

        return {
            "wait_time": 2,
            "temperature_delta": 0.0,
            "prompt_injection": injection,
            "use_schema": True,
            "constraints": [],
        }

    def _strategy_for_quota_exceeded(self, ctx: RetryContext, error_info: dict) -> dict[str, Any]:
        """
        할당량 초과에 대한 전략
        - 긴 대기 시간 후 재시도
        """
        return {
            "wait_time": 30,  # 30초 대기
            "temperature_delta": 0.0,
            "prompt_injection": "",
            "use_schema": True,
            "constraints": [],
        }

    def apply_strategy(self, task_id: str, base_prompt: str, strategy: dict[str, Any]) -> str:
        """
        전략을 프롬프트에 적용

        Args:
            task_id: 태스크 식별자
            base_prompt: 기본 프롬프트
            strategy: 재시도 전략

        Returns:
            수정된 프롬프트
        """
        ctx = self.get_context(task_id)

        # 대기 시간
        wait_time = strategy.get("wait_time", 0)
        if wait_time > 0:
            logging.info(f"⏳ [AdaptiveRetry] {wait_time}초 대기 중...")
            time.sleep(wait_time)

        # 온도 델타 저장 (호출자가 사용)
        ctx.temperature_delta = strategy.get("temperature_delta", 0.0)
        ctx.should_use_schema = strategy.get("use_schema", True)

        # 프롬프트 수정
        modified_prompt = base_prompt
        injection = strategy.get("prompt_injection", "")
        if injection:
            # 프롬프트 앞부분에 경고 주입
            modified_prompt = injection + "\n" + modified_prompt
            ctx.prompt_modifications.append(injection)

        return modified_prompt

    def get_temperature(self, task_id: str, base_temperature: float) -> float:
        """현재 컨텍스트의 온도 반환"""
        ctx = self.get_context(task_id)
        adjusted = base_temperature + ctx.temperature_delta
        return max(0.1, min(1.0, adjusted))  # 0.1 ~ 1.0 범위로 클램핑


# 싱글턴 인스턴스
_adaptive_retry_instance = None


def get_adaptive_retry() -> AdaptiveRetryStrategy:
    """AdaptiveRetryStrategy 싱글턴 인스턴스 반환"""
    global _adaptive_retry_instance
    if _adaptive_retry_instance is None:
        _adaptive_retry_instance = AdaptiveRetryStrategy()
    return _adaptive_retry_instance


# ============================================================================
# [V54.3] Enhanced Adaptive Retry Manager
# ============================================================================

from collections import defaultdict


@dataclass
class FailureRecord:
    """실패 기록"""

    ep_num: int
    agent: str
    error_type: ErrorType
    details: dict
    timestamp: float = 0
    attempt: int = 1

    def __post_init__(self) -> None:
        if self.timestamp == 0:
            self.timestamp = time.time()


class AdaptiveRetryManager:
    """
    [V54.3] 적응형 재시도 관리자 (강화 버전)

    기존 AdaptiveRetryStrategy를 확장하여:
    - 에이전트별 실패 통계 추적
    - 필살기 발동 권장
    - 연속 실패 에스컬레이션
    - [V54.3.1] FailureLearner 연동으로 학습된 제약 자동 주입
    """

    # 필살기 권장 매핑
    ULTIMATE_RECOMMENDATIONS = {
        ErrorType.QUALITY_ISSUE: "adversarial_self_play",
        ErrorType.CHARACTER_INCONSISTENCY: "adversarial_self_play",
        ErrorType.STRUCTURE_ERROR: "tree_of_thoughts",
        ErrorType.SCOPE_OVERFLOW: "tree_of_thoughts",
        ErrorType.CONSTRAINT_VIOLATION: "multi_agent_deliberation",
        ErrorType.LOGIC_ERROR: "multi_agent_deliberation",
    }

    # 에스컬레이션 임계값
    ESCALATION_THRESHOLDS = {
        1: "기본 수정 지침",
        2: "강화된 수정 지침 + 구체적 예시",
        3: "필살기 발동 권고 (ToT/ASP/MAD)",
    }

    # ErrorType → Stage 매핑 (FailureLearner 연동용)
    AGENT_STAGE_MAP = {"analyst": 2, "architect": 3, "writer": 4}

    def __init__(self, max_history: int = 100, failure_learner=None):
        """
        Args:
            max_history: 최대 기록 수
            failure_learner: [V54.3.1] FailureLearner 인스턴스 (연동 활성화)
        """
        self.max_history = max_history
        self.strategy = get_adaptive_retry()
        self.failure_learner = failure_learner  # [V54.3.1]

        # 에피소드별 실패 기록
        self._failures: dict[int, list[FailureRecord]] = defaultdict(list)

        # 에이전트별 실패 통계
        self._agent_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def record_failure(self, ep_num: int, agent: str, error_info: dict, attempt: int = 1) -> ErrorType:
        """
        실패 기록 및 분류

        Args:
            ep_num: 에피소드 번호
            agent: 에이전트 이름 ("writer", "architect", etc.)
            error_info: 에러 정보
            attempt: 시도 횟수

        Returns:
            분류된 에러 타입
        """
        # 에러 분류
        error_type = self.strategy.classify_error(error_info)

        # V54.3 신규 키워드 분류
        message = str(error_info.get("message", "")).lower()
        reason = str(error_info.get("reason", "")).lower()
        combined = f"{message} {reason}"

        if any(k in combined for k in ["캐릭터", "말투", "성격", "character"]):
            error_type = ErrorType.CHARACTER_INCONSISTENCY
        elif any(k in combined for k in ["논리", "모순", "인과", "logic"]):
            error_type = ErrorType.LOGIC_ERROR
        elif any(k in combined for k in ["범위", "초과", "scope", "overflow"]):
            error_type = ErrorType.SCOPE_OVERFLOW

        record = FailureRecord(ep_num=ep_num, agent=agent, error_type=error_type, details=error_info, attempt=attempt)

        self._failures[ep_num].append(record)
        self._agent_stats[agent][error_type.value] += 1

        # 기록 수 제한
        if len(self._failures[ep_num]) > self.max_history:
            self._failures[ep_num] = self._failures[ep_num][-self.max_history :]

        # [V54.3.1] FailureLearner 연동: 실패 기록 동기화
        if self.failure_learner:
            try:
                stage = self.AGENT_STAGE_MAP.get(agent.lower(), 4)
                reason = error_info.get("reason", error_info.get("message", "unknown"))
                self.failure_learner.record_failure(stage=stage, episode=ep_num, reason=str(reason), details=error_info)
            except Exception:
                pass  # FailureLearner 연동 실패는 무시

        return error_type

    def get_retry_guidance(self, ep_num: int, agent: str, current_attempt: int = 1) -> dict[str, Any]:
        """
        재시도 지침 생성

        Args:
            ep_num: 에피소드 번호
            agent: 에이전트 이름
            current_attempt: 현재 시도 횟수

        Returns:
            재시도 지침 딕셔너리
        """
        # 이 에피소드의 실패 기록 조회
        failures = [f for f in self._failures.get(ep_num, []) if f.agent == agent]

        if not failures:
            return {
                "priority_fixes": ["블루프린트 정확히 따르기"],
                "avoid_patterns": ["범위 초과", "연속성 오류"],
                "temperature_adjustment": 0,
                "escalation_level": 1,
            }

        # 실패 유형별 빈도 분석
        type_counts = defaultdict(int)
        for f in failures:
            type_counts[f.error_type] += 1

        if not type_counts:
            return {
                "primary_error": "unknown",
                "failure_count": len(failures),
                "priority_fixes": [],
                "avoid_patterns": [],
                "temperature_adjustment": 0,
            }

        # 가장 빈번한 실패 유형
        primary_error = max(type_counts, key=type_counts.get)

        # 지침 생성
        guidance = {
            "primary_error": primary_error.value,
            "failure_count": len(failures),
            "priority_fixes": [],
            "avoid_patterns": [],
            "temperature_adjustment": 0,
            "escalation_level": min(current_attempt, 3),
        }

        # 에러 타입별 지침
        if primary_error == ErrorType.CONSTRAINT_VIOLATION:
            guidance["priority_fixes"] = ["이전 에피소드 상태 확인", "아이템 일관성 유지"]
            guidance["avoid_patterns"] = ["미획득 아이템 사용", "사망 NPC 등장"]
            guidance["temperature_adjustment"] = -0.1
        elif primary_error == ErrorType.QUALITY_ISSUE:
            guidance["priority_fixes"] = ["감각적 묘사 강화", "대화 품질 향상"]
            guidance["avoid_patterns"] = ["설명 위주 전개", "직접적 감정 서술"]
            guidance["temperature_adjustment"] = 0.1
        elif primary_error == ErrorType.SCOPE_OVERFLOW:
            guidance["priority_fixes"] = ["블루프린트 씬 개수 준수", "범위 내 완결"]
            guidance["avoid_patterns"] = ["다음 화 내용 선취", "과도한 전개"]
            guidance["temperature_adjustment"] = -0.15
        elif primary_error == ErrorType.CHARACTER_INCONSISTENCY:
            guidance["priority_fixes"] = ["캐릭터 말투 일관성", "성격 특성 유지"]
            guidance["avoid_patterns"] = ["갑작스러운 성격 변화", "말투 혼용"]
            guidance["temperature_adjustment"] = -0.1
        elif primary_error == ErrorType.LOGIC_ERROR:
            guidance["priority_fixes"] = ["인과관계 명확화", "동기 부여"]
            guidance["avoid_patterns"] = ["비합리적 행동", "설명 없는 결정"]
            guidance["temperature_adjustment"] = -0.1

        return guidance

    def should_trigger_ultimate(self, ep_num: int, agent: str) -> tuple[bool, str]:
        """
        필살기 발동 여부 판단

        Returns:
            (발동 여부, 권장 필살기)
        """
        failures = [f for f in self._failures.get(ep_num, []) if f.agent == agent]

        if len(failures) < 2:
            return False, ""

        # 실패 패턴 분석
        type_counts = defaultdict(int)
        for f in failures:
            type_counts[f.error_type] += 1

        if not type_counts:
            return False, "adversarial_self_play"

        primary = max(type_counts, key=type_counts.get)

        # 필살기 권장
        recommended = self.ULTIMATE_RECOMMENDATIONS.get(
            primary,
            "adversarial_self_play",  # 기본값
        )

        return True, recommended

    def get_injection_prompt(self, ep_num: int, agent: str, current_attempt: int = 1) -> str:
        """
        프롬프트에 주입할 수정 지침 생성

        Args:
            ep_num: 에피소드 번호
            agent: 에이전트 이름
            current_attempt: 현재 시도 횟수

        Returns:
            주입할 프롬프트 문자열
        """
        guidance = self.get_retry_guidance(ep_num, agent, current_attempt)

        if guidance.get("failure_count", 0) == 0:
            return ""

        lines = ["\n[V54.3 Adaptive Retry - 수정 지침]"]

        if priority := guidance.get("priority_fixes"):
            lines.append("우선 수정:")
            for fix in priority:
                lines.append(f"  - {fix}")

        if avoid := guidance.get("avoid_patterns"):
            lines.append("피해야 할 것:")
            for a in avoid:
                lines.append(f"  - {a}")

        escalation = self.ESCALATION_THRESHOLDS.get(guidance.get("escalation_level", 1), "기본 수정 지침")
        lines.append(f"\n[{current_attempt}회차 시도] {escalation}")

        # [V54.3.1] FailureLearner 학습 제약 주입
        if self.failure_learner:
            try:
                stage = self.AGENT_STAGE_MAP.get(agent.lower(), 4)
                learned_prompt = self.failure_learner.generate_constraint_prompt(stage=stage)
                if learned_prompt:
                    lines.append("")
                    lines.append(learned_prompt)
            except Exception:
                pass  # FailureLearner 연동 실패는 무시

        return "\n".join(lines)

    def get_agent_weakness(self, agent: str) -> dict[str, Any]:
        """에이전트의 약점 분석"""
        stats = self._agent_stats.get(agent, {})

        if not stats:
            return {"status": "no_data"}

        total = sum(stats.values())
        sorted_types = sorted(stats.items(), key=lambda x: -x[1])

        return {
            "total_failures": total,
            "primary_weakness": sorted_types[0][0] if sorted_types else None,
            "weakness_distribution": {k: f"{v / total:.1%}" for k, v in sorted_types[:3]},
        }

    def connect_failure_learner(self, failure_learner) -> None:
        """
        [V54.3.1] FailureLearner 연동
        싱글턴 생성 후 호출하여 FailureLearner 연결

        Args:
            failure_learner: FailureLearner 인스턴스
        """
        self.failure_learner = failure_learner

    def get_summary(self) -> str:
        """요약 통계"""
        total_failures = sum(len(records) for records in self._failures.values())

        agent_summaries = []
        for agent, stats in self._agent_stats.items():
            total = sum(stats.values())
            if stats:
                primary = max(stats, key=stats.get)
                agent_summaries.append(f"  {agent}: {total}회 (주요: {primary})")

        return f"[V54.3 Adaptive Retry 통계]\n총 실패: {total_failures}회\n에이전트별:\n" + "\n".join(agent_summaries)


# V54.3 싱글턴 인스턴스
_adaptive_manager_instance = None


def get_adaptive_manager() -> AdaptiveRetryManager:
    """AdaptiveRetryManager 싱글턴 인스턴스 반환"""
    global _adaptive_manager_instance
    if _adaptive_manager_instance is None:
        _adaptive_manager_instance = AdaptiveRetryManager()
    return _adaptive_manager_instance


# ============================================================================
# [V65] retry_with_feedback — 범용 재시도 래퍼
# ============================================================================


def retry_with_feedback(
    func,  # 호출할 함수: func(attempt, feedback) -> result
    max_attempts: int = 3,
    on_failure=None,  # 실패 시 피드백 생성 콜백: on_failure(result, attempt) -> str
    on_success=None,  # 성공 판정 콜백: on_success(result) -> bool
    logger=None,  # 로깅 함수: logger(msg)
    task_name: str = "",  # 로그용 작업명
) -> tuple:  # (result, attempt_count, success)
    """
    [V65] 범용 피드백 재시도 래퍼.

    인라인 retry 루프를 표준화하기 위한 간결한 유틸리티.
    func(attempt, feedback)를 반복 호출하되, on_success 판정이 True면 즉시 종료.
    실패 시 on_failure로 다음 시도에 전달할 피드백 문자열을 생성한다.

    Args:
        func:         호출할 함수. (attempt: int, feedback: str) -> result
        max_attempts: 최대 시도 횟수 (기본 3)
        on_failure:   실패 시 피드백 생성. (result, attempt) -> str.  None이면 빈 문자열.
        on_success:   성공 판정. (result) -> bool.  None이면 항상 True(첫 시도 성공).
        logger:       로그 함수. None이면 무시.
        task_name:    로그 메시지에 포함할 작업명.

    Returns:
        (result, attempt_count, success)
        - result: 마지막 func 호출의 반환값
        - attempt_count: 실제 시도 횟수 (1-based)
        - success: on_success 통과 여부
    """
    result = None
    feedback = ""
    success = False

    def _log(msg: str):
        if logger:
            try:
                logger(msg)
            except Exception:
                pass

    for attempt in range(max_attempts):
        try:
            result = func(attempt, feedback)
        except Exception as exc:
            _log(f"[retry_with_feedback] {task_name} attempt {attempt + 1}/{max_attempts} 예외: {exc}")
            if attempt < max_attempts - 1:
                feedback = f"이전 시도 예외: {exc}"
                continue
            else:
                return (None, attempt + 1, False)

        # 성공 판정
        if on_success is None or on_success(result):
            success = True
            _log(f"[retry_with_feedback] {task_name} attempt {attempt + 1} 성공")
            return (result, attempt + 1, True)

        # 실패 → 피드백 생성
        if attempt < max_attempts - 1:
            if on_failure:
                try:
                    feedback = on_failure(result, attempt)
                except Exception:
                    feedback = ""
            _log(f"[retry_with_feedback] {task_name} attempt {attempt + 1} 실패, 재시도 예정")

    # 모든 시도 소진
    return (result, max_attempts, False)
