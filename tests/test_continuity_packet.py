from unittest.mock import MagicMock, patch

from modules.core.stage4_context_builder import Stage4ContextBuilder


def _make_ctx():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.current_project = MagicMock()
    ctx.current_project.db = MagicMock()
    ctx.current_project.genre = {"name": "무협"}
    ctx.current_project.master_bible = {}
    ctx.current_project.load_v20_anchor = MagicMock(return_value=None)
    ctx.world_state = None
    ctx.fact_ledger = None
    ctx.state_tracker = None
    ctx.memory = None
    ctx.context_advisor = None
    ctx.foreshadow_tracker = None
    ctx.semantic_plot_guard = None
    ctx.load_narrative_summaries = MagicMock(return_value="")
    return ctx


def _make_world_state(state: dict):
    world_state = MagicMock()
    world_state._state = state
    world_state.get_summary.return_value = ""
    world_state.get_timeline_summary.return_value = ""
    world_state.get_canonical_constraints.return_value = ""
    return world_state


def _make_fact_ledger(ledger: dict):
    fact_ledger = MagicMock()
    fact_ledger._ledger = ledger
    fact_ledger.to_summary.return_value = ""
    fact_ledger.get_canonical_summary.return_value = ""
    return fact_ledger


class TestExtractBlueprintEntities:
    def test_extract_blueprint_entities_basic(self):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": {"장천": {}, "소연": {}, "무관": {}},
                "dead_npcs": {},
                "active_items": {"흑검": {"status": "보유"}},
                "active_plots": [{"plot": "혈교 추적"}],
                "protagonist": {"location": "한양"},
            }
        )
        builder = Stage4ContextBuilder(ctx)

        entities = builder._extract_blueprint_entities(
            {
                "integrated_scenario": "장천과 소연이 흑검을 들고 혈교 추적을 이어간다.",
                "scene_breakdown": {"scene_1": {"summary": "무관은 배후를 본다."}},
            }
        )

        assert entities["npcs"] == ["장천", "소연", "무관"]
        assert entities["items"] == ["흑검"]
        assert entities["plots"] == ["혈교 추적"]
        assert entities["locations"] == ["한양"]
        assert isinstance(entities["_full_text"], str)
        assert "장천과 소연이 흑검을 들고 혈교 추적을 이어간다." in entities["_full_text"]

    def test_extract_blueprint_entities_empty(self):
        builder = Stage4ContextBuilder(_make_ctx())

        entities = builder._extract_blueprint_entities(None)

        assert entities == {"npcs": [], "items": [], "plots": [], "locations": [], "_full_text": ""}

    def test_extract_blueprint_entities_dead_npc(self):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": {"장천": {}},
                "dead_npcs": {"진무": {"ep": 12, "cause": "암살"}},
                "active_items": {},
                "active_plots": [],
                "protagonist": {},
            }
        )
        builder = Stage4ContextBuilder(ctx)

        entities = builder._extract_blueprint_entities(
            {"expected_ending": "장천은 진무를 회상하며 복수를 다짐한다."}
        )

        assert "진무" in entities["npcs"]

    def test_extract_blueprint_entities_returns_full_text(self):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": {"장천": {}},
                "dead_npcs": {},
                "active_items": {},
                "active_plots": [],
                "protagonist": {},
            }
        )
        builder = Stage4ContextBuilder(ctx)

        entities = builder._extract_blueprint_entities(
            {"integrated_scenario": "장천이 자본금 10억을 굴린다."}
        )

        assert "_full_text" in entities
        assert isinstance(entities["_full_text"], str)
        assert entities["_full_text"]


