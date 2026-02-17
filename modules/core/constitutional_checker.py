"""
[V55.2] Constitutional Self-Check (헌법적 자기 검증)
LLM이 출력 전에 스스로 검증 기준을 확인하도록 유도

핵심: 검증 기준을 프롬프트에 주입하여 첫 시도 통과율 향상

원리:
1. Stage별 REJECT 기준을 명시적으로 프롬프트에 주입
2. LLM이 출력 전에 자가 검증 수행하도록 유도
3. "다음 중 하나라도 YES면 수정 후 출력" 패턴

비용: $0 (프롬프트 주입만)

사용:
    checker = ConstitutionalChecker(genre='wuxia')
    injection = checker.get_analyst_constitution(prev_arcs)
    # Analyst 프롬프트에 injection 추가
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from modules.core.constants import ManuscriptLimits


class CheckType(Enum):
    """체크 타입"""

    CONTINUITY = "continuity"  # 연속성
    SCOPE = "scope"  # 범위 초과
    RELATIONSHIP = "relationship"  # 관계 급변
    ITEM = "item"  # 아이템 오류
    TIMELINE = "timeline"  # 타임라인 오류
    QUALITY = "quality"  # 품질 기준


@dataclass
class ConstitutionArticle:
    """헌법 조항"""

    id: str
    check_type: CheckType
    question: str  # YES/NO 질문 형태
    reject_if_yes: bool  # YES면 REJECT
    severity: str  # "CRITICAL" | "HIGH" | "MEDIUM"


class ConstitutionalChecker:
    """헌법적 자기 검증 시스템"""

    # Stage 2 (Arc) 헌법 조항
    ARC_CONSTITUTION = [
        ConstitutionArticle(
            id="A1",
            check_type=CheckType.ITEM,
            question="이전 Arc에서 이미 획득한 아이템을 다시 획득하는가?",
            reject_if_yes=True,
            severity="CRITICAL",
        ),
        ConstitutionArticle(
            id="A2",
            check_type=CheckType.ITEM,
            question="이전 Arc에서 수여받은 물건/직위를 다시 수여받는가?",
            reject_if_yes=True,
            severity="CRITICAL",
        ),
        ConstitutionArticle(
            id="A3",
            check_type=CheckType.CONTINUITY,
            question="직전 Arc의 joint_docs(위치/소지품)을 무시하는가?",
            reject_if_yes=True,
            severity="CRITICAL",
        ),
        ConstitutionArticle(
            id="A4",
            check_type=CheckType.RELATIONSHIP,
            question="NPC 관계가 2단계 이상 급변하는가? (예: 무시→충성)",
            reject_if_yes=True,
            severity="HIGH",
        ),
        ConstitutionArticle(
            id="A5",
            check_type=CheckType.TIMELINE,
            question="5화 구조를 초과하는 사건을 설계하는가?",
            reject_if_yes=True,
            severity="HIGH",
        ),
        ConstitutionArticle(
            id="A6",
            check_type=CheckType.QUALITY,
            question="tactical_doc이 500자 미만인가?",
            reject_if_yes=True,
            severity="MEDIUM",
        ),
    ]

    # Stage 3 (Blueprint) 헌법 조항
    BLUEPRINT_CONSTITUTION = [
        ConstitutionArticle(
            id="B1",
            check_type=CheckType.ITEM,
            question="Blueprint에서 미획득 아이템을 사용하는가?",
            reject_if_yes=True,
            severity="CRITICAL",
        ),
        ConstitutionArticle(
            id="B2",
            check_type=CheckType.CONTINUITY,
            question="직전 화 cliffhanger를 무시하고 시작하는가?",
            reject_if_yes=True,
            severity="CRITICAL",
        ),
        ConstitutionArticle(
            id="B3",
            check_type=CheckType.SCOPE,
            question="씬 개수가 7개를 초과하는가?",
            reject_if_yes=True,
            severity="HIGH",
        ),
        ConstitutionArticle(
            id="B4",
            check_type=CheckType.QUALITY,
            question="ending_hook이 없거나 5자 미만인가?",
            reject_if_yes=True,
            severity="HIGH",
        ),
        ConstitutionArticle(
            id="B5",
            check_type=CheckType.TIMELINE,
            question="Arc tactical_doc 범위를 초과하는 사건이 있는가?",
            reject_if_yes=True,
            severity="HIGH",
        ),
    ]

    # Stage 4 (Manuscript) 헌법 조항
    MANUSCRIPT_CONSTITUTION = [
        ConstitutionArticle(
            id="M1",
            check_type=CheckType.ITEM,
            question="미획득 아이템을 사용하거나 언급하는가?",
            reject_if_yes=True,
            severity="CRITICAL",
        ),
        ConstitutionArticle(
            id="M2",
            check_type=CheckType.CONTINUITY,
            question="직전 화 상태(부상/위치/감정)를 무시하는가?",
            reject_if_yes=True,
            severity="CRITICAL",
        ),
        ConstitutionArticle(
            id="M3",
            check_type=CheckType.RELATIONSHIP,
            question="관계가 2단계 이상 급변하는가?",
            reject_if_yes=True,
            severity="CRITICAL",
        ),
        ConstitutionArticle(
            id="M4",
            check_type=CheckType.SCOPE,
            question="Blueprint의 핵심 씬을 누락하는가?",
            reject_if_yes=True,
            severity="CRITICAL",
        ),
        ConstitutionArticle(
            id="M5",
            check_type=CheckType.QUALITY,
            question=f"원고가 {ManuscriptLimits.MIN_LENGTH}자 미만인가?",
            reject_if_yes=True,
            severity="HIGH",
        ),
        ConstitutionArticle(
            id="M6",
            check_type=CheckType.QUALITY,
            question="직접 감정 서술이 5회 이상인가? (Show don't Tell 위반)",
            reject_if_yes=True,
            severity="MEDIUM",
        ),
        ConstitutionArticle(
            id="M7",
            check_type=CheckType.QUALITY,
            question="클리셰 표현이 3회 이상인가?",
            reject_if_yes=True,
            severity="MEDIUM",
        ),
    ]

    def __init__(self, genre: str = "wuxia"):
        """
        Args:
            genre: 장르 (wuxia, hunter, investment)
        """
        self.genre = genre

    def get_analyst_constitution(self, prev_arcs: list[dict[str, Any]] = None, additional_constraints: str = "") -> str:
        """
        Stage 2 (Analyst/Arc) 헌법 프롬프트 생성

        Args:
            prev_arcs: 이전 Arc 목록
            additional_constraints: 추가 제약

        Returns:
            주입할 프롬프트 문자열
        """
        lines = [
            "=" * 60,
            "[V55.2 Constitutional Self-Check: Arc 설계]",
            "출력 전에 다음 체크리스트를 반드시 확인하세요.",
            "하나라도 YES면 수정 후 출력하세요.",
            "=" * 60,
        ]

        # 이전 Arc 획득 이력 요약
        if prev_arcs:
            acquired_items = []
            grants_received = []

            for arc in prev_arcs:
                arc_no = arc.get("arc_no", "?")
                state = arc.get("state_constraints", {})

                items = state.get("items_acquired", [])
                for item in items:
                    if item:
                        acquired_items.append(f"Arc{arc_no}: {item}")

                grants = state.get("grants_received", [])
                for grant in grants:
                    if grant:
                        grants_received.append(f"Arc{arc_no}: {grant}")

            if acquired_items:
                lines.append("\n🚫 [이미 획득한 아이템 - 중복 획득 금지]")
                for item in acquired_items[-10:]:  # 최근 10개만
                    lines.append(f"   - {item}")

            if grants_received:
                lines.append("\n🚫 [이미 받은 수여물 - 중복 수여 금지]")
                for grant in grants_received[-5:]:
                    lines.append(f"   - {grant}")

        lines.append("\n📋 [자가 검증 체크리스트]")
        for article in self.ARC_CONSTITUTION:
            severity_emoji = "🔴" if article.severity == "CRITICAL" else "🟡" if article.severity == "HIGH" else "🟢"
            lines.append(f"{severity_emoji} [{article.id}] {article.question}")
            lines.append(f"       → YES면 즉시 수정 (심각도: {article.severity})")

        if additional_constraints:
            lines.append(f"\n📌 [추가 제약]\n{additional_constraints}")

        lines.append("\n" + "=" * 60)
        lines.append("위 체크리스트를 통과한 후에만 JSON을 출력하세요.")
        lines.append("=" * 60)

        return "\n".join(lines)

    def get_architect_constitution(
        self, prev_blueprint: dict[str, Any] = None, arc_data: dict[str, Any] = None, additional_constraints: str = ""
    ) -> str:
        """
        Stage 3 (Architect/Blueprint) 헌법 프롬프트 생성
        """
        lines = [
            "=" * 60,
            "[V55.2 Constitutional Self-Check: Blueprint 설계]",
            "출력 전에 다음 체크리스트를 반드시 확인하세요.",
            "=" * 60,
        ]

        # 직전 화 정보
        if prev_blueprint:
            ending = prev_blueprint.get("ending_hook") or prev_blueprint.get("cliffhanger", "")
            if ending:
                lines.append("\n📌 [직전 화 ending_hook - 반드시 이어받을 것]")
                lines.append(f'   "{ending[:150]}"')

        # Arc 범위
        if arc_data:
            tactical = arc_data.get("tactical_doc", "")
            if tactical:
                lines.append("\n📌 [Arc tactical_doc 범위 - 초과 금지]")
                lines.append(f"   {tactical[:200]}...")

        lines.append("\n📋 [자가 검증 체크리스트]")
        for article in self.BLUEPRINT_CONSTITUTION:
            severity_emoji = "🔴" if article.severity == "CRITICAL" else "🟡" if article.severity == "HIGH" else "🟢"
            lines.append(f"{severity_emoji} [{article.id}] {article.question}")
            lines.append("       → YES면 즉시 수정")

        if additional_constraints:
            lines.append(f"\n📌 [추가 제약]\n{additional_constraints}")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def get_writer_constitution(
        self,
        blueprint: dict[str, Any] = None,
        prev_manuscript: str = "",
        inventory: list[str] = None,
        additional_constraints: str = "",
    ) -> str:
        """
        Stage 4 (Writer/Manuscript) 헌법 프롬프트 생성
        """
        lines = [
            "=" * 60,
            "[V55.2 Constitutional Self-Check: 원고 작성]",
            "출력 전에 다음 체크리스트를 반드시 확인하세요.",
            "=" * 60,
        ]

        # 현재 소지품
        if inventory:
            lines.append("\n✅ [현재 소지 아이템 - 이것만 사용 가능]")
            for item in inventory[:10]:
                lines.append(f"   - {item}")

        # 직전 화 상태
        if prev_manuscript:
            ending_part = prev_manuscript[-500:] if len(prev_manuscript) > 500 else prev_manuscript
            lines.append("\n📌 [직전 화 마지막 - 이 상태에서 시작]")
            lines.append(f"   ...{ending_part[-200:]}")

        # Blueprint 핵심 씬
        if blueprint:
            scene_breakdown = blueprint.get("scene_breakdown", {})
            if scene_breakdown:
                lines.append("\n📋 [Blueprint 필수 씬 - 모두 반영할 것]")
                for i, (scene_id, scene_data) in enumerate(list(scene_breakdown.items())[:6], 1):
                    if isinstance(scene_data, dict):
                        desc = scene_data.get("description", str(scene_data))[:50]
                    else:
                        desc = str(scene_data)[:50]
                    lines.append(f"   {i}. {scene_id}: {desc}")

        lines.append("\n📋 [자가 검증 체크리스트]")
        for article in self.MANUSCRIPT_CONSTITUTION:
            severity_emoji = "🔴" if article.severity == "CRITICAL" else "🟡" if article.severity == "HIGH" else "🟢"
            lines.append(f"{severity_emoji} [{article.id}] {article.question}")
            lines.append("       → YES면 즉시 수정")

        if additional_constraints:
            lines.append(f"\n📌 [추가 제약]\n{additional_constraints}")

        lines.append("\n" + "=" * 60)
        lines.append("위 체크리스트를 모두 통과한 원고만 출력하세요.")
        lines.append("=" * 60)

        return "\n".join(lines)

    def get_reject_examples(self, stage: int) -> str:
        """
        REJECT 예시 프롬프트 생성 (Contrastive Few-Shot 강화)

        Args:
            stage: 2, 3, 4

        Returns:
            REJECT 예시 문자열
        """
        if stage == 2:
            return self._get_arc_reject_examples()
        elif stage == 3:
            return self._get_blueprint_reject_examples()
        elif stage == 4:
            return self._get_manuscript_reject_examples()
        return ""

    def _get_arc_reject_examples(self) -> str:
        """
        [V55.5] 확장된 Arc REJECT 예시
        """
        return """
