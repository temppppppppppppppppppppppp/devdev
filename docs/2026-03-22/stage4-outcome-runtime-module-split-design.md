# Stage4 Outcome Runtime Module-Split Design

Status: final
Date: 2026-03-22
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and cohesion check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: tranche ordering and rollback-risk check passed

## Decision

`Stage4Orchestrator` has crossed the point where the next readability ROI is a bounded outcome-runtime split.

That split should target the round outcome governance cluster, not blueprint preflight or session/bootstrap setup.

## Why Now

The public-wrapper queue is already structurally settled:

- `_run_interview_loop()` is a bounded episode loop shell
- `_prepare_stage4_session()` is already normalized
- `_preflight_validate_blueprint()` is already a bounded fail-open shell

What remains concentrated on the owner is the round outcome governance cluster:

- `_handle_reject_round_result()` (`74 LOC`)
- `_handle_pass_round_result()`
- `_run_cove_pass_verification()`
- `_run_cove_llm_verification()`
- `_handle_cove_runtime_failure()`
- `_analyze_reject_round()` (`67 LOC`)
- `_apply_retry_repair_escalation()` (`66 LOC`)
- `_apply_reject_contradiction_advisory()`
- `_build_retry_pathology_payload()` (`65 LOC`)
- `_emit_retry_pathology_signal()` (`59 LOC`)

At the same time, `Stage4Orchestrator` still sits at `89` direct methods, making it the largest remaining unsplit core orchestration surface in the main Stage 4 pipeline.

That means the next readability gain comes from moving a cohesive round-outcome concern out of the owner, not from more same-file helper slicing.

## Why Outcome Runtime Is Viable

This cluster now reads as one policy/runtime concern:

- PASS-side CoVe verification
- REJECT-side bucket and contradiction analysis
- retry pathology signaling
- escalation decision routing
- V75-D / V75-B handoff choice

It sits between:

- the interview-round execution shell that produces `round_result`
- the lower-level blueprint mutation or artifact sink helpers that actually patch/regenerate and persist

That middle layer is now cohesive enough to move.

## Proposed Boundary

Create:

- `modules/core/stage4_outcome_runtime.py`

Recommended shape:

```python
class Stage4OutcomeRuntime:
    def __init__(self, owner: "Stage4Orchestrator") -> None:
        self.owner = owner

    def handle_pass_round_result(...)
    def handle_reject_round_result(...)
```

This mirrors the earlier Stage 4 runtime splits:

- keep `ctx` and top-level loop ownership on the orchestrator
- move one cohesive runtime/policy concern into a dedicated module
- allow owner callbacks where blueprint mutation, artifact snapshotting, or project sinks should stay owner-mediated

## First Tranche Scope

1. Add `modules/core/stage4_outcome_runtime.py`
2. Move the round outcome governance entry chain:
   - `_handle_pass_round_result()`
   - `_run_cove_pass_verification()`
   - `_run_cove_llm_verification()`
   - `_handle_cove_runtime_failure()`
   - `_handle_reject_round_result()`
   - `_analyze_reject_round()`
   - `_apply_reject_contradiction_advisory()`
   - `_apply_retry_repair_escalation()`
   - `_build_retry_pathology_payload()`
   - `_emit_retry_pathology_signal()`
3. Keep the owner-side `_handle_round_outcome()` loop shell thin and delegate into the new runtime
4. Keep blueprint mutation helpers owner-mediated in tranche 1:
   - `_apply_v75d_inplace_repair()`
   - `_run_v75d_patch_attempt()`
   - `_apply_v75b_blueprint_regeneration()`
   - `_regenerate_blueprint()`
   - `_log_escalation_event()`

## Why This Ordering

The pass/reject/CoVe/pathology/escalation layer is the cleanest first move.

Reasons:

- it is already linear and policy-heavy
- it centralizes the outcome taxonomy for each interview round
- it can move without immediately forcing blueprint artifact or regeneration ownership changes
- it reduces direct-method pressure on `Stage4Orchestrator` faster than splitting blueprint preflight

The lower-level V75 patch/regeneration helpers can remain owner callbacks in tranche 1 and only move if the split stays clean.

## Keep On Owner For Now

In the first outcome-runtime tranche, keep these concerns on `Stage4Orchestrator`:

- `_run_interview_loop()`
- `_prepare_episode_round()`
- `_prepare_stage4_session()`
- `_preflight_validate_blueprint()`
- `_build_blueprint_preflight_request()`
- `_resolve_blueprint_preflight_result()`
- `_apply_v75d_inplace_repair()`
- `_run_v75d_patch_attempt()`
- `_apply_v75b_blueprint_regeneration()`
- `_regenerate_blueprint()`
- project/DB ownership
- artifact snapshot ownership

This keeps the first split bounded and avoids mixing readability work with blueprint persistence or artifact-authority changes.

## Non-Goals

Do not do these in the first outcome-runtime tranche:

- blueprint-preflight schema changes
- `generate_content_via_router` request/response contract changes
- blueprint artifact snapshot schema changes
- project DB ownership changes
- merging the new runtime with `Stage4RetryRuntime`, `Stage4RejectRuntime`, or `Stage4DirectorRuntime`

## Stop Condition

Stop and write a follow-up design note if tranche 1 requires:

- more than one new module
- moving blueprint artifact snapshot ownership out of `Stage4Orchestrator`
- changing `regenerate_blueprint` behavior or persistence contract
- broad test rewrites outside `tests/test_stage4_orchestrator.py`

## Recommended Next Step

Implement the first outcome-runtime split tranche:

- add `modules/core/stage4_outcome_runtime.py`
- move the pass/reject/CoVe/pathology/escalation policy chain first
- keep blueprint mutation and artifact sinks owner-mediated in tranche 1
