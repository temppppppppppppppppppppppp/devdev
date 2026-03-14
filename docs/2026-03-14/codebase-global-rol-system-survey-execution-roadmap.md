# Codebase Global ROL System Survey Aggregate Execution Roadmap

Date: 2026-03-14
Status: active
Canonical Path: `docs/2026-03-14/codebase-global-rol-system-survey-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Source Survey Docs:
- `docs/2026-03-14/codebase-global-rol-deep-global-survey.md`
- `docs/2026-03-14/codebase-global-rol-system-full-survey-3pass-audit.md`
Roadmap Authority: `single-ssot`
Live Workspace Revalidation: 2026-03-14 PASS
Revalidated Confidence: 96%
Queue Snapshot:
- `docs/temp/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md`
- `docs/temp/runtime-bootstrap-orchestration-hardening-execution-ssot.md`
- `docs/temp/stage0-operator-surface-contract-hardening-execution-ssot.md`
- `docs/temp/desktop-control-plane-surface-hardening-execution-ssot.md`
- `docs/temp/regression-canary-surface-rationalization-execution-ssot.md`

## 1. Purpose
- Control multi-item realization order after the codebase-global survey produced multiple execution SSOTs.
- Keep the global survey bundle actionable without allowing ad hoc or contradictory implementation order.
- Act as the only roadmap with SSOT authority for the currently active deep global survey bundle.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `residual-print-ui-log-db-full-survey-3pass` | `docs/2026-03-14/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md` | `docs/temp/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md` | in_progress | tranche 1 substrate landed; tranche 2 core runtime conversion landed; Stage 0/menu allowlist remains |
| `runtime-bootstrap-orchestration-hardening` | `docs/2026-03-14/runtime-bootstrap-orchestration-hardening-execution-ssot.md` | `docs/temp/runtime-bootstrap-orchestration-hardening-execution-ssot.md` | pending | reduces monolithic runtime ownership |
| `stage0-operator-surface-contract-hardening` | `docs/2026-03-14/stage0-operator-surface-contract-hardening-execution-ssot.md` | `docs/temp/stage0-operator-surface-contract-hardening-execution-ssot.md` | pending | depends on event substrate and boot seams |
| `desktop-control-plane-surface-hardening` | `docs/2026-03-14/desktop-control-plane-surface-hardening-execution-ssot.md` | `docs/temp/desktop-control-plane-surface-hardening-execution-ssot.md` | pending | depends on stable Stage 0 and event/control contracts |
| `regression-canary-surface-rationalization` | `docs/2026-03-14/regression-canary-surface-rationalization-execution-ssot.md` | `docs/temp/regression-canary-surface-rationalization-execution-ssot.md` | pending | should run after upstream contracts stabilize |

## 3. Dependency Graph
- `residual-print-ui-log-db-full-survey-3pass` -> `runtime-bootstrap-orchestration-hardening`
- `residual-print-ui-log-db-full-survey-3pass` -> `stage0-operator-surface-contract-hardening`
- `runtime-bootstrap-orchestration-hardening` -> `stage0-operator-surface-contract-hardening`
- `residual-print-ui-log-db-full-survey-3pass` -> `desktop-control-plane-surface-hardening`
- `stage0-operator-surface-contract-hardening` -> `desktop-control-plane-surface-hardening`
- `residual-print-ui-log-db-full-survey-3pass` -> `regression-canary-surface-rationalization`
- `runtime-bootstrap-orchestration-hardening` -> `regression-canary-surface-rationalization`
- `stage0-operator-surface-contract-hardening` -> `regression-canary-surface-rationalization`
- `desktop-control-plane-surface-hardening` -> `regression-canary-surface-rationalization`

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`
- substrate-first realization over convenience-first ordering

1. `residual-print-ui-log-db-full-survey-3pass`
2. `runtime-bootstrap-orchestration-hardening`
3. `stage0-operator-surface-contract-hardening`
4. `desktop-control-plane-surface-hardening`
5. `regression-canary-surface-rationalization`

## 4A. Lane Structure
- lane 1: substrate and runtime ownership
  - `residual-print-ui-log-db-full-survey-3pass`
  - `runtime-bootstrap-orchestration-hardening`
- lane 2: operator surface and control plane
  - `stage0-operator-surface-contract-hardening`
  - `desktop-control-plane-surface-hardening`
- lane 3: verification envelope
  - `regression-canary-surface-rationalization`

## 5. Per-Item Plan

### residual-print-ui-log-db-full-survey-3pass
- goal: establish one durable operator-visible event substrate for console, JSONL, and DB
- prerequisites: none
- execution notes: treat as the governing output contract for later queue items that emit operator-visible events
- completion signal: runtime event sink exists and residual print classes are migrated according to the doc
- temp cleanup action: remove the mirror after closure updates land in both the execution doc and this roadmap

