# Q3-Q4-Q6 Pre-Rerun Fixes Execution SSOT

Date: 2026-03-23
Status: closed
Canonical Path: `docs/2026-03-23/q3-q4-q6-pre-rerun-fixes-execution-ssot.md`
Temp Mirror Path: `docs/temp/q3-q4-q6-pre-rerun-fixes-execution-ssot.md`
Commit State:
- Baseline Commit: `a3b9a286`
- Baseline Dirty Summary: `dirty: active 2026-03-23 docs, runtime/db edits, and two pending Q8 execution items`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `Opus realization audited by Codex; one ep_type forwarding drift corrected before closure`
Source Survey Docs:
- `docs/2026-03-23/q1-q8-current-state-merge-audit.md`
- `docs/2026-03-23/opus/q3-verdict-accuracy-deep-dive.md`
- `docs/2026-03-23/opus/q4-feedback-loop-deep-dive.md`
- `docs/2026-03-23/opus/q6-selective-retrieval-deep-dive.md`
- `docs/2026-03-23/fresh-run-3pass-audit-report.md`
Evidence Artifacts:
- `docs/2026-03-23/opus/q3-verdict-accuracy-evidence-manifest.md`
- `docs/2026-03-23/opus/q6-selective-retrieval-evidence-manifest.md`
Side-Effect Coverage: covered

## 1. Intent
- Realize the minimum bounded fixes required before the next fresh run.
- Target the three axes that the merge audit ranked as pre-rerun blockers:
  - Q3 verdict accuracy
  - Q4 feedback-loop fidelity
  - Q6 retrieval silent degradation
- Explicitly avoid duplicating active Q8 work already covered by the DB max-retention and console max-display execution items.

## 2. Baseline Facts
- The last fresh run failed for reasons clustered under `LLM-Director 정합성 불일치`, not under long-function regressions.
- Q3 has live-evidence-backed problems in the verdict chain:
  - V60.97 swap resets score to 50 and can force a REJECT path without a clean re-judgment contract
  - adaptive decision call site omits `ep_type`
  - adaptive decision call site is not fail-closed around grading exceptions
- Q4 has live source evidence that reject/fix guidance loses fidelity before the next generation attempt:
  - `rejection_reason` is replaced by merged feedback text in retry snapshot
  - `contradiction_details` are reduced to 3 items
  - re-audit validation context truncates prior feedback into small warning/focus-point snippets
- Q6's dominant rerun blocker is silent degradation, not catastrophic failure:
  - multi-query fallback is silent
  - advisor fallback to legacy retrieval is silent
  - embedding cache is not invalidated on model change
  - slot cap truncation occurs before priority sort
- Q8 findings about console truncation and DB retention are already being handled by:
  - `docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md`
  - `docs/2026-03-23/console-log-max-display-post-audit-execution-ssot.md`

## 3. Scope
Included:
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/director_grading.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/vec_memory.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/context_advisor.py`
- targeted tests for verdict path, feedback path, and retrieval fallback/ordering

Excluded:
- DB max-retention changes already in active Q8 queue
- console max-display truncation removal already in active Q8 queue
- threshold tuning beyond the bounded Q3 fixes in this document
- broad retrieval redesign
- long-run Q5/Q7 structural refactors

## 4. Execution Classes
- Class A. Verdict-path correctness
  - changes that directly affect whether a candidate is judged consistently with Director intent
- Class B. Feedback fidelity preservation
  - changes that preserve corrective signal between reject and next retry
- Class C. Retrieval observability minima
  - changes that make degraded retrieval visible and stop one known correctness leak

## 5. Realization Tranches
1. Q3 verdict safety and forwarding tranche
   - wrap the `apply_adaptive_decision(...)` call site in a fail-closed guard
   - forward `ep_type` to adaptive decision
   - repair the V60.97 post-swap contract so a swapped candidate is not simply score-reset into a forced REJECT path without an explicit re-evaluation path
2. Q4 feedback preservation tranche
   - preserve the original `rejection_reason` in the reject retry snapshot
   - stop shrinking `contradiction_details` to a tiny fixed subset for retry handoff
   - remove or relax the small re-audit feedback truncation in `stage4_retry_runtime.py` warning/focus-point construction
3. Q6 retrieval observability and correctness-minimum tranche
   - emit operator/log warnings when multi-query fallback triggers
   - emit warning when advisor planning falls back to legacy retrieval
   - clear embedding cache on model mismatch
   - sort retrieval slots by priority before cap truncation
4. Verification and rerun-readiness tranche
   - targeted tests for the three families
   - verify no duplicate Q8 work was reintroduced
   - confirm this item plus the two active Q8 items define the full pre-rerun queue

## 6. Acceptance Criteria
- Q3:
  - adaptive grading exceptions cannot crash the verdict pipeline
  - `ep_type` reaches adaptive decision
  - V60.97 swap no longer creates the observed unconditional reset-to-REJECT cascade
- Q4:
  - original reject reason survives into retry handoff
  - contradiction details are not collapsed to a tiny subset during retry handoff
  - re-audit feedback context no longer drops most corrective signal
- Q6:
  - multi-query fallback is visible in logs
  - advisor fallback is visible in logs
  - embedding cache invalidates on model change
  - slot cap respects priority before truncation
- No duplicate realization of Q8 DB/console work occurs in this item

## 7. Verification Plan
- `python -m py_compile modules/domain/agents/director_ensemble.py modules/domain/agents/director_grading.py modules/core/stage4_reject_runtime.py modules/core/stage4_retry_runtime.py modules/core/vec_memory.py modules/core/stage4_context_builder.py modules/core/context_advisor.py`
- targeted low-memory pytest shards covering:
  - verdict accuracy / director ensemble
  - Stage 4 reject + retry handoff
  - retrieval fallback and ordering
- `python scripts/check_utf8_hygiene.py docs/2026-03-23/q3-q4-q6-pre-rerun-fixes-execution-ssot.md docs/temp/q3-q4-q6-pre-rerun-fixes-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 8. Guardrails
- Do not duplicate Q8 active queue work in this item.
- Do not tune unrelated thresholds or retry counts.
- Do not widen this into a full refactor wave.
- Keep fresh-run blockers separate from long-run architecture debt.
- Preserve current authority ownership: Director remains the verdict owner.

