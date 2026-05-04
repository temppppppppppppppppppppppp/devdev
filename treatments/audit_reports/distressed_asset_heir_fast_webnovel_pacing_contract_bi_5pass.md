# BI 5-Pass 감리 보고서 (2026-05-03)

## 대상
- phase0: `treatments/phase0/distressed_asset_heir_phase0_design.json`
- draft: `treatments/distressed_asset_heir_tr_block_070_draft.json`
- bi: `bible/0_bi_distressed_asset_heir.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 도련님은 부실자산을 산다
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['도련님은 부실자산을 산다']
- bi_meta_title: 도련님은 부실자산을 산다
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: []

## Source TR Metrics
- production_density_gate: PASS
- avg_bundle_chars: 563.89
- avg_solution_chars: 143.97
- foreshadow_total: 140
- callback_total: 146
- callback_ratio: 1.04
- unresolved_foreshadow_count: 0
- diegetic_meta_ref_count: 0
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 0
- opponent_unique: 47
- top_opponent_repetition: 8
- top_opponent_share: 11.4%
- top_weakness_repetition: 1
- deal_top_repetition: 1
- method_top_repetition: 1
- solution_tail20_top_repetition: 1
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
- window_10_opponent_unique_counts: [7, 7, 8, 8, 10, 10, 5]

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
- MetaInfo.title: 도련님은 부실자산을 산다
- MetaInfo.grand_objective: 현금 많은 식품·물류 그룹의 외동 한도윤은 도련님으로 무시받지만, 실제로는 부실자산을 권리와 현금흐름으로 쪼개 읽는 전직 PEF 구조조정 애널리스트다. 그는 문서를 만지면 숨은 현금흐름과 회수 가능한 권리, 90일 생존 가능성을 본다. 첫 전장은 망한 국밥 프랜차이즈다. 그는 점포를 사지 않고 정산권, 물류권, 상표 사용권, 임대차 우선협상권만 싸게 사서 첫 cashflow proof를 만든다.
- MetaInfo.genre_archetype: 현대 한국 business-power 현대판타지 부실자산 경영물
- MetaInfo.logline: 도윤은 가족이 버리려던 국밥 프랜차이즈 장부에서 죽은 점포가 아니라 살아 있는 정산권과 물류권을 본다. 그는 가게를 사지 않는다. 돈이 들어오는 순서만 산다.
- CoreIdentity.protagonist: 한도윤
- CoreIdentity.protagonist_faction: 한성푸드로지스 -> 한성푸드로지스
- CoreIdentity.edge: 부실자산을 점포나 회사가 아니라 권리 묶음, 책임 순서, 현금흐름 병목으로 쪼개 본다.
- CoreIdentity.desire: 국밥 프랜차이즈를 통째로 떠안지 않고 살아 있는 권리 묶음만 싸게 사서 첫 공식 proof를 만든다.
- CoreIdentity.crisis: 도윤은 가족이 버리려던 국밥 프랜차이즈 장부에서 죽은 점포가 아니라 살아 있는 정산권과 물류권을 본다. 그는 가게를 사지 않는다. 돈이 들어오는 순서만 산다.
- FinanceHUD.actual_truth.name: 한도윤
- FinanceHUD.actual_truth.rank: 한성푸드로지스 외동. 공식 경영권은 없고, 가족에게는 엑셀 배운 도련님으로 취급된다. / 한성푸드로지스
- FinanceHUD.actual_truth.current_objective: 국밥 프랜차이즈를 통째로 떠안지 않고 살아 있는 권리 묶음만 싸게 사서 첫 공식 proof를 만든다.
- FinanceHUD.actual_truth.final_goal: 가족 돈의 장식품이 아니라 독립 distressed-asset manager로 인정받고, 한성그룹의 버리는 자산을 돈으로 바꾸는 기준이 된다.
- WorldState.CurrentEra: 2026년 봄
- WorldState.CurrentLocation: 한성푸드로지스 본가 식사실
- KeyNPCs[0].name: 한도윤
- KeyNPCs[1].name: 윤세라
- plot_roadmap[0].title: 버릴 거면 제가 보죠
- plot_roadmap[34].title: 상가를 사지 않는 리츠
- plot_roadmap[69].title: 마지막 도장은 감정이 아니다

## 메모
- pattern_feedback_snapshot.top_opponents: [('백승환', 8), ('백승환과 한성 내부 감사팀', 7), ('백승환 NPL 투자자', 4)]
- pattern_feedback_snapshot.top_weaknesses: [('점포 손익만 보고 권리 묶음을 따로 보지 않은 상태', 1), ('점포 책임을 통째로 떠넘기려 했지만 권리와 책임이 계약상 분리 가능한 점', 1), ('정산 지연이라고 주장했지만 입금 계좌와 예정표가 맞지 않은 점', 1)]
- summary: 5개 PASS 모두 통과
