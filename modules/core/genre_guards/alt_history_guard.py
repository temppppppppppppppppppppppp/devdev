"""
[V61.9] 대체역사물(조선) 전용 Guard
[V57] 완전 구현 - 일관성 검증, 권위 위계, 타임라인 검증
조선 시대 시대고증과 정치적 개연성을 유지
"""

from typing import Any

from .base_guard import BaseGuard


class AltHistoryGuard(BaseGuard):
    """[대체역사물] 조선 시대 시대고증 + 궁중 정치 전문성 보호자 + V57 완전 구현"""

    def __init__(self) -> None:
        super().__init__()
        cfg = self._load_genre_yaml("alt_history")

        self.FORBIDDEN_TERMS = cfg.get(
            "forbidden_terms",
            [
                "스마트폰",
                "컴퓨터",
                "인터넷",
                "노트북",
                "태블릿",
                "모니터",
                "이메일",
                "SNS",
                "앱",
                "어플",
                "블로그",
                "유튜브",
                "네이버",
                "와이파이",
                "블루투스",
                "USB",
                "프린터",
                "AI",
                "인공지능",
                "자동차",
                "버스",
                "지하철",
                "비행기",
                "오토바이",
                "택시",
                "엘리베이터",
                "카페",
                "편의점",
                "백화점",
                "마트",
                "병원",
                "아파트",
                "영화관",
                "놀이공원",
                "체육관",
                "플라스틱",
                "비닐",
                "나일론",
                "폴리에스터",
                "스티로폼",
                "마나",
                "스킬",
                "던전",
                "게이트",
                "각성",
                "레벨업",
                "경험치",
                "상태창",
                "시스템 창",
                "퀘스트",
                "인벤토리",
                "내공",
                "진기",
                "검기",
                "검강",
                "초식",
                "무림",
                "강호",
            ],
        )

        self.JOSEON_TERMS = cfg.get(
            "joseon_terms",
            [
                "영의정",
                "좌의정",
                "우의정",
                "판서",
                "참판",
                "참의",
                "이조",
                "호조",
                "예조",
                "병조",
                "형조",
                "공조",
                "승정원",
                "의금부",
                "사헌부",
                "사간원",
                "홍문관",
                "암행어사",
                "목사",
                "부사",
                "군수",
                "현감",
                "노론",
                "소론",
                "남인",
                "북인",
                "시파",
                "벽파",
                "양반",
                "중인",
                "상민",
                "천민",
                "사대부",
                "서얼",
                "과거",
                "문과",
                "무과",
                "잡과",
                "생원",
                "진사",
                "급제",
                "장원",
                "삼강오륜",
                "충효",
                "예법",
                "존비",
                "항렬",
                "한양",
                "성균관",
                "사직",
                "종묘",
                "경복궁",
                "창덕궁",
            ],
        )

        self.MANDATORY_CONCEPTS = cfg.get(
            "mandatory_concepts",
            [
                "유교적 세계관과 예법·존비의 준수",
                "왕권과 신권(신하)의 역학 관계",
                "당쟁의 논리와 정치적 명분",
                "시대적 한계와 기술 도입의 개연성",
            ],
        )

        self._court_rank_hierarchy = cfg.get(
            "court_rank_hierarchy",
            [
                "종9품",
                "정9품",
                "종8품",
                "정8품",
                "종7품",
                "정7품",
                "종6품",
                "정6품",
                "종5품",
                "정5품",
                "종4품",
                "정4품",
                "종3품",
                "정3품",
                "종2품",
                "정2품",
                "종1품",
                "정1품",
            ],
        )

        self._social_hierarchy = cfg.get("social_hierarchy", ["천민", "상민", "중인", "양반", "왕족"])

        self._class_action_limits = cfg.get(
            "class_action_limits",
            {
                "천민": [r"과거.*응시", r"관직.*임명", r"조정.*참석", r"상소.*올"],
                "상민": [r"조정.*참석", r"왕.*알현", r"양반.*행세"],
                "중인": [r"문과.*급제", r"정승.*임명", r"종묘.*제사"],
            },
        )

        self._rank_action_limits = cfg.get(
            "rank_action_limits",
            {
                "무품": [r"조정.*발언", r"상소.*올", r"왕명.*전달", r"관군.*지휘"],
                "종9품": [r"왕.*독대", r"대신.*탄핵", r"군병.*동원"],
                "정7품": [r"왕.*독대", r"대규모.*군병"],
            },
        )

        self._status_action_limits = cfg.get(
            "status_action_limits",
            {
                "유배": [r"한양.*귀환", r"관직.*복귀", r"조정.*참석", r"왕.*알현"],
                "투옥": [r"자유.*행동", r"외부.*연락", r"관직.*수행"],
                "파직": [r"관직.*수행", r"조정.*참석", r"왕명.*전달"],
                "상중": [r"관직.*수행", r"연회.*참석", r"혼인", r"과거.*응시"],
            },
        )

        self._activity_requirements = {
            "과거 급제": {"social_class": "양반", "status": "active"},
            "관직 임명": {"social_class": "양반", "examination": True},
            "상소문 제출": {"position": True, "social_class": "양반"},
            "왕 독대": {"court_rank": "정3품", "position": True},
            "군사 동원": {"court_rank": "종2품", "military_authority": True},
            "외교 사절": {"court_rank": "정3품", "royal_mandate": True},
        }

    def get_genre_name(self) -> str:
        return "대체역사물(ALT_HISTORY)"

    def _should_check_english(self) -> bool:
        """대체역사물은 사극 배경이므로 영어 엄격 제한"""
        return True

    def _should_check_numbers(self) -> bool:
        """대체역사물은 아라비아 숫자보다 한자 수 표현 권장"""
        return True

    def get_v20_purism_prompt(self) -> str:
        """대체역사물 장르 전문성 지침"""
        return f"""
[📜 V61.9 대체역사물(조선) 장르 가이드라인 (Alt History Genre Authenticity)]

1. **시대 교란 금지**: 근현대 문물({", ".join(self.FORBIDDEN_TERMS[:8])} 등)을 사용하지 마라. 조선 시대 세계관을 유지하라.
2. **유교적 세계관**: 삼강오륜, 충효, 예법, 존비의 질서가 기본이다. 현대적 평등 개념을 당연시하지 마라.
3. **관직 체계 준수**: {", ".join(self.JOSEON_TERMS[:6])} 등 실제 조선 관직 체계를 정확히 사용하라.
4. **당쟁의 논리**: 노론/소론/남인/북인 등 당파간 대립은 단순 선악이 아닌 정치적 명분과 논리에 기반해야 한다.
5. **신분 제도**: 양반/중인/상민/천민의 사회적 제약을 사실적으로 반영하라. 신분 초월은 반드시 개연성 있는 근거가 필요하다.
6. **문체**: 사극에 어울리는 고풍스런 문체를 사용하되, 과도한 한문투는 지양하라. 대화는 ~하오, ~하시오, ~이옵니다 체를 적절히 활용하라.
7. **기술 도입**: 회귀자/빙의자가 현대 지식을 활용할 경우, 조선 시대 기술 수준에서 구현 가능한 범위를 지켜라. 점진적 도입과 저항을 묘사하라.
8. **역사적 사건**: 실제 조선사 사건을 활용하되, '대체역사'로서 변형할 때는 나비효과와 파급을 논리적으로 추적하라.
9. **필수 표현 요소**: {", ".join(self.MANDATORY_CONCEPTS)}
10. **전문가 반응 캘리브레이션**: 관료/학자의 반응은 품계·경험에 비례해야 한다. 정승급이 지방 수령의 상소에 동요하면 안 된다(일상). 반정 모의나 외적 침입에는 긴장해야 한다(실제 국가적 위기). 권력자는 자기 위계 내 일상적 정치 공방에 침착하고, 판도를 뒤흔드는 사건에만 반응한다.

[개연성 체크리스트]
- 주인공의 신분과 행동이 조선 사회 규범에 부합하는가?
- 관직 임명/승진에 합당한 근거(과거 급제, 공적, 인맥)가 있는가?
- 당파 간 대립에 정치적 명분과 논리가 있는가?
- 현대 지식 활용 시 시대적 제약과 저항이 묘사되는가?
"""

    # ========================================================================
    # [V57] 일관성 검증 구현 (대체역사물 특화)
    # ========================================================================

    def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]:
        """[V57] 대체역사물 - 현재 상태에서 불가능한 행동 패턴 반환"""
        actions = []

        # 1. 상태 기반 제한 (유배, 투옥, 파직 등)
        status = current_state.get("status", current_state.get("condition", ""))
        if isinstance(status, str):
            for status_keyword, patterns in self._status_action_limits.items():
                if status_keyword in status:
                    for pattern in patterns:
                        actions.append(
                            {"pattern": pattern, "reason": f"상태 '{status_keyword}'로 인해 불가", "severity": "HIGH"}
                        )

        # 2. 신분 기반 제한
        social_class = current_state.get("social_class", "양반")
        if isinstance(social_class, str):
            for class_name, patterns in self._class_action_limits.items():
                if class_name in social_class:
                    for pattern in patterns:
                        actions.append(
                            {"pattern": pattern, "reason": f"신분 '{class_name}'에서 불가", "severity": "HIGH"}
                        )

        # 3. 관직 등급 기반 제한
        court_rank = current_state.get("court_rank", "무품")
        if isinstance(court_rank, str) and court_rank in self._rank_action_limits:
            for pattern in self._rank_action_limits[court_rank]:
                actions.append({"pattern": pattern, "reason": f"품계 '{court_rank}'에서 불가", "severity": "HIGH"})

        # 4. 회귀자 미래 정보 제한
        is_regressor = current_state.get("is_regressor", False)
        if is_regressor:
            actions.append(
                {
                    "pattern": r"조선.*없는.*기술|불가능.*발명",
                    "reason": "조선 시대 구현 불가능한 기술 직접 사용",
                    "severity": "CRITICAL",
                }
            )

        return actions

    def get_justification_patterns(self) -> list[str]:
        """[V57] 대체역사물 - 정당화로 인정되는 표현 패턴"""
        return [
            # 미래 정보 활용 (회귀물)
            r"미래.*기억",
            r"전생.*경험",
            r"과거.*지식",
            # 정당한 승진/임명
            r"과거.*급제",
            r"공적.*인정",
            r"왕명.*임명",
            r"천거.*받",
            r"상소.*공로",
            # 신분 초월 근거
            r"왕.*특명",
            r"공신.*책봉",
            r"서얼.*허통",
            r"면천.*허락",
            r"양인.*등록",
            # 기술 도입 근거
            r"서양.*문물",
            r"청.*통해",
            r"역관.*소개",
            r"실학.*연구",
            r"오랜.*실험",
            # 정치적 명분
            r"상소.*근거",
            r"경연.*논의",
            r"선례.*따라",
            r"대의.*명분",
            r"유교.*가르침",
        ]

    def get_hierarchy_rules(self) -> dict[str, Any]:
        """[V57] 대체역사물 - 신분/관직 위계 규칙"""
        return {
            "social_classes": self._social_hierarchy,
            "court_ranks": self._court_rank_hierarchy,
            "titles": {
                "천민": ["노비", "백정", "광대", "무녀"],
                "상민": ["농부", "어부", "장인", "상인"],
                "중인": ["역관", "의관", "산원", "화원", "서리"],
                "양반": ["선비", "유생", "사대부", "관원"],
                "왕족": ["왕세자", "대군", "군", "공주", "옹주"],
            },
            "violations": {
                "천민": [r"과거.*응시", r"양반.*행세", r"관직"],
                "상민": [r"조정.*발언", r"왕.*알현"],
                "중인": [r"문과.*급제", r"정승"],
            },
        }

    def get_technique_effect_rules(self) -> dict[str, dict[str, Any]]:
        """[V57] 대체역사물 - 정치 활동별 효능 규칙"""
        return {
            "상소": {
                "effect_type": "political",
                "effect_scope": ["여론 형성", "탄핵", "정책 변경"],
                "cannot_be_used_for": ["즉각적 관직 획득", "왕 폐위"],
                "risk": "역풍 시 파직/유배",
            },
            "과거 급제": {
                "effect_type": "career",
                "effect_scope": ["관직 임명", "명성", "인맥 확대"],
                "cannot_be_used_for": ["즉시 고위직"],
                "requirements": ["양반 신분", "학문 실력"],
            },
            "기술 도입": {
                "effect_type": "innovation",
                "effect_scope": ["부 축적", "군사력", "민심"],
                "cannot_be_used_for": ["즉각적 산업혁명"],
                "requirements": ["자금", "장인", "왕/권력자 후원"],
            },
            "외교": {
                "effect_type": "diplomatic",
                "effect_scope": ["무역", "군사 동맹", "문물 교류"],
                "cannot_be_used_for": ["내정 직접 변경"],
                "requirements": ["관직", "왕명", "외국어 능력"],
            },
            "군사 행동": {
                "effect_type": "military",
                "effect_scope": ["영토 방어", "반란 진압", "세력 확장"],
                "cannot_be_used_for": ["평시 민간 탄압"],
                "requirements": ["군권", "병력", "명분"],
            },
        }

    # ========================================================================
    # [V57] 권위 위계 검증 (대체역사물 특화)
    # ========================================================================

    def get_authority_hierarchy(self) -> dict[str, Any]:
        """[V57] 대체역사물 - 조선 조정 권위 위계"""
        return {
            "positions": ["왕", "영의정", "좌의정", "우의정", "판서", "참판", "참의", "정랑", "좌랑"],
            "position_titles": {
                "왕": ["전하", "주상", "상감", "임금"],
                "영의정": ["영상", "수상"],
                "좌의정": ["좌상"],
                "우의정": ["우상"],
                "판서": ["판서", "대감"],
                "참판": ["참판"],
                "참의": ["참의"],
            },
            "authority_scope": {
                "왕": ["인사", "군사", "외교", "사법", "입법"],
                "영의정": ["국정 총괄", "인사 추천", "정책 조율"],
                "판서": ["해당 조(部) 관할", "소속 관원 인사"],
                "암행어사": ["지방관 감찰", "즉결 처분", "파직 건의"],
            },
        }

    def get_delegation_patterns(self) -> list[str]:
        """[V57] 대체역사물 - 권위 위임 정당화 패턴"""
        return [
            r"왕명.*따라",
            r"어명.*받들어",
            r"비변사.*결정",
            r"의정부.*의결",
            r"영의정.*지시",
            r"판서.*명",
            r"교지.*내려",
            r"밀지.*받고",
        ]

    # ========================================================================
    # [V57] 갈등 및 해소 검증
    # ========================================================================

    def get_hostile_action_types(self) -> list[str]:
        """[V57] 대체역사물 - 적대적 행동 유형"""
        return [
            "탄핵 상소",
            "무고",
            "모반 고변",
            "역모 누명",
            "파직",
            "유배",
            "국문",
            "장형",
            "암살 시도",
            "독살",
            "매복",
            "습격",
            "당론 공격",
            "학맥 배척",
            "서얼 차별",
            "민란 선동",
            "외세 결탁",
        ]

    def get_resolution_patterns(self) -> list[str]:
        """[V57] 대체역사물 - 갈등 해소 패턴"""
        return [
            # 정치적 승리
            r"왕.*편",
            r"탄핵.*성공",
            r"복권",
            r"사면",
            r"관직.*복귀",
            r"공신.*책봉",
            # 명분 승리
            r"상소.*관철",
            r"경연.*설득",
            r"여론.*전환",
            r"민심.*얻",
            r"유생.*지지",
            # 실력 증명
            r"과거.*장원",
            r"외교.*성공",
            r"전쟁.*승리",
            r"기술.*성공",
            r"민생.*안정",
            # 타협/화해
            r"화해",
            r"연립",
            r"타협",
            r"혼인.*동맹",
            r"당론.*조율",
            r"상호.*양보",
        ]

    # ========================================================================
    # [V66] 심층 검증 오버라이드
    # ========================================================================

    def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]:
        """[V66] 대체역사물 심층 검증."""
        result = super().run_deep_validation(manuscript, current_state or {})

        # [V70] get_impossible_actions 중복 제거 (super()가 이미 check_state_action_consistency에서 호출)

        result["has_critical"] = any(v.get("severity") in ("HIGH", "CRITICAL") for v in result["violations"])
        if result["violations"]:
            result["summary"] = "; ".join(v.get("message", "") for v in result["violations"][:5])
            result["feedback"] = f"[대체역사물 Guard] {len(result['violations'])}건: {result['summary']}"
        return result
