# 10-Pair True Benchmark 10-Terminal Opus Order

Date: 2026-04-07
Status: active
Document Type: bounded parallel benchmark order
Canonical Path: `docs/2026-04-07/10pair_true_benchmark_10terminal_opus_order.md`
Scope: canonical live numbered `01-10` `BI + TR + work_guard` bundles only
Execution Mode: `10 terminals / Opus / 1 pair per terminal / read-only true benchmark audit / direct report write when available / no repair / no pair mutation`
Final Merge Owner: `human operator`
Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`

Wave-use note:

- this order is a historical wave-specific launch pack
- for future benchmark dispatch, use:
  - `material_ssot/00_governance/external-model-benchmark-launch-playbook-v1.md`
  - `material_ssot/00_governance/external-model-benchmark-prompt-template-v1.md`

## 1. Purpose

This order answers one bounded question only:

- across the canonical live numbered `01-10` pairs, what is each pair's current grade under `production-pair-benchmark-spec-v1`, which `P0` gates fail, which blocks fail the full-block cider scan, which cap rules are active, and what are the top `3` bounded repair units when the pair is `YELLOW` or `RED`

This is not:

- direct `TR` repair
- direct `BI` repair
- `work_guard` rewrite
- prompt rewriting
- alias promotion execution
- pair mutation of any kind

## 2. Why This Wave Is `True Benchmark`

This wave is stricter than the earlier loose benchmark pass.

- `canonical manifest` is the first resolver, not filename intuition
- `work_guard` is read as intended contract evidence, but it cannot rescue a failed `TR`
- every pass/fail claim must cite exact `TR` block numbers and, when relevant, exact `BI` or `work_guard` anchors
- grading is `ceiling-first`
- ambiguity downgrades; it never promotes
- one no-cider block is enough to lock a `YELLOW ceiling`
- raw full-read of large `BI` and full `TR` blobs is forbidden when targeted extraction or window scan is enough

## 3. Governing Read Stack

Primary laws:

1. `docs/2026-04-07/01_10_canonical_pair_manifest.md`
2. `material_ssot/00_governance/external-model-benchmark-operation-harness-v1.md`
3. `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
4. `material_ssot/20_pitch/cider-doctrine-v1.md`
5. `docs/narrative-router/material-revival-ladder-harness.md`
6. family integrated order
7. assigned `work_guard`
8. assigned `TR`
9. assigned `BI`
10. this order
11. assigned terminal prompt

Interpretation rule:

- `work_guard` clarifies what the pair claims to promise
- `BI` clarifies the pair's early conversion promise and `success_device`
- `TR` decides whether that promise actually cashes out
- `work_guard` and `BI` may sharpen failure judgment, but they may not grant a pass where `TR` has no evidence
- `read` does not mean `paste the full file into context`
- for large files, use search, field extraction, and fixed windows

## 4. Canonical Inventory

Use the canonical manifest, not memory.

| Pair | Family | WG | TR | BI |
| --- | --- | --- | --- | --- |
| `01` | `blockguide` | `work_guards/01_투자물_골든_카나리아 테스트_canonical_v1.yaml` | `treatments/01_tr_투자물_골든_카나리아 테스트_canonical_v1.json` | `bible/01_bi_투자물_골든_카나리아 테스트_canonical_v1.json` |
| `02` | `blockguide` | `work_guards/02_chaebol_allowance_zero.yaml` | `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` | `bible/02_bi_chaebol_allowance_zero.json` |
| `03` | `blockguide` | `work_guards/03_chaebol_ent_empire.yaml` | `treatments/03_chaebol_ent_empire_tr_block_070_draft.json` | `bible/03_bi_chaebol_ent_empire.json` |
| `04` | `blockguide` | `work_guards/04_defense_defect_engineer.yaml` | `treatments/04_defense_defect_engineer_tr_block_070_draft.json` | `bible/04_bi_defense_defect_engineer.json` |
| `05` | `blockguide` | `work_guards/05_failed_future_ceo_intern.yaml` | `treatments/05_failed_future_ceo_intern_tr_block_070_draft.json` | `bible/05_bi_failed_future_ceo_intern.json` |
| `06` | `blockguide` | `work_guards/06_gatekeeper_heir.yaml` | `treatments/06_gatekeeper_heir_tr_block_070_draft.json` | `bible/06_bi_gatekeeper_heir.json` |
| `07` | `blockguide` | `work_guards/07_office_checkup_next_day.yaml` | `treatments/07_office_checkup_next_day_tr_block_070_draft.json` | `bible/07_bi_office_checkup_next_day.json` |
| `08` | `blockguide` | `work_guards/08_pantech_cyworld_reborn.yaml` | `treatments/08_pantech_cyworld_reborn_tr_block_070_draft.json` | `bible/08_bi_pantech_cyworld_reborn.json` |
| `09` | `wuxguide` | `work_guards/09_wuxia_heavenly_physician.yaml` | `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json` | `bible/09_bi_wuxia_heavenly_physician.json` |
| `10` | `blockguide` | `work_guards/10_jaebeol3se_loss_line.yaml` | `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json` | `bible/10_bi_jaebeol3se_loss_line.json` |

