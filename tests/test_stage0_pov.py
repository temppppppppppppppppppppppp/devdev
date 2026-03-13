"""Stage 0 POV and external insert policy selection tests."""

from pathlib import Path
from unittest.mock import patch


class TestPOVSelection:
    def test_pov_options_defined(self):
        from modules.core.stage0 import StageZeroManager

        assert hasattr(StageZeroManager, "POV_OPTIONS")
        assert "1인칭" in StageZeroManager.POV_OPTIONS
        assert "3인칭" in StageZeroManager.POV_OPTIONS
        assert "전지적" in StageZeroManager.POV_OPTIONS
        assert "혼합" in StageZeroManager.POV_OPTIONS
        assert "제한적 허용" in StageZeroManager.EXTERNAL_POV_INSERT_POLICY_OPTIONS

    @patch("builtins.input", side_effect=["1", "1", "1", "1"])
    def test_pov_first_person_selected(self, _mock_input):
        from modules.core.stage0 import StageZeroManager

        mgr = StageZeroManager.__new__(StageZeroManager)
        mgr.genre = ""
        mgr.WORLD_ORIGIN_OPTIONS = StageZeroManager.WORLD_ORIGIN_OPTIONS
        mgr.INCARNATION_TYPES = StageZeroManager.INCARNATION_TYPES
        mgr.POV_OPTIONS = StageZeroManager.POV_OPTIONS
        mgr.EXTERNAL_POV_INSERT_POLICY_OPTIONS = StageZeroManager.EXTERNAL_POV_INSERT_POLICY_OPTIONS

        config = mgr.show_protagonist_config_menu()
        assert config["pov"] == "1인칭"
        assert config["external_pov_insert_policy"] == "금지"

    @patch("builtins.input", side_effect=["1", "1", "2", ""])
    def test_pov_third_person_default_policy_selected(self, _mock_input):
        from modules.core.stage0 import StageZeroManager

        mgr = StageZeroManager.__new__(StageZeroManager)
        mgr.genre = ""
        mgr.WORLD_ORIGIN_OPTIONS = StageZeroManager.WORLD_ORIGIN_OPTIONS
        mgr.INCARNATION_TYPES = StageZeroManager.INCARNATION_TYPES
        mgr.POV_OPTIONS = StageZeroManager.POV_OPTIONS
        mgr.EXTERNAL_POV_INSERT_POLICY_OPTIONS = StageZeroManager.EXTERNAL_POV_INSERT_POLICY_OPTIONS

        config = mgr.show_protagonist_config_menu()
        assert config["pov"] == "3인칭"
        assert config["external_pov_insert_policy"] == "제한적 허용"

    @patch("builtins.input", side_effect=["1", "1", "4", "3"])
    def test_pov_mixed_with_active_external_policy(self, _mock_input):
        from modules.core.stage0 import StageZeroManager

        mgr = StageZeroManager.__new__(StageZeroManager)
        mgr.genre = ""
        mgr.WORLD_ORIGIN_OPTIONS = StageZeroManager.WORLD_ORIGIN_OPTIONS
        mgr.INCARNATION_TYPES = StageZeroManager.INCARNATION_TYPES
        mgr.POV_OPTIONS = StageZeroManager.POV_OPTIONS
        mgr.EXTERNAL_POV_INSERT_POLICY_OPTIONS = StageZeroManager.EXTERNAL_POV_INSERT_POLICY_OPTIONS

        config = mgr.show_protagonist_config_menu()
        assert config["pov"] == "혼합"
        assert config["external_pov_insert_policy"] == "적극 허용"

    @patch("builtins.input", side_effect=["1", "1", "invalid", ""])
    def test_pov_default_on_invalid_input(self, _mock_input):
        from modules.core.stage0 import StageZeroManager

        mgr = StageZeroManager.__new__(StageZeroManager)
        mgr.genre = "investment"
        mgr.WORLD_ORIGIN_OPTIONS = StageZeroManager.WORLD_ORIGIN_OPTIONS
        mgr.INCARNATION_TYPES = StageZeroManager.INCARNATION_TYPES
        mgr.POV_OPTIONS = StageZeroManager.POV_OPTIONS
        mgr.EXTERNAL_POV_INSERT_POLICY_OPTIONS = StageZeroManager.EXTERNAL_POV_INSERT_POLICY_OPTIONS

        config = mgr.show_protagonist_config_menu()
        assert config["pov"] == "3인칭"
        assert config["external_pov_insert_policy"] == "제한적 허용"

    def test_external_pov_menu_strings_are_utf8_clean(self):
        src = Path("modules/core/stage0/__init__.py").read_text(encoding="utf-8")

        assert "[외부 시점 삽입 정책]" in src
        assert "선택 (기본:" in src
        assert "?" not in src
        assert "?좏깮" not in src
