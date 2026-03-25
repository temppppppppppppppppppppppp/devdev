# T8 Validator Signal Quality -- Evidence Ledger

Date: 2026-03-24
Lane: T8 -- Validator Signal Quality
Status: final
Parent Report: `docs/2026-03-24/opus-live-run-residual/t8-validator-signal-quality.md`

---

## A. [V66.1] Warning Full Ledger (43 instances)

### A1. Threat Carryover Drift ("직전 화의 지속 압박/위협이 opening 초반에서 감지되지 않음") -- 30 instances

| # | Ep | Rd | Cand | Verdict Change |
|---|----|----|------|----------------|
| 1 | 2 | R1 | B | No |
| 2 | 2 | R1 | C | No |
| 3 | 2 | R3 | A | No |
| 4 | 2 | R3 | B | No |
| 5 | 2 | R4 | A | No (PASS) |
| 6 | 2 | R4 | B | No |
| 7 | 2 | R4 | C | No |
| 8 | 3 | R1 | A | No |
| 9 | 3 | R1 | B | No (x2) |
| 10 | 3 | R1 | C | No (x2) |
| 11 | 3 | R2 | A | No (x2, PASS) |
| 12 | 4 | R1 | A | No (x2) |
| 13 | 4 | R1 | B | No |
| 14 | 4 | R1 | C | No (x2) |
| 15 | 5 | R1 | A | No |
| 16 | 5 | R1 | B | No |
| 17 | 5 | R1 | C | No |
| 18 | 5 | R3 | A | No |
| 19 | 5 | R3 | B | No |
| 20 | 6 | R1 | A | No |
| 21 | 6 | R1 | B | No |
| 22 | 6 | R1 | C | No |
| 23 | 6 | R2 | A | No |
| 24 | 6 | R3 | A | No |
| 25 | 6 | R3 | B | No |
| 26 | 6 | R3 | C | No |
| 27 | 7 | R1 | B | No |
| 28 | 7 | R1 | C | No |
| 29 | 8 | R1 | B | No |

**Code source**: `continuity_validator.py:435-465` -- `_check_active_pressure_continuity()`
- Severity: always WARNING
- `passed`: always True
- Mechanism: extracts `active_pressure_vectors` from prev_hud, checks cue_term overlap in first 1000 chars of manuscript

### A2. Re-acquisition ("이미 소유한 X을(를) 다시 획득하려 함") -- 8 instances

| # | Ep | Rd | Cand | Item | Verdict Change |
|---|----|----|------|------|----------------|
| 1 | 2 | R1 | B | 가죽 노트 (x2) | No |
| 2 | 2 | R1 | C | 가죽 노트 (x2) | No |
| 3 | 2 | R4 | A | 휴대전화 | No (PASS) |
| 4 | 2 | R4 | B | 가죽 노트 (x2) | No |
| 5 | 8 | R1 | B | 휴대전화 (x2) | No |

**Code source**: `continuity_validator.py:475-635` -- `_check_item_continuity()`
- Severity: CRITICAL (goes to violations list)
- But: only when `duplicate_acquisition` type. Actually in this run, these appear as warnings, not violations, suggesting the item continuity check may have a softer path for re-acquisition vs duplicate-acquisition.

### A3. Location Change ("위치 변화가 감지됨. 이동 경위 묘사 권장") -- 5 instances

| # | Ep | Rd | Cand | Verdict Change |
|---|----|----|------|----------------|
| 1 | 5 | R1 | A | No |
| 2 | 7 | R1 | A | No |
| 3 | 7 | R1 | B | No |
| 4 | 7 | R1 | C | No |
| 5 | 8 | R1 | B | No |

**Code source**: `continuity_validator.py:888-899` -- `location_jump` type, severity INFO

### A4. Season Contradiction -- 1 instance

| # | Ep | Rd | Cand | Verdict Change |
|---|----|----|------|----------------|
| 1 | 1 | R1 | post-PASS | No |

