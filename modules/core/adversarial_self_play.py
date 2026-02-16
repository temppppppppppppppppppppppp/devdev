"""
[V53.6] Adversarial Self-Play (적대적 자기 대결)
Writer 생성 → 가상 Director 비판 → Writer 수정 루프

핵심: 내부적으로 Director 역할을 시뮬레이션하여 사전 품질 향상

원리:
1. Writer가 초안 생성
2. 가상 Director가 비판적 리뷰
3. Writer가 비판 기반 수정
4. 개선된 버전 출력

비용: +$0.03/생성 (2회 추가 호출)

사용:
    asp = AdversarialSelfPlay(api_client)
    result = asp.generate_with_adversary(
        initial_content=draft,
        content_type="manuscript",
        context={"blueprint": bp}
    )
    improved = result.final_output
"""

import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from modules.core.constants import ManuscriptLimits  # [V64.P4]


class ContentType(Enum):
    """콘텐츠 유형"""

    MANUSCRIPT = "manuscript"
    BLUEPRINT = "blueprint"


@dataclass
class AdversaryFeedback:
    """가상 Director 피드백"""

    decision: str  # "PASS", "REVISE", "REJECT"
    score: int  # 0-100
    issues: list[dict[str, str]]  # [{type, description, severity}]
    praise: list[str]  # 잘한 점
    revision_guide: str  # 수정 가이드


@dataclass
class ASPResult:
    """Adversarial Self-Play 결과"""

    initial_content: str
    adversary_feedback: AdversaryFeedback
    revised_content: str
    final_output: str
    improvement_delta: int  # 점수 향상폭
    rounds: int  # 수행 라운드 수


