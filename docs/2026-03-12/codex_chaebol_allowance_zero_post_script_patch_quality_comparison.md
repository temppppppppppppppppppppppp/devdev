# `chaebol_allowance_zero` 스크립트 패치 후 실제 재실행 품질 비교

## Findings

- `BLOCKER`는 해소됐다. 하네스 문서 보강이 실제 생성기/감리 스택에 연결되지 않던 문제가 있었는데, 이번 패치로 [generate_chaebol_allowance_zero_retry.py](/c:/Users/wjjo/Desktop/글도비/scripts/generate_chaebol_allowance_zero_retry.py), [tr_batch_harness.py](/c:/Users/wjjo/Desktop/글도비/scripts/tr_batch_harness.py), [audit_bi_5pass.py](/c:/Users/wjjo/Desktop/글도비/scripts/audit_bi_5pass.py), [build_bi_from_phase0_and_tr.py](/c:/Users/wjjo/Desktop/글도비/scripts/build_bi_from_phase0_and_tr.py)가 새 하네스 규칙을 일부 실제로 반영한다.
- `MAJOR` 새 재실행본은 실패본보다 확실히 낫고, 기존 retry보다도 `반복 억제`와 `상대 다양성`은 더 좋아졌다. 반면 `평균 분량`은 기존 retry보다 낮아졌다.
- `MAJOR` BI 게이트는 이제 source TR 품질을 실제로 본다. 실패 BI는 2026-03-12 재실행 기준 `FAIL`, 기존 retry BI와 새 generic rerun BI는 `PASS`였다.
- `MEDIUM` generic BI builder는 `chaebol_allowance_zero`에는 통과했고, `us_ai_exile_monopoly`도 런타임 빌드는 통과했다. 다만 AI 쪽은 source TR이 새 audit gate에서 `weakness` 반복으로 걸려 BI audit 최종값은 `FAIL`이었다. 즉 빌더 문제와 source TR 문제를 분리해서 봐야 한다.

## TR Comparison

비교 대상:
- 실패본 TR: [02_chaebol_allowance_zero_tr_block_070_draft.json](/c:/Users/wjjo/Desktop/글도비/treatments/02_chaebol_allowance_zero_tr_block_070_draft.json)
- 기존 retry TR: [chaebol_allowance_zero_tr_block_070_draft.json](/c:/Users/wjjo/Desktop/글도비/treatments/chaebol_allowance_zero_tr_block_070_draft.json)
- 스크립트 패치 후 rerun v2 TR: `C:\Users\Public\Documents\ESTsoft\CreatorTemp\codex_chaebol_allowance_zero_rerun_v2\treatments\chaebol_allowance_zero_tr_block_070_draft.json`

핵심 수치:

| metric | 실패본 | 기존 retry | rerun v2 |
| --- | ---: | ---: | ---: |
| `production_density_gate` | FAIL | PASS | PASS |
| `avg_bundle_chars` | 321.29 | 972.93 | 890.24 |
| `avg_solution_chars` | 86.50 | 265.01 | 172.34 |
| `opponent_unique` | 4 | 31 | 35 |
| `weakness_unique` | 7 | 70 | 70 |
| `top_opponent_repetition` | 29 | 17 | 11 |
| `top_opponent_share` | 41.4% | 24.3% | 15.7% |
| `top_weakness_repetition` | 10 | 1 | 1 |
| `solution_tail20_top_repetition` | 14 | 57 | 12 |
| `one_sentence_like_solution_blocks` | 70 | 0 | 0 |
| `business_sector_missing` | 0 | 0 | 0 |
| `section_rotation_missing` | 0 | 0 | 0 |

10블록 구간 opponent 다양성:
- 실패본: `[2, 2, 2, 2, 2, 2, 3]`
- 기존 retry: `[8, 6, 5, 5, 5, 6, 5]`
- rerun v2: `[6, 7, 7, 7, 7, 7, 6]`

직접 차이:
- 기존 retry와 rerun v2는 `title` 70개는 모두 같지만, `block hash`가 같은 블록은 `0/70`이다.
- opponent 슬롯이 같은 블록은 `36/70`이다.
- 즉 이번 rerun v2는 텍스트와 opponent 배치가 실제로 다시 생성된 결과다.

해석:
- 실패본은 여전히 `2~3인 로테이션`, `weakness` 10회 반복, `한 문장 solution` 70/70이라는 구조적 실패다.
- 기존 retry는 실패본을 구조적으로 극복했지만, `solution tail-20` 반복이 `57`로 높아 `cadence` 경고가 심했다.
- rerun v2는 기존 retry 대비 분량은 줄었지만, `opponent_unique 31 -> 35`, `top_opponent_share 24.3% -> 15.7%`, `solution_tail20_top_repetition 57 -> 12`로 개선됐다.
- 결론적으로 rerun v2는 `반복 억제와 배분 품질`은 올라갔고, `서술 밀도`는 조금 내려갔다.

