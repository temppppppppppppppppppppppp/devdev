"""Tests for rollback gating in SovereignApp._rollback_episode."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from main_a import SovereignApp


def _make_app(success: bool):
    writer = MagicMock()
    director = MagicMock()
    return SimpleNamespace(
        _project_service=SimpleNamespace(rollback_episode=MagicMock(return_value=success)),
        state_tracker="tracker",
        _prompt_builder=SimpleNamespace(invalidate_timeline_cache=MagicMock()),
        _cumulative_state_cache="cache",
        _cumulative_state_cache_key="cache_key",
        _narrative_summaries_cache="summary_cache",
        agents={"writer": writer, "director": director},
    )


def test_rollback_episode_cancel_keeps_tracker_and_caches():
    app = _make_app(False)

    SovereignApp._rollback_episode(app)

    assert app.state_tracker == "tracker"
    assert app._cumulative_state_cache == "cache"
    assert app._cumulative_state_cache_key == "cache_key"
    assert app._narrative_summaries_cache == "summary_cache"
    app._prompt_builder.invalidate_timeline_cache.assert_not_called()
    app.agents["writer"].invalidate_manuscript_cache.assert_not_called()
    app.agents["director"].invalidate_caches.assert_not_called()


def test_rollback_episode_success_resets_tracker_and_caches():
    app = _make_app(True)

    SovereignApp._rollback_episode(app)

    assert app.state_tracker is None
    assert app._cumulative_state_cache is None
    assert app._cumulative_state_cache_key is None
    assert app._narrative_summaries_cache is None
    app._prompt_builder.invalidate_timeline_cache.assert_called_once()
    app.agents["writer"].invalidate_manuscript_cache.assert_called_once()
    app.agents["director"].invalidate_caches.assert_called_once()


def test_reset_stage_2_success_invalidates_runtime_caches():
    writer = MagicMock()
    director = MagicMock()
    state_extractor = MagicMock()
    foreshadow_tracker = MagicMock()
    app = SimpleNamespace(
        _project_service=SimpleNamespace(reset_stage_2=MagicMock(return_value=True)),
        state_tracker="tracker",
        _prompt_builder=SimpleNamespace(invalidate_timeline_cache=MagicMock()),
        _cumulative_state_cache="cache",
        _cumulative_state_cache_key="cache_key",
        _narrative_summaries_cache="summary_cache",
        current_project=SimpleNamespace(db=MagicMock()),
        foreshadow_tracker=foreshadow_tracker,
        agents={"writer": writer, "director": director, "state_extractor": state_extractor},
    )

    SovereignApp._reset_stage_2(app)

    assert app.state_tracker is None
    assert app._cumulative_state_cache is None
    assert app._cumulative_state_cache_key is None
    assert app._narrative_summaries_cache is None
    app._prompt_builder.invalidate_timeline_cache.assert_called_once()
    writer.invalidate_manuscript_cache.assert_called_once()
    director.invalidate_caches.assert_called_once()
    state_extractor.invalidate_cache.assert_called_once()
    foreshadow_tracker.clear.assert_called_once()


def test_wipe_production_data_success_invalidates_runtime_caches():
    writer = MagicMock()
    director = MagicMock()
    state_extractor = MagicMock()
    foreshadow_tracker = MagicMock()
    app = SimpleNamespace(
        _project_service=SimpleNamespace(wipe_production_data=MagicMock(return_value=True)),
        state_tracker="tracker",
        _prompt_builder=SimpleNamespace(invalidate_timeline_cache=MagicMock()),
        _cumulative_state_cache="cache",
        _cumulative_state_cache_key="cache_key",
        _narrative_summaries_cache="summary_cache",
        current_project=SimpleNamespace(db=MagicMock()),
        foreshadow_tracker=foreshadow_tracker,
        agents={"writer": writer, "director": director, "state_extractor": state_extractor},
    )

    SovereignApp._wipe_production_data(app)

    assert app.state_tracker is None
    assert app._cumulative_state_cache is None
    assert app._cumulative_state_cache_key is None
    assert app._narrative_summaries_cache is None
    app._prompt_builder.invalidate_timeline_cache.assert_called_once()
    writer.invalidate_manuscript_cache.assert_called_once()
    director.invalidate_caches.assert_called_once()
    state_extractor.invalidate_cache.assert_called_once()
    foreshadow_tracker.clear.assert_called_once()


def test_rewind_stage_2_success_reloads_foreshadow_from_db():
    writer = MagicMock()
    director = MagicMock()
    state_extractor = MagicMock()
    foreshadow_tracker = MagicMock()
    app = SimpleNamespace(
        _project_service=SimpleNamespace(rewind_stage_2=MagicMock(return_value=True)),
        state_tracker="tracker",
        _prompt_builder=SimpleNamespace(invalidate_timeline_cache=MagicMock()),
        _cumulative_state_cache="cache",
        _cumulative_state_cache_key="cache_key",
        _narrative_summaries_cache="summary_cache",
        current_project=SimpleNamespace(db=MagicMock()),
        foreshadow_tracker=foreshadow_tracker,
        agents={"writer": writer, "director": director, "state_extractor": state_extractor},
    )

    SovereignApp._rewind_stage_2(app)

    foreshadow_tracker.load_from_db.assert_called_once_with(app.current_project.db)
    foreshadow_tracker.clear.assert_not_called()


def test_rollback_episode_success_reloads_foreshadow_from_db():
    writer = MagicMock()
    director = MagicMock()
    foreshadow_tracker = MagicMock()
    app = SimpleNamespace(
        _project_service=SimpleNamespace(rollback_episode=MagicMock(return_value=True)),
        state_tracker="tracker",
        _prompt_builder=SimpleNamespace(invalidate_timeline_cache=MagicMock()),
        _cumulative_state_cache="cache",
        _cumulative_state_cache_key="cache_key",
        _narrative_summaries_cache="summary_cache",
        current_project=SimpleNamespace(db=MagicMock()),
        foreshadow_tracker=foreshadow_tracker,
        agents={"writer": writer, "director": director},
    )

    SovereignApp._rollback_episode(app)

    foreshadow_tracker.load_from_db.assert_called_once_with(app.current_project.db)
    foreshadow_tracker.clear.assert_not_called()
