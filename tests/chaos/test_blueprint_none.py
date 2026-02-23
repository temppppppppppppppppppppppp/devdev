"""[P7-02] BlockingValidator blueprint=None fail-safe tests.

Verifies that TF-7-P0-05 patch prevents AttributeError when blueprint is
None, missing, or an unexpected type in the validation context.
"""

from modules.validation.blocking_validator import BlockingValidator

# A manuscript long enough to pass minimum-length check so other checks
# can be observed. MIN_LENGTH is 800; using 900 characters of Korean text.
_LONG_MANUSCRIPT = "가" * 900

# A minimal valid context with no blueprint key at all.
_BASE_CONTEXT = {
    "mode": "MANUSCRIPT",
    "encyclopedia": {"npcs": [], "items": [], "locations": []},
    "martial_hud": {"actual_truth": {"equipment": []}},
}


# ---------------------------------------------------------------------------
# Test 1: validate() with blueprint=None does not raise AttributeError
# ---------------------------------------------------------------------------

def test_validate_blueprint_none_does_not_raise():
    validator = BlockingValidator()
    context = {**_BASE_CONTEXT, "blueprint": None}

    # Must not raise; result must be a dict with "passed" key
    result = validator.validate(_LONG_MANUSCRIPT, context)
    assert isinstance(result, dict)
    assert "passed" in result


# ---------------------------------------------------------------------------
# Test 2: validate() with blueprint={} does not crash
# ---------------------------------------------------------------------------

def test_validate_blueprint_empty_dict_does_not_crash():
    validator = BlockingValidator()
    context = {**_BASE_CONTEXT, "blueprint": {}}

    result = validator.validate(_LONG_MANUSCRIPT, context)
    assert isinstance(result, dict)
    assert "passed" in result


# ---------------------------------------------------------------------------
# Test 3: validate() with no "blueprint" key in context does not crash
# ---------------------------------------------------------------------------

def test_validate_no_blueprint_key_does_not_crash():
    validator = BlockingValidator()
    # Deliberately omit "blueprint" from context
    context = {
        "mode": "MANUSCRIPT",
        "encyclopedia": {"npcs": [], "items": [], "locations": []},
        "martial_hud": {"actual_truth": {"equipment": []}},
    }

    result = validator.validate(_LONG_MANUSCRIPT, context)
    assert isinstance(result, dict)
    assert "passed" in result


# ---------------------------------------------------------------------------
# Test 4: _check_required_scenes directly with blueprint=None passes
# ---------------------------------------------------------------------------

def test_scene_checks_blueprint_none_returns_passed():
    validator = BlockingValidator()
    context = {"blueprint": None}

    result = validator.scene_checks._check_required_scenes(_LONG_MANUSCRIPT, context)

    assert result["passed"] is True
    assert result["check"] == "required_scenes"


# ---------------------------------------------------------------------------
# Test 5: _check_required_scenes with non-dict blueprint (e.g. a string)
# ---------------------------------------------------------------------------

def test_scene_checks_blueprint_string_returns_passed():
    validator = BlockingValidator()
    context = {"blueprint": "invalid-string-blueprint"}

    result = validator.scene_checks._check_required_scenes(_LONG_MANUSCRIPT, context)

    assert result["passed"] is True
