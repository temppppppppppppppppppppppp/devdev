"""[Phase 4B-2] UIService 단위 테스트

추출 대상: _ui_select_bible, _ui_select_treatment, _show_volume_table, _get_int_input
"""

from unittest.mock import MagicMock, patch

import pytest

from modules.core.services.ui_service import UIService


@pytest.fixture
def ui_mock():
    ui = MagicMock()
    ui.log = MagicMock()
    ui.console = MagicMock()
    return ui


@pytest.fixture
def project_mock():
    project = MagicMock()
    project.treatment_path = None
    return project


@pytest.fixture
def svc(ui_mock, project_mock):
    return UIService(ui=ui_mock, project_fn=lambda: project_mock)


# ── get_int_input ────────────────────────────────────────────────


class TestGetIntInput:
    def test_valid_input(self, svc):
        with patch("builtins.input", return_value="5"):
            result = svc.get_int_input("prompt: ", min_val=1, max_val=10)
        assert result == 5

    def test_empty_returns_default(self, svc):
        with patch("builtins.input", return_value=""):
            result = svc.get_int_input("prompt: ", default=7)
        assert result == 7

    def test_out_of_range_retries(self, svc, ui_mock):
        with patch("builtins.input", side_effect=["0", "11", "5"]):
            result = svc.get_int_input("prompt: ", min_val=1, max_val=10)
        assert result == 5
        warning_messages = [call.args[0] for call in ui_mock.log.call_args_list if call.args]
        assert warning_messages.count("⚠️ 최소값은 1입니다.") == 1
        assert warning_messages.count("⚠️ 최대값은 10입니다.") == 1

    def test_non_digit_retries(self, svc, ui_mock):
        with patch("builtins.input", side_effect=["abc", "3"]):
            result = svc.get_int_input("prompt: ", min_val=1, max_val=10)
        assert result == 3
        warning_messages = [call.args[0] for call in ui_mock.log.call_args_list if call.args]
        assert "⚠️ 숫자만 입력 가능합니다." in warning_messages

    def test_exhausted_attempts_returns_default(self, svc):
        with patch("builtins.input", side_effect=["x", "y", "z"]):
            result = svc.get_int_input("prompt: ", default=99, attempts=3)
        assert result == 99


# ── select_bible ─────────────────────────────────────────────────


class TestSelectBible:
    def test_returns_selected_file(self, svc, tmp_path):
        bible_dir = tmp_path / "bible"
        bible_dir.mkdir()
        (bible_dir / "lore1.json").write_text("{}", encoding="utf-8")
        (bible_dir / "lore2.json").write_text("{}", encoding="utf-8")

        with patch("modules.core.services.ui_service.Path", return_value=bible_dir):
            with patch("builtins.input", return_value="2"):
                result = svc.select_bible()
        assert result in ("lore1.json", "lore2.json")

    def test_empty_folder_returns_none(self, svc, tmp_path):
        bible_dir = tmp_path / "bible"
        bible_dir.mkdir()

        with patch("modules.core.services.ui_service.Path", return_value=bible_dir):
            result = svc.select_bible()
        assert result is None


# ── select_treatment ─────────────────────────────────────────────


class TestSelectTreatment:
    def test_returns_selected_file(self, svc, ui_mock, project_mock, tmp_path):
        treat_dir = tmp_path / "treatments"
        treat_dir.mkdir()
        (treat_dir / "plan1.json").write_text("{}", encoding="utf-8")

        with patch("modules.core.services.ui_service.Path", return_value=treat_dir):
            with patch("builtins.input", return_value="1"):
                result = svc.select_treatment()
        assert result == "plan1.json"

    def test_empty_folder_returns_none(self, svc, ui_mock, tmp_path):
        treat_dir = tmp_path / "treatments"
        treat_dir.mkdir()

        with patch("modules.core.services.ui_service.Path", return_value=treat_dir):
            result = svc.select_treatment()
        assert result is None
        ui_mock.log.assert_called()


# ── show_volume_table ────────────────────────────────────────────


class TestShowVolumeTable:
    def test_renders_table(self, svc, ui_mock):
        volumes = [
            {"vol_no": 1, "strategy_doc": "Title Line\nBody", "cider_score": 85},
            {"vol_no": 2, "strategy_doc": {"title": "Dict Title"}, "cider_score": 90},
        ]
        svc.show_volume_table(volumes)
        ui_mock.console.print.assert_called_once()
        table = ui_mock.console.print.call_args.args[0]
        assert table.title == "📊 [V20] 2권 전략 설계 상업성 성적표"

    def test_empty_volumes(self, svc, ui_mock):
        svc.show_volume_table([])
        ui_mock.console.print.assert_called_once()
        table = ui_mock.console.print.call_args.args[0]
        assert table.title == "📊 [V20] 권별 전략 설계 상업성 성적표"

    def test_single_volume_title_is_not_fixed_to_ten(self, svc, ui_mock):
        svc.show_volume_table([{"vol_no": 1, "strategy_doc": "Only Title", "cider_score": 88}])

        ui_mock.console.print.assert_called_once()
        table = ui_mock.console.print.call_args.args[0]
        assert table.title == "📊 [V20] 1권 전략 설계 상업성 성적표"


# ── project_fn None safety ───────────────────────────────────────


class TestNullProject:
    def test_select_treatment_no_project(self, ui_mock, tmp_path):
        svc = UIService(ui=ui_mock, project_fn=lambda: None)
        treat_dir = tmp_path / "treatments"
        treat_dir.mkdir()
        (treat_dir / "plan1.json").write_text("{}", encoding="utf-8")

        with patch("modules.core.services.ui_service.Path", return_value=treat_dir):
            with patch("builtins.input", return_value="1"):
                result = svc.select_treatment()
        assert result == "plan1.json"
