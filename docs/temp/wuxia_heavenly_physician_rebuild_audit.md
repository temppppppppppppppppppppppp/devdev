# Wuxia BI 5-Pass Audit (2026-03-26)

## Inputs
- phase0: `treatments/_quarantine/wuxia_heavenly_physician_phase0_design.json`
- draft: `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json`
- bi: `docs/temp/wuxia_heavenly_physician_rebuild.json`

## PASS 1: encoding and parse
- result: OK
- utf8_json_parse: OK
- garbled_token_zero: OK
- draft_schema_valid: OK

## PASS 2: minimum schema
- result: OK
- validate_bible_structure: OK
- meta_title_present: OK
- plot_roadmap_len_70: OK
- martial_hud_present: OK

## PASS 3: source TR handoff gate
- result: FAIL
- source_tr_density_gate: FAIL
- source_tr_critical_thin_gate: OK
- source_tr_thin_ratio_gate: OK
- source_tr_late_thin_gate: OK
- source_tr_short_stakes_gate: OK
- source_tr_endgame_stakes_gate: OK
- source_tr_callback_gate: OK
- source_tr_unresolved_foreshadow_gate: OK
- source_tr_faction_position_gate: OK
- source_tr_reputation_gate: OK
- source_tr_enemy_pressure_gate: FAIL
- source_tr_late_opponent_gate: OK
- source_tr_solution_stakes_repeat_gate: OK
- source_tr_martial_progress_gate: OK
- source_tr_opponent_diversity_gate: OK
- source_tr_weakness_repeat_gate: FAIL
- source_tr_solution_gate: OK
- protagonist_match: OK
- title_match_phase0: OK
- protagonist_faction_match: OK
- martial_realm_sync_with_tr: OK
- martial_internal_energy_sync_with_tr: OK
- martial_reputation_sync_with_tr: OK
- martial_enemy_pressure_sync_with_tr: OK

## PASS 4: TR linkage
- result: OK
- roadmap_title_sequence: OK
- roadmap_hash_equal: OK
- first_last_title_match: OK
- plot_roadmap_len_matches_draft: OK

## PASS 5: MartialHUD and consistency
- result: OK
- martial_truth_complete: OK
- faction_map_ready: OK
- treasures_ready: OK
- seeds_ready: OK
- npc_name_consistent: OK
- world_state_present: OK
- asset_library_present: OK

## Martial Truth
- name: 진소백(陳小白)
- alias: 진소백(陳小白)
- realm: 천의 (100%, 무량)
- internal_energy: 무량
- mental_method: 기본 심법
- wealth: 빈약
- causal_injuries: 초반 내공 부족으로 침술 시 체력 소모 극심. 감정이 흔들리면 침끝이 떨림. 사랑하는 자를 치료할 때의 불안정.
- current_objective: 가문에서 인정받고 싶다. 형의 끊어진 경맥을 잇고 싶다.
- equipment: {'weapons': [], 'artifacts': []}

## Notes
- key_npcs_seen: ['진소백(陳小白)', '진무강(큰형)', '진소풍(넷째 형)', '백무명(숨은 스승)', '매화(연인)']
- treasures_count: 0
- seeds_count: 1
- source_tr_hard_gate_failures: ['enemy_pressure_present']
- source_tr_callback_ratio: 1.55
- source_tr_martial_progress_blocks: 64/70
- expected_realm_from_tr: 천의 (100%, 무량)
- expected_internal_energy_from_tr: None
- expected_reputation_from_tr: 천의 진소백. 천하를 유람하며 치료하는 전설의 의원
- expected_enemy_pressure_from_tr:
