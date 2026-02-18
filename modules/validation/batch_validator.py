"""
[Phase 2] Batch Validation System

여러 원고를 동시에 검증하여 처리 속도 향상
asyncio 기반 병렬 처리
"""

import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any


class BatchValidator:
    """
    배치 검증 시스템

    여러 원고를 동시에 검증하여 처리 시간 단축
    """

    def __init__(self, orchestrator, max_concurrent: int = 10):
        """
        Args:
            orchestrator: ValidationOrchestrator instance
            max_concurrent: 동시 처리 최대 개수 (기본값 10)
                           - Gemini API: 1000+ RPM 지원
                           - 보수적 설정으로 안정성 확보
                           - 필요시 15-20까지 증가 가능
        """
        self.orchestrator = orchestrator
        self.max_concurrent = max_concurrent
        self.results = []
        self.stats = {"total_manuscripts": 0, "completed": 0, "failed": 0, "total_time": 0, "average_time": 0}
        self._stats_lock = threading.Lock()

    async def validate_batch_async(self, manuscripts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        비동기 배치 검증 (asyncio)

        Args:
            manuscripts: List of {
                'ep_num': int,
                'manuscript': str,
                'validation_context': dict
            }

        Returns:
            List of validation results
        """
        start_time = time.time()
        with self._stats_lock:
            self.stats["total_manuscripts"] = len(manuscripts)

        # Semaphore로 동시 실행 제한 (API rate limit 보호)
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def validate_one(ms_data) -> dict:
            async with semaphore:
                try:
                    # ThreadPoolExecutor로 동기 함수를 비동기로 실행
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(
                        None,
                        self.orchestrator.validate,
                        ms_data["ep_num"],
                        ms_data["manuscript"],
                        ms_data["validation_context"],
                    )
                    with self._stats_lock:
                        self.stats["completed"] += 1
                    return {"ep_num": ms_data["ep_num"], "result": result, "success": True}
                except Exception as e:
                    with self._stats_lock:
                        self.stats["failed"] += 1
                    return {"ep_num": ms_data["ep_num"], "error": str(e), "success": False}

        # 모든 원고 동시 처리
        tasks = [validate_one(ms) for ms in manuscripts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # gather 결과 중 Exception 인스턴스 처리
        processed = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logging.warning("[Sweep7-A] batch validation failed for item %d: %s", i, r)
                ep_num = (
                    manuscripts[i].get("ep_num") if i < len(manuscripts) and isinstance(manuscripts[i], dict) else -1
                )
                processed.append({"ep_num": ep_num, "success": False, "error": str(r)})
            else:
                processed.append(r)
        results = processed

        elapsed = time.time() - start_time
        with self._stats_lock:
            self.stats["total_time"] = elapsed
            self.stats["average_time"] = elapsed / len(manuscripts) if manuscripts else 0

        return results

    def validate_batch_sync(self, manuscripts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        동기 배치 검증 (ThreadPoolExecutor)

        asyncio 사용하지 않는 환경용

        Args:
            manuscripts: List of manuscript data

        Returns:
            List of validation results
        """
        start_time = time.time()
        with self._stats_lock:
            self.stats["total_manuscripts"] = len(manuscripts)

        def validate_one(ms_data) -> dict:
            try:
                result = self.orchestrator.validate(
                    ms_data["ep_num"], ms_data["manuscript"], ms_data["validation_context"]
                )
                with self._stats_lock:
                    self.stats["completed"] += 1
                return {"ep_num": ms_data["ep_num"], "result": result, "success": True}
            except Exception as e:
                with self._stats_lock:
                    self.stats["failed"] += 1
                return {"ep_num": ms_data["ep_num"], "error": str(e), "success": False}

        # ThreadPoolExecutor로 병렬 처리
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            results = list(executor.map(validate_one, manuscripts))

        elapsed = time.time() - start_time
        with self._stats_lock:
            self.stats["total_time"] = elapsed
            self.stats["average_time"] = elapsed / len(manuscripts) if manuscripts else 0

        return results

    def get_statistics(self) -> dict:
        """
        배치 처리 통계 반환

        Returns:
            {
                "total_manuscripts": int,
                "completed": int,
                "failed": int,
                "total_time": float (seconds),
                "average_time": float (seconds),
                "throughput": float (manuscripts/second)
            }
        """
        stats = self.stats.copy()
        if stats["total_time"] > 0:
            stats["throughput"] = stats["total_manuscripts"] / stats["total_time"]
        else:
            stats["throughput"] = 0

        return stats

    def print_report(self) -> None:
        """배치 처리 결과 출력"""
        stats = self.get_statistics()

        logging.info("\n" + "=" * 60)
        logging.info("BATCH VALIDATION REPORT")
        logging.info("=" * 60)
        logging.info(f"Total manuscripts: {stats['total_manuscripts']}")
        logging.info(f"Completed: {stats['completed']}")
        logging.info(f"Failed: {stats['failed']}")
        logging.info(f"Total time: {stats['total_time']:.2f}s")
        logging.info(f"Average time: {stats['average_time']:.2f}s per manuscript")
        logging.info(f"Throughput: {stats['throughput']:.2f} manuscripts/second")
        logging.info("=" * 60)


class BatchOptimizer:
    """
    배치 크기 최적화

    API rate limit과 메모리를 고려하여 최적 배치 크기 결정
    """

    @staticmethod
    def calculate_optimal_batch_size(
        total_manuscripts: int,
        api_rate_limit: int = 60,  # requests per minute
        memory_limit_mb: int = 512,
    ) -> int:
        """
        최적 배치 크기 계산

        Args:
            total_manuscripts: 총 원고 수
            api_rate_limit: API 분당 요청 제한
            memory_limit_mb: 메모리 제한 (MB)

        Returns:
            Optimal batch size
        """
        # API rate limit 고려 (분당 제한 / 4 = 15초당 처리량)
        api_constraint = api_rate_limit // 4

        # 메모리 고려 (원고 1개 = ~10MB 가정)
        memory_constraint = memory_limit_mb // 10

        # 최소값 선택
        optimal = min(api_constraint, memory_constraint)

        # 최소 1, 최대 10으로 제한
        return max(1, min(optimal, 10))

    @staticmethod
    def split_into_batches(manuscripts: list[dict], batch_size: int) -> list[list[dict]]:
        """
        원고 리스트를 배치로 분할

        Args:
            manuscripts: 원고 리스트
            batch_size: 배치 크기

        Returns:
            List of batches
        """
        batches = []
        for i in range(0, len(manuscripts), batch_size):
            batch = manuscripts[i : i + batch_size]
            batches.append(batch)

        return batches


# 편의 함수
def validate_manuscripts_in_batch(
    orchestrator, manuscripts: list[dict[str, Any]], max_concurrent: int = 3, use_async: bool = True
) -> list[dict[str, Any]]:
    """
    여러 원고를 배치로 검증

    Args:
        orchestrator: ValidationOrchestrator instance
        manuscripts: List of manuscript data
        max_concurrent: 동시 처리 개수
        use_async: True=asyncio, False=ThreadPoolExecutor

    Returns:
        List of validation results
    """
    validator = BatchValidator(orchestrator, max_concurrent)

    if use_async:
        # 플랫폼 감지 (개선)
        import sys

        is_notebook = "ipykernel" in sys.modules or "IPython" in sys.modules
        is_streamlit = "streamlit" in sys.modules

        if is_notebook or is_streamlit:
            # Jupyter/Streamlit 환경: 항상 ThreadPool 사용
            env_name = "Jupyter" if is_notebook else "Streamlit"
            logging.info(f"[INFO] {env_name} 환경 감지 - ThreadPool 모드 사용")
            results = validator.validate_batch_sync(manuscripts)
        else:
            # 일반 환경: asyncio 시도
            try:
                # 🔒 Event Loop Nested Execution 방지 (Issue #1)
                # 현재 실행 중인 loop 확인
                try:
                    running_loop = asyncio.get_running_loop()
                    # Loop가 있으면 동기 모드로 fallback (nested loop 방지)
                    logging.warning("[WARNING] 실행 중인 event loop 감지 - ThreadPool 동기 모드로 전환")
                    logging.info("[INFO] (Nested event loop execution을 방지하기 위한 안전 조치)")
                    results = validator.validate_batch_sync(manuscripts)
                except RuntimeError:
                    # Loop 없음 - asyncio.run() 사용 시도
                    try:
                        results = asyncio.run(validator.validate_batch_async(manuscripts))
                    except RuntimeError as run_err:
                        # [FIX] asyncio.run() 실패 시 (다른 스레드에서 loop 충돌)
                        logging.warning(f"[WARNING] asyncio.run() 실패: {run_err} - ThreadPool 모드로 재시도")
                        results = validator.validate_batch_sync(manuscripts)
            except Exception as e:
                # 예기치 못한 오류 시 동기 모드로 fallback
                logging.warning(f"[WARNING] Async 실행 실패: {e}")
                logging.info("[INFO] ThreadPool 동기 모드로 전환")
                results = validator.validate_batch_sync(manuscripts)
    else:
        # ThreadPoolExecutor 사용
        results = validator.validate_batch_sync(manuscripts)

    # 통계 출력
    validator.print_report()

    return results
