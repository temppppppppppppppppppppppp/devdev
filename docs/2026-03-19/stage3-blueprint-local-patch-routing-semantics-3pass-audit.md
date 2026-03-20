# stage3-blueprint-local-patch-routing-semantics-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/stage3-blueprint-local-patch-routing-semantics-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 115`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/blueprint-inplace-30kb-fallback-consistency-3pass-audit.md`
Evidence Basis:
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `tests/test_blueprint_patch_mode.py`
- `tests/test_inplace_reliability.py`
- `tests/test_v75b_escalation.py`
Scope:
- audit the Stage 3 Blueprint local patch routing semantics inside `ThreePhaseBlueprintGenerator.generate()`
- determine how `fix_scope`, score fallback, same-attempt full rewrite fallback, and `F-2` patch pressure currently behave
- lock the current behavior with direct regression coverage where it was still missing
- non-goal: redesign Blueprint patch policy or change runtime thresholds in this document

---

## Pass 1. Structure and Scope

This audit is intentionally bounded.

It covers only the Stage 3 Blueprint repair flow:
- initial REJECT retry routing
- `PASS_WITH_FIX` local patch loop routing
- relation between `_inplace_patch_blueprint()` failure and same-attempt/full-retry regenerate paths
- whether `F-2` high patch pressure is warning-only or a hard gate

It does not cover:
- the `30KB` local guard itself beyond how the generator reacts to it
- Stage 4 manuscript local patch policy
- whether the current thresholds should later be tightened

Key operator question:
- when Stage 3 decides Blueprint needs repair, what exactly routes to inplace patch, partial regenerate, or full regenerate, and does high patch pressure block adoption?

---

## Pass 2. Evidence and Consistency

### 1. Initial retry routing already has a three-way contract

Live code in `modules/domain/agents/three_phase_blueprint_generator.py` uses three distinct repair routes after a rejected Blueprint is carried into the next retry:
- `fix_scope == "inplace"` or missing `fix_scope` with score `>= 60`:
  enter `_inplace_patch_blueprint()`
- `fix_scope == "partial"`:
  skip inplace and run `generate_ensemble(..., single_strategy=<selected strategy>)`
- otherwise:
  run normal full ensemble regenerate

Existing regression coverage already fixes most of this:
- `tests/test_blueprint_patch_mode.py::test_retry1_with_high_score_enters_inplace`
- `tests/test_blueprint_patch_mode.py::test_low_score_skips_inplace`
- `tests/test_blueprint_patch_mode.py::test_score_50_to_59_uses_ensemble_not_inplace`
- `tests/test_blueprint_patch_mode.py::test_score_60_enters_inplace_boundary`

Meaning:
- Stage 3 is not using one vague "retry again" path
- it already has a live decision tree

### 2. Inplace failure is fail-closed locally but fail-soft at generator level

`_inplace_patch_blueprint()` can return `None` for local repair failure, including the already-audited `30KB` refusal case.

Generator behavior is still coherent:
- in the initial retry routing path, inplace failure immediately falls back to full rewrite in the same retry attempt
- in the later `PASS_WITH_FIX` loop, inplace failure breaks local repair and converts back to `REJECT`, which then re-enters the normal generate retry loop

Direct regression already existed for the first case:
- `tests/test_blueprint_patch_mode.py::test_inplace_failure_falls_back_to_full_rewrite_in_same_attempt`

Supporting guard evidence:
- `tests/test_inplace_reliability.py::test_blueprint_over_30kb_returns_none`

Conclusion:
- local Blueprint patch is fail-closed
- the Stage 3 caller is still fail-soft and bounded

### 3. `PASS_WITH_FIX` does not mean "always keep patching locally"

Inside the Stage 3 validation loop, `PASS_WITH_FIX` is routed by `fix_scope`.

Observed behavior:
- missing `fix_scope` still uses score fallback
- `fix_scope in ("partial", "full")` does not enter inplace patch
- instead it breaks out of the local patch loop, marks the attempt as unresolved, and re-enters the generate retry loop
- only local-scope cases continue into `_inplace_patch_blueprint()`

