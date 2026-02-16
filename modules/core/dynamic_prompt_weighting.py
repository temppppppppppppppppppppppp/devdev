"""
[V53.1] Dynamic Prompt Weighting (동적 프롬프트 가중치)
REJECT 패턴 기반 프롬프트 강조 동적 조절

핵심: failure_learner 데이터를 분석하여 취약 영역 프롬프트 강화

원리:
1. 최근 REJECT 사유 분석
2. 카테고리별 실패 빈도 계산
3. 빈도 높은 영역의 프롬프트 가중치 증가
4. 에이전트 프롬프트에 강조 지시어 주입

비용: $0 (프롬프트 최적화만)

사용:
    weighter = DynamicPromptWeighter(failure_learner)
    injection = weighter.get_weighted_prompt(agent_type='writer', stage=4)
"""

from collections import Counter
from dataclasses import dataclass
from enum import Enum


class PromptCategory(Enum):
    """프롬프트 강조 카테고리"""

    CONTINUITY = "continuity"  # 연속성
    ITEM_MANAGEMENT = "item_management"  # 아이템 관리
    RELATIONSHIP = "relationship"  # 관계 변화
    PACING = "pacing"  # 호흡/페이싱
    CHARACTER = "character"  # 캐릭터 일관성
    SCENE_STRUCTURE = "scene_structure"  # 씬 구조
    DIALOGUE = "dialogue"  # 대화 품질
    DESCRIPTION = "description"  # 묘사 품질
    BLUEPRINT_COMPLIANCE = "blueprint"  # 블루프린트 준수
    VILLAIN_INTELLIGENCE = "villain"  # 악역 지능


@dataclass
class WeightedDirective:
    """가중치가 적용된 지시어"""

    category: PromptCategory
    weight: float  # 0.0 ~ 1.0
    directive: str
    urgency: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"


