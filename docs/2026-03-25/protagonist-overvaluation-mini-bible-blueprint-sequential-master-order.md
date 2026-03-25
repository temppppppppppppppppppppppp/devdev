# Protagonist Overvaluation Mini-Bible + Blueprint Sequential Master Order

Date: 2026-03-25
Status: final (3-pass audited)
Document Type: sequential master order
Canonical Path: `docs/2026-03-25/protagonist-overvaluation-mini-bible-blueprint-sequential-master-order.md`
Scope: narrative-design order, survey/design first, canary merge second
Mode: sequential, not parallel

## 1. Intent

This order exists to operationalize the merged conclusion from:
- `docs/2026-03-25/protagonist-overvaluation-staging-4terminal-merge-audit.md`

Merged conclusion:
- Bible owns admiration principles
- Blueprint owns admiration execution
- Arc distributes admiration modes
- Manuscript renders, but is too late for core design

However, a full bible-first redesign is too heavy right now.

So the practical design direction is:
- **mini bible note first**
- **blueprint-first execution design second**
- **canary merge third**

This is a sequential order, not an implementation order.
The immediate goal is to produce a bounded design document that Codex can audit, then merge it with incoming canary evidence before deciding whether to open a narrative-design execution SSOT.

## 2. Sequence Overview

### Step 1. Opus design doc

Produce one compact design document that answers:
- what the **mini bible note** should contain
- what the **blueprint-first execution layer** should do
- what should remain deferred until canary evidence arrives

### Step 2. Codex audit

Codex reviews the design doc for:
- ownership correctness
- boundedness
- over-design risk
- whether the proposal is still too heavy or is realistically actionable

### Step 3. Canary merge

When the next canary result arrives, merge:
- the design proposal
- the canary evidence

Then decide:
- open one bounded narrative-design SSOT
- or defer further

## 3. Hard Constraints

- Survey / design only
- No code changes
- No execution SSOT creation by Opus
- No queue / roadmap / temp edits
- No full bible schema redesign in this wave
- No manuscript-first solutioning
- No deep scene-by-scene rewrite proposals
- Keep the solution bounded to:
  - mini bible note
  - blueprint-first execution guidance
  - canary-aware defer strategy

## 4. Required Output Shape

Opus should produce exactly one design document:
- `docs/2026-03-25/protagonist-overvaluation-mini-bible-blueprint-design.md`

It should answer:
- what belongs in the mini bible note
- what belongs in blueprint execution guidance
- what arc can optionally carry later
- what manuscript should not be asked to solve
- what the first bounded future wave should be if canary does not contradict the design

## 5. Common Opus Order Prompt

```text
Narrative-design sequential order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/2026-03-25/protagonist-overvaluation-mini-bible-blueprint-sequential-master-order.md
3. docs/2026-03-25/protagonist-overvaluation-staging-4terminal-merge-audit.md
4. docs/2026-03-25/opus-protagonist-overvaluation/t1-bible-owner-mapping.md
5. docs/2026-03-25/opus-protagonist-overvaluation/t3-blueprint-staging.md
6. docs/2026-03-25/opus-protagonist-overvaluation/t2-arc-distribution.md
7. docs/2026-03-25/opus-protagonist-overvaluation/t4-manuscript-pov-info-gap.md

Task:
Produce one bounded design document for `mini bible note + blueprint-first execution`.
Survey/design only. No code changes.

Primary goal:
Turn the abstract owner mapping into a practical, lightweight design direction that is realistic to operationalize later.

Hard constraints:
- Do not propose full bible schema reform as the immediate move.
- Do not propose manuscript-first correction as the primary move.
- Do not write an execution SSOT.
- Do not patch code.
- Keep the mini bible note compact enough to fit as a lightweight design note, not a full framework.
- Keep the blueprint-first section practical: staging guidance, not grand theory.
- Explicitly say what should wait for canary evidence.

The design doc must contain:
1. Executive Summary
2. Why `big number -> wow` fails in chaebol/business-power stories
3. Mini Bible Note
   - what 3-5 admiration axes to define
   - what 2-4 forbidden praise patterns to ban
   - what observer-tier concept to define minimally
4. Blueprint-First Execution Layer
   - how blueprint should stage admiration via:
     - observer allocation
     - POV shift timing
     - information asymmetry
     - reveal ordering
     - show-not-tell constraints
5. What Arc Can Carry Later
6. What Manuscript Must Not Be Asked To Invent
7. Best bounded future wave if canary supports this direction
8. What should remain deferred until canary evidence arrives

Style:
- stay abstract but actionable
- avoid code-level patch plans
- avoid full schema diagrams unless truly necessary
- optimize for a design note that Codex can audit quickly

Mandatory final lines:
- Mini bible note owner: <short label>
- Blueprint-first execution owner: <short label>
- Should Codex open a narrative-design execution SSOT now: no
```

## 6. Merge Rule After Canary

After the canary arrives, Codex will merge:
- the design note from this order
- the live canary findings

Then only one of these outcomes is allowed:
- `open one bounded narrative-design SSOT`
- `defer and refine design note`

No multi-wave bundle should be opened from this topic without the canary merge.

## 7. Dispatch Line

Use:

- `docs/2026-03-25/protagonist-overvaluation-mini-bible-blueprint-sequential-master-order.md 읽고 순차 설계 문서만 작성. mini bible note + blueprint-first execution, 코드수정/SSOT 작성 금지.`

