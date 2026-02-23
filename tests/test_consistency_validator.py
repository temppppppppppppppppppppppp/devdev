"""[Sweep20] Regression tests for consistency validator guards."""

from unittest.mock import patch

from modules.validation.consistency_validator import ConsistencyValidator


class _AuthorityGuard:
    def check_state_action_consistency(self, manuscript, current_state):
        return {"passed": True, "violations": []}

    def check_hierarchy_consistency(self, manuscript, character_rank):
        return {"passed": True, "violations": []}

    def check_authority_delegation(self, manuscript, authority_context):
        return {
            "passed": False,
            "violations": [
                {"reason": "delegation with justification", "has_justification": True, "severity": "MEDIUM"},
                {"reason": "delegation without justification", "has_justification": False, "severity": "HIGH"},
            ],
        }

    def get_delegation_patterns(self):
        return []


class _EffectRuleGuard:
    def get_technique_effect_rules(self):
        return None


def test_authority_delegation_uses_per_violation_justification_flag():
    validator = ConsistencyValidator(guard=_AuthorityGuard())
    result = validator.validate(
        manuscript="테스트 원고",
        validation_context={
            "martial_hud": {},
            "authority_context": {"has_chain_of_command": True},
        },
    )

    justifiable = [v for v in result["justifiable_violations"] if v.get("category") == "authority_delegation"]
    unjustifiable = [v for v in result["unjustifiable_violations"] if v.get("category") == "authority_delegation"]

    assert len(justifiable) == 1
    assert len(unjustifiable) == 1
    assert justifiable[0]["reason"] == "delegation with justification"
    assert unjustifiable[0]["reason"] == "delegation without justification"


def test_effect_consistency_guard_handles_none_rule_map():
    validator = ConsistencyValidator(guard=_EffectRuleGuard())
    result = validator._check_effect_consistency("테스트 원고", asset_library=None)
    assert result == {"passed": True, "violations": []}


def test_load_guard_for_supported_nonlegacy_genre_uses_factory():
    fake_guard = object()
    with patch("modules.validation.consistency_validator.create_genre_guard", return_value=fake_guard) as mock_factory:
        validator = ConsistencyValidator(guard=None, genre="fantasy")

    assert validator.guard is fake_guard
    mock_factory.assert_called_once_with("fantasy")
