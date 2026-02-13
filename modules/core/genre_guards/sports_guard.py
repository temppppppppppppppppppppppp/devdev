"""
[V62.1] 스포츠물 전용 Guard
[V57] 완전 구현 - 일관성 검증, 권위 위계, 타임라인 검증
스포츠 산업의 전문성과 개연성을 유지
"""

from typing import Any

from .base_guard import BaseGuard


class SportsGuard(BaseGuard):
    """[스포츠물] 선수 성장 + 팀 스포츠 전문성 보호자 + V57 완전 구현"""

    def __init__(self) -> None:
        super().__init__()
        cfg = self._load_genre_yaml("sports")

        self.FORBIDDEN_TERMS = cfg.get(
            "forbidden_terms",
            [
                "내공",
                "진기",
                "마나",
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
                "기공",
                "경맥",
                "혈도",
                "단전",
                "비급",
            ],
        )

        self.SPORTS_TERMS = cfg.get(
            "sports_terms",
            [
                "드리블",
                "패스",
                "슛",
                "태클",
                "세트피스",
                "코너킥",
                "쿼터",
                "하프타임",
                "연장전",
                "승부차기",
                "PK",
                "심판",
                "파울",
                "옐로카드",
                "레드카드",
                "VAR",
                "트레이닝",
                "피지컬",
                "컨디셔닝",
                "웨이트",
                "인터벌",
                "리그",
                "토너먼트",
                "플레이오프",
                "챔피언십",
                "월드컵",
                "에이전트",
                "스카우트",
                "드래프트",
                "이적료",
                "연봉",
                "스폰서",
                "브랜드",
                "광고",
                "미디어데이",
                "기자회견",
                "MVP",
                "득점왕",
                "어시스트",
                "클린시트",
                "트리플더블",
                "유소년",
                "아카데미",
                "2군",
                "임대",
                "FA",
                "감독",
                "코치",
                "트레이너",
                "피지오",
                "닥터",
            ],
        )

        self.MANDATORY_CONCEPTS = cfg.get(
            "mandatory_concepts",
            [
                "경기 장면의 역동적 묘사",
                "신체 한계와 성장의 개연성",
                "팀 역학과 라이벌 관계",
                "스포츠 산업의 현실적 반영",
            ],
        )

        self._athlete_hierarchy = cfg.get(
            "athlete_hierarchy",
            [
                "동호회",
                "아마추어",
                "세미프로",
                "프로신인",
                "프로정규",
                "올스타",
                "국가대표",
                "전설",
            ],
        )

        self._athlete_action_limits = cfg.get(
            "athlete_action_limits",
            {
                "동호회": [r"프로.*대회.*출전", r"국가대표", r"올림픽", r"프로.*계약", r"스폰서.*계약"],
                "아마추어": [r"프로.*정규시즌", r"국가대표.*선발", r"해외.*빅리그", r"대형.*스폰서"],
                "세미프로": [r"올림픽.*금메달", r"월드컵.*본선", r"빅리그.*스타"],
                "프로신인": [r"전설.*반열", r"올스타.*MVP", r"은퇴.*번호"],
                "프로정규": [r"전설.*반열"],
            },
        )

        self._status_action_limits = cfg.get(
            "status_action_limits",
            {
                "부상": [r"전력.*경기", r"풀타임.*출전", r"무리한.*훈련", r"스프린트"],
                "슬럼프": [r"완벽한.*경기", r"신기록", r"MVP.*수상"],
                "자격정지": [r"공식.*경기", r"리그.*출전", r"대표팀"],
                "은퇴": [r"현역.*복귀", r"경기.*출전", r"리그.*등록"],
                "도핑적발": [r"공식.*경기", r"대표.*선발", r"스폰서"],
            },
        )

        self._competition_requirements = {
            "동네 대회": {"athlete_tier": "동호회"},
            "아마추어 리그": {"athlete_tier": "아마추어"},
            "프로 리그": {"athlete_tier": "프로신인"},
            "전국 대회": {"athlete_tier": "프로정규"},
            "국제 대회": {"athlete_tier": "올스타"},
            "올림픽/월드컵": {"athlete_tier": "국가대표"},
        }

    def get_genre_name(self) -> str:
        return "스포츠물(SPORTS)"

    def _should_check_english(self) -> bool:
        """스포츠물은 현대 배경이므로 영어 완화"""
        return False

    def _should_check_numbers(self) -> bool:
        """스포츠물은 기록/스탯 등 정확한 수치가 중요"""
        return False

    def get_v20_purism_prompt(self) -> str:
        """스포츠물 장르 전문성 지침"""
        return f"""
[🏆 V62.1 스포츠물 장르 가이드라인 (Sports Genre Professionalism)]

1. **장르 교란 금지**: 판타지/무협 용어({", ".join(self.FORBIDDEN_TERMS[:8])} 등)를 사용하지 마라. 현실적인 스포츠 세계관을 유지하라.
2. **스포츠 상식 준수**: 모든 경기와 훈련은 해당 종목의 규칙과 현실에 부합해야 한다. 비현실적 신체 능력이나 불가능한 기록은 금지한다.
3. **전문 용어의 정확성**: {", ".join(self.SPORTS_TERMS[:10])} 등의 스포츠 용어를 정확하게 사용하라.
4. **성장의 개연성**: 주인공의 실력 향상은 반드시 구체적인 훈련과 경험에 기반해야 한다.
5. **경기 묘사**: 속도감 있는 실시간 묘사, 신체 감각(근육/호흡/땀), 관중 분위기, 전술적 해석을 입체적으로 그려라.
6. **팀 역학**: 팀원 간 갈등과 유대, 감독과의 관계, 라이벌과의 긴장을 사실적으로 묘사하라.
7. **스포츠 산업**: 이적, 연봉 협상, 스폰서, 미디어, 팬덤 등 산업적 측면을 현실적으로 다뤄라.
8. **시대적 배경**: SNS, 유튜브, OTT 중계, 데이터 분석 등 현대 스포츠 트렌드를 자연스럽게 활용하라.
9. **필수 표현 요소**: {", ".join(self.MANDATORY_CONCEPTS)}

[개연성 체크리스트]
- 경기력이 주인공의 선수 등급에 부합하는가?
- 훈련량과 기간이 실력 향상에 현실적인가?
- 부상과 재활 기간이 의학적으로 타당한가?
- 팀 내 포지션과 역할이 일관성 있게 묘사되는가?
"""

    # ========================================================================
    # [V57] 일관성 검증 구현 (스포츠물 특화)
    # ========================================================================

    def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]:
        """[V57] 스포츠물 - 현재 상태에서 불가능한 행동 패턴 반환"""
        actions = []

        # 1. 상태 기반 제한 (부상, 슬럼프 등)
        status = current_state.get("status", current_state.get("condition", ""))
        if isinstance(status, str):
            for status_keyword, patterns in self._status_action_limits.items():
                if status_keyword in status:
                    for pattern in patterns:
                        actions.append(
                            {"pattern": pattern, "reason": f"상태 '{status_keyword}'로 인해 불가", "severity": "HIGH"}
                        )

        # 2. 선수 등급 기반 제한
        tier = current_state.get("athlete_tier", current_state.get("tier", "아마추어"))
        tier_class = self._get_athlete_class(tier)
        if tier_class and tier_class in self._athlete_action_limits:
            for pattern in self._athlete_action_limits[tier_class]:
                actions.append({"pattern": pattern, "reason": f"선수 등급 '{tier_class}'에서 불가", "severity": "HIGH"})

        # 3. 부상 상태 상세
        injury = current_state.get("injuries", current_state.get("injury_history", ""))
        if isinstance(injury, str) and any(kw in injury for kw in ["중상", "수술", "인대", "골절"]):
            actions.append(
                {
                    "pattern": r"경기.*출전|풀타임|스프린트|점프|슬라이딩",
                    "reason": "심각한 부상 상태 - 경기 출전 불가",
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
                        "pattern": r"미래.*정보|예지|경기.*결과.*예측",
                        "reason": "회귀 시점 이후 - 미래 정보 없음",
                        "severity": "CRITICAL",
                    }
                )

        return actions

    def _get_athlete_class(self, tier) -> str:
        """선수 등급에 따른 클래스 반환"""
        if isinstance(tier, str):
            for cls_name in self._athlete_hierarchy:
                if cls_name in tier:
                    return cls_name
            return "아마추어"
        return "아마추어"

    def get_justification_patterns(self) -> list[str]:
        """[V57] 스포츠물 - 정당화로 인정되는 표현 패턴"""
        return [
            r"미래.*기억",
            r"과거.*경험",
            r"전생.*정보",
            r"체계적.*훈련",
            r"특별.*트레이닝",
            r"코치.*지도",
            r"실전.*경험",
            r"경기.*경험",
            r"대회.*출전",
            r"멘토.*가르침",
            r"선배.*조언",
            r"감독.*신뢰",
            r"천부적.*재능",
            r"타고난.*신체",
            r"운동.*신경",
            r"피나는.*노력",
            r"새벽.*훈련",
            r"독자.*연습",
            r"부상.*재활",
            r"재활.*성공",
            r"컴백.*준비",
            r"미디어.*노출",
            r"팬.*지지",
            r"스폰서.*제안",
            r"스카우트.*발탁",
            r"공개.*테스트",
            r"트라이아웃",
        ]

    def get_hierarchy_rules(self) -> dict[str, Any]:
        """[V57] 스포츠물 - 선수 등급/위계 규칙"""
        return {
            "athlete_tiers": self._athlete_hierarchy,
            "titles": {
                "동호회": ["동호회 선수", "취미 선수"],
                "아마추어": ["아마추어", "학생 선수", "대학 선수"],
                "세미프로": ["세미프로", "실업팀"],
                "프로신인": ["루키", "신인", "프로 신인"],
                "프로정규": ["프로 선수", "정규 로스터"],
                "올스타": ["올스타", "에이스", "간판 선수"],
                "국가대표": ["국가대표", "대표팀"],
                "전설": ["전설", "레전드", "명예의전당"],
            },
            "violations": {
                "동호회": [r"프로.*계약", r"국가대표", r"올림픽", r"월드컵"],
                "아마추어": [r"프로.*정규시즌", r"빅리그", r"국가대표"],
                "세미프로": [r"올림픽.*금메달", r"월드컵.*본선"],
                "프로신인": [r"전설.*반열", r"올스타.*MVP"],
            },
        }

    def get_technique_effect_rules(self) -> dict[str, dict[str, Any]]:
        """[V57] 스포츠물 - 활동별 효능 규칙"""
        return {
            "체계적 훈련": {
                "effect_type": "training",
                "effect_scope": ["신체 능력 향상", "기술 숙련", "전술 이해"],
                "cannot_be_used_for": ["즉각적 스타", "기록 경신"],
                "requirements": ["트레이너", "훈련 기간", "시설"],
            },
            "실전 경기": {
                "effect_type": "match",
                "effect_scope": ["경험치 축적", "명성 상승", "기록 축적"],
                "cannot_be_used_for": ["신체 능력 급등"],
                "risk": "부상 위험, 패배 시 자신감 하락",
            },
            "멘토 지도": {
                "effect_type": "mentoring",
                "effect_scope": ["기술 교정", "멘탈 강화", "전술 이해"],
                "cannot_be_used_for": ["신체 능력 향상", "즉각적 기록"],
                "requirements": ["멘토 관계", "신뢰"],
            },
            "부상 재활": {
                "effect_type": "recovery",
                "effect_scope": ["컨디션 회복", "복귀 준비", "멘탈 강화"],
                "cannot_be_used_for": ["실력 향상", "경기 출전"],
                "requirements": ["의료진", "재활 기간", "인내"],
            },
            "미디어 노출": {
                "effect_type": "media",
                "effect_scope": ["인지도 상승", "스폰서", "팬덤"],
                "cannot_be_used_for": ["실력 향상", "경기력"],
                "risk": "스캔들 노출 가능성",
            },
        }

    # ========================================================================
    # [V57] 권위 위계 검증 (스포츠물 특화)
    # ========================================================================

    def get_authority_hierarchy(self) -> dict[str, Any]:
        """[V57] 스포츠물 - 스포츠 조직 권위 위계"""
        return {
            "positions": ["구단주", "단장", "감독", "수석코치", "코치", "주장", "주전", "후보", "유스"],
            "position_titles": {
                "구단주": ["구단주", "회장", "오너"],
                "단장": ["단장", "GM", "사무국장"],
                "감독": ["감독", "사령탑", "헤드코치"],
                "수석코치": ["수석코치", "제1코치"],
                "코치": ["코치", "트레이너", "피지컬코치"],
                "주장": ["주장", "캡틴", "리더"],
                "주전": ["주전", "스타터", "선발"],
                "후보": ["후보", "백업", "벤치"],
                "유스": ["유소년", "유스", "아카데미"],
            },
            "authority_scope": {
                "구단주": ["투자", "이적", "감독 인사", "전략"],
                "단장": ["선수 영입", "계약", "트레이드", "로스터"],
                "감독": ["전술", "선발 라인업", "교체", "훈련 계획"],
                "수석코치": ["훈련 진행", "전술 보조", "선수 관리"],
                "주장": ["팀 사기", "현장 소통", "후배 지도"],
            },
        }

    def get_delegation_patterns(self) -> list[str]:
        """[V57] 스포츠물 - 권위 위임 정당화 패턴"""
        return [
            r"감독.*지시",
            r"코치.*판단",
            r"구단.*결정",
            r"트레이너.*처방",
            r"의료진.*소견",
            r"대회.*규정",
            r"리그.*규칙",
            r"긴급.*상황",
            r"부상.*때문",
        ]

    # ========================================================================
    # [V57] 갈등 및 해소 검증
    # ========================================================================

    def get_hostile_action_types(self) -> list[str]:
        """[V57] 스포츠물 - 적대적 행동 유형"""
        return [
            "악성 파울",
            "라커룸 갈등",
            "포지션 경쟁",
            "감독 갈등",
            "트레이드 통보",
            "방출",
            "부상 유발",
            "도핑 모함",
            "승부조작 의혹",
            "미디어 악플",
            "스폰서 압박",
            "팬덤 갈등",
            "연봉 분쟁",
            "계약 위반",
            "불공정 판정",
        ]

    def get_resolution_patterns(self) -> list[str]:
        """[V57] 스포츠물 - 갈등 해소 패턴"""
        return [
            r"경기.*증명",
            r"기록.*갱신",
            r"MVP.*수상",
            r"팀.*단합",
            r"동료.*화해",
            r"감독.*인정",
            r"재계약",
            r"이적.*성공",
            r"복귀전.*활약",
            r"우승",
            r"승격",
            r"챔피언",
            r"재활.*성공",
            r"컴백.*성공",
            r"팬.*지지",
            r"여론.*반전",
            r"결백.*증명",
            r"징계.*해제",
        ]

    # ========================================================================
    # [V66] 심층 검증 오버라이드
    # ========================================================================

    def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]:
        """[V66] 스포츠물 심층 검증."""
        result = super().run_deep_validation(manuscript, current_state or {})

        # [V70] get_impossible_actions 중복 제거 (super()가 이미 check_state_action_consistency에서 호출)

        result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violations"])
        if result["violations"]:
            result["summary"] = "; ".join(v.get("message", "") for v in result["violations"][:5])
            result["feedback"] = f"[스포츠물 Guard] {len(result['violations'])}건: {result['summary']}"
        return result
