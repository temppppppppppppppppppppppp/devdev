# Stage4 And Legacy Execution Roadmap

Date: 2026-03-29
Status: active
Canonical Path: `docs/2026-03-29/stage4-and-legacy-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty: tracked stage4/provider runtime and tests, narrative assets, temp queue artifacts, and canary outputs; several 2026-03-28/2026-03-29 docs are still untracked`
- Resume Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Resume Drift Summary: `same commit; truth-store isolation and world-state rollback fidelity both landed, and the temp queue is now closure-synced down to the remaining 3 parked/deferred items`
Supersedes:
- `docs/2026-03-27/npc-martial-and-soak-canary-execution-roadmap.md`

Queue Snapshot (post-truth-store closure sync 2026-03-29):
- `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md`
- `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md`
- `docs/temp/stage4-provider-fallback-observability-gap-execution-ssot.md`

Removed mirrors (completed Stage4 closure sweep 2026-03-29):
- `stage4-scope-sink-semantics` → canonical: `docs/2026-03-29/`
- `stage4-retry-loop-compression` → canonical: `docs/2026-03-29/`
- `stage4-decision-contract-matrix` → canonical: `docs/2026-03-28/`
- `stage4-feedback-windowing` → canonical: `docs/2026-03-28/`
- `stage4-gemini-direct-default` → canonical: `docs/2026-03-29/`
- `stage4-ifc-bridge` → canonical: `docs/2026-03-28/`
- `stage4-target-locked-patch-lane` → canonical: `docs/2026-03-28/`
- `why-fix-pack-is-empty` → canonical: `docs/2026-03-28/`

Updated truth-store closures (2026-03-29):
- `canary-prep-truth-store-isolation` → canonical: `docs/2026-03-29/`
- `world-state-rollback-fidelity` → canonical: `docs/2026-03-29/`

## 1. Purpose

This roadmap remains the controlling aggregate roadmap and now governs the current 3-item temp execution queue after the truth-store closure sync.

It now does four things:

- records that both truth-store substrate lanes landed and closed cleanly
- marks realized Stage4 waves as completed or closure-sweep candidates instead of pretending they are still pending
- parks low-ROI or unrelated legacy items off the active path
- keeps provider observability deferred unless its ROI rises again

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `world-state-rollback-fidelity` | `docs/2026-03-29/world-state-rollback-fidelity-execution-ssot.md` | `docs/temp/world-state-rollback-fidelity-execution-ssot.md` | completed | implementation, regression coverage, and fresh prepare-only validation passed; temp mirror removed during closure sync |
| `canary-prep-truth-store-isolation` | `docs/2026-03-29/canary-prep-truth-store-isolation-execution-ssot.md` | `docs/temp/canary-prep-truth-store-isolation-execution-ssot.md` | completed | anchor cleanup, duplicate guard, and closure validation passed; temp mirror removed during closure sync |
| `stage4-scope-sink-semantics` | `docs/2026-03-29/stage4-scope-sink-semantics-execution-ssot.md` | `docs/temp/stage4-scope-sink-semantics-execution-ssot.md` | completed | implemented, follow-up micro-fix landed, and later mixed canary interpretation was resolved as a sink-reading issue rather than a reopen-worthy code defect |
| `stage4-retry-loop-compression` | `docs/2026-03-29/stage4-retry-loop-compression-execution-ssot.md` | `docs/temp/stage4-retry-loop-compression-execution-ssot.md` | completed | implemented and live-validated; later EP3 incident was confirmed BP-origin and resolved without reopening runtime policy |
| `stage4-decision-contract-matrix` | `docs/2026-03-28/stage4-decision-contract-matrix-execution-ssot.md` | `docs/temp/stage4-decision-contract-matrix-execution-ssot.md` | completed | implemented and live-validated via fix-scope sink verification; temp mirror still awaits closure cleanup |
| `stage4-feedback-windowing` | `docs/2026-03-28/stage4-feedback-windowing-execution-ssot.md` | `docs/temp/stage4-feedback-windowing-execution-ssot.md` | completed | implemented and clean Gemini canary passed; temp mirror still awaits closure cleanup |
| `stage4-gemini-direct-default` | `docs/2026-03-29/stage4-gemini-direct-default-execution-ssot.md` | `docs/temp/stage4-gemini-direct-default-execution-ssot.md` | completed | Gemini direct default landed; non-Gemini explicit opt-in residual is intentionally deferred |
| `stage4-ifc-bridge` | `docs/2026-03-28/stage4-ifc-bridge-execution-ssot.md` | `docs/temp/stage4-ifc-bridge-execution-ssot.md` | completed | foundation wave realized; later decision-contract work absorbed the remaining seam |
| `stage4-target-locked-patch-lane` | `docs/2026-03-28/stage4-target-locked-patch-lane-execution-ssot.md` | `docs/temp/stage4-target-locked-patch-lane-execution-ssot.md` | completed | TF-PATCH-GATE and target-locked repair safeguards landed; temp mirror still awaits closure cleanup |
| `why-fix-pack-is-empty` | `docs/2026-03-28/why-fix-pack-is-empty-execution-ssot.md` | `docs/temp/why-fix-pack-is-empty-execution-ssot.md` | completed | root-cause wave completed; later fix-scope/contract work closed the actionable seam |
| `stage4-provider-fallback-observability-gap` | `docs/2026-03-29/stage4-provider-fallback-observability-gap-execution-ssot.md` | `docs/temp/stage4-provider-fallback-observability-gap-execution-ssot.md` | pending | code already landed; live validation is intentionally deferred because current ROI is lower than the recent narrative/stale-BP wins |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | in_progress | legacy non-Stage4 lane; still parked off the current critical path despite the in-progress document state |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | legacy non-Stage4 lane; parked off the current critical path |

