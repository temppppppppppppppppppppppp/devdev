# External-Model Benchmark Prompt Template v1

Date: 2026-04-07
Status: active
Scope: reusable prompt template for future `material` or `pair` benchmark dispatch

Replace every bracketed field before launch.

## Prompt Body

```md
# [Target Label] Benchmark Prompt

Date: [YYYY-MM-DD]
Status: active
Document Type: external model prompt
Benchmark Type: [pair/material]
Intended Report Path: `[report path]`

## Mission

Run a read-only benchmark audit for `[target id]` only.
If `Benchmark Type = pair`, use `work_guard` as supporting contract evidence, but never let `work_guard` or `BI` rescue a missing `TR` receipt.
If `Benchmark Type = material`, audit readiness from the target pitch markdown only and do not pretend this report itself is promotion-gate output.
Write the final report directly to the intended report path if your environment allows file creation.

## Non-Negotiables

- read the target definition or manifest first
- never substitute a custom rubric
- if evidence is ambiguous, downgrade; do not infer upward from vibe, premise quality, or later payoff

If `Benchmark Type = pair`:

- for `P0` gates `1~4`, use `TR blocks 2~6` only
- `gate 6` must be anchored in `BI + TR 1~3`
- run a full-block cider scan across every `TR` block
- one no-cider block means `YELLOW ceiling`
- every pass/fail claim must cite exact `TR` block numbers and specific `BI` or `work_guard` anchors when relevant
- `P0` must stay `6 gates`, and `P1` must stay `10 axes x 0/1/2 = 20`

If `Benchmark Type = material`:

- opening readiness uses exact ledger rows `2, 3, 4, 5, 6` only
- `block 1` is setup only and cannot rescue opening readiness
- `block 7+` cannot rescue opening readiness
- any `has_cider:false` row means `not selection-ready`
- `bridge_or_payback_note` may explain a thin receipt, but cannot rescue a false row
- use `PASS / HOLD / REJECT`, not pair grade language
- this report is not promotion-gate output

## Context Safety Rule

If `Benchmark Type = pair`:

- never raw-full-read the entire `BI` or full `TR` into context if targeted extraction and window scan can answer the benchmark
- first extract `WG` and `BI` anchors only:
  - early promise
  - `success_device`
  - `cider_point`
  - `CommercialCode` or semantic equivalent
  - `one_line_truth`
  - `mandatory_scene_engines`
  - `evaluation_thresholds`
  - `custom_rules` / `tracking_slots`
- then inspect `TR blocks 1~10`; score `P0` gates `1~4` from `TR blocks 2~6` only
- then scan `TR` in windows `1~10 / 11~20 / 21~30 / 31~40 / 41~50 / 51~60 / 61~70` and build a terse blockwise cider ledger
- then reopen only flagged `no-cider` blocks and their immediate neighbors for spot-check confirmation
- if a field name does not exist in this family, extract the semantic equivalent only; do not widen to a full raw read by default

If `Benchmark Type = material`:

- do not widen the read beyond the target pitch markdown and the readiness harness unless the operator explicitly adds another source
- inspect the `First-Block Cider Ledger` rows `2~6` directly
- inspect the `Readiness Claim` directly
- if the ledger is missing or malformed, downgrade immediately
- do not invent a parallel material scoring scale

## Compliance Self-Check Before Final Write

If `Benchmark Type = pair`, verify all of the following are `yes`:

- `P0 uses 6 gates only`
- `P1 uses 10 axes x 0/1/2 only`
- `P1 total is 20 only`
- `gates 1~4 are anchored in TR 2~6 only`
- `gate 6 is anchored in BI + TR 1~3 only`
- `full-block cider scan covered every TR block`
- `exact no-cider block numbers are listed, or none`
- `grade obeys any no-cider block -> YELLOW ceiling`
- `pair files were not mutated`

If `Benchmark Type = material`, verify all of the following are `yes`:

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

If any item is `no`, revise before writing the final report.

## Read Order

If `Benchmark Type = pair`:

1. `[manifest or target-definition path]`
2. `material_ssot/00_governance/external-model-benchmark-operation-harness-v1.md`
3. `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
4. `material_ssot/20_pitch/cider-doctrine-v1.md`
5. `[revival or family integrated order path]`
6. `[work_guard path]`
7. `[TR path]`
8. `[BI path]`
9. this prompt

If `Benchmark Type = material`:

1. `[target-definition path]`
2. `material_ssot/00_governance/external-model-benchmark-operation-harness-v1.md`
3. `material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md`
4. `material_ssot/20_pitch/pitch-selection-checklist.md`
5. `[target pitch path]`
6. this prompt

## Assigned Target

- target id: `[id]`
- benchmark type: `[pair/material]`
- family: `[family or n/a]`
- WG: `[work_guard path or n/a]`
- TR: `[TR path or n/a]`
- BI: `[BI path or n/a]`
- Pitch: `[pitch path or n/a]`

## Watchpoint

- [target-specific anti-cheat note]

## Promotion Gate Boundary

- this benchmark report is not canon lock and not `Phase0` promotion
- if operator wants actual material promotion after this report, operator must separately run:
  - pre-canon: `python -X utf8 scripts/material_promotion_gate.py --stage canon --path <candidate-md>`
  - pre-Phase0: `python -X utf8 scripts/material_promotion_gate.py --stage phase0 --path <pitch-md> --work-id <work_id>`
- do not fabricate promotion-gate success inside the report

## Required Output

Create the final markdown report directly at:

- `[report path]`

Fallback:

- if you cannot write files in your environment, output the same markdown body only, with no extra preface or postscript

If `Benchmark Type = pair`, use these sections exactly:

1. `Pair Identity`
2. `Compliance Self-Check`
3. `Evidence Anchor Table`
4. `P0 Hard Gates`
5. `Full-Block Cider Scan`
6. `Active Cap Rules`
7. `P1 Score Table`
8. `Provisional Grade`
9. `Top 3 Repair Units or Alias Note`
10. `Concise Rationale`

If `Benchmark Type = material`, use these sections exactly:

1. `Pitch Identity`
2. `Material Compliance Self-Check`
3. `First-Block Cider Ledger Review`
4. `Planning Candidate 7 Questions`
5. `Work-Guard Freeze Check`
6. `Promotion Verdict`
7. `Fix Queue`

Rules:

- for pair reports:
  - inside `Compliance Self-Check`, answer every required item with `yes` or `no`
  - report total `TR` block count, no-cider block count, exact no-cider block numbers, and longest no-cider drought length
  - inside `Full-Block Cider Scan`, include a short window summary for `1~10 / 11~20 / 21~30 / 31~40 / 41~50 / 51~60 / 61~70`
  - if no cap rule is active, say `none`
  - if the grade is `GREEN` or `GREENPLUS`, give an alias note or residual risk instead of repair units
  - do not propose full-wave surgery
  - last line must be:
    - `read-only true benchmark audit complete; no pair files mutated`
- for material reports:
  - inside `Material Compliance Self-Check`, answer every required item with `yes` or `no`
  - list exact ledger rows `2, 3, 4, 5, 6`
  - if verdict is `PASS`, make clear that promotion still requires a separate gate run
  - use `PASS / HOLD / REJECT`, not pair grades
  - last line must be:
    - `read-only material benchmark audit complete; no pitch files mutated`
```
