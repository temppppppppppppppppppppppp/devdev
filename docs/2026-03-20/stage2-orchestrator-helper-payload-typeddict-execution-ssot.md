# Stage2 Orchestrator Helper Payload TypedDict Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage2-orchestrator-helper-payload-typeddict-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage2-orchestrator-helper-payload-typeddict-execution-ssot.md`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: ongoing stage/smoke/doc/project churn, low-trust intake bundle, prior closed decomposition tranche`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/typed-dict-helper-payload-live-reaudit-3pass-audit.md`
- `docs/2026-03-20/typed-dict-helper-payload-hotspot-survey-3pass-audit.md`
Evidence Artifacts:
- `modules/core/stage2_orchestrator.py`
- `tests/test_stage2_pipeline.py`
- `tests/test_stage234_fixes.py`
- `tests/e2e/test_l3_stage2_realproject.py`
- `tests/e2e/test_l3_golden_route.py`
Side-Effect Coverage: covered

## 1. Intent
- Replace plain helper-result dicts in Stage 2 orchestrator substrate with local `TypedDict` contracts.
- Make startup/batch/finalizer-transition/failure-recovery payloads explicit.

## 2. Baseline Facts
- recent decomposition created four clear helper boundaries
- the top orchestrator still branches on plain dict keys
- this is a good fit for local payload contracts because branch keys are stable and test-backed

## 3. Scope
Included:
- `modules/core/stage2_orchestrator.py`
- same-file `TypedDict` definitions for helper return payloads
- immediate caller annotations

Excluded:
- Stage 2 policy changes
- smoke determinism policy
- preflight contract redesign
- static type checker adoption

## 4. Pass 1. Inventory Summary
- candidate helpers:
  - `_bootstrap_stage2_arc_pipeline`
  - `_run_stage2_batch_enrichment`
  - `_handle_stage2_finalize_transition`
  - `_handle_stage2_arc_failure`

## 5. Pass 2. Semantic Classification
- Class A:
  - startup/bootstrap readiness payload
- Class B:
  - batch enrichment payload
- Class C:
  - finalize transition and arc-failure action payloads

## 6. Side-Effect Map
- file writes / artifacts:
  - unchanged downstream reports/artifacts
- DB / schema / transaction boundaries:
  - unchanged
- JSONL / log / audit sinks:
  - unchanged
- console / UI / operator output:
  - unchanged
- rollback / recovery / retry:
  - unchanged
- cache / global state:
  - unchanged
- bootstrap fallback / config-env mutation:
  - unchanged

## 7. Realization Architecture
- keep `TypedDict` definitions local to `stage2_orchestrator.py`
- focus on the four decomposed helper boundaries only
- preserve async entrypoint and branch semantics

## 8. Execution Tranches
1. Add local `TypedDict` definitions for startup, batch, transition, and failure payloads.
2. Annotate helper functions and immediate call sites.
3. Re-run Stage 2 pipeline and e2e shards, then close.

## 9. Acceptance Criteria
- helper payload contracts are explicit
- `stage_2_arcs_async_logic` keeps current semantics
- Stage 2 pipeline/e2e regressions continue to pass

## 10. Verification Plan
- `python -m pytest tests/test_stage2_pipeline.py -q`
- `python -m pytest tests/test_stage234_fixes.py -q`
- `python -m pytest tests/e2e/test_l3_stage2_realproject.py -q`
- `python -m pytest tests/e2e/test_l3_golden_route.py -q`

## 11. Guardrails
- do not widen into raw arc/blueprint/audit domain typing
- do not move these payload contracts into a shared typing module in tranche 1
- do not mix this item with policy or determinism changes

## 12. Temp Queue Notes
- temp status: closed
- cleanup condition:
  - remove mirror after realization and closure
- roadmap dependency:
  - second item; follows the Stage 2 finalizer payload pattern

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Progress Note
- 2026-03-20 realization completed:
  - introduced local `TypedDict` contracts for startup, batch, finalize-transition, and arc-failure helper payloads
  - annotated helper return signatures and direct caller payload variables
- Closure note:
  - acceptance criteria satisfied
  - Stage 2 pipeline and e2e verification shards passed after typing refinement
