"""
V60.10 State Extractor Agent
이전 Arc/Episode에서 핵심 상태 정보를 구조화하여 추출

Purpose:
- LLM이 무시하기 쉬운 문자열 컨텍스트를 구조화된 JSON으로 변환
- 다음 Arc 설계 시 명확한 제약으로 주입
- Flash 모델로 빠르고 저렴하게 실행
"""

import json
from typing import Optional, List, Dict, Any
from .base_agent import BaseAgent


STATE_EXTRACTION_PROMPT = """
[Role] 서사 상태 추출 전문가 (State Extraction Specialist)
[Task] 아래 Arc 데이터에서 다음 Arc 설계에 필요한 핵심 상태 정보를 추출하라.

### [🚨 SYSTEM RESTRICTION: JSON ONLY]
1. 답변의 첫 글자는 반드시 {{, 마지막 글자는 반드시 }}
2. 설명, 인사말, 서문 절대 금지
3. 오직 유효한 JSON만 출력

### [Arc 데이터]
{arc_data}

### [추출 대상]
1. **부상 상태 (injuries)**
   - 현재 부상 목록과 심각도
   - 필요한 회복 기간 (일 단위)
   - 회복 조건 (운기조식, 치료 등)

2. **내공 상태 (internal_energy)**
   - 현재 내공 퍼센트
   - 소모된 내공
   - 회복에 필요한 시간

3. **소지품 (inventory)**
   - 현재 소지 중인 아이템 전체 목록
   - 이번 Arc에서 새로 획득한 아이템
   - 소모/파손된 아이템

4. **위치 (location)**
   - 현재 위치
   - 이동 경로 (있다면)

5. **신분/권한 (status)**
   - 획득한 패/직위/권한
   - 변화된 사회적 위상

6. **관계 변화 (relationships)**
   - 호감도 상승한 NPC
   - 적대 관계가 된 NPC
   - 사망/퇴장한 NPC

7. **절대 금지 목록 (forbidden)**
   - 이미 획득했으므로 다시 획득 불가한 아이템
   - 이미 해결했으므로 다시 등장 불가한 문제
   - 이미 수여받았으므로 다시 받을 수 없는 권한

### [Output Format - JSON Only]
{{
    "arc_no": {arc_no},
    "protagonist_state": {{
        "injuries": [
            {{"name": "부상명", "severity": "심각도", "recovery_days": 숫자, "recovery_method": "회복방법"}}
        ],
        "internal_energy": {{
            "current_percent": 숫자,
            "consumed_this_arc": 숫자,
            "recovery_needed_days": 숫자
        }},
        "location": {{
            "current": "현재 위치",
            "can_move_immediately": true/false,
            "movement_constraint": "이동 제약 사유"
        }}
    }},
    "inventory": {{
        "current_items": ["소지품 목록"],
        "acquired_this_arc": ["이번 Arc 획득 아이템"],
        "consumed_or_lost": ["소모/분실 아이템"]
    }},
    "status": {{
        "titles": ["직위/칭호"],
        "authorities": ["권한"],
        "social_standing": "사회적 위상 설명"
    }},
    "relationships": {{
        "improved": ["호감 상승 NPC"],
        "worsened": ["관계 악화 NPC"],
        "deceased": ["사망 NPC"]
    }},
    "forbidden_in_next_arc": {{
        "cannot_acquire_again": ["다시 획득 불가 아이템"],
        "cannot_receive_again": ["다시 수여받을 수 없는 것"],
        "resolved_problems": ["해결된 문제"]
    }},
    "next_arc_constraints": {{
        "must_start_with": "다음 Arc 도입부 필수 요소",
        "recovery_scene_required": true/false,
        "min_time_skip_days": 숫자,
        "mandatory_items_in_possession": ["반드시 소지해야 할 아이템"]
    }}
}}
"""


