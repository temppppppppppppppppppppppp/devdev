"""NegativeExampleInjector 장르 디스패치 테스트."""

from modules.domain.agents.negative_example_injector import (
    _COMMON_EXAMPLES,
    _GENRE_OVERRIDES,
    NegativeExampleInjector,
    create_negative_example_injector,
)

# ─── 장르별 디스패치 ───


class TestGenreDispatch:
    """_load_examples_library가 장르별로 올바른 라이브러리를 로드하는지 검증."""

    def test_wuxia_has_common_plus_wuxia_overrides(self):
        inj = NegativeExampleInjector("wuxia")
        lib = inj.examples_library
        # COMMON 4 + WUXIA override 2 = 6 카테고리
        assert "duplicate_acquisition" in lib
        assert "location_teleport" in lib
        assert "joint_docs_mismatch" in lib
        assert "tactical_doc_quality" in lib
        assert "state_discontinuity" in lib
        assert "power_inflation" in lib
        assert len(lib) == 6
        # 무협 전용 내용 확인
        sd = lib["state_discontinuity"]
        assert "무협" in sd["description"]

    def test_hunter_has_hunter_overrides(self):
        inj = NegativeExampleInjector("hunter")
        lib = inj.examples_library
        assert len(lib) == 6
        sd = lib["state_discontinuity"]
        assert "헌터" in sd["description"]
        # 무협 전용 내용이 없어야 함
        for ex in sd["bad_examples"]:
            assert "내공" not in ex["context"]

    def test_investment_has_investment_overrides(self):
        inj = NegativeExampleInjector("investment")
        lib = inj.examples_library
        assert len(lib) == 6
        sd = lib["state_discontinuity"]
        assert "투자" in sd["description"]
        pi = lib["power_inflation"]
        assert "투자" in pi["description"]

    def test_fantasy_has_fantasy_overrides(self):
        inj = NegativeExampleInjector("fantasy")
        lib = inj.examples_library
        assert len(lib) == 6
        sd = lib["state_discontinuity"]
        assert "판타지" in sd["description"]
        # 판타지 전용 내용 확인
        texts = " ".join(ex["context"] for ex in sd["bad_examples"])
        assert "마나" in texts or "축복" in texts

    def test_unknown_genre_falls_back_to_default(self):
        inj = NegativeExampleInjector("alt_history")
        lib = inj.examples_library
        assert len(lib) == 6
        # _default override 사용
        sd = lib["state_discontinuity"]
        assert sd == _GENRE_OVERRIDES["_default"]["state_discontinuity"]

    def test_empty_genre_falls_back_to_default(self):
        inj = NegativeExampleInjector("")
        lib = inj.examples_library
        assert lib["state_discontinuity"] == _GENRE_OVERRIDES["_default"]["state_discontinuity"]


# ─── generate_injection ───


class TestGenerateInjection:
    """generate_injection이 올바른 장르별 내용을 출력하는지 검증."""

    def test_wuxia_injection_contains_wuxia_terms(self):
        inj = NegativeExampleInjector("wuxia")
        output = inj.generate_injection()
        # state_discontinuity (top 4에 포함)에 무협 전용 내용 확인
        assert "내공" in output
        assert "무협" in output

    def test_hunter_injection_does_not_contain_wuxia_terms(self):
        inj = NegativeExampleInjector("hunter")
        output = inj.generate_injection()
        assert "내공" not in output
        assert "삼류" not in output
        # 헌터 전용 내용 확인
        assert "마나" in output or "HP" in output or "E등급" in output

    def test_investment_injection_has_investment_terms(self):
        inj = NegativeExampleInjector("investment")
        output = inj.generate_injection()
        assert "내공" not in output
        assert "자금" in output or "수익" in output

    def test_fantasy_injection_has_fantasy_terms(self):
        inj = NegativeExampleInjector("fantasy")
        output = inj.generate_injection()
        assert "내공" not in output
        assert "마나" in output or "마법" in output

    def test_common_categories_always_present(self):
        """장르 무관하게 COMMON 카테고리 내용이 포함되어야 함."""
        for genre in ["wuxia", "hunter", "investment", "fantasy", "cooking"]:
            inj = NegativeExampleInjector(genre)
            output = inj.generate_injection()
            assert "아이템" in output  # duplicate_acquisition
            assert "tactical_doc" in output  # tactical_doc_quality