[REJECT 사례 - 이런 설계는 즉시 반려됩니다]

❌ 사례 1: 아이템 중복 획득
   Arc 2에서 이미 "백근 대도" 획득
   → Arc 5에서 "백근 대도를 획득하러 간다" 설계
   → REJECT: 이미 소지 중인 아이템

❌ 사례 2: 수여물 중복
   Arc 3에서 "철혈사자패" 하사받음
   → Arc 6에서 "철혈사자패 수여식" 설계
   → REJECT: 이미 받은 수여물

❌ 사례 3: 위치 연속성 무시
   Arc 4 joint_docs.final_location = "청풍검각"
   → Arc 5 1화에서 "낙양에서 아침을 맞았다" 설계
   → REJECT: 순간이동 (이동 경위 필요)

❌ 사례 4: 관계 급변 설계 (V55.5 NEW)
   Arc 3에서 사병들이 주인공을 "무시"하는 상태로 끝남
   → Arc 4에서 "사병들이 충성을 맹세한다" 설계
   → REJECT: 2단계 이상 급변 (무시→의심→경외→충성 단계 필요)
   ✅ 올바른: Arc 4에서 "사병들이 주인공을 의심의 눈초리로 바라본다"

❌ 사례 5: 5화 초과 사건 (V55.5 NEW)
   Arc 5 tactical_doc에 10개 대형 사건 나열
   → REJECT: 5화에 소화 불가능한 분량
   ✅ 올바른: 핵심 사건 2-3개 + 소규모 연결 사건

