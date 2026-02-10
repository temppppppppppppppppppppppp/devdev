"""
[V54.4] Two-Phase Generation System (Enhanced)

Arc 설계 및 원고 생성을 두 단계로 분리하여 품질과 일관성을 높이는 시스템

=== Arc Generation (V49.4) ===
Phase 1 (Skeleton): 구조적 프레임워크 생성
- beat_sequence (화별 비트)
- state_constraints (상태 제약)
- ep_count, ep_start, ep_end

Phase 2 (Flesh): 상세 전술 문서 생성
- tactical_doc (상세 전술)
- joint_docs (연결 문서)
- status_shadow (상태 그림자)

=== Manuscript Generation (V54.4 NEW) ===
Phase 1 (Structure): 원고 구조 설계
- scene_outlines (씬별 개요)
- dialogue_skeleton (대화 골격)
- emotional_arc (감정 곡선)

Phase 2 (Content): 본문 작성
- 풍부한 묘사와 대화
- 감각적 디테일
- 캐릭터 음성

장점:
1. Phase 1에서 제약 조건 검증 후 Phase 2 진행 → 재시도율 감소
2. Phase 1은 낮은 온도로 정확성 확보, Phase 2는 높은 온도로 창의성 확보
3. Phase 1 결과를 Phase 2 입력으로 사용 → 일관성 향상
4. [V54.4] 원고도 2단계 생성 지원 → 품질 향상
"""

import json
from typing import Dict, Any, Optional
from google.genai import types


# [V49.4] Phase 1 Skeleton Schema
ARC_SKELETON_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "arc_no": types.Schema(type=types.Type.INTEGER),
        "ep_count": types.Schema(type=types.Type.INTEGER, minimum=2, maximum=6),
        "ep_start": types.Schema(type=types.Type.INTEGER),
        "ep_end": types.Schema(type=types.Type.INTEGER),
        "title": types.Schema(type=types.Type.STRING),
        "beat_sequence": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING)
        ),
        "hybrid_composition": types.Schema(
            type=types.Type.OBJECT,
            properties={
                "primary": types.Schema(type=types.Type.STRING),
                "secondary": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(type=types.Type.STRING)
                ),
                "mixing_logic": types.Schema(type=types.Type.STRING)
            },
            required=["primary", "mixing_logic"]
        ),
        "state_constraints": types.Schema(
            type=types.Type.OBJECT,
            properties={
                "arc_start_state": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "location": types.Schema(type=types.Type.STRING),
                        "equipment": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(type=types.Type.STRING)
                        ),
                        "injuries": types.Schema(type=types.Type.STRING),
                        "internal_energy": types.Schema(type=types.Type.INTEGER)
                    },
                    required=["location", "equipment"]
                ),
                "arc_end_state": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "location": types.Schema(type=types.Type.STRING),
                        "equipment": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(type=types.Type.STRING)
                        ),
                        "injuries": types.Schema(type=types.Type.STRING),
                        "internal_energy": types.Schema(type=types.Type.INTEGER)
                    },
                    required=["location", "equipment"]
                ),
                "items_acquired": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(type=types.Type.STRING)
                ),
                "items_consumed": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(type=types.Type.STRING)
                )
            },
            required=["arc_start_state", "arc_end_state", "items_acquired", "items_consumed"]
        )
    },
    required=["arc_no", "ep_count", "ep_start", "ep_end", "title", "beat_sequence", "state_constraints"]
)


PHASE1_SKELETON_PROMPT = """
[🚨 SYSTEM: TWO-PHASE GENERATION - SKELETON ONLY]

당신은 서사 구조 설계의 1단계를 수행합니다.
이 단계에서는 **상세 전술 문서(tactical_doc) 없이** 구조적 프레임워크만 생성합니다.

### 역할
Arc의 뼈대(Skeleton)를 설계하라:
1. 화별 비트(beat_sequence) - 각 화의 핵심 전개 한 줄
2. 상태 제약(state_constraints) - 시작/종료 상태, 획득/소모 아이템
3. 패턴 구성(hybrid_composition) - 사용할 서사 패턴

### [🚨 CRITICAL] 제약 조건 준수
{constraint_block}

### [📐 설계 맥락]
- 이전 Arc 상태: {prev_arc_context}
- 현재 설계 대상: {curr_block}
- 다음 Arc 목표: {next_block}

### [📦 가용 자산]
{assets}

### [🎯 복선 미션]
{assigned_seeds_info}

### [Output Format - SKELETON ONLY]
tactical_doc 필드를 포함하지 마십시오. 아래 구조만 반환하십시오:

{{
    "arc_no": {arc_no},
    "ep_count": {ep_count},
    "ep_start": {ep_start},
    "ep_end": {ep_end},
    "title": "아크 제목",
    "beat_sequence": [
        "제 {ep_start}화: [비트] 핵심 전개",
        "..."
    ],
    "hybrid_composition": {{
        "primary": "주 패턴",
        "secondary": ["부 패턴"],
        "mixing_logic": "패턴 조합 전략"
    }},
    "state_constraints": {{
        "arc_start_state": {{
            "location": "시작 위치",
            "equipment": ["소지품"],
            "injuries": "부상 상태",
            "internal_energy": 80
        }},
        "arc_end_state": {{
            "location": "종료 위치",
            "equipment": ["종료 시 소지품"],
            "injuries": "종료 시 부상",
            "internal_energy": 60
        }},
        "items_acquired": ["새로 획득하는 아이템"],
        "items_consumed": ["소모되는 아이템"]
    }}
}}
"""


PHASE2_FLESH_PROMPT = """
[🚨 SYSTEM: TWO-PHASE GENERATION - FLESH ONLY]

당신은 서사 구조 설계의 2단계를 수행합니다.
1단계에서 확정된 뼈대(Skeleton)를 바탕으로 **상세 전술 문서(tactical_doc)**를 작성합니다.

████████████████████████████████████████████████████████████████████████████████
█   🚨 [V60.38] tactical_doc 분량 필수 - 위반 시 즉시 REJECT                   █
█   ⚠️ 총 분량: 최소 (화 수 × 500)자 이상                                      █
█   ⚠️ 1,500자 미만 = CRITICAL REJECT (시스템 자동 거부)                        █
████████████████████████████████████████████████████████████████████████████████

### [🔒 LOCKED SKELETON - 수정 불가]
아래 구조는 1단계에서 확정된 것으로 **절대 변경할 수 없습니다**:
{skeleton_data}

### [📜 전술 문서 작성 지침]
1. 위 skeleton의 beat_sequence 각 항목을 500자 이상으로 확장하십시오.
2. state_constraints의 상태 변화를 자연스럽게 서사에 녹여내십시오.
3. 각 화별로 [제 N화 전술 설계] 섹션을 분리하여 작성하십시오.
4. 총 분량 (화 수 × 500)자 이상을 확보하십시오.

### [📐 맥락]
- 이전 Arc 상태: {prev_arc_context}
- 장르 가이드: {genre_prompt}

### [🎯 복선 미션]
{assigned_seeds_info}

### [V60.40] 화간 상태 체크포인트 필수
각 화는 반드시 시작 상태와 종료 상태를 명시하라:
- 시작 상태: 위치, 내공%, 부상, 소지품 (이전 화 종료 상태와 동일)
- 종료 상태: 위치, 내공%, 부상, 획득/소모 아이템

### [Output Format - FLESH ONLY]
skeleton 데이터에 tactical_doc과 joint_docs, status_shadow를 추가하여 반환하십시오:

{{
    ... (skeleton 필드 그대로 복사),
    "tactical_doc": "[V60.40] 각 화마다 시작/종료 상태 체크포인트 필수. 화당 500자 이상.",
    "joint_docs": {{
        "final_location": "Arc 종료 시점의 구체적 장소",
        "physical_inventory": ["현재 소지품"],
        "world_joint": "다음 Arc가 계승할 환경 변화"
    }},
    "status_shadow": {{
        "internal_energy_loss": "예상 내공 소모량",
        "expected_injuries": "예상 부상",
        "item_consumption": ["소모 아이템"]
    }}
}}
"""


