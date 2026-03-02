"""WorldState 캡 확장 테스트 — destroyed 100, world_laws 50."""

import pytest

from modules.core.db_manager import DBManager
from modules.core.world_state import WorldStateManager


@pytest.fixture
def ws(tmp_path):
    db = DBManager(tmp_path / "test.db")
    mgr = WorldStateManager(db)
    try:
        yield mgr
    finally:
        db.close()


class TestDestroyedCap:
    def test_destroyed_cap_100(self, ws):
        """101개 destroyed → 최근 100개만 유지."""
        ws._state["destroyed"] = [{"name": f"item_{i}", "type": "item", "ep": i, "cause": "파괴"} for i in range(101)]
        # update_from_state_changes 내부의 크기 제한 트리거 (비어있지 않은 dict 필요)
        ws.update_from_state_changes(ep_num=999, state_changes={"_dummy": True})
        assert len(ws._state["destroyed"]) == 100
        # 가장 오래된(item_0)은 탈락, 가장 최근(item_100)은 유지
        names = [d["name"] for d in ws._state["destroyed"]]
        assert "item_0" not in names
        assert "item_100" in names


class TestWorldLawsCap:
    def test_world_laws_cap_50(self, ws):
        """51개 world_laws → 최근 50개만 유지."""
        for i in range(51):
            ws.add_world_law(f"법칙_{i}", ep=i)
        assert len(ws._state["world_laws"]) == 50

    def test_world_laws_critical_pin_preserved(self, ws):
        """CRITICAL 핀 보호 — CRITICAL 법칙은 FIFO 탈락 대상 제외."""
        # CRITICAL 5개 등록
        for i in range(5):
            ws.add_world_law(f"절대법칙_{i}", ep=i, priority="CRITICAL")
        # NORMAL 50개 등록 → 총 55개 → 캡 초과
        for i in range(50):
            ws.add_world_law(f"일반법칙_{i}", ep=100 + i)

        laws = ws._state["world_laws"]
        assert len(laws) == 50
        # CRITICAL 전량 보존
        critical = [e for e in laws if e.get("priority") == "CRITICAL"]
        assert len(critical) == 5
        # NORMAL은 50 - 5 = 45개
        normal = [e for e in laws if e.get("priority") != "CRITICAL"]
        assert len(normal) == 45
