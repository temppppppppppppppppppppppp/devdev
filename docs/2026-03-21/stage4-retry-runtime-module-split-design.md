# Stage4 Retry Runtime Module-Split Design

Status: final
Date: 2026-03-21
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and cohesion check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: tranche ordering and rollback-risk check passed

## Decision

`Stage4InterviewRound` has crossed the point where more same-file leaf extraction is lower ROI than a bounded runtime module split.

The split is justified now.

## Why Now

The remaining `100+` shells in `modules/core/stage4_interview_round.py` are no longer random leftovers. They form two concentrated runtime clusters:

- retry/repair cluster
  - `_execute_pass_with_fix_loop()` (`156 LOC`)
  - `_generate_candidates()` (`101 LOC`)
  - `_prepare_pass_with_fix_iteration_gate()`
  - `_run_pass_with_fix_patch_attempt()`
  - `_run_pass_with_fix_patch_guards()`
  - `_capture_pass_with_fix_patch_delta()`
  - `_run_pass_with_fix_reaudit()`
  - `_apply_pass_with_fix_reaudit_verdict()`
  - `_finalize_pass_with_fix_loop_outcome()`
  - `_resolve_retry_lane_routing()`
  - `_run_inplace_retry_lane()`
  - `_run_patch_or_rewrite_retry_lane()`
  - `_run_asp_correction()`
  - `_apply_asp_candidate_replacement()`

- reject/finalization cluster
  - `_handle_reject()` (`124 LOC`)
  - `_finalize_reject_result()` (`111 LOC`)
  - `_build_reject_guidance_payload()`
  - `_build_reject_retry_snapshot()`
  - `_record_reject_round_metrics()`
  - `_record_reject_attempt_artifact()`
  - `_run_reject_followup_side_effects()`
  - `_sync_reject_result_selection_rationale()`
  - `_log_reject_session_decision()`

At the same time, `Stage4InterviewRound` now sits at `183` direct methods. That means same-file helper extraction is reducing per-function size while increasing class-level scan radius.

This is the exact threshold where a new file buys more readability than another wrapper helper.

## First Boundary To Move

Split the retry/repair cluster first.

Create:

- `modules/core/stage4_retry_runtime.py`

This new module should own:

- retry-lane routing
- retry candidate generation execution
- `PASS_WITH_FIX` patch/re-audit loop execution
- ASP correction replacement

`Stage4InterviewRound` should keep:

- high-level round orchestration
- `ctx` ownership
- Director/chief-writer object ownership
- final result packaging

## Why Retry First

Retry/repair is the cleaner split boundary.

Reasons:

- the cluster is already behaviorally cohesive
- its helper chain is dense and mostly internal to one runtime concern
- it is the largest remaining Stage 4 shell surface
- it can move without dragging DB/session logging sinks into the first tranche

Reject handling is still more entangled with:

- DB rationale sync
- episode-log sink invocation
- session decision logging

That makes reject runtime a worse first split than retry runtime.

## Proposed Extraction Shape

Prefer a small runtime class over a bag of free functions.

Recommended shape:

```python
class Stage4RetryRuntime:
    def __init__(self, owner: "Stage4InterviewRound") -> None:
        self.owner = owner

    def generate_candidates(...)
    def execute_pass_with_fix_loop(...)
```

Why this shape:

- it moves the cluster out of the god-object file immediately
- it avoids a high-friction purity rewrite in the first tranche
- it can still call owner helpers that are not yet worth relocating
- it preserves current runtime semantics with minimal surface churn

This is a readability split first, not a full domain-purity rewrite.

## First Tranche Scope

1. Add `modules/core/stage4_retry_runtime.py`
2. Move the retry/repair helper cluster into that module
3. Keep method names close to the current ones to preserve reviewability
4. Change `Stage4InterviewRound` to delegate:
   - `_generate_candidates()`
   - `_execute_pass_with_fix_loop()`
5. Keep reject handling in `Stage4InterviewRound` for now

## Non-Goals

Do not do these in the first tranche:

- reject runtime split
- persistence split
- logging sink rewrites
- `ctx` ownership migration
- Director/chief-writer lifecycle relocation

## Stop Condition

Stop and write a second design note if the first split requires:

- more than one new module
- changes to reject logging or DB rationale sync
- lifecycle ownership changes for `ctx`, `director`, or `chief_writer`
- broad test rewrites outside `tests/test_stage4_interview_round.py`

## Recommended Next Step

Implement the first runtime split tranche:

- add `modules/core/stage4_retry_runtime.py`
- move retry/repair helpers there
- keep `Stage4InterviewRound` as the orchestration owner
