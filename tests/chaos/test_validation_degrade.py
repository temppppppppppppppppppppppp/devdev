"""[P7-04] ContinuityValidator degraded-path tests.

Verifies that ContinuityValidator.validate() returns a DEGRADED result
when prev_hud is absent.

Policy change (TF-15 P0-06): prev_hud 누락 시 fail-closed (passed=False)
로 전환. 이전에는 passed=True(fail-open)였으나, 검증 우회를 방지하기
위해 passed=False + degraded=True + BLOCKING 위반으로 변경됨.
"""

from modules.validation.continuity_validator import ContinuityValidator

# A manuscript just long enough; content does not matter for these tests.
_MANUSCRIPT = "가" * 200


# ---------------------------------------------------------------------------
# Test 1: validate() with prev_hud=None returns degraded=True, passed=True
# ---------------------------------------------------------------------------


def test_validate_prev_hud_none_returns_degraded():
    validator = ContinuityValidator(context=None)
    # Provide an empty validation_context so there is no fallback source
    result = validator.validate(
        current_ep=5,
        manuscript=_MANUSCRIPT,
        validation_context={},
        prev_hud=None,
    )

    assert result["passed"] is False, "DEGRADED path must fail-closed (TF-15 P0-06)"
    assert result.get("degraded") is True, "DEGRADED flag must be set when prev_hud is None"
    assert result["tier"] == "CONTINUITY"
    assert any(v.get("severity") == "BLOCKING" for v in result.get("violations", [])), (
        "DEGRADED path must include BLOCKING violation"
    )


# ---------------------------------------------------------------------------
# Test 2: validate() with prev_hud={} (empty dict) returns degraded=True
# ---------------------------------------------------------------------------


def test_validate_prev_hud_empty_dict_returns_degraded():
    validator = ContinuityValidator(context=None)
    result = validator.validate(
        current_ep=5,
        manuscript=_MANUSCRIPT,
        validation_context={},
        prev_hud={},
    )

    assert result["passed"] is False, "empty prev_hud must fail-closed (TF-15 P0-06)"
    assert result.get("degraded") is True


# ---------------------------------------------------------------------------
# Test 3: validate() with valid prev_hud does NOT set degraded=True
# ---------------------------------------------------------------------------


def test_validate_with_valid_prev_hud_not_degraded():
    validator = ContinuityValidator(context=None)
    # Provide a minimal but non-empty prev_hud so the normal path runs
    prev_hud = {
        "actual_truth": {
            "equipment": [],
            "weapons": [],
            "injuries": "정상",
            "location": "장안",
        }
    }
    result = validator.validate(
        current_ep=5,
        manuscript=_MANUSCRIPT,
        validation_context={},
        prev_hud=prev_hud,
    )

    assert result.get("degraded") is not True, "degraded must NOT be True when a valid prev_hud is supplied"
    assert result["tier"] == "CONTINUITY"


# ---------------------------------------------------------------------------
# Test 4: First episode (ep=1) always passes without DEGRADED flag
# ---------------------------------------------------------------------------


def test_validate_first_episode_skips_continuity_check():
    validator = ContinuityValidator(context=None)
    result = validator.validate(
        current_ep=1,
        manuscript=_MANUSCRIPT,
        validation_context={},
        prev_hud=None,
    )

    assert result["passed"] is True
    # Episode 1 has no prior episode, so DEGRADED should not apply
    assert result.get("degraded") is not True


# ---------------------------------------------------------------------------
# Test 5: validate() with prev_hud injected via validation_context degrades
#         only if the value resolves to falsy
# ---------------------------------------------------------------------------


def test_validate_prev_hud_none_in_context_returns_degraded():
    validator = ContinuityValidator(context=None)
    # Put None under "prev_hud" key — should still trigger degraded path
    result = validator.validate(
        current_ep=3,
        manuscript=_MANUSCRIPT,
        validation_context={"prev_hud": None},
        prev_hud=None,
    )

    assert result["passed"] is False, "prev_hud=None in context must fail-closed (TF-15 P0-06)"
    assert result.get("degraded") is True
