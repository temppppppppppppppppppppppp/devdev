# main_a Live Wiring Contract Detail Full Survey Audit Order

> 작성일: 2026-03-13
> 트랙: `main_a.py` real-app live wiring blind spot audit
> 상태: `execution-ready`
> 조사 현황: `조사 완료`
> 목적: `main_a.py`가 실제 `SovereignApp` bound method와 runtime context를 통해 Stage 2/3/4 consumer에 연결되는 live wiring contract를 전면 전량 조사한다.
> 방식: `5-terminal 병렬`, 각 터미널 자체 `3PASS`, 통합본 `3PASS 재감리`

---

## 0. 문서 역할

- 이 문서는 `main_a.py` real-app live wiring 조사 오더다.
- 이 문서는 코드 수정 오더가 아니다.
- 조사 단계에서 코드 직접 수정은 금지한다.
- 모든 문서는 `UTF-8` 고정이다. 물음표 치환 흔적이나 깨진 한글이 보이면 즉시 중단하고 인코딩 이상으로 기록한다.
- 결과 문서가 채워지기 전까지는 어떤 finding도 확정으로 간주하지 않는다.

---

## 1. 왜 별도 트랙이 필요한가

기존 문서들은 control plane, retry-feedback, facade shim, persistence helper를 각각 다뤘다. 그러나 아래 표면은 아직 `실제 SovereignApp bound method -> context -> consumer` 경계 관점의 독립 오더로 잠기지 않았다.

- `Stage2Context.from_app()`, `Stage3Context.from_app()`, `Stage4Context.from_app()`가 실제 `main_a.py` surface와 맞물리는 방식
- `main_a.py` export 이름, callability, signature, fallback class가 spec-less `MagicMock` 테스트 뒤에 숨는 영역
- stage consumer test는 녹색인데 real app wiring은 drift할 수 있는 경계
- `protocol -> facade -> context slot -> consumer` 체인이 이름상 통과하지만 실제 runtime semantics는 잠기지 않은 영역
- `lambda`, `MagicMock`, source-string assertion 위주 테스트가 real-app integration을 대체하고 있는 영역

관련 문서:

- `docs/2026-03-13/main_a-facade-shim-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-retry-feedback-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-persistence-narrative-detail-full-survey-audit-order.md`
- `docs/2026-03-13/MFS-T2-state-service-validation-findings.md`
- `docs/2026-03-13/MRF-T1-stage2-callback-binding-findings.md`
- `docs/2026-03-13/MPN-T5-consumer-tests-legacy-contract-findings.md`

본 트랙은 helper 내부 알고리즘 재감사가 아니라, `real app wiring` 자체의 계약과 regression 위험을 조사하는 데 목적이 있다.

---

## 2. 공통 조사 규약

### 2.1 조사 모드

- `static`
- `read-only`
- `code-and-test verification`
- `source-report cross-check`
- `UTF-8 only`

### 2.2 병렬 실행 규칙

- 터미널 `T1` ~ `T5`는 병렬 수행을 전제로 한다.
- 각 터미널은 자기 결과 문서만 작성한다.
- 다른 터미널 결과 문서를 수정하지 않는다.
- 코드 직접 수정, 임시 patch, test 수정은 금지한다.
- 조사 중 발견한 의심 항목은 PASS 1 후보로만 기록하고 PASS 2 전 확정하지 않는다.

### 2.3 3PASS 프로토콜

#### PASS 1 - 표면 수집

- 담당 stage context, consumer file, 관련 test, 기존 문서를 전부 읽는다.
- 후보 finding을 `HIGH`, `MED`, `LOW` 확신도로 분류한다.
- 기존 문서와 겹치는 표면이면 일단 `duplicate candidate`로 표시한다.

#### PASS 2 - 교차 검증

- 코드 근거, 테스트 근거, 문서 근거를 함께 대조한다.
- 기존 문서에서 이미 닫힌 항목은 재오픈하지 않는다.
- 다만 기존 문서가 helper 자체나 stage 내부 문제를 다뤘고, 이번 항목이 `real app wiring contract` 문제면 신규 finding으로 유지 가능하다.

#### PASS 3 - 최종 확정

- 확정 항목만 `[MLW-TN-SEQ]` 형식으로 채택한다.
- 문서 말미에 `PASS1 후보 -> PASS2 제거 -> PASS3 확정` 요약을 남긴다.
- 미확정 사항은 `coverage gap` 또는 `open question`으로 분리한다.

### 2.4 finding 기록 형식

각 finding은 아래 8개 필드를 반드시 가진다.

1. ID
2. Severity (`P0`, `P1`, `P2`, `P3`)
3. 현상 요약
4. 코드 근거
5. downstream 영향 경계
6. 현재 테스트 근거 또는 테스트 부재
7. 기존 문서와의 중복 여부
8. 권장 후속 조치

