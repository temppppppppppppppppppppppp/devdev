# BI 5-Pass 감리 보고서 (2026-05-03)

## 대상
- phase0: `treatments/phase0/laid_off_cashflow_rights_operator_phase0_design.json`
- draft: `treatments/laid_off_cashflow_rights_operator_tr_block_070_draft.json`
- bi: `bible/0_bi_laid_off_cashflow_rights_operator.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 해고 직전, 돈줄이 보였다
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['해고 직전, 돈줄이 보였다']
- bi_meta_title: 해고 직전, 돈줄이 보였다
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: []

## Source TR Metrics
- production_density_gate: PASS
- avg_bundle_chars: 1159.9
- avg_solution_chars: 259.04
- foreshadow_total: 308
- callback_total: 270
- callback_ratio: 0.88
- unresolved_foreshadow_count: 58
- diegetic_meta_ref_count: 0
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 0
- opponent_unique: 56
- top_opponent_repetition: 4
- top_opponent_share: 5.7%
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
- recognition_signal_blocks: 0
- max_recognition_gap_streak: 0
- late_blank_opponent_blocks: []
- endgame_low_stakes_blocks: []
- normalized_solution_stakes_repeat_max: 1
- hard_gate_failures: []
- window_10_opponent_unique_counts: [6, 9, 8, 6, 7, 10, 10]

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
- MetaInfo.title: 해고 직전, 돈줄이 보였다
- MetaInfo.grand_objective: 강도윤이 해고 예정 정산 담당자에서 출발해 반품권, 리퍼브권, 달러 정산권, 물류 병목권, 생산권을 사들이는 외부 권리 포트폴리오 운영자가 되는 것.
- MetaInfo.genre_archetype: 현대판타지 + 회사원 능력물 + 계약정산 돈벌이 + 권리 사냥
- MetaInfo.logline: 해고 직전의 정산 담당자가 버려진 계약서와 창고 재고에서 돈줄을 보고, 현금보다 먼저 접근권과 계약권을 사들여 판을 바꾼다.
- CoreIdentity.protagonist: 강도윤
- CoreIdentity.protagonist_faction: 다온리테일 정산관리팀 -> 도윤권리운영 SPV -> 권리 포트폴리오 운영자
- CoreIdentity.edge: ERP, 계약서, 창고 SKU, 정산일의 어긋남에서 버려진 권리를 읽고 서명과 접근권으로 바꾸는 능력.
- CoreIdentity.desire: 착한 해결사가 아니라 자기 생존권과 다음 권한을 먼저 확보하는 권리 운영자가 된다.
- CoreIdentity.crisis: 해고 통보와 계정 만료로 모든 접근권이 끊기기 직전, 회사가 버린 파일 속 권리 묶음을 먼저 잡아야 한다.
- FinanceHUD.actual_truth.name: 강도윤
- FinanceHUD.actual_truth.rank: 해고 예정자 -> 도윤권리운영 SPV 대표 -> 권리 포트폴리오 운영자
- FinanceHUD.actual_truth.current_objective: 착한 해결사가 아니라 자기 생존권과 다음 권한을 먼저 확보하는 권리 운영자가 된다.
- FinanceHUD.actual_truth.final_goal: 강도윤이 해고 예정 정산 담당자에서 출발해 반품권, 리퍼브권, 달러 정산권, 물류 병목권, 생산권을 사들이는 외부 권리 포트폴리오 운영자가 되는 것.
- WorldState.CurrentEra: 2026년~2028년 현대 한국 유통/제조/공급망 권리 시장
- WorldState.CurrentLocation: 다온리테일 정산관리팀, 반품창고, 제조사 품질/생산본부, 도윤권리운영 SPV
- KeyNPCs[0].name: 강도윤
- KeyNPCs[1].name: 윤서린
- KeyNPCs[2].name: 박만철
- plot_roadmap[0].title: 계정 만료 72시간
- plot_roadmap[34].title: 대체로 반격
- plot_roadmap[69].title: 권리 운영 헌장

## 메모
- pattern_feedback_snapshot.top_opponents: [('최문식', 4), ('제조사 구매본부', 3), ('조대식 / 그린로지스', 2)]
- pattern_feedback_snapshot.top_weaknesses: [('책임 회피, 폐기 손실 회피, SKU 실물과 ERP 라벨 불일치', 1), ('정보 유출 공격을 걸면 접근 권한을 문서화해야 한다는 감사 절차', 1), ('당장 덮고 싶은 현금 합의 욕구와 결재선 책임 회피', 1)]
- summary: 5개 PASS 모두 통과
