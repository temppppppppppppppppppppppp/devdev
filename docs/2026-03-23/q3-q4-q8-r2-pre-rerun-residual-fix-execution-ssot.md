# Q3-Q4-Q8 R2 Pre-Rerun Residual Fix Execution SSOT

Date: 2026-03-23
Status: closed
Canonical Path: `docs/2026-03-23/q3-q4-q8-r2-pre-rerun-residual-fix-execution-ssot.md`
Temp Mirror Path: removed after closure
Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty: 2026-03-23 source/test/doc edits plus fresh-run artifacts under projects/0_0323; no active temp execution mirror before this SSOT`
- Resume Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Resume Drift Summary: `derived from the current live merge-audit state; revalidated against live source before save`
Source Survey Docs:
- `docs/2026-03-23/q1-q8-r2-merge-audit.md`
- `docs/2026-03-23/opus/r2-q3-verdict-accuracy.md`
- `docs/2026-03-23/opus/r2-q4-feedback-fidelity.md`
- `docs/2026-03-23/opus/r2-q8-logging-retention.md`
Evidence Artifacts:
- `projects/0_0323/project_data.db`
- `projects/0_0323/logs/runtime_audit.jsonl`
- `projects/0_0323/logs/episode_production.jsonl`
- `docs/2026-03-23/console.txt`
Side-Effect Coverage: covered

## 1. Intent

- Realize the small residual fix cluster identified by the R2 merge audit.
- Improve rerun correctness and post-run forensic quality without reopening the closed broad DB/console waves.
- Keep the patch bounded to:
  - Q3 downstream verdict semantics
  - Q8 Stage 2/3 DB rationale parity
  - Q4/Q8 residual operator, session-log, and JSONL truncation cleanup

Why now:
- The R2 bundle is complete.
- The remaining live issues are small, current, and higher ROI than another survey round.
- A corrected rerun is more valuable after these residuals land.
- Current audit status:
  - Q3 downstream verdict normalization is realized
  - Q4/Q8 residual truncation cleanup is realized
  - Q8 Stage 2/3 DB parity is realized; `open_review` now forwards where available and `runtime_advisory` / `retry_directives` now forward as explicit empty strings where the concept does not exist on Stage 2/3

## 2. Baseline Facts

- The current merge authority is `docs/2026-03-23/q1-q8-r2-merge-audit.md`.
- Large Stage 4 DB max-retention and console max-display waves are already closed.
- Current live residuals are:
  - one Q3 verdict-contract bug
  - two Q8 Stage 2/3 DB parity gaps
  - one bounded Q4/Q8 observability cluster

Residual set:
1. Q3 V60.97 `CONDITIONAL_PASS` survives locally but still drops into reject handling downstream.
2. Stage 3 `save_stage_attempt()` omits rationale/detail fields that Stage 4 already persists.
3. Stage 2 `save_stage_attempt()` omits rationale/detail fields and still slices `reject_reason[:500]`.
4. Secondary Stage 3/4 operator, session-log, and JSONL paths still keep compact caps.

## 3. Scope

Included:
- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage2_finalizer.py`
- targeted tests for the above surfaces

Excluded:
- closed broad DB logging wave
- closed broad console max-display wave
- Q1 generation-quality cleanup beyond the residual cluster
- Q5 long-run consistency architecture
- Q6 structural retrieval-quality cleanup
- Q7 context-reception long-run budget work
- schema migrations unless a hidden blocker proves they are strictly required

## 4. Pass 1. Inventory Summary

Inventory totals:
- correctness residuals: 1
- DB parity residuals: 2
- observability residual clusters: 1

Main hotspots:
- `director_ensemble.py` V60.97 branch verdict normalization
- `stage3_orchestrator.py` PASS/REJECT Stage 3 persistence parity
- `stage2_finalizer.py` PASS/REJECT Stage 2 persistence parity and caller-side truncation
- `stage4_reject_runtime.py`, `stage4_interview_round.py`, `stage3_orchestrator.py` residual compact logging

Runtime vs script/test separation:
- runtime code changes only in the five production files above
- no script changes expected
- tests are targeted shards only

## 5. Pass 2. Semantic Classification

- Class A: correctness contract
  - Q3 downstream positive-verdict recognition for the V60.97 keep path

- Class B: DB truth parity
  - Stage 2/3 `save_stage_attempt()` should match the richer rationale/detail contract already used by Stage 4

- Class C: operator and settlement observability
  - residual `[:100]`, `[:150]`, `[:200]`, `[:300]`, `[:500]` caps on non-authoritative but still useful surfaces

