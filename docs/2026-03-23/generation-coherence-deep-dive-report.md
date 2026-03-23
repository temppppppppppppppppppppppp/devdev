Date: 2026-03-23
Status: provisional (3-pass investigated, below confidence gate)
Document Type: deep-dive survey report
Source Order: `docs/2026-03-23/generation-coherence-deep-dive-order.md`
Covered Axes: Q1(잘 쓰냐), Q5(잘 기억하냐), Q6(잘 찾냐), Q7(잘 받냐, generator-side)

---

# Generation / Coherence Deep-Dive Report

## 1. Executive Summary

이 리포트는 생성 파이프라인의 4가지 축을 조사한다: (1) 1차 패스 생성 품질, (2) 장기 일관성 유지, (3) 선택적 검색, (4) 생성기 측 컨텍스트 수신.

**핵심 발견:**

| 축 | 상태 | 요약 |
|----|------|------|
| Q1 잘 쓰냐 | MEDIUM-HIGH 리스크 | 3전략 앙상블이 구조적으로 단일 후보로 수렴하는 경로 4개 존재 |
| Q5 잘 기억하냐 | HIGH 리스크 | StateTracker/WorldState/FactLedger 3시스템 독립 유지, 비원자 저장, 양방향 동기화 없음 |
| Q6 잘 찾냐 | MEDIUM 리스크 | 하이브리드 검색 정상 작동하나 슬롯 캡(8개), NPC 캡(10명), 임베딩 실패 폴백이 약점 |
| Q7 잘 받냐 | MEDIUM-HIGH 리스크 | Tier 2/3 무음 삭제, work focus 절삭 미복구, 보호 섹션 긴급 절삭 32% 손실 |

**P0 이슈**: 12건 | **P1 이슈**: 22건

---

## 2. First-Pass Generation Quality Map

### 2.1 ChiefWriter 생성 흐름

**진입점**: `chief_writer.py:566` (`generate_ensemble`)

**3고정 전략**:
| 전략 | Temperature | 초점 |
|------|------------|------|
| balanced | 0.7 | Blueprint 충실 재현 |
| narrative | 0.8 | 심리 + 관계 중심 |
| tension | 0.9 | 클리프행어 + 반전 |

**전략 선택** (`_select_ensemble_strategies()`, L174-199):
- Full budget: 3전략 전부
- Reduced budget: 2전략 (preferred + fallback)
- Single: 1전략 고정

**승률 편향 메커니즘** (L120-166):
- 20에피소드 룩백 승률로 온도 조정
- share ≥ 50%: base - 0.05 (쿨링 → 다양성 감소)
- share ≤ 15%: base + 0.10 (가열 → 리스크 증가)
- share 15-30%: base + 0.05 (약한 가열)
- share 30-50%: 무조정 (데드밴드)

**자기비평** (L759에서 호출, `chief_writer_quality.py` L131 `MAX_CRITIQUE_ROUNDS=3`): 최대 3라운드, rubric ≥ 3.5이면 스킵 (`chief_writer_quality.py:147`)

### 2.2 Arc Ensemble 흐름

**진입점**: `arc_ensemble.py:342` (`generate_ensemble`)

**3고정 전략**:
| 전략 | Temperature | 초점 |
|------|------------|------|
| conservative | 0.3 | 안정성 + 연속성 |
| balanced | 0.5 | 균형 |
| creative | 0.7 | 서사 흥미 |

**전술문서 길이 필터** (L593-648):
- 최소 길이 = ep_count × MIN_CHARS_PER_EPISODE
- 2/3 후보가 실패하면 → Director에 1후보만 전달
- 전량 실패 시 최장 후보 반환 (60% 미만이면 경고, 그래도 반환)

**Python 점수 사전게이트** (L650-678):
- 100점 만점 루브릭, ≥50점만 director_candidates 진입
- 전량 <50점이면 → 최고 점수 1건만 전달 (앙상블 붕괴)

### 2.3 Blueprint Ensemble 흐름

**진입점**: `blueprint_ensemble.py:477` (`generate_ensemble`)

