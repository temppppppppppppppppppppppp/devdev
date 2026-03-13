# [MRF-T5] Consumer Tests / Regression Findings

> 작성일: 2026-03-13
> 상태: `executed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-retry-feedback-detail-full-survey-audit-order.md`

코드 수정이나 테스트 수정 없이, retry-feedback consumer 표면의 테스트/문서 회귀 방어력을 점검했다.

---

## 조사 범위

- `tests/test_stage2_context.py`
- `tests/test_prompt_builder.py`
- 관련 보강 근거
  - `tests/test_feedback_system.py`
  - `tests/e2e/test_l3_stage2_realproject.py`
  - `tests/e2e/test_l3_golden_route.py`
  - `modules/core/stage2_context.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/prompt_builder.py`
  - `main_a.py`
  - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
  - `docs/2026-03-13/OPUS-TF-5terminal-deep-dive-master-audit-order.md`

## Executive Summary

- 확정 findings: `3`
- Severity 합계: `P2 3건`
- 핵심 결론:
  - pure helper 자체는 일부 테스트가 있다.
  - 그러나 `main_a.py -> Stage2Context -> Stage2 consumer` 경계의 callback/wrapper contract는 여전히 녹색 테스트로 충분히 잠기지 않았다.
  - 특히 `analyze_rejection_pattern_v60`와 app-bound `generate_arc_context_v60`는 consumer/integration에서 사실상 우회되고 있다.

## PASS 기록

- PASS 1: consumer test와 관련 helper 표면 전수 수집 완료
- PASS 2: pure helper test와 consumer/integration test를 분리해 오탐 제거 완료
- PASS 3: `MRF-T5-001` ~ `MRF-T5-003` 3건 확정

---

## Pass 1 - Candidate Facts

### 후보 1

- `Stage2Context.from_app()`는 retry-feedback callback을 다수 노출하지만, `tests/test_stage2_context.py`는 그중 일부만 핀 고정한다.

### 후보 2

- `PromptBuilder.generate_arc_context_v60()`의 주 경로는 app/state_extractor/cache/audit_event에 의존하지만, `tests/test_prompt_builder.py`는 `app=None` 폴백만 확인한다.

### 후보 3

- `main_a.py` 로컬 helper `_analyze_rejection_pattern_v60()`, `_normalize_rejection_reason()`, `_get_rejection_fix_guide()`에 대한 직접 테스트가 보이지 않는다.

### 후보 4

- retry-feedback semantics 전체가 미테스트처럼 보였으나, `tests/test_feedback_system.py`가 pure feedback helper 다수를 실제로 검증한다.

### 후보 5

- `generate_arc_context_v60()` 전체 미테스트처럼 보였으나, 최소한 `app=None` 폴백은 이미 테스트된다.

---

## Pass 2 - Cross Validation

### 제거 1: "feedback helper semantics 전체 미테스트"

- 기각.
- `tests/test_feedback_system.py:211-580`는 `build_strong_kind_feedback`, `build_focused_context`, `build_minimal_arc_context`, `generate_structured_arc_feedback`, `generate_reverse_feedback_stage4_to_2`, `get_adaptive_feedback_intensity`, `simplify_prompt_for_retry`를 직접 검증한다.
- 따라서 문제는 helper 내부 로직 전부가 아니라, `main_a` wrapper 및 consumer 경계가 잠기지 않은 점이다.

### 제거 2: "generate_arc_context_v60 완전 미테스트"

- 기각.
- `tests/test_prompt_builder.py:459-468`는 `app=None`일 때 `generate_arc_context_v60()`가 문자열을 반환하는 최소 폴백 동작을 검증한다.
- 다만 app-bound 주 경로와 side effect는 여전히 미검증이므로 retained 범위를 좁혀 유지한다.

---

## Pass 3 - Final Findings

### [MRF-T5-001]

1. ID  
   `MRF-T5-001`
2. Severity  
   `P2`
