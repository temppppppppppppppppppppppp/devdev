"""
[V49] Continuity Inspector - Director 산하 연속성 검증 전문 에이전트

역할:
1. 이전 블루프린트/Arc 전체 분석
2. 아이템/패 획득 타임라인 추적
3. 캐릭터 상태 흐름 검증
4. 모순 감지 시 구체적 수정 지시 제공

실행 시점:
- [V49 NEW] Stage 2에서 Analyst가 Arc 설계 후 - Arc 간 연속성 + 단일 Arc 내 모순 검증
- Stage 3에서 Architect가 블루프린트 생성 후 - 에피소드 연속성 검증
- Director 검증 전에 실행
- REJECT 시 재생성 (모순 지점 피드백 포함)

비용: ~$0.01/에피소드 (flash 모델 사용)
"""

import json
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from .base_agent import BaseAgent


CONTINUITY_INSPECTION_PROMPT = """
[Role] 연속성 검증 전문가 (Continuity Inspector) - 전체 타임라인 분석
[Task] 현재 블루프린트가 제1화부터 지금까지의 전체 서사와 논리적으로 연결되는지 정밀 검증

### 📋 검증 대상
- 현재 에피소드: 제 {current_ep}화
- 현재 블루프린트 시나리오:
{current_scenario}

### 📜 전체 에피소드 타임라인 (제1화 ~ 제{prev_count}화)
{prev_summaries}

### 🎯 핵심 검증 항목 (전체 타임라인 기준)

#### 1. 아이템/무기 타임라인 검증 (전체 에피소드 추적)
- 제1화부터 현재까지 획득한 모든 아이템 목록을 추적하라
- 이미 획득한 아이템을 다시 획득하려 하는가?
- 아직 획득하지 않은 아이템을 소지하고 있는가?
- 무기/장비 소지 상태가 연속적인가?

#### 2. 수여물/신물 타임라인 검증 (전체 에피소드 추적)
- 공식 수여물(패, 권한, 직위 등)의 정확한 수여 시점을 추적하라
- 수여 시점 이전 에피소드에서 소지/사용 묘사가 있으면 CRITICAL 위반
- 수여 시점 이후 에피소드에서는 소지 상태로 시작해야 함

#### 3. 캐릭터 상태 연속성 (전체 서사 흐름)
- 부상 상태가 급격히 회복되지 않았는가?
- 내공/경지가 급격히 변화하지 않았는가?
- 이전 에피소드에서 발생한 상태 변화가 누적되고 있는가?

#### 4. 인물 반응 개연성 (전체 관계 변화 추적)
- 특정 에피소드에서 인정받거나 위상이 변화했다면, 이후 반응이 일관적인가?
- 정보 전파 시간(몇 시진, 하루 등)을 고려해도 모순인가?
- 관계 역행(경외→멸시)이 발생하면 WARNING

### 🚨 판정 기준
- CRITICAL: 명백한 타임라인 오류 (획득 전 소지, 수여 전 보유) → 즉시 REJECT
- MAJOR: 심각한 연속성 오류 (무기 리셋, 상태 급변) → REJECT
- MINOR: 경미한 불일치 (반응 개연성) → WARNING으로 PASS 가능
- NONE: 연속성 문제 없음 → PASS

### [Chain-of-Thought Analysis]
다음 순서로 분석하십시오:

Step 1: 아이템/무기 추적
- 이전 에피소드들에서 획득한 아이템 목록 작성
- 현재 블루프린트에서 획득하려는 아이템 확인
- 중복 획득 여부 판정

Step 2: 수여물 타임라인 분석
- 이전 에피소드들에서 공식 수여된 것들 목록
- 현재 블루프린트에서 소지/사용하는 수여물 확인
- 타임라인 모순 여부 판정

Step 3: 상태 연속성 분석
- 직전 에피소드 종료 시점의 상태 확인
- 현재 블루프린트 시작 시점의 상태 확인
- 급격한 변화 여부 판정

Step 4: 반응 개연성 분석
- 이전 사건들로 인한 관계/평판 변화 확인
- 현재 블루프린트의 NPC 반응 확인
- 불일치 여부 판정

Step 5: 최종 판정
- 위 4단계를 종합하여 PASS/REJECT 결정
- 위반 사항 목록 작성
- 수정 지시 작성

[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "REJECT",
    "severity": "NONE" 또는 "MINOR" 또는 "MAJOR" 또는 "CRITICAL",
    "timeline_analysis": {{
        "items_acquired_before": ["이전에 획득한 아이템 목록"],
        "items_acquired_now": ["현재 획득하려는 아이템 목록"],
        "grants_received_before": ["이전에 수여받은 것들"],
        "grants_used_now": ["현재 사용/소지하는 수여물"]
    }},
    "violations": [
        {{
            "type": "duplicate_acquisition | premature_possession | state_discontinuity | reaction_mismatch",
            "severity": "CRITICAL | MAJOR | MINOR",
            "item_or_subject": "문제 대상",
            "prev_ep": "이전 발생 에피소드",
            "description": "모순 설명",
            "evidence_prev": "이전 에피소드 근거 텍스트",
            "evidence_curr": "현재 블루프린트 근거 텍스트"
        }}
    ],
    "warnings": ["MINOR 수준의 경고 목록"],
    "fix_instructions": "수정 지시 (REJECT 시 필수, PASS 시 권고사항)"
}}
"""


# =================================================================
# [V49 NEW] Arc 수준 연속성 검증 프롬프트
# =================================================================
ARC_CONTINUITY_INSPECTION_PROMPT = """
[Role] Arc 수준 연속성 검증 전문가 (Arc Continuity Inspector)
[Task] 현재 Arc의 전술 설계가 이전 Arc들과 논리적으로 연결되는지, 그리고 단일 Arc 내에서 모순이 없는지 정밀 검증

### 📋 검증 대상: Arc {current_arc_no}
- 설정 화수: {ep_count}화 (제 {ep_start}화 ~ 제 {ep_end}화)
- 전술 설계서:
{tactical_doc}

- Joint Docs (Arc 종료 시점 상태):
{joint_docs}

- Status Shadow (예상 손실):
{status_shadow}

### 📜 이전 Arc 타임라인 (Arc 1 ~ Arc {prev_arc_count})
{prev_arcs_summary}

### 🎯 핵심 검증 항목

#### 1. Arc 간 아이템/무기 연속성 (Cross-Arc Item Timeline)
- 이전 Arc들에서 획득한 아이템이 현재 Arc에서 중복 획득되지 않는가?
- 이전 Arc의 joint_docs.physical_inventory에 명시된 아이템이 현재 Arc에서 연속적으로 소지되는가?
- 현재 Arc에서 새로 획득하려는 아이템이 이전에 이미 획득한 것과 동일하지 않은가?

#### 2. Arc 간 수여물/위상 연속성 (Cross-Arc Grant Timeline)
- 이전 Arc에서 수여받은 권한/패/직위가 현재 Arc에서 유지되는가?
- 이전 Arc에서 "복권"이나 "인정"을 받았다면, 현재 Arc에서 여전히 무시당하는 설정이 있는가?
- 정보 전파 시간을 고려해도 모순인 반응이 있는가?

#### 3. Arc 간 상태 연속성 (Cross-Arc State Timeline)
- 이전 Arc의 status_shadow(부상, 내공 소모)가 현재 Arc 도입부에 반영되는가?
- 부상 상태에서 갑자기 완전 회복된 것처럼 행동하지 않는가?
- 경지/무공 수준이 급격히 변화하지 않았는가?

#### 4. 단일 Arc 내 모순 (Intra-Arc Consistency) [V49 신규]
- 현재 Arc의 tactical_doc 내에서 앞뒤 화 사이에 모순이 없는가?
- 예: 제N화에서 획득한 아이템을 제N+2화에서 다시 획득하러 가는 설정
- 예: 제N화에서 부상을 입었는데 제N+1화에서 멀쩡하게 전투하는 설정
- 예: 제N화에서 설정된 무기 두께/특성이 제N+3화에서 모순되는 설정

#### 5. 설정 일관성 (Setting Consistency) [V49 신규]
- 아이템/무기의 물리적 특성(무게, 두께, 재질)이 Arc 내에서 일관되는가?
- 인물의 호칭/별호가 일관되게 사용되는가?
- 장소 이동이 물리적으로 가능한가?

### 🚨 판정 기준
- CRITICAL: 명백한 타임라인 오류 (중복 획득, 수여 전 소지) → 즉시 REJECT
- MAJOR: 심각한 연속성 오류 (상태 급변, 설정 충돌) → REJECT
- MINOR: 경미한 불일치 (반응 속도, 정보 전파) → WARNING으로 PASS 가능
- NONE: 연속성 문제 없음 → PASS

### [Chain-of-Thought Analysis]
다음 순서로 분석하십시오:

Step 1: 아이템/무기 타임라인 검증
- 이전 Arc들의 joint_docs에서 획득/소지 아이템 목록 추출
- 현재 Arc의 tactical_doc에서 획득하려는 아이템 추출
- 중복 획득 여부 판정

Step 2: 수여물/위상 타임라인 검증
- 이전 Arc들에서 수여/인정받은 것들 목록
- 현재 Arc에서의 NPC 반응이 일관적인지 확인
- 타임라인 모순 여부 판정

Step 3: 상태 연속성 검증
- 직전 Arc의 status_shadow 확인
- 현재 Arc 도입부의 상태 확인
- 급격한 변화 여부 판정

Step 4: 단일 Arc 내 모순 검증
- 현재 Arc의 각 화별 설정 추출
- 화 사이의 인과적 연결 확인
- 내부 모순 여부 판정

Step 5: 설정 일관성 검증
- 무기/아이템의 물리적 특성 일관성
- 인물 호칭/별호 일관성
- 장소 이동의 물리적 타당성

Step 6: 최종 판정
- 위 5단계를 종합하여 PASS/REJECT 결정
- 위반 사항 목록 작성
- 수정 지시 작성

[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "REJECT",
    "severity": "NONE" 또는 "MINOR" 또는 "MAJOR" 또는 "CRITICAL",
    "cross_arc_analysis": {{
        "items_acquired_before": ["이전 Arc들에서 획득한 아이템"],
        "items_in_current_arc": ["현재 Arc에서 획득/사용하려는 아이템"],
        "grants_received_before": ["이전 Arc들에서 수여받은 것들"],
        "status_from_prev_arc": "직전 Arc 종료 시 상태"
    }},
    "intra_arc_analysis": {{
        "internal_timeline": ["Arc 내 각 화별 핵심 사건"],
        "internal_contradictions": ["Arc 내부에서 발견된 모순"]
    }},
    "violations": [
        {{
            "type": "duplicate_acquisition | premature_possession | state_discontinuity | intra_arc_contradiction | setting_inconsistency",
            "severity": "CRITICAL | MAJOR | MINOR",
            "item_or_subject": "문제 대상",
            "prev_arc": "이전 발생 Arc 번호 (Arc 간 모순인 경우)",
            "prev_ep": "이전 발생 화수 (Arc 내 모순인 경우)",
            "curr_ep": "현재 문제 화수",
            "description": "모순 설명",
            "evidence_prev": "이전 근거 텍스트",
            "evidence_curr": "현재 근거 텍스트"
        }}
    ],
    "warnings": ["MINOR 수준의 경고 목록"],
    "fix_instructions": "수정 지시 (REJECT 시 필수, PASS 시 권고사항)"
}}
"""


