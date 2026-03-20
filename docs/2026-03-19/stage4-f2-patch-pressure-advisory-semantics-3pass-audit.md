# stage4-f2-patch-pressure-advisory-semantics-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/stage4-f2-patch-pressure-advisory-semantics-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 114`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/stage4-local-patch-decision-tree-semantics-3pass-audit.md`
Evidence Basis:
- `modules/core/stage4_interview_round.py`
- `tests/test_pass_with_fix.py`
- `tests/test_stage4_interview_round.py`
Scope:
- audit the meaning of Stage 4 `F-2` patch-pressure handling for `PASS_WITH_FIX` local manuscript patching
- determine whether `change_ratio > patch_mode.inplace_max_change_ratio` is an advisory or a hard gate
- lock the current behavior with direct regression coverage
- non-goal: redesign the patch-pressure threshold or change runtime code in this document

---

## Pass 1. Structure and Scope

This audit is intentionally narrow.

It covers only the `F-2` branch inside `Stage4InterviewRound._execute_pass_with_fix_loop()`:
- how `calc_patch_change_ratio()` is used
- what happens when the ratio exceeds the configured threshold
- whether this branch blocks adoption or only informs Director re-audit

It does not cover:
- Stage 2 patch-pressure handling
- patch preserve-ratio hard guards
- whether the current `0.30` threshold should later be tuned

Key operator question:
- when an inplace manuscript patch changes too much, does Stage 4 immediately reject it, or does it treat that fact as a warning for Director re-audit?

---

## Pass 2. Evidence and Consistency

### 1. Live code computes patch pressure but does not abort on it

Observed behavior in `modules/core/stage4_interview_round.py`:
- compute `_change_ratio = calc_patch_change_ratio(_current_ms, _patched_ms)`
- store both:
  - `patch_trace["change_ratio"]`
  - `patch_trace["unchanged_ratio"]`
- compare against `patch_mode.inplace_max_change_ratio` default `0.30`
- if exceeded:
  - build `_f2_advisory`
  - emit warning log
  - continue into Director re-audit

Important negative evidence:
- there is no `break`
- there is no forced `REJECT`
- there is no downgrade to patch/rewrite solely because `F-2` fired

Conclusion:
- `F-2` is advisory-only at this layer

### 2. The advisory is injected into Director re-audit context

After the ratio check, Stage 4 builds `_re_val_ctx` for Director re-audit.

Observed behavior:
- baseline re-audit warnings are always added
- if `_f2_advisory` exists, it is appended to `validation_results[0]["warnings"]`

Meaning:
- patch pressure does not disappear into logs only
- it is surfaced to the Director LLM as a focused caution

Conclusion:
- the design intent is "warn the Director re-audit", not "hard-stop the patch"

### 3. This behavior is consistent with Director sovereignty

The workspace rule is not "patch heuristics decide quality."
The workspace rule is "Director decides quality."

That matters here because `F-2` is only a risk signal:
- it says the local patch changed more than expected
- it does not itself prove the result is bad
- the final quality decision still belongs to Director re-audit

Meaning:
- `F-2` is an input to judgment
- it is not a substitute for judgment

Conclusion:
- keeping `F-2` advisory-only is the design that best matches Director sovereignty

### 4. New direct regression closes the main semantic gap

Before this audit, tests covered:
- `calc_patch_change_ratio()` utility behavior
- `patch_trace` persistence and `unchanged_ratio` serialization

But there was no direct regression proving:
- `change_ratio > 30%` still allows a PASS outcome if Director re-audit accepts it
- the `[F-2 경고]` string is actually present in the re-audit warning payload

New regression:
- `tests/test_pass_with_fix.py::test_pf2_high_change_ratio_is_advisory_not_hard_gate`

This test now fixes:
- mocked `calc_patch_change_ratio = 0.75`
- Director re-audit returns `PASS`
- loop still returns `PASS`
- `patch_trace["change_ratio"] == 0.75`
- `patch_trace["unchanged_ratio"] == 0.25`
- `[F-2 경고]` is present in re-audit warnings

Conclusion:
- the advisory-only semantics are now directly covered

### 5. Relation to stronger hard guards

Stage 4 already has true hard guards elsewhere in the same loop:
- minimum patched length
- preserve-ratio shrink guard
- invalid local-repair contract

Those branches do abort or reroute.

That matters because it makes `F-2` easier to classify:
- when Stage 4 wants a hard gate, it already uses explicit control flow
- `F-2` does not use that control flow

Conclusion:
- `F-2` is intentionally weaker than the real hard gates

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. Stage 4 `F-2` patch-pressure handling is an advisory, not a hard gate.

2. The current invariant is:
- compute patch pressure
- record it in patch trace
- surface it to Director re-audit
- let Director decide whether the patch still passes

3. Any summary that says "`change_ratio > 30%` means Stage 4 local patch is automatically rejected" is incorrect.

### Safe operating rule from this audit

Do:
- keep `F-2` as advisory-only unless a deliberate policy rewrite says otherwise
- keep patch-pressure metadata in `patch_trace`
- keep the new direct regression that proves Director can still PASS after an `F-2` warning
- keep this area explicitly documented as a Director-sovereignty boundary

Do not:
- mistake the warning log for a hard gate
- silently convert `F-2` into auto-reject behavior without a policy decision
- describe `F-2` as equivalent to preserve-ratio or min-length hard guards
- let OPUS-style compressed summaries flatten "Director warning input" into "automatic block"

### Recommended next actions

1. Treat `F-2` as a Stage 4 policy-boundary item, not as a cleanup bug.
2. If the team later wants `F-2` to block, redesign it explicitly as a hard gate and adjust tests accordingly.
3. Keep OPUS-style summaries from collapsing "warning", "Director judgment input", and "blocking guard" into the same sentence.

### Audit result

- runtime code change: not needed
- regression hardening: completed
- documentation conclusion: Stage 4 `F-2` high patch-pressure handling is advisory-only, remains under Director judgment, and should stay unless policy rewrite justifies a change