class TwoPhaseGenerator:
    """
    [V49.4] Two-Phase Arc Generation Engine

    Phase 1: 구조적 Skeleton 생성 (낮은 온도, 스키마 강제)
    Phase 2: 상세 Flesh 생성 (중간 온도, 창의성 확보)
    """

    def __init__(self, client, context):
        """
        Args:
            client: Gemini API 클라이언트
            context: ProjectContext (guard, db 등)
        """
        self.client = client
        self.context = context
        # [V60.24] Gemini 3로 변경
        self.primary_model = "gemini-3-pro-preview"  # Phase 1: 정밀 모델
        self.secondary_model = "gemini-3-pro-preview"  # Phase 2: 동일 품질 유지

    def generate_arc(
        self,
        arc_no: int,
        ep_start: int,
        ep_count: int,
        prev_arc_context: str,
        curr_block: Dict,
        next_block: Dict,
        assets: Dict,
        assigned_seeds_info: str,
        constraint_block: str = ""
    ) -> Optional[Dict]:
        """
        Two-Phase Arc 생성

        Args:
            arc_no: Arc 번호
            ep_start: 시작 화수
            ep_count: 총 화수
            prev_arc_context: 이전 Arc 상태
            curr_block: 현재 블록 데이터
            next_block: 다음 블록 데이터
            assets: 가용 자산
            assigned_seeds_info: 복선 미션
            constraint_block: 제약 조건 블록

        Returns:
            완성된 Arc 데이터 또는 None
        """
        print(f"      📐 [TwoPhase] Phase 1: Skeleton 생성 시작 (Arc {arc_no})")

        # Phase 1: Skeleton 생성
        skeleton = self._generate_skeleton(
            arc_no=arc_no,
            ep_start=ep_start,
            ep_count=ep_count,
            prev_arc_context=prev_arc_context,
            curr_block=curr_block,
            next_block=next_block,
            assets=assets,
            assigned_seeds_info=assigned_seeds_info,
            constraint_block=constraint_block
        )

        if not skeleton:
            print(f"      🚨 [TwoPhase] Phase 1 실패")
            return None

        # Skeleton 검증
        validation_result = self._validate_skeleton(skeleton, constraint_block)
        if not validation_result.get("valid", False):
            print(f"      🚨 [TwoPhase] Skeleton 검증 실패: {validation_result.get('reason')}")
            return None

        print(f"      ✅ [TwoPhase] Phase 1 완료. Phase 2: Flesh 생성 시작")

        # Phase 2: Flesh 생성
        complete_arc = self._generate_flesh(
            skeleton=skeleton,
            prev_arc_context=prev_arc_context,
            assigned_seeds_info=assigned_seeds_info
        )

        if not complete_arc:
            print(f"      🚨 [TwoPhase] Phase 2 실패")
            return None

        print(f"      ✅ [TwoPhase] Arc {arc_no} Two-Phase 생성 완료")
        return complete_arc

    def _generate_skeleton(
        self,
        arc_no: int,
        ep_start: int,
        ep_count: int,
        prev_arc_context: str,
        curr_block: Dict,
        next_block: Dict,
        assets: Dict,
        assigned_seeds_info: str,
        constraint_block: str
    ) -> Optional[Dict]:
        """Phase 1: Skeleton 생성"""
        try:
            # 프롬프트 생성
            prompt = PHASE1_SKELETON_PROMPT.format(
                constraint_block=constraint_block or "(없음)",
                prev_arc_context=self._escape_braces(prev_arc_context or "시작점"),
                curr_block=self._escape_braces(json.dumps(curr_block, ensure_ascii=False)),
                next_block=self._escape_braces(json.dumps(next_block, ensure_ascii=False) if next_block else "(없음)"),
                assets=self._escape_braces(json.dumps(assets, ensure_ascii=False) if assets else "{}"),
                assigned_seeds_info=self._escape_braces(assigned_seeds_info or "(없음)"),
                arc_no=arc_no,
                ep_count=ep_count,
                ep_start=ep_start,
                ep_end=ep_start + ep_count - 1
            )

            # API 호출 (낮은 온도, 스키마 강제)
            response = self.client.models.generate_content(
                model=self.primary_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # 낮은 온도 → 정확성
                    max_output_tokens=4096,
                    response_mime_type="application/json",
                    response_schema=ARC_SKELETON_SCHEMA
                )
            )

            skeleton = json.loads(response.text)
            return skeleton

        except Exception as e:
            print(f"      🚨 [TwoPhase] Skeleton 생성 오류: {e}")
            return None

    def _generate_flesh(
        self,
        skeleton: Dict,
        prev_arc_context: str,
        assigned_seeds_info: str
    ) -> Optional[Dict]:
        """Phase 2: Flesh 생성"""
        try:
            ep_start = skeleton.get("ep_start", 1)
            # [V60.73] ep_count 기반 ep_end 폴백 (기존 +4 오류 수정)
            ep_count = skeleton.get("ep_count", 5)
            ep_end = skeleton.get("ep_end", ep_start + ep_count - 1)

            # 장르 프롬프트
            genre_prompt = ""
            if hasattr(self.context, 'guard') and self.context.guard:
                genre_prompt = self.context.guard.get_v20_purism_prompt()

            # 프롬프트 생성
            prompt = PHASE2_FLESH_PROMPT.format(
                skeleton_data=self._escape_braces(json.dumps(skeleton, ensure_ascii=False, indent=2)),
                prev_arc_context=self._escape_braces(prev_arc_context or "시작점"),
                genre_prompt=self._escape_braces(genre_prompt),
                assigned_seeds_info=self._escape_braces(assigned_seeds_info or "(없음)"),
                ep_start=ep_start,
                ep_end=ep_end
            )

            # API 호출 (중간 온도, 창의성)
            response = self.client.models.generate_content(
                model=self.secondary_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,  # 중간 온도 → 창의성
                    max_output_tokens=8192,
                    response_mime_type="application/json"
                )
            )

            flesh_data = json.loads(response.text)

            # Skeleton과 Flesh 병합
            complete_arc = {**skeleton, **flesh_data}

            # 필수 필드 보장
            if "tactical_doc" not in complete_arc:
                print("      ⚠️ [TwoPhase] tactical_doc 누락, 기본값 설정")
                complete_arc["tactical_doc"] = self._generate_fallback_tactical(skeleton)

            return complete_arc

        except Exception as e:
            print(f"      🚨 [TwoPhase] Flesh 생성 오류: {e}")
            # Skeleton만이라도 반환
            skeleton["tactical_doc"] = self._generate_fallback_tactical(skeleton)
            return skeleton

    def _validate_skeleton(self, skeleton: Dict, constraint_block: str) -> Dict:
        """Skeleton 제약 조건 검증"""
        result = {"valid": True, "reason": "", "warnings": []}

        # 필수 키 검증
        required_keys = ["arc_no", "ep_count", "ep_start", "ep_end", "beat_sequence", "state_constraints"]
        missing = [k for k in required_keys if k not in skeleton]
        if missing:
            result["valid"] = False
            result["reason"] = f"필수 키 누락: {missing}"
            return result

        # state_constraints 검증
        state_constraints = skeleton.get("state_constraints", {})
        items_acquired = state_constraints.get("items_acquired", [])

        # constraint_block에서 금지 아이템 추출 (간단한 파싱)
        if constraint_block and "획득 금지" in constraint_block:
            for item in items_acquired:
                if item in constraint_block:
                    result["valid"] = False
                    result["reason"] = f"금지된 아이템 획득 시도: {item}"
                    return result

        return result

    def _generate_fallback_tactical(self, skeleton: Dict) -> str:
        """Fallback: skeleton으로부터 기본 tactical_doc 생성"""
        beats = skeleton.get("beat_sequence", [])
        ep_start = skeleton.get("ep_start", 1)

        tactical_parts = []
        for i, beat in enumerate(beats):
            ep_num = ep_start + i
            tactical_parts.append(f"[제 {ep_num}화 전술 설계]\n{beat}\n(상세 전술 생성 필요)")

        return "\n\n".join(tactical_parts)

    def _escape_braces(self, text: str) -> str:
        """중괄호 이스케이프"""
        if not isinstance(text, str):
            return str(text)
        return text.replace("{", "{{").replace("}", "}}")


