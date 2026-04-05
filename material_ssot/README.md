# material_ssot

Date: 2026-04-03
Status: active bounded SSOT
Scope: material-side stage SSOT only

`material_ssot` is the stage-axis SSOT for the material side order.

Design baseline:

- `docs/2026-04-03/material-side-order-ssot-design.md`

Official stage chain:

`리서치 -> 기획안 -> Stage 0 preprocess -> Phase 0 design -> TR 생성 -> BI 생성`

Quick start read order:

1. `00_governance/bootstrap-status.md`
2. `00_governance/authority-map.md`
3. `00_governance/stage-read-order.md`
4. `00_governance/work-coverage-matrix.md`
5. one representative work chain under `30_stage0_preprocess/work-index/`

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
- `00_governance/legacy-map.md`
- `00_governance/work-coverage-matrix.md`
- `00_governance/bootstrap-status.md`

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
