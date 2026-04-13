# BI 5-Pass 감리 보고서 (2026-04-12)

## 대상
- phase0: `treatments/phase0/smart_new_hire_phase0_design.json`
- draft: `treatments/smart_new_hire_tr_block_070_draft.json`
- bi: `bible/0_bi_smart_new_hire.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 신입사원이 일을 잘함
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['신입사원이 일을 잘함']
- bi_meta_title: 신입사원이 일을 잘함
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: []

## Source TR Metrics
- production_density_gate: PASS
- avg_bundle_chars: 1381.13
- avg_solution_chars: 458.44
- foreshadow_total: 271
- callback_total: 299
- callback_ratio: 1.1
- unresolved_foreshadow_count: 0
- diegetic_meta_ref_count: 0
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 0
- opponent_unique: 69
- top_opponent_repetition: 1
- top_opponent_share: 1.4%
- top_weakness_repetition: 1
- deal_top_repetition: 1
- method_top_repetition: 1
- solution_tail20_top_repetition: 10
- one_sentence_like_solution_blocks: 10
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
- window_10_opponent_unique_counts: [10, 10, 10, 9, 10, 10, 10]

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
- MetaInfo.title: 신입사원이 일을 잘함
- MetaInfo.grand_objective: 세광리테일 채널운영팀 신입 윤도혁이 일을 맡는 순간만 뜨는 업무 비서형 안내문으로 파일, 숫자, 결재선, 회의 흐름에서 지금 가장 먼저 건드려야 할 한 점을 읽고, 실명 메일, 브리핑 owner, 원장 접근권, line freeze, 임시 PM, 공동권한, 독자 라인, 혁신 PMO를 차례로 회수해 회사가 먼저 찾는 사람이 되는 조직권력 성장물.
- MetaInfo.genre_archetype: 현대 한국 대기업 유통 계열 조직권력 성장물
- MetaInfo.logline: 회의실 사탕을 채우러 들어간 신입이 숨김 열을 먼저 본다. 도혁은 정답을 말하는 대신 책임자를 세워, 회사가 먼저 찾는 사람이 된다.
- CoreIdentity.protagonist: 윤도혁
- CoreIdentity.protagonist_faction: 세광리테일 영업관리본부 채널운영팀 -> 세광리테일 영업관리본부 채널운영팀
- CoreIdentity.edge: 표면 실적이 아니라 왜 저 숫자가 저렇게 보이는지를 먼저 읽고, 그걸 owner 표와 문서 흔적으로 현실에 붙인다.
- CoreIdentity.desire: 안 잘리고 자리 잡기. opening 2~6 안에서 실명 노출, 브리핑 owner, 원장 접근권, line freeze, 거래처 검토권, 소액 예산, 임원 리뷰 배석권을 회수한다.
- CoreIdentity.crisis: 회의실 사탕을 채우러 들어간 신입이 숨김 열을 먼저 본다. 도혁은 정답을 말하는 대신 책임자를 세워, 회사가 먼저 찾는 사람이 된다.
- FinanceHUD.actual_truth.name: 윤도혁
- FinanceHUD.actual_truth.rank: 세광리테일 영업관리본부 채널운영팀 신입사원 / 세광리테일 영업관리본부 채널운영팀
- FinanceHUD.actual_truth.current_objective: 안 잘리고 자리 잡기. opening 2~6 안에서 실명 노출, 브리핑 owner, 원장 접근권, line freeze, 거래처 검토권, 소액 예산, 임원 리뷰 배석권을 회수한다.
- FinanceHUD.actual_truth.final_goal: 회사가 급한 문제를 만나면 먼저 도혁 방식의 체크리스트와 기준표를 찾게 만드는 것.
- WorldState.CurrentEra: 2026년 3월 첫째 주 월요일 아침
- WorldState.CurrentLocation: 세광리테일 본사 11층 채널운영팀 회의실 / 팀 자리
- KeyNPCs[0].name: 윤도혁
- KeyNPCs[1].name: 윤도혁
- KeyNPCs[2].name: 한성우
- plot_roadmap[0].title: 사탕 하나
- plot_roadmap[34].title: 실행 책임표
- plot_roadmap[69].title: 회사가 먼저 찾는 사람

## 메모
- draft_warnings: ['블록 25: content.reward 필드 누락']
- draft_canonical_warnings: ['블록 25: content.reward 필드 누락']
- normalized_draft_canonical_warnings: ['블록 25: content.reward 필드 누락']
- pattern_feedback_snapshot.top_opponents: [('아침 브리핑 관성', 1), ('속보 우선 보고 루프', 1), ('예외코드 책임 공백', 1)]
- pattern_feedback_snapshot.top_weaknesses: [('원본 확인 담당이 비어 있다는 구조', 1), ('요약본만 믿고 원본 검산이 비어 있는 점', 1), ('누구 책임인지 쓰인 칸이 없다는 점', 1)]
- summary: 5개 PASS 모두 통과