def create_two_phase_generator(client, context) -> TwoPhaseGenerator:
    """TwoPhaseGenerator 인스턴스 생성 헬퍼"""
    return TwoPhaseGenerator(client, context)


# ============================================================================
# [V54.4] Two-Phase Manuscript Generation
# ============================================================================

MANUSCRIPT_STRUCTURE_PROMPT = """
[V54.4 TWO-PHASE MANUSCRIPT - PHASE 1: STRUCTURE]

당신은 원고의 뼈대를 설계합니다.
블루프린트를 기반으로 각 씬의 구조만 설계하세요.

### [블루프린트]
{blueprint}

### [이전 원고 마지막 부분]
{prev_ending}

### [컨텍스트]
{context}

### [Output - STRUCTURE ONLY]
실제 원고를 작성하지 마세요. 구조만 반환하세요:

```json
{{
    "scene_count": {scene_count},
    "scene_structures": [
        {{
            "scene_id": 1,
            "scene_type": "씬 유형 (대화/액션/내면/전환)",
            "location": "장소",
            "characters": ["등장 인물"],
            "purpose": "이 씬의 목적",
            "emotional_beat": "감정 (상승/하강/절정/이완)",
            "key_dialogue_points": ["핵심 대화 포인트 1", "포인트 2"],
            "sensory_focus": "주요 감각 (시각/청각/촉각 등)",
            "word_count_target": 800
        }}
    ],
    "emotional_arc": {{
        "start": "시작 감정",
        "climax": "절정 감정",
        "end": "종결 감정"
    }},
    "cliffhanger_setup": "엔딩 훅 준비"
}}
```
"""

MANUSCRIPT_CONTENT_PROMPT = """
[V54.4 TWO-PHASE MANUSCRIPT - PHASE 2: CONTENT]

당신은 1단계에서 설계된 구조를 바탕으로 실제 원고를 작성합니다.

### [🔒 LOCKED STRUCTURE - 수정 불가]
{structure}

### [작성 지침]
1. 위 structure의 각 scene을 풍부하게 확장하세요.
2. 각 씬의 emotional_beat를 정확히 반영하세요.
3. key_dialogue_points를 자연스럽게 대화로 구현하세요.
4. sensory_focus에 맞는 감각 묘사를 포함하세요.
5. word_count_target에 맞춰 분량을 조절하세요.

### [이전 원고 마지막]
{prev_ending}

### [컨텍스트]
{context}

### [문체 가이드]
{style_guide}

실제 원고만 출력하세요. JSON 포맷 없이 순수 본문만 작성하세요.
"""


