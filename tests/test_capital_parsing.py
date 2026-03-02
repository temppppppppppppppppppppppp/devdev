"""V73 자본금 파싱 — _parse_hud_capital_to_eok + _extract_capital_from_manuscript 단위 테스트."""

import pytest

from modules.core.stage4_post_processor import Stage4PostProcessor

_parse = Stage4PostProcessor._parse_hud_capital_to_eok
_extract = Stage4PostProcessor._extract_capital_from_manuscript


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("38억 3,154만 200원", 38.3154),
        ("131억 원", 131.0),
        ("20억", 20.0),
        ("5000만원", 0.5),
        ("3831540200", 38.3154),  # 원 단위 정수
        ("0", 0.0),
        ("", 0.0),
        ("80억", 80.0),
        ("1억 5000만", 1.5),
        ("500만 원", 0.05),
    ],
)
def test_parse_hud_capital_to_eok(raw, expected):
    result = _parse(raw)
    assert abs(result - expected) < 0.001, f"parse({raw!r}) = {result}, expected {expected}"


# ── _extract_capital_from_manuscript 테스트 ──


def test_compound_capital_38eok_3154man():
    """복합 금액 '38억 3,154만 200원'을 정확히 파싱."""
    text = "투자 경과 보고: 현재 자본금 38억 3,154만 200원으로 순항 중입니다."
    result = _extract(text)
    assert result is not None
    assert abs(result - 38.3154) < 0.001, f"extract={result}, expected ~38.3154"


def test_single_unit_still_works():
    """단일 단위 '80억' 회귀 방지."""
    text = "그의 자본금 80억은 대단했다."
    result = _extract(text)
    assert result is not None
    assert abs(result - 80.0) < 0.001, f"extract={result}, expected 80.0"


def test_man_only():
    """만 단위만 있는 경우."""
    text = "현금 5,000만이 남아있었다."
    result = _extract(text)
    assert result is not None
    assert abs(result - 0.5) < 0.001, f"extract={result}, expected 0.5"
