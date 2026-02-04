"""
[V60.80] Blueprint Ensemble Generator
병렬로 3개 Blueprint 후보 생성 후 최적 선택

전략:
- Strategy A: 액션 중심 (긴장도 높음, 전투/추격/대결)
- Strategy B: 감정 중심 (캐릭터 심리, 갈등/화해/성장)
- Strategy C: 대화 중심 (관계 발전, 정보 교환, 음모)

내부적으로 Two-Phase 방식 적용:
1. 구조 생성 (scene_breakdown)
2. 상세화 (integrated_scenario)
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base_agent import BaseAgent


# Blueprint 생성 전략
BLUEPRINT_STRATEGIES = [
    {
        "name": "action_focused",
        "display": "액션 중심",
        "directive": """
[전략: 액션 중심]
- 긴장도를 높게 유지하세요 (7-9/10)
- 전투, 추격, 대결 씬을 중심으로 구성하세요
- 빠른 템포와 역동적인 전개를 강조하세요
- 감정 묘사는 최소화하고 행동으로 보여주세요
""",
        "tension_range": (7, 9)
    },
    {
        "name": "emotion_focused",
        "display": "감정 중심",
        "directive": """
[전략: 감정 중심]
- 캐릭터의 내면 심리를 깊이 있게 다루세요
- 갈등, 화해, 성장의 순간을 부각하세요
- 대화 속 감정의 미묘한 변화를 묘사하세요
- 긴장도는 중간 수준으로 유지하세요 (4-6/10)
""",
        "tension_range": (4, 6)
    },
    {
        "name": "dialogue_focused",
        "display": "대화 중심",
        "directive": """
[전략: 대화 중심]
- 캐릭터 간 대화를 통해 이야기를 전개하세요
- 정보 교환, 음모, 협상 씬을 중심으로 구성하세요
- 대사를 통해 캐릭터 성격과 관계를 드러내세요
- 서브텍스트(말 속에 숨겨진 의미)를 활용하세요
""",
        "tension_range": (3, 7)
    }
]


# Blueprint 생성 프롬프트 템플릿
BLUEPRINT_GENERATION_PROMPT = """
[V60.80 BLUEPRINT ENSEMBLE - {strategy_display}]

당신은 웹소설 에피소드 설계 전문가입니다.
Arc 전술서를 바탕으로 제{ep_num}화 Blueprint를 설계하세요.

╔══════════════════════════════════════════════════════════════╗
║ 🔒 [V61] 주인공 정보 - 반드시 이 이름을 사용하세요!           ║
╠══════════════════════════════════════════════════════════════╣
║ 주인공 이름: {protagonist_name}                               ║
║ → 모든 씬에서 '{protagonist_name}'만 사용하세요               ║
║ → '주인공', '그', '청년' 등 대명사 사용 금지                  ║
╚══════════════════════════════════════════════════════════════╝

### [Arc 전술서 - 이번 화 핵심]
{arc_focus}

### [제약 조건]
{constraints}

{strategy_directive}

### [이전 화 정보]
{prev_info}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### [출력 형식 - 반드시 JSON만 출력]

{{
    "ep_num": {ep_num},
    "title": "에피소드 제목 (10자 이내)",
    "scene_breakdown": {{
        "scene_1": {{
            "title": "씬 제목",
            "location": "장소",
            "characters": ["등장인물1", "등장인물2"],
            "summary": "씬 요약 (50자 이내)",
            "tension": 5,
            "key_events": ["이벤트1", "이벤트2"]
        }},
        "scene_2": {{...}},
        "scene_3": {{...}},
        "scene_4": {{...}}
    }},
    "integrated_scenario": "전체 에피소드 시나리오 (1000자 이상, 씬별 흐름을 자연스럽게 연결)",
    "start_location": "시작 위치",
    "end_location": "종료 위치",
    "time_flow": "시간 흐름 (예: 오전 → 저녁)",
    "ending_hook": "다음 화 연결 훅 (50자 이내)",
    "protagonist_state": {{
        "mood": "감정 상태",
        "injuries": "부상 상태",
        "equipment": ["소지품"]
    }}
}}

