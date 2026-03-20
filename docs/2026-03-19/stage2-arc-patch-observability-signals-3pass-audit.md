# stage2-arc-patch-observability-signals-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/stage2-arc-patch-observability-signals-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 114`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/stage2-local-patch-hard-guards-semantics-3pass-audit.md`
- `docs/2026-03-19/stage2-local-patch-hard-guards-applicability-3pass-audit.md`
Evidence Basis:
- `modules/core/stage2_finalizer.py`
- `tests/test_stage2_finalizer.py`
Scope:
- add narrow, observational-only signals for Stage 2 local Arc patch results
- persist those signals across audit metadata, advisory flags, audit_event, and Director re-audit context
- keep the feature strictly non-blocking
- non-goal: redesign Stage 2 local patch policy or invent new hard guards

---

## Pass 1. Structure and Scope

This audit is intentionally narrow.

It does not change whether Stage 2 local patching is allowed.
It does not add a new reject rule.
It only makes suspicious Arc patch results visible enough for post-hoc review and recursive improvement.

Key operator question:
- if a Stage 2 local Arc patch looks structurally suspicious, where is that evidence supposed to live before we decide whether any future hard guard is justified?

---

## Pass 2. Evidence and Consistency

### 1. The new signals are deliberately narrow

Live `Stage2Finalizer` now records only four low-noise signal types:
- `missing_tactical_doc`
- `structured_section_dropped`
- `structured_section_type_drift`
- `episode_span_inconsistent`

These are intentionally narrower than Stage 4 manuscript guards.
They are based on Arc structure that already exists in live artifacts:
- `tactical_doc`
- `state_changes`
- `joint_docs`
- `status_shadow`
- `hybrid_composition`
- `ep_start/ep_end/ep_count`

Conclusion:
- the new surface is not a broad heuristic layer
- it is a compact structural watchlist

### 2. The signals are observational, not blocking

Observed live behavior in `modules/core/stage2_finalizer.py`:
- signals are collected after `_inplace_patch_arc()` returns
- they are merged into `audit["patch_guard_signals"]`
- they are logged through `audit_event("patch_guard_signal", ...)`
- they are injected into Director re-audit `story_context`
- they are summarized into persisted `advisory_flags`

What they do *not* do:
- they do not break the local patch loop by themselves
- they do not downgrade verdict on their own
- they do not replace the existing `patch_pressure` advisory

Conclusion:
- Stage 2 now has a real observability layer for Arc patch quality
- but policy authority remains unchanged

### 3. The persistence surfaces are sufficient for recursive improvement

The feature now leaves evidence in four places:
- full metadata in `audit["patch_guard_signals"]`
- compact counts/codes in `advisory_flags`
- event-level logging in `audit_event`
- review-time warning context in Director re-audit `story_context`

This means future policy work can answer:
- which signals fire in practice
- whether they correlate with later REJECT or retry
- whether any one signal is noisy enough to stay advisory-only

Conclusion:
- this is the right first step before inventing Arc-specific hard guards

### 4. Regression now locks the contract

Direct regression evidence:
- `tests/test_stage2_finalizer.py::test_pass_with_fix_records_arc_patch_guard_signals`

This test fixes the current contract:
- `PASS_WITH_FIX` enters Stage 2 local patch loop
- patched Arc emits multiple structural signals
- final flow may still end in `PASS`
- `advisory_flags` persist signal count/codes
- Director re-audit sees `[S2 Arc patch signals]`
- `audit_event` records the signal payload

Conclusion:
- the feature is not documentation-only
- its observability contract is regression-backed

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. Stage 2 local Arc patching now has a narrow observational signal layer.

2. That layer is intentionally non-blocking.

3. This is the correct order of operations:
- first collect reliable structural evidence
- then decide later whether any one signal deserves hard-guard status

4. As of `2026-03-19`, the operating decision is:
- keep these signals observational-only
- do not promote them to blocking guards yet
- require live evidence before any signal is considered for hard-guard status

### Safe operating rule from this audit

Do:
- treat `patch_guard_signals` as evidence for post-hoc review and recursive improvement
- keep them distinct from `patch_pressure`
- keep them distinct from Stage 4 manuscript hard guards

Do not:
- describe them as Stage 2 hard guards
- auto-reject solely because a signal exists
- flatten them into the same concept as `F-2` patch pressure

### Recommended next actions

1. Watch which signal codes actually occur in live runs.
2. If a future Stage 2 hard-guard redesign happens, start from these observed codes instead of copying Stage 4 text guards.
3. Keep condensed status docs explicit that Stage 2 now has:
   - blocking local patch failure
   - advisory `patch_pressure`
   - observational `patch_guard_signals`
4. Do not open a hard-guard promotion item until live evidence shows which signal codes are both stable and low-noise.

### Audit result

- runtime code change: completed
- regression hardening: completed
- documentation conclusion: Stage 2 now records narrow Arc patch observability signals, and their promotion to hard-guard status is explicitly deferred pending live evidence
