# Four-Phase Arc Runtime Module-Split Design

Status: final
Date: 2026-03-22
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and cohesion check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: tranche ordering and contract-boundary check passed

## Decision

`FourPhaseArcGenerator.generate()` has crossed the point where the next readability ROI is a bounded runtime split, not more same-file helper extraction.

The next tranche should introduce `FourPhaseArcRuntime` and move the large per-arc four-phase pipeline there while keeping owner-side patch-mode and public contract authority stable.

## Why Now

The pressure is concentrated in one owner method:

- `FourPhaseArcGenerator.generate()` (`625 LOC`)

Its body is not a thin shell. It still mixes:

- protagonist bootstrap and pacing-signal preparation
- Phase 1 preflight, compiler, negative-example, and cache reuse
- Phase 2 ensemble generation, spare-candidate reuse, ASP correction, and patch-mode fallback
- director compare/select branching and advisory payload wiring
- post-generation sanitize and Python advisory checks
- Phase 3 validation, reject bookkeeping, and retry feedback carry-forward
- terminal failure handling

That is a cohesive runtime pipeline, not a residual wrapper problem.

## Why This Boundary Is Viable

The per-arc generation pipeline is cohesive enough to move as one bounded concern.

At the same time, several responsibilities should remain on the owner in tranche 1 because they are external contracts, not readability-only helpers:

- dependency wiring in `__init__()`
- sub-component ownership for `preflight`, `compiler`, `negative_injector`, `ensemble`, and `validator`
- `_inplace_patch_arc()` because external tests and Stage 2 flows already invoke it directly
- `patch_arc_with_feedback()` because Stage 2 and patch-mode callsites already depend on that owner-facing contract
- `stats`, `get_stats()`, and `print_stats()`
- factory/public authority such as `create_four_phase_generator()`

This makes the runtime split viable without forcing a patch-mode contract rewrite.

## Proposed Boundary

Create:

- `modules/domain/agents/four_phase_arc_runtime.py`

Recommended shape:

```python
class FourPhaseArcRuntime:
    def __init__(self, owner: "FourPhaseArcGenerator") -> None:
        self.owner = owner

    def generate(...)
```

The owner should keep the public `generate()` entry point as a thin shell in tranche 1 and delegate to `self.runtime.generate(...)`.

## First Tranche Scope

1. Add `modules/domain/agents/four_phase_arc_runtime.py`
2. Attach `self.runtime` inside `FourPhaseArcGenerator.__init__()`
3. Move the large per-arc pipeline out of `generate()`:
   - protagonist bootstrap and pacing-signal setup
   - Phase 1 preflight/compiler/negative-example/cache handling
   - Phase 2 ensemble generation, spare-candidate reuse, and ASP correction
   - director compare/select routing and advisory merge
   - post-generation sanitize/advisory shaping
   - Phase 3 validation, reject bookkeeping, and retry-loop carry-forward
   - terminal failure handling
4. Leave `FourPhaseArcGenerator.generate()` as a thin owner shell

## Keep On Owner

In tranche 1, keep these concerns on `FourPhaseArcGenerator`:

- `__init__()` dependency wiring
- `_inplace_patch_arc()`
- `patch_arc_with_feedback()`
- `stats`, `get_stats()`, and `print_stats()`
- `create_four_phase_generator()`
- owner-facing patch-mode/public API surface

This keeps the first split bounded and avoids mixing readability work with Stage 2 patch-mode or public factory ownership changes.

## Why This Ordering

This ordering gives the readability win without forcing broad external churn.

It keeps stable:

- Stage 2 and patch-mode callers that already use `_inplace_patch_arc()` and `patch_arc_with_feedback()`
- focused regression surfaces in `tests/test_arc_patch_mode.py`, `tests/test_inplace_reliability.py`, `tests/test_pass_with_fix.py`, and Stage 2 preflight/finalizer tests
- public factory expectations around `create_four_phase_generator()`

That lets tranche 1 target the real problem, which is the large runtime loop itself.

## Non-Goals

Do not do these in the first tranche:

- move `_inplace_patch_arc()` out of the owner
- move `patch_arc_with_feedback()` out of the owner
- redesign Stage 2 patch-mode semantics
- change the public `generate()` signature
- merge this runtime with `ThreePhaseBlueprintRuntime` or Stage 2 runtime modules

## Stop Condition

Stop and write a follow-up design note if tranche 1 requires:

- moving `_inplace_patch_arc()` or `patch_arc_with_feedback()` out of the owner
- changing Stage 2 patch-mode caller contracts
- broad test rewrites outside targeted runtime-delegation and patch-mode authority regressions
- mixing readability work with arc patch semantics or factory/public API redesign

## Recommended Next Step

Implement the first arc-runtime split tranche:

- add `modules/domain/agents/four_phase_arc_runtime.py`
- move the large per-arc pipeline out of `generate()`
- keep patch-mode primitives, stats, and public contract authority on `FourPhaseArcGenerator`
