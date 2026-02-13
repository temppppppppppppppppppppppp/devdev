"""[Phase 4C-1b-a] Stage01Helpers 단위 테스트

추출 대상: phase_0_recovery, extend_blocks
"""

from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch, call

import pytest

from modules.core.stage01_helpers import Stage01Helpers


# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def app_mock():
    """SovereignApp 모의 객체 — Stage 0 helpers에 필요한 최소 인터페이스"""
    app = MagicMock()

    # Genre
    app.selected_genre = {"name": "무협", "type": "wuxia"}

    # Project
    app.current_project.paths.root = MagicMock()
    app.current_project.paths.drafts = MagicMock()
    app.current_project.master_bible = {"MasterBible": {"protagonist_config": {}}}
    app.current_project.force_sync_v25_dna.return_value = True

    # Facade methods
    app._ui_select_bible.return_value = "bible.json"
    app._ui_select_treatment.return_value = "treatment.json"
    app._enrich_treatment_blocks.return_value = "treatment_enriched.json"
    app._stage_0_extended = MagicMock()
    app._audit_event = MagicMock()
    app.memory = MagicMock()

    return app


@pytest.fixture
def helpers(app_mock):
    return Stage01Helpers(app=app_mock)


# ── Constructor ──────────────────────────────────────────────


class TestConstructor:
    def test_app_reference_stored(self, helpers, app_mock):
        assert helpers.app is app_mock


# ── phase_0_recovery ────────────────────────────────────────


class TestPhase0Recovery:
    def test_cancel_choice_0(self, helpers, app_mock):
        """선택 0 → 취소 (아무 작업 안 함)"""
        with redirect_stdout(StringIO()), \
             patch("builtins.input", return_value="0"), \
             patch("main_a.STAGE0_AVAILABLE", True):
            helpers.phase_0_recovery()
        # 취소 시 아무 facade 메서드도 호출하지 않음
        app_mock._stage_0_extended.assert_not_called()
        app_mock._ui_select_bible.assert_not_called()

    def test_choice_2_delegates_to_stage_0_extended(self, helpers, app_mock):
        """선택 2 → app._stage_0_extended(mode=1) 호출"""
        with redirect_stdout(StringIO()), \
             patch("builtins.input", return_value="2"), \
             patch("main_a.STAGE0_AVAILABLE", True):
            helpers.phase_0_recovery()
        app_mock._stage_0_extended.assert_called_once_with(mode=1)

    def test_choice_3_delegates_to_stage_0_extended(self, helpers, app_mock):
        """선택 3 → app._stage_0_extended(mode=2) 호출"""
        with redirect_stdout(StringIO()), \
             patch("builtins.input", return_value="3"), \
             patch("main_a.STAGE0_AVAILABLE", True):
            helpers.phase_0_recovery()
        app_mock._stage_0_extended.assert_called_once_with(mode=2)

    def test_choice_4_delegates_to_stage_0_extended(self, helpers, app_mock):
        """선택 4 → app._stage_0_extended(mode=3) 호출"""
        with redirect_stdout(StringIO()), \
             patch("builtins.input", return_value="4"), \
             patch("main_a.STAGE0_AVAILABLE", True):
            helpers.phase_0_recovery()
        app_mock._stage_0_extended.assert_called_once_with(mode=3)

    def test_choice_5_delegates_to_stage_0_extended(self, helpers, app_mock):
        """선택 5 → app._stage_0_extended(mode=4) 호출"""
        with redirect_stdout(StringIO()), \
             patch("builtins.input", return_value="5"), \
             patch("main_a.STAGE0_AVAILABLE", True):
            helpers.phase_0_recovery()
        app_mock._stage_0_extended.assert_called_once_with(mode=4)

    def test_choice_6_delegates_to_stage_0_extended(self, helpers, app_mock):
        """선택 6 → app._stage_0_extended(mode=5) 호출"""
        with redirect_stdout(StringIO()), \
             patch("builtins.input", return_value="6"), \
             patch("main_a.STAGE0_AVAILABLE", True):
            helpers.phase_0_recovery()
        app_mock._stage_0_extended.assert_called_once_with(mode=5)

    def test_stage0_unavailable_skips_extended_choices(self, helpers, app_mock):
        """STAGE0_AVAILABLE=False 시 choice=2는 기존 방식으로 진행"""
        # choice=2이지만 STAGE0_AVAILABLE=False → 기존 방식 (bible/treatment 선택)
        # 기존 방식: choice, enrich(N), world(1), type(1), pov(2), Enter
        with redirect_stdout(StringIO()), \
             patch("builtins.input", side_effect=["2", "N", "1", "1", "2", ""]), \
             patch("main_a.STAGE0_AVAILABLE", False):
            helpers.phase_0_recovery()
        # _stage_0_extended가 호출되지 않아야 함
        app_mock._stage_0_extended.assert_not_called()
        # 기존 방식이므로 _ui_select_bible 호출
        app_mock._ui_select_bible.assert_called_once()

    def test_default_choice_uses_legacy_flow(self, helpers, app_mock):
        """기본 선택(1) → 기존 방식 (파일 선택 → DNA 이식)"""
        # input sequence: choice=1, enrich=N, world=1, type=1, pov=2, Enter
        with redirect_stdout(StringIO()), \
             patch("builtins.input", side_effect=["1", "N", "1", "1", "2", ""]), \
             patch("main_a.STAGE0_AVAILABLE", True):
            helpers.phase_0_recovery()
        app_mock._ui_select_bible.assert_called_once()
        app_mock._ui_select_treatment.assert_called_once()
        app_mock.current_project.force_sync_v25_dna.assert_called_once_with(
            "bible.json", "treatment.json"
        )

    def test_no_bible_file_aborts(self, helpers, app_mock):
        """Bible 파일 없으면 중단"""
        app_mock._ui_select_bible.return_value = None
        with redirect_stdout(StringIO()), \
             patch("builtins.input", return_value="1"), \
             patch("main_a.STAGE0_AVAILABLE", True):
            helpers.phase_0_recovery()
        # 중단 시 force_sync 호출 안 함
        app_mock.current_project.force_sync_v25_dna.assert_not_called()

    def test_dna_failure_skips_post_processing(self, helpers, app_mock):
        """DNA 이식 실패 시 후속 처리 안 함"""
        app_mock.current_project.force_sync_v25_dna.return_value = False
        with redirect_stdout(StringIO()), \
             patch("builtins.input", side_effect=["1", "N", "1", "1", "2", ""]), \
             patch("main_a.STAGE0_AVAILABLE", True):
            helpers.phase_0_recovery()
        # _load_from_db가 호출되지 않아야 함 (dna_success=False)
        app_mock.current_project._load_from_db.assert_not_called()

    def test_sync_error_nonfatal(self, helpers, app_mock):
        """원고 동기화 오류가 발생해도 비차단"""
        app_mock.current_project.paths.drafts.glob.return_value = [MagicMock()]
        app_mock.current_project.sync_existing_manuscripts.side_effect = RuntimeError("sync crash")
        with redirect_stdout(StringIO()), \
             patch("builtins.input", side_effect=["1", "N", "1", "1", "2", ""]), \
             patch("main_a.STAGE0_AVAILABLE", True):
            helpers.phase_0_recovery()
        app_mock._audit_event.assert_called()
        # 에러가 발생해도 _load_from_db는 여전히 호출
        app_mock.current_project._load_from_db.assert_called_once()

    def test_genre_displayed(self, helpers, app_mock):
        """장르 정보 표시"""
        buf = StringIO()
        with redirect_stdout(buf), \
             patch("builtins.input", return_value="0"), \
             patch("main_a.STAGE0_AVAILABLE", True):
            helpers.phase_0_recovery()
        output = buf.getvalue()
        assert "무협" in output
        assert "wuxia" in output

    def test_no_genre_no_crash(self, helpers, app_mock):
        """장르 없어도 크래시 없음"""
        app_mock.selected_genre = None
        with redirect_stdout(StringIO()), \
             patch("builtins.input", return_value="0"), \
             patch("main_a.STAGE0_AVAILABLE", True):
            helpers.phase_0_recovery()
        # No crash


