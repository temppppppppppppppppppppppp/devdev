# 10-Pair Meta Cleanup Terminal 08 - Pair 08

Date: 2026-04-07
Status: final
Document Type: bounded read-only survey (1 terminal / 1 pair)
Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal08_pair08.md`
Parent Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md`
Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`

## 1. Terminal Scope

- single pair, read-only legacy meta wording survey
- classify `allowed_structural_meta` vs `diegetic_meta_ref` vs `label_meta_ref` vs `blocked_by_pair_truth`
- no repair, no code edits, no `treatments/` mutation, no `bible/` mutation, no `docs/temp/` mutation
- output is this file only

## 2. Assigned Pair and Family

- Pair: `08` (`pantech_cyworld_reborn`)
- Family overlay: `blockguide` (현대판타지 general mode, 가까운 프로파일은 `business_growth_profile` + `tech_startup_profile` + `entertainment_media_profile` 혼합)
- TR path: `treatments/08_pantech_cyworld_reborn_tr_block_070_draft.json`
- BI path: `bible/08_bi_pantech_cyworld_reborn.json`

## 3. Artifact Truth

| Check | TR | BI |
| --- | --- | --- |
| File exists | yes | yes |
| UTF-8 decode | yes (no BOM) | yes (with `utf-8-sig` BOM — `cp65001` BOM prefix present, `utf-8` strict load fails until BOM is stripped or `utf-8-sig` is used) |
| JSON parse | yes (`dict` root, `_schema = tr.v1`, `_total_blocks = 70`, `blocks` length `70`) | yes (`dict` root, `_schema_version = 2.1`, `MasterBible` present) |

Notes:

- TR is a fully populated `tr.v1` with 70 blocks, no `null` blocks, no skeleton gaps observable in this read-only sweep
- BI `_creation_note` openly states `plot_roadmap is live TR full copy, BI level recreation was not done`, which means BI `plot_roadmap[*]` mirrors TR block-for-block; that mirroring is the dominant source of meta wording carry-over in BI
- BI's BOM prefix is a soft hygiene flag, not a parse failure, and is not by itself a `P0`

## 4. Raw Count Snapshot

Raw `Block / ARC / Phase / Stage` token prevalence (informational only, not a failure count):

| Surface | Block / B-N | Arc / ARC-N | Phase | Stage | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| TR | `316` | `31` | `0` | `0` | `347` |
| BI | `387` | `46` | `6` | `1` | `440` |

`Block` numbers in the parent order's snapshot table (`08`: TR `316`, BI `387`) match the `Block N` channel exactly, confirming the same scan basis.

## 5. Findings

### 5.1 `allowed_structural_meta`

These hits are in legitimate machine structural slots and are not violations:

- TR: `blocks[*].block_id` (70 hits, format `Block N`)
- TR: `blocks[*].block_no` (70 hits, integer)
- BI: `MasterBible.plot_roadmap[*].block_id` (70 hits, mirrored from TR)
- BI: `MasterBible.plot_roadmap[*].block_no` (70 hits, integer)
- BI: `MasterBible.AssetLibrary.KeyNPCs[*].key_blocks[*]`, `MasterBible.PayoffTrack.*.triggered_blocks[*]`, `MasterBible.PayoffTrack.capital_payoff.decline_blocks[*]`, `MasterBible.ArcStructure.arcs[*].decline_blocks[*]` are integer-array structural blockrefs and are allowed

There is no `evolution` field in this pair (no `protagonist_config.special_ability.evolution`, no `martial_arts[*].evolution`, no `engine_evolution`), so the `SSOT_bi-evolution-metadata-standard.md` carve-out is not exercised here.

### 5.2 `diegetic_meta_ref` (human-readable narrative leakage)

The dominant failure surface. `Block N` and `Arc N` wording is fused into prose / list-string fields that are clearly meant to be read as narrative or label sentences, not machine ids. By field family:

TR-side (and the same content mirrored into `BI.MasterBible.plot_roadmap[*]`):

- `blocks[*].foreshadow[*]` — `80` Block-token hits across narrative foreshadow strings
- `blocks[*].callback[*]` — `106` Block-token hits across narrative callback strings (often `Block 1 CB 350억이 ...` style)
- `blocks[*].content.solution` — `25` hits, multi-block citation in solution prose (`Block 2 + Block 4 ...`)
- `blocks[*].content.reward` — `20` hits, including `Arc1 종료` end-of-arc tags fused into reward prose
- `blocks[*].content.context` — `9` hits, scene-context prose carries `Block N` references
- `blocks[*].content.event_villain` — `3` hits, including `Arc4 / Arc7` arc-id wording inside antagonist beat prose
- `blocks[*].failure_design.hope_hook` — `17` hits, hope-hook one-liners are written as `Block 9 부실 자산 인수 가격 협상 카드` style
- `blocks[*].stakes` — `14` hits, mostly `Arc1 / Arc2` wording fused into stakes sentences
- `blocks[*].regression_ext.slip_up.schedule_note` — `1` hit (`Arc1~2는 5블록당 1회 예정`)
- `blocks[69].genre_ext.method` — `1` hit (`Block 1 표현 인용+회장 서명 ...`)
- `blocks[69].genre_ext.leverage_used[0]` — `1` hit (`Block 1 표현 공식 인용`)

BI-only authoring surface (not mirrored from TR — these are independently written by the BI):

- `MasterBible.AssetLibrary.KeyNPCs[*].desc` — `33` Block-token hits, every major NPC carries a multi-block trace inside the prose `desc` (e.g. `Block 1 ... → Block 59 ... → Block 62 공식 철회 → Block 70 ...`)
- `MasterBible.AssetLibrary.KeyItems[*].inventory` — `13` hits, inventory entry strings annotated as `... (Block N)`
- `MasterBible.Seeds[*].description` — `8` hits, seed description prose carries `Block N '인용 표현'` style
- `MasterBible.PayoffTrack.foreshadow_payoff.notable_long_arcs[*]` — `6` hits, full prose payoff sentences with `Block 1 ... → Block 70 ...`
- `MasterBible.PayoffTrack.power_payoff.milestones[*]` — `5` hits, milestone strings are written as `Block 10 SPC 독립 회계 인정`
- `MasterBible.PayoffTrack.slip_up_track.suspicion_escalation` — `3` hits (`Block 5 박기태 → Block 29 마키노 레이 → Block 56 한유리`)
- `MasterBible.PayoffTrack.death_flag_track.note` — `1` hit (`Phase0 4 스케줄 버킷 ...`)
- `MasterBible.protagonist_config.regression_mechanic.suspicion_pressure` — `4` hits, includes `Arc7` arc-id token
- `MasterBible.FinanceHUD.Protagonist.actual_truth.financial_status.{initial_capital,total_assets,peak_capital,derivatives.CB,derivatives.ABS}` — `5` hits, numeric-wealth strings annotated `(Block N)`
- `MasterBible.FinanceHUD.Protagonist.actual_truth.wealth` — `1` hit (`7,790억 (Block 70, 생활계정 그룹 실질 승계자 포지션)`)

### 5.3 `label_meta_ref` (label fields with structural id wording instead of natural language)

- `MasterBible.OpponentTransitionPlan.phases[*].phase` — `7` hits. The values are pure structural id strings, not natural-language section titles:
  - `phases[0].phase = "Arc1 (1-10)"`
  - `phases[1].phase = "Arc2 (11-20)"`
  - ... up through `phases[6]`
  - `phase` is exactly the kind of label field section `6.2` of the parent order names as forbidden when carrying structural id wording

This pair has no `section_rotation`, no `arc_section`, and no `phase_label` keys, so the only label-field violation surface here is `OpponentTransitionPlan.phases[*].phase`.

### 5.4 Operational pipeline metadata (informational, not classified as narrative leakage)

These contain `Stage0 / Phase0` tokens but the field semantics are pipeline authority/sync chain, not in-story narrative:

- BI `_creation_note` (`canonical pitch·Stage0 4종·live Phase0·live TR 동기화`)
- BI `_schema_description` (`canonical pitch + live Phase0 + live TR 동기화 생성`)
- BI `MasterBible.ArcStructure._description` (`Phase0·TR와 동기화`)
- BI `MasterBible.OpponentTransitionPlan._description` (`Phase0과 동기화`)

Reading per parent order section `4`: these are operational meta tokens, equivalent to `PASS / HOLD / REJECT / WG-V2 / TR / BI / canon`, not the `Block / ARC / Phase / Stage` 4-channel narrative leakage. They are out of strict scope for this cleanup wave; flagging only.

### 5.5 `blocked_by_pair_truth`

None observed at this read-only level.

- `10pair_tr_bi_consistency_bounded_survey.md` (2026-04-06) classifies pair `08` as `clean` with highest severity `P3` and reads it as `schema/meta wording cleanup only`
- TR has no missing-block / draft-stub gap (70 / 70 populated, `block_no 70` end-state matches BI `Block 70` payoff anchors)
- BI metadata vs TR truth alignment for the headline numbers (`peak_capital`, `total_assets`, `wealth`, `derivatives.CB`, `power_payoff.milestones[*].block_X`) is internally consistent — the BI annotations point to the same blocks the TR actually produces
- there is no `regression_ext.is_regressor`-vs-`incarnation_type` style drift like pair `07`, and no `tr_block_count` undercount like pair `10`
- accordingly, wording cleanup on this pair does not need to wait for any deeper truth repair

## 6. Concrete Anchors (capped at 5)

1. `TR: blocks[0].foreshadow[0]` — diegetic; value `회장의 '해외 거인에게 먹힐 소모품' 단언은 Block 62에서 스스로 철회되는 대비축이 된다.` Move the `62` into `foreshadow_targets[]` and rewrite the prose without the `Block 62` token.
2. `TR: blocks[8].content.solution` — diegetic; value `... Block 2의 보조금 회의록 + Block 4 이사진의 '현금흐름 증거' 요구 ...`. Multi-block prose citations are the most repeated solution-field pattern; cleanup template should target every `blocks[*].content.solution`.
3. `BI: MasterBible.AssetLibrary.KeyNPCs[1].desc` — diegetic, BI-only authoring; value `... Block 1 '숫자만큼은 ...' → Block 5·17 특별감사 → Block 27 ... → Block 66 ... → Block 67 ... → Block 68 ...`. NPC `desc` is a prose biography field, not a machine timeline, and is the worst single BI-side leakage source after `plot_roadmap` mirroring.
4. `BI: MasterBible.OpponentTransitionPlan.phases[0].phase` — `label_meta_ref`; value `Arc1 (1-10)`. `phase` is a label field that must hold a natural-language section title; the structural numbering `1-10` and the arc id `Arc1` should both move to `arc_no` / range fields and the label should be rewritten in prose.
5. `BI: MasterBible.PayoffTrack.power_payoff.milestones[0]` — diegetic; value `Block 10 SPC 독립 회계 인정`. Milestone strings should read as natural-language payoff lines and let the block-id live in a parallel structural field, not in the prose.

## 7. Final Severity

`P2`

Reasoning:

- `P0` is not justified — file present, JSON parses, no decode failure (BOM is a hygiene note only)
- `P1` is not justified — there is no truth blocker that would make wording cleanup unsafe; the prior 10-pair consistency survey already cleared pair `08` as `clean` and routed it to `schema/meta wording cleanup only`
- `P3` is too soft — the leakage is not sparse cosmetic noise; it is repeated and structural across `foreshadow / callback / solution / reward / hope_hook / stakes / NPC desc / Seeds description / FinanceHUD inventory / PayoffTrack milestones / OpponentTransitionPlan.phases.phase`, and one clean `label_meta_ref` violation exists in the `phase` label field
- `P2` correctly states `repeated disallowed meta leakage exists and bounded cleanup should be scheduled soon`

## 8. Final Execution Route

`cleanup_now`

Smallest cleanup unit: **`TR + BI`**

Why both:

- `BI.MasterBible.plot_roadmap[*]` is openly declared as a verbatim TR copy in `_creation_note`; if cleanup is done in TR first the BI `plot_roadmap` will need a re-sync pass anyway
- the BI also carries an independent leakage surface that does not exist in TR (`KeyNPCs[*].desc`, `Seeds[*].description`, `PayoffTrack.*.milestones / notable_long_arcs / suspicion_escalation`, `FinanceHUD.*.inventory`, `OpponentTransitionPlan.phases[*].phase`); these cannot be fixed by TR-only edits
- a TR-only cleanup would leave BI in a half-clean state where the `plot_roadmap` mirror is fixed but the BI-authored prose still reads `Block N → Block N`

Suggested cleanup template (cleanup wave only, do not execute here):

- structural ids stay where they belong: `block_id`, `block_no`, `arc_id`, `arc_no`, `foreshadow_targets[]`, `callback_sources[]`, `decline_blocks[]`, `triggered_blocks[]`, `key_blocks[]`
- prose fields get rewritten so that the meaning survives without the `Block N / Arc N` token (e.g. `Block 62에서 철회된다` → `회장이 '소모품' 단언을 후일 스스로 철회한다`, with `62` carried as a structural target)
- `OpponentTransitionPlan.phases[*].phase` rewritten as a natural-language section title, with `Arc1` and the `(1-10)` range moved to `arc_no` / range fields
- operational pipeline-meta strings (`_creation_note`, `_schema_description`, `_description`) are out of scope for this wave

## 9. One-Line Next Step

Schedule a `TR + BI` joint cleanup patch order targeting prose fields first (`foreshadow / callback / solution / reward / hope_hook / stakes / NPC desc / Seeds description / FinanceHUD inventory / PayoffTrack milestones`) and then the single `OpponentTransitionPlan.phases[*].phase` label-field rewrite, with structural ids redirected to `_targets / _sources / arc_no / block_no` slots.

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
