# scripts/

Operator-facing utility scripts. Not imported by production runtime.

## Categories

- **ops governance**: `ops_validator.py`, `sync_temp_queue_state.py`, `build_execution_roadmap.py`, `populate_process_health_scorecard.py`, `generate_evidence_manifest.py`, `validate_deep_global_survey_bundle.py`, `run_stale_reference_sweep.py`, `validate_material_ssot.py`, `validate_claude_local_paths.py`
- **external visibility sync**: `sync_clickup_queue.py`
- **material-side ClickUp sync**: `build_material_queue_state.py`, `sync_material_clickup_queue.py`
- **ClickUp view setup**: `setup_clickup_views.py`, `setup_material_clickup_views.py`
- **material readiness validation**: `material_readiness_validator.py`
- **material promotion gate**: `material_promotion_gate.py`
- **repo preflight gate**: `pre_new_pitch_readiness_gate.py`
- **pair normalization governance**: `production_pair_normalization_runner.py`
- **opening pacing triage governance**: `production_pair_opening_pacing_triage_runner.py`
- **material benchmark launch generation**: `material_benchmark_order_generator.py`
- **material benchmark batch launch generation**: `material_benchmark_batch_generator.py`
- **UTF-8 hygiene**: `check_utf8_hygiene.py`, `mojibake_global_survey.py`
- **narrative pipeline**: `narrative_router.py`, `narrative_tr_batch.py`, `build_narrative_bi.py`, `audit_narrative_bi.py`, `build_bi_from_phase0_and_tr.py`, `build_wuxia_bi_from_phase0_and_tr.py`, `audit_bi_5pass.py`, `audit_wuxia_bi_5pass.py`, `generate_tr_bibles.py`, `create_narrative_project_scaffold.py`, `sync_narrative_reference_bank.py`
- **narrative scaffold enrichment**: `build_stage0_from_reference_selection.py`
- **planning seed enrichment**: `build_phase0_seed_from_stage0.py`
- **material-side companions**: `run_work_guard_v1.py`
- **data/corpus build**: `build_investment_*.py`, `build_chaebol_*.py`, `build_fallen_prince_*.py`, `build_title_style_control_dataset.py`, `extract_manuscript_samples.py`
- **bounded density baseline build**: `bundle_density_snapshot.py`
- **test support**: `run_pytest_lowmem.py`, `e2e_menu_smoke.ps1`
- **one-shot diagnostics**: `backfill_quality_sidecars.py`, `generate_stagewise_manuscript_truth_report.py`

## Key entry points

| Task | Script |
| --- | --- |
| Validate temp queue + governance | `python scripts/ops_validator.py` |
| Validate bounded `material_ssot` authority, representative work coverage, corpus metadata, and stale-path invariants | `python -X utf8 scripts/validate_material_ssot.py` |
| Validate future canon/intake/synthesis candidate markdown files against the readiness contract | `python -X utf8 scripts/material_readiness_validator.py --path <md-or-dir>` |
| Run the real promotion gate before canon or Phase0 transition | `python -X utf8 scripts/material_promotion_gate.py --stage canon|phase0 --path <md> [--work-id <work_id>]` |
| Run the repo-level preflight before a fresh pitch wave | `python -X utf8 scripts/pre_new_pitch_readiness_gate.py` |
| Audit live BI/TR pairs against the current normalization standard | `python -X utf8 scripts/production_pair_normalization_runner.py [--work-id <work_id>] [--json]` |
| Triage live TR pairs into `RED/YELLOW/GREEN` opening pacing buckets before repair waves | `python -X utf8 scripts/production_pair_opening_pacing_triage_runner.py [--work-id <work_id>] [--json]` |
| Build a bounded empirical `2~6 episode` density baseline from curated corpus folders | `python -X utf8 scripts/bundle_density_snapshot.py --corpus-dir <dir> [--corpus-dir <dir> ...] [--output <json>]` |
| Generate a filled material benchmark prompt file plus a one-line external-model launch order | `python -X utf8 scripts/material_benchmark_order_generator.py --pitch <pitch-md> [--promotion-intent none|canon|phase0]` |
| Generate prompt files and one-line launch orders in batch across canon/intake/synthesis | `python -X utf8 scripts/material_benchmark_batch_generator.py [--path <dir>] [--promotion-intent auto|none|canon|phase0]` |
| Validate `.claude` local-path portability for active GSD docs | `python -X utf8 scripts/validate_claude_local_paths.py` |
| Materialize temp queue state | `python scripts/sync_temp_queue_state.py` |
| Mirror the current repo-side queue into a ClickUp List | `python -X utf8 scripts/sync_clickup_queue.py --list-id <clickup-list-id> [--dry-run]` |
| Build the material-side production queue snapshot for ClickUp mirroring | `python -X utf8 scripts/build_material_queue_state.py [--output docs/temp/material-queue-state.json] [--active-only]` |
| Mirror the material-side production queue into a ClickUp List | `python -X utf8 scripts/sync_material_clickup_queue.py --list-id <clickup-list-id> [--dry-run] [--active-only]` |
| Create the recommended ClickUp board/table views for the mirrored queue | `python -X utf8 scripts/setup_clickup_views.py --list-id <clickup-list-id> [--dry-run]` |
| Create the recommended material-side board/table views for the production schedule list | `python -X utf8 scripts/setup_material_clickup_views.py --list-id <clickup-list-id> [--dry-run]` |

ClickUp sync notes:

- the script loads root `.env` first, then overrides ClickUp-specific values from `secrets/clickup.env` when present
- set `CLICKUP_ENV_FILE` if you want the ClickUp-only env file in a different path
- material-side sync may additionally use `CLICKUP_MATERIAL_ENV_FILE`, `CLICKUP_MATERIAL_LIST_ID`, and `CLICKUP_MATERIAL_STATUS_MAP_JSON`
- material-side sync defaults to a stage-visible schedule: `canon` + `TR/BI production` + `BI complete`
- use `--active-only` if you want to hide completed items and show only canon/in-flight work
- if the material production list later gets manual custom fields, the sync is already field-ready for these names:
  - `Work ID`
  - `Material Stage`
  - `Ops State`
  - `Current Truth Path`
  - `Sequential Status Path`
  - `Last Sequential Block Pass`
  - `Next Unit Type`
  - `Next Block ID`
  - `Resume Basis`
  - `Production Complete`
  - `BI Complete`
  - `Updated At`
| Check UTF-8 hygiene | `python scripts/check_utf8_hygiene.py <files>` |
| Run `WG-V1` shape validation on a draft or publishable `work_guard` | `python -X utf8 scripts/run_work_guard_v1.py --path <yaml>` |
| Build execution roadmap, optionally rewriting queue-state ranks to dependency-respecting order first | `python scripts/build_execution_roadmap.py [--rewrite-roadmap-ranks]` |
| Create a `narrative_ssot` project scaffold | `python -X utf8 scripts/create_narrative_project_scaffold.py --work-id <work_id>` |
| Build Stage0 preprocess drafts from selected reference cards and optional title/profile/opening overrides | `python -X utf8 scripts/build_stage0_from_reference_selection.py --work-id <work_id>` |
| Build a Phase0 planning seed from Stage0 authority | `python -X utf8 scripts/build_phase0_seed_from_stage0.py --work-id <work_id>` |
| Sync `few-shot-bank` into `narrative_ssot` mirror | `python -X utf8 scripts/sync_narrative_reference_bank.py` |
