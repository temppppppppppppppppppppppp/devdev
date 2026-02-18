"""
[V62.1] 의학물 전용 Guard
[V57] 완전 구현 - 일관성 검증, 권위 위계, 타임라인 검증
의학/병원의 전문성과 개연성을 유지
"""

from typing import Any

from .base_guard import BaseGuard


class MedicalGuard(BaseGuard):
    """[의학물] 의사 성장 + 병원 시스템 전문성 보호자 + V57 완전 구현"""

    def __init__(self) -> None:
        super().__init__()
        cfg = self._load_genre_yaml("medical")

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

        self.MEDICAL_TERMS = cfg.get(
            "medical_terms",
            [
                "바이탈",
                "혈압",
                "맥박",
                "산소포화도",
                "체온",
                "수술",
                "절개",
                "봉합",
                "지혈",
                "마취",
                "전신마취",
                "국소마취",
                "진단",
                "소견",
                "판독",
                "검사",
                "혈액검사",
                "조직검사",
                "CT",
                "MRI",
                "X-ray",
                "초음파",
                "PET",
                "처방",
                "투약",
                "수액",
                "항생제",
                "진통제",
                "회진",
                "컨퍼런스",
                "차트",
                "오더",
                "프로토콜",
                "레지던트",
                "어텐딩",
                "인턴",
                "수련의",
                "전공의",
                "응급실",
                "중환자실",
                "수술실",
                "병동",
                "외래",
                "트리아지",
                "코드블루",
                "심폐소생술",
                "제세동기",
                "전과",
                "전원",
                "퇴원",
                "입원",
                "외래진료",
                "임상시험",
                "IRB",
                "인폼드컨센트",
                "예후",
            ],
        )

        self.MANDATORY_CONCEPTS = cfg.get(
            "mandatory_concepts",
            [
                "의학 지식의 정확성과 개연성",
                "환자-의사 관계와 생명윤리",
                "병원 위계와 수련 과정의 사실적 묘사",
                "수술/진료 과정의 긴장감 있는 묘사",
            ],
        )

        self._doctor_hierarchy = cfg.get(
            "doctor_hierarchy",
            [
                "의대생",
                "인턴",
                "레지던트",
                "전문의",
                "펠로우",
                "부교수",
                "교수",
                "석좌교수",
            ],
        )

        self._doctor_action_limits = cfg.get(
            "doctor_action_limits",
            {
                "의대생": [r"독자.*수술", r"단독.*처방", r"전공의.*지도", r"논문.*제1저자"],
                "인턴": [r"독자.*수술", r"전공의.*지도", r"독립적.*진료", r"교수.*임용"],
                "레지던트": [r"독자.*개원", r"교수.*임용", r"석좌.*취임", r"국제.*학회.*기조연설"],
                "전문의": [r"석좌.*취임", r"병원장.*취임"],
            },
        )

        self._status_action_limits = cfg.get(
            "status_action_limits",
            {
                "면허정지": [r"진료", r"수술", r"처방", r"의료.*행위"],
                "과로": [r"장시간.*수술", r"정밀.*시술", r"야간.*당직.*연속"],
                "의료사고": [r"즉각.*복귀", r"수술.*집도", r"환자.*배정"],
                "정신적외상": [r"냉정한.*판단", r"고난이도.*수술", r"응급.*대응"],
                "징계": [r"수술", r"진료", r"환자.*접근"],
            },
        )

        self._surgery_requirements = {
            "단순 봉합": {"doctor_rank": "인턴"},
            "충수절제술": {"doctor_rank": "레지던트"},
            "심장 수술": {"doctor_rank": "전문의", "specialty": "흉부외과"},
            "장기 이식": {"doctor_rank": "부교수", "experience": True},
            "세계 최초 수술": {"doctor_rank": "교수", "research": True, "team": True},
        }

    def get_genre_name(self) -> str:
        return "의학물(MEDICAL)"

    def _should_check_english(self) -> bool:
        """의학물은 현대 배경이므로 영어 완화 (의학 용어에 외래어 많음)"""
        return False

    def _should_check_numbers(self) -> bool:
        """의학물은 바이탈/수치 등 정확한 데이터가 중요"""
        return False

    def get_v20_purism_prompt(self) -> str:
        """의학물 장르 전문성 지침"""
        return f"""
[🏥 V62.1 의학물 장르 가이드라인 (Medical Genre Professionalism)]

1. **장르 교란 금지**: 판타지/무협 용어({", ".join(self.FORBIDDEN_TERMS[:8])} 등)를 사용하지 마라. 현실적인 의학/병원 세계관을 유지하라.
2. **의학 상식 준수**: 모든 진단과 치료는 현대 의학에 부합해야 한다. 존재하지 않는 질병이나 비현실적 치료법은 금지한다.
3. **전문 용어의 정확성**: {", ".join(self.MEDICAL_TERMS[:10])} 등의 의학 용어를 정확하게 사용하라.
4. **성장의 개연성**: 주인공의 의술 향상은 반드시 수련, 수술 경험, 학술 연구에 기반해야 한다.
5. **수술 묘사**: 수술실의 긴장감(바이탈 모니터, 메스, 출혈), 시간 압박, 팀워크를 생생하게 묘사하라.
6. **병원 정치**: 과장 경쟁, 교수 임용, 수련의 갈등, 병원 경영 등 조직 역학을 입체적으로 그려라.
7. **의료 윤리**: 인폼드 컨센트, 환자 자기결정권, 의료 자원 배분 등 윤리적 딜레마를 사실적으로 다뤄라.
8. **시대적 배경**: 원격진료, AI 진단, 로봇수술, 줄기세포 등 현대 의학 트렌드를 자연스럽게 활용하라.
9. **필수 표현 요소**: {", ".join(self.MANDATORY_CONCEPTS)}

[개연성 체크리스트]
- 수술 난이도가 주인공의 직급/경력에 부합하는가?
- 진단 과정이 의학적으로 타당한가?
- 환자의 예후가 현실적인가?
- 병원 내 위계와 의사결정 과정이 사실적인가?
"""

    # ========================================================================
    # [V57] 일관성 검증 구현 (의학물 특화)
    # ========================================================================

    def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]:
        """[V57] 의학물 - 현재 상태에서 불가능한 행동 패턴 반환"""
        actions = []

        # 1. 상태 기반 제한 (면허정지, 과로 등)
        status = current_state.get("status", current_state.get("condition", ""))
        if isinstance(status, str):
            for status_keyword, patterns in self._status_action_limits.items():
                if status_keyword in status:
                    for pattern in patterns:
                        actions.append(
                            {"pattern": pattern, "reason": f"상태 '{status_keyword}'로 인해 불가", "severity": "HIGH"}
                        )

        # 2. 직급 기반 제한
        rank = current_state.get("doctor_rank", current_state.get("rank", "의대생"))
        rank_class = self._get_doctor_class(rank)
        if rank_class and rank_class in self._doctor_action_limits:
            for pattern in self._doctor_action_limits[rank_class]:
                actions.append({"pattern": pattern, "reason": f"직급 '{rank_class}'에서 불가", "severity": "HIGH"})

        # 3. 의료사고 이력
        malpractice = current_state.get("malpractice_record", [])
        if isinstance(malpractice, list) and len(malpractice) > 0:
            recent = malpractice[-1] if malpractice else {}
            if isinstance(recent, dict) and not recent.get("resolved", False):
                actions.append(
                    {
                        "pattern": r"고난이도.*수술|단독.*집도|신규.*환자",
                        "reason": "미해결 의료사고 이력 - 수술 제한",
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
                        "pattern": r"미래.*정보|예지|질병.*예측",
                        "reason": "회귀 시점 이후 - 미래 정보 없음",
                        "severity": "CRITICAL",
                    }
                )

        return actions

    def _get_doctor_class(self, rank) -> str:
        """직급 수준에 따른 클래스 반환"""
        if isinstance(rank, str):
            for cls_name in self._doctor_hierarchy:
                if cls_name in rank:
                    return cls_name
            return "의대생"
        return "의대생"

    def get_justification_patterns(self) -> list[str]:
        """[V57] 의학물 - 정당화로 인정되는 표현 패턴"""
        return [
            r"미래.*기억",
            r"과거.*경험",
            r"전생.*정보",
            r"수술.*집도",
            r"임상.*경험",
            r"수련.*과정",
            r"학술.*연구",
            r"논문.*발표",
            r"학회.*참석",
            r"해외.*연수",
            r"유학.*경험",
            r"명의.*지도",
            r"천부적.*손재주",
            r"타고난.*감각",
            r"직관",
            r"밤새.*공부",
            r"독학.*연구",
            r"케이스.*분석",
            r"응급.*대응",
            r"실전.*경험",
            r"위기.*대처",
            r"멘토.*가르침",
            r"교수.*지도",
            r"선배.*조언",
        ]

    def get_hierarchy_rules(self) -> dict[str, Any]:
        """[V57] 의학물 - 의사 직급/위계 규칙"""
        return {
            "doctor_ranks": self._doctor_hierarchy,
            "titles": {
                "의대생": ["의대생", "본과생", "임상실습생"],
                "인턴": ["인턴", "수련의"],
                "레지던트": ["레지던트", "전공의", "R1", "R2", "R3", "R4"],
                "전문의": ["전문의", "봉직의", "개원의"],
                "펠로우": ["펠로우", "임상강사"],
                "부교수": ["부교수", "조교수"],
                "교수": ["교수", "과장"],
                "석좌교수": ["석좌교수", "명예교수", "원장"],
            },
            "violations": {
                "의대생": [r"독자.*수술", r"단독.*처방", r"교수.*지위"],
                "인턴": [r"독자.*수술", r"교수", r"독립.*진료"],
                "레지던트": [r"교수.*임용", r"독자.*개원", r"석좌"],
                "전문의": [r"석좌.*취임", r"병원장"],
            },
        }

    def get_technique_effect_rules(self) -> dict[str, dict[str, Any]]:
        """[V57] 의학물 - 의료 활동별 효능 규칙"""
        return {
            "수술 집도": {
                "effect_type": "surgery",
                "effect_scope": ["실력 향상", "명성 축적", "경험 축적"],
                "cannot_be_used_for": ["즉각적 교수 임용", "학술 업적"],
                "requirements": ["자격", "환자 동의", "수술팀"],
            },
            "학술 연구": {
                "effect_type": "research",
                "effect_scope": ["학술 업적", "교수 임용 기반", "새 치료법"],
                "cannot_be_used_for": ["임상 실력 향상", "즉각적 명성"],
                "requirements": ["IRB 승인", "연구 기간", "자금"],
            },
            "해외 연수": {
                "effect_type": "training",
                "effect_scope": ["새 기술 습득", "글로벌 인맥", "경력"],
                "cannot_be_used_for": ["국내 진료", "국내 명성"],
                "requirements": ["파견 승인", "연수 기간", "어학"],
            },
            "응급 대응": {
                "effect_type": "emergency",
                "effect_scope": ["위기 대처 능력", "실전 경험", "팀워크"],
                "cannot_be_used_for": ["학술 업적", "정밀 수술 능력"],
                "risk": "실패 시 환자 사망, 의료사고",
            },
            "멘토 지도": {
                "effect_type": "mentoring",
                "effect_scope": ["수술 기법 전수", "의학 철학", "진단 눈"],
                "cannot_be_used_for": ["학술 업적", "독자적 명성"],
                "requirements": ["멘토 관계", "신뢰", "기간"],
            },
        }

    # ========================================================================
    # [V57] 권위 위계 검증 (의학물 특화)
    # ========================================================================

    def get_authority_hierarchy(self) -> dict[str, Any]:
        """[V57] 의학물 - 병원 조직 권위 위계"""
        return {
            "positions": ["병원장", "부원장", "과장", "교수", "부교수", "펠로우", "전문의", "레지던트", "인턴"],
            "position_titles": {
                "병원장": ["병원장", "원장", "이사장"],
                "부원장": ["부원장", "부이사장"],
                "과장": ["과장", "주임교수", "센터장"],
                "교수": ["교수", "지도전문의"],
                "부교수": ["부교수", "조교수"],
                "펠로우": ["펠로우", "임상강사"],
                "전문의": ["전문의", "과장대리"],
                "레지던트": ["레지던트", "전공의"],
                "인턴": ["인턴", "수련의"],
            },
            "authority_scope": {
                "병원장": ["병원 경영", "인사", "투자", "대외 협력"],
                "부원장": ["진료 총괄", "교육", "연구 총괄"],
                "과장": ["과 운영", "수술 배정", "전공의 교육", "인사 추천"],
                "교수": ["수술 집도", "외래 진료", "연구 지도", "전공의 지도"],
                "부교수": ["수술 보조/집도", "외래", "연구"],
                "레지던트": ["회진", "오더", "수술 보조", "당직"],
            },
        }

    def get_delegation_patterns(self) -> list[str]:
        """[V57] 의학물 - 권위 위임 정당화 패턴"""
        return [
            r"교수.*지시",
            r"과장.*명령",
            r"어텐딩.*판단",
            r"병원장.*방침",
            r"위원회.*결정",
            r"응급.*상황",
            r"코드블루",
            r"환자.*동의",
            r"보호자.*요청",
            r"프로토콜",
            r"가이드라인",
        ]

    # ========================================================================
    # [V57] 갈등 및 해소 검증
    # ========================================================================

    def get_hostile_action_types(self) -> list[str]:
        """[V57] 의학물 - 적대적 행동 유형"""
        return [
            "의료사고 모함",
            "논문 표절 의혹",
            "환자 빼앗기",
            "과장 자리 경쟁",
            "수련의 갈굼",
            "부당 지시",
            "의료 소송",
            "내부 고발",
            "파벌 다툼",
            "제약사 로비",
            "보험 사기",
            "은폐 시도",
            "인사 불이익",
            "연구비 횡령 의혹",
        ]

    def get_resolution_patterns(self) -> list[str]:
        """[V57] 의학물 - 갈등 해소 패턴"""
        return [
            r"수술.*성공",
            r"환자.*회복",
            r"진단.*정확",
            r"논문.*게재",
            r"학회.*발표",
            r"연구.*성과",
            r"결백.*증명",
            r"소송.*승소",
            r"조사.*무혐의",
            r"동료.*인정",
            r"교수.*신뢰",
            r"환자.*감사",
            r"승진",
            r"임용",
            r"과장.*취임",
            r"새.*치료법",
            r"세계.*최초",
            r"학술.*업적",
            r"화해",
            r"협력",
            r"팀워크",
        ]

    # ========================================================================
    # [V66] 심층 검증 오버라이드
    # ========================================================================

    def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]:
        """[V66] 의학물 심층 검증."""
        result = super().run_deep_validation(manuscript, current_state or {})

        # [V70] get_impossible_actions 중복 제거 (super()가 이미 check_state_action_consistency에서 호출)

        result["has_critical"] = any(v.get("severity") in ("HIGH", "CRITICAL") for v in result["violations"])
        if result["violations"]:
            result["summary"] = "; ".join(v.get("message", "") for v in result["violations"][:5])
            result["feedback"] = f"[의학물 Guard] {len(result['violations'])}건: {result['summary']}"
        return result
