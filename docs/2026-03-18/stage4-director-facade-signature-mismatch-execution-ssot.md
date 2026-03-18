# Stage 4 director facade signature mismatch Execution SSOT

Date: 2026-03-18
Status: closed
Canonical Path: `docs/2026-03-18/stage4-director-facade-signature-mismatch-execution-ssot.md`
Temp Mirror Path: `none` (removed after closure)
Commit State:
- Baseline Commit: `d4e96804898491ae67085a327bf35b080ced4364`
- Baseline Dirty Summary: `dirty: 12 tracked, 9 untracked; hotspots: docs/2026-03-18/, modules/core/response_schemas.py, modules/domain/agents/base_agent.py, projects/0_260318/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same HEAD; realized in working tree with changes to modules/domain/agents/director.py, main_a.py, tests/test_director_modules.py, tests/test_one_stop_frontier_lag_auto_continue.py`
Source Survey Docs:
- `docs/2026-03-18/stage4-director-facade-signature-mismatch-3pass-audit.md`
- `docs/2026-03-18/stage4-director-facade-signature-mismatch-9pass-audit.md`
Evidence Artifacts:
- `projects/0_260318/logs/session/ui_events.jsonl`
- `projects/0_260318/logs/session_20260318_125200.log`
- `projects/0_260318/logs/runtime_audit_summary.json`
- `projects/0_260318/project_data.db`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/director.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_orchestrator.py`
- `main_a.py`
- `tests/test_director_modules.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_one_stop_frontier_lag_auto_continue.py`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `97%`

## 1. Intent

- Restore Stage 4 manuscript production by fixing the `Director` facade signature/forwarding drift that currently throws `unexpected keyword argument 'decision_core'`.
- Prevent FrontierLag from reporting Stage 4 success when manuscript target progress is still unmet and the manuscript frontier did not advance.

Why now:

- project `0_260318` has Stage 2 and Stage 3 output through episode `11`, but Stage 4 remains blocked at episode `0`
- the failure is deterministic and operator-visible
- current behavior wastes runtime and cost by continuing arc design after fatal Stage 4 failure

## 2. Baseline Facts

- `modules/core/stage4_interview_round.py` now calls `self.ctx.agents["director"].select_and_judge_ensemble(...)` with:
  - `decision_core`
  - `candidate_evidence`
  - `reference_appendix`
- `modules/domain/agents/director_ensemble.py` accepts and consumes all three kwargs.
- `modules/domain/agents/director.py` does not accept or forward those kwargs.
- Python therefore raises the `TypeError` at the facade boundary before ensemble delegation.
- `projects/0_260318/project_data.db` shows:
  - `manuscripts = 0`
  - `episode_meta = 0`
  - `stage_attempts(stage=4) = 0`
  - `director_selections(stage=4) = 0`
- `projects/0_260318/logs/session/ui_events.jsonl` shows repeated `Stage 4 V2 오류` followed by `원고 완료 (0화 생산)` and automatic continuation into later arcs.

Synthesis decision:

- The OPUS 9-pass audit adds precise facade/implementation drift confirmation, unaffected re-audit path context, and the direct test-coverage gap.
- The local 3-pass audit adds persistence truth and FrontierLag blast radius.
- Immediate execution scope should therefore include both:
  - the facade fix
  - a minimal FrontierLag unmet-target zero-progress guard

## 3. Scope

Included:

- `modules/domain/agents/director.py`
- `main_a.py`
- `tests/test_director_modules.py`
- `tests/test_one_stop_frontier_lag_auto_continue.py`

Excluded:

- `modules/domain/agents/director_ensemble.py` behavioral changes beyond current contract
- `modules/core/stage4_interview_round.py` prompt-pack design changes
- broad Stage 4 exception propagation redesign in `modules/core/stage4_orchestrator.py`
- DB schema changes
- queue/roadmap work unrelated to this P0 fix

## 4. Pass 1. Inventory Summary

Hotspots:

1. `modules/domain/agents/director.py`
   - stale facade signature
   - stale delegation call
2. `main_a.py`
   - FrontierLag logs Stage 4 success from manuscript frontier delta only
   - `arcs_advanced += 1` executes even after zero-progress fatal Stage 4 runs
3. `tests/test_director_modules.py`
   - facade delegation test does not cover new kwargs
4. `tests/test_one_stop_frontier_lag_auto_continue.py`
   - no regression guard for unmet Stage 4 target plus zero manuscript progress

Runtime vs non-runtime:

- runtime patch surface is limited to `director.py` and `main_a.py`
- test changes are localized and do not require fixture redesign outside the touched files

## 5. Pass 2. Semantic Classification

- Class A. Root-cause contract repair
  - align `Director.select_and_judge_ensemble(...)` facade with the already-live ensemble contract
- Class B. Operator-truth guard
  - stop FrontierLag from claiming success when Stage 4 target remains unmet and manuscript truth did not move
- Class C. Regression coverage
  - add a facade-bound kwarg forwarding test
  - add a FrontierLag zero-progress abort test

## 6. Side-Effect Map

- file writes / artifacts:
  - no new artifact format
  - FrontierLag logging semantics will change on zero-progress fatal Stage 4 runs
- DB / schema / transaction boundaries:
  - no schema change
  - successful Stage 4 runs should resume normal manuscript persistence once the facade error is removed
- JSONL / log / audit sinks:
  - Stage 4 fatal zero-progress should no longer be followed by false-success UI lines in FrontierLag
- console / UI / operator output:
  - replace misleading Stage 4 success messaging with a blocked-stage message when target progress is unmet
- rollback / recovery / retry:
  - no rollback path change
  - FrontierLag will stop instead of auto-continuing on unmet-target zero-progress Stage 4 failure
- cache / global state:
  - no cache contract change
  - arc frontier advancement will be prevented in the zero-progress blocked case
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

- Keep the fix bounded.
- Do not redesign the Stage 4 orchestrator return contract in this turn.
- Use existing manuscript frontier truth as the minimal authoritative signal in FrontierLag:
  - if `ms_max_before < stage4_target`
  - and `ms_max_after <= ms_max_before`
  - then Stage 4 did not achieve required progress for that tranche
  - treat that as blocked, not success

Contracts:

- facade contract:
  - `director.py` must accept and forward `decision_core`, `candidate_evidence`, `reference_appendix`
- frontier guard contract:
  - zero produced manuscripts is only acceptable when the Stage 4 target was already aligned before the call
  - zero produced manuscripts is not acceptable when backlog existed before the call

## 8. Execution Tranches

1. Facade repair
   - update `modules/domain/agents/director.py` signature
   - forward the three new kwargs to `_ensemble.select_and_judge_ensemble(...)`
2. FrontierLag guard
   - add an unmet-target zero-progress check in `main_a.py`
   - stop the tranche with a Stage 4 blocked stop reason instead of logging success
3. Regression tests
   - extend `tests/test_director_modules.py`
   - add/adjust `tests/test_one_stop_frontier_lag_auto_continue.py`

## 9. Acceptance Criteria

- `Director.select_and_judge_ensemble(...)` accepts `decision_core`, `candidate_evidence`, and `reference_appendix`.
- The facade forwards those kwargs to `DirectorEnsembleSelector.select_and_judge_ensemble(...)`.
- A Stage 4 path using the real `Director` facade no longer raises the reported `TypeError`.
- FrontierLag does not print `원고 완료 (0화 생산)` when `stage4_target` was unmet and manuscript truth did not advance.
- FrontierLag stops the tranche with a blocked stop reason in that case.
- Targeted regression tests cover both the facade forwarding and the FrontierLag guard.

## 10. Verification Plan

- `pytest tests/test_director_modules.py -q`
- `pytest tests/test_one_stop_frontier_lag_auto_continue.py -q`
- `pytest tests/test_main_a_stage_entry_contracts.py -q`
- optional focused runtime guard:
  - inspect `inspect.signature(Director.select_and_judge_ensemble)` after patch

## 11. Guardrails

- Do not modify `director_ensemble.py` unless live code proves the ensemble contract itself is wrong.
- Do not widen this into a general Stage 4 orchestrator redesign in the same patch.
- Do not treat aligned no-op Stage 4 runs as failures.
- Do not touch unrelated dirty workspace files.

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition: remove the temp mirror after realization is closed or superseded
- roadmap dependency: none; single execution item only

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1:

- execution-doc type, scope, canonical/temp policy, and bounded implementation surface checked

Pass 2:

- OPUS 9-pass audit and local 3-pass audit compared against live code, logs, DB, and tests
- synthesis conflict resolved by treating facade drift as primary root cause and FrontierLag false success as bounded adjacent hardening scope

Pass 3:

- tranches, acceptance criteria, verification plan, and guardrails are explicit
- implementation scope remains narrow enough for a same-turn realization

Confidence gate:

- `97%`
- residual uncertainty is limited to future broader Stage 4 fatal paths outside the bounded FrontierLag guard and does not block this execution item

## 15. Closure Summary

- Realization status: closed
- Acceptance criteria satisfied:
  - facade now accepts and forwards the three Director pack kwargs
  - FrontierLag blocks zero-progress Stage 4 backlog runs instead of logging false success
  - targeted regression tests passed
- Closure note:
  - `docs/2026-03-18/stage4-director-facade-signature-mismatch-execution-closure.md`
