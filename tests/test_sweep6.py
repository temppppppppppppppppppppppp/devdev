"""[Sweep6] Thread-safety and resource-cap regression tests."""

from types import SimpleNamespace
from unittest.mock import MagicMock


def test_base_agent_context_cache_has_max_cap(monkeypatch):
    """_context_caches should be trimmed to max size when over limit."""
    from modules.domain.agents import base_agent as ba

    ba.BaseAgent._context_caches = {}
    monkeypatch.setattr(
        ba,
        "types",
        SimpleNamespace(CreateCachedContentConfig=lambda **kwargs: kwargs),
    )

    context = MagicMock()
    context.author_directives = ""

    client = MagicMock()
    created = {"count": 0}

    def _create_cache(**kwargs):
        created["count"] += 1
        return SimpleNamespace(name=f"cache-{created['count']}")

    client.caches.create.side_effect = _create_cache

    agent = ba.BaseAgent(context=context, client=client, model_tier="gemini-2.5-flash")

    for i in range(60):
        content = ("x" * 50001) + str(i)
        agent._get_or_create_context_cache(
            cache_type="blueprint",
            content=content,
            ttl_seconds=1800,
            project_name="sweep6",
        )

    assert len(ba.BaseAgent._context_caches) == ba.BaseAgent._CONTEXT_CACHE_MAX


def test_adaptive_retry_failure_episode_keys_are_capped():
    """AdaptiveRetryManager should keep only recent episode keys."""
    from modules.core.adaptive_retry import AdaptiveRetryManager

    manager = AdaptiveRetryManager(max_history=100)

    for ep in range(1, 61):
        manager.record_failure(
            ep_num=ep,
            agent="writer",
            error_info={"message": "quality issue"},
        )

    keys = sorted(manager._failures.keys())
    assert len(keys) == manager._max_episode_keys
    assert keys[0] == 11
    assert keys[-1] == 60