**Code source**: `continuity_validator.py:1161-1219` -- `_check_time_consistency()` external time_warning

---

## B. Post-Select Conflict Full Ledger (6 conflicts, 6/6 caused REJECT)

### B1. EP2 R1 -- Trust Provenance (어머니 vs 조부)

- **IFC conflict type**: `committed_state_regression`
- **LLM check**: `check_manuscript_history_conflicts` returned CONFLICT (CRITICAL severity)
- **Artifact truth**: `rejected_best__A_balanced.txt` L86: "조부님께서 제 앞으로 남겨주신 HMC투자증권 신탁 계좌가 있습니다"
- **Established fact**: EP1 established "어머니" as trust source
- **Verdict**: PASS (score 96) → REJECT (post_select_conflict)
- **IFC tag**: `[IFC] 불변사실 위반 감지 (시작계약위반 / 확정상태회귀)`
- **Valid**: YES

### B2. EP2 R2 -- Trust Asset Characteristics Drift

- **IFC conflict type**: `committed_state_regression`
- **LLM check**: CONFLICT (CRITICAL + MAJOR)
- **Conflict detail**: EP1 established trust as "어머니가 몰래 남긴 자산" → EP2 R2 describes it as chairman-controlled asset requiring public dissolution request
- **Verdict**: PASS (score 90) → REJECT (post_select_conflict)
- **Valid**: YES

### B3. EP2 R3 -- Timeline Discontinuity (오전 10시 → 늦은 오후)

- **IFC conflict type**: `opening_anchor_drift`
- **LLM check**: CONFLICT (MAJOR)
- **Conflict detail**: EP1 ending action continues immediately into EP2, but EP2 opens in "늦은 오후" while EP1's timeline suggests morning
- **Verdict**: PASS (score 96) → REJECT (post_select_conflict)
- **IFC tag**: `[IFC] 불변사실 위반 감지 (시작계약위반 / 확정상태회귀 / 완료사건반복)`
- **Valid**: YES

### B4. EP3 R1 -- Leather Note Location + Timeline Regression

- **IFC conflict type**: `committed_state_regression` (dual)
- **LLM check**: CONFLICT (CRITICAL: note location, MAJOR: timeline)
- **Conflict detail 1**: 가죽 노트 보관 위치 -- EP2 established "소형 금고" (safe), EP3 R1 rejected says "책상 아래의 서랍" (drawer)
- **Conflict detail 2**: EP2 서재 독대 at 4:35 PM, EP3 증권사 도착 at 3:35 PM -- impossible timeline regression
- **Artifact truth**: `rejected_best__C_tension.txt` L27: "곧장 책상 아래의 서랍을 열어"; `patched_after_fix__A.txt` L27: corrected to "책장으로 다가가...소형 금고"
- **Verdict**: PASS → REJECT (post_select_conflict)
- **Valid**: YES

### B5. EP5 R1 -- Capital Accounting Error

- **IFC conflict type**: `committed_state_regression`
- **LLM check**: CONFLICT (MAJOR: capital, MAJOR: timeline)
- **Conflict detail**: EP4 incurred 5천만 원 corporate startup cost, but EP5 shows 예수금 = 1,900,000,000원 without deduction. Also WTI order execution timeline misalignment.
- **Verdict**: PASS_WITH_FIX (score 93) → REJECT (post_select_conflict override)
- **Valid**: YES

### B6. EP6 R2 -- Capital-State Contradiction (Firewall-Adjacent)

- **Gate**: `Conflict-first retry` -- this was actually a conflict-first retry notice from R1's post-select conflict, not a fresh post-select check
- **Conflict detail**: EP5 deployed full 19억 into WTI, but EP6 R2 describes 20억 available cash
- **Verdict**: REJECT (continuity_firewall, score 44)
- **Valid**: YES

---

## C. IFC Violation Family Classification