Pair `10` discipline:

- `pair 10` means `jaebeol3se_loss_line`
- `work_guards/10_permit_window_grade9.yaml` is not part of this canonical benchmark wave

## 4A. Chunk-Safe Procedure

Use this procedure unless the assigned environment proves it can safely inspect the raw files without context pressure.

1. `manifest resolve`
   - open `01_10_canonical_pair_manifest.md`
   - confirm the exact `WG / TR / BI` trio for the assigned pair
2. `WG extraction`
   - do not ingest the whole `work_guard` as free-form prose if targeted reads suffice
   - extract only the benchmark-relevant anchors:
     - `one_line_truth`
     - `mandatory_scene_engines`
     - `evaluation_thresholds`
     - `custom_rules`
     - `tracking_slots`
     - any explicit cider or no-pain-only contract
3. `BI extraction`
   - do not ingest the whole `BI` if search + targeted field reads suffice
   - extract only the benchmark-relevant anchors:
     - early promise / premise line
     - `success_device`
     - `cider_point`
     - `CommercialCode`
     - protagonist innocence setup
     - any opening reward promise
4. `TR opening pass`
   - inspect blocks `1~10`
   - score `P0` gates `1~4` from `TR blocks 2~6` only
   - use block `1` for setup context only
5. `TR full-block ledger pass`
   - inspect `TR` in fixed windows:
     - `1~10`
     - `11~20`
     - `21~30`
     - `31~40`
     - `41~50`
     - `51~60`
     - `61~70`
   - for each block, record a terse ledger row:
     - `block_no`
     - `has_cider true/false`
     - `receipt_kind`
     - `anchor_note`
6. `flagged-block spot-check`
   - reopen only candidate `no-cider` blocks and their immediate neighbors
   - confirm they are truly `setup-only`, `pain-only`, `failure-only`, `wait-only`, or `later payoff only`
7. `grade pass`
   - compute `P0`
   - apply cap rules
   - compute `P1`
   - finalize provisional grade

Hard safety rules:

- do not raw-full-read a `70`-block `TR` into context at once
- do not raw-full-read a `100k+ token` `BI` into context at once
- if the ledger already proves a `YELLOW ceiling`, do not widen the read scope unless a flagged block needs spot-check confirmation
- exact block evidence beats vague memory; terse ledger beats bloated transcript

## 5. Non-Negotiable True Benchmark Discipline

- for `P0` gates `1~4`, the only valid opening evidence window is `TR blocks 2~6`
- `TR block 1` may explain setup or innocence, but it cannot satisfy `P0` first-block gates
- `TR block 7+` cannot rescue missing first-block proof, reevaluation, token, or first visible cider
- every `TR` block must be scanned individually for `has_cider: true/false`
- one `no-cider block` means `YELLOW ceiling`
- `proof alone is not cider`
- `theme`, `pain`, `mood`, or `later payoff` promise do not count as same-block receipt
- if a claim has no exact block-number evidence, treat it as unproven
- if `work_guard` promises cider and `TR` fails to land it, fail harder, not softer
- `field extraction -> window ledger -> spot-check -> grade` is the default audit route
- never invent a substitute rubric; if the model wants `4/4`, `5-point`, `/40`, or `/100`, that report is automatically non-compliant

## 6. Bounded Audit Questions

Every terminal should answer only these questions:

1. which `P0` hard gates pass and fail
2. which exact blocks fail the full-block cider scan
3. which cap rules are active
4. what is the `P1` score table and total
5. what is the provisional grade
6. if the pair is `YELLOW` or `RED`, what are the top `3` bounded repair units
7. if the pair is `GREEN` or `GREENPLUS`, what alias note or residual risk should be recorded

