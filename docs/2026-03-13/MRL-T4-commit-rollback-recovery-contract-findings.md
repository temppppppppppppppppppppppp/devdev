# [MRL-T4] Commit / Rollback / Async Recovery Contract Findings

> 작성일: 2026-03-13
> 상태: `3pass executed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-runtime-recovery-lifecycle-detail-full-survey-audit-order.md`

---

## 조사 범위

- `main_a.py`
  - `_safe_commit()`
  - `_safe_commit_async()`
  - `_reset_stage_2()`
  - `_rewind_stage_2()`
  - `_rollback_episode()`
  - `_wipe_production_data()`
- `modules/core/services/project_service.py`
  - `_restore_runtime_state()`
  - `reset_stage_2()`
  - `rewind_stage_2()`
  - `rollback_episode()`
  - `wipe_production_data()`

## 필수 근거

- `tests/property/test_db_rollback_props.py`
- `tests/chaos/test_partial_commit.py`
- `tests/integration/test_patch_wiring.py`
- `modules/core/services/project_service.py`
- 추가 확인
  - `tests/test_project_service.py`
  - `tests/test_main_a_rollback.py`
  - `modules/core/stage3_context.py`
  - `modules/core/stage4_context.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_context_builder.py`
  - `docs/2026-03-13/MCP-T4-destructive-ops-recovery-findings.md`
  - `docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md`
  - `docs/2026-03-13/MPN-T5-consumer-tests-legacy-contract-findings.md`
  - `docs/2026-02-23/opus_tf6_a_audit.md`
  - `docs/2026-02-23/opus_tf7r_patch_order.md`

## 실행 로그

- `pytest tests/test_project_service.py tests/property/test_db_rollback_props.py tests/chaos/test_partial_commit.py tests/integration/test_patch_wiring.py tests/test_main_a_rollback.py -q`
  - `52 passed in 5.11s`
- ad hoc verification 3건
  - `world_state.rollback_to()` 예외는 `rollback_episode() -> True`로 남는지 확인
  - `emotion_tracker.rollback_to()` 예외가 `draft/vector cleanup 이후 False`로 바뀌는지 확인
  - `project._load_from_db()` 예외가 같은 경계에서 `False`로 바뀌는지 확인

## PASS 기록

- PASS 1: 완료
  - 후보 5건 수집
  - `_safe_commit[_async]` contract, `_restore_runtime_state()` hard-fail/soft-fail 분기, app-level success gating, 기존 destructive-op 문서와의 중복 여부를 분리했다.
- PASS 2: 완료
  - 관련 테스트 `52 passed in 5.11s`
  - ad hoc verification 3건으로 post-commit recovery helper failure의 실제 반환값과 cleanup 시점을 교차 검증했다.
  - `MCP-T4`, `MPN-T1`, `MPN-T5`, `TF-6-A`, `TF7R` 패치 의도와 대조했다.
- PASS 3: 완료
  - PASS1 후보 5건 -> PASS2 제거 3건 -> 최종 2건

## Executive Summary

- `ProjectService._restore_runtime_state()`는 destructive mutation과 draft/vector cleanup이 끝난 뒤에 실행되는데, 내부 helper 일부는 예외를 그대로 올리고 일부는 log-only로 삼킨다.
- 그 결과 rollback/reset/rewind/wipe는 같은 lifecycle graph 안에서 어떤 실패는 `False`로 끝나 app cache invalidation을 건너뛰고, 어떤 실패는 `True`로 끝나 stale `world_state`/`fact_ledger`를 다음 stage에 그대로 넘긴다.
- 현재 invariant 검사와 테스트는 `emotion/state_delta` tracker에만 집중되어 있어 fail-open recovery helper의 drift를 잡지 못한다.

## PASS 2 제거 항목

