"""[V64.P4] 성능 프로파일링 유틸리티.

에피소드 생산 파이프라인의 각 단계별 소요 시간을 측정하는 가벼운 타이머.

Usage:
    from modules.core.perf_timer import PerfTimer

    timer = PerfTimer("Stage4")
    timer.start("ensemble_generate")
    # ... 작업 ...
    timer.stop("ensemble_generate")

    timer.start("director_audit")
    # ... 작업 ...
    timer.stop("director_audit")

    timer.log_summary()
    # => [PerfTimer:Stage4] ensemble_generate=12.34s, director_audit=5.67s, _total=18.01s
"""

import logging
import time

logger = logging.getLogger(__name__)


class PerfTimer:
    """[V64.P4] 단계별 소요 시간 측정."""

    def __init__(self, label: str = ""):
        self.label = label
        self._marks: dict = {}
        self._start: float | None = None

    def start(self, step: str = "") -> None:
        """타이머 시작."""
        self._marks[step] = {"start": time.monotonic()}
        if self._start is None:
            self._start = time.monotonic()

    def stop(self, step: str = "") -> float:
        """타이머 종료, 경과 시간(초) 반환."""
        if step in self._marks and "start" in self._marks[step]:
            elapsed = time.monotonic() - self._marks[step]["start"]
            self._marks[step]["elapsed"] = elapsed
            return elapsed
        return 0.0

    def summary(self) -> dict:
        """전체 단계별 소요 시간 요약 (초 단위, 소수점 2자리)."""
        result = {}
        for step, data in self._marks.items():
            if "elapsed" in data:
                result[step] = round(data["elapsed"], 2)
        if self._start is not None:
            result["_total"] = round(time.monotonic() - self._start, 2)
        return result

    def log_summary(self) -> None:
        """소요 시간 요약을 로그로 출력."""
        s = self.summary()
        if s:
            parts = [f"{k}={v}s" for k, v in s.items()]
            logger.info(f"[PerfTimer:{self.label}] {', '.join(parts)}")

    def reset(self) -> None:
        """타이머 초기화."""
        self._marks.clear()
        self._start = None