샘플 차이:
- B02 opponent가 `최병태 -> 강미선`으로 바뀌었다.
- B04 opponent가 `오세란 -> 박선오`로 바뀌었다.
- 기존 retry의 반복 tail인 `상대가 비용으로만 보던 것을 반복 수익과 통제권으로 재정의한다` 류 문장이 rerun v2에서는 크게 줄었다.

## BI Comparison

비교 대상:
- 실패본 BI: [02_bi_chaebol_allowance_zero.json](/c:/Users/wjjo/Desktop/글도비/bible/02_bi_chaebol_allowance_zero.json)
- 기존 retry BI: [0_bi_chaebol_allowance_zero.json](/c:/Users/wjjo/Desktop/글도비/bible/0_bi_chaebol_allowance_zero.json)
- generic rerun BI: `C:\Users\Public\Documents\ESTsoft\CreatorTemp\codex_chaebol_allowance_zero_rerun_v2\bible\0_bi_chaebol_allowance_zero_generic_rerun.json`

2026-03-12 동일 audit 기준:
- 실패본 BI + 실패본 TR: `FAIL`
- 기존 retry BI + 기존 retry TR: `PASS`
- generic rerun BI + rerun v2 TR: `PASS`

판정 근거:
- 실패본 BI는 [audit_bi_5pass.py](/c:/Users/wjjo/Desktop/글도비/scripts/audit_bi_5pass.py) 패치 이후 source TR handoff gate에서 탈락한다.
- 기존 retry BI와 generic rerun BI는 둘 다 `plot_roadmap` 길이/시퀀스/hash, protagonist/title/company, portfolio sync를 통과한다.
- generic rerun BI는 이제 legacy 전용 builder가 아니라 [build_bi_from_phase0_and_tr.py](/c:/Users/wjjo/Desktop/글도비/scripts/build_bi_from_phase0_and_tr.py)로도 생성 가능하다.

generic builder 보강 결과:
- `partner_location_sector_distribution`, `capital_curve`, `defeat_blocks`가 phase0에 없어도 treatment에서 파생 가능하다.
- `npc_timeline[*].turning_points`만 보던 문제를 `key_turning_points` fallback으로 보정했다.
- `arcs[*].block_slots`가 없어도 `entry_function`/`exit_function`과 `block_range`로 Arc/HistoricalEvents를 복원한다.
- 엔터 전용 하드코딩(`세령컬처웍스`, `스타 IP`, `entertainment`)은 일반화했다.

회귀 체크:
- [build_bi_from_phase0_and_tr.py](/c:/Users/wjjo/Desktop/글도비/scripts/build_bi_from_phase0_and_tr.py)는 `us_ai_exile_monopoly`도 빌드 자체는 통과했다.
- 다만 AI 쪽 BI audit는 `source_tr_weakness_repeat_gate`에서 `FAIL`이다.
- 이건 generic builder 회귀가 아니라 기존 [us_ai_exile_monopoly_tr_block_070_draft.json](/c:/Users/wjjo/Desktop/글도비/treatments/us_ai_exile_monopoly_tr_block_070_draft.json)의 `weakness` 패턴이 새 audit gate에서 너무 반복적이라는 뜻이다.

## Remaining Gaps

- rerun v2는 기존 retry보다 `avg_bundle_chars`와 `avg_solution_chars`가 낮다. 다양성 개선과 분량 저하를 같이 가져간 셈이라, 다음 패치는 `solution`의 문장 수를 유지한 채 cadence만 줄이는 방향이 맞다.
- [generate_chaebol_allowance_zero_retry.py](/c:/Users/wjjo/Desktop/글도비/scripts/generate_chaebol_allowance_zero_retry.py)는 여전히 `solution_intro/bridge/tail` 조합형 생성기다. 지금은 이전보다 낫지만, 다음 단계에서는 `sector별 solution family`를 더 벌려야 한다.
- [audit_bi_5pass.py](/c:/Users/wjjo/Desktop/글도비/scripts/audit_bi_5pass.py)는 source TR gate를 보게 됐지만, `cadence_warning`는 아직 warning이다. 충분히 좋지 않은 TR이 BI PASS로 올라갈 여지가 남아 있다.
- `us_ai_exile_monopoly`는 이제 generic builder로 BI를 만들 수 있지만, source TR 자체가 새 하네스 기준을 만족하지 못한다. 다음 타깃은 BI builder가 아니라 AI TR 쪽 반복 구조다.

## Final Verdict

이번 라운드의 결론은 명확하다. 하네스 문서 패치만으로 끝나던 상태를 넘어서, 스크립트가 실제로 새 규칙을 먹기 시작했다. `chaebol_allowance_zero` 기준으로는 실패본 대비 개선이 재확인됐고, 기존 retry와 비교해도 rerun v2가 `반복 억제`와 `상대 다양성`에서 더 낫다. 반면 `밀도`는 약간 희생됐으므로, 다음 패치는 생성기 쪽 `solution` 분량 복원에 집중하는 것이 맞다.
