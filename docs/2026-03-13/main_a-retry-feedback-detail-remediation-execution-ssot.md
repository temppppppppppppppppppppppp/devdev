# main_a Retry Feedback Detail Remediation Execution SSOT

> 작성일: 2026-03-13
> 상태: `execution-ready`
> 문서 역할: [main_a-retry-feedback-detail-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-retry-feedback-detail-consolidated-findings.md), [main_a-retry-feedback-detail-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-retry-feedback-detail-consolidated-findings-3pass-reaudit.md) 기준으로 `main_a.py` retry-feedback surface 수정 범위와 순서를 잠그는 단일 실행 SSOT
> 금지사항: 본 문서는 코드 수정 기록, 테스트 실행 로그, postfix closure 문서가 아니다. 범위 고정, 우선순위 잠금, acceptance 정의까지만 담당한다.

## 1. 기준 문서

- [main_a-retry-feedback-detail-full-survey-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-retry-feedback-detail-full-survey-audit-order.md)
- [main_a-retry-feedback-detail-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-retry-feedback-detail-consolidated-findings.md)
- [main_a-retry-feedback-detail-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-retry-feedback-detail-consolidated-findings-3pass-reaudit.md)
- [MRF-T1-stage2-callback-binding-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MRF-T1-stage2-callback-binding-findings.md)
- [MRF-T2-rejection-analysis-intensity-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MRF-T2-rejection-analysis-intensity-findings.md)
- [MRF-T3-prompt-guidance-context-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MRF-T3-prompt-guidance-context-findings.md)
- [MRF-T4-cross-stage-reverse-feedback-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md)
- [MRF-T5-consumer-tests-regression-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MRF-T5-consumer-tests-regression-findings.md)

## 2. Executive Summary

이번 실행 오더의 목표는 retry-feedback surface를 `Stage2 retry loop`, `rejection triage`, `prompt/context helper`, `Stage4->3/2 reverse translation`, `consumer regression net`의 4개 수정 묶음으로 다시 잠그는 것이다.

이번 오더는 확정 건수 13을 다시 세는 문서가 아니다. 재감리에서 확정된 13개 finding을 실제 수정 묶음으로 변환하고, 아래 순서를 고정한다.

1. Stage2 callback required/optional contract 정렬
2. rejection taxonomy / detail payload 복구
3. guidance / context helper live wiring 정리
4. cross-stage reverse feedback semantic preservation

## 3. Scope