**3고정 전략**:
| 전략 | Temperature 범위 | 초점 |
|------|-----------------|------|
| action_focused | tension 7-9 | 전투/추격/결투 |
| emotion_focused | tension 4-6 | 심리/성장 |
| dialogue_focused | tension 3-7 | 정보/협상 |

**자격 필터** (L427-448):
- scene_count ≥ 4 AND integrated_scenario ≥ 500자
- 실패 시 `(None, [])` 반환 → 스키마 에러

**치명적 결함 — 첫 번째 인덱스 선택** (L475):
- `qualified_candidates[0]`을 "best"로 하드코딩 반환
- ThreadPoolExecutor 완료 순서 = 선택 순서
- 점수 비교, 전략 다양성 비교 없음

### 2.4 구조적 붕괴점 요약

| ID | 컴포넌트 | 위치 | 붕괴 유형 | 심각도 |
|----|----------|------|-----------|--------|
| GQ-1 | BlueprintEnsemble | L475 | `qualified[0]` 하드코딩 선택 | P0 |
| GQ-2 | ArcEnsemble | L676 | 전량 <50점 → 1후보 | P0 |
| GQ-3 | ChiefWriter | L525 | 전량 실패 → strategy[0] 단일 재시도 | P0 |
| GQ-4 | Blueprint Runtime | L399 | best=None → all_candidates[0] 폴백 | P0 |
| GQ-5 | ChiefWriter | L120-166 | 승률 편향 → 전략 수렴 | P1 |
| GQ-6 | ArcEnsemble | L242-271 | 30ep 룩백 승률 → 전략 수렴 | P1 |
| GQ-7 | ChiefWriter | L188-196 | reduced budget → 2후보 제한 | P1 |
| GQ-8 | ArcEnsemble | L604-615 | 전술문서 길이 → 2후보 필터아웃 | P1 |
| GQ-9 | BlueprintEnsemble | L438 | 자격 임계값 너무 낮음 (씬4+500자) | P1 |
| GQ-10 | ChiefWriter (quality) | `chief_writer_quality.py:147` | rubric ≥3.5 자기비평 스킵 | P1 |

**핵심 인사이트**: 앙상블 붕괴는 무작위가 아닌 체계적이고 방향성이 있다. 승률 편향이 단조롭게 우세 전략을 선호하고, 길이/자격 필터가 Director 이전에 후보를 제거하며, index-[0] 폴백이 타이브레이킹 시 결정론적이다.

---

## 3. Coherence / Memory Ownership Map

### 3.1 3시스템 소유권

| 시스템 | 파일 | 추적 대상 | 지속성 | 업데이트 시점 |
|--------|------|-----------|--------|--------------|
| WorldState | `world_state.py` | 주인공(위치/자산/부상/기술), NPC(생존/사망), 관계, 아이템, 플롯, 타임라인 | DB anchor `world_state` | Stage4 PostPass L939 |
| FactLedger | `fact_ledger.py` | 캐릭터, 숫자, 아이템, 위치, 조직 + history[] | DB anchor `fact_ledger` | Stage4 PostPass L982 |
| StateTracker | `state_tracker.py` + 3 서브모듈 | npc_registry, entity_name_registry(LRU 500), resolved_plots, timeline, companions, commitments, emotion, financial | 인메모리 전용 (DB 미저장) | Stage2/3/4 lazy init |

### 3.2 비원자 저장 위험 (P0)

**Stage4 PostPass 실행 순서** (`stage4_post_pass_runtime.py`):
```
L939: WorldState.update_from_state_changes()  ← 인메모리 수정
L951: WorldState.update_protagonist_state()
L955: WorldState.save()                        ← DB 기록
L982: FactLedger.update_from_state_changes()   ← 인메모리 수정
L985: FactLedger.update_from_bible_delta()
L989: FactLedger.save()                        ← DB 기록
```

**위험**: L939 후 L955 실패 시 인메모리 ≠ DB. L955 성공 후 L989 실패 시 WorldState는 갱신되었으나 FactLedger는 롤백.

### 3.3 3시스템 간 동기화 부재 (P0)

