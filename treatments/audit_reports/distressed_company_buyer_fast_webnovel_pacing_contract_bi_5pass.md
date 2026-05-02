# BI 5-Pass 감리 보고서 (2026-05-02)

## 대상
- phase0: `treatments/phase0/distressed_company_buyer_phase0_design.json`
- draft: `treatments/distressed_company_buyer_tr_block_070_draft.json`
- bi: `bible/0_bi_distressed_company_buyer.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 부도난 회사만 사들입니다
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['부도난 회사만 사들입니다']
- bi_meta_title: 부도난 회사만 사들입니다
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: []

## Source TR Metrics
- production_density_gate: PASS
- avg_bundle_chars: 1239.84
- avg_solution_chars: 342.51
- foreshadow_total: 279
- callback_total: 256
- callback_ratio: 0.92
- unresolved_foreshadow_count: 0
- diegetic_meta_ref_count: 0
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 0
- opponent_unique: 64
- top_opponent_repetition: 3
- top_opponent_share: 4.3%
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
- recognition_signal_blocks: 28
- max_recognition_gap_streak: 5
- late_blank_opponent_blocks: []
- endgame_low_stakes_blocks: []
- normalized_solution_stakes_repeat_max: 1
- hard_gate_failures: []
- window_10_opponent_unique_counts: [8, 10, 8, 9, 10, 10, 9]

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
- MetaInfo.title: 부도난 회사만 사들입니다
- MetaInfo.grand_objective: 회귀한 구조조정 실사관 한도윤은 모두가 청산가치만 보는 부도 회사에서 아직 살아 있는 인증, 보험금, 납품권, 운송 노선, 숙련 인력 기억을 헐값에 사들여 회생 포트폴리오 제국을 만든다.
- MetaInfo.genre_archetype: 현대 한국 business-power 현대판타지 구조조정 M&A 돈벌이물
- MetaInfo.logline: 도윤은 부도 회사를 통째로 살리지 않는다. 고철처럼 버려진 회사 안에서 돈이 들어오는 권리의 순서만 산다.
- CoreIdentity.protagonist: 한도윤
- CoreIdentity.protagonist_faction: 삼진콜드 -> 삼진콜드
- CoreIdentity.edge: 부도 회사를 회사가 아니라 인증, 보험금, 노선권, 임대차, 설비 리스, 현장 기억의 권리 묶음으로 쪼개 읽는다.
- CoreIdentity.desire: 삼진콜드가 고철 매각으로 넘어가기 전에 회의석, 데이터룸 접근권, 독점 실사권, 우선협상권을 확보한다.
- CoreIdentity.crisis: 도윤은 부도 회사를 통째로 살리지 않는다. 고철처럼 버려진 회사 안에서 돈이 들어오는 권리의 순서만 산다.
- FinanceHUD.actual_truth.name: 한도윤
- FinanceHUD.actual_truth.rank: 대형 회계법인 구조조정본부 계약직 실사관. 부도 기업 현장을 뒤지고 보고서 초안을 쓰지만, 파트너 이름으로만 실적이 남는다. / 삼진콜드
- FinanceHUD.actual_truth.current_objective: 삼진콜드가 고철 매각으로 넘어가기 전에 회의석, 데이터룸 접근권, 독점 실사권, 우선협상권을 확보한다.
- FinanceHUD.actual_truth.final_goal: 채권단과 은행이 먼저 매물을 들고 오는 독립 구조조정 운용사 대표가 된다.
- WorldState.CurrentEra: 2026년 봄, 삼진콜드 청산 회의 당일
- WorldState.CurrentLocation: 삼진콜드 본사 창고 / 냉동차 차고 / 회의실 문밖
- KeyNPCs[0].name: 한도윤
- KeyNPCs[1].name: 윤태식
- KeyNPCs[2].name: 서민재
- plot_roadmap[0].title: 고철 사진이나 찍어 와
- plot_roadmap[34].title: 파손 사유는 가격표다
- plot_roadmap[69].title: 초대장이 먼저 왔다

## 메모
- pattern_feedback_snapshot.top_opponents: [('백승환 / 윤태식 / 고철업자', 3), ('동원푸드넷 채권관리팀 / 명성급식 / 해문푸드서비스 대표', 2), ('채권은행 신용심사팀 / 명성급식 / 해문푸드서비스 대표', 2)]
- pattern_feedback_snapshot.top_weaknesses: [('고철값과 담보 회수만 보면 인증, 보험금, 노선권 같은 살아 있는 권리를 놓친다', 1), ('처리 속도와 담보 회수만 보다가 보험금, 인증, 납품권 포기 책임을 회의록에 남기는 것을 두려워한다', 1), ('종결 속도를 우선하다가 면책 사유와 특약 trigger의 기준 시점을 느슨하게 처리했다', 1)]
- summary: 5개 PASS 모두 통과
