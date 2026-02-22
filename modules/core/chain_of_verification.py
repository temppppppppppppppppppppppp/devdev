"""
[V53.2] Chain-of-Verification (CoVe)
생성 후 자체 사실 검증 체인

핵심: 생성된 내용이 기존 설정과 모순되지 않는지 자체 검증

원리:
1. 생성 완료 후 검증 프롬프트 실행
2. "내가 방금 쓴 내용에서 이전 설정과 모순되는 것은?"
3. 모순 발견 시 수정 제안
4. 심각한 모순은 재생성 트리거

비용: +$0.01/검증

사용:
    cove = ChainOfVerification(api_client)
    result = cove.verify(
        generated_content=manuscript,
        context={"prev_manuscript": prev_text, "hud": hud_data},
        content_type="manuscript"
    )
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class VerificationType(Enum):
    """검증 유형"""

    MANUSCRIPT = "manuscript"
    BLUEPRINT = "blueprint"
    ARC_DESIGN = "arc_design"


class VerificationSeverity(Enum):
    """검증 결과 심각도"""

    NONE = "none"  # 문제 없음
    MINOR = "minor"  # 경미한 불일치 (경고만)
    MAJOR = "major"  # 심각한 모순 (수정 필요)
    CRITICAL = "critical"  # 치명적 오류 (재생성 필요)


@dataclass
class VerificationIssue:
    """검증에서 발견된 이슈"""

    category: str  # "item", "relationship", "timeline", "character", "setting"
    description: str
    location: str  # 문제 위치 (문단 번호 등)
    severity: VerificationSeverity
    suggestion: str  # 수정 제안


@dataclass
class VerificationResult:
    """검증 결과"""

    passed: bool
    severity: VerificationSeverity
    issues: list[VerificationIssue]
    summary: str
    should_regenerate: bool
    correction_hints: str  # 수정 시 참고할 힌트


class ChainOfVerification:
    """사실 검증 체인"""

    VERIFICATION_PROMPT = """당신은 소설 연속성 검증 전문가입니다.

방금 생성된 {content_type}을 검토하고, 주어진 컨텍스트와 모순되는 부분을 찾으세요.

[생성된 내용]
{generated_content}

[참조 컨텍스트]
{context}

다음 관점에서 모순을 검증하세요:

1. **아이템 일관성**: 없는 아이템을 사용하거나, 이미 획득한 아이템을 다시 획득하는가?
2. **관계 일관성**: NPC 관계가 갑자기 바뀌었는가? (적대→충성 같은 급변)
3. **타임라인 일관성**: 시간 순서가 맞는가? 아직 안 일어난 일을 언급하는가?
4. **캐릭터 일관성**: 캐릭터 성격/능력이 갑자기 변했는가?
5. **설정 일관성**: 세계관, 장소, 규칙이 이전과 다른가?
6. **상태 일관성**: 부상, 경지, 컨디션이 직전 상태와 맞는가?

JSON 형식으로 응답:
```json
{{
    "passed": true/false,
    "overall_severity": "none|minor|major|critical",
    "issues": [
        {{
            "category": "item|relationship|timeline|character|setting|state",
            "description": "무엇이 모순되는지 설명",
            "location": "문제 위치 (예: 3번째 문단)",
            "severity": "minor|major|critical",
            "suggestion": "이렇게 수정하면 해결됨"
        }}
    ],
    "summary": "전체 검증 요약 (1-2문장)"
}}
```