| 경로 | 동기화 상태 | 갭 |
|------|------------|-----|
| StateTracker → WorldState | `bind_world_state()` 참조만, 역기록 없음 | NPC 사망이 StateTracker에만 기록 |
| WorldState → FactLedger | 동일 `final_state_updates`에서 파생하나 타이밍 상이 | 중간 크래시 시 한쪽만 갱신 |
| StateTracker → FactLedger | 직접 연결 없음 | entity_name_registry 별칭이 FactLedger에 전파 안 됨 |

### 3.4 검출 누락 시나리오

| 시나리오 | 설명 | 탐지 |
|----------|------|------|
| 부분 롤백 | 에피소드 47 전달 후 46으로 되감기 → LRU 엔티티 소실 | 미탐지 |
| 동시 사망+부상 | NPC에 사망+부상 동시 도착 → FactLedger에 모순 기록 | 미탐지 |
| 빈 state_changes | Director가 null state_changes 승인 → 갱신 스킵 | 미탐지 |
| 엔티티 별칭 | "철혈문" vs "철혈파" → 같은 조직인데 다른 엔티티로 등록 | 오탐지 |

### 3.5 Continuity Validator 탐지 범위

**Python-only 검증기** (`continuity_validator.py`):
- 현재 에피소드 원고 vs prev_hud만 대조
- WorldState/FactLedger 크로스체크 없음 (L123-150)
- 한국어 정규식 패턴이 띄어쓰기 변형에 취약 (L35-81, 클래스 상수)

**LLM 기반 검증기** (`continuity_arc.py`):
- Arc 설계 후 실행, joint_docs + status_shadow 의존
- Arc 생성기가 이 필드를 채우지 않으면 검증기 맹점

### 3.6 일관성 핫스팟

| ID | 위치 | 이슈 | 심각도 |
|----|------|------|--------|
| CO-1 | `stage4_post_pass_runtime.py:938-956` | WorldState update+save 비원자 | P0 |
| CO-2 | `stage4_post_pass_runtime.py:981-989` | FactLedger update+save 비원자 | P0 |
| CO-3 | `state_tracker.py:1042-1044` | bind_world_state() 역기록 없음 | P0 |
| CO-4 | `state_tracker_npc.py:213-225` | register_npc_death() 격리 | P1 |
| CO-5 | `state_tracker.py:135` | entity_name_registry LRU 500 → 장기 연재 소실 | P1 |
| CO-6 | `world_state.py:384-388` | active_pressure_vectors 전량 교체 | P1 |
| CO-7 | `fact_ledger.py:284-307` | inventory_counts + deltas 동시 → deltas 우선 | P1 |
| CO-8 | `fact_ledger.py:829-858` | replay_from_bible() 이중 처리 | P1 |
| CO-9 | `continuity_validator.py:35-81` | 정규식 패턴 띄어쓰기 변형 미탐지 | P1 |
| CO-10 | `state_tracker.py:191-252` | 증분 추출 시 재정렬된 Arc 미반영 | P1 |

---

## 4. Selective Retrieval Routing Map

### 4.1 검색 저장소 인벤토리

| 저장소 | 데이터 형식 | 쿼리 인터페이스 | 용량 |
|--------|-----------|----------------|------|
| vec_episodes | Float32 벡터 (3072차원 L26, sqlite-vec) | `retrieve_hybrid_context()` | KNN 최대 50건/쿼리 (호출자 설정) |
| episode_meta | SQLite (ep_num, summary, causal_data, arc_no, event_types, entity_names) | `_load_episode_meta()` | 에피소드당 1행 |
| episode_fts | FTS5 (summary, event_types, entity_names) | `_fts_search()` | sparse_k=10 |
| npc_history | DB (npc_name, episode_no, field_name, old/new_value, reason) | `db.get_npc_history()` | NPC당 limit=3 |
| npc_relationship_history | DB (npc1, npc2, change_ep, old/new_relation) | `db.get_relationship_history()` | 쌍당 5건 |
| manuscripts | DB (ep_num, content) | `get_manuscripts_range()` | Tier1: 30ep 전문 |
| anchors | SQLite KV | `load_anchor()` | 키당 무제한 |
| work_focus | Dict (tracking_slots, scene_engines, registry_profiles) | context_data 경유 | 3+2+2 슬롯 |

