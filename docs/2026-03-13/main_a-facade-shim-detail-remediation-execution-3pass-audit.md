# main_a Facade Shim Detail Remediation Execution 3PASS Audit

> 작성일: 2026-03-13
> 대상 문서: `main_a-facade-shim-detail-remediation-execution-ssot.md`
> 판정 시점: `current workspace @ 2026-03-13`
> 상태: `valid / FS-E1 executed`

## Executive Summary

대상 실행 SSOT는 현재 코드베이스 기준으로 여전히 유효하다. 문서가 전제한 상위 remediation 축 5개 중 `FS-E2`~`FS-E5`의 핵심 근거가 아직 코드에 남아 있고, 이번 턴에서는 문서 순서대로 `FS-E1`만 실행해 Stage2 facade threshold drift와 flow-guard fallback semantics를 정렬했다.

실행 SSOT 자체를 폐기하거나 재작성해야 할 blocker는 확인되지 않았다. 따라서 다음 기본 단위는 그대로 `FS-E2. State-Service Validation Shim Wiring`이다.

## Pass 1 - 문서 계약 유효성

### P1-1. 패키지 분해와 우선순위는 아직 현재 코드 구조와 맞는다

확인 근거:

- `modules/core/stage2_context.py`에는 여전히 `validate_arc_data_fields` slot/binding이 없다.
- `modules/core/stage3_orchestrator.py`는 Stage3 종료 사유와 무관하게 `stage3_complete` summary를 기록한다.
- `modules/core/stage4_interview_round.py`의 `_build_cv_context()`는 `npc_profiles`를 빈 dict로 시작한다.
- `modules/core/services/ui_service.py`는 여전히 `10권 전략 설계 상업성 성적표` 타이틀을 고정한다.

판정:

- `confirmed`

해석:

- 문서가 정의한 `FS-E2`~`FS-E5`는 아직 실제 remediation 대상이다.
- 따라서 실행 SSOT의 package map과 권장 순서는 현재도 유효하다.

### P1-2. `FS-E1`은 audit 시점 기준 미해결이었고, 이번 턴 수정 대상으로 적절했다

확인 근거:

- audit 시작 시 `main_a.py`, `modules/core/stage2_orchestrator.py`, `modules/core/stage2_validation_pipeline.py`의 duplicate threshold 기본값이 서로 달랐다.
- audit 시작 시 analyzer runtime exception branch는 legacy fallback이 아니라 `{"status": "PASS", "fallback": True}`를 반환했다.

판정:

- `confirmed`

해석:

- 실행 SSOT가 `FS-E1`을 첫 패키지로 둔 우선순위는 여전히 타당했다.

## Pass 2 - 코드 / 테스트 교차 검증

### P2-1. 실행 SSOT의 “green test 뒤 facade drift” 판단은 현재도 성립한다

실행 검증:

- `pytest -q tests/test_stage2_pipeline.py tests/test_stage2_validation_pipeline.py tests/test_stage2_context.py tests/test_stage2_finalizer.py tests/test_stage3_orchestrator.py tests/test_stage4_orchestrator.py tests/test_protocols_services.py tests/test_validation_orchestrator_soft_failure.py tests/test_stage4_cv_context.py tests/test_ui_service.py`
- 결과: `308 passed`

판정:

- `confirmed`

해석:

- broad regression이 green이어도 `FS-E2`~`FS-E5`의 facade/document drift는 여전히 남아 있었다.
- 따라서 실행 SSOT의 핵심 전제는 유지된다.

### P2-2. 이번 턴 `FS-E1` 수정은 문서 acceptance와 일치한다

실행 검증:

- `pytest -q tests/test_stage2_pipeline.py tests/test_stage2_validation_pipeline.py tests/test_main_a_stage_entry_contracts.py`
- 결과: `111 passed`
- `pytest -q tests/test_stage2_pipeline.py tests/test_stage2_validation_pipeline.py tests/test_stage2_context.py tests/test_stage2_finalizer.py tests/test_stage3_orchestrator.py tests/test_stage4_orchestrator.py tests/test_protocols_services.py tests/test_validation_orchestrator_soft_failure.py tests/test_stage4_cv_context.py tests/test_ui_service.py tests/test_main_a_stage_entry_contracts.py`
- 결과: `317 passed`

수정 결과:

- Stage2 duplicate threshold는 shared contract 상수로 통일됐다.
- facade / orchestrator / pipeline이 동일 기본 threshold를 본다.
- analyzer import failure와 runtime exception이 모두 legacy flow guard fallback으로 재평가된다.
- 관련 회귀 테스트가 추가되어 near-duplicate band와 fallback semantics를 잠근다.

판정:

- `pass`

## Pass 3 - 최종 판정

### P3-1. 실행 SSOT는 현재도 유효하다

판정:

- `valid`

근거:

- 남은 remediation package가 아직 실코드에 존재한다.
- package 순서가 현재 위험도와 맞는다.
- 이번 턴 수행한 `FS-E1`도 문서 정의대로 닫혔다.

### P3-2. 다음 단위는 `FS-E2`다

판정:

- `ready`

다음 기본 행동:

1. `Stage2Context` / `Stage2Finalizer` / `Stage3Context` / `Stage4Context`의 live binding을 다시 맞춘다.
2. `validate_arc_data_fields` repair hook를 real bound-method seam에서 잠근다.
3. dormant shim을 제거하거나 reserved surface로 명시한다.

## 최종 결론

- 실행 SSOT 현재 유효성: `유효`
- 이번 턴 완료 단위: `FS-E1`
- blocker: `없음`
- 다음 권장 단위: `FS-E2`
