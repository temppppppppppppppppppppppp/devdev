"""
[V53.7] Multi-Agent Deliberation (다중 에이전트 토론)
Analyst + Architect + Writer 3자 토론 시스템

핵심: 서로 다른 전문성을 가진 에이전트들이 토론하여 품질 향상

원리:
1. 초안 생성
2. 각 에이전트가 자신의 관점에서 리뷰
3. 문제점과 개선안 토론
4. 합의된 최종안 도출

비용: +$0.05~0.08/생성 (3개 에이전트 호출)

사용:
    mad = MultiAgentDeliberation(api_client)
    result = mad.deliberate(
        content=draft,
        content_type="manuscript",
        context={"blueprint": bp, "arc_data": arc}
    )
    final = result.consensus_output
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from modules.core.constants import smart_truncate
from modules.core.llm_generate import generate_content_via_router


class AgentRole(Enum):
    """에이전트 역할"""

    ANALYST = "analyst"  # 전략적 관점 (아크, 볼륨 전체)
    ARCHITECT = "architect"  # 구조적 관점 (씬 구성, 페이싱)
    WRITER = "writer"  # 문학적 관점 (묘사, 대사, 감정)


@dataclass
class AgentOpinion:
    """에이전트 의견"""

    role: AgentRole
    score: int  # 0-100
    strengths: list[str]  # 장점
    concerns: list[str]  # 우려 사항
    suggestions: list[str]  # 개선 제안
    critical_issues: list[str]  # 심각한 문제 (합의 불가)


@dataclass
class DeliberationResult:
    """토론 결과"""

    opinions: list[AgentOpinion]
    consensus_reached: bool
    consensus_score: int  # 합의 점수
    consensus_output: str  # 합의된 최종본
    debate_summary: str  # 토론 요약
    action_items: list[str]  # 수정 필요 항목


class MultiAgentDeliberation:
    """다중 에이전트 토론 시스템"""

    # 에이전트별 리뷰 프롬프트
    AGENT_PROMPTS = {
        AgentRole.ANALYST: """당신은 전략 분석가(Analyst)입니다.
당신의 역할은 콘텐츠가 **전체 서사 전략**에 부합하는지 평가하는 것입니다.

[평가 대상]
{content}

[컨텍스트]
{context}

**Analyst 관점에서 평가:**
1. **아크 정합성**: 현재 아크의 목표와 일치하는가?
2. **복선 관리**: 심어진 복선이 적절히 관리되고 있는가?
3. **페이싱**: 전체 스토리 진행 속도가 적절한가?
4. **캐릭터 아크**: 캐릭터 성장이 자연스러운가?
5. **범위**: 이번 화에 적절한 양의 내용인가?

JSON 형식:
```json
{{
    "score": 0-100,
    "strengths": ["장점1", "장점2"],
    "concerns": ["우려1", "우려2"],
    "suggestions": ["제안1", "제안2"],
    "critical_issues": ["심각한 문제가 있다면"]
}}
```""",
        AgentRole.ARCHITECT: """당신은 구조 설계자(Architect)입니다.
당신의 역할은 콘텐츠의 **구조적 완성도**를 평가하는 것입니다.

[평가 대상]
{content}

[컨텍스트]
{context}

**Architect 관점에서 평가:**
1. **씬 구성**: 씬이 논리적으로 연결되어 있는가?
2. **긴장-이완**: 긴장감 곡선이 적절한가?
3. **전환**: 장면 전환이 자연스러운가?
4. **클리프행어**: 끝이 다음 화를 유인하는가?
5. **시간/공간**: 시간과 공간 이동이 명확한가?

JSON 형식:
```json
{{
    "score": 0-100,
    "strengths": ["장점1", "장점2"],
    "concerns": ["우려1", "우려2"],
    "suggestions": ["제안1", "제안2"],
    "critical_issues": ["심각한 문제가 있다면"]
}}
```""",
        AgentRole.WRITER: """당신은 문학 작가(Writer)입니다.
당신의 역할은 콘텐츠의 **문학적 품질**을 평가하는 것입니다.

[평가 대상]
{content}

[컨텍스트]
{context}

**Writer 관점에서 평가:**
1. **묘사 품질**: 감각적 디테일이 충분한가?
2. **대화 품질**: 캐릭터별 말투가 구분되는가?
3. **감정 전달**: Show don't tell이 지켜지는가?
4. **문장력**: 문장이 매끄럽고 리듬감이 있는가?
5. **몰입감**: 독자가 빠져들 수 있는가?

JSON 형식:
```json
{{
    "score": 0-100,
    "strengths": ["장점1", "장점2"],
    "concerns": ["우려1", "우려2"],
    "suggestions": ["제안1", "제안2"],
    "critical_issues": ["심각한 문제가 있다면"]
}}
```""",
    }

    # 합의 도출 프롬프트
    CONSENSUS_PROMPT = """당신은 중립적인 회의 진행자입니다.
세 전문가의 의견을 종합하여 합의안을 도출해야 합니다.

