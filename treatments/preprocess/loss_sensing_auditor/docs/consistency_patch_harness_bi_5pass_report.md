# BI 5-Pass 감리 보고서 (2026-05-02)

## 대상
- phase0: `treatments/phase0/loss_sensing_auditor_phase0_design.json`
- draft: `treatments/loss_sensing_auditor_tr_block_070_draft.json`
- bi: `bible/0_bi_loss_sensing_auditor.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 손실이 보이는 감사팀 대리
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['손실이 보이는 감사팀 대리']
- bi_meta_title: 손실이 보이는 감사팀 대리
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: ['loss_sensing_auditor']

## Source TR Metrics
- production_density_gate: PASS
- avg_bundle_chars: 1218.44
- avg_solution_chars: 294.71
- foreshadow_total: 210
- callback_total: 219
- callback_ratio: 1.04
- unresolved_foreshadow_count: 0
- diegetic_meta_ref_count: 0
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 0
- opponent_unique: 53
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
- window_10_opponent_unique_counts: [7, 9, 9, 7, 6, 6, 9]

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
- MetaInfo.title: 손실이 보이는 감사팀 대리
- MetaInfo.grand_objective: 반도체 그룹 감사팀으로 좌천된 대리 서태준이 계약서와 숫자에서 미래 손실선과 책임 귀속을 먼저 읽고, 회사 위기를 막을 때마다 감사 보류권, CEO 직보선, 데이터룸 접근권, 공급망 veto 같은 권한으로 회수해 그룹 리스크 관문이 되는 이야기.
- MetaInfo.genre_archetype: 현대판타지 + 조직 권력 상승물 + 반도체 공급망/감사 전장
- MetaInfo.logline: 좌천된 감사팀 대리 서태준은 인수 계약서에서 수조 원 손실선을 본다. 그는 회사를 구하는 척 CFO의 계약을 멈추고, 그 대가로 CEO 직보선과 감사 보류권을 받아낸다.
- CoreIdentity.protagonist: 서태준
- CoreIdentity.protagonist_faction: 한서반도체 감사팀 -> 그룹 리스크전략실
- CoreIdentity.edge: 예상 손실, 책임 귀속, 막는 비용, 권한 회수 가능성을 함께 읽는다.
- CoreIdentity.desire: 다시는 남의 책임을 대신 떠안지 않고, 모든 큰 계약이 자기 조건표를 지나가게 만든다.
- CoreIdentity.crisis: 전략기획 라인에서 좌천되어 감사팀 도장 라인에 묶인 상태
- FinanceHUD.actual_truth.name: 서태준
- FinanceHUD.actual_truth.rank: 한서반도체 그룹 감사팀 대리 / 최종: 그룹 리스크전략실 실권자
- FinanceHUD.actual_truth.current_objective: 다시는 남의 책임을 대신 떠안지 않고, 모든 큰 계약이 자기 조건표를 지나가게 만든다.
- FinanceHUD.actual_truth.final_goal: 대형 계약이 태준의 표준조건표 없이는 CEO 결재 버튼에 도달하지 못하게 만든다.
- WorldState.CurrentEra: 2026년 5월~2028년 4월
- WorldState.CurrentLocation: 한서반도체 본사, 감사팀, 품질 데이터룸, 구매실, 법무팀, CEO실, 이사회, 고객/장비사 전장
- KeyNPCs[0].name: 서태준
- KeyNPCs[1].name: 권도윤
- KeyNPCs[2].name: 민재헌
- plot_roadmap[0].title: 도장 라인
- plot_roadmap[34].title: 작업 원장 적용권
- plot_roadmap[69].title: 조건표 없는 계약은 못 지나간다

## 메모
- pattern_feedback_snapshot.top_opponents: [('권도윤 CFO / 감사실 선임부장 / 이사회 감사위원', 4), ('권도윤 CFO / 해외 장비사 아시아 총괄 / 경쟁사 구매 라인', 3), ('민재헌 품질본부장 / 권도윤 CFO', 2)]
- pattern_feedback_snapshot.top_weaknesses: [('계약 성공을 서두르느라 감사 서명 책임 귀속을 낮게 봤다.', 1), ('CEO 지시 직후 파일명이 바뀐 흔적과 외부 고객사 반송 메일은 기술 해석이 아니라 감사 보존 대상이다.', 1), ('품질본부는 원본 보존 명령 때문에 동일 조건 재현을 거부하기 어렵고, CFO실은 발표 초안을 돌린 만큼 회수 기록을 남긴다.', 1)]
- summary: 5개 PASS 모두 통과
