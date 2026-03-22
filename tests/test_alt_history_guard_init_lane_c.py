import inspect

from modules.core.genre_guards.alt_history_guard import AltHistoryGuard


def test_alt_history_guard_init_delegates_helper_family(monkeypatch):
    calls = []
    sentinel_cfg = {}

    monkeypatch.setattr(AltHistoryGuard, "_load_genre_yaml", lambda self, key: sentinel_cfg)
    monkeypatch.setattr(AltHistoryGuard, "_init_term_sets", lambda self, cfg: calls.append(("terms", cfg)))
    monkeypatch.setattr(AltHistoryGuard, "_init_hierarchy_constraints", lambda self, cfg: calls.append(("hierarchy", cfg)))
    monkeypatch.setattr(AltHistoryGuard, "_init_action_limits", lambda self, cfg: calls.append(("limits", cfg)))
    monkeypatch.setattr(AltHistoryGuard, "_init_activity_requirements", lambda self: calls.append(("activity", None)))

    AltHistoryGuard()

    assert calls == [
        ("terms", sentinel_cfg),
        ("hierarchy", sentinel_cfg),
        ("limits", sentinel_cfg),
        ("activity", None),
    ]


def test_alt_history_guard_helper_fallback_literals_remain_intact():
    guard = AltHistoryGuard.__new__(AltHistoryGuard)

    AltHistoryGuard._init_term_sets(guard, {})
    AltHistoryGuard._init_hierarchy_constraints(guard, {})
    AltHistoryGuard._init_action_limits(guard, {})
    AltHistoryGuard._init_activity_requirements(guard)

    assert "스마트폰" in guard.FORBIDDEN_TERMS
    assert "영의정" in guard.JOSEON_TERMS
    assert "유교적 세계관과 예법·존비의 준수" in guard.MANDATORY_CONCEPTS
    assert guard._court_rank_hierarchy[0] == "종9품"
    assert guard._social_hierarchy[-1] == "왕족"
    assert guard._class_action_limits["천민"] == [r"과거.*응시", r"관직.*임명", r"조정.*참석", r"상소.*올"]
    assert guard._rank_action_limits["종9품"] == [r"왕.*독대", r"대신.*탄핵", r"군병.*동원"]
    assert guard._status_action_limits["상중"] == [r"관직.*수행", r"연회.*참석", r"혼인", r"과거.*응시"]
    assert guard._activity_requirements["외교 사절"] == {"court_rank": "정3품", "royal_mandate": True}


def test_alt_history_guard_init_loc_stays_below_180():
    assert len(inspect.getsource(AltHistoryGuard.__init__).splitlines()) < 180
