# scripts/

Operator-facing utility scripts. Not imported by production runtime.

## Categories

- **ops governance**: `ops_validator.py`, `sync_temp_queue_state.py`, `build_execution_roadmap.py`, `populate_process_health_scorecard.py`, `generate_evidence_manifest.py`, `validate_deep_global_survey_bundle.py`, `run_stale_reference_sweep.py`, `validate_material_ssot.py`, `validate_claude_local_paths.py`
- **material readiness validation**: `material_readiness_validator.py`
- **material promotion gate**: `material_promotion_gate.py`
- **repo preflight gate**: `pre_new_pitch_readiness_gate.py`
- **pair normalization governance**: `production_pair_normalization_runner.py`
- **material benchmark launch generation**: `material_benchmark_order_generator.py`
- **material benchmark batch launch generation**: `material_benchmark_batch_generator.py`
- **UTF-8 hygiene**: `check_utf8_hygiene.py`, `mojibake_global_survey.py`
- **narrative pipeline**: `narrative_router.py`, `narrative_tr_batch.py`, `build_narrative_bi.py`, `audit_narrative_bi.py`, `build_bi_from_phase0_and_tr.py`, `build_wuxia_bi_from_phase0_and_tr.py`, `audit_bi_5pass.py`, `audit_wuxia_bi_5pass.py`, `generate_tr_bibles.py`, `create_narrative_project_scaffold.py`, `sync_narrative_reference_bank.py`
- **material-side companions**: `run_work_guard_v1.py`
- **data/corpus build**: `build_investment_*.py`, `build_chaebol_*.py`, `build_fallen_prince_*.py`, `build_title_style_control_dataset.py`, `extract_manuscript_samples.py`
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
| Generate a filled material benchmark prompt file plus a one-line external-model launch order | `python -X utf8 scripts/material_benchmark_order_generator.py --pitch <pitch-md> [--promotion-intent none|canon|phase0]` |
| Generate prompt files and one-line launch orders in batch across canon/intake/synthesis | `python -X utf8 scripts/material_benchmark_batch_generator.py [--path <dir>] [--promotion-intent auto|none|canon|phase0]` |
| Validate `.claude` local-path portability for active GSD docs | `python -X utf8 scripts/validate_claude_local_paths.py` |
| Materialize temp queue state | `python scripts/sync_temp_queue_state.py` |
| Check UTF-8 hygiene | `python scripts/check_utf8_hygiene.py <files>` |
| Run `WG-V1` shape validation on a draft or publishable `work_guard` | `python -X utf8 scripts/run_work_guard_v1.py --path <yaml>` |
| Build execution roadmap | `python scripts/build_execution_roadmap.py` |
| Create a `narrative_ssot` project scaffold | `python -X utf8 scripts/create_narrative_project_scaffold.py --work-id <work_id>` |
| Sync `few-shot-bank` into `narrative_ssot` mirror | `python -X utf8 scripts/sync_narrative_reference_bank.py` |
