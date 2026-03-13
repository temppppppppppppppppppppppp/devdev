# main_a Persistence Narrative Detail Full Survey Audit Order

> 작성일: 2026-03-13
> 트랙: `main_a.py` shared persistence and narrative helper blind spot audit
> 상태: `execution-ready`
> 목적: `main_a.py`에 남아 있는 shared persistence / protagonist / episode mapping / narrative summary helper 계약을 전면 전량 조사한다.
> 방식: `5-terminal 병렬`, 각 터미널 자체 `3PASS`, 통합본 `3PASS 재감리`

---

## 0. 문서 역할

- 이 문서는 `main_a.py` shared helper 조사 오더다.
- 이 문서는 코드 수정 오더가 아니다.
- 조사 단계에서 코드 직접 수정은 금지한다.
- 모든 문서는 `UTF-8` 고정이다. `???`, `�`, 깨진 한글이 보이면 즉시 중단하고 인코딩 이상으로 기록한다.
- 결과 문서가 채워지기 전까지는 어떤 finding도 확정으로 간주하지 않는다.

---

## 1. 왜 별도 트랙이 필요한가

기존 문서들은 destructive op, control plane, stage quality, 구버전 patch 이력을 각각 다뤘다. 그러나 아래 표면은 아직 `main_a.py` shared helper 계약 관점의 독립 오더로 잠겨 있지 않다.

- `_safe_commit()` / `_safe_commit_async()` / `_restore_preset_registry()` 같은 persistence helper 표면
- protagonist name, entity registry, manuscript episode 계산처럼 Stage 1/2/3/4가 공유하는 narrative helper 표면
- `_generate_narrative_summary()` / `_load_narrative_summaries()`의 저장-로딩-주입 계약
- `_validate_volume_boundaries()`가 Stage01 helper에 남기는 coupling
- 구버전 patch / audit 문서와 현재 runtime contract 사이의 drift 가능성

관련 문서:

- `docs/2026-03-13/main_a-control-plane-detail-full-survey-audit-order.md`
- `docs/2026-03-10/stage-quality-improvement-audit-3pass.md`
- `docs/2026-02-23/opus_tf6_system_audit_order.md`
- `docs/2026-02-23/opus_tf6_patch_order.md`

본 트랙은 destructive op 재감사가 아니라, `main_a.py` shared helper surface의 계약 안정성과 consumer coupling을 조사하는 데 목적이 있다.

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
- 기존 patch / audit 이력과 중복 가능성이 있으면 일단 `legacy overlap`으로 표시한다.

#### PASS 2 - 교차 검증

- 코드 근거, 테스트 근거, 문서 근거를 함께 대조한다.
- 기존 문서에서 이미 닫힌 항목은 재오픈하지 않는다.
- 다만 기존 문서가 특정 patch 이력만 다뤘고, 현재 문제가 `main_a.py` shared helper contract 문제면 신규 finding으로 유지 가능하다.

#### PASS 3 - 최종 확정

- 확정 항목만 `[MPN-TN-SEQ]` 형식으로 채택한다.
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

- `P0`: commit / restore contract 오류로 데이터 손실 또는 회복 불가 상태 파손
- `P1`: protagonist / episode / volume 경계 오판으로 Stage 1/3/4가 잘못된 입력을 소비
- `P2`: summary load/generate drift, helper coupling, cache lifecycle 불명확, 테스트-코드 불일치
- `P3`: 관측성, naming drift, legacy 문서-코드 미세 불일치

---

## 3. 조사 범위 지도

| Terminal | 초점 | 핵심 범위 |
|---------|------|-----------|
| T1 | Commit / preset / cache lifecycle | `_restore_preset_registry()`, `_safe_commit()`, `_safe_commit_async()`, `_is_cache_alive()` |
| T2 | Protagonist / entity / episode mapping | `_get_protagonist_name()`, `_fix_entity_registry_protagonist()`, `_get_max_episode_from_manuscripts()`, `_calculate_arc_from_episode()` |
| T3 | Stage01 shared helper coupling | `_validate_volume_boundaries()`와 `stage01_helpers.py` 소비 경계 |
| T4 | Narrative summary generation / load | `_generate_narrative_summary()`, `_load_narrative_summaries()`와 Stage4 consumer 계약 |
| T5 | Consumer tests / legacy patch regression | Stage2/3/4 context, project_service, 구문서, e2e test 재검증 |

---

## 4. Terminal 1 - Commit / Preset / Cache Lifecycle

### 담당 범위

- `main_a.py`
  - `_restore_preset_registry()`
  - `_safe_commit()`
  - `_safe_commit_async()`
  - `_is_cache_alive()`
- 직접 downstream
  - `modules/core/services/project_service.py`

### 핵심 검사 포인트

1. `_safe_commit()` 실패 시 인메모리와 DB 상태가 어긋나는 경계가 남아 있는가
2. `_safe_commit_async()`와 sync 버전이 같은 rollback 의미를 보장하는가
3. `_restore_preset_registry()`가 recovery helper인지 side-effectful mutation helper인지 명확한가
4. cache alive 판정이 narrative helper / commit helper의 선행 조건으로 오용되지 않는가
5. 구 patch 문서와 현재 코드가 drift했는가

### 필수 근거

- `tests/test_project_service.py`
- `tests/property/test_db_rollback_props.py`
- `tests/chaos/test_partial_commit.py`
- `modules/core/services/project_service.py`

### 산출물

- `docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md`

---

## 5. Terminal 2 - Protagonist / Entity / Episode Mapping

### 담당 범위

