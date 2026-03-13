# [MRL-T5] Lifecycle Tests / Docs / Legacy Patch Regression Findings

> 작성일: 2026-03-13
> 상태: `executed / PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-runtime-recovery-lifecycle-detail-full-survey-audit-order.md`
> 실행 확인:
> - `pytest tests/test_project_service.py tests/test_main_a_rollback.py tests/property/test_db_rollback_props.py tests/chaos/test_partial_commit.py tests/test_runtime_paths.py tests/test_stage_transition.py tests/integration/test_patch_wiring.py -q` -> `64 passed in 3.98s`

`docs/2026-02-23/opus_tf5_patch_order.md` source restoration 이후 PASS1부터 T5 범위를 다시 수행했다.
이번 문서는 blocker 기록이 아니라 rerun 완료본이다. 초점은 code bug 재오픈이 아니라
현재 lifecycle regression net과 legacy proof surface가 실제로 무엇을 보장하는지 다시 잠그는 데 있다.

---

## 조사 범위

- tests
  - `tests/test_project_service.py`
  - `tests/test_main_a_rollback.py`
  - `tests/property/test_db_rollback_props.py`
  - `tests/chaos/test_partial_commit.py`
  - `tests/test_runtime_paths.py`
  - `tests/test_stage_transition.py`
  - `tests/integration/test_patch_wiring.py`
  - `tests/chaos/test_rollback_boundary.py`
- code
  - `modules/core/services/project_service.py`
  - `main_a.py`
- legacy docs
  - `docs/2026-02-23/opus_tf5_patch_order.md`
  - `docs/2026-02-23/opus_tf6_patch_order.md`
  - `docs/2026-02-23/opus_tf7r_patch_order.md`
- related source findings
  - `MRL-T1` .. `MRL-T4`

## PASS 기록

- PASS 1: 후보 6건 수집
  - rollback regression net이 tracker pair에만 잠겨 있다는 후보
  - next-boot / restart lifecycle proof 부재 후보
  - legacy TF-5 / TF7R closure wording 과대 판정 후보
  - `emotion_history` next-boot contamination 재확인 후보
  - preset restore partial-success 재확인 후보
  - `world_state` / `fact_ledger` recovery failure success-path 재확인 후보
- PASS 2: 후보 3건 제거
  - `emotion_history next-boot contamination`
    - 판정: `already-covered-do-not-reopen`
    - 근거: `MRL-T2-001`이 primary code surface로 이미 확정했다.
  - `preset restore partial-success`
    - 판정: `already-covered-do-not-reopen`
    - 근거: `MRL-T3-002`가 destructive recovery success gating 문제를 이미 보유한다.
  - `world_state / fact_ledger recovery failure success-path`
    - 판정: `already-covered-do-not-reopen`
    - 근거: `MRL-T4-002`가 code-level contract failure를 이미 확정했다.
- PASS 3: `MRL-T5-001` .. `MRL-T5-003` 3건 확정

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| `MRL-T5-001` | `P1` | retained | `tests/integration/test_patch_wiring.py`, `tests/chaos/test_partial_commit.py`, `tests/property/test_db_rollback_props.py` | rollback regression net이 `emotion_tracker` / `state_delta_tracker`에만 집중돼 `world_state`, `fact_ledger`, `preset_registry_restorer`를 실제로 잠그지 못한다 |
| `MRL-T5-002` | `P2` | retained | `tests/test_project_service.py`, `tests/test_main_a_rollback.py`, `tests/test_runtime_paths.py` | destructive recovery 이후 `next boot / restart / reload` semantics를 한 번에 검증하는 lifecycle proof가 없다 |
| `MRL-T5-003` | `P2` | retained | `opus_tf5_patch_order.md`, `opus_tf7r_patch_order.md`, current tests | legacy patch closure 문구가 현재 regression surface보다 강한 lifecycle closure를 암시한다 |

---

## [MRL-T5-001] rollback regression net이 tracker pair에만 잠겨 있다

1. ID
   - `MRL-T5-001`
2. Severity
   - `P1`
3. 현상 요약
   - 현재 rollback 회귀망의 직접 assertion은 거의 전부 `emotion_tracker`와 `state_delta_tracker`에 몰려 있다.
   - `world_state`, `fact_ledger`, `preset_registry_restorer`는 실제 `ProjectService._restore_runtime_state()`의 lifecycle core인데,
     핵심 rollback/property/chaos tests에서는 전부 `None` 또는 미주입으로 지나간다.
   - 그래서 `MRL-T4-002`와 `MRL-T3-002`가 지적한 복구 실패 표면은 code bug로는 남아 있어도,
     regression net 관점에서는 여전히 얕게 잠겨 있다.
