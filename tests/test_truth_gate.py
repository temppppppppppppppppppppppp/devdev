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
        npc_reg = {"독고염": {"status": "dead"}}
        ms = "독고염이 검을 들어올렸다."
        result = gate.validate(ms, {}, npc_registry=npc_reg)
        assert not result["passed"]
        assert any("독고염" in w for w in result["warnings"])
        assert result["blocking"] is False

    def test_deceased_npc_recall_allowed(self):
        """회상 문맥에서는 허용."""
        gate = TruthGate()
        npc_reg = {"독고염": {"status": "dead"}}
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

    def test_deceased_npc_status_dead_detected(self):
        """StateTracker 실제 구조 {"status": "dead"}로 사망 NPC 감지."""
        gate = TruthGate()
        npc_reg = {"독고염": {"status": "dead", "death_arc": 3}}
        ms = "독고염이 검을 들어올렸다."
        result = gate.validate(ms, {}, npc_registry=npc_reg)
        assert not result["passed"]
        assert any("독고염" in w for w in result["warnings"])

    def test_deceased_npc_status_dead_recall_allowed(self):
        """status: dead NPC도 회상 문맥에서는 허용."""
        gate = TruthGate()
        npc_reg = {"독고염": {"status": "dead", "death_arc": 3}}
        ms = "진영호는 독고염의 생전 모습을 떠올렸다."
        result = gate.validate(ms, {}, npc_registry=npc_reg)
        assert result["passed"]

    def test_no_deceased_pass(self):
        """사망 NPC 없으면 통과."""
        gate = TruthGate()
        ms = "진영호가 수련을 시작했다."
        result = gate.validate(ms, {}, npc_registry={"진영호": {"status": "alive"}})
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


# ── [Phase4] structured_warnings 테스트 ─────────────────────────────


class TestStructuredWarnings:
    """[Phase4] validate() 반환값의 structured_warnings 구조 검사."""

    def test_structured_warnings_present_in_result(self):
        """반환값에 structured_warnings 키가 항상 존재해야 함."""
        gate = TruthGate()
        result = gate.validate("원고 내용", {})
        assert "structured_warnings" in result
        assert isinstance(result["structured_warnings"], list)

    def test_structured_warnings_empty_on_pass(self):
        """경고 없을 때 structured_warnings는 빈 리스트."""
        gate = TruthGate()
        result = gate.validate("", {})
        assert result["structured_warnings"] == []

    def test_deceased_warning_is_critical(self):
        """사망 NPC 행동 경고 → severity=CRITICAL."""
        ws = FakeWorldState(deceased_npcs=["비검마"])
        gate = TruthGate(world_state=ws)
        ms = "비검마가 달려 나왔다."
        result = gate.validate(ms, {})
        sw = result["structured_warnings"]
        assert len(sw) > 0
        assert any(w["severity"] == "CRITICAL" for w in sw)
        assert any(w["check"] == "deceased_resurrection" for w in sw)

    def test_skill_dup_warning_is_minor(self):
        """스킬 중복 습득 경고 → severity=MINOR."""
        ws = FakeWorldState(known_skills=["파천검법"])
        gate = TruthGate(world_state=ws)
        su = {"skill_updates": [{"name": "파천검법", "action": "learn"}]}
        result = gate.validate("", su)
        sw = result["structured_warnings"]
        assert any(w["severity"] == "MINOR" for w in sw)
        assert any(w["check"] == "skill_duplication" for w in sw)

    def test_blocking_always_false(self):
        """하위 호환: structured_warnings 추가 후에도 blocking=False 유지."""
        ws = FakeWorldState(deceased_npcs=["영웅"])
        gate = TruthGate(world_state=ws)
        ms = "영웅이 공격했다."
        result = gate.validate(ms, {})
        assert result["blocking"] is False

    def test_warnings_and_structured_warnings_consistent(self):
        """warnings(list[str])와 structured_warnings(list[dict])의 건수가 동일해야 함."""
        gate = TruthGate()
        su = {"karma": 150}
        result = gate.validate("", su)
        assert len(result["warnings"]) == len(result["structured_warnings"])

    def test_structured_warning_has_required_fields(self):
        """structured_warnings 각 항목에 text, severity, check 키가 있어야 함."""
        gate = TruthGate()
        su = {"karma": -10}
        result = gate.validate("", su)
        for sw in result["structured_warnings"]:
            assert "text" in sw
            assert "severity" in sw
            assert "check" in sw