class TwoPhaseManuscriptGenerator:
    """
    [V54.4] Two-Phase Manuscript Generator

    Phase 1: 구조 설계 (낮은 온도)
    Phase 2: 본문 작성 (중간 온도)
    """

    def __init__(self, client, model: str = "gemini-2.0-flash"):
        """
        Args:
            client: Gemini API 클라이언트
            model: 사용할 모델
        """
        self.client = client
        self.model = model
        self.enabled = True

    def generate(
        self,
        blueprint: Dict[str, Any],
        prev_ending: str = "",
        context: Dict[str, Any] = None,
        style_guide: str = ""
    ) -> Optional[str]:
        """
        Two-Phase 원고 생성

        Args:
            blueprint: 블루프린트 데이터
            prev_ending: 이전 원고 마지막 부분
            context: 추가 컨텍스트
            style_guide: 문체 가이드

        Returns:
            생성된 원고 또는 None
        """
        if not self.enabled:
            return None

        # 씬 개수 추출
        scene_count = len(blueprint.get("scene_breakdown", {}))
        if scene_count == 0:
            scene_count = 5  # 기본값

        print(f"      📐 [TwoPhaseMS] Phase 1: 구조 설계 시작")

        # Phase 1: 구조 설계
        structure = self._generate_structure(
            blueprint=blueprint,
            prev_ending=prev_ending,
            context=context,
            scene_count=scene_count
        )

        if not structure:
            print(f"      🚨 [TwoPhaseMS] Phase 1 실패")
            return None

        print(f"      ✅ [TwoPhaseMS] Phase 1 완료. Phase 2: 본문 작성 시작")

        # Phase 2: 본문 작성
        manuscript = self._generate_content(
            structure=structure,
            prev_ending=prev_ending,
            context=context,
            style_guide=style_guide
        )

        if not manuscript:
            print(f"      🚨 [TwoPhaseMS] Phase 2 실패")
            return None

        print(f"      ✅ [TwoPhaseMS] Two-Phase 원고 생성 완료 ({len(manuscript)}자)")
        return manuscript

    def _generate_structure(
        self,
        blueprint: Dict[str, Any],
        prev_ending: str,
        context: Dict[str, Any],
        scene_count: int
    ) -> Optional[Dict]:
        """Phase 1: 구조 설계"""
        try:
            prompt = MANUSCRIPT_STRUCTURE_PROMPT.format(
                blueprint=self._escape_braces(json.dumps(blueprint, ensure_ascii=False)[:4000]),
                prev_ending=self._escape_braces(prev_ending[-1500:] if prev_ending else "(없음)"),
                context=self._escape_braces(json.dumps(context, ensure_ascii=False)[:2000] if context else "{}"),
                scene_count=scene_count
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": 0.3,  # 낮은 온도 → 정확성
                    "max_output_tokens": 4096,
                    "response_mime_type": "application/json"
                }
            )

            # JSON 파싱
            import re
            text = response.text
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(text)

        except Exception as e:
            print(f"      🚨 [TwoPhaseMS] 구조 설계 오류: {e}")
            return None

    def _generate_content(
        self,
        structure: Dict,
        prev_ending: str,
        context: Dict[str, Any],
        style_guide: str
    ) -> Optional[str]:
        """Phase 2: 본문 작성"""
        try:
            prompt = MANUSCRIPT_CONTENT_PROMPT.format(
                structure=self._escape_braces(json.dumps(structure, ensure_ascii=False, indent=2)),
                prev_ending=self._escape_braces(prev_ending[-1500:] if prev_ending else "(없음)"),
                context=self._escape_braces(json.dumps(context, ensure_ascii=False)[:1500] if context else "{}"),
                style_guide=self._escape_braces(style_guide[:1000] if style_guide else "(기본 문체)")
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": 0.6,  # 중간 온도 → 창의성
                    "max_output_tokens": 8192
                }
            )

            return response.text

        except Exception as e:
            print(f"      🚨 [TwoPhaseMS] 본문 작성 오류: {e}")
            return None

    def _escape_braces(self, text: str) -> str:
        """중괄호 이스케이프"""
        if not isinstance(text, str):
            return str(text)
        return text.replace("{", "{{").replace("}", "}}")

    def get_summary(self, structure: Dict) -> str:
        """구조 요약"""
        if not structure:
            return "[TwoPhaseMS] 구조 없음"

        scenes = structure.get("scene_structures", [])
        emotional = structure.get("emotional_arc", {})

        return (
            f"[V54.4 Two-Phase Manuscript]\n"
            f"  씬 수: {len(scenes)}\n"
            f"  감정선: {emotional.get('start', '?')} → "
            f"{emotional.get('climax', '?')} → {emotional.get('end', '?')}\n"
            f"  목표 분량: {sum(s.get('word_count_target', 800) for s in scenes)}자"
        )


def create_manuscript_generator(client, model: str = "gemini-2.0-flash") -> TwoPhaseManuscriptGenerator:
    """TwoPhaseManuscriptGenerator 인스턴스 생성 헬퍼"""
    return TwoPhaseManuscriptGenerator(client, model)


# ============================================================================
# [V54.4.1] Two-Phase Blueprint Generation
# ============================================================================

BLUEPRINT_SKELETON_PROMPT = """
[V54.4.1 TWO-PHASE BLUEPRINT - PHASE 1: SKELETON]

당신은 에피소드 블루프린트의 뼈대를 설계합니다.
Arc 전술 문서를 기반으로 씬 구조만 설계하세요.

### [Arc 전술 문서]
{tactical_doc}

### [이전 블루프린트 엔딩 훅]
{prev_ending_hook}

### [제약 조건]
{constraints}

### [Output - SKELETON ONLY]
상세 시나리오를 작성하지 마세요. 구조만 반환하세요:

```json
{{
    "ep_num": {ep_num},
    "scene_count": 5,
    "scene_skeleton": [
        {{
            "scene_id": 1,
            "scene_type": "씬 유형 (대화/액션/내면/전환/훈련)",
            "location": "장소",
            "characters": ["등장인물"],
            "core_beat": "핵심 비트 (한 줄)",
            "tension_level": 3,
            "purpose": "씬 목적"
        }}
    ],
    "item_movements": {{
        "acquired": ["획득할 아이템"],
        "consumed": ["소모할 아이템"],
        "revealed": ["밝혀질 정보"]
    }},
    "emotional_trajectory": {{
        "start": "시작 감정",
        "peak": "절정 감정",
        "end": "종결 감정"
    }},
    "cliffhanger_type": "엔딩 훅 유형 (위기/반전/의문/긴장)"
}}
```
"""

BLUEPRINT_FLESH_PROMPT = """
[V54.4.1 TWO-PHASE BLUEPRINT - PHASE 2: FLESH]

당신은 1단계에서 설계된 뼈대를 바탕으로 상세 블루프린트를 작성합니다.

### [🔒 LOCKED SKELETON - 수정 불가]
{skeleton}

### [작성 지침]
1. 각 scene_skeleton 항목을 scene_breakdown의 상세 씬으로 확장하세요.
2. integrated_scenario를 작성하세요 (전체 에피소드 서사 요약, 1500자 이상).
3. item_movements를 바탕으로 아이템 변화를 자연스럽게 반영하세요.
4. emotional_trajectory에 맞춰 감정선을 설계하세요.
5. cliffhanger_type에 맞는 ending_hook을 작성하세요.

### [이전 블루프린트]
{prev_blueprint}

### [맥락]
{context}

### [Output Format]
```json
{{
    "ep_num": {ep_num},
    "arc_num": {arc_num},
    "volume_num": {volume_num},
    "scene_breakdown": {{
        "scene_1": {{
            "scene_type": "대화",
            "purpose": "씬 목적 상세",
            "characters": ["등장인물"],
            "beats": ["비트1", "비트2"],
            "emotional_note": "감정 노트",
            "spatial_anchor": "공간 앵커"
        }}
    }},
    "integrated_scenario": "전체 에피소드 서사 요약 (1500자 이상)",
    "ending_hook": "클리프행어 엔딩",
    "prev_cliffhanger": "{prev_ending_hook}",
    "relationship_changes": [],
    "time_flow": "시간 흐름"
}}
```
"""