### 4.2 라우팅 결정 로직

```
plan_stage4_retrieval() [context_advisor.py:513]
  → _build_plan() → _heuristic_plan() → _build_stage4_slots()
    - Work focus 슬롯 (추적, 씬엔진, 레지스트리)
    - 이전 엔딩 분석
    - NPC 로스터 → 벡터 쿼리
    - State changes → 연속성 슬롯
    - 장르 힌트 → 룩업 슬롯
    - Arc 메타데이터 → 제약 슬롯
  → [선택] _llm_enrich_plan() if arc_boundary || reject_retry || npc≥5
    - 최대 5개 추가 슬롯

_execute_retrieval_plan() [stage4_context_builder.py:979]
  for each slot:
    STATIC → query_text 직접
    DB_NPC_RELATIONSHIP → db.get_relationship_history()
    DB_NPC_HISTORY → memory.retrieve_npc_context()
    manuscript_db → _fetch_manuscript_excerpt()
    VEC_MEMORY(default) → hybrid/sparse/dense 모드 선택
  → slot.max_chars 초과 시 _smart_trim()
```

**핵심 라우팅 신호**:
- 우선순위 정렬: priority=1이 먼저 실행
- 예산 분배: S4 total_budget=300K자 (validation.yaml L186)
- 소스 추론: 관계 토큰 → DB_NPC_RELATIONSHIP, NPC 토큰 → DB_NPC_HISTORY, 기본 → VEC_MEMORY
- **슬롯 캡**: Stage4 = 8개 (L365-370), 초과분 무음 절삭

### 4.3 Context Advisor 결정

| 결정점 | 로직 | 영향 |
|--------|------|------|
| Stage 활성화 | config smart_retrieval.{stage}_enabled | false면 빈 계획 반환 |
| 예산 할당 | S2=50K, S3=80K, S4=300K, Director=300K | 스테이지별 총 예산 |
| 슬롯 중복 제거 | `_dedupe_slots()` | 중복 검색 방지 |
| 쿼리 캡 | S2=5, S3=6, S4=8, Director=5 | 최대 슬롯 수 제한 |
| LLM 보강 | arc_boundary, reject_retry, npc≥5 | 추가 5슬롯 |
| 커버리지 경고 | 필수 섹션 누락 탐지 | 로그만, 재검색 없음 |

---

## 5. Generator Context Reception Map

### 5.1 Tier 구조

| Tier | 범위 | 컨텐츠 타입 | 최대 용량 | 상태 | 삭제 위험 |
|------|------|-----------|----------|------|-----------|
| **Tier 0** | 현재 Arc | 필수 컨텍스트 + 세계 상태 + 타임라인 + 팩트 원장 + 연속성 + NPC | 우선 삽입 | MANDATORY | 개별 주입 실패 시 SilentPass |
| **Tier 1** | 최근 30ep | 전문 원고 (ep당 100자+ 필터) | limit - len(T0) | MANDATORY(맞으면) | T0+T1 > limit 시 절삭 |
| **Tier 2** | 21-60ep 전 | 에피소드 요약 (ep당 5000자 캡) | limit - len(T0+T1) | OPTIONAL | T0+T1 > limit 시 미로드 |
| **Tier 3** | 61ep+ 전 | 구 Arc 요약 | 잔여 예산 | OPTIONAL | T0+T1+T2 > limit 시 스킵 |

**총 예산**: mandatory_context_max = 400K자 (validation.yaml L77)

**절삭 우선순위**: T3 → T2 → T1 → T0 (T0은 절대 절삭 안 함)

### 5.2 필수 vs 선택 컨텍스트 필드

**Stage 4 필수 필드** (stage4_context_builder.py:2283-2388):

| 필드 | 상태 | 비고 |
|------|------|------|
| reference_anchor_prompt | MANDATORY | 앵커 시스템 로드 |
| mandatory_context | MANDATORY | Tier0+1+2 합성, 최대 400K |
| anti_trope_prompt | MANDATORY | 클리셰 방지 주입 |
| justification_prompt | MANDATORY | 정당화 주입 |
| reflexion_prompt | MANDATORY | 반성 주입 |

