# Gold Manuscript Benchmark Compact Handoff

- date: 2026-03-27
- status: final
- track: system
- mode: survey-only
- confidence: 95
- owner split: this thread stays focused on wuxia canary and soak canary; benchmark exploration may be delegated to another Codex

## Executive Verdict

Yes, this is worth splitting out now.

The idea is not a replacement for live canaries. It is a separate benchmark lane for long-form narrative understanding, state retention, continuity preservation, and forward-constraint inference using completed manuscripts as gold truth.

This lane has high ROI because it can answer important "how well does the model really understand long works" questions much faster and cheaper than full runtime canaries.

## What This Is

A `gold manuscript benchmark` uses existing high-quality serialized manuscripts as the ground truth source.

Instead of requiring:

- plot roadmap
- blueprint
- live app boot
- Stage 3/4 end-to-end runtime
- database mutation
- full retry / patch / rollback loop

it uses:

- corpus ingestion
- checkpoint slicing
- gold truth extraction
- benchmark prompts
- automatic or semi-automatic scoring against the gold continuation

## What This Is Not

This is not the same thing as:

- production pipeline QA
- Stage 3 -> 4 runtime proof
- live persistence proof
- canary replacement for storage substrate validation

It should be treated as a separate lane:

- canary lane: "does the runtime system behave correctly"
- benchmark lane: "does the model understand and preserve long-form narrative truth"

## Why It Matters

The benchmark lane can test questions that are hard to test cheaply with full canaries:

1. long-range state retention
2. relationship memory over hundreds of episodes
3. foreshadow / payoff recall
4. future-arc constraint inference
5. character voice and role stability
6. contradiction detection against gold continuation
7. robustness to false summaries or poisoned recaps

This is especially useful if there are many completed works with 200 / 300 / 500+ episodes.

## Runtime ROI

Relative cost profile:

1. full live canary
   - slowest
   - highest fidelity for runtime truth
2. soak canary
   - middle
   - cheaper runtime stress lane
3. gold manuscript benchmark
   - fastest
   - cheapest way to probe long-memory and story-understanding behavior

Why the benchmark is cheaper:

- no full app boot
- no live Stage 0 / 2 / 3 / 4 orchestration
- no DB write dependency for every run
- no retry / patch / rollback cost unless intentionally simulated
- evaluation can happen at sparse checkpoints instead of every episode

## Core Benchmark Families

### 1. Next-State Reconstruction

Input:

- manuscript up to checkpoint N

Task:

- predict current character states, relationships, injuries, possessions, locations, and unresolved pressures

Score:

- compare against gold state extracted from N+1 onward

### 2. Next-Arc Constraint Inference

Input:

- manuscript up to checkpoint N

Task:

- infer the likely next conflict axis, major constraints, and disallowed moves

Score:

- compare with the actual next arc or next block span from the gold manuscript

### 3. Gold Continuation Contrast

Input:

- manuscript up to checkpoint N
- candidate continuation from the model

Task:

- measure contradiction rate and constraint violations against the gold continuation

Score:

- continuity violations
- forbidden state changes
- relation drift
- world-rule drift

### 4. Foreshadow / Payoff Recall

Input:

- manuscript prefix only

Task:

- identify unresolved seeds and likely payoff points

Score:

- compare with known payoff events later in the gold corpus

### 5. False-Recap Detection

Input:

- manuscript prefix
- one intentionally wrong recap

Task:

- detect false claims and repair the summary

Score:

- error detection precision
- repair accuracy

### 6. Character Voice Persistence

Input:

- long prefix
- character-specific excerpts

Task:

- predict dialogue behavior or classify who would plausibly say a line

Score:

- voice consistency against gold dialogue

## Minimal Data Model

The benchmark does not require full production BI / blueprint artifacts.

It does need a compact gold package per work:

1. normalized episode text
2. checkpoint boundaries
3. gold continuation slices
4. optional gold ledger
   - character state
   - relation state
   - item ownership
   - injury / death
   - location
   - technique / skill
   - unresolved pressure
5. optional seed / payoff map

The ledger can be built in stages:

1. manuscript-only benchmark first
2. lightweight gold ledger second
3. richer payoff / relation annotation later

## Recommended Build Order

### Phase A: Corpus Benchmark Skeleton

- choose 1 to 3 completed long works
- split by episode or block
- define checkpoint intervals
- define benchmark prompt templates
- build a scorer that compares model output to gold continuation snippets

### Phase B: Gold Ledger Layer

- add structured state extraction for checkpoint truth
- add relation / item / injury / technique families
- support contradiction counting instead of only semantic similarity

### Phase C: Adversarial Lane

- inject false recaps
- inject incomplete summaries
- test retrieval stress and summary poisoning

## Recommended Scoring Axes

Use separate axes, not one blended score:

1. state retention
2. contradiction rate
3. relation preservation
4. unresolved-seed recall
5. payoff prediction quality
6. next-arc constraint fit
7. voice consistency
8. false-recap detection

## Boundary With Current Work

This benchmark lane should be split from the current active work.

Current thread should keep ownership of:

- wuxia live canary
- soak canary survey / harness path

Another Codex can own:

- benchmark corpus survey
- gold ledger design
- benchmark runner survey
- scoring contract survey

That separation is good because the benchmark lane is conceptually adjacent to canaries, but not operationally the same.

## Suggested Delegation Brief

Give another Codex a survey-only order with this scope:

1. survey existing corpus candidates for long-form benchmark suitability
2. propose a compact gold package format
3. propose benchmark family coverage and scoring axes
4. identify the smallest reusable code seams in the current workspace
5. do not implement runtime changes yet

Expected output:

- one dated survey doc
- one recommended benchmark MVP
- one list of implementation seams

## Recommended Next Step

Open a separate benchmark survey thread, not an implementation thread.

The first benchmark survey should answer:

1. which completed works are best benchmark sources
2. how to represent checkpoints and gold continuations
3. whether the first MVP should be:
   - manuscript-only
   - manuscript plus lightweight gold ledger
4. which existing validator / world-state / continuity components can be reused safely

## 3-Pass Audit

### Pass 1: Fact Extraction

- the benchmark idea was separated from live canaries
- the runtime ROI distinction was made explicit
- the required gold package and benchmark families were listed

Result: pass

### Pass 2: Contradiction Check

- no claim here assumes the benchmark replaces live runtime canaries
- no claim here assumes BI / blueprint is required
- no claim here assumes immediate implementation

Result: pass

### Pass 3: Decision Audit

- the split of ownership is bounded and practical
- the recommended next step is survey-only
- this handoff can be given to another Codex without dragging the current canary thread off scope

Result: pass

Final decision: save approved