class TestBuildContinuityPacket:
    def test_build_continuity_packet_basic(self):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": {
                    "장천": {"role": "검객", "relation": "동료"},
                    "소연": {"role": "정보상", "relation": "협력"},
                },
                "dead_npcs": {},
                "active_items": {"흑검": {"status": "보유"}},
                "active_plots": [{"plot": "혈교 추적"}],
                "protagonist": {"location": "한양"},
            }
        )
        builder = Stage4ContextBuilder(ctx)

        packet = builder.context_packets.build_continuity_packet(
            {
                "npcs": ["장천", "소연"],
                "items": ["흑검"],
                "plots": ["혈교 추적"],
                "locations": ["한양"],
            }
        )

        assert "[Continuity Packet]" in packet
        assert "장천" in packet
        assert "소연" in packet
        assert "혈교 추적" in packet
        assert "흑검" in packet
        assert "한양" in packet

    def test_build_continuity_packet_budget(self):
        ctx = _make_ctx()
        alive_npcs = {
            f"npc{i}": {"role": "검객", "relation": "동료", "personality": "냉철" * 20}
            for i in range(20)
        }
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": alive_npcs,
                "dead_npcs": {},
                "active_items": {},
                "active_plots": [],
                "protagonist": {},
            }
        )
        builder = Stage4ContextBuilder(ctx)

        packet = builder.context_packets.build_continuity_packet(
            {"npcs": list(alive_npcs.keys()), "items": [], "plots": [], "locations": [], "_full_text": ""}
        )

        assert len(packet) <= 7000

    def test_build_continuity_packet_empty_entities(self):
        builder = Stage4ContextBuilder(_make_ctx())

        packet = builder.context_packets.build_continuity_packet({"npcs": [], "items": [], "plots": [], "locations": []})

        assert packet == ""

    def test_build_continuity_packet_with_fact_ledger(self):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": {"장천": {"role": "검객"}},
                "dead_npcs": {},
                "active_items": {},
                "active_plots": [],
                "protagonist": {},
            }
        )
        ctx.fact_ledger = _make_fact_ledger(
            {
                "characters": {
                    "장천": {
                        "history": [
                            "ep1: 입문",
                            "ep2: 수련",
                            "ep3: 부상",
                            "ep4: 회복",
                            "ep5: 각성",
                            "ep6: 추적 시작",
                        ]
                    }
                }
            }
        )
        builder = Stage4ContextBuilder(ctx)

        packet = builder.context_packets.build_continuity_packet(
            {"npcs": ["장천"], "items": [], "plots": [], "locations": [], "_full_text": ""}
        )

        assert "ep2: 수련" in packet
        assert "ep6: 추적 시작" in packet
        assert "ep1: 입문" not in packet

    def test_build_continuity_packet_with_npc_history(self):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": {"장천": {"role": "검객"}},
                "dead_npcs": {},
                "active_items": {},
                "active_plots": [],
                "protagonist": {},
            }
        )
        ctx.current_project.db.get_npc_history.return_value = [
            {"episode_no": 18, "field_name": "location", "old_value": "한양", "new_value": "북해"}
        ]
        builder = Stage4ContextBuilder(ctx)

        packet = builder.context_packets.build_continuity_packet(
            {"npcs": ["장천"], "items": [], "plots": [], "locations": [], "_full_text": ""}
        )

        assert "[변경 18화] location: 한양 → 북해" in packet

    def test_build_continuity_packet_relationship_trajectory(self):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": {"장천": {"role": "검객"}, "소연": {"role": "정보상"}},
                "dead_npcs": {},
                "active_items": {},
                "active_plots": [],
                "protagonist": {},
            }
        )
        ctx.current_project.db.get_npc_relationship_edges.return_value = [
            {"npc1": "장천", "npc2": "소연", "relation": "연인", "since_ep": 42}
        ]
        ctx.current_project.db.get_relationship_history.return_value = [
            {"change_ep": 3, "new_relation": "적"},
            {"change_ep": 15, "new_relation": "동맹"},
            {"change_ep": 42, "new_relation": "연인"},
        ]
        builder = Stage4ContextBuilder(ctx)

        packet = builder.context_packets.build_continuity_packet(
            {
                "npcs": ["장천", "소연"],
                "items": [],
                "plots": [],
                "locations": [],
                "_full_text": "장천과 소연이 재회한다.",
            }
        )

        assert "관계 변천사" in packet
        assert "적→동맹→연인" in packet
        assert "(ep3→ep15→ep42)" in packet

    def test_build_continuity_packet_relationship_no_overlap(self):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": {"장천": {"role": "검객"}, "소연": {"role": "정보상"}},
                "dead_npcs": {},
                "active_items": {},
                "active_plots": [],
                "protagonist": {},
            }
        )
        ctx.current_project.db.get_npc_relationship_edges.return_value = [
            {"npc1": "장천", "npc2": "소연", "relation": "동맹", "since_ep": 15}
        ]
        builder = Stage4ContextBuilder(ctx)

        packet = builder.context_packets.build_continuity_packet(
            {
                "npcs": ["장천"],
                "items": [],
                "plots": [],
                "locations": [],
                "_full_text": "장천이 혼자 출발한다.",
            }
        )

        assert "관계 변천사" not in packet

    def test_build_continuity_packet_numeric_history(self):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": {},
                "dead_npcs": {},
                "active_items": {},
                "active_plots": [],
                "protagonist": {},
            }
        )
        ctx.fact_ledger = _make_fact_ledger(
            {
                "numbers": {
                    "자본금": {
                        "value": "10억",
                        "unit": "원",
                        "established_value": "1억",
                        "established_ep": 1,
                        "last_ep": 30,
                        "history": ["ep10: 3억 달성", "ep20: 6억 돌파", "ep30: 10억 도달"],
                    }
                }
            }
        )
        builder = Stage4ContextBuilder(ctx)

        packet = builder.context_packets.build_continuity_packet(
            {
                "npcs": [],
                "items": [],
                "plots": [],
                "locations": [],
                "_full_text": "이번 화의 핵심은 자본금 운용이다.",
            }
        )

        assert "수치 변화 이력" in packet
        assert "자본금: 1억 원(ep1) → 10억 원(ep30)" in packet
        assert "ep10: 3억 달성" in packet
        assert "ep30: 10억 도달" in packet

    def test_build_continuity_packet_numeric_no_match(self):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": {},
                "dead_npcs": {},
                "active_items": {},
                "active_plots": [],
                "protagonist": {},
            }
        )
        ctx.fact_ledger = _make_fact_ledger(
            {
                "numbers": {
                    "자본금": {
                        "value": "10억",
                        "unit": "원",
                        "established_value": "1억",
                        "established_ep": 1,
                        "last_ep": 30,
                        "history": ["ep30: 10억 도달"],
                    }
                }
            }
        )
        builder = Stage4ContextBuilder(ctx)

        packet = builder.context_packets.build_continuity_packet(
            {
                "npcs": [],
                "items": [],
                "plots": [],
                "locations": [],
                "_full_text": "이번 화는 감정선만 다룬다.",
            }
        )

        assert "수치 변화 이력" not in packet
        assert packet == ""

    def test_build_continuity_packet_extended_budget(self):
        ctx = _make_ctx()
        alive_npcs = {
            f"npc{i}": {"role": "검객", "relation": "동료", "personality": "냉철" * 30}
            for i in range(10)
        }
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": alive_npcs,
                "dead_npcs": {},
                "active_items": {"혈옥": {"status": "보유"}},
                "active_plots": [{"plot": "북해 원정"}],
                "protagonist": {"location": "북해"},
            }
        )
        ctx.fact_ledger = _make_fact_ledger(
            {
                "numbers": {
                    "자본금": {
                        "value": "10억",
                        "unit": "원",
                        "established_value": "1억",
                        "established_ep": 1,
                        "last_ep": 30,
                        "history": [f"ep{i}: 변화" for i in range(1, 10)],
                    }
                }
            }
        )
        ctx.current_project.db.get_npc_relationship_edges.return_value = [
            {"npc1": "npc0", "npc2": "npc1", "relation": "동맹", "since_ep": 5},
            {"npc1": "npc2", "npc2": "npc3", "relation": "경쟁", "since_ep": 8},
        ]
        ctx.current_project.db.get_relationship_history.side_effect = [
            [
                {"change_ep": 1, "new_relation": "적"},
                {"change_ep": 5, "new_relation": "동맹"},
            ],
            [
                {"change_ep": 4, "new_relation": "경쟁"},
                {"change_ep": 8, "new_relation": "동맹"},
            ],
        ]
        builder = Stage4ContextBuilder(ctx)

        packet = builder.context_packets.build_continuity_packet(
            {
                "npcs": list(alive_npcs.keys()),
                "items": ["혈옥"],
                "plots": ["북해 원정"],
                "locations": ["북해"],
                "_full_text": " ".join(list(alive_npcs.keys()) + ["자본금", "혈옥", "북해 원정"]),
            }
        )

        assert len(packet) <= 7000


