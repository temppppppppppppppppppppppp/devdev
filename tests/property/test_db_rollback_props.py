"""Property-based tests for ProjectService._assert_rollback_invariants.

Key invariants:
1. No WARNING logged when all trackers have max_ep < target_ep
2. WARNING logged for EmotionArcTracker when max_ep >= target_ep
3. WARNING logged for StateDeltaTracker when max_ep >= target_ep
4. None trackers (callbacks returning None) never crash

Note: _assert_rollback_invariants warns when max_ep >= target_ep.
This is consistent with rollback_to(t) using strict "< t" semantics: after a
correct rollback all entries have ep < t, so max_ep < t → no warning.
If the rollback leaked (max_ep >= t) → WARNING is emitted.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.services.project_service import ProjectService  # noqa: E402

# ---------------------------------------------------------------------------
# Helper: build a minimal ProjectService
# ---------------------------------------------------------------------------


def _make_service(
    emotion_tracker=None,
    state_delta_tracker=None,
) -> ProjectService:
    """Return a ProjectService whose tracker callbacks return the given mocks."""
    ui = MagicMock()
    ui.log = MagicMock()
    svc = ProjectService(
        project_fn=lambda: MagicMock(),
        ui=ui,
        safe_commit_fn=lambda: True,
        genre_fn=lambda: {},
        memory_fn=lambda: None,
        emotion_tracker_fn=(lambda: emotion_tracker) if emotion_tracker is not None else None,
        state_delta_tracker_fn=(
            (lambda: state_delta_tracker) if state_delta_tracker is not None else None
        ),
    )
    return svc


def _emotion_mock_with_history(ep_list: list[int]):
    """Return a mock EmotionArcTracker with the given episode numbers."""
    mock = MagicMock()
    mock.history = [(ep, "neutral", 0.5) for ep in ep_list]
    return mock


def _state_delta_mock_with_history(ep_list: list[int]):
    """Return a mock StateDeltaTracker with energy_history at the given eps."""
    mock = MagicMock()
    entries = []
    for ep in ep_list:
        entry = MagicMock()
        entry.episode = ep
        entries.append(entry)
    mock.energy_history = entries
    return mock


# ---------------------------------------------------------------------------
# Invariant 1 — No WARNING when max_ep < target_ep
# ---------------------------------------------------------------------------


@given(
    history_eps=st.lists(st.integers(min_value=1, max_value=20), min_size=1),
    target=st.integers(min_value=1, max_value=25),
)
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_no_warning_when_emotion_within_bounds(
    history_eps: list[int], target: int
) -> None:
    """No WARNING is emitted when all emotion tracker episodes < target."""
    # Only keep episodes that are strictly below target to guarantee invariant
    safe_eps = [ep for ep in history_eps if ep < target]
    if not safe_eps:
        return  # nothing to assert if list is empty

    et = _emotion_mock_with_history(safe_eps)
    svc = _make_service(emotion_tracker=et)

    with patch.object(logging, "warning") as mock_warn:
        svc._assert_rollback_invariants(target)

    # Check no rollback-invariant warning was emitted
    for call in mock_warn.call_args_list:
        args = call.args
        if args and isinstance(args[0], str) and "RollbackInvariant" in args[0]:
            assert False, (
                f"Unexpected RollbackInvariant WARNING for safe eps {safe_eps}, "
                f"target={target}. Call: {call}"
            )


@given(
    history_eps=st.lists(st.integers(min_value=1, max_value=20), min_size=1),
    target=st.integers(min_value=1, max_value=25),
)
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_no_warning_when_state_delta_within_bounds(
    history_eps: list[int], target: int
) -> None:
    """No WARNING is emitted when all state_delta tracker episodes < target."""
    safe_eps = [ep for ep in history_eps if ep < target]
    if not safe_eps:
        return

    sdt = _state_delta_mock_with_history(safe_eps)
    svc = _make_service(state_delta_tracker=sdt)

    with patch.object(logging, "warning") as mock_warn:
        svc._assert_rollback_invariants(target)

    for call in mock_warn.call_args_list:
        args = call.args
        if args and isinstance(args[0], str) and "RollbackInvariant" in args[0]:
            assert False, (
                f"Unexpected RollbackInvariant WARNING for safe eps {safe_eps}, "
                f"target={target}. Call: {call}"
            )


# ---------------------------------------------------------------------------
# Invariant 2 — WARNING when emotion tracker leaks
# ---------------------------------------------------------------------------


@given(
    leak_ep=st.integers(min_value=1, max_value=20),
    target=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_warning_when_emotion_leaks(leak_ep: int, target: int) -> None:
    """A WARNING is emitted when emotion tracker has max_ep >= target_ep."""
    # Ensure at least one episode is >= target
    history_eps = [leak_ep if leak_ep >= target else target]

    et = _emotion_mock_with_history(history_eps)
    svc = _make_service(emotion_tracker=et)

    warned = []
    with patch.object(logging, "warning", side_effect=lambda *a, **kw: warned.append(a)):
        svc._assert_rollback_invariants(target)

    rollback_warnings = [
        a for a in warned if a and isinstance(a[0], str) and "RollbackInvariant" in a[0]
        and "EmotionArcTracker" in a[0]
    ]
    assert len(rollback_warnings) >= 1, (
        f"Expected RollbackInvariant WARNING for history_eps={history_eps}, "
        f"target={target}, but none was emitted"
    )


@given(
    leak_ep=st.integers(min_value=1, max_value=20),
    target=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_warning_when_state_delta_leaks(leak_ep: int, target: int) -> None:
    """A WARNING is emitted when state_delta tracker has max_ep >= target_ep."""
    history_eps = [leak_ep if leak_ep >= target else target]

    sdt = _state_delta_mock_with_history(history_eps)
    svc = _make_service(state_delta_tracker=sdt)

    warned = []
    with patch.object(logging, "warning", side_effect=lambda *a, **kw: warned.append(a)):
        svc._assert_rollback_invariants(target)

    rollback_warnings = [
        a for a in warned
        if a and isinstance(a[0], str) and "RollbackInvariant" in a[0]
        and "StateDeltaTracker" in a[0]
    ]
    assert len(rollback_warnings) >= 1, (
        f"Expected RollbackInvariant WARNING for history_eps={history_eps}, "
        f"target={target}, but none was emitted"
    )


# ---------------------------------------------------------------------------
# Invariant 3 — None tracker callbacks never crash
# ---------------------------------------------------------------------------


@given(
    target=st.integers(min_value=1, max_value=25),
)
@settings(max_examples=200)
def test_none_emotion_tracker_no_crash(target: int) -> None:
    """_assert_rollback_invariants completes without exception when emotion_tracker_fn is None."""
    svc = _make_service(emotion_tracker=None)
    svc._assert_rollback_invariants(target)  # must not raise


@given(
    target=st.integers(min_value=1, max_value=25),
)
@settings(max_examples=200)
def test_none_state_delta_tracker_no_crash(target: int) -> None:
    """_assert_rollback_invariants completes without exception when state_delta_tracker_fn is None."""
    svc = _make_service(state_delta_tracker=None)
    svc._assert_rollback_invariants(target)  # must not raise


@given(
    target=st.integers(min_value=1, max_value=25),
)
@settings(max_examples=200)
def test_both_trackers_none_no_crash(target: int) -> None:
    """_assert_rollback_invariants with both tracker callbacks None never crashes."""
    svc = _make_service()  # no trackers
    svc._assert_rollback_invariants(target)  # must not raise


# ---------------------------------------------------------------------------
# Invariant 4 — Tracker callbacks returning None objects never crash
# ---------------------------------------------------------------------------


@given(
    target=st.integers(min_value=1, max_value=25),
)
@settings(max_examples=200)
def test_callback_returning_none_no_crash(target: int) -> None:
    """Callbacks that return None (not the fn being None) never crash."""
    ui = MagicMock()
    ui.log = MagicMock()
    svc = ProjectService(
        project_fn=lambda: MagicMock(),
        ui=ui,
        safe_commit_fn=lambda: True,
        genre_fn=lambda: {},
        memory_fn=lambda: None,
        emotion_tracker_fn=lambda: None,       # callable but returns None
        state_delta_tracker_fn=lambda: None,   # callable but returns None
    )
    svc._assert_rollback_invariants(target)  # must not raise


# ---------------------------------------------------------------------------
# Invariant 5 — Empty histories never trigger WARNING
# ---------------------------------------------------------------------------


@given(
    target=st.integers(min_value=1, max_value=25),
)
@settings(max_examples=200)
def test_empty_emotion_history_no_warning(target: int) -> None:
    """Empty emotion history: _assert_rollback_invariants emits no RollbackInvariant WARNING."""
    et = _emotion_mock_with_history([])
    svc = _make_service(emotion_tracker=et)

    with patch.object(logging, "warning") as mock_warn:
        svc._assert_rollback_invariants(target)

    for call in mock_warn.call_args_list:
        args = call.args
        if args and isinstance(args[0], str) and "RollbackInvariant" in args[0]:
            assert False, f"Unexpected warning for empty emotion history: {call}"


@given(
    target=st.integers(min_value=1, max_value=25),
)
@settings(max_examples=200)
def test_empty_state_delta_history_no_warning(target: int) -> None:
    """Empty state_delta energy_history: no RollbackInvariant WARNING."""
    sdt = _state_delta_mock_with_history([])
    svc = _make_service(state_delta_tracker=sdt)

    with patch.object(logging, "warning") as mock_warn:
        svc._assert_rollback_invariants(target)

    for call in mock_warn.call_args_list:
        args = call.args
        if args and isinstance(args[0], str) and "RollbackInvariant" in args[0]:
            assert False, f"Unexpected warning for empty state_delta history: {call}"
