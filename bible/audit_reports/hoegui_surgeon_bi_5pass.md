# BI 5-Pass 감리 보고서 (2026-04-13)

## 대상
- phase0: `treatments/phase0/hoegui_surgeon_phase0_design.json`
- draft: `treatments/hoegui_surgeon_tr_block_020_draft.json`
- bi: `bible/0_bi_hoegui_surgeon.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 정년퇴직 외과의가 레지던트 1년차로 돌아갔다
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['정년퇴직 외과의가 레지던트 1년차로 돌아갔다']
- bi_meta_title: 정년퇴직 외과의가 레지던트 1년차로 돌아갔다
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: []

## Source TR Metrics
- production_density_gate: FAIL
- avg_bundle_chars: 2238.8
- avg_solution_chars: 779.5
- foreshadow_total: 52
- callback_total: 213
- callback_ratio: 4.1
- unresolved_foreshadow_count: 0
- diegetic_meta_ref_count: 741
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 741
- opponent_unique: 45
- top_opponent_repetition: 13
- top_opponent_share: 18.6%
- top_weakness_repetition: 1
- deal_top_repetition: 0
- method_top_repetition: 1
- solution_tail20_top_repetition: 1
- one_sentence_like_solution_blocks: 0
- business_sector_missing: 70
- section_rotation_missing: 0
- critical_thin_blocks: []
- thin_blocks: []
- short_stakes_blocks: []
- same_location_clone_count: 0
- npc_continuity_mismatch_count: 129
- recognition_signal_blocks: 19
- max_recognition_gap_streak: 13
- late_blank_opponent_blocks: []
- endgame_low_stakes_blocks: []
- normalized_solution_stakes_repeat_max: 1
- hard_gate_failures: ['diegetic_meta_ref_zero', 'diegetic_block_ref_zero']
- window_10_opponent_unique_counts: [1, 3, 8, 7, 9, 10, 10]

## Meta Leak Check
- bi_diegetic_meta_leak_count: 753
- bi_label_meta_leak_count: 0
- bi_diegetic_meta_leak_examples:
  - `ProjectData.CoreIdentity.desire` -> 지도교수의 수술 접근법 오판을 차트 기록으로 먼저 읽어 적중시키고, 과장 직보선 + 고난도 케이스 사전 배정 + 컨퍼런스 발표권을 Block 1 안에 확보한다.
  - `FinanceHUD.Protagonist.actual_truth.portfolio_history[4].total_assets` -> FS-02 full payoff + 강태준 불편한 공존 관계 + ARC-04 exit 완성 R2 (특별 카테고리 펠로우, ARC-05 진입 준비)
  - `FinanceHUD.Protagonist.actual_truth.portfolio_history[5].total_assets` -> 외과 교수 인사 위원회 조교수 후보 등재 6:3 통과 + 추천 근거 7축 서면 고정 + ARC-05 exit_function 3축(조교수 후보 + 독립 수술팀 관행 + 국내 학회 주목) 달성 + 강태준 공식 반대 부재 + 4단 운영 단서 수용 R2 (실제 임용은 상위 인사 위원회 심사 대기 단계, 즉각 임용 아님)
  - `FinanceHUD.Protagonist.actual_truth.portfolio_history[6].total_assets` -> 외과 수술 교육 위원회 4축 필수 모듈 편제안 가결 13:0:2 + FS-20 full_payoff + 2029-09 신학기 적용 확정 + 대한외과학회 춘계 심포지엄 공식 세션 실행 완결(익명화 완벽) + 세션 공식 보고서 6월 말 확정 예정 + 권혁수 학술 자산 여섯 번째 재소환(형식 한정 불변) + FS-21 강태준 리마인드 앵커 작동(I-31-40-C 해소) + ARC-06 exit_function 3축 달성 확정(과 운영 실무/수술 교육 체계 재편 시작/병원장 라인 독립) + 7월 TF 직책 자동 해제 예정 + 조교수 4축 공식 운영권 단일 직책 복귀 예정 A1 (ARC-06 정식 종결)
  - `FinanceHUD.Protagonist.actual_truth.current_objective` -> 지도교수의 수술 접근법 오판을 차트 기록으로 먼저 읽어 적중시키고, 과장 직보선 + 고난도 케이스 사전 배정 + 컨퍼런스 발표권을 Block 1 안에 확보한다.
  - `AssetLibrary.KeyNPCs[0].key_turning_points[0].event` -> 지도교수의 수술 접근법 오판을 차트 기록으로 먼저 읽어 적중시키고, 과장 직보선 + 고난도 케이스 사전 배정 + 컨퍼런스 발표권을 Block 1 안에 확보한다.
  - `AssetLibrary.LocationPool[55]` -> 외과 조교수 연구실(제안서 작성 4월) → 외과 과장실 검토 → 강태준 서면 회신 수신 → 서울 코엑스 그랜드볼룸 E홀 대한외과학회 2029 춘계 심포지엄 공식 세션(5월 마지막 주 금요일) → 외과 수술 교육 위원회 정기 회의 심의·가결(6월 둘째 주) → 외과 과장실 3단 정리 → 외과 복도 강태준 짧은 마주침 → 차트 노트 ARC-06 exit 4문단 기록
  - `AssetLibrary.LocationPool[60]` -> 대학병원 수술실 4호실 (Block 64 연속 — 간담췌 고난도 수술 전용실 + 실시간 도플러 초음파 이중 모니터 + 마취과 생체 징후 모니터링 시스템 + 집도팀 5-6인) + 외부 관찰자 0
  - `AssetLibrary.CapitalCurve[4].capital_after` -> FS-02 full payoff + 강태준 불편한 공존 관계 + ARC-04 exit 완성 R2 (특별 카테고리 펠로우, ARC-05 진입 준비)
  - `AssetLibrary.CapitalCurve[5].capital_after` -> 외과 교수 인사 위원회 조교수 후보 등재 6:3 통과 + 추천 근거 7축 서면 고정 + ARC-05 exit_function 3축(조교수 후보 + 독립 수술팀 관행 + 국내 학회 주목) 달성 + 강태준 공식 반대 부재 + 4단 운영 단서 수용 R2 (실제 임용은 상위 인사 위원회 심사 대기 단계, 즉각 임용 아님)

## Canonical Contract
- raw_bi_canonical_contract: PASS
- raw_tr_canonical_contract: PASS
- raw_pair_canonical_contract: PASS
- normalized_bi_canonical_view: PASS
- normalized_tr_canonical_view: PASS
- normalized_pair_canonical_view: PASS

## PASS 1: 인코딩/파싱
- result: FAIL
- utf8_json_parse: OK
- garbled_token_zero: OK
- diegetic_meta_text_zero: FAIL
- label_meta_text_zero: OK
- draft_schema_valid: OK

## PASS 2: 최소 스키마
- result: OK
- validate_bible_structure: OK
- meta_title_present: OK
- plot_roadmap_len_70: OK

## PASS 3: source TR handoff gate
- result: FAIL
- source_tr_density_gate: FAIL
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
- source_tr_meta_gate: FAIL
- source_tr_label_meta_gate: OK
- source_tr_block_meta_gate: FAIL
- source_tr_npc_continuity_gate: FAIL
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
- MetaInfo.title: 정년퇴직 외과의가 레지던트 1년차로 돌아갔다
- MetaInfo.grand_objective: 65세 정년퇴직 외과 과장이 28세 R1으로 돌아가, 3만 건 수술에서 축적한 합병증 패턴 판독력으로 교수의 오판을 수술 전에 읽고 차트에 기록으로 남겨, 적중이 반복되면서 서열은 그대로인데 실질적 수술 결정권이 뒤집히는 의료 권력 상승물.
- MetaInfo.genre_archetype: 현대 한국 대학병원 의료 권력 장악물
- MetaInfo.logline: 갈고리만 잡던 R1의 차트 한 줄이 교수의 메스를 멈춘다.
- CoreIdentity.protagonist: 서동혁
- CoreIdentity.protagonist_faction:  -> 
- CoreIdentity.edge: 30년 3만 건 수술에서 축적한 합병증 패턴 판독력. 영상 소견, 혈액 수치, 환자 자세 하나로 수술 중 변수를 수술 전에 읽는다. 28세 체력(손 떨림 0) + 65세 판단력의 물리적 조합.
- CoreIdentity.desire: 지도교수의 수술 접근법 오판을 차트 기록으로 먼저 읽어 적중시키고, 과장 직보선 + 고난도 케이스 사전 배정 + 컨퍼런스 발표권을 Block 1 안에 확보한다.
- CoreIdentity.crisis: 갈고리만 잡던 R1의 차트 한 줄이 교수의 메스를 멈춘다.
- FinanceHUD.actual_truth.name: 서동혁
- FinanceHUD.actual_truth.rank: 대학병원 외과 레지던트 1년차 (R1). 65세 정년퇴직 외과 과장에서 회귀. / 
- FinanceHUD.actual_truth.current_objective: 지도교수의 수술 접근법 오판을 차트 기록으로 먼저 읽어 적중시키고, 과장 직보선 + 고난도 케이스 사전 배정 + 컨퍼런스 발표권을 Block 1 안에 확보한다.
- FinanceHUD.actual_truth.final_goal: 대학병원 외과에서 '이 사람 소견 없이 고난도 수술을 열지 않는다'는 관행을 확립하고, 병원 정치를 실력 기반 권한 구조로 재편한다.
- WorldState.CurrentEra: 2026년 3월 초, 오전~오후
- WorldState.CurrentLocation: 한림대학교병원 외과 브리핑룸 → 차트실
- KeyNPCs[0].name: 서동혁
- KeyNPCs[1].name: 강태준
- KeyNPCs[2].name: 조영채
- plot_roadmap[0].title: 갈고리
- plot_roadmap[34].title: 연구실 봉쇄
- plot_roadmap[69].title: 왕좌

## 메모
- pattern_feedback_snapshot.top_opponents: [('강태준', 13), ('박정민 (간접)', 1), ('박정민 / 강태준 (간접)', 1)]
- pattern_feedback_snapshot.top_weaknesses: [('R1의 의견을 소음으로 처리하는 관성', 1), ('R1 차트 노트를 읽지 않는 관행', 1), ('변이 혈관 미인지', 1)]
- pattern_feedback_snapshot.solution_pattern_warnings: ['diegetic meta leak 741건', 'npc continuity mismatch 129건']
- pattern_feedback_snapshot.structural_gate_failures: ['diegetic_meta_ref_zero', 'diegetic_block_ref_zero']
- summary: 2개 PASS 실패

