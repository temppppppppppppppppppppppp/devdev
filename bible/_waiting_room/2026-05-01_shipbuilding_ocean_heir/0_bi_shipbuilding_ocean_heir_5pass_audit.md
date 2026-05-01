# BI 5-Pass 감리 보고서 (2026-05-01)

## 대상
- phase0: `treatments/phase0/shipbuilding_ocean_heir_phase0_design.json`
- draft: `treatments/shipbuilding_ocean_heir_tr_block_070_draft.json`
- bi: `bible/_waiting_room/2026-05-01_shipbuilding_ocean_heir/0_bi_shipbuilding_ocean_heir.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 망한 조선재벌의 후계자가 돌아왔다
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['망한 조선재벌의 후계자가 돌아왔다']
- bi_meta_title: 망한 조선재벌의 후계자가 돌아왔다
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: []

## Source TR Metrics
- production_density_gate: PASS
- avg_bundle_chars: 804.2
- avg_solution_chars: 227.51
- foreshadow_total: 131
- callback_total: 132
- callback_ratio: 1.01
- unresolved_foreshadow_count: 0
- diegetic_meta_ref_count: 0
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 0
- opponent_unique: 65
- top_opponent_repetition: 2
- top_opponent_share: 2.9%
- top_weakness_repetition: 1
- deal_top_repetition: 1
- method_top_repetition: 1
- solution_tail20_top_repetition: 1
- one_sentence_like_solution_blocks: 0
- business_sector_missing: 0
- section_rotation_missing: 0
- critical_thin_blocks: []
- thin_blocks: []
- short_stakes_blocks: []
- same_location_clone_count: 0
- npc_continuity_mismatch_count: 0
- recognition_signal_blocks: 17
- max_recognition_gap_streak: 11
- late_blank_opponent_blocks: []
- endgame_low_stakes_blocks: []
- normalized_solution_stakes_repeat_max: 1
- hard_gate_failures: []
- window_10_opponent_unique_counts: [9, 10, 10, 8, 10, 9, 10]

## Meta Leak Check
- bi_diegetic_meta_leak_count: 0
- bi_label_meta_leak_count: 0

## Canonical Contract
- raw_bi_canonical_contract: PASS
- raw_tr_canonical_contract: PASS
- raw_pair_canonical_contract: PASS
- normalized_bi_canonical_view: PASS
- normalized_tr_canonical_view: PASS
- normalized_pair_canonical_view: PASS

## PASS 1: 인코딩/파싱
- result: OK
- utf8_json_parse: OK
- garbled_token_zero: OK
- diegetic_meta_text_zero: OK
- label_meta_text_zero: OK
- draft_schema_valid: OK

## PASS 2: 최소 스키마
- result: OK
- validate_bible_structure: OK
- meta_title_present: OK
- plot_roadmap_len_70: OK

## PASS 3: source TR handoff gate
- result: OK
- source_tr_density_gate: OK
- source_tr_critical_thin_gate: OK
- source_tr_thin_ratio_gate: OK
- source_tr_late_thin_gate: OK
- source_tr_short_stakes_gate: OK
- source_tr_endgame_stakes_gate: OK
- source_tr_callback_gate: OK
- source_tr_unresolved_foreshadow_gate: OK
- source_tr_section_rotation_gate: OK
- source_tr_late_opponent_gate: OK
- source_tr_solution_stakes_repeat_gate: OK
- source_tr_same_location_clone_gate: OK
- source_tr_meta_gate: OK
- source_tr_label_meta_gate: OK
- source_tr_block_meta_gate: OK
- source_tr_npc_continuity_gate: OK
- source_tr_opponent_diversity_gate: OK
- source_tr_weakness_repeat_gate: OK
- source_tr_solution_gate: OK
- protagonist_match: OK
- title_match_phase0: OK
- title_within_phase0_surface: OK
- starter_company_match: OK
- portfolio_monotonic: OK
- portfolio_sync_with_tr: OK
- source_tr_regressor_recognition_count_gate: OK
- source_tr_regressor_recognition_gap_gate: OK
- source_tr_opening_reader_earning_gate: OK
- source_tr_opening_macro_progression_gate: OK

## PASS 4: TR↔BI 동기화
- result: OK
- roadmap_title_sequence: OK
- roadmap_first_last: OK
- roadmap_hash_equal: OK

## PASS 5: 품질 감리
- result: OK
- sample_fields_clean: OK
- foreign_token_zero: OK
- company_name_consistent: OK
- npc_name_consistent: OK

## 샘플링
- MetaInfo.title: 망한 조선재벌의 후계자가 돌아왔다
- MetaInfo.grand_objective: 2003년 조선/해운 초호황기에 회귀한 태성오션그룹 전략실 막내 강서준이, 모두가 박수치는 수주 계약을 현재 자료로 해체하고 조건을 바꿀 권한을 얻어 그룹의 유동성 붕괴를 막는다.
- MetaInfo.genre_archetype: 현대 한국 no-fantasy 회귀 재벌 산업 경영물
- MetaInfo.logline: 망한 조선재벌의 해체 실무를 겪고 2003년으로 돌아온 강서준은 수주잔고가 아니라 살아남는 계약만 남기기 위해 선박금융, 보증, 보험, 도크 슬롯, 공시, 인수옵션을 자기 리스크 표에 묶는다.
- CoreIdentity.protagonist: 강서준
- CoreIdentity.protagonist_faction: 태성오션그룹 -> 태성오션그룹
- CoreIdentity.edge: 전생의 그룹 해체 실무를 통해 어떤 수주와 보증이 그룹을 죽였는지 알고, 현재 계약서와 생산능력표로 그 위험을 증명한다.
- CoreIdentity.desire: 대형 벌크선 수주 계약의 위험 조항을 바꾸고 리스크 TF장 권한을 얻는다.
- CoreIdentity.crisis: 망한 조선재벌의 해체 실무를 겪고 2003년으로 돌아온 강서준은 수주잔고가 아니라 살아남는 계약만 남기기 위해 선박금융, 보증, 보험, 도크 슬롯, 공시, 인수옵션을 자기 리스크 표에 묶는다.
- FinanceHUD.actual_truth.name: 강서준
- FinanceHUD.actual_truth.rank: 태성오션그룹 전략실 막내이자 창업주 강태문의 조카. 공식 후계자도 임원도 아니다. / 태성오션그룹
- FinanceHUD.actual_truth.current_objective: 대형 벌크선 수주 계약의 위험 조항을 바꾸고 리스크 TF장 권한을 얻는다.
- FinanceHUD.actual_truth.final_goal: 태성오션그룹의 모든 수주, 보증, M&A가 자신의 리스크 표를 통과하지 않으면 움직이지 않는 구조를 만든다.
- WorldState.CurrentEra: 2003년 봄
- WorldState.CurrentLocation: 태성오션그룹 본관 사장단 회의실
- KeyNPCs[0].name: 강서준
- KeyNPCs[1].name: 강태문
- KeyNPCs[2].name: 민도경
- plot_roadmap[0].title: 해체 발표장의 계약명
- plot_roadmap[34].title: 싼 배가 제일 비싸다
- plot_roadmap[69].title: 덜 지은 배가 그룹을 살린다

## 메모
- pattern_feedback_snapshot.top_opponents: [('한재문', 2), ('리처드 백과 한재문', 2), ('박철웅과 해운 브로커', 2)]
- pattern_feedback_snapshot.top_weaknesses: [('원본 계약서 조항을 아직 회의에서 대조하지 않은 상태', 1), ('선가와 수주잔고만 보고 원가 변동 조항을 낮게 보는 점', 1), ('실제 capacity를 완곡하게 숨긴 점', 1)]
- summary: 5개 PASS 모두 통과