### runtime-bootstrap-orchestration-hardening
- goal: reduce monolithic runtime ownership in `main_a.py`
- prerequisites: operator-event substrate direction is fixed enough to avoid duplicate sink design
- execution notes: keep behavior stable while extracting ownership seams
- completion signal: explicit bootstrap, runtime composition, and shutdown boundaries exist
- temp cleanup action: remove the mirror after canonical closure and roadmap ledger update

### stage0-operator-surface-contract-hardening
- goal: convert Stage 0 from a print/input-heavy CLI surface into a governed operator contract
- prerequisites: operator-event substrate and runtime seams exist
- execution notes: preserve prompts and operator checkpoints while changing the surface contract
- completion signal: Stage 0 events, prompts, and mutations are representable through one operator contract
- temp cleanup action: remove the mirror after canonical closure and roadmap ledger update

### desktop-control-plane-surface-hardening
- goal: align Electron main, preload, backend routes, and event contracts under one authoritative runtime surface
- prerequisites: Stage 0 and operator-event contracts are stable enough to avoid churn
- execution notes: fence debug and compatibility entries while keeping contract tests green
- completion signal: authoritative desktop/runtime boundaries are explicit and synchronized with contract docs
- temp cleanup action: remove the mirror after canonical closure and roadmap ledger update

### regression-canary-surface-rationalization
- goal: separate read-only contract subsets from mutation-heavy smoke and canary flows
- prerequisites: upstream runtime, Stage 0, and desktop contracts are stable enough to define lasting validation tiers
- execution notes: this is the last queue item because it should codify the validation shape after upstream changes
- completion signal: execution docs can cite bounded validation tiers rather than one undifferentiated test mass
- temp cleanup action: remove the mirror after canonical closure and roadmap ledger update

## 6. Shared Risks and Side-Effects
- shared write paths:
  - project DBs
  - JSONL sinks
  - operator-visible console frames
  - desktop settings and debug logs
- shared DB/schema touchpoints:
  - `DBManager`
  - project-local SQLite assets
  - potential future `ui_events` persistence
- shared logs and UI surfaces:
  - `ui.log`
  - Rich console
  - residual raw `print`
  - desktop `/events` stream
- rollback and recovery concerns:
  - runtime ownership and operator surface changes can invalidate downstream docs if realized out of order
  - queue items touching the same operator surfaces should not run in parallel
- roadmap authority risk:
  - do not create a second roadmap for this active bundle; extend this roadmap with lanes or notes instead

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `residual-print-ui-log-db-full-survey-3pass` | in_progress | 2026-03-14 | Stage 0/menu-heavy surfaces, bootstrap fail-safe prints, and threaded metrics-report prints still remain |
| `runtime-bootstrap-orchestration-hardening` | pending | 2026-03-14 | waits on substrate alignment |
| `stage0-operator-surface-contract-hardening` | pending | 2026-03-14 | waits on substrate and boot seams |
| `desktop-control-plane-surface-hardening` | pending | 2026-03-14 | waits on Stage 0 and contract stabilization |
| `regression-canary-surface-rationalization` | pending | 2026-03-14 | waits on upstream contract stabilization |

Allowed statuses:
- pending
- in_progress
- completed
- blocked

## 7A. Current-State Revalidation
- Revalidated against live workspace drift across runtime, observability, Stage 0, desktop, and canary surfaces. No second roadmap is justified; this document remains the only SSOT roadmap for the active queue.
- `residual-print-ui-log-db-full-survey-3pass`: still first. The durable `ui_events` substrate and the core Stage 3/4 runtime conversions have landed, but Stage 0/menu-heavy operator surfaces and explicit residual-print allowlists still belong here before downstream items should leapfrog it.
- `runtime-bootstrap-orchestration-hardening`: still second. `main_a.py` remains monolithic, while new cache-preservation and runtime-restore behaviors increase the value of extracting explicit ownership seams.
- `stage0-operator-surface-contract-hardening`: still third. Stage 0 remains `print`/`input` heavy, even though `ProjectService` now emits richer `ui.log`-based destructive-operation outcomes.
- `desktop-control-plane-surface-hardening`: still fourth. The compatibility shim hardening in `geuldobi-desktop/main.js` is real progress, but root `main.js`, preload/backend contracts, and shadow governance still need coordinated work.
- `regression-canary-surface-rationalization`: still last. Canary proof artifacts became richer, but tier separation should still be codified after upstream contracts stabilize.
- Revalidation outcome: queue order unchanged; dependency graph unchanged; all five items remain pending and active.

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all items are completed, remove `docs/temp/execution-roadmap.md`
- remove `docs/temp/queue-state.json` if present
- leave `docs/temp/README.md`
