# Donor Review And Adoption Contract v1

Date: 2026-04-19
Status: active
Scope: material-side donor review, donor adoption, and donor visibility rules for fresh works and materially touched `TR + BI` pairs

## 1. Role

- define how donor use is handled on the material side
- separate `donor review is mandatory` from `donor adoption is mandatory`
- keep donor-specific surfaces from silently becoming canonical law
- make donor judgment visible before `Phase0`, `TR`, and `BI` are called ready

This contract is material-side only.

It does not create a runtime donor selector.
It does not make the Geuldobi pipeline directly consume donor packets.

## 2. Executive Rule

Use this rule everywhere:

- `donor review`: required
- `donor adoption`: optional, evidence-based, and explicit

Every fresh or actively maintained work must record one of:

- `adopted`
- `considered_but_rejected`
- `not_applicable`

No work may move into `TR/BI pair complete`, `promotion-target pair`, or `active baseline candidate` posture without one of those donor decisions being visible in canonical material-side authority.

## 3. Why This Exists

Recent bounded evidence showed a useful asymmetry:

- strong effects were already visible from donor-translated materials alone
- no direct runtime donor-ingestion feature was required to get those gains

That means the material side should treat donor work as:

- upstream doctrine review
- generalized-slot translation
- contamination control

not as:

- direct scene-copy import
- proper-noun dependency
- runtime magic feature

## 4. Applicability

This contract applies to:

- fresh candidate works
- fresh works moving through `pitch -> Phase0 -> TR -> BI`
- actively maintained works that are being materially rewritten
- regenerated pairs
- promotion-target pairs

This contract does not force backfill on:

- untouched historical live pairs
- purely archival reference pairs
- benchmark-only pairs that are not being promoted or rewritten

## 5. Stage Placement

### 5.1 Pitch

`donor review` belongs on the material side before `Phase0-ready`.

Minimum donor-review outputs:

- donor candidates considered, if any
- what doctrine or loop grammar is being considered
- what contamination must be blocked
- current donor decision:
  - `adopted`
  - `considered_but_rejected`
  - `not_applicable`

### 5.2 Phase0

If a donor is `adopted`, `Phase0` must absorb only the translated generalized law.

Canonical rule:

- `Phase0` may contain generalized loop law, success/failure conditions, slot logic, or reward rotation
- `Phase0` must not become a donor proper-noun dump

### 5.3 work_guard

If a donor is `adopted`, `work_guard` may enforce translated rules and timing thresholds.

Canonical rule:

- `work_guard` is the pass/fail enforcement surface
- donor packet is not the enforcement surface

### 5.4 TR

`TR` must manifest translated doctrine, not explain donor doctrine.

Operational rule:

- donor review must be complete before a `TR` pair is called production-ready
- `TR` should show translated effects:
  - proof
  - receipt
  - observer shift
  - next gate
- `TR` should not carry donor-specific proper-noun contamination as pseudo-law

### 5.5 BI

`BI` must preserve translated story law, not donor-specific skin.

Operational rule:

- donor review must be complete before a `BI` pair is called production-ready
- `BI` may amplify translated structures
- `BI` should not present donor-specific organizations, gimmicks, or scene-order as canonical truth unless they were independently re-authored into the work's own canon

## 6. Canonical Home vs Annex Rule

Use this hierarchy:

### Canonical home

- `Phase0`
- `work_guard`

### Translation / provenance annex

- donor packet
- donor registry
- loop abstraction packet
- source manifest notes

Meaning:

- canonical law stays donor-free
- donor packet explains where the law came from
- donor registry tracks donor status and allowed influence
- source manifest records provenance, not canonical law

## 7. Allowed Decisions

### 7.1 `adopted`

Use when:

- a donor contributes useful generalized doctrine
- contamination can be controlled
- the material-side team can translate the donor into slot-level or law-level statements

Required consequences:

- generalized translation only
- donor-specific surfaces remain annex-only
- contamination guardrails must be named

### 7.2 `considered_but_rejected`

Use when:

- the donor was reviewed
- the donor did not fit the work
- the donor overfit risk outweighed expected gain

Required consequence:

- keep a short rejection reason in canonical material-side authority

### 7.3 `not_applicable`

Use when:

- no meaningful donor was needed
- the work is being produced from internal canon and benchmark law only

Required consequence:

- keep the decision visible so later pair work does not look like the donor question was skipped

## 8. Minimum Visibility Rule

For fresh or materially touched works, donor decision must be visible in at least one canonical upstream authority surface before `TR/BI pair complete` may be claimed.

Preferred visibility surfaces:

1. pitch canon or work current-truth note
2. `Phase0`
3. `work_guard`
4. preprocess manifest or donor annex refs

If the work is `adopted`, the preferred supporting annex surfaces are:

- donor packet
- donor registry entry
- loop abstraction packet mapping

## 9. Pair-Side Rule

For new, newly touched, regenerated, or promotion-target pairs:

- donor review is mandatory
- donor adoption is optional
- pair promotion is blocked until donor decision is visible

Pair-side meaning:

- `pair complete` does not mean `donor adopted`
- it means `donor question was answered and recorded`

## 10. Non-Goals

- forcing donor adoption on every work
- turning donor packets into direct runtime selectors
- copying donor scene order or proper nouns into canon
- requiring historical untouched live pairs to backfill donor notes before they can simply exist

## 11. Reporting Contract

Every donor-aware fresh candidate, maintained work, or materially touched pair should be able to answer:

1. donor decision
2. donor scope
3. contamination risks
4. generalized law that was kept
5. donor-specific surfaces that were blocked

## 12. Guardrails

- do not confuse donor review with donor adoption
- do not let donor proper nouns become canonical law
- do not let `TR` become donor explanation prose
- do not let `BI` hide donor contamination behind generalized language
- do not claim pair readiness when the donor question was never answered

## 13. Operating Consequence

Material-side default going forward:

- donor review is now standard
- donor decision is required
- donor adoption is opt-in
- translated doctrine belongs in `Phase0 + work_guard`
- donor packets remain annexes
