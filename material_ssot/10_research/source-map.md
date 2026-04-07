# Research Source Map

Date: 2026-04-03
Status: active Wave 4 map

## 1. Current Source Classes

- research stage root: `material_ssot/10_research`
- canonical source registry: `material_ssot/10_research/00_registry`
- canonical reference profiles: `material_ssot/10_research/10_reference_profiles`
- canonical few-shot bank: `material_ssot/10_research/20_fewshot_bank`
- normalized work material packs: `material_ssot/10_research/30_work_materials`
- promoted analysis snapshots: `material_ssot/10_research/40_analysis/market_snapshots`
- canonical long-form analysis reports: `material_ssot/10_research/40_analysis/pattern_reports`
- canonical reusable source corpora: `material_ssot/10_research/40_analysis/source_corpora`
- canonical curated corpus bundles: `material_ssot/10_research/50_corpus_curated`
- canonical longtail title corpus: `material_ssot/10_research/60_corpus_longtail`
- promoted raw ingest bucket: `material_ssot/10_research/80_ingest_raw`
- residual raw corpus and legacy pointer root: `docs/실물기반 사각지대 테스트`
- non-SSOT legacy runtime note root: `로직_리서치`
- any future raw research bucket: deferred and non-move in this wave

## 2. Current Reference Clusters

### A. Business / office / investment side

- `10_reference_profiles/투자물_문체_정량_프로파일.md`
- `10_reference_profiles/2026-03-30_modern_business_reference_master_order.md`
- `20_fewshot_bank/투자물_현판.yaml`
- `20_fewshot_bank/investment_engine_pack.md`

### B. Wuxia side

- `10_reference_profiles/무협_곤륜마협_문체프로파일.md`
- `10_reference_profiles/무협_곤륜마협_클리프행어.md`
- `10_reference_profiles/무협_곤륜마협_화간연결.md`
- `10_reference_profiles/무협_파공검제_문체프로파일.md`
- `10_reference_profiles/무협_파공검제_클리프행어.md`
- `10_reference_profiles/무협_파공검제_화간연결.md`
- `20_fewshot_bank/무협_곤륜마협.yaml`
- `20_fewshot_bank/무협_파공검제.yaml`

## 3. Residual Legacy Research Surfaces

- `docs/실물기반 사각지대 테스트/원고/manifest.json`
- `docs/실물기반 사각지대 테스트/원고/errors.log`
- `docs/실물기반 사각지대 테스트/원고/titles/README.md`

These paths remain readable but are no longer the canonical home for moved reference profiles, the few-shot bank, moved analysis reports, moved curated corpus bundles, or the migrated longtail title corpus.

## 4. Canonical Analysis Reports

- `40_analysis/pattern_reports/분석결과_회차간_연결패턴_분석.md`
- `40_analysis/pattern_reports/자하검신_ep051-100_분석.md`

## 4A. Canonical Reusable Source Corpora

- `40_analysis/source_corpora/platform_trends/kr_serial_platforms`
- `40_analysis/source_corpora/youtube/syukaworld`
- first bounded cutover in this lane repoints the platform-trend builders away from the old narrative reference-bank source-corpora platform-trend lane
- second bounded cutover in this lane repoints the syukaworld builders away from the old narrative reference-bank source-corpora YouTube lane
- old narrative reference-bank source-corpora lanes should now be treated as transition residue after the pointer/archive pass

## 5. Canonical Curated Corpus

- `50_corpus_curated/curated_index.md`
- `50_corpus_curated/`
- `50_corpus_curated/reference_samples/medical_magical_surgeon_sample_corpus`
- third bounded cutover in this lane repoints the NAS medical sample builder away from the old narrative reference-bank source-corpora NAS medical sample lane; fresh NAS rebuild validation remains cross-PC

## 6. Canonical Longtail Corpus

- `60_corpus_longtail/longtail_index.md`
- `60_corpus_longtail/titles/`

## 7. Normalized Work Material Packs

- `30_work_materials/` is the canonical home for work-level normalized research handoff packs
- each pack should separate:
  - user agreements
  - fact lock
  - domain map
  - narrative seed bank
  - pattern references
  - gap log
  - final `material_pack`
- representative bounded packs present:
  - `30_work_materials/office_checkup_next_day/90_material_pack.json`
  - `30_work_materials/wuxia_heavenly_physician/90_material_pack.json`
- raw corpus pinning remains optional until a later wave

## 8. Bootstrap Rule

- register source roots and clusters here first
- bind work-level research under `10_research/manifests/`
- normalize work-level packs under `10_research/30_work_materials/`
- feed reusable engine packs and normalized work-level packs into `material_ssot/20_pitch/synthesis/` before canon selection
- promote collector outputs into `40_analysis/` or `80_ingest_raw/` before citing them as stage authority
- promote reusable long-form analysis reports into `40_analysis/pattern_reports/`
- promote bounded representative corpus bundles into `50_corpus_curated/`
- promote longtail title corpus into `60_corpus_longtail/` when it becomes structurally stable
- keep only provenance logs and pointer shells in old roots after corpus migration

## 9. Logic Research Treatment

- `로직_리서치` is no longer interpreted as a stage authority root
- current treatment:
  - collector scripts now live under `scripts/research_collectors`
  - `output/_*.jsonl` was promoted into `80_ingest_raw/2026-04-03`
  - dated `output/*.json` and `output/*.csv` were promoted into `40_analysis/market_snapshots/2026-04-03`
  - `로직_리서치/output` is now a pointer-only legacy path
  - new collector runs write directly into dated `80_ingest_raw/` and `40_analysis/market_snapshots/` buckets
  - operator notes should be promoted into `00_registry/` before they become canonical guidance
