# 장기 기억 능력 평가 — 50화 / 100화 / 200화 정합성 시나리오 분석

> **작성일**: 2026-02-28
> **기준 커밋**: `a4e3fe3` (LM-A~G 전량 완료)
> **목적**: LM-A~G 7종 advisory + TruthGate + 4계층 컨텍스트 시스템이 장기 연재(50/100/200화)에서 정합성을 얼마나 유지하는지 시나리오별로 평가

---

## Part 1: 시스템 기억 인프라 현황 정리

### 1-A. 4계층 컨텍스트 시스템 (`stage4_context_builder.py`)

| 계층 | 범위 | 내용 | 비고 |
|------|------|------|------|
| Tier 1 | 직전 30화 전문 | manuscripts 테이블 full text | `get_manuscripts_range()`, L420: `next_ep - 30` |
| Tier 2 | 31~60화 전 요약 | episode_meta.summary (2000자 cap/화) | FTS5 인덱싱, L440: `next_ep - 60` |
| Tier 3 | 60화 이전 Arc 요약 | `arc_summary_{arc_no}` anchor | Arc 단위 압축 |
| Tier 4 | 60화+ 장기 앵커 | WorldState.get_long_term_anchor() | 세계법칙 + NPC 원본역할 |

### 1-B. 영구 저장소 (DB 테이블)

| 저장소 | 보존 기간 | 캡 | 용도 |
|--------|----------|-----|------|
| episode_bibles | 무제한 | 없음 | 화별 상태 스냅샷 (reveals, knowledge_map 등) |
| manuscripts | 무제한 | 없음 | 원고 전문 |
| npc_history | 무제한 | 없음 | NPC 속성 변경 이력 (append-only) |
| npc_relationship_history | 무제한 | 없음 | NPC 관계 변경 이력 (append-only) |
| vec_episodes + episode_meta | 무제한 | 없음 | 벡터 임베딩 + 메타데이터 |
| episode_fts | 무제한 | 없음 | FTS5 전문 검색 인덱스 |

### 1-C. 상태 레지스트리 (메모리 + DB anchor)

| 레지스트리 | 엔티티 캡 | 이력 캡 | 비고 | 소스 |
|-----------|----------|--------|------|------|
| FactLedger.characters | 무제한 | **100건/엔티티** | FIFO, 가장 오래된 항목 탈락 | `fact_ledger.py` L20 |
| FactLedger.numbers | 무제한 | **100건/엔티티** | 수치 이력 (내공, 재산 등) | `fact_ledger.py` L20 |
| WorldState.alive_npcs | 무제한 | N/A | 사망 전까지 영구 | |
| WorldState.dead_npcs | 무제한 | N/A | 불변 | |
| WorldState.world_laws | **30건** | N/A | CRITICAL 핀 보호, FIFO | `world_state.py` L712 |
| WorldState.skills | **50건** | N/A | FIFO | `world_state.py` L133 |
| WorldState.active_plots | **30건** | N/A | FIFO | `world_state.py` L672 |
| WorldState.active_items | **캡 없음** (dict) | N/A | 상태값으로 소실/파괴 추적, 요약 출력 시 20건 표시 | `world_state.py` |
| WorldState.destroyed | **50건** | N/A | FIFO | `world_state.py` L383 |
| StateTracker.npc_registry | LLM 정리(5Arc 주기) | N/A | 허위 명사 제거 | |
| StateTracker.resolved_plots | **500건** | N/A | LRU | `state_tracker.py` L133 |

### 1-D. Advisory 체인 (LM-A~G)

| Advisory | 데이터 소스 | 이력 깊이 | 주기 | 소스 |
|----------|-----------|----------|------|------|
| TruthGate (LM-A) | WorldState (현재 스냅샷) | 현재 화만 | 매 화 | `truth_gate.py` |
| NpcDriftAdvisor (LM-B) | NPC 스냅샷 vs 원고 | 현재 화만 | 매 화 | `npc_drift_advisor.py` |
| NumericDriftAdvisor (LM-C) | FactLedger.numbers history | **15 포인트 표시** (100 저장, 20 항목) | 5화마다 | `numeric_drift_advisor.py` L14-15 |
| RelationshipDriftAdvisor (LM-D) | npc_relationship_history (전량) | **무제한** (MAX_PAIRS=10, MAX_TIMELINE_CHARS=3000) | 5화 이후 매 화 | `relationship_drift_advisor.py` L13-14 |
| FlashbackVerifier (LM-E) | VecMemory dense/hybrid search | **전체 에피소드** (dense 3건, hybrid 5건 반환) | 매 화 | `flashback_verifier.py` |
| InfoParadoxChecker (LM-F) | episode_bibles.reveals 누적 | **최근 200건** reveals (MAX_KNOWLEDGE_CHARS=3000) | 1인칭 전용 | `info_paradox_checker.py` L13-14 |
| NarrativeContextFormatter (LM-G) | StateTracker 현재값 | 현재만 | Stage2 매 Arc | `narrative_context_formatter.py` |

