from modules.domain.agents.blueprint_ensemble import build_external_pov_policy_constraint


def test_build_external_pov_policy_constraint_first_person_limited():
    text = build_external_pov_policy_constraint("1인칭", "제한적 허용")

    assert "side_glimpse" in text
    assert "villain_scheme" in text
    assert "금지" in text


def test_build_external_pov_policy_constraint_mixed_active():
    text = build_external_pov_policy_constraint("혼합", "적극 허용")

    assert "scene" in text.lower()
    assert "villain_scheme" in text
    assert "same" in text.lower() or "동일" in text
