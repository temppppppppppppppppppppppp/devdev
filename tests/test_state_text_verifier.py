"""
[V75] State-Text Verifier 테스트 — 20개
actual_truth ↔ 원고 교차 검증 모듈 단위 테스트
"""

import json
from unittest.mock import MagicMock

from modules.core.state_text_verifier import StateTextVerifier

# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────


def _mock_agent(response_json: dict | None = None, raise_exc: Exception | None = None):
    """agent.ask() mock — JSON 문자열 반환 또는 예외 발생."""
    agent = MagicMock()
    if raise_exc:
        agent.ask.side_effect = raise_exc
    else:
        agent.ask.return_value = json.dumps(response_json or {"verified": True, "mismatches": []})
    return agent


# ──────────────────────────────────────────────
# verify() 테스트
# ──────────────────────────────────────────────


class TestVerify:
    """verify() 메서드 테스트."""

    def test_verified_no_mismatch(self):
        """#1: 정상 검증 — mismatch 없음 → verified=True."""
        agent = _mock_agent({"verified": True, "mismatches": []})
        stv = StateTextVerifier(agent=agent)
        result = stv.verify("주인공의 자본금은 45억이다.", {"capital": "45억"})
        assert result["verified"] is True
        assert result["mismatches"] == []
        assert result["corrections"] == {}
        assert result["blocking"] is False

    def test_mismatch_with_corrections(self):
        """#2: mismatch 발견 → verified=False, corrections 반환."""
        llm_response = {
            "verified": False,
            "mismatches": [
                {
                    "field": "capital",
                    "extracted": "100억",
                    "evidence": "원고: '자본금 45억'",
                    "corrected": "45억",
                }
            ],
        }
        agent = _mock_agent(llm_response)
        stv = StateTextVerifier(agent=agent)
        result = stv.verify("주인공의 자본금은 45억이다.", {"capital": "100억"})
        assert result["verified"] is False
        assert len(result["mismatches"]) == 1
        assert result["corrections"] == {"capital": "45억"}
        assert result["blocking"] is False

    def test_no_agent_skips_verification(self):
        """#3: agent=None → LLM 스킵, verified=True."""
        stv = StateTextVerifier(agent=None)
        result = stv.verify("원고 텍스트", {"capital": "45억"})
        assert result["verified"] is True
        assert result["corrections"] == {}

    def test_empty_actual_truth_skips(self):
        """#4: 빈 actual_truth → verified=True."""
        agent = _mock_agent()
        stv = StateTextVerifier(agent=agent)
        result = stv.verify("원고 텍스트", {})
        assert result["verified"] is True
        agent.ask.assert_not_called()

    def test_empty_manuscript_skips(self):
        """#5: 빈 manuscript → verified=True."""
        agent = _mock_agent()
        stv = StateTextVerifier(agent=agent)
        result = stv.verify("", {"capital": "45억"})
        assert result["verified"] is True
        agent.ask.assert_not_called()

    def test_llm_exception_silent_pass(self):
        """#6: LLM 예외 → SilentPass, verified=True."""
        agent = _mock_agent(raise_exc=RuntimeError("API timeout"))
        stv = StateTextVerifier(agent=agent)
        result = stv.verify("원고 텍스트", {"capital": "45억"})
        assert result["verified"] is True
        assert result["blocking"] is False

    def test_multiple_mismatches_partial_corrections(self):
        """#7: 복수 불일치 + 부분 correction (null 혼합)."""
        llm_response = {
            "verified": False,
            "mismatches": [
                {"field": "capital", "extracted": "100억", "evidence": "45억", "corrected": "45억"},
                {"field": "level", "extracted": "Lv.10", "evidence": "근거 없음", "corrected": None},
                {"field": "wins", "extracted": "50", "evidence": "48승", "corrected": "48"},
            ],
        }
        agent = _mock_agent(llm_response)
        stv = StateTextVerifier(agent=agent)
        result = stv.verify("자본금 45억, 48승", {"capital": "100억", "level": "Lv.10", "wins": "50"})
        assert result["verified"] is False
        assert len(result["mismatches"]) == 3
        # corrected=None인 level은 corrections에 포함되지 않아야 함
        assert "level" not in result["corrections"]
        assert result["corrections"] == {"capital": "45억", "wins": "48"}


# ──────────────────────────────────────────────
# _parse_response() 테스트
# ──────────────────────────────────────────────


