# ChiefWriter Context Packets Module-Split Design

Status: final
Date: 2026-03-22
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and cohesion check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: tranche ordering and contract-boundary check passed

## Decision

`ChiefWriterContextBuilder.build_common_context()` has crossed the point where the next readability ROI is a bounded context-packets split, not more same-file helper extraction.

The cleanest next boundary is the packet-assembly cluster around Chief Writer context composition:

- digest and recap packets
- past/future guard packets
- HUD anomaly and high-density HUD packets
- NPC equipment/frequency packets
- justification and mandatory-context packets

## Why Now

The pressure is no longer one isolated helper:

- `build_common_context()` (`413 LOC`)
- `_generate_episode_digest()` (`189 LOC`)
- `_check_hud_anomalies()` (`130 LOC`)
- `_build_future_guard_section()` (`75 LOC`)
- `_build_justification_guidance()` (`53 LOC`)

These functions read as one cohesive context-packet family embedded inside `chief_writer_context.py`.

This is not primarily a direct-method god-object problem. `ChiefWriterContextBuilder` is only `22` methods wide, but one packet-assembly concern has outgrown the file-local helper pattern.

## Why This Boundary Is Viable

The candidate split already has a natural internal shape:

- blueprint and ending-hook packet extraction
- bible/protagonist/incarnation packet shaping
- feedback and failure-constraint packet shaping
- past/future guard packet synthesis
- HUD, NPC, and state-tracker packet synthesis
- final prompt-argument assembly before `build_chief_writer_main_prompt()`

This concern is operationally distinct from the surfaces that should stay outside the split:

- `ChiefWriter` prefetch/cache and model-call ownership in `chief_writer.py`
- prompt template authority in `chief_writer_prompts.py`
- top-level genre alias normalization utilities

## Proposed Boundary

Create:

- `modules/domain/agents/chief_writer_context_packets.py`

Recommended shape:

```python
class ChiefWriterContextPackets:
    def __init__(self, owner: "ChiefWriterContextBuilder") -> None:
        self.owner = owner
```

This should follow the same bounded-support-module pattern used elsewhere in the repo:

- `ChiefWriterContextBuilder` remains the adapter used by `ChiefWriter`
- packet construction authority moves into a dedicated module
- the owner keeps only thin coordination and final prompt-template invocation

## First Tranche Scope

1. Add `modules/domain/agents/chief_writer_context_packets.py`
2. Move the packet-building helper family:
   - `_generate_episode_digest()`
   - `_detect_deaths_from_manuscript()`
   - `_detect_past_events_from_manuscript()`
   - `_build_past_guard_section()`
   - `_build_future_guard_section()`
   - `_check_hud_anomalies()`
   - `_get_npc_equipment_summary()`
   - `_get_npc_frequency()`
   - `_get_npc_frequency_warning()`
   - `_get_dna_instruction()`
   - `_build_mandatory_context()`
   - `_extract_recent_events()`
   - `_extract_npc_last_states()`
   - `_build_justification_guidance()`
3. Reduce `build_common_context()` to a thin packet coordinator that:
   - resolves top-level defaults and genre identity
   - asks `ChiefWriterContextPackets` for packet strings
   - calls `build_chief_writer_main_prompt()`

## Keep On Owner

In tranche 1, keep these concerns on `ChiefWriterContextBuilder` or adjacent owner surfaces:

- `build_common_context()` top-level coordination
- `_fit_compact_text()` utility ownership
- genre alias normalization helpers
- final `build_chief_writer_main_prompt()` invocation
- `ChiefWriter` prefetch/cache and model-call ownership in `chief_writer.py`

## Non-Goals

Do not do these in the first tranche:

- rewrite `ChiefWriter.generate_episode()` or cache policy
- move prompt template ownership out of `chief_writer_prompts.py`
- redesign genre alias normalization
- merge this split with Stage 4 packet or runtime modules
- rewrite the broader Chief Writer agent lifecycle

## Stop Condition

Stop and write a follow-up design note if tranche 1 requires:

- more than one new module
- moving `ChiefWriter` cache or LLM-call ownership
- touching unrelated prompt-template contracts
- broad test rewrites outside `tests/test_chief_writer_context.py` and the direct `ChiefWriter` context smoke tests

## Recommended Next Step

Implement the first Chief Writer context-packets split tranche:

- add `modules/domain/agents/chief_writer_context_packets.py`
- move the packet helper family there
- keep `ChiefWriterContextBuilder.build_common_context()` as a thin coordinator