### [필수 조건]
1. scene_breakdown은 최소 3개, 최대 5개 씬
2. integrated_scenario는 최소 1000자 이상
3. 이전 화 종료 위치에서 시작해야 함
4. 정지선(다음 화 내용)을 침범하지 말 것

반드시 유효한 JSON만 출력하세요.
"""


class BlueprintEnsembleGenerator(BaseAgent):
    """
    [V60.80] Blueprint Ensemble Generator

    병렬로 3개 Blueprint 후보 생성 후 최적 선택
    """

    def __init__(self, context, client, model_tier: str = "gemini-3-pro-preview"):
        super().__init__(context, client, model_tier)
        self.strategies = BLUEPRINT_STRATEGIES
        self.max_workers = 3

    def generate_ensemble(
        self,
        ep_num: int,
        arc_data: Dict,
        constraint_block: Dict,
        prev_blueprint: Optional[Dict] = None,
        feedback: str = "",
        protagonist_name: str = "주인공"  # [V61] 주인공 이름 (필수!)
    ) -> Tuple[Optional[Dict], List[Dict]]:
        """
        앙상블 Blueprint 생성

        Args:
            ep_num: 에피소드 번호
            arc_data: Arc 데이터
            constraint_block: 제약 조건 블록
            prev_blueprint: 직전 Blueprint
            feedback: 이전 REJECT 피드백
            protagonist_name: [V61] 주인공 이름 (환각 방지)

        Returns:
            (best_blueprint, all_candidates) - 최적 Blueprint와 모든 후보 리스트
        """
        candidates = []

        # Arc 포커스 추출
        arc_focus = constraint_block.get("must_focus", {}).get("content", "")
        if not arc_focus:
            tactical = arc_data.get("tactical_doc", "")
            if isinstance(tactical, dict):
                tactical = json.dumps(tactical, ensure_ascii=False)
            arc_focus = tactical[:2000]

        # 제약 조건 문자열
        constraints_str = self._format_constraints(constraint_block)

        # 이전 화 정보
        prev_info = self._format_prev_info(prev_blueprint)

        # 병렬 생성
        print(f"      🎲 [BPEnsemble] 3개 후보 병렬 생성 중... (주인공: {protagonist_name})")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for strategy in self.strategies:
                future = executor.submit(
                    self._generate_single,
                    ep_num=ep_num,
                    arc_focus=arc_focus,
                    constraints_str=constraints_str,
                    prev_info=prev_info,
                    strategy=strategy,
                    feedback=feedback,
                    protagonist_name=protagonist_name  # [V61] 주인공 이름 전달
                )
                futures[future] = strategy["name"]

            for future in as_completed(futures):
                strategy_name = futures[future]
                try:
                    result = future.result()
                    if result and isinstance(result, dict):
                        result["_strategy"] = strategy_name
                        candidates.append(result)
                        print(f"         ✓ {strategy_name} 생성 완료")
                except Exception as e:
                    print(f"         ✗ {strategy_name} 실패: {str(e)[:50]}")

        if not candidates:
            print(f"      ❌ [BPEnsemble] 모든 후보 생성 실패")
            return None, []

        # [V60.80] 후보 평가 - Python 영향 최소화 (콘텐츠 풍부도만)
        scored_candidates = []
        for candidate in candidates:
            score = self._evaluate_candidate(candidate, constraint_block)
            candidate["_score"] = score
            scored_candidates.append(candidate)

        # 점수순 정렬 (= 콘텐츠 길이순, Director가 판단할 재료 많은 순)
        scored_candidates.sort(key=lambda x: x.get("_score", 0), reverse=True)

        best = scored_candidates[0]
        best_strategy = best.get('_strategy', 'unknown')
        best_len = len(best.get('integrated_scenario', ''))
        print(f"      🏆 [BPEnsemble] 최적 후보: {best_strategy} ({best_len}자)")

        # [V60.80] Python 경고 수집 - Director 주의 포인트용 (투표 영향 없음)
        warnings = self.collect_warnings(best, constraint_block)
        if warnings:
            print(f"      ⚠️ [BPEnsemble] Director 주의 포인트 {len(warnings)}개:")
            for w in warnings[:3]:
                print(f"         - {w.get('message', '?')}")

        # 메타데이터 저장 (경고 포함 → Director에게 전달)
        best["_ensemble_meta"] = {
            "best_strategy": best_strategy,
            "best_length": best_len,
            "all_lengths": [(c.get("_strategy", "?"), len(c.get("integrated_scenario", ""))) for c in scored_candidates],
            "total_candidates": len(scored_candidates),
            "python_warnings": warnings  # Director가 집중해야 할 포인트
        }

        # 내부 메타 제거 (단, _ensemble_meta 유지)
        for c in scored_candidates:
            c.pop("_strategy", None)
            c.pop("_score", None)

        return best, scored_candidates

    def _generate_single(
        self,
        ep_num: int,
        arc_focus: str,
        constraints_str: str,
        prev_info: str,
        strategy: Dict,
        feedback: str = "",
        protagonist_name: str = "주인공"  # [V61] 주인공 이름
    ) -> Optional[Dict]:
        """단일 Blueprint 생성"""
        # [V60.80] 피드백 강화 주입 - Director 피드백은 반드시 반영
        extra_directive = ""
        if feedback:
            extra_directive = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 [CRITICAL] Director REJECT 피드백 - 이전 시도 실패 원인
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{feedback}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 위 피드백을 반드시 반영하세요. 동일한 실수 반복 시 다시 REJECT됩니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        prompt = BLUEPRINT_GENERATION_PROMPT.format(
            strategy_display=strategy["display"],
            ep_num=ep_num,
            protagonist_name=protagonist_name,  # [V61] 주인공 이름 주입
            arc_focus=self._escape_braces(arc_focus),
            constraints=self._escape_braces(constraints_str),
            strategy_directive=strategy["directive"] + extra_directive,
            prev_info=self._escape_braces(prev_info)
        )

        try:
            response = self.ask(prompt, temperature=0.7)  # 다양성을 위해 약간 높은 온도
            result = self._extract_json_robust(response)

            if not isinstance(result, dict):
                return None

            # 필수 필드 확인
            if "scene_breakdown" not in result or "integrated_scenario" not in result:
                return None

            return result

        except Exception as e:
            print(f"         [BPEnsemble] 생성 오류: {str(e)[:50]}")
            return None

    def _evaluate_candidate(self, candidate: Dict, constraint_block: Dict) -> int:
        """
        [V60.80] 후보 Blueprint 선택 - Python 영향 최소화

        철학: Python은 점수를 매기지 않음. 단순히 가장 풍부한 콘텐츠 선택.
        단, 씬 개수 4개 이하는 구조적 결함 → 당선 불가 수준 감점.
        Director가 최종 품질 판단. Python은 경고만 수집 (별도 처리).
        """
        # 기본 점수: integrated_scenario 길이 (= 콘텐츠 풍부도)
        integrated = candidate.get("integrated_scenario", "")
        if not isinstance(integrated, str):
            integrated = str(integrated) if integrated else ""

        score = len(integrated)

        # [V60.80] 씬 개수 체크 - 3개 이하면 당선 불가 (4개부터 OK)
        scenes = candidate.get("scene_breakdown", {})
        scene_count = len(scenes) if isinstance(scenes, (dict, list)) else 0

        if scene_count <= 3:
            # 당선 불가 수준의 대형 감점 (-100000)
            score -= 100000
            print(f"         ⚠️ 씬 {scene_count}개 (≤3) → 당선 불가")

        return score

    def collect_warnings(self, candidate: Dict, constraint_block: Dict) -> List[Dict]:
        """
        [V60.80] Python 경고 수집 - Director 주의 포인트용

        투표에 영향 없음! Director에게 "여기 집중해서 봐"라고 전달하는 용도.
        """
        warnings = []

        integrated = candidate.get("integrated_scenario", "")
        if not isinstance(integrated, str):
            integrated = str(integrated) if integrated else ""

        # 1. 분량 경고
        if len(integrated) < 800:
            warnings.append({
                "type": "length",
                "message": f"분량이 짧음 ({len(integrated)}자 < 800자)",
                "focus": "서사 밀도와 씬 전개 충분성 확인 필요"
            })

        # 2. 씬 개수 경고
        scenes = candidate.get("scene_breakdown", {})
        scene_count = len(scenes) if isinstance(scenes, dict) else 0
        if scene_count < 3:
            warnings.append({
                "type": "scene_count",
                "message": f"씬 개수 적음 ({scene_count}개)",
                "focus": "에피소드 구조의 완결성 확인 필요"
            })

        # 3. 정지선 위반 의심
        stop_line = constraint_block.get("stop_line", {})
        stop_content = stop_line.get("content", "")
        if stop_content and len(stop_content) > 10:
            stop_keywords = stop_content[:50]
            if stop_keywords in integrated:
                warnings.append({
                    "type": "stop_line",
                    "message": "정지선 위반 가능성",
                    "focus": f"다음 화 내용 침범 여부 확인: '{stop_keywords[:30]}...'"
                })

        # 4. 연속성 경고
        continuity = constraint_block.get("continuity", {})
        expected_location = continuity.get("location", "")
        start_location = candidate.get("start_location", "")
        if expected_location and start_location:
            if expected_location not in start_location and start_location not in expected_location:
                warnings.append({
                    "type": "continuity",
                    "message": f"위치 연속성 의심: {expected_location} → {start_location}",
                    "focus": "이전 화 종료 위치와의 연결 확인 필요"
                })

        return warnings

    def _format_constraints(self, constraint_block: Dict) -> str:
        """제약 조건 포맷팅"""
        lines = []

        # Must Focus
        must_focus = constraint_block.get("must_focus", {})
        if must_focus.get("key_events"):
            lines.append("[이번 화 필수 이벤트]")
            for event in must_focus["key_events"][:5]:
                lines.append(f"  - {event}")

        # Stop Line
        stop_line = constraint_block.get("stop_line", {})
        if stop_line.get("content"):
            lines.append(f"\n🚨 [정지선 - 절대 침범 금지]")
            lines.append(f"다음 화 내용: {stop_line['content'][:150]}")
            lines.append("→ 위 내용을 이번 화에서 다루면 REJECT")

        # Continuity
        continuity = constraint_block.get("continuity", {})
        if continuity.get("location"):
            lines.append(f"\n[연속성]")
            lines.append(f"  이전 화 종료 위치: {continuity['location']}")
            lines.append(f"  → 이 위치에서 시작해야 함")

        # Inherited State
        inherited = constraint_block.get("inherited_state", {})
        if inherited.get("equipment"):
            equip = inherited["equipment"]
            if isinstance(equip, list):
                equip = ", ".join(equip[:5])
            lines.append(f"\n[소지품]")
            lines.append(f"  {equip}")

        return "\n".join(lines) if lines else "(제약 없음)"

    def _format_prev_info(self, prev_blueprint: Optional[Dict]) -> str:
        """이전 Blueprint 정보 포맷팅"""
        if not prev_blueprint:
            return "(첫 에피소드 - 이전 화 없음)"

        lines = []

        ending_hook = prev_blueprint.get("ending_hook", "")
        if ending_hook:
            lines.append(f"엔딩 훅: {ending_hook}")

        end_location = prev_blueprint.get("end_location", "")
        if end_location:
            lines.append(f"종료 위치: {end_location}")

        protag_state = prev_blueprint.get("protagonist_state", {})
        if protag_state:
            mood = protag_state.get("mood", "")
            injuries = protag_state.get("injuries", "")
            if mood:
                lines.append(f"주인공 상태: {mood}")
            if injuries and injuries != "없음":
                lines.append(f"부상: {injuries}")

        return "\n".join(lines) if lines else "(이전 화 정보 없음)"


def create_blueprint_ensemble(context, client, model_tier: str = "gemini-3-pro-preview"):
    """BlueprintEnsembleGenerator 생성 헬퍼"""
    return BlueprintEnsembleGenerator(context, client, model_tier)