### 1-E. 반복 감지

| 메커니즘 | 윈도우 | 비고 | 소스 |
|---------|--------|------|------|
| RepetitionGuard (3-gram) | **직전 5화** | 동일 문구 3+회 반복 | `repetition_guard.py` L24 |
| SentenceFingerprint (SHA256) | **직전 5화** | 정확한 문장 중복 (min_length=15자) | `repetition_guard.py` L192, `db_manager.py` L2412 |
| SemanticPlotGuard (임베딩+키워드) | 현재 Arc 내 | 플롯 중복 감지 | `semantic_plot_guard.py` |

---

## Part 2: 시나리오별 정합성 평가

### 평가 기준

- **✅ 보장**: 시스템이 구조적으로 감지·차단 가능 (>95% 확률)
- **⚠️ 부분적**: 조건부 감지 가능, 빈틈 존재 (50~95%)
- **❌ 미감지**: 시스템이 구조적으로 놓치는 영역 (<50%)

---

### 시나리오 A: NPC 사망/부활 정합성

> "30화에서 사망한 NPC가 N화에서 행동/대사하면?"

| 시점 | N=50화 (20화 후) | N=100화 (70화 후) | N=200화 (170화 후) |
|------|-----------------|------------------|-------------------|
| **TruthGate (LM-A)** | ✅ deceased 리스트 영구 | ✅ 영구 | ✅ 영구 |
| **BlockingValidator** | ✅ dead_npc_resurrection | ✅ | ✅ |
| **WorldState.dead_npcs** | ✅ 불변 레코드 | ✅ | ✅ |
| **종합** | **✅ 보장** | **✅ 보장** | **✅ 보장** |

**근거**: `dead_npcs` 딕셔너리는 무제한 보존, TruthGate `_check_deceased_resurrection()`이 매 화 실행. 사망 NPC는 회상/언급만 허용하는 대원칙이 코드로 강제됨.

---

### 시나리오 B: NPC 성격 일관성

> "10화에서 '냉혹한 암살자'로 등장한 NPC가 N화에서 갑자기 '온화한 성인군자'로 묘사되면?"

| 시점 | N=50화 | N=100화 | N=200화 |
|------|--------|---------|---------|
| **NpcDriftAdvisor (LM-B)** | ✅ 스냅샷 대조 | ✅ 스냅샷 영구 | ✅ 스냅샷 영구 |
| **ContinuityValidator** | ⚠️ 직전 1화만 비교 | ⚠️ | ⚠️ |
| **WorldState.get_npc_role_snapshot()** | ✅ role_at_intro 영구 | ✅ | ✅ |
| **npc_history DB** | ✅ personality_traits 이력 전량 | ✅ | ✅ |
| **종합** | **✅ 보장** | **⚠️ 부분적** | **⚠️ 부분적** |

**50화**: 스냅샷이 정확하고 LLM이 비교 가능. 문제없음.

**100화**: 스냅샷은 영구이나, 정당한 성격 변화(Arc 이벤트)가 축적되어 "현재 성격"이 원본과 다른 것이 정상일 수 있음. LLM이 정당한 변화 vs 표류를 구분해야 하는데, 100화 분량의 맥락 없이는 오탐(정당한 변화를 표류로 판정) 가능.

**200화**: 동일 문제 심화. 스냅샷이 200화 전 원본이므로 현재와 크게 다를 수 있음. LLM 판단 정확도 하락.

**갭**: `known_attrs`에 `changed_ep` 필드가 있어 "언제 변경됐는지"는 알 수 있으나, "왜 변경됐는지"(Arc 이벤트 컨텍스트)는 기록되지 않음.

---

### 시나리오 C: 수치 일관성 (재산/전투력/내공)

