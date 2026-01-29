"""
[Phase 2] Batch Validation System

여러 원고를 동시에 검증하여 처리 속도 향상
asyncio 기반 병렬 처리
"""
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import time


class BatchValidator:
    """
    배치 검증 시스템

    여러 원고를 동시에 검증하여 처리 시간 단축
    """

    def __init__(self, orchestrator, max_concurrent: int = 3):
        """
        Args:
            orchestrator: ValidationOrchestrator instance
            max_concurrent: 동시 처리 최대 개수 (API rate limit 고려)
        """
        self.orchestrator = orchestrator
        self.max_concurrent = max_concurrent
        self.results = []
        self.stats = {
            'total_manuscripts': 0,
            'completed': 0,
            'failed': 0,
            'total_time': 0,
            'average_time': 0
        }

    async def validate_batch_async(
        self,
        manuscripts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
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
        self.stats['total_manuscripts'] = len(manuscripts)

        # Semaphore로 동시 실행 제한 (API rate limit 보호)
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def validate_one(ms_data):
            async with semaphore:
                try:
                    # ThreadPoolExecutor로 동기 함수를 비동기로 실행
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        self.orchestrator.validate,
                        ms_data['ep_num'],
                        ms_data['manuscript'],
                        ms_data['validation_context']
                    )
                    self.stats['completed'] += 1
                    return {
                        'ep_num': ms_data['ep_num'],
                        'result': result,
                        'success': True
                    }
                except Exception as e:
                    self.stats['failed'] += 1
                    return {
                        'ep_num': ms_data['ep_num'],
                        'error': str(e),
                        'success': False
                    }

        # 모든 원고 동시 처리
        tasks = [validate_one(ms) for ms in manuscripts]
        results = await asyncio.gather(*tasks)

        elapsed = time.time() - start_time
        self.stats['total_time'] = elapsed
        self.stats['average_time'] = elapsed / len(manuscripts) if manuscripts else 0

        return results

    def validate_batch_sync(
        self,
        manuscripts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        동기 배치 검증 (ThreadPoolExecutor)

        asyncio 사용하지 않는 환경용

        Args:
            manuscripts: List of manuscript data

        Returns:
            List of validation results
        """
        start_time = time.time()
        self.stats['total_manuscripts'] = len(manuscripts)

        def validate_one(ms_data):
            try:
                result = self.orchestrator.validate(
                    ms_data['ep_num'],
                    ms_data['manuscript'],
                    ms_data['validation_context']
                )
                self.stats['completed'] += 1
                return {
                    'ep_num': ms_data['ep_num'],
                    'result': result,
                    'success': True
                }
            except Exception as e:
                self.stats['failed'] += 1
                return {
                    'ep_num': ms_data['ep_num'],
                    'error': str(e),
                    'success': False
                }

        # ThreadPoolExecutor로 병렬 처리
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            results = list(executor.map(validate_one, manuscripts))

        elapsed = time.time() - start_time
        self.stats['total_time'] = elapsed
        self.stats['average_time'] = elapsed / len(manuscripts) if manuscripts else 0

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
        if stats['total_time'] > 0:
            stats['throughput'] = stats['total_manuscripts'] / stats['total_time']
        else:
            stats['throughput'] = 0

        return stats

    def print_report(self):
        """배치 처리 결과 출력"""
        stats = self.get_statistics()

        print("\n" + "=" * 60)
        print("BATCH VALIDATION REPORT")
        print("=" * 60)
        print(f"Total manuscripts: {stats['total_manuscripts']}")
        print(f"Completed: {stats['completed']}")
        print(f"Failed: {stats['failed']}")
        print(f"Total time: {stats['total_time']:.2f}s")
        print(f"Average time: {stats['average_time']:.2f}s per manuscript")
        print(f"Throughput: {stats['throughput']:.2f} manuscripts/second")
        print("=" * 60)


class BatchOptimizer:
    """
    배치 크기 최적화

    API rate limit과 메모리를 고려하여 최적 배치 크기 결정
    """

    @staticmethod
    def calculate_optimal_batch_size(
        total_manuscripts: int,
        api_rate_limit: int = 60,  # requests per minute
        memory_limit_mb: int = 512
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
    def split_into_batches(
        manuscripts: List[Dict],
        batch_size: int
    ) -> List[List[Dict]]:
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
            batch = manuscripts[i:i + batch_size]
            batches.append(batch)

        return batches


# 편의 함수
def validate_manuscripts_in_batch(
    orchestrator,
    manuscripts: List[Dict[str, Any]],
    max_concurrent: int = 3,
    use_async: bool = True
) -> List[Dict[str, Any]]:
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
        is_notebook = 'ipykernel' in sys.modules or 'IPython' in sys.modules
        is_streamlit = 'streamlit' in sys.modules

        if is_notebook or is_streamlit:
            # Jupyter/Streamlit 환경: 항상 ThreadPool 사용
            env_name = "Jupyter" if is_notebook else "Streamlit"
            print(f"[INFO] {env_name} 환경 감지 - ThreadPool 모드 사용")
            results = validator.validate_batch_sync(manuscripts)
        else:
            # 일반 환경: asyncio 시도
            try:
                # 🔒 Event Loop Nested Execution 방지 (Issue #1)
                # 현재 실행 중인 loop 확인
                try:
                    running_loop = asyncio.get_running_loop()
                    # Loop가 있으면 동기 모드로 fallback (nested loop 방지)
                    print("[WARNING] 실행 중인 event loop 감지 - ThreadPool 동기 모드로 전환")
                    print("[INFO] (Nested event loop execution을 방지하기 위한 안전 조치)")
                    results = validator.validate_batch_sync(manuscripts)
                except RuntimeError:
                    # Loop 없음 - asyncio.run() 사용 안전
                    results = asyncio.run(validator.validate_batch_async(manuscripts))
            except Exception as e:
                # 예기치 못한 오류 시 동기 모드로 fallback
                print(f"[ERROR] Async 실행 실패: {e}")
                print(f"[INFO] ThreadPool 동기 모드로 전환")
                results = validator.validate_batch_sync(manuscripts)
    else:
        # ThreadPoolExecutor 사용
        results = validator.validate_batch_sync(manuscripts)

    # 통계 출력
    validator.print_report()

    return results
