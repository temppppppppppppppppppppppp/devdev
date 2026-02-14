"""[Phase 5-B-2c] 공유 _threshold() 헬퍼 — validation 모듈 전용

ConfigManager를 지연 초기화하고, validation.yaml 에서 임계값을 조회합니다.
YAML 파일 누락/키 누락/타입 불일치 시 항상 default (기존 하드코드값) 반환.
"""

from typing import Any


def _threshold(key: str, default: Any) -> Any:
    """YAML 우선, 실패 시 하드코드 default 반환."""
    if not hasattr(_threshold, "_cfg"):
        try:
            from modules.core.config_manager import ConfigManager

            _threshold._cfg = ConfigManager()
        except Exception:
            _threshold._cfg = None

    if _threshold._cfg:
        return _threshold._cfg.get_guard_threshold(key, default)
    return default
