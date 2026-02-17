"""[B-3-1] TierValidator / EpisodeAwareValidator Protocol 적합성 테스트."""

from modules.protocols.validators import EpisodeAwareValidator, TierValidator

# ──────────────────────────────────────────────────────────────
# 1. TierValidator — 5 positive
# ──────────────────────────────────────────────────────────────


class TestTierValidatorPositive:
    """TierValidator(manuscript, validation_context) 시그니처 적합."""

    def test_blocking_validator_conforms(self):
        from modules.validation.blocking_validator import BlockingValidator

        bv = BlockingValidator()
        assert isinstance(bv, TierValidator)

    def test_consistency_validator_conforms(self):
        from modules.validation.consistency_validator import ConsistencyValidator

        cv = ConsistencyValidator()
        assert isinstance(cv, TierValidator)

    def test_scoring_validator_conforms(self):
        from modules.validation.scoring_validator import ScoringValidator

        sv = ScoringValidator()
        assert isinstance(sv, TierValidator)

    def test_advisory_validator_conforms(self):
        from modules.validation.advisory_validator import AdvisoryValidator

        av = AdvisoryValidator()
        assert isinstance(av, TierValidator)

    def test_pre_llm_validator_conforms(self):
        from modules.validation.pre_llm_validator import PreLLMValidator

        pv = PreLLMValidator()
        assert isinstance(pv, TierValidator)


# ──────────────────────────────────────────────────────────────
# 2. EpisodeAwareValidator — 1 positive
# ──────────────────────────────────────────────────────────────


class TestEpisodeAwareValidatorPositive:
    """ContinuityValidator → EpisodeAwareValidator 적합."""

    def test_continuity_validator_conforms(self):
        from modules.validation.continuity_validator import ContinuityValidator

        cv = ContinuityValidator()
        assert isinstance(cv, EpisodeAwareValidator)


# ──────────────────────────────────────────────────────────────
# 3. Negative — 메서드 없음 / 이름 불일치
# ──────────────────────────────────────────────────────────────


class TestNegative:
    """Protocol 미적합 케이스."""

    def test_no_validate_method(self):
        class Empty:
            pass

        assert not isinstance(Empty(), TierValidator)
        assert not isinstance(Empty(), EpisodeAwareValidator)

    def test_wrong_method_name(self):
        class WrongName:
            def check(self, manuscript, validation_context):
                return {}

        assert not isinstance(WrongName(), TierValidator)


# ──────────────────────────────────────────────────────────────
# 4. Return contract — validate() 결과에 passed 키 존재
# ──────────────────────────────────────────────────────────────


class TestReturnContract:
    """validate() 반환값에 'passed' 키가 포함되는지 확인."""

    def test_blocking_validator_returns_passed(self):
        from modules.validation.blocking_validator import BlockingValidator

        bv = BlockingValidator()
        result = bv.validate("테스트 원고입니다.", {})
        assert "passed" in result

    def test_pre_llm_validator_returns_passed(self):
        from modules.validation.pre_llm_validator import PreLLMValidator

        pv = PreLLMValidator()
        result = pv.validate("테스트 원고입니다.", {})
        assert "passed" in result
