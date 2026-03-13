# main_a Persistence Narrative Detail Consolidated Findings 3PASS Reaudit

> 작성일: 2026-03-13
> 상태: `executed / pass`
> 대상 문서: `main_a-persistence-narrative-detail-consolidated-findings.md`
> 조사 모드: `static / read-only / source-report cross-check / targeted code-and-test verification / UTF-8 only`
> 추가 검증:
> - `pytest -q tests/test_project_service.py tests/property/test_db_rollback_props.py tests/chaos/test_partial_commit.py tests/test_stage01_helpers.py tests/test_stage01_fixes.py tests/test_stage3_orchestrator.py tests/test_stage4_context.py tests/test_stage4_orchestrator.py tests/test_sweep23.py tests/test_sweep36.py` -> `238 passed in 8.28s`

## Executive Summary

통합본은 T1~T5 source ledger를 `16건`으로 정확히 재구성했고, severity 합계도 `P1 5 / P2 10 / P3 1`로 일치한다. protagonist/episode mapping source drift, preset/commit success semantics split, Stage01 hidden coupling, narrative summary lifecycle drift는 모두 현재 코드와 표적 테스트에서 다시 확인됐다.

이번 재감리의 blocker는 없다. 다만 source 자체가 남겨 둔 coverage gap, 특히 `safe_commit_async` smoke skip과 Stage4 narrative summary lifecycle regression 공백은 여전히 살아 있다. 그 공백은 이미 `MPN-T5-003`, `MPN-T4-*` finding으로 ledger에 승격돼 있어 SSOT 승격을 막지는 않는다.

---

## Pass 1 - 소스 문서 완전성 검증

### P1-1. T1~T5 결과 문서와 PASS 요약은 모두 존재한다

직접 근거:

- T1: `PASS1 5 -> PASS2 제거 3 -> 최종 2`
- T2: `PASS1 6 -> PASS2 제거 2 -> 최종 4`
- T3: `PASS1 4 -> PASS2 제거 1 -> 최종 3`
- T4: `PASS1 4 -> PASS2 제거 1 -> 최종 3`
- T5: `PASS1 6 -> PASS2 제거 2 -> 최종 4`

판정:

- `confirmed`

해석:

- 오더의 `T1~T5 문서 존재`, `PASS1 -> PASS2 -> PASS3 요약`, `required evidence field` 요구사항은 충족된다.
- source 문서 상태 표기는 `3pass executed`, `completed`, `PASS3 finalized`처럼 조금씩 다르지만, 모두 template 상태는 아니다.

### P1-2. 통합본 합계 `16건`은 source ledger에서 재구성된다

직접 근거:

- T1: `P2 2`
- T2: `P1 2 / P2 2`
- T3: `P1 1 / P2 2`
- T4: `P1 1 / P2 2`
- T5: `P1 1 / P2 2 / P3 1`

판정:

- `confirmed`

해석:

- 재구성 결과는 `P0 0 / P1 5 / P2 10 / P3 1 / total 16`이다.
- cross-terminal dedupe로 삭제해야 할 exact duplicate finding은 확인되지 않았다.

### P1-3. shared helper와 regression surface가 모두 source ledger에 남아 있다

직접 근거:

- T1/T2/T3/T4는 helper contract 자체의 live drift를 다루고, T5는 consumer/test/legacy contract blind spot을 별도 surface로 다룬다.
- `MPN-T2-04`와 `MPN-T5-001`, `MPN-T1-002`와 `MPN-T5-002`처럼 같은 테마를 다루는 쌍도 code defect와 regression blind spot으로 역할이 분리돼 있다.

판정:

- `confirmed`

해석:

- 통합본이 helper bug만 모은 것도 아니고, test gap만 모은 것도 아니다.
- remediation SSOT로 쓰기에 필요한 “live defect + regression blind spot” 구성이 유지된다.

## Pass 2 - 상위 위험군 재검증

### P2-1. protagonist / episode / arc SSOT split는 현재 코드에서 직접 재확인된다

직접 근거:

- `main_a.py:2050-2060`은 `_get_protagonist_name()`이 live `master_bible` 대신 DB anchor를 우선 읽는다.
- `main_a.py:2079-2088`과 `modules/domain/agents/state_extractor.py:702` 조합은 extracted protagonist row 중복 삽입 가능성을 유지한다.
- `main_a.py:2524-2529`는 `_calculate_arc_from_episode()`의 5화 고정 공식을 유지한다.
- `modules/core/constants.py:335-340`은 중앙 SSOT를 `EPISODES_PER_ARC = 4`로 둔다.
- `modules/core/stage2_orchestrator.py:219-225`는 manuscript smart skip 경계에서 `calculate_arc_from_episode` nullable slot을 unguarded call한다.
- 추가 검증 테스트 `238 passed`는 green이지만, source 문서가 지적한 mapping drift를 닫지 못한다.

판정:

- `confirmed`

해석:

