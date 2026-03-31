# EP8 Artifact-vs-Code Lane 4 Master Synthesis

Date: 2026-03-30
Status: draft-bounded-partial-evidence
Lane: 4 (master synthesis)
Track: system
Terminal: 4
Baseline Commit: `92ba1cf7`
Master Order: `docs/2026-03-30/0_1-ep8-artifact-vs-code-parallel-master-order.md`
Source Drafts:
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane1-artifact-truth-draft.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane2-code-contract-draft.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane3-persistence-timeline-draft.md`

## 1. Coverage

This synthesis merged:

- lane 1 artifact-truth findings
- lane 2 code-contract findings
- lane 3 persistence timeline findings
- direct spot-checks against:
  - `projects/0_1/plans/blueprints/blueprint_0008.txt`
  - `projects/0_1/logs/artifacts/stage4/ep_0008/attempt_05/selected_before_fix__C_asp_correction.txt`
  - `projects/0_1/drafts/ep_0007.txt`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_retry_runtime.py`
  - `modules/core/stage4_reject_runtime.py`
  - `modules/core/project_manager.py`
  - `modules/core/db_manager.py`

## 2. Findings

### S-1. Master classification is `mixed`

The evidence does not support a single-axis answer.

- attempts 1-4 are dominated by a code-stage contract seam:
  - `PASS` is escalated to `PASS_WITH_FIX`
  - no usable `fix_pack.patch_targets` exists
  - Lane 3 gate then fail-closes to `REJECT`
- attempt 5 proves artifact-stage defects are also real blockers:
  - blueprint carries `18년 전 과거의 기억`
  - blueprint carries `남은 5억 원`
  - those defects survive into the selected manuscript and trigger post-select failure

### S-2. Primary current acceptance blocker is artifact-stage

For the current EP8 run, the most direct blocker to a successful accepted manuscript is the blueprint itself.

Confirmed blueprint-origin defects:

1. `18년 전 과거의 기억`
   - wrong for a protagonist currently living in 2006 with memories originating from 2024
   - should be framed as future-memory or prior-life-memory language
2. `남은 5억 원`
   - conflicts with EP7-established residual cash `4억 7,100만 원`

Why this is the current primary blocker:

- attempt 5 already escaped the earlier empty-patch loop
- Director produced a valid `PASS_WITH_FIX`
- the run still fell to `REJECT` because the artifact truth was wrong

### S-3. Primary systemic blocker is code-stage

The strongest systemic defect is the Stage 4 contract seam that burns retry budget before the artifact defects are surfaced cleanly.

Confirmed code-stage defects:

1. strong-advisory escalation can manufacture `PASS_WITH_FIX` without a viable fix pack
2. that impossible state is then rejected by the PASS_WITH_FIX contract gate
3. post-select conflict downgrade leaks scope and can preserve stale `inplace` retry intent when the runtime now needs `full`

This does not mean the code caused attempt 5's factual contradiction.
It means the code wasted attempts 1-4 and can recur on future episodes.

### S-4. Why this is not artifact-first only

It is not artifact-first only because:

- attempts 1-4 never reached a clean artifact adjudication path
- they were short-circuited by a contract mismatch in the retry/gate seam
- the code defect is real, reproducible, and not specific to EP8 text

### S-5. Why this is not code-first only

It is not code-first only because:

- attempt 5 reaches a valid local-fixable manuscript state
- the final rejection still occurs on real content contradictions
- fixing only the code would still leave the current EP8 blueprint unfit for acceptance

## 3. Non-Issues

- opening continuity is not a hard defect; the EP7 ending and EP8 opening align
- dialogue-ratio complaints are style watchlist items, not hard blockers
- attempt 6 is incomplete and cannot be used as closure evidence
- encoding corruption is not in evidence; the authoritative files decode as UTF-8

## 4. Verdict

`mixed`

Primary blocker:
- artifact-stage EP8 blueprint truth

Secondary blocker:
- Stage 4 advisory-escalation / retry-lane contract seam

Immediate next action order:

1. blueprint authoritative repair
2. Stage 4 contract hardening
3. bounded EP8 rerun after both lanes land

## 5. Stop

read-only lane complete; no files mutated
