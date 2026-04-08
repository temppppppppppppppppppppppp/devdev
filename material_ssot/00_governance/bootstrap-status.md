# Bootstrap Status

Date: 2026-04-08
Status: active bounded status
Scope: commit-ready summary for the current `material_ssot` slice

## 1. What Is Done

- `material_ssot` root is created
- stage-axis governance is separated from family-axis routing
- authority and legacy maps are written
- stage read order is written
- research Wave 1 moved reference profiles into `material_ssot/10_research/10_reference_profiles`
- research Wave 1 moved the few-shot bank into `material_ssot/10_research/20_fewshot_bank`
- research Wave 1.5 opened `material_ssot/10_research/30_work_materials`
- research Wave 2 moved long-form analysis reports into `material_ssot/10_research/40_analysis/pattern_reports`
- research Wave 3 moved bounded reusable source corpora into `material_ssot/10_research/40_analysis/source_corpora`
- research Wave 3.5 moved the bounded NAS medical sample corpus into `material_ssot/10_research/50_corpus_curated/reference_samples`
- research Wave 4 moved the longtail title corpus into `material_ssot/10_research/60_corpus_longtail`
- normalized work-level research packs now exist at:
  - `material_ssot/10_research/30_work_materials/office_checkup_next_day/90_material_pack.json`
  - `material_ssot/10_research/30_work_materials/wuxia_heavenly_physician/90_material_pack.json`
- legacy pitch bundle payloads are moved under `material_ssot/20_pitch/intake/legacy_import`
- canonical pitch philosophy now exists at `material_ssot/20_pitch/pitch-philosophy.md`
- active canonical pitch exemplar now exists at `material_ssot/20_pitch/canon/office_checkup_next_day.md`
- pitch-adjacent QA summaries are isolated under `material_ssot/20_pitch/quarantine`
- `narrative_ssot/10_reference_bank` now operates as a cards mirror plus archive residue shell, not as research authority
- bounded machine validation now exists at `python -X utf8 scripts/validate_material_ssot.py`
- repo-level pre-new-pitch readiness gate now exists at `python -X utf8 scripts/pre_new_pitch_readiness_gate.py`
- canonical pair normalization wave now closes all current tracked pairs under one schema runner
- current live pair inventory and benchmark freshness now have a durable registry under `production-pair-operational-registry-v1.md`
- all currently tracked schema-clean pairs now carry benchmark-fresh readings, including the previously unbenchmarked unslotted live pairs

## 2. What Is Intentionally Not Done

- no wholesale raw research migration was attempted
- `로직_리서치` remains deferred and non-move
- `전처리_ssot` was not cut over
- `전처리_ssot/docs/10_pitches` was not cut over
- `narrative_ssot` was not merged
- live artifact roots `treatments/` and `bible/` were not moved

## 3. Current Gaps

- representative work coverage is still bounded to two works
- `office_checkup_next_day`: work-level raw research path is not yet pinned
- `wuxia_heavenly_physician`: work-level raw research path is not yet pinned
- both normalized packs still keep raw corpus pinning deferred
- NAS fresh rebuild verification still belongs to another machine

## 4. Why This Slice Is Stable

- stage-axis SSOT is now explicit under `material_ssot`
- family-axis routing is still isolated under `docs/narrative-router`
- legacy-active, scaffold, mirror, and deferred paths are labeled before any cutover
- research reference profiles and few-shot cards now have one canonical stage root under `material_ssot/10_research`
- `office_checkup_next_day` and `wuxia_heavenly_physician` can now be read from normalized research packs
- active pitch references now point to `material_ssot/20_pitch` paths instead of the old payload bundle
- representative work manifests still connect the current live chain without relocating production artifacts
- pair-side schema readiness, benchmark freshness, and new-pitch preflight now have explicit governance surfaces instead of operator memory

## 5. Recommended Next Step

Recommended next step after this bounded slice:

1. snapshot or commit this documentation slice
2. later decide whether to:
   - add one more representative work into the matrix, or
   - promote `90_migration/pending-cuts.md` into an active next-wave queue
