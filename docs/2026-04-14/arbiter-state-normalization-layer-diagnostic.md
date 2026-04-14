# Arbiter / 상태 정규화 레이어 진단 보고서

**목적**: 파이프라인에서 drift, rerun 증가, 연속성 붕괴의 원인이 "생성 전 상태 정규화 부재/부실"인지 확인  
**조사 방법**: TF 5개 에이전트 병렬 코드베이스 전수 조사  
**조사 일자**: 2026-04-14  
**조사 범위**: `modules/core/`, `modules/domain/agents/` 전체

---

## 1. 생성 직전 컨텍스트 조립

### 핵심 경로

```
Writer.write_v20_manuscript()
  → ChiefWriter.generate_ensemble()
    → ChiefWriter._prepare_generate_ensemble_context()
      → ChiefWriterContextBuilder.build_common_context()        [chief_writer_context.py:116]
        → ChiefWriterContextPackets.build_common_context_packets() [chief_writer_context_packets.py:174]
        → build_chief_writer_main_prompt()                       [chief_writer_prompts.py:50]
```

### 합쳐지는 데이터 (20+ 소스)

| 범주 | 데이터 소스 | 조립 방식 |
|------|-----------|---------|
| **Lore** | `master_bible`, `core_identity`, `world_origin`, `incarnation_type` | `_extract_bible_context()` → 구조화 dict |
| **Summary** | `prev_manuscript`, `prev_digest`, `prev_ending` | `_generate_episode_digest()` → regex 기반 정규화 |
| **Character State** | `hud_report`, `high_density_hud`, `npc_equipment`, `npc_frequency` | packet dict로 분리 조립 |
| **Recent Events** | `chain_link_section`, `carryover_ceiling_section` | 직전 화 연결고리 + 지난 권위 상한선 |
| **Director Feedback** | `director_feedback`, `failure_constraints` | `_build_feedback_section()` → 명시적 섹션 |
| **Blueprint** | `scene_breakdown`, `integrated_scenario_advisory`, `ending_hook`, `opening_anchor` | `_extract_blueprint_sections()` |
| **Arc/Style** | `arc_doc`, `style_guide`, `emotional_beat_section` | 별도 섹션 |
| **Safety Guards** | `future_guard`, `past_guard`, `immutable_fact_section` | TruthGate 연동 |

### 조립 방식: **구조적 merge (단순 concat 아님)**

`build_chief_writer_main_prompt()` [chief_writer_prompts.py:97~227]에서 **명시적 우선순위 계층** 적용:

```
[STEP 0.5: 권위 우선순위]
1. Opening Anchor
2. Immutable Facts / world-state / mandatory truth / chain_link / prev manuscript full-text / prev digest / carryover ceiling
3. Structured scene breakdown
4. Advisory integrated scenario prose
5. Feedback / constraints / HUD-heavy cues / style guidance
```

프롬프트 내부 섹션 순서:
```
STEP 0.5-1: Opening Anchor
STEP 0.5-2: Writer Hard Canon (world_state, immutable_facts, chain_link)
STEP 0.75: Writer Guidance (feedback, constraints, soft guidance)
STEP 1: Blueprint 분석 (scene breakdown, scenario advisory, emotional beat)
STEP 2: 연속성 확인 (prev_ending)
STEP 3: 현재 상태 반영 (HUD, NPC 장비/빈도)
STEP 4: Arc 전술 참조
STEP 5: 세계관 설정
STEP 6: 문체 DNA 가이드
```

---

## 2. 상태 충돌 처리

### 명시적 충돌 감지: **제한적**

| 모듈 | 감지 대상 | 방식 | 한계 |
|------|----------|------|------|
| `TruthGate` [truth_gate.py:79-319] | 사망 NPC 부활, 미보유 아이템 사용, 파괴된 장소 방문, 중복 스킬 습득, 카르마 범위 초과 | Python 규칙 | **advisory 모드만** — 저장 차단 안 함 |
| `StateTextVerifier` [state_text_verifier.py:119-140] | extracted_state ↔ manuscript 교차 검증 | LLM 기반 | advisory — 수정값 제안만, 자동 적용 안 됨 |
| `CrossAgentVerifier` [cross_agent_verifier.py:165-269] | Arc→Blueprint, Blueprint→Manuscript 준수 | Python precheck + 선택적 LLM | 단방향 검증, 상호 충돌 해결 없음 |

### 충돌 감지 **없는** 영역