## 3. Dependency Graph

- `stage4-retry-loop-compression` depends on already-landed substrate from:
  - `why-fix-pack-is-empty`
  - `stage4-target-locked-patch-lane`
  - `stage4-ifc-bridge`
  - `stage4-decision-contract-matrix`
  - `stage4-feedback-windowing`
- `stage4-scope-sink-semantics` depended on:
  - `stage4-decision-contract-matrix`
  - `stage4-feedback-windowing`
  - `stage4-retry-loop-compression`
- `stage4-scope-sink-semantics` is now landed and closed; it no longer defines the next active realization lane
- `canary-prep-truth-store-isolation` and `world-state-rollback-fidelity` are now both landed and closed; they no longer define the next queue action
- `stage4-provider-fallback-observability-gap` is independent of the retry-loop wave and is intentionally deferred
- `stage4-gemini-direct-default` is already landed and supports clean Gemini validation for future Stage4 waves
- the EP3 extreme loop incident is closed as blueprint-origin, so it does not create a new runtime dependency
- `frontier-lag-soak-canary-wave1` and `npc-martial-state-substrate-wave1` share only temp-queue governance with the current Stage4 queue and do not block Stage4 retry-loop work
- shared substrate opportunities:
  - Stage4 runtime observability and canary discipline
  - temp queue governance and closure hygiene
  - clean Gemini direct validation path

## 4. Execution Order

Priority basis:
- `docs/implementation/queue-priority-rubric.md`
- current live workspace evidence
- already-realized waves should be closure-swept, not re-realized
- narrative BP remediation should not leapfrog unresolved truth-store contamination or rollback fidelity gaps

Order rationale:
- no active truth-store or Stage4 retry-loop realization lane remains after the closure sync
- provider observability is still the only Stage4 execution-ready item left, but its ROI remains lower than the narrative lanes that just closed
- legacy non-Stage4 items stay parked unless explicitly reactivated by fresh evidence

If any parked item is reactivated, use this order:

1. `stage4-provider-fallback-observability-gap`
2. `frontier-lag-soak-canary-wave1`
3. `npc-martial-state-substrate-wave1`

## 5. Per-Item Plan

### world-state-rollback-fidelity

- goal:
  - preserve minimum reconstructible pre-boundary cast, relationship, and item truth after cleanup rollback
- prerequisites:
  - none; the lane is already realized and closure-validated
