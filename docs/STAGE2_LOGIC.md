# Stage 2: Arc Tactical Design - 로직 상세

> **목적**: 50개 Arc의 전술적 설계 (권당 5개 Arc)
> **입력**: Stage 1의 Volume 전략 + Bible 데이터
> **출력**: 각 Arc의 tactical_doc, joint_docs, state_constraints

---

## 전체 흐름도

```
┌─────────────────────────────────────────────────────────────────┐
│                    Stage 2: Arc Design                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐                                                │
│  │ 초기화      │ Bible/Volumes 로드, 기존 Arc 데이터 확인       │
│  └──────┬──────┘                                                │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              배치 처리 루프 (5개씩)                      │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │ A. 병렬 농축 단계                                │    │    │
│  │  │    enrich_raw_block_async() × 5 병렬            │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │                       ▼                                  │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │ B. 사후 용접 (stitch_joints)                     │    │    │
│  │  │    Arc 간 인과율 연결 + 엔티티 앵커링            │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │                       ▼                                  │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │ C. 순차 설계 (Arc별)                             │    │    │
│  │  │    ┌─────────────────────────────────────────┐  │    │    │
│  │  │    │ Arc 생성 시도 루프 (최대 4회)           │  │    │    │
│  │  │    │                                         │  │    │    │
│  │  │    │  1. Preflight 분석                      │  │    │    │
│  │  │    │  2. ConstraintCompiler                  │  │    │    │
│  │  │    │  3. Arc 생성 (Analyst/ToT/TwoPhase)     │  │    │    │
│  │  │    │  4. DraftValidator (Python, 무료)       │  │    │    │
│  │  │    │  5. SelfReflector (자기 비판)           │  │    │    │
│  │  │    │  6. Consensus (3-LLM 합의)              │  │    │    │
│  │  │    │  7. ContinuityInspector (LLM 검증)      │  │    │    │
│  │  │    │  8. Director (최종 승인)                │  │    │    │
│  │  │    │                                         │  │    │    │
│  │  │    │  PASS → 저장 & 다음 Arc                 │  │    │    │
│  │  │    │  REJECT → 피드백 주입 & 재시도          │  │    │    │
│  │  │    └─────────────────────────────────────────┘  │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. 초기화 단계

### 1.1 데이터 로드
```
main_a.py:3823-3856

1. master_bible 로드 (DB anchor)
2. volumes 전략 로드 (Stage 1 결과)
3. 기존 arcs 데이터 로드 (이어하기 지원)
4. plot_roadmap에서 전체 Arc 수 파악
5. 주인공 이름 추출 (MartialHUD.Protagonist.actual_truth.name)
```

### 1.2 주요 변수 초기화
| 변수 | 설명 |
|------|------|
| `all_refined_arcs` | 완성된 Arc 리스트 |
| `done_count` | 완료된 Arc 수 |
| `total_count` | 전체 Arc 수 (plot_roadmap 기준) |
| `constraint_db` | ConstraintDB 인스턴스 (제약 조건 관리) |

---

## 2. 배치 처리 루프

> **단위**: 5개 Arc씩 배치 처리
> **이유**: 인과율 정밀 용접을 위해 1회 10개(2개 배치) 이내 권장

### 2.1 A. 병렬 농축 단계 (Enrichment)

```python
# main_a.py:3910-3988

async def throttled_enrich(idx):
    return await self.agents['analyst'].enrich_raw_block_async(
        curr_b,      # 현재 블록 DNA
        prev_b,      # 이전 블록
        next_b_safe, # 미래 블록 (제목만 - 오염 방지)
        [],
        transfused_history=last_refined_context
    )

# 5개 동시 실행 (Semaphore 제한)
enrichment_tasks = [throttled_enrich(i) for i in range(batch_start, batch_end)]
enriched_batch = await asyncio.gather(*enrichment_tasks)
```

**출력 구조**:
- `content.context`: 블록 맥락
- `joint_docs`: Arc 종료 시 상태
- `status_shadow`: 예상 손실 (내공, 부상)

### 2.2 B. 사후 용접 (Stitch Joints)

```python
# main_a.py:3994-4025

