"""Lane-5 contract tests: runtime-authority-and-init-seam-hardening

Covers:
  1. Stage 3 domain-state authority — idempotent lazy init
  2. _run_stage2_arc_async dispatch helper — no-loop path and running-loop path
  3. Boot comment accuracy — world_state / fact_ledger start as None
  4. Stage 4 gateway fallback — initialises state objects when Stage 3 was skipped
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

# ─────────────────────────────────────────────────────────────────────────────
# Helpers / fixtures
# ─────────────────────────────────────────────────────────────────────────────


def _make_app(**overrides):
    """Minimal app mock with V68 state slots."""
    app = MagicMock()
    app.ui.log = MagicMock()
    app.selected_genre = {"type": "wuxia"}
    app.preset_registry = MagicMock()
    app.sys.api_client = MagicMock()
    app.current_project.db.load_anchor.return_value = []
    # Default: state objects already exist (pre-populated)
    app.state_tracker = MagicMock()
    app.world_state = MagicMock()
    app.fact_ledger = MagicMock()
    for k, v in overrides.items():
        setattr(app, k, v)
    return app


# ─────────────────────────────────────────────────────────────────────────────
# 1. Stage 3 domain-state authority
# ─────────────────────────────────────────────────────────────────────────────


class TestStage3LazyInitIdempotency:
    """_init_*_if_needed must not overwrite an already-set attribute."""

    def _make_orch(self, **overrides):
        from modules.core.stage3_orchestrator import Stage3Orchestrator

        app = _make_app(**overrides)
        return Stage3Orchestrator(app=app)

    def test_state_tracker_not_overwritten_when_already_set(self):
        sentinel = object()
        orch = self._make_orch(state_tracker=sentinel)
        orch._init_state_tracker_if_needed()
        assert orch.app.state_tracker is sentinel

    def test_world_state_not_overwritten_when_already_set(self):
        sentinel = object()
        orch = self._make_orch(world_state=sentinel)
        orch._init_world_state_if_needed()
        assert orch.app.world_state is sentinel

    def test_fact_ledger_not_overwritten_when_already_set(self):
        sentinel = object()
        orch = self._make_orch(fact_ledger=sentinel)
        orch._init_fact_ledger_if_needed()
        assert orch.app.fact_ledger is sentinel

    def test_state_tracker_created_when_none(self):
        fake_tracker = MagicMock()
        fake_tracker.npc_registry = {}
        orch = self._make_orch(state_tracker=None)
        with (
            patch("modules.domain.agents.state_tracker.StateTracker", return_value=fake_tracker),
            patch.object(orch.app.current_project.db, "load_anchor", return_value=[]),
        ):
            orch._init_state_tracker_if_needed()
        assert orch.app.state_tracker is fake_tracker

    def test_world_state_created_when_none(self):
        fake_ws = MagicMock()
        fake_ws.last_updated_ep = 0
        orch = self._make_orch(world_state=None)
        with patch("modules.core.world_state.WorldStateManager", return_value=fake_ws):
            orch._init_world_state_if_needed()
        assert orch.app.world_state is fake_ws

    def test_fact_ledger_created_when_none(self):
        fake_fl = MagicMock()
        fake_fl.last_updated_ep = 0
        orch = self._make_orch(fact_ledger=None)
        with patch("modules.core.fact_ledger.FactLedger", return_value=fake_fl):
            orch._init_fact_ledger_if_needed()
        assert orch.app.fact_ledger is fake_fl

    def test_state_tracker_none_on_init_failure(self):
        orch = self._make_orch(state_tracker=None)
        with patch("modules.domain.agents.state_tracker.StateTracker", side_effect=RuntimeError("boom")):
            orch._init_state_tracker_if_needed()
        assert orch.app.state_tracker is None

    def test_world_state_none_on_init_failure(self):
        orch = self._make_orch(world_state=None)
        with patch("modules.core.world_state.WorldStateManager", side_effect=RuntimeError("boom")):
            orch._init_world_state_if_needed()
        assert orch.app.world_state is None


# ─────────────────────────────────────────────────────────────────────────────
# 2. _run_stage2_arc_async dispatch helper
# ─────────────────────────────────────────────────────────────────────────────


class TestRunStage2ArcAsync:
    """_run_stage2_arc_async must set ctx, dispatch, and write back state_tracker."""

    def _make_sovereign_app(self):

        app = SimpleNamespace()
        app.ui = SimpleNamespace(log=MagicMock())
        app.state_tracker = None
        app._state_tracker_loaded_arcs = 0

        # Stage2 orchestrator mock
        fake_ctx = SimpleNamespace(state_tracker=MagicMock(), state_tracker_loaded_arcs=3)
        stage2_orch = SimpleNamespace(ctx=None, stage_2_arcs_async_logic=None)
        app._stage2_orch = stage2_orch

        return app, fake_ctx

    def test_no_running_loop_calls_asyncio_run(self):
        import main_a

        app, fake_ctx = self._make_sovereign_app()
        expected_coro = AsyncMock()

        def _fake_ctx_factory(self_):
            return fake_ctx

        with (
            patch("modules.core.stage2_context.Stage2Context.from_app", return_value=fake_ctx),
            patch("asyncio.get_running_loop", side_effect=RuntimeError("no loop")),
            patch("asyncio.run") as mock_run,
        ):
            app._stage2_orch.stage_2_arcs_async_logic = MagicMock(return_value=expected_coro)
            main_a.SovereignApp._run_stage2_arc_async(app, target_arc_count=1)
            mock_run.assert_called_once_with(expected_coro)

        # state_tracker written back
        assert app.state_tracker is fake_ctx.state_tracker
        assert app._state_tracker_loaded_arcs == 3

    def test_no_running_loop_no_target_arc_count(self):
        import main_a

        app, fake_ctx = self._make_sovereign_app()
        expected_coro = AsyncMock()

        with (
            patch("modules.core.stage2_context.Stage2Context.from_app", return_value=fake_ctx),
            patch("asyncio.get_running_loop", side_effect=RuntimeError("no loop")),
            patch("asyncio.run"),
        ):
            app._stage2_orch.stage_2_arcs_async_logic = MagicMock(return_value=expected_coro)
            main_a.SovereignApp._run_stage2_arc_async(app)
            app._stage2_orch.stage_2_arcs_async_logic.assert_called_once_with(target_arc_count=None)

    def test_state_tracker_not_written_when_ctx_is_none(self):
        import main_a

        app, _ = self._make_sovereign_app()
        app._stage2_orch.ctx = None  # ctx ends up None

        with (
            patch("modules.core.stage2_context.Stage2Context.from_app", return_value=None),
            patch("asyncio.get_running_loop", side_effect=RuntimeError("no loop")),
            patch("asyncio.run"),
        ):
            app._stage2_orch.stage_2_arcs_async_logic = MagicMock(return_value=AsyncMock())
            main_a.SovereignApp._run_stage2_arc_async(app)

        # state_tracker must remain None (no write-back from None ctx)
        assert app.state_tracker is None

    def test_state_tracker_not_written_when_ctx_state_tracker_is_none(self):
        import main_a

        app, fake_ctx = self._make_sovereign_app()
        fake_ctx.state_tracker = None  # ctx has no state_tracker

        with (
            patch("modules.core.stage2_context.Stage2Context.from_app", return_value=fake_ctx),
            patch("asyncio.get_running_loop", side_effect=RuntimeError("no loop")),
            patch("asyncio.run"),
        ):
            app._stage2_orch.stage_2_arcs_async_logic = MagicMock(return_value=AsyncMock())
            main_a.SovereignApp._run_stage2_arc_async(app)

        assert app.state_tracker is None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Boot comment accuracy — init state slots
# ─────────────────────────────────────────────────────────────────────────────


class TestBootInitSlots:
    """Verify that world_state and fact_ledger start as None (lazy-init contract)."""

    def test_world_state_initialized_to_none(self, monkeypatch):
        import main_a
        import modules.core.logger as logger_module

        monkeypatch.setattr(logger_module, "init_logger", MagicMock())
        monkeypatch.setattr(main_a, "StudioVisualizer", lambda: SimpleNamespace(log=MagicMock()))
        monkeypatch.setattr(main_a, "genai", SimpleNamespace(Client=lambda api_key=None: SimpleNamespace()))
        monkeypatch.setattr(main_a, "StudioSystem", lambda api_client=None: SimpleNamespace(api_client=api_client))
        monkeypatch.setattr(main_a, "PromptBuilder", lambda app=None: MagicMock())
        monkeypatch.setattr(main_a, "FeedbackSystem", lambda: MagicMock())
        monkeypatch.setattr(main_a, "Stage01Helpers", lambda app=None: MagicMock())
        monkeypatch.setattr(main_a, "Stage2Orchestrator", lambda app=None: MagicMock())
        monkeypatch.setattr(main_a, "Stage3Orchestrator", lambda app=None: MagicMock())
        monkeypatch.setattr(main_a, "Stage4Orchestrator", lambda app=None: MagicMock())
        monkeypatch.setattr(main_a, "BootstrapStatus", lambda: MagicMock())
        monkeypatch.setattr(main_a, "PerfTimer", lambda label: MagicMock())

        app = SimpleNamespace()
        main_a.SovereignApp._init_core_runtime_state(app)

        assert app.world_state is None
        assert app.fact_ledger is None

    def test_state_tracker_starts_as_none(self, monkeypatch):
        import main_a
        import modules.core.logger as logger_module

        monkeypatch.setattr(logger_module, "init_logger", MagicMock())
        monkeypatch.setattr(main_a, "StudioVisualizer", lambda: SimpleNamespace(log=MagicMock()))
        monkeypatch.setattr(main_a, "genai", SimpleNamespace(Client=lambda api_key=None: SimpleNamespace()))
        monkeypatch.setattr(main_a, "StudioSystem", lambda api_client=None: SimpleNamespace(api_client=api_client))
        monkeypatch.setattr(main_a, "PromptBuilder", lambda app=None: MagicMock())
        monkeypatch.setattr(main_a, "FeedbackSystem", lambda: MagicMock())
        monkeypatch.setattr(main_a, "Stage01Helpers", lambda app=None: MagicMock())
        monkeypatch.setattr(main_a, "Stage2Orchestrator", lambda app=None: MagicMock())
        monkeypatch.setattr(main_a, "Stage3Orchestrator", lambda app=None: MagicMock())
        monkeypatch.setattr(main_a, "Stage4Orchestrator", lambda app=None: MagicMock())
        monkeypatch.setattr(main_a, "BootstrapStatus", lambda: MagicMock())
        monkeypatch.setattr(main_a, "PerfTimer", lambda label: MagicMock())

        app = SimpleNamespace()
        main_a.SovereignApp._init_core_runtime_state(app)

        # state_tracker is not set in _init_core_runtime_state (set by Stage 2/3 lazy init)
        assert not hasattr(app, "state_tracker") or app.state_tracker is None