## 7. Output Contract

Every terminal report must use this section order exactly:

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

Additional rules:

- `Compliance Self-Check` must answer `yes/no` for:
  - `P0 uses 6 gates only`
  - `P1 uses 10 axes x 0/1/2 only`
  - `P1 total is 20 only`
  - `gates 1~4 are anchored in TR 2~6 only`
  - `gate 6 is anchored in BI + TR 1~3 only`
  - `full-block cider scan covered every TR block`
  - `exact no-cider block numbers are listed, or none`
  - `grade obeys any no-cider block -> YELLOW ceiling`
  - `pair files were not mutated`
- `Evidence Anchor Table` must name:
  - first-block proof anchors
  - first-block reevaluation anchors
  - first-block token anchors
  - `BI` early promise anchor
  - `work_guard` contract anchor
- `Full-Block Cider Scan` must report:
  - total `TR` block count
  - no-cider block count
  - exact no-cider block numbers, or `none`
  - longest no-cider drought length
  - window summary for `1~10 / 11~20 / 21~30 / 31~40 / 41~50 / 51~60 / 61~70`
- `Provisional Grade` must explicitly state the active ceiling, or `no ceiling triggered`
- if a pair has any no-cider block, the report must say `YELLOW ceiling active due to full-block cider scan`
- if the report cannot prove a pass with numbered evidence, it must mark the gate `fail` or `unproven`
- if any `Compliance Self-Check` item is `no`, revise before writing the final report
- last line must be:
  - `read-only true benchmark audit complete; no pair files mutated`

## 8. Terminal Ownership

| Terminal | Pair | Prompt | Intended Report Path |
| --- | --- | --- | --- |
| `01` | `01` | `docs/2026-04-07/10pair_true_benchmark_terminal01_pair01_prompt.md` | `docs/2026-04-07/10pair_true_benchmark_terminal01_pair01_report.md` |
| `02` | `02` | `docs/2026-04-07/10pair_true_benchmark_terminal02_pair02_prompt.md` | `docs/2026-04-07/10pair_true_benchmark_terminal02_pair02_report.md` |
| `03` | `03` | `docs/2026-04-07/10pair_true_benchmark_terminal03_pair03_prompt.md` | `docs/2026-04-07/10pair_true_benchmark_terminal03_pair03_report.md` |
| `04` | `04` | `docs/2026-04-07/10pair_true_benchmark_terminal04_pair04_prompt.md` | `docs/2026-04-07/10pair_true_benchmark_terminal04_pair04_report.md` |
| `05` | `05` | `docs/2026-04-07/10pair_true_benchmark_terminal05_pair05_prompt.md` | `docs/2026-04-07/10pair_true_benchmark_terminal05_pair05_report.md` |
| `06` | `06` | `docs/2026-04-07/10pair_true_benchmark_terminal06_pair06_prompt.md` | `docs/2026-04-07/10pair_true_benchmark_terminal06_pair06_report.md` |
| `07` | `07` | `docs/2026-04-07/10pair_true_benchmark_terminal07_pair07_prompt.md` | `docs/2026-04-07/10pair_true_benchmark_terminal07_pair07_report.md` |
| `08` | `08` | `docs/2026-04-07/10pair_true_benchmark_terminal08_pair08_prompt.md` | `docs/2026-04-07/10pair_true_benchmark_terminal08_pair08_report.md` |
| `09` | `09` | `docs/2026-04-07/10pair_true_benchmark_terminal09_pair09_prompt.md` | `docs/2026-04-07/10pair_true_benchmark_terminal09_pair09_report.md` |
| `10` | `10` | `docs/2026-04-07/10pair_true_benchmark_terminal10_pair10_prompt.md` | `docs/2026-04-07/10pair_true_benchmark_terminal10_pair10_report.md` |

## 9. Human Launch Sequence

1. open `10` terminals
2. assign one prompt doc per terminal
3. paste the matching prompt into `Opus`
4. if the terminal has workspace write access, let `Opus` write directly to the intended report path
5. if the terminal cannot write files, collect the markdown output and save it manually at the intended report path
6. merge only after all `10` reports land

## 10. Merge Discipline

- trust `production-pair-benchmark-spec-v1.md` before model intuition
- if a report passes a gate without exact `TR 2~6` evidence, send it back
- if a report ignores the full-block cider scan, send it back
- if a report treats `pair 10` as anything other than `jaebeol3se_loss_line`, send it back
