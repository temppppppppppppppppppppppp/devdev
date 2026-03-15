# runtime-operator-surface-unification-refresh-remediation Execution SSOT

Date: 2026-03-15
Status: closed
Canonical Path: `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: harness/test edits plus unrelated investment/style/pdf/log artifacts and untracked projects/000/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `main_a.py raw prompt bypasses now route through UIService; ProjectService destructive prompts use injected prompt callbacks; UIService fallback emits hidden prompt_response telemetry; prompt authority chain doc saved`
Source Survey Docs: `docs/2026-03-15/codebase-global-log-evidence-merged-3pass-audit.md`; `docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md`; `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-3pass-audit.md`
Evidence Artifacts: `docs/2026-03-15/codebase-global-log-evidence-merged-surface-anchor-inventory.txt`; `docs/2026-03-15/codebase-global-log-evidence-merged-runtime-log-db-evidence.txt`; `docs/2026-03-15/codebase-global-log-evidence-merged-side-effects.txt`; `docs/2026-03-15/runtime-operator-prompt-authority-chain.md`
Side-Effect Coverage: covered

## 1. Intent
- Reduce prompt-authority fragmentation across console mode, wrapper prompts, and service-local confirmation paths.
- Preserve the current user-facing fixes outside the dedicated menu `7` Arc-count contract while simplifying the remaining prompt surface for future work.

## 2. Baseline Facts
- The dedicated operator contract for menu `7` Arc-count semantics now belongs to `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-execution-ssot.md`.
- Latest secured CLI runtime evidence retained two important behaviors outside that dedicated item:
  - durable UI sinks did not show prompt duplication regression
  - broad prompt authority still remains fragmented across raw input sites, wrappers, and service-local helpers
- Even so, source inventory still shows `92` raw `input(...)` sites, `5` `_get_int_input(...)` sites, and `262` prompt anchors overall.
- This makes the lane structural rather than emergency runtime repair.

## 3. Scope
Included:
- `main_a.py`
- `modules/core/services/ui_service.py`
- `modules/core/studio_visualizer.py`
- `modules/core/services/project_service.py`
- service-local confirmation helpers and targeted prompt tests

Excluded:
- menu `7` desired Arc input contract
- desktop transport and reconnect repair
- persistence shutdown/finalization repair
- broad source-text cleanup outside prompt-authority touches

## 4. Pass 1. Inventory Summary
- The menu `7` Arc-count policy is no longer owned here and is handled by a dedicated compact item.
- The remaining defect is architectural drift: prompt construction, response handling, and hidden telemetry still live in too many authorities.

## 5. Pass 2. Semantic Classification
- Class A: raw console prompts that should move toward one authority
- Class B: wrapper prompt/selection telemetry that must not reconstruct prompt semantics separately
- Class C: service-local confirmation helpers that should reuse the shared policy

## 6. Side-Effect Map
- file writes / artifacts:
  - source files, tests, and prompt-contract docs only
- DB / schema / transaction boundaries:
  - indirect only through UI-event metadata
- JSONL / log / audit sinks:
  - prompt/selection event payloads may change
- console / UI / operator output:
  - direct primary effect
- rollback / recovery / retry:
  - bounded prompt loops and non-interactive harnesses must stay stable
- cache / global state:
  - wrapper prompt state and hidden telemetry state
- bootstrap fallback / config-env mutation:
  - not primary

## 7. Realization Architecture
- Define one shared prompt-authority surface for console and wrapper paths where practical.
- Keep non-interactive harness behavior explicit and exempt only by bounded contract.
- Treat `menu 7` Arc-count semantics as an external prerequisite owned by the dedicated compact SSOT rather than re-solving it here.
- Consume the earlier source/output hygiene lane and the backend-front lane as prerequisites rather than re-solving them here.

## 8. Execution Tranches
1. Re-inventory surviving interactive prompt sites by owner and runtime path.
2. Consolidate high-value prompt sites into one shared authority surface.
3. Align hidden telemetry and regression tests with the same prompt contract.

## 9. Acceptance Criteria
- Prompt authority is materially more centralized than today.
- Hidden prompt telemetry reflects the same contract instead of ad hoc reconstruction.
- Existing non-interactive harnesses stay stable.
- Current live CLI fixes outside the dedicated menu `7` Arc-count item are not regressed while centralizing prompt ownership.

## 10. Verification Plan
- targeted pytest for UI service, studio visualizer, FrontierLag helpers, and prompt-adjacent canaries
- `python -m py_compile` for touched Python files
- bounded manual prompt-path smoke if needed after implementation

## 11. Guardrails
- Do not take ownership of menu `7` Arc-count interaction policy; that belongs to `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-execution-ssot.md`.
- Do not fold desktop reconnect logic into this lane.
- Do not widen this lane into persistence sink cleanup.

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition: remove temp mirror only after realization is validated and closed
- roadmap dependency: fifth item in `docs/2026-03-15/codebase-global-log-evidence-merged-execution-roadmap.md`

## 13. Validation And Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- bundle validator: `python scripts/validate_deep_global_survey_bundle.py --survey-doc docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Evidence
- Implemented:
  - `main_a.py`
  - `modules/core/services/ui_service.py`
  - `modules/core/services/project_service.py`
  - `docs/2026-03-15/runtime-operator-prompt-authority-chain.md`
  - targeted prompt-path regression tests
- Realized outcomes:
  - `main_a.py` raw `input(...)` count on the live runtime path is now `0`
  - destructive prompt flows in `ProjectService` now use injected shared callbacks in the live app path
  - `UIService` now owns shared choice / confirm / pause semantics in addition to int input
  - fallback prompt telemetry now emits hidden `prompt_response` events instead of leaving fallback contexts untracked
- Verification:
  - `python -m py_compile main_a.py modules/core/services/ui_service.py modules/core/services/project_service.py tests/test_ui_service.py tests/test_project_service.py tests/test_one_stop_frontier_lag_auto_continue.py tests/test_main_a_boot_binding.py`
  - `python -m pytest tests/test_ui_service.py tests/test_studio_visualizer.py tests/test_project_service.py tests/test_one_stop_frontier_lag_auto_continue.py tests/test_main_a_boot_binding.py`
