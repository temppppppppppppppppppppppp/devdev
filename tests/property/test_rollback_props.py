"""Property-based tests for rollback invariants.

Tests EmotionArcTracker and StateDeltaTracker rollback semantics using hypothesis.

Key invariants:
1. rollback_to never leaks future episodes: after rollback_to(t), no entry has ep >= t
2. rollback_to is idempotent: calling twice == calling once
3. reset / clear produces empty history
4. rollback_to(0) clears everything (no episode has ep < 0)
5. rollback_to(very_large_number) is a no-op
6. rollback_to preserves original order of remaining entries
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.emotion_tracker import EmotionArcTracker  # noqa: E402
from modules.core.state_delta_tracker import StateDeltaTracker  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_EMOTION_STATES = list(EmotionArcTracker.EMOTION_STATES.keys())


def _make_emotion_tracker() -> EmotionArcTracker:
    """Return a tracker with a stub project_context."""
    return EmotionArcTracker(project_context=None)


def _populate_emotion(tracker: EmotionArcTracker, episodes: list[int]) -> None:
    """Directly append (ep, state, intensity) tuples to history."""
    for ep in episodes:
        # Cycle through valid states to avoid repeating the same value every time
        state = VALID_EMOTION_STATES[ep % len(VALID_EMOTION_STATES)]
        tracker.history.append((ep, state, 0.5))


def _populate_state_delta(tracker: StateDeltaTracker, episodes: list[int]) -> None:
    """Add one EnergyDelta per episode number via the public API."""
    for ep in episodes:
        tracker.apply_energy_delta(arc=1, episode=ep, delta=-1, reason="test")


# ---------------------------------------------------------------------------
# EmotionArcTracker — rollback_to
# ---------------------------------------------------------------------------


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=0, max_size=30),
    target=st.integers(min_value=0, max_value=55),
)
@settings(max_examples=300)
def test_emotion_rollback_no_future_leak(episodes: list[int], target: int) -> None:
    """After rollback_to(target), no entry has ep >= target."""
    tracker = _make_emotion_tracker()
    _populate_emotion(tracker, episodes)
    tracker.rollback_to(target)
    for entry in tracker.history:
        assert entry[0] < target, (
            f"Leaked entry ep={entry[0]} >= target={target}"
        )


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=0, max_size=30),
    target=st.integers(min_value=0, max_value=55),
)
@settings(max_examples=300)
def test_emotion_rollback_idempotent(episodes: list[int], target: int) -> None:
    """rollback_to(t) twice produces the same result as calling it once."""
    tracker1 = _make_emotion_tracker()
    _populate_emotion(tracker1, episodes)
    tracker1.rollback_to(target)
    snapshot_once = list(tracker1.history)

    tracker1.rollback_to(target)
    assert tracker1.history == snapshot_once, (
        "rollback_to is not idempotent"
    )


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=0, max_size=30),
)
@settings(max_examples=200)
def test_emotion_clear_empties_history(episodes: list[int]) -> None:
    """clear() always produces an empty history."""
    tracker = _make_emotion_tracker()
    _populate_emotion(tracker, episodes)
    tracker.clear()
    assert tracker.history == [], "clear() did not empty history"


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=1, max_size=30),
)
@settings(max_examples=200)
def test_emotion_rollback_zero_clears_all(episodes: list[int]) -> None:
    """rollback_to(0) removes all entries (no ep can be < 0 when eps >= 1)."""
    tracker = _make_emotion_tracker()
    _populate_emotion(tracker, episodes)
    tracker.rollback_to(0)
    assert tracker.history == [], (
        f"rollback_to(0) left {len(tracker.history)} entries"
    )


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=0, max_size=30),
)
@settings(max_examples=200)
def test_emotion_rollback_large_is_noop(episodes: list[int]) -> None:
    """rollback_to(very_large_number) changes nothing."""
    tracker = _make_emotion_tracker()
    _populate_emotion(tracker, episodes)
    snapshot_before = list(tracker.history)
    tracker.rollback_to(10_000)
    assert tracker.history == snapshot_before, (
        "rollback_to(10000) changed history when it should be a no-op"
    )


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=0, max_size=30),
    target=st.integers(min_value=1, max_value=55),
)
@settings(max_examples=300)
def test_emotion_rollback_preserves_order(episodes: list[int], target: int) -> None:
    """Entries remaining after rollback preserve their original relative order."""
    tracker = _make_emotion_tracker()
    _populate_emotion(tracker, episodes)

    # Compute expected result manually (same filter logic)
    expected = [e for e in tracker.history if e[0] < target]

    tracker.rollback_to(target)
    assert tracker.history == expected, (
        "rollback_to did not preserve original order"
    )


# ---------------------------------------------------------------------------
# EmotionArcTracker — add_episode_emotion public API
# ---------------------------------------------------------------------------


@given(
    ep=st.integers(min_value=1, max_value=50),
    state=st.sampled_from(VALID_EMOTION_STATES),
    intensity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    target=st.integers(min_value=0, max_value=55),
)
@settings(max_examples=200)
def test_emotion_add_then_rollback_no_leak(
    ep: int, state: str, intensity: float, target: int
) -> None:
    """add_episode_emotion + rollback_to: no entry at ep >= target survives."""
    tracker = _make_emotion_tracker()
    tracker.add_episode_emotion(ep, state, intensity)
    tracker.rollback_to(target)
    for entry in tracker.history:
        assert entry[0] < target


# ---------------------------------------------------------------------------
# StateDeltaTracker — rollback_to (energy_history)
# ---------------------------------------------------------------------------


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=0, max_size=30),
    target=st.integers(min_value=0, max_value=55),
)
@settings(max_examples=300)
def test_state_delta_energy_rollback_no_future_leak(
    episodes: list[int], target: int
) -> None:
    """After rollback_to(target), no energy entry has episode >= target."""
    tracker = StateDeltaTracker()
    _populate_state_delta(tracker, episodes)
    tracker.rollback_to(target)
    for entry in tracker.energy_history:
        assert entry.episode < target, (
            f"Energy entry ep={entry.episode} >= target={target}"
        )


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=0, max_size=30),
    target=st.integers(min_value=0, max_value=55),
)
@settings(max_examples=300)
def test_state_delta_energy_rollback_idempotent(
    episodes: list[int], target: int
) -> None:
    """rollback_to(t) twice == rollback_to(t) once for energy_history."""
    tracker = StateDeltaTracker()
    _populate_state_delta(tracker, episodes)
    tracker.rollback_to(target)
    snap_once = list(tracker.energy_history)

    tracker.rollback_to(target)
    assert [(e.episode, e.delta) for e in tracker.energy_history] == [
        (e.episode, e.delta) for e in snap_once
    ], "rollback_to energy_history is not idempotent"


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=1, max_size=30),
)
@settings(max_examples=200)
def test_state_delta_rollback_zero_clears_energy(episodes: list[int]) -> None:
    """rollback_to(0) removes all energy entries."""
    tracker = StateDeltaTracker()
    _populate_state_delta(tracker, episodes)
    tracker.rollback_to(0)
    assert tracker.energy_history == [], (
        f"rollback_to(0) left {len(tracker.energy_history)} energy entries"
    )


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=0, max_size=30),
)
@settings(max_examples=200)
def test_state_delta_rollback_large_is_noop(episodes: list[int]) -> None:
    """rollback_to(10000) does not remove any energy entries."""
    tracker = StateDeltaTracker()
    _populate_state_delta(tracker, episodes)
    snapshot_eps = [e.episode for e in tracker.energy_history]
    tracker.rollback_to(10_000)
    assert [e.episode for e in tracker.energy_history] == snapshot_eps, (
        "rollback_to(10000) unexpectedly changed energy_history"
    )


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=0, max_size=30),
)
@settings(max_examples=200)
def test_state_delta_reset_empties_both_histories(episodes: list[int]) -> None:
    """reset() always produces empty energy_history and injury_history."""
    tracker = StateDeltaTracker()
    _populate_state_delta(tracker, episodes)
    # Also add some injury events so injury_history is non-empty
    for ep in episodes[:3]:
        tracker.apply_injury(arc=1, episode=ep, level="경상", body_part="팔", cause="테스트")
    tracker.reset()
    assert tracker.energy_history == [], "reset() did not empty energy_history"
    assert tracker.injury_history == [], "reset() did not empty injury_history"


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=0, max_size=30),
    target=st.integers(min_value=1, max_value=55),
)
@settings(max_examples=300)
def test_state_delta_rollback_injury_no_future_leak(
    episodes: list[int], target: int
) -> None:
    """After rollback_to(target), no injury entry has episode >= target."""
    tracker = StateDeltaTracker()
    for ep in episodes:
        tracker.apply_injury(arc=1, episode=ep, level="경상", body_part="팔", cause="테스트")
    tracker.rollback_to(target)
    for entry in tracker.injury_history:
        assert entry.episode < target, (
            f"Injury entry ep={entry.episode} >= target={target}"
        )


@given(
    episodes=st.lists(st.integers(min_value=1, max_value=50), min_size=0, max_size=30),
    target=st.integers(min_value=1, max_value=55),
)
@settings(max_examples=300)
def test_state_delta_rollback_preserves_order(
    episodes: list[int], target: int
) -> None:
    """Energy entries remaining after rollback preserve their original order."""
    tracker = StateDeltaTracker()
    _populate_state_delta(tracker, episodes)
    expected_eps = [e.episode for e in tracker.energy_history if e.episode < target]
    tracker.rollback_to(target)
    assert [e.episode for e in tracker.energy_history] == expected_eps, (
        "rollback_to did not preserve energy_history order"
    )


# ---------------------------------------------------------------------------
# Cross-invariant: rollback_to semantics match < ep_num (not <=)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("target", [1, 5, 10])
def test_emotion_rollback_boundary_excludes_target_ep(target: int) -> None:
    """rollback_to(t) removes entries at ep == t (strict < semantics)."""
    tracker = _make_emotion_tracker()
    # Add exactly one entry at the target episode
    tracker.history.append((target, "neutral", 0.5))
    tracker.rollback_to(target)
    # The entry at ep == target must be gone
    assert all(e[0] < target for e in tracker.history), (
        f"Entry at ep={target} survived rollback_to({target})"
    )


@pytest.mark.parametrize("target", [1, 5, 10])
def test_state_delta_rollback_boundary_excludes_target_ep(target: int) -> None:
    """rollback_to(t) removes energy entries at ep == t (strict < semantics)."""
    tracker = StateDeltaTracker()
    tracker.apply_energy_delta(arc=1, episode=target, delta=-5, reason="test")
    tracker.rollback_to(target)
    assert all(e.episode < target for e in tracker.energy_history), (
        f"Energy entry at ep={target} survived rollback_to({target})"
    )
