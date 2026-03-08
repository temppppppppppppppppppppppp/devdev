"""Unit tests for InvestmentArithmeticChecker (Codex F-1)."""

from modules.core.investment_arithmetic_checker import InvestmentArithmeticChecker


def _arc_with_calc(
    *,
    tx: list[dict] | None = None,
    final_cash: float | None = None,
    final_total_assets: float | None = None,
    start_total_assets: str | float | None = None,
    end_total_assets: str | float | None = None,
    tactical_doc: str = "",
) -> dict:
    state_constraints: dict = {
        "arc_start_state": {"total_assets": start_total_assets} if start_total_assets is not None else {},
        "arc_end_state": {"total_assets": end_total_assets} if end_total_assets is not None else {},
    }
    if tx is not None or final_cash is not None or final_total_assets is not None:
        state_constraints["investment_calc"] = {
            "transactions": tx or [],
            "final_cash": final_cash,
            "final_total_assets": final_total_assets,
        }
    return {
        "state_constraints": state_constraints,
        "tactical_doc": tactical_doc,
    }


def test_normal_trade_no_advisory():
    checker = InvestmentArithmeticChecker()
    tx = [
        {
            "ep_no": 9,
            "asset": "WTI",
            "action": "청산",
            "entry_price": 100,
            "exit_price": 110,
            "leverage": 2,
            "principal": 100_000_000,
            "stated_profit": 20_000_000,
        }
    ]
    arc = _arc_with_calc(
        tx=tx,
        final_cash=1_120_000_000,
        final_total_assets=1_120_000_000,
        start_total_assets="10억",
        end_total_assets="11.2억",
    )
    out = checker.check(arc, 4, prev_arc_end_state={"capital": 1_000_000_000, "total_assets": "10억"})
    assert out == []


def test_profit_mismatch_major_advisory():
    checker = InvestmentArithmeticChecker(tolerance=0.15)
    tx = [
        {
            "ep_no": 11,
            "asset": "금",
            "action": "청산",
            "entry_price": 100,
            "exit_price": 110,
            "leverage": 2,
            "principal": 100_000_000,
            "stated_profit": 30_000_000,  # expected=20,000,000
        }
    ]
    arc = _arc_with_calc(tx=tx, final_cash=1_120_000_000, final_total_assets=1_120_000_000)
    out = checker.check(arc, 4, prev_arc_end_state={"capital": 1_000_000_000})
    assert any(x.get("severity") == "MAJOR" and "수익 과대/과소" in x.get("text", "") for x in out)


def test_cash_flow_mismatch_major():
    checker = InvestmentArithmeticChecker()
    tx = [
        {
            "ep_no": 13,
            "asset": "나스닥 선물",
            "action": "청산",
            "entry_price": 100,
            "exit_price": 110,
            "leverage": 2,
            "principal": 100_000_000,
            "stated_profit": 20_000_000,
        }
    ]
    arc = _arc_with_calc(tx=tx, final_cash=1_300_000_000, final_total_assets=1_300_000_000)
    out = checker.check(arc, 4, prev_arc_end_state={"capital": 1_000_000_000})
    assert any(x.get("severity") == "MAJOR" and "현금 합산 불일치" in x.get("text", "") for x in out)


def test_total_assets_mismatch_major():
    checker = InvestmentArithmeticChecker()
    tx = [
        {
            "ep_no": 13,
            "asset": "나스닥 선물",
            "action": "청산",
            "entry_price": 100,
            "exit_price": 110,
            "leverage": 2,
            "principal": 100_000_000,
            "stated_profit": 20_000_000,
        }
    ]
    arc = _arc_with_calc(tx=tx, final_cash=1_120_000_000, final_total_assets=1_300_000_000)
    out = checker.check(arc, 4, prev_arc_end_state={"capital": 1_000_000_000})
    assert any(x.get("severity") == "MAJOR" and "총자산 합산 불일치" in x.get("text", "") for x in out)


def test_arc_boundary_discontinuity_critical():
    checker = InvestmentArithmeticChecker()
    arc = _arc_with_calc(start_total_assets="8억")
    out = checker.check(arc, 5, prev_arc_end_state={"total_assets": "10억"})
    assert any(x.get("severity") == "CRITICAL" and "Arc 경계 자본 불연속" in x.get("text", "") for x in out)


def test_leverage_over_limit_minor():
    checker = InvestmentArithmeticChecker(max_leverage=10)
    tx = [
        {
            "ep_no": 17,
            "asset": "금 선물",
            "action": "청산",
            "entry_price": 100,
            "exit_price": 110,
            "leverage": 20,
            "principal": 100_000_000,
            "stated_profit": 200_000_000,
        }
    ]
    arc = _arc_with_calc(tx=tx, final_cash=1_300_000_000, final_total_assets=1_300_000_000)
    out = checker.check(arc, 5, prev_arc_end_state={"capital": 1_000_000_000})
    assert any(x.get("severity") == "MINOR" and "레버리지" in x.get("text", "") for x in out)


def test_regex_fallback_extracts_transaction():
    checker = InvestmentArithmeticChecker()
    arc = _arc_with_calc(
        tactical_doc="WTI 원유를 60달러에서 66달러로 2배 레버리지 5억 투자, 수익 1억 원 확정",
    )
    out = checker.check(arc, 6)
    assert out == []


def test_regex_fallback_failure_non_blocking():
    checker = InvestmentArithmeticChecker()
    arc = _arc_with_calc(tactical_doc="수치 없는 서술 텍스트")
    out = checker.check(arc, 6)
    assert out == []


def test_zero_entry_price_non_blocking():
    checker = InvestmentArithmeticChecker()
    tx = [
        {
            "ep_no": 1,
            "asset": "BTC",
            "action": "청산",
            "entry_price": 0,
            "exit_price": 100,
            "leverage": 3,
            "principal": 100_000_000,
            "stated_profit": 1_000_000,
        }
    ]
    arc = _arc_with_calc(tx=tx)
    out = checker.check(arc, 1)
    assert out == []


def test_equal_entry_exit_zero_profit_ok():
    checker = InvestmentArithmeticChecker()
    tx = [
        {
            "ep_no": 2,
            "asset": "WTI",
            "action": "청산",
            "entry_price": 100,
            "exit_price": 100,
            "leverage": 3,
            "principal": 100_000_000,
            "stated_profit": 0,
        }
    ]
    arc = _arc_with_calc(tx=tx, final_cash=1_100_000_000, final_total_assets=1_100_000_000)
    out = checker.check(arc, 2, prev_arc_end_state={"capital": 1_000_000_000})
    assert out == []


def test_negative_profit_loss_ok():
    checker = InvestmentArithmeticChecker()
    tx = [
        {
            "ep_no": 3,
            "asset": "WTI",
            "action": "청산",
            "entry_price": 100,
            "exit_price": 90,
            "leverage": 2,
            "principal": 100_000_000,
            "stated_profit": -20_000_000,
        }
    ]
    arc = _arc_with_calc(tx=tx, final_cash=1_080_000_000, final_total_assets=1_080_000_000)
    out = checker.check(arc, 3, prev_arc_end_state={"capital": 1_000_000_000})
    assert out == []


def test_parse_korean_mixed_units():
    checker = InvestmentArithmeticChecker()
    value = checker._parse_number("1억 2,500만 300원")
    assert value == 125_000_300
