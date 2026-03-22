from modules.core.agent_intelligence import AgentIntelligence, AgentType, Exemplar


def test_init_exemplars_populates_expected_family_catalogs():
    intel = AgentIntelligence(genre="wuxia")

    assert sorted(intel.analyst_exemplars) == ["hunter", "investment", "wuxia"]
    assert sorted(intel.architect_exemplars) == ["wuxia"]
    assert sorted(intel.writer_exemplars) == ["wuxia"]
    assert [item.title for item in intel.analyst_exemplars["wuxia"]] == [
        "복수극 Arc 설계",
        "성장 Arc 설계",
    ]
    assert all(isinstance(item, Exemplar) for item in intel.writer_exemplars["wuxia"])


def test_get_few_shot_prompt_uses_genre_specific_analyst_examples():
    intel = AgentIntelligence(genre="hunter")

    prompt = intel.get_few_shot_prompt(AgentType.ANALYST)

    assert "던전 공략 Arc" in prompt
    assert "복수극 Arc 설계" not in prompt


def test_get_few_shot_prompt_falls_back_to_wuxia_and_keeps_two_example_cap():
    intel = AgentIntelligence(genre="science-fantasy")

    writer_prompt = intel.get_few_shot_prompt(AgentType.WRITER)
    architect_prompt = intel.get_few_shot_prompt(AgentType.ARCHITECT)

    assert "전투 묘사" in writer_prompt
    assert "감정 묘사" in writer_prompt
    assert "대화와 행동" not in writer_prompt
    assert "대결 장면 Blueprint" in architect_prompt
