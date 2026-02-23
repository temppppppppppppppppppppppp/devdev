"""
[V70] GenreGuard 단위 테스트

WuxiaGuard(BaseGuard)의 공용 메서드를 검증합니다.
"""

import inspect
from types import SimpleNamespace

import pytest

from modules.core.genre_guards.base_guard import BaseGuard
from modules.core.genre_guards.style_guard import StyleGuard
from modules.core.genre_guards.work_guard import WorkGuard
from modules.core.genre_guards.wuxia_guard import WuxiaGuard


@pytest.fixture
def guard():
    return WuxiaGuard()


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
        # 아라비아 숫자는 숫자값으로 정상 파싱되어야 한다.
        assert guard.convert_to_numeric("100") == 100.0
        assert guard.convert_to_numeric("1.5") == 1.5

    def test_arabic_float_string(self, guard):
        assert guard.convert_to_numeric("1.5") == 1.5

    def test_zero_keywords(self, guard):
        for word in ["영", "무", "없음", "소멸", "0"]:
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


class TestGuardWrapperDelegation:
    def test_work_guard_delegates_v461_methods(self, tmp_path):
        base = WuxiaGuard()
        wrapped = WorkGuard(base_guard=base, yaml_path=tmp_path / "missing_work_guard.yaml")
        assert wrapped.get_authority_hierarchy() == base.get_authority_hierarchy()

    def test_style_guard_delegates_v461_methods(self):
        base = WuxiaGuard()
        style_guide = SimpleNamespace(
            anti_ai_patterns=[],
            forbidden_expressions=[],
            sentence_length="medium",
        )
        wrapped = StyleGuard(base_guard=base, style_guide=style_guide)
        assert wrapped.get_authority_hierarchy() == base.get_authority_hierarchy()


class TestBaseGuardAnnotations:
    def test_abstract_return_types_are_str(self):
        assert inspect.signature(BaseGuard.get_genre_name).return_annotation is str
        assert inspect.signature(BaseGuard.get_v20_purism_prompt).return_annotation is str


class _DummyConsistencyGuard(BaseGuard):
    def get_genre_name(self) -> str:
        return "dummy"

    def get_v20_purism_prompt(self) -> str:
        return "dummy"

    def get_impossible_actions(self, current_state: dict) -> list[dict]:
        return [
            {
                "pattern": r"성벽을 뛰어넘었다",
                "reason": "중상 상태에서 불가능한 행동",
                "severity": "HIGH",
            }
        ]

    def get_justification_patterns(self) -> list[str]:
        return [r"이를 악물고"]

    def get_hostile_action_types(self) -> list[str]:
        return ["배신"]

    def get_resolution_patterns(self) -> list[str]:
        return [r"복수", r"용서"]

    def get_protagonist_victory_patterns(self) -> list[str]:
        return [r"역전"]

    def get_villain_response_patterns(self) -> list[str]:
        return [r"분노", r"후퇴"]


class TestStateActionJustificationWindow:
    def test_justification_far_away_does_not_clear_violation(self):
        guard = _DummyConsistencyGuard()
        manuscript = "그는 중상을 입은 몸으로 성벽을 뛰어넘었다." + ("아" * 300) + "이를 악물고 버텼다."

        result = guard.check_state_action_consistency(manuscript, {})

        assert result["passed"] is False
        assert len(result["violations"]) == 1

    def test_justification_nearby_clears_violation(self):
        guard = _DummyConsistencyGuard()
        manuscript = "그는 중상을 입은 몸으로 성벽을 뛰어넘었다. 이를 악물고 버텼다."

        result = guard.check_state_action_consistency(manuscript, {})

        assert result["passed"] is True
        assert result["violations"] == []


class TestUnresolvedConflictResolutionWindow:
    def test_resolution_far_away_does_not_clear_npc_conflict(self):
        guard = _DummyConsistencyGuard()
        karma_matrix = {
            "마두": {
                "events": [{"type": "배신"}],
                "relation_type": "hostile",
            }
        }
        manuscript = "마두가 함께 움직였다." + ("아" * 120) + "군중은 복수를 외쳤다."

        result = guard.check_unresolved_conflict(manuscript, karma_matrix, ep_num=12)

        assert result["passed"] is False
        assert result["violations"]
        assert result["violations"][0]["npc"] == "마두"

    def test_resolution_nearby_clears_npc_conflict(self):
        guard = _DummyConsistencyGuard()
        karma_matrix = {
            "마두": {
                "events": [{"type": "배신"}],
                "relation_type": "hostile",
            }
        }
        manuscript = "마두가 복수를 당한 뒤 함께 움직였다."

        result = guard.check_unresolved_conflict(manuscript, karma_matrix, ep_num=12)

        assert result["passed"] is True
        assert result["violations"] == []


class TestVillainResponseWindow:
    def test_generic_response_far_away_does_not_clear_villain_check(self):
        guard = _DummyConsistencyGuard()
        villain_context = {"villain_name": "마두", "villain_role": "주적", "is_aware": True}
        manuscript = "주인공은 역전에 성공했다.\n마두는 성루에 서 있었다.\n" + ("아" * 120) + "\n군중은 분노했다."

        result = guard.check_villain_response(manuscript, villain_context, recent_events=[{"type": "역전"}])

        assert result["passed"] is False
        assert result["incompetent_villain_risk"] is True
        assert result["violations"]

    def test_generic_response_nearby_clears_villain_check(self):
        guard = _DummyConsistencyGuard()
        villain_context = {"villain_name": "마두", "villain_role": "주적", "is_aware": True}
        manuscript = "주인공은 역전에 성공했다. 마두는 후퇴를 명령했다."

        result = guard.check_villain_response(manuscript, villain_context, recent_events=[{"type": "역전"}])

        assert result["passed"] is True
        assert result["violations"] == []
