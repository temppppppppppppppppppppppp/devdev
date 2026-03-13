# main_a Facade Shim Detail Consolidated Findings 3PASS Reaudit

> 작성일: 2026-03-13
> 상태: `executed / pass`
> 대상 문서: `main_a-facade-shim-detail-consolidated-findings.md`
> 조사 모드: `static / read-only / source-report cross-check / targeted code-and-test verification / UTF-8 only`
> 추가 검증:
> - `pytest -q tests/test_stage2_pipeline.py tests/test_stage2_validation_pipeline.py tests/test_state_service.py tests/test_stage3_orchestrator.py tests/test_stage4_orchestrator.py tests/test_ui_service.py tests/test_protocols_services.py tests/test_audit_service.py tests/test_validation_orchestrator_soft_failure.py tests/test_stage4_interview_round.py tests/test_stage4_cv_context.py` -> `374 passed in 58.91s`

## Executive Summary

통합본은 T1~T5 source ledger를 `12건`으로 정확히 재구성했고, severity 합계도 `P1 4 / P2 5 / P3 3`으로 일치한다. validation/audit facade miswiring, false-pass semantics drift, dormant or bypassed facade surface, operator-facing observability drift는 모두 현재 코드와 표적 테스트에서 다시 확인됐다.

이번 재감리에서 blocker는 없었다. 특히 T2/T3/T5가 지적한 “green test 뒤에 숨는 facade contract drift”는 재검증에서도 그대로 유지됐다. 즉 테스트가 많이 통과한다는 사실이 오히려 facade shim SSOT 필요성을 강화한다.

---

## Pass 1 - 소스 문서 완전성 검증

### P1-1. T1~T5 결과 문서와 PASS 요약은 모두 존재한다

직접 근거:

- T1: `PASS1 4 -> PASS2 제거 2 -> 최종 2`
- T2: `PASS1 5 -> PASS2 제거 2 -> 최종 3`
- T3: `PASS1 6 -> PASS2 제거 3 -> 최종 3`
- T4: `PASS1 4 -> PASS2 제거 2 -> 최종 2`
- T5: `PASS1 5 -> PASS2 제거 3 -> 최종 2`

판정:

- `confirmed`

해석:

- 오더의 `T1~T5 결과 문서`, `PASS 요약`, `finding 8필드` 요구사항은 충족된다.
- source 문서들은 template 상태가 아니고 모두 PASS3 수준으로 정리돼 있다.

### P1-2. 통합본 합계 `12건`은 source ledger에서 재구성된다

직접 근거:

- T1: `P1 1 / P2 1`
- T2: `P1 1 / P2 1 / P3 1`
- T3: `P1 1 / P2 1 / P3 1`
- T4: `P1 1 / P3 1`
- T5: `P2 2`

판정:

- `confirmed`

해석:

- 재구성 결과는 `P0 0 / P1 4 / P2 5 / P3 3 / total 12`다.
- cross-terminal dedupe가 필요한 exact duplicate는 확인되지 않았다.

### P1-3. dormant facade와 regression blind spot도 통합 ledger에 포함된다

직접 근거:

- T2는 runtime consumer가 없는 dormant shim set을 retained `P3`로 남겼다.
- T5는 protocol/test green 뒤에 남는 tagged callback 및 soft-failure relay blind spot을 retained `P2`로 남겼다.

판정:

- `confirmed`

해석:

- 이 통합본은 live defect만 모은 것이 아니라, facade shim 특유의 “API 표면은 있는데 runtime/test contract가 닫히지 않은 상태”까지 함께 기록한다.
- facade remediation SSOT로 쓰기에 적절한 구성이다.

## Pass 2 - 상위 위험군 재검증

### P2-1. validation / audit facade miswiring은 현재 코드에서 직접 재확인된다

직접 근거:

- `main_a.py:2780-2794`는 `_validate_arc_data_fields()`, `_validate_arc_mapping()`, `_validate_arc_integrity()`, `_validate_blueprint_integrity()` 등 facade shim을 export한다.
- `modules/core/stage2_context.py:46-100`, `modules/core/stage2_context.py:132-156`, `modules/core/stage2_context.py:210-258`에는 `validate_arc_data_fields` slot이 없다.
- `modules/core/stage2_finalizer.py:905-916`은 해당 repair hook가 있을 때만 호출한다.
- `main_a.py:2719-2729`, `main_a.py:3432-3461`, `modules/core/stage4_orchestrator.py:1524-1549`는 Stage4 completion audit callback source가 `ctx`와 `app`로 갈라져 있음을 유지한다.
- `modules/protocols/app_services.py:53-62`와 `tests/test_protocols_services.py:92-119`는 tagged audit summary contract를 끝까지 잠그지 못한다.
- 추가 검증 테스트 `374 passed`는 green이었다.

