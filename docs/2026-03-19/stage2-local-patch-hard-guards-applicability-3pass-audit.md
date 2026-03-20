# stage2-local-patch-hard-guards-applicability-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/stage2-local-patch-hard-guards-applicability-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 114`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/stage4-local-patch-hard-guards-semantics-3pass-audit.md`
- `docs/2026-03-19/stage2-arc-patch-observability-signals-3pass-audit.md`
Evidence Basis:
- `modules/core/stage2_finalizer.py`
- `tests/test_stage2_finalizer.py`
Scope:
- inspect whether Stage 2 local Arc patching has Stage4-like hard guards for min-length or preserve-ratio
- determine whether that comparison is applicable, absent, or stale
- non-goal: redesign Stage 2 local patch policy or change runtime code in this document

---

## Pass 1. Structure and Scope

This audit is intentionally narrow.

Question:
- does Stage 2 local Arc patching have a direct equivalent of Stage 4 manuscript hard guards such as:
  - minimum patched length
  - preserve ratio floor

It does not cover:
- Stage 2 patch-pressure advisory behavior
- Stage 2 explicit `fix_scope` authority alignment behavior
- Stage 4 local patch safety stack beyond comparison context

---

## Pass 2. Evidence and Consistency

### 1. Stage 2 local patch object is structurally different

Stage 2 local patching operates on Arc data:
- `_four_phase._inplace_patch_arc(original_arc=..., ...)`
- result is a structured Arc dict, not a manuscript string

Operational consequence:
- Stage 4-style manuscript length checks are not directly portable

### 2. Live Stage 2 code does not implement Stage4-like min-length or preserve-ratio guards

Observed in `modules/core/stage2_finalizer.py` PASS_WITH_FIX patch loop:
- check agent availability
- attempt `_inplace_patch_arc()`
- fail if patch result is falsy
- run arithmetic warning checks
- compute patch-pressure change ratio
- re-audit via Director

What is not present:
- no `min_patched_length`
- no `inplace_min_preserve_ratio`
- no text-length shrink hard gate

Conclusion:
- Stage 2 does not currently have the Stage 4 manuscript hard guards

### 3. Existing regression coverage is sufficient for this conclusion

Relevant tests already prove the adjacent live behavior:
- `tests/test_stage2_finalizer.py::test_pass_with_fix_high_patch_pressure_is_advisory_only`
- `tests/test_stage2_finalizer.py::test_pass_with_fix_records_arc_patch_guard_signals`
- `tests/test_stage2_finalizer.py::test_director_reject_returns_retry`

Because no Stage4-like hard-guard branches exist in Stage 2 code, there is no missing direct regression for such a branch.

Conclusion:
- this is not a coverage hole
- it is an applicability difference

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. Stage 2 local Arc patching does not currently have Stage4-like min-length or preserve-ratio hard guards.

2. That is not evidence of stale tests by itself.
It is mainly a consequence of Stage 2 patching structured Arc data rather than manuscript text.

3. The correct Stage 2 policy boundaries remain:
- patch-pressure advisory behavior
- explicit `fix_scope` authority for local patch entry
- observational `patch_guard_signals` for suspicious structured output

### Safe operating rule from this audit

Do:
- treat Stage2-vs-Stage4 hard-guard comparison as non-applicable unless Arc patch structure changes
- document the absence explicitly to avoid future false assumptions

Do not:
- assume Stage 2 forgot to add Stage 4 manuscript guards just because the names do not appear
- inflate this into a bug report without a design decision about structured Arc patch safety

### Recommended next actions

1. Keep Stage 2 hard-guard comparison marked as non-applicable / absent in status summaries.
2. If Arc patch safety is revisited later, evaluate structured-Arc-specific guards rather than copying manuscript-length guards.
3. Use the existing `patch_guard_signals` evidence surface first, and only promote a signal to hard-guard status if live evidence shows the signal is high-value and low-noise.

### Audit result

- runtime code change: not needed
- regression hardening: not needed
- documentation conclusion: Stage 2 local Arc patching has no direct Stage4-style min-length or preserve-ratio hard guards, now has non-blocking `patch_guard_signals` for structured observability, and remains an applicability difference rather than a demonstrated bug
