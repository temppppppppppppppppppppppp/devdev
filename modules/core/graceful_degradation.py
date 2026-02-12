"""
[V58] Graceful Degradation System

에이전트 실패 시 자동 복구 시스템:
- 단계적 폴백 전략
- 부분 생성 복구
- 검증 실패 시 자동 수정 시도
- 캐시 기반 복구

실패 레벨:
1. RETRY: 동일 모델로 재시도
2. FALLBACK: 백업 모델로 전환
3. DEGRADE: 품질 저하 허용
4. SKIP: 해당 단계 건너뛰기
5. ABORT: 중단 및 사용자 개입 요청
"""

import json
import logging
import time
import traceback
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class FailureLevel(Enum):
    """실패 심각도 레벨"""
    RECOVERABLE = 1      # 자동 복구 가능
    DEGRADED = 2         # 품질 저하로 진행 가능
    CRITICAL = 3         # 사용자 개입 필요
    FATAL = 4            # 즉시 중단


class RecoveryStrategy(Enum):
    """복구 전략"""
    RETRY = "retry"              # 재시도
    FALLBACK_MODEL = "fallback"  # 백업 모델
    REDUCE_COMPLEXITY = "reduce" # 복잡도 감소
    USE_CACHE = "cache"          # 캐시 사용
    PARTIAL_RESULT = "partial"   # 부분 결과
    SKIP = "skip"                # 건너뛰기
    ABORT = "abort"              # 중단


@dataclass
class FailureRecord:
    """실패 기록"""
    timestamp: str
    stage: str
    agent: str
    error_type: str
    error_message: str
    recovery_attempted: str
    recovery_success: bool
    context: Dict[str, Any] = field(default_factory=dict)


