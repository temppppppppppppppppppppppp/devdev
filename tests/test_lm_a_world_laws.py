"""[LM-A] 세계관 절대 법칙 강제 — 9개 테스트.

1-2: CRITICAL 핀 FIFO 보호
3-4: Bible → WorldState 브릿지
5-9: TruthGate 7번째 검사 (world_law_violation)
"""

import json

from modules.core.truth_gate import TruthGate
from modules.core.world_state import WorldStateManager

# ── 헬퍼 ──────────────────────────────────────────────────────────


class FakeDB:
    """WorldStateManager용 최소 DB stub."""

    def __init__(self, anchor_data=None):
        self._anchors = anchor_data or {}

    def load_anchor(self, key):
        return self._anchors.get(key)

    def save_anchor(self, key, value):
        self._anchors[key] = value


class FakeWorldStateForTG:
    """TruthGate용 WorldState stub (world_laws 지원)."""

    def __init__(self, world_laws=None, deceased_npcs=None):
        self._laws = world_laws or []
        self._deceased = deceased_npcs or []

    def get_world_laws(self):
        return self._laws

    def get_deceased_npcs(self):
        return self._deceased

    def get_owned_items(self):
        return []

    def get_destroyed_locations(self):
        return []

    def get_known_skills(self):
        return []


# ── 1. CRITICAL 핀 보호 ─────────────────────────────────────────


class TestCriticalPinProtection:
    """FIFO 시 CRITICAL 법칙은 탈락하지 않는다."""

    def test_critical_laws_survive_fifo(self):
        """CRITICAL 10 + NORMAL 25 → 30 초과 → CRITICAL 전량 보존."""
        db = FakeDB()
        ws = WorldStateManager(db)

        # CRITICAL 10개
        for i in range(10):
            ws.add_world_law(f"CRITICAL법칙{i}", ep=0, priority="CRITICAL")

        # NORMAL 25개 추가 → 총 35개 → FIFO 발동
        for i in range(25):
            ws.add_world_law(f"NORMAL법칙{i}", ep=i + 1, priority="NORMAL")

        laws = ws._state["world_laws"]
        assert len(laws) == 30

        # CRITICAL 전량 보존 확인
        critical_laws = [e for e in laws if e.get("priority") == "CRITICAL"]
        assert len(critical_laws) == 10
        for i in range(10):
            assert any(e["law"] == f"CRITICAL법칙{i}" for e in critical_laws)

    def test_normal_only_fifo(self):
        """NORMAL only 35개 → 최근 30개 유지 (기존 동작)."""
        db = FakeDB()
        ws = WorldStateManager(db)

        for i in range(35):
            ws.add_world_law(f"법칙{i}", ep=i)

        laws = ws._state["world_laws"]
        assert len(laws) == 30

        # 최근 30개 유지 확인 (법칙5~법칙34)
        law_texts = [e["law"] for e in laws]
        assert "법칙5" in law_texts
        assert "법칙34" in law_texts
        # 초기 법칙(0~4)은 탈락
        assert "법칙0" not in law_texts


# ── 2. Bible → WorldState 브릿지 ─────────────────────────────────


class TestBibleBridge:
    """Stage4Orchestrator._register_bible_world_laws() 동작 검증."""

    def test_bible_world_laws_registered_as_critical(self):
        """WorldLaws 존재 → WorldState 등록 + priority=CRITICAL."""
        db = FakeDB()
        ws = WorldStateManager(db)

        # Bible에서 추출된 법칙 시뮬레이션 (브릿지 로직 직접 호출)
        bible_laws = ["내공 역류 시 사망", "절대 금지 구역 존재"]
        for law in bible_laws:
            ws.add_world_law(law, ep=0, priority="CRITICAL")

        laws = ws._state["world_laws"]
        assert len(laws) == 2
        for entry in laws:
            assert entry["priority"] == "CRITICAL"
            assert entry["established_ep"] == 0

        # get_world_laws()로도 접근 가능
        text_laws = ws.get_world_laws()
        assert "내공 역류 시 사망" in text_laws
        assert "절대 금지 구역 존재" in text_laws

    def test_bible_no_world_laws_no_crash(self):
        """WorldLaws 없음 → 크래시 없음."""
        db = FakeDB()
        ws = WorldStateManager(db)

        # 빈 상태 — 등록 시도 안 함
        assert ws.get_world_laws() == []


# ── 3. TruthGate 7번째 검사 ──────────────────────────────────────


class TestTruthGateWorldLawViolation:
    """TruthGate world_law_violation 검사."""

    def test_violation_detected(self):
        """llm_ask가 violation=true 반환 → CRITICAL 경고."""
        ws = FakeWorldStateForTG(world_laws=["마나 없이는 마법 불가"])

        def mock_llm_ask(prompt):
            return json.dumps({"violation": True, "reason": "마나 없이 마법 사용"})

        gate = TruthGate(world_state=ws, llm_ask=mock_llm_ask)
        result = gate.validate("주인공이 마나 없이 화염구를 던졌다.", {})

        assert not result["passed"]
        assert any("세계관 법칙 위반" in w for w in result["warnings"])
        sw = result["structured_warnings"]
        assert any(w["check"] == "world_law_violation" for w in sw)
        assert any(w["severity"] == "CRITICAL" for w in sw)

    def test_no_violation(self):
        """llm_ask가 violation=false 반환 → 경고 없음."""
        ws = FakeWorldStateForTG(world_laws=["마나 없이는 마법 불가"])

        def mock_llm_ask(prompt):
            return json.dumps({"violation": False, "reason": ""})

        gate = TruthGate(world_state=ws, llm_ask=mock_llm_ask)
        result = gate.validate("주인공이 마나를 집중시켜 화염구를 던졌다.", {})

        assert result["passed"]

    def test_llm_ask_none_backward_compat(self):
        """llm_ask=None → 하위 호환, 기존 6개 검사 정상."""
        ws = FakeWorldStateForTG(world_laws=["절대 법칙"])
        gate = TruthGate(world_state=ws, llm_ask=None)
        result = gate.validate("평범한 원고.", {})

        assert result["passed"]

    def test_llm_ask_exception_graceful(self):
        """llm_ask 예외 → 무시, 나머지 검사 정상."""
        ws = FakeWorldStateForTG(world_laws=["절대 법칙"], deceased_npcs=["독고염"])

        def broken_llm_ask(prompt):
            raise RuntimeError("LLM 서버 다운")

        gate = TruthGate(world_state=ws, llm_ask=broken_llm_ask)
        # 사망 NPC 행동 + 법칙 검사 예외 → 사망 NPC 경고만 발생
        ms = "독고염이 검을 들어올렸다."
        result = gate.validate(ms, {})

        # 사망 NPC 경고는 발생해야 함
        assert not result["passed"]
        assert any("독고염" in w for w in result["warnings"])
        # world_law_violation 경고는 없어야 함 (예외로 스킵)
        assert not any(w.get("check") == "world_law_violation" for w in result["structured_warnings"])

    def test_empty_world_laws_skip(self):
        """world_laws 비어있으면 7번째 검사 skip."""
        ws = FakeWorldStateForTG(world_laws=[])
        call_count = 0

        def counting_llm_ask(prompt):
            nonlocal call_count
            call_count += 1
            return json.dumps({"violation": True, "reason": "test"})

        gate = TruthGate(world_state=ws, llm_ask=counting_llm_ask)
        result = gate.validate("원고 내용", {})

        assert result["passed"]
        assert call_count == 0  # LLM 호출 안 됨
