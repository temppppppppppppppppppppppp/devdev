"""subprocess 래퍼 스텁 — ProcessRunner (스파이크 3)

역할:
- main_a.py를 숨김 프로세스로 기동/종료/상태 추적
- 현재는 인터페이스 정의 + 상태 추적만 실제 동작 (스텁)
- 스파이크 2(subprocess stdin/stdout) PASS 후 실제 Popen 구현 연결 예정

기동 방식 (스파이크 2 연결 후):
    asyncio.create_subprocess_exec(
        sys.executable, "main_a.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
"""

from __future__ import annotations

import logging
from typing import AsyncIterator, Optional

logger = logging.getLogger(__name__)

# 러너가 취할 수 있는 상태 (StatusEnvelope.data.state enum과 동기화)
VALID_STATES = frozenset({"idle", "starting", "running", "waiting_input", "stopping", "error"})


class ProcessRunner:
    """main_a.py subprocess 래퍼.

    스파이크 3에서는 상태 전이만 실제 구현.
    실제 Popen은 스파이크 2 PASS 후 채운다.

    상태머신:
        idle → starting → running → stopping → idle
        any  → error → idle
    """

    def __init__(self) -> None:
        self._state: str = "idle"
        self._run_id: Optional[str] = None
        self._pid: Optional[int] = None

    # ------------------------------------------------------------------
    # 프로퍼티
    # ------------------------------------------------------------------

    @property
    def state(self) -> str:
        return self._state

    @property
    def run_id(self) -> Optional[str]:
        return self._run_id

    @property
    def pid(self) -> Optional[int]:
        return self._pid

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def start(
        self,
        key: str,
        run_id: str,
        sub_key: Optional[str] = None,
        inputs: Optional[dict] = None,
    ) -> None:
        """subprocess 기동 (스텁).

        실제 구현:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "main_a.py",
                stdin=PIPE, stdout=PIPE, stderr=PIPE,
                encoding="utf-8",
            )
            proc.stdin.write(f"{key}\\n")
        """
        logger.info("[STUB] ProcessRunner.start key=%r run_id=%r sub_key=%r", key, run_id, sub_key)
        self._state = "running"
        self._run_id = run_id
        self._pid = None  # 실제 PID는 스파이크 2 연결 후 채워짐

    def stop(self) -> None:
        """subprocess kill + 상태 초기화.

        실제 구현:
            if proc and proc.returncode is None:
                proc.kill()
                await proc.wait()
        """
        if self._state == "idle":
            return  # 멱등 — 이미 중지 상태
        logger.info("[STUB] ProcessRunner.stop run_id=%r", self._run_id)
        self._state = "idle"
        self._run_id = None
        self._pid = None

    async def read_stdout(self) -> AsyncIterator[str]:
        """비동기 stdout 줄 단위 수집 (스텁).

        실제 구현:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                yield line.decode("utf-8").rstrip()

        현재는 빈 제너레이터 — 스파이크 2 결과 반영 후 교체.
        """
        # 스텁: 즉시 종료 (이벤트 없음)
        return
        yield  # noqa: unreachable — AsyncIterator 타입 유지용
