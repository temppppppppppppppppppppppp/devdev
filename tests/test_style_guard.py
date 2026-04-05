"""[D-3] StyleGuard 래퍼 테스트."""

from dataclasses import dataclass


@dataclass
class MockStyleGuide:
    """StyleGuide 최소 mock."""

    anti_ai_patterns: list = None
    forbidden_expressions: list = None
    sentence_length: str = "medium"
    signature_expressions: list = None
    tone: str = "진지"
    pov: str = "3인칭"
    sentence_rhythm: str = ""
    emotion_rendering: str = ""
    dialogue_narration_pattern: str = ""

    def __post_init__(self):
        if self.anti_ai_patterns is None:
            self.anti_ai_patterns = []
        if self.forbidden_expressions is None:
            self.forbidden_expressions = []
        if self.signature_expressions is None:
            self.signature_expressions = []


class MockBaseGuard:
    """BaseGuard 최소 mock."""

    def __init__(self):
        self.FORBIDDEN_TERMS = ["시스템", "로그인"]
        self.ALLOWED_TERMS = []
        self.MANDATORY_CONCEPTS = []

    def get_genre_name(self):
        return "TEST"

    def get_v20_purism_prompt(self):
        return "test prompt"

    def get_impossible_actions(self, current_state=None):
        return []

    def get_justification_patterns(self):
        return []

    def get_hierarchy_rules(self):
        return {}

    def check_state_action_consistency(self, manuscript, current_state):
        return {"violations": []}

    def run_deep_validation(self, manuscript, current_state=None):
        violations = []
        for term in self.FORBIDDEN_TERMS:
            if term in manuscript:
                violations.append(
                    {
                        "type": "forbidden_term",
                        "severity": "HIGH",
                        "message": f"금기어 '{term}' 발견",
                    }
                )
        return {
            "has_critical": any(v["severity"] == "HIGH" for v in violations),
            "violations": violations,
            "summary": "",
            "feedback": "",
        }


