"""Focused persistence contract tests for WorldStateManager."""

import json
from unittest.mock import MagicMock

from modules.core.world_state import WorldStateManager


class _WorldStateDB:
    def load_anchor(self, _name):
        return None

    def save_anchor(self, _name, _payload):
        return True


class _SavingWorldStateDB(_WorldStateDB):
    def __init__(self):
        self.anchor = None

    def load_anchor(self, _name):
        if self.anchor is None:
            return None
        return json.loads(json.dumps(self.anchor, ensure_ascii=False))

    def save_anchor(self, _name, _payload):
        self.anchor = json.loads(json.dumps(_payload, ensure_ascii=False))
        return True


class _BrokenWorldStateDB(_WorldStateDB):
    def save_anchor(self, _name, _payload):
        raise RuntimeError("world write fail")


class _FalseSaveWorldStateDB(_WorldStateDB):
    def save_anchor(self, _name, _payload):
        return False


class _CorruptWorldStateStatusDB(_WorldStateDB):
    def load_anchor_with_status(self, _name, default=None):
        return {"found": True, "data": default if default is not None else {}, "error": "bad json"}


def test_save_sets_degraded_contract_on_failure():
    manager = WorldStateManager(_BrokenWorldStateDB())

    result = manager.save()

    assert result is False
    assert manager.last_save_ok is False
    assert manager.last_save_error == "world write fail"


def test_save_sets_degraded_contract_on_false_return():
    manager = WorldStateManager(_FalseSaveWorldStateDB())

    result = manager.save()

    assert result is False
    assert manager.last_save_ok is False
    assert manager.last_save_error == "save_anchor returned False"


def test_save_clears_degraded_contract_on_success():
    manager = WorldStateManager(_WorldStateDB())
    manager.last_save_ok = False
    manager.last_save_error = "stale"

    result = manager.save()

    assert result is True
    assert manager.last_save_ok is True
    assert manager.last_save_error is None


def test_corrupt_anchor_status_refuses_empty_overwrite():
    manager = WorldStateManager(_CorruptWorldStateStatusDB())

    assert manager.degraded is True
    assert manager.degraded_reason == "world_state anchor load failed: bad json"
    assert manager.save() is False
    assert (
        manager.last_save_error == "refusing to overwrite after degraded load: world_state anchor load failed: bad json"
    )


def test_apply_actor_and_inventory_state_changes_updates_front_family_contract():
    manager = WorldStateManager(_WorldStateDB())
    manager._state["alive_npcs"]["노사부"] = {"first_seen_ep": 1, "role_at_intro": "", "known_attrs": {}}

    manager._apply_actor_and_inventory_state_changes(
        7,
        {
            "npc_deaths": [{"name": "흑풍", "cause": "전투 패배"}],
            "skill_acquisitions": ["천뢰검식"],
            "relationship_changes": [{"npc": "노사부", "from": "사제", "to": "동지"}],
            "major_items": [{"name": "청풍검", "action": "획득"}],
            "inventory_counts": {"청풍검": 2},
            "inventory_count_deltas": [{"name": "청풍검", "from": 1, "to": 2, "delta": 1}],
        },
    )

    assert manager._state["dead_npcs"]["흑풍"]["cause"] == "전투 패배"
    assert "천뢰검식" in manager._state["protagonist"]["skills"]
    relation = manager._state["alive_npcs"]["노사부"]["known_attrs"]["relation_to_protag"]
    assert relation["value"] == "동지"
    assert relation["prev"] == "사제"
    assert manager._state["active_items"]["청풍검"]["quantity"] == 2
    assert manager._state["active_items"]["청풍검"]["status"] == "보유"


def test_apply_entity_and_companion_state_changes_updates_mid_family_contract():
    manager = WorldStateManager(_WorldStateDB())
    manager._state["active_plots"] = [{"plot": "천마 부활", "since_ep": 3}]
    manager._state["alive_npcs"]["노사부"] = {"first_seen_ep": 1, "role_at_intro": "", "known_attrs": {}}

    manager._apply_entity_and_companion_state_changes(
        9,
        {
            "entity_destructions": [{"name": "흑풍채", "type": "조직", "cause": "소탕"}],
            "npc_personality_changes": [{"name": "노사부", "from": "엄격함", "to": "유연함"}],
            "resolved_plots": [{"plot": "천마 부활"}],
            "active_pressure_vectors": [{"text": "추격대가 북문을 포위했다.", "source": "ending_hook"}],
            "companion_changes": [{"name": "연홍", "action": "joined"}],
        },
    )

    assert manager._state["destroyed"][0]["name"] == "흑풍채"
    assert manager._state["alive_npcs"]["노사부"]["personality"] == "유연함"
    assert manager._state["alive_npcs"]["노사부"]["known_attrs"]["personality"]["prev"] == "엄격함"
    assert manager._state["active_plots"] == []
    assert manager._state["active_pressure_vectors"][0]["text"] == "추격대가 북문을 포위했다."
    assert manager._state["alive_npcs"]["연홍"]["companion"] is True


