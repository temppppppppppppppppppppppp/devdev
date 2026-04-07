# External-Model Benchmark Operation Harness v1

Date: 2026-04-07
Status: active
Scope: reusable execution harness for external-model read-only benchmark audits

## 1. Role

This harness exists to stop external models from silently changing the benchmark.

Use it whenever `Opus`, `Sonnet`, or another external model is asked to run:

- pair benchmark
- material benchmark
- re-benchmark after repair
- grade confirmation

This harness governs **execution discipline**, not story taste.

Pair rubric and material rubric are not interchangeable.

- pair benchmark must follow `production-pair-benchmark-spec-v1.md`
- material benchmark must follow `20_pitch/material-benchmark-readiness-harness-v1.md`
- benchmark mode never self-promotes a target into `selection-ready`, `canon`, or `Phase0-ready`
- any real material promotion still requires `scripts/material_promotion_gate.py`

Operator launch guidance lives in:

- `external-model-benchmark-launch-playbook-v1.md`
- `external-model-benchmark-prompt-template-v1.md`
- `external-model-material-benchmark-one-shot-order-template-v1.md`

## 2. Default Launch Mode

- default parallel width: `3 terminals max`
- one terminal = one pair or one benchmark target only
- benchmark mode is `read-only`
- allowed write target in benchmark mode:
  - benchmark report
  - bounded audit note
- not allowed in benchmark mode:
  - `TR` edit
  - `BI` edit
  - `work_guard` edit
  - alias promotion

If a target is too large for a single terminal, split by target, not by rubric.

## 2A. Target-Type Split

There are only two valid benchmark target types.

### 2A.1 Pair Benchmark

- use pair benchmark laws in Sections `3` through `11`
- output the pair benchmark report shape
- final grade may be `GREENPLUS / GREEN / YELLOW / RED`

### 2A.2 Material Benchmark

- use this harness only for dispatch discipline and anti-drift rules
- use `20_pitch/material-benchmark-readiness-harness-v1.md` for actual scoring law and report shape
- final verdict may be `PASS / HOLD / REJECT`
- external model may describe promotion readiness, but may not self-certify promotion
- if operator wants canon or `Phase0` promotion after the report, operator must separately run:
  - `python -X utf8 scripts/material_promotion_gate.py --stage canon --path <candidate-md>`
  - `python -X utf8 scripts/material_promotion_gate.py --stage phase0 --path <pitch-md> --work-id <work_id>`

## 3. Hard Laws

### 3.1 Pair Hard Laws

- `P0` is always **6 gates**
- `P1` is always **10 axes**
- `P1` scoring is always **0 / 1 / 2**
- `P1` total is always **20**
- `P0 gates 1~4` must use `TR blocks 2~6` only
- `TR block 1` may explain setup, but cannot pass `P0 gates 1~5`
- `TR block 7+` cannot rescue missing first-block evidence
- `gate 6` must be anchored to `BI` promise and `TR 1~3`, not to `work_guard` alone
- every `TR` block must be scanned individually for `has_cider: true/false`
- one `no-cider block` means `YELLOW ceiling`
- grade must obey active cap rules even if raw score is high

### 3.2 Material Hard Laws

- opening readiness uses exact rows `2, 3, 4, 5, 6` only
- `block 1` is setup or innocence context only
- `block 7+` is late rescue and invalid for opening readiness
- every row in the first-block ledger must be reviewed individually
- one `has_cider: false` row means `not selection-ready`
- `bridge_or_payback_note` may explain a thin receipt, but may not rescue a false row
- `pain_only_exit: true` at `block 6` means `HOLD`
- benchmark report must not claim canon or `Phase0` promotion as already granted
- any canon or `Phase0` claim without a separate promotion-gate pass is non-compliant

## 4. Forbidden Substitutions

The external model must not do any of the following:

- replace `P0 6 gates` with `4/4`, `5 gates`, or any custom subset
- replace `P1 10 axes x 0/1/2 = 20` with `5-point`, `0~10`, `/40`, `/100`, or weighted custom math
- treat `TR block 1` as first-block cider proof
- treat `TR block 7+` as a rescue for missing `P0 gates 1~4`
- use `work_guard` alone as primary proof for `gate 6`
- count `later payoff` as same-block cider
- count literal `reward != 없다` as automatic cider
- run a vibes-only scan without exact block numbers
- output a grade before completing the full-block cider scan
- mutate pair files in benchmark mode
- reuse pair scoring math for a material readiness audit
- claim `selection-ready` or `Phase0-ready` without exact ledger rows `2~6`
- use `block 1` or `block 7+` as material opening rescue
- use `bridge_or_payback_note` as proof that a false ledger row is acceptable
- treat a benchmark report itself as promotion-gate output

If any forbidden substitution happens, the report is non-compliant and must be sent back.

## 5. Required Execution Sequence

### 5.1 Pair Sequence