- execution notes:
  - realized via `top-level episode_bible` delta replay inside `WorldStateManager.rollback_to()`
  - prepare validation widened to distinguish cleanup success from minimum-truth preservation
  - regression coverage landed and fresh prepare-only validation passed on `canary_0329_truth_store_isolation_prepare_check_v2`
- completion signal:
  - satisfied: fresh prepare-only reset keeps contamination removed and preserves minimum reconstructible truth from EP `< from_ep`
- temp cleanup action:
  - completed; mirror removed during closure sync

### canary-prep-truth-store-isolation

- goal:
  - stop canary prep from carrying orphan `chain_link_*` anchors and accumulated `fact_ledger` / `world_state` residue into fresh projects
- prerequisites:
  - none; the lane is already realized and its follow-up fidelity dependency is closed
- execution notes:
  - substrate landed with orphan `chain_link_*` cleanup, rollback-boundary reuse, and same-episode duplicate-history protection
  - prepare-only validation confirmed capital normalization back to `20억` and removal of orphan `chain_link_4+`
  - the former `world_state` under-restoration issue was resolved by the closed `world-state-rollback-fidelity` lane
- completion signal:
  - satisfied: repeated prepare stays idempotent, no EP4+ orphan truth-store residue remains, and the follow-up fidelity lane is closed
- temp cleanup action:
  - completed; mirror removed during closure sync

### stage4-scope-sink-semantics

- goal:
  - preserve the landed semantics clarification and close out the queue residue cleanly
- prerequisites:
  - no reopen unless fresh evidence proves a real sink defect rather than an audit-reading issue
- execution notes:
  - cleanup-only; not an active realization lane
  - the mixed canary report was resolved by raw sink reread and follow-up micro-fix, so this item should stay closed unless new contradictory evidence appears
- completion signal:
  - mirror removed and queue artifacts resynced
- temp cleanup action:
  - remove the mirror after closure

### completed Stage4 items awaiting closure

- items:
  - `stage4-scope-sink-semantics`
  - `stage4-retry-loop-compression`
  - `stage4-decision-contract-matrix`
  - `stage4-feedback-windowing`
  - `stage4-gemini-direct-default`
  - `stage4-ifc-bridge`
  - `stage4-target-locked-patch-lane`
  - `why-fix-pack-is-empty`
- goal:
  - preserve canonical docs, remove stale temp mirrors, and sync queue artifacts after the active retry-loop wave or during a dedicated closure sweep
- prerequisites:
  - do not re-open these scopes unless fresh evidence contradicts the completed verdict
- execution notes:
  - cleanup-only; not active realization lanes
  - the EP3 extreme-loop case is closed as blueprint-origin and does not reopen Stage4 runtime policy
  - if one must be reopened, refresh the roadmap first
- completion signal:
  - mirror removed and queue artifacts resynced
- temp cleanup action:
  - remove each mirror individually under the execution-closure harness

### stage4-provider-fallback-observability-gap

- goal:
  - keep the wave parked while its live validation remains lower ROI than retry-loop compression
- prerequisites:
  - explicit user or evidence-based promotion
- execution notes:
  - code already landed
  - only fresh live validation remains
  - intentionally deferred because current ROI remains below the recently closed truth-store and narrative lanes
- completion signal:
  - either promoted with fresh validation demand or formally closed as deferred
- temp cleanup action:
  - keep the mirror until explicit closure or reactivation

### frontier-lag-soak-canary-wave1

- goal:
  - preserve legacy queue context without blocking current Stage4 work
- prerequisites:
  - explicit reactivation and fresh bounded evidence
- execution notes:
  - legacy parked item
  - document status remains `in_progress`
  - not on the current critical path
- completion signal:
  - explicit reopen or closure
- temp cleanup action:
  - keep the mirror while parked

### npc-martial-state-substrate-wave1

- goal:
  - preserve legacy queue context without blocking current Stage4 work
- prerequisites:
  - explicit reactivation and fresh bounded evidence
- execution notes:
  - legacy parked item; do not mix with the active Stage4 lane
- completion signal:
  - explicit reopen or closure
- temp cleanup action:
  - keep the mirror while parked

## 6. Shared Risks and Side-Effects

