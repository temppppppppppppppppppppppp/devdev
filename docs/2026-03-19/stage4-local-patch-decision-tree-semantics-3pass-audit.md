# stage4-local-patch-decision-tree-semantics-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/stage4-local-patch-decision-tree-semantics-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 114`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Evidence Basis:
- `modules/core/stage4_interview_round.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_pass_with_fix.py`
Scope:
- audit the retry-round manuscript repair decision tree in `Stage4InterviewRound._generate_candidates()`
- audit the `PASS_WITH_FIX` local patch loop semantics in `Stage4InterviewRound._execute_pass_with_fix_loop()`
- determine whether current routing is a bug, an intentional policy boundary, or a caller/test inconsistency
- non-goal: redesign Stage 4 repair strategy budgets or change runtime code in this document

---

## Pass 1. Structure and Scope

This audit is intentionally narrow.

It covers only the Stage 4 manuscript repair routing:
- round 0 ensemble generation
- retry-round `inplace -> patch -> rewrite` routing
- `post_select_conflict` force-patch behavior
- `PASS_WITH_FIX` local patch loop eligibility

It does not cover:
- Stage 2 Arc repair routing
- Stage 3 Blueprint repair routing
- whether current strategy budgets should later be retuned

Key operator question:
- when Stage 4 needs a manuscript repair, how does Director judgment (`fix_scope`, `reject_bucket`, `fix_pack`) map into the runtime lanes `inplace_patch`, `patch_with_feedback`, or `regenerate_with_feedback`, and is that contract coherent enough to keep?

---

## Pass 2. Evidence and Consistency

### 1. Round 0 is always ensemble generation

`_generate_candidates()` is explicit here:
- `round_num == 0` always uses `chief_writer.generate_ensemble(**_common_writer_kwargs)`
- no local patch routing is attempted on the first round

Meaning:
- Stage 4 starts with full candidate generation
- repair routing only begins on retry rounds

Conclusion:
- any description that implies Stage 4 can start directly in local patch mode is inaccurate

### 2. Retry routing is policy-driven, not score-driven

On retry rounds, `_generate_candidates()` now uses an explicit local-fix contract.

Observed live rules:
- `_force_patch` when:
  - patch mode enabled
  - previous manuscript exists
  - `reject_bucket == "post_select_conflict"`
  - `fix_scope != "full"`
  - `round_num <= 1`
- `_use_inplace` only when:
  - patch mode enabled
  - previous manuscript exists
  - not `_force_patch`
  - `fix_scope == "inplace"`
  - `fix_pack` contract is ready
- `_use_patch` when:
  - `_force_patch`
  - or previous manuscript exists and `fix_scope in {"inplace", "partial"}`
  - or `post_select_conflict` retry with non-full scope

Operational meaning:
- Stage 4 does not trust score alone for local patch eligibility anymore
- Director judgment does not directly "pick one of three code paths"
- instead, Director-emitted contract fields such as `fix_scope`, `reject_bucket`, and `fix_pack` govern the runtime lane routing

Supporting evidence:
- `tests/test_stage4_interview_round.py::test_retry_inplace_requires_fix_pack_and_routes_to_patch`
- `tests/test_pass_with_fix.py::TestFixScopeRouting::*`
- `tests/test_pass_with_fix.py::TestPFImprovements::test_pf1_fix_scope_missing_high_score`

Conclusion:
- the important boundary here is explicit local-repair contract, not numeric score threshold fallback

### 3. Inplace is bounded and fail-soft

If `inplace_patch()` is chosen, Stage 4 still applies acceptance guards before treating it as usable.

Observed live rules:
- empty or blank manuscript result -> patch fallback
- patched manuscript shorter than `patch_mode.min_patched_length` -> patch fallback
- patched manuscript shorter than `inplace_min_preserve_ratio` of original -> patch fallback

Meaning:
- Stage 4 allows local patch attempts
- but does not silently accept obviously collapsed patch output

