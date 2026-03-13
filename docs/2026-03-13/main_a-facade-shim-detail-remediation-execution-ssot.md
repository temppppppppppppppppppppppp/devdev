# main_a Facade Shim Detail Remediation Execution SSOT

> 작성일: 2026-03-13
> 상태: `execution-ready`
> 문서 역할: [main_a-facade-shim-detail-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-facade-shim-detail-consolidated-findings.md), [main_a-facade-shim-detail-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-facade-shim-detail-consolidated-findings-3pass-reaudit.md) 기준으로 `main_a.py` facade shim / audit callback 수정 범위와 순서를 잠그는 단일 실행 SSOT
> 금지사항: 본 문서는 코드 수정 기록, 테스트 실행 로그, closure 문서가 아니다. 범위 고정, 우선순위 잠금, acceptance 정의까지만 담당한다.

## 1. 기준 문서

- [main_a-facade-shim-detail-full-survey-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-facade-shim-detail-full-survey-audit-order.md)
- [main_a-facade-shim-detail-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-facade-shim-detail-consolidated-findings.md)
- [main_a-facade-shim-detail-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-facade-shim-detail-consolidated-findings-3pass-reaudit.md)
- [MFS-T1-stage2-normalization-flow-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MFS-T1-stage2-normalization-flow-findings.md)
- [MFS-T2-state-service-validation-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MFS-T2-state-service-validation-findings.md)
- [MFS-T3-stage3-stage4-audit-callback-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MFS-T3-stage3-stage4-audit-callback-findings.md)
- [MFS-T4-ui-stage01-presentation-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MFS-T4-ui-stage01-presentation-findings.md)
- [MFS-T5-protocol-tests-regression-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MFS-T5-protocol-tests-regression-findings.md)

## 2. Executive Summary

이번 실행 오더의 목표는 facade shim surface를 `Stage2 normalization/flow`, `state-service validation shim`, `audit callback / summary contract`, `Stage4 NPC facade`, `operator-facing observability`의 5개 축으로 다시 잠그는 것이다.

이번 오더는 확정 건수 12를 다시 세는 문서가 아니다. 재감리에서 확정된 12개 finding을 실제 수정 묶음으로 변환하고, 아래 순서를 고정한다.

1. Stage2 normalization / flow shim alignment
2. state-service validation shim wiring 복구
3. audit callback / summary semantics 정렬
4. Stage4 NPC facade / validation parity 복구
5. operator-facing observability / presentation hygiene 정리

## 3. Scope

