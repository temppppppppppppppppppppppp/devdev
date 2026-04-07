# 10pair True Benchmark Terminal 07 Pair 07 Prompt

Date: 2026-04-07
Status: active
Document Type: external model prompt
Canonical Path: `docs/2026-04-07/10pair_true_benchmark_terminal07_pair07_prompt.md`
Parent Order: `docs/2026-04-07/10pair_true_benchmark_10terminal_opus_order.md`
Intended Report Path: `docs/2026-04-07/10pair_true_benchmark_terminal07_pair07_report.md`

## Mission

Run a read-only true benchmark audit for canonical pair `07` only.
Use `work_guard` as supporting contract evidence, but never let `work_guard` or `BI` rescue a missing `TR` receipt.
Write the final report directly to the intended report path if your environment allows file creation.

## Non-Negotiables

- read the canonical manifest first
- for `P0` gates `1~4`, use `TR blocks 2~6` only
- run a full-block cider scan across every `TR` block
- one no-cider block means `YELLOW ceiling`
- every pass/fail claim must cite exact `TR` block numbers and specific `BI` or `work_guard` anchors when relevant
- if evidence is ambiguous, downgrade; do not infer upward from vibe, premise quality, or later payoff
- never substitute a custom rubric; `P0` must stay `6 gates`, and `P1` must stay `10 axes x 0/1/2 = 20`

## Context Safety Rule

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

## Compliance Self-Check Before Final Write

Before writing the final report, verify all of the following are `yes`:

- `P0 uses 6 gates only`
- `P1 uses 10 axes x 0/1/2 only`
- `P1 total is 20 only`
- `gates 1~4 are anchored in TR 2~6 only`
- `gate 6 is anchored in BI + TR 1~3 only`
- `full-block cider scan covered every TR block`
- `exact no-cider block numbers are listed, or none`
- `grade obeys any no-cider block -> YELLOW ceiling`
- `pair files were not mutated`

If any item is `no`, revise before writing the final report.

## Read Order

1. `docs/2026-04-07/01_10_canonical_pair_manifest.md`
2. `material_ssot/00_governance/external-model-benchmark-operation-harness-v1.md`
3. `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
4. `material_ssot/20_pitch/cider-doctrine-v1.md`
5. `docs/narrative-router/material-revival-ladder-harness.md`
6. `docs/blockguide/SSOT_blockguide-integrated-order.md`
7. `work_guards/07_office_checkup_next_day.yaml`
8. `treatments/07_office_checkup_next_day_tr_block_070_draft.json`
9. `bible/07_bi_office_checkup_next_day.json`
10. `docs/2026-04-07/10pair_true_benchmark_10terminal_opus_order.md`
11. this prompt

## Assigned Pair

- pair id: `07`
- family: `blockguide`
- WG: `work_guards/07_office_checkup_next_day.yaml`
- TR: `treatments/07_office_checkup_next_day_tr_block_070_draft.json`
- BI: `bible/07_bi_office_checkup_next_day.json`

## Watchpoint

- do not let strong opening conversion hide later rewardless valleys
- explicitly check for `rewardless pain blocks 2 in a row` and long `no-cider drought` zones

## Required Output

Create the final markdown report directly at:

- `docs/2026-04-07/10pair_true_benchmark_terminal07_pair07_report.md`

Fallback:

- if you cannot write files in your environment, output the same markdown body only, with no extra preface or postscript

Use these sections exactly:

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

Rules:

- inside `Compliance Self-Check`, answer every required item with `yes` or `no`
- report total `TR` block count, no-cider block count, exact no-cider block numbers, and longest no-cider drought length
- inside `Full-Block Cider Scan`, include a short window summary for `1~10 / 11~20 / 21~30 / 31~40 / 41~50 / 51~60 / 61~70`
- if no cap rule is active, say `none`
- if the grade is `GREEN` or `GREENPLUS`, give an alias note or residual risk instead of repair units
- do not propose full-wave surgery
- last line must be:
  - `read-only true benchmark audit complete; no pair files mutated`