### 2.5 Severity 기준

- `P0`: real wiring drift로 production path가 즉시 실패하거나 잘못된 경로로 진행되는데 테스트는 초록으로 남는 경우
- `P1`: required callback/signature drift, 잘못된 slot binding, 잘못된 app surface로 stage 결과가 의미 있게 오염되는 경우
- `P2`: optional callback/fallback drift, spec-less mock 의존, real-app path 미잠금, protocol-semantic mismatch
- `P3`: 관측성, naming drift, test realism 저하, 문서-코드 미세 불일치

---

## 3. 조사 범위 지도

| Terminal | 초점 | 핵심 범위 |
|---------|------|-----------|
| T1 | Stage2 real-app binding | `main_a.py -> Stage2Context.from_app() -> Stage2 consumer` |
| T2 | Stage3 real-app binding | `main_a.py -> Stage3Context.from_app() -> Stage3 consumer` |
| T3 | Stage4 real-app binding | `main_a.py -> Stage4Context/Builder -> Stage4 consumer` |
| T4 | Protocol / facade / runtime slot bridge | `app_services.py`, service facade, context slot, runtime bridge |
| T5 | Test realism / fake app regression | `MagicMock`, fake app, source-string assertion, real wiring blind spot |

---

## 4. Terminal 1 - Stage2 Real-App Binding

### 담당 범위

- `main_a.py`
  - Stage2에 export하는 bound method 전반
- 직접 downstream
  - `modules/core/stage2_context.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_finalizer.py`

### 핵심 검사 포인트

1. `Stage2Context.from_app()`가 실제 `SovereignApp` surface와 이름, callability, signature를 정확히 맞추는가
2. optional callback과 required callback의 경계가 `main_a.py`와 consumer 사이에서 일관적인가
3. `None`, lambda, `MagicMock`으로 통과하는 테스트가 real-app path를 대체하고 있지 않은가
4. retry-feedback, validation, audit 계열 bound method가 실제 app path에서 함께 살아 있는가
5. Stage2 consumer가 `ctx`와 `app`를 혼용해 서로 다른 source를 보지 않는가

### 필수 근거

- `tests/test_stage2_context.py`
- `tests/test_stage2_validation_pipeline.py`
- `tests/test_stage2_finalizer.py`
- `modules/core/stage2_context.py`
- `modules/core/stage2_orchestrator.py`

### 산출물

- `docs/2026-03-13/MLW-T1-stage2-real-app-binding-findings.md`

---

## 5. Terminal 2 - Stage3 Real-App Binding

### 담당 범위

- `main_a.py`
  - Stage3에 export하는 bound method 전반
- 직접 downstream
  - `modules/core/stage3_context.py`
  - `modules/core/stage3_orchestrator.py`

### 핵심 검사 포인트

1. `Stage3Context.from_app()` slot mapping이 실제 `main_a.py` facade 이름과 정확히 대응하는가
2. blueprint, arc context, audit, persistence helper가 real app path에서 함께 유효한가
3. Stage3 테스트가 `MagicMock` auto-attribute에 기대어 실제 app surface 누락을 놓치지 않는가
4. Stage3 consumer가 `main_a.py` facade semantics와 service semantics를 섞어 쓰지 않는가
5. resume / retry / canary 성격의 Stage3 진입 경로가 서로 다른 wiring을 기대하지 않는가

### 필수 근거

