# NPC Martial And Soak Canary Aggregate Execution Roadmap

Date: 2026-03-27
Status: active
Canonical Path: `docs/2026-03-27/npc-martial-and-soak-canary-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `155906f3adb1c2f4a3810ce359f6b59124d8556a`
- Baseline Dirty Summary: `dirty: tracked npc-martial docs/code/tests, docs/temp/queue-state.json, canary DB artifact; untracked soak survey/benchmark docs, temp npc mirror, canary directories`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `roadmap opened because a second execution SSOT entered an already-active temp queue; reordered on 2026-03-28 after npc-martial remained blocked without a live seam diff and frontier-lag was promoted to the active queue item`
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
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | in_progress | execution-ready bounded harness extension; promoted to the active queue item on 2026-03-28 after Director reorder |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | parked follow-up item; no live Stage 4 / STV hotfix seam diff; future resumption requires fresh bounded evidence |

## 3. Dependency Graph

- `frontier-lag-soak-canary-wave1` is the active queue item after the 2026-03-28 Director reorder
- `npc-martial-state-substrate-wave1` remains blocked as a parked follow-up item and no longer blocks frontier realization in this turn
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
- the queue now authorizes the soak canary item as the next bounded realization lane
- no live wuxia canary process remains in the current workspace at decision time
- npc-martial has no live bounded diff on its declared seam and stays parked off the critical path

1. `frontier-lag-soak-canary-wave1`
2. `npc-martial-state-substrate-wave1`

## 5. Per-Item Plan

### frontier-lag-soak-canary-wave1

- goal:
  - realize the bounded soak harness extension from the corroborated survey
- prerequisites:
  - Director promotion is granted by this roadmap refresh
  - no concurrent wuxia canary or npc-martial hotfix run may be opened while this item is active
- execution notes:
  - keep `run_auto_frontier_lag_harness.py` as the base
  - add bounded overrides and post-run state audit only
  - treat this turn as queue promotion only; start code realization in a fresh bounded implementation turn
- completion signal:
  - tranches complete and disposable 3-arc pilot evidence captured
- temp cleanup action:
  - remove the temp mirror after closure

### npc-martial-state-substrate-wave1

- goal:
  - preserve the bounded hotfix context without blocking the active soak item
- prerequisites:
  - fresh bounded diff on the declared Stage 4 / STV hotfix seam, or fresh survey evidence justifying a later reopen after frontier disposition
- execution notes:
  - keep the item bounded to the current wave1 hotfix seam if resumed later
  - do not count unrelated provider, benchmark, TR-harness, or governance edits as item progress
  - do not reopen it in parallel with the active frontier soak lane
- completion signal:
  - a fresh bounded reopen with new evidence, or explicit later closure with queue artifacts synced
- temp cleanup action:
  - keep the temp mirror while parked; remove it only after explicit closure

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
  - starting a new npc-martial hotfix or separate wuxia canary while the active frontier soak item is running would mix operator evidence lanes

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `frontier-lag-soak-canary-wave1` | in_progress | 2026-03-28 | none; Director promotion granted and this is now the active queue item |
| `npc-martial-state-substrate-wave1` | blocked | 2026-03-28 | no live Stage 4 / STV hotfix seam diff; future resumption requires fresh bounded evidence |

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

## 10. Queue Reconciliation 2026-03-28

### Pass 1. Structure and Scope

- the roadmap still governs the same two-item aggregate queue
- this refresh is bounded to authority reconciliation only; it does not authorize realization
- PASS

### Pass 2. Evidence and Consistency

- live `git status --short` no longer overlaps the declared npc-martial hotfix seam
- `docs/temp/queue-state.json` had drifted by marking both items `in_progress`
- roadmap status, item statuses, and queue-promotion rules were corrected to match the live workspace
- PASS

### Pass 3. Execution and Readability

- item 1 is now explicitly blocked instead of pretending to be actively in progress
- item 2 remains pending and cannot start by implication
- the next step is explicit: resume item 1 on its declared seam or close/reorder it before any promotion
- PASS

Queue reconciliation confidence: `97%`

## 11. Director Reorder And Promotion 2026-03-28

Director Verdict: `reorder queue; promote frontier-lag-soak-canary-wave1; keep npc-martial-state-substrate-wave1 blocked off the active lane`

### Pass 1. Structure and Scope

- this refresh is bounded to queue authority and promotion only
- no code realization, canary run, or deployment work was performed in this turn
- PASS

### Pass 2. Evidence and Consistency

- live `git status --short` still shows no bounded diff on the declared npc-martial hotfix seam
- live process inspection shows no active wuxia canary `python` process in the workspace at decision time
- frontier-lag remains execution-ready on already-corroborated bounded harness scope
- PASS

### Pass 3. Execution and Readability

- frontier-lag is now the only honest active queue item
- npc-martial remains preserved as a blocked follow-up item instead of a fake live blocker
- the next bounded implementation turn can start on the frontier soak seam without reopening npc-martial by implication
- PASS

Director reorder confidence: `97%`
