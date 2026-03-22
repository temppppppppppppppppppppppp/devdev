"""
[V51.3] Agent Intelligence Suite (에이전트 지능 향상 모듈)
3가지 지능 향상 기법 통합

1. Few-Shot Exemplar Library - 우수 예시 기반 학습
2. Self-Critique Chain - 자가 검토 체인
3. Anti-Pattern Injection - 안티패턴 회피

비용: Few-Shot/Anti-Pattern = $0, Self-Critique = ~$0.01/회

사용:
    intel = AgentIntelligence(genre='wuxia')

    # Analyst용
    analyst_prompt = intel.get_analyst_enhancement(arc_num, prev_arcs)

    # Architect용
    architect_prompt = intel.get_architect_enhancement(ep_num, arc_data)

    # Writer용
    writer_prompt = intel.get_writer_enhancement(ep_num, blueprint)

    # Self-Critique (선택)
    critique = intel.self_critique(output, agent_type='writer')
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from modules.core.constants import smart_truncate


class AgentType(Enum):
    ANALYST = "analyst"
    ARCHITECT = "architect"
    WRITER = "writer"


@dataclass
class Exemplar:
    """우수 예시"""

    title: str
    content: str
    why_good: str  # 왜 좋은지 설명
    tags: list[str] = field(default_factory=list)


class AgentIntelligence:
    """에이전트 지능 향상 모듈"""

    def __init__(self, genre: str = "wuxia"):
        self.genre = genre
        self._init_exemplars()
        self._init_anti_patterns()
        self._init_critique_templates()

    # ================================================================
    # 1. FEW-SHOT EXEMPLAR LIBRARY
    # ================================================================

    def _init_exemplars(self) -> None:
        """우수 예시 라이브러리 초기화"""

        self.analyst_exemplars = self._build_analyst_exemplars()
        self.architect_exemplars = self._build_architect_exemplars()
        self.writer_exemplars = self._build_writer_exemplars()

    def _build_analyst_exemplars(self) -> dict[str, list[Exemplar]]:
        """Analyst exemplar catalog by genre."""

        return {
            "wuxia": [
                Exemplar(
                    title="복수극 Arc 설계",
                    content="""
[Arc 3: 혈채(\u8840\u50B5)]
- 핵심 갈등: 과거 원수와의 재회, 복수 vs 용서의 딜레마
- 화별 전개:
  1화: 우연한 재회, 원수가 은인으로 위장 (반전 복선)
  2화: 정체 의심, 단서 수집, 내적 갈등 고조
  3화: 진실 폭로, 대치, 예상치 못한 사연 공개
  4화: 결단의 순간, 복수 포기와 새로운 적 등장
  5화: 공동의 적 대항, 관계 재정립
- 감정선: 분노 → 혼란 → 이해 → 결단 → 연대
- 복선: 1화 은인 행동의 이상함 → 3화 회수
""",
                    why_good="복수 클리셰를 비틀어 새로운 전개 창출. 감정선이 명확하고 복선-회수 구조 완비",
                    tags=["복수", "반전", "감정선"],
                ),
                Exemplar(
                    title="성장 Arc 설계",
                    content="""
[Arc 5: 파경(\u7834\u5883)]
- 핵심 갈등: 경지 돌파의 관문, 내면의 마(\u9B54)와 대면
- 화별 전개:
  1화: 돌파 시도 실패, 심마(\u5FC3\u9B54) 발현 조짐
  2화: 과거 트라우마 회귀, 환각 속 대면
  3화: 심마의 정체 = 자신의 그림자, 도피 vs 직면
  4화: 스승의 마지막 가르침 회상, 깨달음의 실마리
  5화: 심마 수용/초월, 새 경지 도달, 대가(부상/기억 일부 상실)
- 성장 대가: 반드시 무언가를 잃어야 함 (공짜 파워업 금지)
""",
                    why_good="성장에 반드시 대가 설정. 내면 갈등을 외면화하여 긴장감 유지",
                    tags=["성장", "경지", "대가"],
                ),
            ],
            "hunter": [
                Exemplar(
                    title="던전 공략 Arc",
                    content="""
