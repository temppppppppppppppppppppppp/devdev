import inspect

import pytest

from modules.core.genre_guards.actor_guard import ActorGuard
from modules.core.genre_guards.composer_guard import ComposerGuard
from modules.core.genre_guards.cooking_guard import CookingGuard
from modules.core.genre_guards.hunter_guard import HunterGuard
from modules.core.genre_guards.investment_guard import InvestmentGuard
from modules.core.genre_guards.medical_guard import MedicalGuard


INIT_CASES = [
    (ComposerGuard, ["_init_term_sets", "_init_fame_constraints", "_init_activity_rules"]),
    (HunterGuard, ["_init_term_sets", "_init_rank_constraints", "_init_awakening_rules"]),
    (CookingGuard, ["_init_term_sets", "_init_hierarchy_constraints", "_init_business_requirements"]),
    (InvestmentGuard, ["_init_term_sets", "_init_wealth_constraints", "_init_market_constraints"]),
    (ActorGuard, ["_init_term_sets", "_init_fame_constraints", "_init_activity_requirements"]),
    (MedicalGuard, ["_init_term_sets", "_init_doctor_constraints", "_init_surgery_requirements"]),
]


@pytest.mark.parametrize(("guard_cls", "helper_names"), INIT_CASES)
def test_guard_init_delegates_helper_family(monkeypatch, guard_cls, helper_names):
    calls = []
    sentinel_cfg = {}

    monkeypatch.setattr(guard_cls, "_load_genre_yaml", lambda self, key: sentinel_cfg)

    for helper_name in helper_names:
        monkeypatch.setattr(
            guard_cls,
            helper_name,
            lambda self, cfg, _helper_name=helper_name: calls.append((_helper_name, cfg)),
        )

    guard_cls()

    assert calls == [(helper_name, sentinel_cfg) for helper_name in helper_names]


@pytest.mark.parametrize("guard_cls", [case[0] for case in INIT_CASES])
def test_guard_init_loc_stays_bounded(guard_cls):
    assert len(inspect.getsource(guard_cls.__init__).splitlines()) < 15


def test_composer_guard_helper_fallback_literals_remain_intact():
    guard = ComposerGuard.__new__(ComposerGuard)

    ComposerGuard._init_term_sets(guard, {})
    ComposerGuard._init_fame_constraints(guard, {})
    ComposerGuard._init_activity_rules(guard, {})

    assert "레이드" in guard.FORBIDDEN_TERMS
    assert "BPM" in guard.MUSIC_TERMS
    assert guard._fame_hierarchy[-1] == "레전드"
    assert guard._fame_ranges["레전드"][0] == 50_000_000
    assert guard._activity_requirements["정규 앨범"]["tracks"] == 8
    assert guard._realistic_chart["스타"][0] == 1_000_000


def test_hunter_guard_helper_fallback_literals_remain_intact():
    guard = HunterGuard.__new__(HunterGuard)

    HunterGuard._init_term_sets(guard, {})
    HunterGuard._init_rank_constraints(guard, {})
    HunterGuard._init_awakening_rules(guard, {})

    assert "내공" in guard.FORBIDDEN_TERMS
    assert "시스템" in guard.ALLOWED_TERMS
    assert guard._rank_hierarchy[0] == "E"
    assert guard._dungeon_entry_requirements["S급"]["min_party"] == 8
    assert guard._awakening_abilities["완전 각성"]["max_skills"] == 12
    assert guard._default_skill_cooldowns["유니크 스킬"] == 86400


def test_cooking_guard_helper_fallback_literals_remain_intact():
    guard = CookingGuard.__new__(CookingGuard)

    CookingGuard._init_term_sets(guard, {})
    CookingGuard._init_hierarchy_constraints(guard, {})
    CookingGuard._init_business_requirements(guard, {})

    assert "마이야르" in guard.COOKING_TERMS
    assert guard._restaurant_hierarchy[-1] == "미슐랭3스타"
    assert guard._chef_action_limits["수습생"][0] == r"전국.*대회.*우승"
    assert guard._restaurant_requirements["파인다이닝"]["capital"] == 100_000_000
    assert guard._competition_requirements["TV 요리 프로그램"]["reputation"] == 50


def test_investment_guard_helper_fallback_literals_remain_intact():
    guard = InvestmentGuard.__new__(InvestmentGuard)

    InvestmentGuard._init_term_sets(guard, {})
    InvestmentGuard._init_wealth_constraints(guard, {})
    InvestmentGuard._init_market_constraints(guard, {})

    assert "IPO" in guard.FINANCIAL_TERMS
    assert guard._wealth_hierarchy[0] == "무일푼"
    assert guard._wealth_ranges["거부"][0] == 100_000_000_000
    assert guard._investment_requirements["기업 인수"] == 1_000_000_000
    assert guard._realistic_returns["벤처"][1] == 10000


def test_actor_guard_helper_fallback_literals_remain_intact():
    guard = ActorGuard.__new__(ActorGuard)

    ActorGuard._init_term_sets(guard, {})
    ActorGuard._init_fame_constraints(guard, {})
    ActorGuard._init_activity_requirements(guard, {})

    assert "오디션" in guard.ENTERTAINMENT_TERMS
    assert guard._fame_hierarchy[0] == "무명"
    assert guard._status_action_limits["군입대"][0] == r"촬영"
    assert guard._activity_requirements["해외 영화제"]["fame"] == "주연"


def test_medical_guard_helper_fallback_literals_remain_intact():
    guard = MedicalGuard.__new__(MedicalGuard)

    MedicalGuard._init_term_sets(guard, {})
    MedicalGuard._init_doctor_constraints(guard, {})
    MedicalGuard._init_surgery_requirements(guard, {})

    assert "바이탈" in guard.MEDICAL_TERMS
    assert guard._doctor_hierarchy[0] == "의대생"
    assert guard._doctor_action_limits["인턴"][0] == r"독자.*수술"
    assert guard._surgery_requirements["장기 이식"]["doctor_rank"] == "부교수"
