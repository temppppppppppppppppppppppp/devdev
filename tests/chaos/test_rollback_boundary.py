"""[P7-01] StateDeltaTracker / EmotionArcTracker rollback boundary tests.

Verifies that the rollback_to and reset/clear methods introduced in the
1차 patches behave correctly at boundary conditions.
"""


from modules.core.emotion_tracker import EmotionArcTracker
from modules.core.state_delta_tracker import StateDeltaTracker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_delta_tracker_with_history() -> StateDeltaTracker:
    """Return a StateDeltaTracker with entries at episodes 1, 5, 10."""
    tracker = StateDeltaTracker(initial_energy=100)
    tracker.apply_energy_delta(arc=1, episode=1, delta=-10, reason="격전")
    tracker.apply_energy_delta(arc=1, episode=5, delta=-15, reason="격전")
    tracker.apply_energy_delta(arc=1, episode=10, delta=-20, reason="격전")
    tracker.apply_injury(arc=1, episode=3, level="경상", body_part="팔", cause="검격")
    tracker.apply_injury(arc=1, episode=8, level="중상", body_part="다리", cause="도검")
    return tracker


def _make_emotion_tracker_with_history() -> EmotionArcTracker:
    """Return an EmotionArcTracker with entries at episodes 1, 5, 10."""

    class _FakeCtx:
        pass

    tracker = EmotionArcTracker(_FakeCtx())
    tracker.add_episode_emotion(ep_num=1, emotion_state="neutral", intensity=0.5)
    tracker.add_episode_emotion(ep_num=5, emotion_state="hope", intensity=0.7)
    tracker.add_episode_emotion(ep_num=10, emotion_state="triumph", intensity=0.9)
    return tracker


# ---------------------------------------------------------------------------
# Test 1: StateDeltaTracker.rollback_to removes entries with ep >= target
# ---------------------------------------------------------------------------

def test_state_delta_tracker_rollback_to_removes_future_entries():
    tracker = _make_delta_tracker_with_history()
    assert len(tracker.energy_history) == 3  # ep 1, 5, 10

    tracker.rollback_to(6)  # Remove ep >= 6 → only ep 1, 5 remain

    assert all(e.episode < 6 for e in tracker.energy_history), (
        "energy_history must not contain episodes >= 6 after rollback_to(6)"
    )
    assert all(e.episode < 6 for e in tracker.injury_history), (
        "injury_history must not contain episodes >= 6 after rollback_to(6)"
    )
    assert len(tracker.energy_history) == 2
    assert len(tracker.injury_history) == 1  # ep 3 survives; ep 8 removed


# ---------------------------------------------------------------------------
# Test 2: StateDeltaTracker.reset clears all entries
# ---------------------------------------------------------------------------

def test_state_delta_tracker_reset_clears_all():
    tracker = _make_delta_tracker_with_history()
    assert tracker.energy_history  # not empty

    tracker.reset()

    assert tracker.energy_history == []
    assert tracker.injury_history == []


# ---------------------------------------------------------------------------
# Test 3: EmotionArcTracker.rollback_to removes entries with ep >= target
# ---------------------------------------------------------------------------

def test_emotion_arc_tracker_rollback_to_removes_future_entries():
    tracker = _make_emotion_tracker_with_history()
    assert len(tracker.history) == 3

    tracker.rollback_to(6)  # Remove ep >= 6 → ep 1, 5 survive

    assert len(tracker.history) == 2
    assert all(entry[0] < 6 for entry in tracker.history), (
        "history must not contain episodes >= 6 after rollback_to(6)"
    )


# ---------------------------------------------------------------------------
# Test 4: EmotionArcTracker.clear clears all entries
# ---------------------------------------------------------------------------

def test_emotion_arc_tracker_clear_empties_history():
    tracker = _make_emotion_tracker_with_history()
    assert tracker.history  # not empty

    tracker.clear()

    assert tracker.history == []


# ---------------------------------------------------------------------------
# Test 5: rollback_to on empty history does nothing (no error)
# ---------------------------------------------------------------------------

def test_state_delta_tracker_rollback_to_empty_history_no_error():
    tracker = StateDeltaTracker(initial_energy=100)
    # Should not raise any exception
    tracker.rollback_to(5)
    assert tracker.energy_history == []
    assert tracker.injury_history == []


def test_emotion_arc_tracker_rollback_to_empty_history_no_error():
    class _FakeCtx:
        pass

    tracker = EmotionArcTracker(_FakeCtx())
    # Should not raise any exception
    tracker.rollback_to(5)
    assert tracker.history == []


# ---------------------------------------------------------------------------
# Test 6: rollback_to(1) removes everything (boundary: ep >= 1)
# ---------------------------------------------------------------------------

def test_state_delta_tracker_rollback_to_1_removes_all():
    tracker = _make_delta_tracker_with_history()
    tracker.rollback_to(1)
    assert tracker.energy_history == []
    assert tracker.injury_history == []


def test_emotion_arc_tracker_rollback_to_1_removes_all():
    tracker = _make_emotion_tracker_with_history()
    tracker.rollback_to(1)
    assert tracker.history == []
