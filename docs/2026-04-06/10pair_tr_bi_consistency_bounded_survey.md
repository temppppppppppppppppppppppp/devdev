# 10-Pair TR/BI Consistency Bounded Survey

Date: 2026-04-06
Status: final
Document Type: bounded merge survey
Canonical Path: `docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md`
Scope: numbered `01-10` `TR/BI` pair consistency only
Merge Owner: `Codex`
Execution Mode: `5-lane Sonnet read-only survey -> Codex merge/audit`

## 1. Source Inputs

Merged lane outputs:

- `docs/2026-04-06/10pair_tr_bi_lane1_pairs_01_02.md`
- `docs/2026-04-06/10pair_tr_bi_lane2_pairs_03_04.md`
- `docs/2026-04-06/10pair_tr_bi_lane3_pairs_05_06.md`
- `docs/2026-04-06/10pair_tr_bi_lane4_pairs_07_08.md`
- `docs/2026-04-06/10pair_tr_bi_lane5_pairs_09_10.md`

Codex spot-check anchors:

- `treatments/07_office_checkup_next_day_tr_block_070_draft.json`
- `bible/07_bi_office_checkup_next_day.json`
- `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json`
- `bible/10_bi_jaebeol3se_loss_line.json`
- `bible/05_bi_failed_future_ceo_intern.json`
- `bible/06_bi_gatekeeper_heir.json`

## 2. Executive Verdict

Across the numbered `01-10` pair set:

- `clean`: `8` pairs
- `mixed`: `2` pairs
- `hard mismatch`: `0` pairs
- `P0`: `0`
- `P1`: `0`
- `P2`: `2 pairs` (`07`, `10`)

Conclusion:

- the pair set is broadly usable for bounded material-side continuity work
- the main risk is not pair identity collapse but `late-sync drift` in a small subset
- `07` is a `BI metadata/end-state drift` case
- `10` is a `TR incomplete vs BI ahead` case

## 3. Aggregate Scoreboard

| Pair | Verdict | Highest Severity | Final Reading |
| --- | --- | --- | --- |
| `01` | `clean` | `P3` | same work, same protagonist engine, naming noise only |
| `02` | `clean` | `P3` | strong blockguide alignment, genre key naming noise only |
| `03` | `clean` | `P3` | entertainment empire pair-consistent, minor metadata noise only |
| `04` | `clean` | `P3` | defense/business-growth pair-consistent, minor metadata gaps only |
| `05` | `clean` | `P3` | identity intact, BI incarnation label drift only |
| `06` | `clean` | `P3` | identity intact, BI cosmetic/wording drift only |
| `07` | `mixed` | `P2` | BI origin-state and incarnation metadata drift from TR truth |
| `08` | `clean` | `P3` | high alignment, schema/meta wording cleanup only |
| `09` | `clean` | `P3` | wuxguide pair-consistent, seeds granularity only |
| `10` | `mixed` | `P2` | TR stops at 57 while BI already carries 58-70 design |

## 4. Key Findings

### 4.1 Stable `clean` set

Pairs `01`, `02`, `03`, `04`, `05`, `06`, `08`, `09` are pair-consistent.

Common pattern:

- same numbered pair, same protagonist, same work identity
- BI materially amplifies the same engine, conflict, and endgame direction already established in TR
- remaining issues are mostly `P3` metadata noise, naming drift, seed granularity, or standalone-document wording cleanup

### 4.2 Pair `07` is `mixed` because BI metadata contradicts TR truth

Lane 4 identified two `P2` issues and Codex spot-check confirmed them:

- `TR` keeps `regression_ext.is_regressor = false`
- `BI: protagonist_config.incarnation_type = "회귀자"`
- `TR` Block 70 end-state is reflected in BI `mobilizable_capital`, but `BI: financial_status.company_state` remains at the Block 1-style start state

Reading:

- this is not a wrong-work pairing
- this is a real `TR truth -> BI metadata/end-state` drift
- pair remains recognizably the same work, but it should not be treated as fully clean until BI metadata is repaired

### 4.3 Pair `10` is `mixed` because TR production is incomplete while BI is ahead

Lane 5 identified the main issue and Codex spot-check confirmed it:

- `TR` file is a root `list` with actual length `57`
- the filename still says `_tr_block_070_draft`
- `BI` contains late design anchors for `58-70`, including `capital_curve` entries at Blocks `59` and `68`, `defeat_blocks` at `63` and `67`, and a fifth arc covering `61-70`
- `BI: _sync_manifest.tr_block_count = 5`, which is also incorrect relative to the live TR

Reading:

- this is not a same-work identity failure
- this is a `late-block production gap` plus `sync metadata error`
- the right next move is to finish `TR 58-70`, then re-sync the BI metadata

## 5. Pair Notes

### Pair `05`

- `clean`
- highest severity `P3`
- main note: `BI: protagonist_config.incarnation_type = "회귀자"` while the pair is framed as `빙의`
- codex spot-check also confirmed `BI: MasterBible.ProjectData.CoreIdentity.desire` still contains a direct `Block 1` reference

### Pair `06`

- `clean`
- highest severity `P3`
- main note: BI is pair-consistent, but carries cosmetic cleanup items such as `start_point.context = "세원정밀를 ..."`
- codex spot-check confirmed the typo and the end-state snapshot convention noted by the lane survey

## 6. Recommended Routing

Immediate priority:

1. repair pair `07` BI metadata and end-state snapshot
2. finish pair `10` TR Blocks `58-70`
3. re-sync pair `10` BI metadata after TR completion

Lower-priority cleanup only:

1. `05` incarnation label normalization
2. `06` typo/cosmetic BI cleanup
3. `01/02/03/04/08/09` optional metadata wording cleanup only

## 7. Final Call

This bounded survey does not show a broad `TR/BI pair collapse` across the numbered set.

The live reading is:

- `8/10` pairs are clean
- `2/10` pairs are mixed
- no pair is a `hard mismatch`
- the set is viable for continued bounded work as long as pair `07` and pair `10` are treated as active repair targets

## 8. 3-Pass Audit Note

Pass 1:

- merged all 5 lane outputs into one scoreboard
- isolated the two non-clean pairs as `07`, `10`

Pass 2:

- performed Codex spot-checks on the flagged anchors for `07`, `10`
- re-checked lane `05`, `06` notes to avoid over-escalating `P3` cosmetics

Pass 3:

- normalized the final verdict into `clean / mixed / hard mismatch`
- kept routing guidance bounded to pair consistency follow-up only
- confirmed no `P0` or `P1` evidence in the current numbered pair set

Confidence: `97%`
