"""
[V40 Multi-Genre] 헌터물 전용 Guard
[V46] 일관성 검증 규칙 추가 - 상태 vs 행동, 정당화 패턴, 등급 위계
[V46.1] 권위 위임, 미해결 갈등(고구마), 빌런 반응 검증 추가
헌터물 장르의 일관성을 유지하고 무협 용어를 차단
"""

from typing import List, Dict, Any
from .base_guard import BaseGuard


class HunterGuard(BaseGuard):
    """[헌터물] 장르 일관성 보호자 + V46 일관성 검증"""

    def __init__(self):
        super().__init__()

        # 헌터물에서 금지되는 용어 (주로 무협 용어)
        self.FORBIDDEN_TERMS = [
            "내공", "진기", "단전", "임독이맥", "주화입마", "기감", "초식", "보법",
            "검기", "검강", "강기", "기공", "경지", "일류", "절정", "화경", "현경",
            "무림", "강호", "문파", "장로", "대협", "소협", "본좌", "포권례",
            "은원", "항렬", "사숙", "사조", "장경각", "비급", "심법", "전음입밀",
            "영약", "영물", "내단", "환골탈태", "기맥", "혈도", "점혈", "투경"
        ]

        # 헌터물에서 필수적으로 허용되는 용어
        self.ALLOWED_TERMS = [
            "스킬", "마나", "던전", "게이트", "레이드", "길드", "각성", "랭크",
            "헌터", "시스템", "스테이터스", "레벨", "경험치", "스탯", "포인트",
            "아이템", "인벤토리", "퀘스트", "포션", "버프", "디버프", "쿨타임",
            "HP", "MP", "공격력", "방어력", "민첩", "지능", "체력"
        ]

        # 헌터물 필수 개념
        self.MANDATORY_CONCEPTS = [
            "던전과 게이트의 명확한 구분",
            "각성 능력의 체계적 표현",
            "길드 시스템과 사회적 관계",
            "성장과 랭크업의 쾌감"
        ]

        # [V46] 헌터 등급 위계 (낮음 → 높음)
        self._rank_hierarchy = ['E', 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS', '국가급', '세계급']

        # [V46] 등급별 사용 불가 스킬/능력 패턴
        self._rank_skill_limits = {
            'E': ['S급 스킬', 'A급 스킬', '영역 전개', '차원', '시공간', '불멸', '신화급'],
            'D': ['S급 스킬', 'A급 스킬', '영역 전개', '차원', '불멸', '신화급'],
            'C': ['S급 스킬', '영역 전개', '차원', '불멸', '신화급'],
            'B': ['S급 스킬', '차원', '불멸', '신화급'],
            'A': ['차원 절단', '불멸', '신화급'],
            'S': ['신화급', '세계급 스킬'],
        }

        # [V46] 상태별 불가능 행동
        self._status_action_limits = {
            '마나 고갈': [r'스킬.*발동', r'마나.*사용', r'능력.*발휘', r'마법.*시전'],
            '중상': [r'전력.*질주', r'고속.*이동', r'연속.*공격', r'회피.*기동'],
            '기절': [r'눈.*떠', r'공격', r'방어', r'이동'],
            'HP 위험': [r'무리.*공격', r'전력.*질주', r'자폭'],
        }

    def get_genre_name(self):
        return "헌터물(HUNTER)"

    def _should_check_english(self):
        """헌터물은 현대 배경이므로 영어 완화"""
        return False

    def _should_check_numbers(self):
        """헌터물은 수치 표현이 중요하므로 아라비아 숫자 허용"""
        return False

    def get_v20_purism_prompt(self):
        """헌터물 장르 일관성 지침"""
        return f"""
[🎮 V40 헌터물 장르 가이드라인 (Hunter Genre Consistency)]

1. **장르 교란 금지**: 무협 용어({', '.join(self.FORBIDDEN_TERMS[:8])} 등)를 사용하지 마라. 헌터물의 세계관을 유지하라.
2. **시스템 요소의 일관성**: 스킬, 마나, 던전, 길드 등의 시스템 요소는 작품 전체에서 일관된 규칙으로 작동해야 한다.
3. **현대적 배경 활용**: 스마트폰, 인터넷, SNS 등 현대 문물을 자연스럽게 활용하라.
4. **각성 능력의 체계성**: 주인공의 각성 능력은 명확한 원리와 제약이 있어야 하며, 갑작스러운 파워업은 반드시 합리적 근거가 있어야 한다.
5. **전투 묘사**: 스킬 발동 시의 시각적 효과, 마나 소모, 쿨타임 등을 구체적으로 묘사하라.
6. **사회적 배경**: 길드, 협회, 정부 기관 등 헌터 사회의 구조를 현실감 있게 그려라.
7. **금융/경제 요소**: 던전 보상, 아이템 거래, 헌터의 수입 등 경제적 측면도 설득력 있게 표현하라.
8. **필수 표현 요소**: {', '.join(self.MANDATORY_CONCEPTS)}
"""

    # ========================================================================
    # [V46] 일관성 검증 구현 (헌터물 특화)
    # ========================================================================

    def get_impossible_actions(self, current_state: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        [V46] 헌터물 - 현재 상태에서 불가능한 행동 패턴 반환

        동적 규칙 생성: HUD의 rank, mana, status에서 추론
        """
        actions = []

        # 1. 상태 기반 제한 (마나 고갈, 중상 등)
        status = current_state.get('status', '')
        if isinstance(status, str):
            for status_keyword, patterns in self._status_action_limits.items():
                if status_keyword in status:
                    for pattern in patterns:
                        actions.append({
                            'pattern': pattern,
                            'reason': f"상태 '{status_keyword}'로 인해 불가",
                            'severity': 'HIGH'
                        })

        # 2. 등급 기반 스킬 제한
        rank = current_state.get('rank', current_state.get('realm', ''))
        if rank and rank.upper() in self._rank_skill_limits:
            forbidden_skills = self._rank_skill_limits[rank.upper()]
            for skill in forbidden_skills:
                actions.append({
                    'pattern': skill,
                    'reason': f"등급 '{rank}'에서 '{skill}' 사용 불가",
                    'severity': 'HIGH'
                })

        # 3. 마나 고갈 상태
        mana = current_state.get('mana', current_state.get('MP', 100))
        if isinstance(mana, (int, float)) and mana <= 5:
            actions.append({
                'pattern': r'스킬.*발동|마나.*사용|능력.*발휘',
                'reason': '마나 고갈 상태에서 스킬 사용 불가',
                'severity': 'HIGH'
            })

        # 4. 미각성 상태
        awakening = current_state.get('awakening', current_state.get('각성', True))
        if awakening is False or awakening == '미각성':
            actions.append({
                'pattern': r'스킬|마나|능력|스탯|시스템',
                'reason': '미각성 상태에서 각성 능력 사용 불가',
                'severity': 'CRITICAL'
            })

        # 5. 쿨타임 중인 스킬
        cooldowns = current_state.get('skill_cooldowns', {})
        if isinstance(cooldowns, dict):
            for skill_name, remaining in cooldowns.items():
                if remaining and remaining > 0:
                    actions.append({
                        'pattern': skill_name,
                        'reason': f"'{skill_name}' 쿨타임 {remaining}초 남음",
                        'severity': 'MEDIUM'
                    })

        return actions

    def get_justification_patterns(self) -> List[str]:
        """
        [V46] 헌터물 - 정당화로 인정되는 표현 패턴

        "각성 폭발", "숨겨진 스킬 발현" 등의 패턴이 있으면
        불가능해 보이는 행동도 허용
        """
        return [
            # 각성/성장 관련
            r'각성.*폭발',
            r'숨겨진.*발현',
            r'잠재력.*깨어',
            r'새로운.*각성',
            r'진정한.*능력',
            r'한계.*돌파',

            # 아이템/보조 수단
            r'포션.*마셔',
            r'아이템.*사용',
            r'버프.*받',
            r'회복.*완료',
            r'장비.*효과',

            # 외부 도움
            r'힐러.*치료',
            r'서포터.*버프',
            r'동료.*도움',

            # 극한 상황
            r'죽기.*살기',
            r'생존.*본능',
            r'마지막.*힘',
            r'대가.*치르',

            # 시스템 관련
            r'시스템.*보상',
            r'특수.*효과',
            r'유니크.*스킬',
            r'히든.*퀘스트',
        ]

    def get_hierarchy_rules(self) -> Dict[str, Any]:
        """
        [V46] 헌터물 - 등급/호칭 위계 규칙

        헌터 등급에 따른 사회적 위치와 호칭
        """
        return {
            'ranks': self._rank_hierarchy,
            'titles': {
                'E': ['하급 헌터', '신입'],
                'D': ['하급 헌터', 'D급 헌터'],
                'C': ['중급 헌터', 'C급 헌터'],
                'B': ['고급 헌터', 'B급 헌터'],
                'A': ['상급 헌터', 'A급 헌터', '에이스'],
                'S': ['최상급 헌터', 'S급 헌터', '레전드'],
                'SS': ['초월자', '인간 재해'],
                'SSS': ['신화급', '인류 최강'],
                '국가급': ['국가 수호자', '국보급'],
                '세계급': ['세계 최강', '절대자'],
            },
            'address_rules': {
                'lower_to_higher': ['선배님', '~씨', '~님', '대장님'],
                'higher_to_lower': ['자네', '~군', '~야'],
                'peer': ['~씨', '동료', '파트너'],
            },
            # 등급 위반 패턴 (E급이 자칭할 수 없는 것들)
            'violations': {
                'E': [r'S급', r'A급', r'에이스', r'레전드', r'최강'],
                'D': [r'S급', r'A급', r'에이스', r'레전드'],
                'C': [r'S급', r'레전드', r'최강'],
                'B': [r'S급', r'레전드'],
            }
        }

    def get_technique_effect_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        [V46] 헌터물 - 스킬/아이템 효능 규칙

        특정 스킬이나 아이템의 정의된 효능과 사용 방식
        """
        return {
            # 스킬 효능
            '파이어볼': {
                'effect_type': 'offensive',
                'effect_scope': ['원거리', '화염', '단일'],
                'cannot_be_used_for': ['치료', '방어', '버프'],
            },
            '힐': {
                'effect_type': 'healing',
                'effect_scope': ['자신', '아군', 'HP'],
                'cannot_be_used_for': ['공격', '디버프'],
            },
            '쉴드': {
                'effect_type': 'defensive',
                'effect_scope': ['자신', '아군', '물리/마법'],
                'cannot_be_used_for': ['공격', '치료'],
            },
            '텔레포트': {
                'effect_type': 'movement',
                'effect_scope': ['자신', '순간이동'],
                'cannot_be_used_for': ['공격', '치료', '타인'],
            },

            # 아이템 효능
            'HP 포션': {
                'effect_type': 'healing',
                'effect_scope': ['자신', 'HP'],
                'cannot_be_used_for': ['마나 회복', '공격', '타인'],
                'transformation_allowed': False,
            },
            'MP 포션': {
                'effect_type': 'recovery',
                'effect_scope': ['자신', 'MP'],
                'cannot_be_used_for': ['HP 회복', '공격', '타인'],
                'transformation_allowed': False,
            },
            '독 포션': {
                'effect_type': 'debuff',
                'effect_scope': ['타인', '지속 피해'],
                'cannot_be_used_for': ['치료', '버프', '자신'],
                'transformation_allowed': False,
            },
        }

    # ========================================================================
    # [V46.1] 권위 위임 검증 (헌터물 특화)
    # ========================================================================

    def get_authority_hierarchy(self) -> Dict[str, Any]:
        """
        [V46.1] 헌터물 - 길드/협회 권위 위계

        길드장 > 부길드장 > 간부 > 정규 > 수습 순
        """
        return {
            'positions': ['길드장', '부길드장', '간부', '정규', '수습', '외부'],  # 높은 순
            'position_titles': {
                '길드장': ['길드장', '마스터', '수장'],
                '길드장대행': ['대행', '임시 길드장', '권한대행'],
                '부길드장': ['부길드장', '부마스터'],
                '간부': ['간부', '팀장', '파티장'],
                '정규': ['정규 길드원', '멤버'],
                '수습': ['수습', '신입', '트레이니'],
            },
            'delegation_required': ['길드장대행', '대행', '임시 길드장'],  # 명분 필요
            # 직위별 권한
            'authority_scope': {
                '길드장': ['제명', '임명', '계약', '자금운용'],
                '부길드장': ['징계', '파티편성', '임무배정'],
                '간부': ['훈련', '보고'],
                '정규': ['제안'],
                '수습': [],
            }
        }

    def get_delegation_patterns(self) -> List[str]:
        """
        [V46.1] 헌터물 - 권위 위임 정당화 패턴
        """
        return [
            # 직접 위임
            r'길드장.*명령',
            r'마스터.*위임',
            r'의 권한으로',
            r'허가.*받아',
            r'승인.*득해',

            # 상황적 정당화
            r'길드장.*부재',
            r'긴급.*상황',
            r'비상.*사태',
            r'레이드.*중',
            r'던전.*안',
        ]

    # ========================================================================
    # [V46.1] 미해결 갈등 검증 (헌터물 특화)
    # ========================================================================

    def get_hostile_action_types(self) -> List[str]:
        """
        [V46.1] 헌터물 - 적대적 행동 유형
        """
        return [
            '배신', 'PK', '킬스틸',
            '모욕', '무시', '왕따',
            '사기', '횡령',
            '암살시도', '습격',
            '협박', '갈취',
            '아이템강탈', '파티추방',
        ]

    def get_resolution_patterns(self) -> List[str]:
        """
        [V46.1] 헌터물 - 갈등 해소 패턴
        """
        return [
            # 용서/화해
            r'용서',
            r'화해',
            r'사과.*받',
            r'오해.*풀',

            # 복수/응징
            r'복수',
            r'응징',
            r'PK',
            r'처단',
            r'제명',

            # 굴복/공포
            r'무릎.*꿇',
            r'빌었다',
            r'공포.*질',
            r'벌벌',

            # 보상/배상
            r'배상',
            r'보상',
            r'합의금',
            r'아이템.*반환',
        ]

    # ========================================================================
    # [V46.1] 빌런 반응 검증 (헌터물 특화)
    # ========================================================================

    def get_protagonist_victory_patterns(self) -> List[str]:
        """
        [V46.1] 헌터물 - 주인공 대역전/승리 패턴
        """
        return [
            # 전투 승리
            r'승리',
            r'이겼다',
            r'쓰러뜨',
            r'처치',
            r'클리어',

            # 각성/성장
            r'각성',
            r'랭크업',
            r'진화',
            r'새로운.*스킬',

            # 음모 파훼
            r'정체.*밝혀',
            r'음모.*파훼',
            r'증거.*확보',

            # 인정
            r'S급.*인정',
            r'협회.*인증',
            r'길드장.*승인',
        ]

    def get_villain_response_patterns(self) -> List[str]:
        """
        [V46.1] 헌터물 - 빌런 적절 대응 패턴
        """
        return [
            # 감정 반응
            r'당황',
            r'경악',
            r'분노',
            r'이를.*갈',
            r'화.*삭',

            # 계획 수정
            r'계획.*변경',
            r'플랜B',
            r'후퇴',
            r'철수',

            # 지능적 제약
            r'던전.*입장',
            r'레이드.*참가',
            r'해외.*출장',
            r'협회.*소환',
            r'긴급.*미션',

            # 다음 기회
            r'두고.*보자',
            r'끝.*아니',
            r'다음.*기회',
            r'반드시',
        ]
