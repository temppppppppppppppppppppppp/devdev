# main_a Facade Shim Detail Remediation FS-E2 Acceptance

> 작성일: 2026-03-13
> 상태: `executed / accepted`
> work package: `FS-E2. State-Service Validation Shim Wiring`
> 기준 문서: `main_a-facade-shim-detail-remediation-execution-ssot.md`

## 요약

`FS-E2`는 현재 코드 기준 acceptance를 만족한다.

- `Stage2Context`가 이제 `validate_arc_data_fields`를 실제 app bound method로 바인딩한다.
- `Stage2Finalizer` real-app seam 회귀가 추가되어 production repair hook가 dead path로 남지 않는다.
- `Stage3Context`, `Stage4Context`도 real bound-method 회귀를 추가해 MagicMock 분할 테스트만으로 facade drift를 가리지 않게 했다.
- dormant state-service facade shim set은 `RESERVED_STATE_SERVICE_FACADE_SHIMS`로 명시하고, live Stage2/3/4 context graph에 연결되지 않음을 회귀로 잠갔다.

## 코드 포인트

- `modules/core/stage2_context.py`
- `main_a.py`
- `tests/test_stage2_context.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context.py`
- `tests/test_main_a_persistence_helpers.py`

## 검증

- `pytest -q tests/test_state_service.py tests/test_stage2_context.py tests/test_stage2_finalizer.py tests/test_stage3_orchestrator.py tests/test_stage4_context.py tests/test_main_a_persistence_helpers.py`
  - `190 passed`
- `pytest -q tests/test_state_service.py tests/test_stage2_context.py tests/test_stage2_validation_pipeline.py tests/test_stage2_finalizer.py tests/test_stage3_orchestrator.py tests/test_stage4_context.py tests/test_stage4_context_builder.py tests/test_stage4_orchestrator.py tests/test_main_a_persistence_helpers.py`
  - `317 passed`

## 판정

- `MFS-T2-001`: accepted
- `MFS-T2-002`: accepted
- `MFS-T2-003`: accepted as `documented reserved surface`

## 다음 단위

- `FS-E3. Audit Callback / Summary Contract Alignment`