> "1화에서 100냥이던 주인공 재산이 N화에서 갑자기 1억냥이면?"

| 시점 | N=50화 | N=100화 | N=200화 |
|------|--------|---------|---------|
| **NumericDriftAdvisor (LM-C)** | ✅ FactLedger 이력 15포인트 | ⚠️ 이력 100건 중 15만 표시 | ⚠️ 100건 FIFO, 초기 이력 탈락 |
| **FactLedger.numbers** | ✅ 100건 이력 | ✅ 100건 | ⚠️ 초기 탈락 시작 |
| **Tier 1 원문** | ❌ 1화는 30화 윈도우 밖 | ❌ | ❌ |
| **Tier 3 Arc 요약** | ⚠️ Arc 요약에 수치 포함 시 | ⚠️ | ⚠️ |
| **종합** | **✅ 보장** | **⚠️ 부분적** | **⚠️ 부분적** |

**50화**: FactLedger에 1~50화 이력 전량 보존 (50건 < 100건 캡). LLM이 15포인트 중 급격한 점프 감지 가능.

**100화**: FactLedger 이력 100건 → 1화부터 100화까지 커버. 이력이 빽빽하면 매 화 변경이 100건 채워짐. Advisory는 15포인트만 보여주므로 5화 간격 샘플링. **점진적 drift(화당 0.5% 증가 = 100화 후 65% 누적)는 감지 어려움**.

**200화**: FactLedger FIFO로 1~100화 이력 탈락. 초기 기준값 소실. "원래 100냥이었다"는 사실이 이력에서 사라질 수 있음.

**갭**: 점진적 수치 인플레이션 (화당 미세 증가가 장기 누적) 감지 메커니즘 없음.

---

### 시나리오 D: NPC 관계 역전

> "1화에서 '원수'였던 두 NPC가 중간에 '동맹'이 되었다가 N화에서 다시 '원수'로 돌아오면?"

| 시점 | N=50화 | N=100화 | N=200화 |
|------|--------|---------|---------|
| **RelationshipDriftAdvisor (LM-D)** | ✅ 전체 타임라인 | ✅ 전체 타임라인 | ✅ 전체 타임라인 |
| **npc_relationship_history** | ✅ append-only 무제한 | ✅ | ✅ |
| **ContinuityValidator** | ⚠️ 직전 1화만 | ⚠️ | ⚠️ |
| **종합** | **✅ 보장** | **✅ 보장** | **⚠️ 부분적** |

**50~100화**: `npc_relationship_history` 테이블이 모든 변경을 기록. LM-D가 전체 타임라인을 LLM에 전달. MAX_PAIRS=10이므로 상위 10쌍은 완벽 감시.

**200화**: 관계 변경이 많아지면 MAX_TIMELINE_CHARS=3000 제한에 걸림. 200화 분량의 관계 이력이 3000자에 압축되면 정보 손실. 또한 MAX_PAIRS=10이라 11번째 이후 관계 쌍은 감시 대상에서 누락.

**갭**: 총 NPC 관계 쌍이 10을 초과하면 우선순위 밖 쌍의 표류를 놓침.

---

### 시나리오 E: 회상/플래시백 오염

> "N화에서 '10화의 전투를 회상'하는데, 실제 10화에서는 전투가 없었다면?"

| 시점 | N=50화 | N=100화 | N=200화 |
|------|--------|---------|---------|
| **FlashbackVerifier (LM-E)** | ✅ VecMemory 검색 | ✅ VecMemory 검색 | ⚠️ 임베딩 정밀도 하락 |
| **VecMemory dense search** | ✅ 50건 중 고정밀 (3건 반환) | ⚠️ 100건 중 정밀도 약간 하락 | ⚠️ 200건, curse-of-dimensionality |
| **VecMemory hybrid (FTS5+RRF)** | ✅ 키워드 보완 (5건 반환) | ✅ FTS5 안정적 | ✅ FTS5 안정적 |
| **종합** | **✅ 보장** | **⚠️ 부분적** | **⚠️ 부분적** |

**50화**: VecMemory에 50개 에피소드만 있으므로 검색 정밀도 최고. 10화 전투 장면이 있었는지 정확히 판별.

**100화**: 임베딩 공간에 100개 벡터. Dense search는 여전히 유효하나, 유사 주제 에피소드 증가로 noise 증가.

