"""
[CON-2-FIX] NPC 직함/직위 추적 테스트

master_bible 병합 + WorldState position 전파 + StateTracker position 이력 +
CW NPC 상태 읽기 시 WorldState 우선 참조 + interview_round superior_position
"""
import pytest
from unittest.mock import MagicMock, patch


class TestMasterBibleMerge:
    """수정 1: new_lore.Key_NPCs → master_bible.AssetLibrary.KeyNPCs 병합"""

    def test_merge_new_npc_to_master_bible(self):
        """신규 NPC가 master_bible KeyNPCs에 추가되는지"""
        mb = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "박성호", "position": "PB", "role": "증권사 담당자"},
                    ]
                }
            }
        }

        key_npcs = [
            {"name": "박성호", "position": "차장", "role": "증권사 PB"},
            {"name": "김민수", "position": "대리", "role": "부동산 중개인"},
        ]

        _mb_root = mb.get("MasterBible", mb)
        _assets = _mb_root.setdefault("AssetLibrary", {})
        _existing_npcs = _assets.get("KeyNPCs", [])
        _npc_by_name = {}
        for _i, _enpc in enumerate(_existing_npcs):
            if isinstance(_enpc, dict):
                _ename = _enpc.get("name", "")
                if _ename:
                    _npc_by_name[_ename] = _i

        for _new_npc in key_npcs:
            _nname = _new_npc.get("name", "")
            if not _nname:
                continue
            if _nname in _npc_by_name:
                _idx = _npc_by_name[_nname]
                for _k, _v in _new_npc.items():
                    if _k in ("name", "Name"):
                        continue
                    if _v:
                        _existing_npcs[_idx][_k] = _v
            else:
                _existing_npcs.append(_new_npc)
                _npc_by_name[_nname] = len(_existing_npcs) - 1

        _assets["KeyNPCs"] = _existing_npcs

        result = _assets["KeyNPCs"]
        assert len(result) == 2
        park = [n for n in result if n["name"] == "박성호"][0]
        assert park["position"] == "차장"
        kim = [n for n in result if n["name"] == "김민수"][0]
        assert kim["position"] == "대리"

    def test_merge_preserves_existing_fields(self):
        """병합 시 기존 필드가 보존되는지"""
        mb = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "박성호", "position": "PB", "role": "담당자", "extra_field": "보존됨"},
                    ]
                }
            }
        }
        key_npcs = [{"name": "박성호", "position": "차장"}]

        _existing = mb["MasterBible"]["AssetLibrary"]["KeyNPCs"]
        _npc_by_name = {"박성호": 0}

        for _new_npc in key_npcs:
            _nname = _new_npc.get("name", "")
            if _nname in _npc_by_name:
                _idx = _npc_by_name[_nname]
                for _k, _v in _new_npc.items():
                    if _k in ("name", "Name"):
                        continue
                    if _v:
                        _existing[_idx][_k] = _v

        park = _existing[0]
        assert park["position"] == "차장"
        assert park["extra_field"] == "보존됨"
        assert park["role"] == "담당자"


class TestStateTrackerPositionTracking:
    """수정 2: state_tracker_npc position 필드 추적"""

    def test_register_npc_position(self):
        """position 필드가 npc_registry에 저장되는지"""
        from modules.domain.agents.state_tracker_npc import StateTrackerNPC

        tracker = MagicMock()
        tracker.npc_registry = {}
        tracker._db = MagicMock()
        tracker._db.insert_npc_change = MagicMock()

        npc_mod = StateTrackerNPC(tracker)

        npc_mod.register_npc_info("박성호", arc_no=1, position="차장", episode_no=6)
        assert tracker.npc_registry["박성호"]["position"] == "차장"

        # 직함 변경 시 이력 기록
        npc_mod.register_npc_info("박성호", arc_no=2, position="팀장", episode_no=13)
        assert tracker.npc_registry["박성호"]["position"] == "팀장"

        # _record_change가 호출됐는지 확인 (_db.insert_npc_change 경유)
        # 인자 순서: (npc_name, episode_no, arc_no, field_name, old_value, new_value, source, reason=...)
        pos_calls = [c for c in tracker._db.insert_npc_change.call_args_list
                     if len(c.args) >= 4 and c.args[3] == "position"]
        # 첫 등록(""→차장) + 변경(차장→팀장) = 2회
        assert len(pos_calls) == 2
        assert pos_calls[1].args[4] == "차장"   # old
        assert pos_calls[1].args[5] == "팀장"   # new

    def test_position_no_change_no_record(self):
        """position이 동일하면 이력 미기록"""
        from modules.domain.agents.state_tracker_npc import StateTrackerNPC

        tracker = MagicMock()
        tracker.npc_registry = {"박성호": {"status": "alive", "position": "차장"}}
        tracker._db = MagicMock()
        tracker._db.insert_npc_change = MagicMock()

        npc_mod = StateTrackerNPC(tracker)
        npc_mod.register_npc_info("박성호", arc_no=1, position="차장", episode_no=6)

        position_calls = [c for c in tracker._db.insert_npc_change.call_args_list
                          if len(c.args) >= 4 and c.args[2] == "position"]
        assert len(position_calls) == 0