def test_apply_timeline_and_goal_state_changes_updates_timeline_motivation_and_promises():
    manager = WorldStateManager(_WorldStateDB())
    manager.db = MagicMock()

    manager._apply_timeline_and_goal_state_changes(
        11,
        {
            "time_markers": [{"episode": 11, "type": "elapsed", "description": "3일 후"}],
            "protagonist_motivations": [{"text": "천마를 막는다", "status": "active"}],
            "promises": [{"text": "사부를 지킨다", "promiser": "이청풍", "promisee": "노사부"}],
        },
    )

    assert manager._state["timeline"][0]["description"] == "3일 후"
    assert manager._state["cumulative_elapsed"]["total_days"] == 3
    assert manager._state["motivations"][0]["text"] == "천마를 막는다"
    assert manager._state["promises"][0]["promiser"] == "이청풍"
    manager.db.upsert_timeline_entry.assert_called_once()


def test_apply_physical_known_attr_state_changes_updates_lmi_contracts():
    manager = WorldStateManager(_WorldStateDB())
    manager._state["alive_npcs"]["흑풍"] = {
        "first_seen_ep": 1,
        "role_at_intro": "",
        "known_attrs": {"location": {"value": "흑풍곡"}},
    }

    manager._apply_physical_known_attr_state_changes(
        12,
        {
            "npc_injuries": [{"name": "흑풍", "state": "중상"}],
            "npc_movements": [{"name": "흑풍", "to": "소림사"}],
            "permanent_injuries": [{"name": "흑풍", "type": "scar", "description": "얼굴 흉터"}],
        },
    )

    known_attrs = manager._state["alive_npcs"]["흑풍"]["known_attrs"]
    assert known_attrs["injury"]["value"] == "중상"
    assert known_attrs["location"]["value"] == "소림사"
    assert known_attrs["location"]["prev"] == "흑풍곡"
    assert "scar: 얼굴 흉터" in known_attrs["permanent_injuries"]["value"]


def test_update_from_state_changes_replays_npc_martial_state_owner_contract():
    manager = WorldStateManager(_WorldStateDB())

    manager.update_from_state_changes(
        5,
        {
            "npc_martial_state_changes": [
                {
                    "name": "Chief Han",
                    "episode": 5,
                    "realm": "Peak",
                    "techniques_learned": ["Storm Palm"],
                }
            ]
        },
    )
    manager.update_from_state_changes(
        6,
        {
            "npc_martial_state_changes": [
                {
                    "name": "Chief Han",
                    "episode": 6,
                    "realm": "Master",
                    "techniques_learned": ["Storm Palm", "Cloud Step"],
                }
            ]
        },
    )

    martial_state = manager._state["alive_npcs"]["Chief Han"]["martial_state"]

    assert martial_state["realm"] == "Master"
    assert martial_state["realm_changed_ep"] == 6
    assert martial_state["techniques"] == ["Storm Palm", "Cloud Step"]
    assert martial_state["last_martial_ep"] == 6


def test_save_and_reload_preserves_npc_martial_state_owner_contract():
    db = _SavingWorldStateDB()
    manager = WorldStateManager(db)

    manager.update_from_state_changes(
        6,
        {
            "npc_martial_state_changes": [
                {
                    "name": "Chief Han",
                    "episode": 6,
                    "realm": "Master",
                    "techniques_learned": ["Storm Palm", "Cloud Step"],
                }
            ]
        },
    )

    assert manager.save() is True

    reloaded = WorldStateManager(db)
    martial_state = reloaded._state["alive_npcs"]["Chief Han"]["martial_state"]

    assert martial_state["realm"] == "Master"
    assert martial_state["realm_changed_ep"] == 6
    assert martial_state["techniques"] == ["Storm Palm", "Cloud Step"]
    assert martial_state["last_martial_ep"] == 6


def test_update_from_state_changes_skips_martial_write_for_same_payload_dead_npc():
    manager = WorldStateManager(_WorldStateDB())

    manager.update_from_state_changes(
        8,
        {
            "npc_deaths": [{"name": "Chief Han", "cause": "final duel"}],
            "npc_martial_state_changes": [
                {
                    "name": "Chief Han",
                    "episode": 8,
                    "realm": "Master",
                    "techniques_learned": ["Storm Palm"],
                }
            ],
        },
    )

    assert "Chief Han" in manager._state["dead_npcs"]
    assert "Chief Han" not in manager._state["alive_npcs"]


def test_apply_npc_registry_and_law_state_changes_updates_registry_contracts():
    manager = WorldStateManager(_WorldStateDB())

    manager._apply_npc_registry_and_law_state_changes(
        6,
        {
            "npc_introductions": [
                {
                    "name": "박성호",
                    "job": "차장",
                    "personality": "냉정함",
                    "knowledge_era": "현대",
                    "secret_role": "감사실 내통자",
                }
            ],
            "world_law_additions": ["사망자는 회상/언급만 허용"],
        },
    )
    manager._apply_npc_registry_and_law_state_changes(
        13,
        {
            "npc_attribute_changes": [{"name": "박성호", "field": "position", "old": "차장", "new": "팀장"}],
        },
    )

    npc_entry = manager._state["alive_npcs"]["박성호"]
    assert npc_entry["known_attrs"]["position"]["value"] == "팀장"
    assert npc_entry["known_attrs"]["position"]["prev"] == "차장"
    assert npc_entry["known_attrs"]["personality"]["value"] == "냉정함"
    assert npc_entry["known_attrs"]["dual_identity"]["value"]["secret_role"] == "감사실 내통자"
    assert manager._state["world_laws"][0]["law"] == "사망자는 회상/언급만 허용"
