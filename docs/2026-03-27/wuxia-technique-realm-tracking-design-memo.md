# Wuxia Technique-Realm Tracking Design Memo

Date: 2026-03-27
Status: final
Type: system-track design memo (design-only, no code changes)
Canonical Path: `docs/2026-03-27/wuxia-technique-realm-tracking-design-memo.md`
Inputs:
- `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md`
- `docs/2026-03-26/wuxia-combat-scene-readiness-compact-survey.md`
- `docs/2026-03-26/wuxia-combat-quality-probe-report.md`

## Findings

The dominant residual seam after `per-work-fact-contract-alignment-wave1` is not general fact authority anymore. It is a narrow wuxia-specific seam:

- protagonist technique / realm facts exist, but remain mostly advisory
- NPC technique / realm facts do not have a clear persistent owner
- prompt-time realm limits exist in `wuxia.yaml`, but realized-state reconciliation is weak

This means the system is no longer missing a broad fact contract. It is missing a bounded answer to:

1. which wuxia technique / realm facts are authoritative now
2. which ones are still only advisory
3. which ones require new modeling rather than another prompt statement

## Live Baseline

The current code already gives us a usable base.

Existing owner surfaces:
- `StateTracker` owns protagonist-side skill accumulation via `protagonist_skills` and `skill_acquisitions`
- `WorldState` can surface protagonist skills in the canonical body summary
- `wuxia.yaml` already defines `realm_hierarchy` and `realm_technique_limits`
- Wave 1 already made prompt-facing authority explicit for:
  - `WorldState current-state facts > advisory summaries`
  - `FactLedger numbers > BI seed numbers`

Existing gaps:
- no explicit prompt-facing authority for technique / realm facts
- no validator-level protagonist technique-vs-realm consistency check
- no persistent NPC technique mastery owner
- no persistent NPC realm owner
- no cross-episode technique usage history

## Core Problem Split

This seam is actually two different problems.

### Problem A. Contract Alignment Gap

These are facts the system already knows in some form, but does not rank clearly enough:

- protagonist learned techniques
- protagonist current confirmed realm, if already present in realized state
- established technique limits implied by current realm

This is still a contract problem.

### Problem B. Missing Modeling Gap

These are facts the system does not truly own yet:

- NPC learned techniques
- NPC realm progression
- NPC technique reveal history
- technique usage chronology across multiple episodes

This is not a contract-only problem. It is a modeling / persistence gap.

The mistake to avoid is treating both problems as one. If we do that, a small follow-up wave inflates into a registry project.

## Design Goal

Reduce wuxia technique / realm contradictions with the smallest viable system move.

That means:
- make protagonist technique / realm authority clearer using existing owners
- avoid introducing a new registry or DB redesign
- defer NPC technique mastery modeling until there is stronger live evidence that it must be persisted structurally

## Non-Goals

This memo does not recommend:

- a per-work registry system
- new DB tables or schema migration
- broad `FactLedger` / `WorldState` redesign
- fight geography persistence
- cross-episode tactical escalation tracking
- NPC organization / sect membership modeling
- a full Stage 3 truth-gate clone of Stage 4

## Recommended Direction

The right direction is:

- `contract-first for protagonist technique / realm`
- `model-later for NPC technique / realm`

In practice:

1. treat protagonist technique / realm as the only execution-ready slice now
2. keep NPC technique / realm as a deferred modeling seam
3. do not open a broad wuxia registry effort

## Proposed Bounded Wave Shape

If a follow-up execution wave is opened, it should stay protagonist-first.

### Lane A. Prompt-Facing Technique / Realm Authority

Add one short Stage 4 authority statement for wuxia-only technique / realm facts.

Target meaning:
- confirmed realized protagonist technique state outranks seed-only BI phrasing
- confirmed realized protagonist realm state outranks stale arc recap or advisory phrasing
- advisory summaries may supplement, but not override, confirmed realized state

Guardrail:
- do not invent canonical technique / realm facts that are not already present in existing owners
- if current realm is not confirmed in realized state, do not synthesize it just to fill the slot

