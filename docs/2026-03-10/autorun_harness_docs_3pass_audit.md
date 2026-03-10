# Auto-Run Harness Docs 3PASS Audit (2026-03-10)

## Targets
- planning: `docs/blockguide/treatment-planning-harness.md`
- treatment: `docs/blockguide/treatment-production-harness-v2.md`
- bi: `docs/blockguide/bi-production-harness-v1.md`

## PASS 1 structure
- result: OK
- planning_autorun_section: OK
- treatment_autorun_section: OK
- bi_autorun_section: OK
- all_utf8_readable: OK

## PASS 2 consistency
- result: OK
- all_docs_autorun_optional: OK
- all_docs_have_stop_gate: OK
- planning_to_treatment_handoff_kept: OK
- treatment_to_bi_handoff_kept: OK
- bi_requires_tr_draft: OK

## PASS 3 actionability
- result: OK
- planning_has_end_condition: OK
- treatment_has_step_checks: OK
- bi_has_ordered_steps: OK
- bi_blocks_cleanup_before_pass: OK
- full_chain_present: OK

## Notes
- auto-run is optional, not default
- stop gates are declared in planning, treatment, and BI docs
- overall: PASS