| Family | Label | Hard Fact? | Occurrences | Episodes |
|--------|-------|-----------|-------------|----------|
| `opening_anchor_drift` | 시작계약위반 | Yes | 4 | EP2 R1/R2/R3 |
| `committed_state_regression` | 확정상태회귀 | Yes | 5 | EP2 R1/R2/R3, EP3 R1, EP5 R1 |
| `completed_event_replay` | 완료사건반복 | Yes | 1 | EP2 R3 |
| `scene_obligation_missing` | 씬의무누락 | No | 0 | -- |
| `scene_order_drift` | 씬순서이탈 | No | 0 | -- |
| `metadata_reference_shape_violation` | 메타데이터형식위반 | No | 0 | -- |

Only the three "hard fact" families (`_HARD_FACT_FAMILIES`) triggered in this run. All correctly identified real immutable-fact violations.

---

## D. ContinuityValidator Architecture Summary

### D1. Verdict Flow

```
ContinuityValidator.validate()
  ├── EP1? → auto-skip (passed=True)
  ├── prev_hud missing? → FAIL-CLOSED (passed=False, score=0, degraded=True)
  └── 7 checks:
      ├── Foundational (always run):
      │   ├── _check_item_continuity → CRITICAL possible (duplicate_acquisition, weapon_reset)
      │   ├── _check_inventory_count_continuity → WARNING only
      │   ├── _check_active_pressure_continuity → WARNING only (always passed=True)
      │   └── _check_weapon_continuity → CRITICAL possible
      └── Contextual:
          ├── _check_injury_continuity → BLOCKING possible (wuxia/hunter/fantasy only)
          ├── _check_location_continuity → BLOCKING possible (arc_pos==1 downgrade)
          ├── _check_personality_continuity → never BLOCKING (routed to warnings via _append_personality_warnings)
          └── _check_time_consistency → BLOCKING possible (severe keywords only)
```

### D2. BLOCKING → WARNING Downgrade Paths

1. `_check_location_continuity`: arc_pos==1 downgrades impossible_teleportation from BLOCKING to WARNING (`[TF-CV-1]`)
2. `_check_personality_continuity`: all findings unconditionally routed to warnings (never violations)
3. No other downgrade paths exist

### D3. Severity → Effect Mapping

| Severity | List | Affects `passed`? |
|----------|------|-------------------|
| BLOCKING | violations | YES (passed=False if any) |
| CRITICAL | violations | YES |
| WARNING | warnings | NO |
| INFO | warnings | NO |
| MAJOR (personality) | warnings (via _append_personality_warnings) | NO |
| MINOR (personality) | warnings (via _append_personality_warnings) | NO |

---

## E. Post-Select Check Architecture

### E1. Execution Model

```python
# stage4_interview_round.py L3670-3701
with ThreadPoolExecutor(max_workers=2, thread_name_prefix="postselect"):
    future_continuity = check_manuscript_continuity_with_cache(...)  # DB-based, cached
    future_history = check_manuscript_history_conflicts(...)          # Text-based
    # Both: timeout=120s, fail-closed on exception
```

### E2. Downgrade Chain

```
Post-select conflict detected
  → verdict = "REJECT"
  → gate_basis = "post_select_conflict"
  → repair_scope = "full"
  → error_category = POST_SELECT_CONTINUITY_CONFLICT / POST_SELECT_HISTORY_CONFLICT / POST_SELECT_CONTINUITY_AND_HISTORY / POST_SELECT_CHECK_ERROR
  → previous_attempt rebuilt with:
      - fix_scope = "full"
      - reject_bucket = "post_select_conflict"
      - provisional_pass_downgrade = True
  → Reject runtime (stage4_reject_runtime.py L514-524):
      - resolved_fix_scope = "full"
      - resolved_fix_pack = {} (WIPED)
      - conflict-first retry notice prepended
```

### E3. History Conflict LLM Verdicts

