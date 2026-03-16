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


class TestActivePlotsCap:
    def test_active_plots_cap_100(self, ws):
        """101개 active_plots → 최근 100개만 유지."""
        for i in range(101):
            ws.add_active_plot(f"플롯{i}", since_ep=i)
        assert len(ws._state["active_plots"]) == 100
        names = [p["plot"] for p in ws._state["active_plots"]]
        assert "플롯0" not in names
        assert "플롯100" in names


class TestSummaryVisibility:
    def test_summary_includes_new_sections_and_truncation_counters(self, ws):
        ws._state.update(
            {
                "last_updated_ep": 12,
                "protagonist": {"name": "장천", "location": "서울", "assets": "10억", "injuries": "정상", "skills": []},
                "motivations": [
                    {"text": "복수", "status": "active", "since_ep": 3},
                    {"text": "은퇴", "status": "resolved", "since_ep": 1},
                ],
                "promises": [
                    {"text": "사부를 지킨다", "status": "pending", "promiser": "장천", "promisee": "노사부", "since_ep": 4},
                    {"text": "완료 약속", "status": "fulfilled", "since_ep": 2},
                ],
                "cumulative_elapsed": {"total_days": 42, "history": []},
                "alive_npcs": {
                    "노사부": {
                        "role": "사부",
                        "relation": "동료",
                        "location": "산장",
                        "companion": True,
                        "known_attrs": {
                            "injury": {"value": "안대"},
                            "location": {"value": "서울시청"},
                            "permanent_injuries": {"value": "왼팔 장애"},
                        },
                    },
                    **{f"npc{i}": {"role": "조연"} for i in range(30)},
                },
                "dead_npcs": {f"dead{i}": {"ep": i, "cause": "사망"} for i in range(21)},
                "relationships": {f"rel{i}": f"관계{i}" for i in range(21)},
                "active_items": {f"item{i}": {"status": "보유"} for i in range(21)},
                "destroyed": [{"name": f"장소{i}", "type": "장소", "ep": i} for i in range(11)],
                "active_plots": [{"plot": f"플롯{i}", "since_ep": i} for i in range(11)],
                "active_pressure_vectors": [
                    {"text": "해독제를 찾지 못하면 독이 퍼진다.", "since_ep": 12},
                    {"text": "흑풍회의 추격대가 문 앞까지 다가왔다.", "since_ep": 12},
                ],
                "timeline": [{"ep": i, "description": f"{i}일 경과"} for i in range(6)],
            }
        )

        summary = ws.get_summary()

        assert "[주인공 핵심 동기]" in summary
        assert "복수" in summary
        assert "[서약/약속]" in summary
        assert "사부를 지킨다" in summary
        assert "[누적 경과] 총 42일" in summary
        assert "부상=안대" in summary
        assert "위치기록=서울시청" in summary
        assert "영구부상=왼팔 장애" in summary
        assert "(총 31명 중 30명 표시)" in summary
        assert "(총 21명 중 20명 표시)" in summary
        assert "(총 21개 중 20개 표시)" in summary
        assert "(총 11개 중 10개 표시)" in summary
        assert "(총 6개 중 5개 표시)" in summary
        assert "[지속 압박/위협]" in summary
        assert "해독제를 찾지 못하면 독이 퍼진다." in summary


class TestInventoryCounts:
    def test_inventory_counts_update_active_items_and_summary(self, ws):
        ws.update_from_state_changes(
            ep_num=7,
            state_changes={
                "inventory_counts": {"트레이딩용 컴퓨터": 3, "모니터": 2},
                "inventory_count_deltas": [{"name": "트레이딩용 컴퓨터", "from": 2, "to": 3, "delta": 1}],
            },
        )

        assert ws._state["active_items"]["트레이딩용 컴퓨터"]["quantity"] == 3
        assert ws._state["active_items"]["트레이딩용 컴퓨터"]["status"] == "보유"
        summary = ws.get_summary()
        assert "트레이딩용 컴퓨터 x3" in summary


class TestActivePressureVectors:
    def test_active_pressure_vectors_replace_and_clear(self, ws):
        ws.update_from_state_changes(
            ep_num=8,
            state_changes={
                "active_pressure_vectors": [
                    {"text": "독이 전신으로 퍼지고 있다.", "source": "ending_hook", "cue_terms": ["독"]},
                    {"text": "추격대가 계단을 오르고 있다.", "source": "cliffhanger", "cue_terms": ["추격대"]},
                ]
            },
        )

        assert len(ws._state["active_pressure_vectors"]) == 2
        assert ws._state["active_pressure_vectors"][0]["text"] == "독이 전신으로 퍼지고 있다."

        ws.update_from_state_changes(ep_num=9, state_changes={"active_pressure_vectors": []})

        assert ws._state["active_pressure_vectors"] == []