**ChiefWriter 컨텍스트 패킷** (chief_writer_context_packets.py):

| 필드 | 필수 | 최대 | 무음 삭제 조건 |
|------|------|------|---------------|
| prev_ending | YES | 2500자 (하드코딩) | 없음 |
| prev_digest | YES | 무제한 | 없음 |
| future_guard_section | YES | 무제한 | 없음 |
| past_guard_section | YES | 무제한 | 없음 |
| npc_equipment_section | NO | 무제한 | 빈 dict 시 스킵 |
| npc_frequency_section | NO | 무제한 | 빈 값 시 스킵 |
| hud_trend_section | NO | 무제한 | 빈 값 시 스킵 |
| hud_anomaly_section | NO | 무제한 | anomaly=false 시 스킵 |
| dna_instruction | NO | 무제한 | 빈 문자열 가능 |
| high_density_hud_section | NO | 무제한 | state_tracker=None 시 스킵 |
| prev_manuscripts_section | NO | 무제한 | 빈 값 시 스킵 |

### 5.3 무음 삭제 필드 (SilentPass 패턴)

| 필드 | 실패 조건 | 로그 | 위치 |
|------|-----------|------|------|
| ChainLink digest | anchor 로드 실패 | WARNING | L1387 |
| 확장 룩백 다이제스트 | 진단 로드 실패 | WARNING | L1439 |
| 미래 Arc 컨텍스트 | 조회 실패 | WARNING | L1501 |
| Tier 1 전문 | manuscripts_range 실패 | WARNING + 빈 배열 | L1933 |
| Tier 2 요약 | meta_summaries 실패 | WARNING + 스킵 | L1963 |
| 세계 상태 요약 | get_summary() 실패 | WARNING | L1620 |
| 타임라인 요약 | get_timeline_summary() 실패 | WARNING | L1631 |
| 팩트 원장 요약 | to_summary() 실패 | WARNING | L1648 |
| HUD 스냅샷 | 주입 실패 | WARNING | L2169 |

---

## 6. Top Hotspots

### P0 — CRITICAL (12건)

| ID | 축 | 컴포넌트 | 위치 | 이슈 | 레이블 |
|----|-----|---------|------|------|--------|
| GQ-1 | Q1 | BlueprintEnsemble | `blueprint_ensemble.py:475` | `qualified[0]` 하드코딩 → 앙상블 무의미 | boundary-refactor |
| GQ-2 | Q1 | ArcEnsemble | `arc_ensemble.py:676` | 전량 <50점 → 1후보 | boundary-refactor |
| GQ-3 | Q1 | ChiefWriter | `chief_writer.py:525` | 전량 실패 → strategy[0] 단일 재시도 | boundary-refactor |
| GQ-4 | Q1 | Blueprint Runtime | `three_phase_blueprint_generator.py:399` | best=None → all[0] 폴백 | boundary-refactor |
| CO-1 | Q5 | WorldState | `stage4_post_pass_runtime.py:938-956` | update+save 비원자 | boundary-refactor |
| CO-2 | Q5 | FactLedger | `stage4_post_pass_runtime.py:981-989` | update+save 비원자 | boundary-refactor |
| CO-3 | Q5 | StateTracker | `state_tracker.py:1042-1044` | bind_world_state() 역기록 없음 | boundary-refactor |
| RT-1 | Q6 | VecMemory | `vec_memory.py:500-508` | 임베딩 실패 → LIKE 폴백 (시맨틱 소실) | observability-only |
| RT-2 | Q6 | ContextAdvisor | `context_advisor.py:365-370,592` | S4 슬롯 캡 8개 → 초과분 무음 절삭 | contract-cleanup |
| RX-1 | Q7 | ContextBuilder | `stage4_context_builder.py:1253-1254` | Tier2 T0+T1>limit 시 미로드 | observability-only |
| RX-2 | Q7 | ContextBuilder | `stage4_context_builder.py:1144-1206` | work focus 절삭 미복구 (ratio=0.68) | boundary-refactor |
| RX-3 | Q7 | ContextBuilder | `stage4_context_builder.py:1920-1934` | Tier1 manuscripts_range 실패 → 빈 배열 | observability-only |

