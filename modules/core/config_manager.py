import logging
from pathlib import Path
from typing import Any


class ConfigManager:
    """[V20 Sovereign Config] 모델 티어 배정 및 프로젝트 경로 체계를 총괄 관리

    [Phase 5-B-1] validation.yaml 로더 + 안전 fallback API 추가
    """

    # [Phase 5-B-1] YAML 설정 파일 경로 (프로젝트 루트 기준)
    _SETTINGS_DIR = "config/settings"
    _VALIDATION_YAML = "validation.yaml"

    def __init__(self) -> None:
        self.root = Path.cwd()

        # 1. 프로젝트 폴더 생성
        self.projects_dir = self.root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        # 2. [🔥 추가] 로그 폴더 생성 로직
        self.logs_dir = self.root / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        logging.info(f"📁 [System] 필수 경로 점검 완료: {self.logs_dir}")

        # [V60.24] 모든 모델을 Gemini 3로 통일
        # Stage 1~4: 모든 단계에서 Gemini 3 Pro 사용
        self.settings = {
            "models": {
                "analyst": "gemini-3-pro-preview",  # [V60.24] Gemini 3
                # [V65] architect 삭제 (레거시 에이전트 제거)
                "writer": "gemini-3-pro-preview",  # 7,000자 고해상도 집필
                "director": "gemini-3-pro-preview",  # [V60.24] Gemini 3
                "manager": "gemini-3-pro-preview",  # [V60.24] Gemini 3
                "editor": "gemini-3-pro-preview",  # [V60.24] Gemini 3
            },
            "limits": {
                "max_retries": 10,  # V20 매니페스토 기준 재시도 횟수
                "target_manuscript_length": 5000,  # 목표 원고 자수
            },
        }

        # [Phase 5-B-1] validation settings 캐시 (lazy load)
        self._validation_settings: dict | None = None

    def get_v20_project_paths(self, project_name: str) -> dict:
        """V20 표준 폴더 구조 정의"""
        base = self.projects_dir / project_name
        return {
            "root": base,
            "config": base / "config",
            "db": base / "db",
            "drafts": base / "drafts",
            "logs": base / "logs",
            "blueprints": base / "blueprints",  # Stage 3 설계도 폴더
            "memory": base / "memory",
        }

    def get_model_for_agent(self, agent_role: str) -> str:
        return self.settings["models"].get(agent_role, "gemini-2.5-flash")

    def __getitem__(self, key: str) -> dict:
        return self.settings[key]

    # ══════════════════════════════════════════════════════════
    # [Phase 5-B-1] Validation Settings API
    # ══════════════════════════════════════════════════════════

    def load_settings(self, *, force_reload: bool = False) -> dict:
        """[Phase 5-B-1] validation.yaml 로드 (캐시 + 안전 fallback).

        - 파일 누락/파싱 실패 시 빈 dict 반환 (기존 하드코드 동작 유지)
        - force_reload=True 시 캐시 무시하고 재로드
        """
        if self._validation_settings is not None and not force_reload:
            return self._validation_settings

        yaml_path = self.root / self._SETTINGS_DIR / self._VALIDATION_YAML
        if not yaml_path.exists():
            logging.warning(f"[Phase 5-B-1] validation.yaml 없음: {yaml_path} — 기본값 사용")
            self._validation_settings = {}
            return self._validation_settings

        try:
            import yaml

            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._validation_settings = data if isinstance(data, dict) else {}
            logging.info(f"[Phase 5-B-1] validation.yaml 로드 완료 ({len(self._validation_settings)} 섹션)")
        except Exception as e:
            logging.warning(f"[Phase 5-B-1] validation.yaml 파싱 실패 — 기본값 사용: {e}")
            self._validation_settings = {}

        return self._validation_settings

    def _get_nested(self, dotted_key: str, default: Any = None) -> Any:
        """[Phase 5-B-1] 점(.) 구분 키로 중첩 dict 탐색.

        예: "manuscript.min_length" → settings["manuscript"]["min_length"]
        키 누락/타입 불일치 시 default 반환.
        """
        settings = self.load_settings()
        parts = dotted_key.split(".")
        current: Any = settings
        for part in parts:
            if not isinstance(current, dict):
                return default
            current = current.get(part)
            if current is None:
                return default
        return current

    def get_guard_threshold(self, key: str, default: Any = None) -> Any:
        """[Phase 5-B-1] 가드/검증 임계값 조회.

        Args:
            key: 점(.) 구분 키 (예: "manuscript.min_length", "scoring.default_pass_threshold")
            default: 키 누락 시 반환할 기본값 (기존 하드코드 값)

        Returns:
            YAML 값 또는 default. 타입이 default와 다르면 default 반환.
        """
        value = self._get_nested(key)
        if value is None:
            return default
        # 타입 안전: default가 주어지고 타입이 다르면 fallback
        if default is not None and not isinstance(value, type(default)):
            # int/float 호환은 허용
            if isinstance(default, int | float) and isinstance(value, int | float):
                return type(default)(value)
            logging.warning(
                f"[Phase 5-B-1] 타입 불일치: {key} = {type(value).__name__}, "
                f"기대 {type(default).__name__} — 기본값 사용"
            )
            return default
        return value

    def get_validation_policy(self, key: str, default: Any = None) -> Any:
        """[Phase 5-B-1] 검증 정책 조회. get_guard_threshold와 동일 로직."""
        return self.get_guard_threshold(key, default)

    def get_feature_flag(self, key: str, default: bool = False) -> bool:
        """[Phase 5-B-1] 기능 플래그 조회.

        Args:
            key: 플래그 이름 (예: "enable_patch_mode")
            default: 키 누락 시 기본값

        Returns:
            bool 값 (비bool 타입이면 default 반환)
        """
        value = self._get_nested(f"feature_flags.{key}")
        if value is None:
            return default
        if not isinstance(value, bool):
            logging.warning(f"[Phase 5-B-1] feature_flag 타입 불일치: {key} = {type(value).__name__} — 기본값 사용")
            return default
        return value

    def invalidate_settings_cache(self) -> None:
        """[Phase 5-B-1] 캐시 무효화. 다음 조회 시 YAML 재로드."""
        self._validation_settings = None
