# Three-Phase Blueprint Runtime Module-Split Design

Status: final
Date: 2026-03-22
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and cohesion check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: tranche ordering and contract-boundary check passed

## Decision

`ThreePhaseBlueprintGenerator.generate()` has crossed the point where the next readability ROI is a bounded runtime split, not more same-file helper extraction.

The next tranche should introduce `ThreePhaseBlueprintRuntime` and move the large per-episode three-phase pipeline there while keeping owner-side patch and public contract authority stable.

## Why Now

The pressure is concentrated in one owner method:

- `ThreePhaseBlueprintGenerator.generate()` (`739 LOC`)

Its body is not a thin shell. It still mixes:

- feedback bootstrap and retry memory assembly
- Phase 1 constraint compilation and cache reuse
- Phase 2 strategy routing between in-place patch, partial regeneration, full ensemble generation, and ASP correction
- Phase 3 continuity checks, director validation, candidate selection, and quality-gate handling
- PASS_WITH_FIX patch-and-reaudit looping
- reject bookkeeping and final emergency fallback resolution

That is a cohesive runtime pipeline, not a residual wrapper problem.

## Why This Boundary Is Viable

The per-episode generation pipeline is cohesive enough to move as one bounded concern.

At the same time, several responsibilities should remain on the owner in tranche 1 because they are external contracts, not readability-only helpers:

- dependency wiring in `__init__()`
- sub-component ownership for `constraint_compiler`, `ensemble`, and `validator`
- `_inplace_patch_blueprint()` because external Stage 4 callsites and dedicated tests already invoke it directly
- pass-rate instrumentation sink behavior around intermediate reject recording
- `stats`, `get_stats()`, and `print_stats()`
- factory/protocol authority such as `create_three_phase_blueprint_generator()` and protocol-facing `generate()` shape

This makes the runtime split viable without forcing a patch-mode contract rewrite.

## Proposed Boundary

Create:

- `modules/domain/agents/three_phase_blueprint_runtime.py`

Recommended shape:

```python
class ThreePhaseBlueprintRuntime:
    def __init__(self, owner: "ThreePhaseBlueprintGenerator") -> None:
        self.owner = owner

    def generate(...)
```

The owner should keep the public `generate()` entry point as a thin shell in tranche 1 and delegate to `self.runtime.generate(...)`.

## First Tranche Scope

1. Add `modules/domain/agents/three_phase_blueprint_runtime.py`
2. Attach `self.runtime` inside `ThreePhaseBlueprintGenerator.__init__()`
3. Move the large per-episode pipeline out of `generate()`:
   - feedback/bootstrap preparation
   - retry-state memory and cached constraint block handling
   - Phase 1 constraint compilation/caching
   - Phase 2 candidate routing and ASP correction
   - Phase 3 continuity/director validation and quality gate
   - PASS_WITH_FIX re-audit loop
   - final reject/emergency fallback resolution
4. Leave `ThreePhaseBlueprintGenerator.generate()` as a thin owner shell

## Keep On Owner

In tranche 1, keep these concerns on `ThreePhaseBlueprintGenerator`:

- `__init__()` dependency wiring
- `_inplace_patch_blueprint()`
- `_record_intermediate_reject()` if the first runtime tranche would otherwise pull pass-rate sink ownership across the boundary
- `stats`, `get_stats()`, and `print_stats()`
- `create_three_phase_blueprint_generator()`
- protocol-facing public ownership of the agent surface

## Why This Ordering

This ordering gives the readability win without forcing broad external churn.

It keeps stable:

- Stage 4 callers that already use `_inplace_patch_blueprint()`
- patch-mode focused regression tests
- protocol/factory expectations around the generator owner

That lets tranche 1 target the real problem, which is the large runtime loop itself.

## Non-Goals

Do not do these in the first tranche:

- move `_inplace_patch_blueprint()` out of the owner
- redesign patch-mode semantics
- rewrite the pass-rate monitor payload contract
- change the public `generate()` signature
- merge this runtime with `FourPhaseArcGenerator` or other blueprint agents

## Stop Condition

Stop and write a follow-up design note if tranche 1 requires:

- moving `_inplace_patch_blueprint()` out of the owner
- changing `modules/protocols/agents.py` contracts
- broad test rewrites outside `tests/test_blueprint_patch_mode.py`, protocol checks, and direct runtime-delegation regressions
- mixing readability work with Stage 4 blueprint-mutation ownership changes

## Recommended Next Step

Implement the first generator-runtime split tranche:

- add `modules/domain/agents/three_phase_blueprint_runtime.py`
- move the large phase/retry/director-validation pipeline out of `generate()`
- keep patch-mode primitives, stats, and public contract authority on `ThreePhaseBlueprintGenerator`