## 6. Side-Effect Map

- file writes / artifacts:
  - no new artifact families expected
  - existing `episode_production.jsonl` and runtime/session logs may change content shape by becoming less truncated

- DB / schema / transaction boundaries:
  - no schema migration expected
  - Stage 2/3 `save_stage_attempt()` payloads should become richer on existing columns
  - DB write authority remains `DBManager.save_stage_attempt()`

- JSONL / log / audit sinks:
  - `stage4_interview_round.py` JSONL settlement fields may become less truncated
  - `stage3_orchestrator.py` session logger fields may become less truncated
  - `stage4_reject_runtime.py` operator-facing and side sinks may become less truncated

- console / UI / operator output:
  - no new sink family
  - existing lines may become longer and more informative

- rollback / recovery / retry:
  - retry policy, verdict routing policy, and rollback behavior must not change
  - only the V60.97 keep-path downstream semantic mismatch may change from false reject to true positive handling

- cache / global state:
  - not applicable beyond normal runtime state already in place

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

- Keep this as a bounded same-file/same-surface patch wave.
- Do not reopen broad refactors.
- Prefer local contract normalization over new abstractions.

Preferred correctness seam:
- For the V60.97 threshold-pass branch, normalize to a downstream-positive verdict contract rather than leaving a local-only `CONDITIONAL_PASS` that the Stage 4 handler still treats as reject.

Preferred DB parity seam:
- Reuse existing `save_stage_attempt()` columns and forward already-available rationale/detail values.
- Do not introduce new DB tables or columns in this wave.

Preferred observability seam:
- Remove or relax compact caps only on the residual lines already identified.
- Do not flood logs by adding brand-new verbose channels.

## 8. Execution Tranches

1. Q3 verdict-contract tranche
   - target: `modules/domain/agents/director_ensemble.py`
   - goal:
     - eliminate the false downstream reject for the V60.97 threshold-pass path
   - preferred implementation:
     - normalize the keep-path to a downstream-positive verdict contract with the smallest blast radius
   - non-goals:
     - no redesign of adaptive policy
     - no threshold retuning

2. Q8 Stage 3 DB parity tranche
   - target: `modules/core/stage3_orchestrator.py`
   - goal:
     - forward `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, and `retry_directives` into `save_stage_attempt()`
   - non-goals:
     - do not create Stage 3 adjunct raw tables in this tranche

3. Q8 Stage 2 DB parity tranche
   - target: `modules/core/stage2_finalizer.py`
   - goal:
     - forward the same richer rationale/detail fields into `save_stage_attempt()`
     - remove caller-side `reject_reason[:500]`
   - non-goals:
     - no redesign of Stage 2 audit format

4. Q4/Q8 residual observability tranche
   - targets:
     - `modules/core/stage4_reject_runtime.py`
     - `modules/core/stage4_interview_round.py`
     - `modules/core/stage3_orchestrator.py`
   - goal:
     - remove residual compact caps from operator, session-log, and JSONL settlement paths that were left after the larger waves
   - non-goals:
     - do not reopen the already closed broad console wave
     - do not touch unrelated Director frame/provenance paths already settled

5. Regression tranche
   - add or update targeted tests for:
     - V60.97 downstream keep-path
     - Stage 2/3 `save_stage_attempt()` rationale parity
     - residual logging/JSONL truncation removal

## 9. Acceptance Criteria

- Q3:
  - V60.97 threshold-pass no longer falls into reject handling solely because of a local/downstream verdict mismatch

- Q8 Stage 3:
  - Stage 3 `save_stage_attempt()` rows can persist rationale/detail fields using the existing schema

- Q8 Stage 2:
  - Stage 2 `save_stage_attempt()` rows can persist rationale/detail fields using the existing schema
  - caller-side `reject_reason[:500]` is removed

- Q4/Q8 observability:
  - identified residual truncation lines are removed or intentionally bounded with a documented reason

- no schema changes are introduced unless a hidden blocker proves them necessary
- no change is made to retry policy, threshold policy, or broad queue/governance docs

## 10. Verification Plan

- `python -m py_compile modules/domain/agents/director_ensemble.py modules/core/stage4_interview_round.py modules/core/stage4_reject_runtime.py modules/core/stage3_orchestrator.py modules/core/stage2_finalizer.py`
- low-memory pytest shards:
  - `python -m pytest tests/test_director_modules.py -q`
  - `python -m pytest tests/test_stage3_orchestrator.py -q`
  - `python -m pytest tests/test_stage2_finalizer.py -q`
  - `python -m pytest tests/test_stage4_interview_round.py -q`
- document/code hygiene:
  - `python scripts/check_utf8_hygiene.py docs/2026-03-23/q3-q4-q8-r2-pre-rerun-residual-fix-execution-ssot.md docs/temp/q3-q4-q8-r2-pre-rerun-residual-fix-execution-ssot.md modules/domain/agents/director_ensemble.py modules/core/stage4_interview_round.py modules/core/stage4_reject_runtime.py modules/core/stage3_orchestrator.py modules/core/stage2_finalizer.py`
- queue integrity:
  - `python scripts/sync_temp_queue_state.py`
  - `python scripts/ops_validator.py`

## 11. Guardrails

- do not reopen Q5, Q6, or Q7 structural work in this tranche
- do not add new schema or raw-retention surfaces unless implementation is blocked without them
- do not change retry counts, quality thresholds, or adaptive grading policy
- do not treat this as a new long-function campaign
- keep fixes bounded and contract-oriented

## 12. Temp Queue Notes

- temp status: completed
- cleanup condition:
  - satisfied; temp mirror removed after realization, Codex audit, and closure
- roadmap dependency:
  - none required if this remains the only active temp execution mirror

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Opus Order Prompt

```text
System-track execution order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/temp/q3-q4-q8-r2-pre-rerun-residual-fix-execution-ssot.md
4. docs/2026-03-23/q3-q4-q8-r2-pre-rerun-residual-fix-execution-ssot.md
5. docs/2026-03-23/q1-q8-r2-merge-audit.md
6. docs/2026-03-23/opus/r2-q3-verdict-accuracy.md
7. docs/2026-03-23/opus/r2-q4-feedback-fidelity.md
8. docs/2026-03-23/opus/r2-q8-logging-retention.md

