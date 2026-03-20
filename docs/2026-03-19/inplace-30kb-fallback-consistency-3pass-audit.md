# inplace-30kb-fallback-consistency-3pass-audit

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/inplace-30kb-fallback-consistency-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; `git status --short` shows 100+ modified/deleted/untracked entries across docs, desktop, modules, tests`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-18/OPUS/ssot/s7-rol-static-improvement.md`
Evidence Basis:
- `modules/domain/agents/four_phase_arc_generator.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_finalizer.py`
- `tests/test_inplace_reliability.py`
- `tests/test_pass_with_fix.py`
- `tests/test_stage2_preflight_helpers.py`
Scope:
- audit the runtime consistency of `_inplace_patch_arc()` `30KB` fail-closed behavior
- determine whether the current behavior is a bug, an intentional guardrail, or a caller-level inconsistency
- clarify where OPUS wording over-compressed the real runtime flow
- non-goal: redesign patch policy or modify code in this document

---

## Pass 1. Structure and Scope

This audit is intentionally narrow.

It covers only the Arc inplace patch path:
- local contract of `_inplace_patch_arc()`
- Stage 2 caller behavior when `_inplace_patch_arc()` returns `None`
- test coverage that fixes current behavior into contract

It does not cover:
- blueprint inplace patch policy
- Stage 4 manuscript inplace patch policy
- whether the `30KB` number itself should later be tuned

Key operator question:
- when Arc inplace patch refuses oversized input, is the system behaving consistently enough to trust the current design?

---

## Pass 2. Evidence and Consistency

### 1. Local function contract is clear and intentional

`modules/domain/agents/four_phase_arc_generator.py` defines `_inplace_patch_arc()` as a strict local-fix path.

Observed behavior:
- serialize `original_arc` to JSON
- if serialized JSON is over `30000` chars, log warning and return `None`
- comment explicitly says the reason is to avoid truncated or broken JSON and fall back to a broader rewrite path

Meaning:
- this is not a random failure
- this is an intentional fail-closed guardrail for oversized inplace patch inputs

Supporting test contract:
- `tests/test_inplace_reliability.py`
  - oversized Arc JSON returns `None`
  - under-threshold Arc proceeds

Conclusion:
- the `30KB` guard itself is coherent and intentional

### 2. Stage 2 preflight uses same-attempt fallback

`modules/core/stage2_preflight.py` handles `_inplace_patch_arc()` failure as an immediate local fallback trigger.

Observed flow:
- if `_use_inplace` is true, preflight tries `_inplace_patch_arc()`
- if the result is falsy, it logs `Arc InPlace 실패 -> Patch 폴백`
- the same call path then enters `patch_arc_with_feedback()` when `_use_patch` is true

Important detail:
- for `fix_scope="inplace"`, `_use_inplace` and `_use_patch` can both be true
- therefore `inplace` refusal in preflight does not necessarily mean overall failure
- it often means immediate same-attempt patch-mode fallback

Operational meaning:
- preflight treats inplace as one repair tactic inside the generation path
- if that tactic refuses the input, the broader patch path may still run in the same attempt

Consistency assessment:
- coherent
- intentionally fail-closed at the local function level, but fail-soft at the caller level

### 3. Stage 2 finalizer uses deferred fallback through retry

`modules/core/stage2_finalizer.py` behaves differently.

Observed flow:
- PASS_WITH_FIX enters a bounded inplace patch loop
- if `_inplace_patch_arc()` returns `None`, finalizer does not call patch mode immediately in the same frame
- instead it breaks the loop, converts the outcome to `REJECT`, preserves patch-related fields, and returns `action=retry`

Supporting test contract:
- `tests/test_pass_with_fix.py::test_finalizer_pass_with_fix_patch_failure_rejects`
  - `patch_arc_return=None` is expected to produce `action="retry"`

Important distinction:
- this is not "drop the patch path forever"
- this is "stop local finalizer repair and hand control back to the outer retry/generation loop"

Why this still makes structural sense:
- finalizer is not the main generation phase
- it is an adjudication-and-local-repair layer
- once local repair fails, the code intentionally escalates back to the broader retry pipeline

Consistency assessment:
- different from preflight
- but not contradictory once the layer boundary is recognized

### 4. The real inconsistency is mostly documentary, not runtime

The OPUS wording around repair flow compresses the system too aggressively.

Example pattern found in OPUS S7:
- `repair_scope -> inplace 시도 -> 실패 시 structural -> 실패 시 full 재생성`

Why this is misleading:
- it reads like one universal same-frame fallback chain
- live code actually splits behavior by layer
  - preflight: immediate same-attempt patch fallback
  - finalizer: REJECT/retry, with fallback deferred to the outer retry loop

Therefore:
- the confusion is real
- but it is caused more by over-compressed document wording than by a proven runtime bug in the current code

### 5. Preflight direct regression gap is now closed

Current test coverage was previously asymmetrical.

Strongly fixed by tests:
- `_inplace_patch_arc()` over-30KB returns `None`
- finalizer turns inplace failure into retry
- preflight now explicitly proves same-attempt fallback
  - when `_inplace_patch_arc()` returns `None`
  - and `_use_patch` is true
  - `patch_arc_with_feedback()` is called in the same attempt
  - broad `generate()` is not called on that path

Supporting regression:
- `tests/test_stage2_preflight.py`

Updated assessment:
- the earlier ambiguity was a coverage gap
- that gap is now closed for the intended preflight fallback contract

---

## Pass 3. Execution and Readability

### Audit conclusion

1. `_inplace_patch_arc()` `30KB` fail-closed behavior is intentional and should not currently be treated as a bug.
2. Caller behavior is not uniform, but the difference is explainable by stage responsibility.
3. The biggest practical problem is documentation ambiguity plus a small regression-coverage gap, not an immediately proven runtime defect.

### What this means operationally

Do not treat this audit as justification to remove the `30KB` guard.

Current best interpretation:
- keep the local guard
- clarify caller semantics
- add missing regression coverage before considering any policy change

### Recommended next actions

1. Optionally add one small operator note or doc update:
   - `inplace fail -> immediate patch fallback` is only true for preflight-style generation flow
   - finalizer uses `REJECT -> retry` escalation instead of same-frame patch fallback

2. Do not change the `30KB` limit itself until the caller contracts are explicitly locked.

### Final verdict

Verdict: `INTENTIONAL-GUARD / CALLER-SPLIT-SEMANTICS / DOC-AMBIGUITY`

Short form:
- guard is intentional
- live runtime behavior is defensible
- OPUS wording was sloppy
- the regression gap is now closed
- the next high-ROI step is documentation hardening, not immediate policy rewrite

---

## Confidence Gate

Estimated confidence for this bounded audit purpose: **97%**

Why this clears the gate:
- all live call sites were checked
- the local function contract and caller contracts were compared directly
- targeted tests were re-run for the core contract surfaces
- the conclusion is bounded and does not overclaim a redesign decision
