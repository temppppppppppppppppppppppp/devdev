# Authority Map

Date: 2026-04-03
Status: active bounded map
Scope: material-side stage authority only

This document answers one operational question:

`지금 이 단계는 어디를 stage SSOT로 읽고, 어디를 live path로 보고, 어떤 경로를 legacy / mirror / deferred로 취급해야 하는가?`

This map does not replace family routing. `docs/narrative-router` remains the family-axis router.

## 1. Stage Table

| Stage | Stage SSOT root | Current canonical or authoritative path | Current live artifact path | Legacy-active path | Mirror or scaffold path | Deferred non-move path | Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Research | `material_ssot/10_research` | `material_ssot/10_research/10_reference_profiles`, `material_ssot/10_research/20_fewshot_bank`, `material_ssot/10_research/40_analysis/pattern_reports`, `material_ssot/10_research/50_corpus_curated`, and `material_ssot/10_research/60_corpus_longtail` | none | `docs/실물기반 사각지대 테스트` provenance and pointer shell | `narrative_ssot/10_reference_bank` | `로직_리서치` | Wave 1 moved reference profiles and the few-shot bank; Wave 2 moved long-form analysis reports; Wave 3 moved bounded top-level corpus bundles; Wave 4 moved the longtail title corpus; only provenance files and pointer shells remain under the old research root |
| Pitch | `material_ssot/20_pitch` | `material_ssot/20_pitch/canon` for anchors and `material_ssot/20_pitch/intake/legacy_import` for migrated payloads | none | `전처리_ssot/docs/10_pitches` | none | none | old `전처리_ssot/기획안` payloads were moved into the stage SSOT; QA summaries are quarantined |
| Stage 0 preprocess | `material_ssot/30_stage0_preprocess` | `material_ssot/30_stage0_preprocess` for stage governance | `treatments/preprocess/{work_id}` | `전처리_ssot` | `narrative_ssot` | none | legacy governance and live preprocess are currently split |
| Phase 0 design | `material_ssot/40_phase0_design` | preferred root file: `treatments/{work_id}_phase0_design.json` | `treatments/{work_id}_phase0_design.json` or preprocess fallback | none | none | none | fallback source is `treatments/preprocess/{work_id}/phase0_ready_snapshot.json` |
| TR | `material_ssot/50_tr` | `treatments/{work_id}_tr_block_070_draft.json` | `treatments/{work_id}_tr_block_070_draft.json` | none | none | none | routed and harness paths currently guarantee canonical TR output |
| BI | `material_ssot/60_bi` | `bible/0_bi_{work_id}.json` | `bible/0_bi_{work_id}.json` | none | none | none | routed and harness paths currently guarantee canonical BI output |

## 2. Cross-Axis Table

| Axis | Current authority | Current role |
| --- | --- | --- |
| Stage axis | `material_ssot` | material-side stage SSOT |
| Family axis | `docs/narrative-router` | family routing and family harness entry |
| Reference scaffold axis | `narrative_ssot` | scaffold plus cards mirror and archive residue shell |
| Live output axis | `treatments/`, `bible/` | live narrative artifacts |

## 3. Representative Work Set

The representative work manifests in this bounded slice are anchored on:

- `gatekeeper_heir`
- `office_checkup_next_day`
- `wuxia_heavenly_physician`

These works were chosen because they already have stable live preprocess, TR, and BI paths.

## 4. Operating Rule

When a path question comes up during the current bounded slice, resolve it in this order:

1. stage SSOT root
2. current authoritative path for that stage
3. current live artifact path
4. legacy, mirror, scaffold, or deferred label
