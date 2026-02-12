"""
[V62] 배우물 전용 Guard
[V57] 완전 구현 - 일관성 검증, 권위 위계, 타임라인 검증
연예계의 전문성과 개연성을 유지
"""

from typing import List, Dict, Any, Tuple
from .base_guard import BaseGuard


class ActorGuard(BaseGuard):
    """[배우물] 연예계 전문성 보호자 + V57 완전 구현"""

    def __init__(self) -> None:
        super().__init__()

        # 배우물에서 금지되는 용어 (무협/판타지/헌터 용어)
        self.FORBIDDEN_TERMS = [
            "내공", "진기", "마나", "스킬", "던전", "게이트", "각성", "헌터",
            "검기", "검강", "초식", "보법", "무림", "강호", "문파", "장로",
            "마법", "주문", "포션", "엘프", "드워프", "드래곤", "오크",
            "레벨업", "경험치", "스테이터스", "인벤토리", "버프", "디버프",
            "상태창", "시스템 창", "퀘스트", "레이드",
            "기공", "경맥", "혈도", "단전", "비급",
        ]

        # 연예계 전문 용어 (정확하게 사용해야 함)
        self.ENTERTAINMENT_TERMS = [
            "오디션", "캐스팅", "콜백", "리딩", "대본 리딩", "촬영",
            "크랭크인", "크랭크업", "올로케", "세트 촬영", "후반작업",
            "시청률", "VOD", "OTT", "스트리밍", "극장 개봉",
            "흥행", "손익분기점", "관객수", "박스오피스",
            "에이전시", "매니지먼트", "전속계약", "출연료", "개런티",
            "시나리오", "콘티", "연출", "감독", "PD", "작가",
            "팬미팅", "팬사인회", "레드카펫", "시사회", "기자회견",
            "연기상", "대상", "신인상", "최우수상", "골든글로브",
            "영화제", "칸", "베니스", "베를린", "부산국제영화제",
            "CF", "광고", "화보", "매거진", "인터뷰",
            "예능", "토크쇼", "버라이어티", "리얼리티",
        ]

        # 배우물 필수 개념
        self.MANDATORY_CONCEPTS = [
            "연기 활동 과정의 구체적 묘사",
            "연예계 생태계의 사실적 반영",
            "계약과 출연료의 현실성",
            "시청률/흥행과 대중 반응의 개연성",
        ]

        # [V57] 인지도 등급
        self._fame_hierarchy = [
            '무명', '엑스트라', '단역', '조연', '주연', '톱스타', '한류스타', '레전드',
        ]

        # [V57] 인지도 등급별 행동 불가 패턴
        self._fame_action_limits = {
            '무명': [r'주연.*캐스팅', r'대형.*CF', r'해외.*진출', r'시상식.*수상', r'팬미팅'],
            '엑스트라': [r'주연.*캐스팅', r'대형.*CF', r'해외.*영화제', r'단독.*팬미팅'],
            '단역': [r'대작.*주연', r'해외.*진출', r'글로벌.*계약'],
            '조연': [r'글로벌.*스타', r'할리우드.*주연'],
            '주연': [r'레전드.*반열'],
        }

        # [V57] 상태별 불가능 행동
        self._status_action_limits = {
            '스캔들': [r'광고.*촬영', r'신규.*캐스팅', r'팬미팅', r'예능.*출연'],
            '부상': [r'액션.*촬영', r'스턴트', r'장시간.*촬영'],
            '계약분쟁': [r'신규.*작품', r'CF.*계약', r'타사.*이적'],
            '은퇴': [r'컴백', r'신작.*촬영', r'활동.*재개'],
            '군입대': [r'촬영', r'출연', r'활동', r'팬미팅'],
            '논란': [r'광고.*모델', r'공식.*행사', r'신규.*캐스팅'],
        }

        # [V57] 활동별 최소 요건
        self._activity_requirements = {
            '단역 출연': {'fame': '엑스트라'},
            '조연 출연': {'fame': '단역'},
            '주연 출연': {'fame': '조연'},
            'CF 촬영': {'fame': '조연'},
            '팬미팅': {'fame': '주연'},
            '해외 영화제': {'fame': '주연'},
            '할리우드 진출': {'fame': '톱스타'},
        }

    def get_genre_name(self) -> str:
        return "배우물(ACTOR)"

    def _should_check_english(self) -> bool:
        """배우물은 현대 배경이므로 영어 완화"""
        return False

    def _should_check_numbers(self) -> bool:
        """배우물은 시청률/관객수 등 정확한 수치가 중요"""
        return False

    def get_v20_purism_prompt(self) -> str:
        """배우물 장르 전문성 지침"""
        return f"""
[🎬 V62 배우물 장르 가이드라인 (Actor Genre Professionalism)]

1. **장르 교란 금지**: 판타지/무협 용어({', '.join(self.FORBIDDEN_TERMS[:8])} 등)를 사용하지 마라. 현실적인 연예계 세계관을 유지하라.
2. **연예계 상식 준수**: 모든 활동은 업계 관행과 현실에 부합해야 한다. 근거 없는 대박이나 비현실적 캐스팅은 금지한다.
3. **전문 용어의 정확성**: {', '.join(self.ENTERTAINMENT_TERMS[:10])} 등의 연예계 용어를 정확하게 사용하라.
4. **성장의 개연성**: 주인공의 인지도 상승은 반드시 구체적인 작품 활동과 대중 반응에 기반해야 한다.
5. **연기 과정의 묘사**: 오디션, 대본 분석, 캐릭터 구축, 촬영 과정을 구체적으로 묘사하라. 배우의 내면 성장이 핵심이다.
6. **업계 생태계**: 소속사, 감독, PD, 작가, 매니저, 기자 등 다양한 이해관계자들의 역학 관계를 입체적으로 그려라.
7. **법률과 계약**: 전속계약, 출연료, 저작인접권, 초상권 등의 법적 관계를 사실적으로 다뤄라.
8. **시대적 배경**: OTT, SNS, K-드라마 글로벌화 등 현대 연예 산업의 트렌드를 자연스럽게 활용하라.
9. **필수 표현 요소**: {', '.join(self.MANDATORY_CONCEPTS)}

[개연성 체크리스트]
- 시청률/관객수가 주인공의 인지도 수준에 부합하는가?
- 캐스팅에 필요한 인지도/경력이 갖춰져 있는가?
- 주인공의 연기력 성장에 구체적 근거(연습, 멘토, 경험)가 있는가?
- 업계 반응(평론, 시청률, 팬덤)이 일관성 있게 묘사되는가?
"""

    # ========================================================================
    # [V57] 일관성 검증 구현 (배우물 특화)
    # ========================================================================

    def get_impossible_actions(self, current_state: Dict[str, Any]) -> List[Dict[str, str]]:
        """[V57] 배우물 - 현재 상태에서 불가능한 행동 패턴 반환"""
        actions = []

        # 1. 상태 기반 제한 (스캔들, 계약분쟁 등)
        status = current_state.get('status', current_state.get('scandal_index', ''))
        if isinstance(status, str):
            for status_keyword, patterns in self._status_action_limits.items():
                if status_keyword in status:
                    for pattern in patterns:
                        actions.append({
                            'pattern': pattern,
                            'reason': f"상태 '{status_keyword}'로 인해 불가",
                            'severity': 'HIGH'
                        })

        # 2. 인지도 등급 기반 제한
        fame = current_state.get('fame', current_state.get('recognition', '무명'))
        fame_class = self._get_fame_class(fame)
        if fame_class and fame_class in self._fame_action_limits:
            for pattern in self._fame_action_limits[fame_class]:
                actions.append({
                    'pattern': pattern,
                    'reason': f"인지도 '{fame_class}'에서 불가",
                    'severity': 'HIGH'
                })

        # 3. 스캔들 지수 높은 경우
        scandal_idx = current_state.get('scandal_index', 0)
        if isinstance(scandal_idx, (int, float)) and scandal_idx >= 80:
            actions.append({
                'pattern': r'광고.*계약|CF|브랜드.*모델|공식.*행사',
                'reason': f'스캔들 지수 {scandal_idx} - 광고/공식행사 불가',
                'severity': 'CRITICAL'
            })

        # 4. 회귀자 미래 정보 제한 (특수)
        is_regressor = current_state.get('is_regressor', False)
        regression_year = current_state.get('regression_year', None)
        current_year = current_state.get('current_year', None)

        if is_regressor and regression_year and current_year:
            if current_year >= regression_year:
                actions.append({
                    'pattern': r'미래.*정보|예지|역사.*변경',
                    'reason': '회귀 시점 이후 - 미래 정보 없음',
                    'severity': 'CRITICAL'
                })

        return actions

    def _get_fame_class(self, fame) -> str:
        """인지도 수준에 따른 등급 반환"""
        if isinstance(fame, str):
            for cls_name in self._fame_hierarchy:
                if cls_name in fame:
                    return cls_name
            return '무명'
        return '무명'

    def get_justification_patterns(self) -> List[str]:
        """[V57] 배우물 - 정당화로 인정되는 표현 패턴"""
        return [
            r'미래.*기억', r'과거.*경험', r'전생.*정보',
            r'오디션.*통과', r'캐스팅.*확정', r'감독.*인정',
            r'연습.*결과', r'멘토.*지도', r'실력.*향상',
            r'인맥.*통해', r'소개.*받', r'추천.*덕분',
            r'천부적.*재능', r'타고난.*감각',
            r'밤새.*연습', r'피나는.*노력', r'대본.*분석',
            r'공개.*오디션', r'SNS.*입소문', r'바이럴',
            r'시청률.*상승', r'관객수.*증가',
        ]

    def get_hierarchy_rules(self) -> Dict[str, Any]:
        """[V57] 배우물 - 인지도/지위 위계 규칙"""
        return {
            'fame_classes': self._fame_hierarchy,
            'titles': {
                '무명': ['무명 배우', '연기 지망생', '보조출연'],
                '엑스트라': ['엑스트라', '보조출연자'],
                '단역': ['단역 배우', '신인 배우'],
                '조연': ['조연급', '떠오르는 배우'],
                '주연': ['주연급', '인기 배우'],
                '톱스타': ['톱스타', '대세 배우'],
                '한류스타': ['한류스타', '글로벌 배우'],
                '레전드': ['레전드', '국민 배우'],
            },
            'violations': {
                '무명': [r'톱스타', r'레전드', r'해외.*진출', r'시상식.*수상'],
                '엑스트라': [r'톱스타', r'한류스타', r'주연.*캐스팅'],
                '단역': [r'레전드', r'글로벌.*스타', r'할리우드'],
                '조연': [r'레전드', r'할리우드.*주연'],
            }
        }

    def get_technique_effect_rules(self) -> Dict[str, Dict[str, Any]]:
        """[V57] 배우물 - 활동별 효능 규칙"""
        return {
            '드라마 출연': {
                'effect_type': 'drama',
                'effect_scope': ['인지도 상승', '팬덤 확보', '연기력 인정'],
                'cannot_be_used_for': ['즉각적 레전드', '해외 인지도'],
                'risk': '시청률 부진 시 이미지 타격',
            },
            '영화 출연': {
                'effect_type': 'film',
                'effect_scope': ['연기력 인정', '영화제 후보', '배우 위상'],
                'cannot_be_used_for': ['대중 인지도 급등'],
                'requirements': ['캐스팅 확정', '촬영 기간', '개봉'],
            },
            'CF 촬영': {
                'effect_type': 'commercial',
                'effect_scope': ['수입', '대중 인지도', '이미지'],
                'cannot_be_used_for': ['연기력 인정', '배우 위상'],
                'requirements': ['깨끗한 이미지', '일정 인지도'],
            },
            '영화제 참석': {
                'effect_type': 'festival',
                'effect_scope': ['글로벌 인지도', '배우 위상', '해외 제안'],
                'cannot_be_used_for': ['국내 팬덤'],
                'requirements': ['출품작', '초청'],
            },
            '예능 출연': {
                'effect_type': 'variety',
                'effect_scope': ['친근한 이미지', '팬덤', '인지도'],
                'cannot_be_used_for': ['연기력 인정', '배우 위상 향상'],
                'risk': '과다 예능 시 배우 이미지 희석',
            },
        }

    # ========================================================================
    # [V57] 권위 위계 검증 (배우물 특화)
    # ========================================================================

    def get_authority_hierarchy(self) -> Dict[str, Any]:
        """[V57] 배우물 - 연예계 권위 위계"""
        return {
            'positions': ['대표', '이사', '본부장', '팀장', '매니저', '로드매니저', '스태프'],
            'position_titles': {
                '대표': ['대표', '회장', '사장', 'CEO'],
                '이사': ['이사', '상무', '전무'],
                '본부장': ['본부장', '실장', '센터장'],
                '팀장': ['팀장', '캐스팅 디렉터'],
                '매니저': ['매니저', '담당 매니저', '수석 매니저'],
                '로드매니저': ['로드매니저', '현장 매니저'],
                '스태프': ['스태프', '코디', '스타일리스트'],
            },
            'authority_scope': {
                '대표': ['계약', '전략', '인사', '투자'],
                '이사': ['기획', '마케팅', '캐스팅 최종'],
                '본부장': ['스케줄 총괄', '작품 선정'],
                '팀장': ['캐스팅 진행', '미팅 설정'],
                '매니저': ['스케줄 관리', '현장 동행'],
            }
        }

    def get_delegation_patterns(self) -> List[str]:
        """[V57] 배우물 - 권위 위임 정당화 패턴"""
        return [
            r'대표.*지시', r'소속사.*방침', r'매니저.*결정',
            r'감독.*요청', r'PD.*제안', r'작가.*의도',
            r'계약.*조건', r'긴급.*상황',
        ]

    # ========================================================================
    # [V57] 갈등 및 해소 검증
    # ========================================================================

    def get_hostile_action_types(self) -> List[str]:
        """[V57] 배우물 - 적대적 행동 유형"""
        return [
            '악성 루머', '파파라치', '스캔들 유포',
            '캐스팅 방해', '소속사 횡포', '노예계약',
            '팬덤 전쟁', '악플 테러', '조작 기사',
            '표절 논란', '연기력 논란', '태도 논란',
            '불공정 계약', '정산 분쟁',
        ]

    def get_resolution_patterns(self) -> List[str]:
        """[V57] 배우물 - 갈등 해소 패턴"""
        return [
            r'합의', r'화해', r'사과', r'해명',
            r'시청률.*증명', r'흥행.*성공', r'수상',
            r'실력.*인정', r'여론.*반전', r'팬.*지지',
            r'소송.*승소', r'계약.*해지', r'독립',
            r'재계약', r'이적.*성공', r'컴백.*성공',
        ]

    # ========================================================================
    # [V66] 심층 검증 오버라이드
    # ========================================================================

    def run_deep_validation(self, manuscript: str, current_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """[V66] 배우물 심층 검증."""
        result = super().run_deep_validation(manuscript, current_state or {})

        # [V70] get_impossible_actions 중복 제거 (super()가 이미 check_state_action_consistency에서 호출)

        result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violations"])
        if result["violations"]:
            result["summary"] = "; ".join(v.get("message", "") for v in result["violations"][:5])
            result["feedback"] = f"[배우물 Guard] {len(result['violations'])}건: {result['summary']}"
        return result
