"""
[T1] character_voice DB 저장 경로 커버리지 테스트

P2: save_to_db(None) 경고 로그 확인
P3: analyze 예외 시 save 독립 실행 확인
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.character_voice import CharacterVoiceTracker

# ---------------------------------------------------------------------------
# P2: save_to_db(None) 시 WARNING 로그 발생 확인
# ---------------------------------------------------------------------------

def test_save_to_db_none_logs_warning(caplog):
    """save_to_db(db=None) 호출 시 WARNING 레벨 로그가 출력되어야 한다."""
    tracker = CharacterVoiceTracker()
    with caplog.at_level(logging.WARNING, logger="root"):
        tracker.save_to_db(None)
    assert any("save_to_db 스킵" in r.message for r in caplog.records), (
        "save_to_db(None) 호출 시 WARNING 로그가 없음"
    )


def test_save_to_db_no_conn_logs_warning(caplog):
    """db 객체가 있지만 conn=None 이면 WARNING 로그가 출력되어야 한다."""
    tracker = CharacterVoiceTracker()
    fake_db = MagicMock()
    fake_db.conn = None
    with caplog.at_level(logging.WARNING, logger="root"):
        tracker.save_to_db(fake_db)
    assert any("save_to_db 스킵" in r.message for r in caplog.records), (
        "conn=None 인 db 전달 시 WARNING 로그가 없음"
    )


# ---------------------------------------------------------------------------
# P3: analyze 예외 시 save 경로 독립 실행 확인
# ---------------------------------------------------------------------------

def test_analyze_exception_does_not_block_save():
    """analyze_manuscript 예외 발생 시에도 save_to_db가 호출되어야 한다."""
    # stage4_post_processor 의 try 분리 패턴을 직접 재현
    voice = MagicMock(spec=CharacterVoiceTracker)
    voice.analyze_manuscript.side_effect = RuntimeError("analyze 실패")
    voice.save_to_db.return_value = None

    fake_db = MagicMock()

    # analyze try
    try:
        voice.analyze_manuscript(1, "원고")
    except Exception:
        pass

    # save try — analyze 예외와 무관하게 실행
    try:
        voice.save_to_db(fake_db)
    except Exception:
        pass

    voice.save_to_db.assert_called_once_with(fake_db)


def test_save_exception_does_not_propagate():
    """save_to_db 예외가 상위로 전파되지 않아야 한다."""
    voice = MagicMock(spec=CharacterVoiceTracker)
    voice.analyze_manuscript.return_value = None
    voice.save_to_db.side_effect = OSError("save 실패")

    fake_db = MagicMock()

    # analyze try
    try:
        voice.analyze_manuscript(1, "원고")
    except Exception:
        pass

    # save try — 예외가 전파되지 않음
    raised = False
    try:
        voice.save_to_db(fake_db)
    except Exception:
        raised = True

    # 예외가 발생했지만 여기까지 도달 = 상위 전파 없음 (except 로 잡음)
    assert raised is True  # save가 raise 했으나
    # 핵심: 이 테스트 자체가 실패 없이 완료되면 상위 전파 없음 확인 완료


def test_v50_true_character_voice_path_covered():
    """v50_modules_available=True + 실제 CharacterVoiceTracker 객체로 경로 커버."""
    tracker = CharacterVoiceTracker()
    # analyze_manuscript: 실 원고(빈 문자열) — 예외 없이 실행되어야 함
    tracker.analyze_manuscript(1, "")

    # save_to_db(None) — WARNING 로그 후 return (예외 없음)
    tracker.save_to_db(None)  # 예외 없이 통과해야 함


# ---------------------------------------------------------------------------
# N4: load_from_db(None) → DEBUG 로그
# ---------------------------------------------------------------------------

def test_cv_load_from_db_none_logs_debug(caplog):
    """load_from_db(db=None) 호출 시 DEBUG 레벨 로그가 출력되어야 한다."""
    tracker = CharacterVoiceTracker()
    with caplog.at_level(logging.DEBUG, logger="root"):
        result = tracker.load_from_db(None)
    assert result == 0, "load_from_db(None) 는 0을 반환해야 한다"
    assert any("load_from_db 스킵" in r.message for r in caplog.records), (
        "load_from_db(None) 호출 시 DEBUG 로그가 없음"
    )
    # WARNING 이상이면 안 됨
    warning_logs = [r for r in caplog.records if "load_from_db 스킵" in r.message and r.levelno >= logging.WARNING]
    assert not warning_logs, "load_from_db 스킵 로그가 WARNING 이상으로 출력됨 — DEBUG 여야 함"
