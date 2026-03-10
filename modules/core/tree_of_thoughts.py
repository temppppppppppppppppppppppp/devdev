"""
[V53.5] Tree of Thoughts (ToT)
여러 추론 경로를 탐색하고 최선을 선택

핵심: 단일 생성 대신 여러 방향 탐색 후 최적 선택

원리:
1. 초기 문제에서 여러 접근 방향 생성
2. 각 방향을 독립적으로 발전
3. 각 경로 평가
4. 최고 경로 선택 또는 병합

비용: +$0.03/생성 (3개 경로 탐색 시)

사용:
    tot = TreeOfThoughts(api_client)
    result = tot.explore(
        task="이번 화 블루프린트 설계",
        context={"arc_data": arc, "prev_ep": prev},
        n_branches=3
    )
    best_output = result.best_path.output
"""

import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from modules.core.constants import AIModels
from modules.core.llm_generate import generate_content_via_router
from modules.core.tactical_utils import extract_episode_tactical


class ExplorationStrategy(Enum):
    """탐색 전략"""

    BREADTH_FIRST = "breadth_first"  # 너비 우선: 모든 경로 동시 발전
    BEST_FIRST = "best_first"  # 최선 우선: 높은 점수 경로만 발전
    RANDOM_SAMPLE = "random_sample"  # 무작위 샘플링


@dataclass
class ThoughtPath:
    """사고 경로"""

    id: int
    approach: str  # 접근 방식 설명
    reasoning: str  # 추론 과정
    output: str  # 최종 출력
    score: float  # 평가 점수 (0-100)
    strengths: list[str]  # 장점
    weaknesses: list[str]  # 약점


@dataclass
class ToTResult:
    """Tree of Thoughts 결과"""

    paths: list[ThoughtPath]
    best_path: ThoughtPath
    merged_output: str | None  # 병합 출력 (있으면)
    exploration_summary: str


