# main_a Dormant Helper Live Consumer Detail Full Survey Audit Order

> 작성일: 2026-03-13
> 트랙: `main_a.py` dormant helper and live consumer inventory audit
> 상태: `execution-ready`
> 목적: `main_a.py`와 직접 하위 모듈에 남아 있는 helper들이 실제 runtime consumer를 가지는지, 우회되는지, dead surface인지 전면 전량 조사한다.
> 방식: `5-terminal 병렬`, 각 터미널 자체 `3PASS`, 통합본 `3PASS 재감리`

---

## 0. 문서 역할

- 이 문서는 `main_a.py` dormant helper / live consumer inventory 조사 오더다.
- 이 문서는 코드 수정 오더가 아니다.
- 조사 단계에서 코드 직접 수정은 금지한다.
- 모든 문서는 `UTF-8` 고정이다. `???`, `�`, 깨진 한글이 보이면 즉시 중단하고 인코딩 이상으로 기록한다.
- 결과 문서가 채워지기 전까지는 어떤 finding도 확정으로 간주하지 않는다.

---

## 1. 왜 별도 트랙이 필요한가

기존 문서들은 helper contract drift를 다뤘지만, 아래 표면은 아직 `이 helper가 실제로 어디서 살아 있는가` 관점의 독립 오더로 잠기지 않았다.

- 정의만 남고 실제 live consumer가 불명확한 helper
- stage runtime은 우회 경로를 쓰는데 facade나 helper는 계속 export되는 표면
- unit test만 있고 production caller가 없는 helper
- coverage gap에서 `별도 audit`로 이관된 dormant / bypassed surface
- dead helper, carry-over helper, hidden one-shot consumer를 구분해야 하는 call graph inventory

관련 문서:

- `docs/2026-03-13/main_a-retry-feedback-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-facade-shim-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-persistence-narrative-detail-full-survey-audit-order.md`
- `docs/2026-03-13/MFS-T3-stage3-stage4-audit-callback-findings.md`
- `docs/2026-03-13/MFS-T4-ui-stage01-presentation-findings.md`
- `docs/2026-03-13/MRF-T3-prompt-guidance-context-findings.md`
- `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`
- `docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md`

본 트랙은 일반적인 dead code 청소 오더가 아니라, `live consumer inventory` 자체를 SSOT로 잠그는 데 목적이 있다.

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

- 담당 helper, caller, test, 기존 문서를 전부 읽는다.
- 후보 finding을 `HIGH`, `MED`, `LOW` 확신도로 분류한다.
- candidate마다 `live`, `dormant`, `bypassed`, `unknown` 상태를 임시 태깅한다.

#### PASS 2 - 교차 검증

- 전역 검색, 직접 caller 추적, 테스트 근거, 기존 문서를 함께 대조한다.
- 문서만 있고 실제 caller가 없으면 `dormant` 후보를 유지하되 과잉 확정은 금지한다.
- 우회 경로가 분명히 확인되면 `bypassed-live-surface`로 분리한다.

#### PASS 3 - 최종 확정

- 확정 항목만 `[MDH-TN-SEQ]` 형식으로 채택한다.
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

- `P0`: 실제 consumer가 dormant/dead helper를 믿고 있어 production path가 즉시 실패하거나 데이터 손실로 이어지는 경우
- `P1`: live consumer가 intended helper를 우회해 의미 있는 semantic 손실이나 silent degradation을 만드는 경우
- `P2`: dormant helper, hidden caller, bypassed facade, one-shot runtime surface, 문서-코드 consumer mismatch
- `P3`: naming drift, dead export, stale docs, test-only helper

---

## 3. 조사 범위 지도

| Terminal | 초점 | 핵심 범위 |
|---------|------|-----------|
| T1 | Retry / guidance helper liveness | retry-feedback, guidance, reverse-feedback helper의 실제 caller |
| T2 | Audit / validation helper liveness | audit, validation, arc context helper의 live consumer 여부 |
| T3 | Stage01 / NPC / UI helper liveness | Stage01, NPC, genre reference, UI presentation helper의 실제 runtime 사용 여부 |
| T4 | Bootstrap / history / cache helper liveness | bootstrap, cache, history, restore helper의 caller inventory |
| T5 | Call graph / runtime artifact / regression | 검색, 로그, e2e, 기존 문서 기반 inventory 교차 검증 |

