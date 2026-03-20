# Stage2 Finalizer Helper Payload TypedDict Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage2-finalizer-helper-payload-typeddict-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage2-finalizer-helper-payload-typeddict-execution-ssot.md`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: ongoing stage/smoke/doc/project churn, low-trust intake bundle, prior closed decomposition tranche`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/typed-dict-helper-payload-live-reaudit-3pass-audit.md`
- `docs/2026-03-20/typed-dict-helper-payload-hotspot-survey-3pass-audit.md`
Evidence Artifacts:
- `modules/core/stage2_finalizer.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_pass_with_fix.py`
- `tests/test_arc_retry.py`
Side-Effect Coverage: covered

## 1. Intent
- Introduce local `TypedDict` contracts for Stage 2 finalizer helper return payloads.
- Improve branch clarity without changing Stage 2 semantics or persistence behavior.

## 2. Baseline Facts
- `run_finalize` is already decomposed into explicit helpers.
- Those helpers still return plain dicts with stable branch/result keys.
- This item is a typing refinement on a recently stabilized substrate, not a fresh structural refactor.

## 3. Scope
Included:
- `modules/core/stage2_finalizer.py`
- same-file `TypedDict` definitions for helper return payloads
- small annotation alignment in direct helper callers

Excluded:
- policy rewrites
- new static type checker integration
- raw arc/audit domain model replacement
- cross-file typing abstraction

## 4. Pass 1. Inventory Summary
- candidate helpers:
  - `_prepare_stage2_pass_arc_for_persistence`
  - `_finalize_stage2_pass_persistence_and_tail`
  - `_run_stage2_pass_with_fix_loop`

## 5. Pass 2. Semantic Classification
- Class A:
  - pass-preparation payload
- Class B:
  - pass-tail/finalization payload
- Class C:
  - `PASS_WITH_FIX` loop result payload

## 6. Side-Effect Map
- file writes / artifacts:
  - none from typing itself
- DB / schema / transaction boundaries:
  - existing Stage 2 persistence paths only
- JSONL / log / audit sinks:
  - existing Stage 2 sinks only
- console / UI / operator output:
  - unchanged
- rollback / recovery / retry:
  - unchanged
- cache / global state:
  - unchanged
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- keep `TypedDict` local to `stage2_finalizer.py`
- type only stable helper result contracts
- prefer `NotRequired` for optional branch keys if needed

## 8. Execution Tranches
1. Introduce local `TypedDict` definitions for the three helper result payloads.
2. Annotate helper returns and immediate caller sites.
3. Run focused regression and close without expanding scope.

## 9. Acceptance Criteria
- helper payload keys are named by `TypedDict` instead of bare `dict`
- no runtime behavior changes
- Stage 2 finalizer regressions continue to pass

## 10. Verification Plan
- `python -m pytest tests/test_stage2_finalizer.py -q`
- `python -m pytest tests/test_pass_with_fix.py -k "Stage2PassWithFix or finalizer" -q`
- `python -m pytest tests/test_arc_retry.py -q`

## 11. Guardrails
- do not type every `dict` in the file
- do not widen into raw `audit`/`refined_arc` domain typing here
- do not add mypy/pyright gating in this item

## 12. Temp Queue Notes
- temp status: closed
- cleanup condition:
  - remove mirror after realization and closure
- roadmap dependency:
  - first item; establishes the Stage 2 helper-payload pattern

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Progress Note
- 2026-03-20 realization completed:
  - introduced local `TypedDict` contracts for pass-preparation, pass-tail, and `PASS_WITH_FIX` loop payloads
  - annotated helper return signatures and direct caller payload variables
  - aligned stale retry test wording with current `transition["action"]` semantics
- Closure note:
  - acceptance criteria satisfied
  - focused Stage 2 finalizer shards passed after typing refinement
