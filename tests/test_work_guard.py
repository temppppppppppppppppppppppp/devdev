"""WorkGuard 래퍼 테스트 — 작품별 work_guard.yaml 커스텀 규칙."""

import textwrap
from pathlib import Path


class MockBaseGuard:
    """BaseGuard 최소 mock."""

    def __init__(self):
        self.FORBIDDEN_TERMS = ["시스템", "로그인"]
        self.ALLOWED_TERMS = ["허용어"]
        self.MANDATORY_CONCEPTS = ["내공"]

    def get_genre_name(self):
        return "TEST"

    def get_v20_purism_prompt(self):
        return "base purism prompt"

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


def _write_yaml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "work_guard.yaml"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ── 초기화 / YAML 로드 ──────────────────────────────────────


class TestWorkGuardInit:
    def test_empty_yaml_uses_defaults(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(tmp_path, "")
        guard = WorkGuard(MockBaseGuard(), p)
        assert guard.FORBIDDEN_TERMS == ["시스템", "로그인"]
        assert "내공" in guard.MANDATORY_CONCEPTS

    def test_missing_file_uses_defaults(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        guard = WorkGuard(MockBaseGuard(), tmp_path / "nonexistent.yaml")
        assert guard.FORBIDDEN_TERMS == ["시스템", "로그인"]

    def test_genre_name_suffix(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(tmp_path, "")
        guard = WorkGuard(MockBaseGuard(), p)
        assert guard.get_genre_name() == "TEST+Work"


# ── extra_forbidden_terms 병합 ───────────────────────────────


class TestForbiddenTerms:
    def test_extra_forbidden_merged(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            extra_forbidden_terms:
              - "천잠비룡공"
              - "절대무적"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)
        assert "천잠비룡공" in guard.FORBIDDEN_TERMS
        assert "절대무적" in guard.FORBIDDEN_TERMS
        assert "시스템" in guard.FORBIDDEN_TERMS  # base 유지

    def test_extra_allowed_removes_from_forbidden(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            extra_allowed_terms:
              - "시스템"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)
        assert "시스템" not in guard.FORBIDDEN_TERMS
        assert "시스템" in guard.ALLOWED_TERMS

    def test_extra_mandatory_merged(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            extra_mandatory_concepts:
              - "삼양신단"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)
        assert "삼양신단" in guard.MANDATORY_CONCEPTS
        assert "내공" in guard.MANDATORY_CONCEPTS  # base 유지


# ── extra_forbidden_patterns regex ───────────────────────────


class TestForbiddenPatterns:
    def test_pattern_match_high_violation(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            extra_forbidden_patterns:
              - pattern: "화경|현경"
                reason: "이 작품에서 경지는 일류까지만 존재"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)
        result = guard.run_deep_validation("그는 화경에 도달했다.")
        work_violations = [v for v in result["violations"] if v["type"] == "work_forbidden_pattern"]
        assert len(work_violations) == 1
        assert work_violations[0]["severity"] == "HIGH"
        assert "일류" in work_violations[0]["message"]

    def test_pattern_no_match_clean(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            extra_forbidden_patterns:
              - pattern: "화경|현경"
                reason: "경지 제한"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)
        result = guard.run_deep_validation("그는 일류 고수였다.")
        work_violations = [v for v in result["violations"] if v["type"] == "work_forbidden_pattern"]
        assert len(work_violations) == 0

    def test_invalid_regex_skipped(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            extra_forbidden_patterns:
              - pattern: "[invalid"
                reason: "bad regex"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)
        result = guard.run_deep_validation("깨끗한 원고")
        assert result["has_critical"] is False

    def test_base_violations_preserved(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            extra_forbidden_patterns:
              - pattern: "화경"
                reason: "경지 제한"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)
        result = guard.run_deep_validation("시스템 화경 도달")
        assert result["has_critical"] is True
        types = {v["type"] for v in result["violations"]}
        assert "forbidden_term" in types
        assert "work_forbidden_pattern" in types


# ── custom_rules → purism prompt ─────────────────────────────


class TestCustomRules:
    def test_custom_rules_in_prompt(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            custom_rules:
              - "주인공은 오른팔을 쓸 수 없다"
              - "비공술은 존재하지 않는다"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)
        prompt = guard.get_v20_purism_prompt()
        assert "base purism prompt" in prompt
        assert "주인공은 오른팔을 쓸 수 없다" in prompt
        assert "비공술은 존재하지 않는다" in prompt
        assert "[작품 전용 규칙]" in prompt

    def test_no_custom_rules_no_extra_section(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(tmp_path, "")
        guard = WorkGuard(MockBaseGuard(), p)
        prompt = guard.get_v20_purism_prompt()
        assert prompt == "base purism prompt"


# ── character_constraints → purism prompt ────────────────────


class TestCharacterConstraints:
    def test_char_constraints_in_prompt(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            character_constraints:
              "주인공":
                - "왼손잡이"
                - "검만 사용"
              "천무진":
                - "장님 (시각 묘사 불가)"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)
        prompt = guard.get_v20_purism_prompt()
        assert "[캐릭터별 제약]" in prompt
        assert "주인공: 왼손잡이" in prompt
        assert "천무진: 장님" in prompt

    def test_age_constraint_reports_warning(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            character_constraints:
              "주인공":
                - "나이 18~35세"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        result = guard.run_deep_validation("주인공은 50세의 외모를 지녔다.", {"protagonist_config": {}})

        assert result["has_warning"] is True
        assert any("50세" in item["message"] for item in result["warning_violations"])

    def test_age_constraint_suppressed_for_possession_regression_settings(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            character_constraints:
              "주인공":
                - "나이 18~35세"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        result = guard.run_deep_validation(
            "주인공은 50세의 기억을 가진 채 젊은 몸에 눈을 떴다.",
            {"protagonist_config": {"incarnation_type": "빙의자"}},
        )

        assert result["has_warning"] is False
        assert result["warning_violations"] == []


# ── StyleGuard 체이닝 호환 ───────────────────────────────────


class TestStyleGuardChaining:
    def test_work_then_style_chain(self, tmp_path):
        """WorkGuard → StyleGuard 체이닝이 정상 작동하는지 확인."""
        from dataclasses import dataclass

        from modules.core.genre_guards.style_guard import StyleGuard
        from modules.core.genre_guards.work_guard import WorkGuard

        @dataclass
        class FakeStyleGuide:
            anti_ai_patterns: list = None
            forbidden_expressions: list = None
            sentence_length: str = "medium"

            def __post_init__(self):
                if self.anti_ai_patterns is None:
                    self.anti_ai_patterns = []
                if self.forbidden_expressions is None:
                    self.forbidden_expressions = []

        p = _write_yaml(
            tmp_path,
            """\
            extra_forbidden_terms:
              - "천잠비룡공"
            custom_rules:
              - "테스트 규칙"
        """,
        )
        base = MockBaseGuard()
        work = WorkGuard(base, p)
        style = StyleGuard(work, FakeStyleGuide(anti_ai_patterns=["그의 눈동자가 흔들렸다"]))

        # genre name 체인 확인
        assert "Work" in style.get_genre_name()
        assert "Style" in style.get_genre_name()

        # FORBIDDEN_TERMS 전파 확인
        assert "천잠비룡공" in style.FORBIDDEN_TERMS

        # deep validation 체인 확인
        result = style.run_deep_validation("천잠비룡공을 시전했다. 그의 눈동자가 흔들렸다.")
        types = {v["type"] for v in result["violations"]}
        assert "forbidden_term" in types  # WorkGuard base
        assert "style_anti_ai" in types  # StyleGuard

    def test_delegation_methods_pass_through(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(tmp_path, "")
        guard = WorkGuard(MockBaseGuard(), p)
        assert guard.get_impossible_actions() == []
        assert guard.get_justification_patterns() == []
        assert guard.get_hierarchy_rules() == {}
        assert guard.check_state_action_consistency("test", {}) == {"violations": []}