stitch_res = self.agents['analyst'].stitch_joints(
    arc_a.get('joint_docs', {}),
    arc_b.get('joint_docs', {}),
    arc_b.get('content', {}).get('context', "")
)

if stitch_res.get('status') == "REPAIRED":
    # 인과율 용접 완료
    arc_b['content']['context'] = stitch_res.get('repaired_joint_b')

    # 고유 명사 앵커링 (Entity Anchoring)
    if stitch_res.get('entity_anchors'):
        self.sys.lore.update_v20_assets({"Temporary_Anchors": stitch_res['entity_anchors']})
```

---

## 3. 순차 설계 단계 (Arc별)

### 3.1 사전 준비

```
main_a.py:4044-4095

1. 결핍 리포트 생성 (Analyst.get_lack_report)
   → 주인공의 무공/위상 결핍 분석

2. 욕망 드라이브 생성 (Weaver.generate_arc_drive)
   → Arc의 핵심 동기/목표 설정

3. ConstraintDB 제약 블록 생성
   → 이전 Arc 기반 획득 금지 아이템 목록

4. ConstraintCompiler 체크리스트 생성
   → 구조화된 MUST DO / MUST NOT DO
```

### 3.2 Arc 생성 시도 루프

> **최대 시도 횟수**: 4회 (ANALYST_MAX_ATTEMPTS)
> **3회 실패 후**: 10초 대기 → 4회차 최종 시도

```
┌────────────────────────────────────────────────────────────────┐
│                Arc 생성 시도 루프 (attempt 0~3)                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  attempt >= 1?  ─────────► REJECT 패턴 분석 주입               │
│                                                                │
│  attempt == 3?  ─────────► 10초 대기 (API 안정화)              │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ [무기 #1] Preflight 분석                                │   │
│  │ - 이전 Arc 전체 분석                                    │   │
│  │ - 아이템/수여물 타임라인                                │   │
│  │ - 금지 사항 맵 구축                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ [무기 #2] ConstraintCompiler                            │   │
│  │ - MUST DO (필수 사항)                                   │   │
│  │ - MUST NOT DO (금지 사항)                               │   │
│  │ - INHERITED STATE (계승 상태)                           │   │
│  │ - SELF-CHECK (자체 검증 항목)                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ▼                                      │
│  attempt >= 2?  ─────────► [필살기] ToT / TwoPhase 시도        │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ [핵심] Analyst Arc 설계                                 │   │
│  │ - plan_single_arc_v20() 호출                            │   │
│  │ - 강화된 컨텍스트 + Preflight + Constraints 주입        │   │
│  │ - Thinking Level "high" 적용                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ [무기 #3] DraftValidator (Python, LLM 비용 0원)         │   │
│  │ - 필수 필드 검증                                        │   │
│  │ - 중복 아이템 획득 검증                                 │   │
│  │ - 위치/부상 연속성 검증                                 │   │
│  │ - tactical_doc 분량 + 화별 분할 검증                    │   │
│  │                                                         │   │
│  │ CRITICAL 발견 → 즉시 재시도                             │   │
│  │ WARNING만 → 계속 진행                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ SelfReflector (Analyst 자기 비판)                       │   │
│  │ - 생성된 Arc 자체 검토                                  │   │
│  │ - 개선 가능 시 수정 적용                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Consensus (3-LLM 합의 검증)                             │   │
│  │ - continuity_focused: 연속성 전문가                     │   │
│  │ - structure_focused: 구조 전문가                        │   │
│  │ - narrative_focused: 서사 전문가                        │   │
│  │                                                         │   │
│  │ CRITICAL 이슈 → 즉시 REJECT                             │   │
│  │ 과반수 REJECT → REJECT                                  │   │
│  │ 그 외 → PASS                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 4. 후처리 검증 파이프라인

### 4.1 검증 순서

```
1. Arc 매핑 검증 (_validate_arc_mapping)
   └─ 블록↔아크 매핑 및 회차 범위 정합성

2. Stage2Optimizer Auto-Corrector
   └─ 자동 수정 가능한 오류 수정

3. ConstraintDB 즉시 검증 (Python, 무료)
   └─ 제약 위반 감지 (중복 획득 등)

4. Flow Guard (서사 폭주/정체 차단)
   └─ _stage2_flow_guard()

5. Duplicate Guard (전술서 중복 차단)
   └─ 직전 Arc와 tactical_doc 유사도 검사

6. DraftValidator 2차 검증
   └─ ArcCorrector로 MAJOR 이슈 부분 수정 시도

7. ContinuityInspector (LLM 심층 검증)
   └─ Arc 간 + Arc 내 모순 검증

8. Director (최종 승인)
   └─ audit_strategic_plan()
```

### 4.2 ContinuityInspector 검증 항목

```
modules/domain/agents/continuity_inspector.py

[Cross-Arc 검증]
1. 아이템/무기 연속성
   - 중복 획득 여부
   - 소지품 계승 여부

2. 수여물/위상 연속성
   - 중복 수여 여부
   - 위상 변화 반영 여부

3. 상태 연속성
   - 부상 상태 계승
   - 내공 수치 연속성

[Intra-Arc 검증]
4. 단일 Arc 내 모순
   - 화 사이 인과 연결
   - 설정 일관성 (무기 특성, 호칭 등)

[판정 기준]
- CRITICAL: 타임라인 오류 → 즉시 REJECT
- MAJOR: 연속성 오류 → REJECT
- MINOR: 경미한 불일치 → WARNING (PASS 가능)
```

### 4.3 Director 검증

```
modules/domain/agents/director.py

audit_strategic_plan():
1. Self-Consistency 검증 (3회 LLM 호출)
   - 동일 프롬프트로 3회 검증
   - 점수 분산이 크면 불안정 판단

2. 품질 점수 산정
   - tactical_doc 분량
   - 화별 구분 명확성
   - 서사 밀도

3. PASS/REJECT 결정
   - 점수 70점 이상: PASS
   - 점수 70점 미만: REJECT + re_slice_instruction
```

---

## 5. 성공 시 저장

### 5.1 저장 데이터

```python
# main_a.py:4919-5017

# 욕망 데이터 + HUD 그림자 박제
refined_arc['arc_drive'] = arc_drive
refined_arc['joint_docs'] = enriched_block.get('joint_docs', {})
refined_arc['status_shadow'] = enriched_block.get('status_shadow', {})

# 소지품 계승 (physical_inventory 빈 경우)
if not curr_inventory:
    inherited = prev_inventory - consumed + acquired
    refined_arc['joint_docs']['physical_inventory'] = inherited

# DB 저장
all_refined_arcs.append(refined_arc)
self.current_project.save_v20_anchor("arcs", all_refined_arcs)
await self._safe_commit_async()

# ConstraintDB 업데이트
constraint_db.update_arc_state(refined_arc)
```

### 5.2 Arc 데이터 구조

```json
{
  "arc_no": 1,
  "ep_start": 1,
  "ep_end": 5,
  "ep_count": 5,
  "title": "Arc 제목",

  "tactical_doc": "제 1화: ... 제 2화: ...",

  "beat_sequence": ["제 1화: 핵심 비트", ...],

  "hybrid_composition": {
    "primary": "주 서사 패턴",
    "secondary": ["부 패턴"],
    "mixing_logic": "패턴 조합 전략"
  },

  "state_constraints": {
    "arc_start_state": {
      "location": "시작 위치",
      "equipment": ["소지품"],
      "injuries": "부상 상태",
      "internal_energy": 100
    },
    "arc_end_state": {
      "location": "종료 위치",
      "equipment": ["종료 시 소지품"],
      "injuries": "종료 시 부상",
      "internal_energy": 70
    },
    "items_acquired": ["새로 획득 아이템"],
    "items_consumed": ["소모 아이템"],
    "grants_received": ["수여받은 것"]
  },

  "joint_docs": {
    "final_location": "Arc 종료 시 정확한 위치",
    "physical_inventory": ["종료 시 소지품 전체 목록"],
    "world_joint": "다음 Arc가 계승할 세계 변화"
  },

  "status_shadow": {
    "internal_energy_loss": "30%",
    "expected_injuries": "부상 상태",
    "item_consumption": ["소모된 아이템"]
  },

  "arc_drive": {
    "desire_vector": "욕망 벡터",
    ...
  }
}
```

---

## 6. 핵심 에이전트 상세

### 6.1 FourPhaseArcGenerator

> **위치**: `modules/domain/agents/four_phase_arc_generator.py`
> **비용**: ~$0.15-0.20/Arc
> **목표**: 초기 통과율 90%+

```
┌─────────────────────────────────────────────────────────────────┐
│                    4-Phase Pipeline                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: PREFLIGHT                                             │
│  ├─ PreflightChecker.analyze(prev_arcs)                        │
│  ├─ ConstraintCompiler.compile(prev_arcs)                      │
│  ├─ NegativeExampleInjector.generate_injection()               │
│  └─ 통합 제약 블록 생성                                         │
│                                                                 │
│  Phase 2: GENERATE (Ensemble)                                   │
│  ├─ 3개 전략으로 병렬 생성                                      │
│  │   ├─ conservative (temp 0.3): 안정성 우선                   │
│  │   ├─ balanced (temp 0.5): 균형                              │
│  │   └─ creative (temp 0.7): 창의성 우선                       │
│  ├─ 각 후보 평가 (100점 만점)                                   │
│  └─ 최고 점수 후보 선택                                         │
│                                                                 │
│  Phase 2.5: QUICK DUPLICATE CHECK (V60.28)                      │
│  └─ Python 기반 중복 아이템 체크 (API 비용 0)                   │
│                                                                 │
│  Phase 3: CRITIQUE                                              │
│  ├─ ArcCritic.critique(generated_arc)                          │
│  ├─ 7가지 기준 평가 (각 10점)                                   │
│  │   ├─ 아이템 연속성                                          │
│  │   ├─ 위치 연속성                                            │
│  │   ├─ 상태 연속성                                            │
│  │   ├─ 수여물 타임라인                                        │
│  │   ├─ tactical_doc 품질                                      │
│  │   ├─ joint_docs 정합성                                      │
│  │   └─ 서사적 일관성                                          │
│  └─ 자동 수정 적용 (가능한 경우)                                │
│                                                                 │
│  Phase 4: VALIDATE (Consensus)                                  │
│  ├─ 3개 LLM 병렬 검증                                           │
│  │   ├─ continuity_focused                                     │
│  │   ├─ structure_focused                                      │
│  │   └─ narrative_focused                                      │
│  ├─ CRITICAL 있으면 → REJECT                                    │
│  ├─ 과반수 REJECT → REJECT                                      │
│  └─ 그 외 → PASS                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 PreflightChecker

> **위치**: `modules/domain/agents/preflight_checker.py`
> **비용**: ~$0.03-0.05/Arc
> **모델**: gemini-3-flash-preview

**분석 출력**:
```json
{
  "timeline_analysis": {
    "items": [{"arc": 1, "episode": 2, "item": "대도", "action": "획득"}],
    "grants": [{"arc": 2, "grant": "철혈사자패", "grantor": "단주"}],
    "current_inventory": ["대도", "철혈사자패"],
    "consumed_items": []
  },
  "relationship_map": {
    "단주": {"current_state": "경외", "history": ["Arc1: 무시 → Arc2: 인정"]}
  },
  "world_state": {
    "current_location": "철혈단 본거지",
    "protagonist_status": {
      "injuries": "왼팔 경상",
      "internal_energy": 85
    }
  },
  "absolute_prohibitions": {
    "items_cannot_acquire": [
      {"item": "대도", "reason": "Arc 1에서 이미 획득", "violation_type": "DUPLICATE_ACQUISITION"}
    ],
    "grants_cannot_receive": [...],
    "state_constraints": [...]
  },
  "next_arc_guidance": {
    "must_start_with": "철혈단 본거지에서 왼팔 경상 상태로",
    "warning": "절대로 이미 가진 것을 다시 획득하지 마세요"
  }
}
```

### 6.3 ConstraintCompiler

> **위치**: `modules/domain/agents/constraint_compiler.py`
> **비용**: 0원 (Python 기반)

**출력 형식**:
```
████████████████████████████████████████████████████████████████████████
█ [V60.28] 절대 금지 - 위반 시 즉시 REJECT                             █
████████████████████████████████████████████████████████████████████████

🚨🚨🚨 다음 아이템은 절대 획득하지 마세요! 🚨🚨🚨
========================================================================
  ❌ '대도' - Arc 1에서 이미 획득함 → 다시 획득 금지!
  ❌ '철혈사자패' - Arc 2에서 이미 획득함 → 다시 획득 금지!
========================================================================

┌──────────────────────────────────────────────────────────────────────┐
│ 🚫 MUST NOT DO (절대 금지 - 위반 시 즉시 REJECT)                     │
├──────────────────────────────────────────────────────────────────────┤
│ [아이템 획득 금지 - 이미 보유 중]                                     │
│   ❌ 대도 (Arc 1에서 획득)                                           │
│   ❌ 철혈사자패 (Arc 2에서 획득)                                     │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 📋 INHERITED STATE (반드시 계승할 상태 - Arc 시작점)                 │
├──────────────────────────────────────────────────────────────────────┤
│ 🗺️ 시작 위치: 철혈단 본거지                                          │
│ 📦 소지품: 대도, 철혈사자패                                          │
│ 💔 부상 상태: 왼팔 경상                                              │
│ ⚡ 내공: 85%                                                         │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ ✅ MUST DO (필수 사항)                                               │
├──────────────────────────────────────────────────────────────────────┤
│ □ Arc 시작 위치 = '철혈단 본거지' 에서 시작                          │
│ □ 소지품 상태로 시작 (새 획득 없이 기존 아이템 소지)                 │
│ □ 부상 상태 계승 (회복 장면 없이 멀쩡하면 안 됨)                     │
│ □ tactical_doc 최소 3000자 이상                                      │
│ □ 화별 구분 명확히 (제 N화 형식)                                     │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 🔍 SELF-CHECK (생성 후 자체 검증)                                    │
├──────────────────────────────────────────────────────────────────────┤
│ □ items_acquired에 금지 목록 아이템 없는가?                          │
│ □ arc_start_state.location = 이전 Arc 종료 위치인가?                 │
│ □ tactical_doc에 '다시 획득' 문구 없는가?                            │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.4 ArcDraftValidator

> **위치**: `modules/domain/agents/arc_draft_validator.py`
> **비용**: 0원 (Python 기반)

**검증 항목**:
1. 필수 필드 존재 여부
2. 중복 아이템 획득 (패턴 매칭)
3. 위치 연속성 (시작 위치 ≠ 이전 종료 위치)
4. 부상 상태 연속성
5. 수여물 타임라인
6. tactical_doc 분량 + 화별 분할
7. 화간 상태 체크포인트 (V60.40)
8. ep_count와 실제 화 수 동기화

**출력**:
```json
{
  "valid": false,
  "score": 45,
  "critical_issues": ["중복 획득 시도: '대도' (이미 획득됨)"],
  "warnings": ["tactical_doc 분량 부족: 2000자 (권장 3000자)"],
  "suggestions": ["내용 빈약한 화: [3] (대사/행동 추가 권장)"]
}
```

### 6.5 ConsensusValidator

> **위치**: `modules/domain/agents/consensus_validator.py`
> **비용**: ~$0.06-0.10/Arc
> **모델**: gemini-3-pro-preview × 3 병렬

**3가지 검증 관점**:

| 관점 | 역할 | 집중 항목 | Temperature |
|------|------|----------|-------------|
| continuity_focused | 연속성 전문가 | 아이템/수여물/위치/상태 타임라인 | 0.1 |
| structure_focused | 구조 전문가 | tactical_doc 분량, 화별 구분, 필드 완성도 | 0.1 |
| narrative_focused | 서사 전문가 | 캐릭터 일관성, 긴장감 곡선, 갈등 계승 | 0.2 |

**합의 로직**:
- CRITICAL 이슈 있음 → REJECT
- 과반수 REJECT → REJECT
- 그 외 → PASS

---

## 7. 에러 처리

### 7.1 재시도 전략

| 시도 | 대응 |
|------|------|
| 1회차 | 기본 생성 (모든 주입 적용) |
| 2회차 | Focus Mode (컨텍스트 최소화) + ToT/TwoPhase 시도 |
| 3회차 | REJECT 패턴 분석 주입 + ToT/TwoPhase |
| 4회차 | 10초 대기 후 최종 시도 (최강 피드백) |

### 7.2 실패 시 사용자 선택

```
[1] 건너뛰고 계속
[2] 중단
[3] 다시 하기 (자동)
[4] 수동 개입 (리포트 확인 후 재시도)
```

### 7.3 실패 리포트

> **위치**: `projects/{name}/logs/arc_{N}_failure_report.txt`

```
============================================================
Arc 5 실패 리포트
============================================================

[REJECT 히스토리]
  시도 1: duplicate_acquisition: 대도 재획득 시도
  시도 2: duplicate_acquisition: 대도 재획득 시도
  시도 3: state_discontinuity: 부상 급격 회복
  시도 4: structure: tactical_doc 분량 부족

[이전 Arc에서 이미 획득한 아이템 - 중복 획득 금지]
  ❌ 대도
  ❌ 철혈사자패
  ❌ 금창약

[현재 제약 조건]
  ...

[마지막 생성된 Arc 데이터]
  tactical_doc 길이: 1800자
  items_acquired: ["대도"]
```

---

## 8. 모델 사용

| 에이전트 | 모델 | 비고 |
|----------|------|------|
| Analyst | gemini-3-pro-preview | Stage 2 고정 |
| PreflightChecker | gemini-3-flash-preview | 분석용 |
| ArcEnsembleGenerator | gemini-3-pro-preview | Thinking "high" |
| ArcCritic | gemini-3-pro-preview | Thinking "medium" |
| ConsensusValidator | gemini-3-pro-preview × 3 | 병렬 |
| ContinuityInspector | gemini-2.5-flash | 비용 절감 |
| Director | gemini-2.0-flash | 고정 |

---

## 9. 성능 지표

### 9.1 PassRateMonitor 기록 항목

```python
{
    "stage": 2,
    "episode": arc_no,
    "arc": arc_no,
    "attempt_num": attempt + 1,
    "success": True/False,
    "reject_reason": "...",
    "generation_method": "analyst" / "tot" / "two_phase"
}
```

### 9.2 QualityDashboard 기록 항목

```python
{
    "ep_num": arc_no,
    "stage": 2,
    "result": {
        "decision": "PASS" / "REJECT",
        "score": 80,
        "violations": [...],
        "warnings": [...]
    }
}
```

---

## 10. 주요 상수

```python
# modules/core/constants.py

class RetryLimits:
    ANALYST_MAX_ATTEMPTS = 4     # Arc 설계 최대 시도

class VolumeSettings:
    ARCS_PER_VOLUME = 5          # 권당 Arc 수

class RecoveryLimits:
    MAX_PARALLEL_RECOVERY = 3    # 병렬 복구 최대 수
    CRITICAL_MISSING_THRESHOLD = 3  # 필수 필드 누락 허용치
```

---

## 부록: 관련 파일 경로

| 파일 | 역할 |
|------|------|
| `main_a.py:3797-5276` | Stage 2 메인 로직 |
| `modules/domain/agents/analyst.py` | Analyst 에이전트 |
| `modules/domain/agents/four_phase_arc_generator.py` | 4-Phase 파이프라인 |
| `modules/domain/agents/preflight_checker.py` | Preflight 분석 |
| `modules/domain/agents/arc_ensemble.py` | Ensemble 생성 |
| `modules/domain/agents/arc_critic.py` | Arc 비평 |
| `modules/domain/agents/consensus_validator.py` | 3-LLM 합의 |
| `modules/domain/agents/arc_draft_validator.py` | Python 사전 검증 |
| `modules/domain/agents/continuity_inspector.py` | 연속성 검증 |
| `modules/domain/agents/constraint_compiler.py` | 제약 컴파일러 |
| `modules/domain/agents/director.py` | 최종 승인 |
| `modules/core/constraint_db.py` | 제약 DB |
