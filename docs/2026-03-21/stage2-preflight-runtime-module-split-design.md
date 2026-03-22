# Stage2 Preflight Runtime Module-Split Design

Status: final
Date: 2026-03-21
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and cohesion check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: tranche ordering and rollback-risk check passed

## Decision

`Stage2PreflightAnalysis` has crossed the point where more same-file leaf extraction is lower ROI than a bounded runtime module split.

The next structural split should target the per-attempt preflight and FourPhase runtime cluster, not the bootstrap/setup shell.

## Why Now

The residual shell queue is effectively closed for the current readability campaign:

- `_preflight_state_setup()` is already a bounded setup shell
- `_preflight_arc_analysis()` is already a bounded attempt-analysis shell
- `_preflight_enrichment()` is already a bounded FourPhase enrichment shell
- `_run_four_phase_generation_attempt()` and `_run_four_phase_enrichment_cycle()` are already normalized orchestrators

At the same time, `Stage2PreflightAnalysis` still carries elevated class pressure:

- `68` direct methods
- one cohesive attempt-runtime concern spread across multiple helper chains
- a second cohesive setup/bootstrap concern that is separate from the attempt runtime

That means the next readability gain comes from moving the attempt-runtime concern out of the owner, not from more same-file helper slicing.

## Why This Boundary Is Viable

The attempt-runtime concern is now cohesive enough to move because it already reads as one runtime pipeline:

- per-attempt analyst context assembly
- analyst weapons preparation
- FourPhase attempt execution
- PASS/FAIL cycle normalization
- FourPhase enrichment result packaging

This concern is distinct from the owner-side setup/bootstrap path:

- it runs after `_preflight_state_setup()`
- it is centered on per-attempt generation and enrichment
- it does not need to own the parallel bootstrap, initial cache warmup, or constraint compiler setup shell

## Keep On Owner

The first tranche should keep these concerns on `Stage2PreflightAnalysis`:

- `_preflight_state_setup()`
- `_compute_arc_drive()`
- `_compute_preflight()`
- `_compute_constraint_block()`
- `_run_preflight_parallel_tasks()`
- `_apply_constraint_compiler_block()`
- `_extract_constraint_compiler_state()`
- top-level Stage 2 orchestration ownership
- `ctx`, project, DB, state-tracker, and perf-timer ownership

This keeps the first split bounded and avoids mixing readability work with bootstrap-lifecycle or cache-ownership changes.

## Proposed Boundary

Create:

- `modules/core/stage2_preflight_runtime.py`

Recommended shape:

```python
class Stage2PreflightRuntime:
    def __init__(self, owner: "Stage2PreflightAnalysis") -> None:
        self.owner = owner

    def preflight_arc_analysis(...)
    def preflight_enrichment(...)
```

This mirrors the Stage 4 runtime split pattern:

- move one cohesive runtime concern out of the god-object file
- preserve owner-side setup/bootstrap authority
- allow bounded owner callbacks where `ctx`-level sinks and caches still belong on `Stage2PreflightAnalysis`

## First Tranche Scope

1. Add `modules/core/stage2_preflight_runtime.py`
2. Move the attempt-analysis chain:
   - `_preflight_arc_analysis()`
   - `_build_arc_analysis_context()`
   - `_apply_arc_analysis_support_layers()`
   - `_build_arc_analysis_base_context()`
   - `_inject_reverse_feedback_advisories()`
   - `_warn_on_large_arc_analysis_context()`
   - `_prepare_analyst_weapons()`
3. Move the FourPhase runtime chain:
   - `_preflight_enrichment()`
   - `_run_four_phase_enrichment_cycle()`
   - `_build_prerun_four_phase_cycle_payload()`
   - `_run_four_phase_attempt_with_spinner()`
   - `_resolve_four_phase_attempt_cycle_payload()`
   - `_run_four_phase_generation_attempt()`
   - `_prepare_four_phase_generation_plan()`
   - `_execute_four_phase_generation_plan()`
   - `_dispatch_four_phase_generation_request()`
   - `_finalize_four_phase_pass()`
4. Keep `_preflight_state_setup()` and its helper chain on the owner
5. Change `Stage2PreflightAnalysis` to delegate the attempt-runtime entry shells to the new runtime

## Why This Ordering

The attempt-analysis and FourPhase paths already share the same local runtime context:

- `attempt`
- `global_arc_no`
- analyst feedback
- cached preflight result
- enriched block and protagonist identity
- Director-facing entity registry

Moving them together avoids a half-split where attempt analysis, generation, and PASS/FAIL normalization still bounce between owner and runtime.

Keeping setup/bootstrap on the owner keeps the first tranche bounded.

## Non-Goals

Do not do these in the first tranche:

- move setup/bootstrap helpers
- move `ctx` ownership away from `Stage2PreflightAnalysis`
- redesign FourPhase result payload schemas
- split the runtime into multiple Stage 2 modules immediately
- relocate perf-timer or cache ownership out of the owner

## Stop Condition

Stop and write a follow-up design note if tranche 1 requires:

- more than one new module
- moving setup/bootstrap ownership out of the owner
- changing FourPhase payload or StateTracker sink contracts
- broad test rewrites outside `tests/test_stage2_preflight.py` and `tests/test_stage2_preflight_helpers.py`

## Recommended Next Step

Implement the first preflight-runtime split tranche:

- add `modules/core/stage2_preflight_runtime.py`
- move the per-attempt analysis and FourPhase enrichment helper chain there
- keep `Stage2PreflightAnalysis` as the setup/bootstrap owner
