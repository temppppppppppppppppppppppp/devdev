# BI 5-Pass 감리 보고서 (2026-05-02)

## 대상
- phase0: `treatments/phase0/pharma_cdmo_industry_heir_phase0_design.json`
- draft: `treatments/pharma_cdmo_industry_heir_tr_block_070_draft.json`
- bi: `bible/0_bi_pharma_cdmo_industry_heir.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 회귀자는 버려진 제약공장을 샀다
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['회귀자는 버려진 제약공장을 샀다']
- bi_meta_title: 회귀자는 버려진 제약공장을 샀다
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: []

## Source TR Metrics
- production_density_gate: PASS
- avg_bundle_chars: 977.01
- avg_solution_chars: 281.91
- foreshadow_total: 210
- callback_total: 210
- callback_ratio: 1.0
- unresolved_foreshadow_count: 16
- diegetic_meta_ref_count: 0
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 0
- opponent_unique: 57
- top_opponent_repetition: 9
- top_opponent_share: 12.9%
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
- recognition_signal_blocks: 22
- max_recognition_gap_streak: 5
- late_blank_opponent_blocks: []
- endgame_low_stakes_blocks: []
- normalized_solution_stakes_repeat_max: 1
- hard_gate_failures: []
- window_10_opponent_unique_counts: [2, 9, 10, 9, 10, 9, 9]

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
- MetaInfo.title: 회귀자는 버려진 제약공장을 샀다
- MetaInfo.grand_objective: 태오바이오를 신약 천재 회사가 아니라 GMP, CDMO, 병원 데이터, 원료소재, 소비재 안전표준, 공급망 금융을 통과시키는 국가 산업 표준 운영자로 만든다.
- MetaInfo.genre_archetype: 현대판타지 + 회귀 + 제약 CDMO + 산업재벌
- MetaInfo.logline: 한 번 죽어 본 제약 공급망 실무자 강태오는 1997년으로 돌아와 버려진 공장을 산다. 그는 신약을 발명하지 않는다. 대신 남들이 외면한 품질문서, 감사권, 납품권, 온도기록, 청구 데이터를 모아 대한민국 산업의 보이지 않는 표준이 된다.
- CoreIdentity.protagonist: 강태오
- CoreIdentity.protagonist_faction: 태오바이오
- CoreIdentity.edge: 미래 공급망 사고의 기억을 신약 정답지가 아니라 품질문서, 감사 대응권, 생산권, 데이터권, 금융 조건표의 우선순위로 바꾸는 능력.
- CoreIdentity.desire: 다시는 남의 불량 배치와 공급망 사고를 대신 뒤집어쓰지 않는다. 모든 산업이 자기 품질표와 조건표를 지나가게 만든다.
- CoreIdentity.crisis: 선의나 신약 재능으로만 움직이면 공장, 병원, 글로벌 제약사, 국가 표준의 운영권을 모두 남에게 빼앗긴다.
- FinanceHUD.actual_truth.name: 강태오
- FinanceHUD.actual_truth.rank: 국가 산업 표준 운영자
- FinanceHUD.actual_truth.current_objective: 태오바이오 표준 운영 사무국을 출범시키고 다산업 인증 gate의 첫 적용을 안정화한다.
- FinanceHUD.actual_truth.final_goal: 모든 산업이 태오바이오의 품질문서, 감사 log, 인증 gate, 금융 조건표를 통과하게 만든다.
- WorldState.CurrentEra: 1997~2012 IMF 이후 제약·바이오 산업 재편기
- WorldState.CurrentLocation: 부평 2공장에서 병원, 글로벌 CDMO 회의장, 원료소재 라인, 국가 산업 표준 회의장으로 확장되는 한국 산업 현장
- KeyNPCs[0].name: 강태오
- KeyNPCs[1].name: 윤세린
- KeyNPCs[2].name: 한재국
- plot_roadmap[0].title: 부도 공장 경매장
- plot_roadmap[34].title: 필터가 없으면 약도 없다
- plot_roadmap[69].title: 생산 표준의 주인

## 메모
- pattern_feedback_snapshot.top_opponents: [('한재국', 9), ('사립병원 구매이사와 기존 병원 납품사', 2), ('냉장물류 조합과 한재국', 2)]
- pattern_feedback_snapshot.top_weaknesses: [('공장 소유권만 털어내면 과거 품질 책임도 같이 사라진다고 믿는다', 1), ('문서를 숨기면 책임도 사라진다고 믿고 원본과 사본의 이동을 가볍게 본다', 1), ('익명 제보가 결함 은폐를 전제로 먹힌다고 믿고 자진 격리 기록의 방어력을 계산하지 못한다', 1)]
- summary: 5개 PASS 모두 통과
