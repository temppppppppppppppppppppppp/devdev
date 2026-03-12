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


# ── work_identity SSOT → purism prompt / warning ───────────────────


class TestWorkIdentity:
    def test_work_identity_sections_in_prompt(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              work_type: "엔터 타이쿤 성장물"
              one_line_truth: "사람을 발굴하고 포지셔닝해 스타 IP 기업으로 키우는 이야기"
              protagonist_weapon:
                - "스타 감각"
                - "포지셔닝 판단"
              business_axes:
                - "배우"
                - "연습생"
              control_axes:
                - "캐스팅 권한"
              mandatory_scene_engines:
                - "인재 발굴"
              forbidden_flattenings:
                - "사람 대신 숫자만으로 승부 보기"
              mandatory_lexicon:
                - "캐스팅"
                - "팬덤"
              tracking_slots:
                - "핵심 배우 라인"
              registry_profiles:
                - name: "talent_registry"
                  purpose: "배우/연습생 성장 상태 추적"
                  required_fields: ["name", "tier", "risk"]
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)
        prompt = guard.get_v20_purism_prompt()
        assert "[작품 정체성 SSOT]" in prompt
        assert "작품 유형: 엔터 타이쿤 성장물" in prompt
        assert "주인공 무기: 스타 감각, 포지셔닝 판단" in prompt
        assert "[우선 추적 슬롯]" in prompt
        assert "핵심 배우 라인" in prompt
        assert "[레지스트리 프로파일]" in prompt
        assert "talent_registry: 배우/연습생 성장 상태 추적 | required_fields=name, tier, risk" in prompt

    def test_retrieval_contract_prompt_contains_slots_and_stage_guidance(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              mandatory_scene_engines:
                - "인재 발굴"
              tracking_slots:
                - "핵심 배우 라인"
                - "주력 포맷/IP"
              registry_profiles:
                - name: "talent_registry"
                  purpose: "배우 상태 추적"
                  required_fields: ["name", "tier"]
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        contract = guard.get_retrieval_contract_prompt("blueprint")

        assert "[작품 메모리 소비 계약 - Stage 3 Blueprint 설계]" in contract
        assert "핵심 배우 라인" in contract
        assert "인재 발굴" in contract
        assert "talent_registry" in contract
        assert "씬은 mandatory_scene_engines 중 최소 하나와 연결" in contract

    def test_director_review_advisory_mentions_identity_drift(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              mandatory_scene_engines:
                - "인재 발굴"
              forbidden_flattenings:
                - "단순 M&A/주식 매매물처럼 흐르기"
              tracking_slots:
                - "핵심 배우 라인"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        advisory = guard.get_director_review_advisory()

        assert "[작품 정체성 감리 기준]" in advisory
        assert "work identity drift" in advisory
        assert "flattened_to_generic_investment" in advisory
        assert "핵심 배우 라인" in advisory

    def test_select_retrieval_focus_prefers_matching_slots(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              mandatory_scene_engines:
                - "인재 발굴"
                - "팬덤 반응"
              tracking_slots:
                - "핵심 배우 라인"
                - "주력 포맷/IP"
                - "외부 투자 라인"
              registry_profiles:
                - name: "talent_registry"
                  purpose: "배우/연습생 성장 상태 추적"
                  required_fields: ["name", "tier", "risk"]
                - name: "finance_registry"
                  purpose: "자금/투자 상태 추적"
                  required_fields: ["cash", "exposure"]
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        focus = guard.select_retrieval_focus(
            stage="manuscript",
            focus_text="이번 화는 배우 캐스팅과 팬덤 반응, 연습생 리스크를 다룬다.",
        )

        assert focus["tracking_slots"][0] == "핵심 배우 라인"
        assert "인재 발굴" in focus["mandatory_scene_engines"] or "팬덤 반응" in focus["mandatory_scene_engines"]
        assert focus["registry_profiles"][0]["name"] == "talent_registry"

    def test_mandatory_lexicon_missing_reports_warning(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              mandatory_lexicon:
                - "캐스팅"
                - "팬덤"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        result = guard.run_deep_validation("지표와 자금만 오가는 차가운 협상 장면", {})

        assert result["has_warning"] is True
        assert any(item["type"] == "work_identity_lexicon_missing" for item in result["warning_violations"])

    def test_mandatory_lexicon_present_stays_clean(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              mandatory_lexicon:
                - "캐스팅"
                - "팬덤"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        result = guard.run_deep_validation("캐스팅 회의 뒤 팬덤 반응까지 확인했다.", {})

        assert not any(item["type"] == "work_identity_lexicon_missing" for item in result["warning_violations"])

    def test_mandatory_scene_engines_missing_reports_warning(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              mandatory_scene_engines:
                - "인재 발굴"
                - "팬덤 반응"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        result = guard.run_deep_validation("지표와 자금만 검토하는 건조한 투자 회의가 이어졌다.", {})

        warning = next(item for item in result["warning_violations"] if item["type"] == "work_identity_scene_engine_missing")

        assert warning["expected_scene_engines"] == ["인재 발굴", "팬덤 반응"]
        assert warning["matched_scene_engines"] == []
        assert "인재 발굴" in warning["scene_engine_keywords"]

    def test_mandatory_scene_engines_present_stays_clean(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              mandatory_scene_engines:
                - "인재 발굴"
                - "팬덤 반응"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        result = guard.run_deep_validation("신인 인재를 발굴한 뒤 팬덤 반응까지 바로 확인했다.", {})

        assert not any(item["type"] == "work_identity_scene_engine_missing" for item in result["warning_violations"])

    def test_forbidden_flattenings_warn_on_generic_investment_drift(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              forbidden_flattenings:
                - "엔터 현장성 없이 투자 용어만 반복"
              mandatory_lexicon:
                - "캐스팅"
                - "팬덤"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        result = guard.run_deep_validation(
            "지분과 밸류, 수익률, 회수 배수만 계산하며 투자 지표만 반복했다.",
            {},
        )

        warning = next(item for item in result["warning_violations"] if item["type"] == "work_identity_flattening_warning")

        assert warning["finance_term_hits"] >= 3
        assert warning["keyword_hits"] >= 0
        assert warning["lexicon_present"] is False

    def test_forbidden_flattenings_do_not_warn_when_work_lexicon_present(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              forbidden_flattenings:
                - "엔터 현장성 없이 투자 용어만 반복"
              mandatory_lexicon:
                - "캐스팅"
                - "팬덤"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        result = guard.run_deep_validation(
            "캐스팅 회의에서 배우 동선을 조정하고 팬덤 반응까지 확인했다.",
            {},
        )

        assert not any(item["type"] == "work_identity_flattening_warning" for item in result["warning_violations"])

    def test_role_fit_constraints_in_prompt(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              role_fit_constraints:
                - name: "한지수"
                  role: "PB"
                  disallowed_actions:
                    - "탭댄스"
                    - "아이돌 안무"
                  exceptions:
                    - "연습생 출신"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)
        prompt = guard.get_v20_purism_prompt()

        assert "[직업 적합성 가드]" in prompt
        assert "한지수 (PB)" in prompt
        assert "탭댄스" in prompt
        assert "연습생 출신" in prompt

    def test_role_fit_constraints_warn_on_unjustified_role_break(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              role_fit_constraints:
                - name: "한지수"
                  role: "PB"
                  disallowed_actions:
                    - "탭댄스"
                    - "아이돌 안무"
                  exceptions:
                    - "연습생 출신"
                    - "무대 훈련"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        result = guard.run_deep_validation("한지수는 회의실에서 갑자기 탭댄스를 추며 분위기를 장악했다.", {})

        warning = next(item for item in result["warning_violations"] if item["type"] == "work_role_fit_warning")

        assert warning["character"] == "한지수"
        assert warning["exceptions_considered"] == ["연습생 출신", "무대 훈련"]
        assert warning["exception_hit"] is False

    def test_role_fit_constraints_skip_when_exception_is_present(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              role_fit_constraints:
                - name: "한지수"
                  role: "PB"
                  disallowed_actions:
                    - "탭댄스"
                  exceptions:
                    - "연습생 출신"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        result = guard.run_deep_validation(
            "연습생 출신인 한지수는 과거 특기를 살려 탭댄스를 짧게 보여줬다.",
            {},
        )

        assert not any(item["type"] == "work_role_fit_warning" for item in result["warning_violations"])

    def test_director_review_advisory_mentions_role_fit(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              role_fit_constraints:
                - name: "한지수"
                  role: "PB"
                  disallowed_actions:
                    - "탭댄스"
        """,
        )
        guard = WorkGuard(MockBaseGuard(), p)

        advisory = guard.get_director_review_advisory()

        assert "직업 적합성" in advisory
        assert "한지수(PB)" in advisory


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
