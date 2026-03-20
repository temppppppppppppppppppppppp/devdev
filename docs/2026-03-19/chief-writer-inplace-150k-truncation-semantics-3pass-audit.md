# chief-writer-inplace-150k-truncation-semantics-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/chief-writer-inplace-150k-truncation-semantics-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 114`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Evidence Basis:
- `modules/domain/agents/chief_writer.py`
- `tests/test_chief_writer.py`
- `tests/test_pass_with_fix.py`
Scope:
- audit the runtime meaning of the `150K` manuscript truncation inside `ChiefWriter.inplace_patch()`
- audit whether `ChiefWriter.patch_with_feedback()` uses the same truncation contract
- determine whether the current behavior is a bug, an intentional prompt-budget policy, or a caller-level inconsistency
- non-goal: redesign the manuscript patch budget or change runtime code in this document

---

## Pass 1. Structure and Scope

This audit is intentionally narrow.

It covers only the manuscript-local patch paths in `ChiefWriter`:
- `inplace_patch()`
- `patch_with_feedback()`
- the meaning of the `150000` char cap
- whether current tests already fix this behavior into an explicit contract

It does not cover:
- full manuscript rewrite policy
- whether `150000` should later be tuned upward or downward
- model-specific context-window policy for all agents

Key operator question:
- when a manuscript is longer than `150K`, is `ChiefWriter` silently losing critical context in a buggy way, or intentionally compressing the prompt budget while preserving recent context?

---

## Pass 2. Evidence and Consistency

### 1. Local contract is not fail-closed

`modules/domain/agents/chief_writer.py` does not reject long manuscripts in these two paths.

Observed behavior in `inplace_patch()`:
- compute `_orig_len = len(original_manuscript or "")`
- if `_orig_len > 150000`, log `[TRUNCATION] chief_writer.inplace_patch ...`
- still build the prompt
- use `smart_truncate(original_manuscript, max_chars=150000, head_chars=20000)`

Observed behavior in `patch_with_feedback()`:
- same `_orig_len > 150000` warning pattern
- same `smart_truncate(..., max_chars=150000, head_chars=20000)` insertion into the patch section

Meaning:
- this is not "oversize manuscript -> fail"
- this is "oversize manuscript -> bounded prompt budget with warning"

Conclusion:
- the runtime contract is bounded continuation, not fail-closed rejection

### 2. Tail-preserving behavior is part of the live contract

The key question is not only that truncation exists.
The key question is whether the current truncation still preserves late manuscript context.

Live code evidence:
- both paths call `smart_truncate(..., max_chars=150000, head_chars=20000)`
- this is the same tail-preserving helper used in other cleaned-up prompt paths

New direct regression coverage:
- `tests/test_chief_writer.py::test_inplace_patch_truncation_preserves_recent_tail_context`
- `tests/test_chief_writer.py::test_patch_with_feedback_truncation_preserves_recent_tail_context`

What these tests now fix:
- manuscript length over `150K`
- warning log still occurs
- the tail marker survives inside:
  - the direct `inplace_patch()` prompt
  - the `patch_with_feedback()` forwarded feedback block

Conclusion:
- the important contract is not merely "logs `[TRUNCATION]`"
- the important contract is "bounded prompt budget while preserving recent context"

### 3. Prior test coverage was incomplete but not contradictory

Existing evidence before this audit:
- `tests/test_pass_with_fix.py` already had a generic warning-focused truncation test
- multiple `ChiefWriter` tests already covered extraction, end-marker stripping, structural patching, and fix-pack behavior

Gap:
- there was no direct regression proving that oversized manuscript prompts still retain the manuscript tail in the live prompt surface

This audit closes that gap with direct behavioral tests instead of only log simulation.

Conclusion:
- the risk here was mostly undocumented semantics, not a demonstrated runtime contradiction

### 4. Operational meaning

`ChiefWriter` manuscript-local patching sits between two bad extremes:
- sending the full oversized manuscript without a bound
- fail-closing the whole local patch path on long input

Current behavior chooses a middle path:
- warn
- cap
- preserve head and tail
- continue local patch generation

That makes sense for this layer:
- local patching still needs recent manuscript context
- it should remain cheaper and more bounded than a full rewrite path

Conclusion:
- the `150K` cap behaves like a prompt-budget policy boundary, not like a bug-class truncation defect

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. `ChiefWriter.inplace_patch()` `150K` truncation is intentional and should not currently be treated as a bug.

2. `ChiefWriter.patch_with_feedback()` uses the same effective truncation contract and is also coherent.

3. The relevant invariant is now:
- warn on oversize manuscript
- cap prompt input at `150K`
- preserve recent tail context
- continue the local patch path

### Safe operating rule from this audit

Do:
- keep the current `150K` cap for `ChiefWriter` local patch paths
- keep tail-preserving truncation as the required behavior
- keep the new direct regression coverage

Do not:
- reinterpret `[TRUNCATION]` as meaning the path should fail-closed
- remove the tail-preserving requirement while keeping the warning log
- change the `150K` cap casually without caller-aware review

### Recommended next actions

1. Treat `ChiefWriter` `150K` truncation as a policy-boundary item, not as a low-risk truncation cleanup candidate.
2. If the cap is revisited later, do it as an explicit context-budget rewrite decision.
3. Keep future OPUS-style summaries from collapsing this into the false statement "long manuscript input is simply cut."

### Audit result

- runtime code change: not needed
- regression hardening: completed
- documentation conclusion: `ChiefWriter` `150K` manuscript truncation is intentional bounded prompt-budget behavior and should stay unless policy rewrite justifies a change
