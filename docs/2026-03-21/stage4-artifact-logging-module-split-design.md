# Stage4 Artifact Logging Module-Split Design

Status: final
Date: 2026-03-21
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and boundary check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: execution ordering and rollback risk check passed

## Decision

`Stage4InterviewRound` pass-episode logging is now at the point where additional leaf-helper extraction is lower ROI than a small module split.

The split is justified now.

## Why Now

The current pass-episode logging cluster in `modules/core/stage4_interview_round.py` spans:

- `_append_pass_episode_log()`
- `_build_pass_episode_log_payload()`
- `_build_pass_episode_log_parts()`
- `_assemble_pass_episode_log_payload()`
- `_build_pass_episode_log_base_fields()`
- `_build_pass_episode_log_round_fields()`
- `_build_pass_episode_log_status_fields()`
- `_build_pass_episode_log_usage_fields()`
- `_build_pass_episode_log_usage_flag_fields()`
- `_build_pass_episode_log_model_field()`
- `_build_pass_episode_log_warning_fields()`
- `_build_pass_feedback_provenance()`
- `_build_pass_episode_log_artifact_fields()`
- `_build_pass_episode_log_artifact_core_fields()`
- `_build_pass_episode_log_attempt_fields()`
- `_build_pass_episode_log_logged_artifact_fields()`
- `_build_pass_episode_log_selection_artifact_fields()`

This cluster now has two clear properties:

- most of the logic is already pure payload assembly
- the remaining non-pure dependency is narrow: `self.ctx`-derived `session_id` and the final `_append_episode_log()` sink

That means further splitting inside the same class would mostly increase helper count without reducing the context radius that an LLM has to scan.

The supporting test surface is also already strong enough for a module move. The dedicated pass-log helper regressions in `tests/test_stage4_interview_round.py` cover the payload builder cluster end-to-end and in leaf form.

## Boundary Decision

Create a new module:

- `modules/core/stage4_episode_logging.py`

This module should own pass-episode-log payload normalization and payload assembly.

`Stage4InterviewRound` should keep only:

- orchestration
- `ctx` access
- final sink call to `_append_episode_log()`

## Proposed Extraction Shape

First extraction target:

- move the pass-episode-log builder cluster into `stage4_episode_logging.py`
- keep the final write call in `Stage4InterviewRound`

Recommended API:

```python
@dataclass(slots=True)
class Stage4PassEpisodeLogRequest:
    ep_num: int
    round_num: int
    arc_num: int
    initial_verdict: str
    initial_score: int
    final_verdict: str
    final_score: int
    director_result: dict
    director_feedback: str
    trace_verdict_reason: str | None
    is_patch: bool
    is_patch_fallback: bool
    tot_used: bool
    mad_used: bool
    asp_used: bool
    model_tier: str | None
    validation_warnings: list[str]
    final_warnings: list[str]
    patch_trace: dict | None
    session_runtime_advisory: str
    session_retry_directives: str
    log_artifact_meta: dict
    selection_artifact_meta: dict
    session_id: str | None
```

And a pure builder entrypoint:

```python
def build_pass_episode_log_payload(request: Stage4PassEpisodeLogRequest) -> dict: ...
```

## Why This Shape

This normalizes away the two remaining object-heavy dependencies:

- `chief_writer` becomes `model_tier`
- `self.ctx` becomes `session_id`

That keeps the extracted module pure and testable.

It also stops the new module from importing large Stage 4 runtime objects just to read one field from each.

## Non-Goals

Do not move these in the first tranche:

- generic `_append_episode_log()`
- reject-path episode logging
- DB/session decision logging
- `Stage4InterviewRound.run()` orchestration

Those can remain in the orchestrator/interview-round layer until the pass-log split lands cleanly.

## Follow-Up Review

Follow-up reviewed on 2026-03-21 after the pass-path runtime shell collapse.

Decision:

- reject-path episode logging does not justify a second module split yet

Why not yet:

- `Stage4InterviewRound._finalize_reject_result()` still mixes three concerns in one path:
  - director rationale DB sync
  - generic `_append_episode_log()` sink invocation
  - session decision logging
- unlike the completed pass-path split, the reject-path does not currently present a large pure payload-builder cluster with narrow runtime inputs
- moving it now would either drag DB/session side effects into a new module or create a thin module with weak reuse value

Recommended next step:

- keep reject-path logging in `Stage4InterviewRound`
- allow same-file helper extraction for reject logging payload normalization
- re-evaluate a second logging module split only after reject-path logging is reduced to a thin runtime shell comparable to the pass-path shell

Current status after follow-up helper extraction:

- `_finalize_reject_result()` is now within the acceptable same-file helper boundary
- the next ROI has shifted away from reject artifact-logging module concerns and back to broader reject orchestration in `_handle_reject()`

## First Tranche Plan

1. Add `modules/core/stage4_episode_logging.py`
2. Add normalized `Stage4PassEpisodeLogRequest`
3. Move pure payload builders into the new module
4. Change `Stage4InterviewRound._append_pass_episode_log()` to:
   - normalize runtime objects into the new request
   - call `build_pass_episode_log_payload()`
   - forward to `_append_episode_log(**payload)`
5. Keep existing test expectations and add one cross-module delegation regression

## Risk Assessment

Main risk:

- changing payload key names during normalization

Why risk is acceptable:

- current payload keys are already heavily regression-tested
- the builder cluster is mostly pure
- the only runtime-sensitive value is `session_id`, which can be normalized before the module call

## Stop Condition

If the first tranche needs more than:

- one new module
- one normalized request dataclass
- one thin delegation change in `Stage4InterviewRound`

then stop and write a second design memo before continuing.

## Recommended Next Step

Implement the first tranche:

- extract pass-episode-log payload assembly into `modules/core/stage4_episode_logging.py`
- leave sinks and broader logging orchestration in `Stage4InterviewRound`
