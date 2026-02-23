"""DB 효율화 save_to_db 트랜잭션 롤백 회귀 테스트."""

import threading

from modules.core.character_voice import (
    CharacterVoiceProfile,
    CharacterVoiceTracker,
    VoicePattern,
    VoiceStyle,
)
from modules.core.foreshadow_tracker import ForeshadowCategory, ForeshadowTracker


class _FailingConn:
    def __init__(self, fail_on_call: int):
        self.fail_on_call = fail_on_call
        self.calls = 0
        self.committed = False
        self.rolled_back = False

    def execute(self, *_args, **_kwargs):
        self.calls += 1
        if self.calls >= self.fail_on_call:
            raise RuntimeError("forced execute failure")
        return None

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class _FakeDB:
    def __init__(self, conn):
        self.conn = conn
        self._lock = threading.RLock()


def test_character_voice_save_to_db_rolls_back_on_error():
    tracker = CharacterVoiceTracker()
    tracker.profiles["A"] = CharacterVoiceProfile(name="A", style=VoiceStyle.INFORMAL, pattern=VoicePattern())
    tracker.profiles["B"] = CharacterVoiceProfile(name="B", style=VoiceStyle.FORMAL, pattern=VoicePattern())

    conn = _FailingConn(fail_on_call=2)  # 두 번째 INSERT에서 실패
    db = _FakeDB(conn)

    tracker.save_to_db(db)

    assert conn.rolled_back is True
    assert conn.committed is False


def test_foreshadow_save_to_db_rolls_back_on_error():
    tracker = ForeshadowTracker()
    tracker.plant(ep_num=1, hook="비밀 편지", category=ForeshadowCategory.MYSTERY)
    tracker.plant(ep_num=2, hook="봉인된 검", category=ForeshadowCategory.CHEKHOV)

    conn = _FailingConn(fail_on_call=3)  # DELETE + 첫 INSERT 후, 두 번째 INSERT에서 실패
    db = _FakeDB(conn)

    tracker.save_to_db(db)

    assert conn.rolled_back is True
    assert conn.committed is False