- **lore / event / summary 간 충돌**: 명시적 감지 로직 부재
- **state_changes의 다중 소스 간 충돌**: 검증 로직 부재
- **장기 축적 drift**: 에피소드 단위 스냅샷만으로 추적 불가

### 우선순위 규칙: **암묵적, 코드 정의 없음**

| 영역 | 현재 처리 | 코드 위치 |
|------|---------|---------|
| 아이템 상태 | `last_updated_ep` 기준 최신 우선 (순차 누적) | `fact_ledger.py:137-250` |
| 상태 변경 적용 | NPC 사망 → 스킬 → 관계 → 아이템 → 파괴 → 부상/이동 (순서 고정, 우선순위 없음) | `world_state.py:118-250` |
| 에너지 회복 | `RECOVERY_LIMITS` dict (영약 40, 운기조식 20, 휴식 50, 기본 5) | `state_delta_tracker.py:77-159` |
| 엔드 상태 | `arc_end_state > status_shadow > joint_docs > 기본값` | `arc_state_utils.py:35-103` |

**`recent_event > lore`, `hard_constraint > summary` 같은 선언적 우선순위 규칙 → 코드에 없음**

---

## 3. 생성 전 "해석 단계" 존재 여부

### **부분적 YES — 정규화 단계가 존재하지만 "충돌 해결"은 아님**

#### 존재하는 정규화:

| 레벨 | 모듈 | 작업 |
|------|------|------|
| **Packet Assembly** | `ChiefWriterContextPackets` [chief_writer_context_packets.py:174~312] | 에피소드 다이제스트 (regex 기반), HUD 급변 감지, NPC 등장 빈도 경고, HUD 변화 추세, 지난 권위 상한선 계산 |
| **Writer Input** | `Writer._collect_writer_prompt_context()` [writer.py:98~183] | 아크 PATTERN_PROFILE 추출, 주인공 설정별 명령 구성, NPC 장비 요약, Entity Registry 포맷팅 |
| **Prompt Structure** | `build_chief_writer_main_prompt()` [chief_writer_prompts.py:116-128] | 권위 우선순위 명시, 섹션 분리 |

#### 존재하지 않는 정규화:

- **상태 소스 간 모순 탐지 → 해결**: 없음
- **우선순위 기반 conflict resolution**: 프롬프트 텍스트로 가이드하지만, 코드 레벨 해결은 없음
- **충돌 시 어떤 값을 채택할지 결정하는 arbitration step**: 없음

**결론**: Producer가 "이미 정리된 데이터"를 받지만, "정리"는 포맷팅/구조화이지 "충돌 해결"이 아님. 충돌이 있을 경우 Producer(LLM)가 프롬프트의 우선순위 계층 지시에 따라 **직접 해석**함.

---

## 4. 상태 vs 텍스트 분리 여부

### **부분적 분리 (분리도 약 70%)**

| 항목 | 분리 여부 | 근거 |
|------|----------|------|
| 텍스트 요약 (Summary) | **분리** | `db_manager.py:1465` `summary` 컬럼 별도 |
| 캐릭터 감정 | **분리** | `state_changes.protagonist_emotion` 명시적 필드 |
| 관계 변화 | **분리** | `relationship_tracker_npc.py` 별도 history |
| 미해결 플롯/떡밥 | **분리** | `foreshadow_tracker.py` hooks/plants/payoffs, `state_tracker.py` active_plots |
| 사건 타임라인 | **분리** | `state_tracker.py:168-169` in_world_timeline |
| 금지/유지 조건 | **분리** | `state_extractor.py:165-170` forbidden_in_next_arc |
| 내공/부상 | **혼합** | `arc_summary_utils.py:49-86` 최종값만, 이력은 `state_delta_tracker.py`에만 |
| NPC 관계+신뢰도 | **혼합** | `world_state.py:137` known_attrs dict가 role/relation과 함께 |
| 아이템 상태 | **혼합** | `inventory_state.py`와 `world_state.py` 양쪽에 존재 |

### 데이터 흐름 구조