From `director_continuity.py` (TF-22 rule):
- CONFLICT if `decision == "CONFLICT"` AND (`critical_count > 0` OR `major_count > 0`)
- PASS if MINOR-only or no issues
- Exception → REJECT (fail-closed, CRITICAL severity synthetic)

---

## F. Inventory Gap Pipeline

### F1. Generation (stage3_orchestrator.py L2383-2447)

```python
def _detect_inventory_gaps(self, blueprint, working_ep):
    if working_ep <= 1: return  # skip EP1
    owned = world_state.get_owned_items()  # primary source
    # fallback: constraint_db (DEAD CODE -- never exposed as app attribute)
    planned = arc.state_constraints.protagonist_items + items_acquired
    referenced = scan(blueprint.protagonist_state.equipment, scene_breakdown, integrated_scenario)
    gaps = [item for item in referenced if item not in owned and item not in planned]
    blueprint["_inventory_gaps"] = gaps  # WRITE-ONCE, never updated during S4 retries
```

### F2. Consumption (chief_writer_context_packets.py L92-108)

```python
gaps = blueprint.get("_inventory_gaps", [])
if gaps:
    future_guard_section += "### [TF-49] Blueprint inventory prerequisite\n"
    for gap in gaps:
        future_guard_section += f"- {gap['item']}: {gap['note']}\n"
    future_guard_section += "위 아이템이 해당 에피소드 내에서 자연스러운 획득 비트 없이 사용될 경우 불합격 처리됩니다.\n"
```

### F3. Run Data (8 S3 + 4 S4 preflight)

| Ep | Gap Count | Items |
|----|-----------|-------|
| 2 | 1 | 18년치 거시경제 지표 노트 |
| 3 | 2 | 노트, 19.3억 계좌 통장/휴대폰 |
| 4 | 3 | 19억 계좌, 사무실 열쇠, 임대차 계약서 |
| 5 | 3 | 사무실 열쇠, 198만달러 파생상품 계좌, 다중 모니터 PC |
| 6 | 2 | 19.3억 계좌 내역, 캐시미어 코트 |
| 7 | 3 | 19.3억 계좌 내역, 캐시미어 코트, WTI 매수 체결 확인서 |
| 8 | 1 | WTI 15억 매수 체결 확인서 |
| 9 | 1 | WTI 15억 매수 체결 확인서 |

---

## G. Cross-Reference: Validator Signals vs Artifact Truth

| Validator Signal | Artifact Truth Match? | Assessment |
|-----------------|----------------------|------------|
| EP2 R1 trust provenance conflict | YES -- rejected_best L86 says "조부", EP1 says "어머니" | Correct catch |
| EP2 R2 trust asset characteristics | YES -- trust asset mechanism changed | Correct catch |
| EP2 R3 timeline discontinuity | YES -- time jumps from morning to late afternoon | Correct catch |
| EP3 R1 note location | YES -- drawer (L27) vs safe (EP2 established) | Correct catch |
| EP3 R1 time regression | YES -- 4:35pm → 3:35pm impossible | Correct catch |
| EP5 R1 capital accounting | YES -- 5천만 corporate cost not deducted from 19.3억 | Correct catch |
| EP6 R2 capital-state impossibility | YES -- 20억 available after 19억 full WTI deployment | Correct catch |
| EP2 V66.1 pressure drift | NO match -- investment genre opening naturally shifts to new setting | Noise |
| EP3 V66.1 pressure drift | NO match -- PB center visit is a planned scene, not a pressure continuation | Noise |
| EP5 V66.1 pressure drift | NO match -- office setup is new chapter context | Noise |
| EP6 V66.1 pressure drift | NO match -- trading/meeting context shift | Noise |
| EP2 V66.1 re-acquisition (노트) | PARTIAL -- writer describes obtaining note from safe, which is technically re-engagement not re-acquisition | Partial signal |
| EP8 V66.1 re-acquisition (휴대전화) | PARTIAL -- writer describes phone use, not re-acquisition | Weak signal |