class TestParseResponse:
    """_parse_response() 정적 메서드 테스트."""

    def test_direct_json(self):
        """#8: 순수 JSON → 직접 파싱."""
        raw = '{"verified": true, "mismatches": []}'
        result = StateTextVerifier._parse_response(raw)
        assert result["verified"] is True
        assert result["mismatches"] == []

    def test_markdown_fenced_json(self):
        """#9: 마크다운 코드블록 → JSON 추출."""
        raw = '```json\n{"verified": false, "mismatches": [{"field": "capital"}]}\n```'
        result = StateTextVerifier._parse_response(raw)
        assert result["verified"] is False
        assert len(result["mismatches"]) == 1

    def test_empty_string(self):
        """#10: 빈 문자열 → 기본값."""
        result = StateTextVerifier._parse_response("")
        assert result["verified"] is True

    def test_non_json_text(self):
        """#11: JSON이 아닌 텍스트 → 기본값."""
        result = StateTextVerifier._parse_response("이해할 수 없는 요청입니다.")
        assert result["verified"] is True
        assert result["mismatches"] == []

    def test_missing_mismatches_key(self):
        """#12: mismatches 키 누락 → 기본값."""
        raw = '{"verified": false}'
        result = StateTextVerifier._parse_response(raw)
        assert result["verified"] is True  # 키 누락이므로 기본값 반환


# ──────────────────────────────────────────────
# _filter_verifiable_fields() 테스트
# ──────────────────────────────────────────────


class TestFilterVerifiableFields:
    """_filter_verifiable_fields() 정적 메서드 테스트."""

    def test_numeric_fields_included(self):
        """#13: 수치 필드만 추출."""
        truth = {
            "capital": "45억",
            "total_assets": "120억",
            "level": "Lv.5",
            "name": "주인공",  # 비수치 — 숫자 없음
            "faction": "청풍문",  # 비수치 — 숫자 없음
        }
        result = StateTextVerifier._filter_verifiable_fields(truth)
        assert "capital" in result
        assert "total_assets" in result
        assert "level" in result
        assert "name" not in result
        assert "faction" not in result

    def test_non_verifiable_excluded(self):
        """#14: 비검증 필드 제외 — name, relationship 등."""
        truth = {
            "name": "홍길동",
            "current_emotion": "분노",
            "location": "서울",
        }
        result = StateTextVerifier._filter_verifiable_fields(truth)
        assert len(result) == 0

    def test_zero_value_included(self):
        """#15: 0 값도 검증 대상에 포함."""
        truth = {"wins": 0, "losses": 0, "capital": ""}
        result = StateTextVerifier._filter_verifiable_fields(truth)
        assert "wins" in result
        assert "losses" in result
        # 빈 문자열은 _VERIFIABLE_FIELDS에 있지만 None이 아닌 ""이므로 포함
        assert "capital" in result


# ──────────────────────────────────────────────
# apply_corrections() 테스트
# ──────────────────────────────────────────────


class TestApplyCorrections:
    """apply_corrections() 메서드 테스트."""

    def test_corrections_applied(self):
        """#16-a: corrections 적용 → 수정된 dict 반환."""
        stv = StateTextVerifier()
        truth = {"capital": "100억", "level": "Lv.5", "name": "주인공"}
        corrections = {"capital": "45억"}
        result = stv.apply_corrections(truth, corrections)
        assert result["capital"] == "45억"
        assert result["level"] == "Lv.5"  # 미수정
        assert result["name"] == "주인공"  # 미수정
        # 원본 불변
        assert truth["capital"] == "100억"

    def test_empty_corrections_returns_copy(self):
        """#16-b: 빈 corrections → 사본 반환 (원본과 독립)."""
        stv = StateTextVerifier()
        truth = {"capital": "45억"}
        result = stv.apply_corrections(truth, {})
        assert result == truth
        assert result is not truth  # 독립 사본

    def test_correction_for_unknown_field_ignored(self):
        """#16-c: actual_truth에 없는 필드 correction → 무시 (필드 주입 방지)."""
        stv = StateTextVerifier()
        truth = {"capital": "45억"}
        corrections = {"mana": "100", "capital": "50억"}
        result = stv.apply_corrections(truth, corrections)
        assert result["capital"] == "50억"
        assert "mana" not in result  # 주입 차단


# ──────────────────────────────────────────────
# 통합 엣지케이스 테스트
# ──────────────────────────────────────────────


class TestIntegrationEdgeCases:
    """감리 패치: 누락 엣지케이스 통합 테스트."""

    def test_all_non_verifiable_fields_skips_llm(self):
        """#17: 비검증 필드만 → LLM 미호출, verified=True."""
        agent = _mock_agent()
        stv = StateTextVerifier(agent=agent)
        result = stv.verify("원고 텍스트", {"name": "홍길동", "faction": "청풍문"})
        assert result["verified"] is True
        agent.ask.assert_not_called()

    def test_non_dict_mismatch_element_skipped(self):
        """#18: LLM이 mismatches에 non-dict 원소 반환 → skip."""
        llm_response = {
            "verified": False,
            "mismatches": [
                "잘못된 항목",
                {"field": "capital", "extracted": "100억", "evidence": "45억", "corrected": "45억"},
            ],
        }
        agent = _mock_agent(llm_response)
        stv = StateTextVerifier(agent=agent)
        result = stv.verify("자본금 45억", {"capital": "100억"})
        assert result["verified"] is False
        assert result["corrections"] == {"capital": "45억"}
