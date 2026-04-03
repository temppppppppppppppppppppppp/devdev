# 10_research

Role:

- own the research stage authority for the material-side order
- keep canonical reference packs under this root
- normalize work-level material packs under this root
- keep registry, promoted analysis snapshots, and promoted raw ingest buckets under this root
- leave raw corpus and deferred research buckets in place until later waves

Current approach:

- use `source-map.md` to map canonical packs, residual corpus, and deferred buckets
- treat `10_reference_profiles/` as the canonical reference-profile pack
- treat `20_fewshot_bank/` as the canonical few-shot bank
- treat `30_work_materials/{work_id}/90_material_pack.json` as the normalized work-level research handoff when present
- treat `00_registry/` as the authority map for non-SSOT runtime research surfaces
- treat `40_analysis/market_snapshots/` as the home for promoted collector snapshots
- treat `40_analysis/pattern_reports/` as the home for canonical long-form analysis reports
- treat `50_corpus_curated/` as the home for bounded representative corpus bundles
- treat `60_corpus_longtail/` as the home for migrated longtail title corpus bundles
- treat `80_ingest_raw/` as the home for promoted raw ingest evidence
- treat `scripts/research_collectors/` as the active runtime collector code root
- treat `docs/실물기반 사각지대 테스트/원고` as a residual provenance and pointer shell
- treat `로직_리서치` as a non-SSOT legacy runtime note root
- note that `로직_리서치/output` has already been cut over and is now pointer-only
- use `manifests/` for light work-level research linkage and pack discovery