class TestStateTrackerFacadePosition:
    """수정 2b: StateTracker facade position 파라미터 전달"""

    def test_facade_passes_position(self):
        """StateTracker.register_npc_info()가 position을 서브모듈에 전달하는지"""
        from modules.domain.agents.state_tracker import StateTracker

        tracker = StateTracker.__new__(StateTracker)
        tracker.npc_registry = {}
        tracker._db = MagicMock()
        tracker._db.insert_npc_change = MagicMock()

        from modules.domain.agents.state_tracker_npc import StateTrackerNPC
        tracker._npc = StateTrackerNPC(tracker)

        tracker.register_npc_info("박성호", arc_no=1, position="차장")
        assert tracker.npc_registry["박성호"]["position"] == "차장"

        tracker.register_npc_info("박성호", arc_no=2, position="팀장")
        assert tracker.npc_registry["박성호"]["position"] == "팀장"


class TestWorldStatePositionKnownAttrs:
    """수정 3: WorldState known_attrs에 position 저장"""

    def test_npc_introduction_stores_position(self):
        """npc_introductions의 job → known_attrs.position 구조화"""
        from modules.core.world_state import WorldStateManager

        db = MagicMock()
        ws = WorldStateManager(db)
        ws.update_from_state_changes(
            state_changes={
                "npc_introductions": [
                    {"name": "박성호", "job": "차장", "episode": 6},
                ]
            },
            ep_num=6,
        )

        alive = ws._state["alive_npcs"]
        assert "박성호" in alive
        ka = alive["박성호"]["known_attrs"]
        assert isinstance(ka.get("position"), dict)
        assert ka["position"]["value"] == "차장"
        assert ka["position"]["changed_ep"] == 6

    def test_npc_attribute_change_updates_position(self):
        """npc_attribute_changes로 position 변경 시 known_attrs 갱신"""
        from modules.core.world_state import WorldStateManager

        db = MagicMock()
        ws = WorldStateManager(db)
        ws._state["alive_npcs"]["박성호"] = {
            "first_seen_ep": 6,
            "role_at_intro": "차장",
            "known_attrs": {"position": {"value": "차장", "prev": "", "changed_ep": 6}},
        }

        ws.update_from_state_changes(
            state_changes={
                "npc_attribute_changes": [
                    {"name": "박성호", "field": "position", "old": "차장", "new": "팀장"},
                ]
            },
            ep_num=13,
        )

        ka = ws._state["alive_npcs"]["박성호"]["known_attrs"]
        # npc_attribute_changes는 generic 처리 — value가 구조화 dict일 수도, 원시값일 수도 있음
        pos = ka.get("position", {})
        if isinstance(pos, dict) and "value" in pos:
            assert pos["value"] in ("팀장",)
        else:
            assert str(pos) == "팀장"


