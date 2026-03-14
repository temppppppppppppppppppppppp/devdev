from unittest.mock import MagicMock, call, patch

import pytest

from modules.core.services.project_service import ProjectService


@pytest.fixture
def ui_mock():
    ui = MagicMock()
    ui.log = MagicMock()
    return ui


@pytest.fixture
def project_mock():
    project = MagicMock()
    project.arcs = [
        {"arc_no": 1, "title": "Arc 1", "ep_start": 1, "ep_end": 2},
        {"arc_no": 2, "title": "Arc 2", "ep_start": 3, "ep_end": 4},
        {"arc_no": 3, "title": "Arc 3", "ep_start": 5, "ep_end": 6},
    ]
    project.get_latest_episode_number.return_value = 6  # latest ep = 5
    project.paths.drafts = MagicMock()
    project.paths.drafts.glob.return_value = []
    project.db = MagicMock()
    project.db.cursor = MagicMock()
    project.db.load_anchor.return_value = {"MasterBible": {"MartialHUD": {"Protagonist": {}}}}
    project.db.save_anchor = MagicMock(return_value=True)
    project._load_from_db = MagicMock()
    return project


@pytest.fixture
def safe_commit_mock():
    return MagicMock(return_value=True)


@pytest.fixture
def genre_fn():
    return lambda: {"type": "wuxia"}


@pytest.fixture
def memory_mock():
    mem = MagicMock()
    mem.delete_episodes_from = MagicMock(return_value=3)
    mem.delete_all_episodes = MagicMock(return_value=5)
    return mem


@pytest.fixture
def svc(ui_mock, project_mock, safe_commit_mock, genre_fn, memory_mock):
    return ProjectService(
        project_fn=lambda: project_mock,
        ui=ui_mock,
        safe_commit_fn=safe_commit_mock,
        genre_fn=genre_fn,
        memory_fn=lambda: memory_mock,
    )


class TestResetStage2:
    def test_confirm_n_does_nothing(self, svc, project_mock):
        with patch("builtins.input", return_value="n"):
            result = svc.reset_stage_2()

        assert result is False
        project_mock.db.reset_after.assert_not_called()

    def test_confirm_y_clears_stage2_and_downstream(self, svc, project_mock, safe_commit_mock, memory_mock):
        with patch("builtins.input", side_effect=["y", ""]):
            result = svc.reset_stage_2()

        assert result is True
        project_mock.db.reset_after.assert_called_once_with(1, commit=False)
        assert project_mock.arcs == []
        safe_commit_mock.assert_called_once()
        memory_mock.delete_all_episodes.assert_called_once()
        execute_calls = project_mock.db.cursor.execute.call_args_list
        assert call("DELETE FROM arc_dependencies") in execute_calls
        assert call("DELETE FROM stage_attempts WHERE stage = 2") in execute_calls
        assert call(
            "DELETE FROM director_selections WHERE stage = 2 OR (stage IS NULL AND COALESCE(selected_label, '') = '')"
        ) in execute_calls
        assert call("DELETE FROM anchors WHERE key LIKE 'narrative_summary_ep_%'") in execute_calls
        assert call("DELETE FROM anchors WHERE key = 'arcs'") in execute_calls

        outcome = svc.last_destructive_result
        assert outcome is not None
        assert outcome.operation == "reset_stage_2"
        assert outcome.target_ep == 1
        assert outcome.status == "success"
        assert outcome.runtime_restore_ok is True
        assert outcome.cache_invalidation_required is True

    def test_commit_failure_returns_false(self, ui_mock, project_mock, genre_fn, memory_mock):
        svc = ProjectService(
            project_fn=lambda: project_mock,
            ui=ui_mock,
            safe_commit_fn=MagicMock(return_value=False),
            genre_fn=genre_fn,
            memory_fn=lambda: memory_mock,
        )
        svc._rollback_open_transaction = MagicMock()

        with patch("builtins.input", side_effect=["y"]):
            result = svc.reset_stage_2()

        assert result is False
        svc._rollback_open_transaction.assert_called_once_with(project_mock)
        ui_mock.log.assert_any_call("DB commit failed during Stage 2 reset")
        outcome = svc.last_destructive_result
        assert outcome is not None
        assert outcome.operation == "reset_stage_2"
        assert outcome.status == "aborted"
        assert outcome.runtime_restore_ok is False
        assert outcome.cache_invalidation_required is False


