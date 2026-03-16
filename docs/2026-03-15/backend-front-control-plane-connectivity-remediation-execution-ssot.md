# backend-front-control-plane-connectivity-remediation Execution SSOT

Date: 2026-03-15
Status: superseded-by-backend-front-control-plane-connectivity-hardening
Successor: `docs/2026-03-15/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md`
Canonical Path: `docs/2026-03-15/backend-front-control-plane-connectivity-remediation-execution-ssot.md`
Temp Mirror Path: `none`
Queue Disposition: `historical cleanroom predecessor only; excluded from active queue`
Authority Class: `historical predecessor; do not use as live execution authority`
Commit State:
- Baseline Commit: `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- Baseline Dirty Summary: `dirty: unrelated investment/style/docs/log artifacts already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs: `docs/2026-03-15/codebase-global-cleanroom-source-only-3pass-audit.md`; `docs/2026-03-15/codebase-global-cleanroom-source-only-deep-global-survey.md`
Evidence Artifacts: `docs/2026-03-15/codebase-global-cleanroom-source-only-backend-front-connectivity.txt`; `docs/2026-03-15/codebase-global-cleanroom-source-only-surface-anchor-inventory.txt`; `docs/2026-03-15/codebase-global-cleanroom-source-only-side-effects.txt`
Side-Effect Coverage: covered

## Historical Supersession Notice

- This cleanroom execution SSOT is retained as a historical predecessor only.
- Live execution authority moved to `docs/2026-03-15/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md`, which was later realized and closed under the post-remediation roadmap.
- Any `execution-ready`, temp-path, or roadmap semantics below are historical snapshot content, not current queue state.

## 1. Intent
- Align the active desktop control plane across renderer, preload, Electron main, FastAPI bridge, `ProcessRunner`, and `PromptBroker`.
- Close source-only fresh-run risks where command readiness, websocket readiness, prompt lifecycle, reconnect behavior, and startup handoff are governed by different local rules.

## 2. Baseline Facts
- `runKey()` goes through preload -> Electron main -> `bridgeFetch()` -> backend HTTP, but renderer run actions are still gated by `_backendConnected`, which is driven by websocket state.
- `PromptBroker` can track multiple pending prompt IDs per run, but renderer ignores `prompt_request` while a dialog is already open.
- Websocket reconnect currently refreshes quality summary but does not show an explicit active-run snapshot, pending-prompt replay, or prompt-recovery contract.
- Splash readiness polls `/status` with a timeout, Electron main has an 8-second fallback handoff, and the main renderer separately waits on websocket connection.
- `bridgeFetch()` has no explicit timeout and still contains dead error-return code after an earlier return in the same branch.

## 3. Scope
Included:
- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/splash/splash.js`
- `geuldobi-desktop/src/desktop_control_plane_contract.js`
- `geuldobi-desktop/src/console_relay.js`
- `modules/api/bridge_server.py`
- `modules/api/process_runner.py`
- `modules/api/prompt_broker.py`
- `modules/api/control_plane_contract.py`
- `modules/api/prompt_classifier.py`
- `modules/api/run_validator.py`
- `docs/implementation/api-contract-v1.yaml`
- `docs/implementation/event-schema-v1.json`
- `docs/implementation/desktop-ipc-surface-contract-v1.json`
- direct desktop/control-plane regression tests

Excluded:
- raw console prompt centralization in `main_a.py`, `UIService`, and `StudioVisualizer`
- persistence sink ownership cleanup and DB boundary refactors
- historical docs, logs, DB artifacts, and runtime evidence
- asset-pack cleanup outside the active desktop control plane

## 4. Pass 1. Inventory Summary
- Renderer control state lives mainly in `index.html`.
- Electron boundary surfaces live in `preload.js`, `main.js`, and `desktop_control_plane_contract.js`.
- Backend control-plane state lives in `bridge_server.py`, `process_runner.py`, and `prompt_broker.py`.
- Current tests cover route names, schema presence, and surface inventories better than they cover live state semantics.

## 5. Pass 2. Semantic Classification
- Class A: readiness and startup handoff
  - splash polling
  - main-window websocket bootstrap
  - command-path availability
- Class B: prompt lifecycle and interactive transport
  - prompt request
  - prompt resolve
  - timeout/default behavior
  - concurrent prompt handling
- Class C: reconnect, timeout, and envelope semantics
  - websocket reconnect
  - bridge HTTP timeouts
  - direct renderer fetch exceptions
  - dead-candidate compatibility surfaces

## 6. Side-Effect Map
- file writes / artifacts:
  - source files, tests, and contract docs only
- DB / schema / transaction boundaries:
  - indirect only through project status, quality reads, or prompt-driven runtime actions
- JSONL / log / audit sinks:
  - bridge error messages, prompt lifecycle event payloads, and startup diagnostics may change
- console / UI / operator output:
  - direct primary effect
- rollback / recovery / retry:
  - reconnect, stop/terminate, prompt timeout/default, and startup fallback semantics are in scope
- cache / global state:
  - renderer `_backendConnected`, `_currentPrompt`, websocket timers, `PromptBroker` registries, `ProcessRunner` tails
- bootstrap fallback / config-env mutation:
  - splash handoff, backend URL discovery, and desktop transport envelope semantics are in scope

## 7. Realization Architecture
- Separate command-path health from websocket event-stream health.
- Define one explicit reconnect policy:
  - either resync active run and pending prompt state
  - or declare that reconnect is observability-only and prevent silent prompt loss by design
- Replace renderer silent prompt dropping with one explicit policy:
  - queue
  - reject upstream
  - or replace with provenance
- Normalize timeout and error-envelope behavior for:
  - splash status polling
  - Electron main `bridgeFetch()`
  - approved direct renderer fetches
- Reconcile splash-to-main handoff so startup readiness does not depend on conflicting timers or channels.

## 8. Execution Tranches
1. Close command-readiness drift between websocket state and bridge-managed HTTP control.
2. Define and implement prompt concurrency policy across renderer and `PromptBroker`.
3. Define reconnect/state-resync behavior and cover it with desktop/control-plane tests.
4. Normalize timeout and transport-envelope semantics across splash, bridge fetches, and approved direct renderer fetches.

## 9. Acceptance Criteria
- Renderer run actions do not depend on websocket-open state unless that dependency is explicitly justified and contract-tested.
- Concurrent prompt requests are no longer silently dropped by the renderer.
- Reconnect behavior is explicit, bounded, and regression-tested.
- Startup handoff and transport timeouts are consistent enough that fresh-run behavior is predictable by contract.

## 10. Verification Plan
- targeted pytest for desktop transport, direct surface, shadow hygiene, frontend connectivity, process runner, and API contract tests
- desktop JS tests for preload/main bridge behavior
- `python -m py_compile` for touched Python files
- contract validation where desktop/control-plane docs are updated

## 11. Guardrails
- Do not widen this lane into raw console prompt centralization; that belongs to runtime/operator surface unification.
- Do not add opportunistic DB/schema refactors here.
- Do not keep dead-candidate compatibility surfaces alive as implicit live recovery paths without an explicit contract.

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition: remove temp mirror only after realization is validated and closed
- roadmap dependency: second item in `docs/2026-03-15/codebase-global-cleanroom-source-only-execution-roadmap.md`

## 13. Validation And Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- bundle validator: `python scripts/validate_deep_global_survey_bundle.py --survey-doc docs/2026-03-15/codebase-global-cleanroom-source-only-deep-global-survey.md --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document
