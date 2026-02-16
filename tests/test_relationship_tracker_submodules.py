"""[R5-2b] RelationshipTracker submodule tests."""

from modules.core.relationship_tracker import RelationshipTracker


def _first_valid_transition(states: dict) -> tuple[str, str]:
    for from_state, spec in states.items():
        targets = spec.get("can_transition_to", [])
        if targets:
            return from_state, targets[0]
    raise AssertionError("No valid transition found")


class TestNPCSubmodule:
    def test_validate_transition_normal(self):
        rt = RelationshipTracker()
        from_state, to_state = _first_valid_transition(rt.npc.STATES)

        result = rt.npc.validate_transition("npc_a", from_state, to_state)

        assert result["valid"] is True

    def test_validate_risky_transition(self):
        rt = RelationshipTracker()
        from_state, to_state = next(iter(rt.npc.RISKY_TRANSITIONS.keys()))

        result = rt.npc.validate_transition("npc_a", from_state, to_state)

        assert result["valid"] is True
        assert result.get("risky") is True

    def test_record_and_retrieve(self):
        rt = RelationshipTracker()
        from_state, to_state = _first_valid_transition(rt.npc.STATES)

        result = rt.npc.record_transition(
            npc_name="npc_a",
            from_state=from_state,
            to_state=to_state,
            arc=1,
            episode=1,
            trigger="충분히 긴 전환 트리거 설명",
            justification="충분히 긴 전환 정당화 설명입니다.",
        )

        assert result["valid"] is True
        assert rt.npc_states["npc_a"] == to_state
        assert len(rt.transition_history) == 1

    def test_infer_state(self):
        rt = RelationshipTracker()
        target_state = next((state for state, kws in rt.npc.STATE_KEYWORDS.items() if kws), None)
        assert target_state is not None
        keyword = rt.npc.STATE_KEYWORDS[target_state][0]

        state = rt.npc.infer_state_from_manuscript("npc_a", f"npc_a {keyword}")

        assert isinstance(state, str)
        assert len(state) > 0

    def test_get_current_state_default(self):
        rt = RelationshipTracker()
        state = rt.npc.get_npc_current_state("unknown_npc")

        assert isinstance(state, str)
        assert len(state) > 0


class TestFactionSubmodule:
    def test_register_faction(self):
        rt = RelationshipTracker()
        faction = rt.factions_module.register_faction_v59("A", power_level=80)

        assert faction.name == "A"
        assert "A" in rt.factions

    def test_set_faction_relation(self):
        rt = RelationshipTracker()
        rt.register_faction_v59("A", power_level=80)
        rt.register_faction_v59("B", power_level=70)
        state = next(iter(rt.factions_module.FACTION_STATES.keys()))

        ok = rt.factions_module.set_faction_relation_v59("A", "B", state)
        rel = rt.factions_module.get_faction_relation_v59("A", "B")

        assert ok is True
        assert rel == state

    def test_validate_faction_transition(self):
        rt = RelationshipTracker()
        from_state, to_state = _first_valid_transition(rt.factions_module.FACTION_STATES)

        result = rt.factions_module.validate_faction_transition_v59("A", "B", from_state, to_state)

        assert "valid" in result

    def test_power_balance(self):
        rt = RelationshipTracker()
        rt.register_faction_v59("A", power_level=80)
        rt.register_faction_v59("B", power_level=70)

        result = rt.factions_module.get_faction_power_balance_v59()

        assert "balance_type" in result


class TestIntegration:
    def test_delegation_npc(self):
        rt = RelationshipTracker()
        from_state, to_state = _first_valid_transition(rt.npc.STATES)

        result = rt.validate_transition("npc_a", from_state, to_state)

        assert result["valid"] is True

    def test_delegation_faction(self):
        rt = RelationshipTracker()
        rt.register_faction_v59("A", power_level=80)

        assert "A" in rt.factions

    def test_lazy_init(self):
        rt = RelationshipTracker()
        assert rt._npc is None
        assert rt._factions is None

        _ = rt.npc
        _ = rt.factions_module

        assert rt._npc is not None
        assert rt._factions is not None
