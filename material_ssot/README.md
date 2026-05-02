# material_ssot

Date: 2026-04-03
Status: active bounded SSOT
Scope: material-side stage SSOT only

`material_ssot` is the stage-axis SSOT for the material side order.

Design baseline:

- `docs/2026-04-03/material-side-order-ssot-design.md`

Official stage chain:

`리서치 -> 기획안 -> Stage 0 preprocess -> Phase 0 design -> TR 생성 -> BI 생성`

Operator alias note:

- in workspace shorthand, `재료 사이드`, `재료 사이드 하네스`, `material-side harness`, `material_ssot 쪽`, `글도비 파이프라인 이전`, `기획안~TR/BI`, and `TR/BI pair 제작` all point to this root and its companion material-side docs
- unless the request explicitly asks for code/runtime/DB/app/test work, interpret those phrases as stage-axis material-side work, not system-track

Normalized fresh-creation route:

- the official stage chain above remains the stage-axis contract
- when operators are creating a fresh work from reusable materials, use this normalized upstream route:
  - `10_research` engine pack or normalized work material pack
  - `20_pitch/synthesis/` one-page synthesis
  - `00_governance/donor-review-and-adoption-contract-v1.md` donor review
  - `20_pitch/pitch-selection-checklist.md` audit
  - `20_pitch/canon/` pitch freeze
  - `20_pitch/work-guard-translation-map.md` -> work-specific `work_guard`
- this route clarifies the operator handoff between research and pitch without adding a new stage root

Operational companion note:

- the official stage chain above remains the root stage-axis contract
- when a work uses `work_guard`, current material-side operating practice treats it as a pre-`TR` runtime-guard companion
- recommended companion flow: `Phase 0 design -> work_guard draft/freeze -> TR 생성 -> BI 생성`
- reviewed/frozen work-specific guards may be published into the Stage 0-visible `work_guards/` library after audit
- current operator pack:
  - `python -X utf8 scripts/run_work_guard_v1.py --path <yaml>`
  - `docs/2026-04-06/work-guard-validator-checklist-spec.md`
  - `docs/2026-04-06/wg-v2-freeze-checklist.md`
  - `docs/2026-04-06/wg-v3-drift-audit-card.md`

Quick start read order:

1. `00_governance/bootstrap-status.md`
2. `00_governance/authority-map.md`
3. `00_governance/stage-read-order.md`
4. `00_governance/delegation-envelope-spec-v1.md`
5. `00_governance/work-current-truth-template-v1.md`
6. `00_governance/work-coverage-matrix.md`
7. one representative work chain under `30_stage0_preprocess/work-index/`

This root does not replace:

- `docs/narrative-router` as the family-axis router
- system-track governance for the Geuldobi pipeline
- live artifact paths such as `treatments/` and `bible/`

Bounded-slice rule:

- establish the authority map, stage read order, and work index first
- do not move existing raw research, preprocess, phase0, TR, or BI files in this wave
- connect legacy paths by manifest and labeling first

Current governance anchors:

- `00_governance/authority-map.md`
- `00_governance/stage-read-order.md`
- `00_governance/donor-review-and-adoption-contract-v1.md`
- `docs/2026-04-29/material-side-immediate-deployment-overlay.md`
- `00_governance/legacy-map.md`
- `00_governance/delegation-envelope-spec-v1.md`
- `00_governance/work-current-truth-template-v1.md`
- `00_governance/work-coverage-matrix.md`
- `00_governance/bootstrap-status.md`
- `00_governance/production-pair-benchmark-spec-v1.md`

Current immediate material deployment:

