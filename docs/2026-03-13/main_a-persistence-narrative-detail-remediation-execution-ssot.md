# main_a Persistence Narrative Detail Remediation Execution SSOT

> 작성일: 2026-03-13
> 상태: `execution-ready`
> 문서 역할: [main_a-persistence-narrative-detail-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-persistence-narrative-detail-consolidated-findings.md), [main_a-persistence-narrative-detail-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-persistence-narrative-detail-consolidated-findings-3pass-reaudit.md) 기준으로 shared persistence / narrative helper 수정 범위와 순서를 잠그는 단일 실행 SSOT
> 금지사항: 본 문서는 코드 수정 기록, rerun 결과 보고, closure 문서가 아니다. 범위 고정, 우선순위 잠금, acceptance 정의까지만 담당한다.

## 1. 기준 문서

- [main_a-persistence-narrative-detail-full-survey-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-persistence-narrative-detail-full-survey-audit-order.md)
- [main_a-persistence-narrative-detail-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-persistence-narrative-detail-consolidated-findings.md)
- [main_a-persistence-narrative-detail-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-persistence-narrative-detail-consolidated-findings-3pass-reaudit.md)
- [MPN-T1-commit-preset-recovery-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md)
- [MPN-T2-protagonist-episode-mapping-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MPN-T2-protagonist-episode-mapping-findings.md)
- [MPN-T3-stage01-stage3-shared-helper-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MPN-T3-stage01-stage3-shared-helper-findings.md)
- [MPN-T4-stage4-summary-cache-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MPN-T4-stage4-summary-cache-findings.md)
- [MPN-T5-consumer-tests-legacy-contract-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MPN-T5-consumer-tests-legacy-contract-findings.md)

## 2. Executive Summary

이번 실행 오더의 목표는 shared helper surface를 `protagonist / episode / arc mapping`, `preset / commit / cache lifecycle`, `Stage01 boundary helper`, `narrative summary lifecycle`, `consumer regression net`의 5개 축으로 다시 잠그는 것이다.

이번 오더는 확정 건수 16을 다시 세는 문서가 아니다. 재감리에서 확정된 16개 finding을 실제 수정 묶음으로 변환하고, 아래 순서를 고정한다.

1. protagonist / episode / arc SSOT 통일
2. preset / commit / cache lifecycle 복구
3. Stage01 boundary helper decoupling과 fail-closed validation 복구
4. narrative summary lifecycle cleanup
5. consumer regression hardening

## 3. Scope

