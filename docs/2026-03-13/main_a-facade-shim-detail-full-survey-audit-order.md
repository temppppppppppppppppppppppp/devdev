# main_a Facade Shim Detail Full Survey Audit Order

> 작성일: 2026-03-13
> 트랙: `main_a.py` facade shim and audit callback blind spot audit
> 상태: `execution-ready`
> 목적: `main_a.py`에 남아 있는 facade shim / validation delegate / audit callback 표면과 직접 consumer 계약을 전면 전량 조사한다.
> 방식: `5-terminal 병렬`, 각 터미널 자체 `3PASS`, 통합본 `3PASS 재감리`

---

## 0. 문서 역할

- 이 문서는 `main_a.py` facade shim 조사 오더다.
- 이 문서는 코드 수정 오더가 아니다.
- 조사 단계에서 코드 직접 수정은 금지한다.
- 모든 문서는 `UTF-8` 고정이다. `???`, `�`, 깨진 한글이 보이면 즉시 중단하고 인코딩 이상으로 기록한다.
- 결과 문서가 채워지기 전까지는 어떤 finding도 확정으로 간주하지 않는다.

---

## 1. 왜 별도 트랙이 필요한가

기존 문서들은 control plane, deep dive, stage quality, canary, Stage 0 일부를 다뤘다. 그러나 아래 표면은 아직 `main_a.py` facade shim 계약 관점의 독립 오더로 잠기지 않았다.

- `main_a.py`가 validation pipeline / state service / prompt builder에 넘겨주는 delegate helper 묶음
- `_audit_event()`, `_flush_audit_buffer()`, `_write_audit_summary()` 같은 audit callback 표면
- `_get_arc_context_for_episode()`, `_validate_arc_data_fields()`, `_validate_blueprint_integrity()` 같은 stage context validator facade
- `_show_volume_table()`를 포함한 Stage01 / UI presentation callback 표면
- 테스트가 method 존재와 호출 여부만 보장하고 semantic contract drift는 놓칠 수 있는 영역

관련 문서:

- `docs/2026-03-13/main_a-control-plane-detail-full-survey-audit-order.md`
- `docs/2026-03-11/00-test-02-03-system-improvement-final-audit-codex.md`
- `docs/2026-03-12/system-wide-full-survey-3pass-master-audit.md`
- `docs/stage_map/stage1.md`

본 트랙은 Stage 2/3/4 내부 알고리즘 재감사가 아니라, `main_a.py` facade / callback surface 자체의 계약과 regression 위험을 조사하는 데 목적이 있다.

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

- 담당 helper, consumer file, test, 기존 문서를 전부 읽는다.
- 후보 finding을 `HIGH`, `MED`, `LOW` 확신도로 분류한다.
- 기존 문서와 중복 가능성이 있으면 일단 `duplicate candidate`로 표시한다.

#### PASS 2 - 교차 검증

- 코드 근거, 테스트 근거, 문서 근거를 함께 대조한다.
- 기존 문서에서 이미 닫힌 항목은 재오픈하지 않는다.
- 다만 기존 문서가 stage 내부 문제를 다뤘고, 이번 항목이 `main_a.py` facade contract 문제면 신규 finding으로 유지 가능하다.

#### PASS 3 - 최종 확정

- 확정 항목만 `[MFS-TN-SEQ]` 형식으로 채택한다.
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

- `P0`: audit / validation facade drift로 잘못된 성공 판정 또는 진행 불가 상태를 유발
- `P1`: validation delegate 오작동, 잘못된 arc/blueprint integrity 판정, audit summary 오염
- `P2`: callback 누락, fallback 불명확, service/protocol 의미 드리프트, 테스트-코드 contract 불일치
- `P3`: 관측성, UI presentation callback drift, source-string brittle test 의존

---

## 3. 조사 범위 지도

