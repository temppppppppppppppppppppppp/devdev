# NPC Martial And Soak Canary Aggregate Execution Roadmap

Date: 2026-03-27
Status: active
Canonical Path: `docs/2026-03-27/npc-martial-and-soak-canary-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `155906f3adb1c2f4a3810ce359f6b59124d8556a`
- Baseline Dirty Summary: `dirty: tracked npc-martial docs/code/tests, docs/temp/queue-state.json, canary DB artifact; untracked soak survey/benchmark docs, temp npc mirror, canary directories`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `roadmap opened because a second execution SSOT entered an already-active temp queue`
Queue Snapshot:
- `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md`
- `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md`

## 1. Purpose

This aggregate roadmap is required because `docs/temp/` now contains more than one execution SSOT mirror.

It governs:

- `npc-martial-state-substrate-wave1`
- `frontier-lag-soak-canary-wave1`

This is the only roadmap with SSOT authority for the current two-item queue.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | in_progress | active hotfix/canary closure item; current queue blocker |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | pending | execution-ready bounded harness extension; waits behind item 1 |

## 3. Dependency Graph

- `npc-martial-state-substrate-wave1` -> `frontier-lag-soak-canary-wave1`
- shared substrate:
  - canary runtime discipline
  - temp queue governance
  - ops validation
- merge opportunities:
  - none at code level; keep the items separate

## 4. Execution Order

Priority basis:
- `docs/implementation/queue-priority-rubric.md`

Order rationale:
- dependency is absolute, so numeric tie-breaking is unnecessary
- the active npc-martial item is a direct queue blocker
- soak canary is the next bounded item once the active blocker clears

1. `npc-martial-state-substrate-wave1`
2. `frontier-lag-soak-canary-wave1`

## 5. Per-Item Plan

### npc-martial-state-substrate-wave1

- goal:
  - finish the active hotfix/canary closure thread cleanly
- prerequisites:
  - none; already in progress
- execution notes:
  - keep the item bounded to the current wave1 closure scope
  - do not let soak-harness work start in parallel
- completion signal:
  - closure-clean SSOT state and temp cleanup readiness
- temp cleanup action:
  - remove the temp mirror only after formal closure

### frontier-lag-soak-canary-wave1

- goal:
  - realize the bounded soak harness extension from the corroborated survey
- prerequisites:
  - `npc-martial-state-substrate-wave1` closed or explicitly paused/reordered by a refreshed roadmap
  - current wuxia canary thread finished
- execution notes:
  - keep `run_auto_frontier_lag_harness.py` as the base
  - add bounded overrides and post-run state audit only
- completion signal:
  - tranches complete and disposable 3-arc pilot evidence captured
- temp cleanup action:
  - remove the temp mirror after closure

## 6. Shared Risks and Side-Effects

- shared write paths:
  - `docs/temp/`
  - queue-state artifact
- shared DB/schema touchpoints:
  - none at schema level
  - both items depend on clean interpretation of canary/disposable project artifacts
- shared logs/UI surfaces:
  - canary logs
  - runtime audit and operator-facing validation commands
- rollback/recovery concerns:
  - avoid overlapping canary-like runs on the same disposable target
- queue collision or ordering risks:
  - starting soak work before the active npc-martial item closes would violate queue governance and mix operator evidence lanes

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `npc-martial-state-substrate-wave1` | in_progress | 2026-03-27 | none |
| `frontier-lag-soak-canary-wave1` | pending | 2026-03-27 | `npc-martial-state-substrate-wave1` active queue blocker |

Allowed statuses:
- pending
- in_progress
- completed
- blocked

## 8. Queue Cleanup Rule

- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when both items are completed:
  - remove `docs/temp/execution-roadmap.md`
  - remove `docs/temp/queue-state.json`
- leave `docs/temp/README.md`

## 9. 3-Pass Audit Record

### Pass 1. Structure and Scope

- queue inventory was rechecked against live `docs/temp/`
- roadmap remains bounded to exactly two execution items
- PASS

### Pass 2. Evidence and Consistency

- dependency order matches the active temp queue and current canary blocker reality
- no ordering contradiction was found with the queue-priority rubric
- PASS

### Pass 3. Execution and Readability

- roadmap makes the blocker explicit
- soak canary remains prepared without prematurely starting realization
- PASS

Estimated confidence: `97%`
