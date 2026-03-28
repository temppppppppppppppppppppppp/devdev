# Material Revival Ladder Harness

Date: 2026-03-27
Status: active
Scope: shared salvage / repair / promotion flow for existing narrative material pairs

## 1. Purpose

- Standardize the repeated revival pattern for existing `BI + TR` pairs.
- Remove the need to rewrite custom order prompts for the same salvage ladder.
- Keep family semantics inside `blockguide` / `wuxguide` while moving the shared pair-revival flow into one router-level harness.
- Keep most pair repairs on a `lite audit -> top 3 repair -> recheck` path instead of defaulting to full-wave surgery.

This harness is for existing material pairs only. It does not replace planning, production, or BI-generation harnesses.

## 2. When To Use

Use this harness after family resolution when all of the following are true:

- the target is an existing `TR + BI` pair
- the pair already exists in `_quarantine` or in an active candidate path
- the request is salvage, repair, revival, promotion, canary, probe, or baseline qualification

An already-promoted active pair may re-enter this ladder at the smallest remaining proven step.

Typical triggers:

- `이 pair 살릴 수 있나`
- `TR 품질부터 확인`
- `BI만 보강`
- `revival canary`
- `promotion patch`
- `active candidate로 승격`
- `Stage 4까지 확인`

Do not use this harness for:

- fresh `phase0_design` generation
- fresh `TR` generation when no pair exists yet
- fresh `BI` generation when the work is still in normal stage flow

## 3. Read Order

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. resolve family
3. open the resolved family integrated order
4. open this harness
5. enter the smallest remaining revival step only

## 4. Entry Preconditions

Before entering the ladder:

1. confirm the pair paths
2. confirm the pair belongs to one `work_id`
3. confirm the target is pair revival, not fresh generation
4. preserve `_quarantine` provenance until promotion criteria are met

If either `TR` or `BI` is missing, return to the family stage harness instead of using this ladder.

Project-only handoff mode inside the ladder:

- if the user gives only the pair target, first identify the smallest remaining unproven step
- if existing reports already prove earlier steps, resume from the next needed step instead of restarting
- if pair identity or prior-step truth is ambiguous, ask one short clarification

## 5. Ladder

Run the ladder in order. Do not skip forward unless an existing artifact already proves the current step.

### Step 1. Pair Consumability

Goal:

- prove the pair is still consumable by the current harness

Check:

- pair admission
- BI standalone roadmap readiness
- embedded roadmap warnings
- runtime protagonist keys / required contract fields

If pair consumability fails:

- patch only the smallest contract blockers first
- do not start narrative repair before contract ingestion is stable

### Step 2. TR Static Audit

Goal:

- decide whether the current `TR` is a usable production spine

Allowed verdicts:

- `strong spine`
- `usable spine but mixed`
- `consumable but skeleton-likely`
- `regenerate TR first`

Branch:

- `strong` -> continue to BI repair decision
- `mixed` -> continue to `Step 2A. Lite Repair Audit`
- `skeleton` or `regenerate` -> regenerate `TR` first, then restart the ladder

### Step 2A. Lite Repair Audit

Goal:

- identify the smallest profitable repair scope for a `mixed` pair

Default check axis:

- live antagonists / pressure sources
- visible cost after major wins
- surface-template repetition
- theme carry / endgame preparation
- sector texture or equivalent family texture

Default output:

- top `3` weak blocks or repair units only
- one-sentence reason per item
- cascade range per item
- recommended repair order

Rules:

- default cap is `top 3` repairs
- do not jump to `top 10`, full-wave surgery, or full-arc rebuild by default
- repair one unit at a time, then recheck the pair
- only expand beyond `top 3` when a later promotion gate explicitly justifies it

Recheck:

- if the pair becomes usable after the bounded repair set, continue to `BI repair` or `revival canary`
- if the pair remains `mixed`, use the promotion gate below before expanding the scope

### Step 3. BI Repair

Goal:

- replace thin-echo or placeholder BI with a BI that materially amplifies the approved `TR`

Rules:

- repair `BI` only
- keep the current `TR` untouched
- add structural value, not just reformatted block summaries

If confidence is below 95%:

- keep the pair in `_quarantine`
- mark the result `mixed`

### Step 4. Revival Canary

Goal:

- prove the repaired pair is safe for current-harness admission and still narratively coherent

Expected evidence:

- consumability still passes after BI repair
- BI/TR alignment still holds
- no schema drift was introduced
- early narrative truth still survives

### Step 5. Promotion Patch

Goal:

- clear trivial promotion blockers without touching narrative content

Examples:

- missing `block_no`
- missing `pov`
- empty structural fields that the active path requires

Rules:

- minimum patch only
- no TR rewrite
- no BI redesign

### Step 6. Revival-Stage Probe