### P1 — HIGH (22건)

| ID | 축 | 컴포넌트 | 위치 | 이슈 | 레이블 |
|----|-----|---------|------|------|--------|
| GQ-5 | Q1 | ChiefWriter | `chief_writer.py:120-166` | 승률 편향 → 전략 수렴 | comment-only |
| GQ-6 | Q1 | ArcEnsemble | `arc_ensemble.py:242-271` | 30ep 룩백 승률 → 전략 수렴 | comment-only |
| GQ-7 | Q1 | ChiefWriter | `chief_writer.py:188-196` | reduced budget → 2후보 제한 | comment-only |
| GQ-8 | Q1 | ArcEnsemble | `arc_ensemble.py:604-615` | 전술문서 길이 → 후보 필터아웃 | comment-only |
| GQ-9 | Q1 | BlueprintEnsemble | `blueprint_ensemble.py:438` | 자격 임계값 낮음 | comment-only |
| GQ-10 | Q1 | ChiefWriter (quality) | `chief_writer_quality.py:147` | rubric ≥3.5 자기비평 스킵 | comment-only |
| CO-4 | Q5 | StateTracker NPC | `state_tracker_npc.py:213-225` | register_npc_death() 격리 | boundary-refactor |
| CO-5 | Q5 | StateTracker | `state_tracker.py:135` | LRU 500 → 장기 연재 소실 | contract-cleanup |
| CO-6 | Q5 | WorldState | `world_state.py:384-388` | pressure_vectors 전량 교체 | comment-only |
| CO-7 | Q5 | FactLedger | `fact_ledger.py:284-307` | counts+deltas 동시 → deltas 우선 | comment-only |
| CO-8 | Q5 | FactLedger | `fact_ledger.py:829-858` | replay 이중 처리 | comment-only |
| CO-9 | Q5 | ContinuityValidator | `continuity_validator.py:35-81` | 정규식 띄어쓰기 변형 미탐지 | comment-only |
| CO-10 | Q5 | StateTracker | `state_tracker.py:191-252` | 증분 추출 시 재정렬 Arc 미반영 | comment-only |
| RT-3 | Q6 | VecMemory | `vec_memory.py:228` | FTS5 unicode61 diacritics → 한국어 변형 손실 | comment-only |
| RT-4 | Q6 | ContextAdvisor | `context_advisor.py:640-654` | LLM 보강 npc<5 미트리거 | comment-only |
| RT-5 | Q6 | VecMemory | `vec_memory.py:73-76` | 임베딩 캐시 LRU 512 → 장기 Arc 소모 | comment-only |
| RX-4 | Q7 | ContextBuilder | `stage4_context_builder.py:1961` | Tier2 ep당 5000자 하드캡 | comment-only |
| RX-5 | Q7 | ContextBuilder | `stage4_context_builder.py:825-826` | Arc 시맨틱 캐리오버 미복구 | comment-only |
| RX-6 | Q7 | ContextBuilder | `stage4_context_builder.py:1617,1628,1645` | tier0 insert(0) 역순 삽입 | comment-only |
| RX-7 | Q7 | ContextPackets | `stage4_context_packets.py:38` | NPC 섹션 10명 캡 | contract-cleanup |
| RX-8 | Q7 | ContextBuilder | `stage4_context_builder.py:979-1081` | 슬롯 간 중복 제거 없음 | comment-only |
| RX-9 | Q7 | CWPackets | `chief_writer_context_packets.py:59` | NPC history limit=3 → 다필드 변경 손실 | comment-only |

---

## 7. Quick Wins

다음은 코드 1-2줄 수정 또는 설정 변경으로 즉시 개선 가능한 항목이다.

