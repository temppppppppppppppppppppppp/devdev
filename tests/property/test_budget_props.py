"""Property-based tests for ContextAdvisor slot budget assignment.

Key invariants:
1. min_chars floor respected: every slot.max_chars >= 1500 (slot_max_chars_default)
2. Positive budget assigns positive chars to all slots
3. Zero or negative budget leaves slots unchanged (max_chars stays at initial 0)
4. Priority ordering: higher-priority slots get >= chars than lower-priority slots
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.context_advisor import ContextAdvisor, RetrievalSlot  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MIN_CHARS_DEFAULT = 1500  # smart_retrieval.slot_max_chars_default


def _make_enabled_advisor() -> ContextAdvisor:
    advisor = ContextAdvisor()
    advisor.enabled = True
    advisor._is_stage_enabled = lambda _stage: True
    return advisor


def _make_slots(priorities: list[int]) -> list[RetrievalSlot]:
    """Create one slot per priority value. max_chars starts at 0."""
    return [
        RetrievalSlot(
            category=f"cat_{i}",
            query=f"query {i}",
            priority=p,
            max_chars=0,
        )
        for i, p in enumerate(priorities)
    ]


# ---------------------------------------------------------------------------
# Invariant 1 — min_chars floor
# ---------------------------------------------------------------------------


@given(
    priorities=st.lists(
        st.integers(min_value=1, max_value=3), min_size=1, max_size=10
    ),
    total_budget=st.integers(min_value=1, max_value=100_000),
)
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_slot_min_chars_respected(priorities: list[int], total_budget: int) -> None:
    """After _assign_slot_budgets(), every slot.max_chars >= _MIN_CHARS_DEFAULT."""
    advisor = _make_enabled_advisor()
    slots = _make_slots(priorities)

    # Monkey-patch _get_stage_budget to return our controlled total_budget
    advisor._get_stage_budget = lambda _stage: total_budget

    advisor._assign_slot_budgets("stage4", slots)

    for slot in slots:
        assert slot.max_chars >= _MIN_CHARS_DEFAULT, (
            f"Slot priority={slot.priority} has max_chars={slot.max_chars} "
            f"< floor={_MIN_CHARS_DEFAULT} (budget={total_budget})"
        )


# ---------------------------------------------------------------------------
# Invariant 2 — positive budget assigns positive chars
# ---------------------------------------------------------------------------


@given(
    priorities=st.lists(
        st.integers(min_value=1, max_value=3), min_size=1, max_size=10
    ),
    total_budget=st.integers(min_value=1, max_value=100_000),
)
@settings(max_examples=300)
def test_positive_budget_assigns_positive_chars(
    priorities: list[int], total_budget: int
) -> None:
    """When total_budget > 0, every slot gets max_chars > 0."""
    advisor = _make_enabled_advisor()
    slots = _make_slots(priorities)
    advisor._get_stage_budget = lambda _stage: total_budget
    advisor._assign_slot_budgets("stage2", slots)
    for slot in slots:
        assert slot.max_chars > 0, (
            f"Slot got max_chars=0 with positive budget={total_budget}"
        )


# ---------------------------------------------------------------------------
# Invariant 3 — zero budget skips assignment
# ---------------------------------------------------------------------------


@given(
    priorities=st.lists(
        st.integers(min_value=1, max_value=3), min_size=1, max_size=10
    ),
)
@settings(max_examples=200)
def test_zero_budget_skips_assignment(priorities: list[int]) -> None:
    """When total_budget == 0, slots are unchanged (max_chars stays 0)."""
    advisor = _make_enabled_advisor()
    slots = _make_slots(priorities)
    advisor._get_stage_budget = lambda _stage: 0
    advisor._assign_slot_budgets("stage4", slots)
    for slot in slots:
        assert slot.max_chars == 0, (
            f"Slot max_chars was modified with zero budget: {slot.max_chars}"
        )


# ---------------------------------------------------------------------------
# Invariant 4 — priority ordering
# ---------------------------------------------------------------------------


@given(
    n_high=st.integers(min_value=1, max_value=5),
    n_low=st.integers(min_value=1, max_value=5),
    total_budget=st.integers(min_value=1, max_value=100_000),
)
@settings(max_examples=300)
def test_priority_1_slots_ge_priority_3_slots(
    n_high: int, n_low: int, total_budget: int
) -> None:
    """Priority-1 slots must receive >= chars than priority-3 slots."""
    advisor = _make_enabled_advisor()
    slots = _make_slots([1] * n_high + [3] * n_low)
    advisor._get_stage_budget = lambda _stage: total_budget
    advisor._assign_slot_budgets("stage4", slots)

    high_slots = [s for s in slots if s.priority == 1]
    low_slots = [s for s in slots if s.priority == 3]

    min_high = min(s.max_chars for s in high_slots)
    max_low = max(s.max_chars for s in low_slots)
    assert min_high >= max_low, (
        f"Priority-1 min={min_high} < priority-3 max={max_low} "
        f"(budget={total_budget}, n_high={n_high}, n_low={n_low})"
    )


@given(
    n_high=st.integers(min_value=1, max_value=5),
    n_mid=st.integers(min_value=1, max_value=5),
    total_budget=st.integers(min_value=1, max_value=100_000),
)
@settings(max_examples=200)
def test_priority_1_slots_ge_priority_2_slots(
    n_high: int, n_mid: int, total_budget: int
) -> None:
    """Priority-1 slots must receive >= chars than priority-2 slots."""
    advisor = _make_enabled_advisor()
    slots = _make_slots([1] * n_high + [2] * n_mid)
    advisor._get_stage_budget = lambda _stage: total_budget
    advisor._assign_slot_budgets("stage3", slots)

    high_slots = [s for s in slots if s.priority == 1]
    mid_slots = [s for s in slots if s.priority == 2]

    min_high = min(s.max_chars for s in high_slots)
    max_mid = max(s.max_chars for s in mid_slots)
    assert min_high >= max_mid, (
        f"Priority-1 min={min_high} < priority-2 max={max_mid} "
        f"(budget={total_budget})"
    )


@given(
    priorities=st.lists(
        st.integers(min_value=1, max_value=3), min_size=1, max_size=10
    ),
    total_budget=st.integers(min_value=1, max_value=100_000),
)
@settings(max_examples=300)
def test_equal_priority_slots_get_equal_chars(
    priorities: list[int], total_budget: int
) -> None:
    """Slots with the same priority value must receive the same max_chars."""
    advisor = _make_enabled_advisor()
    slots = _make_slots(priorities)
    advisor._get_stage_budget = lambda _stage: total_budget
    advisor._assign_slot_budgets("stage4", slots)

    for p in [1, 2, 3]:
        group = [s.max_chars for s in slots if s.priority == p]
        if len(group) > 1:
            assert len(set(group)) == 1, (
                f"Priority-{p} slots have unequal chars: {group}"
            )


# ---------------------------------------------------------------------------
# Invariant — empty slots list is a no-op (no crash)
# ---------------------------------------------------------------------------


@given(
    total_budget=st.integers(min_value=0, max_value=100_000),
)
@settings(max_examples=100)
def test_empty_slots_no_crash(total_budget: int) -> None:
    """_assign_slot_budgets with empty slot list never raises."""
    advisor = _make_enabled_advisor()
    advisor._get_stage_budget = lambda _stage: total_budget
    advisor._assign_slot_budgets("stage2", [])  # must not raise