# ─── generate_self_check_prompt ───


class TestSelfCheckPrompt:
    """generate_self_check_prompt가 장르 범용 체크리스트를 반환하는지 검증."""

    def test_no_wuxia_specific_terms(self):
        inj = NegativeExampleInjector("hunter")
        prompt = inj.generate_self_check_prompt()
        assert "내공" not in prompt
        assert "부상" not in prompt or "부상/자원 손실" in prompt
        # 범용 표현 확인
        assert "items_acquired" in prompt
        assert "arc_start_state.location" in prompt


# ─── get_targeted_warning ───


class TestTargetedWarning:
    """get_targeted_warning이 장르 범용 경고를 반환하는지 검증."""

    def test_state_discontinuity_warning_is_generic(self):
        inj = NegativeExampleInjector("hunter")
        warning = inj.get_targeted_warning("state_discontinuity")
        assert "내공" not in warning
        assert "상태" in warning

    def test_unknown_issue_type_returns_fallback(self):
        inj = NegativeExampleInjector("wuxia")
        warning = inj.get_targeted_warning("nonexistent_type")
        assert "제약 조건" in warning


# ─── record_rejection ───


class TestRecordRejection:
    """record_rejection이 정상 작동하는지 검증."""

    def test_records_and_caps_at_20(self):
        inj = NegativeExampleInjector("wuxia")
        for i in range(25):
            inj.record_rejection(
                {"arc_no": i, "state_constraints": {}},
                f"reason_{i}",
                "test_category",
            )
        assert len(inj.rejection_history) == 20
        assert inj.rejection_history[0]["arc_no"] == 5  # 0~4 삭제됨

    def test_rejection_priority_boost(self):
        inj = NegativeExampleInjector("wuxia")
        inj.record_rejection({"arc_no": 1}, "duplicate!", "power_inflation")
        cats = inj._select_relevant_categories()
        assert cats[0] == "power_inflation"


# ─── create_negative_example_injector ───


class TestHelperFunction:
    def test_creates_with_genre(self):
        inj = create_negative_example_injector("fantasy")
        assert inj.genre == "fantasy"
        assert "판타지" in inj.examples_library["state_discontinuity"]["description"]

    def test_default_genre_is_wuxia(self):
        inj = create_negative_example_injector()
        assert inj.genre == "wuxia"


# ─── 데이터 무결성 ───


class TestDataIntegrity:
    """_COMMON_EXAMPLES와 _GENRE_OVERRIDES 구조 무결성 검증."""

    def test_common_has_4_categories(self):
        assert len(_COMMON_EXAMPLES) == 4
        expected = {"duplicate_acquisition", "location_teleport", "joint_docs_mismatch", "tactical_doc_quality"}
        assert set(_COMMON_EXAMPLES.keys()) == expected

    def test_all_overrides_have_2_categories(self):
        for genre, overrides in _GENRE_OVERRIDES.items():
            assert set(overrides.keys()) == {"state_discontinuity", "power_inflation"}, (
                f"{genre} override has wrong keys: {set(overrides.keys())}"
            )

    def test_all_examples_have_required_fields(self):
        """모든 bad_example이 필수 필드를 가지고 있는지 확인."""
        required_fields = {"context", "mistake", "why_wrong", "correct"}
        all_data = {**_COMMON_EXAMPLES}
        for overrides in _GENRE_OVERRIDES.values():
            all_data.update(overrides)
        for cat_name, cat_data in all_data.items():
            assert "description" in cat_data, f"{cat_name} missing description"
            assert "bad_examples" in cat_data, f"{cat_name} missing bad_examples"
            for i, ex in enumerate(cat_data["bad_examples"]):
                missing = required_fields - set(ex.keys())
                assert not missing, f"{cat_name}[{i}] missing fields: {missing}"