# =================================================================
# [V49.1 NEW] Stage 4 원고 연속성 검증 프롬프트
# =================================================================
MANUSCRIPT_CONTINUITY_PROMPT = """
[Role] 원고 연속성 검증 전문가 (Manuscript Continuity Inspector)
[Task] Writer가 생성한 원고가 이전 원고들과 논리적으로 연결되고, Blueprint 설계를 준수하는지 정밀 검증

### 📋 검증 대상: 제 {current_ep}화 원고
{manuscript_excerpt}

### 📜 이전 원고 타임라인 (최근 {prev_count}화)
{prev_manuscripts_timeline}

### 📐 Blueprint 설계서 (현재 에피소드)
{blueprint_scenario}

### 🎯 핵심 검증 항목

#### 1. 아이템/무기 연속성 (이전 원고 대비)
- 이전 원고들에서 획득한 아이템만 사용하고 있는가?
- 이전 화 끝에서 소지하던 무기가 현재 화 시작에도 유지되는가?
- 획득하지 않은 아이템을 갑자기 사용하고 있지 않은가?

#### 2. 상태 연속성 (이전 원고 대비)
- 직전 화 끝의 부상/피로 상태가 현재 화에 반영되는가?
- 내공/경지가 급격히 변화하지 않았는가?
- 캐릭터의 신체적 상태가 자연스럽게 연결되는가?

#### 3. 관계 연속성 (이전 원고 대비)
- NPC와의 관계가 역행(경외→멸시, 적대→친밀)하지 않는가?
- 이전 사건으로 인한 평판 변화가 반영되는가?
- 정보 전파 시간을 고려해도 모순인 반응이 있는가?

#### 4. Blueprint 준수 여부
- Blueprint에 설계된 핵심 씬(Core Scene)이 원고에 반영되었는가?
- Blueprint의 Cliffhanger 엔딩이 원고 끝에 구현되었는가?
- 설계된 공간/시간 배경이 원고와 일치하는가?
- Blueprint 범위를 넘어선 과잉 생성이 없는가?

### 🚨 판정 기준
- CRITICAL: 명백한 모순 (없는 아이템 사용, 죽은 NPC 등장, 수여 전 소지)
- MAJOR: 심각한 불일치 (상태 급변, 설정 충돌, Blueprint 핵심 씬 누락)
- MINOR: 경미한 차이 (표현 방식, 세부 묘사 차이)
- NONE: 연속성 문제 없음

### [Chain-of-Thought Analysis]
다음 순서로 분석하십시오:

Step 1: 아이템/무기 추적
- 이전 원고들에서 획득한 아이템 목록 작성
- 현재 원고에서 사용/소지하는 아이템 확인
- 미획득 아이템 사용 여부 판정

Step 2: 상태 연속성 분석
- 직전 원고 종료 시점의 상태 확인
- 현재 원고 시작 시점의 상태 확인
- 급격한 변화 여부 판정

Step 3: 관계 일관성 분석
- 이전 원고들의 관계 변화 추적
- 현재 원고의 NPC 반응 확인
- 관계 역행 여부 판정

Step 4: Blueprint 준수 분석
- Blueprint 핵심 씬 목록 확인
- 원고에서 해당 씬 반영 여부 확인
- 누락/과잉 생성 여부 판정

Step 5: 최종 판정
- 위 4단계를 종합하여 PASS/REJECT 결정
- 위반 사항 목록 작성
- 수정 지시 작성

[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "REJECT",
    "severity": "NONE" 또는 "MINOR" 또는 "MAJOR" 또는 "CRITICAL",
    "continuity_analysis": {{
        "items_in_prev": ["이전 원고들에서 획득한 아이템"],
        "items_used_now": ["현재 원고에서 사용하는 아이템"],
        "items_used_correctly": true/false,
        "state_from_prev": "직전 원고 종료 시 상태",
        "state_in_current": "현재 원고 시작 시 상태",
        "state_consistent": true/false,
        "relationships_consistent": true/false
    }},
    "blueprint_alignment": {{
        "core_scenes_in_blueprint": ["Blueprint의 핵심 씬 목록"],
        "scenes_reflected_in_manuscript": ["원고에 반영된 씬 목록"],
        "scenes_reflected": 반영된_씬_개수,
        "total_scenes": 총_씬_개수,
        "cliffhanger_implemented": true/false,
        "missing_elements": ["누락된 요소 목록"],
        "excess_elements": ["과잉 생성된 요소 목록"]
    }},
    "violations": [
        {{
            "type": "unowned_item_usage" | "state_discontinuity" | "relationship_reversal" | "blueprint_violation",
            "severity": "CRITICAL" | "MAJOR" | "MINOR",
            "description": "위반 상세 설명",
            "evidence_prev": "이전 원고 근거",
            "evidence_curr": "현재 원고 근거"
        }}
    ],
    "warnings": ["MINOR 수준의 경고 목록"],
    "fix_instructions": "수정 지시 (REJECT 시 필수, PASS 시 권고사항)"
}}
"""


