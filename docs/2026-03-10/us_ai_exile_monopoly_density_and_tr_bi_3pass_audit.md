# Density Review and TR-BI 3-Pass Audit (2026-03-10)

## Targets
- phase0: `treatments/us_ai_exile_monopoly_phase0_design.json`
- tr: `treatments/us_ai_exile_monopoly_tr_block_070_draft.json`
- bi: `bible/0_bi_us_ai_exile_monopoly.json`

## Production Readiness
- production_readiness: PASS
- verdict: density and consistency are both production-ready.

## Density Metrics
- us_ai avg_chars: 1044.8
- reference avg_chars: 436.5
- us_ai avg_relationships: 2.36
- us_ai avg_foreshadow: 1.24
- us_ai avg_callback: 1.24
- us_ai unique_deal_types: 70 (top repetition 1)
- us_ai unique_methods: 70 (top repetition 1)
- us_ai unique_locations: 70
- us_ai unique_opponents: 10
- us_ai unique_success_patterns: 7
- jaccard_high_pair_ratio: 0.2944

## Density Findings
- avg_chars gate: OK
- foreshadow gate: OK
- callback gate: OK
- relationship density gate: OK
- deal_type repetition gate: OK
- method repetition gate: OK
- reward restatement gate: OK
- current draft is no longer a skeleton draft.

## PASS 1
- result: OK
- phase0_utf8_parse: OK
- tr_utf8_parse: OK
- bi_utf8_parse: OK
- garbled_zero: OK

## PASS 2
- result: OK
- tr_schema_valid: OK
- bi_schema_valid: OK
- capital_continuity: OK
- phase0_title_sync: OK
- block_count_70: OK

## PASS 3
- result: OK
- roadmap_title_sync: OK
- roadmap_hash_equal: OK
- protagonist_sync: OK
- portfolio_sync_with_tr: OK
- first_last_block_sync: OK

## Notes
- summary: consistency 3-pass = PASS, production density = PASS.
