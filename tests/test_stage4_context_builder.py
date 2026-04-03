"""[B-1-2] Stage4ContextBuilder unit tests."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from modules.core.context_advisor import RetrievalPlan, RetrievalSlot, RetrievalSources
from modules.core.stage4_context_builder import Stage4ContextBuilder
from modules.core.stage4_context_packets import Stage4ContextPackets
from modules.core.stage4_orchestrator import Stage4Orchestrator, _RoundContext


def _make_ctx():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.current_project = MagicMock()
    ctx.current_project.db = MagicMock()
    ctx.current_project.genre = {"name": "무협"}
    ctx.current_project.master_bible = {}
    ctx.current_project.load_v20_anchor = MagicMock(return_value=None)
    ctx.sys = MagicMock()
    ctx.sys.hud = MagicMock()
    ctx.sys.hud.get_v20_hud_report.return_value = "HUD 리포트"
    ctx.sys.hud.inventory = []
    ctx.sys.hud.techniques = []
    ctx.world_state = None
    ctx.fact_ledger = None
    ctx.state_tracker = None
    ctx.memory = None
    ctx.context_advisor = None
    ctx.foreshadow_tracker = None
    ctx.semantic_plot_guard = None
    ctx.load_narrative_summaries = MagicMock(return_value="")
    ctx.build_item_acquisition_timeline = MagicMock(return_value="")
    ctx.generate_writer_guidance_v60_8 = None
    ctx.enrich_director_result = None
    return ctx


class _AppTrapContextBuilder(Stage4ContextBuilder):
    @property
    def app(self):
        raise AssertionError("build_mandatory_context should not access self.app")


def _configure_hybrid_db(db, *, manuscripts=None, summaries=None, arcs=None):
    lock = MagicMock()
    lock.__enter__.return_value = None
    lock.__exit__.return_value = False
    db._lock = lock

    db.cursor = MagicMock()
    exec_result = MagicMock()
    exec_result.fetchall.return_value = summaries or []
    db.cursor.execute.return_value = exec_result
    # [A4-P0-2] conn.cursor() 로컬 커서 패턴 대응
    local_cur = MagicMock()
    local_cur.execute.return_value = local_cur
    local_cur.fetchall.return_value = summaries or []
    db.conn = MagicMock()
    db.conn.cursor.return_value = local_cur

    db.get_manuscripts_range.return_value = manuscripts or []
    db.get_episode_meta_summaries.return_value = summaries or []
    db.get_cumulative_bible.return_value = {}

    def _load_anchor_side_effect(key):
        if key == "arcs":
            return arcs or []
        return None

    db.load_anchor.side_effect = _load_anchor_side_effect


class TestContextBuilderInit:
    def test_init_with_ctx(self):
        ctx = _make_ctx()
        cb = Stage4ContextBuilder(ctx)
        assert cb.ctx is ctx
        assert isinstance(cb.context_packets, Stage4ContextPackets)

    def test_lazy_init_via_orchestrator(self):
        app = MagicMock()
        ctx = _make_ctx()
        orch = Stage4Orchestrator(app, context=ctx)

        cb = orch.context_builder

        assert isinstance(cb, Stage4ContextBuilder)
        assert cb.ctx is ctx

    def test_lazy_init_singleton(self):
        app = MagicMock()
        ctx = _make_ctx()
        orch = Stage4Orchestrator(app, context=ctx)

        cb1 = orch.context_builder
        cb2 = orch.context_builder

        assert cb1 is cb2

    def test_collect_npc_roster_handles_scene_breakdown_dict(self):
        names = Stage4ContextBuilder._collect_npc_roster(
            arc_data={},
            blueprint={
                "scene_breakdown": {
                    "scene1": {"npcs": ["alice"]},
                    "scene2": {"participants": "bob,charlie"},
                }
            },
        )

        assert "alice" in names
        assert "bob" in names
        assert "charlie" in names

    def test_source_defaults_align_with_validation_yaml(self):
        src = Path("modules/core/stage4_context_builder.py").read_text(encoding="utf-8")

        assert '_threshold("context.vector_max_results_s4", 50)' in src
        assert '_threshold("smart_retrieval.retrieval_mode", "hybrid")' in src
        assert '_threshold("smart_retrieval.stage4_total_budget", 300000)' in src
        assert '_threshold("context.mandatory_context_max", 400000)' in src
        assert '_threshold("context.lookback_excerpt_chars", 5000)' in src
        assert '_threshold("context.lookback_total_chars", 40000)' in src


class TestContextTailPreservation:
    def test_compose_work_focus_text_preserves_recent_tail_context(self):
        cb = Stage4ContextBuilder(_make_ctx())

        text = cb._compose_work_focus_text(
            arc_data={"constraint_summary": "HEAD-CONFLICT\n" + ("A" * 180) + "\nTAIL-CONFLICT"},
            arc_tactical="전술",
            prev_ending="엔딩",
            blueprint={"scene_breakdown": [{"summary": "SCENE-HEAD\n" + ("B" * 180) + "\nTAIL-WORK"}]},
            cp_entities={"npcs": ["alice"], "items": [], "plots": [], "locations": []},
            max_chars=180,
        )

        assert len(text) <= 180
        assert "TAIL-WORK" in text or "TAIL-CONFLICT" in text

    @patch("modules.core.stage4_context_builder.SemanticQueryBroker")
    def test_work_identity_slot_summary_preserves_relation_slice_tail(self, broker_cls):
        ctx = _make_ctx()
        broker_cls.return_value.build_stage4_relation_slice.return_value = "[관계 의미 질의]\n" + ("R" * 220) + "TAIL-REL"
        cb = Stage4ContextBuilder(ctx)

        summary = cb._build_work_identity_slot_summary(
            focus={
                "tracking_slots": ["slot-a", "slot-b"],
                "mandatory_scene_engines": ["engine-a"],
                "registry_profiles": [{"name": "talent_registry", "required_fields": ["goal", "risk"]}],
            },
            arc_data={"constraint_summary": "갈등축"},
            cp_entities={"npcs": ["alice"], "items": [], "plots": [], "locations": []},
            max_chars=180,
        )

        assert len(summary) <= 180
        assert "TAIL-REL" in summary

    def test_fetch_manuscript_excerpt_preserves_recent_tail_context(self):
        ctx = _make_ctx()
        ctx.db = ctx.current_project.db
        ctx.db.get_manuscripts_range.return_value = [
            {"ep_num": 7, "content": "HEAD-MS\n" + ("M" * 900) + "\nTAIL-MS"}
        ]
        cb = Stage4ContextBuilder(ctx)

        excerpt = cb._fetch_manuscript_excerpt(7, 7, max_chars=220)

        assert len(excerpt) <= 220
        assert "TAIL-MS" in excerpt


class TestSuggestAmbientNpcs:
    def test_suggest_ambient_npcs_office(self):
        blueprint = {
            "scene_breakdown": {
                "scene_1": {"location": "SW 사무실"},
            }
        }
        out = Stage4ContextBuilder._suggest_ambient_npcs(blueprint)
        assert "[TF-J 배경 인물 힌트]" in out
        assert "scene_1 (SW 사무실)" in out
        assert "직원" in out
        assert "비서" in out

    def test_suggest_ambient_npcs_cafe(self):
        blueprint = {
            "scene_breakdown": {
                "scene_2": {"location": "강남 카페"},
            }
        }
        out = Stage4ContextBuilder._suggest_ambient_npcs(blueprint)
        assert "scene_2 (강남 카페)" in out
        assert "바리스타" in out

    def test_suggest_ambient_npcs_no_match(self):
        blueprint = {
            "scene_breakdown": {
                "scene_1": {"location": "달 궤도 정거장"},
            }
        }
        out = Stage4ContextBuilder._suggest_ambient_npcs(blueprint)
        assert out == ""

    def test_suggest_ambient_npcs_empty_blueprint(self):
        out = Stage4ContextBuilder._suggest_ambient_npcs({})
        assert out == ""


class TestLoadChainLinkSection:
    def test_ep1_returns_empty(self):
        cb = Stage4ContextBuilder(_make_ctx())
        assert cb.load_chain_link_section(1) == ""

    def test_loads_chain_link_data(self):
        ctx = _make_ctx()
        ctx.current_project.db.load_anchor.return_value = {
            "cliffhanger": "적이 나타났다",
            "pending_actions": ["도망", "반격"],
            "emotional_state": "긴장",
            "physical_state": "부상",
            "location": "청풍산장",
            "time_marker": "심야",
        }
        cb = Stage4ContextBuilder(ctx)

        result = cb.load_chain_link_section(5)

        assert "적이 나타났다" in result
        assert "청풍산장" in result
        assert "도망" in result

    def test_no_data_returns_empty(self):
        ctx = _make_ctx()
        ctx.current_project.db.load_anchor.return_value = None
        cb = Stage4ContextBuilder(ctx)
        assert cb.load_chain_link_section(5) == ""

    def test_db_exception_returns_empty(self):
        ctx = _make_ctx()
        ctx.current_project.db.load_anchor.side_effect = RuntimeError("DB error")
        cb = Stage4ContextBuilder(ctx)
        assert cb.load_chain_link_section(5) == ""


class TestBuildContinuityPacketHelpers:
    def test_build_continuity_npc_sections_marks_dead_and_history(self):
        cb = Stage4ContextBuilder(_make_ctx())
        db = MagicMock()
        db.get_npc_history.return_value = [
            {
                "episode_no": 7,
                "field_name": "status",
                "old_value": "alive",
                "new_value": "dead",
                "reason": "sacrifice",
            }
        ]

        sections, used = cb.context_packets._build_continuity_npc_sections(
            npc_names=["ally"],
            ws_state={"dead_npcs": {"ally": {"cause": "duel", "name": "ally"}}},
            ledger={"characters": {"ally": {"history": ["ep3: saved the lead"]}}},
            db=db,
            budget=1000,
        )

        assert len(sections) == 1
        assert used == len(sections[0])
        assert "⚠️ 사망" in sections[0]
        assert "[이력] ep3: saved the lead" in sections[0]
        assert "[변경 7화] status: alive → dead (sacrifice)" in sections[0]

    def test_build_continuity_relationship_section_builds_trajectory_once(self):
        cb = Stage4ContextBuilder(_make_ctx())
        db = MagicMock()
        db.get_npc_relationship_edges.side_effect = [
            [{"npc1": "alice", "npc2": "bob", "relation": "friends", "since_ep": 2}],
            [{"npc1": "bob", "npc2": "alice", "relation": "friends", "since_ep": 2}],
        ]
        db.get_relationship_history.return_value = [
            {"new_relation": "rivals", "change_ep": 3},
            {"new_relation": "allies", "change_ep": 5},
        ]

        section = cb.context_packets._build_continuity_relationship_section(npc_names=["alice", "bob"], db=db)

        assert section.startswith("• 관계 변천사")
        assert section.count("alice ↔ bob") == 1
        assert "rivals→allies" in section
        assert "(ep3→ep5)" in section

    @patch("modules.core.stage4_context_builder._build_canonical_facts_section", return_value="• 정설 팩트\nfact")
    def test_build_continuity_fact_sections_includes_numeric_and_canonical(self, _mock_canonical):
        cb = Stage4ContextBuilder(_make_ctx())

        sections = cb.context_packets._build_continuity_fact_sections(
            full_text="score must stay stable in the report",
            ledger={
                "numbers": {
                    "score": {
                        "value": 12,
                        "unit": "pt",
                        "established_value": 10,
                        "established_ep": 2,
                        "last_ep": 7,
                        "history": ["ep7: bonus applied"],
                    }
                }
            },
            fact_ledger=MagicMock(),
            db=MagicMock(),
        )

        assert len(sections) == 2
        assert sections[0].startswith("• 수치 변화 이력")
        assert "score: 10 pt(ep2) → 12 pt(ep7)" in sections[0]
        assert "└ ep7: bonus applied" in sections[0]
        assert sections[1] == "• 정설 팩트\nfact"


class TestBuildExtendedLookback:
    def test_ep3_or_less_returns_empty(self):
        cb = Stage4ContextBuilder(_make_ctx())
        assert cb.build_extended_lookback_digest(3) == ""
        assert cb.build_extended_lookback_digest(1) == ""

    def test_returns_digest_with_excerpts(self):
        ctx = _make_ctx()
        ctx.current_project.db.get_recent_manuscript_excerpts.return_value = [
            {"ep_num": 4, "content": "첫 번째 문장. " * 20},
            {"ep_num": 7, "content": "둘째 문장. " * 20},
            {"ep_num": 9, "content": "최근 3화 범위라 제외됨"},  # next_ep=11에서 제외
        ]
        cb = Stage4ContextBuilder(ctx)

        result = cb.build_extended_lookback_digest(11)

        assert "[확장 Lookback" in result
        assert "[제4화]" in result
        assert "[제7화]" in result
        assert "[제9화]" not in result

    def test_exception_returns_empty(self):
        ctx = _make_ctx()
        ctx.current_project.db.get_recent_manuscript_excerpts.side_effect = RuntimeError("fail")
        cb = Stage4ContextBuilder(ctx)
        assert cb.build_extended_lookback_digest(10) == ""


class TestPrepareEpisodeContext:
    def test_build_episode_base_payload_normalizes_tactical_doc_and_prev_ending(self):
        from modules.core.stage4_context_builder import Stage4EpisodeBasePayload

        ctx = _make_ctx()
        prev_text = "이전 화 내용 " * 300
        ctx.current_project.db.get_manuscript.return_value = {"content": prev_text}
        cb = Stage4ContextBuilder(ctx)
        cb._build_prev_manuscripts_text = MagicMock(return_value="lookback")
        cb._build_episode_digest = MagicMock(return_value="digest")

        result = cb._build_episode_base_payload(
            next_ep=5,
            arc_data={"ep_start": 1, "ep_count": 10, "tactical_doc": {"k": "v"}},
            chief_writer=MagicMock(),
            db=ctx.current_project.db,
        )

        assert result == Stage4EpisodeBasePayload(
            arc_pos=5,
            total_ep_in_arc=10,
            arc_tactical='{"k": "v"}',
            prev_text=prev_text,
            prev_ending=prev_text[-2500:],
            prev_manuscripts_text="lookback",
            episode_digest="digest",
        )
        cb._build_prev_manuscripts_text.assert_called_once_with(5)
        cb._build_episode_digest.assert_called_once()

    def test_build_episode_base_payload_injects_long_term_anchor_before_lookback(self):
        ctx = _make_ctx()
        ctx.current_project.db.get_manuscript.return_value = {"content": "이전 화"}
        ctx.world_state = MagicMock()
        ctx.world_state.get_long_term_anchor.return_value = "[LONGTERM]"
        cb = Stage4ContextBuilder(ctx)
        cb._build_prev_manuscripts_text = MagicMock(return_value="lookback")
        cb._build_episode_digest = MagicMock(return_value="digest")

        result = cb._build_episode_base_payload(
            next_ep=60,
            arc_data={"ep_start": 51, "ep_count": 10, "tactical_doc": "전술"},
            chief_writer=MagicMock(),
            db=ctx.current_project.db,
        )

        assert result["prev_manuscripts_text"] == "[LONGTERM]\n\n---\n\nlookback"
        ctx.world_state.get_long_term_anchor.assert_called_once_with(current_ep=60)

    def test_build_episode_state_payload_collects_hud_and_state_sections(self):
        from modules.core.stage4_context_builder import Stage4EpisodeStatePayload

        ctx = _make_ctx()
        ctx.sys.hud.inventory = ["청룡검"]
        ctx.sys.hud.techniques = ["비연보"]
        ctx.current_project.db.get_cumulative_bible.return_value = {"dead_npcs": ["흑풍"]}
        ctx.build_item_acquisition_timeline.return_value = "timeline"
        ctx.world_state = MagicMock()
        ctx.world_state.get_summary.return_value = "world summary"
        cb = Stage4ContextBuilder(ctx)
        cb.load_chain_link_section = MagicMock(return_value="chain text")
        cb._collect_recent_scene_keywords = MagicMock(return_value=[{"ep": 4, "scenes": [{"검", "혈투"}]}])

        result = cb._build_episode_state_payload(next_ep=5, db=ctx.current_project.db)

        assert result == Stage4EpisodeStatePayload(
            hud_report="HUD 리포트",
            current_inventory=["청룡검"],
            current_martial_arts=["비연보"],
            cumulative_bible={"dead_npcs": ["흑풍"]},
            dead_npcs=["흑풍"],
            item_acquisition_timeline="timeline",
            chain_link_section="chain text",
            world_state_summary="world summary",
            recent_scene_keywords=[{"ep": 4, "scenes": [{"검", "혈투"}]}],
        )
        cb.load_chain_link_section.assert_called_once_with(5)
        cb._collect_recent_scene_keywords.assert_called_once_with(ctx.current_project.db, 5, lookback=3)

    def test_build_episode_state_payload_normalizes_dead_npc_string_and_hud_none(self):
        ctx = _make_ctx()
        ctx.sys.hud = None
        ctx.current_project.db.get_cumulative_bible.return_value = {"dead_npcs": "흑풍"}
        cb = Stage4ContextBuilder(ctx)
        cb.load_chain_link_section = MagicMock(return_value="")
        cb._collect_recent_scene_keywords = MagicMock(side_effect=RuntimeError("scene fail"))

        result = cb._build_episode_state_payload(next_ep=5, db=ctx.current_project.db)

        assert result["hud_report"] == ""
        assert result["current_inventory"] == []
        assert result["current_martial_arts"] == []
        assert result["dead_npcs"] == ["흑풍"]
        assert result["recent_scene_keywords"] == []

    def test_build_episode_digest_uses_chief_writer_generator(self):
        ctx = _make_ctx()
        cb = Stage4ContextBuilder(ctx)
        chief_writer = MagicMock()
        chief_writer._generate_episode_digest.return_value = "digest body"

        result = cb._build_episode_digest(
            prev_text="previous manuscript",
            next_ep=5,
            chief_writer=chief_writer,
        )

        assert result == "digest body"
        chief_writer._generate_episode_digest.assert_called_once_with("previous manuscript", 4)

    def test_build_episode_digest_appends_finance_hud_snapshot(self):
        ctx = _make_ctx()

        class DummyFinanceHUD:
            def __init__(self):
                self.pro_data = {"capital": "1000냥", "total_assets": "2500냥"}

        ctx.sys.hud = DummyFinanceHUD()
        cb = Stage4ContextBuilder(ctx)
        chief_writer = MagicMock()
        chief_writer._generate_episode_digest.return_value = "digest body"

        with patch("modules.core.genre_hud_manager.FinanceHUDManager", DummyFinanceHUD):
            result = cb._build_episode_digest(
                prev_text="previous manuscript",
                next_ep=5,
                chief_writer=chief_writer,
            )

        assert result.startswith("digest body")
        assert "1000냥" in result
        assert "2500냥" in result

    def test_returns_all_keys(self):
        ctx = _make_ctx()
        ctx.current_project.db.get_manuscript.return_value = {"content": "이전 화 내용 " * 40}
        ctx.current_project.db.get_cumulative_bible.return_value = {"dead_npcs": ["흑풍"]}
        chief_writer = MagicMock()
        chief_writer._generate_episode_digest.return_value = "다이제스트"
        cb = Stage4ContextBuilder(ctx)

        result = cb.prepare_episode_context(
            5,
            {"ep_start": 1, "ep_count": 10, "tactical_doc": "전술"},
            chief_writer,
        )

        expected_keys = {
            "arc_pos",
            "total_ep_in_arc",
            "arc_tactical",
            "prev_text",
            "prev_ending",
            "prev_manuscripts_text",
            "episode_digest",
            "hud_report",
            "current_inventory",
            "current_martial_arts",
            "cumulative_bible",
            "dead_npcs",
            "item_acquisition_timeline",
            "chain_link_section",
            "world_state_summary",
        }
        assert expected_keys.issubset(set(result.keys()))
        assert result["arc_pos"] == 5

    def test_tactical_doc_dict_converted(self):
        ctx = _make_ctx()
        ctx.current_project.db.get_manuscript.return_value = {"content": "x" * 600}
        ctx.current_project.db.get_cumulative_bible.return_value = {}
        cb = Stage4ContextBuilder(ctx)

        result = cb.prepare_episode_context(
            2,
            {"ep_start": 1, "ep_count": 5, "tactical_doc": {"k": "v"}},
            MagicMock(),
        )

        assert '"k": "v"' in result["arc_tactical"]

    def test_chain_link_loader_called(self):
        ctx = _make_ctx()
        ctx.current_project.db.get_manuscript.return_value = {"content": "x" * 600}
        ctx.current_project.db.get_cumulative_bible.return_value = {}
        cb = Stage4ContextBuilder(ctx)
        with patch.object(cb, "load_chain_link_section", return_value="chain text") as mock_loader:
            result = cb.prepare_episode_context(3, {"ep_start": 1, "ep_count": 5, "tactical_doc": ""}, MagicMock())
        mock_loader.assert_called_once_with(3)
        assert result["chain_link_section"] == "chain text"

    def test_hud_none_falls_back_to_empty(self):
        ctx = _make_ctx()
        ctx.sys.hud = None
        ctx.current_project.db.get_manuscript.return_value = {"content": "x" * 600}
        ctx.current_project.db.get_cumulative_bible.return_value = {}
        cb = Stage4ContextBuilder(ctx)

        result = cb.prepare_episode_context(
            2,
            {"ep_start": 1, "ep_count": 5, "tactical_doc": ""},
            MagicMock(),
        )

        assert result["hud_report"] == ""
        assert result["current_inventory"] == []
        assert result["current_martial_arts"] == []

    def test_hybrid_context_tier1_full_text(self):
        ctx = _make_ctx()
        db = ctx.current_project.db
        _configure_hybrid_db(
            db,
            manuscripts=[
                {"ep_num": 34, "content": "A" * 140},
                {"ep_num": 39, "content": "B" * 140},
            ],
            summaries=[],
            arcs=[],
        )
        db.get_manuscript.side_effect = lambda ep: {"content": f"ep{ep} " * 120}
        chief_writer = MagicMock()
        chief_writer._generate_episode_digest.return_value = ""

        cb = Stage4ContextBuilder(ctx)
        result = cb.prepare_episode_context(
            40,
            {"ep_start": 1, "ep_count": 50, "tactical_doc": ""},
            chief_writer,
        )

        assert "[EP 34]" in result["prev_manuscripts_text"]
        assert "[EP 39]" in result["prev_manuscripts_text"]

    def test_hybrid_context_tier2_summary(self):
        ctx = _make_ctx()
        db = ctx.current_project.db
        _configure_hybrid_db(
            db,
            manuscripts=[],
            summaries=[{"ep_num": 12, "summary": "summary tier2"}],
            arcs=[],
        )
        db.get_manuscript.side_effect = lambda ep: {"content": f"ep{ep} " * 120}
        chief_writer = MagicMock()
        chief_writer._generate_episode_digest.return_value = ""

        cb = Stage4ContextBuilder(ctx)
        result = cb.prepare_episode_context(
            40,
            {"ep_start": 1, "ep_count": 50, "tactical_doc": ""},
            chief_writer,
        )

        assert "-- Tier2 summaries (21-60 episodes back) --" in result["prev_manuscripts_text"]
        assert "[EP 12 summary] summary tier2" in result["prev_manuscripts_text"]
        db.get_episode_meta_summaries.assert_called_once_with(1, 10)
        db.conn.cursor.assert_not_called()

    def test_hybrid_context_tier2_summary_respects_5k_cap(self):
        ctx = _make_ctx()
        db = ctx.current_project.db
        long_summary = "A" * 6000
        _configure_hybrid_db(
            db,
            manuscripts=[],
            summaries=[{"ep_num": 12, "summary": long_summary}],
            arcs=[],
        )
        db.get_manuscript.side_effect = lambda ep: {"content": f"ep{ep} " * 120}
        chief_writer = MagicMock()
        chief_writer._generate_episode_digest.return_value = ""

        cb = Stage4ContextBuilder(ctx)
        result = cb.prepare_episode_context(
            40,
            {"ep_start": 1, "ep_count": 50, "tactical_doc": ""},
            chief_writer,
        )

        assert f"[EP 12 summary] {'A' * 5000}" in result["prev_manuscripts_text"]
        assert "A" * 5001 not in result["prev_manuscripts_text"]

    def test_hybrid_context_tier3_arc_summary(self):
        ctx = _make_ctx()
        db = ctx.current_project.db
        _configure_hybrid_db(
            db,
            manuscripts=[],
            summaries=[],
            arcs=[
                {"arc_no": 1, "episodes": [1, 2, 3]},
                {"arc_no": 2, "episodes": [32, 33, 34]},
            ],
        )
        db.get_manuscript.side_effect = lambda ep: {"content": f"ep{ep} " * 120}

        def _load_v20_anchor(name):
            if name == "arc_summary_1":
                return {"summary": "arc one summary"}
            if name == "arc_summary_2":
                return {"summary": "arc two summary"}
            return None

        ctx.current_project.load_v20_anchor.side_effect = _load_v20_anchor
        chief_writer = MagicMock()
        chief_writer._generate_episode_digest.return_value = ""

        cb = Stage4ContextBuilder(ctx)
        result = cb.prepare_episode_context(
            80,
            {"ep_start": 1, "ep_count": 100, "tactical_doc": ""},
            chief_writer,
        )

        assert "-- Tier3 arc summaries (older than 60 episodes) --" in result["prev_manuscripts_text"]
        assert "[Arc 1 summary] arc one summary" in result["prev_manuscripts_text"]
        assert "[Arc 2 summary]" not in result["prev_manuscripts_text"]

    def test_hybrid_context_tier3_arc_summary_respects_8k_cap(self):
        ctx = _make_ctx()
        db = ctx.current_project.db
        long_summary = "B" * 9000
        _configure_hybrid_db(
            db,
            manuscripts=[],
            summaries=[],
            arcs=[{"arc_no": 1, "episodes": [1, 2, 3]}],
        )
        db.get_manuscript.side_effect = lambda ep: {"content": f"ep{ep} " * 120}
        ctx.current_project.load_v20_anchor.side_effect = lambda name: (
            {"summary": long_summary} if name == "arc_summary_1" else None
        )
        chief_writer = MagicMock()
        chief_writer._generate_episode_digest.return_value = ""

        cb = Stage4ContextBuilder(ctx)
        result = cb.prepare_episode_context(
            80,
            {"ep_start": 1, "ep_count": 100, "tactical_doc": ""},
            chief_writer,
        )

        assert f"[Arc 1 summary] {'B' * 8000}" in result["prev_manuscripts_text"]
        assert "B" * 8001 not in result["prev_manuscripts_text"]

    def test_hybrid_context_early_episodes(self):
        ctx = _make_ctx()
        db = ctx.current_project.db
        _configure_hybrid_db(
            db,
            manuscripts=[
                {"ep_num": 1, "content": "A" * 140},
                {"ep_num": 5, "content": "B" * 140},
            ],
            summaries=[{"ep_num": 2, "summary": "should not appear"}],
            arcs=[{"arc_no": 1, "episodes": [1, 2, 3]}],
        )
        db.get_manuscript.side_effect = lambda ep: {"content": f"ep{ep} " * 120}
        ctx.current_project.load_v20_anchor.return_value = {"summary": "arc summary should be ignored"}
        chief_writer = MagicMock()
        chief_writer._generate_episode_digest.return_value = ""

        cb = Stage4ContextBuilder(ctx)
        result = cb.prepare_episode_context(
            6,
            {"ep_start": 1, "ep_count": 50, "tactical_doc": ""},
            chief_writer,
        )

        assert "[EP 5]" in result["prev_manuscripts_text"]
        assert "-- Tier2 summaries (11-30 episodes back) --" not in result["prev_manuscripts_text"]
        assert "-- Tier3 arc summaries (older than 30 episodes) --" not in result["prev_manuscripts_text"]


class TestStructuredEntityAndNpcBoundary:
    def test_extract_blueprint_entities_merges_arc_state_changes(self):
        ctx = _make_ctx()
        ctx.world_state = MagicMock()
        ctx.world_state._state = {
            "alive_npcs": {},
            "dead_npcs": {},
            "active_items": {},
            "active_plots": [],
            "protagonist": {"location": "개봉"},
        }
        cb = Stage4ContextBuilder(ctx)

        entities = cb._extract_blueprint_entities(
            {"integrated_scenario": "주인공은 결심했다."},
            arc_data={
                "state_changes": {
                    "npc_introductions": [{"name": "노사부"}],
                    "items_acquired": [{"name": "청룡검"}],
                    "active_plots": [{"plot": "사문 추적"}],
                    "npc_movements": [{"name": "노사부", "to": "무당산"}],
                }
            },
        )

        assert "노사부" in entities["npcs"]
        assert "청룡검" in entities["items"]
        assert "사문 추적" in entities["plots"]
        assert "무당산" in entities["locations"]

    def test_build_npc_boundary_block_includes_knowledge_and_identity_fields(self):
        ctx = _make_ctx()
        ctx.current_project.master_bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {
                            "name": "노사부",
                            "knowledge_era": "선사시대",
                            "knowledge_tags": ["부족사회", "석기"],
                            "expertise_domain": "생존술",
                            "secrets_known": ["회귀 비밀"],
                            "public_facade": "떠돌이 노인",
                            "secret_role": "숨은 수호자",
                            "known_by": ["진우"],
                        }
                    ]
                }
            }
        }
        ctx.world_state = MagicMock()
        ctx.world_state._state = {"alive_npcs": {}, "dead_npcs": {}}
        cb = Stage4ContextBuilder(ctx)

        block = cb._build_npc_boundary_block(["노사부"])

        assert "[NPC 지식 범위/비밀 인지 참고]" in block
        assert "지식시대=선사시대" in block
        assert "전문영역=생존술" in block
        assert "비밀인지=회귀 비밀" in block
        assert "이중정체=공개=떠돌이 노인 / 비밀=숨은 수호자 / 인지=진우" in block


class TestBuildMandatoryContext:
    def test_build_empty_mandatory_context_payload_returns_blank_fields(self):
        from modules.core.stage4_context_builder import Stage4MandatoryContextPayload

        result = Stage4ContextBuilder._build_empty_mandatory_context_payload()

        assert result == Stage4MandatoryContextPayload(
            reference_anchor_prompt="",
            mandatory_context="",
            anti_trope_prompt="",
            justification_prompt="",
            reflexion_prompt="",
        )

    def test_build_empty_mandatory_context_payload_delegates_to_result_payload_builder(self):
        from modules.core.stage4_context_builder import Stage4MandatoryContextPayload

        expected = Stage4MandatoryContextPayload(
            reference_anchor_prompt="",
            mandatory_context="",
            anti_trope_prompt="",
            justification_prompt="",
            reflexion_prompt="",
        )

        with patch.object(
            Stage4ContextBuilder,
            "_build_mandatory_context_result_payload",
            return_value=expected,
        ) as payload_builder:
            result = Stage4ContextBuilder._build_empty_mandatory_context_payload()

        assert result == expected
        payload_builder.assert_called_once_with(
            reference_anchor_prompt="",
            mandatory_context="",
            anti_trope_prompt="",
            justification_prompt="",
            reflexion_prompt="",
        )

    def test_no_writer_agent_returns_empty(self):
        cb = Stage4ContextBuilder(_make_ctx())

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={},
            arc_tactical="",
            prev_text="",
            prev_ending="",
            hud_report="",
            writer_agent=None,
            anchor_sys=MagicMock(),
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        assert result["mandatory_context"] == ""
        assert result["reference_anchor_prompt"] == ""

    def test_no_writer_agent_short_circuits_before_payload_build(self):
        cb = Stage4ContextBuilder(_make_ctx())
        cb._build_mandatory_context_payload = MagicMock(side_effect=AssertionError("should not be called"))

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={},
            arc_tactical="",
            prev_text="",
            prev_ending="",
            hud_report="",
            writer_agent=None,
            anchor_sys=MagicMock(),
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        assert result["mandatory_context"] == ""
        cb._build_mandatory_context_payload.assert_not_called()

    def test_load_reference_anchor_prompt_returns_generated_prompt(self):
        cb = Stage4ContextBuilder(_make_ctx())
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = [{"type": "item", "name": "청월검"}]
        anchor_sys.get_critical_anchors.return_value = []
        anchor_sys.generate_reference_prompt.return_value = "anchor prompt"

        result = cb._load_reference_anchor_prompt(
            anchor_sys=anchor_sys,
            next_ep=5,
            arc_tactical="전술",
        )

        assert result == "anchor prompt"
        anchor_sys.generate_reference_prompt.assert_called_once()

    def test_load_reference_anchor_prompt_logs_and_returns_empty_on_error(self):
        ctx = _make_ctx()
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.side_effect = RuntimeError("anchor boom")

        result = cb._load_reference_anchor_prompt(
            anchor_sys=anchor_sys,
            next_ep=5,
            arc_tactical="전술",
        )

        assert result == ""
        ctx.ui.log.assert_called_once()

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_load_base_mandatory_context_returns_writer_context_and_records_hud(self, _mock_build):
        cb = Stage4ContextBuilder(_make_ctx())
        cb._record_hud_anomaly_observation = MagicMock()

        result = cb._load_base_mandatory_context(next_ep=5)

        assert result == "writer mandatory"
        cb._record_hud_anomaly_observation.assert_called_once()

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", side_effect=RuntimeError("ctx boom"))
    def test_load_base_mandatory_context_logs_and_returns_warning_on_error(self, _mock_build):
        ctx = _make_ctx()
        cb = Stage4ContextBuilder(ctx)

        result = cb._load_base_mandatory_context(next_ep=5)

        assert result.startswith("[경고] 필수 컨텍스트 로딩 실패")
        ctx.ui.log.assert_called_once()

    def test_build_mandatory_context_seed_builds_focus_tier0_and_slot_summary(self):
        cb = Stage4ContextBuilder(_make_ctx())
        cb._extract_blueprint_entities = MagicMock(return_value={"npcs": ["연홍"], "items": [], "plots": [], "locations": [], "_full_text": "bp"})
        cb._resolve_work_retrieval_focus = MagicMock(return_value={"tracking_slots": ["소꿉친구 라인"]})
        cb._build_tier0_mandatory_sections = MagicMock(return_value=["writer mandatory"])
        cb._build_work_identity_slot_summary = MagicMock(return_value="[작품 추적 슬롯 요약]\n소꿉친구 라인")

        result = cb._build_mandatory_context_seed(
            arc_data={"arc_no": 1},
            arc_tactical="소꿉친구 라인 재등장",
            prev_ending="연홍과의 인연이 남았다",
            blueprint={"scene_breakdown": {}},
            mandatory_context="writer mandatory",
        )

        assert result["cp_entities"]["npcs"] == ["연홍"]
        assert result["work_focus"]["tracking_slots"] == ["소꿉친구 라인"]
        assert result["tier0_parts"] == ["writer mandatory"]
        assert result["slot_summary"].startswith("[작품 추적 슬롯 요약]")
        cb._resolve_work_retrieval_focus.assert_called_once()
        cb._build_tier0_mandatory_sections.assert_called_once()
        cb._build_work_identity_slot_summary.assert_called_once()

    def test_resolve_mandatory_context_cp_entities_returns_extracted_blueprint_entities(self):
        cb = Stage4ContextBuilder(_make_ctx())
        cb._extract_blueprint_entities = MagicMock(
            return_value={"npcs": ["연홍"], "items": ["옥패"], "plots": [], "locations": ["객잔"], "_full_text": "bp"}
        )

        result = cb._resolve_mandatory_context_cp_entities(
            blueprint={"scene_breakdown": {}},
            arc_data={"arc_no": 1},
        )

        assert result["npcs"] == ["연홍"]
        assert result["items"] == ["옥패"]
        cb._extract_blueprint_entities.assert_called_once_with(
            {"scene_breakdown": {}},
            arc_data={"arc_no": 1},
        )

    def test_resolve_mandatory_context_cp_entities_returns_empty_payload_on_extraction_failure(self):
        cb = Stage4ContextBuilder(_make_ctx())
        cb._extract_blueprint_entities = MagicMock(side_effect=RuntimeError("bp boom"))

        result = cb._resolve_mandatory_context_cp_entities(
            blueprint={"scene_breakdown": {}},
            arc_data={"arc_no": 1},
        )

        assert result == {"npcs": [], "items": [], "plots": [], "locations": [], "_full_text": ""}

    def test_build_mandatory_context_retrieval_coverage_chains_aux_retrieval_and_compose(self):
        cb = Stage4ContextBuilder(_make_ctx())
        cb.context_packets.build_tier12_auxiliary_sections = MagicMock(
            return_value={"tier1_parts": ["tier1"], "tier2_parts": ["tier2"]}
        )
        cb._collect_stage4_retrieval_context = MagicMock(
            return_value={"retrieval_plan": "plan", "sc_parts": ["sc"], "tier1_parts": ["tier1+"]}
        )
        cb._compose_context_with_retrieval_coverage = MagicMock(
            return_value={
                "mandatory_context": "mandatory",
                "coverage_warnings": ["warn"],
                "source_counts": {"sc": 1},
                "tier2_parts": ["tier2+"],
            }
        )

        result = cb._build_mandatory_context_retrieval_coverage(
            next_ep=5,
            arc_data={"arc_no": 1},
            blueprint={"scene_breakdown": {}},
            s4_genre_type="wuxia",
            v50_modules_available=False,
            pacing_analyzer=None,
            prev_text="prev",
            prev_ending="ending",
            arc_tactical="전술",
            work_focus={"tracking_slots": ["라인"]},
            tier0_parts=["tier0"],
            slot_summary="slot summary",
        )

        assert result["mandatory_context"] == "mandatory"
        cb.context_packets.build_tier12_auxiliary_sections.assert_called_once()
        cb._collect_stage4_retrieval_context.assert_called_once()
        cb._compose_context_with_retrieval_coverage.assert_called_once()

    def test_build_state_tracker_auxiliary_sections_uses_summary_path_and_arc_history(self):
        ctx = _make_ctx()
        state_tracker = MagicMock()
        ctx.state_tracker = state_tracker
        ctx.current_project.load_v20_anchor.side_effect = (
            lambda key: {"summary": key} if key in {"arc_summary_1", "arc_summary_2"} else None
        )
        cb = Stage4ContextBuilder(ctx)
        state_tracker.get_all_summaries.return_value = {"resolved_plots": "summary"}
        state_tracker.format_arc_summary_for_prompt.return_value = "arc summary prompt"
        cb._filter_state_tracker_summaries_for_authority = MagicMock(
            return_value=({"resolved_plots": "filtered summary"}, {"dead_npc": "suppressed"})
        )
        cb._build_state_tracker_authority_note = MagicMock(return_value="authority note")
        cb._prioritize_summaries_by_work_focus = MagicMock(return_value=["focused summary"])

        result = cb.context_packets._build_state_tracker_auxiliary_sections(
            state_tracker=state_tracker,
            arc_data={"arc_no": 3},
            s4_genre_type="wuxia",
            work_focus="resolved plot",
        )

        assert result == ["authority note", "focused summary", "arc summary prompt"]
        state_tracker.get_all_summaries.assert_called_once_with(arc_no=3, genre="wuxia")
        state_tracker.format_arc_summary_for_prompt.assert_called_once()

    def test_build_state_tracker_auxiliary_sections_falls_back_when_summary_bundle_fails(self):
        ctx = _make_ctx()
        state_tracker = MagicMock()
        ctx.state_tracker = state_tracker
        cb = Stage4ContextBuilder(ctx)
        state_tracker.get_all_summaries.side_effect = RuntimeError("boom")
        state_tracker.format_arc_summary_for_prompt.return_value = ""
        cb._filter_state_tracker_summaries_for_authority = MagicMock(
            return_value=({"dungeon_clear": "fallback summary"}, {})
        )
        cb._build_state_tracker_authority_note = MagicMock(return_value="")
        cb._prioritize_summaries_by_work_focus = MagicMock(return_value=["focused fallback"])

        result = cb.context_packets._build_state_tracker_auxiliary_sections(
            state_tracker=state_tracker,
            arc_data={"arc_no": 1},
            s4_genre_type="hunter",
            work_focus="dungeon clear",
        )

        assert result == ["focused fallback"]
        state_tracker.get_dungeon_clear_summary.assert_called_once()
        state_tracker.get_skill_cooldown_summary.assert_called_once()

    def test_build_mandatory_context_payload_merges_helper_outputs(self):
        from modules.core.stage4_context_builder import Stage4MandatoryContextPayload

        cb = Stage4ContextBuilder(_make_ctx())
        cb._load_reference_anchor_prompt = MagicMock(return_value="anchor prompt")
        cb._load_base_mandatory_context = MagicMock(return_value="writer mandatory")
        cb._build_mandatory_context_seed = MagicMock(
            return_value={
                "cp_entities": {"npcs": ["연홍"]},
                "work_focus": {"tracking_slots": ["핵심 라인"]},
                "tier0_parts": ["tier0"],
                "slot_summary": "slot summary",
            }
        )
        cb._build_mandatory_context_retrieval_coverage = MagicMock(
            return_value={
                "mandatory_context": "covered mandatory",
                "coverage_warnings": ["warn"],
                "source_counts": {"sc": 1},
                "tier2_parts": ["tier2"],
            }
        )
        cb._build_mandatory_prompt_injections = MagicMock(
            return_value={
                "anti_trope_prompt": "anti",
                "justification_prompt": "just",
                "reflexion_prompt": "reflect",
            }
        )

        result = cb._build_mandatory_context_payload(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="전술",
            prev_ending="ending",
            prev_text="prev",
            hud_report="HUD",
            anchor_sys=MagicMock(),
            genre_name="무협",
            blueprint={"scene_breakdown": {}},
            s4_genre_type="wuxia",
            v50_modules_available=False,
            pacing_analyzer=None,
        )

        assert isinstance(result, dict)
        assert result == Stage4MandatoryContextPayload(
            reference_anchor_prompt="anchor prompt",
            mandatory_context="covered mandatory",
            anti_trope_prompt="anti",
            justification_prompt="just",
            reflexion_prompt="reflect",
        )
        cb._build_mandatory_context_seed.assert_called_once_with(
            arc_data={"arc_no": 1},
            arc_tactical="전술",
            prev_ending="ending",
            blueprint={"scene_breakdown": {}},
            mandatory_context="writer mandatory",
        )
        cb._build_mandatory_context_retrieval_coverage.assert_called_once()
        cb._build_mandatory_prompt_injections.assert_called_once_with(
            next_ep=5,
            hud_report="HUD",
            genre_name="무협",
            blueprint={"scene_breakdown": {}},
            prev_text="prev",
        )

    def test_build_mandatory_context_result_payload_maps_all_fields(self):
        from modules.core.stage4_context_builder import Stage4MandatoryContextPayload

        cb = Stage4ContextBuilder(_make_ctx())

        result = cb._build_mandatory_context_result_payload(
            reference_anchor_prompt="anchor prompt",
            mandatory_context="mandatory",
            anti_trope_prompt="anti",
            justification_prompt="just",
            reflexion_prompt="reflect",
        )

        assert result == Stage4MandatoryContextPayload(
            reference_anchor_prompt="anchor prompt",
            mandatory_context="mandatory",
            anti_trope_prompt="anti",
            justification_prompt="just",
            reflexion_prompt="reflect",
        )

    def test_append_writer_guidance_prompt_appends_block_to_existing_justification(self):
        ctx = _make_ctx()
        ctx.generate_writer_guidance_v60_8 = MagicMock(return_value="high impact guidance")
        cb = Stage4ContextBuilder(ctx)

        result = cb._append_writer_guidance_prompt(
            justification_prompt="base justification",
            blueprint={"scene_breakdown": {}},
            prev_text="previous manuscript",
        )

        assert result == "base justification\n\n[Writer Guidance]\nhigh impact guidance"
        ctx.generate_writer_guidance_v60_8.assert_called_once_with(
            blueprint={"scene_breakdown": {}},
            prev_manuscript="previous manuscript",
        )

    @patch("modules.core.stage4_context_builder._build_justification", return_value="just")
    @patch("modules.core.stage4_context_builder._build_anti_trope", return_value="anti")
    def test_build_mandatory_prompt_bases_returns_anti_trope_and_justification(self, *_mocks):
        from modules.core.stage4_context_builder import Stage4PromptBasesPayload

        cb = Stage4ContextBuilder(_make_ctx())

        result = cb._build_mandatory_prompt_bases(
            hud_report="HUD",
            genre_name="무협",
        )

        assert result == Stage4PromptBasesPayload(
            anti_trope_prompt="anti",
            justification_prompt="just",
        )

    @patch("modules.core.stage4_context_builder._build_justification", side_effect=RuntimeError("just boom"))
    @patch("modules.core.stage4_context_builder._build_anti_trope", side_effect=RuntimeError("anti boom"))
    def test_build_mandatory_prompt_bases_logs_and_returns_empty_on_failure(self, *_mocks):
        from modules.core.stage4_context_builder import Stage4PromptBasesPayload

        ctx = _make_ctx()
        cb = Stage4ContextBuilder(ctx)

        result = cb._build_mandatory_prompt_bases(
            hud_report="HUD",
            genre_name="무협",
        )

        assert result == Stage4PromptBasesPayload(
            anti_trope_prompt="",
            justification_prompt="",
        )
        assert ctx.ui.log.call_count == 2

    def test_build_mandatory_prompt_payload_maps_all_prompt_fields(self):
        cb = Stage4ContextBuilder(_make_ctx())

        result = cb._build_mandatory_prompt_payload(
            anti_trope_prompt="anti",
            justification_prompt="just",
            reflexion_prompt="reflect",
        )

        assert result == {
            "anti_trope_prompt": "anti",
            "justification_prompt": "just",
            "reflexion_prompt": "reflect",
        }

    def test_load_reflexion_prompt_returns_empty_before_threshold(self):
        cb = Stage4ContextBuilder(_make_ctx())

        result = cb._load_reflexion_prompt(next_ep=19)

        assert result == ""

    def test_load_reflexion_prompt_uses_manager_after_threshold(self):
        ctx = _make_ctx()
        cb = Stage4ContextBuilder(ctx)
        reflexion_manager = MagicMock()
        reflexion_manager.get_prompt_injection.return_value = "reflect"

        with patch("modules.core.reflexion_manager.ReflexionManager", return_value=reflexion_manager):
            result = cb._load_reflexion_prompt(next_ep=20)

        assert result == "reflect"
        reflexion_manager.get_prompt_injection.assert_called_once_with(min_frequency=2)

    @patch("modules.core.stage4_context_builder._build_justification", return_value="just")
    @patch("modules.core.stage4_context_builder._build_anti_trope", return_value="anti")
    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_returns_dict_with_expected_keys(self, *_mocks):
        cb = Stage4ContextBuilder(_make_ctx())
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="전술",
            prev_text="이전 원고 " * 30,
            prev_ending="엔딩",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        assert set(result.keys()) == {
            "reference_anchor_prompt",
            "mandatory_context",
            "anti_trope_prompt",
            "justification_prompt",
            "reflexion_prompt",
        }
        assert "writer mandatory" in result["mandatory_context"]

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="")
    def test_build_mandatory_context_injects_series_summary_once(self, _mock_build):
        ctx = _make_ctx()

        def _load_v20_anchor(key, default=None):
            if key == "series_summary":
                return {"summary": "시리즈 요약 본문이 충분히 길다"}
            return default

        ctx.current_project.load_v20_anchor.side_effect = _load_v20_anchor
        ctx.load_narrative_summaries = MagicMock(
            return_value="### 📚 장기 내러티브 요약 (과거 스토리)\n[제1-4화 요약] 별도 요약"
        )
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="전술",
            prev_text="",
            prev_ending="",
            hud_report="",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="fantasy",
            blueprint={},
            v50_modules_available=False,
        )

        assert result["mandatory_context"].count("시리즈 요약 본문이 충분히 길다") == 1

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_build_mandatory_context_includes_stage2_failure_context(self, *_mocks):
        ctx = _make_ctx()
        ctx.current_project.db.get_stage_attempts_for_arc = MagicMock(
            return_value=[
                {
                    "verdict": "REJECT",
                    "failure_category": "continuity",
                    "reject_reason": "timeline.start/end 불일치",
                },
                {
                    "verdict": "PASS_WITH_FIX",
                    "failure_category": "schema",
                    "reject_reason": "npc_deaths 타입 보정",
                    "verdict_reason": "Keep the prior episode state intact.",
                    "runtime_advisory": "[Advisory digest] keep chronology visible.",
                    "retry_directives": "Avoid repeating the prior ending beat.",
                },
            ]
        )
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 3, "state_changes": {}},
            arc_tactical="arc tactical",
            prev_text="prev text",
            prev_ending="prev ending",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        assert "[Stage 2 실패/보정 이력]" in result["mandatory_context"]
        assert "continuity(1)" in result["mandatory_context"]
        assert "timeline.start/end 불일치" in result["mandatory_context"]
        assert "대표 보정/재시도 지시:" in result["mandatory_context"]
        assert "keep chronology visible." in result["mandatory_context"]
        assert "Avoid repeating the prior ending beat." in result["mandatory_context"]
        ctx.current_project.db.get_stage_attempts_for_arc.assert_called_once_with(3, stages=(2,), limit=12)

    @patch("modules.core.stage4_context_builder._build_justification", return_value="just")
    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_writer_guidance_is_injected_into_live_prompt_path(self, *_mocks):
        ctx = _make_ctx()
        ctx.generate_writer_guidance_v60_8 = MagicMock(return_value="high impact guidance")
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="전술",
            prev_text="이전 원고 " * 30,
            prev_ending="엔딩",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
            blueprint={"scene_breakdown": {}},
        )

        ctx.generate_writer_guidance_v60_8.assert_called_once()
        assert "[Writer Guidance]" in result["justification_prompt"]
        assert "high impact guidance" in result["justification_prompt"]

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_build_mandatory_context_records_hud_anomaly_on_dashboard(self, _mock_build):
        ctx = _make_ctx()
        ctx.quality_dashboard = MagicMock()
        ctx.current_project.db.get_manuscript.side_effect = [
            {"hud_snapshot": {"internal_energy": 100, "realm": "삼류"}},
            {"hud_snapshot": {"internal_energy": 100, "realm": "삼류"}},
            {"hud_snapshot": {"internal_energy": 700, "realm": "삼류"}},
        ]
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="전술",
            prev_text="이전 원고",
            prev_ending="엔딩",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        ctx.quality_dashboard.record_hud_anomaly.assert_called_once()
        kwargs = ctx.quality_dashboard.record_hud_anomaly.call_args.kwargs
        assert kwargs["ep_num"] == 5
        assert kwargs["anomalies"][0]["type"] == "내공 급상승"

    def test_pacing_analyzer_param_used(self):
        cb = Stage4ContextBuilder(_make_ctx())
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []
        mock_pacing = MagicMock()
        mock_pacing.generate_pacing_prompt.return_value = "페이싱 프롬프트"

        cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="",
            prev_text="이전 원고 " * 40,
            prev_ending="엔딩",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
            pacing_analyzer=mock_pacing,
        )

        mock_pacing.analyze.assert_called_once()
        mock_pacing.generate_pacing_prompt.assert_called_once()

    def test_semantic_plot_guard_uses_ctx(self):
        ctx = _make_ctx()
        ctx.semantic_plot_guard = MagicMock()
        ctx.semantic_plot_guard.check_new_arc.return_value = ["warn"]
        ctx.semantic_plot_guard.format_warnings.return_value = "spg warning"
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1, "tactical_doc": "전술"},
            arc_tactical="",
            prev_text="x" * 200,
            prev_ending="엔딩",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        ctx.semantic_plot_guard.check_new_arc.assert_called_once()
        assert "spg warning" in result["mandatory_context"]

    def test_build_mandatory_context_does_not_touch_self_app(self):
        ctx = _make_ctx()
        ctx.semantic_plot_guard = MagicMock()
        ctx.semantic_plot_guard.check_new_arc.return_value = ["warn"]
        ctx.semantic_plot_guard.format_warnings.return_value = "spg warning"
        cb = _AppTrapContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1, "tactical_doc": "tactical note"},
            arc_tactical="",
            prev_text="x" * 200,
            prev_ending="ending beat",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        assert "spg warning" in result["mandatory_context"]

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_falls_back_to_legacy_vector_path_without_advisor(self, *_mocks):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = "legacy vector block"
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1, "state_changes": {"npc_deaths": ["alice"]}},
            arc_tactical="arc tactical text " * 10,
            prev_text="x" * 200,
            prev_ending="ending context",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        assert "legacy vector block" in result["mandatory_context"]
        ctx.memory.retrieve_multi_query_context.assert_called()

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_includes_genre_specific_state_tracker_summaries(self, *_mocks):
        ctx = _make_ctx()
        ctx.state_tracker = MagicMock()
        ctx.state_tracker.get_all_summaries.return_value = {
            "dungeon_clear": "[던전 클리어 기록]\n- 붉은 던전 (클리어 ep12)",
            "skill_cooldown": "[스킬 쿨다운/사용 이력]\n- 연속베기 (쿨다운 2턴)",
        }
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="전술",
            prev_text="이전 원고 " * 30,
            prev_ending="엔딩",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="hunter",
            v50_modules_available=False,
        )

        ctx.state_tracker.get_all_summaries.assert_called_once_with(arc_no=1, genre="hunter")
        assert "[던전 클리어 기록]" in result["mandatory_context"]
        assert "[스킬 쿨다운/사용 이력]" in result["mandatory_context"]

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_suppresses_overlapping_state_tracker_summaries_when_canonical_layers_exist(self, *_mocks):
        ctx = _make_ctx()
        ctx.world_state = MagicMock()
        ctx.world_state.get_summary.return_value = "[세계 상태 요약]"
        ctx.world_state.get_timeline_summary.return_value = "[타임라인 요약]"
        ctx.world_state.get_canonical_constraints.return_value = "[Canonical NPC]"
        ctx.fact_ledger = MagicMock()
        ctx.fact_ledger.to_summary.return_value = "[팩트 원장 요약]"
        ctx.fact_ledger.get_canonical_summary.return_value = "[Canonical Number]"
        ctx.state_tracker = MagicMock()
        ctx.state_tracker.get_all_summaries.return_value = {
            "dead_npc": "[사망 NPC]\n- 장천",
            "item_state": "[아이템 상태]\n- 흑검",
            "relationship_changes": "[관계 변화]\n- 장천/소연 적대",
            "financial_state": "[금융 상태]\n- 자본금 10억",
            "entity_destruction": "[파괴 엔티티]\n- 흑풍회 본부 붕괴",
        }
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="전술",
            prev_text="이전 원고 " * 30,
            prev_ending="엔딩",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="investment",
            v50_modules_available=False,
        )

        text = result["mandatory_context"]
        assert "[Authority precedence]" in text
        assert "WorldState current-state facts override extracted or advisory summaries on conflict." in text
        assert "FactLedger numeric facts override BI seed numbers and arc-derived summaries on conflict." in text
        assert "[파괴 엔티티]" in text
        assert "[사망 NPC]" not in text
        assert "[아이템 상태]" not in text
        assert "[관계 변화]" not in text
        assert "[금융 상태]" not in text

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_injects_authority_precedence_when_canonical_layers_exist_without_state_tracker_overlap(self, *_mocks):
        ctx = _make_ctx()
        ctx.world_state = MagicMock()
        ctx.world_state.get_summary.return_value = ""
        ctx.world_state.get_timeline_summary.return_value = ""
        ctx.world_state.get_canonical_constraints.return_value = "[Canonical NPC]"
        ctx.fact_ledger = MagicMock()
        ctx.fact_ledger.to_summary.return_value = ""
        ctx.fact_ledger.get_canonical_summary.return_value = "[Canonical Number]"
        ctx.state_tracker = MagicMock()
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="tactical summary",
            prev_text="previous episode " * 30,
            prev_ending="ending",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        text = result["mandatory_context"]
        assert "[Authority precedence]" in text
        assert "WorldState current-state facts override extracted or advisory summaries on conflict." in text
        assert "FactLedger numeric facts override BI seed numbers and arc-derived summaries on conflict." in text
        assert "[Canonical NPC]" in text
        assert "[Canonical Number]" in text

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_wuxia_technique_realm_authority_injected_when_skills_exist(self, *_mocks):
        """[Wave-TR1] 무협 장르 + 주인공 기술 존재 시 경지/기술 권위 문구 주입."""
        ctx = _make_ctx()
        ctx.current_project.genre = {"name": "무협"}
        ctx.world_state = MagicMock()
        ctx.world_state._state = {"protagonist": {"skills": ["검기", "장풍"]}}
        ctx.world_state.get_summary.return_value = ""
        ctx.world_state.get_timeline_summary.return_value = ""
        ctx.world_state.get_canonical_constraints.return_value = ""
        ctx.fact_ledger = None
        ctx.state_tracker = MagicMock()
        ctx.state_tracker.get_all_summaries.return_value = {}
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="tactical",
            prev_text="prev " * 30,
            prev_ending="ending",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        text = result["mandatory_context"]
        assert "[무협 기술/경지 권위]" in text
        assert "경지에서 허용되지 않는 기술" in text

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_wuxia_technique_realm_authority_absent_for_non_wuxia(self, *_mocks):
        """[Wave-TR1] 비무협 장르에서는 경지/기술 권위 문구 미주입."""
        ctx = _make_ctx()
        ctx.current_project.genre = {"name": "현대판타지"}
        ctx.world_state = MagicMock()
        ctx.world_state._state = {"protagonist": {"skills": ["마법탄", "텔레키네시스"]}}
        ctx.world_state.get_summary.return_value = ""
        ctx.world_state.get_timeline_summary.return_value = ""
        ctx.world_state.get_canonical_constraints.return_value = ""
        ctx.state_tracker = MagicMock()
        ctx.state_tracker.get_all_summaries.return_value = {}
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="tactical",
            prev_text="prev " * 30,
            prev_ending="ending",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="fantasy",
            v50_modules_available=False,
        )

        text = result["mandatory_context"]
        assert "[무협 기술/경지 권위]" not in text

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_wuxia_technique_realm_authority_absent_when_no_skills(self, *_mocks):
        """[Wave-TR1] 무협이어도 기술 목록 비어있으면 미주입."""
        ctx = _make_ctx()
        ctx.current_project.genre = {"name": "무협"}
        ctx.world_state = MagicMock()
        ctx.world_state._state = {"protagonist": {"skills": []}}
        ctx.world_state.get_summary.return_value = ""
        ctx.world_state.get_timeline_summary.return_value = ""
        ctx.world_state.get_canonical_constraints.return_value = ""
        ctx.state_tracker = MagicMock()
        ctx.state_tracker.get_all_summaries.return_value = {}
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="tactical",
            prev_text="prev " * 30,
            prev_ending="ending",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        text = result["mandatory_context"]
        assert "[무협 기술/경지 권위]" not in text

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_keeps_state_tracker_summaries_when_no_canonical_layers_exist(self, *_mocks):
        ctx = _make_ctx()
        ctx.state_tracker = MagicMock()
        ctx.state_tracker.get_all_summaries.return_value = {
            "dead_npc": "[사망 NPC]\n- 장천",
            "item_state": "[아이템 상태]\n- 흑검",
        }
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={"arc_no": 1},
            arc_tactical="전술",
            prev_text="이전 원고 " * 30,
            prev_ending="엔딩",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        text = result["mandatory_context"]
        assert "[Authority precedence]" not in text
        assert "[사망 NPC]" in text
        assert "[아이템 상태]" in text

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_condensed_world_state_summary_keeps_active_pressure_vectors(self, *_mocks):
        ctx = _make_ctx()
        ctx.world_state = MagicMock()
        ctx.world_state._state = {
            "last_updated_ep": 8,
            "protagonist": {"name": "서진우", "location": "지하실"},
            "active_pressure_vectors": [
                {"text": "해독제를 찾지 못하면 독이 전신으로 퍼진다.", "since_ep": 8},
                {"text": "추격대가 문 앞까지 도착했다.", "since_ep": 8},
            ],
        }
        ctx.world_state.get_summary.return_value = "[fallback world state]"
        ctx.world_state.get_timeline_summary.return_value = ""
        ctx.world_state.get_canonical_constraints.return_value = ""
        ctx.state_tracker = MagicMock()
        ctx.state_tracker.get_all_summaries.return_value = {}
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=9,
            blueprint={"scene_breakdown": [{"npcs": ["장천"]}]},
            arc_data={"arc_no": 2, "state_changes": {"npc_deaths": ["장천"]}},
            arc_tactical="전술",
            prev_text="이전 원고 " * 30,
            prev_ending="엔딩",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        assert "[지속 압박/위협]" in result["mandatory_context"]
        assert "해독제를 찾지 못하면 독이 전신으로 퍼진다." in result["mandatory_context"]

    def test_condensed_world_state_summary_preserves_recent_pressure_tail(self):
        ctx = _make_ctx()
        ctx.world_state = MagicMock()
        ctx.world_state._state = {
            "last_updated_ep": 8,
            "protagonist": {"name": "서진우", "location": "지하실"},
            "active_pressure_vectors": [{"text": "PRESSURE-HEAD\n" + ("P" * 220) + "\nTAIL-PRESSURE"}],
            "alive_npcs": {},
            "active_items": {},
            "active_plots": [],
        }
        cb = Stage4ContextBuilder(ctx)

        summary = cb.context_packets.build_condensed_world_state_summary(
            {"npcs": ["장천"], "items": [], "plots": [], "locations": []},
            max_chars=180,
        )

        assert len(summary) <= 180
        assert "TAIL-PRESSURE" in summary

    def test_build_condensed_world_state_summary_delegates_to_context_packets(self):
        cb = Stage4ContextBuilder(_make_ctx())
        cb.context_packets.build_condensed_world_state_summary = MagicMock(return_value="summary")

        result = cb.context_packets.build_condensed_world_state_summary(
            {"npcs": ["장천"], "items": [], "plots": [], "locations": []},
            max_chars=180,
        )

        assert result == "summary"
        cb.context_packets.build_condensed_world_state_summary.assert_called_once()

    def test_build_condensed_world_state_header_sections_includes_core_headers(self):
        cb = Stage4ContextBuilder(_make_ctx())

        parts = cb.context_packets._build_condensed_world_state_header_sections(
            state={
                "last_updated_ep": 9,
                "protagonist": {
                    "name": "lead",
                    "location": "seoul tower",
                    "assets": "equity portfolio",
                    "injuries": "arm fracture",
                },
                "motivations": [{"status": "active", "text": "protect the fund", "since_ep": 7}],
                "promises": [
                    {
                        "promiser": "lead",
                        "promisee": "ally",
                        "text": "keep the secret",
                        "status": "pending",
                        "since_ep": 8,
                    }
                ],
                "cumulative_elapsed": {"total_days": 12},
            }
        )

        text = "\n\n".join(parts)
        assert "=== 세계 상태 (제9화 기준) ===" in text
        assert "[주인공]" in text
        assert "부상: arm fracture" in text
        assert "[주인공 핵심 동기]" in text
        assert "lead→ally: keep the secret (제8화~)" in text
        assert "[누적 경과] 총 12일" in text

    def test_build_condensed_world_state_registry_sections_skips_cp_entities(self):
        cb = Stage4ContextBuilder(_make_ctx())

        parts = cb.context_packets._build_condensed_world_state_registry_sections(
            state={
                "alive_npcs": {
                    "focus": {"role": "mentor", "relation": "ally", "location": "tower"},
                    "side": {"role": "broker", "relation": "neutral", "location": "office"},
                },
                "dead_npcs": {"ghost": {"ep": 4, "cause": "duel"}},
                "relationships": {"focus": "bond", "side": "tense"},
                "active_items": {"ledger": {}, "seal": {}},
                "active_plots": [{"plot": "focus plot", "since_ep": 6}, {"plot": "side plot", "since_ep": 7}],
            },
            cp_npcs={"focus"},
            cp_items={"ledger"},
            cp_plots={"focus plot"},
        )

        text = "\n\n".join(parts)
        assert "focus" not in text or "핵심 NPC 상세는 Continuity Packet 참조" in text
        assert "- side: broker / 관계=neutral / 위치=office" in text
        assert "[사망 NPC - CP 비포함 1명]" in text
        assert "- side: tense" in text
        assert "[보유 아이템 - CP 비포함]" in text and "- seal" in text
        assert "[진행 중 플롯 - CP 비포함]" in text and "side plot" in text

    def test_build_condensed_world_state_tail_sections_includes_pressure_and_location_reference(self):
        cb = Stage4ContextBuilder(_make_ctx())

        parts = cb.context_packets._build_condensed_world_state_tail_sections(
            state={"active_pressure_vectors": [{"text": "HEAD\n" + ("P" * 120) + "\nTAIL"}]},
            cp_locations={"hq"},
        )

        text = "\n\n".join(parts)
        assert "[지속 압박/위협]" in text
        assert "TAIL" in text
        assert "이번 화 위치 맥락 상세는 Continuity Packet 참조" in text

    def test_condensed_fact_ledger_summary_preserves_recent_tail(self):
        ctx = _make_ctx()
        ctx.fact_ledger = MagicMock()
        ctx.fact_ledger._ledger = {
            "last_updated_ep": 12,
            "characters": {},
            "items": {},
            "numbers": {
                "자본금": {
                    "value": "10억",
                    "unit": "원",
                    "last_ep": 12,
                },
                "긴수치": {
                    "value": "HEAD-NUM\n" + ("N" * 220) + "\nTAIL-NUM",
                    "unit": "",
                    "last_ep": 12,
                },
            },
        }
        cb = Stage4ContextBuilder(ctx)

        summary = cb.context_packets.build_condensed_fact_ledger_summary(
            {"npcs": ["dummy"], "items": [], "plots": [], "locations": [], "_full_text": ""},
            max_chars=180,
        )

        assert len(summary) <= 180
        assert "TAIL-NUM" in summary

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_uses_advisor_retrieval_plan_when_available(self, *_mocks):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = "vec hit"
        ctx.memory.retrieve_hybrid_context.return_value = "vec hit"
        ctx.memory.retrieve_npc_context.return_value = "npc hit"
        ctx.context_advisor = MagicMock()
        ctx.context_advisor.plan_stage4_retrieval.return_value = RetrievalPlan(
            stage="stage4",
            episode_num=7,
            slots=[
                RetrievalSlot(category="scene_context", query="scene query", source="vec_memory", priority=1),
                RetrievalSlot(category="npc_history", query="alice bob", source="db_npc_history", priority=1),
            ],
            total_budget_chars=1200,
        )
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage4_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            return default

        with patch("modules.core.stage4_context_builder._threshold", side_effect=threshold_side_effect):
            result = cb.build_mandatory_context(
                next_ep=7,
                arc_data={"arc_no": 1, "ep_start": 1, "ep_count": 10},
                arc_tactical="arc tactical",
                prev_text="x" * 200,
                prev_ending="ending context",
                hud_report="HUD",
                writer_agent=MagicMock(),
                anchor_sys=anchor_sys,
                s4_genre_type="wuxia",
                v50_modules_available=False,
            )

        ctx.context_advisor.plan_stage4_retrieval.assert_called_once()
        assert (ctx.memory.retrieve_hybrid_context.call_count + ctx.memory.retrieve_multi_query_context.call_count) == 1
        ctx.memory.retrieve_npc_context.assert_called_once()
        assert "[SC:scene_context]" in result["mandatory_context"]
        assert "[SC:npc_history]" in result["mandatory_context"]

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_build_mandatory_context_passes_work_focus_to_stage4_planner(self, _mock_build):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.context_advisor = MagicMock()
        ctx.sys.guard = MagicMock()
        ctx.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["소꿉친구 관계선"],
            "mandatory_scene_engines": ["관계 반전"],
            "registry_profiles": [{"name": "relationship_registry", "purpose": "오래된 인연 추적"}],
        }
        ctx.context_advisor.plan_stage4_retrieval.return_value = RetrievalPlan(
            stage="stage4",
            episode_num=7,
            slots=[
                RetrievalSlot(category="scene_context", query="장면1: 재회", source=RetrievalSources.STATIC, priority=1)
            ],
            total_budget_chars=1200,
        )
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage4_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            return default

        with patch("modules.core.stage4_context_builder._threshold", side_effect=threshold_side_effect):
            cb.build_mandatory_context(
                next_ep=7,
                arc_data={"arc_no": 1, "ep_start": 1, "ep_count": 10},
                arc_tactical="소꿉친구 라인 재등장",
                prev_text="x" * 200,
                prev_ending="연홍과의 관계가 흔들렸다",
                hud_report="HUD",
                writer_agent=MagicMock(),
                anchor_sys=anchor_sys,
                s4_genre_type="wuxia",
                v50_modules_available=False,
            )

        planner_kwargs = ctx.context_advisor.plan_stage4_retrieval.call_args.kwargs
        assert planner_kwargs["work_focus"]["tracking_slots"] == ["소꿉친구 관계선"]
        assert planner_kwargs["work_focus"]["mandatory_scene_engines"] == ["관계 반전"]

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_build_mandatory_context_orders_tiers_truth_then_retrieval_then_bulk(self, _mock_build):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.context_advisor = MagicMock()
        ctx.sys.guard = MagicMock()
        ctx.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["핵심 배우 라인"],
            "mandatory_scene_engines": ["관계 반전"],
            "registry_profiles": [],
        }
        ctx.context_advisor.plan_stage4_retrieval.return_value = RetrievalPlan(
            stage="stage4",
            episode_num=7,
            slots=[
                RetrievalSlot(
                    category="work_tracking_slot_1",
                    query="stage4 작품 tracking slot 핵심 상태/최근 변화: 핵심 배우 라인",
                    source=RetrievalSources.STATIC,
                    priority=1,
                ),
                RetrievalSlot(
                    category="scene_context", query="장면1: 재회", source=RetrievalSources.STATIC, priority=1
                ),
            ],
            total_budget_chars=1200,
        )
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage4_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            return default

        with (
            patch("modules.core.stage4_context_builder._threshold", side_effect=threshold_side_effect),
            patch.object(cb, "build_extended_lookback_digest", return_value="[확장 Lookback]\nLOOKBACK"),
            patch.object(cb, "_build_future_arc_context", return_value="[미래 Arc]\nFUTURE"),
        ):
            result = cb.build_mandatory_context(
                next_ep=7,
                arc_data={"arc_no": 1, "ep_start": 1, "ep_count": 10},
                arc_tactical="핵심 배우 라인 재정비",
                prev_text="x" * 200,
                prev_ending="캐스팅 갈등이 남았다",
                hud_report="HUD",
                writer_agent=MagicMock(),
                anchor_sys=anchor_sys,
                s4_genre_type="investment",
                v50_modules_available=False,
            )

        text = result["mandatory_context"]
        assert text.index("writer mandatory") < text.index("[작품 추적 슬롯 요약]")
        assert text.index("[작품 추적 슬롯 요약]") < text.index("[SC:work_tracking_slot_1]")
        assert text.index("[SC:scene_context]") < text.index("LOOKBACK")

    def test_execute_retrieval_plan_respects_slot_max_chars(self):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = "x" * 1200
        cb = Stage4ContextBuilder(ctx)
        plan = RetrievalPlan(
            stage="stage4",
            episode_num=3,
            slots=[RetrievalSlot(category="long_slot", query="query", source="vec_memory", max_chars=80)],
            total_budget_chars=1000,
        )

        sections = cb._execute_retrieval_plan(plan)

        assert len(sections) == 1
        raw_len = len("[SC:long_slot]\n" + ("x" * 1200))
        assert len(sections[0]) < raw_len

    def test_apply_context_budget_logs_and_trims(self, caplog):
        cb = Stage4ContextBuilder(_make_ctx())
        original_sections = ["a" * 1200, "b" * 1200]

        with caplog.at_level("INFO"):
            trimmed_sections = cb._apply_context_budget(original_sections, total_budget_chars=500)

        assert sum(len(s) for s in trimmed_sections) < 2400
        assert any("[SC] Context budget:" in rec.message for rec in caplog.records)

    def test_apply_context_budget_prefers_preserving_work_slot_summary(self, caplog):
        cb = Stage4ContextBuilder(_make_ctx())
        slot_summary = "[작품 추적 슬롯 요약]\n" + ("slot " * 180)
        generic_block = "[기타 요약]\n" + ("generic " * 220)

        with caplog.at_level("INFO"):
            trimmed_sections = cb._apply_context_budget([slot_summary, generic_block], total_budget_chars=1000)

        assert trimmed_sections[0].startswith("[작품 추적 슬롯 요약]")
        assert len(trimmed_sections[0]) > len(trimmed_sections[1])
        assert any("[SC:TRIM:PROTECTED]" in rec.message for rec in caplog.records)

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="")
    def test_build_mandatory_context_rebalances_sc_and_mc_with_headroom(self, _mock_build, caplog):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = "S" * 320
        ctx.context_advisor = MagicMock()
        ctx.context_advisor.plan_stage4_retrieval.return_value = RetrievalPlan(
            stage="stage4",
            episode_num=7,
            slots=[RetrievalSlot(category="scene_context", query="scene query", source="vec_memory", priority=1)],
            total_budget_chars=320,
        )
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage4_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            if key == "context.mandatory_context_max":
                return 500
            return default

        with (
            patch("modules.core.stage4_context_builder._threshold", side_effect=threshold_side_effect),
            patch.object(cb, "_build_future_arc_context", return_value="M" * 420),
            caplog.at_level("INFO"),
        ):
            result = cb.build_mandatory_context(
                next_ep=7,
                arc_data={"arc_no": 1, "ep_start": 1, "ep_count": 10},
                arc_tactical="arc tactical",
                prev_text="x" * 200,
                prev_ending="ending context",
                hud_report="HUD",
                writer_agent=MagicMock(),
                anchor_sys=anchor_sys,
                s4_genre_type="wuxia",
                v50_modules_available=False,
            )

        assert len(result["mandatory_context"]) <= 500
        assert any("[S4:CTX] compose pre-final" in rec.message for rec in caplog.records)
        assert ctx._stage4_context_budget_meta["budget_ledger"]["budget_bucket"] == "context.mandatory_context_max"
        assert ctx._stage4_context_budget_meta["budget_ledger"]["effective_cap"] == 500

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_build_mandatory_context_injects_work_tracking_slot_summary(self, _mock_build):
        ctx = _make_ctx()
        ctx.sys.guard = MagicMock()
        ctx.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["핵심 배우 라인"],
            "mandatory_scene_engines": ["인재 발굴"],
            "registry_profiles": [
                {"name": "talent_registry", "required_fields": ["name", "tier", "risk"]},
            ],
        }
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=7,
            arc_data={"arc_no": 1, "constraint_summary": "배우 라인 재정비와 팬덤 반응 회수"},
            arc_tactical="캐스팅 재정비",
            prev_text="이전 화 원고",
            prev_ending="팬덤 반응과 캐스팅 갈등이 남았다",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="investment",
            v50_modules_available=False,
            blueprint={"summary": "핵심 배우 라인 중심으로 재정비한다."},
        )

        assert "[작품 추적 슬롯 요약]" in result["mandatory_context"]
        assert "핵심 배우 라인" in result["mandatory_context"]
        assert "talent_registry" in result["mandatory_context"]

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_build_mandatory_context_promotes_work_identity_authority_packet(self, _mock_build):
        ctx = _make_ctx()
        ctx.sys.guard = MagicMock()
        ctx.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["lead actor line"],
            "mandatory_scene_engines": ["contract payoff"],
            "registry_profiles": [
                {"name": "talent_registry", "required_fields": ["name", "tier", "risk"], "purpose": "cast gating"},
            ],
        }
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=7,
            arc_data={"arc_no": 1, "constraint_summary": "Keep the contract payoff attached to the actor line."},
            arc_tactical="Preserve the actor line and pay it off in the negotiation.",
            prev_text="previous manuscript body",
            prev_ending="the deal remains unresolved",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="investment",
            v50_modules_available=False,
            blueprint={"summary": "The lead actor line is the active commercial spine."},
        )

        text = result["mandatory_context"]
        assert "[Stage4 Work Identity Authority]" in text
        assert "tracking_slots MUST survive into scene execution: lead actor line" in text
        assert "mandatory_scene_engines MUST appear on-page: contract payoff" in text
        assert "talent_registry" in text
        assert text.index("[Stage4 Work Identity Authority]") < text.index("[작품 추적 슬롯 요약]")

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_build_mandatory_context_promotes_opening_scene_authority_even_without_work_focus(self, _mock_build):
        ctx = _make_ctx()
        ctx.sys.guard = MagicMock()
        ctx.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": [],
            "mandatory_scene_engines": [],
            "registry_profiles": [],
        }
        ctx.current_project.db.load_anchor.return_value = {
            "cliffhanger": "전화가 오기 직전 멈칫했다.",
            "pending_actions": ["전화를 받기", "현관으로 이동하기"],
            "location": "서재 앞 복도",
            "time_marker": "직후",
        }
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=2,
            arc_data={"arc_no": 1, "constraint_summary": "Preserve EP1→EP2 opening continuity."},
            arc_tactical="Carry the hallway-to-entrance motion forward without resetting space.",
            prev_text="이전 화 원고",
            prev_ending="서재 앞 복도에서 현관 쪽으로 발을 옮겼다.",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="investment",
            v50_modules_available=False,
            blueprint={
                "start_location": "서재 앞 복도",
                "time_flow": "직후",
                "scene_breakdown": {
                    "scene_1": {
                        "title": "복도에서 현관으로",
                        "location": "현관 방향 복도",
                    }
                },
            },
        )

        text = result["mandatory_context"]
        assert "[Stage4 Opening Scene Authority]" in text
        assert "opening start_location MUST be preserved: 서재 앞 복도" in text
        assert "opening carryover location to honor or explicitly transition from: 서재 앞 복도" in text
        assert "opening carryover time_marker to honor or explicitly advance from: 직후" in text
        assert (
            "opening carryover pending_actions to resolve before new thread or explicitly transition away: "
            "전화를 받기, 현관으로 이동하기"
        ) in text
        assert "do not replay a completed prior-episode event in the opening." in text
        assert "use either an explicit transition sentence or a scene-break marker `* * *` first." in text
        assert "the first 1-2 sentences after it must state the changed location, time, or action state." in text
        assert text.index("[Stage4 Opening Scene Authority]") < text.index("[Stage4 Work Identity Authority]")

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_build_mandatory_context_injects_semantic_relation_slice_when_focus_requires_it(self, _mock_build):
        ctx = _make_ctx()
        ctx.quality_dashboard = MagicMock()
        ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {"name": "주인공"}}}
        ctx.sys.guard = MagicMock()
        ctx.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["소꿉친구 라인"],
            "mandatory_scene_engines": [],
            "registry_profiles": [],
        }
        ctx.world_state = MagicMock()
        ctx.world_state.get_state_dict.return_value = {
            "protagonist": {"name": "주인공"},
            "relationships": {"연홍": "죽마고우"},
            "alive_npcs": {
                "연홍": {
                    "relation": "신뢰",
                    "known_attrs": {"relation_to_protag": {"value": "어릴 때부터 함께 자란 친구"}},
                }
            },
        }
        ctx.world_state.get_summary.return_value = ""
        ctx.world_state.get_canonical_constraints.return_value = ""
        ctx.world_state.get_timeline_summary.return_value = ""
        ctx.fact_ledger = MagicMock()
        ctx.fact_ledger._ledger = {
            "characters": {
                "연홍": {
                    "relationship": "소꿉친구",
                    "established_ep": 3,
                    "history": ["ep3: 어릴 때부터 함께 자람"],
                }
            }
        }
        ctx.fact_ledger.to_summary.return_value = ""
        ctx.fact_ledger.get_canonical_summary.return_value = ""
        ctx.current_project.db.get_npc_relationship_edges.return_value = [
            {"npc1": "주인공", "npc2": "연홍", "relation": "신뢰", "updated_ep": 12}
        ]
        ctx.current_project.db.get_relationship_history.return_value = [
            {"old_relation": "중립", "new_relation": "죽마고우", "change_ep": 5}
        ]
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        result = cb.build_mandatory_context(
            next_ep=7,
            arc_data={"arc_no": 1, "constraint_summary": "연홍과의 소꿉친구 라인 회수"},
            arc_tactical="소꿉친구 라인 재등장",
            prev_text="이전 화 원고",
            prev_ending="연홍과의 과거 인연을 다시 꺼낼 필요가 남았다",
            hud_report="HUD",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="investment",
            v50_modules_available=False,
            blueprint={"summary": "연홍이 주인공의 소꿉친구로 다시 부각된다."},
        )

        ctx.quality_dashboard.record_retrieval_observation.assert_called_once()
        kwargs = ctx.quality_dashboard.record_retrieval_observation.call_args.kwargs
        assert kwargs["stage"] == "stage4"
        assert kwargs["observation"]["relation_slice_included"] is True
        assert kwargs["observation"]["provenance_ledger"]["source_pack"] == "stage4"
        assert kwargs["observation"]["budget_ledger"]["budget_bucket"] == "context.mandatory_context_max"
        assert "[관계 의미 질의]" in result["mandatory_context"]
        assert "연홍" in result["mandatory_context"]

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_build_mandatory_context_surfaces_retrieval_coverage_warnings(self, _mock_build):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.db = MagicMock()
        ctx.db.get_relationship_history.return_value = []
        ctx.sys.guard = MagicMock()
        ctx.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["소꿉친구 라인"],
            "mandatory_scene_engines": [],
            "registry_profiles": [],
        }
        ctx.context_advisor = MagicMock()
        ctx.context_advisor.plan_stage4_retrieval.return_value = RetrievalPlan(
            stage="stage4",
            episode_num=7,
            slots=[
                RetrievalSlot(
                    category="work_relationship_context",
                    query="관계 변화 이력: 주인공, 연홍",
                    source=RetrievalSources.DB_NPC_RELATIONSHIP,
                    priority=1,
                )
            ],
            total_budget_chars=1200,
        )
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage4_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            return default

        with (
            patch("modules.core.stage4_context_builder._threshold", side_effect=threshold_side_effect),
            patch("modules.core.stage4_context_builder.SemanticQueryBroker") as broker_cls,
        ):
            broker_cls.return_value.build_stage4_relation_slice.return_value = ""
            result = cb.build_mandatory_context(
                next_ep=7,
                arc_data={"arc_no": 1, "constraint_summary": "연홍과의 관계 회수"},
                arc_tactical="소꿉친구 라인 회수",
                prev_text="이전 화 원고",
                prev_ending="연홍과의 인연을 다시 드러낼 필요가 남았다",
                hud_report="HUD",
                writer_agent=MagicMock(),
                anchor_sys=anchor_sys,
                s4_genre_type="investment",
                v50_modules_available=False,
                blueprint={"summary": "연홍과의 관계 축을 회수한다."},
            )

        assert "[검색 커버리지 경고]" in result["mandatory_context"]
        assert "관계 의미 질의가 빠졌다." in result["mandatory_context"]
        assert not result["mandatory_context"].startswith("[검색 커버리지 경고]")

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_build_mandatory_context_fallback_queries_preserve_tactical_tail_context(self, _mock_build):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = ""
        ctx.context_advisor = None
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return False
            if key == "smart_retrieval.stage4_enabled":
                return False
            if key == "context.vector_max_results_s4":
                return 16
            return default

        with (
            patch("modules.core.stage4_context_builder._threshold", side_effect=threshold_side_effect),
            patch(
                "modules.core.stage4_context_builder.extract_episode_tactical",
                return_value="HEAD-EP-TAC\n" + ("T" * 2400) + "\nTAIL-EP-TAC",
            ),
        ):
            cb.build_mandatory_context(
                next_ep=7,
                arc_data={"arc_no": 1, "episode_details": [{"ep_num": 7, "details": ["detail"]}]},
                arc_tactical="HEAD-ARC-TAC\n" + ("A" * 2600) + "\nTAIL-ARC-TAC",
                prev_text="이전 원고",
                prev_ending="HEAD-ENDING\n" + ("E" * 200) + "\nTAIL-ENDING",
                hud_report="HUD",
                writer_agent=MagicMock(),
                anchor_sys=anchor_sys,
                s4_genre_type="investment",
                v50_modules_available=False,
                blueprint={},
            )

        queries = ctx.memory.retrieve_multi_query_context.call_args.kwargs["queries"]
        assert any("TAIL-EP-TAC" in query for query in queries)
        assert any("TAIL-ENDING" in query for query in queries)

    @patch("modules.core.stage4_context_builder._build_writer_mandatory_context", return_value="writer mandatory")
    def test_build_mandatory_context_warns_when_semantic_carryover_slot_is_missing(self, _mock_build):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.context_advisor = MagicMock()
        ctx.context_advisor.plan_stage4_retrieval.return_value = RetrievalPlan(
            stage="stage4",
            episode_num=7,
            slots=[
                RetrievalSlot(
                    category="arc_semantic_carryover",
                    query="[Arc Semantic Carryover]\nrelationship Han: Han hides the ledger",
                    source=RetrievalSources.STATIC,
                    priority=1,
                )
            ],
            total_budget_chars=1200,
        )
        cb = Stage4ContextBuilder(ctx)
        anchor_sys = MagicMock()
        anchor_sys.get_relevant_anchors.return_value = []
        anchor_sys.get_critical_anchors.return_value = []

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage4_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            return default

        with (
            patch("modules.core.stage4_context_builder._threshold", side_effect=threshold_side_effect),
            patch.object(cb, "_execute_retrieval_plan", return_value=[]),
        ):
            result = cb.build_mandatory_context(
                next_ep=7,
                arc_data={
                    "arc_no": 1,
                    "ep_start": 1,
                    "ep_count": 10,
                    "semantic_carryover": {"relationship_rationale": []},
                },
                arc_tactical="arc tactical",
                prev_text="x" * 200,
                prev_ending="ending context",
                hud_report="HUD",
                writer_agent=MagicMock(),
                anchor_sys=anchor_sys,
                s4_genre_type="wuxia",
                v50_modules_available=False,
            )

        kwargs = ctx.quality_dashboard.record_retrieval_observation.call_args.kwargs
        assert "missing_semantic_carryover" in kwargs["observation"]["coverage_warnings"]
        assert "[SC:arc_semantic_carryover]" not in result["mandatory_context"]


class TestBuildRoundContext:
    def test_returns_round_context_instance(self):
        cb = Stage4ContextBuilder(_make_ctx())
        ep_ctx = {
            "arc_pos": 1,
            "total_ep_in_arc": 10,
            "arc_tactical": "",
            "prev_text": "",
            "prev_ending": "",
            "prev_manuscripts_text": "",
            "episode_digest": "",
            "hud_report": "",
            "current_inventory": [],
            "current_martial_arts": [],
            "dead_npcs": [],
            "item_acquisition_timeline": "",
            "chain_link_section": "",
            "world_state_summary": "",
        }
        ctx_prompts = {
            "reference_anchor_prompt": "",
            "justification_prompt": "",
            "reflexion_prompt": "",
        }

        result = cb.build_round_context(
            ep_ctx=ep_ctx,
            ctx_prompts=ctx_prompts,
            chief_writer=MagicMock(),
            manuscript_validator=MagicMock(),
            consistency_validator=MagicMock(),
            blocking_validator=MagicMock(),
            continuity_validator=MagicMock(),
            next_ep=1,
            blueprint={},
            arc_data={},
            purism_prompt="",
            genre_name="무협",
            npc_equipment_summary="",
            effective_anti_trope="",
            intro_dna="CYNICAL",
            story_context="",
            style_guide="",
            mandatory_context="",
        )

        assert isinstance(result, _RoundContext)


class TestModuleStructure:
    def test_import(self):
        assert Stage4ContextBuilder is not None

    def test_orchestrator_has_context_builder_property(self):
        assert hasattr(Stage4Orchestrator, "context_builder")

    def test_orchestrator_no_legacy_context_methods(self):
        # Compatibility wrapper is intentionally kept for older call sites.
        assert hasattr(Stage4Orchestrator, "_load_chain_link_section")
        assert not hasattr(Stage4Orchestrator, "_build_extended_lookback_digest")
        assert not hasattr(Stage4Orchestrator, "_prepare_episode_context")
        assert not hasattr(Stage4Orchestrator, "_build_mandatory_context")
        assert not hasattr(Stage4Orchestrator, "_build_round_context")
