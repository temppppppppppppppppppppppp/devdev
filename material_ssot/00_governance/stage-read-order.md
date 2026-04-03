# Stage Read Order

Date: 2026-04-03
Status: active bootstrap read order
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
- use `20_pitch/canon/` for work-level pitch anchors
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
- prefer `treatments/{work_id}_phase0_design.json` when it exists
- otherwise fall back to `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`

### E. TR

- read `50_tr/README.md`
- use `treatments/{work_id}_tr_block_070_draft.json` as the live TR artifact

### F. BI

- read `60_bi/README.md`
- use `bible/0_bi_{work_id}.json` as the live BI artifact

## 3. Boundary Rules

- family choice is still resolved by `docs/narrative-router`
- system-track execution remains outside this root
- this order governs stage progression only
- work manifests are the preferred way to connect legacy and live paths during the bootstrap phase
