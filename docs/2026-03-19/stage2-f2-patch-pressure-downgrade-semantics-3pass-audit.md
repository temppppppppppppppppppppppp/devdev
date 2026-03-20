# stage2-f2-patch-pressure-downgrade-semantics-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/stage2-f2-patch-pressure-downgrade-semantics-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 114`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/stage4-f2-patch-pressure-advisory-semantics-3pass-audit.md`
Evidence Basis:
- `modules/core/stage2_finalizer.py`
- `tests/test_stage2_finalizer.py`
Scope:
- audit the meaning of Stage 2 `F-2` patch-pressure handling during `PASS_WITH_FIX`
- determine whether high patch pressure is advisory-only or verdict-affecting
- separate Stage 2 behavior from Stage 4 behavior
- note: the current runtime has been updated and this document reflects the new live policy

---

## Pass 1. Structure and Scope

This audit is intentionally narrow.

It covers only the `F-2` branch inside `Stage2Finalizer.run_finalize()` during the `PASS_WITH_FIX` local Arc patch loop:
- how `calc_patch_change_ratio()` is used
- what happens when change ratio exceeds the configured threshold
- whether final verdict is preserved, downgraded, or rejected

It does not cover:
- Stage 4 manuscript patch pressure handling
- Stage 2 preserve-ratio or other local patch hard guards
- whether the current threshold should later be tuned

Key operator question:
- when a Stage 2 inplace Arc patch changes too much, does the system merely warn, or does it keep the result in a lower-confidence verdict state?

---

## Pass 2. Evidence and Consistency

### 1. Stage 2 records patch pressure metadata when threshold is exceeded

Observed live behavior in `modules/core/stage2_finalizer.py`:
- compute `_change_ratio = calc_patch_change_ratio(_orig_j, _patch_j)`
- compare against `patch_mode.inplace_max_change_ratio` default `0.30`
- if exceeded:
  - set `_patch_pressure_exceeded = True`
  - populate `audit["patch_pressure"]` with:
    - `exceeded`
    - `count`
    - `change_ratio`
    - `max_ratio`
    - `attempt`
  - emit warning log

Meaning:
- high patch pressure is explicitly tracked
- this is not a transient debug-only signal

### 2. Stage 2 now stays advisory-only if Director still clears the Arc

The critical live distinction appears later in the same flow.

Observed behavior:
- if Director re-audit returns `PASS`
- and `_patch_pressure_exceeded` is true
- Stage 2 keeps:
  - `_d_decision = "PASS"`
  - `audit["decision"] = "PASS"`
  - `audit["patch_pressure"]["director_advisory_only"] = True`
  - `audit["patch_pressure"]["cleared_verdict"] = "PASS"`
  - reason text noting `PatchPressure Advisory`

Meaning:
- high patch pressure is not a hard reject
- and it is no longer a verdict downgrade either
- instead it is an advisory that remains visible in persistence and re-audit context

Conclusion:
- Stage 2 `F-2` is advisory-only with explicit persistence

### 3. Existing regression fixes the new contract

Direct regression evidence:
- `tests/test_stage2_finalizer.py::test_pass_with_fix_high_patch_pressure_is_advisory_only`

This test fixes:
- mocked `calc_patch_change_ratio = 0.75`
- Director second audit returns `PASS`
- final action is still `break`
- saved verdict remains `PASS`
- advisory flags record:
  - `patch_pressure_exceeded = 1`
  - `patch_pressure_count = 1`
- re-audit `story_context` carries `[F-2 advisory — high Arc patch pressure]`

Conclusion:
- the new contract is covered in code and regression

### 4. Stage 2 and Stage 4 are now aligned on the verdict axis

From the adjacent Stage 4 audit:
- Stage 4 `F-2` is advisory-only
- Director can still PASS and finalize as `PASS`

Stage 2 now behaves like this:
- Director can PASS on re-audit
- and high patch pressure no longer forces final decision back to `PASS_WITH_FIX`
- Stage 2 still persists stronger structured `patch_pressure` metadata than a plain warning

Operational meaning:
- Stage 2 treats aggressive local Arc modification as a warning Director may still clear fully
- but it keeps explicit structured metadata for later audit

Conclusion:
- the old verdict-level difference is gone
- remaining differences are in metadata shape and object type, not PASS-vs-PASS_WITH_FIX retention

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. Stage 2 `F-2` patch pressure is advisory-only.

2. It is also not a hard reject.

3. The correct classification is:
- warning + metadata recording + Director-context injection + verdict may remain `PASS`

### Safe operating rule from this audit

Do:
- keep Stage 2 `F-2` described as advisory-only with strong visibility
- keep its advisory flags in persistence
- keep its Director warning context explicit

Do not:
- describe Stage 2 `F-2` as mere logging
- silently convert Stage 2 `F-2` into auto-reject without a policy rewrite
- forget that metadata persistence still matters even when verdict remains `PASS`

### Recommended next actions

1. Treat Stage 2 `F-2` as a separate policy-boundary item from Stage 4 `F-2`.
2. Cross-stage policy is now closer on the verdict axis; remaining differences should be documented as metadata/payload differences, not PASS-vs-PASS_WITH_FIX retention.
3. Keep condensed status docs explicit about:
   - Stage 2: advisory-only + explicit `patch_pressure` persistence
   - Stage 4: advisory-only

### Audit result

- runtime code change: completed
- regression hardening: updated
- documentation conclusion: Stage 2 `F-2` high patch pressure is now advisory-only, keeps `patch_pressure` metadata, and no longer forces `PASS_WITH_FIX`
