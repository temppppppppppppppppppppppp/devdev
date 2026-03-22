# Stage4 Reject Runtime Module-Split Design

Status: final
Date: 2026-03-21
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and cohesion check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: tranche ordering and rollback-risk check passed

## Decision

`Stage4InterviewRound` has crossed the point where the next ROI is a second structural split.

That split should target the reject/runtime cluster.

## Why Now

The retry cluster is now structurally settled:

- `modules/core/stage4_retry_runtime.py` owns retry-lane routing
- `modules/core/stage4_retry_runtime.py` owns `PASS_WITH_FIX` execution helpers
- owner-side retry compatibility wrappers are gone

After that settlement, the next concentrated Stage 4 runtime concern is the reject cluster:

- `_handle_reject()` (`124 LOC`)
- `_finalize_reject_result()` (`111 LOC`)
- `_build_reject_guidance_payload()`
- `_build_reject_retry_snapshot()`
- `_record_reject_round_metrics()`
- `_record_reject_attempt_artifact()`
- `_run_reject_followup_side_effects()`
- `_build_reject_logging_payload()`
- `_sync_reject_result_selection_rationale()`
- `_log_reject_session_decision()`

At the same time, `Stage4InterviewRound` still sits at `171` direct methods.

That means the next readability gain comes from moving a cohesive runtime cluster out of the owner, not from more same-file helper extraction.

## Why Reject Runtime Is Now Viable

This was not the first split candidate earlier because reject handling was still tightly entangled with:

- DB rationale sync
- episode-log append
- session-decision logging
- failure learner / adaptive manager / dashboard side effects

That entanglement still exists, but the runtime boundary is now clearer:

- the orchestration shell is already linear
- the helper chain is already explicit
- the retry cluster is no longer competing for the same structural budget

This makes a bounded reject-runtime split viable even if some sink calls still remain owner-mediated in tranche 1.

## Proposed Boundary

Create:

- `modules/core/stage4_reject_runtime.py`

Recommended shape:

```python
class Stage4RejectRuntime:
    def __init__(self, owner: "Stage4InterviewRound") -> None:
        self.owner = owner

    def handle_reject(...)
    def finalize_reject_result(...)
```

This mirrors the retry-runtime pattern:

- move the cohesive runtime concern out of the god-object file
- preserve `ctx` and agent ownership on `Stage4InterviewRound`
- allow owner callbacks for sinks that are not yet worth relocating

## First Tranche Scope

1. Add `modules/core/stage4_reject_runtime.py`
2. Move these helpers first:
   - `_handle_reject()`
   - `_build_reject_guidance_payload()`
   - `_build_reject_retry_snapshot()`
   - `_record_reject_round_metrics()`
   - `_record_reject_attempt_artifact()`
   - `_run_reject_followup_side_effects()`
3. Leave `_finalize_reject_result()` and its sink-heavy tail on the owner in tranche 1 if that keeps the split bounded
4. Keep reject logging, DB/session sink ownership mediated by the owner

## Why This Ordering

`_handle_reject()` is the cleaner first move.

Reasons:

- it is already a linear runtime shell
- most of its helper chain is reject-specific
- it centralizes reject guidance, retry snapshotting, and side-effect execution
- it can move without immediately forcing artifact-log/session-log ownership changes

`_finalize_reject_result()` should move only if tranche 1 stays clean.

## Keep On Owner For Now

In the first reject-runtime tranche, keep these concerns owner-mediated:

- `_append_episode_log()`
- `_log_round_outcome()`
- `_log_session_decision()`
- DB object ownership
- `ctx` ownership

This keeps the split bounded and prevents a logging-schema rewrite from sneaking into a readability tranche.

## Non-Goals

Do not do these in the first reject-runtime tranche:

- episode-log schema changes
- artifact-logging redesign
- DB rationale contract changes
- adaptive-manager / dashboard behavior changes
- merging reject runtime and retry runtime into a larger Stage 4 runtime abstraction

## Stop Condition

Stop and write a follow-up design note if tranche 1 requires:

- more than one new module
- changes to episode-log payload schema
- changes to DB rationale persistence contract
- moving `ctx` or DB ownership out of `Stage4InterviewRound`
- broad test rewrites outside `tests/test_stage4_interview_round.py`

## Recommended Next Step

Implement the first reject-runtime split tranche:

- add `modules/core/stage4_reject_runtime.py`
- move `_handle_reject()` and its reject-specific helper chain first
- keep `Stage4InterviewRound` as the orchestration owner
