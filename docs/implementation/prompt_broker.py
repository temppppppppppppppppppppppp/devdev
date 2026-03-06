"""
Mode B: 인터랙티브 프롬프트 브로커 (prompt_broker.py)

역할:
- prompt_request WS 이벤트 발행 + prompt_id 추적
- /run/{run_id}/input 처리 → prompt_resolved 발행
- 타임아웃 → prompt_timeout 발행 + default 적용
- 중복 입력 차단 (PROMPT_ALREADY_RESOLVED)

사용법 (FastAPI app 초기화 시):
    def emit_fn(run_id: str, event: dict):
        # WebSocket broadcast 구현체 주입
        ws_manager.broadcast(run_id, event)

    seq_counter = itertools.count(1)
    app.state.prompt_broker = PromptBroker(
        emit_fn=emit_fn,
        seq_counter_fn=lambda: next(seq_counter),
    )
"""

import asyncio
import threading
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class PromptState:
    """단일 프롬프트의 생애주기 상태."""

    def __init__(
        self,
        prompt_id: str,
        step_id: str,
        input_type: str,       # "enum" | "int" | "string" | "bool"
        default: Any,
        timeout_sec: int,
        options: Optional[List[str]] = None,
    ) -> None:
        self.prompt_id = prompt_id
        self.step_id = step_id
        self.input_type = input_type
        self.default = default
        self.timeout_sec = timeout_sec
        self.options: List[str] = options or []

        self.resolved: bool = False
        self.value: Optional[Any] = None
        self._event: asyncio.Event = asyncio.Event()


class PromptBroker:
    """
    run_id별 pending prompt 추적 및 WS emit 연결.

    스레드 안전: _lock으로 내부 상태 보호.
    resolve()는 동기 호출 가능 (FastAPI endpoint에서 직접 호출).
    request_input()은 코루틴 — runner 내부 async 컨텍스트에서 await 사용.
    """

    def __init__(
        self,
        emit_fn: Callable[[str, dict], None],
        seq_counter_fn: Callable[[], int],
    ) -> None:
        self._emit = emit_fn
        self._next_seq = seq_counter_fn
        self._prompts: Dict[str, PromptState] = {}          # prompt_id -> PromptState
        self._run_prompts: Dict[str, Set[str]] = {}         # run_id -> {prompt_id, ...}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _ts(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    def _build_event(self, run_id: str, event_type: str, payload: dict) -> dict:
        """event-schema-v1.json 필수 필드 준수."""
        return {
            "event_version": "v1",
            "seq": self._next_seq(),
            "run_id": run_id,
            "type": event_type,
            "ts": self._ts(),
            "payload": payload,
        }

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    async def request_input(self, run_id: str, prompt: PromptState) -> Any:
        """
        prompt_request 이벤트 발행 후 사용자 응답 또는 타임아웃 대기.

        Returns:
            사용자가 입력한 값, 또는 타임아웃 시 prompt.default
        """
        with self._lock:
            self._prompts[prompt.prompt_id] = prompt
            self._run_prompts.setdefault(run_id, set()).add(prompt.prompt_id)

        # prompt_request 이벤트 발행
        payload: dict = {
            "prompt_id": prompt.prompt_id,
            "step_id": prompt.step_id,
            "input_type": prompt.input_type,
            "default": prompt.default,
            "timeout_sec": prompt.timeout_sec,
        }
        if prompt.options:
            payload["options"] = prompt.options

        self._emit(run_id, self._build_event(run_id, "prompt_request", payload))

        # 타임아웃 대기
        try:
            await asyncio.wait_for(prompt._event.wait(), timeout=float(prompt.timeout_sec))
        except asyncio.TimeoutError:
            with self._lock:
                if not prompt.resolved:
                    prompt.resolved = True
                    prompt.value = prompt.default

            # prompt_timeout 이벤트 발행
            self._emit(
                run_id,
                self._build_event(run_id, "prompt_timeout", {
                    "prompt_id": prompt.prompt_id,
                    "applied_default": prompt.default,
                }),
            )

        return prompt.value

    def resolve(
        self, run_id: str, prompt_id: str, value: Any
    ) -> Tuple[str, Optional[str]]:
        """
        /run/{run_id}/input 처리: 사용자 응답을 pending prompt에 연결.

        Returns:
            ("ok", None)                        — 성공
            ("error", "INVALID_PROMPT_ID")      — run_id에 속하지 않는 prompt_id
            ("error", "PROMPT_ALREADY_RESOLVED") — 이미 처리된 prompt_id
        """
        with self._lock:
            run_prompt_ids = self._run_prompts.get(run_id, set())
            if prompt_id not in run_prompt_ids:
                return "error", "INVALID_PROMPT_ID"

            prompt = self._prompts.get(prompt_id)
            if prompt is None:
                return "error", "INVALID_PROMPT_ID"

            if prompt.resolved:
                return "error", "PROMPT_ALREADY_RESOLVED"

            prompt.resolved = True
            prompt.value = value
            prompt._event.set()

        # prompt_resolved 이벤트 발행 (lock 해제 후)
        self._emit(
            run_id,
            self._build_event(run_id, "prompt_resolved", {
                "prompt_id": prompt_id,
                "value": value,
                "source": "user",
            }),
        )

        return "ok", None

    def cleanup_run(self, run_id: str) -> None:
        """run 종료(run_completed / run_failed) 시 관련 prompt 정리."""
        with self._lock:
            prompt_ids = self._run_prompts.pop(run_id, set())
            for pid in prompt_ids:
                self._prompts.pop(pid, None)
