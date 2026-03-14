from __future__ import annotations

import pytest

from modules.core import logger as logger_module


def _reset_studio_logger() -> None:
    instance = logger_module._studio_logger or logger_module.StudioLogger._instance
    if instance is not None:
        try:
            instance.close()
        except Exception:
            pass
    logger_module._studio_logger = None
    logger_module.StudioLogger._instance = None


@pytest.fixture(autouse=True)
def reset_studio_logger():
    _reset_studio_logger()
    yield
    _reset_studio_logger()


def test_retarget_copies_boot_prefix_to_project_log_and_preserves_root_log(tmp_path):
    root_log_dir = tmp_path / "logs"
    project_log_dir = tmp_path / "projects" / "demo" / "logs"
    studio_logger = logger_module.init_logger(log_dir=root_log_dir, session_name="unit_continuity")

    studio_logger.info("[System] bootstrap ready")
    studio_logger.get_logger("UI").info("[Phase 0] project booting")

    root_log_path = root_log_dir / "session_unit_continuity.log"
    root_boot_text = root_log_path.read_text(encoding="utf-8")

    studio_logger.retarget(project_log_dir)
    studio_logger.info("[Runtime] project-bound line")

    project_log_path = project_log_dir / "session_unit_continuity.log"
    project_log_text = project_log_path.read_text(encoding="utf-8")
    root_log_text = root_log_path.read_text(encoding="utf-8")

    assert "[System] bootstrap ready" in root_boot_text
    assert project_log_text.startswith(root_boot_text)
    assert "[Phase 0] project booting" in project_log_text
    assert "[Runtime] project-bound line" in project_log_text
    assert "[Runtime] project-bound line" not in root_log_text
    assert root_log_text == root_boot_text


def test_root_boot_log_survives_without_retarget(tmp_path):
    root_log_dir = tmp_path / "logs"
    studio_logger = logger_module.init_logger(log_dir=root_log_dir, session_name="early_boot")

    studio_logger.info("[System] bootstrap ready")

    root_log_path = root_log_dir / "session_early_boot.log"
    root_log_text = root_log_path.read_text(encoding="utf-8")

    assert root_log_path.exists()
    assert "[System] bootstrap ready" in root_log_text
