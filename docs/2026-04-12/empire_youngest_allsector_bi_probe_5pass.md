# BI 5-Pass 감리 보고서 (2026-04-12)

## 대상
- phase0: `treatments/_quarantine/empire_youngest_allsector_phase0_design.json`
- draft: `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
- bi: `docs/temp/empire_youngest_allsector_bi_probe.json`

## Naming Authority
- phase0_title_resolution: phase0.project.title_ko/title
- phase0_canonical_title: 제국의 막내: 모든 섹터를 먹는 남자
- phase0_commercial_label: (none)
- phase0_slug_aliases: []
- phase0_allowed_titles: ['제국의 막내: 모든 섹터를 먹는 남자']
- bi_meta_title: 제국의 막내: 모든 섹터를 먹는 남자
- bi_meta_commercial_label: (none)
- bi_meta_slug_aliases: []

## Source TR Metrics
- production_density_gate: PASS
- avg_bundle_chars: 1342.87
- avg_solution_chars: 369.71
- foreshadow_total: 173
- callback_total: 190
- callback_ratio: 1.1
- unresolved_foreshadow_count: 0
- diegetic_meta_ref_count: 0
- label_meta_ref_count: 0
- diegetic_block_ref_count(alias): 0
- opponent_unique: 66
- top_opponent_repetition: 1
- top_opponent_share: 1.4%
- top_weakness_repetition: 1
- deal_top_repetition: 3
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
- recognition_signal_blocks: 21
- max_recognition_gap_streak: 13
- late_blank_opponent_blocks: [70]
- endgame_low_stakes_blocks: []
- normalized_solution_stakes_repeat_max: 1
- hard_gate_failures: []
- window_10_opponent_unique_counts: [9, 10, 10, 9, 10, 9, 9]

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
- MetaInfo.title: 제국의 막내: 모든 섹터를 먹는 남자
- MetaInfo.grand_objective: 2045년 제국그룹 파산·추락사 직후 2025년으로 회귀한 재벌 3세 막내 이준서가, 20년치 미래 데이터를 무기로 코인→반도체→바이오→AI부터 금융·방산·우주까지 항상 3개 섹터를 동시에 굴려, 0원에서 200조 J제국홀딩스를 혼자 짓고 썩어가던 제국그룹을 통째로 먹는다.
- MetaInfo.genre_archetype: 현대 한국 회귀·재벌경영 전섹터 투자물
- MetaInfo.logline: 형들이 싸우고 아버지가 무너지고 제국이 썩는 걸 20년간 봤다. 이번엔 혼자서 짓는다 — 반도체, 바이오, AI, 금융, 방산, 우주까지. 항상 세 개씩. 쉬지 않고.
- CoreIdentity.protagonist: 이준서
- CoreIdentity.protagonist_faction: JSR인베스트먼트 -> JSR인베스트먼트
- CoreIdentity.edge: 20년치 미래 데이터(섹터 승자·패자·정책·규제 타이밍) + 전 섹터 연결 그림을 혼자 보는 유일한 인간 + 감정 없는 효율 극대화 의사결정
- CoreIdentity.desire: 0원에서 시작해 코인/주식으로 시드 머니 2,000억 확보
- CoreIdentity.crisis: 형들이 싸우고 아버지가 무너지고 제국이 썩는 걸 20년간 봤다. 이번엔 혼자서 짓는다 — 반도체, 바이오, AI, 금융, 방산, 우주까지. 항상 세 개씩. 쉬지 않고.
- FinanceHUD.actual_truth.name: 이준서
- FinanceHUD.actual_truth.rank: 제국그룹 3세 막내. 회귀 전 전략기획실 상무(무시당함) / JSR인베스트먼트
- FinanceHUD.actual_truth.current_objective: 0원에서 시작해 코인/주식으로 시드 머니 2,000억 확보
- FinanceHUD.actual_truth.final_goal: 제국그룹 경영권 확보(지분 51.3%) 후 부실 22개사 정리, 핵심 26개 통합, J제국홀딩스 200조+ 출범
- WorldState.CurrentEra: 2045년 8월 29일 → 2025년 3월 2일 오전
- WorldState.CurrentLocation: 서울대학교 경영대학원 강의실 및 복도 (2025년 3월). 프롤로그는 제국홀딩스 본사 42층 옥상 (2045년 8월).
- KeyNPCs[0].name: 이준서
- KeyNPCs[1].name: 정하윤
- KeyNPCs[2].name: 김태석
- plot_roadmap[0].title: 옥상에서 강의실로
- plot_roadmap[34].title: 권도준 영입, 방산 포석
- plot_roadmap[69].title: 다음 섹터.

## 메모
- pattern_feedback_snapshot.top_opponents: [('시장 낙관론 (구조적 적대)', 1), ('정하윤의 의심 (내부 마찰)', 1), ('시장 컨센서스 (반도체 하강론)', 1)]
- pattern_feedback_snapshot.top_weaknesses: [("시장 참여자 대부분이 '20만 달러 돌파'를 확신하며 펀딩비율 역대 최고치를 기록 중이다. 과열된 낙관이 바로 천장 신호지만, 시장 안에서는 아무도 그것을 인정하지 않는다.", 1), ("정하윤은 대형 증권사에서 실력은 인정받았으나 승진이 막혀 있었다. 조직 안에서 더 클 수 없다는 좌절이 '비합리적으로 보이는 제안'을 받아들이게 만든 구조적 빈틈이다.", 1), ("시장 전체가 '반도체 사이클 하강'이라는 과거 패턴에 갇혀 HBM이라는 새로운 변수를 과소평가하고 있다. 공급망 재편보다 과거 사이클 반복을 믿는 관성이 빈틈.", 1)]
- summary: 5개 PASS 모두 통과

