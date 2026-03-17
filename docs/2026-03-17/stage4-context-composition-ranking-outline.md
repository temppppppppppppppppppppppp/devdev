# Stage4 Context Composition Ranking Outline

Date: 2026-03-17
Status: draft
Canonical Path: `docs/2026-03-17/stage4-context-composition-ranking-outline.md`
Document Type: planning note
Commit State:
- Baseline Commit: `100ecd03557e1b8c7a3544b5285fc80e7105050c`
- Baseline Dirty Summary: `dirty: 2 tracked docs, 1 tracked runtime log; hotspots: docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt*.md, projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Scope:
- preserve brainstorming context around Stage 4 retrieval and mandatory-context ranking
- treat the main problem as context composition and ordering, not just vector retrieval quality
- capture bounded next-step design ideas without opening an execution queue
Non-Goals:
- no code changes in this note
- no claim that the note is 3-pass finalized
- no execution SSOT, roadmap, or implementation order in this note

## 0. Live Snapshot
- current Stage 4 writer path already has many context producers, but they land in one large accumulated `mandatory_context`
- the sharper current problem is not "retrieval exists or not" but "good retrieval is mixed with bulky reference material and loses ranking authority"
- Director-side retrieval path already passes `work_focus` into the planner, while writer-side retrieval currently does not
- `coverage_warnings` and retrieval observations already exist, so the system can observe some failures, but the composed prompt still mixes truth, retrieval, and bulky advisory layers

### Current Code Touchpoints
- writer mandatory context assembly: `modules/core/stage4_context_builder.py` -> `build_mandatory_context()`
- work-focus resolution for writer path: `modules/core/stage4_context_builder.py` -> `_resolve_work_retrieval_focus()`
- Stage 4 retrieval execution: `modules/core/stage4_context_builder.py` -> `_execute_retrieval_plan()`
- SC retrieval planning: `modules/core/context_advisor.py` -> `plan_stage4_retrieval()`
- budget trim and final composition: `modules/core/stage4_context_builder.py` -> `_apply_context_budget()` and `_compose_mandatory_context_with_headroom()`
- Director-side comparator path: `modules/core/stage4_interview_round.py` -> Director retrieval assembly and coverage warnings

## 0A. Working Assumptions
- upstream retrieval quality matters, but composition order and budget pressure matter more than raw query quality in the current live path
- Stage 4 needs a ranked context stack, not a single undifferentiated blob
- `work_focus` should be a first-class planning input on the writer path, not only a summary/warning surface
- bulky lookback, failure-history, and long-form reference material should be treated as lower-tier support unless explicitly needed

## 1. Main Finding
- the design problem is better framed as `Stage 4 context composition ranking` rather than just `retrieval ranking`
- the current writer path computes `_work_focus` and a work-slot summary, but the planner call omits `work_focus`
- the current Director path does pass `work_focus` into `plan_director_retrieval()`
- therefore the strongest intent signal can influence Director retrieval planning but miss writer retrieval planning

### Consequence
- writer retrieval can plan slots without the strongest work-identity guidance
- later `coverage_warnings` can still detect missing work-focus behavior, but observation comes after planning
- retrieval quality may therefore be blamed for a composition/input contract gap

## 2. Current Producer Inventory
- mandatory context base from writer helper
- work identity / tracking-slot summary
- Stage 2 failure context
- ambient NPC hint
- arc constraint summary
- state_tracker summary bulk
- arc summary digest
- SC retrieval results
- legacy multi-query fallback vector block
- extended lookback digest
- foreshadow prompt
- semantic plot guard warnings
- pacing prompt
- narrative summaries
- future arc context
- coverage-warning note

## 3. Core Problem Statement
- the current pipeline mixes at least three different context classes into one prompt body:
  - truth and continuity layers
  - episode-direct retrieval evidence
  - bulky background/reference/advisory material
- because these classes are not tiered explicitly, budget trim and section order can bury high-value retrieval under lower-value bulk

## 4. Tier Model

### Tier 0: Must-Hold Truth / Carry-Over
- persisted world-state and fact-ledger driven truth
- work-focus summary
- NPC boundary block
- hard continuity and must-not-do constraints
- relationship / threat / prev-hud carry-over surfaces

Principle:
- shortest and most protected layer
- should appear earliest
- should be trimmed last or never under normal conditions

### Tier 1: Episode-Direct Retrieval
- work tracking slot retrieval
- work scene engine retrieval
- work registry retrieval
- previous ending continuity retrieval
- NPC history
- relationship history
- unresolved plot
- scene context
- bounded manuscript excerpt when directly needed

Principle:
- this is the real retrieval pack for CW
- should sit immediately after Tier 0
- can be trimmed mildly, but only after Tier 2 is reduced

### Tier 2: Reference / Advisory / Bulk Support
- Stage 2 failure context
- extended lookback
- future arc context
- narrative summaries
- broad state_tracker summary bulk
- foreshadow / pacing / semantic advisory blocks
- legacy fallback retrieval bulk
- coverage-warning note

Principle:
- useful but not first-write critical by default
- should be gated conditionally
- should be trimmed most aggressively

## 5. Priority Design Issues

### 5.1 Input Contract Mismatch
- writer path resolves `_work_focus` but does not pass it into `plan_stage4_retrieval()`
- Director path resolves `work_focus` and does pass it into `plan_director_retrieval()`
- this asymmetry is likely a higher-ROI fix point than further tuning raw retrieval queries

### 5.2 Section Ranking vs Slot Ranking
- planner already has slot priority and per-slot budget
- prompt composer still lacks section-tier ranking across non-retrieval producers
- current system can therefore have good slot ranking but poor prompt ranking

### 5.3 Budget Pressure
- trim logic protects work-slot summary somewhat, but broader trim still works primarily from section size and overflow
- Tier 2 can still pressure Tier 1 if composition order is not reworked first

### 5.4 Coverage Warnings as Consumer Noise
- current coverage-warning note can be inserted at the head of `_mc_parts`
- this helps observability but may not be the best first-write CW surface
- it likely belongs later, or more on Director/advisory surfaces than CW-leading text

## 6. Five-Step Sequential Hardening

### Step 1. Input Alignment
- make writer retrieval planner consume `work_focus` just as Director retrieval already does
- treat this as a context-input correctness issue, not an advanced ranking issue

### Step 2. Tier Separation
- explicitly classify every producer into Tier 0 / Tier 1 / Tier 2
- preserve behavior initially; classification alone already clarifies later gating and trim logic

### Step 3. Composition Order
- compose as `Tier 0 -> Tier 1 -> Tier 2`
- stop treating all producers as one flat append-only stream
- keep retrieval evidence close to the truth layer instead of burying it behind reference bulk

### Step 4. Conditional Gates
- gate Tier 2 sections by need
- examples:
  - future-arc context on arc-boundary or specific continuation risk
  - Stage 2 failure context mainly on retry-sensitive situations
  - extended lookback mainly when recent retrieval is sparse or thin

### Step 5. Tier-Based Budgeting
- trim Tier 2 first, then Tier 1 lightly, then Tier 0 last
- evolve observability to track not only planned slots and warnings but also tier survival

## 7. Recommended Stop Line
- current ROI is highest at Step 1 through Step 3
- Step 4 and Step 5 should wait until the tier model exists and some real observations accumulate
- going straight into adaptive policy or complex ranking heuristics now would likely be overengineering

## 8. Why This Topic Has High ROI
- both `Pre-Write Pack` quality and retrieval usefulness depend on what survives near the top of the prompt
- even strong retrieval cannot help if it arrives below bulky support material
- narrowing `PASS_WITH_FIX` helps downstream, but context composition ranking can improve first-draft quality upstream

## 9. Open Questions To Resume Later
- should coverage-warning text remain visible to CW at all, or move mostly to Director-facing evidence
- which current state-tracker summaries are truly Tier 0 versus bulky Tier 2 support
- whether legacy multi-query fallback should remain on by default once writer `work_focus` is passed into the planner
- what minimal telemetry is needed to know whether Tier 1 survives and actually improves first-write quality
- whether retrieval composition should be co-designed with the future `Pre-Write Pack`, or stabilized first as a lower-level substrate
