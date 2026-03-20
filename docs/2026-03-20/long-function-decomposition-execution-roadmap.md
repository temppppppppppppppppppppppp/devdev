# Long-Function Decomposition Aggregate Execution Roadmap

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/long-function-decomposition-execution-roadmap.md`
Temp Mirror Path: none while queue is in single-item mode
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: pre-existing stage4/smoke/doc changes, project artifact churn, docs/mmmm intake; no active temp execution queue at start`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Queue Snapshot:
- none; all execution items closed

## 1. Purpose
- Govern the first long-function decomposition queue with a single SSOT roadmap.
- Keep the work bounded to three high-ROI hotspots instead of opening a repo-wide refactor front.
- Apply per-step validity gates before any later realization work starts.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `stage2-finalizer-run-finalize-decomposition` | `docs/2026-03-20/stage2-finalizer-run-finalize-decomposition-execution-ssot.md` | removed after closure | completed | Stage 2 substrate item closed |
| `stage2-orchestrator-stage-2-arcs-async-logic-decomposition` | `docs/2026-03-20/stage2-orchestrator-stage-2-arcs-async-logic-decomposition-execution-ssot.md` | removed after closure | completed | Stage 2 async pipeline decomposition closed |
| `stage4-context-builder-build-mandatory-context-decomposition` | `docs/2026-03-20/stage4-context-builder-build-mandatory-context-decomposition-execution-ssot.md` | removed after closure | completed | Stage 4 context-builder decomposition closed |

## 3. Dependency Graph
- `stage2-finalizer-run-finalize-decomposition -> stage2-orchestrator-stage-2-arcs-async-logic-decomposition`
- `stage4-context-builder-build-mandatory-context-decomposition` is mostly independent
- shared substrate:
  - Stage 2 tranche pair shares orchestration conventions and regression surface
- merge opportunities:
  - none before queue completion; keep Stage 2 and Stage 4 realization separate

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`

1. `stage2-finalizer-run-finalize-decomposition`
2. `stage2-orchestrator-stage-2-arcs-async-logic-decomposition`
3. `stage4-context-builder-build-mandatory-context-decomposition`

Rationale:
- the first item is the strongest Stage 2 blocker and has the clearest test-backed substrate leverage
- the second item depends conceptually on the first
- the third item is high-ROI but independent, so it can wait until the Stage 2 pair is stabilized

## 5. Per-Item Plan

### stage2-finalizer-run-finalize-decomposition
- goal: reduce `run_finalize` to a wrapper over explicit phase helpers
- prerequisites:
  - re-audit the SSOT against live workspace state
  - confirm Stage 2 policy semantics are unchanged
- validity gate before execution:
  - target file and direct tests still match the hotspot survey
  - no newer Stage 2 policy item supersedes this refactor
- completion signal:
  - targeted Stage 2 tests pass
  - temp mirror removed after closure

### stage2-orchestrator-stage-2-arcs-async-logic-decomposition
- goal: split the Stage 2 async pipeline into startup, batch, and finalize/recovery phases
- prerequisites:
  - first item closed or at minimum revalidated and not superseded
  - Stage 2 smoke/determinism queue not reopened with conflicting semantics
- validity gate before execution:
  - Stage 2 substrate still aligns with the first item outcome
  - no new Stage 2 live-merge issue changes ordering
- completion signal:
  - Stage 2 pipeline and golden-route tests pass
  - temp mirror removed after closure

### stage4-context-builder-build-mandatory-context-decomposition
- goal: lower branch density by extracting context section assemblers
- prerequisites:
  - no new Stage 4 sovereignty / retry-policy item has reopened the same file with higher priority
- validity gate before execution:
  - returned payload contract still matches existing tests
  - no fresh Stage 4 incident elevates this file from refactor target to policy target
- completion signal:
  - Stage 4 context-builder tests pass
  - temp mirror removed after closure

## 6. Shared Risks and Side-Effects
- shared write paths:
  - none intended beyond ordinary code/doc/test edits
- shared DB/schema touchpoints:
  - runtime semantics should remain unchanged; schema changes are out of scope
- shared logs/UI surfaces:
  - Stage 2 and Stage 4 operator outputs must remain unchanged
- rollback/recovery concerns:
  - each item must be realizable as same-file helper extraction, not architectural rewrite
- queue collision risks:
  - Stage 2 items should not run out of order

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `stage2-finalizer-run-finalize-decomposition` | completed | 2026-03-20 | none |
| `stage2-orchestrator-stage-2-arcs-async-logic-decomposition` | completed | 2026-03-20 | none |
| `stage4-context-builder-build-mandatory-context-decomposition` | completed | 2026-03-20 | none |

## 8. Queue Cleanup Rule
- remove each temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- long-function decomposition queue is exhausted; no active temp execution artifacts remain
- leave `docs/temp/README.md`
