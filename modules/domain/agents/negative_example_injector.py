"""
[V60.12] Negative Example Injector
실패 사례 기반 Few-Shot 학습 - "하지 말아야 할 것" 명시

목적:
- 과거 REJECT 사례를 분석하여 동일 실수 방지
- Contrastive Learning으로 LLM이 경계해야 할 패턴 학습
- 초기 통과율 극대화

비용: $0 (프롬프트 주입만)
"""

import json
import re
from typing import Dict, List, Any, Optional


# 무협 장르 기본 실패 사례 라이브러리
WUXIA_NEGATIVE_EXAMPLES = {
    "duplicate_acquisition": {
        "description": "이미 획득한 아이템 재획득",
        "bad_examples": [
            {
                "context": "Arc 1에서 대도를 획득한 상태",
                "mistake": "Arc 2의 items_acquired에 '대도' 포함",
                "why_wrong": "대도는 Arc 1에서 이미 획득. 다시 획득할 수 없음.",
                "correct": "items_acquired에서 '대도' 제외. 대신 '새로운 무공 비급' 등 새 아이템"
            },
            {
                "context": "Arc 2에서 철혈사자패를 수여받은 상태",
                "mistake": "Arc 3에서 다시 철혈사자패를 수여받는 장면",
                "why_wrong": "이미 수여받은 것을 다시 수여받을 수 없음",
                "correct": "기존 철혈사자패를 '활용'하는 장면으로 변경"
            }
        ]
    },
    "location_teleport": {
        "description": "위치 순간이동",
        "bad_examples": [
            {
                "context": "Arc 1 종료 시 철혈단 본거지에 있음",
                "mistake": "Arc 2 시작 위치가 '흑풍문 본거지'",
                "why_wrong": "이전 Arc 종료 위치에서 시작해야 함",
                "correct": "arc_start_state.location = '철혈단 본거지'로 시작, 이동 장면 포함"
            }
        ]
    },
    "state_discontinuity": {
        "description": "상태 불연속",
        "bad_examples": [
            {
                "context": "Arc 1 종료 시 왼팔 중상, 내공 60%",
                "mistake": "Arc 2 시작에서 부상 언급 없이 정상 활동",
                "why_wrong": "중상은 회복 과정 없이 사라지지 않음",
                "correct": "Arc 2 초반에 치료 장면 포함 또는 부상 상태로 행동 제한"
            },
            {
                "context": "Arc 2에서 내공 30% 손실",
                "mistake": "Arc 3 시작에서 내공 100%",
                "why_wrong": "내공은 수련/회복 과정 없이 회복되지 않음",
                "correct": "Arc 3 초반 내공 회복 수련 장면 포함"
            }
        ]
    },
    "joint_docs_mismatch": {
        "description": "joint_docs와 tactical_doc 불일치",
        "bad_examples": [
            {
                "context": "tactical_doc 마지막 화에서 흑풍문 전초기지로 이동",
                "mistake": "joint_docs.final_location이 여전히 '철혈단 본거지'",
                "why_wrong": "joint_docs는 tactical_doc 마지막 상태를 정확히 반영해야 함",
                "correct": "joint_docs.final_location = '흑풍문 전초기지'"
            },
            {
                "context": "tactical_doc에서 금창약 사용",
                "mistake": "joint_docs.physical_inventory에 여전히 금창약 포함",
                "why_wrong": "소모된 아이템은 소지품에서 제외",
                "correct": "physical_inventory에서 금창약 제거, items_consumed에 추가"
            }
        ]
    },
    "tactical_doc_quality": {
        "description": "tactical_doc 품질 문제",
        "bad_examples": [
            {
                "context": "Arc 3 tactical_doc 작성",
                "mistake": "1500자 분량의 간략한 요약만 작성",
                "why_wrong": "tactical_doc은 최소 3000자 이상의 상세 시나리오 필요",
                "correct": "각 화별 800자 이상, 총 4000자 이상의 구체적 장면 묘사"
            },
            {
                "context": "5개 화 구성 Arc",
                "mistake": "화 구분 없이 하나의 흐름으로 작성",
                "why_wrong": "'제 N화' 형식으로 명확히 구분 필요",
                "correct": "'제 1화: ...', '제 2화: ...' 형식으로 5개 화 명확 구분"
            }
        ]
    },
    "power_inflation": {
        "description": "파워 인플레이션",
        "bad_examples": [
            {
                "context": "주인공 삼류 수준에서 시작",
                "mistake": "Arc 1에서 바로 일류 경지 도달",
                "why_wrong": "한 Arc에서 2단계 이상 성장은 비현실적",
                "correct": "Arc 1: 삼류→이류, Arc 2: 이류→일류 점진적 성장"
            }
        ]
    }
}