class TestRewindStage2:
    def test_no_arcs_returns_false(self, ui_mock, safe_commit_mock, genre_fn, memory_mock):
        project = MagicMock()
        project.arcs = []
        svc = ProjectService(
            project_fn=lambda: project,
            ui=ui_mock,
            safe_commit_fn=safe_commit_mock,
            genre_fn=genre_fn,
            memory_fn=lambda: memory_mock,
        )

        assert svc.rewind_stage_2() is False

    def test_non_digit_returns_false(self, svc):
        with patch("builtins.input", return_value="abc"):
            result = svc.rewind_stage_2()

        assert result is False

    def test_rewind_uses_removed_arc_start_episode(self, svc, project_mock, memory_mock):
        with patch("builtins.input", side_effect=["2", "y", ""]):
            result = svc.rewind_stage_2()

        assert result is True
        project_mock.db.reset_after.assert_called_once_with(3, commit=False)
        project_mock.db.save_anchor.assert_called_once_with(
            "arcs",
            [{"arc_no": 1, "title": "Arc 1", "ep_start": 1, "ep_end": 2}],
        )
        assert project_mock.arcs == [{"arc_no": 1, "title": "Arc 1", "ep_start": 1, "ep_end": 2}]
        memory_mock.delete_episodes_from.assert_called_once_with(3)
        execute_calls = project_mock.db.cursor.execute.call_args_list
        assert any(
            c.args
            and "DELETE FROM anchors" in c.args[0]
            and "narrative_summary_ep_" in c.args[0]
            and c.args[1] == (3,)
            for c in execute_calls
        )
        outcome = svc.last_destructive_result
        assert outcome is not None
        assert outcome.operation == "rewind_stage_2"
        assert outcome.target_ep == 3
        assert outcome.status == "success"
        assert outcome.runtime_restore_ok is True
        assert outcome.cache_invalidation_required is True

    def test_rewind_commit_failure_returns_false_without_runtime_mutation(
        self, ui_mock, project_mock, genre_fn, memory_mock
    ):
        svc = ProjectService(
            project_fn=lambda: project_mock,
            ui=ui_mock,
            safe_commit_fn=MagicMock(return_value=False),
            genre_fn=genre_fn,
            memory_fn=lambda: memory_mock,
        )
        svc._rollback_open_transaction = MagicMock()
        original_arcs = list(project_mock.arcs)

        with patch("builtins.input", side_effect=["2", "y"]):
            result = svc.rewind_stage_2()

        assert result is False
        svc._rollback_open_transaction.assert_called_once_with(project_mock)
        assert project_mock.arcs == original_arcs
        memory_mock.delete_episodes_from.assert_not_called()
        ui_mock.log.assert_any_call("DB commit failed during Stage 2 rewind")