| 후보 | 판정 | 이유 |
|----|----|----|
| `reset_after()` 조기 커밋으로 인한 destructive partial cleanup | 제거 | `docs/2026-03-13/MCP-T4-destructive-ops-recovery-findings.md`의 `MCP-T4-001`이 이미 본체를 닫고 있다. 이번 문서는 그 이후 recovery helper 단계만 유지한다. |
| rewind/rollback 후 `foreshadow_tracker` 복구 drift | 제거 | `MCP-T4-002`에서 이미 control-plane surface로 확정됐다. runtime recovery 문서에서 재오픈하지 않는다. |
| `_safe_commit_async()` 자체의 신규 runtime recovery 결함 | 제거 | app code 상에서는 `asyncio.to_thread(self._safe_commit)` 위임 외 별도 surface가 없었다. smoke fixture drift는 `MPN-T5-003`에 이미 정리돼 있다. |

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| MRL-T4-001 | P1 | retained | `project_service.py` / `_restore_runtime_state`, destructive op 4종, `main_a.py` success gating | post-commit recovery helper 예외가 이미 반영된 rollback/reset를 `False`로 바꾸고 app-level cache invalidation을 건너뛰게 한다 |
| MRL-T4-002 | P2 | retained | `project_service.py` / `_restore_runtime_state`, `_assert_rollback_invariants` | `world_state`/`fact_ledger` recovery failure는 success로 통과하지만 invariant와 다음-stage consumer가 이를 구분하지 못한다 |

---

## [MRL-T4-001] P1 | post-commit recovery helper 예외가 이미 반영된 destructive op를 `False`로 뒤집고 app cache invalidation을 건너뛴다

**현상 요약**

`reset_stage_2()`, `rewind_stage_2()`, `rollback_episode()`, `wipe_production_data()`는 DB commit과 draft/vector cleanup을 마친 뒤 `_restore_runtime_state()`를 호출한다. 그런데 `_restore_runtime_state()` 안의 `project._load_from_db()`, `state_tracker_invalidator`, `emotion_tracker.rollback_to()`, `state_delta_tracker.rollback_to()`는 예외 보호가 없다. 이 중 하나가 실패하면 service는 `False`를 반환하지만, 이미 삭제된 DB/file/vector 상태는 되돌려지지 않는다. 상위 `main_a.py`는 `success=True`일 때만 prompt/writer/director cache를 비우므로 같은 프로세스 안에 stale runtime cache가 남는다.

**코드 근거**

- `modules/core/services/project_service.py:192-193`
- `modules/core/services/project_service.py:259-260`
- `modules/core/services/project_service.py:347-350`
- `modules/core/services/project_service.py:404-405`
  - destructive op 4종 모두 commit/cleanup 뒤 `_restore_runtime_state(...)`를 호출한다.
- `modules/core/services/project_service.py:63-68`
- `modules/core/services/project_service.py:84-92`
  - `project._load_from_db()`, tracker invalidation, `emotion_tracker.rollback_to()`, `state_delta_tracker.rollback_to()`는 예외를 그대로 올린다.
- `modules/core/services/project_service.py:154-161`
  - 실패 후 호출되는 `_rollback_open_transaction()`은 열린 트랜잭션이 있을 때만 의미가 있다. commit 이후 예외에는 복구 수단이 아니다.
- `modules/core/services/project_service.py:196-199`
- `modules/core/services/project_service.py:263-266`
- `modules/core/services/project_service.py:352-355`
- `modules/core/services/project_service.py:408-410`
  - post-commit helper 예외도 최종적으로 `False`로 변환된다.
- `main_a.py:3157-3183`
- `main_a.py:3187-3215`
- `main_a.py:3219-3255`
- `main_a.py:3259-3285`
  - app-level cache invalidation은 `success` 분기 안에만 있다.

**downstream 영향 경계**

- rollback/reset/rewind/wipe가 실제로는 완료됐는데도 operator는 `False`와 error log만 보게 된다.
- `main_a.py`의 prompt timeline cache, cumulative state cache, writer/director cache는 그대로 남아 DB 실상과 어긋날 수 있다.
- 특히 `project._load_from_db()`가 실패하는 경우 service-level tracker invalidation조차 실행되지 않아 stale `state_tracker`도 남는다.
- 결과적으로 같은 프로세스에서 다음 stage 진입, 추가 rollback 재시도, 상태 미리보기 판단이 split-brain 상태에서 이뤄진다.

**현재 테스트 근거 또는 테스트 부재**

- `tests/test_project_service.py:61-76`, `tests/test_project_service.py:112-137`, `tests/test_project_service.py:162-230`, `tests/test_project_service.py:241-252`
  - success path와 commit failure까지만 본다. `_restore_runtime_state()` 내부 helper exception은 전혀 주입하지 않는다.