class TwoPhaseBlueprintGenerator:
    """
    [V54.4.1] Two-Phase Blueprint Generator

    Phase 1: 구조적 Skeleton 설계 (낮은 온도)
    Phase 2: 상세 Flesh 작성 (중간 온도)

    장점:
    - Phase 1에서 씬 구조/아이템 이동 확정 → 일관성 향상
    - Phase 2에서 창의적 확장 → 품질 향상
    - 실패 시 Phase 1만 재시도 가능 → 비용 절감
    """

    def __init__(self, client, model: str = "gemini-2.5-flash"):
        """
        Args:
            client: Gemini API 클라이언트
            model: 사용할 모델
        """
        self.client = client
        self.model = model
        self.enabled = True

    def generate(
        self,
        ep_num: int,
        arc_num: int,
        volume_num: int,
        tactical_doc: str,
        prev_blueprint: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        constraints: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Two-Phase 블루프린트 생성

        Args:
            ep_num: 에피소드 번호
            arc_num: Arc 번호
            volume_num: 볼륨 번호
            tactical_doc: Arc 전술 문서
            prev_blueprint: 이전 블루프린트
            context: 추가 컨텍스트
            constraints: 제약 조건

        Returns:
            생성된 블루프린트 또는 None
        """
        if not self.enabled:
            return None

        prev_ending_hook = ""
        if prev_blueprint:
            prev_ending_hook = prev_blueprint.get("ending_hook", "")

        print(f"      📐 [TwoPhaseBP] Phase 1: Skeleton 설계 시작 (EP{ep_num})")

        # Phase 1: Skeleton 설계
        skeleton = self._generate_skeleton(
            ep_num=ep_num,
            tactical_doc=tactical_doc,
            prev_ending_hook=prev_ending_hook,
            constraints=constraints
        )

        if not skeleton:
            print(f"      🚨 [TwoPhaseBP] Phase 1 실패")
            return None

        # Skeleton 검증
        if not self._validate_skeleton(skeleton):
            print(f"      🚨 [TwoPhaseBP] Skeleton 검증 실패")
            return None

        print(f"      ✅ [TwoPhaseBP] Phase 1 완료. Phase 2: Flesh 작성 시작")

        # Phase 2: Flesh 작성
        blueprint = self._generate_flesh(
            skeleton=skeleton,
            ep_num=ep_num,
            arc_num=arc_num,
            volume_num=volume_num,
            prev_blueprint=prev_blueprint,
            prev_ending_hook=prev_ending_hook,
            context=context
        )

        if not blueprint:
            print(f"      🚨 [TwoPhaseBP] Phase 2 실패")
            return None

        print(f"      ✅ [TwoPhaseBP] Two-Phase 블루프린트 생성 완료")
        return blueprint

    def _generate_skeleton(
        self,
        ep_num: int,
        tactical_doc: str,
        prev_ending_hook: str,
        constraints: str
    ) -> Optional[Dict]:
        """Phase 1: Skeleton 생성"""
        try:
            prompt = BLUEPRINT_SKELETON_PROMPT.format(
                tactical_doc=self._escape_braces(tactical_doc[:5000] if tactical_doc else "(없음)"),
                prev_ending_hook=self._escape_braces(prev_ending_hook or "(첫 화)"),
                constraints=self._escape_braces(constraints or "(없음)"),
                ep_num=ep_num
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": 0.3,  # 낮은 온도 → 정확성
                    "max_output_tokens": 4096,
                    "response_mime_type": "application/json"
                }
            )

            # JSON 파싱
            import re
            text = response.text
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(text)

        except Exception as e:
            print(f"      🚨 [TwoPhaseBP] Skeleton 생성 오류: {e}")
            return None

    def _generate_flesh(
        self,
        skeleton: Dict,
        ep_num: int,
        arc_num: int,
        volume_num: int,
        prev_blueprint: Dict[str, Any],
        prev_ending_hook: str,
        context: Dict[str, Any]
    ) -> Optional[Dict]:
        """Phase 2: Flesh 생성"""
        try:
            prompt = BLUEPRINT_FLESH_PROMPT.format(
                skeleton=self._escape_braces(json.dumps(skeleton, ensure_ascii=False, indent=2)),
                prev_blueprint=self._escape_braces(
                    json.dumps(prev_blueprint, ensure_ascii=False)[:3000] if prev_blueprint else "(없음)"
                ),
                context=self._escape_braces(
                    json.dumps(context, ensure_ascii=False)[:2000] if context else "{}"
                ),
                ep_num=ep_num,
                arc_num=arc_num,
                volume_num=volume_num,
                prev_ending_hook=self._escape_braces(prev_ending_hook or "(첫 화)")
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": 0.5,  # 중간 온도 → 창의성
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json"
                }
            )

            # JSON 파싱
            import re
            text = response.text
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                blueprint = json.loads(json_match.group(1))
            else:
                blueprint = json.loads(text)

            # Skeleton 정보 병합
            blueprint["_skeleton"] = skeleton
            blueprint["item_movements"] = skeleton.get("item_movements", {})

            return blueprint

        except Exception as e:
            print(f"      🚨 [TwoPhaseBP] Flesh 생성 오류: {e}")
            return None

    def _validate_skeleton(self, skeleton: Dict) -> bool:
        """Skeleton 검증"""
        required = ["ep_num", "scene_skeleton", "item_movements"]
        for key in required:
            if key not in skeleton:
                print(f"      ⚠️ [TwoPhaseBP] Skeleton 필수 키 누락: {key}")
                return False

        scenes = skeleton.get("scene_skeleton", [])
        if len(scenes) < 3:
            print(f"      ⚠️ [TwoPhaseBP] 씬 수 부족: {len(scenes)}")
            return False

        return True

    def _escape_braces(self, text: str) -> str:
        """중괄호 이스케이프"""
        if not isinstance(text, str):
            return str(text)
        return text.replace("{", "{{").replace("}", "}}")

    def get_summary(self, skeleton: Dict) -> str:
        """Skeleton 요약"""
        if not skeleton:
            return "[TwoPhaseBP] Skeleton 없음"

        scenes = skeleton.get("scene_skeleton", [])
        items = skeleton.get("item_movements", {})

        return (
            f"[V54.4.1 Two-Phase Blueprint]\n"
            f"  씬 수: {len(scenes)}\n"
            f"  획득: {items.get('acquired', [])}\n"
            f"  소모: {items.get('consumed', [])}\n"
            f"  클리프행어: {skeleton.get('cliffhanger_type', '?')}"
        )


def create_blueprint_generator(client, model: str = "gemini-2.5-flash") -> TwoPhaseBlueprintGenerator:
    """TwoPhaseBlueprintGenerator 인스턴스 생성 헬퍼"""
    return TwoPhaseBlueprintGenerator(client, model)


# ═══════════════════════════════════════════════════════════════════════════════
# [V55.1] Two-Phase Arc Generator - Stage 2 전용
# ═══════════════════════════════════════════════════════════════════════════════

ARC_SKELETON_PROMPT = """[V57 Two-Phase Arc Generator: Phase 1 - Skeleton]

당신은 Arc 구조 설계 전문가입니다.

=== 입력 정보 ===
Arc 번호: {arc_no}
Volume 전략: {vol_strategy}
현재 블록 DNA: {curr_block}
이전 Arc 맥락: {prev_arc_context}
제약 조건: {constraints}

##############################################################
# 🔒 [V60.18] 주인공 정보 - 반드시 이 이름을 사용!
##############################################################
주인공 이름: {protagonist_name}
→ 모든 화에서 반드시 '{protagonist_name}'을 사용하세요!
→ 다른 이름(이현, 강민수 등)은 절대 사용 금지!
##############################################################

=== Phase 1 목표 ===
Arc의 **구조적 뼈대(Skeleton)**만 설계합니다.

1. **회차별 구조**: 각 화의 핵심 사건 한 줄씩
2. **아이템 타임라인**: 획득/사용/소모 시점 명시
3. **수여물 타임라인**: 수여 시점과 효과 명시
4. **상태 변화 타임라인**: 부상/회복/경지 변화 시점

=== [V57 CRITICAL] 타임라인 검증 체크리스트 ===
아래 체크리스트를 반드시 확인하고 Skeleton을 설계하세요:

□ **아이템 획득 시점 검증**
  - 이전 Arc에서 이미 획득한 아이템을 다시 획득하지 않는가?
  - 획득 방법이 논리적인가? (전투 승리, 발견, 수여 등)
  - 획득 후 소지품 목록이 일관성 있는가?

□ **아이템 소모 시점 검증**
  - 소모하는 아이템을 먼저 획득했는가? (획득화수 < 소모화수)
  - 이미 소모한 아이템을 다시 사용하지 않는가?
  - 소모 사유가 명확한가?

□ **수여물 시점 검증**
  - 수여자가 수여 시점에 해당 위치에 존재하는가?
  - 수여 후 주인공의 위상 변화가 일관성 있는가?
  - 같은 수여물을 중복 수여하지 않는가?

□ **상태 변화 연속성 검증**
  - 부상이 회복 없이 사라지지 않는가?
  - 경지 상승에 충분한 복선/수련이 있는가?
  - 상태 변화 시점이 논리적인가?

□ **이전 Arc 계승 검증**
  - 이전 Arc 종료 상태(위치, 소지품, 관계)를 그대로 계승하는가?
  - 이전 Arc에서 발생한 부상/효과가 반영되는가?

=== 출력 JSON 스키마 ===
{{
    "arc_no": {arc_no},
    "episode_skeleton": [
        {{"ep": 1, "core_event": "핵심 사건 한 줄", "tension": "상승|유지|하강"}},
        {{"ep": 2, "core_event": "...", "tension": "..."}},
        ...
    ],
    "item_timeline": {{
        "acquisitions": [{{"item": "아이템명", "ep": 획득화수, "method": "획득방법"}}],
        "consumptions": [{{"item": "아이템명", "ep": 소모화수, "reason": "소모사유"}}]
    }},
    "grant_timeline": [{{"grant": "수여물명", "ep": 수여화수, "grantor": "수여자", "effect": "효과"}}],
    "state_timeline": [{{"type": "부상|회복|경지|능력", "ep": 화수, "description": "설명"}}],
    "arc_climax_ep": 클라이막스화수,
    "ending_type": "cliffhanger|resolution|transition",
    "timeline_validation": {{
        "item_check": "아이템 타임라인 자체 점검 결과",
        "grant_check": "수여물 타임라인 자체 점검 결과",
        "state_check": "상태 변화 자체 점검 결과",
        "continuity_check": "이전 Arc 계승 자체 점검 결과"
    }}
}}

중요: Phase 1은 구조만 잡습니다. 상세 전술은 Phase 2에서 작성합니다.
timeline_validation 필드에 자체 점검 결과를 반드시 포함하세요.
반드시 JSON만 출력하세요."""


ARC_FLESH_PROMPT = """[V55.1 Two-Phase Arc Generator: Phase 2 - Flesh]

Phase 1에서 확정된 Skeleton을 기반으로 상세 전술 문서를 작성합니다.

##############################################################
# 🔒 [V60.18] 주인공 정보 - 반드시 이 이름을 사용!
##############################################################
주인공 이름: {protagonist_name}
→ tactical_doc에서 반드시 '{protagonist_name}'을 사용하세요!
→ 다른 이름으로 대체 금지!
##############################################################

=== Phase 1 Skeleton ===
{skeleton}

=== 추가 컨텍스트 ===
Volume 전략: {vol_strategy}
현재 블록 DNA: {curr_block}
AssetLibrary: {assets}

=== Phase 2 목표 ===
Skeleton의 구조를 **절대 변경하지 않고** 상세화합니다.

1. **tactical_doc**: 5화 전체 상세 전술 (회차별 장면 구성)
2. **joint_docs**: 마지막 화 종료 시점 상태
3. **state_constraints**: 획득/소모 아이템 목록

=== 출력 JSON 스키마 ===
{{
    "arc_no": {arc_no},
    "tactical_doc": "상세 전술 문서 (각 화별 장면 구성 포함)",
    "joint_docs": {{
        "final_location": "Arc 마지막 위치",
        "physical_inventory": ["소지 아이템 목록"],
        "world_joint": "세계관 변화 요약"
    }},
    "state_constraints": {{
        "items_acquired": ["획득 아이템"],
        "items_consumed": ["소모 아이템"],
        "grants_received": ["받은 수여물"],
        "injuries": ["부상 상태"],
        "level_changes": ["경지 변화"]
    }},
    "hybrid_composition": {{
        "primary": "주 서사 패턴",
        "secondary": "부 서사 패턴"
    }}
}}

중요: Skeleton의 episode_skeleton, item_timeline, grant_timeline을 그대로 반영해야 합니다.
반드시 JSON만 출력하세요."""


class TwoPhaseArcGenerator:
    """
    [V60.10] Two-Phase Arc Generator - Stage 2 전용 (Enhanced)

    Phase 1: 구조적 Skeleton 설계 (낮은 온도) - 회차/아이템/수여물 타임라인 확정
    Phase 2: 상세 Flesh 작성 (중간 온도) - tactical_doc, joint_docs 작성

    V60.10 Enhancement:
    - StateExtractor 통합으로 이전 Arc 상태 정밀 주입
    - flash 모델 사용으로 속도 향상
    - 실패 시 자동 검증 피드백 제공

    장점:
    - Phase 1에서 타임라인 확정 → 연속성 오류 방지
    - Phase 2에서 상세화 → 품질 향상
    - 실패 시 Phase 1만 재시도 가능 → 비용 절감
    """

    def __init__(self, client, model: str = "gemini-3-pro-preview", state_extractor=None):
        """
        [V60.24] Gemini 3로 변경
        Args:
            client: Gemini API 클라이언트
            model: 사용할 모델 (V60.24: Gemini 3)
            state_extractor: [V60.10] StateExtractor 인스턴스 (선택)
        """
        self.client = client
        self.model = model
        self.state_extractor = state_extractor
        self.enabled = True
        self.validation_failures = []  # [V60.10] 검증 실패 이력

    def generate(
        self,
        arc_no: int,
        vol_strategy: str,
        curr_block: Dict[str, Any],
        prev_arc_context: str,
        assets: Dict[str, Any] = None,
        constraints: str = "",
        prev_arcs: list = None,  # [V60.10] 이전 Arc 리스트 (StateExtractor용)
        protagonist_name: str = "주인공"  # [V60.18] 주인공 이름 (필수!)
    ) -> Optional[Dict[str, Any]]:
        """
        Two-Phase Arc 생성

        Args:
            arc_no: Arc 번호
            vol_strategy: Volume 전략 문서
            curr_block: 현재 블록 DNA
            prev_arc_context: 이전 Arc 맥락
            assets: AssetLibrary
            constraints: 제약 조건
            prev_arcs: [V60.10] 이전 Arc 리스트 (StateExtractor 통합용)
            protagonist_name: [V60.18] 주인공 이름 (환각 방지)

        Returns:
            생성된 Arc 설계 또는 None
        """
        if not self.enabled:
            return None

        # [V60.10] StateExtractor가 있고 prev_arcs가 있으면 정밀 맥락 생성
        if self.state_extractor and prev_arcs:
            try:
                cumulative_state = self.state_extractor.extract_cumulative_state(prev_arcs)
                state_constraint_prompt = self.state_extractor.generate_constraint_prompt(cumulative_state)
                # 기존 constraints에 추가
                constraints = state_constraint_prompt + "\n\n" + (constraints or "")
                print(f"      🧠 [V60.10] StateExtractor 제약 주입 완료 ({len(prev_arcs)}개 Arc 분석)")
            except Exception as se_err:
                print(f"      ⚠️ [V60.10] StateExtractor 실패, 기존 맥락 사용: {str(se_err)[:50]}")

        print(f"      🏗️ [TwoPhaseArc] Phase 1: Skeleton 설계 시작 (Arc {arc_no}, 주인공: {protagonist_name})")

        # Phase 1: Skeleton 설계
        skeleton = self._generate_skeleton(
            arc_no=arc_no,
            vol_strategy=vol_strategy,
            curr_block=curr_block,
            prev_arc_context=prev_arc_context,
            constraints=constraints,
            protagonist_name=protagonist_name  # [V60.18]
        )

        if not skeleton:
            print(f"      🚨 [TwoPhaseArc] Phase 1 실패")
            return None

        # Skeleton 검증
        if not self._validate_skeleton(skeleton):
            print(f"      🚨 [TwoPhaseArc] Skeleton 검증 실패")
            return None

        print(f"      ✅ [TwoPhaseArc] Phase 1 완료 ({len(skeleton.get('episode_skeleton', []))}화 구조)")
        print(f"      🏗️ [TwoPhaseArc] Phase 2: Flesh 작성 시작")

        # Phase 2: Flesh 작성
        arc_design = self._generate_flesh(
            skeleton=skeleton,
            arc_no=arc_no,
            vol_strategy=vol_strategy,
            curr_block=curr_block,
            assets=assets,
            protagonist_name=protagonist_name  # [V60.18]
        )

        if not arc_design:
            print(f"      🚨 [TwoPhaseArc] Phase 2 실패")
            return None

        # [V57] Skeleton-Flesh 일치 검증
        flesh_validation = self._validate_flesh_against_skeleton(arc_design, skeleton)
        if not flesh_validation["valid"]:
            print(f"      🚨 [TwoPhaseArc] {flesh_validation['reason']}")
            for warn in flesh_validation.get("warnings", []):
                print(f"         ⚠️ {warn}")
            return None

        # 경고가 있으면 출력 (PASS는 됨)
        if flesh_validation.get("warnings"):
            print(f"      ⚠️ [TwoPhaseArc] Skeleton-Flesh 경고 {len(flesh_validation['warnings'])}건:")
            for warn in flesh_validation["warnings"]:
                print(f"         {warn}")

        # Skeleton 정보 병합 (검증용)
        arc_design['_skeleton'] = skeleton

        print(f"      ✅ [TwoPhaseArc] Two-Phase Arc 생성 완료")
        return arc_design

    def _generate_skeleton(
        self,
        arc_no: int,
        vol_strategy: str,
        curr_block: Dict[str, Any],
        prev_arc_context: str,
        constraints: str,
        protagonist_name: str = "주인공"  # [V60.18]
    ) -> Optional[Dict]:
        """Phase 1: Skeleton 생성"""
        try:
            prompt = ARC_SKELETON_PROMPT.format(
                arc_no=arc_no,
                vol_strategy=self._escape_braces(vol_strategy[:3000] if vol_strategy else "(없음)"),
                curr_block=self._escape_braces(json.dumps(curr_block, ensure_ascii=False) if curr_block else "(없음)"),
                prev_arc_context=self._escape_braces(prev_arc_context[:4000] if prev_arc_context else "(첫 Arc)"),
                constraints=self._escape_braces(constraints or "(없음)"),
                protagonist_name=protagonist_name  # [V60.18]
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": 0.3,  # 낮은 온도 → 구조적 정확성
                    "max_output_tokens": 4096,
                    "response_mime_type": "application/json"
                }
            )

            # JSON 파싱
            import re
            text = response.text
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(text)

        except Exception as e:
            print(f"      🚨 [TwoPhaseArc] Skeleton 생성 오류: {e}")
            return None

    def _generate_flesh(
        self,
        skeleton: Dict,
        arc_no: int,
        vol_strategy: str,
        curr_block: Dict[str, Any],
        assets: Dict[str, Any],
        protagonist_name: str = "주인공"  # [V60.18]
    ) -> Optional[Dict]:
        """Phase 2: Flesh 생성"""
        try:
            prompt = ARC_FLESH_PROMPT.format(
                skeleton=self._escape_braces(json.dumps(skeleton, ensure_ascii=False, indent=2)),
                arc_no=arc_no,
                vol_strategy=self._escape_braces(vol_strategy[:2000] if vol_strategy else "(없음)"),
                curr_block=self._escape_braces(json.dumps(curr_block, ensure_ascii=False) if curr_block else "(없음)"),
                assets=self._escape_braces(json.dumps(assets, ensure_ascii=False)[:2000] if assets else "(없음)"),
                protagonist_name=protagonist_name  # [V60.18]
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": 0.5,  # 중간 온도 → 창의성 허용
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json"
                }
            )

            # JSON 파싱
            import re
            text = response.text
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(text)

        except Exception as e:
            print(f"      🚨 [TwoPhaseArc] Flesh 생성 오류: {e}")
            return None

    def _validate_skeleton(self, skeleton: Dict) -> bool:
        """Skeleton 검증"""
        required = ["arc_no", "episode_skeleton", "item_timeline"]
        for key in required:
            if key not in skeleton:
                print(f"      ⚠️ [TwoPhaseArc] Skeleton 필수 키 누락: {key}")
                return False

        episodes = skeleton.get("episode_skeleton", [])
        if len(episodes) < 3:
            print(f"      ⚠️ [TwoPhaseArc] 에피소드 수 부족: {len(episodes)}")
            return False

        return True

    def _validate_flesh_against_skeleton(self, flesh: Dict, skeleton: Dict) -> Dict[str, Any]:
        """
        [V57] Phase 2 Flesh가 Phase 1 Skeleton 구조를 준수하는지 검증

        검증 항목:
        1. Item Timeline 일치: Skeleton의 아이템 획득/소모가 Flesh에 반영되었는지
        2. Grant Timeline 일치: 수여물 시점이 Flesh에 반영되었는지
        3. Episode Count 일치: 화수가 일치하는지
        4. State Timeline 일치: 상태 변화가 Flesh에 반영되었는지

        Returns:
            {"valid": bool, "reason": str, "warnings": list}
        """
        result = {"valid": True, "reason": "", "warnings": []}

        # 1. Episode Count 검증
        skeleton_ep_count = len(skeleton.get("episode_skeleton", []))
        tactical_doc = flesh.get("tactical_doc", "")

        # tactical_doc에서 화수 추출 (제 N화 패턴)
        import re
        ep_mentions = re.findall(r'제\s*(\d+)\s*화', tactical_doc)
        if ep_mentions:
            flesh_ep_count = len(set(ep_mentions))
            if flesh_ep_count < skeleton_ep_count:
                result["warnings"].append(
                    f"[V57] Episode Count 불일치: Skeleton {skeleton_ep_count}화 vs Flesh {flesh_ep_count}화"
                )

        # 2. Item Timeline 검증
        skeleton_items = skeleton.get("item_timeline", {})
        skeleton_acquisitions = [a.get("item", "").strip() for a in skeleton_items.get("acquisitions", [])]
        skeleton_consumptions = [c.get("item", "").strip() for c in skeleton_items.get("consumptions", [])]

        flesh_state = flesh.get("state_constraints", {})
        flesh_acquired = flesh_state.get("items_acquired", [])
        flesh_consumed = flesh_state.get("items_consumed", [])

        # 획득 아이템 누락 검증
        for item in skeleton_acquisitions:
            if item and not self._item_exists_in_list(item, flesh_acquired) and item not in tactical_doc:
                result["warnings"].append(
                    f"[V57] Skeleton 획득 아이템 '{item}'이 Flesh에 누락됨"
                )

        # 소모 아이템 누락 검증
        for item in skeleton_consumptions:
            if item and not self._item_exists_in_list(item, flesh_consumed) and item not in tactical_doc:
                result["warnings"].append(
                    f"[V57] Skeleton 소모 아이템 '{item}'이 Flesh에 누락됨"
                )

        # 3. Grant Timeline 검증
        skeleton_grants = skeleton.get("grant_timeline", [])
        flesh_grants = flesh_state.get("grants_received", [])

        for grant in skeleton_grants:
            grant_name = grant.get("grant", "").strip()
            if grant_name and not self._item_exists_in_list(grant_name, flesh_grants) and grant_name not in tactical_doc:
                result["warnings"].append(
                    f"[V57] Skeleton 수여물 '{grant_name}'이 Flesh에 누락됨"
                )

        # 4. State Timeline 검증 (부상/경지 변화)
        skeleton_states = skeleton.get("state_timeline", [])
        flesh_injuries = flesh_state.get("injuries", [])
        flesh_levels = flesh_state.get("level_changes", [])

        for state in skeleton_states:
            state_type = state.get("type", "")
            state_desc = state.get("description", "")

            if state_type == "부상":
                if state_desc and not any(state_desc in inj for inj in flesh_injuries) and state_desc not in tactical_doc:
                    result["warnings"].append(
                        f"[V57] Skeleton 부상 '{state_desc}'이 Flesh에 누락됨"
                    )
            elif state_type == "경지":
                if state_desc and not any(state_desc in lv for lv in flesh_levels) and state_desc not in tactical_doc:
                    result["warnings"].append(
                        f"[V57] Skeleton 경지 변화 '{state_desc}'이 Flesh에 누락됨"
                    )

        # 5. Critical 판정: 3개 이상 불일치 시 REJECT
        if len(result["warnings"]) >= 3:
            result["valid"] = False
            result["reason"] = f"[V57] Skeleton-Flesh 불일치 {len(result['warnings'])}건 (3건 이상 → REJECT)"

        return result

    def _item_exists_in_list(self, item: str, item_list: list) -> bool:
        """아이템이 리스트에 존재하는지 확인 (부분 매칭 포함)"""
        if not item or not item_list:
            return False
        item_lower = item.lower().strip()
        for list_item in item_list:
            if isinstance(list_item, str):
                if item_lower in list_item.lower() or list_item.lower() in item_lower:
                    return True
        return False

    def _escape_braces(self, text: str) -> str:
        """중괄호 이스케이프"""
        if not isinstance(text, str):
            return str(text)
        return text.replace("{", "{{").replace("}", "}}")

    def get_summary(self, skeleton: Dict) -> str:
        """Skeleton 요약"""
        if not skeleton:
            return "[TwoPhaseArc] Skeleton 없음"

        episodes = skeleton.get("episode_skeleton", [])
        item_timeline = skeleton.get("item_timeline", {})
        grants = skeleton.get("grant_timeline", [])

        return (
            f"[V55.1 Two-Phase Arc]\n"
            f"  에피소드 수: {len(episodes)}\n"
            f"  획득 아이템: {len(item_timeline.get('acquisitions', []))}\n"
            f"  소모 아이템: {len(item_timeline.get('consumptions', []))}\n"
            f"  수여물: {len(grants)}\n"
            f"  클라이막스: EP{skeleton.get('arc_climax_ep', '?')}"
        )


def create_arc_generator(client, model: str = "gemini-3-pro-preview", state_extractor=None) -> TwoPhaseArcGenerator:
    """[V60.24] TwoPhaseArcGenerator 인스턴스 생성 헬퍼 - Gemini 3 사용

    Args:
        client: Gemini API 클라이언트
        model: 사용할 모델 (V60.24: Gemini 3)
        state_extractor: [V60.10] StateExtractor 인스턴스
    """
    return TwoPhaseArcGenerator(client, model, state_extractor)
