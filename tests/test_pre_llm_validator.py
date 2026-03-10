"""Unit tests for PreLLMValidator."""

from modules.validation.pre_llm_validator import PreLLMValidator


def test_check_npc_naming_detects_single_char_variation():
    validator = PreLLMValidator()
    manuscript = "사헌은 검을 들고 전장으로 뛰어들었다. 사현은 뒤를 지켰다."
    context = {
        "npc_profiles": {"사현": {}},
        "encyclopedia": {"npcs": [{"name": "사현"}]},
    }

    result = validator._check_npc_naming(manuscript, context)

    assert any(found == "사헌" and correct == "사현" for found, correct in result["inconsistencies"])


def test_check_npc_naming_ignores_exact_name_match():
    validator = PreLLMValidator()
    manuscript = "사현이 검을 들어 올렸다."
    context = {
        "npc_profiles": {"사현": {}},
        "encyclopedia": {"npcs": [{"name": "사현"}]},
    }

    result = validator._check_npc_naming(manuscript, context)

    assert result["inconsistencies"] == []


def test_check_pov_consistency_warns_for_omniscient_first_person_leak():
    validator = PreLLMValidator(pov="전지적", protagonist_name="진우")
    manuscript = (
        "나는 숨을 골랐다. 내가 칼을 쥐었다. 나는 다시 일어섰다. "
        "내가 숨을 삼켰다. 나는 천천히 고개를 들었다. 내가 앞을 봤다."
    )

    result = validator._check_pov_consistency(manuscript)

    assert result["has_issue"] is True
    assert result["expected_pov"] == "전지적"


def test_check_pov_consistency_warns_for_mixed_pov_without_scene_separator():
    validator = PreLLMValidator(pov="혼합", protagonist_name="진우")
    manuscript = (
        "나는 검을 들었다. 내가 숨을 삼켰다. 나는 천천히 발을 옮겼다. "
        "진우는 문을 밀었다. 진우가 복도를 바라봤다. 그는 다시 걸었다."
    )

    result = validator._check_pov_consistency(manuscript)

    assert result["has_issue"] is True
    assert "혼합 시점" in result["description"]


def test_check_pov_consistency_allows_mixed_pov_with_scene_separator():
    validator = PreLLMValidator(pov="혼합", protagonist_name="진우")
    manuscript = (
        "나는 검을 들었다. 내가 숨을 삼켰다. 나는 천천히 발을 옮겼다.\n"
        "***\n"
        "진우는 문을 밀었다. 진우가 복도를 바라봤다. 그는 다시 걸었다."
    )

    result = validator._check_pov_consistency(manuscript)

    assert result["has_issue"] is False
