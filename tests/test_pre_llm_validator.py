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
