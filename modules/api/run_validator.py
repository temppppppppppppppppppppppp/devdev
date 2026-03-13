"""T4 — /run 요청 검증 로직.

계약 근거: docs/implementation/api-contract-v1.yaml
키 근거  : docs/implementation/prompt-map-v1.json

오류코드:
    INVALID_KEY            400  허용되지 않은 menu key
    SUB_KEY_REQUIRED       400  key=0 인데 sub_key 누락
    SUB_KEY_NOT_ALLOWED    400  key!=0 인데 sub_key 전달
    INVALID_SUB_KEY        400  key=0 의 sub_key 가 허용 범위 밖
    RUN_ALREADY_ACTIVE     409  실행 중 중복 run 요청
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ─── 허용 상수 ──────────────────────────────────────────────────────────────

ALLOWED_KEYS: frozenset[str] = frozenset(
    {"0", "1", "2", "3", "4", "5", "6", "7", "44", "77", "88", "99"}
)
ALLOWED_SUB_KEYS: frozenset[str] = frozenset({"0", "1", "2", "3", "4", "5", "6", "7"})
RISK_KEYS: frozenset[str] = frozenset({"44", "77", "88", "99"})
ACTIVE_RUN_STATES: frozenset[str] = frozenset({"starting", "running", "stopping"})


# ─── 결과 타입 ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    http_status: int
    code: str
    message: str


_OK = ValidationResult(ok=True, http_status=202, code="OK", message="Request accepted.")


def _err(http_status: int, code: str, message: str) -> ValidationResult:
    return ValidationResult(ok=False, http_status=http_status, code=code, message=message)


# ─── 검증 함수 ───────────────────────────────────────────────────────────────

def validate_run_request(
    key: str,
    sub_key: Optional[str],
    runner_state: str,
) -> ValidationResult:
    """POST /run 요청의 key/sub_key/상태를 검증한다.

    Args:
        key: 메뉴 키 문자열 (e.g. "0", "44").
        sub_key: Stage 0 하위 옵션 키. key!=0 이면 None 이어야 한다.
        runner_state: 현재 러너 상태 ("idle" | "running" | ...).

    Returns:
        ValidationResult — ok=True 이면 통과, False 이면 오류 코드·HTTP 상태 포함.
    """
    # 1. key 화이트리스트
    if key not in ALLOWED_KEYS:
        logger.warning("INVALID_KEY key=%r", key)
        return _err(400, "INVALID_KEY", f"Key '{key}' is not allowed.")

    # 2. key=0: sub_key 필수 + 범위 검증
    if key == "0":
        if not sub_key:
            logger.warning("SUB_KEY_REQUIRED key=0 sub_key=%r", sub_key)
            return _err(400, "SUB_KEY_REQUIRED", "sub_key is required when key=0.")
        if sub_key not in ALLOWED_SUB_KEYS:
            logger.warning("INVALID_SUB_KEY key=0 sub_key=%r", sub_key)
            return _err(400, "INVALID_SUB_KEY", f"sub_key '{sub_key}' is not allowed for key=0.")

    # 3. key!=0: sub_key 금지
    elif sub_key is not None:
        logger.warning("SUB_KEY_NOT_ALLOWED key=%r sub_key=%r", key, sub_key)
        return _err(400, "SUB_KEY_NOT_ALLOWED", f"sub_key is not allowed for key={key}.")

    # 4. 중복 실행 차단
    if runner_state in ACTIVE_RUN_STATES:
        logger.warning("RUN_ALREADY_ACTIVE key=%r", key)
        return _err(409, "RUN_ALREADY_ACTIVE", "Another run is already active.")

    return _OK
