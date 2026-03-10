# Updated Blockguide Re-Audit (2026-03-10)

## Scope
- source docs: `docs/blockguide/blockguide-integrated-order.md`
- source docs: `docs/blockguide/treatment-production-harness-v2.md`
- source docs: `docs/blockguide/bi-production-harness-v1.md`
- target draft: `treatments/us_ai_exile_monopoly_tr_block_070_draft.json`
- target bi: `bible/0_bi_us_ai_exile_monopoly.json`

## Updated Checks
- p0_utf8_only: OK
- p0_capital_continuity: OK
- p1_beat_type_no_adjacent_duplicate: OK
- p1_beat_type_unique_6plus: OK
- p1_intensity_full_1_10: OK
- p1_intensity_no_same3: OK
- p1_success_pattern_4plus: OK
- p1_success_pattern_no_same3: OK
- p1_callback_specific: OK
- p1_deal_type_no_within3: OK
- p1_leverage_set_top_lt3: OK
- p1_template_jaccard_under_30pct: OK
- p2_risk_level_full_range: OK
- p2_global_partner_3plus: OK
- p2_location_no_within15: OK

## Key Metrics
- beat_unique_count: 20
- intensity_unique: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
- success_pattern_unique: ['부분 성공', '승리', '실패', '재정비', '진전', '최종 승리', '피로스 승리']
- risk_levels: ['고위험', '극고위험', '저위험', '중위험']
- global_partner_unique: 7
- leverage_set_top_repetition: 2
- jaccard_high_pair_ratio: 0.2944
- avg_chars: 815.9

## Result
- summary: PASS
