# main_a Runtime Recovery Lifecycle Detail Full Survey Audit Order

> 작성일: 2026-03-13
> 트랙: `main_a.py` bootstrap, recovery, cache lifecycle blind spot audit
> 상태: `execution-ready`
> 목적: `main_a.py`의 boot, project switch, runtime restore, cache anchor, history restore, preset recovery, commit/rollback helper가 하나의 lifecycle graph로 일관되게 동작하는지 전면 전량 조사한다.
> 방식: `5-terminal 병렬`, 각 터미널 자체 `3PASS`, 통합본 `3PASS 재감리`

---

## 0. 문서 역할

- 이 문서는 `main_a.py` runtime recovery lifecycle 조사 오더다.
- 이 문서는 코드 수정 오더가 아니다.
- 조사 단계에서 코드 직접 수정은 금지한다.
- 모든 문서는 `UTF-8` 고정이다. `???`, `�`, 깨진 한글이 보이면 즉시 중단하고 인코딩 이상으로 기록한다.
- 결과 문서가 채워지기 전까지는 어떤 finding도 확정으로 간주하지 않는다.

---

## 1. 왜 별도 트랙이 필요한가

기존 문서들은 control plane, destructive op, shared persistence helper를 각각 다뤘다. 그러나 아래 표면은 아직 `boot -> project switch -> runtime restore -> rollback/recovery -> next boot` 전체 lifecycle graph 관점의 독립 오더로 잠기지 않았다.

- `boot()` 이후 runtime state가 project switch / recovery / restart에서 같은 계약을 유지하는지 여부
- `_ignite_quad_cache_system()`, `_load_v50_history()`, `_restore_preset_registry()`가 같은 lifecycle chain 안에서 어떤 지위를 가지는지 여부
- cache anchor, preset registry, history restore, commit/rollback helper가 부분 성공 / 부분 실패를 어떻게 드러내는지 여부
- `ProjectService._restore_runtime_state()`와 `main_a.py` helper 경계가 같은 복구 의미를 가지는지 여부
- legacy patch 문서의 전제와 현재 runtime lifecycle이 drift했는지 여부

관련 문서:

- `docs/2026-03-13/main_a-control-plane-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-persistence-narrative-detail-full-survey-audit-order.md`
- `docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md`
- `docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md`
- `docs/2026-02-23/opus_tf6_system_audit_order.md`
- `docs/2026-02-23/opus_tf6_patch_order.md`

본 트랙은 destructive op 범위 재감사가 아니라, `runtime recovery lifecycle`을 별도 SSOT로 잠그는 데 목적이 있다.

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

- 담당 helper, service, test, 기존 문서를 전부 읽는다.
- 후보 finding을 `HIGH`, `MED`, `LOW` 확신도로 분류한다.
- boot, restore, rollback, restart 중 어느 lifecycle 구간의 문제인지 태깅한다.

#### PASS 2 - 교차 검증

- 코드 근거, 테스트 근거, 문서 근거를 함께 대조한다.
- helper 단독 문제로 볼지 lifecycle graph 문제로 볼지 경계를 분리한다.
- 기존 문서에서 이미 닫힌 항목은 재오픈하지 않는다.

#### PASS 3 - 최종 확정

- 확정 항목만 `[MRL-TN-SEQ]` 형식으로 채택한다.
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

- `P0`: boot/recovery lifecycle 오류로 데이터 손실, 복구 불가 상태 파손, 다음 부팅 불능이 발생하는 경우
- `P1`: runtime state restore, cache/preset/history 복구, project switch semantics가 잘못돼 다음 작업이 오염되는 경우
- `P2`: partial-fail visibility 부족, helper 간 lifecycle 역할 불명확, legacy patch drift, 테스트-코드 contract 불일치
- `P3`: 관측성, naming drift, 로그/문서 미세 불일치

---

## 3. 조사 범위 지도

| Terminal | 초점 | 핵심 범위 |
|---------|------|-----------|
| T1 | Boot / project switch / runtime state restore | `boot()`, project selection, runtime object rebind, restore entrypoint |
| T2 | Cache / anchor / history lifecycle | `_ignite_quad_cache_system()`, `sys_caches`, `_load_v50_history()` |
| T3 | Preset / config / recovery registry | `_restore_preset_registry()`, preset state, config rebound, project recovery |
| T4 | Commit / rollback / async recovery contract | `_safe_commit()`, `_safe_commit_async()`, rollback helper, service recovery |
| T5 | Lifecycle tests / docs / legacy patch regression | property, chaos, e2e, old patch docs, lifecycle claim 재검증 |

