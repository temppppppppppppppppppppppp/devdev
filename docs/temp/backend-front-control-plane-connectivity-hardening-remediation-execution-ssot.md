# backend-front-control-plane-connectivity-hardening-remediation Execution SSOT

Date: 2026-03-15
Status: execution-ready
Canonical Path: `docs/2026-03-15/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- Baseline Dirty Summary: `dirty: unrelated investment/style/pdf/log artifacts already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs: `docs/2026-03-15/codebase-global-log-evidence-merged-3pass-audit.md`; `docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md`
Evidence Artifacts: `docs/2026-03-15/codebase-global-log-evidence-merged-backend-front-connectivity.txt`; `docs/2026-03-15/codebase-global-log-evidence-merged-surface-anchor-inventory.txt`; `docs/2026-03-15/codebase-global-log-evidence-merged-side-effects.txt`
Side-Effect Coverage: covered

## 1. Intent
- Align renderer, preload, Electron main, bridge server, `ProcessRunner`, and `PromptBroker` under one desktop control-plane contract.
- Close source-led risks around command readiness, prompt concurrency, reconnect behavior, and startup timeout drift.

## 2. Baseline Facts
- Renderer still gates run actions on `_backendConnected` even though `runKey()` uses preload/Electron main HTTP bridge semantics.
- `PromptBroker` can track multiple pending prompt ids per run, while the renderer silently ignores concurrent `prompt_request` when a dialog is already open.
- Reconnect currently restores websocket visibility more than active-run or prompt state.
- Splash polling, Electron handoff, and `bridgeFetch()` timeout semantics are still split.
- No fresh desktop runtime proof exists in this bundle, so the lane remains source-led rather than runtime-proven.

## 3. Scope
Included:
- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/splash/splash.js`
- `geuldobi-desktop/src/desktop_control_plane_contract.js`
- `modules/api/bridge_server.py`
- `modules/api/process_runner.py`
- `modules/api/prompt_broker.py`
- `modules/api/control_plane_contract.py`
- `docs/implementation/api-contract-v1.yaml`
- `docs/implementation/event-schema-v1.json`
- `docs/implementation/desktop-ipc-surface-contract-v1.json`
- targeted desktop/control-plane regression tests

Excluded:
- raw console prompt centralization in `main_a.py`
- persistence shutdown and sink-alignment repair
- broad source-text cleanup except where touched in this lane

## 4. Pass 1. Inventory Summary
- Command path, websocket event path, and prompt lifecycle are still implemented in separate layers but not governed by one coherent readiness policy.
- Latest secured runtime evidence does not disprove these findings because it was CLI-only.

## 5. Pass 2. Semantic Classification
- Class A: command readiness vs websocket readiness
- Class B: prompt concurrency and lifecycle transport
- Class C: reconnect and startup timeout policy

## 6. Side-Effect Map
- file writes / artifacts:
  - source files, tests, and control-plane contract docs only
- DB / schema / transaction boundaries:
  - indirect only
- JSONL / log / audit sinks:
  - bridge diagnostics and prompt lifecycle events may change
- console / UI / operator output:
  - direct primary effect
- rollback / recovery / retry:
  - reconnect, prompt timeout/default, stop/terminate, startup fallback are in scope
- cache / global state:
  - renderer connection state, current prompt state, prompt registries, process tails
- bootstrap fallback / config-env mutation:
  - direct focus through splash and bridge policies

## 7. Realization Architecture
- Separate command-path health from websocket event-stream health.
- Define one explicit prompt concurrency policy instead of renderer-side silent drop.
- Define explicit reconnect and startup timeout semantics across splash, Electron main, and bridge fetches.

## 8. Execution Tranches
1. Decouple run-command readiness from websocket-open state.
2. Close prompt concurrency drift between renderer and `PromptBroker`.
3. Define reconnect/state-resync behavior and regression tests.
4. Normalize startup and timeout behavior across splash and bridge surfaces.

## 9. Acceptance Criteria
- Renderer run actions do not silently fail because websocket state and bridge command state are conflated.
- Concurrent prompts are queued, rejected upstream, or replaced by explicit policy rather than silently ignored.
- Reconnect behavior is explicit and regression-tested.
- Startup timeout behavior is predictable by contract.

## 10. Verification Plan
- targeted pytest for desktop transport, process runner, API contract, and renderer/control-plane tests
- JS-side tests or contract checks for preload/main surfaces
- `python -m py_compile` for touched Python files

## 11. Guardrails
- Do not widen this lane into raw console prompt cleanup or persistence shutdown fixes.
- Do not keep silent renderer prompt drop as an implicit policy.

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition: remove temp mirror only after realization is validated and closed
- roadmap dependency: third item in `docs/2026-03-15/codebase-global-log-evidence-merged-execution-roadmap.md`

## 13. Validation And Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- bundle validator: `python scripts/validate_deep_global_survey_bundle.py --survey-doc docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document
