# External-Model Benchmark Launch Playbook v1

Date: 2026-04-07
Status: active
Scope: human operator playbook for future `material` or `pair` benchmark dispatch

## 1. Role

Use this playbook when a human operator is about to ask `Opus`, `Sonnet`, or another external model to run a benchmark.

This is the dispatch layer above:

- `production-pair-benchmark-spec-v1.md`
- `external-model-benchmark-operation-harness-v1.md`
- `20_pitch/material-benchmark-readiness-harness-v1.md`
- `external-model-material-benchmark-one-shot-order-template-v1.md`

The goal is simple:

- prevent benchmark drift before the model starts
- keep benchmark mode and repair mode separate
- keep pair benchmark and material benchmark separate
- force one shared output shape every time

## 2. Default Routing

- use `Opus` for first-pass benchmark on a new target
- use `Sonnet` for:
  - re-score after a small correction
  - compliance rewrite
  - flagged-block recheck
  - short residual-risk audit
- if the target is large or ambiguous, prefer `Opus`
- if the target already has a good evidence ledger and only needs format correction, `Sonnet` is enough

## 3. Parallel Width

- default: `3 terminals max`
- one terminal = one benchmark target only
- do not run `5+` terminals unless the operator is ready to do heavy return-to-sender filtering
- if one target is huge, do not split the rubric; split the work by target or run chunk-safe inside one terminal

## 4. Mode Separation

There are only three valid lanes.

### 4.1 Pair Benchmark Mode

- read-only
- allowed writes:
  - benchmark report
  - bounded audit note
- forbidden writes:
  - `TR`
  - `BI`
  - `work_guard`
  - alias file

### 4.2 Material Benchmark Mode

- read-only
- allowed writes:
  - material benchmark report
  - bounded audit note
- forbidden writes:
  - candidate markdown
  - canon markdown
  - synthesis markdown
  - `TR`
  - `BI`
  - `work_guard`
- material verdict may be `PASS / HOLD / REJECT`
- material benchmark report is not promotion-gate output

### 4.3 Repair Mode

- scoped mutation only
- must name target blocks before launch
- must name allowed write files before launch
- must not claim final grade; re-audit is separate

### 4.4 Promotion Gate Step

- not a model judgment mode
- operator-only gate after a material write is finished
- use only when a target is being promoted into `canon` or `Phase0`
- commands:
  - pre-canon: `python -X utf8 scripts/material_promotion_gate.py --stage canon --path <candidate-md>`
  - pre-Phase0: `python -X utf8 scripts/material_promotion_gate.py --stage phase0 --path <pitch-md> --work-id <work_id>`
- if this gate has not passed, do not call the target `selection-ready`, `canon-locked`, or `Phase0-ready`

## 5. Dispatch Contract

Before launch, the operator must define:

- exact target type: `pair` or `material`
- exact target id
- exact `WG / TR / BI` paths
- exact report path
- family integrated order path
- whether this is `benchmark mode` or `repair mode`
- whether the task is:
  - full benchmark
  - re-benchmark after repair
  - compliance rewrite only
  - flagged-block recheck only

Never launch a benchmark with fuzzy labels like:

- `that office thing`
- `the current draft`
- `the yellow one`

Always launch with exact paths.

## 6. Mandatory Read Stack

### 6.1 Pair Read Stack

Every pair benchmark dispatch must instruct the model to read in this order:

1. manifest or explicit target definition
2. `external-model-benchmark-operation-harness-v1.md`
3. `production-pair-benchmark-spec-v1.md`
4. `cider-doctrine-v1.md`
5. revival or family integrated order
6. target `work_guard`
7. target `TR`
8. target `BI`
9. launch prompt

If the task is family-specific, include the correct family integrated order:

- `docs/blockguide/SSOT_blockguide-integrated-order.md`
- `docs/wuxguide/SSOT_wuxguide-integrated-order.md`
- or the correct future equivalent

### 6.2 Material Read Stack

Every material benchmark dispatch must instruct the model to read in this order:

1. explicit target definition
2. `external-model-benchmark-operation-harness-v1.md`
3. `20_pitch/material-benchmark-readiness-harness-v1.md`
4. `20_pitch/pitch-selection-checklist.md`
5. target pitch markdown
6. launch prompt

If the operator intends a real promotion after the benchmark, the promotion-gate command belongs in the operator close-out, not inside the benchmark verdict.

## 7. Mandatory Prompt Contract

### 7.1 Pair Prompt Contract

Every pair benchmark prompt must contain all of the following:

- `P0 gates 1~4 use TR 2~6 only`
- `gate 6 uses BI + TR 1~3 only`
- `full-block cider scan across every TR block`
- `any no-cider block -> YELLOW ceiling`
- `never substitute a custom rubric`
- `Compliance Self-Check Before Final Write`
- exact section order for the final report
- last-line mutation contract

Use `external-model-benchmark-prompt-template-v1.md` as the base template.

### 7.2 Material Prompt Contract

Every material benchmark prompt must contain all of the following:

