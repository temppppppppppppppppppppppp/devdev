# Stage 2 Forward-Consistency Fix — Execution SSOT

Date: 2026-03-29
Status: ready-for-execution (3-pass audited, confidence 96%)
Canonical Path: `docs/2026-03-29/stage2-forward-consistency-fix-execution-ssot.md`
Temp Mirror Path: (not mirrored — existing temp queue active)
Source Survey Doc: `docs/2026-03-29/stage2-forward-consistency-bounded-survey.md`
Baseline Commit: `dae2dd2f`

## 1. Bug Families

| ID | Family | Severity | Frequency |
|---|---|---|---|
| **B-1** | Resurrected item (소모 후 부활) | CRITICAL | 3/5 arcs (6-10 batch) |
| **B-2** | Missing [시작 상태] silent pass | HIGH | Validator returns valid=True |
| **B-3** | Equipment Sync trusts LLM-populated arc_end_state | HIGH | Every arc boundary |
| **B-4** | No cumulative destruction ledger | HIGH | Architectural gap |
| **B-5** | Within-arc forward inconsistency | MEDIUM | 파쇄 후 재등장 same arc |
| **B-6** | PWF patch doesn't enforce equipment carryover | MEDIUM | Every PWF cycle |

## 2. Authoritative State Contract (Proposed)

현재: 5개 병렬 source, 단일 authority 없음.
제안: **Python-computed carryover가 authority, LLM output은 candidate**

```
Authority Chain:
  1. prev_arc.joint_docs.physical_inventory          (arc 종료 시점 소지품)
  2. MINUS prev_arc.status_shadow.item_consumption   (소모/파쇄 기록)
  3. PLUS  prev_arc.state_constraints.items_acquired  (신규 획득)
  4. = COMPUTED inherited_inventory                   (Python이 계산)
  5. LLM이 생성한 arc_start_state.equipment는 COMPUTED와 대조 후 override
```

이 contract가 적용되면:
- `arc_end_state.equipment`은 LLM advisory (참고용)
- `joint_docs.physical_inventory`은 arc 종료 시점의 snapshot (seed)
- `status_shadow.item_consumption`은 파쇄/소모 truth
- Python이 (seed - consumed + acquired)를 계산하여 다음 arc에 강제 주입

## 3. Likely Root Cause

**단일 원인**: Equipment Sync(stage2_finalizer.py L1261-1284)가 `arc_end_state.equipment`을 authority로 사용하지만, 이 필드는 LLM이 생성한 것으로 `status_shadow.item_consumption`의 소모 기록을 반영하지 않을 수 있음.

**보조 원인**:
- `state_extractor.py` cumulative extraction에 누적 소모 ledger 없음
- `arc_draft_validator.py`에 소지품 연속성 fail-close 없음
- `stage2_finalizer.py L1125`: inventory 계승이 조건부 (이미 채워져 있으면 skip)

## 4. Touched-File Candidate Set

| File | Change | Risk | Family |
|------|--------|------|--------|
| `modules/core/stage2_finalizer.py` | **Primary**: Equipment Sync를 Python-computed carryover로 교체 | Medium — 핵심 경로 | B-1, B-3 |
| `modules/domain/agents/arc_draft_validator.py` | `arc_start_state` 누락 시 WARNING→REJECT 또는 stronger auto-fix | Low — 검증 강화 | B-2 |
| `modules/domain/agents/state_extractor.py` | `extract_cumulative_state()`에 누적 소모 ledger 추가 | Medium — 새 필드 | B-4 |
| `modules/core/prompt_builder.py` | forbidden list에 누적 소모 아이템 추가 | Low — 프롬프트 보강 | B-1, B-5 |
| `modules/domain/agents/four_phase_arc_generator.py` | PWF patch 시 equipment carryover 강제 (location처럼) | Low — L915-925 패턴 확장 | B-6 |

## 5. Repair-Mode Taxonomy

| Mode | 적용 Family | 설명 | 위험 |
|------|------------|------|------|
| **Deterministic Override** | B-1, B-3 | Equipment Sync에서 Python-computed inventory로 LLM output 강제 교체 | Low — 이미 Equipment Sync가 override하는 구조 |
| **Fail-Close** | B-2 | arc_start_state 완전 누락 시 REJECT (advisory_issues가 아닌 critical로 승격) | Low — 재생성으로 해결 가능 |
| **Ledger Accumulation** | B-4 | 전체 arc chain의 item_consumption을 누적하여 "destroyed items" set 유지 | Medium — 새 데이터 구조 |
| **Prompt Reinforcement** | B-5 | forbidden list에 destroyed items 추가하여 LLM이 부활시키지 않게 유도 | Low — 프롬프트만 변경 |
| **Patch Carryover Enforcement** | B-6 | PWF patch 후 Equipment Sync 재실행 | Low — 기존 함수 재호출 |