4. 코드 근거
   - `tests/chaos/test_partial_commit.py:30-32`는 `world_state_fn=None`, `fact_ledger_fn=None`, `preset_registry_restorer=None`으로 고정한다.
   - `tests/integration/test_patch_wiring.py:424-426`, `494-496`도 같은 세 슬롯을 `None`으로 둔다.
   - `tests/property/test_db_rollback_props.py:36-50`은 property fixture를 `emotion_tracker` / `state_delta_tracker` 전용으로 만든다.
   - `tests/property/test_db_rollback_props.py:206-229`는 tracker callback이 `None`이어도 crash가 없어야 한다는 점만 본다.
   - 반면 실제 service는 `modules/core/services/project_service.py:63-96`에서 `_load_from_db()`, `world_state.rollback_to()`, `fact_ledger.rollback_to()`, `preset_registry_restorer()`를 모두 복구 체인에 포함한다.
5. downstream 영향 경계
   - `rollback/reset/wipe -> runtime restore` 전 구간
   - 특히 `world_state`, `fact_ledger`, preset restore failure가 다음 stage consumer와 next-boot semantics에 미치는 영향
   - `MRL-T4-002`, `MRL-T3-002` 같은 code finding의 regression safety
6. 현재 테스트 근거 또는 테스트 부재
   - 있음: tracker pair rollback warning / no-warning / no-crash proof
   - 부재: `world_state`, `fact_ledger`, preset restore mixed success-failure 조합을 검증하는 service-level regression test
7. 기존 문서와의 중복 여부
   - `related-but-new-runtime-lifecycle-surface`
   - 이유: T4/T3는 code defect를 다뤘고, 본 finding은 그 defect를 막아 줄 regression net의 빈곳을 다룬다.
8. 권장 후속 조치
   - `ProjectService` fixture에 concrete `world_state`, `fact_ledger`, `preset_registry_restorer` doubles를 주입한다.
   - 성공, partial failure, restore exception 세 경우를 나눠 `result`, warning, next-stage observable state를 함께 잠근다.

## [MRL-T5-002] destructive recovery 뒤 `next boot`를 잠그는 proof가 없다

1. ID
   - `MRL-T5-002`
2. Severity
   - `P2`
3. 현상 요약
   - 현재 test suite는 rollback/reset/wipe 호출 자체와 같은-process 후처리까지는 본다.
   - 하지만 `save -> destructive op -> app/runtime reload -> next boot readback`을 하나의 lifecycle graph로 검증하지 않는다.
   - 그 결과 T1/T2/T3가 지적한 truth-source split, cache/history drift, preset/base-genre drift는
     "현재 process에서는 green"이어도 다음 boot에서 다시 드러날 수 있다.
4. 코드 근거
   - `tests/test_project_service.py:196`은 `rollback_episode()` 후 `_load_from_db()` 호출만 확인한다.
   - `tests/test_project_service.py:222-223`은 `save_anchor()` 호출까지만 확인하고 새 app/boot readback은 보지 않는다.
   - `tests/test_main_a_rollback.py:37-150`은 app-level cache invalidation과 `foreshadow_tracker.load_from_db()`까지만 검증한다.
   - `tests/test_runtime_paths.py`는 workspace/project root boot path만 다루고 destructive recovery semantics는 다루지 않는다.
   - `tests/test_stage_transition.py`에는 `rollback`, `reset`, `wipe`, `load_from_db`, `restart` 관련 assertion이 없다.
5. downstream 영향 경계
   - `boot -> project switch -> rollback/reset/wipe -> next boot` lifecycle graph 전체
   - file-backed support contract, cache anchor, preset/base_genre, stale history rehydration
   - operator가 "same-process green"을 "next-boot safe"로 오판하는 risk
6. 현재 테스트 근거 또는 테스트 부재
   - 있음: helper invocation, save/load call, same-process invalidation
   - 부재: new app instance 또는 restart-like rebind를 거친 end-to-end lifecycle proof
7. 기존 문서와의 중복 여부
   - `related-but-new-runtime-lifecycle-surface`
   - 이유: T1/T2/T3는 각각의 drift를 code 기준으로 확정했고, 본 finding은 그 drift를 next-boot까지 잠그는 proof의 부재를 고정한다.
