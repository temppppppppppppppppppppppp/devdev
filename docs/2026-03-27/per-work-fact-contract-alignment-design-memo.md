# Per-Work Fact Contract Alignment Design Memo

Date: 2026-03-27
Status: final
Type: system-track design memo (design-only, no code changes)
Canonical Path: `docs/2026-03-27/per-work-fact-contract-alignment-design-memo.md`
Inputs:
- `docs/2026-03-27/per-work-fact-system-synthesis-memo.md`
- `docs/2026-03-27/per-work-fact-contract-authority-compact-survey.md`
- `docs/2026-03-27/per-work-registry-need-compact-survey.md`

## Findings

The next bounded move should be **contract alignment**, not a new registry layer.

The current system already has enough per-work fact storage:
- `BI`
- `TR`
- `FactLedger`
- `WorldState`
- `StateTracker`
- `Entity Registry`
- `Reference Anchors`
- `ImmutableFactPacket`

The remaining seam is that some authority rules are still too implicit for:
- the LLM prompt
- Stage 3 pre-check timing

So the design target is:
- make authority more explicit
- move one or two high-value contradictions earlier
- do not add a new persistence system

## Design Goal

Clarify and enforce this runtime contract:

1. `BI` owns static origin facts
2. `TR` owns planned episode intent
3. `FactLedger` owns realized numeric and event-sourced fact evolution
4. `WorldState` owns realized current state
5. `StateTracker` and `Entity Registry` are extracted/derived helpers, not final authority
6. `ImmutableFactPacket` compiles attempt-local hard constraints from authoritative realized layers

The two concrete seams to address first are:
- `BI -> FactLedger` numeric precedence is not explicit enough to the LLM
- `Stage 3 -> Stage 4` canonical impossibility checks happen later than ideal

## Proposed Scope

This memo recommends a future bounded wave with only two contract changes.

### Change A. Prompt-Facing Authority Statement

Add one short authority statement near the canonical block / tier-0 injection path.

Intent:
- explicitly tell the LLM that realized persisted layers outrank initial seed layers when they conflict

Target meaning:
- `FactLedger numbers > BI seed numbers`
- `WorldState current state > StateTracker extracted summaries`
- `persisted realized state > advisory extracted recap`

Recommended wording shape:
- keep it short
- declarative, not explanatory
- no large taxonomy dump

Example intent, not final copy:
- "When BI seed facts and persisted realized facts conflict, follow the persisted realized layer."
- "For numbers and assets, follow FactLedger over BI seed values."
- "For NPC current state, follow WorldState over extracted summaries."

Why this is the lightest useful move:
- no schema change
- no new DB table
- no new registry
- directly addresses the dominant seam from the survey

### Change B. Lightweight Stage 3 Canonical Pre-Check

Introduce a narrow Stage 3 pre-check for clearly impossible blueprint assignments.

Priority candidate:
- dead NPC assigned active present-time role

Possible bounded extensions later:
- destroyed item treated as available
- impossible protagonist hard-state contradiction

Why this is worth doing:
- right now these contradictions can survive into Stage 4 and waste a full cycle
- the system already knows many of these facts
- this is timing/alignment improvement, not new memory infrastructure

Guardrail:
- keep Stage 3 pre-check narrow
- only move obviously impossible contradictions earlier
- do not attempt full Stage 4 truth enforcement inside Stage 3

## What This Memo Explicitly Rejects

### 1. New Per-Work Registry System

Rejected for now because:
- current systems already overlap heavily
- a new registry would increase coordination and write-back complexity
- current evidence does not show storage absence as the main blocker

### 2. Broad Persistence Redesign

Rejected for now because:
- the problem is not persistence failure
- long-gap continuity already works better than feared
- the next step should be bounded and cheap

### 3. Wuxia-Only Special Handling

Rejected for now because:
- wuxia is the motivating stress case
- but the contract issue is system-wide
- numeric authority, current-state authority, and early contradiction checking are not wuxia-exclusive

## Ownership Model

The future wave should preserve this ownership model:

| Fact Class | Owner | Notes |
| --- | --- | --- |
| protagonist identity, world origin, genre rules | `BI` | static seed only |
| per-episode planned beats and intent | `TR` / blueprint | planning layer |
| current NPC/item/relationship/timeline state | `WorldState` | realized current state |
| numeric evolution / event-sourced fact history | `FactLedger` | realized evolving facts |
| extracted arc summaries | `StateTracker` | advisory / derived |
| entity alias cache | `Entity Registry` | helper, not final authority |
| attempt-local hard packet | `ImmutableFactPacket` | compiled from authoritative layers |

This means the change is not:
- "who owns facts"

It is:
- "how clearly that ownership is communicated and enforced"

## Prompt Contract Direction

The prompt-facing contract should become explicit but stay minimal.

Recommended rule shape:
- one short precedence block
- attached to the canonical constraint section
- no long prose

Recommended rule content:
1. Static seed from BI is valid unless a persisted realized layer supersedes it
2. `FactLedger` is authoritative for runtime-evolved numeric facts
3. `WorldState` is authoritative for realized current-state facts
4. `StateTracker` is advisory when a persisted canonical layer exists

This avoids the common failure mode:
- BI says one thing
- runtime-evolved state says another
- LLM sees both
- precedence is guessed instead of stated

## Stage 3 Guard Direction

Stage 3 should not become a second Stage 4.

It should only gain:
- a very small impossible-fact pre-check lane

Good candidates:
- dead NPC active role
- maybe one or two similarly absolute contradictions

Bad candidates:
- broad stylistic policing
- soft personality drift
- full continuity validation clone

The principle:
- move only high-certainty, high-cost contradictions earlier

## Architecture Direction

Recommended direction:
- **contract-only with one early-guard supplement**

That means:
- no registry system
- no new persistence store
- no generalized fact refactor
- one prompt authority clarification
- one narrow Stage 3 canonical impossibility pre-check

## Recommended Next Step

**One bounded execution SSOT** should be opened next, but only for:
- prompt-facing authority statement insertion
- Stage 3 dead-NPC pre-check

Not included in that future SSOT:
- registry introduction
- schema migration
- fight geography
- technique usage logging
- broader persistence redesign

## 3-Pass Audit Record

Pass 1. Structure and Scope
- design memo type matches the requested next step after synthesis
- scope remains bounded to contract alignment
- registry and persistence redesign are explicitly excluded
- PASS

Pass 2. Evidence and Consistency
- aligns with synthesis memo recommendation: contract-only
- aligns with authority survey dominant seam: BI-to-FactLedger numeric precedence
- aligns with registry survey conclusion: no new registry needed now
- no new unsupported storage claims introduced
- PASS

Pass 3. Execution and Readability
- findings-first
- future change scope is concrete and narrow
- ownership model is explicit
- rejected alternatives are explicit
- recommended next artifact is clear
- PASS

Estimated confidence: 97%

---

- Recommended direction: contract-only
- Dominant unresolved seam: BI-to-realized-layer precedence is too implicit for the LLM
- Should Codex open an execution SSOT now: yes
