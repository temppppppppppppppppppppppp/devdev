# Sovereign Bootstrap Runtime Module-Split Design

Status: final
Date: 2026-03-22
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and cohesion check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: tranche ordering and owner-boundary check passed

## Decision

`SovereignApp` has crossed the point where the next readability ROI is a bounded bootstrap-runtime split, not more same-file helper extraction.

The target is the bootstrap family under `_attach_agents()`, not menu/control-plane or one-stop pipeline helpers.

## Why Now

The current problem is no longer long-function count alone.

The live readability snapshot shows:

- `SovereignApp` at `185` direct methods
- `_attach_agents()` already normalized to `54 LOC`
- `_init_core_agents()` at `17 LOC`
- `_init_v51_tracking_modules()` at `19 LOC`
- `_init_v6026_reasoning_modules()` still at `109 LOC`
- `_init_v50_modules()` at `20 LOC`

That means same-file helper extraction has started to trade wrapper length for owner method inflation.

Further splitting inside `main_a.py` would likely keep lowering a few method lengths while increasing `SovereignApp` surface area again.

## Why This Boundary Is Viable

The bootstrap cluster is already cohesive:

- core LLM agent registry assembly
- Stage 2 support helper bootstrap
- V51 tracking/failure-memory restore
- V60.26~V55 reasoning/advisory/dashboard bootstrap

These concerns all sit under `_attach_agents()` and share the same dependency bundle:

- `self.current_project`
- `self.sys.api_client`
- `self.ui`
- `self.selected_genre`
- owner-held helper callbacks like `_get_current_project_log_path()`

At the same time, the outer bootstrap contract should remain owner-mediated because it still owns:

- bootstrap status semantics
- partial-failure reporting
- genre binding
- validation toggle binding
- continuity-inspector bootstrap
- final operator-facing bootstrap result

So the seam is now:

- keep `_attach_agents()` as owner shell
- move the dependency-heavy bootstrap family below it into a dedicated runtime/helper authority

## Proposed Boundary

Create:

- `modules/core/sovereign_bootstrap_runtime.py`

Recommended shape:

```python
class SovereignBootstrapRuntime:
    def __init__(self, owner: "SovereignApp") -> None:
        self.owner = owner

    def init_core_agents(...)
    def init_v50_modules(...)
```

This mirrors the earlier bounded runtime/module splits:

- owner keeps top-level contract and status control
- runtime owns one cohesive bootstrap concern
- owner callbacks remain available where project-path or UI authority should not move

## First Tranche Scope

1. Add `modules/core/sovereign_bootstrap_runtime.py`
2. Move the bootstrap family authority out of `main_a.py`:
   - `_init_core_agents()`
   - `_build_flash_analysis_callback()`
   - `_build_core_llm_agents()`
   - `_init_stage2_support_agents()`
   - `_init_v51_tracking_modules()`
   - `_restore_failure_learner_from_db_snapshot()`
   - `_migrate_failure_learner_snapshot_from_json()`
   - `_restore_character_voice_tracker()`
   - `_restore_foreshadow_tracker()`
   - `_init_semantic_plot_guard_module()`
   - `_init_v6026_reasoning_modules()`
3. Keep owner-side `_attach_agents()` thin and delegate into the new runtime
4. Keep owner-side `_init_v50_modules()` as either:
   - a thin delegation shell, or
   - an owner contract wrapper that adds `_load_v50_history()`

## Keep On Owner

In tranche 1, keep these on `SovereignApp`:

- `_load_bootstrap_components()`
- `_apply_genre_bindings()`
- `_load_validation_settings()`
- `_apply_validation_settings()`
- `_bootstrap_continuity_inspector()`
- `_validate_initialized_agents()`
- `_finalize_bootstrap_status()`
- `_attach_agents()`
- `_load_v50_history()`

These are owner/public/bootstrap-contract concerns, not just readability helpers.

## Why This Ordering

This ordering gives the real readability win without destabilizing bootstrap contracts.

It keeps stable:

- `BootstrapStatus` lifecycle and partial-failure semantics
- existing `tests/test_bootstrap_status.py` authority around `_attach_agents()`
- owner-held UI/operator logging
- owner-held continuity/bootstrap follow-up steps after core agent initialization

It also directly addresses the real pressure point:

- reducing `SovereignApp` surface growth caused by repeated same-file helper extraction

## Non-Goals

Do not do these in the first bootstrap-runtime tranche:

- move `_attach_agents()` itself out of the owner
- redesign `BootstrapStatus`
- change genre-binding or continuity-inspector behavior
- merge one-stop pipeline helpers into the same runtime
- mix bootstrap refactor with shutdown/control-plane semantics

## Stop Condition

Stop and write a follow-up design note if tranche 1 requires:

- moving bootstrap-status ownership out of `SovereignApp`
- changing `_attach_agents()` return semantics
- broad test rewrites outside bootstrap authority/delegation coverage
- mixing bootstrap refactor with session lifecycle or one-stop pipeline behavior

## Recommended Next Step

Implement the first bootstrap-runtime split tranche:

- add `modules/core/sovereign_bootstrap_runtime.py`
- move the core/V50 bootstrap family there
- keep `_attach_agents()` and bootstrap status handling owner-mediated
