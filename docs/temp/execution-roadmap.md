# codebase-global-log-evidence-merged Aggregate Execution Roadmap

Date: 2026-03-15
Status: active
Canonical Path: `docs/2026-03-15/codebase-global-log-evidence-merged-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- Baseline Dirty Summary: `dirty: unrelated investment/style/pdf/log artifacts already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Queue Snapshot: `docs/temp/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md`; `docs/temp/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md`; `docs/temp/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md`; `docs/temp/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md`

## 1. Purpose
- Govern the action-bearing execution queue created by the log-inclusive deep global survey.
- Keep one roadmap with SSOT authority for the active queue.
- Order runtime-proven defects ahead of source-led structural hardening without dropping the desktop/control-plane lane.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| persistence/observability finalization and sink alignment | `docs/2026-03-15/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md` | `docs/temp/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md` | pending | runtime-proven lane for stale summary timing, late writes, session-id split, artifact-hash drift, teardown exceptions, and Stage 4 rationale drift |
| source text and runtime/output encoding hygiene | `docs/2026-03-15/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md` | `docs/temp/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md` | pending | repairs active source corruption and restores trustworthy operator/output encoding behavior |
| backend-front/control-plane connectivity | `docs/2026-03-15/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md` | `docs/temp/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md` | pending | source-led desktop/control-plane hardening remains active |
| runtime/operator surface unification | `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md` | `docs/temp/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md` | pending | narrowed structural prompt-authority lane after latest CLI fixes held |

## 3. Dependency Graph
- `persistence finalization -> source-text-and-runtime-encoding hygiene`
- `source-text-and-runtime-encoding hygiene -> backend-front/control-plane connectivity`
- `backend-front/control-plane connectivity -> runtime/operator surface unification`
- `persistence finalization -> runtime/operator surface unification`
- shared substrate:
  - durable sink semantics
  - trustworthy text/output encoding
  - explicit control-plane contracts

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`

1. persistence/observability finalization and sink alignment
2. source text and runtime/output encoding hygiene
3. backend-front/control-plane connectivity
4. runtime/operator surface unification

## 5. Per-Item Plan

### persistence/observability finalization and sink alignment
- goal: stop late writes after close, finalize summary at a quiescent point, unify session/sink lineage, restore artifact-hash truth, and eliminate teardown exceptions plus Stage 4 rationale mismatches
- prerequisites: none
- completion signal: bounded live rerun shows no late-write failures, aligned sink counts/timestamps, aligned artifact hashes, and clean shutdown completion
- temp cleanup action: remove its temp mirror after closure

### source text and runtime/output encoding hygiene
- goal: remove active source corruption and make operator/output hygiene tooling trustworthy
- prerequisites: persistence finalization should land first so runtime-owned logs, artifact evidence, and shutdown diagnostics do not keep changing underneath this lane
- completion signal: scoped source corruption is gone and shell-safe detector output is stable
- temp cleanup action: remove its temp mirror after closure

### backend-front/control-plane connectivity
- goal: separate command readiness from websocket readiness and close prompt/reconnect drift
- prerequisites: persistence finalization should land first; source/output hygiene should land before final operator-surface polish
- completion signal: renderer/backend contract is explicit and regression-tested
- temp cleanup action: remove its temp mirror after closure

### runtime/operator surface unification
- goal: reduce remaining prompt-authority fragmentation without reopening current user-facing fixes
- prerequisites: source/output hygiene, persistence finalization, and backend-front contract changes should already be stabilized
- completion signal: prompt authority is measurably more centralized and current CLI behavior is retained
- temp cleanup action: remove its temp mirror after closure

## 6. Shared Risks And Side-Effects
- shared write paths:
  - runtime source files, tests, desktop control-plane files, and dated docs
- shared DB/schema touchpoints:
  - mostly the second lane; other lanes should avoid opportunistic DB changes
- shared logs/UI surfaces:
  - operator-visible text, shutdown output, prompt telemetry, bridge diagnostics
- rollback/recovery concerns:
  - shutdown lifecycle, teardown quiescence, reconnect, prompt timeout/default, and non-interactive harness safety
- queue collision or ordering risks:
  - doing text/output hygiene before persistence finalization would leave the highest-value runtime truth surfaces unresolved and could force a second edit pass through the same operator evidence
  - doing prompt unification before persistence and desktop contract repair risks re-editing telemetry semantics twice

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| persistence/observability finalization and sink alignment | pending | 2026-03-15 | none |
| source text and runtime/output encoding hygiene | pending | 2026-03-15 | waits on persistence finalization so operator evidence and artifact lineage stop moving |
| backend-front/control-plane connectivity | pending | 2026-03-15 | waits on text/output hygiene only |
| runtime/operator surface unification | pending | 2026-03-15 | waits on lanes 1-3 |

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all items are completed, remove `docs/temp/execution-roadmap.md`
- leave `docs/temp/README.md`
