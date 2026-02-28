"""V73 자본금 파싱 — _parse_hud_capital_to_eok 단위 테스트."""

import pytest

from modules.core.stage4_post_processor import Stage4PostProcessor

_parse = Stage4PostProcessor._parse_hud_capital_to_eok


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