1. resolve target from manifest
2. read benchmark spec
3. read this harness
4. extract only benchmark-relevant `WG` anchors
5. extract only benchmark-relevant `BI` anchors
6. inspect `TR 1~10`
7. score `P0 gates 1~4` from `TR 2~6`
8. run full-block cider scan across the whole `TR`
9. spot-check flagged no-cider blocks and immediate neighbors
10. apply cap rules
11. score `P1`
12. run compliance self-check
13. write report

### 5.2 Material Sequence

1. resolve target from manifest or explicit candidate path
2. read `20_pitch/material-benchmark-readiness-harness-v1.md`
3. read this harness
4. read any required family or pitch-selection order
5. inspect the target pitch doc only
6. extract the exact first-block ledger rows `2~6`
7. verify readiness claim against the ledger
8. apply `PASS / HOLD / REJECT`
9. run compliance self-check
10. write report
11. if operator later wants promotion, stop and hand off to `material_promotion_gate.py`

## 6. Chunk-Safe Rule

- do not raw-full-read a large `TR` if fixed-window scan is enough
- do not raw-full-read a large `BI` if field extraction is enough
- preferred `TR` windows:
  - `1~10`
  - `11~20`
  - `21~30`
  - `31~40`
  - `41~50`
  - `51~60`
  - `61~70`
- preferred `BI` extraction:
  - early promise
  - `success_device`
  - `cider_point`
  - `CommercialCode`
  - innocence setup
- preferred `WG` extraction:
  - `one_line_truth`
  - `mandatory_scene_engines`
  - `evaluation_thresholds`
  - `custom_rules`
  - `tracking_slots`

## 7. Required Report Shape

### 7.1 Pair Report Shape

Every pair benchmark report must use this section order exactly:

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

### 7.2 Material Report Shape

Every material benchmark report must use this section order exactly:

1. `Pitch Identity`
2. `Material Compliance Self-Check`
3. `First-Block Cider Ledger Review`
4. `Planning Candidate 7 Questions`
5. `Work-Guard Freeze Check`
6. `Promotion Verdict`
7. `Fix Queue`

## 8. Compliance Self-Check Contract

### 8.1 Pair Self-Check

The pair benchmark report must explicitly answer all items below with `yes` or `no`.

- `P0 uses 6 gates only`
- `P1 uses 10 axes x 0/1/2 only`
- `P1 total is 20 only`
- `gates 1~4 are anchored in TR 2~6 only`
- `gate 6 is anchored in BI + TR 1~3 only`
- `full-block cider scan covered every TR block`
- `exact no-cider block numbers are listed, or none`
- `grade obeys any no-cider block -> YELLOW ceiling`
- `pair files were not mutated`

If any answer is `no`, the model must revise before finalizing.

### 8.2 Material Self-Check

The material benchmark report must explicitly answer all items below with `yes` or `no`.

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

If any answer is `no`, the model must revise before finalizing.

## 9. Return-To-Sender Rules

### 9.1 Pair Return-To-Sender Rules

Send the pair report back immediately if any of these appear:

- `P0 4/4`
- `P0 5/5`
- `P1 4.5/5`
- `P1 8.4/10`
- `P1 28/40`
- `P1 91/100`
- `gate 6` proved mainly by `work_guard`
- `block 1` counted as first-block cider
- `block 7+` used to rescue a failed first block
- no exact no-cider block numbers
- no full-block scan summary
- `GREEN` or `GREENPLUS` despite any no-cider block

### 9.2 Material Return-To-Sender Rules

Send the material report back immediately if any of these appear:

- `selection-ready` without exact ledger rows `2~6`
- `Phase0-ready` without exact ledger rows `2~6`
- `block 1 opener counts as opening cider`
- `block 7 reward rescues opening`
- `bridge_or_payback_note` is used as main rescue proof
- `benchmark report itself means promotion is done`
- no explicit statement that promotion gate is separate
- pair grade language such as `GREENPLUS / GREEN / YELLOW / RED` inside a material verdict

## 10. Operator Acceptance Checklist

### 10.1 Pair Acceptance Checklist

Before accepting a pair benchmark report, verify:

- section order matches the required shape
- `Compliance Self-Check` is present
- `P0` is 6 gates
- `P1` is 10 axes / total 20
- full-block cider scan names exact no-cider blocks or `none`
- provisional grade matches active caps
- last line confirms read-only mutation status

### 10.2 Material Acceptance Checklist

Before accepting a material benchmark report, verify:

- section order matches the material report shape
- `Material Compliance Self-Check` is present
- exact ledger rows `2~6` are reviewed
- readiness verdict matches the ledger
- no block `1` or block `7+` rescue language exists
- report does not pretend promotion is already granted
- if promotion is desired, operator separately runs `material_promotion_gate.py`

## 11. Last Line Contract

Pair benchmark-mode reports must end with:

- `read-only true benchmark audit complete; no pair files mutated`

Material benchmark-mode reports must end with:

- `read-only material benchmark audit complete; no pitch files mutated`

Repair-mode reports must not use either benchmark last line.
