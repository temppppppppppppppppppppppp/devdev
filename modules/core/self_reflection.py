"""
[V52.1] Self-Reflection Chain (자기 성찰 체인)
생성 → 자기 비평 → 수정 → 최종

핵심: 1차 생성의 명백한 오류를 LLM 스스로 발견하고 수정

원리:
1. 초기 생성 완료
2. 동일 모델에게 자기 비평 요청
3. 비평 기반 수정본 생성
4. 수정본 반환

비용: +$0.01~0.02/생성 (추가 1회 호출)

사용:
    reflector = SelfReflector(api_client)
    improved = reflector.reflect_and_improve(
        original_output=manuscript,
        context={"ep_num": 5, "blueprint": bp},
        agent_type="writer"
    )
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ReflectionTarget(Enum):
    """성찰 대상"""

    WRITER = "writer"
    ARCHITECT = "architect"
    ANALYST = "analyst"


@dataclass
class ReflectionResult:
    """성찰 결과"""

    original: str
    critique: str
    improved: str
    changes_made: list
    improvement_score: float  # 0-1 (개선 정도)


class SelfReflector:
    """자기 성찰 체인"""

    # 에이전트별 성찰 프롬프트
    REFLECTION_PROMPTS = {
        ReflectionTarget.WRITER: """당신은 방금 작성한 원고를 검토하는 편집자입니다.

[작성된 원고]
{output}

[블루프린트 요구사항]
{context}

다음 관점에서 원고를 비평하세요:

1. **연속성 오류**: 이전 내용과 모순되는 부분이 있는가?
2. **캐릭터 일관성**: 캐릭터가 갑자기 다르게 행동하는가?
3. **블루프린트 준수**: 설계된 씬이 모두 반영되었는가?
4. **호흡 문제**: 너무 빠르거나 느린 부분이 있는가?
5. **대가 없는 성장**: 공짜 파워업이 있는가?
6. **악역 지능**: 악역이 비합리적으로 멍청한가?

JSON 형식으로 응답:
```json
{{
    "issues": [
        {{"type": "연속성", "location": "3번째 문단", "problem": "...", "fix": "..."}},
        ...
    ],
    "severity": "high|medium|low|none",
    "overall_quality": 1-10
}}
```""",
        ReflectionTarget.ARCHITECT: """당신은 방금 작성한 블루프린트를 검토하는 수석 설계자입니다.

[작성된 블루프린트]
{output}

[아크 전술 설계]
{context}

다음 관점에서 블루프린트를 비평하세요:

1. **범위 초과**: 이번 화에서 다뤄야 할 범위를 넘어섰는가?
2. **씬 구성**: 4-6개 씬이 적절히 구성되었는가?
3. **클리프행어**: 끝에 다음 화를 유인하는 훅이 있는가?
4. **연속성**: 직전 화 엔딩과 자연스럽게 이어지는가?
5. **긴장 곡선**: 이완-긴장 리듬이 적절한가?

JSON 형식으로 응답:
```json
{{
    "issues": [
        {{"type": "범위초과", "location": "scene_4", "problem": "...", "fix": "..."}},
        ...
    ],
    "severity": "high|medium|low|none",
    "overall_quality": 1-10
}}
```""",
        ReflectionTarget.ANALYST: """당신은 방금 작성한 아크 설계를 검토하는 전략 고문입니다.

[작성된 아크 설계]
{output}

[볼륨 전략]
{context}

다음 관점에서 설계를 비평하세요:

1. **아이템 중복**: 이미 획득한 아이템을 다시 획득하는가?
2. **타임라인**: 시간순이 논리적인가?
3. **갈등 밀도**: 너무 빽빽하거나 느슨하지 않은가?
4. **패턴 반복**: 직전 아크와 너무 유사하지 않은가?
5. **복선 관리**: 심어야 할 복선이 있는가?

JSON 형식으로 응답:
```json
{{
    "issues": [
        {{"type": "중복획득", "item": "대도", "problem": "...", "fix": "..."}},
        ...
    ],
    "severity": "high|medium|low|none",
    "overall_quality": 1-10
}}
```""",
    }

    IMPROVEMENT_PROMPT = """당신의 비평을 바탕으로 원본을 수정하세요.

[원본]
{original}

[비평]
{critique}

[수정 지시]
- severity가 "high"인 문제는 반드시 수정
- severity가 "medium"인 문제는 가능하면 수정
- severity가 "low"인 문제는 선택적 수정

