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

# [V60.95] 원시인 모드 금지어 Guard (JSON 기반)
try:
    from modules.core.primitive_guard import get_primitive_constraint_section
    PRIMITIVE_GUARD_AVAILABLE = True
except ImportError:
    PRIMITIVE_GUARD_AVAILABLE = False


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


# [V60.98] 씬 프리셋 정의 - 장면/화자 전환 연출
SCENE_PRESETS = {
    "opening_hook": "화 시작, 독자 유입용. 시각 중심, 임팩트 있는 오프닝.",
    "daily_routine": "일상 묘사, 세계관 노출. 여유로운 호흡.",
    "tension_build": "긴장감 축적. 불안한 분위기, 짧은 문장.",
    "action_peak": "전투/액션 클라이맥스. 빠른 호흡, 시각 중심, 대사 최소.",
    "emotional_reveal": "감정 폭발, 내면 묘사. 느린 호흡, 대사/독백 중심.",
    "dialogue_duel": "설전/협상/대립. 대사 중심, 긴장감 있는 대화.",
    "villain_scheme": "★악역 시점 전환★ 음모/계략 노출. 독자에게 위협 암시.",
    "side_glimpse": "★조연 시점 전환★ 주인공 부재 상황, '저 사람 대단해!' 반응.",
    "flashback": "과거 회상. 몽환적 전환, 과거 시제.",
    "omniscient_hint": "★전지적 시점★ 복선/떡밥 암시. '그는 아직 몰랐다...'",
    "cliffhanger": "화 끝 훅. 급박한 전개, 긴장 최고조에서 끊기.",
    "resolution": "갈등 해소, 정리. 여운 있는 마무리."
}

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
╠══════════════════════════════════════════════════════════════╣
{protagonist_instructions}
╚══════════════════════════════════════════════════════════════╝

### [Arc 전술서 - 이번 화 핵심]
{arc_focus}

### [제약 조건]
{constraints}

{strategy_directive}

### [이전 화 정보]
{prev_info}

