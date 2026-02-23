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
