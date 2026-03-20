# React Migration Execution Roadmap

Date: 2026-03-19
Status: active
Canonical Path: `docs/2026-03-19/react-migration-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: broad in-flight remediation tree; desktop/runtime/tests/docs all already active`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same working session; first canonical React roadmap opened after four lane execution SSOTs`
Queue Snapshot:
- canonical-only planning phase; no active `docs/temp/` React mirrors yet
- `docs/2026-03-19/react-migration-preload-bridge-execution-ssot.md`
- `docs/2026-03-19/react-migration-test-harness-packaging-execution-ssot.md`
- `docs/2026-03-19/react-migration-control-plane-quality-execution-ssot.md`
- `docs/2026-03-19/react-migration-renderer-state-view-execution-ssot.md`

## 1. Purpose

- Provide the single SSOT roadmap for the active React migration bundle.
- Govern the order and dependency semantics across the four React lane execution SSOTs.
- Keep React authority singular so the program does not fragment into competing per-lane roadmaps.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| preload-bridge | `docs/2026-03-19/react-migration-preload-bridge-execution-ssot.md` | not created yet | in_progress | bridge client and live preload contract inventory landed without authority flip |
| test-harness-packaging | `docs/2026-03-19/react-migration-test-harness-packaging-execution-ssot.md` | not created yet | in_progress | explicit desktop contract scripts and packaging/test guardrails landed |
| control-plane-quality | `docs/2026-03-19/react-migration-control-plane-quality-execution-ssot.md` | not created yet | in_progress | quality/operator read-only surfaces are now largely externalized behind runtime/helpers/bootstrap with inline fallback retained |
| renderer-state-view | `docs/2026-03-19/react-migration-renderer-state-view-execution-ssot.md` | not created yet | in_progress | shell/status/log/material/view plus accordion/gating, workspace assembly, modal/tab shell state, simple toggle UI, prompt overlay shell state, and pure state-update wrappers are moving behind renderer-state helpers/bootstrap while canvas/prompt authority stays inline |

## 3. Dependency Graph

- `preload-bridge -> control-plane-quality`
- `test-harness-packaging -> control-plane-quality`
- `control-plane-quality -> renderer-state-view`
- `preload-bridge -> renderer-state-view`
- `test-harness-packaging -> renderer-state-view`

shared substrate:

- preload/main authority
- shipping/runtime authority docs
- `contract_safe` gate
- direct-surface and bridge contract tests

merge opportunities:

- early contract normalization work across preload-bridge and test-harness-packaging
- later hybrid rollback design shared by control-plane-quality and renderer-state-view

## 4. Execution Order

Priority basis:

- `docs/implementation/queue-priority-rubric.md`

1. preload-bridge
2. test-harness-packaging
3. control-plane-quality
4. renderer-state-view

Roadmap interpretation:

- item 1 and item 2 are both substrate lanes and may interleave in documentation and review
- item 3 is the first user-visible realization target, but only after items 1 and 2 have active guardrails
- item 4 stays late by default

## 5. Per-Item Plan

### preload-bridge

- goal:
  preserve live preload/main authority while creating a typed or modular bridge consumption path for later React consumers
- prerequisites:
  none beyond current canonical React survey bundle
- execution notes:
  keep `src/preload.js`, `src/main.js`, and `window.geuldobiDesktop` authoritative through early hybrid phases
- completion signal:
  bridge contract is normalized and later React consumers can use it without changing authority paths
- temp cleanup action:
  if a temp mirror is later created for realization, remove it immediately after closure

### test-harness-packaging

- goal:
  keep runtime authority, packaging shape, shipping docs, and `contract_safe` gate aligned through React rollout
- prerequisites:
  none beyond current canonical React survey bundle
- execution notes:
  no `dist`-style renderer shipping change should land before this lane documents the dual-layout or authority-flip posture
- completion signal:
  package/build/runtime docs and contract tests agree on the active React migration posture
- temp cleanup action:
  if a temp mirror is later created for realization, remove it immediately after closure

### control-plane-quality

- goal:
  realize the first bounded React islands on read-heavy operator panels without disturbing office/canvas ownership
- prerequisites:
  preload-bridge and test-harness-packaging guardrails are active
- execution notes:
  preserve bridge-managed reads and operator signal semantics; move panels, not the whole shell
- completion signal:
  quality/operator islands can run with explicit rollback boundaries and unchanged contract semantics
- temp cleanup action:
  if a temp mirror is later created for realization, remove it immediately after closure

### renderer-state-view

- goal:
  late decomposition of the shell/office/global-state monolith after earlier lanes reduce hybrid risk
- prerequisites:
  control-plane-quality stabilized; preload-bridge and packaging/test authority settled
- execution notes:
  prioritize state and ownership containment before major render-tree replacement
- completion signal:
  renderer monolith pressure is materially reduced without losing shell-wide rollback clarity
- temp cleanup action:
  if a temp mirror is later created for realization, remove it immediately after closure

## 6. Shared Risks and Side-Effects

- shared write paths:
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/src/main.js`
  - `geuldobi-desktop/src/preload.js`
  - `geuldobi-desktop/src/desktop_control_plane_contract.js`
  - `geuldobi-desktop/package.json`
  - runtime/containment/IPC contract docs
  - desktop contract tests
- shared DB/schema touchpoints:
  - not primary in this roadmap
- shared logs/UI surfaces:
  - runtime health
  - operator quality panels
  - splash/app-ready handoff
  - run/stop/status shell UX
- rollback/recovery concerns:
  - path-authority drift
  - hybrid ownership collisions
  - splash/bootstrap breakage
  - invisible `contract_safe` weakening
- queue collision or ordering risks:
  - lane 3 moving before lane 1/2 substrate hardens
  - lane 4 being mistaken for an early UI cleanup lane

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| preload-bridge | in_progress | 2026-03-19 | keep `window.geuldobiDesktop` authority stable while later consumers standardize on bridge client/contract inventory |
| test-harness-packaging | in_progress | 2026-03-19 | maintain explicit desktop contract/packaging gates while renderer rollout expands |
| control-plane-quality | in_progress | 2026-03-20 | lane is in late-stage stabilization; most read-only quality surfaces already sit behind runtime/helpers/bootstrap with inline fallback retained |
| renderer-state-view | in_progress | 2026-03-20 | lane has reached the high-risk boundary; next step should be office animation/runtime isolation before any prompt, canvas ownership, or run/stop authority move |

Allowed statuses:

- pending
- in_progress
- completed
- blocked

## 8. Queue Cleanup Rule

- keep React docs canonical-only until realization queue activation
- if temp execution SSOT mirrors are later created, remove each mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all React items are completed, remove `docs/temp/execution-roadmap.md` if it was ever created
- remove `docs/temp/queue-state.json` if present
- leave `docs/temp/README.md`

## Confidence Gate

Estimated confidence for this roadmap purpose: **95%**

Why this clears the gate:

- the roadmap is derived from four live-backed lane execution SSOTs, not OPUS prose alone
- dependency order is explicit and consistent with the survey's substrate-first findings
- the single-roadmap rule is preserved

Residual uncertainty:

- exact tranche boundaries inside each lane may still shift during later lane-level re-audit
- temp queue activation timing remains intentionally deferred until realization starts
- the next renderer tranche should follow `docs/2026-03-20/react-office-animation-runtime-isolation-audit.md` rather than directly attempting React ownership of canvas/runtime code
