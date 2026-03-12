"""[Phase 4B-1] AuditService — 감사 이벤트 버퍼링/기록 서비스

원본: main_a.py:2992-3044 (3개 메서드, 53줄)
Protocol: modules/protocols/app_services.py AuditServiceProtocol
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any


class AuditService:
    """감사 이벤트를 버퍼링하고 파일로 기록하는 서비스.

    Args:
        runtime_audit: SovereignApp.runtime_audit 리스트 참조 공유
        project_paths_fn: () -> paths 또는 None (lazy 접근)
        ui_log_fn: UI 로깅 함수 (실패 시 경고 출력)
    """

    def __init__(
        self,
        runtime_audit: list,
        project_paths_fn: Callable[[], Any],
        ui_log_fn: Callable[[str], None],
    ) -> None:
        self._runtime_audit = runtime_audit
        self._project_paths_fn = project_paths_fn
        self._ui_log = ui_log_fn
        self._buffer: list[dict] = []

    @property
    def buffer(self) -> list[dict]:
        """현재 버퍼 참조 (하위 호환용)"""
        return self._buffer

    # ── audit_event ──────────────────────────────────────────────
    def audit_event(self, event_type: str, message: str, data: dict | None = None) -> None:
        """[V66.1] B-3: 배치 버퍼 방식 — 버퍼에 append, 파일 I/O 지연"""
        event = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": event_type,
            "message": message,
            "data": data or {},
        }
        self._runtime_audit.append(event)
        if len(self._runtime_audit) > 1000:
            self._runtime_audit[:] = self._runtime_audit[-500:]
        self._buffer.append(event)

    # ── flush_audit_buffer ───────────────────────────────────────
    def flush_audit_buffer(self) -> None:
        """[V66.1] B-3: 버퍼를 한 번에 파일 기록."""
        paths = self._project_paths_fn()
        if not self._buffer or paths is None:
            return
        try:
            log_dir = paths.root / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "runtime_audit.jsonl"
            with log_path.open("a", encoding="utf-8") as f:
                for event in self._buffer:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")
            self._buffer.clear()
        except Exception as e:
            self._ui_log(f"⚠️ [Audit] 로그 기록 실패: {e}")

    # ── write_audit_summary ──────────────────────────────────────
    def write_audit_summary(self, tag: str = "snapshot") -> None:
        """[V66.1] B-3: 요약 기록 전 버퍼 flush"""
        self.flush_audit_buffer()
        paths = self._project_paths_fn()
        if paths is None:
            return
        try:
            summary = {
                "tag": tag,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_events": len(self._runtime_audit),
                "counts": {},
                "latest_event_type": "",
                "recent_events": [],
            }
            recent_events = self._runtime_audit[-10:]
            for evt in self._runtime_audit[-200:]:
                summary["counts"][evt["type"]] = summary["counts"].get(evt["type"], 0) + 1
            if recent_events:
                summary["latest_event_type"] = str(recent_events[-1].get("type", "") or "")
                summary["recent_events"] = [
                    {
                        "type": str(evt.get("type", "") or ""),
                        "message": str(evt.get("message", "") or "")[:160],
                    }
                    for evt in recent_events
                ]
            log_dir = paths.root / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            summary_path = log_dir / "runtime_audit_summary.json"
            summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            self._ui_log(f"⚠️ [Audit] 요약 기록 실패: {e}")
