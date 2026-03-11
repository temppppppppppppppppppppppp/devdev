"""[Phase 4C-1a] Stage3Orchestrator 단위 테스트

추출 대상: _stage_3_batch_blueprinting (main_a.py → stage3_orchestrator.py)
"""

from unittest.mock import MagicMock, patch

import pytest

from modules.core.stage3_context import Stage3Context
from modules.core.stage3_orchestrator import Stage3Orchestrator

# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def app_mock():
    """SovereignApp 모의 객체 — Stage 3에 필요한 최소 인터페이스"""
    app = MagicMock()

    # UI
    app.ui.log = MagicMock()

    # Project
    app.current_project.arcs = [
        {"arc_no": 1, "ep_start": 1, "ep_end": 5, "ep_count": 5, "tactical_doc": "x" * 600, "beat_sequence": [1, 2]},
    ]
    app.current_project.name = "TestProject"
    app.current_project.db.load_anchor.return_value = []
    app.current_project.db.get_latest_blueprint_number.return_value = 0
    app.current_project.db.get_manuscript.return_value = None
    app.current_project.get_blueprint.return_value = None
    app.current_project.master_bible = {"MasterBible": {"protagonist_config": {}}}

    # Agents
    app.agents = {
        "three_phase_bp": MagicMock(),
        "director": MagicMock(),
        "state_extractor": MagicMock(),
    }
    app.agents["three_phase_bp"].generate.return_value = (
        {"integrated_scenario": "test", "scene_breakdown": {"s1": "scene"}},
        {"final_verdict": "PASS", "phases": {"generate": {"selected_strategy": "A", "selected_score": 85}}},
    )
    app.agents["three_phase_bp"].get_stats.return_value = {"pass_rate": "100%"}

    # Config
    app.selected_genre = {"type": "wuxia"}
    app.sys.api_client = MagicMock()
    app.preset_registry = MagicMock()

    # V68 lazy init (already initialized)
    app.state_tracker = MagicMock()
    app.state_tracker.npc_registry = {}
    app.world_state = MagicMock()
    app.fact_ledger = MagicMock()

    # Facade methods
    app._audit_event = MagicMock()
    app._get_int_input.return_value = 5
    app._get_max_episode_from_manuscripts.return_value = 0
    app._get_arc_context_for_episode.return_value = (0, app.current_project.arcs[0])
    app._get_protagonist_name.return_value = "장무기"
    app._fix_entity_registry_protagonist.return_value = {"characters": ["장무기"]}
    app._validate_arc_data_fields.return_value = app.current_project.arcs[0]
    app._validate_blueprint_integrity.return_value = True
    app._safe_commit = MagicMock()
    app._write_audit_summary = MagicMock()

    # Entity cache sentinel (not on app, on orchestrator)

    return app


@pytest.fixture
def orch(app_mock):
    return Stage3Orchestrator(app=app_mock)


# ── Constructor ──────────────────────────────────────────────


class TestConstructor:
    def test_app_reference_stored(self, orch, app_mock):
        assert orch.app is app_mock

    def test_entity_cache_initialized(self, orch):
        assert orch._entity_cache_arc_idx == -1
        assert orch._cached_entity_registry is None


# ── V68 Lazy Init ────────────────────────────────────────────


class TestInitStateTrackerIfNeeded:
    def test_skip_if_already_initialized(self, orch, app_mock):
        """state_tracker가 이미 있으면 재초기화하지 않음"""
        app_mock.state_tracker = MagicMock()
        orch._init_state_tracker_if_needed()
        # Should NOT import StateTracker
        app_mock.current_project.db.load_anchor.assert_not_called()

    def test_creates_when_none_stub(self, orch, app_mock):
        """state_tracker가 None이면 초기화 (stub 호출 확인)"""
        app_mock.state_tracker = None
        with patch("modules.core.stage3_orchestrator.Stage3Orchestrator._init_state_tracker_if_needed") as mock_init:
            mock_init(orch)  # Just verifying it can be called

    def test_creates_when_none(self, app_mock):
        """state_tracker가 None이면 초기화 (실제 StateTracker import를 패치)"""
        app_mock.state_tracker = None
        app_mock.current_project.db.load_anchor.return_value = []
        orch = Stage3Orchestrator(app=app_mock)
        with patch("modules.domain.agents.state_tracker.StateTracker") as MockST:
            mock_st = MagicMock(npc_registry={})
            MockST.return_value = mock_st
            orch._init_state_tracker_if_needed()
        assert app_mock.state_tracker is mock_st