포함:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/stage2_context.py](C:/Users/User/Desktop/글도비/modules/core/stage2_context.py)
- [modules/core/stage2_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py)
- [modules/core/stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py)
- [modules/core/stage2_validation_pipeline.py](C:/Users/User/Desktop/글도비/modules/core/stage2_validation_pipeline.py)
- [modules/core/stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)
- [modules/core/prompt_builder.py](C:/Users/User/Desktop/글도비/modules/core/prompt_builder.py)
- [modules/core/feedback_system.py](C:/Users/User/Desktop/글도비/modules/core/feedback_system.py)
- [modules/core/stage3_context.py](C:/Users/User/Desktop/글도비/modules/core/stage3_context.py)
- [modules/core/stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)
- [modules/core/stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
- [modules/core/stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- [modules/core/pass_rate_monitor.py](C:/Users/User/Desktop/글도비/modules/core/pass_rate_monitor.py)

제외:

- Stage4 writer prompt 전체 재설계
- Stage2/3/4 내부 생성 알고리즘 전면 개편
- unrelated UI / desktop / packaging 수정

## 4. 실행 원칙

### 원칙 A. callback은 `required`, `optional-with-fallback`, `observability-only`로 명시 분류한다

- `None` 허용 slot과 무가드 hard-call을 섞어 두지 않는다.
- callback 부재는 hard fail, deterministic fallback, audit-only 중 하나로만 처리한다.

### 원칙 B. repeated reject는 count만이 아니라 cause와 detail을 함께 보존해야 한다

- `specific_issue`, normalized reason, fix guide가 함께 살아야 retry feedback가 의미를 가진다.
- `기타` fallback도 empty guidance로 끝내지 않는다.

### 원칙 C. helper가 live path에 안 붙어 있으면 둘 중 하나만 허용한다

- 실제 consumer에 배선한다.
- 아니면 dead surface로 정리한다.

### 원칙 D. cross-stage feedback는 retry cost가 아니라 failure semantics를 전달해야 한다

- Stage4 reject가 Stage3/Stage2에 갈 때 `difficulty`만 남는 구조는 허용하지 않는다.

### 원칙 E. regression은 같은 package의 종료 조건이다

- pure helper unit test만 green인 상태로 package를 닫지 않는다.
- `main_a bound method -> context -> consumer` seam test가 acceptance에 포함된다.

## 5. Package Map

| Work Package | 포함 finding |
|--------------|--------------|
| `RF-E1` Stage2 Callback Contract Hardening | `MRF-T1-001`, `MRF-T1-002`, `MRF-T4-002`, `MRF-T5-001` |
| `RF-E2` Rejection Taxonomy / Detail Restoration | `MRF-T2-01`, `MRF-T2-02`, `MRF-T5-003` |
| `RF-E3` Guidance / Context Live Wiring Cleanup | `MRF-T3-01`, `MRF-T3-02`, `MRF-T3-03`, `MRF-T5-002` |
| `RF-E4` Cross-Stage Reverse Feedback Preservation | `MRF-T4-001`, `MRF-T4-003` |

## 6. Work Packages

### RF-E1. Stage2 Callback Contract Hardening

대상 finding:

- `MRF-T1-001`
- `MRF-T1-002`
- `MRF-T4-002`
- `MRF-T5-001`

대상 파일:

- [modules/core/stage2_context.py](C:/Users/User/Desktop/글도비/modules/core/stage2_context.py)
- [modules/core/stage2_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py)
- [modules/core/stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py)
- [modules/core/stage2_validation_pipeline.py](C:/Users/User/Desktop/글도비/modules/core/stage2_validation_pipeline.py)
- [modules/core/stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)

구현 원칙:

- retry-feedback callback bundle을 `required`, `optional-with-fallback`, `observability-only`로 명시 분리한다.
- `analyze_rejection_pattern_v60`와 `generate_reverse_feedback_stage3_to_2`는 현재 consumer 기준 hard-call / silent-drop 혼합 상태를 제거한다.
- `Stage2Context.from_app()` 또는 별도 validator가 missing callback ledger를 남기게 한다.

acceptance:

- callback이 없는 `from_app()` context에서도 retry loop가 hard crash 대신 명시적 fallback 또는 explicit diagnostic으로 닫힌다.
- `Stage3->2` missing callback branch가 `audit-only` silent green으로 끝나지 않는다.
- Stage2 consumer가 same callback family를 같은 등급으로 해석한다.

필수 테스트:

- 기존: [test_stage2_context.py](C:/Users/User/Desktop/글도비/tests/test_stage2_context.py), [test_stage2_preflight.py](C:/Users/User/Desktop/글도비/tests/test_stage2_preflight.py), [test_stage2_preflight_helpers.py](C:/Users/User/Desktop/글도비/tests/test_stage2_preflight_helpers.py), [test_stage2_validation_pipeline.py](C:/Users/User/Desktop/글도비/tests/test_stage2_validation_pipeline.py)
- 신규:
  - `from_app()` auto-build ctx + missing `analyze_rejection_pattern_v60` regression
  - `callback=None + stage3 failure >= 3` reverse feedback regression
  - callback map completeness / parameter contract regression

### RF-E2. Rejection Taxonomy / Detail Restoration

대상 finding:

- `MRF-T2-01`
- `MRF-T2-02`
- `MRF-T5-003`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)
- [modules/core/stage2_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py)

구현 원칙:

- Stage2 rejection history producer가 `specific_issue` 또는 동등 structured detail field를 남기도록 맞춘다.
- normalization taxonomy는 실제 recorded reason 샘플 기준으로 재작성한다.
- `기타` bucket에도 최소 generic fix guide를 부여한다.

acceptance:

- repeated reject feedback에서 `specific_issue`가 있으면 detail section이 실제 출력된다.
- 자유서술형 대표 reason class가 `기타`로 과도하게 붕괴하지 않는다.
- `_analyze_rejection_pattern_v60()` 계열 helper에 direct regression test가 존재한다.

필수 테스트:

- 기존: [test_feedback_system.py](C:/Users/User/Desktop/글도비/tests/test_feedback_system.py), [test_stage2_preflight_helpers.py](C:/Users/User/Desktop/글도비/tests/test_stage2_preflight_helpers.py)
- 신규:
  - recorded reason sample golden test
  - `specific_issue` present/absent output structure test
  - normalization bucket + fix guide mapping test

### RF-E3. Guidance / Context Live Wiring Cleanup

대상 finding:

- `MRF-T3-01`
- `MRF-T3-02`
- `MRF-T3-03`
- `MRF-T5-002`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/prompt_builder.py](C:/Users/User/Desktop/글도비/modules/core/prompt_builder.py)
- [modules/core/feedback_system.py](C:/Users/User/Desktop/글도비/modules/core/feedback_system.py)
- [modules/core/stage2_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py)
- [modules/core/stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py)
- [modules/core/stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)
- [modules/core/stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)
- [modules/core/stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)

