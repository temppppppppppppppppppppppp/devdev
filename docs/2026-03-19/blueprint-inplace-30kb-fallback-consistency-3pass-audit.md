# blueprint-inplace-30kb-fallback-consistency-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/blueprint-inplace-30kb-fallback-consistency-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 112`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/inplace-30kb-fallback-consistency-3pass-audit.md`
Evidence Basis:
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/stage4_orchestrator.py`
- `tests/test_blueprint_patch_mode.py`
- `tests/test_inplace_reliability.py`
- `tests/test_v75b_escalation.py`
Scope:
- audit the runtime consistency of `_inplace_patch_blueprint()` `30KB` fail-closed behavior
- determine whether the current behavior is a bug, an intentional guardrail, or a caller-level inconsistency
- clarify Stage 3 and Stage 4 caller behavior when Blueprint inplace patch returns `None`
- non-goal: redesign Blueprint patch policy or change code in this document

---

## Pass 1. Structure and Scope

This audit is intentionally narrow.

It covers only the Blueprint inplace patch path:
- local contract of `_inplace_patch_blueprint()`
- Stage 3 caller behavior in `ThreePhaseBlueprintGenerator.generate()`
- Stage 4 caller behavior in `Stage4Orchestrator` B-Light escalation
- regression coverage that fixes current behavior into contract

It does not cover:
- Arc inplace patch policy
- manuscript inplace patch policy
- whether the `30KB` number itself should later be tuned

Key operator question:
- when Blueprint inplace patch refuses oversized input, does the system fall back coherently enough to keep the current design?

---

## Pass 2. Evidence and Consistency

### 1. Local function contract is clear and intentional

`modules/domain/agents/three_phase_blueprint_generator.py` defines `_inplace_patch_blueprint()` as a strict local-fix path.

Observed behavior:
- serialize `original_blueprint` to JSON
- if serialized JSON is over `30000` chars, log warning and return `None`
- inline comment explicitly says the reason is to avoid broken/truncated JSON and fall back to a broader rewrite path

Meaning:
- this is not a random failure
- this is an intentional fail-closed guardrail for oversized inplace patch inputs

Supporting test contract:
- `tests/test_inplace_reliability.py::test_blueprint_over_30kb_returns_none`
- under-threshold Blueprint proceeds normally

Conclusion:
- the `30KB` guard itself is coherent and intentional

### 2. Stage 3 uses same-attempt full rewrite fallback

`ThreePhaseBlueprintGenerator.generate()` treats inplace patch as one repair tactic inside the current retry attempt.

Observed flow:
- retry `0` can produce a best Blueprint and REJECT with score `>= 60`
- retry `1` then enters `_inplace_patch_blueprint()`
- if `_inplace_patch_blueprint()` returns `None`, the same code path immediately calls `ensemble.generate_ensemble()` for a full rewrite fallback

Operational meaning:
- local inplace repair is fail-closed
- the Stage 3 caller is fail-soft inside the same attempt

Direct regression evidence:
- `tests/test_blueprint_patch_mode.py::test_inplace_failure_falls_back_to_full_rewrite_in_same_attempt`
- this test fixes the final available retry case:
  - `max_retries=1`
  - retry `0`: generate + reject
  - retry `1`: inplace returns `None`
  - same retry `1`: full rewrite fallback runs and PASSes

Conclusion:
- Stage 3 caller behavior is coherent
- `30KB` refusal does not mean Stage 3 immediately fails overall

### 3. Stage 4 uses a different but still coherent fallback layer

Stage 4 does not reuse the exact same fallback frame as Stage 3.

Observed evidence from `tests/test_v75b_escalation.py`:
- B-Light success case: `_inplace_patch_blueprint()` succeeds, `_regenerate_blueprint()` is not called
- B-Light failure case: `_inplace_patch_blueprint()` returns `None`, then `_regenerate_blueprint()` is called once
- if both fail, the original Blueprint is kept and the system surfaces the fallback failure

Operational meaning:
- Stage 4 does not do "same-frame inplace then ensemble full rewrite inside the generator loop"
- instead it does "one local inplace attempt, then one higher-level Blueprint regeneration attempt"

This difference makes sense:
- Stage 3 is the native Blueprint generation layer
- Stage 4 is using Blueprint repair as an escalation tactic during manuscript production

Conclusion:
- caller behavior differs by layer
- but the difference is structural, not contradictory

### 4. The real inconsistency risk was documentary, not runtime

As with Arc inplace patching, the dangerous mistake is to collapse all callers into one sentence.

Accurate live summary is:
- local Blueprint inplace patch over `30KB` is intentionally blocked
- Stage 3 caller falls back to full rewrite in the same attempt
- Stage 4 caller falls back to one bounded Blueprint regeneration attempt

Conclusion:
- OPUS-style compressed wording would likely mislead here too
- runtime behavior is more coherent than a one-line summary suggests

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. `_inplace_patch_blueprint()` `30KB` fail-closed behavior is intentional and should not currently be treated as a bug.

2. Stage 3 caller behavior is acceptable.
The local inplace failure falls back to full rewrite in the same attempt, which is the right place for Blueprint regeneration.

3. Stage 4 caller behavior is also acceptable.
It uses a more bounded escalation shape, but still preserves a clear fallback path.

### Safe operating rule from this audit

Do:
- keep the `30KB` guard
- keep Stage 3 same-attempt full rewrite fallback
- keep Stage 4 one-shot Blueprint regeneration fallback
- preserve the new direct regression test for Stage 3 fallback

Do not:
- remove the `30KB` guard based on a mistaken belief that caller fallback is missing
- collapse Stage 3 and Stage 4 fallback semantics into one undocumented sentence

### Recommended next actions

1. Treat Blueprint `30KB` guard as the same class of boundary as Arc `30KB` guard: local fail-closed, caller-dependent fail-soft.
2. Keep caller contracts documented per layer:
   - Stage 3 generation loop
   - Stage 4 B-Light escalation
3. If the limit is ever revisited, do it only after caller contracts stay locked by tests.

### Audit result

- runtime code change: not needed
- regression hardening: completed
- documentation conclusion: Blueprint inplace `30KB` behavior is intentional and caller-consistent