포함:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/stage2_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py)
- [modules/core/stage2_validation_pipeline.py](C:/Users/User/Desktop/글도비/modules/core/stage2_validation_pipeline.py)
- [modules/core/stage2_context.py](C:/Users/User/Desktop/글도비/modules/core/stage2_context.py)
- [modules/core/stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)
- [modules/core/services/state_service.py](C:/Users/User/Desktop/글도비/modules/core/services/state_service.py)
- [modules/core/stage3_context.py](C:/Users/User/Desktop/글도비/modules/core/stage3_context.py)
- [modules/core/stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- [modules/core/stage4_context.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context.py)
- [modules/core/stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)
- [modules/core/stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
- [modules/core/stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- [modules/core/services/audit_service.py](C:/Users/User/Desktop/글도비/modules/core/services/audit_service.py)
- [modules/core/services/ui_service.py](C:/Users/User/Desktop/글도비/modules/core/services/ui_service.py)
- [modules/protocols/app_services.py](C:/Users/User/Desktop/글도비/modules/protocols/app_services.py)
- [modules/validation/validation_orchestrator.py](C:/Users/User/Desktop/글도비/modules/validation/validation_orchestrator.py)
- [modules/validation/consistency_validator.py](C:/Users/User/Desktop/글도비/modules/validation/consistency_validator.py)

제외:

- Stage2/3/4 narrative quality 전면 개편
- desktop / packaging / provider 변경
- unrelated control-plane 부트 / 프로젝트 root 수정

## 4. 실행 원칙

### 원칙 A. facade export와 live consumer graph는 같은 callback 집합을 봐야 한다

- `main_a.py`에 export된 shim이 실제 context에 안 실리면, dead surface 정리 또는 wiring 복구 중 하나만 허용한다.

### 원칙 B. false-pass semantics는 facade 문제로 본다

- runtime exception이 `PASS`로 흡수되거나, 실패/중단 경로가 `complete` summary로 덮이면 facade contract 위반으로 처리한다.

### 원칙 C. protocol / test green은 bound-method seam을 닫았을 때만 acceptance다

- MagicMock 분할 테스트, direct helper call, protocol-only conformance로는 package를 닫지 않는다.

### 원칙 D. live Stage4 validation은 facade를 우회한 빈 context PASS를 허용하지 않는다

- NPC facade가 남아 있는데 `npc_profiles={}`로 태도 검사가 비활성화되는 구조는 허용하지 않는다.

### 원칙 E. operator-facing 문자열도 contract다

- mojibake log와 잘못된 UI 라벨은 P3여도 package acceptance에 포함한다.

## 5. Package Map

| Work Package | 포함 finding |
|--------------|--------------|
| `FS-E1` Stage2 Normalization / Flow Shim Alignment | `MFS-T1-001`, `MFS-T1-002` |
| `FS-E2` State-Service Validation Shim Wiring | `MFS-T2-001`, `MFS-T2-002`, `MFS-T2-003` |
| `FS-E3` Audit Callback / Summary Contract Alignment | `MFS-T3-01`, `MFS-T3-02`, `MFS-T5-001`, `MFS-T5-002` |
| `FS-E4` Stage4 NPC Facade / Validation Parity | `MFS-T4-001` |
| `FS-E5` Observability / Presentation Hygiene | `MFS-T3-03`, `MFS-T4-002` |

## 6. Work Packages

### FS-E1. Stage2 Normalization / Flow Shim Alignment

대상 finding:

- `MFS-T1-001`
- `MFS-T1-002`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/stage2_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py)
- [modules/core/stage2_validation_pipeline.py](C:/Users/User/Desktop/글도비/modules/core/stage2_validation_pipeline.py)

구현 원칙:

- duplicate threshold 기본값은 facade / orchestrator / validation pipeline이 하나의 constant를 공유한다.
- flow analyzer runtime exception은 legacy fallback 또는 explicit diagnostic status로 surface한다.
- `fallback=True`만 남기고 `status='PASS'`로 advisory를 삼키는 구조는 제거한다.

acceptance:

- `0.92 < similarity < 0.98` 구간 샘플에서 facade / orchestrator / pipeline / duplicate guard가 같은 판정을 낸다.
- analyzer runtime exception과 import failure가 같은 fallback semantics를 가진다.

필수 테스트:

- 기존: [test_stage2_pipeline.py](C:/Users/User/Desktop/글도비/tests/test_stage2_pipeline.py), [test_stage2_validation_pipeline.py](C:/Users/User/Desktop/글도비/tests/test_stage2_validation_pipeline.py)
- 신규:
  - threshold band parity regression
  - analyzer runtime exception fallback regression

### FS-E2. State-Service Validation Shim Wiring

대상 finding:

- `MFS-T2-001`
- `MFS-T2-002`
- `MFS-T2-003`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/services/state_service.py](C:/Users/User/Desktop/글도비/modules/core/services/state_service.py)
- [modules/core/stage2_context.py](C:/Users/User/Desktop/글도비/modules/core/stage2_context.py)
- [modules/core/stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)
- [modules/core/stage3_context.py](C:/Users/User/Desktop/글도비/modules/core/stage3_context.py)
- [modules/core/stage4_context.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context.py)
- [modules/core/stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)

구현 원칙:

- `validate_arc_data_fields` repair hook가 live Stage2 graph에 실제 도달하도록 `Stage2Context`에 slot / binding / consumer test를 맞춘다.
- validation shim은 real bound-method fixture를 통해 Stage2/3/4 context에 배선되는지 검증한다.
- consumer가 없는 dormant shim은 제거하거나, future consumer와 contract를 문서/테스트로 명시한다.

acceptance:

- `Stage2Context.from_app(real_app)`로 만든 finalizer가 실제 `validate_arc_data_fields`를 호출한다.
- Stage2/3/4 context 테스트가 MagicMock callback 치환만으로 facade drift를 가리지 않는다.
- dormant shim set은 dead surface 정리 또는 documented reserved surface 중 하나로 정리된다.

필수 테스트:

- 기존: [test_state_service.py](C:/Users/User/Desktop/글도비/tests/test_state_service.py), [test_stage2_context.py](C:/Users/User/Desktop/글도비/tests/test_stage2_context.py), [test_stage2_finalizer.py](C:/Users/User/Desktop/글도비/tests/test_stage2_finalizer.py), [test_stage3_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage3_orchestrator.py), [test_stage4_context.py](C:/Users/User/Desktop/글도비/tests/test_stage4_context.py)
- 신규:
  - real bound-method Stage2 finalizer repair-hook regression
  - Stage2/3/4 context real-app binding regression
  - dormant shim inventory / no-consumer assertion or removal regression

### FS-E3. Audit Callback / Summary Contract Alignment

대상 finding:

- `MFS-T3-01`
- `MFS-T3-02`
- `MFS-T5-001`
- `MFS-T5-002`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- [modules/core/stage4_context.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context.py)
- [modules/core/stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
- [modules/core/services/audit_service.py](C:/Users/User/Desktop/글도비/modules/core/services/audit_service.py)
- [modules/protocols/app_services.py](C:/Users/User/Desktop/글도비/modules/protocols/app_services.py)
- [modules/validation/validation_orchestrator.py](C:/Users/User/Desktop/글도비/modules/validation/validation_orchestrator.py)

구현 원칙:

- `stage3_complete`는 정상 완주 시에만 기록한다.
- Stage4 completion audit callback source는 `ctx` 또는 `app` 한 곳으로 통일한다.
- tagged `write_audit_summary(tag)` facade contract를 protocol/test/consumer seam에서 실제로 잠근다.
- `ValidationOrchestrator` soft-failure relay는 helper direct-call이 아니라 sync/parallel 실제 예외 경로에서 검증한다.

acceptance:

- Stage3 failure / break / retry exhaustion 경로에서는 `stage3_complete` summary가 기록되지 않는다.
- Stage4 success / non-success path가 같은 callback source-of-truth를 사용한다.
- `write_audit_summary("stage*_complete")` tagged contract가 real facade seam에서 regression으로 잠긴다.
- soft-failure relay가 sync/parallel 실제 exception path에서 로그와 audit로 surface된다.

필수 테스트:

- 기존: [test_stage3_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage3_orchestrator.py), [test_stage4_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage4_orchestrator.py), [test_run_stage4_canary.py](C:/Users/User/Desktop/글도비/tests/test_run_stage4_canary.py), [test_protocols_services.py](C:/Users/User/Desktop/글도비/tests/test_protocols_services.py), [test_validation_orchestrator_soft_failure.py](C:/Users/User/Desktop/글도비/tests/test_validation_orchestrator_soft_failure.py)
- 신규:
  - Stage3 non-complete summary negative regression
  - Stage4 completion callback source parity regression
  - tagged audit summary real-app seam regression
  - sync / parallel soft-failure relay execution regression

### FS-E4. Stage4 NPC Facade / Validation Parity

대상 finding:

- `MFS-T4-001`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/prompt_builder.py](C:/Users/User/Desktop/글도비/modules/core/prompt_builder.py)
- [modules/core/stage4_context.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context.py)
- [modules/core/stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- [modules/validation/consistency_validator.py](C:/Users/User/Desktop/글도비/modules/validation/consistency_validator.py)

구현 원칙:

- Stage4 live validation path가 `npc_profiles`를 빈 dict로 넘기지 않게 한다.
- `main_a` NPC facade, `PromptBuilder.build_validation_context()`, `ConsistencyValidator` input contract 중 하나를 canonical source로 고정한다.

acceptance:

- `_build_cv_context()`가 non-empty `npc_profiles`를 실제 populate 하거나, 태도 전환 검사가 facade와 동일 contract를 본다.
- `ConsistencyValidator`의 NPC attitude check가 live Stage4 path에서 bypass되지 않는다.

필수 테스트:

- 기존: [test_prompt_builder.py](C:/Users/User/Desktop/글도비/tests/test_prompt_builder.py), [test_stage4_context.py](C:/Users/User/Desktop/글도비/tests/test_stage4_context.py), [test_stage4_cv_context.py](C:/Users/User/Desktop/글도비/tests/test_stage4_cv_context.py), [test_stage4_interview_round.py](C:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py)
- 신규:
  - Stage4 `npc_profiles` population regression
  - `ConsistencyValidator` input parity regression

### FS-E5. Observability / Presentation Hygiene

대상 finding:

- `MFS-T3-03`
- `MFS-T4-002`

대상 파일:

- [modules/core/stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- [modules/core/services/ui_service.py](C:/Users/User/Desktop/글도비/modules/core/services/ui_service.py)
- [modules/core/stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)

구현 원칙:

- unresolved continuity pin log는 정상 UTF-8 문자열로 고친다.
- `_show_volume_table()` presentation은 실제 권 수 또는 중립 라벨을 쓴다.

acceptance:

- continuity pin unresolved log에서 mojibake가 사라진다.
- 1권 fixture에서도 `10권` 고정 타이틀이 출력되지 않는다.

필수 테스트:

- 기존: [test_stage3_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage3_orchestrator.py), [test_ui_service.py](C:/Users/User/Desktop/글도비/tests/test_ui_service.py), [test_stage01_helpers.py](C:/Users/User/Desktop/글도비/tests/test_stage01_helpers.py)
- 신규:
  - continuity pin log snapshot or sentinel regression
  - dynamic volume table title regression

## 7. 권장 실행 순서

1. `FS-E1`
2. `FS-E2`
3. `FS-E3`
4. `FS-E4`
5. `FS-E5`

## 8. Public Contracts To Preserve

- `main_a.py` facade 메서드 이름과 외부 call surface
- Stage2/3/4 context `from_app()` 진입 surface
- `write_audit_summary(tag)` tagged callback 의미
- `ValidationOrchestrator` degraded-mode soft failure relay
- Stage01 completion UI flow

## 9. Verification Plan

공통:

- package별 focused pytest
- protocol / audit / Stage2/3/4 / UI 관련 기존 회귀군 재실행
- 필요 시 synthetic real-app fixture로 bound-method seam 재현

최종 종료 조건:

- 12개 finding이 모두 code acceptance 또는 regression acceptance로 닫힌다.
- green protocol/test가 facade drift를 가리는 상태가 사라진다.
- live consumer graph와 facade export surface가 같은 contract를 본다.

## 10. Out of Scope Notes

- Stage2/3/4 narrative quality overhaul
- unrelated control-plane / desktop / packaging 변경