class ContinuityInspector(BaseAgent):
    """
    [V49] Director 산하 연속성 검증 전문 에이전트
    
    역할:
    1. [V49 NEW] Arc 수준 연속성 검증 - Arc 간 + 단일 Arc 내 모순 탐지
    2. 전체 블루프린트 분석 (1화부터 현재까지)
    3. 아이템/패 획득 타임라인 추적
    4. 캐릭터 상태 흐름 검증
    5. 모순 감지 시 구체적 수정 지시 제공
    
    [V49 Update]
    - 모델: gemini-2.5-pro (대용량 컨텍스트, 고정밀 추론)
    - [NEW] inspect_arc(): Stage 2에서 Arc 설계 후 호출
    - inspect(): Stage 3에서 블루프린트 생성 후 호출
    """
    
    def __init__(self, context, client, model_tier="gemini-2.5-pro"):
        """
        Args:
            context: ProjectContext 객체
            client: Gemini API 클라이언트
            model_tier: 사용할 모델 (기본: gemini-2.5-pro - 고정밀 분석)
        """
        super().__init__(context, client, model_tier)
        
        # 아이템 획득 패턴 (한국어)
        self.acquire_patterns = [
            r"(.+?)(?:을|를)\s*(?:집어\s*들|뽑아\s*들|획득|챙기|얻|주워\s*들|가져)",
            r"(.+?)(?:을|를)\s*(?:손에\s*넣|가져가|챙겨\s*들)",
            r"(?:녹슨|묵직한|육중한)?\s*(.+?)(?:을|를)\s*(?:집어\s*들|뽑아\s*들)",
            r"(.+?)(?:을|를)\s*(?:발견|찾아)",
        ]
        
        # 수여/하사 패턴 (범용)
        self.grant_patterns = [
            r"(.+?)(?:을|를)\s*(?:하사|수여|내리|던져\s*주|건네)",
            r"(.+?)(?:을|를)\s*(?:풀어|떼어)\s*(?:던지|주)",
            r"(.+?)(?:을|를)\s*(?:위임|부여|임명)",
            r"(.+?권).*?(?:위임|부여|하사)",  # ~권 패턴
            r"(.+?패).*?(?:하사|수여|던지)",  # ~패 패턴
        ]
        
        # 소지/사용 패턴
        self.possession_patterns = [
            r"품속.*?(.+?)(?:이|가)\s*(?:있|자리)",
            r"(.+?)(?:을|를)\s*(?:들어\s*보이|꺼내|쥐)",
            r"(?:쥔|든|멘)\s*(.+?)",
        ]
    
    def inspect(self, current_ep: int, current_blueprint: dict,
                prev_blueprints: List[dict], hud_history: List[dict] = None) -> dict:
        """
        블루프린트 연속성 검증 실행
        
        Args:
            current_ep: 현재 에피소드 번호
            current_blueprint: 현재 블루프린트 dict
            prev_blueprints: 이전 에피소드 블루프린트 리스트 [{ep_num, integrated_scenario, ...}, ...]
            hud_history: HUD 스냅샷 히스토리 (선택적)
        
        Returns:
            {
                "decision": "PASS" | "REJECT",
                "severity": "NONE" | "MINOR" | "MAJOR" | "CRITICAL",
                "violations": [...],
                "warnings": [...],
                "fix_instructions": "..."
            }
        """
        # 1화는 이전 에피소드가 없으므로 자동 PASS
        if current_ep <= 1 or not prev_blueprints:
            return {
                "decision": "PASS",
                "severity": "NONE",
                "timeline_analysis": {},
                "violations": [],
                "warnings": [],
                "fix_instructions": ""
            }
        
        # 현재 시나리오 추출
        current_scenario = current_blueprint.get('integrated_scenario', '')
        if not current_scenario:
            return {
                "decision": "REJECT",
                "severity": "CRITICAL",
                "timeline_analysis": {},
                "violations": [{
                    "type": "missing_scenario",
                    "severity": "CRITICAL",
                    "description": "블루프린트에 integrated_scenario가 없습니다."
                }],
                "warnings": [],
                "fix_instructions": "integrated_scenario를 포함한 완전한 블루프린트를 생성하십시오."
            }
        
        # ═══════════════════════════════════════════════════════════════
        # Phase 1: Python 기반 사전 필터링 (빠른 검증)
        # ═══════════════════════════════════════════════════════════════
        python_check = self._python_precheck(current_ep, current_scenario, prev_blueprints)
        
        # 명백한 위반이 감지되면 LLM 호출 없이 즉시 REJECT
        if python_check['critical_violations']:
            return {
                "decision": "REJECT",
                "severity": "CRITICAL",
                "timeline_analysis": python_check.get('timeline', {}),
                "violations": python_check['critical_violations'],
                "warnings": python_check.get('warnings', []),
                "fix_instructions": self._generate_fix_instructions(python_check['critical_violations'])
            }
        
        # ═══════════════════════════════════════════════════════════════
        # Phase 2: LLM 기반 정밀 검증 (미묘한 모순 탐지)
        # ═══════════════════════════════════════════════════════════════
        
        # 이전 블루프린트 요약 생성
        prev_summaries = self._format_prev_blueprints(prev_blueprints)
        
        # 프롬프트 조립
        prompt = CONTINUITY_INSPECTION_PROMPT.format(
            current_ep=current_ep,
            current_scenario=self._escape_braces(current_scenario[:4000]),  # 토큰 제한
            prev_count=len(prev_blueprints),
            prev_summaries=self._escape_braces(prev_summaries)
        )
        
        try:
            response = self.ask(prompt, temperature=0.1)
            result = self._extract_json_robust(response)
            
            # 결과 검증 및 보완
            if not isinstance(result, dict):
                result = {"decision": "PASS", "severity": "NONE", "violations": [], "warnings": []}
            
            # Python 검증 결과 병합
            if python_check.get('warnings'):
                result.setdefault('warnings', [])
                result['warnings'].extend(python_check['warnings'])
            
            return result
            
        except Exception as e:
            print(f"      🚨 [ContinuityInspector] LLM 검증 실패: {e}")
            # LLM 실패 시 Python 검증 결과만 반환
            if python_check.get('warnings'):
                return {
                    "decision": "PASS",
                    "severity": "MINOR",
                    "timeline_analysis": python_check.get('timeline', {}),
                    "violations": [],
                    "warnings": python_check['warnings'],
                    "fix_instructions": "LLM 검증 실패 - Python 사전 검증만 수행됨"
                }
            return {
                "decision": "PASS",
                "severity": "NONE",
                "violations": [],
                "warnings": ["LLM 검증 실패 - 수동 확인 권장"],
                "fix_instructions": ""
            }
    
    # =================================================================
    # [V49 NEW] Arc 수준 연속성 검증
    # =================================================================
    
    def inspect_arc(self, current_arc: dict, prev_arcs: List[dict]) -> dict:
        """
        [V49] Arc 수준 연속성 검증 실행
        
        Stage 2에서 Analyst가 Arc 설계 후, Director 검증 전에 호출
        
        Args:
            current_arc: 현재 Arc dict {arc_no, tactical_doc, joint_docs, status_shadow, ep_start, ep_end, ...}
            prev_arcs: 이전 Arc 리스트 [{arc_no, tactical_doc, joint_docs, ...}, ...]
        
        Returns:
            {
                "decision": "PASS" | "REJECT",
                "severity": "NONE" | "MINOR" | "MAJOR" | "CRITICAL",
                "violations": [...],
                "warnings": [...],
                "fix_instructions": "..."
            }
        """
        arc_no = current_arc.get('arc_no', 0)
        
        # Arc 1은 이전 Arc가 없으므로 단일 Arc 내 모순만 검증
        if arc_no <= 1 or not prev_arcs:
            return self._inspect_intra_arc_only(current_arc)
        
        # 현재 Arc 데이터 추출
        tactical_doc = current_arc.get('tactical_doc', '')
        joint_docs = current_arc.get('joint_docs', {})
        status_shadow = current_arc.get('status_shadow', {})
        ep_start = current_arc.get('ep_start', 1)
        ep_end = current_arc.get('ep_end', ep_start + 4)
        ep_count = current_arc.get('ep_count', ep_end - ep_start + 1)
        
        if not tactical_doc:
            return {
                "decision": "REJECT",
                "severity": "CRITICAL",
                "cross_arc_analysis": {},
                "intra_arc_analysis": {},
                "violations": [{
                    "type": "missing_tactical_doc",
                    "severity": "CRITICAL",
                    "description": "Arc에 tactical_doc이 없습니다."
                }],
                "warnings": [],
                "fix_instructions": "tactical_doc을 포함한 완전한 Arc를 설계하십시오."
            }
        
        # ═══════════════════════════════════════════════════════════════
        # Phase 1: Python 기반 사전 필터링 (빠른 검증)
        # ═══════════════════════════════════════════════════════════════
        python_check = self._arc_python_precheck(current_arc, prev_arcs)
        
        # 명백한 위반이 감지되면 LLM 호출 없이 즉시 REJECT
        if python_check['critical_violations']:
            return {
                "decision": "REJECT",
                "severity": "CRITICAL",
                "cross_arc_analysis": python_check.get('cross_arc_timeline', {}),
                "intra_arc_analysis": python_check.get('intra_arc_analysis', {}),
                "violations": python_check['critical_violations'],
                "warnings": python_check.get('warnings', []),
                "fix_instructions": self._generate_arc_fix_instructions(python_check['critical_violations'])
            }
        
        # ═══════════════════════════════════════════════════════════════
        # Phase 2: LLM 기반 정밀 검증 (미묘한 모순 탐지)
        # ═══════════════════════════════════════════════════════════════
        
        # 이전 Arc 요약 생성
        prev_arcs_summary = self._format_prev_arcs(prev_arcs)
        
        # 프롬프트 조립
        prompt = ARC_CONTINUITY_INSPECTION_PROMPT.format(
            current_arc_no=arc_no,
            ep_count=ep_count,
            ep_start=ep_start,
            ep_end=ep_end,
            tactical_doc=self._escape_braces(tactical_doc[:6000]),  # 토큰 제한
            joint_docs=self._escape_braces(json.dumps(joint_docs, ensure_ascii=False)),
            status_shadow=self._escape_braces(json.dumps(status_shadow, ensure_ascii=False)),
            prev_arc_count=len(prev_arcs),
            prev_arcs_summary=self._escape_braces(prev_arcs_summary)
        )
        
        try:
            response = self.ask(prompt, temperature=0.1)
            result = self._extract_json_robust(response)
            
            # 결과 검증 및 보완
            if not isinstance(result, dict):
                result = {"decision": "PASS", "severity": "NONE", "violations": [], "warnings": []}
            
            # Python 검증 결과 병합
            if python_check.get('warnings'):
                result.setdefault('warnings', [])
                result['warnings'].extend(python_check['warnings'])
            
            return result
            
        except Exception as e:
            print(f"      🚨 [ContinuityInspector] Arc LLM 검증 실패: {e}")
            # LLM 실패 시 Python 검증 결과만 반환
            if python_check.get('warnings'):
                return {
                    "decision": "PASS",
                    "severity": "MINOR",
                    "cross_arc_analysis": python_check.get('cross_arc_timeline', {}),
                    "intra_arc_analysis": python_check.get('intra_arc_analysis', {}),
                    "violations": [],
                    "warnings": python_check['warnings'] + ["LLM 검증 실패 - 수동 확인 권장"],
                    "fix_instructions": ""
                }
            return {
                "decision": "PASS",
                "severity": "NONE",
                "violations": [],
                "warnings": ["Arc LLM 검증 실패 - 수동 확인 권장"],
                "fix_instructions": ""
            }
    
    def _inspect_intra_arc_only(self, current_arc: dict) -> dict:
        """
        [V49] Arc 1 또는 이전 Arc 없을 때 단일 Arc 내 모순만 검증
        """
        arc_no = current_arc.get('arc_no', 1)
        tactical_doc = current_arc.get('tactical_doc', '')
        
        if not tactical_doc:
            return {
                "decision": "REJECT",
                "severity": "CRITICAL",
                "violations": [{
                    "type": "missing_tactical_doc",
                    "severity": "CRITICAL",
                    "description": "Arc에 tactical_doc이 없습니다."
                }],
                "warnings": [],
                "fix_instructions": "tactical_doc을 포함한 완전한 Arc를 설계하십시오."
            }
        
        # 단일 Arc 내 모순 검증
        intra_violations = self._check_intra_arc_consistency(current_arc)
        
        if intra_violations:
            critical = [v for v in intra_violations if v.get('severity') == 'CRITICAL']
            if critical:
                return {
                    "decision": "REJECT",
                    "severity": "CRITICAL",
                    "intra_arc_analysis": {"internal_contradictions": intra_violations},
                    "violations": intra_violations,
                    "warnings": [],
                    "fix_instructions": self._generate_arc_fix_instructions(intra_violations)
                }
            else:
                return {
                    "decision": "PASS",
                    "severity": "MINOR",
                    "intra_arc_analysis": {"internal_contradictions": intra_violations},
                    "violations": [],
                    "warnings": [v.get('description', '') for v in intra_violations],
                    "fix_instructions": ""
                }
        
        return {
            "decision": "PASS",
            "severity": "NONE",
            "violations": [],
            "warnings": [],
            "fix_instructions": ""
        }
    
    def _arc_python_precheck(self, current_arc: dict, prev_arcs: List[dict]) -> dict:
        """
        [V49] Arc 수준 Python 기반 사전 검증
        
        Returns:
            {
                "critical_violations": [...],
                "warnings": [...],
                "cross_arc_timeline": {...},
                "intra_arc_analysis": {...}
            }
        """
        critical_violations = []
        warnings = []
        
        current_arc_no = current_arc.get('arc_no', 0)
        tactical_doc = current_arc.get('tactical_doc', '')
        joint_docs = current_arc.get('joint_docs', {})
        
        # 이전 Arc들에서 획득한 아이템/수여물 추적
        acquired_items = {}   # {아이템명: Arc 번호}
        granted_items = {}    # {수여물: Arc 번호}
        prev_inventory = {}   # 직전 Arc의 physical_inventory
        prev_status = {}      # 직전 Arc의 status_shadow
        
        for arc in prev_arcs:
            arc_no = arc.get('arc_no', 0)
            arc_tactical = arc.get('tactical_doc', '')
            arc_joint = arc.get('joint_docs', {})
            arc_status = arc.get('status_shadow', {})
            
            # tactical_doc에서 획득 패턴 검색
            for pattern in self.acquire_patterns:
                matches = re.findall(pattern, arc_tactical)
                for item in matches:
                    item = item.strip()
                    if item and len(item) >= 2:
                        acquired_items[item] = arc_no
            
            # tactical_doc에서 수여 패턴 검색
            for pattern in self.grant_patterns:
                matches = re.findall(pattern, arc_tactical)
                for item in matches:
                    item = item.strip()
                    if item and len(item) >= 2:
                        granted_items[item] = arc_no
            
            # joint_docs에서 physical_inventory 추출
            inventory = arc_joint.get('physical_inventory', '')
            if inventory:
                for pattern in self.acquire_patterns:
                    matches = re.findall(pattern, inventory)
                    for item in matches:
                        item = item.strip()
                        if item and len(item) >= 2:
                            acquired_items[item] = arc_no
            
            # 직전 Arc 정보 저장
            prev_inventory = arc_joint
            prev_status = arc_status
        
        # 현재 Arc에서 획득하려는 아이템 검색
        current_acquisitions = []
        for pattern in self.acquire_patterns:
            matches = re.findall(pattern, tactical_doc)
            for item in matches:
                item = item.strip()
                if item and len(item) >= 2:
                    current_acquisitions.append(item)
        
        # ═══════════════════════════════════════════════════════════════
        # 검증 1: 중복 획득 (이전 Arc에서 이미 획득한 아이템을 다시 획득)
        # ═══════════════════════════════════════════════════════════════
        for curr_item in current_acquisitions:
            for prev_item, prev_arc in acquired_items.items():
                if self._is_same_item(curr_item, prev_item):
                    critical_violations.append({
                        "type": "duplicate_acquisition",
                        "severity": "CRITICAL",
                        "item_or_subject": curr_item,
                        "prev_arc": prev_arc,
                        "description": f"'{prev_item}'은(는) 이미 Arc {prev_arc}에서 획득했습니다. "
                                      f"Arc {current_arc_no}에서 다시 획득하려 합니다.",
                        "evidence_prev": f"Arc {prev_arc}에서 획득",
                        "evidence_curr": f"현재 Arc에서 '{curr_item}' 획득 시도"
                    })
                    break
        
        # ═══════════════════════════════════════════════════════════════
        # 검증 2: 단일 Arc 내 모순
        # ═══════════════════════════════════════════════════════════════
        intra_violations = self._check_intra_arc_consistency(current_arc)
        for v in intra_violations:
            if v.get('severity') == 'CRITICAL':
                critical_violations.append(v)
            else:
                warnings.append(v.get('description', ''))
        
        # ═══════════════════════════════════════════════════════════════
        # 검증 3: 상태 연속성 (부상/내공 급변)
        # ═══════════════════════════════════════════════════════════════
        if prev_status:
            prev_injuries = prev_status.get('expected_injuries', '')
            # 직전 Arc에서 심각한 부상이 있었는데 현재 Arc에서 언급 없으면 경고
            if prev_injuries and prev_injuries not in ['없음', '경미', '']:
                if '부상' not in tactical_doc and '회복' not in tactical_doc and '치료' not in tactical_doc:
                    warnings.append(
                        f"직전 Arc에서 '{prev_injuries}' 부상이 있었으나, "
                        f"현재 Arc에서 부상/회복 관련 언급이 없습니다."
                    )
        
        # 타임라인 정보 구성
        cross_arc_timeline = {
            "items_acquired_before": list(acquired_items.keys()),
            "grants_received_before": list(granted_items.keys()),
            "items_in_current_arc": current_acquisitions,
            "prev_inventory": prev_inventory,
            "prev_status": prev_status
        }
        
        intra_arc_analysis = {
            "internal_contradictions": [v.get('description', '') for v in intra_violations]
        }
        
        return {
            "critical_violations": critical_violations,
            "warnings": warnings,
            "cross_arc_timeline": cross_arc_timeline,
            "intra_arc_analysis": intra_arc_analysis
        }
    
    def _check_intra_arc_consistency(self, arc: dict) -> List[dict]:
        """
        [V49] 단일 Arc 내 모순 검증
        
        tactical_doc 내에서 화 사이의 모순을 탐지
        """
        violations = []
        tactical_doc = arc.get('tactical_doc', '')
        beat_sequence = arc.get('beat_sequence', [])
        ep_start = arc.get('ep_start', 1)
        
        if not tactical_doc:
            return violations
        
        # 각 화별 섹션 분리 시도
        ep_sections = {}
        
        # "[제 N화 전술 설계]" 패턴으로 분리
        section_pattern = r'\[제\s*(\d+)화[^\]]*\]'
        sections = re.split(section_pattern, tactical_doc)
        
        if len(sections) > 1:
            # 섹션이 성공적으로 분리된 경우
            for i in range(1, len(sections), 2):
                if i + 1 < len(sections):
                    ep_num = int(sections[i])
                    ep_content = sections[i + 1]
                    ep_sections[ep_num] = ep_content
        
        # 화별 획득 아이템 추적 (단일 Arc 내)
        arc_acquisitions = {}  # {아이템: 획득 화수}
        
        for ep_num, content in ep_sections.items():
            for pattern in self.acquire_patterns:
                matches = re.findall(pattern, content)
                for item in matches:
                    item = item.strip()
                    if item and len(item) >= 2:
                        if item in arc_acquisitions:
                            # 같은 Arc 내에서 동일 아이템 중복 획득
                            prev_ep = arc_acquisitions[item]
                            if ep_num != prev_ep:
                                violations.append({
                                    "type": "intra_arc_contradiction",
                                    "severity": "CRITICAL",
                                    "item_or_subject": item,
                                    "prev_ep": prev_ep,
                                    "curr_ep": ep_num,
                                    "description": f"'{item}'을(를) 제{prev_ep}화에서 획득했는데, "
                                                  f"제{ep_num}화에서 다시 획득하려 합니다. (Arc 내 모순)"
                                })
                        else:
                            arc_acquisitions[item] = ep_num
        
        # 부상/상태 연속성 검증 (인접 화 사이)
        sorted_eps = sorted(ep_sections.keys())
        for i in range(len(sorted_eps) - 1):
            curr_ep = sorted_eps[i]
            next_ep = sorted_eps[i + 1]
            curr_content = ep_sections[curr_ep]
            next_content = ep_sections[next_ep]
            
            # 부상 패턴
            injury_pattern = r'(?:부상|상처|파열|골절|출혈|기절)'
            if re.search(injury_pattern, curr_content):
                # 다음 화에서 부상 관련 언급 없이 전투/격렬한 활동이 있으면 경고
                action_pattern = r'(?:전투|격전|결투|비무|대결)'
                if re.search(action_pattern, next_content) and not re.search(r'(?:회복|치료|휴식)', next_content):
                    violations.append({
                        "type": "state_discontinuity",
                        "severity": "MINOR",
                        "item_or_subject": "부상 상태",
                        "prev_ep": curr_ep,
                        "curr_ep": next_ep,
                        "description": f"제{curr_ep}화에서 부상이 발생했으나, "
                                      f"제{next_ep}화에서 회복 없이 격렬한 활동이 설정됨 (경고)"
                    })
        
        return violations
    
    def _format_prev_arcs(self, prev_arcs: List[dict]) -> str:
        """
        [V49] 이전 Arc들을 LLM용 타임라인 형식으로 변환
        """
        summaries = []
        
        # 전체 타임라인 구조화
        all_acquisitions = []  # [(arc_no, item), ...]
        all_grants = []        # [(arc_no, grant), ...]
        
        for arc in prev_arcs:
            arc_no = arc.get('arc_no', '?')
            tactical_doc = arc.get('tactical_doc', '')
            joint_docs = arc.get('joint_docs', {})
            status_shadow = arc.get('status_shadow', {})
            ep_start = arc.get('ep_start', '?')
            ep_end = arc.get('ep_end', '?')
            
            # 핵심 정보 추출
            items = self._extract_acquisitions(tactical_doc)
            grants = self._extract_grants(tactical_doc)
            
            # 타임라인에 추가
            for item in items:
                all_acquisitions.append((arc_no, item))
            for grant in grants:
                all_grants.append((arc_no, grant))
            
            # Arc별 요약
            summary = f"""
═══ Arc {arc_no} (제 {ep_start}화 ~ 제 {ep_end}화) ═══
[종료 시점 상태 (joint_docs)]
- 위치: {joint_docs.get('final_location', '미정')}
- 소지품: {joint_docs.get('physical_inventory', '미정')}
- 세계 변화: {joint_docs.get('world_joint', '미정')}

[예상 손실 (status_shadow)]
- 내공 소모: {status_shadow.get('internal_energy_loss', '0%')}
- 예상 부상: {status_shadow.get('expected_injuries', '없음')}

[획득 아이템] {', '.join(items) if items else '없음'}
[수여물] {', '.join(grants) if grants else '없음'}

[핵심 전술 요약]
{tactical_doc[:1500] if tactical_doc else '없음'}...
"""
            summaries.append(summary)
        
        # 전체 타임라인 헤더 추가
        timeline_header = f"""
╔══════════════════════════════════════════════════════════════╗
║  전체 아이템/수여물 타임라인 (Arc 1 ~ Arc {len(prev_arcs)})  ║
╚══════════════════════════════════════════════════════════════╝

[📦 획득 아이템 타임라인]
{self._format_arc_timeline(all_acquisitions) if all_acquisitions else '- 없음'}

[🎖️ 수여물 타임라인]
{self._format_arc_timeline(all_grants) if all_grants else '- 없음'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return timeline_header + "\n".join(summaries)
    
    def _format_arc_timeline(self, items: List[tuple]) -> str:
        """Arc 타임라인 항목을 포맷팅"""
        lines = []
        for arc_no, item in items:
            lines.append(f"- Arc {arc_no}: {item}")
        return "\n".join(lines)
    
    def _generate_arc_fix_instructions(self, violations: List[dict]) -> str:
        """Arc 위반 사항에 대한 수정 지시 생성"""
        instructions = []
        
        for v in violations:
            v_type = v.get('type', '')
            item = v.get('item_or_subject', '')
            prev_arc = v.get('prev_arc')
            prev_ep = v.get('prev_ep')
            curr_ep = v.get('curr_ep')
            
            if v_type == 'duplicate_acquisition':
                if prev_arc:
                    instructions.append(
                        f"[중복 획득 수정] '{item}'은(는) 이미 Arc {prev_arc}에서 획득했습니다. "
                        f"현재 Arc에서는 '이미 소지 중'인 상태로 시작해야 합니다. "
                        f"다시 획득하는 장면을 삭제하고, 기존에 가지고 있던 것을 사용하는 것으로 수정하세요."
                    )
                else:
                    instructions.append(
                        f"[중복 획득 수정] '{item}'은(는) 이미 제{prev_ep}화에서 획득했습니다. "
                        f"제{curr_ep}화에서 다시 획득하는 설정을 삭제하세요."
                    )
            elif v_type == 'intra_arc_contradiction':
                instructions.append(
                    f"[Arc 내 모순 수정] '{item}'이(가) 제{prev_ep}화와 제{curr_ep}화 사이에서 모순됩니다. "
                    f"해당 화차의 설정을 일관되게 수정하세요."
                )
            elif v_type == 'state_discontinuity':
                instructions.append(
                    f"[상태 불연속 수정] 제{prev_ep}화에서 발생한 상태 변화가 "
                    f"제{curr_ep}화에서 반영되지 않았습니다. 회복/치료 장면을 추가하거나 "
                    f"상태에 맞는 행동으로 수정하세요."
                )
            elif v_type == 'setting_inconsistency':
                instructions.append(
                    f"[설정 불일치 수정] '{item}'의 물리적 특성이 일관되지 않습니다. "
                    f"설정을 통일하세요."
                )
        
        return "\n".join(instructions) if instructions else "위반 사항을 확인하고 수정하세요."
    
    def _python_precheck(self, current_ep: int, current_scenario: str,
                         prev_blueprints: List[dict]) -> dict:
        """
        Python 기반 사전 검증 (빠른 필터링)
        
        Returns:
            {
                "critical_violations": [...],
                "warnings": [...],
                "timeline": {...}
            }
        """
        critical_violations = []
        warnings = []
        
        # 이전 에피소드에서 획득한 아이템 추적
        acquired_items = {}  # {아이템명: 획득 에피소드}
        granted_items = {}   # {수여물: 수여 에피소드}
        
        for bp in prev_blueprints:
            ep_num = bp.get('ep_num', 0)
            scenario = bp.get('integrated_scenario', '')
            
            # 획득 패턴 검색
            for pattern in self.acquire_patterns:
                matches = re.findall(pattern, scenario)
                for item in matches:
                    item = item.strip()
                    if item and len(item) >= 2:
                        acquired_items[item] = ep_num
            
            # 수여 패턴 검색
            for pattern in self.grant_patterns:
                matches = re.findall(pattern, scenario)
                for item in matches:
                    item = item.strip()
                    if item and len(item) >= 2:
                        granted_items[item] = ep_num
        
        # 현재 블루프린트에서 획득하려는 아이템 검색
        current_acquisitions = []
        for pattern in self.acquire_patterns:
            matches = re.findall(pattern, current_scenario)
            for item in matches:
                item = item.strip()
                if item and len(item) >= 2:
                    current_acquisitions.append(item)
        
        # 현재 블루프린트에서 소지/사용하는 수여물 검색
        current_possessions = []
        for pattern in self.possession_patterns:
            matches = re.findall(pattern, current_scenario)
            for item in matches:
                item = item.strip()
                if item and len(item) >= 2:
                    current_possessions.append(item)
        
        # ═══════════════════════════════════════════════════════════════
        # 검증 1: 중복 획득 (이미 획득한 아이템을 다시 획득)
        # ═══════════════════════════════════════════════════════════════
        for curr_item in current_acquisitions:
            for prev_item, prev_ep in acquired_items.items():
                if self._is_same_item(curr_item, prev_item):
                    critical_violations.append({
                        "type": "duplicate_acquisition",
                        "severity": "CRITICAL",
                        "item_or_subject": curr_item,
                        "prev_ep": prev_ep,
                        "description": f"'{prev_item}'은(는) 이미 제{prev_ep}화에서 획득했습니다. "
                                      f"제{current_ep}화에서 다시 획득하려 합니다.",
                        "evidence_prev": f"제{prev_ep}화에서 획득",
                        "evidence_curr": f"현재 '{curr_item}' 획득 시도"
                    })
                    break
        
        # ═══════════════════════════════════════════════════════════════
        # 검증 2: 미수여 소지 (아직 받지 않은 것을 소지)
        # ═══════════════════════════════════════════════════════════════
        # 주요 수여물 키워드 (범용 패턴)
        # ~패, ~권, ~서, ~인 등 수여물 접미사 기반 탐지
        grant_keywords = ['패', '권', '인장', '직위', '자격', '서']  # 범용 접미사
        
        for possession in current_possessions:
            for keyword in grant_keywords:
                if keyword in possession:
                    # 이 수여물이 이전에 수여되었는지 확인
                    was_granted = False
                    granted_ep = None
                    for granted_item, g_ep in granted_items.items():
                        if keyword in granted_item:
                            was_granted = True
                            granted_ep = g_ep
                            break
                    
                    if not was_granted:
                        critical_violations.append({
                            "type": "premature_possession",
                            "severity": "CRITICAL",
                            "item_or_subject": possession,
                            "prev_ep": None,
                            "description": f"'{possession}'을(를) 소지하고 있으나, "
                                          f"이전 에피소드에서 수여받은 기록이 없습니다.",
                            "evidence_prev": "수여 기록 없음",
                            "evidence_curr": f"현재 '{possession}' 소지/사용"
                        })
                    break
        
        # 타임라인 정보 구성
        timeline = {
            "items_acquired_before": list(acquired_items.keys()),
            "grants_received_before": list(granted_items.keys()),
            "items_acquired_now": current_acquisitions,
            "items_possessed_now": current_possessions
        }
        
        return {
            "critical_violations": critical_violations,
            "warnings": warnings,
            "timeline": timeline
        }
    
    def _format_prev_blueprints(self, prev_blueprints: List[dict]) -> str:
        """
        [V48.1] 전체 블루프린트를 LLM용 타임라인 형식으로 변환
        
        대용량 컨텍스트(gemini-2.5-pro)를 활용하여 전체 에피소드의
        핵심 정보를 구조화된 형태로 제공
        """
        summaries = []
        
        # 전체 타임라인 구조화
        all_acquisitions = []  # [(ep, item), ...]
        all_grants = []        # [(ep, grant), ...]
        all_status_changes = [] # [(ep, change), ...]
        
        for bp in prev_blueprints:
            ep_num = bp.get('ep_num', '?')
            scenario = bp.get('integrated_scenario', '')
            
            # 핵심 정보 추출
            items = self._extract_acquisitions(scenario)
            grants = self._extract_grants(scenario)
            key_sentences = self._extract_key_sentences(scenario)
            
            # 타임라인에 추가
            for item in items:
                all_acquisitions.append((ep_num, item))
            for grant in grants:
                all_grants.append((ep_num, grant))
            
            # 에피소드별 요약 (더 많은 컨텍스트 제공)
            summary = f"""
