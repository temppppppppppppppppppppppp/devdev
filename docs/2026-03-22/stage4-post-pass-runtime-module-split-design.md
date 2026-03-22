# Stage4 Post-Pass Runtime Module-Split Design

Status: final
Date: 2026-03-22
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and cohesion check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: tranche ordering and rollback-risk check passed

## Decision

`Stage4PostProcessor` has crossed the point where the next readability ROI is a bounded post-pass runtime split.

That split should target the manager-settlement, world-state persistence, and advisory-tail cluster, not the owner-side manuscript save or session wrap-up sinks.

## Why Now

The concentrated long-function pressure is no longer one isolated helper:

- `process_pass_result()` (`342 LOC`)
- `_collect_manager_and_build_delta()` (`434 LOC`)
- `_save_world_state_atomic()` (`173 LOC`)
- `_run_post_pass_advisories()` (`183 LOC`)
- `_memorize_and_validate()` (`81 LOC`)
- `_submit_manager_async()` (`62 LOC`)

Together these functions read as one post-pass settlement pipeline that is still embedded inside the owner.

Unlike `Stage4InterviewRound`, `Stage4PostProcessor` is not primarily a direct-method god object problem. The pressure here is one cohesive runtime cluster that has outgrown the file-local helper pattern.

The rest of the current Stage 4 runtime family is already structurally settled:

- `Stage4RetryRuntime`
- `Stage4RejectRuntime`
- `Stage4DirectorRuntime`
- `Stage4OutcomeRuntime`

That makes the post-pass cluster the clearest next Stage 4 readability ROI.

## Why This Boundary Is Viable

This cluster now reads as one runtime pipeline:

- manager async submission and truth capture
- vector-memory and validation sync
- bible delta and actual-truth assembly
- world-state and fact-ledger settlement
- advisory, coverage, pacing, and repetition tails

It is operationally distinct from the owner-side sinks that should stay where they are:

- primary manuscript DB save and rollback path
- emergency dump, HUD update, and output file save
- episode summary, tracker sidecars, cost logging, and perf flush

That separation is strong enough to move the settlement chain without redesigning the pass-result contract.

## Proposed Boundary

Create:

- `modules/core/stage4_post_pass_runtime.py`

Recommended shape:

```python
class Stage4PostPassRuntime:
    def __init__(self, owner: "Stage4PostProcessor") -> None:
        self.owner = owner

    def settle_pass_runtime(...)
```

This should follow the existing Stage 4 runtime pattern:

- keep `ctx`, project, DB, and top-level pass-result ownership on `Stage4PostProcessor`
- move one cohesive runtime concern into a dedicated module
- allow bounded owner callbacks where artifact or sink authority still belongs on the owner

## First Tranche Scope

1. Add `modules/core/stage4_post_pass_runtime.py`
2. Move the post-pass runtime chain:
   - `_submit_manager_async()`
   - `_memorize_and_validate()`
   - `_collect_manager_and_build_delta()`
   - `_save_world_state_atomic()`
   - `_run_post_pass_advisories()`
3. Keep `process_pass_result()` on the owner as a thin shell that:
   - saves the manuscript and Stage 4 sidecars
   - updates HUD and writes output artifacts
   - delegates the post-pass runtime segment into `Stage4PostPassRuntime`
   - performs final session wrap-up and return handling
4. Keep `run_post_episode_tasks()` on the owner

## Keep On Owner

In tranche 1, keep these concerns on `Stage4PostProcessor`:

- `process_pass_result()` top-level orchestration ownership
- manuscript DB save and rollback handling
- emergency dump handling
- HUD update and capital reconciliation
- output file save
- episode-summary and tracker-sidecar saves
- cost logging, audit-buffer flush, and perf reset
- project/DB/session ownership

This keeps the first split bounded and avoids mixing readability work with artifact-output or session-lifecycle ownership changes.

## Why This Ordering

The manager-settlement and advisory path is the cleanest first move because:

- it already shares one local runtime context
- it is where the longest remaining Stage 4 post-pass functions live
- it reduces owner file pressure without forcing a manuscript-output contract rewrite
- it preserves the user-visible pass-result contract while still moving the dense logic block out

## Non-Goals

Do not do these in the first tranche:

- redesign `process_pass_result()` return semantics
- move manuscript DB save ownership out of `Stage4PostProcessor`
- move emergency dump, HUD update, or output file save
- change world-state or fact-ledger persistence semantics
- merge the new runtime with `Stage4OutcomeRuntime` or `Stage4RejectRuntime`

## Stop Condition

Stop and write a follow-up design note if tranche 1 requires:

- more than one new module
- moving manuscript DB save ownership out of the owner
- changing world-state or fact-ledger transaction contracts
- broad test rewrites outside `tests/test_stage4_post_processor.py`, `tests/test_stage4_pass_artifact_contract.py`, and `tests/test_stage4_orchestrator.py`

## Recommended Next Step

Implement the first post-pass runtime split tranche:

- add `modules/core/stage4_post_pass_runtime.py`
- move the manager-settlement, world-state, and advisory chain there
- keep `Stage4PostProcessor` as the manuscript-save, artifact-output, and session-wrap-up owner
