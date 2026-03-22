# Stage4 Context Packets Module-Split Design

Status: final
Date: 2026-03-21
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and cohesion check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: tranche ordering and rollback-risk check passed

## Decision

`Stage4ContextBuilder` has crossed the point where the next readability ROI is a bounded context-packet split, not more same-file helper extraction.

That split should target the continuity/world-state/fact-ledger/tier12 auxiliary-section cluster.

## Why Now

The residual-shell review queue is effectively exhausted for the current readability campaign snapshot:

- `_build_tier12_auxiliary_sections()` is already a bounded shell
- `_build_continuity_packet()` is already a bounded shell
- `_build_condensed_world_state_summary()` is already a bounded shell
- the remaining Stage 4 runtime splits now live in dedicated modules

After the retry, reject, and director runtime splits settled, `Stage4ContextBuilder` is now the clearest remaining owner-side god-object pressure in the Stage 4 path:

- `71` direct methods
- a cohesive context-packet concern spread across multiple helper clusters
- no persistence or sink ownership inside the packet-building path

That means the next readability gain comes from moving a cohesive packet-building concern out of the owner, not from more one-off helper slicing.

## Why This Boundary Is Viable

The packet-building concern is now cohesive enough to move because it already reads as one rendering pipeline:

- continuity packet assembly
- condensed world-state summary assembly
- condensed fact-ledger summary assembly
- tier12/state-tracker auxiliary section assembly

This concern is operationally distinct from the retrieval/budget/orchestration path:

- it formats packet-style context blocks
- it does not own retrieval planning
- it does not own context-budget trimming policy
- it does not own prompt injection or round-context assembly
- it does not own DB or artifact sinks

## Keep On Owner

The first tranche should keep these concerns on `Stage4ContextBuilder`:

- `_build_tier0_mandatory_sections()`
- `_build_mandatory_context_payload()`
- `_build_mandatory_context_retrieval_coverage()`
- `_collect_stage4_retrieval_context()`
- `_execute_retrieval_plan()`
- `_apply_context_budget()`
- `_compose_tiered_mandatory_context_with_headroom()`
- `_compose_context_with_retrieval_coverage()`
- `_build_mandatory_prompt_injections()`
- `build_round_context()`
- insertion-order ownership for tier0/tier1/tier2 composition
- `ctx`, project, world-state, and fact-ledger ownership

This keeps the split bounded and avoids mixing readability work with retrieval-policy or context-budget changes.

## Proposed Boundary

Create:

- `modules/core/stage4_context_packets.py`

Recommended shape:

```python
class Stage4ContextPackets:
    def __init__(self, owner: "Stage4ContextBuilder") -> None:
        self.owner = owner

    def build_continuity_packet(...)
    def build_condensed_world_state_summary(...)
    def build_condensed_fact_ledger_summary(...)
    def build_tier12_auxiliary_sections(...)
```

This mirrors the existing bounded split pattern:

- move one cohesive rendering concern out of the god-object file
- preserve owner-side orchestration and insertion-order control
- allow owner callbacks only where ordering or cross-cluster composition still belongs on `Stage4ContextBuilder`

## First Tranche Scope

1. Add `modules/core/stage4_context_packets.py`
2. Move the continuity packet chain:
   - `_build_continuity_packet()`
   - `_build_continuity_npc_sections()`
   - `_build_continuity_relationship_section()`
   - `_build_continuity_fact_sections()`
3. Move the condensed state packet chain:
   - `_build_condensed_world_state_summary()`
   - `_build_condensed_world_state_header_sections()`
   - `_build_condensed_world_state_registry_sections()`
   - `_build_condensed_world_state_tail_sections()`
   - `_build_condensed_fact_ledger_summary()`
4. Move the tier12 auxiliary-section chain:
   - `_build_tier12_auxiliary_sections()`
   - `_build_state_tracker_auxiliary_sections()`
5. Leave tier0 insertion-order logic and retrieval/budget composition on the owner

## Why This Ordering

These three packet clusters already share the same type of responsibility:

- gather state snapshots from owner-owned services
- shape them into bounded context strings
- return rendered packet text back to the owner

Moving them together avoids a half-split where packet helpers bounce between the owner and the new module while the owner still tries to manage the same packet concern inline.

Keeping tier0 ordering and retrieval coverage on the owner keeps the first tranche bounded.

## Non-Goals

Do not do these in the first tranche:

- move retrieval planning or retrieval execution
- move context-budget trimming policy
- move round-context assembly
- move prompt injection helpers
- move `_build_npc_boundary_block()` unless the first tranche proves the packet module still needs another bounded packet-specific follow-up
- redesign the mandatory-context payload schema

## Stop Condition

Stop and write a follow-up design note if tranche 1 requires:

- more than one new module
- moving retrieval-plan ownership out of `Stage4ContextBuilder`
- moving context-budget authority out of the owner
- broad rewrites outside `tests/test_stage4_context_builder.py`
- cross-cutting changes to prompt payload or round-context contracts

## Recommended Next Step

Implement the first context-packets split tranche:

- add `modules/core/stage4_context_packets.py`
- move the continuity/world-state/fact-ledger/tier12 packet helpers into that module
- keep `Stage4ContextBuilder` as the orchestration owner and insertion-order authority