class TreeOfThoughts:
    """Tree of Thoughts 시스템"""

    # 접근 방식 생성 프롬프트
    BRANCH_GENERATION_PROMPT = """당신은 창의적인 전략가입니다.

주어진 과제에 대해 {n_branches}가지 다른 접근 방식을 제안하세요.
각 접근 방식은 서로 다른 관점이나 전략을 사용해야 합니다.

[과제]
{task}

[컨텍스트]
{context}

각 접근 방식을 JSON 형식으로:
```json
{{
    "approaches": [
        {{
            "id": 1,
            "name": "접근 방식 이름",
            "description": "이 접근 방식의 핵심 아이디어",
            "focus": "무엇에 집중하는지",
            "trade_off": "장단점"
        }},
        ...
    ]
}}
```"""

    # 경로 발전 프롬프트
    PATH_DEVELOPMENT_PROMPT = """당신은 {approach_name} 전문가입니다.

다음 접근 방식으로 과제를 수행하세요:

[접근 방식]
{approach_description}

[과제]
{task}

[컨텍스트]
{context}

[지침]
- 이 접근 방식의 강점을 최대한 활용하세요
- 단점을 인지하고 보완하려 노력하세요
- 구체적이고 실행 가능한 결과물을 생성하세요

결과물을 직접 출력하세요 (JSON 포맷 필요 없음)."""

    # 경로 평가 프롬프트
    PATH_EVALUATION_PROMPT = """당신은 공정한 평가자입니다.

다음 결과물을 평가하세요:

[과제]
{task}

[결과물]
{output}

다음 기준으로 0-100점 평가:
1. **완성도** (30점): 과제 요구사항을 얼마나 충족하는가?
2. **창의성** (20점): 새롭고 흥미로운 요소가 있는가?
3. **일관성** (25점): 내부적으로 모순이 없는가?
4. **실행가능성** (25점): 실제로 사용 가능한 수준인가?

JSON 형식으로:
```json
{{
    "scores": {{
        "completeness": 0-30,
        "creativity": 0-20,
        "consistency": 0-25,
        "feasibility": 0-25
    }},
    "total": 0-100,
    "strengths": ["장점1", "장점2"],
    "weaknesses": ["약점1", "약점2"]
}}
```"""

    def __init__(self, api_client, model: str = AIModels.DEFAULT_ARCHITECT):
        """
        [V60.24] Gemini 3로 변경
        Args:
            api_client: Google GenAI 클라이언트
            model: 사용할 모델 (V60.24: Gemini 3)
        """
        self.client = api_client
        self.model = model
        self.enabled = True

    def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """LLM 호출"""
        try:
            response = generate_content_via_router(
                client=self.client,
                model=self.model,
                contents=prompt,
                config={"temperature": temperature, "max_output_tokens": 4096},
            )
            return response.text or ""  # [V70] None 방어
        except Exception as e:
            logging.warning(f"[TreeOfThoughts] LLM 호출 실패: {e}")
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

    def explore(
        self,
        task: str,
        context: dict[str, Any],
        n_branches: int = 3,
        strategy: ExplorationStrategy = ExplorationStrategy.BREADTH_FIRST,
        custom_generator: Callable = None,
    ) -> ToTResult:
        """
        Tree of Thoughts 탐색 실행

        Args:
            task: 수행할 과제
            context: 컨텍스트 정보
            n_branches: 탐색할 경로 수
            strategy: 탐색 전략
            custom_generator: 사용자 정의 생성 함수 (있으면 LLM 대신 사용)

        Returns:
            ToTResult
        """
        if not self.enabled:
            # 비활성화 시 단일 경로만
            return self._single_path_fallback(task, context, custom_generator)

        # 1. 접근 방식 생성
        approaches = self._generate_approaches(task, context, n_branches)

        if not approaches:
            return self._single_path_fallback(task, context, custom_generator)

        # 2. 각 경로 발전
        paths = []
        for i, approach in enumerate(approaches):
            if custom_generator:
                # 사용자 정의 생성기 사용
                output = custom_generator(approach)
            else:
                output = self._develop_path(task, context, approach)

            paths.append(
                ThoughtPath(
                    id=i + 1,
                    approach=approach.get("name", f"Approach {i + 1}"),
                    reasoning=approach.get("description", ""),
                    output=output,
                    score=0,
                    strengths=[],
                    weaknesses=[],
                )
            )

        # 3. 각 경로 평가
        for path in paths:
            evaluation = self._evaluate_path(task, path.output)
            path.score = evaluation.get("total", 50)
            path.strengths = evaluation.get("strengths", [])
            path.weaknesses = evaluation.get("weaknesses", [])

        # 4. 최선 경로 선택
        paths.sort(key=lambda x: x.score, reverse=True)
        best_path = paths[0]

        # 5. 결과 생성
        summary = self._generate_summary(paths)

        return ToTResult(
            paths=paths,
            best_path=best_path,
            merged_output=None,  # 단순 선택 (병합 옵션은 별도)
            exploration_summary=summary,
        )

    def _generate_approaches(self, task: str, context: dict[str, Any], n_branches: int) -> list[dict[str, str]]:
        """접근 방식 생성"""
        context_str = json.dumps(context, ensure_ascii=False, default=str)[:2000]

        prompt = self.BRANCH_GENERATION_PROMPT.format(
            n_branches=n_branches,
            task=task.replace("{", "{{").replace("}", "}}"),  # [V70] brace escape
            context=context_str.replace("{", "{{").replace("}", "}}"),  # [V70] JSON brace escape
        )

        response = self._call_llm(prompt, temperature=0.8)
        result = self._parse_json(response)

        approaches = result.get("approaches", [])
        if not isinstance(approaches, list):
            approaches = []

        # 충분한 접근 방식이 없으면 기본값 추가
        if len(approaches) < n_branches:
            default_approaches = [
                {"id": 1, "name": "보수적 접근", "description": "안전하고 검증된 방식", "focus": "안정성"},
                {"id": 2, "name": "창의적 접근", "description": "새롭고 독창적인 방식", "focus": "참신함"},
                {"id": 3, "name": "균형적 접근", "description": "장단점을 균형있게 고려", "focus": "조화"},
            ]
            while len(approaches) < n_branches and default_approaches:
                approaches.append(default_approaches.pop(0))

        return approaches[:n_branches]

    def _develop_path(self, task: str, context: dict[str, Any], approach: dict[str, str]) -> str:
        """경로 발전"""
        context_str = json.dumps(context, ensure_ascii=False, default=str)[:2000]

        prompt = self.PATH_DEVELOPMENT_PROMPT.format(
            approach_name=approach.get("name", "전문가"),
            approach_description=approach.get("description", ""),
            task=task.replace("{", "{{").replace("}", "}}"),  # [V70] brace escape
            context=context_str.replace("{", "{{").replace("}", "}}"),  # [V70] brace escape
        )

        return self._call_llm(prompt, temperature=0.6)

    def _evaluate_path(self, task: str, output: str) -> dict[str, Any]:
        """경로 평가"""
        prompt = self.PATH_EVALUATION_PROMPT.format(
            task=task.replace("{", "{{").replace("}", "}}"),  # [V70] brace escape
            output=output[:4000].replace("{", "{{").replace("}", "}}"),  # [V70] brace escape
        )

        response = self._call_llm(prompt, temperature=0.2)
        result = self._parse_json(response)

        if not result:
            # 파싱 실패 시 기본값
            return {"total": 60, "strengths": [], "weaknesses": []}

        return result

    def _generate_summary(self, paths: list[ThoughtPath]) -> str:
        """탐색 요약 생성"""
        lines = ["[V53.5 Tree of Thoughts 탐색 결과]"]
        lines.append(f"탐색 경로: {len(paths)}개\n")

        for path in paths:
            status = "✅ 최선" if path == paths[0] else "  "
            lines.append(f"{status} #{path.id} {path.approach}: {path.score}점")
            if path.strengths:
                lines.append(f"   장점: {', '.join(path.strengths[:2])}")

        return "\n".join(lines)

    def _single_path_fallback(self, task: str, context: dict[str, Any], custom_generator: Callable = None) -> ToTResult:
        """단일 경로 폴백"""
        if custom_generator:
            output = custom_generator({"name": "기본", "description": ""})
        else:
            context_str = json.dumps(context, ensure_ascii=False, default=str)[:2000]
            prompt = f"[과제]\n{task}\n\n[컨텍스트]\n{context_str}\n\n위 과제를 수행하세요."
            output = self._call_llm(prompt)

        path = ThoughtPath(
            id=1,
            approach="단일 경로",
            reasoning="ToT 비활성화 또는 폴백",
            output=output,
            score=70,
            strengths=[],
            weaknesses=[],
        )

        return ToTResult(
            paths=[path], best_path=path, merged_output=None, exploration_summary="단일 경로 생성 (ToT 비활성화)"
        )

    def explore_blueprint(
        self,
        ep_num: int,
        arc_data: dict[str, Any],
        prev_blueprint: dict[str, Any] = None,
        generator_fn: Callable = None,
        n_branches: int = 3,
    ) -> ToTResult:
        """
        블루프린트 전용 ToT 탐색

        Args:
            ep_num: 에피소드 번호
            arc_data: 아크 데이터
            prev_blueprint: 이전 블루프린트
            generator_fn: 블루프린트 생성 함수
            n_branches: 탐색 경로 수

        Returns:
            ToTResult (best_path.output이 최선의 블루프린트)
        """
        task = f"제 {ep_num}화 블루프린트 설계"
        context = {
            "ep_num": ep_num,
            "arc_tactical": extract_episode_tactical(
                arc_data.get("tactical_doc", ""),
                ep_num,
                episode_details=arc_data.get("episode_details"),
            )
            if arc_data
            else "",
            "arc_drive": arc_data.get("arc_drive", {}) if arc_data else {},
            "prev_cliffhanger": prev_blueprint.get("ending_hook", "") if prev_blueprint else "",
        }

        # 블루프린트 전용 접근 방식 (V55.2: 4분기)
        blueprint_approaches = [
            {"name": "긴장감 중심", "description": "긴장-이완 곡선을 극대화하는 씬 배치", "focus": "독자 몰입"},
            {"name": "캐릭터 중심", "description": "캐릭터 성장과 관계 변화에 집중", "focus": "감정선"},
            {"name": "플롯 중심", "description": "사건 전개와 복선 회수에 집중", "focus": "서사 추진"},
            {"name": "연속성 중심", "description": "직전 화 엔딩 계승 + 클리프행어 설계에 집중", "focus": "서사 연결"},
        ]

        paths = []
        for i, approach in enumerate(blueprint_approaches[:n_branches]):
            if generator_fn:
                # 접근 방식을 힌트로 전달
                output = generator_fn()
            else:
                output = self._develop_path(task, context, approach)

            paths.append(
                ThoughtPath(
                    id=i + 1,
                    approach=approach["name"],
                    reasoning=approach["description"],
                    output=output if isinstance(output, str) else json.dumps(output, ensure_ascii=False),
                    score=0,
                    strengths=[],
                    weaknesses=[],
                )
            )

        # [G2] paths가 비어있으면 빈 결과 반환
        if not paths:
            return ToTResult(paths=[], best_path=None, merged_output=None, exploration_summary="No paths generated")

        # 평가
        for path in paths:
            evaluation = self._evaluate_blueprint(path.output)
            path.score = evaluation.get("total", 50)
            path.strengths = evaluation.get("strengths", [])
            path.weaknesses = evaluation.get("weaknesses", [])

        paths.sort(key=lambda x: x.score, reverse=True)

        return ToTResult(
            paths=paths, best_path=paths[0], merged_output=None, exploration_summary=self._generate_summary(paths)
        )

    def _evaluate_blueprint(self, output: str) -> dict[str, Any]:
        """블루프린트 전용 평가 (Python 휴리스틱)"""
        score = 50  # 기본값
        strengths = []
        weaknesses = []

        # JSON 파싱 시도
        try:
            if isinstance(output, str):
                bp = json.loads(output)
            else:
                bp = output
        except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse failure
            bp = {}
            weaknesses.append("JSON 파싱 실패")
            return {"total": 30, "strengths": strengths, "weaknesses": weaknesses}

        # 필수 필드
        if bp.get("integrated_scenario"):
            score += 15
            strengths.append("시나리오 존재")
        else:
            weaknesses.append("시나리오 없음")

        if bp.get("scene_breakdown"):
            scene_count = len(bp["scene_breakdown"])
            if 4 <= scene_count <= 7:
                score += 20
                strengths.append(f"적절한 씬 수 ({scene_count})")
            elif scene_count > 0:
                score += 10
                weaknesses.append(f"씬 수 부적절 ({scene_count})")
        else:
            weaknesses.append("씬 없음")

        if bp.get("ending_hook") or bp.get("cliffhanger"):
            score += 10
            strengths.append("클리프행어 존재")

        return {"total": min(100, score), "strengths": strengths, "weaknesses": weaknesses}

    # ═══════════════════════════════════════════════════════════════════════════════
    # [V55.1] Arc 전용 ToT 탐색 - Stage 2 필살기
    # ═══════════════════════════════════════════════════════════════════════════════

    def explore_arc(
        self,
        arc_no: int,
        vol_strategy: str,
        curr_block: dict[str, Any],
        prev_arc_context: str,
        assets: dict[str, Any] = None,
        feedback: str = "",
        num_branches: int = 3,
        depth: int = 2,
        protagonist_name: str = "주인공",  # [V60.18] 주인공 이름 (필수!)
    ) -> dict[str, Any] | None:
        """
        [V55.1] Arc 전용 ToT 탐색 (Stage 2 필살기)

        3가지 접근 방식으로 Arc 설계 → 평가 → 최선 선택

        Args:
            arc_no: Arc 번호
            vol_strategy: Volume 전략 문서
            curr_block: 현재 블록 DNA
            prev_arc_context: 이전 Arc 맥락
            assets: AssetLibrary
            feedback: 이전 REJECT 피드백
            num_branches: 탐색 경로 수
            depth: 탐색 깊이
            protagonist_name: [V60.18] 주인공 이름 (환각 방지)

        Returns:
            최선의 Arc 설계 또는 None
        """
        if not self.client:
            return None

        logging.info(f" [ToT Arc] {num_branches}개 분기 탐색 시작 (Arc {arc_no}, 주인공: {protagonist_name})")

        # Arc 전용 접근 방식 (V55.2: 4분기)
        arc_approaches = [
            {
                "name": "인과율 중심",
                "description": "이전 Arc 결과를 철저히 계승하고 다음 Arc로 연결되는 인과 고리 구축",
                "focus": "연속성",
                "prompt_hint": "이전 Arc에서 획득한 아이템/수여물/상태를 정확히 계승. 새로운 획득은 기존 소지품과 중복 불가.",
            },
            {
                "name": "긴장감 중심",
                "description": "5화 구조 내에서 긴장-이완 곡선을 최적화",
                "focus": "몰입도",
                "prompt_hint": "각 화마다 긴장 상승/하강을 명확히 구분. 클라이막스는 4-5화에 배치.",
            },
            {
                "name": "캐릭터 중심",
                "description": "주인공과 NPC의 관계 변화, 성장에 집중",
                "focus": "감정선",
                "prompt_hint": "관계 변화는 점진적으로 (무시→의심→경외→충성). 급격한 변화 금지.",
            },
            {
                "name": "복선/회수 중심",
                "description": "이전 Arc의 복선 회수 + 새로운 복선 설치의 균형",
                "focus": "서사밀도",
                "prompt_hint": "최소 1개 이상의 기존 복선 회수. 새로운 복선은 3화 이내 회수 가능한 것만 설치.",
            },
        ]

        # 각 접근 방식으로 Arc 생성
        candidates = []
        for i, approach in enumerate(arc_approaches[:num_branches]):
            try:
                arc_design = self._generate_arc_with_approach(
                    arc_no=arc_no,
                    vol_strategy=vol_strategy,
                    curr_block=curr_block,
                    prev_arc_context=prev_arc_context,
                    assets=assets,
                    feedback=feedback,
                    approach=approach,
                    protagonist_name=protagonist_name,  # [V60.18]
                )

                if arc_design:
                    evaluation = self._evaluate_arc(arc_design, approach["focus"])
                    candidates.append(
                        {
                            "approach": approach["name"],
                            "design": arc_design,
                            "score": evaluation["total"],
                            "strengths": evaluation["strengths"],
                            "weaknesses": evaluation["weaknesses"],
                        }
                    )
                    logging.info(f"✅ [ToT Arc] 분기 {i + 1}/{num_branches} '{approach['name']}' 완료 (점수: {evaluation['total']})"
                    )

            except Exception as e:
                logging.warning(f" [ToT Arc] 분기 {i + 1} 실패: {e}")
                continue

        if not candidates:
            logging.warning(" [ToT Arc] 모든 분기 실패")
            return None

        # 최고 점수 선택
        candidates.sort(key=lambda x: x["score"], reverse=True)
        best = candidates[0]

        logging.info(f" [ToT Arc] 최선 선택: '{best['approach']}' (점수: {best['score']})")
        logging.info(f"강점: {', '.join(best['strengths'][:2])}")
        if best["weaknesses"]:
            logging.info(f"약점: {', '.join(best['weaknesses'][:2])}")

        return best["design"]

    def _generate_arc_with_approach(
        self,
        arc_no: int,
        vol_strategy: str,
        curr_block: dict[str, Any],
        prev_arc_context: str,
        assets: dict[str, Any],
        feedback: str,
        approach: dict[str, str],
        protagonist_name: str = "주인공",  # [V60.18]
    ) -> dict[str, Any] | None:
        """특정 접근 방식으로 Arc 생성"""
        prompt = f"""[V55.1 ToT Arc Generator: {approach["name"]} 접근]

당신은 {approach["focus"]} 전문가입니다.

##############################################################
# 🔒 [V60.18] 주인공 정보 - 반드시 이 이름을 사용!
##############################################################
주인공 이름: {protagonist_name}
→ tactical_doc에서 반드시 '{protagonist_name}'을 사용하세요!
→ 다른 이름(이현, 강민수 등)은 절대 사용 금지!
##############################################################

=== 접근 방식 ===
{approach["description"]}
힌트: {approach["prompt_hint"]}

=== 입력 정보 ===
Arc 번호: {arc_no}
Volume 전략: {self._escape(vol_strategy[:2000] if vol_strategy else "(없음)")}
현재 블록 DNA: {self._escape(json.dumps(curr_block, ensure_ascii=False) if curr_block else "(없음)")}
이전 Arc 맥락: {self._escape(prev_arc_context[:3000] if prev_arc_context else "(첫 Arc)")}
이전 REJECT 피드백: {self._escape(feedback[:1000] if feedback else "(없음)")}

=== 출력 JSON 스키마 ===
{{
    "arc_no": {arc_no},
    "tactical_doc": "5화 상세 전술 문서 (각 화별 핵심 사건 포함)",
    "joint_docs": {{
        "final_location": "Arc 마지막 위치",
        "physical_inventory": ["소지 아이템 목록"],
        "world_joint": "세계관 변화 요약"
    }},
    "state_constraints": {{
        "items_acquired": ["이번 Arc에서 새로 획득한 아이템만"],
        "items_consumed": ["이번 Arc에서 소모/파괴된 아이템"],
        "grants_received": ["이번 Arc에서 받은 수여물"]
    }},
    "hybrid_composition": {{
        "primary": "주 서사 패턴",
        "secondary": "부 서사 패턴"
    }}
}}

중요: {approach["prompt_hint"]}
반드시 JSON만 출력하세요."""

        try:
            response = generate_content_via_router(
                client=self.client,
                model=self.model,
                contents=prompt,
                config={"temperature": 0.6, "max_output_tokens": 8192, "response_mime_type": "application/json"},
            )

            try:  # [V70] response.text ValueError/None 방어
                text = response.text
            except (ValueError, AttributeError):
                text = None
            if not text:
                return None
            import re

            json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(text)

        except Exception as e:
            logging.warning(f" [ToT Arc] '{approach['name']}' 생성 오류: {e}")
            return None

    def _evaluate_arc(self, arc: dict[str, Any], focus: str) -> dict[str, Any]:
        """Arc 평가 (Python 휴리스틱)"""
        score = 50  # 기본값
        strengths = []
        weaknesses = []

        # 필수 필드 검증
        if arc.get("tactical_doc"):
            tactical = arc["tactical_doc"]
            score += 10
            strengths.append("전술문서 존재")

            # 길이 검증
            if len(tactical) > 1000:
                score += 10
                strengths.append(f"충분한 상세도({len(tactical)}자)")
            elif len(tactical) < 500:
                weaknesses.append("전술문서 너무 짧음")

            # 화별 구분 확인
            if "제1화" in tactical or "1화" in tactical:
                score += 5
                strengths.append("화별 구분 명확")
        else:
            weaknesses.append("전술문서 없음")
            score -= 20

        # joint_docs 검증
        joint = arc.get("joint_docs", {})
        if joint.get("final_location"):
            score += 5
            strengths.append("위치 정보 명확")
        if joint.get("physical_inventory"):
            inventory = joint["physical_inventory"]
            if isinstance(inventory, list) and len(inventory) > 0:
                score += 5
                strengths.append(f"소지품 {len(inventory)}개")

        # state_constraints 검증
        state = arc.get("state_constraints", {})
        # [BUG-F] protagonist_items 우선 폴백
        if state.get("protagonist_items") or state.get("items_acquired"):
            score += 5
        if state.get("grants_received"):
            score += 5
            strengths.append("수여물 추적")

        # 포커스별 보너스
        if focus == "연속성":
            if "계승" in str(arc) or "이전" in str(arc):
                score += 5
                strengths.append("연속성 의식")
        elif focus == "몰입도":
            if "긴장" in str(arc) or "클라이막스" in str(arc):
                score += 5
                strengths.append("긴장감 설계")
        elif focus == "감정선":
            if "관계" in str(arc) or "성장" in str(arc):
                score += 5
                strengths.append("캐릭터 성장")

        return {"total": min(100, max(0, score)), "strengths": strengths, "weaknesses": weaknesses}

    def _escape(self, text: str) -> str:
        """중괄호 이스케이프"""
        if not isinstance(text, str):
            return str(text)
        return text.replace("{", "{{").replace("}", "}}")
