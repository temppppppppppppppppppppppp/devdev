"""[Sweep4] Debug Sweep 4 targeted safety tests."""

from types import SimpleNamespace
from unittest.mock import MagicMock


class _EmptyCounter(dict):
    """Dictionary that behaves like an empty counter."""

    def __missing__(self, key):
        return 0

    def __setitem__(self, key, value):
        # Intentionally ignore writes to keep it empty.
        return None


def _empty_defaultdict(*args, **kwargs):
    return _EmptyCounter()


def test_adaptive_retry_empty_type_counts_guard(monkeypatch):
    """AdaptiveRetry should not crash when type_counts is empty."""
    from modules.core import adaptive_retry as ar

    manager = ar.AdaptiveRetryManager()
    rec = ar.FailureRecord(ep_num=1, agent="writer", error_type=ar.ErrorType.QUALITY_ISSUE, details={})
    manager._failures[1] = [rec, rec]

    monkeypatch.setattr(ar, "defaultdict", _empty_defaultdict)

    guidance = manager.get_retry_guidance(ep_num=1, agent="writer", current_attempt=2)
    assert guidance["primary_error"] == "unknown"
    assert guidance["failure_count"] == 2

    trigger, recommended = manager.should_trigger_ultimate(ep_num=1, agent="writer")
    assert trigger is False
    assert recommended == "adversarial_self_play"


def test_pattern_tracker_empty_emotion_balance_defaults_to_neutral():
    """Empty emotion_balance should map to neutral instead of raising ValueError."""
    from modules.core.pattern_tracker import PatternTracker

    tracker = PatternTracker()
    trends = tracker._calculate_trends(
        [
            {"cliche_density": 0.1, "diversity_score": 80, "emotion_balance": {}},
            {"cliche_density": 0.2, "diversity_score": 75, "emotion_balance": {}},
        ]
    )

    assert trends["emotion_shift"]["from"] == "neutral"
    assert trends["emotion_shift"]["to"] == "neutral"


def test_validation_orchestrator_handles_missing_critical_issues_key():
    """PRE-LLM failure should not KeyError when critical_issues key is missing."""
    from modules.validation.validation_orchestrator import ValidationOrchestrator

    orch = ValidationOrchestrator(
        config={"use_pre_llm": True, "use_parallel_validation": False, "use_self_consistency": False},
        client=None,
        genre="wuxia",
        context={},
    )
    orch.pre_llm = MagicMock()
    orch.pre_llm.validate.return_value = {"passed": False}

    result = orch.validate(ep_num=1, manuscript="테스트 원고", validation_context={})
    assert result["final_decision"] == "REJECT"
    assert result["critical_issues"] == []


def test_state_extractor_invalidate_cache():
    """StateExtractor cache invalidation should support single key and full clear."""
    from modules.domain.agents.state_extractor import StateExtractor

    extractor = StateExtractor.__new__(StateExtractor)
    extractor._state_cache = {1: {"a": 1}, 2: {"b": 2}}

    extractor.invalidate_cache(1)
    assert 1 not in extractor._state_cache
    assert 2 in extractor._state_cache

    extractor.invalidate_cache()
    assert extractor._state_cache == {}


def test_chief_writer_invalidate_manuscript_cache():
    """ChiefWriter cache invalidation should reset manuscript cache state."""
    from modules.domain.agents.chief_writer import ChiefWriter

    writer = ChiefWriter.__new__(ChiefWriter)
    writer._manuscript_cache = {3: {"content": "cached"}}
    writer._cache_ep_num = 3

    writer.invalidate_manuscript_cache()

    assert writer._manuscript_cache == {}
    assert writer._cache_ep_num == -1


def test_state_tracker_plots_aliases_none_is_safe():
    """aliases=None should not raise TypeError in name consistency check."""
    from modules.domain.agents.state_tracker_plots import StateTrackerPlots

    tracker = SimpleNamespace(
        entity_name_registry={
            "무림맹": {
                "type": "organization",
                "first_arc": 1,
                "aliases": None,
            }
        }
    )
    plots = StateTrackerPlots(tracker)

    warnings = plots.check_entity_name_consistency("무림파가 움직였다.", arc_no=2)
    assert isinstance(warnings, list)