---

## 4. Terminal 1 - Boot / Project Switch / Runtime State Restore

### 담당 범위

- `main_a.py`
  - `boot()`
  - `_select_project()`
  - project switch 이후 runtime state 재구성 관련 helper
- 직접 downstream
  - `modules/core/project_manager.py`
  - `modules/core/project_support.py`
  - `modules/core/services/project_service.py`

### 핵심 검사 포인트

1. boot 후 runtime object graph와 project switch 후 graph가 같은 복구 의미를 가지는가
2. `current_project`, `selected_genre`, logger, caches, services가 project 전환 후 부분적으로만 갱신되지 않는가
3. recovery entrypoint와 normal boot entrypoint가 서로 다른 초기화 순서를 기대하지 않는가
4. restart 없이 project만 바꿀 때 stale runtime state가 남지 않는가
5. 기존 boot control-plane 문서와 lifecycle 관점이 충돌하지 않는가

### 필수 근거

- `tests/test_runtime_paths.py`
- `tests/test_project_support.py`
- `tests/test_project_service.py`
- `modules/core/project_manager.py`

### 산출물

- `docs/2026-03-13/MRL-T1-bootstrap-runtime-state-restore-findings.md`

---

## 5. Terminal 2 - Cache / Anchor / History Lifecycle

### 담당 범위

- `main_a.py`
  - `_ignite_quad_cache_system()`
  - `_is_cache_alive()`
  - `_load_v50_history()`
  - cache anchor save / read helper 전반

### 핵심 검사 포인트

1. cache anchor 저장 실패, cache alive 실패, history restore no-op이 같은 lifecycle graph 안에서 어떤 의미를 가지는가
2. `_ignite_quad_cache_system()`이 부분 실패 후 성공처럼 보이는가
3. `_load_v50_history()`가 intentional no-op인지, 복구 contract 누락인지 분리 가능한가
4. cache lifecycle과 history restore lifecycle이 project switch / restart와 일관되게 연결되는가
5. 다음 boot에서 stale cache metadata나 missing history가 silent drift를 만들지 않는가

### 필수 근거

- `tests/test_stage_transition.py`
- `tests/test_project_service.py`
- `modules/core/services/project_service.py`
- `docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md`

### 산출물

- `docs/2026-03-13/MRL-T2-cache-anchor-history-lifecycle-findings.md`

---

## 6. Terminal 3 - Preset / Config / Recovery Registry

### 담당 범위

- `main_a.py`
  - `_restore_preset_registry()`
  - preset / config rebound helper 전반
- 직접 downstream
  - `modules/core/services/project_service.py`
  - preset state 관련 runtime object

### 핵심 검사 포인트

1. preset registry 복구가 no-data, malformed data, callback failure에서 같은 정책을 가지는가
2. project switch / rollback / wipe 이후 preset state가 stale하게 남지 않는가
3. preset 복구와 config rebound가 서로 다른 truth source를 보지 않는가
4. recovery registry가 boot path와 destructive-op path에서 다른 의미로 사용되지 않는가
5. 기존 patch 문서가 전제한 preset restore semantics가 현재 코드와 같은가

### 필수 근거

- `tests/test_project_service.py`
- `tests/property/test_db_rollback_props.py`
- `modules/core/services/project_service.py`
- `docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md`

### 산출물

- `docs/2026-03-13/MRL-T3-project-switch-preset-registry-findings.md`

---

## 7. Terminal 4 - Commit / Rollback / Async Recovery Contract

### 담당 범위

- `main_a.py`
  - `_safe_commit()`
  - `_safe_commit_async()`
  - rollback / recovery helper 전반
- 직접 downstream
  - `modules/core/services/project_service.py`
  - rollback 관련 tracker / cache / anchor 경계

### 핵심 검사 포인트

1. sync / async commit helper가 같은 rollback 의미를 보장하는가
2. commit `False`와 exception이 lifecycle graph에서 같은 정책으로 처리되는가
3. recovery helper가 partial cleanup을 남긴 뒤 성공처럼 보이지 않는가
4. rollback 이후 다음 boot / next stage에서 stale state가 남지 않는가
5. service-level rollback invariant와 app-level helper invariant가 같은가

