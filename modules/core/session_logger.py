"""[LOG-1] SessionLogger — LLM I/O + 판정 경로 + 상태 변경 JSONL 전량 로깅.

카테고리별 JSONL 파일 분리, 크기 기반 로테이션, 프롬프트 절삭.
audit_service(경량 감사)와 독립: LLM 풀덤프(100K+자/건) 혼입 방지.

출력 파일:
  - llm_io.jsonl       — BaseAgent.ask() 호출 원문
  - decisions.jsonl     — Director 판정 경로
  - state_changes.jsonl — WorldState/FactLedger 변경
"""

import json
import logging
import os
import threading
import time
from pathlib import Path

from modules.core.soft_failure import report_soft_failure


class SessionLogger:
    """프로젝트별 JSONL 세션 로거.

    Parameters
    ----------
    log_dir : str | Path
        JSONL 파일 출력 디렉토리 (프로젝트 선택 전 임시 경로).
    enabled : bool
        False이면 모든 기록 무시 (기본 OFF).
    max_file_mb : int
        파일당 최대 MB. 초과 시 로테이션.
    max_prompt_chars : int
        프롬프트/응답 문자열 절삭 상한.
    max_rotations : int
        로테이션 파일 최대 개수.
    """

    _CATEGORIES = ("llm_io", "decisions", "state_changes", "ui_events")

    def __init__(
        self,
        log_dir,
        *,
        enabled=False,
        max_file_mb=100,
        max_prompt_chars=200000,
        max_rotations=10,
    ):
        self._log_dir = Path(log_dir)
        self._enabled = bool(enabled)
        self._max_file_bytes = max(1, int(max_file_mb)) * 1024 * 1024
        self._max_prompt_chars = max(1000, int(max_prompt_chars))
        self._max_rotations = max(1, int(max_rotations))
        self._write_lock = threading.Lock()  # [TF-30-7] 멀티스레드 JSONL interleave 방지
        self._soft_failure_count = 0
        self._last_soft_failure = None

    # ── public API ───────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_log_dir(self, new_dir) -> None:
        """프로젝트 선택 후 경로 갱신."""
        self._log_dir = Path(new_dir)

    def begin_shutdown(self) -> None:
        """Freeze best-effort JSONL telemetry writes before process teardown."""
        self._enabled = False

    def get_health_snapshot(self) -> dict:
        """Return recent logger health state for diagnostics."""
        return {
            "enabled": self._enabled,
            "soft_failures": self._soft_failure_count,
            "last_soft_failure": dict(self._last_soft_failure) if isinstance(self._last_soft_failure, dict) else None,
        }

    def log_llm_call(
        self,
        *,
        agent_name: str,
        model: str,
        prompt: str,
        response: str,
        temperature: float = 0.0,
        duration_ms: float = 0.0,
        success: bool = True,
        error: str = "",
        thinking: str = "",  # [TF-28] LLM thinking content
        **meta,
    ) -> None:
        """LLM 호출 원문 기록."""
        if not self._enabled:
            return
        data = {
            "agent": agent_name,
            "model": model,
            "prompt": self._truncate(prompt),
            "response": self._truncate(response),
            "temperature": temperature,
            "duration_ms": round(duration_ms, 1),
            "success": success,
        }
        if error:
            data["error"] = str(error)[:2000]
        if thinking:  # [TF-28] non-empty만 기록
            data["thinking"] = self._truncate(thinking)
        if meta:
            data["meta"] = meta
        self._write("llm_io", data)

    def log_decision(
        self,
        *,
        stage: str,
        ep_num: int,
        round_num: int = 0,
        decision_type: str = "",
        result: str = "",
        score: int = 0,
        advisories: list | None = None,
        **meta,
    ) -> None:
        """Director 판정 경로 기록."""
        if not self._enabled:
            return
        data = {
            "stage": stage,
            "ep_num": ep_num,
            "round_num": round_num,
            "decision_type": decision_type,
            "result": result,
            "score": score,
        }
        if advisories:
            data["advisories"] = advisories[:50]
        if meta:
            data["meta"] = meta
        self._write("decisions", data)

    def log_state_change(
        self,
        *,
        ep_num: int,
        change_type: str,
        entity: str = "",
        before: object = None,
        after: object = None,
        source: str = "",
    ) -> None:
        """상태 변경 기록 (WorldState, FactLedger 등)."""
        if not self._enabled:
            return
        data = {
            "ep_num": ep_num,
            "change_type": change_type,
        }
        if entity:
            data["entity"] = entity
        if before is not None:
            data["before"] = self._safe_serialize(before)
        if after is not None:
            data["after"] = self._safe_serialize(after)
        if source:
            data["source"] = source
        self._write("state_changes", data)

    def log_ui_event(
        self,
        *,
        session_id: str | None = None,
        seq: int | None = None,
        level: str = "info",
        component: str = "UI",
        stage: int | str | None = None,
        ep_num: int | None = None,
        arc_num: int | None = None,
        round_num: int | None = None,
        attempt_key: str | None = None,
        event_kind: str = "log",
        render_format: str = "text",
        message: str = "",
        visible: bool = True,
        selection_value: str | None = None,
        prompt_id: str | None = None,
        artifact_path: str | None = None,
        meta: dict | None = None,
        ts: str | None = None,
    ) -> None:
        """Persist operator-visible UI events to ``ui_events.jsonl``."""
        if not self._enabled:
            return
        data = {
            "session_id": str(session_id or "").strip(),
            "level": str(level or "info"),
            "component": str(component or "UI"),
            "event_kind": str(event_kind or "log"),
            "render_format": str(render_format or "text"),
            "message": self._truncate(message),
            "visible": bool(visible),
        }
        if ts:
            data["ts"] = str(ts)
        if seq is not None:
            data["seq"] = int(seq)
        if stage not in (None, ""):
            data["stage"] = stage
        if ep_num is not None:
            data["ep_num"] = int(ep_num)
        if arc_num is not None:
            data["arc_num"] = int(arc_num)
        if round_num is not None:
            data["round_num"] = int(round_num)
        if attempt_key:
            data["attempt_key"] = str(attempt_key)
        if selection_value:
            data["selection_value"] = self._truncate(str(selection_value))
        if prompt_id:
            data["prompt_id"] = str(prompt_id)
        if artifact_path:
            data["artifact_path"] = str(artifact_path)
        if meta:
            data["meta"] = self._safe_serialize(meta)
        self._write("ui_events", data)

    # ── internal ─────────────────────────────────────────────

    def _truncate(self, text: str) -> str:
        """프롬프트/응답 절삭."""
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        if len(text) <= self._max_prompt_chars:
            return text
        half = self._max_prompt_chars // 2
        return text[:half] + f"\n... [TRUNCATED {len(text) - self._max_prompt_chars} chars] ...\n" + text[-half:]

    def _safe_serialize(self, obj) -> object:
        """JSON 직렬화 가능한 형태로 변환."""
        if isinstance(obj, str | int | float | bool | type(None)):
            return obj
        if isinstance(obj, list | tuple):
            return [self._safe_serialize(item) for item in obj[:100]]
        if isinstance(obj, dict):
            return {str(k): self._safe_serialize(v) for k, v in list(obj.items())[:100]}
        return str(obj)[:1000]

    def _write(self, category: str, data: dict) -> None:
        """JSONL 한 줄 기록."""
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            filepath = self._log_dir / f"{category}.jsonl"

            record = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
                **data,
            }
            line = json.dumps(record, ensure_ascii=False, default=str)

            # [TF-30-7] Lock으로 rotate + write 원자화 (멀티스레드 interleave 방지)
            with self._write_lock:
                self._maybe_rotate(filepath)
                with open(filepath, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
        except Exception as e:
            self._record_soft_failure(
                operation="write",
                message=f"{category} JSONL write failed",
                exc=e,
                extra={"category": category},
            )
            logging.debug("[SessionLogger] write failed (%s): %s", category, e)

    def _maybe_rotate(self, filepath: Path) -> None:
        """파일 크기 초과 시 로테이션."""
        try:
            if not filepath.exists():
                return
            size = filepath.stat().st_size
            if size < self._max_file_bytes:
                return

            # .1, .2, ... .N 로테이션
            for i in range(self._max_rotations, 1, -1):
                src = filepath.with_suffix(f".jsonl.{i - 1}")
                dst = filepath.with_suffix(f".jsonl.{i}")
                if src.exists():
                    try:
                        if dst.exists():
                            os.remove(dst)
                        os.rename(src, dst)
                    except OSError as rotate_err:
                        self._record_soft_failure(
                            operation="rotate",
                            message="rotated session log rename failed",
                            exc=rotate_err,
                            extra={"src": str(src), "dst": str(dst)},
                        )

            # 현재 파일 → .1
            dst_1 = filepath.with_suffix(".jsonl.1")
            try:
                if dst_1.exists():
                    os.remove(dst_1)
                os.rename(filepath, dst_1)
            except OSError as rotate_err:
                self._record_soft_failure(
                    operation="rotate",
                    message="session log primary rotate failed",
                    exc=rotate_err,
                    extra={"src": str(filepath), "dst": str(dst_1)},
                )
        except Exception as e:
            self._record_soft_failure(
                operation="rotate",
                message="session log rotation failed",
                exc=e,
                extra={"filepath": str(filepath)},
            )
            logging.debug("[SessionLogger] rotation failed: %s", e)

    def _record_soft_failure(
        self,
        *,
        operation: str,
        message: str,
        exc: Exception | None = None,
        extra: dict | None = None,
    ) -> None:
        self._soft_failure_count += 1
        self._last_soft_failure = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            "operation": operation,
            "message": message,
        }
        report_soft_failure(
            component="session_logger",
            operation=operation,
            message=message,
            exc=exc,
            degraded=True,
            user_visible=False,
            learnable=True,
            extra=extra,
            log_dir=self._resolve_soft_failure_log_dir(),
            warning_window_sec=120.0,
        )

    def _resolve_soft_failure_log_dir(self) -> Path:
        if self._log_dir.name == "session":
            return self._log_dir.parent
        return self._log_dir
