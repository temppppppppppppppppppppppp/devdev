"""
[Sweep9-D] 장르 가드 확장 테스트 — 미테스트 8개 장르 커버리지
기존 test_genre_guard.py(WuxiaGuard)를 보완합니다.
"""

import pytest

from modules.core.genre_guards.actor_guard import ActorGuard
from modules.core.genre_guards.alt_history_guard import AltHistoryGuard
from modules.core.genre_guards.composer_guard import ComposerGuard
from modules.core.genre_guards.cooking_guard import CookingGuard
from modules.core.genre_guards.fantasy_guard import FantasyGuard
from modules.core.genre_guards.investment_guard import InvestmentGuard
from modules.core.genre_guards.medical_guard import MedicalGuard
from modules.core.genre_guards.sports_guard import SportsGuard

GUARD_CLASSES = [
    (InvestmentGuard, "투자물(INVESTMENT)"),
    (FantasyGuard, "판타지"),
    (CookingGuard, "요리물(COOKING)"),
    (AltHistoryGuard, "대체역사물(ALT_HISTORY)"),
    (ComposerGuard, "작곡가물(COMPOSER)"),
    (ActorGuard, "배우물(ACTOR)"),
    (MedicalGuard, "의학물(MEDICAL)"),
    (SportsGuard, "스포츠물(SPORTS)"),
]


@pytest.fixture(params=GUARD_CLASSES, ids=[c[1] for c in GUARD_CLASSES])
def guard_and_name(request):
    cls, expected_name = request.param
    return cls(), expected_name


class TestGuardInstantiation:
    """가드가 에러 없이 생성되는지 확인"""

    def test_instantiation(self, guard_and_name):
        guard, _ = guard_and_name
        assert guard is not None

    def test_genre_name(self, guard_and_name):
        guard, expected_name = guard_and_name
        assert guard.get_genre_name() == expected_name

    def test_has_forbidden_terms(self, guard_and_name):
        guard, _ = guard_and_name
        assert isinstance(guard.FORBIDDEN_TERMS, list)
        assert len(guard.FORBIDDEN_TERMS) > 0


class TestConvertToNumeric:
    """BaseGuard.convert_to_numeric 기본 동작 (모든 가드 공통)"""

    def test_none_returns_zero(self, guard_and_name):
        guard, _ = guard_and_name
        assert guard.convert_to_numeric(None) == 0.0

    def test_int_passthrough(self, guard_and_name):
        guard, _ = guard_and_name
        assert guard.convert_to_numeric(42) == 42.0

    def test_arabic_string(self, guard_and_name):
        guard, _ = guard_and_name
        assert guard.convert_to_numeric("100") == 100.0

    def test_zero_keywords(self, guard_and_name):
        guard, _ = guard_and_name
        for word in ["영", "없음", "소멸"]:
            assert guard.convert_to_numeric(word) == 0.0

    def test_korean_numeral(self, guard_and_name):
        guard, _ = guard_and_name
        assert guard.convert_to_numeric("삼") == 3.0

    def test_ten_korean(self, guard_and_name):
        guard, _ = guard_and_name
        assert guard.convert_to_numeric("이십") == 20.0


class TestValidateV20Manuscript:
    """BaseGuard.validate_v20_manuscript 기본 검증"""

    def test_clean_text_returns_dict(self, guard_and_name):
        guard, _ = guard_and_name
        result = guard.validate_v20_manuscript("그는 조용히 걸었다. 바람이 불었다.")
        assert isinstance(result, dict)
        assert "is_pure" in result
        assert "issues" in result

    def test_forbidden_term_detected(self, guard_and_name):
        guard, _ = guard_and_name
        if not guard.FORBIDDEN_TERMS:
            pytest.skip("금기어 없음")
        forbidden = guard.FORBIDDEN_TERMS[0]
        result = guard.validate_v20_manuscript(f"그는 {forbidden}을 사용했다.")
        assert result["is_pure"] is False
        assert any(forbidden in issue for issue in result["issues"])


class TestRunDeepValidation:
    """run_deep_validation 반환 구조 검증"""

    def test_returns_dict(self, guard_and_name):
        guard, _ = guard_and_name
        result = guard.run_deep_validation("그는 조용히 걸었다. 바람이 불었다.")
        assert isinstance(result, dict)

    def test_has_expected_keys(self, guard_and_name):
        guard, _ = guard_and_name
        result = guard.run_deep_validation("그는 조용히 걸었다. 바람이 불었다.")
        assert "has_critical" in result
        assert "violations" in result
        assert "summary" in result
        assert "feedback" in result
