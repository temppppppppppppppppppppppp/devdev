"""[LM-I] WorldState known_attrs 동기화 테스트

4개 필드(relation_to_protag, injury, location, permanent_injuries)가
WorldState.update_from_state_changes() 시 known_attrs에 반영되어
NpcDriftAdvisor가 표류를 감지할 수 있는지 검증.
"""

import json
from unittest.mock import MagicMock

import pytest

from modules.core.npc_drift_advisor import NpcDriftAdvisor
from modules.core.world_state import WorldStateManager as WorldState


@pytest.fixture
def ws():
    world = WorldState(db=MagicMock())
    # 기본 NPC 등록
    world._state["alive_npcs"]["노사부"] = {
        "role": "사부",
        "relation": "사제",
        "location": "청풍산장",
        "first_seen_ep": 1,
        "role_at_intro": "무공 사부",
        "known_attrs": {},
    }
    world._state["alive_npcs"]["흑풍"] = {
        "role": "적",
        "relation": "적대",
        "location": "흑풍곡",
        "first_seen_ep": 3,
        "role_at_intro": "도적 두목",
        "known_attrs": {},
    }
    return world


# ══════════════════════════════════════════════════════════════
# 1. relationship_changes → known_attrs["relation_to_protag"]
# ══════════════════════════════════════════════════════════════


class TestRelationToKnownAttrs:
    def test_relation_change_syncs_known_attrs(self, ws):
        ws.update_from_state_changes(
            5,
            {
                "relationship_changes": [{"npc": "노사부", "from": "사제", "to": "동지"}],
            },
        )
        ka = ws._state["alive_npcs"]["노사부"].get("known_attrs", {})
        assert "relation_to_protag" in ka
        assert ka["relation_to_protag"]["value"] == "동지"
        assert ka["relation_to_protag"]["prev"] == "사제"
        assert ka["relation_to_protag"]["changed_ep"] == 5

    def test_relation_appears_in_snapshot(self, ws):
        ws.update_from_state_changes(
            5,
            {
                "relationship_changes": [{"npc": "노사부", "from": "사제", "to": "동지"}],
            },
        )
        snap = ws.get_npc_role_snapshot()
        assert "노사부" in snap
        assert snap["노사부"]["known_attrs"]["relation_to_protag"]["value"] == "동지"


# ══════════════════════════════════════════════════════════════
# 2. npc_injuries → known_attrs["injury"]
# ══════════════════════════════════════════════════════════════


class TestInjuryToKnownAttrs:
    def test_injury_syncs_known_attrs(self, ws):
        ws.update_from_state_changes(
            8,
            {
                "npc_injuries": [{"name": "흑풍", "state": "중상", "cause": "전투", "episode": 8}],
            },
        )
        ka = ws._state["alive_npcs"]["흑풍"].get("known_attrs", {})
        assert "injury" in ka
        assert ka["injury"]["value"] == "중상"
        assert ka["injury"]["changed_ep"] == 8

    def test_injury_sequential_updates(self, ws):
        ws.update_from_state_changes(
            8,
            {
                "npc_injuries": [{"name": "흑풍", "state": "중상"}],
            },
        )
        ws.update_from_state_changes(
            10,
            {
                "npc_injuries": [{"name": "흑풍", "state": "회복"}],
            },
        )
        ka = ws._state["alive_npcs"]["흑풍"]["known_attrs"]
        assert ka["injury"]["value"] == "회복"
        assert ka["injury"]["prev"] == "중상"

    def test_injury_appears_in_snapshot(self, ws):
        ws.update_from_state_changes(
            8,
            {
                "npc_injuries": [{"name": "흑풍", "state": "중상"}],
            },
        )
        snap = ws.get_npc_role_snapshot()
        assert snap["흑풍"]["known_attrs"]["injury"]["value"] == "중상"


# ══════════════════════════════════════════════════════════════
# 3. npc_movements → known_attrs["location"]
# ══════════════════════════════════════════════════════════════


