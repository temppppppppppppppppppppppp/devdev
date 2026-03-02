"""[LM-C] NumericDriftAdvisor 테스트 — FactLedger 수치 누적 표류 감지."""

import json

import pytest

from modules.core.numeric_drift_advisor import NumericDriftAdvisor

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def sample_numbers():
    """이력이 충분한 수치 데이터."""
    return {
        "자산": {
            "value": "300억",
            "unit": "원",
            "last_ep": 67,
            "history": [
                "ep4: 210만원 → 500만원",
                "ep11: 500만원 → 3000만원",
                "ep25: 3000만원 → 2억",
                "ep40: 2억 → 50억",
                "ep67: 50억 → 300억",
            ],
        },
        "전투력": {
            "value": "85000",
            "unit": "",
            "last_ep": 60,
            "history": [
                "ep1: 100 → 200",
                "ep5: 200 → 500",
                "ep10: 500 → 1500",
                "ep20: 1500 → 5000",
            ],
        },
        "체력": {
            "value": "150",
            "unit": "HP",
            "last_ep": 10,
            "history": [
                "ep1: 100 → 110",
                "ep5: 110 → 130",
            ],
        },
    }


@pytest.fixture
def short_history_numbers():
    """이력이 부족한 수치 데이터."""
    return {
        "마나": {
            "value": "500",
            "unit": "MP",
            "last_ep": 3,
            "history": ["ep1: 100 → 200"],
        },
        "명성": {
            "value": "10",
            "unit": "",
            "last_ep": 2,
            "history": ["ep2: 0 → 10"],
        },
    }


# ═══════════════════════════════════════════════════════════════
# FormatHistory 테스트
# ═══════════════════════════════════════════════════════════════


class TestFormatHistory:
    def test_basic_format(self, sample_numbers):
        advisor = NumericDriftAdvisor()
        result = advisor._format_history(sample_numbers, min_history=3)
        assert "[자산]" in result
        assert "300억" in result
        assert "ep4" in result

    def test_min_history_filter(self, sample_numbers):
        advisor = NumericDriftAdvisor()
        result = advisor._format_history(sample_numbers, min_history=3)
        # 체력은 이력 2개 → 제외
        assert "[체력]" not in result
        # 자산(5), 전투력(4) → 포함
        assert "[자산]" in result
        assert "[전투력]" in result

    def test_max_items_cap(self):
        advisor = NumericDriftAdvisor()
        # 35개 항목 생성 (MAX_ITEMS=30 초과)
        numbers = {}
        for i in range(35):
            numbers[f"stat_{i}"] = {
                "value": str(i * 100),
                "unit": "",
                "last_ep": 10,
                "history": [f"ep{j}: {j} → {j + 1}" for j in range(5)],
            }
        result = advisor._format_history(numbers, min_history=3)
        # 최대 30개만 (A-4: 20→30 확장)
        bracket_count = result.count("[stat_")
        assert bracket_count <= 30

    def test_history_value_extraction(self, sample_numbers):
        advisor = NumericDriftAdvisor()
        result = advisor._format_history(sample_numbers, min_history=3)
        # "epN: old -> new" 형식이 유지되는지
        assert "ep4: 210만원 → 500만원" in result

    def test_empty_numbers(self):
        advisor = NumericDriftAdvisor()
        result = advisor._format_history({}, min_history=3)
        assert result == ""


# ═══════════════════════════════════════════════════════════════
# LlmCheck 테스트
# ═══════════════════════════════════════════════════════════════