[Arc 4: 심연의 문]
- 핵심: S급 던전 첫 도전, 팀 역학 시험
- 전개: 준비 → 진입 → 위기 → 분열 → 재결합 → 돌파
- 대가: 팀원 1명 각성 대신 수명 단축 (선택의 무게)
""",
                    why_good="팀 역학과 개인 성장 균형. 선택에 대가 부여",
                    tags=["던전", "팀", "선택"],
                ),
            ],
            "investment": [
                Exemplar(
                    title="시장 위기 Arc",
                    content="""
[Arc 3: 블랙스완]
- 핵심: 예측 불가 시장 폭락, 기회 vs 리스크
- 전개: 조짐 감지 → 경고 무시 → 폭락 → 기회 포착 → 역전
- 교훈: 욕심이 판단을 흐리게 함 (주변 인물 몰락)
""",
                    why_good="금융 리얼리즘 + 인간 드라마 결합",
                    tags=["시장", "위기", "기회"],
                ),
            ],
        }

    def _build_architect_exemplars(self) -> dict[str, list[Exemplar]]:
        """Architect exemplar catalog by genre."""

        return {
            "wuxia": [
                Exemplar(
                    title="대결 장면 Blueprint",
                    content="""
[제15화 Blueprint]
Scene 1 (긴장 축적): 대치 상황, 주변 인물들의 긴장, 과거 회상 플래시백
Scene 2 (도발): 악역의 심리전, 주인공 내면 동요, 주변 반응
Scene 3 (첫 교전): 시험적 공방, 실력 탐색, 의외의 강함 발견
Scene 4 (위기): 주인공 수세, 부상, 과거 트라우마 자극
Scene 5 (반전 준비): 깨달음의 순간, 새 기술 힌트, 분위기 전환
Scene 6 (클리프행어): 새 기술 발동 직전 장면 정지, "과연 통할 것인가?"

[씬 전환 기법]
- Scene 1→2: 시선 이동 (관중 → 대결자)
- Scene 4→5: 내면 독백으로 전환
- 각 씬 800-1200자 목표
""",
                    why_good="6단계 긴장 곡선 완비. 씬 전환 기법 명시. 클리프행어 강력",
                    tags=["대결", "긴장", "클리프행어"],
                ),
                Exemplar(
                    title="일상/훈련 Blueprint",
                    content="""
[제8화 Blueprint]
Scene 1: 훈련 시작, 스승의 불가능해 보이는 과제 제시
Scene 2: 첫 시도 실패, 좌절, 동료와의 대화로 힌트 획득
Scene 3: 재도전, 부분 성공, 새로운 문제 발견
Scene 4: 휴식 중 우연한 깨달음 (일상에서 무공 원리 발견)
Scene 5: 최종 성공, 스승의 인정, 다음 단계 암시 (클리프행어)