class TestStyleGuardInit:
    def test_wraps_base_guard(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide(anti_ai_patterns=["그의 눈동자가 흔들렸다"])
        guard = StyleGuard(base, sg)
        assert "TEST" in guard.get_genre_name()
        assert "Style" in guard.get_genre_name()

    def test_copies_base_forbidden_terms(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide()
        guard = StyleGuard(base, sg)
        assert guard.FORBIDDEN_TERMS == ["시스템", "로그인"]

    def test_filters_short_patterns(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide(anti_ai_patterns=["abc", "네 글자 이상 패턴"])
        guard = StyleGuard(base, sg)
        assert len(guard._anti_ai) == 1


class TestStyleGuardValidation:
    def test_base_guard_violations_preserved(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide()
        guard = StyleGuard(base, sg)

        result = guard.run_deep_validation("이 원고에 시스템 오류가 있습니다.")
        assert result["has_critical"] is True
        assert any(v["type"] == "forbidden_term" for v in result["violations"])

    def test_anti_ai_pattern_detected(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide(anti_ai_patterns=["그의 눈동자가 흔들렸다"])
        guard = StyleGuard(base, sg)

        result = guard.run_deep_validation("그의 눈동자가 흔들렸다. 무슨 일이 일어난 것일까.")
        style_violations = [v for v in result["violations"] if v["type"] == "style_anti_ai"]
        assert len(style_violations) == 1
        assert style_violations[0]["severity"] == "MEDIUM"

    def test_forbidden_expression_detected(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide(forbidden_expressions=["마치 ~처럼", "한편으로는"])
        guard = StyleGuard(base, sg)

        result = guard.run_deep_validation("그는 한편으로는 기뻤지만 슬프기도 했다.")
        style_violations = [v for v in result["violations"] if v["type"] == "style_forbidden_expression"]
        assert len(style_violations) == 1

    def test_no_false_positive_when_clean(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide(
            anti_ai_patterns=["그의 눈동자가 흔들렸다"],
            forbidden_expressions=["한편으로는"],
        )
        guard = StyleGuard(base, sg)

        result = guard.run_deep_validation("검은 바람이 불었다. 이청풍은 검을 뽑았다.")
        style_violations = [v for v in result["violations"] if v["type"].startswith("style_")]
        assert len(style_violations) == 0

    def test_sentence_length_too_short_warning(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide(sentence_length="long")
        guard = StyleGuard(base, sg)

        short_text = ". ".join(["짧은 문장이다"] * 20) + "."
        result = guard.run_deep_validation(short_text)
        length_violations = [v for v in result["violations"] if v["type"] == "style_length_deviation"]
        assert len(length_violations) == 1
        assert length_violations[0]["severity"] == "LOW"

    def test_sentence_length_ok_no_warning(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide(sentence_length="medium")
        guard = StyleGuard(base, sg)

        medium_text = ". ".join(["이청풍은 새벽녘에 눈을 떴다, 검을 잡았다"] * 15) + "."
        result = guard.run_deep_validation(medium_text)
        length_violations = [v for v in result["violations"] if v["type"] == "style_length_deviation"]
        assert len(length_violations) == 0

    def test_style_violations_are_not_critical(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide(anti_ai_patterns=["그의 눈동자가 흔들렸다"])
        guard = StyleGuard(base, sg)

        result = guard.run_deep_validation("그의 눈동자가 흔들렸다. 바람이 불었다.")
        assert result["has_critical"] is False

    def test_warning_fields_from_base_guard_are_preserved(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        class WarningBaseGuard(MockBaseGuard):
            def run_deep_validation(self, manuscript, current_state=None):
                return {
                    "has_critical": False,
                    "has_warning": True,
                    "violations": [],
                    "warning_violations": [{"type": "work_identity_warning", "message": "경고"}],
                    "warning_summary": "작품 경고",
                    "summary": "기본 통과",
                    "feedback": "",
                }

        guard = StyleGuard(WarningBaseGuard(), MockStyleGuide())
        result = guard.run_deep_validation("깨끗한 원고")

        assert result["has_warning"] is True
        assert result["warning_summary"] == "작품 경고"
        assert result["warning_violations"][0]["type"] == "work_identity_warning"


class TestStyleGuardDelegation:
    def test_delegates_purism_prompt(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide()
        guard = StyleGuard(base, sg)
        assert guard.get_v20_purism_prompt() == "test prompt"

    def test_delegates_impossible_actions(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide()
        guard = StyleGuard(base, sg)
        assert guard.get_impossible_actions() == []


class TestStyleGuardMalformedEntries:
    def test_normalizes_dict_backed_style_entries(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide(
            anti_ai_patterns=[{"pattern": "그의 눈동자가 흔들렸다"}, {"ignored": {"nested": "x"}}],
            forbidden_expressions=[{"expression": "한편으로는"}, {"value": ["bad"]}],
        )
        guard = StyleGuard(base, sg)

        assert guard._anti_ai == ["그의 눈동자가 흔들렸다"]
        assert guard._forbidden_expr == ["한편으로는"]

    def test_malformed_style_entries_do_not_crash_validation(self):
        from modules.core.genre_guards.style_guard import StyleGuard

        base = MockBaseGuard()
        sg = MockStyleGuide(
            anti_ai_patterns=[{"pattern": "그의 눈동자가 흔들렸다"}, {"oops": {"nested": "x"}}, ["bad"]],
            forbidden_expressions=[{"expression": "한편으로는"}, {"text": ["bad"]}],
        )
        guard = StyleGuard(base, sg)

        result = guard.run_deep_validation("그의 눈동자가 흔들렸다. 그는 한편으로는 기뻤다.")

        anti_ai = [v for v in result["violations"] if v["type"] == "style_anti_ai"]
        forbidden = [v for v in result["violations"] if v["type"] == "style_forbidden_expression"]
        assert len(anti_ai) == 1
        assert len(forbidden) == 1