수정된 전체 내용을 출력하세요. 형식은 원본과 동일하게 유지하세요."""

    def __init__(self, api_client, model: str = "gemini-3-pro-preview"):
        """
        [V60.24] Gemini 3로 변경
        Args:
            api_client: Google GenAI 클라이언트
            model: 성찰에 사용할 모델 (V60.24: Gemini 3)
        """
        self.client = api_client
        self.model = model
        self.enabled = True  # 활성화 여부

    def _call_llm(self, prompt: str, temperature: float = 0.3) -> str:
        """LLM 호출"""
        try:
            response = self.client.models.generate_content(
                model=self.model, contents=prompt, config={"temperature": temperature, "max_output_tokens": 8192}
            )
            return response.text if response.text else ""  # [V70] None 방어
        except Exception as e:
            logging.warning(f"[SelfReflector] LLM 호출 실패: {e}")
            return ""

    def _parse_critique(self, critique_text: str) -> dict[str, Any]:
        """비평 결과 파싱"""
        try:
            # JSON 블록 추출
            json_match = re.search(r"```json\s*(.*?)\s*```", critique_text, re.DOTALL)
            parsed = json.loads(json_match.group(1)) if json_match else json.loads(critique_text)
            # [Sweep55] LLM이 list 반환 시 첫 dict 추출
            if isinstance(parsed, list):
                parsed = parsed[0] if parsed and isinstance(parsed[0], dict) else {}
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse failure
            # 파싱 실패 시 기본값
            return {"issues": [], "severity": "none", "overall_quality": 7}

    def reflect(self, output: str, context: str, target: ReflectionTarget) -> dict[str, Any]:
        """
        자기 비평 수행

        Args:
            output: 원본 출력
            context: 맥락 정보 (블루프린트, 아크 설계 등)
            target: 대상 에이전트 유형

        Returns:
            비평 결과 딕셔너리
        """
        if not self.enabled:
            return {"issues": [], "severity": "none", "overall_quality": 8}

        prompt_template = self.REFLECTION_PROMPTS.get(target)
        if not prompt_template:
            return {"issues": [], "severity": "none", "overall_quality": 7}

        # [V70] 사용자 콘텐츠 내 {}는 .format()에서 KeyError 유발 → 이스케이프
        _safe_output = output[:8000].replace("{", "{{").replace("}", "}}")
        _safe_context = context[:3000].replace("{", "{{").replace("}", "}}")
        prompt = prompt_template.format(output=_safe_output, context=_safe_context)
        critique_text = self._call_llm(prompt, temperature=0.2)

        return self._parse_critique(critique_text)

    def improve(self, original: str, critique: dict[str, Any], target: ReflectionTarget) -> str:
        """
        비평 기반 개선

        Args:
            original: 원본 출력
            critique: 비평 결과
            target: 대상 에이전트 유형

        Returns:
            개선된 출력
        """
        if not self.enabled:
            return original

        # 심각도가 낮으면 수정 생략
        if critique.get("severity") in ["none", "low"]:
            return original

        # 이슈가 없으면 수정 생략
        if not critique.get("issues"):
            return original

        critique_summary = json.dumps(critique, ensure_ascii=False, indent=2)
        # [V70] 사용자 콘텐츠 내 {}는 .format()에서 KeyError 유발 → 이스케이프
        _safe_original = original[:12000].replace("{", "{{").replace("}", "}}")
        _safe_critique = critique_summary.replace("{", "{{").replace("}", "}}")
        prompt = self.IMPROVEMENT_PROMPT.format(original=_safe_original, critique=_safe_critique)

        improved = self._call_llm(prompt, temperature=0.4)

        # 개선 실패 시 원본 반환
        if not improved or len(improved) < len(original) * 0.5:
            return original

        return improved

    def reflect_and_improve(
        self, output: str, context: str, target: ReflectionTarget, force: bool = False
    ) -> ReflectionResult:
        """
        자기 성찰 + 개선 전체 체인

        Args:
            output: 원본 출력
            context: 맥락 정보
            target: 대상 에이전트 유형
            force: True면 severity 무시하고 항상 개선

        Returns:
            ReflectionResult
        """
        # 1. 비평
        critique = self.reflect(output, context, target)

        # 2. 개선 필요 여부 판단
        severity = critique.get("severity", "none")
        issues = critique.get("issues", [])
        quality = critique.get("overall_quality", 7)

        should_improve = force or severity in ["high", "medium"] or quality < 6

        # 3. 개선 (필요시)
        if should_improve and issues:
            improved = self.improve(output, critique, target)
            changes = [issue.get("type", "unknown") for issue in issues]
            improvement_score = min(1.0, len(issues) * 0.15)
        else:
            improved = output
            changes = []
            improvement_score = 0.0

        return ReflectionResult(
            original=output,
            critique=json.dumps(critique, ensure_ascii=False),
            improved=improved,
            changes_made=changes,
            improvement_score=improvement_score,
        )

    def quick_check(self, output: str, target: ReflectionTarget) -> dict[str, Any]:
        """
        빠른 품질 체크 (개선 없이 점수만)

        Returns:
            {"quality": 1-10, "severity": str, "issues_count": int}
        """
        # 간단한 휴리스틱 체크 (LLM 호출 없음)
        issues_count = 0

        if target == ReflectionTarget.WRITER:
            # 길이 체크
            if len(output) < 3000:
                issues_count += 1
            # 대화 비율 체크
            dialogue_count = output.count('"') + output.count("「")
            if dialogue_count < 4:
                issues_count += 1

        elif target == ReflectionTarget.ARCHITECT:
            # 씬 개수 체크
            scene_count = len(re.findall(r"scene_\d+|씬\s*\d+", output, re.IGNORECASE))
            if scene_count < 3 or scene_count > 8:
                issues_count += 1

        quality = max(1, 10 - issues_count * 2)
        severity = "high" if issues_count > 2 else "medium" if issues_count > 0 else "none"

        return {"quality": quality, "severity": severity, "issues_count": issues_count}
