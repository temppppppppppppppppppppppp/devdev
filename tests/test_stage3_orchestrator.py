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
        assert orch._entity_cache_arc_idx == 0  # Still marked to prevent retries


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
        result = orch._handle_success(3, 1, bp, pr, prev_bps, 2, 1)
        assert result["next_ep"] == 4
        assert result["success_count"] == 3
        assert result["fail_count"] == 0
        app_mock.current_project.save_episode_blueprint.assert_called_once_with(3, bp)
        app_mock._safe_commit.assert_called_once()

    def test_integrity_fail_skips(self, orch, app_mock):
        app_mock._validate_blueprint_integrity.return_value = False
        bp = {"bad": True}
        pr = {}
        result = orch._handle_success(3, 1, bp, pr, [], 2, 0)
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
        """from_app이 19개 슬롯 전부 매핑하는지 확인"""
        ctx = Stage3Context.from_app(app_mock)
        assert ctx.ui is app_mock.ui
        assert ctx.current_project is app_mock.current_project
        assert ctx.agents is app_mock.agents
        assert ctx.sys is app_mock.sys
        assert ctx.state_tracker is app_mock.state_tracker
        assert ctx.world_state is app_mock.world_state
        assert ctx.fact_ledger is app_mock.fact_ledger
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

    def test_slots_count_19(self):
        """__slots__ 개수 검증"""
        assert len(Stage3Context.__slots__) == 19

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