3. 현상 요약  
   `Stage2Context.from_app()`의 retry-feedback callback export 면적은 넓지만, consumer test는 그중 일부 이름 존재만 확인한다. 결과적으로 callback rename/누락/signature drift가 생겨도 현재 테스트는 녹색으로 남을 가능성이 높다.
4. 코드 근거  
   - callback 표면 선언/주입: `modules/core/stage2_context.py:31-43`, `modules/core/stage2_context.py:74-95`, `modules/core/stage2_context.py:193-203`, `modules/core/stage2_context.py:246-256`
   - 실제 consumer 사용:
     - `modules/core/stage2_validation_pipeline.py:877-910`
     - `modules/core/stage2_preflight.py:882-931`
     - `modules/core/stage2_orchestrator.py:487-498`
   - 현재 테스트는 아래 3개 retry-feedback 콜백만 직접 고정:
     - `tests/test_stage2_context.py:91-106`
     - `tests/test_stage2_context.py:108-115`
   - 이 테스트가 놓치는 callback:
     - `generate_structured_arc_feedback`
     - `generate_reverse_feedback_stage3_to_2`
     - `build_strong_kind_feedback`
     - `build_minimal_arc_context`
     - `analyze_rejection_pattern_v60`
     - `get_adaptive_feedback_intensity`
5. downstream 영향 경계  
   Stage 2 retry 경로 전체가 영향권이다. ContinuityInspector advisory, focus mode 최소 컨텍스트, Stage3->2 reverse feedback, retry intensity, repeated reject 패턴 주입이 조용히 비활성화되거나 의미 약화될 수 있다.
6. 현재 테스트 근거 또는 테스트 부재  
   - 있음: `tests/test_stage2_context.py:91-115`는 일부 callback 존재/None 기본값만 확인한다.
   - 부재: 위 6개 callback의 binding 완전성, parameter contract, consumer-visible semantics는 확인하지 않는다.
7. 기존 문서와의 중복 여부  
   `related-but-new-callback-surface`  
   이유: 일반적인 semantic drift 경고는 다른 감리 문서에도 있으나, `main_a.py retry-feedback callback -> Stage2Context` 표면 자체의 테스트 blind spot은 이번 트랙의 신규 책임 경계다.
8. 권장 후속 조치  
   `tests/test_stage2_context.py`를 callback map 기반으로 확장해 retry-feedback callback 전량을 핀 고정하고, 최소 1개는 실제 인자 shape까지 검증한다.

### [MRF-T5-002]

1. ID  
   `MRF-T5-002`
2. Severity  
   `P2`
3. 현상 요약  
   `generate_arc_context_v60`의 실제 app-bound 경로는 `state_extractor`, `_cumulative_state_cache`, `_audit_event`에 의존하지만, 현재 consumer/integration tests는 이 경로를 사실상 실행하지 않는다.
4. 코드 근거  
   - 주 경로: `modules/core/prompt_builder.py:549-595`
   - `main_a` wrapper: `main_a.py:752-754`
   - Stage 2 consumer 사용: `modules/core/stage2_orchestrator.py:276-305`
   - 현재 단위 테스트는 no-app 폴백만 확인: `tests/test_prompt_builder.py:459-468`
   - e2e도 실제 helper 대신 no-op lambda 주입:
     - `tests/e2e/test_l3_stage2_realproject.py:219-229`
     - `tests/e2e/test_l3_golden_route.py:248-253`
5. downstream 영향 경계  
   `last_refined_context` 품질과 batch enrichment의 `transfused_history`가 직접 영향받는다. 캐시 키 drift, audit event 누락, state_extractor fallback 오작동이 생겨도 현재 회귀 테스트는 이를 잡지 못한다.
6. 현재 테스트 근거 또는 테스트 부재  
   - 있음: `tests/test_prompt_builder.py:459-468`는 fallback 문자열 반환만 확인한다.
   - 부재: app-bound `state_extractor` 호출, cache hit/miss, `_audit_event` side effect, 예외 시 fallback 전환은 검증되지 않는다.