- `main_a.py`
  - `_get_protagonist_name()`
  - `_fix_entity_registry_protagonist()`
  - `_get_max_episode_from_manuscripts()`
  - `_calculate_arc_from_episode()`

### 핵심 검사 포인트

1. protagonist name 추출 실패 시 fallback이 의미적으로 안전한가
2. entity registry fix가 destructive overwrite인지 최소 보정인지 명확한가
3. manuscript 기반 max episode 계산이 sparse manuscript나 partial resume에서 오작동하지 않는가
4. episode -> arc 매핑이 Stage 2/3 consumer 기대와 맞는가
5. helper가 `None` / 빈 자료형 / 잘못된 타입에 과도하게 낙관적이지 않은가

### 필수 근거

- `tests/test_stage3_orchestrator.py`
- `tests/e2e/test_l3_stage3_smoke.py`
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`

### 산출물

- `docs/2026-03-13/MPN-T2-protagonist-episode-mapping-findings.md`

---

## 6. Terminal 3 - Stage01 Shared Helper Coupling

### 담당 범위

- `main_a.py`
  - `_validate_volume_boundaries()`
- 직접 downstream
  - `modules/core/stage01_helpers.py`

### 핵심 검사 포인트

1. Stage01 helper가 `main_a.py`에 남은 validation helper에 과도하게 결합되어 있는가
2. volume boundary 판정이 Stage 1 reject / warning 기준과 일치하는가
3. stage map 문서와 실제 helper 반환 구조가 같은가
4. helper 테스트가 길이/경계/invalid structure를 충분히 덮는가
5. 향후 facade 분리 시 regression 위험이 어디에 집중되는가

### 필수 근거

- `tests/test_stage01_helpers.py`
- `docs/stage_map/stage1.md`
- `modules/core/stage01_helpers.py`

### 산출물

- `docs/2026-03-13/MPN-T3-stage01-stage3-shared-helper-findings.md`

---

## 7. Terminal 4 - Narrative Summary Generation / Load

### 담당 범위

- `main_a.py`
  - `_generate_narrative_summary()`
  - `_load_narrative_summaries()`
- 직접 downstream
  - `modules/core/stage4_context.py`

### 핵심 검사 포인트

1. summary generation과 summary load가 같은 보존 범위를 바라보는가
2. hard-coded 상한이 장기 운영에서 구조적 drift를 만들지 않는가
3. Stage4 consumer가 실제로 필요한 summary 집합과 loader 정책이 일치하는가
4. cache / persistence / flush 경계가 summary 저장 시점과 어긋나지 않는가
5. 기존 stage-quality 문서에서 지적된 이슈가 아직 열린 상태인지 닫힌 상태인지 분리 가능한가

### 필수 근거

- `tests/test_sweep23.py`
- `tests/test_stage4_context.py`
- `docs/2026-03-10/stage-quality-improvement-audit-3pass.md`
- `modules/core/stage4_context.py`

### 산출물

- `docs/2026-03-13/MPN-T4-stage4-summary-cache-findings.md`

---

## 8. Terminal 5 - Consumer Tests / Legacy Patch Regression

### 담당 범위

- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`
- `modules/core/services/project_service.py`
- 관련 e2e / property / chaos / legacy docs

### 핵심 검사 포인트

1. context consumer가 helper 존재만 가정하고 semantic contract는 검증하지 않는가
2. 구 patch 문서에서 닫혔다고 적힌 문제가 현재도 잠재 surface로 남아 있는가
3. 같은 helper를 서로 다른 stage가 다른 의미로 해석하지 않는가
4. MagicMock 중심 테스트가 rollback / persistence semantics를 과대평가하지 않는가
5. 최종 통합 시 legacy overlap과 신규 surface를 분리할 수 있는가

### 필수 근거

- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context.py`
- `tests/e2e/test_l3_golden_route.py`
- `docs/2026-02-23/opus_tf6_system_audit_order.md`
- `docs/2026-02-23/opus_tf6_patch_order.md`

### 산출물

- `docs/2026-03-13/MPN-T5-consumer-tests-legacy-contract-findings.md`

---

## 9. 명시적 제외 범위

아래는 참조 근거로만 사용하고, 이번 조사 본체로 재포장하지 않는다.

- destructive op 자체의 삭제 범위 검증
- Stage 2/3/4 내부 생성 알고리즘 심층
- one-stop / frontier-lag / lookahead
- Stage 0 UI 선택 로직
- 실제 remediation patch 작성

---

## 10. 통합 산출물 규칙

### 터미널 결과 문서

- `docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md`
- `docs/2026-03-13/MPN-T2-protagonist-episode-mapping-findings.md`
- `docs/2026-03-13/MPN-T3-stage01-stage3-shared-helper-findings.md`
- `docs/2026-03-13/MPN-T4-stage4-summary-cache-findings.md`
- `docs/2026-03-13/MPN-T5-consumer-tests-legacy-contract-findings.md`

### 통합 문서

- `docs/2026-03-13/main_a-persistence-narrative-detail-consolidated-findings.md`
- `docs/2026-03-13/main_a-persistence-narrative-detail-consolidated-findings-3pass-reaudit.md`

### 중복 처리 규칙

- 기존 patch / audit 문서에서 이미 닫힌 항목은 재오픈 금지
- 단, `main_a.py` shared helper contract 자체가 다른 책임 경계를 가지면 신규 `MPN-*` finding 가능
- 신규 finding에는 아래 중 하나를 반드시 적는다
  - `none`
  - `related-but-new-shared-helper-surface`
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
