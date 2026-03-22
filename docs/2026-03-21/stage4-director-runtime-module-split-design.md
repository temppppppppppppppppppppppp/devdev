# Stage4 Director Runtime Module-Split Design

Status: final
Date: 2026-03-21
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and cohesion check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: tranche ordering and rollback-risk check passed

## Decision

`Stage4InterviewRound` has crossed the point where the next readability ROI is a third bounded structural split.

That split should target the director-review and prevalidation cluster.

## Why Now

The retry-runtime and reject-runtime splits are now structurally settled:

- `modules/core/stage4_retry_runtime.py` owns retry-lane routing and `PASS_WITH_FIX` runtime execution
- `modules/core/stage4_reject_runtime.py` owns reject runtime handling and reject finalization

After those extractions, the next concentrated Stage 4 concern is the director-facing cluster:

- `_run_pre_director_validation()`
- `_run_director_core_validation_modules()`
- `_run_director_optional_validation_modules()`
- `_build_cv_context()`
- `_collect_director_retrieval_context()`
- `_build_director_retrieval_payload()`
- `_run_director_review_phase()`
- `_log_director_review_prelude()`
- `_run_director_decision_and_log_summary()`
- `_invoke_director_review()`
- `_build_director_input_pack()`
- `_build_director_decision_core_parts()`
- `_build_director_candidate_evidence_parts()`
- `_build_director_reference_appendix_parts()`

At the same time, `Stage4InterviewRound` still carries the highest direct-method pressure in the workspace.

That means the next readability gain comes from moving a cohesive review/prevalidation concern out of the owner, not from more same-file leaf extraction.

## Why This Boundary Is Viable

This cluster is now cohesive enough to move because it already reads as one runtime pipeline:

- pre-director Python validation
- director retrieval/context assembly
- director input-pack assembly
- director review invocation and decision shaping

The cluster is also operationally distinct from the retry and reject runtimes:

- it runs before final outcome handling
- it is centered on review-time validation and Director interaction
- it does not need to own retry-lane or reject-side effect logic

## Keep On Owner

The first tranche should keep these concerns on `Stage4InterviewRound`:

- `_persist_director_selection()`
- artifact snapshot ownership
- DB `save_director_selection()` sink ownership
- `_log_attempt_event()`
- `_record_retrieval_observation()`
- `ctx`, agent, DB, and project ownership
- top-level `run()` orchestration and final outcome packaging

This keeps the split bounded and avoids mixing a readability tranche with persistence-contract changes.

## Proposed Boundary

Create:

- `modules/core/stage4_director_runtime.py`

Recommended shape:

```python
class Stage4DirectorRuntime:
    def __init__(self, owner: "Stage4InterviewRound") -> None:
        self.owner = owner

    def run_pre_director_validation(...)
    def run_director_review_phase(...)
```

This mirrors the retry/reject runtime pattern:

- move a cohesive runtime concern out of the god-object file
- preserve owner-side sinks and lifecycle ownership
- allow bounded owner callbacks where sink authority still belongs on `Stage4InterviewRound`

## First Tranche Scope

1. Add `modules/core/stage4_director_runtime.py`
2. Move the prevalidation chain first:
   - `_run_pre_director_validation()`
   - `_run_director_core_validation_modules()`
   - `_run_director_optional_validation_modules()`
   - `_build_cv_context()`
   - `_collect_director_retrieval_context()`
   - `_build_director_retrieval_payload()`
3. Move the director-review chain next in the same module:
   - `_run_director_review_phase()`
   - `_log_director_review_prelude()`
   - `_run_director_decision_and_log_summary()`
   - `_invoke_director_review()`
   - `_build_director_input_pack()`
   - director pack-part helpers
4. Leave `_persist_director_selection()` on the owner in tranche 1
5. Change `Stage4InterviewRound` to delegate the prevalidation/review entry shells to the new runtime

## Why This Ordering

The prevalidation and director-review paths already share the same local context:

- candidate manuscripts
- validation results
- director retrieval context
- Director invocation payloads

Moving them together avoids a half-split where the retrieval and input-pack helpers still bounce between owner and runtime.

Keeping selection persistence on the owner keeps the first tranche bounded.

## Non-Goals

Do not do these in the first tranche:

- move DB selection persistence
- move artifact snapshot ownership
- redesign Director result schema
- merge retry/reject/director runtimes into one Stage 4 mega-runtime
- migrate `ctx` or agent ownership away from `Stage4InterviewRound`

## Stop Condition

Stop and write a follow-up design note if tranche 1 requires:

- more than one new module
- changes to Director result or selection DB contracts
- moving artifact-log or DB sink ownership out of the owner
- broad test rewrites outside `tests/test_stage4_interview_round.py`

## Recommended Next Step

Implement the first director-runtime split tranche:

- add `modules/core/stage4_director_runtime.py`
- move the prevalidation/review helper chain into that module
- keep `Stage4InterviewRound` as the orchestration owner and persistence sink owner
