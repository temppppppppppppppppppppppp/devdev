"""[P7-07] ProjectService._assert_rollback_invariants() tests.

Verifies the post-rollback invariant checker introduced in TF-7-P0 patch:
- Logs WARNING when a tracker still has episodes >= target after rollback
- Logs DEBUG (no WARNING) when all trackers are within bounds
- Handles None tracker callbacks gracefully
"""

import logging
from unittest.mock import MagicMock

from modules.core.services.project_service import ProjectService

# ---------------------------------------------------------------------------
# Helper: build a minimal ProjectService (most callbacks unused here)
# ---------------------------------------------------------------------------

def _make_service(
    emotion_tracker=None,
    state_delta_tracker=None,
) -> ProjectService:
    """Build ProjectService with all non-invariant callbacks mocked away."""
    return ProjectService(
        project_fn=MagicMock(),
        ui=MagicMock(),
        safe_commit_fn=MagicMock(return_value=True),
        genre_fn=MagicMock(return_value=None),
        memory_fn=MagicMock(return_value=None),
        state_tracker_invalidator=None,
        world_state_fn=None,
        fact_ledger_fn=None,
        preset_registry_restorer=None,
        emotion_tracker_fn=(lambda: emotion_tracker) if emotion_tracker is not None else None,
        state_delta_tracker_fn=(lambda: state_delta_tracker) if state_delta_tracker is not None else None,
    )


# ---------------------------------------------------------------------------
# Helpers: fake tracker objects
# ---------------------------------------------------------------------------

class _FakeEmotionTracker:
    """Minimal EmotionArcTracker stand-in with a history list."""

    def __init__(self, history):
        # Each entry is a tuple: (ep_num, emotion_state, intensity)
        self.history = history


class _FakeStateDeltaTracker:
    """Minimal StateDeltaTracker stand-in with an energy_history list."""

    def __init__(self, energy_history):
        # Each entry must have an .episode attribute
        self.energy_history = energy_history


class _FakeEnergyEntry:
    def __init__(self, episode: int):
        self.episode = episode


# ---------------------------------------------------------------------------
# Test 1: WARNING logged when emotion_tracker has ep >= target_ep
# ---------------------------------------------------------------------------

def test_assert_rollback_invariants_warns_when_emotion_tracker_exceeds_target(caplog):
    # Build a tracker that still has ep=10 after a rollback to ep=5
    emotion_tracker = _FakeEmotionTracker(history=[
        (3, "hope", 0.6),
        (10, "triumph", 0.9),  # this is >= target_ep=5 → should trigger WARNING
    ])
    service = _make_service(emotion_tracker=emotion_tracker)

    with caplog.at_level(logging.WARNING, logger="modules.core.services.project_service"):
        service._assert_rollback_invariants(target_ep=5)

    warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any("EmotionArcTracker" in m and "RollbackInvariant" in m for m in warning_msgs), (
        "Expected a RollbackInvariant WARNING for EmotionArcTracker, got: " + str(warning_msgs)
    )


# ---------------------------------------------------------------------------
# Test 2: DEBUG logged (no WARNING) when emotion_tracker is within bounds
# ---------------------------------------------------------------------------

def test_assert_rollback_invariants_no_warning_when_emotion_tracker_within_bounds(caplog):
    # All entries are below target_ep=10
    emotion_tracker = _FakeEmotionTracker(history=[
        (3, "hope", 0.6),
        (7, "neutral", 0.5),
    ])
    service = _make_service(emotion_tracker=emotion_tracker)

    with caplog.at_level(logging.DEBUG, logger="modules.core.services.project_service"):
        service._assert_rollback_invariants(target_ep=10)

    warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    rollback_warnings = [m for m in warning_msgs if "RollbackInvariant" in m and "EmotionArcTracker" in m]
    assert not rollback_warnings, (
        "No RollbackInvariant WARNING expected when all entries are within bounds"
    )


# ---------------------------------------------------------------------------
# Test 3: WARNING logged when state_delta_tracker has ep >= target_ep
# ---------------------------------------------------------------------------

def test_assert_rollback_invariants_warns_when_state_delta_tracker_exceeds_target(caplog):
    sdt = _FakeStateDeltaTracker(energy_history=[
        _FakeEnergyEntry(2),
        _FakeEnergyEntry(12),  # >= target_ep=5 → WARNING
    ])
    service = _make_service(state_delta_tracker=sdt)

    with caplog.at_level(logging.WARNING, logger="modules.core.services.project_service"):
        service._assert_rollback_invariants(target_ep=5)

    warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any("StateDeltaTracker" in m and "RollbackInvariant" in m for m in warning_msgs), (
        "Expected a RollbackInvariant WARNING for StateDeltaTracker"
    )


# ---------------------------------------------------------------------------
# Test 4: No WARNING when state_delta_tracker is within bounds
# ---------------------------------------------------------------------------

def test_assert_rollback_invariants_no_warning_when_state_delta_tracker_within_bounds(caplog):
    sdt = _FakeStateDeltaTracker(energy_history=[
        _FakeEnergyEntry(2),
        _FakeEnergyEntry(4),
    ])
    service = _make_service(state_delta_tracker=sdt)

    with caplog.at_level(logging.DEBUG, logger="modules.core.services.project_service"):
        service._assert_rollback_invariants(target_ep=10)

    warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    rollback_warnings = [m for m in warning_msgs if "RollbackInvariant" in m and "StateDeltaTracker" in m]
    assert not rollback_warnings


# ---------------------------------------------------------------------------
# Test 5: None tracker callbacks are handled gracefully (no AttributeError)
# ---------------------------------------------------------------------------

def test_assert_rollback_invariants_handles_none_trackers_gracefully():
    # Both tracker callbacks are None — should not raise
    service = _make_service(emotion_tracker=None, state_delta_tracker=None)

    # Must not raise any exception
    service._assert_rollback_invariants(target_ep=5)


# ---------------------------------------------------------------------------
# Test 6: Empty history does not trigger WARNING
# ---------------------------------------------------------------------------

def test_assert_rollback_invariants_empty_history_no_warning(caplog):
    emotion_tracker = _FakeEmotionTracker(history=[])
    sdt = _FakeStateDeltaTracker(energy_history=[])
    service = _make_service(emotion_tracker=emotion_tracker, state_delta_tracker=sdt)

    with caplog.at_level(logging.WARNING, logger="modules.core.services.project_service"):
        service._assert_rollback_invariants(target_ep=5)

    warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    rollback_warnings = [m for m in warning_msgs if "RollbackInvariant" in m]
    assert not rollback_warnings, "Empty history must not trigger RollbackInvariant WARNING"