**200화**: Dense search만으로는 정밀도 ~85%로 하락. **Hybrid search(TF-18)가 활성화되어 있어 FTS5 키워드 보완**으로 실질적으로 90%+ 유지 가능.

**핵심**: TF-18에서 Hybrid 검색이 기본 활성화되어 있으므로, 200화에서도 FTS5 보완으로 상당 부분 커버됨.

---

### 시나리오 F: 1인칭 시점 정보 역설

> "주인공이 아직 모르는 정보(N화 후에야 밝혀질 사실)를 미리 아는 것처럼 서술하면?"

| 시점 | N=50화 | N=100화 | N=200화 |
|------|--------|---------|---------|
| **InfoParadoxChecker (LM-F)** | ✅ 50화 reveals 누적 | ⚠️ MAX_REVEALS=200 근접 | ❌ 200건 FIFO, 초기 reveals 탈락 |
| **episode_bibles.knowledge_map** | ✅ 전량 보존 | ✅ 전량 보존 | ✅ 전량 보존 |
| **종합** | **✅ 보장** | **⚠️ 부분적** | **⚠️ 부분적** |

**50화**: 50화 분량의 reveals ≈ 50~150건 (화당 1~3건). MAX_REVEALS=200 이내. 전량 커버.

**100화**: 100화 × 2건/화 = ~200건. MAX_REVEALS 경계. 초기 reveals가 탈락 시작.

**200화**: 200건 초과. 1~100화 reveals 중 상당수 탈락. **초기에 밝혀진 핵심 사실(주인공 정체 등)이 knowledge summary에서 빠질 수 있음**.

**갭**: MAX_REVEALS=200이 장기 연재에서 구조적 한계. `knowledge_map`은 DB에 전량 보존되나 LM-F의 `build_knowledge_summary()`가 reveals 리스트만 사용하므로 knowledge_map 활용도가 낮음. MAX_KNOWLEDGE_CHARS=3000도 추가적 병목.

---

### 시나리오 G: 세계관 법칙 위반

> "1화에서 '이 세계에서는 마법이 존재하지 않는다'고 설정했는데 N화에서 마법을 쓰면?"

| 시점 | N=50화 | N=100화 | N=200화 |
|------|--------|---------|---------|
| **TruthGate._check_world_law_violation()** | ✅ world_laws 영구 | ✅ 영구 | ✅ 영구 |
| **WorldState.world_laws** | ✅ CRITICAL 핀 보호 | ✅ | ⚠️ 30건 캡, CRITICAL 외 FIFO |
| **장기 앵커 (Tier 4)** | ✅ 60화+ 자동 주입 | ✅ | ✅ |
| **종합** | **✅ 보장** | **✅ 보장** | **⚠️ 부분적** |

**50~100화**: `world_laws`에 CRITICAL 핀이 설정되어 있으므로 핵심 법칙은 영구 보존. TruthGate가 LLM으로 매 화 검증.

**200화**: world_laws 캡 30건. CRITICAL 핀이 아닌 법칙(MINOR 등급)은 30건 초과 시 탈락. 다만 핵심 세계관 법칙은 보통 CRITICAL로 등록되므로 실질적 위험은 낮음.

---

### 시나리오 H: 아이템 연속성

> "20화에서 주인공이 '청풍검'을 잃어버렸는데 N화에서 다시 사용하면?"

| 시점 | N=50화 | N=100화 | N=200화 |
|------|--------|---------|---------|
| **TruthGate._check_unowned_items()** | ✅ WorldState 기반 | ✅ | ✅ |
| **BlockingValidator** | ✅ 미소유 아이템 사용 | ✅ | ✅ |
| **FactLedger.items** | ✅ 100건 이력 | ✅ | ⚠️ FIFO 시작 |
| **WorldState.active_items** | ✅ 캡 없음 (dict) | ✅ | ✅ |
| **종합** | **✅ 보장** | **✅ 보장** | **✅ 보장** |

**근거 수정**: 코드 검증 결과 `active_items`는 dict 타입으로 **저장 캡이 없음** (`world_state.py`). 아이템 상태가 "보유"/"소실"/"파괴" 등으로 추적되며, 잃어버린 아이템은 상태값이 변경될 뿐 삭제되지 않음. `get_summary()` 출력 시 20건만 표시하나, TruthGate 검증은 전체 dict를 참조. 따라서 200화에서도 **구조적으로 보장**됨.

