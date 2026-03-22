from modules.validation.blocking_validator import BlockingValidator


def test_extract_owned_items_accepts_list_string_and_dict():
    validator = BlockingValidator()
    checks = validator.entity_checks

    assert checks._extract_owned_items({"actual_truth": {"equipment": ["천상검", 3, ""]}}) == ["천상검", "3"]
    assert checks._extract_owned_items({"actual_truth": {"equipment": "천상검"}}) == ["천상검"]
    assert checks._extract_owned_items({"actual_truth": {"equipment": {"천상검": True, "목검": False, 7: 1}}}) == [
        "천상검",
        "7",
    ]


def test_find_standalone_name_matches_skips_hangul_substring_but_keeps_particle_case():
    validator = BlockingValidator()
    checks = validator.entity_checks

    assert checks._find_standalone_name_matches("백근대도가 벽에 박혔다.", "대도") == []
    assert checks._find_standalone_name_matches("대도를 휘둘렀다.", "대도") == [0]


def test_check_unowned_item_name_usage_skips_negation_sentence():
    validator = BlockingValidator()
    checks = validator.entity_checks

    result = checks._check_unowned_item_name_usage(
        "그는 천상검을 사용하지 않았다.",
        item_name="천상검",
        check_name="천상검",
        owned_items=[],
    )

    assert result is None


def test_check_unowned_item_usage_respects_owned_alias_registry():
    validator = BlockingValidator()
    manuscript = "그는 백근대도를 사용해 벽을 부쉈다."
    context = {
        "encyclopedia": {"items": [{"name": "대도", "aliases": ["백근대도"]}]},
        "martial_hud": {"actual_truth": {"equipment": ["대도"]}},
    }

    result = validator.entity_checks._check_unowned_item_usage(manuscript, context)

    assert result["passed"] is True


def test_check_unowned_item_usage_reports_alias_display_name():
    validator = BlockingValidator()
    manuscript = "그는 백근대도를 사용해 벽을 부쉈다."
    context = {
        "encyclopedia": {"items": [{"name": "대도", "aliases": ["백근대도"]}]},
        "martial_hud": {"actual_truth": {"equipment": []}},
    }

    result = validator.entity_checks._check_unowned_item_usage(manuscript, context)

    assert result["passed"] is False
    assert result["item_name"] == "대도"
    assert result["matched_alias"] == "백근대도"
    assert "백근대도 (대도)" in result["reason"]
