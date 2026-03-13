# main_a Cross-Stage Semantic Preservation Detail Full Survey Audit Order

> 작성일: 2026-03-13
> 트랙: `main_a.py` cross-stage semantic preservation blind spot audit
> 상태: `execution-ready`
> 조사 현황: `조사 완료`
> 목적: `main_a.py`와 직접 consumer가 Stage 4 -> 3 -> 2 및 summary/context handoff 과정에서 같은 실패 의미, 같은 narrative 의미, 같은 경계 의미를 보존하는지 전면 전량 조사한다.
> 방식: `5-terminal 병렬`, 각 터미널 자체 `3PASS`, 통합본 `3PASS 재감리`

---

## 0. 문서 역할

- 이 문서는 `main_a.py` cross-stage semantic preservation 조사 오더다.
- 이 문서는 코드 수정 오더가 아니다.
- 조사 단계에서 코드 직접 수정은 금지한다.
- 모든 문서는 `UTF-8` 고정이다. `???`, `�`, 깨진 한글이 보이면 즉시 중단하고 인코딩 이상으로 기록한다.
- 결과 문서가 채워지기 전까지는 어떤 finding도 확정으로 간주하지 않는다.

---

## 1. 왜 별도 트랙이 필요한가

기존 문서들은 reverse feedback, summary cache, facade drift를 각각 다뤘다. 그러나 아래 표면은 아직 `stage handoff 의미 보존` 관점의 독립 오더로 잠기지 않았다.

- `Stage4 -> 3`, `Stage3 -> 2`, `Stage4 -> 2`로 내려가는 feedback가 같은 실패 원인을 같은 의미로 번역하는지 여부
- `error_category`, `score_breakdown`, `action_items`, `responsibility_guide` 같은 구조화 정보가 단계 간 압축되며 소실되는지 여부
- narrative summary, arc context, focused context가 stage마다 다른 의미로 소비되는지 여부
- Stage4 builder / round / post-processor가 동일한 semantic payload를 유지하는지 여부
- hard/normal gating test는 있으나 semantic preservation test는 없는 영역

관련 문서:

- `docs/2026-03-13/main_a-retry-feedback-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-persistence-narrative-detail-full-survey-audit-order.md`
- `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`
- `docs/2026-03-13/MRF-T3-prompt-guidance-context-findings.md`
- `docs/2026-03-13/MPN-T4-stage4-summary-cache-findings.md`
- `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`

본 트랙은 Stage 내부 알고리즘이나 scoring 품질 자체를 재감사하는 것이 아니라, `handoff semantic contract`를 SSOT로 잠그는 데 목적이 있다.

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

- 담당 handoff helper, consumer file, test, 기존 문서를 전부 읽는다.
- 후보 finding을 `HIGH`, `MED`, `LOW` 확신도로 분류한다.
- semantic loss, semantic rewrite, semantic bypass 후보를 구분해 적는다.

#### PASS 2 - 교차 검증

- 코드 근거, 테스트 근거, 문서 근거를 함께 대조한다.
- 단순 존재/호출 여부 검증만 있는 항목은 semantic-preservation finding으로 과잉 확정하지 않는다.
- 기존 문서에서 이미 닫힌 항목은 재오픈하지 않는다.

#### PASS 3 - 최종 확정

- 확정 항목만 `[MCS-TN-SEQ]` 형식으로 채택한다.
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

- `P0`: handoff semantic corruption으로 production batch가 회복 불가 상태에 빠지거나 대규모 잘못된 재생성으로 이어지는 경우
- `P1`: failure meaning, summary meaning, arc/narrative boundary meaning이 다음 stage에서 유의미하게 잘못 해석되는 경우
- `P2`: optional field 소실, 과도한 압축, fallback semantics 불명확, semantic-preservation 테스트 부재
- `P3`: 관측성, terminology drift, 문서-코드 미세 불일치

---

## 3. 조사 범위 지도

| Terminal | 초점 | 핵심 범위 |
|---------|------|-----------|
| T1 | `Stage4 -> 3` semantic preservation | reverse feedback, director result, Stage3 consumer 해석 |
| T2 | `Stage3 -> 2` semantic preservation | callback optionality, rejection 의미 보존, retry reason 전달 |
| T3 | `Stage4 -> 2` semantic preservation | hard/normal gating 이후 구조화 정보 보존 |
| T4 | Summary / context / arc semantic preservation | narrative summary, focused context, arc context, volume boundary |
| T5 | Tests / docs / regression surface | semantic-preservation blind spot, 문서 중복, proof quality |

