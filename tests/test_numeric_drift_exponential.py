"""[LM-Tier TF-B] NumericDriftAdvisor 지수 성장 Python 사전 감지 테스트."""

from modules.core.numeric_drift_advisor import NumericDriftAdvisor


class TestTryParseFloat:
    """_try_parse_float 정적 메서드 단위 테스트."""

    def test_int(self):
        assert NumericDriftAdvisor._try_parse_float(100) == 100.0

    def test_float(self):
        assert NumericDriftAdvisor._try_parse_float(3.14) == 3.14

    def test_str_with_unit(self):
        assert NumericDriftAdvisor._try_parse_float("100냥") == 100.0

    def test_str_with_comma(self):
        assert NumericDriftAdvisor._try_parse_float("1,000만냥") == 1000.0

    def test_none(self):
        assert NumericDriftAdvisor._try_parse_float(None) is None

    def test_empty_string(self):
        assert NumericDriftAdvisor._try_parse_float("") is None

    def test_no_number(self):
        assert NumericDriftAdvisor._try_parse_float("없음") is None


class TestExponentialGrowth:
    """_detect_exponential_growth 단위 테스트."""

    def test_100x_flagged(self):
        """established_value 대비 100배 초과 → 경고."""
        numbers = {
            "자산": {
                "value": "10000냥",
                "established_value": "100냥",
                "history": [],
            }
        }
        advisor = NumericDriftAdvisor()
        warnings = advisor._detect_exponential_growth(numbers)
        assert len(warnings) == 1
        assert "100배" in warnings[0] or "급등" in warnings[0]

    def test_no_established_no_flag(self):
        """established_value 없으면 급등 검사 스킵."""
        numbers = {
            "자산": {
                "value": "10000냥",
                "history": ["100", "200", "300"],
            }
        }
        advisor = NumericDriftAdvisor()
        warnings = advisor._detect_exponential_growth(numbers)
        # established_value 없으므로 급등 경고 없음 (연속 성장도 6개 미만)
        assert len(warnings) == 0

    def test_5_consecutive_growth(self):
        """5연속 50%+ 성장 → 경고."""
        numbers = {
            "내공": {
                "value": "10000",
                "history": ["100", "200", "400", "800", "1600", "3200"],
            }
        }
        advisor = NumericDriftAdvisor()
        warnings = advisor._detect_exponential_growth(numbers)
        assert len(warnings) == 1
        assert "연속" in warnings[0]
        assert "50%" in warnings[0]

    def test_pre_results_combined(self):
        """두 경고 모두 LLM 프롬프트에 prepend 확인."""
        numbers = {
            "자산": {
                "value": "10000",
                "established_value": "10",
                "history": ["10", "20", "40", "80", "160", "320"],
            }
        }
        advisor = NumericDriftAdvisor()
        warnings = advisor._detect_exponential_growth(numbers)
        # 100배 급등 + 5연속 성장 = 2건
        assert len(warnings) == 2

    def test_below_threshold_no_flag(self):
        """100배 미만 + 연속 성장 부족 → 경고 없음."""
        numbers = {
            "자산": {
                "value": "99",
                "established_value": "1",
                "history": ["10", "20", "15", "25", "20"],
            }
        }
        advisor = NumericDriftAdvisor()
        warnings = advisor._detect_exponential_growth(numbers)
        # 99배 < 100, history < 6
        assert len(warnings) == 0

    def test_empty_numbers(self):
        """빈 입력 안전성."""
        advisor = NumericDriftAdvisor()
        assert advisor._detect_exponential_growth({}) == []
        assert advisor._detect_exponential_growth(None) == []

    def test_non_dict_entry_skipped(self):
        """dict가 아닌 entry 스킵."""
        numbers = {"자산": "invalid"}
        advisor = NumericDriftAdvisor()
        assert advisor._detect_exponential_growth(numbers) == []