- `strict first-block window uses 2~6 only`
- `block 1 is setup only and cannot rescue opening readiness`
- `block 7+ cannot rescue opening readiness`
- `first_block_cider_ledger rows 2~6 are reviewed individually`
- `any has_cider:false row means not selection-ready`
- `bridge_or_payback_note cannot rescue a false row`
- `never substitute pair grading language for material readiness`
- `material benchmark report is not promotion-gate output`
- exact material report section order
- material last-line mutation contract

If promotion is intended after the report, append an operator-only gate step with `material_promotion_gate.py`; do not ask the external model to fake gate success.

For a material-only real dispatch, prefer `external-model-material-benchmark-one-shot-order-template-v1.md` over a manually assembled prompt.

## 8. Acceptance Gate

### 8.1 Pair Acceptance Gate

Do not accept a pair benchmark report unless all of the following are present:

- `Compliance Self-Check`
- `P0 = 6 gates`
- `P1 = 10 axes x 0/1/2 = 20`
- exact no-cider block numbers or `none`
- explicit active cap table
- grade that obeys caps
- last-line mutation statement

### 8.2 Material Acceptance Gate

Do not accept a material benchmark report unless all of the following are present:

- `Material Compliance Self-Check`
- exact ledger rows `2~6`
- no `block 1` or `block 7+` opening rescue
- promotion verdict that matches the ledger
- no fake claim that canon or `Phase0` is already granted
- last-line mutation statement
- if actual promotion is desired, a separate operator gate run is queued

## 9. Return-To-Sender Macro

### 9.1 Pair Return-To-Sender Macro

If a pair benchmark drifts, send this exact correction:

```text
This report is non-compliant with production-pair-benchmark-spec-v1 and external-model-benchmark-operation-harness-v1. Re-write it without changing the evidence base. P0 must stay 6 gates, P1 must stay 10 axes x 0/1/2 = 20, gates 1~4 must be anchored in TR 2~6 only, gate 6 must be anchored in BI + TR 1~3 only, full-block cider scan must cover every TR block, exact no-cider block numbers must be listed, and any no-cider block must lock a YELLOW ceiling. Add the Compliance Self-Check section and revise before finalizing.
```

### 9.2 Material Return-To-Sender Macro

If a material benchmark drifts, send this exact correction:

```text
This report is non-compliant with material-benchmark-readiness-harness-v1 and external-model-benchmark-operation-harness-v1. Re-write it without changing the evidence base. Opening readiness must use exact ledger rows 2~6 only, block 1 and block 7+ cannot rescue the opening, any has_cider:false row means not selection-ready, bridge_or_payback_note cannot rescue a false row, and the benchmark report itself is not promotion-gate output. Add the Material Compliance Self-Check section and revise before finalizing.
```

## 10. Recommended Launch Shapes

### 10.1 First-Pass Benchmark

- `Opus`
- `1 target per terminal`
- `3 terminals max`
- use full prompt template

### 10.2 Re-Score After Repair

- `Sonnet` is acceptable
- include prior report path and repair note path
- benchmark remains read-only
- forbid silent score-scale changes

### 10.3 Compliance Rewrite

- `Sonnet`
- reuse evidence only
- no new literary judgment unless a cited line is invalid

### 10.4 Material Readiness Audit

- `Opus` for first-pass or ambiguous candidates
- `Sonnet` for compliance rewrite after a narrow document correction
- do not mix material readiness verdict with actual promotion
- if the report passes and the operator wants promotion, run `material_promotion_gate.py` separately
- for copy-paste launch, start from `external-model-material-benchmark-one-shot-order-template-v1.md`
- if the operator wants a filled reference first, see:
  - `external-model-material-benchmark-example-office_checkup_next_day-v1.md`
  - `external-model-material-benchmark-example-line_stop_deputy-v1.md`
- for report-shape training across verdicts, also see:
  - `docs/2026-04-07/material_benchmark_office_checkup_next_day_report.md`
  - `docs/2026-04-07/material_benchmark_line_stop_deputy_hold_example.md`
  - `docs/2026-04-07/material_benchmark_legacy_import_042_reject_example.md`
- for fast operator judgment before launch or acceptance, see:
  - `docs/2026-04-07/material_benchmark_pass_hold_reject_cheat_sheet.md`
- for real launch with fewer path mistakes, prefer:
  - `python -X utf8 scripts/material_benchmark_order_generator.py --pitch <pitch-md> [--promotion-intent none|canon|phase0]`
- for multi-target launch sheets across canon/intake/synthesis, prefer:
  - `python -X utf8 scripts/material_benchmark_batch_generator.py [--path <dir>] [--promotion-intent auto|none|canon|phase0]`

## 11. Failure Smells

If you see any of the following, reject immediately:

- `P0 4/4`
- `P1 4.5/5`
- `P1 8.4/10`
- `P1 28/40`
- `P1 91/100`
- `block 1 counted as first-block proof`
- `block 7+ rescues opening`
- `literal reward search only`
- `GREEN` or `GREENPLUS` with no-cider blocks still present
- `selection-ready` without exact ledger rows 2~6
- `Phase0-ready` claimed without promotion-gate output
- material report using pair grade language as its main verdict

## 12. One-Line Operating Rule

`Dispatch narrow, split pair from material, repair separately, and never let the model invent a new ruler or fake a promotion gate.`
