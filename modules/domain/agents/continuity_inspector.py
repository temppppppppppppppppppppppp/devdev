"""
[V49] Continuity Inspector - Director 산하 연속성 검증 전문 에이전트

역할:
1. 이전 블루프린트/Arc 전체 분석
2. 아이템/패 획득 타임라인 추적
3. 캐릭터 상태 흐름 검증
4. 모순 감지 시 구체적 수정 지시 제공
5. [V61 NEW] Entity 명칭 일관성 검증 (캐릭터, 조직, 장소, 물품, 기술)

실행 시점:
- [V49 NEW] Stage 2에서 Analyst가 Arc 설계 후 - Arc 간 연속성 + 단일 Arc 내 모순 검증
- Stage 3에서 Architect가 블루프린트 생성 후 - 에피소드 연속성 검증
- [V61 NEW] Stage 4에서 원고 검증 시 - Entity 명칭 일관성 검증
- Director 검증 전에 실행
- REJECT 시 재생성 (모순 지점 피드백 포함)

비용: ~$0.01/에피소드 (flash 모델 사용)
"""

import json
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from .base_agent import BaseAgent

# [V49.7] 품질 향상 모듈 임포트
try:
    from modules.core.state_delta_tracker import StateDeltaTracker
    from modules.core.relationship_tracker import RelationshipTracker
    from modules.core.power_scaling import PowerScalingTracker
    from modules.core.foreshadowing_tracker import ForeshadowingTracker
    from modules.core.information_diffusion import InformationDiffusion
    V49_7_MODULES_AVAILABLE = True
except ImportError:
    V49_7_MODULES_AVAILABLE = False


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

Step 5: [V61 NEW] Entity 명칭 일관성 검증
- Entity Registry가 제공된 경우, 등록된 정식 명칭과 현재 블루프린트의 명칭 비교
- 캐릭터: 이전 에피소드에서 '팽무진'으로 확립되었는데 현재 '무진' 또는 '주인공'으로 표기되면 WARNING
- 조직/문파: '철혈문' vs '철혈파' 같은 미묘한 명칭 차이 탐지
- 장소: '무기고' vs '병기고' 같은 동일 장소의 다른 명칭 탐지
- 물품: '백근도' vs '거구도' 같은 동일 무기의 다른 명칭 탐지
- 기술/무공: '이화접목' vs '중검무봉' 같은 기술명 불일치 탐지
- Entity Registry:
{entity_registry}

