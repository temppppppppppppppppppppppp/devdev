"""[L3] Stage readiness truthiness checks for StudioSystem.check_v20_readiness()."""

from unittest.mock import MagicMock

import pytest

from modules.core.db_manager import DBManager
from modules.core.system import StudioSystem


@pytest.fixture
def studio_system(tmp_path):
    """StudioSystem + mock project + real DBManager."""
    db = DBManager(tmp_path / "stage_status_test.db")
    project = MagicMock()
    project.db = db

    sys_obj = StudioSystem.__new__(StudioSystem)
    sys_obj.project = project
    yield sys_obj
    db.close()


class TestCheckV20Readiness:
    def test_empty_db_all_false(self, studio_system):
        """Missing anchors should all be False."""
        status = studio_system.check_v20_readiness()
        assert status["Stage 0 (Bible)"] is False
        assert status["Stage 1 (Volumes)"] is False
        assert status["Stage 2 (Arcs)"] is False

    def test_empty_dict_is_false(self, studio_system):
        """Empty dict should be treated as not ready."""
        studio_system.project.db.save_anchor("bible", {})
        status = studio_system.check_v20_readiness()
        assert status["Stage 0 (Bible)"] is False

    def test_empty_list_is_false(self, studio_system):
        """Empty list should be treated as not ready."""
        studio_system.project.db.save_anchor("arcs", [])
        status = studio_system.check_v20_readiness()
        assert status["Stage 2 (Arcs)"] is False

    def test_real_data_is_true(self, studio_system):
        """Real anchor payloads should be treated as ready."""
        studio_system.project.db.save_anchor("bible", {"MasterBible": {"ProjectData": {}}})
        studio_system.project.db.save_anchor("volumes", [{"vol_no": 1}])
        studio_system.project.db.save_anchor("arcs", [{"arc_no": 1}])

        status = studio_system.check_v20_readiness()
        assert status["Stage 0 (Bible)"] is True
        assert status["Stage 1 (Volumes)"] is True
        assert status["Stage 2 (Arcs)"] is True
