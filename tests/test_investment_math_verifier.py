"""Unit tests for InvestmentMathVerifier (Codex F-2)."""

from modules.core.investment_math_verifier import InvestmentMathVerifier


def test_verify_empty_returns_no_advisory():
    verifier = InvestmentMathVerifier(llm_ask=lambda _prompt: "[]")
    out = verifier.verify("tactical_doc", [], 4, genre="investment")
    assert out == []


def test_verify_narrative_mismatch_major():
    payload = """
분석 결과:
[
  {
    "ep_no": 17,
    "issue": "횡보 서술과 10% 이상 변동 모순",
    "expected": "보합",
    "stated": "10% 상승",
    "severity": "MAJOR",
    "category": "narrative_mismatch"
  }
]
"""
    verifier = InvestmentMathVerifier(llm_ask=lambda _prompt: payload)
    out = verifier.verify("tactical_doc", [{"severity": "MAJOR"}], 4, genre="investment")
    assert len(out) == 1
    assert out[0]["severity"] == "MAJOR"
    assert out[0]["category"] == "narrative_mismatch"
    assert "Arc 4 Ep.17" in out[0]["text"]


def test_verify_python_fp_category():
    payload = """
[
  {
    "ep_no": 9,
    "issue": "Python 오탐",
    "severity": "MINOR",
    "category": "python_fp"
  }
]
"""
    verifier = InvestmentMathVerifier(llm_ask=lambda _prompt: payload)
    out = verifier.verify("tactical_doc", [{"severity": "MAJOR"}], 3, genre="investment")
    assert len(out) == 1
    assert out[0]["category"] == "python_fp"


def test_verify_skip_when_no_llm():
    verifier = InvestmentMathVerifier(llm_ask=None)
    out = verifier.verify("tactical_doc", [{"severity": "MAJOR"}], 4, genre="investment")
    assert out == []


def test_verify_json_parse_failure_non_blocking():
    verifier = InvestmentMathVerifier(llm_ask=lambda _prompt: "not-json")
    out = verifier.verify("tactical_doc", [{"severity": "MAJOR"}], 4, genre="investment")
    assert out == []
