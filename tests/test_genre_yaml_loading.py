"""
장르 가드 YAML 로딩 테스트
- YAML 파싱 및 필수 키 검증
- Guard의 YAML 로딩 동작 검증
- YAML 누락 시 하드코딩 fallback 검증
"""

from pathlib import Path

import pytest
import yaml

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config" / "genres"

GENRE_KEYS = [
    "wuxia",
    "hunter",
    "investment",
    "actor",
    "alt_history",
    "composer",
    "cooking",
    "fantasy",
    "medical",
    "sports",
]


class TestAllGenreYamlsValid:
    """10개 장르 YAML 파일 존재/파싱/필수 키 검증."""

    @pytest.mark.parametrize("genre_key", GENRE_KEYS)
    def test_yaml_exists_and_parseable(self, genre_key):
        yaml_path = CONFIG_DIR / f"{genre_key}.yaml"
        assert yaml_path.exists(), f"{genre_key}.yaml not found"
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), f"{genre_key}.yaml is not a dict"

    @pytest.mark.parametrize("genre_key", GENRE_KEYS)
    def test_yaml_has_required_keys(self, genre_key):
        yaml_path = CONFIG_DIR / f"{genre_key}.yaml"
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "forbidden_terms" in data, f"{genre_key}.yaml missing forbidden_terms"
        assert "mandatory_concepts" in data, f"{genre_key}.yaml missing mandatory_concepts"
        assert isinstance(data["forbidden_terms"], list)
        assert isinstance(data["mandatory_concepts"], list)
        assert len(data["forbidden_terms"]) > 0
        assert len(data["mandatory_concepts"]) > 0


class TestYamlLoadedByGuards:
    """Guard 인스턴스가 YAML 데이터를 정상 로딩하는지 검증."""

    def test_wuxia_loads_from_yaml(self):
        from modules.core.genre_guards.wuxia_guard import WuxiaGuard

        guard = WuxiaGuard()
        assert len(guard.FORBIDDEN_TERMS) >= 40
        assert "상태창" in guard.FORBIDDEN_TERMS

    def test_hunter_loads_from_yaml(self):
        from modules.core.genre_guards.hunter_guard import HunterGuard

        guard = HunterGuard()
        assert len(guard.FORBIDDEN_TERMS) >= 30
        assert len(guard.ALLOWED_TERMS) >= 10

    def test_all_guards_instantiate(self):
        from modules.core.genre_guards import create_genre_guard

        for genre_key in GENRE_KEYS:
            guard = create_genre_guard(genre_key)
            assert guard is not None, f"Failed to create guard for {genre_key}"
            assert hasattr(guard, "FORBIDDEN_TERMS")
            assert hasattr(guard, "MANDATORY_CONCEPTS")


class TestYamlFallback:
    """YAML 누락 시 하드코딩 fallback 동작 검증."""

    def test_missing_yaml_uses_hardcoded(self, tmp_path, monkeypatch):
        from modules.core.genre_guards.base_guard import BaseGuard
        from modules.core.genre_guards.wuxia_guard import WuxiaGuard

        monkeypatch.setattr(BaseGuard, "_CONFIG_DIR", tmp_path)
        guard = WuxiaGuard()
        assert len(guard.FORBIDDEN_TERMS) >= 40