[원본 콘텐츠]
{content}

[전문가 의견]
**Analyst (전략):** 점수 {analyst_score}
- 장점: {analyst_strengths}
- 우려: {analyst_concerns}
- 제안: {analyst_suggestions}

**Architect (구조):** 점수 {architect_score}
- 장점: {architect_strengths}
- 우려: {architect_concerns}
- 제안: {architect_suggestions}

**Writer (문학):** 점수 {writer_score}
- 장점: {writer_strengths}
- 우려: {writer_concerns}
- 제안: {writer_suggestions}

[합의 도출 지침]
1. 3명 중 2명 이상이 동의하는 문제는 반드시 수정
2. 한 명만 지적한 문제는 심각도에 따라 판단
3. 상충되는 제안은 중간점 찾기
4. 모든 장점은 보존

합의된 수정본을 출력하세요. 원본의 형식을 유지하되, 합의된 개선사항을 반영하세요."""

    def __init__(
        self, api_client, model: str = "gemini-2.5-flash"
    ):  # [SSOT-P2] 호출부(main_a.py:L1936)가 model 인자를 명시 전달
        """
        Args:
            api_client: Google GenAI 클라이언트
            model: 사용할 모델
        """
        self.client = api_client
        self.model = model
        self.enabled = True

    @staticmethod
    def _fit_prompt_text(value: str, max_chars: int, head_ratio: float = 0.55) -> str:
        """Prompt cap은 유지하되 최근 문맥을 같이 남긴다."""
        text = str(value or "")
        if len(text) <= max_chars:
            return text
        return smart_truncate(text, max_chars=max_chars, head_chars=max(1, int(max_chars * head_ratio)))

    def _call_llm(self, prompt: str, temperature: float = 0.4) -> str:
        """LLM 호출"""
        try:
            response = generate_content_via_router(
                client=self.client,
                model=self.model,
                contents=prompt,
                config={"temperature": temperature, "max_output_tokens": 8192},
            )
            return response.text or ""  # [V70] None 방어
        except Exception as e:
            logging.warning(f"[MultiAgentDeliberation] LLM 호출 실패: {e}")
            return ""

    def _parse_json(self, text: str) -> dict[str, Any]:
        """JSON 파싱"""
        try:
            json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            parsed = json.loads(json_match.group(1)) if json_match else json.loads(text)
            # [Sweep55] LLM이 list 반환 시 첫 dict 추출
            if isinstance(parsed, list):
                parsed = parsed[0] if parsed and isinstance(parsed[0], dict) else {}
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, ValueError):  # [V64.P4] JSON parse failure
            return {}

    def _get_agent_opinion(self, role: AgentRole, content: str, context: dict[str, Any]) -> AgentOpinion:
        """에이전트 의견 수집"""
        context_str = self._fit_prompt_text(json.dumps(context, ensure_ascii=False, default=str), 2000)

        prompt = self.AGENT_PROMPTS[role].format(
            content=self._fit_prompt_text(content, 5000).replace("{", "{{").replace("}", "}}"),  # [V70]
            context=context_str.replace("{", "{{").replace("}", "}}"),  # [V70] brace escape
        )

        response = self._call_llm(prompt, temperature=0.3)
        result = self._parse_json(response)

        if not result:
            return AgentOpinion(
                role=role, score=70, strengths=["파싱 실패"], concerns=[], suggestions=[], critical_issues=[]
            )

        try:
            _score = int(result.get("score", 70))
        except (ValueError, TypeError):
            _score = 70

        return AgentOpinion(
            role=role,
            score=_score,
            strengths=result.get("strengths", []),
            concerns=result.get("concerns", []),
            suggestions=result.get("suggestions", []),
            critical_issues=result.get("critical_issues", []),
        )

    def _build_consensus(self, content: str, opinions: list[AgentOpinion]) -> str:
        """합의안 도출"""
        # 역할별 의견 분리
        analyst = next((o for o in opinions if o.role == AgentRole.ANALYST), None)
        architect = next((o for o in opinions if o.role == AgentRole.ARCHITECT), None)
        writer = next((o for o in opinions if o.role == AgentRole.WRITER), None)

        def _esc(s):
            return s.replace("{", "{{").replace("}", "}}")

        prompt = self.CONSENSUS_PROMPT.format(
            content=_esc(self._fit_prompt_text(content, 6000)),
            analyst_score=analyst.score if analyst else 70,
            analyst_strengths=_esc(", ".join(analyst.strengths[:3])) if analyst else "없음",
            analyst_concerns=_esc(", ".join(analyst.concerns[:3])) if analyst else "없음",
            analyst_suggestions=_esc(", ".join(analyst.suggestions[:3])) if analyst else "없음",
            architect_score=architect.score if architect else 70,
            architect_strengths=_esc(", ".join(architect.strengths[:3])) if architect else "없음",
            architect_concerns=_esc(", ".join(architect.concerns[:3])) if architect else "없음",
            architect_suggestions=_esc(", ".join(architect.suggestions[:3])) if architect else "없음",
            writer_score=writer.score if writer else 70,
            writer_strengths=_esc(", ".join(writer.strengths[:3])) if writer else "없음",
            writer_concerns=_esc(", ".join(writer.concerns[:3])) if writer else "없음",
            writer_suggestions=_esc(", ".join(writer.suggestions[:3])) if writer else "없음",
        )

        return self._call_llm(prompt, temperature=0.5)

    def deliberate(
        self, content: str, content_type: str = "manuscript", context: dict[str, Any] = None
    ) -> DeliberationResult:
        """
        다중 에이전트 토론 실행

        Args:
            content: 토론할 콘텐츠
            content_type: "manuscript" 또는 "blueprint"
            context: 참조 컨텍스트

        Returns:
            DeliberationResult
        """
        if not self.enabled:
            return DeliberationResult(
                opinions=[],
                consensus_reached=True,
                consensus_score=75,
                consensus_output=content,
                debate_summary="토론 비활성화",
                action_items=[],
            )

        context = context or {}

        # 1. 각 에이전트 의견 수집
        opinions = []
        for role in [AgentRole.ANALYST, AgentRole.ARCHITECT, AgentRole.WRITER]:
            opinion = self._get_agent_opinion(role, content, context)
            opinions.append(opinion)

        # 2. 합의 여부 판단
        scores = [o.score for o in opinions]
        avg_score = sum(scores) / len(scores)

        # 모든 에이전트가 80점 이상이면 즉시 합의
        all_pass = all(s >= 80 for s in scores)

        # 심각한 문제가 있으면 합의 불가
        all_critical = []
        for o in opinions:
            all_critical.extend(o.critical_issues)

        consensus_reached = all_pass or (not all_critical and avg_score >= 70)

        # 3. 합의안 도출
        if consensus_reached and all_pass:
            # 모두 동의하면 원본 유지
            consensus_output = content
        else:
            # 토론 후 수정본 생성
            consensus_output = self._build_consensus(content, opinions)

            # 수정본이 너무 짧으면 원본 유지
            if len(consensus_output) < len(content) * 0.5:
                consensus_output = content

        # 4. 액션 아이템 수집
        action_items = []
        concern_counts = {}

        for o in opinions:
            for concern in o.concerns:
                concern_counts[concern] = concern_counts.get(concern, 0) + 1

        # 2명 이상이 지적한 우려사항
        for concern, count in concern_counts.items():
            if count >= 2:
                action_items.append(f"[공통 우려] {concern}")

        # 심각한 문제
        for issue in all_critical:
            action_items.append(f"[심각] {issue}")

        # 5. 토론 요약 생성
        debate_summary = self._generate_summary(opinions, consensus_reached)

        return DeliberationResult(
            opinions=opinions,
            consensus_reached=consensus_reached,
            consensus_score=int(avg_score),
            consensus_output=consensus_output,
            debate_summary=debate_summary,
            action_items=action_items,
        )

    def _generate_summary(self, opinions: list[AgentOpinion], consensus_reached: bool) -> str:
        """토론 요약 생성"""
        lines = ["[V53.7 Multi-Agent Deliberation]"]

        for o in opinions:
            role_name = o.role.value.upper()
            status = "✅" if o.score >= 80 else "⚠️" if o.score >= 60 else "❌"
            lines.append(f"{status} {role_name}: {o.score}점")

        avg = sum(o.score for o in opinions) / len(opinions)
        lines.append(f"\n평균: {avg:.0f}점")
        lines.append(f"합의: {'도달' if consensus_reached else '미달'}")

        return "\n".join(lines)

    def quick_deliberate(self, content: str, content_type: str = "manuscript") -> tuple[int, list[str]]:
        """
        빠른 토론 (Python 휴리스틱, LLM 없음)

        Returns:
            (예상 합의 점수, 주요 우려사항)
        """
        concerns = []
        score = 70  # 기본값

        if content_type == "manuscript":
            # Analyst 관점
            if len(content) > 12000:
                concerns.append("[Analyst] 범위 초과 의심")
                score -= 10

            # Architect 관점
            paragraphs = content.split("\n\n")
            if len(paragraphs) < 5:
                concerns.append("[Architect] 씬 구분 부족")
                score -= 5

            # Writer 관점
            sensory_words = ["보이", "들리", "느껴", "냄새"]
            sensory_count = sum(1 for w in sensory_words if w in content)
            if sensory_count < 3:
                concerns.append("[Writer] 감각 묘사 부족")
                score -= 5

            dialogue_count = content.count('"') // 2 + content.count("「")
            if dialogue_count < 4:
                concerns.append("[Writer] 대화 부족")
                score -= 5

        return max(0, min(100, score)), concerns

    def get_action_summary(self, result: DeliberationResult) -> str:
        """액션 아이템 요약"""
        if not result.action_items:
            return ""

        lines = ["[토론 결과 - 필요 조치]"]
        for item in result.action_items[:5]:
            lines.append(f"  {item}")

        return "\n".join(lines)