포함:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/services/project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py)
- [modules/core/db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)
- [modules/core/stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)
- [modules/core/stage2_context.py](C:/Users/User/Desktop/글도비/modules/core/stage2_context.py)
- [modules/core/stage2_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py)
- [modules/core/stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py)
- [modules/core/stage3_context.py](C:/Users/User/Desktop/글도비/modules/core/stage3_context.py)
- [modules/core/stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- [modules/core/stage4_context.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context.py)
- [modules/core/stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)
- [modules/core/stage4_post_processor.py](C:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py)
- [modules/domain/agents/state_extractor.py](C:/Users/User/Desktop/글도비/modules/domain/agents/state_extractor.py)
- [modules/domain/agents/director_continuity.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py)

제외:

- destructive op 전체 재감사 전반
- Stage2/3/4 내부 생성 quality 개편
- unrelated UI / desktop / provider 변경

## 4. 실행 원칙

### 원칙 A. protagonist와 arc mapping은 live runtime source를 기준으로 하나만 본다

- DB anchor와 in-memory `master_bible`를 혼용하지 않는다.
- episode -> arc 계산은 중앙 설정 또는 실제 arc boundary 중 하나만 SSOT로 쓴다.

### 원칙 B. commit helper의 bool 의미는 stage마다 달라지면 안 된다

- `False` 반환은 무시, hard fail, audit-only 중 하나로 통일한다.

### 원칙 C. Stage01 validation helper는 fail-open과 hidden coupling을 동시에 허용하지 않는다

- 비문자열 payload는 검사 없이 통과시키지 않는다.
- `main_a.py` private method 숨은 의존은 명시적 service 또는 helper 내부 구현으로 정리한다.

### 원칙 D. narrative summary는 저장 범위와 로드 범위가 같은 episode semantics를 봐야 한다

- stale future summary, sparse `ep_range`, duplicate summary injection을 허용하지 않는다.

### 원칙 E. skip되는 smoke와 MagicMock auto-attr는 acceptance가 아니다

- consumer regression blind spot은 별도 package에서 focused regression으로 닫는다.

## 5. Package Map

| Work Package | 포함 finding |
|--------------|--------------|
| `PN-E1` Protagonist / Episode / Arc SSOT Alignment | `MPN-T2-01`, `MPN-T2-02`, `MPN-T2-03`, `MPN-T2-04`, `MPN-T5-001` |
| `PN-E2` Preset / Commit / Cache Lifecycle Recovery | `MPN-T1-001`, `MPN-T1-002`, `MPN-T5-002` |
| `PN-E3` Stage01 Boundary Helper Decoupling | `MPN-T3-001`, `MPN-T3-002`, `MPN-T3-003` |
| `PN-E4` Narrative Summary Lifecycle Cleanup | `MPN-T4-001`, `MPN-T4-002`, `MPN-T4-003` |
| `PN-E5` Consumer Regression Hardening | `MPN-T5-003`, `MPN-T5-004` |

## 6. Work Packages

### PN-E1. Protagonist / Episode / Arc SSOT Alignment

대상 finding:

- `MPN-T2-01`
- `MPN-T2-02`
- `MPN-T2-03`
- `MPN-T2-04`
- `MPN-T5-001`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/constants.py](C:/Users/User/Desktop/글도비/modules/core/constants.py)
- [modules/core/stage2_context.py](C:/Users/User/Desktop/글도비/modules/core/stage2_context.py)
- [modules/core/stage2_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py)
- [modules/core/stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- [modules/core/stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)
- [modules/core/stage4_post_processor.py](C:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py)
- [modules/domain/agents/state_extractor.py](C:/Users/User/Desktop/글도비/modules/domain/agents/state_extractor.py)
- [modules/domain/agents/director_continuity.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py)

구현 원칙:

- `_get_protagonist_name()`의 1순위 source를 live `current_project.master_bible`로 올리고 DB anchor는 fallback으로 내린다.
- `_fix_entity_registry_protagonist()`는 동일 이름 extracted row를 protagonist row로 승격하는 최소 보정으로 바꾼다.
- `calculate_arc_from_episode` nullable slot은 hard-call하지 않는다.
- `_calculate_arc_from_episode()`는 5화 고정 공식 대신 중앙 설정 또는 실제 arc boundary 기반 계산으로 통일한다.

acceptance:

- live bible 최신 / DB anchor stale 상황에서 protagonist name이 live source를 따른다.
- protagonist extracted row가 이미 있으면 duplicate row를 만들지 않는다.
- manuscript>0 + `calculate_arc_from_episode=None` 조합에서도 Stage2가 crash 대신 deterministic fallback/diagnostic으로 닫힌다.
- `ep=4/5/8/9` 경계에서 smart skip arc 번호가 current SSOT와 일치한다.

필수 테스트:

- 기존: [test_stage3_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage3_orchestrator.py), [test_stage2_context.py](C:/Users/User/Desktop/글도비/tests/test_stage2_context.py), [test_sweep36.py](C:/Users/User/Desktop/글도비/tests/test_sweep36.py)
- 신규:
  - protagonist source drift regression
  - extracted protagonist dedupe regression
  - nullable callback guard regression
  - variable `ep_count` arc mapping regression

### PN-E2. Preset / Commit / Cache Lifecycle Recovery

대상 finding:

- `MPN-T1-001`
- `MPN-T1-002`
- `MPN-T5-002`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/services/project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py)
- [modules/core/db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)
- [modules/core/stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)

구현 원칙:

- `_restore_preset_registry()`는 no-data / malformed payload에서 stale preset을 유지하지 않는다.
- cache metadata save path는 `save_anchor()`와 `_safe_commit()` 성공을 실제로 확인한 뒤에만 success log / cache injection을 수행한다.
- Stage4 cleanup도 `_safe_commit=False`를 Stage2/3과 같은 의미로 surface한다.

acceptance:

- project switch / rollback 이후 stale preset이 남지 않는다.
- `save_anchor=False` 또는 `_safe_commit=False`면 cache success log / audit / injection이 발생하지 않는다.
- Stage4 cleanup에서 `_safe_commit=False`가 조용히 무시되지 않는다.

필수 테스트:

- 기존: [test_project_service.py](C:/Users/User/Desktop/글도비/tests/test_project_service.py), [test_main_a_rollback.py](C:/Users/User/Desktop/글도비/tests/test_main_a_rollback.py), [test_stage4_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage4_orchestrator.py)
- 신규:
  - stale preset clear regression
  - cache metadata false-success regression
  - Stage4 cleanup commit-failure regression

### PN-E3. Stage01 Boundary Helper Decoupling

대상 finding:

- `MPN-T3-001`
- `MPN-T3-002`
- `MPN-T3-003`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)
- [modules/protocols/app_services.py](C:/Users/User/Desktop/글도비/modules/protocols/app_services.py)
- [modules/core/stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py)

구현 원칙:

- `_validate_volume_boundaries()`는 비문자열 `strategy_doc`를 fail-open 하지 않는다.
- validator는 `main_a.py` private method 숨은 결합 대신 Stage01 helper 내부 또는 explicit service contract로 승격한다.
- success path 테스트는 retry wrapper 전체를 mock하지 않고 실제 boundary callback chain을 실행한다.

acceptance:

- `strategy_doc`가 `dict`, `None`, invalid structure일 때 boundary semantics가 명시적으로 잠긴다.
- Stage01 helper가 숨은 `app._validate_volume_boundaries` 의존 없이 동작하거나, 그 의존이 protocol/test/document에서 명시된다.
- success path 테스트가 실제 `REJECT`, `WARNING`, invalid structure 분기를 실행한다.

