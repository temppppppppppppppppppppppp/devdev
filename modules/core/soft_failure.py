"""Structured reporting for non-blocking failures."""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_WARN_LOCK = threading.Lock()
_LAST_WARNING_AT: dict[tuple[str, str, str], float] = {}


def _should_emit_warning(key: tuple[str, str, str], window_sec: float) -> bool:
    now = time.monotonic()
    with _WARN_LOCK:
        last = _LAST_WARNING_AT.get(key, 0.0)
        if now - last < window_sec:
            return False
        _LAST_WARNING_AT[key] = now
        return True


def _normalize_log_dir(log_dir: str | Path | None) -> Path | None:
    if log_dir is None:
        return None
    try:
        return Path(log_dir)
    except Exception:
        return None


def build_soft_failure_event(
    *,
    component: str,
    operation: str,
    message: str,
    exc: Exception | None = None,
    severity: str = "warning",
    stage: int | str | None = None,
    ep_num: int | None = None,
    run_id: str | None = None,
    degraded: bool = True,
    user_visible: bool = False,
    learnable: bool = False,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "component": component,
        "operation": operation,
        "severity": severity,
        "message": str(message or "").strip(),
        "degraded": bool(degraded),
        "user_visible": bool(user_visible),
        "learnable": bool(learnable),
    }
    if stage is not None:
        event["stage"] = stage
    if ep_num is not None:
        event["ep_num"] = ep_num
    if run_id:
        event["run_id"] = run_id
    if exc is not None:
        event["exception_type"] = type(exc).__name__
        event["exception"] = str(exc)[:300]
    if extra:
        event["extra"] = extra
    return event


def report_soft_failure(
    *,
    component: str,
    operation: str,
    message: str,
    exc: Exception | None = None,
    severity: str = "warning",
    stage: int | str | None = None,
    ep_num: int | None = None,
    run_id: str | None = None,
    degraded: bool = True,
    user_visible: bool = False,
    learnable: bool = False,
    extra: dict[str, Any] | None = None,
    log_dir: str | Path | None = None,
    audit_event=None,
    warning_window_sec: float = 60.0,
) -> dict[str, Any]:
    """Emit a throttled warning and persist a structured soft-failure record."""

    event = build_soft_failure_event(
        component=component,
        operation=operation,
        message=message,
        exc=exc,
        severity=severity,
        stage=stage,
        ep_num=ep_num,
        run_id=run_id,
        degraded=degraded,
        user_visible=user_visible,
        learnable=learnable,
        extra=extra,
    )

    warn_key = (component, operation, str(type(exc).__name__ if exc else ""))
    if _should_emit_warning(warn_key, warning_window_sec):
        suffix = f" ({type(exc).__name__}: {str(exc)[:160]})" if exc is not None else ""
        logging.warning("[SOFT_FAILURE] %s.%s: %s%s", component, operation, message, suffix)

    if callable(audit_event):
        try:
            audit_event("soft_failure", f"{component}.{operation}: {message}", event)
        except Exception as audit_err:
            if _should_emit_warning((component, "audit_event", ""), 300.0):
                logging.warning("[SOFT_FAILURE] audit_event relay failed: %s", str(audit_err)[:160])

    normalized_dir = _normalize_log_dir(log_dir)
    if normalized_dir is not None:
        try:
            normalized_dir.mkdir(parents=True, exist_ok=True)
            with (normalized_dir / "soft_failures.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        except Exception as persist_err:
            if _should_emit_warning((component, "persist", ""), 300.0):
                logging.warning("[SOFT_FAILURE] persist failed for %s.%s: %s", component, operation, str(persist_err)[:160])

    return event
