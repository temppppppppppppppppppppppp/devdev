# Pair 07/10 Mixed-Pair Parallel Execution SSOT

Date: 2026-04-06
Status: active
Document Type: narrative pair-repair execution SSOT
Canonical Path: `docs/2026-04-06/07_10_mixed_pair_parallel_execution_ssot.md`
Scope: bounded repair execution for pair `07` and pair `10` only
Execution Mode: `parallel-but-gated`
Family Overlay: `blockguide` for both pairs
Final Audit Owner: `Codex`

## 1. Source Authority

Read order for every worker:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md`
5. this execution SSOT

Execution anchor docs:

- `docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md`
- `docs/2026-04-06/10pair_tr_bi_lane4_pairs_07_08.md`
- `docs/2026-04-06/10pair_tr_bi_lane5_pairs_09_10.md`

## 2. Why This Exists

The bounded survey closed with:

- pair `07` = `mixed`, because BI metadata and end-state snapshot drift from TR truth
- pair `10` = `mixed`, because TR stops at `57` while BI already carries late-block design through `70`

This execution SSOT promotes the survey routing into one bounded repair wave.

## 3. Execution Decision

Use a `2-lane parallel model`:

- `Lane A`: pair `07` BI repair can run immediately and independently
- `Lane B`: pair `10` runs as one owned vertical chain
  - `Step B1`: finish `TR` Blocks `58-70`
  - `Step B2`: re-sync `BI` against the landed `TR`

Do not split pair `10` across multiple terminals. The same lane should carry `B1 -> B2` in order.
However, `Lane B` must obey the material-side production harness:

- block is the base execution unit
- same-order auto-run cap is `5` blocks
- `Block 060` and `Block 070` boundaries require the mandatory `10-block` audit gate before proceeding
- if the harness gate stops progress before `TR 70`, stop cleanly and leave a resume note instead of forcing the BI step early

## 4. Ownership Map

| Lane | Owner File(s) | Mode | Dependency | Output Note |
| --- | --- | --- | --- | --- |
| `Lane A` | `bible/07_bi_office_checkup_next_day.json` | direct repair | none | `docs/2026-04-06/07_pair_bi_repair_note.md` |
| `Lane B` | `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json` and `bible/10_bi_jaebeol3se_loss_line.json` | resumable vertical repair chain | `TR` first, then `BI` | `docs/2026-04-06/10_pair_vertical_repair_note.md` |
| `Codex` | final audit + closure docs | merge/audit | after `A`, `B` | reserved |

Collision rule:

- one lane owns one live artifact file
- no shared editing of the same `TR` or `BI`
- no lane writes another lane's note file

## 5. Lane Scope

### 5.1 Lane A: Pair `07` BI Repair

Target:

- `bible/07_bi_office_checkup_next_day.json`

Required repair scope:

1. align `MasterBible.protagonist_config.incarnation_type` with live TR truth
2. align `MasterBible.FinanceHUD.Protagonist.actual_truth.financial_status.company_state` with the pair's late-state / end-state rather than the Block 1 start-state

Allowed small sweep:

- if a trivial low-risk cleanup is directly adjacent to the touched keys, it may be fixed
- do not expand into broad BI beautification

Do not do:

- TR rewrite
- new plot invention
- family reclassification
- broad `KeyNPCs` or schema cleanup beyond the bounded repair

Completion standard:

- pair `07` should upgrade from `mixed` to `clean` on the two proven `P2` points

### 5.2 Lane B: Pair `10` Vertical Repair

This lane is one owned chain:

1. finish the `TR`
2. then re-sync the `BI`

#### Step B1: Pair `10` TR Completion

Target:

- `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json`

Required repair scope:

1. preserve the live root format
2. extend the current `57`-block TR to a real `70`-block TR
3. write Blocks `58-70` so they honor the existing protagonist engine:
   - 손실선 판독
   - 내부 방어 + 외부 공개 데이터 포지션의 dual-lane
   - insider-trading contamination 금지
   - blockguide business-power pressure continuity
4. land the late-block promises already visible in the BI only if they fit the current TR spine

Material-side execution rule:

- read and follow the material-side stage chain and the live production handoff before producing
- follow `docs/blockguide/treatment-production-harness-v2.md`
- base write unit is always `1 block`
- same-order auto-run cap is `5 blocks`
- after `Block 060`, perform the mandatory `Block 051~060` audit before entering `061+`
- after `Block 070`, perform the mandatory `Block 061~070` audit before BI handoff

Authority rule:

- the current TR spine remains primary
- the BI is a downstream contract aid, not a license to overwrite the live TR voice or logic

Do not do:

- BI edits in this lane
- whole-file rewrite if append/finish can solve it
- contamination into wuxguide semantics

Completion standard:

- live TR count reaches `70`
- the pair's late-block chain is no longer missing

#### Step B2: Pair `10` BI Re-Sync

Target:

- `bible/10_bi_jaebeol3se_loss_line.json`

Start gate:

- begin only after `Step B1` finishes and the new `TR 58-70` is live

Required repair scope:

1. re-check late-block references against the landed `TR`
2. update any BI late-arc summaries that drift from the real finished TR
3. fix sync metadata, especially `_sync_manifest.tr_block_count`
4. keep BI aligned to the finished TR without inventing a second canon

Likely touch zones:

- `arcs`
- `capital_curve`
- `defeat_blocks`
- `_sync_manifest`
- any directly adjacent late-block summary fields that no longer match the landed TR

Do not do:

- re-open pair identity or early-arc design
- rewrite the whole BI if a bounded sync pass is enough

Completion standard:

- pair `10` should upgrade from `mixed` to `clean`, or else leave a precise residual note if a new contradiction appears

## 6. Recommended Terminal Mapping

### Terminal A

- owns `Lane A`
- pair `07` BI repair only

### Terminal B

- owns `Lane B`
- pair `10` vertical chain only
- finish `TR 58-70`, then repair `BI`

Codex role:

- review lane notes
- spot-check live artifacts
- produce final closure note

## 7. Paste-Ready Orders

### Terminal A Order

```text
Read first:
1. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
2. C:\Users\wjjo\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
3. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
4. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_bounded_survey.md
5. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\07_10_mixed_pair_parallel_execution_ssot.md