## 9. Temp Queue Notes
- temp status: removed after Codex closure
- cleanup condition:
  - completed
- roadmap dependency:
  - `docs/2026-03-23/max-retention-observability-execution-roadmap.md`

## 10. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 10A. Opus Dispatch Prompt
Use this exact prompt when handing the item to Opus:

```text
System-track execution order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/temp/q3-q4-q6-pre-rerun-fixes-execution-ssot.md
4. docs/2026-03-23/q3-q4-q6-pre-rerun-fixes-execution-ssot.md
5. docs/2026-03-23/q1-q8-current-state-merge-audit.md
6. docs/2026-03-23/opus/q3-verdict-accuracy-deep-dive.md
7. docs/2026-03-23/opus/q4-feedback-loop-deep-dive.md
8. docs/2026-03-23/opus/q6-selective-retrieval-deep-dive.md
9. docs/2026-03-23/max-retention-observability-execution-roadmap.md

Task:
Implement the bounded pre-rerun fixes defined in docs/temp/q3-q4-q6-pre-rerun-fixes-execution-ssot.md.

Primary goal:
Fix the minimum live blockers that should be resolved before the next fresh run, limited to Q3 verdict accuracy, Q4 feedback fidelity, and Q6 retrieval silent degradation.

Hard constraints:
- Follow the execution SSOT exactly.
- Do not widen scope.
- Do not duplicate active Q8 DB or console work.
- Do not open a refactor wave.
- Do not change Director authority ownership.
- Do not tune unrelated thresholds or retry counts.
- If an included item is already fixed in live code, shrink scope and continue.
- Do not close the execution SSOT after implementation; Codex will audit and close it.

Execution scope:
1. Q3 verdict safety and forwarding
- wrap apply_adaptive_decision(...) in a fail-closed guard
- forward ep_type
- repair the V60.97 post-swap reset-to-REJECT cascade without changing broader verdict policy

2. Q4 feedback preservation
- preserve original rejection_reason in retry handoff
- stop shrinking contradiction_details to a tiny subset
- remove or relax small re-audit warning/focus truncation in stage4_retry_runtime.py

3. Q6 retrieval observability and correctness minima
- emit warnings when multi-query fallback triggers
- emit warnings when advisor planning falls back to legacy retrieval
- clear embedding cache on model mismatch
- sort slots by priority before cap truncation

4. Verification
- run targeted low-memory tests for verdict, retry handoff, and retrieval ordering/fallback
- verify no duplicate Q8 work was reintroduced

Implementation rules:
- Use apply_patch for edits.
- Keep comments short and boundary-oriented.
- Preserve behavior except for the intended bounded fixes.
- If a hidden design fork appears, stop and report it rather than improvising a wider change.

Required verification:
- python -m py_compile modules/domain/agents/director_ensemble.py modules/domain/agents/director_grading.py modules/core/stage4_reject_runtime.py modules/core/stage4_retry_runtime.py modules/core/vec_memory.py modules/core/stage4_context_builder.py modules/core/context_advisor.py
- targeted low-memory pytest shards covering:
  - verdict accuracy / director ensemble
  - Stage 4 reject + retry handoff
  - retrieval fallback and ordering
- python scripts/check_utf8_hygiene.py docs/2026-03-23/q3-q4-q6-pre-rerun-fixes-execution-ssot.md docs/temp/q3-q4-q6-pre-rerun-fixes-execution-ssot.md
- python scripts/sync_temp_queue_state.py
- python scripts/ops_validator.py

Output requirements:
- summarize exactly what changed by tranche
- list verification results
- list any deferred item and why
- do not close or supersede the execution SSOT; Codex will audit that afterward
```

## 11. 3-Pass Audit Record
- Pass 1: collapsed Q3/Q4/Q6 findings into rerun-relevant classes and discarded Q8 overlap
- Pass 2: split correctness, feedback, and retrieval minima into bounded tranches
- Pass 3: rechecked queue lineage against the existing two-item roadmap and set this item as the third queue entry

## 11A. Closure Note
- Realized by Opus, then audited by Codex.
- Codex corrected one live drift: `ep_type` now reaches `apply_adaptive_decision(...)` in `director_ensemble.py`.
- Verification passed on:
  - `tests/test_director_modules.py`
  - `tests/test_stage4_interview_round.py`
  - `tests/test_context_advisor.py`
  - `tests/test_vec_memory.py`
  - `tests/test_stage4_context_builder.py`
- A small subset of `director_ensemble.py` operator max-display / provenance work landed incidentally during this item. Treat that as realized baseline for the active `console-log-max-display-post-audit-execution-ssot` rather than reopening it here.

## 12. Confidence
- Estimated confidence: 96%
- Residual uncertainty:
  - exact V60.97 repair shape should be chosen during implementation Pass 1
  - retrieval warning formatting can stay compact as long as degradation becomes visible