Goal:

- prove Stage 2 / Stage 3 runtime outputs stay alive after repair

Expected evidence:

- runtime admission
- usable Stage 2 arc output
- usable Stage 3 blueprint output
- genre texture survives runtime translation

### Step 7. Active Promotion

Goal:

- copy or move the now-proven pair from `_quarantine` into the active candidate path

Rules:

- preserve exact contents
- prefer copy over move when provenance matters
- confirm byte-identical promotion when possible
- save a promotion note

### Step 8. Bounded Stage 4 Canary

Goal:

- prove the promoted active pair survives actual manuscript generation

Expected evidence:

- Stage 4 admission pass
- prose remains scene-grade
- genre texture survives into manuscript
- protagonist engine still reads in prose, not only metadata

If this passes, the pair qualifies as an active baseline candidate for that family lane.

## 6. Decision Table

| Current result | Next action |
| --- | --- |
| pair consumability = fail | minimal contract patch first |
| TR verdict = strong, BI repair viable = yes | BI repair |
| TR verdict = mixed | Step 2A lite repair audit |
| lite repair top 3 recheck = pass | BI repair or revival canary |
| lite repair top 3 recheck = still mixed | use promotion gate before expanding |
| TR verdict = skeleton or regenerate | regenerate TR first |
| BI repair status = pass | revival canary |
| revival canary = pass, only trivial blockers remain | promotion patch |
| promotion patch = pass | revival-stage probe |
| revival-stage probe = pass | active promotion |
| active promotion = done | bounded Stage 4 canary |
| Stage 4 canary = pass | treat as active family baseline candidate |

## 6A. Promotion Escalation Gate

Use this table before expanding beyond the default `top 3` repair cap.

| Pair target state | Allowed repair depth | Rule |
| --- | --- | --- |
| quarantine salvage check | top `3` only | stop after recheck unless a single continuity micro-patch is obviously required |
| quarantine promotion candidate | top `3` + optional `4-6` | expand only if top `3` recheck is still mixed and the remaining blockers are concentrated, not diffuse |
| active baseline candidate / Stage 4 target | top `3` + optional `4-6` + bounded continuity patches | expansion is allowed only when it directly protects runtime admission or stage survival |

Hard guardrails:

- `top 10` or all-arc repair is not the default path
- full-wave surgery must be explicitly justified as higher ROI than regenerate-first
- if repair spread becomes too diffuse, classify the pair as regenerate-first instead of endlessly extending salvage scope

## 7. Family Overlays

This harness is shared. Final judgment still uses family semantics.

### 7.1 Blockguide

Prioritize:

- protagonist engine
- capital / leverage / resource logic
- commercial hook persistence
- business-domain texture
- scene-grade runtime output instead of summary-only slabs

### 7.2 Wuxguide

Prioritize:

- protagonist engine
- sect / faction continuity
- realm / technique continuity
- fight sceneability
- late-block escalation that does not flatten into generic stronger-enemy repetition

## 8. Guardrails

- No code or system edits inside this ladder.
- Do not rewrite both `TR` and `BI` at the same time unless the `TR` was explicitly classified as regenerate-first.
- Do not promote based on schema pass alone.
- Prefer artifact truth over metadata-only claims.
- If confidence is below 95%, do not overstate success.
- Keep `_quarantine` provenance until active promotion is explicitly justified.

## 9. Shared Output Pattern

Recommended note/report sequence:

- `docs/YYYY-MM-DD/{work_id}-tr-static-quality-audit.md`
- `docs/YYYY-MM-DD/{work_id}-bi-repair-note.md`
- `docs/YYYY-MM-DD/{work_id}-revival-canary-report.md`
- `docs/YYYY-MM-DD/{work_id}-promotion-patch-note.md`
- `docs/YYYY-MM-DD/{work_id}-revival-stage-probe-report.md`
- `docs/YYYY-MM-DD/{work_id}-promotion-note.md`
- `docs/YYYY-MM-DD/{work_id}-stage4-canary-report.md`

If a step is already proven by an existing report, do not rerun it just to satisfy formality.

## 10. Stop Gates

Stop the ladder when:

- pair identity is ambiguous
- `work_id` coherence is unclear
- contract ingestion is still unstable
- the `TR` is judged regenerate-first
- confidence falls below 95% and no smaller next step exists
- the user redirects scope

## 11. Operator Shorthand

Minimal shorthand:

- `Use the material revival ladder for this pair.`

Expanded shorthand:

- `pair consumability -> TR static audit -> BI repair -> revival canary -> promotion patch -> revival-stage probe -> active promotion -> Stage 4 canary`

## 12. Outcome Rule

The ladder exists to answer one question:

- is this pair still quarantine salvage,
- or has it become an active family baseline candidate?

Do not collapse these two states into one.
