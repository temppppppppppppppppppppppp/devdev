"""
[V60.12] Arc Critic
생성된 Arc를 즉시 비평하고 구체적인 수정 지시 생성

목적:
- ContinuityInspector 전에 자체 비평으로 문제 조기 발견
- 문제 발견 시 구체적인 수정 방향 제시
- 수정된 Arc 반환 (가능한 경우)

비용: ~$0.02-0.04/Arc (gemini-2.5-pro 사용)
"""

import json
import logging

from modules.core.arc_summary_utils import generate_prev_arc_summary  # [V64.P4]
from modules.core.prompt_loader import SafeDict

from .base_agent import BaseAgent

ARC_CRITIQUE_PROMPT = """
[V60.12 ARC CRITIC - 생성 Arc 즉시 비평]

당신은 엄격한 Arc 품질 검사관입니다.
생성된 Arc를 다음 기준으로 철저히 비평하세요.

### [생성된 Arc]
{generated_arc}

### [이전 Arc 요약]
{prev_arc_summary}

### [제약 조건]
{constraints}

### [비평 기준 - 각 항목 0-10점]

1. **아이템 연속성 (10점)**
   - items_acquired에 이미 획득한 아이템이 포함되었는가?
   - 이전 Arc 소지품이 누락되지 않았는가?
   - 새 획득 아이템에 타당한 맥락이 있는가?

2. **위치 연속성 (10점)**
   - arc_start_state.location이 이전 Arc 종료 위치와 일치하는가?
   - 위치 이동이 논리적인가?

3. **상태 연속성 (10점)**
   - 부상 상태가 적절히 계승되었는가?
   - 내공 수치가 연속적인가?
   - 상태 회복에 합리적인 설명이 있는가?

4. **수여물 타임라인 (10점)**
   - grants_received에 이미 수여받은 것이 포함되었는가?
   - 새 수여물에 적절한 맥락이 있는가?

5. **tactical_doc 품질 (10점)**
   - 충분한 분량인가? (최소 3000자 권장)
   - 화별 구분이 명확한가?
   - 구체적인 장면 묘사가 있는가?

6. **joint_docs 정합성 (10점)**
   - final_location이 tactical_doc 마지막 화와 일치하는가?
   - physical_inventory가 정확한가?
   - world_joint가 의미있는 변화를 담고 있는가?

7. **서사적 일관성 (10점)**
   - 이전 Arc의 복선/갈등이 적절히 이어지는가?
   - 캐릭터 행동이 일관적인가?
   - 긴장감 곡선이 적절한가?

### [출력 형식 - JSON]

{{
    "scores": {{
        "item_continuity": 8,
        "location_continuity": 10,
        "state_continuity": 7,
        "grant_timeline": 10,
        "tactical_quality": 6,
        "joint_docs_accuracy": 5,
        "narrative_coherence": 8
    }},
    "total_score": 54,
    "verdict": "NEEDS_REVISION",
    "critical_issues": [
        {{
            "category": "joint_docs_accuracy",
            "severity": "HIGH",
            "issue": "final_location이 tactical_doc 마지막 화의 종료 위치와 불일치",
            "current": "철혈단 본거지",
            "expected": "흑풍문 전초기지",
            "fix_instruction": "joint_docs.final_location을 '흑풍문 전초기지'로 수정"
        }}
    ],
    "warnings": [
        {{
            "category": "tactical_quality",
            "issue": "tactical_doc 분량이 2500자로 권장치(3000자) 미달",
            "suggestion": "제3화 전투 장면 상세화 권장"
        }}
    ],
    "auto_fixes": {{
        "joint_docs": {{
            "final_location": "흑풍문 전초기지",
            "physical_inventory": ["대도", "철혈사자패"]
        }}
    }},
    "revision_priority": [
        "1. joint_docs.final_location 수정 (필수)",
        "2. tactical_doc 분량 보강 (권장)",
        "3. 제4화 긴장감 강화 (권장)"
    ]
}}

### verdict 기준:
- PASS (70점 이상, CRITICAL 없음): 수정 없이 통과
- NEEDS_REVISION (50-69점 또는 CRITICAL 있음): auto_fixes 적용 후 재검토
- REJECT (50점 미만): 완전 재생성 필요

반드시 유효한 JSON만 출력하세요.
"""