### 필수 근거

- `tests/property/test_db_rollback_props.py`
- `tests/chaos/test_partial_commit.py`
- `tests/integration/test_patch_wiring.py`
- `modules/core/services/project_service.py`

### 산출물

- `docs/2026-03-13/MRL-T4-commit-rollback-recovery-contract-findings.md`

---

## 8. Terminal 5 - Lifecycle Tests / Docs / Legacy Patch Regression

### 담당 범위

- lifecycle 관련 test 전반
- `docs/2026-02-23/*`
- `docs/2026-03-13/*consolidated-findings*.md`
- property / chaos / e2e / smoke artifact

### 핵심 검사 포인트

1. 현재 테스트가 lifecycle graph 전체를 잠그는가, 아니면 helper 단위만 초록으로 남기는가
2. legacy patch 문서에서 닫혔다고 본 lifecycle 가정이 현재도 성립하는가
3. boot, restore, rollback, restart가 서로 다른 문서에서 다른 truth를 갖고 있지 않은가
4. 통합 시 `boot`, `restore`, `rollback`, `next-boot drift` ledger를 재구성할 수 있는가
5. 이전 문서와 신규 surface의 중복 판정이 가능한가

### 필수 근거

- `tests/e2e/test_l3_golden_route.py`
- `tests/chaos/test_partial_commit.py`
- `docs/2026-02-23/opus_tf6_system_audit_order.md`
- `docs/2026-02-23/opus_tf6_patch_order.md`
- `docs/2026-03-13/main_a-control-plane-detail-consolidated-findings.md`

### 산출물

- `docs/2026-03-13/MRL-T5-lifecycle-tests-docs-regression-findings.md`

---

## 9. 명시적 제외 범위

아래는 참조 근거로만 사용하고, 이번 조사 본체로 재포장하지 않는다.

- Stage 2/3/4 내부 생성 알고리즘 심층
- desktop IPC / frontend connectivity
- unrelated global dead code sweep
- remediation patch 작성
- destructive op 삭제 범위 자체의 재감사

---

## 10. 통합 산출물 규칙

### 터미널 결과 문서

- `docs/2026-03-13/MRL-T1-bootstrap-runtime-state-restore-findings.md`
- `docs/2026-03-13/MRL-T2-cache-anchor-history-lifecycle-findings.md`
- `docs/2026-03-13/MRL-T3-project-switch-preset-registry-findings.md`
- `docs/2026-03-13/MRL-T4-commit-rollback-recovery-contract-findings.md`
- `docs/2026-03-13/MRL-T5-lifecycle-tests-docs-regression-findings.md`

### 통합 문서

- `docs/2026-03-13/main_a-runtime-recovery-lifecycle-detail-consolidated-findings.md`
- `docs/2026-03-13/main_a-runtime-recovery-lifecycle-detail-consolidated-findings-3pass-reaudit.md`

### 중복 처리 규칙

- 기존 control-plane, persistence, destructive-op 문서에서 이미 닫힌 항목은 재오픈 금지
- 단, `runtime recovery lifecycle` 자체가 다른 책임 경계를 가지면 신규 `MRL-*` finding 가능
- 신규 finding에는 아래 중 하나를 반드시 적는다
  - `none`
  - `related-but-new-runtime-lifecycle-surface`
  - `already-covered-do-not-reopen`

---

## 11. 실행 완료 판정

아래를 모두 만족해야 본 오더가 닫힌다.

1. T1 ~ T5 결과 문서가 모두 존재한다.
2. 각 문서가 `PASS1 -> PASS2 -> PASS3` 요약을 가진다.
3. 각 finding이 코드 근거, 테스트 근거, downstream 경계, 중복 여부를 모두 가진다.
4. 통합본이 boot / restore / rollback / next-boot drift ledger를 재구성한다.
5. 통합본 3PASS 재감리가 최종 오탐 제거 여부와 SSOT 승격 가능성을 명시한다.

---

## 12. 초기 상태

- 본 오더 문서는 `execution-ready`다.
- 결과 문서와 통합 문서는 본 오더와 함께 생성되지만 초기 상태는 모두 `template / not executed`다.
- 조사 단계가 끝나기 전에는 확정 finding이 없는 상태로 본다.