class GracefulDegradation:
    """
    [V58] Graceful Degradation Manager

    에이전트 실패 시 단계적 복구를 시도하는 시스템

    복구 체인:
    1. 동일 설정으로 재시도 (최대 2회)
    2. 온도 낮춰서 재시도
    3. 백업 모델로 전환
    4. 복잡도 감소 (프롬프트 단순화)
    5. 캐시/이전 결과 활용
    6. 부분 결과 반환
    7. 건너뛰기 (경고 포함)
    8. 중단 및 사용자 개입 요청
    """

    # 에이전트별 복구 전략
    AGENT_RECOVERY_CHAINS = {
        'analyst': [
            RecoveryStrategy.RETRY,
            RecoveryStrategy.FALLBACK_MODEL,
            RecoveryStrategy.REDUCE_COMPLEXITY,
            RecoveryStrategy.ABORT,
        ],
        'architect': [
            RecoveryStrategy.RETRY,
            RecoveryStrategy.FALLBACK_MODEL,
            RecoveryStrategy.USE_CACHE,
            RecoveryStrategy.PARTIAL_RESULT,
            RecoveryStrategy.ABORT,
        ],
        'writer': [
            RecoveryStrategy.RETRY,
            RecoveryStrategy.FALLBACK_MODEL,
            RecoveryStrategy.REDUCE_COMPLEXITY,
            RecoveryStrategy.PARTIAL_RESULT,
            RecoveryStrategy.ABORT,
        ],
        'director': [
            RecoveryStrategy.RETRY,
            RecoveryStrategy.FALLBACK_MODEL,
            RecoveryStrategy.SKIP,  # Director 실패 시 검증 건너뛰기
        ],
        'default': [
            RecoveryStrategy.RETRY,
            RecoveryStrategy.FALLBACK_MODEL,
            RecoveryStrategy.ABORT,
        ],
    }

    # 오류 유형별 복구 전략 매핑
    ERROR_RECOVERY_MAP = {
        'RateLimitError': RecoveryStrategy.RETRY,
        'TimeoutError': RecoveryStrategy.RETRY,
        'JSONDecodeError': RecoveryStrategy.RETRY,
        'ContentFilterError': RecoveryStrategy.REDUCE_COMPLEXITY,
        'TokenLimitError': RecoveryStrategy.REDUCE_COMPLEXITY,
        'ModelOverloadError': RecoveryStrategy.FALLBACK_MODEL,
        'ValidationError': RecoveryStrategy.RETRY,
        'NetworkError': RecoveryStrategy.RETRY,
    }

    # 백업 모델 매핑
    FALLBACK_MODELS = {
        'gemini-3-pro-preview': 'gemini-2.5-pro',
        'gemini-2.5-pro': 'gemini-2.5-flash',
        'gemini-2.5-flash': 'gemini-2.0-flash',
        'gemini-2.0-flash': 'gemini-1.5-flash',
    }

    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Args:
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간 대기 시간 (초)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.failure_history: List[FailureRecord] = []
        self.recovery_stats = {
            'total_failures': 0,
            'recovered': 0,
            'degraded': 0,
            'aborted': 0,
        }

    def execute_with_recovery(
        self,
        func: Callable,
        agent_name: str,
        stage: str,
        context: Dict[str, Any] = None,
        fallback_result: Any = None
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        복구 체인을 적용하여 함수 실행

        Args:
            func: 실행할 함수 (인자 없음, 또는 context를 받음)
            agent_name: 에이전트 이름
            stage: 현재 Stage 이름
            context: 실행 컨텍스트 (수정 가능)
            fallback_result: 최종 실패 시 반환할 기본값

        Returns:
            (결과, 메타데이터)
        """
        context = context or {}
        metadata = {
            'attempts': 0,
            'recovery_used': [],
            'final_status': 'unknown',
            'degraded': False,
        }

        recovery_chain = self.AGENT_RECOVERY_CHAINS.get(
            agent_name,
            self.AGENT_RECOVERY_CHAINS['default']
        )

        current_strategy_idx = 0
        retry_count = 0

        while current_strategy_idx < len(recovery_chain):
            strategy = recovery_chain[current_strategy_idx]
            metadata['attempts'] += 1

            try:
                # 전략에 따른 컨텍스트 수정
                modified_context = self._apply_strategy(strategy, context, metadata)

                # 함수 실행
                if callable(func):
                    try:
                        result = func(modified_context) if modified_context else func()
                    except TypeError:
                        result = func()

                # 성공
                if result is not None:
                    metadata['final_status'] = 'success'
                    self.recovery_stats['recovered'] += 1
                    return result, metadata

                raise ValueError("결과가 None입니다")

            except Exception as e:
                error_type = type(e).__name__
                error_message = str(e)

                # 실패 기록
                self._record_failure(
                    stage=stage,
                    agent=agent_name,
                    error_type=error_type,
                    error_message=error_message,
                    recovery_attempted=strategy.value,
                    recovery_success=False,
                    context=context
                )

                logging.info(f"⚠️ [{agent_name}] {error_type}: {error_message[:100]}")

                # 재시도 전략인 경우
                if strategy == RecoveryStrategy.RETRY:
                    retry_count += 1
                    if retry_count < self.max_retries:
                        logging.info(f"🔄 재시도 {retry_count}/{self.max_retries}...")
                        time.sleep(self.retry_delay * retry_count)  # 점진적 대기
                        continue
                    else:
                        # 재시도 소진, 다음 전략으로
                        current_strategy_idx += 1
                        retry_count = 0
                        continue

                # 다음 전략으로 이동
                metadata['recovery_used'].append(strategy.value)
                current_strategy_idx += 1

                # SKIP 전략
                if strategy == RecoveryStrategy.SKIP:
                    logging.info(f"⏭️ [{agent_name}] 건너뛰기")
                    metadata['final_status'] = 'skipped'
                    metadata['degraded'] = True
                    self.recovery_stats['degraded'] += 1
                    return fallback_result, metadata

                # ABORT 전략
                if strategy == RecoveryStrategy.ABORT:
                    break

        # 모든 복구 전략 실패
        metadata['final_status'] = 'aborted'
        self.recovery_stats['aborted'] += 1
        self.recovery_stats['total_failures'] += 1

        logging.warning(f"🚨 [{agent_name}] 모든 복구 전략 실패 - 중단")
        return fallback_result, metadata

    def _apply_strategy(
        self,
        strategy: RecoveryStrategy,
        context: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """복구 전략 적용"""
        modified = context.copy()

        if strategy == RecoveryStrategy.FALLBACK_MODEL:
            current_model = context.get('model', 'gemini-2.5-pro')
            fallback = self.FALLBACK_MODELS.get(current_model)
            if fallback:
                modified['model'] = fallback
                modified['_fallback_applied'] = True
                logging.info(f"🔀 백업 모델로 전환: {current_model} → {fallback}")

        elif strategy == RecoveryStrategy.REDUCE_COMPLEXITY:
            # 온도 낮추기
            modified['temperature'] = max(0.1, context.get('temperature', 0.5) - 0.2)
            # 토큰 제한 줄이기
            modified['max_tokens'] = int(context.get('max_tokens', 8192) * 0.7)
            # 프롬프트 단순화 플래그
            modified['_simplified'] = True
            logging.info(f"📉 복잡도 감소: temp={modified['temperature']}, tokens={modified['max_tokens']}")
            metadata['degraded'] = True

        elif strategy == RecoveryStrategy.USE_CACHE:
            modified['_use_cache'] = True
            logging.info(f"💾 캐시 사용 시도")

        elif strategy == RecoveryStrategy.PARTIAL_RESULT:
            modified['_accept_partial'] = True
            metadata['degraded'] = True
            logging.info(f"📄 부분 결과 허용")

        return modified

    def _record_failure(
        self,
        stage: str,
        agent: str,
        error_type: str,
        error_message: str,
        recovery_attempted: str,
        recovery_success: bool,
        context: Dict[str, Any]
    ):
        """실패 기록"""
        record = FailureRecord(
            timestamp=datetime.now().isoformat(),
            stage=stage,
            agent=agent,
            error_type=error_type,
            error_message=error_message[:500],
            recovery_attempted=recovery_attempted,
            recovery_success=recovery_success,
            context={k: str(v)[:100] for k, v in context.items() if k != 'prompt'}
        )
        self.failure_history.append(record)

        # 최근 100개만 유지
        if len(self.failure_history) > 100:
            self.failure_history = self.failure_history[-100:]

    def get_recovery_suggestion(self, error_type: str) -> RecoveryStrategy:
        """오류 유형에 따른 복구 전략 제안"""
        return self.ERROR_RECOVERY_MAP.get(error_type, RecoveryStrategy.RETRY)

    def get_stats(self) -> Dict[str, Any]:
        """복구 통계"""
        total = self.recovery_stats['total_failures']
        if total == 0:
            return {
                **self.recovery_stats,
                'recovery_rate': 100.0,
                'degradation_rate': 0.0,
            }

        return {
            **self.recovery_stats,
            'recovery_rate': self.recovery_stats['recovered'] / max(1, total) * 100,
            'degradation_rate': self.recovery_stats['degraded'] / max(1, total) * 100,
        }

    def get_failure_summary(self) -> str:
        """실패 요약"""
        if not self.failure_history:
            return "[V58] 실패 기록 없음"

        lines = ["[V58 Failure Summary]"]
        lines.append(f"  총 실패: {len(self.failure_history)}건")

        # 에이전트별 집계
        by_agent = {}
        for record in self.failure_history:
            by_agent[record.agent] = by_agent.get(record.agent, 0) + 1

        lines.append("  에이전트별:")
        for agent, count in sorted(by_agent.items(), key=lambda x: -x[1]):
            lines.append(f"    - {agent}: {count}건")

        # 오류 유형별 집계
        by_error = {}
        for record in self.failure_history:
            by_error[record.error_type] = by_error.get(record.error_type, 0) + 1

        lines.append("  오류 유형별:")
        for error, count in sorted(by_error.items(), key=lambda x: -x[1])[:5]:
            lines.append(f"    - {error}: {count}건")

        return "\n".join(lines)


class ValidationRecovery:
    """
    [V58] 검증 실패 복구 전문 클래스

    REJECT된 원고/블루프린트 자동 수정 시도
    """

    def __init__(self, client=None) -> None:
        """
        Args:
            client: Gemini API 클라이언트 (자동 수정 시 필요)
        """
        self.client = client

    def attempt_auto_fix(
        self,
        content: str,
        validation_result: Dict[str, Any],
        content_type: str = "manuscript"
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        검증 실패 내용 자동 수정 시도

        Args:
            content: 원본 내용
            validation_result: 검증 결과 (issues 포함)
            content_type: 내용 유형 (manuscript/blueprint)

        Returns:
            (수정된 내용 또는 None, 메타데이터)
        """
        metadata = {
            'attempted': True,
            'fix_type': None,
            'success': False,
        }

        issues = validation_result.get('issues', [])
        if not issues:
            return None, metadata

        # 자동 수정 가능한 이슈 필터링
        fixable_issues = [i for i in issues if self._is_auto_fixable(i)]

        if not fixable_issues:
            metadata['fix_type'] = 'none_fixable'
            return None, metadata

        # Python 기반 자동 수정 시도
        fixed_content = content
        fixes_applied = []

        for issue in fixable_issues:
            fix_result = self._apply_python_fix(fixed_content, issue)
            if fix_result:
                fixed_content = fix_result
                fixes_applied.append(issue['type'])

        if fixes_applied:
            metadata['fix_type'] = 'python'
            metadata['fixes_applied'] = fixes_applied
            metadata['success'] = True
            return fixed_content, metadata

        # LLM 기반 수정 (비용 발생)
        if self.client and len(fixable_issues) <= 3:
            llm_result = self._apply_llm_fix(content, fixable_issues, content_type)
            if llm_result:
                metadata['fix_type'] = 'llm'
                metadata['success'] = True
                return llm_result, metadata

        return None, metadata

    def _is_auto_fixable(self, issue: Dict) -> bool:
        """자동 수정 가능 여부 판단"""
        fixable_types = [
            'word_repetition',      # 단어 반복
            'sentence_ending',      # 문장 종결 형식
            'dialogue_tag',         # 대사 태그
            'whitespace',           # 공백 문제
            'formatting',           # 포맷팅
            'length_issue',         # 길이 문제 (잘라내기)
        ]

        return issue.get('type') in fixable_types or \
               issue.get('auto_fixable', False)

    def _apply_python_fix(self, content: str, issue: Dict) -> Optional[str]:
        """Python 기반 자동 수정"""
        import re

        issue_type = issue.get('type', '')

        if issue_type == 'word_repetition':
            # 반복 단어 일부 제거/대체
            word = issue.get('word', '')
            if word and len(word) >= 2:
                # 연속 반복만 제거
                pattern = rf'({re.escape(word)})\s+\1'
                return re.sub(pattern, r'\1', content)

        elif issue_type == 'whitespace':
            # 과다 공백 정리
            content = re.sub(r'[ \t]+', ' ', content)
            content = re.sub(r'\n{3,}', '\n\n', content)
            return content

        elif issue_type == 'sentence_ending':
            # 문장 종결 통일 (간단한 케이스만)
            # "했다." 스타일로 통일
            pass

        return None

    def _apply_llm_fix(
        self,
        content: str,
        issues: List[Dict],
        content_type: str
    ) -> Optional[str]:
        """LLM 기반 자동 수정 (비용 발생)"""
        if not self.client:
            return None

        try:
            issues_desc = "\n".join([
                f"- {i.get('type')}: {i.get('message', '')}"
                for i in issues[:3]
            ])

            prompt = f"""다음 {content_type}의 문제를 수정해주세요.

[문제점]
{issues_desc}

[원본]
{content[:3000]}

[지시사항]
1. 위 문제점만 수정하세요
2. 나머지 내용은 그대로 유지하세요
3. 수정된 내용만 출력하세요 (설명 없이)
"""

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"temperature": 0.3, "max_output_tokens": 4096}
            )

            return response.text

        except Exception as e:
            logging.warning(f"⚠️ [AutoFix] LLM 수정 실패: {e}")
            return None


def create_graceful_degradation(max_retries: int = 3) -> GracefulDegradation:
    """GracefulDegradation 인스턴스 생성 헬퍼"""
    return GracefulDegradation(max_retries=max_retries)