Task:
Implement the bounded pre-rerun residual fix cluster defined in docs/temp/q3-q4-q8-r2-pre-rerun-residual-fix-execution-ssot.md.

Primary goal:
Land the small residual fixes that remain after the R2 merge audit so the next rerun has cleaner verdict semantics, better Stage 2/3 DB parity, and less truncated post-run evidence.

Hard constraints:
- Follow the execution SSOT exactly.
- Do not widen scope.
- Do not reopen the closed broad DB/console waves.
- Do not refactor unrelated files.
- Do not change retry policy, threshold policy, or adaptive policy beyond the bounded downstream verdict-contract fix.
- Do not create new schema unless strictly required to unblock the scoped parity work.
- If an included item is already fixed in live code, shrink scope and continue.
- Do not close the execution SSOT after implementation; Codex will audit and close it.

Execution scope:
1. Q3 V60.97 downstream positive-verdict fix
2. Q8 Stage 3 save_stage_attempt rationale parity
3. Q8 Stage 2 save_stage_attempt rationale parity + reject_reason caller-side truncation removal
4. Q4/Q8 residual operator, session-log, and JSONL truncation cleanup
5. Regression tests for the touched seams

Out of scope:
- Q5 long-run consistency work
- Q6 structural retrieval-quality work
- Q7 context-budget work
- new raw-retention infrastructure
- new prompt tuning
- broad logging redesign

Required verification:
- python -m py_compile modules/domain/agents/director_ensemble.py modules/core/stage4_interview_round.py modules/core/stage4_reject_runtime.py modules/core/stage3_orchestrator.py modules/core/stage2_finalizer.py
- python -m pytest tests/test_director_modules.py -q
- python -m pytest tests/test_stage3_orchestrator.py -q
- python -m pytest tests/test_stage2_finalizer.py -q
- python -m pytest tests/test_stage4_interview_round.py -q
- python scripts/check_utf8_hygiene.py docs/2026-03-23/q3-q4-q8-r2-pre-rerun-residual-fix-execution-ssot.md docs/temp/q3-q4-q8-r2-pre-rerun-residual-fix-execution-ssot.md modules/domain/agents/director_ensemble.py modules/core/stage4_interview_round.py modules/core/stage4_reject_runtime.py modules/core/stage3_orchestrator.py modules/core/stage2_finalizer.py
- python scripts/sync_temp_queue_state.py
- python scripts/ops_validator.py

Output requirements:
- summarize exactly what changed by tranche
- list verification results
- list any deferred items and why
- state whether any included item was already resolved and skipped
- do not close the execution SSOT; Codex will handle closure
```