- `tests/test_main_a_rollback.py:20-30`
  - `False` 반환 시 cache를 유지하는 current policy만 검증한다.
- `tests/integration/test_patch_wiring.py:381-520`
  - `emotion/state_delta rollback_to()`가 호출되는지만 보고, 예외 시 cleanup 시점은 보지 않는다.
- ad hoc verification
  - `emotion_tracker.rollback_to()`에 예외를 주입하면 `rollback_episode()`는 `False`를 반환했지만, `reset_after`, draft delete, `memory.delete_episodes_from()`는 이미 실행됐다.
  - `project._load_from_db()` 예외도 같은 경계에서 `False`를 반환했고, 마지막 로그는 `Rollback failed: load boom`이었다.

**기존 문서와의 중복 여부**

- `duplicate status`: `related-but-new-runtime-lifecycle-surface`
- 관련 문서:
  - `MCP-T4-001`은 `reset_after()/save_anchor()/safe_commit()` 단계의 partial cleanup을 다뤘다.
  - 이번 finding은 그 이후 `_restore_runtime_state()` 단계에서 발생하는 hard-fail recovery surface다.
  - `TF-A-3`은 tracker invalidation 호출 경계만 봤고, post-commit recovery exception policy까지는 닫지 않았다.

**권장 후속 조치**

- `_restore_runtime_state()`를 `success/failure/partial_failure_committed` 같은 구조화 결과로 바꾸고, 이미 destructive mutation이 끝난 뒤의 예외는 단순 `False`로 압축하지 않는다.
- 최소한 post-commit helper 실패 시에도 `main_a.py`가 prompt/writer/director cache invalidation을 수행하도록 partial-failure 경계를 분리한다.
- 회귀 테스트를 추가한다.
  - `project._load_from_db()` 예외 after cleanup
  - `emotion_tracker.rollback_to()` 예외 after cleanup
  - `state_delta_tracker.rollback_to()` 예외 after cleanup

---

## [MRL-T4-002] P2 | `world_state`/`fact_ledger` recovery failure는 success로 통과하지만 invariant와 next-stage consumer가 이를 구분하지 못한다

**현상 요약**

`_restore_runtime_state()`는 `world_state.rollback_to()`와 `fact_ledger.rollback_to()` 예외를 log-only로 처리하고 계속 진행한다. 따라서 rollback/reset/rewind/wipe는 runtime recovery 일부가 실패해도 `True`를 반환할 수 있다. 그런데 `_assert_rollback_invariants()`와 현재 테스트는 `emotion/state_delta` tracker만 검사한다. 동시에 Stage 3/4 context와 builder는 `app.world_state`/`app.fact_ledger`를 직접 소비한다. 결과적으로 operator는 성공 메시지를 보지만, 다음 stage는 stale world/fact runtime object를 정상 상태처럼 사용한다.

**코드 근거**

- `modules/core/services/project_service.py:70-82`
  - `world_state.rollback_to()`와 `fact_ledger.rollback_to()` 예외는 `ui.log(...)`만 남기고 무시한다.
- `modules/core/services/project_service.py:357-379`
  - `_assert_rollback_invariants()`는 `EmotionArcTracker`, `StateDeltaTracker`만 검사한다.
- `tests/property/test_db_rollback_props.py:1-290`
- `tests/chaos/test_partial_commit.py:1-169`
  - property/chaos 모두 `_assert_rollback_invariants()`의 tracker 경계만 검증한다.
- `tests/integration/test_patch_wiring.py:381-520`
  - integration도 `emotion/state_delta rollback_to()` 호출 여부만 본다.
- `modules/core/stage3_context.py:103-115`
  - `Stage3Context.from_app()`가 `app.world_state`, `app.fact_ledger`, `app.preset_registry`를 그대로 싣는다.
- `modules/core/stage4_context.py:168-177`
  - `Stage4Context.from_app()`도 같은 객체를 직접 싣는다.
- `modules/core/stage3_orchestrator.py:512-516`
  - Stage 3은 `ctx.state_tracker.bind_world_state(ctx.world_state)`까지 수행한다.
