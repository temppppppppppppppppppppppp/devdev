# World-State Rollback Fidelity Execution SSOT

Date: 2026-03-29
Status: closed
Canonical Path: `docs/2026-03-29/world-state-rollback-fidelity-execution-ssot.md`
Temp Mirror Path: `docs/temp/world-state-rollback-fidelity-execution-ssot.md`
Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty workspace with active stage4/provider/runtime edits, narrative assets, temp queue artifacts, and canary outputs`
- Resume Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Resume Drift Summary: `same commit; canary-prep truth-store isolation was implemented and prepare-only validation exposed world_state under-restoration after contamination cleanup`
Source Survey Docs:
- `docs/2026-03-29/world-state-rollback-fidelity-full-survey.md`
- `docs/2026-03-29/canary-prep-truth-store-isolation-execution-ssot.md`
- `docs/2026-03-29/bp-preflight-integrity-survey.md`
Evidence Artifacts:
- `projects/canary_0329_ep3_bp_patch_recheck/project_data.db`
- `projects/canary_0329_truth_store_isolation_prepare_check/project_data.db`
- EP1~EP3 committed manuscripts and `chain_link_3`
Side-Effect Coverage: covered

## 1. Intent

### Goal

Preserve `world_state` as a contamination-free but still minimally useful pre-boundary truth store after canary prep rollback.

### Why Now

The truth-store isolation wave correctly removed:

- orphan `chain_link_4+`
- duplicated `fact_ledger` scalar history
- post-boundary `world_state` residue

But fresh prepare-only validation showed that `WorldStateManager.rollback_to(target_ep)` rebuilds too little clean truth after cleanup:

- pre-EP4 cast disappears
- pre-EP4 relationship state disappears
- most pre-EP4 inventory/setup truth disappears

This is not a rollback of the previous fix. It is a bounded follow-up that restores minimum fidelity after contamination cleanup.

### Separation From Other Lanes

This lane is not:

- narrative BP patch work
- `fact_ledger` reconciliation work
- `chain_link` cleanup work
- Stage 4 runtime policy work
- provider/fallback work

Those lanes stay closed or deferred. This lane only fixes the `world_state` reconstruction contract and the validation that claims cleanup success.

## 2. Baseline Facts

### Confirmed By Live Validation

- source project `canary_0329_ep3_bp_patch_recheck`
  - `fact_ledger capital = 40억`
  - `chain_link_count = 7`
  - contaminated `world_state` with EP4+ residue
- prepared target `canary_0329_truth_store_isolation_prepare_check`
  - `fact_ledger capital = 20억`
  - `chain_link_count = 3`
  - `world_state.last_updated_ep = 3`
  - `alive_npcs = 0`
  - `relationships = 0`
  - `active_items = ['OTP 카드']`

### Reconstruction Gap

`rollback_to(target_ep)` at [world_state.py](C:/Users/User/Desktop/글도비/modules/core/world_state.py#L1324):

1. resets `_INIT_STATE`
2. loads all `episode_bibles`
3. replays only `episode_bibles.state_changes`

It does not consume top-level bible delta fields such as:

- `new_npcs`
- `relationship_changes`
- `new_items`
- `lost_items`

That means reconstructible pre-boundary truth is discarded even though it already exists in structured sources.

### Mixed Root Cause

Two things are true at once:

1. `rollback_to()` under-restores clean truth because it ignores top-level bible delta
2. some truth needed by preflight lives only in manuscript prose or `chain_link`, so even a fixed rollback will not become a full narrative snapshot

This lane addresses only item 1.

## 3. Included Scope

- [world_state.py](C:/Users/User/Desktop/글도비/modules/core/world_state.py)
  - `rollback_to(target_ep)`
  - bounded helper(s) needed to replay top-level bible delta into `_state`
- [stage4_canary_tools.py](C:/Users/User/Desktop/글도비/modules/core/stage4_canary_tools.py)
  - prepare/reset validation payload after rollback
- [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)
  - reuse only; no schema redesign expected
- tests for rollback fidelity and prepare-only validation

## 4. Excluded Scope

- manuscript parsing into `world_state`
- `chain_link` to `world_state` synthesis
- protagonist location / cliffhanger reconstruction from prose
- `fact_ledger` duplicate guard changes
- `chain_link` orphan cleanup logic already landed
- EP4 blueprint patch
- preflight authority-order doc changes as the primary answer
- Stage 4 Director / Chief Writer / retry policy logic

## 5. Target Contract

After `reset_stage4_outputs(project_root, from_ep=N)` completes:

1. contamination cleanup guarantees remain true
   - no `chain_link_M` for `M >= N`
   - no `fact_ledger` history rows for `ep >= N`
   - no `world_state` entities/items introduced at or after `N`
2. `world_state.rollback_to(N)` must also restore minimum reconstructible pre-boundary truth from EP `< N`:
   - cast introduced by top-level `new_npcs`
   - relationship state from top-level `relationship_changes`
   - item ownership from top-level `new_items` / `lost_items`
3. this lane does not promise manuscript-grade fidelity for:
   - location
   - pending actions
   - opening-ending bridge
4. `anchor_validation = ok` should mean both:
   - contamination removed
   - reconstructible minimum truth preserved

## 6. Realization Shape

### Tranche 1. Rollback Reconstruction Widening

Goal:
- widen `WorldStateManager.rollback_to()` so it replays top-level episode_bible delta in addition to `state_changes`

Files:
- [world_state.py](C:/Users/User/Desktop/글도비/modules/core/world_state.py)

Expected shape:
- keep the current `_INIT_STATE` reset
- keep replay order by episode
- after or around `state_changes` replay, apply a bounded top-level bible-delta replay path for:
  - `new_npcs`
  - `relationship_changes`
  - `new_items`
  - `lost_items`

Guardrail:
- do not attempt prose inference here
- do not silently fabricate protagonist location or chain-link pending actions

### Tranche 2. Fidelity Validation Upgrade

Goal:
- make prepare-only validation distinguish `contamination removed` from `minimum truth preserved`

Files:
- [stage4_canary_tools.py](C:/Users/User/Desktop/글도비/modules/core/stage4_canary_tools.py)

Expected shape:
- extend validation payload beyond:
  - post-boundary emptiness
  - `last_updated_ep`
- include a bounded comparison against reconstructible pre-boundary truth derived from episode_bibles:
  - expected minimal NPCs
  - expected minimal relationships
  - expected minimal items

Guardrail:
- validation should not claim manuscript-level fidelity
- validation should only assert fields this lane truly reconstructs

### Tranche 3. Regression Coverage

Goal:
- lock the widened rollback contract and validation semantics

Files:
- existing canary prep isolation tests
- new or extended rollback-fidelity tests

Minimum cases:
- rollback preserves pre-boundary NPC registry from `new_npcs`
- rollback preserves pre-boundary relationships from top-level `relationship_changes`
- rollback preserves pre-boundary items from `new_items` / `lost_items`
- prepare-only validation fails when reconstructible minimum truth is dropped
- prepare-only validation still passes when contamination is removed and minimum truth remains

## 7. Acceptance Criteria

1. After fresh prepare-only reset from `from_ep=4`, the target project still has:
   - pre-EP4 cast reconstructed from episode_bibles
   - pre-EP4 relationship state reconstructed from episode_bibles
   - pre-EP4 item ownership reconstructed from episode_bibles
2. EP4+ residue remains absent after the same reset
3. `fact_ledger` and `chain_link` fixes do not regress
4. `world_state` still does not pretend to restore prose-only truths it cannot know
5. prepare-only validation distinguishes:
   - cleanup success
   - fidelity success
6. rerunning prepare-only remains idempotent

## 8. Verification Plan

- `pytest tests/test_canary_prep_isolation.py -x -v`
- `pytest tests/test_stage4_canary_tools.py -x -v`
- targeted new rollback-fidelity tests if split into a separate file
- `python -m py_compile modules/core/world_state.py modules/core/stage4_canary_tools.py tests/test_canary_prep_isolation.py tests/test_stage4_canary_tools.py`
- `ruff check modules/core/world_state.py modules/core/stage4_canary_tools.py tests/test_canary_prep_isolation.py tests/test_stage4_canary_tools.py`
- `python scripts/check_utf8_hygiene.py modules/core/world_state.py modules/core/stage4_canary_tools.py docs/2026-03-29/world-state-rollback-fidelity-execution-ssot.md docs/temp/world-state-rollback-fidelity-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`
- fresh prepare-only validation on a polluted project copy after implementation

## 9. Risks

- source `world_state` is contaminated, so tests must derive expected truth from episode_bibles rather than trusting the source anchor wholesale
- if rollback tries to restore too much using weak heuristics, it will reintroduce invented truth
- if validation claims more than the code actually reconstructs, operators will over-trust `world_state`

## 10. Queue Position

- realized and closure-synced on 2026-03-29 after the fresh prepare-only validation passed
- no longer blocks narrative BP preflight or narrow canary work
- temp mirror cleanup completed during the same closure sync

## 11. 3-Pass Audit Record

### Pass 1. Scope

- confirmed this lane is a bounded follow-up, not a reopen of BP patch or Stage4 runtime policy
- locked scope to `world_state` reconstruction plus validation semantics

### Pass 2. Contract

- separated reconstructible top-level bible delta from prose-only / chain-link-only truth
- kept contamination cleanup success distinct from fidelity success

### Pass 3. Queue Fit

- placed this lane directly after the prepare-only live validation result
- verified it is the next honest blocker before EP4 preflight and canary work

Estimated confidence: 0.97

## 12. Closure Note

Date: 2026-03-29
Closure Status: closed

### 12.1 Realized Scope

- `WorldStateManager.rollback_to()` now replays top-level episode-bible delta in addition to `state_changes`
- reconstructible pre-boundary NPC, relationship, and item truth now survives canary prep rollback
- prepare-only validation now distinguishes `cleanup_status` from `minimum_truth_status`
- the lane stayed bounded: no manuscript parsing, no chain-link synthesis, and no narrative BP logic changes were introduced

### 12.2 Verification Summary

- implementation verification:
  - `pytest tests/test_canary_prep_isolation.py tests/test_stage4_canary_tools.py tests/test_rollback_npc.py -x -v` -> `28 passed`
  - `python -m py_compile` on touched runtime files and tests passed
  - `ruff check`, UTF-8 hygiene, `sync_temp_queue_state.py`, and `ops_validator.py --strict` all passed
- live validation:
  - fresh prepare-only run on `canary_0329_truth_store_isolation_prepare_check_v2` reported `anchor_validation.status=ok`, `cleanup_status=ok`, and `minimum_truth_status=ok`
  - resulting target anchor state preserved minimum reconstructible truth with `capital=20억`, `world_last_updated_ep=3`, `alive_npcs=13`, `relationships=10`, and `active_items=5`

### 12.3 Residual Risks

- `world_state` still does not and should not claim manuscript-grade fidelity for exact location, pending actions, or cliffhanger semantics
- narrative preflight must continue to treat committed manuscript and `chain_link` as the authority for those prose-only truths

### 12.4 Follow-Up

- no further system-track work remains in this rollback-fidelity lane
- reopen only if fresh evidence shows under-restoration of reconstructible episode-bible truth

### 12.5 Temp Cleanup

- execution SSOT mirror removed: yes
- roadmap mirror removed: no
- queue-state refreshed or removed: refreshed during the 2026-03-29 closure sync