모순이 없으면:
```json
{{
    "passed": true,
    "overall_severity": "none",
    "issues": [],
    "summary": "검증 통과: 모순 없음"
}}
```"""

    def __init__(self, api_client, model: str = "gemini-2.5-flash"):
        """
        Args:
            api_client: Google GenAI 클라이언트
            model: 검증에 사용할 모델
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
            logging.warning(f"[ChainOfVerification] LLM 호출 실패: {e}")
            return ""

    def _parse_result(self, response_text: str) -> dict[str, Any]:
        """응답 파싱"""
        try:
            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            parsed = json.loads(json_match.group(1)) if json_match else json.loads(response_text)
            if isinstance(parsed, list):
                parsed = parsed[0] if parsed else {}
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):  # [V64.P4] JSON parse failure
            pass
        return {"passed": True, "overall_severity": "none", "issues": [], "summary": "파싱 실패 - 기본 통과"}

    def _build_context_string(self, context: dict[str, Any]) -> str:
        """컨텍스트를 문자열로 변환"""
        parts = []

        if "prev_manuscript" in context:
            prev = context["prev_manuscript"]
            if isinstance(prev, str) and len(prev) > 100:
                parts.append(f"[직전 화 엔딩]\n{prev[-1500:]}")

        if "hud" in context:
            hud = context["hud"]
            if isinstance(hud, dict):
                parts.append(f"[캐릭터 상태 (HUD)]\n{json.dumps(hud, ensure_ascii=False, indent=2)[:5000]}")

        if "blueprint" in context:
            bp = context["blueprint"]
            if isinstance(bp, dict):
                parts.append(f"[Blueprint 설계]\n{json.dumps(bp, ensure_ascii=False, indent=2)[:8000]}")

        if "arc_data" in context:
            arc = context["arc_data"]
            if isinstance(arc, dict):
                parts.append(f"[Arc 설계]\n{json.dumps(arc, ensure_ascii=False, indent=2)[:5000]}")

        if "inventory" in context:
            inv = context["inventory"]
            parts.append(f"[현재 소지품]\n{inv}")

        if "relationships" in context:
            rel = context["relationships"]
            parts.append(f"[NPC 관계 상태]\n{rel}")

        return "\n\n".join(parts) if parts else "컨텍스트 없음"

    def verify(
        self, generated_content: str, context: dict[str, Any], content_type: str = "manuscript"
    ) -> VerificationResult:
        """
        생성된 내용 검증

        Args:
            generated_content: 검증할 생성 내용
            context: 참조 컨텍스트 (prev_manuscript, hud, blueprint 등)
            content_type: "manuscript", "blueprint", "arc_design"

        Returns:
            VerificationResult
        """
        if not self.enabled:
            return VerificationResult(
                passed=True,
                severity=VerificationSeverity.NONE,
                issues=[],
                summary="검증 비활성화",
                should_regenerate=False,
                correction_hints="",
            )

        # 내용이 너무 짧으면 검증 스킵
        if len(generated_content) < 500:
            return VerificationResult(
                passed=True,
                severity=VerificationSeverity.NONE,
                issues=[],
                summary="내용이 짧아 검증 스킵",
                should_regenerate=False,
                correction_hints="",
            )

        context_str = self._build_context_string(context)

        prompt = self.VERIFICATION_PROMPT.format(
            content_type=content_type,
            generated_content=generated_content[:30000].replace("{", "{{").replace("}", "}}"),  # [V70] brace escape
            context=context_str[:15000].replace("{", "{{").replace("}", "}}"),  # [V70] brace escape
        )

        response = self._call_llm(prompt)
        result = self._parse_result(response)

        # 결과 변환
        issues = []
        for issue_data in result.get("issues", []):
            severity_str = issue_data.get("severity", "minor")
            try:
                severity = VerificationSeverity(severity_str)
            except (ValueError, KeyError):  # [V64.P4] enum parse failure
                severity = VerificationSeverity.MINOR

            issues.append(
                VerificationIssue(
                    category=issue_data.get("category", "unknown"),
                    description=issue_data.get("description", ""),
                    location=issue_data.get("location", ""),
                    severity=severity,
                    suggestion=issue_data.get("suggestion", ""),
                )
            )

        overall_severity_str = result.get("overall_severity", "none")
        try:
            overall_severity = VerificationSeverity(overall_severity_str)
        except (ValueError, KeyError):  # [V64.P4] enum parse failure
            overall_severity = VerificationSeverity.NONE

        passed = result.get("passed", True)
        should_regenerate = overall_severity == VerificationSeverity.CRITICAL

        # 수정 힌트 생성
        correction_hints = self._generate_correction_hints(issues)

        return VerificationResult(
            passed=passed,
            severity=overall_severity,
            issues=issues,
            summary=result.get("summary", ""),
            should_regenerate=should_regenerate,
            correction_hints=correction_hints,
        )

    def _generate_correction_hints(self, issues: list[VerificationIssue]) -> str:
        """이슈 목록에서 수정 힌트 생성"""
        if not issues:
            return ""

        hints = ["[V53.2 CoVe 수정 힌트]"]
        for issue in issues[:5]:  # 최대 5개
            if issue.suggestion:
                hints.append(f"- {issue.category}: {issue.suggestion}")

        return "\n".join(hints)

    def quick_verify(self, generated_content: str, context: dict[str, Any]) -> tuple[bool, str]:
        """
        빠른 검증 (Python 휴리스틱만, LLM 없음)

        Returns:
            (통과 여부, 경고 메시지)
        """
        warnings = []

        # 1. 이전 원고에서 언급된 아이템이 갑자기 사라지는지 체크
        prev_ms = context.get("prev_manuscript", "")
        if prev_ms:
            # 대도, 검, 무기 등 핵심 아이템 추적
            item_patterns = [
                r"(대도|장검|단검|검|창|도끼|활|궁|봉|철퇴)",
                r"(패|사자패|철혈|영패)",
            ]
            for pattern in item_patterns:
                prev_items = set(re.findall(pattern, prev_ms[-2000:]))
                curr_items = set(re.findall(pattern, generated_content[:2000]))

                # 이전에 있던 핵심 아이템이 현재 시작부에서 언급 안 되면 경고
                missing = prev_items - curr_items
                if missing and len(prev_items) > 0:
                    # 모든 아이템이 사라진 건 아닌지 체크
                    if len(missing) == len(prev_items):
                        warnings.append(f"직전 화 아이템({', '.join(missing)})이 현재 화에서 언급되지 않음")

        # 2. 시간 역행 체크 (간단한 패턴)
        time_forward = ["다음 날", "이튿날", "며칠 후", "후에", "지난 후"]
        time_backward = ["전날", "어제", "이전에", "예전에"]

        forward_count = sum(1 for t in time_forward if t in generated_content[:1000])
        backward_count = sum(1 for t in time_backward if t in generated_content[:1000])

        if backward_count > forward_count and backward_count > 2:
            warnings.append("시작부에 과거 시제 언급이 많음 (회상 의도가 아니라면 확인 필요)")

        # 3. 급격한 관계 변화 키워드
        sudden_change_patterns = [
            r"갑자기.{0,20}(충성|복종|굴복)",
            r"(적대|무시).{0,30}(충성|신뢰)",
            r"단번에.{0,20}(인정|존경)",
        ]
        for pattern in sudden_change_patterns:
            if re.search(pattern, generated_content):
                warnings.append("급격한 관계 변화 표현 감지 (자연스러운 전개인지 확인)")
                break

        passed = len(warnings) == 0
        return passed, "; ".join(warnings) if warnings else ""

    def generate_feedback(self, result: VerificationResult) -> str:
        """검증 결과를 피드백 문자열로 변환"""
        if result.passed and result.severity == VerificationSeverity.NONE:
            return ""

        lines = ["[V53.2 Chain-of-Verification 검증 결과]"]
        lines.append(f"심각도: {result.severity.value}")
        lines.append(f"요약: {result.summary}")

        if result.issues:
            lines.append("\n발견된 모순:")
            for issue in result.issues[:3]:
                lines.append(f"  - [{issue.category}] {issue.description}")
                if issue.suggestion:
                    lines.append(f"    → 제안: {issue.suggestion}")

        if result.correction_hints:
            lines.append(f"\n{result.correction_hints}")

        return "\n".join(lines)