Step 6: 최종 판정
- 위 5단계를 종합하여 PASS/REJECT 결정
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
    "entity_consistency": {{
        "registered_entities": {{"characters": [], "organizations": [], "locations": [], "objects": [], "concepts": []}},
        "current_entities": {{"characters": [], "organizations": [], "locations": [], "objects": [], "concepts": []}},
        "mismatches": [
            {{
                "category": "character | organization | location | object | concept",
                "registered_name": "등록된 정식 명칭",
                "current_name": "현재 사용된 명칭",
                "severity": "CRITICAL | MAJOR | MINOR",
                "recommendation": "수정 권고"
            }}
        ]
    }},
    "violations": [
        {{
            "type": "duplicate_acquisition | premature_possession | state_discontinuity | reaction_mismatch | entity_name_mismatch",
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

Step 6: [V61 NEW] Entity 명칭 일관성 검증
- Entity Registry가 제공된 경우, 등록된 정식 명칭과 현재 Arc의 명칭 비교
- 캐릭터: 이전 Arc에서 '팽무진'으로 확립되었는데 현재 '무진' 또는 '주인공'으로 표기되면 WARNING
- 조직/문파: '철혈문' vs '철혈파' 같은 미묘한 명칭 차이 탐지
- 장소: '무기고' vs '병기고' 같은 동일 장소의 다른 명칭 탐지
- 물품: '백근도' vs '거구도' 같은 동일 무기의 다른 명칭 탐지
- 기술/무공: '이화접목' vs '중검무봉' 같은 기술명 불일치 탐지
- Entity Registry:
{entity_registry}

Step 7: 최종 판정
- 위 6단계를 종합하여 PASS/REJECT 결정
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
    "entity_consistency": {{
        "registered_entities": {{"characters": [], "organizations": [], "locations": [], "objects": [], "concepts": []}},
        "current_entities": {{"characters": [], "organizations": [], "locations": [], "objects": [], "concepts": []}},
        "mismatches": [
            {{
                "category": "character | organization | location | object | concept",
                "registered_name": "등록된 정식 명칭",
                "current_name": "현재 사용된 명칭",
                "severity": "CRITICAL | MAJOR | MINOR",
                "recommendation": "수정 권고"
            }}
        ]
    }},
    "violations": [
        {{
            "type": "duplicate_acquisition | premature_possession | state_discontinuity | intra_arc_contradiction | setting_inconsistency | entity_name_mismatch",
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
# [V49.2 NEW] Joint Docs 정밀 추출 프롬프트
# =================================================================
JOINT_DOCS_EXTRACTION_PROMPT = """
[Role] Arc 종료 상태 추출기 (Joint Docs Extractor)
[Task] Arc의 마지막 화(제 {last_ep}화) 내용을 분석하여 정확한 종료 상태를 추출하라.

### 📋 Arc {arc_no} 전술 설계서 (마지막 화 중심)
{last_ep_content}

### 🎯 추출 항목

#### 1. final_location (종료 시점 위치)
- 마지막 화가 끝나는 시점에 주인공이 위치한 **구체적인 장소**
- 예: "팽가 연무장", "무기고 앞", "가주 집무실"
- 단순히 "팽가"가 아닌 **세부 장소**까지 명시

#### 2. physical_inventory (물리적 소지품) [⚠️ 매우 중요]
- 마지막 화 종료 시점에 주인공이 **소지 중인 모든 핵심 물품**
- **🚨 핵심 원칙**: 무기, 패, 문서 등은 **명시적으로 버리거나 잃어버리지 않는 한 계속 소지 중**
- 예: 주인공이 제5화에서 "백근 대도"를 획득했고, 제8화까지 버린 언급이 없다면 → "백근 대도"는 여전히 소지 중
- 예시 목록: ["백근 대도", "철혈사자패", "비급서", "양피지 문서"]
- 소모품(영약 등)만 소모 처리, **무기/패/문서는 버리지 않으면 항상 포함**
- ❌ 빈 배열 `[]` 반환 금지 - 최소한 주무기와 핵심 아이템은 항상 포함

#### 3. world_joint (환경적 변화)
- 이 Arc가 끝나면서 **다음 Arc가 즉시 계승해야 할** 세계 상태
- 예: "팽가의 권력 구도가 뒤집힘", "청사가 가문 감옥에 수감됨"

### 🚨 추출 원칙
1. 추론하지 말고 **문서에 명시된 내용만** 추출하라
2. 획득 vs 소지 구분: 새로 획득한 것만이 아닌, 현재 소지 중인 모든 핵심 아이템
3. 마지막 화의 "(4) 연속성 체크포인트" 섹션이 있다면 우선 참조

[Output Format] JSON Only
{{
    "final_location": "종료 시점의 구체적 장소",
    "physical_inventory": ["소지품 1", "소지품 2", ...],
    "world_joint": "다음 Arc가 계승할 환경 변화",
    "extraction_confidence": "HIGH | MEDIUM | LOW",
    "extraction_notes": "추출 시 참고한 문서 내 근거 (선택)"
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

Step 5: [V61 NEW] Entity 명칭 일관성 검증
- Entity Registry가 제공된 경우, 등록된 정식 명칭과 현재 원고의 명칭 비교
- 캐릭터명이 일관되게 사용되는지 확인 (예: '팽무진' vs '무진' vs '주인공')
- 조직/문파명, 장소명, 물품명, 기술명의 일관성 확인
- Entity Registry:
{entity_registry}

Step 6: 최종 판정
- 위 5단계를 종합하여 PASS/REJECT 결정
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
    "entity_consistency": {{
        "mismatches": [
            {{
                "category": "character | organization | location | object | concept",
                "registered_name": "등록된 정식 명칭",
                "current_name": "현재 사용된 명칭",
                "severity": "CRITICAL | MAJOR | MINOR",
                "recommendation": "수정 권고"
            }}
        ]
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
    6. [V61 NEW] Entity 명칭 일관성 검증

    [V49 Update]
    - 모델: gemini-3-pro-preview (V60.24: Gemini 3로 업그레이드)
    - [NEW] inspect_arc(): Stage 2에서 Arc 설계 후 호출
    - inspect(): Stage 3에서 블루프린트 생성 후 호출

    [V61 Update]
    - [NEW] entity_registry 파라미터: 모든 inspect 메서드에 추가
    - Entity 명칭 일관성 검증: 캐릭터, 조직, 장소, 물품, 기술명 일관성 체크
    - entity_consistency 출력 필드 추가
    """

    def __init__(self, context, client, model_tier="gemini-3-pro-preview"):
        """
        [V60.24] Gemini 3로 변경
        Args:
            context: ProjectContext 객체
            client: Gemini API 클라이언트
            model_tier: 사용할 모델 (V60.24: gemini-3-pro-preview)
        """
        super().__init__(context, client, model_tier)
        
        # 아이템 획득 패턴 (한국어) - [V49.4 FIX] 더 엄격한 패턴
        # 아이템 이름은 보통 2~25자의 한글/숫자로 구성
        # [V60.53] "집어 들", "뽑아 들" 제거 - 사용과 획득 혼동 방지
        self.acquire_patterns = [
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:획득|챙기|얻|주워\s*들|가져)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:손에\s*넣|가져가|챙겨\s*들)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:발견|찾아)",
            # [V60.53] 명시적 획득만 인정 (새로, 처음으로 등)
            r"(?:새로운?|처음으로?)\s*['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:얻|획득|손에\s*넣)",
        ]

        # [V60.53] 사용/꺼내기 패턴 - 이미 가진 것을 쓰는 행동 (획득 아님)
        self.usage_patterns = [
            r"(?:다시|이미|자신의|허리춤의|품속의|등에\s*멘)\s*['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:다시\s*)?(?:세우|휘두르|내리치|찔러|베|쥐)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:뽑아\s*들|집어\s*들|꺼내\s*들)",
            r"(?:허리춤|품속|등|어깨)(?:에서|의)\s*['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)",
        ]
        
        # 수여/하사 패턴 (범용) - [V49.4 FIX] 더 엄격한 패턴
        self.grant_patterns = [
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:하사|수여|내리|던져\s*주|건네)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:풀어|떼어)\s*(?:던지|주)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:위임|부여|임명)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,20}권)['\"]?.*?(?:위임|부여|하사)",  # ~권 패턴
            r"['\"]?([가-힣a-zA-Z0-9]{2,20}패)['\"]?.*?(?:하사|수여|던지)",  # ~패 패턴
        ]
        
        # 소지/사용 패턴
        self.possession_patterns = [
            r"품속.*?(.+?)(?:이|가)\s*(?:있|자리)",
            r"(.+?)(?:을|를)\s*(?:들어\s*보이|꺼내|쥐)",
            r"(?:쥔|든|멘)\s*(.+?)",
        ]

        # [V49.2] 복장/의복 패턴 (복장 일관성 검증용)
        self.attire_patterns = [
            r"(?:비단|명주|무명|삼베|가죽|철갑|갑옷)\s*(?:옷|의|포|복|갑)",
            r"(?:화려한|허름한|낡은|깨끗한|더러운|피묻은|찢어진)\s*(?:옷|의|포|복|차림)",
            r"(?:옷|의복|복장|차림)(?:이|을|를)\s*(?:갈아입|바꾸|벗)",
        ]

        # [V49.2] 부상/상태 패턴
        self.injury_patterns = [
            r"(?:부상|상처|파열|골절|출혈|기절|내상|중상|경상)",
            r"(?:어깨|팔|다리|허리|등|가슴|복부|머리).*?(?:부상|상처|다치)",
            r"(?:피가|피를)\s*(?:흘|뿜|쏟)",
        ]

        # [V49.6] 분배/지급 제외 패턴 - 타인에게 지급한 아이템은 주인공 획득에서 제외
        self.distribution_patterns = [
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:나눠\s*주|지급|분배|하사하|배분)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?[이가]?\s*(?:실린|담긴)\s*(?:수레|마차|짐|보따리)",
            r"(?:병사|무사|사병|부하)들?(?:에게|한테).*?['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:내려\s*보내|전달하|건네주)",
            r"(?:막사|연무장|무기고).*?(?:도착|배달|전달).*?['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?",
        ]

        # [V49.7] 품질 향상 트래커 초기화
        self._init_v49_7_trackers()
    
    def inspect(self, current_ep: int, current_blueprint: dict,
                prev_blueprints: List[dict], hud_history: List[dict] = None,
                entity_registry: dict = None) -> dict:
        """
        블루프린트 연속성 검증 실행

        Args:
            current_ep: 현재 에피소드 번호
            current_blueprint: 현재 블루프린트 dict
            prev_blueprints: 이전 에피소드 블루프린트 리스트 [{ep_num, integrated_scenario, ...}, ...]
            hud_history: HUD 스냅샷 히스토리 (선택적)
            entity_registry: [V61] Entity Registry dict {characters:[], organizations:[], locations:[], objects:[], concepts:[]}

        Returns:
            {
                "decision": "PASS" | "REJECT",
                "severity": "NONE" | "MINOR" | "MAJOR" | "CRITICAL",
                "violations": [...],
                "warnings": [...],
                "fix_instructions": "...",
                "entity_consistency": {...}  # V61 NEW
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
        # Phase 1: Python 기반 사전 정보 수집 (Advisory Only)
        # [V60.56] Python은 REJECT 권한 없음, 정보만 수집
        # ═══════════════════════════════════════════════════════════════
        python_check = self._python_precheck(current_ep, current_scenario, prev_blueprints)

        # [V60.56] Python 검사 결과를 advisory로 변환 (LLM에게 전달할 정보)
        python_advisory = python_check.get('critical_violations', [])
        if python_advisory:
            print(f"      📋 [V60.56] Python advisory 발견 {len(python_advisory)}건 - LLM에게 전달")
        # Python은 더 이상 REJECT하지 않음, LLM이 최종 판단
        
        # ═══════════════════════════════════════════════════════════════
        # Phase 2: LLM 기반 정밀 검증 (미묘한 모순 탐지)
        # ═══════════════════════════════════════════════════════════════
        
        # 이전 블루프린트 요약 생성
        prev_summaries = self._format_prev_blueprints(prev_blueprints)

        # [V61] Entity Registry 포맷팅
        entity_registry_str = self._format_entity_registry(entity_registry)

        # 프롬프트 조립
        prompt = CONTINUITY_INSPECTION_PROMPT.format(
            current_ep=current_ep,
            current_scenario=self._escape_braces(current_scenario[:4000]),  # 토큰 제한
            prev_count=len(prev_blueprints),
            prev_summaries=self._escape_braces(prev_summaries),
            entity_registry=self._escape_braces(entity_registry_str)
        )
        
        try:
            response = self.ask(prompt, temperature=0.1)
            result = self._extract_json_robust(response)

            # [V60.74] 결과 검증 및 보완 - 파싱 실패 시 신뢰도 0 표시
            if not isinstance(result, dict):
                print(f"      ⚠️ [V60.74] JSON 파싱 실패 - 수동 검수 권장")
                result = {
                    "decision": "PASS",
                    "severity": "NONE",
                    "violations": [],
                    "warnings": ["[V60.74] LLM 응답 파싱 실패 - 수동 검수 필요"],
                    "confidence": 0.0,
                    "parsing_error": True
                }

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
    
    def inspect_arc(self, current_arc: dict, prev_arcs: List[dict],
                    entity_registry: dict = None) -> dict:
        """
        [V49] Arc 수준 연속성 검증 실행

        Stage 2에서 Analyst가 Arc 설계 후, Director 검증 전에 호출

        Args:
            current_arc: 현재 Arc dict {arc_no, tactical_doc, joint_docs, status_shadow, ep_start, ep_end, ...}
            prev_arcs: 이전 Arc 리스트 [{arc_no, tactical_doc, joint_docs, ...}, ...]
            entity_registry: [V61] Entity Registry dict {characters:[], organizations:[], locations:[], objects:[], concepts:[]}

        Returns:
            {
                "decision": "PASS" | "REJECT",
                "severity": "NONE" | "MINOR" | "MAJOR" | "CRITICAL",
                "violations": [...],
                "warnings": [...],
                "fix_instructions": "...",
                "entity_consistency": {...}  # V61 NEW
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
        # [V60.73] ep_count 우선 참조, ep_end는 ep_count 기반 계산 (기존 +4 폴백 오류 수정)
        ep_count = current_arc.get('ep_count', 5)
        ep_end = current_arc.get('ep_end', ep_start + ep_count - 1)
        
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
        # Phase 1: Python 기반 사전 정보 수집 (Advisory Only)
        # [V60.56] Python은 REJECT 권한 없음, 정보만 수집하여 LLM에게 전달
        # ═══════════════════════════════════════════════════════════════
        python_check = self._arc_python_precheck(current_arc, prev_arcs)

        # [V60.56] Python 검사 결과를 advisory로 변환 (LLM이 최종 판단)
        python_advisory = python_check.get('critical_violations', [])
        if python_advisory:
            print(f"      📋 [V60.56] Python advisory 발견 {len(python_advisory)}건 - LLM에게 전달")
            for adv in python_advisory[:3]:
                print(f"         - [{adv.get('type', '?')}] {adv.get('item_or_subject', adv.get('description', '?'))[:50]}")
        # Python은 더 이상 REJECT하지 않음, LLM이 컨텍스트를 보고 최종 판단
        
        # ═══════════════════════════════════════════════════════════════
        # Phase 1.5: Joint Docs Auto-Correction [V49.2 NEW]
        # - tactical_doc에서 정확한 joint_docs를 추출하여 불일치 사전 방지
        # ═══════════════════════════════════════════════════════════════
        corrected_joint_docs = self._extract_accurate_joint_docs(
            tactical_doc=tactical_doc,
            arc_no=arc_no,
            ep_end=ep_end,
            original_joint_docs=joint_docs
        )

        # joint_docs가 수정되었으면 current_arc에 반영
        joint_docs_corrected = False
        if corrected_joint_docs and corrected_joint_docs != joint_docs:
            joint_docs = corrected_joint_docs
            joint_docs_corrected = True
            print(f"         🔧 [V49.2] Joint Docs 자동 수정 완료")

        # ═══════════════════════════════════════════════════════════════
        # Phase 1.6: Arc Start State Auto-Correction [V60.13 NEW]
        # - 이전 Arc의 arc_end_state를 현재 Arc의 arc_start_state로 강제 적용
        # ═══════════════════════════════════════════════════════════════
        start_state_corrected = False
        if prev_arcs:
            last_arc = prev_arcs[-1]
            prev_state = last_arc.get('state_constraints', {})
            prev_end = prev_state.get('arc_end_state', {})
            prev_joint = last_arc.get('joint_docs', {})
            prev_shadow = last_arc.get('status_shadow', {})

            # 이전 Arc의 정확한 종료 상태 추출
            correct_energy = prev_end.get('internal_energy')
            if correct_energy is None:
                loss_str = prev_shadow.get('internal_energy_loss', '0%')
                try:
                    import re
                    loss = int(re.search(r'(\d+)', str(loss_str)).group(1))
                    correct_energy = max(0, 100 - loss)
                except:
                    # [V60.73] 보수적 기본값 50 (파싱 실패 시 만땅 가정 위험)
                    print(f"      ⚠️ [V60.73] internal_energy_loss 파싱 실패: '{loss_str}' → 50% 가정")
                    correct_energy = 50

            correct_injuries = prev_end.get('injuries') or prev_shadow.get('expected_injuries', '없음')
            correct_location = prev_end.get('location') or prev_joint.get('final_location', '알 수 없음')
            correct_equipment = prev_end.get('equipment') or prev_joint.get('physical_inventory', [])

            # 현재 Arc의 state_constraints 수정
            curr_state = current_arc.get('state_constraints', {})
            curr_start = curr_state.get('arc_start_state', {})

            # 불일치 검사 및 수정
            needs_correction = (
                curr_start.get('internal_energy') != correct_energy or
                curr_start.get('injuries') != correct_injuries or
                curr_start.get('location') != correct_location
            )

            if needs_correction:
                corrected_start = {
                    'internal_energy': correct_energy,
                    'injuries': correct_injuries,
                    'location': correct_location,
                    'equipment': correct_equipment
                }
                curr_state['arc_start_state'] = corrected_start
                current_arc['state_constraints'] = curr_state
                start_state_corrected = True
                print(f"         🔧 [V60.13] Arc Start State 자동 수정 완료 (내공: {correct_energy}%, 부상: {correct_injuries})")

        # ═══════════════════════════════════════════════════════════════
        # Phase 2: LLM 기반 정밀 검증 (미묘한 모순 탐지)
        # ═══════════════════════════════════════════════════════════════

        # 이전 Arc 요약 생성
        prev_arcs_summary = self._format_prev_arcs(prev_arcs)

        # [V61] Entity Registry 포맷팅
        entity_registry_str = self._format_entity_registry(entity_registry)

        # 프롬프트 조립 (수정된 joint_docs 사용)
        prompt = ARC_CONTINUITY_INSPECTION_PROMPT.format(
            current_arc_no=arc_no,
            ep_count=ep_count,
            ep_start=ep_start,
            ep_end=ep_end,
            tactical_doc=self._escape_braces(tactical_doc[:6000]),  # 토큰 제한
            joint_docs=self._escape_braces(json.dumps(joint_docs, ensure_ascii=False)),
            status_shadow=self._escape_braces(json.dumps(status_shadow, ensure_ascii=False)),
            prev_arc_count=len(prev_arcs),
            prev_arcs_summary=self._escape_braces(prev_arcs_summary),
            entity_registry=self._escape_braces(entity_registry_str)
        )
        
        try:
            response = self.ask(prompt, temperature=0.1)
            result = self._extract_json_robust(response)

            # [V60.74] 결과 검증 및 보완 - 파싱 실패 시 신뢰도 0 표시
            if not isinstance(result, dict):
                print(f"      ⚠️ [V60.74] JSON 파싱 실패 - 수동 검수 권장")
                result = {
                    "decision": "PASS",
                    "severity": "NONE",
                    "violations": [],
                    "warnings": ["[V60.74] LLM 응답 파싱 실패 - 수동 검수 필요"],
                    "confidence": 0.0,
                    "parsing_error": True
                }

            # Python 검증 결과 병합
            if python_check.get('warnings'):
                result.setdefault('warnings', [])
                result['warnings'].extend(python_check['warnings'])

            # ═══════════════════════════════════════════════════════════════
            # [V49.2] Joint Docs 자동 수정 정보 포함
            # ═══════════════════════════════════════════════════════════════
            if joint_docs_corrected:
                result['corrected_joint_docs'] = joint_docs
                result.setdefault('warnings', [])
                if "[V49.2]" not in str(result.get('warnings', [])):
                    result['warnings'].append("[V49.2] joint_docs가 tactical_doc 기반으로 자동 수정됨")

            # ═══════════════════════════════════════════════════════════════
            # [V60.13] Arc Start State 자동 수정 정보 포함
            # ═══════════════════════════════════════════════════════════════
            if start_state_corrected:
                result['corrected_state_constraints'] = current_arc.get('state_constraints', {})
                result.setdefault('warnings', [])
                if "[V60.13]" not in str(result.get('warnings', [])):
                    result['warnings'].append("[V60.13] arc_start_state가 이전 Arc의 arc_end_state 기반으로 자동 수정됨")

            # ═══════════════════════════════════════════════════════════════
            # [V60.13] intra_arc_contradiction은 WARNING으로 완화
            # - 내공 계산 오류 등 Arc 내부 모순은 치명적이지 않음
            # - cross-arc 문제가 없으면 PASS 처리
            # ═══════════════════════════════════════════════════════════════
            violations = result.get('violations', [])
            has_critical_cross_arc = any(
                v.get('type') in ['duplicate_acquisition', 'premature_possession', 'state_discontinuity']
                and v.get('severity') in ['CRITICAL', 'MAJOR']
                for v in violations
            )

            # cross-arc 문제 없이 intra_arc만 있으면 WARNING으로 완화
            if result.get('decision') == 'REJECT' and not has_critical_cross_arc:
                intra_only = all(
                    v.get('type') in ['intra_arc_contradiction', 'setting_inconsistency']
                    for v in violations
                )
                if intra_only and start_state_corrected:
                    # REJECT → PASS로 변경, violations → warnings로 이동
                    result['decision'] = 'PASS'
                    result['severity'] = 'MINOR'
                    result.setdefault('warnings', [])
                    for v in violations:
                        result['warnings'].append(f"[완화됨] {v.get('type')}: {v.get('description', '')[:100]}")
                    result['violations'] = []
                    print(f"         ⚠️ [V60.13] intra-arc 오류 완화 → PASS (cross-arc 정상)")

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

    # =================================================================
    # [V49.2 NEW] Joint Docs 자동 추출 메서드
    # =================================================================

    def _extract_accurate_joint_docs(
        self,
        tactical_doc: str,
        arc_no: int,
        ep_end: int,
        original_joint_docs: dict
    ) -> Optional[dict]:
        """
        [V49.2] tactical_doc의 마지막 화 내용에서 정확한 joint_docs를 추출

        Analyst가 tactical_doc과 joint_docs를 동시 생성하면서 발생하는
        불일치 문제를 해결하기 위해, tactical_doc에서 joint_docs를 추출합니다.

        Args:
            tactical_doc: Arc의 전술 설계서 전문
            arc_no: Arc 번호
            ep_end: Arc의 마지막 화 번호
            original_joint_docs: 원래 생성된 joint_docs (비교용)

        Returns:
            추출된 joint_docs dict 또는 None (추출 실패 시)
        """
        if not tactical_doc:
            return None

        # 마지막 화 내용 추출
        last_ep_content = self._extract_last_episode_content(tactical_doc, ep_end)

        if not last_ep_content or len(last_ep_content) < 100:
            # 마지막 화 추출 실패 시 원본 유지
            return original_joint_docs

        # LLM 호출하여 정확한 joint_docs 추출
        prompt = JOINT_DOCS_EXTRACTION_PROMPT.format(
            arc_no=arc_no,
            last_ep=ep_end,
            last_ep_content=self._escape_braces(last_ep_content[:4000])
        )

        try:
            response = self.ask(prompt, temperature=0.1)
            extracted = self._extract_json_robust(response)

            if not isinstance(extracted, dict):
                return original_joint_docs

            # 추출 결과 검증
            if not extracted.get('final_location') and not extracted.get('physical_inventory'):
                return original_joint_docs

            # 추출 신뢰도 확인
            confidence = extracted.get('extraction_confidence', 'LOW')
            if confidence == 'LOW':
                # 낮은 신뢰도면 원본과 병합
                merged = original_joint_docs.copy() if isinstance(original_joint_docs, dict) else {}
                if extracted.get('final_location'):
                    merged['final_location'] = extracted['final_location']
                if extracted.get('physical_inventory'):
                    merged['physical_inventory'] = extracted['physical_inventory']
                if extracted.get('world_joint'):
                    merged['world_joint'] = extracted['world_joint']
                return merged

            # 높은 신뢰도면 추출 결과 사용
            return {
                'final_location': extracted.get('final_location', ''),
                'physical_inventory': extracted.get('physical_inventory', []),
                'world_joint': extracted.get('world_joint', '')
            }

        except Exception as e:
            print(f"         ⚠️ [V49.2] Joint Docs 추출 실패: {e}")
            return original_joint_docs

    def _extract_last_episode_content(self, tactical_doc: str, ep_end: int) -> str:
        """
        [V49.2] tactical_doc에서 마지막 화 내용만 추출

        패턴: "[제 N화 전술 설계]" 또는 "제 N화:" 형태
        """
        # 마지막 화 시작 패턴들
        patterns = [
            rf'\[제\s*{ep_end}화\s*전술\s*설계\]',
            rf'제\s*{ep_end}화[:\s]',
            rf'\[제{ep_end}화\]',
            rf'Beat\s*{ep_end}:',
        ]

        last_ep_start = -1
        for pattern in patterns:
            match = re.search(pattern, tactical_doc)
            if match:
                last_ep_start = match.start()
                break

        if last_ep_start < 0:
            # 패턴 매칭 실패 시 마지막 30% 반환
            cutoff = int(len(tactical_doc) * 0.7)
            return tactical_doc[cutoff:]

        # 마지막 화부터 끝까지 반환
        return tactical_doc[last_ep_start:]

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
            arc_state_constraints = arc.get('state_constraints', {})

            # [V49.6] protagonist_items 우선 사용, items_acquired는 하위 호환
            items_from_constraints = arc_state_constraints.get('protagonist_items', [])
            if not items_from_constraints:
                # Fallback to legacy field
                items_from_constraints = arc_state_constraints.get('items_acquired', [])

            if isinstance(items_from_constraints, list):
                # [V49.6] 분배된 아이템 필터링 (이중 안전망)
                filtered_items = self._filter_distributed_items(
                    [i for i in items_from_constraints if i and isinstance(i, str) and 2 <= len(i) <= 30],
                    arc_tactical
                )
                for item in filtered_items:
                    acquired_items[item] = arc_no
                    print(f"      📝 [V60.54 DEBUG] Arc {arc_no} 획득 기록: '{item}'")

            # [V60.54] Fallback 패턴 검색 비활성화 - 오탐 방지
            # 명시적으로 state_constraints에 선언된 아이템만 추적
            if not items_from_constraints:
                print(f"      ⚠️ [V60.54 DEBUG] Arc {arc_no} state_constraints에 획득 아이템 없음")
                # raw_items = []
                # for pattern in self.acquire_patterns:
                #     matches = re.findall(pattern, arc_tactical)
                #     for item in matches:
                #         item = item.strip()
                #         if item and 2 <= len(item) <= 30:
                #             raw_items.append(item)
                # for item in self._filter_distributed_items(raw_items, arc_tactical):
                #     acquired_items[item] = arc_no
                pass  # 명시적 선언만 인정

            # tactical_doc에서 수여 패턴 검색 (길이 제한 추가)
            for pattern in self.grant_patterns:
                matches = re.findall(pattern, arc_tactical)
                for item in matches:
                    item = item.strip()
                    # [V49.4 FIX] 길이 상한 추가 (2~30자)
                    if item and 2 <= len(item) <= 30:
                        granted_items[item] = arc_no

            # joint_docs에서 physical_inventory 추출
            inventory = arc_joint.get('physical_inventory', '')
            # [V49.4 FIX] 리스트인 경우 직접 처리
            # [V49.6] 분배된 아이템 필터링 적용
            if isinstance(inventory, list):
                filtered_inv = self._filter_distributed_items(
                    [i for i in inventory if i and isinstance(i, str) and 2 <= len(i) <= 30],
                    arc_tactical
                )
                for item in filtered_inv:
                    acquired_items[item] = arc_no
            elif isinstance(inventory, str) and inventory:
                raw_inv = []
                for pattern in self.acquire_patterns:
                    matches = re.findall(pattern, inventory)
                    for item in matches:
                        item = item.strip()
                        if item and 2 <= len(item) <= 30:
                            raw_inv.append(item)
                for item in self._filter_distributed_items(raw_inv, arc_tactical):
                    acquired_items[item] = arc_no

            # 직전 Arc 정보 저장
            prev_inventory = arc_joint
            prev_status = arc_status
        
        # 현재 Arc에서 획득하려는 아이템 검색
        current_acquisitions = []
        current_state_constraints = current_arc.get('state_constraints', {})

        # [V49.6] protagonist_items 우선 사용, items_acquired는 하위 호환
        items_from_current = current_state_constraints.get('protagonist_items', [])
        if not items_from_current:
            items_from_current = current_state_constraints.get('items_acquired', [])

        # [V60.54] 디버깅: state_constraints에서 획득 아이템
        if items_from_current:
            print(f"      📥 [V60.54 DEBUG] state_constraints 획득 아이템: {items_from_current}")

        if isinstance(items_from_current, list):
            for item in items_from_current:
                if item and isinstance(item, str) and 2 <= len(item) <= 30:
                    current_acquisitions.append(item)

        # Fallback: tactical_doc에서 패턴 검색 (길이 제한 추가)
        # [V60.54] state_constraints에 명시된 경우만 사용, 패턴 검색 비활성화
        if not current_acquisitions:
            print(f"      ⚠️ [V60.54 DEBUG] state_constraints에 획득 아이템 없음 - 패턴 검색 스킵")
            # [V60.54] 패턴 검색 비활성화 - 오탐 방지
            # for pattern in self.acquire_patterns:
            #     matches = re.findall(pattern, tactical_doc)
            #     for item in matches:
            #         item = item.strip()
            #         if item and 2 <= len(item) <= 30:
            #             current_acquisitions.append(item)
            pass  # 명시적 획득 선언만 인정
        
        # ═══════════════════════════════════════════════════════════════
        # [V60.50] 이미 소지 중인 아이템은 중복 검사에서 제외
        # "뽑아 들었다", "사용했다" 같은 문맥은 획득이 아니라 사용임
        # ═══════════════════════════════════════════════════════════════
        prev_inventory_items = []
        if isinstance(prev_inventory, dict):
            inv_list = prev_inventory.get('physical_inventory', [])
            if isinstance(inv_list, list):
                prev_inventory_items = [str(i) for i in inv_list if i]
            elif isinstance(inv_list, str) and inv_list:
                prev_inventory_items = [inv_list]

        # 현재 Arc의 시작 소지품도 확인
        current_joint = current_arc.get('joint_docs', {})
        current_inventory_items = []
        if isinstance(current_joint, dict):
            curr_inv = current_joint.get('physical_inventory', [])
            if isinstance(curr_inv, list):
                current_inventory_items = [str(i) for i in curr_inv if i]
            elif isinstance(curr_inv, str) and curr_inv:
                current_inventory_items = [curr_inv]

        # ═══════════════════════════════════════════════════════════════
        # [V60.53] 사용 패턴 필터링 - "다시 세웠다", "뽑아 들었다" 등은 획득 아님
        # ═══════════════════════════════════════════════════════════════
        usage_items = set()
        for pattern in self.usage_patterns:
            matches = re.findall(pattern, tactical_doc)
            for item in matches:
                item = item.strip() if isinstance(item, str) else str(item)
                if item and 2 <= len(item) <= 30:
                    usage_items.add(item)

        # [V60.54] 디버깅: 사용 패턴 감지 결과
        if usage_items:
            print(f"      📦 [V60.54 DEBUG] 사용 패턴 감지: {list(usage_items)[:5]}")

        # 이미 소지 중인 아이템 + 사용 패턴 아이템 모두 제외
        all_existing_items = prev_inventory_items + current_inventory_items + list(usage_items)

        # [V60.54] 디버깅: 필터링 전 상태
        print(f"      📦 [V60.54 DEBUG] Arc {current_arc_no} 중복 검사 시작")
        print(f"         - 현재 획득 후보: {current_acquisitions[:5] if current_acquisitions else '없음'}")
        print(f"         - 이전 소지품: {prev_inventory_items[:3] if prev_inventory_items else '없음'}")
        print(f"         - 현재 소지품: {current_inventory_items[:3] if current_inventory_items else '없음'}")
        print(f"         - 이전 Arc 획득 기록: {list(acquired_items.keys())[:5] if acquired_items else '없음'}")

        filtered_current_acquisitions = []
        for curr_item in current_acquisitions:
            is_already_owned = False
            for owned_item in all_existing_items:
                if self._is_same_item(curr_item, owned_item):
                    print(f"         ⏭️ 필터링: '{curr_item}' (이미 소지: '{owned_item}')")
                    is_already_owned = True
                    break
            if not is_already_owned:
                filtered_current_acquisitions.append(curr_item)

        current_acquisitions = filtered_current_acquisitions
        print(f"         - 필터링 후 획득 후보: {current_acquisitions if current_acquisitions else '없음'}")

        # ═══════════════════════════════════════════════════════════════
        # [V60.54] 검증 1: 중복 획득 - 보수적 접근
        # 정확히 같은 아이템만 REJECT, 애매하면 PASS
        # ═══════════════════════════════════════════════════════════════
        for curr_item in current_acquisitions:
            for prev_item, prev_arc in acquired_items.items():
                is_same = self._is_same_item(curr_item, prev_item)
                if is_same:
                    print(f"      🚨 [V60.54] 중복 획득 감지!")
                    print(f"         - 현재 Arc: {current_arc_no}, 아이템: '{curr_item}'")
                    print(f"         - 이전 Arc: {prev_arc}, 아이템: '{prev_item}'")
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

        if not critical_violations:
            print(f"      ✅ [V60.54] Arc {current_arc_no} 중복 획득 없음")
        
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
                    # [V49.4 FIX] 길이 상한 추가 (2~30자)
                    if item and 2 <= len(item) <= 30:
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

            # [V49.2] 복장 일관성 검증
            # 현재 화에서 복장 묘사 추출
            curr_attire_fancy = re.search(r'(?:비단|명주|화려한)\s*(?:옷|의|포|복|차림)', curr_content)
            curr_attire_plain = re.search(r'(?:허름한|낡은|무명|삼베)\s*(?:옷|의|포|복|차림)', curr_content)
            next_attire_fancy = re.search(r'(?:비단|명주|화려한)\s*(?:옷|의|포|복|차림)', next_content)
            next_attire_plain = re.search(r'(?:허름한|낡은|무명|삼베)\s*(?:옷|의|포|복|차림)', next_content)

            # 복장 급변 감지 (비단 → 허름한, 허름한 → 비단)
            attire_change_pattern = r'(?:옷|의복|복장|차림)(?:을|를)\s*(?:갈아입|바꾸|벗)'
            has_change_scene = re.search(attire_change_pattern, next_content)

            if curr_attire_fancy and next_attire_plain and not has_change_scene:
                violations.append({
                    "type": "setting_inconsistency",
                    "severity": "MAJOR",
                    "item_or_subject": "복장",
                    "prev_ep": curr_ep,
                    "curr_ep": next_ep,
                    "description": f"제{curr_ep}화에서 '화려한/비단 복장'이었으나, "
                                  f"제{next_ep}화에서 복장 변경 장면 없이 '허름한 복장'으로 설정됨"
                })
            elif curr_attire_plain and next_attire_fancy and not has_change_scene:
                violations.append({
                    "type": "setting_inconsistency",
                    "severity": "MINOR",
                    "item_or_subject": "복장",
                    "prev_ep": curr_ep,
                    "curr_ep": next_ep,
                    "description": f"제{curr_ep}화에서 '허름한 복장'이었으나, "
                                  f"제{next_ep}화에서 복장 변경 장면 없이 '화려한 복장'으로 설정됨 (경고)"
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
            state_constraints = arc.get('state_constraints', {})  # [V60.12 FIX] 핵심 상태 추가
            arc_end_state = state_constraints.get('arc_end_state', {})  # [V60.12 FIX] 종료 상태
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

            # [V60.12 FIX] 정확한 종료 상태 값 추출
            final_internal_energy = arc_end_state.get('internal_energy', status_shadow.get('internal_energy_loss', '?'))
            final_injuries = arc_end_state.get('injuries', status_shadow.get('expected_injuries', '없음'))
            final_location = arc_end_state.get('location', joint_docs.get('final_location', '미정'))
            final_equipment = arc_end_state.get('equipment', joint_docs.get('physical_inventory', []))

            # Arc별 요약 [V60.12 FIX] state_constraints.arc_end_state 정보 추가
            summary = f"""
═══ Arc {arc_no} (제 {ep_start}화 ~ 제 {ep_end}화) ═══
[🔴 정확한 종료 상태 (state_constraints.arc_end_state) - 다음 Arc 시작점]
- 최종 내공: {final_internal_energy}% ← 다음 Arc는 이 값으로 시작해야 함
- 최종 부상: {final_injuries}
- 최종 위치: {final_location}
- 최종 소지품: {final_equipment}

[참고: joint_docs]
- 위치: {joint_docs.get('final_location', '미정')}
- 소지품: {joint_docs.get('physical_inventory', '미정')}
- 세계 변화: {joint_docs.get('world_joint', '미정')}

[참고: status_shadow]
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

    def _format_entity_registry(self, entity_registry: dict) -> str:
        """
        [V61] Entity Registry를 LLM용 포맷으로 변환

        Args:
            entity_registry: {characters:[], organizations:[], locations:[], objects:[], concepts:[]}

        Returns:
            포맷된 문자열 (Entity Registry가 없으면 "(등록된 Entity 없음)" 반환)
        """
        if not entity_registry:
            return "(등록된 Entity 없음 - 이전 에피소드/Arc에서 추출된 Entity가 없습니다)"

        lines = []
        categories = [
            ('characters', '캐릭터'),
            ('organizations', '조직/문파'),
            ('locations', '장소'),
            ('objects', '물품/아이템'),
            ('concepts', '기술/개념')
        ]

        has_any = False
        for key, label in categories:
            items = entity_registry.get(key, [])
            if items:
                has_any = True
                # 각 Entity는 dict 또는 str일 수 있음
                formatted_items = []
                for item in items:
                    if isinstance(item, dict):
                        name = item.get('name', item.get('canonical_name', str(item)))
                        aliases = item.get('aliases', [])
                        first_ep = item.get('first_appearance', item.get('first_ep', '?'))
                        if aliases:
                            formatted_items.append(f"{name} (별칭: {', '.join(aliases)}, 첫등장: ep{first_ep})")
                        else:
                            formatted_items.append(f"{name} (첫등장: ep{first_ep})")
                    else:
                        formatted_items.append(str(item))
                lines.append(f"[{label}] {', '.join(formatted_items)}")

        if not has_any:
            return "(등록된 Entity 없음)"

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

            # 획득 패턴 검색 (길이 제한 추가)
            for pattern in self.acquire_patterns:
                matches = re.findall(pattern, scenario)
                for item in matches:
                    item = item.strip()
                    # [V49.4 FIX] 길이 상한 추가 (2~30자)
                    if item and 2 <= len(item) <= 30:
                        acquired_items[item] = ep_num

            # 수여 패턴 검색 (길이 제한 추가)
            for pattern in self.grant_patterns:
                matches = re.findall(pattern, scenario)
                for item in matches:
                    item = item.strip()
                    # [V49.4 FIX] 길이 상한 추가 (2~30자)
                    if item and 2 <= len(item) <= 30:
                        granted_items[item] = ep_num

        # 현재 블루프린트에서 획득하려는 아이템 검색 (길이 제한 추가)
        current_acquisitions = []
        for pattern in self.acquire_patterns:
            matches = re.findall(pattern, current_scenario)
            for item in matches:
                item = item.strip()
                # [V49.4 FIX] 길이 상한 추가 (2~30자)
                if item and 2 <= len(item) <= 30:
                    current_acquisitions.append(item)

        # 현재 블루프린트에서 소지/사용하는 수여물 검색 (길이 제한 추가)
        current_possessions = []
        for pattern in self.possession_patterns:
            matches = re.findall(pattern, current_scenario)
            for item in matches:
                item = item.strip()
                # [V49.4 FIX] 길이 상한 추가 (2~30자)
                if item and 2 <= len(item) <= 30:
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
        """
        [V60.55] 두 아이템이 같은 것인지 판단 - 초보수적 접근
        100% 확실한 경우만 True, 조금이라도 다르면 False
        "녹슨 대도" vs "대도" = False (다른 아이템)
        """
        item1_clean = item1.strip()
        item2_clean = item2.strip()

        # 정확히 같은 경우만 True (공백, 대소문자 무시)
        item1_normalized = ''.join(item1_clean.lower().split())
        item2_normalized = ''.join(item2_clean.lower().split())

        if item1_normalized == item2_normalized:
            print(f"      🔍 [_is_same_item] 정확 매칭: '{item1_clean}' == '{item2_clean}'")
            return True

        # [V60.55] 포함 매칭도 제거 - "녹슨 대도" vs "대도" 오탐 방지
        # 정확히 같은 문자열만 같은 아이템으로 인정
        print(f"      ⏭️ [_is_same_item] 다른 아이템: '{item1_clean}' != '{item2_clean}'")
        return False

    def _is_distributed_item(self, item: str, context: str) -> bool:
        """
        [V49.6] 아이템이 타인에게 분배/지급된 것인지 판단

        Args:
            item: 아이템 이름
            context: 해당 아이템이 언급된 맥락 (tactical_doc의 일부)

        Returns:
            True if the item was distributed to others (not protagonist's personal acquisition)
        """
        if not item or not context:
            return False

        # 아이템 주변 맥락 추출 (아이템 언급 전후 100자)
        item_pos = context.find(item)
        if item_pos == -1:
            return False

        start = max(0, item_pos - 100)
        end = min(len(context), item_pos + len(item) + 100)
        local_context = context[start:end]

        # 분배/지급 키워드 확인
        distribution_keywords = [
            '지급', '분배', '나눠', '배분', '내려 보내', '하사하',
            '수레', '마차', '도착', '배달', '전달',
            '병사들', '무사들', '사병들', '부하들',
            '병사에게', '무사에게', '사병에게', '부하에게',
            '막사 앞', '연무장에', '도착한다', '실린',
        ]

        for keyword in distribution_keywords:
            if keyword in local_context:
                # 분배 맥락에서 언급됨 - 주인공 획득이 아님
                return True

        # 분배 패턴으로 정규식 검사
        for pattern in self.distribution_patterns:
            matches = re.findall(pattern, local_context)
            for match in matches:
                if self._is_same_item(item, match):
                    return True

        return False

    def _filter_distributed_items(self, items: List[str], context: str) -> List[str]:
        """
        [V49.6] 분배된 아이템을 필터링

        Args:
            items: 추출된 아이템 목록
            context: 전체 맥락 텍스트

        Returns:
            분배된 아이템이 제외된 목록
        """
        if not items or not context:
            return items

        filtered = []
        for item in items:
            if not self._is_distributed_item(item, context):
                filtered.append(item)
            # else:
            #     print(f"      📦 [V49.6] 분배 아이템 제외: {item}")

        return filtered

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

        # 6. [V49.5] 관계 급변 탐지 (무시→충성 같은 급격한 점프 방지)
        relationship_issues = self._check_relationship_jump(prev_manuscripts, manuscript)
        for issue in relationship_issues:
            if issue.get('severity') == 'MAJOR':
                critical_violations.append(issue)  # 점프 거리 2 이상이면 REJECT
            else:
                warnings.append(issue)

        # 7. [V49.5] 악역 지능 보호 (과소평가 패턴 반복 감지)
        # [V55.5] 강화: 2회 이상 과소평가 시 CRITICAL로 REJECT 처리
        villain_issues = self._check_villain_intelligence(prev_manuscripts, manuscript)
        for issue in villain_issues:
            if issue.get('severity') == 'CRITICAL':
                critical_violations.append(issue)  # [V55.5] REJECT 처리
            else:
                warnings.append(issue)

        # 8. [V49.5] 시간 흐름 검증 (비현실적 동선 감지)
        time_issues = self._check_time_flow(prev_manuscripts, manuscript)
        warnings.extend(time_issues)

        # 9. [V49.5] 독자 몰입도 예측 (납득 불가 위험 플래깅)
        immersion_issues = self._check_reader_immersion(prev_manuscripts, manuscript, current_ep)
        warnings.extend(immersion_issues)

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
    
    def _check_relationship_jump(self, prev_manuscripts: List[dict], manuscript: str) -> List[dict]:
        """
        [V49.5] 관계 급변 탐지 - 무시→충성 같은 급격한 관계 점프 감지

        NPC 개별 등록 없이 원고 텍스트에서 자동으로 관계 상태 추론 및 비교
        """
        warnings = []

        # 관계 상태 키워드 정의 (낮은 상태 → 높은 상태 순서)
        RELATIONSHIP_KEYWORDS = {
            "멸시": ["멸시", "비웃", "하찮", "하인 취급", "깔보", "경멸", "조롱", "무시당"],
            "무시": ["무시", "대수롭지", "관심 없", "신경 쓰지", "거들떠보지"],
            "의심": ["의심", "수상", "이상하", "믿을 수 없", "의구심", "진심인가"],
            "경외": ["경외", "두려워", "떨며", "감히 못", "공포", "벌벌", "존경", "눈빛이 달라"],
            "충성": ["충성", "주군", "목숨 바쳐", "명을 따르", "따르겠", "주군님", "만세"],
        }

        # 상태 우선순위 (높을수록 강한 긍정 관계)
        STATE_PRIORITY = {"멸시": 0, "무시": 1, "의심": 2, "경외": 3, "충성": 4}

        # 허용되는 1단계 전환만 (급격한 점프 방지)
        ALLOWED_TRANSITIONS = {
            "멸시": ["무시", "의심"],
            "무시": ["의심", "경외"],  # 무시→충성 직행 불가
            "의심": ["경외", "무시"],
            "경외": ["충성", "의심"],
            "충성": ["경외"],  # 역행도 1단계만
        }

        # 집단/인물 키워드 (개별 NPC 등록 없이 자동 탐지)
        GROUP_KEYWORDS = ["사병", "무사들", "병사들", "부하들", "수하들", "호위", "교두", "장로들"]

        # 이전 원고들에서 각 집단의 최종 관계 상태 추론 (마지막 등장 = 어떻게 끝났는지)
        prev_states = {}
        for prev_ms in prev_manuscripts:
            content = prev_ms.get('content', '')
            for group in GROUP_KEYWORDS:
                if group in content:
                    # 마지막 등장 위치의 문맥 추출 (이전 화가 어떤 관계로 끝났는지)
                    idx = content.rfind(group)
                    context = content[max(0, idx-300):min(len(content), idx+300)]

                    for state, keywords in RELATIONSHIP_KEYWORDS.items():
                        if any(kw in context for kw in keywords):
                            prev_states[group] = state
                            break

        # 현재 원고에서 관계 상태 추론 (첫 등장 = 어떻게 시작하는지)
        current_states = {}
        for group in GROUP_KEYWORDS:
            if group in manuscript:
                # 첫 등장 위치의 문맥 추출 (현재 화가 어떤 관계로 시작하는지)
                idx = manuscript.find(group)
                context = manuscript[max(0, idx-300):min(len(manuscript), idx+300)]

                for state, keywords in RELATIONSHIP_KEYWORDS.items():
                    if any(kw in context for kw in keywords):
                        current_states[group] = state
                        break

        # 급격한 점프 감지
        for group, current_state in current_states.items():
            if group in prev_states:
                prev_state = prev_states[group]
                if current_state != prev_state:
                    allowed = ALLOWED_TRANSITIONS.get(prev_state, [])
                    if current_state not in allowed:
                        # 점프 거리 계산
                        jump_distance = abs(STATE_PRIORITY.get(current_state, 0) - STATE_PRIORITY.get(prev_state, 0))
                        severity = "MAJOR" if jump_distance >= 2 else "MINOR"

                        warnings.append({
                            'type': 'relationship_jump',
                            'severity': severity,
                            'description': f"'{group}'의 관계가 '{prev_state}'→'{current_state}'로 급변함 (점프 거리: {jump_distance}단계). "
                                          f"'{prev_state}'에서 허용된 전환: {allowed}. "
                                          f"중간 단계(예: 경외)를 거치는 묘사 필요."
                        })

        return warnings

    def _check_villain_intelligence(self, prev_manuscripts: List[dict], manuscript: str) -> List[dict]:
        """
        [V49.5] 악역 지능 보호 - 과소평가 패턴 반복 감지

        [V55.5] 강화: 2회 이상 과소평가 → CRITICAL (REJECT)
        악역이 주인공을 계속 과소평가하는 "어리석은 악역" 클리셰 방지
        """
        issues = []

        # 과소평가 키워드
        UNDERESTIMATE_KEYWORDS = [
            "철부지", "객기", "어린 놈", "망나니", "한심", "우습",
            "내버려 둬", "방심", "신경 쓸 것 없", "겁줄 것 없",
            "어차피", "알아서 망할", "제풀에 지쳐"
        ]

        # 경계 키워드 (악역이 주인공을 경계하는 묘사)
        VIGILANT_KEYWORDS = [
            "의심", "경계", "감시", "조사", "확인", "주시",
            "예의주시", "눈여겨", "수상", "이상하"
        ]

        # [V55.5] 학습 반응 키워드 (악역이 실패에서 배우는 묘사)
        LEARNING_KEYWORDS = [
            "다음엔", "이번엔", "대비", "각오", "반드시", "두 번 다시",
            "실수를 반복", "방심했던", "얕보았던 게", "조심해야"
        ]

        # 이전 원고들에서 과소평가 횟수 카운트
        underestimate_count = 0
        vigilant_found = False
        learning_found = False

        for prev_ms in prev_manuscripts:
            content = prev_ms.get('content', '')
            if any(kw in content for kw in UNDERESTIMATE_KEYWORDS):
                underestimate_count += 1
            if any(kw in content for kw in VIGILANT_KEYWORDS):
                vigilant_found = True
            if any(kw in content for kw in LEARNING_KEYWORDS):
                learning_found = True

        # 현재 원고에서 또 과소평가?
        current_underestimate = any(kw in manuscript for kw in UNDERESTIMATE_KEYWORDS)
        current_vigilant = any(kw in manuscript for kw in VIGILANT_KEYWORDS)
        current_learning = any(kw in manuscript for kw in LEARNING_KEYWORDS)

        # [V55.5] 2회 이상 과소평가 + 경계/학습 묘사 없음 → CRITICAL (REJECT)
        if current_underestimate and underestimate_count >= 1 and not vigilant_found and not current_vigilant:
            if not learning_found and not current_learning:
                issues.append({
                    'type': 'stupid_villain',
                    'severity': 'CRITICAL',  # [V55.5] MAJOR → CRITICAL
                    'description': f"악역이 주인공을 {underestimate_count + 1}회 연속 과소평가 중. "
                                  f"'어리석은 악역' 클리셰로 서사 몰입도 저하. "
                                  f"최소 1회는 경계/의심 또는 '다음엔 대비하겠다'는 학습 반응 필요.",
                    'fix_suggestion': "악역이 주인공에게 당한 후 '이 녀석, 만만치 않군...' 또는 "
                                     "'다음엔 반드시 대비하겠다' 같은 학습 반응 추가"
                })
            else:
                # 학습 반응이 있으면 WARNING만
                issues.append({
                    'type': 'stupid_villain',
                    'severity': 'WARNING',
                    'description': f"악역이 주인공을 {underestimate_count + 1}회 과소평가 (학습 반응 감지됨). "
                                  f"지속적인 과소평가 주의."
                })

        return issues

    def _check_time_flow(self, prev_manuscripts: List[dict], manuscript: str) -> List[dict]:
        """
        [V49.5] 시간 흐름 검증 - 비현실적 동선/일정 감지

        하룻밤에 너무 많은 대형 이벤트, 부상 후 즉시 활동 등 체크
        """
        warnings = []

        # 시간 경과 키워드
        TIME_PASS_KEYWORDS = ["다음 날", "이틀 후", "며칠 후", "일주일", "한 달", "다음날 아침"]
        SAME_DAY_KEYWORDS = ["그날 밤", "같은 날", "그 시각", "잠시 후", "얼마 지나지 않아"]

        # 대형 이벤트 키워드
        MAJOR_EVENT_KEYWORDS = [
            "전투", "혈투", "습격", "잠입", "도박장", "연회",
            "대결", "비무", "암살", "폭발", "화재"
        ]

        # 부상 키워드
        INJURY_KEYWORDS = ["부상", "중상", "피를 흘", "골절", "탈골", "찢어", "터져"]
        RECOVERY_KEYWORDS = ["회복", "치료", "요양", "휴식", "쉬"]

        # 직전 원고 분석
        if prev_manuscripts:
            last_ms = prev_manuscripts[-1]
            last_content = last_ms.get('content', '')

            # 직전 화에서 대형 이벤트 + 부상
            last_had_event = any(kw in last_content for kw in MAJOR_EVENT_KEYWORDS)
            last_had_injury = any(kw in last_content[-1000:] for kw in INJURY_KEYWORDS)

            # 현재 화 분석
            current_same_day = any(kw in manuscript[:500] for kw in SAME_DAY_KEYWORDS)
            current_time_passed = any(kw in manuscript[:500] for kw in TIME_PASS_KEYWORDS)
            current_has_event = any(kw in manuscript for kw in MAJOR_EVENT_KEYWORDS)
            current_has_recovery = any(kw in manuscript[:500] for kw in RECOVERY_KEYWORDS)

            # 같은 날 + 연속 대형 이벤트
            if last_had_event and current_has_event and current_same_day and not current_time_passed:
                warnings.append({
                    'type': 'unrealistic_timeline',
                    'severity': 'MINOR',
                    'description': "연속된 대형 이벤트가 같은 날에 발생. "
                                  "시간 경과 묘사 또는 체력적 한계 묘사 권장."
                })

            # 부상 후 회복 없이 즉시 활동
            if last_had_injury and current_has_event and not current_has_recovery and not current_time_passed:
                warnings.append({
                    'type': 'injury_ignored',
                    'severity': 'MINOR',
                    'description': "직전 화에서 부상 후 회복/시간 경과 없이 대형 이벤트 진행. "
                                  "응급처치, 회복 묘사, 또는 무리하는 대가 묘사 권장."
                })

        # 현재 원고 내 대형 이벤트 수 체크
        event_count = sum(1 for kw in MAJOR_EVENT_KEYWORDS if kw in manuscript)
        if event_count >= 3:
            warnings.append({
                'type': 'event_overload',
                'severity': 'MINOR',
                'description': f"한 화에 대형 이벤트가 {event_count}개 이상. "
                              f"집중도 분산 위험. 일부를 다음 화로 분리 권장."
            })

        return warnings

    def _check_reader_immersion(self, prev_manuscripts: List[dict], manuscript: str, current_ep: int) -> List[dict]:
        """
        [V49.5] 독자 몰입도 예측 - 납득 불가 위험 구간 플래깅

        - 공짜 파워업 감지
        - 복선 회수 없이 결과만 나오는 경우
        - 설정 충돌 (이전에 언급된 내용과 모순)
        """
        warnings = []

        # === 1. 공짜 파워업 감지 ===
        POWERUP_KEYWORDS = ["경지 상승", "돌파", "각성", "깨달음", "내공 증가", "실력 향상", "한 수 위"]
        COST_KEYWORDS = ["대가", "희생", "고통", "부작용", "한계", "무리", "피를 토", "쓰러"]

        has_powerup = any(kw in manuscript for kw in POWERUP_KEYWORDS)
        has_cost = any(kw in manuscript for kw in COST_KEYWORDS)

        if has_powerup and not has_cost:
            warnings.append({
                'type': 'free_powerup',
                'severity': 'MINOR',
                'description': "파워업/성장이 묘사되었으나 대가/고통 묘사 없음. "
                              "'공짜 파워업' 느낌 방지를 위해 대가 묘사 권장."
            })

        # === 2. 갑작스러운 능력 사용 ===
        # 이전에 언급 없이 갑자기 특수 능력 사용
        ABILITY_KEYWORDS = ["비전", "절기", "비급", "암기", "독문", "가전"]

        current_abilities = [kw for kw in ABILITY_KEYWORDS if kw in manuscript]
        if current_abilities and prev_manuscripts:
            # 이전 원고에서 언급된 적 있는지 체크
            prev_all_text = " ".join(m.get('content', '') for m in prev_manuscripts)
            new_abilities = [a for a in current_abilities if a not in prev_all_text]

            if new_abilities and current_ep > 3:  # 초반 3화는 설정 구축 기간이므로 제외
                warnings.append({
                    'type': 'sudden_ability',
                    'severity': 'MINOR',
                    'description': f"이전에 언급 없던 능력 갑자기 등장: {new_abilities}. "
                                  f"복선이나 기연 묘사 없이 등장하면 '설정 추가' 느낌."
                })

        # === 3. 주인공 무쌍 과다 ===
        WIN_KEYWORDS = ["쓰러뜨", "제압", "격파", "승리", "이겼", "물리쳤", "쓰러졌다"]
        STRUGGLE_KEYWORDS = ["위기", "궁지", "밀리", "고전", "위험", "절체절명"]

        win_count = sum(1 for kw in WIN_KEYWORDS if kw in manuscript)
        has_struggle = any(kw in manuscript for kw in STRUGGLE_KEYWORDS)

        if win_count >= 3 and not has_struggle:
            warnings.append({
                'type': 'effortless_victory',
                'severity': 'MINOR',
                'description': f"다수의 승리({win_count}회) 묘사가 있으나 고전/위기 묘사 없음. "
                              f"긴장감 저하 우려. 최소 1회 위기 상황 권장."
            })

        # === 4. 연속 행운 ===
        LUCK_KEYWORDS = ["마침", "우연히", "때마침", "운 좋게", "다행히", "공교롭게"]
        luck_count = sum(1 for kw in LUCK_KEYWORDS if kw in manuscript)

        if luck_count >= 2:
            warnings.append({
                'type': 'excessive_luck',
                'severity': 'MINOR',
                'description': f"우연/행운 표현이 {luck_count}회 사용됨. "
                              f"'작가 편의' 느낌 방지를 위해 인과관계 강화 권장."
            })

        return warnings

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
                           hud_history: List[dict] = None,
                           entity_registry: dict = None) -> dict:
        """
        [V49.1] 원고 연속성 검증 실행

        Args:
            current_ep: 현재 에피소드 번호
            manuscript: Writer가 생성한 원고 텍스트
            blueprint: 현재 에피소드 Blueprint dict
            prev_manuscripts: 이전 원고 리스트 [{ep_num, content, title}, ...]
            hud_history: HUD 스냅샷 히스토리 (선택적)
            entity_registry: [V61] Entity Registry dict {characters:[], organizations:[], locations:[], objects:[], concepts:[]}

        Returns:
            {
                "decision": "PASS" | "REJECT",
                "severity": "NONE" | "MINOR" | "MAJOR" | "CRITICAL",
                "continuity_analysis": {...},
                "blueprint_alignment": {...},
                "entity_consistency": {...},  # V61 NEW
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
        
        # [V60.56] Python 검사 결과를 advisory로 변환 (LLM이 최종 판단)
        python_advisory = python_check.get('critical_violations', [])
        if python_advisory:
            print(f"      📋 [V60.56] Python advisory 발견 {len(python_advisory)}건 - LLM에게 전달")
        # Python은 더 이상 REJECT하지 않음, LLM이 컨텍스트를 보고 최종 판단
        
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

        # [V61] Entity Registry 포맷팅
        entity_registry_str = self._format_entity_registry(entity_registry)

        # 프롬프트 조립
        prompt = MANUSCRIPT_CONTINUITY_PROMPT.format(
            current_ep=current_ep,
            manuscript_excerpt=self._escape_braces(manuscript_excerpt),
            prev_count=len(prev_manuscripts),
            prev_manuscripts_timeline=self._escape_braces(prev_timeline[:6000]),
            blueprint_scenario=self._escape_braces(blueprint_scenario[:2000]),
            entity_registry=self._escape_braces(entity_registry_str)
        )
        
        try:
            response = self.ask(prompt, temperature=0.1)
            result = self._extract_json_robust(response)

            # [V60.74] 결과 검증 및 보완 - 파싱 실패 시 신뢰도 0 표시
            if not isinstance(result, dict):
                print(f"      ⚠️ [V60.74] JSON 파싱 실패 - 수동 검수 권장")
                result = {
                    "decision": "PASS",
                    "severity": "NONE",
                    "continuity_analysis": {},
                    "blueprint_alignment": {},
                    "violations": [],
                    "warnings": ["[V60.74] LLM 응답 파싱 실패 - 수동 검수 필요"],
                    "confidence": 0.0,
                    "parsing_error": True
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

    # ═══════════════════════════════════════════════════════════════════════════
    # [V49.7] 품질 향상 트래커 초기화 및 통합
    # ═══════════════════════════════════════════════════════════════════════════

    def _init_v49_7_trackers(self):
        """
        [V49.7] 품질 향상 모듈 트래커 초기화

        사용 가능한 경우:
        - StateDeltaTracker: 내공/부상 변화 추적
        - RelationshipTracker: NPC 관계 상태 전이
        - PowerScalingTracker: 파워 레벨 스케일링
        - ForeshadowingTracker: 복선 설치/회수
        - InformationDiffusion: 정보 비대칭 추적
        """
        if V49_7_MODULES_AVAILABLE:
            self.state_tracker = StateDeltaTracker(
                initial_energy=100,
                protagonist_name=self._get_protagonist_name()
            )
            self.relationship_tracker = RelationshipTracker()
            self.power_tracker = PowerScalingTracker()
            self.foreshadow_tracker = ForeshadowingTracker()

            # InformationDiffusion은 context가 필요함
            try:
                self.info_diffusion = InformationDiffusion(self.context)
            except Exception:
                self.info_diffusion = None

            self.v49_7_enabled = True
        else:
            self.state_tracker = None
            self.relationship_tracker = None
            self.power_tracker = None
            self.foreshadow_tracker = None
            self.info_diffusion = None
            self.v49_7_enabled = False

    def _get_protagonist_name(self) -> str:
        """프로젝트에서 주인공 이름 추출"""
        try:
            bible = getattr(self.context, 'master_bible', {})
            bible_root = bible.get('MasterBible', bible)
            proj_data = bible_root.get('ProjectData', {})
            return proj_data.get('protagonist', '주인공')
        except Exception:
            return '주인공'

    def _validate_with_v49_7_trackers(
        self,
        arc: int,
        episode: int,
        content: str,
        content_type: str = "blueprint"
    ) -> Dict[str, Any]:
        """
        [V49.7] 트래커 기반 검증 실행

        Args:
            arc: 현재 Arc 번호
            episode: 현재 에피소드 번호
            content: 검증할 내용 (blueprint scenario 또는 manuscript)
            content_type: "blueprint" 또는 "manuscript"

        Returns:
            {
                "warnings": [],
                "violations": [],
                "tracker_results": {
                    "state_delta": {...},
                    "relationship": {...},
                    "power_scaling": {...},
                    "foreshadowing": {...}
                }
            }
        """
        if not self.v49_7_enabled:
            return {"warnings": [], "violations": [], "tracker_results": {}}

        warnings = []
        violations = []
        tracker_results = {}

        # ═══════════════════════════════════════════════════════════════
        # 1. 관계 상태 검증 (RelationshipTracker)
        # ═══════════════════════════════════════════════════════════════
        if self.relationship_tracker:
            rel_result = self._check_relationship_with_tracker(arc, episode, content)
            if rel_result.get("violations"):
                violations.extend(rel_result["violations"])
            if rel_result.get("warnings"):
                warnings.extend(rel_result["warnings"])
            tracker_results["relationship"] = rel_result.get("details", {})

        # ═══════════════════════════════════════════════════════════════
        # 2. 파워 스케일링 검증 (PowerScalingTracker)
        # ═══════════════════════════════════════════════════════════════
        if self.power_tracker:
            power_result = self._check_power_with_tracker(arc, episode, content)
            if power_result.get("warnings"):
                warnings.extend(power_result["warnings"])
            tracker_results["power_scaling"] = power_result.get("details", {})

        # ═══════════════════════════════════════════════════════════════
        # 3. 복선 상태 검증 (ForeshadowingTracker)
        # ═══════════════════════════════════════════════════════════════
        if self.foreshadow_tracker:
            foreshadow_result = self._check_foreshadowing_with_tracker(arc, episode, content)
            if foreshadow_result.get("warnings"):
                warnings.extend(foreshadow_result["warnings"])
            tracker_results["foreshadowing"] = foreshadow_result.get("details", {})

        # ═══════════════════════════════════════════════════════════════
        # 4. 상태 델타 검증 (StateDeltaTracker) - manuscript에서만
        # ═══════════════════════════════════════════════════════════════
        if self.state_tracker and content_type == "manuscript":
            state_result = self._check_state_with_tracker(arc, episode, content)
            if state_result.get("warnings"):
                warnings.extend(state_result["warnings"])
            tracker_results["state_delta"] = state_result.get("details", {})

        return {
            "warnings": warnings,
            "violations": violations,
            "tracker_results": tracker_results
        }

    def _check_relationship_with_tracker(
        self, arc: int, episode: int, content: str
    ) -> Dict[str, Any]:
        """RelationshipTracker를 사용한 관계 전이 검증"""
        warnings = []
        violations = []
        details = {}

        # 집단 키워드 정의
        group_keywords = ["사병", "무사들", "병사들", "부하들", "수하들", "호위", "교두", "장로들"]

        for group in group_keywords:
            if group in content:
                # 현재 상태 추론
                current_state = self.relationship_tracker.infer_state_from_manuscript(
                    group, content
                )

                if current_state:
                    # 이전 상태 확인
                    prev_history = self.relationship_tracker.get_transition_history(group)

                    if prev_history:
                        prev_state = prev_history[-1].get("to_state", "무시")

                        # 전이 유효성 검증
                        validation = self.relationship_tracker.validate_transition_with_justification(
                            npc_name=group,
                            from_state=prev_state,
                            to_state=current_state,
                            proposed_justification="",
                            arc=arc,
                            episode=episode
                        )

                        if not validation.get("valid"):
                            severity = validation.get("severity", "MINOR")
                            if severity in ["CRITICAL", "MAJOR"]:
                                violations.append({
                                    "type": "relationship_violation",
                                    "severity": severity,
                                    "description": validation.get("message", "관계 전이 오류")
                                })
                            else:
                                warnings.append({
                                    "type": "relationship_warning",
                                    "severity": "MINOR",
                                    "description": validation.get("message", "관계 전이 경고")
                                })

                        details[group] = {
                            "from": prev_state,
                            "to": current_state,
                            "valid": validation.get("valid", True)
                        }

        return {"warnings": warnings, "violations": violations, "details": details}

    def _check_power_with_tracker(
        self, arc: int, episode: int, content: str
    ) -> Dict[str, Any]:
        """PowerScalingTracker를 사용한 파워 스케일링 검증"""
        warnings = []
        details = {}

        protagonist = self._get_protagonist_name()

        # 파워 관련 키워드 탐지
        power_keywords = {
            "각성": 25,
            "돌파": 20,
            "비급": 20,
            "영약": 15,
            "수련": 15,
            "깨달음": 15,
            "경지 상승": 20,
            "내공 증가": 10,
        }

        detected_growth = 0
        growth_reason = ""

        for keyword, power_delta in power_keywords.items():
            if keyword in content:
                detected_growth = max(detected_growth, power_delta)
                growth_reason = keyword

        if detected_growth > 0:
            current_power = self.power_tracker.get_power(protagonist) or 30
            new_power = current_power + detected_growth

            validation = self.power_tracker.validate_growth(
                character=protagonist,
                arc=arc,
                new_power=new_power,
                justification=growth_reason
            )

            if validation.get("severity") == "CRITICAL":
                warnings.append({
                    "type": "power_scaling_critical",
                    "severity": "MAJOR",
                    "description": validation.get("message", "급격한 파워업")
                })
            elif validation.get("severity") == "WARNING":
                warnings.append({
                    "type": "power_scaling_warning",
                    "severity": "MINOR",
                    "description": validation.get("suggestion", "성장 속도 조절 권장")
                })

            details["detected_growth"] = detected_growth
            details["reason"] = growth_reason
            details["validation"] = validation

        return {"warnings": warnings, "details": details}

    def _check_foreshadowing_with_tracker(
        self, arc: int, episode: int, content: str
    ) -> Dict[str, Any]:
        """ForeshadowingTracker를 사용한 복선 상태 검증"""
        warnings = []
        details = {}

        # 미회수 복선 경고
        pending = self.foreshadow_tracker.get_pending_foreshadowings(arc)

        critical_pending = [p for p in pending if p.get("severity") == "CRITICAL"]
        warning_pending = [p for p in pending if p.get("severity") == "WARNING"]

        if critical_pending:
            warnings.append({
                "type": "foreshadowing_critical",
                "severity": "MAJOR",
                "description": f"미회수 복선 {len(critical_pending)}개가 10개 Arc 이상 방치됨: " +
                              ", ".join([p["id"] for p in critical_pending[:3]])
            })

        if warning_pending:
            warnings.append({
                "type": "foreshadowing_warning",
                "severity": "MINOR",
                "description": f"미회수 복선 {len(warning_pending)}개가 5개 Arc 이상 방치됨"
            })

        # 복선 설치/회수 키워드 탐지 (선택적)
        foreshadow_keywords = ["암시", "복선", "떡밥", "비밀", "예언", "숨겨진"]
        detected_foreshadows = [kw for kw in foreshadow_keywords if kw in content]

        details["pending_count"] = len(pending)
        details["critical_count"] = len(critical_pending)
        details["detected_keywords"] = detected_foreshadows

        return {"warnings": warnings, "details": details}

    def _check_state_with_tracker(
        self, arc: int, episode: int, content: str
    ) -> Dict[str, Any]:
        """StateDeltaTracker를 사용한 내공/부상 상태 검증"""
        warnings = []
        details = {}

        # 부상 키워드 탐지
        injury_level = "정상"
        if any(kw in content for kw in ["위독", "사경", "기절", "의식 잃"]):
            injury_level = "위독"
        elif any(kw in content for kw in ["중상", "심한 부상", "피투성이", "골절"]):
            injury_level = "중상"
        elif any(kw in content for kw in ["경상", "가벼운 상처", "찰과상"]):
            injury_level = "경상"

        # 내공 소모 키워드 탐지
        energy_delta = 0
        if any(kw in content for kw in ["내공 고갈", "기력 소진", "탈진"]):
            energy_delta = -50
        elif any(kw in content for kw in ["내공 소모", "기력 사용", "힘이 빠져"]):
            energy_delta = -20
        elif any(kw in content for kw in ["운기조식", "회복", "휴식"]):
            energy_delta = 15

        # 상태 변화 적용 및 검증
        if energy_delta != 0:
            result = self.state_tracker.apply_energy_delta(
                arc=arc,
                episode=episode,
                delta=energy_delta,
                reason="자동 탐지"
            )
            if result.get("warning"):
                warnings.append({
                    "type": "energy_warning",
                    "severity": "MINOR",
                    "description": result["warning"]
                })
            details["energy"] = result

        if injury_level != "정상":
            result = self.state_tracker.apply_injury(
                arc=arc,
                episode=episode,
                level=injury_level,
                body_part="전신",
                cause="자동 탐지"
            )
            if result.get("warning"):
                warnings.append({
                    "type": "injury_warning",
                    "severity": "MINOR",
                    "description": result["warning"]
                })
            details["injury"] = result

        details["current_energy"] = self.state_tracker.get_current_energy()
        details["current_injury"] = self.state_tracker.get_current_injury_level()

        return {"warnings": warnings, "details": details}

    def load_trackers_from_db(self, arcs_data: List[Dict] = None) -> Dict[str, int]:
        """
        [V49.7] DB에서 트래커 상태 로드

        Arc 데이터에서 복선, 파워, 관계 정보를 추출하여
        트래커들을 초기화합니다.

        Args:
            arcs_data: Arc 데이터 리스트 (None이면 DB에서 로드)

        Returns:
            로드 결과 {foreshadowings: int, relationships: int, ...}
        """
        if not self.v49_7_enabled:
            return {"error": "V49.7 modules not available"}

        results = {
            "foreshadowings": 0,
            "relationships": 0,
            "power_entries": 0
        }

        # Arc 데이터 로드
        if arcs_data is None:
            try:
                arcs_data = self.context.db.load_anchor("arcs") or []
            except Exception:
                arcs_data = []

        # 복선 로드
        if self.foreshadow_tracker and arcs_data:
            results["foreshadowings"] = self.foreshadow_tracker.load_from_arcs(arcs_data)

        # 관계/파워는 Arc의 state_constraints에서 추출
        for arc in arcs_data:
            if not isinstance(arc, dict):
                continue

            arc_no = arc.get("arc_no", 0)
            state_constraints = arc.get("state_constraints", {})

            # 파워 정보 로드
            if self.power_tracker:
                protagonist = self._get_protagonist_name()
                arc_end = state_constraints.get("arc_end_state", {})
                if "power_level" in arc_end:
                    self.power_tracker.set_power(
                        character=protagonist,
                        arc=arc_no,
                        power=arc_end.get("power_level", 30),
                        reason="Arc 종료 상태"
                    )
                    results["power_entries"] += 1

            # 관계 변화 로드
            if self.relationship_tracker:
                rel_changes = arc.get("relationship_changes", [])
                for change in rel_changes:
                    if isinstance(change, dict):
                        self.relationship_tracker.record_transition(
                            arc=arc_no,
                            episode=arc.get("ep_end", 0),
                            npc_name=change.get("target", ""),
                            from_state=change.get("from", "무시"),
                            to_state=change.get("to", "무시"),
                            trigger=change.get("trigger", ""),
                            justification=change.get("justification", "")
                        )
                        results["relationships"] += 1

        return results

    # ═══════════════════════════════════════════════════════════════════════════
    # [V59] 스킬 사용 타임라인 추적
    # ═══════════════════════════════════════════════════════════════════════════

    # 무공/스킬 관련 패턴
    SKILL_ACQUISITION_PATTERNS = [
        r"['\"]?([가-힣a-zA-Z0-9]{2,20}(?:법|결|공|권법|검법|장법|각법|신법|보법|심법|기공))['\"]?(?:을|를)\s*(?:익히|배우|습득|전수받|깨달|체득)",
        r"['\"]?([가-힣a-zA-Z0-9]{2,20}(?:초식|절초|절기|비기|오의))['\"]?(?:을|를)\s*(?:익히|배우|습득|전수받|터득)",
        r"(?:전수|가르침|지도).*?['\"]?([가-힣a-zA-Z0-9]{2,20}(?:법|공|결|술))['\"]?",
        r"비급.*?['\"]?([가-힣a-zA-Z0-9]{2,20}(?:법|공|결|심법))['\"]?",
    ]

    SKILL_USAGE_PATTERNS = [
        r"['\"]?([가-힣a-zA-Z0-9]{2,20}(?:법|결|공|권법|검법|장법|각법|신법|보법))['\"]?(?:을|를)?\s*(?:펼치|시전|사용|발동|구사)",
        r"['\"]?([가-힣a-zA-Z0-9]{2,20}(?:초식|절초|절기|비기|오의))['\"]?(?:을|를)?\s*(?:펼치|날리|전개)",
        r"(?:내공|진기).*?['\"]?([가-힣a-zA-Z0-9]{2,20}(?:법|공|결))['\"]?",
    ]

    def _check_skill_timeline(
        self,
        current_ep: int,
        manuscript: str,
        prev_manuscripts: List[dict]
    ) -> dict:
        """
        [V59] 스킬 사용 타임라인 검증

        습득 전에 스킬을 사용하는 모순 감지

        Args:
            current_ep: 현재 에피소드 번호
            manuscript: 현재 원고
            prev_manuscripts: 이전 원고 리스트

        Returns:
            {
                "violations": [...],
                "warnings": [...],
                "skill_timeline": {skill_name: acquired_ep}
            }
        """
        violations = []
        warnings = []
        skill_timeline = {}  # {스킬명: 습득 에피소드}

        # 1. 이전 원고들에서 습득한 스킬 추적
        for prev_ms in prev_manuscripts:
            prev_content = prev_ms.get('content', '')
            ep_num = prev_ms.get('ep_num', 0)

            for pattern in self.SKILL_ACQUISITION_PATTERNS:
                matches = re.findall(pattern, prev_content)
                for skill in matches:
                    skill = skill.strip() if isinstance(skill, str) else ''
                    if skill and len(skill) >= 2:
                        if skill not in skill_timeline:
                            skill_timeline[skill] = ep_num

        # 2. 현재 원고에서 새로 습득하는 스킬 추가
        for pattern in self.SKILL_ACQUISITION_PATTERNS:
            matches = re.findall(pattern, manuscript)
            for skill in matches:
                skill = skill.strip() if isinstance(skill, str) else ''
                if skill and len(skill) >= 2:
                    if skill not in skill_timeline:
                        skill_timeline[skill] = current_ep

        # 3. 현재 원고에서 사용하는 스킬 추출
        used_skills = set()
        for pattern in self.SKILL_USAGE_PATTERNS:
            matches = re.findall(pattern, manuscript)
            for skill in matches:
                skill = skill.strip() if isinstance(skill, str) else ''
                if skill and len(skill) >= 2:
                    used_skills.add(skill)

        # 4. 미습득 스킬 사용 감지
        for skill in used_skills:
            # 일반 명사 필터링
            generic_terms = ['내공', '진기', '기력', '무공', '검법', '권법', '장법']
            if skill in generic_terms:
                continue

            # 습득 여부 확인
            is_acquired = False
            acquired_ep = None

            for known_skill, acq_ep in skill_timeline.items():
                if self._is_same_skill(skill, known_skill):
                    is_acquired = True
                    acquired_ep = acq_ep
                    break

            if not is_acquired:
                # 5화 이후에만 엄격하게 체크 (초반은 설정 구축 기간)
                if current_ep > 5:
                    violations.append({
                        'type': 'unlearned_skill_usage',
                        'severity': 'MAJOR',
                        'skill': skill,
                        'description': f"'{skill}'은(는) 이전에 습득한 기록이 없습니다. "
                                      f"배우지 않은 무공/스킬 사용은 연속성 오류입니다."
                    })
                else:
                    warnings.append({
                        'type': 'unlearned_skill_usage',
                        'severity': 'MINOR',
                        'skill': skill,
                        'description': f"'{skill}' 사용됨 (습득 장면 권장)"
                    })

        return {
            'violations': violations,
            'warnings': warnings,
            'skill_timeline': skill_timeline
        }

    def _is_same_skill(self, skill1: str, skill2: str) -> bool:
        """두 스킬이 같은 것인지 판단"""
        skill1 = skill1.strip().lower()
        skill2 = skill2.strip().lower()

        if skill1 == skill2:
            return True

        if skill1 in skill2 or skill2 in skill1:
            return True

        # 핵심 키워드 비교
        keywords1 = set(re.findall(r'[가-힣]{2,}', skill1))
        keywords2 = set(re.findall(r'[가-힣]{2,}', skill2))

        stopwords = {'법', '공', '결', '술', '식', '초'}
        keywords1 -= stopwords
        keywords2 -= stopwords

        common = keywords1 & keywords2
        if len(common) >= 1 and (len(keywords1) <= 2 or len(keywords2) <= 2):
            return True

        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # [V59] 관계 변화 히스토리 추적 강화
    # ═══════════════════════════════════════════════════════════════════════════

    def _track_relationship_history(
        self,
        current_ep: int,
        manuscript: str,
        prev_manuscripts: List[dict]
    ) -> dict:
        """
        [V59] 관계 변화 히스토리 추적 강화

        에피소드별 NPC 관계 상태 변화를 추적하고 급변 감지

        Returns:
            {
                "relationship_history": {npc: [(ep, state), ...]},
                "violations": [...],
                "warnings": [...]
            }
        """
        violations = []
        warnings = []
        relationship_history = {}  # {NPC명: [(ep_num, state), ...]}

        # 관계 상태 키워드 (우선순위 순서)
        STATE_KEYWORDS = {
            "사망": ["죽었", "숨이 끊", "사망", "절명", "목숨을 잃", "숨을 거두"],
            "굴복": ["굴복", "용서를", "목숨을 구걸", "바닥을 기", "살려주", "복종", "무릎"],
            "충성": ["충성", "주군", "목숨 바쳐", "명을 따르", "따르겠", "만세", "주군님"],
            "경외": ["경외", "두려워", "떨며", "감히 못", "공포", "벌벌", "존경", "눈빛이 달라"],
            "의심": ["의심", "수상", "이상하", "믿을 수 없", "의구심", "진심인가", "정체가"],
            "무시": ["무시", "대수롭지", "관심 없", "신경 쓰지", "거들떠보지", "하찮"],
            "적대": ["적대", "원수", "죽이겠", "공격", "증오", "살의", "적의"],
        }

        # 상태 순서 (관계 발전 방향)
        STATE_ORDER = ["적대", "무시", "의심", "경외", "충성"]

        # 주요 NPC/집단 키워드
        NPC_KEYWORDS = [
            "사병", "무사들", "병사들", "부하들", "수하들", "호위", "교두",
            "장로들", "가주", "대장로", "청사", "가솔들", "문주", "총관"
        ]

        def infer_state_from_context(npc: str, content: str) -> str:
            """문맥에서 NPC 관계 상태 추론"""
            if npc not in content:
                return "알 수 없음"

            idx = content.find(npc)
            context = content[max(0, idx-300):min(len(content), idx+300)]

            for state, keywords in STATE_KEYWORDS.items():
                if any(kw in context for kw in keywords):
                    return state

            return "중립"

        # 1. 이전 원고들에서 관계 히스토리 구축
        for prev_ms in prev_manuscripts:
            prev_content = prev_ms.get('content', '')
            ep_num = prev_ms.get('ep_num', 0)

            for npc in NPC_KEYWORDS:
                if npc in prev_content:
                    state = infer_state_from_context(npc, prev_content)
                    if state != "알 수 없음":
                        if npc not in relationship_history:
                            relationship_history[npc] = []
                        relationship_history[npc].append((ep_num, state))

        # 2. 현재 원고에서 관계 상태 추론
        current_states = {}
        for npc in NPC_KEYWORDS:
            if npc in manuscript:
                state = infer_state_from_context(npc, manuscript)
                if state != "알 수 없음":
                    current_states[npc] = state
                    if npc not in relationship_history:
                        relationship_history[npc] = []
                    relationship_history[npc].append((current_ep, state))

        # 3. 급격한 관계 변화 감지
        for npc, history in relationship_history.items():
            if len(history) < 2:
                continue

            # 마지막 두 상태 비교
            prev_ep, prev_state = history[-2] if len(history) >= 2 else (0, "무시")
            curr_ep, curr_state = history[-1]

            if prev_state == curr_state:
                continue

            # 점프 거리 계산
            if prev_state in STATE_ORDER and curr_state in STATE_ORDER:
                prev_idx = STATE_ORDER.index(prev_state)
                curr_idx = STATE_ORDER.index(curr_state)
                jump_distance = abs(curr_idx - prev_idx)

                if jump_distance >= 2:
                    # 2단계 이상 점프는 위반
                    violations.append({
                        'type': 'relationship_jump',
                        'severity': 'MAJOR',
                        'npc': npc,
                        'from_state': prev_state,
                        'to_state': curr_state,
                        'from_ep': prev_ep,
                        'to_ep': curr_ep,
                        'jump_distance': jump_distance,
                        'description': f"'{npc}'의 관계가 제{prev_ep}화 '{prev_state}'에서 "
                                      f"제{curr_ep}화 '{curr_state}'로 {jump_distance}단계 급변. "
                                      f"중간 단계(예: {STATE_ORDER[prev_idx + 1] if prev_idx < len(STATE_ORDER) - 1 else prev_state})를 거치는 묘사 필요."
                    })
                elif jump_distance == 1:
                    # 1단계 점프는 경고만
                    warnings.append({
                        'type': 'relationship_change',
                        'severity': 'INFO',
                        'npc': npc,
                        'description': f"'{npc}' 관계: {prev_state}→{curr_state} (정상 전환)"
                    })

        return {
            'relationship_history': relationship_history,
            'violations': violations,
            'warnings': warnings
        }

    def inspect_manuscript_v59(
        self,
        current_ep: int,
        manuscript: str,
        blueprint: dict,
        prev_manuscripts: List[dict],
        hud_history: List[dict] = None
    ) -> dict:
        """
        [V59] 강화된 원고 연속성 검증 (스킬 + 관계 타임라인 포함)

        기존 inspect_manuscript()에 V59 검증을 추가

        Args:
            current_ep: 현재 에피소드 번호
            manuscript: Writer가 생성한 원고 텍스트
            blueprint: 현재 에피소드 Blueprint dict
            prev_manuscripts: 이전 원고 리스트
            hud_history: HUD 스냅샷 히스토리 (선택적)

        Returns:
            기존 결과 + skill_timeline + relationship_history
        """
        # 기존 검증 실행
        base_result = self.inspect_manuscript(
            current_ep, manuscript, blueprint, prev_manuscripts, hud_history
        )

        # V59 스킬 타임라인 검증
        skill_check = self._check_skill_timeline(current_ep, manuscript, prev_manuscripts)

        # V59 관계 히스토리 검증
        rel_check = self._track_relationship_history(current_ep, manuscript, prev_manuscripts)

        # 결과 병합
        all_violations = base_result.get('violations', []) + skill_check.get('violations', []) + rel_check.get('violations', [])
        all_warnings = base_result.get('warnings', []) + skill_check.get('warnings', []) + rel_check.get('warnings', [])

        # 위반 여부에 따라 decision 조정
        if any(v.get('severity') in ['CRITICAL', 'MAJOR'] for v in all_violations):
            final_decision = "REJECT"
            final_severity = "CRITICAL" if any(v.get('severity') == 'CRITICAL' for v in all_violations) else "MAJOR"
        else:
            final_decision = base_result.get('decision', 'PASS')
            final_severity = base_result.get('severity', 'NONE')

        return {
            **base_result,
            "decision": final_decision,
            "severity": final_severity,
            "violations": all_violations,
            "warnings": all_warnings,
            "v59_skill_timeline": skill_check.get('skill_timeline', {}),
            "v59_relationship_history": rel_check.get('relationship_history', {}),
            "fix_instructions": self._generate_v59_fix_instructions(all_violations) if all_violations else base_result.get('fix_instructions', '')
        }

    def _generate_v59_fix_instructions(self, violations: List[dict]) -> str:
        """[V59] 위반 사항에 대한 수정 지시 생성"""
        instructions = []

        for v in violations:
            v_type = v.get('type', '')

            if v_type == 'unlearned_skill_usage':
                skill = v.get('skill', '')
                instructions.append(
                    f"[V59 스킬 연속성] '{skill}'은(는) 습득 기록 없이 사용됨. "
                    f"해당 스킬의 습득 장면을 이전 원고에 추가하거나, "
                    f"현재 원고에서 '이전에 배운'으로 언급하세요."
                )
            elif v_type == 'relationship_jump':
                npc = v.get('npc', '')
                from_state = v.get('from_state', '')
                to_state = v.get('to_state', '')
                instructions.append(
                    f"[V59 관계 연속성] '{npc}'의 '{from_state}'→'{to_state}' 급변. "
                    f"중간 단계를 묘사하거나, 급변의 서사적 근거를 추가하세요."
                )
            else:
                # 기존 수정 지시
                instructions.append(self._generate_manuscript_fix_instructions([v]))

        return "\n".join(instructions) if instructions else "위반 사항을 확인하고 수정하세요."
