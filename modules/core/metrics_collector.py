"""
[V44] 글도비 성능 메트릭 수집기

에이전트 호출, API 사용량, 성능 지표를 추적하고 분석합니다.

Features:
- 에이전트별 호출 횟수/재시도 횟수 추적
- 응답 시간 측정 (P50, P90, P99)
- 토큰 사용량 추정
- API 비용 계산
- 세션별 통계 리포트
"""

import time
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import statistics


@dataclass
class AgentMetric:
    """개별 에이전트 호출 메트릭"""
    agent_name: str
    model: str
    start_time: float
    end_time: float = 0.0
    success: bool = False
    retry_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    error_type: Optional[str] = None

    @property
    def duration_ms(self) -> float:
        """응답 시간 (밀리초)"""
        if self.end_time == 0:
            return 0
        return (self.end_time - self.start_time) * 1000

    @property
    def total_tokens(self) -> int:
        """총 토큰 수"""
        return self.input_tokens + self.output_tokens


@dataclass
class SessionStats:
    """세션 통계"""
    session_id: str
    start_time: datetime
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_retries: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    agent_stats: Dict[str, Dict] = field(default_factory=dict)
    model_stats: Dict[str, Dict] = field(default_factory=dict)


# 모델별 토큰 비용 (USD per 1M tokens, 2024년 기준 추정)
MODEL_COSTS = {
    'gemini-2.0-flash': {'input': 0.075, 'output': 0.30},
    'gemini-2.5-flash': {'input': 0.15, 'output': 0.60},
    'gemini-2.5-pro': {'input': 1.25, 'output': 5.00},
    'gemini-3-pro-preview': {'input': 2.50, 'output': 10.00},
    'default': {'input': 0.50, 'output': 2.00}
}