```
Arc Design
  ├─ tactical_doc (텍스트 설명)
  ├─ state_constraints (구조화)
  │   ├─ arc_end_state (내공, 부상, 위치, 장비 dict)
  │   ├─ relationship_changes (구조화 dict)
  │   ├─ items_consumed / protagonist_items (list)
  │   └─ forbidden_in_next_arc (list)
  └─ state_changes (StateChangesDict TypedDict)
       ├─ npc_deaths, skill_acquisitions, relationship_changes
       ├─ protagonist_emotion (dict) ← 분리
       ├─ permanent_injuries, companion_changes, commitments
       └─ 나머지: str | dict 혼합

DB Storage
  ├─ state_logs (ep_num → data JSON + summary TEXT) ← 혼합
  ├─ npc_relationship_edges (구조화)
  ├─ canonical_facts (수치 팩트)
  ├─ causal_graph (인과 연결)
  └─ anchors
      ├─ world_state (alive_npcs, relationships, timeline 혼합)
      └─ fact_ledger (characters, numbers, items, locations 분리)
```

---

## 5. State 변경 기록

### **이중 구조: 미시 추적 O, 거시 추적 X**

| 추적 대상 | 저장소 | 기록 방식 | 이력 보존 |
|----------|-------|---------|---------|
| 내공 변화 | `StateDeltaTracker` (메모리) | EnergyDelta 리스트 누적 | **전체** |
| 부상 변화 | `StateDeltaTracker.injury_history` | InjuryEvent 리스트 | **전체** |
| 관계 변화 | `RelationshipTracker.transition_history` | RelationshipEvent 리스트 | **전체** |
| 감정 변화 | `EmotionArcTracker.history` | (ep_num, emotion, intensity) | **전체** |
| 복선 상태 | `ForeshadowTracker.hooks` | hint_episodes 리스트 | **재암시 기록** |
| 팩트 (NPC, 수치, 아이템) | `FactLedger` + DB anchors | history[] 누적 | **최대 100건** |
| **에피소드별 전체 상태** | **state_logs (DB)** | **INSERT OR REPLACE** | **최신값만 (덮어쓰기)** |

### 변경 기록 흐름

```
episode_bible.state_changes (구조화)
  ↓
FactLedger.update_from_state_changes(ep_num, state_changes)
  ├─ _apply_character_foundation_state_changes() → history[] 추가 (최대 100)
  ├─ _apply_item_state_changes() → history[] 추가
  └─ _apply_entity_state_changes() → history[] 추가
  ↓
FactLedger.save() → db.save_anchor("fact_ledger", self._ledger) ← history 포함
  ↓
db_manager.save_state_log_with_summary(ep_num, state_data, summary)
  └─ INSERT OR REPLACE → 이전 state_data 덮어쓰기 ← 이전 에피소드 상태 손실
```

**핵심 문제**: 개별 변수(내공, 관계, 감정 등)는 변화 이력을 기록하지만, **에피소드별 전체 상태 스냅샷은 최신값만 유지**. 200화 장기 연재에서 1화 시점의 전체 상태 복원 불가.

---

## 6. Producer의 역할 범위

### **충돌 정보 명시적 포함: YES**

Producer(Chief Writer)는 다음 경로로 충돌 정보를 **명시적으로** 수신:

| 채널 | 내용 | 코드 위치 |
|------|------|---------|
| `director_feedback` | Director 심사 결과 텍스트 | chief_writer.py:898 |
| `failure_constraints` | 이전 REJECT action_items → "이전 REJECT 사유:\n- ..." | chief_writer.py:1374-1387 |
| `conflict_contract` | conflict_type, conflict_detail, expected_truth, truth_pins | chief_writer.py:55-84 |
| `prev_manuscripts_text` | 이전 30화 원고 전문 (진실의 원천) | chief_writer_context.py |
| `world_state_summary` | 세계 상태 요약 | chief_writer_context.py |
| `immutable_fact_section` | FactLedger 기반 불변 팩트 | chief_writer_context.py:207-214 |

**Structured Conflict Contract 구조** [chief_writer.py:55-152]:
```
conflicts: [{conflict_type, conflict_detail, expected_truth, source_episode}]
truth_pins: [{pin_key, expected, observed}]
rewrite_required_reasons: [str]
```

**결론**: Producer는 "lore + summary만 보고 스스로 해석"하는 것이 아니라, Director가 이미 검사한 결과를 **구조화된 계약서**로 받는다. 단, **Director가 검사하지 못한 충돌(lore/event/summary 간 사전 충돌)은 여전히 Producer가 직접 해석**해야 한다.

---

## 7. Director 개입 방식

### **Feedback = 상태 객체 수정 + 프롬프트 주입 (rerun 트리거만이 아님)**

#### 피드백 흐름