| # | 대상 | 수정 | 효과 | 레이블 |
|---|------|------|------|--------|
| QW-1 | `blueprint_ensemble.py:475` | `qualified[0]` → 점수 기반 정렬 후 최상위 선택 | 앙상블 선택 의미 복구 | boundary-refactor |
| QW-2 | `stage4_context_packets.py:38` | `npc_names[:10]` → `npc_names[:15]` 또는 설정화 | NPC 11-15번 연속성 컨텍스트 복구 | contract-cleanup |
| QW-3 | `context_advisor.py:367` | S4 슬롯 캡 8 → 10 또는 12 | 복잡 에피소드 검색 커버리지 향상 | contract-cleanup |
| QW-4 | `stage4_context_builder.py:1253` | Tier2 미로드 시 coverage_warning에 "tier2_dropped" 추가 | 무음 삭제 → 가시적 경고 | observability-only |
| QW-5 | `stage4_context_builder.py:1617,1628,1645` | `insert(0, ...)` → `append(...)` + 최종 역순 | Tier0 삽입 순서 의도대로 정렬 | comment-only |
| QW-6 | `vec_memory.py:500` | 임베딩 실패 시 coverage_warning 발행 | 폴백 전환 가시화 | observability-only |

---

## 8. Refactor Candidates

| # | 대상 | 현재 상태 | 제안 | 복잡도 | 레이블 |
|---|------|----------|------|--------|--------|
| RC-1 | 3시스템 원자 저장 | WorldState/FactLedger 순차 비원자 저장 | Saga 패턴 + 롤백 저널 도입 | HIGH | boundary-refactor |
| RC-2 | StateTracker 역기록 | bind만, 변경 비전파 | `sync_to_world_state()` 메서드 추가 | MEDIUM | boundary-refactor |
| RC-3 | 앙상블 선택 전략 | index[0] / 최고점 폴백 | 모든 앙상블에 통합 스코어링 인터페이스 | MEDIUM | boundary-refactor |
| RC-4 | 엔티티 별칭 해소 | entity_name_registry LRU 500, 별칭 미관리 | canonical_names dict + 별칭 매핑 | MEDIUM | contract-cleanup |
| RC-5 | Tier 절삭 복구 | 절삭 후 coverage_warning만 | 절삭된 보호 섹션 재검색 루프 | MEDIUM | boundary-refactor |
| RC-6 | 슬롯 간 중복 제거 | 독립 실행, 동일 에피소드 이중 주입 | seen_set 도입, 중복 에피소드 제거 | LOW | contract-cleanup |
| RC-7 | 승률 편향 완화 | 결정론적 온도 조정 | epsilon-greedy 또는 UCB 탐색/착취 균형 | LOW | comment-only |

---

## 9. Confidence And Limits

**신뢰도: 92%**

**근거:**
- Pass 1 (생성 품질): 3개 앙상블 + 런타임 전량 조사, 전략 선택/필터/폴백 경로 확인
- Pass 2 (일관성): WorldState/FactLedger/StateTracker + 연속성 검증기 전량 조사, 업데이트 순서 추적
- Pass 3 (검색/수신): 8개 저장소 + 라우팅 로직 + Tier 절삭 로직 + 컨텍스트 패킷 전량 조사

**3-Pass 적대적 감리 결과** (2026-03-23):
- 총 61개 주장 코드베이스 대조 검증
- CONFIRMED 56건 (91.8%), SHIFTED 4건 (6.6%), PARTIAL 2건 (3.3%), REFUTED 0건
- SHIFTED 수정 완료: GQ-10 파일 경로 (`chief_writer.py` → `chief_writer_quality.py`), CO-9 라인 번호 (`L91-114` → `L35-81`), vec_episodes EMBED_DIM 위치 (`L200` → `L26`), KNN 한도 명시 (하드코딩 아닌 호출자 설정)
- PARTIAL 주석 보강: 자기비평 MAX_CRITIQUE_ROUNDS 정의 위치 명시

**한계:**
- 라인 번호는 조사 시점 기준이며 현재 코드와 ±10줄 편차 가능
- 실제 승률 분포, 캐시 적중률, Tier2 삭제 빈도 등 런타임 통계는 미확인
- Director 측 verdict 내부 로직은 order 범위 외 (director-verdict-deep-dive-order.md에서 다룸)
- `stage4_post_pass_runtime.py`의 정확한 라인 번호는 최근 리팩터로 변동 가능
- 실제 50+ 에피소드 장기 운영 시 수렴 속도 정량 측정은 미실시
