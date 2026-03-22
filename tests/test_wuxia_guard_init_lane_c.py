from modules.core.genre_guards.wuxia_guard import WuxiaGuard


def test_wuxia_guard_init_delegates_helper_family(monkeypatch):
    calls = []

    monkeypatch.setattr(WuxiaGuard, "_load_genre_yaml", lambda self, key: {})

    monkeypatch.setattr(WuxiaGuard, "_init_forbidden_terms", lambda self, cfg: calls.append("forbidden"))
    monkeypatch.setattr(WuxiaGuard, "_init_mandatory_concepts", lambda self, cfg: calls.append("mandatory"))
    monkeypatch.setattr(WuxiaGuard, "_init_realm_constraints", lambda self, cfg: calls.append("realm"))
    monkeypatch.setattr(WuxiaGuard, "_init_injury_action_limits", lambda self, cfg: calls.append("injury"))
    monkeypatch.setattr(WuxiaGuard, "_init_forbidden_modern_patterns", lambda self, cfg: calls.append("modern"))

    WuxiaGuard()

    assert calls == ["forbidden", "mandatory", "realm", "injury", "modern"]


def test_init_forbidden_terms_preserves_fallback_literals():
    guard = WuxiaGuard.__new__(WuxiaGuard)

    WuxiaGuard._init_forbidden_terms(guard, {})

    assert "상태창" in guard.FORBIDDEN_TERMS
    assert "펌핑감" in guard.FORBIDDEN_TERMS


def test_init_forbidden_modern_patterns_normalizes_yaml_dict_entries():
    guard = WuxiaGuard.__new__(WuxiaGuard)
    cfg = {
        "forbidden_modern_patterns": [
            {"pattern": r"\\(10%\\)", "reason": "퍼센트 금지"},
            {"pattern": r"\\(5km\\)", "reason": "거리 금지"},
        ]
    }

    WuxiaGuard._init_forbidden_modern_patterns(guard, cfg)

    assert guard.FORBIDDEN_MODERN_PATTERNS == [(r"\\(10%\\)", "퍼센트 금지"), (r"\\(5km\\)", "거리 금지")]
