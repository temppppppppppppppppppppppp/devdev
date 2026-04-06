# `chaebol_allowance_zero` 실패본 vs 재시도본 Fusion

## Findings

1. `Major` 재시도본은 실패본을 실무 기준에서 대체 가능하다. 직접 재검증 기준으로 TR은 `opponent_unique 4 -> 31`, `weakness_unique 7 -> 70`, `avg_bundle_chars 321.29 -> 972.93`로 개선됐고, 실패본의 초반 10블록 2인 로테이션과 10회 weakness 반복이 해소됐다.
2. `Major` BI는 둘 다 `MasterBible.plot_roadmap` 길이 70과 title sequence 정합성은 맞지만, `FinanceHUD.portfolio_history`는 두 파일 모두 비어 있다. 따라서 기존 비교 문서의 "portfolio_history 동기화" 표현은 과했고, 직접 확인 가능한 동기화 축은 `financial_status.total_assets`와 `mobilizable_capital`이다.
3. `Major` D2 비교 오더의 핵심 오기는 정리됐다. 현재 골든 TR 정본은 `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`이고, 실패 TR 정본은 `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`이며, 실패본 아크 6 opponent는 `윤석진 5 / 백도현 5` 2명이다.
4. `Major` 현행 `R31`은 비교 결론과 분리해야 한다. 실패본은 `tail-20 최다 14블록`으로 충분히 FAIL이지만, 현재 골든 TR도 `tail-20 최다 57블록`으로 걸리므로 하네스 규칙 자체가 과잉이다. 이 문제는 재시도본의 개선 사실을 뒤집지 않고 별도 재조정 이슈로 다루는 것이 맞다.
5. `Medium` `sector missing`은 content defect가 아니라 field-drift 성격으로 보는 편이 맞다. 직접 재검증 결과 실패본과 재시도본 모두 `genre_ext.business_sector`, `genre_ext.section_rotation` 누락이 `0`이다.

## Shared Ground

이번 비교는 같은 기획 축 재시도 비교로 유효하다. 기획 SSOT [opus_재벌3세인데용돈이0원.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-03-10/opus_재벌3세인데용돈이0원.md)와 [chaebol_allowance_zero_phase0_design.json](/c:/Users/wjjo/Desktop/글도비/treatments/chaebol_allowance_zero_phase0_design.json)은 둘 다 `윤재이`, `재벌 3세인데 용돈이 0원`, `가문보다 먼저 돈줄의 주인이 된다` 축을 유지한다. 실패 TR과 재시도 TR도 70개 title sequence가 동일하므로, 이번 결과는 "다른 작품" 비교가 아니라 "같은 작품 같은 기획의 재시도" 비교다.

실패본의 공통 문제는 분명하다. `서도윤/윤석진` 집중, 아크 단위 weakness 고정, `주도권을 자기 쪽으로 당긴다` 계열 solution 반복, 낮은 번들 밀도가 함께 겹쳤다. 재시도본은 같은 타이틀 배열을 유지한 상태에서 opponent와 weakness를 분화하고, solution 길이를 늘리고, 블록당 실행 전개를 확장해 이 패턴을 크게 줄였다.

BI 쪽 공통분모도 분명하다. 둘 다 `MasterBible.plot_roadmap`는 source TR과 맞고, 제목·주인공명·최종 자산 표시는 각 source TR과 맞는다. 반면 BI의 품질 차이는 구조보다 source TR의 품질 차이에 더 가깝고, `portfolio_history`가 비어 있다는 점 때문에 BI 자체의 성장 이력 표현은 아직 약하다.

## Resolved Corrections

