"""Property-based tests for validation boundary conditions.

Key invariants:
1. prev_hud=None (and not resolvable) -> degraded=True, passed=True
2. blueprint=None in context never raises AttributeError
3. blueprint={} in context never raises
4. Degraded result structure is always {"passed": True, "degraded": True, warnings: [non-empty]}
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.validation.blocking_validator_scene_checks import (  # noqa: E402
    BlockingValidatorSceneChecks,
)
from modules.validation.continuity_validator import ContinuityValidator  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_minimal_context(extra: dict | None = None) -> dict:
    """Build the smallest valid context for ContinuityValidator.validate()."""
    ctx: dict = {}
    if extra:
        ctx.update(extra)
    return ctx


def _make_scene_checks_host():
    """Build a minimal host object for BlockingValidatorSceneChecks.

    BlockingValidatorSceneChecks needs host.consistency_checks._extract_keywords.
    We provide a minimal stub so we can exercise the blueprint=None path.
    """
    from unittest.mock import MagicMock

    host = MagicMock()
    # _extract_keywords is called inside _check_required_scenes and
    # _check_scene_completeness.  Return an empty set so nothing matches,
    # which is fine for our "never-raises" invariant.
    host.consistency_checks._extract_keywords.return_value = set()
    return host


# ---------------------------------------------------------------------------
# ContinuityValidator — prev_hud=None always degraded
# ---------------------------------------------------------------------------

# Strategies
_text_st = st.text(min_size=0, max_size=500)
_small_dict_st = st.dictionaries(
    st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("L",))),
    st.text(min_size=0, max_size=20),
    max_size=5,
)


@given(
    manuscript=_text_st,
    current_ep=st.integers(min_value=2, max_value=100),
)
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_continuity_no_prev_hud_always_degraded(
    manuscript: str, current_ep: int
) -> None:
    """When no prev_hud is available, validate() returns degraded=True, passed=True."""
    validator = ContinuityValidator(context=None)
    # Empty context: no prev_hud key anywhere
    ctx: dict = {}
    result = validator.validate(
        current_ep=current_ep,
        manuscript=manuscript,
        validation_context=ctx,
        prev_hud=None,
    )
    assert isinstance(result, dict), "validate() must return a dict"
    assert result.get("degraded") is True, (
        f"Expected degraded=True when prev_hud absent, got: {result}"
    )
    assert result.get("passed") is True, (
        f"Expected passed=True in degraded path, got: {result}"
    )


@given(
    manuscript=_text_st,
    current_ep=st.integers(min_value=2, max_value=100),
    extra_ctx=_small_dict_st,
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_continuity_no_prev_hud_degraded_structure(
    manuscript: str, current_ep: int, extra_ctx: dict
) -> None:
    """Degraded result always has passed=True and at least one warning."""
    validator = ContinuityValidator(context=None)
    result = validator.validate(
        current_ep=current_ep,
        manuscript=manuscript,
        validation_context=extra_ctx,
        prev_hud=None,
    )
    if result.get("degraded"):
        assert result["passed"] is True
        warnings = result.get("warnings", [])
        assert len(warnings) >= 1, (
            "Degraded result must carry at least one warning"
        )


@given(
    manuscript=_text_st,
)
@settings(max_examples=200)
def test_continuity_ep1_always_passes(manuscript: str) -> None:
    """Episode 1 always passes regardless of prev_hud."""
    validator = ContinuityValidator(context=None)
    result = validator.validate(
        current_ep=1,
        manuscript=manuscript,
        validation_context={},
        prev_hud=None,
    )
    assert result["passed"] is True
    assert result.get("degraded") is not True


@given(
    manuscript=_text_st,
    current_ep=st.integers(min_value=2, max_value=100),
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_continuity_validate_always_returns_dict(
    manuscript: str, current_ep: int
) -> None:
    """validate() never raises; always returns a dict."""
    validator = ContinuityValidator(context=None)
    result = validator.validate(
        current_ep=current_ep,
        manuscript=manuscript,
        validation_context={},
        prev_hud=None,
    )
    assert isinstance(result, dict)
    assert "passed" in result
    assert "tier" in result


# ---------------------------------------------------------------------------
# BlockingValidatorSceneChecks — blueprint=None / {} never raises
# ---------------------------------------------------------------------------


@given(
    manuscript=_text_st,
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_scene_checks_blueprint_none_never_raises(manuscript: str) -> None:
    """_check_required_scenes and _check_scope_overflow with blueprint=None never raise."""
    host = _make_scene_checks_host()
    checker = BlockingValidatorSceneChecks(host)
    ctx = {"blueprint": None, "mode": "MANUSCRIPT"}

    result_req = checker._check_required_scenes(manuscript, ctx)
    result_scope = checker._check_scope_overflow(manuscript, ctx)
    result_complete = checker._check_scene_completeness(manuscript, ctx)
    result_cliff = checker._check_cliffhanger_ending(manuscript, ctx)

    assert isinstance(result_req, dict)
    assert isinstance(result_scope, dict)
    assert isinstance(result_complete, dict)
    assert isinstance(result_cliff, dict)


@given(
    manuscript=_text_st,
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_scene_checks_blueprint_empty_dict_never_raises(manuscript: str) -> None:
    """All scene checks with blueprint={} never raise AttributeError."""
    host = _make_scene_checks_host()
    checker = BlockingValidatorSceneChecks(host)
    ctx = {"blueprint": {}, "mode": "MANUSCRIPT"}

    result_req = checker._check_required_scenes(manuscript, ctx)
    result_scope = checker._check_scope_overflow(manuscript, ctx)
    result_complete = checker._check_scene_completeness(manuscript, ctx)
    result_cliff = checker._check_cliffhanger_ending(manuscript, ctx)

    assert isinstance(result_req, dict)
    assert isinstance(result_scope, dict)
    assert isinstance(result_complete, dict)
    assert isinstance(result_cliff, dict)


@given(
    manuscript=_text_st,
    blueprint_value=st.one_of(
        st.none(),
        st.just({}),
        st.just("not_a_dict"),
        st.just(42),
        st.just([]),
    ),
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_scene_checks_arbitrary_blueprint_never_raises(
    manuscript: str, blueprint_value: object
) -> None:
    """Scene checks never raise for any non-dict blueprint value."""
    host = _make_scene_checks_host()
    checker = BlockingValidatorSceneChecks(host)
    ctx = {"blueprint": blueprint_value, "mode": "MANUSCRIPT"}

    # None of these should raise
    checker._check_required_scenes(manuscript, ctx)
    checker._check_scope_overflow(manuscript, ctx)
    checker._check_scene_completeness(manuscript, ctx)
    checker._check_cliffhanger_ending(manuscript, ctx)


@given(
    manuscript=_text_st,
    blueprint_value=st.one_of(st.none(), st.just({})),
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_scene_checks_none_blueprint_required_scenes_passes(
    manuscript: str, blueprint_value: object
) -> None:
    """With blueprint=None or {}, _check_required_scenes always returns passed=True."""
    host = _make_scene_checks_host()
    checker = BlockingValidatorSceneChecks(host)
    ctx = {"blueprint": blueprint_value, "mode": "MANUSCRIPT"}

    result = checker._check_required_scenes(manuscript, ctx)
    assert result["passed"] is True, (
        f"required_scenes must pass when blueprint has no scene_breakdown: {result}"
    )


@given(
    manuscript=_text_st,
    blueprint_value=st.one_of(st.none(), st.just({})),
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_scene_checks_none_blueprint_scene_completeness_passes(
    manuscript: str, blueprint_value: object
) -> None:
    """With blueprint=None or {}, _check_scene_completeness always passes."""
    host = _make_scene_checks_host()
    checker = BlockingValidatorSceneChecks(host)
    ctx = {"blueprint": blueprint_value, "mode": "MANUSCRIPT"}

    result = checker._check_scene_completeness(manuscript, ctx)
    assert result["passed"] is True, (
        f"scene_completeness must pass when blueprint has no scene_breakdown: {result}"
    )
