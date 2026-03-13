# main_a Retry Feedback Detail Consolidated Findings

> 작성일: 2026-03-13
> 상태: `executed / consolidated`
> 범위: `MRF-T1` ~ `MRF-T5` 통합본
> 기준 오더: `main_a-retry-feedback-detail-full-survey-audit-order.md`
> 확정 결과: `총 13건 (P0 0 / P1 4 / P2 9 / P3 0)`

이 문서는 2026-03-13 기준 retry-feedback 트랙의 T1~T5 PASS3 결과를 재구성한 통합 SSOT다. 교차 터미널 중복 제거로 삭제한 finding은 없었고, T4 원문이 heading에서 bracket form ID를 쓴 부분은 통합 ledger에서 일반 코드 토큰(`MRF-T4-001`)으로만 정규화했다. finding 내용 자체는 바꾸지 않았다.

---

## 터미널별 상태

| 터미널 | 소스 상태 | 문서 | PASS 요약 | 최종 건수 |
|--------|-----------|------|-----------|-----------|
| T1 | `PASS3 completed` | `MRF-T1-stage2-callback-binding-findings.md` | `PASS1 4 -> PASS2 제거 2 -> 최종 2` | 2 |
| T2 | `executed` | `MRF-T2-rejection-analysis-intensity-findings.md` | `PASS1 3 -> PASS2 제거 1 -> 최종 2` | 2 |
| T3 | `executed / PASS3 finalized` | `MRF-T3-prompt-guidance-context-findings.md` | `PASS1 4 -> PASS2 제거 1 -> 최종 3` | 3 |
| T4 | `executed / PASS3 completed` | `MRF-T4-cross-stage-reverse-feedback-findings.md` | `PASS1 4 -> PASS2 제거 1 -> 최종 3` | 3 |
| T5 | `executed` | `MRF-T5-consumer-tests-regression-findings.md` | `PASS1 5 -> PASS2 제거 2 -> 최종 3` | 3 |

## Severity Summary

| Severity | T1 | T2 | T3 | T4 | T5 | 확정 |
|----------|----|----|----|----|----|------|
| P0 | 0 | 0 | 0 | 0 | 0 | 0 |
| P1 | 1 | 0 | 2 | 1 | 0 | 4 |
| P2 | 1 | 2 | 1 | 2 | 3 | 9 |
| P3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 합계 | 2 | 2 | 3 | 3 | 3 | 13 |

## 상위 위험군

| 위험군 | 포함 finding | 의미 |
|--------|--------------|------|
| Stage2 callback required/optional drift | `MRF-T1-001`, `MRF-T1-002`, `MRF-T4-002`, `MRF-T5-001` | 같은 retry-feedback bundle이 어떤 경로에서는 required hard-call, 어떤 경로에서는 silent degradation으로 처리돼 callback contract가 한 곳에 잠겨 있지 않다 |
| Rejection semantics / normalization loss | `MRF-T2-01`, `MRF-T2-02`, `MRF-T5-003` | repeated reject triage가 `specific_issue` detail과 자유서술 reason taxonomy를 잃으면서 수정 가이드가 `기타`/무가이드로 붕괴한다 |
| Guidance / context helper dead-or-split path | `MRF-T3-01`, `MRF-T3-02`, `MRF-T3-03`, `MRF-T5-002` | writer guidance 계열 helper는 live path에서 죽어 있거나, 같은 arc context family 안에서도 no-op 인자와 energy 계산 drift가 존재한다 |
| Cross-stage reverse translation drift | `MRF-T4-001`, `MRF-T4-003` | Stage4 reject semantics가 Stage3/Stage2로 번역될 때 helper wiring이 빠지거나 difficulty-only 요약으로 과압축돼 같은 실패 원인이 같은 의미로 전달되지 않는다 |

## 취합 메모

