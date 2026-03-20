# Stage2 Finalizer run_finalize Decomposition Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage2-finalizer-run-finalize-decomposition-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage2-finalizer-run-finalize-decomposition-execution-ssot.md`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: pre-existing stage4/smoke/doc changes, project artifact churn, docs/mmmm intake; no active temp execution queue at start`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/long-function-decomposition-live-reaudit-3pass-audit.md`
- `docs/2026-03-20/long-function-decomposition-hotspot-survey-3pass-audit.md`
Evidence Artifacts:
- `modules/core/stage2_finalizer.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_pass_with_fix.py`
- `tests/test_arc_retry.py`
Side-Effect Coverage: covered

## 1. Intent
- Decompose `Stage2Finalizer.run_finalize` without changing Stage 2 verdict semantics.
- Turn the current 1,134-line method into a thin orchestration wrapper over explicit subphases.

## 2. Baseline Facts
- The function is one of the largest live orchestration surfaces in production code.
- The file already contains local helper scaffolding, metrics sinks, patch-guard helpers, and advisory builders.
- Existing direct tests are strong enough to support tranche refactoring without inventing a new verification surface.

## 3. Scope
Included:
- `modules/core/stage2_finalizer.py`
- direct helper extraction inside the same module
- targeted Stage 2 regression alignment

Excluded:
- Director policy rewrites
- Stage 2 scoring semantics
- DB schema changes
- prompt wording changes

## 4. Pass 1. Inventory Summary
- primary public surface: `run_finalize`
- local subdomains already visible in code:
  - director context and advisory assembly
  - director call and verdict normalization
  - pass persistence / metrics / side-effect handling
  - reject / retry / rollback handling

## 5. Pass 2. Semantic Classification
- Class A: pure or mostly-pure context assembly helpers
- Class B: side-effectful pass-path persistence and metrics
- Class C: reject-path rollback and retry envelope

## 6. Side-Effect Map
- file writes / artifacts: none directly, but downstream persistence hooks are triggered
- DB / schema / transaction boundaries: Stage 2 arc persistence and project DB writes
- JSONL / log / audit sinks: runtime audit, pass-rate metrics, quality/decision surfaces
- console / UI / operator output: Stage 2 log lines and advisory notices
- rollback / recovery / retry: constraint DB snapshot and retry handoff
- cache / global state: current project / ctx mutation, constraint snapshot, semantic carryover payloads
- bootstrap fallback / config-env mutation: not applicable

## 7. Realization Architecture
- keep `run_finalize` as the only public orchestration entrypoint
- extract helper boundaries in the same file first
- preserve current kwargs contract and return dict contract
- avoid cross-file moves in tranche 1

## 8. Execution Tranches
1. Extract pre-director context/advisory assembly helpers.
2. Extract pass-path persistence/metrics helpers.
3. Extract reject/retry handoff helpers and leave `run_finalize` as wrapper orchestration.

## 9. Acceptance Criteria
- public signature and return contract of `run_finalize` remain unchanged
- Stage 2 PASS / PASS_WITH_FIX / REJECT routing semantics remain unchanged
- all current Stage 2 regression tests continue to pass

## 10. Verification Plan
- `python -m pytest tests/test_stage2_finalizer.py -q`
- `python -m pytest tests/test_pass_with_fix.py -k "Stage2PassWithFix or finalizer" -q`
- `python -m pytest tests/test_arc_retry.py -q`

## 11. Guardrails
- do not mix decomposition with Stage 2 policy changes
- do not alter Director sovereignty or patch-scope semantics here
- do not change DB or audit sink payloads unless a separate SSOT is opened

## 12. Temp Queue Notes
- temp status: closed
- cleanup condition: remove temp mirror after realization and closure
- roadmap dependency: first item; Stage 2 orchestrator item should not start before this item is revalidated

## 14. Progress Note
- 2026-03-20 realization tranche 1 completed:
  - extracted Stage 2 Director story-context assembly into a dedicated helper
  - extracted Director audit/timing/display path into a dedicated helper
  - extracted session-decision logging into a dedicated helper
  - extracted `PASS_WITH_FIX` retry/patch loop into a dedicated helper
- 2026-03-20 realization tranche 2 completed:
  - extracted the Director `REJECT` / retry envelope into a dedicated helper
  - extracted the pass-path QualityGate downgrade branch into a dedicated helper
- 2026-03-20 realization tranche 3 completed:
  - extracted pass-path persistence preparation into a dedicated helper
  - extracted pass-path persistence/finalization tail into a dedicated helper
  - reduced `run_finalize` to a thin orchestration wrapper over explicit phase helpers
- Closure note:
  - acceptance criteria satisfied
  - direct Stage 2 regression shards passed after helper extraction

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document
