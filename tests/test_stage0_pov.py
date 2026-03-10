"""[D-1] Stage 0 POV 선택 메뉴 테스트."""

from unittest.mock import patch


class TestPOVSelection:
    """Stage 0 POV 선택 메뉴 검증."""

    def test_pov_options_defined(self):
        """POV_OPTIONS 상수가 4개 시점을 포함."""
        from modules.core.stage0 import StageZeroManager

        assert hasattr(StageZeroManager, "POV_OPTIONS")
        assert "1인칭" in StageZeroManager.POV_OPTIONS
        assert "3인칭" in StageZeroManager.POV_OPTIONS
        assert "전지적" in StageZeroManager.POV_OPTIONS
        assert "혼합" in StageZeroManager.POV_OPTIONS

    @patch("builtins.input", side_effect=["1", "1", "1"])  # world, type, pov
    def test_pov_first_person_selected(self, _mock_input):
        """1인칭 선택 시 config에 pov='1인칭' 포함."""
        from modules.core.stage0 import StageZeroManager

        mgr = StageZeroManager.__new__(StageZeroManager)
        mgr.WORLD_ORIGIN_OPTIONS = StageZeroManager.WORLD_ORIGIN_OPTIONS
        mgr.INCARNATION_TYPES = StageZeroManager.INCARNATION_TYPES
        mgr.POV_OPTIONS = StageZeroManager.POV_OPTIONS

        config = mgr.show_protagonist_config_menu()
        assert config["pov"] == "1인칭"

    @patch("builtins.input", side_effect=["1", "1", "2"])  # world, type, pov=3인칭
    def test_pov_third_person_selected(self, _mock_input):
        """3인칭 선택 시 config에 pov='3인칭' 포함."""
        from modules.core.stage0 import StageZeroManager

        mgr = StageZeroManager.__new__(StageZeroManager)
        mgr.WORLD_ORIGIN_OPTIONS = StageZeroManager.WORLD_ORIGIN_OPTIONS
        mgr.INCARNATION_TYPES = StageZeroManager.INCARNATION_TYPES
        mgr.POV_OPTIONS = StageZeroManager.POV_OPTIONS

        config = mgr.show_protagonist_config_menu()
        assert config["pov"] == "3인칭"

    @patch("builtins.input", side_effect=["1", "1", "4"])  # world, type, pov=혼합
    def test_pov_mixed_selected(self, _mock_input):
        """혼합 선택 시 config에 pov='혼합' 포함."""
        from modules.core.stage0 import StageZeroManager

        mgr = StageZeroManager.__new__(StageZeroManager)
        mgr.WORLD_ORIGIN_OPTIONS = StageZeroManager.WORLD_ORIGIN_OPTIONS
        mgr.INCARNATION_TYPES = StageZeroManager.INCARNATION_TYPES
        mgr.POV_OPTIONS = StageZeroManager.POV_OPTIONS

        config = mgr.show_protagonist_config_menu()
        assert config["pov"] == "혼합"

    @patch("builtins.input", side_effect=["1", "1", "invalid"])  # 잘못된 입력 → 기본값
    def test_pov_default_on_invalid_input(self, _mock_input):
        """잘못된 입력 시 기본값 '3인칭'."""
        from modules.core.stage0 import StageZeroManager

        mgr = StageZeroManager.__new__(StageZeroManager)
        mgr.WORLD_ORIGIN_OPTIONS = StageZeroManager.WORLD_ORIGIN_OPTIONS
        mgr.INCARNATION_TYPES = StageZeroManager.INCARNATION_TYPES
        mgr.POV_OPTIONS = StageZeroManager.POV_OPTIONS

        config = mgr.show_protagonist_config_menu()
        assert config["pov"] == "3인칭"