- cross-terminal dedupe로 삭제한 항목은 없었다.
- `MRF-T1-001`과 `MRF-T4-002`는 둘 다 optional callback 문제지만, 전자는 retry loop hard crash surface이고 후자는 silent drop surface라 분리 유지했다.
- `MRF-T3-02`와 `MRF-T5-002`도 둘 다 `generate_arc_context_v60()` 계열을 다루지만, 하나는 helper contract 자체의 no-op 인자 문제이고 다른 하나는 app-bound live path 미검증 문제라 별개로 유지했다.
- `MRF-T2-01`과 `MRF-T5-003` 역시 하나는 live detail field dead branch, 다른 하나는 그 triage helper 전체의 regression blind spot이라 중복으로 처리하지 않았다.

## 통합 Ledger

| ID | 터미널 | Sev | 주제 | duplicate status |
|----|--------|-----|------|------------------|
| `MRF-T1-001` | T1 | `P1` | `analyze_rejection_pattern_v60`는 optional binding인데 Stage 2 retry loop는 required처럼 호출한다 | `related-but-new-callback-surface` |
| `MRF-T1-002` | T1 | `P2` | retry-feedback callback bundle이 consumer마다 다른 fallback 규약을 가져 누락 시 조용한 기능 축소를 만든다 | `related-but-new-callback-surface` |
| `MRF-T2-01` | T2 | `P2` | repeated reject 분석의 `specific_issue` 상세 블록이 현재 Stage2 history 경로에서는 사실상 dead field다 | `none` |
| `MRF-T2-02` | T2 | `P2` | 자유서술형 REJECT reason이 좁은 정규화 버킷 밖으로 떨어지면 반복 패턴 분석이 `기타`와 무가이드로 수렴한다 | `none` |
| `MRF-T3-01` | T3 | `P1` | retry / writer guidance helper 다수가 export만 되고 실제 writer prompt 경로에는 주입되지 않는다 | `none` |
| `MRF-T3-02` | T3 | `P2` | `generate_arc_context_v60()`는 `current_arc_no`를 시그니처로 받지만 구현은 인자를 완전히 무시한다 | `related-but-new-callback-surface` |
| `MRF-T3-03` | T3 | `P1` | `build_minimal_arc_context()`가 full arc context와 다른 내공 시작값을 주입할 수 있다 | `related-but-new-callback-surface` |
| `MRF-T4-001` | T4 | `P1` | `Stage4->3` reverse feedback helper는 존재하지만 live Stage3 consumer에는 연결되지 않는다 | `related-but-new-callback-surface` |
| `MRF-T4-002` | T4 | `P2` | `Stage3->2` reverse feedback callback은 optional contract가 일관되지 않아 누락 시 audit-only silent drop이 된다 | `related-but-new-callback-surface` |
| `MRF-T4-003` | T4 | `P2` | active `Stage4->2` chain은 reject semantics를 difficulty-only 요약으로 압축해 의미를 잃는다 | `related-but-new-callback-surface` |
| `MRF-T5-001` | T5 | `P2` | `Stage2Context.from_app()` retry-feedback callback export 면적 대비 test pinning 범위가 너무 좁다 | `related-but-new-callback-surface` |
| `MRF-T5-002` | T5 | `P2` | `generate_arc_context_v60`의 실제 app-bound 경로가 unit/e2e에서 우회된다 | `related-but-new-callback-surface` |
| `MRF-T5-003` | T5 | `P2` | `_analyze_rejection_pattern_v60()` 계열 repeated reject triage helper에 직접 테스트가 없다 | `none` |

## 결론

- 이번 트랙의 통합 baseline은 `13 confirmed findings`다.
- 우선 remediation 순서는 `Stage2 callback required/optional 정렬 -> rejection taxonomy/detail 복구 -> writer/context helper live wiring 정리 -> Stage4→3/2 reverse feedback 의미 보존`이 적절하다.
- 최종 SSOT 승격 여부는 `main_a-retry-feedback-detail-consolidated-findings-3pass-reaudit.md` 기준으로 판단한다.