### Lane B. Protagonist Technique / Realm Consistency Check

Add one bounded consistency lane only if current owners can support it cleanly.

Good candidate:
- protagonist uses a technique above the highest confirmed realm limit

Bad candidates for this wave:
- full NPC technique policing
- choreography repetition scoring
- broad martial-arts creativity evaluation

This should be validator-shaped or prompt-guard-shaped, not a new persistence system.

### Lane C. Optional Stage 3 Absolute Pre-Check

Only if scope remains small, one more absolute pre-check is reasonable:

- destroyed or unavailable signature item treated as currently usable

Why this belongs here:
- it matches the same "high-certainty contradiction, caught earlier" principle as the dead-NPC pre-check
- it is adjacent to wuxia combat continuity

Why it should stay optional:
- it is not the dominant technique / realm seam
- it must not distract the wave into generic inventory policing

## What Should Stay Deferred

These should not be smuggled into the next wave.

### 1. NPC Technique Tracking

There is no convincing contract-only solution here.

If the system does not persist:
- which NPC knows which technique
- what realm that NPC is established at
- when those facts changed

then a prompt statement alone will not solve the problem.

This needs a later design pass if live failures justify it.

### 2. Technique Usage History

Tracking "used once in EP12" versus "never revealed before" is not just authority ordering. It is event history. That is heavier than the next bounded wave should take on.

### 3. Cross-Episode Fight Geography

This remains a separate combat-structure seam already identified in the wuxia combat survey. It should not be bundled into the technique / realm wave.

## Ownership Model For The Next Wave

If a bounded execution wave is opened, ownership should stay simple.

| Fact Class | Owner | Intended Role |
| --- | --- | --- |
| protagonist learned techniques | `StateTracker` + existing realized-state surfaces | realized advisory promoted by contract clarification |
| protagonist confirmed current realm | existing realized-state owner only, when present | prompt-facing authoritative fact |
| technique limit by realm | `wuxia.yaml` | static rule/guard |
| NPC technique mastery | deferred | not in next wave |
| NPC realm progression | deferred | not in next wave |

Important distinction:

- `wuxia.yaml` defines what is allowed in principle
- realized-state owners define what this work has actually established

The next wave should reconcile those two for the protagonist only.

## Why Registry Is Still The Wrong Next Step

A registry would only be justified if the live problem were:

- facts exist nowhere
- or facts exist but cannot be retrieved at all

That is not what current evidence shows.

Current evidence shows:
- protagonist-side technique facts already exist
- realm limits already exist
- what is missing is narrower authority and enforcement

So a registry now would be a too-heavy answer to a partly solved problem.

## Recommended Next Artifact

Open one bounded execution SSOT, but only for:

1. wuxia protagonist technique / realm authority clarification in Stage 4
2. one narrow protagonist technique-vs-realm consistency lane, if current owners are sufficient
3. optional destroyed-item Stage 3 pre-check only if it fits without widening scope

Explicitly exclude:
- NPC technique persistence
- NPC realm persistence
- technique usage ledger
- fight geography
- registry introduction

## 3-Pass Audit Record

Pass 1. Structure and Scope
- memo stays on the residual seam identified by the post-wave survey
- protagonist-ready versus NPC-deferred scope is explicit
- no registry or persistence redesign is silently reintroduced
- PASS

Pass 2. Evidence and Consistency
- aligns with the residual survey: dominant seam is `technique-realm-tracking`
- aligns with the wuxia combat survey: technique progression remains weak while core combat infra is otherwise usable
- aligns with live owner surfaces: protagonist skill accumulation exists, NPC technique ownership does not
- PASS

Pass 3. Execution Readiness
- memo cleanly separates execution-ready contract work from deferred modeling work
- next artifact recommendation is bounded and actionable
- no unsupported claim of "already solved" is made
- PASS

Estimated confidence: 96%

---

- Recommended direction: protagonist-contract-now / NPC-modeling-later
- Dominant unresolved seam: NPC technique mastery has no persistent owner
- Should Codex open an execution SSOT now: yes