class TestRollbackEpisode:
    def test_no_episodes_returns_false(self, ui_mock, safe_commit_mock, genre_fn, memory_mock):
        project = MagicMock()
        project.get_latest_episode_number.return_value = 1
        svc = ProjectService(
            project_fn=lambda: project,
            ui=ui_mock,
            safe_commit_fn=safe_commit_mock,
            genre_fn=genre_fn,
            memory_fn=lambda: memory_mock,
        )

        assert svc.rollback_episode() is False

    def test_cancel_returns_false(self, svc, ui_mock):
        with patch("builtins.input", side_effect=["3", "n"]):
            result = svc.rollback_episode()

        assert result is False
        ui_mock.log.assert_any_call("Cancelled.")

    def test_confirm_y_uses_reset_after_and_restores_state(self, svc, project_mock, memory_mock):
        project_mock.db.cursor.fetchone.return_value = None

        with patch("builtins.input", side_effect=["3", "y", ""]):
            result = svc.rollback_episode()

        assert result is True
        project_mock.db.reset_after.assert_called_once_with(3, commit=False)
        project_mock._load_from_db.assert_called_once()
        memory_mock.delete_episodes_from.assert_called_once_with(3)
        execute_calls = project_mock.db.cursor.execute.call_args_list
        assert any(
            c.args
            and "DELETE FROM anchors" in c.args[0]
            and "narrative_summary_ep_" in c.args[0]
            and c.args[1] == (3,)
            for c in execute_calls
        )
        assert any(
            c.args
            and c.args[0] == "UPDATE seeds SET status = 'active', recovered_ep = NULL WHERE recovered_ep >= ?"
            and c.args[1] == (3,)
            for c in execute_calls
        )

    def test_hud_restore_saves_anchor_after_reset(self, svc, project_mock):
        project_mock.db.cursor.fetchone.return_value = {
            "data": '{"state_updates": {"actual_truth": {"bank": "safe"}}}'
        }

        with patch("builtins.input", side_effect=["3", "y", ""]):
            result = svc.rollback_episode()

        assert result is True
        project_mock.db.save_anchor.assert_called_once()
        saved_key, saved_payload = project_mock.db.save_anchor.call_args.args
        assert saved_key == "bible"
        assert saved_payload["MasterBible"]["MartialHUD"]["Protagonist"]["actual_truth"] == {"bank": "safe"}

    def test_rollback_commit_failure_returns_false_without_bible_or_memory_mutation(
        self, ui_mock, project_mock, genre_fn, memory_mock
    ):
        svc = ProjectService(
            project_fn=lambda: project_mock,
            ui=ui_mock,
            safe_commit_fn=MagicMock(return_value=False),
            genre_fn=genre_fn,
            memory_fn=lambda: memory_mock,
        )
        svc._rollback_open_transaction = MagicMock()
        project_mock.db.cursor.fetchone.return_value = None

        with patch("builtins.input", side_effect=["3", "y"]):
            result = svc.rollback_episode()

        assert result is False
        svc._rollback_open_transaction.assert_called_once_with(project_mock)
        project_mock.db.reset_after.assert_called_once_with(3, commit=False)
        project_mock.db.save_anchor.assert_not_called()
        memory_mock.delete_episodes_from.assert_not_called()
        ui_mock.log.assert_any_call("DB commit failed during rollback")

    def test_rollback_post_commit_load_failure_surfaces_partial_result_and_clears_agent_context_cache(
        self, ui_mock, project_mock, safe_commit_mock, genre_fn, memory_mock
    ):
        from modules.domain.agents.base_agent import BaseAgent

        emotion_tracker = MagicMock()
        emotion_tracker.history = [(2, "neutral", 0.5), (4, "hope", 0.7)]
        state_delta_tracker = MagicMock()
        state_delta_tracker.energy_history = []
        state_delta_tracker.injury_history = []
        invalidate_tracker = MagicMock()
        project_mock.db.cursor.fetchone.return_value = None
        project_mock._load_from_db.side_effect = RuntimeError("load boom")

        svc = ProjectService(
            project_fn=lambda: project_mock,
            ui=ui_mock,
            safe_commit_fn=safe_commit_mock,
            genre_fn=genre_fn,
            memory_fn=lambda: memory_mock,
            state_tracker_invalidator=invalidate_tracker,
            emotion_tracker_fn=lambda: emotion_tracker,
            state_delta_tracker_fn=lambda: state_delta_tracker,
        )

        with BaseAgent._cache_lock:
            original_cache = dict(BaseAgent._context_caches)
            BaseAgent._context_caches.clear()
            BaseAgent._context_caches["stale"] = {"name": "stale-cache"}

        try:
            with patch("builtins.input", side_effect=["3", "y", ""]):
                result = svc.rollback_episode()

            assert result is True
            invalidate_tracker.assert_called_once()
            emotion_tracker.rollback_to.assert_called_once_with(3)
            state_delta_tracker.rollback_to.assert_called_once_with(3)

            outcome = svc.last_destructive_result
            assert outcome is not None
            assert outcome.status == "partial_restore_failed"
            assert outcome.db_committed is True
            assert outcome.cache_invalidation_required is True
            assert any(
                failure["step"] == "project.load_from_db" and "load boom" in failure["reason"]
                for failure in outcome.partial_failures
            )

            logs = [call.args[0] for call in ui_mock.log.call_args_list if call.args]
            assert any("[Partial] rollback_episode committed" in message for message in logs)
            assert not any("[Success] Rollback completed" in message for message in logs)
            with BaseAgent._cache_lock:
                assert BaseAgent._context_caches == {}
        finally:
            with BaseAgent._cache_lock:
                BaseAgent._context_caches.clear()
                BaseAgent._context_caches.update(original_cache)

    def test_rollback_tracker_failure_trims_tracker_residue_and_records_partial_result(
        self, ui_mock, project_mock, safe_commit_mock, genre_fn, memory_mock
    ):
        class _Entry:
            def __init__(self, episode: int) -> None:
                self.episode = episode

        emotion_tracker = MagicMock()
        emotion_tracker.history = [(1, "neutral", 0.5), (3, "hope", 0.7), (4, "triumph", 0.9)]
        emotion_tracker.rollback_to.side_effect = RuntimeError("emotion boom")

        state_delta_tracker = MagicMock()
        state_delta_tracker.energy_history = [_Entry(2), _Entry(5)]
        state_delta_tracker.injury_history = [_Entry(1), _Entry(4)]
        state_delta_tracker.rollback_to.side_effect = RuntimeError("delta boom")
        project_mock.db.cursor.fetchone.return_value = None

        svc = ProjectService(
            project_fn=lambda: project_mock,
            ui=ui_mock,
            safe_commit_fn=safe_commit_mock,
            genre_fn=genre_fn,
            memory_fn=lambda: memory_mock,
            emotion_tracker_fn=lambda: emotion_tracker,
            state_delta_tracker_fn=lambda: state_delta_tracker,
        )

        with patch("builtins.input", side_effect=["3", "y", ""]):
            result = svc.rollback_episode()

        assert result is True
        assert all(entry[0] < 3 for entry in emotion_tracker.history)
        assert [entry.episode for entry in state_delta_tracker.energy_history] == [2]
        assert [entry.episode for entry in state_delta_tracker.injury_history] == [1]

        outcome = svc.last_destructive_result
        assert outcome is not None
        assert outcome.status == "partial_restore_failed"
        steps = {failure["step"] for failure in outcome.partial_failures}
        assert "emotion_history.rollback_to" in steps
        assert "state_delta_tracker.rollback_to" in steps

    def test_rollback_invariant_leak_surfaces_partial_result_even_without_tracker_exception(
        self, ui_mock, project_mock, safe_commit_mock, genre_fn, memory_mock
    ):
        class _Entry:
            def __init__(self, episode: int) -> None:
                self.episode = episode

        emotion_tracker = MagicMock()
        emotion_tracker.history = [(1, "neutral", 0.5), (4, "hope", 0.7)]
        state_delta_tracker = MagicMock()
        state_delta_tracker.energy_history = [_Entry(2), _Entry(4)]
        state_delta_tracker.injury_history = [_Entry(1)]
        project_mock.db.cursor.fetchone.return_value = None

        svc = ProjectService(
            project_fn=lambda: project_mock,
            ui=ui_mock,
            safe_commit_fn=safe_commit_mock,
            genre_fn=genre_fn,
            memory_fn=lambda: memory_mock,
            emotion_tracker_fn=lambda: emotion_tracker,
            state_delta_tracker_fn=lambda: state_delta_tracker,
        )

        with patch("builtins.input", side_effect=["3", "y", ""]):
            result = svc.rollback_episode()

        assert result is True
        outcome = svc.last_destructive_result
        assert outcome is not None
        assert outcome.status == "partial_restore_failed"
        assert {"emotion_history.invariant", "state_delta_tracker.invariant"} <= {
            failure["step"] for failure in outcome.partial_failures
        }
        logs = [call.args[0] for call in ui_mock.log.call_args_list if call.args]
        assert any("[Partial] rollback_episode committed" in message for message in logs)


