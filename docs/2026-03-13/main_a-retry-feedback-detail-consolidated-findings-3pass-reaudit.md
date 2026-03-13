# main_a Retry Feedback Detail Consolidated Findings 3PASS Reaudit

> 작성일: 2026-03-13
> 상태: `executed / pass`
> 대상 문서: `main_a-retry-feedback-detail-consolidated-findings.md`
> 조사 모드: `static / read-only / source-report cross-check / targeted code-and-test verification / UTF-8 only`
> 추가 검증:
> - `pytest -q tests/test_stage2_context.py tests/test_feedback_system.py tests/test_prompt_builder.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage2_validation_pipeline.py tests/test_stage2_finalizer.py tests/test_arc_retry.py tests/test_stage3_orchestrator.py tests/test_stage4_context_builder.py` -> `338 passed in 6.12s`

## Executive Summary

통합본은 T1~T5 source ledger를 `13건`으로 정확히 재구성했고, severity 합계도 `P1 4 / P2 9`로 재현됐다. callback required/optional drift, rejection taxonomy 붕괴, writer/context helper dead-or-split path, Stage4 reverse feedback 의미 압축은 모두 현재 코드와 표적 테스트 기준으로 여전히 살아 있는 retry-feedback surface다.

이번 재감리에서 blocker는 없었다. source 문서 간 서술 형식 차이는 일부 있었지만 PASS chain, evidence field, duplicate status는 통합 SSOT를 막을 수준이 아니었다. 결론적으로 이 통합본은 retry-feedback remediation의 실행 기준 문서로 승격 가능하다.

---

## Pass 1 - 소스 문서 완전성 검증

### P1-1. T1~T5 결과 문서와 PASS 요약은 모두 존재한다

직접 근거:

- T1: `PASS1 4 -> PASS2 제거 2 -> 최종 2`
- T2: `PASS1 3 -> PASS2 제거 1 -> 최종 2`
- T3: `PASS1 4 -> PASS2 제거 1 -> 최종 3`
- T4: `PASS1 4 -> PASS2 제거 1 -> 최종 3`
- T5: `PASS1 5 -> PASS2 제거 2 -> 최종 3`

판정:

- `confirmed`

해석:

- 오더의 `T1~T5 문서 존재`와 `PASS1 -> PASS2 -> PASS3 요약` 조건은 충족된다.
- 일부 문서는 PASS 요약이 header가 아니라 본문 하단에 있었지만, source completeness 관점의 blocker는 아니다.

### P1-2. 통합본 합계 `13건`은 source ledger에서 재구성된다

직접 근거:

- T1: `P1 1 / P2 1`
- T2: `P2 2`
- T3: `P1 2 / P2 1`
- T4: `P1 1 / P2 2`
- T5: `P2 3`

판정:

- `confirmed`

해석:

- 재구성 결과는 `P0 0 / P1 4 / P2 9 / P3 0 / total 13`이다.
- cross-terminal dedupe로 삭제해야 할 동일 finding은 확인되지 않았다.

### P1-3. source 문서는 required evidence를 유지한다

직접 근거:

- 모든 source 문서에 코드 근거, downstream 영향 경계, 현재 테스트 근거 또는 테스트 부재, 기존 문서와의 중복 여부가 포함돼 있다.
- T2/T5는 `Finding Ledger`와 `Coverage Gap Log`, T1/T3/T4는 여기에 더해 실행 검증 또는 PASS 요약을 명시한다.

판정:

- `confirmed`

해석:

- 통합본은 source 문서의 필수 근거 필드를 잃지 않고 SSOT로 묶을 수 있다.
- bracket form heading이나 서술 위치 차이는 문서 포맷 편차일 뿐, ledger integrity를 손상시키지 않는다.

## Pass 2 - 상위 위험군 재검증

### P2-1. Stage2 callback required/optional drift는 현재 코드에서 직접 재확인된다

직접 근거:

- `modules/core/stage2_context.py:142-152`, `modules/core/stage2_context.py:246-256`은 retry-feedback callback bundle을 optional `None` 허용으로 바인딩한다.
- `modules/core/stage2_orchestrator.py:487-498`은 `analyze_rejection_pattern_v60(...)`를 hard-call한다.
- `modules/core/stage2_preflight.py:895-920`은 `Stage3->2` reverse feedback를 예외 흡수형으로 호출하고, `modules/core/stage2_preflight.py:924-944`은 `Stage4->2`를 explicit guard로 처리한다.
- 추가 검증 테스트 `338 passed`는 green이지만, 이 green 상태가 바로 `callback contract drift는 테스트로 닫히지 않았다`는 source 판단과 양립한다.

판정:

- `confirmed`

해석:

- `MRF-T1-001`, `MRF-T1-002`, `MRF-T4-002`, `MRF-T5-001`은 여전히 같은 bundle 안에서 required/optional semantics가 분열된 상태로 남아 있다.
- 즉시 장애 surface와 silent degradation surface가 함께 존재한다는 통합본의 상위 위험군 분류는 타당하다.