판정:

- `confirmed`

해석:

- `MFS-T2-001`, `MFS-T2-002`, `MFS-T3-02`, `MFS-T5-001`은 모두 facade export와 실제 consumer graph 사이의 miswiring이라는 통합 위험군으로 유지된다.
- 특히 bound-method rename/signature drift를 현재 테스트가 충분히 차단하지 못한다는 판단이 재확인된다.

### P2-2. false-pass / degraded semantics drift도 유지된다

직접 근거:

- `modules/core/stage2_validation_pipeline.py:1095-1134`는 flow analyzer runtime exception을 legacy fallback이 아니라 `{"status": "PASS", "fallback": True}`로 흡수한다.
- `modules/core/stage3_orchestrator.py:585-598`은 Stage3 루프 종료 사유와 무관하게 `stage3_complete` summary를 기록한다.
- `modules/validation/validation_orchestrator.py:276-305`, `modules/validation/validation_orchestrator.py:430-447`, `modules/validation/validation_orchestrator.py:1211-1231`은 soft-failure relay helper를 가지지만, source T5 문서가 지적한 실제 sync/parallel exception path blind spot은 그대로 남아 있다.
- 관련 테스트 재실행은 모두 green이었다.

판정:

- `confirmed`

해석:

- `MFS-T1-002`, `MFS-T3-01`, `MFS-T5-002`는 모두 “실패가 hard fail이 아니라 성공 또는 관측성 약화로 흡수되는” 계열의 facade risk다.
- 통합본이 이들을 같은 remediation wave로 묶은 판단은 타당하다.

### P2-3. dormant/bypassed facade와 operator-facing observability drift도 재확인된다

직접 근거:

- `main_a.py:2666-2691`, `main_a.py:2784-2786`의 여러 shim은 `modules/` consumer graph에서 호출되지 않고 service unit test 주변에만 남아 있다.
- `modules/core/stage4_interview_round.py:3477-3485`, `modules/core/stage4_interview_round.py:2110`, `modules/validation/consistency_validator.py:412-423` 조합은 Stage4 live path가 NPC facade를 우회하고 `npc_profiles={}`로 attitude check를 PASS 처리함을 유지한다.
- `modules/core/services/ui_service.py:86-101`은 `10권 전략 설계 상업성 성적표` 타이틀을 고정한다.
- `modules/core/stage3_orchestrator.py:1479-1481`에는 unresolved continuity pin mojibake log literal이 남아 있다.

판정:

- `confirmed`

해석:

- `MFS-T2-003`, `MFS-T4-001`, `MFS-T4-002`, `MFS-T3-03`은 facade의 표면과 실제 operator/runtime 경험이 어긋나는 cluster로 유지된다.
- P3 항목이더라도 observability SSOT 관점에서는 무시할 수 없는 상태다.

## Pass 3 - 통합 SSOT 승격 판정

### P3-1. 통합본은 facade shim remediation SSOT로 승격 가능하다

직접 근거:

- source 문서 5개와 통합 ledger `12건`이 재구성 가능하다.
- 상위 위험군이 현재 코드와 표적 테스트 재실행에서 다시 확인됐다.
- grand total과 severity 합계에 재현 불가 구간이 없다.

판정:

- `pass`

해석:

- 이 통합본은 facade shim surface를 정리하는 remediation 기준 문서로 사용할 수 있다.
- 별도 normalization blocker는 없다.

### P3-2. green test가 많아도 facade contract SSOT 필요성은 줄지 않는다

직접 근거:

- 이번 재감리에서 `374 passed`가 나왔지만, source finding 다수가 바로 “green test가 facade drift를 가린다”는 성격을 가진다.
- 재검증 결과도 그 구조를 뒤집지 못했다.

판정:

- `confirmed`

해석:

- 이 트랙의 다음 단계는 추가 broad test 실행보다, real bound-method fixture를 쓰는 focused regression과 facade surface 축소/정렬이다.

## 보정 로그

| 항목 | 상태 | 메모 |
|------|------|------|
| cross-terminal dedupe | none | 삭제된 finding 없음 |
| tagged audit summary contract | rechecked | protocol/context green 뒤 blind spot 유지 |
| mojibake log observation | retained | UTF-8 파싱은 가능하지만 log literal 품질 이슈는 `MFS-T3-03`로 유지 |

## 최종 판정

- 최종 상태: `pass`
- 통합본 SSOT 승격: `가능`
- blocker: `없음`
- 후속 권장: `validation/audit facade wiring 정렬 -> false-pass semantics 차단 -> dormant facade 축소 -> operator-facing observability 정리` 순으로 remediation 문서를 작성