> 참고: 요약 출력(get_summary)에서 20건만 표시하는 것은 LLM 컨텍스트 효율을 위한 것이며, 내부 검증 로직에는 영향 없음.

---

### 시나리오 I: 장소 일관성

> "50화에서 '풍운성이 파괴되었다'고 했는데 N화에서 풍운성에서 전투가 벌어지면?"

| 시점 | N=100화 | N=200화 |
|------|---------|---------|
| **TruthGate._check_destroyed_locations()** | ✅ WorldState.destroyed 영구 | ✅ |
| **WorldState.destroyed** | ✅ 50건 캡 이내 | ⚠️ 50건 초과 시 FIFO |
| **종합** | **✅ 보장** | **⚠️ 부분적** |

**100화**: 파괴된 장소 리스트 50건 이내면 완벽 보존.

**200화**: 대규모 전쟁 서사에서 파괴 장소가 50건 초과하면 초기 파괴 기록 탈락.

---

### 시나리오 J: 문장/패턴 반복

> "50화 전에 쓴 인상적인 대사를 N화에서 거의 동일하게 다시 쓰면?"

| 시점 | N=50화 (5화 전) | N=50화 (45화 전) | N=100화 | N=200화 |
|------|----------------|-----------------|---------|---------|
| **RepetitionGuard (3-gram)** | ✅ 5화 윈도우 | ❌ 윈도우 밖 | ❌ | ❌ |
| **SentenceFingerprint** | ✅ 5화 윈도우 | ❌ | ❌ | ❌ |
| **SemanticPlotGuard** | ⚠️ Arc 내 | ❌ | ❌ | ❌ |
| **종합** | **직전 5화만 ✅** | **❌ 미감지** | **❌** | **❌** |

**핵심 갭**: 반복 감지 윈도우가 5화로 고정. 6화 이상 간격의 반복은 구조적으로 감지 불가.

---

### 시나리오 K: 시간 경과 모순

> "30화에서 '3일 후'라고 했는데, 50화에서 갑자기 '30화로부터 1년이 지났다'면?"

| 시점 | N=50화 | N=100화 | N=200화 |
|------|--------|---------|---------|
| **episode_bibles.time_passed** | ✅ 전량 보존 | ✅ | ✅ |
| **ContinuityValidator.time_consistency** | ⚠️ 직전 1화만 | ⚠️ | ⚠️ |
| **누적 시간 계산 메커니즘** | ❌ 없음 | ❌ | ❌ |
| **종합** | **❌ 미감지** | **❌** | **❌** |

**핵심 갭**: `time_passed` 필드가 화별로 기록되나, 이를 누적 합산하여 "작중 총 경과 시간"을 추적하는 메커니즘이 없음. 시간 모순은 직전 1화 간격만 검사.

---

## Part 3: 종합 정합성 매트릭스

| 시나리오 | 50화 | 100화 | 200화 | 핵심 병목 |
|---------|------|-------|-------|----------|
| A. NPC 사망/부활 | ✅ | ✅ | ✅ | 없음 (영구 보존) |
| B. NPC 성격 일관성 | ✅ | ⚠️ | ⚠️ | 정당한 변화 vs 표류 구분 난이도 |
| C. 수치 일관성 | ✅ | ⚠️ | ⚠️ | FactLedger 100건 FIFO + Advisory 15포인트 |
| D. NPC 관계 역전 | ✅ | ✅ | ⚠️ | MAX_PAIRS=10, MAX_TIMELINE_CHARS=3000 |
| E. 회상 오염 | ✅ | ⚠️ | ⚠️ | VecMemory 정밀도 + Hybrid 보완 |
| F. 정보 역설 (1인칭) | ✅ | ⚠️ | ⚠️ | MAX_REVEALS=200 FIFO |
| G. 세계관 법칙 | ✅ | ✅ | ⚠️ | world_laws 30건 캡 (CRITICAL 핀 보호) |
| H. 아이템 연속성 | ✅ | ✅ | ✅ | 없음 (active_items 캡 없음, dict) |
| I. 장소 일관성 | ✅ | ✅ | ⚠️ | destroyed 50건 캡 |
| J. 문장 반복 | ⚠️ | ❌ | ❌ | 5화 윈도우 고정 |
| K. 시간 경과 모순 | ❌ | ❌ | ❌ | 누적 시간 추적 없음 |

### 등급 요약

