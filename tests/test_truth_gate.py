"""[TF-17] Truth Gate — 메모리 오염 방지 advisory 검증기 테스트."""

from modules.core.truth_gate import TruthGate

# ── 헬퍼 ──────────────────────────────────────────────────────────


class FakeWorldState:
    """테스트용 WorldState."""

    def __init__(
        self,
        deceased_npcs=None,
        owned_items=None,
        destroyed_locations=None,
        known_skills=None,
    ):
        self._deceased = deceased_npcs or []
        self._items = owned_items or []
        self._destroyed = destroyed_locations or []
        self._skills = known_skills or []

    def get_deceased_npcs(self):
        return self._deceased

    def get_owned_items(self):
        return self._items

    def get_destroyed_locations(self):
        return self._destroyed

    def get_known_skills(self):
        return self._skills


# ── 사망 NPC 부활 감지 ─────────────────────────────────────────────


class TestDeceasedResurrection:
    """사망 NPC가 행동/대사로 등장하면 경고."""

    def test_deceased_npc_action_detected(self):
        """사망 NPC가 행동 주어로 등장하면 경고."""
        gate = TruthGate()
        npc_reg = {"독고염": {"deceased": True}}
        ms = "독고염이 검을 들어올렸다."
        result = gate.validate(ms, {}, npc_registry=npc_reg)
        assert not result["passed"]
        assert any("독고염" in w for w in result["warnings"])
        assert result["blocking"] is False

    def test_deceased_npc_recall_allowed(self):
        """회상 문맥에서는 허용."""
        gate = TruthGate()
        npc_reg = {"독고염": {"deceased": True}}
        ms = "진영호는 독고염의 생전 모습을 떠올렸다."
        result = gate.validate(ms, {}, npc_registry=npc_reg)
        assert result["passed"]

    def test_deceased_from_world_state(self):
        """world_state에서 사망 NPC 목록을 보충."""
        ws = FakeWorldState(deceased_npcs=["독고염"])
        gate = TruthGate(world_state=ws)
        ms = "독고염이 달려왔다."
        result = gate.validate(ms, {})
        assert not result["passed"]
        assert any("독고염" in w for w in result["warnings"])

    def test_no_deceased_pass(self):
        """사망 NPC 없으면 통과."""
        gate = TruthGate()
        ms = "진영호가 수련을 시작했다."
        result = gate.validate(ms, {}, npc_registry={"진영호": {"deceased": False}})
        assert result["passed"]


# ── 미보유 아이템 감지 ─────────────────────────────────────────────


class TestUnownedItems:
    """미보유 아이템 사용/장착 시 경고."""

    def test_unowned_item_use(self):
        ws = FakeWorldState(owned_items=["철검"])
        gate = TruthGate(world_state=ws)
        su = {"item_updates": {"천마신공비급": {"action": "use"}}}
        result = gate.validate("", su)
        assert not result["passed"]
        assert any("천마신공비급" in w for w in result["warnings"])

    def test_owned_item_ok(self):
        ws = FakeWorldState(owned_items=["철검"])
        gate = TruthGate(world_state=ws)
        su = {"item_updates": {"철검": {"action": "equip"}}}
        result = gate.validate("", su)
        assert result["passed"]

    def test_no_world_state_skip(self):
        """world_state 없으면 검사 스킵."""
        gate = TruthGate()
        su = {"item_updates": {"천마신공비급": {"action": "use"}}}
        result = gate.validate("", su)
        assert result["passed"]


# ── 파괴된 장소 감지 ─────────────────────────────────────────────


class TestDestroyedLocations:
    """파괴된 장소 방문 감지."""

    def test_destroyed_location_visit(self):
        ws = FakeWorldState(destroyed_locations=["흑풍곡"])
        gate = TruthGate(world_state=ws)
        ms = "진영호는 흑풍곡에 도착했다."
        su = {"location_update": "흑풍곡"}
        result = gate.validate(ms, su)
        assert not result["passed"]
        assert any("흑풍곡" in w for w in result["warnings"])

    def test_no_destroyed_pass(self):
        ws = FakeWorldState(destroyed_locations=[])
        gate = TruthGate(world_state=ws)
        ms = "진영호는 화산파에 도착했다."
        result = gate.validate(ms, {})
        assert result["passed"]


# ── 스킬 중복 감지 ─────────────────────────────────────────────


class TestSkillDuplication:
    """동일 스킬 중복 습득 감지."""

    def test_duplicate_skill(self):
        ws = FakeWorldState(known_skills=["태극검법"])
        gate = TruthGate(world_state=ws)
        su = {"skill_updates": [{"name": "태극검법", "action": "learn"}]}
        result = gate.validate("", su)
        assert not result["passed"]
        assert any("태극검법" in w for w in result["warnings"])

    def test_new_skill_ok(self):
        ws = FakeWorldState(known_skills=["태극검법"])
        gate = TruthGate(world_state=ws)
        su = {"skill_updates": [{"name": "천마지체", "action": "learn"}]}
        result = gate.validate("", su)
        assert result["passed"]


# ── 카르마 범위 감지 ─────────────────────────────────────────────


class TestKarmaBounds:
    """카르마 값 범위 (0-100) 초과 감지."""

    def test_karma_over_100(self):
        gate = TruthGate()
        su = {"karma": 150}
        result = gate.validate("", su)
        assert not result["passed"]
        assert any("범위 초과" in w for w in result["warnings"])

    def test_karma_negative(self):
        gate = TruthGate()
        su = {"karma": -10}
        result = gate.validate("", su)
        assert not result["passed"]

    def test_karma_valid(self):
        gate = TruthGate()
        su = {"karma": 50}
        result = gate.validate("", su)
        assert result["passed"]

    def test_karma_in_protagonist_updates(self):
        gate = TruthGate()
        su = {"protagonist_updates": {"karma": 200}}
        result = gate.validate("", su)
        assert not result["passed"]

    def test_karma_non_numeric(self):
        gate = TruthGate()
        su = {"karma": "높음"}
        result = gate.validate("", su)
        assert not result["passed"]
        assert any("숫자가 아닙니다" in w for w in result["warnings"])


# ── 엣지 케이스 ─────────────────────────────────────────────────


class TestEdgeCases:
    """경계 사례 및 graceful skip."""

    def test_empty_inputs(self):
        gate = TruthGate()
        result = gate.validate("", {})
        assert result["passed"]

    def test_none_inputs(self):
        gate = TruthGate()
        result = gate.validate(None, None)
        assert result["passed"]

    def test_world_state_none_graceful(self):
        """world_state=None 시 관련 검사 스킵."""
        gate = TruthGate(world_state=None)
        su = {"item_updates": {"천마신공": {"action": "use"}}}
        result = gate.validate("", su)
        assert result["passed"]  # 검사 스킵 → 통과

    def test_advisory_mode_never_blocking(self):
        """blocking 필드는 항상 False."""
        gate = TruthGate()
        su = {"karma": -999}
        result = gate.validate("", su)
        assert result["blocking"] is False