class TestInitWorldStateIfNeeded:
    def test_skip_if_already_initialized(self, orch, app_mock):
        app_mock.world_state = MagicMock()
        orch._init_world_state_if_needed()
        # No error, no new assignment

    def test_creates_when_none(self, orch, app_mock):
        app_mock.world_state = None
        with patch("modules.core.world_state.WorldStateManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.last_updated_ep = 0
            MockWS.return_value = mock_ws
            orch._init_world_state_if_needed()
        assert app_mock.world_state is mock_ws

    def test_failure_is_non_blocking(self, orch, app_mock):
        app_mock.world_state = None
        with patch("modules.core.world_state.WorldStateManager", side_effect=RuntimeError("DB error")):
            orch._init_world_state_if_needed()
        assert app_mock.world_state is None
        app_mock.ui.log.assert_called()


class TestInitFactLedgerIfNeeded:
    def test_skip_if_already_initialized(self, orch, app_mock):
        app_mock.fact_ledger = MagicMock()
        orch._init_fact_ledger_if_needed()

    def test_creates_when_none(self, orch, app_mock):
        app_mock.fact_ledger = None
        with patch("modules.core.fact_ledger.FactLedger") as MockFL:
            mock_fl = MagicMock()
            mock_fl.last_updated_ep = 5
            mock_fl.get_stats.return_value = {"characters": 3, "items": 2}
            MockFL.return_value = mock_fl
            orch._init_fact_ledger_if_needed()
        assert app_mock.fact_ledger is mock_fl

    def test_failure_is_non_blocking(self, orch, app_mock):
        app_mock.fact_ledger = None
        with patch("modules.core.fact_ledger.FactLedger", side_effect=RuntimeError("DB error")):
            orch._init_fact_ledger_if_needed()
        assert app_mock.fact_ledger is None


# ── Entity Registry Cache ────────────────────────────────────


class TestGetEntityRegistry:
    def test_first_call_extracts(self, orch, app_mock):
        app_mock.agents["state_extractor"].extract_cumulative_state.return_value = {
            "entity_registry": {"characters": ["A"]}
        }
        result = orch._get_entity_registry(arc_idx=0)
        assert result is not None
        assert orch._entity_cache_arc_idx == 0

    def test_cached_on_same_arc(self, orch, app_mock):
        # First call
        app_mock.agents["state_extractor"].extract_cumulative_state.return_value = {
            "entity_registry": {"characters": ["A"]}
        }
        orch._get_entity_registry(arc_idx=0)

        # Second call — should use cache
        app_mock.agents["state_extractor"].extract_cumulative_state.reset_mock()
        result = orch._get_entity_registry(arc_idx=0)
        app_mock.agents["state_extractor"].extract_cumulative_state.assert_not_called()

    def test_refreshes_on_new_arc(self, orch, app_mock):
        app_mock.agents["state_extractor"].extract_cumulative_state.return_value = {
            "entity_registry": {"characters": ["A"]}
        }
        orch._get_entity_registry(arc_idx=0)
        orch._get_entity_registry(arc_idx=1)
        assert orch._entity_cache_arc_idx == 1

    def test_failure_non_blocking(self, orch, app_mock):
        app_mock.agents["state_extractor"].extract_cumulative_state.side_effect = RuntimeError("LLM error")
        result = orch._get_entity_registry(arc_idx=0)
        assert result is None
        assert orch._entity_cache_arc_idx == 0  # [P0] 실패한 arc_idx 캐싱 — 동일 arc 무한 재시도 방지


# ── Blueprint Helpers ────────────────────────────────────────


class TestLoadPrevBlueprint:
    def test_returns_none_for_ep1(self, orch):
        result = orch._load_prev_blueprint(1)
        assert result is None

    def test_returns_prev_for_ep2(self, orch, app_mock):
        app_mock.current_project.get_blueprint.return_value = {"ep": 1}
        result = orch._load_prev_blueprint(2)
        assert result == {"ep": 1}

    def test_crash_returns_none(self, orch, app_mock):
        app_mock.current_project.get_blueprint.side_effect = RuntimeError("DB crash")
        result = orch._load_prev_blueprint(5)
        assert result is None


class TestGetProtagonistNameSafe:
    def test_returns_name(self, orch, app_mock):
        app_mock._get_protagonist_name.return_value = "소림사"
        assert orch._get_protagonist_name_safe() == "소림사"

    def test_crash_returns_default(self, orch, app_mock):
        app_mock._get_protagonist_name.side_effect = RuntimeError("crash")
        assert orch._get_protagonist_name_safe() == "주인공"


class TestNs4TimelineHelpers:
    def test_extract_timeline_start_end_from_range_string(self, orch):
        arc_data = {
            "state_changes": {
                "timeline": {
                    "start": "2006년 5월~8월",
                    "end": "2006년 5월~8월",
                }
            }
        }
        start, end = orch._extract_timeline_start_end(arc_data)
        assert start == (2006, 5)
        assert end == (2006, 8)

    def test_timeline_start_end_raw_equal(self, orch):
        arc_data = {
            "state_changes": {
                "timeline": {
                    "start": "2006년 5월~8월",
                    "end": "2006년 5월~8월",
                }
            }
        }
        assert orch._timeline_start_end_raw_equal(arc_data) is True


class TestGenerateBlueprint:
    @patch("modules.core.spinners.StageSpinner")
    def test_world_state_advisory_included_in_semantic_context(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.world_state.get_summary.return_value = "주인공 상태=긴장, 진행 플롯=적대적 인수합병"

        orch._generate_blueprint(
            working_ep=1,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={},
            protagonist_name="장무기",
            protagonist_config={},
        )

        semantic_context = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["semantic_context"]
        assert "[WorldState 핵심 요약]" in semantic_context
        assert "진행 플롯=적대적 인수합병" in semantic_context

    @patch("modules.core.spinners.StageSpinner")
    def test_fact_ledger_advisory_included_in_semantic_context(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.current_project.db.load_anchor.side_effect = lambda key: (
            {"numbers": {"자본금": {"value": "10억", "unit": "원", "last_ep": 12}}}
            if key == "fact_ledger"
            else []
        )

        orch._generate_blueprint(
            working_ep=1,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={},
            protagonist_name="장무기",
            protagonist_config={},
        )

        semantic_context = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["semantic_context"]
        assert "[팩트 원장 핵심 수치]" in semantic_context
        assert "자본금" in semantic_context

    @patch("modules.core.spinners.StageSpinner")
    def test_style_guide_advisory_included_in_semantic_context(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.current_project.load_v20_anchor.return_value = {
            "tone": "건조함",
            "pov": "3인칭",
            "sentence_length": "short",
            "paragraph_style": "mixed",
            "anti_ai_patterns": ["그의 눈동자가 흔들렸다"],
        }

        orch._generate_blueprint(
            working_ep=1,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={},
            protagonist_name="장무기",
            protagonist_config={},
        )

        semantic_context = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["semantic_context"]
        assert "[StyleGuide 문체/anti-AI 참고]" in semantic_context
        assert "그의 눈동자가 흔들렸다" in semantic_context

    @patch("modules.core.spinners.StageSpinner")
    def test_work_focus_summary_included_in_semantic_context(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.sys.guard = MagicMock()
        app_mock.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["핵심 배우 라인"],
            "mandatory_scene_engines": ["인재 발굴"],
            "registry_profiles": [
                {
                    "name": "talent_registry",
                    "required_fields": ["name", "status", "fan_reaction"],
                }
            ],
        }

        orch._generate_blueprint(
            working_ep=1,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={"characters": ["윤서아", "강이현"]},
            protagonist_name="장무기",
            protagonist_config={},
        )

        semantic_context = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["semantic_context"]
        assert "[작품 추적 슬롯 요약]" in semantic_context
        assert "핵심 배우 라인" in semantic_context
        assert "talent_registry" in semantic_context

    @patch("modules.core.spinners.StageSpinner")
    def test_stage3_advisor_receives_work_focus(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.context_advisor = MagicMock()
        app_mock.memory = MagicMock()
        app_mock.memory.retrieve_multi_query_context.return_value = "vec context"
        app_mock.memory.retrieve_npc_context.return_value = "npc context"
        app_mock.sys.guard = MagicMock()
        app_mock.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["핵심 배우 라인"],
            "mandatory_scene_engines": ["팬덤 반응"],
            "registry_profiles": [{"name": "talent_registry", "required_fields": ["name", "heat"]}],
        }
        app_mock.context_advisor.plan_stage3_retrieval.return_value = MagicMock(
            slots=[
                MagicMock(category="work_tracking_slot_1", query="slot query", source="db_npc_history", max_chars=400),
                MagicMock(category="genre_context_1", query="genre query", source="vec_memory", max_chars=400),
            ]
        )

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage3_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 8
            return default

        with patch("modules.validation.threshold_helper._threshold", side_effect=threshold_side_effect):
            orch._generate_blueprint(
                working_ep=1,
                arc_data=app_mock.current_project.arcs[0],
                arc_idx=0,
                prev_blueprint=None,
                prev_blueprints=[],
                entity_registry={"characters": [{"name": "윤서아"}, {"name": "강이현"}]},
                protagonist_name="장무기",
                protagonist_config={},
            )

        app_mock.context_advisor.plan_stage3_retrieval.assert_called_once()
        call_kwargs = app_mock.context_advisor.plan_stage3_retrieval.call_args.kwargs
        assert call_kwargs["work_focus"]["tracking_slots"] == ["핵심 배우 라인"]

    @patch("modules.core.spinners.StageSpinner")
    def test_stage3_work_focus_relation_slice_included_in_semantic_context(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.quality_dashboard = MagicMock()
        app_mock.sys.guard = MagicMock()
        app_mock.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["소꿉친구 관계선"],
            "mandatory_scene_engines": [],
            "registry_profiles": [],
        }
        app_mock.world_state.get_state_dict.return_value = {"relationships": {"연홍": "죽마고우"}}
        app_mock.fact_ledger._ledger = {
            "characters": {"연홍": {"relationship": "소꿉친구", "established_ep": 3, "history": []}}
        }
        app_mock.current_project.db.get_npc_relationship_edges.return_value = [
            {"npc1": "장무기", "npc2": "연홍", "relation": "죽마고우", "updated_ep": 3}
        ]
        app_mock.current_project.db.get_relationship_history.return_value = [
            {"old_relation": "친구", "new_relation": "죽마고우", "change_ep": 3}
        ]

        orch._generate_blueprint(
            working_ep=1,
            arc_data={
                **app_mock.current_project.arcs[0],
                "constraint_summary": "연홍과의 소꿉친구 관계를 회복한다",
            },
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={"characters": ["연홍"]},
            protagonist_name="장무기",
            protagonist_config={},
        )

        semantic_context = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["semantic_context"]
        app_mock.quality_dashboard.record_retrieval_observation.assert_called_once()
        kwargs = app_mock.quality_dashboard.record_retrieval_observation.call_args.kwargs
        assert kwargs["stage"] == "stage3"
        assert kwargs["observation"]["relation_slice_included"] is True
        assert "[관계 의미 질의]" in semantic_context
        assert "연홍" in semantic_context


# ── Single Episode Processing ────────────────────────────────


class TestProcessSingleEpisode:
    def test_skip_existing_blueprint(self, orch, app_mock):
        app_mock.current_project.get_blueprint.return_value = {"existing": True}
        result = orch._process_single_episode(1, 5, [], 0, 0)
        assert result["next_ep"] == 2

    def test_continuity_block(self, orch, app_mock):
        """직전 화 Blueprint 없으면 중단"""

        # ep 1 exists, ep 2 does not
        def get_bp(ep):
            if ep == 1:
                return None  # ep 1 missing (for ep=2 check)
            return None

        app_mock.current_project.get_blueprint.side_effect = get_bp
        result = orch._process_single_episode(2, 5, [], 0, 0)
        assert result.get("break") is True

    def test_no_arc_context_breaks(self, orch, app_mock):
        app_mock.current_project.get_blueprint.return_value = None
        app_mock._get_arc_context_for_episode.return_value = (None, None)
        result = orch._process_single_episode(1, 5, [], 0, 0)
        assert result.get("break") is True


# ── Result Handlers ──────────────────────────────────────────


class TestHandleSuccess:
    def test_saves_and_increments(self, orch, app_mock):
        bp = {"integrated_scenario": "text", "scene_breakdown": {"s1": "scene"}}
        pr = {"phases": {"generate": {"selected_strategy": "A", "selected_score": 85}}}
        prev_bps = []
        result = orch._handle_success(3, 1, {}, bp, pr, prev_bps, 2, 1)
        assert result["next_ep"] == 4
        assert result["success_count"] == 3
        assert result["fail_count"] == 0
        app_mock.current_project.save_episode_blueprint.assert_called_once_with(3, bp)
        app_mock._safe_commit.assert_called_once()

    def test_integrity_fail_skips(self, orch, app_mock):
        app_mock._validate_blueprint_integrity.return_value = False
        bp = {"bad": True}
        pr = {}
        result = orch._handle_success(3, 1, {}, bp, pr, [], 2, 0)
        assert result["fail_count"] == 1
        app_mock.current_project.save_episode_blueprint.assert_not_called()


class TestHandleFailure:
    def test_increments_fail_count(self, orch, app_mock):
        pr = {"final_verdict": "FAIL"}
        result = orch._handle_failure(3, pr, 2, 1)
        assert result["fail_count"] == 2

    def test_three_consecutive_fails_breaks(self, orch, app_mock):
        pr = {"final_verdict": "FAIL"}
        result = orch._handle_failure(3, pr, 0, 2)  # 2 + 1 = 3
        assert result["fail_count"] == 3
        assert result.get("break") is True


# ── Main Entry Point ─────────────────────────────────────────


class TestStage3BatchBlueprintingEntryPoint:
    def test_no_arcs_returns_early(self, app_mock):
        app_mock.current_project.arcs = []
        orch = Stage3Orchestrator(app=app_mock)
        orch.stage_3_batch_blueprinting()
        app_mock._write_audit_summary.assert_not_called()

    def test_full_run_single_episode(self, orch, app_mock):
        """1화짜리 전체 플로우 — 성공 경로"""
        # target_ep=5, production_head=0 → working_ep=1
        # _get_int_input returns 1 (1화만 생성)
        app_mock._get_int_input.return_value = 1

        with patch("modules.core.spinners.StageSpinner"):
            orch.stage_3_batch_blueprinting()

        app_mock._write_audit_summary.assert_called_once_with("stage3_complete")
        app_mock.current_project.save_episode_blueprint.assert_called_once()


# ── [Phase 4C-4] Stage3Context DI 테스트 ─────────────────────


class TestStage3ContextDI:
    def test_ctx_none_by_default(self, app_mock):
        """초기 _ctx=None"""
        orch = Stage3Orchestrator(app=app_mock)
        assert orch._ctx is None

    def test_ctx_auto_builds_from_app(self, app_mock):
        """property 접근 시 app에서 자동 빌드"""
        orch = Stage3Orchestrator(app=app_mock)
        ctx = orch.ctx
        assert isinstance(ctx, Stage3Context)
        assert ctx.ui is app_mock.ui
        assert ctx.current_project is app_mock.current_project

    def test_ctx_injected_at_init(self, app_mock):
        """context= 키워드로 주입"""
        ctx = Stage3Context(ui=app_mock.ui, current_project=app_mock.current_project)
        orch = Stage3Orchestrator(app=app_mock, context=ctx)
        assert orch.ctx is ctx

    def test_ctx_setter_replaces_context(self, app_mock):
        """ctx setter로 교체"""
        ctx = Stage3Context(ui=app_mock.ui, current_project=app_mock.current_project)
        orch = Stage3Orchestrator(app=app_mock)
        orch.ctx = ctx
        assert orch.ctx is ctx
        assert orch._ctx is ctx

    def test_get_protagonist_name_safe_uses_ctx(self, app_mock):
        """_get_protagonist_name_safe가 ctx.get_protagonist_name 경유"""
        cb = MagicMock(return_value="장무기")
        ctx = Stage3Context(
            ui=app_mock.ui,
            current_project=app_mock.current_project,
            get_protagonist_name=cb,
        )
        orch = Stage3Orchestrator(app=app_mock, context=ctx)
        result = orch._get_protagonist_name_safe()
        cb.assert_called_once()
        assert result == "장무기"

    def test_from_app_all_slots(self, app_mock):
        """from_app이 20개 슬롯 전부 매핑하는지 확인"""
        ctx = Stage3Context.from_app(app_mock)
        assert ctx.ui is app_mock.ui
        assert ctx.current_project is app_mock.current_project
        assert ctx.agents is app_mock.agents
        assert ctx.sys is app_mock.sys
        assert ctx.state_tracker is app_mock.state_tracker
        assert ctx.world_state is app_mock.world_state
        assert ctx.fact_ledger is app_mock.fact_ledger
        assert ctx.adversarial_self_play is app_mock.adversarial_self_play
        assert ctx.preset_registry is app_mock.preset_registry
        assert ctx.selected_genre is app_mock.selected_genre
        assert ctx.get_protagonist_name is app_mock._get_protagonist_name
        assert ctx.audit_event is app_mock._audit_event
        assert ctx.write_audit_summary is app_mock._write_audit_summary
        assert ctx.get_arc_context_for_episode is app_mock._get_arc_context_for_episode
        assert ctx.get_max_episode_from_manuscripts is app_mock._get_max_episode_from_manuscripts
        assert ctx.get_int_input is app_mock._get_int_input
        assert ctx.safe_commit is app_mock._safe_commit
        assert ctx.validate_arc_data_fields is app_mock._validate_arc_data_fields
        assert ctx.validate_blueprint_integrity is app_mock._validate_blueprint_integrity
        assert ctx.fix_entity_registry_protagonist is app_mock._fix_entity_registry_protagonist

    def test_slots_count_20(self):
        """__slots__ 개수 검증"""
        assert len(Stage3Context.__slots__) == 21  # [LOG-1] +session_logger

    def test_ctx_sync_after_lazy_init(self, app_mock):
        """lazy init 후 state_tracker/world_state/fact_ledger가 ctx에 sync되는지 확인"""
        app_mock.state_tracker = None
        app_mock.world_state = None
        app_mock.fact_ledger = None
        app_mock._get_int_input.return_value = 1

        orch = Stage3Orchestrator(app=app_mock)

        with (
            patch("modules.domain.agents.state_tracker.StateTracker") as MockST,
            patch("modules.core.world_state.WorldStateManager") as MockWS,
            patch("modules.core.fact_ledger.FactLedger") as MockFL,
            patch("modules.core.spinners.StageSpinner"),
        ):
            mock_st = MagicMock(npc_registry={})
            MockST.return_value = mock_st
            mock_ws = MagicMock(last_updated_ep=0)
            MockWS.return_value = mock_ws
            mock_fl = MagicMock(last_updated_ep=0)
            MockFL.return_value = mock_fl

            orch.stage_3_batch_blueprinting()

        assert orch.ctx.state_tracker is mock_st
        assert orch.ctx.world_state is mock_ws
        assert orch.ctx.fact_ledger is mock_fl

    def test_backward_compat_app_still_works(self, app_mock):
        """self.app 접근 유지 (레거시 호환)"""
        orch = Stage3Orchestrator(app=app_mock)
        assert orch.app is app_mock

    def test_none_callbacks_do_not_raise_type_error(self, app_mock):
        """[G-1] DI 콜백이 None이어도 callable 가드로 TypeError 없이 종료."""
        ctx = Stage3Context.from_app(app_mock)
        ctx.get_max_episode_from_manuscripts = None
        ctx.get_int_input = None
        ctx.write_audit_summary = None
        ctx.get_arc_context_for_episode = None
        ctx.get_protagonist_name = None
        orch = Stage3Orchestrator(app=app_mock, context=ctx)

        orch.stage_3_batch_blueprinting()

        app_mock._write_audit_summary.assert_not_called()
