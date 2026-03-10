"""
[NC-1/NC-2] NumericConsistencyChecker — Python-only 수치 정합성 검사

대원칙 준수: Python은 수집만, 판단은 LLM이. Advisory-only, REJECT 권한 없음.
8개 검사: 숫자 추출 → FactLedger 교차 → 산술 일관성 → 직함 변경 → "처음" 이벤트 모순
          → 퍼센트 구성 검증(NC-2) → NPC 동명이인(NC-2) → 도입부 유사도(NC-2)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

# ── 숫자 추출 패턴 ──────────────────────────────────────────────
_DIALOGUE_RE = re.compile(r'[""\u201c][^""\u201c\u201d]*[""\u201d]')

_MONEY_KEYWORDS = (
    "잔고|자본금?|현금|자산|실탄|예수금|수익|원금|투자금|손실|"
    "포지션|연봉|매출|부채|세금|배당|이익|손익|매출액|시가총액|"
    "펀드|대출|예치금|보유금|운용금|총액|순이익|영업이익"
)

_MONEY_PATTERNS = [
    # "잔고 131억", "수익 5억 3000만원"
    re.compile(
        rf"(?:{_MONEY_KEYWORDS})[이가은는:의]?\s*(?:약?\s*)?(\d[\d,.]*)\s*(억|만)\s*(?:(\d[\d,.]*)\s*만)?\s*(?:원)?",
    ),
    # "80억의 자본", "130억 원의 잔고"
    re.compile(
        rf"(\d[\d,.]*)\s*(억|만)\s*(?:원)?[의이가]?\s*(?:{_MONEY_KEYWORDS})",
    ),
]

_COMPOUND_MONEY_RE = re.compile(
    rf"(?:{_MONEY_KEYWORDS})[이가은는:의]?\s*(?:약?\s*)?"
    r"(?:(\d[\d,.]*)\s*억)?\s*(?:(\d[\d,.]*)\s*만)?\s*(?:(\d[\d,.]*)\s*원?)?"
)

_PERCENT_RE = re.compile(
    r"(?:수익률|이율|금리|이자|배당률|세율|할인율|증가율|성장률|하락률)[이가은는:의]?\s*(?:약?\s*)?(\d[\d,.]+)\s*%"
)

# [NC-2 GAP-2] 퍼센트/비율 구성 검증용 패턴
_PERCENT_COMPOSITION_RE = re.compile(
    r"(?:유지율|담보비율|증거금\s*(?:유지)?율|LTV|마진율|자기자본비율|부채비율)"
    r"[이가은는:의]?\s*(?:약?\s*)?(\d[\d,.]+)\s*%"
)
_PERCENT_COMPOSITION_KEYWORDS = {
    "유지율": ("평가금액", "증거금"),
    "담보비율": ("담보", "대출"),
    "증거금유지율": ("평가금액", "증거금"),
    "증거금 유지율": ("평가금액", "증거금"),
    "LTV": ("대출", "담보"),
    "마진율": ("이익", "매출"),
    "자기자본비율": ("자본", "자산"),
    "부채비율": ("부채", "자본"),
}
_LEVERAGE_RE = re.compile(r"(\d[\d,.]*)\s*배\s*(?:레버리지|배율)")

# 합산 패턴: "수익 A + 원금 B = 총 C" 변형
_SUM_PATTERN = re.compile(
    r"(\d[\d,.]*)\s*(억|만).*?(?:\+|더하면|합치면|합산|합계).*?(\d[\d,.]*)\s*(억|만).*?(?:=|총|합계|합산).*?(\d[\d,.]*)\s*(억|만)"
)
_LEVERAGE_CALC_RE = re.compile(r"(\d[\d,.]*)\s*(억|만).*?[xX×]\s*(\d[\d,.]*)\s*배.*?(?:=|→)?\s*(\d[\d,.]*)\s*(억|만)")

# 직함 패턴
_TITLE_LIST = [
    "인턴",
    "레지던트",
    "전문의",
    "회장",
    "부회장",
    "사장",
    "부사장",
    "전무",
    "상무",
    "이사",
    "본부장",
    "실장",
    "국장",
    "부장",
    "차장",
    "과장",
    "대리",
    "사원",
    "팀장",
    "파트장",
    "센터장",
    "소장",
    "원장",
    "관장",
    "대표",
    "CEO",
    "CFO",
    "CTO",
    "COO",
    "PB",
    "매니저",
    "디렉터",
    "파트너",
    "VP",
    "MD",
    "교수",
    "부교수",
    "조교수",
    "강사",
    "연구원",
    "의사",
    "간호사",
    "약사",
    "병장",
    "상병",
    "일병",
    "이등병",
    "하사",
    "중사",
    "상사",
    "감독",
    "코치",
    "선수",
    "주장",
    "1군",
    "2군",
    "국대",
    "국가대표",
    "석사",
    "박사",
]
_TITLE_RE = re.compile(
    r"([\uac00-\ud7a3]{2,6})\s*(" + "|".join(re.escape(t) for t in _TITLE_LIST) + r")(?:\b|[이가은는의를에])",
)

# 직함 승진 순서 (동일 계열만 비교)
_TITLE_PROGRESSIONS = {
    "corporate": [
        "사원",
        "대리",
        "과장",
        "차장",
        "부장",
        "팀장",
        "파트장",
        "실장",
        "본부장",
        "이사",
        "상무",
        "전무",
        "부사장",
        "사장",
        "부회장",
        "회장",
        "대표",
        "CEO",
        "CFO",
        "CTO",
        "COO",
        "VP",
        "MD",
        "파트너",
        "디렉터",
        "매니저",
        "PB",
    ],
    "academic": ["강사", "연구원", "석사", "박사", "조교수", "부교수", "교수"],
    "medical": ["간호사", "인턴", "레지던트", "의사", "전문의", "약사", "원장", "교수"],
    "military": ["이등병", "일병", "상병", "병장", "하사", "중사", "상사"],
    "sports": ["2군", "선수", "1군", "국대", "국가대표", "주장", "코치", "감독"],
    "research": ["연구원", "선임연구원", "책임연구원", "소장", "센터장", "관장"],
}

_TITLE_RANK = {
    title: (domain, idx)
    for domain, titles in _TITLE_PROGRESSIONS.items()
    for idx, title in enumerate(titles)
}

# "처음" 마커
_FIRST_TIME_RE = re.compile(r"(?:처음|최초|첫|난생처음|태어나서\s*처음)[으로이]?\s*([\uac00-\ud7a3a-zA-Z0-9\s]{2,30})")


@dataclass
class _ExtractedNumber:
    raw: str
    value_eok: float
    context_label: str
    position: int


@dataclass
class ConsistencyWarning:
    check: str
    severity: str  # "MAJOR" | "MINOR"
    text: str


class NumericConsistencyChecker:
    """[NC-1] Python-only 수치 정합성 검사. Advisory 전용, REJECT 권한 없음."""

    # FactLedger key ↔ 원고 키워드 동의어 맵
    _SYNONYM_MAP: dict[str, set[str]] = {
        "잔고": {"자본금", "자본", "현금", "자산", "실탄", "예수금", "보유금", "운용금"},
        "자본금": {"잔고", "자본", "현금", "자산", "실탄", "예수금", "보유금"},
        "포지션": {"투자금", "투자액", "투자 규모"},
        "수익": {"이익", "순이익", "영업이익", "순수익"},
        "원금": {"투자원금", "초기투자금"},
        "매출": {"매출액", "총매출"},
        "연봉": {"급여", "월급"},
        "부채": {"대출", "빚", "차입금"},
    }

    def __init__(
        self,
        fact_ledger=None,
        db=None,
        world_state=None,
    ) -> None:
        self._fact_ledger = fact_ledger
        self._db = db
        self._world_state = world_state

    def check(
        self,
        manuscript: str,
        ep_num: int,
        *,
        state_updates: dict | None = None,
        prev_manuscript: str | None = None,
    ) -> list[dict]:
        """전체 검사 실행. [{check, severity, text}] 반환."""
        if not manuscript or not manuscript.strip():
            return []

        warnings: list[dict] = []
        extracted = self._extract_all_numbers(manuscript)

        # 1. FactLedger 교차 검증
        try:
            _fl_warns = self._check_against_ledger(extracted, ep_num)
            warnings.extend(_fl_warns)
        except Exception as e:
            logging.debug("[NC-1] FactLedger 교차 검증 실패: %s", e)

        # 2. 산술 일관성
        try:
            _arith_warns = self._check_arithmetic(extracted, manuscript)
            warnings.extend(_arith_warns)
        except Exception as e:
            logging.debug("[NC-1] 산술 검사 실패: %s", e)

        # 3. 직함 변경
        try:
            _title_warns = self._check_title_consistency(manuscript, ep_num)
            warnings.extend(_title_warns)
        except Exception as e:
            logging.debug("[NC-1] 직함 검사 실패: %s", e)

        # 4. "처음" 이벤트 모순
        try:
            _event_warns = self._check_event_ordering(manuscript, ep_num)
            warnings.extend(_event_warns)
        except Exception as e:
            logging.debug("[NC-1] 이벤트 순서 검사 실패: %s", e)

        # 5. [NC-2 GAP-2] 퍼센트/비율 구성 검증
        try:
            _pct_warns = self._check_percent_composition(extracted, manuscript)
            warnings.extend(_pct_warns)
        except Exception as e:
            logging.debug("[NC-2] 퍼센트 구성 검사 실패: %s", e)

        # 6. [NC-2 GAP-4] NPC 동명이인 감지
        try:
            _name_warns = self._check_npc_name_collision(manuscript)
            warnings.extend(_name_warns)
        except Exception as e:
            logging.debug("[NC-2] NPC 동명이인 검사 실패: %s", e)

        # 7. [NC-2 GAP-6] 연속 에피소드 도입부 유사도
        try:
            _opening_warns = self._check_opening_similarity(manuscript, prev_manuscript=prev_manuscript)
            warnings.extend(_opening_warns)
        except Exception as e:
            logging.debug("[NC-2] 도입부 유사도 검사 실패: %s", e)

        return warnings

    # ── 1. 숫자 추출 엔진 ────────────────────────────────────────

    def _extract_all_numbers(self, text: str) -> list[_ExtractedNumber]:
        """원고에서 금액/퍼센트/배율 숫자를 추출. 대사는 제외."""
        narration = _DIALOGUE_RE.sub("", text)
        results: list[_ExtractedNumber] = []

        # 금액 패턴
        for pat in _MONEY_PATTERNS:
            for m in pat.finditer(narration):
                raw_num = m.group(1).replace(",", "")
                try:
                    num = float(raw_num)
                except (ValueError, TypeError):
                    continue
                unit = m.group(2)
                eok = num if unit == "억" else num / 10000
                # 만 부분 추가 매칭
                if m.lastindex and m.lastindex >= 3 and m.group(3):
                    try:
                        eok += float(m.group(3).replace(",", "")) / 10000
                    except (ValueError, TypeError):
                        pass
                label = self._guess_label(m.group(0), narration, m.start())
                results.append(
                    _ExtractedNumber(
                        raw=m.group(0).strip(),
                        value_eok=eok,
                        context_label=label,
                        position=m.start(),
                    )
                )

        # 복합 금액
        for m in _COMPOUND_MONEY_RE.finditer(narration):
            eok_part, man_part, won_part = m.group(1), m.group(2), m.group(3)
            if not eok_part and not man_part:
                continue
            total = 0.0
            if eok_part:
                total += float(eok_part.replace(",", ""))
            if man_part:
                total += float(man_part.replace(",", "")) / 10000
            if total > 0:
                label = self._guess_label(m.group(0), narration, m.start())
                # 중복 체크 (같은 위치에서 이미 추출된 것 방지)
                if not any(abs(r.position - m.start()) < 5 and abs(r.value_eok - total) < 0.01 for r in results):
                    results.append(
                        _ExtractedNumber(
                            raw=m.group(0).strip(),
                            value_eok=total,
                            context_label=label,
                            position=m.start(),
                        )
                    )

        # 퍼센트
        for m in _PERCENT_RE.finditer(narration):
            try:
                pct = float(m.group(1).replace(",", ""))
            except (ValueError, TypeError):
                continue
            results.append(
                _ExtractedNumber(
                    raw=m.group(0).strip(),
                    value_eok=pct,
                    context_label="퍼센트",
                    position=m.start(),
                )
            )

        # 레버리지 배율
        for m in _LEVERAGE_RE.finditer(narration):
            try:
                lev = float(m.group(1).replace(",", ""))
            except (ValueError, TypeError):
                continue
            results.append(
                _ExtractedNumber(
                    raw=m.group(0).strip(),
                    value_eok=lev,
                    context_label="레버리지",
                    position=m.start(),
                )
            )

        return results

    @staticmethod
    def _guess_label(match_text: str, full_text: str, pos: int) -> str:
        """매칭 텍스트 주변에서 키워드를 추정해 라벨 반환."""
        context = full_text[max(0, pos - 30) : pos + len(match_text) + 30]
        for kw in [
            "잔고",
            "자본금",
            "자본",
            "현금",
            "자산",
            "포지션",
            "투자금",
            "수익",
            "원금",
            "손실",
            "연봉",
            "매출",
            "부채",
            "세금",
            "배당",
            "펀드",
            "대출",
            "예치금",
            "보유금",
            "운용금",
            "총액",
            "순이익",
        ]:
            if kw in context:
                return kw
        return "금액"

    # ── 2. FactLedger 교차 검증 ──────────────────────────────────

    def _check_against_ledger(self, extracted: list[_ExtractedNumber], ep_num: int) -> list[dict]:
        """추출된 숫자와 FactLedger 수치를 교차 비교. 5% 허용 오차."""
        if not self._fact_ledger:
            return []
        nums = self._fact_ledger.get_numbers()
        if not nums:
            return []

        warnings: list[dict] = []
        tolerance = 0.05  # 5%

        for ext in extracted:
            if ext.context_label in ("퍼센트", "레버리지"):
                continue
            for fl_key, fl_val in nums.items():
                if not isinstance(fl_val, dict):
                    continue
                ledger_value = fl_val.get("value")
                if ledger_value is None:
                    continue
                # 라벨 매칭: 정확 매칭 or 동의어 매칭 or 부분 문자열
                if not self._label_matches(ext.context_label, fl_key):
                    continue
                # 값 비교
                try:
                    ledger_eok = self._to_eok(ledger_value, fl_val.get("unit", ""))
                except (ValueError, TypeError):
                    continue
                if ledger_eok == 0:
                    continue
                diff = abs(ext.value_eok - ledger_eok)
                ratio = diff / abs(ledger_eok)
                if ratio > tolerance:
                    warnings.append(
                        {
                            "check": "FactLedger 교차",
                            "severity": "MAJOR",
                            "text": (
                                f"[수치 불일치] 원고 '{ext.raw}' ({ext.value_eok:.1f}억) "
                                f"vs FactLedger '{fl_key}'={ledger_eok:.1f}억 "
                                f"(차이 {diff:.1f}억, {ratio:.0%})"
                            ),
                        }
                    )
        return warnings

    def _label_matches(self, manuscript_label: str, ledger_key: str) -> bool:
        """원고 라벨과 FactLedger 키가 동의어인지 확인."""
        if not manuscript_label or not ledger_key:
            return False
        ml = manuscript_label.strip()
        lk = ledger_key.strip()
        # 정확 매칭
        if ml == lk or ml in lk or lk in ml:
            return True
        # 동의어 매칭
        for canonical, synonyms in self._SYNONYM_MAP.items():
            combined = synonyms | {canonical}
            if ml in combined and lk in combined:
                return True
            # FactLedger key에 canonical/synonym이 포함된 경우
            if ml in combined and any(s in lk for s in combined):
                return True
            if lk in combined and any(s in ml for s in combined):
                return True
        return False

    @staticmethod
    def _to_eok(value, unit: str) -> float:
        """FactLedger value를 억 단위 float로 변환."""
        s = str(value).replace(",", "").strip()
        unit = str(unit).strip()
        try:
            num = float(re.sub(r"[^\d.\-]", "", s))
        except (ValueError, TypeError):
            return 0.0
        if "만" in unit:
            return num / 10000
        if "원" in unit and "억" not in unit and "만" not in unit:
            return num / 1_0000_0000
        # 기본적으로 억 단위로 가정
        return num

    # ── 3. 산술 일관성 검사 ──────────────────────────────────────

    def _check_arithmetic(self, extracted: list[_ExtractedNumber], text: str) -> list[dict]:
        """합산 패턴(A+B=C)과 레버리지 계산(A×N=C) 검증."""
        narration = _DIALOGUE_RE.sub("", text)
        warnings: list[dict] = []
        tolerance_eok = 0.1  # 0.1억 = 1000만원

        # A + B = C 패턴
        for m in _SUM_PATTERN.finditer(narration):
            try:
                a = float(m.group(1).replace(",", ""))
                a_unit = m.group(2)
                b = float(m.group(3).replace(",", ""))
                b_unit = m.group(4)
                c = float(m.group(5).replace(",", ""))
                c_unit = m.group(6)
                a_eok = a if a_unit == "억" else a / 10000
                b_eok = b if b_unit == "억" else b / 10000
                c_eok = c if c_unit == "억" else c / 10000
                expected = a_eok + b_eok
                if abs(expected - c_eok) > tolerance_eok:
                    warnings.append(
                        {
                            "check": "산술 일관성",
                            "severity": "MAJOR",
                            "text": (
                                f"[산술 불일치] {a}{a_unit} + {b}{b_unit} = {expected:.1f}억이어야 하나 "
                                f"원고에서 {c}{c_unit}({c_eok:.1f}억)으로 표기 (차이 {abs(expected - c_eok):.1f}억)"
                            ),
                        }
                    )
            except (ValueError, TypeError):
                continue

        # 레버리지 계산: A × N배 = C
        for m in _LEVERAGE_CALC_RE.finditer(narration):
            try:
                base = float(m.group(1).replace(",", ""))
                base_unit = m.group(2)
                mult = float(m.group(3).replace(",", ""))
                result = float(m.group(4).replace(",", ""))
                result_unit = m.group(5)
                base_eok = base if base_unit == "억" else base / 10000
                result_eok = result if result_unit == "억" else result / 10000
                expected = base_eok * mult
                if abs(expected - result_eok) > tolerance_eok:
                    warnings.append(
                        {
                            "check": "산술 일관성",
                            "severity": "MAJOR",
                            "text": (
                                f"[레버리지 불일치] {base}{base_unit} × {mult:.0f}배 = {expected:.1f}억이어야 하나 "
                                f"원고에서 {result}{result_unit}({result_eok:.1f}억)으로 표기"
                            ),
                        }
                    )
            except (ValueError, TypeError):
                continue

        # 레버리지 수익률(%) 검증: "X달러 → Y달러 × N배 → Z%" 패턴
        warnings.extend(self._check_leverage_return_pct(narration))

        return warnings

    _LEVERAGE_PCT_RE = re.compile(
        r"(\d[\d.]*)\s*달러[^.。\n]{0,60}?(\d[\d.]*)\s*달러[^.。\n]{0,80}?"
        r"(\d[\d.]*)\s*배[^.。\n]{0,60}?"
        r"(?:수익률|수익)[^.。\n]{0,30}?(\d[\d.]*)\s*%",
    )

    def _check_leverage_return_pct(self, narration: str) -> list[dict]:
        """[NC-1] 달러 가격 변동 × 레버리지 → 수익률(%) 정합성 검증."""
        warnings: list[dict] = []
        for m in self._LEVERAGE_PCT_RE.finditer(narration):
            try:
                price_a = float(m.group(1).replace(",", ""))
                price_b = float(m.group(2).replace(",", ""))
                leverage = float(m.group(3).replace(",", ""))
                claimed_pct = float(m.group(4).replace(",", ""))
                if price_a <= 0 or leverage <= 0:
                    continue
                expected_pct = abs(price_b - price_a) / price_a * leverage * 100
                # 10%p 이상 괴리 시 경고
                if abs(expected_pct - claimed_pct) > 10.0:
                    warnings.append(
                        {
                            "check": "레버리지 수익률",
                            "severity": "MAJOR",
                            "text": (
                                f"[레버리지 수익률 불일치] {price_a}달러→{price_b}달러 × {leverage:.0f}배 "
                                f"= 약 {expected_pct:.1f}%이어야 하나 원고에서 {claimed_pct:.1f}%로 표기"
                            ),
                        }
                    )
            except (ValueError, TypeError):
                continue
        return warnings

    # ── 4. 직함 변경 감지 ────────────────────────────────────────

    def _check_title_consistency(self, text: str, ep_num: int) -> list[dict]:
        """원고 내 직함과 이전 화 직함을 비교. 승진은 허용, 무단 변경은 경고."""
        if not self._db or ep_num <= 1:
            return []

        narration = _DIALOGUE_RE.sub("", text)
        current_titles: dict[str, str] = {}
        for m in _TITLE_RE.finditer(narration):
            name, title = m.group(1), m.group(2)
            current_titles[name] = title

        if not current_titles:
            return []

        # 직전 3화 원고에서 직함 이력 수집
        prev_titles: dict[str, set[str]] = {}
        for prev_ep in range(max(1, ep_num - 3), ep_num):
            try:
                ms_row = self._db.get_manuscript(prev_ep)
                if not ms_row:
                    continue
                prev_text = ms_row.get("manuscript", "") or ms_row.get("text", "")
                if not prev_text:
                    continue
                prev_narration = _DIALOGUE_RE.sub("", prev_text)
                for m in _TITLE_RE.finditer(prev_narration):
                    pname, ptitle = m.group(1), m.group(2)
                    prev_titles.setdefault(pname, set()).add(ptitle)
            except Exception as _e:
                logging.debug("[NC-1] _check_title_consistency prev_titles 수집 실패 ep=%d: %s", prev_ep, _e)
                continue

        warnings: list[dict] = []
        for name, cur_title in current_titles.items():
            if name not in prev_titles:
                continue
            prev_set = prev_titles[name]
            if cur_title in prev_set:
                continue
            # 승진 여부 판별
            cur_rank = _TITLE_RANK.get(cur_title)
            is_promotion = False
            for pt in prev_set:
                prev_rank = _TITLE_RANK.get(pt)
                if (
                    cur_rank is not None
                    and prev_rank is not None
                    and cur_rank[0] == prev_rank[0]
                    and cur_rank[1] > prev_rank[1]
                ):
                    is_promotion = True
                    break
            if not is_promotion:
                warnings.append(
                    {
                        "check": "직함 변경",
                        "severity": "MAJOR",
                        "text": (
                            f"[직함 무단 변경] '{name}'의 직함이 "
                            f"{'/'.join(sorted(prev_set))} → {cur_title}로 변경됨 "
                            f"(승진 이벤트 없이 변경된 경우 연속성 오류)"
                        ),
                    }
                )

        return warnings

    # ── 5. "처음" 이벤트 모순 ────────────────────────────────────

    def _check_event_ordering(self, text: str, ep_num: int) -> list[dict]:
        """'처음/최초/첫' 마커가 이전 화에서 이미 발생한 이벤트를 참조하면 경고."""
        if not self._db or ep_num <= 1:
            return []

        narration = _DIALOGUE_RE.sub("", text)
        first_events: list[tuple[str, str]] = []
        for m in _FIRST_TIME_RE.finditer(narration):
            event_desc = m.group(1).strip()
            if len(event_desc) >= 2:
                first_events.append((m.group(0).strip(), event_desc))

        if not first_events:
            return []

        # 이전 화 episode_bibles에서 이벤트 키워드 수집
        prev_events_text = ""
        for prev_ep in range(max(1, ep_num - 10), ep_num):
            try:
                bible = self._db.get_episode_bible(prev_ep)
                if bible:
                    # state_changes, reveals, new_items 등에서 텍스트 수집
                    for key in ("state_changes", "reveals", "new_items", "relationship_changes"):
                        val = bible.get(key)
                        if val:
                            prev_events_text += " " + str(val)
            except Exception as _e:
                logging.debug("[NC-1] _check_event_ordering bible 조회 실패 ep=%d: %s", prev_ep, _e)
                continue

        # 직전 3화 원고에서도 텍스트 수집
        for prev_ep in range(max(1, ep_num - 3), ep_num):
            try:
                ms_row = self._db.get_manuscript(prev_ep)
                if ms_row:
                    prev_ms = ms_row.get("manuscript", "") or ms_row.get("text", "")
                    if prev_ms:
                        prev_events_text += " " + prev_ms[:5000]
            except Exception as _e:
                logging.debug("[NC-1] _check_event_ordering 원고 조회 실패 ep=%d: %s", prev_ep, _e)
                continue

        if not prev_events_text:
            return []

        warnings: list[dict] = []
        for full_match, event_desc in first_events:
            # 이벤트 핵심 키워드 (2글자 이상 한글 단어들, 조사 제거)
            raw_keywords = re.findall(r"[\uac00-\ud7a3]{2,}", event_desc)
            keywords = [self._strip_particle(kw) for kw in raw_keywords]
            keywords = [kw for kw in keywords if len(kw) >= 2]
            if not keywords:
                continue
            # 키워드 2개 이상 이전 텍스트에 존재하면 모순
            match_count = sum(1 for kw in keywords if kw in prev_events_text)
            if match_count >= 2 or (len(keywords) == 1 and keywords[0] in prev_events_text):
                warnings.append(
                    {
                        "check": "이벤트 순서",
                        "severity": "MINOR",
                        "text": (
                            f"[\"처음\" 모순 의심] '{full_match[:40]}' — "
                            f"이전 화에서 유사 이벤트({', '.join(keywords[:3])}) 존재 가능성. "
                            f"실제 '처음'인지 확인 필요"
                        ),
                    }
                )

        return warnings

    @staticmethod
    def _strip_particle(word: str) -> str:
        """한국어 단어에서 흔한 조사/어미를 제거."""
        # 긴 접미사부터 시도
        for suffix in (
            "에서는",
            "에서",
            "에게",
            "으로",
            "이라",
            "에는",
            "에",
            "을",
            "를",
            "이",
            "가",
            "은",
            "는",
            "의",
            "와",
            "과",
            "도",
            "로",
            "만",
        ):
            if len(word) > len(suffix) + 1 and word.endswith(suffix):
                return word[: -len(suffix)]
        return word

    # ── 6. [NC-2 GAP-2] 퍼센트/비율 구성 검증 ────────────────────

    def _check_percent_composition(
        self,
        extracted: list[_ExtractedNumber],
        text: str,
    ) -> list[dict]:
        """원고의 퍼센트 수치를 FactLedger 기반으로 역산 검증. 2%p 허용."""
        if not self._fact_ledger:
            return []
        nums = self._fact_ledger.get_numbers()
        if not nums:
            return []

        narration = _DIALOGUE_RE.sub("", text)
        warnings: list[dict] = []

        for m in _PERCENT_COMPOSITION_RE.finditer(narration):
            try:
                stated_pct = float(m.group(1).replace(",", ""))
            except (ValueError, TypeError):
                continue

            # 매칭 텍스트에서 키워드 판별
            match_ctx = narration[max(0, m.start() - 20) : m.end()]
            for kw, (numerator_label, denominator_label) in _PERCENT_COMPOSITION_KEYWORDS.items():
                if kw not in match_ctx:
                    continue
                # FactLedger에서 분자/분모 값 탐색
                numer_val = self._find_ledger_value(nums, numerator_label)
                denom_val = self._find_ledger_value(nums, denominator_label)
                if numer_val is None or denom_val is None or denom_val == 0:
                    continue
                computed_pct = (numer_val / denom_val) * 100
                diff_pp = abs(stated_pct - computed_pct)
                if diff_pp > 2.0:
                    warnings.append(
                        {
                            "check": "퍼센트 구성",
                            "severity": "MAJOR",
                            "text": (
                                f"[비율 불일치] 원고 '{kw} {stated_pct}%' "
                                f"vs 역산({numerator_label}/{denominator_label}) "
                                f"= {computed_pct:.1f}% (차이 {diff_pp:.1f}%p)"
                            ),
                        }
                    )
                break  # 첫 매칭 키워드로 충분

        return warnings

    def _find_ledger_value(self, nums: dict, label: str) -> float | None:
        """FactLedger nums에서 label과 매칭되는 억 단위 값을 찾는다."""
        for fl_key, fl_val in nums.items():
            if not isinstance(fl_val, dict):
                continue
            ledger_value = fl_val.get("value")
            if ledger_value is None:
                continue
            if self._label_matches(label, fl_key):
                try:
                    return self._to_eok(ledger_value, fl_val.get("unit", ""))
                except (ValueError, TypeError):
                    continue
        return None

    # ── 7. [NC-2 GAP-4] NPC 동명이인 감지 ────────────────────────

    def _check_npc_name_collision(self, text: str) -> list[dict]:
        """동일 이름의 NPC가 2명 이상 등록되었거나, 원고에서 혼동 가능한 경우 경고."""
        if not self._world_state:
            return []

        def _normalize_npc_name(name: str) -> str:
            # [M-4] 괄호 접미사 제거: "박성호 (담당 PB)" -> "박성호"
            return re.sub(r"\s*\(.*?\)\s*$", "", str(name or "")).strip()

        # NPC 이름 목록 취득
        npcs = getattr(self._world_state, "npcs", None)
        if not npcs:
            return []

        # NPC 이름 → 역할/설명 매핑
        name_to_roles: dict[str, list[str]] = {}
        name_aliases: dict[str, set[str]] = {}
        if isinstance(npcs, dict):
            for npc_id, npc_data in npcs.items():
                raw_name = npc_data.get("name", "") if isinstance(npc_data, dict) else str(npc_data)
                name = _normalize_npc_name(raw_name)
                if not name or len(name) < 2:
                    continue
                role = ""
                if isinstance(npc_data, dict):
                    role = npc_data.get("role", "") or npc_data.get("title", "") or npc_id
                name_to_roles.setdefault(name, []).append(role)
                if raw_name:
                    name_aliases.setdefault(name, set()).add(str(raw_name).strip())
        elif isinstance(npcs, list):
            for npc_data in npcs:
                if isinstance(npc_data, dict):
                    raw_name = npc_data.get("name", "")
                    name = _normalize_npc_name(raw_name)
                    if name and len(name) >= 2:
                        role = npc_data.get("role", "") or npc_data.get("title", "") or ""
                        name_to_roles.setdefault(name, []).append(role)
                        if raw_name:
                            name_aliases.setdefault(name, set()).add(str(raw_name).strip())

        warnings: list[dict] = []

        # Case 1: 등록된 NPC 중 동명이인
        for name, roles in name_to_roles.items():
            unique_roles = sorted({r for r in roles if r})
            aliases = sorted(name_aliases.get(name, {name}))
            if len(unique_roles) >= 2 or len(aliases) >= 2:
                roles_str = "/".join(unique_roles)[:60] if unique_roles else "역할 미상"
                alias_note = f", 표기: {'/'.join(aliases)[:40]}" if len(aliases) >= 2 else ""
                warnings.append(
                    {
                        "check": "NPC 동명이인",
                        "severity": "MINOR",
                        "text": (
                            f"[동명이인] '{name}' — NPC {len(roles)}명 등록 ({roles_str}){alias_note}. "
                            "별명/성씨로 구분 필요"
                        ),
                    }
                )

        # Case 2: 원고에서 NPC 이름이 다른 맥락으로 등장 (같은 이름, 다른 역할 의심)
        narration = _DIALOGUE_RE.sub("", text)
        for name, roles in name_to_roles.items():
            if len(roles) != 1:
                continue
            # 원고에서 이 이름이 등록된 역할과 다른 직함으로 등장하는지 확인
            registered_role = roles[0]
            name_pattern = re.compile(rf"{re.escape(name)}\s*(\S{{1,6}})")
            found_titles = set()
            for tm in name_pattern.finditer(narration):
                suffix = tm.group(1)
                for title in _TITLE_LIST:
                    if suffix.startswith(title):
                        found_titles.add(title)
            if len(found_titles) >= 2:
                warnings.append(
                    {
                        "check": "NPC 동명이인",
                        "severity": "MINOR",
                        "text": (
                            f"[동명이인 의심] '{name}' — 원고에서 복수 직함 "
                            f"({'/'.join(sorted(found_titles))}) 사용. "
                            f"동일 인물인지 확인 필요"
                        ),
                    }
                )

        return warnings

    # ── [TF-60] Stage 2 tactical_doc 산술 검증 ──────────────────────

    def check_tactical_doc(
        self,
        tactical_doc: str,
        arc_num: int,
        *,
        fact_ledger_snapshot: dict | None = None,
    ) -> list[dict]:
        """[TF-60] Stage 2 tactical_doc 산술 검증. check()의 서브셋.

        Advisory-only: REJECT 권한 없음 (대원칙 3 준수).
        검사: ①FactLedger 교차 ②산술 일관성(A+B=C, 레버리지) ③퍼센트 구성
        """
        if not tactical_doc or not tactical_doc.strip():
            return []

        warnings: list[dict] = []
        extracted = self._extract_all_numbers(tactical_doc)

        # 1. FactLedger 교차 (사용 가능한 경우)
        if self._fact_ledger:
            try:
                warnings.extend(self._check_against_ledger(extracted, arc_num))
            except Exception as e:
                logging.debug("[NC-1-S2] FactLedger 교차 실패: %s", e)

        # 2. 산술 일관성 (A+B=C, 레버리지, 레버리지 수익률%)
        try:
            warnings.extend(self._check_arithmetic(extracted, tactical_doc))
        except Exception as e:
            logging.debug("[NC-1-S2] 산술 검사 실패: %s", e)

        # 3. 퍼센트 구성 검증
        try:
            warnings.extend(self._check_percent_composition(extracted, tactical_doc))
        except Exception as e:
            logging.debug("[NC-1-S2] 퍼센트 구성 실패: %s", e)

        return warnings

    # ── 8. [NC-2 GAP-6] 연속 에피소드 도입부 유사도 ─────────────────

    @staticmethod
    def _check_opening_similarity(
        text: str,
        *,
        prev_manuscript: str | None = None,
        threshold: float = 0.40,
        opening_chars: int = 500,
    ) -> list[dict]:
        """직전 화와 현재 화 도입부의 3-gram 자카드 유사도 검사."""
        if not prev_manuscript or not prev_manuscript.strip():
            return []

        curr_opening = text[:opening_chars].strip()
        prev_opening = prev_manuscript[:opening_chars].strip()

        if len(curr_opening) < 50 or len(prev_opening) < 50:
            return []

        # 3-gram 생성
        curr_ngrams = {curr_opening[i : i + 3] for i in range(len(curr_opening) - 2)}
        prev_ngrams = {prev_opening[i : i + 3] for i in range(len(prev_opening) - 2)}

        if not curr_ngrams or not prev_ngrams:
            return []

        intersection = curr_ngrams & prev_ngrams
        union = curr_ngrams | prev_ngrams
        similarity = len(intersection) / len(union) if union else 0.0

        if similarity > threshold:
            return [
                {
                    "check": "도입부 유사도",
                    "severity": "MINOR",
                    "text": (f"[도입부 중복] 직전 화와 도입부 3-gram 유사도 {similarity:.0%}. 다양한 시작 필요"),
                }
            ]

        return []