class TestLocationToKnownAttrs:
    def test_movement_syncs_known_attrs(self, ws):
        ws.update_from_state_changes(
            6,
            {
                "npc_movements": [{"name": "노사부", "from": "청풍산장", "to": "중원"}],
            },
        )
        ka = ws._state["alive_npcs"]["노사부"].get("known_attrs", {})
        assert "location" in ka
        assert ka["location"]["value"] == "중원"
        assert ka["location"]["prev"] == "청풍산장"
        assert ka["location"]["changed_ep"] == 6

    def test_movement_without_from_uses_existing(self, ws):
        """from이 없을 때 기존 known_attrs에서 이전 위치 추출"""
        ws.update_from_state_changes(
            5,
            {
                "npc_movements": [{"name": "노사부", "from": "청풍산장", "to": "개봉"}],
            },
        )
        ws.update_from_state_changes(
            7,
            {
                "npc_movements": [{"name": "노사부", "to": "소림사"}],
            },
        )
        ka = ws._state["alive_npcs"]["노사부"]["known_attrs"]
        assert ka["location"]["value"] == "소림사"
        assert ka["location"]["prev"] == "개봉"

    def test_movement_appears_in_snapshot(self, ws):
        ws.update_from_state_changes(
            6,
            {
                "npc_movements": [{"name": "노사부", "from": "청풍산장", "to": "중원"}],
            },
        )
        snap = ws.get_npc_role_snapshot()
        assert snap["노사부"]["known_attrs"]["location"]["value"] == "중원"


# ══════════════════════════════════════════════════════════════
# 4. permanent_injuries → known_attrs["permanent_injuries"]
# ══════════════════════════════════════════════════════════════


class TestPermanentInjuryToKnownAttrs:
    def test_permanent_injury_syncs_known_attrs(self, ws):
        ws.update_from_state_changes(
            10,
            {
                "permanent_injuries": [{"name": "흑풍", "type": "amputation", "description": "왼팔 절단"}],
            },
        )
        ka = ws._state["alive_npcs"]["흑풍"].get("known_attrs", {})
        assert "permanent_injuries" in ka
        assert "왼팔 절단" in ka["permanent_injuries"]["value"]

    def test_permanent_injury_accumulates(self, ws):
        ws.update_from_state_changes(
            10,
            {
                "permanent_injuries": [{"name": "흑풍", "type": "amputation", "description": "왼팔 절단"}],
            },
        )
        ws.update_from_state_changes(
            15,
            {
                "permanent_injuries": [{"name": "흑풍", "type": "blindness", "description": "왼쪽 눈 실명"}],
            },
        )
        ka = ws._state["alive_npcs"]["흑풍"]["known_attrs"]
        val = ka["permanent_injuries"]["value"]
        assert "왼팔 절단" in val
        assert "왼쪽 눈 실명" in val

    def test_permanent_injury_appears_in_snapshot(self, ws):
        ws.update_from_state_changes(
            10,
            {
                "permanent_injuries": [{"name": "흑풍", "type": "scar", "description": "얼굴 흉터"}],
            },
        )
        snap = ws.get_npc_role_snapshot()
        assert "permanent_injuries" in snap["흑풍"]["known_attrs"]


# ══════════════════════════════════════════════════════════════
# 5. 사망 NPC는 known_attrs 업데이트 제외
# ══════════════════════════════════════════════════════════════


class TestDeadNpcExcluded:
    def test_dead_npc_injury_ignored(self, ws):
        ws._state["dead_npcs"]["흑풍"] = {"ep": 9, "cause": "전투 사망"}
        ws.update_from_state_changes(
            10,
            {
                "npc_injuries": [{"name": "흑풍", "state": "중상"}],
            },
        )
        # 사망 NPC의 alive_npcs 엔트리는 known_attrs가 비어야 함
        ka = ws._state["alive_npcs"]["흑풍"].get("known_attrs", {})
        assert "injury" not in ka

    def test_dead_npc_movement_ignored(self, ws):
        ws._state["dead_npcs"]["흑풍"] = {"ep": 9, "cause": "전투 사망"}
        ws.update_from_state_changes(
            10,
            {
                "npc_movements": [{"name": "흑풍", "from": "흑풍곡", "to": "소림사"}],
            },
        )
        ka = ws._state["alive_npcs"]["흑풍"].get("known_attrs", {})
        assert "location" not in ka


# ══════════════════════════════════════════════════════════════
# 6. NpcDriftAdvisor가 신규 필드를 프롬프트에 포함
# ══════════════════════════════════════════════════════════════