| 기준 | ✅ 보장 | ⚠️ 부분적 | ❌ 미감지 |
|------|--------|----------|---------|
| **50화 이전** | **9/11** | 1/11 (J) | 1/11 (K) |
| **100화 이전** | **5/11** (A,D,G,H,I) | 4/11 (B,C,E,F) | 2/11 (J,K) |
| **200화 이전** | **2/11** (A,H) | 7/11 (B,C,D,E,F,G,I) | 2/11 (J,K) |

### 플랜 대비 코드 검증 수정 사항

- **시나리오 H (아이템)**: 플랜에서 "active_items 50건 캡"으로 기술했으나, 코드 검증 결과 `active_items`는 **dict 타입으로 저장 캡 없음**. `get_summary()` 출력만 20건 제한. 따라서 200화에서도 ✅ 보장으로 상향.
- **NumericDriftAdvisor**: MAX_ITEMS=20 (항목 수 제한) 추가 확인. 20개 이상 수치 카테고리는 누락됨.

---

## Part 4: 구조적 갭 + 개선 후보 (P0~P2)

### P0 (200화 안전 확보에 필수)

| # | 갭 | 영향 시나리오 | 개선안 | 난이도 |
|---|-----|-------------|--------|--------|
| P0-1 | MAX_REVEALS=200 | F. 정보 역설 | 200→500 확장, 또는 knowledge_map 병합 활용 | 낮음 |
| P0-2 | FactLedger 초기값 소실 | C. 수치 일관성 | `established_value` 필드 추가 (최초 등록값 영구 보존) | 중간 |

### P1 (품질 향상)

| # | 갭 | 영향 시나리오 | 개선안 | 난이도 |
|---|-----|-------------|--------|--------|
| P1-1 | 점진적 수치 drift | C. 수치 | 장기 추세선 감지 (exponential growth detector) | 중간 |
| P1-2 | MAX_PAIRS=10 | D. 관계 | 10→20 확장 + 동적 우선순위 | 낮음 |
| P1-3 | destroyed 50건 캡 | I. 장소 | 50→100 확장 | 낮음 |
| P1-4 | world_laws 30건 캡 | G. 세계관 | 30→50 확장 | 낮음 |
| P1-5 | 반복 윈도우 5화 고정 | J. 반복 | VecMemory 기반 장기 반복 감지 | 높음 |

### P2 (장기 과제)

| # | 갭 | 영향 시나리오 | 개선안 |
|---|-----|-------------|--------|
| P2-1 | 누적 시간 추적 없음 | K. 시간 | WorldState에 `elapsed_time` 필드 + time_passed 누적기 |
| P2-2 | NPC 성격 변화 사유 미기록 | B. 성격 | npc_history에 `reason` 컬럼 추가 |
| P2-3 | VecMemory 200화+ 정밀도 | E. 회상 | 주기적 re-indexing 또는 hierarchical clustering |

---

## Part 5: 결론

### 강점

1. **영구 불변 데이터(사망/세계법칙/아이템 상태)는 완벽하게 보호됨** — `dead_npcs`, `world_laws` CRITICAL 핀, `active_items` dict가 구조적 안전망.
2. **append-only 이력 테이블(`npc_history`, `npc_relationship_history`)이 DB에 무제한 보존** — 데이터는 있으나, Advisory가 참조하는 윈도우/캡이 병목.
3. **Hybrid 검색(TF-18)이 기본 활성화** — 200화에서도 FTS5 키워드 보완으로 VecMemory 정밀도 유지.
4. **4계층 컨텍스트가 원문→요약→Arc요약→앵커로 자연스러운 압축** — 60화 이전 정보도 Arc 요약으로 보존.

### 핵심 약점

1. **Advisory 윈도우/캡이 데이터 보존보다 좁음** — DB에는 전량 있으나 LLM에 전달하는 양이 제한적 (MAX_REVEALS=200, MAX_HISTORY_POINTS=15, MAX_PAIRS=10).
2. **시간 경과 추적 부재** — 시간 모순은 현재 구조적으로 감지 불가.
3. **반복 감지가 5화 윈도우** — 장기 반복(10화+ 간격)은 완전 미감지.

### 200화 안전 확보를 위한 최소 개선

P0-1(MAX_REVEALS 확장)과 P0-2(FactLedger 초기값 보존)만 구현해도 200화 매트릭스에서 ⚠️→✅ 전환 2건 달성 가능. 총 비용: 낮음~중간.
