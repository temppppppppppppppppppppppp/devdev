# Desktop Control Plane Surface Hardening Execution SSOT

Date: 2026-03-14
Status: closed
Canonical Path: `docs/2026-03-14/desktop-control-plane-surface-hardening-execution-ssot.md`
Temp Mirror Path: `docs/temp/desktop-control-plane-surface-hardening-execution-ssot.md`
Source Survey Docs:
- `docs/2026-03-14/codebase-global-rol-deep-global-survey.md`
- `docs/2026-03-14/codebase-global-rol-system-full-survey-3pass-audit.md`
Evidence Artifacts:
- `docs/2026-03-14/codebase-global-rol-deep-survey-entrypoints.txt`
- `docs/2026-03-14/codebase-global-rol-deep-survey-side-effects.json`
- `docs/2026-03-14/codebase-global-rol-deep-survey-regression-surface.txt`
- `docs/2026-03-14/codebase-global-rol-system-survey-entrypoints.txt`
- `docs/2026-03-14/codebase-global-rol-system-survey-side-effects.json`
- `docs/2026-03-14/codebase-global-rol-system-survey-regression-surface.txt`
Side-Effect Coverage: covered
Confidence Target: 95%
Live Workspace Revalidation: 2026-03-14 PASS
Revalidated Confidence: 97%

## 1. Intent
- Harden the desktop control plane around one authoritative runtime surface.
- Keep Electron main, preload, backend HTTP/WebSocket, and subprocess runner contracts synchronized.
- Reduce drift risk between authoritative, compatibility, and debug entry files.

## 2. Baseline Facts
- `geuldobi-desktop/src/main.js` is the authoritative Electron main process and is `898` LOC.
- `geuldobi-desktop/package.json` points `main` at `src/main.js`, which agrees with the desktop runtime contract and the shadow hygiene tests.
- `modules/api/bridge_server.py` is `1764` LOC and owns the HTTP plus WebSocket backend control plane.
- `modules/api/process_runner.py` is `794` LOC and owns the subprocess boundary to `main_a.py`.
- `geuldobi-desktop/main.js` is a clean compatibility shim, but the root `main.js` remains a manual debug shadow with duplicated runtime logic.
- `geuldobi-desktop/temp-electron-loadcheck.js` and `geuldobi-desktop/temp-electron-paths.js` are auxiliary Electron probes, not runtime authorities, but they enlarge the stale-edit surface.
- Live contracts already exist in:
  - `docs/implementation/desktop-runtime-contract-v1.json`
  - `docs/implementation/desktop-ipc-surface-contract-v1.json`
  - `docs/implementation/api-contract-v1.yaml`
  - `docs/implementation/event-schema-v1.json`

