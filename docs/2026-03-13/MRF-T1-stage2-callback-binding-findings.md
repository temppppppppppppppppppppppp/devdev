# [MRF-T1] Stage2 Callback Binding Findings

> 작성일: 2026-03-13
> 상태: `PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-retry-feedback-detail-full-survey-audit-order.md`
> 실행 요약: `PASS1 후보 4건 -> PASS2 제거 2건 -> 최종 2건`

---

## 조사 범위

- `main_a.py`
  - `_generate_structured_arc_feedback()`
  - `_generate_reverse_feedback_stage3_to_2()`
  - `_generate_reverse_feedback_stage4_to_2()`
  - `_build_strong_kind_feedback()`
  - `_build_minimal_arc_context()`
  - `_build_focused_context()`
  - `_analyze_rejection_pattern_v60()`
  - `_get_adaptive_feedback_intensity()`
  - `_generate_arc_context_v60()`
- `modules/core/stage2_context.py`
- `modules/core/stage2_orchestrator.py`
- 실제 Stage 2 consumer 확인
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_finalizer.py`

## 필수 근거

- 읽은 테스트:
  - `tests/test_stage2_context.py`
  - `tests/test_stage2_preflight.py`
  - `tests/test_stage2_preflight_helpers.py`
  - `tests/test_stage2_validation_pipeline.py`
  - `tests/test_stage2_finalizer.py`
  - `tests/integration/test_pipeline_smoke.py`
  - `tests/e2e/test_l3_golden_route.py`
  - `tests/e2e/test_l3_stage2_realproject.py`
- 읽은 참조 문서:
  - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
  - `docs/2026-03-13/OPUS-TF-5terminal-deep-dive-master-audit-order.md`
  - `docs/2026-03-13/S-T2-cross-stage-root-cause-deep-dive-findings.md`
- 실행 검증:
  - `pytest -q tests/test_stage2_context.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage2_validation_pipeline.py tests/test_stage2_finalizer.py tests/integration/test_pipeline_smoke.py`
  - 결과: `163 passed`

## PASS 기록

- PASS 1:
  - 후보 1: `Stage2Context.from_app()`는 retry-feedback callback 전부를 optional `None`으로 허용하는데, `Stage2Orchestrator`가 `analyze_rejection_pattern_v60`를 무가드 호출한다.
  - 후보 2: `generate_reverse_feedback_stage3_to_2`와 context helper들이 consumer마다 다른 fallback 규약을 가져 callback 누락 시 조용한 기능 축소를 만든다.
  - 후보 3: `main_a.py` export 이름과 `stage2_context.py`가 기대하는 이름이 현재 어긋나 있다.
  - 후보 4: 현재 call site와 wrapper 시그니처가 이미 어긋나 있다.
- PASS 2:
  - 후보 3 제거: 현재 이름 매핑은 정확히 일치한다. `stage2_context.py:246-256`의 `getattr(app, "_...")`와 `main_a.py:659-760` wrapper 이름은 현재 코드 기준 mismatch가 없다.
  - 후보 4 제거: 현재 call site keyword와 wrapper 파라미터 이름도 맞는다. 즉시 시그니처 붕괴는 확인되지 않았다.
- PASS 3:
  - callback bundle의 required/optional 경계가 실제 consumer와 맞지 않는 2건만 `MRF-T1-*`로 채택했다.

## Finding Ledger

| ID | Severity | 상태 | 파일/함수 | 요약 |
|----|----------|------|-----------|------|
| MRF-T1-001 | P1 | confirmed | `modules/core/stage2_context.py::Stage2Context.from_app`, `modules/core/stage2_orchestrator.py` | `analyze_rejection_pattern_v60`는 binding 계층에서 optional인데 retry consumer는 required처럼 호출해 callback drift 시 Stage 2 retry path가 바로 깨진다 |
| MRF-T1-002 | P2 | confirmed | `modules/core/stage2_context.py::Stage2Context.from_app`, `modules/core/stage2_preflight.py`, `modules/core/stage2_validation_pipeline.py`, `modules/core/stage2_finalizer.py` | 동일 callback bundle이 consumer별로 hard-call, broad-except, empty-string fallback으로 갈라져 누락 시 silent degradation과 테스트 맹점을 만든다 |

## Final Findings

### [MRF-T1-001] P1 - `analyze_rejection_pattern_v60`는 optional binding인데 Stage 2 retry loop는 required처럼 호출한다

1. ID
   - `MRF-T1-001`
2. Severity
   - `P1`
3. 현상 요약
   - `Stage2Context.from_app()`는 `analyze_rejection_pattern_v60`를 `getattr(app, "_analyze_rejection_pattern_v60", None)`로 주입한다.
   - `tests/test_stage2_context.py`는 callback 미구현 app도 `from_app()`가 정상 동작하고 `None`을 저장하는 계약을 승인한다.
   - 그러나 `Stage2Orchestrator` retry loop는 `attempt >= 1`이고 `stage_rejection_history`가 존재하면 `self.ctx.analyze_rejection_pattern_v60(...)`를 가드 없이 직접 호출한다.
   - 따라서 `_analyze_rejection_pattern_v60` 이름 변경, 누락, 비호환 주입이 생기면 첫 REJECT 이후 retry path에서 즉시 `TypeError` 계열로 중단될 수 있다.
4. 코드 근거
   - `main_a.py:760-820` 현재 export 자체는 존재하지만, `Stage2Context`는 이를 required로 선언하지 않는다.
   - `modules/core/stage2_context.py:150-152` `analyze_rejection_pattern_v60=None`, `get_adaptive_feedback_intensity=None`, `generate_arc_context_v60=None`
   - `modules/core/stage2_context.py:201` `self.analyze_rejection_pattern_v60 = analyze_rejection_pattern_v60`
   - `modules/core/stage2_context.py:254` `analyze_rejection_pattern_v60=getattr(app, "_analyze_rejection_pattern_v60", None)`
   - `modules/core/stage2_orchestrator.py:487-498` retry 이력 존재 시 `self.ctx.analyze_rejection_pattern_v60(arc_rejections, global_arc_no)`를 무가드 호출
   - `tests/test_stage2_context.py:128-139` callback 없는 app에서도 `from_app()`가 `None`으로 통과함을 확인
   - `tests/test_stage2_context.py:156-163` `Stage2Orchestrator.ctx`는 callback 없는 `app_mock`에서 자동 빌드만 확인하고 retry consumer와 묶지 않는다
5. downstream 영향 경계
   - Stage 2에서 한 번이라도 REJECT가 기록된 Arc의 다음 retry 시점부터 영향이 나타난다.
   - 영향 범위는 `pattern_analysis` 주입이 아니라 retry loop 자체다. 해당 callback drift가 생기면 현재 Arc 재시도 루프가 중단될 수 있다.
   - 결과적으로 반복 REJECT Arc가 batch 진행을 멈추거나 Stage 2 전체 회복 경로를 깨뜨릴 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - 실행한 관련 테스트는 모두 통과했다 (`163 passed`).
   - 하지만 `tests/test_stage2_context.py`는 callback 존재/부재 저장만 본다.
   - `tests/e2e/test_l3_golden_route.py:244-253`, `tests/e2e/test_l3_stage2_realproject.py:220-229`도 실제 `main_a.py` export 대신 lambda stub를 주입해 contract drift를 가리지 못한다.
   - `from_app()`로 만든 ctx에서 `stage_rejection_history`를 채운 뒤 retry path를 태우는 회귀 테스트는 없다.
7. 기존 문서와의 중복 여부
   - duplicate status: `related-but-new-callback-surface`
   - `docs/2026-03-13/S-T2-cross-stage-root-cause-deep-dive-findings.md:102-104`는 optional callback 패턴 일반론만 언급했고, `analyze_rejection_pattern_v60`가 실제 retry consumer에서 hard requirement처럼 호출된다는 구체 surface는 닫지 않았다.
8. 권장 후속 조치
   - `Stage2Context`에 retry path 필수 callback을 명시적으로 분리하거나, `from_app()` 시점에 fail-fast validation을 추가한다.
   - 최소한 `modules/core/stage2_orchestrator.py:487-498`에 `callable(...)` guard와 명시적 fallback 또는 진단 로그를 추가한다.
   - 회귀 테스트를 추가한다: callback 없는 `from_app()` ctx + populated `stage_rejection_history` + retry 진입 시 hard crash가 아닌 명시적 fallback/diagnostic이 발생하는지 검증.

### [MRF-T1-002] P2 - 동일 callback bundle이 consumer마다 다른 fallback 규약을 가져 누락 시 조용한 기능 축소를 만든다

1. ID
   - `MRF-T1-002`
2. Severity
   - `P2`
3. 현상 요약
   - `Stage2Context.from_app()`는 retry-feedback callback 묶음을 전부 optional slot으로 저장한다.
   - 하지만 실제 consumer는 동일 묶음을 세 가지 방식으로 다룬다.
   - `generate_reverse_feedback_stage3_to_2`는 `try/except` 안에서 무가드 호출되어 누락 시 기능이 사라지고 오류는 `audit_event`가 있을 때만 남는다.
   - `build_minimal_arc_context`, `generate_arc_context_v60`, `generate_structured_arc_feedback`, `build_strong_kind_feedback`, `build_focused_context`, `get_adaptive_feedback_intensity`는 empty string 또는 축약 context fallback으로 계속 진행한다.
   - 즉, callback rename 또는 binding 누락이 생겨도 어떤 항목은 crash, 어떤 항목은 조용한 비활성, 어떤 항목은 text fallback으로 처리되어 표면 계약이 일관되지 않다.
4. 코드 근거
   - `modules/core/stage2_context.py:142-152`, `246-256` callback bundle 전체를 optional `getattr(..., None)`로 바인딩
   - `modules/core/stage2_preflight.py:882-887` `build_minimal_arc_context` 부재 시 `enhanced_context[:15000]` 폴백
   - `modules/core/stage2_preflight.py:895-920` `generate_reverse_feedback_stage3_to_2`는 무가드 호출 후 broad `except Exception`; `audit_event`가 없으면 실질적으로 silent drop
   - `modules/core/stage2_preflight.py:924-945` `generate_reverse_feedback_stage4_to_2`는 truthy check만 하고 없으면 그냥 미주입
   - `modules/core/stage2_validation_pipeline.py:486-489`, `877-904` `get_adaptive_feedback_intensity`, `generate_structured_arc_feedback`, `build_strong_kind_feedback`, `build_focused_context` 부재 시 빈 문자열로 계속 진행
   - `modules/core/stage2_finalizer.py:1155-1156`, `1307-1311` `generate_arc_context_v60`, `get_adaptive_feedback_intensity` 부재 시 조용히 축소 진행
5. downstream 영향 경계
   - Stage 3 실패 누적이 있어도 Stage 2가 구조적 역방향 피드백을 받지 못할 수 있다.
   - retry focus mode가 `minimal arc context` 대신 잘린 text fallback으로 내려앉을 수 있다.
   - continuity advisory, retry intensity, refined arc context가 빠져도 파이프라인은 green으로 지나가며 품질만 떨어질 수 있다.
   - 즉, batch가 멈추지 않아도 retry-feedback semantics가 약화된 채 진행될 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage2_preflight.py:65-66`, `tests/test_stage2_preflight_helpers.py:55-60`, `tests/test_stage2_validation_pipeline.py:32-33,289-290`, `tests/test_stage2_finalizer.py:34-37`는 거의 모두 `MagicMock`으로 callback을 선주입한다.
   - `tests/test_stage2_preflight_helpers.py:699-700`은 callback이 호출됐는지만 보고, callback이 없을 때 fallback이 의도된 의미를 보존하는지는 보지 않는다.
   - `tests/test_stage2_context.py:91-115`는 일부 callback이 바운드되거나 `None`인지 확인할 뿐, 9개 callback 전부의 required/optional 등급이나 consumer별 fallback 일관성을 잠그지 않는다.
   - `tests/e2e/test_l3_golden_route.py:244-253`, `tests/e2e/test_l3_stage2_realproject.py:220-229`는 다수 callback을 lambda stub로 대체해 실제 `main_a.py` export binding을 검증하지 않는다.
