# BI 5-Pass 감리 보고서 (2026-05-02)

## 대상
- phase0: `treatments/phase0/telecom_gate_monopoly_1997_phase0_design.json`
- draft: `treatments/telecom_gate_monopoly_1997_tr_block_001_draft.json`
- bi: `bible/0_bi_telecom_gate_monopoly_1997.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 1997년, 통신 게이트를 독식했다
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['1997년, 통신 게이트를 독식했다']
- bi_meta_title: 1997년, 통신 게이트를 독식했다
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: []

## Source TR Metrics
- production_density_gate: PASS
- avg_bundle_chars: 1133.07
- avg_solution_chars: 276.67
- foreshadow_total: 286
- callback_total: 209
- callback_ratio: 0.73
- unresolved_foreshadow_count: 67
- diegetic_meta_ref_count: 0
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 0
- opponent_unique: 69
- top_opponent_repetition: 2
- top_opponent_share: 2.9%
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
- recognition_signal_blocks: 15
- max_recognition_gap_streak: 9
- late_blank_opponent_blocks: []
- endgame_low_stakes_blocks: []
- normalized_solution_stakes_repeat_max: 1
- hard_gate_failures: []
- window_10_opponent_unique_counts: [10, 10, 10, 10, 10, 9, 10]

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
- MetaInfo.title: 1997년, 통신 게이트를 독식했다
- MetaInfo.grand_objective: 2026년 플랫폼 결제 전략가였던 강재현은 1997년 IMF 직후 태림그룹 방계 손자의 몸에 빙의해, 모두가 팔아치우려는 PCS 지분, 기지국 유지보수권, 단말 유통망, 카드 청구망을 하나의 월 청구서 게이트로 묶어 통신에서 금융, 게임, 쇼핑, 광고까지 모든 섹터의 입장료를 받는 제국을 만든다.
- MetaInfo.genre_archetype: 현대 한국 business-power 재벌 빙의 통신 플랫폼 독식물
- MetaInfo.logline: 강재현은 태림그룹을 착해서 구하지 않는다. 따로 팔리면 고철인 번호, 단말, 유지보수, 청구망을 묶어 자신만 통행료를 받는 게이트로 만든다.
- CoreIdentity.protagonist: 강재현
- CoreIdentity.protagonist_faction: 태림모바일서비스 -> 태림모바일서비스
- CoreIdentity.edge: 전화번호, 단말 유통, 기지국 유지보수, 카드 청구, 부가서비스 정산을 하나의 플랫폼 게이트로 묶어 읽는 2026년식 결제/플랫폼 감각.
- CoreIdentity.desire: 72시간 안에 PCS 잔여 의결권, 태림전선 유지보수 SLA, 태림전자 단말 창고, 태림카드 청구 대행 계약을 묶어 구조조정위원회 동석권과 매각 보류권을 확보한다.
- CoreIdentity.crisis: 강재현은 태림그룹을 착해서 구하지 않는다. 따로 팔리면 고철인 번호, 단말, 유지보수, 청구망을 묶어 자신만 통행료를 받는 게이트로 만든다.
- FinanceHUD.actual_truth.name: 강재현
- FinanceHUD.actual_truth.rank: 태림그룹 방계 손자이자 구조조정 TF의 부실자산 정리 담당. 본가는 그를 폐품 목록에 줄 긋는 사람으로 본다. / 태림모바일서비스
- FinanceHUD.actual_truth.current_objective: 72시간 안에 PCS 잔여 의결권, 태림전선 유지보수 SLA, 태림전자 단말 창고, 태림카드 청구 대행 계약을 묶어 구조조정위원회 동석권과 매각 보류권을 확보한다.
- FinanceHUD.actual_truth.final_goal: 2002년까지 국민 휴대폰 번호와 월 청구서 기반의 생활계정 게이트를 장악해 모든 섹터가 태림모바일서비스에 통행료를 내게 만든다.
- WorldState.CurrentEra: 1997년 12월 IMF 구조조정 첫 주
- WorldState.CurrentLocation: 태림그룹 본관 17층 구조조정 TF 회의실 / 야간 문서보관실
- KeyNPCs[0].name: 강재현
- KeyNPCs[1].name: 장문기
- KeyNPCs[2].name: 송인호
- plot_roadmap[0].title: 폐품 목록에 줄 긋는 도련님
- plot_roadmap[34].title: 동의서가 한도가 된다
- plot_roadmap[69].title: 모든 길은 월 청구서로 돌아온다

## 메모
- pattern_feedback_snapshot.top_opponents: [('통신사 광고 담당자 / 데이터센터 투자 반대파 / 스팸 민원 라인 / 기업 고객', 2), ('장문기 / 본가 기획조정실 / 외국계 펀드', 1), ('장문기 / 노태섭 / 본가 기획조정실 / 백도균', 1)]
- pattern_feedback_snapshot.top_weaknesses: [('각자 빠른 매각과 분리매입만 보며 번호, 유지보수, 단말, 청구, 점포가 결합될 때 생기는 반복 수수료 gate를 보지 못한다', 1), ('빠른 현금화와 책임 회피 때문에 분리 매각 후 남는 위약금, 가입자 확보 비용, 회수율 하락을 한 표에서 동시에 보지 못한다', 1), ('조달팀은 싸구려 하청을 싫어하지만 SLA 위약금과 가입자 민원비용을 줄이는 검증된 복구 capacity는 버릴 수 없다', 1)]
- summary: 5개 PASS 모두 통과