❌ 사례 6: 복권 남발 (V55.5 NEW)
   Arc 2: 주인공이 복권 선포
   Arc 3: 또 다른 복권 선포
   → REJECT: 복권은 1회만 가능
   ✅ 올바른: 복권 후에는 "위상 상승" 또는 "새로운 도전" 설계

✅ 올바른 예시:
   "허리에 찬 백근 대도를 뽑아 들었다" (기존 소지품 사용)
   "품 안의 철혈사자패를 내보였다" (기존 수여물 활용)
   "청풍검각을 떠나 낙양으로 향했다" (이동 경위 명시)
   "사병들의 눈빛이 경계로 바뀌었다" (관계 1단계 변화)
"""

    def _get_blueprint_reject_examples(self) -> str:
        """
        [V55.5] 확장된 Blueprint REJECT 예시
        """
        return """
[REJECT 사례 - 이런 Blueprint는 즉시 반려됩니다]

❌ 사례 1: cliffhanger 무시
   직전 화 ending_hook: "독이 퍼지기 시작했다"
   → 이번 화 Scene 1: "화창한 아침, 주인공이 산책을 나선다"
   → REJECT: 긴급 상황 무시

❌ 사례 2: 씬 과다
   Scene 1~8까지 8개 씬 설계
   → REJECT: 최대 6-7개 권장