- `modules/core/stage4_orchestrator.py:372-381`
- `modules/core/stage4_context_builder.py:391-552`
- `modules/core/stage4_context_builder.py:1873-2188`
  - Stage 4는 `world_state` summary, raw state, `fact_ledger` summary/canonical data를 직접 소비한다.
- ad hoc verification
  - `world_state.rollback_to()`에 예외를 주입해도 `rollback_episode()`는 `True`를 반환했고, UI에는 `[WorldState] rollback_to failed: ws boom`만 남았다.

**downstream 영향 경계**

- rollback success 직후 Stage 3/4가 stale `world_state` 요약, canonical constraints, fact summary를 prompt/context에 주입할 수 있다.
- `state_tracker.bind_world_state(...)`가 stale object를 다시 바인딩해 다음 생성 단계 판단이 오염될 수 있다.
- operator는 성공/실패를 `True/False`로만 보는데, 실제로는 `partial recovery success`가 구분되지 않는다.

**현재 테스트 근거 또는 테스트 부재**

- `tests/test_project_service.py`에는 `world_state_fn`/`fact_ledger_fn` failure injection이 없다.
- `tests/property/test_db_rollback_props.py`와 `tests/chaos/test_partial_commit.py`는 tracker invariant만 다루며, world/fact recovery 결과를 전혀 보지 않는다.
- `tests/integration/test_patch_wiring.py`는 world/fact/preset restore wiring 자체를 커버하지 않는다.
- 이번 실행의 `52 passed`는 전부 이 fail-open contract를 허용한 상태에서 통과했다.

**기존 문서와의 중복 여부**

- `duplicate status`: `related-but-new-runtime-lifecycle-surface`
- 관련 문서:
  - `MCP-T4`는 `world_state/fact_ledger/preset restore` 테스트 공백을 coverage gap으로만 남겼다.
  - 이번 finding은 fail-open이 실제 success semantics로 굳어져 있고, Stage 3/4 consumer가 stale object를 직접 소비한다는 runtime lifecycle 경계를 확정한다.
  - `MPN-T1-001`의 stale preset 자체는 재오픈하지 않는다. 본 finding은 world/fact fail-open visibility가 본체다.

**권장 후속 조치**

- `_assert_rollback_invariants()`를 tracker 전용 helper로 두지 말고, `world_state.last_updated_ep`, `fact_ledger.last_updated_ep`, preset restore 결과까지 포함한 recovery ledger를 분리한다.
- `world_state`/`fact_ledger` restore 실패는 log-only가 아니라 operator-visible `partial_recovery` 결과와 audit event로 남긴다.
- 회귀 테스트를 추가한다.
  - `world_state.rollback_to()` 예외 -> partial recovery signal 확인
  - `fact_ledger.rollback_to()` 예외 -> Stage3/4 consumer가 stale object를 쓰지 않도록 guard 확인

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `_restore_runtime_state()` exception matrix | 테스트 부재 | `load_from_db`, `state_tracker_invalidator`, `world_state`, `fact_ledger`, `emotion`, `state_delta`, `preset` 각각의 failure injection test |
| `partial_failure_committed` 이후 app cache policy | 테스트 부재 | `main_a.py` wrappers가 partial recovery signal에서도 invalidate를 수행하는지 보는 regression test |
| `_safe_commit_async()`와 runtime recovery graph 연결 | open | 현재 app code엔 신규 defect 근거가 부족하므로, consumer-side contract drift는 `MPN-T5-003`와 함께 추적 |

## 마감 체크

- sync/async commit helper 의미 비교: 신규 retained 없음, 기존 `MPN-T5-003`과 중복 제거
- service-level rollback invariant vs app-level helper invariant 비교: 2건 확정
- partial cleanup / partial recovery visibility 점검: hard-fail 1건, fail-open 1건 확정
- legacy patch drift 확인: TF7R은 rollback 호출 추가까지는 잠갔지만 failure policy와 recovery ledger는 잠그지 못했다

## 최종 판정

- 최종 retained finding: `2건`
  - `P0`: 0건
  - `P1`: 1건
  - `P2`: 1건
  - `P3`: 0건
- PASS1 후보 5건 -> PASS2 제거 3건 -> PASS3 확정 2건
- 본 문서는 `template / not executed`가 아니라 `executed T4 finding set`이다.