| Terminal | 초점 | 핵심 범위 |
|---------|------|-----------|
| T1 | Stage2 normalization / flow delegate | `_normalize_tactical_text()`, `_is_tactical_doc_duplicate()`, `_normalize_flow_text()`, `_stage2_flow_guard()` |
| T2 | State service / validation shim | `_extract_block_index()`, `_validate_arc_mapping()`, `_extract_pattern_keywords()`, `_pattern_presence_check()` 등 |
| T3 | Audit callback / stage context facade | `_audit_event()`, `_flush_audit_buffer()`, `_write_audit_summary()`, `_get_arc_context_for_episode()` 등 |
| T4 | Prompt / NPC / UI presentation shim | NPC helper, genre reference helper, `_show_volume_table()` |
| T5 | Protocol / tests / regression surface | `app_services.py`, tests, 기존 감리 문서, semantic drift 재검증 |

---

## 4. Terminal 1 - Stage2 Normalization / Flow Delegate

### 담당 범위

- `main_a.py`
  - `_normalize_tactical_text()`
  - `_is_tactical_doc_duplicate()`
  - `_normalize_flow_text()`
  - `_stage2_flow_guard()`
  - `_stage2_flow_guard_legacy()`
- 직접 downstream
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_validation_pipeline.py`

### 핵심 검사 포인트

1. `main_a.py` shim과 실제 validation pipeline 구현이 의미적으로 같은가
2. shim이 단순 위임처럼 보여도 인자 / 반환 계약 drift가 숨어 있지 않은가
3. legacy flow guard fallback이 여전히 살아 있는 의미가 명확한가
4. 테스트가 orchestrator 자체만 보고 `main_a.py` shim drift는 놓치지 않는가
5. normalization helper가 `None` / 비문자 입력에서 조용히 의미를 왜곡하지 않는가

### 필수 근거

- `tests/test_stage2_pipeline.py`
- `tests/test_stage2_validation_pipeline.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_validation_pipeline.py`

### 산출물

- `docs/2026-03-13/MFS-T1-stage2-normalization-flow-findings.md`

---

## 5. Terminal 2 - State Service / Validation Shim

### 담당 범위

- `main_a.py`
  - `_build_item_acquisition_timeline()`
  - `_extract_block_index()`
  - `_validate_arc_mapping()`
  - `_extract_pattern_keywords()`
  - `_pattern_presence_check()`
  - `_build_validation_context()`
  - `_load_genre_references()`
  - `_validate_arc_integrity()`
  - `_validate_blueprint_integrity()`
- 직접 downstream
  - `modules/core/services/state_service.py`

### 핵심 검사 포인트

1. state service가 기대하는 helper 의미와 `main_a.py` facade 의미가 같은가
2. integrity / mapping helper가 audit-only인지 hard gate인지 명확한가
3. pattern / context helper가 prompt builder or validation pipeline과 중복 정의돼 drift를 만들지 않는가
4. `audit_event`와 결합된 validation helper가 side effect를 숨기지 않는가
5. 테스트가 helper 존재만 보장하고 반환 계약 drift는 놓치지 않는가

### 필수 근거

- `tests/test_state_service.py`
- `modules/core/services/state_service.py`
- `modules/core/stage2_context.py`

### 산출물

- `docs/2026-03-13/MFS-T2-state-service-validation-findings.md`

---

## 6. Terminal 3 - Audit Callback / Stage Context Facade

### 담당 범위

- `main_a.py`
  - `_classify_rejection_feedback()`
  - `_audit_event()`
  - `_flush_audit_buffer()`
  - `_write_audit_summary()`
  - `_get_arc_context_for_episode()`
  - `_validate_arc_data_fields()`
  - `_validate_blueprint_integrity()`
- 직접 downstream
  - `modules/core/stage3_context.py`
  - `modules/core/stage4_context.py`
  - `modules/core/stage4_orchestrator.py`

### 핵심 검사 포인트

1. audit event / summary callback가 실패 / 중단 경로를 성공으로 오염시키지 않는가
2. `flush -> summary -> analyze` 순서가 실제 consumer와 맞는가
3. arc context / data field validator facade가 Stage3 consumer 기대와 일치하는가
4. stage4 audit callback과 stage3 audit callback이 같은 completion semantics를 공유하는가
5. canary / final audit 문서와 현재 코드가 불일치하는가

### 필수 근거

- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_run_stage4_canary.py`
- `docs/2026-03-11/00-test-02-03-system-improvement-final-audit-codex.md`