7. 기존 문서와의 중복 여부
   - duplicate status: `related-but-new-callback-surface`
   - 기존 deep dive는 optional callback 패턴 일반론과 write-back 유지 여부를 봤지만, 이번 항목처럼 retry-feedback bundle 안에서 fallback 규약이 제각각이라 semantic drift를 숨긴다는 surface는 별도 정리되지 않았다.
8. 권장 후속 조치
   - retry-feedback callback bundle에 대해 `required`, `optional-with-fallback`, `optional-observability-only`를 명시적으로 나눈다.
   - `Stage2Context.from_app()` 또는 별도 validator에서 누락 callback ledger를 만들고, Stage 2 진입 전에 명시적으로 출력한다.
   - 회귀 테스트를 추가한다: callback 누락/rename 시 `retry feedback amputated but green` 상태가 되지 않도록, fallback 결과와 audit 진단을 함께 검증한다.

## Rejected Candidates

| 후보 | PASS2 판정 | 근거 |
|------|------------|------|
| `main_a.py` export 이름과 `Stage2Context.from_app()` 기대 이름이 현재 이미 어긋나 있다 | removed | `main_a.py:659-760`의 `_build_*`, `_generate_*`, `_get_*`, `_analyze_*` 이름과 `modules/core/stage2_context.py:246-256`의 `getattr(app, "_...")` 키는 현재 코드 기준 정확히 일치한다 |
| 현재 consumer call site와 wrapper 시그니처가 이미 충돌한다 | removed | `modules/core/stage2_validation_pipeline.py:877-904`, `modules/core/stage2_preflight.py:882-905`, `modules/core/stage2_orchestrator.py:495`, `modules/core/stage2_finalizer.py:1155-1156,1307-1308`의 호출 인자 이름은 `main_a.py` wrapper 정의와 현재는 맞는다 |

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `from_app()` auto-build ctx의 retry callback 필수성 | 테스트 공백 | callback 일부가 없는 app으로 `Stage2Orchestrator.ctx`를 자동 생성한 뒤 실제 retry path를 태워 hard fail / fallback / audit 진단을 확인하는 회귀 테스트 |
| silent degradation의 사용자 가시성 | 관측성 공백 | `audit_event`가 없는 환경에서도 callback amputated 상태가 UI/log에 드러나는지 검증 |
| 실제 `main_a.py` export와 Stage2 consumer 결합 테스트 | 계약 공백 | lambda/MagicMock이 아닌 실제 `SovereignApp` bound method를 이용해 callback bundle 이름, callability, fallback 분류를 통합 검증 |

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- `PASS1 -> PASS2 -> PASS3` 요약 포함
