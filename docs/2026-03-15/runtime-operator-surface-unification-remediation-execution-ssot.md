# runtime-operator-surface-unification-remediation Execution SSOT

Date: 2026-03-15
Status: superseded-by-runtime-operator-surface-unification-refresh
Successor: `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md`
Canonical Path: `docs/2026-03-15/runtime-operator-surface-unification-remediation-execution-ssot.md`
Temp Mirror Path: `none`
Queue Disposition: `historical cleanroom predecessor only; excluded from active queue`
Authority Class: `historical predecessor; do not use as live execution authority`
Commit State:
- Baseline Commit: `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- Baseline Dirty Summary: `dirty: unrelated investment/style/docs/log artifacts already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs: `docs/2026-03-15/codebase-global-cleanroom-source-only-3pass-audit.md`; `docs/2026-03-15/codebase-global-cleanroom-source-only-deep-global-survey.md`
Evidence Artifacts: `docs/2026-03-15/codebase-global-cleanroom-source-only-source-inventory.txt`; `docs/2026-03-15/codebase-global-cleanroom-source-only-surface-anchor-inventory.txt`; `docs/2026-03-15/codebase-global-cleanroom-source-only-side-effects.txt`
Side-Effect Coverage: covered

## Historical Supersession Notice

- This cleanroom execution SSOT is retained as a historical predecessor only.
- Live execution authority moved to `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md`, which was later realized and closed under the post-remediation roadmap.
- Any `execution-ready`, temp-path, or roadmap semantics below are historical snapshot content, not current queue state.

## 1. Intent
- Centralize operator prompt authority across console mode and wrapper prompt surfaces.
- Reduce drift between raw `input(...)`, `_get_int_input(...)`, wrapper prompts, and hidden prompt telemetry after backend-front transport semantics are stabilized elsewhere.

## 2. Baseline Facts
- Source sweep found 91 raw `input(...)` calls, 5 `_get_int_input(...)` calls, and 2 `console.input(...)` calls.
- Prompt authority is still split across `main_a.py`, `UIService`, `StudioVisualizer`, and a small number of service-local confirmation helpers.
- Desktop renderer, preload, Electron main, `bridge_server`, `ProcessRunner`, and `PromptBroker` remain relevant context, but their transport-state and reconnect problems are now governed by the dedicated backend-front connectivity lane.
- This is `P1` because operator behavior and future regressions depend on one coherent prompt contract.

## 3. Scope
Included:
- `main_a.py`
- `modules/core/services/ui_service.py`
- `modules/core/studio_visualizer.py`
- `modules/core/services/project_service.py`
- `modules/core/stage4_post_processor.py`
- direct regression tests and canary helpers touching prompt paths and wrapper telemetry

Excluded:
- backend-front/control-plane transport repair:
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/src/preload.js`
  - `geuldobi-desktop/src/main.js`
  - `modules/api/process_runner.py`
  - `modules/api/prompt_broker.py`
  - `modules/api/bridge_server.py`
- persistence sink refactors except where prompt metadata contracts require a coordinated touch
- historical docs, logs, and DB artifacts
- asset-pack cleanup

## 4. Pass 1. Inventory Summary
- Console-mode prompts still live in `main_a.py` and project services.
- Wrapper prompts and hidden response telemetry live in `UIService` and `StudioVisualizer`.
- The remaining gap in this lane is that wrapper/console prompt semantics are still not governed by one shared authority.

## 5. Pass 2. Semantic Classification
- Class A: raw console prompts that should flow through one shared authority
- Class B: wrapper prompts/selection telemetry that must not drift from raw prompts
- Class C: service-local confirmation helpers that should reuse the same prompt policy instead of re-implementing it

## 6. Side-Effect Map
- file writes / artifacts:
  - source files, tests, and possibly prompt-contract docs only
- DB / schema / transaction boundaries:
  - indirect only via UI-event or audit metadata contracts
- JSONL / log / audit sinks:
  - prompt/selection event payloads may change
- console / UI / operator output:
  - direct primary effect
- rollback / recovery / retry:
  - non-interactive harnesses and bounded confirm loops must remain stable
- cache / global state:
  - wrapper prompt state and hidden telemetry state must stay coherent
- bootstrap fallback / config-env mutation:
  - not a primary surface in this lane

## 7. Realization Architecture
- Define one prompt-authority contract:
  - raw console path
  - wrapped UI prompt path
- service-local confirmation path
- Move prompt construction and response handling toward one shared surface instead of file-local ad hoc prompts.
- Consume the backend-front connectivity lane as a prerequisite rather than re-solving transport state here.

## 8. Execution Tranches
1. Inventory and classify every surviving interactive prompt site by owner and runtime path.
2. Replace direct/raw prompt sites with one shared prompt-authority surface where justified.
3. Align wrapper telemetry and regression tests with the same policy.

## 9. Acceptance Criteria
- Prompt authority is centralized enough that console, wrapper, and service-local prompt paths no longer diverge by construction.
- Hidden prompt telemetry reflects the same prompt contract instead of reconstructing it separately.
- Direct raw `input(...)` use is reduced to bounded exceptions or eliminated from the main runtime path.

## 10. Verification Plan
- targeted pytest for UI service, studio visualizer, frontier lag, and canary/helpers touching prompt wrappers or console prompts
- `python -m py_compile` for touched Python files

## 11. Guardrails
- Do not break existing non-interactive harnesses while centralizing prompt authority.
- Do not pull websocket or Electron readiness repair back into this lane; that belongs to the backend-front connectivity execution doc.

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition: remove temp mirror only after realization is validated and closed
- roadmap dependency: third item in `docs/2026-03-15/codebase-global-cleanroom-source-only-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document
