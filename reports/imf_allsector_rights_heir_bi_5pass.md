# BI 5-Pass 감리 보고서 (2026-05-01)

## 대상
- phase0: `treatments/phase0/imf_allsector_rights_heir_phase0_design.json`
- draft: `treatments/imf_allsector_rights_heir_tr_block_070_draft.json`
- bi: `bible/0_bi_imf_allsector_rights_heir.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 재벌가 후계자는 버려진 권리를 산다
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['재벌가 후계자는 버려진 권리를 산다']
- bi_meta_title: 재벌가 후계자는 버려진 권리를 산다
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: []

## Source TR Metrics
- production_density_gate: PASS
- avg_bundle_chars: 494.89
- avg_solution_chars: 143.54
- foreshadow_total: 130
- callback_total: 92
- callback_ratio: 0.71
- unresolved_foreshadow_count: 0
- diegetic_meta_ref_count: 0
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 0
- opponent_unique: 62
- top_opponent_repetition: 5
- top_opponent_share: 7.1%
- top_weakness_repetition: 1
- deal_top_repetition: 1
- method_top_repetition: 1
- solution_tail20_top_repetition: 26
- one_sentence_like_solution_blocks: 0
- business_sector_missing: 0
- section_rotation_missing: 0
- critical_thin_blocks: []
- thin_blocks: []
- short_stakes_blocks: []
- same_location_clone_count: 0
- npc_continuity_mismatch_count: 0
- recognition_signal_blocks: 14
- max_recognition_gap_streak: 9
- late_blank_opponent_blocks: []
- endgame_low_stakes_blocks: []
- normalized_solution_stakes_repeat_max: 1
- hard_gate_failures: []
- window_10_opponent_unique_counts: [6, 10, 8, 9, 10, 10, 9]

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
- MetaInfo.title: 재벌가 후계자는 버려진 권리를 산다
- MetaInfo.grand_objective: 2026년 세강그룹 해체 잔여자산을 정리하던 강태준은, 그룹이 IMF 때 팔아치운 자산 대부분이 단순 자산이 아니라 미래 권리였다는 사실을 끝까지 본다. 1997년 11월로 돌아온 그는 선의나 복수보다 이득과 효율을 기준으로 냉장물류, 회선/PC방, PCS, NPL, 부품소재, 도심 인프라, IP의 버려진 권리를 매각 보류권과 실사권, 우선매수권으로 회수한다.
- MetaInfo.genre_archetype: 현대 한국 no-fantasy 재벌 회귀 business-growth 권리 회수물
- MetaInfo.logline: IMF 직전 비상자산 매각 회의에서 강태준은 남서 냉장창고 매각안을 멈추는 동시에 해지될 PC방/초고속 회선 계약을 포착한다. 그는 창고를 사는 것이 아니라 창고와 회선에 붙은 권리를 사기 위해 30일 권리 실사권부터 빼앗는다.
- CoreIdentity.protagonist: 강태준
- CoreIdentity.protagonist_faction: 세강그룹 회장실 / 비상자산 매각 회의 -> 세강그룹 회장실 / 비상자산 매각 회의
- CoreIdentity.edge: 남들이 쓰레기로 보는 자산에서 남은 권리와 미래 협상권을 읽고, 현재 문서로 proof를 만든 뒤 권한으로 환전한다.
- CoreIdentity.desire: 남서 냉장창고 매각과 회선 계약 해지를 동시에 멈추고 30일 권리 실사권을 얻는다.
- CoreIdentity.crisis: IMF 직전 비상자산 매각 회의에서 강태준은 남서 냉장창고 매각안을 멈추는 동시에 해지될 PC방/초고속 회선 계약을 포착한다. 그는 창고를 사는 것이 아니라 창고와 회선에 붙은 권리를 사기 위해 30일 권리 실사권부터 빼앗는다.
- FinanceHUD.actual_truth.name: 강태준
- FinanceHUD.actual_truth.rank: 세강그룹 창업주 강문식의 손자. 회귀 전에는 그룹 해체 뒤 남은 부실자산 정리 실무를 맡았다. / 세강그룹 회장실 / 비상자산 매각 회의
- FinanceHUD.actual_truth.current_objective: 남서 냉장창고 매각과 회선 계약 해지를 동시에 멈추고 30일 권리 실사권을 얻는다.
- FinanceHUD.actual_truth.final_goal: 세강그룹의 IMF 매각 목록을 태준의 권리 holding structure로 뒤집고, 사장단이 그를 거치지 않고는 자산을 팔 수 없게 만든다.
- WorldState.CurrentEra: 1997년 11월 말
- WorldState.CurrentLocation: 세강그룹 본사 비상자산 매각 회의실
- KeyNPCs[0].name: 강태준
- KeyNPCs[1].name: 강문식
- KeyNPCs[2].name: 최도겸
- plot_roadmap[0].title: 매각 목록 위의 빨간 줄
- plot_roadmap[34].title: 현금 부족
- plot_roadmap[69].title: 버려진 권리의 주인

## 메모
- pattern_feedback_snapshot.top_opponents: [('최도겸 CFO', 5), ('단말 유통사 / 최도겸 CFO', 2), ('동진은행 구조조정팀 / 최도겸 CFO', 2)]
- pattern_feedback_snapshot.top_weaknesses: [('현금화 일정만 보고 권리 잔존 가치를 분리하지 못한 상태', 1), ('각 안건을 분리해 보면 비용이지만 같은 날짜의 권리 소멸로 보면 리스크가 된다는 점', 1), ('현금 수익이 없으면 가치가 낮다고 보는 평가 기준', 1)]
- summary: 5개 PASS 모두 통과