### P2-2. Rejection taxonomy와 writer/context helper drift도 재확인된다

직접 근거:

- `main_a.py:776-861`은 repeated reject triage, normalization bucket, fix guide를 담당한다.
- `modules/core/stage2_finalizer.py:1690-1697`은 실제 Stage2 history에 `specific_issue` 없이 minimal reason payload만 저장한다.
- `modules/core/prompt_builder.py:486-524`, `modules/core/prompt_builder.py:549-726`, `modules/core/prompt_builder.py:732-796`은 writer guidance와 arc context helper를 유지하지만, `modules/core/stage4_context_builder.py:2035-2592`와 `modules/core/stage4_orchestrator.py` 경로에서는 live writer prompt wiring이 닫히지 않는다.
- `tests/test_feedback_system.py`, `tests/test_prompt_builder.py`, `tests/test_stage4_context_builder.py`를 포함한 재검증 스위트는 모두 green이었다.

판정:

- `confirmed`

해석:

- `MRF-T2-01`, `MRF-T2-02`, `MRF-T3-01`, `MRF-T3-02`, `MRF-T3-03`, `MRF-T5-002`, `MRF-T5-003`은 pure helper 존재 여부와 별개로 live contract drift라는 점이 유지된다.
- 현재 테스트 green은 helper 존재/출력 단위는 보장하지만, helper가 실제 consumer graph에서 같은 의미를 유지하는지는 잠그지 못한다.

### P2-3. Cross-stage reverse feedback chain의 의미 압축도 그대로 남아 있다

직접 근거:

- `modules/core/stage3_context.py:10-13`, `modules/core/stage3_context.py:16-42`, `modules/core/stage3_context.py:95-119`에는 `Stage4->3` helper slot이 없다.
- 실제 Stage4 -> Stage3 escalation은 `modules/core/stage4_orchestrator.py:1033-1149`의 별도 advisory 로직으로 우회된다.
- `modules/core/pass_rate_monitor.py:478-533`은 Stage4 reject history를 `difficulty / avg_attempts / hard_episodes` 요약으로 압축한다.
- `modules/core/stage2_preflight.py:922-944`는 그 난이도 dict만 `generate_reverse_feedback_stage4_to_2()`에 전달한다.
- 관련 테스트를 포함한 재검증 스위트는 green이었다.

판정:

- `confirmed`

해석:

- `MRF-T4-001`과 `MRF-T4-003`의 핵심은 “helper가 있느냐”가 아니라 “같은 실패 원인이 같은 의미로 다음 stage에 전달되느냐”다.
- 현재 live chain은 Stage4 semantics를 Stage3/Stage2에 SSOT로 보존하지 못한다는 통합 결론이 유지된다.

## Pass 3 - 통합 SSOT 승격 판정

### P3-1. 통합본은 retry-feedback remediation SSOT로 승격 가능하다

직접 근거:

- source 문서 5개와 통합 ledger `13건`이 모두 재구성 가능하다.
- 상위 위험군이 현재 코드와 표적 테스트 재실행에서 다시 확인됐다.
- grand total과 severity 합계에 재현 불가 구간이 없다.

판정:

- `pass`

해석:

- 이 통합본은 template 단계가 아니라 실제 remediation 우선순위를 정할 수 있는 실행 기준 문서다.
- 별도 blocker 없이 SSOT 승격이 가능하다.

### P3-2. coverage gap은 남아 있지만 SSOT 승격 blocker는 아니다

직접 근거:

- source 문서들은 공통적으로 callback missing branch, app-bound context path, reverse feedback semantic preservation의 regression 부재를 지적한다.
- 그러나 각 항목은 코드 근거와 현재 테스트 공백을 함께 고정하고 있어 “증거 부족”이 아니라 “회귀망 부족” 문제로 정리된다.

판정:

- `confirmed`

해석:

- 다음 단계는 추가 조사보다 remediation + regression test 설계다.
- retry-feedback remediation order를 별도로 만드는 것이 자연스럽다.

## 보정 로그

| 항목 | 상태 | 메모 |
|------|------|------|
| cross-terminal dedupe | none | 삭제된 finding 없음 |
| source PASS summary 위치 편차 | noted | 일부 문서는 header 대신 본문 하단 요약을 사용하지만 blocker 아님 |
| T4 bracket form heading ID | noted | 통합 ledger에서는 plain code token으로만 표기 |

## 최종 판정

- 최종 상태: `pass`
- 통합본 SSOT 승격: `가능`
- blocker: `없음`
- 후속 권장: `Stage2 callback required/optional 정렬 -> rejection taxonomy/detail 복구 -> writer/context helper live wiring 정리 -> Stage4 reverse feedback semantic preservation` 순으로 remediation 문서를 작성
