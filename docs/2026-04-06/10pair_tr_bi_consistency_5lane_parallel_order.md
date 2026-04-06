# 10-Pair TR/BI Consistency 5-Lane Parallel Order

Date: 2026-04-06
Status: final
Document Type: bounded parallel survey order
Canonical Path: `docs/2026-04-06/10pair_tr_bi_consistency_5lane_parallel_order.md`
Scope: read-only `TR/BI pair consistency` audit for the numbered `01-10` pair set only
Execution Mode: `5 terminals / Sonnet / parallel / no repair / no code edits / no pair mutation`
Final Merge Owner: `Codex`

## 1. Purpose

This order exists to answer one bounded question only:

- across the numbered `01-10` `TR/BI` pairs, which pairs are `pair-consistent`, which are `mixed`, and which have `hard mismatch`

This is not:

- fresh generation
- pair repair
- promotion
- Stage 2 or Stage 4 runtime probing
- code/system work

## 2. Inventory

Confirmed numbered pair inventory:

| Pair | TR | BI | Family Overlay |
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
| `10` | `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json` | `bible/10_bi_jaebeol3se_loss_line.json` | `blockguide` |

## 3. Required Read Order

Each terminal must read in this order before judging any pair:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/narrative-router/material-revival-ladder-harness.md`
3. family overlay:
   - `blockguide`: `docs/blockguide/SSOT_blockguide-integrated-order.md`
   - `wuxguide`: `docs/wuxguide/SSOT_wuxguide-integrated-order.md`
4. this order file

## 4. Bounded Audit Question

For each assigned pair, answer:

1. are `TR` and `BI` clearly the same work
2. does `BI` materially amplify the same protagonist engine and core conflict that the `TR` establishes
3. do the family-critical contract anchors remain aligned
4. does the pair look `clean`, `mixed`, or `hard mismatch`

## 5. Audit Axes

Check only these axes:

1. `artifact truth`
   - file exists
   - UTF-8 decode succeeds
   - JSON parse succeeds
2. `pair identity truth`
   - same numbered pair
   - same work title / slug intent
   - same protagonist identity
3. `core narrative truth`
   - protagonist desire / engine
   - growth resource / power axis
   - main antagonistic pressure
   - core premise and tone
4. `late-pair carry`
   - BI reflects the TR's late-block escalation, endgame pressure, or final promised direction
5. `family overlay truth`
   - `blockguide`: resource-power HUD meaning, operating arena, business/domain line, commercial or institutional pressure
   - `wuxguide`: realm / internal-energy / martial-arts / faction / jianghu continuity, `MartialHUD`-style semantic fit

Do not widen into:

- line-by-line prose editing
- full TR static quality grading
- BI redesign proposals beyond minimal next-step hints
- runtime canary claims

## 6. Severity Scale

- `P0`
  - file missing
  - UTF-8 or JSON unreadable
  - pair identity unrecoverable
- `P1`
  - protagonist, core premise, or family profile clearly contradicts across TR and BI
  - BI is not a usable companion for that TR
- `P2`
  - pair is broadly the same work, but key pressure/growth/endgame axes drift materially
- `P3`
  - naming noise, thin emphasis drift, metadata oddities, or minor under-spec without breaking pair identity

Pair verdict:

- `clean`
- `mixed`
- `hard mismatch`

## 7. Lane Split

Ownership is by pair. No lane may write to another lane's output file.

### Lane 1

- owns pairs `01`, `02`
- output:
  - `docs/2026-04-06/10pair_tr_bi_lane1_pairs_01_02.md`

### Lane 2

- owns pairs `03`, `04`
- output:
  - `docs/2026-04-06/10pair_tr_bi_lane2_pairs_03_04.md`

### Lane 3

- owns pairs `05`, `06`
- output:
  - `docs/2026-04-06/10pair_tr_bi_lane3_pairs_05_06.md`

### Lane 4

- owns pairs `07`, `08`
- output:
  - `docs/2026-04-06/10pair_tr_bi_lane4_pairs_07_08.md`

### Lane 5

- owns pairs `09`, `10`
- special note:
  - apply `wuxguide` semantics to `09`
  - apply `blockguide` semantics to `10`
- output:
  - `docs/2026-04-06/10pair_tr_bi_lane5_pairs_09_10.md`

Final merge output is reserved for Codex only:

- `docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md`

## 8. Output Contract

Each lane file must contain:

1. lane scope
2. assigned pair list
3. one section per pair
4. per pair:
   - pair verdict
   - severity summary
   - `3-6` findings max
   - concrete file/key anchors
   - one-line minimal next-step suggestion
5. lane summary table

Use key-path style anchors such as:

- `TR: protagonist_config.name`
- `BI: FinanceHUD.capital_axis`
- `BI: MartialHUD.realm`

Do not dump large JSON excerpts.

## 9. Merge Rules

- no lane writes the final merged survey
- no lane edits pair artifacts
- no lane edits `docs/temp/`
- no lane performs repair
- no lane claims promotion readiness
- Codex will merge the 5 lane outputs afterward

## 10. Paste-Ready Terminal Orders

### Terminal 1

```text
Read first:
1. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\wjjo\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_5lane_parallel_order.md

Task:
- read-only bounded audit only
- own pairs 01 and 02 only
- audit TR/BI pair consistency only
- no repair
- no code edits
- no docs/temp edits

Output:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_lane1_pairs_01_02.md
```

### Terminal 2

```text
Read first:
1. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\wjjo\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_5lane_parallel_order.md

Task:
- read-only bounded audit only
- own pairs 03 and 04 only
- audit TR/BI pair consistency only
- no repair
- no code edits
- no docs/temp edits

Output:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_lane2_pairs_03_04.md
```

### Terminal 3

```text
Read first:
1. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\wjjo\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_5lane_parallel_order.md

Task:
- read-only bounded audit only
- own pairs 05 and 06 only
- audit TR/BI pair consistency only
- no repair
- no code edits
- no docs/temp edits

Output:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_lane3_pairs_05_06.md
```

### Terminal 4

```text
Read first:
1. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\wjjo\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_5lane_parallel_order.md

Task:
- read-only bounded audit only
- own pairs 07 and 08 only
- audit TR/BI pair consistency only
- no repair
- no code edits
- no docs/temp edits

Output:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_lane4_pairs_07_08.md
```

### Terminal 5

```text
Read first:
1. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
3. C:\Users\wjjo\Desktop\글도비\docs\wuxguide\SSOT_wuxguide-integrated-order.md for pair 09
4. C:\Users\wjjo\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md for pair 10
5. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_5lane_parallel_order.md

Task:
- read-only bounded audit only
- own pairs 09 and 10 only
- apply wuxguide semantics to 09 and blockguide semantics to 10
- audit TR/BI pair consistency only
- no repair
- no code edits
- no docs/temp edits

Output:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_lane5_pairs_09_10.md
```

## 11. 3-Pass Audit Note

Pass 1:

- fixed the numbered pair inventory to the live workspace `01-10` set only
- bounded the task to pair consistency rather than full repair or promotion

Pass 2:

- aligned the order with router + pair-revival read order
- explicitly separated `blockguide` and `wuxguide` overlay handling for the mixed-family set

Pass 3:

- split ownership cleanly into `5 lanes`
- reserved final merge for Codex so terminals do not collide on one output file
- kept the output contract compact enough for a quick Sonnet audit pass

Confidence: `97%`
