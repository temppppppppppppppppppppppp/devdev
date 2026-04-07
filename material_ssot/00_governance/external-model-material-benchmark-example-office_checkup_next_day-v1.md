# External-Model Material Benchmark Example: office_checkup_next_day v1

Date: 2026-04-07
Status: active
Scope: filled example for a read-only canon material recheck

Use this when the operator wants a fully filled material benchmark prompt for the active canon pitch `office_checkup_next_day`.

Promotion intent for this example is `none`.

```md
# office_checkup_next_day Material Benchmark Prompt

Date: 2026-04-07
Status: active
Document Type: external model prompt
Benchmark Type: material
Intended Report Path: `docs/2026-04-07/material_benchmark_office_checkup_next_day_report.md`

## Mission

Run a read-only material benchmark for `office_checkup_next_day` only.
Audit readiness from the target pitch markdown only.
Do not pretend this report itself is canon lock or `Phase0` promotion.
Write the final report directly to the intended report path if your environment allows file creation.

## Non-Negotiables

- opening readiness uses exact ledger rows `2, 3, 4, 5, 6` only
- `block 1` is setup only and cannot rescue opening readiness
- `block 7+` cannot rescue opening readiness
- any `has_cider:false` row means `not selection-ready`
- `bridge_or_payback_note` may explain a thin receipt, but cannot rescue a false row
- use `PASS / HOLD / REJECT`, not pair grade language
- this report is not promotion-gate output
- if evidence is ambiguous, downgrade
- never substitute a custom rubric

## Context Safety Rule

- do not widen the read beyond the target pitch markdown and the readiness harness unless the operator explicitly adds another source
- inspect the `First-Block Cider Ledger` rows `2~6` directly
- inspect the `Readiness Declaration` directly
- if the ledger is missing or malformed, downgrade immediately
- do not invent a parallel material scoring scale

## Compliance Self-Check Before Final Write

Before writing the final report, verify all of the following are `yes`:

- `strict first-block window uses 2~6 only`
- `block 1 is not used as opening cider proof`
- `block 7+ is not used as opening rescue`
- `ledger contains exact rows 2, 3, 4, 5, 6`
- `no ledger row is blank`
- `every selection-ready row has has_cider true`
- `bridge_or_payback_note is not used to rescue a false row`
- `block 6 is not pain_only_exit`
- `promotion verdict matches the ledger`
- `benchmark report is not pretending to be promotion-gate output`
- `pitch files were not mutated`

If any item is `no`, revise before writing the final report.

## Read Order

1. `material_ssot/00_governance/external-model-benchmark-operation-harness-v1.md`
2. `material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md`
3. `material_ssot/20_pitch/pitch-selection-checklist.md`
4. `material_ssot/20_pitch/canon/office_checkup_next_day.md`
5. this prompt

## Assigned Target

- target id: `office_checkup_next_day`
- benchmark type: `material`
- family: `blockguide`
- Pitch: `material_ssot/20_pitch/canon/office_checkup_next_day.md`

## Watchpoint

- do not drift into downstream `TR/BI` pair scoring; this is a material-side canon recheck only
- do not let `block 1` opening humiliation stand in for ledger rows `2~6`
- do not call the target newly promoted; this file is already canon and this report is only a read-only readiness recheck

## Promotion Gate Boundary

- this benchmark report is not canon lock and not `Phase0` promotion
- for this example, promotion intent is `none`
- do not fabricate promotion-gate success inside the report

## Required Output

Create the final markdown report directly at:

- `docs/2026-04-07/material_benchmark_office_checkup_next_day_report.md`

Fallback:

- if you cannot write files in your environment, output the same markdown body only, with no extra preface or postscript

Use these sections exactly:

1. `Pitch Identity`
2. `Material Compliance Self-Check`
3. `First-Block Cider Ledger Review`
4. `Planning Candidate 7 Questions`
5. `Work-Guard Freeze Check`
6. `Promotion Verdict`
7. `Fix Queue`

Rules:

- inside `Material Compliance Self-Check`, answer every required item with `yes` or `no`
- list exact ledger rows `2, 3, 4, 5, 6`
- use `PASS / HOLD / REJECT`, not pair grades
- because this is a canon recheck, explain any residual risk as audit note only
- last line must be:
  - `read-only material benchmark audit complete; no pitch files mutated`
```

Operator close-out for this example:

- read the returned report
- do not run promotion gate, because promotion intent is `none`
- if the report finds drift, fix the canon doc first and then rerun the same prompt