class TestWipeProductionData:
    def test_confirm_n_returns_false(self, svc, project_mock):
        with patch("builtins.input", return_value="n"):
            result = svc.wipe_production_data()

        assert result is False
        project_mock.db.reset_after.assert_not_called()

    def test_confirm_y_clears_episode_outputs(self, svc, project_mock, memory_mock):
        with patch("builtins.input", side_effect=["y", ""]):
            result = svc.wipe_production_data()

        assert result is True
        project_mock.db.reset_after.assert_called_once_with(1, commit=False)
        memory_mock.delete_all_episodes.assert_called_once()
        execute_calls = project_mock.db.cursor.execute.call_args_list
        assert any(
            c.args and c.args[0] == "UPDATE seeds SET status = 'active', recovered_ep = NULL"
            for c in execute_calls
        )
        assert any(
            c.args and c.args[0] == "DELETE FROM anchors WHERE key LIKE 'narrative_summary_ep_%'"
            for c in execute_calls
        )
        outcome = svc.last_destructive_result
        assert outcome is not None
        assert outcome.operation == "wipe_production_data"
        assert outcome.target_ep == 1
        assert outcome.status == "success"
        assert outcome.runtime_restore_ok is True
        assert outcome.cache_invalidation_required is True

    def test_commit_failure_rolls_back_open_transaction(self, ui_mock, project_mock, genre_fn, memory_mock):
        svc = ProjectService(
            project_fn=lambda: project_mock,
            ui=ui_mock,
            safe_commit_fn=MagicMock(return_value=False),
            genre_fn=genre_fn,
            memory_fn=lambda: memory_mock,
        )
        svc._rollback_open_transaction = MagicMock()

        with patch("builtins.input", side_effect=["y"]):
            result = svc.wipe_production_data()

        assert result is False
        svc._rollback_open_transaction.assert_called_once_with(project_mock)
        ui_mock.log.assert_any_call("DB commit failed during production wipe")
