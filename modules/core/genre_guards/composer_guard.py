"""
[V61.8] 작곡가물 전용 Guard
[V57] 완전 구현 - 일관성 검증, 권위 위계, 타임라인 검증
음악 업계의 전문성과 개연성을 유지
"""

from typing import List, Dict, Any, Tuple
from .base_guard import BaseGuard


class ComposerGuard(BaseGuard):
    """[작곡가물] 음악 산업 전문성 보호자 + V57 완전 구현"""

    def __init__(self):
        super().__init__()

        # 작곡가물에서 금지되는 용어 (무협/판타지/헌터 용어)
        self.FORBIDDEN_TERMS = [
            "내공", "진기", "마나", "스킬", "던전", "게이트", "각성", "헌터",
            "검기", "검강", "초식", "보법", "무림", "강호", "문파", "장로",
            "마법", "주문", "포션", "엘프", "드워프", "드래곤", "오크",
            "레벨업", "경험치", "스테이터스", "인벤토리", "버프", "디버프",
            "상태창", "시스템 창", "퀘스트", "레이드",
        ]

        # 음악 업계 전문 용어 (정확하게 사용해야 함)
        self.MUSIC_TERMS = [
            "BPM", "코드 진행", "멜로디", "하모니", "리듬", "비트",
            "브릿지", "훅", "벌스", "코러스", "프리코러스", "아웃트로", "인트로",
            "마스터링", "믹싱", "레코딩", "프로듀싱", "편곡", "작곡", "작사",
            "저작권", "저작인접권", "음원", "음반", "앨범", "싱글", "타이틀곡",
            "차트", "스트리밍", "음원 사재기", "역주행", "올킬",
            "기획사", "레이블", "매니지먼트", "에이전시",
            "시상식", "음악방송", "컴백", "활동", "안무", "퍼포먼스",
            "보컬", "래퍼", "프로듀서", "디제이", "세션맨",
            "키", "옥타브", "전조", "음색", "음역대",
            "DAW", "미디", "신디사이저", "샘플링", "루프",
        ]

        # 작곡가물 필수 개념
        self.MANDATORY_CONCEPTS = [
            "음악 창작 과정의 구체적 묘사",
            "음악 업계 생태계의 사실적 반영",
            "저작권과 계약 관계의 현실성",
            "청중 반응과 차트 성적의 개연성",
        ]

        # [V57] 명성 등급
        self._fame_hierarchy = [
            '무명', '신인', '주목받는', '인기', '스타', '톱스타', '레전드',
        ]

        # [V57] 명성 등급별 범위 (팔로워/인지도 기준)
        self._fame_ranges = {
            '무명': (0, 1_000),
            '신인': (1_000, 10_000),
            '주목받는': (10_000, 100_000),
            '인기': (100_000, 1_000_000),
            '스타': (1_000_000, 10_000_000),
            '톱스타': (10_000_000, 50_000_000),
            '레전드': (50_000_000, float('inf')),
        }

        # [V57] 명성 등급별 행동 불가 패턴
        self._fame_action_limits = {
            '무명': [r'대형.*콘서트', r'해외.*투어', r'광고.*모델', r'시상식.*수상'],
            '신인': [r'대형.*콘서트', r'해외.*투어', r'글로벌.*계약'],
            '주목받는': [r'단독.*월드투어', r'글로벌.*레이블'],
            '인기': [r'레전드.*반열'],
        }

        # [V57] 상태별 불가능 행동
        self._status_action_limits = {
            '슬럼프': [r'히트곡.*생산', r'걸작.*완성', r'영감.*폭발'],
            '계약분쟁': [r'신규.*계약', r'앨범.*발매', r'공식.*활동'],
            '부상': [r'라이브.*공연', r'콘서트', r'녹음', r'연주'],
            '은퇴': [r'컴백', r'신곡.*발매', r'활동.*재개'],
            '논란': [r'광고.*촬영', r'방송.*출연', r'팬미팅'],
        }

        # [V57] 음악 활동별 최소 요건
        self._activity_requirements = {
            '싱글 발매': {'reputation': '신인', 'contract': True},
            '정규 앨범': {'reputation': '주목받는', 'tracks': 8},
            '단독 콘서트': {'reputation': '인기', 'fanbase': 10_000},
            '해외 투어': {'reputation': '스타', 'global_fanbase': True},
            '작곡 의뢰': {'reputation': '주목받는', 'portfolio': 5},
            '프로듀싱': {'reputation': '주목받는', 'skills': ['production']},
            '음악 방송 1위': {'reputation': '인기', 'chart_rank': 10},
        }

        # [V57] 차트 성적 현실성 (주간 스트리밍 수)
        self._realistic_chart = {
            '무명': (0, 10_000),
            '신인': (1_000, 100_000),
            '주목받는': (10_000, 1_000_000),
            '인기': (100_000, 10_000_000),
            '스타': (1_000_000, 50_000_000),
            '톱스타': (5_000_000, 200_000_000),
            '레전드': (10_000_000, float('inf')),
        }

    def get_genre_name(self):
        return "작곡가물(COMPOSER)"

    def _should_check_english(self):
        """작곡가물은 현대 배경이므로 영어 완화 (음악 용어에 영어 많음)"""
        return False

    def _should_check_numbers(self):
        """작곡가물은 차트/수익 등 정확한 수치가 중요"""
        return False

    def get_v20_purism_prompt(self):
        """작곡가물 장르 전문성 지침"""
        return f"""
[🎵 V61.8 작곡가물 장르 가이드라인 (Composer Genre Professionalism)]

1. **장르 교란 금지**: 판타지/무협 용어({', '.join(self.FORBIDDEN_TERMS[:8])} 등)를 사용하지 마라. 현실적인 음악 업계 세계관을 유지하라.
2. **음악 상식 준수**: 모든 음악 활동은 업계 관행과 현실에 부합해야 한다. 근거 없는 차트 올킬이나 비현실적 성공은 금지한다.
3. **전문 용어의 정확성**: {', '.join(self.MUSIC_TERMS[:10])} 등의 음악 용어를 정확하게 사용하라.
4. **성장의 개연성**: 주인공의 명성 상승은 반드시 구체적인 작품 활동과 업계 반응에 기반해야 한다.
5. **창작 과정의 묘사**: 작곡/편곡/프로듀싱 과정을 감각적이고 구체적으로 묘사하라. 음악을 글로 전달하는 기술이 핵심이다.
6. **업계 생태계**: 기획사, 프로듀서, 아티스트, 매니저, 평론가 등 다양한 이해관계자들의 역학 관계를 입체적으로 그려라.
7. **법률과 계약**: 저작권, 전속계약, 수익 분배 등의 법적 관계를 사실적으로 다뤄라.
8. **시대적 배경**: 스트리밍, SNS, K-POP 글로벌화 등 현대 음악 산업의 트렌드를 자연스럽게 활용하라.
9. **필수 표현 요소**: {', '.join(self.MANDATORY_CONCEPTS)}

[개연성 체크리스트]
- 차트 성적이 주인공의 명성 수준에 부합하는가?
- 음원 발매/활동에 필요한 계약/소속 관계가 갖춰져 있는가?
- 주인공의 음악적 역량 성장에 구체적 근거(연습, 멘토, 경험)가 있는가?
- 업계 반응(평론, 차트, 팬덤)이 일관성 있게 묘사되는가?
"""

    # ========================================================================
    # [V57] 일관성 검증 구현 (작곡가물 특화)
    # ========================================================================

    def get_impossible_actions(self, current_state: Dict[str, Any]) -> List[Dict[str, str]]:
        """[V57] 작곡가물 - 현재 상태에서 불가능한 행동 패턴 반환"""
        actions = []

        # 1. 상태 기반 제한 (슬럼프, 계약분쟁 등)
        status = current_state.get('mental_state', current_state.get('status', ''))
        if isinstance(status, str):
            for status_keyword, patterns in self._status_action_limits.items():
                if status_keyword in status:
                    for pattern in patterns:
                        actions.append({
                            'pattern': pattern,
                            'reason': f"상태 '{status_keyword}'로 인해 불가",
                            'severity': 'HIGH'
                        })

        # 2. 명성 등급 기반 제한
        fame = current_state.get('reputation', current_state.get('fame', '무명'))
        fame_class = self._get_fame_class(fame)
        if fame_class and fame_class in self._fame_action_limits:
            for pattern in self._fame_action_limits[fame_class]:
                actions.append({
                    'pattern': pattern,
                    'reason': f"명성 '{fame_class}'에서 불가",
                    'severity': 'HIGH'
                })

        # 3. 슬럼프/창작 고통
        creative_block = current_state.get('creative_block', '없음')
        if creative_block and creative_block not in ('없음', '정상', ''):
            actions.append({
                'pattern': r'걸작.*완성|천재적.*영감|순식간.*작곡',
                'reason': f'창작 고통 상태: {creative_block}',
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
        """명성 수준에 따른 등급 반환"""
        if isinstance(fame, str):
            for cls_name in self._fame_hierarchy:
                if cls_name in fame:
                    return cls_name
            return '무명'
        if isinstance(fame, (int, float)):
            for cls_name, (min_val, max_val) in self._fame_ranges.items():
                if min_val <= fame < max_val:
                    return cls_name
        return '무명'

    def get_justification_patterns(self) -> List[str]:
        """[V57] 작곡가물 - 정당화로 인정되는 표현 패턴"""
        return [
            # 미래 정보 활용 (회귀물)
            r'미래.*기억', r'과거.*경험', r'전생.*정보',

            # 정당한 성장
            r'연습.*결과', r'멘토.*지도', r'실력.*향상',
            r'오디션.*통과', r'콩쿠르.*입상',

            # 인맥 활용
            r'인맥.*통해', r'소개.*받', r'추천.*덕분',
            r'업계.*관계자',

            # 재능/노력
            r'천부적.*재능', r'절대음감', r'타고난',
            r'밤새.*작업', r'피나는.*연습',

            # 합법적 기회
            r'공모전', r'공개.*오디션', r'SNS.*입소문',
            r'바이럴', r'차트.*역주행',
        ]

    def get_hierarchy_rules(self) -> Dict[str, Any]:
        """[V57] 작곡가물 - 명성/지위 위계 규칙"""
        return {
            'fame_classes': self._fame_hierarchy,
            'titles': {
                '무명': ['무명 작곡가', '인디', '지망생'],
                '신인': ['신인 작곡가', '루키'],
                '주목받는': ['주목받는 작곡가', '떠오르는'],
                '인기': ['인기 작곡가', '히트메이커'],
                '스타': ['스타 프로듀서', '톱 작곡가'],
                '톱스타': ['거장', '전설급'],
                '레전드': ['레전드', '음악의 신'],
            },
            'violations': {
                '무명': [r'톱스타', r'레전드', r'해외.*투어', r'시상식.*수상'],
                '신인': [r'톱스타', r'레전드', r'월드투어'],
                '주목받는': [r'레전드', r'글로벌.*지배'],
            }
        }

    def get_technique_effect_rules(self) -> Dict[str, Dict[str, Any]]:
        """[V57] 작곡가물 - 음악 활동별 효능 규칙"""
        return {
            '싱글 발매': {
                'effect_type': 'release',
                'effect_scope': ['명성 상승', '수익', '팬덤 확보'],
                'cannot_be_used_for': ['즉각적 부유', '즉시 레전드'],
                'risk': '흥행 실패 시 명성 하락',
            },
            '정규 앨범': {
                'effect_type': 'album',
                'effect_scope': ['대폭 명성 상승', '시상식 후보', '투어 기반'],
                'cannot_be_used_for': ['소규모 테스트'],
                'requirements': ['최소 8곡', '계약/레이블', '마케팅'],
            },
            '프로듀싱': {
                'effect_type': 'production',
                'effect_scope': ['수익', '업계 인맥', '실력 인정'],
                'cannot_be_used_for': ['직접적 팬덤', '개인 명성 급등'],
                'requirements': ['프로듀싱 실력', '스튜디오 접근'],
            },
            '콘서트/투어': {
                'effect_type': 'live',
                'effect_scope': ['팬덤 강화', '수익', '라이브 명성'],
                'cannot_be_used_for': ['음원 차트 상승'],
                'requirements': ['충분한 팬베이스', '기획/제작 능력'],
            },
            '작곡 의뢰': {
                'effect_type': 'commission',
                'effect_scope': ['수익', '업계 입지', '포트폴리오'],
                'cannot_be_used_for': ['개인 팬덤', '차트 성적'],
                'requirements': ['검증된 포트폴리오', '업계 인맥'],
            },
        }

    # ========================================================================
    # [V57] 권위 위계 검증 (작곡가물 특화)
    # ========================================================================

    def get_authority_hierarchy(self) -> Dict[str, Any]:
        """[V57] 작곡가물 - 음악 업계 권위 위계"""
        return {
            'positions': ['대표', '본부장', 'A&R 디렉터', '프로듀서', '매니저', '트레이너', '스태프'],
            'position_titles': {
                '대표': ['대표', '회장', '사장', 'CEO'],
                '본부장': ['본부장', '이사', '실장'],
                'A&R 디렉터': ['A&R', '디렉터', '기획팀장'],
                '프로듀서': ['PD', '프로듀서', '총괄PD'],
                '매니저': ['매니저', '담당자', '로드매니저'],
                '트레이너': ['트레이너', '보컬 트레이너', '안무가'],
                '스태프': ['스태프', '엔지니어', '세션'],
            },
            'authority_scope': {
                '대표': ['계약', '전략', '인사', '투자'],
                '본부장': ['기획', '마케팅', '예산'],
                'A&R 디렉터': ['아티스트 발굴', '앨범 기획', '컨셉'],
                '프로듀서': ['음악 제작', '녹음', '편곡 방향'],
                '매니저': ['스케줄', '현장 관리'],
            }
        }

    def get_delegation_patterns(self) -> List[str]:
        """[V57] 작곡가물 - 권위 위임 정당화 패턴"""
        return [
            r'대표.*지시',
            r'프로듀서.*결정',
            r'계약.*조건',
            r'A&R.*승인',
            r'소속사.*방침',
            r'긴급.*상황',
        ]

    # ========================================================================
    # [V57] 갈등 및 해소 검증
    # ========================================================================

    def get_hostile_action_types(self) -> List[str]:
        """[V57] 작곡가물 - 적대적 행동 유형"""
        return [
            '표절 고소', '계약 위반', '저작권 분쟁',
            '악성 루머', '악플 테러', '음원 사재기 폭로',
            '전속계약 소송', '수익 분배 분쟁',
            '팬덤 전쟁', '디스곡', '폭로',
            '기획사 갑질', '노예계약',
        ]

    def get_resolution_patterns(self) -> List[str]:
        """[V57] 작곡가물 - 갈등 해소 패턴"""
        return [
            # 합의
            r'합의', r'화해', r'협상.*타결', r'재계약',

            # 승리
            r'차트.*1위', r'시상식.*수상', r'역주행',
            r'소송.*승소', r'표절.*무혐의',

            # 실력 증명
            r'걸작.*발표', r'대중.*인정', r'평단.*호평',
            r'글로벌.*진출', r'콜라보.*성공',

            # 독립
            r'독립.*레이블', r'자체.*프로덕션', r'1인.*기획사',
            r'전속.*해지', r'자유.*계약',
        ]

    # ========================================================================
    # [V57] 음악 검증 헬퍼
    # ========================================================================

    def get_music_rules_prompt(self) -> str:
        """[V57] 음악 규칙 프롬프트 생성 (Writer/Architect 주입용)"""
        return """
[V57 작곡가물 음악 메카닉스]

1. **명성 등급별 행동 제약**
   - 무명~신인: 인디 활동, 소규모 공연, 작곡 의뢰
   - 주목받는~인기: 음악방송, 정규앨범, 팬사인회
   - 스타 이상: 대형 콘서트, 해외 투어, 글로벌 콜라보

2. **음악 활동 현실성**
   - 싱글 발매: 소속사/레이블 필요 (인디 자체발매 가능)
   - 정규 앨범: 최소 8트랙, 제작비, 마케팅
   - 콘서트: 팬베이스 기반, 기획/제작 인프라

3. **차트 성적 현실성**
   - 무명: 주간 스트리밍 0~1만
   - 인기: 10만~1000만
   - 톱스타: 500만~2억

4. **회귀물 특수 규칙**
   - 회귀 시점 이전의 히트곡 정보 활용 가능
   - 나비 효과로 트렌드 변경 가능성
   - 미래 곡 표절 시 도덕적 딜레마 묘사 필수

5. **법률/계약 제약**
   - 전속계약: 기간, 수익 분배율, 위약금
   - 저작권: 작곡/작사/편곡 각각 별도 권리
   - 표절: 8마디 이상 유사 시 법적 문제
"""

    # ========================================================================
    # [V66] 심층 검증 오버라이드
    # ========================================================================

    def run_deep_validation(self, manuscript: str, current_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """[V66] 작곡가물 심층 검증."""
        result = super().run_deep_validation(manuscript, current_state or {})

        # 작곡가물 추가 검증: 상태/명성 기반 불가 행동 체크
        if current_state:
            impossible = self.get_impossible_actions(current_state)
            import re
            for action in impossible:
                pattern = action.get('pattern', '')
                if pattern and re.search(pattern, manuscript):
                    result["violations"].append({
                        "type": "impossible_action",
                        "severity": action.get('severity', 'HIGH'),
                        "message": f"불가 행동 감지: {action.get('reason', '')}"
                    })

        result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violations"])
        if result["violations"]:
            result["summary"] = "; ".join(v.get("message", "") for v in result["violations"][:5])
            result["feedback"] = f"[작곡가물 Guard] {len(result['violations'])}건: {result['summary']}"
        return result
