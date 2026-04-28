"""
[V70] PromptLoader 단위 테스트

modules/core/prompt_loader.py의 싱글톤 로더, YAML 파싱, 변수 치환 검증.
"""

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from modules.core.prompt_loader import PromptLoader, SafeDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _code_text() -> str:
    """Return concatenated production Python source used for prompt lookups."""
    parts = []
    modules_root = PROJECT_ROOT / "modules"
    for py_file in modules_root.rglob("*.py"):
        parts.append(py_file.read_text(encoding="utf-8", errors="ignore"))
    parts.append((PROJECT_ROOT / "main_a.py").read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(parts)


def _remaining_yaml_keys() -> dict[str, set[str]]:
    key_re = re.compile(r"^([A-Z][A-Z0-9_]+):\s*\|\s*$", re.MULTILINE)
    out: dict[str, set[str]] = {}
    for yaml_file in sorted((PROJECT_ROOT / "config" / "prompts").glob("*.yaml")):
        keys = set(key_re.findall(yaml_file.read_text(encoding="utf-8")))
        out[yaml_file.stem] = keys
    return out


def _load_references_from_code() -> dict[str, set[str]]:
    load_re = re.compile(
        r"""(?:[A-Za-z_][A-Za-z0-9_]*|PromptLoader\(\))\s*\.\s*load\(
            \s*["']([a-z0-9_]+)["']\s*,\s*["']([A-Z0-9_]+)["']
        """,
        re.VERBOSE,
    )
    refs: dict[str, set[str]] = {}
    for domain, key in load_re.findall(_code_text()):
        refs.setdefault(domain, set()).add(key)
    return refs


@pytest.fixture(autouse=True)
def reset_singleton():
    """각 테스트 전 싱글톤 리셋"""
    PromptLoader._instance = None
    PromptLoader._cache = {}
    PromptLoader._metadata_cache = {}
    yield
    PromptLoader._instance = None
    PromptLoader._cache = {}
    PromptLoader._metadata_cache = {}


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
_version: "v1.2"
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


class TestMetadata:
    def test_get_metadata_reads_version(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            metadata = loader.get_metadata("test_domain")
            assert metadata["_version"] == "v1.2"

    def test_get_prompt_version_prefers_yaml_metadata(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            assert loader.get_prompt_version("test_domain") == "v1.2"

    def test_resolve_prompt_reports_yaml_authority(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            prompt, contract = loader.resolve_prompt("test_domain", "SIMPLE_PROMPT")
            assert prompt is not None
            assert contract["available"] is True
            assert contract["used_fallback"] is False
            assert contract["effective_source"] == "config/prompts/test_domain.yaml:SIMPLE_PROMPT"
            assert contract["prompt_version"] == "test_domain@v1.2"

    def test_resolve_prompt_uses_fallback_contract_when_key_missing(self, sample_yaml):
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            prompt, contract = loader.resolve_prompt(
                "test_domain",
                "MISSING_PROMPT",
                fallback="fallback text",
                fallback_source="inline_test_fallback",
            )
            assert prompt == "fallback text"
            assert contract["available"] is True
            assert contract["used_fallback"] is True
            assert contract["effective_source"] == "inline_test_fallback"

    def test_compose_version_tag_preserves_order_and_dedups(self, sample_yaml):
        other_yaml = sample_yaml / "other.yaml"
        other_yaml.write_text('_version: "v9"\nOTHER_PROMPT: |\n  hello\n', encoding="utf-8")
        loader = PromptLoader()
        with patch.object(loader, "_prompts_dir", sample_yaml):
            tag = loader.compose_version_tag("test_domain", "other", "test_domain")
            assert tag == "test_domain@v1.2|other@v9"


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
            cache_key = (str(sample_yaml), "test_domain")
            assert cache_key in loader._cache

            # 특정 도메인 무효화
            loader.invalidate_cache("test_domain")
            assert cache_key not in loader._cache

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

    def test_chief_writer_prompts_allow_required_scene_headers(self):
        loader = PromptLoader()
        writing_guidelines = loader.load("chief_writer", "WRITING_GUIDELINES_SECTION")
        patch_prompt = loader.load(
            "chief_writer",
            "PATCH_MODE_PROMPT",
            original_char_count=5000,
            min_char_target=4500,
            style_guide="문체 유지",
            feedback_text="씬 헤더 누락",
            original_manuscript="원고",
        )
        structural_prompt = loader.load(
            "chief_writer",
            "PATCH_MODE_STRUCTURAL_PROMPT",
            style_guide="문체 유지",
            feedback_text="scene separation missing",
            focus_label="scene_header",
            scene_plan="scene_1",
            target_scene_ids="scene_1",
            boundary_context="",
            target_scene_payload="",
        )

        assert "`### 씬 N: 제목`은 예외" in writing_guidelines
        assert "원본에 있는 `### 씬 N: 제목` 씬 헤더는 보존" in patch_prompt
        assert "scene header 이외의 Markdown" in structural_prompt

    def test_emotion_tracker_yaml_loads(self):
        loader = PromptLoader()
        keys = loader.list_keys("emotion_tracker")
        assert len(keys) > 0

    def test_writing_directive_prompt_loads_with_literal_json_braces(self):
        loader = PromptLoader()
        prompt = loader.load(
            "writing_directive",
            "WRITING_DIRECTIVE_SYSTEM",
            N=3,
            pattern_summary="요약",
            blueprint_summary="블루프린트",
        )

        assert prompt is not None
        assert '"ending_style"' in prompt
        assert '"npc_directives"' in prompt
        assert "{N}" not in prompt


class TestTier5PromptHygiene:
    def test_deleted_yaml_keys_not_referenced(self):
        refs = _load_references_from_code()
        deleted_keys = {
            "SUGGEST_EXPRESSION_IMPROVEMENTS__PROMPT",
            "INIT_EXEMPLARS__CONTENT",
            "CHECK_CAUSAL_ERRORS__PROMPT",
            "RE_ENRICH_WITH_CAUSAL_FIX__PROMPT",
            "BLOCK_ENRICHMENT_PROMPT",
            "ENRICHMENT_VALIDATION_PROMPT",
            "DIRECTOR_BLOCK_AUDIT_PROMPT",
            "ASSESS_CHARACTER_LOGIC__PROMPT",
            "VALIDATE_ENTITY_CONSISTENCY__PROMPT",
            "CHECK_MANUSCRIPT_HISTORY_WITH_CACHE__PROMPT",
            "COMPARE_AND_SELECT_BLUEPRINT__COMPARISON_PROMPT",
            "STAGE3_MEDICAL",
            "GENERATE_CORRECTION_PROMPT__PROMPT",
            "DEEP_LLM_ANALYSIS__PROMPT",
            "GENERATE_ANTI_PATTERNS__PROMPT",
            "GENERATE_ARC_DRIVE__DYNAMIC_PROMPT",
            "WRITE_V20_MANUSCRIPT__DYNAMIC_PROMPT",
            "CORRECTION_PROMPT",
            "ARC_CRITIQUE_PROMPT",
            "CONSENSUS_VALIDATION_PROMPT",
            "ARC_CONTINUITY_INSPECTION_PROMPT",
            "JOINT_DOCS_EXTRACTION_PROMPT",
            "CONTINUITY_INSPECTION_PROMPT",
            "MANUSCRIPT_CONTINUITY_PROMPT",
            "UPDATE_STATE_PROMPT_V25",
            "PREFLIGHT_ANALYSIS_PROMPT",
            "STATE_EXTRACTION_PROMPT",
            "UNIFIED_VALIDATION_PROMPT",
            "EPISODE_TEMPLATE",
            "ARC_SYNTHESIS_PROMPT",
        }
        for domain_keys in refs.values():
            assert domain_keys.isdisjoint(deleted_keys)

    def test_safedict_format_map_resilience(self):
        template = "A={a}, B={b}, C={c}"
        rendered = template.format_map(SafeDict(a="1", c="3"))
        assert rendered == "A=1, B={b}, C=3"

    def test_remaining_yaml_keys_all_referenced(self):
        code = _code_text()
        missing = {}
        for domain, keys in _remaining_yaml_keys().items():
            missing_keys = sorted(k for k in keys if f'"{k}"' not in code and f"'{k}'" not in code)
            if missing_keys:
                missing[domain] = missing_keys
        assert missing == {}

    def test_no_dual_definition_yaml_inline(self):
        # Keys removed from YAML should remain only as inline constants, not in YAML.
        removed_keys = {
            "CORRECTION_PROMPT",
            "ARC_CRITIQUE_PROMPT",
            "CONSENSUS_VALIDATION_PROMPT",
            "ARC_CONTINUITY_INSPECTION_PROMPT",
            "JOINT_DOCS_EXTRACTION_PROMPT",
            "CONTINUITY_INSPECTION_PROMPT",
            "MANUSCRIPT_CONTINUITY_PROMPT",
            "UPDATE_STATE_PROMPT_V25",
            "PREFLIGHT_ANALYSIS_PROMPT",
            "STATE_EXTRACTION_PROMPT",
            "UNIFIED_VALIDATION_PROMPT",
            "EPISODE_TEMPLATE",
            "ARC_SYNTHESIS_PROMPT",
        }
        remaining_key_set = set()
        for keys in _remaining_yaml_keys().values():
            remaining_key_set.update(keys)
        assert removed_keys.isdisjoint(remaining_key_set)