---

## 4. Terminal 1 - Stage4 -> 3 Semantic Preservation

### 담당 범위

- `main_a.py`
  - `_generate_reverse_feedback_stage4_to_3()`
  - `_enrich_director_result()`
- 직접 downstream
  - `modules/core/stage3_context.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_interview_round.py`

### 핵심 검사 포인트

1. Stage4 rejection 의미가 Stage3 feedback로 내려갈 때 category, severity, responsibility가 유지되는가
2. `_enrich_director_result()`가 실제 live chain에 연결되는가, 아니면 semantic-rich helper가 dead surface인가
3. Stage3 consumer가 Stage4 feedback payload를 단순 문자열로 축소하지 않는가
4. helper unit test와 live consumer 사이에 semantic contract 차이가 없는가
5. 문서상 존재하는 `Stage4 -> 3` 체인이 실제 runtime에서도 살아 있는가

### 필수 근거

- `tests/test_director_feedback_loop.py`
- `tests/test_stage3_orchestrator.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_interview_round.py`

### 산출물

- `docs/2026-03-13/MCS-T1-stage4-to-stage3-semantic-findings.md`

---

## 5. Terminal 2 - Stage3 -> 2 Semantic Preservation

### 담당 범위

- `main_a.py`
  - `_generate_reverse_feedback_stage3_to_2()`
  - `_analyze_rejection_pattern_v60()`
  - `_normalize_rejection_reason()`
  - `_get_rejection_fix_guide()`
- 직접 downstream
  - `modules/core/stage2_context.py`
  - `modules/core/stage2_preflight.py`

### 핵심 검사 포인트

1. Stage3 failure 의미가 Stage2 retry planning에 같은 의미로 반영되는가
2. optional callback이 `None`일 때 semantic-preservation contract가 무너지는가
3. rejection reason normalization이 reverse feedback 분류와 모순되지 않는가
4. Stage2 consumer가 강도만 남기고 의미를 잃는 구조가 아닌가
5. `callback=None + failure>=3` 같은 missing-branch가 semantic gap을 만들지 않는가

### 필수 근거

- `tests/test_stage2_preflight.py`
- `tests/test_stage2_preflight_helpers.py`
- `modules/core/stage2_context.py`
- `modules/core/stage2_preflight.py`

### 산출물

- `docs/2026-03-13/MCS-T2-stage3-to-stage2-semantic-findings.md`

---

## 6. Terminal 3 - Stage4 -> 2 Semantic Preservation

### 담당 범위

- `main_a.py`
  - `_generate_reverse_feedback_stage4_to_2()`
  - `_quantify_reject_feedback()`
  - `_analyze_score_breakdown()`
- 직접 downstream
  - `modules/core/stage2_context.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage4_post_processor.py`

### 핵심 검사 포인트

1. Stage4 failure payload가 Stage2로 내려갈 때 hard/normal gate 외 semantic 정보가 남는가
2. `error_category`, `score_breakdown`, `action_items`, `open_review`가 사라지지 않는가
3. score/intensity helper가 의미 손실 없이 retry planning에 연결되는가
4. Stage4 post-processing 이후 helper 입력 구조와 Stage2 기대 구조가 같은가
5. 현재 테스트가 gate만 보고 semantic preservation은 놓치고 있지 않은가

### 필수 근거

- `tests/test_stage2_preflight_helpers.py`
- `tests/test_feedback_system.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage2_context.py`

### 산출물

- `docs/2026-03-13/MCS-T3-stage4-to-stage2-semantic-findings.md`

---

## 7. Terminal 4 - Summary / Context / Arc Semantic Preservation

### 담당 범위

- `main_a.py`
  - `_generate_narrative_summary()`
  - `_load_narrative_summaries()`
  - `_build_focused_context()`
  - `_build_minimal_arc_context()`
  - `_generate_arc_context_v60()`
  - `_get_arc_context_for_episode()`
  - `_validate_volume_boundaries()`
- 직접 downstream
  - `modules/core/stage4_context.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage01_helpers.py`

