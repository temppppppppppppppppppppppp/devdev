# Chaebol Ent Empire TR/BI 3PASS Audit (2026-03-10)

## Targets
- TR: `treatments/chaebol_ent_empire_tr_block_070_draft.json`
- BI: `bible/0_bi_chaebol_ent_empire.json`

## UTF-8 baseline
- result: OK
- python_utf8_parse_tr: OK
- python_utf8_parse_bi: OK
- powershell_utf8_parse_tr_bi: OK
- garbled_token_zero_tr: OK
- garbled_token_zero_bi: OK

## TR internal PASS 1
- result: OK
- validate_treatment_structure: OK
- block_count_70: OK
- block_id_sequence: OK

## TR internal PASS 2
- result: OK
- primary_pov_consistent: OK
- primary_pov_majority: OK
- first_last_pov_match: OK
- time_format_has_year_month: OK
- tension_level_range_1_10: OK

## TR internal PASS 3
- result: OK
- all_non_regressor: OK
- regression_type_all_null: OK
- execution_doctrine_present: OK

## BI internal PASS 1
- result: OK
- validate_bible_structure: OK
- masterbible_present: OK
- meta_title_present: OK

## BI internal PASS 2
- result: OK
- core_vs_hud_protagonist: OK
- core_vs_roadmap_primary_pov: OK
- bi_incarnation_non_regression: OK

## BI internal PASS 3
- result: OK
- plot_roadmap_len_70: OK
- roadmap_primary_pov_majority: OK
- roadmap_first_last_pov_match: OK

## TR-BI cross PASS 1
- result: OK
- protagonist_match: OK
- non_regression_match: OK
- roadmap_primary_pov_match: OK

## TR-BI cross PASS 2
- result: OK
- length_match: OK
- first_title_match: OK
- last_title_match: OK

## TR-BI cross PASS 3
- result: OK
- full_hash_equal: OK
- first_block_equal: OK
- last_block_equal: OK

## Notes
- protagonist: 권태하
- TR POV counts: {'권태하': 60, '윤서아': 6, '최라희': 4}
- BI roadmap POV counts: {'권태하': 60, '윤서아': 6, '최라희': 4}
- incarnation_type: 비회귀 / 비빙의
- roadmap_hash: 5a815de451941a07b88b43f734ae80181a73a8d000c63b03563962c3f63d8756
- tr_hash: 5a815de451941a07b88b43f734ae80181a73a8d000c63b03563962c3f63d8756
- first_title: 쓰레기통 상속
- last_title: 인정이 아니라 표준
- overall: PASS

