# BI 5-Pass 감리 보고서 (2026-05-03)

## 대상
- phase0: `treatments/phase0/venture_bubble_king_2000_phase0_design.json`
- draft: `treatments/venture_bubble_king_2000_tr_block_070_draft.json`
- bi: `bible/0_bi_venture_bubble_king_2000.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 2000년, 벤처버블의 왕이 되었다
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['2000년, 벤처버블의 왕이 되었다']
- bi_meta_title: 2000년, 벤처버블의 왕이 되었다
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: []

## Source TR Metrics
- production_density_gate: PASS
- avg_bundle_chars: 696.14
- avg_solution_chars: 186.64
- foreshadow_total: 207
- callback_total: 179
- callback_ratio: 0.86
- unresolved_foreshadow_count: 21
- diegetic_meta_ref_count: 0
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 0
- opponent_unique: 59
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
- recognition_signal_blocks: 16
- max_recognition_gap_streak: 13
- late_blank_opponent_blocks: []
- endgame_low_stakes_blocks: []
- normalized_solution_stakes_repeat_max: 1
- hard_gate_failures: []
- window_10_opponent_unique_counts: [10, 10, 6, 9, 9, 8, 7]

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
- MetaInfo.title: 2000년, 벤처버블의 왕이 되었다
- MetaInfo.grand_objective: 2026년 플랫폼 그룹 해체 작업을 끝낸 서도윤은, 2000년 1월 태성텔레콤 방계 벤처 심사역으로 돌아온다. 모두가 닷컴 지분과 상장 프리미엄을 외칠 때, 도윤은 곧 터질 버블 속에서 서버 임대권, 도메인, 결제 모듈, PC방 회선, 모바일 과금, 검색 트래픽, 광고 재고처럼 살아남는 권리만 회수한다.
- MetaInfo.genre_archetype: 현대 한국 no-fantasy 회귀 테크/플랫폼 권리 독식물
- MetaInfo.logline: 상장 직전 닷컴 IR에서 서도윤은 지분투자를 거절하고 IDC 임대권, PG 테스트 계약, 도메인 예치를 담보로 요구한다. 버블이 꺼질수록 망한 회사들은 도윤에게 현금 대신 권리를 내놓고, 그는 대한민국 인터넷 생태계의 관문을 하나씩 잠근다.
- CoreIdentity.protagonist: 서도윤
- CoreIdentity.protagonist_faction: 태성텔레콤 벤처투자 태스크 -> 태성텔레콤 벤처투자 태스크
- CoreIdentity.edge: 미래 대박 회사를 맞히는 사람이 아니라, 망할 회사 안에서 서버권, 결제권, 회선권, 사용자 데이터처럼 살아남는 권리를 분리해 현재 문서로 고정하는 사람이다.
- CoreIdentity.desire: 클릭스퀘어 상장 전 IR에서 현금투자 대신 IDC 임대권, PG 테스트 계약, 도메인 예치, 72시간 독점 실사권을 얻는다.
- CoreIdentity.crisis: 상장 직전 닷컴 IR에서 서도윤은 지분투자를 거절하고 IDC 임대권, PG 테스트 계약, 도메인 예치를 담보로 요구한다. 버블이 꺼질수록 망한 회사들은 도윤에게 현금 대신 권리를 내놓고, 그는 대한민국 인터넷 생태계의 관문을 하나씩 잠근다.
- FinanceHUD.actual_truth.name: 서도윤
- FinanceHUD.actual_truth.rank: 태성텔레콤 창업주 한경수의 외손자. 계열 VC의 말석 심사역으로 밀려나 있다. / 태성텔레콤 벤처투자 태스크
- FinanceHUD.actual_truth.current_objective: 클릭스퀘어 상장 전 IR에서 현금투자 대신 IDC 임대권, PG 테스트 계약, 도메인 예치, 72시간 독점 실사권을 얻는다.
- FinanceHUD.actual_truth.final_goal: 태성텔레콤 본류도 도윤을 거치지 않고는 인터넷 서비스, 결제, 모바일 콘텐츠, 광고 재고를 움직일 수 없게 만든다.
- WorldState.CurrentEra: 2000년 1월
- WorldState.CurrentLocation: 태성텔레콤 계열 VC IR 회의장
- KeyNPCs[0].name: 서도윤
- KeyNPCs[1].name: 한경수
- KeyNPCs[2].name: 민지아
- plot_roadmap[0].title: 상장 전날의 서버실
- plot_roadmap[34].title: 포털 경쟁사의 배너
- plot_roadmap[69].title: 벤처버블의 왕

## 메모
- pattern_feedback_snapshot.top_opponents: [('임성필 / 윤기석', 4), ('임성필 / 윤기석 / 백승민', 2), ('링크허브 채권자단 / 넥스트서치 이재문', 2)]
- pattern_feedback_snapshot.top_weaknesses: [('지분평가와 상장 일정에만 집중해 서버/결제/도메인 권리를 낮게 본다.', 1), ('상장 전 평판을 지키려다 실제 연체 권리를 더 싼 조건으로 내준다.', 1), ('시장 조정으로 시간이 줄어들자 현금보다 담보권이 더 현실적인 보호장치가 된다.', 1)]
- summary: 5개 PASS 모두 통과