---

## 4. Terminal 1 - Retry / Guidance Helper Liveness

### 담당 범위

- `main_a.py`
  - `_generate_writer_guidance_v60_8()`
  - `_generate_arc_position_guide()`
  - `_simplify_prompt_for_retry()`
  - `_build_focused_context()`
  - `_build_minimal_arc_context()`
  - `_generate_reverse_feedback_stage4_to_3()`
  - `_enrich_director_result()`

### 핵심 검사 포인트

1. helper가 실제 runtime caller를 가지는가, 아니면 unit test 전용인가
2. intended consumer가 있는데도 실제 production path는 우회하고 있지 않은가
3. retry / guidance family 안에서 dead helper와 live helper가 섞여 있지 않은가
4. hidden one-shot consumer가 e2e, canary, manual path에만 남아 있지 않은가
5. 기존 coverage gap의 `별도 audit` 요청을 이번 inventory로 닫을 수 있는가

### 필수 근거

- `tests/test_arc_retry.py`
- `tests/test_stage2_preflight_helpers.py`
- `tests/test_stage4_context_builder.py`
- `modules/core/stage4_context_builder.py`

### 산출물

- `docs/2026-03-13/MDH-T1-retry-guidance-helper-liveness-findings.md`

---

## 5. Terminal 2 - Audit / Validation Helper Liveness

### 담당 범위

- `main_a.py`
  - `_classify_rejection_feedback()`
  - `_audit_event()`
  - `_flush_audit_buffer()`
  - `_write_audit_summary()`
  - `_get_arc_context_for_episode()`
  - `_validate_arc_data_fields()`
  - `_validate_blueprint_integrity()`
  - `_build_item_acquisition_timeline()`

### 핵심 검사 포인트

1. helper가 실제 Stage3/4 runtime에서 호출되는가
2. helper가 정의돼 있어도 live path는 직접 service나 다른 helper를 우회 호출하지 않는가
3. audit/validation helper 중 test-only surface는 무엇인가
4. success / failure / interrupt 경로가 서로 다른 helper source를 바라보며 dormant facade를 남기지 않는가
5. `coverage gap`로 남아 있던 항목이 dead helper인지 hidden consumer인지 분리 가능한가

### 필수 근거

- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`

### 산출물

- `docs/2026-03-13/MDH-T2-audit-validation-helper-liveness-findings.md`

---

## 6. Terminal 3 - Stage01 / NPC / UI Helper Liveness

### 담당 범위

- `main_a.py`
  - `_validate_volume_boundaries()`
  - `_extract_npc_profiles()`
  - `_get_character_traits()`
  - `_load_character_archetypes()`
  - `_get_archetype_reference_for_npcs()`
  - `_show_volume_table()`
- 직접 downstream
  - `modules/core/stage01_helpers.py`
  - `modules/core/stage4_context.py`

### 핵심 검사 포인트

1. Stage01, Stage4, UI path가 helper를 실제로 쓰는가
2. helper는 살아 있는데 consumer가 빈 dict, bypass, direct path를 택해 dormant surface가 되지 않았는가
3. genre reference helper가 프롬프트 조립에 실제로 실리는가
4. UI presentation helper가 문서에만 남고 runtime에서는 무의미해지지 않았는가
5. stage map / docs와 실제 caller inventory가 같은가

### 필수 근거

- `tests/test_stage01_helpers.py`
- `tests/test_stage4_context.py`
- `tests/test_ui_service.py`
- `docs/stage_map/stage1.md`

### 산출물

- `docs/2026-03-13/MDH-T3-stage01-npc-ui-helper-liveness-findings.md`

---

## 7. Terminal 4 - Bootstrap / History / Cache Helper Liveness

### 담당 범위

- `main_a.py`
  - `_ignite_quad_cache_system()`
  - `_load_v50_history()`
  - `_restore_preset_registry()`
  - `_is_cache_alive()`
  - bootstrap / restore helper 전반

### 핵심 검사 포인트

1. helper가 실제 boot / project switch / recovery path에서 호출되는가
2. no-op stub, dead helper, legacy carry-over helper가 무엇인지 분리 가능한가
3. history / cache / preset restore helper가 문서상 기대와 runtime caller가 같은가
4. live caller가 있지만 결과를 무시하는 one-shot helper는 없는가
5. 기존 bootstrap 문서가 helper 존재만 기록하고 실제 live consumer는 놓치지 않았는가

### 필수 근거

- `tests/test_stage_transition.py`
- `tests/test_project_service.py`
- `modules/core/services/project_service.py`
- `docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md`

### 산출물

- `docs/2026-03-13/MDH-T4-bootstrap-history-cache-helper-liveness-findings.md`

---

## 8. Terminal 5 - Call Graph / Runtime Artifact / Regression

### 담당 범위

- repo 전역 검색 결과
- `tests/e2e`, canary, smoke, integration artifact
- 기존 감리 문서와 consolidated findings

### 핵심 검사 포인트

1. static grep과 runtime-oriented artifact가 같은 caller inventory를 가리키는가
2. e2e / smoke / canary에서만 살아 있는 helper가 있는가
3. 문서상 dead로 보였지만 runtime artifact가 live consumer를 암시하지 않는가
4. 이미 닫힌 finding을 dormant-helper inventory 명목으로 다시 여는 오탐은 없는가
5. 최종 통합 시 `dead`, `dormant`, `bypassed-live`, `unknown` ledger를 재구성할 수 있는가

### 필수 근거

- `tests/e2e/test_l3_golden_route.py`
- `tests/test_run_stage4_canary.py`
- `docs/2026-03-13/main_a-retry-feedback-detail-consolidated-findings.md`
- `docs/2026-03-13/main_a-facade-shim-detail-consolidated-findings.md`
- `docs/2026-03-13/main_a-persistence-narrative-detail-consolidated-findings.md`

### 산출물

- `docs/2026-03-13/MDH-T5-callgraph-runtime-artifact-regression-findings.md`

---

## 9. 명시적 제외 범위

아래는 참조 근거로만 사용하고, 이번 조사 본체로 재포장하지 않는다.

- helper 내부 알고리즘의 품질 자체
- dead file 전체 청소 작업
- desktop IPC 세부 구현
- remediation patch 작성
- unrelated module general dead code sweep

---

## 10. 통합 산출물 규칙

### 터미널 결과 문서

- `docs/2026-03-13/MDH-T1-retry-guidance-helper-liveness-findings.md`
- `docs/2026-03-13/MDH-T2-audit-validation-helper-liveness-findings.md`
- `docs/2026-03-13/MDH-T3-stage01-npc-ui-helper-liveness-findings.md`
- `docs/2026-03-13/MDH-T4-bootstrap-history-cache-helper-liveness-findings.md`
- `docs/2026-03-13/MDH-T5-callgraph-runtime-artifact-regression-findings.md`

### 통합 문서

- `docs/2026-03-13/main_a-dormant-helper-live-consumer-detail-consolidated-findings.md`
- `docs/2026-03-13/main_a-dormant-helper-live-consumer-detail-consolidated-findings-3pass-reaudit.md`

### 중복 처리 규칙

- 기존 facade, retry, bootstrap, persistence 문서에서 이미 닫힌 항목은 재오픈 금지
- 단, `live consumer inventory` 자체가 다른 책임 경계를 가지면 신규 `MDH-*` finding 가능
- 신규 finding에는 아래 중 하나를 반드시 적는다
  - `none`
  - `related-but-new-live-consumer-surface`
  - `already-covered-do-not-reopen`

---

## 11. 실행 완료 판정

아래를 모두 만족해야 본 오더가 닫힌다.

1. T1 ~ T5 결과 문서가 모두 존재한다.
2. 각 문서가 `PASS1 -> PASS2 -> PASS3` 요약을 가진다.
3. 각 finding이 코드 근거, 테스트 근거, downstream 경계, 중복 여부를 모두 가진다.
4. 통합본이 `dead / dormant / bypassed-live / unknown` ledger를 재구성한다.
5. 통합본 3PASS 재감리가 최종 오탐 제거 여부와 SSOT 승격 가능성을 명시한다.

---

## 12. 초기 상태

- 본 오더 문서는 `execution-ready`다.
- 결과 문서와 통합 문서는 본 오더와 함께 생성되지만 초기 상태는 모두 `template / not executed`다.
- 조사 단계가 끝나기 전에는 확정 finding이 없는 상태로 본다.