### 산출물

- `docs/2026-03-13/MFS-T3-stage3-stage4-audit-callback-findings.md`

---

## 7. Terminal 4 - Prompt / NPC / UI Presentation Shim

### 담당 범위

- `main_a.py`
  - `_extract_npc_profiles()`
  - `_get_character_traits()`
  - `_load_character_archetypes()`
  - `_get_archetype_reference_for_npcs()`
  - `_show_volume_table()`
- 직접 downstream
  - `modules/core/prompt_builder.py`
  - `modules/core/stage01_helpers.py`
  - `modules/core/stage4_context.py`

### 핵심 검사 포인트

1. NPC / archetype helper가 prompt builder fallback과 의미 충돌을 일으키지 않는가
2. `_show_volume_table()`가 UI service contract와 문서 기대를 어기지 않는가
3. Stage01 and Stage4 consumer가 같은 helper를 서로 다른 의미로 사용하지 않는가
4. UI callback이 단순 표시용인지 flow control에 영향을 주는지 명확한가
5. 관련 테스트가 semantic contract보다는 호출 여부에 치우치지 않는가

### 필수 근거

- `tests/test_prompt_builder.py`
- `tests/test_ui_service.py`
- `tests/test_stage4_context.py`
- `docs/stage_map/stage1.md`

### 산출물

- `docs/2026-03-13/MFS-T4-ui-stage01-presentation-findings.md`

---

## 8. Terminal 5 - Protocol / Tests / Regression Surface

### 담당 범위

- `modules/protocols/app_services.py`
- `modules/validation/validation_orchestrator.py`
- 관련 테스트와 기존 감리 문서
- `main_a.py` facade shim 전체 표면

### 핵심 검사 포인트

1. protocol conformance가 이름상 통과하지만 semantic contract는 어긋나지 않는가
2. source-string or MagicMock 중심 테스트가 facade drift를 과소평가하지 않는가
3. 기존 감리 문서와 현재 consumer graph가 불일치하는가
4. 이미 닫힌 finding을 다시 여는 오탐을 통합 단계 전에 제거할 수 있는가
5. 최종 통합 시 `related-but-new-facade-surface`와 `already-covered-do-not-reopen`을 분리할 수 있는가

### 필수 근거

- `tests/test_validation_orchestrator_soft_failure.py`
- `tests/test_audit_service.py`
- `modules/protocols/app_services.py`
- `docs/2026-03-12/system-wide-full-survey-3pass-master-audit.md`

### 산출물

- `docs/2026-03-13/MFS-T5-protocol-tests-regression-findings.md`

---

## 9. 명시적 제외 범위

아래는 참조 근거로만 사용하고, 이번 조사 본체로 재포장하지 않는다.

- `_ui_select_bible()`, `_ui_select_treatment()`, `_enrich_treatment_blocks()` 표면
- Stage 2/3/4 내부 알고리즘 심층
- one-stop / frontier-lag / lookahead
- desktop IPC 세부 구현
- 실제 remediation patch 작성

---

## 10. 통합 산출물 규칙

### 터미널 결과 문서

- `docs/2026-03-13/MFS-T1-stage2-normalization-flow-findings.md`
- `docs/2026-03-13/MFS-T2-state-service-validation-findings.md`
- `docs/2026-03-13/MFS-T3-stage3-stage4-audit-callback-findings.md`
- `docs/2026-03-13/MFS-T4-ui-stage01-presentation-findings.md`
- `docs/2026-03-13/MFS-T5-protocol-tests-regression-findings.md`

### 통합 문서

- `docs/2026-03-13/main_a-facade-shim-detail-consolidated-findings.md`
- `docs/2026-03-13/main_a-facade-shim-detail-consolidated-findings-3pass-reaudit.md`

### 중복 처리 규칙

- 기존 문서에서 이미 닫힌 항목은 재오픈 금지
- 단, `main_a.py` facade contract 자체가 다른 책임 경계를 가지면 신규 `MFS-*` finding 가능
- 신규 finding에는 아래 중 하나를 반드시 적는다
  - `none`
  - `related-but-new-facade-surface`
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
