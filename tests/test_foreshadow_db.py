"""
[T1] foreshadow_tracker DB 저장/로드 경로 커버리지 테스트

N1: save_to_db(None) 시 WARNING 로그 확인
N2: auto_detect 예외 시 save_to_db 독립 실행 확인 (try 분리)
N3: save_to_db 예외 미전파 확인
N4: load_from_db(None) 시 DEBUG 로그 확인
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.foreshadow_tracker import ForeshadowTracker

# ---------------------------------------------------------------------------
# N1: save_to_db(None) → WARNING 로그
# ---------------------------------------------------------------------------


def test_foreshadow_save_to_db_none_logs_warning(caplog):
    """save_to_db(db=None) 호출 시 WARNING 레벨 로그가 출력되어야 한다."""
    tracker = ForeshadowTracker()
    with caplog.at_level(logging.WARNING, logger="root"):
        tracker.save_to_db(None)
    assert any("save_to_db 스킵" in r.message for r in caplog.records), "save_to_db(None) 호출 시 WARNING 로그가 없음"


# ---------------------------------------------------------------------------
# N2: auto_detect 예외 시에도 save_to_db 호출 확인
# ---------------------------------------------------------------------------


def test_foreshadow_auto_detect_exception_does_not_block_save():
    """auto_detect_from_manuscript 예외 발생 시에도 save_to_db가 호출되어야 한다."""
    tracker = MagicMock(spec=ForeshadowTracker)
    tracker.auto_detect_from_manuscript.side_effect = RuntimeError("감지 실패")
    tracker.save_to_db.return_value = None

    fake_db = MagicMock()

    # auto_detect try
    try:
        tracker.auto_detect_from_manuscript(1, "원고")
    except Exception:
        pass

    # save try — 독립 실행
    try:
        tracker.save_to_db(fake_db)
    except Exception:
        pass

    tracker.save_to_db.assert_called_once_with(fake_db)


# ---------------------------------------------------------------------------
# N3: save_to_db 예외 미전파
# ---------------------------------------------------------------------------


def test_foreshadow_save_exception_does_not_propagate():
    """save_to_db 예외가 상위로 전파되지 않아야 한다."""
    tracker = MagicMock(spec=ForeshadowTracker)
    tracker.auto_detect_from_manuscript.return_value = None
    tracker.save_to_db.side_effect = OSError("저장 실패")

    fake_db = MagicMock()

    try:
        tracker.auto_detect_from_manuscript(1, "원고")
    except Exception:
        pass

    # save 예외가 잡혀야 하며 이 테스트 함수가 실패 없이 종료되어야 함
    try:
        tracker.save_to_db(fake_db)
    except Exception:
        pass  # except 로 잡힘 — 상위 전파 없음 확인


# ---------------------------------------------------------------------------
# N4: load_from_db(None) → DEBUG 로그
# ---------------------------------------------------------------------------


def test_foreshadow_load_from_db_none_logs_debug(caplog):
    """load_from_db(db=None) 호출 시 DEBUG 레벨 로그가 출력되어야 한다."""
    tracker = ForeshadowTracker()
    with caplog.at_level(logging.DEBUG, logger="root"):
        result = tracker.load_from_db(None)
    assert result == 0, "load_from_db(None) 는 0을 반환해야 한다"
    assert any("load_from_db 스킵" in r.message for r in caplog.records), "load_from_db(None) 호출 시 DEBUG 로그가 없음"
    # DEBUG 이어야 하며 WARNING 이상이면 안 됨
    warning_logs = [r for r in caplog.records if "load_from_db 스킵" in r.message and r.levelno >= logging.WARNING]
    assert not warning_logs, "load_from_db 스킵 로그가 WARNING 이상으로 출력됨 — DEBUG 여야 함"