class AdversarialSelfPlay:
    """적대적 자기 대결 시스템"""

    # 가상 Director 프롬프트
    ADVERSARY_PROMPT = """당신은 까다롭고 정밀한 소설 편집장 Director입니다.
당신의 역할은 원고를 냉정하게 평가하고 개선점을 찾는 것입니다.

[평가 대상 - {content_type}]
{content}

[참조 컨텍스트]
{context}

다음 기준으로 냉정하게 평가하세요:

**무협 소설 평가 기준:**
1. **연속성** (25점): 이전 내용과 모순 없는가?
2. **캐릭터 일관성** (20점): 캐릭터가 자연스럽게 행동하는가?
3. **씬 완성도** (20점): 설계된 씬이 충실히 구현되었는가?
4. **몰입도** (20점): 독자가 빠져들 수 있는 묘사인가?
5. **기술적 완성도** (15점): 문장력, 구성, 마무리

**찾아야 할 문제:**
- 갑작스러운 관계 변화
- 미획득 아이템 사용
- 부상 상태 무시
- 설명만 있고 묘사 없음
- 악역의 비합리적 행동
- 범위 초과 (다음 화 내용 포함)

JSON 형식으로 냉정하게:
```json
{{
    "decision": "PASS|REVISE|REJECT",
    "score": 0-100,
    "issues": [
        {{"type": "문제 유형", "description": "구체적 설명", "severity": "critical|major|minor"}}
    ],
    "praise": ["잘한 점1", "잘한 점2"],
    "revision_guide": "이렇게 수정하면 더 좋아집니다: ..."
}}
```

기준: 85점 이상 PASS, 60-84점 REVISE, 60점 미만 REJECT"""

    # Writer 수정 프롬프트
    REVISION_PROMPT = """당신은 숙련된 소설 작가입니다.
편집장의 피드백을 받고 원고를 수정해야 합니다.

[원본 {content_type}]
{original}

[편집장 피드백]
점수: {score}/100
결정: {decision}

문제점:
{issues}

수정 가이드:
{revision_guide}

[수정 지침]
1. 지적된 문제점을 모두 해결하세요
2. 잘한 부분은 유지하세요
3. 원본의 톤과 스타일을 유지하세요
4. 새로운 문제를 만들지 마세요

수정된 전체 내용을 출력하세요."""

    def __init__(self, api_client, model: str = "gemini-2.0-flash"):
        """
        Args:
            api_client: Google GenAI 클라이언트
            model: 사용할 모델
        """
        self.client = api_client
        self.model = model
        self.enabled = True
        self.max_rounds = 2  # 최대 수정 라운드

    def _call_llm(self, prompt: str, temperature: float = 0.4) -> str:
        """LLM 호출"""
        try:
            response = self.client.models.generate_content(
                model=self.model, contents=prompt, config={"temperature": temperature, "max_output_tokens": 8192}
            )
            return response.text or ""  # [V70] None 방어
        except Exception as e:
            logging.warning(f"[AdversarialSelfPlay] LLM 호출 실패: {e}")
            return ""

    def _parse_json(self, text: str) -> dict[str, Any]:
        """JSON 파싱"""
        try:
            json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):  # [V64.P4] JSON parse failure
            return {}

    def _get_adversary_feedback(self, content: str, content_type: str, context: dict[str, Any]) -> AdversaryFeedback:
        """가상 Director 피드백 생성"""
        context_str = json.dumps(context, ensure_ascii=False, default=str)[:2000]

        prompt = self.ADVERSARY_PROMPT.format(
            content_type=content_type,
            content=content[:6000].replace("{", "{{").replace("}", "}}"),  # [V70] brace escape
            context=context_str.replace("{", "{{").replace("}", "}}"),  # [V70] brace escape
        )

        response = self._call_llm(prompt, temperature=0.3)
        result = self._parse_json(response)

        if not result:
            # 파싱 실패 시 기본값
            return AdversaryFeedback(
                decision="PASS", score=70, issues=[], praise=["파싱 실패로 기본 통과"], revision_guide=""
            )

        return AdversaryFeedback(
            decision=result.get("decision", "PASS"),
            score=result.get("score", 70),
            issues=result.get("issues", []),
            praise=result.get("praise", []),
            revision_guide=result.get("revision_guide", ""),
        )

    def _revise_content(self, original: str, feedback: AdversaryFeedback, content_type: str) -> str:
        """피드백 기반 수정"""
        issues_text = "\n".join(
            [
                f"- [{i.get('severity', 'minor')}] {i.get('type', '')}: {i.get('description', '')}"
                for i in feedback.issues[:5]
            ]
        )

        prompt = self.REVISION_PROMPT.format(
            content_type=content_type,
            original=original[:8000].replace("{", "{{").replace("}", "}}"),  # [V70] brace escape
            score=feedback.score,
            decision=feedback.decision,
            issues=(issues_text if issues_text else "없음").replace("{", "{{").replace("}", "}}"),  # [V70]
            revision_guide=(feedback.revision_guide if feedback.revision_guide else "원본 유지")
            .replace("{", "{{")
            .replace("}", "}}"),  # [V70]
        )

        revised = self._call_llm(prompt, temperature=0.5)

        # 수정본이 너무 짧으면 원본 유지
        if len(revised) < len(original) * 0.5:
            return original

        return revised

    def generate_with_adversary(
        self,
        initial_content: str,
        content_type: str = "manuscript",
        context: dict[str, Any] = None,
        generator_fn: Callable = None,
    ) -> ASPResult:
        """
        적대적 자기 대결로 콘텐츠 개선

        Args:
            initial_content: 초기 콘텐츠 (또는 빈 문자열이면 generator_fn 사용)
            content_type: "manuscript" 또는 "blueprint"
            context: 참조 컨텍스트
            generator_fn: 초기 콘텐츠 생성 함수 (initial_content가 없을 때)

        Returns:
            ASPResult
        """
        if not self.enabled:
            return ASPResult(
                initial_content=initial_content,
                adversary_feedback=AdversaryFeedback(
                    decision="PASS", score=75, issues=[], praise=[], revision_guide=""
                ),
                revised_content=initial_content,
                final_output=initial_content,
                improvement_delta=0,
                rounds=0,
            )

        context = context or {}

        # 초기 콘텐츠 생성
        if not initial_content and generator_fn:
            initial_content = generator_fn()
            if isinstance(initial_content, dict):
                initial_content = json.dumps(initial_content, ensure_ascii=False)

        if not initial_content:
            return ASPResult(
                initial_content="",
                adversary_feedback=AdversaryFeedback(
                    decision="REJECT",
                    score=0,
                    issues=[{"type": "empty", "description": "콘텐츠 없음"}],
                    praise=[],
                    revision_guide="",
                ),
                revised_content="",
                final_output="",
                improvement_delta=0,
                rounds=0,
            )

        current_content = initial_content
        initial_score = 0
        final_feedback = None
        rounds = 0

        # 적대적 루프
        for round_num in range(self.max_rounds):
            rounds = round_num + 1

            # 1. 가상 Director 평가
            feedback = self._get_adversary_feedback(current_content, content_type, context)

            if round_num == 0:
                initial_score = feedback.score

            final_feedback = feedback

            # 2. PASS면 종료
            if feedback.decision == "PASS":
                break

            # 3. 이슈가 없으면 종료
            if not feedback.issues:
                break

            # 4. Writer 수정
            revised = self._revise_content(current_content, feedback, content_type)
            current_content = revised

        # 최종 결과
        improvement_delta = (final_feedback.score if final_feedback else initial_score) - initial_score

        return ASPResult(
            initial_content=initial_content,
            adversary_feedback=final_feedback
            or AdversaryFeedback(decision="PASS", score=75, issues=[], praise=[], revision_guide=""),
            revised_content=current_content,
            final_output=current_content,
            improvement_delta=improvement_delta,
            rounds=rounds,
        )

    def quick_adversary_check(self, content: str, content_type: str = "manuscript") -> tuple[bool, str]:
        """
        빠른 적대적 체크 (Python 휴리스틱, LLM 없음)

        Returns:
            (통과 여부, 문제점 요약)
        """
        issues = []

        if content_type == "manuscript":
            # 길이 체크
            if len(content) < ManuscriptLimits.MIN_LENGTH:  # [V64.P4]
                issues.append(f"길이 부족 ({len(content)}자)")

            # 대화 체크
            dialogue_count = content.count('"') // 2 + content.count("「")
            if dialogue_count < 3:
                issues.append(f"대화 부족 ({dialogue_count}개)")

            # 갑작스러운 관계 변화 패턴
            sudden_patterns = [
                r"갑자기.{0,30}(충성|복종)",
                r"(적대|무시).{0,50}(신뢰|충성)",
            ]
            for pattern in sudden_patterns:
                if re.search(pattern, content):
                    issues.append("급격한 관계 변화 감지")
                    break

            # 악역 멍청 패턴
            villain_stupid = [
                r"(놈|자식).{0,30}(바보|멍청)",
                r"어리석.{0,20}(적|악역|상대)",
            ]
            for pattern in villain_stupid:
                if re.search(pattern, content):
                    issues.append("악역 과소평가 패턴 감지")
                    break

        elif content_type == "blueprint":
            try:
                bp = json.loads(content) if isinstance(content, str) else content
            except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse failure
                issues.append("JSON 파싱 실패")
                bp = {}

            if not bp.get("integrated_scenario"):
                issues.append("시나리오 없음")

            scene_count = len(bp.get("scene_breakdown", {}))
            if scene_count < 3:
                issues.append(f"씬 부족 ({scene_count}개)")

        passed = len(issues) == 0
        return passed, "; ".join(issues) if issues else ""

    def get_summary(self, result: ASPResult) -> str:
        """결과 요약"""
        lines = ["[V53.6 Adversarial Self-Play]"]
        lines.append(f"라운드: {result.rounds}")
        lines.append(
            f"초기 → 최종: {result.adversary_feedback.score - result.improvement_delta} → {result.adversary_feedback.score}"
        )
        lines.append(f"향상: +{result.improvement_delta}점")
        lines.append(f"결정: {result.adversary_feedback.decision}")

        if result.adversary_feedback.issues:
            lines.append(f"발견 이슈: {len(result.adversary_feedback.issues)}건")

        return "\n".join(lines)
