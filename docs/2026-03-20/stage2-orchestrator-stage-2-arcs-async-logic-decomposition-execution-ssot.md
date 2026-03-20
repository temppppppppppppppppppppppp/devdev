# Stage2 Orchestrator stage_2_arcs_async_logic Decomposition Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage2-orchestrator-stage-2-arcs-async-logic-decomposition-execution-ssot.md`
Temp Mirror Path: removed after closure
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: pre-existing stage4/smoke/doc changes, project artifact churn, docs/mmmm intake; no active temp execution queue at start`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/long-function-decomposition-live-reaudit-3pass-audit.md`
- `docs/2026-03-20/long-function-decomposition-hotspot-survey-3pass-audit.md`
Evidence Artifacts:
- `modules/core/stage2_orchestrator.py`
- `tests/test_stage2_pipeline.py`
- `tests/e2e/test_l3_golden_route.py`
- `tests/e2e/test_l3_stage2_realproject.py`
- `tests/test_stage234_fixes.py`
Side-Effect Coverage: covered

## 1. Intent
- Decompose `stage_2_arcs_async_logic` into explicit Stage 2 pipeline phases without changing orchestration semantics.
- Reduce the current single-method pipeline knot after the finalizer substrate has been clarified.

## 2. Baseline Facts
- The method mixes bootstrap, volume/bible loading, state-tracker setup, target-limit selection, batch enrichment, per-arc processing, and recovery/reporting.
- A placeholder `_preflight_*` surface already exists, which gives a natural extraction direction.
- This item depends conceptually on the Stage 2 finalizer decomposition item.

## 3. Scope
Included:
- `modules/core/stage2_orchestrator.py`
- helper extraction inside the same module
- Stage 2 pipeline orchestration clarity only

Excluded:
- Stage 2 pacing semantics
- preflight policy rewrites
- smoke fixture behavior changes
- new concurrency models

## 4. Pass 1. Inventory Summary
- bootstrap and data readiness
- tracker/constraint initialization
- target limit calculation
- batch enrichment
- per-arc generation/finalize loop
- failure report writing and recovery

## 5. Pass 2. Semantic Classification
- Class A: startup/bootstrap and readiness checks
- Class B: batch enrichment and per-arc worker orchestration
- Class C: finalize/recovery/report glue

## 6. Side-Effect Map
- file writes / artifacts: failure reports and arc output artifacts downstream
- DB / schema / transaction boundaries: current project anchors and stage persistence
- JSONL / log / audit sinks: UI logs, runtime logging, downstream metrics
- console / UI / operator output: Stage 2 progress, warnings, and prompts
- rollback / recovery / retry: batch retry, finalize fallback, failure reports
- cache / global state: state tracker reuse, cumulative cache, selected genre/project ctx
- bootstrap fallback / config-env mutation: startup guards only; no env mutation intended

## 7. Realization Architecture
- keep `stage_2_arcs_async_logic` as the public entrypoint
- make phase helpers explicit rather than continuing to grow the single method
- reuse the existing `_preflight_*` placeholder surface where appropriate instead of inventing a second internal protocol

## 8. Execution Tranches
1. Extract startup/bootstrap and readiness-limit helpers.
2. Extract batch enrichment / worker scheduling helpers.
3. Extract per-arc finalize/recovery/report wiring and leave the top method as coordinator.

## 9. Acceptance Criteria
- public async contract remains unchanged
- Stage 2 batch progression semantics remain unchanged
- existing Stage 2 pipeline tests and golden-route tests continue to pass

## 10. Verification Plan
- `python -m pytest tests/test_stage2_pipeline.py -q`
- `python -m pytest tests/test_stage234_fixes.py -q`
- `python -m pytest tests/e2e/test_l3_golden_route.py -q`
- `python -m pytest tests/e2e/test_l3_stage2_realproject.py -q`

## 11. Guardrails
- do not merge this work with Stage 2 policy or smoke determinism changes
- do not rewrite state-tracker or constraint DB ownership inside this item
- do not start before the Stage 2 finalizer item has been revalidated

## 12. Temp Queue Notes
- temp status: closed
- cleanup condition: completed; temp mirror removed after realization and closure
- roadmap dependency: second item; depends on the Stage 2 finalizer item for clearer substrate boundaries

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Progress Note
- 2026-03-20 realization tranche 1 in progress:
  - extracted startup/bootstrap and readiness-limit logic into `_bootstrap_stage2_arc_pipeline`
  - reduced `stage_2_arcs_async_logic` top-of-method setup to startup-state acquisition plus batch loop handoff
- 2026-03-20 realization tranche 2 completed:
  - extracted batch enrichment, sanitize, and recovery flow into `_run_stage2_batch_enrichment`
  - reduced the main batch loop to helper dispatch plus stitching/per-arc handoff
- 2026-03-20 realization tranche 3 completed:
  - extracted failed-arc report/manual recovery flow into `_handle_stage2_arc_failure`
  - extracted finalizer outcome transition, session logging, previous-attempt derivation, and cache invalidation into `_handle_stage2_finalize_transition`
  - reduced the per-arc loop to finalizer dispatch plus failure-helper action branching
- Closure note:
  - startup/bootstrap, batch enrichment, finalizer transition, and failed-arc recovery/report wiring are all extracted
  - `stage_2_arcs_async_logic` remains the public coordinator but no longer owns the largest Stage 2 side-path blocks inline
