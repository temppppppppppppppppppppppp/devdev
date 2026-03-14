# main_a Retry Feedback Detail Full Survey Audit Order

> 작성일: 2026-03-13
> 트랙: `main_a.py` retry-feedback callback blind spot audit
> 상태: `execution-ready`
> 목적: `main_a.py`에 남아 있는 retry / feedback helper 표면과 직접 consumer 계약을 전면 전량 조사한다.
> 방식: `5-terminal 병렬`, 각 터미널 자체 `3PASS`, 통합본 `3PASS 재감리`

---

## 0. 문서 역할

- 이 문서는 `main_a.py` retry-feedback helper 표면 조사 오더다.
- 이 문서는 실제 코드 수정 오더가 아니다.
- 조사 중 코드 직접 수정은 금지한다.
- 모든 문서는 `UTF-8` 고정이다. 물음표 치환 흔적이나 깨진 한글이 보이면 즉시 중단하고 인코딩 이상으로 기록한다.
- 결과 문서가 채워지기 전까지는 어떤 finding도 확정으로 간주하지 않는다.

---

## 1. 왜 별도 트랙이 필요한가

기존 문서들은 control plane, deep dive, one-stop, Stage 0, UI connectivity를 각각 다뤘다. 그러나 아래 표면은 아직 별도 조사 트랙으로 잠기지 않았다.

- `main_a.py`가 Stage 2/3/4 consumer에 노출하는 retry-feedback callback 묶음
- rejection reason 정규화, intensity 조절, reverse feedback chain의 계약 일관성
- prompt retry 축약, context builder, guidance string helper의 입력/출력 계약
- context builder가 `getattr(app, "...")`로 물고 들어가는 callback bundle의 drift 가능성
- 테스트가 메서드 존재나 호출만 검증하고 semantic drift는 놓치는 영역

관련 문서:

- `docs/2026-03-13/main_a-control-plane-detail-full-survey-audit-order.md`
- `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
- `docs/2026-03-13/OPUS-TF-5terminal-deep-dive-master-audit-order.md`

본 트랙은 Stage 2/3/4 내부 알고리즘 재감사가 아니라, `main_a.py` callback surface 자체의 계약과 regression 위험을 조사하는 데 목적이 있다.

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
- 코드 직접 수정, 임시 패치, 실행 중 수동 hotfix는 금지한다.
- 조사 중 발견한 의심 항목은 PASS 1 후보로만 기록하고 PASS 2 전 확정하지 않는다.

### 2.3 3PASS 프로토콜

#### PASS 1 - 표면 수집

- 담당 callback, consumer file, 관련 test, 관련 기존 문서를 전부 읽는다.
- 후보 finding을 `HIGH`, `MED`, `LOW` 확신도로 분류한다.
- 기존 문서와 중복 가능성이 있으면 일단 `duplicate candidate`로 표시한다.

#### PASS 2 - 교차 검증

- 코드 근거, 테스트 근거, 문서 근거를 함께 대조한다.
- 기존 문서에서 이미 닫힌 항목은 재오픈하지 않는다.
- 다만 기존 문서가 stage 내부 문제를 다뤘고, 이번 항목이 `main_a.py` callback contract 문제면 신규 finding으로 유지 가능하다.

#### PASS 3 - 최종 확정

- 확정 항목만 `[MRF-TN-SEQ]` 형식으로 채택한다.
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

- `P0`: 잘못된 feedback contract로 배치 전체가 진행 불가 또는 대규모 잘못된 재시도 유도
- `P1`: cross-stage reverse feedback 의미 드리프트, rejection 분류 오류, 잘못된 retry guidance
- `P2`: callback 누락, fallback 불명확, context helper 의미 약화, 테스트-코드 contract drift
- `P3`: 관측성, naming drift, source-string brittle test 의존, 문서-코드 미세 불일치

---

## 3. 조사 범위 지도

| Terminal | 초점 | 핵심 범위 |
|---------|------|-----------|
| T1 | Callback binding / export surface | `stage2_context.py`가 `main_a.py` callback을 주입받는 경계 |
| T2 | Rejection analysis / normalization | rejection reason, score breakdown, intensity, fix guide |
| T3 | Prompt retry / guidance / context builders | retry prompt 축약, focused context, guidance string, arc context |
| T4 | Reverse feedback / structured feedback chain | Stage4→3, Stage3→2, Stage4→2, enrich result |
| T5 | Consumer tests / docs / regression surface | 테스트, 기존 감리, 중복 판정, semantic drift 재검증 |

---

## 4. Terminal 1 - Callback Binding / Export Surface

### 담당 범위

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
- 직접 downstream
  - `modules/core/stage2_context.py`

### 핵심 검사 포인트

1. `stage2_context.py`가 기대하는 callback 이름과 `main_a.py` export 이름이 정확히 일치하는가
2. `getattr(app, "...", None)` 기반 주입이 `None` 허용인지 필수 의존인지 명확한가
3. callback 누락 시 silent degradation이 발생하는가
4. callback signature 변화가 context consumer를 조용히 깨뜨릴 위험이 있는가
5. 테스트가 존재 확인만 하고 semantic contract는 놓치고 있지 않은가

### 필수 근거

- `tests/test_stage2_context.py`
- `modules/core/stage2_context.py`
- `modules/core/stage2_orchestrator.py`

### 산출물

- `docs/2026-03-13/MRF-T1-stage2-callback-binding-findings.md`

---

## 5. Terminal 2 - Rejection Analysis / Normalization

### 담당 범위

- `main_a.py`
  - `_quantify_reject_feedback()`
  - `_analyze_score_breakdown()`
  - `_get_adaptive_feedback_intensity()`
  - `_analyze_rejection_pattern_v60()`
  - `_normalize_rejection_reason()`
  - `_get_rejection_fix_guide()`

### 핵심 검사 포인트

1. rejection reason normalization이 하위 분기와 맞물리는가
2. breakdown 분석 결과가 retry guidance 세기와 일관된가
3. 동일 failure 입력에 대해 stage별 intensity 정책이 drift하지 않는가
4. string heuristic가 locale/표현 차이에 과도하게 취약하지 않은가
5. 테스트가 명시되지 않은 reason class가 있는가

### 필수 근거

- `modules/core/stage2_context.py`
- `tests/test_stage2_context.py`
- 관련 기존 feedback 문서

### 산출물

- `docs/2026-03-13/MRF-T2-rejection-analysis-intensity-findings.md`

---

## 6. Terminal 3 - Prompt Retry / Guidance / Context Builders

### 담당 범위

- `main_a.py`
  - `_simplify_prompt_for_retry()`
  - `_build_strong_kind_feedback()`
  - `_build_focused_context()`
  - `_build_minimal_arc_context()`
  - `_generate_arc_position_guide()`
  - `_get_dynamic_critical_keywords()`
  - `_generate_writer_guidance_v60_8()`
  - `_generate_arc_context_v60()`
- 직접 downstream
  - `modules/core/prompt_builder.py`

### 핵심 검사 포인트

1. retry 횟수 증가에 따라 guidance가 과잉 단순화되거나 의미를 잃지 않는가
2. focused / minimal context가 서로 다른 consumer에서 의미 충돌을 일으키지 않는가
3. arc position guide와 arc context helper가 episode/arc boundary와 일치하는가
4. keyword helper가 hard-coded drift를 낳지 않는가
5. prompt builder fallback과 `main_a.py` helper 출력이 상호 모순되지 않는가

### 필수 근거

- `tests/test_prompt_builder.py`
- `modules/core/prompt_builder.py`
- `modules/core/stage2_context.py`

### 산출물

- `docs/2026-03-13/MRF-T3-prompt-guidance-context-findings.md`

---

## 7. Terminal 4 - Reverse Feedback / Structured Feedback Chain

### 담당 범위

- `main_a.py`
  - `_enrich_director_result()`
  - `_generate_structured_arc_feedback()`
  - `_generate_reverse_feedback_stage4_to_3()`
  - `_generate_reverse_feedback_stage3_to_2()`
  - `_generate_reverse_feedback_stage4_to_2()`

### 핵심 검사 포인트

1. Stage 4 -> 3 -> 2 reverse feedback chain이 같은 failure 원인을 다른 의미로 번역하지 않는가
2. structured feedback와 enrich 결과가 severity/score 정보를 일관되게 보존하는가
3. helper 간 입력 자료형과 optional field 기대치가 같은가
4. director result enrichment가 false confidence를 유발하지 않는가
5. 기존 Stage4 feedback loop 감리와 표면이 겹치더라도 `main_a.py` 책임 경계를 분리할 수 있는가

### 필수 근거

- `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
- `modules/core/stage2_context.py`
- 관련 Stage 4 feedback consumer test

