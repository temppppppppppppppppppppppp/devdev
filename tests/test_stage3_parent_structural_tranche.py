from modules.domain.agents.director_ensemble import DirectorEnsembleSelector
from modules.domain.agents.unified_blueprint_validator import BLUEPRINT_MIN_CHARS


def test_director_compare_prompt_uses_stage3_blueprint_min_chars():
    selector = DirectorEnsembleSelector.__new__(DirectorEnsembleSelector)
    candidates = [
        {
            "integrated_scenario": "A" * (BLUEPRINT_MIN_CHARS + 20),
            "scene_breakdown": {"scene_1": {"summary": "alpha"}, "scene_2": {"summary": "beta"}},
            "start_location": "office",
            "end_location": "office",
            "time_flow": "morning",
            "ending_hook": "call arrives",
            "_ensemble_meta": {"strategy": "balanced", "scene_count": 2, "length": BLUEPRINT_MIN_CHARS + 20},
        },
        {
            "integrated_scenario": "B" * (BLUEPRINT_MIN_CHARS + 30),
            "scene_breakdown": {"scene_1": {"summary": "alpha"}, "scene_2": {"summary": "beta"}},
            "start_location": "office",
            "end_location": "home",
            "time_flow": "morning -> night",
            "ending_hook": "door opens",
            "_ensemble_meta": {"strategy": "dense", "scene_count": 2, "length": BLUEPRINT_MIN_CHARS + 30},
        },
    ]

    prompt = selector._build_blueprint_compare_prompt(
        candidates=candidates,
        arc_data={"tactical_doc": "제1화: 도입", "episode_details": []},
        ep_num=1,
        prev_blueprint=None,
    )

    assert f"{BLUEPRINT_MIN_CHARS}자 미만" in prompt
    assert "1000자 미만" not in prompt