[Show Don't Tell]
- "열심히 수련했다" (X)
- "천 번째 검을 휘두를 때 손바닥이 터졌다" (O)
""",
                    why_good="훈련 장면에도 드라마 구조 적용. Show Don't Tell 예시 포함",
                    tags=["훈련", "성장", "깨달음"],
                ),
            ],
        }

    def _build_writer_exemplars(self) -> dict[str, list[Exemplar]]:
        """Writer exemplar catalog by genre."""

        return {
            "wuxia": [
                Exemplar(
                    title="전투 묘사",
                    content="""
[나쁜 예]
그는 검을 빠르게 휘둘렀다. 적은 피했다. 다시 공격했다.

[좋은 예]
검이 허공을 갈랐다. 찰나, 적의 눈이 커졌다—피하지 못할 궤적이었다.
그러나 몸이 먼저 반응했다. 허리를 비틀며 반 보 물러서는 그 찰나,
검끝이 옷자락을 스치며 실오라기가 흩날렸다.
"제법이군."
숨이 거칠어진 건 피한 자가 아니라 휘두른 자였다.
""",
                    why_good="짧은 문장으로 긴박감. 감각 디테일. 반전(공격자가 더 지침). 여운",
                    tags=["전투", "긴장", "반전"],
                ),
                Exemplar(
                    title="감정 묘사",
                    content="""
[나쁜 예]
그는 매우 슬펐다. 눈물이 났다.

[좋은 예]
목구멍이 조여왔다. 삼키려 해도 삼켜지지 않는 무언가가
차오르고 있었다. 손끝이 저렸다. 주먹을 쥐어도 힘이 들어가지 않았다.
시야가 흐려지는 걸 느꼈을 때, 그는 고개를 들어 하늘을 보았다.
구름 한 점 없이 맑은 하늘이, 그래서 더 잔인하게 느껴졌다.
""",
                    why_good="감정을 직접 명명하지 않고 신체 반응으로 표현. 환경과 감정 대비",
                    tags=["감정", "신체", "환경"],
                ),
                Exemplar(
                    title="대화와 행동",
                    content="""
[나쁜 예]
"안녕하세요." 그가 말했다.
"안녕." 그녀가 대답했다.

[좋은 예]
"...오랜만이군."
그녀는 대답 대신 찻잔을 내려놓았다. 잔이 탁자에 닿는 소리가
유난히 크게 울렸다. 아니, 그렇게 느껴진 것인지도 몰랐다.
"앉아도 되겠나?"
"의자가 부족하진 않으니."
그 말투. 십 년 전과 똑같았다. 변한 것은 눈빛뿐이었다.
예전에는 차가웠다. 지금은—텅 비어 있었다.
""",
                    why_good="대화에 행동 삽입. 감각 디테일. 시간 경과 암시. 눈빛으로 변화 표현",
                    tags=["대화", "행동", "변화"],
                ),
            ],
        }

    def get_few_shot_prompt(self, agent_type: AgentType, context: dict = None) -> str:
        """Few-Shot 예시 프롬프트 생성"""
        if agent_type == AgentType.ANALYST:
            exemplars = self.analyst_exemplars.get(self.genre, self.analyst_exemplars.get("wuxia", []))
        elif agent_type == AgentType.ARCHITECT:
            exemplars = self.architect_exemplars.get(self.genre, self.architect_exemplars.get("wuxia", []))
        else:  # WRITER
            exemplars = self.writer_exemplars.get(self.genre, self.writer_exemplars.get("wuxia", []))

        if not exemplars:
            return ""

        lines = ["[V51.3 우수 예시 참고]"]
        lines.append("다음은 높은 품질의 예시입니다. 이 수준을 목표로 하세요:\n")

        for i, ex in enumerate(exemplars[:2], 1):  # 최대 2개
            lines.append(f"--- 예시 {i}: {ex.title} ---")
            lines.append(ex.content.strip())
            lines.append(f"[왜 좋은가]: {ex.why_good}")
            lines.append("")

        return "\n".join(lines)

    # ================================================================
    # 2. ANTI-PATTERN INJECTION
    # ================================================================

    def _init_anti_patterns(self) -> None:
        """안티패턴 라이브러리 초기화"""

        self.anti_patterns = {
            "analyst": {
                "wuxia": [
                    ("매 Arc마다 비급 획득", "비급은 전체 작품에서 2-3회로 제한"),
                    ("모든 적이 주인공을 과소평가", "일부 적은 처음부터 경계해야 함"),
                    ("우연한 만남의 반복", "만남에 인과관계 부여 필요"),
                    ("매번 위기→기적적 탈출", "때로는 패배/후퇴 필요"),
                    ("Arc마다 새 여자 등장", "기존 인물 관계 심화 우선"),
                ],
                "hunter": [
                    ("매 던전마다 레벨업", "성장 속도 조절 필요"),
                    ("항상 솔로 플레이", "팀워크 에피소드 배치"),
                    ("스킬 무한 습득", "스킬 개수 제한, 성장 방향 선택"),
                ],
                "investment": [
                    ("모든 투자 성공", "실패 경험으로 성장 표현"),
                    ("정보만으로 승리", "판단력과 실행력 강조"),
                ],
            },
            "architect": {
                "wuxia": [
                    ("모든 씬이 비슷한 길이", "중요도에 따라 분량 차등"),
                    ("씬 전환 없이 시간 점프", "전환 기법 명시 필요"),
                    ("클리프행어 없이 종료", "반드시 다음 화 기대감 유발"),
                    ("장소 변경만으로 씬 구분", "감정/상황 변화가 씬 구분 기준"),
                    ("5개 씬 전부 액션", "완급 조절로 리듬감 부여"),
                ],
            },
            "writer": {
                "wuxia": [
                    ("'매우', '정말', '굉장히' 남발", "구체적 묘사로 대체"),
                    ("감정 직접 명명 ('슬펐다', '화났다')", "신체 반응으로 표현"),
                    ("'그는 ~했다' 반복", "다양한 문장 구조 사용"),
                    ("설명으로 긴장감 해소", "독자가 추론하게 유도"),
                    ("모든 대화에 '말했다' 사용", "행동/침묵으로 대체"),
                    ("내공/경지 숫자 나열", "체감되는 묘사로 전환"),
                    ("'갑자기', '순간' 남용", "전조/복선으로 자연스럽게"),
                ],
            },
        }

    def get_anti_pattern_prompt(self, agent_type: AgentType) -> str:
        """안티패턴 회피 프롬프트 생성"""
        agent_key = agent_type.value
        patterns = self.anti_patterns.get(agent_key, {}).get(self.genre, [])

        if not patterns:
            return ""

        lines = ["[V51.3 회피해야 할 패턴]"]
        lines.append("다음 패턴은 품질을 저하시킵니다. 반드시 피하세요:\n")

        for bad, good in patterns:
            lines.append(f"❌ {bad}")
            lines.append(f"   → ✅ {good}")
            lines.append("")

        return "\n".join(lines)

    # ================================================================
    # 3. SELF-CRITIQUE CHAIN
    # ================================================================

    def _init_critique_templates(self) -> None:
        """자가 검토 템플릿 초기화"""

        self.critique_templates = {
            "analyst": """
[Arc 설계 자가 검토]
생성한 Arc를 다음 기준으로 평가하세요:

1. 독창성 (1-10): 기존 Arc와 차별화되는가?
   - 비슷한 전개가 이전에 있었는가?
   - 예측 가능한 클리셰인가?

2. 인과성 (1-10): 사건들이 논리적으로 연결되는가?
   - "우연히"가 과도하게 사용되지 않았는가?
   - 캐릭터 동기가 명확한가?

3. 감정선 (1-10): 독자 감정이 설계되어 있는가?
   - 긴장/이완의 리듬이 있는가?
   - 클라이맥스가 명확한가?

4. 성장 대가: 주인공 성장에 대가가 있는가?

[결과]
총점 35점 이상이면 제출, 미만이면 수정 후 재생성
""",
            "architect": """
[Blueprint 자가 검토]
생성한 Blueprint를 다음 기준으로 평가하세요:

1. 구조 (1-10): 씬 배치가 효과적인가?
   - 오프닝이 이전 화와 자연스럽게 연결되는가?
   - 씬 간 전환이 매끄러운가?
   - 완급 조절이 되어 있는가?

2. 클리프행어 (1-10): 다음 화 기대감을 유발하는가?
   - 단순 궁금증이 아닌 긴장감인가?
   - 해결의 실마리가 보이되 확실하지 않은가?

3. 밀도 (1-10): 각 씬의 정보량이 적절한가?
   - 불필요한 씬이 없는가?
   - 씬당 예상 분량이 800-1200자인가?

[결과]
총점 25점 이상이면 제출, 미만이면 수정
""",
            "writer": """
[원고 자가 검토]
생성한 원고를 다음 기준으로 평가하세요:

1. 문장력 (1-10):
   - '매우/정말/굉장히' 사용 횟수는?
   - 감정을 직접 명명하지 않고 보여주는가?
   - 문장 길이가 다양한가?

2. 감각 묘사 (1-10):
   - 시각 외 감각(청각, 촉각, 후각)이 있는가?
   - 환경 묘사가 분위기를 강화하는가?

3. 대화 (1-10):
   - 캐릭터별 말투가 구분되는가?
   - 대화에 행동/반응이 삽입되어 있는가?
   - '~라고 말했다' 반복이 없는가?

4. Blueprint 반영 (1-10):
   - 모든 핵심 씬이 포함되었는가?
   - 클리프행어가 효과적인가?

[결과]
총점 35점 이상이면 제출, 미만이면 문제 영역 수정
""",
        }

    def get_self_critique_prompt(self, agent_type: AgentType) -> str:
        """자가 검토 프롬프트 반환"""
        return self.critique_templates.get(agent_type.value, "")

    def generate_critique_request(self, output: str, agent_type: AgentType) -> str:
        """LLM에 자가 검토를 요청하는 프롬프트 생성"""
        template = self.get_self_critique_prompt(agent_type)
        output_excerpt = smart_truncate(output or "", max_chars=3000, head_chars=1650)

        return f"""
다음 출력물을 검토하고 점수를 매기세요.

[출력물]
{output_excerpt}  # 토큰 절약

{template}

JSON 형식으로 응답:
{{
    "scores": {{"criteria1": 8, "criteria2": 7, ...}},
    "total": 32,
    "pass": true/false,
    "improvements": ["개선점1", "개선점2"]
}}
"""

    # ================================================================
    # 통합 인터페이스
    # ================================================================

    def get_analyst_enhancement(self, arc_num: int, prev_arcs: list[dict] = None) -> str:
        """Analyst용 통합 지능 향상 프롬프트"""
        parts = []

        # 1. Few-Shot
        few_shot = self.get_few_shot_prompt(AgentType.ANALYST)
        if few_shot:
            parts.append(few_shot)

        # 2. Anti-Pattern
        anti = self.get_anti_pattern_prompt(AgentType.ANALYST)
        if anti:
            parts.append(anti)

        # 3. 이전 Arc 패턴 분석 (반복 방지)
        if prev_arcs and len(prev_arcs) >= 2:
            recent_themes = []
            for arc in prev_arcs[-3:]:
                theme = arc.get("theme", arc.get("핵심_갈등", ""))
                if theme:
                    recent_themes.append(theme)

            if recent_themes:
                parts.append(f"[최근 Arc 테마 - 반복 금지]\n{', '.join(recent_themes)}")

        # 4. Self-Critique 안내
        parts.append(self.get_self_critique_prompt(AgentType.ANALYST))

        return "\n\n".join(parts)

    def get_architect_enhancement(self, ep_num: int, arc_data: dict = None, prev_blueprint: dict = None) -> str:
        """Architect용 통합 지능 향상 프롬프트"""
        parts = []

        # 1. Few-Shot
        few_shot = self.get_few_shot_prompt(AgentType.ARCHITECT)
        if few_shot:
            parts.append(few_shot)

        # 2. Anti-Pattern
        anti = self.get_anti_pattern_prompt(AgentType.ARCHITECT)
        if anti:
            parts.append(anti)

        # 3. 아크 내 위치 기반 가이드
        if arc_data:
            try:
                ep_start = int(arc_data.get("ep_start", 1))
            except (TypeError, ValueError):
                ep_start = 1
            try:
                ep_end = int(arc_data.get("ep_end", 5))
            except (TypeError, ValueError):
                ep_end = 5
            position = ep_num - ep_start + 1
            total = ep_end - ep_start + 1

            position_guide = {
                1: "Arc 시작: 설정/갈등 제시에 집중. 클리프행어로 다음 화 유인",
                2: "전개 초반: 갈등 심화, 장애물 등장. 위기 고조",
                3: "중반: 반전 또는 새 정보 공개. 예상 뒤집기",
                4: "클라이맥스 준비: 최고 긴장점 직전. 결전 암시",
                5: "Arc 종결: 클라이맥스 + 다음 Arc 복선. 해소와 새 시작",
            }
            guide = position_guide.get(position, "")
            if guide:
                parts.append(f"[Arc 내 위치: {position}/{total}화]\n{guide}")

        # 4. Self-Critique 안내
        parts.append(self.get_self_critique_prompt(AgentType.ARCHITECT))

        return "\n\n".join(parts)

    def get_writer_enhancement(self, ep_num: int, blueprint: dict = None, prev_manuscript: str = "") -> str:
        """Writer용 통합 지능 향상 프롬프트"""
        parts = []

        # 1. Few-Shot
        few_shot = self.get_few_shot_prompt(AgentType.WRITER)
        if few_shot:
            parts.append(few_shot)

        # 2. Anti-Pattern
        anti = self.get_anti_pattern_prompt(AgentType.WRITER)
        if anti:
            parts.append(anti)

        # 3. 이전 원고 문체 분석 (반복 방지)
        if prev_manuscript and len(prev_manuscript) > 500:
            # 간단한 패턴 감지
            import re

            warnings = []

            # 반복 표현 감지
            very_count = len(re.findall(r"매우|정말|굉장히|너무", prev_manuscript))
            if very_count > 5:
                warnings.append(f"'매우/정말/굉장히' {very_count}회 사용 → 구체적 묘사로 대체")

            suddenly_count = len(re.findall(r"갑자기|순간|문득", prev_manuscript))
            if suddenly_count > 3:
                warnings.append(f"'갑자기/순간' {suddenly_count}회 → 전조를 통한 자연스러운 전개로")

            said_count = len(re.findall(r"말했다|대답했다|물었다", prev_manuscript))
            if said_count > 10:
                warnings.append(f"대화 태그 과다 ({said_count}회) → 행동/침묵으로 대체")

            if warnings:
                parts.append("[이전 화 문체 경고]\n" + "\n".join(warnings))

        # 4. Self-Critique 안내
        parts.append(self.get_self_critique_prompt(AgentType.WRITER))

        return "\n\n".join(parts)

    def quick_quality_check(self, text: str, agent_type: AgentType) -> dict[str, Any]:
        """
        빠른 품질 체크 (LLM 없이 Python으로)

        Returns:
            Dict with 'score', 'issues', 'pass'
        """
        import re

        issues = []
        score = 100

        if agent_type == AgentType.WRITER:
            # 반복 표현
            very_count = len(re.findall(r"매우|정말|굉장히|너무", text))
            if very_count > 5:
                issues.append(f"과도한 강조어 ({very_count}회)")
                score -= very_count * 2

            # 감정 직접 명명
            emotion_count = len(re.findall(r"슬[펐펍]|화[났나]|기[뻤쁜]|행복", text))
            if emotion_count > 3:
                issues.append(f"감정 직접 명명 ({emotion_count}회)")
                score -= emotion_count * 3

            # 단조로운 문장
            said_count = len(re.findall(r"말했다|대답했다", text))
            if said_count > 10:
                issues.append(f"대화 태그 반복 ({said_count}회)")
                score -= said_count

            # 문장 다양성 (간단 체크)
            sentences = re.split(r"[.!?]", text)
            if sentences:
                lengths = [len(s.strip()) for s in sentences if s.strip()]
                if lengths:
                    avg_len = sum(lengths) / len(lengths)
                    variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
                    if variance < 100:  # 너무 균일
                        issues.append("문장 길이 단조로움")
                        score -= 10

        elif agent_type == AgentType.ARCHITECT:
            # 씬 개수 체크
            scene_count = len(re.findall(r"[Ss]cene|씬\s*\d|장면\s*\d", text))
            if scene_count < 4:
                issues.append(f"씬 부족 ({scene_count}개)")
                score -= 15
            elif scene_count > 7:
                issues.append(f"씬 과다 ({scene_count}개)")
                score -= 10

            # 클리프행어 체크
            if not re.search(r"클리프|절벽|긴장|다음|계속", text[-500:]):
                issues.append("클리프행어 약함")
                score -= 15

        elif agent_type == AgentType.ANALYST:
            # 화별 구분 체크
            episode_markers = len(re.findall(r"\d화|제\d|화별", text))
            if episode_markers < 3:
                issues.append("화별 전개 불명확")
                score -= 10

            # 감정선 체크
            if not re.search(r"감정|심리|내면|갈등", text):
                issues.append("감정선 설계 부족")
                score -= 10

        score = max(0, min(100, score))
        return {"score": score, "issues": issues, "pass": score >= 70 and len(issues) <= 2}
