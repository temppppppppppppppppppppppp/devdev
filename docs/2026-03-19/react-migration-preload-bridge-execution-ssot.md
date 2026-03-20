# React Migration Preload Bridge Execution SSOT

Date: 2026-03-19
Status: active
Canonical Path: `docs/2026-03-19/react-migration-preload-bridge-execution-ssot.md`
Temp Mirror Path: `docs/temp/react-migration-preload-bridge-execution-ssot.md`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: broad in-flight remediation tree; desktop/runtime/tests/docs all already active`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same working session; first React lane execution SSOT opened after frontend full survey`
Source Survey Docs:
- `docs/2026-03-19/react-migration-program-charter-3pass-audit.md`
- `docs/2026-03-19/react-migration-full-survey-audit-order.md`
- `docs/2026-03-19/react-migration-frontend-full-survey-3pass-audit.md`
Evidence Artifacts:
- direct live file reading only; no separate evidence txt created yet
Side-Effect Coverage: covered

## 1. Intent

- Realize the preload and desktop bridge lane first, before any user-visible React panel migration.
- Preserve the live `window.geuldobiDesktop` contract while creating room for typed or componentized renderer consumers later.
- Keep desktop shell authority explicit so React does not blur main/preload/renderer ownership.

## 2. Baseline Facts

- Authoritative main process entry remains `geuldobi-desktop/src/main.js`.
- Authoritative preload entry remains `geuldobi-desktop/src/preload.js`.
- Authoritative preload contract source remains `geuldobi-desktop/src/desktop_control_plane_contract.js`.
- `desktop-ipc-surface-contract-v1.json` still lists two active renderer consumers:
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/src/splash/splash.js`
- Live preload surface currently exposes `25` methods through `window.geuldobiDesktop`.
- `geuldobi-desktop/src/main.js` currently contains `23` `ipcMain.handle` registrations.
- The preload surface still mixes:
  - splash bootstrap
  - app-ready handoff
  - run/stop/status control
  - quality/operator reads
  - settings persistence
  - material manager operations
  - prompt resolution
  - project/work-guard flows
  - workspace utility flows

## 3. Scope

Included:

- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/desktop_control_plane_contract.js`
- `docs/implementation/desktop-ipc-surface-contract-v1.json`
- `tests/test_desktop_preload_bridge_behavior.js`
- `tests/test_desktop_work_guard_template_contract.py`
- `tests/test_desktop_direct_surface_contract.py`

Excluded:

- React panel/component realization inside the renderer
- `index.html` office/canvas state migration
- packaging/build pipeline changes beyond what is necessary to preserve preload authority
- backend route semantics and HTTP contract redesign

## 4. Pass 1. Inventory Summary

- Current preload exposure root: `contextBridge.exposeInMainWorld("geuldobiDesktop", ...)`
- Current compatibility root name is fixed: `window.geuldobiDesktop`
- Live method groups:
  - splash bootstrap: `getSplashConfig`, `notifyBackendReady`, `onAppReady`
  - run control: `runKey`, `stopRun`, `getStatus`
  - operator surfaces: `getQualitySummary`, `getQualityDashboard`, `getSafeOpsPreview`, `saveQualityReview`
  - bootstrap/runtime metadata: `getBackendUrl`, `getCliContract`
  - settings/project/material: `saveSettings`, `loadSettings`, `listProjects`, `createProject`, `loadProjectConfigSurfaces`, `saveProjectConfigSurfaces`, `listMaterialFiles`, `importMaterialFile`, `deleteMaterialFile`
  - prompt/work-guard/workspace: `resolvePrompt`, `listWorkGuardTemplates`, `applyWorkGuardTemplate`, `openWorkspaceFolder`
- Current contract tests already assert:
  - parity between `preload.js` and `desktop_control_plane_contract.js`
  - exact `PRELOAD_METHOD_CHANNELS` extraction shape
  - work-guard template method presence in preload and main
  - direct live path authority for `src/main.js` and `src/preload.js`

## 5. Pass 2. Semantic Classification

- Class A. Authority-bearing surfaces
  - `src/preload.js`
  - `src/main.js`
  - `src/desktop_control_plane_contract.js`
  - `desktop-ipc-surface-contract-v1.json`