class MetricsCollector:
    """
    [V44] 성능 메트릭 수집기

    Usage:
        collector = MetricsCollector()

        # 호출 시작
        metric_id = collector.start_call("Writer", "gemini-3-pro-preview")

        # 작업 수행...

        # 호출 종료
        collector.end_call(metric_id, success=True, input_tokens=1000, output_tokens=500)

        # 통계 조회
        stats = collector.get_session_stats()
    """

    _instance: Optional['MetricsCollector'] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """싱글톤 패턴"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, metrics_dir: Optional[Path] = None):
        """
        메트릭 수집기 초기화

        Args:
            metrics_dir: 메트릭 저장 디렉토리 (기본: logs/metrics/)
        """
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._initialized = True
        self.metrics_dir = metrics_dir or Path("logs") / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        # 세션 정보
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_start = datetime.now()

        # 메트릭 저장소
        self._metrics: Dict[str, AgentMetric] = {}
        self._metric_counter = 0

        # 집계 데이터
        self._agent_durations: Dict[str, List[float]] = defaultdict(list)
        self._agent_calls: Dict[str, int] = defaultdict(int)
        self._agent_successes: Dict[str, int] = defaultdict(int)
        self._agent_retries: Dict[str, int] = defaultdict(int)
        self._model_tokens: Dict[str, Dict[str, int]] = defaultdict(lambda: {'input': 0, 'output': 0})

        # 스레드 안전성
        self._lock = threading.Lock()

    def start_call(self, agent_name: str, model: str) -> str:
        """
        에이전트 호출 시작 기록

        Args:
            agent_name: 에이전트 이름 (Writer, Architect, etc.)
            model: 사용 모델명

        Returns:
            str: 메트릭 ID (end_call에서 사용)
        """
        with self._lock:
            self._metric_counter += 1
            metric_id = f"{self.session_id}_{self._metric_counter}"

            metric = AgentMetric(
                agent_name=agent_name,
                model=model,
                start_time=time.time()
            )
            self._metrics[metric_id] = metric
            self._agent_calls[agent_name] += 1

            return metric_id

    def end_call(
        self,
        metric_id: str,
        success: bool = True,
        retry_count: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error_type: Optional[str] = None
    ):
        """
        에이전트 호출 종료 기록

        Args:
            metric_id: start_call에서 반환된 ID
            success: 성공 여부
            retry_count: 재시도 횟수
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
            error_type: 에러 타입 (실패 시)
        """
        with self._lock:
            if metric_id not in self._metrics:
                return

            metric = self._metrics[metric_id]
            metric.end_time = time.time()
            metric.success = success
            metric.retry_count = retry_count
            metric.input_tokens = input_tokens
            metric.output_tokens = output_tokens
            metric.error_type = error_type

            # 집계 업데이트
            agent = metric.agent_name
            self._agent_durations[agent].append(metric.duration_ms)
            self._agent_retries[agent] += retry_count

            if success:
                self._agent_successes[agent] += 1

            # 모델별 토큰 집계
            model = metric.model
            self._model_tokens[model]['input'] += input_tokens
            self._model_tokens[model]['output'] += output_tokens

    def record_retry(self, agent_name: str):
        """재시도 기록 (간편 메서드)"""
        with self._lock:
            self._agent_retries[agent_name] += 1

    def estimate_tokens(self, text: str, is_input: bool = True) -> int:
        """
        텍스트의 토큰 수 추정 (간단한 휴리스틱)

        Args:
            text: 텍스트
            is_input: 입력인지 출력인지

        Returns:
            int: 추정 토큰 수
        """
        if not text:
            return 0
        # 대략적 추정: 한글 1.5자당 1토큰, 영어 4자당 1토큰
        korean_chars = sum(1 for c in text if '가' <= c <= '힣')
        other_chars = len(text) - korean_chars
        return int(korean_chars / 1.5 + other_chars / 4)

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        API 비용 계산

        Args:
            model: 모델명
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수

        Returns:
            float: 비용 (USD)
        """
        costs = MODEL_COSTS.get(model, MODEL_COSTS['default'])
        input_cost = (input_tokens / 1_000_000) * costs['input']
        output_cost = (output_tokens / 1_000_000) * costs['output']
        return input_cost + output_cost

    def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """
        특정 에이전트의 통계 반환

        Args:
            agent_name: 에이전트 이름

        Returns:
            dict: 에이전트 통계
        """
        with self._lock:
            durations = self._agent_durations.get(agent_name, [])
            calls = self._agent_calls.get(agent_name, 0)
            successes = self._agent_successes.get(agent_name, 0)
            retries = self._agent_retries.get(agent_name, 0)

            stats = {
                'agent_name': agent_name,
                'total_calls': calls,
                'successful_calls': successes,
                'failed_calls': calls - successes,
                'success_rate': (successes / calls * 100) if calls > 0 else 0,
                'total_retries': retries,
                'avg_retries_per_call': (retries / calls) if calls > 0 else 0
            }

            if durations:
                stats['duration_stats'] = {
                    'avg_ms': statistics.mean(durations),
                    'min_ms': min(durations),
                    'max_ms': max(durations),
                    'p50_ms': statistics.median(durations),
                    'p90_ms': self._percentile(durations, 90),
                    'p99_ms': self._percentile(durations, 99)
                }

            return stats

    def get_session_stats(self) -> SessionStats:
        """세션 전체 통계 반환"""
        with self._lock:
            total_calls = sum(self._agent_calls.values())
            successful_calls = sum(self._agent_successes.values())
            total_retries = sum(self._agent_retries.values())

            # 총 토큰 및 비용 계산
            total_tokens = 0
            total_cost = 0.0
            model_stats = {}

            for model, tokens in self._model_tokens.items():
                input_t = tokens['input']
                output_t = tokens['output']
                cost = self.calculate_cost(model, input_t, output_t)

                total_tokens += input_t + output_t
                total_cost += cost

                model_stats[model] = {
                    'input_tokens': input_t,
                    'output_tokens': output_t,
                    'total_tokens': input_t + output_t,
                    'cost_usd': round(cost, 4)
                }

            # 에이전트별 통계
            agent_stats = {
                agent: self.get_agent_stats(agent)
                for agent in self._agent_calls.keys()
            }

            return SessionStats(
                session_id=self.session_id,
                start_time=self.session_start,
                total_calls=total_calls,
                successful_calls=successful_calls,
                failed_calls=total_calls - successful_calls,
                total_retries=total_retries,
                total_tokens=total_tokens,
                total_cost_usd=round(total_cost, 4),
                agent_stats=agent_stats,
                model_stats=model_stats
            )

    def get_summary_report(self) -> str:
        """사람이 읽을 수 있는 요약 리포트 반환"""
        stats = self.get_session_stats()
        duration = datetime.now() - stats.start_time

        lines = [
            "=" * 60,
            f"  [V44] 글도비 성능 메트릭 리포트",
            "=" * 60,
            f"세션 ID: {stats.session_id}",
            f"실행 시간: {duration}",
            "",
            "[호출 통계]",
            f"- 총 호출: {stats.total_calls}회",
            f"- 성공: {stats.successful_calls}회 ({(stats.successful_calls / stats.total_calls * 100) if stats.total_calls > 0 else 0:.1f}%)",
            f"- 실패: {stats.failed_calls}회",
            f"- 총 재시도: {stats.total_retries}회",
            "",
            "[비용 통계]",
            f"- 총 토큰: {stats.total_tokens:,}",
            f"- 예상 비용: ${stats.total_cost_usd:.4f} USD",
            "",
            "[에이전트별 통계]"
        ]

        for agent, agent_stat in stats.agent_stats.items():
            lines.append(f"  {agent}:")
            lines.append(f"    - 호출: {agent_stat['total_calls']}회 (성공률: {agent_stat['success_rate']:.1f}%)")
            lines.append(f"    - 평균 재시도: {agent_stat['avg_retries_per_call']:.2f}회/호출")
            if 'duration_stats' in agent_stat:
                d = agent_stat['duration_stats']
                lines.append(f"    - 응답시간: avg={d['avg_ms']:.0f}ms, p50={d['p50_ms']:.0f}ms, p90={d['p90_ms']:.0f}ms")

        lines.append("")
        lines.append("[모델별 통계]")
        for model, model_stat in stats.model_stats.items():
            lines.append(f"  {model}:")
            lines.append(f"    - 토큰: {model_stat['total_tokens']:,} (in={model_stat['input_tokens']:,}, out={model_stat['output_tokens']:,})")
            lines.append(f"    - 비용: ${model_stat['cost_usd']:.4f}")

        lines.append("=" * 60)

        return "\n".join(lines)

    def save_metrics(self):
        """메트릭을 파일로 저장"""
        stats = self.get_session_stats()
        filepath = self.metrics_dir / f"metrics_{self.session_id}.json"

        data = {
            'session_id': stats.session_id,
            'start_time': stats.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_calls': stats.total_calls,
            'successful_calls': stats.successful_calls,
            'failed_calls': stats.failed_calls,
            'total_retries': stats.total_retries,
            'total_tokens': stats.total_tokens,
            'total_cost_usd': stats.total_cost_usd,
            'agent_stats': stats.agent_stats,
            'model_stats': stats.model_stats
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        return filepath

    def _percentile(self, data: List[float], percentile: int) -> float:
        """백분위수 계산"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (len(sorted_data) - 1) * percentile / 100
        lower = int(index)
        upper = lower + 1
        if upper >= len(sorted_data):
            return sorted_data[-1]
        weight = index - lower
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


# 전역 인스턴스
_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """전역 메트릭 수집기 반환"""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


def start_call(agent_name: str, model: str) -> str:
    """편의 함수: 호출 시작"""
    return get_metrics_collector().start_call(agent_name, model)


def end_call(metric_id: str, **kwargs):
    """편의 함수: 호출 종료"""
    get_metrics_collector().end_call(metric_id, **kwargs)