```
Director verdict 판정
  ↓
[REJECT] → reject_step.director_feedback 생성
[PASS]   → pass_disposition.director_feedback 생성
  ↓
loop_state.director_feedback = director_feedback          [stage4_orchestrator.py:1757, 1779]
  ↓
다음 라운드: interview_round.run(..., director_feedback)  [stage4_orchestrator.py:1700]
  ↓
writer_kwargs["director_feedback"] = director_feedback    [stage4_interview_round.py:3849]
  ↓
chief_writer._build_regeneration_feedback()               [chief_writer.py:1334-1372]
  ↓
_build_feedback_section(director_feedback)                [chief_writer_context.py:409-415]
  ↓
build_chief_writer_main_prompt(..., feedback_section=...) [chief_writer_prompts.py:157]
  ↓
"### [Director 피드백 - 반드시 반영]"                       ← 프롬프트 STEP 0.75에 삽입
  ↓
LLM 호출 (feedback 포함)
```

#### 핵심 특징

- **상태 정규화**: `_InterviewRoundLoopState.director_feedback` 필드에 저장, 다음 iteration에 carry-over [stage4_orchestrator.py:452-463]
- **프롬프트 주입**: `feedback_section`으로 구성, LLM 프롬프트의 STEP 0.75에 삽입
- **다중 레이어**: Regeneration Feedback (Director + 이전 시도 분석) + Strategy-Specific Feedback + Fix Pack Guidance
- **다음 에피소드에는 미반영**: feedback은 **같은 에피소드의 재시도 루프 내에서만** carry-over. 다음 에피소드로 넘어가면 `loop_state`가 초기화됨.

---

## 8. Rerun 발생 패턴

### 주요 원인 분류

| ErrorType | 설명 | 코드 위치 |
|-----------|------|---------|
| `CONSTRAINT_VIOLATION` | 제약 조건 위반 | adaptive_retry.py:42-54 |
| `QUALITY_ISSUE` | 밀도 부족, 개연성 | |
| `STRUCTURE_ERROR` | JSON 파싱 실패, 필수 키 누락 | |
| `CHARACTER_INCONSISTENCY` | 캐릭터 일관성 문제 | |
| `LOGIC_ERROR` | 논리적 모순 | |
| `SCOPE_OVERFLOW` | 범위 초과 | |

### 부분 수정(Patch) vs 전체 재생성 결정 로직

**Patch 가능 조건** [stage4_retry_runtime.py:123-142]:
1. `patch_enabled == True`
2. `fix_scope == "inplace"`
3. `fix_pack_contract.ready == True`
4. `provenance in {"runtime_backfilled", "runtime_synthesized"}`
5. `target_kind in {"entity_ref", "local_phrase", "local_sentence"}`

**Patch 불가능 → 전체 재생성**:
- `conflict_type`에 "continuity"와 "history" 동시 포함
- `truth_pins` 중 proper_noun_group, asset_state, capital_state, world_fact 계열
- `rewrite_required_reasons` 존재
- proper_noun 또는 history conflict type

### 재시도 에스컬레이션 파이프라인

```
REJECT
  ├─ fix_scope 판정: inplace vs partial vs full
  ├─ inplace 가능?
  │  ├─ YES → Patch 시도 (최대 2회, max_change_ratio 30%)
  │  │  ├─ 실패 → 전체 재생성으로 전환
  │  │  └─ 성공 → PASS_WITH_FIX
  │  └─ NO → 직접 전체 재생성
  └─ 최대 재시도 횟수 도달 → FINAL_REJECT
```

---

## 9. "정규화 레이어" 존재 여부 판단

| 질문 | 답변 | 근거 |
|------|------|------|
| 생성 전에 상태 충돌을 명시적으로 정리하는 단계가 있다 | **NO** | 포맷팅/구조화는 있지만 충돌 감지→해결 단계 없음 |
| 상태 우선순위 규칙이 코드로 정의되어 있다 | **NO** | 프롬프트 텍스트에 우선순위 명시되지만, 코드 레벨 선언적 규칙 없음 |
| producer는 상태 해석 없이 생성만 수행한다 | **NO** | Director가 검사한 충돌은 구조화 전달, 그 외 충돌은 Producer가 직접 해석 |
| 상태와 텍스트가 분리되어 관리된다 | **부분적 YES** | 감정/관계/플롯은 분리, 내공/부상/아이템은 혼합 (분리도 약 70%) |

---

