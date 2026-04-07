# 쓰레기통 상속 Material Benchmark Prompt

Date: 2026-04-07
Status: active
Document Type: external model prompt
Benchmark Type: material
Intended Report Path: `docs/2026-04-07/material_benchmark_chaebol_ent_empire_external_report.md`

## Mission

Run a read-only material benchmark for `chaebol_ent_empire` only.
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
- inspect the `Readiness Claim` or `Readiness Declaration` directly
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
4. `material_ssot/20_pitch/canon/chaebol_ent_empire.md`
5. this prompt

## Assigned Target

- target id: `chaebol_ent_empire`
- benchmark type: `material`
- family: `blockguide`
- Pitch: `material_ssot/20_pitch/canon/chaebol_ent_empire.md`

## Watchpoint

- canon recheck only; do not drift into downstream pair scoring; do not claim new promotion from an already canon source

## Promotion Gate Boundary

- this benchmark report is not canon lock and not `Phase0` promotion
- promotion intent for this run: `none`
- for this run, no promotion gate execution is requested
- do not fabricate promotion-gate success inside the report

## Required Output

Create the final markdown report directly at:

- `docs/2026-04-07/material_benchmark_chaebol_ent_empire_external_report.md`

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
- if verdict is `PASS`, make clear that promotion still requires a separate gate run
- use `PASS / HOLD / REJECT`, not pair grades
- if the doc is exploratory only, say `HOLD`, not `PASS`
- last line must be:
  - `read-only material benchmark audit complete; no pitch files mutated`