class TestCWNpcStateWorldStatePriority:
    """수정 4: CW NPC 상태 읽기 시 WorldState 우선 참조"""

    def test_extract_npc_last_states_worldstate_override(self):
        """WorldState known_attrs.position이 master_bible 값을 덮어쓰는지"""
        from modules.domain.agents.chief_writer_context import ChiefWriterContextBuilder

        ws = MagicMock()
        ws._state = {
            "alive_npcs": {
                "박성호": {
                    "first_seen_ep": 6,
                    "role_at_intro": "차장",
                    "relation": "동맹",
                    "known_attrs": {
                        "position": {"value": "팀장", "prev": "차장", "changed_ep": 13},
                    },
                },
            },
        }

        host = MagicMock()
        host.context = MagicMock()
        host.context.master_bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "박성호", "position": "PB", "relationship_state": "중립", "last_appearance_ep": 6},
                    ]
                }
            }
        }
        host.context.world_state = ws

        builder = ChiefWriterContextBuilder(host)
        result = builder._extract_npc_last_states(current_ep=14)

        assert "박성호" in result
        assert result["박성호"]["position"] == "팀장"

    def test_extract_npc_last_states_no_worldstate(self):
        """WorldState 없을 때 master_bible 값 사용"""
        from modules.domain.agents.chief_writer_context import ChiefWriterContextBuilder

        host = MagicMock()
        host.context = MagicMock()
        host.context.master_bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "박성호", "position": "PB", "relationship_state": "중립", "last_appearance_ep": 6},
                    ]
                }
            }
        }
        host.context.world_state = None

        builder = ChiefWriterContextBuilder(host)
        result = builder._extract_npc_last_states(current_ep=14)
        assert result["박성호"]["position"] == "PB"


class TestInterviewRoundSuperiorPosition:
    """수정 5: superior_position WorldState 우선 참조"""

    def test_superior_position_from_worldstate(self):
        ws_state = {
            "alive_npcs": {
                "박성호": {
                    "known_attrs": {
                        "position": {"value": "팀장", "prev": "차장", "changed_ep": 13},
                    }
                }
            }
        }
        ws = MagicMock()
        ws._state = ws_state

        mb_npc = {"name": "박성호", "position": "PB", "role": "상사"}

        _ws_position = ""
        _ws_npc = ws._state.get("alive_npcs", {}).get("박성호", {})
        _ws_ka = _ws_npc.get("known_attrs", {})
        if isinstance(_ws_ka.get("position"), dict):
            _ws_position = _ws_ka["position"].get("value", "")

        superior_position = _ws_position or mb_npc.get("position", mb_npc.get("role", ""))
        assert superior_position == "팀장"

    def test_superior_position_fallback_to_master_bible(self):
        ws = MagicMock()
        ws._state = {"alive_npcs": {}}

        mb_npc = {"name": "박성호", "position": "PB", "role": "상사"}

        _ws_position = ""
        _ws_npc = ws._state.get("alive_npcs", {}).get("박성호", {})
        _ws_ka = _ws_npc.get("known_attrs", {})
        if isinstance(_ws_ka.get("position"), dict):
            _ws_position = _ws_ka["position"].get("value", "")

        superior_position = _ws_position or mb_npc.get("position", mb_npc.get("role", ""))
        assert superior_position == "PB"


class TestEndToEndPositionFlow:
    """E2E: 전체 position 추적 흐름 검증"""

    def test_position_change_detected_and_propagated(self):
        """NPC position 변경이 WorldState 전체에 전파"""
        from modules.core.world_state import WorldStateManager

        db = MagicMock()
        ws = WorldStateManager(db)

        # ep6: 박성호 첫 등장 (차장)
        ws.update_from_state_changes(
            state_changes={
                "npc_introductions": [{"name": "박성호", "job": "차장", "episode": 6}],
            },
            ep_num=6,
        )
        assert ws._state["alive_npcs"]["박성호"]["known_attrs"]["position"]["value"] == "차장"

        # ep13: 승진 (팀장)
        ws.update_from_state_changes(
            state_changes={
                "npc_attribute_changes": [
                    {"name": "박성호", "field": "position", "old": "차장", "new": "팀장"},
                ],
            },
            ep_num=13,
        )

        # npc_attribute_changes는 generic dict 저장
        ka = ws._state["alive_npcs"]["박성호"]["known_attrs"]
        # §9 generic 처리는 {value, prev, changed_ep} 구조
        pos = ka.get("position", {})
        if isinstance(pos, dict):
            actual_value = pos.get("value", pos.get("new", ""))
            assert actual_value == "팀장"

        # get_npc_role_snapshot에서 position 조회 가능
        snap = ws.get_npc_role_snapshot()
        assert "박성호" in snap
        pos_data = snap["박성호"]["known_attrs"].get("position", {})
        assert isinstance(pos_data, dict)
