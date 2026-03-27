"""
[V40 Multi-Genre] 무협 전용 Purism Guard
[V46] 일관성 검증 규칙 추가 - 상태 vs 행동, 정당화 패턴, 직위 위계
[V46.1] 권위 위임, 미해결 갈등(고구마), 빌런 반응 검증 추가
무협의 순혈성을 보존하고 현대어/게임 용어를 차단
"""
# utf8-hygiene: allow-file -- legitimate Hangul/Hanja wuxia literals and regex ? tokens are part of the guard contract.

from typing import Any

from .base_guard import BaseGuard


class WuxiaGuard(BaseGuard):
    """[무협] 순혈주의 파수꾼 + V46 일관성 검증"""

    def __init__(self) -> None:
        super().__init__()
        cfg = self._load_genre_yaml("wuxia")

        self._init_forbidden_terms(cfg)

        self._init_mandatory_concepts(cfg)
        self._init_realm_constraints(cfg)

        self._init_injury_action_limits(cfg)
        self._init_forbidden_modern_patterns(cfg)

    def _init_forbidden_terms(self, cfg: dict[str, Any]) -> None:
        # 무협 금기어 목록 (YAML 우선, 없으면 하드코딩 폴백)
        self.FORBIDDEN_TERMS = cfg.get(
            "forbidden_terms",
            [
                "상태창",
                "시스템",
                "로그",
                "퀘스트",
                "스킬",
                "마나",
                "서클",
                "스테이터스",
                "레벨업",
                "경험치",
                "아이템 파밍",
                "레이드",
                "던전",
                "포션",
                "귀환 주문서",
                "데이터",
                "바이러스",
                "현대적 비속어",
                "영어 직역투",
                "MARTIAL HUD",
                "스마트폰",
                "모세의 기적",
                "분자",
                "원자",
                "세포",
                "DNA",
                "유전자",
                "물리학",
                "화학",
                "중력",
                "가속도",
                "산소",
                "탄소",
                "미생물",
                "트라우마",
                "스트레스",
                "메커니즘",
                "프로세스",
                "인터페이스",
                "에너지",
                "벡터",
                "중력장",
                "운동 에너지",
                "진공",
                "시멘트",
                "저작권",
                "저작권 침해",
                "입자",
                "포탄",
                "쓰나미",
                "물류",
                "비자금",
                "투자",
                "청구서",
                "질량",
                "엔진",
                "계산기",
                "펌프질",
                "전송",
                "임계점",
                "폼",
                "헌터",
                "각성",
                "게이트",
                "길드",
                "펌핑",
                "펌핑감",
                "쇠질",
                "헬스",
                "헬스장",
                "운동기구",
                "덤벨",
                "바벨",
                "스쿼트",
                "데드리프트",
                "벤치프레스",
                "프로틴",
                "보충제",
                "유산소",
                "무산소",
                "근비대",
                "벌크업",
                "컷팅",
                "루틴",
                "킬로그램",
                "킬로미터",
                "센티미터",
                "밀리미터",
                "소프트웨어",
                "하드웨어",
                "프로그램",
                "코드",
                "알고리즘",
                "버그",
                "디버깅",
                "아카데미",
                "메소드",
                "연기",
                "오스카",
                "에미상",
                "감독상",
                "주연상",
                "쇼크",
                "쇼크사",
                "회전근개",
                "인대",
                "연골",
                "디스크",
                "근섬유",
                "관절염",
                "아드레날린",
                "도파민",
                "세로토닌",
                "호르몬",
                "항체",
                "면역",
                "사브르",
                "레이피어",
                "에페",
                "플뢰레",
                "머스킷",
                "라이플",
                "현대의 기억",
                "전생의 현대",
                "지구의",
                "21세기",
                "20세기",
                "화학 반응",
                "근육세포",
                "근섬유",
            ],
        )

    def _init_mandatory_concepts(self, cfg: dict[str, Any]) -> None:
        # 무협 필수 개념
        self.MANDATORY_CONCEPTS = cfg.get(
            "mandatory_concepts",
            ["진기(眞氣)와 내공의 운용", "초식(招式)의 형상화", "강호의 은원(恩怨)", "항렬과 예법"],
        )

    def _init_realm_constraints(self, cfg: dict[str, Any]) -> None:
        # [V46] 무협 경지 위계 (낮음 → 높음)
        self._realm_hierarchy = cfg.get(
            "realm_hierarchy", ["입문", "삼류", "이류", "일류", "절정", "초절정", "화경", "현경", "귀신", "선천"]
        )

        # [V46] 경지별 불가능 무공 패턴
        self._realm_technique_limits = cfg.get(
            "realm_technique_limits",
            {
                "입문": ["검기", "검강", "이기어검", "비검", "장력", "경공"],
                "삼류": ["검강", "이기어검", "비검", "강기", "투경"],
                "이류": ["검강", "이기어검", "비검", "투경"],
                "일류": ["이기어검", "비검", "투경"],
                "절정": ["투경"],
                "초절정": [],
                "화경": [],
                "현경": [],
            },
        )

    def _init_injury_action_limits(self, cfg: dict[str, Any]) -> None:
        # [V46] 부상 상태별 불가능 행동
        self._injury_action_limits = cfg.get(
            "injury_action_limits",
            {
                "중상": [r"\d{2,}근.*들", r"전력.*질주", r"경공.*전개", r"내공.*폭발"],
                "나약": [r"\d{2,}근.*들", r"질주", r"도약", r"경공"],
                "기력 저하": [r"내공.*운용", r"진기.*순환", r"장력", r"검기"],
                "단전 손상": [r"내공", r"진기", r"단전", r"기해"],
            },
        )

    def _init_forbidden_modern_patterns(self, cfg: dict[str, Any]) -> None:
        # [V49.5] 괄호 현대어 금지 패턴
        _raw_modern = cfg.get("forbidden_modern_patterns", None)
        if _raw_modern and isinstance(_raw_modern, list) and isinstance(_raw_modern[0], dict):
            self.FORBIDDEN_MODERN_PATTERNS = [(p["pattern"], p["reason"]) for p in _raw_modern]
        else:
            self.FORBIDDEN_MODERN_PATTERNS = [
                (r"\(\s*약?\s*\d+\.?\d*\s*%\s*\)", "퍼센트 표기 금지"),
                (r"\d+\.?\d*\s*%", "퍼센트 기호 금지"),
                (r"\(\s*약?\s*\d+\.?\d*\s*(km|m|cm|mm|kg|g|mg)\s*\)", "현대 단위 금지"),
                (r"\(\s*약?\s*\d+\.?\d*\s*(킬로미터|미터|센티미터|킬로그램|그램)\s*\)", "현대 단위 금지"),
                (r"\d+\.?\d*\s*kg(?![가-힣])", "현대 단위(kg) 금지 - 근(斤) 사용"),
                (r"\d+\.?\d*\s*cm(?![가-힣])", "현대 단위(cm) 금지 - 촌(寸) 사용"),
                (r"\d+\.?\d*\s*m(?![가-힣km])", "현대 단위(m) 금지 - 장(丈)/척(尺) 사용"),
                (r"\d+\.?\d*\s*km(?![가-힣])", "현대 단위(km) 금지 - 리(里) 사용"),
                (r"[일이삼사오육칠팔구십백천만]+\s*킬로그램", "한글 현대 단위(킬로그램) 금지 - 근(斤) 사용"),
                (r"[일이삼사오육칠팔구십백천만]+\s*킬로미터", "한글 현대 단위(킬로미터) 금지 - 리(里) 사용"),
                (r"[일이삼사오육칠팔구십백천만]+\s*센티미터", "한글 현대 단위(센티미터) 금지 - 촌(寸) 사용"),
                (r"[일이삼사오육칠팔구십백천만]+\s*미터(?!법)", "한글 현대 단위(미터) 금지 - 장(丈)/척(尺) 사용"),
                (r"\(\s*약?\s*\d+\s*(시간|분|초)\s*\)", "현대 시간 단위 금지"),
                (r"\(\s*[A-Za-z]{2,}\s*\)", "영어 주석 금지"),
                (r"\(\s*(즉|다시 말해|쉽게 말해|예를 들어)\s*[,\s]", "현대식 부연 설명 금지"),
                (r"현대의\s*기억", "현대인 빙의 표현 금지 - 전생의 기억 사용"),
                (r"전생[,\s]*현대", "현대인 빙의 표현 금지"),
            ]

    def get_genre_name(self) -> str:
        return "무협(WUXIA)"

    def get_v20_purism_prompt(self) -> str:
        """무협 순혈주의 지침 프롬프트"""
        return f"""
[🛡️ V40 무협 순혈주의 절대 준수 (Wuxia Purism Enforcement)]

1. **괄호 현대어 주석 절대 금지**: 다음 패턴은 즉시 REJECT 대상이다:
   - 퍼센트/비율: (30%), (약 50%), 30% 등 → 대신 '삼할(三割)', '절반', '태반' 사용
   - 현대 단위: (10km), (약 5m), (100kg), 60kg 등 → 대신 '십 리(十里)', '오 장(五丈)', '백 근(百斤)' 사용
   - 시간 환산: (약 3시간), (30분) 등 → 대신 '한 시진(一時辰)', '일각(一刻)', '한 식경(一食頃)' 사용
   - 영어/외래어 주석: (Anchor), (즉, ~), (다시 말해) 등 완전 금지
   - 허용되는 괄호: 한자 표기용만 허용 (예: 철혈사자패(鐵血獅子牌))
2. **과학/현대 용어 절대 금지**: 현대 과학/물리 지식을 무협적 개념으로 '번역'하여 서술하라.
   - 분자/원자/세포/질량 → 미진(微塵), 근원(根源), 기(氣)의 입자, 무게
   - 중력/압력/에너지 → 천근추(千斤墜), 태산 같은 기세, 공압(空壓), 기운
   - 투자/물류/비자금 → 밑천, 보급/운송, 사재(私財)/뒷돈
3. **게임 시스템 용어 금지**: {", ".join(self.FORBIDDEN_TERMS[:10])} 등 상태창류 단어를 쓰면 즉시 파기한다.
4. **수치 표기**: 모든 숫자(거리, 무게, 인원, 날짜 등)는 반드시 '한글'로만 표기하라. (예: 100근 X -> 일백 근 O)
5. **언어 순혈주의**: 영어, 외래어, 현대적 비속어는 금지한다. 오직 정통 무협의 어휘만 허용한다.
6. **[V60.85] 현대 생활 용어 금지 (현대인 빙의자 착각 방지)**:
   - 체육관/헬스 용어: 펌핑, 펌핑감, 쇠질, 헬스, 덤벨, 바벨, 프로틴, 루틴 등 절대 금지
   - 현대 감각 비유: "헬스장에서 느끼는 그 감각", "운동 후 펌핑감" 등 금지
   - 회귀자/빙의자라도 무협 세계관 내 표현만 사용: 근육의 팽창 → "근육이 철처럼 부풀어 오르다", "힘줄이 살아 꿈틀거리다"
7. **[V60.86] IT/의학/외래어 금지 (원고 스캔 기반)**:
   - IT 용어: 소프트웨어, 프로그램, 알고리즘 등 금지 → "두뇌", "운용하는 방식", "계책"
   - 영화/엔터 용어: 아카데미, 메소드 연기 등 금지 → "백무무대의 명창", "천의무봉의 가식"
   - 의학 현대어: 회전근개, 쇼크, 아드레날린 등 금지 → "어깨 근육", "기절", "피가 끓어오르다"
   - 외래어 무기: 사브르, 레이피어 등 금지 → "곡도(曲刀)", "세검(細劍)"
   - 회귀 표현: "현대의 기억", "전생, 현대" 금지 → "전생의 기억", "과거의 기억"
   - 화학/생물 용어: 화학 반응, 근섬유, 근육세포 금지 → "기운의 흐름", "근육 가닥", "살점"
7. **필수 묘사 요소**: {", ".join(self.MANDATORY_CONCEPTS)}
8. **고수 반응 캘리브레이션**: 무인의 반응은 경지·경험에 비례해야 한다. 화경 고수가 삼류 자객 습격에 놀라면 안 된다(일상). 천하오절급의 내습이나 전대미문의 마공에는 긴장해야 한다(실제 위협). 고수는 경지 이하의 위협에 여유 있고, 동급 이상의 존재에만 반응한다.
9. **[V60.87] 허용 예외 패턴 (Justification Patterns)**: 아래 상황에서는 일반적으로 불가능한 동작이 서사적으로 허용될 수 있다:
   - 내공/진기 활용 (내공으로 이용, 진기를 끌어모아)
   - 극한 상황 돌파 (죽기 살기, 한계를 넘어, 대가를 치르, 반동을 감수, 수명을 깎아, 생사의 경계)
   - 외부 도움 (영약 복용, 단약 효과, 비급을 깨달아)
   - 잠재력 폭발 (잠재력 폭발, 혈맥을 뚫어, 기연을 얻어)
   - 의지력 (정신력으로 버텨, 의지로 일으켜, 이를 악물어)
   해당 패턴이 서사에 명확히 제시된 경우에만 허용된다. 패턴 없이 한계를 초월하면 REJECT 대상이다.
"""

    # ========================================================================
    # [V46] 일관성 검증 구현 (무협 특화)
    # ========================================================================

    def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]:
        """
        [V46] 무협 - 현재 상태에서 불가능한 행동 패턴 반환

        동적 규칙 생성: HUD의 injuries, realm, internal_energy에서 추론
        """
        actions = []

        # 1. 부상 상태 기반 제한
        injuries = current_state.get("causal_injuries", "")
        if isinstance(injuries, str):
            for injury_keyword, patterns in self._injury_action_limits.items():
                if injury_keyword in injuries:
                    for pattern in patterns:
                        actions.append(
                            {
                                "pattern": pattern,
                                "reason": f"부상 상태 '{injury_keyword}'로 인해 불가",
                                "severity": "HIGH",
                            }
                        )

        # 2. 경지 기반 기술 제한
        realm = current_state.get("realm", "")
        if realm and realm in self._realm_technique_limits:
            forbidden_techniques = self._realm_technique_limits[realm]
            for technique in forbidden_techniques:
                actions.append(
                    {"pattern": technique, "reason": f"경지 '{realm}'에서 '{technique}' 사용 불가", "severity": "HIGH"}
                )

        # 3. 내공 고갈 상태
        internal_energy = current_state.get("internal_energy", 100)
        if isinstance(internal_energy, int | float) and internal_energy <= 10:
            actions.append(
                {
                    "pattern": r"내공.*끌어|진기.*운용|기해.*열어",
                    "reason": "내공 고갈 상태에서 내공 운용 불가",
                    "severity": "MEDIUM",
                }
            )

        # 4. 나약한 육체 + 중량물 들기
        body_state = current_state.get("body_condition", "")
        if "나약" in str(body_state) or "허약" in str(body_state):
            actions.append(
                {
                    "pattern": r"[일이삼사오육칠팔구십백천]?[십백]?\s*근.*들|무거운.*들어올",
                    "reason": "나약한 육체로 중량물 들기 불가",
                    "severity": "MEDIUM",
                }
            )

        return actions

    def get_justification_patterns(self) -> list[str]:
        """
        [V46] 무협 - 정당화로 인정되는 표현 패턴

        "내공 기교로 분산", "죽기 살기로" 등의 패턴이 있으면
        불가능해 보이는 행동도 허용
        """
        return [
            # 내공/진기 활용
            r"내공.*이용",
            r"내공.*끌어.*모아",
            r"진기.*끌어",
            r"기교.*분산",
            r"진기.*한 곳.*모아",
            # 극한 상황 돌파
            r"죽기.*살기",
            r"한계.*넘어",
            r"대가.*치르",
            r"반동.*감수",
            r"수명.*깎",
            r"생사.*경계",
            # 외부 도움
            r"영약.*복용",
            r"단약.*효과",
            r"비급.*깨달",
            # 잠재력 폭발
            r"잠재력.*폭발",
            r"혈맥.*뚫",
            r"기연.*얻",
            # 의지력
            r"정신력.*버텨",
            r"의지.*일으켜",
            r"이를.*악물",
        ]

    def get_hierarchy_rules(self) -> dict[str, Any]:
        """
        [V46] 무협 - 직위/호칭 위계 규칙

        경지에 따른 자칭/타칭 규칙
        """
        return {
            "ranks": self._realm_hierarchy,
            "titles": {
                "입문": ["소생", "재하"],
                "삼류": ["소생", "재하", "소협"],
                "이류": ["소협", "재하"],
                "일류": ["소협", "재하", "본인"],
                "절정": ["본좌", "본인", "소협", "대협"],
                "초절정": ["본좌", "본인", "대협"],
                "화경": ["본좌", "노부", "대협"],
                "현경": ["본좌", "노부", "선배"],
            },
            "address_rules": {
                "junior_to_senior": ["선배님", "대협", "전배", "사숙", "사조"],
                "senior_to_junior": ["소협", "후배", "젊은이"],
                "peer": ["형제", "도우", "벗"],
            },
            # 강호 위계 위반 패턴
            "violations": {
                "입문": [r"본좌", r"노부", r"대협이라 불려"],  # 입문자가 쓸 수 없는 호칭
                "삼류": [r"본좌", r"노부"],
                "이류": [r"본좌", r"노부"],
                "일류": [r"노부"],
            },
        }

    def get_technique_effect_rules(self) -> dict[str, dict[str, Any]]:
        """
        [V46] 무협 - 기술/아이템 효능 규칙

        특정 기술이나 아이템의 정의된 효능과 사용 방식
        """
        return {
            # 무공 효능
            "파천신장": {
                "effect_type": "destructive",
                "effect_scope": ["외부", "물리"],
                "cannot_be_used_for": ["치료", "방어", "은신"],
            },
            "금강불괴": {
                "effect_type": "defensive",
                "effect_scope": ["자신", "육체"],
                "cannot_be_used_for": ["공격", "원거리"],
            },
            "경공": {
                "effect_type": "movement",
                "effect_scope": ["자신", "이동"],
                "cannot_be_used_for": ["공격", "치료", "방어"],
            },
            # 아이템 효능
            "독약": {
                "effect_type": "debuff",
                "effect_scope": ["타인", "내상"],
                "cannot_be_used_for": ["치료", "버프", "자신"],
                "transformation_allowed": False,
            },
            "해독단": {
                "effect_type": "healing",
                "effect_scope": ["자신", "해독"],
                "cannot_be_used_for": ["공격", "독 강화"],
                "transformation_allowed": False,
            },
        }

    # ========================================================================
    # [V46.1] 권위 위임 검증 (무협 특화)
    # ========================================================================

    def get_authority_hierarchy(self) -> dict[str, Any]:
        """
        [V46.1] 무협 - 가문/문파 권위 위계

        가주 > 대장로 > 장로 > 직계 > 방계 순
        """
        return {
            "positions": ["가주", "문주", "대장로", "장로", "직계", "방계", "외인"],  # 높은 순
            "position_titles": {
                "가주": ["가주", "문주", "방주", "총관"],
                "가주대행": ["대행", "권한대행", "가주 대행", "문주 대행"],
                "대장로": ["대장로", "태상장로", "원로"],
                "장로": ["장로", "호법"],
                "직계": ["도련님", "아가씨", "공자", "소저"],
                "방계": ["소협", "공자"],
            },
            "delegation_required": ["가주대행", "대행", "권한대행"],  # 명분 필요
            # 직위별 권한
            "authority_scope": {
                "가주": ["처단", "제명", "임명", "재산처분"],
                "대장로": ["징계", "임시처분"],
                "장로": ["훈계", "보고"],
                "직계": ["명령(하인)", "요청"],
                "방계": ["요청"],
            },
        }

    def get_delegation_patterns(self) -> list[str]:
        """
        [V46.1] 무협 - 권위 위임 정당화 패턴

        "가주의 명으로", "철혈사자패를 지닌" 등
        """
        return [
            # 직접 위임
            r"의 명으로",
            r"께서 위임",
            r"의 뜻을 받들어",
            r"의 허락으로",
            r"가 명하셨",
            # 증표/신물
            r"사자패.*지닌",
            r"영패.*보이",
            r"가주.*직인",
            r"인장.*받아",
            r"신물.*가진",
            # 상황적 정당화
            r"가주.*부재",
            r"가주.*위독",
            r"긴급.*사안",
            r"가문.*위기",
        ]

    # ========================================================================
    # [V46.1] 미해결 갈등 검증 (무협 특화)
    # ========================================================================

    def get_hostile_action_types(self) -> list[str]:
        """
        [V46.1] 무협 - 적대적 행동 유형

        구타, 모욕, 독살 시도 등
        """
        return [
            "구타",
            "폭행",
            "모욕",
            "멸시",
            "학대",
            "배신",
            "밀고",
            "암살",
            "독살",
            "습격",
            "협박",
            "갈취",
            "모함",
            "누명",
            "가족해침",
            "은인해침",
        ]

    def get_resolution_patterns(self) -> list[str]:
        """
        [V46.1] 무협 - 갈등 해소 패턴

        용서, 복수, 응징 등
        """
        return [
            # 용서/화해
            r"용서",
            r"화해",
            r"사과.*받",
            r"진심.*뉘우",
            # 복수/응징
            r"복수",
            r"응징",
            r"처단",
            r"목.*베",
            r"피.*갚",
            # 굴복/공포
            r"무릎.*꿇",
            r"고개.*조아",
            r"용서.*빌",
            r"목숨.*구걸",
            r"공포.*질",
            r"벌벌.*떨",
            r"오줌.*지",
            # 추방/제명
            r"추방",
            r"제명",
            r"쫓아내",
            r"내쫓",
        ]

    # ========================================================================
    # [V46.1] 빌런 반응 검증 (무협 특화)
    # ========================================================================

    def get_protagonist_victory_patterns(self) -> list[str]:
        """
        [V46.1] 무협 - 주인공 대역전/승리 패턴
        """
        return [
            # 비무/대결 승리
            r"승리.*거두",
            r"이겼다",
            r"쓰러뜨",
            r"제압",
            r"굴복.*시",
            # 음모 파훼
            r"음모.*밝혀",
            r"계략.*파훼",
            r"비밀.*드러",
            r"정체.*폭로",
            # 인정/성취
            r"사자패.*받",
            r"후계.*인정",
            r"비급.*얻",
            r"기연.*획득",
            # 역전
            r"역전",
            r"반격",
            r"기사회생",
            r"돌파",
        ]

    def get_villain_response_patterns(self) -> list[str]:
        """
        [V46.1] 무협 - 빌런 적절 대응 패턴
        """
        return [
            # 감정 반응
            r"당황",
            r"경악",
            r"분노",
            r"치를.*떨",
            r"이를.*갈",
            r"눈.*충혈",
            # 계획 수정
            r"계획.*변경",
            r"다른.*방법",
            r"후퇴",
            r"물러서",
            # 지능적 제약 (자리를 비워야 하는 이유)
            r"급한.*소식",
            r"밀약",
            r"마교",
            r"비밀.*회동",
            r"다른.*곳.*불",
            r"떠나야",
            r"자리.*비워",
            # 다음 기회 노림
            r"두고.*보자",
            r"끝.*아니",
            r"반드시",
            r"복수.*다짐",
        ]

    # ========================================================================
    # [V49.5] 괄호 현대어 검증
    # ========================================================================

    def check_modern_notation(self, text: str) -> list[dict[str, str]]:
        """
        [V49.5] 원고에서 금지된 현대어 표기 패턴 검출

        Returns:
            List of violations: [{'pattern': str, 'reason': str, 'match': str}]
        """
        import re

        violations = []

        for pattern, reason in self.FORBIDDEN_MODERN_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                violations.append(
                    {"pattern": pattern, "reason": reason, "match": match if isinstance(match, str) else str(match)}
                )

        return violations

    # ========================================================================
    # [V66] run_deep_validation override
    # ========================================================================

    def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]:
        """[V66] Wuxia 심층 검증: base + 현대 표기 검사 + 경지별 무공 제한."""
        result = super().run_deep_validation(manuscript, current_state or {})

        # 현대 표기 검사
        modern_violations = self.check_modern_notation(manuscript)
        if modern_violations:
            examples = [v.get("match", "")[:20] for v in modern_violations[:3]]
            result["violations"].append(
                {"type": "modern_notation", "severity": "MEDIUM", "message": f"현대 표기 발견: {examples}"}
            )

        # 경지별 무공 제한 (HUD 상태 기반)
        if current_state:
            realm = str(current_state.get("realm", "")).strip()
            if realm and realm in ("삼류", "이류"):
                # 절대고수급 무공 사용 검사
                forbidden_moves = ["파천", "멸세", "천지", "신마", "파천성장"]
                for move in forbidden_moves:
                    if move in manuscript:
                        result["violations"].append(
                            {
                                "type": "power_mismatch",
                                "severity": "HIGH",
                                "message": f"경지 '{realm}'에서 절대고수급 무공 '{move}' 사용",
                            }
                        )

        result["has_critical"] = any(v.get("severity") in ("HIGH", "CRITICAL") for v in result["violations"])
        if result["violations"]:
            result["summary"] = "; ".join(v.get("message", "") for v in result["violations"][:5])
            result["feedback"] = f"[무협 Guard] {len(result['violations'])}건: {result['summary']}"
        return result
