"""
[V61.9] 요리물 전용 Guard
[V57] 완전 구현 - 일관성 검증, 권위 위계, 타임라인 검증
요리 업계의 전문성과 개연성을 유지
"""

from typing import Any

from .base_guard import BaseGuard


class CookingGuard(BaseGuard):
    """[요리물] 셰프 성장 + 식당 경영 전문성 보호자 + V57 완전 구현"""

    def __init__(self) -> None:
        super().__init__()
        cfg = self._load_genre_yaml("cooking")

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
                "상태창",
                "시스템 창",
                "퀘스트",
                "레이드",
            ],
        )

        self.COOKING_TERMS = cfg.get(
            "cooking_terms",
            [
                "마이야르",
                "캐러멜라이즈",
                "데글라제",
                "플랑베",
                "수비드",
                "블랑쉬",
                "브레이즈",
                "소테",
                "포칭",
                "콩피",
                "플레이팅",
                "미장플라스",
                "가니시",
                "아뮤즈부쉬",
                "식감",
                "풍미",
                "감칠맛",
                "우마미",
                "테루아",
                "코스요리",
                "아뮤즈",
                "앙트레",
                "디저트",
                "프리픽스",
                "미슐랭",
                "빕구르망",
                "고메",
                "파인다이닝",
                "가스트로펍",
                "원가율",
                "식재료 수급",
                "레시피 개발",
                "메뉴 엔지니어링",
                "주방장",
                "수셰프",
                "파티시에",
                "소믈리에",
                "바리스타",
                "식품위생",
                "HACCP",
                "콜드체인",
                "숙성",
                "발효",
            ],
        )

        self.MANDATORY_CONCEPTS = cfg.get(
            "mandatory_concepts",
            [
                "요리 과정의 감각적 묘사 (오감)",
                "식재료 선별과 수급의 현실성",
                "고객 관계와 평판의 개연성",
                "식당 경영의 사실적 반영",
            ],
        )

        self._chef_hierarchy = cfg.get(
            "chef_hierarchy",
            [
                "수습생",
                "준요리사",
                "요리사",
                "수석요리사",
                "셰프",
                "명셰프",
                "거장",
                "전설의요리인",
            ],
        )

        self._restaurant_hierarchy = cfg.get(
            "restaurant_hierarchy",
            [
                "포장마차",
                "동네식당",
                "맛집",
                "파인다이닝",
                "미슐랭1스타",
                "미슐랭2스타",
                "미슐랭3스타",
            ],
        )

        self._chef_action_limits = cfg.get(
            "chef_action_limits",
            {
                "수습생": [r"전국.*대회.*우승", r"미슐랭.*심사", r"TV.*출연.*셰프", r"해외.*유명.*레스토랑.*헤드셰프"],
                "준요리사": [r"전국.*대회.*우승", r"미슐랭.*획득", r"해외.*지점.*오픈"],
                "요리사": [r"미슐랭.*3스타", r"글로벌.*프랜차이즈", r"전설.*반열"],
                "수석요리사": [r"전설.*반열", r"글로벌.*요리.*제국"],
            },
        )

        self._status_action_limits = cfg.get(
            "status_action_limits",
            {
                "부상": [r"장시간.*조리", r"대량.*주문", r"대회.*출전", r"뜨거운.*불.*앞"],
                "미각상실": [r"신메뉴.*개발", r"맛.*평가", r"시식.*심사", r"레시피.*완성"],
                "자금난": [r"고급.*식재료", r"리모델링", r"지점.*확장", r"프리미엄"],
                "식중독사고": [r"영업.*정상", r"신뢰.*회복", r"미슐랭.*심사"],
                "폐업": [r"매출.*상승", r"고객.*방문", r"영업"],
            },
        )

        self._restaurant_requirements = {
            "동네식당": {"chef_rank": "요리사", "capital": 5_000_000},
            "맛집": {"chef_rank": "수석요리사", "reputation": 40, "regulars": 50},
            "파인다이닝": {"chef_rank": "셰프", "reputation": 60, "capital": 100_000_000},
            "미슐랭1스타": {"chef_rank": "셰프", "reputation": 75, "consistency": True},
            "미슐랭2스타": {"chef_rank": "명셰프", "reputation": 85, "innovation": True},
            "미슐랭3스타": {"chef_rank": "거장", "reputation": 95, "perfection": True},
        }

        self._competition_requirements = {
            "동네 요리 대회": {"chef_rank": "준요리사"},
            "지역 셰프 대회": {"chef_rank": "요리사", "reputation": 20},
            "전국 요리 대회": {"chef_rank": "수석요리사", "reputation": 40},
            "국제 요리 대회": {"chef_rank": "셰프", "reputation": 60},
            "TV 요리 프로그램": {"chef_rank": "수석요리사", "reputation": 50},
            "미슐랭 심사": {"restaurant_tier": "파인다이닝", "consistency": True},
        }

    def get_genre_name(self) -> str:
        return "요리물(COOKING)"

    def _should_check_english(self) -> bool:
        """요리물은 현대 배경이므로 영어 완화 (요리 용어에 외래어 많음)"""
        return False

    def _should_check_numbers(self) -> bool:
        """요리물은 매출/원가/가격 등 정확한 수치가 중요"""
        return False

    def get_v20_purism_prompt(self) -> str:
        """요리물 장르 전문성 지침"""
        return f"""
[🍳 V61.9 요리물 장르 가이드라인 (Cooking Genre Professionalism)]

1. **장르 교란 금지**: 판타지/무협 용어({", ".join(self.FORBIDDEN_TERMS[:8])} 등)를 사용하지 마라. 현실적인 요리/식당 세계관을 유지하라.
2. **요리 상식 준수**: 모든 조리 과정은 식품 과학과 현실에 부합해야 한다. 존재하지 않는 식재료나 비현실적 조리법은 금지한다.
3. **전문 용어의 정확성**: {", ".join(self.COOKING_TERMS[:10])} 등의 요리 용어를 정확하게 사용하라.
4. **성장의 개연성**: 주인공의 요리 실력 상승은 반드시 구체적인 수련/경험에 기반해야 한다.
5. **오감 묘사**: 요리를 글로 전달하라 - 향기, 맛, 식감, 색감, 소리(지글지글, 보글보글)를 감각적으로 묘사하라.
6. **식당 경영 현실성**: 원가율, 인건비, 임대료, 식재료 수급, 위생 관리 등 경영의 현실적 측면을 반영하라.
7. **식재료 일관성**: 계절성, 산지, 공급처를 고려한 재료 사용. 이전에 구할 수 없던 재료를 갑자기 사용 금지.
8. **시대적 배경**: 배달앱, SNS 마케팅, 미슐랭 가이드, 먹방 등 현대 외식 산업 트렌드를 자연스럽게 활용하라.
9. **필수 표현 요소**: {", ".join(self.MANDATORY_CONCEPTS)}
10. **전문가 반응 캘리브레이션**: 셰프의 반응은 등급·경험에 비례해야 한다. 그랑셰프급이 재료 원가 변동에 당황하면 안 된다(일상). 미슐랭 심사관 방문이나 식중독 사고에는 긴장해야 한다(실제 위기). 전문가는 주방의 일상적 압박에 침착하고, 진짜 비상 상황에만 반응한다.

[개연성 체크리스트]
- 요리 난이도가 주인공의 셰프 등급에 부합하는가?
- 식당 규모와 매출이 식당 등급에 현실적인가?
- 식재료 조달 경로가 확보되어 있는가?
- 고객 반응과 평판이 일관성 있게 묘사되는가?
"""

    # ========================================================================
    # [V57] 일관성 검증 구현 (요리물 특화)
    # ========================================================================

    def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]:
        """[V57] 요리물 - 현재 상태에서 불가능한 행동 패턴 반환"""
        actions = []

        # 1. 상태 기반 제한 (부상, 미각상실 등)
        status = current_state.get("status", current_state.get("condition", ""))
        if isinstance(status, str):
            for status_keyword, patterns in self._status_action_limits.items():
                if status_keyword in status:
                    for pattern in patterns:
                        actions.append(
                            {"pattern": pattern, "reason": f"상태 '{status_keyword}'로 인해 불가", "severity": "HIGH"}
                        )

        # 2. 셰프 등급 기반 제한
        chef_rank = current_state.get("chef_rank", "수습생")
        if isinstance(chef_rank, str):
            for rank_keyword, patterns in self._chef_action_limits.items():
                if rank_keyword in chef_rank:
                    for pattern in patterns:
                        actions.append(
                            {"pattern": pattern, "reason": f"셰프 등급 '{rank_keyword}'에서 불가", "severity": "HIGH"}
                        )

        # 3. 자금난
        capital = current_state.get("capital", "0원")
        # [TypeSafety] LLM이 capital을 숫자(0)로 반환할 수 있음
        _capital_is_broke = False
        if isinstance(capital, int | float):
            _capital_is_broke = capital <= 0
        elif isinstance(capital, str):
            # 숫자 문자열 시도
            try:
                _capital_is_broke = float(capital) <= 0
            except (TypeError, ValueError):
                _capital_is_broke = "0원" in capital or "마이너스" in capital or "적자" in capital
        if _capital_is_broke:
            actions.append(
                {
                    "pattern": r"고급.*식재료.*대량|리모델링|2호점|프리미엄.*장비",
                    "reason": "자금 부족으로 대규모 투자 불가",
                    "severity": "CRITICAL",
                }
            )

        # 4. 회귀자 미래 정보 제한 (특수)
        is_regressor = current_state.get("is_regressor", False)
        regression_year = current_state.get("regression_year", None)
        current_year = current_state.get("current_year", None)

        if is_regressor and regression_year and current_year:
            if current_year >= regression_year:
                actions.append(
                    {
                        "pattern": r"미래.*정보|예지|역사.*변경",
                        "reason": "회귀 시점 이후 - 미래 정보 없음",
                        "severity": "CRITICAL",
                    }
                )

        return actions

    def get_justification_patterns(self) -> list[str]:
        """[V57] 요리물 - 정당화로 인정되는 표현 패턴"""
        return [
            # 미래 정보 활용 (회귀물)
            r"미래.*기억",
            r"과거.*경험",
            r"전생.*정보",
            # 정당한 성장
            r"연습.*결과",
            r"멘토.*지도",
            r"스승.*가르침",
            r"대회.*입상",
            r"수련.*성과",
            # 식재료 확보
            r"산지.*직거래",
            r"계약.*재배",
            r"특수.*루트",
            r"직접.*재배",
            r"수입.*경로",
            # 재능/노력
            r"천부적.*미각",
            r"절대.*미각",
            r"타고난",
            r"밤새.*연구",
            r"수백.*번.*실험",
            # 합법적 기회
            r"공모전",
            r"요리.*대회",
            r"SNS.*입소문",
            r"방송.*출연",
            r"맛집.*소개",
        ]

    def get_hierarchy_rules(self) -> dict[str, Any]:
        """[V57] 요리물 - 셰프 등급/식당 위계 규칙"""
        return {
            "chef_ranks": self._chef_hierarchy,
            "restaurant_tiers": self._restaurant_hierarchy,
            "titles": {
                "수습생": ["수습생", "견습 요리사", "보조"],
                "준요리사": ["준요리사", "라인 쿡"],
                "요리사": ["요리사", "쿡"],
                "수석요리사": ["수석요리사", "수셰프", "부주방장"],
                "셰프": ["셰프", "주방장", "헤드셰프"],
                "명셰프": ["명셰프", "스타셰프", "유명 셰프"],
                "거장": ["거장", "마스터셰프", "그랜드셰프"],
                "전설의요리인": ["전설", "요리의 신", "레전드"],
            },
            "violations": {
                "수습생": [r"명셰프", r"거장", r"전설", r"미슐랭.*획득", r"전국.*대회.*우승"],
                "준요리사": [r"거장", r"전설", r"미슐랭", r"해외.*유명"],
                "요리사": [r"전설", r"미슐랭.*3스타", r"글로벌"],
            },
        }

    def get_technique_effect_rules(self) -> dict[str, dict[str, Any]]:
        """[V57] 요리물 - 요리 활동별 효능 규칙"""
        return {
            "신메뉴 개발": {
                "effect_type": "creation",
                "effect_scope": ["평판 상승", "매출 증가", "고객 유치"],
                "cannot_be_used_for": ["즉각적 미슐랭", "즉시 전설"],
                "risk": "실패 시 식재료 손실, 평판 하락",
            },
            "요리 대회 출전": {
                "effect_type": "competition",
                "effect_scope": ["명성 상승", "미디어 노출", "인맥 확대"],
                "cannot_be_used_for": ["직접적 매출", "식당 등급 상승"],
                "requirements": ["출전 자격", "대회 레시피", "준비 기간"],
            },
            "멘토 수련": {
                "effect_type": "training",
                "effect_scope": ["기법 습득", "셰프 등급 상승 기반", "요리 철학"],
                "cannot_be_used_for": ["즉각적 등급 상승", "매출"],
                "requirements": ["멘토 관계", "수련 기간"],
            },
            "식당 리뉴얼": {
                "effect_type": "business",
                "effect_scope": ["식당 등급 상승", "고객층 변화", "매출 변동"],
                "cannot_be_used_for": ["셰프 실력 향상"],
                "requirements": ["자금", "컨셉", "인력"],
            },
            "방송 출연": {
                "effect_type": "media",
                "effect_scope": ["대중 인지도", "고객 급증", "브랜드 가치"],
                "cannot_be_used_for": ["요리 실력 향상", "미슐랭 심사"],
                "requirements": ["일정 수준 명성", "방송 섭외"],
            },
        }

    # ========================================================================
    # [V57] 권위 위계 검증 (요리물 특화)
    # ========================================================================

    def get_authority_hierarchy(self) -> dict[str, Any]:
        """[V57] 요리물 - 주방/외식업계 권위 위계"""
        return {
            "positions": ["오너셰프", "총주방장", "주방장", "수셰프", "라인쿡", "수습생", "홀매니저"],
            "position_titles": {
                "오너셰프": ["오너", "대표", "사장", "원장"],
                "총주방장": ["총주방장", "총괄셰프", "그랜드셰프"],
                "주방장": ["주방장", "헤드셰프", "셰프"],
                "수셰프": ["수셰프", "부주방장", "서브셰프"],
                "라인쿡": ["라인쿡", "요리사", "조리사"],
                "수습생": ["수습", "견습", "인턴", "보조"],
                "홀매니저": ["홀매니저", "매니저", "지배인"],
            },
            "authority_scope": {
                "오너셰프": ["메뉴 결정", "인사", "투자", "브랜드"],
                "총주방장": ["레시피", "식재료", "주방 인사", "품질 관리"],
                "주방장": ["조리 지시", "메뉴 제안", "주방 운영"],
                "수셰프": ["라인 관리", "준비 감독", "재고"],
                "홀매니저": ["고객 응대", "예약", "서비스"],
            },
        }

    def get_delegation_patterns(self) -> list[str]:
        """[V57] 요리물 - 권위 위임 정당화 패턴"""
        return [
            r"오너.*지시",
            r"총주방장.*결정",
            r"주방장.*명령",
            r"긴급.*상황",
            r"대회.*규정",
            r"위생.*검사",
        ]

    # ========================================================================
    # [V57] 갈등 및 해소 검증
    # ========================================================================

    def get_hostile_action_types(self) -> list[str]:
        """[V57] 요리물 - 적대적 행동 유형"""
        return [
            "레시피 도용",
            "식재료 가로채기",
            "악의적 평가",
            "위생 신고",
            "영업 방해",
            "인력 빼가기",
            "라이벌 도발",
            "대회 부정행위",
            "허위 리뷰",
            "식중독 모함",
            "가격 덤핑",
            "공급처 차단",
        ]

    def get_resolution_patterns(self) -> list[str]:
        """[V57] 요리물 - 갈등 해소 패턴"""
        return [
            # 요리로 증명
            r"요리.*실력.*증명",
            r"맛으로.*승부",
            r"대회.*우승",
            r"고객.*인정",
            r"평론가.*극찬",
            # 합의/화해
            r"합의",
            r"화해",
            r"협상.*타결",
            r"협력",
            # 경영 승리
            r"매출.*역전",
            r"미슐랭.*획득",
            r"맛집.*선정",
            r"예약.*대기",
            r"줄.*서는.*맛집",
            # 독립/성장
            r"독립.*오픈",
            r"자기.*가게",
            r"독자.*노선",
            r"새로운.*메뉴",
            r"혁신.*요리",
        ]

    # ========================================================================
    # [V57] 요리 검증 헬퍼
    # ========================================================================

    def get_cooking_rules_prompt(self) -> str:
        """[V57] 요리 규칙 프롬프트 생성 (Writer/Architect 주입용)"""
        return """
[V57 요리물 메카닉스]

1. **셰프 등급별 행동 제약**
   - 수습생~준요리사: 보조 업무, 기초 요리, 동네 대회
   - 요리사~수석요리사: 독립 조리, 메뉴 제안, 지역 대회
   - 셰프~명셰프: 메뉴 총괄, 전국 대회, 미디어 출연
   - 거장 이상: 미슐랭 심사 대상, 국제 대회, 요리 철학 정립

2. **식당 등급 현실성**
   - 포장마차/동네식당: 월매출 500만~3000만, 1인~3인 운영
   - 맛집: 월매출 3000만~1억, 안정적 단골, SNS 인지도
   - 파인다이닝: 월매출 1억~5억, 코스 요리, 소믈리에
   - 미슐랭: 일관된 품질, 혁신성, 완벽한 서비스

3. **식재료 수급 현실성**
   - 계절 식재료 존중 (겨울에 생딸기 대량 사용 금지)
   - 수입 식재료는 공급 경로 명시
   - 희귀 재료는 획득 과정 서술

4. **회귀물 특수 규칙**
   - 미래의 트렌드/레시피 정보 활용 가능
   - 나비 효과로 식재료 시장 변동 가능
   - 미래 레시피 사용 시 재현 과정 필수 (재료/기법 차이)

5. **경영 제약**
   - 원가율: 식재료비 30~35% 기준
   - 인건비: 매출의 25~30%
   - 임대료와 고정비 고려
   - 흑자 전환까지 최소 6개월~1년
"""

    # ========================================================================
    # [V66] 심층 검증 오버라이드
    # ========================================================================

    def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]:
        """[V66] 요리물 심층 검증."""
        result = super().run_deep_validation(manuscript, current_state or {})

        # [V70] get_impossible_actions 중복 제거 (super()가 이미 check_state_action_consistency에서 호출)

        result["has_critical"] = any(v.get("severity") in ("HIGH", "CRITICAL") for v in result["violations"])
        if result["violations"]:
            result["summary"] = "; ".join(v.get("message", "") for v in result["violations"][:5])
            result["feedback"] = f"[요리물 Guard] {len(result['violations'])}건: {result['summary']}"
        return result