## 해석 및 종합 진단

### 현재 구조 요약

```
[데이터 소스들]                    [정규화 단계]              [생성]
lore (bible)          ─┐
summary (prev_digest) ─┤
character state (HUD)  ─┤  ChiefWriterContextPackets    ChiefWriter
recent events          ─┤  (포맷팅/구조화만)        →    (LLM이 충돌 해석)
director feedback      ─┤  ↓                            ↓
blueprint             ─┤  build_chief_writer_main_prompt Director 심사
arc_doc               ─┤  (우선순위 명시, 섹션 분리)     ↓
world_state           ─┘                                PASS / REJECT
                                                         ↓ (REJECT 시)
[검증 레이어]                                            conflict_contract
TruthGate (advisory)                                    → 재시도 프롬프트에 주입
StateTextVerifier (advisory)
CrossAgentVerifier (단방향)
```

### 핵심 발견

1. **"포맷팅 정규화"는 존재하지만 "충돌 해결 정규화"는 부재**
   - 데이터를 구조적으로 merge하고 우선순위를 프롬프트에 명시하는 체계는 갖춰져 있음
   - 그러나 `lore`에서 "주인공은 A 소속"이고 `recent_event`에서 "주인공이 B로 이적"일 때, 이를 **코드 레벨에서 감지하고 해결하는 arbitration step은 없음**

2. **검증 레이어는 "사후 검증"이지 "사전 정규화"가 아님**
   - TruthGate, StateTextVerifier, CrossAgentVerifier 모두 **생성 후** 또는 **추출 후** 검증
   - 생성 **전**에 입력 데이터의 충돌을 감지하고 정리하는 단계는 없음

3. **Director feedback은 동일 에피소드 내 재시도에만 유효**
   - `loop_state`가 에피소드 경계에서 초기화되므로, Director가 발견한 문제가 다음 에피소드 생성에는 전달되지 않음
   - 이것이 **drift 누적의 구조적 원인** 중 하나일 수 있음

4. **state_logs 덮어쓰기 구조가 장기 drift 추적을 방해**
   - FactLedger는 100건까지 이력을 보존하지만, 에피소드별 전체 상태 스냅샷은 최신값만 유지
   - 200화 장기 연재에서 "언제부터 drift가 시작됐는지" 역추적 곤란

### Arbiter 필요성 판단

**YES — Arbiter/정규화 레이어 도입 검토 필요**

근거:
- NO 3개, 부분적 YES 1개 → "producer가 상태 해석까지 담당하는 구조"에 해당
- 현재 구조에서 drift/rerun 증가의 원인이 될 수 있는 지점:
  1. 생성 전 상태 소스 간 충돌 미감지
  2. Director feedback의 에피소드 경계 소실
  3. 에피소드별 전체 상태 이력 부재

### 도입 시 고려할 위치

```
[데이터 소스들] → [Arbiter/정규화 레이어] → [ChiefWriter 프롬프트 조립] → [생성]
                      ↑
                  여기에 삽입
                  - 소스 간 충돌 감지
                  - 우선순위 기반 해결
                  - 정규화된 단일 상태 dict 출력
                  - Director 이력 carry-over
```

---

## 파일 참조 인덱스

| 영역 | 핵심 파일 | 라인 |
|------|----------|------|
| 컨텍스트 조립 | `chief_writer_context.py` | 116-284 |
| 프롬프트 구조 | `chief_writer_prompts.py` | 50-227 |
| Packet Assembly | `chief_writer_context_packets.py` | 174-413 |
| 충돌 감지 (사후) | `truth_gate.py` | 79-319 |
| 상태-텍스트 검증 | `state_text_verifier.py` | 119-140 |
| 교차 검증 | `cross_agent_verifier.py` | 165-269 |
| 상태 추적 | `state_tracker.py` | 132-200 |
| 팩트 원장 | `fact_ledger.py` | 227-600 |
| 상태 변화 추적 | `state_delta_tracker.py` | 77-159 |
| 세계 상태 관리 | `world_state.py` | 118-250 |
| Director 피드백 | `stage4_orchestrator.py` | 452-463, 1757, 1779 |
| 재시도 런타임 | `stage4_retry_runtime.py` | 123-632 |
| Conflict Contract | `chief_writer.py` | 55-152 |
| Producer 재생성 | `chief_writer.py` | 1334-1387 |
| DB 상태 저장 | `db_manager.py` | 1459-1508 |
