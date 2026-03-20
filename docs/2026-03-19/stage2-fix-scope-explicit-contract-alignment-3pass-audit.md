# stage2-fix-scope-explicit-contract-alignment-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.97`
Canonical Path: `docs/2026-03-19/stage2-fix-scope-explicit-contract-alignment-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 115`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/stage2-stage4-fix-scope-missing-divergence-3pass-audit.md`
- `docs/2026-03-19/stage2-local-patch-hard-guards-semantics-3pass-audit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Evidence Basis:
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_preflight.py`
- `tests/test_pass_with_fix.py`
- `tests/test_stage2_preflight.py`
Scope:
- align Stage 2 local Arc repair authority with the stricter explicit-contract rule already used on Stage 4
- remove score-based fallback when `fix_scope` is missing
- keep the rest of Stage 2 safety semantics unchanged
- non-goal: port Stage 4 manuscript hard guards or Fix Pack contract to Stage 2

---

## Pass 1. Structure and Scope

This change is intentionally narrow.

It touches only the meaning of missing `fix_scope` in Stage 2 local Arc repair:
- `Stage2Finalizer`
- `Stage2Preflight`

It does not change:
- Stage 2 `F-2` patch-pressure advisory behavior
- Stage 2 local patch fail-soft retry structure
- Stage 4 `fix_pack` contract
- Stage 4 min-length or preserve-ratio hard guards

Key operator question:
- if Director did not explicitly authorize a local Arc repair scope, should Stage 2 still infer `inplace/full` from score?

---

## Pass 2. Evidence and Consistency

### 1. Previous live divergence was real

Historical audit already confirmed that Stage 2 differed from Stage 4:
- Stage 2 used score fallback when `fix_scope` was missing
- Stage 4 treated missing `fix_scope` as explicit-contract failure

That divergence existed in two Stage 2 layers:
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_preflight.py`

Meaning:
- even if finalizer stopped local patching, the next retry could still reopen local patch paths from score alone

### 2. Runtime now requires explicit `fix_scope` in both Stage 2 layers

Updated behavior:
- `Stage2Finalizer`:
  missing `fix_scope` no longer score-falls-back to `inplace/full`
  it now logs no local patch authority and returns to retry handling
- `Stage2Preflight`:
  missing `fix_scope` no longer opens `inplace` or patch mode from previous score
  it now skips local patch lanes and proceeds to full generate

Meaning:
- Stage 2 no longer infers local repair authority from score alone
- the Stage 2 retry path is now consistent with the stricter explicit-contract interpretation

### 3. The alignment is intentionally partial, not a full Stage 4 copy

This change does **not** import the full Stage 4 local-patch stack.

Still unchanged in Stage 2:
- no Stage 4-style min-length hard guard
- no Stage 4-style preserve-ratio hard guard
- no mandatory Fix Pack contract

That is intentional because Stage 2 patches structured Arc dicts, not manuscripts.

Conclusion:
- Stage 2 is aligned on local-patch authority
- Stage 2 is not blindly cloned from Stage 4

### 4. Regression coverage now fixes the new contract

New or updated regression evidence:
- `tests/test_pass_with_fix.py::test_s2_fix_scope_missing_skips_inplace`
  proves missing `fix_scope` in `Stage2Finalizer` does not call `_inplace_patch_arc()` and returns retry
- `tests/test_stage2_preflight.py::test_missing_fix_scope_skips_local_patch_and_uses_full_generate`
  proves retry preflight no longer opens local patch lanes from score alone

Supporting surrounding coverage remains:
- `tests/test_pass_with_fix.py::test_s2_fix_scope_partial_skips_inplace`
- `tests/test_pass_with_fix.py::test_s2_fix_scope_full_skips_inplace`
- existing Stage 2 `F-2` downgrade and patch-failure regressions

Conclusion:
- the old divergence is now closed in runtime and in regression coverage

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. Stage 2 should no longer infer local Arc repair authority from score when `fix_scope` is missing.

2. The safe invariant is now:
- explicit `fix_scope="inplace"`: local inplace repair allowed
- explicit `fix_scope="partial"`: broader local patch lane allowed in preflight
- explicit `fix_scope="full"`: regenerate lane
- missing `fix_scope`: no local patch authority

3. This resolves the most important Stage2-vs-Stage4 contract divergence without importing manuscript-specific hard guards.

### Safe operating rule from this change

Do:
- require explicit `fix_scope` for Stage 2 local repair authority
- keep Stage 2 and Stage 4 different where data shape truly differs
- keep historical divergence docs as evidence of what changed

Do not:
- reintroduce score fallback for missing `fix_scope`
- treat score alone as local repair authority
- copy Stage 4 hard guards into Stage 2 without a separate policy decision

### Recommended next actions

1. Mark the old Stage2-vs-Stage4 `fix_scope` divergence as resolved in the current status doc.
2. Keep future Stage 2 policy work focused on the remaining items:
   - `F-2` downgrade semantics
   - local patch hard-guard applicability
3. If Stage 2 ever adopts a stronger local contract later, evaluate that separately from this authority alignment.

### Audit result

- runtime code change: completed
- regression hardening: completed
- documentation conclusion: Stage 2 now requires explicit `fix_scope` for local patch authority; the prior score-fallback divergence with Stage 4 is closed
