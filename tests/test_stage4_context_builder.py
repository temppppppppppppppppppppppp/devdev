"""[B-1-2] Stage4ContextBuilder unit tests."""

import inspect
from unittest.mock import MagicMock, patch

from modules.core.context_advisor import RetrievalPlan, RetrievalSlot
from modules.core.stage4_context_builder import Stage4ContextBuilder
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
    return ctx


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
        ctx.current_project.load_v20_anchor.side_effect = lambda name: {"summary": long_summary} if name == "arc_summary_1" else None
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

    def test_no_self_app_reference_in_source(self):
        source = inspect.getsource(Stage4ContextBuilder.build_mandatory_context)
        assert "self.app" not in source
        assert "self.ctx.semantic_plot_guard" in source

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
    def test_uses_advisor_retrieval_plan_when_available(self, *_mocks):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = "vec hit"
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
        ctx.memory.retrieve_multi_query_context.assert_called_once()
        ctx.memory.retrieve_npc_context.assert_called_once()
        assert "[SC:scene_context]" in result["mandatory_context"]
        assert "[SC:npc_history]" in result["mandatory_context"]

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
        assert "[관계 의미 질의]" in result["mandatory_context"]
        assert "연홍" in result["mandatory_context"]


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