class ArcCritic(BaseAgent):
    """
    [V60.12] Arc Critic

    생성된 Arc를 즉시 비평하고 자동 수정
    """

    def __init__(
        self, context, client, model_tier: str = "gemini-2.5-flash"
    ):  # [SSOT-P2] 호출부(main_a.py:L1529)가 model_tier 인자를 명시 전달
        # [V60.53] Flash로 변경 - 비평은 Flash로 충분
        super().__init__(context, client, model_tier)
        # [V60.37] 스마트 폴백 (BaseAgent에서 자동 설정)

    def critique(self, generated_arc: dict, prev_arcs: list[dict], constraints: str = "") -> tuple[dict, dict]:
        """
        Arc 비평 및 자동 수정

        Args:
            generated_arc: 생성된 Arc
            prev_arcs: 이전 Arc 리스트
            constraints: 제약 조건 텍스트

        Returns:
            (critique_result, fixed_arc) - 비평 결과와 수정된 Arc
        """
        # 이전 Arc 요약 생성
        prev_summary = self._generate_prev_summary(prev_arcs)

        prompt = ARC_CRITIQUE_PROMPT.format_map(
            SafeDict(
                generated_arc=self._escape_braces(json.dumps(generated_arc, ensure_ascii=False, indent=2)[:18000]),
                prev_arc_summary=self._escape_braces(prev_summary),
                constraints=self._escape_braces(constraints[:9000] if constraints else "(없음)"),
            )
        )

        try:
            # [V60.27] Thinking Level "medium" 적용 - 비평 정확도 향상
            result = self.ask(prompt, temperature=0.2, thinking_level="medium")

            if isinstance(result, str):
                result = self._extract_json_robust(result)  # [V70] bare json.loads → robust 파서

            # 필수 필드 보장
            result = self._ensure_critique_fields(result)

            # 자동 수정 적용
            fixed_arc = self._apply_auto_fixes(generated_arc, result)

            return result, fixed_arc

        except Exception as e:
            logging.warning(f" [Critic] 비평 오류: {str(e)[:50]}")
            # 폴백: Python 기반 간단 검증
            return self._python_critique_fallback(generated_arc, prev_arcs), generated_arc

    def _generate_prev_summary(self, prev_arcs: list[dict]) -> str:
        """[V64.P4] 위임 → modules.core.arc_summary_utils.generate_prev_arc_summary"""
        return generate_prev_arc_summary(prev_arcs, include_energy=False)

    def _ensure_critique_fields(self, result: dict) -> dict:
        """비평 결과 필수 필드 보장"""
        if "scores" not in result:
            result["scores"] = {}

        if "total_score" not in result:
            scores = result["scores"]
            try:
                result["total_score"] = sum(int(v) for v in scores.values()) if scores else 0
            except (ValueError, TypeError):
                result["total_score"] = 0

        if "verdict" not in result:
            try:
                score = int(result["total_score"])
            except (ValueError, TypeError):
                score = 0
            has_critical = len(result.get("critical_issues", [])) > 0
            if score >= 70 and not has_critical:
                result["verdict"] = "PASS"
            elif score >= 50:
                result["verdict"] = "NEEDS_REVISION"
            else:
                result["verdict"] = "REJECT"

        if "critical_issues" not in result:
            result["critical_issues"] = []

        if "warnings" not in result:
            result["warnings"] = []

        if "auto_fixes" not in result:
            result["auto_fixes"] = {}

        if "revision_priority" not in result:
            result["revision_priority"] = []

        return result

    def _apply_auto_fixes(self, arc: dict, critique: dict) -> dict:
        """자동 수정 적용"""
        fixed = json.loads(json.dumps(arc, ensure_ascii=False))  # Deep copy

        auto_fixes = critique.get("auto_fixes", {})

        # joint_docs 수정
        if "joint_docs" in auto_fixes:
            if "joint_docs" not in fixed:
                fixed["joint_docs"] = {}
            for key, value in auto_fixes["joint_docs"].items():
                fixed["joint_docs"][key] = value

        # state_constraints 수정
        # [V60.73] 자동 수정 시 경고 로그 (tactical_doc과 불일치 가능성)
        if "state_constraints" in auto_fixes:
            if "state_constraints" not in fixed:
                fixed["state_constraints"] = {}
            for key, value in auto_fixes["state_constraints"].items():
                old_value = fixed["state_constraints"].get(key)
                if old_value != value:
                    logging.info(f" [V60.73] state_constraints 자동 수정: {key}: {old_value} → {value} (tactical_doc 불일치 주의)"
                    )
                fixed["state_constraints"][key] = value

        # items_acquired 수정 (중복 제거)
        if "remove_items" in auto_fixes:
            items = fixed.get("state_constraints", {}).get("items_acquired", [])
            for item_to_remove in auto_fixes["remove_items"]:
                if item_to_remove in items:
                    items.remove(item_to_remove)

        return fixed

    def _python_critique_fallback(self, arc: dict, prev_arcs: list[dict]) -> dict:
        """LLM 실패 시 Python 폴백 비평"""
        issues = []
        warnings = []
        score = 70  # 기본 점수

        # 1. tactical_doc 분량 체크
        tactical = arc.get("tactical_doc", "")
        # [V60.37] 타입 안전성
        if not isinstance(tactical, str):
            tactical = str(tactical) if tactical else ""
        if len(tactical) < 2000:
            issues.append(
                {
                    "category": "tactical_quality",
                    "severity": "HIGH",
                    "issue": f"tactical_doc 분량 부족: {len(tactical)}자",
                    "fix_instruction": "최소 2000자 이상 작성 필요",
                }
            )
            score -= 15
        elif len(tactical) < 3000:
            warnings.append(
                {"category": "tactical_quality", "issue": f"tactical_doc 분량 미흡: {len(tactical)}자 (권장: 3000자)"}
            )
            score -= 5

        # 2. 필수 필드 체크
        required = ["arc_no", "ep_count", "tactical_doc", "joint_docs", "state_constraints"]
        for field in required:
            if field not in arc or not arc[field]:
                issues.append({"category": "structure", "severity": "HIGH", "issue": f"필수 필드 누락: {field}"})
                score -= 10

        # 3. 중복 아이템 체크
        if prev_arcs:
            # [Sweep-Codex] dict 아이템 방어 (unhashable type 방지)
            def _ikey(x):
                return x.get("name", x.get("item", "")) if isinstance(x, dict) else str(x)

            all_prev_items = set()
            for p in prev_arcs:
                items = p.get("state_constraints", {}).get("items_acquired", [])
                if isinstance(items, list):
                    all_prev_items.update(_ikey(i) for i in items)

            current_items = arc.get("state_constraints", {}).get("items_acquired", [])
            if isinstance(current_items, list):
                duplicates = {_ikey(i) for i in current_items} & all_prev_items
                if duplicates:
                    issues.append(
                        {
                            "category": "item_continuity",
                            "severity": "CRITICAL",
                            "issue": f"중복 아이템 획득: {list(duplicates)}",
                        }
                    )
                    score -= 20

        verdict = (
            "PASS"
            if score >= 70 and not any(i.get("severity") == "CRITICAL" for i in issues)
            else "NEEDS_REVISION"
            if score >= 50
            else "REJECT"
        )

        return {
            "scores": {"overall": score},
            "total_score": score,
            "verdict": verdict,
            "critical_issues": issues,
            "warnings": warnings,
            "auto_fixes": {},
            "revision_priority": [],
        }

    def should_regenerate(self, critique: dict) -> bool:
        """재생성이 필요한지 판단"""
        return critique.get("verdict") == "REJECT"

    def should_apply_fixes(self, critique: dict) -> bool:
        """자동 수정 적용이 필요한지 판단"""
        return critique.get("verdict") == "NEEDS_REVISION" and bool(critique.get("auto_fixes"))

    def get_revision_feedback(self, critique: dict) -> str:
        """재생성 시 피드백 생성"""
        lines = ["[ARC CRITIC 피드백 - 재생성 필요]", ""]

        # Critical issues
        critical_issues = critique.get("critical_issues", [])
        if not isinstance(critical_issues, list):
            critical_issues = []
        for issue in critical_issues:
            if not isinstance(issue, dict):
                continue
            lines.append(f"🚨 [{issue.get('severity', 'HIGH')}] {issue.get('issue', '')}")
            if issue.get("fix_instruction"):
                lines.append(f"   → {issue['fix_instruction']}")

        # Revision priority
        priorities = critique.get("revision_priority", [])
        if priorities:
            lines.append("")
            lines.append("수정 우선순위:")
            for p in priorities[:5]:
                lines.append(f"  {p}")

        return "\n".join(lines)


def create_arc_critic(
    context, client, model_tier: str = "gemini-2.5-flash"
):  # [SSOT-P2] 호출부(main_a.py:L1529)가 model_tier 인자를 명시 전달
    """[V60.53] ArcCritic 생성 헬퍼 - Flash로 변경"""
    return ArcCritic(context, client, model_tier)
