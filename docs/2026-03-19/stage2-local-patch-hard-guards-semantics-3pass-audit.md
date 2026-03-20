# stage2-local-patch-hard-guards-semantics-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/stage2-local-patch-hard-guards-semantics-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 114`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/stage2-f2-patch-pressure-downgrade-semantics-3pass-audit.md`
- `docs/2026-03-19/stage2-arc-patch-observability-signals-3pass-audit.md`
Evidence Basis:
- `modules/core/stage2_finalizer.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_pass_with_fix.py`
Scope:
- audit the true hard guards around Stage 2 local Arc patching
- separate contract gate, hard reject paths, and patch-pressure advisory behavior
- determine whether current Stage 2 safety stack is coherent
- non-goal: redesign Stage 2 patch policy or change runtime code in this document

---

## Pass 1. Structure and Scope

This audit is intentionally narrow.

It covers only the Stage 2 local Arc patch loop inside `Stage2Finalizer`:
- entry gating by `fix_scope`
- patch existence requirement
- finalization outcome when the local patch attempt is unusable
- relation to patch-pressure advisory behavior

It does not cover:
- Stage 4 manuscript patch safety rules
- Stage 2 quality-gate floor after PASS/PASS_WITH_FIX acceptance
- whether current thresholds should later be tuned

Key operator question:
- what exactly counts as a blocking guard in Stage 2 local patching, and how is that different from warning or advisory behavior?

---

## Pass 2. Evidence and Consistency

### 1. Stage 2 has a contract gate before local patching

Observed live behavior in `modules/core/stage2_finalizer.py`:
- if `fix_scope` is missing, Stage 2 now breaks before local patching
- if resulting scope is `partial` or `full`, it breaks out of local inplace patching
- only `inplace` continues into `_inplace_patch_arc()`

Meaning:
- Stage 2 local patching is not unconditional
- and unlike the earlier runtime, score alone is no longer local patch authority

Conclusion:
- Stage 2 now begins with an explicit contract gate on local patch authority

### 2. Missing or failed local patch is a true blocking guard

After entering the local patch path:
- if `four_phase._inplace_patch_arc` is missing -> break
- if `_inplace_patch_arc()` returns falsy -> break
- exceptions in patch call -> break

Meaning:
- Stage 2 does not try a same-frame bounded patch fallback like Stage 4 manuscript repair
- local Arc patch failure is blocking for this loop and hands control back to the broader retry path

Supporting evidence from `tests/test_pass_with_fix.py`:
- the Stage 2 helper block still expects `patch 실패(None) -> REJECT 전환 (action=retry)`

Conclusion:
- Stage 2 local patch failure is a real blocking guard

### 3. Stage 2 safety stack is different from Stage 4

Stage 4 local manuscript repair distinguishes:
- contract gate
- hard guards
- bounded patch fallback
- full rewrite fallback

Stage 2 local Arc repair is simpler:
- contract gate
- local patch attempt
- if patch missing/fails -> break and retry path
- if patch succeeds but pressure is high -> advisory-only with metadata persistence
- if patch succeeds but Arc structure looks suspicious -> record observational `patch_guard_signals`

Meaning:
- Stage 2 has fewer local repair layers
- its safety model is tighter around local patch failure, while still remaining simpler than Stage 4
- and it now exposes a non-blocking observability layer for suspicious structured Arc patch output

Conclusion:
- the two stages should not be described as if they share one identical local patch stack
- Stage 2 now has three distinct layers:
  - contract gate
  - blocking patch failure
  - advisory / observability metadata

### 4. Patch pressure is not a hard guard in Stage 2

This audit depends on the adjacent `F-2` audit result:
- high patch pressure does not block the patch outright
- instead it remains advisory-only while persisting explicit metadata and warning context

Meaning:
- Stage 2 has both:
  - hard guards: missing patch / unusable local path
  - advisory path: high patch pressure

Conclusion:
- Stage 2 safety stack must be read as:
  - contract gate
  - blocking patch failure
  - advisory on high pressure
  - observational Arc patch signals

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. Stage 2 local Arc patching has real hard guards.

2. The key blocking guards are:
- no usable local patch agent/path
- local patch call failure
- falsy local patch result

3. High patch pressure is explicitly *not* one of those hard guards.
It belongs to the advisory layer instead.

4. Arc patch structural signals are also explicitly *not* hard guards.
They belong to the observability layer instead.

### Safe operating rule from this audit

Do:
- keep Stage 2 local patch hard guards and patch-pressure advisory conceptually separate
- keep Stage 2 described as a simpler local patch stack than Stage 4
- preserve the current tests that already cover blocking patch failure and pressure advisory

Do not:
- summarize Stage 2 as if every local patch issue were just advisory
- summarize Stage 2 as if it had the same patch fallback ladder as Stage 4
- casually unify Stage 2 and Stage 4 without first choosing a policy model

### Recommended next actions

1. Treat Stage 2 local patch hard guards as their own policy-boundary item.
2. If Stage 2/Stage 4 are ever unified, explicitly choose whether Stage 2 should gain:
   - additional local contract requirements beyond explicit `fix_scope`
   - bounded patch fallback
   - preserve-ratio style hard guards
3. Until then, keep current condensed docs explicit about Stage 2’s simpler safety stack.

### Audit result

- runtime code change: not needed
- regression hardening: updated by later explicit-`fix_scope` alignment work and Arc patch signal observability tests
- documentation conclusion: Stage 2 local patching has real blocking guards, now requires explicit `fix_scope` authority, records advisory `patch_pressure`, and also exposes non-blocking `patch_guard_signals` for structured Arc post-hoc review
