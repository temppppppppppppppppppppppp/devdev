"""[V70] 프롬프트 외부화 로더.

YAML 파일에서 프롬프트 템플릿을 로드하고 변수를 치환하는 유틸리티.
config/prompts/ 디렉토리의 YAML 파일을 읽어 프롬프트를 반환한다.

Usage:
    from modules.core.prompt_loader import PromptLoader

    loader = PromptLoader()
    prompt = loader.load("analyst", "ENRICH_BLOCK_PROMPT_V30",
                         prev_context="...", curr_block="...")
"""

import logging
import os
import threading
from pathlib import Path
from typing import Any, Optional


class PromptLoader:
    """YAML 기반 프롬프트 템플릿 로더.

    - config/prompts/{domain}.yaml에서 프롬프트를 로드
    - {변수} 플레이스홀더를 .format_map()으로 치환
    - 캐싱: 한 번 로드한 YAML은 메모리에 보관
    - fallback: YAML 로드 실패 시 None 반환 (호출측에서 기존 상수 사용)
    """

    _instance: Optional["PromptLoader"] = None
    _cache: dict[str, dict[str, str]] = {}
    _instance_lock = threading.Lock()
    _cache_lock = threading.Lock()

    def __new__(cls) -> "PromptLoader":
        """싱글톤 패턴 — 앱 전체에서 하나의 인스턴스만 사용."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._cache = {}
        return cls._instance

    def __init__(self) -> None:
        # 프로젝트 루트/config/prompts/ 경로 자동 탐색
        self._prompts_dir = self._find_prompts_dir()

    def _find_prompts_dir(self) -> Path:
        """config/prompts/ 디렉토리 경로를 탐색."""
        # 1) 환경변수로 지정된 경우
        env_path = os.getenv("PROMPT_DIR")
        if env_path:
            return Path(env_path)

        # 2) 프로젝트 루트 기준 탐색 (이 파일 위치 기준)
        # modules/core/prompt_loader.py → 프로젝트루트/config/prompts/
        current = Path(__file__).resolve()
        project_root = current.parent.parent.parent  # modules/core/ → modules/ → root
        prompts_dir = project_root / "config" / "prompts"
        return prompts_dir

    def _load_yaml_file(self, domain: str) -> dict[str, str]:
        """YAML 파일을 로드하여 딕셔너리로 반환."""
        with self._cache_lock:
            if domain in self._cache:
                return self._cache[domain]

        yaml_path = self._prompts_dir / f"{domain}.yaml"
        if not yaml_path.exists():
            logging.debug(f"[PromptLoader] YAML not found: {yaml_path}")
            with self._cache_lock:
                self._cache[domain] = {}
            return {}

        try:
            # PyYAML 의존성 회피 — 간단한 YAML 파서 사용
            # 구조: "KEY_NAME: |" 로 시작하는 멀티라인 블록
            import re

            key_pattern = re.compile(r"^([A-Z][A-Z0-9_]+):\s*\|")
            prompts = {}
            current_key = None
            current_lines: list[str] = []
            indent_size = 2  # 기본 인덴트 크기

            with open(yaml_path, encoding="utf-8") as f:
                all_lines = f.readlines()

            for line in all_lines:
                raw = line.rstrip("\n\r")

                # 새 키 감지: "KEY_NAME: |" (대문자로 시작)
                m = key_pattern.match(raw)
                if m:
                    # 이전 키 저장
                    if current_key is not None:
                        # 끝부분 빈 줄 제거
                        while current_lines and current_lines[-1] == "":
                            current_lines.pop()
                        prompts[current_key] = "\n".join(current_lines)

                    current_key = m.group(1)
                    current_lines = []
                    indent_size = 2  # 리셋
                    continue

                # 파일 시작의 주석 (키 할당 전)
                if current_key is None:
                    continue

                # 현재 블록에 속하는 줄
                # 빈 줄은 블록 내 빈 줄로 처리
                if raw.strip() == "":
                    current_lines.append("")
                    continue

                # 들여쓰기된 내용 — 인덴트 제거
                if raw.startswith(" " * indent_size):
                    current_lines.append(raw[indent_size:])
                elif raw.startswith(" ") or raw.startswith("\t"):
                    # 인덴트가 다르면 그냥 추가
                    current_lines.append(raw.lstrip())
                else:
                    # 인덴트 없는 비-키 줄 → 주석이면 무시, 아니면 블록에 포함
                    if raw.strip().startswith("#"):
                        continue
                    current_lines.append(raw)

            # 마지막 키 저장
            if current_key is not None:
                while current_lines and current_lines[-1] == "":
                    current_lines.pop()
                prompts[current_key] = "\n".join(current_lines)

            with self._cache_lock:
                self._cache[domain] = prompts
            logging.debug(f"[PromptLoader] Loaded {len(prompts)} prompts from {domain}.yaml")
            return prompts

        except Exception as e:
            logging.warning(f"[PromptLoader] Failed to load {yaml_path}: {e}")
            with self._cache_lock:
                self._cache[domain] = {}
            return {}

    def load(self, domain: str, key: str, **kwargs: Any) -> str | None:
        """프롬프트 템플릿을 로드하고 변수를 치환.

        Args:
            domain: YAML 파일 이름 (확장자 없이). 예: "analyst", "director"
            key: 프롬프트 키. 예: "ENRICH_BLOCK_PROMPT_V30"
            **kwargs: 템플릿 변수. 예: prev_context="...", curr_block="..."

        Returns:
            치환된 프롬프트 문자열. YAML 파일이 없거나 키가 없으면 None.
        """
        prompts = self._load_yaml_file(domain)
        if key not in prompts:
            return None

        template = prompts[key]

        if kwargs:
            try:
                # format_map은 누락된 키를 그대로 유지
                class SafeDict(dict):
                    def __missing__(self, k: str) -> str:
                        return "{" + k + "}"

                return template.format_map(SafeDict(**kwargs))
            except Exception as e:
                logging.warning(f"[PromptLoader] Template substitution failed for {domain}/{key}: {e}")
                return template

        return template

    def get_raw(self, domain: str, key: str) -> str | None:
        """변수 치환 없이 원본 템플릿 반환."""
        prompts = self._load_yaml_file(domain)
        return prompts.get(key)

    def list_keys(self, domain: str) -> list[str]:
        """도메인의 모든 프롬프트 키 목록 반환."""
        prompts = self._load_yaml_file(domain)
        return list(prompts.keys())

    def invalidate_cache(self, domain: str | None = None) -> None:
        """캐시 무효화. domain 지정 시 해당 도메인만, 없으면 전체 초기화."""
        with self._cache_lock:
            if domain:
                self._cache.pop(domain, None)
            else:
                self._cache.clear()