- `golden_canary_deepclone_probe_a_fullblock_v1`
- `distressed_asset_heir`
- `distressed_company_buyer`
- `venture_bubble_king_2000`
- `telecom_gate_monopoly_1997`
- `pharma_cdmo_industry_heir`
- `shipbuilding_ocean_heir`
- `power_grid_heir`
- `healthy_heir_group_succession`
- `laid_off_cashflow_rights_operator`
- reason: current immediate-deployment rows have donor structure applied or adopted in visible material-side authority and are closed by named overlay/audit artifacts
- pharma CDMO row carries explicit 70/70 `webnovel_pacing_contract` coverage in TR and BI for immediate writer handoff
- pharma CDMO row now also carries canonical downstream episode pacing hint coverage at TR 70/70 and BI 70/70, with attachment audit PASS and registry `range_attachment_status=range_complete`
- power-grid row carries canonical downstream episode pacing hint coverage at TR 70/70 and BI 70/70, donor review/contamination guardrail closeout, and registry `range_attachment_status=range_complete`
- healthy-heir row now carries donor review/contamination guardrail closeout, BIAmplificationPower, TR/BI `reader_payoff_ladder` 70/70, TR/BI `webnovel_pacing_contract` 70/70, and downstream episode pacing hint TR/BI 70/70 with `range_attachment_status=range_complete`
- laid-off cashflow-rights/operator row carries root TR/BI, donor review/contamination guardrail closeout, declared-contract opening GREEN, BIAmplificationPower, TR/BI `reader_payoff_ladder` 70/70, TR/BI `webnovel_pacing_contract` 70/70, and downstream episode pacing hint TR/BI 70/70 with `range_attachment_status=range_complete`
- from 2026-05-02 onward, immediate-deployment claims also require a visible material-side downstream episode pacing hint or equivalent advisory range surface
- other `GREENPLUS` / `GREEN` pairs remain benchmark/reference inventory until donor structure is applied, recorded, and closed by named overlay promotion

TR block semantics note:

- on the material side, `TR block` is a planning bundle, not a published episode-count unit
- default operator reading: one meaningful `TR block` should be dense enough to unfold into roughly `2~6` serialized episodes downstream
- do not write or audit with the mental model `TR block 1 = episode 1`, `TR block 2 = episode 2`
- benchmark shorthand such as `block 1` refers to the first reader-earning episode bundle, which the current benchmark operationalizes through `TR blocks 2~6`, not literal `TR block 1`
- for immediate-use material classification, the material side should expose an advisory downstream episode pacing range per block, for example `recommended_episode_count`, `acceptable_episode_range`, `stretch_cap`, and the proof/receipt/gate that must land inside that range
- this pacing hint is not an S2 contract or runtime schema change; it is a writer-facing material-side harness surface used to prevent downstream expansion drift before S2 consumes the pair
- if BI exists, mirror or summarize the same pacing hint in the BI roadmap/payoff surface so TR and BI handoff do not disagree
- canonical pair-side path for newly touched rows: `TR.blocks[*].genre_ext.downstream_episode_pacing_hint` mirrored to `MasterBible.plot_roadmap[*].genre_ext.downstream_episode_pacing_hint`
- current immediate-deployment rows admitted before the range gate keep shelf identity; rows without a bounded attachment audit remain pending range attachment until coverage and mismatch counts are recorded

Current path labels at a glance:

- `material_ssot` = canonical stage root
- `전처리_ssot` = legacy-active transition hub
- `narrative_ssot` = scaffold plus mirror/archive shell
- `material_ssot/10_research/10_reference_profiles` = canonical reference profiles
- `material_ssot/10_research/20_fewshot_bank` = canonical few-shot bank
- `docs/실물기반 사각지대 테스트` = legacy residual research corpus
- `로직_리서치` = deferred non-move
- `treatments/`, `bible/` = live outputs

Current representative work set:

- `gatekeeper_heir`
- `office_checkup_next_day`
- `wuxia_heavenly_physician`

Large artifact write rule:

- do not attempt one-shot overwrite for large live artifacts such as `phase0_design`, `tr_block_070_draft`, or `BI` JSON files
- keep the current bounded execution unit as the write unit; do not widen it just because the target file is large
- maintain parseable JSON on disk after each bounded save step
- if a file is too large for a stable single save, write it incrementally by the current bounded unit and verify the file still parses before continuing
- for `TR`, this never overrides family production rules: block is the base execution unit, and 70-block or 10-block batch generation remains forbidden

Current stage directories:

- `00_governance`
- `10_research`
- `20_pitch`
- `30_stage0_preprocess`
- `40_phase0_design`
- `50_tr`
- `60_bi`
- `90_migration`

This bounded slice is commit-ready for active material-side SSOT operation.
