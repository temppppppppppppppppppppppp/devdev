# [MFS-T5] Protocol / Tests / Regression Findings

> 작성일: 2026-03-13
> 상태: `PASS 3 complete / confirmed`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-facade-shim-detail-full-survey-audit-order.md`
> 추가 검증 실행:
> - `pytest -q tests/test_protocols_services.py tests/test_audit_service.py tests/test_validation_orchestrator_soft_failure.py tests/test_stage3_orchestrator.py tests/test_stage4_context.py` -> `116 passed in 2.80s`

---

## 조사 범위

- `main_a.py` facade shim 중 `protocol / tests / regression surface`
- `modules/protocols/app_services.py`
- `modules/validation/validation_orchestrator.py`
- `tests/test_protocols_services.py`
- `tests/test_audit_service.py`
- `tests/test_validation_orchestrator_soft_failure.py`
- 관련 Stage2/3/4 context callback 테스트
- 기존 감리 문서 중 protocol/test drift 기결 항목

## 필수 근거

- `tests/test_validation_orchestrator_soft_failure.py`
- `tests/test_audit_service.py`
- `modules/protocols/app_services.py`
- `docs/2026-03-12/system-wide-full-survey-3pass-master-audit.md`

## PASS 기록

- PASS 1: 후보 5건 식별
  - `_write_audit_summary(tag)` facade callback blind spot
  - `ValidationOrchestrator` soft-failure fallback blind spot
  - `StateServiceProtocol` vs extracted `StateService` semantic drift
  - `AuditServiceProtocol.write_audit_summary` 시그니처 누락
  - `MockProject.arcs` setter 미검증
- PASS 2: 후보 3건 제거
  - `StateServiceProtocol` vs extracted `StateService` semantic drift는 `docs/2026-03-13/MCP-T5-control-contract-regression-findings.md`의 `MCP-T5-003`으로 이미 닫혀 있어 재오픈하지 않음
  - `AuditServiceProtocol.write_audit_summary` 시그니처 누락은 `docs/2026-03-13/OPUS-TF-T1-infrastructure-findings.md`의 `T1-25`로 이미 닫혀 있어 재오픈하지 않음
  - `MockProject.arcs` setter 미검증은 `docs/2026-03-13/OPUS-TF-T1-infrastructure-findings.md`의 `T1-28`로 이미 닫혀 있어 재오픈하지 않음
- PASS 3: 최종 2건 확정

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| MFS-T5-001 | P2 | confirmed | `main_a.py::_write_audit_summary`, `stage2_orchestrator.py`, `stage3_orchestrator.py`, `tests/test_protocols_services.py` | tagged audit summary를 요구하는 실제 facade contract를 현재 protocol/context 테스트가 잠그지 못한다 |
| MFS-T5-002 | P2 | confirmed | `validation_orchestrator.py::_report_soft_failure`, `validate()`, `validate_parallel_v59()` | soft-failure helper는 테스트되지만 실제 blocking failure 예외 경유 relay는 sync/parallel 모두 미검증이다 |

---

## Findings

### [MFS-T5-001] tagged audit summary facade contract가 green test 뒤에 숨는다

1. ID
- `MFS-T5-001`

2. Severity
- `P2`

3. 현상 요약
- 실제 consumer는 Stage 2/3 완료 시 `write_audit_summary("stage2_complete")`, `write_audit_summary("stage3_complete")`처럼 tagged callback 계약을 사용한다.
- `main_a.py` facade도 `_write_audit_summary(tag="snapshot") -> _audit_service.write_audit_summary(tag)`로 이 계약을 그대로 전달한다.
- 그런데 protocol/test 표면은 이 tagged contract를 잠그지 못한다.
- `AuditServiceProtocol` 적합성 테스트는 `write_audit_summary(self)`만 가진 `MockAudit`를 conforming으로 통과시키고, Stage2/3/4 context 테스트는 실제 bound facade를 실행하지 않고 `MagicMock` 또는 `None` 가드만 본다.
- 결과적으로 `_write_audit_summary()`가 tag를 누락하거나 잘못 바인딩돼도 현 회귀망은 초록으로 남을 수 있다.

4. 코드 근거
- 실제 facade delegate: `main_a.py:2719-2729`
- tagged consumer 호출: `modules/core/stage2_orchestrator.py:891-892`, `modules/core/stage3_orchestrator.py:596-597`
- 실제 구현체는 tag를 받음: `modules/core/services/audit_service.py:72-74`
- protocol은 무인자 summary로 모델링: `modules/protocols/app_services.py:53-62`
- protocol 테스트도 무인자 mock을 conforming으로 승인: `tests/test_protocols_services.py:92-119`
- Stage2 context 테스트는 callback identity만 확인: `tests/test_stage2_context.py:91-106`
- Stage3 테스트는 binding/None guard만 확인: `tests/test_stage3_orchestrator.py:923-925`, `tests/test_stage3_orchestrator.py:971-983`
- Stage4 context 테스트도 `MagicMock` flush만 확인: `tests/test_stage4_context.py:259-265`
- service 단위 테스트는 구현체 직접 호출만 확인: `tests/test_audit_service.py:81-89`, `tests/test_audit_service.py:109-117`

5. downstream 영향 경계
- Stage 2 완료 audit summary 기록
- Stage 3 완료 audit summary 기록
- `main_a.py` facade -> `AuditService` delegate 배선
- 향후 Stage4 또는 canary가 tagged summary를 재사용할 경우의 callback contract

6. 현재 테스트 근거 또는 테스트 부재
- 존재하는 테스트는 `AuditService` 구현체 자체와 callback 존재 여부는 검증한다.
- 그러나 `main_a.py`의 실제 bound facade 메서드가 Stage2/3 consumer에서 tag 인자를 끝까지 전달하는지는 검증하지 않는다.
- 이번 표적 실행에서도 `116 passed`였지만, 이 blind spot은 그대로 남았다.

7. 기존 문서와의 중복 여부
- `related-but-new-facade-surface`
- 기존 `T1-25`는 protocol 시그니처 누락 자체를 닫은 문서다.
- 이번 finding은 그보다 좁고 직접적인 `main_a.py` facade + Stage2/3 tagged callback regression surface가 테스트되지 않는다는 점을 별도로 확정한다.

8. 권장 후속 조치
- `main_a` 최소 host에 실제 `AuditService`를 연결하고, `Stage2Context.from_app()` 또는 `Stage3Context.from_app()`를 통해 `write_audit_summary("stage*_complete")`를 실제로 호출하는 focused regression test를 추가한다.
- `tests/test_protocols_services.py`의 `MockAudit.write_audit_summary()`도 `tag` 인자를 반영하거나, 해당 blind spot을 의도적으로 명시한 negative test를 분리한다.

### [MFS-T5-002] `ValidationOrchestrator` soft-failure regression net이 helper 직접 호출에서 멈춘다

1. ID
- `MFS-T5-002`

2. Severity
- `P2`

3. 현상 요약
- `ValidationOrchestrator`는 `FailureLearner.record_failure()`가 예외를 던질 때 `_report_soft_failure()`로 degraded audit/log relay를 남기도록 설계돼 있다.
- 이 경로는 sync validate와 parallel validate 양쪽에 별도 분기까지 있다.
- 하지만 현재 테스트는 helper `_report_soft_failure()`를 직접 호출해 relay 형식만 확인할 뿐, 실제 `validate()`/`validate_parallel_v59()`에서 blocking advisory 수집 도중 예외가 났을 때 그 relay가 살아 있는지는 검증하지 않는다.
- integration 테스트도 `record_failure.assert_called()` happy path까지만 보고 예외 경로는 건드리지 않는다.
- 결과적으로 soft-failure relay, log_dir resolution, parallel branch message/extra payload drift가 실제 실행 경로에서 깨져도 현 스위트는 놓칠 수 있다.

4. 코드 근거
- sync blocking advisory exception path: `modules/validation/validation_orchestrator.py:430-447`
- parallel blocking advisory exception path: `modules/validation/validation_orchestrator.py:1211-1231`
- helper relay 구현: `modules/validation/validation_orchestrator.py:276-305`
- helper 단위 테스트는 직접 호출만 수행: `tests/test_validation_orchestrator_soft_failure.py:6-25`
- integration 테스트는 happy path만 본다: `tests/integration/test_patch_wiring.py:310-358`
- parallel 관련 기존 테스트는 wrapper fallback만 본다: `tests/test_validation_orchestrator.py:58-65`

5. downstream 영향 경계
- blocking advisory 수집 중 `FailureLearner` 장애 관측성
- `soft_failures.jsonl` 생성 여부와 audit relay payload
- sync Stage 4 validation path
- parallel validation path의 degraded mode 추적

6. 현재 테스트 근거 또는 테스트 부재
- helper 수준의 relay 형식 검증은 존재한다.
- 그러나 `record_failure.side_effect`를 주고 실제 `validate()`/`validate_parallel_v59()`를 태워 soft-failure 산출물과 audit event를 확인하는 테스트는 없다.
- 이번 표적 실행에서도 관련 스위트는 모두 green이었지만, 실제 예외 경로는 여전히 미폐쇄다.

7. 기존 문서와의 중복 여부
- `none`

8. 권장 후속 조치
- sync 경로용 테스트: `_failure_learner.record_failure.side_effect = RuntimeError(...)`를 주고 `validate()` 호출 후 `soft_failure` audit relay와 `logs/soft_failures.jsonl` 생성을 확인한다.
- parallel 경로용 테스트: 동일 조건으로 `validate_parallel_v59()` 또는 `validate_parallel_sync_v59()`를 호출해 `failure_learner_record_failure_parallel` branch를 직접 검증한다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| real `main_a` audit facade through Stage2/3 context | 미검증 | `main_a` bound method + real `AuditService` 조합으로 tagged callback 전달을 실행하는 focused test |
| `ValidationOrchestrator` degraded sync/parallel exception path | 미검증 | `record_failure` 예외 유도 후 `soft_failure` audit relay와 파일 산출물까지 확인하는 execution test |
| protocol/service semantic drift (`UIServiceProtocol`, `StateServiceProtocol`) | 기결 | `MCP-T5-003`이 이미 닫았으므로 이번 문서에서는 재오픈하지 않음 |
| `AuditServiceProtocol` tag signature / `MockProject.arcs` setter | 기결 | `T1-25`, `T1-28`이 이미 닫았으므로 이번 문서에서는 재오픈하지 않음 |

## PASS 요약

- PASS1 후보 5건 -> PASS2 제거 3건 -> PASS3 확정 2건
- 이번 트랙의 retained risk는 전부 `protocol/test green` 뒤에 남아 있는 facade callback 및 degraded exception 경로다.
- 이미 닫힌 일반 protocol drift는 재오픈하지 않고, `main_a.py` facade 표면에 직접 걸리는 신규 regression surface만 유지했다.

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
