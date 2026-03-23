Date: 2026-03-23
Document Type: Q5 R2 evidence manifest
Terminal: T5

---

## Source File Inventory (R2)

| File | LOC | Read Coverage | R2 Delta |
|------|-----|---------------|----------|
| `modules/core/world_state.py` | ~1,312 | Full | 재검증: FIFO 절삭 11+ sites all silent |
| `modules/core/fact_ledger.py` | ~859 | Full | 재검증: 4 upsert exact key, 5 category FIFO silent |
| `modules/domain/agents/state_tracker.py` | ~1,669 | Partial | bind_world_state, entity_name_registry 확인 |
| `modules/domain/agents/state_tracker_npc.py` | ~2,205 | Full | LLM fallback L752, revive L1376-1414, NPC-NPC L1687-1708 |
| `modules/validation/continuity_validator.py` | ~1,265 | Full | 재검증: WS/FL 참조 0건, growth_keywords Korean confirmed |
| `modules/domain/agents/continuity_arc.py` | ~1,096 | Partial | 교차 참조용 |
| `modules/core/stage4_post_pass_runtime.py` | ~1,200 | L920-1117 | **R2 핵심**: atomic snapshot/rollback mechanism 검증 |
| `modules/core/stage2_orchestrator.py` | ~1,731 | L281-361 | P1-5 shifted: world_state slot 존재 확인 |
| `modules/core/stage4_interview_round.py` | L3369-3399 | ContinuityValidator call site | P0-3 persists 확인 |

---

## Fresh-Run DB Evidence (`projects/0_0323/project_data.db`)

### WorldState Anchor

```
key: world_state
size: 2,933 bytes
version: 1
last_updated_ep: 3
alive_npcs: 8 (한시우[주인공], 한정호, 박 여사, 한태민, 김 실장, 박 차장, 부동산 중개인, 개인 시계 딜러)
dead_npcs: 0
active_items: 2 (ThinkPad T60, flip phone)
active_plots: 0  ← DORMANT
timeline: 0       ← DORMANT
destroyed: 0
pressure_vectors: 2 (ep3 ending_hook, expected_ending)
world_notes: 0    ← DORMANT
world_laws: 0     ← DORMANT
motivations: 0    ← DORMANT
promises: 0       ← DORMANT
```

### FactLedger Anchor

```
key: fact_ledger
size: 1,988 bytes
characters: 8 (박 여사[4], 한정호[6], 김 실장[3], 한태민[2], 박 차장[2], 부동산 중개인[2], 개인 시계 딜러[2], 유성증권 동료 직원들[1])
items: 2
locations: 0      ← NOT EXTRACTED
organizations: 0  ← NOT EXTRACTED
numbers: 1 (capital, 1 history entry)
```

History format: flat string `"ep3: 관계 변화: -> 목격자"` (not dict)

### ChainLink Anchors

```
chain_link_1: 1,263 bytes
  cliffhanger: "아버지의 서재 문이 열리며 한정호가 모습을 드러낸다..."
  pending_actions: 5
  emotional_state: present

chain_link_2: 1,468 bytes
  cliffhanger: "한정호의 눈이 가늘어지며 전화기를 들어올린다..."
  pending_actions: 4
  emotional_state: present

chain_link_3: 1,573 bytes
  cliffhanger: "한태민이 문 앞에 서 있다..."
  pending_actions: 5
  emotional_state: present
```

### StateLogs

```
ep1: capital=0, wealth=0, total_assets=0
ep2: capital=2,000,000,000, wealth=0, total_assets=0    ← INCONSISTENCY
ep3: capital=2,015,487,250, wealth=2,015,487,250, total_assets=2,015,487,250  ← CONVERGED
```

### Entity Name Parity

```
WorldState alive_npcs: {한시우, 한정호, 박 여사, 한태민, 김 실장, 박 차장, 부동산 중개인, 개인 시계 딜러}
FactLedger characters:  {한시우, 한정호, 박 여사, 한태민, 김 실장, 박 차장, 부동산 중개인, 유성증권 동료 직원들, 개인 시계 딜러}

Note: "유성증권 동료 직원들" is in FactLedger but not in WorldState alive_npcs
      "한시우" is in FactLedger but is the protagonist, not tracked in alive_npcs
Result: functional parity for NPC names (protagonist/group entries expected to differ)
```

---

## R1→R2 Finding Anchor Cross-Reference

### P0-1 → F-1 (SHIFTED)

```
R1 anchor: stage4_post_pass_runtime.py:1070-1117
R2 anchor: stage4_post_pass_runtime.py:1070-1117 (unchanged location)
R2 new anchors:
  L920-932: _capture_atomic_metadata_snapshots() — deepcopy snapshots
  L1019-1068: _handle_atomic_metadata_rollback() — best-effort rollback
  L1088: meta_db.transaction() attempt
  L1091: sequential_mode fallback with WARNING
```

### P0-2 (PERSISTS)

```
R1 anchor: fact_ledger.py:504-596
R2 anchor: fact_ledger.py:504-595 (minor line shift)
  _upsert_character L508: chars[name]
  _upsert_item L540: items[name]
  _upsert_location L564: locs[name]
  _upsert_org L584: orgs[name]
  update_number L416: numbers[key]
```

### P0-3 (PERSISTS)

```
R1 anchor: continuity_validator.py:129, stage4_interview_round.py:3349-3390
R2 anchor: continuity_validator.py:83-88 (constructor), 123-174 (validate)
R2 call site: stage4_interview_round.py:3369-3399
Grep result: 0 references to world_state or fact_ledger in continuity_validator.py
```

### P0-4 (PERSISTS)

```
R1 anchor: state_tracker_npc.py:751-752
R2 anchor: state_tracker_npc.py:745-752
  if not self.tracker._llm_client or not candidates:
      return candidates  # unfiltered
```

### P1-5 (SHIFTED)

```
R1 anchor: stage2_orchestrator.py:281-361 (no world_state)
R2 anchor: stage2_context.py L141 (world_state slot exists)
R2 anchor: stage2_orchestrator.py L338 (bind_world_state call)
R2 gap: four_phase_arc_generator.py L1024,1107,1192 (DB independent load)
```

### P1-7 (STALE)

```
R1 anchor: continuity_validator.py:1009-1018
R2 anchor: continuity_validator.py:1009-1018
Current content:
  growth_keywords = (
      "성장", "변화", "깨달", "반성", "후회", "각성", "결심", "다짐",
  )
All Korean, no mojibake. Bug claim invalid.
```

---

## T-Report Cross-Reference Absorption

| T-Report | Finding | Q5 Absorption |
|----------|---------|---------------|
| T1 F-2/F-3 | reject_reason [:500] 절삭 | Q4/Q8 영역, Q5 참고만 |
| T2 F-5/F-6 | stage_attempts textual metadata loss | Q8 영역, Q5 진단 간접 제약 |
| T10 F1 | Blueprint time_flow date contamination | WorldState timeline 미사용(F-5)과 결합 시 시간 일관성 이중 취약 |
| T10 F2 | Scene detection false-positive | Q5 직접 무관 |
| GenCoherence CO-1/2/3 | 비원자 저장 + StateTracker 역기록 | R1 P0-1과 정합, F-1에서 shifted 재확인 |
| GenCoherence CO-5 | entity_name_registry LRU 500 | R1 P2-2와 일치 |
| GenCoherence CO-9 | 정규식 띄어쓰기 변형 | Q5 장기 연재에서 NPC 이름 변형 미탐지 위험 |
