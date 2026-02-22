"""
[V52.4] Cross-Agent Verification (교차 에이전트 검증)
에이전트 간 설계 준수 여부를 검증하는 시스템

핵심: 상위 에이전트의 설계를 하위 에이전트가 제대로 따르는지 확인

원리:
1. Architect → Analyst 설계 준수 검증 (Stage 3)
   - Arc tactical_doc의 핵심 요소가 Blueprint에 반영되었는지
2. Writer → Blueprint 준수 검증 (Stage 4)
   - Blueprint의 씬/요소가 원고에 반영되었는지

비용: +$0.01/stage (flash 모델 사용)

사용:
    verifier = CrossAgentVerifier(api_client)
    result = verifier.verify_architect_compliance(blueprint, arc_design)
    result = verifier.verify_writer_compliance(manuscript, blueprint)
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from modules.core.constants import ManuscriptLimits  # [V64.P4]


class ComplianceLevel(Enum):
    """준수 수준"""

    FULL = "full"  # 완전 준수
    PARTIAL = "partial"  # 부분 준수 (경고)
    VIOLATION = "violation"  # 위반 (재생성 필요)


@dataclass
class ComplianceResult:
    """검증 결과"""

    level: ComplianceLevel
    score: float  # 0-1
    violations: list[dict[str, str]]  # {"item": ..., "reason": ...}
    warnings: list[dict[str, str]]
    details: str
    should_regenerate: bool


class CrossAgentVerifier:
    """교차 에이전트 검증기"""

    # Architect→Arc 검증 프롬프트
    ARCHITECT_COMPLIANCE_PROMPT = """당신은 설계 준수 검증관입니다.

[Arc 전술 설계 (상위 설계)]
{arc_design}

[생성된 Blueprint (하위 구현)]
{blueprint}

Arc 설계의 핵심 요소가 Blueprint에 제대로 반영되었는지 검증하세요.

검증 항목:
1. **핵심 이벤트 반영**: Arc에서 지정한 주요 사건이 Blueprint 씬에 포함되어 있는가?
2. **캐릭터 등장**: Arc에서 등장해야 할 캐릭터들이 Blueprint에 있는가?
3. **아이템/획득물**: Arc에서 획득/사용되어야 할 아이템이 반영되었는가?
4. **관계 변화**: Arc에서 계획된 관계 변화가 Blueprint에 녹아있는가?
5. **범위 준수**: Blueprint가 해당 화의 범위를 넘어서지 않았는가?

JSON 형식으로 응답:
```json
{
    "compliance_score": 0.0-1.0,
    "violations": [
        {"item": "핵심이벤트X 누락", "reason": "Arc에서 필수로 지정된 대결 씬이 없음"}
    ],
    "warnings": [
        {"item": "캐릭터Y 약화", "reason": "등장은 하지만 역할이 축소됨"}
    ],
    "summary": "전체 평가 요약"
}
```"""

    # Writer→Blueprint 검증 프롬프트
    WRITER_COMPLIANCE_PROMPT = """당신은 원고 준수 검증관입니다.

[Blueprint 설계 (상위 설계)]
{blueprint}

[생성된 원고 (하위 구현)]
{manuscript}

Blueprint의 핵심 요소가 원고에 제대로 반영되었는지 검증하세요.

검증 항목:
1. **씬 반영**: Blueprint의 모든 씬이 원고에 포함되어 있는가?
2. **클리프행어**: Blueprint의 ending_hook이 원고 끝에 반영되었는가?
3. **핵심 대사/행동**: Blueprint에서 강조된 대사나 행동이 원고에 있는가?
4. **감정 곡선**: Blueprint의 tension_flow가 원고에서 느껴지는가?
5. **범위 준수**: 원고가 Blueprint 범위를 넘어서 다음 화 내용을 포함하지 않았는가?

