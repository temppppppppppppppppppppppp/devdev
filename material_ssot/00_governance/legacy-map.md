# Legacy Map

Date: 2026-04-03
Status: active bootstrap map
Scope: path labeling during the material_ssot bootstrap phase

## 1. Label Meanings

| Label | Meaning |
| --- | --- |
| `canonical-stage-root` | path that owns stage-axis governance now |
| `legacy-active` | old path still used in live operations |
| `legacy-frozen` | old path kept as a pointer only; do not write new payloads there |
| `live-output` | current artifact path |
| `mirror` | copied or mirrored reference path, not primary |
| `scaffold` | future-structure candidate, not current authority |
| `deferred-non-move` | intentionally left in place for a later wave |

## 2. Path Label Table

| Path | Label | Why it has that label |
| --- | --- | --- |
| `material_ssot` | `canonical-stage-root` | new stage-axis SSOT root for the material side order |
| `material_ssot/10_research` | `canonical-stage-root` | research stage governance now lives here |
| `material_ssot/10_research/10_reference_profiles` | `canonical-stage-root` | migrated reference profiles now live under the research stage root |
| `material_ssot/10_research/20_fewshot_bank` | `canonical-stage-root` | migrated few-shot bank now lives under the research stage root |
| `material_ssot/10_research/50_corpus_curated` | `canonical-stage-root` | canonical bounded corpus bundles now live under the research stage root |
| `material_ssot/10_research/60_corpus_longtail` | `canonical-stage-root` | canonical longtail title corpus now lives under the research stage root |
| `material_ssot/20_pitch` | `canonical-stage-root` | pitch stage governance now lives here |
| `material_ssot/20_pitch/intake/legacy_import` | `canonical-stage-root` | migrated legacy pitch payloads now sit under the pitch stage root |
| `material_ssot/20_pitch/quarantine` | `canonical-stage-root` | non-canonical pitch-adjacent docs are isolated here |
| `material_ssot/30_stage0_preprocess` | `canonical-stage-root` | Stage 0 preprocess stage governance now lives here |
| `material_ssot/40_phase0_design` | `canonical-stage-root` | Phase 0 design stage governance now lives here |
| `material_ssot/50_tr` | `canonical-stage-root` | TR stage governance now lives here |
| `material_ssot/60_bi` | `canonical-stage-root` | BI stage governance now lives here |
| `전처리_ssot` | `legacy-active` | still used as transition hub and Stage 0 governance carryover |
| `전처리_ssot/docs/10_pitches` | `legacy-active` | current best transition hub for pitch documents |
| `전처리_ssot/기획안` | `legacy-frozen` | old pitch bundle payloads were moved out on 2026-04-03 and the path now serves as a pointer only |
| `docs/실물기반 사각지대 테스트` | `legacy-active` | residual research corpus root kept in place during the staged research cutover |
| `docs/실물기반 사각지대 테스트/원고` | `legacy-frozen` | root now holds provenance files and pointer shells after Wave 4 longtail migration |
| `docs/실물기반 사각지대 테스트/원고/titles` | `legacy-frozen` | old longtail title path is now a pointer-only shell |
| `material_ssot/10_research/40_analysis/pattern_reports` | `canonical-stage-root` | canonical long-form analysis reports now live here |
| `docs/실물기반 사각지대 테스트/분석` | `legacy-frozen` | moved analysis payloads were cut over on 2026-04-03 and this path now serves as a pointer only |
| `docs/실물기반 사각지대 테스트/분석결과_회차간_연결패턴_분석.md` | `legacy-frozen` | moved analysis report now lives under `material_ssot/10_research/40_analysis/pattern_reports` |
| `treatments/preprocess/` | `live-output` | current preprocess live artifact root |
| `treatments/` | `live-output` | current Phase 0 and TR live artifact root |
| `bible/` | `live-output` | current BI live artifact root |
| `narrative_ssot/10_reference_bank` | `mirror` | reference bank mirror, not the primary authority |
| `narrative_ssot` | `scaffold` | future-structure candidate and pilot scaffold |
| `로직_리서치` | `deferred-non-move` | explicitly left in place for a later research wave |

## 3. Bootstrap Rule

Do not cut over a path only because it is labeled here.

The label order is:

1. identify the label
2. connect the path through manifests
3. cut or move only in a later wave
