# stage4-local-patch-hard-guards-semantics-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/stage4-local-patch-hard-guards-semantics-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 114`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/stage4-local-patch-decision-tree-semantics-3pass-audit.md`
- `docs/2026-03-19/stage4-f2-patch-pressure-advisory-semantics-3pass-audit.md`
Evidence Basis:
- `modules/core/stage4_interview_round.py`
- `tests/test_pass_with_fix.py`
- `tests/test_stage4_interview_round.py`
Scope:
- audit the true hard guards applied to Stage 4 local manuscript patching
- separate blocking guards from advisory-only signals
- determine whether current min-length and preserve-ratio behavior is intentional
- non-goal: redesign thresholds or change runtime code in this document

---

## Pass 1. Structure and Scope

This audit is intentionally narrow.

It covers only the hard guards around Stage 4 local patching:
- `patch_mode.min_patched_length`
- `patch_mode.inplace_min_preserve_ratio`
- how these guards behave in:
  - `PASS_WITH_FIX` local patch loop
  - retry-round `inplace_patch()` routing

It does not cover:
- `F-2` patch-pressure advisory semantics
- `fix_pack` contract gating
- Stage 2 or Stage 3 patch hard guards

Key operator question:
- which Stage 4 local patch checks are real blocking guards, and which are only warnings?

---

## Pass 2. Evidence and Consistency

### 1. PASS_WITH_FIX loop has two real hard guards before re-audit

Inside `_execute_pass_with_fix_loop()`, after `inplace_patch()` returns a manuscript:
- if patched manuscript is empty or shorter than `patch_mode.min_patched_length` default `2000`
  - log warning
  - mark `inplace` contract failure
  - widen next retry scope to `partial`
  - `break`
- if patched manuscript is below `patch_mode.inplace_min_preserve_ratio` default `0.70` of the current manuscript
  - log warning
  - mark `inplace` contract failure
  - widen next retry scope to `partial`
  - `break`

Meaning:
- Stage 4 does not even attempt Director re-audit for these obviously unsafe local patches
- these are blocking guards, not advisories
- but they are no longer silent aborts; the failure reason is preserved for later retry routing and audit

Supporting evidence:
- `tests/test_pass_with_fix.py::test_pf2_min_patched_length_yaml`
- `tests/test_pass_with_fix.py::test_pf2_inplace_preserve_ratio_yaml`
- `tests/test_pass_with_fix.py::test_pf3_pass_with_fix_shrunk_patch_becomes_reject`
- `tests/test_pass_with_fix.py::test_pass_with_fix_short_patch_becomes_reject`

Conclusion:
- `min_patched_length` and `inplace_min_preserve_ratio` are true hard gates in the PASS_WITH_FIX loop

### 2. Retry-round candidate generation uses the same hard-guard idea, but fail-soft

In `_generate_candidates()` retry mode:
- empty/blank inplace result -> patch fallback
- too-short inplace result -> patch fallback
- preserve-ratio failure -> patch fallback

Important distinction:
- the retry path does not abort the whole round
- it falls forward into `patch_with_feedback()`

Meaning:
- same safety principle
- different caller-level consequence

Supporting evidence:
- `tests/test_stage4_interview_round.py::test_reject_retry_shrunk_inplace_patch_falls_back_to_patch`
- `tests/test_stage4_interview_round.py::test_retry_inplace_requires_fix_pack_and_routes_to_patch`

Conclusion:
- the guard is still blocking for inplace adoption
- but the caller handles it fail-soft by escalating to the next repair layer

### 3. These guards are intentionally stronger than F-2

`F-2` patch pressure in the same loop does not `break`.

By contrast:
- min length does `break`
- preserve ratio does `break`

This makes the semantic split clear:
- `F-2` = advisory-only
- min length / preserve ratio = hard guard

Conclusion:
- the current code already distinguishes warnings from blocking guards in control flow, not only in comments

### 4. Operational meaning

The current Stage 4 local patch safety stack is layered:
- contract gate:
  - explicit `fix_scope=inplace`
  - valid local `fix_pack`
- hard guards:
  - minimum patch length
  - preserve ratio
- advisory:
  - high patch pressure (`F-2`)

This is coherent:
- contract decides whether local patching is allowed
- hard guards reject clearly unsafe patch outputs
- advisory warns about suspicious but still potentially acceptable outputs

Conclusion:
- the behavior is more structured than a single "patch succeeded/failed" summary suggests

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. `patch_mode.min_patched_length` and `patch_mode.inplace_min_preserve_ratio` are intentional hard guards in Stage 4 local patching.

2. Their semantics differ by caller:
- `PASS_WITH_FIX` loop: hard break, preserve explicit failure reason, and hand the next retry to `partial` patch lane
- retry round routing: hard reject for inplace adoption, then patch fallback

3. They should not be described as if they were only logging or advisory behavior.

4. As of `2026-03-19`, the operating decision is to stop here.
- keep current hard-guard behavior
- keep `PASS_WITH_FIX` contract failure recorded as failure
- keep next retry widened to `partial`
- do not add same-attempt emergency patch escalation in this item

### Safe operating rule from this audit

Do:
- keep these two checks classified as hard guards
- keep `F-2` classified separately as advisory-only
- preserve the existing regression coverage that proves both behaviors

Do not:
- collapse preserve-ratio failure into the same category as patch-pressure warning
- remove these guards casually while keeping local patch mode enabled
- summarize retry fallback and PASS_WITH_FIX abort as if they were identical outcomes

### Recommended next actions

1. Treat Stage 4 local patch hard guards as a separate policy-boundary item from `F-2`.
2. If thresholds change later, revisit them as a coordinated Stage 4 local patch safety rewrite.
3. Keep condensed operational summaries explicit about:
   - contract gate
   - hard guard
   - advisory
4. If same-attempt emergency patch escalation is revisited later, treat it as a separate policy rewrite rather than a small extension of this item.

### Audit result

- runtime code change: not needed
- regression hardening: not needed beyond current coverage
- documentation conclusion: Stage 4 min-length and preserve-ratio checks are intentional hard guards, current retry-to-partial behavior stays, and same-attempt emergency patch escalation remains deferred unless a later policy rewrite justifies it