class TestDriftAdvisorNewFields:
    def test_format_includes_relation(self):
        advisor = NpcDriftAdvisor()
        snaps = {
            "노사부": {
                "role_at_intro": "사부",
                "first_seen_ep": 1,
                "known_attrs": {
                    "relation_to_protag": {"value": "동지", "changed_ep": 5},
                },
            }
        }
        text = advisor._format_snapshot_for_prompt(snaps, ["노사부"])
        assert "relation_to_protag=동지" in text

    def test_format_includes_injury(self):
        advisor = NpcDriftAdvisor()
        snaps = {
            "흑풍": {
                "role_at_intro": "도적",
                "first_seen_ep": 3,
                "known_attrs": {
                    "injury": {"value": "중상", "changed_ep": 8},
                },
            }
        }
        text = advisor._format_snapshot_for_prompt(snaps, ["흑풍"])
        assert "injury=중상" in text

    def test_format_includes_location(self):
        advisor = NpcDriftAdvisor()
        snaps = {
            "노사부": {
                "role_at_intro": "사부",
                "first_seen_ep": 1,
                "known_attrs": {
                    "location": {"value": "중원", "changed_ep": 6},
                },
            }
        }
        text = advisor._format_snapshot_for_prompt(snaps, ["노사부"])
        assert "location=중원" in text

    def test_format_includes_permanent_injuries(self):
        advisor = NpcDriftAdvisor()
        snaps = {
            "흑풍": {
                "role_at_intro": "도적",
                "first_seen_ep": 3,
                "known_attrs": {
                    "permanent_injuries": {"value": "amputation: 왼팔 절단", "changed_ep": 10},
                },
            }
        }
        text = advisor._format_snapshot_for_prompt(snaps, ["흑풍"])
        assert "permanent_injuries=" in text
        assert "왼팔 절단" in text

    def test_drift_detected_for_injury_field(self):
        """NpcDriftAdvisor가 injury 필드 표류를 감지"""
        drift_response = json.dumps(
            [{"npc": "흑풍", "field": "injury", "expected": "중상", "found_in_ms": "멀쩡한 모습"}],
            ensure_ascii=False,
        )
        advisor = NpcDriftAdvisor(llm_ask=lambda _: drift_response)
        snaps = {
            "흑풍": {
                "role_at_intro": "도적",
                "first_seen_ep": 3,
                "known_attrs": {"injury": {"value": "중상", "changed_ep": 8}},
            }
        }
        result = advisor.check("흑풍은 멀쩡한 모습으로 걸어왔다.", snaps, ep_num=10)
        assert len(result) == 1
        assert result[0]["field"] == "injury"
        assert result[0]["check"] == "npc_drift"

    def test_prompt_mentions_new_field_categories(self):
        """프롬프트에 검사 대상 필드 목록이 포함"""
        captured_prompt = []

        def _capture(prompt):
            captured_prompt.append(prompt)
            return "[]"

        advisor = NpcDriftAdvisor(llm_ask=_capture)
        snaps = {
            "노사부": {
                "role_at_intro": "사부",
                "first_seen_ep": 1,
                "known_attrs": {"location": {"value": "중원", "changed_ep": 6}},
            }
        }
        advisor.check("노사부가 걸어갔다.", snaps, ep_num=10)
        assert captured_prompt
        p = captured_prompt[0]
        assert "relation_to_protag" in p
        assert "injury" in p
        assert "location" in p
        assert "permanent_injuries" in p


# ══════════════════════════════════════════════════════════════
# 7. 미등록 NPC → 자동 등록 후 known_attrs 반영
# ══════════════════════════════════════════════════════════════


class TestAutoRegisterNpc:
    def test_unregistered_npc_injury_creates_entry(self):
        w = WorldState(db=MagicMock())
        w.update_from_state_changes(
            5,
            {
                "npc_injuries": [{"name": "신규NPC", "state": "경상"}],
            },
        )
        assert "신규NPC" in w._state["alive_npcs"]
        ka = w._state["alive_npcs"]["신규NPC"].get("known_attrs", {})
        assert ka["injury"]["value"] == "경상"

    def test_unregistered_npc_movement_creates_entry(self):
        w = WorldState(db=MagicMock())
        w.update_from_state_changes(
            5,
            {
                "npc_movements": [{"name": "신규NPC", "from": "", "to": "개봉"}],
            },
        )
        assert "신규NPC" in w._state["alive_npcs"]
        ka = w._state["alive_npcs"]["신규NPC"].get("known_attrs", {})
        assert ka["location"]["value"] == "개봉"