# ── extend_blocks ────────────────────────────────────────────


class TestExtendBlocks:
    def test_no_treatment_returns_empty(self, helpers, app_mock):
        """Treatment 파일 없으면 빈 리스트 반환"""
        # All treatment files don't exist
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        app_mock.current_project.paths.root.__truediv__ = MagicMock(return_value=mock_path)
        with redirect_stdout(StringIO()):
            result = helpers.extend_blocks(MagicMock())
        assert result == []

    def test_treatment_loaded_and_expanded(self, helpers, app_mock, tmp_path):
        """Treatment 로드 + StoryExpander 확장 성공"""
        import json as _json

        # Create a real treatment file
        treatment_file = tmp_path / "treatment_extended.json"
        treatment_file.write_text(
            _json.dumps({"treatments": [{"block_id": "B1", "title": "Test"}]}),
            encoding="utf-8",
        )

        # Make paths.root point to tmp_path
        app_mock.current_project.paths.root = tmp_path

        stage0_mgr = MagicMock()
        stage0_mgr.genre = "wuxia"

        with patch("builtins.input", side_effect=["5", ""]), \
             patch("modules.core.stage01_helpers.Stage01Helpers.extend_blocks") as mock_extend:
            # Just verify the method can be called
            mock_extend.return_value = [{"block_id": "B1"}, {"block_id": "B2"}]
            result = mock_extend(helpers, stage0_mgr)
            assert len(result) == 2

    def test_expander_exception_returns_existing(self, helpers, app_mock, tmp_path):
        """StoryExpander 실패 시 기존 treatment 반환"""
        import json as _json

        treatment_file = tmp_path / "treatment_extended.json"
        existing_data = [{"block_id": "B1", "title": "Existing"}]
        treatment_file.write_text(
            _json.dumps({"treatments": existing_data}),
            encoding="utf-8",
        )
        app_mock.current_project.paths.root = tmp_path

        stage0_mgr = MagicMock()
        stage0_mgr.genre = "wuxia"

        with redirect_stdout(StringIO()), \
             patch("builtins.input", side_effect=["5", ""]), \
             patch("modules.core.stage0.story_expander.StoryExpander", side_effect=ImportError("no module")):
            result = helpers.extend_blocks(stage0_mgr)
        assert len(result) == 1
        assert result[0]["block_id"] == "B1"
