# Scene Pattern Probe Operating Note

Date: 2026-03-26
Type: operating note
Scope: when to prefer targeted scene-pattern probes over full fresh runs
Mode: documentation-only

## Intent

- Record the current operating shift:
  - from `full fresh run first`
  - to `targeted scene-pattern / seam probe first`
- Keep future validation more interpretable, cheaper, and less loop-heavy.

## Context

Recent system work established a usable baseline:

- Stage 3 major culprit families were materially reduced through clarity/self-audit/PWF work
- Stage 4 IFC/state-injection seams were materially reduced through Wave 1 and Wave 2
- remaining issues are increasingly:
  - narrow seams
  - model-compliance residuals
  - pattern-specific continuity weaknesses

That means many next questions are no longer:

- "Can the whole system run end-to-end at all?"

and are increasingly:

- "Can this specific scene pattern survive the current contracts?"
- "Does this exact seam reproduce outside investment fiction?"
- "Is this a genre problem or a pattern problem?"

## Core Rule

Not every question deserves a full fresh run.

Default preference:

`specific seam or scene-pattern question -> targeted probe first`

Use a full fresh run only when:

- validating a newly landed cross-cutting wave end-to-end
- promoting a local fix into baseline confidence
- checking whether many separate seams interact in a real production chain

## Why Pattern Probes Are Better

### 1. Better variable control

A targeted probe isolates one question:

- combat-heavy episode readiness
- ownership / contract-state continuity
- multi-episode carry-forward
- crowd-reaction / protagonist overvaluation staging

This is easier to interpret than an 8-episode mixed run.

### 2. Lower cost

Full fresh runs are expensive in:

- LLM calls
- time
- operator attention

Pattern probes are cheaper and easier to repeat.

### 3. Faster diagnosis

If the probe fails, the likely cause family is already narrower:

- context injection miss
- low-authority continuity packet
- validator blind spot
- model compliance weakness

### 4. Less canary churn

The current system is at risk of overusing canaries.

Pattern probes reduce:

- repeated "same question, same helper" runs
- stale interpretation loops
- expensive evidence that does not change the next decision

## Current Operating Split

### Keep full fresh runs for:

- baseline refresh after a material cross-cutting wave
- promotion from "looks fixed" to "operationally trusted"
- control-run comparisons against `골든_카나리아`

### Prefer targeted probes for:

- genre expansion readiness
- seam-specific validation
- scene-form validation
- continuity-family reproduction checks

## Current Examples

### Good probe targets

- `기업물`
  - ownership
  - contract completion
  - corporate/personal subject confusion
  - organization/authority continuity

- `무협`
  - combat-heavy episode viability
  - fight geography
  - injury carry-forward
  - stance/power escalation
  - multi-episode combat continuity

### Existing control

- `골든_카나리아` remains the control/stress-test lane

This means new genre work should usually be read as:

- `control stays`
- `new genre adds a pattern probe`

not:

- `replace control with another full run`

## Probe Design Rule

A good probe should ask only one narrow question.

Good:

- "Can wuxia sustain an episode that is mostly combat?"
- "Can corporate fiction preserve ownership/completed-state facts?"
- "Can a two-episode continuation preserve geography and tactical escalation?"

Bad:

- "Is the whole genre fully ready?"
- "Can everything work now?"

## Decision Rule After A Probe

After one probe, choose only one next move:

- no action
- one compact follow-up survey
- one bounded execution SSOT
- one full fresh run

Do not chain:

- probe -> probe -> probe -> canary -> canary -> survey

without a new concrete decision being made.

## Current Recommendation

For the current system state:

- keep `골든_카나리아` as control
- prefer `기업물` and `무협` as next pattern-probe genres
- start with Stage 3-first bounded probes
- escalate to Stage 4 or full fresh run only if the probe actually shows a real seam

## Single Summary

The system is no longer in a phase where every uncertainty needs a full fresh run.

It is now more effective to ask:

- what exact pattern is under test
- what exact seam is under suspicion
- what smallest probe can answer that question

and only then decide whether a larger live run is still necessary.

---

## 3-Pass Audit Notes

- Pass 1: scope bounded to operating guidance, not implementation
- Pass 2: aligned the note with current canary fatigue, genre expansion, and seam-based validation logic
- Pass 3: kept the consequence operational: probe first, full run second
- Confidence: 97%
