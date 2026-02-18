from pathlib import Path

from modules.core.context_compression import ContextCompressor


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_rollback_episode_source_invalidates_director_caches():
    src = _read("main_a.py")
    section = src[src.index("def _rollback_episode") : src.index("def _wipe_production_data")]
    assert "_director._caching.manuscript_cache_name = None" in section
    assert "_director._caching._cached_manuscript_count = 0" in section
    assert "_director._continuity._cached_manuscript_ep = None" in section
    assert "_director._continuity._cached_blueprint_ep = None" in section


def test_rewind_stage_2_source_invalidates_state_related_caches():
    src = _read("main_a.py")
    section = src[src.index("def _rewind_stage_2") : src.index("def _rollback_episode")]
    assert "self._cumulative_state_cache = None" in section
    assert "self._cumulative_state_cache_key = 0" in section
    assert "self._prompt_builder._item_timeline_cache = {}" in section
    assert "self._narrative_summaries_cache = None" in section
    assert "_se.invalidate_cache()" in section


def test_base_agent_source_has_inner_network_retry_loop():
    src = _read("modules/domain/agents/base_agent.py")
    assert "attempt = 0" in src
    assert "while attempt < MAX_CONTINUATIONS:" in src
    assert "if self._is_network_error(api_error) and network_retry_count < self.MAX_NETWORK_RETRIES:" in src
    assert "attempt += 1" in src


def test_context_compressor_handles_deep_nested_dict_without_recursion_error():
    compressor = ContextCompressor(max_field_length=50)
    deep = {"value": "x"}
    for _ in range(50):
        deep = {"nested": deep}

    out = compressor._process_field("root", deep)
    assert isinstance(out, dict)


def test_context_compressor_source_has_depth_guard():
    src = _read("modules/core/context_compression.py")
    assert "def _process_field(self, key: str, value: Any, _depth: int = 0) -> Any:" in src
    assert "if _depth > 20:" in src
    assert "self._process_field(k, v, _depth + 1)" in src