class TestCondensedSummaries:
    def test_condensed_world_state_summary_uses_packet_refs_for_blueprint_npcs(self):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "last_updated_ep": 12,
                "protagonist": {"name": "장천", "location": "한양"},
                "alive_npcs": {
                    "장천": {"role": "주인공", "relation": "본인", "location": "한양"},
                    "소연": {"role": "정보상", "relation": "협력", "location": "개경"},
                    "진무": {"role": "추적자", "relation": "적대", "location": "하북"},
                },
                "active_items": {"흑검": {"status": "보유"}, "패도검": {"status": "보유"}},
                "active_plots": [{"plot": "혈교 추적", "since_ep": 9}, {"plot": "황실 거래", "since_ep": 11}],
            }
        )
        builder = Stage4ContextBuilder(ctx)

        summary = builder.context_packets.build_condensed_world_state_summary(
            {"npcs": ["소연"], "items": ["흑검"], "plots": ["혈교 추적"], "locations": ["한양"], "_full_text": "소연 흑검 혈교 추적"}
        )

        assert "진무" in summary
        assert "소연: 정보상" not in summary
        assert "Continuity Packet 참조" in summary
        assert "황실 거래" in summary
        assert "혈교 추적" not in summary

    def test_condensed_fact_ledger_summary_omits_cp_entities(self):
        ctx = _make_ctx()
        ctx.fact_ledger = _make_fact_ledger(
            {
                "last_updated_ep": 12,
                "characters": {
                    "소연": {"status": "alive", "role": "정보상", "relationship": "협력", "established_ep": 2},
                    "진무": {"status": "alive", "role": "추적자", "relationship": "적대", "established_ep": 5},
                },
                "items": {
                    "흑검": {"status": "보유", "owner": "장천"},
                    "패도검": {"status": "보유", "owner": "진무"},
                },
                "numbers": {
                    "자본금": {"value": "10억", "unit": "원", "last_ep": 12},
                    "명성": {"value": "A급", "unit": "", "last_ep": 12},
                },
            }
        )
        builder = Stage4ContextBuilder(ctx)

        summary = builder.context_packets.build_condensed_fact_ledger_summary(
            {"npcs": ["소연"], "items": ["흑검"], "plots": [], "locations": [], "_full_text": "소연 흑검 자본금"}
        )

        assert "진무" in summary
        assert "소연" not in summary
        assert "패도검" in summary
        assert "흑검" not in summary
        assert "명성" in summary
        assert "자본금" not in summary

    def test_condensed_fact_ledger_summary_marks_asset_numbers_as_carryover_baseline(self):
        ctx = _make_ctx()
        ctx.fact_ledger = _make_fact_ledger(
            {
                "last_updated_ep": 12,
                "characters": {},
                "items": {},
                "numbers": {
                    "자본금": {"value": "10억", "unit": "원", "last_ep": 12},
                    "명성": {"value": "A급", "unit": "", "last_ep": 12},
                },
            }
        )
        builder = Stage4ContextBuilder(ctx)

        summary = builder.context_packets.build_condensed_fact_ledger_summary(
            {"npcs": [], "items": [], "plots": [], "locations": [], "_full_text": "carryover probe"}
        )

        assert "자본금: 10억 원 (ep12 carryover baseline)" in summary
        assert "명성: A급 (ep12 기준)" in summary