7. 기존 문서와의 중복 여부  
   `related-but-new-callback-surface`  
   이유: PromptBuilder pure helper coverage와는 별개로, `main_a -> PromptBuilder -> Stage2 consumer` app-bound contract 미검증이 핵심이다.
8. 권장 후속 조치  
   mock `state_extractor`와 `_audit_event`를 가진 app로 `PromptBuilder` 또는 `main_a._generate_arc_context_v60()`를 호출해
   - cache miss -> extract 호출
   - cache hit -> extract 미호출
   - 예외 -> fallback + audit 기록
   를 각각 잠그는 테스트를 추가한다.

### [MRF-T5-003]

1. ID  
   `MRF-T5-003`
2. Severity  
   `P2`
3. 현상 요약  
   repeated reject triage의 핵심인 `_analyze_rejection_pattern_v60()`, `_normalize_rejection_reason()`, `_get_rejection_fix_guide()`는 `main_a.py` 로컬 helper인데, 현재 테스트 스위트에서 직접 검증되지 않는다. integration 쪽에서도 실 helper 대신 빈 lambda가 주입된다.
4. 코드 근거  
   - helper 구현: `main_a.py:760-861`
   - 실제 consumer 사용: `modules/core/stage2_orchestrator.py:487-498`
   - 테스트 스위트의 retry surface 대체:
     - `tests/e2e/test_l3_stage2_realproject.py:227-229`
     - `tests/e2e/test_l3_golden_route.py:251-253`
   - 대조군: pure feedback helper는 `tests/test_feedback_system.py:211-580`에서 커버되지만, 위 `main_a` 로컬 triage helper는 아니다.
5. downstream 영향 경계  
   Stage 2 재시도 누적 시 어떤 failure bucket이 상위에 노출되는지, 어떤 수정 가이드가 prepend되는지가 달라진다. locale 표현 차이 또는 heuristic drift가 생기면 retry guidance가 잘못 좁혀질 수 있다.
6. 현재 테스트 근거 또는 테스트 부재  
   - 직접 테스트 부재.
   - repo 내 test reference는 사실상 e2e lambda stubs뿐이다.
7. 기존 문서와의 중복 여부  
   `none`
8. 권장 후속 조치  
   `_analyze_rejection_pattern_v60()` 계열을 direct unit test 또는 extract된 pure helper test로 분리해
   - 한글/영문 reason variant
   - normalization bucket
   - fix guide 매핑
   - specific_issue 포함 문자열
   을 각각 고정한다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| retry-feedback 통합 중복 판정 | provisional | T1~T4 결과 문서가 아직 비실행 상태라 최종 duplicate ledger는 통합본 단계에서 재확정 필요 |
| runtime artifact 기반 semantic 검증 | partial | 현재 e2e가 핵심 helper를 lambda로 대체하므로 실제 `main_a` retry-feedback 출력이 런타임에서 어떻게 소비되는지 별도 artifact 필요 |

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| MRF-T5-001 | P2 | retained | `Stage2Context.from_app`, `tests/test_stage2_context.py` | callback export 면적 대비 test pinning 범위가 너무 좁음 |
| MRF-T5-002 | P2 | retained | `PromptBuilder.generate_arc_context_v60`, `main_a._generate_arc_context_v60` | app-bound 주 경로가 unit/e2e에서 우회됨 |
| MRF-T5-003 | P2 | retained | `main_a._analyze_rejection_pattern_v60` 계열 | repeated reject triage helper에 직접 테스트가 없음 |

## PASS 요약

- PASS1 후보 `5건`
- PASS2 제거 `2건`
- PASS3 확정 `3건`

## 마감 체크

- 코드 근거 포함: `yes`
- downstream 영향 경계 포함: `yes`
- 현재 테스트 근거 또는 테스트 부재 포함: `yes`
- 기존 문서와의 중복 여부 포함: `yes`
- 수동 코드 수정 금지 준수: `yes`