JSON 형식으로 응답:
```json
{
    "compliance_score": 0.0-1.0,
    "violations": [
        {"item": "scene_3 누락", "reason": "Blueprint의 3번 씬이 완전히 생략됨"}
    ],
    "warnings": [
        {"item": "클리프행어 약화", "reason": "ending_hook이 있지만 임팩트가 약함"}
    ],
    "summary": "전체 평가 요약"
}
```"""

    def __init__(self, api_client, model: str = "gemini-2.5-flash"):
        """
        Args:
            api_client: Google GenAI 클라이언트
            model: 검증에 사용할 모델 (빠른 모델 권장)
        """
        self.client = api_client
        self.model = model
        self.enabled = True

    def _call_llm(self, prompt: str, temperature: float = 0.1) -> str:
        """LLM 호출"""
        try:
            response = self.client.models.generate_content(
                model=self.model, contents=prompt, config={"temperature": temperature, "max_output_tokens": 2048}
            )
            return response.text or ""  # [V70] None 방어
        except Exception as e:
            logging.warning(f"[CrossAgentVerifier] LLM 호출 실패: {e}")
            return ""

    def _parse_result(self, response_text: str) -> dict[str, Any]:
        """응답 파싱"""
        try:
            # JSON 블록 추출
            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                # 직접 JSON 시도
                parsed = json.loads(response_text)

            if isinstance(parsed, list):
                parsed = parsed[0] if parsed and isinstance(parsed[0], dict) else {}
            if isinstance(parsed, dict):
                return parsed
            # 직접 JSON 시도
            return {"compliance_score": 0.7, "violations": [], "warnings": [], "summary": "파싱 실패 - 기본값 반환"}
        except (json.JSONDecodeError, ValueError):  # [V64.P4] JSON parse failure
            return {"compliance_score": 0.7, "violations": [], "warnings": [], "summary": "파싱 실패 - 기본값 반환"}

    def _python_precheck_architect(self, blueprint: dict[str, Any], arc_design: dict[str, Any]) -> list[dict[str, str]]:
        """
        Python 기반 빠른 Architect 준수 체크 (LLM 비용 0원)
        """
        violations = []

        # 1. 필수 씬 개수 체크
        scene_breakdown = blueprint.get("scene_breakdown", {})
        if not isinstance(scene_breakdown, dict):
            scene_breakdown = {}
        min_scenes = arc_design.get("min_scenes", 4)
        if len(scene_breakdown) < min_scenes:
            violations.append(
                {"item": "씬 개수 부족", "reason": f"최소 {min_scenes}개 씬 필요, 현재 {len(scene_breakdown)}개"}
            )

        # 2. 핵심 키워드 반영 체크
        arc_keywords = arc_design.get("core_keywords", [])
        if not arc_keywords and "tactical_doc" in arc_design:
            # tactical_doc에서 키워드 추출 시도
            doc = arc_design.get("tactical_doc", "")
            if isinstance(doc, str):
                # 따옴표로 감싼 단어들 추출
                arc_keywords = re.findall(r'[「『"\'](.*?)[」』"\']', doc)

        blueprint_text = json.dumps(blueprint, ensure_ascii=False)
        missing_keywords = []
        for kw in arc_keywords[:5]:  # 상위 5개만
            if kw and kw not in blueprint_text:
                missing_keywords.append(kw)

        if missing_keywords:
            violations.append(
                {"item": "핵심 키워드 누락", "reason": f"Arc 설계 키워드 미반영: {', '.join(missing_keywords[:3])}"}
            )

        # 3. 클리프행어 존재 체크
        ending_hook = blueprint.get("ending_hook") or blueprint.get("cliffhanger")
        if not ending_hook:
            violations.append({"item": "클리프행어 누락", "reason": "ending_hook 또는 cliffhanger 필드가 비어있음"})

        return violations

    def _python_precheck_writer(self, manuscript: str, blueprint: dict[str, Any]) -> list[dict[str, str]]:
        """
        Python 기반 빠른 Writer 준수 체크 (LLM 비용 0원)
        """
        violations = []

        # 1. 최소 길이 체크
        if len(manuscript) < ManuscriptLimits.MIN_LENGTH:  # [V64.P4]
            violations.append(
                {"item": "분량 부족", "reason": f"최소 {ManuscriptLimits.MIN_LENGTH}자 필요, 현재 {len(manuscript)}자"}
            )

        # 2. 씬 반영 체크 (휴리스틱)
        scene_breakdown = blueprint.get("scene_breakdown", {})
        if not isinstance(scene_breakdown, dict):
            scene_breakdown = {}
        if scene_breakdown:
            # 각 씬의 핵심 키워드가 원고에 있는지 체크
            scene_count = len(scene_breakdown)
            reflected_count = 0

            for scene_id, scene_data in scene_breakdown.items():
                if isinstance(scene_data, dict):
                    desc = scene_data.get("description", "")
                    # 씬 설명에서 핵심 단어 추출
                    keywords = re.findall(r"[\w가-힣]+", desc)
                    significant_words = [w for w in keywords if len(w) >= 2][:3]

                    # 원고에 하나라도 있으면 반영된 것으로 간주
                    if any(w in manuscript for w in significant_words):
                        reflected_count += 1

            if scene_count > 0:
                reflection_rate = reflected_count / scene_count
                if reflection_rate < 0.5:
                    violations.append(
                        {
                            "item": "씬 반영 부족",
                            "reason": f"{scene_count}개 씬 중 {reflected_count}개만 감지됨 ({reflection_rate:.0%})",
                        }
                    )

        # 3. 클리프행어 반영 체크
        ending_hook = blueprint.get("ending_hook") or blueprint.get("cliffhanger", "")
        if ending_hook and isinstance(ending_hook, str):
            # 원고 마지막 500자에서 훅 키워드 체크
            ending_part = manuscript[-500:] if len(manuscript) > 500 else manuscript
            hook_keywords = re.findall(r"[\w가-힣]{2,}", ending_hook)[:3]

            if hook_keywords and not any(kw in ending_part for kw in hook_keywords):
                violations.append(
                    {"item": "클리프행어 미반영", "reason": f"ending_hook '{ending_hook[:30]}...'이 원고 끝에 없음"}
                )

        # 4. 범위 초과 체크
        max_expected_length = len(scene_breakdown) * 1500 * 1.5 if scene_breakdown else 12000
        if len(manuscript) > max_expected_length:
            violations.append(
                {"item": "범위 초과 의심", "reason": f"예상 최대 {max_expected_length}자, 현재 {len(manuscript)}자"}
            )

        return violations

    def verify_architect_compliance(
        self, blueprint: dict[str, Any], arc_design: dict[str, Any], use_llm: bool = True
    ) -> ComplianceResult:
        """
        Architect가 Arc 설계를 준수했는지 검증

        Args:
            blueprint: Architect가 생성한 Blueprint
            arc_design: Analyst가 작성한 Arc 전술 설계
            use_llm: LLM 검증 사용 여부 (False면 Python만)

        Returns:
            ComplianceResult
        """
        if not self.enabled:
            return ComplianceResult(
                level=ComplianceLevel.FULL,
                score=1.0,
                violations=[],
                warnings=[],
                details="검증 비활성화",
                should_regenerate=False,
            )

        # Phase 1: Python Precheck (무료)
        py_violations = self._python_precheck_architect(blueprint, arc_design)

        # 명백한 위반이 있으면 LLM 생략
        if len(py_violations) >= 2:
            return ComplianceResult(
                level=ComplianceLevel.VIOLATION,
                score=0.3,
                violations=py_violations,
                warnings=[],
                details="Python precheck에서 다중 위반 감지",
                should_regenerate=True,
            )

        # Phase 2: LLM Deep Check (선택적)
        if use_llm:
            arc_text = json.dumps(arc_design, ensure_ascii=False, indent=2)[:4000]
            bp_text = json.dumps(blueprint, ensure_ascii=False, indent=2)[:6000]

            # [V70] .format() → .replace() (템플릿 내 JSON 예시 브레이스 충돌 방지)
            prompt = self.ARCHITECT_COMPLIANCE_PROMPT.replace("{arc_design}", arc_text).replace("{blueprint}", bp_text)

            response = self._call_llm(prompt)
            result = self._parse_result(response)

            violations = py_violations + result.get("violations", [])
            warnings = result.get("warnings", [])
            try:
                score = float(result.get("compliance_score", 0.7))
            except (ValueError, TypeError):
                score = 0.7

            # Python 위반이 있으면 점수 감점
            if py_violations:
                score = max(0.0, score - 0.2 * len(py_violations))
        else:
            violations = py_violations
            warnings = []
            score = 1.0 - (0.2 * len(py_violations))

        # 결과 판정
        if score >= 0.8 and not violations:
            level = ComplianceLevel.FULL
            should_regenerate = False
        elif score >= 0.5 or len(violations) <= 1:
            level = ComplianceLevel.PARTIAL
            should_regenerate = False
        else:
            level = ComplianceLevel.VIOLATION
            should_regenerate = True

        return ComplianceResult(
            level=level,
            score=score,
            violations=violations,
            warnings=warnings,
            details=result.get("summary", "") if use_llm else "Python-only 검증",
            should_regenerate=should_regenerate,
        )

    def verify_writer_compliance(
        self, manuscript: str, blueprint: dict[str, Any], use_llm: bool = True
    ) -> ComplianceResult:
        """
        Writer가 Blueprint를 준수했는지 검증

        Args:
            manuscript: Writer가 생성한 원고
            blueprint: Architect가 작성한 Blueprint
            use_llm: LLM 검증 사용 여부

        Returns:
            ComplianceResult
        """
        if not self.enabled:
            return ComplianceResult(
                level=ComplianceLevel.FULL,
                score=1.0,
                violations=[],
                warnings=[],
                details="검증 비활성화",
                should_regenerate=False,
            )

        # Phase 1: Python Precheck (무료)
        py_violations = self._python_precheck_writer(manuscript, blueprint)

        # 명백한 위반이 있으면 LLM 생략
        if len(py_violations) >= 2:
            return ComplianceResult(
                level=ComplianceLevel.VIOLATION,
                score=0.3,
                violations=py_violations,
                warnings=[],
                details="Python precheck에서 다중 위반 감지",
                should_regenerate=True,
            )

        # Phase 2: LLM Deep Check (선택적)
        if use_llm:
            bp_text = json.dumps(blueprint, ensure_ascii=False, indent=2)[:4000]
            ms_text = manuscript[:8000]

            # [V70] .format() → .replace() (템플릿 내 JSON 예시 브레이스 충돌 방지)
            prompt = self.WRITER_COMPLIANCE_PROMPT.replace("{blueprint}", bp_text).replace("{manuscript}", ms_text)

            response = self._call_llm(prompt)
            result = self._parse_result(response)

            violations = py_violations + result.get("violations", [])
            warnings = result.get("warnings", [])
            try:
                score = float(result.get("compliance_score", 0.7))
            except (ValueError, TypeError):
                score = 0.7

            if py_violations:
                score = max(0.0, score - 0.2 * len(py_violations))
        else:
            violations = py_violations
            warnings = []
            score = 1.0 - (0.2 * len(py_violations))

        # 결과 판정
        if score >= 0.8 and not violations:
            level = ComplianceLevel.FULL
            should_regenerate = False
        elif score >= 0.5 or len(violations) <= 1:
            level = ComplianceLevel.PARTIAL
            should_regenerate = False
        else:
            level = ComplianceLevel.VIOLATION
            should_regenerate = True

        return ComplianceResult(
            level=level,
            score=score,
            violations=violations,
            warnings=warnings,
            details=result.get("summary", "") if use_llm else "Python-only 검증",
            should_regenerate=should_regenerate,
        )

    def generate_feedback(self, result: ComplianceResult, target: str = "general") -> str:
        """
        검증 결과를 기반으로 재생성 가이드 생성

        Args:
            result: ComplianceResult
            target: "architect" 또는 "writer"

        Returns:
            재생성 시 참고할 피드백 문자열
        """
        if result.level == ComplianceLevel.FULL:
            return ""

        feedback_parts = [f"[V52.4 Cross-Agent 검증 피드백 - {target.upper()}]"]
        feedback_parts.append(f"준수 점수: {result.score:.0%}")

        if result.violations:
            feedback_parts.append("\n⛔ 위반 사항 (반드시 수정):")
            for v in result.violations:
                feedback_parts.append(f"  - {v['item']}: {v['reason']}")

        if result.warnings:
            feedback_parts.append("\n⚠️ 경고 사항 (권장 수정):")
            for w in result.warnings:
                feedback_parts.append(f"  - {w['item']}: {w['reason']}")

        if result.details:
            feedback_parts.append(f"\n📝 상세: {result.details}")

        return "\n".join(feedback_parts)

    def quick_check(self, content: str, reference: dict[str, Any], check_type: str) -> tuple[bool, list[str]]:
        """
        빠른 준수 체크 (Python only, LLM 비용 0원)

        Args:
            content: 검증할 콘텐츠 (원고 텍스트 또는 Blueprint JSON 문자열)
            reference: 참조 설계
            check_type: "architect" 또는 "writer"

        Returns:
            (통과 여부, 위반 목록)
        """
        if check_type == "architect":
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse failure
                    return False, ["Blueprint JSON 파싱 실패"]
            violations = self._python_precheck_architect(content, reference)
        elif check_type == "writer":
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)
            violations = self._python_precheck_writer(content, reference)
        else:
            return True, []

        passed = len(violations) == 0
        messages = [f"{v['item']}: {v['reason']}" for v in violations]
        return passed, messages
