"""
[V40 Multi-Genre] 헌터물 전용 Guard
[V46] 일관성 검증 규칙 추가 - 상태 vs 행동, 정당화 패턴, 등급 위계
[V46.1] 권위 위임, 미해결 갈등(고구마), 빌런 반응 검증 추가
[V57] 던전/각성/쿨다운 규칙 확장
헌터물 장르의 일관성을 유지하고 무협 용어를 차단
"""

import re
from typing import Any

from .base_guard import BaseGuard


class HunterGuard(BaseGuard):
    """[헌터물] 장르 일관성 보호자 + V46 일관성 검증 + V57 확장"""

    def __init__(self) -> None:
        super().__init__()
        cfg = self._load_genre_yaml("hunter")

        # 헌터물에서 금지되는 용어 (YAML 우선, 없으면 하드코딩 폴백)
        self.FORBIDDEN_TERMS = cfg.get(
            "forbidden_terms",
            [
                "내공",
                "진기",
                "단전",
                "임독이맥",
                "주화입마",
                "기감",
                "초식",
                "보법",
                "검기",
                "검강",
                "강기",
                "기공",
                "경지",
                "일류",
                "절정",
                "화경",
                "현경",
                "무림",
                "강호",
                "문파",
                "장로",
                "대협",
                "소협",
                "본좌",
                "포권례",
                "은원",
                "항렬",
                "사숙",
                "사조",
                "장경각",
                "비급",
                "심법",
                "전음입밀",
                "영약",
                "영물",
                "내단",
                "환골탈태",
                "기맥",
                "혈도",
                "점혈",
                "투경",
            ],
        )

        self.ALLOWED_TERMS = cfg.get(
            "allowed_terms",
            [
                "스킬",
                "마나",
                "던전",
                "게이트",
                "레이드",
                "길드",
                "각성",
                "랭크",
                "헌터",
                "시스템",
                "스테이터스",
                "레벨",
                "경험치",
                "스탯",
                "포인트",
                "아이템",
                "인벤토리",
                "퀘스트",
                "포션",
                "버프",
                "디버프",
                "쿨타임",
                "HP",
                "MP",
                "공격력",
                "방어력",
                "민첩",
                "지능",
                "체력",
            ],
        )

        self.MANDATORY_CONCEPTS = cfg.get(
            "mandatory_concepts",
            [
                "던전과 게이트의 명확한 구분",
                "각성 능력의 체계적 표현",
                "길드 시스템과 사회적 관계",
                "성장과 랭크업의 쾌감",
            ],
        )

        self._rank_hierarchy = cfg.get(
            "rank_hierarchy", ["E", "D", "C", "B", "A", "S", "SS", "SSS", "국가급", "세계급"]
        )

        self._rank_skill_limits = cfg.get(
            "rank_technique_limits",
            {
                "E": ["S급 스킬", "A급 스킬", "영역 전개", "차원", "시공간", "불멸", "신화급"],
                "D": ["S급 스킬", "A급 스킬", "영역 전개", "차원", "불멸", "신화급"],
                "C": ["S급 스킬", "영역 전개", "차원", "불멸", "신화급"],
                "B": ["S급 스킬", "차원", "불멸", "신화급"],
                "A": ["차원 절단", "불멸", "신화급"],
                "S": ["신화급", "세계급 스킬"],
            },
        )

        self._status_action_limits = cfg.get(
            "status_action_limits",
            {
                "마나 고갈": [r"스킬.*발동", r"마나.*사용", r"능력.*발휘", r"마법.*시전"],
                "중상": [r"전력.*질주", r"고속.*이동", r"연속.*공격", r"회피.*기동"],
                "기절": [r"눈.*떠", r"공격", r"방어", r"이동"],
                "HP 위험": [r"무리.*공격", r"전력.*질주", r"자폭"],
            },
        )

        self._dungeon_entry_requirements = cfg.get(
            "dungeon_requirements",
            {
                "E급": {"min_rank": "E", "recommended_rank": "E", "min_party": 1},
                "D급": {"min_rank": "E", "recommended_rank": "D", "min_party": 2},
                "C급": {"min_rank": "D", "recommended_rank": "C", "min_party": 3},
                "B급": {"min_rank": "C", "recommended_rank": "B", "min_party": 4},
                "A급": {"min_rank": "B", "recommended_rank": "A", "min_party": 5},
                "S급": {"min_rank": "A", "recommended_rank": "S", "min_party": 8},
                "SS급": {"min_rank": "S", "recommended_rank": "SS", "min_party": 10},
                "SSS급": {"min_rank": "SS", "recommended_rank": "SSS", "min_party": 20},
                "레드 게이트": {"min_rank": "S", "special": "탈출 불가"},
                "블랙 게이트": {"min_rank": "SS", "special": "국가급 헌터 필수"},
            },
        )

        self._dungeon_break_rules = {
            "E급": {"max_consecutive": 3, "rest_required": 0},
            "D급": {"max_consecutive": 3, "rest_required": 0},
            "C급": {"max_consecutive": 2, "rest_required": 4},
            "B급": {"max_consecutive": 2, "rest_required": 8},
            "A급": {"max_consecutive": 1, "rest_required": 24},
            "S급": {"max_consecutive": 1, "rest_required": 48},
        }

        self._awakening_stages = [
            "미각성",
            "초기 각성",
            "1차 각성",
            "2차 각성",
            "3차 각성",
            "완전 각성",
            "초월 각성",
        ]

        self._awakening_abilities = {
            "미각성": {"max_skills": 0, "stat_multiplier": 1.0, "can_see_system": False},
            "초기 각성": {"max_skills": 1, "stat_multiplier": 1.5, "can_see_system": True},
            "1차 각성": {"max_skills": 3, "stat_multiplier": 2.0, "can_see_system": True},
            "2차 각성": {"max_skills": 5, "stat_multiplier": 3.0, "can_see_system": True},
            "3차 각성": {"max_skills": 8, "stat_multiplier": 5.0, "can_see_system": True},
            "완전 각성": {"max_skills": 12, "stat_multiplier": 10.0, "can_see_system": True},
            "초월 각성": {"max_skills": -1, "stat_multiplier": -1, "can_see_system": True},
        }

        self._default_skill_cooldowns = {
            "기본 공격": 0,
            "버프": 60,
            "디버프": 90,
            "회복": 30,
            "궁극기": 300,
            "영역 전개": 600,
            "각성 스킬": 3600,
            "유니크 스킬": 86400,
        }

    def get_genre_name(self) -> str:
        return "헌터물(HUNTER)"

    def _should_check_english(self) -> bool:
        """헌터물은 현대 배경이므로 영어 완화"""
        return False

    def _should_check_numbers(self) -> bool:
        """헌터물은 수치 표현이 중요하므로 아라비아 숫자 허용"""
        return False

    def get_v20_purism_prompt(self) -> str:
        """헌터물 장르 일관성 지침"""
        return f"""
[🎮 V40 헌터물 장르 가이드라인 (Hunter Genre Consistency)]

1. **장르 교란 금지**: 무협 용어({", ".join(self.FORBIDDEN_TERMS[:8])} 등)를 사용하지 마라. 헌터물의 세계관을 유지하라.
2. **시스템 요소의 일관성**: 스킬, 마나, 던전, 길드 등의 시스템 요소는 작품 전체에서 일관된 규칙으로 작동해야 한다.
3. **현대적 배경 활용**: 스마트폰, 인터넷, SNS 등 현대 문물을 자연스럽게 활용하라.
4. **각성 능력의 체계성**: 주인공의 각성 능력은 명확한 원리와 제약이 있어야 하며, 갑작스러운 파워업은 반드시 합리적 근거가 있어야 한다.
5. **전투 묘사**: 스킬 발동 시의 시각적 효과, 마나 소모, 쿨타임 등을 구체적으로 묘사하라.
6. **사회적 배경**: 길드, 협회, 정부 기관 등 헌터 사회의 구조를 현실감 있게 그려라.
7. **금융/경제 요소**: 던전 보상, 아이템 거래, 헌터의 수입 등 경제적 측면도 설득력 있게 표현하라.
8. **필수 표현 요소**: {", ".join(self.MANDATORY_CONCEPTS)}
"""

    # ========================================================================
    # [V46] 일관성 검증 구현 (헌터물 특화)
    # ========================================================================

    def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]:
        """
        [V46] 헌터물 - 현재 상태에서 불가능한 행동 패턴 반환

        동적 규칙 생성: HUD의 rank, mana, status에서 추론
        """
        actions = []

        # 1. 상태 기반 제한 (마나 고갈, 중상 등)
        status = current_state.get("status", "")
        if isinstance(status, str):
            for status_keyword, patterns in self._status_action_limits.items():
                if status_keyword in status:
                    for pattern in patterns:
                        actions.append(
                            {"pattern": pattern, "reason": f"상태 '{status_keyword}'로 인해 불가", "severity": "HIGH"}
                        )

        # 2. 등급 기반 스킬 제한
        rank = current_state.get("rank", current_state.get("realm", ""))
        if rank and rank.upper() in self._rank_skill_limits:
            forbidden_skills = self._rank_skill_limits[rank.upper()]
            for skill in forbidden_skills:
                actions.append(
                    {"pattern": skill, "reason": f"등급 '{rank}'에서 '{skill}' 사용 불가", "severity": "HIGH"}
                )

        # 3. 마나 고갈 상태
        mana = current_state.get("mana", current_state.get("MP", 100))
        if isinstance(mana, int | float) and mana <= 5:
            actions.append(
                {
                    "pattern": r"스킬.*발동|마나.*사용|능력.*발휘",
                    "reason": "마나 고갈 상태에서 스킬 사용 불가",
                    "severity": "HIGH",
                }
            )

        # 4. 미각성 상태
        awakening = current_state.get("awakening", current_state.get("각성", True))
        if awakening is False or awakening == "미각성":
            actions.append(
                {
                    "pattern": r"스킬|마나|능력|스탯|시스템",
                    "reason": "미각성 상태에서 각성 능력 사용 불가",
                    "severity": "CRITICAL",
                }
            )

        # 5. 쿨타임 중인 스킬
        cooldowns = current_state.get("skill_cooldowns", {})
        if isinstance(cooldowns, dict):
            for skill_name, remaining in cooldowns.items():
                if remaining and remaining > 0:
                    actions.append(
                        {
                            "pattern": re.escape(skill_name),
                            "reason": f"'{skill_name}' 쿨타임 {remaining}초 남음",
                            "severity": "MEDIUM",
                        }
                    )

        return actions

    def get_justification_patterns(self) -> list[str]:
        """
        [V46] 헌터물 - 정당화로 인정되는 표현 패턴

        "각성 폭발", "숨겨진 스킬 발현" 등의 패턴이 있으면
        불가능해 보이는 행동도 허용
        """
        return [
            # 각성/성장 관련
            r"각성.*폭발",
            r"숨겨진.*발현",
            r"잠재력.*깨어",
            r"새로운.*각성",
            r"진정한.*능력",
            r"한계.*돌파",
            # 아이템/보조 수단
            r"포션.*마셔",
            r"아이템.*사용",
            r"버프.*받",
            r"회복.*완료",
            r"장비.*효과",
            # 외부 도움
            r"힐러.*치료",
            r"서포터.*버프",
            r"동료.*도움",
            # 극한 상황
            r"죽기.*살기",
            r"생존.*본능",
            r"마지막.*힘",
            r"대가.*치르",
            # 시스템 관련
            r"시스템.*보상",
            r"특수.*효과",
            r"유니크.*스킬",
            r"히든.*퀘스트",
        ]

    def get_hierarchy_rules(self) -> dict[str, Any]:
        """
        [V46] 헌터물 - 등급/호칭 위계 규칙

        헌터 등급에 따른 사회적 위치와 호칭
        """
        return {
            "ranks": self._rank_hierarchy,
            "titles": {
                "E": ["하급 헌터", "신입"],
                "D": ["하급 헌터", "D급 헌터"],
                "C": ["중급 헌터", "C급 헌터"],
                "B": ["고급 헌터", "B급 헌터"],
                "A": ["상급 헌터", "A급 헌터", "에이스"],
                "S": ["최상급 헌터", "S급 헌터", "레전드"],
                "SS": ["초월자", "인간 재해"],
                "SSS": ["신화급", "인류 최강"],
                "국가급": ["국가 수호자", "국보급"],
                "세계급": ["세계 최강", "절대자"],
            },
            "address_rules": {
                "lower_to_higher": ["선배님", "~씨", "~님", "대장님"],
                "higher_to_lower": ["자네", "~군", "~야"],
                "peer": ["~씨", "동료", "파트너"],
            },
            # 등급 위반 패턴 (E급이 자칭할 수 없는 것들)
            "violations": {
                "E": [r"S급", r"A급", r"에이스", r"레전드", r"최강"],
                "D": [r"S급", r"A급", r"에이스", r"레전드"],
                "C": [r"S급", r"레전드", r"최강"],
                "B": [r"S급", r"레전드"],
            },
        }

    def get_technique_effect_rules(self) -> dict[str, dict[str, Any]]:
        """
        [V46] 헌터물 - 스킬/아이템 효능 규칙

        특정 스킬이나 아이템의 정의된 효능과 사용 방식
        """
        return {
            # 스킬 효능
            "파이어볼": {
                "effect_type": "offensive",
                "effect_scope": ["원거리", "화염", "단일"],
                "cannot_be_used_for": ["치료", "방어", "버프"],
            },
            "힐": {
                "effect_type": "healing",
                "effect_scope": ["자신", "아군", "HP"],
                "cannot_be_used_for": ["공격", "디버프"],
            },
            "쉴드": {
                "effect_type": "defensive",
                "effect_scope": ["자신", "아군", "물리/마법"],
                "cannot_be_used_for": ["공격", "치료"],
            },
            "텔레포트": {
                "effect_type": "movement",
                "effect_scope": ["자신", "순간이동"],
                "cannot_be_used_for": ["공격", "치료", "타인"],
            },
            # 아이템 효능
            "HP 포션": {
                "effect_type": "healing",
                "effect_scope": ["자신", "HP"],
                "cannot_be_used_for": ["마나 회복", "공격", "타인"],
                "transformation_allowed": False,
            },
            "MP 포션": {
                "effect_type": "recovery",
                "effect_scope": ["자신", "MP"],
                "cannot_be_used_for": ["HP 회복", "공격", "타인"],
                "transformation_allowed": False,
            },
            "독 포션": {
                "effect_type": "debuff",
                "effect_scope": ["타인", "지속 피해"],
                "cannot_be_used_for": ["치료", "버프", "자신"],
                "transformation_allowed": False,
            },
        }

    # ========================================================================
    # [V46.1] 권위 위임 검증 (헌터물 특화)
    # ========================================================================

    def get_authority_hierarchy(self) -> dict[str, Any]:
        """
        [V46.1] 헌터물 - 길드/협회 권위 위계

        길드장 > 부길드장 > 간부 > 정규 > 수습 순
        """
        return {
            "positions": ["길드장", "부길드장", "간부", "정규", "수습", "외부"],  # 높은 순
            "position_titles": {
                "길드장": ["길드장", "마스터", "수장"],
                "길드장대행": ["대행", "임시 길드장", "권한대행"],
                "부길드장": ["부길드장", "부마스터"],
                "간부": ["간부", "팀장", "파티장"],
                "정규": ["정규 길드원", "멤버"],
                "수습": ["수습", "신입", "트레이니"],
            },
            "delegation_required": ["길드장대행", "대행", "임시 길드장"],  # 명분 필요
            # 직위별 권한
            "authority_scope": {
                "길드장": ["제명", "임명", "계약", "자금운용"],
                "부길드장": ["징계", "파티편성", "임무배정"],
                "간부": ["훈련", "보고"],
                "정규": ["제안"],
                "수습": [],
            },
        }

    def get_delegation_patterns(self) -> list[str]:
        """
        [V46.1] 헌터물 - 권위 위임 정당화 패턴
        """
        return [
            # 직접 위임
            r"길드장.*명령",
            r"마스터.*위임",
            r"의 권한으로",
            r"허가.*받아",
            r"승인.*득해",
            # 상황적 정당화
            r"길드장.*부재",
            r"긴급.*상황",
            r"비상.*사태",
            r"레이드.*중",
            r"던전.*안",
        ]

    # ========================================================================
    # [V46.1] 미해결 갈등 검증 (헌터물 특화)
    # ========================================================================

    def get_hostile_action_types(self) -> list[str]:
        """
        [V46.1] 헌터물 - 적대적 행동 유형
        """
        return [
            "배신",
            "PK",
            "킬스틸",
            "모욕",
            "무시",
            "왕따",
            "사기",
            "횡령",
            "암살시도",
            "습격",
            "협박",
            "갈취",
            "아이템강탈",
            "파티추방",
        ]

    def get_resolution_patterns(self) -> list[str]:
        """
        [V46.1] 헌터물 - 갈등 해소 패턴
        """
        return [
            # 용서/화해
            r"용서",
            r"화해",
            r"사과.*받",
            r"오해.*풀",
            # 복수/응징
            r"복수",
            r"응징",
            r"PK",
            r"처단",
            r"제명",
            # 굴복/공포
            r"무릎.*꿇",
            r"빌었다",
            r"공포.*질",
            r"벌벌",
            # 보상/배상
            r"배상",
            r"보상",
            r"합의금",
            r"아이템.*반환",
        ]

    # ========================================================================
    # [V46.1] 빌런 반응 검증 (헌터물 특화)
    # ========================================================================

    def get_protagonist_victory_patterns(self) -> list[str]:
        """
        [V46.1] 헌터물 - 주인공 대역전/승리 패턴
        """
        return [
            # 전투 승리
            r"승리",
            r"이겼다",
            r"쓰러뜨",
            r"처치",
            r"클리어",
            # 각성/성장
            r"각성",
            r"랭크업",
            r"진화",
            r"새로운.*스킬",
            # 음모 파훼
            r"정체.*밝혀",
            r"음모.*파훼",
            r"증거.*확보",
            # 인정
            r"S급.*인정",
            r"협회.*인증",
            r"길드장.*승인",
        ]

    def get_villain_response_patterns(self) -> list[str]:
        """
        [V46.1] 헌터물 - 빌런 적절 대응 패턴
        """
        return [
            # 감정 반응
            r"당황",
            r"경악",
            r"분노",
            r"이를.*갈",
            r"화.*삭",
            # 계획 수정
            r"계획.*변경",
            r"플랜B",
            r"후퇴",
            r"철수",
            # 지능적 제약
            r"던전.*입장",
            r"레이드.*참가",
            r"해외.*출장",
            r"협회.*소환",
            r"긴급.*미션",
            # 다음 기회
            r"두고.*보자",
            r"끝.*아니",
            r"다음.*기회",
            r"반드시",
        ]

    # ========================================================================
    # [V57] 던전 메카닉스 검증
    # ========================================================================

    def validate_dungeon_entry(self, dungeon_grade: str, hunter_rank: str, party_size: int = 1) -> tuple[bool, str]:
        """
        [V57] 던전 입장 가능 여부 검증

        Args:
            dungeon_grade: 던전 등급 (예: 'A급', 'S급')
            hunter_rank: 헌터 등급 (예: 'B', 'A')
            party_size: 파티원 수

        Returns:
            (허용 여부, 사유)
        """
        requirements = self._dungeon_entry_requirements.get(dungeon_grade)
        if not requirements:
            return True, "등급 정보 없음 - 기본 허용"

        # 최소 등급 체크
        min_rank = requirements.get("min_rank", "E")
        if self._compare_ranks(hunter_rank, min_rank) < 0:
            return False, f"[V57] {dungeon_grade} 던전 입장 불가: 최소 {min_rank}급 필요 (현재: {hunter_rank}급)"

        # 파티 인원 체크
        min_party = requirements.get("min_party", 1)
        if party_size < min_party:
            return False, f"[V57] {dungeon_grade} 던전 입장 불가: 최소 {min_party}인 필요 (현재: {party_size}인)"

        # 특수 조건 체크
        special = requirements.get("special")
        if special:
            return True, f"[V57] {dungeon_grade} 던전 입장 가능 (특수 조건: {special})"

        return True, f"[V57] {dungeon_grade} 던전 입장 가능"

    def validate_dungeon_break(
        self, dungeon_grade: str, consecutive_count: int, rest_hours: float = 0
    ) -> tuple[bool, str]:
        """
        [V57] 던전 연속 입장 제한 검증

        Args:
            dungeon_grade: 던전 등급
            consecutive_count: 연속 입장 횟수
            rest_hours: 마지막 던전 이후 휴식 시간

        Returns:
            (허용 여부, 사유/경고)
        """
        rules = self._dungeon_break_rules.get(dungeon_grade)
        if not rules:
            return True, "규칙 없음 - 기본 허용"

        max_consecutive = rules.get("max_consecutive", 99)
        rest_required = rules.get("rest_required", 0)

        if consecutive_count > max_consecutive:
            # [Sweep47] rest_required=0이면 무조건 차단 (E/D급 연속 제한 복원)
            if rest_required == 0 or rest_hours < rest_required:
                return (
                    False,
                    f"[V57] {dungeon_grade} 던전 연속 {consecutive_count}회 입장 불가: "
                    f"최대 {max_consecutive}회 연속 가능"
                    + (f" ({rest_required}시간 휴식 필요, 현재: {rest_hours}시간)" if rest_required > 0 else ""),
                )

        return True, f"[V57] {dungeon_grade} 던전 입장 가능 (연속 {consecutive_count}회)"

    def _compare_ranks(self, rank1: str, rank2: str) -> int:
        """
        등급 비교: rank1 > rank2이면 양수, 같으면 0, 작으면 음수
        """
        r1 = rank1.upper().replace("급", "")
        r2 = rank2.upper().replace("급", "")

        # [V70] 한글 항목도 '급' 제거하여 비교 (국가급→국가, 세계급→세계)
        _normalized = [r.replace("급", "") for r in self._rank_hierarchy]
        try:
            idx1 = _normalized.index(r1)
            idx2 = _normalized.index(r2)
            return idx1 - idx2
        except ValueError:
            return 0

    # ========================================================================
    # [V57] 각성 진행 검증
    # ========================================================================

    def validate_awakening_progression(self, current_stage: str, target_stage: str) -> tuple[bool, str]:
        """
        [V57] 각성 단계 진행 검증 (스킵 불가)

        Args:
            current_stage: 현재 각성 단계
            target_stage: 목표 각성 단계

        Returns:
            (허용 여부, 사유)
        """
        try:
            current_idx = self._awakening_stages.index(current_stage)
            target_idx = self._awakening_stages.index(target_stage)
        except ValueError:
            return True, "각성 단계 정보 없음 - 기본 허용"

        # 역행 불가
        if target_idx < current_idx:
            return False, f"[V57] 각성 역행 불가: {current_stage} → {target_stage}"

        # 2단계 이상 스킵 불가
        if target_idx - current_idx > 1:
            intermediate = self._awakening_stages[current_idx + 1]
            return False, f"[V57] 각성 스킵 불가: {current_stage} → {intermediate} → {target_stage} 순서 필요"

        return True, f"[V57] 각성 진행 가능: {current_stage} → {target_stage}"

    def get_awakening_abilities(self, stage: str) -> dict[str, Any]:
        """
        [V57] 각성 단계별 능력 범위 조회
        """
        return self._awakening_abilities.get(stage, self._awakening_abilities["미각성"])

    def validate_skill_count(self, awakening_stage: str, skill_count: int) -> tuple[bool, str]:
        """
        [V57] 각성 단계별 스킬 보유 수 검증

        Args:
            awakening_stage: 각성 단계
            skill_count: 보유 스킬 수

        Returns:
            (허용 여부, 사유)
        """
        abilities = self.get_awakening_abilities(awakening_stage)
        max_skills = abilities.get("max_skills", 0)

        if max_skills == -1:  # 무제한
            return True, f"[V57] {awakening_stage}: 스킬 제한 없음"

        if skill_count > max_skills:
            return False, f"[V57] {awakening_stage}에서 최대 {max_skills}개 스킬 보유 가능 (현재: {skill_count}개)"

        return True, f"[V57] {awakening_stage}: 스킬 {skill_count}/{max_skills}개"

    # ========================================================================
    # [V57] 쿨타임 관리
    # ========================================================================

    def get_skill_cooldown(self, skill_type: str) -> int:
        """
        [V57] 스킬 유형별 기본 쿨타임 조회 (초)
        """
        return self._default_skill_cooldowns.get(skill_type, 60)

    def validate_skill_usage(
        self, skill_name: str, skill_type: str, last_used_seconds_ago: float, custom_cooldown: int = None
    ) -> tuple[bool, str]:
        """
        [V57] 스킬 쿨타임 검증

        Args:
            skill_name: 스킬명
            skill_type: 스킬 유형
            last_used_seconds_ago: 마지막 사용 후 경과 시간 (초)
            custom_cooldown: 커스텀 쿨타임 (있으면 사용)

        Returns:
            (허용 여부, 사유)
        """
        cooldown = custom_cooldown if custom_cooldown else self.get_skill_cooldown(skill_type)

        if last_used_seconds_ago < cooldown:
            remaining = cooldown - last_used_seconds_ago
            return False, f"[V57] '{skill_name}' 쿨타임 중: {remaining:.0f}초 남음"

        return True, f"[V57] '{skill_name}' 사용 가능"

    def get_dungeon_rules_prompt(self) -> str:
        """
        [V57] 던전 규칙 프롬프트 생성 (Writer/Architect 주입용)
        """
        return """
[V57 헌터물 던전 메카닉스]

1. **입장 제한**
   - E~D급 던전: 솔로 가능
   - C~B급 던전: 최소 3~4인 파티 권장
   - A급 이상: 협회 허가 + 최소 5인 이상 필수
   - S급 이상: 길드 공식 레이드 필수

2. **연속 입장 제한**
   - A급 이상 던전: 1회 클리어 후 24시간 휴식 필수
   - S급 던전: 48시간 휴식 필수
   - 무시 시: 스탯 저하, 스킬 약화, 심하면 각성 역행

3. **특수 던전**
   - 레드 게이트: 클리어 전 탈출 불가
   - 블랙 게이트: 국가급 헌터 동반 필수
   - 던전 브레이크 임박: 24시간 내 클리어 필수

4. **던전 내 규칙**
   - 포션/아이템: 제한적 사용 (인벤토리 크기)
   - 귀환석: 보스룸 이후 사용 불가
   - 통신: 던전 내 외부 연락 불가
"""

    def get_awakening_rules_prompt(self) -> str:
        """
        [V57] 각성 규칙 프롬프트 생성
        """
        stages_str = " → ".join(self._awakening_stages)
        return f"""
[V57 헌터물 각성 시스템]

1. **각성 단계**: {stages_str}

2. **단계별 제한**
   - 미각성: 스킬 0개, 시스템 창 불가
   - 초기 각성: 스킬 1개, 기본 스탯만 확인
   - 1차 각성: 스킬 3개, 스킬 레벨업 가능
   - 2차 각성: 스킬 5개, 유니크 스킬 각성 가능
   - 3차 각성: 스킬 8개, 영역 전개 가능
   - 완전 각성: 스킬 12개, 초월 능력 해금
   - 초월 각성: 제한 없음, 신화급 능력

3. **각성 진행 규칙**
   - 단계 스킵 불가 (1차 → 3차 X)
   - 각성 역행 불가 (정신적 충격으로 약화는 가능)
   - 각성 진행: 생사의 고비, 던전 클리어, 특수 이벤트

4. **각성별 행동 제약**
   - 미각성자가 스킬 사용 언급 → 즉시 REJECT
   - 초기 각성자가 영역 전개 → 즉시 REJECT
   - 각성 단계에 맞지 않는 스킬 수 → WARNING
"""

    # ========================================================================
    # [V66] run_deep_validation override
    # ========================================================================

    def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]:
        """[V66] Hunter 심층 검증: base + 던전 진입 + 각성 순서 + 랭크 스킵 감지."""
        import re

        result = super().run_deep_validation(manuscript, current_state or {})

        # 던전 진입 검증
        dungeon_patterns = re.findall(r"(\w+)\s*(?:등급|랭크|급)\s*던전", manuscript)
        hunter_rank = str((current_state or {}).get("realm", "E"))
        for dungeon_rank in dungeon_patterns:
            valid, msg = self.validate_dungeon_entry(
                f"{dungeon_rank}급", hunter_rank
            )  # [V70] "S" → "S급" (dict 키 매칭)
            if not valid:
                result["violations"].append({"type": "dungeon_entry", "severity": "HIGH", "message": msg})

        # 각성 순서 검증 (단계 스킵 감지)
        awakening_patterns = re.findall(r"(\d)차\s*각성", manuscript)
        for stage_str in awakening_patterns:
            try:
                stage = int(stage_str)
                if stage >= 3:
                    # 현재 상태에서 1-2차가 이미 완료됐는지 체크 불가 → WARNING 등급
                    result["violations"].append(
                        {
                            "type": "awakening_skip_risk",
                            "severity": "MEDIUM",
                            "message": f"{stage}차 각성 언급 — 이전 단계 완료 여부 확인 필요",
                        }
                    )
            except ValueError:
                pass

        # 스킬 개수 제한 (미각성 → 0, 초기 → 3, ...)
        skill_mentions = re.findall(r"스킬\s*[:\-]?\s*([가-힣]+)", manuscript)
        if skill_mentions and not (current_state or {}).get("realm"):
            result["violations"].append(
                {
                    "type": "skill_without_awakening",
                    "severity": "MEDIUM",
                    "message": f"각성 전 스킬 언급 ({len(skill_mentions)}건)",
                }
            )

        result["has_critical"] = any(v.get("severity") in ("HIGH", "CRITICAL") for v in result["violations"])
        if result["violations"]:
            result["summary"] = "; ".join(v.get("message", "") for v in result["violations"][:5])
            result["feedback"] = f"[헌터 Guard] {len(result['violations'])}건: {result['summary']}"
        return result