class NegativeExampleInjector:
    """
    [V60.12] Negative Example Injector

    실패 사례 기반 프롬프트 강화
    """

    def __init__(self, genre: str = "wuxia"):
        self.genre = genre
        self.examples_library = self._load_examples_library(genre)
        self.rejection_history: List[Dict] = []

    def _load_examples_library(self, genre: str) -> Dict:
        """장르별 실패 사례 라이브러리 로드"""
        if genre == "wuxia":
            return WUXIA_NEGATIVE_EXAMPLES
        # 다른 장르는 기본 라이브러리 사용
        return WUXIA_NEGATIVE_EXAMPLES

    def record_rejection(self, arc: Dict, rejection_reason: str, category: str):
        """REJECT 사례 기록"""
        self.rejection_history.append({
            "arc_no": arc.get("arc_no", "?"),
            "reason": rejection_reason,
            "category": category,
            "items_acquired": arc.get("state_constraints", {}).get("items_acquired", []),
            "grants_received": arc.get("state_constraints", {}).get("grants_received", []),
            "timestamp": "now"
        })

        # 최근 20개만 유지
        if len(self.rejection_history) > 20:
            self.rejection_history = self.rejection_history[-20:]

    def generate_injection(self, context: Dict = None) -> str:
        """Analyst 프롬프트에 주입할 실패 사례 텍스트 생성"""
        lines = [
            "",
            "╔" + "═" * 70 + "╗",
            "║" + " [V60.12 NEGATIVE EXAMPLES - 절대 하지 말아야 할 것] ".center(70) + "║",
            "╚" + "═" * 70 + "╝",
            "",
            "다음은 과거에 REJECT된 실패 사례입니다.",
            "동일한 실수를 반복하지 마세요!",
            ""
        ]

        # 최근 REJECT 히스토리 기반 사례
        if self.rejection_history:
            lines.append("━━━ 최근 REJECT 사례 ━━━")
            for rej in self.rejection_history[-5:]:
                lines.append(f"❌ Arc {rej['arc_no']}: {rej['reason']}")
            lines.append("")

        # 기본 실패 사례 라이브러리
        lines.append("━━━ 일반적인 실패 패턴 ━━━")
        lines.append("")

        # 상황에 맞는 사례 선택
        relevant_categories = self._select_relevant_categories(context)

        for category in relevant_categories[:4]:  # 최대 4개 카테고리
            cat_data = self.examples_library.get(category, {})
            if not cat_data:
                continue

            lines.append(f"▶ {cat_data.get('description', category)}")
            lines.append("")

            for ex in cat_data.get("bad_examples", [])[:2]:  # 카테고리당 최대 2개
                lines.append(f"  상황: {ex.get('context', '')}")
                lines.append(f"  ❌ 잘못된 예: {ex.get('mistake', '')}")
                lines.append(f"  → 왜 틀렸나: {ex.get('why_wrong', '')}")
                lines.append(f"  ✅ 올바른 예: {ex.get('correct', '')}")
                lines.append("")

        # 최종 경고
        lines.append("━" * 60)
        lines.append("⚠️ 위 실패 사례를 절대 반복하지 마세요!")
        lines.append("⚠️ 특히 '이미 획득한 아이템 재획득'은 즉시 REJECT됩니다!")
        lines.append("")

        return "\n".join(lines)

    def _select_relevant_categories(self, context: Dict = None) -> List[str]:
        """상황에 맞는 카테고리 선택"""
        # 기본 우선순위
        priority = [
            "duplicate_acquisition",
            "location_teleport",
            "state_discontinuity",
            "joint_docs_mismatch",
            "tactical_doc_quality",
            "power_inflation"
        ]

        # 최근 REJECT 히스토리 기반 우선순위 조정
        recent_categories = [r.get("category") for r in self.rejection_history[-5:]]
        for cat in recent_categories:
            if cat in priority:
                priority.remove(cat)
                priority.insert(0, cat)  # 최근 실패한 카테고리 우선

        return priority

    def generate_self_check_prompt(self) -> str:
        """생성 후 자가 검증 프롬프트"""
        return """
### [V60.12 자가 검증 체크리스트 - 제출 전 필수 확인]

다음 항목을 모두 확인하고 "예"로 답할 수 있어야 합니다:

□ items_acquired에 이전 Arc에서 이미 획득한 아이템이 없는가?
□ grants_received에 이전 Arc에서 이미 수여받은 것이 없는가?
□ arc_start_state.location이 이전 Arc의 final_location과 일치하는가?
□ 이전 Arc의 부상 상태가 적절히 계승되었는가?
□ tactical_doc이 3000자 이상인가?
□ tactical_doc에 '제 N화' 형식으로 5개 화가 구분되어 있는가?
□ joint_docs.final_location이 tactical_doc 마지막 화 종료 위치와 일치하는가?
□ joint_docs.physical_inventory에 소모된 아이템이 제외되어 있는가?

위 항목 중 하나라도 "아니오"면 수정 후 제출하세요!
"""

    def get_targeted_warning(self, issue_type: str) -> str:
        """특정 이슈에 대한 타겟 경고 생성"""
        warnings = {
            "duplicate_acquisition": """
⚠️ [중복 획득 경고]
이전 Arc에서 이미 획득한 아이템을 다시 획득하려 합니다!
→ items_acquired 목록에서 해당 아이템을 제거하세요.
→ 대신 '새로운' 아이템을 획득하거나, 기존 아이템을 '활용'하는 장면으로 변경하세요.
""",
            "location_mismatch": """
⚠️ [위치 불일치 경고]
Arc 시작 위치가 이전 Arc 종료 위치와 다릅니다!
→ arc_start_state.location을 이전 Arc의 final_location과 동일하게 수정하세요.
→ 위치 이동이 필요하면 Arc 초반에 이동 장면을 포함하세요.
""",
            "state_discontinuity": """
⚠️ [상태 불연속 경고]
이전 Arc의 부상/내공 상태가 무시되었습니다!
→ 부상이 있었다면 회복 과정을 포함하거나 부상 상태로 활동을 제한하세요.
→ 내공 손실이 있었다면 회복 수련 장면을 포함하세요.
""",
            "joint_docs_mismatch": """
⚠️ [Joint Docs 불일치 경고]
joint_docs가 tactical_doc 내용과 일치하지 않습니다!
→ final_location을 tactical_doc 마지막 화 종료 위치로 수정하세요.
→ physical_inventory를 정확히 업데이트하세요.
"""
        }
        return warnings.get(issue_type, "⚠️ 제약 조건을 다시 확인하세요.")


def create_negative_example_injector(genre: str = "wuxia") -> NegativeExampleInjector:
    """NegativeExampleInjector 생성 헬퍼"""
    return NegativeExampleInjector(genre)