Task:
- repair pair 07 only
- own bible/07_bi_office_checkup_next_day.json only
- fix incarnation_type drift and end-state company_state drift only
- keep repair bounded
- do not edit TR
- write a short completion note only to:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\07_pair_bi_repair_note.md
```

### Terminal B Order

```text
Read first:
1. C:\Users\wjjo\Desktop\글도비\material_ssot\README.md
2. C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\stage-read-order.md
3. C:\Users\wjjo\Desktop\글도비\material_ssot\20_pitch\canon\jaebeol3se_loss_line.md
4. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\jaebeol3se_loss_line_tr_production_handoff.md
5. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
6. C:\Users\wjjo\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
7. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md
8. C:\Users\wjjo\Desktop\글도비\docs\blockguide\treatment-production-harness-v2.md
9. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10pair_tr_bi_consistency_bounded_survey.md
10. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\07_10_mixed_pair_parallel_execution_ssot.md

Task:
- repair pair 10 only as one vertical chain
- own treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json and bible/10_bi_jaebeol3se_loss_line.json only
- follow the material-side handoff and production harness exactly
- preserve the existing spine and root format
- block is the base execution unit
- same-order auto-run cap is 5 blocks
- complete Block 58 onward in harness order
- when Block 060 is reached, run the mandatory 051~060 audit gate before entering 061+
- only after TR reaches Block 070 and the required 061~070 audit gate passes may BI re-sync begin
- if the harness gate or 5-block cap stops progress before TR 70, do not touch BI yet; leave the exact resume point in the note
- if TR reaches 70 cleanly in this run, then re-sync the BI against the landed TR
- write a short completion note only to:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\10_pair_vertical_repair_note.md
```

## 8. Stop Conditions

Stop and escalate instead of forcing the patch if any of these happen:

1. pair `07` BI repair requires TR reinterpretation rather than metadata alignment
2. pair `10` BI late design turns out to contradict the existing TR spine so strongly that `58-70` cannot be added without major regeneration
3. new pair-identity doubt appears
4. a lane would need to edit another lane's owned file

## 9. Completion Gate

This wave is complete only when:

1. pair `07` proven `P2` drift is removed
2. pair `10` TR reaches `70` blocks
3. pair `10` BI is re-synced against the finished TR
4. Codex performs a bounded post-repair audit and writes the closure note

Reserved final closure output:

- `docs/2026-04-06/07_10_mixed_pair_parallel_closure_note.md`

## 10. 3-Pass Audit Note

Pass 1:

- translated the prior survey's recommended routing into owned execution lanes
- separated independent pair `07` work from the vertical pair `10` chain

Pass 2:

- re-checked the live file structure for pair `07` BI and pair `10` TR/BI
- pinned the actual repair surfaces and kept pair `10` as one gated owner lane

Pass 3:

- converted the plan into a collision-safe `2-lane` execution SSOT
- added paste-ready `A/B` terminal orders and reserved final closure ownership for Codex

Confidence: `97%`
