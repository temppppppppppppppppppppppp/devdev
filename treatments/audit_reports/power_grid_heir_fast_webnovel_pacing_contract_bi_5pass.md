# BI 5-Pass 감리 보고서 (2026-05-03)

## 대상
- phase0: `treatments/phase0/power_grid_heir_phase0_design.json`
- draft: `treatments/power_grid_heir_tr_block_070_draft.json`
- bi: `bible/0_bi_power_grid_heir.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 회귀한 재벌 3세는 전력망을 산다
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['회귀한 재벌 3세는 전력망을 산다']
- bi_meta_title: 회귀한 재벌 3세는 전력망을 산다
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: []

## Source TR Metrics
- production_density_gate: PASS
- avg_bundle_chars: 802.96
- avg_solution_chars: 206.56
- foreshadow_total: 140
- callback_total: 159
- callback_ratio: 1.14
- unresolved_foreshadow_count: 49
- diegetic_meta_ref_count: 0
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 0
- opponent_unique: 50
- top_opponent_repetition: 5
- top_opponent_share: 7.1%
- top_weakness_repetition: 1
- deal_top_repetition: 1
- method_top_repetition: 1
- solution_tail20_top_repetition: 1
- one_sentence_like_solution_blocks: 2
- business_sector_missing: 0
- section_rotation_missing: 0
- critical_thin_blocks: []
- thin_blocks: []
- short_stakes_blocks: []
- same_location_clone_count: 0
- npc_continuity_mismatch_count: 0
- recognition_signal_blocks: 17
- max_recognition_gap_streak: 9
- late_blank_opponent_blocks: []
- endgame_low_stakes_blocks: []
- normalized_solution_stakes_repeat_max: 1
- hard_gate_failures: []
- window_10_opponent_unique_counts: [8, 8, 5, 10, 8, 8, 8]

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
- MetaInfo.title: 회귀한 재벌 3세는 전력망을 산다
- MetaInfo.grand_objective: 미래의 AI/data center 호황이 전력망, 변압기, 냉각수, PPA, SLA, project finance 병목에서 무너지는 것을 본 서도윤은 회귀 후 AI 회사가 아니라 AI 기업들이 반드시 통과해야 하는 전력 권리와 결재권을 선점한다.
- MetaInfo.genre_archetype: 현대 한국 no-system 회귀 재벌 business-power 인프라 성장물
- MetaInfo.logline: 회귀 직후 도윤은 선우그룹의 AI 데이터센터 계약에서 power SLA 폭탄을 발견한다. 그는 맞는 말을 하는 대신 72시간 review right를 사서, 전력망 병목을 권한 영수증으로 환전하기 시작한다.
- CoreIdentity.protagonist: 서도윤
- CoreIdentity.protagonist_faction: 선우그룹 회장실 / AI 데이터센터 계약 승인 회의 -> 선우그룹 회장실 / AI 데이터센터 계약 승인 회의
- CoreIdentity.edge: AI boom의 진짜 병목을 GPU가 아니라 전력망, 변압기, 냉각수, site permit, PPA, SLA, project finance로 읽고 현재 문서로 증명한다.
- CoreIdentity.desire: AI 데이터센터 계약의 power SLA 폭탄을 멈추고 72시간 review right를 얻는다.
- CoreIdentity.crisis: 회귀 직후 도윤은 선우그룹의 AI 데이터센터 계약에서 power SLA 폭탄을 발견한다. 그는 맞는 말을 하는 대신 72시간 review right를 사서, 전력망 병목을 권한 영수증으로 환전하기 시작한다.
- FinanceHUD.actual_truth.name: 서도윤
- FinanceHUD.actual_truth.rank: 선우그룹 branch-line 3세. 과거 생에서는 전력망 리스크 보고서를 냈지만 결재권이 없어 묵살당했다. / 선우그룹 회장실 / AI 데이터센터 계약 승인 회의
- FinanceHUD.actual_truth.current_objective: AI 데이터센터 계약의 power SLA 폭탄을 멈추고 72시간 review right를 얻는다.
- FinanceHUD.actual_truth.final_goal: Strategic Power TF를 통해 선우그룹을 AI 시대의 전력 관문으로 만들고, 자신 없이는 그룹의 AI 인프라 판단이 움직이지 않는 상태를 만든다.
- WorldState.CurrentEra: 2026년 5월 초
- WorldState.CurrentLocation: 선우그룹 회장실 승인 회의
- KeyNPCs[0].name: 서도윤
- KeyNPCs[1].name: 서문호
- KeyNPCs[2].name: 서강준
- plot_roadmap[0].title: 서명 전 별첨
- plot_roadmap[34].title: 투자자 앞의 화살표
- plot_roadmap[69].title: 전력망을 산 후계자

## 메모
- pattern_feedback_snapshot.top_opponents: [('선우오션 구조조정 라인', 5), ('서강준', 4), ('외부 MRO 경쟁사', 4)]
- pattern_feedback_snapshot.top_weaknesses: [('본문 매출과 별첨 책임을 같은 화면에 놓지 않은 점', 1), ('AI 고객 확보 압박 때문에 전력 책임 검토를 뒤로 미룬 점', 1), ('납기와 안전을 분리해 보고 중단 비용을 한 표로 보지 않은 점', 1)]
- summary: 5개 PASS 모두 통과