class DynamicPromptWeighter:
    """동적 프롬프트 가중치 시스템"""

    # 실패 키워드 → 카테고리 매핑
    FAILURE_KEYWORD_MAP = {
        PromptCategory.CONTINUITY: [
            "연속성",
            "continuity",
            "이전 화",
            "직전",
            "모순",
            "불일치",
            "타임라인",
            "timeline",
            "시간 역행",
        ],
        PromptCategory.ITEM_MANAGEMENT: [
            "아이템",
            "item",
            "획득",
            "중복",
            "소지",
            "무기",
            "장비",
            "inventory",
            "duplicate",
        ],
        PromptCategory.RELATIONSHIP: ["관계", "relationship", "급변", "역행", "충성", "적대", "NPC", "반응"],
        PromptCategory.PACING: ["호흡", "pacing", "템포", "서사 폭주", "서사 정체", "범위 초과", "scope"],
        PromptCategory.CHARACTER: ["캐릭터", "character", "일관성", "OOC", "성격", "말투", "voice"],
        PromptCategory.SCENE_STRUCTURE: ["씬", "scene", "구조", "반영", "누락", "장면"],
        PromptCategory.DIALOGUE: ["대화", "dialogue", "대사", "말", "conversation"],
        PromptCategory.DESCRIPTION: ["묘사", "description", "감각", "시각", "청각", "sensory"],
        PromptCategory.BLUEPRINT_COMPLIANCE: ["blueprint", "블루프린트", "설계", "준수", "compliance"],
        PromptCategory.VILLAIN_INTELLIGENCE: ["악역", "villain", "지능", "멍청", "과소평가", "경계"],
    }

    # 카테고리별 강조 지시어 템플릿
    DIRECTIVE_TEMPLATES = {
        PromptCategory.CONTINUITY: {
            "CRITICAL": "[🚨 연속성 최우선] 이전 화와의 연속성을 반드시 확인하라. 직전 화 엔딩에서 이어지는 상황/상태/소지품을 정확히 반영하라. 이전에 발생한 사건을 부정하거나 없던 일로 만들지 마라.",
            "HIGH": "[⚠️ 연속성 주의] 직전 화 엔딩 상황을 확인하고, 자연스럽게 이어지도록 작성하라.",
            "MEDIUM": "[연속성 확인] 이전 화와의 연결을 의식하며 작성하라.",
        },
        PromptCategory.ITEM_MANAGEMENT: {
            "CRITICAL": "[🚨 아이템 관리 필수] 현재 소지 아이템 목록을 정확히 파악하라. 이미 획득한 아이템을 다시 획득하거나, 없는 아이템을 사용하지 마라. 아이템 획득/소실은 명시적으로 묘사하라.",
            "HIGH": "[⚠️ 아이템 주의] 캐릭터의 현재 소지품을 확인하고 일관되게 사용하라.",
            "MEDIUM": "[아이템 확인] 소지품 사용 시 보유 여부를 확인하라.",
        },
        PromptCategory.RELATIONSHIP: {
            "CRITICAL": "[🚨 관계 변화 금지] NPC 관계를 갑자기 바꾸지 마라. 적대→충성 같은 급변은 반드시 충분한 계기와 설득 과정이 필요하다. 관계 변화는 점진적이어야 한다.",
            "HIGH": "[⚠️ 관계 일관성] NPC 반응이 이전 관계 상태와 일치하는지 확인하라.",
            "MEDIUM": "[관계 확인] 캐릭터 간 관계가 자연스럽게 유지되는지 점검하라.",
        },
        PromptCategory.PACING: {
            "CRITICAL": "[🚨 범위 엄수] 이번 화에서 다뤄야 할 범위만 작성하라. Blueprint 범위를 절대 초과하지 마라. 서사 폭주(한 화에 너무 많은 사건)를 피하라.",
            "HIGH": "[⚠️ 호흡 조절] 한 화에 적절한 분량의 사건만 다루라. 급하게 진행하지 마라.",
            "MEDIUM": "[호흡 확인] 이야기 템포가 적절한지 확인하라.",
        },
        PromptCategory.CHARACTER: {
            "CRITICAL": "[🚨 캐릭터 일관성] 캐릭터의 성격, 말투, 행동 패턴을 일관되게 유지하라. 갑작스러운 성격 변화는 금지.",
            "HIGH": "[⚠️ 캐릭터 주의] 각 캐릭터의 고유한 특성을 유지하라.",
            "MEDIUM": "[캐릭터 확인] 캐릭터다운 행동인지 점검하라.",
        },
        PromptCategory.SCENE_STRUCTURE: {
            "CRITICAL": "[🚨 씬 완전 반영] Blueprint의 모든 씬을 빠짐없이 반영하라. 씬을 건너뛰거나 생략하지 마라.",
            "HIGH": "[⚠️ 씬 반영] Blueprint 씬들을 충실히 구현하라.",
            "MEDIUM": "[씬 확인] 설계된 씬들이 모두 포함되었는지 확인하라.",
        },
        PromptCategory.DIALOGUE: {
            "CRITICAL": "[🚨 대화 품질] 대화 후 반드시 반응/행동 묘사를 포함하라. 대사만 나열하지 마라. 캐릭터별 말투를 구분하라.",
            "HIGH": "[⚠️ 대화 주의] 대화에 감정과 행동을 곁들여라.",
            "MEDIUM": "[대화 확인] 대화가 자연스러운지 점검하라.",
        },
        PromptCategory.DESCRIPTION: {
            "CRITICAL": "[🚨 감각 묘사 필수] 시각만이 아닌 청각, 촉각, 후각 등 다양한 감각을 포함하라. 추상적 설명 대신 구체적 묘사를 사용하라.",
            "HIGH": "[⚠️ 묘사 강화] 감각적 디테일을 추가하라.",
            "MEDIUM": "[묘사 확인] 묘사가 충분한지 점검하라.",
        },
        PromptCategory.BLUEPRINT_COMPLIANCE: {
            "CRITICAL": "[🚨 Blueprint 준수] Blueprint의 핵심 요소를 반드시 포함하라. ending_hook을 원고 끝에 반영하라.",
            "HIGH": "[⚠️ 설계 준수] Blueprint 설계를 충실히 따르라.",
            "MEDIUM": "[설계 확인] Blueprint와 일치하는지 확인하라.",
        },
        PromptCategory.VILLAIN_INTELLIGENCE: {
            "CRITICAL": "[🚨 악역 지능 보호] 악역을 멍청하게 만들지 마라. 악역도 합리적으로 사고하고 경계하는 인물이다. 주인공 과소평가 클리셰를 피하라.",
            "HIGH": "[⚠️ 악역 주의] 악역이 합리적인 판단을 하도록 묘사하라.",
            "MEDIUM": "[악역 확인] 악역의 행동이 지능적인지 점검하라.",
        },
    }

    def __init__(self, failure_learner=None) -> None:
        """
        Args:
            failure_learner: FailureLearner 인스턴스 (없으면 기본 가중치 사용)
        """
        self.failure_learner = failure_learner
        self.category_weights: dict[PromptCategory, float] = {}
        self._update_weights()

    def _update_weights(self) -> None:
        """실패 데이터 기반 가중치 업데이트"""
        # 기본 가중치 초기화
        for cat in PromptCategory:
            self.category_weights[cat] = 0.0

        if not self.failure_learner:
            return

        # 최근 실패 기록 분석 (최근 50건)
        recent_failures = self.failure_learner.get_recent_failures(limit=50)

        if not recent_failures:
            return

        # 실패 사유에서 카테고리 추출
        category_counts = Counter()

        for failure in recent_failures:
            reason = (
                getattr(failure, "reason", "") if not isinstance(failure, dict) else failure.get("reason", "")
            )  # [V70] FailureRecord dataclass 대응
            detected_cats = self._detect_categories(reason)
            for cat in detected_cats:
                category_counts[cat] += 1

        # 가중치 계산 (정규화)
        total = sum(category_counts.values()) or 1
        for cat, count in category_counts.items():
            self.category_weights[cat] = min(1.0, count / total * 3)  # 최대 1.0

    def _detect_categories(self, text: str) -> list[PromptCategory]:
        """텍스트에서 카테고리 감지"""
        text_lower = text.lower()
        detected = []

        for cat, keywords in self.FAILURE_KEYWORD_MAP.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    detected.append(cat)
                    break

        return detected

    def _get_urgency(self, weight: float) -> str:
        """가중치 → 긴급도 변환"""
        if weight >= 0.7:
            return "CRITICAL"
        elif weight >= 0.4:
            return "HIGH"
        elif weight >= 0.2:
            return "MEDIUM"
        else:
            return "LOW"

    def get_weighted_directives(
        self, agent_type: str = "writer", stage: int = 4, top_n: int = 3
    ) -> list[WeightedDirective]:
        """
        가중치 적용된 지시어 목록 반환

        Args:
            agent_type: "analyst", "architect", "writer"
            stage: 2, 3, 4
            top_n: 반환할 최대 지시어 수

        Returns:
            가중치 순으로 정렬된 WeightedDirective 목록
        """
        self._update_weights()  # 최신 데이터 반영

        # 에이전트/스테이지별 관련 카테고리 필터
        relevant_categories = self._get_relevant_categories(agent_type, stage)

        directives = []
        for cat in relevant_categories:
            weight = self.category_weights.get(cat, 0.0)
            if weight < 0.1:  # 너무 낮은 가중치는 제외
                continue

            urgency = self._get_urgency(weight)
            if urgency == "LOW":
                continue

            template = self.DIRECTIVE_TEMPLATES.get(cat, {}).get(urgency, "")
            if template:
                directives.append(WeightedDirective(category=cat, weight=weight, directive=template, urgency=urgency))

        # 가중치 순 정렬
        directives.sort(key=lambda x: x.weight, reverse=True)
        return directives[:top_n]

    def _get_relevant_categories(self, agent_type: str, stage: int) -> list[PromptCategory]:
        """에이전트/스테이지별 관련 카테고리"""

        if agent_type == "analyst":
            return [PromptCategory.PACING, PromptCategory.RELATIONSHIP, PromptCategory.SCENE_STRUCTURE]
        elif agent_type == "architect":
            return [
                PromptCategory.CONTINUITY,
                PromptCategory.PACING,
                PromptCategory.SCENE_STRUCTURE,
                PromptCategory.ITEM_MANAGEMENT,
                PromptCategory.RELATIONSHIP,
            ]
        elif agent_type == "writer":
            return [
                PromptCategory.CONTINUITY,
                PromptCategory.ITEM_MANAGEMENT,
                PromptCategory.RELATIONSHIP,
                PromptCategory.CHARACTER,
                PromptCategory.DIALOGUE,
                PromptCategory.DESCRIPTION,
                PromptCategory.BLUEPRINT_COMPLIANCE,
                PromptCategory.VILLAIN_INTELLIGENCE,
                PromptCategory.PACING,
            ]
        else:
            return list(PromptCategory)

    def get_weighted_prompt(self, agent_type: str = "writer", stage: int = 4, top_n: int = 3) -> str:
        """
        에이전트에 주입할 가중치 프롬프트 생성

        Args:
            agent_type: "analyst", "architect", "writer"
            stage: 2, 3, 4
            top_n: 포함할 최대 지시어 수

        Returns:
            주입용 프롬프트 문자열
        """
        directives = self.get_weighted_directives(agent_type, stage, top_n)

        if not directives:
            return ""

        lines = ["[V53.1 Dynamic Prompt Weighting - 취약 영역 강조]"]
        lines.append("최근 REJECT 패턴 분석 결과, 아래 영역에 특별히 주의하십시오:\n")

        for i, d in enumerate(directives, 1):
            lines.append(f"{i}. {d.directive}")

        return "\n".join(lines)

    def get_weight_summary(self) -> dict[str, float]:
        """현재 카테고리별 가중치 요약"""
        self._update_weights()
        return {cat.value: weight for cat, weight in self.category_weights.items() if weight > 0}

    def force_add_weight(self, category: PromptCategory, weight: float = 0.5) -> None:
        """특정 카테고리 가중치 강제 추가 (디버깅/테스트용)"""
        self.category_weights[category] = min(1.0, self.category_weights.get(category, 0) + weight)
