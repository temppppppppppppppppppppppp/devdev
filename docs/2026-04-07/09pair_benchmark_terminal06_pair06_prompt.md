# Pair Benchmark Terminal 06 Pair 06 Prompt

Date: 2026-04-07
Status: active
Document Type: external model prompt
Canonical Path: `docs/2026-04-07/09pair_benchmark_terminal06_pair06_prompt.md`
Parent Order: `docs/2026-04-07/09pair_production_pair_benchmark_9terminal_opus_order.md`
Intended Report Path: `docs/2026-04-07/09pair_benchmark_terminal06_pair06_report.md`

## Mission

Run a read-only benchmark audit for pair `06` only.
Do not repair anything. Do not discuss any other pair.
Write the final report directly to the intended report path if your environment allows file creation.

## Strict Window Rule

- for `P0` gates `1~4`, use `TR blocks 2~6` only
- `TR block 1` may explain setup or innocence, but it cannot satisfy first-block gates
- `TR block 7+` cannot rescue a missing first-block reward, proof, reevaluation, or token
- gate `5` may mention `TR block 7+` only to confirm that a token already earned by `TR block 6` opened the next gate
- if the first concrete `cider` lands at `TR block 7+`, gate `1` fails and the pair has a `YELLOW ceiling`

## Full-Block Cider Scan Rule

- scan every `TR` block from `1` to the final block
- mark each block `has_cider: true/false`
- a block counts as `has_cider: true` only if it contains at least one reader-countable payback:
  - visible reward token
  - weighted reevaluation receipt
  - protection receipt
  - authority or access shift
  - recovery asset that offsets same-block pain
  - explicit next-card or next-gate receipt
- setup-only, explanation-only, wait-only, pain-only, humiliation-only, failure-only, or `later payoff only` blocks are `has_cider: false`
- if any block is `has_cider: false`, the pair has a `YELLOW ceiling`
- list the exact no-cider block numbers in the report

## Read Order

1. `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
2. `material_ssot/20_pitch/cider-doctrine-v1.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/blockguide/SSOT_blockguide-integrated-order.md`
5. `docs/2026-04-07/09pair_production_pair_benchmark_9terminal_opus_order.md`
6. this prompt
7. `treatments/06_gatekeeper_heir_tr_block_070_draft.json`
8. `bible/06_bi_gatekeeper_heir.json`

## Assigned Pair

- pair id: `06`
- family: `blockguide`
- TR: `treatments/06_gatekeeper_heir_tr_block_070_draft.json`
- BI: `bible/06_bi_gatekeeper_heir.json`

## Watchpoint

- this pair is a proof-scene precision benchmark, but do not auto-promote it
- verify that hidden-asset discovery converts into reevaluation and entry-ticket reward inside block 1

## Required Output

Create the final markdown report directly at:

- `docs/2026-04-07/09pair_benchmark_terminal06_pair06_report.md`

Fallback:

- if you cannot write files in your environment, output the same markdown body only, with no extra preface or postscript, so the operator can paste it into the path above

Use these sections exactly:

1. `Pair Identity`
2. `P0 Hard Gates`
3. `Full-Block Cider Scan`
4. `Active Cap Rules`
5. `P1 Score Table`
6. `Provisional Grade`
7. `Top 3 Repair Units or Alias Note`
8. `Concise Rationale`

Rules:

- use benchmark vocabulary exactly
- cite concrete block or field anchors where possible
- report total `TR` block count, no-cider block count, and exact no-cider block numbers
- if no cap rule is active, say `none`
- if the grade is `GREEN` or `GREENPLUS`, give an alias note or residual risk instead of repair units
- do not propose full-wave surgery
- do not ask for a different documentation path
- do not pass `P0` gates `1~4` with `TR block 1` or `TR block 7+` evidence
- do not grade above `YELLOW` if even one block fails the full-block cider scan
- last line must be:
  - `read-only benchmark audit complete; no pair files mutated`
