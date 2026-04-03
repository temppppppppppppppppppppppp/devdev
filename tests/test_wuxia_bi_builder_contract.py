from __future__ import annotations

import scripts.build_wuxia_bi_from_phase0_and_tr as build_script


def _build_phase0() -> dict:
    return {
        "project": {
            "title_ko": "Wuxia Project",
            "title": "Wuxia Project",
            "format": "wuxia",
            "logline": "A fallen disciple climbs again.",
            "core_premise": "A regressor survives sect politics and climbs through martial insight.",
            "start_year": "late dynasty",
            "end_year": "restored order",
        },
        "setting": {
            "resource_state": "lean",
            "starter_faction": {"name": "Azure Sect"},
            "jianghu_phase": "fractured order",
            "execution_doctrine": "win through technique and timing",
        },
        "protagonist": {
            "name": "Seo Jin",
            "public_image": "Quiet Blade",
            "age_at_start": 22,
            "status": "outer disciple",
            "initial_goal": "survive the purge",
            "mid_goal": "retake the archive",
            "final_goal": "break the blood feud",
            "true_strength": "reads movement before intent fully forms",
            "true_weakness": "old meridian injury",
            "signature_art": "Falling Star Sword",
            "mental_method": "Still Water Breathing",
            "reputation": "unknown",
            "inventory": ["travel blade"],
            "martial_arts": ["Falling Star Sword"],
        },
        "phase0_design": {
            "arcs": [
                {"arc_id": "arc_1", "title": "Purged Disciple", "main_opponents": ["Iron Hall"], "block_range": "1-2", "time_window": "spring"},
            ],
            "npc_timeline": [{"name": "Master Han", "role": "mentor"}],
            "foreshadow_map": [{"id": "S-001", "description": "The blood seal hidden in the archive."}],
            "opponent_transition_plan": [{"faction": "Iron Hall", "goal": "seal the archive"}],
        },
    }


def _build_blocks(*, is_regressor: bool) -> list[dict]:
    regression_type = "회귀" if is_regressor else "none"
    return [
        {
            "block_id": f"Block {idx}",
            "title": f"Block {idx} title",
            "content": {
                "context": f"Block {idx} context",
                "event_villain": f"Block {idx} villain move",
                "solution": f"Block {idx} solution",
                "reward": f"Block {idx} reward",
            },
            "stakes": f"stakes {idx}",
            "power_shift": {"protagonist": "gains initiative", "antagonist": "loses control"},
            "relationship_delta": [],
            "foreshadow": [],
            "callback": [],
            "emotional_beat": {"type": "resolve", "intensity": 7},
            "tension_level": 8,
            "pov_character": "Seo Jin",
            "location": {"place": f"sect-yard-{idx}", "type": "sect courtyard"},
            "time_span": {"duration": "1 day", "in_story_time": f"spring day {idx}"},
            "martial_ext": {"realm_after": "Body Tempering"},
            "regression_ext": {"is_regressor": is_regressor, "regression_type": regression_type},
        }
        for idx in range(1, 3)
    ]


def test_build_wuxia_bi_emits_runtime_protagonist_contract_and_block_numbers():
    bible = build_script.build_bible(_build_phase0(), _build_blocks(is_regressor=False))

    protagonist_config = bible["MasterBible"]["protagonist_config"]
    roadmap = bible["MasterBible"]["plot_roadmap"]

    assert protagonist_config["world_origin"] == "원시인"
    assert protagonist_config["incarnation_type"] == "일반"
    assert protagonist_config["pov"] == "3인칭"
    assert protagonist_config["external_pov_insert_policy"] == "제한적 허용"
    assert roadmap[0]["block_no"] == 1
    assert roadmap[1]["block_no"] == 2


def test_build_wuxia_bi_promotes_regressor_treatment_to_runtime_incarnation_type():
    bible = build_script.build_bible(_build_phase0(), _build_blocks(is_regressor=True))

    protagonist_config = bible["MasterBible"]["protagonist_config"]

    assert protagonist_config["incarnation_type"] == "회귀자"