- `tests/test_stage3_orchestrator.py`
- `tests/e2e/test_l3_stage3_smoke.py`
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`

### 산출물

- `docs/2026-03-13/MLW-T2-stage3-real-app-binding-findings.md`

---

## 6. Terminal 3 - Stage4 Real-App Binding

### 담당 범위

- `main_a.py`
  - Stage4에 export하는 bound method 전반
- 직접 downstream
  - `modules/core/stage4_context.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/stage4_orchestrator.py`

### 핵심 검사 포인트

1. `Stage4Context.from_app()`와 `Stage4ContextBuilder`가 실제 app surface를 같은 의미로 바라보는가
2. audit, summary, guidance, narrative helper가 success / failure / interrupt 경로에서 같은 source를 바라보는가
3. Stage4 테스트가 real app 대신 callback mock만 검증해 wiring drift를 놓치지 않는가
4. builder path와 round path가 서로 다른 helper source를 보지 않는가
5. Stage4 manual injection과 from-app path가 contract 차이를 만들지 않는가

### 필수 근거

- `tests/test_stage4_context.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_run_stage4_canary.py`
- `modules/core/stage4_context.py`

### 산출물

- `docs/2026-03-13/MLW-T3-stage4-real-app-binding-findings.md`

---

## 7. Terminal 4 - Protocol / Facade / Runtime Slot Bridge

### 담당 범위

- `modules/protocols/app_services.py`
- `modules/core/services/state_service.py`
- `modules/core/services/audit_service.py`
- `modules/core/services/project_service.py`
- context `from_app()` helper 전반

### 핵심 검사 포인트

1. protocol conformance가 이름상 통과하지만 real runtime slot semantics는 어긋나지 않는가
2. service facade와 `main_a.py` bound method가 서로 다른 signature / fallback 규약을 갖지 않는가
3. context slot이 service protocol보다 넓거나 좁아 runtime bridge drift를 만들지 않는가
4. real `SovereignApp` path와 `app_services` protocol이 같은 contract를 표현하는가
5. `from_app()` helper가 실제 service/protocol 변화에 둔감하게 초록으로 남지 않는가

### 필수 근거

- `tests/test_protocols_services.py`
- `tests/test_audit_service.py`
- `tests/test_state_service.py`
- `modules/protocols/app_services.py`

### 산출물

- `docs/2026-03-13/MLW-T4-protocol-facade-runtime-bridge-findings.md`

---

## 8. Terminal 5 - Test Realism / Fake App Regression

### 담당 범위

- `tests/` 전반의 `MagicMock`, lambda, fake app 기반 slot/binding 테스트
- source-string assertion 계열 회귀 테스트
- 기존 감리 문서와 현재 wiring surface

### 핵심 검사 포인트

1. spec 없는 `MagicMock` fixture가 실제 app surface drift를 숨기지 않는가
2. lambda 주입이 real bound method contract를 대체해 false green을 만들지 않는가
3. source-string assertion이 wiring contract 대신 코드 모양만 잠그고 있지 않은가
4. 기존 감리 문서가 실제 production binding이 아니라 test harness 구조만 보고 결론 내린 지점은 없는가
5. 최종 통합 시 `related-but-new-live-wiring-surface`와 기존 mock-realism finding을 분리할 수 있는가

### 필수 근거

- `tests/test_stage2_context.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context.py`
- `tests/test_resume_status.py`
- `docs/2026-03-13/MFS-T5-protocol-tests-regression-findings.md`

### 산출물

- `docs/2026-03-13/MLW-T5-test-realism-regression-findings.md`

---

## 9. 명시적 제외 범위

아래는 참조 근거로만 사용하고, 이번 조사 본체로 재포장하지 않는다.

- Stage 2/3/4 내부 알고리즘 심층
- one-stop / frontier-lag / lookahead
- desktop IPC 세부 구현
- 실제 remediation patch 작성
- helper 내부 로직의 품질 평가 자체

---

## 10. 통합 산출물 규칙

### 터미널 결과 문서

- `docs/2026-03-13/MLW-T1-stage2-real-app-binding-findings.md`
- `docs/2026-03-13/MLW-T2-stage3-real-app-binding-findings.md`
- `docs/2026-03-13/MLW-T3-stage4-real-app-binding-findings.md`
- `docs/2026-03-13/MLW-T4-protocol-facade-runtime-bridge-findings.md`
- `docs/2026-03-13/MLW-T5-test-realism-regression-findings.md`

### 통합 문서

- `docs/2026-03-13/main_a-live-wiring-contract-detail-consolidated-findings.md`
- `docs/2026-03-13/main_a-live-wiring-contract-detail-consolidated-findings-3pass-reaudit.md`

### 중복 처리 규칙

- 기존 facade, retry-feedback, persistence 문서에서 이미 닫힌 항목은 재오픈 금지
- 단, `real app wiring contract` 자체가 다른 책임 경계를 가지면 신규 `MLW-*` finding 가능
- 신규 finding에는 아래 중 하나를 반드시 적는다
  - `none`
  - `related-but-new-live-wiring-surface`
  - `already-covered-do-not-reopen`

---

## 11. 실행 완료 판정

아래를 모두 만족해야 본 오더가 닫힌다.

1. T1 ~ T5 결과 문서가 모두 존재한다.
2. 각 문서가 `PASS1 -> PASS2 -> PASS3` 요약을 가진다.
3. 각 finding이 코드 근거, 테스트 근거, downstream 경계, 중복 여부를 모두 가진다.
4. 통합본이 터미널별 ledger와 severity 합계를 재구성한다.
5. 통합본 3PASS 재감리가 최종 오탐 제거 여부와 SSOT 승격 가능성을 명시한다.

---

## 12. 초기 상태

- 본 오더 문서는 `execution-ready`다.
- 결과 문서와 통합 문서는 본 오더와 함께 생성되지만 초기 상태는 모두 `template / not executed`다.
- 조사 단계가 끝나기 전에는 확정 finding이 없는 상태로 본다.

---

## 13. 현재 조사 현황

- 기준일: `2026-03-13`
- 조사 현황: `조사 완료`
- 메모: 터미널별 결과 문서 작성 이후에도 통합본 및 `3PASS 재감리`가 남아 있으므로, 본 트랙은 아직 조사 진행 중으로 관리한다.
