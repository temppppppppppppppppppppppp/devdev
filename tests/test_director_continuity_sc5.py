"""SC-5 tests for Director continuity prompt memory injection."""

from unittest.mock import MagicMock

from modules.domain.agents.director_continuity import DirectorContinuityValidator


def _make_validator():
    director = MagicMock()
    director.manuscript_history_check_enabled = True
    director.history_check_max_episodes = 30
    director._escape_braces.side_effect = lambda value: value
    director.context = MagicMock(project_name="test_project")
    director.merge_contexts_for_caching.return_value = "cached-context"
    director._get_or_create_context_cache.return_value = {"cached": False, "cache_name": None}
    director._ask_with_cached_context.return_value = '{"decision":"PASS","conflicts":[],"summary":"ok"}'
    director.ask.return_value = '{"decision":"PASS","conflicts":[],"summary":"ok"}'
    director._extract_json_robust.return_value = {"decision": "PASS", "conflicts": [], "summary": "ok"}

    validator = DirectorContinuityValidator(director)
    validator._prompt_loader.load = MagicMock(return_value="BASE_PROMPT")
    return validator, director


def test_memory_context_default_empty():
    validator, director = _make_validator()
    db = MagicMock()
    db.get_recent_manuscripts.return_value = [{"ep_num": 2, "content": "previous manuscript"}]

    result = validator.check_manuscript_continuity_with_cache(
        new_manuscript="current manuscript",
        ep_num=3,
        db=db,
    )

    assert result["decision"] == "PASS"
    prompt = director.ask.call_args.args[0]
    assert "[SC-5]" not in prompt


def test_memory_context_injected_into_prompt():
    validator, director = _make_validator()
    db = MagicMock()
    db.get_recent_manuscripts.return_value = [{"ep_num": 2, "content": "previous manuscript"}]

    result = validator.check_manuscript_continuity_with_cache(
        new_manuscript="current manuscript",
        ep_num=3,
        db=db,
        memory_context="[SC:npc] npc context block",
    )

    assert result["decision"] == "PASS"
    prompt = director.ask.call_args.args[0]
    assert "[SC-5]" in prompt
    assert "[SC:npc] npc context block" in prompt


def test_memory_context_in_history_conflicts():
    validator, director = _make_validator()

    result = validator.check_manuscript_history_conflicts(
        ep_num=3,
        current_manuscript="current manuscript",
        manuscript_history=[{"ep_num": 1, "text": "previous manuscript"}],
        use_summary=False,
        memory_context="[SC:event] event context block",
    )

    assert result["decision"] == "PASS"
    prompt = director.ask.call_args.args[0]
    assert "[SC-5]" in prompt
    assert "[SC:event] event context block" in prompt