❌ 사례 3: ending_hook 누락
   ending_hook: "" (빈 문자열)
   → REJECT: 다음 화 연결고리 필수

❌ 사례 4: Arc 범위 초과 (V55.5 NEW)
   Arc tactical_doc: "1화~3화: 청풍검각 사건"
   → Blueprint: 5화에서 청풍검각 밖의 낙양 사건 설계
   → REJECT: Arc 범위 밖 사건 (다음 Arc에서 처리)

❌ 사례 5: 핵심 씬 희석 (V55.5 NEW)
   Arc tactical_doc 핵심 사건: "철혈사자패 수여"
   → Blueprint: 철혈사자패 수여가 Scene 6의 부차적 묘사
   → REJECT: 핵심 사건은 독립 씬으로 설계
   ✅ 올바른: Scene 4: "철혈사자패 수여식 - 주인공의 위상 변화"

❌ 사례 6: 약한 ending_hook (V55.5 NEW)
   ending_hook: "다음 화에서 계속"
   → REJECT: 구체적 갈등/미완결 상황 필요
   ✅ 올바른: "독이 해독되었으나, 배후의 정체가 밝혀지며 더 큰 음모의 실마리가 드러난다"

✅ 올바른 예시:
   Scene 1: "독이 퍼지는 상황에서 해독을 시도한다" (직전 화 연결)
   씬 개수: 4-6개 (핵심 사건당 1개 씬)
   ending_hook: "해독에 성공했으나, 독을 넣은 자의 정체가 의외의 인물임이 밝혀진다" (구체적 갈등)
"""

    def _get_manuscript_reject_examples(self) -> str:
        """
        [V55.5] 확장된 REJECT 예시 (10개 → 14개)
        Wuxia 특화 + 서사 품질 강화
        """
        return """
[REJECT 사례 - 이런 원고는 즉시 반려됩니다]

❌ 사례 1: 미획득 아이템 사용
   소지품: [검, 은자 10냥]
   → 원고: "품에서 해독단을 꺼냈다"
   → REJECT: 해독단 미소지

❌ 사례 2: 관계 급변
   직전 화: 사병들이 주인공을 "무시"
   → 이번 화: 사병들이 "충성"을 맹세
   → REJECT: 2단계 이상 급변 (무시→의심→경외→충성)

❌ 사례 3: Blueprint 씬 누락
   Blueprint Scene 4: "악당과의 대결"
   → 원고에 대결 씬 없음
   → REJECT: 핵심 씬 누락

❌ 사례 4: Show Don't Tell 위반
   "그는 분노했다. 그는 슬펐다. 그는 기뻤다."
   → REJECT: 직접 감정 서술 과다

