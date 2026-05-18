# Stage Read Order

Date: 2026-04-03
Status: active bounded read order
Scope: material-side stage progression only

## 1. Default Read Order

1. `material_ssot/README.md`
2. `material_ssot/00_governance/authority-map.md`
3. `material_ssot/00_governance/legacy-map.md`
4. `material_ssot/10_research`
5. `material_ssot/20_pitch`
6. `material_ssot/30_stage0_preprocess`
7. `material_ssot/40_phase0_design`
8. `material_ssot/50_tr`
9. `material_ssot/60_bi`

## 2. Stage Entry Rule

### A. Research

- read `10_research/README.md`
- read `10_research/source-map.md`
- then read `10_research/10_reference_profiles/`
- then read `10_research/20_fewshot_bank/`
- then read `10_research/40_analysis/pattern_reports/` when reusable interpretation reports are needed
- then read `10_research/50_corpus_curated/` when representative corpus text is needed
- then read `10_research/60_corpus_longtail/` when longtail title corpus evidence is needed
- open `docs/실물기반 사각지대 테스트/원고/titles/README.md` only as a frozen pointer
- treat `로직_리서치` as a legacy runtime note root, not a stage authority root

### B. Pitch

- read `20_pitch/README.md`
- read `20_pitch/cider-doctrine-v1.md` immediately after the README
- read `20_pitch/material-benchmark-readiness-harness-v1.md` before calling any pitch selection-ready or `Phase0-ready`
- read `20_pitch/pitch-philosophy.md` before touching synthesis or canon promotion
- read `00_governance/donor-review-and-adoption-contract-v1.md` before calling a fresh candidate `Phase0-ready` or a touched pair `TR/BI-ready`
- when building a fresh candidate from reusable material truth, start with `20_pitch/synthesis/README.md`
- place the one-page operator handoff under `20_pitch/synthesis/` before promoting anything into canon
- run `20_pitch/pitch-selection-checklist.md` before calling a synthesis selection-ready
- use `20_pitch/canon/` for work-level pitch anchors
- use `20_pitch/work-guard-translation-map.md` only after pitch truth is frozen enough to translate into a work-specific guard
- if the material must feed Firefly/S4 or writer-facing output, read `C:\Users\User\Desktop\글도비_파이어플라이\docs\material_ssot\geuldobi_handoff\C:\Users\User\Desktop\글도비_파이어플라이\docs\material_ssot\geuldobi_handoff\00_governance\firefly-s4-scene-native-material-bridge-v1.md` before Phase0/TR expansion and verify that scene-native handoff semantics exist
- before any full 70-block production TR for Firefly/S4-bound material, read `C:\Users\User\Desktop\글도비_파이어플라이\docs\material_ssot\geuldobi_handoff\00_governance\firefly-b1-b2-micro-canary-before-70-harness-v1.md` and require B1-B2 or EP001 micro-canary proof
- use `20_pitch/intake/legacy_import/` for migrated legacy pitch payloads
- use `20_pitch/quarantine/` only for non-canonical pitch-adjacent docs
- treat `전처리_ssot/docs/10_pitches` as legacy transition docs
- treat `전처리_ssot/기획안` as a frozen pointer path

### C. Stage 0 preprocess

- read `30_stage0_preprocess/README.md`
- then use the work manifest under `30_stage0_preprocess/work-index/`
- then open the live preprocess directory under `treatments/preprocess/{work_id}`
- preferred live files:
  - `source_manifest.json`
  - `profile_lock.json`
  - `material_bundle_summary.json`
  - `phase0_ready_snapshot.json` when needed

### D. Phase 0 design

- read `40_phase0_design/README.md`
- prefer `treatments/phase0/{work_id}_phase0_design.json` when it exists
- otherwise fall back to `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`
- keep donor decision visibility checked here before calling a work `TR-ready`
- if the work follows the standard material-side path, check companion `work_guard` visibility here before entering `TR`
- this companion check is advisory only and does not rewrite current stage detection

### E. TR

- read `50_tr/README.md`
- use `treatments/NN_{work_id}_tr_block_070_draft.json` when the work is in the numbered live set
- otherwise fall back to `treatments/{work_id}_tr_block_070_draft.json`
- keep donor decision visibility checked before calling a pair `TR-ready` or `pair complete`
- if a frozen work-specific guard exists, keep its library path visible during early `TR` drift checks

### F. BI

- read `60_bi/README.md`
- use `bible/NN_bi_{work_id}.json` when the work is in the numbered live set
- otherwise fall back to `bible/0_bi_{work_id}.json`
- keep donor decision visibility checked before calling a pair `BI-ready`, promotion-target, or active baseline candidate

## 3. Boundary Rules

- family choice is still resolved by `docs/narrative-router`
- system-track execution remains outside this root
- this order governs stage progression only
- work manifests are the preferred way to connect legacy and live paths during the current bounded slice