═══ 제 {ep_num}화 ═══
[핵심 사건]
{key_sentences[:2000]}

[획득 아이템] {', '.join(items) if items else '없음'}
[수여물] {', '.join(grants) if grants else '없음'}
"""
            summaries.append(summary)
        
        # 전체 타임라인 헤더 추가
        timeline_header = f"""
╔══════════════════════════════════════════════════════════════╗
║  전체 아이템/수여물 타임라인 (제1화 ~ 제{len(prev_blueprints)}화)  ║
╚══════════════════════════════════════════════════════════════╝

[📦 획득 아이템 타임라인]
{self._format_timeline(all_acquisitions) if all_acquisitions else '- 없음'}

[🎖️ 수여물 타임라인]
{self._format_timeline(all_grants) if all_grants else '- 없음'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return timeline_header + "\n".join(summaries)
    
    def _format_timeline(self, items: List[tuple]) -> str:
        """타임라인 항목을 포맷팅"""
        lines = []
        for ep, item in items:
            lines.append(f"- 제{ep}화: {item}")
        return "\n".join(lines)
    
    def _extract_acquisitions(self, scenario: str) -> List[str]:
        """시나리오에서 획득 아이템 추출"""
        items = []
        for pattern in self.acquire_patterns:
            matches = re.findall(pattern, scenario)
            for item in matches:
                item = item.strip()
                if item and 2 <= len(item) <= 20:
                    items.append(item)
        return list(set(items))[:5]  # 중복 제거, 최대 5개
    
    def _extract_grants(self, scenario: str) -> List[str]:
        """시나리오에서 수여물 추출"""
        grants = []
        for pattern in self.grant_patterns:
            matches = re.findall(pattern, scenario)
            for grant in matches:
                grant = grant.strip() if isinstance(grant, str) else str(grant)
                if grant and 2 <= len(grant) <= 20:
                    grants.append(grant)
        return list(set(grants))[:3]  # 중복 제거, 최대 3개
    
    def _extract_key_sentences(self, scenario: str) -> str:
        """시나리오에서 연속성 관련 핵심 문장 추출"""
        key_patterns = [
            r'[^.。!?]*(?:획득|집어\s*들|뽑아\s*들|챙기|얻)[^.。!?]*[.。!?]',
            r'[^.。!?]*(?:하사|수여|위임|부여)[^.。!?]*[.。!?]',
            r'[^.。!?]*(?:부상|상처|파열|회복)[^.。!?]*[.。!?]',
            r'[^.。!?]*(?:품속|손에|어깨에|허리에)[^.。!?]*[.。!?]',
            r'[^.。!?]*(?:하사|수여|위임|부여|임명)[^.。!?]*[.。!?]',  # 수여 관련 문장
        ]
        
        key_sentences = set()
        for pattern in key_patterns:
            matches = re.findall(pattern, scenario)
            for match in matches:
                if len(match.strip()) > 10:
                    key_sentences.add(match.strip())
        
        # 순서 유지를 위해 원문에서의 위치로 정렬
        sorted_sentences = sorted(
            key_sentences,
            key=lambda s: scenario.find(s) if scenario.find(s) >= 0 else len(scenario)
        )
        
        # 핵심 문장들을 연결
        result = " ... ".join(sorted_sentences[:10])  # 최대 10개
        
        # 핵심 문장이 부족하면 시나리오 앞/뒤 추가
        if len(result) < 500:
            result = scenario[:800] + " ... [중략] ... " + scenario[-500:]
        
        return result
    
    def _is_same_item(self, item1: str, item2: str) -> bool:
        """두 아이템이 같은 것인지 판단"""
        item1 = item1.strip().lower()
        item2 = item2.strip().lower()
        
        if item1 == item2:
            return True
        
        if item1 in item2 or item2 in item1:
            return True
        
        # 핵심 키워드 비교
        keywords1 = set(re.findall(r'[가-힣]{2,}', item1))
        keywords2 = set(re.findall(r'[가-힣]{2,}', item2))
        
        stopwords = {'을', '를', '이', '가', '에', '에서', '으로', '로', '의', '한', '된', '인', '와', '과'}
        keywords1 -= stopwords
        keywords2 -= stopwords
        
        common = keywords1 & keywords2
        if len(common) >= 2:
            return True
        
        # 핵심 무기/아이템 단어
        important_words = ['대도', '검', '창', '도', '패', '환', '단', '권', '서']
        for word in important_words:
            if word in item1 and word in item2:
                return True
        
        return False
    
    def _generate_fix_instructions(self, violations: List[dict]) -> str:
        """위반 사항에 대한 수정 지시 생성"""
        instructions = []
        
        for v in violations:
            v_type = v.get('type', '')
            item = v.get('item_or_subject', '')
            prev_ep = v.get('prev_ep')
            
            if v_type == 'duplicate_acquisition':
                instructions.append(
                    f"[중복 획득 수정] '{item}'은(는) 이미 제{prev_ep}화에서 획득했습니다. "
                    f"현재 에피소드에서는 '이미 소지 중'인 상태로 시작해야 합니다. "
                    f"다시 획득하는 장면을 삭제하고, 기존에 가지고 있던 것을 사용하는 것으로 수정하세요."
                )
            elif v_type == 'premature_possession':
                instructions.append(
                    f"[미수여 소지 수정] '{item}'은(는) 아직 수여받지 않았습니다. "
                    f"해당 수여물을 소지/사용하는 묘사를 삭제하거나, "
                    f"먼저 수여받는 장면이 있는 에피소드 이후로 이동시키세요."
                )
            elif v_type == 'state_discontinuity':
                instructions.append(
                    f"[상태 불연속 수정] 캐릭터 상태가 급격히 변화했습니다. "
                    f"변화에 대한 서사적 근거를 추가하거나, 이전 상태를 유지하세요."
                )
        
        return "\n".join(instructions) if instructions else "위반 사항을 확인하고 수정하세요."
    
    def get_prev_blueprints(self, current_ep: int, window: int = None) -> List[dict]:
        """
        DB에서 이전 블루프린트들을 조회하는 헬퍼 메서드
        
        [V48.1] window=None이면 1화부터 현재 직전까지 전체 조회
        
        Args:
            current_ep: 현재 에피소드 번호
            window: 조회할 이전 에피소드 수 (None이면 전체)
        
        Returns:
            [{ep_num, integrated_scenario, scene_breakdown}, ...]
        """
        prev_blueprints = []
        
        if not hasattr(self, 'context') or not self.context:
            return prev_blueprints
        
        # [V48.1] window=None이면 1화부터 전체 조회
        start_ep = 1 if window is None else max(1, current_ep - window)
        
        for ep in range(start_ep, current_ep):
            try:
                bp = self.context.get_blueprint(ep)
                if bp and isinstance(bp, dict):
                    prev_blueprints.append({
                        'ep_num': ep,
                        'integrated_scenario': bp.get('integrated_scenario', ''),
                        'scene_breakdown': bp.get('scene_breakdown', {})
                    })
            except Exception as e:
                print(f"      ⚠️ [ContinuityInspector] 제{ep}화 블루프린트 조회 실패: {e}")
        
        return prev_blueprints
    
    # =================================================================
    # [V49.1 NEW] Stage 4 원고 연속성 검증
    # =================================================================
    
    def get_prev_manuscripts(self, current_ep: int, window: int = 5) -> List[dict]:
        """
        DB에서 이전 원고들을 조회하는 헬퍼 메서드
        
        Args:
            current_ep: 현재 에피소드 번호
            window: 조회할 이전 에피소드 수 (기본 5화)
        
        Returns:
            [{ep_num, content, title}, ...]
        """
        prev_manuscripts = []
        
        if not hasattr(self, 'context') or not self.context:
            return prev_manuscripts
        
        start_ep = max(1, current_ep - window)
        
        for ep in range(start_ep, current_ep):
            try:
                ms = self.context.db.get_manuscript(ep)
                if ms and isinstance(ms, dict):
                    prev_manuscripts.append({
                        'ep_num': ep,
                        'content': ms.get('content', ''),
                        'title': ms.get('title', '')
                    })
            except Exception as e:
                print(f"      ⚠️ [ContinuityInspector] 제{ep}화 원고 조회 실패: {e}")
        
        return prev_manuscripts
    
    def _manuscript_python_precheck(self, current_ep: int, manuscript: str, 
                                     prev_manuscripts: List[dict], blueprint: dict) -> dict:
        """
        [V49.1] 원고 연속성 Python 기반 사전 필터링
        
        빠른 정규식 기반 검증으로 명백한 위반을 LLM 호출 전에 차단
        """
        critical_violations = []
        warnings = []
        
        # 1. 이전 원고들에서 아이템 추출
        all_acquired_items = set()
        last_ep_items = set()
        last_ep_state = ""
        
        for prev_ms in prev_manuscripts:
            prev_content = prev_ms.get('content', '')
            ep_num = prev_ms.get('ep_num', 0)
            
            # 획득 패턴 매칭
            for pattern in self.ACQUISITION_PATTERNS:
                matches = re.findall(pattern, prev_content)
                for match in matches:
                    item = match.strip() if isinstance(match, str) else match[0].strip() if match else ''
                    if item and len(item) >= 2:
                        all_acquired_items.add(item)
                        if ep_num == current_ep - 1:
                            last_ep_items.add(item)
            
            # 직전 화 상태 추출
            if ep_num == current_ep - 1:
                # 마지막 500자에서 상태 추출
                last_ep_state = prev_content[-500:] if len(prev_content) > 500 else prev_content
        
        # 2. 현재 원고에서 사용 아이템 추출
        used_items = set()
        for pattern in self.POSSESSION_PATTERNS:
            matches = re.findall(pattern, manuscript)
            for match in matches:
                item = match.strip() if isinstance(match, str) else match[0].strip() if match else ''
                if item and len(item) >= 2:
                    used_items.add(item)
        
        # 3. 미획득 아이템 사용 체크
        for item in used_items:
            if item and not self._is_item_acquired(item, all_acquired_items):
                # 일반 명사 필터링 (오탐 방지)
                if item not in ['무기', '검', '도', '창', '활', '손', '발', '몸', '눈', '입']:
                    critical_violations.append({
                        'type': 'unowned_item_usage',
                        'severity': 'CRITICAL',
                        'item_or_subject': item,
                        'description': f"'{item}'은(는) 이전 원고에서 획득한 기록이 없습니다."
                    })
        
        # 4. 부상 상태 연속성 체크
        injury_keywords = ['부상', '중상', '피를 흘', '쓰러', '기절', '골절', '찢어']
        recovery_keywords = ['멀쩡', '회복', '완치', '상처가 아물']
        
        prev_injured = any(kw in last_ep_state for kw in injury_keywords)
        current_start = manuscript[:500] if len(manuscript) > 500 else manuscript
        current_recovered = any(kw in current_start for kw in recovery_keywords)
        
        if prev_injured and current_recovered:
            warnings.append({
                'type': 'rapid_recovery',
                'severity': 'MINOR',
                'description': '직전 화에서 부상 상태였으나 현재 화 시작에서 회복된 것처럼 묘사됨'
            })
        
        # 5. Blueprint 핵심 씬 반영 체크
        scene_breakdown = blueprint.get('scene_breakdown', {})
        if scene_breakdown:
            core_scenes = [k for k, v in scene_breakdown.items() if '[Core]' in str(v)]
            reflected_count = 0
            
            for scene_key in core_scenes:
                scene_desc = scene_breakdown.get(scene_key, '')
                keywords = self._extract_keywords(scene_desc)
                if any(kw in manuscript for kw in keywords if kw):
                    reflected_count += 1
            
            if core_scenes and reflected_count < len(core_scenes) // 2:
                critical_violations.append({
                    'type': 'blueprint_violation',
                    'severity': 'MAJOR',
                    'description': f"Blueprint 핵심 씬 {len(core_scenes)}개 중 {reflected_count}개만 반영됨"
                })
        
        return {
            'critical_violations': critical_violations,
            'warnings': warnings,
            'timeline': {
                'acquired_items': list(all_acquired_items),
                'used_items': list(used_items)
            }
        }
    
    def _is_item_acquired(self, item: str, acquired_items: Set[str]) -> bool:
        """아이템이 이미 획득되었는지 확인 (유사 아이템 포함)"""
        if item in acquired_items:
            return True
        
        # 부분 매칭 허용 (예: '녹슨 대도' vs '대도')
        for acquired in acquired_items:
            if item in acquired or acquired in item:
                return True
        
        return False
    
    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """텍스트에서 핵심 키워드 추출"""
        pattern = r'[가-힣]{2,}'
        words = re.findall(pattern, text)
        
        stopwords = {'것이다', '있다', '없다', '하다', '되다', '이다', '그', '저', '이', 
                     '그것', '저것', '이것', '때문', '그래서', '하지만', '그러나'}
        keywords = [w for w in words if w not in stopwords and len(w) >= 2]
        
        return keywords[:max_keywords]
    
    def _format_prev_manuscripts(self, prev_manuscripts: List[dict]) -> str:
        """이전 원고들을 LLM용 타임라인 형식으로 변환"""
        lines = []
        
        for ms in prev_manuscripts:
            ep_num = ms.get('ep_num', 0)
            content = ms.get('content', '')
            title = ms.get('title', f'제{ep_num}화')
            
            # 원고 앞뒤 요약 (토큰 절약)
            if len(content) > 1500:
                excerpt = content[:700] + "\n...(중략)...\n" + content[-500:]
            else:
                excerpt = content
            
            lines.append(f"### 제 {ep_num}화: {title}")
            lines.append(excerpt)
            lines.append("")
        
        return "\n".join(lines)
    
    def inspect_manuscript(self, current_ep: int, manuscript: str,
                           blueprint: dict, prev_manuscripts: List[dict],
                           hud_history: List[dict] = None) -> dict:
        """
        [V49.1] 원고 연속성 검증 실행
        
        Args:
            current_ep: 현재 에피소드 번호
            manuscript: Writer가 생성한 원고 텍스트
            blueprint: 현재 에피소드 Blueprint dict
            prev_manuscripts: 이전 원고 리스트 [{ep_num, content, title}, ...]
            hud_history: HUD 스냅샷 히스토리 (선택적)
        
        Returns:
            {
                "decision": "PASS" | "REJECT",
                "severity": "NONE" | "MINOR" | "MAJOR" | "CRITICAL",
                "continuity_analysis": {...},
                "blueprint_alignment": {...},
                "violations": [...],
                "warnings": [...],
                "fix_instructions": "..."
            }
        """
        # 1화는 이전 원고가 없으므로 Blueprint 준수만 체크
        if current_ep <= 1 or not prev_manuscripts:
            return self._check_blueprint_only(current_ep, manuscript, blueprint)
        
        # 원고가 비어있으면 REJECT
        if not manuscript or len(manuscript.strip()) < 500:
            return {
                "decision": "REJECT",
                "severity": "CRITICAL",
                "continuity_analysis": {},
                "blueprint_alignment": {},
                "violations": [{
                    "type": "empty_manuscript",
                    "severity": "CRITICAL",
                    "description": "원고가 비어있거나 너무 짧습니다."
                }],
                "warnings": [],
                "fix_instructions": "최소 500자 이상의 원고를 생성하십시오."
            }
        
        # ═══════════════════════════════════════════════════════════════
        # Phase 1: Python 기반 사전 필터링 (빠른 검증)
        # ═══════════════════════════════════════════════════════════════
        python_check = self._manuscript_python_precheck(
            current_ep, manuscript, prev_manuscripts, blueprint
        )
        
        # 명백한 위반이 감지되면 LLM 호출 없이 즉시 REJECT
        if python_check['critical_violations']:
            return {
                "decision": "REJECT",
                "severity": "CRITICAL",
                "continuity_analysis": python_check.get('timeline', {}),
                "blueprint_alignment": {},
                "violations": python_check['critical_violations'],
                "warnings": python_check.get('warnings', []),
                "fix_instructions": self._generate_manuscript_fix_instructions(
                    python_check['critical_violations']
                )
            }
        
        # ═══════════════════════════════════════════════════════════════
        # Phase 2: LLM 기반 정밀 검증 (미묘한 모순 탐지)
        # ═══════════════════════════════════════════════════════════════
        
        # 이전 원고 요약 생성
        prev_timeline = self._format_prev_manuscripts(prev_manuscripts)
        
        # Blueprint 시나리오 추출
        blueprint_scenario = blueprint.get('integrated_scenario', '')
        if not blueprint_scenario:
            blueprint_scenario = str(blueprint.get('scene_breakdown', {}))
        
        # 원고 발췌 (토큰 제한)
        manuscript_excerpt = manuscript[:4000] if len(manuscript) > 4000 else manuscript
        
        # 프롬프트 조립
        prompt = MANUSCRIPT_CONTINUITY_PROMPT.format(
            current_ep=current_ep,
            manuscript_excerpt=self._escape_braces(manuscript_excerpt),
            prev_count=len(prev_manuscripts),
            prev_manuscripts_timeline=self._escape_braces(prev_timeline[:6000]),
            blueprint_scenario=self._escape_braces(blueprint_scenario[:2000])
        )
        
        try:
            response = self.ask(prompt, temperature=0.1)
            result = self._extract_json_robust(response)
            
            # 결과 검증 및 보완
            if not isinstance(result, dict):
                result = {
                    "decision": "PASS", 
                    "severity": "NONE", 
                    "continuity_analysis": {},
                    "blueprint_alignment": {},
                    "violations": [], 
                    "warnings": []
                }
            
            # Python 검증 결과 병합
            if python_check.get('warnings'):
                result.setdefault('warnings', [])
                result['warnings'].extend(python_check['warnings'])
            
            return result
            
        except Exception as e:
            print(f"      🚨 [ContinuityInspector] 원고 LLM 검증 실패: {e}")
            # LLM 실패 시 Python 검증 결과만 반환
            if python_check.get('warnings'):
                return {
                    "decision": "PASS",
                    "severity": "MINOR",
                    "continuity_analysis": python_check.get('timeline', {}),
                    "blueprint_alignment": {},
                    "violations": [],
                    "warnings": python_check['warnings'],
                    "fix_instructions": "LLM 검증 실패 - Python 사전 검증만 수행됨"
                }
            return {
                "decision": "PASS",
                "severity": "NONE",
                "continuity_analysis": {},
                "blueprint_alignment": {},
                "violations": [],
                "warnings": ["LLM 검증 실패 - 수동 확인 권장"],
                "fix_instructions": ""
            }
    
    def _check_blueprint_only(self, current_ep: int, manuscript: str, blueprint: dict) -> dict:
        """
        1화 또는 이전 원고 없을 때 Blueprint 준수만 체크
        """
        scene_breakdown = blueprint.get('scene_breakdown', {})
        
        if not scene_breakdown:
            return {
                "decision": "PASS",
                "severity": "NONE",
                "continuity_analysis": {},
                "blueprint_alignment": {"note": "Blueprint 없음"},
                "violations": [],
                "warnings": [],
                "fix_instructions": ""
            }
        
        # 핵심 씬 반영 체크
        total_scenes = len(scene_breakdown)
        reflected = 0
        missing = []
        
        for scene_key, scene_desc in scene_breakdown.items():
            keywords = self._extract_keywords(str(scene_desc))
            if any(kw in manuscript for kw in keywords if kw):
                reflected += 1
            else:
                missing.append(scene_key)
        
        severity = "NONE"
        decision = "PASS"
        
        if reflected < total_scenes // 2:
            severity = "MAJOR"
            decision = "REJECT"
        elif missing:
            severity = "MINOR"
        
        return {
            "decision": decision,
            "severity": severity,
            "continuity_analysis": {},
            "blueprint_alignment": {
                "scenes_reflected": reflected,
                "total_scenes": total_scenes,
                "missing_elements": missing
            },
            "violations": [{
                "type": "blueprint_violation",
                "severity": severity,
                "description": f"씬 {total_scenes}개 중 {reflected}개만 반영"
            }] if decision == "REJECT" else [],
            "warnings": [f"누락된 씬: {missing}"] if missing and decision == "PASS" else [],
            "fix_instructions": f"다음 씬을 원고에 반영하세요: {missing}" if missing else ""
        }
    
    def _generate_manuscript_fix_instructions(self, violations: List[dict]) -> str:
        """원고 위반 사항에 대한 수정 지시 생성"""
        instructions = []
        
        for v in violations:
            v_type = v.get('type', '')
            item = v.get('item_or_subject', '')
            
            if v_type == 'unowned_item_usage':
                instructions.append(
                    f"[미획득 아이템 사용 수정] '{item}'은(는) 이전 원고에서 획득한 기록이 없습니다. "
                    f"해당 아이템 사용 장면을 삭제하거나, 이전에 획득한 것으로 설정을 수정하세요."
                )
            elif v_type == 'state_discontinuity':
                instructions.append(
                    f"[상태 불연속 수정] 직전 화 상태가 현재 화에 연속되지 않습니다. "
                    f"캐릭터의 부상/회복 상태를 이전 화와 일관되게 수정하세요."
                )
            elif v_type == 'relationship_reversal':
                instructions.append(
                    f"[관계 역행 수정] NPC와의 관계가 이전 원고와 모순됩니다. "
                    f"관계 변화에 대한 서사적 근거를 추가하거나 반응을 수정하세요."
                )
            elif v_type == 'blueprint_violation':
                instructions.append(
                    f"[Blueprint 미준수] 설계된 핵심 씬이 원고에 반영되지 않았습니다. "
                    f"Blueprint의 scene_breakdown에 명시된 씬들을 원고에 포함시키세요."
                )
        
        return "\n".join(instructions) if instructions else "위반 사항을 확인하고 수정하세요."
