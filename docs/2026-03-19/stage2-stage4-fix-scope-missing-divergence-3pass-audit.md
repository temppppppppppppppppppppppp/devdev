# stage2-stage4-fix-scope-missing-divergence-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/stage2-stage4-fix-scope-missing-divergence-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 114`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/stage4-local-patch-decision-tree-semantics-3pass-audit.md`
Evidence Basis:
- `modules/core/stage2_finalizer.py`
- `modules/core/stage4_interview_round.py`
- `tests/test_pass_with_fix.py`
Scope:
- audit the live divergence between Stage 2 and Stage 4 when `PASS_WITH_FIX` arrives without explicit `fix_scope`
- determine whether the current difference is real runtime policy or documentary noise
- non-goal: unify the two layers or change runtime code in this document

---

## Pass 1. Structure and Scope

This audit is intentionally narrow.

It covers only one question:
- what happens when `PASS_WITH_FIX` lacks explicit `fix_scope`

Compared layers:
- Stage 2 `Stage2Finalizer`
- Stage 4 `Stage4InterviewRound`

It does not cover:
- `fix_pack` completeness beyond what is needed for this comparison
- patch pressure behavior
- preserve-ratio or min-length hard guards

Key operator question:
- do Stage 2 and Stage 4 currently treat missing `fix_scope` the same way?

---

## Pass 2. Evidence and Consistency

### 1. Stage 2 still has score-based fallback

Observed live behavior in `modules/core/stage2_finalizer.py`:
- in the PASS_WITH_FIX loop
- if `_fix_scope` is missing
- load `patch_mode.inplace_below` default `60`
- set:
  - `"inplace"` if `_score >= threshold`
  - `"full"` otherwise
- emit warning log:
  - `[PF-1] fix_scope 누락 -> score=%d fallback: %s`

Meaning:
- Stage 2 still uses score as a fallback repair-scope inference when explicit scope is absent

Conclusion:
- Stage 2 is permissive here

### 2. Stage 4 rejects the same ambiguity

Observed live behavior in `modules/core/stage4_interview_round.py`:
- `_evaluate_pass_with_fix_contract()` treats missing scope as `missing_fix_scope`
- `_enforce_pass_with_fix_contract()` downgrades invalid `PASS_WITH_FIX` to `REJECT`
- `_execute_pass_with_fix_loop()` aborts with Lane3 Gate notice when contract is not eligible

Supporting regression:
- `tests/test_pass_with_fix.py::test_pf1_fix_scope_missing_high_score`
- `tests/test_pass_with_fix.py::test_pf1_fix_scope_missing_low_score`

Both now expect:
- `REJECT`
- no inplace patch call

Meaning:
- Stage 4 no longer allows score-only inplace fallback
- it requires explicit local-repair semantics

Conclusion:
- Stage 4 is strict here

### 3. The divergence is real, not documentary

This is not a wording problem.

Stage 2:
- score-based fallback still exists in live control flow

Stage 4:
- score-based fallback was deliberately removed from live control flow

Operational meaning:
- the two stages currently implement different policy choices

Conclusion:
- any compressed summary that says "missing fix_scope falls back the same way everywhere" is wrong

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. Stage 2 and Stage 4 intentionally diverge today on missing `fix_scope`.

2. Current live summary is:
- Stage 2: missing `fix_scope` can still infer `inplace` from score
- Stage 4: missing `fix_scope` is contract failure and causes downgrade/abort

3. This divergence should be documented as-is until an explicit unification decision is made.

### Safe operating rule from this audit

Do:
- document the Stage 2 / Stage 4 difference explicitly
- treat Stage 4 as the stricter contract layer
- avoid assuming that Stage 2 semantics automatically imply Stage 4 semantics

Do not:
- collapse the two layers into one sentence in roadmap or audit summaries
- "fix" one side casually without deciding whether cross-stage unification is intended

### Recommended next actions

1. Keep this divergence visible in the status board.
2. If unification is desired later, decide which rule wins:
   - Stage 2 permissive score fallback
   - Stage 4 explicit contract-only rule
3. Until then, treat both as policy-boundary items, not cleanup bugs.

### Audit result

- runtime code change: not needed
- regression hardening: already sufficient for Stage 4 side
- documentation conclusion: Stage 2 and Stage 4 differ intentionally on missing `fix_scope`, and that divergence should remain explicit unless policy rewrite justifies unification
