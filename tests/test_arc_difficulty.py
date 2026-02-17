"""[Item4] PassRateMonitor arc difficulty tests."""

from modules.core.pass_rate_monitor import PassRateMonitor


def test_get_arc_difficulty_unknown_when_no_records(tmp_path):
    monitor = PassRateMonitor(str(tmp_path))

    result = monitor.get_arc_difficulty(arc_no=3)

    assert result["arc_no"] == 3
    assert result["difficulty"] == "unknown"
    assert result["avg_attempts"] == 0.0
    assert result["hard_episodes"] == []


def test_get_arc_difficulty_easy(tmp_path):
    monitor = PassRateMonitor(str(tmp_path))

    # Arc 2, episode 11/12: each one-pass
    monitor.record_attempt(stage=4, episode=11, arc=2, attempt_num=1, success=True)
    monitor.record_attempt(stage=4, episode=12, arc=2, attempt_num=1, success=True)

    result = monitor.get_arc_difficulty(arc_no=2)

    assert result["difficulty"] == "easy"
    assert result["avg_attempts"] == 1.0
    assert result["hard_episodes"] == []


def test_get_arc_difficulty_hard_and_hard_episodes(tmp_path):
    monitor = PassRateMonitor(str(tmp_path))

    # ep21: 4 attempts, ep22: 3 attempts, ep23: 3 attempts -> avg 3.3 => hard
    for attempt in range(1, 5):
        monitor.record_attempt(stage=4, episode=21, arc=3, attempt_num=attempt, success=(attempt == 4))
    for attempt in range(1, 4):
        monitor.record_attempt(stage=4, episode=22, arc=3, attempt_num=attempt, success=(attempt == 3))
    for attempt in range(1, 4):
        monitor.record_attempt(stage=4, episode=23, arc=3, attempt_num=attempt, success=(attempt == 3))

    result = monitor.get_arc_difficulty(arc_no=3)

    assert result["difficulty"] == "hard"
    assert result["avg_attempts"] == 3.3
    assert result["hard_episodes"] == [21, 22, 23]