### [V60.95 고밀도 HUD - 주인공 상태]
{hud_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### [V60.98 씬 프리셋 - 장면/화자 전환 연출]
각 씬에 적합한 프리셋을 선택하세요. 시점 전환을 통해 다채로운 연출이 가능합니다.

| 프리셋 | 용도 |
|--------|------|
| opening_hook | 화 시작, 독자 유입 |
| daily_routine | 일상 묘사, 세계관 노출 |
| tension_build | 긴장감 축적 |
| action_peak | 전투/액션 클라이맥스 |
| emotional_reveal | 감정 폭발, 내면 묘사 |
| dialogue_duel | 설전/협상/대립 |
| villain_scheme | ★악역 시점★ 음모 노출 (예: 악당이 함정 준비) |
| side_glimpse | ★조연 시점★ 주인공 칭송/반응 (예: "저 사람 대체 뭐지?") |
| flashback | 과거 회상 |
| omniscient_hint | ★전지적 시점★ 복선 암시 (예: "그는 아직 몰랐다...") |
| cliffhanger | 화 끝 훅 |
| resolution | 갈등 해소, 정리 |

💡 시점 전환 팁:
- 악당 음모 씬 → villain_scheme (악역 시점으로 위협감 부여)
- 주인공 활약 직후 → side_glimpse (조연 시점으로 "대단해!" 반응)
- 떡밥 투척 → omniscient_hint (전지적 시점으로 독자에게만 정보 제공)

### [출력 형식 - 반드시 JSON만 출력]

{{
    "ep_num": {ep_num},
    "title": "에피소드 제목 (10자 이내)",
    "scene_breakdown": {{
        "scene_1": {{
            "type": "opening_hook",
            "title": "씬 제목",
            "location": "장소",
            "characters": ["등장인물1", "등장인물2"],
            "summary": "씬 요약 (50자 이내)",
            "tension": 5,
            "key_events": ["이벤트1", "이벤트2"]
        }},
        "scene_2": {{"type": "tension_build", ...}},
        "scene_3": {{"type": "action_peak", ...}},
        "scene_4": {{"type": "cliffhanger", ...}}
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
5. [V60.98] 각 씬에 반드시 type(프리셋) 필드 포함할 것
6. [V60.98] 시점 전환 프리셋(villain_scheme, side_glimpse, omniscient_hint)은 상황에 맞게 적극 활용

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
        protagonist_name: str = "주인공",  # [V61] 주인공 이름 (필수!)
        protagonist_config: Dict = None,  # [V60.90] 주인공 설정 (world_origin, incarnation_type)
        state_tracker=None  # [V60.95] StateTracker (고밀도 HUD 전달)
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
            protagonist_config: [V60.90] 주인공 설정 {world_origin, incarnation_type}
            state_tracker: [V60.95] StateTracker (고밀도 HUD - 17+ 필드, NPC 레지스트리)

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

        # [V60.95] 고밀도 HUD 컨텍스트 구축
        hud_context = self._build_hud_context(state_tracker, ep_num)

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
                    protagonist_name=protagonist_name,  # [V61] 주인공 이름 전달
                    protagonist_config=protagonist_config,  # [V60.90] 주인공 설정 전달
                    hud_context=hud_context  # [V60.95] 고밀도 HUD 주입
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

        # [V60.85] Python 최소 기준 필터링 - 씬 4개 이상만 통과
        # 철학: Python은 "당선 불가" 후보만 걸러냄, 선택은 Director가 함
        qualified_candidates = []
        disqualified = []

        for candidate in candidates:
            strategy_name = candidate.get("_strategy", "unknown")
            scenes = candidate.get("scene_breakdown", {})
            scene_count = len(scenes) if isinstance(scenes, (dict, list)) else 0
            integrated = candidate.get("integrated_scenario", "")
            integrated_len = len(integrated) if isinstance(integrated, str) else 0

            # 최소 기준: 씬 4개 이상, 시나리오 500자 이상
            if scene_count >= 4 and integrated_len >= 500:
                candidate["_qualified"] = True
                candidate["_scene_count"] = scene_count
                candidate["_length"] = integrated_len
                qualified_candidates.append(candidate)
                print(f"         ✓ {strategy_name}: 통과 (씬 {scene_count}개, {integrated_len}자)")
            else:
                disqualified.append((strategy_name, scene_count, integrated_len))
                print(f"         ✗ {strategy_name}: 탈락 (씬 {scene_count}개, {integrated_len}자)")

        if not qualified_candidates:
            print(f"      ❌ [BPEnsemble] 모든 후보 최소 기준 미달")
            return None, candidates  # 원본 반환 (디버깅용)

        # [V60.85] Director가 선택할 수 있도록 후보 목록 반환
        # Python은 선택하지 않음 - Director에게 전체 전달
        print(f"      📋 [BPEnsemble] {len(qualified_candidates)}개 후보 → Director 선택 대기")

        # 메타데이터 저장 (Director 비교용)
        for idx, candidate in enumerate(qualified_candidates):
            strategy_name = candidate.get("_strategy", "unknown")
            candidate["_ensemble_meta"] = {
                "candidate_index": idx,
                "strategy": strategy_name,
                "scene_count": candidate.get("_scene_count", 0),
                "length": candidate.get("_length", 0),
                "total_candidates": len(qualified_candidates),
                "disqualified": disqualified
            }
            # 임시 필드 정리
            candidate.pop("_strategy", None)
            candidate.pop("_qualified", None)
            candidate.pop("_scene_count", None)
            candidate.pop("_length", None)

        # [V60.85] 첫 번째 후보를 "대표"로 반환하되, 전체 후보 리스트도 함께 반환
        # Validator에서 Director가 전체 비교 후 최종 선택
        return qualified_candidates[0], qualified_candidates

    def _generate_single(
        self,
        ep_num: int,
        arc_focus: str,
        constraints_str: str,
        prev_info: str,
        strategy: Dict,
        feedback: str = "",
        protagonist_name: str = "주인공",  # [V61] 주인공 이름
        protagonist_config: Dict = None,  # [V60.90] 주인공 설정
        hud_context: str = ""  # [V60.95] 고밀도 HUD 컨텍스트
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

        # [V60.90] protagonist_config 기반 지시사항 생성
        protagonist_instructions = self._build_protagonist_instructions(protagonist_config)

        prompt = BLUEPRINT_GENERATION_PROMPT.format(
            strategy_display=strategy["display"],
            ep_num=ep_num,
            protagonist_name=protagonist_name,  # [V61] 주인공 이름 주입
            protagonist_instructions=protagonist_instructions,  # [V60.90] 주인공 설정 지시
            arc_focus=self._escape_braces(arc_focus),
            constraints=self._escape_braces(constraints_str),
            strategy_directive=strategy["directive"] + extra_directive,
            prev_info=self._escape_braces(prev_info),
            hud_context=self._escape_braces(hud_context) if hud_context else "(상태 정보 없음)"  # [V60.95]
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

    def _build_protagonist_instructions(self, protagonist_config: Dict) -> str:
        """
        [V60.90] protagonist_config 기반 프롬프트 지시사항 생성

        Args:
            protagonist_config: {world_origin: '원시인'|'현대인', incarnation_type: '회귀자'|'빙의자'|'환생자'}

        Returns:
            프롬프트에 삽입할 지시사항 문자열
        """
        if not protagonist_config:
            return "║ (주인공 설정 정보 없음)"

        lines = []
        world_origin = protagonist_config.get('world_origin', '원시인')
        incarnation_type = protagonist_config.get('incarnation_type', '회귀자')

        # [V60.96] 장르 추출 (장르별 금지어 적용)
        genre = "wuxia"
        try:
            if hasattr(self, 'context') and hasattr(self.context, 'db'):
                bible = self.context.db.load_anchor('bible')
                if bible:
                    genre = bible.get('_genre', 'wuxia')
        except:
            pass

        # [V60.96] world_origin 기반 지시 (장르별 JSON 기반 PrimitiveGuard)
        if world_origin == '원시인':
            if PRIMITIVE_GUARD_AVAILABLE:
                prim_section = get_primitive_constraint_section(protagonist_config, genre=genre, length="short")
                lines.append(f"║ {prim_section}")
            else:
                lines.append("║ ⚠️ [원시인 모드] 현대 용어 절대 금지!")
        else:
            lines.append("║ 📝 [현대인 모드] 주인공은 현대 사회를 알고 있음")

        # incarnation_type 기반 지시
        if incarnation_type == '회귀자':
            lines.append("║ 🔄 [회귀자] 미래를 알고 있음 (합리적 이유 없이는 내면 독백으로 처리)")
        elif incarnation_type == '빙의자':
            lines.append("║ 👤 [빙의자] 원래 인물의 기억/관계를 의식")
        elif incarnation_type == '환생자':
            lines.append("║ 👶 [환생자] 전생의 기억이 있음")

        return "\n".join(lines) if lines else "║ (주인공 설정 정보 없음)"

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

    def _build_hud_context(self, state_tracker, ep_num: int) -> str:
        """
        [V60.95] StateTracker에서 고밀도 HUD 컨텍스트 구축

        PresetRegistry 기반 17+ 필드를 프롬프트에 주입
        NPC 레지스트리 정보도 포함

        Args:
            state_tracker: StateTracker 인스턴스
            ep_num: 현재 에피소드 번호

        Returns:
            str: 프롬프트용 HUD 컨텍스트
        """
        if not state_tracker:
            return ""

        lines = []

        # 1. 주인공 상태 (고밀도 필드)
        try:
            # 직전 에피소드 상태 가져오기
            prev_state = None
            if ep_num > 1 and hasattr(state_tracker, 'episode_states'):
                prev_state = state_tracker.episode_states.get(ep_num - 1)

            if prev_state:
                state_dict = prev_state.to_dict() if hasattr(prev_state, 'to_dict') else {}

                lines.append("[주인공 현재 상태]")

                # 핵심 필드 (항상 표시)
                core_fields = ['location', 'internal_energy', 'injuries']
                for field in core_fields:
                    if field in state_dict:
                        lines.append(f"  - {field}: {state_dict[field]}")

                # 확장 필드 (있으면 표시)
                extended_fields = [
                    ('realm', '경지'), ('reputation', '평판'), ('mental_state', '정신상태'),
                    ('faction', '소속'), ('rank', '지위'), ('gold', '재화'),
                    ('awakening_grade', '각성등급'), ('gate_clearance', '클리어 게이트'),
                    ('net_worth', '자산'), ('market_reputation', '시장평판'),
                    ('mana', '마나'), ('skills', '스킬'), ('titles', '칭호')
                ]

                for field, display in extended_fields:
                    if field in state_dict and state_dict[field]:
                        value = state_dict[field]
                        # 리스트는 쉼표로 연결
                        if isinstance(value, list):
                            value = ', '.join(str(v) for v in value[:5])  # 최대 5개
                        lines.append(f"  - {display}: {value}")

                # 소지품
                items = state_dict.get('items', [])
                weapons = state_dict.get('weapons', [])
                if items or weapons:
                    all_items = weapons + items
                    lines.append(f"  - 소지품: {', '.join(str(i) for i in all_items[:8])}")

                # 관계
                relationships = state_dict.get('relationships', {})
                if relationships:
                    rel_str = ', '.join(f"{k}:{v}" for k, v in list(relationships.items())[:5])
                    lines.append(f"  - 관계: {rel_str}")

        except Exception as e:
            lines.append(f"  (상태 로드 오류: {str(e)[:30]})")

        # 2. NPC 레지스트리 (살아있는 주요 NPC)
        try:
            if hasattr(state_tracker, 'npc_registry') and state_tracker.npc_registry:
                alive_npcs = [
                    (name, info) for name, info in state_tracker.npc_registry.items()
                    if info.get('status') != 'dead'
                ][:10]  # 최대 10명

                if alive_npcs:
                    lines.append("")
                    lines.append("[등장 가능 NPC]")
                    for name, info in alive_npcs:
                        role = info.get('role', '')
                        relationship = info.get('relationship', '')
                        faction = info.get('faction', '')

                        npc_desc = f"  - {name}"
                        details = []
                        if role:
                            details.append(role)
                        if faction:
                            details.append(faction)
                        if relationship:
                            details.append(f"관계:{relationship}")
                        if details:
                            npc_desc += f" ({', '.join(details)})"
                        lines.append(npc_desc)

                # 사망 NPC 경고
                dead_npcs = [
                    name for name, info in state_tracker.npc_registry.items()
                    if info.get('status') == 'dead'
                ]
                if dead_npcs:
                    lines.append("")
                    lines.append(f"⚠️ [사망 NPC - 등장 금지]: {', '.join(dead_npcs[:5])}")

        except Exception as e:
            pass  # NPC 로드 실패 시 무시

        return "\n".join(lines) if lines else "(상태 정보 없음)"

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