### 산출물

- `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`

---

## 8. Terminal 5 - Consumer Tests / Docs / Regression Surface

### 담당 범위

- `tests/test_stage2_context.py`
- `tests/test_prompt_builder.py`
- 관련 retry-feedback 문서와 감리 기록
- `main_a.py` retry-feedback helper 전체 표면

### 핵심 검사 포인트

1. 테스트가 callback 존재만 확인하고 semantic drift는 놓치지 않는가
2. 기존 감리 문서와 현재 코드가 불일치하는가
3. 이미 닫힌 finding을 다시 여는 오탐이 있는가
4. source-string or MagicMock 중심 테스트가 contract 안정성을 과대평가하지 않는가
5. 최종 통합 시 중복 surface를 `related-but-new-callback-surface`로 분리할 수 있는가

### 필수 근거

- `tests/test_stage2_context.py`
- `tests/test_prompt_builder.py`
- `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
- `docs/2026-03-13/OPUS-TF-5terminal-deep-dive-master-audit-order.md`

### 산출물

- `docs/2026-03-13/MRF-T5-consumer-tests-regression-findings.md`

---

## 9. 명시적 제외 범위

아래는 참조 근거로만 사용하고, 이번 조사 본체로 재포장하지 않는다.

- Stage 2/3/4 내부 생성 알고리즘 심층
- one-stop / frontier-lag / lookahead
- Stage 0 UI 선택 로직
- desktop IPC 세부 구현
- 실제 remediation patch 작성

---

## 10. 통합 산출물 규칙

### 터미널 결과 문서

- `docs/2026-03-13/MRF-T1-stage2-callback-binding-findings.md`
- `docs/2026-03-13/MRF-T2-rejection-analysis-intensity-findings.md`
- `docs/2026-03-13/MRF-T3-prompt-guidance-context-findings.md`
- `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`
- `docs/2026-03-13/MRF-T5-consumer-tests-regression-findings.md`

### 통합 문서

- `docs/2026-03-13/main_a-retry-feedback-detail-consolidated-findings.md`
- `docs/2026-03-13/main_a-retry-feedback-detail-consolidated-findings-3pass-reaudit.md`

### 중복 처리 규칙

- 기존 문서에서 이미 닫힌 항목은 재오픈 금지
- 단, `main_a.py` callback contract 자체가 다른 책임 경계를 가지면 신규 `MRF-*` finding 가능
- 신규 finding에는 아래 중 하나를 반드시 적는다
  - `none`
  - `related-but-new-callback-surface`
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