❌ 사례 5: 경지 급상승 (V55.5 NEW)
   직전 화: "이류 초입"
   → 이번 화: "일류 경지에 올랐다"
   → REJECT: 한 화 만에 2단계 경지 상승 (수련 과정 필수)
   ✅ 올바른: "밤새 기혈을 운용하며 병목을 돌파했다. 온몸이 부서질 듯 아팠다."

❌ 사례 6: 부상 무시 (V55.5 NEW)
   직전 화 끝: "검에 깊이 베여 피를 쏟으며 쓰러졌다"
   → 이번 화 시작: "화창한 아침, 가볍게 검을 휘둘렀다"
   → REJECT: 중상 후 즉시 활동 (회복 과정 필수)
   ✅ 올바른: "상처가 아물기까지 사흘을 꼼짝없이 누워 있어야 했다."

❌ 사례 7: 어리석은 악역 (V55.5 NEW)
   이전 2화: 악역이 주인공을 "철부지"라며 무시
   → 이번 화: 또 "어린 놈이 뭘 안다고" 무시
   → REJECT: 3회 연속 과소평가 (학습 반응 필수)
   ✅ 올바른: "이 녀석... 만만히 볼 상대가 아니군."

❌ 사례 8: 정보 텔레파시 (V55.5 NEW)
   청풍검각에서 발생한 사건 (주인공 부재)
   → 주인공이 낙양에서 사건을 "이미 알고 있었다"
   → REJECT: 정보 습득 경위 없음
   ✅ 올바른: "떠도는 소문을 들으니 청풍검각에서..." (정보원 명시)

❌ 사례 9: 무기 증발 (V55.5 NEW)
   직전 화 끝: "백근대도를 허리에 차고 객잔을 나섰다"
   → 이번 화: 대도 언급 없이 맨손 격투
   → REJECT: 핵심 장비 증발
   ✅ 올바른: "대도를 등에 지고" 또는 "대도가 무거워 객실에 두고 나왔다"

❌ 사례 10: 순간이동 (V55.5 NEW)
   직전 화: 청풍검각 (산속)
   → 이번 화 시작: 낙양 성문 앞
   → REJECT: 이동 경위 없음 (도보 5일 거리)
   ✅ 올바른: "5일간 쉬지 않고 달려 낙양에 도착했다"

❌ 사례 11: 공짜 파워업 (V55.5 NEW)
   "기혈을 운용하자 상대가 날아갔다"
   → REJECT: 정당화/대가 없는 초인적 힘
   ✅ 올바른: "발경을 쓰자 팔목 기혈이 역류했다. 고통을 참으며..."

❌ 사례 12: 복선 없는 비급 (V55.5 NEW)
   언급 없던 절기가 갑자기 등장: "천잔검법을 펼쳤다"
   → REJECT: 복선 없는 새 기술
   ✅ 올바른: 이전 화에서 "오래전 스승에게 배웠으나 미완성인 검법..." 복선 필요

✅ 올바른 예시 종합:
   "허리에 찬 검을 뽑아 들었다" (소지품 사용)
   "사병들의 눈빛에 경계가 서렸다" (의심 단계 - 자연스러운 변화)
   "주먹을 꽉 쥐자 손톱이 살을 파고들었다" (분노를 보여줌)
   "전생의 기억이 손끝을 이끌었다" (파워업 정당화)
   "부상이 채 낫지 않아 한 손만으로 검을 쥐었다" (부상 연속성)
"""

    def get_full_injection(self, stage: int, context: dict[str, Any] = None) -> str:
        """
        전체 주입 프롬프트 생성 (Constitutional + REJECT Examples)

        Args:
            stage: 2, 3, 4
            context: Stage별 컨텍스트

        Returns:
            전체 주입 문자열
        """
        context = context or {}

        if stage == 2:
            constitution = self.get_analyst_constitution(
                prev_arcs=context.get("prev_arcs", []), additional_constraints=context.get("feedback", "")
            )
        elif stage == 3:
            constitution = self.get_architect_constitution(
                prev_blueprint=context.get("prev_blueprint"),
                arc_data=context.get("arc_data"),
                additional_constraints=context.get("feedback", ""),
            )
        elif stage == 4:
            constitution = self.get_writer_constitution(
                blueprint=context.get("blueprint"),
                prev_manuscript=context.get("prev_manuscript", ""),
                inventory=context.get("inventory", []),
                additional_constraints=context.get("feedback", ""),
            )
        else:
            return ""

        reject_examples = self.get_reject_examples(stage)

        return f"{constitution}\n\n{reject_examples}"
