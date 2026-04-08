# Material Benchmark Readiness Harness v1

Date: 2026-04-07
Status: active
Scope: reusable readiness harness for `material_ssot/20_pitch` candidate, canon, and pre-Phase0 material audits

## 1. Role

This harness exists to stop material-side benchmark drift before `Phase0`, `TR`, or `BI`.

Use it when a human or external model is asked to judge:

- fresh pitch candidate
- canon pitch
- selection-ready claim
- `Phase0-ready` claim
- material re-check after pitch tightening

This harness governs readiness judgment, not downstream pair grading.

## 2. Three Material States

### 2.1 Exploratory Draft

- idea is still being explored
- `first_block_cider_ledger` may temporarily contain `has_cider: false`
- every false row must be treated as a named hole, not as an acceptable production answer
- default verdict is `HOLD`

### 2.2 Selection-Ready

- candidate is requesting promotion into active canon or `Phase0` lane
- all rows in `first_block_cider_ledger` for blocks `2~6` must be `has_cider: true`
- block `1` cannot rescue the ledger
- block `7+` cannot rescue the ledger
- any false row means `not selection-ready`

### 2.3 Phase0-Ready

- same requirements as `selection-ready`
- plus the ledger must clearly show which block carries:
  - proof
  - reevaluation
  - visible token
  - next gate opening
- if the promotion path depends on `bridge_or_payback_note` instead of same-block payback, it is not `Phase0-ready`

## 3. Hard Laws

- readiness judgment uses strict `TR blocks 2, 3, 4, 5, 6` only
- `TR block 1` is setup or innocence context only
- `TR block 7+` is late rescue and invalid for opening readiness
- `first_block_cider_ledger` must contain exactly five rows for `2~6`
- blank rows are invalid
- for `selection-ready`, every row must pay inside that same block
- `bridge_or_payback_note` may explain a thin receipt, but it may not rescue a false row
- `pain_only_exit: true` at block `6` is immediate `HOLD`
- if any row is false, upstream material may stay as draft, but it must not be promoted
- `work_guard` translation may compress a ledger result, but it may not override a false row

## 4. Required Material Output Shape

When running a material benchmark, use this section order:

1. `Pitch Identity`
2. `Material Compliance Self-Check`
3. `First-Block Cider Ledger Review`
4. `Planning Candidate 7 Questions`
5. `Work-Guard Freeze Check`
6. `Promotion Verdict`
7. `Fix Queue`

## 4A. Machine-Readable Ledger Contract

New candidate, canon, and synthesis docs should write the ledger in this exact key shape:

```md
- block_no: 2
  has_cider: true
  same_block_receipt: ...
  receipt_kind: ...
  bridge_or_payback_note:

- block_no: 3
  has_cider: true
  same_block_receipt: ...
  receipt_kind: ...
  bridge_or_payback_note:

- block_no: 4
  has_cider: true
  same_block_receipt: ...
  receipt_kind: ...
  bridge_or_payback_note:

- block_no: 5
  has_cider: true
  same_block_receipt: ...
  receipt_kind: ...
  bridge_or_payback_note:

- block_no: 6
  has_cider: true
  same_block_receipt: ...
  receipt_kind: ...
  pain_only_exit: false
  bridge_or_payback_note:
```

Rules:

- use exact keys, not paraphrases
- use exact rows `2, 3, 4, 5, 6`
- `bridge_or_payback_note` is optional explanation only
- if a row is `has_cider: false`, `bridge_or_payback_note` may not be used as rescue proof

## 4B. Machine-Readable Readiness Claim

New docs should write readiness in this exact key shape:

```md
- selection-ready: yes/no
- Phase0-ready: yes/no
- all 2~6 ledger rows have has_cider true: yes/no
- block 1 used as opening rescue: yes/no
- block 7+ used as opening rescue: yes/no
```

Operator gate:

- before starting a fresh repo-level pitch wave, run:
  - `python -X utf8 scripts/pre_new_pitch_readiness_gate.py`
- run `python -X utf8 scripts/material_readiness_validator.py --path <md-or-dir>` before promotion
- for real promotion, prefer:
  - pre-canon: `python -X utf8 scripts/material_promotion_gate.py --stage canon --path <candidate-md>`
  - pre-Phase0: `python -X utf8 scripts/material_promotion_gate.py --stage phase0 --path <pitch-md> --work-id <work_id>`
- any validator fail means `HOLD` until fixed
- validator scope is limited to candidate/canon/working-synthesis docs
- checklist audits, integration handoff notes, and retire notes are not promotion targets and are outside this gate

## 5. Material Compliance Self-Check

The audit must answer all of the following with `yes` or `no`:

- `strict first-block window uses 2~6 only`
- `block 1 is not used as opening cider proof`
- `block 7+ is not used as opening rescue`
- `ledger contains exact rows 2, 3, 4, 5, 6`
- `no ledger row is blank`
- `every selection-ready row has has_cider true`
- `bridge_or_payback_note is not used to rescue a false row`
- `block 6 is not pain_only_exit`
- `promotion verdict matches the ledger`

If any answer is `no`, downgrade before finalizing.

## 6. Promotion Verdict Rule

- `PASS`
  - all self-check items are `yes`
  - all `2~6` rows pay in-block
  - first-block proof, reevaluation, token, and next gate are all visible
- `HOLD`
  - one or more rows are false
  - one or more rows are blank
  - opening relies on block `1` or block `7+`
  - `bridge_or_payback_note` is carrying the opening instead of receipt
- `REJECT`
  - protagonist engine itself breaks the house law
  - opening is pain-only by design
  - no credible first-block visible token exists

## 7. Return-To-Sender Smells

Reject the material benchmark immediately if you see:

- `초반에 사이다 있음` without exact `2~6` rows
- `block 1 opener counts as first-block cider`
- `block 7 reward rescues opening`
- `false row is okay because the next block will pay`
- `bridge_or_payback_note` used as main proof of readiness
- `selection-ready` claimed while any `has_cider: false` row remains

## 8. One-Line Rule

`Draft may expose holes, but promotion may not hide them.`
