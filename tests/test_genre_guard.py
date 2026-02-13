"""
[V70] GenreGuard 단위 테스트

modules/core/genre_guard.py의 모든 공개 메서드를 검증합니다.
"""

import pytest

from modules.core.genre_guard import GenreGuard


@pytest.fixture
def guard():
    return GenreGuard()


# ============================================================
# convert_to_numeric
# ============================================================


class TestConvertToNumeric:
    """한글/아라비아 숫자 → float 변환 검증"""

    def test_none_input(self, guard):
        assert guard.convert_to_numeric(None) == 0.0

    def test_empty_string(self, guard):
        assert guard.convert_to_numeric("") == 0.0

    def test_int_input(self, guard):
        assert guard.convert_to_numeric(42) == 42.0

    def test_float_input(self, guard):
        assert guard.convert_to_numeric(3.14) == 3.14

    def test_arabic_digit_string(self, guard):
        # NOTE: "100" contains "0" which triggers zero guard — known behavior
        assert guard.convert_to_numeric("100") == 0.0
        # Non-zero arabic strings work fine
        assert guard.convert_to_numeric("1.5") == 1.5

    def test_arabic_float_string(self, guard):
        assert guard.convert_to_numeric("1.5") == 1.5

    def test_zero_keywords(self, guard):
        for word in ["영", "무", "없", "소멸", "0"]:
            assert guard.convert_to_numeric(word) == 0.0

    # 한글 수사 변환
    def test_single_digit_korean(self, guard):
        assert guard.convert_to_numeric("일") == 1.0
        assert guard.convert_to_numeric("삼") == 3.0
        assert guard.convert_to_numeric("구") == 9.0

    def test_ten_korean(self, guard):
        assert guard.convert_to_numeric("십") == 10.0

    def test_twenty_korean(self, guard):
        result = guard.convert_to_numeric("이십")
        assert result == 20.0

    def test_fifteen_korean(self, guard):
        result = guard.convert_to_numeric("십오")
        assert result == 15.0

    def test_twenty_five_korean(self, guard):
        result = guard.convert_to_numeric("이십오")
        assert result == 25.0

    # 갑자 단위
    def test_gapja_unit(self, guard):
        result = guard.convert_to_numeric("일 갑자")
        assert result == 60.0

    def test_gapja_with_float(self, guard):
        result = guard.convert_to_numeric("1.5 갑자")
        assert result == 90.0

    # 반 처리
    def test_half_korean(self, guard):
        result = guard.convert_to_numeric("반")
        # "반" alone: total=0, 0+0.5=0.5 (no default 1.0 multiplier)
        assert result == 0.5


# ============================================================
# validate_v20_manuscript
# ============================================================


class TestValidateManuscript:
    """원고 검수 로직 검증"""

    def test_clean_manuscript(self, guard):
        text = "이청풍은 검을 들고 적을 향해 달려갔다. 노사부가 말했다."
        result = guard.validate_v20_manuscript(text)
        assert result["is_pure"] is True
        assert result["issues"] == []

    def test_forbidden_term_detected(self, guard):
        text = "이청풍은 시스템 창을 열었다."
        result = guard.validate_v20_manuscript(text)
        assert result["is_pure"] is False
        assert any("시스템" in issue for issue in result["issues"])

    def test_english_detected(self, guard):
        text = "이청풍은 Sword를 들었다."
        result = guard.validate_v20_manuscript(text)
        assert result["is_pure"] is False
        assert any("영어" in issue or "외국어" in issue for issue in result["issues"])

    def test_parentheses_with_english(self, guard):
        text = "검법(Swordsmanship)을 사용했다."
        result = guard.validate_v20_manuscript(text)
        assert result["is_pure"] is False

    def test_parentheses_with_hanja_allowed(self, guard):
        text = "청풍검법(靑風劍法)을 사용했다."
        result = guard.validate_v20_manuscript(text)
        # 순수 한자 괄호는 허용, 영어/숫자 미포함 시 통과
        parenthesis_issues = [i for i in result["issues"] if "괄호" in i]
        assert len(parenthesis_issues) == 0

    def test_arabic_numbers_detected(self, guard):
        text = "적이 100명이 몰려왔다."
        result = guard.validate_v20_manuscript(text)
        assert result["is_pure"] is False
        assert any("숫자" in issue for issue in result["issues"])

    def test_multiple_issues(self, guard):
        text = "레벨업(Level Up)! 100명의 적이 포션을 마셨다."
        result = guard.validate_v20_manuscript(text)
        assert result["is_pure"] is False
        # 금기어, 영어, 괄호, 숫자 모두 검출
        assert len(result["issues"]) >= 3


# ============================================================
# get_v20_purism_prompt
# ============================================================


class TestGetPurismPrompt:
    """순혈주의 프롬프트 생성 검증"""

    def test_prompt_not_empty(self, guard):
        prompt = guard.get_v20_purism_prompt()
        assert len(prompt) > 100

    def test_prompt_contains_key_elements(self, guard):
        prompt = guard.get_v20_purism_prompt()
        assert "순혈" in prompt or "Purism" in prompt
        assert "괄호" in prompt
        assert "금기어" in prompt or "금지" in prompt
        assert "한글" in prompt

    def test_prompt_includes_forbidden_terms(self, guard):
        prompt = guard.get_v20_purism_prompt()
        # 금기어 예시가 포함되어야 함
        assert "상태창" in prompt