구현 원칙:

- writer guidance 계열 helper는 live Stage4 path에 실제로 연결하거나, dead surface를 정리한다.
- `generate_arc_context_v60(current_arc_no=...)`는 no-op 인자를 유지하지 않는다.
- `build_minimal_arc_context()`와 full arc context가 shared energy / state utility를 재사용하게 한다.

acceptance:

- Stage4 writer prompt / context build path에서 writer guidance family의 live 여부가 문서/코드/테스트 중 하나로 명확히 잠긴다.
- `current_arc_no` contract가 no-op 상태로 남지 않는다.
- retry minimal context와 full arc context가 같은 multi-arc energy state를 설명한다.

필수 테스트:

- 기존: [test_prompt_builder.py](C:/Users/User/Desktop/글도비/tests/test_prompt_builder.py), [test_feedback_system.py](C:/Users/User/Desktop/글도비/tests/test_feedback_system.py), [test_stage4_context_builder.py](C:/Users/User/Desktop/글도비/tests/test_stage4_context_builder.py)
- 신규:
  - writer guidance live wiring integration test
  - `current_arc_no` semantic contract regression
  - multi-arc energy parity regression
  - app-bound `generate_arc_context_v60` cache/audit regression

### RF-E4. Cross-Stage Reverse Feedback Preservation

대상 finding:

- `MRF-T4-001`
- `MRF-T4-003`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/stage3_context.py](C:/Users/User/Desktop/글도비/modules/core/stage3_context.py)
- [modules/core/stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
- [modules/core/stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- [modules/core/pass_rate_monitor.py](C:/Users/User/Desktop/글도비/modules/core/pass_rate_monitor.py)
- [modules/core/feedback_system.py](C:/Users/User/Desktop/글도비/modules/core/feedback_system.py)
- [modules/core/stage2_preflight.py](C:/Users/User/Desktop/글도비/modules/core/stage2_preflight.py)

구현 원칙:

- `Stage4->3` helper를 live Stage3 consumer에 실제로 연결하거나, 현재 advisory path를 SSOT로 승격하면서 dead helper를 제거한다.
- `Stage4->2` reverse payload는 difficulty-only 요약을 넘어서 semantic field를 함께 전달한다.
- `_enrich_director_result()`를 실제 live path에 연결할지, dead helper로 정리할지 결정한다.

acceptance:

- `Stage4 reject -> Stage3 correction prompt` 경계에서 helper 또는 문서화된 대체 경로가 실제로 하나만 SSOT로 남는다.
- `Stage4 record_attempt -> Stage2 reverse feedback` 경계에서 `error_category`, `reject_bucket`, `score_breakdown` 또는 동등 semantic field가 보존된다.

필수 테스트:

- 기존: [test_feedback_system.py](C:/Users/User/Desktop/글도비/tests/test_feedback_system.py), [test_stage3_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage3_orchestrator.py), [test_stage4_interview_round.py](C:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py), [test_arc_difficulty.py](C:/Users/User/Desktop/글도비/tests/test_arc_difficulty.py)
- 신규:
  - `Stage4 reject -> Stage3 reverse feedback injection` integration test
  - `Stage4 attempt record -> Stage2 reverse feedback semantic preservation` integration test

## 7. 권장 실행 순서

1. `RF-E1`
2. `RF-E2`
3. `RF-E3`
4. `RF-E4`

## 8. Public Contracts To Preserve

- `main_a.py` retry-feedback facade 메서드 이름 체계
- `Stage2Context.from_app()` auto-build 진입 surface
- Stage2 retry loop의 repeated reject prepend semantics
- Stage4 reject history -> Stage3/Stage2 feedback 전달 경계

## 9. Verification Plan

공통:

- package별 focused pytest
- 관련 기존 회귀군 재실행
- 필요 시 synthetic app/context ad-hoc 재현

최종 종료 조건:

- 13개 finding이 모두 code acceptance 또는 regression acceptance로 닫힌다.
- callback contract drift가 green test 뒤에 숨지 않는다.
- reverse feedback chain이 difficulty-only shortcut이 아니라 semantic-preserving contract로 바뀐다.

## 10. Out of Scope Notes

- Stage4 scoring rubric 재정의
- writer prompt 문체 / 내용 quality overhaul
- unrelated Stage0 / desktop / packaging 수정
