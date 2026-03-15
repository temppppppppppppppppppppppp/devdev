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
| source text and runtime/output encoding hygiene | `docs/2026-03-15/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md` | `docs/temp/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md` | pending | repairs active source corruption and restores trustworthy operator/output encoding behavior |
| persistence/observability finalization and sink alignment | `docs/2026-03-15/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md` | `docs/temp/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md` | pending | runtime-proven lane for stale summary timing, late writes, session-id split, and Stage 4 rationale drift |
| backend-front/control-plane connectivity | `docs/2026-03-15/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md` | `docs/temp/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md` | pending | source-led desktop/control-plane hardening remains active |
| runtime/operator surface unification | `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md` | `docs/temp/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md` | pending | narrowed structural prompt-authority lane after latest CLI fixes held |

## 3. Dependency Graph
- `source-text-and-runtime-encoding hygiene -> persistence finalization`
- `source-text-and-runtime-encoding hygiene -> backend-front/control-plane connectivity`
- `backend-front/control-plane connectivity -> runtime/operator surface unification`
- `persistence finalization -> runtime/operator surface unification`
- shared substrate:
  - trustworthy text/output encoding
  - durable sink semantics
  - explicit control-plane contracts

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`

1. source text and runtime/output encoding hygiene
2. persistence/observability finalization and sink alignment
3. backend-front/control-plane connectivity
4. runtime/operator surface unification

## 5. Per-Item Plan

### source text and runtime/output encoding hygiene
- goal: remove active source corruption and make operator/output hygiene tooling trustworthy
- prerequisites: none
- completion signal: scoped source corruption is gone and shell-safe detector output is stable
- temp cleanup action: remove its temp mirror after closure

### persistence/observability finalization and sink alignment
- goal: stop late writes after close, finalize summary at a quiescent point, unify session/sink lineage, and close Stage 4 rationale mismatches
- prerequisites: source/output hygiene should land first so shutdown and summary logs stay readable during implementation
- completion signal: bounded live rerun shows no late-write failures and aligned sink counts/timestamps
- temp cleanup action: remove its temp mirror after closure

### backend-front/control-plane connectivity
- goal: separate command readiness from websocket readiness and close prompt/reconnect drift
- prerequisites: source/output hygiene should land first; persistence lane may proceed independently
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
  - shutdown lifecycle, reconnect, prompt timeout/default, and non-interactive harness safety
- queue collision or ordering risks:
  - doing persistence finalization before text/output hygiene would make runtime proof harder to read and debug
  - doing prompt unification before persistence and desktop contract repair risks re-editing telemetry semantics twice

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| source text and runtime/output encoding hygiene | pending | 2026-03-15 | none |
| persistence/observability finalization and sink alignment | pending | 2026-03-15 | waits on text/output hygiene for clean operator diagnostics |
| backend-front/control-plane connectivity | pending | 2026-03-15 | waits on text/output hygiene only |
| runtime/operator surface unification | pending | 2026-03-15 | waits on lanes 1-3 |

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all items are completed, remove `docs/temp/execution-roadmap.md`
- leave `docs/temp/README.md`