Supporting evidence:
- `tests/test_stage4_interview_round.py::test_reject_retry_shrunk_inplace_patch_falls_back_to_patch`
- `tests/test_pass_with_fix.py::test_pf3_pass_with_fix_shrunk_patch_becomes_reject`

Conclusion:
- Stage 4 local patching is intentionally fail-soft into the next broader repair layer

### 4. Patch is the preferred bounded fallback, rewrite is last

If `inplace_patch()` is unavailable or rejected, Stage 4 moves to `patch_with_feedback()`.

If that also fails, Stage 4 falls back to `regenerate_with_feedback()`.

Observed live rules:
- patch failure sets `patch_fallback=True`
- rewrite strategy budget is:
  - `reduced` for `quality_issue` / `constraint_violation` with non-full scope
  - `full` otherwise

Supporting evidence:
- `tests/test_stage4_interview_round.py::test_patch_fallback_records_method_ensemble`
- `tests/test_stage4_interview_round.py::test_post_select_conflict_prefers_patch_before_inplace`
- `tests/test_stage4_interview_round.py::test_post_select_conflict_force_patch_only_once`

Conclusion:
- Stage 4 routing is intentionally layered:
  - local patch
  - bounded single-strategy patch regenerate
  - full regeneration

### 5. PASS_WITH_FIX loop uses the same explicit local contract

`_execute_pass_with_fix_loop()` no longer applies the old "high score can still imply local patch" idea.

Observed live rules:
- first enforce `PASS_WITH_FIX` contract
- if `fix_scope != "inplace"` or `fix_pack` is not ready:
  - emit Lane3 Gate notice
  - abort the loop
  - hand back control to retry semantics
- repeated `PASS_WITH_FIX` re-audits must also carry valid local contract if they want another inplace pass

This audit also exposed stale tests:
- helper-level `PASS_WITH_FIX` fixtures in `tests/test_pass_with_fix.py` were still missing `fix_pack`
- one test still assumed missing `fix_scope` plus high score could fall back to inplace

Those tests were updated to match live semantics:
- default helper now carries a valid local `fix_pack`
- missing `fix_scope` now expects `REJECT`, not inplace fallback
- repeated `PASS_WITH_FIX` re-audit fixtures now carry valid local `fix_pack`

Conclusion:
- the runtime contract is coherent
- the inconsistency risk was mainly documentary and test drift

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. Stage 4 manuscript repair routing is intentional and should not currently be treated as a bug-class branch mess.

2. The current policy boundary is:
- first round: ensemble only
- retry round: Director contract fields are mapped into runtime repair lanes
- explicit local contract decides inplace eligibility
- if local patch is unusable: bounded patch regenerate
- if patch is unusable: regenerate

3. `PASS_WITH_FIX` loop should now be read as:
- explicit local repair only
- no score-only inplace fallback
- valid `fix_pack` required throughout repeated local re-audits

### Safe operating rule from this audit

Do:
- keep the current retry routing hierarchy
- keep `post_select_conflict` as a bounded force-patch case
- keep `fix_pack` as the required local-repair contract for `PASS_WITH_FIX`
- keep the refreshed regression coverage in `tests/test_stage4_interview_round.py` and `tests/test_pass_with_fix.py`

Do not:
- describe Stage 4 as if score alone selects local patch mode
- collapse `inplace`, `patch`, and `rewrite` into one vague "retry repair" sentence
- remove `fix_pack` gating without an explicit policy rewrite

### Recommended next actions

1. Treat Stage 4 local manuscript repair semantics as a policy-boundary item, not a low-risk cleanup candidate.
2. If repair routing is revisited later, redesign it deliberately as a Stage 4 repair-policy rewrite.
3. Keep OPUS-style condensed summaries from erasing the difference between:
   - explicit local repair
   - bounded patch rewrite
   - full regeneration

### Audit result

- runtime code change: not needed
- regression hardening: completed via stale-test alignment
- documentation conclusion: Stage 4 manuscript local patch routing is coherent and should stay unless policy rewrite justifies a change