| 항목 | 기존 혼선 | Fusion 확정 |
| ---- | --------- | ----------- |
| 골든 TR 정본 | `02_...`를 골든처럼 참조한 문서가 있었음 | `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`이 현재 골든 TR |
| 실패 TR 정본 | 실패 보관본과 현행 복사본이 섞여 있었음 | `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`이 실패 TR 현행 복사본 |
| 실패 아크 6 opponent | `서도윤`이 포함된 3명 아크로 잘못 기술된 문서가 있었음 | 실제는 `윤석진 5 / 백도현 5` 2명 |
| 현재 골든 핵심 수치 | `15명 / 약 33% / 268자` 같은 구버전 수치가 섞였음 | `opponent_unique 31`, `max_share 24.3%`, `avg_bundle_chars 972.93` 기준으로 잠금 |
| `R31` 상태 | 골든 TR도 PASS라고 적힌 문서가 있었음 | 현재 골든 TR은 현행 `R31`에서 `tail-20 최다 57블록`으로 걸림 |
| `sector missing` 판정 | `sector` 단일 키 기준의 실패 평가가 있었음 | `genre_ext.business_sector`와 `genre_ext.section_rotation`를 정식 호환 필드로 인정 |
| BI 자산 동기화 표현 | `portfolio_history` 동기화로 넓게 적은 문서가 있었음 | 직접 확인 가능한 축은 `financial_status.total_assets`와 `mobilizable_capital`이다. 두 BI 모두 `portfolio_history`는 비어 있음 |

## Remaining Open Issues

1. `R31`은 현행 상태로 정본화하면 안 된다. [codex_r31_tail_repetition_recalibration.md](/c:/Users/wjjo/Desktop/글도비/docs/blockguide/codex_r31_tail_repetition_recalibration.md) 기준의 `Hard FAIL / Soft Warning` 이원화가 필요하다.
2. `validate_v3`의 sector 탐색 경로는 `genre_ext.business_sector`, `genre_ext.section_rotation`까지 포함하도록 문서와 코드가 함께 정리돼야 한다.
3. `FinanceHUD.portfolio_history`가 두 BI에서 모두 비어 있다. 앞으로 이 필드를 실제로 채울지, 아니면 BI 비교 계약에서 핵심 축을 `financial_status.total_assets`로 낮출지 정해야 한다.
4. `docs/2026-03-11`와 `docs/blockguide`에 같은 주제의 오더 문서가 중복돼 있다. 이제 `docs/blockguide`판을 정본으로 두고 날짜 폴더 문서는 보관본으로 정리하는 게 맞다.
5. `docs/2026-03-11/opus_chaebol_allowance_zero_failed_vs_retry_comparison.md`는 현재 워크스페이스에서 확인되지 않았다. 필요하면 나중에 이 fusion 문서에 추가 검토본으로만 덧붙이고, 정본 기준은 흔들지 않는 것이 낫다.

## Fusion Verdict

`대체 가능`

재시도본은 같은 기획 축과 같은 70개 블록 제목을 유지하면서도, 실패본의 핵심 결함인 적대자 쏠림, 아크 단위 weakness 복붙, 낮은 번들 밀도를 실질적으로 해소했다. BI도 source TR title sequence와 최종 자산 표시는 각각 정확히 싣고 있어, 산출물 체인은 실패본보다 낫다. 다만 이 결론은 "현재 하네스가 완벽하다"는 뜻이 아니라, "현재 산출물 비교에서는 재시도본이 명백히 우위"라는 뜻이다. 하네스 쪽 미해결 과제는 `R31`과 `portfolio_history` 계약 정리다.

## Next Actions

1. 비교 결론만 확정할 거면 이 문서를 최종본으로 두고 종료한다.
2. 하네스까지 정리할 거면 [codex_r31_tail_repetition_recalibration.md](/c:/Users/wjjo/Desktop/글도비/docs/blockguide/codex_r31_tail_repetition_recalibration.md)를 기준으로 [treatment-production-harness-v2.md](/c:/Users/wjjo/Desktop/글도비/docs/blockguide/treatment-production-harness-v2.md), [TF-BH1_block_harness_reinforcement.md](/c:/Users/wjjo/Desktop/글도비/docs/blockguide/TF-BH1_block_harness_reinforcement.md), [codex_chaebol_allowance_zero_failed_vs_retry_comparison_order.md](/c:/Users/wjjo/Desktop/글도비/docs/blockguide/codex_chaebol_allowance_zero_failed_vs_retry_comparison_order.md)을 순차 패치한다.
3. BI 계약까지 바로잡을 거면 `portfolio_history`를 실제 채울지, 아니면 비교 규칙에서 `financial_status.total_assets`를 정식 기준으로 낮출지 먼저 결정한다.
