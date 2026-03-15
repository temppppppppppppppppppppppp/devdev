"""[Codex F-1] 투자물 수치 Python 역산 검증기."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from modules.validation.threshold_helper import _threshold

_PRICE_RE = re.compile(
    r"(\d[\d,.]*)\s*달러.*?(\d[\d,.]*)\s*달러",
    re.DOTALL,
)
_LEVERAGE_RE = re.compile(r"(\d+)\s*배\s*레버리지|레버리지\s*(\d+)\s*배")
_PRINCIPAL_RE = re.compile(r"(\d[\d,.]*)\s*(억|만)\s*(?:원)?\s*(?:매수|투자|진입|증거금)")
_PROFIT_RE = re.compile(r"(?:수익|이익|확정)\s*(?:약\s*)?(\d[\d,.]*)\s*(억|만)\s*원")


@dataclass
class _TxCalc:
    ep_no: int | None
    asset: str
    action: str
    principal: float | None
    expected_profit: float | None
    stated_profit: float | None
    new_investment: float
    recovered_cash: float
    open_position_value: float
    warning: dict | None = None


class InvestmentArithmeticChecker:
    """
    [Codex F-1] 투자물 장르 수치 Python 역산 검증기.

    Arc의 investment_calc 구조화 필드 또는 tactical_doc 자유 서술에서
    투자 거래를 추출하고 산술 검산. LLM 0회, advisory-only.
    """

    def __init__(
        self,
        tolerance: float = 0.15,
        *,
        cash_tolerance: float = 0.05,
        total_assets_tolerance: float = 0.05,
        arc_boundary_tolerance: float = 0.01,
        max_leverage: float = 10.0,
    ) -> None:
        self.tolerance = float(tolerance)
        self.cash_tolerance = float(cash_tolerance)
        self.total_assets_tolerance = float(total_assets_tolerance)
        self.arc_boundary_tolerance = float(arc_boundary_tolerance)
        self.max_leverage = float(max_leverage)

    @classmethod
    def from_yaml(cls) -> InvestmentArithmeticChecker:
        """validation.yaml 임계값으로 초기화."""
        return cls(
            tolerance=float(_threshold("investment_math.python_tolerance", 0.15)),
            cash_tolerance=float(_threshold("investment_math.cash_tolerance", 0.05)),
            total_assets_tolerance=float(_threshold("investment_math.total_assets_tolerance", 0.05)),
            arc_boundary_tolerance=float(_threshold("investment_math.arc_boundary_tolerance", 0.01)),
            max_leverage=float(_threshold("investment_math.max_leverage", 10)),
        )

    def check(
        self,
        arc: dict,
        arc_no: int,
        *,
        prev_arc_end_state: dict | None = None,
    ) -> list[dict]:
        """
        Arc의 투자 수치를 Python으로 검산.

        Returns:
            list[dict]: [{"check": "investment_arithmetic", "severity": "...", "text": "..."}]
        """
        if not isinstance(arc, dict):
            return []

        warnings: list[dict] = []
        state_constraints = arc.get("state_constraints", {})
        if not isinstance(state_constraints, dict):
            state_constraints = {}

        investment_calc = state_constraints.get("investment_calc")
        transactions = self._extract_transactions(investment_calc, arc.get("tactical_doc", ""))

        tx_rows: list[_TxCalc] = []
        for tx in transactions:
            tx_rows.extend(self._validate_transaction(tx, arc_no))
        for tx_row in tx_rows:
            if tx_row.warning:
                warnings.append(tx_row.warning)

        # 2) 현금 내역 합산
        final_cash = self._extract_final_cash(investment_calc, state_constraints)
        prev_cash = self._extract_prev_cash(prev_arc_end_state or {})
        if prev_cash is not None and final_cash is not None and tx_rows:
            expected_cash = prev_cash + sum(t.recovered_cash for t in tx_rows) - sum(t.new_investment for t in tx_rows)
            cash_gap = self._safe_ratio(final_cash - expected_cash, expected_cash)
            if cash_gap > self.cash_tolerance:
                warnings.append(
                    self._warn(
                        severity="MAJOR",
                        text=(
                            f"[F-1] Arc {arc_no}: 현금 합산 불일치. 계산 {self._fmt_won(expected_cash)} "
                            f"vs 서술 {self._fmt_won(final_cash)} (괴리 {cash_gap * 100:.0f}%)"
                        ),
                    )
                )

        # 3) 총자산 합산
        final_total_assets = self._extract_final_total_assets(investment_calc, state_constraints)
        if final_cash is not None and final_total_assets is not None and tx_rows:
            expected_total_assets = final_cash + sum(t.open_position_value for t in tx_rows)
            assets_gap = self._safe_ratio(final_total_assets - expected_total_assets, expected_total_assets)
            if assets_gap > self.total_assets_tolerance:
                warnings.append(
                    self._warn(
                        severity="MAJOR",
                        text=(
                            f"[F-1] Arc {arc_no}: 총자산 합산 불일치. 계산 {self._fmt_won(expected_total_assets)} "
                            f"vs 서술 {self._fmt_won(final_total_assets)} (괴리 {assets_gap * 100:.0f}%)"
                        ),
                    )
                )

        # 4) Arc 경계 자본 연속성
        prev_total_assets = self._parse_number((prev_arc_end_state or {}).get("total_assets"))
        current_start_assets = self._parse_number(
            (state_constraints.get("arc_start_state", {}) if isinstance(state_constraints.get("arc_start_state"), dict) else {}).get(
                "total_assets"
            )
        )
        if prev_total_assets is not None and current_start_assets is not None:
            boundary_gap = self._safe_ratio(current_start_assets - prev_total_assets, prev_total_assets)
            if boundary_gap > self.arc_boundary_tolerance:
                warnings.append(
                    self._warn(
                        severity="CRITICAL",
                        text=(
                            f"[F-1] Arc {arc_no}: Arc 경계 자본 불연속. 이전 종료 총자산 {self._fmt_won(prev_total_assets)} "
                            f"vs 현재 시작 총자산 {self._fmt_won(current_start_assets)} "
                            f"(괴리 {boundary_gap * 100:.1f}%)"
                        ),
                    )
                )

        return warnings

    def _validate_transaction(self, tx: dict, arc_no: int) -> list[_TxCalc]:
        rows: list[_TxCalc] = []
        if not isinstance(tx, dict):
            return rows

        ep_no = self._parse_int(tx.get("ep_no"))
        asset = str(tx.get("asset", "자산")).strip() or "자산"
        action = str(tx.get("action", "")).strip().lower()

        entry = self._parse_number(tx.get("entry_price"))
        exit_price = self._parse_number(tx.get("exit_price"))
        leverage = self._parse_number(tx.get("leverage")) or 1.0
        principal = self._parse_number(tx.get("principal"))
        stated_profit = self._parse_number(tx.get("stated_profit"))

        is_short_like = any(k in action for k in ("공매도", "short", "매도"))
        if leverage > self.max_leverage:
            rows.append(
                self._tx_row(
                    ep_no=ep_no,
                    asset=asset,
                    action=action,
                    principal=principal,
                    expected_profit=None,
                    stated_profit=stated_profit,
                    warning=self._warn(
                        severity="MINOR",
                        text=f"[F-1] Arc {arc_no} Ep.{ep_no or '?'}: {asset} 레버리지 {leverage:g}배는 상한 {self.max_leverage:g}배 초과",
                    ),
                )
            )
        elif leverage < 1 and not is_short_like:
            rows.append(
                self._tx_row(
                    ep_no=ep_no,
                    asset=asset,
                    action=action,
                    principal=principal,
                    expected_profit=None,
                    stated_profit=stated_profit,
                    warning=self._warn(
                        severity="MINOR",
                        text=f"[F-1] Arc {arc_no} Ep.{ep_no or '?'}: {asset} 레버리지 {leverage:g}배는 비정상 값",
                    ),
                )
            )

        expected_profit = None
        if principal is not None and entry and entry > 0 and exit_price is not None and exit_price > 0:
            expected_profit = principal * ((exit_price - entry) / entry) * leverage

        if expected_profit is not None and stated_profit is not None:
            gap = self._safe_ratio(stated_profit - expected_profit, expected_profit)
            if gap > self.tolerance:
                rows.append(
                    self._tx_row(
                        ep_no=ep_no,
                        asset=asset,
                        action=action,
                        principal=principal,
                        expected_profit=expected_profit,
                        stated_profit=stated_profit,
                        warning=self._warn(
                            severity="MAJOR",
                            text=(
                                f"[F-1] Arc {arc_no} Ep.{ep_no or '?'}: {asset} 수익 과대/과소. "
                                f"{entry:g}→{exit_price:g} × {leverage:g}배 × {self._fmt_won(principal)} = "
                                f"{self._fmt_won(expected_profit)} (서술: {self._fmt_won(stated_profit)}, 괴리 {gap * 100:.0f}%)"
                            ),
                        ),
                    )
                )

        # 현금/총자산 합산용 집계값
        new_investment = 0.0
        recovered_cash = 0.0
        open_position_value = 0.0

        if principal is not None and principal > 0:
            close_like = any(k in action for k in ("청산", "close", "익절", "손절", "매도"))
            open_like = any(k in action for k in ("매수", "진입", "투자", "buy", "open"))

            if close_like or (exit_price is not None and exit_price > 0 and not open_like):
                profit_for_cash = expected_profit
                if profit_for_cash is None:
                    profit_for_cash = stated_profit if stated_profit is not None else 0.0
                recovered_cash = principal + profit_for_cash
            elif open_like or (exit_price is None or exit_price <= 0):
                new_investment = principal
                # 미청산 포지션은 원금 평가액으로 보수 계산
                open_position_value = principal

        rows.append(
            _TxCalc(
                ep_no=ep_no,
                asset=asset,
                action=action,
                principal=principal,
                expected_profit=expected_profit,
                stated_profit=stated_profit,
                new_investment=max(0.0, new_investment),
                recovered_cash=recovered_cash,
                open_position_value=max(0.0, open_position_value),
            )
        )
        return rows

    def _extract_transactions(self, investment_calc: object, tactical_doc: str) -> list[dict]:
        if isinstance(investment_calc, dict):
            txs = investment_calc.get("transactions")
            if isinstance(txs, list) and txs:
                return [t for t in txs if isinstance(t, dict)]
        return self._extract_from_tactical_doc(str(tactical_doc or ""))

    def _extract_from_tactical_doc(self, tactical_doc: str) -> list[dict]:
        if not tactical_doc.strip():
            return []

        prices = []
        for m in _PRICE_RE.finditer(tactical_doc):
            entry = self._parse_number(m.group(1))
            exit_price = self._parse_number(m.group(2))
            if entry is None or exit_price is None:
                continue
            prices.append((entry, exit_price))

        leverages = []
        for m in _LEVERAGE_RE.finditer(tactical_doc):
            raw = m.group(1) or m.group(2)
            lv = self._parse_number(raw)
            if lv is not None:
                leverages.append(lv)

        principals = []
        for m in _PRINCIPAL_RE.finditer(tactical_doc):
            amount = self._parse_korean_amount(m.group(1), m.group(2))
            if amount is not None:
                principals.append(amount)

        profits = []
        for m in _PROFIT_RE.finditer(tactical_doc):
            amount = self._parse_korean_amount(m.group(1), m.group(2))
            if amount is not None:
                profits.append(amount)

        if not prices and not principals:
            return []

        n = max(len(prices), len(principals), len(leverages), len(profits), 1)
        out: list[dict] = []
        for idx in range(n):
            entry, exit_price = prices[idx] if idx < len(prices) else (None, None)
            principal = principals[idx] if idx < len(principals) else None
            leverage = leverages[idx] if idx < len(leverages) else 1.0
            stated_profit = profits[idx] if idx < len(profits) else None
            action = "청산" if exit_price and exit_price > 0 else "매수"
            out.append(
                {
                    "ep_no": None,
                    "asset": "미상 자산",
                    "action": action,
                    "entry_price": entry,
                    "exit_price": exit_price or 0,
                    "leverage": leverage,
                    "principal": principal,
                    "stated_profit": stated_profit,
                }
            )
        return out

    def _extract_final_cash(self, investment_calc: object, state_constraints: dict) -> float | None:
        if isinstance(investment_calc, dict):
            value = self._parse_number(investment_calc.get("final_cash"))
            if value is not None:
                return value
        arc_end = state_constraints.get("arc_end_state", {}) if isinstance(state_constraints.get("arc_end_state"), dict) else {}
        for key in ("capital", "cash", "final_cash"):
            value = self._parse_number(arc_end.get(key))
            if value is not None:
                return value
        return None

    def _extract_final_total_assets(self, investment_calc: object, state_constraints: dict) -> float | None:
        if isinstance(investment_calc, dict):
            value = self._parse_number(investment_calc.get("final_total_assets"))
            if value is not None:
                return value
        arc_end = state_constraints.get("arc_end_state", {}) if isinstance(state_constraints.get("arc_end_state"), dict) else {}
        for key in ("total_assets", "assets", "final_total_assets"):
            value = self._parse_number(arc_end.get(key))
            if value is not None:
                return value
        return None

    def _extract_prev_cash(self, prev_arc_end_state: dict) -> float | None:
        if not isinstance(prev_arc_end_state, dict):
            return None
        for key in ("final_cash", "cash", "capital"):
            value = self._parse_number(prev_arc_end_state.get(key))
            if value is not None:
                return value
        return None

    @staticmethod
    def _warn(severity: str, text: str) -> dict:
        return {
            "check": "investment_arithmetic",
            "severity": severity,
            "text": text,
        }

    def _tx_row(
        self,
        *,
        ep_no: int | None,
        asset: str,
        action: str,
        principal: float | None,
        expected_profit: float | None,
        stated_profit: float | None,
        warning: dict | None,
    ) -> _TxCalc:
        if warning:
            # check()에서 warning dict를 누적하기 위해 logging side-effect 사용
            logging.debug("[InvestmentArithmeticChecker] advisory: %s", warning.get("text", "")[:200])
        return _TxCalc(
            ep_no=ep_no,
            asset=asset,
            action=action,
            principal=principal,
            expected_profit=expected_profit,
            stated_profit=stated_profit,
            new_investment=0.0,
            recovered_cash=0.0,
            open_position_value=0.0,
            warning=warning,
        )

    @staticmethod
    def _parse_int(raw: object) -> int | None:
        if isinstance(raw, int):
            return raw
        if isinstance(raw, float):
            return int(raw)
        try:
            return int(str(raw).strip())
        except Exception:
            return None

    def _parse_korean_amount(self, number: str, unit: str) -> float | None:
        base = self._parse_number(number)
        if base is None:
            return None
        if unit == "억":
            return base * 1e8
        if unit == "만":
            return base * 1e4
        return base

    def _parse_number(self, raw: object) -> float | None:
        if isinstance(raw, (int, float)):
            return float(raw)
        if raw is None:
            return None
        s = str(raw).strip()
        if not s:
            return None

        s = re.sub(r"\([^)]*\)", "", s).strip()
        sign = 1.0
        if s and s[0] in "+-":
            if s[0] == "-":
                sign = -1.0
            s = s[1:].strip()

        total = 0.0
        matched = False
        for unit, mul in (("조", 1e12), ("억", 1e8), ("만", 1e4)):
            for m in re.finditer(rf"(\d[\d,.]*(?:\.\d+)?)\s*{unit}", s):
                matched = True
                try:
                    total += float(m.group(1).replace(",", "")) * mul
                except ValueError:
                    return None
            s = re.sub(rf"\d[\d,.]*(?:\.\d+)?\s*{unit}", " ", s)

        if matched:
            tail = re.search(r"(\d[\d,.]*(?:\.\d+)?)", s)
            if tail:
                try:
                    total += float(tail.group(1).replace(",", ""))
                except ValueError:
                    return None
            return sign * total

        m = re.search(r"(\d[\d,.]*(?:\.\d+)?)", s)
        if not m:
            return None
        try:
            return sign * float(m.group(1).replace(",", ""))
        except ValueError:
            return None

    @staticmethod
    def _safe_ratio(diff: float, base: float) -> float:
        den = abs(base) if abs(base) > 1 else 1.0
        return abs(diff) / den

    @staticmethod
    def _fmt_won(value: float | None) -> str:
        if value is None:
            return "?"
        sign = "-" if value < 0 else ""
        v = abs(float(value))
        if v >= 1e8:
            return f"{sign}{v / 1e8:.2f}억"
        if v >= 1e4:
            return f"{sign}{v / 1e4:.1f}만"
        return f"{sign}{v:.0f}원"
