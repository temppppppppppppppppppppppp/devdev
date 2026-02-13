"""[Phase 4B-3] ProjectService 단위 테스트

추출 대상: reset_stage_2, rewind_stage_2, rollback_episode, wipe_production_data
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call

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
        {"arc_no": 1, "title": "Arc 1"},
        {"arc_no": 2, "title": "Arc 2"},
        {"arc_no": 3, "title": "Arc 3"},
    ]
    project.get_latest_episode_number.return_value = 6  # latest_ep = 5
    project.paths.drafts = MagicMock()
    project.paths.drafts.glob.return_value = []
    project.db.cursor = MagicMock()
    project.db.conn = MagicMock()
    project.db.delete_episode_bibles_after.return_value = 2
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
    mem.collection = MagicMock()
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


# ── reset_stage_2 ────────────────────────────────────────────


class TestResetStage2:
    def test_confirm_y_deletes_arcs(self, svc, project_mock, safe_commit_mock, ui_mock):
        with patch("builtins.input", side_effect=["y", ""]):
            svc.reset_stage_2()
        project_mock.db.cursor.execute.assert_called_once_with(
            "DELETE FROM anchors WHERE key = 'arcs'"
        )
        safe_commit_mock.assert_called_once()
        assert project_mock.arcs == []

    def test_confirm_n_does_nothing(self, svc, project_mock, safe_commit_mock):
        with patch("builtins.input", return_value="n"):
            svc.reset_stage_2()
        project_mock.db.cursor.execute.assert_not_called()
        safe_commit_mock.assert_not_called()


# ── rewind_stage_2 ───────────────────────────────────────────


class TestRewindStage2:
    def test_no_arcs_returns_early(self, ui_mock, safe_commit_mock, genre_fn, memory_mock):
        project = MagicMock()
        project.arcs = []
        svc = ProjectService(
            project_fn=lambda: project,
            ui=ui_mock,
            safe_commit_fn=safe_commit_mock,
            genre_fn=genre_fn,
            memory_fn=lambda: memory_mock,
        )
        svc.rewind_stage_2()
        ui_mock.log.assert_any_call("❌ 삭제할 아크 데이터가 없습니다.")

    def test_non_digit_returns_early(self, svc, ui_mock):
        with patch("builtins.input", return_value="abc"):
            svc.rewind_stage_2()
        ui_mock.log.assert_any_call("❌ 숫자만 입력 가능합니다.")

    def test_confirm_y_deletes_from_target(self, svc, project_mock, ui_mock):
        # input: target=2, confirm=y, Enter
        with patch("builtins.input", side_effect=["2", "y", ""]):
            svc.rewind_stage_2()
        # arcs should only keep arc_no < 2, i.e., arc_no=1
        assert project_mock.arcs == [{"arc_no": 1, "title": "Arc 1"}]
        project_mock.save_v20_anchor.assert_called_once()

    def test_confirm_n_preserves_arcs(self, svc, project_mock):
        original_arcs = list(project_mock.arcs)
        with patch("builtins.input", side_effect=["2", "n"]):
            svc.rewind_stage_2()
        assert project_mock.arcs == original_arcs


# ── rollback_episode ─────────────────────────────────────────


class TestRollbackEpisode:
    def test_no_episodes_returns_early(self, ui_mock, safe_commit_mock, genre_fn, memory_mock):
        project = MagicMock()
        project.get_latest_episode_number.return_value = 1  # latest_ep = 0
        svc = ProjectService(
            project_fn=lambda: project,
            ui=ui_mock,
            safe_commit_fn=safe_commit_mock,
            genre_fn=genre_fn,
            memory_fn=lambda: memory_mock,
        )
        svc.rollback_episode()
        ui_mock.log.assert_any_call("❌ 롤백할 에피소드가 없습니다.")

    def test_non_digit_returns_early(self, svc, ui_mock):
        with patch("builtins.input", return_value="abc"):
            svc.rollback_episode()
        ui_mock.log.assert_any_call("❌ 숫자만 입력 가능합니다.")

    def test_out_of_range_returns_early(self, svc, ui_mock):
        with patch("builtins.input", return_value="99"):
            svc.rollback_episode()
        ui_mock.log.assert_any_call("❌ 1~5 범위 내에서 입력해주세요.")

    def test_cancel_returns_early(self, svc, ui_mock):
        with patch("builtins.input", side_effect=["3", "n"]):
            svc.rollback_episode()
        ui_mock.log.assert_any_call("❌ 취소되었습니다.")

    def test_confirm_y_executes_rollback(self, svc, project_mock, safe_commit_mock, ui_mock):
        # No HUD data (cursor returns None for state_logs)
        project_mock.db.cursor.fetchone.return_value = None
        with patch("builtins.input", side_effect=["3", "y", ""]):
            svc.rollback_episode()
        safe_commit_mock.assert_called_once()
        project_mock._load_from_db.assert_called_once()

    def test_rollback_memory_none(self, ui_mock, safe_commit_mock, genre_fn):
        """벡터 DB 없어도 롤백 성공"""
        project = MagicMock()
        project.get_latest_episode_number.return_value = 4  # latest_ep = 3
        project.db.cursor.fetchone.return_value = None
        project.paths.drafts.glob.return_value = []
        project.db.delete_episode_bibles_after.return_value = 0
        svc = ProjectService(
            project_fn=lambda: project,
            ui=ui_mock,
            safe_commit_fn=safe_commit_mock,
            genre_fn=genre_fn,
            memory_fn=lambda: None,
        )
        with patch("builtins.input", side_effect=["2", "y", ""]):
            svc.rollback_episode()
        # Should still succeed despite no memory
        assert any("벡터 소거 생략" in str(c) for c in ui_mock.log.call_args_list) or \
               any("Success" in str(c) for c in ui_mock.log.call_args_list)


# ── wipe_production_data ─────────────────────────────────────


class TestWipeProductionData:
    def test_confirm_n_does_nothing(self, svc, project_mock):
        with patch("builtins.input", return_value="n"):
            svc.wipe_production_data()
        project_mock.db.cursor.execute.assert_not_called()

    def test_confirm_y_deletes_all_production(self, svc, project_mock, ui_mock):
        with patch("builtins.input", side_effect=["y", ""]):
            svc.wipe_production_data()
        # Check that multiple DELETE statements were executed
        execute_calls = project_mock.db.cursor.execute.call_args_list
        assert len(execute_calls) >= 7  # 7 tables + 1 UPDATE seeds
        project_mock.db.conn.commit.assert_called_once()

    def test_wipe_cleans_files(self, svc, project_mock, tmp_path):
        drafts = tmp_path / "drafts"
        drafts.mkdir()
        (drafts / "1.txt").write_text("test", encoding="utf-8")
        (drafts / "2.txt").write_text("test", encoding="utf-8")
        project_mock.paths.drafts = drafts
        with patch("builtins.input", side_effect=["y", ""]):
            svc.wipe_production_data()
        remaining = list(drafts.glob("*.txt"))
        assert len(remaining) == 0

    def test_wipe_vectordb_failure_nonfatal(self, ui_mock, safe_commit_mock, genre_fn):
        """벡터 DB 삭제 실패해도 비차단"""
        project = MagicMock()
        project.paths.drafts.glob.return_value = []
        memory = MagicMock()
        memory.collection.delete.side_effect = RuntimeError("ChromaDB error")
        svc = ProjectService(
            project_fn=lambda: project,
            ui=ui_mock,
            safe_commit_fn=safe_commit_mock,
            genre_fn=genre_fn,
            memory_fn=lambda: memory,
        )
        with patch("builtins.input", side_effect=["y", ""]):
            svc.wipe_production_data()
        # Should still complete despite vectordb failure
        assert any("VectorDB" in str(c) for c in ui_mock.log.call_args_list)


# ── constructor ──────────────────────────────────────────────


class TestConstructor:
    def test_lazy_project_fn(self, ui_mock, safe_commit_mock, genre_fn, memory_mock):
        """project_fn is called lazily, not at construction time"""
        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return MagicMock()

        svc = ProjectService(
            project_fn=counting_fn,
            ui=ui_mock,
            safe_commit_fn=safe_commit_mock,
            genre_fn=genre_fn,
            memory_fn=lambda: memory_mock,
        )
        assert call_count == 0  # Not called at init