class TestLlmCheck:
    def test_drift_detected(self, sample_numbers):
        drift_response = json.dumps(
            [
                {
                    "key": "자산",
                    "issue": "ep40→ep67에서 50억→300억으로 6배 급등, 서사적 근거 불명",
                    "history_snippet": "ep40: 50억 → ep67: 300억",
                }
            ],
            ensure_ascii=False,
        )

        advisor = NumericDriftAdvisor(llm_ask=lambda _: drift_response)
        result = advisor.check(numbers=sample_numbers, ep_num=70)
        assert len(result) == 1
        assert result[0]["key"] == "자산"
        assert result[0]["severity"] == "MAJOR"
        assert result[0]["check"] == "numeric_drift"

    def test_no_drift(self, sample_numbers):
        advisor = NumericDriftAdvisor(llm_ask=lambda _: "[]")
        result = advisor.check(numbers=sample_numbers, ep_num=70)
        assert result == []

    def test_no_llm_returns_empty(self, sample_numbers):
        advisor = NumericDriftAdvisor(llm_ask=None)
        result = advisor.check(numbers=sample_numbers, ep_num=70)
        assert result == []

    def test_llm_empty_response(self, sample_numbers):
        advisor = NumericDriftAdvisor(llm_ask=lambda _: "")
        result = advisor.check(numbers=sample_numbers, ep_num=70)
        assert result == []

    def test_llm_exception_graceful(self, sample_numbers):
        def _raise(_):
            raise RuntimeError("API 오류")

        advisor = NumericDriftAdvisor(llm_ask=_raise)
        result = advisor.check(numbers=sample_numbers, ep_num=70)
        assert result == []

    def test_json_in_code_fence(self, sample_numbers):
        fenced = '```json\n[{"key": "전투력", "issue": "급등", "history_snippet": "ep10→ep20"}]\n```'
        advisor = NumericDriftAdvisor(llm_ask=lambda _: fenced)
        result = advisor.check(numbers=sample_numbers, ep_num=70)
        assert len(result) == 1
        assert result[0]["key"] == "전투력"

    def test_invalid_json_graceful(self, sample_numbers):
        advisor = NumericDriftAdvisor(llm_ask=lambda _: "이것은 JSON이 아닙니다")
        result = advisor.check(numbers=sample_numbers, ep_num=70)
        assert result == []


# ═══════════════════════════════════════════════════════════════
# EdgeCases 테스트
# ═══════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_empty_numbers_dict(self):
        advisor = NumericDriftAdvisor(llm_ask=lambda _: "[]")
        result = advisor.check(numbers={}, ep_num=70)
        assert result == []

    def test_all_below_min_history(self, short_history_numbers):
        advisor = NumericDriftAdvisor(llm_ask=lambda _: "[]")
        result = advisor.check(numbers=short_history_numbers, ep_num=10)
        assert result == []

    def test_format_history_shows_established_value(self):
        """established_value가 현재값과 다를 때 초기값 표시."""
        numbers = {
            "자산": {
                "value": "300억",
                "unit": "원",
                "last_ep": 67,
                "established_value": "100만원",
                "history": [
                    "ep4: 100만원 → 500만원",
                    "ep11: 500만원 → 3000만원",
                    "ep25: 3000만원 → 2억",
                ],
            }
        }
        advisor = NumericDriftAdvisor()
        result = advisor._format_history(numbers, min_history=3)
        assert "초기값=100만원" in result


# ═══════════════════════════════════════════════════════════════
# Integration 테스트
# ═══════════════════════════════════════════════════════════════


class TestIntegration:
    def test_check_returns_correct_format(self, sample_numbers):
        drift_response = json.dumps(
            [
                {"key": "자산", "issue": "급등", "history_snippet": "50억→300억"},
                {"key": "전투력", "issue": "비정상 상승", "history_snippet": "500→5000"},
            ],
            ensure_ascii=False,
        )

        advisor = NumericDriftAdvisor(llm_ask=lambda _: drift_response)
        result = advisor.check(numbers=sample_numbers, ep_num=70)
        assert len(result) == 2
        for item in result:
            assert "key" in item
            assert "issue" in item
            assert "history_snippet" in item
            assert item["severity"] == "MAJOR"
            assert item["check"] == "numeric_drift"
