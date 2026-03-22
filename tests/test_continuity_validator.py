"""Regression tests for continuity validator history ordering."""

from modules.validation.continuity_validator import ContinuityValidator


def test_personality_sudden_change_uses_chronological_npc_history_order():
    validator = ContinuityValidator(context=None)

    validation_context = {
        "npc_personalities": {"장철": {"traits": "냉혹", "motivation": "복수"}},
        "npc_history": {
            "장철": [
                {
                    "id": 3,
                    "episode_no": 12,
                    "field_name": "personality_traits",
                    "new_value": "온화",
                },
                {
                    "id": 2,
                    "episode_no": 11,
                    "field_name": "personality_traits",
                    "new_value": "냉혹",
                },
                {
                    "id": 1,
                    "episode_no": 10,
                    "field_name": "personality_traits",
                    "new_value": "냉혹",
                },
            ]
        },
    }

    result = validator._check_personality_continuity("장철이 회의장에 들어섰다.", validation_context)

    sudden_changes = [v for v in result["violations"] if v.get("type") == "personality_sudden_change"]
    assert len(sudden_changes) == 1
    assert sudden_changes[0]["npc"] == "장철"


def test_personality_growth_keyword_downgrades_nearby_contradiction():
    validator = ContinuityValidator(context=None)

    validation_context = {
        "npc_personalities": {"장무기": {"traits": "냉정"}},
        "npc_history": {},
    }

    result = validator._check_personality_continuity(
        "장무기는 오랜 반성 끝에 깨달음을 얻었고 따뜻한 미소를 지었다.",
        validation_context,
    )

    contradictions = [v for v in result["violations"] if v.get("type") == "personality_contradiction"]
    assert len(contradictions) == 1
    assert contradictions[0]["npc"] == "장무기"
    assert contradictions[0]["growth_context"] is True
    assert contradictions[0]["severity"] == "MINOR"