## 3. Pass 1. Inventory Summary
- authoritative desktop files:
  - `geuldobi-desktop/src/main.js`
  - `geuldobi-desktop/src/preload.js`
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/src/splash/splash.js`
- backend authority:
  - `modules/api/bridge_server.py`
  - `modules/api/process_runner.py`
  - `modules/api/prompt_broker.py`
- contract and regression authority:
  - `tests/test_desktop_shadow_hygiene.py`
  - `tests/test_desktop_direct_surface_contract.py`
  - `tests/test_desktop_transport_contract.py`
  - `tests/test_bridge_server_http_contract.py`
  - `tests/test_bridge_server_desktop_risk_gate.py`

## 4. Pass 2. Semantic Classification

### Class A. Process and Spawn Ownership
- Electron main spawns the backend and writes debug logs and settings.
- `ProcessRunner` spawns `main_a.py` and owns prompt and stream handling.

### Class B. Bridge and Contract Ownership
- preload exposes the IPC bridge to the renderer
- backend exposes `/run`, `/stop`, `/status`, `/events`, and operator-quality routes
- event schema and API contract already exist but must stay aligned with code

### Class C. Ownership Drift Risks
- `geuldobi-desktop/main.js` is fenced as a shim
- root `main.js` still resembles a runtime shadow and can confuse future edits if not explicitly governed

## 5. Side-Effect Map
- subprocess:
  - backend spawn and stop from Electron main
  - engine spawn and prompt handling from `ProcessRunner`
- network:
  - splash direct `/status` poll
  - renderer direct WebSocket `/events`
  - bridge-managed backend HTTP routes
- file writes:
  - `electron-main.log`
  - settings JSON
  - backend control-plane provenance JSONL
- env mutation:
  - desktop packaged env wiring for backend and workspace roots

## 6. Realization Architecture
- Keep one authoritative desktop runtime entry and explicitly fence all compatibility or debug shadows.
- Define a contract-refresh path that validates:
  - IPC surface
  - backend route inventory
  - event schema
  - packaged env and resource assumptions
- Reduce bridge drift by moving repeated channel or route ownership into clearly tested contract maps where practical.

## 7. Execution Tranches
1. Fence shadow and compatibility entries so only the authoritative live desktop surface owns runtime behavior.
2. Reconcile preload methods, backend routes, and event types against the contract docs.
3. Harden spawn, env, and workspace ownership boundaries between Electron main and the backend.
4. Refresh the desktop and backend contract regression set after contract alignment changes.

## 8. Acceptance Criteria
- One authoritative desktop runtime surface is unambiguous.
- Debug or compatibility shadows cannot silently become live control-plane authorities.
- Preload, backend routes, and WebSocket event contracts are synchronized with tests and documentation.
- Packaged env and resource assumptions remain explicit and regression-tested.

## 9. Verification Plan
- `tests/test_desktop_shadow_hygiene.py`
- `tests/test_desktop_transport_contract.py`
- `tests/test_desktop_direct_surface_contract.py`
- `tests/test_bridge_server_http_contract.py`
- `tests/test_bridge_server_desktop_risk_gate.py`
- packaged/desktop contract subset from `geuldobi-desktop/package.json`

## 9A. Current-State Revalidation
- Revalidated against live workspace changes in `geuldobi-desktop/src/main.js`, `geuldobi-desktop/src/preload.js`, `geuldobi-desktop/main.js`, `main.js`, `modules/api/bridge_server.py`, `modules/api/process_runner.py`, `geuldobi-desktop/package.json`, and the desktop contract tests.
- `geuldobi-desktop/main.js` is now an explicit `10`-line compatibility shim that delegates to `./src/main.js`.
- The root `main.js` is now a thin manual-debug shadow shim that delegates to `./geuldobi-desktop/src/main.js` and no longer carries duplicated runtime/control-plane logic.
- `geuldobi-desktop/src/main.js` and `src/preload.js` now carry explicit bridge transport constants plus `approvalId` propagation, while `bridge_server.py` exposes an explicit control-plane provenance log path. Those are contract-surface changes, not a reason to split or reorder the roadmap item.
- Tranche 2 landed. `geuldobi-desktop/src/desktop_control_plane_contract.js` now owns shared IPC channel names and bridge-managed route inventory for both `src/main.js` and `src/preload.js`.
- Focused verification passed:
  - `14` tests across desktop shadow hygiene, surface containment, transport contract, direct surface contract, and desktop risk-gate coverage
  - `20` tests across desktop packaging, runtime paths, desktop contract refresh, and desktop work-guard template contract coverage
  - node smoke: `tests/test_desktop_preload_bridge_behavior.js`, `tests/test_desktop_material_offline_behavior.js`, `tests/test_splash_runtime_behavior.js`
- Revalidation outcome: acceptance criteria satisfied for this item. Shadow authority, preload/main IPC naming, bridge-managed route inventory, and packaging/runtime assumptions are now explicitly fenced and regression-backed.

## 10. Guardrails
- Do not mix renderer UI redesign with control-plane hardening.
- Do not let root `main.js` become authoritative for packaged/runtime changes.
- Do not change direct-network allowlists without refreshing the API and transport contracts.

## 11. Temp Queue Notes
- temp status: pending
- cleanup condition: remove mirror after implementation and closure
- roadmap dependency: execute after Stage 0 and operator-event contract decisions are stable enough to avoid duplicate bridge churn

## 12. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 13. Closure Note
- closure status: `closed`
- verification evidence:
  - `python -m pytest -q tests/test_desktop_shadow_hygiene.py tests/test_surface_containment_contract.py tests/test_desktop_direct_surface_contract.py tests/test_desktop_transport_contract.py tests/test_bridge_server_desktop_risk_gate.py`
  - `python -m pytest -q tests/test_desktop_packaging_contract.py tests/test_runtime_paths.py tests/test_desktop_contract_refresh.py tests/test_desktop_work_guard_template_contract.py`
  - `node tests/test_desktop_preload_bridge_behavior.js`
  - `node tests/test_desktop_material_offline_behavior.js`
  - `node tests/test_splash_runtime_behavior.js`
- residual risk:
  - renderer UI churn is intentionally out of scope for this control-plane item.
  - downstream regression/canary tier separation remains active in the final queue item.
- temp cleanup action: remove `docs/temp/desktop-control-plane-surface-hardening-execution-ssot.md` after roadmap and queue synchronization.