### 핵심 검사 포인트

1. narrative summary가 Stage4 builder와 round에서 같은 범위 의미를 갖는가
2. minimal / focused / full arc context가 같은 사건, 위치, 내공, 부상 정보를 다르게 왜곡하지 않는가
3. volume boundary helper와 arc context helper가 stage 간 다른 경계 의미를 만들지 않는가
4. sparse manuscript나 partial resume에서 summary 범위가 semantic drift를 만들지 않는가
5. summary/cached context가 hard-coded 상한 때문에 의미를 잘라먹지 않는가

### 필수 근거

- `tests/test_stage4_context.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage01_helpers.py`
- `tests/test_sweep23.py`

### 산출물

- `docs/2026-03-13/MCS-T4-shared-context-summary-semantic-findings.md`

---

## 8. Terminal 5 - Tests / Docs / Regression Surface

### 담당 범위

- cross-stage 관련 테스트 전반
- 기존 audit / findings / consolidated docs
- semantic preservation blind spot inventory

### 핵심 검사 포인트

1. 현재 테스트가 존재/호출 여부만 보장하고 semantic preservation은 놓치지 않는가
2. 기존 감리 문서와 현재 runtime path의 semantic claim이 일치하는가
3. 같은 semantic issue가 다른 트랙에서 이미 닫힌 항목인지 중복 판정 가능한가
4. 최종 통합 시 `semantic-loss`, `semantic-rewrite`, `semantic-bypass` ledger를 만들 수 있는가
5. proof quality가 unit helper 중심에 치우쳐 live consumer 의미를 과장하지 않는가

### 필수 근거

- `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`
- `docs/2026-03-13/MPN-T4-stage4-summary-cache-findings.md`
- `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
- 관련 cross-stage test 파일

### 산출물

- `docs/2026-03-13/MCS-T5-cross-stage-tests-docs-regression-findings.md`

---

## 9. 명시적 제외 범위

아래는 참조 근거로만 사용하고, 이번 조사 본체로 재포장하지 않는다.

- LLM 출력 품질 그 자체의 우열 평가
- stage 내부 scoring 알고리즘 세부 조정
- one-stop / frontier-lag / desktop IPC
- remediation patch 작성
- non-`main_a.py` 독립 모듈 전체 재감사

---

## 10. 통합 산출물 규칙

### 터미널 결과 문서

- `docs/2026-03-13/MCS-T1-stage4-to-stage3-semantic-findings.md`
- `docs/2026-03-13/MCS-T2-stage3-to-stage2-semantic-findings.md`
- `docs/2026-03-13/MCS-T3-stage4-to-stage2-semantic-findings.md`
- `docs/2026-03-13/MCS-T4-shared-context-summary-semantic-findings.md`
- `docs/2026-03-13/MCS-T5-cross-stage-tests-docs-regression-findings.md`

### 통합 문서

- `docs/2026-03-13/main_a-cross-stage-semantic-preservation-detail-consolidated-findings.md`
- `docs/2026-03-13/main_a-cross-stage-semantic-preservation-detail-consolidated-findings-3pass-reaudit.md`

### 중복 처리 규칙

- 기존 retry, facade, persistence 문서에서 이미 닫힌 항목은 재오픈 금지
- 단, `cross-stage semantic preservation` 자체가 다른 책임 경계를 가지면 신규 `MCS-*` finding 가능
- 신규 finding에는 아래 중 하나를 반드시 적는다
  - `none`
  - `related-but-new-cross-stage-semantic-surface`
  - `already-covered-do-not-reopen`

---

## 11. 실행 완료 판정

아래를 모두 만족해야 본 오더가 닫힌다.

1. T1 ~ T5 결과 문서가 모두 존재한다.
2. 각 문서가 `PASS1 -> PASS2 -> PASS3` 요약을 가진다.
3. 각 finding이 코드 근거, 테스트 근거, downstream 경계, 중복 여부를 모두 가진다.
4. 통합본이 semantic-loss / semantic-rewrite / semantic-bypass ledger를 재구성한다.
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
- 메모: 본 표면의 터미널별 전수조사는 완료로 기록한다. 다만 트랙 마감 여부와 통합본 `3PASS 재감리`는 별도 단계로 관리한다.