필수 테스트:

- 기존: [test_stage01_helpers.py](C:/Users/User/Desktop/글도비/tests/test_stage01_helpers.py), [test_stage01_fixes.py](C:/Users/User/Desktop/글도비/tests/test_stage01_fixes.py), [test_ui_service.py](C:/Users/User/Desktop/글도비/tests/test_ui_service.py)
- 신규:
  - `dict strategy_doc` fail-closed regression
  - real `_vol_on_success()` execution regression
  - protocol or fake-app based dependency regression

### PN-E4. Narrative Summary Lifecycle Cleanup

대상 finding:

- `MPN-T4-001`
- `MPN-T4-002`
- `MPN-T4-003`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/services/project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py)
- [modules/core/db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)
- [modules/core/stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)
- [modules/core/stage4_context.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context.py)
- [modules/core/stage4_post_processor.py](C:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py)

구현 원칙:

- destructive op 이후 `narrative_summary_ep_*` lifecycle을 명시적으로 정리하거나 loader가 current episode 경계를 기준으로 필터링한다.
- `ep_range`는 실제 manuscript episode set 기준으로 저장한다.
- series/volume/narrative summary 조립 책임을 builder 또는 loader 한 곳으로 단일화한다.

acceptance:

- rollback / reset / wipe 뒤 미래 narrative summary가 Stage4 prompt에 주입되지 않는다.
- sparse manuscript에서도 `ep_range`가 실제 커버리지를 거짓으로 표기하지 않는다.
- summary 중복 주입이 제거되고 budget 소비가 한 경로에서만 일어난다.

필수 테스트:

- 기존: [test_sweep23.py](C:/Users/User/Desktop/글도비/tests/test_sweep23.py), [test_stage4_context.py](C:/Users/User/Desktop/글도비/tests/test_stage4_context.py), [test_stage4_context_builder.py](C:/Users/User/Desktop/글도비/tests/test_stage4_context_builder.py), [test_stage4_post_processor.py](C:/Users/User/Desktop/글도비/tests/test_stage4_post_processor.py)
- 신규:
  - rollback/wipe narrative summary filter regression
  - sparse manuscript `ep_range` regression
  - summary dedupe / single-injection regression

### PN-E5. Consumer Regression Hardening

대상 finding:

- `MPN-T5-003`
- `MPN-T5-004`

대상 파일:

- [tests/e2e/test_l3_stage2_realproject.py](C:/Users/User/Desktop/글도비/tests/e2e/test_l3_stage2_realproject.py)
- [tests/e2e/test_l3_golden_route.py](C:/Users/User/Desktop/글도비/tests/e2e/test_l3_golden_route.py)
- [tests/test_stage3_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage3_orchestrator.py)

구현 원칙:

- e2e smoke fixture의 `_safe_commit_async()`는 production contract와 같은 `bool` 반환을 가진다.
- skip 의존은 줄이되, hermetic fixture가 어렵다면 최소 smoke 대체 regression을 추가한다.
- Stage3 slot coverage는 spec 없는 MagicMock auto-attr에 기대지 않는다.

acceptance:

- Stage2 smoke fixture가 `_safe_commit_async -> bool` 계약을 정확히 모사한다.
- skip돼도 core contract를 닫는 hermetic regression이 존재한다.
- Stage3 `from_app` slot coverage test가 명시적 fake or spec mock로 바뀐다.

필수 테스트:

- 기존: [test_stage2_finalizer.py](C:/Users/User/Desktop/글도비/tests/test_stage2_finalizer.py), [test_stage3_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage3_orchestrator.py)
- 신규:
  - `safe_commit_async=False` negative regression
  - hermetic Stage2 commit semantics smoke
  - spec-based Stage3 `from_app` slot coverage regression

## 7. 권장 실행 순서

1. `PN-E1`
2. `PN-E2`
3. `PN-E3`
4. `PN-E4`
5. `PN-E5`

## 8. Public Contracts To Preserve

- `current_project.master_bible`를 사용하는 Stage1/3/4 consumer surface
- `safe_commit()` / `safe_commit_async()` bool-return contract
- Stage01 `volumes` anchor와 UI completion flow
- Stage4 summary loading / injection 외부 callback surface

## 9. Verification Plan

공통:

- package별 focused pytest
- persistence / rollback / Stage01 / Stage4 관련 기존 회귀군 재실행
- 필요 시 synthetic app/project ad-hoc 재현

최종 종료 조건:

- 16개 finding이 모두 code acceptance 또는 regression acceptance로 닫힌다.
- skip되는 smoke와 MagicMock auto-attr가 핵심 계약을 대신하지 않는다.
- protagonist/episode mapping과 summary lifecycle이 하나의 SSOT로 정렬된다.

## 10. Out of Scope Notes

- BI schema 전체 재작성
- Stage2/3/4 narrative quality 개선 전반
- unrelated UI / desktop / packaging / provider 수정