- Class B. Compatibility-boundary surfaces
  - `window.geuldobiDesktop`
  - splash handoff calls
  - run/status/prompt bridge calls
- Class C. Deferred realization surfaces
  - React component consumers that may later call the bridge
  - typed renderer facades behind the same exposed surface

Operational interpretation:

- This lane is substrate first.
- The first safe migration work is not renaming files or replacing the preload root.
- The first safe migration work is making the bridge boundary easier to consume without changing authority.

## 6. Side-Effect Map

- file writes / artifacts:
  - `geuldobi-desktop/src/preload.js`
  - `geuldobi-desktop/src/main.js`
  - `geuldobi-desktop/src/desktop_control_plane_contract.js`
  - `docs/implementation/desktop-ipc-surface-contract-v1.json`
  - preload/bridge tests
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - not primary for this lane
  - any bridge contract drift should surface through tests and docs, not runtime JSONL first
- console / UI / operator output:
  - splash readiness
  - renderer run/stop/status behavior
  - prompt resolution path
  - settings/work-guard/project UX
- rollback / recovery / retry:
  - splash handoff and app-ready timing are rollback-critical
  - channel drift can break renderer boot before React ever mounts
- cache / global state:
  - `window.geuldobiDesktop`
  - renderer consumer assumptions in `src/index.html` and `src/splash/splash.js`
- bootstrap fallback / config-env mutation:
  - splash bootstrap APIs
  - app-ready signal
  - no env mutation should be introduced casually here

## 7. Realization Architecture

- Keep `src/preload.js` authoritative until late roadmap-authorized consolidation.
- Keep `window.geuldobiDesktop` as the compatibility surface during hybrid migration.
- Move toward a typed or centrally generated bridge contract from `desktop_control_plane_contract.js`, but do not split runtime truth across multiple competing channel definitions.
- Any new renderer-facing wrapper must remain a thin adapter over the existing preload surface until lane C and lane A are ready.
- `src/main.js` handler ownership remains explicit; React does not get to bypass the preload boundary.

## 8. Execution Tranches

1. Contract normalization
   - ensure `desktop_control_plane_contract.js`, `preload.js`, and `desktop-ipc-surface-contract-v1.json` stay singular and aligned
2. Compatibility-preserving adapter layer
   - introduce typed or modular bridge consumption without changing exposed surface name or channel names
3. Consumer migration preparation
   - prepare React-facing bridge utilities for later lane C and lane A adoption while keeping current `index.html` and `splash.js` live

## 9. Acceptance Criteria

- `window.geuldobiDesktop` remains the live exposed root unless the single roadmap explicitly authorizes a switch.
- All `25` live preload methods remain present or any delta is explicitly documented and test-updated in the same tranche.
- `src/index.html` and `src/splash/splash.js` continue to work against the same authoritative preload entry.
- No silent IPC channel rename lands without contract-doc and test updates in the same change set.
- Splash bootstrap and app-ready handoff remain operational through hybrid React adoption.

## 10. Verification Plan

- `python -m pytest tests/test_desktop_work_guard_template_contract.py -q`
- `node tests/test_desktop_preload_bridge_behavior.js`
- `python -m pytest tests/test_desktop_direct_surface_contract.py -q`
- later realization tranches should also re-run the desktop subset gate from `package.json` and the roadmap-selected runtime smoke path

## 11. Guardrails

- Do not rename `src/preload.js` or `src/main.js` in this lane without explicit roadmap approval.
- Do not replace `window.geuldobiDesktop` with a React-only abstraction early.
- Do not split channel truth across contract files, ad-hoc wrappers, and component code.
- Do not fold splash bootstrap into the main renderer migration; splash remains a separate live consumer.
- Do not create a `dist`-first preload/main authority before the packaging lane has its own SSOT.

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition: no temp mirror until React realization queue is activated by the single roadmap
- roadmap dependency: must be ordered by the future canonical React execution roadmap

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## Confidence Gate

Estimated confidence for this execution-SSOT purpose: **96%**

Why this clears the gate:

- live preload/main/contract surfaces were read directly
- active consumer files and parity tests were read directly
- the lane boundary is narrow and authority-bearing
- rollback stance is strongly constrained by current runtime contracts

Residual uncertainty:

- exact typed-bridge generation strategy is intentionally deferred
- some channel ownership may move later once lane C and lane A execution docs exist