Before this audit, the explicit `partial/full` regenerate branches were visible in code but not fully fixed by regression.

New regression:
- `tests/test_blueprint_patch_mode.py::test_pass_with_fix_partial_routes_to_single_strategy_regenerate`
- `tests/test_blueprint_patch_mode.py::test_pass_with_fix_full_routes_to_full_regenerate`

This test now proves:
- `PASS_WITH_FIX + fix_scope="partial"` does not call `_inplace_patch_blueprint()`
- the next retry calls `generate_ensemble()` with `single_strategy=<selected strategy>`
- the flow can still recover to final `PASS`
- `PASS_WITH_FIX + fix_scope="full"` also skips `_inplace_patch_blueprint()`
- the next retry re-enters the full regenerate lane without `single_strategy`

Conclusion:
- Stage 3 local repair is contract-driven, not just score-driven
- `partial` and `full` are both real regenerate lanes, not documentary noise

### 4. Stage 3 `F-2` patch pressure is warning-only, not a hard gate

The `PASS_WITH_FIX` loop computes Blueprint patch change ratio:
- `calc_patch_change_ratio(_orig_j, _patch_j)`
- compares it with `patch_mode.inplace_max_change_ratio`
- if exceeded, logs `[F-2] InPlace Blueprint 변경 비율 ...`

Important negative evidence:
- there is no `break`
- there is no forced downgrade
- there is no forced `REJECT` solely because `F-2` fired

New direct regression:
- `tests/test_blueprint_patch_mode.py::test_pass_with_fix_high_change_ratio_is_warning_only`

This test now fixes:
- mocked `change_ratio = 0.75`
- re-validation returns `PASS`
- final pipeline verdict still becomes `PASS`
- the `[F-2]` warning is emitted

Conclusion:
- Stage 3 `F-2` is advisory-only at this layer
- this matches the live control flow more closely than OPUS-style compressed wording

### 5. Stage 4 hard-guard assumptions do not transfer here

Stage 4 manuscript local patching has explicit hard guards such as minimum patched length and preserve-ratio checks.

Stage 3 Blueprint local patching does not currently implement the same safety stack.

Its active boundaries are different:
- `30KB` local fail-closed guard
- `fix_scope` / score routing
- same-attempt or next-retry regenerate fallback
- `F-2` warning-only patch pressure

Conclusion:
- treating Stage 3 as if it had the same hard guards as Stage 4 would be inaccurate

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. Stage 3 Blueprint local patching already has a coherent routing policy and should not be described as one generic "patch mode".

2. The current invariant is:
- local oversized/failed inplace repair returns `None`
- Stage 3 generator falls back coherently
- `partial` is a real single-strategy regenerate lane
- `F-2` high patch pressure is warning-only, not blocking

3. Any summary that says "Stage 3 high patch pressure blocks Blueprint local patch" is incorrect.

### Safe operating rule from this audit

Do:
- keep Blueprint `30KB` fail-closed guard
- keep `partial` as a distinct regenerate lane
- keep `F-2` as advisory-only unless a deliberate policy rewrite changes it
- keep the new direct regressions for `partial/full` routing and `F-2` warning-only semantics

Do not:
- collapse `partial` and `full` into the same undocumented retry sentence
- assume Stage 4 hard guards exist on Stage 3 Blueprint patching
- silently convert Stage 3 `F-2` into a blocking gate without a policy decision

### Recommended next actions

1. Treat Stage 3 Blueprint local patch routing as its own policy-boundary item.
2. When summarizing Blueprint repair, separate:
   - local `30KB` guard
   - Stage 3 generator routing
   - Stage 4 B-Light caller escalation
3. If stricter Blueprint patch gating is ever desired, add it explicitly rather than borrowing Stage 4 semantics by assumption.

### Audit result

- runtime code change: not needed
- regression hardening: completed
- documentation conclusion: Stage 3 Blueprint local patching uses contract-driven routing, same-attempt/next-retry regenerate fallback, and advisory-only `F-2`