## 6. Implementation Order

### Phase 1: Deterministic Carryover (B-1, B-3) — Highest Impact

**Seam**: `stage2_finalizer.py` L1261-1284 (Equipment Sync)

현재:
```python
correct_equip = prev_end.get("equipment")  # LLM이 생성한 값 — 신뢰 불가
if correct_equip is None:
    correct_equip = prev_arc.get("joint_docs", {}).get("physical_inventory", [])
```

제안:
```python
# Python-computed carryover: physical_inventory - item_consumption + items_acquired
prev_inventory = prev_arc.get("joint_docs", {}).get("physical_inventory", [])
prev_consumed = prev_arc.get("status_shadow", {}).get("item_consumption", [])
prev_acquired = prev_arc.get("state_constraints", {}).get("items_acquired", [])
correct_equip = _compute_inherited_inventory(prev_inventory, prev_consumed, prev_acquired)
```

`_compute_inherited_inventory()`: prev_inventory에서 consumed 아이템 이름을 빼고, acquired를 더함. `stage2_finalizer.py L1138-1164`에 이미 유사 로직 존재 — 통합 가능.

### Phase 2: Cumulative Destruction Ledger (B-4)

**Seam**: `state_extractor.py` `extract_cumulative_state()`

현재: `forbidden_in_next_arc.cannot_acquire_again` = 현재 소지품만.
제안: `all_consumed_items` set을 누적하여 `cannot_acquire_again`에 포함.

```python
all_consumed = set()
for arc in all_arcs:
    consumed = arc.get("status_shadow", {}).get("item_consumption", [])
    all_consumed.update(_item_names(consumed))
result["forbidden_in_next_arc"]["cannot_acquire_again"].extend(all_consumed)
```

### Phase 3: Validator Fail-Close (B-2)

**Seam**: `arc_draft_validator.py` L209-211

현재: `arc_start_state` 누락 = WARNING.
제안: `arc_start_state` AND `arc_end_state` 둘 다 누락이면 CRITICAL (reject 후보). 하나만 누락이면 WARNING 유지.

### Phase 4: Prompt Reinforcement (B-5)

**Seam**: `prompt_builder.py` L683-690

현재: `cannot_acquire_again` = 현재 소지품.
제안: `cannot_acquire_again` += 누적 destroyed items (Phase 2의 ledger 사용).

### Phase 5: PWF Patch Enforcement (B-6)

**Seam**: `four_phase_arc_generator.py` L915-925

현재: location만 강제.
제안: equipment도 강제 (동일 패턴).

## 7. Validation Matrix

| Check | Method | Expected |
|---|---|---|
| Resurrection: 파쇄 아이템 부활 차단 | 0_1 arcs 6-10 재생성 canary | 파쇄된 아이템이 이후 arc start state에 없음 |
| Equipment Sync: Python computed | Unit test: prev_inventory=[A,B,C], consumed=[A], acquired=[D] → [B,C,D] | Deterministic output |
| Fail-close: missing arc_start_state | Unit test: arc with empty state_constraints → CRITICAL | valid=False |
| Cumulative ledger: destroyed items | Unit test: 3-arc chain, item destroyed in arc 1 → forbidden in arc 3 | cannot_acquire_again includes destroyed item |
| Regression: existing tests | `pytest tests/ -k stage2` | No regression |
| Ruff | `ruff check` on touched files | 0 violations |

## 8. Closure Criteria

- [ ] Phase 1 적용 후 canary re-run: resurrection 0건
- [ ] Phase 2 적용 후: `cannot_acquire_again`에 destroyed items 포함 확인
- [ ] Phase 3 적용 후: missing arc_start_state → REJECT
- [ ] Existing tests pass
- [ ] Ruff clean
- [ ] 3-pass code audit on touched lines

## 9. Non-Goals

- Stage 3/4 carryover 개선 (별도 scope)
- LLM에게 "미래를 보게" 만드는 것 (invariant 강화가 목표)
- DB schema 변경 (Python computation으로 해결)
- joint_docs.physical_inventory 구조 변경 (기존 format 유지)
- 전체 arc 재생성 (canary로 검증, 실전은 별도 판단)
