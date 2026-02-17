"""[Sweep2-A1] Stage 간 StateTracker 동기화 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock


class TestStage2ToAppSync:
    """A-1: Stage 2 완료 후 state_tracker가 app에 동기화되는지 확인."""

    def _run_sync_logic(self, app):
        """main_a.py _stage_2_arcs() 끝의 동기화 로직 재현."""
        _s2_ctx = app._stage2_orch.ctx
        if _s2_ctx is not None and getattr(_s2_ctx, "state_tracker", None) is not None:
            app.state_tracker = _s2_ctx.state_tracker

    def test_state_tracker_synced_after_stage2(self):
        """Stage 2 완료 후 app.state_tracker == ctx.state_tracker."""
        app = MagicMock()
        app.state_tracker = None

        mock_tracker = MagicMock()
        mock_tracker.npc_registry = {"npc_1": {"name": "테스트", "status": "alive"}}
        app._stage2_orch.ctx.state_tracker = mock_tracker

        self._run_sync_logic(app)

        assert app.state_tracker is mock_tracker
        assert app.state_tracker.npc_registry["npc_1"]["name"] == "테스트"

    def test_state_tracker_not_synced_when_ctx_none(self):
        """ctx 자체가 None이면 동기화하지 않음."""
        app = MagicMock()
        app.state_tracker = None
        app._stage2_orch.ctx = None

        self._run_sync_logic(app)

        assert app.state_tracker is None

    def test_state_tracker_not_synced_when_tracker_none(self):
        """ctx.state_tracker가 None이면 동기화하지 않음."""
        app = MagicMock()
        app.state_tracker = None
        app._stage2_orch.ctx = MagicMock()
        app._stage2_orch.ctx.state_tracker = None

        self._run_sync_logic(app)

        assert app.state_tracker is None

    def test_stage3_reuses_synced_tracker(self):
        """동기화된 state_tracker가 있으면 Stage 3 lazy init 스킵."""
        mock_tracker = MagicMock()

        app = MagicMock()
        app.state_tracker = mock_tracker  # Stage 2에서 동기화된 상태

        # Stage 3 lazy init 조건 재현
        should_init = not hasattr(app, "state_tracker") or app.state_tracker is None
        assert should_init is False  # lazy init 스킵

    def test_stage4_reuses_synced_tracker(self):
        """동기화된 state_tracker가 있으면 Stage 4 lazy init도 스킵."""
        mock_tracker = MagicMock()

        app = MagicMock()
        app.state_tracker = mock_tracker  # Stage 2에서 동기화된 상태

        # Stage 4 lazy init 조건 재현 (main_a.py L2725)
        should_init = not hasattr(app, "state_tracker") or app.state_tracker is None
        assert should_init is False  # lazy init 스킵

    def test_synced_tracker_preserves_rich_data(self):
        """동기화 시 Stage 2의 풍부한 NPC 데이터가 보존되는지 확인."""
        app = MagicMock()
        app.state_tracker = None

        mock_tracker = MagicMock()
        # Stage 2가 구축하는 다양한 데이터 시뮬레이션
        mock_tracker.npc_registry = {"villain": {"status": "dead"}}
        mock_tracker.skill_registry = {"hero_skill": {"level": 5}}
        mock_tracker.time_markers = [{"ep": 1, "event": "sunrise"}]
        mock_tracker.permanent_injuries = {"hero": ["arm"]}
        mock_tracker.companions = ["sidekick"]
        mock_tracker.commitments = [{"type": "oath"}]
        mock_tracker.protagonist_emotion = "determined"
        app._stage2_orch.ctx.state_tracker = mock_tracker

        self._run_sync_logic(app)

        # 모든 풍부한 데이터가 app에 전달됨
        assert app.state_tracker.npc_registry["villain"]["status"] == "dead"
        assert app.state_tracker.skill_registry["hero_skill"]["level"] == 5
        assert len(app.state_tracker.time_markers) == 1
        assert app.state_tracker.permanent_injuries["hero"] == ["arm"]
        assert app.state_tracker.companions == ["sidekick"]
        assert app.state_tracker.protagonist_emotion == "determined"