class StateExtractor(BaseAgent):
    """
    V60.10 상태 추출 에이전트

    이전 Arc의 종료 상태를 구조화된 JSON으로 추출하여
    다음 Arc 설계 시 명확한 제약으로 활용
    """

    def __init__(self, context, client, model_tier: str = "gemini-3-flash-preview"):
        """
        [V60.24] StateExtractor 초기화 - Gemini 3 Flash (추출용)

        Args:
            context: ProjectContext
            client: genai.Client
            model_tier: 사용할 모델 (V60.24: Flash로 변경 - 추출 작업)
        """
        super().__init__(context, client, model_tier)
        self.backup_model = "gemini-3-pro-preview"  # 실패 시 Pro 폴백

    def extract_state(self, arc_data: dict) -> dict:
        """
        단일 Arc에서 상태 추출

        Args:
            arc_data: Arc 데이터 (tactical_doc, joint_docs, status_shadow 포함)

        Returns:
            구조화된 상태 정보 dict
        """
        arc_no = arc_data.get('arc_no', 'Unknown')

        # Arc 데이터 정리
        # [V60.13 FIX] state_constraints.arc_end_state 포함
        cleaned_data = {
            'arc_no': arc_no,
            'tactical_doc': arc_data.get('tactical_doc', '')[:3000],  # 토큰 절약
            'joint_docs': arc_data.get('joint_docs', {}),
            'status_shadow': arc_data.get('status_shadow', {}),
            'state_constraints': arc_data.get('state_constraints', {}),  # [V60.13] arc_end_state 포함
            'beat_sequence': arc_data.get('beat_sequence', [])
        }

        prompt = STATE_EXTRACTION_PROMPT.format(
            arc_data=json.dumps(cleaned_data, ensure_ascii=False, indent=2),
            arc_no=arc_no
        )

        try:
            result = self.ask(prompt, temperature=0.2)

            if isinstance(result, str):
                result = json.loads(result)

            # 필수 필드 검증
            result = self._validate_and_fix_result(result, arc_data)

            return result

        except Exception as e:
            # 실패 시 기본 추출 (Python 기반)
            return self._fallback_extraction(arc_data)

    def extract_cumulative_state(self, arcs: List[dict]) -> dict:
        """
        여러 Arc의 누적 상태 추출

        Args:
            arcs: Arc 데이터 리스트 (시간순)

        Returns:
            누적된 상태 정보
        """
        if not arcs:
            return self._empty_state()

        # 마지막 Arc 기준으로 추출
        latest_arc = arcs[-1]
        current_state = self.extract_state(latest_arc)

        # 전체 Arc에서 획득한 아이템 누적
        all_acquired = []
        all_grants = []
        all_deceased = []

        for arc in arcs:
            joint = arc.get('joint_docs', {})
            inventory = joint.get('physical_inventory', '')

            # 아이템 추출
            if isinstance(inventory, str):
                items = [i.strip() for i in inventory.split(',') if i.strip()]
                all_acquired.extend(items)
            elif isinstance(inventory, list):
                all_acquired.extend(inventory)

            # 수여물 추출
            tactical = arc.get('tactical_doc', '')
            grants = self._extract_grants_from_text(tactical)
            all_grants.extend(grants)

            # 사망 NPC 추출
            if 'deceased' in str(tactical).lower() or '사망' in tactical:
                # 간단한 추출 로직
                pass

        # 중복 제거
        current_state['cumulative'] = {
            'all_acquired_items': list(set(all_acquired)),
            'all_grants_received': list(set(all_grants)),
            'total_arcs_completed': len(arcs)
        }

        return current_state

    def generate_constraint_prompt(self, state: dict) -> str:
        """
        추출된 상태를 Analyst 프롬프트용 제약 텍스트로 변환

        Args:
            state: extract_state() 결과

        Returns:
            프롬프트에 주입할 제약 텍스트
        """
        protagonist = state.get('protagonist_state', {})
        inventory = state.get('inventory', {})
        forbidden = state.get('forbidden_in_next_arc', {})
        constraints = state.get('next_arc_constraints', {})

        lines = [
            "=" * 60,
            "🚨🚨🚨 [V60.10 STATE LOCK - 위반 시 즉시 REJECT] 🚨🚨🚨",
            "=" * 60,
            "",
            "### 1. 부상/내공 상태 (RECOVERY REQUIRED)",
        ]

        injuries = protagonist.get('injuries', [])
        if injuries:
            for inj in injuries:
                lines.append(f"   - {inj.get('name', '?')}: {inj.get('severity', '?')} "
                           f"(회복 {inj.get('recovery_days', '?')}일 필요)")
        else:
            lines.append("   - 없음")

        energy = protagonist.get('internal_energy', {})
        lines.append(f"   - 내공: {energy.get('current_percent', 100)}% "
                    f"(회복 {energy.get('recovery_needed_days', 0)}일 필요)")

        lines.append("")
        lines.append("### 2. 현재 소지품 (MUST HAVE)")
        current_items = inventory.get('current_items', [])
        if current_items:
            for item in current_items:
                lines.append(f"   - {item}")
        else:
            lines.append("   - 없음")

        lines.append("")
        lines.append("### 3. 절대 금지 (CANNOT DO)")
        cannot_acquire = forbidden.get('cannot_acquire_again', [])
        if cannot_acquire:
            lines.append("   [다시 획득 불가]")
            for item in cannot_acquire:
                lines.append(f"   ❌ {item}")

        cannot_receive = forbidden.get('cannot_receive_again', [])
        if cannot_receive:
            lines.append("   [다시 수여받기 불가]")
            for item in cannot_receive:
                lines.append(f"   ❌ {item}")

        lines.append("")
        lines.append("### 4. 다음 Arc 필수 사항")
        if constraints.get('recovery_scene_required'):
            lines.append(f"   ✅ 회복 장면 필수 (최소 {constraints.get('min_time_skip_days', 1)}일)")
        if constraints.get('must_start_with'):
            lines.append(f"   ✅ 도입부: {constraints.get('must_start_with')}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _validate_and_fix_result(self, result: dict, original_arc: dict) -> dict:
        """결과 검증 및 보정"""

        # protagonist_state 보정
        if 'protagonist_state' not in result:
            result['protagonist_state'] = {}

        ps = result['protagonist_state']
        if 'injuries' not in ps:
            ps['injuries'] = []
        if 'internal_energy' not in ps:
            ps['internal_energy'] = {'current_percent': 100, 'consumed_this_arc': 0}
        if 'location' not in ps:
            joint = original_arc.get('joint_docs', {})
            ps['location'] = {
                'current': joint.get('final_location', '알 수 없음'),
                'can_move_immediately': True
            }

        # inventory 보정
        if 'inventory' not in result:
            result['inventory'] = {}

        inv = result['inventory']
        if 'current_items' not in inv:
            joint = original_arc.get('joint_docs', {})
            raw_inv = joint.get('physical_inventory', '')
            if isinstance(raw_inv, str):
                inv['current_items'] = [i.strip() for i in raw_inv.split(',') if i.strip()]
            elif isinstance(raw_inv, list):
                inv['current_items'] = raw_inv
            else:
                inv['current_items'] = []

        # forbidden 보정
        if 'forbidden_in_next_arc' not in result:
            result['forbidden_in_next_arc'] = {
                'cannot_acquire_again': inv.get('current_items', []),
                'cannot_receive_again': [],
                'resolved_problems': []
            }

        # next_arc_constraints 보정
        if 'next_arc_constraints' not in result:
            injuries = ps.get('injuries', [])
            energy = ps.get('internal_energy', {})

            recovery_needed = bool(injuries) or energy.get('current_percent', 100) < 50
            min_days = max([inj.get('recovery_days', 0) for inj in injuries] + [0])

            result['next_arc_constraints'] = {
                'must_start_with': '이전 상태 계승' if recovery_needed else None,
                'recovery_scene_required': recovery_needed,
                'min_time_skip_days': min_days,
                'mandatory_items_in_possession': inv.get('current_items', [])
            }

        return result

    def _fallback_extraction(self, arc_data: dict) -> dict:
        """LLM 실패 시 Python 기반 추출"""

        joint = arc_data.get('joint_docs', {})
        shadow = arc_data.get('status_shadow', {})
        # [V60.13 FIX] arc_end_state 우선 사용
        state_constraints = arc_data.get('state_constraints', {})
        arc_end_state = state_constraints.get('arc_end_state', {})

        # 소지품 추출
        raw_inv = joint.get('physical_inventory', '')
        if isinstance(raw_inv, str):
            current_items = [i.strip() for i in raw_inv.split(',') if i.strip()]
        elif isinstance(raw_inv, list):
            current_items = raw_inv
        else:
            current_items = []

        # 부상 추출 - arc_end_state 우선
        injuries_raw = arc_end_state.get('injuries') or shadow.get('expected_injuries', '')
        injuries = []
        if injuries_raw and injuries_raw != '없음':
            injuries.append({
                'name': injuries_raw[:50],
                'severity': 'unknown',
                'recovery_days': 3,
                'recovery_method': '운기조식'
            })

        # 내공 추출 - arc_end_state 우선
        if arc_end_state.get('internal_energy') is not None:
            current_energy = arc_end_state['internal_energy']
            loss_percent = 100 - current_energy
        else:
            energy_loss = shadow.get('internal_energy_loss', '0%')
            try:
                loss_percent = int(str(energy_loss).replace('%', '').strip())
                current_energy = 100 - loss_percent
            except:
                loss_percent = 0
                current_energy = 100

        return {
            'arc_no': arc_data.get('arc_no', 'Unknown'),
            'protagonist_state': {
                'injuries': injuries,
                'internal_energy': {
                    'current_percent': current_energy,
                    'consumed_this_arc': loss_percent,
                    'recovery_needed_days': loss_percent // 10
                },
                'location': {
                    'current': joint.get('final_location', '알 수 없음'),
                    'can_move_immediately': not bool(injuries)
                }
            },
            'inventory': {
                'current_items': current_items,
                'acquired_this_arc': [],
                'consumed_or_lost': shadow.get('item_consumption', [])
            },
            'forbidden_in_next_arc': {
                'cannot_acquire_again': current_items,
                'cannot_receive_again': [],
                'resolved_problems': []
            },
            'next_arc_constraints': {
                'recovery_scene_required': bool(injuries) or loss_percent > 30,
                'min_time_skip_days': max([i.get('recovery_days', 0) for i in injuries] + [0]),
                'mandatory_items_in_possession': current_items
            }
        }

    def _empty_state(self) -> dict:
        """빈 상태 반환"""
        return {
            'arc_no': 0,
            'protagonist_state': {
                'injuries': [],
                'internal_energy': {'current_percent': 100, 'consumed_this_arc': 0},
                'location': {'current': '시작점', 'can_move_immediately': True}
            },
            'inventory': {
                'current_items': [],
                'acquired_this_arc': [],
                'consumed_or_lost': []
            },
            'forbidden_in_next_arc': {
                'cannot_acquire_again': [],
                'cannot_receive_again': [],
                'resolved_problems': []
            },
            'next_arc_constraints': {
                'recovery_scene_required': False,
                'min_time_skip_days': 0,
                'mandatory_items_in_possession': []
            }
        }

    def _extract_grants_from_text(self, text: str) -> List[str]:
        """텍스트에서 수여물 추출"""
        import re
        grants = []

        patterns = [
            r'([가-힣]+패)[를을]?\s*(?:하사|수여|받|얻)',
            r'([가-힣]+권)[를을]?\s*(?:위임|부여|받|얻)',
            r'([가-힣]+직|[가-힣]+장)[에으로]?\s*(?:임명|취임)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            grants.extend(matches)

        return list(set(grants))
