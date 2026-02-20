"""
[V40 Multi-Genre] 투자물 전용 Guard
[V57] 완전 구현 - 일관성 검증, 권위 위계, 타임라인 검증
투자물 장르의 전문성과 개연성을 유지
"""

from typing import Any

from .base_guard import BaseGuard


class InvestmentGuard(BaseGuard):
    """[투자물] 장르 전문성 보호자 + V57 완전 구현"""

    def __init__(self) -> None:
        super().__init__()
        cfg = self._load_genre_yaml("investment")

        self.FORBIDDEN_TERMS = cfg.get(
            "forbidden_terms",
            [
                "내공",
                "진기",
                "마나",
                "스킬",
                "던전",
                "게이트",
                "각성",
                "헌터",
                "검기",
                "검강",
                "초식",
                "보법",
                "무림",
                "강호",
                "문파",
                "장로",
                "마법",
                "주문",
                "포션",
                "엘프",
                "드워프",
                "드래곤",
                "오크",
                "레벨업",
                "경험치",
                "스테이터스",
                "인벤토리",
                "버프",
                "디버프",
            ],
        )

        # 투자물 필수 금융 용어 (정확하게 사용해야 함)
        self.FINANCIAL_TERMS = cfg.get(
            "financial_terms",
            [
                "주식",
                "채권",
                "펀드",
                "선물",
                "옵션",
                "공매도",
                "매수",
                "매도",
                "상장",
                "IPO",
                "M&A",
                "배당",
                "액면분할",
                "증자",
                "감자",
                "자본금",
                "부채",
                "자산",
                "유동성",
                "레버리지",
                "헤지",
                "PER",
                "PBR",
                "ROE",
                "EBITDA",
                "시가총액",
                "거래량",
                "차트",
                "캔들",
                "이동평균선",
                "거래소",
                "코스피",
                "코스닥",
                "재무제표",
                "손익계산서",
                "대차대조표",
                "현금흐름표",
                "신용등급",
                "회사채",
                "전환사채",
                "워런트",
                "스톡옵션",
            ],
        )

        # 투자물 필수 개념
        self.MANDATORY_CONCEPTS = cfg.get(
            "mandatory_concepts",
            [
                "시장 논리와 경제 상식의 준수",
                "자본 증식의 합리적 근거",
                "재무 지표와 기업 가치 분석",
                "투자 전략의 구체적 묘사",
            ],
        )

        # [V57] 자산 규모 등급
        self._wealth_hierarchy = cfg.get(
            "wealth_hierarchy", ["무일푼", "소시민", "중산층", "부유층", "거부", "재벌", "대재벌", "국가급", "글로벌급"]
        )

        # [V57] 자산 규모별 범위 (원)
        self._wealth_ranges = {
            "무일푼": (0, 100_000_000),  # 0~1억
            "소시민": (100_000_000, 1_000_000_000),  # 1억~10억
            "중산층": (1_000_000_000, 10_000_000_000),  # 10억~100억
            "부유층": (10_000_000_000, 100_000_000_000),  # 100억~1000억
            "거부": (100_000_000_000, 1_000_000_000_000),  # 1000억~1조
            "재벌": (1_000_000_000_000, 10_000_000_000_000),  # 1조~10조
            "대재벌": (10_000_000_000_000, 100_000_000_000_000),  # 10조~100조
            "국가급": (100_000_000_000_000, float("inf")),  # 100조 이상
        }

        # [V57] 자산 규모별 행동 불가 패턴
        self._wealth_action_limits = cfg.get(
            "wealth_action_limits",
            {
                "무일푼": [r"대기업.*인수", r"건물.*매입", r"펀드.*설립", r"유상증자.*참여"],
                "소시민": [r"대기업.*인수", r"상장사.*대주주", r"펀드.*설립"],
                "중산층": [r"대기업.*인수", r"재벌.*협상", r"국가급.*투자"],
                "부유층": [r"재벌.*인수", r"국가급.*로비"],
                "거부": [r"대재벌.*인수", r"글로벌.*패권"],
            },
        )

        # [V57] 투자 유형별 최소 자본 요건
        self._investment_requirements = {
            "개인 주식": 100_000,  # 10만원
            "일반 펀드": 1_000_000,  # 100만원
            "사모펀드": 100_000_000,  # 1억
            "부동산 경매": 10_000_000,  # 1000만원
            "부동산 매입": 100_000_000,  # 1억
            "비상장 투자": 50_000_000,  # 5000만원
            "벤처 투자": 100_000_000,  # 1억
            "기업 인수": 1_000_000_000,  # 10억
            "상장사 인수": 100_000_000_000,  # 1000억
            "재벌 인수": 10_000_000_000_000,  # 10조
        }

        # [V57] 수익률 현실성 범위 (연간 %)
        self._realistic_returns = {
            "예금": (1, 5),
            "채권": (2, 8),
            "주식": (-50, 200),  # 개별 종목
            "주식 인덱스": (-30, 50),  # 지수 추종
            "부동산": (-20, 100),
            "사모펀드": (-30, 300),
            "벤처": (-100, 10000),  # 고위험 고수익
            "암호화폐": (-90, 50000),  # 극단적 변동성
        }

        # [V57] 상태별 불가능 행동
        self._status_action_limits = cfg.get(
            "status_action_limits",
            {
                "파산": [r"투자", r"대출", r"신용", r"계약"],
                "신용불량": [r"대출", r"신용", r"카드", r"보증"],
                "수사중": [r"해외.*이동", r"자산.*이전", r"은닉"],
                "구속": [r"자유.*활동", r"투자", r"회의.*참석"],
                "자금경색": [r"대규모.*투자", r"추가.*매수", r"인수"],
            },
        )

    def get_genre_name(self) -> str:
        return "투자물(INVESTMENT)"

    def _should_check_english(self) -> bool:
        """투자물은 현대 배경이므로 영어 완화 (금융 용어에 영어 많음)"""
        return False

    def _should_check_numbers(self) -> bool:
        """투자물은 정확한 수치가 중요하므로 아라비아 숫자 필수"""
        return False

    def get_v20_purism_prompt(self) -> str:
        """투자물 장르 전문성 지침"""
        return f"""
[💼 V40 투자물 장르 가이드라인 (Investment Genre Professionalism)]

1. **장르 교란 금지**: 판타지/무협 용어({", ".join(self.FORBIDDEN_TERMS[:8])} 등)를 사용하지 마라. 현실적인 투자물 세계관을 유지하라.
2. **금융 상식 준수**: 모든 투자 행위는 시장 논리와 경제 법칙에 부합해야 한다. 근거 없는 주가 폭등이나 비현실적 수익률은 금지한다.
3. **전문 용어의 정확성**: {", ".join(self.FINANCIAL_TERMS[:10])} 등의 금융 용어를 정확하게 사용하라.
4. **자본 증식의 개연성**: 주인공의 재산 증가는 반드시 구체적인 투자 전략과 시장 상황에 기반해야 한다.
5. **리스크와 보상**: 모든 투자에는 위험이 따른다. 손실 가능성과 리스크 관리도 함께 묘사하라.
6. **인물 관계망**: 투자자, 기업인, 정치인, 언론인 등 다양한 이해관계자들의 역학 관계를 입체적으로 그려라.
7. **법률과 윤리**: 내부자거래, 주가조작 등 불법 행위는 그 결과(처벌 위험)도 함께 다뤄야 한다.
8. **시대적 배경**: 현대적 금융 시스템(전자거래, 블록체인, 핀테크 등)을 자연스럽게 활용하라.
9. **필수 표현 요소**: {", ".join(self.MANDATORY_CONCEPTS)}

[개연성 체크리스트]
- 투자 수익률이 현실적인 범위 내에 있는가?
- 주가 변동에 명확한 이유(뉴스, 실적, 이슈)가 있는가?
- 주인공의 정보력과 판단 근거가 구체적인가?
- 시장 상황과 경제 지표가 일관성 있게 묘사되는가?
"""

    # ========================================================================
    # [V57] 일관성 검증 구현 (투자물 특화)
    # ========================================================================

    def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]:
        """
        [V57] 투자물 - 현재 상태에서 불가능한 행동 패턴 반환

        동적 규칙 생성: HUD의 wealth, status에서 추론
        """
        actions = []

        # 1. 상태 기반 제한 (파산, 신용불량 등)
        status = current_state.get("status", "")
        if isinstance(status, str):
            for status_keyword, patterns in self._status_action_limits.items():
                if status_keyword in status:
                    for pattern in patterns:
                        actions.append(
                            {"pattern": pattern, "reason": f"상태 '{status_keyword}'로 인해 불가", "severity": "HIGH"}
                        )

        # 2. 자산 규모 기반 제한
        wealth = current_state.get("wealth", current_state.get("assets", 0))
        wealth_class = self._get_wealth_class(wealth)
        if wealth_class and wealth_class in self._wealth_action_limits:
            for pattern in self._wealth_action_limits[wealth_class]:
                actions.append(
                    {"pattern": pattern, "reason": f"자산 규모 '{wealth_class}'에서 불가", "severity": "HIGH"}
                )

        # 3. 유동성 위기
        liquidity = current_state.get("liquidity", current_state.get("cash", 0))
        if isinstance(liquidity, int | float) and liquidity <= 0:
            actions.append(
                {
                    "pattern": r"추가.*매수|신규.*투자|인수.*제안",
                    "reason": "유동성 부족으로 신규 투자 불가",
                    "severity": "CRITICAL",
                }
            )

        # 4. 회귀자 미래 정보 제한 (특수)
        is_regressor = current_state.get("is_regressor", False)
        regression_year = current_state.get("regression_year", None)
        current_year = current_state.get("current_year", None)

        if is_regressor and regression_year and current_year:
            # 회귀 시점 이후의 정보는 사용 불가
            if current_year >= regression_year:
                actions.append(
                    {
                        "pattern": r"미래.*정보|예지|역사.*변경",
                        "reason": "회귀 시점 이후 - 미래 정보 없음",
                        "severity": "CRITICAL",
                    }
                )

        return actions

    def _get_wealth_class(self, wealth: float) -> str:
        """자산 규모에 따른 등급 반환"""
        if not isinstance(wealth, int | float):
            return "소시민"

        for class_name, (min_val, max_val) in self._wealth_ranges.items():
            if min_val <= wealth < max_val:
                return class_name
        return "글로벌급"

    def get_justification_patterns(self) -> list[str]:
        """
        [V57] 투자물 - 정당화로 인정되는 표현 패턴
        """
        return [
            # 미래 정보 활용 (회귀물)
            r"미래.*기억",
            r"과거.*경험",
            r"역사.*알",
            r"전생.*정보",
            # 정당한 투자
            r"분석.*결과",
            r"재무제표.*검토",
            r"시장.*조사",
            r"전문가.*자문",
            # 인맥 활용
            r"인맥.*통해",
            r"정보.*입수",
            r"내부.*관계자",
            r"업계.*소식",
            # 위험 감수
            r"위험.*감수",
            r"도박.*같",
            r"올인",
            r"레버리지",
            # 합법적 기회
            r"공개.*정보",
            r"공시.*확인",
            r"뉴스.*보도",
            r"시장.*흐름",
        ]

    def get_hierarchy_rules(self) -> dict[str, Any]:
        """
        [V57] 투자물 - 자산/지위 위계 규칙
        """
        return {
            "wealth_classes": self._wealth_hierarchy,
            "titles": {
                "무일푼": ["개미", "서민"],
                "소시민": ["개미", "소액투자자"],
                "중산층": ["개인투자자", "슈퍼개미"],
                "부유층": ["자산가", "투자자"],
                "거부": ["큰손", "기관급"],
                "재벌": ["재벌", "기업인"],
                "대재벌": ["재벌 총수", "그룹 회장"],
                "국가급": ["경제 거물", "국가급 자산가"],
                "글로벌급": ["세계적 부호", "글로벌 투자자"],
            },
            "violations": {
                "무일푼": [r"재벌", r"대기업", r"인수합병"],
                "소시민": [r"재벌", r"대기업 인수"],
                "중산층": [r"재벌", r"대규모 인수"],
                "부유층": [r"대재벌", r"국가급"],
            },
        }

    def get_technique_effect_rules(self) -> dict[str, dict[str, Any]]:
        """
        [V57] 투자물 - 투자 유형별 효능 규칙
        """
        return {
            "주식 매수": {
                "effect_type": "investment",
                "effect_scope": ["자산 증가", "배당", "의결권"],
                "cannot_be_used_for": ["즉시 현금화", "담보"],
                "risk": "원금 손실 가능",
            },
            "공매도": {
                "effect_type": "short",
                "effect_scope": ["하락 시 수익", "헤지"],
                "cannot_be_used_for": ["무제한 수익", "장기 보유"],
                "risk": "무제한 손실 가능",
            },
            "M&A": {
                "effect_type": "acquisition",
                "effect_scope": ["기업 지배", "시너지", "구조조정"],
                "cannot_be_used_for": ["빠른 수익", "소액 투자"],
                "requirements": ["대규모 자금", "전문 인력", "법률 검토"],
            },
            "IPO": {
                "effect_type": "listing",
                "effect_scope": ["자금 조달", "기업 가치 상승", "유동성"],
                "cannot_be_used_for": ["비공개 유지", "소규모 기업"],
                "requirements": ["재무 요건", "감사", "주관사"],
            },
            "부동산": {
                "effect_type": "real_estate",
                "effect_scope": ["임대 수익", "시세 차익", "담보"],
                "cannot_be_used_for": ["빠른 현금화", "소액 분할"],
                "risk": "유동성 낮음, 규제 영향",
            },
        }

    # ========================================================================
    # [V57] 권위 위계 검증 (투자물 특화)
    # ========================================================================

    def get_authority_hierarchy(self) -> dict[str, Any]:
        """
        [V57] 투자물 - 기업/금융 권위 위계
        """
        return {
            "positions": ["회장", "부회장", "CEO", "CFO", "임원", "부장", "과장", "대리", "사원"],
            "position_titles": {
                "회장": ["회장", "총수", "오너"],
                "부회장": ["부회장", "부총수"],
                "CEO": ["대표이사", "CEO", "사장"],
                "CFO": ["재무이사", "CFO", "재무담당"],
                "임원": ["이사", "상무", "전무"],
                "부장": ["부장", "팀장"],
                "과장": ["과장", "파트장"],
                "대리": ["대리", "선임"],
                "사원": ["사원", "신입"],
            },
            "authority_scope": {
                "회장": ["인사", "투자", "M&A", "전략"],
                "CEO": ["경영", "대외", "인사"],
                "CFO": ["재무", "투자", "자금"],
                "임원": ["부서 운영", "보고"],
                "부장": ["팀 운영", "보고"],
            },
        }

    def get_delegation_patterns(self) -> list[str]:
        """
        [V57] 투자물 - 권위 위임 정당화 패턴
        """
        return [
            r"회장.*지시",
            r"대표.*위임",
            r"이사회.*승인",
            r"권한.*부여",
            r"대행.*명령",
            r"비상.*상황",
            r"긴급.*결정",
        ]

    # ========================================================================
    # [V57] 갈등 및 해소 검증
    # ========================================================================

    def get_hostile_action_types(self) -> list[str]:
        """
        [V57] 투자물 - 적대적 행동 유형
        """
        return [
            "배신",
            "횡령",
            "배임",
            "적대적 인수",
            "공매도 공격",
            "주가조작",
            "정보 유출",
            "소송",
            "고발",
            "언론 플레이",
            "여론전",
            "세무조사",
            "감사 공격",
        ]

    def get_resolution_patterns(self) -> list[str]:
        """
        [V57] 투자물 - 갈등 해소 패턴
        """
        return [
            # 합의
            r"합의",
            r"화해",
            r"협상.*타결",
            r"배상.*받",
            # 승리
            r"인수.*성공",
            r"소송.*승소",
            r"방어.*성공",
            r"주가.*반등",
            # 보복
            r"역인수",
            r"경영권.*탈환",
            r"파산.*신청",
            r"형사.*고발",
            # 굴복
            r"백기.*투항",
            r"지분.*매각",
            r"퇴진",
            r"사퇴",
        ]

    # ========================================================================
    # [V57] 투자 검증 헬퍼
    # ========================================================================

    def validate_investment_scale(self, investment_type: str, amount: float, current_wealth: float) -> tuple[bool, str]:
        """
        [V57] 투자 규모 적정성 검증

        Args:
            investment_type: 투자 유형
            amount: 투자 금액
            current_wealth: 현재 총 자산

        Returns:
            (허용 여부, 사유)
        """
        # 최소 자본 요건 체크
        min_required = self._investment_requirements.get(investment_type, 0)
        if amount < min_required:
            return False, f"[V57] '{investment_type}' 최소 금액 미달: {amount:,}원 < {min_required:,}원"

        # 자산 대비 비율 체크 (올인 경고)
        if current_wealth > 0:
            ratio = amount / current_wealth
            if ratio > 0.9:
                return True, f"[V57] 경고: 자산의 {ratio * 100:.0f}% 투자 (올인)"
            elif ratio > 0.5:
                return True, f"[V57] 주의: 자산의 {ratio * 100:.0f}% 투자 (고비중)"

        return True, f"[V57] '{investment_type}' 투자 적정"

    def validate_return_rate(
        self, investment_type: str, return_rate: float, period_years: float = 1
    ) -> tuple[bool, str]:
        """
        [V57] 수익률 현실성 검증

        Args:
            investment_type: 투자 유형
            return_rate: 수익률 (%)
            period_years: 투자 기간 (년)

        Returns:
            (허용 여부, 사유)
        """
        ranges = self._realistic_returns.get(investment_type)
        if not ranges:
            return True, "수익률 범위 정보 없음"

        min_rate, max_rate = ranges

        # 연환산 수익률
        annualized = return_rate / period_years if period_years > 0 else return_rate

        # [I-21] 단기 수익률 상한 — 일간 100%, 주간 500% (crypto 기준)
        if period_years > 0 and period_years < 0.1 and annualized > 1000:
            return (
                False,
                f"[I-21] 비현실적 단기 수익: {return_rate:.1f}% / {period_years:.3f}년 (연환산 {annualized:.0f}%)",
            )

        if annualized < min_rate:
            return True, f"[V57] 손실: {annualized:.1f}%/년 (범위 내)"
        elif annualized > max_rate:
            return False, f"[V57] 비현실적 수익률: {annualized:.1f}%/년 > {max_rate}% (최대)"

        return True, f"[V57] 수익률 현실적: {annualized:.1f}%/년"

    def validate_timeline_event(
        self, event_date: str, regression_date: str = None, current_date: str = None
    ) -> tuple[bool, str]:
        """
        [V57] 타임라인 이벤트 검증 (회귀물 특화)

        Args:
            event_date: 이벤트 발생 예정일
            regression_date: 회귀 시작 날짜
            current_date: 현재 서사 날짜

        Returns:
            (허용 여부, 사유)
        """
        # 간단한 날짜 비교 (YYYY-MM-DD 형식 가정)
        try:
            if regression_date and event_date < regression_date:
                return True, "[V57] 회귀 전 이벤트 - 미래 지식으로 활용 가능"
            elif current_date and event_date > current_date:
                return False, f"[V57] 미래 이벤트 사전 언급 불가: {event_date}"
        except Exception:
            pass

        return True, "[V57] 타임라인 정상"

    def get_finance_rules_prompt(self) -> str:
        """
        [V57] 금융 규칙 프롬프트 생성 (Writer/Architect 주입용)
        """
        return """
[V57 투자물 금융 메카닉스]

1. **자산 규모별 행동 제약**
   - 무일푼~소시민: 소액 주식, 적금 수준
   - 중산층~부유층: 부동산, 사모펀드 가능
   - 거부 이상: 기업 인수, M&A 가능

2. **투자 유형별 최소 자본**
   - 일반 주식: 10만원 이상
   - 사모펀드: 1억원 이상
   - 기업 인수: 10억원 이상
   - 상장사 인수: 1000억원 이상

3. **수익률 현실성**
   - 예금/채권: 연 1~8%
   - 주식: -50% ~ +200% (개별 종목)
   - 벤처: -100% ~ +10000% (극단적)
   - 암호화폐: -90% ~ +50000%

4. **회귀물 특수 규칙**
   - 회귀 시점 이전 정보만 활용 가능
   - 나비 효과로 역사 변경 가능성
   - 미래 지식 사용 시 명확한 근거 필요

5. **법률/윤리 제약**
   - 내부자 거래: 범죄, 처벌 묘사 필수
   - 주가 조작: 범죄, 조사 대상
   - 횡령/배임: 구속, 파산 가능성
"""

    # ========================================================================
    # [V66] run_deep_validation override
    # ========================================================================

    def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]:
        """[V66] Investment 심층 검증: base + 투자 규모/수익률 범위 검증."""
        import re

        result = super().run_deep_validation(manuscript, current_state or {})

        # 투자 규모 검증
        amount_patterns = re.findall(r"(\d+(?:,\d{3})*)\s*(억|만)\s*(?:원|달러|불)", manuscript)  # [V70] 단위 캡처 추가
        for amount_str, unit in amount_patterns:
            try:
                amount = int(amount_str.replace(",", ""))
                if unit == "억":  # [V70] 단위 승수 적용
                    amount *= 100_000_000
                elif unit == "만":
                    amount *= 10_000
                _wealth = float((current_state or {}).get("total_assets", 0) or 0)
                valid, msg = self.validate_investment_scale("개인 주식", amount, _wealth)  # [G20] 한국어 키 매칭
                if not valid:
                    result["violations"].append({"type": "investment_scale", "severity": "MEDIUM", "message": msg})
            except (ValueError, TypeError):
                pass

        # 수익률 범위 검증
        roi_patterns = re.findall(r"(\d+(?:\.\d+)?)\s*%", manuscript)
        for roi_str in roi_patterns:
            try:
                roi = float(roi_str)
                if roi > 100:
                    valid, msg = self.validate_return_rate("주식", roi, 1.0)  # [G20] 한국어 키 매칭
                    if not valid:
                        result["violations"].append({"type": "return_rate", "severity": "MEDIUM", "message": msg})
            except (ValueError, TypeError):
                pass

        result["has_critical"] = any(v.get("severity") in ("HIGH", "CRITICAL") for v in result["violations"])
        if result["violations"]:
            result["summary"] = "; ".join(v.get("message", "") for v in result["violations"][:5])
            result["feedback"] = f"[투자 Guard] {len(result['violations'])}건: {result['summary']}"
        return result
