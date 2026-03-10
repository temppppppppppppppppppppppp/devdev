# Next-Step Harness Docs 3PASS Audit (2026-03-10)

## Targets
- planning: `docs/blockguide/treatment-planning-harness.md`
- treatment: `docs/blockguide/treatment-production-harness-v2.md`
- bi: `docs/blockguide/bi-production-harness-v1.md`

## PASS 1 structure
- result: OK
- planning_section_present: OK
- treatment_section_present: OK
- bi_section_present: OK
- all_utf8_readable: OK

## PASS 2 consistency
- result: OK
- planning_ends_at_phase0_json: OK
- treatment_handles_draft_and_handoff: OK
- bi_starts_from_tr_draft: OK
- all_docs_use_next_step_trigger: OK
- one_unit_per_turn_declared: OK

## PASS 3 actionability
- result: OK
- planning_has_rules_order_ban: OK
- treatment_has_rules_table_stop: OK
- bi_has_handoff_table_rules: OK
- bi_mentions_utf8_audit: OK
- flow_covers_planning_to_bi: OK

## Notes
- scope: reinforced existing blockguide docs instead of adding a separate fourth harness doc
- design choice: a single `next-step` trigger now bridges planning -> treatment -> BI handoff
- overall: PASS

