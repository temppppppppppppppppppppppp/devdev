# Active Temp Execution Roadmap

Date: 2026-03-31
Status: active (3-pass audited)
Canonical Path: `docs/2026-03-31/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
Baseline Dirty Summary: `dirty: active stage4 runtime/tests/log-db drift, active temp queue/roadmap already dirty, multiple 2026-03-30 and 2026-03-31 docs plus artifact outputs untracked`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Supersedes:
- `docs/2026-03-30/active-temp-execution-roadmap.md`

Queue Snapshot:
- `docs/temp/stage4-cw-webnovel-identity-context-hierarchy-remediation-execution-ssot.md`
- `docs/temp/0_1-stage4-cw-first-pass-false-miss-remediation-execution-ssot.md`
- `docs/temp/0_1-stage4-retry-efficiency-remediation-execution-ssot.md`
- `docs/temp/0_1-stage4-ep9-remediation-execution-ssot.md`
- `docs/temp/0_1-stage3-blueprint-fix-execution-ssot.md`
- `docs/temp/stage3-blueprint-validator-hardening-execution-ssot.md`
- `docs/temp/stage3-capital-unit-drift-hardening-execution-ssot.md`
- `docs/temp/stage4-provider-fallback-observability-gap-execution-ssot.md`
- `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md`
- `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md`

## 1. Purpose

This roadmap is the current controller for the aggregate `docs/temp/` execution queue.

This refresh does four specific things:

1. admits the new `stage4-cw-webnovel-identity-context-hierarchy-remediation` lane into the active queue
2. places that lane at the top because it is the latest user-driven system priority and is backed by a completed post-run merge audit
3. keeps the already in-progress `0_1-stage4-cw-first-pass-false-miss-remediation` lane near the top because its runtime evidence and closure work are already underway
4. keeps older Stage 3 / legacy items visible without letting them outrank the current Stage 4 user-driven sequence

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `stage4-cw-webnovel-identity-context-hierarchy-remediation` | `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-remediation-execution-ssot.md` | `docs/temp/stage4-cw-webnovel-identity-context-hierarchy-remediation-execution-ssot.md` | in_progress | code landed and targeted static validation passed; fresh Stage 3 -> Stage 4 rerun evidence still pending before closure |
| `0_1-stage4-cw-first-pass-false-miss-remediation` | `docs/2026-03-31/0_1-stage4-cw-first-pass-false-miss-remediation-execution-ssot.md` | `docs/temp/0_1-stage4-cw-first-pass-false-miss-remediation-execution-ssot.md` | in_progress | code landed; runtime evidence through EP15 collected; merged closure audit still pending |
| `0_1-stage4-retry-efficiency-remediation` | `docs/2026-03-31/0_1-stage4-retry-efficiency-remediation-execution-ssot.md` | `docs/temp/0_1-stage4-retry-efficiency-remediation-execution-ssot.md` | ready-for-execution | new bounded retry-compression lane from the EP8-15 efficiency survey |
| `0_1-stage4-ep9-remediation` | `docs/2026-03-30/0_1-stage4-ep9-remediation-execution-ssot.md` | `docs/temp/0_1-stage4-ep9-remediation-execution-ssot.md` | closure-pending | code landed and EP9 live pass was observed; final closure doc/temp cleanup still pending |
| `0_1-stage3-blueprint-fix` | `docs/2026-03-30/0_1-stage3-blueprint-fix-execution-ssot.md` | `docs/temp/0_1-stage3-blueprint-fix-execution-ssot.md` | pending | bounded artifact fix lane |
| `stage3-blueprint-validator-hardening` | `docs/2026-03-30/stage3-blueprint-validator-hardening-execution-ssot.md` | `docs/temp/stage3-blueprint-validator-hardening-execution-ssot.md` | ready-for-execution | validator contract hardening lane |
| `stage3-capital-unit-drift-hardening` | `docs/2026-03-30/stage3-capital-unit-drift-hardening-execution-ssot.md` | `docs/temp/stage3-capital-unit-drift-hardening-execution-ssot.md` | ready-for-execution | preventive Stage 3 capital drift lane |
| `stage4-provider-fallback-observability-gap` | `docs/2026-03-29/stage4-provider-fallback-observability-gap-execution-ssot.md` | `docs/temp/stage4-provider-fallback-observability-gap-execution-ssot.md` | pending | lower immediate ROI than the current Stage 4 correctness/efficiency lanes |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | parked | non-critical soak lane |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | awaits fresh evidence and explicit reactivation |

## 3. Dependency Notes

- `stage4-cw-webnovel-identity-context-hierarchy-remediation` is now the top user-driven lane because it addresses the currently observed Stage 3+4 prompt/authority failure family from the `0_2` frontier run and has a completed post-run merge audit.
- `0_1-stage4-cw-first-pass-false-miss-remediation` remains near the top because code already landed and runtime evidence has already been gathered against it.
- `0_1-stage4-retry-efficiency-remediation` should follow the new hierarchy-remediation lane because retry compression should not outrank upstream prompt/authority cleanup when both are active.
- `0_1-stage4-retry-efficiency-remediation` depends conceptually on the already-landed Stage 4 substrates:
  - EP9 NpcDrift/advisory-contract correction
  - verdict-layer observability surfacing
- `0_1-stage4-ep9-remediation` is no longer the top execution lane, but it remains in queue until formal closure and temp cleanup are finished.
- the Stage 3 lanes remain independent and actionable, but they are not the current user-requested Stage 4 priority.
- `stage4-provider-fallback-observability-gap` stays below the current Stage 4 correctness/efficiency sequence.
- the last two items remain parked legacy lanes.

## 4. Execution Order

1. `stage4-cw-webnovel-identity-context-hierarchy-remediation`
2. `0_1-stage4-cw-first-pass-false-miss-remediation`
3. `0_1-stage4-retry-efficiency-remediation`
4. `0_1-stage4-ep9-remediation`
5. `0_1-stage3-blueprint-fix`
6. `stage3-blueprint-validator-hardening`
7. `stage3-capital-unit-drift-hardening`
8. `stage4-provider-fallback-observability-gap`
9. `frontier-lag-soak-canary-wave1`
10. `npc-martial-state-substrate-wave1`

Order rationale:

- the new hierarchy-remediation lane is the latest user-driven execution priority and directly targets the currently observed `0_2` Stage 3+4 failure family
- the current Stage 4 CW lane remains high because it is already in motion, but it is no longer the top priority after the user's redirect
- the retry-efficiency lane remains high ROI, but it follows the hierarchy-remediation lane because retry compression should not outrank upstream prompt/authority cleanup when both are active
- the EP9 lane is important substrate history but is now primarily a closure/pending-cleanup item rather than the highest active leverage lane
- the remaining Stage 3 and legacy items keep their older lower-priority positions

## 5. Per-Item Status Ledger

### stage4-cw-webnovel-identity-context-hierarchy-remediation

- next action:
  - use the canonical SSOT as the governing document for the next bounded Stage 3+4 patch wave
  - re-audit the canonical SSOT against the live workspace immediately before code edits
- temp cleanup action:
  - remove mirror after bounded code/test realization, fresh Stage 3 -> Stage 4 rerun validation, closure audit, roadmap refresh, and queue-state sync

### 0_1-stage4-cw-first-pass-false-miss-remediation

- next action:
  - complete merged closure audit against the already collected runtime evidence
  - if closure is not supportable, reopen only the residual seam that remains live
- temp cleanup action:
  - remove mirror after closure audit, roadmap refresh, and queue-state sync

### 0_1-stage4-retry-efficiency-remediation

- next action:
  - use the canonical SSOT as the governing document for the next bounded Stage 4 policy wave
  - re-audit the canonical SSOT against the live workspace immediately before code edits
- temp cleanup action:
  - remove mirror after bounded code/test realization, fresh-session live efficiency audit, closure review, roadmap refresh, and queue-state sync

### 0_1-stage4-ep9-remediation

- next action:
  - convert the live pass plus post-patch survey chain into formal closure, or explicitly justify why the mirror remains active
- temp cleanup action:
  - remove mirror after closure audit, roadmap refresh, and queue-state sync

### 0_1-stage3-blueprint-fix

- next action:
  - follow canonical SSOT if the artifact fix lane is reactivated
- temp cleanup action:
  - remove mirror after bounded artifact patch and closure validation

### stage3-blueprint-validator-hardening

- next action:
  - follow canonical SSOT if the validator lane is reactivated
- temp cleanup action:
  - remove mirror after code/test closure

### stage3-capital-unit-drift-hardening

- next action:
  - execute only after re-auditing the canonical SSOT against the live workspace
- temp cleanup action:
  - remove mirror after preventive validator lane lands and validates

### stage4-provider-fallback-observability-gap

- next action:
  - remain deferred unless observability ROI rises again
- temp cleanup action:
  - remove mirror only after live validation or formal park/closure decision

### frontier-lag-soak-canary-wave1

- next action:
  - stay parked
- temp cleanup action:
  - remove mirror on explicit closure or replacement

### npc-martial-state-substrate-wave1

- next action:
  - stay blocked pending fresh evidence
- temp cleanup action:
  - remove mirror only after reactivation decision or formal closure

## 6. Cleanup Rule

- canonical execution SSOTs remain in dated `docs/`
- temp mirrors remain the active queue only until each item is realized or formally closed
- when the queue is exhausted, remove:
  - temp execution SSOT mirrors
  - `docs/temp/execution-roadmap.md`
  - `docs/temp/queue-state.json`

Confidence: 96%