- shared write paths:
  - `modules/core/stage4_*`
  - `modules/domain/agents/*`
  - `tests/`
  - `docs/temp/`
- shared DB/schema touchpoints:
  - `anchors` table cleanup and rollback-triggered rewrites for `fact_ledger` / `world_state`
- shared logs/UI surfaces:
  - canary logs
  - JSONL/operator evidence sinks
  - retry-path payloads and Director/Chief Writer prompt surfaces
- rollback/recovery concerns:
  - do not mix active retry-loop realization with unrelated legacy queue work
  - closure sweeps must not delete temp mirrors for incomplete items
- queue collision or ordering risks:
  - reopening a completed Stage4 wave without refreshing this roadmap would create false parallel authority
  - using the stale 2026-03-27 roadmap would misroute effort to inactive legacy items

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `world-state-rollback-fidelity` | completed | 2026-03-29 | none; closure sync completed after fresh prepare-only validation passed |
| `canary-prep-truth-store-isolation` | completed | 2026-03-29 | none; closure sync completed after world-state fidelity follow-up landed |
| `stage4-scope-sink-semantics` | completed | 2026-03-29 | none; pending closure cleanup only |
| `stage4-retry-loop-compression` | completed | 2026-03-29 | none; pending closure cleanup only |
| `stage4-decision-contract-matrix` | completed | 2026-03-29 | none; pending closure cleanup only |
| `stage4-feedback-windowing` | completed | 2026-03-29 | none; pending closure cleanup only |
| `stage4-gemini-direct-default` | completed | 2026-03-29 | none; ambient residual intentionally deferred |
| `stage4-ifc-bridge` | completed | 2026-03-29 | none; pending closure cleanup only |
| `stage4-target-locked-patch-lane` | completed | 2026-03-29 | none; pending closure cleanup only |
| `why-fix-pack-is-empty` | completed | 2026-03-29 | none; pending closure cleanup only |
| `stage4-provider-fallback-observability-gap` | pending | 2026-03-29 | live validation deferred because ROI remains lower than current needs |
| `frontier-lag-soak-canary-wave1` | in_progress | 2026-03-29 | legacy parked item; not on current critical path |
| `npc-martial-state-substrate-wave1` | blocked | 2026-03-29 | legacy parked item |

Allowed statuses:
- pending
- in_progress
- completed
- blocked

## 8. Queue Cleanup Rule

- keep canonical dated execution SSOTs
- `world-state-rollback-fidelity` is now the next honest queue action
- completed Stage4 mirrors should be removed only under the execution-closure harness
- blocked legacy or deferred items stay in temp until explicit closure or reactivation
- when the queue is eventually exhausted:
  - remove `docs/temp/execution-roadmap.md`
  - remove `docs/temp/queue-state.json`
  - leave `docs/temp/README.md`

## 9. Queue Drift Note

`docs/temp/queue-state.json` is still machine-derived from per-item temp mirror metadata.
It therefore lags the roadmap-level status reconciliation until a closure sweep updates or removes the completed mirrors.

This roadmap is the controlling SSOT for order and status interpretation in the meantime.

## 10. 3-Pass Audit Record

### Pass 1. Structure and Scope

- re-enumerated all 11 active temp execution mirrors
- replaced the stale 2-item roadmap with a queue-wide controller
- bounded the roadmap to order, status truth, and closure posture only
- PASS

### Pass 2. Evidence and Consistency

- matched realized Stage4 waves against live session evidence:
  - fix-scope sink verification pass
  - feedback-windowing canary pass
  - Gemini direct default landing
  - retry-loop-compression canary improvement (`8R -> 2R`)
- scope-sink semantics later landed and the mixed sink canary was resolved by raw evidence reread plus the follow-up micro-fix
- confirmed the remaining EP3 extreme loop case was blueprint-origin and closed by blueprint patch rather than runtime-policy redesign
- confirmed provider observability and legacy items are safely deferrable
- PASS

### Pass 3. Execution and Readability

- made the lack of a new active realization lane explicit
- separated completed cleanup-only items from deferred backlog
- documented queue-state drift instead of pretending machine status is current
- PASS

Estimated confidence: `96%`

