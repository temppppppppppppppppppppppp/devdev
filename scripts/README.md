# scripts/

Operator-facing utility scripts. Not imported by production runtime.

## Categories

- **ops governance**: `ops_validator.py`, `sync_temp_queue_state.py`, `build_execution_roadmap.py`, `populate_process_health_scorecard.py`, `generate_evidence_manifest.py`, `validate_deep_global_survey_bundle.py`, `run_stale_reference_sweep.py`
- **UTF-8 hygiene**: `check_utf8_hygiene.py`, `mojibake_global_survey.py`
- **narrative pipeline**: `narrative_router.py`, `narrative_tr_batch.py`, `build_narrative_bi.py`, `audit_narrative_bi.py`, `build_bi_from_phase0_and_tr.py`, `build_wuxia_bi_from_phase0_and_tr.py`, `audit_bi_5pass.py`, `audit_wuxia_bi_5pass.py`, `generate_tr_bibles.py`
- **data/corpus build**: `build_investment_*.py`, `build_chaebol_*.py`, `build_fallen_prince_*.py`, `build_title_style_control_dataset.py`, `extract_manuscript_samples.py`
- **test support**: `run_pytest_lowmem.py`, `e2e_menu_smoke.ps1`
- **one-shot diagnostics**: `backfill_quality_sidecars.py`, `generate_stagewise_manuscript_truth_report.py`

## Key entry points

| Task | Script |
| --- | --- |
| Validate temp queue + governance | `python scripts/ops_validator.py` |
| Materialize temp queue state | `python scripts/sync_temp_queue_state.py` |
| Check UTF-8 hygiene | `python scripts/check_utf8_hygiene.py <files>` |
| Build execution roadmap | `python scripts/build_execution_roadmap.py` |