8. 권장 후속 조치
   - hermetic project fixture 하나로 `commit -> rollback/reset/wipe -> fresh ProjectService/bootstrap reload` 시나리오를 추가한다.
   - assertion은 단순 call 여부가 아니라 `selected_genre`, preset base genre, cache/history, support artifacts의 final state까지 포함해야 한다.

## [MRL-T5-003] legacy patch closure는 현재 proof surface보다 강하게 읽힌다

1. ID
   - `MRL-T5-003`
2. Severity
   - `P2`
3. 현상 요약
   - 복구된 `opus_tf5_patch_order.md`와 기존 `opus_tf7r_patch_order.md`는 rollback / invariant / test closure를 역사 기록으로는 유효하게 남긴다.
   - 하지만 현재 live regression surface는 그 문구가 암시하는 만큼 넓지 않다.
   - 특히 TF7R 문서는 `world/fact/foreshadow/emotion` invariant와 boundary scenario를 강하게 적지만,
     현재 남아 있는 직접 테스트는 tracker class boundary와 partial-commit scaffolding 중심이다.
4. 코드/문서 근거
   - `docs/2026-02-23/opus_tf7r_patch_order.md:17`, `132-136`, `347-377`은 post-invariant와 rollback boundary scenarios를 `world/fact/foreshadow/emotion` 수준으로 기술한다.
   - 그러나 `tests/chaos/test_rollback_boundary.py`는 실제로 `StateDeltaTracker` / `EmotionArcTracker` class boundary만 다룬다.
   - `docs/2026-02-23/opus_tf5_patch_order.md:55`, `58`, `73`, `256-266`은 rollback closure와 broad pytest totals를 historical proof로 남긴다.
   - 이번 rerun의 green result는 `64 passed in 3.98s`였지만, 위 PASS3 findings가 보여 주듯 lifecycle proof surface는 tracker pair와 same-process checks에 더 가깝다.
5. downstream 영향 경계
   - legacy patch order를 "current lifecycle regression guarantee"로 읽는 운영/감리 판단
   - historical patch closure와 current regression net의 책임 경계 혼동
   - 향후 blocker triage 시 historical doc가 proof matrix를 과대 대표하는 위험
6. 현재 테스트 근거 또는 테스트 부재
   - 있음: 현재 targeted suite는 green이며, restored TF-5 source도 UTF-8로 판독 가능하다.
   - 부재: legacy patch 문서와 current tests를 1:1로 매핑한 coverage matrix
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - `opus_tf5_patch_order.md`, `opus_tf7r_patch_order.md`는 historical provenance로 취급하고 current guarantee 문서로 쓰지 않는다.
   - consolidated doc에는 `historical patch closure != current regression closure` note를 명시한다.
   - 이후 runtime lifecycle proof는 fresh rerun artifact와 explicit coverage matrix 기준으로 재관리한다.

---

## Rejected / Removed Candidates

### RC-1. `emotion_history` next-boot contamination 재오픈

- 판정: `already-covered-do-not-reopen`
- 이유:
  - `MRL-T2-001`이 primary code surface를 이미 확정했다.
  - T5에서는 이를 막아 줄 proof surface 공백만 별도 유지한다.

### RC-2. preset restore partial-success 재오픈

- 판정: `already-covered-do-not-reopen`
- 이유:
  - `MRL-T3-002`가 destructive recovery success gating 문제를 이미 보유한다.

### RC-3. `world_state` / `fact_ledger` success-path mismatch 재오픈

- 판정: `already-covered-do-not-reopen`
- 이유:
  - `MRL-T4-002`가 code-level contract drift를 이미 잠갔다.

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| service-level rollback invariant beyond tracker pair | open | `world_state`, `fact_ledger`, preset restore mixed-success regression test |
| destructive recovery next-boot proof | open | fresh app/bootstrap reload를 포함한 end-to-end lifecycle test |
| historical patch -> current regression matrix | open | TF-5 / TF7R item과 current tests를 매핑한 explicit coverage table |

## PASS 요약

- PASS1 후보 `6건`
- PASS2 제거 `3건`
- PASS3 확정 `3건`

## 마감 체크

- 코드 근거 포함: `yes`
- 현재 테스트 근거 또는 테스트 부재 포함: `yes`
- 기존 문서와의 중복 여부 포함: `yes`
- restored TF-5 source 재판독 포함: `yes`
- `PASS1 -> PASS2 -> PASS3` 요약 포함: `yes`
