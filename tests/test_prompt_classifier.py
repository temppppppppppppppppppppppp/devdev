from modules.api.prompt_classifier import classify


def test_classify_uses_semantic_prompt_text_for_generic_choice_tail():
    result = classify(
        "👉 Choice (1-1):",
        [
            "  선택 (기본: 1):    📚 [Bible Selection] 사용할 성경(Lore)을 선택하십시오:",
            "   1. 01_bi_투자물_골든_카나리아 테스트.json",
        ],
    )

    assert result["input_type"] == "enum"
    assert result["prompt_text"] == "📚 [Bible Selection] 사용할 성경(Lore)을 선택하십시오:"
    assert result["options"] == [{"key": "1", "label": "01_bi_투자물_골든_카나리아 테스트.json"}]


def test_classify_sets_default_when_enum_has_single_option():
    result = classify(
        "👉 Choice (1-1, 미입력 시 1번):",
        [
            "   🧬 [Roadmap Selection] V25 상세 설계도(JSON)를 선택하십시오:",
            "   1. 01_tr_투자물_골든_카나리아 테스트.json",
        ],
    )

    assert result["input_type"] == "enum"
    assert result["default"] == "1"
    assert result["prompt_text"] == "🧬 [Roadmap Selection] V25 상세 설계도(JSON)를 선택하십시오:"