- `MPN-T2-01` ~ `MPN-T2-04`, `MPN-T5-001`이 묶인 protagonist/episode risk cluster는 통합본 그대로 유지된다.
- 특히 5화 고정 helper와 4화 시스템의 충돌은 code + regression 양쪽에서 동시에 살아 있다.

### P2-2. shared persistence / commit success semantics split도 그대로 남아 있다

직접 근거:

- `main_a.py:363-399`, `main_a.py:1000-1009`은 `_restore_preset_registry()` no-data/failure 시 stale preset clear를 하지 않는다.
- `main_a.py:1226-1249`는 cache persistence 경로에서 `save_anchor()`와 `_safe_commit()`의 bool 반환을 무시한다.
- `modules/core/stage2_finalizer.py:1091-1094`, `modules/core/stage3_orchestrator.py:1503-1507`, `modules/core/stage4_orchestrator.py:1539-1549`은 같은 commit helper 계열을 stage마다 다르게 소비한다.
- `tests/e2e/test_l3_stage2_realproject.py`와 `tests/e2e/test_l3_golden_route.py`의 skip 기반 smoke 공백은 source T5 문서가 직접 고정했고, 이번 재감리의 재실행 묶음에는 포함되지 않았다.

판정:

- `confirmed`

해석:

- `MPN-T1-001`, `MPN-T1-002`, `MPN-T5-002`, `MPN-T5-003`은 persistence helper 의미가 stage/test마다 다르다는 통합 판단을 유지한다.
- skip-based smoke gap은 blocker가 아니라 이미 retained finding의 일부다.

### P2-3. Stage01 hidden coupling과 Stage4 narrative summary lifecycle drift도 재확인된다

직접 근거:

- `main_a.py:2620-2647`과 `modules/core/stage01_helpers.py:768-813`은 비문자열 `strategy_doc` fail-open과 hidden private validator coupling을 유지한다.
- `tests/test_stage01_helpers.py:529-544`는 success path에서 retry wrapper를 mock해 실제 boundary callback chain을 우회한다.
- `main_a.py:3194-3321`, `modules/core/stage4_context_builder.py:2142-2153`, `modules/core/stage4_context_builder.py:2447-2449`은 narrative summary range/loader/injection contract를 유지한다.
- `modules/core/services/project_service.py:102-103,162,222,304,369`과 `modules/core/db_manager.py:2283-2333,2494-2509` 조합은 rollback/reset 이후 narrative summary anchor lifecycle 공백을 그대로 남긴다.
- 재검증 테스트 `238 passed`는 green이었다.

판정:

- `confirmed`

해석:

- `MPN-T3-001` ~ `MPN-T3-003`, `MPN-T4-001` ~ `MPN-T4-003`, `MPN-T5-004`는 helper coupling과 regression blind spot이 결합된 상태로 남아 있다.
- summary lifecycle과 Stage01 boundary semantics는 별도 remediation 트랙으로 다룰 가치가 있다.

## Pass 3 - 통합 SSOT 승격 판정

### P3-1. 통합본은 shared persistence / narrative helper SSOT로 승격 가능하다

직접 근거:

- source 문서 5개와 통합 ledger `16건`이 재구성 가능하다.
- 상위 위험군이 현재 코드와 표적 테스트 재실행에서 다시 확인됐다.
- grand total과 severity 합계에 재현 불가 구간이 없다.

판정:

- `pass`

해석:

- 이 통합본은 helper remediation 순서를 정하는 실행 기준 문서로 사용 가능하다.
- 별도 normalization blocker는 없다.

### P3-2. skip-based smoke gap과 summary lifecycle gap은 residual risk이지 SSOT blocker가 아니다

직접 근거:

- `MPN-T5-003`이 e2e skip + wrong fixture contract를 retained finding으로 이미 고정한다.
- `MPN-T4-*`가 narrative summary lifecycle 공백을 retained finding으로 이미 고정한다.

판정:

- `confirmed`

해석:

- source 문서가 gap을 숨기지 않고 ledger로 끌어올렸기 때문에, 통합본은 오히려 현재 한계를 정직하게 드러내는 SSOT다.
- 다음 단계는 추가 조사보다 remediation + hermetic regression 보강이다.

## 보정 로그

| 항목 | 상태 | 메모 |
|------|------|------|
| cross-terminal dedupe | none | 삭제된 finding 없음 |
| source 상태 표기 편차 | noted | `3pass executed`, `completed`, `PASS3 finalized` 등 표현 차이만 존재 |
| Stage2 smoke skip residual risk | noted | blocker가 아니라 `MPN-T5-003` retained finding으로 유지 |

## 최종 판정

- 최종 상태: `pass`
- 통합본 SSOT 승격: `가능`
- blocker: `없음`
- 후속 권장: `protagonist/arc mapping SSOT 통일 -> preset/commit success semantics 정렬 -> Stage01 boundary helper 분리 -> narrative summary lifecycle 정리` 순으로 remediation 문서를 작성
