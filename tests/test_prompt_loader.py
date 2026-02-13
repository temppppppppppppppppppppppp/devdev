"""
[V70] PromptLoader 단위 테스트

modules/core/prompt_loader.py의 싱글톤 로더, YAML 파싱, 변수 치환 검증.
"""

from unittest.mock import patch

import pytest

from modules.core.prompt_loader import PromptLoader


@pytest.fixture(autouse=True)
def reset_singleton():
    """각 테스트 전 싱글톤 리셋"""
    PromptLoader._instance = None
    PromptLoader._cache = {}
    yield
    PromptLoader._instance = None
    PromptLoader._cache = {}


@pytest.fixture
def temp_prompts_dir(tmp_path):
    """임시 프롬프트 YAML 디렉토리"""
    prompts_dir = tmp_path / "config" / "prompts"
    prompts_dir.mkdir(parents=True)
    return prompts_dir


@pytest.fixture
def sample_yaml(temp_prompts_dir):
    """샘플 YAML 프롬프트 파일"""
    content = """# 테스트용 프롬프트 파일
GREETING_PROMPT: |
  안녕하세요, {name}님!
  오늘의 장르는 {genre}입니다.

SIMPLE_PROMPT: |
  이것은 단순 프롬프트입니다.
  변수가 없습니다.

MULTI_VAR_PROMPT: |
  Arc {arc_no} 설계서
  장르: {genre}
  주인공: {protagonist}
"""
    yaml_path = temp_prompts_dir / "test_domain.yaml"
    yaml_path.write_text(content, encoding="utf-8")
    return temp_prompts_dir


# ============================================================
# 싱글톤 패턴
# ============================================================


class TestSingleton:
    """싱글톤 패턴 검증"""

    def test_same_instance(self):
        a = PromptLoader()
        b = PromptLoader()
        assert a is b

    def test_cache_shared(self):
        a = PromptLoader()
        b = PromptLoader()
        assert a._cache is b._cache


# ============================================================
# YAML 로드
# ============================================================


class TestYamlLoading:
    """YAML 파일 로드 및 파싱 검증"""

    def test_load_nonexistent_domain(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            result = loader.load("nonexistent", "ANY_KEY")
            assert result is None

    def test_load_existing_key(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            result = loader.load("test_domain", "SIMPLE_PROMPT")
            assert result is not None
            assert "단순 프롬프트" in result

    def test_load_nonexistent_key(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            result = loader.load("test_domain", "NONEXISTENT_KEY")
            assert result is None

    def test_variable_substitution(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            result = loader.load("test_domain", "GREETING_PROMPT", name="이청풍", genre="무협")
            assert result is not None
            assert "이청풍" in result
            assert "무협" in result

    def test_missing_variable_preserved(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            result = loader.load(
                "test_domain",
                "GREETING_PROMPT",
                name="이청풍",
                # genre 누락 — SafeDict이 {genre}를 그대로 유지
            )
            assert result is not None
            assert "이청풍" in result
            assert "{genre}" in result

    def test_multi_variable_substitution(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            result = loader.load("test_domain", "MULTI_VAR_PROMPT", arc_no=3, genre="무협", protagonist="이청풍")
            assert "3" in result
            assert "무협" in result
            assert "이청풍" in result


# ============================================================
# get_raw
# ============================================================


class TestGetRaw:
    """원본 템플릿 반환 검증"""

    def test_get_raw_returns_template(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            raw = loader.get_raw("test_domain", "GREETING_PROMPT")
            assert raw is not None
            assert "{name}" in raw
            assert "{genre}" in raw

    def test_get_raw_nonexistent_returns_none(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            raw = loader.get_raw("test_domain", "NO_SUCH_KEY")
            assert raw is None


# ============================================================
# list_keys
# ============================================================


class TestListKeys:
    """도메인 키 목록 반환 검증"""

    def test_list_keys(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            keys = loader.list_keys("test_domain")
            assert "GREETING_PROMPT" in keys
            assert "SIMPLE_PROMPT" in keys
            assert "MULTI_VAR_PROMPT" in keys
            assert len(keys) == 3

    def test_list_keys_nonexistent_domain(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            keys = loader.list_keys("nonexistent")
            assert keys == []


# ============================================================
# invalidate_cache
# ============================================================


class TestInvalidateCache:
    """캐시 무효화 검증"""

    def test_invalidate_specific_domain(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            # 캐시 로드
            loader.load("test_domain", "SIMPLE_PROMPT")
            assert "test_domain" in loader._cache

            # 특정 도메인 무효화
            loader.invalidate_cache("test_domain")
            assert "test_domain" not in loader._cache

    def test_invalidate_all(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            loader.load("test_domain", "SIMPLE_PROMPT")
            loader.invalidate_cache()
            assert loader._cache == {}


# ============================================================
# 실제 config/prompts/ YAML 파일 검증
# ============================================================


class TestRealYamlFiles:
    """실제 프로젝트의 config/prompts/ 디렉토리 YAML 파일 로드 검증"""

    def test_analyst_yaml_loads(self):
        loader = PromptLoader()
        keys = loader.list_keys("analyst")
        # analyst.yaml이 존재하고 키가 있어야 함
        assert len(keys) > 0

    def test_director_yaml_loads(self):
        loader = PromptLoader()
        keys = loader.list_keys("director")
        assert len(keys) > 0

    def test_ensemble_yaml_loads(self):
        loader = PromptLoader()
        keys = loader.list_keys("ensemble")
        assert len(keys) > 0

    def test_chief_writer_yaml_loads(self):
        loader = PromptLoader()
        keys = loader.list_keys("chief_writer")
        assert len(keys) > 0

    def test_genre_stage_yaml_loads(self):
        loader = PromptLoader()
        keys = loader.list_keys("genre_stage")
        assert len(keys) > 0
