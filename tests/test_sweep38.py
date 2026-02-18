from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_semantic_cache_invalidate_and_stats_are_locked():
    src = _read("modules/core/semantic_cache.py")
    invalidate_idx = src.index("def invalidate")
    stats_idx = src.index("def get_stats")
    invalidate_section = src[invalidate_idx:stats_idx]
    stats_section = src[stats_idx : stats_idx + 260]
    assert "with self._lock:" in invalidate_section
    assert "with self._lock:" in stats_section


def test_vec_memory_cursor_cleanup_present_in_critical_methods():
    src = _read("modules/core/vec_memory.py")
    assert (
        "def _ensure_tables" in src
        and "cur.close()" in src[src.index("def _ensure_tables") : src.index("def _embed_text")]
    )
    mem_section = src[src.index("def memorize_v20_episode") : src.index("def retrieve_high_res_context")]
    assert "finally:" in mem_section
    assert "if cur is not None:" in mem_section
    assert "cur.close()" in mem_section
    del_section = src[src.index("def delete_episodes_from") : src.index("def delete_all_episodes")]
    assert "finally:" in del_section
    assert "if cur is not None:" in del_section
    assert "cur.close()" in del_section


def test_adaptive_retry_strategy_uses_lock_for_context_map():
    src = _read("modules/core/adaptive_retry.py")
    strategy_idx = src.index("class AdaptiveRetryStrategy")
    manager_idx = src.index("class AdaptiveRetryManager")
    strategy_section = src[strategy_idx:manager_idx]
    assert "self._lock = threading.Lock()" in strategy_section
    assert "def get_context" in strategy_section and "with self._lock:" in strategy_section
    assert "def reset_context" in strategy_section and "self.contexts.pop(task_id, None)" in strategy_section


def test_adaptive_retry_manager_uses_lock_for_shared_state():
    src = _read("modules/core/adaptive_retry.py")
    manager_idx = src.index("class AdaptiveRetryManager")
    section = src[manager_idx:]
    assert "self._lock = threading.Lock()" in section
    record_idx = section.index("def record_failure")
    guidance_idx = section.index("def get_retry_guidance")
    record_section = section[record_idx:guidance_idx]
    assert "with self._lock:" in record_section
    guidance_section = section[guidance_idx : section.index("def should_trigger_ultimate")]
    assert "with self._lock:" in guidance_section


def test_pass_rate_monitor_lock_guards_core_record_access():
    src = _read("modules/core/pass_rate_monitor.py")
    assert "self._lock = threading.Lock()" in src
    assert (
        "def _save_records" in src
        and "with self._lock:" in src[src.index("def _save_records") : src.index("def record_attempt")]
    )
    rec_section = src[src.index("def record_attempt") : src.index("def get_stage_stats")]
    assert "with self._lock:" in rec_section
    stage_section = src[src.index("def get_stage_stats") : src.index("def get_all_stats")]
    assert "with self._lock:" in stage_section
    arc_section = src[src.index("def get_arc_difficulty") : src.index("def save")]
    assert "with self._lock:" in arc_section


def test_pre_llm_validator_body_physics_regex_uses_dotall():
    src = _read("modules/validation/pre_llm_validator.py")
    triple_idx = src.index("triple_action = re.findall(")
    injury_idx = src.index("injury_action = re.findall(")
    triple_section = src[triple_idx:injury_idx]
    injury_section = src[injury_idx : injury_idx + 260]
    assert "re.DOTALL" in triple_section
    assert "re.DOTALL" in injury_section