class TestMandatoryContextContinuityPacket:
    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_mandatory_context_includes_packet(self, *_mocks):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": {"장천": {"role": "검객", "relation": "동료"}},
                "dead_npcs": {},
                "active_items": {"흑검": {"status": "보유"}},
                "active_plots": [{"plot": "혈교 추적"}],
                "protagonist": {"location": "한양"},
            }
        )
        ctx.fact_ledger = _make_fact_ledger(
            {"characters": {"장천": {"history": ["ep10: 혈교 단서 확보"]}}}
        )
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []
        builder = Stage4ContextBuilder(ctx)

        result = builder.build_mandatory_context(
            next_ep=21,
            arc_data={"arc_no": 1},
            arc_tactical="",
            prev_text="이전 원고 " * 40,
            prev_ending="엔딩",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
            blueprint={"integrated_scenario": "장천이 흑검을 들고 혈교 추적을 이어간다."},
        )

        assert "[Continuity Packet]" in result["mandatory_context"]
        assert "장천" in result["mandatory_context"]

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_mandatory_context_no_blueprint_no_packet(self, *_mocks):
        ctx = _make_ctx()
        ctx.world_state = _make_world_state(
            {
                "alive_npcs": {"장천": {"role": "검객"}},
                "dead_npcs": {},
                "active_items": {},
                "active_plots": [],
                "protagonist": {},
            }
        )
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []
        builder = Stage4ContextBuilder(ctx)

        result = builder.build_mandatory_context(
            next_ep=21,
            arc_data={"arc_no": 1},
            arc_tactical="",
            prev_text="이전 원고 " * 40,
            prev_ending="엔딩",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
            blueprint=None,
        )

        assert "[Continuity Packet]" not in result["mandatory_context"]
