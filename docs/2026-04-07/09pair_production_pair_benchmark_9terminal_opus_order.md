# 09-Pair Production Pair Benchmark 9-Terminal Opus Order

Date: 2026-04-07
Status: active
Document Type: bounded parallel benchmark order
Canonical Path: `docs/2026-04-07/09pair_production_pair_benchmark_9terminal_opus_order.md`
Scope: live numbered `01-09` `TR/BI` pairs only
Execution Mode: `9 terminals / Opus / 1 pair per terminal / read-only benchmark audit / direct report write when available / no repair / no pair mutation`
Final Merge Owner: `human operator`
Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`

## 1. Purpose

This order answers one bounded question only:

- across the live numbered `01-09` `TR/BI` pairs, what is each pair's current grade under `production-pair-benchmark-spec-v1`, which hard gates fail, which blocks fail the full-block cider scan, which cap rules are active, and what are the top `3` bounded repair units when the pair is `YELLOW` or `RED`

This is not:

- direct `TR` repair
- direct `BI` repair
- prompt rewriting
- `TR 58-70` completion work
- promotion or alias update execution
- full-wave redesign
- pair mutation of any kind

This order exists so that `9` parallel model lanes judge the same `9` pairs with the same ruler before any repair wave starts.

## 2. Why 9 Terminals

- current live benchmark sweep target is `01-09`
- `1 terminal = 1 pair` is the cleanest no-collision ownership model
- each terminal can stay read-only and pair-local
- later human merge becomes easier because every report shares one fixed output shape

Pair `10` is excluded from this wave on purpose:

- the operator requested a `9-terminal` split
- pair `10` already carries a separate instability history and should stay in its own repair lane instead of contaminating the clean `01-09` benchmark pass

## 3. Evidence Basis

Primary policy anchors:

1. `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
2. `material_ssot/20_pitch/cider-doctrine-v1.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. family integrated order:
   - pairs `01-08`: `docs/blockguide/SSOT_blockguide-integrated-order.md`
   - pair `09`: `docs/wuxguide/SSOT_wuxguide-integrated-order.md`
5. this order file

Interpretation rule:

- `production-pair-benchmark-spec-v1.md` is the top grading law for this survey
- `cider-doctrine-v1.md` clarifies the first-block reward contract
- `material-revival-ladder-harness.md` caps repair ambition at the smallest profitable scope
- for `P0` gates `1~4`, the only valid first-block evidence window is `TR blocks 2~6`

## 4. Inventory

Confirmed live benchmark inventory:

| Pair | TR | BI | Family |
| --- | --- | --- | --- |
| `01` | `treatments/01_tr_투자물_골든_카나리아 테스트_canonical_v1.json` | `bible/01_bi_투자물_골든_카나리아 테스트_canonical_v1.json` | `blockguide` |
| `02` | `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` | `bible/02_bi_chaebol_allowance_zero.json` | `blockguide` |
| `03` | `treatments/03_chaebol_ent_empire_tr_block_070_draft.json` | `bible/03_bi_chaebol_ent_empire.json` | `blockguide` |
| `04` | `treatments/04_defense_defect_engineer_tr_block_070_draft.json` | `bible/04_bi_defense_defect_engineer.json` | `blockguide` |
| `05` | `treatments/05_failed_future_ceo_intern_tr_block_070_draft.json` | `bible/05_bi_failed_future_ceo_intern.json` | `blockguide` |
| `06` | `treatments/06_gatekeeper_heir_tr_block_070_draft.json` | `bible/06_bi_gatekeeper_heir.json` | `blockguide` |
| `07` | `treatments/07_office_checkup_next_day_tr_block_070_draft.json` | `bible/07_bi_office_checkup_next_day.json` | `blockguide` |
| `08` | `treatments/08_pantech_cyworld_reborn_tr_block_070_draft.json` | `bible/08_bi_pantech_cyworld_reborn.json` | `blockguide` |
| `09` | `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json` | `bible/09_bi_wuxia_heavenly_physician.json` | `wuxguide` |

## 5. Required Read Order

Each terminal should read in this order before judging its assigned pair:

1. `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
2. `material_ssot/20_pitch/cider-doctrine-v1.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. family integrated order for the assigned pair
5. this order file
6. assigned terminal prompt file
7. assigned `TR`
8. assigned `BI`

## 6. Bounded Audit Questions

Every terminal should answer only these questions:

1. which `P0` hard gates pass and fail
2. which blocks fail the full-block cider scan
3. which cap rules are active
4. what is the `P1` score table and total
5. what is the provisional grade
6. if the pair is `YELLOW` or `RED`, what are the top `3` repair units
7. if the pair is `GREEN` or `GREENPLUS`, what alias note or residual risk should be recorded

Do not widen into:

- full rewrite planning
- new premise design
- treatment patching
- bible regeneration
- block-by-block rewrite outlines
- speculative promotion

## 7. Output Contract

Every terminal report must use this section order exactly:

1. `Pair Identity`
2. `P0 Hard Gates`
3. `Full-Block Cider Scan`
4. `Active Cap Rules`
5. `P1 Score Table`
6. `Provisional Grade`
7. `Top 3 Repair Units or Alias Note`
8. `Concise Rationale`

Additional rules:

- cite concrete field names, block numbers, or pair-specific anchors where possible
- keep benchmark vocabulary exact:
  - `P0 hard gates`
  - `full-block cider scan`
  - `cap rules`
  - `P1 score`
  - `provisional grade`
  - `top 3 repair units`
- the full-block cider scan must report:
  - total `TR` block count
  - no-cider block count
  - exact no-cider block numbers, or `none`
- do not repair inside the report
- do not recommend full-wave surgery by default
- write directly to the intended report path if the environment allows file creation
- if direct file write is unavailable, emit the markdown body only so the operator can paste it into the intended report path
- if a `P0` gate `1~4` is passed using `TR block 1` or `TR block 7+`, that reading is invalid and the report must be corrected before merge
- last line must be:
  - `read-only benchmark audit complete; no pair files mutated`

## 8. Grade Discipline

Non-negotiable grading rules from the benchmark spec:

- `block 1` means `TR blocks 2~6` only for benchmark evidence
- `TR block 1` is setup context only; it cannot satisfy `P0` gates `1~5`
- `TR block 7+` cannot rescue a missing `P0` gate `1~4`
- if there is no visible `cider` inside block 1, the pair has a `YELLOW ceiling`
- every `TR` block must survive the full-block cider scan
- if any one `TR` block is `has_cider: false`, the pair has a `YELLOW ceiling`
- proof alone is not `cider`
- block 1 must land:
  - protagonist-only proof
  - reevaluation
  - visible reward token
  - next gate opening
- if the first concrete reward or first real token lands at `TR block 7+`, gate `1` fails
- two or more `P0` hard gate failures should start from a `RED` lane

## 9. Terminal Ownership

| Terminal | Pair | Prompt | Intended Report Path |
| --- | --- | --- | --- |
| `01` | `01` | `docs/2026-04-07/09pair_benchmark_terminal01_pair01_prompt.md` | `docs/2026-04-07/09pair_benchmark_terminal01_pair01_report.md` |
| `02` | `02` | `docs/2026-04-07/09pair_benchmark_terminal02_pair02_prompt.md` | `docs/2026-04-07/09pair_benchmark_terminal02_pair02_report.md` |
| `03` | `03` | `docs/2026-04-07/09pair_benchmark_terminal03_pair03_prompt.md` | `docs/2026-04-07/09pair_benchmark_terminal03_pair03_report.md` |
| `04` | `04` | `docs/2026-04-07/09pair_benchmark_terminal04_pair04_prompt.md` | `docs/2026-04-07/09pair_benchmark_terminal04_pair04_report.md` |
| `05` | `05` | `docs/2026-04-07/09pair_benchmark_terminal05_pair05_prompt.md` | `docs/2026-04-07/09pair_benchmark_terminal05_pair05_report.md` |
| `06` | `06` | `docs/2026-04-07/09pair_benchmark_terminal06_pair06_prompt.md` | `docs/2026-04-07/09pair_benchmark_terminal06_pair06_report.md` |
| `07` | `07` | `docs/2026-04-07/09pair_benchmark_terminal07_pair07_prompt.md` | `docs/2026-04-07/09pair_benchmark_terminal07_pair07_report.md` |
| `08` | `08` | `docs/2026-04-07/09pair_benchmark_terminal08_pair08_prompt.md` | `docs/2026-04-07/09pair_benchmark_terminal08_pair08_report.md` |
| `09` | `09` | `docs/2026-04-07/09pair_benchmark_terminal09_pair09_prompt.md` | `docs/2026-04-07/09pair_benchmark_terminal09_pair09_report.md` |

Ownership rule:

- one terminal owns one pair
- do not merge across pairs inside the terminal output
- do not comment on pair `10`

## 10. Human Launch Sequence

Recommended operator flow:

1. open `9` terminals
2. assign one prompt doc per terminal
3. paste the matching prompt into `Opus`
4. if the terminal has workspace write access, let `Opus` write directly to the intended report path
5. if the terminal cannot write files, collect the markdown output and save it manually at the intended report path
6. run merge and disagreement review only after all `9` land

## 11. Merge Reminder

If multiple terminals disagree with house intuition:

- trust the benchmark spec first
- check whether the disagreement comes from `P0` evidence, cap-rule reading, or score inflation
- repair the scoring note, not the pair, until the evidence basis is stable
